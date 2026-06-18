#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FICHA SDA — Auditoria de PARIDAD por-vol x sensor vs MIROVA (post-adopcion VIIRS375 Muy Bajo, S112).

POR QUE (fenomeno -> mecanismo -> numeros):
  MIROVA es la hoja de respuestas. Para cada noche-satelite de cada volcan, comparamos
  si detectamos la anomalia termica AL CRATER y con que magnitud. Distinguimos 3 sensores
  porque cada uno ve fisica distinta (MODIS 1km integra mucho fondo; VIIRS750 M-band;
  VIIRS375 I-band resuelve focos sub-pixel mas finos).

Mapeo de sensores (A48 convencion del proyecto):
  - MODIS_TERRA / MODIS_AQUA              -> MIROVA "MODIS"
  - VIIRS_*_750 (sufijo _750)             -> MIROVA "VIIRS"  (M-band 750m)
  - VIIRS_SNPP/NOAA20/NOAA21 (sin sufijo) -> MIROVA "VIIRS375" (I-band 375m)

Criterio "detectado al crater" (independiente del bug ancla MODIS A69/D11):
  pc.vrp_mw > 0  AND  pc.centroid_dist_km <= inner_radius_km   (A10 usar pc.vrp; A68 inner grande pinta summit)
  Reportamos tambien distance_class record-level para transparencia (afectado por ancla MODIS OFF).

Emparejado por-noche por-sensor (A67 ratio por-noche por-sensor):
  Agrupamos por (fecha calendario UTC, bucket-sensor). MIROVA agrupa SNPP/NOAA20/NOAA21
  bajo "VIIRS375" y reporta 1 valor por pasada; nosotros tenemos 3 plataformas con timestamps
  distintos la misma noche. Tomamos el MAX pc.vrp_mw summit nuestro vs el MAX VRP_MW MIROVA
  de esa noche+sensor. RATIO = mediana(nuestro/ MIROVA) sobre noches con ambos > 0.

