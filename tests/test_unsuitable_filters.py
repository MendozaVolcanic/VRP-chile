"""S72 F1.2 — Unsuitable-pixel filters (Coppola 2016a SP 426.5).

Tests sintéticos que cubren los 3 filtros del paper §267-273 + §298-300:

  - Edge pixels (1 píxel de margen) → unsuitable.
  - dNTI < -0.1                     → unsuitable.
  - dETI < -0.1                     → unsuitable.
  - Test 1 K1 active (NTI > -0.8)   → unsuitable (sólo si test1_mask se provee).

Defaults preservan backward-compat: callers que no propagen test1_mask
mantienen el comportamiento legacy (Test 1 no filtra el pool bg).
"""
import numpy as np
import pytest


def _make_bg_pair(shape, rng, noise=0.0005):
    """Background bien-condicionado para polyfit: NTI ≈ NTI_app."""
    nti_app = rng.uniform(-0.99, -0.95, shape)
    nti = nti_app + rng.normal(0.0, noise, shape)
    return nti, nti_app


# ---------------------------------------------------------------------------
# build_unsuitable_mask — helper directo (filtros aislados).
# ---------------------------------------------------------------------------


def test_unsuitable_edge_pixel_excluded():
    """Borde de matriz queda fuera del pool suitable aún con dNTI/dETI buenos."""
    from pipeline.detection_context import build_unsuitable_mask

    shape = (10, 10)
    roi = np.ones(shape, dtype=bool)
    dnti = np.zeros(shape)
    deti = np.zeros(shape)
    suitable = build_unsuitable_mask(roi, dnti, deti)

    # Esquina (0,0) edge → False
    assert not suitable[0, 0]
    assert not suitable[-1, -1]
    assert not suitable[0, 5]
    # Centro → True
    assert suitable[5, 5]


def test_unsuitable_dnti_negative_excluded():
    """Pixel interior con dNTI=-0.5 < -0.1 queda fuera del pool suitable."""
    from pipeline.detection_context import build_unsuitable_mask

    shape = (10, 10)
    roi = np.ones(shape, dtype=bool)
    dnti = np.zeros(shape)
    deti = np.zeros(shape)
    dnti[5, 5] = -0.5  # negative outlier, debería marcar unsuitable

    suitable = build_unsuitable_mask(roi, dnti, deti)
    assert not suitable[5, 5], "dNTI<-0.1 debe excluir del pool bg"
    # Vecino sin outlier → suitable
    assert suitable[5, 6]


def test_unsuitable_deti_negative_excluded():
    """Pixel interior con dETI=-0.3 < -0.1 queda fuera del pool suitable."""
    from pipeline.detection_context import build_unsuitable_mask

    shape = (10, 10)
    roi = np.ones(shape, dtype=bool)
    dnti = np.zeros(shape)
    deti = np.zeros(shape)
    deti[5, 5] = -0.3

    suitable = build_unsuitable_mask(roi, dnti, deti)
    assert not suitable[5, 5], "dETI<-0.1 debe excluir del pool bg"
    assert suitable[5, 6]


def test_unsuitable_test1_mask_excluded_when_passed():
    """Pixel con Test 1 K1 active queda fuera del pool si test1_mask se provee."""
    from pipeline.detection_context import build_unsuitable_mask

    shape = (10, 10)
    roi = np.ones(shape, dtype=bool)
    dnti = np.zeros(shape)
    deti = np.zeros(shape)
    test1 = np.zeros(shape, dtype=bool)
    test1[5, 5] = True  # pixel "active" Test 1 K1

    suitable_with = build_unsuitable_mask(roi, dnti, deti, test1_mask=test1)
    assert not suitable_with[5, 5], "Test 1 active debe filtrarse cuando se provee"

    # Backward compat: si test1_mask no se pasa, el pixel sigue suitable.
    suitable_without = build_unsuitable_mask(roi, dnti, deti)
    assert suitable_without[5, 5], "Sin test1_mask el pixel queda suitable (legacy)"


