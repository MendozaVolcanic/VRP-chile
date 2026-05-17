"""Tests TDD para local kernel 3x3 background variant (S57).

Implementa Coppola 2024 chapter L1129 literal: "T_bk is retrieved from the
pixels adjacent to the hot one" — kernel local NxN excluyendo el centro
(y otros pixels hot), NO ring 5-25km.

Hipótesis S56 (refrendada por Coppola 2024): median(ring 5-25km) sobre-estima
T_bk en lava lake Villarrica (0/5 ratios aceptables), p01(ring) recupera 4/5,
y kernel local 3x3 sobre vecinos adyacentes debería matchear MIROVA-OSF.

Mantiene Iron Law TDD: estos tests fueron escritos ANTES de implementar
compute_local_background. RED esperado en primer run.
"""
from __future__ import annotations

import math

import numpy as np
import pytest


# Import bajo prueba — fallará en RED (función no existe todavía)
from pipeline.vrp_regimes import compute_local_background, compute_vrp_lava_lake_eq16


# -----------------------------------------------------------------------------
# Tests unitarios compute_local_background — kernel adjacency
# -----------------------------------------------------------------------------

def test_simple_5x5_grid_single_hot_center_returns_mean_of_8_neighbors():
    """Caso canónico: grid 5x5 uniforme bg=275K con 1 hot central (310K).

    Kernel 3x3 excluyendo centro debe retornar media de los 8 vecinos
    adyacentes, todos a 275K → t_bk = 275.0 K exacto.
    """
    bt_grid = np.full((5, 5), 275.0)
    bt_grid[2, 2] = 310.0  # hot central

    t_bks = compute_local_background(
        bt_grid, hot_rows=[2], hot_cols=[2], kernel_size=3
    )

    assert len(t_bks) == 1
    assert math.isclose(t_bks[0], 275.0, abs_tol=1e-9), (
        f"Expected 275.0, got {t_bks[0]}"
    )


def test_hot_pixel_at_corner_averages_only_available_neighbors():
    """Hot pixel en esquina (0,0) solo tiene 3 vecinos disponibles.

    Kernel 3x3 sobre (0,0) → cubre rows 0..1, cols 0..1, excluye centro =
    3 vecinos: (0,1), (1,0), (1,1). Si bg uniforme 270 → t_bk=270.
    """
    bt_grid = np.full((4, 4), 270.0)
    bt_grid[0, 0] = 305.0  # hot en esquina superior-izquierda

    t_bks = compute_local_background(
        bt_grid, hot_rows=[0], hot_cols=[0], kernel_size=3
    )

    assert len(t_bks) == 1
    assert math.isclose(t_bks[0], 270.0, abs_tol=1e-9)


def test_hot_pixel_with_some_nan_neighbors_ignores_nans():
    """Vecinos con NaN deben ignorarse en el promedio.

    Grid 3x3, hot central, 4 vecinos NaN, 4 vecinos a 280K → t_bk=280.
    """
    bt_grid = np.array([
        [280.0, np.nan, 280.0],
        [np.nan, 320.0, np.nan],
        [280.0, np.nan, 280.0],
    ])

    t_bks = compute_local_background(
        bt_grid, hot_rows=[1], hot_cols=[1], kernel_size=3
    )

    assert len(t_bks) == 1
    assert math.isclose(t_bks[0], 280.0, abs_tol=1e-9)


def test_hot_pixel_with_all_nan_neighbors_returns_nan():
    """Si TODOS los vecinos son NaN, t_bk = NaN (no se puede estimar bg local).

    Caller debe manejar este caso (fallback a ring p01 o reject record).
    """
    bt_grid = np.full((3, 3), np.nan)
    bt_grid[1, 1] = 320.0  # solo hot, nada de vecinos válidos

    t_bks = compute_local_background(
        bt_grid, hot_rows=[1], hot_cols=[1], kernel_size=3
    )

    assert len(t_bks) == 1
    assert math.isnan(t_bks[0]), f"Expected NaN, got {t_bks[0]}"


