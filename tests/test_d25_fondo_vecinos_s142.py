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
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from arnes_sintetico_s142 import (CENTRO_V375, correr_en_subproceso,  # noqa: E402
                                  escena_v375)
from pipeline.vrp_regimes import neighbor_mean_radiance_background  # noqa: E402

LAMBDA_I04 = 3.740
GOLDEN = json.loads((ROOT / "tests" / "golden_s142" / "apagado.json").read_text(encoding="utf-8"))


def _src(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


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


# ---------------------------------------------------------------------------
# Envoltorio, de punta a punta y guards de fuente (Tarea 6).
# ---------------------------------------------------------------------------


def test_envoltorio_usa_el_fondo_de_hoy_solo_sin_vecinos_y_lo_cuenta():
    import pipeline.process_viirs as pv
    bt = np.full((9, 9), 255.0)
    bt[3:6, 3:6] = 300.0
    alert = np.zeros((9, 9), dtype=bool)
    alert[3:6, 3:6] = True
    rows, cols = [4, 3], [4, 3]
    l_bg, n_sin = pv.vrp_bg_neighbor_mean_v375(bt, alert, rows, cols, np.float64(0.123), max_half_px=1)
    assert n_sin == 1
    assert l_bg[0] == 0.123                                   # interior: respaldo escalar
    assert math.isclose(l_bg[1], float(_planck(255.0)), rel_tol=1e-12)   # borde: vecinos
    legado = np.array([0.5, 0.6])
    l_bg2, n_sin2 = pv.vrp_bg_neighbor_mean_v375(bt, alert, rows, cols, legado, max_half_px=1)
    assert n_sin2 == 1 and l_bg2[0] == 0.5                    # respaldo por píxel


@pytest.fixture(scope="module")
def v375_vecinos(tmp_path_factory):
    texto = correr_en_subproceso(tmp_path_factory.mktemp("d25"), perfil="mirova_equivalent",
                                 parches=("ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375=True",), solo="v375")
    return json.loads(texto)["v375"]


def _esperado_vrp(bt4, alert, r, c):
    """Reimplementa la cuenta a mano desde la escena: media de la radiancia de los vecinos no
    alertados, por Wooster, con el área nadir fija que usa producción."""
    import pipeline.process_viirs as pv
    ventana = bt4[r - 1:r + 2, c - 1:c + 2]
    usable = ~alert[r - 1:r + 2, c - 1:c + 2] & np.isfinite(ventana)
    l_bk = float(np.mean(_planck(ventana[usable])))
    l_hot = float(pv.bt_to_spectral_radiance(np.float64(bt4[r, c]), pv.I04_LAMBDA))
    area = pv.NADIR_PIXEL_AREA_M2   # nadir fijo en producción (ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS)
    return area * pv.WOOSTER_COEFF * max(l_hot - l_bk, 0.0) / 1e6


def test_extremo_a_extremo_el_crater_deja_de_publicarse_en_cero(v375_vecinos):
    """Con el fondo del anillo regional el cráter sale más frío que su propio fondo y se recorta a
    0,0 MW; con el fondo de los vecinos pasa a tener magnitud."""
    bands, _geo = escena_v375("nevado_vecino_tibio")
    bt4 = bands["I04"].astype(np.float64)
    c = CENTRO_V375
    alert = np.zeros(bt4.shape, dtype=bool)
    alert[c, c] = alert[c, c + 1] = True
    hoy = GOLDEN["v375"]["nevado_vecino_tibio|kernel=False"]
    on = v375_vecinos["nevado_vecino_tibio|kernel=False"]
    assert [p["vrp_mw"] for p in hoy["anomaly_pixels"]] == [0.0, 0.0]
    por_bt = {p["bt_k"]: p["vrp_mw"] for p in on["anomaly_pixels"]}
    assert math.isclose(por_bt[266.0], _esperado_vrp(bt4, alert, c, c), abs_tol=6e-5)
    assert math.isclose(por_bt[262.0], _esperado_vrp(bt4, alert, c, c + 1), abs_tol=6e-5)
    assert por_bt[266.0] > 0.0
    # la detección y el fondo del anillo no se tocan: sólo la resta
    assert on["t_bg_k"] == hoy["t_bg_k"] and on["n_anomalous_pixels"] == hoy["n_anomalous_pixels"]
    assert on["diag_bg_vecinos_n_sin_vecinos"] == 0
    assert on["diag_L_bg_vecinos_w_m2_sr_um"] is not None
    assert "diag_bg_vecinos_n_sin_vecinos" not in hoy


def test_el_camino_del_test1_tambien_recibe_el_fondo_nuevo(v375_vecinos):
    """H1 y b3. En esta escena el bloque contextual NO corre (cero píxeles anómalos), así que si el
    diagnóstico del fondo por vecinos aparece, lo escribió el bloque del Test 1 que reconstruye
    `anomaly_pixels`: es la prueba observable de que ese bloque recibe el fondo nuevo y de que su
    diagnóstico describe la población publicada y no la de otro bloque."""
    hoy = GOLDEN["v375"]["test1_difuso|kernel=False"]
    on = v375_vecinos["test1_difuso|kernel=False"]
    assert hoy["n_anomalous_pixels"] == 0 and on["n_anomalous_pixels"] == 0
    assert hoy["final_hotspot_source"] == "test1_roi" == on["final_hotspot_source"]
    assert json.dumps(on["anomaly_pixels"], sort_keys=True) != json.dumps(hoy["anomaly_pixels"], sort_keys=True)
    assert on["diag_L_bg_vecinos_w_m2_sr_um"] is not None
    assert on["diag_bg_vecinos_n_sin_vecinos"] == 0


def test_fuente_el_bloque_nuevo_va_despues_del_legado_y_el_recorte_sigue():
    s = _src("pipeline/process_viirs.py")
    legado = re.search(r"^\s*if ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible:", s, flags=re.M)
    nuevo = re.search(r"^\s*if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:\s*$", s, flags=re.M)
    recorte = re.search(r"^\s*delta_L = np\.maximum\(L_hot - L_bg, 0\.0\)", s, flags=re.M)
    assert legado and nuevo and recorte
    assert legado.start() < nuevo.start() < recorte.start()
    # los dos bloques del Test 1 usan el fondo por vecinos bajo el flag
    assert len(re.findall(r"_t1_Lbg, _n_sin = vrp_bg_neighbor_mean_v375\(", s)) == 2
    assert len(re.findall(r"np\.maximum\(t1_L - _t1_Lbg, 0\.0\)", s)) == 2


def test_fuente_el_contador_se_reinicia_en_el_bloque_publicado_del_test1():
    """b3 (hallazgo H8): el bloque contextual ACUMULA y el del Test 1 que reconstruye
    `anomaly_pixels` REINICIA, para que el contador y la mediana del fondo describan lo publicado
    y no la suma de dos poblaciones distintas."""
    s = _src("pipeline/process_viirs.py")
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos \+= _n_sin", s)) == 1
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos = _n_sin", s)) == 1
    assert len(re.findall(r"diag_L_bg_vecinos = redondear_diag\(", s)) == 2


@pytest.mark.parametrize("rel", ["pipeline/process_modis.py", "pipeline/process_viirs_mod.py"])
def test_modis_no_conoce_el_fondo_por_vecinos_y_v750_usa_solo_el_suyo(rel):
    """MODIS sigue con la mediana del anillo (D25 abierta ahi, S145 no lo toca).

    VIIRS 750 desde S145 tiene su propio fondo por vecinos: puede nombrar el helper compartido y su
    propio flag, nunca el de I-band (A92: el modo de falla de esta familia es el sensor equivocado
    leyendo el flag del otro).
    """
    s = _src(rel)
    prohibidos = ["ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375", "vrp_bg_neighbor_mean_v375"]
    if "process_modis" in rel:
        prohibidos += ["neighbor_mean_radiance_background", "VRP_BG_NEIGHBOR_MAX_HALF_PX",
                       "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"]
    else:
        # control de instrumento: si V750 dejara de cablearlo, este test pasaria por omision
        assert re.search(r"(?<![A-Za-z0-9_])ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750(?![A-Za-z0-9_])", s)
    for token in prohibidos:
        assert not re.search(r"(?<![A-Za-z0-9_])" + token + r"(?![A-Za-z0-9_])", s), (rel, token)
