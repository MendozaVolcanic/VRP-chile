"""Tests S71 D9 fix — 3 alternativas A/B path D contextual (cirrus FPs).

Cubre:
- Carga correcta de los 4 keys nuevos en profile.py (con tipo y valor).
- Lógica unitaria del predicado de cada opción (sin tocar HDF5 raw).
- Defaults OFF en profile operacional `mirova_equivalent`.

Las 3 opciones están wireadas en pipeline/process_modis.py,
pipeline/process_viirs.py, pipeline/process_viirs_mod.py.
"""
from __future__ import annotations

import importlib
import os

import numpy as np
import pytest


# --- Helpers ---


def _reload_profile(name: str):
    """Forzar reload de pipeline.profile con un VRP_PROFILE específico."""
    os.environ["VRP_PROFILE"] = name
    import pipeline.profile as p
    importlib.reload(p)
    return p


# --- Profile loading tests ---


def test_operacional_keys_default_off():
    """mirova_equivalent (operacional) NO debe activar D9 — defaults OFF."""
    p = _reload_profile("mirova_equivalent")
    assert p.PATH_D_ATM_GATE_TBG_MIN_K is None
    assert p.PATH_D_REQUIRES_COVALIDATION is False
    assert p.PATH_D_ONLY_CAP_MW is None
    assert p.PATH_D_ONLY_CAP_TBG_MAX_K is None


def test_atm_gate_profile_loads():
    """profile path_d_atm_gate_v1 — Opción A activa con t_bg < 265K."""
    p = _reload_profile("mirova_equivalent_path_d_atm_gate_v1")
    assert isinstance(p.PATH_D_ATM_GATE_TBG_MIN_K, float)
    assert p.PATH_D_ATM_GATE_TBG_MIN_K == 265.0
    assert p.PATH_D_REQUIRES_COVALIDATION is False
    assert p.PATH_D_ONLY_CAP_MW is None
    assert p.DATA_SUBDIR == "mirova_equivalent_path_d_atm_gate_v1"


def test_covalidation_profile_loads():
    """profile path_d_covalidation_v1 — Opción B activa."""
    p = _reload_profile("mirova_equivalent_path_d_covalidation_v1")
    assert p.PATH_D_ATM_GATE_TBG_MIN_K is None
    assert p.PATH_D_REQUIRES_COVALIDATION is True
    assert p.PATH_D_ONLY_CAP_MW is None
    assert p.DATA_SUBDIR == "mirova_equivalent_path_d_covalidation_v1"


def test_cap_profile_loads():
    """profile path_d_cap_v1 — Opción C activa con cap 5 MW @ 270K."""
    p = _reload_profile("mirova_equivalent_path_d_cap_v1")
    assert p.PATH_D_ATM_GATE_TBG_MIN_K is None
    assert p.PATH_D_REQUIRES_COVALIDATION is False
    assert isinstance(p.PATH_D_ONLY_CAP_MW, float)
    assert p.PATH_D_ONLY_CAP_MW == 5.0
    assert isinstance(p.PATH_D_ONLY_CAP_TBG_MAX_K, float)
    assert p.PATH_D_ONLY_CAP_TBG_MAX_K == 270.0


# --- Option A — atm gate predicate ---


def _atm_gate_skip(t_bg: float, gate_k):
    """Replica el predicado wireado en los 3 procesadores."""
    return (
        gate_k is not None
        and not np.isnan(t_bg)
        and t_bg < gate_k
    )


def test_optA_skip_when_tbg_below_gate():
    """t_bg=260K + gate=265K → skip firing contextual."""
    assert _atm_gate_skip(260.0, 265.0) is True


def test_optA_pass_when_tbg_above_gate():
    """t_bg=280K + gate=265K → no skip, firing contextual permitido."""
    assert _atm_gate_skip(280.0, 265.0) is False


def test_optA_off_when_gate_none():
    """gate_k = None (default) → nunca skip."""
    assert _atm_gate_skip(200.0, None) is False
    assert _atm_gate_skip(300.0, None) is False


def test_optA_off_when_tbg_nan():
    """t_bg NaN (escena inválida) → no skip (la lógica downstream ya filtra)."""
    assert _atm_gate_skip(float("nan"), 265.0) is False


# --- Option B — co-validation predicate ---


def _covalidation_ctx_only(bt_path_hot: np.ndarray, nti_path_hot: np.ndarray):
    """Replica el predicado wireado: ctx-only si ni BT ni NTI dispararon."""
    return (not np.any(bt_path_hot)) and (not np.any(nti_path_hot))


def test_optB_blocks_when_ctx_only():
    """bt_path=0, nti_path=0 → ctx_only True → hot_mask debe vaciarse."""
    bt_path = np.zeros((10, 10), dtype=bool)
    nti_path = np.zeros((10, 10), dtype=bool)
    assert _covalidation_ctx_only(bt_path, nti_path) is True


