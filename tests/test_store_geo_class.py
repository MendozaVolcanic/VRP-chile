"""S88 Frente B TDD — campo derivado `pc.geo_class` en store.append_record.

Objetivo: etiquetar GEOMÉTRICAMENTE cada detección respecto al cono volcánico,
para que el frontend pueda renderizar honestamente "monitoreo VRP Chile con
desglose MIROVA" en lugar de "clon que sobre-detecta". El 46.3% de nuestros
"FPs" son features volcánicas reales no publicadas por MIROVA (marco S86,
docs/AUDIT_S86.md) — geo_class las distingue de las lejanas.

Diseño: docs/superpowers/specs/2026-05-29-s88-pc-classification-design.md
  - "summit"    — primary_cluster dentro del inner_radius_km (es el cráter).
  - "extension" — fuera del inner pero dentro de EXT_KM de una feature
                  volcánica catalogada (lacolito PCC, Lazufre, El Agrio...).
  - "far"       — ni cráter ni feature catalogada cerca.
  - None        — sin primary_cluster (no aplica).

Decisión arquitectural (design §4.2): geo_class es GEOMETRÍA PURA sobre
pc.centroid_dist_km / lat / lon ya calculados. NO usa el gate t_bg<260K
(refutado S86 — perdería Lascar 02-17 eruptivo). NO cambia detección, VRP, ni
filtra: es solo una etiqueta descriptiva. El cruce con MIROVA
(mirova_confirmed) vive en el frontend, NO acá (no acoplar NRT a CSV externo).

Campo nuevo: kwargs `inner_radius_km` y `volcanic_features` (lista de dicts
{lat, lon, ext_km}) en append_record, espejando el patrón max_cluster_pixels.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


# Volcán de prueba: vent en (-23.37, -67.73) (estilo Lascar).
VENT_LAT, VENT_LON = -23.37, -67.73


def _make_record(pc_lat, pc_lon, pc_dist_km, vrp=10.0,
                 dt="2026-05-23 05:30", sensor="MODIS_TERRA"):
    """Record mínimo con primary_cluster en (pc_lat, pc_lon) a pc_dist_km del vent."""
    return {
        "vrp_mw": vrp,
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 5,
        "n_vent_pixels": 0,
        "hotspot_lat": pc_lat,
        "hotspot_lon": pc_lon,
        "hotspot_dist_km": pc_dist_km,
        "final_hotspot_lat": pc_lat,
        "final_hotspot_lon": pc_lon,
        "final_hotspot_dist_km": pc_dist_km,
        "final_hotspot_source": "eruption",
        "distance_class": "summit" if pc_dist_km <= 5 else "far",
        "anomaly_pixels": [],
        "primary_cluster": {
            "n_pixels": 5,
            "vrp_mw": vrp,
            "centroid_lat": pc_lat,
            "centroid_lon": pc_lon,
            "centroid_dist_km": pc_dist_km,
        },
        "t_bg_k": 282.0,
        "t_max_k": 300.0,
        "sensor": sensor,
        "granule": "test.h5",
        "product_version": "standard",
        "datetime_utc": dt,
    }


@pytest.fixture
def basic_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS750", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    return tmp_path


def _save_and_load(rec, basic_setup, volcano="TestVol",
                   inner_radius_km=None, volcanic_features=None):
    store_mod.append_record(
        volcano, rec, VENT_LAT, VENT_LON,
        overwrite=False,
        max_hotspot_dist_km=25.0,
        enable_pixel_level_distance_filter=False,
        inner_radius_km=inner_radius_km,
        volcanic_features=volcanic_features,
    )
    data = json.loads((basic_setup / f"{volcano}.json").read_text())
    return data["records"][0]


def test_summit_within_inner_radius(basic_setup):
    """Cluster a 2 km del vent, inner=5 → geo_class='summit'."""
    rec = _make_record(VENT_LAT + 0.018, VENT_LON, pc_dist_km=2.0)
    saved = _save_and_load(rec, basic_setup, inner_radius_km=5.0)
    assert saved["primary_cluster"]["geo_class"] == "summit", (
        f"cluster intra-radio debe ser summit. got {saved['primary_cluster'].get('geo_class')}"
    )


def test_far_no_feature(basic_setup):
    """Cluster a 20 km del vent, sin features catalogadas → geo_class='far'."""
    rec = _make_record(VENT_LAT + 0.18, VENT_LON, pc_dist_km=20.0)
    saved = _save_and_load(rec, basic_setup, inner_radius_km=5.0,
                           volcanic_features=None)
    assert saved["primary_cluster"]["geo_class"] == "far", (
        f"cluster lejano sin feature debe ser far. got {saved['primary_cluster'].get('geo_class')}"
    )


def test_extension_near_catalogued_feature(basic_setup):
    """Cluster fuera del inner pero a ~1 km de una feature catalogada (estilo
    lacolito PCC / Lazufre) → geo_class='extension'."""
    # feature catalogada en (-23.50, -67.73), ~14.4 km al sur del vent.
    feat_lat, feat_lon = -23.50, -67.73
    # cluster a ~1 km de la feature (todavía fuera del inner de 5 km del vent).
    rec = _make_record(feat_lat + 0.009, feat_lon, pc_dist_km=15.4)
    saved = _save_and_load(
        rec, basic_setup, inner_radius_km=5.0,
        volcanic_features=[{"lat": feat_lat, "lon": feat_lon, "ext_km": 2.0}],
    )
    assert saved["primary_cluster"]["geo_class"] == "extension", (
        f"cluster cerca de feature catalogada debe ser extension. "
        f"got {saved['primary_cluster'].get('geo_class')}"
    )


def test_far_outside_feature_ext(basic_setup):
    """Cluster lejano de la feature (más allá de su ext_km) → geo_class='far'."""
    feat_lat, feat_lon = -23.50, -67.73
    # cluster a ~5 km de la feature, ext_km=2 → fuera → far.
    rec = _make_record(feat_lat + 0.045, feat_lon, pc_dist_km=10.5)
    saved = _save_and_load(
        rec, basic_setup, inner_radius_km=5.0,
        volcanic_features=[{"lat": feat_lat, "lon": feat_lon, "ext_km": 2.0}],
    )
    assert saved["primary_cluster"]["geo_class"] == "far", (
        f"cluster fuera del ext_km de la feature debe ser far. "
        f"got {saved['primary_cluster'].get('geo_class')}"
    )


def test_summit_takes_precedence_over_feature(basic_setup):
    """Cluster intra-radio Y cerca de feature → summit gana (es el cráter)."""
    rec = _make_record(VENT_LAT + 0.018, VENT_LON, pc_dist_km=2.0)
    saved = _save_and_load(
        rec, basic_setup, inner_radius_km=5.0,
        volcanic_features=[{"lat": VENT_LAT, "lon": VENT_LON, "ext_km": 2.0}],
    )
    assert saved["primary_cluster"]["geo_class"] == "summit"


def test_no_inner_radius_no_geo_class(basic_setup):
    """Sin inner_radius_km (None) → no se computa geo_class (legacy intacto).

    Garantiza que perfiles/volcanes sin la config no rompen ni agregan campo.
    """
    rec = _make_record(VENT_LAT + 0.018, VENT_LON, pc_dist_km=2.0)
    saved = _save_and_load(rec, basic_setup, inner_radius_km=None)
    assert "geo_class" not in saved["primary_cluster"], (
        "sin inner_radius_km no debe agregarse geo_class (legacy). "
        f"got {saved['primary_cluster'].get('geo_class')}"
    )


def test_geo_class_does_not_change_vrp(basic_setup):
    """geo_class es etiqueta pura: NO cambia vrp_mw ni distance_class."""
    rec = _make_record(VENT_LAT + 0.18, VENT_LON, pc_dist_km=20.0, vrp=42.0)
    saved = _save_and_load(rec, basic_setup, inner_radius_km=5.0)
    # vrp_mw puede ser zero-out por hotspot_dist>radius en otro path, pero el
    # cluster vrp y la etiqueta geo_class no deben interferir entre sí.
    assert saved["primary_cluster"]["geo_class"] == "far"
    # el cluster vrp original se preserva en primary_cluster
    assert saved["primary_cluster"]["vrp_mw"] == pytest.approx(42.0, rel=1e-2)
