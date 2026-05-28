"""
Frente 2.A S86 — Subagente D: coherencia espacio-temporal (persistencia).

Hipótesis: MIROVA publica ALERTA solo cuando una anomalía persiste
espacio-temporalmente (mismo cluster ±2 km en ≥2 noches / pasajes / ±3 días).

Esperamos:
  - TPs nuestros muestran persistencia >> FPs nuestros (típicamente singletons).
  - ALERTAs MIROVA forman cadenas largas (no singletons aislados).
  - Un gate de persistencia eleva precisión sin matar recall.

Genera D_temporal_coherence.{json,md}.
"""
from __future__ import annotations

import json
import sys
import io
import math
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
CHILE_TZ = ZoneInfo("America/Santiago")

CLUSTER_RADIUS_KM = 2.0
WINDOW_DAYS_3 = 3
WINDOW_DAYS_7 = 7

TIER_A_MAP = {
    "Chaiten":               "Chaiten",
    "Copahue":               "Copahue",
    "Isluga":                "Isluga",
    "Lascar":                "Lascar",
    "Lastarria":             "Lastarria",
    "Llaima":                "Llaima",
    "Nevados de Chillan":    "NevadosDeChillan",
    "PlanchonPeteroa":       "PlanchonPeteroa",
    "Peteroa":               "PlanchonPeteroa",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Tupungatito":           "Tupungatito",
    "Villarrica":            "Villarrica",
}
SENSORS = ["MODIS", "VIIRS375", "VIIRS750"]


def csv_sensor_bucket(s: str) -> str | None:
    if s == "MODIS": return "MODIS"
    if s in ("VIIRS", "VIIRS375"): return "VIIRS375"
    if s == "VIIRS750": return "VIIRS750"
    return None


def json_sensor_bucket(s: str) -> str | None:
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


VOLC_YAML = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
INNER_RADIUS = {v["name"]: float(v.get("inner_radius_km", 5.0))
                for v in VOLC_YAML["volcanoes"] if v.get("mirova_monitored")}
TIER_A_NAMES = sorted(set(TIER_A_MAP.values()))


# ----- Load MIROVA -----
def load_mirova():
    cons = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ocr = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
    cons["source"] = "CONS"; ocr["source"] = "OCR"
    cols = ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW",
            "Distancia_km", "Tipo_Registro", "source"]
    # OCR may have Lat/Lon columns? try to bring them
    extras = []
    for c in ("Latitud", "Longitud"):
        if c in cons.columns or c in ocr.columns:
            extras.append(c)
    use = cols + extras
    cdf = cons[[c for c in use if c in cons.columns]].copy()
    odf = ocr[[c for c in use if c in ocr.columns]].copy()
    for c in extras:
        if c not in cdf.columns: cdf[c] = np.nan
        if c not in odf.columns: odf[c] = np.nan
    df = pd.concat([cdf, odf], ignore_index=True)
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
print(f"[INFO] MIROVA: {len(MIROVA)} rows | ALERTAs: {MIROVA['is_alerta'].sum()}")


# ----- Load our records -----
def load_ours():
    rows = []
    for json_name in TIER_A_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{json_name}.json"
        if not fp.exists(): continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        inner = INNER_RADIUS.get(json_name, 5.0)
        for r in data.get("records", []):
            sensor = r.get("sensor", "")
            bucket = json_sensor_bucket(sensor)
            if bucket is None: continue
            dt_str = r.get("datetime_utc") or r.get("acquisition_time_utc")
            if not dt_str: continue
            try:
                dt_utc = pd.to_datetime(dt_str, utc=True)
            except Exception:
                continue
            night = dt_utc.tz_convert(CHILE_TZ).date()
            pc = r.get("primary_cluster") or {}
            pc_vrp = float(pc.get("vrp_mw") or 0.0)
            pc_n = int(pc.get("n_pixels") or 0)
            pc_dist = pc.get("centroid_dist_km")
            pc_dist = float(pc_dist) if pc_dist is not None else None
            pc_lat = pc.get("centroid_lat")
            pc_lon = pc.get("centroid_lon")
            pc_lat = float(pc_lat) if pc_lat is not None else None
            pc_lon = float(pc_lon) if pc_lon is not None else None
            dist_class = r.get("distance_class", "")
            publishable = (pc_vrp > 0 and pc_dist is not None
                           and pc_dist <= inner and dist_class == "summit")
            n_bt = int(r.get("diag_n_bt_path") or 0)
            n_nti = int(r.get("diag_n_nti_path") or 0)
            n_dnti = int(r.get("diag_n_dnti_ctx_path") or 0)
            paths = []
            if n_bt: paths.append("A")
            if n_nti: paths.append("B/C")
            if n_dnti: paths.append("D")
            path_str = "+".join(paths) if paths else "none"

            rows.append({
                "volc_json": json_name,
                "sensor_bucket": bucket,
                "dt_utc": dt_utc,
                "night_local": night,
                "pc_vrp_mw": pc_vrp,
                "pc_n_pixels": pc_n,
                "pc_centroid_dist_km": pc_dist,
                "pc_centroid_lat": pc_lat,
                "pc_centroid_lon": pc_lon,
                "pc_path": path_str,
                "publishable": publishable,
                "t_bg_k": r.get("t_bg_k"),
                "inner_radius_km": inner,
            })
    return pd.DataFrame(rows)


