"""Tests TDD — fondo LOCAL de magnitud MODIS: corona del cluster CONTIGUO
(Coppola 2016a Eq.6 "around the active cluster"). Frente §2 / D12 destape.

Design: docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md
(revisión S107: cierra el gap A48 — la corona del cluster, NO el kernel per-pixel
`compute_local_background`, que falla en los INTERIORES de un blob compacto).

Iron Law TDD: estos tests fueron escritos ANTES de implementar
`cluster_corona_background` y `cluster_vrp_mw_with_bg`. RED esperado en primer run
(ImportError → los helpers no existen todavía).

Mecanismo físico bajo prueba:
- Blob de escena tibia (artefacto): corona tan tibia como el blob → ΔL≈0 → VRP chico.
- Lava real (Láscar): cluster rodeado de roca fría → corona fría → ΔL grande → VRP preservado.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline.constants import C1, C2
# Imports bajo prueba — fallan en RED (no existen aún)
from pipeline.vrp_regimes import (
    cluster_corona_background,
    cluster_vrp_mw_with_bg,
    compute_local_background,  # ya existe — para el contraste A48 (test interior)
)

LAMBDA = 3.959  # MODIS B21/22 µm (no crítico para los tests de BT-corona)


def _planck(t_k: float, lam: float) -> float:
    """Planck B(λ,T) independiente del helper (para asserts de VRP)."""
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t_k)) - 1))


# =============================================================================
# Helper 1 — cluster_corona_background: fondo de la corona del cluster contiguo
# =============================================================================

def test_cold_corona_around_small_cluster_returns_cold_bg():
    """Lava real: cluster chico (2 px) sobre roca fría → corona fría.

    Grid 7x7 bg=250K, cluster = (3,3),(3,4) hot 320K. La corona (anillo
    inmediato) son todos píxeles fríos a 250K → t_bk ≈ 250, no degradado.
    Esto preserva ΔL grande (VRP de lava conservado).
    """
    bt = np.full((7, 7), 250.0)
    bt[3, 3] = 320.0
    bt[3, 4] = 320.0
    scene_hot = np.zeros((7, 7), bool)
    scene_hot[3, 3] = scene_hot[3, 4] = True

    t_bk, degraded = cluster_corona_background(
        bt, [(3, 3), (3, 4)], scene_hot, mode="footprint", ring_px=1
    )
    assert degraded is False
    assert math.isclose(t_bk, 250.0, abs_tol=1e-9), f"got {t_bk}"


def test_warm_corona_around_compact_blob_returns_warm_bg():
    """Blob tibio (artefacto): cluster 3x3 (9 px) sobre escena igual de tibia.

    Grid 9x9 bg=285K, cluster = bloque rows 3-5 x cols 3-5 hot 288K. La corona
    está a 285K (igual de tibia) → t_bk ≈ 285 → ΔL≈0 → VRP colapsa. Es justo
    el artefacto que MIROVA descarta ("<5 MW").
    """
    bt = np.full((9, 9), 285.0)
    cluster = [(r, c) for r in (3, 4, 5) for c in (3, 4, 5)]
    scene_hot = np.zeros((9, 9), bool)
    for (r, c) in cluster:
        bt[r, c] = 288.0
        scene_hot[r, c] = True

    t_bk, degraded = cluster_corona_background(
        bt, cluster, scene_hot, mode="footprint", ring_px=1
    )
    assert degraded is False
    assert math.isclose(t_bk, 285.0, abs_tol=1e-9), f"got {t_bk}"


def test_compact_cluster_interior_gets_valid_corona_unlike_per_pixel():
    """A48 KEY: el píxel INTERIOR de un blob compacto.

    `compute_local_background` (per-pixel) da NaN para el centro de un 3x3
    (todos sus vecinos son hot → excluidos) → el caller cae a fondo regional
    frío → RE-INFLACIÓN. `cluster_corona_background` (corona del cluster)
    devuelve un valor FINITO (el anillo que rodea TODO el bloque) → desinfla
    el interior igual que el borde. Esta es la corrección A48.
    """
    bt = np.full((9, 9), 260.0)
    cluster = [(r, c) for r in (3, 4, 5) for c in (3, 4, 5)]
    scene_hot = np.zeros((9, 9), bool)
    for (r, c) in cluster:
        bt[r, c] = 290.0
        scene_hot[r, c] = True

    # per-pixel del CENTRO (4,4) con TODOS los hot de la escena (como el caller
    # real process_modis.py:843): sus 8 vecinos son hot → excluidos → NaN.
    hot_rows = [r for (r, c) in cluster]
    hot_cols = [c for (r, c) in cluster]
    center_idx = cluster.index((4, 4))
    center_pp = compute_local_background(bt, hot_rows, hot_cols, kernel_size=3)[center_idx]
    assert math.isnan(center_pp), "per-pixel del interior debería ser NaN (A48)"

    # corona del cluster: FINITA y fría (260) → desinfla el interior
    t_bk, degraded = cluster_corona_background(
        bt, cluster, scene_hot, mode="footprint", ring_px=1
    )
    assert degraded is False
    assert not math.isnan(t_bk)
    assert math.isclose(t_bk, 260.0, abs_tol=1e-9), f"got {t_bk}"


def test_corona_excludes_adjacent_blob_hot_pixels():
    """Exclusión escena-wide: la corona de A NO incluye hot pixels de otro blob.

    Grid 11x11 bg=250K. Cluster A = (5,5) hot 320K. Otro blob B = (5,7) hot 320K
    (2 px de distancia, scene_hot incluye ambos). Con ring_px=2 la corona de A
    ALCANZA (5,7), pero debe EXCLUIRLO (es hot de otro cluster) → t_bk se queda
    en 250 (frío), NO contaminado hacia 320. Sin la exclusión, t_bk subiría.
    """
    bt = np.full((11, 11), 250.0)
    bt[5, 5] = 320.0
    bt[5, 7] = 320.0
    scene_hot = np.zeros((11, 11), bool)
    scene_hot[5, 5] = scene_hot[5, 7] = True

    t_bk, degraded = cluster_corona_background(
        bt, [(5, 5)], scene_hot, mode="footprint", ring_px=2
    )
    assert degraded is False
    assert math.isclose(t_bk, 250.0, abs_tol=1e-9), (
        f"corona contaminada por blob adyacente: t_bk={t_bk}"
    )


def test_cluster_at_border_with_few_corona_pixels_degrades():
    """Borde del ROI: si la corona válida < min_corona → degradado.

    Cluster en esquina (0,0) con casi todo NaN alrededor → solo 2 píxeles de
    corona válidos < min_corona=4 → (NaN, True) para que el caller caiga al
    fondo regional explícitamente (no silencioso).
    """
    bt = np.full((5, 5), np.nan)
    bt[0, 0] = 320.0          # cluster (hot)
    bt[0, 1] = 250.0          # corona válida 1
    bt[1, 0] = 250.0          # corona válida 2
    scene_hot = np.zeros((5, 5), bool)
    scene_hot[0, 0] = True

    t_bk, degraded = cluster_corona_background(
        bt, [(0, 0)], scene_hot, mode="footprint", ring_px=1, min_corona=4
    )
    assert degraded is True
    assert math.isnan(t_bk)


def test_corona_ignores_nan_neighbors():
    """NaN en la corona se ignoran; con ≥min_corona válidos → no degradado."""
    bt = np.full((7, 7), 270.0)
    bt[3, 3] = 320.0          # cluster
    bt[2, 2] = np.nan         # un par de NaN en la corona
    bt[2, 3] = np.nan
    scene_hot = np.zeros((7, 7), bool)
    scene_hot[3, 3] = True

    t_bk, degraded = cluster_corona_background(
        bt, [(3, 3)], scene_hot, mode="footprint", ring_px=1, min_corona=4
    )
    assert degraded is False
    assert math.isclose(t_bk, 270.0, abs_tol=1e-9), f"got {t_bk}"


def test_ring_mode_excludes_footprint_of_large_cluster():
    """V-A (mode='ring'): el anillo geométrico cae FUERA del footprint.

    Cluster 3x3 hot=300K sobre bg=260K. El anillo (r_in > radio del footprint)
    debe promediar solo bg frío (260), NO los píxeles hot del interior. Si r_in
    fuera muy chico, incluiría hot → t_bk subiría.
    """
    bt = np.full((13, 13), 260.0)
    cluster = [(r, c) for r in (5, 6, 7) for c in (5, 6, 7)]
    scene_hot = np.zeros((13, 13), bool)
    for (r, c) in cluster:
        bt[r, c] = 300.0
        scene_hot[r, c] = True

    t_bk, degraded = cluster_corona_background(
        bt, cluster, scene_hot, mode="ring", ring_px=2
    )
    assert degraded is False
    assert math.isclose(t_bk, 260.0, abs_tol=1e-9), f"ring incluyó hot? t_bk={t_bk}"


# =============================================================================
# Helper 2 — cluster_vrp_mw_with_bg: VRP del cluster con un fondo dado
# =============================================================================

def test_vrp_collapses_when_corona_equals_cluster_temp():
    """Blob tibio: corona ≈ temperatura del cluster → ΔL≈0 → VRP ≈ 0."""
    bt = np.full((5, 5), 285.0)
    for (r, c) in [(2, 2), (2, 3)]:
        bt[r, c] = 285.5
    areas = np.full((5, 5), 1e6)  # 1 km² nadir
    vrp = cluster_vrp_mw_with_bg(
        bt, areas, [(2, 2), (2, 3)], t_bk_bg_k=285.0,
        wooster_coeff=18.9, lambda_um=LAMBDA,
    )
    assert vrp < 0.5, f"blob tibio debería colapsar, got {vrp} MW"


def test_vrp_preserved_when_corona_cold_matches_manual():
    """Lava real: corona fría → ΔL grande → VRP > 0 y == cálculo manual."""
    bt = np.full((5, 5), 250.0)
    bt[2, 2] = 330.0
    areas = np.full((5, 5), 1e6)
    vrp = cluster_vrp_mw_with_bg(
        bt, areas, [(2, 2)], t_bk_bg_k=250.0,
        wooster_coeff=18.9, lambda_um=LAMBDA,
    )
    expected = 1e6 * 18.9 * (_planck(330.0, LAMBDA) - _planck(250.0, LAMBDA)) / 1e6
    assert vrp > 0
    assert math.isclose(vrp, expected, rel_tol=1e-6), f"{vrp} vs {expected}"


def test_vrp_clips_negative_delta_to_zero():
    """Píxel más frío que la corona → ΔL clip a 0 (no VRP negativo)."""
    bt = np.full((5, 5), 250.0)
    bt[2, 2] = 240.0  # más frío que el bg
    areas = np.full((5, 5), 1e6)
    vrp = cluster_vrp_mw_with_bg(
        bt, areas, [(2, 2)], t_bk_bg_k=250.0,
        wooster_coeff=18.9, lambda_um=LAMBDA,
    )
    assert vrp == 0.0, f"ΔL negativo no clipeado: {vrp}"


def test_vrp_skips_nan_cluster_pixels():
    """Píxeles NaN del cluster se saltan (no rompen la suma)."""
    bt = np.full((5, 5), 250.0)
    bt[2, 2] = 330.0
    bt[2, 3] = np.nan
    areas = np.full((5, 5), 1e6)
    vrp = cluster_vrp_mw_with_bg(
        bt, areas, [(2, 2), (2, 3)], t_bk_bg_k=250.0,
        wooster_coeff=18.9, lambda_um=LAMBDA,
    )
    expected = 1e6 * 18.9 * (_planck(330.0, LAMBDA) - _planck(250.0, LAMBDA)) / 1e6
    assert math.isclose(vrp, expected, rel_tol=1e-6), f"{vrp} vs {expected}"


# =============================================================================
# Integración en process_modis (smoke, patrón S58 — pyhdf roto en Windows)
# =============================================================================

def test_local_cluster_magnitude_flag_defaults_off():
    """El flag está OFF por default → comportamiento operacional sin cambios
    hasta un flip futuro post-A/B (A45)."""
    from pipeline.profile import ENABLE_LOCAL_CLUSTER_MAGNITUDE
    assert ENABLE_LOCAL_CLUSTER_MAGNITUDE is False


def test_process_modis_integrates_local_cluster_magnitude_flag():
    """Smoke test (patrón S58 test_local_kernel_modis.py:152): la integración del
    fondo-local-corona está presente en process_modis.py detrás del flag
    ENABLE_LOCAL_CLUSTER_MAGNITUDE. No corre el pipeline full (HDF L1B / pyhdf
    roto en Windows); la validación conductual son los unit tests de los helpers
    + el A/B real en GH Actions.
    """
    import inspect
    import pipeline.process_modis as pm
    src = inspect.getsource(pm)
    assert "ENABLE_LOCAL_CLUSTER_MAGNITUDE" in src, "flag no importado/usado"
    assert "cluster_corona_background" in src, "helper corona no usado"
    # S127: el recompute pasa por el helper POR PÍXEL, no por el que sólo devuelve el
    # total. Con el total solo, todo lo que corre después (focal, single-pixel mode)
    # seguía leyendo los VRP del fondo regional y anulaba la corona sin dejar rastro.
    assert "cluster_vrp_per_pixel_with_bg" in src, "helper vrp por píxel no usado"
    assert "if ENABLE_LOCAL_CLUSTER_MAGNITUDE" in src, "flag no usado como guard"
