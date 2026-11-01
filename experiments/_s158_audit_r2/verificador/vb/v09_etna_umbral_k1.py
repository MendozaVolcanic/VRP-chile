"""VB v09: la pasada de ejemplo del codigo de MIROVA (Etna, VIIRS750_example.mat) ejercita el umbral K1?
Leo el .mat con scipy y calculo el NTI = (M13 - M15)/(M13 + M15) de toda la matriz. Si ningun pixel cae entre -0,8 y
-0,7 (nuestro K1 contra el del codigo) ni cerca, la pasada no distingue los dos umbrales. Cuento tambien los pixeles
por encima de -0,7 y de -0,8. Control: el maximo NTI tiene que estar muy arriba (la pasada tiene un foco).
Solo lectura de datos; no ejecuto MATLAB."""
import sys, io
import numpy as np
from scipy.io import loadmat
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
S = loadmat(sys.argv[1])
print("variables:", sorted(k for k in S if not k.startswith("__")))
m13, m15 = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float)
nti = (m13 - m15) / (m13 + m15)
v = nti[np.isfinite(nti)]
print("pixeles validos", v.size, "NTI max", round(float(v.max()), 4), "p99", round(float(np.percentile(v, 99)), 4),
      "mediana", round(float(np.median(v)), 4))
for lo, hi in ((-0.8, -0.7), (-0.85, -0.65)):
    print(f"pixeles con NTI en [{lo},{hi}):", int(((v >= lo) & (v < hi)).sum()))
print("pixeles > -0.7:", int((v > -0.7).sum()), " > -0.8:", int((v > -0.8).sum()), " > -0.5:", int((v > -0.5).sum()))
print("dayflag", S.get("dayflag"), "BOX clases", np.unique(S["BOX"]) if "BOX" in S else None)
