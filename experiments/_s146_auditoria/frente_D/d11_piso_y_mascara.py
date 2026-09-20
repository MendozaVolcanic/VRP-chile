# -*- coding: utf-8 -*-
"""d11: MISSION.md:142 (tabla de parches): '582 records invisibles -> 0' (piso VRP, S130) y 'la mascara de 260 K ciega ~23 % de las
pasadas' de VIIRS 375. (a) replica r_piso_invisibles del libro de cuentas; (b) fraccion de pasadas V375 con n_cloud_masked>0 y con
t_bg ausente/ciega por mes: si #535 apago la mascara, n_cloud_masked debe caer a 0 desde 2026-08-29 (control del regimen).
Instrumento: (1) si el campo n_cloud_masked no se persistiera daria None en todo: se imprime cuantos lo traen. (2) idem."""
import io, sys, json
from collections import defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); n = 0
for v in VOLS:
    for r in D[v]:
        if r.get("diag_vrp_raw_mw") is None: continue
        if not ((r.get("vrp_mw") or 0) > 0) and r.get("triggered_test1") is not True: n += 1
print("piso_invisibles hoy:", n)
