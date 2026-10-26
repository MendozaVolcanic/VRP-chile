"""geo_utils.py — small geometry helpers shared across the pipeline.

Two distinct geographic roles, kept separate on purpose (S98, enfoque B):

  * **grid center** — the center of MIROVA's processing scene (the 50x50 km
    KMZ GroundOverlay LatLonBox). Used for grid/ROI extent and as an audit
    cross-check against the distance MIROVA reports. This is `mirova_center`.

  * **detection anchor** — the physical crater (`vent_lat/vent_lon`,
    field-verified by Nicolas). Used to anchor vent-path dual-ROI detection,
    `vent_anchored` cluster selection, `distance_class`, and the distance shown
    in the dashboard.

Why they are separate: `mirova_center` is the *frame* of the image, not where
the heat is. For Tupungatito it sits 4.86 km south of the crater (on the
glacier), PuyehueCordonCaulle 7.57 km, PlanchonPeteroa 2.02 km. Conflating the
two (older `get_effective_vent`, mirova_center-priority) made detection,
clustering and distance anchor on the grid center, so the crater was reported
"far" and the cold glacier field won cluster selection. S65 fixed it by
dropping Tupungatito's mirova_center; S80 regenerated all 11 from the KMZ and
silently reverted it. Splitting the roles makes the fix robust to future
consolidations (see tests/test_detection_anchor.py guard).

See `volcanoes.yaml` fields `mirova_center_lat`/`mirova_center_lon` (grid) and
`vent_lat`/`vent_lon` (crater).
"""


def get_grid_center(volcano: dict) -> tuple:
    """Return (lat, lon) of MIROVA's grid/scene center.

    Priority:
      1. mirova_center_lat/lon (MIROVA reference center, KMZ-derived)
      2. vent_lat/vent_lon
      3. lat/lon (volcano centroid)
      4. (None, None)

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


def get_detection_anchor(volcano: dict) -> tuple:
    """Return (lat, lon) to anchor detection, clustering and distance.

    Priority — the crater wins (this is the S98 fix):
      1. vent_lat/vent_lon (Nicolas field-verified morphological crater)
      2. mirova_center_lat/lon (grid center fallback)
      3. lat/lon (volcano centroid)
      4. (None, None)

    Partial vent (only lat OR only lon) is treated as unset.

    Uniform across all 11 volcanoes (no per-volcano special-casing): for the 8
    with offset <0.55 km the crater ~= grid center, so this is a no-op; for
    Tupungatito/PCC/PlanchonPeteroa it moves the anchor back onto the crater.
    """
    v_lat = volcano.get("vent_lat")
    v_lon = volcano.get("vent_lon")
    if v_lat is not None and v_lon is not None:
        return (v_lat, v_lon)

    mc_lat = volcano.get("mirova_center_lat")
    mc_lon = volcano.get("mirova_center_lon")
    if mc_lat is not None and mc_lon is not None:
        return (mc_lat, mc_lon)

    return (volcano.get("lat"), volcano.get("lon"))


def get_effective_vent(volcano: dict) -> tuple:
    """DEPRECATED (S98): grid-center-priority resolver kept as an alias of
    `get_grid_center` for backward compatibility with offline experiment
    scripts. Production detection/clustering now uses `get_detection_anchor`.
    Do NOT use for new detection code — use `get_detection_anchor`.
    """
    return get_grid_center(volcano)
