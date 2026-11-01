# -*- coding: utf-8 -*-
"""S157: la vuelta a radiancia de MODIS con K usa la longitud de onda de la banda de donde vino la temperatura.

POR QUÉ FÍSICO. MIROVA arma UNA banda MIR corregida, L21ok, «centred at 3.959 µm», con la radiancia de B22 o
la de B21 donde B22 satura (Coppola 2016a, sp426.5.pdf p. 3, columna derecha, leída renderizada) y calcula el
exceso directamente en radiancia, ΔL = L_alerta − L_fondo, antes de multiplicar por 18,9 · A (p. 8, Ec. 6 y 7).
El pipeline pasa por temperatura de brillo (los umbrales trabajan en K) y vuelve a radiancia para la Ec. 7.
Esa ida y vuelta sólo devuelve la radiancia medida si usa la MISMA λ en los dos sentidos. Con K (B22
primaria, D21) la ida es con 3,959 µm y la vuelta seguía con 3,929 µm: la radiancia que entra a la Ec. 7 sale
~5 % más baja que la medida (medido en experiments/_s157_lambda_b22/: F mediano 1,0575 sobre 24 records).

QUÉ EXIGE EL TEST. Con el flag `enable_modis_mir_lambda_por_banda` encendido, el VRP de cada píxel alertado es
18,9 · A · (L_medida − L_fondo), con L_medida la radiancia de B22 en un píxel donde B22 no saturó y la de B21
donde sí saturó, y L_fondo la radiancia de Planck del fondo con la λ de la banda primaria. Con el flag
apagado el procesador queda bit a bit como hoy (A45): se comprueba que el defecto sigue ahí, que es la
prueba de que el test lo ve.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import process_modis as pm  # noqa: E402

CLAT, CLON = -36.86, -71.38   # una escena cualquiera; el volcán va al centro
N = 61
SPAN_KM = 30.0
T_FONDO = 275.0
T_B22 = 300.0        # píxel caliente que B22 todavía mide
T_B21 = 420.0        # píxel que satura B22 (~331 K) y entra por B21
T_TIR = 275.5


def _escena():
    rng = np.random.default_rng(7)
    lam21, lam22, lam31 = pm.BAND21_LAMBDA, pm.BAND22_LAMBDA, pm.BAND31_LAMBDA
    t_mir = T_FONDO + rng.normal(0.0, 0.05, size=(N, N))
    # B21 y B22 miran la misma ventana: la radiancia de la escena es UNA. Cada banda la reporta igual; lo que
    # cambia es con qué λ el pipeline la invierte. Se fabrica la radiancia con la λ de B22 (la del paper).
    rad = pm.bt_to_radiance(t_mir, lam22).astype(np.float32)
    band21 = rad.copy()
    band22 = rad.copy()
    band31 = pm.bt_to_radiance(np.full((N, N), T_TIR), lam31).astype(np.float32)
    c = N // 2
    p22, p21 = (c, c), (c, c + 2)   # dos píxeles dentro del cráter, separados por uno frío
    band21[p22] = band22[p22] = pm.bt_to_radiance(T_B22, lam22)
    band21[p21] = pm.bt_to_radiance(T_B21, lam22)
    band22[p21] = np.nan             # B22 saturada: calibrate() la deja en NaN
    dlat = SPAN_KM / 111.0
    dlon = SPAN_KM / (111.0 * np.cos(np.radians(CLAT)))
    lat, lon = np.meshgrid(np.linspace(CLAT - dlat, CLAT + dlat, N),
                           np.linspace(CLON - dlon, CLON + dlon, N), indexing="ij")
    data = {"band21": band21, "band22": band22, "band31": band31,
            "lat": lat.astype(np.float32), "lon": lon.astype(np.float32), "angles": {}}
    return data, p22, p21


def _correr(flag):
    data, p22, p21 = _escena()
    with patch.object(pm, "read_modis_l1b", return_value=data), \
         patch.object(pm, "ENABLE_MODIS_B22_PRIMARY", True), \
         patch.object(pm, "ENABLE_MODIS_MIR_LAMBDA_POR_BANDA", flag, create=True):
        rec = pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026290.0300.061.fake.hdf"), geo_path=Path("x"),
            volcano_lat=CLAT, volcano_lon=CLON, radius_km=25.0,
            vent_lat=CLAT, vent_lon=CLON, inner_radius_km=5.0)
    return rec, data, p22, p21


def _vrp_esperado(L_medida, rec, lam_fondo):
    L_fondo = pm.bt_to_radiance(rec["t_bg_k"], lam_fondo)
    return pm.WOOSTER_COEFF * pm.NADIR_PIXEL_AREA_M2 * (L_medida - L_fondo) / 1e6


def _pixel(rec, data, p):
    lat, lon = round(float(data["lat"][p]), 5), round(float(data["lon"][p]), 5)
    for a in rec["anomaly_pixels"]:
        if a["lat"] == lat and a["lon"] == lon:
            return a
    pytest.fail(f"el píxel {p} no quedó alertado: la escena sintética no ejercita el camino de magnitud")


def test_con_flag_el_pixel_de_b22_usa_su_radiancia_medida():
    rec, data, p22, _ = _correr(True)
    a = _pixel(rec, data, p22)
    esp = _vrp_esperado(float(data["band22"][p22]), rec, pm.BAND22_LAMBDA)
    assert a["vrp_mw"] == pytest.approx(esp, rel=1e-4)


def test_con_flag_el_pixel_de_b21_saturado_usa_la_radiancia_de_b21():
    rec, data, _, p21 = _correr(True)
    a = _pixel(rec, data, p21)
    esp = _vrp_esperado(float(data["band21"][p21]), rec, pm.BAND22_LAMBDA)
    assert a["vrp_mw"] == pytest.approx(esp, rel=1e-4)


def test_sin_flag_queda_el_defecto_de_hoy():
    """Control (A116): apagado, el píxel de B22 vuelve a radiancia con λ de B21 y sale más bajo que lo medido.
    Si esto dejara de fallar, el test de arriba no estaría midiendo la λ."""
    rec, data, p22, _ = _correr(False)
    a = _pixel(rec, data, p22)
    medido = _vrp_esperado(float(data["band22"][p22]), rec, pm.BAND22_LAMBDA)
    assert a["vrp_mw"] < medido / 1.03


def test_lambda_por_pixel_helper():
    rad21 = np.array([1.0, 2.0, np.nan], dtype=np.float32)
    rad22 = np.array([5.0, np.nan, np.nan], dtype=np.float32)
    lam = pm.lambda_mir_por_pixel(rad21, rad22, b22_primary=True, por_banda=True)
    assert lam[0] == pm.BAND22_LAMBDA and lam[1] == pm.BAND21_LAMBDA
    # Apagado: el ESCALAR histórico (no un arreglo float64), para que la aritmética float32 no cambie.
    assert pm.lambda_mir_por_pixel(rad21, rad22, b22_primary=True, por_banda=False) == pm.BAND21_LAMBDA
    assert np.ndim(pm.lambda_mir_por_pixel(rad21, rad22, b22_primary=True, por_banda=False)) == 0
    # Con B21 primaria (C0) la regla es la misma, «la λ de la banda de origen»: B22 sólo donde B21 es NaN.
    lam_c0 = pm.lambda_mir_por_pixel(np.array([1.0, np.nan]), np.array([5.0, 6.0]), b22_primary=False,
                                     por_banda=True)
    assert lam_c0[0] == pm.BAND21_LAMBDA and lam_c0[1] == pm.BAND22_LAMBDA
    assert pm.lambda_mir_fondo(b22_primary=True, por_banda=True) == pm.BAND22_LAMBDA
    assert pm.lambda_mir_fondo(b22_primary=True, por_banda=False) == pm.BAND21_LAMBDA
    assert pm.lambda_mir_fondo(b22_primary=False, por_banda=True) == pm.BAND21_LAMBDA


def test_flag_se_lee_desde_pipeline_profile_y_esta_apagado_en_produccion():
    """A89: el flag se lee de pipeline.profile (no del YAML a mano) y el procesador usa ESE valor. Encenderlo es
    decisión de Nicolás (A45)."""
    import pipeline.profile as prof
    assert prof.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA is False
    assert pm.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA is prof.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA


@pytest.mark.parametrize("seccion", [None, "paths"])
def test_la_clave_del_yaml_es_la_que_lee_el_codigo(seccion):
    """A89: el nombre de la clave en el YAML es el que `pipeline.profile` lee, en la raíz o en `paths:`. Se
    inyecta la clave encendida al cargar el perfil y se exige que la constante resuelva True. Si alguien la
    renombra en un lado y no en el otro, esto cae (un `grep` del nombre no lo vería)."""
    import importlib

    import yaml

    import pipeline.profile as prof
    real = yaml.safe_load

    def con_clave(f):
        cfg = real(f)
        if isinstance(cfg, dict) and "extends" not in cfg:
            (cfg if seccion is None else cfg.setdefault(seccion, {}))["enable_modis_mir_lambda_por_banda"] = True
            if seccion is not None:
                cfg.pop("enable_modis_mir_lambda_por_banda", None)  # que la raíz no tape a la sección
        return cfg

    try:
        with patch.object(yaml, "safe_load", con_clave):
            importlib.reload(prof)
        assert prof.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA is True
    finally:
        importlib.reload(prof)
    assert prof.ENABLE_MODIS_MIR_LAMBDA_POR_BANDA is False


def test_test1_acepta_lambda_por_pixel():
    """Verificador S157 H10: con el flag, el Test 1 integrado (apagado hoy, D30) también tiene que volver a
    radiancia con la λ de cada píxel; con una λ escalar de B22, un píxel de B21 a 420 K saldría 1,028 veces
    más brillante que lo medido. `bt_to_radiance_um` acepta un arreglo de λ con la forma de la temperatura y
    da lo mismo que llamarla píxel por píxel; con escalar, igual que siempre."""
    from pipeline.test1_integrated import bt_to_radiance_um
    bt = np.array([[268.0, 300.0], [np.nan, 420.0]])
    lam = np.array([[pm.BAND22_LAMBDA, pm.BAND22_LAMBDA], [pm.BAND22_LAMBDA, pm.BAND21_LAMBDA]])
    L = bt_to_radiance_um(bt, lam)
    for i, j in ((0, 0), (0, 1), (1, 1)):
        assert L[i, j] == bt_to_radiance_um(np.array([bt[i, j]]), float(lam[i, j]))[0]
    assert np.isnan(L[1, 0])
