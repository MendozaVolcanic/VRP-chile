import os, sys, pickle
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b7 import boot
C = pickle.load(open("h_cruz.pkl","rb")); C=C[C.estado=="ok"].copy()
N = pickle.load(open("h_otra.pkl","rb")); N=N[N.estado=="ok"].copy()
C["k"]=list(zip(C.vol,C.t)); N["k"]=list(zip(N.vol,N.t))
i=set(C.k)&set(N.k)
a=C[C.k.isin(i)].sort_values(["vol","t"]).reset_index(drop=True)
b=N[N.k.isin(i)].sort_values(["vol","t"]).reset_index(drop=True)
assert (a.k==b.k).all()
print("== MISMAS %d pasadas del estrato hermano ==" % len(a))
def ln(nom, d, s):
    lo,hi=boot(d, s.vol.values, s.noche.values)
    print("  %-46s D=%+.4f  IC95 [%+.4f, %+.4f]" % (nom, np.mean(d), lo, hi))
ln("eje1 con raster de la MISMA noche (45-120 min)", (a.e_P-a.e_X).values, a)
ln("eje1 con raster de OTRA noche (>3 d)",           (b.e_P-b.e_X).values, b)
ln("diferencia (componente 'de esta noche')",        ((a.e_P-a.e_X)-(b.e_P-b.e_X)).values, a)
ln("EJE2 pareado: e_P(misma noche) - e_P(otra noche)", (a.e_P-b.e_P).values, a)
print("   tasas: e_P misma %.4f  e_P otra %.4f  e_X misma %.4f  e_X otra %.4f"
      % (a.e_P.mean(), b.e_P.mean(), a.e_X.mean(), b.e_X.mean()))
print()
print("== descomposicion de eje1 (misma noche, n=%d) ==" % len(a))
print("  tasa P              %.4f" % a.e_P.mean())
print("  tasa S (mismo radio)%.4f   -> componente de RADIO = %+.4f (%.0f%% del total)"
      % (a.e_S.mean(), a.e_S.mean()-a.e_X.mean(), 100*(a.e_S.mean()-a.e_X.mean())/(a.e_P.mean()-a.e_X.mean())))
print("  tasa X (uniforme)   %.4f   -> componente ACIMUT+SITIO a radio fijo = %+.4f (%.0f%%)"
      % (a.e_X.mean(), a.e_P.mean()-a.e_S.mean(), 100*(a.e_P.mean()-a.e_S.mean())/(a.e_P.mean()-a.e_X.mean())))
