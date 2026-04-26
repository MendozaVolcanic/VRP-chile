"""Invariantes script 38: clasificación TP/T1/T2b/T3/T4 mutuamente exclusiva.

Field names alineados al schema real:
- record JSON: 'n_anomalous_pixels', 'distance_class', 'final_hotspot_dist_km',
               'datetime_utc', 'sensor', 'vrp_mw', 'vrp_vent_mw'
- CSV Mirova-v1: 'Fecha_Satelite_UTC', 'Volcan', 'Sensor', 'VRP_MW',
                  'Distancia_km', 'Origen_Dato'
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.forense_h17_replicable import (
    classify_ref, run_forense, sensor_match,
)


def _ref(ts: str = "2026-04-15 05:30:00", vrp: float = 0.2,
         dist: float = 5.0, sensor: str = "VIIRS375",
         origen: str = "latest.php"):
    return {
        "Fecha_Satelite_UTC": ts,
        "Volcan": "Tupungatito",
        "Sensor": sensor,
        "VRP_MW": vrp,
        "Distancia_km": dist,
        "Origen_Dato": origen,
    }


def _record(ts: str = "2026-04-15 05:35", vrp: float = 0.0, vent: float = 0.0,
            dist_class: str | None = "far", final_dist: float = 10.0,
            n_anom: int = 0, sensor: str = "VIIRS_SNPP"):
    return {
        "datetime_utc": ts,
        "sensor": sensor,
        "vrp_mw": vrp,
        "vrp_vent_mw": vent,
        "distance_class": dist_class,
        "final_hotspot_dist_km": final_dist,
        "n_anomalous_pixels": n_anom,
    }


# === sensor_match ===

def test_sensor_match_viirs375():
    assert sensor_match("VIIRS375", "VIIRS_SNPP")
    assert sensor_match("VIIRS375", "VIIRS_NOAA20")
    assert sensor_match("VIIRS375", "VIIRS_NOAA21")
    assert not sensor_match("VIIRS375", "VIIRS_SNPP_750")
    assert not sensor_match("VIIRS375", "MODIS_AQUA")


def test_sensor_match_viirs750():
    assert sensor_match("VIIRS", "VIIRS_SNPP_750")
    assert sensor_match("VIIRS", "VIIRS_NOAA20_750")
    assert not sensor_match("VIIRS", "VIIRS_SNPP")  # 375m no debe matchear 750m


def test_sensor_match_modis():
    assert sensor_match("MODIS", "MODIS_AQUA")
    assert sensor_match("MODIS", "MODIS_TERRA")
    assert not sensor_match("MODIS", "VIIRS_SNPP")


# === classify_ref ===

def test_classify_t1_no_record():
    """Ref MIROVA exists, no record our side → T1 (no granule)."""
    out = classify_ref(_ref(), records=[], inner_radius_km=7.0,
                       tolerance_min=60)
    assert out["class"] == "T1"


def test_classify_tp_summit():
    """distance_class='summit' → TP."""
    rec = _record(vrp=0.2, vent=0.15, dist_class="summit",
                  final_dist=2.5, n_anom=1)
    out = classify_ref(_ref(), [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "TP"


def test_classify_tp_within_inner_radius():
    """final_hotspot_dist_km <= inner_radius_km → TP aunque distance_class != summit."""
    rec = _record(vrp=0.2, dist_class=None, final_dist=4.5, n_anom=1)
    out = classify_ref(_ref(), [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "TP"


def test_classify_t3_legacy():
    """vrp_vent>0 + distance_class=far + far_dist > inner → T3 (Regla D no aplicada)."""
    rec = _record(vrp=0.2, vent=0.15, dist_class="far",
                  final_dist=12.0, n_anom=1)
    out = classify_ref(_ref(), [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T3"


def test_classify_t4_pixels_only_far():
    """n_anomalous_pixels>0, no summit, vrp_vent=0 → T4 (background no localizado)."""
    rec = _record(vrp=1.0, vent=0.0, dist_class="far",
                  final_dist=15.0, n_anom=377)
    out = classify_ref(_ref(), [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T4"


def test_classify_t2b_cold_scene():
    """Record presente pero n_anomalous=0 → T2b (escena fría)."""
    rec = _record(vrp=0.0, vent=0.0, dist_class=None,
                  final_dist=20.0, n_anom=0)
    out = classify_ref(_ref(), [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T2b"


def test_classify_outside_window_is_t1():
    """Si record está más allá de tolerance_min, clasifica T1."""
    rec = _record(ts="2026-04-15 10:00", final_dist=2.0,
                  dist_class="summit", n_anom=1)
    out = classify_ref(_ref("2026-04-15 05:30:00"), [rec],
                       inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T1"


def test_classes_total_equals_n_refs():
    """Para N refs, sum(TP+T1+T2b+T3+T4) == N."""
    refs = [_ref(f"2026-04-{d:02d} 05:30:00") for d in range(10, 20)]
    records = [
        _record("2026-04-12 05:35", dist_class="summit", final_dist=2.0,
                vrp=0.2, n_anom=1),
        _record("2026-04-15 05:35", dist_class="far", final_dist=12.0,
                vrp=0.2, vent=0.15, n_anom=1),
    ]
    classifications = [classify_ref(r, records, 7.0, 60)["class"] for r in refs]
    counts = {c: classifications.count(c) for c in ("TP", "T1", "T2b", "T3", "T4")}
    assert sum(counts.values()) == len(refs)


def test_run_forense_excludes_ocr_individual_csv(tmp_path):
    """CSV individual con columna Origen_Dato: filtra OCR."""
    csv = tmp_path / "individual.csv"
    pd.DataFrame([
        _ref("2026-04-15 05:30:00", origen="latest.php"),
        _ref("2026-04-16 05:30:00", origen="OCR"),
    ]).to_csv(csv, index=False)

    json_path = tmp_path / "Tupungatito.json"
    json_path.write_text(json.dumps({"records": []}))

    yaml_path = tmp_path / "volcanoes.yaml"
    yaml_path.write_text("Tupungatito:\n  inner_radius_km: 7\n")

    out = run_forense(
        volcano="Tupungatito",
        consolidado_csv=csv,
        records_json=json_path,
        volcanoes_yaml=yaml_path,
        start="2026-04-10",
        end="2026-04-20",
    )
    assert out["n_refs"] == 1


def test_run_forense_excludes_ocr_consolidado_csv(tmp_path):
    """CSV consolidado con columna Tipo_Registro: filtra ALERTA_TERMICA_OCR/RUTINA/NULO."""
    csv = tmp_path / "consolidado.csv"
    pd.DataFrame([
        {"Fecha_Satelite_UTC": "2026-04-15 05:30:00", "Volcan": "Tupungatito",
         "Sensor": "VIIRS375", "Tipo_Registro": "ALERTA_TERMICA",
         "VRP_MW": 0.2, "Distancia_km": 5.0},
        {"Fecha_Satelite_UTC": "2026-04-16 05:30:00", "Volcan": "Tupungatito",
         "Sensor": "VIIRS375", "Tipo_Registro": "ALERTA_TERMICA_OCR",
         "VRP_MW": 0.1, "Distancia_km": 0.0},
        {"Fecha_Satelite_UTC": "2026-04-17 21:00:00", "Volcan": "Tupungatito",
         "Sensor": "MODIS", "Tipo_Registro": "RUTINA",
         "VRP_MW": 0.0, "Distancia_km": 0.0},
        {"Fecha_Satelite_UTC": "2026-04-18 21:00:00", "Volcan": "Tupungatito",
         "Sensor": "MODIS", "Tipo_Registro": "NULO",
         "VRP_MW": 0.0, "Distancia_km": 0.0},
    ]).to_csv(csv, index=False)

    json_path = tmp_path / "Tupungatito.json"
    json_path.write_text(json.dumps({"records": []}))

    yaml_path = tmp_path / "volcanoes.yaml"
    yaml_path.write_text("Tupungatito:\n  inner_radius_km: 7\n")

    out = run_forense(
        volcano="Tupungatito",
        consolidado_csv=csv,
        records_json=json_path,
        volcanoes_yaml=yaml_path,
        start="2026-04-10",
        end="2026-04-20",
    )
    assert out["n_refs"] == 1  # Solo ALERTA_TERMICA cuenta
