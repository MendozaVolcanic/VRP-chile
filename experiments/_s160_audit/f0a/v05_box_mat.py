"""V0a (verificador de F6-7 b y F1-H4 lectura de regiones): layout de BOX en el .mat de ejemplo del OSF.
Pregunta 1: si la clase 2 no fuera la caja central, la bounding box de la clase 2 no estaria centrada en (33,33).
Pregunta 2: control = la clase 0 debe ser la mayoria y el centro (33,33) debe tener alguna clase.
"""
import numpy as np, scipy.io as sio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
S = sio.loadmat(r"C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
B = S["BOX"].astype(float)
print("size", B.shape, "dayflag", S["dayflag"].ravel(), "acq", S.get("acquisition_id"))
for c in (0, 1, 2):
    rr, cc = np.where(B == c)
    print(f"clase {c}: n={len(rr)} filas {rr.min()}-{rr.max()} cols {cc.min()}-{cc.max()} (base 0)")
print("NaN en BOX:", int(np.isnan(B).sum()), "; centro (33,33) clase:", B[33, 33])
print("fila 33:", "".join(str(int(x)) if not np.isnan(x) else "." for x in B[33, :]))
