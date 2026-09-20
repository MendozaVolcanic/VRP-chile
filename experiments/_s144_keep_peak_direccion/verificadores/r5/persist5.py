# De donde viene el residuo de la pasada cruzada: brazo de OTRA NOCHE con los MISMOS sitios de
# referencia y el mismo estadistico. Si D sigue positivo ahi, el sitio es persistentemente especial
# (la seleccion opera sobre una propiedad permanente); si cae a 0, el exceso es de esa noche.
# Solo lectura. No toca ninguna pasada de la muestra del veredicto en su P.
import os, sys, math, pickle, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa
from cruz5 import df, idx_v, zc, refs_de, cruzada_de, MINREF  # noqa

OUT = df[df.patron & df.pub & (df.vol != "Lastarria") & df.lab.isin(["far_ref", "sin_info"])].copy()

# indice de rasters usables por volcan (cualquier pasada del archivo)
res = []
t0 = time.time()
for vol, g in OUT.groupby("vol"):
    if vol not in zc.index:
        continue
    ix = idx_v[vol]
    for _, r in g.sort_values("t").iterrows():
        t_p = r["t"]
        R = refs_de(vol, t_p, r["noche"], r["P"])
        if len(R) < MINREF:
            continue
        # raster de OTRA NOCHE (>3 d), el mas cercano en el tiempo que sea usable
        dd = (ix.acquisition_utc - t_p).dt.total_seconds()
        m = (dd.abs() > 3 * 86400)
        cand = ix[m]
        if not len(cand):
            continue
        orden = np.argsort(dd[m].abs().values)
        Rr = None
        for i in orden[:8]:
            rr = cand.iloc[i]
            Rq, why = usable({"own": bool(rr["own"]), "path": rr["path"]}, vol)
            if Rq is not None:
                Rr = Rq; gapd = float(dd[m].iloc[i] / 86400); break
        if Rr is None:
            continue
        zo = Z(Rr, r["P"])
        if zo is None:
            continue
        zr = [Z(Rr, p) for p, _g in R]
        zr = [x for x in zr if x is not None]
        if len(zr) < MINREF:
            continue
        e = 1.0 * (zo >= zc[vol])
        rf = float(np.mean([x >= zc[vol] for x in zr]))
        res.append(dict(vol=vol, t=t_p, noche=r["noche"], lab=r["lab"], e=e, r=rf, d=e - rf,
                        gap_d=gapd))
    raster.cache_clear()
    print("  %-22s acumulado %d (%.0fs)" % (vol, len(res), time.time() - t0), flush=True)

P = pd.DataFrame(res)
pickle.dump(P, open(HERE + "/persist5.pkl", "wb"))


def boot_D(s, Bn=2000, seed=144, col="d"):
    g = np.random.default_rng(seed)
    key = (s.vol + "|" + s.noche).values
    noches = {v: np.array(sorted(set(key[(s.vol == v).values]))) for v in s.vol.unique()}
    porn = {k: v[col].values for k, v in s.groupby(key)}
    out = []
    for _ in range(Bn):
        vals = []
        for v, ns in noches.items():
            sel = g.choice(ns, len(ns), True)
            vals.append(np.concatenate([porn[k] for k in sel]))
        out.append(float(np.mean(np.concatenate(vals))))
    return np.percentile(out, [2.5, 97.5])


lo, hi = boot_D(P)
print("\n== BRAZO DE OTRA NOCHE (mismo P, mismos sitios de referencia, raster de >3 d) ==")
print("  n=%d  D=%+.4f  IC95 [%+.4f, %+.4f]  obs=%.3f ref=%.3f  gap mediano %.1f d"
      % (len(P), P.d.mean(), lo, hi, P.e.mean(), P.r.mean(), P.gap_d.abs().median()))
print("\n-- por volcan --")
print(P.groupby("vol").agg(n=("d", "size"), D=("d", "mean"), obs=("e", "mean"), ref=("r", "mean")).round(3).to_string())
