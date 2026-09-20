import os, sys, pickle
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE+"/../v3"), os.path.abspath(HERE+"/../v4"), HERE): sys.path.insert(0,p)
from common3 import *  # noqa
D=pickle.load(open(HERE+"/c6.pkl","rb"))
ro=D["R"]; ro=ro[ro.estado=="ok"].copy()
Z=pickle.load(open(os.path.abspath(HERE+"/../v5")+"/zc5.pkl","rb")); zc=Z["zc"]
print("== Isluga: zobs contra zref en el estrato hermano (zc=%.2f) =="%zc["Isluga"])
s=ro[ro.vol=="Isluga"]
zo=s.zobs.values; zr=np.concatenate([np.array(x) for x in s.zref])
print("  n pasadas=%d  zobs: mediana %.2f p90 %.2f max %.2f   >=zc: %d"%(len(s),np.median(zo),np.percentile(zo,90),zo.max(),(zo>=zc['Isluga']).sum()))
print("  n refs=%d    zref: mediana %.2f p90 %.2f max %.2f   >=zc: %d (%.1f%%)"%(len(zr),np.median(zr),np.percentile(zr,90),zr.max(),(zr>=zc['Isluga']).sum(),100*(zr>=zc['Isluga']).mean()))
print("\n  -- lo mismo por volcan: mediana de zobs contra mediana de zref --")
rows=[]
for v,g in ro.groupby("vol"):
    a=g.zobs.values; b=np.concatenate([np.array(x) for x in g.zref])
    rows.append(dict(vol=v,n=len(g),zc=round(float(zc[v]),2),med_obs=round(float(np.median(a)),2),
                     med_ref=round(float(np.median(b)),2),p95_obs=round(float(np.percentile(a,95)),2),
                     p95_ref=round(float(np.percentile(b,95)),2),
                     tasa_obs=round(float((a>=zc[v]).mean()),3),tasa_ref=round(float((b>=zc[v]).mean()),3)))
print(pd.DataFrame(rows).to_string(index=False))
