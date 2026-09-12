"""S137 - guards del probe de sigma del dNTI.

El probe monkeypatchea dos flags del namespace de process_modis. Si no los restaura, contamina
todos los brazos siguientes y el resultado seria un artefacto del orden de ejecucion, no una
medicion. Eso es justo el tipo de trampa de instrumento que este proyecto lleva doce veces
encontrando (A92, A93), asi que el guard va escrito antes de correrlo.
"""
import importlib
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def _mod():
    sys.path.insert(0, str(RAIZ / "experiments" / "_s137"))
    return importlib.import_module("sigma_dnti_4brazos")


def test_los_cuatro_brazos_son_las_cuatro_combinaciones():
    m = _mod()
    combos = {(v["b22"], v["regrid"]) for v in m.BRAZOS.values()}
    assert combos == {(False, False), (True, False), (False, True), (True, True)}
    assert m.BRAZOS["base"] == {"b22": False, "regrid": False}


def test_las_constantes_son_las_de_la_tabla_1_noche_roi1():
    m = _mod()
    assert m.C1_SUMMIT == 0.003
    assert m.C2_SUMMIT == 5.0


def test_correr_restaura_los_flags_aunque_el_pipeline_reviente():
    """El finally debe devolver los flags a su valor original incluso con excepcion."""
    m = _mod()
    import pipeline.process_modis as pm

    antes = (pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID)

    def explota(*a, **k):
        raise RuntimeError("granule corrupto")

    orig = pm.calculate_vrp
    pm.calculate_vrp = explota
    try:
        out = m.correr(Path("x.hdf"), None, {"lat": 0.0, "lon": 0.0}, "ambos")
    finally:
        pm.calculate_vrp = orig

    assert out is None, "una excepcion debe dar None, no propagarse"
    assert (pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID) == antes, (
        "el probe dejo los flags cambiados: los brazos siguientes quedarian contaminados")


def test_correr_aplica_los_flags_del_brazo_durante_la_llamada():
    """Y que efectivamente los cambie mientras corre, si no el A/B mide un solo brazo."""
    m = _mod()
    import pipeline.process_modis as pm

    visto = {}

    def espia(*a, **k):
        visto["b22"] = pm.ENABLE_MODIS_B22_PRIMARY
        visto["regrid"] = pm.ENABLE_UTM_REGRID
        return None

    orig = pm.calculate_vrp
    pm.calculate_vrp = espia
    try:
        m.correr(Path("x.hdf"), None, {"lat": 0.0, "lon": 0.0}, "ambos")
    finally:
        pm.calculate_vrp = orig

    assert visto == {"b22": True, "regrid": True}


def test_mediana_ignora_los_none():
    m = _mod()
    assert m.mediana([1.0, None, 3.0, 2.0]) == 2.0
    assert m.mediana([None]) is None
    assert m.mediana([]) is None


@pytest.mark.parametrize("nombre", ["base", "b22", "regrid", "ambos"])
def test_el_json_del_brazo_trae_sd_dnti(nombre):
    """La clave que el probe mide no puede cambiar de nombre sin que el guard lo note (A89)."""
    m = _mod()
    import pipeline.process_modis as pm

    def falso(*a, **k):
        return {"diag_mu_dnti": 0.001, "diag_sd_dnti": 0.007, "primary_cluster": None}

    orig = pm.calculate_vrp
    pm.calculate_vrp = falso
    try:
        out = m.correr(Path("x.hdf"), None, {"lat": 0.0, "lon": 0.0}, nombre)
    finally:
        pm.calculate_vrp = orig

    assert out["sd_dnti"] == 0.007
    assert out["mu_dnti"] == 0.001