def test_unsuitable_pixel_passes_all_filters():
    """Pixel interior con dNTI/dETI moderados y no-Test1 entra al pool."""
    from pipeline.detection_context import build_unsuitable_mask

    shape = (10, 10)
    roi = np.ones(shape, dtype=bool)
    dnti = np.full(shape, 0.001)  # cerca de 0 — claramente > -0.1
    deti = np.full(shape, 0.001)
    test1 = np.zeros(shape, dtype=bool)

    suitable = build_unsuitable_mask(roi, dnti, deti, test1_mask=test1)
    assert suitable[5, 5]
    assert suitable[3, 7]


# ---------------------------------------------------------------------------
# first_pass_tests_2_and_3 — integración: el pool μ/σ cambia según filtros.
# ---------------------------------------------------------------------------


def test_first_pass_test1_mask_changes_bg_when_flag_on():
    """Pasar test1_mask cambia μ/σ vs no pasarlo (alineado con flag retire)."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    rng = np.random.default_rng(101)
    nti, nti_app = _make_bg_pair(shape, rng)
    # Inyectar un pixel "Test 1 K1 active" con NTI alto que ensucia μ/σ.
    nti[10, 10] = -0.5  # interior, alto → contamina dNTI pool si no se filtra
    bt = np.full(shape, 268.0)
    bt[10, 10] = 285.0
    roi = np.ones(shape, dtype=bool)
    dist = np.full(shape, 2.0)
    test1 = np.zeros(shape, dtype=bool)
    test1[10, 10] = True

    # Run 1: sin filtro Test 1 (legacy, test1_mask=None).
    _hot_legacy, diag_legacy = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        test1_mask=None,
    )

    # Run 2: con Test 1 filter activo.
    _hot_filt, diag_filt = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        test1_mask=test1,
    )

    # n_bg debe diferir: en el filtrado al menos el pixel Test 1 + edges
    # están fuera. Y σ_dnti del filtrado debe ser ≤ σ_dnti legacy (al sacar
    # el outlier alto la dispersión cae).
    assert diag_filt["n_bg_used"] < diag_legacy["n_bg_used"]
    assert diag_filt["sd_dnti"] <= diag_legacy["sd_dnti"] + 1e-12


def test_first_pass_backward_compat_default_test1_none():
    """Default test1_mask=None preserva comportamiento legacy (suite sin regresión)."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    rng = np.random.default_rng(102)
    nti, nti_app = _make_bg_pair(shape, rng)
    bt = np.full(shape, 268.0)
    roi = np.ones(shape, dtype=bool)
    dist = np.full(shape, 2.0)

    # Llamada sin test1_mask (default) — no debe fallar.
    hot, diag = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )
    # bg pool debe contener interiores (edges quedan fuera por F1.2.a).
    assert diag["n_bg_used"] > 0
    assert isinstance(hot, np.ndarray)


