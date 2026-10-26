# -*- coding: utf-8 -*-
"""Tarea 1.20: relacion entre el tope de la LUT (Reported Range, UserGuide L1B VIIRS Aug 2021 p. 42,
Tabla C.3) y la Tmax de especificacion (ATBD Radiometrico VIIRS Rev C, p. 6, Tabla 2). El ATBD (p. 81)
dice que la saturacion del detector esta por diseno en ~1,2 veces la senal de Tmax y que la LUT llega a
1,5 veces (HDEBBT). Radiancia monocromatica en el centro de banda: aproximacion, no la LUT real.
"""
import sys, io
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C1, C2 = 1.191042e8, 14388.0
L = lambda T, lam: C1 / (lam**5 * (np.exp(C2 / (lam * T)) - 1))
BT = lambda Lv, lam: C2 / (lam * np.log(C1 / (Lv * lam**5) + 1))
for banda, lam, tmax, l_tope in (("M15", 10.763, 343.0, 25.5562), ("I4", 3.740, 353.0, 4.65933)):
    print(f"{banda}: BT(tope LUT {l_tope}) = {BT(l_tope, lam):.1f} K | BT(1,5 x L(Tmax)) = {BT(1.5*L(tmax, lam), lam):.1f} K"
          f" | BT(1,2 x L(Tmax)) = {BT(1.2*L(tmax, lam), lam):.1f} K | tope/L(Tmax) = {l_tope/L(tmax, lam):.2f}")
