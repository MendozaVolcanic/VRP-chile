# -*- coding: utf-8 -*-
"""S138 eje 4 (b) y (c): cuanto de lo que el operador VE depende de que la compuerta
`bt > t_bg + 3 K` NO se reaplique en el segundo paso, y cuantos records summit tienen su pixel
pico por debajo de ese margen.

Por que se puede medir sobre data/ aunque el pipeline no persista "pixeles que pasaron los
Tests 2 y 3 y cayeron solo por la compuerta": el segundo paso (`second_pass_adjacent`,
pipeline/detection_context.py) corre con el conjunto activo VACIO (flag
ENABLE_SECOND_PASS_CONDITIONED = False) y NO tiene compuerta de temperatura. Un record con
diag_n_first_pass_pixels == 0 y diag_n_second_pass_recapture > 0 cuyo cumulo cae dentro del
inner es un pixel que paso los Tests 2 y 3 (en el segundo paso, con la misma dNTI porque no
hay activos que excluir) y que el primer paso no marco. Si ademas el pixel mas caliente
persistido esta por debajo de t_bg + 3 K, la compuerta lo mato con certeza.

Que mide, por volcan y sensor:
  (b1) records visibles en el dashboard (pc.vrp > 0, summit, centroide <= inner) cuya deteccion
       viene SOLO del segundo paso sin activos (fp == 0 y sp > 0), y de esos cuantos tienen el
       pico persistido < t_bg + 3 K (certeza de compuerta).
  (b2) noches con ALERTA MIROVA (nocturnas) cubiertas UNICAMENTE por records de ese tipo: es el
       costo en noches que tendria cerrar D2 (condicionar el segundo paso) SIN quitar D22.
  (b3) margen del pico: max(bt_k de anomaly_pixels) - t_bg_k en records summit visibles,
       fraccion < 3 K, con IC 95 % bootstrap; y la metrica literal t_max_k - t_bg_k < 3 K.

Las dos preguntas del instrumento:
  P1. Si la compuerta no existiera, (b1)/(b3) darian pico < t_bg + 3 en records con fp > 0;
      hoy eso es imposible por construccion, y se comprueba (control: debe dar 0).
  P2. Si los diag no estuvieran persistidos, fp y sp serian None y el script lo reporta como
      SIN DATO en vez de contarlos como 0.
Nota A90: t_max_k es el maximo de TODA la ROI (hasta 25 km), no del crater; la metrica literal
(b3-literal) no puede ver el fenomeno y se reporta solo para dejar constancia.
"""
import collections
import csv
import io
import json
import os
import random
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
# Regimen: clasificacion del orquestador S138; coincide con experiments/_s136/
# medir_fenomeno_test1.py:26 (NEVADOS) y _s135_ab_d1d2/evaluar_ab.py:91 (FOCALES) en
# los volcanes que ambas listan.
REGIMEN = {"Lascar": "focal", "Lastarria": "focal", "Isluga": "focal",
           "PlanchonPeteroa": "intermedio",
           "Villarrica": "nevado", "Llaima": "nevado", "NevadosDeChillan": "nevado",
           "Tupungatito": "nevado", "PuyehueCordonCaulle": "nevado", "Chaiten": "nevado",
           "Copahue": "nevado"}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
BUCKETS = ["VIIRS375", "VIIRS750", "MODIS"]
MARGEN_K = 3.0


def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def visible(r, vol):
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0.0
    if not (0 < v <= 50000):
        return False
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return False
    cd = pc.get("centroid_dist_km")
    return cd is not None and cd <= INNER[vol]


def margen_pico(r):
    """Margen del pixel mas caliente persistido sobre el fondo del anillo.

    INSTRUMENTO: `anomaly_pixels` guarda solo pixeles con VRP > 0 y, cuando el Test 1
    disparo, el bloque S94 (process_viirs.py, `if final_hotspot_source == "test1"`) los
    REEMPLAZA por el footprint del Test 1 (1 pixel con keep_peak) aunque el ancla honesta
    despues rotule la fuente como ctx_cluster. En esos records el pico persistido NO es el
    pico del hot mask contextual: se devuelve None (SIN DATO). Verificado con el control P1:
    sin esta exclusion, 489 records con fp > 0 mostraban pico < t_bg + 3, imposible por
    construccion; con ella el control debe dar 0.
    """
    if r.get("triggered_test1"):
        return None
    ap = r.get("anomaly_pixels") or []
    tb = r.get("t_bg_k")
    if not ap or tb is None:
        return None
    return max((p.get("bt_k") or -999) for p in ap) - tb


