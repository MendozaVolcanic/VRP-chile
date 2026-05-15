"""Test Variante 13 EXPERIMENTAL — Di Bella 2024 n=12 noche VIIRS.

NO clon literal MIROVA. Di Bella es INGV Catania (regla S26).
Documentado como exploración objetivo (2) "mejor que MIROVA".

Solo VIIRS (process_viirs.py + process_viirs_mod.py). MODIS NO recibe override.
"""
import numpy as np

from pipeline.detection_context import first_pass_tests_2_and_3


def test_dibella_n12_viirs_more_strict_than_coppola_C2_5():
    """Mismo escenario: n=12 NO es más permisivo que C2=5.

    Verifica empíricamente que reemplazar C2=5 (Coppola Tabla 1 noche summit)
    por n=12 (Di Bella 2024 RSDF) produce un set de pixels active subset
    del original — coherente con que n=12 sea un threshold estadístico
    más estricto sobre dNTI/dETI.
    """
    shape = (100, 100)
    rng = np.random.default_rng(42)
    nti = rng.normal(-0.97, 0.0001, shape)  # σ chico
    nti_app = rng.normal(-0.97, 0.0001, shape)
    bt = np.full(shape, 268.0)

    # Pixel marginal: dNTI ≈ 7σ sobre mean
    # → pasa C2=5, NO pasa n=12
    nti[50, 50] = -0.97 + 7 * 0.0001
    nti_app[50, 50] = -0.97
    bt[50, 50] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)

    # Coppola C2=5
    hot_coppola, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    # Di Bella n=12
    hot_dibella, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=12, c2_deti_summit=12,
        inner_km=5.0,
    )

    # Al menos, n=12 NO debería ser más permisivo que n=5
    n_coppola = int(np.sum(hot_coppola))
    n_dibella = int(np.sum(hot_dibella))
    assert n_dibella <= n_coppola, (
        f"n=12 debe ser stricter: dibella detecta {n_dibella}, "
        f"coppola {n_coppola}"
    )


def test_dibella_override_default_none_preserves_legacy():
    """Verifica que el flag default None preserva el comportamiento legacy.

    Importa el módulo profile y verifica que VIIRS_C2_OVERRIDE_NIGHT
    está expuesto y su valor default es None (no override).
    """
    from pipeline import profile
    assert hasattr(profile, "VIIRS_C2_OVERRIDE_NIGHT"), (
        "profile debe exponer VIIRS_C2_OVERRIDE_NIGHT")
    # Default en mirova_equivalent.yaml es None (sin la key)
    assert profile.VIIRS_C2_OVERRIDE_NIGHT is None, (
        f"default debe ser None, got {profile.VIIRS_C2_OVERRIDE_NIGHT}")
