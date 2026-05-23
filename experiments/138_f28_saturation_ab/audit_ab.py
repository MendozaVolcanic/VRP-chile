"""F2.8.f A/B audit — compare PP records before/after saturation guard fix.

Usage:
    python experiments/138_f28_saturation_ab/audit_ab.py <profile> <before_path>

Args:
    profile: e.g. "mirova_equivalent" — where the current (post-reproc) JSON lives.
    before_path: path to snapshot saved pre-reproc (e.g.
        experiments/138_f28_saturation_ab/PlanchonPeteroa.before_f28.json).

Output: prints A/B comparison to stdout. Exits 1 if fossils > 50K MW survive.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def stats(recs, label):
    foss = [r for r in recs if (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 50000]
    pc_vals = [(r.get("primary_cluster") or {}).get("vrp_mw", 0) for r in recs]
    pc_max = max(pc_vals) if pc_vals else 0
    targets = [r for r in recs if str(r.get("datetime_utc", "")).startswith("2026-03-18")]
    print(f"{label}: total={len(recs)}, fossils>50K={len(foss)}, pc_max={pc_max:,.2f}")
    print(f"  2026-03-18 records: {len(targets)}")
    for t in targets:
        pc = t.get("primary_cluster") or {}
        print(
            f"    {t.get('datetime_utc')} {t.get('sensor'):25s} "
            f"vrp_mw={t.get('vrp_mw', 0):8.2f} pc.vrp_mw={pc.get('vrp_mw', 0):10.2f} "
            f"n_anom={t.get('n_anomalous_pixels', 0):4d} dist_class={t.get('distance_class', '')}"
        )
    print()


def main(argv):
    if len(argv) < 3:
        print("Usage: audit_ab.py <profile> <before_path>", file=sys.stderr)
        return 1
    profile = argv[1]
    before_path = Path(argv[2])
    after_path = Path(f"data/{profile}/PlanchonPeteroa.json")

    if not before_path.exists():
        print(f"WARN: before snapshot not found at {before_path}, skipping A/B comparison")
        if after_path.exists():
            after = json.loads(after_path.read_text(encoding="utf-8")).get("records", [])
            stats(after, "AFTER  (post-F2.8 fix, no before snapshot)")
        return 0

    before = json.loads(before_path.read_text(encoding="utf-8")).get("records", [])
    after = json.loads(after_path.read_text(encoding="utf-8")).get("records", [])

    stats(before, "BEFORE (pre-F2.8 fix)")
    stats(after, "AFTER  (post-F2.8 fix)")

    after_foss = [r for r in after if (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 50000]
    if after_foss:
        print(f"FAIL: still {len(after_foss)} fossils > 50K MW")
        return 1
    print("PASS: 0 fossils > 50K MW after fix")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
