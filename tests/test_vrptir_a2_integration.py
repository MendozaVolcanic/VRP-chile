"""F31 Task A2 — VRPTIR Aveni 2025 GRL diagnostic-only integration en process_viirs.

Testea la helper `_compute_vrptir_aveni_diagnostic` que se invoca dentro del
bloque I05 de pipeline.process_viirs.calculate_vrp() y agrega 3 campos al
record cuando ENABLE_VRPTIR_AVENI=True:

- vrptir_aveni_mw       : VRP_TIR per Aveni 2025 GRL Eq.9 sobre pixels hot
                          ya detectados por nuestro pipeline TIR (proxy
                          TIRVolcH, S76 piloto).
- vrptir_aveni_n_pixels : pixels efectivamente usados (subset hot ∩ 300-600 K).
- vrptir_aveni_caveat   : etiqueta corta describiendo el caveat A35.

Pre-condiciones del experimento:
- Flag OFF (default mirova_equivalent operacional) → helper devuelve None,
  el record no recibe los campos. Backward-compat estricto.
- Flag ON (experimental_lowT) + pixels in-range → dict con los 3 keys.
- Flag ON + todos los pixels fuera de rango (≤300 K o >600 K) → MW=0, n=0
  (campo presente pero numericamente nulo).

NO testea integración end-to-end con archivos L1B reales (eso requiere
fixtures HDF5 — fuera de scope bite-sized A2). Testea la helper directo
con arrays sintéticos.

Refs:
- pipeline/vrptir.py (Eq.8/Eq.9 verbatim Aveni 2025 GRL, PR #156)
- docs/F31_AVENI_GRL_2025_EXTRACT.md
- tasks/BLOQUE_ARRANQUE_S76.md §2 P1
"""

from __future__ import annotations

import os
import numpy as np
import pytest


# El helper vive en process_viirs.py — import diferido a cada test para que
# los monkeypatches sobre pipeline.profile surtan efecto antes del import.
def _reload_with_flag(monkeypatch, enable_vrptir):
    """Re-importa pipeline.profile y pipeline.process_viirs con flag toggled."""
    import importlib
    import pipeline.profile as prof_mod
    import pipeline.process_viirs as pv_mod
    monkeypatch.setattr(prof_mod, "ENABLE_VRPTIR_AVENI", bool(enable_vrptir))
    monkeypatch.setattr(pv_mod, "ENABLE_VRPTIR_AVENI", bool(enable_vrptir), raising=False)
    return pv_mod


def test_flag_off_returns_none(monkeypatch):
    """Default operacional: ENABLE_VRPTIR_AVENI=False → helper devuelve None."""
    pv = _reload_with_flag(monkeypatch, enable_vrptir=False)
    bt5 = np.full((4, 4), 280.0)
    bt5[1, 1] = 400.0
    bt5[2, 2] = 410.0
    hot_mask = np.zeros_like(bt5, dtype=bool)
    hot_mask[1, 1] = True
    hot_mask[2, 2] = True
    t_bg = 280.0

    result = pv._compute_vrptir_aveni_diagnostic(bt5, hot_mask, t_bg)
    assert result is None, "Con flag OFF la helper no debe ejecutar Aveni"


def test_flag_on_pixels_in_range_returns_dict(monkeypatch):
    """Flag ON + 2 pixels a 400/410 K sobre BG 280 K → dict con MW > 0."""
    pv = _reload_with_flag(monkeypatch, enable_vrptir=True)
    bt5 = np.full((4, 4), 280.0)
    bt5[1, 1] = 400.0
    bt5[2, 2] = 410.0
    hot_mask = np.zeros_like(bt5, dtype=bool)
    hot_mask[1, 1] = True
    hot_mask[2, 2] = True
    t_bg = 280.0

    result = pv._compute_vrptir_aveni_diagnostic(bt5, hot_mask, t_bg)
    assert result is not None
    assert set(result.keys()) == {
        "vrptir_aveni_mw", "vrptir_aveni_n_pixels", "vrptir_aveni_caveat"
    }
    assert result["vrptir_aveni_n_pixels"] == 2
    assert result["vrptir_aveni_mw"] > 0.0
    # Sanity: VIIRS-like lava lake 2px @ 400-410 K cae en O(0.1-100 MW)
    assert 0.001 < result["vrptir_aveni_mw"] < 10000.0
    assert isinstance(result["vrptir_aveni_caveat"], str)
    assert len(result["vrptir_aveni_caveat"]) > 0


def test_flag_on_pixels_out_of_range_returns_zero(monkeypatch):
    """Flag ON pero todos los pixels < 300 K (sub-rango Aveni) → MW=0 n=0."""
    pv = _reload_with_flag(monkeypatch, enable_vrptir=True)
    bt5 = np.full((4, 4), 270.0)
    bt5[1, 1] = 285.0  # bajo 300K — fuera de rango Aveni
    bt5[2, 2] = 290.0
    hot_mask = np.zeros_like(bt5, dtype=bool)
    hot_mask[1, 1] = True
    hot_mask[2, 2] = True
    t_bg = 265.0

    result = pv._compute_vrptir_aveni_diagnostic(bt5, hot_mask, t_bg)
    assert result is not None, "Flag ON → helper debe devolver dict aunque MW=0"
    assert result["vrptir_aveni_n_pixels"] == 0
    assert result["vrptir_aveni_mw"] == 0.0


def test_flag_on_no_hot_pixels_returns_zero(monkeypatch):
    """Flag ON pero hot_mask vacío (sin detecciones) → MW=0 n=0."""
    pv = _reload_with_flag(monkeypatch, enable_vrptir=True)
    bt5 = np.full((4, 4), 280.0)
    hot_mask = np.zeros_like(bt5, dtype=bool)
    t_bg = 280.0

    result = pv._compute_vrptir_aveni_diagnostic(bt5, hot_mask, t_bg)
    assert result is not None
    assert result["vrptir_aveni_n_pixels"] == 0
    assert result["vrptir_aveni_mw"] == 0.0
