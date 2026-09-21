# -*- coding: utf-8 -*-
"""S149. Los cumulos V375 que cambian de lugar mas de 500 m entre el control B y el brazo F, CON
DIRECCION: rumbo desde el ancla de deteccion en cada brazo, distancia al ancla, y separacion al cumulo
de referencia del volcan (mediana de las positivas publicadas por ambos brazos sin moverse)."""
import json, math, sys, io, collections, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
T = json.loads((AQUI.parent / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
import yaml
V = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]} if isinstance(yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8")), dict) else {}
def hav(a, b, c, d):
    p = math.radians; x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))
def rumbo(a, b, c, d):
    p = math.radians; y = math.sin(p(d - b)) * math.cos(p(c)); x = math.cos(p(a)) * math.sin(p(c)) - math.sin(p(a)) * math.cos(p(c)) * math.cos(p(d - b))
    g = (math.degrees(math.atan2(y, x)) + 360) % 360
    return "N NE E SE S SO O NO".split()[int((g + 22.5) // 45) % 8], g
pares = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    if b != "VIIRS375": continue
    x, y = v[B], v[F]
    if x["pub"] and y["pub"] and x["pc_lat"] is not None and y["pc_lat"] is not None:
        pares.append(dict(vol=vol, dt=dt, lab=x["lab"], mov=hav(x["pc_lat"], x["pc_lon"], y["pc_lat"], y["pc_lon"]), x=x, y=y))
print("pares V375 publicados por ambos brazos con posicion:", len(pares), "| se mueven mas de 0,5 km:", sum(p["mov"] > .5 for p in pares))
# referencia por volcan: mediana de posiciones de positivas que NO se mueven
ref = {}
for vol in {p["vol"] for p in pares}:
    s = [p for p in pares if p["vol"] == vol and p["lab"] == "pos" and p["mov"] <= .05]
    if len(s) >= 3: ref[vol] = (st.median(p["x"]["pc_lat"] for p in s), st.median(p["x"]["pc_lon"] for p in s), len(s))
for p in sorted([p for p in pares if p["mov"] > .5], key=lambda p: (p["vol"], p["dt"])):
    x, y = p["x"], p["y"]; r = ref.get(p["vol"])
    rm = rumbo(x["pc_lat"], x["pc_lon"], y["pc_lat"], y["pc_lon"])[0]
    sB = hav(x["pc_lat"], x["pc_lon"], r[0], r[1]) if r else float("nan"); sF = hav(y["pc_lat"], y["pc_lon"], r[0], r[1]) if r else float("nan")
    print("  %-20s %s %-10s | mueve %.2f km hacia %-2s | dist ancla B %.2f F %.2f | a la posicion tipica de alerta: B %.2f F %.2f | MW B %.3f F %.3f | ref %s" % (
        p["vol"], p["dt"], p["lab"], p["mov"], rm, x["pc_dist"], y["pc_dist"], sB, sF, x["disp"] or 0, y["disp"] or 0, x["vrp_ref"]))
m = [p for p in pares if p["mov"] > .5 and p["vol"] in ref]
ac = sum(1 for p in m if hav(p["y"]["pc_lat"], p["y"]["pc_lon"], *ref[p["vol"]][:2]) < hav(p["x"]["pc_lat"], p["x"]["pc_lon"], *ref[p["vol"]][:2]))
print("\nDe los que se mueven y tienen posicion tipica: F queda MAS CERCA de la posicion tipica de alerta en %d de %d" % (ac, len(m)))
print("posicion tipica (n de positivas quietas):", {k: v[2] for k, v in ref.items()})
