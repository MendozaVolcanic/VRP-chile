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

from typing import Optional

import numpy as np
from scipy.ndimage import generic_filter, convolve

from .constants import C1 as _PLANCK_C1, C2 as _PLANCK_C2


# ---------------------------------------------------------------------------
# S72 F1.2 — Unsuitable-pixel filters (Coppola 2016a SP 426.5).
#
# Paper §267-273 ("Spatial analysis") textual:
#   "all the pixels at the edge of the resampled matrices ... all the pixels
#    with dNTI ... < -0.1 ... and all the pixels with dETI < -0.1 are
#    considered unsuitable for the analysis"
#
# Paper §298-300 ("Spectral analysis"):
#   "Pixels that satisfy Test 1 are flagged as 'active' and subsequently
#    discarded (unsuitable) for further steps"
#
# Estos pixels NO deben contaminar el cómputo de μ/σ de dNTI/dETI usados como
# rama estadística de Tests 2 y 3 (paper §316-325). Drift histórico VRP Chile:
# computábamos μ/σ sobre TODOS los pixels ROI válidos, inflando el desvío
# estándar con outliers negativos (sombras de nube, bordes de granule) y
# pixels Test 1 ya marcados active. Resultado: thresholds estadísticos más
# laxos en escenas con cirrus / edges / hotspots adyacentes → más FPs path D.
# ---------------------------------------------------------------------------

# Default unsuitable floors (Coppola 2016a §267-273, hardcoded del paper).
UNSUITABLE_DNTI_FLOOR_DEFAULT: float = -0.1
UNSUITABLE_DETI_FLOOR_DEFAULT: float = -0.1


def _edge_unsuitable_mask(shape: tuple) -> np.ndarray:
    """Mark 1-pixel border of the matrix as unsuitable.

    Coppola 2016a §267-273: "all the pixels at the edge of the resampled
    matrices are considered unsuitable". El kernel 8-vecinos en el borde
    promedia contra NaN/cval virtual, sesgando dNTI/dETI.
    """
    edge = np.zeros(shape, dtype=bool)
    if shape[0] >= 1:
        edge[0, :] = True
        edge[-1, :] = True
    if shape[1] >= 1:
        edge[:, 0] = True
        edge[:, -1] = True
    return edge


def build_unsuitable_mask(
    roi_mask: np.ndarray,
    dnti: np.ndarray,
    deti: np.ndarray,
    *,
    test1_mask: Optional[np.ndarray] = None,
    dnti_floor: float = UNSUITABLE_DNTI_FLOOR_DEFAULT,
    deti_floor: float = UNSUITABLE_DETI_FLOOR_DEFAULT,
) -> np.ndarray:
    """Coppola 2016a SP 426.5 §267-273 + §298-300 — pixels SUITABLE para μ/σ bg.

    Devuelve la mask de pixels que SÍ entran al cálculo de μ/σ de la rama
    estadística de Tests 2 y 3 (no es la mask de "unsuitable" en sí — es su
    complemento dentro del ROI, conveniente para indexar bg_vals).

    Filtros aplicados (todos del paper, §267-273):
      - Edge pixels (1 píxel de margen)        → unsuitable
      - dNTI < dnti_floor (default -0.1)       → unsuitable
      - dETI < deti_floor (default -0.1)       → unsuitable
      - Test 1 K1 active (§298-300)            → unsuitable (si test1_mask provisto)

    Args:
        roi_mask: bool 2D, True dentro del ROI volcánico.
        dnti: 2D float, dNTI per pixel (puede contener NaN).
        deti: 2D float, dETI per pixel (puede contener NaN).
        test1_mask: bool 2D opcional, pixels que satisfacen Test 1 K1
            (NTI > -0.8 noche). Si None → no se filtran por Test 1
            (backward-compat con callers que no propaguen el flag).
        dnti_floor: umbral dNTI < floor → unsuitable. Default -0.1 (paper).
        deti_floor: umbral dETI < floor → unsuitable. Default -0.1 (paper).

    Returns:
        bool 2D, True donde el pixel ES suitable para entrar a μ/σ bg.
        Pixels que sean NaN en dnti o deti también quedan False
        (no se pueden usar para estadísticas).
    """
    if dnti.shape != deti.shape or dnti.shape != roi_mask.shape:
        raise ValueError(
            f"shape mismatch dnti={dnti.shape} deti={deti.shape} "
            f"roi={roi_mask.shape}"
        )

    edge = _edge_unsuitable_mask(roi_mask.shape)
    # Tratamos NaN como "unsuitable" (no se puede comparar). El operador < con
    # NaN devuelve False — así que dnti<floor solo marca pixels con valor real
    # negativo, no NaN. Igualmente filtramos NaN en el AND final via isfinite.
    dnti_neg = dnti < dnti_floor
    deti_neg = deti < deti_floor
    unsuitable = edge | dnti_neg | deti_neg
    if test1_mask is not None:
        if test1_mask.shape != roi_mask.shape:
            raise ValueError(
                f"test1_mask shape {test1_mask.shape} != roi {roi_mask.shape}"
            )
        unsuitable = unsuitable | test1_mask

    suitable = (
        roi_mask
        & ~unsuitable
        & np.isfinite(dnti)
        & np.isfinite(deti)
    )
    return suitable


