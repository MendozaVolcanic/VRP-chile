# Climatologia espacial del exceso: cuanto del efecto del eje 1 lo explica el SECTOR (acimut)
# y cuanto el sitio exacto. Solo estrato hermano, solo lectura.
import os, sys, pickle, time, math, random
import numpy as np, pandas as pd
sys.path.insert(0,'.')
from b7 import *  # noqa
H=herm()
# 1) mapa climatologico por volcan: fraccion de rasteres en que cada celda supera zc
clim={}; geo={}
for vol in sorted(VOLS):
    g=H[H.vol==vol]
    if not len(g) or vol not in zc.index: continue
    v=vent(vol); acc=None; n=0; paths=set()
    for _,r in g.sort_values("t").iterrows():
        cr,_=cruzada(vol,r["t"])
        if cr is None: continue
        Rr,_=cr
        key=(Rr["shape"], float(Rr["lat"][0,0]), float(np.nansum(Rr["L"][:3,:3])))
        if key in paths: continue
        paths.add(key)
        e=(np.nan_to_num(Rr["z"],nan=-99)>=zc[vol]).astype(float)
        if acc is None:
            acc=e; n=1; geo[vol]=(Rr["lat"],Rr["lon"])
        elif e.shape==acc.shape:
            acc=acc+e; n+=1
    if acc is not None:
        clim[vol]=acc/n
        print("  %-22s %d rasteres, tasa media de celda %.4f"%(vol,n,float(np.nanmean(clim[vol]))),flush=True)
    raster.cache_clear()
# 2) valor climatologico en P y en X, y por sector de acimut
C=pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy()
PM={(v,t):p for v,t,p in zip(df.vol,df.t,df.P)}
rows=[]
rng_X=random.Random(7144)
for vol in sorted(VOLS):
    g=H[H.vol==vol]
    if not len(g) or vol not in zc.index: continue
    v=vent(vol)
    la,lo = geo.get(vol,(None,None))
    if la is None: continue
    d0=hav(la,lo,v[0],v[1])
    dn=(la-v[0])*110.574; de=(lo-v[1])*111.320*math.cos(math.radians(v[0]))
    az0=(np.degrees(np.arctan2(de,dn)))%360.0
    ban=(d0>=1.5)&(d0<=3.0)
    cl=clim[vol]
    for _,r in g.sort_values("t").iterrows():
        P=r["P"]
        if P is None or P[0] is None: continue
        X,_,_,_=sortear_sep(rng_X,v,P,modo="par")
        if (vol,r["t"]) not in set(zip(C.vol,C.t)): continue
        out={}
        for nom,pt in (("P",P),("X",X)):
            dd=hav(la,lo,pt[0],pt[1]); m=dd<=0.75
            out["sitio_"+nom]=float(np.nanmax(cl[m])) if m.any() else np.nan
            _,az=radio_az(vol,pt)
            ms=ban & (np.minimum(np.abs(az0-az),360-np.abs(az0-az))<=15)
            out["sector_"+nom]=float(np.nanmean(cl[ms])) if ms.any() else np.nan
        out.update(vol=vol,noche=r["noche"])
        out["banda"]=float(np.nanmean(cl[ban]))
        rows.append(out)
D=pd.DataFrame(rows).dropna()
print("\n== climatologia del exceso (fraccion de rasteres en que se supera zc) ==")
print("  n=%d"%len(D))
print("  sitio  P: %.4f   X: %.4f   razon %.2f" % (D.sitio_P.mean(), D.sitio_X.mean(), D.sitio_P.mean()/max(D.sitio_X.mean(),1e-9)))
print("  sector P: %.4f   X: %.4f   banda entera: %.4f" % (D.sector_P.mean(), D.sector_X.mean(), D.banda.mean()))
print("  el sector de P esta %.2fx sobre la banda; el sitio de P esta %.2fx sobre el sitio de X"
      %(D.sector_P.mean()/max(D.banda.mean(),1e-9), D.sitio_P.mean()/max(D.sitio_X.mean(),1e-9)))
print("\n-- por volcan --")
print(D.groupby("vol").agg(n=("sitio_P","size"),sitio_P=("sitio_P","mean"),sitio_X=("sitio_X","mean"),
                           sector_P=("sector_P","mean"),sector_X=("sector_X","mean"),banda=("banda","mean")).round(4).to_string())
