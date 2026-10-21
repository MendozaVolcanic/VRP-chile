# -*- coding: utf-8 -*-
"""F6 M10: Max_Dist maximo y cola por sensor (OSF v2.5, todo el archivo). Si el corte a 30 km es del dominio de
VIIRS 750 (BOX), no tiene por que repetirse en 375 m y en MODIS; si se repite, es un paso comun posterior.
Denominador: todas las filas por Resolution."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
f = pd.read_csv(sys.argv[1], usecols=["Resolution", "Max_Dist", "Npix"])
for res, g in f.groupby("Resolution"):
    md = g.Max_Dist
    print(f"res {res}: n={len(g)} max {md.max():.2f} m; >25 km {int((md>25000).sum())}; >28 km {int((md>28000).sum())}; "
          f"[29,30] km {int(((md>=29000)&(md<=30000)).sum())}; >30 km {int((md>30000).sum())}; =30000 exacto {int((md==30000).sum())}")
