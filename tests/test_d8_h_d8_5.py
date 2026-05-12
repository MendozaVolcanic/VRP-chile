"""Tests S37 H_D8_5 — skeleton del fix D8 cluster selection.

Estos tests acompañan el PRIMER commit de implementación H_D8_5
(skeleton). Su propósito:

1. **Capturar el bug D8 actual** (test_clustering_picks_largest_not_closest):
   reproduce el escenario Puyehue lacolito donde clustering elige el cluster
   con mayor VRP en vez del cluster cercano-al-vent que MIROVA reporta. Este
   test PASA hoy (documenta el comportamiento actual). Cuando implementemos
   sum-reporting, será reemplazado por uno que verifica que el record
   reporta `Σ RP_pix` no `primary_cluster.vrp_mw`.

2. **Verificar contrato de los stubs** (test_eti_quadratic_stub_raises,
   test_second_pass_stub_raises): garantizan que mientras la implementación
   está pendiente, llamarlas dispara NotImplementedError con mensaje claro.

3. **Verificar perfil H_D8_5** (test_h_d8_5_profile_loads): el yaml es
   sintácticamente válido y declara los tres flags esperados.

Cuando implementemos ETI cuadrático + second-pass + sum reporting, este
archivo crece con tests funcionales reales (regresión cuadrática sobre
escena sintética, second-pass recaptura pixels marginales, sum de VRPs
sobre dos clusters da total no primario).

Ver `docs/superpowers/specs/2026-05-10-d8-cluster-selection.md`.
"""
from __future__ import annotations

import numpy as np
import pytest
import yaml
from pathlib import Path

from pipeline.clustering import cluster_hotspots
from pipeline.constants import C1 as PLANCK_C1, C2 as PLANCK_C2
from pipeline.detection_context import (
    compute_eti_scene_quadratic,
    compute_nti_and_nti_app,
    second_pass_adjacent,
)


def _planck(lam_um, T_k):
    """Helper Planck para tests sintéticos (misma fórmula que el código)."""
    return PLANCK_C1 / (lam_um ** 5 * (np.exp(PLANCK_C2 / (lam_um * T_k)) - 1.0))

REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. Reproducir bug D8 actual (TEST POSITIVO — debe pasar hoy)
# ---------------------------------------------------------------------------

def test_clustering_picks_largest_not_closest():
    """Reproduce el bug D8 en su forma estructural mínima.

    Escenario sintético inspirado en Puyehue 2026-05-09:
      - Cluster A: cráter principal, 5 pixels, VRP total alto (4.94 MW),
        distancia al vent ~0.5 km.
      - Cluster B: lacolito, 3 pixels, VRP total bajo (0.18 MW), distancia
        al vent ~7.7 km.

    MIROVA reporta el cluster B (lacolito) en la escena real. Nuestro
    clustering ordenado por `vrp_mw desc` elige A. Este test confirma
    ese comportamiento — NO es la fix, es la documentación del bug que
    H_D8_5 sum reporting va a corregir reportando `Σ RP_pix` sobre AMBOS
    clusters (5.12 MW) en lugar de elegir uno.
    """
    # Grid 20x20, vent en celda (10, 10) ≈ (-40.6, -72.1)
    H = W = 20
    lat = np.zeros((H, W))
    lon = np.zeros((H, W))
    for i in range(H):
        for j in range(W):
            lat[i, j] = -40.6 + (i - 10) * 0.01     # ~1.1 km/grado
            lon[i, j] = -72.1 + (j - 10) * 0.01
    vent_lat, vent_lon = -40.6, -72.1

    hot_mask = np.zeros((H, W), dtype=bool)
    vrp = np.zeros((H, W), dtype=float)

    # Cluster A: cráter — 5 pixels contiguos cerca del vent, VRPs altos
    crater_pixels = [(10, 10), (10, 11), (11, 10), (11, 11), (9, 10)]
    for (i, j) in crater_pixels:
        hot_mask[i, j] = True
        vrp[i, j] = 1.0  # total = 5 MW

    # Cluster B: lacolito — 3 pixels contiguos a ~7 km, VRPs bajos
    lacolito_pixels = [(3, 16), (3, 17), (4, 16)]
    for (i, j) in lacolito_pixels:
        hot_mask[i, j] = True
        vrp[i, j] = 0.06  # total = 0.18 MW

    clusters = cluster_hotspots(
        hot_mask, lat, lon, vent_lat, vent_lon,
        connectivity=8, vrp_per_pixel=vrp,
    )
    assert len(clusters) == 2, "expected 2 distinct clusters"
    primary = clusters[0]
    secondary = clusters[1]

    # BUG D8: el primary es el cluster con MÁS VRP, no el más cercano al vent
    assert primary["vrp_mw"] == pytest.approx(5.0, abs=0.01)
    assert primary["centroid_dist_km"] < 2.0   # cráter cerca del vent
    assert secondary["vrp_mw"] == pytest.approx(0.18, abs=0.01)
    assert secondary["centroid_dist_km"] > 5.0  # lacolito lejos

    # Lo que MIROVA reportaría con sum(RP_pix) — total scene
    sum_active = sum(c["vrp_mw"] for c in clusters)
    assert sum_active == pytest.approx(5.18, abs=0.01)


