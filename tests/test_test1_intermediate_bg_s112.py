"""S112 Parte B Q3 — fondo de anillo INTERMEDIO para el recompute de magnitud Test1.

POR QUÉ (fenómeno): en un cráter con calor crónico (NdC Nicanor, domo activo + lava
reciente) el anillo local 1-3 km está contaminado por la propia anomalía → el exceso
MIR se recorta a 0 (FN de magnitud). El anillo global 5-25 km es nieve/roca de altura
fría → el exceso se infla (~4.4× MIROVA). El anillo INTERMEDIO (2-4 / 3-5 km) es el
"Goldilocks": fuera del halo de calor crónico pero sobre terreno de altitud similar,
así que no infla.

POR QUÉ (mecanismo): el recompute del Test1 usa `effective_L_bg`. Hoy elige
global (per-vol lbg_global_compatible) o local. Q3 añade el anillo intermedio con
PRECEDENCIA sobre el global cuando su flag está ON. Default OFF → legacy idéntico.

Helpers puros bajo prueba: `intermediate_ring_bg_bt`, `select_test1_effective_lbg`.
"""
from __future__ import annotations
import importlib
import math

import numpy as np

from pipeline.test1_integrated import (
    intermediate_ring_bg_bt,
    select_test1_effective_lbg,
)


def _radial_grid(bt_inner, bt_ring, bt_outer):
    """Grid 11x11 (~0.5 km/px) centrado en el vent; asigna BT por anillo de distancia.

    Devuelve (bt, dist_km) donde dist_km es la distancia al centro en km.
    """
    n = 11
    cy = cx = n // 2
    km_per_px = 0.5
    yy, xx = np.mgrid[0:n, 0:n]
    dist_km = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2) * km_per_px
    bt = np.full((n, n), np.nan, dtype=np.float64)
    bt[dist_km <= 1.5] = bt_inner          # halo de calor crónico (cráter)
    bt[(dist_km > 1.5) & (dist_km <= 4.0)] = bt_ring   # anillo intermedio
    bt[dist_km > 4.0] = bt_outer           # afuera, frío
    return bt, dist_km


def test_intermediate_ring_bg_bt_returns_ring_median():
    """La mediana se toma SOLO sobre los píxeles del anillo [r_in, r_out]."""
    bt, dist = _radial_grid(bt_inner=290.0, bt_ring=272.0, bt_outer=265.0)
    val = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0, min_pixels=5)
    assert math.isfinite(val)
    assert abs(val - 272.0) < 1e-9, f"esperaba la mediana del anillo (272 K); got {val}"


def test_intermediate_ring_bg_bt_excludes_inner_crater_heat():
    """El cráter caliente (1.5 km) NO debe contaminar el fondo intermedio."""
    bt, dist = _radial_grid(bt_inner=300.0, bt_ring=272.0, bt_outer=265.0)
    val = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0, min_pixels=5)
    assert abs(val - 272.0) < 1e-9, "el calor del cráter no debe entrar al fondo intermedio"


def test_intermediate_ring_bg_bt_nan_when_insufficient():
    """Menos de min_pixels válidos en el anillo → NaN (fallback aguas arriba)."""
    bt, dist = _radial_grid(bt_inner=290.0, bt_ring=272.0, bt_outer=265.0)
    val = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0, min_pixels=10_000)
    assert math.isnan(val), f"con min_pixels enorme debe devolver NaN; got {val}"


def test_intermediate_ring_bg_bt_nan_safe():
    """NaNs en el array no rompen ni sesgan la mediana."""
    bt, dist = _radial_grid(bt_inner=290.0, bt_ring=272.0, bt_outer=265.0)
    bt[0, 0] = np.nan  # esquina (afuera del anillo igual)
    val = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0, min_pixels=5)
    assert abs(val - 272.0) < 1e-9