def test_first_pass_dnti_negative_outlier_filtered_from_bg():
    """Outlier dNTI = -0.5 NO entra al pool μ/σ (paper §267-273)."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    rng = np.random.default_rng(103)
    nti, nti_app = _make_bg_pair(shape, rng)
    # Forzar un pixel con dNTI muy negativo: nti << mean vecinos.
    # Estrategia: bajar nti[10,10] mucho — el mean 8-vecinos queda como bg
    # típico (-0.97), entonces dnti[10,10] = nti - mean ≈ -0.5 - (-0.97) = 0.47.
    # Eso no funciona — el pixel queda con dNTI POSITIVO alto. Lo que sí
    # produce dNTI negativo es bajar el pixel: nti[10,10] = -1.5 → dnti ≈ -0.53.
    nti[10, 10] = -1.5
    bt = np.full(shape, 268.0)
    roi = np.ones(shape, dtype=bool)
    dist = np.full(shape, 2.0)

    _hot, diag = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    # σ_dnti debe ser modesto — si el outlier -0.5 hubiera entrado al pool,
    # la σ explotaría a ~0.1. Con el filtro queda ~ruido bg (~0.0005).
    assert diag["sd_dnti"] < 0.05, (
        f"σ_dnti inflado: {diag['sd_dnti']:.4f} — el filtro dNTI<-0.1 "
        f"no excluyó al outlier"
    )


# ---------------------------------------------------------------------------
# S72 F2.3 — split flags: profiles aislados cargan los 2 flags independientes.
# ---------------------------------------------------------------------------


def _reload_profile(monkeypatch, profile_name):
    """Helper: re-importa pipeline.profile con VRP_PROFILE = profile_name."""
    import importlib
    import pipeline.profile as profile_mod
    monkeypatch.setenv("VRP_PROFILE", profile_name)
    importlib.reload(profile_mod)
    return profile_mod


def test_profile_unsuitable_only_loads_correct_flags(monkeypatch):
    """unsuitable_only_v1: §267-273 ON + K1 retire OFF."""
    profile = _reload_profile(monkeypatch, "mirova_equivalent_unsuitable_only_v1")
    assert profile.PROFILE_NAME == "mirova_equivalent_unsuitable_only_v1"
    assert profile.ENABLE_UNSUITABLE_FILTERS_267_273 is True, (
        "unsuitable_only debe activar §267-273 (edge + dNTI/dETI<-0.1)"
    )
    assert profile.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK is False, (
        "unsuitable_only debe DESACTIVAR K1 retire para aislar §267-273"
    )


def test_profile_test1_retire_only_loads_correct_flags(monkeypatch):
    """test1_retire_only_v1: §267-273 OFF + K1 retire ON."""
    profile = _reload_profile(monkeypatch, "mirova_equivalent_test1_retire_only_v1")
    assert profile.PROFILE_NAME == "mirova_equivalent_test1_retire_only_v1"
    assert profile.ENABLE_UNSUITABLE_FILTERS_267_273 is False, (
        "test1_retire_only debe DESACTIVAR §267-273 (floors=-inf)"
    )
    assert profile.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK is True, (
        "test1_retire_only debe activar K1 retire §298-300"
    )


def test_profile_default_unsuitable_filters_true_for_operational(monkeypatch):
    """Default ENABLE_UNSUITABLE_FILTERS_267_273=True preserva post-F1.2.a."""
    profile = _reload_profile(monkeypatch, "mirova_equivalent")
    # mirova_equivalent operacional no setea el flag explícito — usa default True
    # (preserva comportamiento post-F1.2.a: §267-273 floors -0.1 en first_pass).
    assert profile.ENABLE_UNSUITABLE_FILTERS_267_273 is True, (
        "mirova_equivalent operacional default debe ser True (backward compat)"
    )


def test_first_pass_floor_neg_inf_disables_filter():
    """unsuitable_dnti_floor=-inf efectivamente desactiva §267-273 en pool bg."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    rng = np.random.default_rng(204)
    nti, nti_app = _make_bg_pair(shape, rng)
    # Outlier dNTI muy negativo que ANTES era filtrado por floor -0.1.
    nti[10, 10] = -1.5
    bt = np.full(shape, 268.0)
    roi = np.ones(shape, dtype=bool)
    dist = np.full(shape, 2.0)

    # Run con floor -inf: outlier entra al pool → σ_dnti se infla.
    _hot, diag_off = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        unsuitable_dnti_floor=-np.inf,
        unsuitable_deti_floor=-np.inf,
    )
    # Run con floor -0.1 (default): outlier excluido → σ_dnti modesto.
    _hot, diag_on = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi, dist_km=dist,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        unsuitable_dnti_floor=-0.1,
        unsuitable_deti_floor=-0.1,
    )
    # Con floor desactivado, σ debe ser mayor (outlier contamina).
    assert diag_off["sd_dnti"] > diag_on["sd_dnti"], (
        f"floor -inf debería inflar σ vs floor -0.1: "
        f"off={diag_off['sd_dnti']:.4f} on={diag_on['sd_dnti']:.4f}"
    )
