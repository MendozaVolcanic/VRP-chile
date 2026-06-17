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


def _local_background_nti(
    nti: np.ndarray, lat: np.ndarray, lon: np.ndarray,
    vent_lat: float, vent_lon: float, roi_km: float,
    r_in_km: float, r_out_km: float, min_local: int, nti_bg_fallback: float,
) -> np.ndarray:
    """Fondo LOCAL de NTI por píxel (S105, realineamiento MIROVA Coppola 2024 Eq.13).

    Para cada píxel del ROI, el fondo es la mediana del NTI en su anillo local
    [r_in, r_out] km — no la mediana del anillo entero. Cancela la estructura
    topográfica residual del NTI uniformemente: el valle tibio se compara con su
    propio entorno (no destaca), la lava se compara con la cumbre fría (destaca).
    Fallback al fondo escalar del anillo donde hay < min_local vecinos válidos
    (borde de granule). Uniforme para todos los volcanes (sin per-vol).

    Devuelve un array 2D (mismo shape que nti) con el fondo local; NaN fuera del ROI.
    """
    dist_vent = haversine_km(vent_lat, vent_lon, lat, lon)
    # región fuente: ROI + margen r_out, para que cada píxel del ROI tenga vecinos
    region = (dist_vent <= roi_km + r_out_km) & np.isfinite(nti)
    rlat = lat[region]; rlon = lon[region]; rnti = nti[region]
    out = np.full(nti.shape, np.nan, dtype=np.float64)
    roi_idx = np.where((dist_vent <= roi_km) & np.isfinite(nti))
    for k in range(len(roi_idx[0])):
        iy, ix = roi_idx[0][k], roi_idx[1][k]
        d = haversine_km(lat[iy, ix], lon[iy, ix], rlat, rlon)
        local = (d >= r_in_km) & (d <= r_out_km)
        n = int(np.sum(local))
        out[iy, ix] = float(np.median(rnti[local])) if n >= min_local else nti_bg_fallback
    return out


def intermediate_ring_bg_bt(
    bt: np.ndarray, dist_km: np.ndarray,
    r_in_km: float, r_out_km: float, min_pixels: int = 20,
    valid_mask: "np.ndarray | None" = None,
) -> float:
    """S112 Q3 — mediana de BT del anillo INTERMEDIO [r_in, r_out] km del cráter.

    POR QUÉ: en un cráter con calor crónico (NdC Nicanor, domo activo + lava reciente)
    el fondo local 1-3 km está contaminado por la propia anomalía (→ exceso recortado a
    0, FN de magnitud) y el fondo global 5-25 km es nieve/roca de altura fría (→ exceso
    inflado ~4.4× MIROVA). Un anillo intermedio queda FUERA del halo de calor crónico
    pero sobre terreno de altitud similar → fondo "Goldilocks" para el recompute.

    valid_mask (S112 review MEDIUM): máscara 2D opcional para igualar el criterio del
    fondo GLOBAL, que excluye nubes (cloud_free = I05 ≥ 260 K). Sin ella, topes de nube
    fríos dentro del anillo bajarían la mediana → exceso MIR mayor → magnitud INFLADA
    (al revés del objetivo del A/B), justo en las noches de cirrus de la reactivación NdC.
    El caller pasa el mismo cloud_free que alimenta bg_mask → apples-to-apples.

    NaN-safe; devuelve NaN si hay < min_pixels válidos en el anillo (fallback aguas
    arriba al global/local). Función pura, sin I/O.
    """
    bt = np.asarray(bt, dtype=np.float64)
    dist_km = np.asarray(dist_km, dtype=np.float64)
    ring = (dist_km >= r_in_km) & (dist_km <= r_out_km) & np.isfinite(bt)
    if valid_mask is not None:
        ring = ring & np.asarray(valid_mask, dtype=bool)
    vals = bt[ring]
    if vals.size < min_pixels:
        return float("nan")
    return float(np.median(vals))


def select_test1_effective_lbg(*, intermediate_enabled, intermediate_lbg,
                               global_enabled, lbg_global_compatible, global_lbg,
                               local_lbg):
    """S112 — elige el L_bg (radiancia MIR) efectivo para el recompute de magnitud Test1.

    PRECEDENCIA: anillo intermedio (S112 Q3) > global per-vol (S33 D4) > local (S26).
    Cada nivel solo gana si su flag está habilitado Y su valor es finito; si no, cae al
    siguiente. Centraliza la cascada para que sea unit-testeable; con todos los flags
    nuevos OFF el resultado es BYTE-IDÉNTICO al legacy (global cuando enabled+compatible+
    finito, sino local).

    SCOPE (S112 adopción, A45): tanto el anillo intermedio como el global están gateados
    por `lbg_global_compatible` (per-vol, volcanoes.yaml) — solo los 3 nevados de calor
    crónico (Lascar/NdC/Lastarria) donde el fondo global se contamina con valles tibios.
    Así la adopción no cambia la magnitud de vols no validados en el A/B.

    Devuelve float (radiancia) o el local_lbg tal cual (puede ser None fuera del bloque I04).
    """
    if (intermediate_enabled and lbg_global_compatible and intermediate_lbg is not None
            and math.isfinite(float(intermediate_lbg))):
        return float(intermediate_lbg)
    if (global_enabled and lbg_global_compatible and global_lbg is not None
            and math.isfinite(float(global_lbg))):
        return float(global_lbg)
    return local_lbg