# ---------------------------------------------------------------------------
# 2. Contrato de los stubs H_D8_5
# ---------------------------------------------------------------------------

def test_eti_quadratic_recovers_coefficients_clean():
    """Sobre escena sintética sin outliers donde NTI = a·NTI²_app + b·NTI_app + c
    exactamente, ETI debe ser ~0 en todos los pixels (residual = ruido numérico).
    """
    rng = np.random.default_rng(42)
    H = W = 30
    # NTI_app distribuido en rango realista [-1, -0.6]
    nti_app = rng.uniform(-1.0, -0.6, size=(H, W))
    # Coeficientes "verdaderos" de la escena
    a_true, b_true, c_true = 0.2, 1.1, 0.3
    nti = a_true * nti_app**2 + b_true * nti_app + c_true
    mask = np.ones((H, W), dtype=bool)

    eti = compute_eti_scene_quadratic(nti, nti_app, mask)

    # Sin hot pixels: NTI matchea la regresión perfectamente → ETI ≈ 0
    assert np.all(np.isfinite(eti))
    assert np.max(np.abs(eti)) < 1e-9, f'ETI no es ~0: max={np.max(np.abs(eti))}'


def test_eti_quadratic_hot_pixels_stand_out():
    """Sobre escena sintética con background regresional + algunos pixels
    "hot" (NTI elevado vs el predicho), los hot pixels deben tener ETI
    significativamente mayor que los background.

    Replica el rol detector del paper: hot pixels desvían de la regresión
    cuadrática esperada y se identifican como anómalos.
    """
    rng = np.random.default_rng(7)
    H = W = 30
    nti_app = rng.uniform(-1.0, -0.6, size=(H, W))
    nti = 0.15 * nti_app**2 + 1.05 * nti_app + 0.25 + rng.normal(0, 0.002, size=(H, W))
    mask = np.ones((H, W), dtype=bool)

    # Inyectar 5 hot pixels con NTI elevado (~0.05 sobre el predicho)
    hot_coords = [(5, 5), (5, 6), (6, 5), (20, 20), (15, 25)]
    for (i, j) in hot_coords:
        nti[i, j] += 0.05

    eti = compute_eti_scene_quadratic(nti, nti_app, mask)

    # Background: ETI debe ser pequeño (residual de ruido + ajuste)
    bg_mask = np.ones((H, W), dtype=bool)
    for (i, j) in hot_coords:
        bg_mask[i, j] = False
    eti_bg = eti[bg_mask]
    eti_hot = np.array([eti[i, j] for (i, j) in hot_coords])

    bg_std = np.std(eti_bg)
    assert bg_std < 0.01, f'bg ETI std demasiado alto: {bg_std}'
    # Hot pixels deben sobresalir >5σ del background
    assert np.all(eti_hot > 5 * bg_std), (
        f'hot pixels no destacan: eti_hot={eti_hot}, 5*bg_std={5*bg_std}'
    )
    # Hot pixels deben tener ETI cercano a los 0.05 inyectados (iterative
    # re-fit los excluye del ajuste, así que el background se recupera limpio)
    assert np.all(eti_hot > 0.03)
    assert np.all(eti_hot < 0.07)