# 8-neighbor footprint (3x3 excluyendo centro)
_FOOTPRINT_8N = np.array(
    [[1, 1, 1],
     [1, 0, 1],
     [1, 1, 1]],
    dtype=bool,
)

# Kernel para convolución vectorizada 8-vecinos (center=0, neighbors=1)
_KERNEL_8N = np.array(
    [[1.0, 1.0, 1.0],
     [1.0, 0.0, 1.0],
     [1.0, 1.0, 1.0]],
)


def _nanmean_8neighbors_fast(arr: np.ndarray) -> np.ndarray:
    """Vectorized arithmetic mean of 8-neighbors ignoring NaN.

    Equivalente a `generic_filter(arr, _nanmean_ignore_self, footprint=_FOOTPRINT_8N)`
    pero ~100× más rápido sobre arrays grandes porque evita el callback Python
    por pixel. Crítico para escenas VIIRS 375m (~29M pixels) donde el callback
    lento causa timeout del worker.

    Algoritmo:
        sum_neigh = convolve(where(nan, 0, arr), kernel_3x3_center0)
        count_neigh = convolve(is_valid_int, kernel_3x3_center0)
        mean = sum_neigh / count_neigh   (NaN donde count == 0)

    Args:
        arr: 2D array float con NaN posibles.

    Returns:
        2D array float con la media aritmética de los 8 vecinos (sin centro)
        donde hay >=1 vecino válido. NaN donde no hay ningún vecino válido.
    """
    is_valid = np.isfinite(arr)
    arr_filled = np.where(is_valid, arr, 0.0)
    sum_neigh = convolve(arr_filled, _KERNEL_8N, mode='constant', cval=0.0)
    count_neigh = convolve(is_valid.astype(np.float64), _KERNEL_8N,
                           mode='constant', cval=0.0)
    with np.errstate(invalid='ignore', divide='ignore'):
        mean = np.where(count_neigh > 0, sum_neigh / count_neigh, np.nan)
    return mean


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
    *,
    test1_mask: Optional[np.ndarray] = None,
    apply_unsuitable_filters: bool = False,
    unsuitable_dnti_floor: float = UNSUITABLE_DNTI_FLOOR_DEFAULT,
    unsuitable_deti_floor: float = UNSUITABLE_DETI_FLOOR_DEFAULT,
    deti: Optional[np.ndarray] = None,
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

    # S72 F1.2 — Coppola 2016a SP 426.5 §267-273 + §298-300: pixels unsuitable
    # NO deben aparecer en el hot mask. Para path D contextual los filtros
    # son: borde de matriz, dNTI<-0.1 (irrelevante: el gate (dnti>c1) ya lo
    # excluye), dETI<-0.1 (si deti se provee), y Test 1 K1 active (si flag).
    if apply_unsuitable_filters:
        edge = _edge_unsuitable_mask(roi_mask.shape)
        unsuitable = edge | (dnti < unsuitable_dnti_floor)
        if deti is not None:
            unsuitable = unsuitable | (deti < unsuitable_deti_floor)
        if test1_mask is not None:
            unsuitable = unsuitable | test1_mask
        hot = hot & ~unsuitable
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
    *,
    test1_mask: Optional[np.ndarray] = None,
    apply_unsuitable_filters: bool = False,
    unsuitable_dnti_floor: float = UNSUITABLE_DNTI_FLOOR_DEFAULT,
    unsuitable_deti_floor: float = UNSUITABLE_DETI_FLOOR_DEFAULT,
    deti: Optional[np.ndarray] = None,
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
    # S72 F1.2 — forward unsuitable filters a las dos llamadas contextuales.
    _kwargs = dict(
        test1_mask=test1_mask,
        apply_unsuitable_filters=apply_unsuitable_filters,
        unsuitable_dnti_floor=unsuitable_dnti_floor,
        unsuitable_deti_floor=unsuitable_deti_floor,
        deti=deti,
    )
    hot_summit = contextual_dnti_hot_mask(
        nti, bt, summit_mask, t_bg, c1_summit, bt_sanity_k, **_kwargs,
    )
    hot_scene = contextual_dnti_hot_mask(
        nti, bt, scene_mask, t_bg, c1_scene, bt_sanity_k, **_kwargs,
    )
    return hot_summit | hot_scene


# ---------------------------------------------------------------------------
# S46 Drift #2+#3 — first-pass Tests 2 ∧ 3 + dETI + AND + C2·σ + dual-ROI.
#
# Coppola 2016a SP 426.5 líneas 316-325 dicen textualmente:
#   Test 2:  dNTI > C1   OR   dNTI > μ_dNTI + C2·σ_dNTI
#   Test 3:  dETI > C1   OR   dETI > μ_dETI + C2·σ_dETI
#   pixel active ⇔ Test 2 ∧ Test 3
#
# Tabla 1 (noche): C1_summit=0.003 / C1_scene=0.010, C2_summit=5 / C2_scene=10.
#
# Implementación actual contextual_dnti_hot_mask sólo computa dnti > c1 (drift):
# falta Test 3 (dETI), falta rama OR estadística (μ + C2·σ), falta dual-ROI Tabla 2.
#
# Flag ENABLE_FIRST_PASS_TESTS_2_AND_3 reemplaza paths legacy con conjunción
# Tests 2 ∧ 3 sobre dNTI/dETI. ENABLE_DUAL_ROI_FIRST_PASS activa Tabla 2.
# ---------------------------------------------------------------------------


