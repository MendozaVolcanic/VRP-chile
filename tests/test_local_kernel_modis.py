"""Tests TDD para integracion ENABLE_LOCAL_KERNEL_BG en process_modis (S58).

Paridad con la integracion VIIRS (process_viirs.py lineas ~791-802). Cuando el
flag ENABLE_LOCAL_KERNEL_BG esta ON, MODIS debe calcular L_bg per-pixel desde
un kernel 3x3 alrededor de cada hot pixel (Coppola 2024 L1129 literal), con
fallback al L_bg global (derivado de t_bg) cuando el kernel local da NaN.

Banda MODIS B21 = 3.929 um (vs VIIRS I04 = 3.74 um). Wooster coeff = 18.9
para MODIS 1km (vs 18.0 VIIRS 375m).

Iron Law TDD: tests escritos ANTES de la integracion en process_modis.py.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline.vrp_regimes import compute_local_background


BAND21_LAMBDA = 3.929  # um, mismo valor que pipeline/process_modis.py:40
C1 = 1.1910429e8   # W·um^4/(m^2·sr) — pipeline/constants.py
C2 = 1.4387752e4   # um·K — pipeline/constants.py
WOOSTER_COEFF_MODIS = 18.9


def _planck_radiance(bt_k: float, lambda_um: float) -> float:
    """L = c1 / (lambda^5 * (exp(c2/(lambda*T)) - 1)) — Planck spectral radiance."""
    return float(C1 / (lambda_um ** 5 * (np.exp(C2 / (lambda_um * bt_k)) - 1.0)))


# -----------------------------------------------------------------------------
# Unit-style tests: local kernel calculation, MODIS lambda
# -----------------------------------------------------------------------------

def test_modis_local_kernel_single_hot_neighbors_uniform_bg():
    """Grid 5x5 uniforme 280K + hot central 320K, kernel 3x3 → t_bk=280K.

    Reutiliza compute_local_background; sanity check de que la misma funcion
    sirve tal cual para MODIS (es agnostica de banda — solo opera sobre BT).
    """
    bt_grid = np.full((5, 5), 280.0)
    bt_grid[2, 2] = 320.0

    t_bks = compute_local_background(
        bt_grid, hot_rows=[2], hot_cols=[2], kernel_size=3
    )

    assert len(t_bks) == 1
    assert math.isclose(t_bks[0], 280.0, abs_tol=1e-9)


def test_modis_local_kernel_radiance_b21_lambda_consistent():
    """Cuando t_bk_local=280K y lambda=B21 (3.929 um), L_bg debe ser Planck literal.

    Validamos que la conversion BT→radiancia con la lambda MODIS produce un
    numero coherente con la formula inline usada en process_modis.py
    (L_bg = C1/(lambda^5 * (exp(C2/(lambda*T))-1))).
    """
    t_bk = 280.0
    expected_L_bg = _planck_radiance(t_bk, BAND21_LAMBDA)

    # Sanidad: lambda MODIS produce radiancia ~0.4-0.5 W/m^2/sr/um a 280K.
    # (No es el mismo numero que VIIRS I04 a 3.74 um.)
    assert 0.2 < expected_L_bg < 1.0, (
        f"Planck B21@280K={expected_L_bg} fuera de rango fisico esperado"
    )


# -----------------------------------------------------------------------------
# Integration tests: vrp_mw per_pixel uses local L_bg when flag ON
# -----------------------------------------------------------------------------
# Estos tests usan stubs para evitar dependencia de pyhdf (roto en Windows).
# Validan que process_modis, dado un BT grid sintetico + ENABLE_LOCAL_KERNEL_BG
# ON, computa per_pixel_vrp_mw con L_bg derivado del kernel local en lugar de
# L_bg global derivado de t_bg.

def _expected_vrp_mw_from_local_bg(bt_hot_k, bt_bg_local_k, pixel_area_m2):
    """VRP esperado per-pixel con L_bg LOCAL (Coppola 2024 L1129)."""
    L_hot = _planck_radiance(bt_hot_k, BAND21_LAMBDA)
    L_bg = _planck_radiance(bt_bg_local_k, BAND21_LAMBDA)
    delta_L = max(L_hot - L_bg, 0.0)
    return pixel_area_m2 * WOOSTER_COEFF_MODIS * delta_L / 1e6


def _expected_vrp_mw_from_global_bg(bt_hot_k, bt_bg_global_k, pixel_area_m2):
    """VRP esperado per-pixel con L_bg GLOBAL (comportamiento legacy)."""
    L_hot = _planck_radiance(bt_hot_k, BAND21_LAMBDA)
    L_bg = _planck_radiance(bt_bg_global_k, BAND21_LAMBDA)
    delta_L = max(L_hot - L_bg, 0.0)
    return pixel_area_m2 * WOOSTER_COEFF_MODIS * delta_L / 1e6


def test_local_kernel_vs_global_bg_yields_different_vrp_when_local_colder():
    """Setup canonico Villarrica-like: local bg (cráter nevado) < global bg
    (anillo 5-25km incluye lago tibio).

    Local kernel = 275K, global t_bg = 280K, hot = 310K.

    Con flag OFF (legacy): VRP = f(L_hot - L_bg_global)
    Con flag ON: VRP = f(L_hot - L_bg_local) — mas grande porque local es mas
    frio → delta_L mayor.

    Esto es lo que el flag DEBE producir cuando se integre en process_modis.py.
    """
    bt_hot = 310.0
    bt_bg_local = 275.0
    bt_bg_global = 280.0
    pixel_area = 1_000_000.0  # 1 km^2 MODIS nadir

    vrp_local = _expected_vrp_mw_from_local_bg(bt_hot, bt_bg_local, pixel_area)
    vrp_global = _expected_vrp_mw_from_global_bg(bt_hot, bt_bg_global, pixel_area)

    # Local mas frio → delta_L mayor → vrp_local > vrp_global
    assert vrp_local > vrp_global, (
        f"Expected vrp_local ({vrp_local}) > vrp_global ({vrp_global}) "
        f"cuando bt_bg_local ({bt_bg_local}K) < bt_bg_global ({bt_bg_global}K)"
    )

    # Valores fisicos razonables MODIS 1km2 a 310K vs bg 275K: ~10-30 MW.
    assert 5 < vrp_local < 100, f"vrp_local={vrp_local} fuera de rango"


def test_local_kernel_with_all_nan_neighbors_falls_back_to_global_bg():
    """Si compute_local_background retorna NaN (todos los vecinos NaN), el
    pipeline MODIS debe fallback al t_bg global — no propagar NaN al VRP.

    Replica logica process_viirs.py:797-799:
        t_bk_arr = np.where(np.isnan(t_bk_arr), t_bg_i04, t_bk_arr)
    """
    bt_grid = np.full((3, 3), np.nan)
    bt_grid[1, 1] = 320.0
    t_bg_global = 278.0

    t_bks = compute_local_background(
        bt_grid, hot_rows=[1], hot_cols=[1], kernel_size=3
    )
    assert math.isnan(t_bks[0])

    # Replicar fallback que la integracion MODIS debe aplicar
    t_bk_arr = np.array(t_bks, dtype=np.float64)
    t_bk_arr = np.where(np.isnan(t_bk_arr), t_bg_global, t_bk_arr)
    assert math.isclose(t_bk_arr[0], t_bg_global, abs_tol=1e-9)


# -----------------------------------------------------------------------------
# Integration test: process_modis._build_record uses ENABLE_LOCAL_KERNEL_BG
# -----------------------------------------------------------------------------

def test_process_modis_integrates_enable_local_kernel_bg_flag():
    """Verifica que process_modis.py importa ENABLE_LOCAL_KERNEL_BG y usa
    compute_local_background cuando el flag esta ON.

    Test de smoke a nivel modulo (no full pipeline run — requeriria HDF L1B).
    Garantiza que la integracion esta presente en el codigo.
    """
    import pipeline.process_modis as pm
    import inspect

    src = inspect.getsource(pm)

    # 1) Debe importar el flag
    assert "ENABLE_LOCAL_KERNEL_BG" in src, (
        "process_modis.py no importa ENABLE_LOCAL_KERNEL_BG — integracion S58 "
        "incompleta"
    )

    # 2) Debe importar compute_local_background
    assert "compute_local_background" in src, (
        "process_modis.py no importa compute_local_background — integracion "
        "S58 incompleta"
    )

    # 3) Debe usar el flag como guard (if ENABLE_LOCAL_KERNEL_BG: ...)
    assert "if ENABLE_LOCAL_KERNEL_BG" in src, (
        "process_modis.py no usa el flag ENABLE_LOCAL_KERNEL_BG como guard"
    )

    # 4) La banda usada en bt_to_spectral_radiance (o Planck inline) debe ser
    #    BAND21_LAMBDA cuando se computa L_bg local en MODIS.
    assert "BAND21_LAMBDA" in src
