# -*- coding: utf-8 -*-
"""S131 auditoria MAGNITUD - item 5: R1 (focal) y R2 (single-pixel) siguen vivos?

POR QUE. AUDIT_S125 s0 describio dos reducciones aguas abajo de la Eq. 8 de Coppola
2016a: R1 `cluster_focal_vrp_mw` (suma un subconjunto del cluster) y R2
`apply_single_pixel_mode` (maximo en vez de suma). El encargo pide verificarlo con el
flag EFECTIVO y con un conteo sobre records recientes, no con el doc.

DEFINICIONES (A90, dentro de la afirmacion):
  - universo: records de los 11 Tier A en `data/mirova_equivalent/`, con
    `primary_cluster` presente y `pc.vrp_mw > 0`, NOCTURNOS (solar_zenith_deg >= 90 o
    ausente), ventana declarada en cada tabla (2026 completo y 2026-06-01..hoy).
  - R1 "aplicado": `pc.focal_magnitude == True` (el bloque corrio).
    R1 "con efecto": `pc.focal_degraded == True` (colapso al pixel pico) — es el unico
    efecto observable en el JSON; el recorte parcial (algunos pixeles fuera) NO deja
    rastro persistido.
  - R2 "aplicado": `pc.single_pixel_mode == True`.
    R2 "con efecto": aplicado Y `pc.n_pixels` en {2, 3} (con 1 pixel max == suma).
  - Ratio suma/maximo de R2: reconstruido desde `anomaly_pixels` (top-100 por VRP,
    lat/lon/vrp_mw por pixel) tomando los `n_pixels` pixeles mas cercanos al centroide
    del cluster; se acepta SOLO si el maximo de esos pixeles coincide con pc.vrp_mw
    (+-0.002 MW), que es la prueba de que se eligieron los pixeles correctos. Es una
    reconstruccion, no el dato: S125 la dejo SIN RESPALDO porque `per_pixel_vrp` no se
    persiste; aca se recupera con esa verificacion cruzada.
"""
import io
import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import bucket, haversine  # noqa: E402

OUT = os.path.join(HERE, "01_r1_r2_vigencia.json")
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]
VENTANAS = {"2026": ("2026-01-01", "2026-12-31"),
            "reciente_2026-06..09": ("2026-06-01", "2026-12-31")}
PITCH_KM = {"v375": 0.375, "v750": 0.75, "modis": 1.0}


def nocturno(r):
    sz = r.get("solar_zenith_deg")
    return sz is None or sz >= 90


def ratio_suma_max(r, bk):
    pc = r.get("primary_cluster") or {}
    n = int(pc.get("n_pixels") or 0)
    if n not in (2, 3):
        return None
    ap = r.get("anomaly_pixels") or []
    if len(ap) < n or pc.get("centroid_lat") is None:
        return None
    c = (pc["centroid_lat"], pc["centroid_lon"])
    near = sorted(ap, key=lambda p: haversine(c, (p["lat"], p["lon"])))[:n]
    # los n pixeles deben estar dentro de ~2 pitches del centroide (cluster 8-conexo)
    if haversine(c, (near[-1]["lat"], near[-1]["lon"])) > 2.0 * PITCH_KM[bk]:
        return None
    vals = [float(p.get("vrp_mw") or 0) for p in near]
    mx = max(vals)
    if mx <= 0 or abs(mx - float(pc.get("vrp_mw") or 0)) > 0.002:
        return None
    return sum(vals) / mx


