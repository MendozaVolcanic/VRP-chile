"""
S72 F2.2 - A/B audit unsuitable filters (mirova_equivalent vs
mirova_equivalent_unsuitable_filters_v1).

Diferencias vs experiments/128_path_d_ab_audit/audit.py:
  - Matching MIROVA: ±60 min sensor-aware (no ±3h por noche).
  - Per-record TP/FP/FN (no agregado por noche).
  - Baseline desde data/mirova_equivalent (operacional S70).
  - A/B desde data extraida del commit 750fbc0 (PR #115). Ese commit
    introdujo data/mirova_equivalent_unsuitable_filters_v1/ que NO existe en
    el worktree actual; el script acepta tanto un path local override como
    un staging dir tmp.

Bug D9 count:
  pc.vrp_mw > 5 MW AND diag_n_bt_path==0 AND diag_n_nti_path==0 AND t_bg_k<260K.

d9_capped:
  campo del profile mirova_equivalent_path_d_cap_v1; NO se emite ni en
  baseline mirova_equivalent ni en unsuitable_filters_v1. Se reporta como
  N/A (gap A7: no calculado en este profile) en lugar de 0/0 confundible.

Convencion A4: usar pc.vrp_mw cuando exista.
"""
from __future__ import annotations

import calendar
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

TIER_A_SUCCESS = [
    "Lascar", "Lastarria", "Isluga", "Villarrica", "Chaiten",
    "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle",
    "Llaima", "Copahue",
]

VOL_CSV_MAP = {
    "Lastarria": ["Lastarria"],
    "Lascar": ["Lascar"],
    "Isluga": ["Isluga"],
    "Villarrica": ["Villarrica"],
    "Chaiten": ["Chaiten"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Peteroa"],
    "Tupungatito": ["Tupungatito"],
    "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle"],
    "Llaima": ["Llaima"],
    "Copahue": ["Copahue"],
}

CONS_CSV = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR_CSV = ROOT / "data" / "mirova_reference" / "registro_vrp_ocr.csv"

BASELINE_DIR = ROOT / "data" / "mirova_equivalent"
# A/B dir override via env var (so we can point at extracted tmp)
AB_DIR = Path(os.environ.get(
    "AB_DIR",
    str(ROOT / "data" / "mirova_equivalent_unsuitable_filters_v1"),
))

MATCH_TOL_MIN = 60.0
BUG_D9_VRP_MIN_MW = 5.0
BUG_D9_TBG_MAX_K = 260.0

# Window from prompt: 2026-02-20 -> 2026-05-20 (UTC)
WINDOW_START = datetime(2026, 2, 20, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 5, 20, 23, 59, 59, tzinfo=timezone.utc)
WINDOW_START_TS = WINDOW_START.timestamp()
WINDOW_END_TS = WINDOW_END.timestamp()


def sensor_family(s: str) -> str:
    """Map record/csv sensor strings to a family for matching.
    VRP records: VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21 / MODIS_TERRA / MODIS_AQUA
    CSV: MODIS / VIIRS / VIIRS375
    """
    if not s:
        return ""
    su = s.upper()
    if "MODIS" in su:
        return "MODIS"
    if "VIIRS" in su:
        return "VIIRS"  # collapse VIIRS / VIIRS375 / VIIRS750
    return su


