"""S89 #2 — validación del dato `pipeline/volcanic_features.yaml` + su wiring.

Complementa `test_store_geo_class.py` (que prueba la LÓGICA de geo_class con
features sintéticas). Acá probamos el DATO real cargado del yaml:

1. Integridad estructural: cada feature tiene name/lat/lon/ext_km/source con
   tipos válidos y coords dentro del territorio chileno-andino aproximado.
2. Lazufre (Lastarria) está catalogada con la coord empírica S85
   (F_S81_C_1_ZONES_CATALOG.md cluster 17). Es la única sub-feature S86 que vive
   GENUINAMENTE fuera del inner_radius — las otras (Cerro Blanco 4 km / inner 5,
   Pichi-Llaima 1.3 km / inner 5, El Agrio = vent) ya caen summit, y Planchón N
   no tiene coord verificada distinta del complejo. Ver design §4.4.
3. Integración: un cluster en la coord de Lazufre, con el inner_radius real de
   Lastarria (3 km), se etiqueta `geo_class='extension'`; uno lejos → `far`.

REGLA DE INTEGRIDAD (S88): la coord de Lazufre es un centroide EMPÍRICO de
detección (archivo del repo, fuente aceptada por el header del yaml), NO una
coord de catálogo GVP — mismo estándar que el lacolito PCC ya presente.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod

FEATURES_FILE = Path(__file__).parent.parent / "pipeline" / "volcanic_features.yaml"

# Lazufre — centroide empírico cluster 17 (F_S81_C_1_ZONES_CATALOG.md, S85).
LAZUFRE_LAT, LAZUFRE_LON = -25.174, -68.627
# Vent Lastarria (volcanoes.yaml) e inner_radius operacional.
LASTARRIA_VENT_LAT, LASTARRIA_VENT_LON = -25.168, -68.507
LASTARRIA_INNER_KM = 3.0


@pytest.fixture(scope="module")
def features() -> dict:
    data = yaml.safe_load(FEATURES_FILE.read_text(encoding="utf-8"))
    return data or {}


def test_yaml_loads_as_dict(features):
    assert isinstance(features, dict), "volcanic_features.yaml debe ser un dict por volcán"


def test_every_feature_well_formed(features):
    """Cada feature de cada volcán: name/lat/lon/ext_km/source válidos.

    Bloquea coords inventadas o entradas incompletas (regla integridad S88).
    """
    for volcano, feats in features.items():
        assert isinstance(feats, list), f"{volcano}: el valor debe ser una lista de features"
        for f in feats:
            assert isinstance(f.get("name"), str) and f["name"], f"{volcano}: feature sin name"
            assert isinstance(f.get("lat"), (int, float)), f"{volcano}/{f.get('name')}: lat no numérica"
            assert isinstance(f.get("lon"), (int, float)), f"{volcano}/{f.get('name')}: lon no numérica"
            # Territorio chileno-andino aproximado (incluye lado argentino de complejos).
            assert -56.0 <= f["lat"] <= -17.0, f"{volcano}/{f['name']}: lat {f['lat']} fuera de Chile-Andes"
            assert -76.0 <= f["lon"] <= -66.0, f"{volcano}/{f['name']}: lon {f['lon']} fuera de Chile-Andes"
            assert isinstance(f.get("ext_km"), (int, float)) and f["ext_km"] > 0, (
                f"{volcano}/{f['name']}: ext_km debe ser > 0"
            )
            assert isinstance(f.get("source"), str) and f["source"], (
                f"{volcano}/{f['name']}: feature sin source (cita obligatoria, integridad S88)"
            )


def test_lazufre_catalogued(features):
    """Lazufre presente bajo Lastarria con la coord empírica S85."""
    lastarria = features.get("Lastarria")
    assert lastarria, "Lastarria debe tener al menos la feature Lazufre"
    laz = [f for f in lastarria if "azufre" in f["name"].lower() or "lazufre" in f["name"].lower()]
    assert laz, "no se encontró la feature Lazufre en Lastarria"
    f = laz[0]
    assert f["lat"] == pytest.approx(LAZUFRE_LAT, abs=1e-3)
    assert f["lon"] == pytest.approx(LAZUFRE_LON, abs=1e-3)


def _make_record(pc_lat, pc_lon, pc_dist_km, vent_lat, vent_lon):
    return {
        "vrp_mw": 10.0,
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
        "distance_class": "far",
        "anomaly_pixels": [],
        "primary_cluster": {
            "n_pixels": 5,
            "vrp_mw": 10.0,
            "centroid_lat": pc_lat,
            "centroid_lon": pc_lon,
            "centroid_dist_km": pc_dist_km,
        },
        "t_bg_k": 282.0,
        "t_max_k": 300.0,
        "sensor": "MODIS_TERRA",
        "granule": "test.h5",
        "product_version": "standard",
        "datetime_utc": "2026-05-29 05:30",
    }


def test_lazufre_cluster_classified_extension(features, tmp_path, monkeypatch):
    """Integración: cluster EN la coord de Lazufre, con inner_radius real de
    Lastarria (3 km), se etiqueta extension; uno lejano del campo → far."""
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    feats = features["Lastarria"]

    # haversine vent→Lazufre ≈ 12 km, bien fuera del inner de 3 km.
    rec_ext = _make_record(LAZUFRE_LAT, LAZUFRE_LON, 12.1,
                           LASTARRIA_VENT_LAT, LASTARRIA_VENT_LON)
    store_mod.append_record(
        "LastarriaTest", rec_ext, LASTARRIA_VENT_LAT, LASTARRIA_VENT_LON,
        overwrite=True, max_hotspot_dist_km=25.0,
        enable_pixel_level_distance_filter=False,
        inner_radius_km=LASTARRIA_INNER_KM, volcanic_features=feats,
    )
    saved = json.loads((tmp_path / "LastarriaTest.json").read_text())["records"][0]
    assert saved["primary_cluster"]["geo_class"] == "extension", (
        "cluster en Lazufre debe ser extension. "
        f"got {saved['primary_cluster'].get('geo_class')}"
    )

    # Cluster lejano del campo Lazufre (a ~0.7° = ~70 km) → far.
    rec_far = _make_record(LAZUFRE_LAT - 0.7, LAZUFRE_LON, 80.0,
                           LASTARRIA_VENT_LAT, LASTARRIA_VENT_LON)
    store_mod.append_record(
        "LastarriaTest2", rec_far, LASTARRIA_VENT_LAT, LASTARRIA_VENT_LON,
        overwrite=True, max_hotspot_dist_km=200.0,
        enable_pixel_level_distance_filter=False,
        inner_radius_km=LASTARRIA_INNER_KM, volcanic_features=feats,
    )
    saved2 = json.loads((tmp_path / "LastarriaTest2.json").read_text())["records"][0]
    assert saved2["primary_cluster"]["geo_class"] == "far", (
        "cluster lejos del campo Lazufre debe ser far. "
        f"got {saved2['primary_cluster'].get('geo_class')}"
    )