def main():
    res = {"definicion": __doc__, "ventanas": {}}
    for wname, (w0, w1) in VENTANAS.items():
        agg = defaultdict(Counter)
        ratios = defaultdict(list)
        por_vol = defaultdict(Counter)
        for v in VOLS:
            p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
            for r in json.load(open(p, encoding="utf-8"))["records"]:
                bk = bucket(r.get("sensor"))
                if bk is None or not nocturno(r):
                    continue
                d = (r.get("datetime_utc") or "")[:10]
                if not (w0 <= d <= w1):
                    continue
                pc = r.get("primary_cluster")
                if not pc or (pc.get("vrp_mw") or 0) <= 0:
                    continue
                src = r.get("final_hotspot_source") or "?"
                key = bk
                agg[key]["n_pc"] += 1
                agg[(key, src)]["n_pc"] += 1
                por_vol[v]["n_pc"] += 1
                if pc.get("focal_magnitude"):
                    agg[key]["r1_aplicado"] += 1
                    agg[(key, src)]["r1_aplicado"] += 1
                    por_vol[v]["r1_aplicado"] += 1
                    if pc.get("focal_degraded"):
                        agg[key]["r1_degradado_a_pico"] += 1
                        agg[(key, src)]["r1_degradado_a_pico"] += 1
                        por_vol[v]["r1_degradado_a_pico"] += 1
                if pc.get("single_pixel_mode"):
                    agg[key]["r2_aplicado"] += 1
                    por_vol[v]["r2_aplicado"] += 1
                    if int(pc.get("n_pixels") or 0) in (2, 3):
                        agg[key]["r2_con_efecto_n2_3"] += 1
                        agg[(key, src)]["r2_con_efecto_n2_3"] += 1
                        por_vol[v]["r2_con_efecto_n2_3"] += 1
                        q = ratio_suma_max(r, bk)
                        if q is not None:
                            ratios[key].append(q)
                            ratios[v].append(q)
                if "corona_degraded" in pc:
                    agg[key]["corona_presente"] += 1
                if pc.get("d9_capped"):
                    agg[key]["d9_capped"] += 1
        out = {"por_sensor": {}, "por_sensor_y_path": {}, "por_volcan": {},
               "ratio_suma_sobre_max_R2": {}}
        print(f"\n=== ventana {wname} ({w0}..{w1}) nocturnas, pc.vrp_mw>0 ===")
        for bk in ("modis", "v750", "v375"):
            c = agg[bk]
            out["por_sensor"][bk] = dict(c)
            n = c["n_pc"] or 1
            print(f"  {bk:6s} n_pc={c['n_pc']:5d}  R1 aplicado={c['r1_aplicado']:5d} "
                  f"({100*c['r1_aplicado']/n:5.1f}%)  R1 degradado a pico="
                  f"{c['r1_degradado_a_pico']:5d} ({100*c['r1_degradado_a_pico']/n:5.1f}%)  "
                  f"R2 aplicado={c['r2_aplicado']:5d} ({100*c['r2_aplicado']/n:5.1f}%)  "
                  f"R2 con efecto n2-3={c['r2_con_efecto_n2_3']:5d} "
                  f"({100*c['r2_con_efecto_n2_3']/n:5.1f}%)  corona={c['corona_presente']} "
                  f"d9cap={c['d9_capped']}")
        for k, c in sorted(agg.items(), key=str):
            if isinstance(k, tuple):
                out["por_sensor_y_path"][f"{k[0]}|{k[1]}"] = dict(c)
                print(f"     {k[0]:6s} path={k[1]:12s} n={c['n_pc']:5d} R1apl={c['r1_aplicado']:5d} "
                      f"R1deg={c['r1_degradado_a_pico']:5d} R2efec={c['r2_con_efecto_n2_3']:4d}")
        for v in VOLS:
            c = por_vol[v]
            out["por_volcan"][v] = dict(c)
            n = c["n_pc"] or 1
            print(f"  {v:20s} n={c['n_pc']:5d} R1deg={c['r1_degradado_a_pico']:4d} "
                  f"({100*c['r1_degradado_a_pico']/n:4.1f}%) R2efec={c['r2_con_efecto_n2_3']:4d} "
                  f"({100*c['r2_con_efecto_n2_3']/n:4.1f}%)")
        print("  ratio suma/max reconstruido (R2 con efecto, verificado max==pc.vrp_mw):")
        for k, xs in ratios.items():
            if len(xs) >= 15:
                xs = sorted(xs)
                out["ratio_suma_sobre_max_R2"][k] = {
                    "n": len(xs), "mediana": round(st.median(xs), 3),
                    "p90": round(xs[int(0.9 * len(xs))], 3)}
                print(f"     {k:20s} n={len(xs):4d} mediana={st.median(xs):.3f} "
                      f"p90={xs[int(0.9*len(xs))]:.3f}")
            else:
                out["ratio_suma_sobre_max_R2"][k] = {"n": len(xs), "mediana": None}
        res["ventanas"][wname] = out
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
