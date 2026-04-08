"""
rebuild_mirova_lascar.py — Regenerate data/mirova/Lascar.json from the
authoritative source CSV at:

    Automatizacion web/Mirova-v1/monitoreo_satelital/registro_vrp_consolidado.csv

This script intentionally uses ONLY the consolidated CSV (text-scraped from
mirovaweb.it). It IGNORES the OCR CSV because OCR truncates decimal values
(verified: VRP=3.43 -> OCR reads 3.0, VRP=2.28 -> OCR reads 2.0). The OCR
data is only reliable for "presence/absence" of an event, not for VRP_MW.

Output schema (matches existing format consumed by frontend/index.html and
scripts/validate_lascar_vs_mirova.py):

    {
      "volcano": "Lascar",
      "source": "registro_vrp_consolidado.csv (text-scraped MIROVA)",
      "generated_at": "<ISO timestamp>",
      "records": [
        {
          "datetime_utc": "YYYY-MM-DD HH:MM",
          "sensor": "MODIS|VIIRS375|VIIRS",
          "VRP_MW": float,
          "distancia_km": float,
          "clasificacion": "<MIROVA class>",
          "source": "consolidado"
        }
      ]
    }

Filters applied:
  - Volcan == "Lascar"
  - VRP_MW > 0 (drop NULO/zero rows — they mean "satellite passed but
    detected nothing", which is not a calibration reference)

Dedup: by (datetime_utc, sensor). If duplicates exist, keep the highest VRP.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
SOURCE = Path(
    r"C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Mirova-v1\monitoreo_satelital\registro_vrp_consolidado.csv"
)
DEST = REPO / "data" / "mirova" / "Lascar.json"


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source CSV not found: {SOURCE}")

    with open(SOURCE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows in source CSV: {len(rows)}")

    lascar = [r for r in rows if r.get("Volcan") == "Lascar"]
    print(f"Lascar rows: {len(lascar)}")

    nonzero = []
    for r in lascar:
        try:
            vrp = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if vrp <= 0:
            continue
        # Normalize datetime to "YYYY-MM-DD HH:MM"
        dt_raw = (r.get("Fecha_Satelite_UTC") or "").strip()
        if not dt_raw:
            continue
        try:
            dt = datetime.strptime(dt_raw[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(dt_raw[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                print(f"  WARN: bad datetime '{dt_raw}', skipping")
                continue
        dt_str = dt.strftime("%Y-%m-%d %H:%M")
        sensor = (r.get("Sensor") or "").strip()
        try:
            dist = float(r.get("Distancia_km") or 0)
        except ValueError:
            dist = 0.0
        nonzero.append({
            "datetime_utc": dt_str,
            "sensor": sensor,
            "VRP_MW": round(vrp, 3),
            "distancia_km": round(dist, 2),
            "clasificacion": (r.get("Clasificacion Mirova") or "").strip(),
            "source": "consolidado",
        })

    print(f"Lascar rows with VRP > 0: {len(nonzero)}")

    # Dedupe by (datetime_utc, sensor) — keep max VRP
    by_key = {}
    for rec in nonzero:
        key = (rec["datetime_utc"], rec["sensor"])
        if key not in by_key or rec["VRP_MW"] > by_key[key]["VRP_MW"]:
            by_key[key] = rec

    deduped = sorted(by_key.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
    print(f"After dedup by (datetime, sensor): {len(deduped)}")

    # Sensor breakdown
    from collections import Counter
    sensors = Counter(r["sensor"] for r in deduped)
    print(f"Sensors: {dict(sensors)}")
    dates = [r["datetime_utc"] for r in deduped]
    if dates:
        print(f"Range: {dates[0]} -> {dates[-1]}")

    output = {
        "volcano": "Lascar",
        "source": "registro_vrp_consolidado.csv (text-scraped from mirovaweb.it)",
        "note": "OCR-derived records intentionally excluded (decimals truncated by OCR). Only text-scraped values used for quantitative calibration.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records": deduped,
    }

    DEST.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nWrote: {DEST}")


if __name__ == "__main__":
    main()
