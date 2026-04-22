"""detection_context.py — Contextual (8-neighbor) detection gates.

Currently contains the dNTI contextual hot-mask used by P3.2 S15.

Fenomeno fisico: el gate `(NTI_pixel - median(NTI_8_vecinos)) > C1` detecta
pixels que destacan del entorno inmediato, independientemente del sigma
del anillo de fondo. En zonas uniformemente tibias (Lastarria hidrotermal,
Tupungatito glaciar + crateres multiples) el gate global sigma-anillo
infla detecciones espurias porque sigma_bg vuela con la heterogeneidad
regional. El gate contextual inmuniza contra esa heterogeneidad
manteniendo sensibilidad a hotspots localizados.

Ref: Coppola et al. 2016 SP 426.5 "An enhanced automated thermal anomaly
detection algorithm" — C1 absoluto + C2 contextual en dual-ROI.
"""

import numpy as np
from scipy.ndimage import generic_filter


# 8-neighbor footprint (3x3 excluyendo centro)
_FOOTPRINT_8N = np.array(
    [[1, 1, 1],
     [1, 0, 1],
     [1, 1, 1]],
    dtype=bool,
)


def _nanmedian_ignore_self(x: np.ndarray) -> float:
    """Median ignorando NaN; NaN si todos los vecinos son NaN."""
    valid = x[~np.isnan(x)]
    if valid.size == 0:
        return np.nan
    return float(np.median(valid))


def contextual_dnti_hot_mask(
    nti: np.ndarray,
    bt: np.ndarray,
    roi_mask: np.ndarray,
    t_bg: float,
    c1: float,
    bt_sanity_k: float,
) -> np.ndarray:
    """Contextual dNTI hot-pixel mask (Coppola 2016a, 8-neighbor median).

    Un pixel es hot si:
        (NTI_pixel - median(NTI_8_vecinos)) > c1
        AND bt_pixel > t_bg + bt_sanity_k
        AND roi_mask[pixel]

    Args:
        nti: array 2D NTI values, NaN allowed.
        bt: array 2D brightness temperature (K).
        roi_mask: bool 2D, True within volcano ROI.
        t_bg: float, background BT median of the ring (K).
        c1: float, contextual threshold (Coppola 2016a: 0.003 summit).
        bt_sanity_k: float, minimal BT anomaly vs t_bg to avoid cold
            artefacts (K).

    Returns:
        bool array same shape as nti, True where hot.
    """
    if nti.shape != bt.shape or nti.shape != roi_mask.shape:
        raise ValueError(
            f"shape mismatch nti={nti.shape} bt={bt.shape} roi={roi_mask.shape}"
        )
    nti_nbr_med = generic_filter(
        nti, _nanmedian_ignore_self,
        footprint=_FOOTPRINT_8N, mode="constant", cval=np.nan,
    )
    dnti = nti - nti_nbr_med
    hot = (
        roi_mask
        & ~np.isnan(dnti)
        & ~np.isnan(bt)
        & (dnti > c1)
        & (bt > t_bg + bt_sanity_k)
    )
    return hot