def test_two_adjacent_hot_pixels_each_excludes_the_other_hot():
    """Dos hot pixels vecinos: cada uno debe excluir al otro al estimar t_bk.

    Grid 5x5 bg=270, hot en (2,2)=315 y (2,3)=320. Para (2,2):
    vecinos kernel 3x3 son rows 1..3, cols 1..3, excluyendo (2,2) hot Y
    excluyendo (2,3) que también es hot → 7 vecinos a 270 → t_bk=270.
    """
    bt_grid = np.full((5, 5), 270.0)
    bt_grid[2, 2] = 315.0
    bt_grid[2, 3] = 320.0

    t_bks = compute_local_background(
        bt_grid, hot_rows=[2, 2], hot_cols=[2, 3], kernel_size=3
    )

    assert len(t_bks) == 2
    assert math.isclose(t_bks[0], 270.0, abs_tol=1e-9), (
        f"Hot 1 t_bk wrong: {t_bks[0]}"
    )
    assert math.isclose(t_bks[1], 270.0, abs_tol=1e-9), (
        f"Hot 2 t_bk wrong: {t_bks[1]}"
    )


def test_kernel_size_5_uses_5x5_neighborhood_excluding_center():
    """kernel_size=5 → vecindario 5x5 centrado, excluye centro.

    Grid 7x7 uniforme 273, hot central (3,3)=310 → kernel 5x5 = 24 vecinos
    todos a 273 → t_bk=273.
    """
    bt_grid = np.full((7, 7), 273.0)
    bt_grid[3, 3] = 310.0

    t_bks = compute_local_background(
        bt_grid, hot_rows=[3], hot_cols=[3], kernel_size=5
    )

    assert len(t_bks) == 1
    assert math.isclose(t_bks[0], 273.0, abs_tol=1e-9)


# -----------------------------------------------------------------------------
# Tests integración local kernel → Eq.16 lava lake (anchors Villarrica MIROVA)
# -----------------------------------------------------------------------------

def test_villarrica_2026_02_26_local_bg_275_yields_vrp_about_0_12_mw():
    """Anchor MIROVA-OSF Villarrica 2026-02-26: VRP ~0.12 MW.

    Setup: hot pixel BT=282K rodeado de 8 vecinos a 275K (cráter sub-pixel
    con lava lake, background invernal). Local kernel da t_bk=275, alimenta
    Eq.16 con T_e=1000K default → VRP ~0.12 MW (calibrado vs MIROVA OSF).

    Punto clave S56: ring 5-25km da median ~280K (lago Villarrica cercano
    + nieve parcial) → VRP sobre-estimado o 0. Local 3x3 al cráter ve solo
    nieve invernal a 275K → recupera magnitud MIROVA.
    """
    bt_grid = np.full((5, 5), 275.0)
    bt_grid[2, 2] = 282.0  # cráter hot

    t_bks = compute_local_background(
        bt_grid, hot_rows=[2], hot_cols=[2], kernel_size=3
    )
    t_bk = t_bks[0]

    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=282.0,
        bt_bg_k=t_bk,
        t_bk_k=t_bk,
        t_e_k=1000.0,
        epsilon=0.95,
        a_pix_m2=140625.0,
        lambda_mir_um=3.74,
    )

    # Esperado ~0.12 MW (tolerancia ±20% para captura calibración MIROVA)
    assert 0.10 <= result["vrp_mw"] <= 0.15, (
        f"Villarrica 2026-02-26: VRP={result['vrp_mw']:.4f} MW fuera de "
        f"banda MIROVA-OSF 0.10-0.15"
    )


def test_villarrica_2026_04_09_local_bg_275_yields_vrp_about_0_11_mw():
    """Anchor MIROVA-OSF Villarrica 2026-04-09: VRP ~0.11 MW.

    Setup similar al test anterior pero bt_hot ligeramente menor (281.5K)
    consistente con MIROVA-OSF 0.11 MW.
    """
    bt_grid = np.full((5, 5), 275.0)
    bt_grid[2, 2] = 281.5

    t_bks = compute_local_background(
        bt_grid, hot_rows=[2], hot_cols=[2], kernel_size=3
    )
    t_bk = t_bks[0]

    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=281.5,
        bt_bg_k=t_bk,
        t_bk_k=t_bk,
        t_e_k=1000.0,
        epsilon=0.95,
        a_pix_m2=140625.0,
        lambda_mir_um=3.74,
    )

    assert 0.08 <= result["vrp_mw"] <= 0.14, (
        f"Villarrica 2026-04-09: VRP={result['vrp_mw']:.4f} MW fuera de "
        f"banda MIROVA-OSF 0.08-0.14"
    )
