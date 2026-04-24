"""TDD S18 Bloque 1 — NOAA-21 (JPSS-2) en fetch.py y process_viirs*.

Hipótesis H10 (docs/HYPOTHESIS_LOG.md): MIROVA procesa VIIRS NOAA-21 (short_name
VJ202IMG / VJ202MOD) desde enero 2023. Nuestro pipeline no lo enumera.
Evidencia CMR (S17 2026-04-23): earthaccess retorna granules VJ202IMG v2.1 para
Tupungatito 2026-04-10 a las 04:48 y 06:24 UTC — exactamente las horas MIROVA
que nos faltaban.

Respaldo documental NOAA-21: JPSS VIIRS Radiometric ATBD Rev C
(documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf). No hay paper MIROVA
que mencione NOAA-21 — su adopción es operacional.

Estos tests fallan RED hasta que el pipeline soporte los 4 productos nuevos:
    VJ202IMG  (L1B I-band 375m)   + VJ203IMG (geo)
    VJ202MOD  (L1B M-band 750m)   + VJ203MOD (geo)
cada uno con su variante _NRT (LANCE fallback ~3h latencia).
"""

from pathlib import Path
from datetime import datetime

import pytest

from pipeline import fetch


# ---------------------------------------------------------------------------
# 1. PRODUCTS dict contiene entradas NOAA-21
# ---------------------------------------------------------------------------

def test_products_has_noaa21_img_l1b():
    """VIIRS NOAA-21 I-band L1B: short_name VJ202IMG v2.1 + NRT fallback."""
    assert "VIIRS_NOAA21_L1B" in fetch.PRODUCTS, (
        "fetch.PRODUCTS must have VIIRS_NOAA21_L1B entry (VJ202IMG)"
    )
    entry = fetch.PRODUCTS["VIIRS_NOAA21_L1B"]
    assert entry["short_name"] == "VJ202IMG"
    # versions list con 2.1 principal (misma convención que NOAA-20)
    versions = entry.get("versions") or [entry.get("version")]
    assert "2.1" in versions, f"expected '2.1' in {versions}"
    assert "nrt" in entry
    nrt = entry["nrt"]
    assert nrt["short_name"] == "VJ202IMG_NRT"
    nrt_versions = nrt.get("versions") or [nrt.get("version")]
    assert "2.1" in nrt_versions


def test_products_has_noaa21_img_geo():
    """VIIRS NOAA-21 I-band geolocation: VJ203IMG v2.1."""
    assert "VIIRS_NOAA21_GEO" in fetch.PRODUCTS
    entry = fetch.PRODUCTS["VIIRS_NOAA21_GEO"]
    assert entry["short_name"] == "VJ203IMG"
    versions = entry.get("versions") or [entry.get("version")]
    assert "2.1" in versions
    nrt = entry["nrt"]
    assert nrt["short_name"] == "VJ203IMG_NRT"


def test_products_has_noaa21_mod_l1b():
    """VIIRS NOAA-21 M-band 750m L1B: VJ202MOD v2.1."""
    assert "VIIRS_NOAA21_MOD_L1B" in fetch.PRODUCTS
    entry = fetch.PRODUCTS["VIIRS_NOAA21_MOD_L1B"]
    assert entry["short_name"] == "VJ202MOD"
    versions = entry.get("versions") or [entry.get("version")]
    assert "2.1" in versions
    nrt = entry["nrt"]
    assert nrt["short_name"] == "VJ202MOD_NRT"


def test_products_has_noaa21_mod_geo():
    """VIIRS NOAA-21 M-band geolocation: VJ203MOD v2.1."""
    assert "VIIRS_NOAA21_MOD_GEO" in fetch.PRODUCTS
    entry = fetch.PRODUCTS["VIIRS_NOAA21_MOD_GEO"]
    assert entry["short_name"] == "VJ203MOD"
    versions = entry.get("versions") or [entry.get("version")]
    assert "2.1" in versions
    nrt = entry["nrt"]
    assert nrt["short_name"] == "VJ203MOD_NRT"


