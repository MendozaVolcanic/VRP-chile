"""
Experimento J S86 — Huella canónica volcánica per-vol.

Idea geológica (Nicolás): cada volcán tiene una "huella" espacial estable donde
se ubica su anomalía volcánica real, consistente durante el año. Si una detección
cae FUERA de esa huella, probablemente es incendio/artefacto, no el volcán.

La huella 2D se construye desde los CENTROIDES de NUESTROS clusters que
coincidieron con ALERTAs MIROVA (TPs) — por definición, lugares donde MIROVA
confirmó anomalía volcánica real.

Reusa la lógica de matching de script_C (noche local Chile x sensor_bucket x vol)
y las categorías a/b/c/d de E_fp_classification (clasificación geográfica de FPs).

Output: J_canonical_footprint.{json,md}

LIMITACIONES (declaradas):
- El JSON guarda solo el primary_cluster ya seleccionado (criterio vent_anchored
  S38). NO hay clusters alternativos. La huella se construye con el centroide de
  ese primary.
- MIROVA CSV NO tiene lat/lon, solo Distancia_km radial (OCR en Nota_Validacion
  como dist≈XX km; CONS suele ser 0). La huella es de NUESTROS centroides; la
  validación contra MIROVA es solo radial.
- El loader actual tiene bugs F-B1/B2 (OCR no consumido en distancia, alias).
  La huella hereda lo que el cruce exacto produjo.
"""
from __future__ import annotations

import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)
CHILE_TZ = ZoneInfo("America/Santiago")

TIER_A_MAP = {
    "Chaiten": "Chaiten", "Copahue": "Copahue", "Isluga": "Isluga",
    "Lascar": "Lascar", "Lastarria": "Lastarria", "Llaima": "Llaima",
    "Nevados de Chillan": "NevadosDeChillan",
    "PlanchonPeteroa": "PlanchonPeteroa", "Peteroa": "PlanchonPeteroa",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Tupungatito": "Tupungatito", "Villarrica": "Villarrica",
}
SENSORS = ["MODIS", "VIIRS375", "VIIRS750"]
TIER_A_NAMES = sorted(set(TIER_A_MAP.values()))


def csv_sensor_bucket(s):
    if s == "MODIS": return "MODIS"
    if s in ("VIIRS", "VIIRS375"): return "VIIRS375"
    if s == "VIIRS750": return "VIIRS750"
    return None


def json_sensor_bucket(s):
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return None


def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VOLC_YAML = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
VOL_CFG = {}
for v in VOLC_YAML["volcanoes"]:
    if v.get("mirova_monitored"):
        VOL_CFG[v["name"]] = {
            "vent_lat": v.get("vent_lat"), "vent_lon": v.get("vent_lon"),
            "mirova_lat": v.get("mirova_center_lat", v.get("vent_lat")),
            "mirova_lon": v.get("mirova_center_lon", v.get("vent_lon")),
            "inner": float(v.get("inner_radius_km", 5.0)),
        }


