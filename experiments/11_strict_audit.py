"""
11_strict_audit.py — clean-slate strict audit of our pipeline vs MIROVA
(Session 9, post NULO contamination — see lessons L7.10).

Hard rules (defense in depth against S8-style contamination):
    1. Ref MUST have source starting with 'registro_vrp_consolidado'.
    2. Every ref record MUST have clasificacion in {"Muy Bajo", "Bajo"}.
       Any other value aborts the run with a clear error pointing to L7.10.
    3. Pairing is strict 1:1 by (sensor_family, time window).
       No closest-of-day fallback.
    4. Never report a ratio without also reporting TP, FP, FN.

Usage:
    python experiments/11_strict_audit.py --volcano Lascar
    python experiments/11_strict_audit.py --tier A
    python experiments/11_strict_audit.py --all

Outputs (per run):
    experiments/audit_s9/<volcano>.json — reproducible snapshot

Sensor family mapping (ours -> ref):
    MODIS_TERRA, MODIS_AQUA                  ->  MODIS
    VIIRS_NOAA20, VIIRS_SNPP                 ->  VIIRS375  (375 m I-band)
    VIIRS_NOAA20_750, VIIRS_SNPP_750         ->  VIIRS     (750 m M-band)

Time tolerance:
    MODIS     ±60 min
    VIIRS375  ±30 min
    VIIRS     ±30 min
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median, quantiles

REPO = Path(__file__).parent.parent
DATA_DIR = REPO / "data"
MIROVA_DIR = DATA_DIR / "mirova"
OUT_DIR = REPO / "experiments" / "audit_s9"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Closed set of valid clasificaciones. MUST match rebuild_mirova_from_consolidado.py.
# Any record outside this set in a ref file means the ref is contaminated (L7.10).
VALID_CLASSES = {"Muy Bajo", "Bajo"}

# Required source prefix — the only trusted provenance is text-scraped CSV,
# never the OCR-era source='MIROVA' files.
REQUIRED_SOURCE_PREFIX = "registro_vrp_consolidado"

# Tiering (see tasks/todo.md S9 plan)
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito"]
TIER_B = ["PlanchonPeteroa", "Chaiten", "Villarrica"]
TIER_C = ["NevadosDeChillan", "Llaima", "Copahue"]  # not calibratable
ALL_VOLCANOES = TIER_A + TIER_B + TIER_C

# Sensor family mapping: ours -> canonical family matching MIROVA vocabulary
OURS_TO_FAMILY = {
    "MODIS_TERRA": "MODIS",
    "MODIS_AQUA": "MODIS",
    "VIIRS_NOAA20": "VIIRS375",
    "VIIRS_SNPP": "VIIRS375",
    "VIIRS_NOAA20_750": "VIIRS",
    "VIIRS_SNPP_750": "VIIRS",
}
REF_TO_FAMILY = {"MODIS": "MODIS", "VIIRS375": "VIIRS375", "VIIRS": "VIIRS"}

# Time tolerance per family (minutes)
TOLERANCE_MIN = {"MODIS": 60, "VIIRS375": 30, "VIIRS": 30}

# VRP buckets (MW) for reporting
BUCKETS = [
    ("<0.5", 0.0, 0.5),
    ("0.5-1", 0.5, 1.0),
    ("1-2", 1.0, 2.0),
    ("2-5", 2.0, 5.0),
    ("5-10", 5.0, 10.0),
    (">10", 10.0, float("inf")),
]


def parse_dt(s: str) -> datetime:
    """Parse 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'."""
    s = (s or "").strip()
    if len(s) >= 19:
        try:
            return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def load_ref(volcano: str) -> tuple[list[dict], dict]:
    """Load and HARD-VALIDATE a mirova ref file.

    Raises SystemExit with a clear message if the ref is contaminated.
    """
    path = MIROVA_DIR / f"{volcano}.json"
    if not path.exists():
        raise SystemExit(f"FATAL: ref file not found: {path}")

    doc = json.loads(path.read_text(encoding="utf-8"))
    source = doc.get("source", "")
    records = doc.get("records", [])

    # Defense 1: source must be consolidado
    if not source.startswith(REQUIRED_SOURCE_PREFIX):
        raise SystemExit(
            f"FATAL: {path.name} has source={source!r}, expected prefix "
            f"{REQUIRED_SOURCE_PREFIX!r}. This is likely an OCR-era file. "
            f"Regenerate with scripts/rebuild_mirova_from_consolidado.py. "
            f"See lessons L7.5, L7.10."
        )

    # Defense 2: every clasificacion must be valid
    bad = [
        (i, r.get("clasificacion"))
        for i, r in enumerate(records)
        if (r.get("clasificacion") or "").strip() not in VALID_CLASSES
    ]
    if bad:
        sample = bad[:3]
        raise SystemExit(
            f"FATAL: {path.name} has {len(bad)} records with clasificacion "
            f"not in {sorted(VALID_CLASSES)}. Sample: {sample}. "
            f"This ref is CONTAMINATED. Regenerate it. See lessons L7.10."
        )

    # Parse datetimes
    parsed = []
    for r in records:
        try:
            dt = parse_dt(r["datetime_utc"])
        except Exception:
            continue
        family = REF_TO_FAMILY.get(r.get("sensor", "").strip())
        if family is None:
            continue
        parsed.append(
            {
                "dt": dt,
                "family": family,
                "vrp": float(r.get("VRP_MW", 0.0)),
                "raw_sensor": r.get("sensor"),
                "clasificacion": r.get("clasificacion"),
                "distancia_km": r.get("distancia_km"),
            }
        )

    return parsed, doc


