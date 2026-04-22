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


def dual_roi_contextual_dnti_hot_mask(
    nti: np.ndarray,
    bt: np.ndarray,
    roi_mask: np.ndarray,
    dist_km: np.ndarray,
    t_bg: float,
    c1_summit: float,
    c1_scene: float,
    inner_km: float,
    bt_sanity_k: float,
) -> np.ndarray:
    """Dual-ROI contextual dNTI mask (Coppola 2016a SP 426.5, P3.1 S15).

    Aplica umbrales distintos segun la distancia al centro del volcan:
      - summit (dist <= inner_km): c1_summit (sensible, 0.003 por paper).
      - scene  (dist >  inner_km): c1_scene  (estricto, 0.010 por paper).

    Fenomeno fisico: el analisis S15 Lastarria muestra que 80% de refs MIROVA
    25 anos estan en summit (0-3 km), pero Path D sin dual-ROI captura 55%
    de pixels a 15-25 km (Lazufre/Cordon del Azufre — termicamente reales
    pero fuera del vent MIROVA). Umbral scene estricto descarta esos.

    Args:
        nti, bt, roi_mask, t_bg, bt_sanity_k: como en contextual_dnti_hot_mask.
        dist_km: array 2D con distancia de cada pixel al vent (km).
        c1_summit: C1 contextual para summit ROI.
        c1_scene: C1 contextual para scene ROI.
        inner_km: radio que separa summit de scene (inner_radius_km del vol).

    Returns:
        bool array True donde hot segun el C1 aplicable por distancia.
    """
    if dist_km.shape != nti.shape:
        raise ValueError(f"dist_km shape {dist_km.shape} != nti {nti.shape}")
    summit_mask = roi_mask & (dist_km <= inner_km)
    scene_mask = roi_mask & (dist_km > inner_km)
    hot_summit = contextual_dnti_hot_mask(
        nti, bt, summit_mask, t_bg, c1_summit, bt_sanity_k,
    )
    hot_scene = contextual_dnti_hot_mask(
        nti, bt, scene_mask, t_bg, c1_scene, bt_sanity_k,
    )
    return hot_summit | hot_scene
