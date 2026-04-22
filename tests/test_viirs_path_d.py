"""Integration smoke test: Path D (dNTI contextual) wiring en process_viirs.py.

No corre pipeline completo (requiere L1B/GEO files). Verifica:
  1. El helper importado funciona con escena Lastarria sintetica.
  2. El flag ENABLE_DNTI_CONTEXTUAL_PATH se lee correcto por profile.
  3. El profile experimental queda con el flag false.
"""

import os
import importlib

# Lock mirova_equivalent for main test
os.environ["VRP_PROFILE"] = "mirova_equivalent"
# Force reload in case profile was already imported
import pipeline.profile
importlib.reload(pipeline.profile)

import numpy as np
from pipeline.detection_context import contextual_dnti_hot_mask


def test_path_d_isolated_hotspot_lastarria_like():
    """Escenario Lastarria: 9x9 zona tibia uniforme + 1 pixel localizado.
    Path A (sigma-anillo inflado) detectaria muchos; Path D solo el real."""
    rng = np.random.default_rng(10)
    nti = rng.normal(-0.92, 0.0008, size=(9, 9))
    bt = rng.normal(290.0, 0.4, size=(9, 9))
    nti[4, 4] = -0.895
    bt[4, 4] = 305.0
    roi = np.ones((9, 9), dtype=bool)
    mask_d = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=290.0, c1=0.003, bt_sanity_k=3.0)
    assert mask_d[4, 4] == True
    others = mask_d.copy(); others[4, 4] = False
    assert others.sum() == 0


def test_flag_enabled_in_mirova_equivalent():
    import pipeline.profile as prof
    # Already reloaded above with mirova_equivalent
    assert prof.ENABLE_DNTI_CONTEXTUAL_PATH == True
    assert prof.DNTI_CONTEXTUAL_C1 == 0.003


def test_flag_disabled_in_experimental():
    import pipeline.profile as prof
    os.environ["VRP_PROFILE"] = "experimental"
    importlib.reload(prof)
    try:
        assert prof.ENABLE_DNTI_CONTEXTUAL_PATH == False
    finally:
        # Restore for downstream tests
        os.environ["VRP_PROFILE"] = "mirova_equivalent"
        importlib.reload(prof)
