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


def test_scene_is_day_from_modis_filename():
    """_scene_is_day clasifica día/noche por elevación solar desde el nombre del
    granule MODIS (formato <prod>.A<YYYY><DDD>.<HHMM>...) + coords del volcán.
    Casos reales NdC (lat -36.83, lon -71.4):
    - 2026-03-17 13:15 UTC (doy 076) → solar ~08:30 local → DÍA.
    - 2026-05-14 05:48 UTC (doy 134) → solar ~01:00 local → NOCHE.
    """
    from pipeline.process_modis import _scene_is_day
    assert _scene_is_day("MOD021KM.A2026076.1315.061.hdf", -36.83, -71.4) is True
    assert _scene_is_day("MOD021KM.A2026134.0548.061.hdf", -36.83, -71.4) is False
    # nombre no parseable → asumir noche (conservador, no procesar diurno dudoso)
    assert _scene_is_day("garbage.hdf", -36.83, -71.4) is False


def test_store_daytime_gate_decision():
    """_reject_daytime: literal MIROVA. De noche nunca rechaza. De día rechaza
    salvo MODIS con el flag ON (VIIRS diurno SIEMPRE rechazado — sin fuente
    MIROVA-core diurna para VIIRS)."""
    from pipeline.store import _reject_daytime
    # Noche (elev <= 0): nunca rechaza, sin importar sensor/flag.
    assert _reject_daytime("MODIS_AQUA", -10.0, True) is False
    assert _reject_daytime("VIIRS_NOAA20", -5.0, True) is False
    # Día + flag OFF: rechaza todo (comportamiento histórico).
    assert _reject_daytime("MODIS_AQUA", 12.0, False) is True
    assert _reject_daytime("VIIRS_NOAA20", 12.0, False) is True
    # Día + flag ON: MODIS pasa, VIIRS sigue rechazado (literal MIROVA).
    assert _reject_daytime("MODIS_TERRA", 12.0, True) is False
    assert _reject_daytime("VIIRS_NOAA20", 12.0, True) is True
    assert _reject_daytime("VIIRS_NOAA20_750", 12.0, True) is True
