"""S106 — Ancla espacial honesta (design 2026-06-11 §3.1).

Cascada de POSICIÓN del record (final_hotspot_*). Nunca decide magnitud ni
detección: los bloques de magnitud del pipeline siguen leyendo la semántica
legacy interna; este helper se aplica como override de los campos de posición
justo antes de armar el record.

Principio (auditoría S106 papers-first): un test integrado de ROI no tiene
posición por píxel — la posición MIROVA-real viene de los píxeles flaggeados
por los tests contextuales (Tests 2/3 Coppola 2016a, inmunes a topografía
A69). Cuando solo disparó el Test1 integrado, la posición honesta es el vent
del ROI (modo "vent") o el píxel de NTI máximo del ROI (modo "nti_peak").
"""


def honest_anchor_applies(*, enabled, first_pass_gate_enabled, n_first_pass_summit):
    """S111 D11 — ¿se aplica el override de posición del ancla honesta MODIS?

    FICHA SDA — Nivel 2 (decisión de clasificación). POR QUÉ: el ancla honesta
    MODIS, si se aplicara sin condición, promovería a ``summit`` los artefactos
    topográficos del valle de Nevados de Chillán (A69/D11). Esos clusters
    near-crater son 100% recaptura del ``second_pass_adjacent`` que el gate
    intra-radio S85 preserva (A55, probe assembly run 27625289232: first_pass_
    summit ARTEFACTO=0 / REAL=57), NO señal volcánica del primer pase. El gate
    condiciona el override a que exista señal-summit PROPIA genuina: ≥1 píxel del
    FIRST-PASS (Tests 2&3 de Coppola 2016a, contextuales/espectrales, inmunes a
    topografía vía ETI) dentro del ``inner_radius_km``.

    Args:
        enabled: flag maestro ``ENABLE_HONEST_ANCHOR_MODIS``.
        first_pass_gate_enabled: sub-flag ``ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE``.
            Con False (brazo A/B "ancla-sin-gate"), el override se aplica siempre
            que ``enabled`` (comportamiento S106). Con True, requiere first-pass summit.
        n_first_pass_summit: nº de píxeles del first-pass Tests 2&3 dentro del
            inner_radius (excluye recaptura second-pass / gate S85).

    Returns:
        True si process_modis debe sobrescribir final_hotspot_* con el ancla
        honesta; False si debe conservar la cascada legacy (clasificación de hoy).
    """
    if not enabled:
        return False
    if not first_pass_gate_enabled:
        return True
    # bool() normaliza el tipo: n_first_pass_summit puede llegar como escalar numpy
    # de un caller futuro; sin esto el retorno sería numpy.bool_ (no JSON-safe, rompe
    # `is True`/`is False` aguas abajo). En el pipeline real ya viene int()-wrapped.
    return bool((n_first_pass_summit or 0) > 0)


def resolve_honest_anchor(ctx_cluster, test1_triggered, test1_summit_hit,
                          vent_lat, vent_lon, nti_peak, vent_hotspot,
                          loose_pixel, inner_radius_km, mode="vent"):
    """Devuelve (lat, lon, dist_km, source) para final_hotspot_*.

    ctx_cluster:  dict centroid_lat/centroid_lon/centroid_dist_km del cluster
                  contextual vent-anchored (hot_mask first-pass, sin Test1) o None.
    nti_peak:     dict lat/lon/dist_km del píxel de NTI máximo del ROI o None.
    vent_hotspot: dict lat/lon/dist_km del vent-path legacy o None.
    loose_pixel:  dict lat/lon/dist_km del píxel suelto scene-wide o None.
    mode:         "vent" | "nti_peak" (destino de los records Test1-dominantes).
    """
    ctx_far = (ctx_cluster is not None and inner_radius_km is not None
               and ctx_cluster["centroid_dist_km"] > inner_radius_km)

    if ctx_cluster is not None and not (ctx_far and test1_summit_hit):
        return (ctx_cluster["centroid_lat"], ctx_cluster["centroid_lon"],
                ctx_cluster["centroid_dist_km"], "ctx_cluster")
    if test1_triggered:
        if mode == "nti_peak" and nti_peak is not None:
            return (nti_peak["lat"], nti_peak["lon"], nti_peak["dist_km"],
                    "test1_nti_peak")
        return (vent_lat, vent_lon, 0.0, "test1_roi")
    if vent_hotspot is not None:
        return (vent_hotspot["lat"], vent_hotspot["lon"],
                vent_hotspot["dist_km"], "vent")
    if loose_pixel is not None:
        return (loose_pixel["lat"], loose_pixel["lon"],
                loose_pixel["dist_km"], "eruption_loose")
    return (None, None, None, None)
