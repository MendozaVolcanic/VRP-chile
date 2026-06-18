# -*- coding: utf-8 -*-
"""TDD para fix S113 #3 — guard de coherencia A46 en store.append_record.

=== El bug (A46 schema asimétrico, bidireccional) ===

`distance_class` (summit/far) se deriva de `final_hotspot_dist_km`, pero el
dashboard reporta la magnitud desde `primary_cluster.vrp_mw` y su gate efectivo
(`mirovaEqVrp`, frontend/index.html) ya exige `distance_class=="summit" AND
pc.centroid_dist_km <= inner_radius_km`. Dos forzados de store.py pueden setear
`distance_class="summit"` SIN respetar el inner_radius, dejando que el dashboard
pinte un punto rojo "summit" cuya magnitud (pc.vrp) viene de un cluster lejano:

  1. cluster_rescue (F47 S77, store.py): rescata cuando pc_cdist <= MAX_HOTSPOT_DIST_KM,
     PERO MAX = geofence radius_km (~25 km) >> inner_radius_km (3-7 km). La suposición
     "near by construction" es falsa cuando MAX >> inner.
  2. vent / Regla D (S20, store.py): vrp_vent>0 fuerza "summit", pero el
     primary_cluster que lleva pc.vrp puede ser un cluster regional lejano.

Caso bandera real (S113, full-history = solo 2 records, ambos Villarrica artefacto
NTI piso, MIROVA silente):
  - 2026-06-11 cluster_rescue: pc.cdist=23.789 km (50 px, geo=far) forzado summit.
  - 2026-06-18 vent: vent 1.638 km (vrp_vent 0.595) forzado summit, pc.cdist=33.9 km.

=== El fix (UNIDIRECCIONAL — decisión Nicolás S113, A45) ===

Guard al final de append_record (tras todos los forzados): si distance_class=="summit"
PERO existe un primary_cluster con vrp_mw>0 cuyo centroid_dist_km > inner_radius_km
(= la magnitud que muestra el dashboard viene de lejos) → relabel "far".

UNIDIRECCIONAL a propósito: NO re-deriva far→summit (eso flipearía 2527 records, trap
A48/A18: clusters crateriana reales tapados por un píxel lejano, 73 de NdC = artefacto
A69 sub-píxel que NO hay que destapar — ver reference_s113_a46_bidirectional). Solo
corrige la etiqueta de color cuando la magnitud reportada viene de fuera del inner.

NO toca detección, cluster selection (A18), magnitud, ni paths. Es alineación interna
del campo de clasificación visual con el gate que el frontend YA aplica (MISSION Q3).

Tag defensivo: pre-s113-a46-coherence-guard.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


@pytest.fixture
def basic_setup(tmp_path, monkeypatch):
    """DATA_DIR aislado + pisos VRP a 0 para no interferir."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS750", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    return tmp_path


def _save_and_load(rec, basic_setup, volcano="VillTest",
                   vent_lat=-39.420227, vent_lon=-71.939876,
                   max_hotspot=25.0, inner_radius_km=5.0):
    """append_record (con inner_radius_km, como el caller real) → record persistido.

    max_hotspot=25 (geofence radius_km) e inner=5 reproducen Villarrica: la
    asimetría MAX >> inner es justamente la que dispara el bug del cluster_rescue.
    """
    store_mod.append_record(
        volcano, rec, vent_lat, vent_lon,
        overwrite=False,
        max_hotspot_dist_km=max_hotspot,
        enable_pixel_level_distance_filter=False,
        inner_radius_km=inner_radius_km,
    )
    data = json.loads((basic_setup / f"{volcano}.json").read_text())
    return data["records"][0]


# ===========================================================================
# RED — los 2 casos bandera reales: summit forzado pero pc lejano → far
# ===========================================================================

