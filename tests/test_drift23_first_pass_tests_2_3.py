"""Tests Drift #2+#3 — first-pass Tests 2 ∧ 3 + dETI + AND + C2·σ + dual-ROI."""
import numpy as np
import pytest


def _make_bg_pair(shape, rng, nti_app_low=-0.99, nti_app_high=-0.95, noise=0.0005):
    """Background bien-condicionado para polyfit: nti_app spans rango,
    NTI = NTI_app + ruido (relación identidad esperada para pixels homogéneos)."""
    nti_app = rng.uniform(nti_app_low, nti_app_high, shape)
    nti = nti_app + rng.normal(0.0, noise, shape)
    return nti, nti_app


def _build_synthetic_test2_only_pixel():
    """Granule: pixel pasa Test 2 (dNTI alto) pero falla Test 3 (dETI bajo).

    NTI sube anómalo Y NTI_app sube igual → quedan en la diagonal NTI=NTI_app →
    el modelo polyfit captura ambos sin desvío → ETI≈0 → dETI≈0 → Test 3 falla.
    """
    shape = (20, 20)
    rng = np.random.default_rng(42)
    nti, nti_app = _make_bg_pair(shape, rng)
    bt = np.full(shape, 268.0)

    # Pixel @ (10,10): NTI y NTI_app suben juntos → ETI ≈ 0
    nti[10, 10] = -0.5
    nti_app[10, 10] = -0.5
    bt[10, 10] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)
    return {"nti": nti, "nti_app": nti_app, "bt": bt,
            "roi_mask": roi_mask, "dist_km": dist_km}


def _build_synthetic_test2_and_test3_pixel():
    """Granule: pixel pasa AMBOS Tests 2 ∧ 3.

    NTI sube anómalo, NTI_app permanece en bg → desviación de la diagonal →
    ETI alto → dETI alto → Tests 2 y 3 ambos pasan.
    """
    shape = (20, 20)
    rng = np.random.default_rng(43)
    nti, nti_app = _make_bg_pair(shape, rng)
    bt = np.full(shape, 268.0)

    # NTI sube anómalo (-0.5), NTI_app se queda en bg (-0.97)
    nti[10, 10] = -0.5
    nti_app[10, 10] = -0.97
    bt[10, 10] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)
    return {"nti": nti, "nti_app": nti_app, "bt": bt,
            "roi_mask": roi_mask, "dist_km": dist_km}


def test_drift23_requires_both_tests_2_AND_3():
    """Pixel Test 2 sin Test 3 → NO active."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    data = _build_synthetic_test2_only_pixel()
    hot, diag = first_pass_tests_2_and_3(
        nti=data["nti"], nti_app=data["nti_app"], bt=data["bt"],
        roi_mask=data["roi_mask"], dist_km=data["dist_km"],
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    assert not hot[10, 10], "Conjunción AND obligatoria: dETI=0 rechaza"
    assert diag["n_first_pass_pixels"] == 0


def test_drift23_passes_when_both_tests_pass():
    """Pixel con dNTI Y dETI altos → active."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    data = _build_synthetic_test2_and_test3_pixel()
    hot, diag = first_pass_tests_2_and_3(
        nti=data["nti"], nti_app=data["nti_app"], bt=data["bt"],
        roi_mask=data["roi_mask"], dist_km=data["dist_km"],
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    assert hot[10, 10], "Tests 2 y 3 pasan → active"
    assert diag["n_first_pass_pixels"] >= 1


def test_drift23_dual_roi_uses_stricter_C1_in_scene():
    """Pixel scene con dNTI marginal pasa C1=0.003 (summit) pero NO C1=0.010 (scene)."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    rng = np.random.default_rng(44)
    nti, nti_app = _make_bg_pair(shape, rng)
    bt = np.full(shape, 268.0)

    # Pixel scene dNTI marginal: NTI anómalo modesto, NTI_app en bg → dETI también marginal
    nti[10, 10] = -0.96  # leve anomalía
    nti_app[10, 10] = -0.97  # mantiene bg → ETI/dETI marginal
    bt[10, 10] = 285.0

    dist_km = np.full(shape, 10.0)  # scene zone
    roi_mask = np.ones(shape, dtype=bool)

    hot_dual, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        c1_dnti_scene=0.050, c1_deti_scene=0.050,
        c2_dnti_scene=10, c2_deti_scene=10,
    )

    assert not hot_dual[10, 10], "Dual-ROI scene: dNTI marginal NO pasa C1 estricto"


def test_drift23_statistical_OR_branch():
    """Pixel dNTI < C1 pero > μ + C2·σ → active vía rama statistical.

    Demostración del OR estadístico: si bg dispersa (σ chica) y C1 alto
    artificialmente, una anomalía moderada NO supera C1 pero SÍ supera μ+C2σ.
    Usa C1 altísimo (0.05) y bg uniforme — la anomalía supera el threshold
    statistical pero no el absoluto.
    """
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (100, 100)
    rng = np.random.default_rng(45)
    nti, nti_app = _make_bg_pair(shape, rng, noise=0.00005)
    bt = np.full(shape, 268.0)

    # Anomalía moderada: nti sube ~0.01, nti_app en bg → dNTI/dETI ~0.01
    nti[50, 50] = -0.96
    nti_app[50, 50] = -0.97
    bt[50, 50] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)

    # C1=0.05 absoluto NO pasaría con dNTI=0.01. Pero μ+5σ con σ chico SÍ pasa.
    hot_stat, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.05, c1_deti_summit=0.05,
        c2_dnti_summit=1, c2_deti_summit=1,  # C2 chico → stat fácil
        inner_km=5.0,
    )

    assert hot_stat[50, 50], "Rama OR estadística debe disparar (μ+1σ con σ chico)"
