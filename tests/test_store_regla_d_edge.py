"""Edge cases para Regla D vent-priority (S20). Garantizar que NO rompe
KeyError si los campos vent_hotspot_* faltan inesperadamente.

S23 Task 1 audit followup: detectado en audit S22 que store.py:150-156
asumía que `record["vent_hotspot_dist_km"]` existía cuando vrp_vent>0.
Si el campo está ausente del dict (no None, sino key missing), el código
lanza KeyError silencioso en producción.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import pipeline.store as store_mod


def _record_vrp_vent_pos_no_vent_hotspot():
    """Record con vrp_vent>0 pero SIN keys vent_hotspot_*.

    Edge case: bug aguas arriba podría retornar vrp_vent>0 pero olvidarse
    de poblar las coords. Antes del fix S23: KeyError.
    """
    return {
        "vrp_mir_mw": 0.5,
        "vrp_mw": 0.5,  # alias unified
        "vrp_vent_mw": 0.15,  # >0 dispara Regla D
        # NOTA: NO hay vent_hotspot_lat/lon/dist_km en el dict.
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 1,
        "hotspot_lat": -33.4,
        "hotspot_lon": -69.8,
        "hotspot_dist_km": 1.5,
        "final_hotspot_lat": -33.4,
        "final_hotspot_lon": -69.8,
        "final_hotspot_dist_km": 1.5,
        "final_hotspot_source": "eruption",
        "distance_class": "summit",  # vino de eruption-path dentro inner
        "anomaly_pixels": [],
        "t_bg_k": 265.0,
        "t_max_i04_k": 270.0,
        "sensor": "VIIRS_NOAA20",
        "granule": "VJ102IMG.A2026100.0500.021.fake.nc",
        "product_version": "standard",
        "datetime_utc": "2026-04-10 05:00",
    }


def test_regla_d_no_keyerror_when_vent_hotspot_dist_missing(tmp_path,
                                                             monkeypatch):
    """Si vrp_vent>0 pero vent_hotspot_dist_km key está ausente, NO debe crashear.

    Antes del fix: line 155 hace `record["vent_hotspot_dist_km"]` directo
    si lat/lon están presentes pero dist falta → KeyError.
    """
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)

    rec = _record_vrp_vent_pos_no_vent_hotspot()
    # Caso 1: lat/lon ausentes también — debería no crashear, distance_class sin promover
    store_mod.append_record(
        volcano_name="TestNoCrash",
        record=rec,
        volcano_lat=-33.4, volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
    )

    # Caso 2: lat/lon presentes pero dist_km ausente — bug latente original
    rec2 = _record_vrp_vent_pos_no_vent_hotspot()
    rec2["vent_hotspot_lat"] = -33.4
    rec2["vent_hotspot_lon"] = -69.8
    # vent_hotspot_dist_km key SIGUE AUSENTE
    rec2["datetime_utc"] = "2026-04-11 05:00"  # otro dt para no chocar key
    store_mod.append_record(
        volcano_name="TestNoCrash",
        record=rec2,
        volcano_lat=-33.4, volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
    )

    # Si llegamos aquí sin excepción, el fix funcionó.
    out_file = tmp_path / "TestNoCrash.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data["records"]) == 2


def test_regla_d_promotes_summit_even_without_coords_legacy(tmp_path,
                                                            monkeypatch):
    """Comportamiento deliberado S20 (test_legacy_vent_without_coords_*):
    vrp_vent>0 → distance_class='summit' aunque vent_hotspot_* sean None/missing.

    Razón S20: "podemos etiquetarlo correctamente como summit aunque no tengamos
    coords" (test_vent_priority.py:188-190).

    El fix S23 mantiene este comportamiento; solo se asegura de NO lanzar
    KeyError cuando alguna key del vent_hotspot_* está ausente del dict.
    final_hotspot_* NO se reescribe si vent_hotspot_* incompletos
    (cuando aplica, queda lo que vino del eruption-path).
    """
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)

    rec = _record_vrp_vent_pos_no_vent_hotspot()
    rec["distance_class"] = "far"
    rec["final_hotspot_dist_km"] = 15.0
    rec["final_hotspot_source"] = "eruption"
    rec["final_hotspot_lat"] = -33.42
    rec["final_hotspot_lon"] = -69.85
    # vrp_vent>0 pero SIN vent_hotspot_*. S20 dice: promover a summit igual.
    store_mod.append_record(
        volcano_name="TestPromoteLegacy",
        record=rec,
        volcano_lat=-33.4, volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
    )

    data = json.loads((tmp_path / "TestPromoteLegacy.json").read_text())
    saved = data["records"][0]
    # Comportamiento legacy: distance_class debe promoverse a summit.
    assert saved["distance_class"] == "summit", (
        f"S20 Regla D: vrp_vent>0 debe promover summit aunque coords missing. "
        f"distance_class={saved['distance_class']}"
    )
    # Pero final_hotspot_* NO se reescribe (no había vent coords). Queda
    # lo del eruption-path original.
    assert saved["final_hotspot_source"] == "eruption", (
        "Sin vent_hotspot_* completo, final_hotspot_source NO debe reescribirse a 'vent'"
    )
    assert saved["final_hotspot_dist_km"] == 15.0


def test_regla_d_does_promote_when_vent_hotspot_complete(tmp_path,
                                                         monkeypatch):
    """Sanity check: si vent_hotspot_* completos, Regla D SÍ promueve correctamente."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)

    rec = _record_vrp_vent_pos_no_vent_hotspot()
    rec["distance_class"] = "far"
    rec["final_hotspot_dist_km"] = 15.0
    rec["final_hotspot_source"] = "eruption"
    rec["vent_hotspot_lat"] = -33.39
    rec["vent_hotspot_lon"] = -69.83
    rec["vent_hotspot_dist_km"] = 2.5

    store_mod.append_record(
        volcano_name="TestPromote",
        record=rec,
        volcano_lat=-33.4, volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
    )

    data = json.loads((tmp_path / "TestPromote.json").read_text())
    saved = data["records"][0]
    assert saved["distance_class"] == "summit"
    assert saved["final_hotspot_source"] == "vent"
    assert saved["final_hotspot_dist_km"] == 2.5
