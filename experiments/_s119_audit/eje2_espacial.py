#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S119 AUDITORIA — Eje 2, tarea 2.4 (eje espacial A61/A70) + 2.4-extra (Villarrica jun-2026).

POR QUE:
  A70: auditar el offset DIRECCIONAL con MEDIANA (Δlat, Δlon por separado), no la
  distancia con media — la mediana robusta revela sesgos sistemáticos que |dist| oculta.
  Referencia conocida: sesgo N ~1-1.5 km en nevados (residuo A69 irreducible).
  FLAG solo si sesgo NUEVO: >2 km mediano o rumbo distinto al conocido.

  Ventanas: POST-FLIP gates C2 (>= 2026-06-28T21:00Z, S118 #474) y ultimos ~30d
  (>= 2026-06-01) para robustez estadistica.

  2.4-extra: Villarrica salto 0.06 -> ~1.4 MW mediana summit el 16-jun (MIROVA CONS=0).
  (i) posicion del cluster summit vs crater; (ii) OCR fresco Villarrica jun-2026.
"""
import sys, io, json, os, math, statistics
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

import yaml  # noqa: E402

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
POST_FLIP = "2026-06-28T21:00"
LAST30 = "2026-06-01"


def our_bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return None


def bearing(dlat_km, dlon_km):
    """Cuadrante dominante del vector mediano."""
    if abs(dlat_km) < 0.05 and abs(dlon_km) < 0.05:
        return "-"
    ns = "N" if dlat_km > 0 else "S"
    ew = "E" if dlon_km > 0 else "W"
    if abs(dlat_km) > 2 * abs(dlon_km):
        return ns
    if abs(dlon_km) > 2 * abs(dlat_km):
        return ew
    return ns + ew


# ---------- vents fisicos desde volcanoes.yaml ----------
vy = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
vents = {}
for v in vy["volcanoes"]:
    if v["name"] in VOLS:
        vents[v["name"]] = (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))

# ---------- offsets ----------
def collect(win_start):
    """-> {(vol,bucket): {'final':[(dlat,dlon,dist)..], 'pc':[...]}} solo records
    con pc.vrp>0 (senal de cluster) — mide donde ANCLA el pipeline."""
    out = defaultdict(lambda: {"final": [], "pc": []})
    for vol in VOLS:
        vlat, vlon = vents[vol]
        klon = 111.32 * math.cos(math.radians(vlat))
        d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"),
                           encoding="utf-8"))
        for rec in d["records"]:
            dt = rec.get("datetime_utc") or ""
            if dt < win_start:
                continue
            b = our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            pc = rec.get("primary_cluster") or {}
            if not (pc.get("vrp_mw") or 0):
                continue
            for tagf, (la, lo) in {
                "final": (rec.get("final_hotspot_lat"), rec.get("final_hotspot_lon")),
                "pc": (pc.get("centroid_lat"), pc.get("centroid_lon")),
            }.items():
                if la is None or lo is None:
                    continue
                dlat = (la - vlat) * 111.32
                dlon = (lo - vlon) * klon
                out[(vol, b)][tagf].append((dlat, dlon, math.hypot(dlat, dlon)))
    return out


def summarize(coll):
    rows = []
    for (vol, b), fields in sorted(coll.items()):
        for tagf, pts in fields.items():
            if not pts:
                continue
            mlat = statistics.median(p[0] for p in pts)
            mlon = statistics.median(p[1] for p in pts)
            mdist = statistics.median(p[2] for p in pts)
            rows.append({"vol": vol, "sensor": b, "field": tagf, "n": len(pts),
                         "med_dlat_km": round(mlat, 2), "med_dlon_km": round(mlon, 2),
                         "med_dist_km": round(mdist, 2), "rumbo": bearing(mlat, mlon),
                         "flag_gt2km": bool(mdist > 2.0)})
    return rows


res = {"post_flip": summarize(collect(POST_FLIP)),
       "last30d": summarize(collect(LAST30))}

# ---------- 2.4-extra Villarrica junio 2026 ----------
vlat, vlon = vents["Villarrica"]
klon = 111.32 * math.cos(math.radians(vlat))
vd = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", "Villarrica.json"),
                    encoding="utf-8"))
vil = []
for rec in vd["records"]:
    dt = rec.get("datetime_utc") or ""
    if not dt.startswith("2026-06"):
        continue
    pc = rec.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0
    if not vrp:
        continue
    dclass = rec.get("distance_class")
    if dclass and dclass != "summit":
        continue
    la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
    dist = math.hypot((la - vlat) * 111.32, (lo - vlon) * klon) if la is not None else None
    vil.append({"dt": dt, "sensor": our_bucket(rec.get("sensor", "")),
                "pc_vrp_mw": round(vrp, 3),
                "pc_dist_vent_km": round(dist, 2) if dist is not None else None,
                "nti_max": rec.get("nti_max")})
vil.sort(key=lambda x: x["dt"])
pre = [x["pc_vrp_mw"] for x in vil if x["dt"] < "2026-06-16"]
post = [x["pc_vrp_mw"] for x in vil if x["dt"] >= "2026-06-16"]
post_d = [x["pc_dist_vent_km"] for x in vil if x["dt"] >= "2026-06-16"
          and x["pc_dist_vent_km"] is not None]
vil_sum = {
    "n_pre16": len(pre), "med_vrp_pre16": round(statistics.median(pre), 3) if pre else None,
    "n_post16": len(post), "med_vrp_post16": round(statistics.median(post), 3) if post else None,
    "med_dist_vent_post16_km": round(statistics.median(post_d), 2) if post_d else None,
    "frac_post16_dist_lt1km": round(sum(1 for d_ in post_d if d_ < 1.0) / len(post_d), 2) if post_d else None,
}

# OCR fresco Villarrica jun-2026
alertas = load_mirova_alertas(
    cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
    ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"), volcano="Villarrica")
ocr_jun = sorted([{"fecha_utc": a["fecha_utc"], "sensor": a["sensor_bucket"],
                   "vrp_mw": a["vrp_mw"], "dist_km": a["dist_km"], "source": a["source"]}
                  for a in alertas if (a["fecha_utc"] or "").startswith("2026-06")],
                 key=lambda x: x["fecha_utc"])

res["villarrica_jun2026"] = {"summary": vil_sum, "our_records": vil,
                             "mirova_alertas_jun": ocr_jun,
                             "n_ocr_only": sum(1 for x in ocr_jun if x["source"] == "OCR")}

json.dump(res, open(os.path.join(HERE, "eje2_espacial.json"), "w", encoding="utf-8"), indent=1)

print("=== 2.4 POST-FLIP (>= %s) — solo filas flag o n>=5 ===" % POST_FLIP)
print("vol/sensor/field         n   dLat_km dLon_km |dist| rumbo FLAG")
for r in res["post_flip"]:
    print(f"{r['vol']:<20}{r['sensor']:<9}{r['field']:<6}{r['n']:>4} "
          f"{r['med_dlat_km']:>7} {r['med_dlon_km']:>7} {r['med_dist_km']:>6} "
          f"{r['rumbo']:>4} {'<<FLAG' if r['flag_gt2km'] else ''}")
print("\n=== 2.4 LAST30D (>= %s) ===" % LAST30)
for r in res["last30d"]:
    print(f"{r['vol']:<20}{r['sensor']:<9}{r['field']:<6}{r['n']:>4} "
          f"{r['med_dlat_km']:>7} {r['med_dlon_km']:>7} {r['med_dist_km']:>6} "
          f"{r['rumbo']:>4} {'<<FLAG' if r['flag_gt2km'] else ''}")
print("\n=== 2.4-extra VILLARRICA jun-2026 ===")
print(json.dumps(vil_sum, indent=1))
print("MIROVA ALERTAs jun (CONS∪OCR):", len(ocr_jun), "| OCR-only:",
      res["villarrica_jun2026"]["n_ocr_only"])
for x in ocr_jun:
    print(" ", x["fecha_utc"], x["sensor"], f"VRP={x['vrp_mw']}", f"dist={x['dist_km']}",
          x["source"])
print("\nWROTE eje2_espacial.json")
