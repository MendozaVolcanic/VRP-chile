"""Test detection-anchor vs grid-center role separation (S98, enfoque B).

Contexto (docs/superpowers/specs/2026-06-02-detection-anchor-crater-design.md):
`get_effective_vent()` conflaba dos roles. El `mirova_center` (centro del
recuadro KMZ, el extent de la grilla MIROVA) se usaba como ancla de detección
dual-ROI + clustering vent_anchored + distance_class. Para Tupungatito (4.86 km),
PuyehueCordonCaulle (7.57 km) y PlanchonPeteroa (2.02 km) ese centro está lejos
del cráter físico → detecciones corridas (Tupungatito ~5.9 km al sur, glaciar).

Fix S98 = separar roles:
  - get_grid_center(volcano)      -> mirova_center prioritario (extent/grid/cross-check)
  - get_detection_anchor(volcano) -> vent_lat prioritario (cráter): detección,
                                     clustering, distance_class y distancia mostrada.

El guard de regresión real (test_real_*) es la salvaguarda que faltó en S80:
una consolidación que regenere los 11 mirova_center desde el KMZ NO debe volver
a mover el ancla de detección al grid center.
"""

import math
from pathlib import Path

import yaml

from pipeline.geo_utils import get_detection_anchor, get_grid_center

_REPO = Path(__file__).resolve().parents[1]


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _load_volcanoes():
    data = yaml.safe_load(open(_REPO / "volcanoes.yaml", encoding="utf-8"))
    return {v["name"]: v for v in data["volcanoes"]}


# --- get_detection_anchor: prioriza el cráter (vent) -----------------------

def test_detection_anchor_prefers_vent_over_mirova_center():
    v = {"lat": -33.4, "lon": -69.8,
         "vent_lat": -33.389044, "vent_lon": -69.826374,
         "mirova_center_lat": -33.42694, "mirova_center_lon": -69.80039}
    assert get_detection_anchor(v) == (-33.389044, -69.826374)


def test_detection_anchor_falls_back_to_mirova_center_when_no_vent():
    v = {"lat": -33.4, "lon": -69.8,
         "mirova_center_lat": -33.42694, "mirova_center_lon": -69.80039}
    assert get_detection_anchor(v) == (-33.42694, -69.80039)


def test_detection_anchor_falls_back_to_volcano_center():
    v = {"lat": -42.8, "lon": -72.65}
    assert get_detection_anchor(v) == (-42.8, -72.65)


def test_detection_anchor_none_when_nothing_set():
    assert get_detection_anchor({}) == (None, None)


def test_detection_anchor_partial_vent_falls_back_cleanly():
    """Solo vent_lat (sin vent_lon) -> tratar vent como unset, caer a mirova_center."""
    v = {"vent_lat": -33.389,
         "mirova_center_lat": -33.42694, "mirova_center_lon": -69.80039}
    assert get_detection_anchor(v) == (-33.42694, -69.80039)


# --- get_grid_center: prioriza el centro del grid (mirova_center) ----------

def test_grid_center_prefers_mirova_center_over_vent():
    v = {"lat": -33.4, "lon": -69.8,
         "vent_lat": -33.389044, "vent_lon": -69.826374,
         "mirova_center_lat": -33.42694, "mirova_center_lon": -69.80039}
    assert get_grid_center(v) == (-33.42694, -69.80039)


def test_grid_center_falls_back_to_vent_then_centroid():
    v = {"lat": -23.37, "lon": -67.73, "vent_lat": -23.363, "vent_lon": -67.730}
    assert get_grid_center(v) == (-23.363, -67.730)
    assert get_grid_center({"lat": -42.8, "lon": -72.65}) == (-42.8, -72.65)


def test_grid_center_partial_mirova_center_falls_back_cleanly():
    v = {"vent_lat": -33.389, "vent_lon": -69.826, "mirova_center_lat": -33.4269}
    assert get_grid_center(v) == (-33.389, -69.826)


# --- GUARD anti-regresión (config real) — la salvaguarda que faltó en S80 ---

OFFSET_VOLS = ["Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"]


def test_real_offset_volcanoes_anchor_at_crater_not_grid():
    """Tupun/PCC/PP: el ancla de detección DEBE ser el cráter (vent), NO el
    centro del grid. Falla si una consolidación revierte el fix (como S80)."""
    vols = _load_volcanoes()
    for name in OFFSET_VOLS:
        v = vols[name]
        anchor = get_detection_anchor(v)
        assert anchor == (v["vent_lat"], v["vent_lon"]), (
            f"{name}: detection anchor {anchor} != cráter "
            f"({v['vent_lat']},{v['vent_lon']})")
        # y debe estar lejos del grid center (el offset que causaba el corrimiento)
        gc = get_grid_center(v)
        off = _haversine_km(anchor[0], anchor[1], gc[0], gc[1])
        assert off > 1.5, (
            f"{name}: ancla a solo {off:.2f} km del grid center; el guard "
            f"asume offset grande (Tupun 4.86 / PCC 7.57 / PP 2.02 km)")


def test_real_small_offset_volcanoes_unchanged():
    """Los volcanes de offset chico (<1 km): anchor ≈ grid center → cambio nulo."""
    vols = _load_volcanoes()
    names = set(vols) - set(OFFSET_VOLS)
    for name in names:
        v = vols[name]
        if not v.get("mirova_monitored"):
            continue
        if v.get("vent_lat") is None or v.get("mirova_center_lat") is None:
            continue
        anchor = get_detection_anchor(v)
        gc = get_grid_center(v)
        off = _haversine_km(anchor[0], anchor[1], gc[0], gc[1])
        assert off < 1.0, (
            f"{name}: offset {off:.2f} km — esperado <1 km (sin cambio observable)")
