"""
store.py — Persist VRP results as JSON time series, one file per volcano.

Format: data/{volcano_name}.json
{
  "volcano": "PuyehueCordonCaulle",
  "updated": "2024-03-15T12:00:00Z",
  "records": [
    {
      "datetime_utc": "2024-03-14 00:00",
      "sensor": "MODIS_TERRA",
      "vrp_mw": 12.5,
      "n_anomalous_pixels": 3,
      "t_bg_k": 285.2,
      "t_max_k": 310.1,
      "granule": "MOD021KM.A2024074.0000.061..."
    },
    ...
  ]
}
"""

import json
import math
from pathlib import Path
from datetime import datetime, timezone

from pipeline.profile import (
    DATA_SUBDIR,
    MIN_VRP_MW_VIIRS375,
    MIN_VRP_MW_VIIRS750,
    MIN_VRP_MW_MODIS,
    ENABLE_SUM_VRP_REPORTING,
    ENABLE_DAYTIME_MODIS,
)


# Per-profile data directory: data/mirova_equivalent/ or data/experimental/
DATA_DIR = Path(__file__).parent.parent / "data" / DATA_SUBDIR

# S19 M4 2026-04-24: sanity cap físico para vrp_mw. Calibrado contra el archivo
# OSF v2.5 (615k filas globales 2000-2025): P99.99 = 39.3 GW, max histórico
# = 70 GW. 50 GW = 1.3x P99.99 / 0.71x record. Cualquier vrp_mw arriba es
# inverosímil → bug (típicamente flag DN no enmascarado en granule MODIS).
SANITY_CAP_VRP_MW = 50000.0


def _solar_elevation(lat: float, lon: float, dt_utc: datetime) -> float:
    """Quick solar elevation check. Returns degrees (negative = night)."""
    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0
    gamma = 2 * math.pi * (doy - 1) / 365.0
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma))
    solar_hour = hour_utc + lon / 15.0
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))
    lat_r = math.radians(lat)
    sin_elev = (math.sin(lat_r) * math.sin(decl)
                + math.cos(lat_r) * math.cos(decl) * math.cos(hour_angle))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))