def first_pass_tests_2_and_3(
    nti: np.ndarray,
    nti_app: np.ndarray,
    bt: np.ndarray,
    roi_mask: np.ndarray,
    dist_km: np.ndarray,
    t_bg: float,
    bt_sanity_k: float,
    *,
    c1_dnti_summit: float = 0.003,
    c1_deti_summit: float = 0.003,
    c2_dnti_summit: float = 5,
    c2_deti_summit: float = 5,
    inner_km: float,
    c1_dnti_scene: Optional[float] = None,
    c1_deti_scene: Optional[float] = None,
    c2_dnti_scene: Optional[float] = None,
    c2_deti_scene: Optional[float] = None,
    min_bg_pixels: int = 10,
    test1_mask: Optional[np.ndarray] = None,
    unsuitable_dnti_floor: float = UNSUITABLE_DNTI_FLOOR_DEFAULT,
    unsuitable_deti_floor: float = UNSUITABLE_DETI_FLOOR_DEFAULT,
) -> tuple:
    """Coppola 2016a SP426.5 first-pass — Tests 2 ∧ 3 conjunción + dual-ROI.

    Paper líneas 316-325:
        Test 2: dNTI > C1  OR  dNTI > μ_dNTI + C2·σ_dNTI
        Test 3: dETI > C1  OR  dETI > μ_dETI + C2·σ_dETI
        active ⇔ Test 2 ∧ Test 3

    Tabla 1 (noche): C1_summit=0.003 / C1_scene=0.010, C2_summit=5 / C2_scene=10.

    Reusa compute_eti_scene_quadratic (eq 4 paper, regresión NTI_bk) y
    _nanmean_8neighbors_fast (kernel mean aritmético, paper línea 242-244).

    Args:
        nti: NTI observado (eq 1 paper).
        nti_app: NTI sintético modelo no-volcánico (eq 2 paper).
        bt: BT MIR (K).
        roi_mask: bool 2D ROI mask.
        dist_km: per-pixel distance to vent (km).
        t_bg, bt_sanity_k: bg stats + floor.
        c1_*_summit, c2_*_summit: thresholds ROI1 (Tabla 1).
        inner_km: radio split summit/scene.
        c1_*_scene, c2_*_scene: thresholds ROI2 si dual; None → uniforme.
        min_bg_pixels: mínimo para μ, σ confiable.
        test1_mask: bool 2D opcional con pixels que satisfacen Test 1 K1
            (NTI > -0.8 noche). Si se provee, esos pixels se filtran del pool
            μ/σ por ser "unsuitable" según Coppola 2016a SP 426.5 §298-300.
            Default None → backward-compat (Test 1 NO filtra el pool bg).
        unsuitable_dnti_floor: pixels con dNTI < floor se excluyen del pool
            μ/σ (Coppola 2016a §267-273). Default -0.1 (paper literal).
        unsuitable_deti_floor: ídem para dETI. Default -0.1.

    Returns:
        (hot_mask: bool 2D, diag: dict con n_first_pass_pixels, mu_dnti,
         sd_dnti, mu_deti, sd_deti, n_bg_used).
    """
    # 1) ETI via helper existente
    mask_valid_eti = roi_mask & np.isfinite(nti) & np.isfinite(nti_app)
    eti = compute_eti_scene_quadratic(nti, nti_app, mask_valid_eti)

    # 2) dNTI y dETI vía 8-neighbor mean
    mean_nti = _nanmean_8neighbors_fast(nti)
    mean_eti = _nanmean_8neighbors_fast(eti)
    dnti = nti - mean_nti
    deti = eti - mean_eti

    # 3) S72 F1.2 — pool bg "suitable" Coppola 2016a §267-273 + §298-300.
    # Excluye edge pixels, dNTI<-0.1, dETI<-0.1, y opcionalmente Test 1 K1 active.
    # Drift previo: bg_mask = roi & isfinite(dnti) & isfinite(deti) — incluía
    # outliers negativos que inflaban σ y aflojaban thresholds μ+C2·σ.
    bg_mask = build_unsuitable_mask(
        roi_mask=roi_mask,
        dnti=dnti,
        deti=deti,
        test1_mask=test1_mask,
        dnti_floor=unsuitable_dnti_floor,
        deti_floor=unsuitable_deti_floor,
    )
    n_bg = int(np.count_nonzero(bg_mask))
    if n_bg < min_bg_pixels:
        return np.zeros_like(roi_mask, dtype=bool), {
            "n_first_pass_pixels": 0, "n_bg_used": n_bg,
            "mu_dnti": None, "sd_dnti": None,
            "mu_deti": None, "sd_deti": None,
        }
    mu_dnti = float(np.mean(dnti[bg_mask]))
    sd_dnti = float(np.std(dnti[bg_mask]))
    mu_deti = float(np.mean(deti[bg_mask]))
    sd_deti = float(np.std(deti[bg_mask]))

    # 4) Threshold por ROI (dual o uniforme).
    # Paper Tests 2/3: `dNTI > C1 OR dNTI > μ + C2·σ` → threshold efectivo es
    # el MENOR de los dos (suficiente con que uno se supere). Equivalente:
    # ``thr = min(C1, μ + C2·σ)``.
    is_summit = dist_km <= inner_km
    dual = c1_dnti_scene is not None

    if dual:
        thr_dnti_sum = min(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti)
        thr_deti_sum = min(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)
        thr_dnti_sce = min(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti)
        thr_deti_sce = min(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti)
        pass_2 = np.where(is_summit, dnti > thr_dnti_sum, dnti > thr_dnti_sce)
        pass_3 = np.where(is_summit, deti > thr_deti_sum, deti > thr_deti_sce)
    else:
        thr_dnti = min(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti)
        thr_deti = min(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)
        pass_2 = dnti > thr_dnti
        pass_3 = deti > thr_deti

    # 5) Conjunción AND + ROI + bt sanity
    hot = (
        roi_mask
        & np.isfinite(dnti) & np.isfinite(deti)
        & pass_2 & pass_3
        & (bt > t_bg + bt_sanity_k)
    )

    diag = {
        "n_first_pass_pixels": int(np.sum(hot)),
        "mu_dnti": mu_dnti, "sd_dnti": sd_dnti,
        "mu_deti": mu_deti, "sd_deti": sd_deti,
        "n_bg_used": n_bg,
        # S46 Task 5: expose eti para second_pass_adjacent reuse (evita recomputar
        # la regresión cuadrática scene-wide que ya hicimos arriba).
        "eti": eti,
    }
    return hot, diag


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


