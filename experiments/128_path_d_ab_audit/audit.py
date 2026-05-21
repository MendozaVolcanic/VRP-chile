"""
S71 T1 F2.d - Audit cruzado de las 3 opciones path D fix D9.

Compara baseline (mirova_equivalent) vs:
  A: atm_gate_v1 (skip path D si t_bg<265K)
  B: covalidation_v1 (path D requiere BT o NTI duro)
  C: cap_v1 (cap vrp_mw 5MW si ctx-only + t_bg<270K)

Ventana: interseccion de fechas presentes en los 3 experimentos (~ Feb20-May20).
Tier A: 11 vols.

Metricas per (opcion, vol):
- N records con deteccion (n_anomalous_pixels>0)
- TP/FP/FN vs MIROVA NRT (CONS+OCR ALERTA, ±3h)
- recall, precision
- ratio mediano pc.vrp_mw / MIROVA vrp_mw (cuando ambos detectan)
- conteo path-D-only con eqVrp>5 MW (proxy del bug D9)
- conteo cap aplicado (Opcion C)

Output:
  audit.json (metricas brutas)
  audit_report.md (tablas + verdict)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from statistics import median

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

TIER_A = [
    "Lastarria", "Lascar", "Isluga", "Villarrica", "Chaiten",
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
    "NevadosDeChillan": ["Nevados de Chillan"],
}

CONS_CSV = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR_CSV = ROOT / "data" / "mirova_reference" / "registro_vrp_ocr.csv"

OPTIONS = {
    "baseline": ROOT / "data" / "mirova_equivalent",
    "A_atm_gate": ROOT / "data" / "mirova_equivalent_path_d_atm_gate_v1",
    "B_covalidation": ROOT / "data" / "mirova_equivalent_path_d_covalidation_v1",
    "C_cap": ROOT / "data" / "mirova_equivalent_path_d_cap_v1",
}

MATCH_TOL_HOURS = 3.0
EQVRP_MIN_MW = 5.0


def load_mirova_alerts() -> pd.DataFrame:
    cons = pd.read_csv(CONS_CSV)
    ocr = pd.read_csv(OCR_CSV)
    cons_a = cons[cons["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)].copy()
    ocr_a = ocr[ocr["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)].copy()
    cons_a["source"] = "CONS"
    ocr_a["source"] = "OCR"
    common = ["timestamp", "Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Tipo_Registro", "source"]
    alerts = pd.concat([cons_a[common], ocr_a[common]], ignore_index=True)
    alerts["timestamp"] = pd.to_numeric(alerts["timestamp"], errors="coerce")
    alerts = alerts.dropna(subset=["timestamp"]).reset_index(drop=True)
    alerts["VRP_MW"] = pd.to_numeric(alerts["VRP_MW"], errors="coerce")
    return alerts


def parse_record_dt(dt_str):
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
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
    """Record cuenta como deteccion si n_anomalous_pixels>0 o pc.vrp_mw>0."""
    npx = rec.get("n_anomalous_pixels") or 0
    if npx > 0:
        return True
    eqv = get_eqvrp_mw(rec)
    return eqv > 0.01


def is_path_d_only(rec):
    bt = rec.get("diag_n_bt_path", 0) or 0
    nti = rec.get("diag_n_nti_path", 0) or 0
    dnti = rec.get("diag_n_dnti_ctx_path", 0) or 0
    nti_rel = rec.get("n_nti_rel_path", 0) or 0
    return (bt == 0) and (nti == 0) and (nti_rel == 0) and (dnti > 0)


def find_mirova_match(rec_dt, vol_csv_names, alerts):
    """Return MIROVA alert match (row) within tolerance, or None."""
    ts_target = rec_dt.timestamp()
    tol = MATCH_TOL_HOURS * 3600
    sub = alerts[alerts["Volcan"].isin(vol_csv_names)]
    if sub.empty:
        return None
    diffs = (sub["timestamp"].astype(float) - ts_target).abs()
    mask = diffs <= tol
    if not mask.any():
        return None
    idx = diffs[mask].idxmin()
    return sub.loc[idx]


def night_key(rec_dt):
    """Volcanic 'night' key: yyyy-mm-dd of the local night (UTC).
    For Chile we use UTC date; MIROVA aggregates by satellite night ~UTC.
    """
    return rec_dt.strftime("%Y-%m-%d")


def audit_volcano(vol, alerts, shared_dts):
    """Per-volcano metrics for each option."""
    vol_csv_names = VOL_CSV_MAP.get(vol, [vol])
    # Load records per option
    opts_records = {}
    for opt, dir_ in OPTIONS.items():
        fp = dir_ / f"{vol}.json"
        if not fp.exists():
            opts_records[opt] = None
            continue
        with open(fp) as f:
            d = json.load(f)
        opts_records[opt] = {r["datetime_utc"]: r for r in d.get("records", []) if r.get("datetime_utc")}

    # MIROVA alerts in shared date window (per-night truth set)
    if shared_dts:
        sorted_dts = sorted(shared_dts)
        min_dt = parse_record_dt(sorted_dts[0])
        max_dt = parse_record_dt(sorted_dts[-1])
    else:
        min_dt = max_dt = None

    alerts_vol = alerts[alerts["Volcan"].isin(vol_csv_names)].copy()
    if min_dt is not None:
        alerts_vol = alerts_vol[
            (alerts_vol["timestamp"] >= min_dt.timestamp() - MATCH_TOL_HOURS*3600) &
            (alerts_vol["timestamp"] <= max_dt.timestamp() + MATCH_TOL_HOURS*3600)
        ].copy()
    alerts_vol["night"] = pd.to_datetime(alerts_vol["timestamp"], unit="s").dt.strftime("%Y-%m-%d")
    mirova_nights = set(alerts_vol["night"].dropna().unique())

    results = {}
    for opt in OPTIONS:
        recs_by_dt = opts_records[opt]
        if recs_by_dt is None:
            results[opt] = {"error": "json_missing"}
            continue

        # Restrict to shared window dts
        recs = [recs_by_dt[dt] for dt in shared_dts if dt in recs_by_dt]

        n_total = len(recs)
        n_detect = 0
        ratios = []  # pc.vrp_mw / mirova VRP
        path_d_only_high = 0  # path-D-only with eqVrp > 5 MW
        path_d_only_high_low_tbg = 0  # the bug subset (path-D-only + eqVrp>5MW + t_bg<260K)
        cap_count = 0  # records where vrp_mw differs from baseline because cap

        nights_with_detection = set()
        detection_to_mirova = {}  # night -> bool (matched mirova)

        for rec in recs:
            rec_dt = parse_record_dt(rec.get("datetime_utc"))
            if rec_dt is None:
                continue
            night = night_key(rec_dt)
            eqvrp = get_eqvrp_mw(rec)
            detected = has_detection(rec)
            if detected:
                n_detect += 1
                nights_with_detection.add(night)
            # Path D-only diagnostic
            if is_path_d_only(rec) and eqvrp > EQVRP_MIN_MW:
                path_d_only_high += 1
                tbg = rec.get("t_bg_k")
                try:
                    if tbg is not None and float(tbg) < 260.0:
                        path_d_only_high_low_tbg += 1
                except (ValueError, TypeError):
                    pass
            # Ratio cuando ambos detectan
            if detected and eqvrp > 0.01:
                mat = find_mirova_match(rec_dt, vol_csv_names, alerts_vol)
                if mat is not None and mat["VRP_MW"] and mat["VRP_MW"] > 0:
                    try:
                        ratios.append(eqvrp / float(mat["VRP_MW"]))
                    except (ValueError, TypeError):
                        pass

        # TP/FP/FN aggregated by NIGHT (paridad con MIROVA cluster cadence)
        # TP: night with detection AND mirova ALERTA
        # FP: night with detection AND no mirova
        # FN: night with mirova ALERTA AND no detection in our pipeline
        # Limit denominators to nights present in shared window (where we have data)
        our_nights = nights_with_detection
        # nights covered by VRP records (any record present, regardless of detection)
        covered_nights = set()
        for rec in recs:
            rec_dt = parse_record_dt(rec.get("datetime_utc"))
            if rec_dt:
                covered_nights.add(night_key(rec_dt))

        tp = len(our_nights & mirova_nights)
        fp = len(our_nights - mirova_nights)
        # FN: mirova nights inside our covered nights but we missed them
        fn = len((mirova_nights & covered_nights) - our_nights)
        # MIROVA nights outside our coverage are NOT FN (we have no data)

        recall = tp / (tp + fn) if (tp + fn) > 0 else None
        precision = tp / (tp + fp) if (tp + fp) > 0 else None

        ratio_median = median(ratios) if ratios else None

        results[opt] = {
            "n_records_in_window": n_total,
            "n_records_detection": n_detect,
            "tp_nights": tp,
            "fp_nights": fp,
            "fn_nights": fn,
            "mirova_nights_total": len(mirova_nights & covered_nights),
            "covered_nights": len(covered_nights),
            "recall": recall,
            "precision": precision,
            "ratio_median": ratio_median,
            "ratio_n": len(ratios),
            "path_d_only_eqvrp_gt5": path_d_only_high,
            "path_d_only_high_low_tbg": path_d_only_high_low_tbg,
        }

    return results


def compute_shared_dts(vol):
    """Datetimes shared across the 3 experiment options for this vol."""
    sets = []
    for opt in ("A_atm_gate", "B_covalidation", "C_cap"):
        fp = OPTIONS[opt] / f"{vol}.json"
        if not fp.exists():
            return set()
        with open(fp) as f:
            d = json.load(f)
        sets.append({r["datetime_utc"] for r in d.get("records", []) if r.get("datetime_utc")})
    if not sets:
        return set()
    inter = sets[0]
    for s in sets[1:]:
        inter &= s
    return inter


def main():
    print("[loading MIROVA alerts]")
    alerts = load_mirova_alerts()
    print(f"  total ALERTA rows: {len(alerts)}")

    out = {"params": {
        "MATCH_TOL_HOURS": MATCH_TOL_HOURS,
        "EQVRP_MIN_MW_BUG": EQVRP_MIN_MW,
        "tier_a": TIER_A,
    }, "per_volcano": {}}

    for vol in TIER_A:
        print(f"[{vol}]")
        shared = compute_shared_dts(vol)
        if not shared:
            print(f"  WARN: no shared dts (likely missing dataset)")
            out["per_volcano"][vol] = {"error": "no_shared_dts"}
            continue
        res = audit_volcano(vol, alerts, shared)
        # Include baseline-restricted-to-window too for fair comparison
        out["per_volcano"][vol] = {
            "n_shared_dts": len(shared),
            "results": res,
        }
        for opt, r in res.items():
            if "error" in r:
                print(f"  {opt}: {r['error']}")
                continue
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prec = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmed = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            print(f"  {opt}: TP={r['tp_nights']} FP={r['fp_nights']} FN={r['fn_nights']} rec={rec} pre={prec} ratio_med={rmed} pD-only>{EQVRP_MIN_MW}={r['path_d_only_eqvrp_gt5']}")

    # Write JSON
    with open(OUT_DIR / "audit.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[wrote {OUT_DIR/'audit.json'}]")

    # Write Markdown report
    write_report(out, OUT_DIR / "audit_report.md")
    print(f"[wrote {OUT_DIR/'audit_report.md'}]")


def write_report(out, path):
    lines = []
    lines.append("# Audit cruzado D9 path D fix - 3 opciones (S71 T1 F2.d)")
    lines.append("")
    lines.append(f"Tolerancia matching MIROVA: ±{out['params']['MATCH_TOL_HOURS']}h (CONS+OCR ALERTA). "
                 f"Ventana: interseccion fechas en los 3 experimentos (~ Feb20-May20, 90d).")
    lines.append("")
    lines.append("## Resumen por volcan: recall / precision / ratio mediano")
    lines.append("")
    lines.append("| Volcan | Opcion | TP | FP | FN | Recall | Precision | Ratio_med | N_ratio | pD-only>5MW | pD>5_tbg<260 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        if "error" in pv:
            lines.append(f"| {vol} | - | {pv['error']} | | | | | | | | |")
            continue
        for opt in ("baseline", "A_atm_gate", "B_covalidation", "C_cap"):
            r = pv["results"].get(opt, {})
            if "error" in r:
                lines.append(f"| {vol} | {opt} | {r['error']} | | | | | | | | |")
                continue
            rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
            prec = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
            rmed = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
            lines.append(f"| {vol} | {opt} | {r['tp_nights']} | {r['fp_nights']} | {r['fn_nights']} | {rec} | {prec} | {rmed} | {r['ratio_n']} | {r['path_d_only_eqvrp_gt5']} | {r['path_d_only_high_low_tbg']} |")
    lines.append("")
    # Delta tables
    lines.append("## Delta vs baseline (recall_keep, precision_gain, ratio_change)")
    lines.append("")
    lines.append("| Volcan | Opcion | dRecall | dPrecision | dRatio | pD-only_drop |")
    lines.append("|---|---|---|---|---|---|")
    for vol in TIER_A:
        pv = out["per_volcano"].get(vol, {})
        if "error" in pv:
            continue
        b = pv["results"].get("baseline", {})
        if "error" in b:
            continue
        for opt in ("A_atm_gate", "B_covalidation", "C_cap"):
            r = pv["results"].get(opt, {})
            if "error" in r:
                continue
            def diff(a, c):
                if a is None or c is None: return "-"
                return f"{(a-c):+.2f}"
            d_rec = diff(r["recall"], b["recall"])
            d_pre = diff(r["precision"], b["precision"])
            d_rat = diff(r["ratio_median"], b["ratio_median"])
            pD_drop = (b["path_d_only_eqvrp_gt5"] - r["path_d_only_eqvrp_gt5"])
            lines.append(f"| {vol} | {opt} | {d_rec} | {d_pre} | {d_rat} | {pD_drop} |")
    lines.append("")
    # Aggregate criteria
    lines.append("## Cumplimiento de criterios per opcion")
    lines.append("")
    lines.append("Criterios (BLOQUE_ARRANQUE_S71):")
    lines.append("- Mediana ratio per-vol ∈ [0.5, 2.0]")
    lines.append("- Recall ≥0.70 per vol Tier A con N≥10 MIROVA ALERTAS")
    lines.append("- Precision ≥0.50 per vol Tier A")
    lines.append("- Ningun record pD-only con eqVrp>5MW + t_bg<260K")
    lines.append("")
    lines.append("| Opcion | Vols ratio∈[0.5,2] | Vols recall≥0.7 (n_mirova≥10) | Vols precision≥0.5 | Σ pD-only_eqVrp>5 + tbg<260 |")
    lines.append("|---|---|---|---|---|")
    for opt in ("baseline", "A_atm_gate", "B_covalidation", "C_cap"):
        n_ok_ratio = 0
        n_ok_recall = 0; n_recall_eligible = 0
        n_ok_prec = 0; n_prec_eligible = 0
        sum_bug = 0
        for vol in TIER_A:
            pv = out["per_volcano"].get(vol, {})
            if "error" in pv: continue
            r = pv["results"].get(opt, {})
            if "error" in r: continue
            if r["ratio_median"] is not None and 0.5 <= r["ratio_median"] <= 2.0:
                n_ok_ratio += 1
            if r["mirova_nights_total"] >= 10 and r["recall"] is not None:
                n_recall_eligible += 1
                if r["recall"] >= 0.70:
                    n_ok_recall += 1
            if r["precision"] is not None:
                n_prec_eligible += 1
                if r["precision"] >= 0.50:
                    n_ok_prec += 1
            sum_bug += r["path_d_only_high_low_tbg"]
        lines.append(f"| {opt} | {n_ok_ratio}/11 | {n_ok_recall}/{n_recall_eligible} | {n_ok_prec}/{n_prec_eligible} | {sum_bug} |")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("Ver tablas. La decision se documenta en el reporte inline (chat).")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
