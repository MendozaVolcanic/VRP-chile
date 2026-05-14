"""Tests S38 D8 fix — cluster selection vent-anchored.

A/B H_D8_5 (S37) refutó empíricamente "MIROVA suma todo": el path ETI
cuadrático produce subset redundante. Re-análisis caso canónico Puyehue
lacolito + Lascar Salar mostró que el bug D8 NO es de detección sino
de cluster selection. Fix S38: cuando `strategy="vent_anchored"`,
cluster_hotspots() prioriza clusters dentro de inner_radius_km sobre
clusters lejanos, y entre cada grupo prefiere el más cercano.

Estos tests aíslan el contrato del nuevo strategy y validan que
backward-compat se preserva con strategy="vrp_max" (default).
"""
from __future__ import annotations

import numpy as np
import pytest
import yaml
from pathlib import Path

from pipeline.clustering import cluster_hotspots

REPO = Path(__file__).resolve().parent.parent


def _make_scene_two_clusters(vent_lat=-40.6, vent_lon=-72.1):
    """Escena sintética 20×20 con dos clusters bien separados:
    - Cluster A "cráter": 5 pixels cerca del vent (~0.5 km), VRP total 5 MW.
    - Cluster B "lacolito"/"salar": 3 pixels lejanos (~7-8 km), VRP total 0.18 MW.

    El bug D8 canónico: strategy="vrp_max" elige A (más VRP, también más cerca).
    Si invertimos magnitudes (B grande lejano, A chico cercano), el bug se
    manifiesta: vrp_max elige B; vent_anchored elige A.

    Returns: (hot_mask, lat, lon, vrp, vent_lat, vent_lon)
    """
    H = W = 20
    lat = np.zeros((H, W))
    lon = np.zeros((H, W))
    for i in range(H):
        for j in range(W):
            # ~1.1 km/grado (latitud)
            lat[i, j] = vent_lat + (i - 10) * 0.01
            lon[i, j] = vent_lon + (j - 10) * 0.01
    return H, W, lat, lon, vent_lat, vent_lon


def test_vent_anchored_picks_closest_when_far_cluster_is_bigger():
    """Escenario invertido (bug D8 canónico Lascar Salar):
    - Cluster cráter cercano: 2 pixels @ 0.5 km, VRP total 1 MW
    - Cluster Salar lejano: 30 pixels @ 25 km, VRP total 100 MW

    strategy="vrp_max" elige Salar (100 MW > 1 MW).
    strategy="vent_anchored" con inner_radius_km=5 elige cráter (dentro).
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    # Cráter @ vent (i=10, j=10), pixels 10,10 y 10,11
    for (i, j) in [(10, 10), (10, 11)]:
        hot_mask[i, j] = True
        vrp[i, j] = 0.5  # total 1 MW
    # Salar lejano (~25 km del vent), grande, 30 pixels
    salar_pixels = []
    for di in range(0, 5):
        for dj in range(0, 6):
            i, j = -8 + di + 10, -8 + dj + 10  # offset (-8, -8) → fila/col 2-7, 2-7
            if 0 <= i < H and 0 <= j < W:
                salar_pixels.append((i, j))
    salar_pixels = salar_pixels[:30]
    for (i, j) in salar_pixels:
        hot_mask[i, j] = True
        vrp[i, j] = 100.0 / 30.0  # total 100 MW

    # strategy vrp_max (default): Salar primary
    cl_vrp = cluster_hotspots(hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp)
    primary_vrp = cl_vrp[0]
    assert primary_vrp["vrp_mw"] > 50  # es el Salar
    assert primary_vrp["centroid_dist_km"] > 5  # lejos

    # strategy vent_anchored con inner=5km: cráter primary
    cl_va = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vent_anchored", inner_radius_km=5.0,
    )
    primary_va = cl_va[0]
    assert primary_va["vrp_mw"] < 5  # cráter chico
    assert primary_va["centroid_dist_km"] < 2  # cerca del vent


def test_vent_anchored_falls_back_to_closest_when_none_inside_inner():
    """Si NO hay clusters dentro del inner_radius_km, vent_anchored elige
    el más cercano de los que hay fuera (no hace fallback a vrp_max).
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    # Cluster A @ ~8 km (afuera de inner=5)
    for (i, j) in [(3, 10), (3, 11)]:
        hot_mask[i, j] = True
        vrp[i, j] = 0.5  # total 1 MW
    # Cluster B @ ~15 km (más afuera) pero MUCHO más grande
    for (i, j) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        hot_mask[i, j] = True
        vrp[i, j] = 25.0  # total 100 MW

    # vent_anchored: A más cercano gana aunque B sea más grande
    cl = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vent_anchored", inner_radius_km=5.0,
    )
    primary = cl[0]
    assert primary["vrp_mw"] == pytest.approx(1.0, abs=0.01)
    assert 7 <= primary["centroid_dist_km"] <= 9


