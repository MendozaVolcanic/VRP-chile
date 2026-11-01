# -*- coding: utf-8 -*-
"""H511 (S139) bajo K: con la banda 22 primaria, process_modis.py convierte la BT de la banda 22
(retrieved a 3,959 um) de vuelta a radiancia con BAND21_LAMBDA = 3,929 um para el VRP. Tamano del
sesgo en el exceso de radiancia dL = L(T_hot) - L(T_bg), para temperaturas tipicas de la noche.
Constantes de Planck: las mismas C1/C2 del pipeline (se importan; no se copian).
P1: si el sesgo fuera nulo, el cociente daria 1,000. P2: control: con lambda igual en ambos lados el
cociente tiene que dar exactamente 1."""
import sys, io, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np
import pipeline.process_modis as pm
def L(lam, T):
    return pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * T)) - 1))
l21, l22 = pm.BAND21_LAMBDA, pm.BAND22_LAMBDA
print("lambda21", l21, "lambda22", l22)
print("control (lambda22 en ambos):", (L(l22, 300) - L(l22, 265)) / (L(l22, 300) - L(l22, 265)))
for tbg in (250.0, 265.0, 275.0):
    for th in (280.0, 300.0, 330.0):
        r = (L(l21, th) - L(l21, tbg)) / (L(l22, th) - L(l22, tbg))
        print(f"T_bg {tbg} T_hot {th}: dL(l21)/dL(l22) = {r:.4f}")
