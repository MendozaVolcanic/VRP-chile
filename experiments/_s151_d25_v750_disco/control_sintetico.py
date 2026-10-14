# -*- coding: utf-8 -*-
"""S151 (loop 1.5): control sintético de las dos variantes del fondo, ANTES de gastar runner.

POR QUÉ. El probe de CI llama a la función del pipeline (`vrp_bg_neighbor_mean_v750`) con la máscara
de alertados que arma `variantes.py`. Si esa cadena tuviera un error (la variante (b) no sacara a los
vecinos nublados, o el respaldo no cayera al fondo de hoy), el probe mediría otra cosa en silencio
(A110: un control se valida midiendo su nulo). Aquí cada caso tiene una respuesta conocida de antemano.

CASOS (respuesta esperada fijada antes de correr):
  K1 nulo: escena uniforme a 265 K, un píxel alertado a 266 K. El fondo por vecinos tiene que ser
     Planck(265 K) con error relativo < 1e-12, igual al fondo de hoy cuando el anillo también está a 265 K.
  K2 el cráter frío: píxel alertado a 262 K, vecinos a 260 K, anillo regional a 264 K. Con el fondo de hoy
     el exceso se recorta a 0; con el fondo por vecinos debe dar > 0, y ese valor debe coincidir con
     k * A * (L(262) - L(260)) / 1e6.
  K3 nube: la mitad de los 8 vecinos a 240 K de M13 y 240 K de M15 (nube fría), la otra mitad a 260 K
     en las dos bandas. (a) promedia las 8 (fondo más frío, exceso MAYOR); (b) promedia sólo las 4
     tibias y debe igualar el fondo de K2.
  K4 todo nublado: los 8 vecinos (y la corona 5x5 y 7x7) bajo 255 K en M15. (b) no tiene vecinos útiles
     y debe caer al respaldo (el fondo de hoy), con n_sin_vecinos = 1.
  K5 formas distintas entre M13 y M15: la variante (b) tiene que fallar con ValueError, no seguir.
Sale 2 si cualquier caso falla. Salida: control_sintetico_salida.txt (vía tee).
"""
import io
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pipeline.process_viirs_mod import (M13_LAMBDA, NADIR_PIXEL_AREA_M2, WOOSTER_COEFF,  # noqa: E402
                                        bt_to_spectral_radiance, vrp_bg_neighbor_mean_v750)
from pipeline.profile import VRP_BG_NEIGHBOR_MAX_HALF_PX  # noqa: E402
import variantes  # noqa: E402

L = lambda t: float(bt_to_spectral_radiance(np.float64(t), M13_LAMBDA))  # noqa: E731
MW = lambda dl: NADIR_PIXEL_AREA_M2 * WOOSTER_COEFF * max(dl, 0.0) / 1e6  # noqa: E731
fallas = []


def chequear(nombre, ok, detalle):
    print(f"{'OK ' if ok else 'FALLA'} {nombre}: {detalle}")
    if not ok:
        fallas.append(nombre)


def escena(t_fondo, t_hot, n=15):
    g = np.full((n, n), float(t_fondo))
    a = np.zeros((n, n), bool)
    c = n // 2
    g[c, c] = t_hot
    a[c, c] = True
    return g, a, c


def fondo(g, a, c, legado, tir=None):
    mask = a if tir is None else variantes.alertados_mas_nube(a, tir)
    lb, nsin = vrp_bg_neighbor_mean_v750(g, mask, np.array([c]), np.array([c]), legado,
                                         max_half_px=VRP_BG_NEIGHBOR_MAX_HALF_PX)
    return float(lb[0]), nsin


print(f"max_half_px del perfil = {VRP_BG_NEIGHBOR_MAX_HALF_PX}")
# K1
g, a, c = escena(265.0, 266.0)
lb, _ = fondo(g, a, c, L(265.0))
chequear("K1 nulo", abs(lb / L(265.0) - 1) < 1e-12, f"L_bk={lb:.10g} contra Planck(265)={L(265.0):.10g}")
# K2
g, a, c = escena(260.0, 262.0)
legado = L(264.0)
lb, _ = fondo(g, a, c, legado)
hoy, nuevo, esperado = MW(L(262.0) - legado), MW(L(262.0) - lb), MW(L(262.0) - L(260.0))
chequear("K2 cráter frío", hoy == 0.0 and nuevo > 0 and abs(nuevo - esperado) < 1e-12,
         f"hoy {hoy} MW, por vecinos {nuevo:.6f} MW, esperado {esperado:.6f} MW")
# K3
g, a, c = escena(260.0, 262.0)
tir = np.full_like(g, 260.0)
for i, (dr, dc) in enumerate([(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]):
    if i % 2 == 0:
        g[c + dr, c + dc] = 240.0
        tir[c + dr, c + dc] = 240.0
lb_a, _ = fondo(g, a, c, legado)
lb_b, _ = fondo(g, a, c, legado, tir)
chequear("K3 nube", lb_a < lb_b and abs(lb_b / L(260.0) - 1) < 1e-12,
         f"(a) {MW(L(262.0) - lb_a):.6f} MW, (b) {MW(L(262.0) - lb_b):.6f} MW (debe igualar K2 {esperado:.6f})")
cnt = variantes.contar_vecinos_nublados(a, tir, [c], [c])
chequear("K3 conteo", cnt == [{"no_alertados": 8, "nublados": 4}], f"{cnt}")
# K4
g, a, c = escena(260.0, 262.0)
tir = np.full_like(g, 250.0)
lb_b, nsin = fondo(g, a, c, legado, tir)
chequear("K4 todo nublado", lb_b == legado and nsin == 1, f"fondo {lb_b:.6g} (respaldo {legado:.6g}), n_sin_vecinos {nsin}")
# K5
try:
    variantes.alertados_mas_nube(a, np.zeros((3, 3)))
    chequear("K5 formas distintas", False, "no levantó ValueError")
except ValueError as e:
    chequear("K5 formas distintas", True, f"ValueError: {e}")

print(f"escala: 1 K de exceso a 262 K en un píxel de 750 m = {MW(L(262.5) - L(261.5)):.4f} MW")
if fallas:
    print("FALLAN:", fallas)
    sys.exit(2)
print("todos los casos pasan")
