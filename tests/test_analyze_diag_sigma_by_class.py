"""Invariantes script 40: análisis distribuciones diag_sigma_bg_k por clase forense."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.analyze_diag_sigma_by_class import (
    extract_sigma_by_class, summarize_distributions,
)


def _classification(cls: str, sigma: float, t_bg: float = 280.0,
                    eff_thr: float = 5.0):
    return {
        "class": cls,
        "rec": {
            "diag_sigma_bg_k": sigma,
            "t_bg_k": t_bg,
            "diag_eff_threshold_k": eff_thr,
        },
    }


def test_extract_groups_by_class():
    classifications = [
        _classification("TP", 0.5),
        _classification("TP", 0.7),
        _classification("T4", 2.5),
        _classification("T4", 2.9),
        _classification("T1", 0.0),  # T1 has no rec
    ]
    classifications[-1]["rec"] = None  # T1 = no record
    out = extract_sigma_by_class(classifications)
    assert "TP" in out
    assert "T4" in out
    assert len(out["TP"]) == 2
    assert len(out["T4"]) == 2
    assert "T1" not in out  # T1 has no rec, excluded


def test_extract_skips_missing_sigma():
    classifications = [
        {"class": "TP", "rec": {"diag_sigma_bg_k": 0.5}},
        {"class": "TP", "rec": {}},  # no sigma
    ]
    out = extract_sigma_by_class(classifications)
    assert len(out["TP"]) == 1


def test_summarize_returns_stats_per_class():
    sigmas = {
        "TP": [0.4, 0.5, 0.6, 0.7, 0.8],
        "T4": [2.0, 2.5, 3.0, 3.5, 4.0],
    }
    summary = summarize_distributions(sigmas)
    assert "TP" in summary
    assert "T4" in summary
    assert summary["TP"]["median"] == 0.6
    assert summary["T4"]["median"] == 3.0
    assert summary["T4"]["median"] > summary["TP"]["median"]
    assert summary["TP"]["n"] == 5


def test_summarize_handles_empty():
    summary = summarize_distributions({"TP": []})
    assert summary["TP"]["n"] == 0
    assert np.isnan(summary["TP"]["median"])
