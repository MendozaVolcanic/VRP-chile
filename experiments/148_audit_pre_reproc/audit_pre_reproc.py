"""S77 Audit pre-reproc — ours vs MIROVA NRT.

READ-ONLY. No reproc executed. Produces:
- master_table.csv  : 11 Tier A x 3 sensor buckets x 4 windows
- anomalies.csv     : top anomalous records (vrp>100MW, vrptir_aveni>100MW, cluster_rescue, discards)
- gaps.csv          : MIROVA alerts (non-NULO) without ours match +/-60 min last 90d
- summary.json      : run metadata + counts

Match rule: same volcano, same sensor bucket, |delta_t| <= 60 min.
ours VRP for match: mimics frontend `mirovaEqVrp` -> use vrp_mw filtered by
distance_class=='summit' OR final_hotspot_dist_km <= inner_radius_km.
"""
from __future__ import annotations
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "148_audit_pre_reproc"
OUT.mkdir(parents=True, exist_ok=True)

# --- Tier A list + inner_radius ---
with open(ROOT / "volcanoes.yaml", "r", encoding="utf-8") as f:
    YML = yaml.safe_load(f)

TIER_A = []
INNER = {}
DISPLAY = {}
for v in YML["volcanoes"]:
    if v.get("mirova_monitored"):
        TIER_A.append(v["name"])
        INNER[v["name"]] = float(v.get("inner_radius_km") or 5.0)
        DISPLAY[v["name"]] = v.get("display_name", v["name"])

# Map MIROVA CSV volcan strings -> our canonical names
CSV2OURS = {
    "Tupungatito": "Tupungatito",
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Isluga": "Isluga",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Peteroa": "PlanchonPeteroa",
    "Chaiten": "Chaiten",
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Nevados de Chillan": "NevadosDeChillan",
    "Villarrica": "Villarrica",
    "Llaima": "Llaima",
    "Copahue": "Copahue",
}

# --- Load MIROVA CSV ---
csv_path = ROOT / "latest_consolidado.csv"
mir = pd.read_csv(csv_path)
mir["dt_utc"] = pd.to_datetime(mir["Fecha_Satelite_UTC"], utc=True, errors="coerce")
mir = mir.dropna(subset=["dt_utc"]).copy()
mir["volcano_ours"] = mir["Volcan"].map(CSV2OURS)
mir = mir[mir["volcano_ours"].isin(TIER_A)].copy()
mir["VRP_MW"] = pd.to_numeric(mir["VRP_MW"], errors="coerce").fillna(0.0)
mir["sensor_bucket"] = mir["Sensor"]  # MODIS / VIIRS / VIIRS375

print(f"[mir] {len(mir)} rows after Tier A filter, "
      f"{mir['dt_utc'].min()} -> {mir['dt_utc'].max()}")

# --- Load our JSON records ---
def sensor_bucket_ours(sensor: str) -> str:
    """Map our sensor strings to MIROVA buckets."""
    if not sensor:
        return "UNKNOWN"
    s = sensor.upper()
    # MODIS variants
    if "MOD" in s or s.startswith("AQUA") or s.startswith("TERRA") or s in ("MODIS",):
        return "MODIS"
    # VIIRS 375m (I-band)
    if "375" in s or "VJ102IMG" in s or "VNP02IMG" in s or "_I" in s:
        return "VIIRS375"
    # VIIRS M-band 750m
    if "VIIRS" in s or "VJ102MOD" in s or "VNP02MOD" in s or "_M" in s:
        return "VIIRS"
    return "UNKNOWN"

def mirova_eq_vrp(rec: dict, inner_km: float) -> float:
    """Replicate frontend mirovaEqVrp: summit-class hotspot or
    final_hotspot_dist_km <= inner_radius_km."""
    vrp = float(rec.get("vrp_mw") or 0.0)
    if vrp <= 0:
        return 0.0
    dist = rec.get("final_hotspot_dist_km")
    dclass = rec.get("distance_class")
    if dclass == "summit":
        return vrp
    if dist is not None and dist <= inner_km:
        return vrp
    return 0.0

