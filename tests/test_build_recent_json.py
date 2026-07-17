"""Tests para scripts/build_recent_json.py (fix dashboard liviano S120)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_recent_json import filter_recent, parse_dt  # noqa: E402


def test_parse_dt_formats():
    assert parse_dt("2026-07-15 06:30") == datetime(2026, 7, 15, 6, 30, tzinfo=timezone.utc)
    assert parse_dt("2026-07-15T06:30") == datetime(2026, 7, 15, 6, 30, tzinfo=timezone.utc)
    assert parse_dt("2026-07-15") == datetime(2026, 7, 15, 0, 0, tzinfo=timezone.utc)
    assert parse_dt("") is None
    assert parse_dt("garbage") is None


def test_filter_recent_keeps_only_recent_and_metadata():
    cutoff = datetime(2026, 4, 7, tzinfo=timezone.utc)  # 100 días antes de 2026-07-16
    doc = {
        "updated": "2026-07-16T00:00",
        "records": [
            {"datetime_utc": "2026-07-15 06:30", "vrp_mw": 1.0},  # dentro
            {"datetime_utc": "2026-05-01 00:00", "vrp_mw": 2.0},  # dentro
            {"datetime_utc": "2025-09-15 00:00", "vrp_mw": 3.0},  # fuera (backfill)
            {"datetime_utc": "", "vrp_mw": 9.0},                  # sin fecha → fuera
        ],
    }
    out = filter_recent(doc, cutoff)
    assert len(out["records"]) == 2
    assert {r["vrp_mw"] for r in out["records"]} == {1.0, 2.0}
    assert out["updated"] == "2026-07-16T00:00"  # metadata conservada
    assert out["_recent_window_days"] == 100
    # el doc original NO se muta
    assert len(doc["records"]) == 4


def test_filter_recent_list_form():
    cutoff = datetime(2026, 4, 7, tzinfo=timezone.utc)
    doc = [{"datetime_utc": "2026-07-15 06:30"}, {"datetime_utc": "2024-01-01 00:00"}]
    out = filter_recent(doc, cutoff)
    assert len(out["records"]) == 1
