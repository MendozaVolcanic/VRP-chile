"""Tests TDD — magnitud MODIS núcleo focal/contextual del cluster (S109 §1).

Design: docs/superpowers/specs/2026-06-14-magnitud-modis-nucleo-focal-design.md

La magnitud del cluster suma SOLO los píxeles contextualmente anómalos (anómalos vs
sus 8 vecinos = dNTI, Coppola 2016a Tests 2/3) ∪ {pico}. El campo difuso tibio uniforme
(no anómalo vs vecinos) se cae; el foco discreto (cráter activo / lava / INCENDIO) se
conserva. Generaliza a la magnitud del cluster el filtro contextual ya adoptado en VIIRS
(ctxpeak, test1_contextual_filter.py, S100). Coppola 2023 Eq.1: "VRP fundamentally
insensitive to diffuse heat dispersed from the crater area a few degrees above background".

Iron Law TDD: escritos ANTES de implementar `cluster_focal_vrp_mw` (RED = ImportError).

Mecanismo físico bajo prueba:
- Campo difuso (Chaitén/Villarrica nevados): píxeles ~10K sobre fondo, ninguno anómalo
  vs sus vecinos → con keep_peak colapsa al pico (≈MIROVA ~0); sin keep_peak → 0 (canario).
- Foco discreto (incendio / lava / Láscar): píxel dominante anómalo vs vecinos → conservado.
"""
from __future__ import annotations

import numpy as np
import pytest

# Import bajo prueba — falla en RED (no existe aún)
from pipeline.vrp_regimes import cluster_focal_vrp_mw


def _diffuse_cluster():
    """Cluster 3x3 (9 px) difuso: pico 1.2 MW, resto 0.6 MW. Suma cruda = 6.0 MW.
    Ningún píxel contextualmente anómalo (dnti_ctx todo False sobre el cluster)."""
    vrp = np.zeros((5, 5), dtype=float)
    idx = [(i, j) for i in (1, 2, 3) for j in (1, 2, 3)]
    for (i, j) in idx:
        vrp[i, j] = 0.6
    vrp[2, 2] = 1.2  # pico (cráter más caliente del campo)
    ctx = np.zeros((5, 5), dtype=bool)
    return vrp, ctx, idx


# =============================================================================
# Campo difuso → colapsa al pico (keep_peak) o a 0 (canario)
# =============================================================================

def test_diffuse_cluster_collapses_to_peak_with_keeppeak():
    vrp, ctx, idx = _diffuse_cluster()
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 1.2), f"esperado solo el pico 1.2, got {vrp_mw}"
    assert n_focal == 1
    assert degraded is True  # ningún píxel contextual → solo sobrevivió el pico


def test_diffuse_pure_canary_gives_zero():
    """keep_peak=False (canario): sin foco contextual → magnitud 0. Revela
    honestamente que el cluster es campo topográfico puro sin anomalía contextual."""
    vrp, ctx, idx = _diffuse_cluster()
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=False)
    assert np.isclose(vrp_mw, 0.0)
    assert n_focal == 0
    assert degraded is True


# =============================================================================
# Foco contextual → se conserva
# =============================================================================

def test_contextual_pixels_are_summed():
    """3 píxeles anómalos vs vecinos → se suman (el resto difuso se cae)."""
    vrp, ctx, idx = _diffuse_cluster()
    ctx[2, 2] = ctx[1, 1] = ctx[3, 3] = True  # pico + 2 esquinas anómalas
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 1.2 + 0.6 + 0.6), f"got {vrp_mw}"
    assert n_focal == 3
    assert degraded is False


def test_keeppeak_preserves_hottest_even_if_not_contextual():
    """Cráter embebido: el pico NO es contextual pero es el más caliente → keep_peak
    lo conserva igual (anti-FN sub-píxel). Suma = ctx(0.6) + pico(1.2)."""
    vrp, ctx, idx = _diffuse_cluster()
    ctx[1, 1] = True            # un píxel contextual, NO el pico
    # pico (2,2)=1.2 no es contextual
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 0.6 + 1.2), f"got {vrp_mw}"
    assert n_focal == 2


def test_fire_focal_pixel_preserved():
    """Restricción de Nicolás: un INCENDIO (foco dominante, anómalo vs vecinos) se
    conserva mientras el campo difuso de su entorno se cae. Pico 5.0 MW (fuego) ctx;
    8 vecinos difusos 0.3 MW no-ctx → se conserva 5.0, se cae el difuso (2.4)."""
    vrp = np.zeros((5, 5), dtype=float)
    idx = [(i, j) for i in (1, 2, 3) for j in (1, 2, 3)]
    for (i, j) in idx:
        vrp[i, j] = 0.3
    vrp[2, 2] = 5.0
    ctx = np.zeros((5, 5), dtype=bool)
    ctx[2, 2] = True  # el fuego ES anómalo vs sus vecinos
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 5.0), f"el fuego debe sobrevivir intacto, got {vrp_mw}"
    assert n_focal == 1
    assert degraded is False


def test_all_contextual_preserves_full_sum():
    """Anomalía multi-píxel genuina (todos contextuales) → suma completa, sin recorte."""
    vrp = np.zeros((4, 4), dtype=float)
    idx = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for (i, j) in idx:
        vrp[i, j] = 1.0
    ctx = np.zeros((4, 4), dtype=bool)
    for (i, j) in idx:
        ctx[i, j] = True
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw(idx, vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 4.0)
    assert n_focal == 4
    assert degraded is False


def test_empty_cluster_returns_zero():
    """Guard: cluster vacío → 0, n_focal 0, degraded True (no crash)."""
    vrp = np.zeros((3, 3), dtype=float)
    ctx = np.zeros((3, 3), dtype=bool)
    vrp_mw, n_focal, degraded = cluster_focal_vrp_mw([], vrp, ctx, keep_peak=True)
    assert np.isclose(vrp_mw, 0.0)
    assert n_focal == 0
    assert degraded is True