def _reject_daytime(sensor: str, solar_elev_deg: float, enable_daytime_modis: bool) -> bool:
    """S90 — ¿rechazar este record diurno? (clon literal MIROVA).

    De noche (solar_elev <= 0) NUNCA se rechaza. De día se rechaza salvo que sea
    MODIS con el flag ON: MIROVA procesa MODIS de día (Coppola 2016a Tabla 1) pero
    VIIRS solo de noche (sin fuente MIROVA-core diurna; el n=8 diurno es Di Bella,
    NO MIROVA — regla A9). Con el flag OFF se rechaza todo el diurno (histórico)."""
    if solar_elev_deg <= 0:
        return False
    if enable_daytime_modis and str(sensor).startswith("MODIS"):
        return False
    return True


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia haversine en km. Usado por geo_class (S88 Frente B)."""
    R = 6371.0
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlat = lat2r - lat1r
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _load(volcano_name: str) -> dict:
    path = DATA_DIR / f"{volcano_name}.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"volcano": volcano_name, "updated": "", "records": []}


def _save(volcano_name: str, store: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    store["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = DATA_DIR / f"{volcano_name}.json"
    with open(path, "w") as f:
        json.dump(store, f, indent=2)


def _filter_pixels_by_distance(record: dict, max_dist_km: float) -> tuple[bool, int, int]:
    """H8 (S35): filtra anomaly_pixels pixel-por-pixel por distance.

    Reemplaza el filtro all-or-nothing antiguo (línea 119 pre-S35) que
    descartaba TODA la lista cuando el pixel más caliente individual estaba
    fuera de max_dist_km.

    Bug que resuelve: caso Puyehue lacolito 2026-05-09 05:42 — VRP-chile
    detectó 35 pixels en zona summit (7-8 km, dentro inner_radius=20) +
    1 pixel a 29 km (fuego). El pixel lejano era el más caliente → todo
    se descartaba → vrp_mw=0 aunque vrp_mir_mw=5.07.

    Returns: (changed, n_kept, n_discarded).
    Modifica record in-place:
      - record.anomaly_pixels = pixels in_range
      - record.discarded_anomaly_pixels = pixels out_of_range
      - record.vrp_mir_mw recalculado = sum(in_range vrp_mw)
      - record.hotspot_* recalculado = max in_range
      - record.discarded_reason = 'partial_eruption_hotspot_too_far' si
        hubo descarte parcial; 'eruption_hotspot_too_far' si todo descartado.
    """
    pixels = record.get("anomaly_pixels") or []
    if not pixels or max_dist_km is None:
        return False, len(pixels), 0

    in_range = [p for p in pixels if (p.get("dist_km") or 0) <= max_dist_km]
    out_range = [p for p in pixels if (p.get("dist_km") or 0) > max_dist_km]

    if not out_range:
        return False, len(in_range), 0

    record["discarded_anomaly_pixels"] = out_range
    record["anomaly_pixels"] = in_range
    record["discarded_n_pixels"] = len(out_range)

    if in_range:
        # Recalcular hotspot desde pixels preservados
        hottest = max(in_range, key=lambda p: p.get("vrp_mw", 0) or 0)
        record["hotspot_lat"] = hottest.get("lat")
        record["hotspot_lon"] = hottest.get("lon")
        record["hotspot_dist_km"] = hottest.get("dist_km")
        # vrp_mir_mw recalculado = suma in_range
        new_vrp = sum((p.get("vrp_mw") or 0) for p in in_range)
        record["vrp_mir_mw"] = round(new_vrp, 4)
        record["discarded_reason"] = "partial_eruption_hotspot_too_far"
    else:
        record["hotspot_lat"] = None
        record["hotspot_lon"] = None
        record["hotspot_dist_km"] = None
        record["vrp_mir_mw"] = 0
        record["discarded_reason"] = "eruption_hotspot_too_far"

    return True, len(in_range), len(out_range)


def append_record(volcano_name: str, record: dict,
                   volcano_lat: float = None, volcano_lon: float = None,
                   overwrite: bool = False,
                   max_hotspot_dist_km: float = None,
                   enable_pixel_level_distance_filter: bool = False,
                   max_cluster_pixels: int = None,
                   inner_radius_km: float = None,
                   volcanic_features: list = None):
    """
    Append a VRP record to the volcano's JSON file.
    Deduplicates by (datetime_utc, sensor) — safe to re-run.
    If volcano_lat/lon provided, rejects daytime records as a safety net.
    If overwrite=True, replace any existing record with the same key
    (used for reprocessing with corrected algorithms, e.g. scan-angle fix).

    S35 H8: enable_pixel_level_distance_filter (default True) usa el nuevo
    filtro pixel-por-pixel. False = comportamiento legacy (all-or-nothing).
    """
    if record is None:
        return

    # Normalize VRP field: ensure every record has a unified 'vrp_mw' field.
    # VIIRS 375m returns vrp_mir_mw/vrp_vent_mw; MODIS/VIIRS750 return vrp_mw/vrp_vent_mw.
    #
    # IMPORTANTE para consumers (S45 nota anti-confusión):
    # - `record["vrp_mw"]` es la SUMA scene-wide de todos los hot pixels in_range
    #   post-piso-sensor. NO es lo que el dashboard muestra. NO usar en audits.
    # - `record["primary_cluster"]["vrp_mw"]` es el cluster principal post
    #   vent_anchored + sanity cap 50,000 MW. ES lo que dashboard usa via
    #   `mirovaEqVrp(r)` (frontend/index.html) — además filtra cdist > inner_radius.
    # - Audits Python: replicar la lógica mirovaEqVrp:
    #     pc = r["primary_cluster"]; cdist = pc["centroid_dist_km"]; v = pc["vrp_mw"]
    #     vrp_eq = 0 if (cdist > inner_radius_km or v > 50_000) else v
    # - Refactor a `vrp_mw_scene_total` + `vrp_mw_primary` queda en backlog S46+
    #   (afecta schema, dashboard, audits, OSF mapping).
    MAX_HOTSPOT_DIST_KM = max_hotspot_dist_km if max_hotspot_dist_km is not None else 5.0

    # S35 H8: filtro pixel-por-pixel ANTES de los normalizaciones de VRP.
    # Esto garantiza que vrp_mir_mw refleje SOLO los pixels in_range, y que
    # los downstream consumers (audit, dashboard) vean datos consistentes.
    if enable_pixel_level_distance_filter:
        _filter_pixels_by_distance(record, MAX_HOTSPOT_DIST_KM)

    if "vrp_mir_mw" in record and "vrp_mw" not in record:
        record["vrp_mw"] = record["vrp_mir_mw"]
    vrp_eruption = record.get("vrp_mw", 0) or 0
    hotspot_dist = record.get("hotspot_dist_km")
    vrp_vent = record.get("vrp_vent_mw", 0) or 0

    # F47 H4 rescate (S77, A45 autorizado, tag pre-s77-f47-store-cluster-rescue):
    # Si el primary_cluster vent-anchored está DENTRO de MAX_HOTSPOT_DIST_KM
    # con VRP > 0 (= anomalía real del cráter) pero hotspot_dist apunta a un
    # pixel single far (FP aislado tipo salar térmico, incendio, etc.), el
    # gate legacy de líneas siguientes destruía el rollup. La regla del rescate:
    # cuando cluster_rescues=True, NO disparar el zero-out — usar pc.vrp_mw
    # como vrp_eruption y reescribir hotspot/final_hotspot al centroide cluster.
    #
    # Caso bandera empírico: NdC 2026-02-01 03:35 MODIS_TERRA, pc.vrp_mw=332.756
    # @ 0.536 km del vent (21 px), pero hotspot_dist=26.58 km (salar). Pre-fix
    # vrp_mw=0; post-fix vrp_mw=332.756.
    #
    # Impacto sistémico: ~200-400 records VRP recuperados en los 11 Tier A
    # (PCC 110, Copahue 79, Villarrica 59, Chaitén 49, NdC 33, Llaima 27,
    # Lascar 20...). Verificado experiments/141_f47_h4_rootcause/.
    pc = record.get("primary_cluster") or {}
    pc_cdist = pc.get("centroid_dist_km")
    pc_vrp = pc.get("vrp_mw") or 0
    cluster_rescues = (
        pc_cdist is not None
        and pc_cdist <= MAX_HOTSPOT_DIST_KM
        and pc_vrp > 0
    )

    # Safety net (legacy + H8): si después del pixel-level filter, hotspot_dist
    # sigue indicando un hotspot lejano (caso típico legacy: anomaly_pixels
    # vacío pero record["hotspot_dist_km"] fue seteado por upstream), aplicar
    # el zero-out histórico. Garantiza que vrp_mw=0 cuando solo hay señal far.
    # F47 H4 modificación: si cluster_rescues, en vez de zero-out el rollup
    # gana el cluster vent-anchored y se reescriben los campos hotspot/final.
    if hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
        if cluster_rescues:
            # F47 rescate — cluster vent-anchored gana al FP single far.
            vrp_eruption = pc_vrp
            record["hotspot_lat"] = pc.get("centroid_lat")
            record["hotspot_lon"] = pc.get("centroid_lon")
            record["hotspot_dist_km"] = pc_cdist
            # S106 ancla honesta: si el upstream ya fijó un ancla deliberada
            # (ctx_cluster / test1_roi / test1_nti_peak), el rescate conserva
            # el rollup de magnitud pero NO pisa la posición/clase honesta
            # (design 2026-06-11 §6: sin este guard, el rescue re-sesgaría
            # los records test1→vent hacia el cluster test1-derivado).
            _honest_anchor_sources = {"ctx_cluster", "test1_roi", "test1_nti_peak"}
            if record.get("final_hotspot_source") not in _honest_anchor_sources:
                record["final_hotspot_lat"] = pc.get("centroid_lat")
                record["final_hotspot_lon"] = pc.get("centroid_lon")
                record["final_hotspot_dist_km"] = pc_cdist
                record["final_hotspot_source"] = "cluster_rescue"
                # F47 follow-up S77 (audit dashboard CRITICAL): forzar
                # distance_class='summit'. Por construccion del rescate
                # (pc.centroid_dist_km <= MAX_HOTSPOT_DIST_KM Y pc.vrp_mw > 0),
                # el cluster esta cerca del vent — es summit por definicion.
                # Sin este set, el procesador upstream dejo 'far' basado en el
                # pixel single hottest del scene (que apuntaba al FP), y el
                # frontend filtraba el record via mirovaEqVrp:743 -> invisible.
                # Asegura que los ~400 records rescatados sean visibles en UI.
                record["distance_class"] = "summit"
            # Forzar la etiqueta diagnóstica de rescate (puede pisar una previa
            # de H8 — eso es correcto: rescate gana al descarte por hotspot far).
            record["discarded_reason"] = "single_pixel_far_overridden_by_cluster"
        else:
            # Comportamiento legacy: zero-out completo.
            record["discarded_hotspot_lat"] = record.get("hotspot_lat")
            record["discarded_hotspot_lon"] = record.get("hotspot_lon")
            record["discarded_hotspot_dist_km"] = hotspot_dist
            # Solo seteamos discarded_reason si no fue ya seteado por H8
            record.setdefault("discarded_reason", "eruption_hotspot_too_far")
            if record.get("anomaly_pixels"):
                record["discarded_anomaly_pixels"] = record["anomaly_pixels"]
            record["hotspot_lat"] = None
            record["hotspot_lon"] = None
            record["hotspot_dist_km"] = None
            record["anomaly_pixels"] = []
            vrp_eruption = 0

    # F52-A/S77 (A45) — Per-volcano cap sobre n_pixels del cluster.
    # Villarrica tiene clusters glaciares (Pichillancahue NW) de 16-86 pixels
    # con ΔT 5-11K (snow/ice marginal, no lava real). MIROVA los filtra,
    # nosotros los sumábamos → ratio mediano 10.91× vs MIROVA. Otros Tier A
    # con clusters grandes (Lastarria/Llaima/Copahue mediana 35-46 px) están
    # BIEN calibrados porque sus pixels tienen ΔT alto (lava real) — por eso
    # el cap es per-volcano (yaml override `max_cluster_pixels: 12` solo
    # Villarrica). Sin override (None ó 0) → comportamiento legacy.
    # Ver docs/F52_VILLARRICA_OVER_ESTIMATION_S77.md.
    if max_cluster_pixels is not None and max_cluster_pixels > 0:
        pc_for_cap = record.get("primary_cluster") or {}
        pc_n_pixels = pc_for_cap.get("n_pixels") or 0
        if pc_n_pixels > max_cluster_pixels:
            vrp_eruption = 0
            record["discarded_reason"] = "cluster_too_large_for_volcano"
            record["discarded_max_cluster_pixels"] = max_cluster_pixels
            record["discarded_actual_cluster_pixels"] = pc_n_pixels

    record["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)

    # S20 Regla D — vent-priority (2026-04-25, espíritu S9 traducido a S14+).
    # Si vrp_vent_mw > 0, el vent-path detectó señal sub-pixel del cráter
    # (por construcción dentro del vent_radius_km). Forzamos distance_class=
    # 'summit' y final_hotspot apunta al vent, independientemente de qué
    # pixel far más caliente exista en el record.
    #
    # Causa del fix: forense H17 S20 mostró que 8/15 FN Tupungatito eran
    # "T3" — vent-path SÍ detectaba el cráter (vrp_vent>0) pero distance_class
    # quedaba 'far' porque un eruption-path far más caliente "robaba" el
    # clasificador. El vent en MIROVA implica anomalía real del cráter.
    #
    # Validación contrafactual (3 volcanes, 30 días): aplicar regla D sobre
    # JSONs ya generados subió recall 0.25 → 0.69 (+0.44). Chaitén alcanzó
    # 1.00 (iguala S9 0.93+).
    # S23 audit fix: usar .get() para evitar KeyError silencioso si la key
    # vent_hotspot_dist_km está AUSENTE del dict (no None — ausente).
    # Mantiene comportamiento legacy S20 deliberado:
    # vrp_vent>0 → distance_class='summit' aunque coords vent estén missing
    # ('podemos etiquetarlo correctamente como summit aunque no tengamos
    # coords' — test_legacy_vent_without_coords_classified_summit).
    # Solo se reescriben final_hotspot_* si los 3 campos están presentes y no-None.
    if vrp_vent > 0:
        record["distance_class"] = "summit"
        vh_lat = record.get("vent_hotspot_lat")
        vh_lon = record.get("vent_hotspot_lon")
        vh_dist = record.get("vent_hotspot_dist_km")
        if vh_lat is not None and vh_lon is not None and vh_dist is not None:
            record["final_hotspot_lat"] = vh_lat
            record["final_hotspot_lon"] = vh_lon
            record["final_hotspot_dist_km"] = vh_dist
            record["final_hotspot_source"] = "vent"

    # S19 M4 2026-04-24: sanity cap físico antes del piso por sensor.
    # 50,000 MW = 1.3x el P99.99 del archivo OSF v2.5 (615k filas globales
    # 2000-2025) y 0.71x el récord histórico documentado por MIROVA (~70 GW
    # Etna paroxismo). Cualquier vrp por arriba es estadística y físicamente
    # inverosímil — bandera de bug (típicamente flag DN no enmascarado, ej.
    # caso Lastarria 2026-04-23 01:50 con BT=566 K que generó 1.5M MW).
    # Records sobre el cap se clampean a 0 con el valor crudo preservado
    # en diag_rejected_sanity_cap_mw para auditoría posterior.
    if record["vrp_mw"] > SANITY_CAP_VRP_MW:
        record["diag_rejected_sanity_cap_mw"] = record["vrp_mw"]
        record["diag_sanity_cap_threshold_mw"] = SANITY_CAP_VRP_MW
        record["vrp_mw"] = 0.0

    # S41 fix: sanity cap también a primary_cluster.vrp_mw. El cap S19 M4
    # original aplicaba solo a record.vrp_mw (sum total), dejando pasar el
    # caso Lastarria 2026-04-23 01:50 MODIS_TERRA donde el granule tenía
    # BT=566K (sensor saturado, flag DN no enmascarado) → pc.vrp_mw=1.6M MW
    # pero record.vrp_mw=0 (post-floor) → cap original no aplicaba a pc.
    # El dashboard usa pc.vrp_mw via mirovaEqVrp → values garbage llegaban
    # al UI. Fix: aplicar mismo cap a pc.vrp_mw, marcar diag para auditoría.
    pc = record.get("primary_cluster") or {}
    pc_vrp = pc.get("vrp_mw", 0) or 0
    if pc_vrp > SANITY_CAP_VRP_MW:
        record["diag_pc_rejected_sanity_cap_mw"] = pc_vrp
        record["primary_cluster"]["vrp_mw"] = 0.0
        # Si record.vrp_mw también es 0 (caso Lastarria garbage), marcar
        # discarded_reason explícito.
        if record["vrp_mw"] == 0 and not record.get("discarded_reason"):
            record["discarded_reason"] = "sanity_cap_pc_garbage"

    # S12 2026-04-15: piso VRP por sensor (paridad MIROVA).
    # Si vrp_mw < piso_sensor, se trata como no-detección (vrp_mw = 0).
    # Preserva el valor original en diag_vrp_raw_mw para auditoría.
    sensor = record.get("sensor", "")
    if "375" in sensor or sensor in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"):
        floor = MIN_VRP_MW_VIIRS375
    elif "750" in sensor:
        floor = MIN_VRP_MW_VIIRS750
    elif "MODIS" in sensor:
        floor = MIN_VRP_MW_MODIS
    else:
        floor = 0.0
    if floor > 0 and 0 < record["vrp_mw"] < floor:
        record["diag_vrp_raw_mw"] = record["vrp_mw"]
        record["diag_vrp_floor_mw"] = floor
        record["vrp_mw"] = 0.0
        # El operador sigue viendo el record (con vrp=0) pero no cuenta
        # como detección en auditoría ni en dashboard "últimas VRP>0".

    # Normalize t_max_k for VIIRS 375m (uses t_max_i04_k internally)
    if "t_max_i04_k" in record and "t_max_k" not in record:
        record["t_max_k"] = record["t_max_i04_k"]

    # S88 Frente B — geo_class: etiqueta GEOMÉTRICA descriptiva del
    # primary_cluster respecto al cono volcánico. NO cambia detección, VRP ni
    # filtra nada — solo describe (diseño:
    # docs/superpowers/specs/2026-05-29-s88-pc-classification-design.md):
    #   "summit"    cluster dentro del inner_radius_km (es el cráter).
    #   "extension" fuera del inner pero <= ext_km de una feature volcánica
    #               catalogada (lacolito PCC, Lazufre, El Agrio... features
    #               reales no publicadas por MIROVA — categoría b del marco S86).
    #   "far"       ni cráter ni feature catalogada cerca.
    # Solo se computa si inner_radius_km provisto (legacy intacto sin él). NO
    # usa el gate t_bg<260K (refutado S86 — perdería Lascar 02-17 eruptivo). El
    # cruce con MIROVA (mirova_confirmed) vive en el frontend, NO acá (no
    # acoplar el NRT a un CSV externo de scraping).
    if inner_radius_km is not None:
        pc_geo = record.get("primary_cluster") or {}
        pcd = pc_geo.get("centroid_dist_km")
        if pcd is not None:
            if pcd <= inner_radius_km:
                pc_geo["geo_class"] = "summit"
            else:
                geo = "far"
                plat = pc_geo.get("centroid_lat")
                plon = pc_geo.get("centroid_lon")
                if volcanic_features and plat is not None and plon is not None:
                    for feat in volcanic_features:
                        d = _haversine_km(plat, plon, feat["lat"], feat["lon"])
                        if d <= feat.get("ext_km", 2.0):
                            geo = "extension"
                            break
                pc_geo["geo_class"] = geo

    # S37 H_D8_5 — sum VRP reporting (Coppola 2016a eq 8 + líneas 510-513).
    # Cuando ENABLE_SUM_VRP_REPORTING=True, el record persiste dos campos
    # adicionales que reflejan la convención MIROVA literal:
    #   - vrp_mw_sum_active: Σ RP_pix sobre TODOS los anomaly pixels reportados
    #     (no primary cluster). MIROVA no selecciona cluster — eq 8 paper.
    #   - hotspot_dist_km_furthest: distancia al vent del active pixel MÁS
    #     LEJANO. Paper líneas 510-513: "distance between main vent and the
    #     centre of the furthermost alerted pixel".
    # Ambos campos respetan el sensor floor (si vrp_mw fue zero-out por floor,
    # vrp_mw_sum_active también se reporta 0). Frontend / audit pueden usar
    # estos campos para reproducir la métrica MIROVA-style sin tocar
    # primary_cluster (que sigue presente para backward compat).
    if ENABLE_SUM_VRP_REPORTING:
        pixels = record.get("anomaly_pixels") or []
        if pixels and record.get("vrp_mw", 0) > 0:
            sum_vrp = sum((p.get("vrp_mw") or 0) for p in pixels)
            dists = [p.get("dist_km") for p in pixels if p.get("dist_km") is not None]
            record["vrp_mw_sum_active"] = round(float(sum_vrp), 4)
            record["hotspot_dist_km_furthest"] = (
                round(float(max(dists)), 3) if dists else None
            )
        else:
            record["vrp_mw_sum_active"] = 0.0
            record["hotspot_dist_km_furthest"] = None

    # Safety net: reject daytime records (solar contamination → false VRP).
    # S90: con ENABLE_DAYTIME_MODIS, MODIS diurno SÍ se acepta (Coppola 2016a
    # params día); VIIRS diurno sigue rechazado. Flag OFF = rechazo histórico.
    if volcano_lat is not None and volcano_lon is not None:
        dt_str = record.get("datetime_utc", "")
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            elev = _solar_elevation(volcano_lat, volcano_lon, dt)
            if _reject_daytime(record.get("sensor", ""), elev, ENABLE_DAYTIME_MODIS):
                print(f"  STORE REJECT daytime: {dt_str} {record.get('sensor')} "
                      f"(solar elev={elev:.1f}°)")
                return
        except (ValueError, TypeError):
            pass  # Can't parse — store anyway

    store = _load(volcano_name)
    key = (record.get("datetime_utc"), record.get("sensor"))
    existing_idx = {
        (r.get("datetime_utc"), r.get("sensor")): i
        for i, r in enumerate(store["records"])
    }
    if key in existing_idx:
        existing = store["records"][existing_idx[key]]
        # S12: auto-upgrade NRT -> standard. If the previously stored record
        # came from a LANCE-NRT granule and the new one is a definitive
        # Standard product, replace it even without overwrite=True. This
        # lets the regular 6-hourly NRT cron automatically consolidate the
        # historical archive to Standard once NASA publishes the L1B,
        # typically 3-5 days after the overpass. No separate weekly cron
        # needed, no records lost, no bias accumulated.
        is_upgrade = (
            existing.get("product_version") == "nrt"
            and record.get("product_version") == "standard"
        )
        if overwrite or is_upgrade:
            store["records"][existing_idx[key]] = record
            store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
            _save(volcano_name, store)
            if is_upgrade and not overwrite:
                print(f"  STORE upgrade NRT->standard: {key[0]} {key[1]}")
    else:
        store["records"].append(record)
        store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
        _save(volcano_name, store)


def get_records(volcano_name: str, last_n: int = None) -> list:
    store = _load(volcano_name)
    records = store["records"]
    if last_n:
        records = records[-last_n:]
    return records
