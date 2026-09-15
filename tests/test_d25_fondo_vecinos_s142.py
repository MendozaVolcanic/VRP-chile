# -*- coding: utf-8 -*-
"""S142 D25: fondo del VRP = media de la radiancia de los vecinos NO alertados de cada píxel alertado.

EL FENÓMENO. El VRP resta a la radiancia del píxel caliente la del terreno que tendría sin el
foco. Hoy ese terreno es la mediana de un anillo de 5 a 25 km: en un cono nevado de noche es valle
tibio, más caliente que la cumbre, y el cráter con lava sub-píxel sale con exceso negativo,
recortado a 0,0 MW. MIROVA (Coppola 2016a ec. 6; Fernandina 2025 p. 9; Campus 2024 p. 3) usa los
píxeles que rodean a cada alertado y que no están alertados.

QUÉ FIJAN. (1) La media es de RADIANCIA, no Planck de la media de temperaturas (Planck es convexo en
el MIR y la diferencia crece con la heterogeneidad del entorno). (2) Los alertados vecinos quedan
fuera. (3) El píxel interior de un cúmulo busca afuera, hasta `max_half_px`. (4) NaN se ignora. (5)
El envoltorio de process_viirs usa el fondo de hoy sólo donde no hay vecinos, y lo cuenta.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from pipeline.vrp_regimes import neighbor_mean_radiance_background  # noqa: E402

LAMBDA_I04 = 3.740


def _planck(bt):
    import pipeline.process_viirs as pv
    return pv.bt_to_spectral_radiance(np.asarray(bt, dtype=np.float64), pv.I04_LAMBDA)


def test_un_alertado_al_centro_es_la_media_de_radiancia_de_sus_8_vecinos():
    bt = np.full((5, 5), 260.0)
    bt[1:4, 1:4] = np.array([[250.0, 290.0, 250.0], [290.0, 330.0, 290.0], [250.0, 290.0, 250.0]])
    alert = np.zeros((5, 5), dtype=bool)
    alert[2, 2] = True
    l_bk, half = neighbor_mean_radiance_background(bt, alert, [2], [2], LAMBDA_I04, max_half_px=1)
    vecinos = [250.0, 290.0, 250.0, 290.0, 290.0, 250.0, 290.0, 250.0]
    esperado = float(np.mean(_planck(vecinos)))
    assert math.isclose(l_bk[0], esperado, rel_tol=1e-12)
    assert half[0] == 1
    # y NO es Planck de la media de temperaturas (270 K): Jensen en el MIR
    planck_media_bt = float(_planck(np.mean(vecinos)))
    assert not math.isclose(l_bk[0], planck_media_bt, rel_tol=1e-3)


def test_los_vecinos_alertados_quedan_fuera():
    bt = np.full((5, 5), 260.0)
    bt[2, 2] = 330.0
    bt[2, 3] = 320.0
    alert = np.zeros((5, 5), dtype=bool)
    alert[2, 2] = alert[2, 3] = True
    l_bk, half = neighbor_mean_radiance_background(bt, alert, [2, 2], [2, 3], LAMBDA_I04, max_half_px=1)
    assert math.isclose(l_bk[0], float(_planck(260.0)), rel_tol=1e-12)
    assert math.isclose(l_bk[1], float(_planck(260.0)), rel_tol=1e-12)
    assert list(half) == [1, 1]


def test_el_interior_de_un_cumulo_busca_afuera_hasta_max_half():
    bt = np.full((9, 9), 255.0)
    bt[3:6, 3:6] = 300.0
    bt[4, 4] = 320.0
    alert = np.zeros((9, 9), dtype=bool)
    alert[3:6, 3:6] = True
    l1, h1 = neighbor_mean_radiance_background(bt, alert, [4], [4], LAMBDA_I04, max_half_px=1)
    assert math.isnan(l1[0]) and h1[0] == 0
    l3, h3 = neighbor_mean_radiance_background(bt, alert, [4], [4], LAMBDA_I04, max_half_px=3)
    assert h3[0] == 2
    assert math.isclose(l3[0], float(_planck(255.0)), rel_tol=1e-12)


def test_nan_se_ignora_y_sin_vecinos_validos_da_nan():
    bt = np.full((3, 3), np.nan)
    bt[1, 1] = 300.0
    bt[0, 0] = 260.0
    alert = np.zeros((3, 3), dtype=bool)
    alert[1, 1] = True
    l_bk, half = neighbor_mean_radiance_background(bt, alert, [1], [1], LAMBDA_I04, max_half_px=1)
    assert math.isclose(l_bk[0], float(_planck(260.0)), rel_tol=1e-12) and half[0] == 1
    bt[0, 0] = np.nan
    l_bk, half = neighbor_mean_radiance_background(bt, alert, [1], [1], LAMBDA_I04, max_half_px=3)
    assert math.isnan(l_bk[0]) and half[0] == 0


def test_borde_de_la_escena_no_envuelve():
    bt = np.full((4, 4), 250.0)
    bt[0, 3] = 290.0   # esquina opuesta en columna: no puede ser vecina de (0, 0)
    bt[0, 0] = 330.0
    alert = np.zeros((4, 4), dtype=bool)
    alert[0, 0] = True
    l_bk, _ = neighbor_mean_radiance_background(bt, alert, [0], [0], LAMBDA_I04, max_half_px=1)
    assert math.isclose(l_bk[0], float(_planck(250.0)), rel_tol=1e-12)


def test_entradas_invalidas_fallan():
    bt = np.full((3, 3), 260.0)
    with pytest.raises(ValueError):
        neighbor_mean_radiance_background(bt, np.zeros((3, 3), bool), [1], [1], LAMBDA_I04, max_half_px=0)
    with pytest.raises(ValueError):
        neighbor_mean_radiance_background(bt, np.zeros((2, 2), bool), [1], [1], LAMBDA_I04)
    with pytest.raises(ValueError):
        neighbor_mean_radiance_background(bt, np.zeros((3, 3), bool), [1, 2], [1], LAMBDA_I04)


def test_sin_alertados_devuelve_arreglos_vacios():
    l_bk, half = neighbor_mean_radiance_background(np.full((3, 3), 260.0), np.zeros((3, 3), bool),
                                                   [], [], LAMBDA_I04)
    assert l_bk.shape == (0,) and half.shape == (0,)
