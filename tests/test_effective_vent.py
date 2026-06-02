"""Test get_effective_vent — DEPRECATED grid-center resolver (S98 alias).

Since S98 `get_effective_vent` is an alias of `get_grid_center`
(mirova_center-priority); it is NO LONGER the detection anchor. Detection,
clustering and distance now use `get_detection_anchor` (crater-priority) —
see tests/test_detection_anchor.py. These tests pin the legacy grid-center
behavior so offline experiment scripts that still import it keep working.
Priority: mirova_center_lat/lon > vent_lat/vent_lon > lat/lon.
"""

from pipeline.geo_utils import get_effective_vent


def test_mirova_center_takes_precedence():
    v = {"lat": -33.4, "lon": -69.8,
         "vent_lat": -33.389044, "vent_lon": -69.826374,
         "mirova_center_lat": -33.4269, "mirova_center_lon": -69.8004}
    assert get_effective_vent(v) == (-33.4269, -69.8004)


def test_falls_back_to_vent_when_no_mirova_center():
    v = {"lat": -23.37, "lon": -67.73,
         "vent_lat": -23.363, "vent_lon": -67.730}
    assert get_effective_vent(v) == (-23.363, -67.730)


def test_falls_back_to_volcano_center_when_no_vent():
    v = {"lat": -42.8, "lon": -72.65}
    assert get_effective_vent(v) == (-42.8, -72.65)


def test_returns_none_when_nothing_set():
    assert get_effective_vent({}) == (None, None)


def test_partial_mirova_center_falls_back_cleanly():
    """If only one of mirova_center_lat/lon is set, treat as unset (defensive)."""
    v = {"vent_lat": -33.389, "vent_lon": -69.826,
         "mirova_center_lat": -33.4269}
    assert get_effective_vent(v) == (-33.389, -69.826)
