# -*- coding: utf-8 -*-
"""S138 eje 4 (a): cumulos detectados con VRP 0,0 MW en VIIRS 375, VIIRS 750 y MODIS.

Que mide. Sobre data/mirova_equivalent/<Tier A>.json (read-only), por volcan y sensor:
  1. records con primary_cluster.n_pixels > 0 y primary_cluster.vrp_mw == 0 ("pc0"), su
     fraccion sobre los records con cumulo, y el MECANISMO que los produce, leido de los
     diagnosticos persistidos (final_hotspot_source, diag_n_first_pass_pixels,
     diag_n_second_pass_recapture, n_anomalous_pixels, bt del pixel pico vs t_bg_k).
  2. el costo en NOCHES (A94): noches con ALERTA de MIROVA (CONS u OCR, solo pasadas que el
     pipeline mira: se excluyen las diurnas con el mismo criterio de store.py) en que NINGUNA
     pasada nuestra de ese sensor publica en el dashboard (pc.vrp_mw > 0, summit, centroide
     dentro del inner) y al menos una pasada nuestra tiene un cumulo en 0,0 MW.

Las dos preguntas del instrumento:
  P1. Si el mecanismo del cero estuviera roto del todo (todo cumulo en 0), esta medicion lo
      veria: la fraccion pc0 subiria a 1 y las noches perdidas con pc0 igualarian las perdidas.
  P2. Si el instrumento estuviera muerto (JSON sin cumulos, CSV sin alertas), se ve distinto:
      n_pc = 0 o n_mir = 0 se imprimen y se marcan SIN DATO, no como OK.
Control positivo: Lascar VIIRS375, noche con ALERTA MIROVA y record nuestro con pc.vrp > 0,
se imprime la primera coincidencia. Control negativo: una fecha sin alerta y sin record no
entra en ningun conteo (se comprueba explicitamente).

Denominadores y ventana: se imprimen en cada tabla (A90). Noche = fecha UTC de la pasada
(misma convencion que scripts/auto_audit_weekly.py, clave dt[:10]).
"""
import collections
import csv
import io
import json
import os
import random
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from auto_audit_weekly import es_pasada_diurna_descartada, _coords_por_volcan  # noqa: E402

OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
        "NevadosDeChillan", "Llaima", "Villarrica", "Copahue",
        "PuyehueCordonCaulle", "Chaiten"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
BUCKETS = ["VIIRS375", "VIIRS750", "MODIS"]
CAP = 50000


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def mecanismo(r):
    """Clasifica un record pc0 por el camino que fabrico el cumulo en cero."""
    src = r.get("final_hotspot_source")
    fp = (r.get("diag_n_first_pass_pixels") or 0) > 0
    sp = (r.get("diag_n_second_pass_recapture") or 0) > 0
    if src == "ctx_cluster":
        if not fp and sp:
            return "ctx: 2do paso sin activos (D19)"
        return "ctx: con activos del 1er paso"
    if src in ("test1_roi", "test1", "test1_nti_peak"):
        return "test1: keep_peak / anillo (D19 magnitud)"
    return f"otro ({src})"


def pico_frio(r):
    """True si el pixel mas caliente persistido no supera la mediana del anillo."""
    ap = r.get("anomaly_pixels") or []
    tb = r.get("t_bg_k")
    if not ap or tb is None:
        return None
    return max((p.get("bt_k") or -1) for p in ap) <= tb


def visible_dashboard(r, vol):
    """Criterio de frontend/index.html mirovaEqVrp (l. 1043-1064)."""
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0.0
    if not (0 < v <= CAP):
        return False
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return False
    cd = pc.get("centroid_dist_km")
    return cd is not None and cd <= INNER[vol]


def ic_prop(k, n, nb=5000, semilla=42):
    """IC 95 % bootstrap de una proporcion (remuestreo de unidades)."""
    if n == 0:
        return (float("nan"), float("nan"))
    rng = random.Random(semilla)
    xs = [1] * k + [0] * (n - k)
    ms = sorted(sum(rng.choices(xs, k=n)) / n for _ in range(nb))
    return ms[int(0.025 * nb)], ms[int(0.975 * nb)]


