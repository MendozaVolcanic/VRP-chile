"""Coppola 2015 Eq.1 — Test 1 integrated-ROI MIR detection.

Reference: Coppola et al. 2015, "MIROVA: a new hotspot detection system based
on MODIS Level 1B data", Bulletin of Volcanology 77:55, §2.2.

Test 1 detects spatially-extended sub-pixel hot anomalies that pixel-by-pixel
methods miss. Used by MIROVA as one of three independent detection criteria.

Validated S25 against 6 ALERTA Villarrica VIIRS 375m refs (lava lake
0.05–0.21 MW): 6/6 refs trigger (POC `experiments/53_test1_villarrica_poc.py`).

Algorithm:
    L_MIR(i,j) = spectral radiance from BT via Planck.
    L_bg = median over background ring (excludes inner_km).
    σ_bg = MAD * 1.4826 over same ring.
    ΔL_ROI = Σ max(0, L_MIR(i,j) − L_bg) over full ROI ≤ roi_km.
    σ_ΔL = σ_bg * sqrt(N_ROI_pixels).
    Trigger if: ΔL_ROI > k_sigma * σ_ΔL  AND  ΔL_ROI > mir_rel * L_bg * N_ROI.

Sin side-effects, sin I/O — función pura, testeable con fixtures.
"""
from __future__ import annotations
import math

import numpy as np

from pipeline.scan_geometry import haversine_km

# Planck constants for spectral radiance (units μm)
_C1_LAMBDA = 1.191042e8   # W·m⁻²·sr⁻¹·μm⁻¹·μm⁵
_C2 = 14387.7             # μm·K


def bt_to_radiance_um(bt_K: np.ndarray, lambda_um: float) -> np.ndarray:
    """Planck spectral radiance from brightness temperature.

    Returns radiance in W·m⁻²·sr⁻¹·μm⁻¹. NaN-preserving.
    """
    bt = np.asarray(bt_K, dtype=np.float64)
    out = np.full_like(bt, np.nan)
    mask = np.isfinite(bt) & (bt > 0)
    expo = _C2 / (lambda_um * bt[mask])
    safe = expo < 700  # avoid overflow
    out_idx = np.where(mask)
    expo_safe = np.where(safe, expo, np.nan)
    rad = np.where(safe, (_C1_LAMBDA / lambda_um**5) / (np.exp(expo_safe) - 1), np.nan)
    out[out_idx] = rad
    return out


