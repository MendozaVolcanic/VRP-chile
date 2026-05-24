"""TIRVolcH — Thermal Infrared Recognition of Volcanic Hotspots (detector).

Implementación de Aveni 2024 RSE (doi:10.1016/j.rse.2024.114388).
Detector single-band TIR (VIIRS I5, 11.45 µm, 375 m) para hotspot
identification con sensibilidad declarada 0.5 K above background y FP rate
~1.8% (paper abstract).

**STATUS S75 (Task F31 A1)**: módulo NUEVO standalone, NO integrado a
process_viirs.py (eso es Task A2). Valores numéricos del paper extraídos
desde Vault note `aveni2024tirvolch.md` (confidence:high, explored 2026-04-21).
PDF Aveni 2024 RSE local en `documentacion/Aveni_2024_TIRVolcH_RSE.pdf`,
pending verbatim re-check para A35 upgrade a HIGH-VERIFIED.

**Rol dentro de F31**: pre-requisito operacional del módulo `vrptir.py`.
TIRVolcH identifica qué pixels son hotspot-contaminated; VRPTIR (Aveni 2025
GRL Eq.8) cuantifica VRP sobre esos pixels en rango 300-600 K.

**Algoritmo (7 pasos, Vault note aveni2024tirvolch §Algoritmo)**:
1. Gate absoluto: OBS > 313.15 K (40 °C).
2. Residuo: RES = OBS − REF (REF = stack mensual nocturno cloud-free).
3. Percentil 99.5 sobre RES (ABSDT 10-20 K, ABSCL -10 a 0 K, condicionales).
4. Z-score > 7 sobre RES (estricto vs n_sigma_tir=4 actual).
5. Land-dominated: clustering Euclidean OBS-vs-REF con PolyROI + buffer 0.5-4 K.
6. Water-dominated: contextual 10×σ sobre media o p99.95.
7. VSROI volcán-específico (sensibilidad ajustada a baseline local).

**Quality control**:
- R² > 0.5 sobre REF como proxy quality vs nube.
- MAD ×3 para outlier removal del stack mensual.
- Grilla 134×134 UTM ~2500 km².
- 4 ROIs concéntricas: 1, 5, 12.5, 25 km del vent.

**Validación paper**: Vulcano 2021-22 fumarólica, Agung 2017 pre-dome,
La Palma 2021 lava cooling. Volcán chileno mencionado: **Copahue**
(casos adicionales). Sin volcán chileno Tier A formal — caveat operacional.

**Caveat A35 (jerarquía fuentes)**: valores extraídos de Vault note
confidence:high. PDF disponible localmente — pending verbatim cross-check
antes de integración operacional (Task A2). Si discrepa con paper, prevalece
PDF.

Refs:
- Aveni S., Laiolo M., Campus A., Massimetti F., Coppola D. (2024).
  TIRVolcH. RSE 311, 114388. doi:10.1016/j.rse.2024.114388
- Vault/10_Bibliografia/99_por_clasificar/aveni2024tirvolch.md (confidence:high)
- pipeline/vrptir.py (módulo VRPTIR Aveni 2025 GRL, ya integrado S74)
- docs/F31_AVENI_VRPTIR_PLAN_S74.md — plan F31 completo
- CLAUDE.md A35 (jerarquía autoridad fuentes)
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Constantes del paper (Vault confidence:high; PDF verify PENDING para A2)
# ---------------------------------------------------------------------------

# Paso 1: gate absoluto OBS > 313.15 K (40 °C) — paper §3, Vault §Algoritmo
TIRVOLCH_T_ABS_MIN_K: float = 313.15

# Paso 4: Z-score > 7 sobre residuo (estricto, paper §3) — Vault §Algoritmo
TIRVOLCH_Z_THRESHOLD: float = 7.0

# Sensibilidad declarada (abstract): ΔBT ≥ 0.5 K above background
TIRVOLCH_DT_MIN_K: float = 0.5

# Quality control REF stack mensual
TIRVOLCH_R2_MIN: float = 0.5     # R² > 0.5 vs cloud contamination
TIRVOLCH_MAD_FACTOR: float = 3.0  # outlier removal MAD ×3

# Water-dominated branch (Paso 6): 10×σ sobre media contextual
TIRVOLCH_WATER_SIGMA_FACTOR: float = 10.0

# Buffers PolyROI cluster land-dominated (Paso 5)
TIRVOLCH_LAND_BUFFER_MIN_K: float = 0.5
TIRVOLCH_LAND_BUFFER_MAX_K: float = 4.0

# Grilla y ROIs (estructurales)
TIRVOLCH_GRID_SIZE_PX: int = 134  # ~2500 km² UTM
TIRVOLCH_ROI_RADII_KM: tuple[float, ...] = (1.0, 5.0, 12.5, 25.0)

# FP rate declarado (referencia auditorías)
TIRVOLCH_FP_RATE_DECLARED: float = 0.018  # ~1.8% abstract


# ---------------------------------------------------------------------------
# Función principal del detector
# ---------------------------------------------------------------------------

def detect_tirvolch(
    bt_tir: np.ndarray,
    baseline_mean: np.ndarray,
    baseline_std: np.ndarray,
    threshold_k_min: float = TIRVOLCH_DT_MIN_K,
    n_sigma_temporal: float = TIRVOLCH_Z_THRESHOLD,
    t_abs_min_k: float = TIRVOLCH_T_ABS_MIN_K,
) -> np.ndarray:
    """Aplica los gates principales de TIRVolcH (Aveni 2024 RSE).

    Combina Paso 1 (gate absoluto), Paso 2 (residuo) y Paso 4 (Z-score
    temporal) del algoritmo. Devuelve máscara booleana de candidatos
    hotspot. NO implementa Pasos 5-7 (PolyROI / water-vs-land / VSROI),
    que son refinamientos espaciales delegados a Task A2 (integración
    process_viirs.py).

    Parámetros
    ----------
    bt_tir : np.ndarray (2D, K)
        Brightness temperature TIR observada (VIIRS I5 sugerido).
        NaN permitido — propagado como False.
    baseline_mean : np.ndarray
        REF mensual cloud-free, misma shape que bt_tir.
    baseline_std : np.ndarray
        σ temporal del stack REF, misma shape. Debe ser > 0 donde se
        evalúe; NaN/0 → pixel descartado.
    threshold_k_min : float
        Sensibilidad mínima ΔBT (default 0.5 K, paper abstract).
    n_sigma_temporal : float
        Z-score threshold sobre residuo (default 7.0, paper §3 Paso 4).
    t_abs_min_k : float
        Gate absoluto OBS (default 313.15 K = 40 °C, paper §3 Paso 1).

    Returns
    -------
    np.ndarray, dtype=bool, misma shape que bt_tir
        True donde el pixel es candidato hotspot tras Pasos 1+2+4.

    Notes
    -----
    Implementa los gates "temporal and contextual analysis" base. La
    rama contextual espacial (ring de vecinos, Paso 6 water-dominated)
    se computa con `compute_contextual_ring()`.
    """
    bt = np.asarray(bt_tir, dtype=float)
    ref = np.asarray(baseline_mean, dtype=float)
    sigma = np.asarray(baseline_std, dtype=float)

    if bt.shape != ref.shape or bt.shape != sigma.shape:
        raise ValueError(
            f"Shapes mismatch: bt={bt.shape} ref={ref.shape} sigma={sigma.shape}"
        )

    # Mask NaN propagation
    finite = np.isfinite(bt) & np.isfinite(ref) & np.isfinite(sigma) & (sigma > 0)

    # Paso 1: gate absoluto OBS > 313.15 K
    gate_abs = bt > t_abs_min_k

    # Paso 2: residuo RES = OBS − REF
    res = np.where(finite, bt - ref, np.nan)

    # Sensibilidad mínima ΔBT (paper abstract)
    gate_dt = res >= threshold_k_min

    # Paso 4: Z-score temporal > n_sigma
    with np.errstate(invalid="ignore", divide="ignore"):
        zscore = np.where(finite, res / sigma, np.nan)
    gate_z = zscore >= n_sigma_temporal

    return finite & gate_abs & gate_dt & gate_z


# ---------------------------------------------------------------------------
# Construcción del baseline temporal (Paso 2 — REF stack mensual)
# ---------------------------------------------------------------------------

def compute_temporal_baseline(
    history_bt_array: np.ndarray,
    mad_factor: float = TIRVOLCH_MAD_FACTOR,
) -> tuple[np.ndarray, np.ndarray]:
    """Construye baseline REF mensual cloud-free + σ temporal.

    Aveni 2024 §3 Paso 2: REF se arma stackeando pasadas nocturnas
    cloud-free del mismo mes, removiendo outliers por MAD ×3 (Vault
    §Filtros de calidad).

    Parámetros
    ----------
    history_bt_array : np.ndarray (N, H, W)
        Stack de N escenas nocturnas cloud-free del mismo mes para los
        últimos años. Pixels nube → NaN antes de pasar al stack.
    mad_factor : float
        Factor MAD para outlier removal (default 3.0, paper).

    Returns
    -------
    baseline_mean : np.ndarray (H, W)
        Mediana robusta del stack (post-MAD).
    baseline_std : np.ndarray (H, W)
        σ temporal robusta (MAD × 1.4826 ≈ std equivalente gaussiana).

    Notes
    -----
    Implementación robusta clásica: la mediana y el MAD son resistentes
    a cloud-leak residual. Paper no detalla cuántos años de history
    requiere — Vault §Performance dice 2012-2023 (10+ años). Para Chile,
    A35 caveat: nieve estacional puede romper la stationarity asumida
    (Vault §Preguntas abiertas — REF estacional vs mensual). Pending
    validación empírica Task A2/A3.
    """
    arr = np.asarray(history_bt_array, dtype=float)
    if arr.ndim != 3:
        raise ValueError(f"Expected (N,H,W), got shape {arr.shape}")

    n = arr.shape[0]
    if n < 2:
        raise ValueError(f"Need at least 2 frames for baseline, got {n}")

    # Median temporal (robusto a cloud-leak residual)
    median = np.nanmedian(arr, axis=0)

    # MAD = median(|x - median|), escalado por 1.4826 para σ gaussiana eq.
    abs_dev = np.abs(arr - median[None, :, :])
    mad = np.nanmedian(abs_dev, axis=0)
    sigma_robust = mad * 1.4826

    # Outlier removal: pixels con |x - median| > mad_factor * mad → NaN
    threshold = mad_factor * mad
    # broadcast threshold a stack shape
    is_outlier = abs_dev > threshold[None, :, :]
    arr_clean = np.where(is_outlier, np.nan, arr)

    # Recompute mean/std post-cleanup
    baseline_mean = np.nanmean(arr_clean, axis=0)
    baseline_std = np.nanstd(arr_clean, axis=0, ddof=0)

    # Floor σ a sigma_robust donde quedó NaN/0 (evita div-by-zero downstream)
    bad = ~np.isfinite(baseline_std) | (baseline_std <= 0)
    baseline_std = np.where(bad, sigma_robust, baseline_std)

    return baseline_mean, baseline_std


# ---------------------------------------------------------------------------
# Análisis contextual espacial (ring de vecinos)
# ---------------------------------------------------------------------------

def compute_contextual_ring(
    bt_tir: np.ndarray,
    row: int,
    col: int,
    ring_radius_px: int = 5,
    inner_exclude_px: int = 1,
) -> dict:
    """Calcula estadísticas del ring contextual alrededor de un pixel.

    Implementa la rama contextual del Paso 6 (water-dominated) y soporta
    la decisión land-vs-water del Paso 5. Devuelve mean/std/p99.95 del
    anillo de vecinos excluyendo el pixel central (y opcionalmente un
    núcleo interior si hay cluster).

    Parámetros
    ----------
    bt_tir : np.ndarray (2D)
        BT TIR de la escena.
    row, col : int
        Coordenadas del pixel a evaluar.
    ring_radius_px : int
        Radio externo del ring (default 5 px).
    inner_exclude_px : int
        Radio interno excluido (default 1 px = solo centro).

    Returns
    -------
    dict con keys: 'mean', 'std', 'p9995', 'n_valid', 'center_dt'.
        'center_dt' = bt_tir[row,col] − mean del ring.
        Si el ring queda fuera del array o sin pixels válidos, devuelve
        NaN/0 según corresponda.

    Notes
    -----
    Aveni 2024 §3 Paso 6 usa "10×σ sobre la media o p99.95 del ring".
    Esta función provee los building blocks; el threshold decision se
    aplica fuera (e.g. en Task A2 integración).
    """
    arr = np.asarray(bt_tir, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape {arr.shape}")

    h, w = arr.shape
    if not (0 <= row < h and 0 <= col < w):
        return {"mean": np.nan, "std": np.nan, "p9995": np.nan,
                "n_valid": 0, "center_dt": np.nan}

    r0 = max(0, row - ring_radius_px)
    r1 = min(h, row + ring_radius_px + 1)
    c0 = max(0, col - ring_radius_px)
    c1 = min(w, col + ring_radius_px + 1)

    patch = arr[r0:r1, c0:c1].copy()

    # Build mask: keep ring, exclude center core
    rr, cc = np.ogrid[r0:r1, c0:c1]
    dist_px = np.sqrt((rr - row) ** 2 + (cc - col) ** 2)
    ring_mask = (dist_px > inner_exclude_px) & (dist_px <= ring_radius_px)

    ring_vals = patch[ring_mask]
    ring_vals = ring_vals[np.isfinite(ring_vals)]

    if ring_vals.size == 0:
        return {"mean": np.nan, "std": np.nan, "p9995": np.nan,
                "n_valid": 0, "center_dt": np.nan}

    mean = float(np.mean(ring_vals))
    std = float(np.std(ring_vals, ddof=0))
    p9995 = float(np.percentile(ring_vals, 99.95))
    center = float(arr[row, col]) if np.isfinite(arr[row, col]) else np.nan
    center_dt = center - mean if np.isfinite(center) else np.nan

    return {
        "mean": mean,
        "std": std,
        "p9995": p9995,
        "n_valid": int(ring_vals.size),
        "center_dt": center_dt,
    }
