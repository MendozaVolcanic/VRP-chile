"""F49/S77 — CI freshness test para latest_consolidado.csv.

Si la max fecha del CSV es >48h vieja, falla → CI rojo, alerta automática.
Detecta cualquier futura caída del sync auto sin esperar a que un humano
abra el dashboard.

Si el test falla en CI:
- Verificar workflow `.github/workflows/sync-mirova-csv.yml` runs en GH Actions
- Verificar que Mirova-v1 sigue corriendo (gh run list -R MendozaVolcanic/Mirova-v1)
- Sync manual de emergencia:
    curl -sL https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv -o latest_consolidado.csv
    git add latest_consolidado.csv && git commit -m "data(mirova): emergency sync" && git push

Threshold 48h elegido como banda razonable:
- Sync cron cada 1h (workflow sync-mirova-csv.yml).
- MIROVA NRT mismo tiene ~3h latencia.
- 48h da margen para fines de semana / GH Actions outages cortos sin
  alertar falso-positivo.

Refs:
- docs/F49_SCRAPER_MIROVA_DOWN_S77.md
- .github/workflows/sync-mirova-csv.yml
- frontend/index.html renderMirovaFreshness (banner 14d threshold)
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest


CSV_PATH = Path(__file__).parent.parent / "latest_consolidado.csv"
MAX_AGE_HOURS = 48


def _latest_date_in_csv(path: Path) -> datetime | None:
    """Devuelve la max fecha Fecha_Satelite_UTC del CSV, o None si vacío."""
    if not path.exists():
        return None
    latest: datetime | None = None
    with path.open("r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            s = (row.get("Fecha_Satelite_UTC") or "").strip()
            if not s:
                continue
            try:
                # Schema: "2026-05-24 18:24:02"
                dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            dt = dt.replace(tzinfo=timezone.utc)
            if latest is None or dt > latest:
                latest = dt
    return latest


def test_csv_exists():
    assert CSV_PATH.exists(), (
        f"latest_consolidado.csv no encontrado en {CSV_PATH}. "
        "Si fue movido, actualizar este test + workflow sync-mirova-csv.yml."
    )


def test_csv_has_rows():
    rows = 0
    with CSV_PATH.open("r", encoding="utf-8") as fp:
        for _ in csv.DictReader(fp):
            rows += 1
            if rows >= 10:
                break
    assert rows > 0, "CSV vacío (0 filas después del header)."


@pytest.mark.skipif(
    os.environ.get("SKIP_FRESHNESS_TEST") == "1",
    reason="Skipped por env var SKIP_FRESHNESS_TEST=1 (e.g. reproc histórico local)",
)
def test_csv_max_age_under_48h():
    latest = _latest_date_in_csv(CSV_PATH)
    assert latest is not None, "CSV sin fechas válidas en columna Fecha_Satelite_UTC."

    now = datetime.now(timezone.utc)
    age = now - latest
    assert age < timedelta(hours=MAX_AGE_HOURS), (
        f"latest_consolidado.csv stale: max date = {latest.isoformat()}, "
        f"age = {age}. Threshold = {MAX_AGE_HOURS}h.\n"
        f"Probable causa: workflow .github/workflows/sync-mirova-csv.yml "
        f"caído o Mirova-v1 upstream caído. Ver docs/F49_SCRAPER_MIROVA_DOWN_S77.md "
        f"para fix manual de emergencia."
    )
