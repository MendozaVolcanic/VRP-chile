# 1) Persistencia espacial de nuestros P (sin abrir ningun raster: pura geometria).
# 2) Proxy de seleccion ampliado: Z en NUESTRO P sobre pasadas FUERA de la muestra del veredicto
#    (Lastarria completa; far_ref y sin_info fuera de Lastarria).
import os, sys, math, pickle, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa

df = B.df
pools = pickle.load(open(HERE + "/pools4.pkl", "rb"))
A = pools["A"]

# ---------- 1. persistencia de P en la muestra de M2 (554 con TIF usable no hace falta: uso las 1113)
m2 = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
print("== persistencia espacial de P (patron+pub+neg_limpio fuera de Lastarria, n=%d) ==" % len(m2))
print("   para cada P, cuantas NOCHES DISTINTAS del mismo volcan tienen otro P a <= 0,75 km")
fil = []
for v, g in m2.groupby("vol"):
    la = np.array([p[0] for p in g.P]); lo = np.array([p[1] for p in g.P])
    noches = g.noche.values
    for i in range(len(g)):
        d = hav(la, lo, la[i], lo[i])
        otras = set(noches[(d <= 0.75)]) - {noches[i]}
        fil.append(dict(vol=v, noche=noches[i], n_otras_noches=len(otras),
                        n_tot_noches=len(set(noches))))
F = pd.DataFrame(fil)
agg = F.groupby("vol").apply(lambda s: pd.Series({
    "n": len(s), "mediana_otras_noches": s.n_otras_noches.median(),
    "frac_ge1": float((s.n_otras_noches >= 1).mean()),
    "frac_ge5": float((s.n_otras_noches >= 5).mean()),
    "noches_vol": s.n_tot_noches.max()}), include_groups=False)
print(agg.round(3).to_string())
print("\n  global: %.3f de los P tienen otro P nuestro a <=0,75 km en otra noche; mediana de otras noches = %.0f"
      % (float((F.n_otras_noches >= 1).mean()), F.n_otras_noches.median()))

# ---------- 2. proxy ampliado
cand = df[(df.patron & df.pub & (df.vol == "Lastarria")) |
          (df.patron & df.pub & (df.vol != "Lastarria") & df.lab.isin(["far_ref", "sin_info"]))].copy()
cand = cand[cand.tif.notna()]
print("\n== proxy ampliado: candidatas fuera de la muestra del veredicto: %d ==" % len(cand))
print(cand.groupby(["vol", "lab"]).size().to_dict())

res = []
t0 = time.time()
for vol, g in cand.groupby("vol"):
    a = A.get(vol)
    if a is None:
        continue
    keep = []
    for _, r in a.iterrows():
        Rr, why = usable({"own": r["own"], "path": r["path"]}, vol)
        if Rr is not None:
            keep.append((pd.Timestamp(r["dt"]), Rr))
    keep.sort(key=lambda x: x[0])
    ref_dts = np.array([k[0].value for k in keep], dtype="int64")
    for _, r in g.iterrows():
        Rp, why = usable({"own": r["own"], "path": r["tif"]}, vol)
        if Rp is None:
            continue
        X = r["P"]
        zo = Z(Rp, X)
        if zo is None:
            continue
        dtp = pd.Timestamp(r["dt"])
        gaps = (ref_dts - dtp.value) / 86400e9
        zs = np.array([(lambda q: np.nan if q is None else q)(Z(Rr, X)) for _d, Rr in keep])
        res.append(dict(vol=vol, dt=dtp, lab=r["lab"], zobs=zo, zs=zs, gaps=gaps))
    raster.cache_clear()
    print("  %-22s %d medidas (%.0fs)" % (vol, len(res), time.time() - t0), flush=True)

pickle.dump(res, open(HERE + "/prox_amp.pkl", "wb"))
print("listo:", len(res))
