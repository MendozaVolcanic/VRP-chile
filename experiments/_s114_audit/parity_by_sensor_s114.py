#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FICHA SDA — Re-auditoria de PARIDAD por sensor vs MIROVA, S114 (data fresca 2026-06-19).

POR QUE (fenomeno -> mecanismo -> numeros):
  MIROVA es la hoja de respuestas. Para cada noche-satelite de cada volcan, comparamos
  si detectamos la anomalia termica AL CRATER. Distinguimos 3 sensores (MODIS 1km integra
  mucho fondo; VIIRS750 M-band; VIIRS375 I-band resuelve focos sub-pixel mas finos).

  S114 mide DOS criterios para destapar el bug A46 far->summit:
    (1) CRATER (pipeline): el cluster crateriano genuino fue encontrado por el pipeline.
        pc.vrp_mw>0  AND  pc.centroid_dist_km<=inner  AND  pc.vrp_mw<=50000
    (2) DASHBOARD (operador): lo que mirovaEqVrp MUESTRA en el frontend (gate real).
        distance_class=="summit" (o ausente)  AND  (1)
  La BRECHA (1)-(2) = records con cluster crateriano real pero etiquetados "far" por el
  bug A46 (final_hotspot apunta a Salar/fuego/glaciar que roba el hotspot) -> OCULTOS.

