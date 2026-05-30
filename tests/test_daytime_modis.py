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