def test_intermediate_ring_bg_bt_excludes_clouds_via_valid_mask():
    """S112 review (MEDIUM): topes de nube frios dentro del anillo NO deben bajar la
    mediana del fondo. El fondo global usa cloud_free (I05>=260K); el anillo intermedio
    debe usar el MISMO criterio (apples-to-apples) o sesgaria la magnitud al ALZA en
    noches con cirrus (justo al reves del objetivo del A/B)."""
    bt, dist = _radial_grid(bt_inner=290.0, bt_ring=272.0, bt_outer=265.0)
    # inyectar pixeles de nube fria (250 K) dentro del anillo
    ring = (dist >= 2.0) & (dist <= 4.0)
    cloud = np.zeros_like(bt, dtype=bool)
    ring_idx = np.argwhere(ring)
    for (iy, ix) in ring_idx[: len(ring_idx) // 2]:  # la mitad del anillo es nube
        bt[iy, ix] = 250.0
        cloud[iy, ix] = True
    valid = ~cloud  # cloud_free
    # SIN mascara: la mediana baja (contaminada por nubes)
    val_nomask = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0, min_pixels=5)
    assert val_nomask < 272.0, "sin mascara las nubes frias bajan la mediana (control)"
    # CON mascara: las nubes quedan fuera -> mediana del terreno (272 K)
    val_masked = intermediate_ring_bg_bt(bt, dist, r_in_km=2.0, r_out_km=4.0,
                                         min_pixels=5, valid_mask=valid)
    assert abs(val_masked - 272.0) < 1e-9, (
        f"con cloud_free las nubes no deben entrar; got {val_masked}")