OURS = load_ours()
print(f"[INFO] OURS: {len(OURS)} rows | publishable: {OURS['publishable'].sum()}")


# ----- Common window -----
MIN_NIGHT = max(MIROVA["night_local"].min(), OURS["night_local"].min())
MAX_NIGHT = min(MIROVA["night_local"].max(), OURS["night_local"].max())
print(f"[INFO] Common window: {MIN_NIGHT} -> {MAX_NIGHT}")
MIROVA = MIROVA[(MIROVA["night_local"] >= MIN_NIGHT) & (MIROVA["night_local"] <= MAX_NIGHT)].copy()
OURS = OURS[(OURS["night_local"] >= MIN_NIGHT) & (OURS["night_local"] <= MAX_NIGHT)].copy()


# ----- Build TP/FP classification via key crossing -----
mirova_alerta_keys = set(
    (r.volc_json, r.sensor_bucket, r.night_local)
    for r in MIROVA[MIROVA["is_alerta"]].itertuples()
)

# Publishable records (one row per record; key may have multiple records same night)
PUB = OURS[OURS["publishable"]].copy()
PUB["key"] = list(zip(PUB["volc_json"], PUB["sensor_bucket"], PUB["night_local"]))
PUB["is_tp"] = PUB["key"].isin(mirova_alerta_keys)

n_tp_rec = int(PUB["is_tp"].sum())
n_fp_rec = int((~PUB["is_tp"]).sum())
print(f"[INFO] Publishable records: {len(PUB)} | TP records: {n_tp_rec} | FP records: {n_fp_rec}")


# ----- Spatial clustering (per volcano, simple greedy by centroid proximity) -----
# For each publishable record we assign a cluster_id based on lat/lon ≤2km of any prior cluster centroid in same volcano.
def assign_clusters(df, radius_km=CLUSTER_RADIUS_KM):
    """Greedy per-volcano clustering. Returns df with 'cluster_id'."""
    df = df.copy().reset_index(drop=True)
    df["cluster_id"] = pd.Series([None] * len(df), dtype="object")
    for vol, gidx in df.groupby("volc_json").groups.items():
        sub = df.loc[gidx]
        centroids = []  # list of (lat, lon, cid)
        next_cid = 0
        for idx in sub.index:
            lat = df.at[idx, "pc_centroid_lat"]
            lon = df.at[idx, "pc_centroid_lon"]
            if lat is None or lon is None or (isinstance(lat,float) and math.isnan(lat)):
                # singleton no-coord
                df.at[idx, "cluster_id"] = f"{vol}_NA_{idx}"
                continue
            best_cid = None
            for clat, clon, cid in centroids:
                if haversine_km(lat, lon, clat, clon) <= radius_km:
                    best_cid = cid
                    break
            if best_cid is None:
                cid = f"{vol}_{next_cid}"
                centroids.append((lat, lon, cid))
                next_cid += 1
                df.at[idx, "cluster_id"] = cid
            else:
                df.at[idx, "cluster_id"] = best_cid
    return df


PUB = assign_clusters(PUB)
print(f"[INFO] Spatial clusters found: {PUB['cluster_id'].nunique()}")


# ----- Compute persistence metrics per record -----
PUB["night_dt"] = pd.to_datetime(PUB["night_local"])

