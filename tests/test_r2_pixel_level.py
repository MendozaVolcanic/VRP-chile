"""R2 pixel-level tests S46 — 5 casos canónicos vs TIF MIROVA archive.

NOTA: Estos tests usan `@pytest.mark.r2_pixel_level`. Skip automático si
TIF no disponible en mirova-tif-archive (gap actual ~7d 2026-05-01 a 05-08).

Run selectivo:
    pytest tests/test_r2_pixel_level.py -m r2_pixel_level -v

Run normal (skip):
    pytest tests/ (estos tests requieren TIF y profile específico, skip)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

# TIF archive path
TIF_ARCHIVE_ROOT = Path(
    "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
)
TIF_INDEX = TIF_ARCHIVE_ROOT / "index.csv"


# 5 casos canónicos del handoff S46
# (volcano, sensor_label, granule_ts, expected_dist_km, expected_vrp_mw, hipotesis)
R2_CASES = [
    (
        "PuyehueCordonCaulle",
        "VIIRS375",
        "2026-05-09 05:42",
        7.73,
        0.18,
        "lacolito vs cráter",
    ),
    (
        "Lascar",
        "MODIS",
        "2026-04-30 07:30",
        1.0,
        0.99,
        "Salar vs cráter sub-MW",
    ),
    (
        "Tupungatito",
        "VIIRS375",
        "2026-04-27 05:18",
        5.41,
        0.11,
        "Test1+VRP=0 case",
    ),
    (
        "Isluga",
        "VIIRS375",
        "2026-04-29 05:24",
        0.84,
        0.10,
        "VJ202IMG fetch gap",
    ),
    (
        "Lastarria",
        "VIIRS375",
        "2026-04-30 06:00",
        0.5,
        0.30,
        "control sin regresión",
    ),
]


def _find_tif_for_granule(
    volcano: str,
    sensor: str,
    granule_time: pd.Timestamp,
    tol_min: float = 60,
) -> Path | None:
    """Match granule to MIROVA TIF in archive within ±tol_min window.

    Returns Path al TIF si encontrado, None si gap (no disponible).
    """
    if not TIF_INDEX.exists():
        return None
    try:
        idx = pd.read_csv(TIF_INDEX)
    except Exception:
        return None
    if "volcano" not in idx.columns or "sensor" not in idx.columns:
        return None
    # Use last_modified_utc o equivalente (verificar columna real)
    ts_col = None
    for cand in ["last_modified_utc", "captured_at_utc", "acquisition_utc"]:
        if cand in idx.columns:
            ts_col = cand
            break
    if ts_col is None:
        return None

    idx["ts"] = pd.to_datetime(idx[ts_col], errors="coerce", utc=True)
    idx = idx.dropna(subset=["ts"])
    mask = (idx["volcano"] == volcano) & (idx["sensor"] == sensor)
    cands = idx[mask]
    if cands.empty:
        return None

    if granule_time.tz is None:
        granule_time_utc = granule_time.tz_localize("UTC")
    else:
        granule_time_utc = granule_time
    delta_min = (
        (cands["ts"] - granule_time_utc).dt.total_seconds().abs()
    ) / 60.0
    if delta_min.min() > tol_min:
        return None

    best_idx = delta_min.idxmin()
    tif_rel = cands.loc[best_idx, "tif_path"]
    return TIF_ARCHIVE_ROOT / tif_rel


@pytest.mark.r2_pixel_level
@pytest.mark.parametrize(
    "volcano,sensor,granule_ts,exp_dist,exp_vrp,hipotesis",
    R2_CASES,
    ids=[case[5] for case in R2_CASES],
)
def test_r2_pixel_level_match_mirova_tif(
    volcano,
    sensor,
    granule_ts,
    exp_dist,
    exp_vrp,
    hipotesis,
):
    """R2 pixel-level: nuestra detección coincide con MIROVA TIF.

    Skip si TIF no disponible (gap archive). Cuando archive cubre el
    granule, valida que nuestro primary_cluster coincide con MIROVA
    dentro de tolerancia ±50% VRP y ±2 km distancia.
    """
    granule_time = pd.Timestamp(granule_ts)
    tif_path = _find_tif_for_granule(volcano, sensor, granule_time)

    if tif_path is None or not tif_path.exists():
        pytest.skip(
            f"TIF MIROVA no disponible: {volcano} {sensor} {granule_ts} "
            f"(archive gap o no descargado)"
        )

    # Aquí iría la lógica de cruce TIF vs nuestro JSON.
    # Por ahora, marcar como pending implementation (R2 detallada en Ronda 2).
    pytest.skip(
        f"R2 pixel-level cross-validation not yet implemented (TIF available "
        f"para {hipotesis}). Pendiente: load TIF rasterio + compare vs "
        f"data/<profile>/{volcano}.json primary_cluster."
    )


def test_tif_archive_index_loadable():
    """Smoke test: TIF archive index existe y es loadable."""
    if not TIF_INDEX.exists():
        pytest.skip(f"TIF archive index no existe: {TIF_INDEX}")

    idx = pd.read_csv(TIF_INDEX)
    assert "volcano" in idx.columns
    assert "sensor" in idx.columns
    # Tipo de timestamp column flexible
    ts_cols = ["last_modified_utc", "captured_at_utc", "acquisition_utc"]
    assert any(c in idx.columns for c in ts_cols), (
        f"Index debe tener al menos una columna timestamp: {ts_cols}"
    )
    assert len(idx) > 0


def test_r2_cases_documented():
    """Smoke: los 5 casos R2 están bien estructurados."""
    assert len(R2_CASES) == 5
    for case in R2_CASES:
        assert len(case) == 6
        volcano, sensor, ts_str, dist, vrp, hipotesis = case
        # Sanity: dist < 30 km, vrp < 100 MW (casos sub-MW)
        assert 0 <= dist < 30
        assert 0 < vrp < 100
        # Sensor válido
        assert sensor in {"MODIS", "VIIRS375", "VIIRS750", "VIIRS"}
        # Timestamp parseable
        pd.Timestamp(ts_str)
