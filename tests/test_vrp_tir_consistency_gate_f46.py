"""F46 fix S77 — Tests TDD para gate de consistencia MIR/NTI sobre vrp_tir_mw.

**STATUS**: tests RED contra estado actual de `pipeline/process_viirs.py`. Marcados
con `@pytest.mark.xfail(reason="F46 fix pending A45 — store.py:..., process_viirs.py:968-986")`.

Pre-fix (estado actual S76):
- `process_viirs.py:1050-1067` computa `vrp_tir_mw` con `max(0.5K, 4σ_bg)` como
  umbral sobre I05. En terreno heterogéneo (nieve/lago/cirrus) σ_bg se infla,
  ~100-230 pixels pasan el gate, cada uno aporta ~3-5 MW residual × A_pix →
  3 000-9 600 MW espurios. 143 records afectados en data/mirova_equivalent/.

Post-fix esperado (Opción A+B del `docs/F46_VRP_TIR_BUG_S76.md`):
- Helper nueva `_compute_vrp_tir_with_gate(bt5, roi_mask, pixel_areas, t_bg_i05,
    std_bg5, hot_mask_mir, *, tir_floor_k=3.0, n_sigma_tir=6.0)`
- Reglas:
  - Threshold = `max(tir_floor_k, n_sigma_tir * std_bg5)` (subido vs `max(0.5, 4σ)`).
  - Gate de consistencia: si `hot_mask_mir.sum() == 0` (MIR/NTI no detectó nada)
    entonces `vrp_tir_mw = 0` (sin coherencia espacial el TIR es espurio).
  - Si hay overlap espacial: VRP_TIR Stefan-Boltzmann sobre la intersección
    `hot5_mask ∩ dilate(hot_mask_mir, k=3)` (vecindad 3-pixel para tolerar
    desalineamiento sensor inter-band).

Tests cubren los 4 patrones físicos del audit:
1. Chaitén patognomónico — hot_mask_mir vacío, hot5_mask grande → 0 MW.
2. Lascar legítimo — ambos masks solapados → VRP_TIR > 0.
3. Terreno heterogéneo umbral subido — pixel ΔT=5 K con σ=2 K bajo nuevo
   threshold (max(3, 6×2)=12 K) NO dispara aunque pre-fix sí.
4. Anomalía real fuerte — pixel ΔT=20 K con σ=2 K SÍ dispara post-fix.

Refs:
- docs/F46_VRP_TIR_BUG_S76.md (plan completo, opciones A/B/A+B)
- experiments/138_audit_mw_outliers_s76/outliers.json
- tag defensivo: pre-s77-f46-vrp-tir-fix
"""
from __future__ import annotations

import numpy as np
import pytest

# Constantes físicas locales (replicadas para tests aislados)
SIGMA_SB = 5.670374419e-8  # Stefan-Boltzmann
A_PIX_VIIRS_I = 140625.0     # 375 × 375 m


def _try_import_gate():
    """Intenta importar la helper esperada post-fix. None si aún no existe."""
    try:
        from pipeline.process_viirs import _compute_vrp_tir_with_gate
        return _compute_vrp_tir_with_gate
    except ImportError:
        return None


_GATE = _try_import_gate()


@pytest.fixture
def scene_uniform_bg():
    """Escena base 8×8 a t_bg=285 K, sin pixels hot, máscara ROI completa."""
    bt5 = np.full((8, 8), 285.0)
    roi_mask = np.ones((8, 8), dtype=bool)
    pixel_areas = np.full((8, 8), A_PIX_VIIRS_I)
    return {
        "bt5": bt5,
        "roi_mask": roi_mask,
        "pixel_areas": pixel_areas,
        "t_bg_i05": 285.0,
        "std_bg5": 2.0,  # terreno heterogéneo Andino típico
    }


@pytest.mark.xfail(_GATE is None, reason="F46 fix pending A45 — helper no implementada todavía")
def test_chaiten_patognomonico_mir_vacio(scene_uniform_bg):
    """F46-A: cuando MIR/NTI no detectó nada, vrp_tir_mw = 0 (gate consistencia).

    Caso bandera Chaitén 2026-03-25 05:18 SNPP: n_anomalous_pixels=0 pero
    vrp_tir_mw=6872 MW en el código actual. Post-fix debe dar 0.
    """
    scene = scene_uniform_bg
    # Inyectar 100 pixels "tibios" a 290 K (ΔT=5 K) — pasan threshold pre-fix
    # max(0.5, 4×2)=8 K SÍ los descarta, pero terreno con σ=1.5 K (no 2)
    # baja threshold a max(0.5, 6)=6 → pixels ΔT=7 K disparan.
    scene["bt5"][2:6, 2:6] = 292.0  # 16 pixels @ 292 K, ΔT=7 K
    scene["std_bg5"] = 1.5
    # hot_mask_mir vacío (MIR no detectó)
    hot_mask_mir = np.zeros((8, 8), dtype=bool)

    result_mw = _GATE(
        scene["bt5"], scene["roi_mask"], scene["pixel_areas"],
        scene["t_bg_i05"], scene["std_bg5"], hot_mask_mir,
    )
    assert result_mw == 0.0, (
        f"Gate consistencia debe vetar vrp_tir cuando MIR/NTI vacío "
        f"(caso Chaitén patognomónico). Obtuvo {result_mw} MW."
    )