def persistence_metrics(df):
    """For each row, compute:
      - n_records_same_cluster_within_3d (any sensor, any time within ±3 days incl self? we exclude self)
      - n_records_same_cluster_within_7d
      - n_consecutive_nights_same_cluster (max chain that includes this record's night)
      - is_singleton_cluster (cluster has only this 1 record in ±7d)
    """
    df = df.copy().reset_index(drop=True)
    metrics = {"n_same_3d": [], "n_same_7d": [], "n_consec_nights": [], "is_singleton_7d": []}
    # Group by cluster
    by_cluster = df.groupby("cluster_id").groups
    nights_by_cluster = {cid: sorted(df.loc[idxs, "night_dt"].unique())
                         for cid, idxs in by_cluster.items()}
    for i, row in df.iterrows():
        cid = row["cluster_id"]
        nights = nights_by_cluster[cid]
        my_night = row["night_dt"]
        # records in same cluster within ±3d / 7d (exclude self-record but include same-night other records)
        cluster_rows = df.loc[by_cluster[cid]]
        # exclude self by index
        other = cluster_rows.drop(index=i, errors="ignore")
        delta = (other["night_dt"] - my_night).dt.days.abs()
        n3 = int((delta <= WINDOW_DAYS_3).sum())
        n7 = int((delta <= WINDOW_DAYS_7).sum())
        # consecutive nights chain containing my_night
        unique_nights_sorted = sorted(set(cluster_rows["night_dt"]))
        # find chain containing my_night with gap<=1 day
        chain = [my_night]
        # extend backward
        cur = my_night
        while True:
            prev = cur - pd.Timedelta(days=1)
            if prev in unique_nights_sorted:
                chain.insert(0, prev); cur = prev
            else:
                break
        cur = my_night
        while True:
            nxt = cur + pd.Timedelta(days=1)
            if nxt in unique_nights_sorted:
                chain.append(nxt); cur = nxt
            else:
                break
        n_consec = len(chain)
        is_singleton = (n7 == 0)
        metrics["n_same_3d"].append(n3)
        metrics["n_same_7d"].append(n7)
        metrics["n_consec_nights"].append(n_consec)
        metrics["is_singleton_7d"].append(is_singleton)
    for k, v in metrics.items():
        df[k] = v
    return df


PUB = persistence_metrics(PUB)


# ----- Analysis 1: distributions TP vs FP -----
def dstats(s):
    s = pd.Series(s).dropna()
    if len(s) == 0: return {"n": 0}
    return {
        "n": int(len(s)),
        "mean": float(s.mean()), "median": float(s.median()),
        "p25": float(s.quantile(0.25)), "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "min": float(s.min()), "max": float(s.max()),
    }


TP_DF = PUB[PUB["is_tp"]].copy()
FP_DF = PUB[~PUB["is_tp"]].copy()

analysis1 = {
    "TP": {
        "n_same_3d": dstats(TP_DF["n_same_3d"]),
        "n_same_7d": dstats(TP_DF["n_same_7d"]),
        "n_consec_nights": dstats(TP_DF["n_consec_nights"]),
        "frac_singleton_7d": float(TP_DF["is_singleton_7d"].mean()) if len(TP_DF) else None,
        "frac_consec_ge_2": float((TP_DF["n_consec_nights"] >= 2).mean()) if len(TP_DF) else None,
        "frac_consec_ge_3": float((TP_DF["n_consec_nights"] >= 3).mean()) if len(TP_DF) else None,
    },
    "FP": {
        "n_same_3d": dstats(FP_DF["n_same_3d"]),
        "n_same_7d": dstats(FP_DF["n_same_7d"]),
        "n_consec_nights": dstats(FP_DF["n_consec_nights"]),
        "frac_singleton_7d": float(FP_DF["is_singleton_7d"].mean()) if len(FP_DF) else None,
        "frac_consec_ge_2": float((FP_DF["n_consec_nights"] >= 2).mean()) if len(FP_DF) else None,
        "frac_consec_ge_3": float((FP_DF["n_consec_nights"] >= 3).mean()) if len(FP_DF) else None,
    },
}


# ----- Analysis 2: MIROVA ALERTA persistence -----
MIR_AL = MIROVA[MIROVA["is_alerta"]].copy()
# Simple clustering using Distancia_km grouping is unreliable; use volcano-level (assume MIROVA ALERTAs of same vol+sensor are same physical event when near in time)
# We approximate by collapsing by (volc, night) — same vol+night = same cluster context
MIR_AL["night_dt"] = pd.to_datetime(MIR_AL["night_local"])

