"""compact_anomaly_pixels.py — S26 utility para reducir bloat JSON.

Aplica el cap top-100 retroactivamente a records existentes con anomaly_pixels
listas largas. Necesario por GitHub 100MB file size limit que rompió el push
de Lascar feb-abr (117 MB).

Uso:
    python scripts/compact_anomaly_pixels.py --dry-run   # solo reporta
    python scripts/compact_anomaly_pixels.py             # aplica in-place

Idempotente: si record ya tiene <=100 pixels, no se modifica.
Mantiene records ordenados por timestamp.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

DATA_DIRS = [
    Path("data/mirova_equivalent"),
    Path("data/experimental"),
    Path("data/_test1_enabled"),
    Path("data/_test1_disabled"),
    Path("data/_p3_1_enabled"),
    Path("data/_p3_1_disabled"),
]
CAP = 100


def compact_file(path: Path, dry_run: bool) -> dict:
    """Compact one JSON file. Returns stats dict."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("records", []) if isinstance(raw, dict) else raw

    size_before = path.stat().st_size
    records_modified = 0
    pixels_removed = 0

    for r in records:
        ap = r.get("anomaly_pixels", [])
        if len(ap) > CAP:
            # Pixels ya están sorted by VRP descending (built in process_*.py)
            # pero verificamos por las dudas
            ap_sorted = sorted(ap, key=lambda p: -(p.get("vrp_mw", 0) or 0))
            r["anomaly_pixels"] = ap_sorted[:CAP]
            pixels_removed += len(ap) - CAP
            records_modified += 1

    if records_modified > 0 and not dry_run:
        if isinstance(raw, dict):
            raw["records"] = records
            path.write_text(json.dumps(raw, indent=2, default=str), encoding="utf-8")
        else:
            path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    size_after = path.stat().st_size if not dry_run else size_before

    return {
        "path": str(path),
        "size_before_mb": size_before / 1e6,
        "size_after_mb": size_after / 1e6,
        "n_records": len(records),
        "records_modified": records_modified,
        "pixels_removed": pixels_removed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Solo reporta, no modifica.")
    args = ap.parse_args()

    print(f"# Compact anomaly_pixels (cap={CAP}) {'[DRY RUN]' if args.dry_run else ''}")
    print()
    print(f"{'file':<50} {'before':>10} {'after':>10} {'records':>8} {'modif':>6} {'pix_rm':>10}")
    total_before = 0
    total_after = 0
    total_pix_removed = 0
    for d in DATA_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.glob("*.json")):
            stats = compact_file(p, args.dry_run)
            print(f"{stats['path']:<50} {stats['size_before_mb']:>10.2f} "
                  f"{stats['size_after_mb']:>10.2f} {stats['n_records']:>8} "
                  f"{stats['records_modified']:>6} {stats['pixels_removed']:>10}")
            total_before += stats["size_before_mb"]
            total_after += stats["size_after_mb"]
            total_pix_removed += stats["pixels_removed"]

    print()
    print(f"# Total before: {total_before:.1f} MB")
    print(f"# Total after:  {total_after:.1f} MB")
    print(f"# Pixels removed: {total_pix_removed}")
    if args.dry_run:
        print()
        print("# DRY RUN — re-correr sin --dry-run para aplicar.")


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
