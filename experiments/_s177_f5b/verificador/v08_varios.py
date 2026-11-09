# -*- coding: utf-8 -*-
"""V177 v08. Cabos sueltos.
1. El 1 punto de diferencia con el nulo de V5B: sorteo o universo de j? V5B toma los j solo entre pasadas con control A ok; s03 toma todos.
2. Componentes >= 2 en Chillan con C2 (INFORME sec. 8 dice 1 de 69 en V375; s02 dice 0).
3. Cumulo: la ventaja propia de cov_N y cov_M sobrevive si igualo tambien el numero de pixeles alertados?
4. Las 31 componentes de Chillan que A borraba: distancia de nuestro punto a la celda mas cercana (si fueran huecos sin dato, seria aleatoria dentro del inner).
5. Laminas distintas (INFORME sec. 3: 291) y las 2 de Lascar donde mi A difiere.
"""
import os, sys, pickle, collections, json
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comun import *

R = pickle.load(open(os.path.join(HERE, "v01_manchas.pkl"), "rb"))
GEO = geo_chillan()
print("1. Nulo de V5B con mancha A, j solo entre pasadas con control A ok (todos los volcanes), exacto:")
for b in ("VIIRS375", "VIIRS750"):
    obs, nu_ok, nu_all = [], [], []
    for vol in sorted({o["vol"] for o in R}):
        g = grilla(vol, b) if any(o["vol"] == vol and o["b"] == b for o in R) else None
        s = [o for o in R if o["vol"] == vol and o["b"] == b]
        ok = [o for o in s if clase(o["A"], o["pt"], o["dist"], b, o["celda"], g, "cent") != "iv"]
        for o in ok:
            otros_ok = [x for x in ok if x is not o]
            otros_all = [x for x in s if x is not o]
            if otros_ok:
                nu_ok.append(np.mean([hav(o["A"]["la"], o["A"]["lo"], *x["pt"]) <= TOL[b] for x in otros_ok]))
            if otros_all:
                nu_all.append(np.mean([hav(o["A"]["la"], o["A"]["lo"], *x["pt"]) <= TOL[b] for x in otros_all]))
    print(f"   {b}: j control ok {np.mean(nu_ok):.3f} (n={len(nu_ok)}); j todos {np.mean(nu_all):.3f} (n={len(nu_all)})")

print("\n2. Componentes de C2 por sensor en Chillan:")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    s = [o for o in R if o["vol"] == CH and o["b"] == b]
    print(f"   {b}: n={len(s)}, con >= 2 componentes: {sum(o['C2']['ncomp'] >= 2 for o in s)}; C2 distinto de C1 en px: {sum(o['C2']['px'] != o['C1']['px'] for o in s)}")

print("\n3. Cumulo con numero de pixeles igualado:")
for b, nom in (("VIIRS375", "V375"), ("VIIRS750", "V750")):
    s = [o for o in R if o["vol"] == CH and o["b"] == b]
    g = grilla(CH, b)
    cel = g["celda"]
    for o in s:
        r = GEO[(o["sensor"], o["dt"])]
        o["zen"], o["azi"] = r["sensor_zenith_deg"], r["sensor_azimuth_deg"]
        o["pix"] = [(p["lat"], p["lon"]) for p in r.get("anomaly_pixels", [])]

    def cob(o, pix):
        la, lo = np.array([p[0] for p in pix]), np.array([p[1] for p in pix])
        D = hav(o["C2"]["lats"][:, None], o["C2"]["lons"][:, None], la[None, :], lo[None, :])
        return float((D.min(axis=0) <= cel + 1e-9).mean()), float((D.min(axis=1) <= cel + 1e-9).mean())

    def dazi(a, c):
        x = abs(a - c) % 360
        return min(x, 360 - x)

    for etq, f in (("N3 (igual que s05)", lambda oi, oj: True), ("N3 y |dif n pixeles| <= 1", lambda oi, oj: abs(len(oi["pix"]) - len(oj["pix"])) <= 1), ("N3 y mismo n pixeles", lambda oi, oj: len(oi["pix"]) == len(oj["pix"]))):
        res = []
        for oi in s:
            if not oi["pix"]:
                continue
            ot = [oj for oj in s if oj is not oi and oj["pix"] and abs(oj["zen"] - oi["zen"]) <= 5 and dazi(oj["azi"], oi["azi"]) <= 30 and f(oi, oj)]
            if len(ot) < 2:
                continue
            a = cob(oi, oi["pix"])
            nn = np.array([cob(oi, oj["pix"]) for oj in ot])
            res.append((a[0] - nn[:, 0].mean(), a[1] - nn[:, 1].mean()))
        res = np.array(res)
        rng = np.random.default_rng(9)
        idx = rng.integers(0, len(res), (2000, len(res)))
        bN, bM = res[:, 0][idx].mean(1), res[:, 1][idx].mean(1)
        print(f"   {nom} {etq}: n={len(res)}; cov_N {res[:, 0].mean():+.3f} [{np.percentile(bN, 2.5):+.3f}, {np.percentile(bN, 97.5):+.3f}] | cov_M {res[:, 1].mean():+.3f} [{np.percentile(bM, 2.5):+.3f}, {np.percentile(bM, 97.5):+.3f}]")

print("\n4. Componentes que A borraba en Chillan (C1 con px distinto de A): distancia de nuestro punto a la celda mas cercana de la mancha C2")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    s = [o for o in R if o["vol"] == CH and o["b"] == b and (o["C1"]["px"] != o["A"]["px"] or abs(o["C1"]["la"] - o["A"]["la"]) > 1e-6)]
    d = np.array([hav(o["C2"]["lats"], o["C2"]["lons"], *o["pt"]).min() for o in s])
    print(f"   {b}: n={len(s)}, d min p50 {np.median(d):.2f} max {d.max():.2f} km (inner 5 km); celda {grilla(CH, b)['celda']:.2f}")

print("\n5. Laminas distintas:", len({x["png"] for x in P8 if x.get("png")}), "de", sum(1 for x in P8 if x.get("png")), "con lamina;", len(P8), "aciertos")
for o in R:
    if abs(o["A"]["la"] - o["F5b"][0]) >= 2e-5 or abs(o["A"]["lo"] - o["F5b"][1]) >= 2e-5:
        print("   mi A difiere:", o["vol"], o["sensor"], o["dt"], "mio", round(o["A"]["la"], 5), round(o["A"]["lo"], 5), "lum", round(o["A"]["mx"], 1), "| F5b", o["F5b"], "lum", o["x"].get("lum_max"), "| clase F5b", o["claseF5b"])
