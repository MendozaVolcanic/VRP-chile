import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
D = pickle.load(open(HERE + "/cruz5.pkl", "rb"))
co = D["cross"]; co = co[co.estado == "ok"].copy()
nu = D["null"]; nu = nu[nu.estado == "ok"].copy()
co["gap"] = co.dsep_min.abs()
print("== residuo de la pasada cruzada segun la separacion temporal ==")
for lo, hi in ((0, 45), (45, 60), (60, 120), (120, 1e9)):
    s = co[(co.gap >= lo) & (co.gap < hi)]
    if len(s) < 5: continue
    print("  |dt| %4d-%4s min: n=%3d  D=%+.4f  obs=%.3f ref=%.3f" % (lo, hi if hi < 1e9 else "inf", len(s), s.d.mean(), s.e.mean(), s.r.mean()))
print("\n== tasas de exceso comparables DENTRO del mismo nulo (mismas pasadas y rasters) ==")
print("  punto sorteado en el anillo 1,5-3,0: %.4f   sitios P de otras noches: %.4f  (n=%d pasadas)"
      % (nu.e.mean(), nu.r.mean(), len(nu)))
print("\n== distribucion de d_p (cruzada fuera de muestra) ==")
print("  ", co.d.round(2).value_counts().sort_index().to_dict())
print("  fraccion con e=1: %.3f ; fraccion con d_p=0: %.3f" % (co.e.mean(), (co.d == 0).mean()))
