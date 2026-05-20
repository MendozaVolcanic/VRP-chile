"""
Calibracion empirica del umbral t_bg_k para Opcion A del fix D9 (S71).

Identifica records VRP Chile triggered SOLO por path D (dNTI contextual),
los clasifica como TP/FP por cross-check contra MIROVA NRT (CONS+OCR ALERTA),
y reporta tabla ROC para umbral skip-path-D if t_bg_k < X.

Read-only. Outputs:
  - calibration.json (raw)
  - calibration_report.md (summary)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

# Tier A volcanoes per CLAUDE.md
TIER_A = [
    "Lastarria", "Lascar", "Isluga", "Villarrica", "Chaiten",
    "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle",
    "Llaima", "Copahue", "NevadosDeChillan",
]

# Map VRP volcano name (file) -> CSV "Volcan" column values to match
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
    "NevadosDeChillan": ["Nevados de Chillan"],
}

CONS_CSV = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR_CSV = ROOT / "data" / "mirova_reference" / "registro_vrp_ocr.csv"
VRP_DIR = ROOT / "data" / "mirova_equivalent"

# Threshold sweep
T_BG_THRESHOLDS_K = [255, 260, 265, 268, 270, 273, 275, 278, 280]

# eqVrp threshold (in MW): record is "path-D-only with eqVrp>X"
EQVRP_MIN_MW = 5.0

# Tolerance for MIROVA cross-check (hours)
MATCH_TOL_HOURS = 3.0


def load_mirova_alerts() -> pd.DataFrame:
    """Load CONS + OCR ALERTA_TERMICA records."""
    cons = pd.read_csv(CONS_CSV)
    ocr = pd.read_csv(OCR_CSV)
    cons_a = cons[cons["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)].copy()
    ocr_a = ocr[ocr["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)].copy()
    cons_a["source"] = "CONS"
    ocr_a["source"] = "OCR"
    common = ["timestamp", "Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Tipo_Registro", "source"]
    alerts = pd.concat([cons_a[common], ocr_a[common]], ignore_index=True)
    alerts["timestamp"] = pd.to_numeric(alerts["timestamp"], errors="coerce")
    alerts = alerts.dropna(subset=["timestamp"])
    return alerts


def parse_record_dt(rec: dict) -> datetime | None:
    """Parse datetime_utc from a VRP record."""
    dt_str = rec.get("datetime_utc")
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def get_eqvrp_mw(rec: dict) -> float:
    """Return effective VRP (MW) for the record. Prefer pc.vrp_mw (A4/S52)."""
    pc = rec.get("primary_cluster")
    if isinstance(pc, dict) and pc.get("vrp_mw") is not None:
        try:
            return float(pc["vrp_mw"])
        except (ValueError, TypeError):
            pass
    # fallback: record-level vrp_mw
    v = rec.get("vrp_mw")
    if v is not None:
        try:
            return float(v)
        except (ValueError, TypeError):
            pass
    return 0.0


def is_path_d_only(rec: dict) -> bool:
    """True iff path D (dNTI contextual) was sole trigger.
    Uses diag_n_*_path counters (the canonical 'how many pixels each path produced')."""
    bt = rec.get("diag_n_bt_path", 0) or 0
    nti = rec.get("diag_n_nti_path", 0) or 0
    dnti = rec.get("diag_n_dnti_ctx_path", 0) or 0
    # also consider nti_rel (path C) if present
    nti_rel = rec.get("n_nti_rel_path", 0) or 0
    return (bt == 0) and (nti == 0) and (nti_rel == 0) and (dnti > 0)


def match_mirova(rec_dt: datetime, vol_names: list[str], alerts: pd.DataFrame) -> bool:
    """True if there's a MIROVA ALERTA within +/- MATCH_TOL_HOURS hours for this volcano."""
    ts_target = rec_dt.timestamp()
    tol = MATCH_TOL_HOURS * 3600
    sub = alerts[alerts["Volcan"].isin(vol_names)]
    if sub.empty:
        return False
    diffs = (sub["timestamp"].astype(float) - ts_target).abs()
    return bool((diffs <= tol).any())