def test_optB_preserves_when_bt_path_fires():
    """bt_path con 1 pixel → ctx_only False → hot_mask preservado."""
    bt_path = np.zeros((10, 10), dtype=bool)
    bt_path[5, 5] = True
    nti_path = np.zeros((10, 10), dtype=bool)
    assert _covalidation_ctx_only(bt_path, nti_path) is False


def test_optB_preserves_when_nti_path_fires():
    """nti_path con 1 pixel → ctx_only False → hot_mask preservado."""
    bt_path = np.zeros((10, 10), dtype=bool)
    nti_path = np.zeros((10, 10), dtype=bool)
    nti_path[3, 7] = True
    assert _covalidation_ctx_only(bt_path, nti_path) is False


# --- Option C — cap predicate ---


def _cap_active(t_bg: float, n_bt: int, n_nti: int, cap_mw, cap_tbg_max):
    """Replica el predicado de cap (boolean)."""
    return (
        cap_mw is not None
        and cap_tbg_max is not None
        and not np.isnan(t_bg)
        and n_bt == 0
        and n_nti == 0
        and t_bg < cap_tbg_max
    )


def _apply_cap(vrp_mw: float, cap_active: bool, cap_mw):
    """Replica la aplicación del cap a primary_cluster.vrp_mw."""
    if cap_active and cap_mw is not None and vrp_mw > cap_mw:
        return cap_mw, True
    return vrp_mw, False


def test_optC_caps_when_ctx_only_and_tbg_below():
    """t_bg=265K + ctx-only + vrp=20 + cap=5 → cap a 5, flag d9_capped True."""
    active = _cap_active(265.0, 0, 0, 5.0, 270.0)
    assert active is True
    vrp_out, flag = _apply_cap(20.0, active, 5.0)
    assert vrp_out == 5.0
    assert flag is True


def test_optC_no_cap_when_tbg_warm():
    """t_bg=275K (warm) → no cap activo, vrp_mw original preservado."""
    active = _cap_active(275.0, 0, 0, 5.0, 270.0)
    assert active is False
    vrp_out, flag = _apply_cap(20.0, active, 5.0)
    assert vrp_out == 20.0
    assert flag is False


def test_optC_no_cap_when_bt_path_fires():
    """bt_path > 0 → ctx-only False → no cap (firing co-validado por BT)."""
    active = _cap_active(265.0, 3, 0, 5.0, 270.0)
    assert active is False


def test_optC_no_cap_when_nti_path_fires():
    """nti_path > 0 → ctx-only False → no cap."""
    active = _cap_active(265.0, 0, 2, 5.0, 270.0)
    assert active is False


def test_optC_no_cap_when_vrp_below_threshold():
    """vrp_mw=3 (< cap=5) → no se altera aunque cap esté activo."""
    active = _cap_active(265.0, 0, 0, 5.0, 270.0)
    assert active is True
    vrp_out, flag = _apply_cap(3.0, active, 5.0)
    assert vrp_out == 3.0
    assert flag is False


def test_optC_off_when_keys_none():
    """cap_mw=None (default operacional) → cap nunca activo."""
    active = _cap_active(260.0, 0, 0, None, None)
    assert active is False


# --- Sanity: keys importables desde procesadores ---


def test_keys_importable_from_modis():
    """Verifica que process_modis.py importa los 4 keys nuevos sin error."""
    _reload_profile("mirova_equivalent")
    # Re-importar el módulo procesador (importa los keys desde profile).
    import pipeline.process_modis as pm
    importlib.reload(pm)
    # Si la importación falló, el reload habría lanzado ImportError.
    assert hasattr(pm, "PATH_D_ATM_GATE_TBG_MIN_K")
    assert hasattr(pm, "PATH_D_REQUIRES_COVALIDATION")
    assert hasattr(pm, "PATH_D_ONLY_CAP_MW")
    assert hasattr(pm, "PATH_D_ONLY_CAP_TBG_MAX_K")


def test_keys_importable_from_viirs():
    """Verifica que process_viirs.py importa los 4 keys nuevos sin error."""
    _reload_profile("mirova_equivalent")
    import pipeline.process_viirs as pv
    importlib.reload(pv)
    assert hasattr(pv, "PATH_D_ATM_GATE_TBG_MIN_K")
    assert hasattr(pv, "PATH_D_REQUIRES_COVALIDATION")
    assert hasattr(pv, "PATH_D_ONLY_CAP_MW")
    assert hasattr(pv, "PATH_D_ONLY_CAP_TBG_MAX_K")


def test_keys_importable_from_viirs_mod():
    """Verifica que process_viirs_mod.py importa los 4 keys nuevos sin error."""
    _reload_profile("mirova_equivalent")
    import pipeline.process_viirs_mod as pvm
    importlib.reload(pvm)
    assert hasattr(pvm, "PATH_D_ATM_GATE_TBG_MIN_K")
    assert hasattr(pvm, "PATH_D_REQUIRES_COVALIDATION")
    assert hasattr(pvm, "PATH_D_ONLY_CAP_MW")
    assert hasattr(pvm, "PATH_D_ONLY_CAP_TBG_MAX_K")