# ---------------------------------------------------------------------------
# H_D8_5 (S37) — helper compartido NTI / NTI_app (Coppola 2016a eqs 1-3).
# Necesario por los 3 procesadores cuando enable_eti_quadratic_scene=true.
# ---------------------------------------------------------------------------


def compute_nti_and_nti_app(
    rad_mir: np.ndarray,
    bt_tir: np.ndarray,
    lambda_mir_um: float,
    lambda_tir_um: float,
) -> tuple:
    """Coppola 2016a SP 426.5 eqs 1-3 — NTI observado + NTI_app sintético.

    Por qué necesitamos ambos: la regresión cuadrática del paso 1
    (compute_eti_scene_quadratic) opera sobre la relación esperada
    ``NTI(NTI_app)`` para pixels "cold" (temperatura homogénea). Pixels
    con fracción hot tienen ``NTI > NTI_app`` y desvían de la regresión —
    ese desvío es exactamente la anomalía ETI que detectamos.

    Definiciones (paper §"NTI and ETI"):

        L_TIR ≡ Planck(λ_TIR, BT_TIR)        # rad TIR observada
        NTI   = (L_MIR_obs - L_TIR) / (L_MIR_obs + L_TIR)         # eq 1
        L_MIR_app(T) = Planck(λ_MIR, T)      # MIR si pixel fuera T uniforme
        NTI_app = (L_MIR_app(BT_TIR) - L_TIR) / (L_MIR_app(BT_TIR) + L_TIR)
                                                                   # eq 3

    Donde T_app = BT_TIR (asumir pixel temp homogénea = la T que el TIR
    "ve"; eq 2 del paper). Por construcción, para un pixel realmente
    homogéneo se cumple ``rad_mir ≈ L_MIR_app(BT_TIR)`` → ``NTI ≈ NTI_app``.

    Para un pixel con sub-pixel hotspot, MIR es mucho más sensible al
    componente hot (Planck crece más rápido en MIR que en TIR a alta T),
    así que ``rad_mir > L_MIR_app(BT_TIR)`` → ``NTI > NTI_app``.

    Constantes Planck reusadas de pipeline.constants (forma L_λ = C1 /
    (λ^5 (e^(C2/λT) - 1))) con λ en μm.

    Args:
        rad_mir: 2D array radiancia MIR observada (W·m⁻²·sr⁻¹·μm⁻¹).
        bt_tir: 2D array brightness temperature TIR (K).
        lambda_mir_um: longitud de onda central MIR en μm (ej 3.959 para
            MODIS B22, 3.74 VIIRS I04, 4.05 VIIRS M13).
        lambda_tir_um: longitud de onda central TIR en μm (ej 11.0 MODIS
            B31, 11.45 VIIRS I05, 10.76 VIIRS M15).

    Returns:
        (nti, nti_app): tuple de 2D arrays float64 con shape igual a
        ``rad_mir``. NaN donde inputs son NaN o donde la fórmula diverge.
    """
    # rad_tir desde BT_TIR (consistencia: tratamos BT como definición
    # invertible de la radiance; rad_tir = Planck(λ_TIR, BT_TIR))
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        rad_tir = _PLANCK_C1 / (
            lambda_tir_um ** 5
            * (np.exp(_PLANCK_C2 / (lambda_tir_um * bt_tir)) - 1.0)
        )
        nti = (rad_mir - rad_tir) / (rad_mir + rad_tir)
        rad_mir_app = _PLANCK_C1 / (
            lambda_mir_um ** 5
            * (np.exp(_PLANCK_C2 / (lambda_mir_um * bt_tir)) - 1.0)
        )
        nti_app = (rad_mir_app - rad_tir) / (rad_mir_app + rad_tir)
    return nti.astype(np.float64), nti_app.astype(np.float64)


