"""S99 DF-1 — TDD wiring de compute_vrp_lava_lake_eq16 al pipeline (4º candidato A/B).

El método Eq.16 (Coppola 2024, lava lake sub-píxel) estaba construido + testeado
(test_vrp_regimes_lava_lake.py) pero NUNCA conectado (hallazgo dormido S99). Acá lo
conectamos detrás de `enable_test1_lava_lake_eq16` (default OFF), gateado per-vol por
`lava_lake_magmatic` (Villarrica). Cuando la fuente es Test 1, recomputa pc.vrp_mw
desde el píxel pico vía Eq.15+16 en vez de la suma Wooster (fuera de rango sub-píxel).

Estos tests validan el cableado de flags/params; el comportamiento físico de la
función ya está cubierto por test_vrp_regimes_lava_lake.py, y la magnitud real se
valida con el A/B (A18).
"""
from __future__ import annotations

import importlib
import pytest


def test_flag_default_off(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_LAVA_LAKE_EQ16 is False
    assert profile.TEST1_LAVA_LAKE_TE_K == pytest.approx(1000.0)
    assert profile.TEST1_LAVA_LAKE_EPS == pytest.approx(0.95)


def test_flag_on_in_eq16_profile(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "_s99_test1_eq16")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_LAVA_LAKE_EQ16 is True
    assert profile.ENABLE_TEST1_PATH is True


def test_villarrica_yaml_has_lava_lake_flag():
    """El gate per-vol requiere lava_lake_magmatic: true en Villarrica."""
    import yaml
    from pathlib import Path
    vy = yaml.safe_load(open(Path(__file__).resolve().parents[1] / "volcanoes.yaml", encoding="utf-8"))
    vols = vy if isinstance(vy, list) else vy.get("volcanoes", vy)
    villa = next((v for v in vols if v.get("name") == "Villarrica"), None)
    assert villa is not None
    assert villa.get("lava_lake_magmatic") is True
    # Tupungatito NO es lava lake (cráter fumarólico) → Eq.16 no debe aplicar.
    tupun = next((v for v in vols if v.get("name") == "Tupungatito"), None)
    assert not tupun.get("lava_lake_magmatic", False)


def test_eq16_gives_sub_mw_for_villarrica_like():
    """Sanity de integración: para un pixel Villarrica-like, Eq.16 da sub-MW
    (no la magnitud Wooster inflada). Refuerza por qué el wiring vale."""
    from pipeline.test1_spatial_core import spatial_core_filter  # noqa: F401 (módulo hermano S99)
    from pipeline.vrp_regimes import compute_vrp_lava_lake_eq16
    res = compute_vrp_lava_lake_eq16(bt_hot_k=283.3, bt_bg_k=280.0, t_bk_k=280.0)
    assert 0.0 < res["vrp_mw"] < 1.0