def test_eti_quadratic_iterative_refit_excludes_outliers():
    """Con iterative_refit=True vs False, el resultado para hot pixels debe
    diferir: sin refit, los hot pixels contaminan el ajuste; con refit, son
    excluidos y los coeficientes recuperados están más cerca de la verdad.
    """
    rng = np.random.default_rng(11)
    H = W = 40
    nti_app = rng.uniform(-1.0, -0.5, size=(H, W))
    a_true, b_true, c_true = 0.1, 1.0, 0.2
    nti = a_true * nti_app**2 + b_true * nti_app + c_true
    mask = np.ones((H, W), dtype=bool)

    # Contaminar 8% con hot pixels (offset grande)
    n_hot = int(0.08 * H * W)
    flat_idx = rng.choice(H * W, size=n_hot, replace=False)
    for idx in flat_idx:
        i, j = idx // W, idx % W
        nti[i, j] += 0.1

    eti_refit = compute_eti_scene_quadratic(nti, nti_app, mask, iterative_refit=True)
    eti_no_refit = compute_eti_scene_quadratic(nti, nti_app, mask, iterative_refit=False)

    bg_mask = np.ones((H, W), dtype=bool)
    for idx in flat_idx:
        i, j = idx // W, idx % W
        bg_mask[i, j] = False

    # Con refit, el background ETI debe estar más cerca de 0 que sin refit
    bg_abs_refit = np.mean(np.abs(eti_refit[bg_mask]))
    bg_abs_no_refit = np.mean(np.abs(eti_no_refit[bg_mask]))
    assert bg_abs_refit < bg_abs_no_refit, (
        f'iterative refit no mejoró: con={bg_abs_refit}, sin={bg_abs_no_refit}'
    )


def test_eti_quadratic_too_few_pixels_returns_nan():
    """Cuando hay <min_pixels válidos en la escena, el fit es inseguro y
    debe devolver array de NaN (no inventar coeficientes con datos
    insuficientes).
    """
    nti = np.full((5, 5), -0.8)
    nti_app = np.full((5, 5), -0.7)
    mask = np.zeros((5, 5), dtype=bool)
    mask[0, 0] = True  # 1 solo pixel válido
    eti = compute_eti_scene_quadratic(nti, nti_app, mask, min_pixels=10)
    assert np.all(np.isnan(eti))


def test_eti_quadratic_respects_mask():
    """Pixels donde mask_valid=False deben quedar como NaN, aunque el fit
    se haya hecho sobre los válidos.
    """
    rng = np.random.default_rng(3)
    H = W = 25
    nti_app = rng.uniform(-1.0, -0.6, size=(H, W))
    nti = 0.1 * nti_app**2 + 1.0 * nti_app + 0.2
    mask = np.ones((H, W), dtype=bool)
    mask[0, :] = False  # primera fila enmascarada (e.g. edge)
    mask[-1, :] = False

    eti = compute_eti_scene_quadratic(nti, nti_app, mask)

    assert np.all(np.isnan(eti[0, :]))
    assert np.all(np.isnan(eti[-1, :]))
    assert np.all(np.isfinite(eti[1:-1, :]))


def test_second_pass_recovers_adjacent_marginal_pixels():
    """Replica el efecto descrito por Coppola 2016a líneas 347-356.

    Escena: 3 pixels core muy hot + 2 pixels marginales ligeramente hot
    adyacentes al core. Los marginales NO se detectan en single-pass
    porque sus vecinos incluyen el core, que infla la mean local y baja
    su dNTI. Tras excluir el core del cómputo de mean (second-pass), los
    marginales destacan contra el verdadero bg uniforme y son
    recapturados.
    """
    H = W = 10
    nti = np.full((H, W), -0.9, dtype=np.float64)
    eti = np.full((H, W), 0.0, dtype=np.float64)

    # 3 pixels core muy hot (primer pass los detectó)
    core = [(5, 5), (5, 6), (6, 5)]
    for (i, j) in core:
        nti[i, j] = -0.50
        eti[i, j] = 0.060

    # 2 pixels marginales adyacentes al core, ligeramente hot
    marginal = [(5, 4), (6, 6)]
    for (i, j) in marginal:
        nti[i, j] = -0.85   # 0.05 sobre el bg
        eti[i, j] = 0.005   # 0.005 sobre el bg

    active_mask = np.zeros((H, W), dtype=bool)
    for (i, j) in core:
        active_mask[i, j] = True

    new_active = second_pass_adjacent(
        nti, eti, active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5.0, c2_deti=5.0,
    )

    # Core preservado
    for (i, j) in core:
        assert new_active[i, j], f'core pixel ({i},{j}) perdido'
    # Marginales recapturados (eran invisibles con vecinos contaminados)
    for (i, j) in marginal:
        assert new_active[i, j], f'marginal ({i},{j}) no recapturado'
    # Bg lejano no marcado
    assert not new_active[0, 0]
    assert not new_active[9, 9]


