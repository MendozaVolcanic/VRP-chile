# -*- coding: utf-8 -*-
"""S151 D-10 (issue #813): rama diurna VIIRS, apagada por flag.

POR QUÉ (el fenómeno). De día el canal de infrarrojo medio suma a la emisión térmica la luz solar
reflejada, y el NTI y el ETI se vuelven más variables. MIROVA no deja de mirar: procesa VIIRS de
día (Campus et al. 2022, Sensors 22:1713, p. 16 §5 y p. 17 Tabla 4) con umbrales más altos
(Coppola 2016a, sp426.5.pdf p. 7, Tabla 1: de día K1 = -0,6, C1 = 0,02 y C2 = 15 en ROI1 y ROI2).
La réplica descartaba todo VIIRS diurno en cuatro lugares distintos (filtro previo a la descarga,
salto del gránulo, umbrales del procesador y rechazo en store), así que perdía por construcción las
alertas diurnas de MIROVA (40 pasadas protegidas usables bajo A119).

QUÉ FIJAN ESTOS TESTS.
1. Con el flag apagado nada cambia, ni de noche ni de día (el golden bit a bit de S142 lo cubre de
   noche; acá se agrega la pasada diurna, que el golden no ejerce).
2. Con el flag encendido el flag llega a TODOS los consumidores (A118: en S92 el A/B diurno de MODIS
   abrió una compuerta y no la otra, y midió cero sin saberlo).
3. Con el flag encendido los umbrales diurnos llegan a las llamadas reales de los Tests 2 y 3, y
   el efecto se MIDE sobre una escena (A116), no se supone.
4. De noche el flag encendido no cambia nada.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import arnes_sintetico_s142 as arnes  # noqa: E402
from produccion_pre_k import produccion_pre_k  # noqa: E402

# Villarrica (la malla del arnés) el 2026-07-19 (día 200). 06:00 UTC es la madrugada local;
# 18:00 UTC es pasado el mediodía solar (elevación ~27°): pasada diurna sin ambigüedad.
NOCHE_V375 = "VNP02IMG.A2026200.0600.002.nc"
DIA_V375 = "VNP02IMG.A2026200.1800.002.nc"
NOCHE_V750 = "VNP02MOD.A2026200.0600.002.nc"
DIA_V750 = "VNP02MOD.A2026200.1800.002.nc"

# Campos que dependen sólo del nombre del gránulo, no de la detección.
CAMPOS_DEL_NOMBRE = {"granule", "datetime_utc", "product_version"}


def _flag(valor):
    import pipeline.profile as prof
    return patch.object(prof, "ENABLE_DAYTIME_VIIRS", valor)


def _sin_nombre(rec):
    return arnes.canonico({k: v for k, v in rec.items() if k not in CAMPOS_DEL_NOMBRE})


def _correr(modulo, escena, nombre, espias=()):
    """Corre un procesador VIIRS real sobre una escena del arnés S142, con el nombre de gránulo
    pedido. `espias` son nombres de funciones del módulo a envolver: se llaman las REALES y se
    guardan sus kwargs, para ver qué umbral recibió cada llamada de producción."""
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    llamadas = {n: [] for n in espias}
    parches = []
    for n in espias:
        real = getattr(modulo, n)

        def envoltura(*a, _real=real, _n=n, **kw):
            llamadas[_n].append(kw)
            return _real(*a, **kw)
        parches.append(patch.object(modulo, n, envoltura))
    if modulo is pv:
        bands, geo = arnes.escena_v375(escena)
        parches += [patch.object(pv, "read_viirs_l1b", return_value=bands),
                    patch.object(pv, "read_viirs_geo", return_value=geo)]
        geo_nombre = "VNP03IMG.sintetico.nc"
    else:
        bands, geo = arnes.escena_v750(escena)
        parches += [patch.object(pvm, "read_viirs_mod_l1b", return_value=bands),
                    patch.object(pvm, "read_viirs_mod_geo", return_value=geo)]
        geo_nombre = "VNP03MOD.sintetico.nc"
    for p in parches:
        p.start()
    try:
        rec = modulo.calculate_vrp(Path(nombre), Path(geo_nombre),
                                   volcano_lat=arnes.LAT0, volcano_lon=arnes.LON0,
                                   radius_km=25.0, vent_lat=arnes.LAT0, vent_lon=arnes.LON0,
                                   inner_radius_km=5.0)
    finally:
        for p in parches:
            p.stop()
    return rec, llamadas


# ── 1. perfil y módulo diurno ────────────────────────────────────────────────────────────────

def test_perfil_expone_el_flag_apagado_y_c2_diurno():
    import pipeline.profile as P
    assert P.ENABLE_DAYTIME_VIIRS is False, "el flag nace APAGADO: producción no cambia"
    # Coppola 2016a p. 7, Tabla 1, columna Daytime, ROI1 y ROI2.
    assert P.C2_DNTI_DAY == 15.0 and P.C2_DETI_DAY == 15.0
    assert P.NTI_K1_DAY == -0.6 and P.DNTI_CONTEXTUAL_C1_DAY == 0.02


def test_umbrales_viirs_apagado_devuelve_la_noche_sin_tocarla():
    from pipeline.diurno import umbrales_viirs
    noche = {"nti_k1": object()}
    assert umbrales_viirs(es_dia=True, habilitado=False, noche=noche) is noche
    assert umbrales_viirs(es_dia=False, habilitado=True, noche=noche) is noche
    assert umbrales_viirs(es_dia=False, habilitado=False, noche=noche) is noche


def test_umbrales_viirs_dia_es_la_tabla_1_diurna():
    from pipeline.diurno import umbrales_viirs
    dia = umbrales_viirs(es_dia=True, habilitado=True, noche={})
    assert dia["nti_k1"] == -0.6
    assert dia["c1"] == dia["c1_summit"] == dia["c1_scene"] == 0.02
    for k in ("c2_dnti_summit", "c2_dnti_scene", "c2_deti_summit", "c2_deti_scene"):
        assert dia[k] == 15.0, k
    assert dia["n_sigma_summit"] == dia["n_sigma_scene"] == 15.0
    # El override nocturno de C2 (Di Bella n=12, S46) no es de día: no se arrastra.
    assert dia["viirs_c2_override"] is None
    assert dia["dia"] is True


def test_filtro_nocturno_sigue_al_flag_solo_en_viirs():
    from pipeline.diurno import aplica_filtro_nocturno
    plataformas = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP_750",
                   "VIIRS_NOAA20_750", "VIIRS_NOAA21_750")
    with _flag(False):
        for p in plataformas + ("MODIS_TERRA", "MODIS_AQUA"):
            assert aplica_filtro_nocturno(True, p) is True
            assert aplica_filtro_nocturno(False, p) is False
    with _flag(True):
        for p in plataformas:
            assert aplica_filtro_nocturno(True, p) is False, p
        assert aplica_filtro_nocturno(True, "MODIS_TERRA") is True
        assert aplica_filtro_nocturno(True, "MODIS_AQUA") is True


def test_pasada_es_diurna_usa_la_regla_de_store():
    from pipeline.diurno import pasada_es_diurna
    assert pasada_es_diurna("2026-07-19 18:00", arnes.LAT0, arnes.LON0) is True
    assert pasada_es_diurna("2026-07-19 06:00", arnes.LAT0, arnes.LON0) is False
    assert pasada_es_diurna("unknown", arnes.LAT0, arnes.LON0) is False


# ── 2. store ─────────────────────────────────────────────────────────────────────────────────

def test_store_acepta_viirs_diurno_solo_con_el_flag():
    from pipeline.store import _reject_daytime
    for s in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21_750"):
        assert _reject_daytime(s, 30.0, False) is True
        assert _reject_daytime(s, 30.0, False, enable_daytime_viirs=False) is True
        assert _reject_daytime(s, 30.0, False, enable_daytime_viirs=True) is False
        assert _reject_daytime(s, -10.0, False, enable_daytime_viirs=True) is False
    # El flag VIIRS no abre MODIS: MODIS sigue con su propio flag.
    assert _reject_daytime("MODIS_TERRA", 30.0, False, enable_daytime_viirs=True) is True
    assert _reject_daytime("MODIS_TERRA", 30.0, True, enable_daytime_viirs=False) is False


def test_append_record_lee_el_flag_vivo(tmp_path):
    import pipeline.store as st
    rec = {"datetime_utc": "2026-07-19 18:00", "sensor": "VIIRS_NOAA20", "vrp_mw": 0.0}
    with patch.object(st, "DATA_DIR", tmp_path):
        with _flag(False):
            st.append_record("Prueba", dict(rec), volcano_lat=arnes.LAT0, volcano_lon=arnes.LON0)
        assert not (tmp_path / "Prueba.json").exists() or \
            json.loads((tmp_path / "Prueba.json").read_text())["records"] == []
        with _flag(True):
            st.append_record("Prueba", dict(rec), volcano_lat=arnes.LAT0, volcano_lon=arnes.LON0)
        datos = json.loads((tmp_path / "Prueba.json").read_text(encoding="utf-8"))
        assert [r["datetime_utc"] for r in datos["records"]] == ["2026-07-19 18:00"]


# ── 3. procesadores ──────────────────────────────────────────────────────────────────────────

ESPIAS = ("first_pass_tests_2_and_3", "second_pass_adjacent", "compute_bg_stats")


@pytest.mark.parametrize("cual", ["v375", "v750"])
def test_flag_encendido_lleva_la_tabla_1_diurna_a_los_tests_2_y_3(cual):
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    modulo, escena, dia = ((pv, "nevado_vecino_tibio", DIA_V375) if cual == "v375"
                           else (pvm, "nevado", DIA_V750))
    with _flag(True):
        rec, ll = _correr(modulo, escena, dia, ESPIAS)
    fp = ll["first_pass_tests_2_and_3"]
    assert fp, "el primer pase no corrió: la escena no ejerce el camino"
    kw = fp[0]
    assert kw["c1_dnti_summit"] == kw["c1_deti_summit"] == 0.02
    assert kw["c2_dnti_summit"] == kw["c2_deti_summit"] == 15.0
    assert kw["c1_dnti_scene"] == kw["c1_deti_scene"] == 0.02
    assert kw["c2_dnti_scene"] == kw["c2_deti_scene"] == 15.0
    for kw2 in ll["second_pass_adjacent"]:
        assert kw2["c1_dnti"] == 0.02 and kw2["c2_dnti"] == 15.0 and kw2["c2_deti"] == 15.0
        if kw2.get("c2_dnti_scene") is not None:
            assert kw2["c1_dnti_scene"] == 0.02 and kw2["c2_dnti_scene"] == 15.0
    assert all(kw3["nti_k1_threshold"] == -0.6 for kw3 in ll["compute_bg_stats"])
    assert rec["diag_umbrales_diurnos"] is True


@pytest.mark.parametrize("cual", ["v375", "v750"])
def test_de_noche_el_flag_encendido_no_cambia_nada(cual):
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    modulo, escena, noche = ((pv, "nevado_vecino_tibio", NOCHE_V375) if cual == "v375"
                             else (pvm, "nevado", NOCHE_V750))
    with _flag(False):
        apagado, ll_off = _correr(modulo, escena, noche, ESPIAS)
    with _flag(True):
        encendido, ll_on = _correr(modulo, escena, noche, ESPIAS)
    assert arnes.canonico(encendido) == arnes.canonico(apagado)
    assert arnes.canonico(ll_on) == arnes.canonico(ll_off)
    assert "diag_umbrales_diurnos" not in encendido


@pytest.mark.parametrize("cual", ["v375", "v750"])
def test_flag_apagado_trata_el_dia_igual_que_hoy(cual):
    """Hoy el procesador no distingue día de noche: con el flag apagado, la pasada diurna recibe
    exactamente los umbrales nocturnos y el record es el mismo que el de una pasada nocturna de la
    misma escena (salvo los campos que salen del nombre del gránulo)."""
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    modulo, escena, noche, dia = ((pv, "nevado_vecino_tibio", NOCHE_V375, DIA_V375)
                                  if cual == "v375" else (pvm, "nevado", NOCHE_V750, DIA_V750))
    with _flag(False):
        rec_n, ll_n = _correr(modulo, escena, noche, ESPIAS)
        rec_d, ll_d = _correr(modulo, escena, dia, ESPIAS)
    assert _sin_nombre(rec_d) == _sin_nombre(rec_n)
    assert arnes.canonico(ll_d) == arnes.canonico(ll_n)
    assert "diag_umbrales_diurnos" not in rec_d
    assert ll_d["first_pass_tests_2_and_3"][0]["c1_dnti_summit"] == 0.003


def _plana_con_crater(cual, exceso_k):
    """Cono plano del arnés S142 con UN píxel del cráter `exceso_k` más caliente en el MIR."""
    if cual == "v375":
        bands, geo = arnes.escena_v375("plana")
        bands["I04"][arnes.CENTRO_V375, arnes.CENTRO_V375] += exceso_k
    else:
        bands, geo = arnes.escena_v750("plana")
        bands["M13"][81 // 2, 81 // 2] += exceso_k
    return bands, geo


def _marcados_en_el_dia(cual, exceso_k, flag):
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    bands, geo = _plana_con_crater(cual, exceso_k)
    modulo, nombre = (pv, DIA_V375) if cual == "v375" else (pvm, DIA_V750)
    lect = (("read_viirs_l1b", "read_viirs_geo") if cual == "v375"
            else ("read_viirs_mod_l1b", "read_viirs_mod_geo"))
    with _flag(flag), patch.object(modulo, lect[0], return_value=bands), \
            patch.object(modulo, lect[1], return_value=geo):
        r = modulo.calculate_vrp(Path(nombre), Path("geo.sintetico.nc"),
                                 volcano_lat=arnes.LAT0, volcano_lon=arnes.LON0, radius_km=25.0,
                                 vent_lat=arnes.LAT0, vent_lon=arnes.LON0, inner_radius_km=5.0)
    return r["diag_n_first_pass_pixels"] + r["diag_n_second_pass_recapture"]


@pytest.mark.parametrize("cual", ["v375", "v750"])
def test_el_efecto_de_la_tabla_diurna_se_mide(cual):
    """A116: no basta con que el umbral llegue, hay que ver que mueve algo.

    Medido con un barrido S151 sobre el cono plano del arnés (exceso del cráter de 0,5 a 10 K): un
    cráter 2 K más caliente que su entorno es anómalo con la vara nocturna (C1 0,003, C2 5) y deja
    de serlo con la diurna (C1 0,02, C2 15), en los dos sensores; uno 6 K más caliente pasa con las
    dos. Es lo que el paper busca al subir la vara de día: perder lo débil, que de día no se puede
    separar del Sol, y conservar lo fuerte. Los dos lados son controles: si el débil no marcara con
    el flag apagado, o el fuerte dejara de marcar con el flag encendido, el test no mediría nada.
    """
    # S153: el barrido de 2 K y 6 K se midió con la conectiva `min` de la producción de antes de K; con `max`
    # (adoptada en #848) el cráter de 2 K ya no marca ni de noche. Se mide sobre esa detección, fijada con el
    # ancla congelada (tests/produccion_pre_k.py), porque los brazos del A/B diurno también la congelaron.
    with produccion_pre_k():
        assert _marcados_en_el_dia(cual, 2.0, False) == 1, "control: el cráter débil no marca de noche"
        assert _marcados_en_el_dia(cual, 2.0, True) == 0, "la Tabla 1 diurna no movió nada"
        assert _marcados_en_el_dia(cual, 6.0, False) == 1
        assert _marcados_en_el_dia(cual, 6.0, True) == 1, "la vara diurna mató también lo fuerte"


# S153: la misma medicion sobre la produccion de HOY (K), que es sobre la que se adoptaria la rama diurna.
# Barrido S153 sobre el mismo cono plano: con `max` lo debil sube (V375 deja de marcar de noche bajo 3 K, V750
# bajo 2 K) y la vara diurna deja pasar desde 13 K en V375 y desde 8 K en V750. Los puntos elegidos quedan a
# 2 K o mas de cada borde. Los dos lados vuelven a ser controles (A116).
K_DEBIL_FUERTE = {"v375": (6.0, 20.0), "v750": (4.0, 15.0)}


@pytest.mark.parametrize("cual", ["v375", "v750"])
def test_el_efecto_de_la_tabla_diurna_se_mide_con_k(cual):
    import pipeline.process_viirs as pv
    import pipeline.process_viirs_mod as pvm
    modulo = pv if cual == "v375" else pvm
    assert modulo.ENABLE_TESTS_23_PROSE_BRANCH is True and modulo.ENABLE_TEST1_PATH is False, (
        "el procesador no esta en K: este test mediria otra deteccion")
    debil, fuerte = K_DEBIL_FUERTE[cual]
    assert _marcados_en_el_dia(cual, debil, False) == 1, "control: el crater debil no marca de noche"
    assert _marcados_en_el_dia(cual, debil, True) == 0, "la Tabla 1 diurna no movio nada"
    assert _marcados_en_el_dia(cual, fuerte, False) == 1
    assert _marcados_en_el_dia(cual, fuerte, True) == 1, "la vara diurna mato tambien lo fuerte"


# ── 4. fetch, run_pipeline y la auditoría ────────────────────────────────────────────────────

def test_fetch_no_filtra_viirs_de_noche_con_el_flag(tmp_path):
    import pipeline.fetch as f
    filtradas = []

    def espia(granulos, lat, lon, *a, **kw):
        return []

    def correr():
        filtradas.clear()
        with patch.object(f, "auth"), \
                patch.object(f, "search_granules", side_effect=lambda key, *a, **k: [key]), \
                patch.object(f, "_filter_nighttime_granules",
                             side_effect=lambda g, *a, **k: (filtradas.append(g[0]), [])[1]), \
                patch.object(f, "_match_granules", return_value=[]):
            f.fetch_for_volcano({"name": "Prueba", "lat": arnes.LAT0, "lon": arnes.LON0},
                                datetime(2026, 7, 19), tmp_path, nighttime_only=True)
        return list(filtradas)
    with _flag(False):
        off = correr()
    with _flag(True):
        on = correr()
    assert any("VIIRS" in k for k in off) and any("MODIS" in k for k in off)
    assert on and all("MODIS" in k for k in on), on


def _run_pipeline():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_pipeline_diurno_s151", ROOT / "scripts" / "run_pipeline.py")
    rp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rp)
    return rp


def test_run_pipeline_deja_pasar_el_granulo_viirs_diurno_solo_con_el_flag(tmp_path):
    rp = _run_pipeline()
    l1b = tmp_path / DIA_V375
    geo = tmp_path / DIA_V375.replace("VNP02IMG", "VNP03IMG")
    l1b.write_text("x")
    geo.write_text("x")
    volcan = {"name": "Prueba", "display_name": "Prueba", "lat": arnes.LAT0,
              "lon": arnes.LON0, "radius_km": 25.0}

    def correr():
        llegaron = []
        with patch.object(rp.fetch, "fetch_for_volcano",
                          return_value={"VIIRS_SNPP": [l1b, geo]}), \
                patch.object(rp.process_viirs, "calculate_vrp",
                             side_effect=lambda p, *a, **k: llegaron.append(p.name)):
            rp.process_date(volcan, datetime(2026, 7, 19), nighttime_only=True)
        return llegaron
    with _flag(False):
        assert correr() == []
    with _flag(True):
        assert correr() == [DIA_V375]


def test_la_auditoria_sigue_al_flag():
    from scripts.auto_audit_weekly import es_pasada_diurna_descartada
    dt = datetime(2026, 7, 19, 18, 0)
    with _flag(False):
        assert es_pasada_diurna_descartada("VIIRS375", arnes.LAT0, arnes.LON0, dt) is True
        assert es_pasada_diurna_descartada("VIIRS750", arnes.LAT0, arnes.LON0, dt) is True
    with _flag(True):
        assert es_pasada_diurna_descartada("VIIRS375", arnes.LAT0, arnes.LON0, dt) is False
        assert es_pasada_diurna_descartada("VIIRS750", arnes.LAT0, arnes.LON0, dt) is False
        assert es_pasada_diurna_descartada("MODIS", arnes.LAT0, arnes.LON0, dt) is True
