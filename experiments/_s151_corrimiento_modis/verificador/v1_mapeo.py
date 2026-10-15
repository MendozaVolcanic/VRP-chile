# Verificador del PR #826 (contexto limpio): reproduce el mapeo de _interp_geo con la funcion REAL y lo pasa a km.
# Copiado desde la carpeta temporal del verificador; solo cambia la ruta del repo, que ahora es relativa.
import sys, math, numpy as np, scipy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pipeline.process_modis import _interp_geo
print("scipy", scipy.__version__)
NL, NS = 2030, 1354
# rampa de frames verdaderos en la grilla gruesa: columna j <-> frame 2+5j ; fila i <-> linea (i//2)*10 + 2 + 5*(i%2)
cols = 2 + 5*np.arange(271, dtype=np.float64)
rows = np.array([(i//2)*10 + 2 + 5*(i % 2) for i in range(406)], dtype=np.float64)
cf = np.tile(cols, (406, 1)).astype(np.float32)
rf = np.tile(rows[:, None], (1, 271)).astype(np.float32)
F = _interp_geo(cf, NL, NS); L = _interp_geo(rf, NL, NS)
s = np.arange(NS)
a, b = np.polyfit(s, F[1000], 1)
print("frame: asignado = %.5f*s + %.4f ; extremos %s %s" % (a, b, F[1000, :3], F[1000, -3:]))
l = np.arange(NL); a2, b2 = np.polyfit(l, L[:, 500], 1)
print("linea: asignado = %.5f*l + %.4f ; offset en l=0: %.2f, l=1015: %.2f, l=2029: %.2f" % (a2, b2, L[0,500]-0, L[1015,500]-1015, L[2029,500]-2029))
# a km, geometria esferica, h=705 km, IFOV 1 km nadir
R, H = 6371.0, 705.0
def x(beta):
    return R*(math.asin(min(1,(R+H)/R*math.sin(beta))) - beta)
c = (NS-1)/2
def z_of(beta):
    return math.degrees(math.asin((R+H)/R*math.sin(beta)))
print("cenit  lado_frame0_km  otro_lado_km  (positivo = hacia nadir); tamano pixel cross km")
for zt in (5,10,17,20,25,31,35,40,45,50,55):
    bt = math.asin(R/(R+H)*math.sin(math.radians(zt)))
    out=[]
    for sgn in (-1,1):
        sv = c + sgn*bt*H
        if not (0 <= sv <= NS-1): out.append(float('nan')); continue
        t = float(np.interp(sv, s, F[1000]))
        xs, xt = x((sv-c)/H), x((t-c)/H)
        out.append((xt-xs)*(1 if xs<0 else -1))
    dpx = (x(bt+0.5/H)-x(bt-0.5/H))
    print("%4d   %6.2f   %6.2f   %5.2f" % (zt, out[0], out[1], dpx))
