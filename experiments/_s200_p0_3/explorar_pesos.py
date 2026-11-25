"""Exploración: cuántos píxeles del recorte llegan a alguna celda, y con qué peso máximo."""
import numpy as np
import comun as C
C.utf8()
for esc in C.escenas():
    E = C.Escena(esc)
    M, fuera = E.matrices()[0]
    wmax = np.asarray(abs(M).max(axis=0).todense()).ravel()
    fin = np.isfinite(E.d["m13"]) & np.isfinite(E.d["m15"])
    print(f"{esc['clave']:40s} pix {wmax.size} finitos {fin.sum()} wmax=0 {np.mean(wmax[fin]==0):.2f} "
          f"wmax>=0.5 {np.mean(wmax[fin]>=0.5):.2f} mediana wmax {np.median(wmax[fin]):.2f}")