# ---------------------------------------------------------------------------
# H_D8_5 (S37) — skeleton funciones algoritmo MIROVA literal Coppola 2016a.
#
# Status: stubs registrados. Lógica pendiente — disparan NotImplementedError
# hasta que se implementen. Tres flags en `_h_d8_5_full.yaml` controlan su
# activación; mientras estén OFF en `mirova_equivalent`, el operacional no
# se ve afectado.
#
# Diseño completo: `docs/superpowers/specs/2026-05-10-d8-cluster-selection.md`.
# Paper referencia: `documentacion/sp426.5.pdf` (Coppola 2016a SP 426.5).
# ---------------------------------------------------------------------------


def compute_eti_scene_quadratic(
    nti: np.ndarray,
    nti_app: np.ndarray,
    mask_valid: np.ndarray,
    *,
    iterative_refit: bool = True,
    max_iter: int = 3,
    outlier_sigma: float = 3.0,
    min_pixels: int = 10,
) -> np.ndarray:
    """Coppola 2016a SP 426.5 eqs 4-5 — ETI scene-wide regresional.

    Reemplaza el background local annulus por una regresión polinomial
    cuadrática sobre la escena completa::

        NTI_bk = a · NTI²_app + b · NTI_app + c        (eq 4)
        ETI    = NTI - NTI_bk                          (eq 5)

    Los coeficientes ``a, b, c`` se ajustan por imagen (NO fijos). Estrategia:

    1. **Single-pass polyfit** orden 2 (``numpy.polyfit``) sobre todos los
       pixels válidos. Baseline robusta de la relación esperada NTI(NTI_app).
    2. **Iterative re-fit** (cuando ``iterative_refit=True``): hasta
       ``max_iter`` iteraciones, identificar outliers donde
       ``|nti - NTI_bk| > outlier_sigma · σ(residuals)`` y re-fit
       excluyéndolos. Equivalente práctico al RANSAC del paper para
       evitar que los hot pixels reales distorsionen el ajuste del bg.

    Resultado: ETI alto = pixel anómalo vs el comportamiento esperado de
    la escena. Los pixels que el paper describe como "active" son
    exactamente los que sobresalen de la regresión.

    Por qué importa para clon MIROVA: nuestro pipeline usa background local
    annulus (radio 5-25 km). Funciona para contraste local pero el paper
    opera scene-wide para que el "esperado" sea consistente entre regiones.

    Args:
        nti: 2D array NTI observado por pixel.
        nti_app: 2D array NTI sintético assuming pixel temp homogéneo
            (computado de BT_TIR vía Planck_MIR, eqs 2-3 del paper).
        mask_valid: bool 2D array, True donde pixel es analizable.
        iterative_refit: si True, refina excluyendo outliers >outlier_sigma·σ.
        max_iter: máximo de iteraciones de refit (default 3, típicamente
            converge en 1-2).
        outlier_sigma: umbral en sigmas de residual para marcar outlier
            (default 3.0).
        min_pixels: mínimo de pixels válidos para intentar el fit. Si la
            scene tiene menos, devuelve array de NaN (signal "fit unsafe").
            Default 10.

    Returns:
        2D array ETI = NTI - NTI_bk, shape igual a ``nti``. NaN donde
        ``mask_valid`` es False O donde no se pudo ajustar el modelo.
    """
    eti = np.full_like(nti, np.nan, dtype=np.float64)

    finite_mask = mask_valid & np.isfinite(nti) & np.isfinite(nti_app)
    n_valid = int(np.count_nonzero(finite_mask))
    if n_valid < min_pixels:
        return eti

    x = nti_app[finite_mask].astype(np.float64)
    y = nti[finite_mask].astype(np.float64)

    # Pass 1 — fit inicial sobre todos los pixels válidos
    try:
        coeffs = np.polyfit(x, y, 2)  # [a, b, c]
    except (np.linalg.LinAlgError, ValueError):
        return eti

    # Pass 2..max_iter — iterative re-fit excluyendo outliers
    if iterative_refit:
        inlier_idx = np.arange(len(x))
        for _ in range(max_iter):
            x_in = x[inlier_idx]
            y_in = y[inlier_idx]
            residuals = y_in - np.polyval(coeffs, x_in)
            sigma = np.std(residuals)
            if sigma == 0 or not np.isfinite(sigma):
                break
            new_inliers = np.where(np.abs(residuals) <= outlier_sigma * sigma)[0]
            if len(new_inliers) == len(inlier_idx):
                break  # converged
            inlier_idx = inlier_idx[new_inliers]
            if len(inlier_idx) < min_pixels:
                break  # too few inliers — keep last good coeffs
            try:
                coeffs = np.polyfit(x[inlier_idx], y[inlier_idx], 2)
            except (np.linalg.LinAlgError, ValueError):
                break

    # Evaluar NTI_bk = a·NTI²_app + b·NTI_app + c sobre TODO el grid
    nti_bk = np.polyval(coeffs, nti_app)
    eti_full = nti - nti_bk
    eti[mask_valid] = eti_full[mask_valid]
    return eti