Mapeo de sensores (A48): MODIS_* -> MODIS ; VIIRS_*_750 -> VIIRS750 ; VIIRS_SNPP/NOAA* -> VIIRS375.
Emparejado por-noche por-sensor (A67). MAX pc.vrp summit nuestro vs MAX VRP_MW MIROVA esa noche+sensor.
Ventana: 2026-05-01 .. 2026-06-30.
"""
import csv, json, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")  # A17 fresco 2026-06-19

WIN_START = "2026-05-01"
WIN_END   = "2026-06-30"

VOLS = {
    "Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
    "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
    "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
    "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
}
INNER = {
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
    "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
    "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20,
}
SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]
CAP = 50000  # mirovaEqVrp cap


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def in_window(dt):
    return bool(dt) and WIN_START <= dt[:10] <= WIN_END


# ---------- 1. MIROVA cons.csv ----------
mir = defaultdict(lambda: {"alerta_vrps": [], "rutina_n": 0})
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vol = r["Volcan"]
        if vol not in VOLS.values():
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        sens = r["Sensor"]
        if sens == "VIIRS":
            sens = "VIIRS750"
        if sens not in SENSORS:
            continue
        key = (vol, sens, dt[:10])
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        if r["Tipo_Registro"] == "ALERTA_TERMICA":
            mir[key]["alerta_vrps"].append(vrp)
        elif r["Tipo_Registro"] == "RUTINA":
            mir[key]["rutina_n"] += 1


# ---------- 2. Nuestros JSON: ambos criterios + captura far->summit ----------
# ours[(vol,sens,date)] = {"crater":[vrp..], "dash":[vrp..]}
ours = defaultdict(lambda: {"crater": [], "dash": []})
far2summit = []  # records cluster crateriano real pero distance_class=="far" (A46 oculto)
for vjson, vcons in VOLS.items():
    path = os.path.join(ROOT, "data", "mirova_equivalent", vjson + ".json")
    d = json.load(open(path, encoding="utf-8"))
    inner = INNER[vjson]
    for rec in d["records"]:
        dt = rec.get("datetime_utc")
        if not in_window(dt):
            continue
        b = our_bucket(rec.get("sensor", ""))
        if b is None:
            continue
        key = (vcons, b, dt[:10])
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        cdist = pc.get("centroid_dist_km")
        dclass = rec.get("distance_class")
        crater_ok = (0 < vrp <= CAP) and (cdist is not None and cdist <= inner)
        dash_ok = crater_ok and (not dclass or dclass == "summit")
        if crater_ok:
            ours[key]["crater"].append(vrp)
        if dash_ok:
            ours[key]["dash"].append(vrp)
        # far->summit: cluster crateriano genuino PERO etiquetado far -> oculto
        if crater_ok and dclass == "far":
            far2summit.append({
                "vol": vjson, "sensor": b, "date": dt[:10], "datetime": dt,
                "pc_vrp_mw": round(vrp, 3), "centroid_dist_km": round(cdist, 2),
                "final_hotspot_dist_km": rec.get("final_hotspot_dist_km"),
                "final_hotspot_source": rec.get("final_hotspot_source"),
                "nti_max": rec.get("nti_max"),
            })


# ---------- 3. Metricas por vol x sensor + agregado por sensor ----------
results = []
agg = {s: {"n_alerta": 0, "det_crater": 0, "det_dash": 0} for s in SENSORS}
for vjson, vcons in VOLS.items():
    for sens in SENSORS:
        alerta_nights = []
        for (v, s, date), m in mir.items():
            if v == vcons and s == sens and m["alerta_vrps"]:
                alerta_nights.append((date, max(m["alerta_vrps"])))
        n_alerta = len(alerta_nights)
        det_crater = det_dash = 0
        ratios_dash = []
        for date, mir_vrp in alerta_nights:
            o = ours.get((vcons, sens, date))
            if o and o["crater"]:
                det_crater += 1
            if o and o["dash"]:
                det_dash += 1
                if mir_vrp > 0:
                    ratios_dash.append(max(o["dash"]) / mir_vrp)
        agg[sens]["n_alerta"] += n_alerta
        agg[sens]["det_crater"] += det_crater
        agg[sens]["det_dash"] += det_dash
        results.append({
            "vol": vjson, "sensor": sens, "inner_km": INNER[vjson],
            "n_alerta": n_alerta, "det_crater": det_crater, "det_dash": det_dash,
            "recall_crater_pct": round(det_crater / n_alerta * 100, 1) if n_alerta else None,
            "recall_dash_pct": round(det_dash / n_alerta * 100, 1) if n_alerta else None,
            "gap_records": det_crater - det_dash,
            "ratio_dash_med": round(statistics.median(ratios_dash), 3) if ratios_dash else None,
        })


# ---------- 4. Salida ----------
print("RE-AUDITORIA PARIDAD POR SENSOR S114 — cons fresco 2026-06-19")
print("VENTANA:", WIN_START, "..", WIN_END)
print()
print(">>> AGREGADO POR SENSOR (rollup 11 Tier A) <<<")
print("  sensor    n_ALERTA  recall_CRATER  recall_DASHBOARD  brecha(far->summit oculto)")
for s in SENSORS:
    a = agg[s]
    rc = a["det_crater"] / a["n_alerta"] * 100 if a["n_alerta"] else 0
    rd = a["det_dash"] / a["n_alerta"] * 100 if a["n_alerta"] else 0
    print("  %-9s %7d   %6.1f%% (%d/%d)   %6.1f%% (%d/%d)   %d noches" % (
        s, a["n_alerta"], rc, a["det_crater"], a["n_alerta"],
        rd, a["det_dash"], a["n_alerta"], a["det_crater"] - a["det_dash"]))
print()
print(">>> POR VOL x SENSOR (solo filas con n_alerta>0 o brecha>0) <<<")
print("  %-18s %-9s %5s %6s %6s %8s %8s %5s" % (
    "VOL", "SENSOR", "n_ALR", "detC", "detD", "recC%", "recD%", "gap"))
for r in results:
    if r["n_alerta"] == 0 and r["gap_records"] == 0:
        continue
    print("  %-18s %-9s %5d %6d %6d %8s %8s %5d" % (
        r["vol"], r["sensor"], r["n_alerta"], r["det_crater"], r["det_dash"],
        r["recall_crater_pct"], r["recall_dash_pct"], r["gap_records"]))

print()
print(">>> RECORDS far->summit OCULTOS (cluster crateriano real, distance_class=far) <<<")
print("  total:", len(far2summit))
by_vs = defaultdict(int)
for x in far2summit:
    by_vs[(x["vol"], x["sensor"])] += 1
for (v, s), n in sorted(by_vs.items(), key=lambda kv: -kv[1]):
    print("  %-18s %-9s  %d records" % (v, s, n))

json.dump({"agg": agg, "by_vol_sensor": results, "far2summit": far2summit},
          open(os.path.join(HERE, "parity_s114_result.json"), "w", encoding="utf-8"), indent=1)
print()
print("WROTE parity_s114_result.json (", len(far2summit), "far->summit records )")