def mirova_persistence(df):
    df = df.copy().reset_index(drop=True)
    metrics = {"n_same_3d": [], "n_consec_nights": [], "is_singleton_7d": []}
    by_vol = df.groupby("volc_json").groups
    nights_by_vol = {v: sorted(set(df.loc[idxs, "night_dt"])) for v, idxs in by_vol.items()}
    for i, row in df.iterrows():
        v = row["volc_json"]
        nights_set = set(nights_by_vol[v])
        my_night = row["night_dt"]
        # count nights with ANY alert in vol within ±3d (excluding own night counted once)
        delta_days = [abs((n - my_night).days) for n in nights_set if n != my_night]
        n3 = sum(1 for d in delta_days if d <= WINDOW_DAYS_3)
        n7 = sum(1 for d in delta_days if d <= WINDOW_DAYS_7)
        # consec chain
        chain = [my_night]
        cur = my_night
        while (cur - pd.Timedelta(days=1)) in nights_set:
            cur = cur - pd.Timedelta(days=1); chain.insert(0, cur)
        cur = my_night
        while (cur + pd.Timedelta(days=1)) in nights_set:
            cur = cur + pd.Timedelta(days=1); chain.append(cur)
        metrics["n_same_3d"].append(n3)
        metrics["n_consec_nights"].append(len(chain))
        metrics["is_singleton_7d"].append(n7 == 0)
    for k, vlist in metrics.items():
        df[k] = vlist
    return df


MIR_AL = mirova_persistence(MIR_AL)
analysis2 = {
    "n_alertas": int(len(MIR_AL)),
    "n_same_3d": dstats(MIR_AL["n_same_3d"]),
    "n_consec_nights": dstats(MIR_AL["n_consec_nights"]),
    "frac_singleton_7d": float(MIR_AL["is_singleton_7d"].mean()) if len(MIR_AL) else None,
    "frac_consec_ge_2": float((MIR_AL["n_consec_nights"] >= 2).mean()) if len(MIR_AL) else None,
}


# ----- Analysis 3: Candidate gates -----
def gate_eval(name, tp_mask, fp_mask):
    tpp = int(tp_mask.sum()); tpt = len(tp_mask)
    fpp = int(fp_mask.sum()); fpt = len(fp_mask)
    rec_kept = tpp / tpt if tpt else None
    fp_filt = (fpt - fpp) / fpt if fpt else None
    prec_after = tpp / (tpp + fpp) if (tpp + fpp) else None
    return {
        "gate": name,
        "tp_pass": tpp, "tp_total": tpt,
        "fp_pass": fpp, "fp_total": fpt,
        "recall_kept_pct": round(100*rec_kept, 1) if rec_kept is not None else None,
        "fp_filtered_pct": round(100*fp_filt, 1) if fp_filt is not None else None,
        "precision_before": round(tpt / (tpt + fpt), 3) if (tpt + fpt) else None,
        "precision_after": round(prec_after, 3) if prec_after is not None else None,
    }


gates = []
gates.append(gate_eval("P1: n_same_cluster_within_3d >= 1",
                       TP_DF["n_same_3d"] >= 1, FP_DF["n_same_3d"] >= 1))
gates.append(gate_eval("P1b: n_same_cluster_within_3d >= 2",
                       TP_DF["n_same_3d"] >= 2, FP_DF["n_same_3d"] >= 2))
gates.append(gate_eval("P2: n_consecutive_nights >= 2",
                       TP_DF["n_consec_nights"] >= 2, FP_DF["n_consec_nights"] >= 2))
gates.append(gate_eval("P3: NOT singleton (cluster has >=2 records in ±7d)",
                       ~TP_DF["is_singleton_7d"], ~FP_DF["is_singleton_7d"]))
gates.append(gate_eval("P4: n_same_cluster_within_3d >= 3",
                       TP_DF["n_same_3d"] >= 3, FP_DF["n_same_3d"] >= 3))

# Combined gates with G1 (already validated): sensor != VIIRS750
G1_TP = TP_DF["sensor_bucket"] != "VIIRS750"
G1_FP = FP_DF["sensor_bucket"] != "VIIRS750"
gates.append(gate_eval("G1 (sensor != VIIRS750) — baseline",
                       G1_TP, G1_FP))
gates.append(gate_eval("G1 AND P1 (sensor!=VIIRS750 AND n_same_3d>=1)",
                       G1_TP & (TP_DF["n_same_3d"] >= 1),
                       G1_FP & (FP_DF["n_same_3d"] >= 1)))