def process_volcano(vol: str, alerts: pd.DataFrame) -> dict:
    """Return per-volcano results dict."""
    fp_path = VRP_DIR / f"{vol}.json"
    if not fp_path.exists():
        return {"volcano": vol, "error": "json_missing", "total_records": 0}

    with open(fp_path) as f:
        data = json.load(f)
    records = data.get("records", [])

    vol_csv_names = VOL_CSV_MAP.get(vol, [vol])

    tp_rows = []  # path-D-only & MIROVA-confirmed
    fp_rows = []  # path-D-only & no MIROVA

    schema_missing_tbg = 0

    for rec in records:
        if not is_path_d_only(rec):
            continue
        eqvrp = get_eqvrp_mw(rec)
        if eqvrp <= EQVRP_MIN_MW:
            continue
        t_bg = rec.get("t_bg_k")
        if t_bg is None:
            schema_missing_tbg += 1
            continue
        try:
            t_bg = float(t_bg)
        except (ValueError, TypeError):
            schema_missing_tbg += 1
            continue
        rec_dt = parse_record_dt(rec)
        if rec_dt is None:
            continue
        matched = match_mirova(rec_dt, vol_csv_names, alerts)
        row = {
            "datetime_utc": rec.get("datetime_utc"),
            "t_bg_k": t_bg,
            "eqvrp_mw": eqvrp,
            "sensor": rec.get("sensor"),
            "diag_n_dnti_ctx_path": rec.get("diag_n_dnti_ctx_path"),
        }
        (tp_rows if matched else fp_rows).append(row)

    def stats(rows):
        if not rows:
            return {"n": 0}
        s = pd.Series([r["t_bg_k"] for r in rows])
        return {
            "n": int(s.size),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "p10": float(s.quantile(0.10)),
            "p25": float(s.quantile(0.25)),
            "p75": float(s.quantile(0.75)),
            "p90": float(s.quantile(0.90)),
            "min": float(s.min()),
            "max": float(s.max()),
        }

    return {
        "volcano": vol,
        "total_records": len(records),
        "n_path_d_only_eqvrp_gt5": len(tp_rows) + len(fp_rows),
        "tp": stats(tp_rows),
        "fp": stats(fp_rows),
        "tp_rows": tp_rows,
        "fp_rows": fp_rows,
        "schema_missing_tbg": schema_missing_tbg,
    }


def roc_table(all_results: list[dict]) -> list[dict]:
    """For each threshold, compute TPs lost vs FPs eliminated (global + per volcano)."""
    all_tp = []
    all_fp = []
    for r in all_results:
        all_tp.extend([(r["volcano"], row) for row in r.get("tp_rows", [])])
        all_fp.extend([(r["volcano"], row) for row in r.get("fp_rows", [])])

    rows = []
    n_tp_total = len(all_tp)
    n_fp_total = len(all_fp)
    for x in T_BG_THRESHOLDS_K:
        # "skip path D if t_bg_k < X" -> records with t_bg_k < X are eliminated
        tp_lost = sum(1 for _, r in all_tp if r["t_bg_k"] < x)
        fp_elim = sum(1 for _, r in all_fp if r["t_bg_k"] < x)
        rows.append({
            "threshold_k": x,
            "tp_lost": tp_lost,
            "tp_total": n_tp_total,
            "tp_recall_kept": (1 - tp_lost / n_tp_total) if n_tp_total else None,
            "fp_eliminated": fp_elim,
            "fp_total": n_fp_total,
            "fp_elim_frac": (fp_elim / n_fp_total) if n_fp_total else None,
        })
    return rows


def roc_per_vol(all_results: list[dict]) -> dict:
    """Per-volcano ROC: TPs lost / FPs eliminated for each threshold."""
    out = {}
    for r in all_results:
        tp_rows = r.get("tp_rows", [])
        fp_rows = r.get("fp_rows", [])
        if (len(tp_rows) + len(fp_rows)) == 0:
            continue
        rows = []
        for x in T_BG_THRESHOLDS_K:
            tp_lost = sum(1 for rec in tp_rows if rec["t_bg_k"] < x)
            fp_elim = sum(1 for rec in fp_rows if rec["t_bg_k"] < x)
            rows.append({
                "threshold_k": x,
                "tp_lost": tp_lost, "tp_total": len(tp_rows),
                "fp_eliminated": fp_elim, "fp_total": len(fp_rows),
            })
        out[r["volcano"]] = rows
    return out


def main():
    print(f"[loading MIROVA alerts CONS+OCR]")
    alerts = load_mirova_alerts()
    print(f"  total ALERTA rows: {len(alerts)}")

    all_results = []
    for vol in TIER_A:
        print(f"[processing {vol}]")
        r = process_volcano(vol, alerts)
        all_results.append(r)
        if "error" not in r:
            print(f"  total={r['total_records']}  pathD-only-eqVrp>5: TP={r['tp']['n']} FP={r['fp']['n']}")

    roc = roc_table(all_results)
    roc_pv = roc_per_vol(all_results)

    # Recommendation: max FPs eliminated keeping TP recall >= 0.90
    recommend = None
    for r in sorted(roc, key=lambda x: -x["threshold_k"]):
        rec = r["tp_recall_kept"]
        if rec is not None and rec >= 0.90:
            if recommend is None or r["fp_eliminated"] > recommend["fp_eliminated"]:
                recommend = r
    # pick the threshold giving largest fp_elim with recall>=0.90
    candidates = [r for r in roc if r["tp_recall_kept"] is not None and r["tp_recall_kept"] >= 0.90]
    if candidates:
        recommend = max(candidates, key=lambda x: x["fp_eliminated"])

    out_json = {
        "params": {
            "EQVRP_MIN_MW": EQVRP_MIN_MW,
            "MATCH_TOL_HOURS": MATCH_TOL_HOURS,
            "T_BG_THRESHOLDS_K": T_BG_THRESHOLDS_K,
        },
        "per_volcano": [{k: v for k, v in r.items() if k not in ("tp_rows", "fp_rows")} for r in all_results],
        "roc_global": roc,
        "roc_per_volcano": roc_pv,
        "recommendation": recommend,
        "raw_tp_rows": {r["volcano"]: r.get("tp_rows", []) for r in all_results},
        "raw_fp_rows": {r["volcano"]: r.get("fp_rows", []) for r in all_results},
    }

    out_path = OUT_DIR / "calibration.json"
    with open(out_path, "w") as f:
        json.dump(out_json, f, indent=2, default=str)
    print(f"\n[wrote {out_path}]")

    # markdown report
    write_report(out_json, OUT_DIR / "calibration_report.md")
    print(f"[wrote {OUT_DIR / 'calibration_report.md'}]")


