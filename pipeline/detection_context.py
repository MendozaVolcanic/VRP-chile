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


def _nanmean_ignore_self(x: np.ndarray) -> float:
    """Arithmetic mean ignorando NaN; NaN si todos los vecinos son NaN.

    S17 D1 fix: Coppola 2016a SP 426.5 seccion "Spatial analysis" dice
    textualmente "subtracting from its value the average (arithmetic mean)
    of the eight neighbouring pixels". Campus et al. 2024 Bull Volcanol
    86:25 p.3 confirma: "arithmetic mean of the radiance of the pixels
    surrounding the alerted one(s)". Previo a este commit usabamos np.median,
    drift sin respaldo en papers MIROVA. Cambio a np.mean aritmetica.
    """
    valid = x[~np.isnan(x)]
    if valid.size == 0:
        return np.nan
    return float(np.mean(valid))


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
    # S17 perf fix: generic_filter con funcion Python sobre granule
    # completo (~6400x6400 VIIRS) tarda horas. Recortamos al bbox del
    # ROI (+1 pixel de margen para el footprint 3x3) — el resultado
    # fuera del ROI se descarta de todos modos, asi que el recorte es
    # matematicamente no-op.
    ys, xs = np.where(roi_mask)
    if ys.size == 0:
        return np.zeros_like(roi_mask, dtype=bool)
    y0 = max(0, int(ys.min()) - 1)
    y1 = min(nti.shape[0], int(ys.max()) + 2)
    x0 = max(0, int(xs.min()) - 1)
    x1 = min(nti.shape[1], int(xs.max()) + 2)
    nbr_crop = generic_filter(
        nti[y0:y1, x0:x1], _nanmean_ignore_self,
        footprint=_FOOTPRINT_8N, mode="constant", cval=np.nan,
    )
    nti_nbr_med = np.full_like(nti, np.nan)
    nti_nbr_med[y0:y1, x0:x1] = nbr_crop
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


def dual_roi_bt_threshold(
    bt: np.ndarray,
    roi_mask: np.ndarray,
    dist_km: np.ndarray,
    t_bg: float,
    std_bg: float,
    inner_km: float,
    n_sigma_summit: float,
    n_sigma_scene: float,
    anomaly_floor_k: float,
    max_sigma_cap_k: float,
) -> np.ndarray:
    """Coppola 2016a Tabla 1 — dual-ROI N·sigma thresholds en eruption-path BT.

    Pixels dentro del summit (dist <= inner_km) usan threshold sensible
    (5 sigma tipico Coppola); fuera usan threshold estricto (10 sigma noche).

    Mantiene fixes historicos:
    - Floor (`anomaly_floor_k`, Coppola 2015 ANOMALY_THRESHOLD_K).
    - Cap (`max_sigma_cap_k`, S15 Tema F MAX_SIGMA_COMPONENT_K=7K) para no
      explotar threshold cuando std_bg es enorme (orografia glaciar).

    Args:
        bt: 2-D array brightness temperature (K). NaN preserva.
        roi_mask: bool 2-D, pixels candidatos a evaluar.
        dist_km: 2-D distancia al vent (km).
        t_bg: median background.
        std_bg: sigma background.
        inner_km: radio del split summit/scene.
        n_sigma_summit, n_sigma_scene: multiplicadores N sigma por zona.
        anomaly_floor_k: floor delta-BT minimo.
        max_sigma_cap_k: cap del componente N sigma.

    Returns:
        bool array shape igual a bt, True donde pixel es hot.
    """
    sigma_summit = min(n_sigma_summit * std_bg, max_sigma_cap_k)
    sigma_scene = min(n_sigma_scene * std_bg, max_sigma_cap_k)
    threshold_summit = max(anomaly_floor_k, sigma_summit)
    threshold_scene = max(anomaly_floor_k, sigma_scene)
    eff_summit = t_bg + threshold_summit
    eff_scene = t_bg + threshold_scene

    is_summit = dist_km <= inner_km
    eff_threshold = np.where(is_summit, eff_summit, eff_scene)
    return roi_mask & ~np.isnan(bt) & (bt > eff_threshold)
