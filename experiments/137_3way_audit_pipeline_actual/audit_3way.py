"""
S72 F2.7 - 3-way A/B audit at SAME pipeline SHA (post-PR #126 merge).

Setups (all produced by same code, only profile flags differ):
  - operacional   : data/mirova_equivalent             (cap S71 ON, bt_path OFF, all S38-S71 adoptions)
  - no_cap_v1     : data/mirova_equivalent_no_cap_v1   (cap S71 OFF, rest identical to operacional)
  - bt_path_on_v1 : data/mirova_equivalent_bt_path_on_v1 (bt_path ON [revert S40], rest identical)

Sample: intersection of 11 Tier A vols available in all 3 setups.
  no_cap_v1 missing: Lascar, Villarrica (workflow failures F2.6.b).
  bt_path_on_v1: 11 present (F2.6.e had 0 failures).
  -> 3-way intersection = 9 vols.

Metric defs reused from experiments/133 (sensor-aware ±60min per-record,
pc.vrp_mw convention A4, bug D9 contextual-only @ t_bg<260K).

Window: 2026-02-20 -> 2026-05-20 (90d, matches F2.6 reproc range).

Questions:
  Q1: Is cap S71 still adding value? (operacional vs no_cap)
  Q2: Does bt_path_on inflate Lascar magnitude as F2.6.c predicted at 100%?
       -> Lascar excluded from intersection but reported standalone.
  Q3: Any vol where alt setup beats operacional?
"""
from __future__ import annotations

import calendar
import json
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
    "operacional":  ROOT / "data" / "mirova_equivalent",
    "no_cap":       ROOT / "data" / "mirova_equivalent_no_cap_v1",
    "bt_path_on":   ROOT / "data" / "mirova_equivalent_bt_path_on_v1",
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


def count_d9_capped(records, window_start_ts, window_end_ts):
    """Count records that were capped by S71 cap (only meaningful in operacional).
    Heuristic: presence of cap diagnostic field. Look for 'd9_capped' or similar."""
    n = 0
    for r in records or []:
        rts = parse_record_ts(r.get("datetime_utc"))
        if rts is None or not (window_start_ts <= rts <= window_end_ts):
            continue
        # Try common diagnostic flag names
        if r.get("d9_capped") or r.get("vrp_d9_capped") or r.get("cap_s71_applied"):
            n += 1
    return n


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
    d9_capped = 0
    vrp_values_detected = []
    for rts, r in in_recs:
        sf = sensor_family(r.get("sensor", ""))
        detected = has_detection(r)
        if detected:
            n_detect += 1
            eqv = get_eqvrp_mw(r)
            vrp_values_detected.append(eqv)
            m = find_match(rts, sf, alerts_vol)
            if m is not None:
                tp += 1
                matched_alert_idxs.add(m.name)
                if m["VRP_MW"] and m["VRP_MW"] > 0:
                    if eqv > 0:
                        try:
                            ratios.append(eqv / float(m["VRP_MW"]))
                        except (ValueError, TypeError):
                            pass
            else:
                fp += 1
        if is_d9_bug(r):
            bug_d9 += 1
        if r.get("d9_capped") or r.get("vrp_d9_capped") or r.get("cap_s71_applied"):
            d9_capped += 1
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
    vrp_max = max(vrp_values_detected) if vrp_values_detected else None
    vrp_med = median(vrp_values_detected) if vrp_values_detected else None
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
        "d9_capped_count": d9_capped,
        "vrp_max_detected": vrp_max,
        "vrp_median_detected": vrp_med,
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
    setups = ["operacional", "no_cap", "bt_path_on"]
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
            vmax = f"{r['vrp_max_detected']:.1f}" if r["vrp_max_detected"] is not None else "-"
            return (f"r={rec} p={prc} rat={rmd} D9={r['bug_d9_count']} cap={r['d9_capped_count']}"
                    f" det={r['n_records_detection']} vmax={vmax}")
        print(f"[{vol}] alerts={len(al_v)}")
        for s in setups:
            print(f"   {s:11s}: {fmt(res[s])}")

    out_json = OUT_DIR / "audit_3way.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[wrote {out_json}]")

    md = render_report(out)
    out_md = OUT_DIR / "audit.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote {out_md}]")


