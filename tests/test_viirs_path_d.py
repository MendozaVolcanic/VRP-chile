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


def test_experimental_hereda_la_deteccion_operacional():
    """S124: `experimental` HEREDA el path D del operacional.

    Antes (S15) este test exigía el flag en False: el perfil era una copia
    congelada del baseline de entonces y se lo mantenía divergente para
    comparar A/B. Esa razón caducó — el perfil se quedó ~100 sesiones atrás y
    dejó de ser un baseline útil para volverse ruido (en Nevados de Chillán
    daba VRP mediano 5.7 MW contra 0.357 del operacional, con máximos de 522 MW
    y distancia mediana de 25 km, o sea en el borde del radio de búsqueda y no
    en el volcán).

    Desde S124 `experimental` es `extends: mirova_equivalent` y diverge en UNA
    sola dimensión deliberada: el piso de magnitud. Este test es el guard de esa
    intención (A63) — si alguien vuelve a hacer divergir la detección, falla.
    """
    import pipeline.profile as prof
    os.environ["VRP_PROFILE"] = "experimental"
    importlib.reload(prof)
    try:
        # hereda la detección operacional...
        assert prof.ENABLE_DNTI_CONTEXTUAL_PATH is True
        assert prof.DNTI_CONTEXTUAL_C1 == 0.003
        # ...y diverge SOLO en el piso de magnitud (0.02 operacional -> 0.005).
        assert prof._cfg["thresholds"]["min_vrp_mw_viirs375"] == 0.005
    finally:
        # Restore for downstream tests
        os.environ["VRP_PROFILE"] = "mirova_equivalent"
        importlib.reload(prof)
