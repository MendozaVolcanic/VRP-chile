# -*- coding: utf-8 -*-
"""A61 PCC 2026-10-10 05:54: posicion de cada pixel de la sombra (V750) y de K (V375), distancias a los puntos de
referencia, y compatibilidad con la Distancia_km cuantizada de MIROVA (D15: sqrt(i^2+j^2)*celda).
Uso: python -I s02_geometria.py <worktree>  -> imprime y escribe salidas/s02_geometria.json"""
import json, math, sys
from pathlib import Path
import numpy as np
from pyproj import Transformer

WT = Path(sys.argv[1]); OUT = Path(__file__).resolve().parents[1] / "salidas"
utm = Transformer.from_crs("EPSG:4326", "EPSG:32718", always_xy=True)
def xy(lat, lon):
    x, y = utm.transform(lon, lat); return x / 1000.0, y / 1000.0
def d(a, b):
    ax, ay = xy(*a); bx, by = xy(*b); return math.hypot(ax - bx, ay - by)

import yaml
vs = yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8")); vs = vs.get("volcanoes", vs) if isinstance(vs, dict) else vs
v = next(x for x in vs if x["name"] == "PuyehueCordonCaulle")
REF = {"vent (ancla get_detection_anchor)": (v["vent_lat"], v["vent_lon"]),
       "mirova_center (KMZ)": (v["mirova_center_lat"], v["mirova_center_lon"]),
       "lat/lon nominal": (v["lat"], v["lon"]),
       "lacolito SE segun F60/BEYOND (-40.582,-72.131)": (-40.582, -72.131)}
print("Referencias:", {k: v_ for k, v_ in REF.items()})
print(f"vent -> mirova_center: {d(REF['vent (ancla get_detection_anchor)'], REF['mirova_center (KMZ)']):.3f} km")
cx, cy = xy(*REF["mirova_center (KMZ)"])
vx, vy = xy(*REF["vent (ancla get_detection_anchor)"])
print(f"vent respecto de mirova_center (UTM 18S): dE={vx-cx:+.3f} km, dN={vy-cy:+.3f} km")

def recs(path):
    return json.load(open(WT / path, encoding="utf-8"))["records"]
CASOS = [("sombra V750", "data/experimental_v2/PuyehueCordonCaulle.json", "VIIRS_NOAA21_750", 0.75, 7.83),
         ("sombra V375", "data/experimental_v2/PuyehueCordonCaulle.json", "VIIRS_NOAA21", 0.375, 7.73),
         ("K V375", "data/mirova_equivalent/PuyehueCordonCaulle.json", "VIIRS_NOAA21", 0.375, 7.73)]
res = {"refs": REF}
for nom, path, sen, celda, dmir in CASOS:
    r = next(x for x in recs(path) if x["sensor"] == sen and x["datetime_utc"] == "2026-10-10 05:54")
    pc = r["primary_cluster"]
    print(f"\n== {nom} ({sen}); primary_cluster n={pc['n_pixels']} vrp={pc['vrp_mw']} centroide=({pc['centroid_lat']},{pc['centroid_lon']}) dist_ancla={pc['centroid_dist_km']}")
    # la cuantizacion de MIROVA: candidatos i,j enteros con sqrt(i^2+j^2)*celda = dmir (+-0.005)
    cands = [(i, j) for i in range(0, 40) for j in range(0, 40) if abs(math.hypot(i, j) * celda - dmir) < 0.006]
    print(f"   MIROVA {dmir} km = celdas (|i|,|j|) en {sorted(set(tuple(sorted(c)) for c in cands))} (celda {celda} km)")
    filas = []
    pts = [(p["lat"], p["lon"], p.get("vrp_mw"), p.get("bt_k")) for p in (r.get("anomaly_pixels") or [])]
    pts.append((pc["centroid_lat"], pc["centroid_lon"], pc["vrp_mw"], None))
    for k, (la, lo, vrp, bt) in enumerate(pts):
        x, y = xy(la, lo)
        dd = {rk: round(d((la, lo), rv), 3) for rk, rv in REF.items()}
        de, dn = x - cx, y - cy
        ci, cj = de / celda, dn / celda
        qi, qj = round(ci), round(cj)
        dq = math.hypot(qi, qj) * celda
        tag = "centroide" if k == len(pts) - 1 else f"px{k}"
        filas.append({"id": tag, "lat": la, "lon": lo, "vrp_mw": vrp, "bt_k": bt, **dd,
                      "dE_km": round(de, 3), "dN_km": round(dn, 3), "celdas_E_N": [round(ci, 2), round(cj, 2)],
                      "dist_cuantizada_km": round(dq, 3)})
        print(f"   {tag:9s} ({la:.5f},{lo:.5f}) vrp={vrp} bt={bt} | " +
              " | ".join(f"{rk.split(' ')[0]} {val:.2f}" for rk, val in dd.items()) +
              f" | dE {de:+.2f} dN {dn:+.2f} km = celdas ({ci:+.2f},{cj:+.2f}) -> cuantizada {dq:.3f} km")
    res[nom] = filas
(OUT / "s02_geometria.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
