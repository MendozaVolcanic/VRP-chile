#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-audit semanal de paridad vs MIROVA (S120, propuesta §8 AUDIT_S119).

POR QUÉ (fenómeno → mecanismo): la paridad con MIROVA se validaba en auditorías
episódicas (A51, cada ~20 sesiones). Entre auditorías, una regresión silenciosa
(un flip de flag, un cambio NASA, un drift del ground truth) puede correr semanas
sin detección. Este script empaqueta los criterios EXACTOS del Eje 2 de la
auditoría S119 (experiments/_s119_audit/eje2_recall_magnitud.py) en una corrida
semanal con ventana rodante → data/audit_continuous/latest.json. El workflow
audit-weekly.yml lo corre por cron y abre un issue si algo sale de banda.

Criterios (idénticos a S119, regla S91 — no re-derivar):
  - CRÁTER: pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND vrp<=50000 (A10).
  - DASHBOARD: CRÁTER AND distance_class in {summit, None}.
  - Recall por bucket de sensor sobre noches ALERTA del loader canónico (A11).
  - Magnitud: mediana per-vol de max(dash)/max(MIROVA VRP) por noche común.

Bandas (referencia S119 − margen 5pp; magnitud banda paridad [0.5, 2.0]):
  - recall crater VIIRS375 >= 93.4 (ref 98.4), VIIRS750 >= 79.5 (ref 84.5),
    MODIS >= 95.0 (ref 100) — solo si n_noches >= MIN_N_RECALL.
  - magnitud: vol fuera de banda con n>=5 → flag. Excepción documentada:
    Lastarria sub-banda es cat-b Lazufre conocido (AUDIT_S119 §2.3) — solo
    flaggea si ratio > 2.0 (sobre-estimación, que sí sería nuevo).
  - integridad: parse errors o duplicados (datetime_utc, sensor) > 0 → flag.
"""
import sys
import io
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")
OUTDIR = os.path.join(ROOT, "data", "audit_continuous")

WINDOW_DAYS = 60
MIN_N_RECALL = 15   # noches ALERTA mínimas para que el recall del bucket sea flaggeable
MIN_N_RATIO = 5     # noches comunes mínimas para que el ratio per-vol sea flaggeable

VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000
RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}
RATIO_BAND = (0.5, 2.0)
# Excepciones físicas documentadas (AUDIT_S119 §2.3): sub-banda esperada, no flaggear.
UNDER_BAND_KNOWN = {"Lastarria"}


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def main():
    today = datetime.now(timezone.utc).date()
    win = ((today - timedelta(days=WINDOW_DAYS)).isoformat(), today.isoformat())

    def in_win(dt):
        return bool(dt) and win[0] <= dt[:10] <= win[1]

    # 1. MIROVA (loader canónico, CONS ∪ OCR): noches ALERTA por (vol, bucket, fecha)
    alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
    mir = defaultdict(float)
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if not in_win(dt) or a["sensor_bucket"] not in SENSORS:
            continue
        key = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[key] = max(mir[key], a["vrp_mw"] or 0.0)

    # 2. Nuestros records (mismos criterios crater/dash del eje2 S119) + integridad
    ours = defaultdict(lambda: {"crater": [], "dash": []})
    integrity = {"parse_errors": [], "duplicates_total": 0}
    for vol in VOLS:
        path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — A47-style corrupción es justo lo vigilado
            integrity["parse_errors"].append(f"{vol}: {e}")
            continue
        seen = set()
        for rec in d["records"]:
            k2 = (rec.get("datetime_utc"), rec.get("sensor"))
            if k2 in seen:
                integrity["duplicates_total"] += 1
            seen.add(k2)
            dt = rec.get("datetime_utc")
            if not in_win(dt):
                continue
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cdist = pc.get("centroid_dist_km")
            if (0 < vrp <= CAP) and (cdist is not None and cdist <= INNER[vol]):
                key = (vol, b, dt[:10])
                ours[key]["crater"].append(vrp)
                dclass = rec.get("distance_class")
                if not dclass or dclass == "summit":
                    ours[key]["dash"].append(vrp)

    # 3. Recall por sensor + magnitud per-vol
    agg = {s: {"n": 0, "c": 0, "d": 0} for s in SENSORS}
    ratios_by_vol = defaultdict(list)
    for (vol, s, date), mvrp in mir.items():
        if vol not in VOLS:
            continue
        agg[s]["n"] += 1
        o = ours.get((vol, s, date))
        if o and o["crater"]:
            agg[s]["c"] += 1
        if o and o["dash"]:
            agg[s]["d"] += 1
            if mvrp > 0:
                ratios_by_vol[vol].append(max(o["dash"]) / mvrp)

    recall = {}
    for s in SENSORS:
        n = agg[s]["n"]
        recall[s] = {"n_noches": n,
                     "recall_crater_pct": round(agg[s]["c"] / n * 100, 1) if n else None,
                     "recall_dash_pct": round(agg[s]["d"] / n * 100, 1) if n else None}
    magnitud = {v: {"n_noches": len(r), "ratio_mediano": round(statistics.median(r), 3)}
                for v, r in sorted(ratios_by_vol.items())}

    # 4. Flags contra bandas
    flags = []
    for s in SENSORS:
        r = recall[s]
        if r["n_noches"] >= MIN_N_RECALL and r["recall_crater_pct"] is not None \
                and r["recall_crater_pct"] < RECALL_MIN[s]:
            flags.append(f"recall {s} {r['recall_crater_pct']}% < banda {RECALL_MIN[s]}% "
                         f"(n={r['n_noches']})")
    for v, m in magnitud.items():
        if m["n_noches"] < MIN_N_RATIO:
            continue
        lo, hi = RATIO_BAND
        if m["ratio_mediano"] > hi:
            flags.append(f"magnitud {v} {m['ratio_mediano']}x > {hi} (SOBRE-estima, n={m['n_noches']})")
        elif m["ratio_mediano"] < lo and v not in UNDER_BAND_KNOWN:
            flags.append(f"magnitud {v} {m['ratio_mediano']}x < {lo} (n={m['n_noches']})")
    if integrity["parse_errors"]:
        flags.append(f"integridad: {len(integrity['parse_errors'])} JSON con parse error")
    if integrity["duplicates_total"]:
        flags.append(f"integridad: {integrity['duplicates_total']} records duplicados (datetime,sensor)")

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": list(win),
        "criteria": "eje2 S119 (crater A10 + dash), loader canónico CONS∪OCR",
        "recall": recall,
        "magnitud_ratio_by_vol": magnitud,
        "integrity": integrity,
        "flags": flags,
        "verdict": "FUERA_DE_BANDA" if flags else "VERDE",
    }
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    hist_line = {"date": out["generated_utc"][:10], "verdict": out["verdict"],
                 "recall": {s: recall[s]["recall_crater_pct"] for s in SENSORS},
                 "n_flags": len(flags)}
    with open(os.path.join(OUTDIR, "history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(hist_line, ensure_ascii=False) + "\n")

    print(f"Auto-audit semanal — ventana {win[0]} → {win[1]}")
    for s in SENSORS:
        r = recall[s]
        print(f"  {s:<9} recall crater {r['recall_crater_pct']}% (n={r['n_noches']})")
    for v, m in magnitud.items():
        print(f"  ratio {v:<20} {m['ratio_mediano']}x (n={m['n_noches']})")
    print(f"VEREDICTO: {out['verdict']}" + (f" — {len(flags)} flags" if flags else ""))
    for fl in flags:
        print("  ⚠", fl)


if __name__ == "__main__":
    main()
