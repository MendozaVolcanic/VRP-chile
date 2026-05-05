"""
process_modis.py — Calculate VRP from MODIS MOD021KM / MYD021KM L1B granules.

Algorithm: MIROVA (Coppola et al. 2015, sp426.5)
  VRP = A_pixel * sigma * (T_pix^4 - T_bg^4)
  threshold = max(5K, 3 * std_background)

Bands:
  EV_1KM_Emissive contains all 16 emissive bands [20-25, 27-36]
  - Band 21 (3.929 um): index 1 in EV_1KM_Emissive — primary MIR hotspot channel
  - Band 22 (3.959 um): index 2 — used where Band 21 is saturated

Geolocation: MOD021KM includes coarse lat/lon (every 5 pixels),
  interpolated to 1km for pixel-level matching.

References:
  - MODIS L1B User Guide C7 (MODIS_L1B_UserGuide_C7.pdf)
  - Coppola et al. 2015, Geological Society Special Publication 426
"""

import numpy as np
from pathlib import Path

try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False
    print("WARNING: pyhdf not found. Install: conda install -c conda-forge pyhdf")

from .scan_geometry import modis_pixel_areas, roi_mask_bbox
from .exclusion_zones import filter_hot_mask, guard_exclude_zones
from .clustering import cluster_hotspots, cluster_pixels_geographic
from .test1_integrated import compute_test1_mir


# S23 T17: constantes físicas centralizadas en pipeline/constants.py
from pipeline.constants import SIGMA, C1, C2

BAND21_LAMBDA = 3.929
BAND22_LAMBDA = 3.959
# Band 31 (TIR 11 um) — used for NTI dual criteria (E3).
# EV_1KM_Emissive band order [20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36]
# so Band 31 is index 10.
BAND31_IDX = 10
BAND31_LAMBDA = 11.03
# Nadir pixel area; actual area is computed per-pixel from scan column index
# in scan_geometry.modis_pixel_areas (sec^3(theta_z) correction).
NADIR_PIXEL_AREA_M2 = 1e6  # 1 km^2 at nadir

# Wooster MIR radiance coefficient (Coppola 2015, Eq.7)
WOOSTER_COEFF = 18.9

# --- All detection thresholds come from the active profile ---
# See pipeline/profiles/*.yaml for the documented values. Profile is
# selected via $VRP_PROFILE (set by run_pipeline.py --profile).
#
# E3 — NTI (Normalized Thermal Index, Coppola 2015) for MODIS.
# Analogous to the dual criteria already used in process_viirs.py on I04/I05.
# NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR), computed per-pixel from Band 21
# (MIR ~3.93 um) and Band 31 (TIR ~11 um). A pixel is flagged hot if EITHER
# the BT-branch passes OR the NTI-branch passes (Coppola 2015 Test 1).
# See ROOT_CAUSE_S9.md RF4/RF6 and experiments/F1_validation.md.
#
# E2a — Cloud mask for the background annulus (CLOUD_MASK_BT_K).
# E2b' — Sigma cap for detection threshold (MAX_SIGMA_COMPONENT_K).
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    N_SIGMA,
    BG_INNER_KM,
    BG_OUTER_KM,
    NTI_K1_NIGHT,
    NTI_BT_SANITY_K,
    CLOUD_MASK_BT_K,
    MAX_SIGMA_COMPONENT_K,
    ENABLE_ERUPTION_PATH,
    ENABLE_VENT_PATH_MODIS,
    VENT_THRESHOLD_K,
    MODIS_VENT_THRESHOLD_K,
    MODIS_VENT_VRP_FLOOR_MW,
    N_SIGMA_VENT,
    MAX_VENT_SIGMA_CONTRIB_K,
    MIN_VENT_PIXELS,
    DNTI_CONTEXTUAL_C1,
    DNTI_CONTEXTUAL_C1_SUMMIT,
    DNTI_CONTEXTUAL_C1_SCENE,
    ENABLE_DNTI_CONTEXTUAL_PATH,
    ENABLE_DNTI_DUAL_ROI,
    ENABLE_DUAL_ROI_BT,
    ENABLE_TEST1_PIXEL_FILTER,
    ENABLE_FINAL_PIXEL_FILTER,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
    ENABLE_EXCLUDE_ZONES,
    ENABLE_TEST1_PATH,
    TEST1_K_SIGMA,
    TEST1_MIR_RELATIVE,
    TEST1_ROI_KM,
    TEST1_INNER_RING_KM,
    P95_VENT_EXCLUSION_MODIS_KM,
)
from .detection_context import (
    contextual_dnti_hot_mask,
    dual_roi_contextual_dnti_hot_mask,
    dual_roi_bt_threshold,
)

