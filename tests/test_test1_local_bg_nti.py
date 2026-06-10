"""S105 — TDD: Test1 con FONDO LOCAL sobre NTI (realineamiento MIROVA uniforme).

Diseño: docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md.

Clave (por qué V2 con fondo-anillo no bastó): en la realidad el NTI NO es exactamente
plano sobre el ROI — tiene ESTRUCTURA residual (gradiente suave por ruido / bordes de
nieve). El fondo-anillo (mediana del anillo entero) deja que un lado del gradiente supere
la mediana → dispara y arrastra el centroide al valle. El fondo LOCAL (mediana del anillo
local alrededor de cada píxel) captura esa estructura → cada píxel ~ su entorno → el valle
deja de ser anomalía. Solo la lava (que rompe la simetría MIR/TIR sobre su entorno frío)
destaca. Uniforme, sin per-vol (Coppola 2024 Eq.13).

API nueva: compute_test1_nti(..., local_bg_ring_km=(r_in, r_out), min_local_bg_pixels=N).
local_bg_ring_km=None → comportamiento actual (fondo anillo, backward-compat).
"""
import numpy as np
import pytest

from pipeline.test1_integrated import compute_test1_nti, bt_to_radiance_um
from pipeline.scan_geometry import haversine_km

LMIR, LTIR = 3.74, 11.45
VLAT, VLON = -39.420, -71.940
_C1, _C2 = 1.191042e8, 14387.7
LOCAL = (0.5, 1.5)  # anillo local (km) — mismo para todos los volcanes (uniforme)


def _inv_planck(L, lam):
    return _C2 / (lam * np.log((_C1 / lam**5) / L + 1.0))


def _grid(n=41, step=0.004):
    offs = (np.arange(n) - n // 2) * step
    lat = VLAT + offs[:, None] * np.ones(n)[None, :]
    lon = VLON + np.ones(n)[:, None] * offs[None, :]
    return lat, lon


def _nti_field_to_bt(nti_field, bt_tir):
    """Construye bt_mir tal que NTI = nti_field exacto, dado bt_tir."""
    L5 = bt_to_radiance_um(bt_tir, LTIR)
    L4 = L5 * (1 + nti_field) / (1 - nti_field)
    return _inv_planck(L4, LMIR)


def _topographic_structured():
    """NTI con GRADIENTE residual (no plano): el valle al N tiene NTI levemente mayor,
    simulando la estructura que el NTI no cancela del todo en la realidad. El fondo-anillo
    lo lee como anomalía (un lado supera la mediana); el fondo-local NO (gradiente suave)."""
    lat, lon = _grid()
    rng = np.random.default_rng(2)
    bt_tir = 268.0 + rng.normal(0, 0.3, lat.shape)
    n = lat.shape[0]
    rows = (np.arange(n)[:, None] * np.ones(n)[None, :] - n // 2) / (n // 2)
    nti_field = -0.96 + 0.012 * rows  # gradiente N-S suave +-0.012 (estructura residual)
    bt_mir = _nti_field_to_bt(nti_field, bt_tir)
    return bt_mir, bt_tir, lat, lon


def _lava_on_gradient():
    """Gradiente residual + foco de lava sub-pixel en el cráter (eleva L_MIR sin tocar
    L_TIR → NTI elevado y CONCENTRADO en el cráter, destaca sobre su entorno local)."""
    bt_mir, bt_tir, lat, lon = _topographic_structured()
    L4 = bt_to_radiance_um(bt_mir, LMIR)
    c = lat.shape[0] // 2
    L4[c - 1:c + 2, c - 1:c + 2] *= 2.2  # foco MIR sub-pixel en el cráter (3x3)
    bt_mir = _inv_planck(L4, LMIR)
    return bt_mir, bt_tir, lat, lon


# 1. CRÍTICO — gradiente residual de NTI: el fondo-anillo dispara (centroide al valle),
#    el fondo-local NO dispara (cada píxel ~ su entorno).
def test_structured_gradient_anillo_triggers_local_does_not():
    f = _topographic_structured()
    r_ring = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR)  # fondo anillo (actual)
    r_local = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR, local_bg_ring_km=LOCAL)
    assert r_ring["triggered"] is True, "el fondo-anillo debe disparar sobre el gradiente"
    assert r_local["triggered"] is False, "el fondo-local NO debe disparar (cada px ~ entorno)"


# 2. Lava sobre gradiente: el fondo-local dispara y ancla el centroide al cráter
def test_lava_on_gradient_local_anchors_to_crater():
    r = compute_test1_nti(*_lava_on_gradient(), VLAT, VLON, LMIR, LTIR, local_bg_ring_km=LOCAL)
    assert r["triggered"] is True
    d = haversine_km(VLAT, VLON, r["centroid_lat"], r["centroid_lon"])
    assert d < 0.7, f"centroide a {d:.2f} km del cráter (debe anclar al foco, no al valle)"


# 3. El fondo-local ancla MEJOR que el fondo-anillo sobre el mismo campo con lava+gradiente
def test_local_anchors_closer_than_ring_on_gradient():
    f = _lava_on_gradient()
    r_ring = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR)
    r_local = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR, local_bg_ring_km=LOCAL)
    d_ring = haversine_km(VLAT, VLON, r_ring["centroid_lat"], r_ring["centroid_lon"])
    d_local = haversine_km(VLAT, VLON, r_local["centroid_lat"], r_local["centroid_lon"])
    assert d_local <= d_ring + 1e-9, f"local {d_local:.2f} debe anclar <= anillo {d_ring:.2f}"


# 4. Backward-compat: local_bg_ring_km=None → idéntico al modo anillo actual
def test_backward_compat_none_is_ring_mode():
    f = _lava_on_gradient()
    r_def = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR)
    r_none = compute_test1_nti(*f, VLAT, VLON, LMIR, LTIR, local_bg_ring_km=None)
    assert r_def["triggered"] == r_none["triggered"]
    assert r_def["delta_nti_integrated"] == pytest.approx(r_none["delta_nti_integrated"])


# 5. Devuelve L_bg_mir también en modo local (el VRP usa MIR sobre píxeles NTI-elegidos)
def test_local_returns_l_bg_mir():
    r = compute_test1_nti(*_lava_on_gradient(), VLAT, VLON, LMIR, LTIR, local_bg_ring_km=LOCAL)
    assert r.get("L_bg_mir") is not None and r["L_bg_mir"] > 0


# 6. Guard: shapes distintos → ValueError (también en modo local)
def test_shape_mismatch_raises_local():
    bt_mir, bt_tir, lat, lon = _lava_on_gradient()
    with pytest.raises(ValueError):
        compute_test1_nti(bt_mir, bt_tir[:3, :3], lat, lon, VLAT, VLON, LMIR, LTIR,
                          local_bg_ring_km=LOCAL)