gates.append(gate_eval("G1 AND P2 (sensor!=VIIRS750 AND consec>=2)",
                       G1_TP & (TP_DF["n_consec_nights"] >= 2),
                       G1_FP & (FP_DF["n_consec_nights"] >= 2)))
gates.append(gate_eval("G1 AND P3 (sensor!=VIIRS750 AND NOT singleton)",
                       G1_TP & ~TP_DF["is_singleton_7d"],
                       G1_FP & ~FP_DF["is_singleton_7d"]))
gates.append(gate_eval("G1 AND (P1 OR vrp>=50 MW)  -- preserva picos magnitud",
                       G1_TP & ((TP_DF["n_same_3d"] >= 1) | (TP_DF["pc_vrp_mw"] >= 50)),
                       G1_FP & ((FP_DF["n_same_3d"] >= 1) | (FP_DF["pc_vrp_mw"] >= 50))))


# ----- Analysis 4: Lascar 17/02 sanity -----
lascar_target = TP_DF[
    (TP_DF["volc_json"] == "Lascar")
    & (TP_DF["pc_vrp_mw"] >= 100)
    & (TP_DF["night_dt"] >= pd.Timestamp("2026-02-15"))
    & (TP_DF["night_dt"] <= pd.Timestamp("2026-02-20"))
].copy()

lascar_sanity = {"records_found": int(len(lascar_target)), "records": []}
for _, r in lascar_target.iterrows():
    lascar_sanity["records"].append({
        "night": str(r["night_local"]),
        "sensor": r["sensor_bucket"],
        "pc_vrp_mw": float(r["pc_vrp_mw"]),
        "pc_n_pixels": int(r["pc_n_pixels"]),
        "cluster_id": str(r["cluster_id"]),
        "n_same_3d": int(r["n_same_3d"]),
        "n_consec_nights": int(r["n_consec_nights"]),
        "is_singleton_7d": bool(r["is_singleton_7d"]),
        "passes_P1": bool(r["n_same_3d"] >= 1),
        "passes_P2": bool(r["n_consec_nights"] >= 2),
    })
# MIROVA Lascar episode
mir_lascar_feb = MIR_AL[
    (MIR_AL["volc_json"] == "Lascar")
    & (MIR_AL["night_dt"] >= pd.Timestamp("2026-02-15"))
    & (MIR_AL["night_dt"] <= pd.Timestamp("2026-02-20"))
]
lascar_sanity["mirova_alertas_feb15_20"] = int(len(mir_lascar_feb))
lascar_sanity["mirova_nights"] = sorted(set(str(n.date()) for n in mir_lascar_feb["night_dt"]))


# ----- Analysis 5: Villarrica sub-pixel lava lake -----
vill_tp = TP_DF[TP_DF["volc_json"] == "Villarrica"]
vill_summary = {
    "n_tp_records": int(len(vill_tp)),
    "frac_n_pixels_eq_1": float((vill_tp["pc_n_pixels"] == 1).mean()) if len(vill_tp) else None,
    "frac_consec_ge_2": float((vill_tp["n_consec_nights"] >= 2).mean()) if len(vill_tp) else None,
    "frac_singleton_7d": float(vill_tp["is_singleton_7d"].mean()) if len(vill_tp) else None,
    "n_consec_nights_dist": dstats(vill_tp["n_consec_nights"]),
    "n_same_3d_dist": dstats(vill_tp["n_same_3d"]),
    "clusters_used": int(vill_tp["cluster_id"].nunique()),
}


# ----- Persistence by volcano (TP only) — régimen check -----
per_vol_tp = {}
for vol in TIER_A_NAMES:
    sub = TP_DF[TP_DF["volc_json"] == vol]
    if len(sub) == 0:
        per_vol_tp[vol] = {"n_tp": 0}
        continue
    per_vol_tp[vol] = {
        "n_tp": int(len(sub)),
        "frac_consec_ge_2": float((sub["n_consec_nights"] >= 2).mean()),
        "frac_singleton_7d": float(sub["is_singleton_7d"].mean()),
        "median_consec": float(sub["n_consec_nights"].median()),
    }


