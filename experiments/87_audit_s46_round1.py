"""Audit S46 Ronda 1 — A/B Coppola literal 13 variantes.

Computa F1 vs MIROVA + ratio mediano + delta dist per (variante, volcan, sensor).
Output: experiments/87_results.md + experiments/87_results.json.

Reusa pattern de experiments/76_audit_independent.py:
  - INNER_RADIUS_KM tabla independiente
  - sensor_match() mapeo our_sensor (e.g. VIIRS_VJ102IMG) vs csv_sensor ('VIIRS'/'VIIRS375'/'MODIS')
  - detection_vrp_independent() criterio mirovaEqVrp (primary_cluster.vrp_mw si centroid_dist <= inner_radius)

CSV ground truth: 01_05_2026_registro_vrp_consolidado.csv (Mirova-v1 scraper).
Sensores CSV: 'MODIS', 'VIIRS' (=M-band 750m), 'VIIRS375' (=I-band 375m).
"""
from __future__ import annotations
import json
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
import yaml

# Force utf-8 stdout for Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


VARIANTS = [
    "_baseline_s44",
    "_drift1a_only", "_drift1b_only", "_drift1ab_only",
    "_drift23_only", "_drift23_dual_only",
    "_drift4_only", "_drift234_only",
    "_drift7_modis_only", "_drift7_viirs_only", "_drift7_both_only",
    "_coppola_full",
    "_dibella_n12_viirs_only",
]

# vol_key (folder/yaml) -> nombre en CSV
VOLC_CSV_MAP = {
    "Lascar": "Lascar",
    "Tupungatito": "Tupungatito",
    "Lastarria": "Lastarria",
    "NevadosDeChillan": "Nevados de Chillan",
    "Llaima": "Llaima",
    "Copahue": "Copahue",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Isluga": "Isluga",
    "Villarrica": "Villarrica",
    "Chaiten": "Chaiten",
}

# Labels MIROVA CSV: 'MODIS', 'VIIRS' (750m M-band), 'VIIRS375' (I-band)
SENSORS = ["MODIS", "VIIRS", "VIIRS375"]

# Fallback inner_radius por volcan (en caso volcanoes.yaml no exponga el campo)
INNER_RADIUS_FALLBACK = {
    'Lascar': 5, 'Lastarria': 3, 'Tupungatito': 7, 'Villarrica': 5,
    'PuyehueCordonCaulle': 20, 'Copahue': 4, 'NevadosDeChillan': 5,
    'Llaima': 5, 'Chaiten': 5, 'PlanchonPeteroa': 3, 'Isluga': 5,
}


def _sensor_match(record_sensor: str, target_sensor: str) -> bool:
    """Match record.sensor (pipeline) vs CSV sensor label.

    Pipeline emite: 'MODIS_MOD021KM', 'MODIS_MYD021KM',
                    'VIIRS_VJ102IMG' (I-band 375m),
                    'VIIRS_VJ102MOD_750' / 'VIIRS_VNP02MOD_750' (M-band 750m).
    CSV ground truth: 'MODIS', 'VIIRS' (=750m), 'VIIRS375' (=I-band).
    """
    if not record_sensor:
        return False
    rs = record_sensor.upper()
    if target_sensor == "MODIS":
        return rs.startswith("MODIS")
    if target_sensor == "VIIRS":
        # M-band 750m: suffix _750 o contiene MOD (M-band products)
        return rs.startswith("VIIRS_") and rs.endswith("_750")
    if target_sensor == "VIIRS375":
        # I-band 375m: VIIRS_VJ102IMG / VIIRS_VNP02IMG (no _750)
        return rs.startswith("VIIRS_") and not rs.endswith("_750")
    return False


