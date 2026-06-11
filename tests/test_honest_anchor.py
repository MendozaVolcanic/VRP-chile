"""Tests S106 — cascada de ancla espacial honesta (design 2026-06-11 §3.1).

La cascada decide SOLO posición/clase (lat, lon, dist, source); nunca magnitud.
Casos del design: ctx-cluster gana; Regla D honesta (ctx far + test1 summit →
test1); test1 → vent (modo A) o NTI-peak (modo B, fallback vent); vent-path
legacy; píxel suelto como último recurso documentado; nada → None.
"""
from pipeline.anchor import resolve_honest_anchor

VENT = (-33.389044, -69.826374)  # Tupungatito
CTX_SUMMIT = {"centroid_lat": -33.3922, "centroid_lon": -69.8281, "centroid_dist_km": 0.39}
CTX_FAR = {"centroid_lat": -33.30, "centroid_lon": -69.70, "centroid_dist_km": 14.9}
NTI_PEAK = {"lat": -33.3895, "lon": -69.8270, "dist_km": 0.07}
LOOSE = {"lat": -33.28, "lon": -69.66, "dist_km": 19.6}
VENT_HS = {"lat": -33.3891, "lon": -69.8262, "dist_km": 0.02}
INNER = 7.0


def _call(**kw):
    base = dict(ctx_cluster=None, test1_triggered=False, test1_summit_hit=False,
                vent_lat=VENT[0], vent_lon=VENT[1], nti_peak=None,
                vent_hotspot=None, loose_pixel=None, inner_radius_km=INNER,
                mode="vent")
    base.update(kw)
    return resolve_honest_anchor(**base)


def test_ctx_cluster_summit_gana():
    lat, lon, dist, src = _call(ctx_cluster=CTX_SUMMIT, test1_triggered=True,
                                test1_summit_hit=True)
    assert (lat, lon, dist) == (-33.3922, -69.8281, 0.39)
    assert src == "ctx_cluster"


def test_regla_d_honesta_ctx_far_test1_summit_gana_test1():
    lat, lon, dist, src = _call(ctx_cluster=CTX_FAR, test1_triggered=True,
                                test1_summit_hit=True)
    assert (lat, lon) == VENT
    assert dist == 0.0
    assert src == "test1_roi"


def test_ctx_far_sin_test1_ancla_ctx():
    # contextual far sin test1 summit: el cluster ES la detección, far honesto.
    lat, lon, dist, src = _call(ctx_cluster=CTX_FAR)
    assert dist == 14.9
    assert src == "ctx_cluster"


def test_test1_only_modo_vent():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True)
    assert (lat, lon, dist) == (VENT[0], VENT[1], 0.0)
    assert src == "test1_roi"


def test_test1_only_modo_nti_peak():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True,
                                nti_peak=NTI_PEAK, mode="nti_peak")
    assert (lat, lon, dist) == (-33.3895, -69.8270, 0.07)
    assert src == "test1_nti_peak"


def test_modo_nti_peak_sin_peak_cae_a_vent():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True,
                                mode="nti_peak")
    assert (lat, lon, dist) == (VENT[0], VENT[1], 0.0)
    assert src == "test1_roi"


def test_vent_path_legacy_fallback():
    lat, lon, dist, src = _call(vent_hotspot=VENT_HS)
    assert dist == 0.02
    assert src == "vent"


def test_pixel_suelto_ultimo_recurso():
    lat, lon, dist, src = _call(loose_pixel=LOOSE)
    assert dist == 19.6
    assert src == "eruption_loose"


def test_nada_devuelve_none():
    assert _call() == (None, None, None, None)


def test_prioridad_test1_sobre_vent_path_y_loose():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=False,
                                vent_hotspot=VENT_HS, loose_pixel=LOOSE)
    # test1 triggered (aunque no summit-hit) con ctx ausente → test1_roi:
    # la integral existe, su posición honesta es el vent del ROI.
    assert src == "test1_roi"
