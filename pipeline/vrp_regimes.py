# ════════════════════════════════════════════════════════════════════
# FICHA SDA · vrp_regimes.py  ·  SDA: VRP Chile (clon MIROVA)  ·  ID: VRP-CL
# Objetivo      : Cuantificar la potencia radiada volcánica (VRP) para apoyar
#                 la clasificación de actividad térmica (alerta volcánica OVDAS).
# Lógica        : Para cada anomalía térmica, estima el fondo local y aplica la
#                 ecuación de Wooster/Coppola según el régimen del rasgo térmico
#                 (lava fresca, lava lake sub-pixel, lago hidrotermal).
# Modelo/método : Reglas físicas determinísticas (Planck/Wooster, Coppola 2016/2024).
#                 NO es caja negra — la lógica es auditable (cumple punto 5.5 Res. 372).
# Datos entrada : Radiancia MODIS (MOD14/MYD14) y VIIRS. SIN datos personales.
# Variables     : VRP (MW), BT del píxel, T de fondo (corona/local), área del píxel.
# Limitaciones  : Saturación de píxel, contaminación por lago/nieve, falsos positivos
#                 por incendios; fondo regional como fallback degrada explícitamente.
# Refs/datos    : Coppola et al. 2016a, Coppola 2024 (Springer). Datos de
#                 entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""VRP regímenes diferenciados según Coppola 2024 chapter Springer.

3 regímenes según rango T del VTF (volcanic thermal feature):
- R1: Lava fresca >600K → Wooster MIR Eq.17 (ya implementado en process_*.py)
- R2: Lava lake magmático sub-pixel ~1000K → Eq.16 Burgi-Coppola (este módulo)
- R3: Crater lake hidrotermal <600K → Eq.25 Ruapehu (pendiente)

Design doc: docs/superpowers/specs/2026-05-17-vrp-three-regimes-design.md
HYPOTHESIS_LOG: H_S52_VIIRS375_OVERDETECT + H_S53_R2_LAVA_LAKE_EQ16
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy.ndimage import binary_dilation

from pipeline.constants import SIGMA, C1, C2


def compute_local_background(
    bt_grid: np.ndarray,
    hot_rows: Sequence[int],
    hot_cols: Sequence[int],
    kernel_size: int = 3,
) -> list[float]:
    """Estima T_bk localmente desde pixels adyacentes a cada hot pixel.

    Implementa Coppola 2024 chapter L1129 literal: "T_bk is retrieved from
    the pixels adjacent to the hot one". Para cada hot pixel, promedia los
    vecinos en una ventana NxN centrada, excluyendo (a) el centro mismo y
    (b) cualquier otro pixel marcado como hot (lista hot_rows/hot_cols).
    NaNs en vecinos son ignorados.

    Esta es la variante S57 reemplazo de median(ring 5-25km) que sobre-estima
    en Villarrica por contaminación del lago + nieve heterogénea — ver
    HYPOTHESIS_LOG H_S57_LOCAL_KERNEL.

    Args:
        bt_grid: 2D array (rows, cols) con BT en K. NaN para pixels inválidos.
        hot_rows: índices de fila de cada hot pixel.
        hot_cols: índices de columna de cada hot pixel.
        kernel_size: lado del kernel cuadrado (impar). Default 3 → ventana 3x3
                    = 8 vecinos. Coppola 2024 sugiere "adjacent" = 8-conn.

    Returns:
        Lista de t_bk (float) en K, una entrada por hot pixel. NaN si todos
        los vecinos válidos están ausentes (caller debe fallback).

    Raises:
        ValueError: si kernel_size es par o < 3.
    """
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError(
            f"kernel_size debe ser impar >= 3, recibido {kernel_size}"
        )
    if len(hot_rows) != len(hot_cols):
        raise ValueError("hot_rows y hot_cols deben tener mismo largo")

    grid = np.asarray(bt_grid, dtype=float)
    n_rows, n_cols = grid.shape
    half = kernel_size // 2

    # Máscara de hot pixels para excluir del background
    hot_set = set(zip(hot_rows, hot_cols))

    t_bks: list[float] = []
    for r, c in zip(hot_rows, hot_cols):
        r0 = max(0, r - half)
        r1 = min(n_rows, r + half + 1)
        c0 = max(0, c - half)
        c1 = min(n_cols, c + half + 1)

        # Recolectar vecinos no-hot, no-NaN
        neighbors: list[float] = []
        for rr in range(r0, r1):
            for cc in range(c0, c1):
                if (rr, cc) in hot_set:
                    continue  # excluye centro y otros hot
                val = grid[rr, cc]
                if not np.isnan(val):
                    neighbors.append(float(val))

        if not neighbors:
            t_bks.append(float("nan"))
        else:
            t_bks.append(float(np.mean(neighbors)))

    return t_bks


