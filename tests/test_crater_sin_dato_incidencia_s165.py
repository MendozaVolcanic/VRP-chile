# -*- coding: utf-8 -*-
"""S165 (V165-03): la pasada que el flag «sin dato» descarta queda anotada en la cobertura.

POR QUÉ. Con ENABLE_MODIS_CRATER_SIN_DATO encendido (#920, APAGADO en producción), una pasada en que el cráter no
tiene posición en el gránulo no deja record: no es una noche observada sin anomalía, es una noche sin dato. El
verificador de #920 encontró que tampoco dejaba rastro: `run_pipeline` sólo anota incidencias cuando falta el
archivo de geolocalización entero (S159), y el resumen seguía diciendo «Cobertura: completa». Medido en el censo
MOD-D, serían 223 de 5.465 pasadas MODIS que desaparecerían sin aviso.

Decisiones (Nicolás, chat de la sesión S165, 2026-10-27): se anota como incidencia nueva `crater_sin_dato` y NO
cuenta en modo estricto. El modo estricto existe para que un brazo de un A/B con pasadas de menos por un corte de
NASA se repita (A108); este descarte sale de la geometría de la órbita y repetir el job no lo recupera. Contra un
control sin el flag (el A/B que decida encenderlo) lo explica `evaluador_comun.CAUSA_SIN_DATO_CRATER`.

Con el flag apagado la corrida es idéntica, bit a bit, a la del tag pre-s165-v165-03-sin-dato (golden congelado
antes de tocar pipeline/ y scripts/, `tests/datos_s165_mxd03/sin_dato_corrida_*_antes.json`).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import arnes_mxd03_s165 as M  # noqa: E402
import arnes_sin_dato_s165 as ARNES  # noqa: E402

GEO, SIN_DATO = "ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO"
DATOS = REPO / "tests" / "datos_s165_mxd03"
SIN_CRATER = ("crater_borde", "crater_relleno")
CON_CRATER = ("etiqueta", "mxd03_corrido")


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sin_dato_s165")
    return {
        "apagado": ARNES.correr_en_subproceso(tmp),
        "geo": ARNES.correr_en_subproceso(tmp, (GEO,)),
        "geo_sin_dato": ARNES.correr_en_subproceso(tmp, (GEO, SIN_DATO)),
    }


def _sin_incidencias(d):
    """La corrida sin lo que este cambio agrega: las incidencias y su conteo."""
    out = json.loads(json.dumps(d))
    for v in out.values():
        v["cobertura"].pop("incidencias", None)
        v["cobertura"].pop("n_incidencias", None)
    return out


def _incidencias(v, tipo="crater_sin_dato"):
    return [i for i in v["cobertura"].get("incidencias", []) if i.get("tipo") == tipo]


# ---------------------------------------------------------------- con el flag apagado, nada cambia

def test_apagado_bit_a_bit_con_el_tag(corridas):
    antes = (DATOS / "sin_dato_corrida_apagado_antes.json").read_text(encoding="utf-8")
    assert corridas["apagado"] == antes


def test_geo_solo_no_anota_nada(corridas):
    d = json.loads(corridas["geo"])
    assert all(not _incidencias(v) for v in d.values())
    assert all(len(v["records"]) == 1 for v in d.values())


# ---------------------------------------------------------------- con el flag encendido, la pasada queda anotada

@pytest.mark.parametrize("escena", SIN_CRATER)
@pytest.mark.parametrize("estricto", [False, True])
def test_pasada_sin_dato_queda_anotada(corridas, escena, estricto):
    v = json.loads(corridas["geo_sin_dato"])[f"{escena}|estricto={estricto}"]
    assert v["records"] == []
    inc = _incidencias(v)
    assert len(inc) == 1, v["cobertura"]
    i = inc[0]
    assert i["volcan"] == ARNES.VOLCAN and i["fecha"] == ARNES.FECHA and i["plataforma"] == "MODIS_TERRA"
    assert ARNES.L1B in i["motivo"]
    assert i["cuenta_estricto"] is False
    assert v["codigo"] == 0          # ni con --estricto-cobertura (decisión de Nicolás, S165)


@pytest.mark.parametrize("escena", CON_CRATER)
def test_pasada_con_crater_no_anota(corridas, escena):
    d = json.loads(corridas["geo_sin_dato"])
    for estricto in (False, True):
        v = d[f"{escena}|estricto={estricto}"]
        assert not _incidencias(v) and len(v["records"]) == 1


def test_control_cambia_y_solo_en_las_incidencias(corridas):
    """Contra lo que el tag hacía con los mismos flags: cambia (A116) y lo único que cambia es la incidencia."""
    antes = json.loads((DATOS / "sin_dato_corrida_geo_sin_dato_antes.json").read_text(encoding="utf-8"))
    ahora = json.loads(corridas["geo_sin_dato"])
    assert ahora != antes
    assert _sin_incidencias(ahora) == _sin_incidencias(antes)
    assert all(not _incidencias(v) for v in antes.values())   # el defecto que V165-03 describe, en el golden


# ---------------------------------------------------------------- las piezas por separado

def test_el_tipo_existe_y_no_cuenta_en_estricto():
    from pipeline import fetch
    assert fetch.TIPOS_INCIDENCIA["crater_sin_dato"] is False


def _calcular(tipo, flags, al_sin_dato):
    import pipeline.process_modis as pm
    data, mxd, vent_lat, vent_lon = M.escena(tipo)
    ctx = [patch.object(pm, "read_modis_l1b", return_value=data), patch.object(pm, "leer_mxd03", return_value=mxd)]
    ctx += [patch.object(pm, k, v) for k, v in flags.items()]
    for p in ctx:
        p.start()
    try:
        return pm.calculate_vrp(
            hdf_path=Path(ARNES.L1B), geo_path=Path(ARNES.GEO), volcano_lat=M.A.LAT0, volcano_lon=M.A.LON0,
            radius_km=25.0, vent_lat=vent_lat, vent_lon=vent_lon, inner_radius_km=M.INNER_KM,
            al_sin_dato=al_sin_dato)
    finally:
        for p in ctx:
            p.stop()


@pytest.mark.parametrize("flags,escena,avisa", [
    ({GEO: True, SIN_DATO: True}, "crater_borde", True),
    ({GEO: True, SIN_DATO: True}, "crater_relleno", True),
    ({GEO: True, SIN_DATO: True}, "etiqueta", False),
    ({GEO: True}, "crater_borde", False),
    ({SIN_DATO: True}, "crater_borde", False),
    ({}, "crater_borde", False),
])
def test_calculate_vrp_avisa_solo_cuando_descarta(flags, escena, avisa):
    avisos = []
    r = _calcular(escena, flags, avisos.append)
    if avisa:
        assert r is None and len(avisos) == 1 and ARNES.L1B in avisos[0]
    else:
        assert avisos == [] and r is not None


def test_sin_aviso_sigue_devolviendo_none():
    """Un llamador que no pasa el aviso (experimentos) recibe el mismo None de antes."""
    assert _calcular("crater_borde", {GEO: True, SIN_DATO: True}, None) is None


@pytest.mark.parametrize("estricto", [False, True])
def test_el_resumen_nombra_el_caso(capsys, tmp_path, estricto):
    spec = importlib.util.spec_from_file_location("run_pipeline_s165_t", REPO / "scripts" / "run_pipeline.py")
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    inc = [{"tipo": "crater_sin_dato", "cuenta_estricto": False, "volcan": "Villarrica", "fecha": "2026-07-19",
            "plataforma": "MODIS_TERRA", "motivo": "simulado"}]
    cod = rp.informar_cobertura([], ruta_json=tmp_path / "c.json", estricto=estricto, incidencias=inc)
    out = capsys.readouterr().out
    assert cod == 0
    assert "Cobertura: completa" not in out
    assert "cráter sin posición" in out and "no cuenta en modo estricto" in out


# ---------------------------------------------------------------- el evaluador de los A/B la reconoce (V16503-01)

def test_el_evaluador_distingue_la_pasada_sin_dato_de_una_perdida():
    """Verificador de #922 (V16503-01): `evaluador_comun.causa_ausencia` no conocía el tipo y devolvía «el run no
    registró nada» para una pasada cuyo único evento era la incidencia. En el A/B que decida encender el flag, las
    pasadas descartadas quedarían indistinguibles de una pérdida del proceso. Se reusa la pasada de VIIRS 750 de la
    prueba S163 porque la función empareja por volcán, día y sensor; en producción el tipo sólo lo anota MODIS."""
    import test_evaluador_comun_s163 as T163
    from scripts import evaluador_comun as ec
    f = [x for x in T163._fila_T() if x["pasada"].instante.strftime("%H:%M") == "05:18"][0]
    ev = {"tipo": "crater_sin_dato", "volcan": T163.CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}
    assert ec.causa_ausencia(f, "K", [ev]) == ec.CAUSA_SIN_DATO_CRATER
    falla = {"tipo": "falla_busqueda", "volcan": T163.CH, "fecha": "2026-10-12", "plataforma": "VIIRS_NOAA21_750"}
    assert ec.causa_ausencia(f, "K", [ev, falla]) == ec.CAUSA_HUECO          # una falla de NASA manda
    vacia = {"tipo": "sin_granulos", "volcan": T163.CH, "fecha": "2026-10-12", "plataforma": "VIIRS_SNPP_750"}
    assert ec.causa_ausencia(f, "K", [vacia, ev]) == ec.CAUSA_SIN_DATO_CRATER  # el descarte es un hecho, la vacía no
    assert ec.causa_ausencia(f, "K", [dict(ev, volcan="Lascar")]) == ec.CAUSA_SIN_INCIDENCIA