def main():
    alertas = load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"),
                                  ocr_path=str(SNAP / "registro_vrp_ocr.csv"))
    coords = _coords_por_volcan()
    fechas = sorted(a["fecha_utc"][:10] for a in alertas)
    GT_INI, GT_FIN = fechas[0], fechas[-1]
    print(f"Universo MIROVA CONS u OCR: {len(alertas)} pasadas-ALERTA, {GT_INI} a {GT_FIN}")

    mir = collections.defaultdict(float)   # (vol, bucket, fecha) -> max vrp
    n_diurnas = 0
    for a in alertas:
        if a["volcano"] not in VOLS or a["sensor_bucket"] not in BUCKETS:
            continue
        dt = a["fecha_utc"]
        latlon = coords.get(a["volcano"])
        try:
            dt_obj = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        except ValueError:
            dt_obj = None
        if latlon and dt_obj and es_pasada_diurna_descartada(a["sensor_bucket"], latlon[0],
                                                              latlon[1], dt_obj):
            n_diurnas += 1
            continue
        k = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
    print(f"Pasadas diurnas excluidas (criterio store._reject_daytime): {n_diurnas}; "
          f"noches-ALERTA MIROVA (vol, sensor, fecha UTC): {len(mir)}")

    filas_rec, filas_noc, filas_mec = [], [], []
    ejemplos_perdidas = []
    control_pos = None
    for vol in VOLS:
        d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json",
                           encoding="utf-8"))
        recs = d["records"]
        por_b = collections.defaultdict(list)
        for r in recs:
            b = bucket(r.get("sensor"))
            if b:
                por_b[b].append(r)
        for b in BUCKETS:
            rs = por_b[b]
            fe = [r["datetime_utc"][:10] for r in rs if r.get("datetime_utc")]
            ini, fin = (min(fe), max(fe)) if fe else ("SIN DATO", "SIN DATO")
            con_pc = [r for r in rs if (r.get("primary_cluster") or {}).get("n_pixels", 0) > 0]
            pc0 = [r for r in con_pc if (r["primary_cluster"].get("vrp_mw") or 0) == 0]
            lo, hi = ic_prop(len(pc0), len(con_pc))
            mec = collections.Counter(mecanismo(r) for r in pc0)
            frio = collections.Counter(pico_frio(r) for r in pc0)
            filas_rec.append({"volcan": vol, "sensor": b, "ventana": f"{ini}..{fin}",
                              "n_records": len(rs), "n_con_cumulo": len(con_pc),
                              "n_pc0": len(pc0),
                              "frac_pc0": round(len(pc0) / len(con_pc), 4) if con_pc else None,
                              "ic95_lo": round(lo, 4), "ic95_hi": round(hi, 4),
                              "pico_frio_si": frio.get(True, 0),
                              "pico_frio_no": frio.get(False, 0),
                              "sin_pixeles_persistidos": frio.get(None, 0)})
            for m, n in mec.most_common():
                filas_mec.append({"volcan": vol, "sensor": b, "mecanismo": m, "n": n,
                                  "frac_de_pc0": round(n / len(pc0), 3)})

            # --- noches (ventana de la referencia) ---
            noches = collections.defaultdict(lambda: {"vis": 0, "pc0": 0, "rec": 0,
                                                      "pc0_mec": []})
            for r in rs:
                f = (r.get("datetime_utc") or "")[:10]
                if not (GT_INI <= f <= GT_FIN):
                    continue
                n = noches[f]
                n["rec"] += 1
                if visible_dashboard(r, vol):
                    n["vis"] += 1
                pc = r.get("primary_cluster") or {}
                if pc.get("n_pixels", 0) > 0 and (pc.get("vrp_mw") or 0) == 0:
                    n["pc0"] += 1
                    n["pc0_mec"].append(mecanismo(r))
            n_mir = sum(1 for (v, bb, f) in mir if v == vol and bb == b)
            cub = perd = perd_pc0 = perd_sin_rec = perd_rec_no_vis = 0
            mec_perd = collections.Counter()
            for (v, bb, f), mv in mir.items():
                if v != vol or bb != b:
                    continue
                n = noches.get(f)
                if n and n["vis"] > 0:
                    cub += 1
                    if control_pos is None and vol == "Lascar" and b == "VIIRS375":
                        control_pos = (vol, b, f, mv)
                    continue
                perd += 1
                if n is None or n["rec"] == 0:
                    perd_sin_rec += 1
                elif n["pc0"] > 0:
                    perd_pc0 += 1
                    for m in set(n["pc0_mec"]):
                        mec_perd[m] += 1
                    if len(ejemplos_perdidas) < 40:
                        ejemplos_perdidas.append((vol, b, f, mv, sorted(set(n["pc0_mec"]))))
                else:
                    perd_rec_no_vis += 1
            lo2, hi2 = ic_prop(perd_pc0, n_mir)
            filas_noc.append({"volcan": vol, "sensor": b, "ventana": f"{GT_INI}..{GT_FIN}",
                              "noches_alerta_mirova": n_mir, "cubiertas_dashboard": cub,
                              "perdidas": perd, "perdidas_con_pc0": perd_pc0,
                              "perdidas_sin_record_nuestro": perd_sin_rec,
                              "perdidas_con_record_no_visible_sin_pc0": perd_rec_no_vis,
                              "frac_perdidas_pc0_sobre_alertas":
                                  round(perd_pc0 / n_mir, 4) if n_mir else None,
                              "ic95_lo": round(lo2, 4), "ic95_hi": round(hi2, 4),
                              "mecanismos_en_perdidas": "; ".join(
                                  f"{m}={k}" for m, k in mec_perd.most_common())})

    def escribir(nombre, filas):
        p = OUT / nombre
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows(filas)
        return p

    p1 = escribir("01a_pc0_records.csv", filas_rec)
    p2 = escribir("01b_pc0_noches.csv", filas_noc)
    p3 = escribir("01c_pc0_mecanismos.csv", filas_mec)

    print("\n(a1) Records con cumulo y VRP 0 por volcan y sensor (toda la serie persistida)")
    print(f"{'volcan':20s}{'sensor':9s}{'ventana':24s}{'n_rec':>6s}{'n_pc':>6s}{'pc0':>5s}"
          f"{'frac':>7s}{'IC95':>16s}{'pico<=tbg':>10s}{'pico>tbg':>9s}{'sin_pix':>8s}")
    for f in filas_rec:
        fr = "SIN DATO" if f["frac_pc0"] is None else f"{f['frac_pc0']:.3f}"
        print(f"{f['volcan']:20s}{f['sensor']:9s}{f['ventana']:24s}{f['n_records']:6d}"
              f"{f['n_con_cumulo']:6d}{f['n_pc0']:5d}{fr:>7s}"
              f"  [{f['ic95_lo']:.3f},{f['ic95_hi']:.3f}]{f['pico_frio_si']:10d}"
              f"{f['pico_frio_no']:9d}{f['sin_pixeles_persistidos']:8d}")

    print("\n(a2) Mecanismo de los pc0 (agregado por sensor sobre los 11 Tier A)")
    agg = collections.defaultdict(collections.Counter)
    for f in filas_mec:
        agg[f["sensor"]][f["mecanismo"]] += f["n"]
    for b in BUCKETS:
        tot = sum(agg[b].values())
        print(f"  {b}: total pc0={tot}")
        for m, n in agg[b].most_common():
            print(f"     {m:45s} {n:5d}  ({n / tot:.1%})" if tot else "     SIN DATO")

    print(f"\n(a3) Costo en NOCHES contra MIROVA, ventana {GT_INI}..{GT_FIN}")
    print(f"{'volcan':20s}{'sensor':9s}{'alertas':>8s}{'cubiertas':>10s}{'perdidas':>9s}"
          f"{'perd_pc0':>9s}{'perd_sinrec':>12s}{'perd_novis':>12s}{'frac_pc0':>9s}{'IC95':>16s}")
    for f in filas_noc:
        fr = "SIN DATO" if f["frac_perdidas_pc0_sobre_alertas"] is None else \
            f"{f['frac_perdidas_pc0_sobre_alertas']:.3f}"
        print(f"{f['volcan']:20s}{f['sensor']:9s}{f['noches_alerta_mirova']:8d}"
              f"{f['cubiertas_dashboard']:10d}{f['perdidas']:9d}{f['perdidas_con_pc0']:9d}"
              f"{f['perdidas_sin_record_nuestro']:12d}{f['perdidas_con_record_no_visible_sin_pc0']:12d}"
              f"{fr:>9s}  [{f['ic95_lo']:.3f},{f['ic95_hi']:.3f}]  {f['mecanismos_en_perdidas']}")
    tot = collections.Counter()
    for f in filas_noc:
        for k in ("noches_alerta_mirova", "cubiertas_dashboard", "perdidas",
                  "perdidas_con_pc0", "perdidas_sin_record_nuestro",
                  "perdidas_con_record_no_visible_sin_pc0"):
            tot[(f["sensor"], k)] += f[k]
    print("\n  Totales por sensor:")
    for b in BUCKETS:
        print(f"  {b}: alertas={tot[(b, 'noches_alerta_mirova')]} cubiertas="
              f"{tot[(b, 'cubiertas_dashboard')]} perdidas={tot[(b, 'perdidas')]} "
              f"perdidas_con_pc0={tot[(b, 'perdidas_con_pc0')]} "
              f"perdidas_sin_record={tot[(b, 'perdidas_sin_record_nuestro')]} "
              f"perdidas_con_record_no_visible_sin_pc0={tot[(b, 'perdidas_con_record_no_visible_sin_pc0')]}")

    print("\nEjemplos de noches perdidas con cumulo en 0 (vol, sensor, fecha UTC, VRP MIROVA, mecanismos):")
    for e in ejemplos_perdidas:
        print("  ", e)
    print("\nControl positivo (Lascar VIIRS375, primera noche ALERTA cubierta):", control_pos)
    # control negativo: fecha anterior a toda la serie
    k_neg = ("Lascar", "VIIRS375", "2024-12-31")
    print("Control negativo: clave", k_neg, "en mir:", k_neg in mir,
          "(debe ser False; no entra en ningun conteo)")
    print("\nTablas:", p1, p2, p3, sep="\n  ")


if __name__ == "__main__":
    main()