def load_mirova_alerts() -> pd.DataFrame:
    cons = pd.read_csv(CONS_CSV)
    ocr = pd.read_csv(OCR_CSV)
    keep = ["timestamp", "Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Tipo_Registro"]
    cons_a = cons[cons["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)][keep].copy()
    ocr_a = ocr[ocr["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)][keep].copy()
    cons_a["source"] = "CONS"
    ocr_a["source"] = "OCR"
    al = pd.concat([cons_a, ocr_a], ignore_index=True)
    al["timestamp"] = pd.to_numeric(al["timestamp"], errors="coerce")
    al["VRP_MW"] = pd.to_numeric(al["VRP_MW"], errors="coerce")
    al = al.dropna(subset=["timestamp"]).reset_index(drop=True)
    al["sensor_fam"] = al["Sensor"].apply(sensor_family)
    # Restrict to audit window
    al = al[(al["timestamp"] >= WINDOW_START_TS) &
            (al["timestamp"] <= WINDOW_END_TS)].reset_index(drop=True)
    return al


def parse_record_ts(dt_str):
    """Parse VRP record datetime_utc as a UTC unix timestamp (the string IS UTC)."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            t = datetime.strptime(dt_str, fmt)
            return calendar.timegm(t.timetuple())
        except (ValueError, TypeError):
            continue
    return None


def get_eqvrp_mw(rec):
    pc = rec.get("primary_cluster")
    if isinstance(pc, dict) and pc.get("vrp_mw") is not None:
        try:
            return float(pc["vrp_mw"])
        except (ValueError, TypeError):
            pass
    v = rec.get("vrp_mw")
    if v is not None:
        try:
            return float(v)
        except (ValueError, TypeError):
            pass
    return 0.0


def has_detection(rec):
    """Detection = published cluster (pc.vrp_mw>0). Esto refleja firing real,
    no solo hot mask candidates (que mientras n_anomalous_pixels>0 puede haber
    sido descartado por cluster filter / dist / min_vent_pixels)."""
    return get_eqvrp_mw(rec) > 0.01


def is_d9_bug(rec):
    """pc.vrp_mw>5 AND contextual-only AND t_bg<260K."""
    eqv = get_eqvrp_mw(rec)
    if eqv <= BUG_D9_VRP_MIN_MW:
        return False
    bt = rec.get("diag_n_bt_path", 0) or 0
    nti = rec.get("diag_n_nti_path", 0) or 0
    if bt > 0 or nti > 0:
        return False
    tbg = rec.get("t_bg_k")
    try:
        if tbg is None or float(tbg) >= BUG_D9_TBG_MAX_K:
            return False
    except (ValueError, TypeError):
        return False
    return True


def load_vol(dir_, vol):
    fp = dir_ / f"{vol}.json"
    if not fp.exists():
        return None
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("records", [])


def in_window(rec_ts):
    return rec_ts is not None and WINDOW_START_TS <= rec_ts <= WINDOW_END_TS


def find_match(rec_ts, sensor_fam, sub_al):
    """Find MIROVA alert within ±60min for same sensor family. Returns row or None."""
    if sub_al.empty:
        return None
    tol = MATCH_TOL_MIN * 60.0
    sub = sub_al[sub_al["sensor_fam"] == sensor_fam]
    if sub.empty:
        return None
    diffs = (sub["timestamp"].astype(float) - rec_ts).abs()
    mask = diffs <= tol
    if not mask.any():
        return None
    idx = diffs[mask].idxmin()
    return sub.loc[idx]


def audit_vol_dir(vol, records, alerts_vol):
    """Compute per-record metrics within audit window."""
    if records is None:
        return {"error": "json_missing"}

    # Filter to window
    in_recs = []
    for r in records:
        rts = parse_record_ts(r.get("datetime_utc"))
        if in_window(rts):
            in_recs.append((rts, r))

    n_records = len(in_recs)
    n_detect = 0
    tp = 0
    fp = 0
    matched_alert_idxs = set()
    ratios = []
    bug_d9 = 0
    d9_capped = 0
    d9_capped_supported = False

    for rts, r in in_recs:
        sf = sensor_family(r.get("sensor", ""))
        detected = has_detection(r)
        if detected:
            n_detect += 1
            m = find_match(rts, sf, alerts_vol)
            if m is not None:
                tp += 1
                matched_alert_idxs.add(m.name)  # row index
                if m["VRP_MW"] and m["VRP_MW"] > 0:
                    eqv = get_eqvrp_mw(r)
                    if eqv > 0:
                        try:
                            ratios.append(eqv / float(m["VRP_MW"]))
                        except (ValueError, TypeError):
                            pass
            else:
                fp += 1
        if is_d9_bug(r):
            bug_d9 += 1
        # d9_capped: only counted if present as bool key
        if "d9_capped" in r:
            d9_capped_supported = True
            if r.get("d9_capped"):
                d9_capped += 1

    # FN: MIROVA alerts in window for this vol where no VRP record matched
    # AND we have VRP coverage near that alert (record within ±60min, sensor-fam match).
    # If we have no VRP record at all near the alert it's a "no-coverage" gap, not FN.
    # Build set of (sensor_fam, ts) of in-window VRP records
    vrp_by_sf = {}
    for rts, r in in_recs:
        sf = sensor_family(r.get("sensor", ""))
        vrp_by_sf.setdefault(sf, []).append(rts)

    fn = 0
    n_alerts_no_coverage = 0
    for i, alert in alerts_vol.iterrows():
        if i in matched_alert_idxs:
            continue
        sf = alert["sensor_fam"]
        a_ts = float(alert["timestamp"])
        candidates = vrp_by_sf.get(sf, [])
        has_cov = any(abs(v - a_ts) <= MATCH_TOL_MIN * 60.0 for v in candidates)
        if has_cov:
            fn += 1
        else:
            n_alerts_no_coverage += 1

    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    ratio_med = median(ratios) if ratios else None

    return {
        "n_records_in_window": n_records,
        "n_records_detection": n_detect,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "alerts_in_window": int(len(alerts_vol)),
        "alerts_no_coverage": n_alerts_no_coverage,
        "recall": recall,
        "precision": precision,
        "ratio_median": ratio_med,
        "ratio_n": len(ratios),
        "bug_d9_count": bug_d9,
        "d9_capped_count": d9_capped if d9_capped_supported else None,
        "d9_capped_supported": d9_capped_supported,
    }


def main():
    print(f"[loading MIROVA alerts {WINDOW_START.date()} - {WINDOW_END.date()}]")
    alerts = load_mirova_alerts()
    print(f"  total ALERTA rows in window: {len(alerts)}")
    print(f"[baseline: {BASELINE_DIR}]")
    print(f"[A/B:      {AB_DIR}]")
    print(f"  AB exists: {AB_DIR.exists()}")

    out = {
        "params": {
            "window_start": WINDOW_START.isoformat(),
            "window_end": WINDOW_END.isoformat(),
            "match_tol_min": MATCH_TOL_MIN,
            "bug_d9_vrp_min_mw": BUG_D9_VRP_MIN_MW,
            "bug_d9_tbg_max_k": BUG_D9_TBG_MAX_K,
            "tier_a_success": TIER_A_SUCCESS,
            "baseline_dir": str(BASELINE_DIR),
            "ab_dir": str(AB_DIR),
        },
        "per_volcano": {},
    }

    for vol in TIER_A_SUCCESS:
        print(f"[{vol}]")
        names = VOL_CSV_MAP.get(vol, [vol])
        al_v = alerts[alerts["Volcan"].isin(names)].copy()
        base_recs = load_vol(BASELINE_DIR, vol)
        ab_recs = load_vol(AB_DIR, vol)
        r_base = audit_vol_dir(vol, base_recs, al_v)
        r_ab = audit_vol_dir(vol, ab_recs, al_v)
        out["per_volcano"][vol] = {
            "n_alerts_in_window": int(len(al_v)),
            "baseline": r_base,
            "ab": r_ab,
        }
        def fmt(r):
            if "error" in r:
                return r["error"]
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            return f"TP={r['tp']} FP={r['fp']} FN={r['fn']} rec={rec} pre={prc} ratio={rmd} D9bug={r['bug_d9_count']}"
        print(f"  base: {fmt(r_base)}")
        print(f"  ab:   {fmt(r_ab)}")

    out_json = OUT_DIR / "audit_unsuitable_filters.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[wrote {out_json}]")

    md = render_report(out)
    out_md = OUT_DIR / "audit_report.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote {out_md}]")


def render_report(out):
    L = []
    p = out["params"]
    L.append("# S72 F2.2 - A/B Unsuitable Filters audit")
    L.append("")
    L.append(f"Ventana: {p['window_start'][:10]} -> {p['window_end'][:10]}  (90d)")
    L.append(f"Matching MIROVA: ±{int(p['match_tol_min'])} min sensor-aware (per-record)")
    L.append(f"Bug D9: pc.vrp_mw>{p['bug_d9_vrp_min_mw']} MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<{p['bug_d9_tbg_max_k']} K")
    L.append("")
    L.append("## Per-volcano: baseline vs A/B")
    L.append("")
    L.append("| Volcan | Set | n_alerts | n_rec_det | TP | FP | FN | Recall | Precision | Ratio_med | N_ratio | D9_bug | d9_capped |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for vol in TIER_A_SUCCESS:
        pv = out["per_volcano"].get(vol, {})
        na = pv.get("n_alerts_in_window", 0)
        for label, key in [("base", "baseline"), ("A/B", "ab")]:
            r = pv.get(key, {})
            if "error" in r:
                L.append(f"| {vol} | {label} | {na} | err:{r['error']} | | | | | | | | | |")
                continue
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            cap = "N/A" if not r["d9_capped_supported"] else str(r["d9_capped_count"])
            L.append(f"| {vol} | {label} | {na} | {r['n_records_detection']} | {r['tp']} | {r['fp']} | {r['fn']} | {rec} | {prc} | {rmd} | {r['ratio_n']} | {r['bug_d9_count']} | {cap} |")
    L.append("")
    L.append("## Delta A/B - baseline")
    L.append("")
    L.append("| Volcan | dRecall | dPrecision | dRatio | dD9_bug | dD9_bug_% |")
    L.append("|---|---|---|---|---|---|")
    sum_b = sum_a = 0
    n_d9_drop_50 = 0
    n_ratio_better = 0
    n_recall_ok = 0
    n_recall_eligible = 0
    n_prec_no_degrade = 0
    n_prec_eligible = 0
    vols_with_baseline_d9 = 0
    for vol in TIER_A_SUCCESS:
        pv = out["per_volcano"].get(vol, {})
        b = pv.get("baseline", {})
        a = pv.get("ab", {})
        if "error" in b or "error" in a:
            L.append(f"| {vol} | - | - | - | - | - |")
            continue
        def diff(x, y):
            if x is None or y is None:
                return "-"
            return f"{(x - y):+.2f}"
        d_rec = diff(a["recall"], b["recall"])
        d_pre = diff(a["precision"], b["precision"])
        d_rat = diff(a["ratio_median"], b["ratio_median"])
        d_bug = a["bug_d9_count"] - b["bug_d9_count"]
        if b["bug_d9_count"] > 0:
            pct = (1 - a["bug_d9_count"] / b["bug_d9_count"]) * 100
            vols_with_baseline_d9 += 1
            if (b["bug_d9_count"] - a["bug_d9_count"]) / b["bug_d9_count"] >= 0.5:
                n_d9_drop_50 += 1
            pct_s = f"{pct:+.0f}%"
        else:
            pct_s = "-"
        sum_b += b["bug_d9_count"]
        sum_a += a["bug_d9_count"]
        # better-or-equal ratio: |a-1| <= |b-1|
        if a["ratio_median"] is not None and b["ratio_median"] is not None:
            if abs(a["ratio_median"] - 1.0) <= abs(b["ratio_median"] - 1.0) + 1e-9:
                n_ratio_better += 1
        # recall regression check
        n_mir = a["tp"] + a["fn"]
        if n_mir >= 10 and a["recall"] is not None and b["recall"] is not None:
            n_recall_eligible += 1
            if (b["recall"] - a["recall"]) <= 0.05:
                n_recall_ok += 1
        # precision no-degrade
        if a["precision"] is not None and b["precision"] is not None:
            n_prec_eligible += 1
            if a["precision"] >= b["precision"] - 1e-9:
                n_prec_no_degrade += 1
        L.append(f"| {vol} | {d_rec} | {d_pre} | {d_rat} | {d_bug:+d} | {pct_s} |")
    L.append("")
    L.append("## Resumen criterios S33")
    L.append("")
    total_d9_drop_pct = (1 - sum_a / sum_b) * 100 if sum_b > 0 else 0
    L.append(f"- Bug D9 baseline total: **{sum_b}** -> A/B total: **{sum_a}** ({total_d9_drop_pct:+.1f}%)")
    L.append(f"- Vols con baseline D9>0: {vols_with_baseline_d9}; con drop >=50%: **{n_d9_drop_50}**")
    L.append(f"- Vols con ratio mejor o igual: **{n_ratio_better}/10**")
    L.append(f"- Vols con recall no-degrade (>5pp) [n_mirova>=10]: **{n_recall_ok}/{n_recall_eligible}**")
    L.append(f"- Vols con precision no-degrade: **{n_prec_no_degrade}/{n_prec_eligible}**")
    L.append("")
    L.append("Criterios adopcion S33:")
    L.append("- Bug D9 drop >50% en >=5/10 vols.")
    L.append("- Ratio mediano mejora o se mantiene en >=6/10 vols.")
    L.append("- Recall NO degrada >5pp en ningun vol con n_mirova>=10.")
    L.append("- Precision NO degrada en ningun vol.")
    L.append("- Sin regresion Tier A Alto (Lascar/Lastarria/Isluga).")
    L.append("")
    L.append("Caveats:")
    L.append("- NdC excluido (1 vol failure run 26236980698) -> 10/11 sample.")
    L.append("- d9_capped column es N/A: este profile NO emite el campo (es flag del profile path_d_cap_v1).")
    L.append("- d9_capped fix de raiz: ver bug_d9_count como proxy del bug, no del cap aplicado.")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
