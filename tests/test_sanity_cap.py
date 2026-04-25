"""tests/test_sanity_cap.py — sanity cap físico en store.py (M4 S19 2026-04-24).

Bug que motivó el fix: granule MODIS Terra 2026-04-23 01:50 Lastarria devolvió
357 pixels con BT=566 K (292°C) — flag DN no enmascarado decodificado como
temperatura real. Generó vrp=1,529,426 MW en el dashboard, físicamente imposible.

Cap calibrado a 50,000 MW (M4 S19), 1.3x el P99.99 del archivo OSF v2.5
(615k filas globales 2000-2025) y 0.71x el récord histórico (Etna ~70 GW).
Cualquier record con vrp_mw > 50,000 MW es estadística y físicamente
inverosímil — bandera de bug.

Comportamiento esperado:
  - vrp_mw ≤ 50,000 → record pasa intacto.
  - vrp_mw > 50,000 → record se clampea (vrp_mw = 0) y se preserva el valor
    crudo en `diag_rejected_sanity_cap_mw` para auditoría.
"""

import pytest
from pipeline import store


def _base_record(vrp_mw):
    return {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-24 05:00",
        "vrp_mir_mw": vrp_mw,
        "vrp_vent_mw": 0.0,
        "vrp_tir_mw": 0.0,
        "hotspot_dist_km": 1.5,
        "anomaly_pixels": [],
        "final_hotspot_dist_km": 1.5,
    }


def test_normal_record_passes(tmp_path, monkeypatch):
    """Record con vrp normal (50 MW) debe pasar sin tocarlo."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)  # sin floor para aislar el cap
    rec = _base_record(50.0)
    store.append_record("TestVolcano", rec, volcano_lat=-33.0, volcano_lon=-70.0,
                        max_hotspot_dist_km=25)
    stored = store._load("TestVolcano")
    assert len(stored["records"]) == 1
    r = stored["records"][0]
    assert r["vrp_mw"] == 50.0
    assert "diag_rejected_sanity_cap_mw" not in r


def test_high_but_plausible_record_passes(tmp_path, monkeypatch):
    """Record con vrp 30,000 MW (plausible, Etna paroxismo) debe pasar."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)
    rec = _base_record(30000.0)
    store.append_record("TestVolcano", rec, volcano_lat=-33.0, volcano_lon=-70.0,
                        max_hotspot_dist_km=25)
    r = store._load("TestVolcano")["records"][0]
    assert r["vrp_mw"] == 30000.0
    assert "diag_rejected_sanity_cap_mw" not in r


def test_at_cap_boundary_passes(tmp_path, monkeypatch):
    """Record con vrp = 50,000 MW exactamente debe pasar (≤ cap, no <)."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)
    rec = _base_record(50000.0)
    store.append_record("TestVolcano", rec, volcano_lat=-33.0, volcano_lon=-70.0,
                        max_hotspot_dist_km=25)
    r = store._load("TestVolcano")["records"][0]
    assert r["vrp_mw"] == 50000.0
    assert "diag_rejected_sanity_cap_mw" not in r


def test_above_cap_clamped(tmp_path, monkeypatch):
    """Record con vrp > 50,000 MW debe clamparse a 0 + preservar crudo en diag."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)
    rec = _base_record(80000.0)
    store.append_record("TestVolcano", rec, volcano_lat=-33.0, volcano_lon=-70.0,
                        max_hotspot_dist_km=25)
    r = store._load("TestVolcano")["records"][0]
    assert r["vrp_mw"] == 0.0
    assert r.get("diag_rejected_sanity_cap_mw") == 80000.0
    assert r.get("diag_sanity_cap_threshold_mw") == 50000.0


def test_lastarria_bug_caught(tmp_path, monkeypatch):
    """El record histórico FP Lastarria 1.5M MW (caso real S18) debe ser clampeado."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)
    rec = _base_record(1529426.278)  # mismo valor del granule MODIS dañado
    rec["sensor"] = "MODIS_TERRA"
    store.append_record("Lastarria", rec, volcano_lat=-25.168, volcano_lon=-68.507,
                        max_hotspot_dist_km=25)
    r = store._load("Lastarria")["records"][0]
    assert r["vrp_mw"] == 0.0, "FP Lastarria 1.5M MW NO se clampeó"
    assert r.get("diag_rejected_sanity_cap_mw") == 1529426.278