def load_ours(volcano: str) -> list[dict]:
    """Load our pipeline output, normalize to audit schema."""
    path = DATA_DIR / f"{volcano}.json"
    if not path.exists():
        raise SystemExit(f"FATAL: ours file not found: {path}")

    doc = json.loads(path.read_text(encoding="utf-8"))
    records = doc.get("records", [])
    out = []
    for r in records:
        vrp = float(r.get("vrp_mw", 0.0) or 0.0)
        if vrp <= 0:
            continue  # only detections go into pairing
        sensor = r.get("sensor", "").strip()
        family = OURS_TO_FAMILY.get(sensor)
        if family is None:
            # Unknown sensor, skip (will log count)
            continue
        try:
            dt = parse_dt(r["datetime_utc"])
        except Exception:
            continue
        out.append(
            {
                "dt": dt,
                "family": family,
                "vrp": vrp,
                "raw_sensor": sensor,
                "n_anomalous_pixels": r.get("n_anomalous_pixels", 0),
                "n_vent_pixels": r.get("n_vent_pixels", 0),
                "hotspot_dist_km": r.get("hotspot_dist_km"),
            }
        )
    return out


def bucket_for(vrp: float) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= vrp < hi:
            return name
    return ">10"


def pair_records(
    ours: list[dict], ref: list[dict]
) -> tuple[list[tuple[dict, dict]], list[dict], list[dict]]:
    """Strict 1:1 pairing by (family, time-window).

    Greedy algorithm:
    - Sort ref by datetime
    - For each ref record, find the closest unmatched our-record in the same
      family within the tolerance window
    - If found: TP pair. If not: ref is FN.
    - Unmatched our-records become FP.

    No closest-of-day fallback. No bucket-and-match.
    """
    ours_by_family: dict[str, list[dict]] = defaultdict(list)
    for r in ours:
        ours_by_family[r["family"]].append(dict(r, _used=False))
    for family in ours_by_family:
        ours_by_family[family].sort(key=lambda x: x["dt"])

    tp_pairs = []
    fn_records = []

    for ref_rec in sorted(ref, key=lambda x: x["dt"]):
        family = ref_rec["family"]
        tol = timedelta(minutes=TOLERANCE_MIN[family])
        candidates = ours_by_family.get(family, [])

        best = None
        best_delta = tol + timedelta(seconds=1)
        for our_rec in candidates:
            if our_rec["_used"]:
                continue
            delta = abs(our_rec["dt"] - ref_rec["dt"])
            if delta <= tol and delta < best_delta:
                best = our_rec
                best_delta = delta

        if best is not None:
            best["_used"] = True
            tp_pairs.append((ref_rec, best))
        else:
            fn_records.append(ref_rec)

    fp_records = [
        r for recs in ours_by_family.values() for r in recs if not r["_used"]
    ]
    # Clean the _used marker before returning
    for r in fp_records:
        r.pop("_used", None)

    return tp_pairs, fn_records, fp_records


