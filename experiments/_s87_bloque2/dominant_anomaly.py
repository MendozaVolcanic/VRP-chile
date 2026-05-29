"""S87 Bloque 2 parte 2 — Validación 1:1 anomalía dominante + cruce binario actualizado.

Pregunta central (refinamiento Nicolás S86): para cada pasada satelital donde
MIROVA reporta SU mayor anomalía a una distancia D_mirova del centro, ¿la mayor
anomalía que NOSOTROS reportamos cae en el mismo punto?

Dos criterios de selección de "nuestra mayor" se evalúan offline (A/B sin
reproceso, porque los `anomaly_pixels` crudos están persistidos en el JSON):

  - "vent_anchored": el `primary_cluster` que el pipeline ya eligió (S38 D8 fix,
    prioriza proximidad al vent sobre magnitud).
  - "vrp_max": el cluster de mayor VRP de toda la escena, reconstruido con
    `cluster_pixels_geographic` sobre `anomaly_pixels` (lo que MIROVA hace:
    reportar la anomalía más fuerte de la escena).

Distancias: TODAS recalculadas desde `mirova_center` del volcanoes.yaml para ser
comparables con MIROVA (que mide desde su coord de referencia ≈ Smithsonian GVP).
NO usar `pc.centroid_dist_km` (mide desde vent) ni `pixel.dist_km` (mide desde
mirova_center) mezclados — A3 schema gap.

Salidas:
  - dominant_anomaly.json — métricas por volcán × sensor × criterio.
  - dominant_anomaly.md — lectura geológica + tablas.
  - crossing_loader.json — cruce binario TP/FP con el loader canónico (cierra
    Bloque 2 parte 2: muestra que el loader NO mueve el gap a nivel noche).
"""
from __future__ import annotations

import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from pipeline.clustering import cluster_pixels_geographic  # noqa: E402

CHILE_TZ = "America/Santiago"
CONS = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
OCR = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"

