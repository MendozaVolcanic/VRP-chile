"""S85 Fase B' — Tests TDD gate intra-radio sobre second_pass_recapture.

Cubre:
- Helper unitario `apply_second_pass_intra_radio_gate`.
- Pixel del second pass intra-radio → preservado.
- Pixel del second pass extra-radio → mascarado.
- Pixel del first pass extra-radio → intacto (gate no aplica).
- Flag OFF → comportamiento idéntico.
- inner_radius_km=None → fallback no-op.
- Carga del flag `enable_second_pass_intra_radio_gate` desde profile YAML.

Diseño justificado en docs/F_S81_B_PRIME_SECOND_PASS_GATE.md.
Audit B0 que motivó esto: docs/R3_RESIDUAL_BY_PATH.md.
"""
from __future__ import annotations

import importlib
import os

import numpy as np


def _reload_profile(name: str):
    os.environ["VRP_PROFILE"] = name
    import pipeline.profile as p
    importlib.reload(p)
    return p


# --- Tests unitarios del helper ---


def test_gate_off_passthrough_identical():
    """Flag OFF → máscara devuelta == final_active_mask original."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((5, 5), dtype=bool)
    first[2, 2] = True   # 1 pixel first pass intra-radio

    final = first.copy()
    final[4, 4] = True   # second pass recapture extra-radio

    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[4, 4] = 20.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=False,
    )
    assert np.array_equal(out, final)


def test_second_pass_extra_radio_masked():
    """Flag ON → pixel nuevo del second pass fuera del inner_radius descartado."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((5, 5), dtype=bool)
    first[2, 2] = True   # first pass intra-radio (preservar)

    final = first.copy()
    final[4, 4] = True   # second pass extra-radio (descartar)

    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[4, 4] = 20.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert bool(out[2, 2]) is True   # first preservado
    assert bool(out[4, 4]) is False  # 2nd extra-radio descartado
    assert int(out.sum()) == 1


def test_second_pass_intra_radio_preserved():
    """Flag ON → pixel nuevo del second pass dentro del inner_radius preservado."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((5, 5), dtype=bool)
    first[2, 2] = True

    final = first.copy()
    final[2, 3] = True   # 2nd pass adyacente, intra-radio

    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[2, 3] = 2.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert bool(out[2, 2]) is True
    assert bool(out[2, 3]) is True
    assert int(out.sum()) == 2


def test_first_pass_extra_radio_intact_when_gate_on():
    """Flag ON NO mascarea pixels del first pass (incluso extra-radio).

    El gate es responsabilidad estricta del second pass; el first pass tiene
    sus propios filtros (BT path / NTI path / dnti_ctx path con F-S81-A).
    """
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((5, 5), dtype=bool)
    first[2, 2] = True   # intra-radio
    first[4, 4] = True   # extra-radio (raro pero válido — paths A/B sin gate)

    final = first.copy()  # second pass no agregó nada

    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[4, 4] = 20.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert bool(out[2, 2]) is True
    assert bool(out[4, 4]) is True  # first pass extra-radio INTACTO
    assert int(out.sum()) == 2


def test_inner_radius_none_passthrough():
    """Flag ON + inner_radius_km=None → no-op fallback."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((4, 4), dtype=bool)
    first[1, 1] = True
    final = first.copy()
    final[3, 3] = True
    vent_dist = np.full((4, 4), 100.0)

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=None,
        enabled=True,
    )
    assert np.array_equal(out, final)


def test_no_recapture_when_gate_on_returns_first_pass():
    """Si second pass no recapturó nada, salida == first pass mask."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((4, 4), dtype=bool)
    first[1, 1] = True
    final = first.copy()  # idéntico
    vent_dist = np.full((4, 4), 1.0)

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert np.array_equal(out, first)


def test_boundary_pixel_at_inner_radius_preserved():
    """Pixel del second pass exactamente a inner_radius_km → preservado (<= inclusivo).

    Coherente con F-S81-A (apply_intra_radio_gate usa <= no <).
    """
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((5, 5), dtype=bool)
    first[2, 2] = True
    final = first.copy()
    final[3, 3] = True  # nuevo, justo a 5km

    vent_dist = np.full((5, 5), 100.0)
    vent_dist[2, 2] = 1.0
    vent_dist[3, 3] = 5.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert bool(out[3, 3]) is True


def test_dtype_and_shape_preserved():
    """Helper devuelve bool array de la misma shape."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((7, 9), dtype=bool)
    first[3, 4] = True
    final = first.copy()
    final[5, 5] = True
    vent_dist = np.full((7, 9), 10.0)
    vent_dist[3, 4] = 1.0
    vent_dist[5, 5] = 2.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    assert out.dtype == bool
    assert out.shape == (7, 9)


def test_many_pixels_mixed():
    """Caso realista: varios pixels mixtos. Verificar conteo y geometría."""
    from pipeline.second_pass_intra_radio import apply_second_pass_intra_radio_gate

    first = np.zeros((10, 10), dtype=bool)
    first[5, 5] = True
    first[5, 6] = True

    final = first.copy()
    # 2nd pass recaptura 4 pixels: 2 intra, 2 extra
    final[4, 5] = True   # intra
    final[6, 5] = True   # intra
    final[1, 1] = True   # extra
    final[9, 9] = True   # extra

    vent_dist = np.full((10, 10), 100.0)
    vent_dist[5, 5] = 0.5
    vent_dist[5, 6] = 1.0
    vent_dist[4, 5] = 1.0
    vent_dist[6, 5] = 1.5
    vent_dist[1, 1] = 25.0
    vent_dist[9, 9] = 50.0

    out = apply_second_pass_intra_radio_gate(
        first_pass_mask=first,
        final_active_mask=final,
        vent_dist_per_pixel=vent_dist,
        inner_radius_km=5.0,
        enabled=True,
    )
    # 2 first + 2 second intra = 4. Los 2 extra del 2nd descartados.
    assert int(out.sum()) == 4
    assert bool(out[5, 5]) is True
    assert bool(out[5, 6]) is True
    assert bool(out[4, 5]) is True
    assert bool(out[6, 5]) is True
    assert bool(out[1, 1]) is False
    assert bool(out[9, 9]) is False


# --- Profile loading tests ---


def test_operacional_default_off():
    """mirova_equivalent (operacional) — flag default OFF hasta validación A/B."""
    p = _reload_profile("mirova_equivalent")
    assert p.ENABLE_SECOND_PASS_INTRA_RADIO_GATE is False


def test_profile_enabled_sets_flag_true():
    """profile _f_s81_b_prime_2nd_pass_gate_enabled — flag ON + data_subdir."""
    p = _reload_profile("mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled")
    assert p.ENABLE_SECOND_PASS_INTRA_RADIO_GATE is True
    assert p.DATA_SUBDIR == "mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled"


def test_profile_disabled_sets_flag_false():
    """profile _f_s81_b_prime_2nd_pass_gate_disabled — flag OFF + data_subdir."""
    p = _reload_profile("mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled")
    assert p.ENABLE_SECOND_PASS_INTRA_RADIO_GATE is False
    assert p.DATA_SUBDIR == "mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled"
