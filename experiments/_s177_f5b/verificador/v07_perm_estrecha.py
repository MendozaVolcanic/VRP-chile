# -*- coding: utf-8 -*-
"""V177 v07. La permutacion restringida de v02 da p chico. Fuga posible: dentro de la ventana de geometria la pasada propia siempre tiene diferencia de visada cero, las otras no.
Si la ventaja es geometria residual, debe encogerse al estrechar la ventana o al restar un modelo de geometria.
Pre-registro: ventanas (5, 30), (3, 15), (2, 10), (1,5, 8), solo mismo satelite; d propia y d perm; p. Modelo: E y N de cada brazo contra polinomio de tan(zen) sin(az), tan(zen) cos(az) (terminos hasta grado 2 + dummy de satelite), correlacion de residuos y p por barajado.
Control: 60 brazos barajados dentro de N3, p debe repartirse parejo.
"""
import os, sys, pickle, collections
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
GEO = geo_chillan()
rng = np.random.default_rng(1109)


def dazi(a, b):
    x = abs(a - b) % 360
    return min(x, 360 - x)


def cadena(N, T, n_mues=3000):
    n = len(N)
    M = N.copy()
    np.fill_diagonal(M, True)
    pi = np.arange(n)
    for a, b in rng.integers(0, n, size=(100 * n * n, 2)):
        if M[a, pi[b]] and M[b, pi[a]]:
            pi[a], pi[b] = pi[b], pi[a]
    v, mov = [], []
    for k in range(n_mues):
        for a, b in rng.integers(0, n, size=(5 * n, 2)):
            if M[a, pi[b]] and M[b, pi[a]]:
                pi[a], pi[b] = pi[b], pi[a]
        v.append(T(pi))
        mov.append(np.mean(pi != np.arange(n)))
    return np.array(v), float(np.mean(mov))


for nom, b in (("Chillan VIIRS 375", "VIIRS375"), ("Chillan VIIRS 750", "VIIRS750")):
    s = [o for o in R if o["vol"] == CH and o["b"] == b]
    for o in s:
        r = GEO[(o["sensor"], o["dt"])]
        o["zen"], o["azi"] = r["sensor_zenith_deg"], r["sensor_azimuth_deg"]
    n = len(s)
    pla, plo = np.array([o["pt"][0] for o in s]), np.array([o["pt"][1] for o in s])
    mla, mlo = np.array([o["C2"]["la"] for o in s]), np.array([o["C2"]["lo"] for o in s])
    D = hav(mla[:, None], mlo[:, None], pla[None, :], plo[None, :])
    T = lambda pi: D[np.arange(n), pi].mean()
    print(f"\n== {nom} n={n}; sin control de distancia; centroide C2")
    print(f"zenit min {min(o['zen'] for o in s):.1f} max {max(o['zen'] for o in s):.1f}")
    for fz, fa, sat in ((5, 30, False), (3, 15, False), (2, 10, False), (1.5, 8, False), (5, 30, True), (3, 15, True)):
        N = np.array([[i != j and abs(s[i]["zen"] - s[j]["zen"]) <= fz and dazi(s[i]["azi"], s[j]["azi"]) <= fa and (not sat or s[i]["sensor"] == s[j]["sensor"]) for j in range(n)] for i in range(n)])
        v, mov = cadena(N, T)
        o_ = T(np.arange(n))
        p = (1 + (v <= o_).sum()) / (1 + len(v))
        con = N.sum(axis=1) >= 1
        dobs_con = np.diag(D)[con].mean()
        print(f"  zen+-{fz} azi+-{fa} mismo_sat={sat}: pasadas con >=1 vecino {con.sum()}, fraccion que se mueve {mov:.2f}; d obs (todas) {o_:.3f}, perm {v.mean():.3f}, diferencia {v.mean() - o_:+.3f} km, p {p:.4f}")
    # modelo de geometria
    z = np.tan(np.radians([o["zen"] for o in s]))
    az = np.radians([o["azi"] for o in s])
    x1, x2 = z * np.sin(az), z * np.cos(az)
    sats = sorted({o["sensor"] for o in s})
    Xcols = [np.ones(n), x1, x2, x1 ** 2, x2 ** 2, x1 * x2] + [np.array([o["sensor"] == q for o in s], float) for q in sats[1:]]
    X = np.column_stack(Xcols)
    la0, lo0 = np.median(pla), np.median(plo)
    k_lo, k_la = 111.32 * np.cos(np.radians(la0)), 110.57
    E_p, N_p = (plo - lo0) * k_lo, (pla - la0) * k_la
    E_m, N_m = (mlo - lo0) * k_lo, (mla - la0) * k_la
    res = lambda y: y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    for etq, a_, b_ in (("E", E_p, E_m), ("N", N_p, N_m)):
        ra, rb = res(a_), res(b_)
        r0 = np.corrcoef(ra, rb)[0, 1]
        perm = np.array([np.corrcoef(ra[rng.permutation(n)], rb)[0, 1] for _ in range(20000)])
        print(f"  Modelo: componente {etq}: var total nuestro {a_.std():.3f}, residual {ra.std():.3f}; mancha {b_.std():.3f}, residual {rb.std():.3f}; r residuos {r0:+.2f}, p {(1 + (perm >= r0).sum()) / 20001:.4f}, R2 de geometria nuestro {1 - ra.var() / a_.var():.2f}")
    # control
    N3 = np.array([[i != j and abs(s[i]["zen"] - s[j]["zen"]) <= 5 and dazi(s[i]["azi"], s[j]["azi"]) <= 30 for j in range(n)] for i in range(n)])
    M = N3.copy()
    np.fill_diagonal(M, True)
    ps = []
    for rep in range(60):
        pi = np.arange(n)
        for a, c in rng.integers(0, n, size=(30 * n * n, 2)):
            if M[a, pi[c]] and M[c, pi[a]]:
                pi[a], pi[c] = pi[c], pi[a]
        To = T(pi)
        v, _ = cadena(N3, T, n_mues=300)
        ps.append((1 + (v <= To).sum()) / 301)
    ps = np.array(ps)
    print(f"  Control 60 brazos barajados: p<0,05: {(ps < 0.05).sum()}, p<0,01: {(ps < 0.01).sum()}, mediana {np.median(ps):.2f}, cuartiles {np.percentile(ps, 25):.2f} {np.percentile(ps, 75):.2f}")