def cluster_corona_background(
    bt_grid: np.ndarray,
    cluster_indices: Sequence[tuple[int, int]],
    scene_hot_mask: np.ndarray | None,
    *,
    mode: str = "footprint",
    ring_px: int = 1,
    min_corona: int = 4,
) -> tuple[float, bool]:
    """Fondo LOCAL de la corona que rodea al cluster CONTIGUO (Coppola 2016a Eq.6
    "around the active cluster"). Frente §2 / D12 destape.

    A diferencia de `compute_local_background` (per-pixel "adjacent to the hot
    one", Coppola 2024 L1129), calcula UN solo t_bk para todo el cluster desde
    el anillo de píxeles que lo rodean, excluyendo TODOS los hot pixels de la
    escena y NaN. Esto desinfla los píxeles INTERIORES de un blob compacto (que
    el per-pixel deja en NaN → fallback regional → re-inflación; gap A48).

    Design: docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md

    Args:
        bt_grid: 2D array BT en K (NaN para inválidos).
        cluster_indices: lista de (row, col) del footprint del cluster contiguo
            (la `pixel_indices` que devuelve `cluster_hotspots`).
        scene_hot_mask: 2D bool con TODOS los hot pixels de la escena (para
            excluirlos de la corona — evita que un blob adyacente la contamine).
            None → solo se excluye el footprint propio.
        mode: "footprint" (V-B, recomendada): corona = dilatación 8-conexa del
            footprint, grosor `ring_px` píxeles. "ring" (V-A): anillo geométrico
            `[r_foot+0.5, r_foot+0.5+ring_px]` alrededor del centroide.
        ring_px: grosor de la corona en píxeles.
        min_corona: mínimo de píxeles válidos; bajo eso → (NaN, True) para que
            el caller caiga al fondo regional explícitamente (no silencioso).

    Returns:
        (t_bk_corona_K, corona_degraded). degraded=True ⟺ t_bk es NaN.
    """
    grid = np.asarray(bt_grid, dtype=float)
    n_rows, n_cols = grid.shape
    cluster_mask = np.zeros((n_rows, n_cols), dtype=bool)
    for (i, j) in cluster_indices:
        cluster_mask[i, j] = True

    if scene_hot_mask is None:
        scene_hot = cluster_mask
    else:
        scene_hot = np.asarray(scene_hot_mask, dtype=bool)

    if mode == "footprint":
        structure = np.ones((3, 3), dtype=bool)
        dilated = binary_dilation(
            cluster_mask, structure=structure, iterations=int(ring_px)
        )
        corona_region = dilated & ~cluster_mask
    elif mode == "ring":
        ii = np.array([i for (i, j) in cluster_indices], dtype=float)
        jj = np.array([j for (i, j) in cluster_indices], dtype=float)
        ci, cj = float(ii.mean()), float(jj.mean())
        r_foot = float(np.sqrt((ii - ci) ** 2 + (jj - cj) ** 2).max()) if ii.size else 0.0
        r_in = r_foot + 0.5
        r_out = r_foot + 0.5 + int(ring_px)
        rows_i, cols_i = np.mgrid[0:n_rows, 0:n_cols]
        dist = np.sqrt((rows_i - ci) ** 2 + (cols_i - cj) ** 2)
        corona_region = (dist >= r_in) & (dist <= r_out) & ~cluster_mask
    else:
        raise ValueError(f"mode debe ser 'footprint' o 'ring', got {mode!r}")

    corona = corona_region & ~scene_hot & ~np.isnan(grid)
    vals = grid[corona]
    if vals.size < int(min_corona):
        return (float("nan"), True)
    return (float(np.mean(vals)), False)


