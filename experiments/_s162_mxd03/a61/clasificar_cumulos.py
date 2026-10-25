# -*- coding: utf-8 -*-
"""Clasificacion final de las 48 protegidas (A61): ¿el cumulo de X son los MISMOS pixeles que el de K?
Criterios, en orden:
  1. MISMO PIXEL POR INDICE: cumulo de 1 pixel en K y en X, y en las dos grillas el centroide coincide (< 50 m) con el
     pixel mas caliente por indice (`pico`, mismo indice (linea, frame) en todos los brazos por construccion).
  2. MISMOS PIXELES POR RESIDUO: mismo numero de pixeles y residuo (K->X menos el corrimiento del granulo en el pixel
     del crater) < 0,3 km.
  3. RESELECCION PARCIAL: lo demas, con el detalle.
Y para todas: distancia de X al crater y al objeto VIIRS de la noche, para descartar que se fue a otro objeto.
P1: si X hubiera cambiado de pixel en muchas, el criterio 1 y 2 fallarian y la lista 3 creceria (control positivo:
Lascar 2026-03-05 07:55 cae en 3 por construccion, ver detalle_casos_salida.txt). P2: con X = K todas darian residuo
igual al corrimiento del granulo (1 a 2,5 km), ninguna pasaria el criterio 2."""
import csv
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
tab = list(csv.DictReader(open(Path(__file__).parent / "a61_protegidas.csv", encoding="utf-8")))
c1, c2, c3 = [], [], []
for f in tab:
    if f["K_npx"] == "1" and f["X_npx"] == "1" and f["pico_es_pcK"] == "True" and f["pico_es_pcX"] == "True":
        c1.append(f)
    elif f["K_npx"] == f["X_npx"] and float(f["residuo_km"]) < 0.3:
        c2.append(f)
    else:
        c3.append(f)
print("n = %d | 1 mismo pixel por indice: %d | 2 mismos pixeles por residuo: %d | 3 reseleccion parcial: %d" % (len(tab), len(c1), len(c2), len(c3)))
print("en 1 y 2 juntos: %d de %d; X a <= 0,70 km del crater en %d de %d; X a <= 0,70 km del objeto VIIRS de la noche en %d de %d con referencia" % (
    len(c1) + len(c2), len(tab), sum(1 for f in tab if float(f["X_dist"]) <= 0.70), len(tab),
    sum(1 for f in tab if f["X_a_viirs"] and float(f["X_a_viirs"]) <= 0.70), sum(1 for f in tab if f["X_a_viirs"])))
print("X mas lejos del crater: %s" % (max((float(f["X_dist"]), f["vol"], f["dt"]) for f in tab),))
print("en el grupo 1, el residuo medido (que deberia ser ~0 salvo bow tie): mediana %.3f, max %.3f (%s)" % (
    sorted(float(f["residuo_km"]) for f in c1)[len(c1) // 2], max(float(f["residuo_km"]) for f in c1),
    max(c1, key=lambda f: float(f["residuo_km"]))["dt"]))
print("grupo 3, caso por caso:")
for f in c3:
    print("   %s %s z=%s | K dist %s npx %s vrp %s | X dist %s npx %s vrp %s | residuo %s | X/K vrp %.2f | VIIRS: X a %s km, K a %s km" % (
        f["vol"], f["dt"], f["z"], f["K_dist"], f["K_npx"], f["K_vrp"], f["X_dist"], f["X_npx"], f["X_vrp"], f["residuo_km"],
        float(f["X_vrp"]) / float(f["K_vrp"]), f["X_a_viirs"], f["K_a_viirs"]))
print("cambio de magnitud |X/K - 1| > 10 %% en las 48: %d; > 20 %%: %d; mediana X/K %.3f" % (
    sum(1 for f in tab if abs(float(f["X_vrp"]) / float(f["K_vrp"]) - 1) > 0.10), sum(1 for f in tab if abs(float(f["X_vrp"]) / float(f["K_vrp"]) - 1) > 0.20),
    sorted(float(f["X_vrp"]) / float(f["K_vrp"]) for f in tab)[len(tab) // 2]))
