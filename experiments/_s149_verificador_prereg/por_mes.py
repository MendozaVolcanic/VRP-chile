# -*- coding: utf-8 -*-
"""Verificador S149: alertas nocturnas por mes (pasada unica), Lascar MODIS y Villarrica/Chillan.
Reusa el cargador de recuento_independiente.py (su salida se repite arriba; lo nuevo va al final)."""
import collections, runpy
from pathlib import Path
g = runpy.run_path(str(Path(__file__).with_name("recuento_independiente.py")))
print()
print("==================== POR MES (n de alertas nocturnas, n con 0,5 MW o mas)")
P = g["pasadas"]
c = collections.Counter(); g5 = collections.Counter()
for (vol, b, m), p in P.items():
    if p["alerta"] and p["noche"]:
        c[(vol, b, m[:7])] += 1
        if max(p["vrp"] or [0]) >= 0.5:
            g5[(vol, b, m[:7])] += 1
for vol, b in (("Lascar", "MODIS"), ("Villarrica", "VIIRS375"), ("Nevados de Chillan", "VIIRS375"), ("Villarrica", "VIIRS750")):
    print(vol, b, {m: (c[(vol, b, m)], g5[(vol, b, m)]) for m in ["2026-%02d" % i for i in range(1, 10)]})