def _vrp_mirovaEq(record: dict, inner_radius_km: float) -> float:
    """Reimplementacion mirovaEqVrp independiente (pattern S33+).

    Steps:
      1. None/non-dict -> 0
      2. primary_cluster None -> fallback global vrp_mw
      3. centroid_dist_km > inner_radius_km -> 0 (Salar/lago lejano)
      4. sanity cap vrp_mw > 50000 MW (S41 — garbage BT) -> 0
      5. return pc.vrp_mw

    BUG FIX S46 audit: el filtro previo `distance_class == "far"` filtraba
    records donde el hotspot LEGACY estaba lejano pero el primary_cluster
    SÍ estaba en summit. Sub-contaba TPs por ~70% en Lascar MODIS.
    El dashboard real (mirovaEqVrp) solo filtra por pc.centroid_dist_km,
    no por distance_class. Alineamos.
    """
    if record is None or not isinstance(record, dict):
        return 0.0
    pc = record.get("primary_cluster")
    if pc is None:
        v = record.get("vrp_mw", 0.0)
        try:
            return float(v) if v else 0.0
        except (TypeError, ValueError):
            return 0.0
    cdist = pc.get("centroid_dist_km")
    if cdist is None:
        return 0.0
    if cdist > inner_radius_km:
        return 0.0
    vrp = pc.get("vrp_mw", 0.0)
    try:
        vrp_f = float(vrp) if vrp else 0.0
    except (TypeError, ValueError):
        return 0.0
    if vrp_f > 50000:  # sanity cap S41
        return 0.0
    return vrp_f


def _parse_rec_dt(s: str) -> pd.Timestamp | None:
    if not s:
        return None
    try:
        return pd.Timestamp(s).tz_convert("UTC") if pd.Timestamp(s).tzinfo \
            else pd.Timestamp(s).tz_localize("UTC")
    except Exception:
        return None


def _compute_metrics(sensor_recs, mirova_csv, vol_csv_name, sensor_label, inner_radius,
                     window_start, window_end) -> tuple:
    """Compute TP/FN/FP + ratio_med + dist_med per (volcan, sensor)."""
    mvol = mirova_csv[(mirova_csv["Volcan"] == vol_csv_name)
                       & (mirova_csv["Sensor"] == sensor_label)].copy()
    mvol = mvol[(mvol["ts"] >= window_start) & (mvol["ts"] < window_end)]

    alerts = mvol[mvol["Tipo_Registro"] == "ALERTA_TERMICA"]
    fps_marker = mvol[mvol["Tipo_Registro"] == "FALSO_POSITIVO"]

    tol = timedelta(minutes=30)
    tp = 0
    fn = 0
    fp = 0
    matched_recs = set()
    vrp_ratios = []
    dist_diffs = []

    for _, m in alerts.iterrows():
        t_m = m["ts"]
        match_idx = None
        best_delta = tol + timedelta(seconds=1)
        for i, (t_o, r) in enumerate(sensor_recs):
            if i in matched_recs:
                continue
            delta = abs(t_o - t_m)
            if delta > tol:
                continue
            vrp_eq = _vrp_mirovaEq(r, inner_radius)
            if vrp_eq > 0 and delta < best_delta:
                match_idx = i
                best_delta = delta

        if match_idx is not None:
            tp += 1
            matched_recs.add(match_idx)
            _, r_matched = sensor_recs[match_idx]
            pc = r_matched.get("primary_cluster") or {}
            vrp_o = pc.get("vrp_mw", 0)
            vrp_m = m.get("VRP_MW", 0)
            try:
                vrp_m_f = float(vrp_m) if vrp_m else 0
            except (TypeError, ValueError):
                vrp_m_f = 0
            if vrp_m_f > 0 and vrp_o:
                vrp_ratios.append(float(vrp_o) / vrp_m_f)
            dist_o = pc.get("centroid_dist_km")
            dist_m = m.get("Distancia_km")
            try:
                dist_m_f = float(dist_m) if dist_m is not None else None
            except (TypeError, ValueError):
                dist_m_f = None
            if dist_o is not None and dist_m_f is not None:
                dist_diffs.append(abs(float(dist_o) - dist_m_f))
        else:
            fn += 1

    # FP: detectamos VRP>0 cuando MIROVA marca FALSO_POSITIVO en ese timestamp
    for _, mfp in fps_marker.iterrows():
        t_m = mfp["ts"]
        for i, (t_o, r) in enumerate(sensor_recs):
            if abs(t_o - t_m) > tol:
                continue
            if _vrp_mirovaEq(r, inner_radius) > 0:
                fp += 1
                break

    ratio_med = float(np.median(vrp_ratios)) if vrp_ratios else None
    dist_med = float(np.median(dist_diffs)) if dist_diffs else None
    return tp, fn, fp, ratio_med, dist_med


