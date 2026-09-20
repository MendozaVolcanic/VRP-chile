import os, sys, math, pickle
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
D=pickle.load(open(HERE+"/c6.pkl","rb")); E=pickle.load(open(HERE+"/e6.pkl","rb"))
F=E[(E.est=="ok")&(E.n_ref>=3)]
na=D["N1a"]; na=na[na.estado=="ok"]
nc=na[(na.vol!="Lastarria")&(na.lab=="neg_limpio")]
blk={}
for (v,n),g in nc.groupby(["vol","noche"]): blk.setdefault(v,[]).append(g.d.values)
todos=[b for v in blk for b in blk[v]]
ro=D["R"]; ro=ro[ro.estado=="ok"]
rblk=[g.d.values for _,g in ro.groupby([ro.vol,ro.noche])]
def boot_ic(vals,Bn=300,rng=None):
    out=[]
    for _ in range(Bn):
        allv=[]
        for v,bs in vals.items():
            sel=rng.integers(0,len(bs),len(bs)); allv.append(np.concatenate([bs[i] for i in sel]))
        out.append(float(np.mean(np.concatenate(allv))))
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))
def boot_s(bs,Bn=300,rng=None):
    out=[]
    for _ in range(Bn):
        sel=rng.integers(0,len(bs),len(bs)); out.append(float(np.mean(np.concatenate([bs[i] for i in sel]))))
    return float(np.mean(out)),float(np.percentile(out,2.5)),float(np.percentile(out,97.5))
def sim(NN,rep=80,seed=5):
    rng=np.random.default_rng(seed); ELIG=[v for v,n in NN.items() if n>=20]; res=[]
    for _ in range(rep):
        vals={}
        for v,nn in NN.items():
            pool=blk.get(v) or todos
            if len(pool)<3: pool=todos
            sel=rng.integers(0,len(pool),nn); vals[v]=[pool[i] for i in sel]
        lo,hi=boot_ic(vals,rng=rng)
        sel=rng.integers(0,len(rblk),len(rblk)); Rp,Rlo,Rhi=boot_s([rblk[i] for i in sel],rng=rng)
        Dv={v:float(np.mean(np.concatenate(b))) for v,b in vals.items()}
        c2=(sum(1 for v in ELIG if Dv[v]>0)>=math.ceil(2/3*len(ELIG))) if ELIG else None
        pos=(lo>max(0.05,Rhi)) and bool(c2); equ=(lo>=Rp-0.05) and (hi<=Rp+0.05)
        res.append(("cae sobre un exceso" if pos else ("no se distingue" if equ else "INCONCLUSO"),hi-lo))
    r=pd.DataFrame(res,columns=["ver","ancho"]); return r
for nom in ("pre","post"):
    NN=F[F.tramo==nom].groupby("vol").noche.nunique().to_dict()
    elig=[v for v,n in NN.items() if n>=20]
    r=sim(NN)
    print("tramo %-4s: %d noches, elegibles>=20: %d %s  ancho medio %.3f  -> %s"
          %(nom,sum(NN.values()),len(elig),elig,r.ancho.mean(),r.ver.value_counts().to_dict()))
print()
print("fraccion de d_p exactamente cero, estrato hermano con la ventana v6: %.3f"%float((ro.d==0).mean()))
print("fraccion de d_p exactamente cero, nulo N1a:                          %.3f"%float((na.d==0).mean()))
