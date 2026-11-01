# -*- coding: utf-8 -*-
"""V1 (S158) F6-1, parte "nunca en VIIRS 375 ni MODIS": identidad con el k PROPIO de cada sensor, por cenit.
k375 = 18,0 * 140625 (VIIRS 375, CLAUDE.md, validado S14); k1000 = 18,9e6 (MODIS). Control: si el k fuera el
equivocado, ninguna fila cumpliria (lo que paso con k750 en v1/f6_1_cenit.py)."""
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
df = pd.read_csv(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
for res, k in [(375, 18.0 * 140625), (1000, 18.9e6)]:
    x = df[df.Resolution == res].copy()
    x["r"] = x.VRP / (k * (x.Tot_Lmir_hot - x.Tot_Lmir_bk))
    x["fuera"] = (x.r - 1).abs() >= 1e-3
    for nm, s in [("cenit<=50", x.SatZen <= 50), ("cenit>50", x.SatZen > 50)]:
        print(res, nm, "n", int(s.sum()), "fuera(|r-1|>=1e-3)", int(x[s].fuera.sum()), "mediana r", round(x[s].r.median(), 5))