ours_rows = []
for vol in TIER_A:
    path = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
    if not path.exists():
        print(f"[ours] missing {vol}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    recs = d.get("records", []) if isinstance(d, dict) else d
    for r in recs:
        dt = r.get("datetime_utc")
        if not dt:
            continue
        try:
            ts = pd.to_datetime(dt, utc=True)
        except Exception:
            continue
        sensor = r.get("sensor", "")
        sb = sensor_bucket_ours(sensor)
        vrp_meq = mirova_eq_vrp(r, INNER[vol])
        ours_rows.append({
            "volcano": vol,
            "dt_utc": ts,
            "sensor_raw": sensor,
            "sensor_bucket": sb,
            "vrp_mw_raw": float(r.get("vrp_mw") or 0.0),
            "vrp_mw_meq": vrp_meq,
            "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
            "final_hotspot_source": r.get("final_hotspot_source"),
            "distance_class": r.get("distance_class"),
            "vrptir_aveni_mw": float(r.get("vrptir_aveni_mw") or 0.0)
                if r.get("vrptir_aveni_mw") is not None else 0.0,
            "n_anomalous_pixels": r.get("n_anomalous_pixels"),
            "discarded_reason": r.get("discarded_reason"),
            "granule": r.get("granule"),
        })
ours = pd.DataFrame(ours_rows)
print(f"[ours] {len(ours)} records across {ours['volcano'].nunique()} volcanoes")
print(f"[ours] sensor buckets: {ours['sensor_bucket'].value_counts().to_dict()}")

# --- Matching + master_table ---
NOW = max(mir["dt_utc"].max(), ours["dt_utc"].max())
WINDOWS = {
    "7d": NOW - pd.Timedelta(days=7),
    "30d": NOW - pd.Timedelta(days=30),
    "90d": NOW - pd.Timedelta(days=90),
    "all": min(mir["dt_utc"].min(), ours["dt_utc"].min()),
}
TOL = pd.Timedelta(minutes=60)
ALERT_CLASSES = {"Bajo", "Muy Bajo", "FALSO POSITIVO"}

def match_pair(o_sub: pd.DataFrame, m_sub: pd.DataFrame):
    """Return (matched_ratios, only_ours, only_mir, matched_pairs).
    matched_pairs: list of (o_idx, m_idx, ratio).
    """
    if o_sub.empty or m_sub.empty:
        return [], len(o_sub), len(m_sub), []
    # only consider VRP>0 on both sides for ratios; FP/FN computed separately
    pairs = []
    used_m = set()
    used_o = set()
    # sort by time both
    o_sorted = o_sub.sort_values("dt_utc")
    m_sorted = m_sub.sort_values("dt_utc")
    m_times = m_sorted["dt_utc"].values
    for o_idx, o_row in o_sorted.iterrows():
        ts = np.datetime64(o_row["dt_utc"])
        diffs = np.abs(m_times - ts)
        if len(diffs) == 0:
            continue
        j = int(diffs.argmin())
        if diffs[j] <= np.timedelta64(60, "m"):
            m_idx = m_sorted.index[j]
            if m_idx in used_m:
                continue
            used_m.add(m_idx)
            used_o.add(o_idx)
            pairs.append((o_idx, m_idx))
    ratios = []
    for o_idx, m_idx in pairs:
        ov = o_sub.loc[o_idx, "vrp_mw_meq"]
        mv = m_sub.loc[m_idx, "VRP_MW"]
        if ov > 0 and mv > 0:
            ratios.append(ov / mv)
    only_ours = (o_sub["vrp_mw_meq"] > 0).sum() - sum(
        1 for o_idx, m_idx in pairs
        if o_sub.loc[o_idx, "vrp_mw_meq"] > 0 and m_sub.loc[m_idx, "VRP_MW"] > 0)
    only_mir = (m_sub["VRP_MW"] > 0).sum() - sum(
        1 for o_idx, m_idx in pairs
        if o_sub.loc[o_idx, "vrp_mw_meq"] > 0 and m_sub.loc[m_idx, "VRP_MW"] > 0)
    return ratios, only_ours, only_mir, pairs

rows = []
for vol in TIER_A:
    for bucket in ["MODIS", "VIIRS375", "VIIRS"]:
        for wname, wstart in WINDOWS.items():
            o_sub = ours[(ours["volcano"] == vol) & (ours["sensor_bucket"] == bucket) &
                         (ours["dt_utc"] >= wstart)].copy()
            m_sub = mir[(mir["volcano_ours"] == vol) & (mir["sensor_bucket"] == bucket) &
                        (mir["dt_utc"] >= wstart)].copy()
            n_o = int((o_sub["vrp_mw_meq"] > 0).sum())
            n_m = int((m_sub["VRP_MW"] > 0).sum())
            ratios, only_o, only_m, pairs = match_pair(o_sub, m_sub)
            n_matched = len(ratios)
            row = {
                "volcano": vol,
                "sensor_bucket": bucket,
                "ventana_dias": wname,
                "n_ours_vrp_gt_0": n_o,
                "n_mirova_vrp_gt_0": n_m,
                "n_matched": n_matched,
                "n_only_ours_FP": int(only_o),
                "n_only_mirova_FN": int(only_m),
                "ratio_median": float(np.median(ratios)) if ratios else None,
                "ratio_p25": float(np.percentile(ratios, 25)) if ratios else None,
                "ratio_p75": float(np.percentile(ratios, 75)) if ratios else None,
                "p_value_wilcoxon": None,
                "max_ours": float(o_sub["vrp_mw_meq"].max()) if not o_sub.empty else 0.0,
                "max_mirova": float(m_sub["VRP_MW"].max()) if not m_sub.empty else 0.0,
            }
            if n_matched >= 6:
                try:
                    from scipy.stats import wilcoxon
                    # paired test: ours_vrp vs mir_vrp on matched pairs (only both >0)
                    o_vals = []
                    m_vals = []
                    for o_idx, m_idx in pairs:
                        ov = o_sub.loc[o_idx, "vrp_mw_meq"]
                        mv = m_sub.loc[m_idx, "VRP_MW"]
                        if ov > 0 and mv > 0:
                            o_vals.append(ov)
                            m_vals.append(mv)
                    if len(o_vals) >= 6:
                        try:
                            stat, p = wilcoxon(o_vals, m_vals)
                            row["p_value_wilcoxon"] = float(p)
                        except Exception:
                            pass
                except Exception:
                    pass
            rows.append(row)

master = pd.DataFrame(rows)
master.to_csv(OUT / "master_table.csv", index=False)
print(f"[master_table] {len(master)} rows -> {OUT / 'master_table.csv'}")

# --- Anomalies ---
ANOM = []

# (1) ours vrp_mw > 100 MW top 50
top_vrp = ours[ours["vrp_mw_raw"] > 100].nlargest(50, "vrp_mw_raw")[
    ["volcano", "dt_utc", "sensor_raw", "vrp_mw_raw", "vrp_mw_meq", "final_hotspot_dist_km",
     "final_hotspot_source", "distance_class", "n_anomalous_pixels", "granule"]
].assign(category="vrp_mw_gt_100")
ANOM.append(top_vrp)

# (2) vrptir_aveni_mw > 100 top 20
top_aveni = ours[ours["vrptir_aveni_mw"] > 100].nlargest(20, "vrptir_aveni_mw")[
    ["volcano", "dt_utc", "sensor_raw", "vrptir_aveni_mw", "vrp_mw_raw", "n_anomalous_pixels", "granule"]
].assign(category="vrptir_aveni_gt_100")
ANOM.append(top_aveni)

# (3) cluster_rescue top 20
cr = ours[ours["final_hotspot_source"] == "cluster_rescue"].nlargest(20, "vrp_mw_raw")[
    ["volcano", "dt_utc", "sensor_raw", "vrp_mw_raw", "final_hotspot_dist_km", "n_anomalous_pixels", "granule"]
].assign(category="cluster_rescue")
ANOM.append(cr)

# (4) cluster_too_large_for_volcano all
ctl = ours[ours["discarded_reason"] == "cluster_too_large_for_volcano"][
    ["volcano", "dt_utc", "sensor_raw", "vrp_mw_raw", "n_anomalous_pixels", "granule", "discarded_reason"]
].assign(category="cluster_too_large_for_volcano")
ANOM.append(ctl)

# (5) single_pixel_far_overridden_by_cluster all
sp = ours[ours["discarded_reason"] == "single_pixel_far_overridden_by_cluster"][
    ["volcano", "dt_utc", "sensor_raw", "vrp_mw_raw", "n_anomalous_pixels", "granule", "discarded_reason"]
].assign(category="single_pixel_far_overridden_by_cluster")
ANOM.append(sp)

anom_df = pd.concat(ANOM, ignore_index=True)
anom_df.to_csv(OUT / "anomalies.csv", index=False)
print(f"[anomalies] {len(anom_df)} rows -> {OUT / 'anomalies.csv'}")

# --- GAPS: MIROVA alerts last 90d without ours match ---
m90 = mir[(mir["dt_utc"] >= NOW - pd.Timedelta(days=90)) &
          (mir["Clasificacion Mirova"].isin(ALERT_CLASSES))].copy()

gap_rows = []
for _, mrow in m90.iterrows():
    vol = mrow["volcano_ours"]
    bucket = mrow["sensor_bucket"]
    ts = mrow["dt_utc"]
    o_sub = ours[(ours["volcano"] == vol) & (ours["sensor_bucket"] == bucket)]
    if not o_sub.empty:
        diffs = (o_sub["dt_utc"] - ts).abs()
        j_min = diffs.idxmin() if len(diffs) else None
        if j_min is not None and diffs.loc[j_min] <= TOL:
            o_row = o_sub.loc[j_min]
            if o_row["vrp_mw_meq"] > 0:
                continue  # matched, not a gap
            gap_rows.append({
                "fecha_utc": ts,
                "volcano": vol,
                "sensor": bucket,
                "mirova_vrp_mw": mrow["VRP_MW"],
                "mirova_class": mrow["Clasificacion Mirova"],
                "ours_present": True,
                "ours_vrp_raw": o_row["vrp_mw_raw"],
                "ours_vrp_meq": o_row["vrp_mw_meq"],
                "ours_dist_km": o_row["final_hotspot_dist_km"],
                "ours_discarded_reason": o_row["discarded_reason"],
                "ours_granule": o_row["granule"],
                "delta_min": float(diffs.loc[j_min].total_seconds() / 60.0),
            })
            continue
    gap_rows.append({
        "fecha_utc": ts,
        "volcano": vol,
        "sensor": bucket,
        "mirova_vrp_mw": mrow["VRP_MW"],
        "mirova_class": mrow["Clasificacion Mirova"],
        "ours_present": False,
        "ours_vrp_raw": None,
        "ours_vrp_meq": None,
        "ours_dist_km": None,
        "ours_discarded_reason": None,
        "ours_granule": None,
        "delta_min": None,
    })

gaps_df = pd.DataFrame(gap_rows)
gaps_df.to_csv(OUT / "gaps.csv", index=False)
print(f"[gaps] {len(gaps_df)} MIROVA alerts (last 90d, non-NULO) -> {OUT / 'gaps.csv'}")

# --- summary.json ---
summary = {
    "run_at": datetime.now(timezone.utc).isoformat(),
    "csv_path": str(csv_path.name),
    "csv_rows_total": int(len(pd.read_csv(csv_path))),
    "csv_date_range": [str(mir["dt_utc"].min()), str(mir["dt_utc"].max())],
    "csv_classifications": mir["Clasificacion Mirova"].value_counts().to_dict(),
    "ours_records_total": int(len(ours)),
    "ours_volcanoes": int(ours["volcano"].nunique()),
    "ours_date_range": [str(ours["dt_utc"].min()), str(ours["dt_utc"].max())],
    "tier_a": TIER_A,
    "inner_radius_km": INNER,
    "osf_v25_local": False,
    "osf_v25_note": "No OSF v2.5 archive present locally. data/mirova_reference/ contains only OCR ground truth (236 rows) and a v1 snapshot of the same NRT CSV.",
    "anomaly_counts": {
        "vrp_mw_gt_100": int((ours["vrp_mw_raw"] > 100).sum()),
        "vrptir_aveni_gt_100": int((ours["vrptir_aveni_mw"] > 100).sum()),
        "cluster_rescue": int((ours["final_hotspot_source"] == "cluster_rescue").sum()),
        "cluster_too_large_for_volcano": int(
            (ours["discarded_reason"] == "cluster_too_large_for_volcano").sum()),
        "single_pixel_far_overridden_by_cluster": int(
            (ours["discarded_reason"] == "single_pixel_far_overridden_by_cluster").sum()),
    },
    "gap_counts": {
        "n_total_mirova_alerts_90d": int(len(gaps_df)),
        "n_no_ours_record": int((~gaps_df["ours_present"]).sum()) if not gaps_df.empty else 0,
        "n_ours_zero_meq": int(((gaps_df["ours_present"]) & (gaps_df["ours_vrp_meq"] == 0)).sum())
            if not gaps_df.empty else 0,
    },
}
with open(OUT / "summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"[summary] -> {OUT / 'summary.json'}")
print("DONE")
