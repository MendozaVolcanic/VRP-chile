# -*- coding: utf-8 -*-
"""F6 M16: ¿el cambio en el VRP publicado es un escalon en cenit = 50 o una rampa? Filas V750 con k*dL > 100 MW
(donde la regla actua casi siempre sobre 50), en bandas de 0,5 grados alrededor de 50.
Control: misma tabla en 375 m y 1000 m con su propio k (debe dar 0 fuera en todas las bandas, M1).
Denominador: filas V750 del OSF v2.5 con k*dL > 100 MW y cenit entre 47 y 53 (2012-2025)."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
full = pd.read_csv(sys.argv[1], usecols=["Resolution","SatZen","Tot_Lmir_hot","Tot_Lmir_bk","VRP"])
for res, k in [(750, 1.97e7*0.5625), (375, 2531250.0), (1000, 18.9e6)]:
    d = full[full.Resolution == res].copy()
    d["kdl"] = k * (d.Tot_Lmir_hot - d.Tot_Lmir_bk)
    d["fuera"] = (d.VRP / d.kdl - 1).abs() >= 1e-4
    z = d[(d.kdl > 1e8) & (d.SatZen > 47) & (d.SatZen < 53)].copy()
    z["b"] = pd.cut(z.SatZen, np.arange(47, 53.01, 0.5))
    t = z.groupby("b", observed=True).fuera.agg(["sum", "count"])
    print(f"\nres {res}:"); print(t.T.to_string())