def test_cluster_rescue_summit_with_far_cluster_relabeled_far(basic_setup):
    """RED: caso 06-11. cluster_rescue fuerza summit (pc_cdist 15<=MAX 25) pero
    el cluster (la magnitud que muestra el dashboard) está a 15 km > inner 5.
    El guard debe relabelar a 'far' (incoherente: rojo summit con magnitud lejana).
    """
    rec = {
        "vrp_mir_mw": 11.89,
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 50,
        "n_vent_pixels": 0,
        "vent_hotspot_lat": None, "vent_hotspot_lon": None, "vent_hotspot_dist_km": None,
        # pixel single más caliente = FP lejano (>MAX=25) → dispara la rama de rescate
        "hotspot_lat": -39.6, "hotspot_lon": -72.2, "hotspot_dist_km": 30.0,
        "final_hotspot_lat": -39.6, "final_hotspot_lon": -72.2,
        "final_hotspot_dist_km": 30.0, "final_hotspot_source": "eruption",
        "distance_class": "far",
        "primary_cluster": {
            "n_pixels": 50, "vrp_mw": 11.89,
            "centroid_lat": -39.55, "centroid_lon": -72.05,
            "centroid_dist_km": 15.0, "geo_class": "far",
        },
        "anomaly_pixels": [{"lat": -39.6, "lon": -72.2, "dist_km": 30.0, "bt_k": 300.0, "vrp_mw": 5.0}],
        "t_bg_k": 268.0, "t_max_i04_k": 300.0,
        "sensor": "VIIRS_NOAA21", "granule": "fake_0611.h5",
        "product_version": "standard", "datetime_utc": "2026-06-11 05:24",
    }
    saved = _save_and_load(rec, basic_setup)
    # Sanity: el rescate ocurrió (final_hotspot apunta al cluster lejano).
    assert saved.get("final_hotspot_source") == "cluster_rescue"
    assert saved["primary_cluster"]["centroid_dist_km"] == pytest.approx(15.0)
    # CRÍTICO: distance_class debe ser 'far' (magnitud reportada viene de 15 km > inner 5).
    assert saved.get("distance_class") == "far", (
        f"A46: summit con pc.centroid 15km > inner 5km debe relabelarse 'far'. "
        f"got={saved.get('distance_class')}"
    )


def test_vent_summit_with_far_cluster_relabeled_far(basic_setup):
    """RED: caso 06-18. vrp_vent>0 fuerza summit (Regla D) + final_hotspot→vent (1.6km),
    pero el primary_cluster que da pc.vrp está a 33.9 km > inner 5. El dashboard
    muestra pc.vrp=4.342 'summit' → incoherente. El guard debe relabelar a 'far'.
    """
    rec = {
        "vrp_mir_mw": 0.595,
        "vrp_vent_mw": 0.595,
        "n_anomalous_pixels": 2,
        "n_vent_pixels": 1,
        "vent_hotspot_lat": -39.41, "vent_hotspot_lon": -71.95, "vent_hotspot_dist_km": 1.638,
        "hotspot_lat": -39.7, "hotspot_lon": -72.3, "hotspot_dist_km": 35.0,
        "final_hotspot_lat": -39.7, "final_hotspot_lon": -72.3,
        "final_hotspot_dist_km": 35.0, "final_hotspot_source": "eruption",
        "distance_class": "far",
        "primary_cluster": {
            "n_pixels": 2, "vrp_mw": 4.342,
            "centroid_lat": -39.7, "centroid_lon": -72.3,
            "centroid_dist_km": 33.9, "geo_class": "far",
        },
        "anomaly_pixels": [{"lat": -39.7, "lon": -72.3, "dist_km": 35.0, "bt_k": 295.0, "vrp_mw": 4.342}],
        "t_bg_k": 258.0, "t_max_i04_k": 295.0,
        "sensor": "VIIRS_NOAA21_750", "granule": "fake_0618.h5",
        "product_version": "standard", "datetime_utc": "2026-06-18 04:54",
    }
    saved = _save_and_load(rec, basic_setup)
    # Sanity: la Regla D vent forzó summit + final_hotspot→vent (1.638km).
    assert saved.get("final_hotspot_source") == "vent"
    assert saved.get("vrp_mw") == pytest.approx(0.595, rel=1e-2)
    # CRÍTICO: la magnitud que muestra el dashboard (pc.vrp 4.342) viene de 33.9 km → 'far'.
    assert saved.get("distance_class") == "far", (
        f"A46: summit por vent pero pc.centroid 33.9km > inner 5km debe relabelarse 'far'. "
        f"got={saved.get('distance_class')}"
    )


