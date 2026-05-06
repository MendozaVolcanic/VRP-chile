"""S33 — métricas de audit centralizadas, alineadas con frontend Driver A.

Función `mirova_eq_vrp(record, volcano_name)` replica la lógica del frontend
`mirovaEqVrp` (frontend/index.html, frontend/diario.html). Centraliza para
evitar drift entre lógica frontend y audit Python.

Invariantes documentadas (S33 bug fix):

  1. Si `record.distance_class` es 'far' → return 0.
     MIROVA no reporta clusters far del cráter.

  2. Si `record.primary_cluster` es None (records pre-S27) → return vrp_mw global.
     Backward-compat para data legacy sin cluster aggregation.

  3. **CRÍTICO (bug S33)**: si `pc.centroid_dist_km > inner_radius_km` del
     volcán → return 0, AUNQUE distance_class sea 'summit'.

     Por qué: distance_class se calcula desde `final_hotspot_*` (que cuando
     Test 1 dispara apunta al centroide ROI 1-3km del vent). Pero
     primary_cluster se elige por VRP máximo, puede ser un cluster
     geográficamente lejano (Salar Atacama, lago Conguillío, etc.).

     Sin este chequeo, clusters far reportaban su VRP como si fuera del
     cráter — engañando los audits S27→S32 con TPs falsos.

  4. Si pc.centroid_dist_km es None → return pc.vrp_mw (sin validar dist).
     Records pre-S27 que no exportaron centroid_dist_km.

  5. Caso normal (pc dentro de inner_radius) → return pc.vrp_mw.

Inner radius MIROVA por volcán Tier A (oficial, de KMZs MIROVA web).
"""
from __future__ import annotations

INNER_RADIUS_KM_TIER_A = {
    'Lascar': 5,
    'Lastarria': 3,
    'Tupungatito': 7,
    'Villarrica': 5,
    'PuyehueCordonCaulle': 20,  # lacolito 7-9km del centro
    'Copahue': 4,
    'NevadosDeChillan': 5,
    'Llaima': 5,
    'Chaiten': 5,
    'PlanchonPeteroa': 3,
    'Isluga': 5,
}

DEFAULT_INNER_KM = 10  # Conservative fallback for non-Tier-A or unknown volcanoes


def mirova_eq_vrp(record, volcano_name=None, inner_km=None):
    """VRP MIROVA-equivalent: cluster contiguo del cráter dentro de inner_radius.

    Args:
        record: dict del JSON de records pipeline.
        volcano_name: str, name from JSON filename (e.g. 'Lastarria').
            Used to lookup INNER_RADIUS_KM_TIER_A.
        inner_km: float optional. Override explícito del inner_radius
            (precedencia sobre volcano_name lookup).

    Returns:
        float: VRP (MW) o 0.

    Lógica (S33 fixed, alineada con frontend mirovaEqVrp):
        1. record None → 0
        2. distance_class == 'far' → 0
        3. no primary_cluster → return vrp_mw global (legacy fallback)
        4. pc.centroid_dist_km > inner_radius_km → 0 (bug S33 fix)
        5. else → return pc.vrp_mw
    """
    if not record:
        return 0
    # Determinar inner radius effectivo
    if inner_km is None:
        inner_km = INNER_RADIUS_KM_TIER_A.get(volcano_name, DEFAULT_INNER_KM)
    # Regla 2: si dist_class es 'far' (asignado pipeline), MIROVA no reportaría
    dc = record.get('distance_class')
    if dc and dc != 'summit':
        return 0
    # Regla 3: legacy fallback si no hay primary_cluster
    pc = record.get('primary_cluster')
    if not pc:
        return record.get('vrp_mw') or 0
    # Regla 4 (bug S33 fix): validar pc.centroid_dist_km contra inner_radius
    pc_dist = pc.get('centroid_dist_km')
    if pc_dist is not None and pc_dist > inner_km:
        return 0
    # Regla 5: caso normal
    return pc.get('vrp_mw', 0) or 0