def compute_test1_mir(
    bt: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    vent_lat: float,
    vent_lon: float,
    lambda_um: float,
    roi_km: float = 3.0,
    inner_ring_km: float = 1.0,
    k_sigma: float = 3.0,
    mir_relative: float = 0.02,
    min_bg_pixels: int = 20,
    nti_hot_mask: "np.ndarray | None" = None,
) -> dict:
    """Coppola 2015 Test 1 integrated-ROI on a MIR brightness temperature array.

    Args:
        bt: 2-D BT array (K), NaN for invalid pixels.
        lat, lon: 2-D coordinate arrays matching bt shape.
        vent_lat, vent_lon: target volcano vent coordinates (deg).
        lambda_um: MIR band wavelength (μm). VIIRS I04=3.74, M13=4.05, MODIS B21/22=3.95.
        roi_km: ROI radius around vent.
        inner_ring_km: exclude radius for background estimation.
        k_sigma: absolute trigger multiplier (Coppola default 3.0).
        mir_relative: relative trigger threshold per-pixel (Coppola default 0.02 = 2%).
        min_bg_pixels: minimum valid pixels in bg ring to compute statistics.
        nti_hot_mask: optional 2-D bool array (bt shape). When provided (S104
            co-validación NTI, Coppola 2024 Eq.13), only pixels that ALSO passed an
            NTI-relative path count toward delta_L, n_contributing and the centroid.
            Excludes warm low-altitude terrain (topographic gradient, NTI-flat) that
            would otherwise inflate the Test1 and drag the centroid off the crater in
            snow-capped volcanoes. None → legacy behavior (no gate).

    Returns:
        dict with keys:
          triggered (bool), abs_criterion (bool), rel_criterion (bool),
          n_roi (int), n_bg (int), n_contributing (int),
          L_bg (float, W·m⁻²·sr⁻¹·μm⁻¹), sigma_bg (float),
          delta_L_integrated (float), sigma_delta_L_integrated (float),
          k_sigma_observed (float), rel_observed (float),
          delta_L_per_pixel (np.ndarray), excess_per_pixel (np.ndarray),
          mask_roi (np.ndarray bool), mask_contributing (np.ndarray bool),
          centroid_lat (float | None), centroid_lon (float | None),
          reason (str if not triggered).
    """
    bt = np.asarray(bt, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    if bt.shape != lat.shape or bt.shape != lon.shape:
        raise ValueError(f"shape mismatch: bt={bt.shape} lat={lat.shape} lon={lon.shape}")
    if nti_hot_mask is not None:
        nti_hot_mask = np.asarray(nti_hot_mask, dtype=bool)
        if nti_hot_mask.shape != bt.shape:
            raise ValueError(
                f"nti_hot_mask shape mismatch: {nti_hot_mask.shape} != bt {bt.shape}"
            )

    dist = haversine_km(vent_lat, vent_lon, lat, lon)
    valid = np.isfinite(bt)
    roi_mask = (dist <= roi_km) & valid
    bg_mask = (dist > inner_ring_km) & (dist <= roi_km) & valid

    n_roi = int(np.sum(roi_mask))
    n_bg = int(np.sum(bg_mask))

    # Empty result template
    empty = {
        "triggered": False,
        "abs_criterion": False,
        "rel_criterion": False,
        "n_roi": n_roi,
        "n_bg": n_bg,
        "n_contributing": 0,
        "L_bg": float("nan"),
        "sigma_bg": float("nan"),
        "delta_L_integrated": 0.0,
        "sigma_delta_L_integrated": 0.0,
        "k_sigma_observed": 0.0,
        "rel_observed": 0.0,
        "mask_roi": roi_mask,
        "mask_contributing": np.zeros_like(bt, dtype=bool),
        "centroid_lat": None,
        "centroid_lon": None,
        "reason": "",
    }

    if n_bg < min_bg_pixels:
        empty["reason"] = f"insufficient_bg_pixels (n_bg={n_bg}<{min_bg_pixels})"
        return empty
    if n_roi == 0:
        empty["reason"] = "empty_roi"
        return empty

    L = bt_to_radiance_um(bt, lambda_um)
    L_bg_vals = L[bg_mask]
    L_bg = float(np.median(L_bg_vals))
    mad = float(np.median(np.abs(L_bg_vals - L_bg)))
    sigma_bg = 1.4826 * mad
    if sigma_bg <= 0:
        empty["reason"] = "zero_sigma_bg"
        return empty

    L_roi = L[roi_mask]
    excess_roi = np.maximum(0.0, L_roi - L_bg)
    if nti_hot_mask is not None:
        # Co-validación NTI (Coppola 2024 Eq.13, S104): solo los píxeles que también
        # pasaron un path NTI relativo cuentan para disparar/integrar/posicionar. El
        # terreno tibio de baja altitud (gradiente topográfico) tiene NTI plano →
        # queda fuera de la máscara → su exceso MIR no infla el Test1 ni arrastra el
        # centroide. Ver docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md.
        nti_roi = nti_hot_mask[roi_mask]
        excess_roi = np.where(nti_roi, excess_roi, 0.0)
    delta_L = float(np.sum(excess_roi))
    sigma_delta_L = sigma_bg * math.sqrt(n_roi)

    contributing_in_roi = excess_roi > 0
    n_contributing = int(np.sum(contributing_in_roi))

    abs_criterion = delta_L > k_sigma * sigma_delta_L
    rel_criterion = delta_L > mir_relative * L_bg * n_roi
    triggered = bool(abs_criterion and rel_criterion)

    # Build full-shape contributing mask
    mask_contributing = np.zeros_like(bt, dtype=bool)
    roi_idx = np.where(roi_mask)
    for k in range(len(roi_idx[0])):
        if contributing_in_roi[k]:
            mask_contributing[roi_idx[0][k], roi_idx[1][k]] = True

    centroid_lat = None
    centroid_lon = None
    if n_contributing > 0:
        weights = excess_roi[contributing_in_roi]
        lat_contrib = lat[mask_contributing]
        lon_contrib = lon[mask_contributing]
        wsum = float(np.sum(weights))
        if wsum > 0:
            centroid_lat = float(np.sum(lat_contrib * weights) / wsum)
            centroid_lon = float(np.sum(lon_contrib * weights) / wsum)

    return {
        "triggered": triggered,
        "abs_criterion": bool(abs_criterion),
        "rel_criterion": bool(rel_criterion),
        "n_roi": n_roi,
        "n_bg": n_bg,
        "n_contributing": n_contributing,
        "L_bg": L_bg,
        "sigma_bg": sigma_bg,
        "delta_L_integrated": delta_L,
        "sigma_delta_L_integrated": sigma_delta_L,
        "k_sigma_observed": delta_L / sigma_delta_L if sigma_delta_L > 0 else 0.0,
        "rel_observed": delta_L / (L_bg * n_roi) if L_bg > 0 else 0.0,
        "mask_roi": roi_mask,
        "mask_contributing": mask_contributing,
        "centroid_lat": centroid_lat,
        "centroid_lon": centroid_lon,
        "reason": "",
    }