def cluster_vrp_per_pixel_with_bg(
    bt_grid: np.ndarray,
    pixel_areas: np.ndarray,
    cluster_indices: Sequence[tuple[int, int]],
    t_bk_bg_k: float,
    wooster_coeff: float,
    lambda_um: float,
) -> list[float]:
    """VRP (MW) de CADA píxel del cluster bajo un único fondo `t_bk_bg_k`.

    POR QUÉ EXISTE (S127): el fondo no es una propiedad del cluster sino de la
    medición entera — si se recomputa el total con la corona Eq.6 pero los consumidores
    aguas abajo siguen leyendo los VRP por píxel del fondo REGIONAL, el recompute se
    pierde. Eso es lo que pasó en el A/B de S126: `apply_single_pixel_mode` reemplazaba
    el total de la corona por `max(per_pixel)` del fondo viejo y anulaba el recompute en
    1.164 de los 1.179 records donde la corona sí había corrido.

    El caso límite lo hace evidente: para un cluster de UN píxel, la suma y el máximo
    son el mismo número; que difieran sólo puede significar dos fondos distintos.

    Devuelve la lista alineada con `cluster_indices` (los NaN aportan 0.0, para que la
    longitud y el orden se conserven). `cluster_vrp_mw_with_bg` es su suma — una sola
    fórmula, para que no puedan divergir.
    """
    grid = np.asarray(bt_grid, dtype=float)
    areas = np.asarray(pixel_areas, dtype=float)
    lam = float(lambda_um)
    l_bg = C1 / (lam ** 5 * (math.exp(C2 / (lam * float(t_bk_bg_k))) - 1))
    out: list[float] = []
    for (i, j) in cluster_indices:
        bt = grid[i, j]
        if np.isnan(bt):
            out.append(0.0)
            continue
        l_pix = C1 / (lam ** 5 * (math.exp(C2 / (lam * float(bt))) - 1))
        delta = l_pix - l_bg
        if delta < 0.0:
            delta = 0.0
        out.append(float(areas[i, j]) * float(wooster_coeff) * delta / 1e6)
    return out


def sum_cluster_vrp(per_pixel_vrp_mw: Sequence[float]) -> float:
    """Suma los VRP por píxel de un cluster con acumulación NAIVE, a propósito.

    POR QUÉ NO `sum()` (S127): desde Python 3.12 el `sum()` builtin usa suma
    compensada de Neumaier sobre floats, que es más exacta que un acumulador simple —
    y por eso mismo NO da bit a bit lo que daba el loop `total += ...` histórico. La
    diferencia es de un ULP (~2e-15 MW sobre 15 MW) y no tiene significado físico, pero
    convierte un cambio que debía ser no-op en uno que mueve números. El test
    `test_con_la_corona_apagada_el_total_es_identico_al_de_antes` lo detectó.

    Preferimos reproducir la aritmética anterior exactamente: en un clon literal, un
    refactor que no debe cambiar nada tiene que poder demostrarlo con igualdad estricta.
    """
    total = 0.0
    for v in per_pixel_vrp_mw:
        total += float(v)
    return total