def test_second_pass_isolated_active_unchanged():
    """Si los pixels active están aislados y los vecinos son uniformes,
    no hay marginales que recapturar — el mask se devuelve igual.
    """
    H = W = 12
    nti = np.full((H, W), -0.9, dtype=np.float64)
    eti = np.full((H, W), 0.0, dtype=np.float64)
    # Un solo pixel active rodeado por bg uniforme
    nti[6, 6] = -0.4
    eti[6, 6] = 0.08
    active_mask = np.zeros((H, W), dtype=bool)
    active_mask[6, 6] = True

    new_active = second_pass_adjacent(
        nti, eti, active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5.0, c2_deti=5.0,
    )

    # active pixel preservado
    assert new_active[6, 6]
    # Ningún otro pixel agregado (vecinos uniformes, dNTI/dETI ≈ 0)
    assert int(np.count_nonzero(new_active)) == 1


def test_second_pass_dual_roi_applies_distinct_thresholds():
    """Con dual-ROI (is_summit + thresholds scene), pixels marginales en
    summit pasan thresholds permisivos; mismos pixels en scene son
    cortados por umbral más estricto. Replica Coppola 2016a Tabla 1
    (5σ summit / 10σ scene).
    """
    H = W = 15
    nti = np.full((H, W), -0.9, dtype=np.float64)
    eti = np.full((H, W), 0.0, dtype=np.float64)
    # ROI summit (mitad izquierda) y scene (mitad derecha)
    is_summit = np.zeros((H, W), dtype=bool)
    is_summit[:, :7] = True

    # Cluster en summit (cols 4-5)
    nti[7, 4] = -0.50; eti[7, 4] = 0.06
    nti[7, 5] = -0.50; eti[7, 5] = 0.06
    # Marginal summit (col 3) — debe pasar con c1=0.003
    nti[7, 3] = -0.85; eti[7, 3] = 0.005

    # Cluster en scene (cols 11-12)
    nti[7, 11] = -0.50; eti[7, 11] = 0.06
    nti[7, 12] = -0.50; eti[7, 12] = 0.06
    # Marginal scene (col 10) con MISMO exceso — debe ser cortado por c1=0.10
    nti[7, 10] = -0.85; eti[7, 10] = 0.005

    active_mask = np.zeros((H, W), dtype=bool)
    active_mask[7, 4] = active_mask[7, 5] = True
    active_mask[7, 11] = active_mask[7, 12] = True

    new_active = second_pass_adjacent(
        nti, eti, active_mask,
        c1_dnti=0.003, c1_deti=0.003,    # summit permisivo
        c2_dnti=5.0, c2_deti=5.0,
        is_summit=is_summit,
        c1_dnti_scene=0.10, c1_deti_scene=0.10,  # scene MUY estricto
        c2_dnti_scene=10.0, c2_deti_scene=10.0,
    )

    # Marginal en summit recapturado
    assert new_active[7, 3], 'marginal summit no recapturado'
    # Marginal en scene cortado por threshold estricto
    assert not new_active[7, 10], 'marginal scene escapó al threshold'


def test_second_pass_too_few_bg_returns_unchanged():
    """Si tras excluir active pixels quedan <min_bg_pixels válidos, μ/σ
    no son confiables → devolver active_mask original.
    """
    H = W = 5
    nti = np.full((H, W), -0.9, dtype=np.float64)
    eti = np.full((H, W), 0.0, dtype=np.float64)
    # Casi todos active — solo queda 1 bg
    active_mask = np.ones((H, W), dtype=bool)
    active_mask[0, 0] = False

    new_active = second_pass_adjacent(
        nti, eti, active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5.0, c2_deti=5.0,
        min_bg_pixels=10,
    )

    # Sin bg suficiente, retorna el active_mask sin cambios
    np.testing.assert_array_equal(new_active, active_mask)


# ---------------------------------------------------------------------------
# 3. Profile H_D8_5 parsea y declara los flags esperados
# ---------------------------------------------------------------------------

