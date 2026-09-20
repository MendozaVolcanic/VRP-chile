import os, sys, math, pickle
import numpy as np, pandas as pd
sys.path.insert(0,'.')
V6=os.path.abspath("../v6")
C=pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy(); C["d1"]=C.e_P-C.e_X; C["dn"]=C.e_A-C.e_B
E=pickle.load(open(V6+"/e6.pkl","rb")); F=E[(E.est=="ok")&(E.n_ref>=3)]
print("== muestra del veredicto por tramo ==")
for t,g in F.groupby("tramo"):
    nn=g.groupby("vol").noche.nunique()
    print("  tramo %-5s %d pasadas  %d noches de volcan  volcanes >=20 noches: %d %s"
          %(t,len(g),g.groupby(["vol","noche"]).ngroups,int((nn>=20).sum()),[v for v in nn.index if nn[v]>=20]))
blk={}
for (v,n),g in C.groupby(["vol","noche"]): blk.setdefault(v,[]).append(g.dn.values)
todos=[b for v in blk for b in blk[v]]
def anchos(NN, rep=120, seed=5):
    rng=np.random.default_rng(seed); W=[]; VER=[]
    ELIG=[v for v,n in NN.items() if n>=20]
    for _ in range(rep):
        vals={}
        for v,nn in NN.items():
            pool=blk.get(v) or todos
            if len(pool)<3: pool=todos
            sel=rng.integers(0,len(pool),nn); vals[v]=[pool[i] for i in sel]
        out=[]
        for _b in range(300):
            allv=[]
            for v,bs in vals.items():
                s=rng.integers(0,len(bs),len(bs)); allv.append(np.concatenate([bs[i] for i in s]))
            out.append(float(np.mean(np.concatenate(allv))))
        lo,hi=np.percentile(out,[2.5,97.5]); W.append(hi-lo)
        VER.append("no se distingue" if (lo>=-0.05 and hi<=0.05) else ("exceso" if (lo>0.05) else "INCONCLUSO"))
    return float(np.mean(W)), pd.Series(VER).value_counts().to_dict()
for t,g in F.groupby("tramo"):
    NN=g.groupby("vol").noche.nunique().to_dict()
    w,vc=anchos(NN)
    print("  tramo %-5s bajo el nulo: ancho medio del intervalo %.4f   %s"%(t,w,vc))
NN=F.groupby("vol").noche.nunique().to_dict()
w,vc=anchos(NN); print("  muestra completa: ancho %.4f  %s"%(w,vc))
print("\n== fraccion de Delta_p igual a cero ==")
print("  estadistico de la v7 (P - X):  %.3f" % (C.d1==0).mean())
print("  nulo A - B:                    %.3f" % (C.dn==0).mean())
