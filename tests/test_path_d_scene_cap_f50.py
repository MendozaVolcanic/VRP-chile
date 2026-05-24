"""F50/S77 TDD tests — cap D9 sobre vrp_mw scene-wide.

Bug F50 (PR #185 audit): el cap `PATH_D_ONLY_CAP_MW=5.0` se aplicaba SOLO
a `primary_cluster.vrp_mw` (process_modis.py:802 + :1017, simétrico en
los otros 2 procesadores) pero NO a `vrp_mw = sum(per_pixel_vrp_mw)`
scene-wide en línea 753 (y simétricos). Resultado: 715 records afectados
en 11 Tier A (621 MODIS + 94 VIIRS) durante condiciones cirrus extendido,
con vrp_mw scene-wide alcanzando 80-510 MW mientras el cluster summit
era 0.6-5 MW.

Patognomónico (PR #185 audit): MODIS_AQUA 2026-05-23 07:25 UTC, mismo
granule cubrió 5 Tier A simultáneos, todos con vrp_mw 81-510 MW y
pc.vrp_mw 0.6-5 MW. Cirrus extendido confirmado por t_bg<270K simultáneo.

Fix Opción A (mínima): aplicar el mismo cap a vrp_mw scene-wide cuando
`_path_d_cap_active` (cirrus + 0 BT/NTI duros). Helper compartida
`pipeline.path_d_cap.apply_d9_scene_cap`.

Refs:
- docs/F50_MODIS_07_25_AUDIT_S77.md
- experiments/138_audit_mw_outliers_s76/ (precedente metodológico F46)
- tag defensivo: pre-s77-f50-vrp-mw-cap
"""
from __future__ import annotations

import pytest


def _try_import():
    try:
        from pipeline.path_d_cap import apply_d9_scene_cap
        return apply_d9_scene_cap
    except ImportError:
        return None


_FUNC = _try_import()


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_active_over_threshold_capped_to_cap():
    """Bug F50 escenario principal: cirrus + suma scene-wide enorme → cap."""
    result = _FUNC(vrp_mw=150.47, path_d_cap_active=True, cap_mw=5.0)
    assert result == 5.0, (
        f"Cap D9 debe limitar vrp_mw=150 a cap=5.0 cuando path_d_cap_active=True. "
        f"got {result}"
    )


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_active_under_threshold_unchanged():
    """Cap NO afecta valores ya bajo el threshold."""
    result = _FUNC(vrp_mw=2.5, path_d_cap_active=True, cap_mw=5.0)
    assert result == 2.5, (
        f"Cap no debe modificar vrp_mw=2.5 < cap=5.0. got {result}"
    )


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_inactive_passthrough_high():
    """Cuando path_d_cap_active=False (firing real BT/NTI o no cirrus), passthrough."""
    result = _FUNC(vrp_mw=150.47, path_d_cap_active=False, cap_mw=5.0)
    assert result == 150.47, (
        f"Sin cap activo (firing real volcanico), passthrough. got {result}"
    )


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_active_at_exact_threshold_unchanged():
    """Boundary: exact == cap NO se modifica (estrictamente mayor para cap)."""
    result = _FUNC(vrp_mw=5.0, path_d_cap_active=True, cap_mw=5.0)
    assert result == 5.0


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_active_zero_unchanged():
    """Edge: vrp_mw=0 no se toca aunque cap activo."""
    result = _FUNC(vrp_mw=0.0, path_d_cap_active=True, cap_mw=5.0)
    assert result == 0.0


@pytest.mark.xfail(_FUNC is None, reason="F50 helper pending fix")
def test_cap_none_passthrough():
    """Cap=None significa flag deshabilitado (compat con perfiles que no lo tienen)."""
    result = _FUNC(vrp_mw=150.47, path_d_cap_active=True, cap_mw=None)
    assert result == 150.47, (
        f"Cap=None → flag OFF → passthrough sin importar path_d_cap_active. "
        f"got {result}"
    )
