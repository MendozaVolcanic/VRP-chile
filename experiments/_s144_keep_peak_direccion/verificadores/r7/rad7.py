# Gradiente radial del instrumento: fraccion de celdas con z>=zc por anillo de radio,
# y probabilidad de que Z(X) (maximo sobre el disco de T) supere zc segun el radio de X.
import os, sys, pickle, time, math, random
import numpy as np, pandas as pd
sys.path.insert(0,'.')
from b7 import *  # noqa
H=herm(); rows=[]; t0=time.time()
rng=random.Random(555)
BINS=[(1.5,1.9),(1.9,2.2),(2.2,2.5),(2.5,2.75),(2.75,3.0)]
for vol in sorted(VOLS):
    g=H[H.vol==vol]
    if not len(g) or vol not in zc.index: continue
    v=vent(vol); hecho=set()
    for _,r in g.sort_values("t").iterrows():
        cr,_=cruzada(vol,r["t"])
        if cr is None: continue
        Rr,_=cr
        key=id(Rr)
        if key in hecho: continue
        hecho.add(key)
        d=hav(Rr["lat"],Rr["lon"],v[0],v[1])
        for lo_,hi_ in BINS:
            m=(d>=lo_)&(d<hi_)&np.isfinite(Rr["z"])
            if not m.any(): continue
            rows.append(dict(vol=vol,bin="%.2f-%.2f"%(lo_,hi_),frac_celdas=float(np.mean(Rr["z"][m]>=zc[vol])),
                             zmed=float(np.median(Rr["z"][m])), n=int(m.sum())))
        # Z(X) por radio: 6 sorteos por bin
        for lo_,hi_ in BINS:
            for _ in range(6):
                u=rng.random(); rr=math.sqrt(lo_**2+u*(hi_**2-lo_**2)); az=rng.uniform(0,2*math.pi)
                X=desplazar(v[0],v[1],rr*math.cos(az),rr*math.sin(az))
                z=Z(Rr,X)
                if z is None: continue
                rows.append(dict(vol=vol,bin="%.2f-%.2f"%(lo_,hi_),eX=float(z>=zc[vol])))
    raster.cache_clear(); print("  ...%s (%.0fs)"%(vol,time.time()-t0),flush=True)
D=pd.DataFrame(rows)
print("\n== gradiente radial del instrumento (rasteres cruzados del estrato hermano) ==")
t=D.groupby("bin").agg(frac_celdas=("frac_celdas","mean"), z_mediano=("zmed","mean"),
                       P_de_Z_supera=("eX","mean"), n_sorteos=("eX","count"))
print(t.round(4).to_string())
print("\n  razon del ultimo anillo contra el primero: celdas %.2fx   Z(X) %.2fx"
      %(t.frac_celdas.iloc[-1]/max(t.frac_celdas.iloc[0],1e-9), t.P_de_Z_supera.iloc[-1]/max(t.P_de_Z_supera.iloc[0],1e-9)))
