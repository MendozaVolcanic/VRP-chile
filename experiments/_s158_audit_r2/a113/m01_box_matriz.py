# M01: geometria de BOX en la matriz de ejemplo de MIROVA.
# Pregunta 1 (si lo medido estuviera roto, lo veria?): si BOX==2 no fuera la caja central,
#   el conteo por clase y el bounding box lo mostrarian.
# Pregunta 2 (instrumento muerto?): imprime shape y conteos de todas las clases; un archivo
#   vacio o mal leido daria shape 0 o clases ausentes.
import scipy.io as sio, numpy as np, sys
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_d17_diseno\osf_codigo_mirova\Example\VIIRS750_example.mat"
S = sio.loadmat(p)
print("keys:", [k for k in S if not k.startswith("__")])
B = np.array(S["BOX"], dtype=float)
print("shape BOX:", B.shape)
vals, cnt = np.unique(B[~np.isnan(B)], return_counts=True)
print("clases:", dict(zip(vals.tolist(), cnt.tolist())), "NaN:", int(np.isnan(B).sum()))
for v in vals:
    r, c = np.where(B == v)
    print(f"clase {v}: filas {r.min()}-{r.max()} cols {c.min()}-{c.max()} n={len(r)}")
print("centro matriz:", (B.shape[0]-1)/2, (B.shape[1]-1)/2)
for k in ["dayflag","sat_zen","sun_zen","acquisition_id"]:
    if k in S: print(k, S[k])
