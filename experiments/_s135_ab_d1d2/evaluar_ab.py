# -*- coding: utf-8 -*-
"""S135 — evalúa el A/B de D1 (`keep_peak`) x D2 (segundo pase condicionado).

Aplica, sin ajustar nada después de ver los datos, el criterio de
`docs/PREREGISTRO_AB_D1_D2_S135.md`, con la decisión de Nicolás del 2026-09-07:

  CRITERIO 1 — CERO pérdidas sobre lo que MIROVA entrega.
      noche cat-b = (volcán, fecha UTC) con alerta MIROVA VIIRS375 (CONS ∪ OCR) **de una pasada
      NOCTURNA** que el brazo CONTROL publica como detección en el cráter. FN = noches cat-b que
      el control publica y el brazo no. El umbral es 0: cualquier pérdida bloquea la adopción Y
      abre una investigación por pasada (no descarta el brazo automáticamente).

      Las pasadas diurnas se excluyen con `is_nighttime`, la MISMA función con que el pipeline
      decide qué granule mirar: comparar contra una alerta que por diseño no podemos ver sería
      fabricar un falso negativo. Son los artefactos solares de A76 (98 filas en la referencia
      de V375). Lo que NO se admite como explicación de una pérdida es «MIROVA lo revisó a
      mano»: el canal NRT que comparamos no tiene supervisión humana (regla durable desde S21),
      y aceptarlo sería aceptar un techo artificial.
  CRITERIO 2 — el brazo elimina >= 70 % de la porción ALCANZABLE del nivel base falso.
      nivel base falso = record summit V375 con cúmulo de 1 píxel, ese píxel más frío que el
      fondo global, y sin alerta de MIROVA esa noche. «Alcanzable» = la porción que llega por
      `final_hotspot_source == "test1_roi"` en el control; el resto (path contextual) no
      depende de ninguno de los dos ejes y se reporta como remanente.
  CRITERIO 3 — la paridad de magnitud no empeora.
      razón = magnitud nuestra / VRP de MIROVA, emparejando por pasada (|Δt| <= 20 min).
      La mediana agregada del brazo no puede alejarse de 1,0 más que la del control.
  DESEMPATE — entre los que cumplen, gana el más cercano al paper: D > C > B > E.

Estratifica por régimen (A83): focales = Láscar, Lastarria; nevados = los otros cuatro.
Todo conteo va con denominador y ventana (A90). Read-only.

Uso:
    python experiments/_s135_ab_d1d2/evaluar_ab.py --dir <carpeta con los artefactos bajados>

La carpeta esperada es la que produce `gh run download`: subcarpetas
`s135ab-<perfil>-<volcán>/<volcán>.json`. Si en vez de eso los JSON ya están en
`data/<perfil>/<volcán>.json`, pasar `--dir data`.
"""
import argparse
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from run_pipeline import is_nighttime  # noqa: E402  (el mismo criterio que usa el pipeline)

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
BRAZOS = [
    ("A", "_s135_ab_a_control", "control (producción de hoy)"),
    ("B", "_s135_ab_b_nokeeppeak", "keep_peak OFF"),
    ("C", "_s135_ab_c_cond", "segundo pase condicionado"),
    ("D", "_s135_ab_d_ambos", "ambos (el más fiel al paper)"),
    ("E", "_s135_ab_e_sp_off", "segundo pase apagado"),
]
CONTROL = "_s135_ab_a_control"
ORDEN_FIDELIDAD = ["_s135_ab_d_ambos", "_s135_ab_c_cond", "_s135_ab_b_nokeeppeak",
                   "_s135_ab_e_sp_off"]
VOLCANES = ["Isluga", "Lascar", "Lastarria", "PuyehueCordonCaulle", "PlanchonPeteroa",
            "Tupungatito"]
