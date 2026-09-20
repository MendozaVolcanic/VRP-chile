# -*- coding: utf-8 -*-
"""V-02: 'en MODIS el pipeline encuentra el crater el 90 %' sin tasa base.
Unidad: pasada MODIS nocturna nuestra (record), pareada por volcan+fecha UTC con la referencia MODIS del CSV.
  positivas = hay ALERTA_TERMICA(_OCR) MODIS esa fecha; negativas limpias = hay filas MODIS esa fecha y TODAS son RUTINA.
  'encuentra el crater' = primary_cluster con vrp>0 y centroid_dist_km <= inner del volcan.
(1) roto? si el pareo fallara, positivas=0 y se imprime. (2) muerto? se mide tambien v375, donde se espera una brecha mayor entre positivas y negativas;
    si las dos tasas fueran identicas en todos los sensores el predicado no discriminaria nada."""
import io, sys
from collections import defaultdict
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
INNER = {"Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4, "Tupungatito": 7, "PuyehueCordonCaulle": 20}
D = cargar(); REF = referencia()
tipos = defaultdict(set)
for f in REF: tipos[(f["vol"], f["fecha"], f["b"])].add(f["tipo"])
def noche(r):
    sz = r.get("solar_zenith_deg"); return sz is None or sz >= 90
for tramo in (("2026-01-29", "2026-08-28"), ("2026-08-29", "2026-09-19")):
    for b in ("modis", "v750", "v375"):
        tot = defaultdict(lambda: [0, 0, 0]); porvol = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        for v in VOLS:
            inn = INNER.get(v, 5)
            for r in D[v]:
                f = r["datetime_utc"][:10]
                if not (tramo[0] <= f <= tramo[1]) or bucket(r["sensor"]) != b or not noche(r): continue
                t = tipos.get((v, f, b))
                if not t: continue
                clase = "pos" if any(x.startswith("ALERTA") for x in t) else "neg" if t == {"RUTINA"} else "otro"
                pc = r.get("primary_cluster") or {}
                ok = (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inn
                vis = ok and r.get("distance_class") == "summit"
                tot[clase][0] += 1; tot[clase][1] += ok; tot[clase][2] += vis
                porvol[v][clase][0] += 1; porvol[v][clase][1] += ok
        print(tramo, b, {k: f"n={a} crater={c} ({100*c/a:.1f}%) crater_y_summit={s} ({100*s/a:.1f}%)" for k, (a, c, s) in tot.items() if a})
        if b == "modis":
            for v in VOLS:
                p, n = porvol[v]["pos"], porvol[v]["neg"]
                print("     ", v, "pos", p, f"{100*p[1]/p[0]:.0f}%" if p[0] else "SIN DATO", "| neg", n, f"{100*n[1]/n[0]:.0f}%" if n[0] else "SIN DATO")
