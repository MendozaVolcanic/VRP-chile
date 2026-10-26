# -*- coding: utf-8 -*-
"""Verificador: recomputo el veredicto con mi propia implementacion (vectorizada, otro flujo de numeros aleatorios)
y mido la sensibilidad: x = 0, 1, 2, 3 con n = 390; n = 400 (contando las 10 no evaluables en el denominador);
Clopper-Pearson y Wilson de 2/390; y la lectura de la cota conservadora.
Pregunta 1: si la regla del autor estuviera mal implementada (por ejemplo IC de la parte otros solo), mi IC
diferiria en mas que el ruido de Monte Carlo (~1 unidad). Pregunta 2: control positivo: con x = 40 debe dar REFUTA y
con x = 0 CONFIRMA (fronteras de la tabla de planificacion del §3)."""
import json, sys, math
from pathlib import Path
import numpy as np
D = Path(sys.argv[1])
F = json.loads((D / "filas_lote_s159_modis_fisica.json").read_text(encoding="utf-8"))["filas"]
print("filas:", len(F), "clases:", {c: sum(1 for x in F if x["c"] == c) for c in sorted({x["c"] for x in F})})
def de_otros_arr(sel, cls):
    # sel: array de indices por clase ya remuestreados; cls: filas
    w = np.array([x["w"] for x in cls]); K = np.array([bool(x["K"]) for x in cls]); X = np.array([bool(x["X"]) for x in cls])
    c = np.array([x["c"] for x in cls])
    bp = (w * ((c == "pos_bajo") & K & ~X))[sel].sum(axis=1)
    bg = (w * ((c == "pos_bajo") & ~K & X))[sel].sum(axis=1)
    ne = (w * ((c == "neg_pub") & X & ~K))[sel].sum(axis=1)
    na = (w * ((c == "neg_pub") & K & ~X))[sel].sum(axis=1)
    return (bp - bg) + (ne - na)
pb = [x for x in F if x["c"] == "pos_bajo"]; npb = [x for x in F if x["c"] == "neg_pub"]
punto = sum(x["w"] for x in pb if x["K"] and not x["X"]) - sum(x["w"] for x in pb if not x["K"] and x["X"]) + sum(x["w"] for x in npb if x["X"] and not x["K"]) - sum(x["w"] for x in npb if x["K"] and not x["X"])
print(f"DeltaE_otros punto (mi calculo): {punto:+.2f} (el autor declara -44,0)")
R = 20000
rng = np.random.default_rng(20261024)   # OTRA semilla a proposito
ipb = rng.integers(0, len(pb), (R, len(pb))); inp = rng.integers(0, len(npb), (R, len(npb)))
de = de_otros_arr(ipb, pb) + de_otros_arr(inp, npb)
print(f"DeltaE_otros bootstrap (mi flujo): IC [{np.percentile(de, 2.5):+.2f}; {np.percentile(de, 97.5):+.2f}] (autor: [-59,50; -29,50])")
N = 5055
def ver(x, n):
    p = rng.beta(x + .5, n - x + .5, R)
    t = de + N * p
    lo, hi = np.percentile(t, [2.5, 97.5])
    v = "CONFIRMA" if hi < 0 else ("REFUTA" if lo > 0 else "INDECIDIBLE")
    return lo, hi, v, -44.0 + N * x / n
for x, n in ((2, 390), (0, 390), (1, 390), (3, 390), (2, 400), (0, 388), (2, 388), (7, 390), (8, 390), (40, 400), (0, 400)):
    lo, hi, v, pt = ver(x, n)
    print(f"  x={x:>2} n={n}: punto {pt:+.1f} IC [{lo:+.1f}; {hi:+.1f}] -> {v}")
# binomial exacta para 2/390 (Clopper-Pearson) y Wilson, en pasadas del marco
from math import comb
def cp(x, n, a=0.05):
    # inversion por biseccion de la binomial acumulada
    def cdf(p, k): return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))
    def bis(f, lo, hi):
        for _ in range(200):
            m = (lo+hi)/2
            if f(m) > 0: lo = m
            else: hi = m
        return (lo+hi)/2
    # bis busca la raiz de f decreciente en p: P(X>=x) crece con p, asi que se usa su negativo
    low = 0.0 if x == 0 else bis(lambda p: a/2 - (1 - cdf(p, x-1)), 0, 1)   # P(X>=x) = a/2
    upp = bis(lambda p: cdf(p, x) - a/2, 0, 1)                               # P(X<=x) = a/2 (decreciente)
    return low, upp
lo, hi = cp(2, 390)
print(f"Clopper-Pearson 2/390: [{lo:.4f}; {hi:.4f}] -> en pasadas del marco [{N*lo:.0f}; {N*hi:.0f}]; punto {2/390:.4f} ({N*2/390:.1f} pasadas)")
z = 1.96; n = 390; p = 2/n; d = 1 + z*z/n
wl = (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d; wu = (p + z*z/(2*n) + z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d
print(f"Wilson 2/390: [{wl:.4f}; {wu:.4f}] -> marco [{N*wl:.0f}; {N*wu:.0f}]; cota conservadora = {np.percentile(de, 97.5):+.1f} + {N*wu:.1f} = {np.percentile(de, 97.5) + N*wu:+.1f} (autor +64,0)")
# cuantiles de la Beta de Jeffreys sola
pj = rng.beta(2.5, 388.5, 200000)
print(f"Jeffreys Beta(2.5, 388.5): media {pj.mean():.4f}, IC [{np.percentile(pj, 2.5):.4f}; {np.percentile(pj, 97.5):.4f}] -> marco [{N*np.percentile(pj, 2.5):.0f}; {N*np.percentile(pj, 97.5):.0f}]")