def second_pass_adjacent(
    nti: np.ndarray,
    eti: np.ndarray,
    active_mask: np.ndarray,
    *,
    c1_dnti: float,
    c1_deti: float,
    c2_dnti: float,
    c2_deti: float,
    is_summit: np.ndarray = None,
    c1_dnti_scene: float = None,
    c1_deti_scene: float = None,
    c2_dnti_scene: float = None,
    c2_deti_scene: float = None,
    min_bg_pixels: int = 10,
) -> np.ndarray:
    """Coppola 2016a SP 426.5 paso 5 — second-pass adyacente.

    Tras detectar pixels active en el primer pass, recomputar dNTI y dETI
    EXCLUYENDO esos pixels active del cómputo de la media de 8-vecinos
    (un active vecino contamina la media bajando el contraste de pixels
    adyacentes y los hace pasar desapercibidos en el primer pass).
    Re-aplicar Tests 2 y 3 sobre las matrices nuevas. El cluster crece
    orgánicamente recapturando los pixels marginales perdidos.

    Cita exacta del paper (líneas 347-356)::

        "active pixels may strongly modify the average values of their
        surroundings, with a consequent decrease in the dNTI and dETI
        values of adjacent pixels. To avoid this problem, step 2 (spatial
        analysis) is performed a SECOND TIME, being particularly careful
        to eliminate all of the 'active' pixels already detected."

    Tests 2 y 3 (paper líneas 311-315), aplicados en conjunción (AND)::

        Test 2:  dNTI > C1   OR   dNTI > μ_dNTI + C2·σ_dNTI
        Test 3:  dETI > C1   OR   dETI > μ_dETI + C2·σ_dETI
        pixel active ⇔ Test 2 ∧ Test 3

    μ y σ se computan sobre pixels NO active (background regional) de la
    escena (no del primer pass — la idea es separar señal de fondo).

    Dual-ROI: cuando ``is_summit`` y los thresholds ``*_scene`` se proveen,
    se aplican umbrales distintos según Tabla 1 del paper (5σ summit /
    10σ scene noche). Cuando no, se aplica el set único uniforme.

    Args:
        nti: 2D array NTI original (no dNTI). El second-pass recalcula
            dNTI internamente.
        eti: 2D array ETI original. El second-pass recalcula dETI.
        active_mask: bool 2D, True donde primer pass marcó active.
            Estos pixels se excluyen del cómputo de la media de vecinos.
        c1_dnti, c1_deti: umbrales absolutos summit (o uniforme).
        c2_dnti, c2_deti: multiplicadores σ summit (o uniforme).
        is_summit: bool 2D opcional. True en ROI summit (paper Tabla 1).
        c1_dnti_scene, c1_deti_scene: umbrales absolutos scene (Tabla 1).
        c2_dnti_scene, c2_deti_scene: multiplicadores σ scene.
        min_bg_pixels: mínimo pixels bg para computar μ, σ confiable.
            Si menos, devuelve active_mask sin cambios.

    Returns:
        bool 2D con pixels active tras recapture (incluye primer pass +
        nuevos). Shape igual a ``nti``.
    """
    # 1) Excluir active pixels del cómputo de mean: ponerlos a NaN.
    nti_for_mean = np.where(active_mask, np.nan, nti)
    eti_for_mean = np.where(active_mask, np.nan, eti)

    # 2) 8-neighbor mean ignorando NaN (vectorized — _nanmean_8neighbors_fast).
    #    Equivalente al generic_filter+_nanmean_ignore_self pero ~100× más rápido
    #    sobre escenas grandes (VIIRS 375m ~29M pixels). Crítico para que el
    #    workflow A/B no haga timeout per granule.
    mean_nti_neigh = _nanmean_8neighbors_fast(nti_for_mean)
    mean_eti_neigh = _nanmean_8neighbors_fast(eti_for_mean)
    dnti = nti - mean_nti_neigh
    deti = eti - mean_eti_neigh

    # 3) μ, σ del background (no active, finito).
    bg_mask = (~active_mask) & np.isfinite(dnti) & np.isfinite(deti)
    if int(np.count_nonzero(bg_mask)) < min_bg_pixels:
        return active_mask.copy()
    mu_dnti = float(np.mean(dnti[bg_mask]))
    sd_dnti = float(np.std(dnti[bg_mask]))
    mu_deti = float(np.mean(deti[bg_mask]))
    sd_deti = float(np.std(deti[bg_mask]))

    # 4) Threshold por ROI (dual o uniforme).
    dual = (is_summit is not None
            and c1_dnti_scene is not None and c1_deti_scene is not None
            and c2_dnti_scene is not None and c2_deti_scene is not None)
    # Paper Tests 2/3 (líneas 316-325): `dNTI > C1 OR dNTI > μ + C2·σ` →
    # threshold efectivo es el MENOR de los dos (basta superar uno). Equivalente:
    # ``thr = min(C1, μ + C2·σ)``. Bug fix S46 Task 5: antes usábamos `max`
    # (AND lógico), ahora `min` (OR lógico paper-correct). Alineado con
    # first_pass_tests_2_and_3 líneas 290-300.
    if dual:
        thr_dnti_sum = min(c1_dnti, mu_dnti + c2_dnti * sd_dnti)
        thr_deti_sum = min(c1_deti, mu_deti + c2_deti * sd_deti)
        thr_dnti_sce = min(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti)
        thr_deti_sce = min(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti)
        pass_2 = np.where(is_summit, dnti > thr_dnti_sum, dnti > thr_dnti_sce)
        pass_3 = np.where(is_summit, deti > thr_deti_sum, deti > thr_deti_sce)
    else:
        thr_dnti = min(c1_dnti, mu_dnti + c2_dnti * sd_dnti)
        thr_deti = min(c1_deti, mu_deti + c2_deti * sd_deti)
        pass_2 = dnti > thr_dnti
        pass_3 = deti > thr_deti

    # 5) Pixel "newly active" si pasa Test 2 ∧ Test 3 y es válido.
    newly_active = (pass_2 & pass_3
                    & np.isfinite(dnti) & np.isfinite(deti))

    return active_mask | newly_active


