# -*- coding: utf-8 -*-
"""F6 M15: ¿por que camino del codigo entra cada uno de los 5 pixeles de Etna? (oraculo, matriz de ejemplo).
Sirve para clasificar que partes del codigo quedan contrastadas por el unico resultado publicado que se reproduce.
Pregunta 1: si un camino no aporta pixeles en Etna, el acuerdo con el OSF no dice nada de el."""
import sys, io
import numpy as np, scipy.io as sio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, sys.argv[1]); import mirova_v750 as mv
S = sio.loadmat(sys.argv[2])
g = mv.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
alert, diag = mv.hotspot_detection(S["ZI_M13"], S["ZI_M15"], S["BOX"], S["dayflag"].item(), g, devolver_diag=True)
print("sunglint", round(g, 2), " alertas", alert.tolist())
print("absolutas", diag["n_absolutas"], " pase1 [box0, roi1, roi2]", diag["n_pase1"], " pase2", diag["n_pase2"])
B = S["BOX"].ravel(order="F")
print("clase BOX de cada alerta:", [int(B[i]) for i in alert])
for p in ("pase1", "pase2"):
    d = diag[p]; print(p, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in d.items() if k != "coef"})
v = mv.vrp(S["ZI_M13"], alert); print("VRP MW", round(v[0], 4), "npix", v[1], "L_hot", round(v[4], 8), "L_bk", round(v[5], 8))
