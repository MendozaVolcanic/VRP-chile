"""¿Qué interpolación reproduce el Tot_Lmir_bk del OSF en Etna? (fillmissing2 'linear' no está documentado).

Pregunta 1: si el port del fondo estuviera roto, ¿se vería? Sí, contra Tot_Lmir_bk = 1,072886152 del OSF v2.5, que
el port no lee. Pregunta 2: un instrumento muerto daría NaN o el mismo número para todos los métodos; abajo hay
métodos que discrepan entre sí, así que el instrumento distingue. Ventana: la pasada de Etna 2023-05-19 00:54.
Píxeles: los 5 que da el segundo oráculo (mismos Npix y L_hot que el OSF, control_etna_salida.txt).
"""
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.interpolate import griddata, LinearNDInterpolator
from scipy.spatial import Delaunay
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mirova_v750_r2 as M  # noqa: E402

S = sio.loadmat(AQUI.parents[1] / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat")
m13 = S["ZI_M13"].astype(float)
sg = M.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
mask, _ = M.detectar(m13, S["ZI_M15"], S["BOX"], 0, sg)
OSF_BK = 1.072886152
enm = m13.copy(); enm[mask] = np.nan
excl = binary_dilation(np.isnan(enm), structure=np.ones((5, 5), bool))
enm[excl] = np.nan
n, m = enm.shape
print("pixeles excluidos por la dilatacion 5x5:", int(excl.sum()))


def lbk(fondo):
    return float(fondo[mask].sum())


def delaunay_con(yy, xx):
    ok = ~np.isnan(enm)
    f = LinearNDInterpolator(np.column_stack([yy[ok], xx[ok]]), enm[ok])
    out = enm.copy(); out[~ok] = f(yy[~ok], xx[~ok]); return out


yy, xx = np.mgrid[0:n, 0:m].astype(float)
res = {}
res["delaunay_qhull_sin_perturbar"] = lbk(delaunay_con(yy, xx))
e = 1e-7
res["delaunay_cizalle_x+y"] = lbk(delaunay_con(yy, xx + e * yy))
res["delaunay_cizalle_x-y"] = lbk(delaunay_con(yy, xx - e * yy))
res["delaunay_cizalle_y+x"] = lbk(delaunay_con(yy + e * xx, xx))
res["delaunay_cizalle_y-x"] = lbk(delaunay_con(yy - e * xx, xx))


def fill_1d(A, eje):
    B = A.copy() if eje == 1 else A.T.copy()
    for i in range(B.shape[0]):
        r = B[i]; ok = ~np.isnan(r)
        if ok.sum() >= 2 and (~ok).any():
            r[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), r[ok])
    return B if eje == 1 else B.T


fr, fc = fill_1d(enm, 1), fill_1d(enm, 0)
res["lineal_por_filas"] = lbk(fr)
res["lineal_por_columnas"] = lbk(fc)
res["promedio_filas_columnas"] = lbk((fr + fc) / 2)


def laplace(A, it=20000):
    B = np.where(np.isnan(A), np.nanmean(A), A); fal = np.isnan(A)
    for _ in range(it):
        P = np.pad(B, 1, mode="edge")
        B[fal] = ((P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4)[fal]
    return B


res["laplace_armonico"] = lbk(laplace(enm))
v = [lbk(M._fillmissing2_lineal(enm, jitter=1e-6, semilla=s)) for s in range(200)]
res["delaunay_jitter_min_200"] = min(v)
res["delaunay_jitter_max_200"] = max(v)
mejor = int(np.argmin([abs(x - OSF_BK) for x in v]))
res["delaunay_jitter_mas_cercano"] = v[mejor]
for k, x in res.items():
    vrp = (m13[mask].sum() - x) * 1.97e7 * 0.5625
    print(f"{k:32s} L_bk={x:.9f}  razon_vs_OSF={x/OSF_BK:.6f}  VRP_W={vrp:.1f}")
print("OSF Tot_Lmir_bk =", OSF_BK, " VRP_W = 9889528.362")

# Cuántos fondos distintos produce el conjunto de triangulaciones, y cuántas semillas caen en el del OSF.
vals = np.round(np.array(v), 8)
uniq, cnt = np.unique(vals, return_counts=True)
print(f"valores distintos de L_bk entre 200 triangulaciones: {len(uniq)}")
print(f"semillas cuyo L_bk coincide con el OSF a 1e-7: {int(np.sum(np.abs(np.array(v) - OSF_BK) < 1e-7))} de 200;"
      f" primera semilla: {mejor}")

# La perturbación de 1e-6 mete ruido propio (~1e-6) en el valor interpolado. Para aislar el efecto de la
# TRIANGULACIÓN: se triangula con coordenadas perturbadas y se interpola con las coordenadas exactas sobre esos
# mismos triángulos (baricéntricas exactas). Así cada resultado distinto es una triangulación distinta, sin ruido.
def lbk_triangulacion_exacta(semilla, jit=1e-6):
    ok = ~np.isnan(enm)
    rng = np.random.default_rng(semilla)
    P = np.column_stack([yy[ok], xx[ok]])
    tri = Delaunay(P + rng.uniform(-jit, jit, P.shape))
    q = np.column_stack([yy[mask], xx[mask]])
    s = tri.find_simplex(q + 0.0)  # los puntos de consulta no se perturban
    out = []
    for qi, si in zip(q, s):
        vert = tri.simplices[si]
        A = np.column_stack([P[vert].T, ]).T  # 3x2
        T = np.array([[A[0, 0] - A[2, 0], A[1, 0] - A[2, 0]], [A[0, 1] - A[2, 1], A[1, 1] - A[2, 1]]])
        l12 = np.linalg.solve(T, qi - A[2])
        w = np.array([l12[0], l12[1], 1 - l12.sum()])
        out.append(float(w @ enm[ok][vert]))
    return sum(out)

v2 = np.array([lbk_triangulacion_exacta(s) for s in range(400)])
u2 = np.unique(np.round(v2, 12))
print(f"triangulaciones exactas: {len(u2)} valores distintos de L_bk en 400 semillas; rango {u2.min():.9f} a {u2.max():.9f}")
dist = np.abs(u2 - OSF_BK)
print(f"el mas cercano al OSF: {u2[np.argmin(dist)]:.9f} (diferencia {dist.min():.2e}; el CSV trae 9 decimales)")
print("todos los valores distintos:", " ".join(f"{x:.9f}" for x in u2[:60]), "..." if len(u2) > 60 else "")
