"""
S76 - Recall/Precision/F1/ratio audit fresco para los 11 volcanes Tier A.

Reusa la metodologia validada de experiments/137_3way_audit_pipeline_actual
(sensor-aware matching +/-60min, pc.vrp_mw convention con fallback a vrp_mw,
ground truth = CONS + OCR ALERTA_TERMICA).

Setup unico: operacional (data/mirova_equivalent/), post PRs S71-S75 mergeados.

Ventana: 2026-02-01 -> 2026-05-20 (108d, sin bordes de los JSON 2026-01-29 a
2026-05-23).

Output:
  - audit_s76.json (raw metricas por volcan)
  - audit_s76.csv  (tabla TP/FP/FN/recall/precision/F1/ratio)
  - audit_s76.md   (reporte + diff vs S12 baseline + diagnosticos)
"""
from __future__ import annotations

import calendar
import csv
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

OP_DIR = ROOT / "data" / "mirova_equivalent"

MATCH_TOL_MIN = 60.0

WINDOW_START = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 5, 20, 23, 59, 59, tzinfo=timezone.utc)
WINDOW_START_TS = WINDOW_START.timestamp()
WINDOW_END_TS = WINDOW_END.timestamp()

# Baseline S12 (2026-04-16) por CLAUDE.md L455-459
S12_BASELINE = {
    "Chaiten":              {"recall": 0.87},
    "Lastarria":            {"recall": 0.85},
    "Tupungatito":          {"recall": 0.83},
    "PuyehueCordonCaulle":  {"recall": 0.82},
    "Lascar":               {"recall": 0.55, "precision_ocr_adj": 0.69, "ratio": 1.11},
    "Villarrica":           {"recall": 0.00},
}


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
    """Convencion A4: prefer pc.vrp_mw, fallback to global vrp_mw."""
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


def load_vol(vol):
    fp = OP_DIR / f"{vol}.json"
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


def audit_vol(records, alerts_vol):
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
    # FN: alertas MIROVA en ventana con coverage sensor pero sin match
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
    f1 = None
    if recall is not None and precision is not None and (recall + precision) > 0:
        f1 = 2 * recall * precision / (recall + precision)
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
        "f1": f1,
        "ratio_median": ratio_med,
        "ratio_n": len(ratios),
        "vrp_max_detected": vrp_max,
        "vrp_median_detected": vrp_med,
    }


def diagnose(vol, r):
    flags = []
    if r.get("error"):
        return ["MISSING_JSON"]
    if r["recall"] is not None and r["recall"] < 0.5:
        flags.append(f"recall_bajo({r['recall']:.2f})")
    if r["precision"] is not None and r["precision"] < 0.5:
        flags.append(f"precision_baja({r['precision']:.2f})")
    if r["ratio_median"] is not None and (r["ratio_median"] < 0.5 or r["ratio_median"] > 2.0):
        flags.append(f"ratio_fuera_rango({r['ratio_median']:.2f})")
    if r["alerts_in_window"] == 0:
        flags.append("sin_alertas_MIROVA_en_ventana")
    if r["alerts_no_coverage"] > 0:
        flags.append(f"no_cov={r['alerts_no_coverage']}")
    return flags


def main():
    print(f"[loading MIROVA alerts {WINDOW_START.date()} - {WINDOW_END.date()}]")
    alerts = load_mirova_alerts()
    print(f"  total ALERTA rows in window: {len(alerts)}")
    print(f"[scanning {OP_DIR}] exists={OP_DIR.exists()}")

    out = {
        "params": {
            "window_start": WINDOW_START.isoformat(),
            "window_end": WINDOW_END.isoformat(),
            "match_tol_min": MATCH_TOL_MIN,
            "dir": str(OP_DIR),
            "ground_truth": [str(CONS_CSV), str(OCR_CSV)],
            "tier_a_count": len(TIER_A),
        },
        "per_volcano": {},
    }
    for vol in TIER_A:
        names = VOL_CSV_MAP.get(vol, [vol])
        al_v = alerts[alerts["Volcan"].isin(names)].copy()
        recs = load_vol(vol)
        res = audit_vol(recs, al_v)
        res["n_alerts_in_window"] = int(len(al_v))
        res["diagnose"] = diagnose(vol, res)
        out["per_volcano"][vol] = res
        if "error" not in res:
            rec = f"{res['recall']:.2f}" if res["recall"] is not None else "-"
            prc = f"{res['precision']:.2f}" if res["precision"] is not None else "-"
            f1 = f"{res['f1']:.2f}" if res["f1"] is not None else "-"
            rmd = f"{res['ratio_median']:.2f}" if res["ratio_median"] is not None else "-"
            print(f"[{vol:22s}] alerts={len(al_v):4d} det={res['n_records_detection']:4d} TP={res['tp']:3d} FP={res['fp']:3d} FN={res['fn']:3d} r={rec} p={prc} F1={f1} rat={rmd}")
        else:
            print(f"[{vol:22s}] MISSING")

    # CSV
    csv_path = OUT_DIR / "audit_s76.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["volcano", "n_alerts_mirova", "n_records", "n_detections", "TP", "FP", "FN",
                    "recall", "precision", "F1", "ratio_median",
                    "vrp_max_detected_mw", "vrp_median_detected_mw",
                    "alerts_no_coverage", "diagnose"])
        for vol in TIER_A:
            r = out["per_volcano"][vol]
            if "error" in r:
                w.writerow([vol, r.get("n_alerts_in_window", "-")] + ["MISSING"] * 13)
                continue
            w.writerow([
                vol, r["n_alerts_in_window"], r["n_records_in_window"], r["n_records_detection"],
                r["tp"], r["fp"], r["fn"],
                f"{r['recall']:.3f}" if r["recall"] is not None else "",
                f"{r['precision']:.3f}" if r["precision"] is not None else "",
                f"{r['f1']:.3f}" if r["f1"] is not None else "",
                f"{r['ratio_median']:.3f}" if r["ratio_median"] is not None else "",
                f"{r['vrp_max_detected']:.1f}" if r["vrp_max_detected"] is not None else "",
                f"{r['vrp_median_detected']:.1f}" if r["vrp_median_detected"] is not None else "",
                r["alerts_no_coverage"],
                ";".join(r["diagnose"]),
            ])
    print(f"[wrote {csv_path}]")

    # JSON
    json_path = OUT_DIR / "audit_s76.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[wrote {json_path}]")

    # MD report
    md = render_report(out)
    md_path = OUT_DIR / "audit_s76.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote {md_path}]")


