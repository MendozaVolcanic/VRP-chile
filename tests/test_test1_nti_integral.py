"""S104 V2 — TDD: Test1 que integra exceso de NTI (no de MIR).

Ground truth (docs/AUDIT_S104 + 2 probes Actions): la lava débil (régimen típico
Villarrica, MIROVA ALERTA 0.11 MW) NO tiene firma per-píxel (1.8σ) pero el NTI está
levemente elevado y centrado en el cráter; la topografía tiene NTI plano aunque el
MIR tenga gradiente de 15 K. → integrar exceso de NTI distingue lava de topografía.

compute_test1_nti(bt_mir, bt_tir, ...) integra Σ max(0, NTI−NTI_bg) sobre el ROI y
 pondera el centroide por ese exceso. Dispara si el exceso integrado supera k·σ.
"""
import math
import numpy as np
import pytest

from pipeline.test1_integrated import compute_test1_nti, bt_to_radiance_um
from pipeline.scan_geometry import haversine_km

LMIR, LTIR = 3.74, 11.45
VLAT, VLON = -39.420, -71.940
_C1, _C2 = 1.191042e8, 14387.7


def _inv_planck(L, lam):
    """BT (K) desde radiancia espectral — inversa de bt_to_radiance_um."""
    return _C2 / (lam * np.log((_C1 / lam**5) / L + 1.0))


def _grid(n=41, step=0.004):
    offs = (np.arange(n) - n // 2) * step
    lat = VLAT + offs[:, None] * np.ones(n)[None, :]
    lon = VLON + np.ones(n)[:, None] * offs[None, :]
    return lat, lon


def _topographic():
    """Gradiente topográfico con NTI EXACTAMENTE constante: el terreno tibio sube
    MIR y TIR de modo que el cociente normalizado no cambia (así emite un cuerpo gris
    real). bt_mir se deriva invirtiendo Planck para fijar NTI = NTI0 en cada píxel,
    incluido el parche tibio al N. El NTI no debe disparar el Test1."""
    lat, lon = _grid()
    rng = np.random.default_rng(1)
    bt_tir = 268.0 + rng.normal(0, 0.3, lat.shape)
    c = lat.shape[0] // 2
    bt_tir[c + 5:c + 8, c - 1:c + 2] += 11.0  # valle tibio (sube TIR)
    NTI0 = -0.96
    L5 = bt_to_radiance_um(bt_tir, LTIR)
    L4 = L5 * (1 + NTI0) / (1 - NTI0)  # fija NTI = NTI0 constante
    bt_mir = _inv_planck(L4, LMIR)
    return bt_mir, bt_tir, lat, lon


def _weak_lava():
    """Lava débil sub-pixel: parte del campo topográfico NTI-plano y agrega un foco
    de radiancia MIR en el cráter (sub-pixel caliente eleva L_MIR sin tocar L_TIR) →
    NTI elevado y concentrado en el cráter."""
    bt_mir, bt_tir, lat, lon = _topographic()
    L4 = bt_to_radiance_um(bt_mir, LMIR)
    c = lat.shape[0] // 2
    L4[c - 1:c + 1, c - 1:c + 1] *= 1.5  # foco MIR en el cráter (TIR sin tocar)
    bt_mir = _inv_planck(L4, LMIR)
    return bt_mir, bt_tir, lat, lon


# 1. Topografía (NTI plano): NO dispara aunque el MIR tenga parche tibio
def test_topographic_nti_flat_does_not_trigger():
    bt_mir, bt_tir, lat, lon = _topographic()
    r = compute_test1_nti(bt_mir, bt_tir, lat, lon, VLAT, VLON, LMIR, LTIR)
    assert r["triggered"] is False


# 2. Lava débil (NTI elevado en cráter): dispara y ancla el centroide al cráter
def test_weak_lava_triggers_and_anchors_to_crater():
    bt_mir, bt_tir, lat, lon = _weak_lava()
    r = compute_test1_nti(bt_mir, bt_tir, lat, lon, VLAT, VLON, LMIR, LTIR)
    assert r["triggered"] is True
    d = haversine_km(VLAT, VLON, r["centroid_lat"], r["centroid_lon"])
    assert d < 0.7, f"centroide a {d:.2f} km del cráter"


# 3. El exceso de NTI integrado de la lava supera al de la topografía (separabilidad)
def test_lava_nti_excess_exceeds_topographic():
    rt = compute_test1_nti(*_topographic(), VLAT, VLON, LMIR, LTIR)
    rl = compute_test1_nti(*_weak_lava(), VLAT, VLON, LMIR, LTIR)
    assert rl["delta_nti_integrated"] > rt["delta_nti_integrated"]


# 4. Guard: shapes distintos → ValueError
def test_shape_mismatch_raises():
    bt_mir, bt_tir, lat, lon = _weak_lava()
    with pytest.raises(ValueError):
        compute_test1_nti(bt_mir, bt_tir[:3, :3], lat, lon, VLAT, VLON, LMIR, LTIR)