def summarize(
    volcano: str,
    tp_pairs: list[tuple[dict, dict]],
    fn_records: list[dict],
    fp_records: list[dict],
    ref: list[dict],
    ours: list[dict],
) -> dict:
    """Compute and return metrics dict."""
    n_tp = len(tp_pairs)
    n_fn = len(fn_records)
    n_fp = len(fp_records)
    n_ref = len(ref)
    n_ours = len(ours)

    precision = n_tp / (n_tp + n_fp) if (n_tp + n_fp) > 0 else None
    recall = n_tp / (n_tp + n_fn) if (n_tp + n_fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision and recall and (precision + recall) > 0
        else None
    )

    # Ratios (ours / mirova) for TPs only
    ratios = [our["vrp"] / ref_r["vrp"] for ref_r, our in tp_pairs if ref_r["vrp"] > 0]
    ratio_stats = None
    if ratios:
        srt = sorted(ratios)
        q1 = quantiles(srt, n=4)[0] if len(srt) >= 4 else srt[0]
        q3 = quantiles(srt, n=4)[2] if len(srt) >= 4 else srt[-1]
        ratio_stats = {
            "n": len(ratios),
            "min": round(min(ratios), 3),
            "q1": round(q1, 3),
            "median": round(median(ratios), 3),
            "q3": round(q3, 3),
            "max": round(max(ratios), 3),
        }

    # Per sensor-family breakdown
    by_family = {}
    for family in ("MODIS", "VIIRS375", "VIIRS"):
        fam_tp = [(rr, our) for rr, our in tp_pairs if rr["family"] == family]
        fam_fn = [r for r in fn_records if r["family"] == family]
        fam_fp = [r for r in fp_records if r["family"] == family]
        fam_ref = [r for r in ref if r["family"] == family]
        fam_ours = [r for r in ours if r["family"] == family]

        fam_ratios = [o["vrp"] / rr["vrp"] for rr, o in fam_tp if rr["vrp"] > 0]
        fam_ratio_stats = None
        if fam_ratios:
            srt = sorted(fam_ratios)
            q1 = quantiles(srt, n=4)[0] if len(srt) >= 4 else srt[0]
            q3 = quantiles(srt, n=4)[2] if len(srt) >= 4 else srt[-1]
            fam_ratio_stats = {
                "n": len(fam_ratios),
                "q1": round(q1, 3),
                "median": round(median(fam_ratios), 3),
                "q3": round(q3, 3),
            }

        p_fam = (
            len(fam_tp) / (len(fam_tp) + len(fam_fp))
            if (len(fam_tp) + len(fam_fp)) > 0
            else None
        )
        r_fam = (
            len(fam_tp) / (len(fam_tp) + len(fam_fn))
            if (len(fam_tp) + len(fam_fn)) > 0
            else None
        )

        by_family[family] = {
            "n_ref": len(fam_ref),
            "n_ours_det": len(fam_ours),
            "tp": len(fam_tp),
            "fn": len(fam_fn),
            "fp": len(fam_fp),
            "precision": round(p_fam, 3) if p_fam is not None else None,
            "recall": round(r_fam, 3) if r_fam is not None else None,
            "ratio": fam_ratio_stats,
        }

    # Per bucket (of MIROVA VRP) breakdown
    by_bucket = {}
    for name, lo, hi in BUCKETS:
        bk_ref = [r for r in ref if lo <= r["vrp"] < hi]
        bk_tp = [(rr, o) for rr, o in tp_pairs if lo <= rr["vrp"] < hi]
        bk_fn = [r for r in fn_records if lo <= r["vrp"] < hi]
        bk_fp = [r for r in fp_records if lo <= r["vrp"] < hi]
        bk_ratios = [o["vrp"] / rr["vrp"] for rr, o in bk_tp if rr["vrp"] > 0]
        bk_ratio_stats = None
        if bk_ratios:
            bk_ratio_stats = {
                "n": len(bk_ratios),
                "median": round(median(bk_ratios), 3),
            }
        by_bucket[name] = {
            "n_ref": len(bk_ref),
            "tp": len(bk_tp),
            "fn": len(bk_fn),
            "fp_in_bucket": len(bk_fp),
            "ratio": bk_ratio_stats,
        }

    return {
        "volcano": volcano,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "audit_script": "experiments/11_strict_audit.py",
        "totals": {
            "n_ref": n_ref,
            "n_ours_detections": n_ours,
            "tp": n_tp,
            "fn": n_fn,
            "fp": n_fp,
            "precision": round(precision, 3) if precision is not None else None,
            "recall": round(recall, 3) if recall is not None else None,
            "f1": round(f1, 3) if f1 is not None else None,
            "ratio_overall": ratio_stats,
        },
        "by_family": by_family,
        "by_bucket": by_bucket,
    }


