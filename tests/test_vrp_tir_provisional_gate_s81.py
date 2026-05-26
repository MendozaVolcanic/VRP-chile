"""F46 provisional gate S81 (A45 Nicolás) — test sintético.

Valida que `_compute_vrp_tir_with_gate(enable_output=False)` retorna 0.0
incondicionalmente, sin importar inputs.

Contexto: la auditoría S81 frente #3 detectó 726 records con
vrp_tir_mw/vrp_mir_mw > 1000× post-S77 gate Opción A+B. Mientras F46
(Coppola 2024 Eq.16 con background subtraction + unmixing A_hot) no esté
implementado, gate provisional silencia el campo.

Ver:
- docs/F46_VRP_TIR_GATE_S81.md — mitigación
- docs/F46_VRP_TIR_BUG_S76.md — plan completo
- pipeline/process_viirs.py:_compute_vrp_tir_with_gate
"""
from __future__ import annotations

import numpy as np
import pytest

from pipeline.process_viirs import _compute_vrp_tir_with_gate


def _setup_inflated_scene():
    """Escena sintética que SIN gate produce vrp_tir inflado.

    Pixel hot a 320 K, background 280 K, std_bg 5 K. ΔT=40K, hot_area=140625 m².
    Stefan-Boltzmann naive da ~5500 W/pixel → ~5.5 MW si pasara unmasked.
    Con varios pixels hot el total escala.
    """
    bt5 = np.full((10, 10), 280.0)
    bt5[4:7, 4:7] = 320.0  # 9 pixels hot 40 K sobre bg
    roi_mask = np.ones_like(bt5, dtype=bool)
    pixel_areas = np.full_like(bt5, 140625.0)
    hot_mask_mir = np.zeros_like(bt5, dtype=bool)
    hot_mask_mir[4:7, 4:7] = True  # MIR detecta los mismos pixels
    return {
        "bt5": bt5,
        "roi_mask": roi_mask,
        "pixel_areas": pixel_areas,
        "t_bg_i05": 280.0,
        "std_bg5": 5.0,
        "hot_mask_mir": hot_mask_mir,
    }


def test_enable_output_false_returns_zero_even_with_inflated_scene():
    """Con enable_output=False → 0.0 sin ejecutar gate ni Stefan-Boltzmann."""
    inputs = _setup_inflated_scene()
    vrp = _compute_vrp_tir_with_gate(
        **inputs,
        enable_output=False,
    )
    assert vrp == 0.0


def test_enable_output_false_overrides_enable_gate_false():
    """Aunque enable_gate=False (modo legacy), enable_output=False gana."""
    inputs = _setup_inflated_scene()
    vrp = _compute_vrp_tir_with_gate(
        **inputs,
        enable_gate=False,  # legacy mode = sin gate de consistencia
        enable_output=False,  # PERO output silenciado
    )
    assert vrp == 0.0


def test_enable_output_true_default_passes_gate_normal():
    """Con enable_output=True (default), el gate F46 S77 sigue actuando normal."""
    inputs = _setup_inflated_scene()
    vrp = _compute_vrp_tir_with_gate(
        **inputs,
        enable_output=True,
    )
    # Con MIR coincidente y ΔT=40K, el gate F46 deja pasar → vrp > 0
    assert vrp > 0.0


def test_enable_output_default_value_is_true():
    """Default debe ser True (legacy behavior si profile no setea flag)."""
    inputs = _setup_inflated_scene()
    # Llamada sin parámetro enable_output explícito.
    vrp = _compute_vrp_tir_with_gate(**inputs)
    assert vrp > 0.0  # default True permite cómputo


def test_profile_constant_imported_correctly():
    """Sanity: ENABLE_VRP_TIR_OUTPUT existe en profile.py y es bool."""
    from pipeline.profile import ENABLE_VRP_TIR_OUTPUT
    assert isinstance(ENABLE_VRP_TIR_OUTPUT, bool)


def test_mirova_equivalent_profile_silences_output():
    """mirova_equivalent.yaml setea enable_vrp_tir_output=false."""
    import yaml
    from pathlib import Path
    repo_root = Path(__file__).parent.parent
    profile_path = repo_root / "pipeline" / "profiles" / "mirova_equivalent.yaml"
    cfg = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert cfg.get("enable_vrp_tir_output") is False, (
        "mirova_equivalent.yaml debe setear enable_vrp_tir_output=false "
        "como gate provisional F46 (S81). Si fue subido a true, "
        "verificar que el fix F46 completo (Coppola 2024 Eq.16) esté implementado."
    )
