import os, sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import boot
D = pickle.load(open("h_cruz.pkl","rb"))
O = D[D.estado=="ok"].copy()
print("n ok =", len(O))
# atricion: Z None
for k in ["P","X","Xaz","A","B","Bfree","S","M"]:
    c="z_"+k
    n_none = int(O[c].isna().sum())
    print("  %-6s Z None en %d de %d (%.2f%%)  tasa e=%.4f" % (k, n_none, len(O), 100*n_none/len(O), O["e_"+k].mean()))
print()
def linea(nom, a, b, sub=None):
    s = O if sub is None else sub
    m = s["e_"+a].notna() & s["e_"+b].notna()
    s = s[m]
    d = (s["e_"+a]-s["e_"+b]).values
    lo,hi = boot(d, s.vol.values, s.noche.values)
    print("  %-34s n=%4d  D=%+.4f  IC95 [%+.4f, %+.4f]   tasa %s=%.4f  tasa %s=%.4f"
          % (nom, len(s), d.mean(), lo, hi, a, s["e_"+a].mean(), b, s["e_"+b].mean()))
    return d
print("== estadistico de la v7 y sus nulos, estrato hermano, raster cruzado 45-120 min ==")
linea("EJE1 literal: P - X", "P","X")
linea("nulo N1 lectura CON separacion: A - B", "A","B")
linea("nulo N1 lectura SIN separacion: A - Bfree", "A","Bfree")
linea("P - X(solo acimut re-sorteado)", "P","Xaz")
linea("P - S(mismo radio que P)", "P","S")
linea("P - M(reflejo de P)", "P","M")
linea("X - A (dos sorteos de streams distintos)","X","A")
print()
print("== por volcan, EJE1 literal ==")
O["d1"]=O.e_P-O.e_X; O["dS"]=O.e_P-O.e_S; O["dN"]=O.e_A-O.e_B
t=O.groupby("vol").agg(n=("d1","size"), noches=("noche","nunique"), D_eje1=("d1","mean"),
                        D_mismoR=("dS","mean"), D_nulo=("dN","mean"),
                        eP=("e_P","mean"), eX=("e_X","mean"))
print(t.round(3).to_string())
print()
print("== geometria: radio de P contra radio de X ==")
print("  r_P  mediana %.3f  media %.3f  p05 %.3f p95 %.3f  max %.3f" % (O.r_P.median(),O.r_P.mean(),O.r_P.quantile(.05),O.r_P.quantile(.95),O.r_P.max()))
print("  r_X  mediana %.3f  media %.3f  p05 %.3f p95 %.3f  max %.3f" % (O.r_X.median(),O.r_X.mean(),O.r_X.quantile(.05),O.r_X.quantile(.95),O.r_X.max()))
print("  fraccion r_P > 2.5 km: %.3f   fraccion r_X > 2.5 km: %.3f" % ((O.r_P>2.5).mean(),(O.r_X>2.5).mean()))
print("  iteraciones de rechazo para X: media %.2f  max %d  (fraccion con >=1: %.3f)" % (O.it_X.mean(),O.it_X.max(),(O.it_X>0).mean()))
print("  d(P,X) mediana %.3f km  minimo %.3f" % (O.d_PX.median(), O.d_PX.min()))
# tasa de exceso por radio (con los sorteos libres A y Bfree, que no dependen de P)
import numpy as np
for nom,rc,ec in (("A",'r_A','e_A'),):
    pass