# ---------------------------------------------------------------------------
# S46 Drift #1a — combine_hot_paths helper.
#
# Coppola 2016a SP 426.5 línea 298-300 dice textualmente:
#   "Pixels that satisfy Test 1 are flagged as 'active' and subsequently
#    discarded (unsuitable) for further steps"
#
# Test 1 K1 (NTI > -0.8 noche / NTI > -0.6 día) es una MÁSCARA DE SATURACIÓN
# que retira pixels del cómputo de mean/std del background — NO un path de
# detección reportable. Nuestro código actual mete `nti_path_hot` al OR del
# hot_mask, lo cual es un drift respecto al paper.
#
# Flag `enable_test1_k1_retire_from_hot_mask` (default OFF): cuando ON,
# `nti_path_hot` NO contribuye al hot_mask reportable. Su cálculo se mantiene
# para diagnóstico (qué pixels eran "saturados" Test 1 K1).
# ---------------------------------------------------------------------------


def combine_hot_paths(
    bt_path_hot: np.ndarray,
    nti_path_hot: np.ndarray,
    dnti_ctx_hot: np.ndarray,
    test1_hot: np.ndarray,
    *,
    enable_test1_k1_retire_from_hot_mask: bool = False,
    nti_rel_hot: np.ndarray = None,
    eti_path_hot: np.ndarray = None,
) -> np.ndarray:
    """Combina paths legacy + nuevos drift flags (S46 drift #1a).

    Drift #1a: si flag ON, nti_path_hot NO entra al OR (Coppola 2016a literal —
    Test 1 K1 es saturation mask, NO hotspot reportable; SP426.5:298-300).

    Args:
        bt_path_hot, nti_path_hot, dnti_ctx_hot, test1_hot: bool 2D masks.
        enable_test1_k1_retire_from_hot_mask: flag drift #1a.
        nti_rel_hot, eti_path_hot: opcional, default None → zeros.

    Returns:
        bool 2D hot_mask combinado.
    """
    if nti_rel_hot is None:
        nti_rel_hot = np.zeros_like(bt_path_hot)
    if eti_path_hot is None:
        eti_path_hot = np.zeros_like(bt_path_hot)

    if enable_test1_k1_retire_from_hot_mask:
        # Drift #1a: nti_path_hot NO contribuye al hot_mask
        return bt_path_hot | dnti_ctx_hot | test1_hot | nti_rel_hot | eti_path_hot
    else:
        return bt_path_hot | nti_path_hot | dnti_ctx_hot | test1_hot | nti_rel_hot | eti_path_hot


# ---------------------------------------------------------------------------
# S46 Drift #1b — bg_vals excluye Test 1 K1 active pixels.
#
# Coppola 2016a SP 426.5 línea 352-356 dice textualmente:
#   "active pixels may strongly modify the average values of their surroundings,
#    with a consequent decrease in the dNTI and dETI values of adjacent pixels.
#    To avoid this problem, step 2 (spatial analysis) is performed a second time,
#    being particularly careful to eliminate all of the 'active' pixels already
#    detected"
#
# Drift #1b: nuestro bg_vals (background ring usado para t_bg/std_bg) actualmente
# NO excluye pixels Test 1 K1 active. Si hay anomalías dentro o cerca del ring,
# t_bg/std_bg se contaminan y los umbrales N·σ inflan o pierden señal real.
#
# Flag `enable_test1_k1_bg_exclude` (default OFF): cuando ON, computamos bg
# sobre pixels NTI <= NTI_K1 (es decir, excluimos los Test 1 K1 active del bg).
# ---------------------------------------------------------------------------