FOCALES = {"Lascar", "Lastarria"}
INNER = {"Isluga": 5, "Lascar": 5, "Lastarria": 3, "PuyehueCordonCaulle": 20,
         "PlanchonPeteroa": 3, "Tupungatito": 7}
CAP_MW = 50000.0
PAR_DT_MIN = 20
UMBRAL_C2 = 0.70


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def parse_dt(s):
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, f)
        except (ValueError, TypeError):
            pass
    return None


def cargar(base, perfil, vol):
    """Busca el JSON del brazo, en el layout de artefactos o en data/<perfil>/."""
    for cand in (os.path.join(base, f"s135ab-{perfil}-{vol}", f"{vol}.json"),
                 os.path.join(base, perfil, f"{vol}.json"),
                 os.path.join(base, f"{perfil}-{vol}", f"{vol}.json")):
        if os.path.exists(cand):
            d = json.load(open(cand, encoding="utf-8"))
            return d["records"] if isinstance(d, dict) else d
    return None


def publica_en_crater(r, inner):
    """Lo que el operador ve como detección crateriana (definición S119/S114)."""
    pc = r.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0.0
    cd = pc.get("centroid_dist_km")
    dc = r.get("distance_class")
    return (0 < vrp <= CAP_MW and cd is not None and cd <= inner
            and (not dc or dc == "summit"))


def magnitud(r):
    if r.get("f5_core_vrp_mw") is not None:
        return float(r["f5_core_vrp_mw"])
    return float((r.get("primary_cluster") or {}).get("vrp_mw") or 0.0)


