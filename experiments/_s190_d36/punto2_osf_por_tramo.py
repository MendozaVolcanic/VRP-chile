# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): script de medición sobre el OSF v2.5, sólo lectura.
"""D36 punto 2, poder de la prueba: ¿con qué frecuencia actúa el escalón de cenit en el OSF v2.5, por tramo del VRP
del código (k * ΔL), sobre 50°? Si en 20 a 100 MW actúa poco, los 12 pares nuestros de ese tramo no pueden decir si
MIROVA lo sigue aplicando en el NRT. Definición de fila afectada y k: las de experiments/_s158_audit/f6/m16_escalon_50.py
(|VRP / kΔL - 1| >= 1e-4; k = 1,97e7 * 0,5625). Unidades del CSV: W.
Uso: python experiments/_s190_d36/punto2_osf_por_tramo.py <VRP_GLOBAL_ARCHIVE_2025.csv>
"""
import sys

import numpy as np
import pandas as pd

d = pd.read_csv(sys.argv[1], usecols=["Resolution", "SatZen", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP"])
d = d[d.Resolution == 750].copy()
d["kdl"] = 1.97e7 * 0.5625 * (d.Tot_Lmir_hot - d.Tot_Lmir_bk)
d["fuera"] = (d.VRP / d.kdl - 1).abs() >= 1e-4
z = d[d.SatZen > 50]
for a, b in [(0, 20), (20, 100), (100, 500), (500, np.inf)]:
    t = z[(z.kdl > a * 1e6) & (z.kdl <= b * 1e6)]
    r = (t.VRP / t.kdl)[t.fuera]
    print(f"cenit > 50, kdL {a}-{b} MW: afectadas {int(t.fuera.sum())} de {len(t)}"
          f" ({100 * t.fuera.mean():.1f} %), mediana de VRP/kdL en las afectadas {r.median():.3f}")
