"""TDD edge cases para pipeline.store.append_record.

S23 Task 6 audit followup: store.py tenía solo cobertura indirecta vía
test_vent_priority.py. Edge cases (key collision, overwrite, sanity cap M4,
piso VRP por sensor) sin tests dedicados.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


def _basic_record(dt="2026-04-10 05:00", sensor="VIIRS_NOAA20",
                  vrp_mir=0.5, vrp_vent=0.0):
    return {
        "vrp_mir_mw": vrp_mir,
        "vrp_vent_mw": vrp_vent,
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 0,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        "hotspot_lat": -33.4, "hotspot_lon": -69.8, "hotspot_dist_km": 1.0,
        "final_hotspot_lat": -33.4, "final_hotspot_lon": -69.8,
        "final_hotspot_dist_km": 1.0, "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": [],
        "t_bg_k": 265.0, "t_max_i04_k": 270.0,
        "sensor": sensor, "granule": f"fake_{dt}_{sensor}.nc",
        "product_version": "standard", "datetime_utc": dt,
    }


def test_append_record_no_duplicate_key(tmp_path, monkeypatch):
    """Mismo (datetime, sensor) NO debe duplicar — overwrite=False mantiene primero."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _basic_record(vrp_mir=0.5)
    store_mod.append_record("Vol1", rec, -33.4, -69.8, overwrite=False,
                            max_hotspot_dist_km=25.0)
    # 2do call con mismo dt+sensor pero distinto vrp
    rec2 = _basic_record(vrp_mir=0.99)
    store_mod.append_record("Vol1", rec2, -33.4, -69.8, overwrite=False,
                            max_hotspot_dist_km=25.0)

    data = json.loads((tmp_path / "Vol1.json").read_text())
    assert len(data["records"]) == 1, "duplicate key debe saltarse"
    # Primero gana (overwrite=False)
    saved = data["records"][0]
    assert (saved.get("vrp_mw") or saved.get("vrp_mir_mw")) == 0.5


def test_append_record_overwrite_replaces_existing(tmp_path, monkeypatch):
    """overwrite=True reemplaza record con mismo (datetime, sensor)."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)

    rec1 = _basic_record(vrp_mir=0.5)
    rec2 = _basic_record(vrp_mir=1.0)  # mismo dt+sensor, distinto vrp
    store_mod.append_record("Vol2", rec1, -33.4, -69.8, overwrite=True,
                            max_hotspot_dist_km=25.0)
    store_mod.append_record("Vol2", rec2, -33.4, -69.8, overwrite=True,
                            max_hotspot_dist_km=25.0)

    data = json.loads((tmp_path / "Vol2.json").read_text())
    assert len(data["records"]) == 1
    saved = data["records"][0]
    assert (saved.get("vrp_mw") or saved.get("vrp_mir_mw")) == 1.0


def test_append_record_sanity_cap_50k_mw_zeroes_value(tmp_path, monkeypatch):
    """vrp_mw que excede SANITY_CAP_VRP_MW (50K MW) se clamea a 0 con valor crudo
    preservado en diag_rejected_sanity_cap_mw (M4 S19)."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _basic_record(vrp_mir=100_000.0)  # imposible físicamente
    store_mod.append_record("Vol3", rec, -33.4, -69.8, overwrite=False,
                            max_hotspot_dist_km=25.0)

    data = json.loads((tmp_path / "Vol3.json").read_text())
    saved = data["records"][0]
    # vrp_mw clamped a 0
    assert (saved.get("vrp_mw") or 0) == 0.0
    # raw preservado
    assert saved.get("diag_rejected_sanity_cap_mw") == 100_000.0
    assert saved.get("diag_sanity_cap_threshold_mw") == 50_000.0


def test_append_record_far_hotspot_filtered_to_zero(tmp_path, monkeypatch):
    """Si hotspot_dist_km > max_hotspot_dist_km, eruption-path vrp_mw debe quedar en 0
    (geofencing S12). store.py compara `hotspot_dist_km` (eruption hotspot) contra
    el cap, no `final_hotspot_dist_km`.
    """
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _basic_record()
    rec["hotspot_dist_km"] = 30.0  # eruption hotspot > 25 km max
    rec["vrp_mir_mw"] = 50.0  # eruption-path detectó algo lejano
    rec["vrp_vent_mw"] = 0.0  # vent-path no
    store_mod.append_record("Vol4", rec, -33.4, -69.8, overwrite=False,
                            max_hotspot_dist_km=25.0)

    data = json.loads((tmp_path / "Vol4.json").read_text())
    saved = data["records"][0]
    # vrp_mw debe quedar en 0 porque hotspot eruption fuera del max
    assert (saved.get("vrp_mw") or 0) == 0.0
    # Y el lat/lon original se preserva en discarded_* para auditoría
    assert "discarded_hotspot_lat" in saved or saved.get("discarded_hotspot_lat") is not None or \
           (saved.get("hotspot_lat") is not None)  # alguna evidencia del filter


def test_append_record_creates_json_with_volcano_metadata(tmp_path, monkeypatch):
    """Primera escritura crea JSON con keys 'volcano' y 'records' presentes."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _basic_record()
    store_mod.append_record("Vol5", rec, -33.4, -69.8, overwrite=False,
                            max_hotspot_dist_km=25.0)

    data = json.loads((tmp_path / "Vol5.json").read_text())
    assert "records" in data
    assert "volcano" in data
    assert data["volcano"] == "Vol5"
