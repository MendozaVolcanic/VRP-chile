# -*- coding: utf-8 -*-
"""S165: guard de los tres flags MxD03 de MODIS (plan 2026-10-25-flag-mxd03-modis, Tareas 1 y 6).

POR QUÉ. Los tres flags entran APAGADOS (sí de Nicolás en el chat de la sesión S165, A45; tag pre-s165-mxd03-modis).
Antes de que nadie los encienda, cada una de estas cosas tiene su prueba:
  1. existen, están apagados en producción y en el laboratorio, y se leen de `thresholds:` (S124, A89): una clave
     escrita en la raíz del YAML no los enciende;
  2. con los tres apagados, `calculate_vrp` da lo que daba el código del tag (golden congelado antes de tocar
     pipeline/, `tests/datos_s165_mxd03/apagado_antes.json`), también en las tres escenas del arnés S142;
  3. cada flag encendido SÍ cambia lo que debe (control, A116), y llega a todos sus consumidores (A118): la distancia
     del píxel anómalo, la del hotspot y la final salen del cráter; el anillo de fondo no cambia.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import arnes_mxd03_s165 as ARNES  # noqa: E402
import arnes_sintetico_s142 as S142  # noqa: E402

FLAGS = ("ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER")
GEO, SIN_DATO, DIST = FLAGS
DATOS = REPO / "tests" / "datos_s165_mxd03"


def _leer_flags(perfil, inyectar=None, donde="thresholds"):
    """Lee los flags como los lee el código, importando pipeline.profile en un proceso limpio. `inyectar` agrega una
    clave al YAML cargado (en `thresholds:` o en la raíz) sin tocar el archivo."""
    codigo = ["import yaml", "_o = yaml.safe_load",
              "def _f(x):",
              "    c = _o(x)",
              f"    if {inyectar!r} and isinstance(c, dict) and 'thresholds' in c:",
              f"        (c['thresholds'] if {donde!r} == 'thresholds' else c)[{inyectar!r}] = True",
              "    return c",
              "yaml.safe_load = _f",
              "import pipeline.profile as p, pipeline.process_modis as pm",
              f"print([(getattr(p, n), getattr(pm, n)) for n in {FLAGS!r}])"]
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", "\n".join(codigo)], cwd=REPO, env=env, capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != 0:  # caída, no aserción (ver arnes_mxd03_s165.correr_en_subproceso)
        raise RuntimeError(r.stderr[-3000:])
    return dict(zip(FLAGS, eval(r.stdout.strip().splitlines()[-1])))  # noqa: S307 (salida propia)


# ------------------------------------------------------------------------------------------------ 1. los flags
@pytest.mark.parametrize("perfil", ["mirova_equivalent", "experimental"])
def test_flags_existen_y_estan_apagados(perfil):
    for nombre, (en_perfil, en_modis) in _leer_flags(perfil).items():
        assert en_perfil is False and en_modis is False, nombre


@pytest.mark.parametrize("clave,nombre", [("enable_modis_geo_mxd03", GEO),
                                          ("enable_modis_crater_sin_dato", SIN_DATO),
                                          ("enable_modis_dist_desde_crater", DIST)])
def test_flag_se_lee_de_thresholds_y_no_de_la_raiz(clave, nombre):
    assert _leer_flags("mirova_equivalent", clave, "thresholds")[nombre] == (True, True)
    assert _leer_flags("mirova_equivalent", clave, "raiz")[nombre] == (False, False)


def test_las_claves_estan_escritas_apagadas_en_thresholds():
    import yaml
    cfg = yaml.safe_load((REPO / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8"))
    for clave in ("enable_modis_geo_mxd03", "enable_modis_crater_sin_dato", "enable_modis_dist_desde_crater"):
        assert cfg["thresholds"][clave] is False, clave
        assert clave not in cfg, clave


# ------------------------------------------------------------------------------------------------ 2. bit a bit
def _canon(obj):
    return json.dumps(S142._redondear(obj), sort_keys=True, default=S142._a_json, ensure_ascii=False)


# `.get("geo_fuente")` y no `["geo_fuente"]`: si el campo dejara de escribirse, la prueba tiene que FALLAR por aserción,
# no caerse con KeyError (la batería de mutaciones cuenta una caída como no atrapada, S152 y S156).
def _correr(tmp_path, *flags):
    return json.loads(ARNES.correr_en_subproceso(tmp_path, flags))


@pytest.fixture(scope="module")
def corridas(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mxd03")
    combos = {"apagado": (), "geo": (GEO,), "sin_dato": (SIN_DATO,), "dist": (DIST,),
              "geo_sin_dato": (GEO, SIN_DATO), "los_tres": FLAGS}
    return {k: _correr(tmp, *v) for k, v in combos.items()}


def test_apagado_bit_a_bit_con_el_tag(corridas):
    antes = json.loads((DATOS / "apagado_antes.json").read_text(encoding="utf-8"))
    assert _canon(corridas["apagado"]) == _canon(antes)
    # El golden no es trivial: las cuatro escenas publican calor y la etiqueta de hoy es far.
    assert all(antes[t]["vrp_mw"] > 0 and antes[t]["distance_class"] == "far" for t in ARNES.ESCENAS)


def test_apagado_bit_a_bit_en_las_escenas_s142(tmp_path):
    """Las tres escenas MODIS del arnés S142 contra el golden que congeló #919 (modis_k_antes.json)."""
    hoy = S142.correr_en_subproceso(tmp_path, solo="modis")
    antes = json.loads((REPO / "tests" / "datos_s164_modis" / "modis_k_antes.json").read_text(encoding="utf-8"))
    assert _canon(json.loads(hoy)["modis"]) == _canon(antes["modis"])


