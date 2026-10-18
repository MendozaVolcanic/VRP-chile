# -*- coding: utf-8 -*-
"""Paso 6: nulo justo del anillo (A110). El nulo de s4 (radio +-1,5 km) estaba sesgado: un anillo mas grande tiene
mas celdas y su maximo es mayor por construccion. Aqui: percentil del maximo de anomalia sobre el anillo verdadero
entre 500 maximos de subconjuntos AL AZAR del mismo numero de celdas, sacados del mismo disco de busqueda. Si el
anillo identifica el calor de MIROVA, los percentiles se amontonan arriba; si no, son uniformes (media 0,5)."""
import json, sys, math
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.argv = ['x']
import importlib.util
spec = importlib.util.spec_from_file_location("s4", "s4_analisis.py")
src = open("s4_analisis.py", encoding="utf-8").read().split("filas = []")[0]
g = {}; exec(compile(src, "s4_head", "exec"), g)
A = json.load(open("s4_analisis.json", encoding="utf-8"))["filas"]
rng = np.random.default_rng(0)
out = []
for r in A:
    y = g["Y"][r["vol"]]; vl, vo, ml, mo = y["vent_lat"], y["vent_lon"], y["mirova_center_lat"], y["mirova_center_lon"]
    if r["mir_dist"] is None: continue
    lim = max(y["inner_radius_km"], 5) + 3
    for img in r["imagenes"]:
        p = "tif/" + img["tif"].replace("data/tif/", "").replace("/", "_")
        ds, a, an, lat, lon, cx, cy, res_km = g["cargar"](p)
        dm = g["dist_grid"](lat, lon, ml, mo); dv = g["dist_grid"](lat, lon, vl, vo)
        tol = g["CELDA"][r["s"]] * 0.5 + 0.1 + res_km * 0.5
        disco = (dv <= lim) & np.isfinite(an)
        ring = disco & (np.abs(dm - r["mir_dist"]) <= tol)
        n = int(ring.sum())
        if n == 0: continue
        vt = float(an[ring].max()); pool = an[disco]
        mx = np.array([rng.choice(pool, n, replace=False).max() for _ in range(500)])
        pct = float((mx < vt).mean())
        out.append((r["k"], img["tipo"], n, pct))
print("imagenes:", len(out))
for t in ("propia", "otra", "reciclada"):
    v = [x[3] for x in out if x[1] == t]
    if v: print("%-9s n=%2d media pct %.2f | pct>=0,9: %d | pct<=0,1: %d" % (t, len(v), np.mean(v), sum(x >= 0.9 for x in v), sum(x <= 0.1 for x in v)))
v = [x[3] for x in out]
print("todas    n=%2d media pct %.2f | >=0,9: %d (esperado al azar %.1f)" % (len(v), np.mean(v), sum(x >= 0.9 for x in v), 0.1 * len(v)))
for x in out: print("  %-44s %-9s celdas=%3d pct=%.2f" % x)
json.dump(out, open("s6_nulo.json", "w"), indent=1)