def write_report(out: dict, path: Path):
    lines = []
    lines.append("# Calibracion umbral t_bg_k - Path D fix D9 (S71 T1)")
    lines.append("")
    lines.append(f"**Params**: eqVrp >= {out['params']['EQVRP_MIN_MW']} MW (path-D-only), match MIROVA +/- {out['params']['MATCH_TOL_HOURS']}h (CONS+OCR ALERTA).")
    lines.append("")
    lines.append("## Per-volcano summary (path-D-only records, eqVrp>5 MW)")
    lines.append("")
    lines.append("| Volcan | total_records | N_pD_only | N_TP | t_bg_TP_median | N_FP | t_bg_FP_median |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in out["per_volcano"]:
        if "error" in r:
            lines.append(f"| {r['volcano']} | - | error: {r['error']} | | | | |")
            continue
        tp = r["tp"]; fp = r["fp"]
        tp_med = f"{tp['median']:.1f}" if tp["n"] else "-"
        fp_med = f"{fp['median']:.1f}" if fp["n"] else "-"
        lines.append(f"| {r['volcano']} | {r['total_records']} | {r['n_path_d_only_eqvrp_gt5']} | {tp['n']} | {tp_med} | {fp['n']} | {fp_med} |")
    lines.append("")
    lines.append("## Per-volcano t_bg_k distribution (TPs)")
    lines.append("")
    lines.append("| Volcan | n | mean | p10 | p25 | median | p75 | p90 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in out["per_volcano"]:
        if "error" in r or r["tp"]["n"] == 0:
            continue
        s = r["tp"]
        lines.append(f"| {r['volcano']} | {s['n']} | {s['mean']:.1f} | {s['p10']:.1f} | {s['p25']:.1f} | {s['median']:.1f} | {s['p75']:.1f} | {s['p90']:.1f} |")
    lines.append("")
    lines.append("## Per-volcano t_bg_k distribution (FPs)")
    lines.append("")
    lines.append("| Volcan | n | mean | p10 | p25 | median | p75 | p90 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in out["per_volcano"]:
        if "error" in r or r["fp"]["n"] == 0:
            continue
        s = r["fp"]
        lines.append(f"| {r['volcano']} | {s['n']} | {s['mean']:.1f} | {s['p10']:.1f} | {s['p25']:.1f} | {s['median']:.1f} | {s['p75']:.1f} | {s['p90']:.1f} |")
    lines.append("")
    lines.append("## ROC global: skip path D if t_bg_k < X")
    lines.append("")
    lines.append("| Threshold K | TP_lost | TP_total | Recall_kept | FP_eliminated | FP_total | FP_elim_frac |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in out["roc_global"]:
        rec = f"{r['tp_recall_kept']:.3f}" if r["tp_recall_kept"] is not None else "-"
        fef = f"{r['fp_elim_frac']:.3f}" if r["fp_elim_frac"] is not None else "-"
        lines.append(f"| {r['threshold_k']} | {r['tp_lost']} | {r['tp_total']} | {rec} | {r['fp_eliminated']} | {r['fp_total']} | {fef} |")
    lines.append("")
    lines.append("## ROC per volcano (TPs lost / FPs eliminated at each threshold)")
    lines.append("")
    for vol, rows in out["roc_per_volcano"].items():
        lines.append(f"### {vol}")
        lines.append("")
        lines.append("| Threshold K | TP_lost/TP_total | FP_eliminated/FP_total |")
        lines.append("|---|---|---|")
        for r in rows:
            lines.append(f"| {r['threshold_k']} | {r['tp_lost']}/{r['tp_total']} | {r['fp_eliminated']}/{r['fp_total']} |")
        lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    rec = out["recommendation"]
    if rec:
        lines.append(f"**Recommended threshold: skip path D if t_bg_k < {rec['threshold_k']} K**")
        lines.append("")
        lines.append(f"- Recall preserved: {rec['tp_recall_kept']:.3f} ({rec['tp_total'] - rec['tp_lost']}/{rec['tp_total']} TPs kept)")
        lines.append(f"- FPs eliminated: {rec['fp_eliminated']}/{rec['fp_total']} ({rec['fp_elim_frac']:.1%})")
    else:
        lines.append("No threshold maintains TP recall >= 0.90 - sample insufficient or data does not separate.")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
