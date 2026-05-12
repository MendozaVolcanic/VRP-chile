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
from pipeline.detection_context import (
    compute_eti_scene_quadratic,
    second_pass_adjacent,
)

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


def test_second_pass_stub_raises():
    """second_pass_adjacent stubbed — NotImplementedError con referencia
    a líneas exactas del paper.
    """
    dnti = np.zeros((10, 10))
    deti = np.zeros((10, 10))
    active = np.zeros((10, 10), dtype=bool)
    is_summit = np.zeros((10, 10), dtype=bool)
    with pytest.raises(NotImplementedError) as exc:
        second_pass_adjacent(
            dnti, deti, active,
            c1_dnti=0.003, c1_deti=0.003,
            c2_dnti=5.0, c2_deti=5.0,
            is_summit=is_summit,
        )
    msg = str(exc.value).lower()
    assert "h_d8_5" in msg
    assert "347" in msg  # paper line range citado


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

@pytest.mark.xfail(reason='H_D8_5 second-pass implementación pendiente',
                   strict=True)
def test_second_pass_recovers_adjacent_pixels():
    """Cuando se implemente second_pass_adjacent, verificará que sobre cluster
    sintético con pixels marginales escondidos por contaminación del primer
    pass, el segundo pass los recapture.
    """
    raise NotImplementedError('pending H_D8_5 implementation')


@pytest.mark.xfail(reason='sum_vrp_reporting implementación pendiente — toca store.py',
                   strict=True)
def test_sum_vrp_reporting_replaces_primary_cluster():
    """Cuando enable_sum_vrp_reporting=true, el record persistido debe
    contener `vrp_mw_sum_active` = sum sobre TODOS los active pixels, y
    `hotspot_dist_km_furthest` = max distancia entre active pixels.
    """
    raise NotImplementedError('pending H_D8_5 implementation')
