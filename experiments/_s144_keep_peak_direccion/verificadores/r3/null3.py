# Nulo del control P': pasadas RUTINA (neg_limpio) SIN patron o sin publicar, fuera de la muestra
# de M2. Mide si Z(X) supera a Z(X') cuando X se pone donde suele caer nuestro P.
import os, sys, math, pickle, random
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
d = pickle.load(open(HERE + "/pool3.pkl", "rb"))
df = d["df"]
geomP = pickle.load(open(HERE + "/geomP.pkl", "rb"))

# --- pool nulo: neg_limpio, fuera de Lastarria, que NO entra a la muestra de M2
nul = df[(df.lab == "neg_limpio") & (df.vol != "Lastarria") & ~(df.patron & df.pub)].copy()
nul = nul[nul.tif.notna()]
print("pool nulo candidato (neg_limpio sin patron/publicado, con TIF pareado):", len(nul))
print(nul.vol.value_counts().to_dict())

emp = {v: g[["rP", "azP"]].values for v, g in geomP.groupby("vol")}
rng = random.Random(144)
SECT = list(range(0, 360, 45))
filas = []
nul = nul.sort_values(["vol", "dt"])
for _, r in nul.iterrows():
    vol = r["vol"]
    if vol not in emp:
        continue
    Rr, why = usable({"own": r["own"], "path": r["tif"]}, vol)
    if Rr is None:
        filas.append(dict(vol=vol, dt=r["dt"], estado=why))
        continue
    v = vent(vol)
    # (a) sorteo uniforme en la banda 1,5-3,5 km (regla de zc_punto de la v3)
    ru = math.sqrt(rng.uniform(1.5 ** 2, 3.5 ** 2))
    au = rng.uniform(0, 360)
    Xu = desplazar(v[0], v[1], ru * math.cos(math.radians(au)), ru * math.sin(math.radians(au)))
    # (b) punto "como nuestro P": (r, acimut) sorteado del empirico del mismo volcan
    rp, ap = emp[vol][rng.randrange(len(emp[vol]))]
    Xp = desplazar(v[0], v[1], rp * math.cos(math.radians(ap)), rp * math.sin(math.radians(ap)))
    Xpp = reflejo(Xp, v)
    f = dict(vol=vol, dt=r["dt"], estado="ok", tramo=r["tramo"],
             zu=Z(Rr, Xu), zu_ref=Z(Rr, reflejo(Xu, v)),
             zp=Z(Rr, Xp), zpp=Z(Rr, Xpp), rp=rp, ap=ap)
    # (c) perfil acimutal a radio fijo 2,8 km
    for s in SECT:
        Xs = desplazar(v[0], v[1], 2.8 * math.cos(math.radians(s)), 2.8 * math.sin(math.radians(s)))
        f[f"z_{s}"] = Z(Rr, Xs)
    filas.append(f)

D = pd.DataFrame(filas)
D.to_pickle(HERE + "/null3.pkl")
print("\nestados:", D.estado.value_counts().to_dict())
ok = D[D.estado == "ok"].copy()
print("pool nulo usable:", len(ok))
print(ok.vol.value_counts().to_dict())