def render_report(out):
    L = []
    p = out["params"]
    L.append("# S76 - Audit recall/precision Tier A (operacional fresco)")
    L.append("")
    L.append(f"Ventana: {p['window_start'][:10]} -> {p['window_end'][:10]} (108d)")
    L.append(f"Matching: sensor-aware +/-{int(p['match_tol_min'])} min")
    L.append(f"Ground truth: CONS + OCR ALERTA_TERMICA")
    L.append(f"Setup: data/mirova_equivalent/ (post PRs S71-S75)")
    L.append("")
    L.append("## Tabla principal")
    L.append("")
    L.append("| Volcan | n_alert | n_rec | n_det | TP | FP | FN | Recall | Precision | F1 | Ratio_med | vmax(MW) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for vol in TIER_A:
        r = out["per_volcano"][vol]
        if "error" in r:
            L.append(f"| {vol} | - | MISSING | | | | | | | | | |")
            continue
        rec = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
        prc = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
        f1 = f"{r['f1']:.2f}" if r["f1"] is not None else "-"
        rmd = f"{r['ratio_median']:.2f}" if r["ratio_median"] is not None else "-"
        vmax = f"{r['vrp_max_detected']:.1f}" if r["vrp_max_detected"] is not None else "-"
        L.append(
            f"| {vol} | {r['n_alerts_in_window']} | {r['n_records_in_window']} | "
            f"{r['n_records_detection']} | {r['tp']} | {r['fp']} | {r['fn']} | "
            f"{rec} | {prc} | {f1} | {rmd} | {vmax} |"
        )
    L.append("")

    # Diff vs S12 baseline
    L.append("## Diff vs S12 baseline (2026-04-16)")
    L.append("")
    L.append("| Volcan | S12 recall | S76 recall | Delta | Estado |")
    L.append("|---|---|---|---|---|")
    for vol, base in S12_BASELINE.items():
        r = out["per_volcano"].get(vol, {})
        if "error" in r:
            L.append(f"| {vol} | {base['recall']:.2f} | MISSING | - | - |")
            continue
        cur = r.get("recall")
        s12 = base["recall"]
        if cur is None:
            L.append(f"| {vol} | {s12:.2f} | - | - | sin metrica |")
            continue
        delta = cur - s12
        if delta > 0.10:
            estado = "MEJORA"
        elif delta < -0.10:
            estado = "REGRESION"
        else:
            estado = "estable"
        L.append(f"| {vol} | {s12:.2f} | {cur:.2f} | {delta:+.2f} | {estado} |")
    L.append("")

    # Diagnostico problemas
    L.append("## Diagnostico volcanes problematicos (recall<0.5 OR precision<0.5 OR ratio fuera 0.5-2.0)")
    L.append("")
    any_issue = False
    for vol in TIER_A:
        r = out["per_volcano"][vol]
        if "error" in r:
            continue
        flags = r.get("diagnose", [])
        critical = [f for f in flags if not f.startswith("no_cov") and f != "sin_alertas_MIROVA_en_ventana"]
        if critical:
            any_issue = True
            L.append(f"- **{vol}**: {', '.join(flags)}")
            L.append(f"    TP={r['tp']} FP={r['fp']} FN={r['fn']}, "
                     f"vmax={r['vrp_max_detected']} vmed={r['vrp_median_detected']}, "
                     f"alertas={r['alerts_in_window']} no_cov={r['alerts_no_coverage']}")
    if not any_issue:
        L.append("- (ninguno - todos pasan umbrales recall>=0.5, precision>=0.5, ratio 0.5-2.0)")
    L.append("")

    L.append("## Notas metodologicas")
    L.append("")
    L.append("- `pc.vrp_mw` con fallback global `vrp_mw` (convencion A4 desde experiments/137).")
    L.append("- Matching sensor-aware (MODIS vs VIIRS no se cruzan).")
    L.append("- Tolerancia +/-60 min cubre desfase scraper vs L1B + multiple granules/noche.")
    L.append("- FN solo cuenta alertas con cobertura sensor (no penaliza nights sin granule).")
    L.append("- Baseline S12 viene de CLAUDE.md (snapshot 2026-04-16, pre S15-S75 changes).")
    return "\n".join(L)


if __name__ == "__main__":
    main()
