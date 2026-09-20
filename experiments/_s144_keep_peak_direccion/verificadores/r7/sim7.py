import os, sys, math, pickle
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
V6=os.path.abspath(HERE+"/../v6")
C = pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy()
C["d1"]=C.e_P-C.e_X; C["dn"]=C.e_A-C.e_B
E = pickle.load(open(V6+"/e6.pkl","rb")); F=E[(E.est=="ok")&(E.n_ref>=3)]
NN = F.groupby("vol").noche.nunique().to_dict()
ELIG=[v for v,n in NN.items() if n>=20]
print("muestra del veredicto: %d pasadas, %d noches de volcan, elegibles %s"%(len(F),sum(NN.values()),ELIG))
print("noches por volcan:", NN)

# --- re-ponderacion del efecto medido en el hermano a la mezcla del veredicto
Dv = C.groupby("vol").d1.mean()
nh = C.groupby("vol").noche.nunique(); wh=nh/nh.sum()
wv = pd.Series(NN, dtype=float); wv=wv.reindex(Dv.index).fillna(0); wv=wv/wv.sum()
print("\n== efecto eje1 del estrato hermano, re-ponderado ==")
print("  agrupado tal cual (mezcla del hermano) : %+.4f" % C.d1.mean())
print("  re-ponderado a la mezcla del veredicto : %+.4f" % float((Dv*wv).sum()))
print("  solo los 6 volcanes elegibles          : %+.4f" % C[C.vol.isin(ELIG)].d1.mean())
cmp=pd.DataFrame({"D_eje1":Dv,"peso_hermano":wh,"peso_veredicto":wv}).round(3)
print(cmp.to_string()); print("  distancia L1 de composiciones: %.3f"%float((cmp.peso_hermano-cmp.peso_veredicto).abs().sum()))

# --- bloques de nulo (pares sorteados A-B) por volcan
blk={}
for (v,n),g in C.groupby(["vol","noche"]):
    blk.setdefault(v,[]).append(g.dn.values)
todos=[b for v in blk for b in blk[v]]
print("\nnulo A-B: media %+.4f  bloques %d  %% de ceros %.3f"%(C.dn.mean(),len(todos),(C.dn==0).mean()))
print("eje1 P-X: media %+.4f  %% de ceros %.3f"%(C.d1.mean(),(C.d1==0).mean()))

def boot_ic(vals,Bn=300,rng=None):
    out=[]
    for _ in range(Bn):
        allv=[]
        for v,bs in vals.items():
            sel=rng.integers(0,len(bs),len(bs)); allv.append(np.concatenate([bs[i] for i in sel]))
        out.append(float(np.mean(np.concatenate(allv))))
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))

def sim(rep=200, delta=0.0, seed=7):
    rng=np.random.default_rng(seed); res=[]
    for _ in range(rep):
        vals={}
        for v,nn in NN.items():
            pool=blk.get(v) or todos
            if len(pool)<3: pool=todos
            sel=rng.integers(0,len(pool),nn); bs=[]
            for i in sel:
                d=pool[i].copy()
                if delta>0:
                    fl=rng.random(len(d))<delta
                    d=np.clip(np.where(fl,np.minimum(1.0,d+1.0),d),-1,1)
                bs.append(d)
            vals[v]=bs
        lo,hi=boot_ic(vals,rng=rng)
        Dm=float(np.mean(np.concatenate([np.concatenate(b) for b in vals.values()])))
        Dvv={v:float(np.mean(np.concatenate(b))) for v,b in vals.items()}
        c2 = sum(1 for v in ELIG if Dvv[v]>0) >= math.ceil(2/3*len(ELIG))
        pos = (lo>0.05) and c2
        equ = (lo>=-0.05) and (hi<=0.05)
        ver = "exceso" if pos else ("no se distingue" if equ else "INCONCLUSO")
        res.append((ver,Dm,lo,hi,hi-lo,pos,equ))
    return pd.DataFrame(res,columns=["ver","D","lo","hi","ancho","pos","equ"])

print("\n== regla de la v7 (contra cero), estructura real de noches ==")
for dl in (0.0,0.02,0.035,0.05,0.064,0.083,0.10,0.131,0.16,0.20):
    r=sim(rep=200 if dl==0 else 150, delta=dl, seed=11+int(dl*1000))
    vc=r.ver.value_counts(); n=len(r)
    print("  delta=%.3f  D medido %+.4f  ancho %.4f -> exceso %3.0f%%  no se distingue %3.0f%%  INCONCLUSO %3.0f%%"
          %(dl,r.D.mean(),r.ancho.mean(),100*vc.get("exceso",0)/n,100*vc.get("no se distingue",0)/n,100*vc.get("INCONCLUSO",0)/n))
