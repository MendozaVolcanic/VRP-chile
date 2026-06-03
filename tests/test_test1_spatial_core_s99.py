"""S99 Candidato B — TDD recorte de compacidad espacial Test 1.

Fenómeno: sobre el glaciar nevado de Tupungatito, el Test 1 integrado marca un
anillo nival difuso (1-3 km) de píxeles marginalmente sobre el fondo frío. El VRP
suma todo ese halo → factor ~19× MIROVA. El discriminante correcto es ESPACIAL
(foco compacto vs halo difuso), NO térmico (t_bg refutado S86/A54).

`spatial_core_filter` conserva solo el foco compacto alrededor del píxel de máxima
energía (R_core), conservando SIEMPRE el pico (guard anti-falso-negativo: un foco
sub-píxel genuino como el lava lake de Villarrica nunca queda en VRP=0), más
píxeles de lava extendida real (bt ≥ bt_ext_k).

Análogo en pipeline del Núcleo F5' display (frontend `f5CoreMagnitude`, S95).
Función pura, sin I/O. Default OFF (flag `enable_test1_spatial_core`).
"""
from __future__ import annotations

import importlib
import numpy as np
import pytest

from pipeline.scan_geometry import haversine_km


def _grid(n=11, center_lat=-33.38, center_lon=-69.83, px_km=0.375):
    """Grid n×n centrado en (center_lat, center_lon), espaciado ~px_km."""
    dlat = px_km / 111.0
    dlon = px_km / (111.0 * np.cos(np.radians(center_lat)))
    half = n // 2
    rows = (np.arange(n) - half) * dlat + center_lat
    cols = (np.arange(n) - half) * dlon + center_lon
    lat = np.repeat(rows[:, None], n, axis=1)
    lon = np.repeat(cols[None, :], n, axis=0)
    return lat, lon


# ---------------------------------------------------------------------------
# 1. CURA: el halo nival lejano se desinfla, el foco compacto se conserva.
# ---------------------------------------------------------------------------
def test_spatial_core_deflates_nival_halo():
    from pipeline.test1_spatial_core import spatial_core_filter
    lat, lon = _grid(n=11)
    c = 5  # centro
    bt = np.full((11, 11), 255.0)  # glaciar frío
    vrp = np.zeros((11, 11))
    mask = np.zeros((11, 11), dtype=bool)

    # Foco compacto: pico en el centro + 2 vecinos inmediatos (<0.75 km)
    for (r, cc, v) in [(c, c, 0.20), (c, c + 1, 0.05), (c + 1, c, 0.04)]:
        mask[r, cc] = True
        vrp[r, cc] = v
        bt[r, cc] = 262.0  # tibio pero sub-pixel, NO lava (<295)

    # Halo nival difuso: anillo de píxeles marginales a >0.75 km del pico
    halo = [(0, 0), (0, 10), (10, 0), (10, 10), (1, 5), (9, 5), (5, 1), (5, 9),
            (2, 2), (8, 8), (2, 8), (8, 2), (3, 0), (0, 3)]
    for (r, cc) in halo:
        mask[r, cc] = True
        vrp[r, cc] = 0.06  # cada uno marginal, pero SUMAN mucho
        bt[r, cc] = 258.0  # tibio relativo a 255, NO lava

    n_before = int(mask.sum())
    vrp_before = float(vrp[mask].sum())

    res = spatial_core_filter(mask, vrp, lat, lon, bt, r_core_km=0.75, bt_ext_k=295.0)
    fmask = res["mask"]
    vrp_after = float(vrp[fmask].sum())

    # El pico (foco) siempre conservado
    assert fmask[c, c], "el pixel de maxima energia debe conservarse siempre"
    # El halo lejano se cae
    assert not fmask[0, 0] and not fmask[10, 10], "halo lejano debe descartarse"
    # Conserva muchos menos pixels y baja la magnitud sustancialmente
    assert int(fmask.sum()) < n_before
    assert vrp_after < vrp_before
    # La cura: el VRP del nucleo es ~el foco (0.29), no el halo entero (~1.13)
    assert vrp_after <= 0.4, f"nucleo deberia ~foco compacto, got {vrp_after}"
    assert vrp_before > 1.0, "setup: el halo debe inflar el baseline"