def test_select_effective_lbg_intermediate_takes_precedence():
    """Intermedio ON + finito → gana sobre global y local."""
    chosen = select_test1_effective_lbg(
        intermediate_enabled=True, intermediate_lbg=5.0,
        global_enabled=True, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen == 5.0


def test_select_effective_lbg_intermediate_gated_by_lbg_global_compatible():
    """S112 adopción (A45 scope): el anillo intermedio SOLO aplica a vols
    lbg_global_compatible (los 3 nevados con calor crónico Lascar/NdC/Lastarria, donde el
    fondo global se contamina con valles tibios). En un vol NO compatible, intermedio ON
    NO debe usarse → cae al local (legacy). Evita cambiar la magnitud de vols no validados
    en el A/B."""
    # vol NO compatible: intermedio ON pero se ignora → local
    chosen = select_test1_effective_lbg(
        intermediate_enabled=True, intermediate_lbg=5.0,
        global_enabled=True, lbg_global_compatible=False, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen == 9.0, "intermedio NO debe aplicar a vol no-compatible"
    # vol compatible: intermedio ON → se usa
    chosen_c = select_test1_effective_lbg(
        intermediate_enabled=True, intermediate_lbg=5.0,
        global_enabled=True, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen_c == 5.0, "intermedio SÍ aplica a vol compatible"


def test_select_effective_lbg_intermediate_none_falls_to_global():
    """Intermedio ON pero None/NaN → cae al global (si habilitado y compatible)."""
    chosen = select_test1_effective_lbg(
        intermediate_enabled=True, intermediate_lbg=None,
        global_enabled=True, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen == 2.0
    chosen_nan = select_test1_effective_lbg(
        intermediate_enabled=True, intermediate_lbg=float("nan"),
        global_enabled=True, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen_nan == 2.0


def test_select_effective_lbg_legacy_global_when_intermediate_off():
    """Flag intermedio OFF → comportamiento LEGACY: global cuando enabled+compatible+finito."""
    chosen = select_test1_effective_lbg(
        intermediate_enabled=False, intermediate_lbg=5.0,
        global_enabled=True, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0)
    assert chosen == 2.0, "intermedio OFF no debe usar su valor"


def test_select_effective_lbg_legacy_local_fallback():
    """Sin intermedio y sin global aplicable → local (S26 default)."""
    # global deshabilitado
    assert select_test1_effective_lbg(
        intermediate_enabled=False, intermediate_lbg=None,
        global_enabled=False, lbg_global_compatible=True, global_lbg=2.0,
        local_lbg=9.0) == 9.0
    # global habilitado pero vol no compatible
    assert select_test1_effective_lbg(
        intermediate_enabled=False, intermediate_lbg=None,
        global_enabled=True, lbg_global_compatible=False, global_lbg=2.0,
        local_lbg=9.0) == 9.0
    # global habilitado+compatible pero NaN
    assert select_test1_effective_lbg(
        intermediate_enabled=False, intermediate_lbg=None,
        global_enabled=True, lbg_global_compatible=True, global_lbg=float("nan"),
        local_lbg=9.0) == 9.0


def test_select_effective_lbg_global_inf_falls_to_local():
    """S112 review (LOW, fija contrato): un global_lbg no-finito (inf) NO se propaga al
    recompute. El legacy con `not np.isnan` propagaba inf; el código nuevo (isfinite) cae
    al local. Mejora deliberada (operacionalmente inalcanzable, t_bg viene de LUT acotado
    A37, pero se fija el contrato para que un refactor futuro no lo revierta)."""
    chosen = select_test1_effective_lbg(
        intermediate_enabled=False, intermediate_lbg=None,
        global_enabled=True, lbg_global_compatible=True, global_lbg=float("inf"),
        local_lbg=9.0)
    assert chosen == 9.0, "global inf debe rechazarse y caer al local"


def test_intermediate_ring_robust_to_halo_overlap_at_3km():
    """S112 review (LOW): el halo de calor crónico del Nicanor llega a ~3 km, así que el
    anillo Q3a [2,4] muestrea 2-3 km de halo caliente. La mediana es robusta a una fracción
    de píxeles calientes — no debe devolver un fondo descabellado. Q3b [3,5] cubre el caso
    de halo extendido (la lectura Q3a vs Q3b discrimina cuánto se extiende el halo)."""
    # cráter+halo caliente hasta 3 km (290 K), anillo terreno 272 K, afuera frío
    n = 11; cy = cx = n // 2; km = 0.5
    yy, xx = np.mgrid[0:n, 0:n]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2) * km
    bt = np.full((n, n), np.nan)
    bt[dist <= 3.0] = 290.0          # halo crónico extendido a 3 km
    bt[(dist > 3.0) & (dist <= 5.0)] = 272.0
    # anillo [2,4] solapa halo (2-3km caliente) + terreno (3-4km) -> mediana entre ambos,
    # acotada (no devuelve el pico ni un valor sin sentido)
    val24 = intermediate_ring_bg_bt(bt, dist, 2.0, 4.0, min_pixels=5)
    assert 272.0 <= val24 <= 290.0, f"fondo [2,4] acotado entre terreno y halo; got {val24}"
    # anillo [3,5] queda fuera del halo -> terreno limpio
    val35 = intermediate_ring_bg_bt(bt, dist, 3.0, 5.0, min_pixels=5)
    assert abs(val35 - 272.0) < 1e-9, f"[3,5] fuera del halo = terreno 272; got {val35}"


def test_profile_intermediate_bg_default_off_unset(monkeypatch):
    """El flag es default OFF cuando un perfil no lo activa (un perfil base sin el flag)."""
    monkeypatch.setenv("VRP_PROFILE", "_baseline_s44")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_INTERMEDIATE_BG is False


def test_profile_intermediate_bg_ADOPTED_operacional_s112(monkeypatch):
    """S112 ADOPTADO (2026-06-17): recuperar la magnitud Muy Bajo VIIRS375 (reactivación
    NdC, paridad MIROVA 0.06 corroborada por Sentinel-2). El operacional activa Parte A
    (weak-cluster) + anillo intermedio, gateado per-vol por lbg_global_compatible
    (Lascar/NdC/Lastarria). Ring default [2,4] km. Tag pre-s112-intermediate-bg-adoption."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_PRIORITY_WEAK_CLUSTER is True
    assert profile.ENABLE_TEST1_INTERMEDIATE_BG is True
    assert tuple(profile.TEST1_INTERMEDIATE_BG_RING_KM) == (2.0, 4.0)
