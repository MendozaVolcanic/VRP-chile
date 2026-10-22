# -*- coding: utf-8 -*-
"""F6 M12: ¿la cadena NRT de HOY (latest.php, 2026) sigue en la grilla de 750 m centrada en la cumbre?
Distancia_km de las alertas VIIRS (750) del scraper contra 0,75*sqrt(i^2+j^2) redondeado a 0,01 km.
Pregunta 1: si la grilla fuera otra (celda distinta o no centrada) la fraccion cuantizada caeria al azar.
Control: celda de 0,70 km y de 0,375 km (esta ultima contiene a la de 0,75, se espera tambien alta: no discrimina
media celda, se informa). Azar: la fraccion de valores 0,01..max que caen en la grilla por casualidad.
Denominador: alertas ALERTA_TERMICA de Sensor == VIIRS con Distancia_km > 0 (consolidado al 2026-10-14)."""
import sys, io, math
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
s = pd.read_csv(sys.argv[1])
a = s[(s.Sensor == "VIIRS") & (s.Tipo_Registro == "ALERTA_TERMICA") & (s.Distancia_km > 0)]
print("n =", len(a), " ventana", a.Fecha_Satelite_UTC.min(), "a", a.Fecha_Satelite_UTC.max())
def grilla(cell, maxd=40.0):
    v = set()
    for i in range(0, 60):
        for j in range(0, 60):
            d = cell * math.hypot(i, j)
            if d <= maxd: v.add(round(d, 2))
    return v
for cell in (0.75, 0.70, 0.375):
    g = grilla(cell)
    ok = a.Distancia_km.round(2).isin(g)
    azar = np.mean([round(x, 2) in g for x in np.arange(0.01, a.Distancia_km.max() + 0.005, 0.01)])
    print(f"celda {cell}: cuantizadas {int(ok.sum())} de {len(a)} ({100*ok.mean():.1f} %)   azar {100*azar:.1f} %")
g = grilla(0.75)
print("no cuantizadas a 0,75:", a[~a.Distancia_km.round(2).isin(g)][["Fecha_Satelite_UTC","Volcan","VRP_MW","Distancia_km"]].to_string())
