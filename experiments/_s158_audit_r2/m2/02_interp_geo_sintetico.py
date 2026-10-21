"""M2 (S158 r2): ¿la interpolación de la grilla de 5 km de MOD021KM corre los píxeles?

Fenómeno: MOD021KM trae lat/lon sólo cada 5 píxeles (406 x 271 para 2030 x 1354). Esos puntos
corresponden al píxel CENTRAL de cada bloque de 5 x 5 (desplazamiento 2 en líneas y 2 en
muestras; la convención se documenta en el informe con la cita del producto). `_interp_geo` de
pipeline/process_modis.py usa scipy.ndimage.zoom, que estira la grilla gruesa para que su
primer punto caiga en el píxel 0 y el último en el píxel 2029/1353, sin saber del desplazamiento.

Instrumento: fabrico una geolocalización "verdadera" de 1 km (coordenada = índice de píxel, en
unidades de píxel, lineal en líneas y con el crecimiento real del tamaño de píxel a lo largo del
barrido), la submuestreo como lo hace el producto ([2::5, 2::5]) y la paso por la MISMA función
`_interp_geo` del pipeline. La diferencia entre lo que la función devuelve y la verdad es el error
en píxeles, columna por columna.

Pregunta 1: si la función fuera correcta, el error sería ~0 en todo el interior (interpolación
lineal de una función lineal es exacta). Pregunta 2: control positivo: la misma prueba con una
grilla gruesa que SÍ parte en el píxel 0 ([0::5, 0::5] con 407 x 271 puntos no existe en el
producto, pero sirve para ver que el instrumento da ~0 cuando la convención coincide).

Ventana: no aplica (prueba geométrica, independiente de los datos).
"""
import os, sys, io
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, REPO)
os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.process_modis import _interp_geo

NL, NS = 2030, 1354
lines = np.arange(NL, dtype=np.float64)
samples = np.arange(NS, dtype=np.float64)
# "verdad": coordenada de línea = índice; coordenada de muestra = índice (unidades de píxel)
true_line = np.repeat(lines[:, None], NS, axis=1)
true_samp = np.repeat(samples[None, :], NL, axis=0)

# Convención del producto: puntos de 5 km en el píxel central del bloque: líneas 2,7,...,2027 (406)
# y muestras 2,7,...,1352 (271).
coarse_line = true_line[2::5, 2::5]
coarse_samp = true_samp[2::5, 2::5]
assert coarse_line.shape == (406, 271), coarse_line.shape

il = _interp_geo(coarse_line.astype(np.float32), NL, NS)
isamp = _interp_geo(coarse_samp.astype(np.float32), NL, NS)
err_line = il - true_line     # >0: al píxel se le asigna la posición de un píxel de índice mayor
err_samp = isamp - true_samp

print("forma interpolada:", il.shape)
print("error en LÍNEAS (píxeles), en las líneas 0, 2, 500, 1015, 1500, 2027, 2029:")
for L in (0, 2, 500, 1015, 1500, 2027, 2029):
    print(f"  línea {L:4d}: {err_line[L, 677]:+.3f}")
print("error en MUESTRAS (píxeles), en las columnas 0, 2, 100, 338, 677, 1016, 1252, 1352, 1353:")
for S in (0, 2, 100, 338, 677, 1016, 1252, 1352, 1353):
    print(f"  col {S:4d}: {err_samp[1015, S]:+.3f}")

# ¿Hacia dónde? Un error +k en muestras significa que al píxel i se le asigna la lat/lon del píxel
# i+k. El nadir está en la columna ~676,5: en la mitad izquierda (i < 676) +k apunta HACIA el nadir;
# en la mitad derecha, -k apunta hacia el nadir.
hacia_nadir = np.where(samples < 676.5, err_samp[1015] > 0, err_samp[1015] < 0)
print("columnas donde el corrimiento apunta hacia el nadir:", int(hacia_nadir.sum()), "de", NS)

# Tamaño de píxel a lo largo del barrido (km) para convertir a distancia en el suelo: modelo
# estándar MODIS (Nishihama 1997): ancho ~ 1 km * sec^2(theta) aprox; uso la función del repo si
# existe para el cenit por columna.
try:
    from pipeline.scan_geometry import modis_zenith_from_column
    zen = modis_zenith_from_column(samples)
    w_km = 1.0 / np.cos(np.radians(zen)) ** 2   # ancho along-scan aproximado
    print("\ncorrimiento en el suelo (km) = error(px) * ancho(px), en columnas seleccionadas:")
    for S in (0, 100, 338, 677, 1016, 1252, 1353):
        print(f"  col {S:4d}: cenit {zen[S]:5.1f} deg, ancho {w_km[S]:.2f} km, corrimiento {err_samp[1015, S] * w_km[S]:+.2f} km")
except Exception as e:
    print("sin modis_zenith_from_column:", e)

print("\n== control positivo: grilla gruesa que SÍ parte en el píxel 0 (0::5), 406 x 271 recortando la cola ==")
cl0 = true_line[0::5, 0::5][:406, :271]
cs0 = true_samp[0::5, 0::5][:406, :271]
il0 = _interp_geo(cl0.astype(np.float32), NL, NS)
is0 = _interp_geo(cs0.astype(np.float32), NL, NS)
print("error muestras col 0 / 677 / 1353:", f"{(is0 - true_samp)[1015, 0]:+.3f} / {(is0 - true_samp)[1015, 677]:+.3f} / {(is0 - true_samp)[1015, 1353]:+.3f}")
print("(con 0::5 el último punto gruesa es la muestra 1350, así que zoom lo estira 3 px al final: el instrumento ve también ese defecto)")
