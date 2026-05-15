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
