"""S99 Candidato C — TDD filtro contextual del path Test 1 (la vía MÁS fiel a MIROVA).

Fenómeno: el Test 1 integrado marca todo píxel sobre la mediana del anillo regional
(1-3 km). Sobre el glaciar nevado, ese fondo está sesgado frío por la nieve → cada
parche de roca tibia del mosaico aparece "anómalo" → halo inflado. MIROVA, en cambio,
marca por criterio CONTEXTUAL (Tests 2/3, SP426.5): un píxel es anómalo si supera a sus
8 VECINOS inmediatos. La roca tibia rodeada de roca tibia NO es contextualmente anómala
→ MIROVA la ignora. `apply_contextual_test1_filter` intersecta los píxeles del Test 1
con la máscara contextual dNTI (dnti_ctx_hot) → solo sobreviven los anómalos vs vecinos.

RIESGO (a medir en A/B, NO ocultar): si el cráter está EMBEBIDO en la roca tibia (sus
vecinos son tibios), su dNTI también es bajo → se cae → FALSO NEGATIVO. Por eso este
candidato se prueba en su forma PURA (sin keep-peak) — para que el canario revele si el
mecanismo fiel preserva el recall o no.

Función pura, sin I/O. Flag `enable_test1_contextual_filter`, default OFF.
"""
from __future__ import annotations

import importlib
import numpy as np
import pytest


def test_drops_halo_keeps_contextual_anomaly():
    """test1 marca 10 px (1 cráter anómalo vs vecinos + 9 halo no-anómalos).
    La máscara contextual solo tiene el cráter → intersección deja solo el cráter."""
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    test1 = np.zeros((10, 10), dtype=bool)
    halo = [(2, 2), (2, 3), (3, 2), (3, 3), (6, 6), (6, 7), (7, 6), (7, 7), (5, 1)]
    crater = (5, 5)
    for r, c in halo + [crater]:
        test1[r, c] = True
    dnti_ctx = np.zeros((10, 10), dtype=bool)
    dnti_ctx[crater] = True  # solo el cráter es anómalo vs sus vecinos
    out = apply_contextual_test1_filter(test1, dnti_ctx)
    assert out[crater], "el cráter (contextualmente anómalo) debe conservarse"
    assert int(out.sum()) == 1, "el halo no-contextual debe caer"
    assert not out[2, 2]


def test_embedded_crater_dropped_is_FN_risk():
    """Caso del RIESGO: el cráter está en test1 pero NO en la máscara contextual
    (embebido en roca tibia → no anómalo vs vecinos) → se cae. El filtro PURO NO lo
    rescata; el A/B/canario debe revelar esto. Documenta el trade-off, no lo oculta."""
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    test1 = np.zeros((6, 6), dtype=bool)
    test1[3, 3] = True  # único foco
    dnti_ctx = np.zeros((6, 6), dtype=bool)  # contextual vacío (embebido)
    out = apply_contextual_test1_filter(test1, dnti_ctx)
    assert int(out.sum()) == 0, "cráter embebido sin señal contextual → cae (FN, esperado)"


def test_none_contextual_is_passthrough():
    """Si la máscara contextual no está disponible (None), NO filtrar (passthrough);
    el caller decide. Defensa contra paths sin dNTI contextual."""
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    test1 = np.zeros((4, 4), dtype=bool)
    test1[1, 1] = True
    out = apply_contextual_test1_filter(test1, None)
    assert np.array_equal(out, test1)


def test_profile_flag_default_off(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_CONTEXTUAL_FILTER is False


def test_profile_flag_on_in_ctx_profile(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "_s99_test1_ctx")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_CONTEXTUAL_FILTER is True
    assert profile.ENABLE_TEST1_PATH is True
    assert profile.ENABLE_DNTI_CONTEXTUAL_PATH is True