# ---------------------------------------------------------------------------
# 2. fetch_for_volcano incluye platforms VIIRS_NOAA21 y VIIRS_NOAA21_750
# ---------------------------------------------------------------------------

class _SearchSpy:
    """Captura llamadas a search_granules y devuelve [] (sin red)."""

    def __init__(self):
        self.product_keys_called = []

    def __call__(self, product_key, lat, lon, radius_km, date):
        self.product_keys_called.append(product_key)
        return []


def test_fetch_for_volcano_queries_noaa21_img_product(monkeypatch, tmp_path):
    """fetch_for_volcano(..., sensors=['VIIRS']) debe enumerar VIIRS_NOAA21_L1B."""
    monkeypatch.setattr(fetch, "auth", lambda: None)
    spy = _SearchSpy()
    monkeypatch.setattr(fetch, "search_granules", spy)

    volcano = {"name": "TestVolcano", "lat": -33.0, "lon": -70.0, "radius_km": 25}
    fetch.fetch_for_volcano(
        volcano, datetime(2026, 4, 10), tmp_path, sensors=["VIIRS"]
    )

    assert "VIIRS_NOAA21_L1B" in spy.product_keys_called, (
        f"VIIRS_NOAA21_L1B never queried. Called: {spy.product_keys_called}"
    )


def test_fetch_for_volcano_queries_noaa21_mod_product(monkeypatch, tmp_path):
    """fetch_for_volcano(..., sensors=['VIIRS']) debe enumerar VIIRS_NOAA21_MOD_L1B."""
    monkeypatch.setattr(fetch, "auth", lambda: None)
    spy = _SearchSpy()
    monkeypatch.setattr(fetch, "search_granules", spy)

    volcano = {"name": "TestVolcano", "lat": -33.0, "lon": -70.0, "radius_km": 25}
    fetch.fetch_for_volcano(
        volcano, datetime(2026, 4, 10), tmp_path, sensors=["VIIRS"]
    )

    assert "VIIRS_NOAA21_MOD_L1B" in spy.product_keys_called, (
        f"VIIRS_NOAA21_MOD_L1B never queried. Called: {spy.product_keys_called}"
    )


def test_fetch_for_volcano_preserves_snpp_and_noaa20(monkeypatch, tmp_path):
    """Agregar NOAA-21 no debe reemplazar SNPP/NOAA-20; los 3 coexisten."""
    monkeypatch.setattr(fetch, "auth", lambda: None)
    spy = _SearchSpy()
    monkeypatch.setattr(fetch, "search_granules", spy)

    volcano = {"name": "TestVolcano", "lat": -33.0, "lon": -70.0, "radius_km": 25}
    fetch.fetch_for_volcano(
        volcano, datetime(2026, 4, 10), tmp_path, sensors=["VIIRS"]
    )

    for expected in (
        "VIIRS_SNPP_L1B", "VIIRS_NOAA20_L1B", "VIIRS_NOAA21_L1B",
        "VIIRS_SNPP_MOD_L1B", "VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA21_MOD_L1B",
    ):
        assert expected in spy.product_keys_called, (
            f"{expected} missing. Called: {spy.product_keys_called}"
        )


# ---------------------------------------------------------------------------
# 3. Sensor label: VJ2* filename → VIIRS_NOAA21 (no VIIRS_NOAA20)
# ---------------------------------------------------------------------------

def test_sensor_label_vj2_img_is_noaa21():
    """VJ202IMG filename debe mapear a sensor='VIIRS_NOAA21'.

    Bug pre-fix: process_viirs.py:555 asumía startswith('VNP')->SNPP else NOAA20.
    Eso etiqueta VJ202IMG como NOAA20 incorrectamente (el CSV MIROVA distingue
    NOAA-20 y NOAA-21 por short_name; conflatearlos rompe la tabla).
    """
    from pipeline.process_viirs import _sensor_label_from_filename
    assert _sensor_label_from_filename("VJ202IMG.A2026100.0506.021.nc") == "VIIRS_NOAA21"


