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


def test_operacional_adopta_optC():
    """mirova_equivalent (operacional) — S71 adoptó Opción C (cap 5MW @ t_bg<270K)
    como defensa intermedia D9. Opciones A y B siguen OFF (causa raíz pendiente T1.5).

    Regla S33 vinculante: R1+R2+R3 validados antes de adopción.
    Ver experiments/130_r3_audit_independent_optC/, 131_r2_pixel_level_optC/,
    docs/MIROVA_DIVERGENCES.md D9.
    """
    p = _reload_profile("mirova_equivalent")
    # Opción A — gate atmosférico: OFF (causa-raíz pendiente T1.5)
    assert p.PATH_D_ATM_GATE_TBG_MIN_K is None
    # Opción B — co-validación: OFF (colapsa recall NdC)
    assert p.PATH_D_REQUIRES_COVALIDATION is False
    # Opción C — cap magnitud: ON (winner S71 R1+R2+R3)
    assert p.PATH_D_ONLY_CAP_MW == 5.0
    assert p.PATH_D_ONLY_CAP_TBG_MAX_K == 270.0


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


def test_no_cap_profile_loads_with_null_cap():
    """profile mirova_equivalent_no_cap_v1 (S72 F2.6.b) — copia exacta del
    operacional con cap S71 OFF (null). Resto de la deriva S38-S61 intacta.
    Permite A/B aislado cap-on (operacional) vs cap-off (este profile) mismo SHA.
    """
    p = _reload_profile("mirova_equivalent_no_cap_v1")
    # Cap S71 D9 OFF — override del operacional 5.0 / 270.0
    assert p.PATH_D_ONLY_CAP_MW is None
    assert p.PATH_D_ONLY_CAP_TBG_MAX_K is None
    # Opciones A y B siguen OFF (idem operacional)
    assert p.PATH_D_ATM_GATE_TBG_MIN_K is None
    assert p.PATH_D_REQUIRES_COVALIDATION is False
    # data_subdir aislado
    assert p.DATA_SUBDIR == "mirova_equivalent_no_cap_v1"


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


# --- F2.6.a anti-regresión: el cap NO debe aniquilar records sub-cap ---
# Diagnóstico F2.5.b reportó Lascar VIIRS 2026-03-19 06:36 con pc.vrp_mw
# 0.667 → 0.008 (-83x) atribuido al cap. Análisis F2.6.a probó que el cap
# NO disparó (d9_capped=None en cap_v1 reproc; capped records muestran
# pc.vrp_mw=5.0 exacto en 100% de los casos). La reducción es deriva
# arquitectural entre el reproc S26 que produjo el record operacional
# y el reproc S71 cap_v1, no el cap. Estos tests blindan la semántica
# esperada para evitar futura confusión.


def test_optC_strict_gt_no_cap_at_exact_threshold():
    """vrp_mw = cap_mw exacto (5.0) → no se modifica (cap usa `>` estricto).

    Sin este guard, un cap con `>=` reduciría a 5.0 records ya en 5.0
    sin marca d9_capped (no-op silencioso) o marcaría flag falso.
    """
    active = _cap_active(265.0, 0, 0, 5.0, 270.0)
    assert active is True
    vrp_out, flag = _apply_cap(5.0, active, 5.0)
    assert vrp_out == 5.0
    assert flag is False  # `>` estricto: 5.0 no es > 5.0


def test_optC_no_cap_for_sub_mw_record_ctx_only_cold_bg():
    """Record con vrp_mw=0.5 + t_bg=265K + ctx-only → preserved (NO aniquilado).

    Replica el escenario F2.5.b reportado (Lascar VIIRS 06:36 pc=0.667
    cirrus). El cap NO debe tocar records sub-cap independientemente del
    régimen atmosférico. Si este test falla, el cap se aplica fuera del
    if `> cap_mw` (bug grave).
    """
    active = _cap_active(265.0, 0, 0, 5.0, 270.0)
    assert active is True  # predicate activo (ctx-only + cold bg)
    vrp_out, flag = _apply_cap(0.5, active, 5.0)
    assert vrp_out == 0.5  # intacto
    assert flag is False


def test_optC_no_cap_for_record_2_5_mw_ctx_only_cold_bg():
    """vrp_mw=2.5 sub-cap → preserved. Replica F2.5.b MODIS 71.6→0.40 (que
    si fuese causado por cap habría que ver pc=5.0, no 0.40)."""
    active = _cap_active(260.0, 0, 0, 5.0, 270.0)
    assert active is True
    vrp_out, flag = _apply_cap(2.5, active, 5.0)
    assert vrp_out == 2.5
    assert flag is False


def test_optC_caps_exactly_to_cap_value_no_truncation():
    """vrp_mw=8.0 supra-cap → pc.vrp_mw exact 5.0 (no aproximaciones float)."""
    active = _cap_active(268.0, 0, 0, 5.0, 270.0)
    vrp_out, flag = _apply_cap(8.0, active, 5.0)
    assert vrp_out == 5.0  # equality estricta
    assert flag is True


def test_optC_no_cap_at_tbg_max_boundary():
    """t_bg = cap_tbg_max exacto (270.0) → no activo (`<` estricto).

    Sin este guard, un cap con `<=` en t_bg afectaría escenas justo en
    el límite warm/cold que MIROVA típicamente clasifica diferente.
    """
    active = _cap_active(270.0, 0, 0, 5.0, 270.0)
    assert active is False  # `<` estricto: 270.0 no es < 270.0


def test_optC_no_cap_when_bt_and_nti_both_fire():
    """bt_path=5 + nti_path=3 (firing co-validado) → no cap (no es ctx-only)."""
    active = _cap_active(265.0, 5, 3, 5.0, 270.0)
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