def cluster_vrp_mw_with_bg(
    bt_grid: np.ndarray,
    pixel_areas: np.ndarray,
    cluster_indices: Sequence[tuple[int, int]],
    t_bk_bg_k: float,
    wooster_coeff: float,
    lambda_um: float,
) -> float:
    """VRP (MW) del cluster = suma de ΔL·área·Wooster sobre sus píxeles, usando
    un único fondo `t_bk_bg_k` (típicamente la corona del cluster, Eq.6).

    Misma fórmula Planck/Wooster que process_modis.py:824-858, scoped al cluster
    contiguo. ΔL clip a 0 (Wooster requiere exceso positivo). NaN se saltan.

    NOTA S127 — **no es la ruta operacional**. Desde el fix de la corona (#546) los
    tres procesadores llaman a `cluster_vrp_per_pixel_with_bg` y suman con
    `sum_cluster_vrp`, porque necesitan los valores POR PIXEL para alimentar
    coherentemente lo que corre después (`cluster_focal_vrp_mw`,
    `apply_single_pixel_mode`). Esta función queda como API pública y como
    referencia de los tests, que la usan para fijar el invariante «la suma de los
    por-píxel es el total». Se aclara acá para que nadie la lea como el camino que
    produce el número que se publica.
    """
    return sum_cluster_vrp(cluster_vrp_per_pixel_with_bg(
        bt_grid, pixel_areas, cluster_indices, t_bk_bg_k,
        wooster_coeff, lambda_um,
    ))


def cluster_focal_vrp_mw(
    cluster_indices: Sequence[tuple[int, int]],
    vrp_per_pixel_2d: np.ndarray,
    dnti_ctx_mask: np.ndarray,
    keep_peak: bool = True,
) -> tuple[float, int, bool]:
    """Magnitud del cluster sumando SOLO píxeles contextualmente anómalos ∪ {pico}.

    S109 §1 — el campo difuso tibio uniforme (no anómalo vs sus 8 vecinos) se cae;
    el foco discreto (cráter activo / lava / incendio, anómalo vs vecinos) se conserva.
    Generaliza a la magnitud del cluster el filtro contextual de Test 1 ya adoptado en
    VIIRS (ctxpeak, test1_contextual_filter.apply_contextual_test1_filter, S100).
    Fundamento: Coppola 2016a SP426.5 Tests 2/3 (dNTI contextual) + Coppola 2023 Eq.1
    ("VRP fundamentally insensitive to the diffuse heat dispersed from the crater area
    at a few degrees above the background"). NO es fondo-local (guard A48): no toca L_bg
    ni la radiancia per-pixel — solo SELECCIONA qué píxeles ya-computados entran a la suma.

    Args:
        cluster_indices: píxeles (i, j) del cluster primario YA seleccionado.
        vrp_per_pixel_2d: VRP (MW) por píxel ya computado (Wooster), 0 fuera de hot.
        dnti_ctx_mask: bool 2-D, píxeles contextualmente anómalos (dnti_ctx_hot).
        keep_peak: si True, conserva SIEMPRE el píxel de mayor VRP del cluster
            (anti-FN del cráter embebido no-contextual). Si False (canario), puede
            dar 0 cuando ningún píxel del cluster es contextual.

    Returns:
        (vrp_mw, n_focal, degraded). degraded=True ⟺ ningún píxel del cluster era
        contextual (se cayó al solo-pico con keep_peak, o a 0 sin él) — transparencia,
        no fallback silencioso.
    """
    ctx = np.asarray(dnti_ctx_mask, dtype=bool)
    vrp2d = np.asarray(vrp_per_pixel_2d, dtype=float)
    focal = [(int(i), int(j)) for (i, j) in cluster_indices if ctx[int(i), int(j)]]
    degraded = len(focal) == 0
    if keep_peak and len(cluster_indices) > 0:
        peak = max(cluster_indices, key=lambda rc: vrp2d[int(rc[0]), int(rc[1])])
        peak = (int(peak[0]), int(peak[1]))
        if peak not in focal:
            focal.append(peak)
    vrp_mw = float(sum(vrp2d[i, j] for (i, j) in focal))
    return vrp_mw, len(focal), degraded