# Tolerancias radiales para "match" de ubicación (km).
TOLS = [1.0, 2.0, 3.0]
TOL_MAIN = 2.0  # tolerancia principal para el veredicto (igual que exp L)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.radians
    dlat = p(lat2 - lat1)
    dlon = p(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# --- volcanoes.yaml: mirova_center + inner_radius por Tier A ---
VY = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
TIERA = {}
for v in VY["volcanoes"]:
    if v.get("mirova_monitored"):
        TIERA[v["name"]] = {
            "mc_lat": float(v["mirova_center_lat"]),
            "mc_lon": float(v["mirova_center_lon"]),
            "inner": float(v.get("inner_radius_km", 5.0)),
        }
TIERA_NAMES = sorted(TIERA)


def json_sensor_bucket(s: str):
    s = (s or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


# ---------------------------------------------------------------------------
# 1. Cargar MIROVA (CONS ∪ OCR) con distancia resuelta
# ---------------------------------------------------------------------------
mirova_all = load_mirova_alertas(str(CONS), str(OCR))
mirova_df = pd.DataFrame(mirova_all)
mirova_df["dt"] = pd.to_datetime(mirova_df["fecha_utc"], utc=True, errors="coerce")
mirova_df = mirova_df[mirova_df["dt"].notna()].copy()
mirova_df["night"] = mirova_df["dt"].dt.tz_convert(CHILE_TZ).dt.date

# Por (vol, sensor, noche): la ALERTA MIROVA de MAYOR vrp = "su mayor anomalía"
mirova_dominant = {}
for (vol, sb, night), g in mirova_df.groupby(["volcano", "sensor_bucket", "night"]):
    best = g.loc[g["vrp_mw"].idxmax()]
    mirova_dominant[(vol, sb, night)] = {
        "dist_km": float(best["dist_km"]) if pd.notna(best["dist_km"]) else None,
        "vrp_mw": float(best["vrp_mw"]),
        "n_alertas": int(len(g)),
        "source": best["source"],
    }


# ---------------------------------------------------------------------------
# 2. Cargar nuestros records, reconstruir escena offline
# ---------------------------------------------------------------------------
def load_our_dominant():
    """Por (vol, sensor, noche): nuestro record de mayor VRP de escena, con
    la ubicación de los dos criterios (vent_anchored y vrp_max)."""
    out = {}
    for vol in TIERA_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{vol}.json"
        if not fp.exists():
            continue
        mc_lat, mc_lon = TIERA[vol]["mc_lat"], TIERA[vol]["mc_lon"]
        data = json.loads(fp.read_text(encoding="utf-8"))
        per_key = defaultdict(list)
        for r in data.get("records", []):
            ap = r.get("anomaly_pixels")
            if not ap:
                continue
            sb = json_sensor_bucket(r.get("sensor", ""))
            if sb is None:
                continue
            dt = pd.to_datetime(r.get("datetime_utc"), utc=True, errors="coerce")
            if pd.isna(dt):
                continue
            night = dt.tz_convert(CHILE_TZ).date()

            # Escena reconstruida — cluster de mayor VRP
            clusters = cluster_pixels_geographic(ap, max_dist_km=1.5)
            if not clusters:
                continue
            top = clusters[0]  # mayor vrp_mw (vrp_max scene)
            vrpmax_dist = haversine_km(mc_lat, mc_lon,
                                       top["centroid_lat"], top["centroid_lon"])
            vrpmax_vrp = float(top["vrp_mw"])

            # vrp_max DENTRO del inner_radius (criterio candidato S87)
            inner = TIERA[vol]["inner"]
            inner_clusters = [
                c for c in clusters
                if haversine_km(mc_lat, mc_lon,
                                c["centroid_lat"], c["centroid_lon"]) <= inner
            ]
            if inner_clusters:
                top_in = inner_clusters[0]  # ya ordenados por vrp desc
                vrpmaxin_dist = haversine_km(mc_lat, mc_lon,
                                             top_in["centroid_lat"],
                                             top_in["centroid_lon"])
                vrpmaxin_vrp = float(top_in["vrp_mw"])
            else:
                vrpmaxin_dist, vrpmaxin_vrp = None, None

            # vent_anchored — el primary que el pipeline eligió.
            pc = r.get("primary_cluster") or {}
            if pc.get("centroid_lat") is not None:
                va_dist = haversine_km(mc_lat, mc_lon,
                                       float(pc["centroid_lat"]),
                                       float(pc["centroid_lon"]))
                va_vrp = float(pc.get("vrp_mw") or 0.0)
            else:
                va_dist, va_vrp = None, None

            per_key[(vol, sb, night)].append({
                "scene_vrp": vrpmax_vrp,
                "vrpmax_dist": vrpmax_dist, "vrpmax_vrp": vrpmax_vrp,
                "vrpmaxin_dist": vrpmaxin_dist, "vrpmaxin_vrp": vrpmaxin_vrp,
                "va_dist": va_dist, "va_vrp": va_vrp,
                "n_clusters": len(clusters),
            })

        # Por key, quedarse con el record de mayor VRP de escena
        for key, lst in per_key.items():
            out[key] = max(lst, key=lambda x: x["scene_vrp"])
    return out


our_dominant = load_our_dominant()


# ---------------------------------------------------------------------------
# 3. Validación 1:1 anomalía dominante (pasadas TP: MIROVA y nosotros presentes)
# ---------------------------------------------------------------------------
def match(our_dist, mir_dist, tol):
    if our_dist is None or mir_dist is None:
        return None
    return abs(our_dist - mir_dist) <= tol


results = defaultdict(lambda: {
    "n_compared": 0,
    "va_match": {t: 0 for t in TOLS},
    "vrpmax_match": {t: 0 for t in TOLS},
    "vrpmaxin_match": {t: 0 for t in TOLS},
    "va_dist_minus_mir": [], "vrpmax_dist_minus_mir": [],
    "mir_dist": [], "va_dist": [], "vrpmax_dist": [],
    "va_vrp_ratio": [], "vrpmax_vrp_ratio": [],
})

detail_rows = []
for key, mir in mirova_dominant.items():
    vol, sb, night = key
    ours = our_dominant.get(key)
    if ours is None:
        continue  # MIROVA reportó pero no tenemos escena con pixels (FN-like)
    if mir["dist_km"] is None:
        continue
    agg = results[(vol, sb)]
    agg["n_compared"] += 1
    for t in TOLS:
        if match(ours["va_dist"], mir["dist_km"], t):
            agg["va_match"][t] += 1
        if match(ours["vrpmax_dist"], mir["dist_km"], t):
            agg["vrpmax_match"][t] += 1
        if match(ours["vrpmaxin_dist"], mir["dist_km"], t):
            agg["vrpmaxin_match"][t] += 1
    if ours["va_dist"] is not None:
        agg["va_dist_minus_mir"].append(ours["va_dist"] - mir["dist_km"])
        agg["va_dist"].append(ours["va_dist"])
    if ours["vrpmax_dist"] is not None:
        agg["vrpmax_dist_minus_mir"].append(ours["vrpmax_dist"] - mir["dist_km"])
        agg["vrpmax_dist"].append(ours["vrpmax_dist"])
    agg["mir_dist"].append(mir["dist_km"])
    if mir["vrp_mw"] > 0:
        if ours["va_vrp"]:
            agg["va_vrp_ratio"].append(ours["va_vrp"] / mir["vrp_mw"])
        if ours["vrpmax_vrp"]:
            agg["vrpmax_vrp_ratio"].append(ours["vrpmax_vrp"] / mir["vrp_mw"])
    detail_rows.append({
        "vol": vol, "sensor": sb, "night": str(night),
        "mir_dist": round(mir["dist_km"], 2), "mir_vrp": round(mir["vrp_mw"], 3),
        "mir_src": mir["source"],
        "va_dist": round(ours["va_dist"], 2) if ours["va_dist"] is not None else None,
        "vrpmax_dist": round(ours["vrpmax_dist"], 2),
        "vrpmaxin_dist": round(ours["vrpmaxin_dist"], 2) if ours["vrpmaxin_dist"] is not None else None,
        "va_vrp": round(ours["va_vrp"], 3) if ours["va_vrp"] is not None else None,
        "vrpmax_vrp": round(ours["vrpmax_vrp"], 3),
    })


def med(lst):
    s = pd.Series(lst).dropna()
    return float(s.median()) if len(s) else None


def pct(num, den):
    return round(100 * num / den, 1) if den else None


# Resumen por volcán (agregando sensores) y por volcán×sensor
summary = {}
for (vol, sb), agg in results.items():
    n = agg["n_compared"]
    summary[f"{vol}|{sb}"] = {
        "n_compared": n,
        "va_match_pct": {str(t): pct(agg["va_match"][t], n) for t in TOLS},
        "vrpmax_match_pct": {str(t): pct(agg["vrpmax_match"][t], n) for t in TOLS},
        "vrpmaxin_match_pct": {str(t): pct(agg["vrpmaxin_match"][t], n) for t in TOLS},
        "med_mir_dist": med(agg["mir_dist"]),
        "med_va_dist": med(agg["va_dist"]),
        "med_vrpmax_dist": med(agg["vrpmax_dist"]),
        "med_va_vrp_ratio": med(agg["va_vrp_ratio"]),
        "med_vrpmax_vrp_ratio": med(agg["vrpmax_vrp_ratio"]),
    }

# Agregado por volcán (todos los sensores juntos)
per_vol = defaultdict(lambda: {"n": 0, "va": {t: 0 for t in TOLS},
                               "vrpmax": {t: 0 for t in TOLS},
                               "vrpmaxin": {t: 0 for t in TOLS}})
for (vol, sb), agg in results.items():
    pv = per_vol[vol]
    pv["n"] += agg["n_compared"]
    for t in TOLS:
        pv["va"][t] += agg["va_match"][t]
        pv["vrpmax"][t] += agg["vrpmax_match"][t]
        pv["vrpmaxin"][t] += agg["vrpmaxin_match"][t]

per_vol_summary = {}
for vol, pv in per_vol.items():
    n = pv["n"]
    per_vol_summary[vol] = {
        "n_compared": n,
        "va_match_pct": pct(pv["va"][TOL_MAIN], n),
        "vrpmax_match_pct": pct(pv["vrpmax"][TOL_MAIN], n),
        "vrpmaxin_match_pct": pct(pv["vrpmaxin"][TOL_MAIN], n),
    }

(OUT / "dominant_anomaly.json").write_text(json.dumps({
    "tol_main_km": TOL_MAIN,
    "per_vol_summary": per_vol_summary,
    "per_vol_sensor": summary,
    "n_detail_rows": len(detail_rows),
}, indent=2, default=str), encoding="utf-8")

(OUT / "dominant_anomaly_detail.json").write_text(
    json.dumps(detail_rows, indent=2, default=str), encoding="utf-8")

print("=== VALIDACIÓN 1:1 ANOMALÍA DOMINANTE (tol=%.0f km) ===" % TOL_MAIN)
print(f"{'Volcán':<22} {'n':>5} {'vent_anch%':>11} {'vrp_max%':>10} {'vrpmax_in%':>11}")
for vol in TIERA_NAMES:
    s = per_vol_summary.get(vol)
    if not s:
        continue
    print(f"{vol:<22} {s['n_compared']:>5} {str(s['va_match_pct']):>11} "
          f"{str(s['vrpmax_match_pct']):>10} {str(s['vrpmaxin_match_pct']):>11}")
print()
print("[OK] dominant_anomaly.json + dominant_anomaly_detail.json escritos")
