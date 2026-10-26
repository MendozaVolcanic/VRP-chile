"""clean_feb_p32_only_artifacts.py — Limpieza quirurgica dashboard S15.

Los records de Feb 2026 reprocesados durante el overnight P3.2 (sin dual-ROI)
contaminan el dashboard con VRP inflados (Lascar 158 MW a 24 km, Lastarria
76 MW a 10 km). Son pixels Lazufre/flanco NW capturados por Path D sin
scene C1 estricto.

Este script encuentra records:
  - datetime_utc.startswith('2026-02')
  - tiene campo n_dnti_ctx_path o diag_n_dnti_ctx_path
Y los DESCARTA (remueve del JSON). Cuando P3.1 reprocese esos granules
futuro, se re-escriben limpios.

Es seguro: opera sobre mirova_equivalent/ JSONs que son regenerables.
Backup automatico .cleanbackup antes de modificar.

Uso:
  python scripts/clean_feb_p32_only_artifacts.py [--dry-run]
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "mirova_equivalent"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Solo reporta cuantos records removeria, no modifica.")
    args = ap.parse_args()

    total_before = 0
    total_after = 0
    total_removed = 0
    affected_volcanoes = []

    for jf in sorted(DATA_DIR.glob("*.json")):
        try:
            d = json.load(open(jf, "r", encoding="utf-8"))
        except Exception as e:
            print(f"SKIP {jf.name}: {e}")
            continue
        recs = d.get("records", [])
        n_before = len(recs)
        # Remove Feb 2026 records that have Path D field populated
        kept = []
        removed = 0
        for r in recs:
            dt = r.get("datetime_utc", "")
            has_pd = ("n_dnti_ctx_path" in r) or ("diag_n_dnti_ctx_path" in r)
            if dt.startswith("2026-02") and has_pd:
                removed += 1
                continue
            kept.append(r)
        n_after = len(kept)
        total_before += n_before
        total_after += n_after
        total_removed += removed
        if removed > 0:
            affected_volcanoes.append((jf.name, removed))
            if not args.dry_run:
                # Backup
                backup = jf.with_suffix(".json.cleanbackup")
                shutil.copy2(jf, backup)
                # Write cleaned
                d["records"] = kept
                json.dump(d, open(jf, "w", encoding="utf-8"),
                          indent=None, separators=(",", ":"))

    print(f"{'DRY RUN:' if args.dry_run else 'APPLIED:'}")
    print(f"  Total records before: {total_before}")
    print(f"  Total records after:  {total_after}")
    print(f"  Removed: {total_removed}")
    print()
    print("Volcanes afectados:")
    for name, n in affected_volcanoes:
        print(f"  {name}: -{n} records")
    if not args.dry_run and affected_volcanoes:
        print()
        print("Backups: *.json.cleanbackup (para revertir via shutil.copy inverso).")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