# ===========================================================================
# GREEN — casos legítimos que el guard NO debe tocar (anti-regresión)
# ===========================================================================

def test_legitimate_summit_near_cluster_stays_summit(basic_setup):
    """GREEN: detección summit normal (cluster en el cráter, centroid <= inner).
    El guard NO debe disparar."""
    rec = {
        "vrp_mir_mw": 2.0, "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": 5, "n_vent_pixels": 0,
        "vent_hotspot_lat": None, "vent_hotspot_lon": None, "vent_hotspot_dist_km": None,
        "hotspot_lat": -39.42, "hotspot_lon": -71.94, "hotspot_dist_km": 0.5,
        "final_hotspot_lat": -39.42, "final_hotspot_lon": -71.94,
        "final_hotspot_dist_km": 0.5, "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "primary_cluster": {
            "n_pixels": 5, "vrp_mw": 2.0,
            "centroid_lat": -39.42, "centroid_lon": -71.94,
            "centroid_dist_km": 0.5, "geo_class": "summit",
        },
        "anomaly_pixels": [{"lat": -39.42, "lon": -71.94, "dist_km": 0.5, "bt_k": 330.0, "vrp_mw": 2.0}],
        "t_bg_k": 270.0, "t_max_i04_k": 330.0,
        "sensor": "VIIRS_NOAA21", "granule": "fake_g.h5",
        "product_version": "standard", "datetime_utc": "2026-06-01 05:00",
    }
    saved = _save_and_load(rec, basic_setup)
    assert saved.get("distance_class") == "summit"
    assert saved.get("vrp_mw") == pytest.approx(2.0)


def test_regla_d_vent_summit_near_cluster_stays_summit(basic_setup):
    """GREEN (protege recall S20): vrp_vent>0 con primary_cluster CERCA del vent
    (centroid <= inner) — detección summit legítima del cráter. El guard NO dispara
    (el caso Tupungatito/Chaitén que la Regla D recuperó: pc near, no far)."""
    rec = {
        "vrp_mir_mw": 1.5, "vrp_vent_mw": 1.5,
        "n_anomalous_pixels": 1, "n_vent_pixels": 1,
        "vent_hotspot_lat": -39.42, "vent_hotspot_lon": -71.94, "vent_hotspot_dist_km": 0.3,
        "hotspot_lat": None, "hotspot_lon": None, "hotspot_dist_km": None,
        "final_hotspot_lat": None, "final_hotspot_lon": None,
        "final_hotspot_dist_km": None, "final_hotspot_source": None,
        "distance_class": None,
        "primary_cluster": {
            "n_pixels": 3, "vrp_mw": 1.5,
            "centroid_lat": -39.42, "centroid_lon": -71.94,
            "centroid_dist_km": 2.0, "geo_class": "summit",
        },
        "anomaly_pixels": [],
        "t_bg_k": 270.0, "t_max_i04_k": 320.0,
        "sensor": "MODIS_TERRA", "granule": "fake_d.hdf",
        "product_version": "standard", "datetime_utc": "2026-06-02 03:00",
    }
    saved = _save_and_load(rec, basic_setup)
    # La Regla D forzó summit y el cluster está cerca → debe quedar summit.
    assert saved.get("distance_class") == "summit"


