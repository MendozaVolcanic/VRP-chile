import os, sys, json, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE+"/../v3"), os.path.abspath(HERE+"/../v4"), HERE):
    sys.path.insert(0, p)
from common3 import *  # noqa
from c6 import df, idx_v, raster  # noqa
print("== control G: filas CONS con VRP>=0,3 MW desde 2026-05-09, dedup por pasada, TIF usable ==")
d = ref(); tot = {}
for vol in ("Lascar", "Villarrica"):
    s = d[(d.vol == vol) & (d.src == "CONS") & (pd.to_numeric(d.VRP_MW, errors="coerce") >= 0.3)]
    s = s[s.t >= pd.Timestamp("2026-05-09", tz="UTC")]
    vistos, n = set(), 0
    for _, r in s.iterrows():
        g = idx_v.get(vol)
        dd = (g.acquisition_utc - r["t"]).dt.total_seconds().abs()
        if not (dd <= 120).any(): continue
        rr = g.loc[dd.idxmin()]
        k = (vol, rr["acquisition_utc"])
        if k in vistos: continue
        Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
        if Rq is None: continue
        vistos.add(k); n += 1
    raster.cache_clear(); tot[vol] = n
    print("   %-12s filas CONS VRP>=0,3: %3d  pasadas distintas con TIF usable: %3d" % (vol, len(s), n))
print("   total pool G: %d  fraccion Lascar: %.2f   (la v6 dice '42 de 43')" % (sum(tot.values()), tot["Lascar"]/max(1,sum(tot.values()))))