def test_h_d8_5_profile_loads():
    """El perfil `_h_d8_5_full.yaml` parsea y declara los tres flags
    H_D8_5 en ON, sin tocar el resto de la config mirova_equivalent.
    """
    path = REPO / 'pipeline' / 'profiles' / '_h_d8_5_full.yaml'
    assert path.exists(), f'{path} missing'
    with open(path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    assert cfg['profile'] == '_h_d8_5_full'
    paths = cfg['paths']
    # Tres flags H_D8_5 ON
    assert paths['enable_eti_quadratic_scene'] is True
    assert paths['enable_second_pass_adjacent'] is True
    assert paths['enable_sum_vrp_reporting'] is True
    # Compatibilidad: H8 OFF (sum reporting es el fix estructural)
    assert paths.get('enable_pixel_level_distance_filter', False) is False
    # Aislamiento operacional
    assert cfg['output']['data_subdir'] == '_h_d8_5_full'
    # Hereda thresholds Coppola 2016a Tabla 1 (5σ summit / 10σ scene)
    assert cfg['thresholds']['n_sigma_mir_summit'] == 5.0
    assert cfg['thresholds']['n_sigma_mir_scene'] == 10.0


# ---------------------------------------------------------------------------
# 4. Marcador: tests funcionales pendientes (xfail hasta implementación)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# NTI / NTI_app helper (commit 4a)
# ---------------------------------------------------------------------------

def test_nti_app_equals_nti_for_homogeneous_pixel():
    """Para un pixel realmente homogéneo (temperatura uniforme), por
    construcción rad_mir = Planck(λ_MIR, BT_TIR) y por tanto NTI ≈ NTI_app.
    """
    # Pixel a 280 K (típica escena nocturna sin actividad)
    bt_tir = np.full((5, 5), 280.0)
    # rad_mir consistente con temp 280 K en λ_MIR=3.959 μm (MODIS B22)
    lam_mir = 3.959
    lam_tir = 11.0
    rad_mir = _planck(lam_mir, 280.0) * np.ones((5, 5))

    nti, nti_app = compute_nti_and_nti_app(rad_mir, bt_tir, lam_mir, lam_tir)

    np.testing.assert_allclose(nti, nti_app, rtol=1e-12)


def test_nti_greater_than_nti_app_for_hot_subpixel():
    """Para un pixel con fracción hot (parte del pixel a alta temperatura),
    rad_mir excede el rad esperado para temp uniforme → NTI > NTI_app.

    Físicamente: MIR (3.7-4 μm) es mucho más sensible al componente hot que
    TIR (11 μm) porque Planck crece más rápido a alta T en λ corta. Un
    sub-pixel hotspot levanta mucho la radiance MIR pero apenas la TIR.
    """
    bt_tir = np.full((3, 3), 270.0)
    lam_mir, lam_tir = 3.959, 11.0
    # Pixel "cold" + 5% de pixel hot a 600 K (lava)
    f_hot = 0.05
    rad_mir_homog = _planck(lam_mir, 270.0)
    rad_mir_hot = _planck(lam_mir, 600.0)
    rad_mir_mixed = (1 - f_hot) * rad_mir_homog + f_hot * rad_mir_hot
    rad_mir = np.full((3, 3), rad_mir_mixed)

    nti, nti_app = compute_nti_and_nti_app(rad_mir, bt_tir, lam_mir, lam_tir)

    # NTI debe estar significativamente arriba de NTI_app
    diff = nti - nti_app
    assert np.all(diff > 0.01), f'NTI no destacó de NTI_app: diff={diff}'


def test_nti_nan_propagates():
    """Donde input tiene NaN, output debe ser NaN."""
    rad_mir = np.array([[0.5, np.nan], [0.5, 0.5]])
    bt_tir = np.array([[270.0, 270.0], [np.nan, 270.0]])
    nti, nti_app = compute_nti_and_nti_app(rad_mir, bt_tir, 3.959, 11.0)
    assert np.isnan(nti[0, 1])  # rad_mir NaN
    assert np.isnan(nti[1, 0])  # bt_tir NaN
    assert np.isfinite(nti[0, 0])
    assert np.isfinite(nti[1, 1])


def test_nti_typical_volcanic_range():
    """Sanity: para BT_TIR en rango realista (260-280 K) y rad_mir
    igualmente realista, NTI sale en rango [-1, 0] (paper noche típica -0.8).
    """
    rng = np.random.default_rng(0)
    bt_tir = rng.uniform(260, 280, size=(20, 20))
    lam_mir, lam_tir = 3.959, 11.0
    # rad_mir consistente: pixels homogéneos a una temp ligeramente menor
    # (~5K menos, simula MIR de noche típica)
    rad_mir = _planck(lam_mir, bt_tir - 5.0)
    nti, nti_app = compute_nti_and_nti_app(rad_mir, bt_tir, lam_mir, lam_tir)
    assert np.all(nti >= -1.0)
    assert np.all(nti <= 0.0)
    assert np.all(nti_app >= -1.0)
    assert np.all(nti_app <= 0.0)


def test_sum_vrp_reporting_persists_fields(tmp_path, monkeypatch):
    """Con ENABLE_SUM_VRP_REPORTING=True (toggle vía VRP_PROFILE=_h_d8_5_full),
    store.append_record persiste vrp_mw_sum_active y hotspot_dist_km_furthest
    sobre TODOS los anomaly_pixels reportados.

    Test usa monkeypatch para forzar el flag sin requerir env var,
    asegurando que el comportamiento opt-in funciona independiente del
    entorno de tests.
    """
    import pipeline.store as store
    import importlib
    monkeypatch.setattr(store, 'ENABLE_SUM_VRP_REPORTING', True)
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    record = {
        'datetime_utc': '2026-05-12 03:30',
        'sensor': 'MODIS_TERRA',
        'vrp_mw': 5.18,           # sum total esperada
        'hotspot_lat': -40.6,
        'hotspot_lon': -72.1,
        'hotspot_dist_km': 0.5,    # primary cluster (cráter cercano)
        'anomaly_pixels': [
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
            # Cluster lacolito lejano (que MIROVA reportaría):
            {'lat': -40.5, 'lon': -72.0, 'dist_km': 7.7, 'vrp_mw': 0.06},
            {'lat': -40.5, 'lon': -72.0, 'dist_km': 7.7, 'vrp_mw': 0.06},
            {'lat': -40.5, 'lon': -72.0, 'dist_km': 7.7, 'vrp_mw': 0.06},
        ],
        'product_version': 'standard',
    }
    # No coords de volcán → safety net no aplica
    store.append_record('TestVolcano', record)

    # Releer
    records = store.get_records('TestVolcano')
    assert len(records) == 1
    r = records[0]
    # Sum MIROVA-style: 5×1.0 + 3×0.06 = 5.18
    assert r['vrp_mw_sum_active'] == pytest.approx(5.18, abs=0.001)
    # Furthest active pixel: lacolito @ 7.7 km
    assert r['hotspot_dist_km_furthest'] == pytest.approx(7.7, abs=0.001)
    # primary_cluster style fields siguen intactos (no se sobreescriben)
    assert r['hotspot_dist_km'] == pytest.approx(0.5, abs=0.001)


def test_sum_vrp_reporting_off_does_not_add_fields(tmp_path, monkeypatch):
    """Con ENABLE_SUM_VRP_REPORTING=False (default operacional), los
    campos vrp_mw_sum_active / hotspot_dist_km_furthest NO deben aparecer
    en el record persistido. Garantiza backward-compat del schema.
    """
    import pipeline.store as store
    monkeypatch.setattr(store, 'ENABLE_SUM_VRP_REPORTING', False)
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    record = {
        'datetime_utc': '2026-05-12 03:30',
        'sensor': 'MODIS_TERRA',
        'vrp_mw': 1.0,
        'hotspot_dist_km': 0.5,
        'anomaly_pixels': [
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 1.0},
        ],
        'product_version': 'standard',
    }
    store.append_record('TestVolcanoOff', record)
    r = store.get_records('TestVolcanoOff')[0]
    assert 'vrp_mw_sum_active' not in r
    assert 'hotspot_dist_km_furthest' not in r


