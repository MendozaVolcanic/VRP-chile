#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FICHA SDA — EJE 6 S122: desempeno vs ground truth MIROVA (CONS union OCR), por volcan x sensor.

POR QUE (fenomeno -> mecanismo -> numeros):
  MIROVA es la hoja de respuestas. Cada noche-satelite de cada volcan es una pregunta.
  El universo real de MIROVA no es solo latest.php (CONS): el canal OCR (imagenes por
  volcan) aporta pasadas que CONS no publica (regla A11) -> se usa CONS union OCR via el
  loader canonico pipeline/mirova_csv_loader.py (resuelve alias A14 y distancias OCR F-B2).

  Nuestro "positivo" es lo que el OPERADOR VE en el dashboard (gate mirovaEqVrp):
  primary_cluster.vrp_mw > 0, centroide dentro de inner_radius_km, vrp <= cap 50000,
  y distance_class summit/ausente. Se usa pc.vrp_mw (cluster crateriano) y NUNCA
  record.vrp_mw (suma scene-wide) — regla A10.

  Se reporta ademas el criterio CRATER (sin el gate de distance_class) para medir la
  brecha del bug A46 far->summit (records con cluster crateriano real ocultos).

Emparejado por (volcan, sensor_bucket, fecha UTC). Sensores (A48):
  MODIS_* -> MODIS ; VIIRS_*_750 -> VIIRS750 ; VIIRS_SNPP/NOAA* (sin sufijo) -> VIIRS375.

Precision: FP = noche-sensor donde MIROVA SI proceso (hay fila RUTINA/NULO/ALERTA en el
CSV para ese vol+sensor+fecha) pero NO declaro ALERTA, y nosotros si detectamos.
Las noches sin ninguna fila MIROVA se excluyen (no hay hoja de respuestas -> no se puede
contar ni acierto ni error).

