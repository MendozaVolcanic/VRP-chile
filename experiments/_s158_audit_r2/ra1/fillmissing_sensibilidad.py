# -*- coding: utf-8 -*-
"""RA1: sensibilidad del fondo del .m a la triangulacion (fillmissing2 'linear' de MATLAB vs griddata).
En una grilla regular la triangulacion de Delaunay es ambigua (dos diagonales por celda); se prueba la orientacion
transpuesta y una interpolacion bilineal por fila/columna para acotar cuanto del 0,7 % contra el OSF es metodo."""
import os, sys
import numpy as np, scipy.io as sio
from scipy import ndimage
from scipy.interpolate import griddata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from port_mirova_v750 import detectar, sunglint_deg
S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
M13 = S["ZI_M13"].astype(float)
sg = sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sun_azi"].item(), S["sat_azi"].item())
alert, _ = detectar(S["ZI_M13"], S["ZI_M15"], S["BOX"], 0, sg)
masked = M13.copy()
for r, c in alert: masked[r, c] = np.nan
excl = ndimage.binary_dilation(np.isnan(masked), structure=np.ones((5, 5), bool))
masked[excl] = np.nan
n = M13.shape[0]
rr, cc = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
ok = ~np.isnan(masked)
OSF_BK = 1.072886152
def suma(bk): return float(sum(bk[r, c] for r, c in alert))
bk1 = masked.copy(); bk1[~ok] = griddata((rr[ok], cc[ok]), masked[ok], (rr[~ok], cc[~ok]), method="linear")
bk2 = masked.copy(); bk2[~ok] = griddata((cc[ok], rr[ok]), masked[ok], (cc[~ok], rr[~ok]), method="linear")
bk3 = masked.copy(); bk3[~ok] = griddata((rr[ok], cc[ok]), masked[ok], (rr[~ok], cc[~ok]), method="cubic")
bk4 = masked.copy(); bk4[~ok] = griddata((rr[ok], cc[ok]), masked[ok], (rr[~ok], cc[~ok]), method="nearest")
# bilineal separable: interpola a lo largo de filas y de columnas y promedia
def interp_1d(A, axis):
    B = A.copy()
    for i in range(B.shape[0]):
        line = B[i] if axis == 1 else B[:, i]
        x = np.arange(line.size); m = ~np.isnan(line)
        if m.sum() >= 2:
            line[~m] = np.interp(x[~m], x[m], line[m])
    return B
bk5 = 0.5 * (interp_1d(masked, 1) + interp_1d(masked, 0))
for nombre, bk in (("griddata lineal (fila,col)", bk1), ("griddata lineal transpuesto", bk2), ("griddata cubico", bk3), ("vecino mas cercano", bk4), ("bilineal separable fila/col", bk5)):
    s = suma(bk); print("%-32s suma bk=%.6f  dif vs OSF=%+.6f (%+.2f %%)  VRP=%.4f MW" % (nombre, s, s - OSF_BK, 100 * (s - OSF_BK) / OSF_BK, (1.96534218 - s) * 1.97e7 * 0.5625 / 1e6))
print("pixeles excluidos por la dilatacion 5x5 alrededor de los 5 alertados y de los 99 NaN previos: %d" % int(excl.sum()))
