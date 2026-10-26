# -*- coding: utf-8 -*-
"""S162 V750-A: pruebas del CABLEADO de la vía «código MIROVA» (parche pendiente del sí de Nicolás, A45).

Van con `cableado.patch` (process_viirs_mod.py, store.py y run_pipeline.py). Cuando el parche entre, este archivo se
mueve a tests/ y se suma a tests/test_mirova_v750_codigo_s162.py. Comprueban: con el flag apagado calculate_vrp no toca
el módulo; con el flag encendido devuelve el record de la vía y le pasa el nombre del volcán; un volcán sin grilla corre
K y el record lo dice; run_pipeline pasa el nombre sólo a VIIRS 750; y el almacén no aplica a un record de la vía las
compuertas de la era K que el código de MIROVA no tiene (A118).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import mirova_v750_codigo as MV  # noqa: E402


# ------------------------------------------------------------------------------------------------ 2. flag apagado = hoy
class _K(Exception):
    pass


class _ViaTocada(Exception):
    pass


def test_flag_apagado_no_toca_la_via(monkeypatch):
    """Con el flag apagado, calculate_vrp va directo al lector de K y nunca llama al módulo."""
    from pipeline import process_viirs_mod as PVM
    monkeypatch.setattr(PVM, "ENABLE_V750_CODIGO_MIROVA", False)
    monkeypatch.setattr(PVM, "read_viirs_mod_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    for nombre in ("grilla_del_volcan", "leer_radiancia_l1b", "leer_geo_l1b", "calcular_vrp_granulo"):
        monkeypatch.setattr(MV, nombre, lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    with pytest.raises(_K):
        PVM.calculate_vrp(Path("VJ102MOD.A2026290.0554.021.nc"), Path("geo.nc"), -38.69, -71.73,
                          volcan_nombre="Llaima")


def test_flag_encendido_devuelve_el_record_de_la_via(monkeypatch):
    from pipeline import process_viirs_mod as PVM
    monkeypatch.setattr(PVM, "ENABLE_V750_CODIGO_MIROVA", True)
    monkeypatch.setattr(PVM, "read_viirs_mod_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    llamado = {}
    monkeypatch.setattr(MV, "leer_radiancia_l1b", lambda p: {"M13": 1, "M15": 2})
    monkeypatch.setattr(MV, "leer_geo_l1b", lambda p: ("lat", "lon", {}))

    def falso(rad, lat, lon, ang, nombre, vlat, vlon, inner, sensor):
        llamado.update(nombre=nombre, vlat=vlat, inner=inner, sensor=sensor)
        return {"vrp_mw": 1.5, "via_codigo_mirova": True}
    monkeypatch.setattr(MV, "calcular_vrp_granulo", falso)
    r = PVM.calculate_vrp(Path("VJ102MOD.A2026290.0554.021.nc"), Path("geo.nc"), -38.69, -71.73,
                          vent_lat=-38.692, vent_lon=-71.729, inner_radius_km=5.0, volcan_nombre="Llaima")
    assert r["via_codigo_mirova"] is True and r["granule"] == "VJ102MOD.A2026290.0554.021.nc"
    assert llamado == {"nombre": "Llaima", "vlat": -38.692, "inner": 5.0, "sensor": "VIIRS_NOAA20_750"}


def test_flag_encendido_sin_grilla_sigue_k_y_lo_dice(monkeypatch):
    """Un volcán sin grilla de MIROVA no inventa una: corre K. (Se corta en el lector de K para no necesitar un
    gránulo; la marca la cubre la prueba de texto de abajo.)"""
    from pipeline import process_viirs_mod as PVM
    monkeypatch.setattr(PVM, "ENABLE_V750_CODIGO_MIROVA", True)
    monkeypatch.setattr(PVM, "read_viirs_mod_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    monkeypatch.setattr(MV, "leer_radiancia_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    with pytest.raises(_K):
        PVM.calculate_vrp(Path("VJ102MOD.A2026290.0554.021.nc"), Path("geo.nc"), -33.0, -70.0,
                          volcan_nombre="VolcanSinGrilla")
    src = (REPO / "pipeline/process_viirs_mod.py").read_text(encoding="utf-8")
    assert 'salida["via_codigo_mirova"] = "sin_grilla"' in src


def test_run_pipeline_pasa_el_nombre_solo_a_viirs_750():
    src = (REPO / "scripts/run_pipeline.py").read_text(encoding="utf-8")
    assert src.count('volcan_nombre=volcano["name"]') == 1
    i = src.index("process_viirs_mod.calculate_vrp(")
    assert src.index('volcan_nombre=volcano["name"]') > i
    assert src.index('volcan_nombre=volcano["name"]') < src.index("store.append_record", i)


# ------------------------------------------------------------------------------------------------ el almacén
def _record_via(marca):
    r = {"datetime_utc": "2026-10-10 05:54", "sensor": "VIIRS_NOAA20_750", "vrp_mw": 4.0, "vrp_vent_mw": 0.0,
         "hotspot_lat": -38.5, "hotspot_lon": -71.7, "hotspot_dist_km": 30.0,
         "primary_cluster": {"vrp_mw": 4.0, "n_pixels": 20, "centroid_lat": -38.5, "centroid_lon": -71.7,
                             "centroid_dist_km": 30.0, "single_pixel_mode": False},
         "anomaly_pixels": [{"lat": -38.5, "lon": -71.7, "dist_km": 30.0, "bt_k": 300.0}],
         "distance_class": "far", "product_version": "standard"}
    if marca:
        r["via_codigo_mirova"] = True
    return r


@pytest.mark.parametrize("marca,vrp_esperado", [(True, 4.0), (False, 0.0)])
def test_almacen_no_aplica_las_compuertas_de_k_a_la_via(tmp_path, monkeypatch, marca, vrp_esperado):
    """Geocerca por hotspot_dist_km y tope de píxeles por cúmulo: el record de K las sufre, el de la vía no."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_via(marca)
    store.append_record("TestVolcano", r, max_hotspot_dist_km=25.0, max_cluster_pixels=12,
                        enable_pixel_level_distance_filter=True, inner_radius_km=5.0)
    assert r["vrp_mw"] == vrp_esperado