def resolve_test1_source_priority(*, test1_summit_hit, eruption_far, only_test1_source,
                                  cluster_vrp_mw, weak_cluster_enabled, weak_cluster_eps):
    """S111 — ¿el Test1 debe ganar `final_hotspot_source` (y con él el recompute de
    magnitud del Test1 integrado)?

    POR QUÉ: el recompute del VRP Test1 (process_viirs/process_modis) está gateado por
    source=='test1'. Cuando el Test1 detecta una señal sub-píxel real al cráter pero
    coexiste un cluster cercano DÉBIL (1 píxel, vrp≈0 por fondo MIR contaminado), la
    cascada elige `eruption` y la magnitud colapsa a 0 — el FN de la reactivación de
    Nevados de Chillán (MIROVA 0.06 MW). Este helper centraliza las condiciones bajo
    las que el Test1 es la señal real dominante.

    Las dos primeras ramas son las clásicas (Regla D S30 + only_test1 S44), invariantes
    al flag. La tercera (S111, `weak_cluster_enabled`) añade: si el Test1 detectó summit
    y el cluster rival no aporta magnitud real (None o vrp < ε), el Test1 gana. NO le
    roba la fuente a un cluster con magnitud genuina (guard cluster_vrp_mw >= ε).

    Returns bool de Python (JSON-safe).
    """
    if test1_summit_hit and eruption_far:
        return True
    if only_test1_source:
        return True
    if weak_cluster_enabled and test1_summit_hit:
        if cluster_vrp_mw is None or float(cluster_vrp_mw) < weak_cluster_eps:
            return True
    return False