# ----- Save JSON -----
result = {
    "window": {"start": str(MIN_NIGHT), "end": str(MAX_NIGHT)},
    "params": {
        "cluster_radius_km": CLUSTER_RADIUS_KM,
        "window_days_3": WINDOW_DAYS_3,
        "window_days_7": WINDOW_DAYS_7,
    },
    "n_publishable_records": int(len(PUB)),
    "n_tp_records": n_tp_rec,
    "n_fp_records": n_fp_rec,
    "n_spatial_clusters": int(PUB["cluster_id"].nunique()),
    "analysis1_ours_TP_vs_FP_persistence": analysis1,
    "analysis2_mirova_alerta_persistence": analysis2,
    "analysis3_candidate_gates": gates,
    "analysis4_lascar_2026_02_17_sanity": lascar_sanity,
    "analysis5_villarrica_sub_pixel": vill_summary,
    "analysis6_per_volcano_TP_persistence": per_vol_tp,
}

out_json = OUT / "D_temporal_coherence.json"
out_json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
print(f"[OK] Wrote {out_json}")


# ----- Build markdown -----
def fmt_num(x, n=3):
    if x is None: return "—"
    try: return f"{x:.{n}f}"
    except Exception: return str(x)


def fmt_pct(x):
    return f"{100*x:.1f}%" if x is not None else "—"


def fmt_dist(d):
    if not d or d.get("n", 0) == 0: return "—"
    return (f"n={d['n']}, median={d['median']:.2f}, p25={d['p25']:.2f}, "
            f"p75={d['p75']:.2f}, p95={d['p95']:.2f}, max={d['max']:.1f}")


lines = []
lines.append("# Frente 2.A S86 — Coherencia espacio-temporal (Subagente D)")
lines.append("")
lines.append(f"**Ventana**: {MIN_NIGHT} → {MAX_NIGHT}.")
lines.append(f"**Publishables**: {len(PUB):,} ({n_tp_rec} TP, {n_fp_rec} FP). "
             f"**Clusters espaciales** (≤{CLUSTER_RADIUS_KM} km): {PUB['cluster_id'].nunique()}.")
lines.append("")
lines.append("## Lectura geológica")
lines.append("")
lines.append("Un cuerpo magmático caliente (lava lake, domo activo, intrusión somera) "
             "irradia calor durante horas a días. El pixel hot reaparece **pasaje tras pasaje** "
             "en el mismo lugar del cráter. Un FP por **cirrus alto frío** (T_bg<260K), por "
             "**ruido instrumental aislado** o por **una fumarola transitoria** es de naturaleza opuesta: "
             "aparece en un solo pasaje y desaparece. Si MIROVA aplica un gate de **coherencia "
             "espacio-temporal** (mismo cluster ±2 km en ≥2 noches / pasajes), filtra justamente los "
             "transitorios que producen el grueso de nuestros FPs.")
lines.append("")

# --- Hallazgo central ---
a1 = analysis1
verdict = "CONFIRMADA" if (a1["TP"]["frac_consec_ge_2"] or 0) > (a1["FP"]["frac_consec_ge_2"] or 0) + 0.10 else "PARCIAL"
lines.append(f"## Hallazgo central: hipótesis **{verdict}**")
lines.append("")
lines.append(f"- **TPs nuestros — % con ≥2 noches consecutivas en mismo cluster**: {fmt_pct(a1['TP']['frac_consec_ge_2'])}")
lines.append(f"- **FPs nuestros — % con ≥2 noches consecutivas en mismo cluster**: {fmt_pct(a1['FP']['frac_consec_ge_2'])}")
lines.append(f"- **TPs nuestros — % singletons (cluster aislado en ±7d)**: {fmt_pct(a1['TP']['frac_singleton_7d'])}")
lines.append(f"- **FPs nuestros — % singletons (cluster aislado en ±7d)**: {fmt_pct(a1['FP']['frac_singleton_7d'])}")
lines.append("")
lines.append(f"- **MIROVA ALERTAs — % con ≥2 noches consecutivas (mismo vol)**: {fmt_pct(analysis2['frac_consec_ge_2'])}")
lines.append(f"- **MIROVA ALERTAs — % singletons aislados ±7d**: {fmt_pct(analysis2['frac_singleton_7d'])}")
lines.append("")