def es_base_falso(r, fechas_mir, inner):
    """1 píxel + más frío que su fondo + sin alerta de MIROVA esa noche."""
    if not publica_en_crater(r, inner):
        return False
    pc = r.get("primary_cluster") or {}
    if pc.get("n_pixels") != 1 or pc.get("centroid_lat") is None:
        return False
    tbg = r.get("t_bg_k")
    ap = r.get("anomaly_pixels") or []
    if tbg is None or not ap:
        return False
    def d2(q):
        return (q["lat"] - pc["centroid_lat"]) ** 2 + (q["lon"] - pc["centroid_lon"]) ** 2
    best = min(ap, key=d2)
    if best.get("bt_k") is None or best["bt_k"] >= tbg:
        return False
    return r["datetime_utc"][:10] not in fechas_mir


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(ROOT, "data"))
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    args = ap.parse_args()

    alertas = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                                  ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
    import yaml
    _vc = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    coord = {v["name"]: (v["lat"], v["lon"]) for v in _vc["volcanoes"]}
    fechas_mir, filas_mir = defaultdict(set), defaultdict(list)
    fin_gt = ""
    n_diurnas = defaultdict(int)
    for a in alertas:
        f = a.get("fecha_utc")
        if not f or a["sensor_bucket"] != "VIIRS375":
            continue
        fin_gt = max(fin_gt, f[:10])
        # A76: una alerta de pasada diurna no puede contarse contra un pipeline night-only.
        dt_a = parse_dt(f)
        vol_a = a["volcano"]
        if dt_a is not None and vol_a in coord and not is_nighttime(*coord[vol_a], dt_a):
            n_diurnas[vol_a] += 1
            continue
        fechas_mir[a["volcano"]].add(f[:10])
        dt = parse_dt(f)
        if dt and (a.get("vrp_mw") or 0) > 0:
            filas_mir[a["volcano"]].append((dt, float(a["vrp_mw"])))

    # ---- cargar todos los brazos ----
    datos, faltan = {}, []
    for _, perfil, _ in BRAZOS:
        for vol in VOLCANES:
            recs = cargar(args.dir, perfil, vol)
            if recs is None:
                faltan.append(f"{perfil}/{vol}")
                continue
            datos[(perfil, vol)] = [r for r in recs if es_v375(r)]
    if faltan:
        print(f"FALTAN {len(faltan)} de {len(BRAZOS) * len(VOLCANES)} archivos: "
              f"{', '.join(faltan[:8])}{' …' if len(faltan) > 8 else ''}")
        if len(faltan) == len(BRAZOS) * len(VOLCANES):
            print(f"\nNo hay nada que evaluar en {args.dir}. Bajar los artefactos con:")
            print("  gh run download <run_id> --dir <destino>")
            return

    res = {"ventana_ground_truth_hasta": fin_gt, "volcanes": VOLCANES,
           "faltantes": faltan, "brazos": {},
           "alertas_diurnas_excluidas": {k: v for k, v in n_diurnas.items() if k in VOLCANES}}

    # ---- noches cat-b según el CONTROL ----
    catb = {}
    for vol in VOLCANES:
        recs = datos.get((CONTROL, vol)) or []
        noches = set()
        for r in recs:
            d = r["datetime_utc"][:10]
            if d <= fin_gt and d in fechas_mir.get(vol, set()) and publica_en_crater(r, INNER[vol]):
                noches.add(d)
        catb[vol] = noches
    res["noches_catb_control"] = {v: len(n) for v, n in catb.items()}

    # ---- base falso del control (denominador del criterio 2) ----
    base_ctrl = {}
    for vol in VOLCANES:
        recs = datos.get((CONTROL, vol)) or []
        tot = [r for r in recs if es_base_falso(r, fechas_mir.get(vol, set()), INNER[vol])]
        alc = [r for r in tot if r.get("final_hotspot_source") == "test1_roi"]
        base_ctrl[vol] = {"total": len(tot), "alcanzable": len(alc)}
    res["base_falso_control"] = base_ctrl

    print(f"A/B S135 · ventana de ground truth hasta {fin_gt} · {len(VOLCANES)} volcanes")
    print("alertas de pasadas DIURNAS excluidas del universo (A76):",
          dict(res["alertas_diurnas_excluidas"]) or "ninguna")
    print("noches cat-b (las que el control publica y MIROVA confirma):",
          {v: len(n) for v, n in catb.items()}, "\n")

    # ---- evaluar cada brazo ----
    for letra, perfil, desc in BRAZOS:
        fn_por_vol, base_por_vol, razones = {}, {}, []
        detalle_fn = []
        for vol in VOLCANES:
            recs = datos.get((perfil, vol))
            if recs is None:
                continue
            inner = INNER[vol]
            publica = {r["datetime_utc"][:10] for r in recs if publica_en_crater(r, inner)}
            perdidas = sorted(catb[vol] - publica)
            fn_por_vol[vol] = {"fn": len(perdidas), "de": len(catb[vol]), "noches": perdidas}
            for d in perdidas:
                detalle_fn.append({"volcan": vol, "fecha": d})
            base = [r for r in recs if es_base_falso(r, fechas_mir.get(vol, set()), inner)]
            base_por_vol[vol] = {
                "total": len(base),
                "alcanzable_restante": len([r for r in base
                                            if r.get("final_hotspot_source") == "test1_roi"])}
            mir = sorted(filas_mir.get(vol, []))
            for r in recs:
                if not publica_en_crater(r, inner):
                    continue
                dt = parse_dt(r["datetime_utc"])
                if dt is None:
                    continue
                cerca = [(abs((m - dt).total_seconds()), v) for m, v in mir
                         if abs((m - dt).total_seconds()) <= PAR_DT_MIN * 60]
                if not cerca:
                    continue
                _, mvrp = min(cerca)
                nuestro = magnitud(r)
                if nuestro > 0 and mvrp > 0:
                    razones.append(nuestro / mvrp)

        fn_total = sum(v["fn"] for v in fn_por_vol.values())
        alc_ctrl = sum(base_ctrl[v]["alcanzable"] for v in fn_por_vol)
        alc_rest = sum(v["alcanzable_restante"] for v in base_por_vol.values())
        elim = (1 - alc_rest / alc_ctrl) if alc_ctrl else None
        med = st.median(razones) if razones else None
        res["brazos"][perfil] = {
            "letra": letra, "descripcion": desc,
            "criterio1_fn_total": fn_total,
            "criterio1_por_volcan": fn_por_vol,
            "criterio1_detalle": detalle_fn,
            "criterio1_cumple": fn_total == 0,
            "criterio2_alcanzable_control": alc_ctrl,
            "criterio2_alcanzable_restante": alc_rest,
            "criterio2_eliminado_pct": (round(100 * elim, 1) if elim is not None else None),
            "criterio2_cumple": (elim is not None and elim >= UMBRAL_C2),
            "criterio3_razon_mediana": (round(med, 3) if med is not None else None),
            "criterio3_n_pares": len(razones),
            "base_falso_por_volcan": base_por_vol,
            "focales_vs_nevados": {
                "focales_fn": sum(v["fn"] for k, v in fn_por_vol.items() if k in FOCALES),
                "nevados_fn": sum(v["fn"] for k, v in fn_por_vol.items() if k not in FOCALES)},
        }

    # criterio 3 se juzga contra el control
    ctrl_med = res["brazos"][CONTROL]["criterio3_razon_mediana"]
    for perfil, b in res["brazos"].items():
        m = b["criterio3_razon_mediana"]
        b["criterio3_cumple"] = (
            None if (m is None or ctrl_med is None)
            else abs(m - 1.0) <= abs(ctrl_med - 1.0) + 1e-9)

    # ---- veredicto ----
    print(f"{'brazo':<26}{'FN (c1)':>9}{'elim. base falso (c2)':>24}{'razón (c3)':>13}  veredicto")
    for letra, perfil, desc in BRAZOS:
        b = res["brazos"].get(perfil)
        if not b:
            continue
        c1 = "0 ✓" if b["criterio1_cumple"] else f"{b['criterio1_fn_total']} ✗"
        c2 = (f"{b['criterio2_eliminado_pct']}%"
              f"{' ✓' if b['criterio2_cumple'] else ' ✗'}"
              if b["criterio2_eliminado_pct"] is not None else "—")
        c3 = (f"{b['criterio3_razon_mediana']}"
              f"{' ✓' if b['criterio3_cumple'] else ' ✗'}" if b["criterio3_razon_mediana"] else "—")
        if perfil == CONTROL:
            ver = "control"
        elif b["criterio1_cumple"] and b["criterio2_cumple"] and b["criterio3_cumple"]:
            ver = "CUMPLE"
        elif not b["criterio1_cumple"]:
            ver = "pierde noches → investigar cada una"
        else:
            ver = "no cumple"
        print(f"{letra} {perfil:<24}{c1:>9}{c2:>24}{c3:>13}  {ver}")

    ganador = next((p for p in ORDEN_FIDELIDAD
                    if res["brazos"].get(p, {}).get("criterio1_cumple")
                    and res["brazos"].get(p, {}).get("criterio2_cumple")
                    and res["brazos"].get(p, {}).get("criterio3_cumple")), None)
    res["ganador_por_desempate"] = ganador
    print(f"\nDesempate por fidelidad (D > C > B > E): "
          f"{ganador if ganador else 'ninguno cumple los tres criterios'}")

    # pérdidas a investigar (criterio de Nicolás: entender, no descartar)
    print("\nNoches perdidas por brazo (cada una abre una investigación, no descarta el brazo):")
    for letra, perfil, _ in BRAZOS:
        b = res["brazos"].get(perfil)
        if not b or perfil == CONTROL or not b["criterio1_detalle"]:
            continue
        print(f"  {letra}: " + ", ".join(f"{d['volcan']} {d['fecha']}"
                                         for d in b["criterio1_detalle"][:12])
              + (" …" if len(b["criterio1_detalle"]) > 12 else ""))

    p = os.path.join(args.out, "resultado_ab.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(f"\n→ {p}")


if __name__ == "__main__":
    main()
