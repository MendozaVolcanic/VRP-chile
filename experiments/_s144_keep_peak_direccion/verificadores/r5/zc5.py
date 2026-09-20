# zc_punto con la regla LITERAL de la v5 S4 (anillo 1,5-3,0 km, Random(144), volcanes
# alfabeticos, pasadas por datetime ascendente, dos numeros por pasada: u del radio y acimut).
# Solo lectura.
import os, sys, math, pickle, time, random
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa

pools = pickle.load(open(V4 + "/pools4.pkl", "rb"))
A = pools["A"]

VOLS_S = sorted(VOLS)
rng = random.Random(144)
rows, meta = [], []
t0 = time.time()
for vol in VOLS_S:
    a = A.get(vol)
    if a is None:
        continue
    a = a.sort_values("dt").reset_index(drop=True)
    v = vent(vol)
    nus = 0
    for _, r in a.iterrows():
        Rr, why = usable({"own": r["own"], "path": r["path"]}, vol)
        if Rr is None:
            continue
        nus += 1
        u = rng.random()
        rr = math.sqrt(1.5 ** 2 + u * (3.0 ** 2 - 1.5 ** 2))
        az = rng.uniform(0, 2 * math.pi)
        X = desplazar(v[0], v[1], rr * math.cos(az), rr * math.sin(az))
        rows.append(dict(vol=vol, dt=pd.Timestamp(r["dt"]), r=rr, z=Z(Rr, X), path=r["path"]))
    meta.append(dict(vol=vol, n_tif=len(a), n_usable=nus))
    print("  %-22s TIF=%3d usable=%3d  (%.0fs)" % (vol, len(a), nus, time.time() - t0), flush=True)
    raster.cache_clear()

Zc = pd.DataFrame(rows)
M = pd.DataFrame(meta)
zz = Zc.dropna(subset=["z"])
zc = zz.groupby("vol").z.quantile(0.95)
g = np.random.default_rng(144)
print("\n== zc_punto v5 (anillo 1,5-3,0) ==")
out = {}
for v in zc.index:
    s = zz[zz.vol == v].z.values
    bs = np.percentile([np.percentile(g.choice(s, len(s), True), 95) for _ in range(2000)], [2.5, 97.5])
    out[v] = (len(s), float(zc[v]), float(bs[0]), float(bs[1]))
    print("  %-22s n=%3d  zc=%5.2f  IC[%.2f, %.2f]" % (v, len(s), zc[v], bs[0], bs[1]))
pickle.dump(dict(Zc=Zc, zc=zc, meta=M, ic=out), open(HERE + "/zc5.pkl", "wb"))
print("\nlisto en %.0f s" % (time.time() - t0))
