# -*- coding: utf-8 -*-
"""S158: el oráculo (port a Python del código de MIROVA para VIIRS 750) reproduce el resultado operacional de MIROVA.

POR QUÉ: la matriz de ejemplo que MIROVA publicó con su código es la pasada de Etna del 2023-05-19 00:54 (NOAA-20):
el archivo OSF v2.5 la trae con el mismo cenit (7,753455827) y azimut (-77,46321927), y con el resultado que dio el
sistema en producción: 5 píxeles, suma de L_hot 1,96534218, suma de L_bk 1,072886152, VRP 9.889.528,362 W. Que el port
reproduzca eso prueba que el port es fiel en la detección de cumbre, el fondo y la fórmula del VRP. No prueba los umbrales
(en Etna ningún píxel entra por K1 ni por la región de fuera) ni el VRP sobre 50° de cenit, donde MIROVA publica otra
cosa en el 24 % de las filas de VIIRS 750 del OSF (experiments/_s158_audit/f6/INFORME.md, hallazgos 1 y 2).
Las dos preguntas del instrumento: (1) si el port estuviera roto en la detección, los índices o la suma de L_hot no
coincidirían a 8 decimales; (2) el control de mutación (segundo pase apagado) muestra que la prueba puede fallar.
Lo que este caso NO cubre (mutaciones que no cambian Etna): experiments/_s158_oraculo_mirova/mutar_oraculo_salida.txt.
"""
import os
import sys

import numpy as np
import pytest
import scipy.io as sio

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "experiments", "_s158_oraculo_mirova"))
import mirova_v750 as m  # noqa: E402

EJEMPLO = os.path.join(RAIZ, "experiments", "_s158_d17_diseno", "osf_codigo_mirova", "Example", "VIIRS750_example.mat")
MIROVA_ETNA = {"npix": 5, "l_hot": 1.96534218, "l_bk": 1.072886152, "vrp_w": 9889528.362}


@pytest.fixture(scope="module")
def ejemplo():
    S = sio.loadmat(EJEMPLO)
    sg = m.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
    return S, sg


def _correr(S, sg):
    a = m.hotspot_detection(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg)
    return a, m.vrp(S["ZI_M13"], a)


def test_el_ejemplo_es_la_pasada_de_etna_del_osf(ejemplo):
    S, _ = ejemplo
    assert str(S["acquisition_id"][0]).startswith("20231390054-VJ1")
    assert S["sat_zen"].item() == pytest.approx(7.753455827, abs=1e-8)
    assert S["sat_azi"].item() == pytest.approx(-77.46321927, abs=1e-7)


def test_detecta_los_mismos_cinco_pixeles_que_mirova(ejemplo):
    a, (v, npix, dl, bk, l_hot, l_bk) = _correr(*ejemplo)
    assert npix == MIROVA_ETNA["npix"]
    assert sorted(a.tolist()) == [2179, 2180, 2246, 2247, 2313]
    assert l_hot == pytest.approx(MIROVA_ETNA["l_hot"], abs=1e-8)


def test_el_vrp_queda_a_menos_de_0_2_por_ciento_de_mirova(ejemplo):
    """El fondo pasa por el supuesto sobre fillmissing2 (orden de ejes de MATLAB): 0,07 % en L_bk, 0,09 % en VRP."""
    _, (v, npix, dl, bk, l_hot, l_bk) = _correr(*ejemplo)
    assert l_bk == pytest.approx(MIROVA_ETNA["l_bk"], rel=2e-3)
    assert v * 1e6 == pytest.approx(MIROVA_ETNA["vrp_w"], rel=2e-3)


def test_la_prueba_puede_fallar_sin_segundo_pase(ejemplo, monkeypatch):
    """Control positivo: en Etna el segundo pase agrega 1 de los 5 píxeles; sin él la prueba de arriba fallaría."""
    original = m._contextual_pass
    llamadas = []

    def sin_segundo(*args, **kw):
        llamadas.append(1)
        if len(llamadas) == 2:
            return (np.array([], dtype=int),) * 3
        return original(*args, **kw)

    monkeypatch.setattr(m, "_contextual_pass", sin_segundo)
    a, (v, npix, *_r) = _correr(*ejemplo)
    assert npix == 4
    assert abs(v * 1e6 / MIROVA_ETNA["vrp_w"] - 1) > 0.05


def test_coeficiente_y_planck_del_operacional():
    assert m.MIR_COEFFICIENT * m.PIXEL_AREA_KM2 == pytest.approx(11081250.0)
    L = np.array([0.05, 0.3, 2.0])
    assert m.temperature_to_radiance(m.radiance_to_temperature(L, 4.05), 4.05) == pytest.approx(L, rel=1e-9)


def test_rechaza_por_sunglint_y_por_escena_incompleta(ejemplo):
    S, sg = ejemplo
    assert m.hotspot_detection(S["ZI_M13"], S["ZI_M15"], S["BOX"], 0, 11.9).size == 0
    m13 = S["ZI_M13"].astype(float).copy()
    m13[: m13.shape[0] // 2 + 1, :] = np.nan
    assert m.hotspot_detection(m13, S["ZI_M15"], S["BOX"], 0, sg).size == 0
