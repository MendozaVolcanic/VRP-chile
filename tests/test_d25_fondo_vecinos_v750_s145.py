# -*- coding: utf-8 -*-
"""S145: el fondo por vecinos (D25) en VIIRS 750 (M-band).

POR QUE. El helper de vrp_regimes ya es agnostico de sensor; lo que este archivo fija es que en
M-band se use M13_LAMBDA (4,05 um) y no I04, que el respaldo del pixel sin vecinos sea el fondo de
hoy, y que el flag propio de V750 no se confunda con el de I-band (A92).

Plan: docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md
"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# M13_LAMBDA NO vive en pipeline.constants: esta definido en el propio process_viirs_mod,
# igual que I04_LAMBDA vive en process_viirs. Importarlo de constants da ImportError.
from pipeline.process_viirs_mod import M13_LAMBDA, vrp_bg_neighbor_mean_v750  # noqa: E402
from pipeline.vrp_regimes import neighbor_mean_radiance_background  # noqa: E402


def test_el_envoltorio_de_m_band_usa_la_longitud_de_onda_de_m13():
    """Si usara I04 (3,74 um) el fondo saldria distinto: Planck no es plano entre 3,74 y 4,05 um."""
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 400.0
    alerta = np.zeros((5, 5), dtype=bool)
    alerta[2, 2] = True
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [2], [2], 9.99, max_half_px=1)
    esperado, _ = neighbor_mean_radiance_background(
        bt, alerta, [2], [2], M13_LAMBDA, max_half_px=1)
    assert n_sin == 0
    np.testing.assert_allclose(l_bg, esperado)


def test_sin_vecinos_no_alertados_cae_al_fondo_de_hoy_y_lo_cuenta():
    """Un unico pixel de una escena 1x1: no hay a quien promediar, manda el respaldo."""
    bt = np.full((1, 1), 300.0)
    alerta = np.ones((1, 1), dtype=bool)
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [0], [0], 0.1234, max_half_px=3)
    assert n_sin == 1
    np.testing.assert_allclose(l_bg, [0.1234])
