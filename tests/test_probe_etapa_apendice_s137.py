"""S137 - guards del probe por etapa del Apendice A.

POR QUE. El probe envuelve la funcion de los Tests 2 y 3 dentro del procesador. Tres cosas pueden
hacer que mida mal sin avisar: que el envoltorio cambie lo que devuelve (entonces ya no observa, altera),
que no restaure la funcion o el flag de banda (entonces contamina el brazo siguiente), y que la
descomposicion por condicion cuente otra cosa que la que dice. Los tres se fijan antes de correr.
"""
import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def _mod():
    sys.path.insert(0, str(RAIZ / "experiments" / "_s137"))
    return importlib.import_module("probe_etapa_apendice")


def _escena(n=11, fondo=-0.93, pico=None, bt_fondo=260.0, bt_pico=None):
    nti = np.full((n, n), fondo)
    bt = np.full((n, n), bt_fondo)
    c = n // 2
    if pico is not None:
        nti[c, c] = pico
    if bt_pico is not None:
        bt[c, c] = bt_pico
    yy, xx = np.mgrid[0:n, 0:n]
    dist = np.hypot(yy - c, xx - c)  # 1 km por pixel
    roi = np.ones((n, n), dtype=bool)
    return nti, bt, dist, roi


def test_importar_no_toca_el_stdout():
    sys.modules.pop("probe_etapa_apendice", None)
    antes = sys.stdout
    try:
        _mod()
        assert sys.stdout is antes
    finally:
        sys.stdout = antes


def test_escena_plana_no_tiene_candidatos():
    m = _mod()
    nti, bt, dist, roi = _escena()
    st = m.estadisticas_etapa(nti, nti.copy(), bt, dist, roi, 250.0, 1.0, inner_km=5.0, c1=0.003,
                              c2=5.0, mu_dnti=0.0, sd_dnti=0.001, mu_deti=0.0, sd_deti=0.001)
    assert st["min"]["n_ambos"] == 0


def test_un_pico_en_el_crater_pasa_las_cuatro_condiciones():
    m = _mod()
    nti, bt, dist, roi = _escena(pico=-0.90, bt_pico=270.0)
    st = m.estadisticas_etapa(nti, nti.copy(), bt, dist, roi, 250.0, 1.0, inner_km=5.0, c1=0.003,
                              c2=5.0, mu_dnti=0.0, sd_dnti=0.001, mu_deti=0.0, sd_deti=0.001)
    mn = st["min"]
    assert (mn["n_dnti"], mn["n_deti"], mn["n_ambos"], mn["n_ambos_y_bt"]) == (1, 1, 1, 1)
    assert st["mejor"]["dist_km"] == 0.0 and st["crater"]["dist_km"] == 0.0
    assert st["mejor"]["dnti"] == pytest.approx(0.03)


def test_la_compuerta_de_temperatura_se_cuenta_aparte():
    """Pico espectral real pero pixel frio: pasa dNTI y dETI y cae solo en la compuerta BT."""
    m = _mod()
    nti, bt, dist, roi = _escena(pico=-0.90, bt_pico=240.0)
    st = m.estadisticas_etapa(nti, nti.copy(), bt, dist, roi, 250.0, 1.0, inner_km=5.0, c1=0.003,
                              c2=5.0, mu_dnti=0.0, sd_dnti=0.001, mu_deti=0.0, sd_deti=0.001)
    assert st["min"]["n_ambos"] == 1 and st["min"]["n_ambos_y_bt"] == 0
    assert st["mejor"]["pasa_bt"] is False


def test_fuera_del_radio_no_cuenta():
    m = _mod()
    nti, bt, dist, roi = _escena(pico=-0.90, bt_pico=270.0)
    st = m.estadisticas_etapa(nti, nti.copy(), bt, dist, roi, 250.0, 1.0, inner_km=0.5, c1=0.003,
                              c2=5.0, mu_dnti=0.0, sd_dnti=0.001, mu_deti=0.0, sd_deti=0.001)
    assert st["n_inner"] == 1  # solo el pixel central cae a <= 0,5 km


def test_la_prosa_usa_el_mayor_de_los_dos_umbrales():
    m = _mod()
    nti, bt, dist, roi = _escena(pico=-0.90, bt_pico=270.0)
    st = m.estadisticas_etapa(nti, nti.copy(), bt, dist, roi, 250.0, 1.0, inner_km=5.0, c1=0.003,
                              c2=5.0, mu_dnti=0.0, sd_dnti=0.01, mu_deti=0.0, sd_deti=0.01)
    assert st["min"]["thr_dnti"] == pytest.approx(0.003)
    assert st["max"]["thr_dnti"] == pytest.approx(0.05)
    assert st["min"]["n_ambos"] == 1 and st["max"]["n_ambos"] == 0


def test_el_envoltorio_devuelve_exactamente_lo_mismo():
    m = _mod()
    sentinela = (object(), {"eti": None, "n_bg_used": 3})
    env = m.envolver(lambda **kw: sentinela)
    assert env(nti=None) is sentinela


def test_correr_brazo_restaura_funcion_y_flags_aunque_reviente():
    m = _mod()
    import pipeline.process_modis as pm
    antes = (pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID, pm.first_pass_tests_2_and_3)
    orig = pm.calculate_vrp
    visto = {}

    def explota(*a, **k):
        visto["b22"], visto["regrid"] = pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID
        visto["envuelta"] = pm.first_pass_tests_2_and_3 is not antes[2]
        raise RuntimeError("granule corrupto")

    pm.calculate_vrp = explota
    try:
        out = m.correr_brazo(Path("x.hdf"), None, {"lat": 0.0, "lon": 0.0}, True, True)
    finally:
        pm.calculate_vrp = orig
    assert visto == {"b22": True, "regrid": True, "envuelta": True}, "el brazo no quedo activo durante la llamada"
    assert "error" in out
    assert (pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID, pm.first_pass_tests_2_and_3) == antes


def test_los_brazos_son_b21_b22_y_b22_con_remuestreo():
    m = _mod()
    assert m.BRAZOS == {"B21": (False, False), "B22": (True, False), "B22_regrid": (True, True)}


def test_rumbo_cardinales():
    m = _mod()
    assert m.rumbo_deg(0, 0, 1, 0) == pytest.approx(0.0, abs=1e-6)
    assert m.rumbo_deg(0, 0, 0, 1) == pytest.approx(90.0, abs=1e-6)
    assert m.rumbo_deg(0, 0, -1, 0) == pytest.approx(180.0, abs=1e-6)