def ic_prop(k, n, nb=5000, semilla=42):
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
    mir = set()
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
            continue
        mir.add((a["volcano"], a["sensor_bucket"], dt[:10]))

    filas = []
    sin_dato_diag = 0
    control_fp_pos_pico_bajo = 0     # debe ser 0: con fp>0 el pico no puede estar bajo el margen
    control_fp_pos_n = 0
    for vol in VOLS:
        d = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json",
                           encoding="utf-8"))
        por_b = collections.defaultdict(list)
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            if b:
                por_b[b].append(r)
        for b in BUCKETS:
            rs = por_b[b]
            fe = [r["datetime_utc"][:10] for r in rs if r.get("datetime_utc")]
            ventana = f"{min(fe)}..{max(fe)}" if fe else "SIN DATO"
            vis = [r for r in rs if visible(r, vol)]
            solo2p, solo2p_pico_bajo, solo2p_pico_nd = [], 0, 0
            margenes, lit_bajo, lit_n = [], 0, 0
            for r in vis:
                fp = r.get("diag_n_first_pass_pixels")
                sp = r.get("diag_n_second_pass_recapture")
                if fp is None or sp is None:
                    sin_dato_diag += 1
                    continue
                m = margen_pico(r)
                if m is not None:
                    margenes.append(m)
                if r.get("t_max_k") is not None and r.get("t_bg_k") is not None:
                    lit_n += 1
                    if r["t_max_k"] - r["t_bg_k"] < MARGEN_K:
                        lit_bajo += 1
                if fp > 0:
                    control_fp_pos_n += 1
                    if m is not None and m < MARGEN_K and r.get("final_hotspot_source") == "ctx_cluster":
                        control_fp_pos_pico_bajo += 1
                if fp == 0 and sp > 0 and r.get("final_hotspot_source") == "ctx_cluster":
                    solo2p.append(r)
                    if m is None:
                        solo2p_pico_nd += 1
                    elif m < MARGEN_K:
                        solo2p_pico_bajo += 1
            # noches MIROVA cubiertas solo por records "solo segundo paso"
            noches_vis = collections.defaultdict(lambda: {"otro": 0, "solo2p": 0})
            ids_solo2p = {id(r) for r in solo2p}
            for r in vis:
                f = (r.get("datetime_utc") or "")[:10]
                if not (GT_INI <= f <= GT_FIN):
                    continue
                noches_vis[f]["solo2p" if id(r) in ids_solo2p else "otro"] += 1
            n_mir = sum(1 for (v, bb, f) in mir if v == vol and bb == b)
            cub = cub_solo2p = 0
            for (v, bb, f) in mir:
                if v != vol or bb != b:
                    continue
                n = noches_vis.get(f)
                if n and (n["otro"] + n["solo2p"]) > 0:
                    cub += 1
                    if n["otro"] == 0:
                        cub_solo2p += 1
            lo, hi = ic_prop(len(solo2p), len(vis))
            lo2, hi2 = ic_prop(cub_solo2p, n_mir)
            nb = sum(1 for m in margenes if m < MARGEN_K)
            lo3, hi3 = ic_prop(nb, len(margenes))
            filas.append({
                "volcan": vol, "regimen": REGIMEN[vol], "sensor": b, "ventana": ventana,
                "n_visibles": len(vis),
                "vis_solo_2do_paso": len(solo2p),
                "frac_solo_2do_paso": round(len(solo2p) / len(vis), 4) if vis else None,
                "ic95_lo": round(lo, 4), "ic95_hi": round(hi, 4),
                "solo2p_pico_bajo_margen": solo2p_pico_bajo,
                "solo2p_pico_sin_pixeles": solo2p_pico_nd,
                "ventana_mirova": f"{GT_INI}..{GT_FIN}",
                "noches_alerta_mirova": n_mir, "cubiertas": cub,
                "cubiertas_solo_por_2do_paso": cub_solo2p,
                "frac_noches_solo_2do_paso": round(cub_solo2p / n_mir, 4) if n_mir else None,
                "ic95n_lo": round(lo2, 4), "ic95n_hi": round(hi2, 4),
                "n_con_pico": len(margenes), "pico_bajo_3K": nb,
                "frac_pico_bajo_3K": round(nb / len(margenes), 4) if margenes else None,
                "ic95p_lo": round(lo3, 4), "ic95p_hi": round(hi3, 4),
                "mediana_margen_K": round(sorted(margenes)[len(margenes) // 2], 2) if margenes else None,
                "literal_tmax_menos_tbg_bajo_3K": lit_bajo, "literal_n": lit_n,
            })

    p = OUT / "02_compuerta_margen.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    print(f"Records visibles sin diag fp/sp persistidos (SIN DATO): {sin_dato_diag}")
    print(f"Control P1: records visibles ctx con fp>0 = {control_fp_pos_n}; de ellos con pico "
          f"< t_bg+3 = {control_fp_pos_pico_bajo} (debe ser 0: la compuerta del 1er paso lo impide)")
    print("\n(b1) Records VISIBLES cuya deteccion viene solo del 2do paso sin activos (fp=0, sp>0)")
    print(f"{'volcan':20s}{'reg':11s}{'sensor':9s}{'n_vis':>6s}{'solo2p':>7s}{'frac':>7s}{'IC95':>16s}"
          f"{'pico<3K':>8s}{'sin_pix':>8s}")
    for f in filas:
        fr = "SIN DATO" if f["frac_solo_2do_paso"] is None else f"{f['frac_solo_2do_paso']:.3f}"
        print(f"{f['volcan']:20s}{f['regimen']:11s}{f['sensor']:9s}{f['n_visibles']:6d}"
              f"{f['vis_solo_2do_paso']:7d}{fr:>7s}  [{f['ic95_lo']:.3f},{f['ic95_hi']:.3f}]"
              f"{f['solo2p_pico_bajo_margen']:8d}{f['solo2p_pico_sin_pixeles']:8d}")
    print(f"\n(b2) Noches ALERTA MIROVA ({GT_INI}..{GT_FIN}) cubiertas UNICAMENTE por records solo-2do-paso")
    print(f"{'volcan':20s}{'sensor':9s}{'alertas':>8s}{'cubiertas':>10s}{'solo2p':>7s}{'frac':>7s}{'IC95':>16s}")
    tot = collections.Counter()
    for f in filas:
        fr = "SIN DATO" if f["frac_noches_solo_2do_paso"] is None else f"{f['frac_noches_solo_2do_paso']:.3f}"
        print(f"{f['volcan']:20s}{f['sensor']:9s}{f['noches_alerta_mirova']:8d}{f['cubiertas']:10d}"
              f"{f['cubiertas_solo_por_2do_paso']:7d}{fr:>7s}  [{f['ic95n_lo']:.3f},{f['ic95n_hi']:.3f}]")
        tot[(f["sensor"], "n")] += f["noches_alerta_mirova"]
        tot[(f["sensor"], "c")] += f["cubiertas"]
        tot[(f["sensor"], "s")] += f["cubiertas_solo_por_2do_paso"]
    for b in BUCKETS:
        n, c, s = tot[(b, "n")], tot[(b, "c")], tot[(b, "s")]
        lo, hi = ic_prop(s, n)
        print(f"  {b}: alertas={n} cubiertas={c} solo_2do_paso={s} "
              f"({s / n:.1%} de las alertas, IC95 [{lo:.3f},{hi:.3f}])" if n else f"  {b}: SIN DATO")
    print("\n(b3) Margen del pico persistido (max bt_k de anomaly_pixels - t_bg_k) en records visibles")
    print(f"{'volcan':20s}{'reg':11s}{'sensor':9s}{'n_pico':>7s}{'<3K':>5s}{'frac':>7s}{'IC95':>16s}"
          f"{'med_K':>7s}{'literal<3K':>11s}{'lit_n':>6s}")
    for f in filas:
        fr = "SIN DATO" if f["frac_pico_bajo_3K"] is None else f"{f['frac_pico_bajo_3K']:.3f}"
        md = "SIN DATO" if f["mediana_margen_K"] is None else f"{f['mediana_margen_K']:.2f}"
        print(f"{f['volcan']:20s}{f['regimen']:11s}{f['sensor']:9s}{f['n_con_pico']:7d}{f['pico_bajo_3K']:5d}"
              f"{fr:>7s}  [{f['ic95p_lo']:.3f},{f['ic95p_hi']:.3f}]{md:>7s}"
              f"{f['literal_tmax_menos_tbg_bajo_3K']:11d}{f['literal_n']:6d}")
    # agregado por regimen y sensor
    print("\n(b3-agregado) por regimen y sensor: fraccion de records visibles con pico < t_bg + 3 K")
    agg = collections.defaultdict(lambda: [0, 0])
    for f in filas:
        a = agg[(f["regimen"], f["sensor"])]
        a[0] += f["pico_bajo_3K"]
        a[1] += f["n_con_pico"]
    for k in sorted(agg):
        nb, n = agg[k]
        lo, hi = ic_prop(nb, n)
        print(f"  {k[0]:11s}{k[1]:9s} {nb:5d}/{n:5d} = {nb / n:.3f}  IC95 [{lo:.3f},{hi:.3f}]" if n
              else f"  {k[0]:11s}{k[1]:9s} SIN DATO")
    print("\nTabla:", p)


if __name__ == "__main__":
    main()
