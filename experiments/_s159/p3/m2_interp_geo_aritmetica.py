# M2. Error de posición que introduce pipeline/process_modis.py::_interp_geo (scipy.ndimage.zoom,
# order=1, alineación de esquinas) frente al mapa de dimensiones del diccionario L1B C7
# (p. 66, Fig. 2.1.1: DimensionMap offset 2, increment 5 a lo largo del barrido; 271 = 1354/5+1).
# Aritmética pura: se interpola el ÍNDICE de 1 km que corresponde a cada nodo de 5 km.
# Pregunta 1: si _interp_geo estuviera roto, ¿se vería? Sí: el error en píxeles sale distinto de 0.
# Pregunta 2: si el instrumento estuviera muerto: control positivo con una interpolación CORRECTA
#   (np.interp sobre los índices verdaderos 2+5c) que debe dar error 0 en el interior.
# La traducción a km usa una Tierra esférica (Re 6378 km, H 705 km) y el ángulo de barrido de MODIS
# (±55°, 1354 muestras); es un ORDEN DE MAGNITUD, no la geometría real (sin elipsoide ni relieve).
# El eje a lo largo de la traza NO se mide: el extracto renderizado sólo muestra un mapa de dimensión.
import sys, io, numpy as np
from scipy.ndimage import zoom
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
N = 1354; NC = 271
true_idx_of_node = 2 + 5 * np.arange(NC, dtype=float)          # índice 1 km de cada nodo (dicc. C7)
got = zoom(true_idx_of_node, N / NC, order=1)                   # lo que hace _interp_geo
err_px = got - np.arange(N)                                     # >0: el píxel recibe la posición de uno de índice mayor
ok = np.interp(np.arange(N), true_idx_of_node, true_idx_of_node) - np.arange(N)  # control positivo
print("control (interp correcta) error máx interior:", np.abs(ok[2:1353]).max())
Re, H = 6378.0, 705.0
theta = np.deg2rad((np.arange(N) - (N - 1) / 2) * (110.0 / (N - 1)))   # ±55°
beta = np.arcsin((Re + H) / Re * np.sin(theta)) - theta                 # ángulo de Tierra
ground = Re * beta                                                      # km desde el nadir
zen = np.rad2deg(np.arcsin((Re + H) / Re * np.sin(np.abs(theta))))
dg = np.gradient(ground)                                                # km por muestra
err_km = err_px * dg
print("j    zenit  err_px  km/px  err_km  (signo: + = hacia índice mayor)")
for j in [0, 50, 136, 250, 406, 550, 677, 800, 947, 1100, 1216, 1300, 1353]:
    toward = "hacia el nadir" if (err_px[j] > 0) == (j < 677) else "hacia el borde"
    print(f"{j:5d} {zen[j]:5.1f} {err_px[j]:+6.2f} {dg[j]:5.2f} {err_km[j]:+6.2f}  {toward}")
for lo, hi in [(0, 25), (25, 40), (40, 55), (55, 66)]:
    for side, m in (("índices bajos", np.arange(N) < 677), ("índices altos", np.arange(N) >= 677)):
        s = m & (zen >= lo) & (zen < hi)
        if s.any():
            print(f"cenit {lo}-{hi}°, {side}: |err| km mediana {np.median(np.abs(err_km[s])):.2f}  máx {np.abs(err_km[s]).max():.2f}")

# --- A lo largo de la traza (dicc. C7 p. 100: line_numbers "3, 8" en base 1 => líneas 2 y 7 de cada
# barrido de 10). Gránulo de 203 barridos = 2030 líneas, 406 filas de 5 km. Sólo índice (sin km):
# el tamaño del píxel a lo largo de la traza depende del ángulo de barrido de la columna (1 a ~2 km).
NL, NR = 2030, 406
node_line = np.array([10 * (r // 2) + (2 if r % 2 == 0 else 7) for r in range(NR)], float)
got_l = zoom(node_line, NL / NR, order=1)
err_l = got_l - np.arange(NL)
print("\nA lo largo de la traza (líneas): error en la línea 0 %+.2f, en la 1015 %+.2f, en la 2029 %+.2f" %
      (err_l[0], err_l[1015], err_l[2029]))
print("fracción de líneas con |error| > 1 línea: %.1f %%" % (100 * np.mean(np.abs(err_l) > 1)))