def print_report(metrics: dict) -> None:
    v = metrics["volcano"]
    t = metrics["totals"]
    print(f"\n=== {v} ===")
    print(
        f"  ref={t['n_ref']}  ours_det={t['n_ours_detections']}  "
        f"TP={t['tp']}  FN={t['fn']}  FP={t['fp']}"
    )
    print(
        f"  precision={t['precision']}  recall={t['recall']}  f1={t['f1']}"
    )
    if t["ratio_overall"]:
        r = t["ratio_overall"]
        print(
            f"  ratio ours/mirova: n={r['n']}  "
            f"Q1={r['q1']}  median={r['median']}  Q3={r['q3']}"
        )
    print("  by family:")
    for family, fm in metrics["by_family"].items():
        if fm["n_ref"] == 0 and fm["n_ours_det"] == 0:
            continue
        line = (
            f"    {family:9s}  ref={fm['n_ref']:3d}  ours={fm['n_ours_det']:3d}  "
            f"TP={fm['tp']:3d}  FN={fm['fn']:3d}  FP={fm['fp']:3d}"
        )
        if fm["precision"] is not None:
            line += f"  P={fm['precision']:.2f}"
        if fm["recall"] is not None:
            line += f"  R={fm['recall']:.2f}"
        if fm["ratio"]:
            line += f"  ratio_med={fm['ratio']['median']}"
        print(line)
    print("  by bucket (MIROVA VRP):")
    for name, bk in metrics["by_bucket"].items():
        if bk["n_ref"] == 0 and bk["fp_in_bucket"] == 0:
            continue
        line = (
            f"    {name:6s}  ref={bk['n_ref']:3d}  TP={bk['tp']:3d}  "
            f"FN={bk['fn']:3d}  FP_bk={bk['fp_in_bucket']:3d}"
        )
        if bk["ratio"]:
            line += f"  ratio_med={bk['ratio']['median']}"
        print(line)


def audit_one(volcano: str) -> dict:
    ref, _ = load_ref(volcano)
    ours = load_ours(volcano)

    # Restrict ours to ref time range to avoid penalizing us for detections
    # outside the ref period (the consolidado scrape has a finite range).
    if ref:
        ref_start = min(r["dt"] for r in ref) - timedelta(hours=2)
        ref_end = max(r["dt"] for r in ref) + timedelta(hours=2)
        ours = [r for r in ours if ref_start <= r["dt"] <= ref_end]

    tp_pairs, fn, fp = pair_records(ours, ref)
    metrics = summarize(volcano, tp_pairs, fn, fp, ref, ours)

    # Save snapshot
    snap_path = OUT_DIR / f"{volcano}.json"
    # Convert datetimes in FN/FP for serialization
    snap = {
        **metrics,
        "fn_records": [
            {**r, "dt": r["dt"].strftime("%Y-%m-%d %H:%M")} for r in fn
        ],
        "fp_records": [
            {**r, "dt": r["dt"].strftime("%Y-%m-%d %H:%M")} for r in fp
        ],
    }
    snap_path.write_text(json.dumps(snap, indent=2, default=str), encoding="utf-8")

    print_report(metrics)
    print(f"  snapshot: {snap_path.relative_to(REPO)}")
    return metrics


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--volcano", help="Single volcano stem")
    g.add_argument("--tier", choices=["A", "B", "C", "all"], help="Tier to audit")
    g.add_argument("--all", action="store_true", help="Audit all volcanoes")
    args = p.parse_args()

    if args.volcano:
        vols = [args.volcano]
    elif args.tier == "A":
        vols = TIER_A
    elif args.tier == "B":
        vols = TIER_B
    elif args.tier == "C":
        vols = TIER_C
    elif args.tier == "all" or args.all:
        vols = ALL_VOLCANOES
    else:
        vols = []

    results = []
    for v in vols:
        try:
            m = audit_one(v)
            results.append(m)
        except SystemExit as e:
            print(f"\n!!! {v}: {e}", file=sys.stderr)
            sys.exit(1)

    if len(results) > 1:
        print("\n=== SUMMARY ===")
        print(
            f"{'volcano':22s}  {'ref':>4s}  {'TP':>4s}  {'FN':>4s}  {'FP':>4s}  "
            f"{'P':>5s}  {'R':>5s}  {'F1':>5s}  ratio_med"
        )
        for m in results:
            t = m["totals"]
            rm = t["ratio_overall"]["median"] if t["ratio_overall"] else None
            print(
                f"{m['volcano']:22s}  {t['n_ref']:4d}  {t['tp']:4d}  "
                f"{t['fn']:4d}  {t['fp']:4d}  "
                f"{(t['precision'] or 0):.2f}  {(t['recall'] or 0):.2f}  "
                f"{(t['f1'] or 0):.2f}  {rm if rm is not None else '-'}"
            )


if __name__ == "__main__":
    main()
