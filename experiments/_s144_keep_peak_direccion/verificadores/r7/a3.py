import os, sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0,'.')
from b7 import boot
O = pickle.load(open("h_cruz.pkl","rb")); O=O[O.estado=="ok"].copy()
def ln(nom,a,b):
    d=(O["e_"+a]-O["e_"+b]).values; lo,hi=boot(d,O.vol.values,O.noche.values)
    print("  %-40s %+.4f  IC95 [%+.4f, %+.4f]"%(nom,d.mean(),lo,hi))
print("== contrastes entre puntos sorteados (todos deberian dar 0) ==")
ln("S(radio de P) - X(uniforme)","S","X")
ln("A(libre) - Bfree(libre)","A","Bfree")
ln("A(libre) - X(con separacion de P)","A","X")
ln("B(con separacion de A) - A(libre)","B","A")
ln("M(reflejo de P) - X(uniforme)","M","X")
ln("S(radio de P) - M(reflejo de P)","S","M")
print("\n== promedio de e por punto ==")
for k in ["P","X","Xaz","A","B","Bfree","S","M"]:
    print("   %-6s %.4f" % (k,O["e_"+k].mean()))
# Delta_v: agrupado contra media de las medias por volcan
V6=os.path.abspath("../v6"); E=pickle.load(open(V6+"/e6.pkl","rb")); F=E[(E.est=="ok")&(E.n_ref>=3)]
NN=F.groupby("vol").noche.nunique().to_dict(); ELIG=[v for v,n in NN.items() if n>=20]
O["d1"]=O.e_P-O.e_X
Dv=O.groupby("vol").d1.mean()
print("\n== dos lecturas de 'Delta' en el estrato hermano ==")
print("  agrupado por pasada (lo que hace el remuestreo descrito): %+.4f" % O.d1.mean())
print("  media de las medias por volcan (10 volcanes)            : %+.4f" % Dv.mean())
print("  media de las medias, solo los 6 elegibles               : %+.4f" % Dv[ELIG].mean())
print("  agrupado por pasada, solo los 6 elegibles               : %+.4f" % O[O.vol.isin(ELIG)].d1.mean())
print("  Delta_v>0 entre los 6 elegibles: %d de 6  %s" % (int((Dv[ELIG]>0).sum()), Dv[ELIG].round(3).to_dict()))