def compute_bg_stats(
    bt: np.ndarray,
    bg_mask: np.ndarray,
    *,
    nti: Optional[np.ndarray] = None,
    nti_k1_threshold: float = -0.8,
    enable_test1_k1_bg_exclude: bool = False,
    min_bg_pixels: int = 10,
) -> tuple:
    """Compute t_bg (median), std_bg, n_bg sobre bg_mask.

    Drift #1b (Coppola 2016a SP426.5:352-356): si enable_test1_k1_bg_exclude
    True, excluye pixels Test 1 K1 active del bg_vals para alinear con paper
    "second time... eliminate all of the 'active' pixels already detected".

    Args:
        bt: 2D array BT (K).
        bg_mask: bool 2D, True en bg ring.
        nti: 2D array NTI (requerido si enable_test1_k1_bg_exclude).
        nti_k1_threshold: K1 noche (-0.8) o día (-0.6).
        enable_test1_k1_bg_exclude: flag drift #1b.
        min_bg_pixels: mínimo bg para confiabilidad.

    Returns:
        (t_bg, std_bg, n_bg) o (None, None, n_bg_count) si <min_bg_pixels.
    """
    effective_bg_mask = bg_mask & ~np.isnan(bt)

    if enable_test1_k1_bg_exclude:
        if nti is None:
            raise ValueError(
                "nti requerido si enable_test1_k1_bg_exclude=True"
            )
        test1_k1_active = (nti > nti_k1_threshold) & ~np.isnan(nti)
        effective_bg_mask = effective_bg_mask & ~test1_k1_active

    bg_vals = bt[effective_bg_mask]
    n_bg = int(len(bg_vals))
    if n_bg < min_bg_pixels:
        return None, None, n_bg

    t_bg = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))


# ---------------------------------------------------------------------------
# F66 Dual-bg consistency gate (S79 P1, design doc 2026-05-26)
#
# Filtra pixels donde el "calor" es un artefacto del background ring 5-25 km
# (lago tibio rodeado de terreno frío distante) vs señal espacial real.
#
# MIROVA-faithful: Coppola 2024 L1129 + Coppola 2016a L240-249 + L357-359 +
# Campus 2024 L119-124 verbatim usan background local (vecinos inmediatos
# 3×3 = 8-conn) — nuestro pipeline usa ring annular, que es un drift.
# Este helper actúa como gate de consistencia secundario PRESERVANDO la
# arquitectura ring (gate primario sin cambios).
#
# Edge cases:
#   - Todos vecinos hot/NaN → t_bg_local = NaN → fallback ring (no vetar)
#   - Algunos vecinos NaN → mean(válidos)
#   - Pixel borde imagen → vecinos truncados, mismo fallback
# ---------------------------------------------------------------------------


def apply_f66_consistency_gate(
    bt: np.ndarray,
    hot_mask: np.ndarray,
    *,
    kernel_size: int = 3,
    dt_min: float = 5.0,
) -> tuple[np.ndarray, dict]:
    """Apply F66 dual-bg consistency gate sobre hot_mask del ring.

    Para cada pixel marcado hot por gate primario (ring 5-25 km), computa
    t_bg_local con kernel 3×3 (vecinos inmediatos) excluyendo otros hot y
    NaN. Si ΔT_local = bt - t_bg_local < dt_min → vetar.

    Política edge case: si t_bg_local es NaN (todos vecinos hot o NaN) →
    fallback ring (no vetar) para preservar recall en lava extendida.

    Args:
        bt: 2D array BT en K.
        hot_mask: bool 2D, True para pixels marcados hot por gate primario.
        kernel_size: lado kernel cuadrado (impar). Default 3 = 8 vecinos.
        dt_min: ΔT_local mínimo en K para que pixel pase el gate.

    Returns:
        (hot_mask_filtered, diag_dict) donde diag_dict tiene:
            n_evaluated: pixels que entraron al gate (= hot_mask.sum())
            n_vetoed: pixels rechazados por ΔT < dt_min
            n_nan_fallback: pixels con t_bg_local NaN (passed por fallback)
    """
    from pipeline.vrp_regimes import compute_local_background

    hot_rows_arr, hot_cols_arr = np.where(hot_mask)
    n_evaluated = int(hot_rows_arr.size)

    if n_evaluated == 0:
        return hot_mask.copy(), {
            "n_evaluated": 0,
            "n_vetoed": 0,
            "n_nan_fallback": 0,
        }

    t_bg_locals = compute_local_background(
        bt, hot_rows_arr.tolist(), hot_cols_arr.tolist(),
        kernel_size=kernel_size,
    )
    t_bg_locals_arr = np.asarray(t_bg_locals, dtype=float)
    delta_t_local = bt[hot_rows_arr, hot_cols_arr] - t_bg_locals_arr
    nan_fallback = np.isnan(t_bg_locals_arr)
    passes = (delta_t_local >= dt_min) | nan_fallback

    hot_mask_out = np.zeros_like(hot_mask)
    hot_mask_out[hot_rows_arr[passes], hot_cols_arr[passes]] = True

    diag = {
        "n_evaluated": n_evaluated,
        "n_vetoed": int((~passes).sum()),
        "n_nan_fallback": int(nan_fallback.sum()),
    }
    return hot_mask_out, diag
    return t_bg, std_bg, n_bg
