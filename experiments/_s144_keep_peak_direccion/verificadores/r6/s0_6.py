# Conteos de la seccion 0-bis de la v6: 2.541 pasadas con patron, 1.824 con cruzada >=15 min,
# 1.594 con cruzada >=45 min. Solo conteo sobre el indice de TIF.
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE + "/../v3"), os.path.abspath(HERE + "/../v4"), HERE):
    sys.path.insert(0, p)
from common3 import *  # noqa
import base4 as B  # noqa

df = B.df.copy()
df["t"] = pd.to_datetime(df.dt, utc=True)
df["noche"] = df.t.dt.strftime("%Y-%m-%d")
idx_v = B.idx_v

print("== denominadores de 'pasadas con patron' ==")
print("  patron sin exigir publicacion : %d" % int(df.patron.sum()))
print("  patron como lo define la 4 (publica): %d" % int((df.patron & df.pub).sum()))
print("  ... fuera de Lastarria        : %d" % int((df.patron & df.pub & (df.vol != 'Lastarria')).sum()))
print("  la v6 S0-bis dice 2.541")


def tiene(vol, t, gmin, gmax=None, misma_noche=False):
    g = idx_v.get(vol)
    if g is None:
        return False
    dd = (g.acquisition_utc - t).dt.total_seconds()
    m = dd.abs() >= gmin
    if gmax is not None:
        m &= dd.abs() <= gmax
    if misma_noche:
        m &= (g.acquisition_utc.dt.strftime("%Y-%m-%d") == t.strftime("%Y-%m-%d"))
    return bool(m.any())


for nom, sub in (("patron sin pub (2.999)", df[df.patron]),
                 ("patron con pub (2.627)", df[df.patron & df.pub])):
    print("\n-- %s --" % nom)
    for etq, kw in (("otra pasada misma noche, >=15 min", dict(gmin=900, misma_noche=True)),
                    ("otra pasada cualquiera, >=15 min", dict(gmin=900)),
                    ("otra pasada misma noche, >=45 min", dict(gmin=2700, misma_noche=True)),
                    ("otra pasada cualquiera, >=45 min", dict(gmin=2700)),
                    ("ventana v6 [45,120] min", dict(gmin=2700, gmax=7200))):
        n = sum(tiene(r["vol"], r["t"], **kw) for _, r in sub.iterrows())
        print("   %-38s %4d" % (etq, n))
print("\n  la v6 dice: 1.824 con >=15 min y 1.594 con >=45 min")