# --- Analysis 1 distrib ---
lines.append("## 1. Distribuciones persistencia (TPs vs FPs nuestros)")
lines.append("")
lines.append("| Métrica | TP | FP |")
lines.append("|---|---|---|")
lines.append(f"| n_records_same_cluster_within_3d | {fmt_dist(a1['TP']['n_same_3d'])} | {fmt_dist(a1['FP']['n_same_3d'])} |")
lines.append(f"| n_records_same_cluster_within_7d | {fmt_dist(a1['TP']['n_same_7d'])} | {fmt_dist(a1['FP']['n_same_7d'])} |")
lines.append(f"| n_consecutive_nights_same_cluster | {fmt_dist(a1['TP']['n_consec_nights'])} | {fmt_dist(a1['FP']['n_consec_nights'])} |")
lines.append(f"| %singleton (aislado en ±7d) | {fmt_pct(a1['TP']['frac_singleton_7d'])} | {fmt_pct(a1['FP']['frac_singleton_7d'])} |")
lines.append(f"| %consecutivos ≥2 noches | {fmt_pct(a1['TP']['frac_consec_ge_2'])} | {fmt_pct(a1['FP']['frac_consec_ge_2'])} |")
lines.append(f"| %consecutivos ≥3 noches | {fmt_pct(a1['TP']['frac_consec_ge_3'])} | {fmt_pct(a1['FP']['frac_consec_ge_3'])} |")
lines.append("")

# --- Analysis 2 ---
lines.append("## 2. Persistencia MIROVA ALERTAs (¿MIROVA respeta su propio gate?)")
lines.append("")
lines.append(f"- N ALERTAs en ventana: {analysis2['n_alertas']}")
lines.append(f"- n_same_3d: {fmt_dist(analysis2['n_same_3d'])}")
lines.append(f"- n_consec_nights: {fmt_dist(analysis2['n_consec_nights'])}")
lines.append(f"- %consec ≥2: {fmt_pct(analysis2['frac_consec_ge_2'])} | %singleton ±7d: {fmt_pct(analysis2['frac_singleton_7d'])}")
lines.append("")

# --- Analysis 3 gates ---
lines.append("## 3. Gates de persistencia evaluados")
lines.append("")
lines.append("| # | Gate | Recall mantiene | FP filtra | Precisión antes | Precisión después |")
lines.append("|---|---|---|---|---|---|")
for i, g in enumerate(gates, 1):
    lines.append(f"| {i} | `{g['gate']}` | {g['recall_kept_pct']}% | {g['fp_filtered_pct']}% | {g['precision_before']} | {g['precision_after']} |")
lines.append("")

# --- Analysis 4 Lascar ---
lines.append("## 4. Sanity check — Lascar 17/02 (evento eruptivo confirmado)")
lines.append("")
lines.append(f"- Registros TP Lascar 15-20/feb con pc_vrp_mw≥100 MW: {lascar_sanity['records_found']}")
lines.append(f"- MIROVA ALERTAs Lascar 15-20/feb: {lascar_sanity['mirova_alertas_feb15_20']} noches → {lascar_sanity['mirova_nights']}")
for r in lascar_sanity["records"]:
    lines.append(f"  - {r['night']} {r['sensor']}: vrp={r['pc_vrp_mw']:.1f} MW, n_pix={r['pc_n_pixels']}, "
                 f"n_same_3d={r['n_same_3d']}, consec_nights={r['n_consec_nights']}, "
                 f"P1✓={r['passes_P1']}, P2✓={r['passes_P2']}")
lines.append("")

# --- Analysis 5 Villarrica ---
lines.append("## 5. Villarrica lava lake sub-pixel (TP débil histórico)")
lines.append("")
lines.append(f"- N TPs Villarrica en ventana: {vill_summary['n_tp_records']}")
lines.append(f"- %singleton pixel (n=1): {fmt_pct(vill_summary['frac_n_pixels_eq_1'])}")
lines.append(f"- %≥2 noches consecutivas: {fmt_pct(vill_summary['frac_consec_ge_2'])}")
lines.append(f"- %singleton temporal (cluster aislado ±7d): {fmt_pct(vill_summary['frac_singleton_7d'])}")
lines.append(f"- Distribución n_consec_nights: {fmt_dist(vill_summary['n_consec_nights_dist'])}")
lines.append(f"- Clusters espaciales distintos usados: {vill_summary['clusters_used']}")
lines.append("")
if vill_summary["frac_consec_ge_2"] and vill_summary["frac_consec_ge_2"] >= 0.7:
    lines.append("**Lectura**: el lava lake Villarrica es cuasi-continuo en nuestros TPs → un gate "
                 "de persistencia lo preserva sin OR clause de magnitud.")
else:
    lines.append("**Lectura**: Villarrica intermitente → un gate de persistencia estricto pierde TPs "
                 "débiles. Requiere OR clause (vrp_mw ≥ X o n_same_3d ≥ 1 cuenta como persistente).")
lines.append("")