def test_vent_anchored_inside_inner_beats_outside_regardless_of_vrp():
    """Caso clave Puyehue lacolito: cluster cráter pequeño dentro de inner
    (cráter @ <1km, 1MW) gana sobre cluster lacolito fuera de inner pero
    con más VRP (@ ~8km, 5MW). Ambos son MIROVA-relevantes; vent_anchored
    prefiere el del vent oficial. NOTA: en realidad MIROVA reportó el
    lacolito como ALERTA. Este test documenta que vent_anchored prefiere
    el cráter — la decisión metodológica es: para clones literales MIROVA,
    si MIROVA reporta uno u otro, debería ser el cluster summit aquí.
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    # Cráter @ vent: 2 pixels, 1 MW total
    for (i, j) in [(10, 10), (10, 11)]:
        hot_mask[i, j] = True
        vrp[i, j] = 0.5
    # Lacolito @ ~8 km, 5 pixels, 5 MW total
    for (i, j) in [(3, 16), (3, 17), (4, 16), (4, 17), (3, 18)]:
        hot_mask[i, j] = True
        vrp[i, j] = 1.0

    cl = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vent_anchored", inner_radius_km=5.0,
    )
    primary = cl[0]
    # cráter gana porque está dentro de inner=5km
    assert primary["centroid_dist_km"] < 2
    assert primary["vrp_mw"] == pytest.approx(1.0, abs=0.01)
    # secondary = lacolito
    assert cl[1]["centroid_dist_km"] > 7
    assert cl[1]["vrp_mw"] == pytest.approx(5.0, abs=0.01)


def test_strategy_vrp_max_preserves_legacy_behavior():
    """Backward compat: con strategy="vrp_max" (default), el resultado debe
    ser idéntico al comportamiento anterior (sin parámetro strategy).
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    for (i, j) in [(10, 10), (10, 11), (11, 10)]:
        hot_mask[i, j] = True
        vrp[i, j] = 1.0
    for (i, j) in [(3, 16), (3, 17)]:
        hot_mask[i, j] = True
        vrp[i, j] = 5.0

    cl_default = cluster_hotspots(hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp)
    cl_explicit = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vrp_max",
    )

    # Mismos clusters en mismo orden, mismos valores
    assert len(cl_default) == len(cl_explicit) == 2
    for cd, ce in zip(cl_default, cl_explicit):
        assert cd["vrp_mw"] == ce["vrp_mw"]
        assert cd["centroid_dist_km"] == ce["centroid_dist_km"]
        assert cd["n_pixels"] == ce["n_pixels"]


def test_vent_anchored_requires_inner_radius_km():
    """strategy="vent_anchored" sin inner_radius_km → ValueError."""
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    hot_mask[10, 10] = True

    with pytest.raises(ValueError, match="inner_radius_km"):
        cluster_hotspots(
            hot_mask, lat, lon, vlat, vlon,
            strategy="vent_anchored",  # inner_radius_km ausente
        )


def test_vent_anchored_prefers_cluster_with_vrp_over_zero_close():
    """S43 fix — Caso Lastarria FN: cluster cercano vent con vrp=0 (todos
    pixels delta_L clip 0) vs cluster lejano con vrp>0 (hot real).
    vent_anchored debe elegir el cluster con vrp>0 aunque sea más lejos.
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    # Cluster A: 5 pixels @ vent, vrp=0 (delta_L clip a 0)
    for (i, j) in [(10, 10), (10, 11), (11, 10), (11, 11), (9, 10)]:
        hot_mask[i, j] = True
        vrp[i, j] = 0.0  # ¡vrp=0!
    # Cluster B: 3 pixels @ ~7km, vrp=0.43 (hot real)
    for (i, j) in [(3, 16), (3, 17), (4, 16)]:
        hot_mask[i, j] = True
        vrp[i, j] = 0.15

    cl = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vent_anchored", inner_radius_km=5.0,
    )
    primary = cl[0]
    # vent_anchored prefiere cluster B (vrp>0) aunque más lejos vs cluster A vrp=0
    assert primary["vrp_mw"] == pytest.approx(0.45, abs=0.01), \
        'Debe elegir cluster con vrp>0, no el vrp=0 más cerca'
    assert primary["centroid_dist_km"] > 5  # cluster B está más lejos


def test_vent_anchored_fallback_to_closest_when_all_vrp_zero():
    """S43 sanity: si TODOS clusters tienen vrp=0, fallback a vent_anchored
    proximity normal (preserva comportamiento previo cuando no hay señal real).
    """
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)
    # Ambos clusters con vrp=0
    for (i, j) in [(10, 10), (10, 11)]: hot_mask[i, j] = True
    for (i, j) in [(3, 16), (3, 17)]: hot_mask[i, j] = True

    cl = cluster_hotspots(
        hot_mask, lat, lon, vlat, vlon, vrp_per_pixel=vrp,
        strategy="vent_anchored", inner_radius_km=5.0,
    )
    # Cluster cercano (10,10) gana porque ambos tienen vrp=0
    primary = cl[0]
    assert primary["centroid_dist_km"] < 2


def test_invalid_strategy_raises():
    """strategy desconocido → ValueError."""
    H, W, lat, lon, vlat, vlon = _make_scene_two_clusters()
    hot_mask = np.zeros((H, W), dtype=bool)
    hot_mask[10, 10] = True

    with pytest.raises(ValueError, match="strategy"):
        cluster_hotspots(
            hot_mask, lat, lon, vlat, vlon,
            strategy="some_random_strategy",
        )


def test_d8_vent_anchored_profile_loads():
    """El perfil `_d8_vent_anchored.yaml` parsea y declara el flag
    `enable_vent_anchored_clustering: true` + H8 pixel filter ON.
    """
    path = REPO / 'pipeline' / 'profiles' / '_d8_vent_anchored.yaml'
    assert path.exists(), f'{path} missing'
    with open(path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    assert cfg['profile'] == '_d8_vent_anchored'
    paths_cfg = cfg['paths']
    assert paths_cfg['enable_vent_anchored_clustering'] is True
    # H8 pixel-level filter también activo (combo D8 fix)
    assert paths_cfg.get('enable_pixel_level_distance_filter') is True
    # H_D8_5 paths permanecen OFF (refutados en S37)
    assert paths_cfg.get('enable_eti_quadratic_scene', False) is False
    assert cfg['output']['data_subdir'] == '_d8_vent_anchored'
