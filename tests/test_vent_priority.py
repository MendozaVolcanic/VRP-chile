"""tests/test_vent_priority.py — Regla D S20 (vent-priority).

Hallazgo S20 forense H17: 8/15 FN Tupungatito son "T3" (vent-path SÍ detectó
señal del cráter, vrp_vent_mw>0, pero el record completo quedó clasificado
distance_class="far" porque hay otro pixel lejano más caliente). Esto rompe
la lógica MIROVA donde el vent-path implica anomalía real del cráter.

Regla D (espíritu S9): si vrp_vent_mw > 0, el record debe clasificarse como
summit, con final_hotspot apuntando al vent. Independiente de qué pixel far
más caliente exista.

Validación contrafactual S20 (2026-04-25):
  - Recall agregado actual (3 volcanes, 30 días): 0.25
  - Recall con regla D:                            0.69 (+0.44)
  - Chaitén con D: 1.00 (iguala S9 0.93+)
  - Tupungatito con D: 0.57 (sigue lejos de S9 0.98 — los 9 T4 son otro fix)
"""

import pytest
from pipeline import store


def _far_with_vent_record():
    """Caso T3: record con detección far + vent-path activa.

    Antes de D: distance_class='far' (porque hotspot far más caliente).
    Después de D: distance_class='summit', final_hotspot apunta al vent.
    """
    return {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-15 05:42",
        "vrp_mir_mw": 1.5,            # eruption-path detectó pixel lejano
        "vrp_vent_mw": 0.092,         # vent-path detectó cráter sub-pixel
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 1,
        # Hotspot principal apunta a un pixel far (regla actual lo prioriza por VRP)
        "hotspot_lat": -33.250,
        "hotspot_lon": -69.620,
        "hotspot_dist_km": 22.7,
        # Vent hotspot apunta al cráter (vent-path coord real)
        "vent_hotspot_lat": -33.389,
        "vent_hotspot_lon": -69.826,
        "vent_hotspot_dist_km": 0.5,
        # Schema unificado original (será reescrito por la regla D)
        "final_hotspot_lat": -33.250,
        "final_hotspot_lon": -69.620,
        "final_hotspot_dist_km": 22.7,
        "final_hotspot_source": "eruption",
        "distance_class": "far",
        "anomaly_pixels": [],
    }


def _far_without_vent_record():
    """Caso T4: record con detección far + sin vent-path.

    Regla D NO aplica (no hay vrp_vent>0). El record sigue como far.
    """
    return {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-14 05:12",
        "vrp_mir_mw": 0.5,
        "vrp_vent_mw": 0.0,           # vent-path NO disparó
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 0,
        "hotspot_lat": -33.250,
        "hotspot_lon": -69.620,
        "hotspot_dist_km": 26.5,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        "final_hotspot_lat": -33.250,
        "final_hotspot_lon": -69.620,
        "final_hotspot_dist_km": 26.5,
        "final_hotspot_source": "eruption",
        "distance_class": "far",
        "anomaly_pixels": [],
    }


def _legacy_far_with_vent_no_coords():
    """Caso legacy: vent_path antiguo sin vent_hotspot_lat/lon (pre-S12 fix).

    vrp_vent>0 pero coords del vent no están en el record. La regla D debe:
      - distance_class='summit' (sí podemos clasificarlo correctamente).
      - final_hotspot_lat/lon: caer al volcano center (no romper el JSON).
    """
    return {
        "sensor": "VIIRS_SNPP",
        "datetime_utc": "2026-04-13 05:30",
        "vrp_mir_mw": 0.0,
        "vrp_vent_mw": 0.176,         # vent SÍ pero sin coords
        "n_anomalous_pixels": 0,
        "n_vent_pixels": 1,
        "hotspot_lat": None,
        "hotspot_lon": None,
        "hotspot_dist_km": None,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        "final_hotspot_lat": None,
        "final_hotspot_lon": None,
        "final_hotspot_dist_km": None,
        "final_hotspot_source": "vent",
        "distance_class": None,        # legacy sin clase
        "anomaly_pixels": [],
    }


