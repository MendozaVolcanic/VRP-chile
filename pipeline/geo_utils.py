"""geo_utils.py — small geometry helpers shared across the pipeline.

Currently contains the effective-vent resolver, introduced to handle
cases where MIROVA centers its processing scene off the morphological
summit (Tupungatito ~3 km SE, Planchon-Peteroa ~1.9 km N). For paridad
MIROVA our vent-path detection and distance reporting must anchor at
MIROVA's reference center, not at the geologist's field vent.

See `volcanoes.yaml` fields `mirova_center_lat` / `mirova_center_lon`
and the KMZ GroundOverlay LatLonBox centers extracted S15 2026-04-21.
"""


def get_effective_vent(volcano: dict) -> tuple:
    """Return (lat, lon) to use for vent-path detection and distance reporting.

    Priority:
      1. mirova_center_lat/lon (MIROVA reference center, KMZ-derived)
      2. vent_lat/vent_lon (Nicolas field-verified morphological vent)
      3. lat/lon (volcano centroid fallback)
      4. (None, None) if nothing is available

    Partial mirova_center (only lat OR only lon) is treated as unset.
    """
    mc_lat = volcano.get("mirova_center_lat")
    mc_lon = volcano.get("mirova_center_lon")
    if mc_lat is not None and mc_lon is not None:
        return (mc_lat, mc_lon)

    v_lat = volcano.get("vent_lat")
    v_lon = volcano.get("vent_lon")
    if v_lat is not None and v_lon is not None:
        return (v_lat, v_lon)

    return (volcano.get("lat"), volcano.get("lon"))