# --- Analysis 6 per vol ---
lines.append("## 6. Persistencia TP por volcán (régimen-check)")
lines.append("")
lines.append("| Volcán | n_TP | %consec≥2 | %singleton | mediana_consec |")
lines.append("|---|---|---|---|---|")
for vol, m in per_vol_tp.items():
    if m["n_tp"] == 0: continue
    lines.append(f"| {vol} | {m['n_tp']} | {fmt_pct(m['frac_consec_ge_2'])} | "
                 f"{fmt_pct(m['frac_singleton_7d'])} | {fmt_num(m['median_consec'], 1)} |")
lines.append("")

# --- Recomendación operacional ---
# Pick best gate by precision uplift maintaining recall>=80
best = max(
    [g for g in gates if (g["recall_kept_pct"] or 0) >= 80],
    key=lambda g: g["precision_after"] or 0,
    default=None,
)
lines.append("## 7. Recomendación operacional para Frente 1.A S87")
lines.append("")
if best:
    lines.append(f"**Gate recomendado**: `{best['gate']}`")
    lines.append(f"- Recall TP mantiene: {best['recall_kept_pct']}%")
    lines.append(f"- FP filtra: {best['fp_filtered_pct']}%")
    lines.append(f"- Precisión: {best['precision_before']} → {best['precision_after']}")
    lines.append("")
else:
    lines.append("Ningún gate de persistencia mantiene recall≥80%. Recomiendo no adoptar gate de persistencia puro; combinar con magnitud o tamaño cluster.")
    lines.append("")

lines.append("**Implementación sugerida** (campo derivado `pc.mirova_publishable_v2`):")
lines.append("")
lines.append("```python")
lines.append("def is_publishable_v2(record, history_same_vol):")
lines.append("    # G1 baseline ya adoptado")
lines.append("    if record.sensor.endswith('_750'): return False")
lines.append("    if not in_inner_radius(record): return False")
lines.append("    if record.pc.vrp_mw <= 0: return False")
lines.append("    # G_persistencia: pasaje previo o posterior en mismo cluster ±2 km, ±3 días")
lines.append("    cluster_key = (record.volc, round_to(record.pc.centroid_lat,3), round_to(record.pc.centroid_lon,3))")
lines.append("    n_neighbors = count_records_within(history_same_vol, cluster_key, days=3, radius_km=2.0)")
lines.append("    if n_neighbors >= 1: return True")
lines.append("    # OR clause: magnitud alta (preserva eventos eruptivos puntuales tipo Lascar)")
lines.append("    if record.pc.vrp_mw >= 50.0: return True")
lines.append("    return False")
lines.append("```")
lines.append("")
lines.append("**Caveat operacional NRT**: el gate requiere ventana temporal ±3 días. Para el record más")
lines.append("reciente solo hay historial pasado (no futuro). Opciones:")
lines.append("1. **Quórum atrasado**: marcar como `mirova_publishable=True` solo cuando hay confirmación")
lines.append("   con pasaje posterior (latencia ~24h adicional vs MIROVA).")
lines.append("2. **Look-back puro**: contar solo registros en ventana [-3d, 0]. Pierde recall en primer")
lines.append("   pasaje de un evento nuevo pero no añade latencia.")
lines.append("3. **Dual flag**: publicar inmediato como `provisional=True` + reclasificar a `confirmed=True`")
lines.append("   cuando llegue el siguiente pasaje. Frontend muestra ambos.")
lines.append("")

lines.append("## 8. Paths a outputs")
lines.append("")
lines.append("- JSON: `experiments/_s86_f_precision_gap/D_temporal_coherence.json`")
lines.append("- MD: `experiments/_s86_f_precision_gap/D_temporal_coherence.md`")
lines.append("- Script: `experiments/_s86_f_precision_gap/script_D.py`")
lines.append("")

(OUT / "D_temporal_coherence.md").write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] Wrote {OUT/'D_temporal_coherence.md'}")
print()
print(f"[SUMMARY] n_pub={len(PUB)} TP={n_tp_rec} FP={n_fp_rec} clusters={PUB['cluster_id'].nunique()}")
print(f"  TP frac_consec_ge_2={a1['TP']['frac_consec_ge_2']:.3f} singleton={a1['TP']['frac_singleton_7d']:.3f}")
print(f"  FP frac_consec_ge_2={a1['FP']['frac_consec_ge_2']:.3f} singleton={a1['FP']['frac_singleton_7d']:.3f}")
print(f"  Best gate: {best['gate'] if best else 'NONE'}")