# ---------------------------------------------------------------------------
# 2. CANARIO FN: un foco sub-píxel solitario (Villarrica lava lake) NUNCA → 0.
# ---------------------------------------------------------------------------
def test_spatial_core_preserves_compact_subpixel():
    from pipeline.test1_spatial_core import spatial_core_filter
    lat, lon = _grid(n=11)
    c = 5
    bt = np.full((11, 11), 250.0)
    vrp = np.zeros((11, 11))
    mask = np.zeros((11, 11), dtype=bool)
    # Un solo pixel: lava lake sub-pixel débil
    mask[c, c] = True
    vrp[c, c] = 0.12
    bt[c, c] = 268.0  # sub-pixel, no supera umbral por-pixel duro

    res = spatial_core_filter(mask, vrp, lat, lon, bt, r_core_km=0.75, bt_ext_k=295.0)
    fmask = res["mask"]
    assert fmask[c, c], "el unico foco compacto debe conservarse (anti-FN)"
    assert float(vrp[fmask].sum()) == pytest.approx(0.12), "VRP nunca debe caer a 0"
    assert int(fmask.sum()) == 1


# ---------------------------------------------------------------------------
# 3. Lava extendida real (bt alto) se conserva aunque esté lejos del pico.
# ---------------------------------------------------------------------------
def test_spatial_core_keeps_extended_hot_lava():
    from pipeline.test1_spatial_core import spatial_core_filter
    lat, lon = _grid(n=11)
    c = 5
    bt = np.full((11, 11), 250.0)
    vrp = np.zeros((11, 11))
    mask = np.zeros((11, 11), dtype=bool)
    mask[c, c] = True; vrp[c, c] = 0.30; bt[c, c] = 320.0  # pico lava
    # Píxel lejano (>0.75km) PERO con BT de lava genuina (>=295)
    mask[0, 0] = True; vrp[0, 0] = 0.25; bt[0, 0] = 300.0
    # Píxel lejano tibio NO-lava → debe caer
    mask[10, 10] = True; vrp[10, 10] = 0.05; bt[10, 10] = 260.0

    res = spatial_core_filter(mask, vrp, lat, lon, bt, r_core_km=0.75, bt_ext_k=295.0)
    fmask = res["mask"]
    assert fmask[c, c], "pico conservado"
    assert fmask[0, 0], "lava extendida real (bt>=295) conservada aunque lejos"
    assert not fmask[10, 10], "tibio lejano no-lava descartado"


# ---------------------------------------------------------------------------
# 4. Mask vacía / sin píxeles → identidad (defensa).
# ---------------------------------------------------------------------------
def test_spatial_core_empty_mask_identity():
    from pipeline.test1_spatial_core import spatial_core_filter
    lat, lon = _grid(n=5)
    bt = np.full((5, 5), 250.0)
    vrp = np.zeros((5, 5))
    mask = np.zeros((5, 5), dtype=bool)
    res = spatial_core_filter(mask, vrp, lat, lon, bt)
    assert int(res["mask"].sum()) == 0


# ---------------------------------------------------------------------------
# 5. Flags de perfil: default OFF en operacional, ON en perfil A/B core.
# ---------------------------------------------------------------------------
def test_profile_flag_default_off(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_SPATIAL_CORE is False
    assert profile.TEST1_CORE_R_KM == pytest.approx(0.75)
    assert profile.TEST1_CORE_BT_EXT_K == pytest.approx(295.0)


def test_profile_flag_on_in_core_profile(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "_s99_test1_core")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_SPATIAL_CORE is True
    assert profile.ENABLE_TEST1_PATH is True