def test_sensor_label_vj1_img_is_noaa20():
    """Regresión: VJ102IMG sigue siendo VIIRS_NOAA20."""
    from pipeline.process_viirs import _sensor_label_from_filename
    assert _sensor_label_from_filename("VJ102IMG.A2026100.0506.021.nc") == "VIIRS_NOAA20"


def test_sensor_label_vnp_img_is_snpp():
    """Regresión: VNP02IMG sigue siendo VIIRS_SNPP."""
    from pipeline.process_viirs import _sensor_label_from_filename
    assert _sensor_label_from_filename("VNP02IMG.A2026100.0506.002.nc") == "VIIRS_SNPP"


def test_sensor_label_vj2_nrt_is_noaa21():
    """VJ202IMG_NRT mapea a VIIRS_NOAA21 (el sufijo NRT no cambia el sensor)."""
    from pipeline.process_viirs import _sensor_label_from_filename
    assert _sensor_label_from_filename("VJ202IMG_NRT.A2026100.0506.021.nc") == "VIIRS_NOAA21"


def test_sensor_label_mod_vj2_is_noaa21_750():
    """VJ202MOD en process_viirs_mod debe mapear a VIIRS_NOAA21_750."""
    from pipeline.process_viirs_mod import _sensor_label_from_filename
    assert _sensor_label_from_filename("VJ202MOD.A2026100.0506.021.nc") == "VIIRS_NOAA21_750"


def test_sensor_label_mod_vj1_is_noaa20_750():
    """Regresión: VJ102MOD sigue siendo VIIRS_NOAA20_750."""
    from pipeline.process_viirs_mod import _sensor_label_from_filename
    assert _sensor_label_from_filename("VJ102MOD.A2026100.0506.021.nc") == "VIIRS_NOAA20_750"


def test_sensor_label_mod_vnp_is_snpp_750():
    """Regresión: VNP02MOD sigue siendo VIIRS_SNPP_750."""
    from pipeline.process_viirs_mod import _sensor_label_from_filename
    assert _sensor_label_from_filename("VNP02MOD.A2026100.0506.002.nc") == "VIIRS_SNPP_750"


# ---------------------------------------------------------------------------
# 4. store.py aplica piso VRP 375m a VIIRS_NOAA21 (mismo trato que SNPP/NOAA-20)
# ---------------------------------------------------------------------------

def test_store_applies_viirs375_floor_to_noaa21(tmp_path, monkeypatch):
    """Un record VIIRS_NOAA21 con vrp_mw debajo del piso 375m debe ser clampeado a 0.

    Pre-fix: store.py:134 chequeaba `sensor in ("VIIRS_SNPP", "VIIRS_NOAA20")`
    pero no incluía VIIRS_NOAA21 — los records NOAA-21 caían al else (floor=0),
    rompiendo paridad MIROVA en el piso de detección.
    """
    from pipeline import store

    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.15)

    # vrp debajo del piso → debe quedar 0.0 (y diag_vrp_raw_mw preservado)
    record = {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-10 05:30",
        "vrp_mir_mw": 0.10,
        "vrp_vent_mw": 0.0,
        "vrp_tir_mw": 0.0,
        "hotspot_dist_km": 1.5,
        "anomaly_pixels": [],
        "final_hotspot_dist_km": 1.5,
    }
    # volcano at -66° lat → 05:30 UTC es noche (solar elev < 0 en abril)
    store.append_record(
        "TestVolcanoNoaa21", record,
        volcano_lat=-66.0, volcano_lon=-70.0,
        max_hotspot_dist_km=25,
    )

    stored = store._load("TestVolcanoNoaa21")
    assert len(stored["records"]) == 1
    r = stored["records"][0]
    assert r["vrp_mw"] == 0.0, (
        f"NOAA-21 record debajo del piso 375m debía clampearse a 0, quedó {r['vrp_mw']}"
    )
    assert r.get("diag_vrp_raw_mw") == 0.10
    assert r.get("diag_vrp_floor_mw") == 0.15
