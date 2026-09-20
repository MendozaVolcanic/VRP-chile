# Eje 2 LITERAL de la v7: Theta_p = e_p - fraccion de e en el MISMO P en los 5 rasteres
# usables mas cercanos de otras noches (>3 d). Solo estrato hermano.
import os, sys, pickle, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import *  # noqa
C = pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy()
PM = {(v,t):p for v,t,p in zip(df.vol, df.t, df.P)}
C["P"] = [PM[(v,t)] for v,t in zip(C.vol, C.t)]
rows=[]; t0=time.time()
for vol, g in C.groupby("vol"):
    ix = idx_v[vol]
    for _, r in g.iterrows():
        t_p=r["t"]
        dd=(ix.acquisition_utc-t_p).dt.total_seconds()
        m=dd.abs()>3*86400
        cand=ix[m]; ordn=np.argsort(dd[m].abs().values)
        zs=[]
        for i in ordn:
            if len(zs)>=5: break
            rr=cand.iloc[i]
            Rq,_=usable({"own":bool(rr["own"]),"path":rr["path"]}, vol)
            if Rq is None: continue
            z=Z(Rq, r["P"])
            if z is None: continue
            zs.append(float(z>=zc[vol]))
        if len(zs)<5: 
            rows.append(dict(vol=vol,t=t_p,noche=r["noche"],estado="pocos",n=len(zs))); continue
        rows.append(dict(vol=vol,t=t_p,noche=r["noche"],estado="ok",n=5,
                         e=r["e_P"], base=float(np.mean(zs)), th=r["e_P"]-float(np.mean(zs))))
    raster.cache_clear(); print("  ...%s (%.0fs)"%(vol,time.time()-t0),flush=True)
T=pd.DataFrame(rows); pickle.dump(T,open("eje2.pkl","wb"))
O=T[T.estado=="ok"]
lo,hi=boot(O.th.values,O.vol.values,O.noche.values)
print("\n== EJE 2 LITERAL (5 rasteres de otras noches, mismo P) ==")
print("  n=%d  Theta=%+.4f  IC95 [%+.4f, %+.4f]   e_p=%.4f  base(otras noches)=%.4f"
      %(len(O),O.th.mean(),lo,hi,O.e.mean(),O.base.mean()))
print(O.groupby("vol").agg(n=("th","size"),Theta=("th","mean"),e=("e","mean"),base=("base","mean")).round(3).to_string())
print("  estados:",T.estado.value_counts().to_dict())
