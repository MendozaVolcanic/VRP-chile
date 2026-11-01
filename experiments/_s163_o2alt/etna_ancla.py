"""S163 O2 alternativa, parte 1: el ancla de Etna. ¿Qué variante del fondo reproduce el único número de MATLAB que
conocemos a 9 decimales (OSF v2.5, Etna NOAA-20 2023-05-19 00:54, Tot_Lmir_bk 1,072886152)?

POR QUÉ. El VRP del `.m` depende de cómo `fillmissing2` rompe los empates de la triangulación (INFORME S159, H1/H2).
Etna es 5 píxeles con hueco de 5 × 5, no un píxel, pero la regla de desempate que acierte ahí es la misma que decide
el hueco de 3 × 3 de una alerta de un píxel.

Pregunta 1 (¿mide lo que dice?): se recalcula Tot_Lmir_hot (debe dar 1,965342180, no depende del fondo) y cada
candidato perturbado se comprueba sin aristas ilegales. Pregunta 2 (¿puede dar distinto de cero?): las ocho simetrías
del marco dan valores distintos entre sí, y el nulo mide con qué frecuencia una triangulación al azar (perturbación
aleatoria de 1e-6 de los centros, 2000 semillas, interpolada con coordenadas exactas) cae en el valor del OSF: esa es la probabilidad de acertar por suerte.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo"))
import delaunay_perturbado as DP  # noqa: E402
import mirova_v750_r2 as R2  # noqa: E402

spec = importlib.util.spec_from_file_location("o1p", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)

OSF_LBK, OSF_LHOT, OSF_VRP_W = 1.072886152, 1.965342180, 9889528.362
TOL = 1e-9  # el CSV del OSF trae 9 decimales

S = sio.loadmat(EXP / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat")
m13 = S["ZI_M13"].astype(float)
alert = np.array([2180, 2181, 2247, 2314, 2248]) - 1  # salida del .m en Octave (INFORME S159 §2.1)
mask = np.zeros(m13.shape, bool); mask[np.unravel_index(alert, m13.shape, order="F")] = True
lhot = m13[mask].sum()
print(f"Tot_Lmir_hot {lhot:.9f} (OSF {OSF_LHOT:.9f}) {'OK' if abs(lhot-OSF_LHOT)<TOL else 'DISTINTO'}")
enm = m13.copy(); enm[mask] = np.nan
enm[binary_dilation(np.isnan(enm), structure=np.ones((5, 5), bool))] = np.nan


def fila(nombre, lbk):
    vrp = (lhot - lbk) * 1.97e7 * 0.5625
    print(f"{nombre:34s} L_bk {lbk:.9f}  dif {lbk-OSF_LBK:+.3e}  VRP {vrp:12.1f} W  {'== OSF' if abs(lbk-OSF_LBK)<TOL else ''}")


print(f"OSF v2.5                           L_bk {OSF_LBK:.9f}  VRP {OSF_VRP_W:12.1f} W")
sh = sio.loadmat(AQUI / "salida_octave_s163.mat")
fila("shim Octave (S159)", float(sh["LBK"].ravel()[0]))
fila("segundo port (R2, fila-col)", R2.vrp(m13, mask)["L_bk"])
fila("primer port (O1, col-fila)", O1.vrp(m13, alert)[5])
fila("R2 jitter semilla 126 (S158)", R2.vrp(m13, mask, jitter=1e-6, semilla=126)["L_bk"])
print("perturbacion simbolica (regla CGAL), 8 simetrias del marco:")
aciertos = 0
for ejes in ("xy_fila_col", "xy_col_fila"):
    for sx in (1, -1):
        for sy in (1, -1):
            B, info = DP.rellenar(enm, ejes, sx, sy)
            lbk = B[mask].sum()
            aciertos += abs(lbk - OSF_LBK) < TOL
            fila(f"  {ejes} sx={sx:+d} sy={sy:+d} (ileg {info['ilegales']})", lbk)
print(f"simetrias que aciertan al OSF: {aciertos} de 8")

# Nulo: triangulaciones al azar, interpoladas con coordenadas EXACTAS sobre los triángulos de la perturbada (método de
# S158 firma_fillmissing2.py l. 95-112): cada valor distinto es una triangulación distinta, sin ruido del jitter.
from scipy.spatial import Delaunay  # noqa: E402
ok = ~np.isnan(enm); yy, xx = np.indices(enm.shape)
P = np.column_stack([yy[ok], xx[ok]]).astype(float); vals_ok = enm[ok]
q = np.column_stack([yy[mask], xx[mask]]).astype(float)


def lbk_exacta(semilla, jit=1e-6):
    rng = np.random.default_rng(semilla)
    tri = Delaunay(P + rng.uniform(-jit, jit, P.shape))
    tot = 0.0
    for qi, si in zip(q, tri.find_simplex(q)):
        v = tri.simplices[si]; A = P[v]
        T = np.array([[A[0, 0] - A[2, 0], A[1, 0] - A[2, 0]], [A[0, 1] - A[2, 1], A[1, 1] - A[2, 1]]])
        l12 = np.linalg.solve(T, qi - A[2]); w = np.array([l12[0], l12[1], 1 - l12.sum()])
        tot += float(w @ vals_ok[v])
    return tot


N = 2000
vals = np.array([lbk_exacta(s) for s in range(N)])
hit = np.abs(vals - OSF_LBK) < TOL
u, c = np.unique(np.round(vals, 9), return_counts=True)
print(f"NULO triangulaciones al azar (jitter 1e-6, interpolacion exacta), {N} semillas: {u.size} valores distintos;"
      f" rango {vals.min():.9f} a {vals.max():.9f}")
print(f"  semillas que caen en el OSF (|dif|<{TOL:g}): {int(hit.sum())} de {N} -> p_azar por candidato = {hit.mean():.4f}")
print(f"  frecuencia del valor mas comun: {c.max()} de {N} ({u[c.argmax()]:.9f})")
p1 = hit.mean()
print(f"  prob. de que al menos 1 de 2 candidatos a priori (fila-col, col-fila) acierte por azar: {1-(1-p1)**2:.4f}")
print(f"  prob. de que al menos 1 de 8 simetrias acierte por azar: {1-(1-p1)**8:.4f}")
# la regla perturbada cae en una triangulación del espacio que muestrea el nulo? (si no, el nulo no la representa)
B, _ = DP.rellenar(enm, "xy_fila_col", 1, 1)
print(f"  el valor de la regla fila-col aparece en el nulo: {int((np.abs(vals - B[mask].sum()) < TOL).sum())} veces")
