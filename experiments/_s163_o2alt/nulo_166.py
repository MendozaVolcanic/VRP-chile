"""S163 O2 alternativa, parte 2b: nulo MEDIDO del calce 166 de 166 (regla A110).

¿Con qué frecuencia una regla de desempate cualquiera calzaría con MATLAB en las 166 escenas con alerta de O2? Se
toman 20 triangulaciones al azar (Qhull sobre centros perturbados 1e-6, interpolación con coordenadas exactas sobre
esos triángulos, método de S158 firma_fillmissing2.py l. 95-112) y se cuenta en cuántas escenas el VRP coincide con el
de MATLAB a 1e-9 relativo. Si el máximo del nulo queda muy por debajo de 166, el calce de la regla perturbada no es
suerte. Fuera de la envolvente convexa: vecino más cercano (igual que delaunay_perturbado.rellenar).
"""
import hashlib, json
from pathlib import Path
import numpy as np, scipy.io as sio
from scipy.ndimage import binary_dilation
from scipy.spatial import Delaunay
from scipy.interpolate import griddata

O2 = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete")
assert hashlib.md5((O2 / "resultado_o2.mat").read_bytes()).hexdigest() == "1f7fdc4bed0f8cb6223204bbce42ba43"
R = sio.loadmat(O2 / "resultado_o2.mat"); E = sio.loadmat(O2 / "entradas_o2.mat")
casos = []
for k in range(R["VRP"].shape[0]):
    a = np.asarray(R["ALERTAS"][k, 0]).ravel().astype(int)
    if a.size == 0: continue
    m13 = E["M13"][:, :, k].astype(float)
    mask = np.zeros(m13.shape, bool); mask[np.unravel_index(a - 1, m13.shape, order="F")] = True
    enm = m13.copy(); enm[mask] = np.nan
    kk = 3 if a.size <= 4 else (5 if a.size <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((kk, kk), bool))] = np.nan
    casos.append((k, a.size, enm, mask, float(np.nansum(m13[mask])), float(R["VRP"][k, 0])))

def vrp_azar(enm, mask, lhot, semilla):
    ok = ~np.isnan(enm); yy, xx = np.indices(enm.shape)
    P = np.column_stack([yy[ok], xx[ok]]).astype(float); v = enm[ok]
    q = np.column_stack([yy[mask], xx[mask]]).astype(float)
    tri = Delaunay(P + np.random.default_rng(semilla).uniform(-1e-6, 1e-6, P.shape))
    tot = 0.0
    for qi, si in zip(q, tri.find_simplex(q)):
        if si < 0:
            tot += float(griddata(P, v, qi[None, :], method="nearest")[0]); continue
        s = tri.simplices[si]; A = P[s]
        T = np.array([[A[0, 0] - A[2, 0], A[1, 0] - A[2, 0]], [A[0, 1] - A[2, 1], A[1, 1] - A[2, 1]]])
        l = np.linalg.solve(T, qi - A[2]); tot += float(np.array([l[0], l[1], 1 - l.sum()]) @ v[s])
    return (lhot - tot) * 1.97e7 * 0.5625 / 1e6

n1 = sum(c[1] == 1 for c in casos)
print(f"escenas con alerta: {len(casos)} (1 px: {n1})")
res = []
for sem in range(20):
    ok = [abs(vrp_azar(enm, mask, lh, sem) / vm - 1) < 1e-9 for (_, np_, enm, mask, lh, vm) in casos]
    ok1 = [o for o, c in zip(ok, casos) if c[1] == 1]
    res.append((sum(ok), sum(ok1)))
    print(f"  semilla {sem:2d}: calza con MATLAB en {sum(ok):3d} de {len(casos)} | en 1 px {sum(ok1):2d} de {n1}")
t = np.array(res)
print(f"NULO 20 triangulaciones al azar: calces totales mediana {np.median(t[:,0]):.0f}, max {t[:,0].max()} de {len(casos)};"
      f" en 1 px mediana {np.median(t[:,1]):.0f}, max {t[:,1].max()} de {n1}. Regla perturbada fila-col: 166 de 166 (pert_contra_matlab_salida.txt)")
