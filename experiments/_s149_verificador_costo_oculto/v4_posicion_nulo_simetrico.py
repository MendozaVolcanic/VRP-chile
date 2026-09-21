# -*- coding: utf-8 -*-
"""Verificador S149, seccion 4. c1 mide la misma noche con MIN sobre los cumulos positivos de la noche y el
nulo con MEDIANA sobre todas las otras noches: estadisticos distintos. Aca el nulo usa el MISMO estadistico:
min sobre los cumulos positivos de UNA otra noche del mismo volcan, promediado sobre todas las otras noches
(mediana de esos min) y tambien sorteando una. Igual para los negativos limpios. Ademas: 141 contra 109."""
import json, math, sys, io, collections, random, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parent
T = json.loads((EXP / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
def hav(a, b, c, d):
    p = math.radians; x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))
R = []
for k, v in T.items():
    vol, b, dt = k.split("|")
    if b == "VIIRS375": R.append(dict(vol=vol, dt=dt, n=dt[:10], lab=v[B]["lab"], pB=v[B]["pub"], pF=v[F]["pub"], lat=v[B]["pc_lat"], lon=v[B]["pc_lon"], dist=v[B]["pc_dist"]))
pos = collections.defaultdict(list)
for r in R:
    if r["lab"] == "pos" and r["pB"] and r["lat"] is not None: pos[(r["vol"], r["n"])].append(r)
np_ = {(r["vol"], r["n"]) for r in R if r["lab"] == "pos"}
si = [r for r in R if r["lab"] == "sin_info" and (r["vol"], r["n"]) in np_ and r["pB"] and r["lat"] is not None]
ap = [r for r in si if not r["pF"]]; sv = [r for r in si if r["pF"]]
neg = [r for r in R if r["lab"] == "neg_limpio" and r["pB"] and not r["pF"] and r["lat"] is not None]
mn = lambda r, c: min(hav(r["lat"], r["lon"], x["lat"], x["lon"]) for x in c)
def linea(nom, ds):
    ds = [d for d in ds if d is not None]
    print("  %-52s n %3d | mediana %.2f | <=0.4: %2d (%.0f %%) | >2: %2d (%.0f %%)" % (nom, len(ds), st.median(ds), sum(d <= .4 for d in ds), 100 * sum(d <= .4 for d in ds) / len(ds), sum(d > 2 for d in ds), 100 * sum(d > 2 for d in ds) / len(ds)))
def otras(r):
    return [c for (v, n), c in pos.items() if v == r["vol"] and n != r["n"]]
print("Estadistico unico: MIN sobre los cumulos positivos de una noche")
linea("apagadas, MISMA noche (replica de c1)", [mn(r, pos[(r["vol"], r["n"])]) if (r["vol"], r["n"]) in pos else None for r in ap])
linea("apagadas, OTRA noche (mediana de los min por noche)", [st.median(mn(r, c) for c in otras(r)) if otras(r) else None for r in ap])
rnd = random.Random(149); meds = []
for i in range(500):
    ds = [mn(r, rnd.choice(otras(r))) for r in ap if otras(r)]; meds.append(st.median(ds))
print("  apagadas, UNA otra noche al azar, 500 sorteos: mediana de medianas %.2f | p5 %.2f | p95 %.2f" % (st.median(meds), sorted(meds)[25], sorted(meds)[475]))
linea("sobreviven, MISMA noche", [mn(r, pos[(r["vol"], r["n"])]) if (r["vol"], r["n"]) in pos else None for r in sv])
linea("sobreviven, OTRA noche (mediana de los min)", [st.median(mn(r, c) for c in otras(r)) if otras(r) else None for r in sv])
allpos = collections.defaultdict(list)
for (v, n), c in pos.items(): allpos[v].append(c)
linea("neg limpios apagados, mediana de los min por noche", [st.median(mn(r, c) for c in allpos[r["vol"]]) if allpos[r["vol"]] else None for r in neg])
print("\nLa separacion es casi la distancia al ancla? correlacion simple en las apagadas:")
xs = [(mn(r, pos[(r["vol"], r["n"])]), r["dist"]) for r in ap if (r["vol"], r["n"]) in pos and r["dist"] is not None]
mx, my = st.mean(a for a, _ in xs), st.mean(b for _, b in xs)
cor = sum((a - mx) * (b - my) for a, b in xs) / math.sqrt(sum((a - mx) ** 2 for a, _ in xs) * sum((b - my) ** 2 for _, b in xs))
print("  r de Pearson sep contra pc_dist: %.3f (n %d) | mediana |sep - dist| %.2f km" % (cor, len(xs), st.median(abs(a - b) for a, b in xs)))
print("\nMezcla de volcanes: apagadas", dict(collections.Counter(r["vol"] for r in ap)))
print("                   neg limpios apagados", dict(collections.Counter(r["vol"] for r in neg)))
print("neg limpios apagados SOLO en los volcanes de las apagadas, ponderado igual? por volcan (mediana de min):")
for v in sorted({r["vol"] for r in ap}):
    a = [mn(r, pos[(r["vol"], r["n"])]) for r in ap if r["vol"] == v and (r["vol"], r["n"]) in pos]
    b = [st.median(mn(r, c) for c in allpos[v]) for r in neg if r["vol"] == v and allpos[v]]
    print("   %-20s apagadas n %2d med %s | neg limpios apagados n %2d med %s" % (v, len(a), "%.2f" % st.median(a) if a else "-", len(b), "%.2f" % st.median(b) if b else "-"))
