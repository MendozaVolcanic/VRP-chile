# R contra el nulo del instrumento SOBRE LAS MISMAS PASADAS del estrato hermano.
# Separa "residuo del instrumento" de "efecto del sitio P". Solo lectura, fuera del veredicto.
import os, sys, pickle, random
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
for p in (os.path.abspath(HERE+"/../v3"), os.path.abspath(HERE+"/../v4"), HERE): sys.path.insert(0,p)
from common3 import *  # noqa
from c6 import df, medir  # noqa
HER = df[df.patron & df.pub & (df.vol!="Lastarria") & df.lab.isin(["far_ref","sin_info"])].copy()
N = medir(HER, "null", rng=random.Random(2144))
pickle.dump(N, open(HERE+"/par6.pkl","wb"))
D=pickle.load(open(HERE+"/c6.pkl","rb")); ro=D["R"]; ro=ro[ro.estado=="ok"].copy()
no=N[N.estado=="ok"].copy()
def boot(s,Bn=2000,seed=144,col="d"):
    g=np.random.default_rng(seed); key=(s.vol+"|"+s.noche).values
    noches={v:np.array(sorted(set(key[(s.vol==v).values]))) for v in s.vol.unique()}
    porn={k:v[col].values for k,v in s.groupby(key)}
    out=[]
    for _ in range(Bn):
        vals=[]
        for v,ns in noches.items():
            sel=g.choice(ns,len(ns),True); vals.append(np.concatenate([porn[k] for k in sel]))
        out.append(float(np.mean(np.concatenate(vals))))
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))
print("\n== estrato hermano, ventana v6: observado = nuestro P  contra  observado = punto sorteado ==")
for nom,s in (("R (observado = nuestro P)",ro),("nulo (observado = punto sorteado)",no)):
    lo,hi=boot(s)
    print("  %-36s n=%4d D=%+.4f IC95 [%+.4f, %+.4f] obs=%.3f ref=%.3f"%(nom,len(s),s.d.mean(),lo,hi,s.e.mean(),s.r.mean()))
ro["k"]=list(zip(ro.vol,ro.t)); no["k"]=list(zip(no.vol,no.t))
inter=set(ro.k)&set(no.k)
a=ro[ro.k.isin(inter)]; b=no[no.k.isin(inter)]
print("  mismas pasadas (n=%d): R %+.4f  nulo %+.4f  diferencia %+.4f"%(len(inter),a.d.mean(),b.d.mean(),a.d.mean()-b.d.mean()))
print("\n  -- por volcan sobre las mismas pasadas --")
t=pd.DataFrame({"R":a.groupby("vol").d.mean(),"nulo":b.groupby("vol").d.mean(),"n":a.groupby("vol").d.size()})
t["dif"]=t.R-t.nulo
print(t.round(3).to_string())
