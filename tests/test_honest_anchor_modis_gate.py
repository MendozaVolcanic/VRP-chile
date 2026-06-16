"""Tests S111 D11 — gate del ancla honesta MODIS por señal-summit propia (M1).

Mecánica (design 2026-06-16-d11-ancla-modis-crater-gated): el override de POSICIÓN
del ancla honesta MODIS solo se aplica si hay ≥1 píxel del FIRST-PASS (Tests 2&3 de
Coppola, contextuales/espectrales) dentro del inner_radius_km. Excluye la recaptura
del second_pass_adjacent que el gate intra-radio S85 preserva (A55): ese cluster
near-crater es artefacto topográfico (valle tibio NdC), NO señal volcánica.

- ARTEFACTO NdC: first_pass_summit=0 → NO aplica override → queda clasificación legacy (far).
- REAL / D12 Láscar: first_pass_summit>0 → aplica override → ancla al cráter (summit).

El gate vive en una función PURA (testeable sin pyhdf/HDF). El wiring de process_modis
solo decide SI llamar resolve_honest_anchor según esta función.
"""
from pipeline.anchor import honest_anchor_applies


def test_master_off_nunca_aplica():
    # Sin el flag maestro, el ancla MODIS no se aplica jamás (gate irrelevante).
    assert honest_anchor_applies(enabled=False, first_pass_gate_enabled=True,
                                 n_first_pass_summit=57) is False
    assert honest_anchor_applies(enabled=False, first_pass_gate_enabled=False,
                                 n_first_pass_summit=0) is False


def test_gate_off_aplica_siempre_brazo_sin_gate():
    # Brazo A/B "ancla-sin-gate" (S106): override siempre que el maestro esté ON.
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=False,
                                 n_first_pass_summit=0) is True
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=False,
                                 n_first_pass_summit=57) is True


def test_gate_on_artefacto_no_aplica():
    # NdC artefacto: 0 seeds first-pass en summit (recaptura S85 pura) → NO override.
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=0) is False


def test_gate_on_real_aplica():
    # Láscar D12 / cat-b real: first-pass genuino en summit → override (ancla al cráter).
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=1) is True
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=57) is True


def test_gate_on_borde_un_pixel():
    # El umbral es estricto >0: exactamente 1 píxel first-pass summit ya habilita.
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=1) is True
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=0) is False


def test_negativos_o_none_se_tratan_como_cero():
    # Robustez: conteos inválidos no deben habilitar el override bajo gate ON.
    assert honest_anchor_applies(enabled=True, first_pass_gate_enabled=True,
                                 n_first_pass_summit=None) is False
