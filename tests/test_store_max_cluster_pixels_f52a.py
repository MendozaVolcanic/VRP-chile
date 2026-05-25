"""F52-A/S77 TDD — per-volcano max_cluster_pixels cap (Villarrica glaciar fix).

Bug F52-A (PR #191 audit confirmado): Villarrica tiene ratio mediano
ours/MIROVA = 10.91× porque clusters de 16-86 pixels caen sobre el glaciar
Pichillancahue NW del cráter (ΔT 5-11K — pixels glaciares marginales, NO
lava lake real). Vent coords correctas, exclude_zones del lago activos.

Otros Tier A con clusters similares (Lastarria/Llaima/Copahue mediana
35-46 pixels) están bien calibrados — porque sus pixels tienen ΔT alto
(lava real). El problema es ESPECÍFICO de Villarrica donde clusters
grandes son glaciares.

Fix: agregar campo opcional `max_cluster_pixels` per-volcano en
`volcanoes.yaml`. Cuando seteado y `primary_cluster.n_pixels >
max_cluster_pixels`, anular el rollup (vrp_mw=0, discarded_reason
"cluster_too_large_for_volcano").

Para Villarrica: `max_cluster_pixels: 12` (sweep confirmó cae 31→5 records
matching MIROVA). Sin override → comportamiento legacy intacto.

Refs:
- docs/F52_VILLARRICA_OVER_ESTIMATION_S77.md (PR #191)
- experiments/146_f52_villarrica/audit_result.json
- tag defensivo: pre-s77-f52a-villarrica-cluster-cap
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import store as store_mod


# Helper para construir record mínimo válido
def _make_record(n_pixels: int, pc_vrp: float = 50.0, dist_km: float = 1.0):
    return {
        "vrp_mir_mw": pc_vrp,
        "vrp_vent_mw": 0.0,
        "n_anomalous_pixels": n_pixels,
        "n_vent_pixels": 0,
        "hotspot_lat": -39.42 + 0.001,
        "hotspot_lon": -71.94 + 0.001,
        "hotspot_dist_km": dist_km,
        "final_hotspot_lat": -39.42 + 0.001,
        "final_hotspot_lon": -71.94 + 0.001,
        "final_hotspot_dist_km": dist_km,
        "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": [],
        "primary_cluster": {
            "n_pixels": n_pixels,
            "vrp_mw": pc_vrp,
            "centroid_lat": -39.42 + 0.001,
            "centroid_lon": -71.94 + 0.001,
            "centroid_dist_km": dist_km,
        },
        "t_bg_k": 282.0,
        "t_max_i04_k": 290.0,
        "sensor": "VIIRS_NOAA20",
        "granule": "test_granule.h5",
        "product_version": "standard",
        "datetime_utc": "2026-05-23 05:30",
    }


@pytest.fixture
def basic_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS375", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_VIIRS750", 0.0)
    monkeypatch.setattr(store_mod, "MIN_VRP_MW_MODIS", 0.0)
    return tmp_path


def _save_and_load(rec, basic_setup, volcano="TestVol", max_cluster_pixels=None):
    """Helper: ejecuta append_record (con nuevo kwarg max_cluster_pixels) + load."""
    store_mod.append_record(
        volcano, rec, -39.42, -71.94,
        overwrite=False,
        max_hotspot_dist_km=25.0,
        enable_pixel_level_distance_filter=False,
        max_cluster_pixels=max_cluster_pixels,  # F52-A: nuevo kwarg
    )
    data = json.loads((basic_setup / f"{volcano}.json").read_text())
    return data["records"][0]


def test_no_cap_passthrough_legacy(basic_setup):
    """Sin max_cluster_pixels (default None) → comportamiento legacy intacto.

    Records existentes para volcanes sin override (Lastarria/Llaima/etc.
    que tienen clusters grandes legítimos por lava real) NO se afectan.
    """
    rec = _make_record(n_pixels=60, pc_vrp=80.0)
    saved = _save_and_load(rec, basic_setup, max_cluster_pixels=None)
    assert saved.get("vrp_mw", 0) == pytest.approx(80.0, rel=1e-2), (
        f"Sin cap, cluster 60 px debe pasar (legacy). got {saved.get('vrp_mw')}"
    )


def test_cap_blocks_oversized_cluster(basic_setup):
    """Villarrica scenario: cluster 60 px (glaciar) con cap=12 → vrp_mw=0."""
    rec = _make_record(n_pixels=60, pc_vrp=80.0)
    saved = _save_and_load(rec, basic_setup, max_cluster_pixels=12)
    assert saved.get("vrp_mw", 0) == 0, (
        f"Cluster 60 px > cap 12 → vrp_mw debe ser 0 (descartado por glaciar). "
        f"got {saved.get('vrp_mw')}"
    )
    assert saved.get("discarded_reason") == "cluster_too_large_for_volcano", (
        f"discarded_reason debe etiquetar el descarte. got {saved.get('discarded_reason')}"
    )


def test_cap_passes_small_cluster(basic_setup):
    """Cluster 8 px con cap=12 → passthrough (es cluster pequeño legítimo)."""
    rec = _make_record(n_pixels=8, pc_vrp=12.5)
    saved = _save_and_load(rec, basic_setup, max_cluster_pixels=12)
    assert saved.get("vrp_mw", 0) == pytest.approx(12.5, rel=1e-2), (
        f"Cluster 8 px <= cap 12 → passthrough. got {saved.get('vrp_mw')}"
    )


def test_cap_at_exact_boundary(basic_setup):
    """Boundary: n_pixels == cap → pass (estrictamente mayor para cap)."""
    rec = _make_record(n_pixels=12, pc_vrp=20.0)
    saved = _save_and_load(rec, basic_setup, max_cluster_pixels=12)
    assert saved.get("vrp_mw", 0) == pytest.approx(20.0, rel=1e-2), (
        f"n_pixels == cap NO debe descartarse (estricto >). got {saved.get('vrp_mw')}"
    )


def test_cap_zero_passthrough(basic_setup):
    """Edge: cap=0 → todo cluster con n>0 sería descartado.
    Comportamiento aceptable pero anti-intuitivo. Convención: cap=0 OFF.
    """
    rec = _make_record(n_pixels=5, pc_vrp=8.0)
    saved = _save_and_load(rec, basic_setup, max_cluster_pixels=0)
    # cap=0 tratamos como flag OFF (no cap aplicable)
    assert saved.get("vrp_mw", 0) == pytest.approx(8.0, rel=1e-2), (
        f"cap=0 debe tratarse como OFF (passthrough). got {saved.get('vrp_mw')}"
    )
