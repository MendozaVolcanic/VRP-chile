# S197 #1106: campo de contraste del detector de la vía (producción, sin tocar) alrededor del cráter,
# desde el recorte nativo que guardó el probe (run 45290835369). Captura el diagnóstico de detectar_mirova.
import sys, os, json, numpy as np
sys.path.insert(0, "D:/vrp-trabajo/worktrees/s197-1106-probe")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline import mirova_v750_codigo as MV
npz, vlat, vlon, inner, sensor, ylat, ylon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], float(sys.argv[6]), float(sys.argv[7])
z = np.load(npz)
ang = {k: z[k] for k in z.files if k not in ("mir", "tir", "lat", "lon")}
cap = {}
orig = MV.detectar_mirova
def espia(*a, **k):
    m, d = orig(*a, **k); cap["d"] = d; cap["a"] = a; return m, d
MV.detectar_mirova = espia
nombre = MV.volcan_por_coordenadas(ylat, ylon)  # como p1_runner: grilla por las coordenadas del yaml, cráter por el ancla
rec = MV.calcular_vrp_granulo({"MIR": z["mir"], "TIR": z["tir"]}, z["lat"], z["lon"], ang, nombre, vlat, vlon, inner,
                              sensor, familia="MODIS")
print("record vrp", rec.get("vrp_mw"), "n", rec.get("n_anomalous_pixels"))
d, a = cap["d"], cap["a"]
m13g, m15g, box = a[0], a[1], a[2]
g = MV.grilla_del_volcan(nombre, paso_m=MV.FAMILIAS["MODIS"]["paso_m"], clave_roi="roi_modis")
celda = MV.celda_de(g, vlat, vlon)
print("celda crater", celda, "paso", g["paso"], "claves diag", sorted(d.keys()))
cn, ce = d["contrastes"][1]
s1 = {k: v for k, v in d.items() if not hasattr(v, "shape")}
print("diag escalar", json.dumps({k: (v if isinstance(v, (int, float, str, type(None))) else str(v)[:120]) for k, v in s1.items()}, default=str)[:1500])
r0, c0 = celda
paso = g["paso"] / 1000.0
rows = []
for r in range(r0 - 6, r0 + 7):
    for c in range(c0 - 6, c0 + 7):
        dist = paso * np.hypot(r - r0, c - c0)
        rows.append((r, c, round(dist, 2), int(box[r, c]), float(cn[r, c]), float(ce[r, c])))
print("celdas con dist 2,5 a 4,5 km ordenadas por c_nti:")
for t in sorted([x for x in rows if 2.5 <= x[2] <= 4.5], key=lambda x: -x[4])[:10]:
    print("  fila %d col %d dist %.2f zona %d c_nti %.5f c_eti %.5f" % t)
print("top 10 c_nti en +-6 celdas:")
for t in sorted(rows, key=lambda x: -x[4])[:10]:
    print("  fila %d col %d dist %.2f zona %d c_nti %.5f c_eti %.5f" % t)
np.set_printoptions(linewidth=250, precision=1, suppress=True)
print("mapa c_nti x1000 (+-6, fila arriba = menor índice):")
print(np.round(cn[r0-6:r0+7, c0-6:c0+7] * 1000, 1))
print("mapa zona:"); print(box[r0-6:r0+7, c0-6:c0+7])
