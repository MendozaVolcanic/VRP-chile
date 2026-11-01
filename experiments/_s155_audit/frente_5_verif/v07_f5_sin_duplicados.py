# -*- coding: utf-8 -*-
"""Verificador F5, paso 7: cuanto infla F5' (V375) la doble cuenta de huellas solapadas.
Para cada record V375 pareado: conjunto F5 (mismo criterio que pipeline/f5_core.py, verificado igual en
v03) y, dentro de el, se agrupan pixeles a menos de 0,19 km (mitad del paso de nadir I-band: no pueden ser
dos muestras distintas del mismo barrido) y se conserva solo el de mayor VRP de cada grupo.
Pregunta 1: si no hubiera duplicados, F5_dedup = F5 en todas: lo veria (se imprime cuantas cambian).
Pregunta 2: denominador = pasadas V375 pareadas con MIROVA en la ventana.
LIMITE: que dos centros a <0,19 km sean la misma huella es inferencia geometrica; sin el L1B (fila y
columna del pixel) no se puede probar que vienen de barridos distintos."""
import io, json, math, os, sys, statistics
# stdout ya lo envuelve v03 al importarse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v03_fondo_cero_v375 import f5_conjunto, hav
AQUI = os.path.dirname(os.path.abspath(__file__))
pares = json.load(open(os.path.join(AQUI, "pares_remoto.json"), encoding="utf-8"))
d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
idx = {(r["datetime_utc"][:16], r["sensor"]): r for r in d["records"]}
filas = []
for f in pares:
    if f["b"] != "VIIRS375":
        continue
    r = idx[(f["t"], f["sensor"])]
    s = f5_conjunto(r["anomaly_pixels"], r["primary_cluster"])
    s = sorted(s, key=lambda p: -p["vrp_mw"])
    keep = []
    for p in s:
        if all(hav(p["lat"], p["lon"], q["lat"], q["lon"]) >= 0.19 for q in keep):
            keep.append(p)
    f5 = sum(p["vrp_mw"] for p in s); dd = sum(p["vrp_mw"] for p in keep)
    filas.append((f["t"], f["zen"], f5, dd, f["mir"], len(s), len(keep)))
cambian = [x for x in filas if x[5] != x[6]]
print("pasadas V375 pareadas=%d; con duplicado dentro del conjunto F5=%d" % (len(filas), len(cambian)))
for x in cambian:
    print("  %s cenit %4.1f  F5 %.2f -> sin duplicados %.2f (x%.2f)  MIROVA %.2f  pixeles %d -> %d" % (x[0], x[1], x[2], x[3], x[2] / x[3], x[4], x[5], x[6]))
print("banda  n  r_F5  r_dedup  (MIROVA >= 1 MW)")
for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
    e = [x for x in filas if lo <= x[1] < hi and x[4] >= 1 and x[2] > 0]
    if e:
        print("%2d-%2d %3d  %.2f  %.2f" % (lo, hi, len(e), statistics.median(x[2] / x[4] for x in e), statistics.median(x[3] / x[4] for x in e)))
