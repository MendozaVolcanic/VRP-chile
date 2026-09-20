# Nulo del CONTROL TEMPORAL de la v4 (S5 + S7). Solo lectura.
# Para cada pasada del pool nulo (neg_limpio sin patron / sin publicar) pongo un punto X
# sorteado de la distribucion empirica de nuestros P y evaluo Z(X) en esa pasada y en TODAS
# las pasadas RUTINA con TIF usable del volcan. De ahi salen todas las variantes de brecha.
import os, sys, math, pickle, random, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3); sys.path.insert(0, HERE)
from common3 import *  # noqa
import base4 as B  # noqa

pools = pickle.load(open(HERE + "/pools4.pkl", "rb"))
A = pools["A"]
df = B.df
geomP = B.geomP
emp = {v: g[["rP", "azP"]].values for v, g in geomP.groupby("vol")}

VOLS_S = sorted(VOLS)
rng_zc = random.Random(144)      # el de la v4 S4 para zc_punto
rng_x = random.Random(1440)      # el mio para el sorteo del nulo (la v4 no lo fija)

# ---- pool nulo (mismo criterio que la ronda 3) y proxy de contaminacion
nul = df[(df.lab == "neg_limpio") & (df.vol != "Lastarria") & ~(df.patron & df.pub) & df.tif.notna()].copy()
prox = df[(df.lab == "neg_limpio") & (df.vol != "Lastarria") & df.patron & ~df.pub & df.tif.notna()].copy()
print("pool nulo candidato:", len(nul), " proxy (patron, neg_limpio, NO publicado):", len(prox))

res_zc, res_null, res_prox, res_ref = [], [], [], []
t0 = time.time()
for vol in VOLS_S:
    a = A.get(vol)
    if a is None or vol not in emp:
        continue
    # 1. abrir y filtrar por usabilidad todas las RUTINA del volcan
    keep = []
    for _, r in a.iterrows():
        Rr, why = usable({"own": r["own"], "path": r["path"]}, vol)
        if Rr is not None:
            keep.append((pd.Timestamp(r["dt"]), Rr, r["path"]))
    keep.sort(key=lambda x: x[0])
    ref_dts = np.array([k[0].value for k in keep], dtype="int64")
    res_ref.append(dict(vol=vol, n_rutina_tif=len(a), n_rutina_usable=len(keep)))
    print("  %-22s RUTINA con TIF=%3d  usable=%3d   (%.0fs)" % (vol, len(a), len(keep), time.time() - t0), flush=True)
    v = vent(vol)

    # 2. zc_punto: un sorteo uniforme en area en el anillo 1,5-3,5 km por pasada, orden (vol, dt)
    for dt, Rr, _p in keep:
        ru = math.sqrt(rng_zc.uniform(1.5 ** 2, 3.5 ** 2))
        au = rng_zc.uniform(0, 360)
        X = desplazar(v[0], v[1], ru * math.cos(math.radians(au)), ru * math.sin(math.radians(au)))
        res_zc.append(dict(vol=vol, dt=dt, z=Z(Rr, X)))

    # 3. nulo: punto "como nuestro P", Z en la pasada y en todas las referencias
    def medir(sub, modo):
        out = []
        for _, r in sub.iterrows():
            if r["vol"] != vol:
                continue
            Rp, why = usable({"own": r["own"], "path": r["tif"]}, vol)
            if Rp is None:
                continue
            if modo == "null":
                rp, ap = emp[vol][rng_x.randrange(len(emp[vol]))]
                X = desplazar(v[0], v[1], rp * math.cos(math.radians(ap)), rp * math.sin(math.radians(ap)))
            else:
                X = r["P"]
                rp = hav(X[0], X[1], v[0], v[1]); ap = np.nan
            zobs = Z(Rp, X)
            dtp = pd.Timestamp(r["dt"])
            zs = np.array([(lambda q: np.nan if q is None else q)(Z(Rr, X)) for _d, Rr, _p in keep])
            gaps = (ref_dts - dtp.value) / 86400e9
            out.append(dict(vol=vol, dt=dtp, tramo=r["tramo"], rp=rp, ap=ap, X=X,
                            zobs=zobs, zs=zs, gaps=gaps, modo=modo))
        return out

    res_null += medir(nul, "null")
    res_prox += medir(prox, "prox")
    raster.cache_clear()

pickle.dump(dict(zc=pd.DataFrame(res_zc), null=res_null, prox=res_prox,
                 ref=pd.DataFrame(res_ref)), open(HERE + "/null4.pkl", "wb"))
print("\nlisto en %.0f s: nulo=%d proxy=%d" % (time.time() - t0, len(res_null), len(res_prox)))
