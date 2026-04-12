"""
Tests for Path C (NTI-relative) detection logic.

These test the core boolean masking that Path C adds, using synthetic arrays.
We don't test the full process_granule pipeline (requires HDF files) —
we test the detection decision logic that Path C introduces.
"""
import numpy as np
import pytest


def compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k):
    """
    Replicate the Path C mask logic that will be added to process_viirs.py.
    A pixel passes Path C if:
      - It is in the ROI
      - nti > nti_bg + max(0.005, 3.0 * nti_std)    [relative NTI threshold]
      - bt > t_bg + bt_sanity_k                      [BT sanity floor]
    """
    nti_threshold = nti_bg + max(0.005, 3.0 * nti_std)
    return (
        roi_mask
        & ~np.isnan(nti)
        & ~np.isnan(bt)
        & (nti > nti_threshold)
        & (bt > (t_bg + bt_sanity_k))
    )


class TestPathCDetection:
    """Path C: NTI-relative detection for weak fumarolic signals."""

    def _make_scene(self, n=20):
        """Create a synthetic n×n scene with known background."""
        np.random.seed(42)
        roi_mask = np.zeros((n, n), dtype=bool)
        roi_mask[5:15, 5:15] = True  # 10×10 ROI in center

        # Background NTI ~ -0.95 ± 0.002 (typical Andean volcano)
        nti = np.full((n, n), -0.950) + np.random.normal(0, 0.002, (n, n))
        # Background BT ~ 275 K
        bt = np.full((n, n), 275.0) + np.random.normal(0, 1.0, (n, n))

        nti_bg = -0.950
        nti_std = 0.002
        t_bg = 275.0
        bt_sanity_k = 3.0

        return nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k

    def test_no_anomaly_in_background(self):
        """Pure background scene: no pixels should pass Path C."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_weak_fumarole_detected(self):
        """Single pixel with NTI bump +0.015 and BT +4K: should pass Path C."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        # Inject weak fumarole at pixel (10, 10)
        nti[10, 10] = nti_bg + 0.015   # delta=0.015 > max(0.005, 3*0.002=0.006)
        bt[10, 10] = t_bg + 4.0        # 4K > sanity 3K
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 1
        assert mask[10, 10]

    def test_nti_anomaly_below_bt_sanity_rejected(self):
        """NTI is anomalous but BT is too cold: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti[10, 10] = nti_bg + 0.015
        bt[10, 10] = t_bg + 2.0  # 2K < sanity 3K
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_bt_warm_but_nti_normal_rejected(self):
        """BT above sanity but NTI within background: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        bt[10, 10] = t_bg + 5.0   # warm
        # nti stays at background level
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_outside_roi_rejected(self):
        """Anomalous pixel outside ROI: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        # Pixel (2, 2) is outside ROI (roi_mask is [5:15, 5:15])
        nti[2, 2] = nti_bg + 0.015
        bt[2, 2] = t_bg + 4.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_nan_pixels_rejected(self):
        """NaN in either NTI or BT: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti[10, 10] = nti_bg + 0.015
        bt[10, 10] = np.nan  # NaN BT
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_sigma_floor_005(self):
        """When sigma is very small, floor of 0.005 applies."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti_std_tiny = 0.001  # 3*0.001 = 0.003 < floor 0.005
        # Delta of 0.004 should fail (below floor 0.005)
        nti[10, 10] = nti_bg + 0.004
        bt[10, 10] = t_bg + 4.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std_tiny, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0
        # Delta of 0.006 should pass (above floor 0.005)
        nti[10, 10] = nti_bg + 0.006
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std_tiny, t_bg, bt_sanity_k)
        assert np.sum(mask) == 1

    def test_planchonpeteroa_scenario(self):
        """
        Reproduce the PP FN scenario: nti_delta=0.013, bt delta=7K.
        With sigma_nti=0.004, threshold = max(0.005, 0.012) = 0.012.
        Delta 0.013 > 0.012: should detect.
        """
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti_bg_pp = -0.950
        nti_std_pp = 0.004
        t_bg_pp = 276.0
        nti[10, 10] = nti_bg_pp + 0.013
        bt[10, 10] = t_bg_pp + 7.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg_pp, nti_std_pp, t_bg_pp, bt_sanity_k)
        assert np.sum(mask) == 1
