# -*- coding: utf-8 -*-
"""V177 v09: cuantos pixeles de hueco une la dilatacion de lib177.seleccionar (structure 3x3, 1 iteracion)? El docstring dice 1 px."""
import numpy as np
from scipy import ndimage as ni

s8 = np.ones((3, 3), bool)
for hueco in (1, 2, 3):
    a = np.zeros((5, 12), bool)
    a[2, 2] = True
    a[2, 3 + hueco] = True
    lab, n = ni.label(ni.binary_dilation(a, structure=s8, iterations=1), structure=s8)
    print(f"hueco de {hueco} px entre dos pixeles: componentes tras dilatar = {n}")
