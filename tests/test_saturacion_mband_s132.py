# -*- coding: utf-8 -*-
"""S132 — Techo de saturación de las bandas M de VIIRS (decisión #2 de AUDIT_S131 §4).

POR QUÉ. Un píxel saturado no es un píxel caliente: es un píxel del que el sensor ya no
sabe nada. Si el techo declarado está por encima del techo real del detector, los píxeles
que el sensor entregó clampeados entran al cálculo como si fueran medición buena e inflan
la magnitud (es el mecanismo del record PP 2026-03-18 de 695.431 MW, F28).

El techo de M15 estaba puesto en 423,0 K "análogo a I05" — una analogía, no una medición.
Campus et al. 2022 (Sensors 22:1713), Tabla 1, mide sobre órbita:

    TMAX (SNR-NEdT on orbit)   M13: 634 K (0,04)      MODIS B21: 500 K (0,183)
    TMAX (SNR-NEdT on orbit)   M15: 343 K (0,03)      MODIS B31: 400 K (0,017)

Es la misma fuente y la misma tabla de la que ya sale el 634,0 de M13, así que tomar de
ahí el 343,0 de M15 no mezcla autoridades (A35: jerarquía UserGuide > paper canon MIROVA).
Campus es canon MIROVA (Torino/Firenze, A9). El VIIRS L1B UserGuide da 374,6 K como techo
de la LUT de M15, que es el techo del contenedor, no el del detector: por eso 343,0 es el
número operacional y 374,6 no lo contradice.
"""
import numpy as np
import pytest

from pipeline.process_viirs_mod import BT_LUT_MAX_MBAND, aplicar_techo_saturacion_mband


def test_techo_m15_es_el_medido_por_campus_2022():
    """M15 satura a 343 K medidos, no a los 423 K heredados por analogía con I05."""
    assert BT_LUT_MAX_MBAND["M15"] == 343.0


def test_techo_m13_no_cambia():
    """Control: el techo de M13 ya venía de la misma tabla y no se toca."""
    assert BT_LUT_MAX_MBAND["M13"] == 634.0


@pytest.mark.parametrize("bt_in, esperado_nan", [
    (300.0, False),   # escena nocturna normal
    (342.0, False),   # justo debajo del techo
    (343.0, True),    # en el techo: el detector ya no mide
    (350.0, True),    # clampeado por el sensor
    (420.0, True),    # habría pasado con el techo viejo de 423,0
])
def test_m15_por_encima_del_techo_se_descarta(bt_in, esperado_nan):
    bt = aplicar_techo_saturacion_mband(np.array([bt_in], dtype=np.float32), "M15")
    assert np.isnan(bt[0]) == esperado_nan


def test_banda_sin_techo_declarado_pasa_intacta():
    bt = aplicar_techo_saturacion_mband(np.array([9999.0], dtype=np.float32), "M99")
    assert bt[0] == 9999.0