def test_far_with_vent_reclassified_as_summit(tmp_path, monkeypatch):
    """T3: record class=far + vrp_vent>0 → debe quedar class=summit con vent como hotspot."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _far_with_vent_record()
    store.append_record("TestVolcano", rec,
                        volcano_lat=-33.4, volcano_lon=-69.8,
                        max_hotspot_dist_km=25)

    stored = store._load("TestVolcano")["records"][0]
    assert stored["distance_class"] == "summit", (
        f"T3: record con vrp_vent>0 debe clasificarse summit, quedó '{stored['distance_class']}'"
    )
    assert stored["final_hotspot_source"] == "vent", (
        "final_hotspot_source debe apuntar al vent cuando regla D aplica"
    )
    assert stored["final_hotspot_lat"] == -33.389, (
        f"final_hotspot_lat debe ser vent_hotspot_lat (-33.389), quedó {stored['final_hotspot_lat']}"
    )
    assert stored["final_hotspot_lon"] == -69.826
    assert stored["final_hotspot_dist_km"] == 0.5


def test_far_without_vent_stays_far(tmp_path, monkeypatch):
    """T4: record class=far + sin vrp_vent → no toca, sigue far."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _far_without_vent_record()
    store.append_record("TestVolcano", rec,
                        volcano_lat=-33.4, volcano_lon=-69.8,
                        max_hotspot_dist_km=25)

    stored = store._load("TestVolcano")["records"][0]
    assert stored["distance_class"] == "far", (
        "T4: record sin vrp_vent debe quedar far"
    )
    # final_hotspot NO debe haber cambiado
    assert stored["final_hotspot_dist_km"] == 26.5


def test_summit_already_correct_not_disturbed(tmp_path, monkeypatch):
    """Record ya class=summit con vent-path: no debe modificarse innecesariamente."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-12 05:48",
        "vrp_mir_mw": 0.5,
        "vrp_vent_mw": 0.092,
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 1,
        "hotspot_lat": -33.389,
        "hotspot_lon": -69.826,
        "hotspot_dist_km": 0.4,
        "vent_hotspot_lat": -33.389,
        "vent_hotspot_lon": -69.826,
        "vent_hotspot_dist_km": 0.4,
        "final_hotspot_lat": -33.389,
        "final_hotspot_lon": -69.826,
        "final_hotspot_dist_km": 0.4,
        "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": [],
    }
    store.append_record("TestVolcano", rec,
                        volcano_lat=-33.4, volcano_lon=-69.8,
                        max_hotspot_dist_km=25)

    stored = store._load("TestVolcano")["records"][0]
    assert stored["distance_class"] == "summit"
    assert stored["final_hotspot_dist_km"] == 0.4


def test_legacy_vent_without_coords_classified_summit(tmp_path, monkeypatch):
    """Legacy: vrp_vent>0 sin vent_hotspot_lat/lon → distance_class='summit'.

    No podemos rellenar coords del vent (no las tenemos), pero al menos
    podemos etiquetarlo correctamente como summit.
    """
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = _legacy_far_with_vent_no_coords()
    store.append_record("TestVolcano", rec,
                        volcano_lat=-33.4, volcano_lon=-69.8,
                        max_hotspot_dist_km=25)

    stored = store._load("TestVolcano")["records"][0]
    assert stored["distance_class"] == "summit", (
        "Legacy con vrp_vent>0 debe quedar summit aunque no tenga coords"
    )


def test_no_vent_no_eruption_no_change(tmp_path, monkeypatch):
    """Record sin detecciones (vrp=0): regla D no debe inventar nada."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "MIN_VRP_MW_VIIRS375", 0.0)

    rec = {
        "sensor": "VIIRS_NOAA21",
        "datetime_utc": "2026-04-11 05:00",
        "vrp_mir_mw": 0.0,
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 0,
        "n_vent_pixels": 0,
        "hotspot_lat": None,
        "hotspot_lon": None,
        "hotspot_dist_km": None,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        "final_hotspot_lat": None,
        "final_hotspot_lon": None,
        "final_hotspot_dist_km": None,
        "final_hotspot_source": None,
        "distance_class": None,
        "anomaly_pixels": [],
    }
    store.append_record("TestVolcano", rec,
                        volcano_lat=-33.4, volcano_lon=-69.8,
                        max_hotspot_dist_km=25)

    stored = store._load("TestVolcano")["records"][0]
    # Sin detección, no debe inventar summit
    assert stored.get("distance_class") in (None, "")
