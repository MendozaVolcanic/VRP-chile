# Variante "celda exacta" en vez de "maximo sobre el disco de T": separa rugosidad de exceso.
import os, sys, pickle, time, math, random
import numpy as np, pandas as pd
sys.path.insert(0,'.')
from b7 import *  # noqa
def Zcel(R, pt):
    d = hav(R["lat"], R["lon"], pt[0], pt[1])
    i = np.unravel_index(np.argmin(d), d.shape)
    z = R["z"][i]
    return None if not np.isfinite(z) else float(z)
H=herm()
rng_X=random.Random(7144); rng_A=random.Random(90001); rng_B=random.Random(90002); rng_S=random.Random(90003)
rows=[]; t0=time.time()
for vol in sorted(VOLS):
    g=H[H.vol==vol]
    if not len(g) or vol not in zc.index: continue
    v=vent(vol)
    for _,r in g.sort_values("t").iterrows():
        P=r["P"]
        if P is None or P[0] is None: continue
        rP,_=radio_az(vol,P)
        X,_,_,_=sortear_sep(rng_X,v,P,modo="par")
        A,_,_=sortear(rng_A,v); Bp,_,_,_=sortear_sep(rng_B,v,A,modo="par")
        S,_,_=sortear_mismo_radio(rng_S,v,P,rP)
        cr,why=cruzada(vol,r["t"])
        if cr is None: continue
        Rr,_=cr
        rows.append(dict(vol=vol,noche=r["noche"],
                         zP=Zcel(Rr,P),zX=Zcel(Rr,X),zA=Zcel(Rr,A),zB=Zcel(Rr,Bp),zS=Zcel(Rr,S)))
    raster.cache_clear()
D=pd.DataFrame(rows).dropna()
print("n=%d (%.0fs)"%(len(D),time.time()-t0))
for k in "PXABS":
    D["e"+k]=[float(z>=zc[v]) for z,v in zip(D["z"+k],D.vol)]
print("\n== variante CELDA EXACTA (mismo umbral zc, sin maximo sobre el disco) ==")
for nom,a,b in (("P - X","P","X"),("nulo A - B","A","B"),("P - S (mismo radio)","P","S")):
    d=(D["e"+a]-D["e"+b]).values; lo,hi=boot(d,D.vol.values,D.noche.values)
    print("  %-22s D=%+.4f IC95 [%+.4f, %+.4f]  tasa %s=%.4f tasa %s=%.4f"%(nom,d.mean(),lo,hi,a,D["e"+a].mean(),b,D["e"+b].mean()))
print("\n  z medio: P %.3f  X %.3f  S %.3f  A %.3f" % (D.zP.mean(),D.zX.mean(),D.zS.mean(),D.zA.mean()))
print("  z mediano: P %.3f  X %.3f  S %.3f" % (D.zP.median(),D.zX.median(),D.zS.median()))