# ---------------------------------------------------------------------------
# MIROVA refs (CONS+OCR) -> ALERTA keys
# ---------------------------------------------------------------------------
def load_mirova():
    cons = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ocr = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
    common = ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW",
              "Distancia_km", "Tipo_Registro"]
    cons["source"] = "CONS"; ocr["source"] = "OCR"
    df = pd.concat([cons[common + ["source"]], ocr[common + ["source"]]], ignore_index=True)
    df = df[df["Volcan"].isin(TIER_A_MAP.keys())].copy()
    df["volc_json"] = df["Volcan"].map(TIER_A_MAP)
    df["sensor_bucket"] = df["Sensor"].apply(csv_sensor_bucket)
    df = df[df["sensor_bucket"].notna()]
    df["dt_utc"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df[df["dt_utc"].notna()]
    df["night_local"] = df["dt_utc"].dt.tz_convert(CHILE_TZ).dt.date
    df["is_alerta"] = df["Tipo_Registro"].isin(["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"])
    return df


MIROVA = load_mirova()


# ---------------------------------------------------------------------------
# Our records (publishable per frontend gate)
# ---------------------------------------------------------------------------
def load_ours():
    rows = []
    for name in TIER_A_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{name}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        inner = VOL_CFG.get(name, {}).get("inner", 5.0)
        for r in data.get("records", []):
            bucket = json_sensor_bucket(r.get("sensor", ""))
            if bucket is None:
                continue
            dt_str = r.get("datetime_utc")
            if not dt_str:
                continue
            try:
                dt_utc = pd.to_datetime(dt_str, utc=True)
            except Exception:
                continue
            night = dt_utc.tz_convert(CHILE_TZ).date()
            pc = r.get("primary_cluster") or {}
            pc_vrp = float(pc.get("vrp_mw") or 0.0)
            pc_dist = pc.get("centroid_dist_km")
            pc_dist = float(pc_dist) if pc_dist is not None else None
            pc_lat = pc.get("centroid_lat")
            pc_lon = pc.get("centroid_lon")
            dist_class = r.get("distance_class", "")
            publishable = (pc_vrp > 0 and pc_dist is not None
                           and pc_dist <= inner and dist_class == "summit")
            rows.append({
                "volc_json": name, "sensor_bucket": bucket,
                "dt_utc": dt_utc, "night_local": night,
                "pc_vrp_mw": pc_vrp, "pc_n_pixels": int(pc.get("n_pixels") or 0),
                "pc_centroid_dist_km": pc_dist, "pc_lat": pc_lat, "pc_lon": pc_lon,
                "distance_class": dist_class, "publishable": publishable,
                "t_bg_k": r.get("t_bg_k"), "inner_radius_km": inner,
            })
    return pd.DataFrame(rows)


OURS = load_ours()

# Common window
MIN_N = max(MIROVA["night_local"].min(), OURS["night_local"].min())
MAX_N = min(MIROVA["night_local"].max(), OURS["night_local"].max())
MIROVA = MIROVA[(MIROVA["night_local"] >= MIN_N) & (MIROVA["night_local"] <= MAX_N)]
OURS = OURS[(OURS["night_local"] >= MIN_N) & (OURS["night_local"] <= MAX_N)]

mirova_alerta_keys = set(
    (r["volc_json"], r["sensor_bucket"], r["night_local"])
    for _, r in MIROVA[MIROVA["is_alerta"]].iterrows()
)

# TP = our publishable record on a night-sensor MIROVA also alerted
OURS["key"] = list(zip(OURS["volc_json"], OURS["sensor_bucket"], OURS["night_local"]))
OURS["is_tp"] = OURS["publishable"] & OURS["key"].isin(mirova_alerta_keys)
OURS["is_fp"] = OURS["publishable"] & ~OURS["key"].isin(mirova_alerta_keys)

print(f"[INFO] window {MIN_N}->{MAX_N} | OURS rows {len(OURS)} | "
      f"publishable {OURS['publishable'].sum()} | TP {OURS['is_tp'].sum()} | FP {OURS['is_fp'].sum()}")


# ---------------------------------------------------------------------------
# Geographic classification of FPs (replicada de script_E, simplificada)
# ---------------------------------------------------------------------------
def classify_geographic(row):
    vol = row["volc_json"]
    cfg = VOL_CFG[vol]
    lat, lon = row["pc_lat"], row["pc_lon"]
    pc_dist = row["pc_centroid_dist_km"]
    n_pix = row["pc_n_pixels"]
    t_bg = row["t_bg_k"]
    if lat is None or lon is None:
        if pc_dist is not None and pc_dist <= cfg["inner"] * 0.5:
            return "b"
        return "d"
    d_mirova = haversine_km(lat, lon, cfg["mirova_lat"], cfg["mirova_lon"])
    d_vent = haversine_km(lat, lon, cfg["vent_lat"], cfg["vent_lon"])
    if d_mirova is not None and d_mirova <= cfg["inner"]:
        try:
            if t_bg is not None and float(t_bg) < 260.0:
                return "d"  # cirrus alto frio A23
        except Exception:
            pass
        if vol == "Tupungatito" and d_vent is not None and d_vent > 3.0:
            return "d"  # ring glaciar A19
        if d_vent is not None and d_vent > cfg["inner"] * 0.7 and n_pix <= 3:
            return "d"  # singleton lejos
        return "b"
    return "d"  # fuera del inner


fp_mask = OURS["is_fp"]
OURS.loc[fp_mask, "fp_category"] = OURS[fp_mask].apply(classify_geographic, axis=1)


# ---------------------------------------------------------------------------
# J.1 — Construir huella por volcán desde centroides TP
# ---------------------------------------------------------------------------
def footprint_stats(sub):
    """sub: rows with pc_lat/pc_lon non-null. Returns footprint dict."""
    pts = sub.dropna(subset=["pc_lat", "pc_lon"])
    n = len(pts)
    if n == 0:
        return None
    mean_lat = float(pts["pc_lat"].mean())
    mean_lon = float(pts["pc_lon"].mean())
    # distance of each TP centroid to the footprint centroid (km)
    dists = np.array([haversine_km(la, lo, mean_lat, mean_lon)
                      for la, lo in zip(pts["pc_lat"], pts["pc_lon"])])
    dists = dists[~np.isnan(dists)]
    return {
        "n_tp_with_coords": int(n),
        "mean_lat": round(mean_lat, 5),
        "mean_lon": round(mean_lon, 5),
        "spread_std_km": round(float(np.std(dists)), 3) if len(dists) else None,
        "r50_km": round(float(np.percentile(dists, 50)), 3) if len(dists) else None,
        "r90_km": round(float(np.percentile(dists, 90)), 3) if len(dists) else None,
        "r95_km": round(float(np.percentile(dists, 95)), 3) if len(dists) else None,
        "max_km": round(float(np.max(dists)), 3) if len(dists) else None,
    }


footprints = {}
for vol in TIER_A_NAMES:
    cfg = VOL_CFG[vol]
    tp_sub = OURS[(OURS["volc_json"] == vol) & (OURS["is_tp"])]
    fpr = footprint_stats(tp_sub)
    if fpr is None:
        footprints[vol] = {"n_tp_with_coords": 0, "note": "no TP con coords en ventana"}
        continue
    # distance footprint centroid -> vent / mirova_center
    fpr["d_footprint_to_vent_km"] = round(
        haversine_km(fpr["mean_lat"], fpr["mean_lon"], cfg["vent_lat"], cfg["vent_lon"]), 3)
    fpr["d_footprint_to_mirova_center_km"] = round(
        haversine_km(fpr["mean_lat"], fpr["mean_lon"], cfg["mirova_lat"], cfg["mirova_lon"]), 3)
    fpr["inner_radius_km"] = cfg["inner"]
    # compactness verdict
    r90 = fpr["r90_km"] or 0
    fpr["compactness"] = ("compacta" if r90 <= 2.0 else
                          "intermedia" if r90 <= 5.0 else "extendida/difusa")
    footprints[vol] = fpr

print("[INFO] footprints built")


# ---------------------------------------------------------------------------
# J.2 — Estabilidad temporal (drift del centroide mes a mes)
# ---------------------------------------------------------------------------
def monthly_stability(vol):
    tp = OURS[(OURS["volc_json"] == vol) & (OURS["is_tp"])].dropna(subset=["pc_lat", "pc_lon"]).copy()
    if len(tp) == 0:
        return {"months": [], "max_inter_month_drift_km": None}
    tp["month"] = pd.to_datetime(tp["night_local"]).dt.to_period("M").astype(str)
    months = []
    centroids = []
    for m, g in tp.groupby("month"):
        ml = float(g["pc_lat"].mean()); mo = float(g["pc_lon"].mean())
        months.append({"month": m, "n": int(len(g)),
                       "lat": round(ml, 5), "lon": round(mo, 5)})
        centroids.append((m, ml, mo))
    # max pairwise drift between monthly centroids
    drifts = []
    for i in range(len(centroids)):
        for j in range(i + 1, len(centroids)):
            d = haversine_km(centroids[i][1], centroids[i][2],
                             centroids[j][1], centroids[j][2])
            if d is not None:
                drifts.append(d)
    return {
        "months": months,
        "n_months": len(months),
        "max_inter_month_drift_km": round(max(drifts), 3) if drifts else None,
        "mean_inter_month_drift_km": round(float(np.mean(drifts)), 3) if drifts else None,
    }


stability = {vol: monthly_stability(vol) for vol in TIER_A_NAMES}


# ---------------------------------------------------------------------------
# J.3 — Separación huella vs categorias (% dentro del r95)
# ---------------------------------------------------------------------------
def within_footprint_fraction(vol, mask):
    """% of records (mask) whose centroid is within r95 of the footprint."""
    fpr = footprints.get(vol)
    if not fpr or fpr.get("n_tp_with_coords", 0) == 0 or fpr.get("r95_km") is None:
        return None, 0
    r95 = max(fpr["r95_km"], 0.5)  # floor 0.5km to avoid degenerate r95=0
    sub = OURS[(OURS["volc_json"] == vol) & mask].dropna(subset=["pc_lat", "pc_lon"])
    if len(sub) == 0:
        return None, 0
    inside = 0
    for la, lo in zip(sub["pc_lat"], sub["pc_lon"]):
        d = haversine_km(la, lo, fpr["mean_lat"], fpr["mean_lon"])
        if d is not None and d <= r95:
            inside += 1
    return round(100 * inside / len(sub), 1), len(sub)


separation = {}
for vol in TIER_A_NAMES:
    is_v = OURS["volc_json"] == vol
    tp_pct, tp_n = within_footprint_fraction(vol, is_v & OURS["is_tp"])
    fpb_pct, fpb_n = within_footprint_fraction(vol, is_v & (OURS.get("fp_category") == "b"))
    fpd_pct, fpd_n = within_footprint_fraction(vol, is_v & (OURS.get("fp_category") == "d"))
    separation[vol] = {
        "tp_within_r95_pct": tp_pct, "tp_n": tp_n,
        "fp_b_within_r95_pct": fpb_pct, "fp_b_n": fpb_n,
        "fp_d_within_r95_pct": fpd_pct, "fp_d_n": fpd_n,
    }

# Global aggregate of separation (pooled over all vols using a "within own footprint" flag)
def pooled_within(mask):
    inside = total = 0
    for vol in TIER_A_NAMES:
        fpr = footprints.get(vol)
        if not fpr or fpr.get("r95_km") is None:
            continue
        r95 = max(fpr["r95_km"], 0.5)
        sub = OURS[(OURS["volc_json"] == vol) & mask].dropna(subset=["pc_lat", "pc_lon"])
        for la, lo in zip(sub["pc_lat"], sub["pc_lon"]):
            d = haversine_km(la, lo, fpr["mean_lat"], fpr["mean_lon"])
            if d is None:
                continue
            total += 1
            if d <= r95:
                inside += 1
    return (round(100 * inside / total, 1) if total else None), total


pooled = {
    "tp": pooled_within(OURS["is_tp"]),
    "fp_b": pooled_within(OURS.get("fp_category") == "b"),
    "fp_d": pooled_within(OURS.get("fp_category") == "d"),
}

# Compare: % FP-d inside inner_radius circular (already publishable so all inside inner by definition)
# Key question: footprint r95 is FINER than inner_radius -> does it catch more d?
inner_vs_footprint = {}
for vol in TIER_A_NAMES:
    fpr = footprints.get(vol)
    if not fpr or fpr.get("r95_km") is None:
        continue
    inner_vs_footprint[vol] = {
        "inner_radius_km": fpr["inner_radius_km"],
        "footprint_r95_km": fpr["r95_km"],
        "footprint_finer_by_km": round(fpr["inner_radius_km"] - fpr["r95_km"], 3),
    }


# ---------------------------------------------------------------------------
# J.4 — Casos especiales: detecciones que ganan en VRP pero fuera de huella
# ---------------------------------------------------------------------------
def candidates_outside_footprint(vol, top=15):
    """Publishable records whose centroid is OUTSIDE the footprint r95 but high VRP."""
    fpr = footprints.get(vol)
    if not fpr or fpr.get("r95_km") is None:
        return []
    r95 = max(fpr["r95_km"], 0.5)
    sub = OURS[(OURS["volc_json"] == vol) & OURS["publishable"]].dropna(subset=["pc_lat", "pc_lon"]).copy()
    out = []
    for _, r in sub.iterrows():
        d = haversine_km(r["pc_lat"], r["pc_lon"], fpr["mean_lat"], fpr["mean_lon"])
        if d is not None and d > r95:
            out.append({
                "night": str(r["night_local"]), "sensor": r["sensor_bucket"],
                "pc_vrp_mw": round(r["pc_vrp_mw"], 3),
                "dist_to_footprint_km": round(d, 2),
                "pc_centroid_dist_km": round(r["pc_centroid_dist_km"], 2) if r["pc_centroid_dist_km"] is not None else None,
                "is_tp": bool(r["is_tp"]),
                "fp_category": r.get("fp_category") if not r["is_tp"] else None,
            })
    out.sort(key=lambda x: x["pc_vrp_mw"], reverse=True)
    return out[:top]


special = {}
for vol in ["PuyehueCordonCaulle", "Lascar", "Tupungatito"]:
    special[vol] = {
        "footprint": footprints.get(vol),
        "stability": stability.get(vol),
        "candidates_outside_footprint": candidates_outside_footprint(vol),
    }


# ---------------------------------------------------------------------------
# Save JSON
# ---------------------------------------------------------------------------
result = {
    "window": {"start": str(MIN_N), "end": str(MAX_N)},
    "method_note": (
        "Huella = nube de centroides primary_cluster de NUESTROS records TP "
        "(publishable & MIROVA alerto esa noche-sensor). r95 = radio que contiene "
        "95% de los centroides TP respecto al centroide medio de la huella."
    ),
    "limitations": [
        "JSON solo guarda primary_cluster (criterio vent_anchored S38). No clusters alternativos.",
        "MIROVA CSV sin lat/lon (solo Distancia_km radial; OCR en Nota como dist~XX km).",
        "Loader hereda bugs F-B1/B2 (OCR distancia no consumida, alias). Huella construida con cruce exacto C.",
        "Categorias FP a/b/c/d via heuristica geografica replicada de script_E (no verificacion humana).",
    ],
    "footprints": footprints,
    "temporal_stability": stability,
    "separation_by_category": separation,
    "pooled_within_footprint": pooled,
    "inner_radius_vs_footprint_r95": inner_vs_footprint,
    "special_cases": special,
}
(OUT / "J_canonical_footprint.json").write_text(
    json.dumps(result, indent=2, default=str), encoding="utf-8")
print(f"[OK] wrote {OUT/'J_canonical_footprint.json'}")


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def fp_line(vol):
    f = footprints[vol]
    if f.get("n_tp_with_coords", 0) == 0:
        return f"| {vol} | 0 | — | — | — | — | — | — |"
    return (f"| {vol} | {f['n_tp_with_coords']} | {f['mean_lat']:.4f},{f['mean_lon']:.4f} | "
            f"{f.get('r50_km')} | {f.get('r90_km')} | {f.get('r95_km')} | "
            f"{f.get('d_footprint_to_vent_km')} | {f.get('compactness')} |")


md = []
md.append("# Experimento J S86 — Huella canónica volcánica per-vol")
md.append("")
md.append(f"**Ventana**: {MIN_N} → {MAX_N}.")
md.append(f"**Records publishable**: {int(OURS['publishable'].sum())} | "
          f"**TP**: {int(OURS['is_tp'].sum())} | **FP**: {int(OURS['is_fp'].sum())}.")
md.append("")
md.append("## Lectura física")
md.append("")
md.append("La hipótesis de Nicolás es geológicamente sólida: el calor volcánico "
          "sale de una fuente fija — el cráter activo, el lago cratérico, el "
          "lacolito intruido. Esa fuente no se mueve de una noche a la otra. "
          "Por lo tanto la anomalía térmica real debe agruparse, mes tras mes, "
          "en un mismo punto del terreno. Una detección que aparece lejos de esa "
          "nube — un foco térmico que surge fuera de la huella — es sospechosa: "
          "un incendio de pastizal en verano, un reflejo, una nube fría que el "
          "kernel contextual confunde. La huella canónica formaliza esa intuición: "
          "la construimos con los centroides de los clusters que MIROVA nos "
          "confirmó (TP), porque esos son, por definición, los puntos donde un "
          "operador defendió 'esto es el volcán'.")
md.append("")
md.append("## J.1 — Huella por volcán")
md.append("")
md.append("| Volcán | n TP coords | centroide (lat,lon) | r50 km | r90 km | r95 km | d→vent km | forma |")
md.append("|---|---:|---|---:|---:|---:|---:|---|")
for vol in TIER_A_NAMES:
    md.append(fp_line(vol))
md.append("")
md.append("- **r50/r90/r95**: radio (km) que contiene 50/90/95% de los centroides TP "
          "respecto al centroide medio de la huella. Mide la dispersión espacial.")
md.append("- **forma**: compacta (r90≤2 km, foco puntual), intermedia (2–5 km), "
          "extendida/difusa (>5 km).")
md.append("")
md.append("## J.2 — Estabilidad temporal (drift centroide mes a mes)")
md.append("")
md.append("| Volcán | n meses | drift máx entre meses (km) | drift medio (km) |")
md.append("|---|---:|---:|---:|")
for vol in TIER_A_NAMES:
    s = stability[vol]
    md.append(f"| {vol} | {s.get('n_months', 0)} | "
              f"{s.get('max_inter_month_drift_km', '—')} | "
              f"{s.get('mean_inter_month_drift_km', '—')} |")
md.append("")
md.append("Lectura: si el drift máximo entre meses es pequeño (≤ r95 de la huella), "
          "la huella es **estable durante el año** — confirma la hipótesis de Nicolás. "
          "Drift grande indica o bien fuente migrante (raro) o bien contaminación "
          "del primary por clusters no-volcánicos algunos meses.")
md.append("")
md.append("## J.3 — Separación huella vs categorías (% dentro del r95)")
md.append("")
md.append("| Volcán | TP %∈r95 (n) | FP-b %∈r95 (n) | FP-d %∈r95 (n) |")
md.append("|---|---|---|---|")
for vol in TIER_A_NAMES:
    s = separation[vol]
    md.append(f"| {vol} | {s['tp_within_r95_pct']} ({s['tp_n']}) | "
              f"{s['fp_b_within_r95_pct']} ({s['fp_b_n']}) | "
              f"{s['fp_d_within_r95_pct']} ({s['fp_d_n']}) |")
md.append("")
md.append(f"**Pooled (todos los vols)**: TP {pooled['tp'][0]}% (n={pooled['tp'][1]}), "
          f"FP-b {pooled['fp_b'][0]}% (n={pooled['fp_b'][1]}), "
          f"FP-d {pooled['fp_d'][0]}% (n={pooled['fp_d'][1]}).")
md.append("")
md.append("**Métrica clave**: si TP y FP-b (volcánico real del complejo) caen "
          "mayoritariamente DENTRO del r95, y FP-d (artefacto) caen FUERA, "
          "entonces el gate 'dentro de la huella' separa volcánico de artefacto "
          "mejor que el inner_radius circular.")
md.append("")
md.append("### inner_radius vs huella r95 (¿la huella es más fina?)")
md.append("")
md.append("| Volcán | inner_radius km | huella r95 km | huella más fina por (km) |")
md.append("|---|---:|---:|---:|")
for vol, iv in inner_vs_footprint.items():
    md.append(f"| {vol} | {iv['inner_radius_km']} | {iv['footprint_r95_km']} | {iv['footprint_finer_by_km']} |")
md.append("")
md.append("## J.4 — Casos especiales (PCC lacolito, Lascar cráter, Tupungatito lago)")
md.append("")
for vol in ["PuyehueCordonCaulle", "Lascar", "Tupungatito"]:
    f = footprints[vol]
    md.append(f"### {vol}")
    if f.get("n_tp_with_coords", 0) == 0:
        md.append("Sin TP con coords en la ventana.")
        md.append("")
        continue
    md.append(f"- Huella: centroide ({f['mean_lat']:.4f}, {f['mean_lon']:.4f}), "
              f"r95={f.get('r95_km')} km, forma **{f.get('compactness')}**, "
              f"a {f.get('d_footprint_to_vent_km')} km del vent.")
    cands = special[vol]["candidates_outside_footprint"]
    if cands:
        md.append(f"- **Candidatos a incendio/artefacto** (publishable, centroide "
                  f"fuera del r95, alto VRP): {len(cands)} listados (top por VRP):")
        md.append("")
        md.append("  | noche | sensor | VRP MW | dist a huella km | TP? | cat FP |")
        md.append("  |---|---|---:|---:|---|---|")
        for c in cands[:10]:
            md.append(f"  | {c['night']} | {c['sensor']} | {c['pc_vrp_mw']} | "
                      f"{c['dist_to_footprint_km']} | {c['is_tp']} | {c['fp_category'] or '—'} |")
    else:
        md.append("- Sin detecciones publishable fuera del r95 de la huella.")
    md.append("")

md.append("## Limitaciones")
md.append("")
for lim in result["limitations"]:
    md.append(f"- {lim}")
md.append("")
(OUT / "J_canonical_footprint.md").write_text("\n".join(md), encoding="utf-8")
print(f"[OK] wrote {OUT/'J_canonical_footprint.md'}")
print(f"[SUMMARY] pooled TP∈r95={pooled['tp']}, FP-b∈r95={pooled['fp_b']}, FP-d∈r95={pooled['fp_d']}")