# Indices of bands 21 and 22 within EV_1KM_Emissive
# Band_1KM_Emissive order: [20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36]
BAND21_IDX = 1
BAND22_IDX = 2


def radiance_to_bt(L: np.ndarray, wavelength_um: float) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2 / (wavelength_um * np.log(C1 / (L * wavelength_um ** 5) + 1))


def bt_to_radiance(bt, wavelength_um: float):
    """Planck spectral radiance (W/m^2/sr/um) for a given BT (K) and wavelength."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return C1 / (wavelength_um ** 5 * (np.exp(C2 / (wavelength_um * bt)) - 1))


def read_modis_l1b(hdf_path: Path) -> dict:
    """
    Read MODIS MOD021KM L1B HDF4 file.

    Returns:
        {
          "band21": ndarray float32 — calibrated radiance (W/m^2/sr/um)
          "band22": ndarray float32
          "lat":    ndarray float32 — latitude at 1km resolution (interpolated)
          "lon":    ndarray float32 — longitude at 1km resolution
        }
    """
    if not HDF4_AVAILABLE:
        raise ImportError("pyhdf required: conda install -c conda-forge pyhdf")

    sd = SD(str(hdf_path), SDC.READ)

    # --- Read emissive bands ---
    emissive_sds = sd.select("EV_1KM_Emissive")
    emissive_data = emissive_sds.get()              # shape: (16, n_lines, n_samples)
    attrs = emissive_sds.attributes()
    scales = np.array(attrs["radiance_scales"])     # (16,) — one per band
    offsets = np.array(attrs["radiance_offsets"])   # (16,)
    fill = attrs.get("_FillValue", 65535)
    emissive_sds.endaccess()

    def calibrate(band_idx, wavelength):
        dn = emissive_data[band_idx].astype(np.float32)
        rad = (dn - offsets[band_idx]) * scales[band_idx]
        rad[dn >= fill] = np.nan
        return rad

    band21 = calibrate(BAND21_IDX, BAND21_LAMBDA)
    band22 = calibrate(BAND22_IDX, BAND22_LAMBDA)
    band31 = calibrate(BAND31_IDX, BAND31_LAMBDA)  # E3: TIR for NTI

    # --- Read coarse geolocation (5km grid embedded in MOD021KM) ---
    lat_coarse = sd.select("Latitude").get().astype(np.float32)   # (406, 271) for 2030x1354
    lon_coarse = sd.select("Longitude").get().astype(np.float32)

    sd.end()

    # Interpolate coarse lat/lon to full 1km resolution
    n_lines, n_samples = band21.shape
    lat = _interp_geo(lat_coarse, n_lines, n_samples)
    lon = _interp_geo(lon_coarse, n_lines, n_samples)

    return {"band21": band21, "band22": band22, "band31": band31, "lat": lat, "lon": lon}


def _interp_geo(coarse: np.ndarray, target_lines: int, target_samples: int) -> np.ndarray:
    """Bilinear interpolation of coarse (5km) geolocation to 1km resolution."""
    from scipy.ndimage import zoom
    scale_y = target_lines / coarse.shape[0]
    scale_x = target_samples / coarse.shape[1]
    try:
        from scipy.ndimage import zoom as _zoom
        return _zoom(coarse, (scale_y, scale_x), order=1)
    except ImportError:
        # Fallback: repeat each value (less accurate but functional)
        return np.repeat(np.repeat(coarse, int(round(scale_y)), axis=0),
                         int(round(scale_x)), axis=1)[:target_lines, :target_samples]


# S23 Task 2: haversine_km centralizado en pipeline/scan_geometry.py
# (era duplicado en 3 archivos process_*.py).
from pipeline.scan_geometry import haversine_km


def calculate_vrp(hdf_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 15.0,
                  vent_lat: float = None, vent_lon: float = None,
                  vent_radius_km: float = 4.0,
                  inner_radius_km: float | None = None,
                  exclude_zones: list = None,
                  active_water_bodies: list = None) -> dict | None:
    """
    Calculate VRP from MODIS L1B granule.

    geo_path is accepted for API compatibility but not used —
    geolocation is embedded in MOD021KM.

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
            Uses a low threshold (1K) in a tight ROI without ROI p95 filter.
        vent_radius_km: Radius for vent-scale search.
        inner_radius_km: MIROVA-style visual classification radius (S14 D1).
            If None, distance_class is None.

    Returns dict or None if granule does not cover volcano.
    """
    data = read_modis_l1b(hdf_path)

    lat = data["lat"]
    lon = data["lon"]
    # Per-pixel ground area corrected for off-nadir scan geometry
    pixel_areas = modis_pixel_areas(lat.shape)
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    # P3.1 S15: per-pixel distance from effective vent for dual-ROI.
    if vent_lat is not None and vent_lon is not None:
        vent_dist_per_pixel = haversine_km(vent_lat, vent_lon, lat, lon)
    else:
        vent_dist_per_pixel = dist

    # S15 Tema E: bbox cuadrado (paridad MIROVA KMZ 50x50 km).
    roi_mask = roi_mask_bbox(lat, lon, volcano_lat, volcano_lon, radius_km)
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    # Merge bands: use Band 21 primary, Band 22 where 21 is NaN (saturated)
    # Work with both radiance (for VRP) and BT (for thresholds/reporting)
    rad21 = data["band21"]
    rad22 = data["band22"]
    rad_mir = np.where(np.isnan(rad21), rad22, rad21)

    bt21 = radiance_to_bt(rad21, BAND21_LAMBDA)
    bt22 = radiance_to_bt(rad22, BAND22_LAMBDA)
    bt_mir = np.where(np.isnan(bt21), bt22, bt21)

    # E3: TIR Band 31 for NTI. Keep the MIR radiance we'll use for NTI aligned
    # with whichever band provided bt_mir (21 primary, 22 fallback).
    rad31 = data["band31"]
    bt31 = radiance_to_bt(rad31, BAND31_LAMBDA)
    rad_mir_for_nti = np.where(np.isnan(rad21), rad22, rad21)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (rad_mir_for_nti - rad31) / (rad_mir_for_nti + rad31)

    # E2a: exclude cold-cloud contaminated pixels from the background annulus.
    bg_cloud_free = bg_mask & ~np.isnan(bt_mir) & (bt_mir > CLOUD_MASK_BT_K)
    bg_vals = bt_mir[bg_cloud_free]
    if len(bg_vals) < 10:
        return None

    t_bg = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
    # E2b': cap the sigma component so orographic heterogeneity in the
    # annulus can't blow up the threshold and mask real vent anomalies.
    sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
    threshold = max(ANOMALY_THRESHOLD_K, sigma_component)

    # Additional local-ROI filter: use the ROI's own statistics to avoid
    # topographic false positives (e.g., high-altitude volcanoes with warmer
    # low-altitude terrain in the background annulus).
    # A pixel must exceed BOTH the background threshold AND the ROI p95 threshold.
    #
    # IMPORTANT (session 6, E1 fix): when a vent is known, exclude a safety
    # zone around it from the p95 calculation. Otherwise the vent pixel itself
    # elevates the p95 and the filter "eats its own tail": the vent ends up
    # needing to be ~3 K hotter than itself to clear the local threshold.
    # Empirically (Lascar, 16 MODIS pairs in the 2-10 MW bucket), this caused
    # the pipeline to report n_anomalous_pixels=0 on every single ref, with
    # dT_bg as high as 11.7 K but blocked by `p95 + 3K`. The vent exclusion
    # uses a slightly larger margin than vent_radius_km because the 1 km MODIS
    # pixel footprint can overlap the vent even when its center is outside the
    # vent ROI (an Aqua pass with vent_radius_km=3 may still have the hottest
    # pixel at ~4 km from the vent center due to pixel centering).
    # S23 T18: configurable via profile (era hardcoded 5.0 km).
    P95_VENT_EXCLUSION_KM = P95_VENT_EXCLUSION_MODIS_KM
    roi_bt_full = np.where(roi_mask & ~np.isnan(bt_mir), bt_mir, np.nan)
    if vent_lat is not None and vent_lon is not None:
        vent_dist_for_p95 = haversine_km(vent_lat, vent_lon, lat, lon)
        p95_mask = (roi_mask
                    & ~np.isnan(bt_mir)
                    & (vent_dist_for_p95 > max(vent_radius_km, P95_VENT_EXCLUSION_KM)))
        roi_valid = bt_mir[p95_mask]
    else:
        roi_valid = roi_bt_full[~np.isnan(roi_bt_full)]
    if len(roi_valid) >= 10:
        roi_p95 = float(np.percentile(roi_valid, 95))
        roi_std = float(np.std(roi_valid))
        local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
        effective_threshold = max(t_bg + threshold, local_threshold)
    else:
        roi_p95 = float("nan")
        local_threshold = float("nan")
        effective_threshold = t_bg + threshold

    # E3: NTI background statistics on the same cloud-masked annulus.
    # We also require band 31 to be valid on those pixels.
    nti_bg_vals = nti[bg_cloud_free & ~np.isnan(nti)]
    if len(nti_bg_vals) >= 10:
        nti_bg = float(np.median(nti_bg_vals))
        nti_std = float(np.std(nti_bg_vals))
    else:
        nti_bg = float("nan")
        nti_std = float("nan")

    # Find all anomalous pixels with their 2D indices.
    # Dual path (Coppola 2015 / MIROVA Test 1, analogous to process_viirs.py NTI):
    #   A) BT path: existing E2-capped local+bg threshold (conservative).
    #   B) NTI path: MIROVA fixed floor K1_NIGHT=-0.8 with a BT sanity margin
    #      so we never trigger on pure noise. This rescues subpixel hotspots
    #      at andean volcanoes where sigma_bg inflates the BT threshold beyond
    #      reach but NTI still responds cleanly to even a 1-2% hot fraction.
    # S26 dual-ROI N·sigma BT (Coppola 2016a Tabla 1): summit 5sigma, scene 10sigma.
    # Cuando flag activo y hay vent + inner_radius, sustituimos el bt_path_hot
    # uniforme por dos thresholds diferenciados. local_threshold sigue aplicando
    # encima como filtro p95 (preserva fix histórico).
    if (ENABLE_DUAL_ROI_BT and inner_radius_km is not None
            and vent_lat is not None and vent_lon is not None):
        bt_path_hot = dual_roi_bt_threshold(
            bt=bt_mir, roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg, inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        # Aplicar local_threshold p95 si existe (filtro complementario).
        if not np.isnan(local_threshold):
            bt_path_hot = bt_path_hot & (bt_mir > local_threshold)
    else:
        bt_path_hot = roi_mask & ~np.isnan(bt_mir) & (bt_mir > effective_threshold)
    nti_path_hot = (
        roi_mask
        & ~np.isnan(nti)
        & ~np.isnan(bt_mir)
        & (nti > NTI_K1_NIGHT)
        & (bt_mir > (t_bg + NTI_BT_SANITY_K))
    )

    # Path D — dNTI contextual 8-vecinos (P3.2 + P3.1 S15, Coppola 2016a).
    # P3.1 dual-ROI: summit C1=0.003 sensible, scene C1=0.010 estricto.
    n_dnti_ctx_path = 0
    if ENABLE_DNTI_CONTEXTUAL_PATH and not np.isnan(nti_bg):
        if ENABLE_DNTI_DUAL_ROI and inner_radius_km is not None:
            dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
                nti=nti, bt=bt_mir, roi_mask=roi_mask,
                dist_km=vent_dist_per_pixel,
                t_bg=t_bg,
                c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                c1_scene=DNTI_CONTEXTUAL_C1_SCENE,
                inner_km=inner_radius_km,
                bt_sanity_k=NTI_BT_SANITY_K,
            )
        else:
            dnti_ctx_hot = contextual_dnti_hot_mask(
                nti=nti, bt=bt_mir, roi_mask=roi_mask,
                t_bg=t_bg,
                c1=DNTI_CONTEXTUAL_C1,
                bt_sanity_k=NTI_BT_SANITY_K,
            )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(bt_path_hot)

    # S29 — Path Test 1 integrated-ROI MIR (Coppola 2015 §2.2 Eq.1) en MODIS
    # Banda 21 (3.929 µm). Coppola 2015 fue diseñado ORIGINALMENTE para MODIS
    # L1B. Tras S27 (VIIRS 375m) y S28 (VIIRS 750m M13) confirmaron H_S27_1 con
    # +30pp y +2pp recall, S29 lo extiende a MODIS para rescatar Lascar 77 FNs
    # MODIS donde el primary_cluster cae en Salar de Atacama (~25 km del vent)
    # mientras MIROVA detecta el cráter a 1-2 km. Test 1 con ROI=3km centrado
    # en vent ignora el Salar y rescata el cráter sub-pixel.
    test1_hot = np.zeros_like(bt_path_hot)
    test1_triggered = False
    test1_n_contrib = 0
    test1_k_obs = 0.0
    test1_centroid_lat = None
    test1_centroid_lon = None
    test1_L_bg_local = None
    if (ENABLE_TEST1_PATH
            and vent_lat is not None and vent_lon is not None):
        test1_res = compute_test1_mir(
            bt=bt_mir, lat=lat, lon=lon,
            vent_lat=vent_lat, vent_lon=vent_lon,
            lambda_um=BAND21_LAMBDA,
            roi_km=TEST1_ROI_KM,
            inner_ring_km=TEST1_INNER_RING_KM,
            k_sigma=TEST1_K_SIGMA,
            mir_relative=TEST1_MIR_RELATIVE,
        )
        test1_triggered = test1_res["triggered"]
        test1_k_obs = test1_res["k_sigma_observed"]
        if test1_triggered:
            test1_hot = test1_res["mask_contributing"]
            test1_n_contrib = test1_res["n_contributing"]
            test1_centroid_lat = test1_res.get("centroid_lat")
            test1_centroid_lon = test1_res.get("centroid_lon")
            test1_L_bg_local = test1_res.get("L_bg")

    hot_mask_2d = bt_path_hot | nti_path_hot | dnti_ctx_hot | test1_hot

    # S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene a la mask
    # final combinada (Coppola 2016a Tabla 1). Ver explicación en process_viirs.py.
    if (ENABLE_FINAL_PIXEL_FILTER and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        final_thr_mask = dual_roi_bt_threshold(
            bt=bt_mir,
            roi_mask=np.ones_like(bt_mir, dtype=bool),
            dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg,
            inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        hot_mask_2d = hot_mask_2d & final_thr_mask

    # S16 P3.6: filtrar exclude_zones.
    # S27 T3: guard ENABLE_EXCLUDE_ZONES — en _mirova_literal queda en False
    # (parche no documentado en papers MIROVA).
    exclude_zones, active_water_bodies = guard_exclude_zones(
        exclude_zones, active_water_bodies, enabled=ENABLE_EXCLUDE_ZONES)
    n_excluded_water = 0
    if exclude_zones:
        hot_mask_2d, n_excluded_water = filter_hot_mask(
            hot_mask_2d, lat, lon, exclude_zones, active_water_bodies)
    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)
    n_bt_path = int(np.sum(bt_path_hot))
    n_nti_path = int(np.sum(nti_path_hot))

    # S27 cluster aggregation se mueve abajo (post per_pixel_vrp_mw)
    # para incluir vrp_mw del cluster contiguo principal.
    n_hotspots_clustered = 0
    primary_cluster = None

    vrp_mw = 0.0
    hotspot_lat = None
    hotspot_lon = None
    hotspot_dist_km = None
    anomaly_pixels = []

    if n_anomalous > 0:
        # Wooster MIR radiance method (Coppola 2015, Eq.7)
        # Use L_bg derived from BT median (not direct radiance median) to avoid
        # inconsistency when background annulus has heterogeneous terrain/clouds.
        # Planck is nonlinear: median(radiance) != radiance(median(BT)).
        L_bg = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))

        hotpix_bt = bt_mir[hot_rows, hot_cols]
        # Convert hot pixel BT to radiance for consistent VRP calculation
        hotpix_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * hotpix_bt)) - 1))
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]
        # S26: clip ΔL ≥ 0 — Wooster requiere excess radiancia positivo.
        # Pixels marcados hot por Path D dNTI o Test 1 pueden tener BT < t_bg
        # global (vs L_bg local). Sin clip, VRP_MIR sale negativo y rompe sumas.
        delta_L = np.maximum(hotpix_rad - L_bg, 0.0)
        per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
        vrp_mw = float(np.nansum(per_pixel_vrp_mw))

        # Build list of TOP-100 anomalous pixels sorted by VRP (descending).
        # S26: cap a 100 para evitar bloat JSON (>100MB GitHub limit). Records
        # eruptivos típicamente tienen 1000-4000 pixels detectados; los top 100
        # capturan >95% de la señal VRP y son suficientes para visualización
        # frontend. n_anomalous_pixels conserva el count total.
        sorted_indices = np.argsort(-per_pixel_vrp_mw)[:100]
        for idx in sorted_indices:
            r, c = int(hot_rows[idx]), int(hot_cols[idx])
            anomaly_pixels.append({
                "lat": round(float(lat[r, c]), 5),
                "lon": round(float(lon[r, c]), 5),
                "dist_km": round(float(dist[r, c]), 2),
                "bt_k": round(float(hotpix_bt[idx]), 2),
                "vrp_mw": round(float(per_pixel_vrp_mw[idx]), 4),
            })

        # Primary hotspot = highest VRP pixel
        hotspot_lat = anomaly_pixels[0]["lat"]
        hotspot_lon = anomaly_pixels[0]["lon"]
        hotspot_dist_km = anomaly_pixels[0]["dist_km"]

        # S27 — cluster aggregation alineado con MIROVA n_hotspots (Coppola 2016a).
        # MIROVA reporta VRP del cluster contiguo principal (~1km connectivity),
        # NO la suma indistinta de todos los pixels. Construimos un mapa 2D de
        # VRPs por pixel y agrupamos por componentes conexos 8-vecinos.
        # Cierre divergencia D1 (docs/MIROVA_DIVERGENCES.md).
        vrp_per_pixel_2d = np.zeros_like(hot_mask_2d, dtype=float)
        vrp_per_pixel_2d[hot_rows, hot_cols] = per_pixel_vrp_mw
        _vlat = vent_lat if vent_lat is not None else volcano_lat
        _vlon = vent_lon if vent_lon is not None else volcano_lon
        _clusters = cluster_hotspots(
            hot_mask_2d, lat, lon, _vlat, _vlon,
            vrp_per_pixel=vrp_per_pixel_2d,
        )
        n_hotspots_clustered = len(_clusters)
        if _clusters:
            _c = _clusters[0]
            primary_cluster = {
                "n_pixels": _c["n_pixels"],
                "vrp_mw": round(_c["vrp_mw"], 3),
                "centroid_lat": round(_c["centroid_lat"], 5),
                "centroid_lon": round(_c["centroid_lon"], 5),
                "centroid_dist_km": round(_c["centroid_dist_km"], 3),
            }

    valid_roi = roi_bt_full[~np.isnan(roi_bt_full)]
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    # E3 diag: max NTI inside the ROI
    roi_nti = np.where(roi_mask & ~np.isnan(nti), nti, np.nan)
    nti_max = float(np.nanmax(roi_nti)) if np.any(~np.isnan(roi_nti)) else float("nan")

    # Diagnostic (session 6): location of the hottest pixel in the ROI.
    # Useful when n_anomalous_pixels=0 to understand whether the hottest
    # pixel was inside or outside the vent_radius.
    t_max_dist_km_diag = float("nan")
    if len(valid_roi) > 0:
        flat_idx_max = np.nanargmax(roi_bt_full)
        r_max, c_max = np.unravel_index(flat_idx_max, roi_bt_full.shape)
        t_max_dist_km_diag = float(dist[r_max, c_max])

    # --- Vent-scale detection (weak fumarolic signals) ---
    # Same approach as VIIRS 375m: tight ROI around known vent, low threshold,
    # no ROI p95 filter. Uses the regional background (t_bg) already computed.
    # Session 10 (RF1 fix): gated by ENABLE_VENT_PATH_MODIS. In mirova_equivalent
    # this is False — MODIS 1km pixel produces too many vent-only FPs (21% vs 9%
    # in VIIRS). The eruption-path still runs; only the permissive vent-scale is off.
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    vent_hotspot_lat = None
    vent_hotspot_lon = None
    vent_hotspot_dist_km = None
    if ENABLE_VENT_PATH_MODIS and vent_lat is not None and vent_lon is not None and not np.isnan(t_bg):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt_mir), bt_mir, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                # Session 12: MODIS uses its own higher threshold (2.5K in experimental)
                # to compensate for 1km pixel dilution (SNR 2.5× vs VIIRS 4-5×).
                # Fix F1: also apply sigma gating (same as VIIRS).
                # Fix F1b: cap the sigma contribution (MAX_VENT_SIGMA_CONTRIB_K).
                sigma_contrib = min(N_SIGMA_VENT * std_bg, MAX_VENT_SIGMA_CONTRIB_K)
                modis_vent_thresh = max(MODIS_VENT_THRESHOLD_K, sigma_contrib)
                if t_max_vent > (t_bg + modis_vent_thresh):
                    L_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_max_vent)) - 1)))
                    L_bg_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))
                    vent_area = float(pixel_areas[r_vent, c_vent])
                    vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                    # S12 E4: count hot pixels + floor check
                    vent_hot_mask = vent_bt > (t_bg + modis_vent_thresh)
                    n_hot_in_vent = int(np.sum(vent_hot_mask))
                    if vrp_vent_mw >= MODIS_VENT_VRP_FLOOR_MW and n_hot_in_vent >= MIN_VENT_PIXELS:
                        n_vent_pixels = n_hot_in_vent
                        vent_hotspot_lat = float(lat[r_vent, c_vent])
                        vent_hotspot_lon = float(lon[r_vent, c_vent])
                        vent_hotspot_dist_km = float(haversine_km(vent_lat, vent_lon, vent_hotspot_lat, vent_hotspot_lon))
                    else:
                        vrp_vent_mw = 0.0

    # --- Schema unification (S14 D6) ---
    # S30: portar Regla D Test 1-priority desde process_viirs.py.
    # Cuando eruption-path detecta lejos (Salar Atacama caso Lascar MODIS) Y
    # Test 1 detecta señal sub-pixel summit (cráter), Test 1 GANA. Sin este
    # fix los 63 FNs MODIS Lascar quedaban "far" porque el primary_cluster
    # caía en el Salar a 19-27km.
    test1_hotspot_dist_km = None
    if (test1_triggered and test1_centroid_lat is not None
            and vent_lat is not None and vent_lon is not None):
        from .scan_geometry import haversine_km as _hav
        _d = _hav(vent_lat, vent_lon, np.array([test1_centroid_lat]),
                  np.array([test1_centroid_lon]))
        test1_hotspot_dist_km = float(_d[0]) if hasattr(_d, '__len__') else float(_d)

    test1_summit_hit = (test1_triggered and inner_radius_km is not None
                        and test1_hotspot_dist_km is not None
                        and test1_hotspot_dist_km <= inner_radius_km)
    eruption_far = (hotspot_dist_km is not None and inner_radius_km is not None
                    and hotspot_dist_km > inner_radius_km)

    if hotspot_lat is not None and hotspot_lon is not None:
        if test1_summit_hit and eruption_far:
            # Regla D Test 1-priority: eruption far + Test 1 summit → Test 1 gana.
            final_hotspot_lat = test1_centroid_lat
            final_hotspot_lon = test1_centroid_lon
            final_hotspot_dist_km = test1_hotspot_dist_km
            final_hotspot_source = "test1"
        else:
            final_hotspot_lat = hotspot_lat
            final_hotspot_lon = hotspot_lon
            final_hotspot_dist_km = hotspot_dist_km
            final_hotspot_source = "eruption"
    elif test1_summit_hit:
        # No hay eruption pero Test 1 detectó summit.
        final_hotspot_lat = test1_centroid_lat
        final_hotspot_lon = test1_centroid_lon
        final_hotspot_dist_km = test1_hotspot_dist_km
        final_hotspot_source = "test1"
    elif vent_hotspot_lat is not None and vent_hotspot_lon is not None:
        final_hotspot_lat = vent_hotspot_lat
        final_hotspot_lon = vent_hotspot_lon
        final_hotspot_dist_km = vent_hotspot_dist_km
        final_hotspot_source = "vent"
    else:
        final_hotspot_lat = None
        final_hotspot_lon = None
        final_hotspot_dist_km = None
        final_hotspot_source = None

    distance_class = None
    if final_hotspot_dist_km is not None and inner_radius_km is not None:
        distance_class = "summit" if final_hotspot_dist_km <= inner_radius_km else "far"

    # S30: VRP recompute cuando final_hotspot_source='test1' — replica fix
    # S26 D de process_viirs.py. Sin esto vrp_mw queda como suma del cluster
    # eruption far (Salar) o 0. Recomputamos VRP usando SOLO pixels Test 1
    # con L_bg LOCAL del ring 1-3km del cráter (no global del ROI 25km).
    # S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1).
    # Ver explicación en process_viirs.py. Default OFF.
    test1_hot_filtered = test1_hot
    if (ENABLE_TEST1_PIXEL_FILTER and final_hotspot_source == "test1"
            and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        pixel_thr_mask = dual_roi_bt_threshold(
            bt=bt_mir,
            roi_mask=np.ones_like(bt_mir, dtype=bool),
            dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg,
            inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        test1_hot_filtered = test1_hot & pixel_thr_mask

    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and test1_L_bg_local is not None
            and not np.isnan(test1_L_bg_local)):
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt_mir[t1_rows, t1_cols]
            t1_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t1_bt)) - 1))
            t1_delta_L = np.maximum(t1_rad - test1_L_bg_local, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            vrp_mw = float(np.sum(t1_vrp))

    # S31+ fix magnitud: cluster_hotspots (8-conn pixel-vecindad scipy.label)
    # — ver explicación en process_viirs.py.
    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and test1_L_bg_local is not None
            and not np.isnan(test1_L_bg_local)):
        t1_vrp_2d = np.zeros_like(bt_mir, dtype=np.float64)
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt_mir[t1_rows, t1_cols]
            t1_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t1_bt)) - 1))
            t1_delta_L = np.maximum(t1_rad - test1_L_bg_local, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp_arr = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            t1_vrp_2d[t1_rows, t1_cols] = t1_vrp_arr
            t1_clusters = cluster_hotspots(
                test1_hot_filtered, lat, lon, vent_lat, vent_lon,
                connectivity=8, vrp_per_pixel=t1_vrp_2d,
            )
            if t1_clusters:
                top = t1_clusters[0]
                primary_cluster = {
                    "n_pixels": top["n_pixels"],
                    "vrp_mw": round(top["vrp_mw"], 3),
                    "centroid_lat": round(top["centroid_lat"], 5),
                    "centroid_lon": round(top["centroid_lon"], 5),
                    "centroid_dist_km": round(top["centroid_dist_km"], 3),
                }
                n_hotspots_clustered = len(t1_clusters)

    return {
        "vrp_mw": round(vrp_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_hotspots_clustered": n_hotspots_clustered,
        "primary_cluster": primary_cluster,
        # S29: Test 1 integrated-ROI extendido a MODIS Banda 21.
        "triggered_test1": test1_triggered,
        "n_test1_pixels": test1_n_contrib,
        "test1_k_observed": round(test1_k_obs, 2) if test1_k_obs else 0.0,
        "n_vent_pixels": n_vent_pixels,
        "vent_hotspot_lat": vent_hotspot_lat,
        "vent_hotspot_lon": vent_hotspot_lon,
        "vent_hotspot_dist_km": round(vent_hotspot_dist_km, 3) if vent_hotspot_dist_km is not None else None,
        "hotspot_lat": hotspot_lat,
        "hotspot_lon": hotspot_lon,
        "hotspot_dist_km": hotspot_dist_km,
        "final_hotspot_lat": final_hotspot_lat,
        "final_hotspot_lon": final_hotspot_lon,
        "final_hotspot_dist_km": round(final_hotspot_dist_km, 3) if final_hotspot_dist_km is not None else None,
        "final_hotspot_source": final_hotspot_source,
        "distance_class": distance_class,
        "anomaly_pixels": anomaly_pixels,
        "t_bg_k": round(t_bg, 2),
        "t_max_k": round(t_max, 2),
        # Diagnostic fields (session 6) — present when MODIS path runs.
        "diag_sigma_bg_k": round(std_bg, 3),
        "diag_t_max_dist_km": round(t_max_dist_km_diag, 2) if not (t_max_dist_km_diag != t_max_dist_km_diag) else None,
        "diag_roi_p95_k": round(roi_p95, 2) if not (roi_p95 != roi_p95) else None,
        "diag_eff_threshold_k": round(effective_threshold, 2),
        # E3 NTI diagnostics
        "diag_nti_bg": round(nti_bg, 4) if not (nti_bg != nti_bg) else None,
        "diag_nti_std": round(nti_std, 4) if not (nti_std != nti_std) else None,
        "diag_nti_max": round(nti_max, 4) if not (nti_max != nti_max) else None,
        "diag_n_bt_path": n_bt_path,
        "diag_n_nti_path": n_nti_path,
        "diag_n_dnti_ctx_path": n_dnti_ctx_path,
        "sensor": "MODIS_TERRA" if "MOD0" in hdf_path.name else "MODIS_AQUA",
        "granule": hdf_path.name,
        "product_version": "nrt" if "_NRT" in hdf_path.name else "standard",
        "datetime_utc": _parse_datetime(hdf_path.name),
    }


def _parse_datetime(filename: str) -> str:
    try:
        parts = filename.split(".")
        year = int(parts[1][1:5])
        doy = int(parts[1][5:8])
        hour = int(parts[2][:2])
        minute = int(parts[2][2:4])
        import datetime
        dt = datetime.datetime(year, 1, 1) + datetime.timedelta(days=doy - 1,
                                                                  hours=hour,
                                                                  minutes=minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"
