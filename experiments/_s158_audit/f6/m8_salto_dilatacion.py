# -*- coding: utf-8 -*-
"""F6 M8: ¿la firma de la dilatacion del fondo (cuadrado de 3, 5 o 7 segun npix <= 4, <= 30, > 30) se ve en el OSF?
Fenomeno: al pasar de npix 4 a 5 (y de 30 a 31) el hueco crece y el fondo se interpola desde mas lejos del foco, donde
el halo caliente pesa menos: el fondo por pixel deberia BAJAR en escalon, no en rampa.
Instrumento: y = log(Lbk/Npix) menos la mediana del volcan (quita el nivel de fondo propio). Se compara el salto entre
n y n+1 en los cortes del codigo (4->5, 30->31) contra saltos placebo (2->3, 7->8, 12->13, 20->21, 40->41).
Pregunta 1: si la regla de dilatacion fuera otra, el salto en 4->5 y 30->31 no se distinguiria de los placebo.
Pregunta 2: con muy pocas filas por Npix el error estandar sube; se imprime n y el error de cada salto.
Denominador: filas V750 con SatZen <= 50 (las que cumplen la identidad), OSF v2.5 2012-2025, sin filtrar clase."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1])
d = d[(d.SatZen <= 50) & (d.Tot_Lmir_bk > 0)].copy()
d["y"] = np.log(d.Tot_Lmir_bk / d.Npix)
d["y"] -= d.groupby("Volc_Name").y.transform("median")
# tambien la fraccion de fondo: Lbk/Lhot (sube si el fondo pesa mas)
def salto(n):
    a, b = d[d.Npix == n].y, d[d.Npix == n + 1].y
    dif = b.mean() - a.mean()
    se = np.sqrt(a.var() / len(a) + b.var() / len(b))
    return len(a), len(b), dif, se
print("n -> n+1 :  na  nb  salto_log  se  z")
for n in [2, 3, 4, 5, 7, 12, 20, 28, 29, 30, 31, 40]:
    na, nb, dif, se = salto(n)
    tag = "  <- corte del codigo" if n in (4, 30) else ""
    print(f"{n:3d}->{n+1:3d}: {na:6d} {nb:6d} {dif:+.4f} {se:.4f} {dif/se:+.1f}{tag}")