def test_sum_vrp_reporting_zero_when_floor_zeros_out(tmp_path, monkeypatch):
    """Si el sensor floor llevó vrp_mw a 0 (señal sub-piso), reportar
    vrp_mw_sum_active=0 (no inventar suma de pixels descartados por floor).
    """
    import pipeline.store as store
    monkeypatch.setattr(store, 'ENABLE_SUM_VRP_REPORTING', True)
    monkeypatch.setattr(store, 'DATA_DIR', tmp_path)

    record = {
        'datetime_utc': '2026-05-12 03:30',
        'sensor': 'VIIRS_SNPP',  # piso 0.02 MW
        'vrp_mw': 0.015,         # bajo piso → será zero-out
        'vrp_mir_mw': 0.015,
        'hotspot_dist_km': 0.5,
        'anomaly_pixels': [
            {'lat': -40.6, 'lon': -72.1, 'dist_km': 0.5, 'vrp_mw': 0.015},
        ],
        'product_version': 'standard',
    }
    store.append_record('TestVolcanoFloor', record)
    r = store.get_records('TestVolcanoFloor')[0]
    assert r['vrp_mw'] == 0.0  # zero-out floor aplicó
    assert r['vrp_mw_sum_active'] == 0.0
    assert r['hotspot_dist_km_furthest'] is None
