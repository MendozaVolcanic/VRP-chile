"""S104 — TDD: co-validación NTI del Test1 integrado (realineamiento MIROVA).

Causa raíz (docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md): compute_test1_mir integra
exceso de radiancia MIR ABSOLUTA sobre todo el ROI y pondera el centroide por ese
exceso, sin gate NTI → en volcanes nevados el terreno tibio de baja altitud
(gradiente topográfico) supera la mediana del anillo, dispara el Test1 y arrastra
el centroide lejos del cráter.

Fix: nuevo parámetro `nti_hot_mask` (2-D bool). Cuando se provee, solo los píxeles
que también pasaron un path NTI relativo cuentan para disparar/integrar/posicionar
(Coppola 2024 Eq.13). El valle tibio (NTI plano) queda excluido; el lava lake real
(que pasa dNTI) se conserva.
"""
import numpy as np
import pytest

from pipeline.test1_integrated import compute_test1_mir

LAMBDA_I04 = 3.74
VLAT, VLON = -39.420, -71.940


def _grid(n=41, step_deg=0.004):
    """Grid cuadrado centrado en el vent. step≈0.004° ≈ 375 m (VIIRS I-band)."""
    offs = (np.arange(n) - n // 2) * step_deg
    lat = VLAT + offs[:, None] * np.ones(n)[None, :]
    lon = VLON + np.ones(n)[:, None] * offs[None, :]
    return lat, lon


def _cold_bg(lat, seed):
    """Fondo frío con ruido natural determinista (sigma_bg > 0, como el caso real)."""
    rng = np.random.default_rng(seed)
    return 270.0 + rng.normal(0.0, 0.4, lat.shape)


def _topographic_field():
    """Campo SIN lava: parche tibio COMPACTO desplazado al Norte (valle de baja
    altitud) sobre fondo frío. Simula el gradiente topográfico — calor real
    térmico, NO volcánico. El parche es chico vs el anillo de fondo, así que la
    mediana del fondo se mantiene fría y el exceso dispara el Test1 (drift actual)."""
    lat, lon = _grid()
    bt = _cold_bg(lat, seed=1)
    c = lat.shape[0] // 2
    # parche 3x3 ~2 km al Norte (índice mayor = lat mayor = N en hemisferio sur)
    bt[c + 5:c + 8, c - 1:c + 2] = 282.0
    return bt, lat, lon


def _lava_field():
    """Campo CON lava sub-pixel: parche caliente compacto EN el cráter."""
    lat, lon = _grid()
    bt = _cold_bg(lat, seed=2)
    c = lat.shape[0] // 2
    bt[c - 1:c + 1, c - 1:c + 1] = 285.0  # foco caliente en el cráter
    return bt, lat, lon


def _mask_where(lat, lon, center_lat, center_lon, radius_km=0.8):
    """Bool mask True dentro de radius_km del punto dado (proxy de 'pasó NTI')."""
    from pipeline.scan_geometry import haversine_km
    return haversine_km(center_lat, center_lon, lat, lon) <= radius_km


# 1. Gradiente topográfico puro: el gate (máscara vacía en el valle) NO debe disparar
def test_topographic_field_with_empty_nti_mask_does_not_trigger():
    bt, lat, lon = _topographic_field()
    # baseline: SIN gate, el valle tibio dispara el Test1 (comportamiento drift actual)
    base = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04)
    assert base["triggered"] is True, "fixture inválido: el valle debe disparar sin gate"
    # con gate: ningún píxel del valle pasó NTI → máscara toda False → NO dispara
    nti_mask = np.zeros(bt.shape, dtype=bool)
    gated = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04, nti_hot_mask=nti_mask)
    assert gated["triggered"] is False
    assert gated["n_contributing"] == 0
    assert gated["centroid_lat"] is None


# 2. Lava real co-validada por NTI: el gate la conserva y ancla el centroide al cráter
def test_lava_field_with_nti_mask_triggers_and_anchors_to_crater():
    bt, lat, lon = _lava_field()
    nti_mask = _mask_where(lat, lon, VLAT, VLON, radius_km=0.9)  # NTI destaca en el cráter
    gated = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04, nti_hot_mask=nti_mask)
    assert gated["triggered"] is True
    assert gated["n_contributing"] >= 1
    # centroide a <0.7 km del cráter (no arrastrado)
    from pipeline.scan_geometry import haversine_km
    d = haversine_km(VLAT, VLON, gated["centroid_lat"], gated["centroid_lon"])
    assert d < 0.7, f"centroide a {d:.2f} km del cráter, debería estar anclado"


# 3. Mixto (gradiente + lava): el gate ancla al cráter, no al valle tibio
def test_mixed_field_gate_anchors_to_crater_not_warm_valley():
    bt_lava, lat, lon = _lava_field()
    bt_topo, _, _ = _topographic_field()
    bt = np.maximum(bt_lava, bt_topo)  # lava en cráter + valle tibio al N
    # sin gate: el centroide se sesga al Norte (valle extenso pesa)
    base = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04)
    from pipeline.scan_geometry import haversine_km
    d_base = haversine_km(VLAT, VLON, base["centroid_lat"], base["centroid_lon"])
    # con gate: solo la lava del cráter pasó NTI
    nti_mask = _mask_where(lat, lon, VLAT, VLON, radius_km=0.9)
    gated = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04, nti_hot_mask=nti_mask)
    d_gated = haversine_km(VLAT, VLON, gated["centroid_lat"], gated["centroid_lon"])
    assert d_gated < d_base, "el gate debe acercar el centroide al cráter"
    assert d_gated < 0.7


# 4. Backward-compat: nti_hot_mask=None ≡ comportamiento actual (sin el param)
def test_none_mask_is_backward_compatible():
    bt, lat, lon = _lava_field()
    without = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04)
    with_none = compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04, nti_hot_mask=None)
    assert without["triggered"] == with_none["triggered"]
    assert without["delta_L_integrated"] == pytest.approx(with_none["delta_L_integrated"])
    assert without["n_contributing"] == with_none["n_contributing"]
    assert without["centroid_lat"] == with_none["centroid_lat"]


# 5. Guard: nti_hot_mask con shape distinto → ValueError
def test_mask_shape_mismatch_raises():
    bt, lat, lon = _lava_field()
    bad = np.zeros((3, 3), dtype=bool)
    with pytest.raises(ValueError):
        compute_test1_mir(bt, lat, lon, VLAT, VLON, LAMBDA_I04, nti_hot_mask=bad)
