# -*- coding: utf-8 -*-
"""Tarea 1.20 (1): ventana fisica en que el techo de M15 (343 K, corte 342,5 K) borra un pixel
que M13 todavia mide (M13 < 634 - 0,5 K). Modelo de dos componentes por pixel (lava a T_h con
fraccion p, fondo a T_bg), radiancia monocromatica en el centro de banda (M13 4,050 um, M15 10,763
um, constantes de pipeline/process_viirs_mod.py). VRP con el metodo MIR: k=1,97e7 m^2*... * A_pix,
igual que el pipeline (WOOSTER_COEFF 19.7 * 562500 m^2 -> 11.081.250). Solo lectura, sin red.
"""
import sys, io, json
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 14388.0  # W um^4 m^-2 sr^-1, um K (mismas que el pipeline)
L13, L15 = 4.050, 10.763
def L(T, lam): return C1 / (lam**5 * (np.exp(C2 / (lam * T)) - 1.0))
def BT(Lv, lam): return C2 / (lam * np.log(C1 / (Lv * lam**5) + 1.0))
K = 19.7 * 562500.0  # = 11.081.250, CLAUDE.md "Reglas cientificas"
CORTE15, CORTE13, LUTMAX15 = 342.5, 633.5, 374.6
out = {}
p = np.logspace(-5, 0, 200001)
for Tbg in (250.0, 270.0, 290.0):
    for Th in (500.0, 600.0, 800.0, 1000.0, 1150.0):
        l15 = p * L(Th, L15) + (1 - p) * L(Tbg, L15)
        l13 = p * L(Th, L13) + (1 - p) * L(Tbg, L13)
        b15, b13 = BT(l15, L15), BT(l13, L13)
        vrp = K * (l13 - L(Tbg, L13)) / 1e6  # MW
        i15 = np.argmax(b15 >= CORTE15) if (b15 >= CORTE15).any() else None
        i13 = np.argmax(b13 >= CORTE13) if (b13 >= CORTE13).any() else None
        ilut = np.argmax(b15 >= LUTMAX15) if (b15 >= LUTMAX15).any() else None
        r = {"p_M15_corte": None if i15 is None else float(p[i15]),
             "BT_M13_en_corte_M15": None if i15 is None else round(float(b13[i15]), 1),
             "VRP_MW_en_corte_M15": None if i15 is None else round(float(vrp[i15]), 1),
             "p_M13_corte": None if i13 is None else float(p[i13]),
             "VRP_MW_en_corte_M13": None if i13 is None else round(float(vrp[i13]), 1),
             "p_M15_lutmax": None if ilut is None else float(p[ilut]),
             "VRP_MW_en_lutmax_M15": None if ilut is None else round(float(vrp[ilut]), 1)}
        if i15 is not None:
            r["ventana_M15_borra_M13_mide"] = bool((i13 is None) or (i15 < i13))
        out[f"Tbg{int(Tbg)}_Th{int(Th)}"] = r
        print(f"Tbg={Tbg:.0f} Th={Th:.0f}: {r}")
json.dump(out, open(__file__.replace('.py', '.json'), 'w'), indent=1)
