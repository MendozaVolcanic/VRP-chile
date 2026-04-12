"""
rebuild_mirova_from_consolidado.py — Regenerate any data/mirova/<Volcano>.json
from the authoritative text-scraped CSV (registro_vrp_consolidado.csv).

Generalisation of rebuild_mirova_lascar.py (kept for history). Use this for
any new volcano before trusting it as a validation reference.

Usage:
    python scripts/rebuild_mirova_from_consolidado.py <JsonName> <CsvName>
    python scripts/rebuild_mirova_from_consolidado.py PuyehueCordonCaulle "Puyehue-Cordon Caulle"
    python scripts/rebuild_mirova_from_consolidado.py Tupungatito Tupungatito

The first arg is the JSON stem used by data/mirova/<stem>.json (matching
volcanoes.yaml 'name' field). The second is the 'Volcan' value as it appears
in the CSV (which may differ: hyphens, spaces, accents).

If the destination JSON exists it is backed up to
  data/mirova/<stem>_OLD_pre_consolidado.json
before overwriting.
"""
import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).parent.parent
# Session 9 2026-04-08: swapped from the original 'registro_vrp_consolidado.csv'
# (9717 rows, range 2026-01-10 to 2026-03-28, 381 real records) to the updated
# 'registro_vrp_consolidado al 08042026.csv' (11319 rows, range 2026-01-10 to
# 2026-04-08, 445 real records). +64 real records and +11 days of coverage.
# All tiering is stable (no volcano changes tier). The old file is preserved
# on disk at the same parent directory if a historical comparison is needed.
SOURCE = Path(
    r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\10.04.2026 registro_vrp_consolidado.csv"
)


def rebuild(json_stem: str, csv_volcano: str) -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source CSV not found: {SOURCE}")

    dest = REPO / "data" / "mirova" / f"{json_stem}.json"

    with open(SOURCE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    matched = [r for r in rows if (r.get("Volcan") or "").strip() == csv_volcano]
    print(f"Total CSV rows: {len(rows)}")
    print(f"{csv_volcano}: {len(matched)}")

    # CRITICAL — see lessons L7.10 (post-mortem of session 8 contamination):
    # Filter by 'Clasificacion Mirova'. The CSV's universe of values is exactly
    # 4 categories (verified 2026-04-08 on registro_vrp_consolidado.csv):
    #     NULO            9324  — MIROVA-rejected, NOT a thermal detection
    #     Muy Bajo         263  — real detection (low activity)
    #     Bajo             118  — real detection
    #     FALSO POSITIVO    12  — MIROVA-confirmed false positive
    # Only 'Muy Bajo' and 'Bajo' are ground truth. The first version of this
    # script filtered only by VRP_MW>0, which imported all 9324 NULOs and
    # contaminated the entire Session 8 audit. This must never happen again.
    # The set is CLOSED at {'Muy Bajo', 'Bajo'} until a new category actually
    # appears in the CSV — do NOT speculatively add 'Moderado'/'Alto'/etc.,
    # silent additions hide regressions.
    VALID_CLASSES = {"Muy Bajo", "Bajo"}
    rejected_clases = Counter()
    kept = []
    for r in matched:
        try:
            vrp = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if vrp <= 0:
            continue
        clas = (r.get("Clasificacion Mirova") or "").strip()
        if clas not in VALID_CLASSES:
            rejected_clases[clas] += 1
            continue
        dt_raw = (r.get("Fecha_Satelite_UTC") or "").strip()
        if not dt_raw:
            continue
        try:
            dt = datetime.strptime(dt_raw[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(dt_raw[:16], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
        dt_str = dt.strftime("%Y-%m-%d %H:%M")
        sensor = (r.get("Sensor") or "").strip()
        try:
            dist = float(r.get("Distancia_km") or 0)
        except ValueError:
            dist = 0.0
        kept.append({
            "datetime_utc": dt_str,
            "sensor": sensor,
            "VRP_MW": round(vrp, 3),
            "distancia_km": round(dist, 2),
            "clasificacion": (r.get("Clasificacion Mirova") or "").strip(),
            "source": "consolidado",
        })

    print(f"  rejected by clasificacion: {dict(rejected_clases)}")
    print(f"  with VRP > 0 AND clasificacion in {sorted(VALID_CLASSES)}: {len(kept)}")

    # Defense in depth: hard-fail if any NULO snuck through. Impossible with
    # the filter above, but if a future edit weakens VALID_CLASSES this check
    # will catch it before it contaminates a ref file. See L7.10.
    leaked = [r for r in kept if (r.get("clasificacion") or "").strip() not in VALID_CLASSES]
    assert not leaked, f"FATAL: {len(leaked)} records leaked past clasificacion filter"

    # Dedupe (datetime, sensor) — keep max VRP
    by_key = {}
    for rec in kept:
        key = (rec["datetime_utc"], rec["sensor"])
        if key not in by_key or rec["VRP_MW"] > by_key[key]["VRP_MW"]:
            by_key[key] = rec
    deduped = sorted(by_key.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
    print(f"  after dedupe: {len(deduped)}")

    sensors = Counter(r["sensor"] for r in deduped)
    print(f"  sensors: {dict(sensors)}")
    if deduped:
        print(f"  range: {deduped[0]['datetime_utc']} -> {deduped[-1]['datetime_utc']}")

    # Backup old OCR file if present
    if dest.exists():
        backup = dest.with_name(f"{json_stem}_OLD_pre_consolidado.json")
        shutil.copy(dest, backup)
        print(f"  backed up existing to: {backup.name}")

    output = {
        "volcano": json_stem,
        "source": "registro_vrp_consolidado.csv (text-scraped from mirovaweb.it)",
        "note": "OCR-derived records intentionally excluded (decimals truncated by OCR). Only text-scraped values used for quantitative calibration.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records": deduped,
    }
    dest.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"  wrote: {dest}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json_stem", help="JSON stem (e.g. PuyehueCordonCaulle)")
    p.add_argument("csv_volcano", help="Volcano name as it appears in the CSV")
    args = p.parse_args()
    rebuild(args.json_stem, args.csv_volcano)


if __name__ == "__main__":
    main()
