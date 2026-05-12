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

def test_eti_quadratic_stub_raises():
    """compute_eti_scene_quadratic está stubbed — debe disparar
    NotImplementedError con mensaje que apunte al design doc y al paper.
    """
    nti = np.zeros((10, 10))
    nti_app = np.zeros((10, 10))
    mask = np.ones((10, 10), dtype=bool)
    with pytest.raises(NotImplementedError) as exc:
        compute_eti_scene_quadratic(nti, nti_app, mask)
    msg = str(exc.value).lower()
    assert "h_d8_5" in msg
    assert "sp426.5" in msg or "documentacion" in msg


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

@pytest.mark.xfail(reason='H_D8_5 implementación pendiente — primer commit S37 solo skeleton',
                   strict=True)
def test_eti_quadratic_recovers_synthetic_background():
    """Cuando se implemente compute_eti_scene_quadratic, este test verificará
    que sobre escena sintética con (a, b, c) conocidos + ruido, la función
    recupere coeficientes dentro de tolerancia. Stub hoy → xfail strict.
    """
    raise NotImplementedError('pending H_D8_5 implementation')


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