@pytest.mark.xfail(_GATE is None, reason="F46 fix pending A45")
def test_lascar_legitimo_mir_overlap(scene_uniform_bg):
    """F46-A: cuando MIR/NTI detectó pixels solapados con hot_tir → vrp_tir > 0."""
    scene = scene_uniform_bg
    scene["bt5"][3:5, 3:5] = 310.0  # 4 pixels a 310 K, ΔT=25 K — anomalía real
    # MIR detectó en la misma región
    hot_mask_mir = np.zeros((8, 8), dtype=bool)
    hot_mask_mir[3:5, 3:5] = True

    result_mw = _GATE(
        scene["bt5"], scene["roi_mask"], scene["pixel_areas"],
        scene["t_bg_i05"], scene["std_bg5"], hot_mask_mir,
    )
    assert result_mw > 0, (
        f"Cluster legítimo con overlap MIR debe dar vrp_tir>0. "
        f"Obtuvo {result_mw} MW."
    )
    # Sanity bound: 4 pixels × σ·(310^4-285^4) × A_pix
    expected = 4 * SIGMA_SB * (310**4 - 285**4) * A_PIX_VIIRS_I / 1e6
    assert abs(result_mw - expected) / expected < 0.1, (
        f"vrp_tir fuera de ±10% del valor Stefan-Boltzmann esperado "
        f"({expected:.2f} MW vs {result_mw:.2f} MW)."
    )


@pytest.mark.xfail(_GATE is None, reason="F46 fix pending A45")
def test_threshold_subido_descarta_ruido_heterogeneo(scene_uniform_bg):
    """F46-B: con TIR_floor=3 K y N_SIGMA_TIR=6, pixels ΔT=5 K no disparan."""
    scene = scene_uniform_bg
    # 50 pixels a 290 K (ΔT=5 K). Con σ=2, pre-fix threshold=max(0.5,8)=8K → ya
    # los descartaba. Pero con σ=1.0 (escena más limpia), pre-fix threshold=4K
    # → 5K ΔT SÍ dispara. Post-fix threshold=max(3, 6×1)=6K → NO dispara.
    scene["std_bg5"] = 1.0
    scene["bt5"][2:7, 2:7] = 290.0  # 25 pixels @ ΔT=5K
    # MIR con algunos pixels solapados — no por eso debe pasar el gate de threshold
    hot_mask_mir = np.zeros((8, 8), dtype=bool)
    hot_mask_mir[3:5, 3:5] = True

    result_mw = _GATE(
        scene["bt5"], scene["roi_mask"], scene["pixel_areas"],
        scene["t_bg_i05"], scene["std_bg5"], hot_mask_mir,
    )
    assert result_mw == 0.0, (
        f"Threshold post-fix (max(3K, 6σ)) debe filtrar ΔT=5K con σ=1K. "
        f"Obtuvo {result_mw} MW."
    )


@pytest.mark.xfail(_GATE is None, reason="F46 fix pending A45")
def test_anomalia_real_fuerte_pasa(scene_uniform_bg):
    """F46: anomalía ΔT=20 K con σ=2 K SÍ dispara post-fix."""
    scene = scene_uniform_bg
    scene["bt5"][3:5, 3:5] = 305.0  # 4 pixels a 305 K, ΔT=20 K
    hot_mask_mir = np.zeros((8, 8), dtype=bool)
    hot_mask_mir[3:5, 3:5] = True

    result_mw = _GATE(
        scene["bt5"], scene["roi_mask"], scene["pixel_areas"],
        scene["t_bg_i05"], scene["std_bg5"], hot_mask_mir,
    )
    assert result_mw > 0, (
        f"Anomalía real ΔT=20K debe pasar post-fix. Obtuvo {result_mw} MW."
    )


@pytest.mark.xfail(_GATE is None, reason="F46 fix pending A45")
def test_mir_lejos_de_tir_no_rescata(scene_uniform_bg):
    """F46-A: si MIR/NTI detectó pero NO solapa con hot_tir, gate veta.

    Caso edge: MIR detectó otra región del scene (otro hotspot lejano).
    El TIR debe contabilizar solo si hay coherencia espacial.
    """
    scene = scene_uniform_bg
    scene["bt5"][1:3, 1:3] = 295.0  # hot_tir top-left
    hot_mask_mir = np.zeros((8, 8), dtype=bool)
    hot_mask_mir[6:8, 6:8] = True   # MIR bottom-right (lejano)

    result_mw = _GATE(
        scene["bt5"], scene["roi_mask"], scene["pixel_areas"],
        scene["t_bg_i05"], scene["std_bg5"], hot_mask_mir,
    )
    assert result_mw == 0.0, (
        f"hot_tir sin solapamiento espacial con hot_mir debe dar 0. "
        f"Obtuvo {result_mw} MW."
    )
