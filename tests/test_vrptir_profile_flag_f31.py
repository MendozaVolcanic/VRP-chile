"""Tests F31 Task A3 — profile flag enable_vrptir_aveni + experimental_lowT.yaml.

Verifica que el flag opt-in se lee correctamente desde el perfil y que las
constantes VRPTIR coinciden con valores verbatim Aveni 2025 GRL (A35 verified).

Refs:
- pipeline/profile.py (ENABLE_VRPTIR_AVENI + constants)
- pipeline/profiles/experimental_lowT.yaml (extends mirova_equivalent)
- docs/F31_AVENI_GRL_2025_EXTRACT.md (Eq.8 verbatim)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def _load_profile_module(profile_name: str):
    """Set env VRP_PROFILE + reload pipeline.profile fresh in subprocess."""
    env = os.environ.copy()
    env["VRP_PROFILE"] = profile_name
    code = (
        "import pipeline.profile as p; "
        "import json; "
        "print(json.dumps({"
        "'ENABLE_VRPTIR_AVENI': p.ENABLE_VRPTIR_AVENI, "
        "'VRPTIR_T_MIN_K': p.VRPTIR_T_MIN_K, "
        "'VRPTIR_T_MAX_K': p.VRPTIR_T_MAX_K, "
        "'VRPTIR_K_TIR_I5': p.VRPTIR_K_TIR_I5, "
        "}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Profile load failed for '{profile_name}':\n{result.stderr}")
    last_line = [ln for ln in result.stdout.strip().split("\n") if ln.strip().startswith("{")][-1]
    return json.loads(last_line)


def test_mirova_equivalent_defaults_vrptir_off():
    """En mirova_equivalent (operacional), enable_vrptir_aveni debe ser False."""
    data = _load_profile_module("mirova_equivalent")
    assert data["ENABLE_VRPTIR_AVENI"] is False


def test_experimental_lowT_enables_vrptir():
    """En experimental_lowT, enable_vrptir_aveni debe ser True (via extends + override)."""
    data = _load_profile_module("experimental_lowT")
    assert data["ENABLE_VRPTIR_AVENI"] is True


def test_vrptir_thresholds_verbatim_aveni_2025():
    """Thresholds VRPTIR coinciden con valores verbatim Aveni 2025 GRL."""
    data = _load_profile_module("experimental_lowT")
    assert data["VRPTIR_T_MIN_K"] == 300.0
    assert data["VRPTIR_T_MAX_K"] == 600.0
    assert abs(data["VRPTIR_K_TIR_I5"] - 60.17) < 1e-6


def test_default_vrptir_thresholds_match_paper():
    """Aun en operacional, las constantes VRPTIR son verbatim. Solo flag cambia."""
    data = _load_profile_module("mirova_equivalent")
    assert data["VRPTIR_T_MIN_K"] == 300.0
    assert data["VRPTIR_T_MAX_K"] == 600.0
    assert abs(data["VRPTIR_K_TIR_I5"] - 60.17) < 1e-6
