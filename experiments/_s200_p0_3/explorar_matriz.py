"""Exploración: la matriz rápida reproduce la grilla de producción y el impulso de remuestrear_grilla."""
import time

import numpy as np

import comun as C

C.utf8()
E = C.Escena(C.escenas()[4])
t0 = time.time()
W = E.matrices()
print(f"matrices: {time.time() - t0:.1f} s")
for (M, fuera), b, ref in zip(W, ("m13", "m15"), (E.m13g, E.m15g)):
    v = np.nan_to_num(E.d[b], nan=0.0)
    g = (M @ v).reshape(ref.shape)
    g[fuera.reshape(ref.shape)] = np.nan
    print(b, "max |W v - grilla prod| =", np.nanmax(np.abs(g - ref)), "nan iguales:",
          bool((np.isnan(g) == np.isnan(ref)).all()))
for i in (500, 4000, 7000):
    w_r = E.pesos_pixel(i)
    w_l = E.pesos_pixel_lento(i)
    print(i, [float(np.max(np.abs(a - b))) for a, b in zip(w_r, w_l)], [float(a.sum()) for a in w_r])