# ------------------------------------------------------------------------------------------------ 3. controles
def test_sin_dato_solo_no_cambia_nada(corridas):
    """El estado «sin dato» sólo actúa con la posición del MxD03 (con la interpolada, el relleno no es NaN)."""
    assert _canon(corridas["sin_dato"]) == _canon(corridas["apagado"])


def test_geo_cambia_la_posicion_y_lo_declara(corridas):
    a, g = corridas["apagado"]["mxd03_corrido"], corridas["geo"]["mxd03_corrido"]
    assert "geo_fuente" not in a                      # apagado: el record no gana campos
    assert g.get("geo_fuente") == "mxd03"
    assert g["final_hotspot_lat"] == pytest.approx(a["final_hotspot_lat"] - 2.0 / 111.0, abs=2e-5)
    assert g["hotspot_dist_km"] != a["hotspot_dist_km"]
    # En la escena sin corrimiento, el MxD03 es la misma grilla: sólo cambia la declaración de la fuente.
    e_a, e_g = dict(corridas["apagado"]["etiqueta"]), dict(corridas["geo"]["etiqueta"])
    assert e_g.pop("geo_fuente", None) == "mxd03"
    assert _canon(e_g) == _canon(e_a)


def test_geo_con_relleno_sin_estado_sigue_dando_record(corridas):
    r = corridas["geo"]["crater_relleno"]
    assert r is not None and r.get("geo_fuente") == "mxd03"


@pytest.mark.parametrize("escena", ["crater_relleno", "crater_borde"])
def test_geo_y_sin_dato_no_escriben_record_sin_crater(corridas, escena):
    assert corridas["geo"][escena] is not None
    assert corridas["geo_sin_dato"][escena] is None
    # Con el cráter cubierto, el estado no quita la pasada.
    assert corridas["geo_sin_dato"]["etiqueta"] is not None


def test_sin_dato_se_juzga_desde_el_crater_y_no_desde_el_centro():
    """En `crater_relleno` el píxel del cráter tiene un vecino sin posición y el del centro del volcán no."""
    import pipeline.process_modis as pm
    _data, (lat_m, lon_m), vent_lat, vent_lon = ARNES.escena("crater_relleno")
    assert pm.crater_cubierto(lat_m, lon_m, vent_lat, vent_lon) is False
    assert pm.crater_cubierto(lat_m, lon_m, S142.LAT0, S142.LON0) is True


def test_dist_desde_el_crater_llega_a_todos_sus_consumidores(corridas):
    a, d = corridas["apagado"]["etiqueta"], corridas["dist"]["etiqueta"]
    esperado = 5.0 - ARNES.VENT_NORTE_KM            # el píxel está 5 km al norte del centro, el cráter 0,68 km
    assert a["distance_class"] == "far" and d["distance_class"] == "summit"
    assert d["anomaly_pixels"][0]["dist_km"] == pytest.approx(esperado, abs=0.02)
    assert d["hotspot_dist_km"] == pytest.approx(esperado, abs=0.02)
    assert d["final_hotspot_dist_km"] == pytest.approx(esperado, abs=0.02)
    # El anillo de fondo sigue centrado en el volcán (D17, fuera de alcance) y la magnitud no cambia.
    for campo in ("diag_n_bg_anillo", "diag_L_bg_w_m2_sr_um", "diag_sigma_bg_k", "vrp_mw", "n_anomalous_pixels"):
        assert d[campo] == a[campo], campo


def test_los_tres_juntos(corridas):
    t = corridas["los_tres"]
    assert t["crater_relleno"] is None and t["crater_borde"] is None
    assert t["mxd03_corrido"].get("geo_fuente") == "mxd03"
    assert t["etiqueta"]["distance_class"] == "summit"
