# Analisis del nulo del control temporal + regla de veredicto de la v4 S7. Solo lectura.
import os, sys, math, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa

D = pickle.load(open(HERE + "/null4.pkl", "rb"))
zc_df, NUL, PROX = D["zc"], D["null"], D["prox"]
df = B.df

# ---------- 1. zc_punto por volcan (regla literal de la v4 S4)
zz = zc_df.dropna(subset=["z"])
zc = zz.groupby("vol").z.quantile(0.95)
ncal = zz.groupby("vol").z.size()
rng = np.random.default_rng(144)


def boot_q(v, B_=2000):
    s = zz[zz.vol == v].z.values
    return np.percentile([np.percentile(rng.choice(s, len(s), True), 95) for _ in range(B_)], [2.5, 97.5])


print("== zc_punto por volcan (p95, pool RUTINA de la FILA de MIROVA con TIF usable) ==")
for v in zc.index:
    lo, hi = boot_q(v)
    print("  %-22s n=%3d  zc=%5.2f  IC[%.2f, %.2f]" % (v, ncal[v], zc[v], lo, hi))

# ---------- 2. armado del control temporal
pub_m2 = set()
for r in df[(df.lab == "neg_limpio") & df.patron & df.pub & (df.vol != "Lastarria")].itertuples():
    pub_m2.add((r.vol, pd.Timestamp(r.dt).floor("min")))


def arma(recs, gap_d=3.0, nref=5):
    out = []
    for f in recs:
        v = f["vol"]
        if v not in zc.index or f["zobs"] is None:
            continue
        zs, gaps = f["zs"], f["gaps"]
        ok = np.isfinite(zs) & (np.abs(gaps) > gap_d)
        idx = np.argsort(np.abs(np.where(ok, gaps, 1e9)))[:nref]
        idx = [i for i in idx if ok[i]]
        n_disp = int(ok.sum())
        n_nan = int((~np.isfinite(zs) & (np.abs(gaps) > gap_d)).sum())
        if len(idx) < 3:
            out.append(dict(vol=v, dt=f["dt"], tramo=f["tramo"], usada=False, n_ref=len(idx),
                            n_disp=n_disp, n_nan=n_nan)); continue
        e = 1.0 * (f["zobs"] >= zc[v])
        r_ = float(np.mean(zs[idx] >= zc[v]))
        sep = float(np.median(np.abs(gaps[idx])))
        refs_m2 = sum(1 for i in idx if (v, (f["dt"] + pd.Timedelta(days=float(gaps[i]))).floor("min")) in pub_m2)
        out.append(dict(vol=v, dt=f["dt"], noche=pd.Timestamp(f["dt"]).strftime("%Y-%m-%d"),
                        tramo=f["tramo"], usada=True, e=e, r=r_, d=e - r_, n_ref=len(idx),
                        n_disp=n_disp, n_nan=n_nan, sep=sep, refs_m2=refs_m2,
                        zobs=f["zobs"], zref=list(zs[idx])))
    return pd.DataFrame(out)


def boot_D(s, Bn=2000, seed=144):
    """remuestreo POR NOCHE DE VOLCAN, estratificado por volcan."""
    g = np.random.default_rng(seed)
    key = s.vol + "|" + s.noche
    noches = {v: np.array(sorted(set(key[s.vol == v]))) for v in s.vol.unique()}
    porn = {k: v.d.values for k, v in s.groupby(key)}
    out = []
    for _ in range(Bn):
        vals = []
        for v, ns in noches.items():
            sel = g.choice(ns, len(ns), True)
            vals.append(np.concatenate([porn[k] for k in sel]))
        out.append(float(np.mean(np.concatenate(vals))))
    return np.percentile(out, [2.5, 97.5]), np.array(out)


print("\n== NULO DEL CONTROL TEMPORAL (533 pasadas RUTINA ajenas a la muestra de M2) ==")
tabla = {}
for gap in (3.0, 10.0, 30.0):
    s = arma(NUL, gap_d=gap)
    u = s[s.usada]
    (lo, hi), _ = boot_D(u)
    print("  brecha >%2d d: n usadas=%3d (descartadas por <3 refs: %d)  D=%+.4f  IC95 [%+.4f, %+.4f]"
          "  tasa obs=%.3f  tasa ref=%.3f  sep mediana=%.0f d"
          % (gap, len(u), int((~s.usada).sum()), u.d.mean(), lo, hi, u.e.mean(), u.r.mean(), u.sep.median()))
    tabla[gap] = u

u = tabla[3.0]
print("\n-- por volcan (brecha >3 d) --")
for v, g in u.groupby("vol"):
    print("  %-22s n=%3d noches=%3d  D_v=%+.4f  obs=%.3f ref=%.3f  refs que son de M2: %.2f/5"
          % (v, len(g), g.noche.nunique(), g.d.mean(), g.e.mean(), g.r.mean(), g.refs_m2.mean()))

print("\n-- diagnosticos de ejecucion --")
print("  referencias con Z inexistente (punto fuera del raster o sin dL0): %d de %d evaluadas"
      % (int(u.n_nan.sum()), int(u.n_disp.sum() + u.n_nan.sum())))
print("  pasadas con menos de 5 referencias disponibles: %d" % int((u.n_ref < 5).sum()))
print("  separacion temporal mediana de las referencias: %.1f d (p90 %.1f d)"
      % (u.sep.median(), u.sep.quantile(0.9)))
print("  valores distintos de d_p:", sorted(set(np.round(u.d.values, 3))))

# --- la referencia que es una pasada de M2 vs la que no: sesgo de seleccion
allz = []
for f in NUL:
    v = f["vol"]
    if v not in zc.index:
        continue
    for i, (z, gp) in enumerate(zip(f["zs"], f["gaps"])):
        if not np.isfinite(z) or abs(gp) <= 3:
            continue
        t = (f["dt"] + pd.Timedelta(days=float(gp))).floor("min")
        allz.append((v, z >= zc[v], (v, t) in pub_m2))
az = pd.DataFrame(allz, columns=["vol", "exc", "es_m2"])
print("\n-- tasa de exceso en la referencia, segun si esa pasada es una del universo de M2 --")
print("  referencias que SI son pasadas de M2 (patron+publicado): n=%d  tasa=%.4f"
      % (int(az.es_m2.sum()), az[az.es_m2].exc.mean()))
print("  referencias que NO lo son:                               n=%d  tasa=%.4f"
      % (int((~az.es_m2).sum()), az[~az.es_m2].exc.mean()))
pv = az.groupby(["vol", "es_m2"]).exc.agg(["mean", "size"]).unstack()
print(pv.round(3).to_string())

pickle.dump({"tabla": {k: v for k, v in tabla.items()}, "zc": zc, "az": az},
            open(HERE + "/analiza4.pkl", "wb"))