def audit_variant(variant_dir: Path, mirova_csv: pd.DataFrame, vol_meta: dict,
                  window_start, window_end) -> dict:
    """Audit per-(volcan, sensor) breakdown sobre data/<variant>/."""
    results = {}
    for vol_key, vol_csv_name in VOLC_CSV_MAP.items():
        op_path = variant_dir / f"{vol_key}.json"
        if not op_path.exists():
            continue
        try:
            data = json.loads(op_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  WARN: failed to load {op_path.name}: {e}")
            continue
        recs = data.get("records", [])
        inner_radius = vol_meta.get(vol_key, {}).get(
            "inner_radius_km", INNER_RADIUS_FALLBACK.get(vol_key, 5),
        )

        op_recs = []
        for r in recs:
            ts = r.get("datetime_utc") or r.get("timestamp_utc")
            t = _parse_rec_dt(ts)
            if t is None:
                continue
            if window_start <= t < window_end:
                op_recs.append((t, r))

        sensor_breakdown = {}
        for sensor_label in SENSORS:
            sensor_recs = [
                (t, r) for t, r in op_recs
                if _sensor_match(r.get("sensor", ""), sensor_label)
            ]
            tp, fn, fp, ratio_med, dist_med = _compute_metrics(
                sensor_recs, mirova_csv, vol_csv_name, sensor_label,
                inner_radius, window_start, window_end,
            )
            sensor_breakdown[sensor_label] = {
                "TP": tp, "FN": fn, "FP": fp,
                "ratio_med": ratio_med,
                "dist_med_km": dist_med,
            }

        results[vol_key] = {
            "inner_radius_km": inner_radius,
            "n_records": len(op_recs),
            "sensor_breakdown": sensor_breakdown,
        }
    return results


def _compute_f1(tp: int, fn: int, fp: int) -> tuple:
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1


def write_markdown_summary(results: dict, output_path: Path, window_start, window_end):
    lines = ["# S46 Ronda 1 - Results A/B Coppola literal\n\n"]
    lines.append(f"Window: {window_start.date()} a {window_end.date()}.\n")
    lines.append(f"Variantes auditadas: {len(results)} ({', '.join(results.keys())}).\n\n")

    # Tabla agregada todos sensores
    lines.append("## Tabla agregada (Tier A, todos sensores)\n\n")
    lines.append("| Variante | TP | FN | FP | F1 | Recall | Precision |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for variant, vol_results in results.items():
        tp = sum(s["TP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fn = sum(s["FN"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fp = sum(s["FP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        p, r, f1 = _compute_f1(tp, fn, fp)
        lines.append(f"| {variant} | {tp} | {fn} | {fp} | "
                     f"{f1*100:.1f}% | {r*100:.1f}% | {p*100:.1f}% |\n")

    # Per-sensor breakdown
    lines.append("\n## Per-sensor breakdown\n\n")
    for sensor in SENSORS:
        lines.append(f"### {sensor}\n\n")
        lines.append("| Variante | TP | FN | FP | F1 |\n")
        lines.append("|---|---|---|---|---|\n")
        for variant, vol_results in results.items():
            tp = sum(v["sensor_breakdown"].get(sensor, {}).get("TP", 0)
                     for v in vol_results.values())
            fn = sum(v["sensor_breakdown"].get(sensor, {}).get("FN", 0)
                     for v in vol_results.values())
            fp = sum(v["sensor_breakdown"].get(sensor, {}).get("FP", 0)
                     for v in vol_results.values())
            p, r, f1 = _compute_f1(tp, fn, fp)
            lines.append(f"| {variant} | {tp} | {fn} | {fp} | {f1*100:.1f}% |\n")
        lines.append("\n")

    # Decision automatica
    lines.append("## Decision automatica (delta F1 vs baseline_s44)\n\n")
    lines.append("| Variante | dF1 (pp) | dRecall (pp) | Decision |\n")
    lines.append("|---|---|---|---|\n")

    bv = results.get("_baseline_s44", {})
    bl_tp = sum(s["TP"] for v in bv.values() for s in v["sensor_breakdown"].values())
    bl_fn = sum(s["FN"] for v in bv.values() for s in v["sensor_breakdown"].values())
    bl_fp = sum(s["FP"] for v in bv.values() for s in v["sensor_breakdown"].values())
    _, bl_r, bl_f1 = _compute_f1(bl_tp, bl_fn, bl_fp)

    for variant, vol_results in results.items():
        if variant == "_baseline_s44":
            continue
        tp = sum(s["TP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fn = sum(s["FN"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fp = sum(s["FP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        _, r, f1 = _compute_f1(tp, fn, fp)
        df1 = f1 - bl_f1
        dr = r - bl_r
        if df1 > 0.02 and dr > 0:
            decision = "WIN - adopt operacional"
        elif df1 > 0 and dr >= -0.02:
            decision = "NEUTRAL win - adopt for paper alignment"
        elif df1 > -0.02:
            decision = "NEUTRAL - defer Ronda 2"
        else:
            decision = "REGRESS - investigate"
        lines.append(f"| {variant} | {df1*100:+.1f} | {dr*100:+.1f} | {decision} |\n")

    output_path.write_text("".join(lines), encoding="utf-8")


def main():
    repo_root = Path(__file__).parent.parent

    csv_candidates = sorted(repo_root.glob("*registro_vrp_consolidado*.csv"))
    if not csv_candidates:
        print("ERROR: No CSV consolidado MIROVA encontrado")
        return 1
    csv_path = csv_candidates[-1]
    print(f"Loading MIROVA CSV: {csv_path.name}")

    mirova_csv = pd.read_csv(csv_path)
    mirova_csv["ts"] = pd.to_datetime(
        mirova_csv["Fecha_Satelite_UTC"], errors="coerce", utc=True,
    )
    mirova_csv = mirova_csv.dropna(subset=["ts"])
    print(f"  rows: {len(mirova_csv)}, latest: {mirova_csv['ts'].max()}")

    vol_meta = {}
    yaml_path = repo_root / "volcanoes.yaml"
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # volcanoes.yaml: top-level list o dict con 'volcanoes' key
        vols = data.get("volcanoes", data) if isinstance(data, dict) else data
        if isinstance(vols, list):
            vol_meta = {v["name"]: v for v in vols if isinstance(v, dict) and "name" in v}

    window_end = mirova_csv["ts"].max() + pd.Timedelta(days=1)
    window_start = window_end - pd.Timedelta(days=30)
    print(f"Window audit: {window_start.date()} -> {window_end.date()}")

    all_results = {}
    for variant in VARIANTS:
        variant_dir = repo_root / "data" / variant
        if not variant_dir.exists():
            print(f"  SKIP {variant}: data dir missing")
            continue
        print(f"  Auditing {variant}...")
        all_results[variant] = audit_variant(
            variant_dir, mirova_csv, vol_meta, window_start, window_end,
        )

    output_dir = repo_root / "experiments"
    output_dir.mkdir(exist_ok=True)

    if all_results:
        (output_dir / "87_results.json").write_text(
            json.dumps(all_results, indent=2, default=str), encoding="utf-8",
        )
        write_markdown_summary(
            all_results, output_dir / "87_results.md", window_start, window_end,
        )
        print("\nAudit completo. Outputs:")
        print(f"  - {output_dir / '87_results.json'}")
        print(f"  - {output_dir / '87_results.md'}")
    else:
        print("\nNo variant data found yet (pre-A/B dispatch expected).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
