import os, sys, pickle, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa
from analiza4 import zc, boot_D  # noqa

res = pickle.load(open(HERE + "/prox_amp.pkl", "rb"))
# zc de Lastarria: no esta en zc (geomP lo excluye). Lo calculo con el mismo pool y regla.
print("volcanes con zc:", list(zc.index))

rows = []
for f in res:
    v = f["vol"]
    if v not in zc.index:
        continue
    zs, gaps = f["zs"], f["gaps"]
    ok = np.isfinite(zs) & (np.abs(gaps) > 3)
    idx = [i for i in np.argsort(np.abs(np.where(ok, gaps, 1e9)))[:5] if ok[i]]
    if len(idx) < 3:
        continue
    e = 1.0 * (f["zobs"] >= zc[v])
    r = float(np.mean(zs[idx] >= zc[v]))
    rows.append(dict(vol=v, dt=f["dt"], lab=f["lab"], e=e, r=r, d=e - r,
                     noche=f["dt"].strftime("%Y-%m-%d")))
P = pd.DataFrame(rows)
print("\n== PROXY AMPLIADO: Z en NUESTRO P, pasadas FUERA de la muestra del veredicto ==")
print("  n=%d  D=%+.4f  tasa obs=%.3f  tasa ref(mismo P otras noches)=%.3f" %
      (len(P), P.d.mean(), P.e.mean(), P.r.mean()))
(lo, hi), _ = boot_D(P)
print("  IC95 (remuestreo por noche, estratificado por volcan) [%+.4f, %+.4f]" % (lo, hi))
print("\n-- por etiqueta --")
print(P.groupby("lab").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
print("\n-- por volcan --")
print(P.groupby("vol").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
