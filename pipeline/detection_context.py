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

from .constants import C1 as _PLANCK_C1, C2 as _PLANCK_C2


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

    # 2) 8-neighbor mean ignorando NaN (footprint excluye el centro).
    mean_nti_neigh = generic_filter(
        nti_for_mean, _nanmean_ignore_self,
        footprint=_FOOTPRINT_8N, mode='constant', cval=np.nan,
    )
    mean_eti_neigh = generic_filter(
        eti_for_mean, _nanmean_ignore_self,
        footprint=_FOOTPRINT_8N, mode='constant', cval=np.nan,
    )
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
    if dual:
        thr_dnti_sum = max(c1_dnti, mu_dnti + c2_dnti * sd_dnti)
        thr_deti_sum = max(c1_deti, mu_deti + c2_deti * sd_deti)
        thr_dnti_sce = max(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti)
        thr_deti_sce = max(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti)
        pass_2 = np.where(is_summit, dnti > thr_dnti_sum, dnti > thr_dnti_sce)
        pass_3 = np.where(is_summit, deti > thr_deti_sum, deti > thr_deti_sce)
    else:
        thr_dnti = max(c1_dnti, mu_dnti + c2_dnti * sd_dnti)
        thr_deti = max(c1_deti, mu_deti + c2_deti * sd_deti)
        pass_2 = dnti > thr_dnti
        pass_3 = deti > thr_deti

    # 5) Pixel "newly active" si pasa Test 2 ∧ Test 3 y es válido.
    newly_active = (pass_2 & pass_3
                    & np.isfinite(dnti) & np.isfinite(deti))

    return active_mask | newly_active
