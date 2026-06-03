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


def test_keep_peak_rescues_embedded_crater():
    """Híbrido C+keep-peak: el cráter embebido (en test1, NO en contextual) SOBREVIVE
    si se pasa su (r,c) como peak. Es el guard anti-FN que salva al recall del veto C."""
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    test1 = np.zeros((6, 6), dtype=bool)
    test1[3, 3] = True            # cráter (pico)
    test1[3, 4] = True            # halo vecino
    dnti_ctx = np.zeros((6, 6), dtype=bool)  # nada contextualmente anómalo (embebido)
    # sin keep_peak → se cae (FN)
    out0 = apply_contextual_test1_filter(test1, dnti_ctx)
    assert int(out0.sum()) == 0
    # con keep_peak=(3,3) → el cráter sobrevive
    out1 = apply_contextual_test1_filter(test1, dnti_ctx, keep_peak_rc=(3, 3))
    assert out1[3, 3] and int(out1.sum()) == 1, "el pico debe conservarse (anti-FN)"


def test_keep_peak_plus_contextual_union():
    """keep-peak conserva el pico Y los contextualmente anómalos (unión)."""
    from pipeline.test1_contextual_filter import apply_contextual_test1_filter
    test1 = np.zeros((6, 6), dtype=bool)
    for rc in [(3, 3), (1, 1), (4, 4)]:
        test1[rc] = True
    dnti_ctx = np.zeros((6, 6), dtype=bool)
    dnti_ctx[1, 1] = True  # un vecino-anómalo aparte del pico
    out = apply_contextual_test1_filter(test1, dnti_ctx, keep_peak_rc=(3, 3))
    assert out[1, 1] and out[3, 3], "contextual ∪ pico"
    assert not out[4, 4]
    assert int(out.sum()) == 2


def test_profile_flag_keep_peak(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "_s99_test1_ctxpeak")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_CONTEXTUAL_FILTER is True
    assert profile.ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK is True


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
