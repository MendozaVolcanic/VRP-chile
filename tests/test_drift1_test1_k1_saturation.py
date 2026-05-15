"""Tests Drift #1a — Test 1 K1 retire from hot_mask (Coppola 2016a literal)."""
import numpy as np
import pytest


def _build_synthetic_granule_test1_only(nti_value=-0.5):
    """Granule con 1 pixel que cumple Test 1 K1 (NTI > -0.8 noche) pero NO Tests 2∧3."""
    shape = (10, 10)
    nti = np.full(shape, -0.97)  # bg típico
    nti[5, 5] = nti_value  # 1 pixel anómalo solo en Test 1 K1
    bt = np.full(shape, 268.0)
    bt[5, 5] = 270.0  # ligeramente sobre bg
    roi_mask = np.ones(shape, dtype=bool)
    return {"nti": nti, "bt": bt, "roi_mask": roi_mask}


def test_drift1a_off_legacy_nti_path_contributes():
    """Flag OFF: pixel Test 1 K1 entra al hot_mask (legacy behavior)."""
    from pipeline.detection_context import combine_hot_paths

    data = _build_synthetic_granule_test1_only(nti_value=-0.5)
    saturation_mask = np.zeros_like(data["roi_mask"])
    nti_path_hot = (~saturation_mask) & data["roi_mask"] & (data["nti"] > -0.8)

    hot_mask = combine_hot_paths(
        bt_path_hot=np.zeros_like(data["roi_mask"]),
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=np.zeros_like(data["roi_mask"]),
        test1_hot=np.zeros_like(data["roi_mask"]),
        enable_test1_k1_retire_from_hot_mask=False,
    )

    assert hot_mask[5, 5], "Legacy: pixel Test 1 K1 debe estar en hot_mask"
    assert int(np.sum(hot_mask)) == 1


def test_drift1a_on_nti_path_removed_from_hot_mask():
    """Flag ON: pixel Test 1 K1 NO entra al hot_mask."""
    from pipeline.detection_context import combine_hot_paths

    data = _build_synthetic_granule_test1_only(nti_value=-0.5)
    saturation_mask = np.zeros_like(data["roi_mask"])
    nti_path_hot = (~saturation_mask) & data["roi_mask"] & (data["nti"] > -0.8)

    hot_mask = combine_hot_paths(
        bt_path_hot=np.zeros_like(data["roi_mask"]),
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=np.zeros_like(data["roi_mask"]),
        test1_hot=np.zeros_like(data["roi_mask"]),
        enable_test1_k1_retire_from_hot_mask=True,
    )

    assert not hot_mask[5, 5], "Flag ON: pixel Test 1 K1 NO debe estar en hot_mask"
    assert int(np.sum(hot_mask)) == 0


def test_drift1a_does_not_affect_other_paths():
    """Flag ON: paths bt_path, dnti_ctx, test1 NO afectados."""
    from pipeline.detection_context import combine_hot_paths

    shape = (10, 10)
    bt_path_hot = np.zeros(shape, dtype=bool)
    bt_path_hot[3, 3] = True  # 1 pixel bt_path
    nti_path_hot = np.zeros(shape, dtype=bool)
    nti_path_hot[5, 5] = True  # 1 pixel solo Test 1 K1
    dnti_ctx_hot = np.zeros(shape, dtype=bool)
    test1_hot = np.zeros(shape, dtype=bool)

    hot_mask = combine_hot_paths(
        bt_path_hot=bt_path_hot,
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=dnti_ctx_hot,
        test1_hot=test1_hot,
        enable_test1_k1_retire_from_hot_mask=True,
    )

    assert hot_mask[3, 3], "bt_path debe seguir contribuyendo"
    assert not hot_mask[5, 5], "nti_path NO debe contribuir con flag ON"
    assert int(np.sum(hot_mask)) == 1


# ---------------------------------------------------------------------------
# Drift #1b — bg_vals excluye Test 1 K1 active pixels (Coppola 2016a:352-356).
# ---------------------------------------------------------------------------


def _build_synthetic_bg_with_test1_in_ring():
    """Background ring incluye 1 pixel hot Test 1 K1 → contaminates t_bg."""
    shape = (20, 20)
    bt_mir = np.full(shape, 268.0, dtype=np.float64)
    nti = np.full(shape, -0.97, dtype=np.float64)
    bg_mask = np.zeros(shape, dtype=bool)
    bg_mask[2:18, 2:18] = True
    bg_mask[5:7, 5:7] = False  # core volcano excluido

    # Inject pixel Test 1 K1 dentro del bg ring
    bt_mir[10, 10] = 295.0
    nti[10, 10] = -0.5  # supera K1=-0.8 noche
    return {"bt_mir": bt_mir, "nti": nti, "bg_mask": bg_mask}


def test_drift1b_off_bg_contaminated_by_test1_active():
    """Flag OFF: t_bg inflado por pixel Test 1 K1 dentro del ring."""
    from pipeline.detection_context import compute_bg_stats

    data = _build_synthetic_bg_with_test1_in_ring()
    t_bg, std_bg, n_bg = compute_bg_stats(
        bt=data["bt_mir"],
        bg_mask=data["bg_mask"],
        nti=data["nti"],
        nti_k1_threshold=-0.8,
        enable_test1_k1_bg_exclude=False,
    )

    # Sin exclusión: pixel @ 295K infla t_bg sobre 268 (en media; mediana puede ser robusta).
    # Verificamos al menos que std_bg está inflado y n_bg incluye el pixel hot.
    assert n_bg == int(np.sum(data["bg_mask"])), (
        "Sin exclusión, n_bg debe contar todos los pixels bg_mask"
    )
    assert std_bg > 0.5, (
        f"Sin exclusión, std_bg debería estar inflado por outlier 295K (got {std_bg})"
    )


def test_drift1b_on_bg_excludes_test1_k1_active():
    """Flag ON: pixel Test 1 K1 excluido del bg → t_bg correcto."""
    from pipeline.detection_context import compute_bg_stats

    data = _build_synthetic_bg_with_test1_in_ring()
    t_bg, std_bg, n_bg = compute_bg_stats(
        bt=data["bt_mir"],
        bg_mask=data["bg_mask"],
        nti=data["nti"],
        nti_k1_threshold=-0.8,
        enable_test1_k1_bg_exclude=True,
    )

    assert t_bg == pytest.approx(268.0, abs=0.1), (
        f"Con exclusión, t_bg debería ser ~268K (got {t_bg})"
    )
    assert std_bg == pytest.approx(0.0, abs=0.01), (
        f"Con exclusión, std_bg debería ser ~0 (todos los bg son 268K), got {std_bg}"
    )
    assert n_bg < int(np.sum(data["bg_mask"])), (
        "Con exclusión, n_bg debe ser menor (pixel Test 1 K1 excluido)"
    )


def test_drift1b_min_bg_pixels_returns_none():
    """Si <min_bg_pixels válidos, retorna (None, None, n)."""
    from pipeline.detection_context import compute_bg_stats

    shape = (10, 10)
    bt = np.full(shape, np.nan, dtype=np.float64)
    bg_mask = np.ones(shape, dtype=bool)

    t_bg, std_bg, n_bg = compute_bg_stats(
        bt=bt,
        bg_mask=bg_mask,
        min_bg_pixels=10,
    )

    assert t_bg is None and std_bg is None
    assert n_bg == 0