def test_summit_no_primary_cluster_stays_summit(basic_setup):
    """GREEN: summit por vent sin primary_cluster (legacy / sin clustering).
    Sin pc no hay magnitud lejana que delate incoherencia → el guard no dispara."""
    rec = {
        "vrp_mir_mw": 0.8, "vrp_vent_mw": 0.8,
        "n_anomalous_pixels": 1, "n_vent_pixels": 1,
        "vent_hotspot_lat": -39.42, "vent_hotspot_lon": -71.94, "vent_hotspot_dist_km": 0.4,
        "hotspot_lat": None, "hotspot_lon": None, "hotspot_dist_km": None,
        "final_hotspot_lat": None, "final_hotspot_lon": None,
        "final_hotspot_dist_km": None, "final_hotspot_source": None,
        "distance_class": None,
        "anomaly_pixels": [],
        "t_bg_k": 270.0, "t_max_i04_k": 315.0,
        "sensor": "VIIRS_NOAA21", "granule": "fake_n.h5",
        "product_version": "standard", "datetime_utc": "2026-06-03 05:00",
    }
    saved = _save_and_load(rec, basic_setup)
    assert saved.get("distance_class") == "summit"


def test_summit_far_cluster_zero_vrp_stays_summit(basic_setup):
    """GREEN: summit con primary_cluster lejano pero pc.vrp==0 — el dashboard no
    muestra magnitud desde ese cluster (mirovaEqVrp=0 igual) → no hay incoherencia
    de magnitud que corregir. El guard requiere pc.vrp>0, así que no dispara."""
    rec = {
        "vrp_mir_mw": 0.5, "vrp_vent_mw": 0.5,
        "n_anomalous_pixels": 1, "n_vent_pixels": 1,
        "vent_hotspot_lat": -39.42, "vent_hotspot_lon": -71.94, "vent_hotspot_dist_km": 0.4,
        "hotspot_lat": None, "hotspot_lon": None, "hotspot_dist_km": None,
        "final_hotspot_lat": -39.42, "final_hotspot_lon": -71.94,
        "final_hotspot_dist_km": 0.4, "final_hotspot_source": "vent",
        "distance_class": "summit",
        "primary_cluster": {
            "n_pixels": 1, "vrp_mw": 0.0,
            "centroid_lat": -39.7, "centroid_lon": -72.3,
            "centroid_dist_km": 20.0, "geo_class": "far",
        },
        "anomaly_pixels": [],
        "t_bg_k": 270.0, "t_max_i04_k": 312.0,
        "sensor": "VIIRS_NOAA21", "granule": "fake_z.h5",
        "product_version": "standard", "datetime_utc": "2026-06-04 05:00",
    }
    saved = _save_and_load(rec, basic_setup)
    assert saved.get("distance_class") == "summit"


def test_guard_skipped_when_inner_radius_none(basic_setup):
    """GREEN: si inner_radius_km es None (no configurado) el guard no puede decidir
    → no toca distance_class (mismo patrón que el procesador upstream)."""
    rec = {
        "vrp_mir_mw": 0.595, "vrp_vent_mw": 0.595,
        "n_anomalous_pixels": 2, "n_vent_pixels": 1,
        "vent_hotspot_lat": -39.41, "vent_hotspot_lon": -71.95, "vent_hotspot_dist_km": 1.6,
        "hotspot_lat": None, "hotspot_lon": None, "hotspot_dist_km": None,
        "final_hotspot_lat": -39.41, "final_hotspot_lon": -71.95,
        "final_hotspot_dist_km": 1.6, "final_hotspot_source": "vent",
        "distance_class": "summit",
        "primary_cluster": {
            "n_pixels": 2, "vrp_mw": 4.342,
            "centroid_lat": -39.7, "centroid_lon": -72.3,
            "centroid_dist_km": 33.9, "geo_class": "far",
        },
        "anomaly_pixels": [],
        "t_bg_k": 258.0, "t_max_i04_k": 295.0,
        "sensor": "VIIRS_NOAA21_750", "granule": "fake_inone.h5",
        "product_version": "standard", "datetime_utc": "2026-06-05 04:54",
    }
    saved = _save_and_load(rec, basic_setup, inner_radius_km=None)
    assert saved.get("distance_class") == "summit"
