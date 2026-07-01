"""S83 F-S81-A Fase 2 — Tests TDD gate Path D MODIS intra-radio.

Cubre:
- Helper unitario `apply_intra_radio_gate` (mascarea dnti_ctx_hot fuera del
  inner_radius_km cuando el flag está ON).
- Fallback cuando inner_radius_km is None (no-op + warning interno).
- Comportamiento idéntico cuando flag OFF (gate transparente).
- Carga del flag `enable_path_d_intra_radio_gate` desde el profile YAML.

Diseño A-simplificada justificada en docs/F_S81_A_FASE1B_SANITY_P95.md:
solo Lascar tiene N>=10 ALERTAs MODIS (p95=2km < inner=5km). Los otros 10
Tier A colapsarian al fallback inner_radius_km igual con o sin script p95.
Gate puro a inner_radius_km cae ~89% de los FPs MODIS Path D (los 765 'far'
del audit Fase 1 sobre experiments/_s82_intra_radio/).
"""
from __future__ import annotations

import importlib
import os

import numpy as np
import pytest


# --- Helpers de reload ---


def _reload_profile(name: str):
    os.environ["VRP_PROFILE"] = name
    import pipeline.profile as p
    importlib.reload(p)
    return p


# --- Tests unitarios del helper ---


def test_gate_off_passthrough_identical():
    """Flag OFF → máscara devuelta es idéntica a la entrada (no toca nada)."""
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((10, 10), dtype=bool)
    dnti_ctx_hot[2, 2] = True   # dentro inner=5km
    dnti_ctx_hot[8, 8] = True   # fuera inner=5km
    vent_dist = np.full((10, 10), 100.0)  # todos far
    vent_dist[2, 2] = 1.0
    vent_dist[8, 8] = 25.0

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=False,
    )
    assert out.shape == dnti_ctx_hot.shape
    assert np.array_equal(out, dnti_ctx_hot)


def test_gate_on_masks_pixels_outside_inner_radius():
    """Flag ON + inner=5km → pixels a >5km del vent se descartan; intra-radius se preserva."""
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((10, 10), dtype=bool)
    dnti_ctx_hot[2, 2] = True   # dist=1km → preservar
    dnti_ctx_hot[3, 3] = True   # dist=4km → preservar
    dnti_ctx_hot[4, 4] = True   # dist=6km → descartar
    dnti_ctx_hot[8, 8] = True   # dist=25km → descartar

    vent_dist = np.full((10, 10), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[3, 3] = 4.0
    vent_dist[4, 4] = 6.0
    vent_dist[8, 8] = 25.0

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert out[2, 2] is np.True_ or bool(out[2, 2]) is True
    assert bool(out[3, 3]) is True
    assert bool(out[4, 4]) is False
    assert bool(out[8, 8]) is False
    # total hot intra-radius == 2 (los 6km y 25km se cayeron)
    assert int(out.sum()) == 2


def test_gate_on_inclusive_at_boundary():
    """Flag ON + inner=5km → pixel exactamente a 5km se preserva (cota inferior <=).

    Coppola 2016a Tabla 2 define summit como inner_km incluido (<=, no <).
    """
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((5, 5), dtype=bool)
    dnti_ctx_hot[2, 2] = True
    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 5.0   # exactamente en borde

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert bool(out[2, 2]) is True


def test_gate_on_inner_radius_none_passthrough():
    """Flag ON pero inner_radius_km=None → no-op (fallback conservador).

    Vols sin entrada inner_radius_km en volcanoes.yaml no deben verse afectados.
    """
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((4, 4), dtype=bool)
    dnti_ctx_hot[1, 1] = True
    dnti_ctx_hot[3, 3] = True
    vent_dist = np.array([
        [1.0, 5.0, 10.0, 25.0],
        [2.0, 4.0, 12.0, 30.0],
        [3.0, 6.0, 15.0, 35.0],
        [4.0, 7.0, 18.0, 40.0],
    ])

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=None,
        enabled=True,
    )
    assert np.array_equal(out, dnti_ctx_hot)


def test_gate_on_empty_mask_returns_empty():
    """Máscara vacía (sin dnti_ctx hits) → salida también vacía, sin error."""
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((6, 6), dtype=bool)
    vent_dist = np.random.rand(6, 6) * 30.0
    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert int(out.sum()) == 0


def test_gate_on_all_intra_radius_no_change():
    """Si todos los hits ya están dentro de inner_radius → salida == entrada."""
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((5, 5), dtype=bool)
    dnti_ctx_hot[2, 2] = True
    dnti_ctx_hot[1, 1] = True
    vent_dist = np.full((5, 5), 1.5)

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert np.array_equal(out, dnti_ctx_hot)


def test_gate_preserves_dtype_and_shape():
    """Helper devuelve bool array de la misma shape."""
    from pipeline.path_d_intra_radio import apply_intra_radio_gate

    dnti_ctx_hot = np.zeros((7, 9), dtype=bool)
    dnti_ctx_hot[3, 4] = True
    vent_dist = np.full((7, 9), 10.0)
    vent_dist[3, 4] = 1.0

    out = apply_intra_radio_gate(
        dnti_ctx_hot=dnti_ctx_hot,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert out.dtype == bool
    assert out.shape == (7, 9)


# --- Profile loading tests ---


def test_operacional_flipped_off_S118():
    """mirova_equivalent (operacional) — flag REMOVIDO (OFF) desde S118.

    Guard de intención (A63): el A/B S118 (run 28312968093, 180/180 success,
    docs/AUDIT_S118_C2_GATES_AB.md) midió CERO robos de cluster en 214 noches
    focales MIROVA-confirmadas con el gate OFF → el gate era anti-patrón A55
    sin protección real (MISSION: MIROVA no cerca por geografía). La adopción
    S84 (run 26540794992) se revierte deliberadamente. Tag pre-s118-c2-flip.
    Si una consolidación futura re-enciende el flag, este test la detecta.
    """
    p = _reload_profile("mirova_equivalent")
    assert p.ENABLE_PATH_D_INTRA_RADIO_GATE is False


def test_profile_enabled_sets_flag_true():
    """profile _f_s81_a_intra_radio_enabled — flag ON + data_subdir aislado."""
    p = _reload_profile("mirova_equivalent_f_s81_a_intra_radio_enabled")
    assert p.ENABLE_PATH_D_INTRA_RADIO_GATE is True
    assert p.DATA_SUBDIR == "mirova_equivalent_f_s81_a_intra_radio_enabled"


def test_profile_disabled_sets_flag_false():
    """profile _f_s81_a_intra_radio_disabled — flag OFF + data_subdir aislado.

    Sirve como baseline aislado del operacional para el A/B (mismo SHA, mismo
    día reprocesado, sin cap S71 distinto, sin más diferencias).
    """
    p = _reload_profile("mirova_equivalent_f_s81_a_intra_radio_disabled")
    assert p.ENABLE_PATH_D_INTRA_RADIO_GATE is False
    assert p.DATA_SUBDIR == "mirova_equivalent_f_s81_a_intra_radio_disabled"