def _planck_spectral_radiance(t_k: float, lambda_um: float) -> float:
    """Planck spectral radiance B(λ, T) en W/m²/sr/μm."""
    if t_k <= 0 or lambda_um <= 0:
        return 0.0
    try:
        denom = math.exp(C2 / (lambda_um * t_k)) - 1.0
        if denom <= 0:
            return 0.0
        return C1 / (lambda_um ** 5 * denom)
    except OverflowError:
        return 0.0


def compute_vrp_lava_lake_eq16(
    bt_hot_k: float,
    bt_bg_k: float,
    t_bk_k: float,
    t_e_k: float = 1000.0,
    epsilon: float = 0.95,
    a_pix_m2: float = 140625.0,
    lambda_mir_um: float = 3.74,
) -> dict:
    """Calcula VRP de lava lake magmático sub-pixel vía Coppola 2024 Eq.15+16.

    Aplica cuando el VTF es lava magmática expuesta sub-pixel (típico Villarrica,
    Erebus): A_lake ≪ A_pix, BT_pixel mezclado con background frío.

    Método (Coppola 2024 chapter §Lava lakes, Burgi-Coppola convention):
    1. Asume T_e (lava lake temperature) fijo, default 1000 K
    2. Despeja A_hot desde Eq.15:
       A_hot = (L_pixel - L_bg) / (B(λ, T_e) - L_bg) × A_pix
    3. Calcula VRP via Eq.16:
       φ_rad = A_hot × σ × ε × (T_e⁴ - T_bk⁴)

    Args:
        bt_hot_k: Brightness temperature del pixel hot (K)
        bt_bg_k: BT del background ring (K) — usado para L_bg en Eq.15
        t_bk_k: T background físico para Stefan-Boltzmann en Eq.16 (típicamente = bt_bg_k)
        t_e_k: T efectiva asumida del lava lake (K). Default 1000 (Burgi-Coppola)
        epsilon: emisividad. Default 0.95 (literatura volcánica)
        a_pix_m2: área del pixel (m²). Default VIIRS I04 nadir 140625
        lambda_mir_um: longitud de onda MIR (μm). Default 3.74 (VIIRS I04)

    Returns:
        dict con keys:
          - vrp_mw: VRP en MW
          - a_hot_m2: área hot estimada en m²

    Edge cases:
        - bt_hot ≤ bt_bg → vrp=0, a_hot=0 (no anomalía)
        - a_hot > a_pix → clip a a_pix (saturación física)
        - T_bk ≥ T_e → vrp=0 (sin gradiente útil)
    """
    # Edge: sin gradiente positivo
    if bt_hot_k <= bt_bg_k:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}
    if t_bk_k >= t_e_k:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}

    # Radiancias espectrales Planck
    l_pixel = _planck_spectral_radiance(bt_hot_k, lambda_mir_um)
    l_bg = _planck_spectral_radiance(bt_bg_k, lambda_mir_um)
    b_te = _planck_spectral_radiance(t_e_k, lambda_mir_um)

    if b_te <= l_bg:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}

    # Eq.15 — despejar A_hot (Coppola 2024 chapter L1140-1143)
    a_hot = (l_pixel - l_bg) / (b_te - l_bg) * a_pix_m2

    # Clip físico: A_hot ≤ A_pix
    a_hot = min(max(a_hot, 0.0), a_pix_m2)

    # Eq.16 — VRP radiante (Coppola 2024 chapter L1146-1148)
    phi_rad_w = a_hot * SIGMA * epsilon * (t_e_k ** 4 - t_bk_k ** 4)
    vrp_mw = phi_rad_w / 1e6

    return {"vrp_mw": vrp_mw, "a_hot_m2": a_hot}
