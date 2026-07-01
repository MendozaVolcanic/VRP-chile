#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S119 AUDITORIA — Eje 2 (tareas 2.2 recall por sensor + 2.3 magnitud A10).

POR QUE:
  MIROVA es la hoja de respuestas (CONS ∪ OCR via loader canonico, regla A11).
  Cruzamos noche-satelite ALERTA MIROVA vs records summit nuestros por bucket
  (MODIS / VIIRS750 / VIIRS375), patron S114/S116 (parity_by_sensor_s114.py):
    - CRATER (pipeline): pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND vrp<=50000
    - DASHBOARD (operador): CRATER AND distance_class in {summit, None}
  Referencia S116 (CONS-only, ventana ~mayo-jun): VIIRS375 98.4% / V750 85% /
  MODIS crater 100% (dashboard 12.5% = etiquetado A46, no deteccion).
  Se reporta el universo CONS-only (comparable a S116) Y CONS∪OCR (loader A11).

  Magnitud (A10): ratio mediano max(pc.vrp summit dashboard) / max(VRP_MW MIROVA)
  por noche comun (ALERTA con VRP>0), por volcan. Banda paridad focales [0.5, 2.0].

Matching por fecha UTC de la pasada (dt[:10]), patron S114 (Fecha_Satelite_UTC
vs datetime_utc — ambos UTC, sin conversion a hora local).
"""
import sys, io, json, os, statistics
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")

WIN_FULL = ("2026-01-01", "2026-12-31")   # 2026 completa
WIN_S116 = ("2026-05-01", "2026-06-30")   # ventana comparable S114/S116

VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000  # cap mirovaEqVrp


def our_bucket(sensor):
    # Convencion real del repo (A48): MODIS_* -> MODIS; VIIRS_*_750 -> VIIRS750;
    # VIIRS_SNPP/NOAA2x sin sufijo -> VIIRS375 (I-band).
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def in_win(dt, win):
    return bool(dt) and win[0] <= dt[:10] <= win[1]


# ---------- 1. MIROVA (loader canonico) : noches ALERTA por (vol,sensor,fecha) ----------
alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)


def mirova_nights(universe, win):
    """universe: 'CONS' (solo CONS) o 'UNION' (CONS∪OCR). -> {(vol,bucket,date): max_vrp}"""
    nights = defaultdict(float)
    seen = set()
    for a in alertas:
        if universe == "CONS" and a["source"] != "CONS":
            continue
        dt = a["fecha_utc"] or ""
        if not in_win(dt, win):
            continue
        if a["sensor_bucket"] not in SENSORS:
            continue
        key = (a["volcano"], a["sensor_bucket"], dt[:10])
        seen.add(key)
        nights[key] = max(nights[key], a["vrp_mw"] or 0.0)
    return {k: nights[k] for k in seen}


# ---------- 2. Nuestros records summit ----------
ours = defaultdict(lambda: {"crater": [], "dash": []})
for vol in VOLS:
    path = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    d = json.load(open(path, encoding="utf-8"))
    inner = INNER[vol]
    for rec in d["records"]:
        dt = rec.get("datetime_utc")
        if not in_win(dt, WIN_FULL):
            continue
        b = our_bucket(rec.get("sensor", ""))
        if b is None:
            continue
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0       # A10: pc.vrp_mw, NUNCA record.vrp_mw
        cdist = pc.get("centroid_dist_km")
        dclass = rec.get("distance_class")
        crater_ok = (0 < vrp <= CAP) and (cdist is not None and cdist <= inner)
        if crater_ok:
            key = (vol, b, dt[:10])
            ours[key]["crater"].append(vrp)
            if not dclass or dclass == "summit":
                ours[key]["dash"].append(vrp)


# ---------- 3. Recall por sensor (x universo x ventana) + magnitud ----------
def run(universe, win, tag):
    mir = mirova_nights(universe, win)
    agg = {s: {"n": 0, "c": 0, "d": 0} for s in SENSORS}
    byvs = []
    ratios_by_vol = defaultdict(list)
    for vol in VOLS:
        for s in SENSORS:
            nights = [(k[2], v) for k, v in mir.items() if k[0] == vol and k[1] == s]
            n = len(nights)
            c = d_ = 0
            for date, mvrp in nights:
                o = ours.get((vol, s, date))
                if o and o["crater"]:
                    c += 1
                if o and o["dash"]:
                    d_ += 1
                    if mvrp > 0:
                        ratios_by_vol[vol].append(max(o["dash"]) / mvrp)
            agg[s]["n"] += n
            agg[s]["c"] += c
            agg[s]["d"] += d_
            if n:
                byvs.append({"vol": vol, "sensor": s, "n_alerta": n,
                             "det_crater": c, "det_dash": d_,
                             "recall_crater_pct": round(c / n * 100, 1),
                             "recall_dash_pct": round(d_ / n * 100, 1)})
    out = {"tag": tag, "universe": universe, "window": list(win),
           "agg": {s: {**agg[s],
                       "recall_crater_pct": round(agg[s]["c"] / agg[s]["n"] * 100, 1) if agg[s]["n"] else None,
                       "recall_dash_pct": round(agg[s]["d"] / agg[s]["n"] * 100, 1) if agg[s]["n"] else None}
                   for s in SENSORS},
           "by_vol_sensor": byvs}
    if tag == "full2026_union":
        out["magnitud_ratio_by_vol"] = {
            v: {"n_noches": len(r), "ratio_mediano": round(statistics.median(r), 3)}
            for v, r in sorted(ratios_by_vol.items()) if r}
    return out


results = {
    "csv_rows": {"cons": 25210, "ocr": 737, "cons_prev": 17966, "ocr_prev": 520},
    "runs": [
        run("CONS", WIN_S116, "winS116_cons"),    # comparable a referencia S116
        run("CONS", WIN_FULL, "full2026_cons"),
        run("UNION", WIN_FULL, "full2026_union"),  # loader canonico A11 + magnitud
    ],
}

json.dump(results, open(os.path.join(HERE, "eje2_recall_magnitud.json"), "w",
                        encoding="utf-8"), indent=1)

for r in results["runs"]:
    print(f"\n=== {r['tag']}  universo={r['universe']}  ventana={r['window']} ===")
    print("  sensor    n_ALERTA  recall_CRATER  recall_DASH")
    for s in SENSORS:
        a = r["agg"][s]
        print(f"  {s:<9} {a['n']:>7}   {a['recall_crater_pct']}%   {a['recall_dash_pct']}%")
    if "magnitud_ratio_by_vol" in r:
        print("\n  MAGNITUD (ratio mediano pc.vrp/MIROVA, noches ALERTA VRP>0):")
        for v, m in r["magnitud_ratio_by_vol"].items():
            print(f"    {v:<20} n={m['n_noches']:>3}  ratio={m['ratio_mediano']}")
print("\nWROTE eje2_recall_magnitud.json")
