import os, sys, pickle, collections
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import *  # noqa
idx = load_idx("VIIRS375")
print("TIF en el indice VIIRS375 con archivo: %d" % len(idx))
sh=collections.Counter(); ep=collections.Counter(); cel=[]; ext=[]
import random as _r
rows=[]
for vol, g in idx.groupby("vol"):
    gg = g.sample(min(12,len(g)), random_state=1)
    for _, r in gg.iterrows():
        R = raster(r["path"])
        if R is None: 
            ep["sin_crs"]+=1; continue
        sh[R["shape"]]+=1; ep[R["epsg"]]+=1
        dy,dx = celda_km(R)
        v=vent(vol)
        d = hav(R["lat"],R["lon"],v[0],v[1])
        rows.append(dict(vol=vol, shape=str(R["shape"]), epsg=R["epsg"], dy=dy, dx=dx,
                         dmax=float(d.max()), dmin_borde=float(min(d[0,:].min(),d[-1,:].min(),d[:,0].min(),d[:,-1].min())),
                         nanfrac=R["nan_frac"]))
    raster.cache_clear()
T=pd.DataFrame(rows)
print("formas:", dict(sh))
print("epsg:", dict(ep))
print(T.groupby("vol").agg(n=("dy","size"), dy_km=("dy","mean"), dx_km=("dx","mean"),
                           borde_mas_cercano_km=("dmin_borde","min"), nan=("nanfrac","mean")).round(3).to_string())
# nodata por radio, promediado
acc={}
for vol, g in idx.groupby("vol"):
    gg=g.sample(min(8,len(g)), random_state=2); v=vent(vol)
    prof=[]
    for _,r in gg.iterrows():
        R=raster(r["path"])
        if R is None: continue
        d=hav(R["lat"],R["lon"],v[0],v[1])
        f=[]
        for lo_,hi_ in [(0,1),(1,1.5),(1.5,2),(2,2.5),(2.5,3),(3,4)]:
            m=(d>=lo_)&(d<hi_)
            f.append(float(np.mean(~np.isfinite(R["z"][m]))) if m.any() else np.nan)
        prof.append(f)
    raster.cache_clear()
    if prof: acc[vol]=np.nanmean(np.array(prof),axis=0)
P=pd.DataFrame(acc, index=["0-1","1-1.5","1.5-2","2-2.5","2.5-3","3-4"]).T
print("\n== fraccion de celdas SIN z (dL0) por anillo de radio (media de 8 TIF por volcan) ==")
print(P.round(3).to_string())
