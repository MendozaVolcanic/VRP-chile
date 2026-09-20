import os, sys, pickle, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import *  # noqa
t0=time.time()
H = herm()
D = corre(H, "otra", "otra_noche")
pickle.dump(D, open("h_otra.pkl","wb"))
print("estados:", D.estado.value_counts().to_dict(), " %.0fs"%(time.time()-t0))
O=D[D.estado=="ok"]
print("tasas: P=%.4f X=%.4f S=%.4f A=%.4f B=%.4f"%(O.e_P.mean(),O.e_X.mean(),O.e_S.mean(),O.e_A.mean(),O.e_B.mean()))
d=(O.e_P-O.e_X).values
lo,hi=boot(d,O.vol.values,O.noche.values)
print("EJE1 con raster de OTRA NOCHE (>3 d): n=%d D=%+.4f IC95 [%+.4f, %+.4f]"%(len(O),d.mean(),lo,hi))
d2=(O.e_P-O.e_S).values; lo,hi=boot(d2,O.vol.values,O.noche.values)
print("  P - S (mismo radio), otra noche:      n=%d D=%+.4f IC95 [%+.4f, %+.4f]"%(len(O),d2.mean(),lo,hi))
d3=(O.e_A-O.e_B).values; lo,hi=boot(d3,O.vol.values,O.noche.values)
print("  nulo A-B, otra noche:                 n=%d D=%+.4f IC95 [%+.4f, %+.4f]"%(len(O),d3.mean(),lo,hi))
print(O.groupby("vol").agg(n=("e_P","size"),eP=("e_P","mean"),eX=("e_X","mean"),eS=("e_S","mean")).round(3).to_string())
