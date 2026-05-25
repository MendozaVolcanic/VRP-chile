"""
S78 audit pasada-por-pasada — MIROVA NRT vs ours for 11 Tier A volcanoes.

Read-only. Outputs:
  - master.csv: per (volcano, sensor) counts + ratio stats + FN/FP counts
  - lagos_persistentes.csv: records near known lake exclude_zones
  - per_pass_pairs.csv: matched pairs for inspection
  - fn_pasadas.csv: MIROVA detected, ours didn't (±5 min)
  - fp_pasadas.csv: ours detected, MIROVA didn't (±5 min)
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

# ---- Mapping (Tier A volcano: our JSON filename <-> CSV volcano label) ----
TIER_A = {
    # ours_name             :  (csv_label_in_consolidado,)
    "PuyehueCordonCaulle":   "Puyehue-Cordon Caulle",
    "Villarrica":            "Villarrica",
    "Lascar":                "Lascar",
    "Copahue":               "Copahue",
    "NevadosDeChillan":      "Nevados de Chillan",
    "Llaima":                "Llaima",
    "Chaiten":               "Chaiten",
    "PlanchonPeteroa":       "PlanchonPeteroa",
    "Lastarria":             "Lastarria",
    "Isluga":                "Isluga",
    "Tupungatito":           "Tupungatito",
}

MATCH_TOLERANCE_MIN = 5  # ±5 min match window

EARTH_R = 6371.0
def haversine_km(lat1, lon1, lat2, lon2):
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = rlat2 - rlat1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(rlat1)*math.cos(rlat2)*math.sin(dlon/2)**2
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def sensor_bucket(sensor_raw: str) -> str:
    """Normalize sensor labels for matching MIROVA CSV vs ours."""
    s = str(sensor_raw).upper()
    # MIROVA CSV uses 'VIIRS' or 'MODIS'
    if "VIIRS" in s or "I04" in s or "I05" in s or "M13" in s or "M15" in s or s.startswith("VJ") or s.startswith("VNP"):
        return "VIIRS"
    if "MODIS" in s or "AQUA" in s or "TERRA" in s or s.startswith("MOD") or s.startswith("MYD"):
        return "MODIS"
    return s


def load_yaml_cfg():
    with open(ROOT / "volcanoes.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    by_name = {v["name"]: v for v in cfg["volcanoes"]}
    return by_name


def load_mirova_csv():
    df = pd.read_csv(ROOT / "latest_consolidado.csv")
    df["dt"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df = df.dropna(subset=["dt"])
    df["sensor_bucket"] = df["Sensor"].map(sensor_bucket)
    df["clasif_clean"] = df["Clasificacion Mirova"].fillna("").str.strip()
    return df


def load_ours(name: str) -> pd.DataFrame:
    p = ROOT / "data" / "mirova_equivalent" / f"{name}.json"
    if not p.exists():
        return pd.DataFrame()
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    recs = d.get("records", []) if isinstance(d, dict) else d
    rows = []
    for r in recs:
        dt = r.get("datetime_utc")
        if not dt:
            continue
        pc = r.get("primary_cluster") or {}
        rows.append({
            "datetime_utc": dt,
            "sensor": r.get("sensor"),
            "sensor_bucket": sensor_bucket(r.get("sensor", "")),
            "vrp_mw": float(r.get("vrp_mw") or 0),
            "n_anomalous_pixels": int(r.get("n_anomalous_pixels") or 0),
            "primary_n_pixels": int(pc.get("n_pixels") or 0),
            "primary_lat": pc.get("centroid_lat"),
            "primary_lon": pc.get("centroid_lon"),
            "primary_dist_km": pc.get("centroid_dist_km"),
            "primary_vrp_mw": float(pc.get("vrp_mw") or 0),
            "final_hotspot_lat": r.get("final_hotspot_lat"),
            "final_hotspot_lon": r.get("final_hotspot_lon"),
            "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
            "distance_class": r.get("distance_class"),
            "t_max_k": r.get("t_max_k"),
            "granule": r.get("granule"),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["dt"] = pd.to_datetime(df["datetime_utc"], errors="coerce")
    df = df.dropna(subset=["dt"])
    return df


# ---- Section 1: granularity counts per (vol, sensor, minute) ----
def granularity_table(name_ours, csv_label, df_csv, df_ours):
    sub_csv = df_csv[df_csv["Volcan"] == csv_label].copy()
    sub_csv["minute_key"] = sub_csv["dt"].dt.floor("min")
    cnt_csv = sub_csv.groupby(["minute_key", "sensor_bucket"]).size().reset_index(name="n_mirova")

    df_ours = df_ours.copy()
    if df_ours.empty:
        cnt_ours = pd.DataFrame(columns=["minute_key", "sensor_bucket", "n_ours"])
    else:
        df_ours["minute_key"] = df_ours["dt"].dt.floor("min")
        cnt_ours = df_ours.groupby(["minute_key", "sensor_bucket"]).size().reset_index(name="n_ours")

    merged = cnt_csv.merge(cnt_ours, on=["minute_key", "sensor_bucket"], how="outer").fillna(0)
    merged["n_mirova"] = merged["n_mirova"].astype(int)
    merged["n_ours"] = merged["n_ours"].astype(int)
    merged["volcano"] = name_ours
    # summary
    summary = {
        "volcano": name_ours,
        "n_mirova_passes": int((merged["n_mirova"] > 0).sum()),
        "n_ours_passes": int((merged["n_ours"] > 0).sum()),
        "n_passes_mirova_eq1_ours_gt1": int(((merged["n_mirova"] == 1) & (merged["n_ours"] > 1)).sum()),
        "n_passes_mirova_eq1_ours_eq1": int(((merged["n_mirova"] == 1) & (merged["n_ours"] == 1)).sum()),
        "n_passes_ours_avg_per_mirova_pass": float(merged.loc[merged["n_mirova"] >= 1, "n_ours"].mean()) if (merged["n_mirova"] >= 1).any() else 0.0,
        "max_ours_for_single_mirova": int(merged.loc[merged["n_mirova"] == 1, "n_ours"].max()) if (merged["n_mirova"] == 1).any() else 0,
    }
    return merged, summary


# ---- Section 2 & 3 & 4: temporal match ±5 min ----
def match_passes(df_csv_vol, df_ours, tol_min=MATCH_TOLERANCE_MIN):
    """For each MIROVA pass (CSV row), find closest ours within ±tol_min same sensor bucket.
    Returns pairs DF (one-to-one greedy match)."""
    pairs = []
    unmatched_mirova = []
    used_ours = set()

    df_csv_vol = df_csv_vol.sort_values("dt").reset_index(drop=True)
    if df_ours.empty:
        for _, m in df_csv_vol.iterrows():
            unmatched_mirova.append(m)
        return pd.DataFrame(pairs), pd.DataFrame(unmatched_mirova), df_ours.copy() if not df_ours.empty else df_ours

    df_ours = df_ours.sort_values("dt").reset_index(drop=True)
    ours_by_sensor = {s: g.copy() for s, g in df_ours.groupby("sensor_bucket")}

    tol = pd.Timedelta(minutes=tol_min)

    for _, m in df_csv_vol.iterrows():
        sb = m["sensor_bucket"]
        cand = ours_by_sensor.get(sb)
        if cand is None or cand.empty:
            unmatched_mirova.append(m)
            continue
        dts = cand["dt"]
        diffs = (dts - m["dt"]).abs()
        idx_min = diffs.idxmin()
        if diffs.loc[idx_min] <= tol and idx_min not in used_ours:
            used_ours.add(idx_min)
            o = cand.loc[idx_min]
            pairs.append({
                "volcano_csv": m["Volcan"],
                "sensor_bucket": sb,
                "mirova_dt": m["dt"],
                "ours_dt": o["dt"],
                "diff_min": float(diffs.loc[idx_min].total_seconds() / 60.0),
                "mirova_vrp_mw": float(m["VRP_MW"]) if pd.notna(m["VRP_MW"]) else 0.0,
                "mirova_clasif": m["clasif_clean"],
                "mirova_dist_km": float(m["Distancia_km"]) if pd.notna(m["Distancia_km"]) else None,
                "ours_vrp_mw": float(o["vrp_mw"]),
                "ours_primary_vrp_mw": float(o["primary_vrp_mw"]),
                "ours_n_anomalous_pixels": int(o["n_anomalous_pixels"]),
                "ours_primary_n_pixels": int(o["primary_n_pixels"]),
                "ours_primary_lat": o["primary_lat"],
                "ours_primary_lon": o["primary_lon"],
                "ours_distance_class": o["distance_class"],
                "ours_final_hotspot_dist_km": o["final_hotspot_dist_km"],
                "ratio_ours_mirova": (float(o["vrp_mw"]) / float(m["VRP_MW"])) if (pd.notna(m["VRP_MW"]) and float(m["VRP_MW"]) > 0) else None,
            })
        else:
            unmatched_mirova.append(m)

    # ours not used = FP candidates
    ours_unmatched = df_ours.drop(index=list(used_ours)).copy()
    return pd.DataFrame(pairs), pd.DataFrame(unmatched_mirova), ours_unmatched


# ---- Section 5: lake-proximity ----
def lake_proximity(name_ours, df_ours, cfg_vol):
    ez = cfg_vol.get("exclude_zones") or []
    if not ez or df_ours.empty:
        return pd.DataFrame()
    rows = []
    for _, r in df_ours.iterrows():
        lat = r["primary_lat"] or r["final_hotspot_lat"]
        lon = r["primary_lon"] or r["final_hotspot_lon"]
        if lat is None or lon is None:
            continue
        for z in ez:
            d = haversine_km(lat, lon, z["lat"], z["lon"])
            buf = z["radius_km"] * 1.5
            if d <= buf:
                rows.append({
                    "volcano": name_ours,
                    "datetime_utc": str(r["datetime_utc"]),
                    "sensor": r["sensor"],
                    "primary_lat": lat,
                    "primary_lon": lon,
                    "vrp_mw": r["vrp_mw"],
                    "n_anom_pixels": r["n_anomalous_pixels"],
                    "primary_n_pixels": r["primary_n_pixels"],
                    "distance_class": r["distance_class"],
                    "lake_name": z["name"],
                    "dist_to_lake_center_km": round(d, 2),
                    "lake_radius_km": z["radius_km"],
                    "in_exclude_zone": d <= z["radius_km"],
                    "in_buffer_15x": (d > z["radius_km"]) and (d <= buf),
                })
                break  # one lake per record
    return pd.DataFrame(rows)


def main():
    cfg_by_name = load_yaml_cfg()
    df_csv = load_mirova_csv()

    master_rows = []
    all_pairs = []
    all_fn = []
    all_fp = []
    all_gran = []
    all_lakes = []
    inflated_rows = []  # Section 6

    print(f"MIROVA CSV total rows: {len(df_csv)}")

    for ours_name, csv_label in TIER_A.items():
        df_csv_vol = df_csv[df_csv["Volcan"] == csv_label].copy()
        # Only NRT real detections: classification != NULO, and VRP > 0
        df_csv_real = df_csv_vol[(df_csv_vol["clasif_clean"].str.upper() != "NULO") & (df_csv_vol["VRP_MW"] > 0)].copy()

        df_ours = load_ours(ours_name)
        print(f"\n=== {ours_name} | csv={csv_label} ===  mirova_csv_rows={len(df_csv_vol)}  mirova_real={len(df_csv_real)}  ours={len(df_ours)}")

        if df_ours.empty:
            print(f"  WARN: no ours data for {ours_name}")
            continue

        # Section 1: granularity
        gran, gran_summary = granularity_table(ours_name, csv_label, df_csv_real, df_ours)
        all_gran.append(gran)

        # Section 2-4: match passes (use REAL mirova only for ratio/FN; use all mirova-real-passes for FP determination)
        pairs, fn_mirova, fp_ours = match_passes(df_csv_real, df_ours)
        if not pairs.empty:
            pairs["volcano"] = ours_name
            all_pairs.append(pairs)
        if not fn_mirova.empty:
            fn_mirova = fn_mirova.copy()
            fn_mirova["volcano"] = ours_name
            all_fn.append(fn_mirova[["volcano", "Volcan", "dt", "Sensor", "sensor_bucket", "VRP_MW", "Distancia_km", "clasif_clean"]])

        # FP: ours has vrp_mw > 0 and no MIROVA-real match
        fp_pos = fp_ours[fp_ours["vrp_mw"] > 0].copy()
        if not fp_pos.empty:
            fp_pos["volcano"] = ours_name
            all_fp.append(fp_pos[["volcano", "datetime_utc", "sensor", "sensor_bucket", "vrp_mw", "n_anomalous_pixels", "primary_n_pixels", "primary_lat", "primary_lon", "primary_dist_km", "distance_class", "t_max_k"]])

        # ratio stats
        ratios = pairs["ratio_ours_mirova"].dropna() if not pairs.empty else pd.Series([], dtype=float)

        # Section 5: lakes
        cfg_vol = cfg_by_name.get(ours_name, {})
        lakes = lake_proximity(ours_name, df_ours, cfg_vol)
        if not lakes.empty:
            all_lakes.append(lakes)

        # Section 6: inflated MODIS (n_anomalous>50 vs primary<20)
        inflated = df_ours[(df_ours["sensor_bucket"] == "MODIS") & (df_ours["n_anomalous_pixels"] > 50)]
        n_inflated = len(inflated)
        n_inflated_summit_ok = int(((inflated["primary_n_pixels"] < 20) & (inflated["distance_class"] == "summit")).sum()) if n_inflated else 0
        n_inflated_far_big = int(((inflated["primary_n_pixels"] >= 20) | (inflated["distance_class"] != "summit")).sum()) if n_inflated else 0
        if n_inflated:
            tmp = inflated.copy()
            tmp["volcano"] = ours_name
            inflated_rows.append(tmp[["volcano","datetime_utc","sensor","n_anomalous_pixels","primary_n_pixels","primary_vrp_mw","vrp_mw","primary_dist_km","distance_class"]])

        # Master row
        master_rows.append({
            "volcano": ours_name,
            "mirova_csv_label": csv_label,
            "n_mirova_rows_all": len(df_csv_vol),
            "n_mirova_rows_real": len(df_csv_real),
            "n_ours_records": len(df_ours),
            "n_ours_records_vrp_gt0": int((df_ours["vrp_mw"] > 0).sum()),
            **gran_summary,
            "n_matched_pairs": len(pairs),
            "n_FN_mirova_no_ours": len(fn_mirova),
            "n_FP_ours_no_mirova": len(fp_pos),
            "ratio_median": float(ratios.median()) if len(ratios) else None,
            "ratio_p25": float(ratios.quantile(0.25)) if len(ratios) else None,
            "ratio_p75": float(ratios.quantile(0.75)) if len(ratios) else None,
            "n_lake_proximity": len(lakes),
            "n_in_exclude_zone": int(lakes["in_exclude_zone"].sum()) if not lakes.empty else 0,
            "n_in_buffer_15x": int(lakes["in_buffer_15x"].sum()) if not lakes.empty else 0,
            "n_MODIS_inflated_pixels50plus": n_inflated,
            "n_MODIS_inflated_summit_primary_ok": n_inflated_summit_ok,
        })

    # ---- write outputs ----
    pd.DataFrame(master_rows).to_csv(OUT / "master.csv", index=False)
    if all_pairs:
        pd.concat(all_pairs, ignore_index=True).to_csv(OUT / "per_pass_pairs.csv", index=False)
    if all_fn:
        pd.concat(all_fn, ignore_index=True).to_csv(OUT / "fn_pasadas.csv", index=False)
    if all_fp:
        pd.concat(all_fp, ignore_index=True).to_csv(OUT / "fp_pasadas.csv", index=False)
    if all_gran:
        pd.concat(all_gran, ignore_index=True).to_csv(OUT / "granularity_per_pass.csv", index=False)
    if all_lakes:
        pd.concat(all_lakes, ignore_index=True).to_csv(OUT / "lagos_persistentes.csv", index=False)
    if inflated_rows:
        pd.concat(inflated_rows, ignore_index=True).to_csv(OUT / "modis_inflated.csv", index=False)
    print("\nDONE. Outputs in", OUT)


if __name__ == "__main__":
    main()
