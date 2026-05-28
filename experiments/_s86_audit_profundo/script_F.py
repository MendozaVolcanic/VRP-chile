# -*- coding: utf-8 -*-
"""
Subagente F (S86) — Auditoria integridad scraper Mirova-v1 + CSVs.

Outputs:
  experiments/_s86_audit_profundo/F_scraper_integrity.json
  experiments/_s86_audit_profundo/F_scraper_integrity.md
"""

import csv
import io
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Force utf-8 stdout for Windows
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
CONS_CSV = os.path.join(BASE, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
OCR_CSV = os.path.join(BASE, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
OUT_DIR = os.path.join(BASE, "experiments/_s86_audit_profundo")
os.makedirs(OUT_DIR, exist_ok=True)

TIER_A = {
    "Lascar", "Lastarria", "Isluga", "Villarrica", "Llaima",
    "Nevados de Chillan", "Copahue", "Puyehue-Cordon Caulle",
    "Chaiten", "PlanchonPeteroa", "Tupungatito",
    # Variantes
    "Planchon-Peteroa", "PuyehueCordonCaulle", "NevadosDeChillan",
    "ChillanNevadosde",
}

TIER_A_CANONICAL = [
    "Lascar", "Lastarria", "Isluga", "Villarrica", "Llaima",
    "Nevados de Chillan", "Copahue", "Puyehue-Cordon Caulle",
    "Chaiten", "PlanchonPeteroa", "Tupungatito",
]


def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def parse_dt(s):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def audit():
    out = {"meta": {}, "schema": {}, "coverage": {}, "gaps": {}, "tz": {},
           "ocr_vs_cons": {}, "name_variants": {}, "issues": []}

    # -------- LOAD --------
    cons = load_csv(CONS_CSV)
    ocr = load_csv(OCR_CSV)
    out["meta"]["cons_rows"] = len(cons)
    out["meta"]["ocr_rows"] = len(ocr)
    out["meta"]["cons_cols"] = list(cons[0].keys()) if cons else []
    out["meta"]["ocr_cols"] = list(ocr[0].keys()) if ocr else []

    # -------- SCHEMA DRIFT --------
    tipos_cons = Counter(r["Tipo_Registro"] for r in cons)
    tipos_ocr = Counter(r["Tipo_Registro"] for r in ocr)
    clasif_cons = Counter(r["Clasificacion Mirova"] for r in cons)
    clasif_ocr = Counter(r["Clasificacion Mirova"] for r in ocr)
    sensors_cons = Counter(r["Sensor"] for r in cons)
    sensors_ocr = Counter(r["Sensor"] for r in ocr)
    vols_cons = Counter(r["Volcan"] for r in cons)
    vols_ocr = Counter(r["Volcan"] for r in ocr)

    out["schema"]["cons_tipo_registro"] = dict(tipos_cons)
    out["schema"]["ocr_tipo_registro"] = dict(tipos_ocr)
    out["schema"]["cons_clasificacion"] = dict(clasif_cons)
    out["schema"]["ocr_clasificacion"] = dict(clasif_ocr)
    out["schema"]["cons_sensors"] = dict(sensors_cons)
    out["schema"]["ocr_sensors"] = dict(sensors_ocr)
    out["schema"]["cons_volcanes"] = dict(vols_cons)
    out["schema"]["ocr_volcanes"] = dict(vols_ocr)

    # -------- NAME VARIANTS --------
    out["name_variants"]["cons"] = sorted(vols_cons.keys())
    out["name_variants"]["ocr"] = sorted(vols_ocr.keys())
    only_cons = set(vols_cons) - set(vols_ocr)
    only_ocr = set(vols_ocr) - set(vols_cons)
    out["name_variants"]["only_in_cons"] = sorted(only_cons)
    out["name_variants"]["only_in_ocr"] = sorted(only_ocr)

    # -------- COVERAGE --------
    cov_cons = {}
    for vol in TIER_A_CANONICAL:
        rows = [r for r in cons if r["Volcan"] == vol]
        if not rows:
            cov_cons[vol] = {"rows": 0, "min": None, "max": None,
                             "alertas": 0, "sensors": {}}
            continue
        dts = [parse_dt(r["Fecha_Satelite_UTC"]) for r in rows]
        dts = [d for d in dts if d]
        alertas = sum(1 for r in rows if r["Tipo_Registro"] == "ALERTA_TERMICA")
        sensors = Counter(r["Sensor"] for r in rows
                          if r["Tipo_Registro"] == "ALERTA_TERMICA")
        cov_cons[vol] = {
            "rows": len(rows),
            "alertas": alertas,
            "min": min(dts).isoformat() if dts else None,
            "max": max(dts).isoformat() if dts else None,
            "alertas_por_sensor": dict(sensors),
        }
    out["coverage"]["cons_per_vol"] = cov_cons

    cov_ocr = {}
    for vol in set(vols_ocr.keys()):
        rows = [r for r in ocr if r["Volcan"] == vol]
        dts = [parse_dt(r["Fecha_Satelite_UTC"]) for r in rows]
        dts = [d for d in dts if d]
        sensors = Counter(r["Sensor"] for r in rows)
        cov_ocr[vol] = {
            "rows": len(rows),
            "min": min(dts).isoformat() if dts else None,
            "max": max(dts).isoformat() if dts else None,
            "sensors": dict(sensors),
        }
    out["coverage"]["ocr_per_vol"] = cov_ocr

    # -------- TIMESTAMP GAPS (CONS) --------
    gaps_summary = {}
    for vol in TIER_A_CANONICAL:
        rows = sorted(
            [r for r in cons if r["Volcan"] == vol],
            key=lambda x: parse_dt(x["Fecha_Satelite_UTC"]) or datetime.min,
        )
        deltas = []
        for i in range(1, len(rows)):
            a = parse_dt(rows[i - 1]["Fecha_Satelite_UTC"])
            b = parse_dt(rows[i]["Fecha_Satelite_UTC"])
            if a and b:
                deltas.append((b - a).total_seconds() / 3600.0)
        big_gaps = [round(d, 2) for d in deltas if d > 48]
        gaps_summary[vol] = {
            "n_records": len(rows),
            "n_gaps_gt_48h": len(big_gaps),
            "max_gap_h": round(max(deltas), 2) if deltas else 0,
            "median_gap_h": round(sorted(deltas)[len(deltas) // 2], 2) if deltas else 0,
            "p95_gap_h": round(sorted(deltas)[int(len(deltas) * 0.95)], 2) if deltas else 0,
            "biggest_5_gaps_h": sorted(big_gaps, reverse=True)[:5],
        }
    out["gaps"]["cons_per_vol"] = gaps_summary

    # -------- TIMEZONE --------
    tz_samples = []
    bad_tz = 0
    for r in cons[:5000]:
        utc = parse_dt(r["Fecha_Satelite_UTC"])
        cl = parse_dt(r["Fecha_Captura_Chile"])
        if utc and cl:
            diff_h = (utc - cl).total_seconds() / 3600.0
            if diff_h not in (3.0, 4.0):
                bad_tz += 1
                if len(tz_samples) < 5:
                    tz_samples.append({
                        "utc": r["Fecha_Satelite_UTC"],
                        "cl": r["Fecha_Captura_Chile"],
                        "diff_h": diff_h,
                    })
    out["tz"]["cons_first5k_bad"] = bad_tz
    out["tz"]["cons_bad_samples"] = tz_samples

    # -------- Distancia_km en CONS vs OCR --------
    cons_dist_zero = sum(
        1 for r in cons if r["Tipo_Registro"] == "ALERTA_TERMICA"
        and float(r.get("Distancia_km") or 0) == 0.0
    )
    cons_alertas = sum(1 for r in cons if r["Tipo_Registro"] == "ALERTA_TERMICA")
    ocr_dist_zero = sum(
        1 for r in ocr if float(r.get("Distancia_km") or 0) == 0.0
    )
    out["meta"]["cons_alertas_total"] = cons_alertas
    out["meta"]["cons_alertas_dist_eq_zero"] = cons_dist_zero
    out["meta"]["ocr_total"] = len(ocr)
    out["meta"]["ocr_dist_eq_zero"] = ocr_dist_zero

    # -------- OCR vs CONS overlap (ts, vol_normalized, sensor) --------
    def norm_vol(v):
        return (v or "").lower().replace("-", "").replace("_", "").replace(" ", "")

    def norm_sensor(s):
        s = (s or "").upper()
        if s == "VIIRS":
            return "VIIRS750"
        return s

    cons_keys = set()
    for r in cons:
        try:
            ts = int(r["timestamp"])
        except Exception:
            continue
        cons_keys.add((ts, norm_vol(r["Volcan"]), norm_sensor(r["Sensor"])))

    ocr_in_cons = 0
    ocr_not_in_cons = 0
    ocr_not_in_cons_per_vol = Counter()
    for r in ocr:
        try:
            ts = int(r["timestamp"])
        except Exception:
            continue
        k = (ts, norm_vol(r["Volcan"]), norm_sensor(r["Sensor"]))
        if k in cons_keys:
            ocr_in_cons += 1
        else:
            ocr_not_in_cons += 1
            ocr_not_in_cons_per_vol[r["Volcan"]] += 1

    out["ocr_vs_cons"]["ocr_total"] = len(ocr)
    out["ocr_vs_cons"]["ocr_overlap_with_cons"] = ocr_in_cons
    out["ocr_vs_cons"]["ocr_only_not_in_cons"] = ocr_not_in_cons
    out["ocr_vs_cons"]["ocr_only_per_vol"] = dict(ocr_not_in_cons_per_vol)

    # -------- ENCODING / mojibake --------
    bad_enc = 0
    bad_samples = []
    bad_chars = ("�", "Ã©", "Ã³", "Ã±")
    for r in cons:
        text = " ".join(str(v) for v in r.values())
        if any(c in text for c in bad_chars):
            bad_enc += 1
            if len(bad_samples) < 5:
                bad_samples.append(r)
    out["schema"]["cons_mojibake_rows"] = bad_enc
    out["schema"]["cons_mojibake_samples"] = bad_samples

    # -------- VIIRS750 ALERTAs (Subagente C: 0 en Tier A) --------
    viirs750_alertas = Counter()
    for r in cons:
        if r["Tipo_Registro"] == "ALERTA_TERMICA" and r["Sensor"] in ("VIIRS750", "VIIRS"):
            viirs750_alertas[r["Volcan"]] += 1
    out["schema"]["viirs750_alertas_per_vol"] = dict(viirs750_alertas)

    # -------- FALSO_POSITIVO en CONS (segun scraper.py logic) --------
    fp_per_vol = Counter()
    for r in cons:
        if r["Tipo_Registro"] == "FALSO_POSITIVO":
            fp_per_vol[r["Volcan"]] += 1
    out["schema"]["falso_positivo_per_vol_cons"] = dict(fp_per_vol)

    # -------- WRITE OUTPUT --------
    json_path = os.path.join(OUT_DIR, "F_scraper_integrity.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    print(f"[OK] Wrote {json_path}")

    return out


if __name__ == "__main__":
    audit()
