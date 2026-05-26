"""
S72 F2.4 - 4-way A/B audit to isolate Lascar regression culprit.

Setups:
  - baseline (B):  data/mirova_equivalent
      §267-273 first_pass=ON, §267-273 pathD=OFF, K1 retire=OFF
  - F2.1 (F1):     data/mirova_equivalent_unsuitable_filters_v1 (10 vols, no NdC)
      §267-273 first_pass=ON, §267-273 pathD=OFF, K1 retire=ON
  - A/B-1 (A1):    tmp_ab1/ (extracted from commit dc4b286, 10 vols, no Chaiten)
      §267-273 first_pass=ON, §267-273 pathD=ON, K1 retire=OFF
  - A/B-2 (A2):    tmp_ab2/ (extracted from commit a775a7d, 9 vols, no NdC/PCC)
      §267-273 first_pass=OFF, §267-273 pathD=OFF, K1 retire=ON

Reuses metric definitions / matching from experiments/132 (per-record MIROVA
±60min sensor-aware; pc.vrp_mw convention A4; bug D9 contextual-only @ t_bg<260K).

Verdict logic:
  - K1 culprit if A1 OK (no Lascar regress) and A2 reproduces regress.
  - §267-273 pathD culprit if both A1 and F1 regress (A2 may also).
  - Interaction if both A1 and A2 OK individually (F1 still regresses combo).
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

TIER_A = [
    "Lascar", "Lastarria", "Isluga", "Villarrica", "Chaiten",
    "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle",
    "Llaima", "Copahue", "NevadosDeChillan",
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
    "NevadosDeChillan": ["NevadosDeChillan", "Nevados de Chillan"],
}

CONS_CSV = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR_CSV = ROOT / "data" / "mirova_reference" / "registro_vrp_ocr.csv"

DIRS = {
    "baseline": ROOT / "data" / "mirova_equivalent",
    "f21": ROOT / "data" / "mirova_equivalent_unsuitable_filters_v1",
    "ab1": OUT_DIR / "tmp_ab1",
    "ab2": OUT_DIR / "tmp_ab2",
}

MATCH_TOL_MIN = 60.0
BUG_D9_VRP_MIN_MW = 5.0
BUG_D9_TBG_MAX_K = 260.0

WINDOW_START = datetime(2026, 2, 20, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 5, 20, 23, 59, 59, tzinfo=timezone.utc)
WINDOW_START_TS = WINDOW_START.timestamp()
WINDOW_END_TS = WINDOW_END.timestamp()


def sensor_family(s):
    if not s:
        return ""
    su = s.upper()
    if "MODIS" in su:
        return "MODIS"
    if "VIIRS" in su:
        return "VIIRS"
    return su


def load_mirova_alerts():
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
    al = al[(al["timestamp"] >= WINDOW_START_TS) & (al["timestamp"] <= WINDOW_END_TS)].reset_index(drop=True)
    return al


def parse_record_ts(dt_str):
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
    return get_eqvrp_mw(rec) > 0.01


def is_d9_bug(rec):
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


def audit_vol_dir(records, alerts_vol):
    if records is None:
        return {"error": "json_missing"}
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
    for rts, r in in_recs:
        sf = sensor_family(r.get("sensor", ""))
        detected = has_detection(r)
        if detected:
            n_detect += 1
            m = find_match(rts, sf, alerts_vol)
            if m is not None:
                tp += 1
                matched_alert_idxs.add(m.name)
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
    vrp_by_sf = {}
    for rts, r in in_recs:
        sf = sensor_family(r.get("sensor", ""))
        vrp_by_sf.setdefault(sf, []).append(rts)
    fn = 0
    n_no_cov = 0
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
            n_no_cov += 1
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
        "alerts_no_coverage": n_no_cov,
        "recall": recall,
        "precision": precision,
        "ratio_median": ratio_med,
        "ratio_n": len(ratios),
        "bug_d9_count": bug_d9,
    }


def main():
    print(f"[loading MIROVA alerts {WINDOW_START.date()} - {WINDOW_END.date()}]")
    alerts = load_mirova_alerts()
    print(f"  total ALERTA rows in window: {len(alerts)}")
    for k, d in DIRS.items():
        print(f"[{k}] {d} exists={d.exists()}")

    out = {
        "params": {
            "window_start": WINDOW_START.isoformat(),
            "window_end": WINDOW_END.isoformat(),
            "match_tol_min": MATCH_TOL_MIN,
            "bug_d9_vrp_min_mw": BUG_D9_VRP_MIN_MW,
            "bug_d9_tbg_max_k": BUG_D9_TBG_MAX_K,
            "dirs": {k: str(d) for k, d in DIRS.items()},
        },
        "per_volcano": {},
    }
    setups = ["baseline", "f21", "ab1", "ab2"]
    for vol in TIER_A:
        names = VOL_CSV_MAP.get(vol, [vol])
        al_v = alerts[alerts["Volcan"].isin(names)].copy()
        res = {"n_alerts_in_window": int(len(al_v))}
        for s in setups:
            recs = load_vol(DIRS[s], vol)
            res[s] = audit_vol_dir(recs, al_v)
        out["per_volcano"][vol] = res
        # short print
        def fmt(r):
            if "error" in r:
                return "MISSING"
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            return f"r={rec} p={prc} rat={rmd} D9={r['bug_d9_count']} det={r['n_records_detection']}"
        print(f"[{vol}] alerts={len(al_v)}")
        for s in setups:
            print(f"   {s:9s}: {fmt(res[s])}")

    out_json = OUT_DIR / "audit_4way.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[wrote {out_json}]")

    md = render_report(out)
    out_md = OUT_DIR / "audit_4way_report.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote {out_md}]")


def render_report(out):
    L = []
    p = out["params"]
    setups = ["baseline", "f21", "ab1", "ab2"]
    setup_labels = {
        "baseline": "Baseline (firstpass ON, pathD OFF, K1 OFF)",
        "f21": "F2.1 (firstpass ON, pathD OFF, K1 ON)",
        "ab1": "A/B-1 (firstpass ON, pathD ON, K1 OFF)",
        "ab2": "A/B-2 (firstpass OFF, pathD OFF, K1 ON)",
    }
    L.append("# S72 F2.4 — 4-way A/B audit (Lascar regression culprit)")
    L.append("")
    L.append(f"Ventana: {p['window_start'][:10]} → {p['window_end'][:10]} (90d)")
    L.append(f"Matching MIROVA: ±{int(p['match_tol_min'])} min sensor-aware (per-record, CONS+OCR ALERTAs)")
    L.append(f"Bug D9: pc.vrp_mw>{p['bug_d9_vrp_min_mw']} MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<{p['bug_d9_tbg_max_k']} K")
    L.append("")
    L.append("## Setups")
    L.append("")
    L.append("| Setup | §267-273 first_pass | §267-273 pathD | K1 retire | Data source |")
    L.append("|---|---|---|---|---|")
    L.append("| baseline | ON | OFF | OFF | `data/mirova_equivalent/` |")
    L.append("| F2.1     | ON | OFF | ON  | `data/mirova_equivalent_unsuitable_filters_v1/` |")
    L.append("| A/B-1    | ON | **ON** | OFF | extracted from commit `dc4b286` |")
    L.append("| A/B-2    | OFF | OFF | ON  | extracted from commit `a775a7d` |")
    L.append("")
    L.append("## Per-volcano 4-way (recall / precision / ratio_med / D9_bug / det)")
    L.append("")
    L.append("| Volcan | n_alert | Setup | n_det | TP | FP | FN | Recall | Prec | Ratio | D9 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        na = pv.get("n_alerts_in_window", 0)
        for s in setups:
            r = pv.get(s, {})
            if "error" in r:
                L.append(f"| {vol} | {na} | {s} | MISSING | | | | | | | |")
                continue
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            L.append(f"| {vol} | {na} | {s} | {r['n_records_detection']} | {r['tp']} | {r['fp']} | {r['fn']} | {rec} | {prc} | {rmd} | {r['bug_d9_count']} |")
    L.append("")
    L.append("## Deltas vs baseline (recall / D9)")
    L.append("")
    L.append("| Volcan | dRecall F2.1 | dRecall A/B-1 | dRecall A/B-2 | dD9 F2.1 | dD9 A/B-1 | dD9 A/B-2 |")
    L.append("|---|---|---|---|---|---|---|")

    def diff_r(a, b):
        if a is None or b is None:
            return "-"
        return f"{(a - b):+.3f}"

    common_vols = []
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        b = pv.get("baseline", {})
        f1 = pv.get("f21", {})
        a1 = pv.get("ab1", {})
        a2 = pv.get("ab2", {})
        if "error" in b:
            L.append(f"| {vol} | base-MISSING | | | | | |")
            continue
        def dr(x):
            if "error" in x or x.get("recall") is None:
                return "MISSING"
            return diff_r(x["recall"], b["recall"])
        def dd(x):
            if "error" in x:
                return "MISSING"
            return f"{x['bug_d9_count'] - b['bug_d9_count']:+d}"
        L.append(f"| {vol} | {dr(f1)} | {dr(a1)} | {dr(a2)} | {dd(f1)} | {dd(a1)} | {dd(a2)} |")
        # common = vol available in all 4 setups
        if all("error" not in x for x in [b, f1, a1, a2]):
            common_vols.append(vol)

    L.append("")
    L.append(f"## Cross-comparison fairness: vols comunes a los 4 setups = {len(common_vols)}")
    L.append(f"  {', '.join(common_vols)}")
    L.append("")
    L.append("Exclusiones (missing en al menos 1 setup):")
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        miss = [s for s in setups if "error" in pv.get(s, {})]
        if miss:
            L.append(f"  - {vol}: missing in {miss}")
    L.append("")

    # Lascar regression analysis
    lascar = out["per_volcano"].get("Lascar", {})
    L.append("## Lascar regression analysis (focus)")
    L.append("")
    L.append("| Setup | Recall | dRecall vs baseline | D9_bug | Diagnosis flag |")
    L.append("|---|---|---|---|---|")
    base_rec = lascar.get("baseline", {}).get("recall")
    for s in setups:
        r = lascar.get(s, {})
        if "error" in r:
            continue
        rec = r["recall"]
        d = rec - base_rec if (rec is not None and base_rec is not None) else None
        d_s = f"{d:+.3f}" if d is not None else "-"
        flag = ""
        if d is not None:
            if d < -0.05:
                flag = "REGRESS >5pp"
            elif d > 0.05:
                flag = "IMPROVE >5pp"
            else:
                flag = "stable"
        L.append(f"| {s} | {rec:.3f} | {d_s} | {r['bug_d9_count']} | {flag} |")
    L.append("")

    # Verdict logic
    L.append("## Verdict")
    L.append("")
    rec_b = lascar.get("baseline", {}).get("recall")
    rec_f1 = lascar.get("f21", {}).get("recall")
    rec_a1 = lascar.get("ab1", {}).get("recall")
    rec_a2 = lascar.get("ab2", {}).get("recall")
    def regress(r):
        if r is None or rec_b is None:
            return None
        return (rec_b - r) > 0.05
    f1_reg = regress(rec_f1)
    a1_reg = regress(rec_a1)
    a2_reg = regress(rec_a2)
    L.append(f"- F2.1 Lascar regression: {f1_reg}")
    L.append(f"- A/B-1 Lascar regression (§267-273 pathD only): {a1_reg}")
    L.append(f"- A/B-2 Lascar regression (K1 retire only): {a2_reg}")
    L.append("")
    if a1_reg is False and a2_reg is True:
        verdict = "**K1 retire (§298-300) ES EL CULPABLE.** A/B-1 (sin K1) preserva recall Lascar; A/B-2 (solo K1) reproduce regress. Adoptar §267-273 pathD extendido (A/B-1) como fix sin K1."
    elif a1_reg is True and a2_reg is False:
        verdict = "**§267-273 pathD ES EL CULPABLE.** A/B-1 (con pathD) regresa; A/B-2 (sin pathD, solo K1) preserva. NO adoptar pathD; investigar K1 standalone."
    elif a1_reg is True and a2_reg is True:
        verdict = "**AMBOS CONTRIBUYEN.** Tanto pathD como K1 reducen recall Lascar individualmente. Ningún subset es adoptable sin más investigación; revisar implementación de cada feature contra papers."
    elif a1_reg is False and a2_reg is False:
        verdict = "**INTERACCIÓN.** Ningún feature individual regresa Lascar; la combinación F2.1 sí. Adoptar el que mejore más D9 (preferir A/B-1 por extender pathD)."
    else:
        verdict = "**INDETERMINADO** — falta data para alguna celda crítica."
    L.append(verdict)
    L.append("")

    # Adoption criteria checks per setup
    L.append("## Adopción S33 (criterio relajado por sample reducido)")
    L.append("")
    L.append("Criterios:")
    L.append("- Bug D9 drop >50% en ≥5/N vols (N = common vols).")
    L.append("- Recall NO degrada >5pp en ningún vol con n_mirova≥10.")
    L.append("- Precision NO degrada en ningún vol.")
    L.append("")
    L.append("| Setup | Vols con D9>0 base | D9 drop≥50% | Recall OK (n≥10) | Prec no-degrade | Pasa criterio |")
    L.append("|---|---|---|---|---|---|")
    for s in ["f21", "ab1", "ab2"]:
        n_d9_base = 0
        n_d9_drop = 0
        n_recall_elig = 0
        n_recall_ok = 0
        n_prec_elig = 0
        n_prec_ok = 0
        for vol in common_vols:
            pv = out["per_volcano"][vol]
            b = pv["baseline"]
            a = pv[s]
            if b["bug_d9_count"] > 0:
                n_d9_base += 1
                if (b["bug_d9_count"] - a["bug_d9_count"]) / b["bug_d9_count"] >= 0.5:
                    n_d9_drop += 1
            n_mir = a["tp"] + a["fn"]
            if n_mir >= 10 and a["recall"] is not None and b["recall"] is not None:
                n_recall_elig += 1
                if (b["recall"] - a["recall"]) <= 0.05:
                    n_recall_ok += 1
            if a["precision"] is not None and b["precision"] is not None:
                n_prec_elig += 1
                if a["precision"] >= b["precision"] - 1e-9:
                    n_prec_ok += 1
        passes = (n_d9_drop >= 5 and n_recall_ok == n_recall_elig and n_prec_ok == n_prec_elig)
        L.append(f"| {s} | {n_d9_base} | {n_d9_drop} | {n_recall_ok}/{n_recall_elig} | {n_prec_ok}/{n_prec_elig} | {'YES' if passes else 'NO'} |")
    L.append("")
    L.append("Notas:")
    L.append("- F2.1 = combo (pathD OFF, K1 ON) — replica condicion testeada F2.2.")
    L.append("- A/B-1 = pathD ON, K1 OFF — aisla §267-273 firstpass + extension.")
    L.append("- A/B-2 = K1 ON solo — aisla retire mechanism.")
    L.append("- NdC missing en F2.1 + A/B-1 + A/B-2 (failures workflow).")
    L.append("- Chaiten missing en A/B-1 (failure workflow run 26258435593).")
    L.append("- PCC missing en A/B-2 (failure workflow run 26258437263).")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