Ventana: mayo-junio 2026 (2026-05-01 .. 2026-06-30 inclusive).
"""
import csv, json, os, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONS = os.path.join(ROOT, "experiments", "_s111_d11", "mirova_fresh", "cons.csv")

WIN_START = "2026-05-01"
WIN_END   = "2026-06-30"  # inclusive (comparamos prefijo fecha <= '2026-06-30')

# 11 Tier A: nombre JSON -> nombre en cons.csv (A14 variantes)
VOLS = {
    "Lascar":            "Lascar",
    "Lastarria":         "Lastarria",
    "Tupungatito":       "Tupungatito",
    "PlanchonPeteroa":   "PlanchonPeteroa",
    "NevadosDeChillan":  "Nevados de Chillan",
    "Chaiten":           "Chaiten",
    "Villarrica":        "Villarrica",
    "Llaima":            "Llaima",
    "Copahue":           "Copahue",
    "Isluga":            "Isluga",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
}

INNER = {  # inner_radius_km de volcanoes.yaml
    "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
    "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
    "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20,
}

SENSORS = ["MODIS", "VIIRS750", "VIIRS375"]


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def in_window(dt):
    if not dt:
        return False
    d = dt[:10]
    return WIN_START <= d <= WIN_END


# ---------- 1. Cargar MIROVA cons.csv ----------
# mir[(vol, sensor, date)] = {"alerta_vrps": [..], "rutina_n": int}
mir = defaultdict(lambda: {"alerta_vrps": [], "rutina_n": 0, "alerta_dist": []})
with open(CONS, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        vol = r["Volcan"]
        if vol not in VOLS.values():
            continue
        dt = r["Fecha_Satelite_UTC"]
        if not in_window(dt):
            continue
        sens = r["Sensor"]  # MODIS / VIIRS / VIIRS375
        if sens == "VIIRS":
            sens = "VIIRS750"
        if sens not in SENSORS:
            continue
        date = dt[:10]
        key = (vol, sens, date)
        tipo = r["Tipo_Registro"]
        try:
            vrp = float(r["VRP_MW"])
        except (ValueError, TypeError):
            vrp = 0.0
        try:
            dist = float(r["Distancia_km"])
        except (ValueError, TypeError):
            dist = None
        if tipo == "ALERTA_TERMICA":
            mir[key]["alerta_vrps"].append(vrp)
            if dist is not None:
                mir[key]["alerta_dist"].append(dist)
        elif tipo == "RUTINA":
            mir[key]["rutina_n"] += 1
        # FALSO_POSITIVO ignorado (etiqueta del scraper, no MIROVA)


# ---------- 2. Cargar nuestros JSON ----------
# ours[(vol, sensor, date)] = {"summit_vrps":[..], "any_record": bool}
ours = defaultdict(lambda: {"summit_vrps": [], "n_records": 0})
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
        date = dt[:10]
        key = (vcons, b, date)
        ours[key]["n_records"] += 1
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0.0
        cdist = pc.get("centroid_dist_km")
        # detectado al crater: pc.vrp>0 y centroide dentro de inner_radius
        if vrp > 0 and cdist is not None and cdist <= inner:
            ours[key]["summit_vrps"].append(vrp)


# ---------- 3. Calcular metricas por vol x sensor ----------
results = []  # dict per (vol, sensor)
for vjson, vcons in VOLS.items():
    inner = INNER[vjson]
    for sens in SENSORS:
        # noches MIROVA ALERTA con este sensor
        alerta_nights = []  # (date, mir_max_vrp)
        rutina_nights = []  # dates RUTINA only (no alerta)
        for (v, s, date), m in mir.items():
            if v != vcons or s != sens:
                continue
            if m["alerta_vrps"]:
                alerta_nights.append((date, max(m["alerta_vrps"])))
            elif m["rutina_n"] > 0:
                rutina_nights.append(date)

        n_alerta = len(alerta_nights)
        # RECALL: de las noches ALERTA, cuantas detectamos al crater
        detected = 0
        ratios = []
        for date, mir_vrp in alerta_nights:
            o = ours.get((vcons, sens, date))
            if o and o["summit_vrps"]:
                detected += 1
                our_max = max(o["summit_vrps"])
                if mir_vrp > 0:
                    ratios.append(our_max / mir_vrp)
        recall = (detected / n_alerta * 100.0) if n_alerta else None
        ratio_med = statistics.median(ratios) if ratios else None

        # SOBRE-DETECCION: noches RUTINA MIROVA donde reportamos summit pc.vrp>0
        overdet = 0
        for date in rutina_nights:
            o = ours.get((vcons, sens, date))
            if o and o["summit_vrps"]:
                overdet += 1
        n_rutina = len(rutina_nights)

        results.append({
            "vol": vjson, "sensor": sens, "inner_km": inner,
            "n_alerta": n_alerta, "detected": detected,
            "recall_pct": round(recall, 1) if recall is not None else None,
            "ratio_med": round(ratio_med, 3) if ratio_med is not None else None,
            "n_ratio": len(ratios),
            "n_rutina": n_rutina, "overdet_rutina": overdet,
            "overdet_pct": round(overdet / n_rutina * 100.0, 1) if n_rutina else None,
        })


# ---------- 4. Imprimir tabla + flags ----------
def fmt(x, w):
    return ("" if x is None else str(x)).rjust(w)

print("VENTANA:", WIN_START, "..", WIN_END, "(mayo-junio 2026)")
print()
hdr = ["VOL", "SENSOR", "inner", "n_ALR", "det", "RECALL%", "RATIO", "n_r", "n_RUT", "ovdet", "ovd%"]
ws = [18, 9, 6, 6, 4, 8, 8, 4, 6, 6, 6]
print(" ".join(h.rjust(w) for h, w in zip(hdr, ws)))
print("-" * (sum(ws) + len(ws)))
for r in results:
    row = [r["vol"], r["sensor"], r["inner_km"], r["n_alerta"], r["detected"],
           r["recall_pct"], r["ratio_med"], r["n_ratio"], r["n_rutina"],
           r["overdet_rutina"], r["overdet_pct"]]
    print(" ".join(fmt(c, w) for c, w in zip(row, ws)))

# FLAGS: lejos de MIROVA
print()
print("=== FLAGS (ratio>3x o <0.3x  |  recall<50% con n_alerta>=5) ===")
for r in results:
    flags = []
    if r["ratio_med"] is not None:
        if r["ratio_med"] > 3.0:
            flags.append("RATIO_ALTO(sobre-estima %.2fx)" % r["ratio_med"])
        elif r["ratio_med"] < 0.3:
            flags.append("RATIO_BAJO(sub-estima %.2fx)" % r["ratio_med"])
    if r["recall_pct"] is not None and r["recall_pct"] < 50 and r["n_alerta"] >= 5:
        flags.append("RECALL_BAJO(%.0f%% n=%d)" % (r["recall_pct"], r["n_alerta"]))
    if flags:
        print("  %-18s %-9s -> %s" % (r["vol"], r["sensor"], "; ".join(flags)))

# dump JSON para verificacion programatica
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parity_result.json")
json.dump(results, open(out, "w", encoding="utf-8"), indent=1)
print()
print("WROTE", out)
