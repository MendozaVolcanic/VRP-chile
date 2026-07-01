#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S119 Eje 2 — extras reproducibles (S91):
  (a) Villarrica post-16-jun por sensor (2.4-extra, distingue senal real vs A69);
  (b) cobertura/limites del A/B S118 C2 desde windows.json (2.5);
  (c) detalle de outliers de magnitud (2.3): Lastarria (0.47x) y Llaima (n=2).
"""
import sys, io, json, os, math, statistics
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")

out = {}

# (a) Villarrica post-16-jun por sensor — reusa eje2_espacial.json
esp = json.load(open(os.path.join(HERE, "eje2_espacial.json"), encoding="utf-8"))
recs = [x for x in esp["villarrica_jun2026"]["our_records"] if x["dt"] >= "2026-06-16"]
by = defaultdict(list)
for x in recs:
    by[x["sensor"]].append(x)
out["villarrica_post16_por_sensor"] = {}
for s, xs in sorted(by.items()):
    v = [x["pc_vrp_mw"] for x in xs]
    dd = [x["pc_dist_vent_km"] for x in xs if x["pc_dist_vent_km"] is not None]
    out["villarrica_post16_por_sensor"][s] = {
        "n": len(xs), "med_vrp_mw": round(statistics.median(v), 3),
        "med_dist_vent_km": round(statistics.median(dd), 2),
        "frac_dist_lt1km": round(sum(1 for z in dd if z < 1.0) / len(dd), 2)}

# (b) limites A/B S118
w = json.load(open(os.path.join(ROOT, "experiments", "_s118_c2ab", "windows.json"),
                   encoding="utf-8"))
inc = w["include"]
out["s118_ab_limits"] = {
    "ventana_temporal": [min(x["start"] for x in inc), max(x["end"] for x in inc)],
    "n_windows_include": len(inc),
    "kinds": dict(Counter(x["kind"] for x in inc)),
    "por_volcan": {v: {"alerta_dates_total": s["n_alerta_dates"],
                       "chunks_kept": s["n_chunks_kept"],
                       "chunks_candidate": s["n_chunks_candidate"],
                       "chunks_dropped": s["n_chunks_dropped"]}
                   for v, s in w["summary"].items()},
    "config": w["config"],
}

# (c) outliers de magnitud: Lastarria y Llaima, por sensor, noches ALERTA VRP>0 2026
alertas = load_mirova_alertas(cons_path=CONS, ocr_path=OCR)
INNER = {"Lastarria": 3, "Llaima": 5}
CAP = 50000


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


out["magnitud_outliers"] = {}
for vol in ["Lastarria", "Llaima"]:
    mir = defaultdict(float)
    for a in alertas:
        dt = a["fecha_utc"] or ""
        if a["volcano"] != vol or not dt.startswith("2026"):
            continue
        if a["sensor_bucket"] in ("MODIS", "VIIRS750", "VIIRS375") and (a["vrp_mw"] or 0) > 0:
            k = (a["sensor_bucket"], dt[:10])
            mir[k] = max(mir[k], a["vrp_mw"])
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"),
                       encoding="utf-8"))
    ours = defaultdict(list)
    for rec in d["records"]:
        dt = rec.get("datetime_utc") or ""
        if not dt.startswith("2026"):
            continue
        b = our_bucket(rec.get("sensor", ""))
        pc = rec.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0
        cd = pc.get("centroid_dist_km")
        dclass = rec.get("distance_class")
        if b and 0 < vrp <= CAP and cd is not None and cd <= INNER[vol] \
                and (not dclass or dclass == "summit"):
            ours[(b, dt[:10])].append(vrp)
    ratios_by_sensor = defaultdict(list)
    pairs = []
    for k, mv in mir.items():
        if k in ours:
            r = max(ours[k]) / mv
            ratios_by_sensor[k[0]].append(r)
            pairs.append({"sensor": k[0], "date": k[1], "mirova_mw": mv,
                          "ours_mw": round(max(ours[k]), 3), "ratio": round(r, 3)})
    out["magnitud_outliers"][vol] = {
        "por_sensor": {s: {"n": len(r), "ratio_mediano": round(statistics.median(r), 3)}
                       for s, r in sorted(ratios_by_sensor.items())},
        "pares": sorted(pairs, key=lambda x: x["date"]) if vol == "Llaima" else
                 f"{len(pairs)} pares (ver ratios por sensor)"}

json.dump(out, open(os.path.join(HERE, "eje2_extras.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1, ensure_ascii=False))
print("\nWROTE eje2_extras.json")