def compute_test1_nti(
    bt_mir: np.ndarray,
    bt_tir: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    vent_lat: float,
    vent_lon: float,
    lambda_mir_um: float,
    lambda_tir_um: float,
    roi_km: float = 3.0,
    inner_ring_km: float = 1.0,
    k_sigma: float = 3.0,
    nti_relative: float = 0.0,
    min_bg_pixels: int = 20,
    local_bg_ring_km: tuple[float, float] | None = None,
    min_local_bg_pixels: int = 8,
) -> dict:
    """Test 1 integrado sobre exceso de NTI (S104 V2, realineamiento MIROVA).

    A diferencia de `compute_test1_mir` (integra radiancia MIR absoluta, sesgable por
    gradiente topográfico), integra el exceso del índice normalizado
    NTI = (L_MIR − L_TIR)/(L_MIR + L_TIR), que cancela la topografía (MIR y TIR suben
    juntos sobre terreno tibio). Detecta lava sub-pixel débil (NTI levemente elevado y
    concentrado en el cráter) y rechaza el valle tibio (NTI plano). Ground truth:
    docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md (2 probes Actions).

    Returns dict análogo a compute_test1_mir con `delta_nti_integrated` en vez de
    `delta_L_integrated`, más `triggered`, `n_contributing`, `mask_contributing`,
    `centroid_lat/lon`, `nti_bg`, `sigma_bg`, `k_sigma_observed`, `reason`.
    """
    bt_mir = np.asarray(bt_mir, dtype=np.float64)
    bt_tir = np.asarray(bt_tir, dtype=np.float64)
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    for name, arr in (("bt_tir", bt_tir), ("lat", lat), ("lon", lon)):
        if arr.shape != bt_mir.shape:
            raise ValueError(f"shape mismatch: {name}={arr.shape} bt_mir={bt_mir.shape}")

    dist = haversine_km(vent_lat, vent_lon, lat, lon)
    valid = np.isfinite(bt_mir) & np.isfinite(bt_tir)
    roi_mask = (dist <= roi_km) & valid
    bg_mask = (dist > inner_ring_km) & (dist <= roi_km) & valid
    n_roi = int(np.sum(roi_mask))
    n_bg = int(np.sum(bg_mask))

    empty = {
        "triggered": False, "abs_criterion": False, "rel_criterion": False,
        "n_roi": n_roi, "n_bg": n_bg, "n_contributing": 0,
        "nti_bg": float("nan"), "sigma_bg": float("nan"),
        "delta_nti_integrated": 0.0, "sigma_delta_nti": 0.0,
        "k_sigma_observed": 0.0, "mask_roi": roi_mask,
        "mask_contributing": np.zeros_like(bt_mir, dtype=bool),
        "centroid_lat": None, "centroid_lon": None,
        "L_bg_mir": None, "reason": "",
    }
    if n_bg < min_bg_pixels:
        empty["reason"] = f"insufficient_bg_pixels (n_bg={n_bg}<{min_bg_pixels})"
        return empty
    if n_roi == 0:
        empty["reason"] = "empty_roi"
        return empty

    L4 = bt_to_radiance_um(bt_mir, lambda_mir_um)
    L5 = bt_to_radiance_um(bt_tir, lambda_tir_um)
    denom = L4 + L5
    nti = np.where(denom > 0, (L4 - L5) / denom, np.nan)

    # L_bg MIR (mediana de radiancia MIR del anillo) — para que el caller compute el
    # VRP Wooster sobre los píxeles NTI-elegidos (V2.5: el VRP usa MIR, no NTI).
    L4_bg_vals = L4[bg_mask]
    L4_bg_vals = L4_bg_vals[np.isfinite(L4_bg_vals)]
    L_bg_mir = float(np.median(L4_bg_vals)) if L4_bg_vals.size else float("nan")

    nti_bg_vals = nti[bg_mask]
    nti_bg_vals = nti_bg_vals[np.isfinite(nti_bg_vals)]
    if nti_bg_vals.size < min_bg_pixels:
        empty["reason"] = "insufficient_finite_nti_bg"
        return empty
    nti_bg = float(np.median(nti_bg_vals))
    sigma_bg = 1.4826 * float(np.median(np.abs(nti_bg_vals - nti_bg)))
    if sigma_bg <= 0:
        empty["reason"] = "zero_sigma_bg"
        return empty

    nti_roi = nti[roi_mask]
    # S105 — fondo escalar (anillo entero, legacy) o LOCAL por píxel (realineamiento
    # MIROVA Coppola 2024 Eq.13). El fondo local cancela la estructura topográfica
    # residual del NTI sin per-vol. local_bg_ring_km=None preserva el comportamiento.
    if local_bg_ring_km is not None:
        r_in_km, r_out_km = local_bg_ring_km
        nti_bg_field = _local_background_nti(
            nti, lat, lon, vent_lat, vent_lon, roi_km,
            r_in_km, r_out_km, min_local_bg_pixels, nti_bg)
        nti_bg_roi = nti_bg_field[roi_mask]
    else:
        nti_bg_roi = nti_bg  # escalar (broadcast)
    excess_roi = np.where(np.isfinite(nti_roi), np.maximum(0.0, nti_roi - nti_bg_roi), 0.0)
    delta_nti = float(np.sum(excess_roi))
    sigma_delta_nti = sigma_bg * math.sqrt(n_roi)

    contributing_in_roi = excess_roi > 0
    n_contributing = int(np.sum(contributing_in_roi))
    abs_criterion = delta_nti > k_sigma * sigma_delta_nti
    rel_criterion = delta_nti > nti_relative * n_roi if nti_relative > 0 else True
    triggered = bool(abs_criterion and rel_criterion)

    mask_contributing = np.zeros_like(bt_mir, dtype=bool)
    roi_idx = np.where(roi_mask)
    for k in range(len(roi_idx[0])):
        if contributing_in_roi[k]:
            mask_contributing[roi_idx[0][k], roi_idx[1][k]] = True

    centroid_lat = centroid_lon = None
    if n_contributing > 0:
        w = excess_roi[contributing_in_roi]
        wsum = float(np.sum(w))
        if wsum > 0:
            centroid_lat = float(np.sum(lat[mask_contributing] * w) / wsum)
            centroid_lon = float(np.sum(lon[mask_contributing] * w) / wsum)

    return {
        "triggered": triggered, "abs_criterion": bool(abs_criterion),
        "rel_criterion": bool(rel_criterion), "n_roi": n_roi, "n_bg": n_bg,
        "n_contributing": n_contributing, "nti_bg": nti_bg, "sigma_bg": sigma_bg,
        "delta_nti_integrated": delta_nti, "sigma_delta_nti": sigma_delta_nti,
        "k_sigma_observed": delta_nti / sigma_delta_nti if sigma_delta_nti > 0 else 0.0,
        "mask_roi": roi_mask, "mask_contributing": mask_contributing,
        "centroid_lat": centroid_lat, "centroid_lon": centroid_lon,
        "L_bg_mir": L_bg_mir, "reason": "",
    }


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
