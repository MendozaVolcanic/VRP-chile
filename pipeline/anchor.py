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
