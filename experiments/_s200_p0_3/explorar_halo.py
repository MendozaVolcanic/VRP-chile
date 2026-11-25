"""Exploración: perfil radial del exceso de M13 alrededor del pico en las escenas con alerta, y tiempo del detector."""
import time

import numpy as np

import comun as C

C.utf8()
for esc in C.escenas():
    E = C.Escena(esc)
    mask, d = E.detectar(E.m13g, E.m15g)
    if not mask.any():
        continue
    f, k = np.nonzero(mask)
    i = np.argmax(E.m13g[mask])
    pf, pk = f[i], k[i]
    r, q = np.indices(E.m13g.shape)
    dist = np.hypot(r - pf, q - pk) * 0.75
    bt = C.MV.radiancia_a_temperatura(E.m13g, C.MV.LAMBDA_M13)
    ref = np.nanmedian(bt[(dist > 8) & (dist < 12)])
    prof = []
    for a, b in [(0, 0.5), (0.5, 1.2), (1.2, 2), (2, 3), (3, 4), (4, 5), (5, 7), (7, 10)]:
        s = (dist >= a) & (dist < b)
        prof.append(f"{a}-{b}km:{np.nanmedian(bt[s]) - ref:+.2f}K")
    print(f"{esc['clave']:40s} pico ({pf},{pk}) BT ref anillo 8-12 km {ref:.1f} K | " + " ".join(prof))

E = C.Escena(C.escenas()[0])
t0 = time.time()
for _ in range(50):
    E.detectar(E.m13g, E.m15g)
print(f"detector: {(time.time() - t0) / 50 * 1000:.1f} ms por llamada")
t0 = time.time()
for i in range(5):
    E.pesos_pixel(1000 + i)
print(f"pesos de un píxel (2 bandas): {(time.time() - t0) / 5 * 1000:.1f} ms")
