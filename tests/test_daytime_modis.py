# -*- coding: utf-8 -*-
"""S90 — detección diurna MODIS (clon literal MIROVA, Coppola 2016a Tabla 1).
Plan: docs/superpowers/plans/2026-05-30-daytime-modis-detection.md.
Diseño: docs/superpowers/specs/2026-05-30-daytime-modis-detection-design.md."""
import os
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")


def test_profile_exposes_daytime_constants():
    """profile.py expone las constantes día MODIS + flag (default OFF).
    mirova_equivalent NO define el flag → defaults seguros (Coppola 2016a Tabla 1)."""
    import pipeline.profile as P
    assert hasattr(P, "ENABLE_DAYTIME_MODIS")
    assert P.ENABLE_DAYTIME_MODIS is False           # default OFF, no toca operacional
    assert hasattr(P, "NTI_K1_DAY") and abs(P.NTI_K1_DAY - (-0.6)) < 1e-9
    assert hasattr(P, "N_SIGMA_MIR_DAY") and abs(P.N_SIGMA_MIR_DAY - 15.0) < 1e-9
    assert hasattr(P, "DNTI_CONTEXTUAL_C1_DAY") and abs(P.DNTI_CONTEXTUAL_C1_DAY - 0.02) < 1e-9


def test_threshold_set_selection():
    """_select_thresholds devuelve el set día/noche correcto. El set día SOLO
    aplica con enable_day=True Y is_day=True; cualquier otro caso → noche."""
    from pipeline.process_modis import _select_thresholds
    # noche → params nocturnos (Coppola 2016a Tabla 1 noche)
    night = _select_thresholds(is_day=False, enable_day=True)
    assert night["nti_k1"] == -0.8
    assert night["n_sigma_summit"] == 5.0 and night["n_sigma_scene"] == 10.0
    assert night["c1_summit"] == 0.003 and night["c1_scene"] == 0.010
    # día + flag ON → params día (15σ ambos ROIs, K1=-0.6, C1=0.02 ambos)
    day = _select_thresholds(is_day=True, enable_day=True)
    assert day["nti_k1"] == -0.6
    assert day["n_sigma_summit"] == 15.0 and day["n_sigma_scene"] == 15.0
    assert day["c1_summit"] == 0.02 and day["c1_scene"] == 0.02
    # día pero flag OFF → noche (no se aplican params día; operacional intacto)
    off = _select_thresholds(is_day=True, enable_day=False)
    assert off["nti_k1"] == -0.8 and off["n_sigma_summit"] == 5.0