Uso:
  python audit_gt_s122.py --root <repo_root> [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from pipeline.mirova_csv_loader import (  # noqa: E402
    load_mirova_alertas,
    normalize_sensor,
    normalize_volcano_name,
)

VOLS = [
    "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
    "Chaiten", "Villarrica", "Llaima", "Copahue", "Isluga", "PuyehueCordonCaulle",
]
INNER = {
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
    "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
    "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20,
}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000.0  # cap del gate mirovaEqVrp del frontend


def our_bucket(sensor: str):
    """Bucket canonico del sensor NUESTRO (convencion del repo, NO regex inventado)."""
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=REPO, help="raiz con data/ (default: repo)")
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "audit_gt_s122_result.json"))
    args = ap.parse_args()

    cons = os.path.join(args.root, "data", "mirova_reference", "mirova_v1_snapshot",
                        "registro_vrp_consolidado.csv")
    ocr = os.path.join(args.root, "data", "mirova_reference", "mirova_v1_snapshot",
                       "registro_vrp_ocr.csv")

    # ---- 0. Coberturas reales (para declarar la ventana valida, no inventarla) ----
    gt_dates = []
    gt_rows_total = 0
    passes = defaultdict(set)      # (vol,sensor) -> set(fecha) con CUALQUIER fila MIROVA
    for p in (cons, ocr):
        with open(p, encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                gt_rows_total += 1
                d = (r.get("Fecha_Satelite_UTC") or "")[:10]
                if not d:
                    continue
                gt_dates.append(d)
                vol = normalize_volcano_name(r.get("Volcan"))
                if vol is None:
                    continue
                passes[(vol, normalize_sensor(r.get("Sensor")))].add(d)

    our_dates = []
    ours = defaultdict(lambda: {"crater": [], "dash": []})
    far2summit = defaultdict(int)
    for v in VOLS:
        path = os.path.join(args.root, "data", "mirova_equivalent", v + ".json")
        d = json.load(open(path, encoding="utf-8"))
        inner = INNER[v]
        for rec in d["records"]:
            dt = rec.get("datetime_utc")
            if not dt:
                continue
            our_dates.append(dt[:10])
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cdist = pc.get("centroid_dist_km")
            dclass = rec.get("distance_class")
            crater_ok = (0 < vrp <= CAP) and (cdist is not None and cdist <= inner)
            if not crater_ok:
                continue
            key = (v, b, dt[:10])
            ours[key]["crater"].append(vrp)
            if not dclass or dclass == "summit":
                ours[key]["dash"].append(vrp)
            else:
                far2summit[(v, b)] += 1

    cov = {
        "gt_rows_total": gt_rows_total,
        "gt_date_min": min(gt_dates), "gt_date_max": max(gt_dates),
        "our_date_min": min(our_dates), "our_date_max": max(our_dates),
    }
    start = args.start or max(cov["gt_date_min"], cov["our_date_min"])
    end = args.end or min(cov["gt_date_max"], cov["our_date_max"])

    # ---- 1. ALERTAs MIROVA (CONS union OCR, loader canonico) ----
    alertas = defaultdict(list)  # (vol,sensor,fecha) -> [vrp..]
    n_alert_rows = {"CONS": 0, "OCR": 0}
    for a in load_mirova_alertas(cons_path=cons, ocr_path=ocr):
        d = (a.get("fecha_utc") or "")[:10]
        if not d or not (start <= d <= end):
            continue
        n_alert_rows[a["source"]] += 1
        alertas[(a["volcano"], a["sensor_bucket"], d)].append(a["vrp_mw"])

    # ---- 2. Metricas por vol x sensor ----
    rows = []
    agg = {s: dict(n_alerta=0, tp=0, tp_crater=0, fp=0, ratios=[]) for s in SENSORS}
    for v in VOLS:
        for s in SENSORS:
            alert_nights = {d: max(vs) for (vv, ss, d), vs in alertas.items()
                            if vv == v and ss == s}
            pass_nights = {d for d in passes.get((v, s), ()) if start <= d <= end}
            tp = tp_crater = fp = 0
            ratios = []
            for d, mvrp in alert_nights.items():
                o = ours.get((v, s, d))
                if o and o["crater"]:
                    tp_crater += 1
                if o and o["dash"]:
                    tp += 1
                    if mvrp > 0:
                        ratios.append(max(o["dash"]) / mvrp)
            for d in pass_nights - set(alert_nights):
                o = ours.get((v, s, d))
                if o and o["dash"]:
                    fp += 1
            n_a = len(alert_nights)
            agg[s]["n_alerta"] += n_a
            agg[s]["tp"] += tp
            agg[s]["tp_crater"] += tp_crater
            agg[s]["fp"] += fp
            agg[s]["ratios"] += ratios
            rows.append(dict(
                vol=v, sensor=s, inner_km=INNER[v],
                n_alerta=n_a, n_pass=len(pass_nights),
                tp=tp, tp_crater=tp_crater, fp=fp,
                recall_pct=round(tp / n_a * 100, 1) if n_a else None,
                recall_crater_pct=round(tp_crater / n_a * 100, 1) if n_a else None,
                precision_pct=round(tp / (tp + fp) * 100, 1) if (tp + fp) else None,
                ratio_med=round(statistics.median(ratios), 3) if ratios else None,
                n_ratio=len(ratios),
                gap_a46=tp_crater - tp,
            ))

    # ---- 3. Salida ----
    print("EJE 6 S122 — DESEMPENO vs MIROVA (CONS union OCR)")
    print("root:", args.root)
    print("cobertura GT  :", cov["gt_date_min"], "..", cov["gt_date_max"],
          "(", cov["gt_rows_total"], "filas )")
    print("cobertura ours:", cov["our_date_min"], "..", cov["our_date_max"])
    print("VENTANA VALIDA (interseccion):", start, "..", end)
    print("ALERTA rows en ventana: CONS=%d  OCR=%d" % (n_alert_rows["CONS"], n_alert_rows["OCR"]))
    print()
    print(">>> AGREGADO POR SENSOR (11 Tier A) <<<")
    print("  %-9s %8s %6s %6s %8s %10s %10s %6s" % (
        "SENSOR", "n_ALERTA", "TP", "FP", "recall%", "precision%", "ratio_med", "gapA46"))
    for s in SENSORS:
        a = agg[s]
        rc = a["tp"] / a["n_alerta"] * 100 if a["n_alerta"] else None
        pr = a["tp"] / (a["tp"] + a["fp"]) * 100 if (a["tp"] + a["fp"]) else None
        rm = statistics.median(a["ratios"]) if a["ratios"] else None
        print("  %-9s %8d %6d %6d %8s %10s %10s %6d" % (
            s, a["n_alerta"], a["tp"], a["fp"],
            "%.1f" % rc if rc is not None else "-",
            "%.1f" % pr if pr is not None else "-",
            "%.2f" % rm if rm is not None else "-",
            a["tp_crater"] - a["tp"]))
    print()
    print(">>> POR VOLCAN x SENSOR <<<")
    print("  %-20s %-9s %6s %6s %5s %5s %8s %10s %10s %6s" % (
        "VOL", "SENSOR", "n_ALR", "n_PASS", "TP", "FP", "recall%", "precision%",
        "ratio_med", "gapA46"))
    for r in rows:
        if r["n_alerta"] == 0 and r["fp"] == 0 and r["gap_a46"] == 0:
            continue
        print("  %-20s %-9s %6d %6d %5d %5d %8s %10s %10s %6d" % (
            r["vol"], r["sensor"], r["n_alerta"], r["n_pass"], r["tp"], r["fp"],
            r["recall_pct"] if r["recall_pct"] is not None else "-",
            r["precision_pct"] if r["precision_pct"] is not None else "-",
            r["ratio_med"] if r["ratio_med"] is not None else "-",
            r["gap_a46"]))

    out = dict(coverage=cov, window=[start, end], alert_rows=n_alert_rows,
               agg={s: {k: (v if k != "ratios" else len(v)) for k, v in a.items()}
                    for s, a in agg.items()},
               agg_ratio_med={s: (round(statistics.median(a["ratios"]), 3)
                                  if a["ratios"] else None) for s, a in agg.items()},
               by_vol_sensor=rows,
               far2summit={f"{k[0]}|{k[1]}": n for k, n in far2summit.items()})
    json.dump(out, open(args.out, "w", encoding="utf-8"), indent=1)
    print("\nWROTE", args.out)


if __name__ == "__main__":
    main()
