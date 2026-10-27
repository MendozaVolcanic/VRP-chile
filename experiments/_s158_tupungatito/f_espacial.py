# -*- coding: utf-8 -*-
"""S158. Eje espacial (A61) de la comparación: ¿publicamos el mismo objeto que MIROVA en las pasadas pareadas?
Y dónde están las dos anomalías lejanas del 28 y 29 de septiembre.

POR QUÉ: un déficit de magnitud puede venir de medir otro objeto (otro píxel, otra celda). La tabla de MIROVA
trae la distancia SIN acimut y medida desde SU punto de referencia (el centro de la grilla del KMZ,
mirova_center en volcanoes.yaml, a 4,9 km del cráter; S65), cuantizada a su grilla (D15). Por eso sólo se puede
comparar radio contra radio desde el mismo punto: si los radios difieren mucho, es otro objeto; si coinciden, es
compatible (A93, A107: una cota de distancia escalar no identifica el objeto).

Uso: python -I f_espacial.py
"""
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]


def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def rumbo(a, b, c, d):
    y = math.sin(math.radians(d - b)) * math.cos(math.radians(c))
    x = (math.cos(math.radians(a)) * math.sin(math.radians(c))
         - math.sin(math.radians(a)) * math.cos(math.radians(c)) * math.cos(math.radians(d - b)))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


vol = next(v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
           if v["name"] == "Tupungatito")
mc = (vol["mirova_center_lat"], vol["mirova_center_lon"])
vent = (vol["vent_lat"], vol["vent_lon"])
recs = {(r["sensor"], r["datetime_utc"]): r
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / "Tupungatito.json", encoding="utf-8"))["records"]}
d = json.load(open(AQUI / "d_pasadas_salida.json", encoding="utf-8"))["pasadas"]
L = []
P = L.append
P(f"centro MIROVA {mc}, cráter (vent) {vent}: {hav(*mc, *vent):.2f} km, rumbo {rumbo(*mc, *vent):.0f}°")
dif, difp = [], []
for f in d:
    r = recs[(f["sensor"], f["pasada"])]
    pc = r.get("primary_cluster") or {}
    if pc.get("centroid_lat") is None:
        continue
    rc = hav(*mc, pc["centroid_lat"], pc["centroid_lon"])
    pix = [p for p in r["anomaly_pixels"] if p["dist_km"] <= 7]
    hp = max(pix, key=lambda p: p["bt_k"]) if pix else None
    rp = hav(*mc, hp["lat"], hp["lon"]) if hp else None
    dif.append(rc - f["dist_M_tabla"])
    if rp is not None:
        difp.append(rp - f["dist_M_tabla"])
ad = sorted(abs(x) for x in dif)
P(f"pasadas pareadas con la tabla (d_pasadas): {len(dif)}")
P(f"radio desde el centro MIROVA: nuestro centroide menos el de la tabla: mediana {st.median(dif):+.2f} km; "
  f"|dif| mediana {st.median(ad):.2f}, p90 {ad[9 * len(ad) // 10]:.2f}, máx {ad[-1]:.2f}; |dif| <= 1 km en "
  f"{sum(1 for x in ad if x <= 1)} de {len(ad)}")
adp = sorted(abs(x) for x in difp)
P(f"lo mismo con nuestro píxel más caliente: mediana {st.median(difp):+.2f} km; |dif| mediana {st.median(adp):.2f}, "
  f"p90 {adp[9 * len(adp) // 10]:.2f}")
P(f"distancias de la tabla en esas pasadas (km, cuantizadas, D15): "
  f"{sorted(set(round(f['dist_M_tabla'], 2) for f in d))}")
P("")
P("las dos anomalías lejanas (nuestro record de la misma pasada):")
for k in (("VIIRS_SNPP", "2026-09-28 05:18"), ("VIIRS_SNPP", "2026-09-29 04:54")):
    r = recs[k]
    pc = r["primary_cluster"]
    P(f"  {k[1]} {k[0]}: centroide ({pc['centroid_lat']:.4f}, {pc['centroid_lon']:.4f}), "
      f"{hav(*vent, pc['centroid_lat'], pc['centroid_lon']):.2f} km del cráter rumbo "
      f"{rumbo(*vent, pc['centroid_lat'], pc['centroid_lon']):.0f}°, {hav(*mc, pc['centroid_lat'], pc['centroid_lon']):.2f} km "
      f"del centro MIROVA; VRP {pc['vrp_mw']} MW, {pc['n_pixels']} píxel, clase {r['distance_class']}, "
      f"t_max {r.get('t_max_k')} K, t_bg {r.get('t_bg_k')} K")
txt = "\n".join(L)
print(txt)
(AQUI / "f_espacial_salida.txt").write_text(txt + "\n", encoding="utf-8")
