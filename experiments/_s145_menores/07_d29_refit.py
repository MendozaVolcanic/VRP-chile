"""S145 D29 - Control sintetico del refit iterativo a 3 sigma de la regresion
cuadratica de NTIbk.

POR QUE: D29 esta registrada como "menor" y "probablemente mejora el fondo", sin
ninguna medicion. Es la unica de las cuatro que se puede medir sin reprocesar
granules, porque el refit vive dentro de una funcion pura
(`compute_eti_scene_quadratic`) cuyo parametro `iterative_refit` se puede apagar
desde afuera sin tocar el pipeline (ningun caller lo pasa: siempre corre en True).

EL FENOMENO. El paper (p. 5, ec. 4) ajusta UNA parabola NTI contra NTIapp sobre
la escena y llama fondo a esa curva. Si la escena trae una colada de varios
pixeles calientes, esos puntos tiran la parabola HACIA ARRIBA, el fondo estimado
sube, y el exceso (ETI = NTI - NTIbk) de los propios pixeles calientes baja: la
anomalia se tapa a si misma. Nuestro refit saca los residuos de mas de 3 sigma y
vuelve a ajustar, asi que la parabola queda en el terreno frio y el exceso de la
anomalia sale mas grande. O sea: el refit nos hace DETECTAR MAS que el paper, no
menos. Este script mide cuanto.

METODO. Escena sintetica fisicamente construida: BT del TIR como un campo con
gradiente y ruido, radiancia MIR = Planck del mismo BT (pixel homogeneo) mas
ruido instrumental, y un cumulo de pixeles con una fraccion sub-pixel a 700 K.
NTI y NTIapp salen de la funcion real del pipeline. Se corre la regresion real
con refit y sin refit y se compara el ETI.

DECLARADO: es un control SINTETICO. No dice cuantos records reales cambia; dice
en que direccion y de que tamano es el efecto, y a partir de que fraccion de
escena caliente importa.

Salida: 07_d29_refit.json
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "07_d29_refit.json"
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(ROOT))

from pipeline.detection_context import (  # noqa: E402
    compute_eti_scene_quadratic, compute_nti_and_nti_app,
)
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
import pipeline.profile as prof  # noqa: E402

LAM_MIR, LAM_TIR = 3.959, 11.03      # MODIS B22 / B31
C1_SUMMIT = prof.DNTI_CONTEXTUAL_C1_SUMMIT
RNG = np.random.default_rng(20260920)
N = 180                               # escena 180x180


def planck(lam_um, T):
    return C1_PLANCK / (lam_um ** 5 * (np.exp(C2_PLANCK / (lam_um * T)) - 1.0))


def escena(n_hot, frac_subpixel, t_hot=700.0, ruido_mir_rel=0.004):
    """Construye (nti, nti_app, mask_valid, idx_hot) de una escena sintetica."""
    yy, xx = np.mgrid[0:N, 0:N]
    # Fondo: gradiente topografico suave de 8 K mas ruido de 0,8 K.
    bt_tir = 272.0 + 8.0 * (yy / N) + RNG.normal(0, 0.8, (N, N))
    rad_mir = planck(LAM_MIR, bt_tir)
    rad_mir *= 1.0 + RNG.normal(0, ruido_mir_rel, (N, N))
    # Cumulo caliente centrado: lado del cuadrado que contiene n_hot pixeles.
    lado = int(np.ceil(np.sqrt(max(n_hot, 1))))
    c = N // 2
    ys, xs = np.mgrid[c:c + lado, c:c + lado]
    ys, xs = ys.ravel()[:n_hot], xs.ravel()[:n_hot]
    if n_hot > 0:
        rad_mir[ys, xs] = (
            (1 - frac_subpixel) * planck(LAM_MIR, bt_tir[ys, xs])
            + frac_subpixel * planck(LAM_MIR, t_hot))
    nti, nti_app = compute_nti_and_nti_app(
        rad_mir=rad_mir, bt_tir=bt_tir,
        lambda_mir_um=LAM_MIR, lambda_tir_um=LAM_TIR)
    mask = np.isfinite(nti) & np.isfinite(nti_app)
    return nti, nti_app, mask, (ys, xs)


casos = []
for n_hot in (1, 9, 49, 196, 900, 3600):
    for frac in (2e-5, 1e-4):
        nti, nti_app, mask, (ys, xs) = escena(n_hot, frac)
        eti_con = compute_eti_scene_quadratic(nti, nti_app, mask,
                                              iterative_refit=True)
        eti_sin = compute_eti_scene_quadratic(nti, nti_app, mask,
                                              iterative_refit=False)
        eti_hot_con = float(np.median(eti_con[ys, xs]))
        eti_hot_sin = float(np.median(eti_sin[ys, xs]))
        frio = mask.copy()
        frio[ys, xs] = False
        casos.append({
            "n_pixeles_calientes": n_hot,
            "pct_escena_caliente": round(100.0 * n_hot / (N * N), 4),
            "fraccion_subpixel_a_700K": frac,
            "eti_mediano_del_cumulo_CON_refit": round(eti_hot_con, 6),
            "eti_mediano_del_cumulo_SIN_refit": round(eti_hot_sin, 6),
            "diferencia_abs": round(eti_hot_con - eti_hot_sin, 6),
            "diferencia_en_unidades_de_C1_summit": round(
                (eti_hot_con - eti_hot_sin) / C1_SUMMIT, 3),
            "cumulo_supera_C1_CON_refit": bool(eti_hot_con > C1_SUMMIT),
            "cumulo_supera_C1_SIN_refit": bool(eti_hot_sin > C1_SUMMIT),
            "eti_mediano_del_fondo_CON_refit": round(
                float(np.median(eti_con[frio])), 8),
            "eti_mediano_del_fondo_SIN_refit": round(
                float(np.median(eti_sin[frio])), 8),
            "pixeles_frios_sobre_C1_CON_refit": int(
                np.count_nonzero(eti_con[frio] > C1_SUMMIT)),
            "pixeles_frios_sobre_C1_SIN_refit": int(
                np.count_nonzero(eti_sin[frio] > C1_SUMMIT)),
        })


# --- Segundo bloque: residuos con cola pesada (banda de cirrus) --------------
# El primer bloque usa ruido gaussiano, y un refit a 3 sigma sobre residuos
# gaussianos casi no tiene a quien sacar. La objecion honesta es que las escenas
# reales traen grupos sistematicos fuera de la parabola: nube alta, sombra,
# cuerpo de agua. Aca se agrega una banda fria de cirrus que corre el NTI de un
# 18 % de la escena, que es el caso donde un ajuste unico si se puede torcer.
casos_cirrus = []
for pct_cirrus in (0.05, 0.18, 0.35):
    for n_hot in (9, 196):
        yy, xx = np.mgrid[0:N, 0:N]
        bt_tir = 272.0 + 8.0 * (yy / N) + RNG.normal(0, 0.8, (N, N))
        banda = xx < int(pct_cirrus * N)
        bt_tir[banda] -= 25.0                      # cirrus alto, TIR mucho mas frio
        rad_mir = planck(LAM_MIR, bt_tir)
        rad_mir *= 1.0 + RNG.normal(0, 0.004, (N, N))
        rad_mir[banda] *= 1.12                     # el cirrus sube el MIR aparte
        lado = int(np.ceil(np.sqrt(n_hot)))
        c = N // 2
        ys, xs = np.mgrid[c:c + lado, c:c + lado]
        ys, xs = ys.ravel()[:n_hot], xs.ravel()[:n_hot]
        rad_mir[ys, xs] = (0.99998 * planck(LAM_MIR, bt_tir[ys, xs])
                           + 2e-5 * planck(LAM_MIR, 700.0))
        nti, nti_app = compute_nti_and_nti_app(
            rad_mir=rad_mir, bt_tir=bt_tir,
            lambda_mir_um=LAM_MIR, lambda_tir_um=LAM_TIR)
        mask = np.isfinite(nti) & np.isfinite(nti_app)
        e_con = compute_eti_scene_quadratic(nti, nti_app, mask, iterative_refit=True)
        e_sin = compute_eti_scene_quadratic(nti, nti_app, mask, iterative_refit=False)
        hc, hs = float(np.median(e_con[ys, xs])), float(np.median(e_sin[ys, xs]))
        frio = mask.copy(); frio[ys, xs] = False
        casos_cirrus.append({
            "pct_escena_con_cirrus": pct_cirrus, "n_pixeles_calientes": n_hot,
            "eti_cumulo_CON_refit": round(hc, 6), "eti_cumulo_SIN_refit": round(hs, 6),
            "diferencia_en_unidades_de_C1_summit": round((hc - hs) / C1_SUMMIT, 3),
            "cumulo_supera_C1_CON_refit": bool(hc > C1_SUMMIT),
            "cumulo_supera_C1_SIN_refit": bool(hs > C1_SUMMIT),
            "pixeles_frios_sobre_C1_CON_refit": int(np.count_nonzero(e_con[frio] > C1_SUMMIT)),
            "pixeles_frios_sobre_C1_SIN_refit": int(np.count_nonzero(e_sin[frio] > C1_SUMMIT)),
        })

out = {
    "que_es": "control sintetico, no records reales",
    "escena": {"lado_px": N, "lambda_mir_um": LAM_MIR, "lambda_tir_um": LAM_TIR,
               "bt_tir_K": "272 a 280 con ruido 0,8 K",
               "ruido_mir_relativo": 0.004, "t_subpixel_K": 700.0,
               "semilla": 20260920},
    "C1_summit_de_referencia": C1_SUMMIT,
    "direccion_esperada": ("el refit saca los calientes del ajuste, baja el fondo "
                           "estimado y SUBE el ETI del cumulo: detectamos mas que "
                           "el ajuste unico del paper"),
    "casos": casos,
    "casos_cirrus": casos_cirrus,
}
OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("escrito", OUT)
print(f"{'n_hot':>6s} {'%escena':>8s} {'frac':>8s} {'ETI con':>10s} {'ETI sin':>10s}"
      f" {'dif/C1':>8s} {'>C1 con':>8s} {'>C1 sin':>8s} {'frios>C1 con/sin':>18s}")
for c in casos:
    print(f"{c['n_pixeles_calientes']:6d} {c['pct_escena_caliente']:8.3f}"
          f" {c['fraccion_subpixel_a_700K']:8.0e}"
          f" {c['eti_mediano_del_cumulo_CON_refit']:10.5f}"
          f" {c['eti_mediano_del_cumulo_SIN_refit']:10.5f}"
          f" {c['diferencia_en_unidades_de_C1_summit']:8.2f}"
          f" {str(c['cumulo_supera_C1_CON_refit']):>8s}"
          f" {str(c['cumulo_supera_C1_SIN_refit']):>8s}"
          f" {c['pixeles_frios_sobre_C1_CON_refit']:8d}/"
          f"{c['pixeles_frios_sobre_C1_SIN_refit']:<8d}")
print()
print("-- con banda de cirrus (cola pesada) --")
print(f"{'%cirrus':>8s} {'n_hot':>6s} {'ETI con':>10s} {'ETI sin':>10s} {'dif/C1':>8s}"
      f" {'>C1 con/sin':>12s} {'frios>C1 con/sin':>18s}")
for c in casos_cirrus:
    print(f"{c['pct_escena_con_cirrus']:8.2f} {c['n_pixeles_calientes']:6d}"
          f" {c['eti_cumulo_CON_refit']:10.5f} {c['eti_cumulo_SIN_refit']:10.5f}"
          f" {c['diferencia_en_unidades_de_C1_summit']:8.2f}"
          f"   {str(c['cumulo_supera_C1_CON_refit'])}/{str(c['cumulo_supera_C1_SIN_refit'])}"
          f"   {c['pixeles_frios_sobre_C1_CON_refit']}/{c['pixeles_frios_sobre_C1_SIN_refit']}")
