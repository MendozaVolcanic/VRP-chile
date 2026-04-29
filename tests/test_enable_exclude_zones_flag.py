"""S27 T3 — TDD: flag ENABLE_EXCLUDE_ZONES desactiva filtro de exclude_zones.

Para clon literal MIROVA (Coppola 2016a + 2020 + Laiolo 2026), exclude_zones
es un parche nuestro (S16 P3.6 + S26 lagos) que NO está en papers MIROVA.
El flag ENABLE_EXCLUDE_ZONES=False desactiva el filtro sin tocar volcanoes.yaml.
"""
from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture(autouse=True)
def _restore_default_profile():
    """Después de cada test reload profile.py a mirova_equivalent.

    Sin esto, el state global de pipeline.profile queda con valores del
    último reload (ej. _mirova_literal con max_sigma=999), contaminando
    tests posteriores que asumen mirova_equivalent (test_sigma_cap_eruption).
    """
    yield
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    import pipeline.profile
    importlib.reload(pipeline.profile)


def test_profile_default_enables_exclude_zones(monkeypatch):
    """mirova_equivalent operacional mantiene exclude_zones ON (default)."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_EXCLUDE_ZONES is True


def test_profile_literal_disables_exclude_zones(monkeypatch):
    """_mirova_literal (treatment A/B) desactiva exclude_zones — parche no-paper."""
    monkeypatch.setenv("VRP_PROFILE", "_mirova_literal")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_EXCLUDE_ZONES is False


def test_guard_clears_exclude_zones_when_disabled():
    """Guard helper: cuando flag=False, exclude_zones queda en None."""
    from pipeline.exclusion_zones import guard_exclude_zones
    zones = [{"lat": -33.0, "lon": -70.0, "radius_km": 5.0}]
    wl = [{"lat": -33.1, "lon": -70.1, "radius_km": 1.0}]
    z2, w2 = guard_exclude_zones(zones, wl, enabled=False)
    assert z2 is None
    assert w2 is None


def test_guard_preserves_exclude_zones_when_enabled():
    """Guard helper: cuando flag=True, exclude_zones se preserva."""
    from pipeline.exclusion_zones import guard_exclude_zones
    zones = [{"lat": -33.0, "lon": -70.0, "radius_km": 5.0}]
    wl = [{"lat": -33.1, "lon": -70.1, "radius_km": 1.0}]
    z2, w2 = guard_exclude_zones(zones, wl, enabled=True)
    assert z2 is zones
    assert w2 is wl
