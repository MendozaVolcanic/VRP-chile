import os, sys, pickle, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import *  # noqa
H = herm()
D = corre(H, "propia", "propia")
pickle.dump(D, open("h_prop.pkl","wb"))
print("estados:", D.estado.value_counts().to_dict())
O=D[D.estado=="ok"]
C=pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy()
O["k"]=list(zip(O.vol,O.t)); C["k"]=list(zip(C.vol,C.t))
i=set(O.k)&set(C.k)
a=O[O.k.isin(i)].sort_values(["vol","t"]).reset_index(drop=True)
b=C[C.k.isin(i)].sort_values(["vol","t"]).reset_index(drop=True)
print("\n== CONTROL B con el estadistico de la v7 (P - X), mismas %d pasadas ==" % len(a))
for nom,s in (("imagen PROPIA",a),("imagen CRUZADA",b)):
    d=(s.e_P-s.e_X).values; lo,hi=boot(d,s.vol.values,s.noche.values)
    print("  %-16s D=%+.4f IC95 [%+.4f, %+.4f]  tasa P=%.4f tasa X=%.4f"%(nom,d.mean(),lo,hi,s.e_P.mean(),s.e_X.mean()))
d=((a.e_P-a.e_X)-(b.e_P-b.e_X)).values; lo,hi=boot(d,a.vol.values,a.noche.values)
print("  diferencia (lo que corta la pasada cruzada) = %+.4f [%+.4f, %+.4f]"%(d.mean(),lo,hi))
# tambien sobre TODAS las que tienen imagen propia
d=(O.e_P-O.e_X).values; lo,hi=boot(d,O.vol.values,O.noche.values)
print("  imagen propia, las %d que la tienen: D=%+.4f [%+.4f,%+.4f]"%(len(O),d.mean(),lo,hi))
