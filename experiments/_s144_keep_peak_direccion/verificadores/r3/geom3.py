# Geometria de P en la muestra de M2 (sin abrir ningun raster).
import os, sys, math, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

d = pickle.load(open(os.path.dirname(os.path.abspath(__file__)) + "/pool3.pkl", "rb"))
df = d["df"]


def az(vol, P):
    v = vent(vol)
    dn = (P[0] - v[0]) * 110.574
    de = (P[1] - v[1]) * 111.320 * math.cos(math.radians(v[0]))
    return (math.degrees(math.atan2(de, dn)) + 360) % 360


sub = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
sub["azP"] = [az(r.vol, r.P) for r in sub.itertuples()]
print("== r(P) desde el crater, neg_limpio fuera de Lastarria, patron+pub (n=%d) ==" % len(sub))
q = sub.groupby("vol").rP.describe(percentiles=[.1, .25, .5, .75, .9])[["count", "10%", "50%", "90%"]]
q["frac_en_banda_1.5_3.5"] = sub.groupby("vol").rP.apply(lambda s: float(((s >= 1.5) & (s <= 3.5)).mean()))
print(q.round(2).to_string())
print("\nglobal: frac en banda 1,5-3,5 km = %.3f ; mediana r(P) = %.2f km"
      % (float(((sub.rP >= 1.5) & (sub.rP <= 3.5)).mean()), float(sub.rP.median())))

print("\n== acimut de P (0=N, 90=E), por volcan ==")
for v, g in sub.groupby("vol"):
    s = np.radians(g.azP.values)
    Rm = math.hypot(np.mean(np.sin(s)), np.mean(np.cos(s)))
    med = (math.degrees(math.atan2(np.mean(np.sin(s)), np.mean(np.cos(s)))) + 360) % 360
    sect = pd.cut(g.azP, bins=[0, 45, 90, 135, 180, 225, 270, 315, 360],
                  labels=["N", "NE", "E", "SE", "S", "SW", "W", "NW"], right=False)
    top = sect.value_counts(normalize=True).head(2)
    print(f"  {v:22s} n={len(g):4d} acimut medio={med:6.1f}  concentracion R={Rm:.2f}  "
          f"top sectores: {', '.join(f'{i}={p:.2f}' for i, p in top.items())}")

pickle.dump(sub[["vol", "dt", "rP", "azP", "P", "tramo"]], open(
    os.path.dirname(os.path.abspath(__file__)) + "/geomP.pkl", "wb"))