def render_report(out):
    L = []
    p = out["params"]
    setups = ["operacional", "no_cap", "bt_path_on"]
    L.append("# S72 F2.7 - 3-way audit pipeline actual (post-PR #126)")
    L.append("")
    L.append(f"Ventana: {p['window_start'][:10]} -> {p['window_end'][:10]} (90d)")
    L.append(f"Matching MIROVA: +/-{int(p['match_tol_min'])} min sensor-aware (per-record, CONS+OCR ALERTAs)")
    L.append(f"Bug D9: pc.vrp_mw>{p['bug_d9_vrp_min_mw']} MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<{p['bug_d9_tbg_max_k']} K")
    L.append("")
    L.append("## Setups (mismo SHA, solo difiere 1 flag)")
    L.append("")
    L.append("| Setup | cap S71 | bt_path_hot | Otras features S38-S71 | Source |")
    L.append("|---|---|---|---|---|")
    L.append("| operacional   | **ON**  | OFF (S40 revert) | todas adopciones | `data/mirova_equivalent/` |")
    L.append("| no_cap        | **OFF** | OFF              | todas adopciones | `data/mirova_equivalent_no_cap_v1/` |")
    L.append("| bt_path_on    | ON      | **ON** (S40 reverted) | todas adopciones | `data/mirova_equivalent_bt_path_on_v1/` |")
    L.append("")
    L.append("## Per-volcano 3-way")
    L.append("")
    L.append("| Volcan | n_alert | Setup | n_det | TP | FP | FN | Recall | Prec | Ratio | D9 | cap | vmax(MW) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        na = pv.get("n_alerts_in_window", 0)
        for s in setups:
            r = pv.get(s, {})
            if "error" in r:
                L.append(f"| {vol} | {na} | {s} | MISSING | | | | | | | | | |")
                continue
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            vmax = f"{r['vrp_max_detected']:.1f}" if r["vrp_max_detected"] is not None else "-"
            L.append(
                f"| {vol} | {na} | {s} | {r['n_records_detection']} | {r['tp']} | {r['fp']} | {r['fn']} | "
                f"{rec} | {prc} | {rmd} | {r['bug_d9_count']} | {r['d9_capped_count']} | {vmax} |"
            )
    L.append("")

    # Intersection (9 vols)
    common_vols = [v for v in TIER_A
                   if all("error" not in out["per_volcano"][v].get(s, {}) for s in setups)]
    L.append(f"## Intersection 3-setup = {len(common_vols)} vols")
    L.append(f"  {', '.join(common_vols)}")
    L.append("")
    L.append("Excluded (missing in at least 1 setup):")
    for vol in TIER_A:
        pv = out["per_volcano"][vol]
        miss = [s for s in setups if "error" in pv.get(s, {})]
        if miss:
            L.append(f"  - {vol}: missing in {miss}")
    L.append("")

    # Deltas vs operacional
    L.append("## Deltas vs operacional (intersection only)")
    L.append("")
    L.append("| Volcan | dRecall no_cap | dRecall bt_on | dRatio no_cap | dRatio bt_on | dD9 no_cap | dD9 bt_on | dVmax no_cap | dVmax bt_on |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    def diff(a, b, fmt="{:+.3f}"):
        if a is None or b is None:
            return "-"
        return fmt.format(a - b)
    for vol in common_vols:
        pv = out["per_volcano"][vol]
        op = pv["operacional"]
        nc = pv["no_cap"]
        bt = pv["bt_path_on"]
        L.append(
            f"| {vol} | {diff(nc['recall'], op['recall'])} | {diff(bt['recall'], op['recall'])} | "
            f"{diff(nc['ratio_median'], op['ratio_median'], '{:+.2f}')} | "
            f"{diff(bt['ratio_median'], op['ratio_median'], '{:+.2f}')} | "
            f"{nc['bug_d9_count'] - op['bug_d9_count']:+d} | "
            f"{bt['bug_d9_count'] - op['bug_d9_count']:+d} | "
            f"{diff(nc['vrp_max_detected'], op['vrp_max_detected'], '{:+.1f}')} | "
            f"{diff(bt['vrp_max_detected'], op['vrp_max_detected'], '{:+.1f}')} |"
        )
    L.append("")

    # Byte-equivalence operacional vs no_cap
    L.append("## Q1: Cap S71 aporta algo operacionalmente?")
    L.append("")
    diffs_q1 = []
    for vol in common_vols:
        pv = out["per_volcano"][vol]
        op = pv["operacional"]
        nc = pv["no_cap"]
        same_n = op["n_records_in_window"] == nc["n_records_in_window"]
        same_det = op["n_records_detection"] == nc["n_records_detection"]
        same_tp = op["tp"] == nc["tp"]
        same_fp = op["fp"] == nc["fp"]
        same_d9 = op["bug_d9_count"] == nc["bug_d9_count"]
        # vrp_max diff signals cap action
        vmax_diff = None
        if op["vrp_max_detected"] is not None and nc["vrp_max_detected"] is not None:
            vmax_diff = nc["vrp_max_detected"] - op["vrp_max_detected"]
        identical = all([same_n, same_det, same_tp, same_fp, same_d9]) and (vmax_diff is None or abs(vmax_diff) < 0.01)
        diffs_q1.append((vol, identical, vmax_diff, op["bug_d9_count"], nc["bug_d9_count"]))
        L.append(f"- **{vol}**: identical={identical} | dVmax={vmax_diff} | D9 op={op['bug_d9_count']} no_cap={nc['bug_d9_count']}")
    n_identical = sum(1 for _, ident, *_ in diffs_q1 if ident)
    L.append("")
    L.append(f"**Resumen Q1**: {n_identical}/{len(common_vols)} vols son identicos op vs no_cap.")
    if n_identical == len(common_vols):
        q1_verdict = "Cap S71 NO produce diferencia observable en ningun vol intersection. Otras features S38-S71 ya absorben el caso. Considerar REMOVE cap (mantenibilidad)."
    else:
        # Check D9 direction
        d9_worse_no_cap = sum(1 for _, _, _, d9o, d9n in diffs_q1 if d9n > d9o)
        if d9_worse_no_cap > 0:
            q1_verdict = f"Cap S71 SI aporta: {d9_worse_no_cap} vols muestran D9 mas alto sin cap. MANTENER."
        else:
            q1_verdict = "Cap S71 produce diferencias pero NO en bug D9. Evaluar caso a caso si vale la pena mantener."
    L.append(f"**Veredicto Q1**: {q1_verdict}")
    L.append("")

    # Q2: bt_path_on Lascar
    L.append("## Q2: bt_path_on infla magnitud Lascar?")
    L.append("")
    lascar = out["per_volcano"].get("Lascar", {})
    op_l = lascar.get("operacional", {})
    bt_l = lascar.get("bt_path_on", {})
    nc_l = lascar.get("no_cap", {})
    if "error" not in op_l and "error" not in bt_l:
        L.append(f"- operacional Lascar: vmax={op_l.get('vrp_max_detected')} MW, vmed={op_l.get('vrp_median_detected')} MW, det={op_l['n_records_detection']}, FP={op_l['fp']}, recall={op_l['recall']:.3f}, ratio={op_l['ratio_median']:.2f}")
        L.append(f"- bt_path_on Lascar:  vmax={bt_l.get('vrp_max_detected')} MW, vmed={bt_l.get('vrp_median_detected')} MW, det={bt_l['n_records_detection']}, FP={bt_l['fp']}, recall={bt_l['recall']:.3f}, ratio={bt_l['ratio_median']:.2f}")
        if "error" not in nc_l:
            L.append(f"- no_cap Lascar:      MISSING (workflow failure F2.6.b)")
        else:
            L.append(f"- no_cap Lascar:      MISSING (workflow failure F2.6.b)")
        if op_l.get("vrp_max_detected") and bt_l.get("vrp_max_detected"):
            mult = bt_l["vrp_max_detected"] / op_l["vrp_max_detected"]
            L.append("")
            L.append(f"**Vmax bt_path_on / operacional = {mult:.2f}x**  (esperado >>1 si F2.6.c rank 1 confirmado)")
            if mult > 5:
                q2_verdict = f"CONFIRMA F2.6.c al 100%: bt_path_on infla vmax {mult:.1f}x ({op_l['vrp_max_detected']:.1f} -> {bt_l['vrp_max_detected']:.1f} MW). S40 fue mejora real, NO revertir."
            elif mult > 1.5:
                q2_verdict = f"Inflacion parcial ({mult:.2f}x). bt_path contribuye pero no es unica fuente; otras features absorben caso parcialmente."
            else:
                q2_verdict = f"NO confirma F2.6.c: bt_path_on NO infla magnitud significativamente ({mult:.2f}x). Otra feature S38-S46 hizo el trabajo."
        else:
            q2_verdict = "INDETERMINADO (vmax missing)"
    else:
        q2_verdict = "Lascar missing en setup necesario"
    L.append(f"**Veredicto Q2**: {q2_verdict}")
    L.append("")

    # Q3: Any vol where alt setup beats operacional?
    L.append("## Q3: Hay vols donde no_cap o bt_path_on dan MEJORES resultados?")
    L.append("")
    L.append("| Volcan | Mejor recall | Mejor ratio (closest to 1) | Mejor precision |")
    L.append("|---|---|---|---|")
    q3_findings = []
    for vol in common_vols:
        pv = out["per_volcano"][vol]
        def safe(d, k):
            v = d.get(k)
            return v if v is not None else float("nan")
        # Best recall
        recs = {s: safe(pv[s], "recall") for s in setups}
        recs_valid = {k: v for k, v in recs.items() if v == v}  # filter nan
        best_rec = max(recs_valid, key=recs_valid.get) if recs_valid else "-"
        # Best ratio (closest to 1)
        rats = {s: safe(pv[s], "ratio_median") for s in setups}
        rats_valid = {k: v for k, v in rats.items() if v == v}
        best_rat = min(rats_valid, key=lambda k: abs(rats_valid[k] - 1.0)) if rats_valid else "-"
        # Best precision
        pres = {s: safe(pv[s], "precision") for s in setups}
        pres_valid = {k: v for k, v in pres.items() if v == v}
        best_pre = max(pres_valid, key=pres_valid.get) if pres_valid else "-"
        rec_v = recs_valid.get(best_rec)
        rat_v = rats_valid.get(best_rat)
        pre_v = pres_valid.get(best_pre)
        rec_str = f"{rec_v:.2f}" if isinstance(rec_v, float) else "-"
        rat_str = f"{rat_v:.2f}" if isinstance(rat_v, float) else "-"
        pre_str = f"{pre_v:.2f}" if isinstance(pre_v, float) else "-"
        L.append(f"| {vol} | {best_rec} ({rec_str}) | {best_rat} ({rat_str}) | {best_pre} ({pre_str}) |")
        if best_rec != "operacional" or best_rat != "operacional":
            q3_findings.append((vol, best_rec, best_rat, best_pre))
    L.append("")
    if not q3_findings:
        q3_verdict = "Operacional gana o empata en todos los vols intersection. NO hay caso per-vol opt-in para no_cap ni bt_path_on."
    else:
        q3_verdict = f"{len(q3_findings)} vols con algun metric superior en setup alternativo: ver tabla arriba. Considerar per-vol opt-in caso a caso, pero verificar trade-offs (recall vs FP)."
    L.append(f"**Veredicto Q3**: {q3_verdict}")
    L.append("")

    # Final recommendation
    L.append("## Recomendacion adopcion S72 cierre")
    L.append("")
    L.append(f"- **Cap S71**: {q1_verdict}")
    L.append(f"- **bt_path_hot (S40)**: {q2_verdict}")
    L.append(f"- **Per-vol opt-in**: {q3_verdict}")
    L.append("")

    return "\n".join(L)


if __name__ == "__main__":
    main()
