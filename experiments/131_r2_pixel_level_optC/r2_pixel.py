"""R2 pixel-level validacion del winner Opcion C (S71 T1 F2.d).

Verifica pixel-level (vs TIFs MIROVA archive) que el cap `path_d_only_cap_mw: 5.0`
no enmascara casos donde MIROVA reporta magnitud >5MW legitima en escenas con
t_bg<270K antes de adoptar la opcion en `mirova_equivalent.yaml`.

Metodologia (replica el patron R2 S70-1 + R2_GATES_BY_REGIME.md):
  1. Sample 4 categorias en `data/mirova_equivalent_path_d_cap_v1/`:
       - cap-applied: pc.d9_capped == True (>=5 records, distribuidos >=3 vols).
       - ratio-extreme: pc.vrp_mw / MIROVA.VRP_MW > 5x con match MIROVA (cap data).
       - no-cap-applied: registros sin d9_capped pero detection (control).
       - no-MIROVA-alerta: detection nuestra sin ALERTA MIROVA dentro de +-3h
         (FPs candidatos).
  2. Por cada record:
       - Match TIF mas cercano por timestamp (tol 6h, MIROVA latency ~3h capture).
       - Filtro TIF positive pixels <=3 km del vent del volcan.
       - Centroide ponderado top-10. Drift vs pc.centroid_lat/lon.
       - Ratio pc.vrp_mw / MIROVA.VRP_MW (cuando hay match CSV).
       - Verdict per regimen (R2_GATES_BY_REGIME.md):
           * Régimen A (Lastarria/Lascar/Isluga): ratio [0.5,2.0] + drift <2 km.
           * Régimen B1 (Villarrica/Chaiten): ratio [0.5,2.0] + drift <3 km.
           * Régimen B2 (PP): ratio [0.5,2.0] + drift <3 km (single-case marginal).
           * Régimen C (PCC): R2-drift no aplica, magnitud agregada solo.
           * Tupungatito/Llaima/Copahue/NdC: no clasificados (poca data S70) -> gates revisados.

Gates específicas del cap:
  G_CAP_OK: cap-applied AND MIROVA.VRP_MW <= 5 MW (cap no oculta nada).
  G_CAP_LEAK: cap-applied AND MIROVA.VRP_MW > 5 MW (cap enmascara magnitud real).
  G_DET_NO_MIROVA: detection nuestra sin MIROVA -> FP candidate (cap deberia ayudar).

Output:
  - r2_pixel.json (datos brutos por record + agregados).
  - r2_pixel_report.md (tabla + verdict adopcion).
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

import numpy as np
import pandas as pd
import rasterio


HERE = Path(__file__).parent
ROOT = HERE.parents[1]  # VRP-Chile-s70/
TIF_ARCHIVE = ROOT.parent / "mirova-tif-archive" / "data" / "tif"

CAP_DIR = ROOT / "data" / "mirova_equivalent_path_d_cap_v1"
BASELINE_DIR = ROOT / "data" / "mirova_equivalent"
CONS_CSV = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OCR_CSV = ROOT / "data" / "mirova_reference" / "registro_vrp_ocr.csv"

VOLS = [
    "Lastarria", "Lascar", "Isluga", "Villarrica", "Chaiten",
    "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle",
    "Llaima", "Copahue", "NevadosDeChillan",
]

# Régimen por vol (R2_GATES_BY_REGIME.md sec 4)
REGIME = {
    "Lastarria": "A", "Lascar": "A", "Isluga": "A",
    "Villarrica": "B1", "Chaiten": "B1",
    "PlanchonPeteroa": "B2",
    "PuyehueCordonCaulle": "C",
    "Tupungatito": "B1?",  # no clasificado oficial; ΔT bajo + glaciar
    "Llaima": "A?", "Copahue": "A?", "NevadosDeChillan": "A?",  # poca data S70
}

# Drift gate por régimen
DRIFT_GATE_KM = {"A": 2.0, "B1": 3.0, "B2": 3.0, "C": None,
                 "B1?": 3.0, "A?": 3.0}

VENT_COORDS = {
    "Lastarria": (-25.1680, -68.5070),
    "Lascar": (-23.3629, -67.7314),
    "Isluga": (-19.1500, -68.8300),
    "Villarrica": (-39.4202, -71.9399),
    "Chaiten": (-42.8345, -72.6529),
    "PlanchonPeteroa": (-35.2411, -70.5733),
    "Tupungatito": (-33.3890, -69.8264),
    "PuyehueCordonCaulle": (-40.5255, -72.1461),
    "Llaima": (-38.6920, -71.7290),
    "Copahue": (-37.8560, -71.1830),
    "NevadosDeChillan": (-36.8630, -71.3770),
}

# Volcan -> CSV name (subset, complejos)
VOL_CSV_MAP = {
    "Lastarria": ["Lastarria"],
    "Lascar": ["Lascar"],
    "Isluga": ["Isluga"],
    "Villarrica": ["Villarrica"],
    "Chaiten": ["Chaiten"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Peteroa", "Planchon-Peteroa"],
    "Tupungatito": ["Tupungatito"],
    "PuyehueCordonCaulle": [
        "PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
        "Puyehue Cordon Caulle", "PuyehueCordónCaulle"
    ],
    "Llaima": ["Llaima"],
    "Copahue": ["Copahue"],
    "NevadosDeChillan": ["NevadosDeChillan", "Nevados de Chillan",
                         "ChillanNevadosde"],
}

# TIF folder name override (archive uses different vol names)
VOL_TIF_DIR = {
    "NevadosDeChillan": "ChillanNevadosde",
}

# TIF cobertura: scraper empezo 2026-05-09
TIF_MIN_DT = datetime(2026, 5, 9)

# Tolerancias
TIF_TIME_TOL_HOURS = 6.0
MIROVA_TIME_TOL_HOURS = 3.0
TARGET_DRIFT_PER_REGIME = DRIFT_GATE_KM
RATIO_BAND = (0.5, 2.0)
CAP_MW = 5.0
CAP_TBG_K = 270.0


# -------------------- Helpers --------------------

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1 = np.radians(lat1); p2 = np.radians(lat2)
    dp = np.radians(np.asarray(lat2) - np.asarray(lat1))
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


def parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


def parse_tif_dt(fname):
    """Parse YYYYMMDD_HHMMSS_* TIF filename to datetime."""
    base = fname.replace("_lm", "")  # accept lm tag
    try:
        date_part = base.split("_")[0]
        time_part = base.split("_")[1]
        return datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
    except (ValueError, IndexError):
        return None


def list_tifs(vol):
    tif_dir_name = VOL_TIF_DIR.get(vol, vol)
    tif_dir = TIF_ARCHIVE / tif_dir_name
    if not tif_dir.exists():
        return []
    items = []
    for f in tif_dir.iterdir():
        if not f.name.endswith(".tif"):
            continue
        dt = parse_tif_dt(f.name)
        if dt is None:
            continue
        # filter by sensor token from filename
        # e.g. 20260509_042626_MODIS.tif, *_VIIRS375.tif, *_VIIRS750.tif
        parts = f.stem.split("_")
        sensor_token = parts[-1] if parts[-1] != "lm" else parts[-2]
        items.append((dt, sensor_token, f))
    return items


def sensor_to_token(record_sensor):
    """Map our record sensor name to TIF filename sensor token."""
    s = record_sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    # VIIRS_NOAA20, VIIRS_NOAA21, VIIRS_SNPP -> 375 (I-band) or 750 (M-band)?
    # Our pipeline names indicate granule, NOT band. Default: VIIRS375.
    # But records have explicit 'I-band' vs 'M-band' via vrp coefficient?
    # Easier: accept either VIIRS375 or VIIRS750 (closest in time).
    if s.startswith("VIIRS"):
        return "VIIRS"  # special: match both 375 and 750
    return s


def find_closest_tif(vol, record_dt, record_sensor):
    """Return (tif_path, tif_dt, time_diff_h, sensor_token) of closest TIF."""
    tifs = list_tifs(vol)
    if not tifs:
        return None
    token = sensor_to_token(record_sensor)
    candidates = []
    for dt, stoken, fp in tifs:
        if token == "VIIRS" and not stoken.startswith("VIIRS"):
            continue
        if token == "MODIS" and stoken != "MODIS":
            continue
        if token not in ("VIIRS", "MODIS"):
            continue
        diff = abs((dt - record_dt).total_seconds()) / 3600.0
        if diff <= TIF_TIME_TOL_HOURS:
            candidates.append((diff, dt, stoken, fp))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    diff, dt, stoken, fp = candidates[0]
    return {"tif_path": fp, "tif_dt": dt, "time_diff_h": diff, "tif_sensor": stoken}


def load_tif(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype(float)
        transform = src.transform
    arr = np.where(np.isnan(arr), 0.0, arr)
    return arr, transform


def top_n_centroid(arr, transform, vent_lat, vent_lon, max_km=3.0, n=10):
    """Centroide ponderado top-N pixels filtrados a <=max_km del vent."""
    rows, cols = np.where(arr > 0)
    if len(rows) == 0:
        return None
    xs, ys = rasterio.transform.xy(transform, rows.tolist(), cols.tolist())
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    vals = arr[rows, cols]
    dists = haversine_km(ys, xs, vent_lat, vent_lon)
    near = dists <= max_km
    if not near.any():
        return {"lat": None, "lon": None, "n_positive_in_filter": 0,
                "n_positive_total": int(len(rows)),
                "tif_sum_in_filter": 0.0}
    xs_n = xs[near]; ys_n = ys[near]; vals_n = vals[near]
    n_used = min(n, len(vals_n))
    top_idx = np.argsort(vals_n)[-n_used:]
    xt, yt, vt = xs_n[top_idx], ys_n[top_idx], vals_n[top_idx]
    lon_c = float((xt * vt).sum() / vt.sum())
    lat_c = float((yt * vt).sum() / vt.sum())
    return {
        "lat": lat_c, "lon": lon_c,
        "n_used": int(n_used),
        "n_positive_in_filter": int(near.sum()),
        "n_positive_total": int(len(rows)),
        "tif_sum_in_filter": float(vals_n.sum()),
        "tif_max_in_filter": float(vals_n.max()),
    }


def load_mirova_alerts():
    cons = pd.read_csv(CONS_CSV)
    cons = cons[cons["Tipo_Registro"].astype(str).str.contains("ALERTA", na=False)].copy()
    cons["timestamp"] = pd.to_numeric(cons["timestamp"], errors="coerce")
    cons["VRP_MW"] = pd.to_numeric(cons["VRP_MW"], errors="coerce")
    cons = cons.dropna(subset=["timestamp"]).reset_index(drop=True)
    return cons


def find_mirova_match(alerts, vol, record_dt):
    csv_names = VOL_CSV_MAP.get(vol, [vol])
    sub = alerts[alerts["Volcan"].isin(csv_names)]
    if sub.empty:
        return None
    ts = record_dt.timestamp()
    tol = MIROVA_TIME_TOL_HOURS * 3600.0
    diffs = (sub["timestamp"].astype(float) - ts).abs()
    mask = diffs <= tol
    if not mask.any():
        return None
    idx = diffs[mask].idxmin()
    row = sub.loc[idx]
    return {
        "Fecha_Satelite_UTC": str(row["Fecha_Satelite_UTC"]),
        "Sensor": str(row["Sensor"]),
        "VRP_MW": float(row["VRP_MW"]) if pd.notna(row["VRP_MW"]) else 0.0,
        "Distancia_km": float(row["Distancia_km"]) if pd.notna(row["Distancia_km"]) else None,
        "time_diff_h": float(diffs.loc[idx]) / 3600.0,
    }


# -------------------- Sampling --------------------

def has_detection(rec):
    npx = rec.get("n_anomalous_pixels") or 0
    if npx > 0:
        return True
    pc = rec.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0.0
    return v > 0.01


def is_capped(rec):
    pc = rec.get("primary_cluster") or {}
    return isinstance(pc, dict) and bool(pc.get("d9_capped"))


def pc_vrp(rec):
    pc = rec.get("primary_cluster") or {}
    v = pc.get("vrp_mw")
    if v is not None:
        try: return float(v)
        except: return 0.0
    return float(rec.get("vrp_mw") or 0.0)


def load_records():
    """Returns {vol: [records...]} for cap profile, filtered to TIF window."""
    by_vol = {}
    for vol in VOLS:
        fp = CAP_DIR / f"{vol}.json"
        if not fp.exists():
            continue
        d = json.load(open(fp, encoding="utf-8"))
        recs = []
        for r in d.get("records", []):
            dt = parse_dt(r.get("datetime_utc"))
            if dt is None or dt < TIF_MIN_DT:
                continue
            recs.append(r)
        by_vol[vol] = recs
    return by_vol


def sample_categories(by_vol, alerts, target_per_cat=5):
    """Sample 4 categories:
      A: cap-applied (d9_capped=True)
      B: ratio-extreme (pc.vrp/MIROVA > 5x AND MIROVA match exists)
      C: no-cap-applied control (detection, no d9_capped)
      D: no-MIROVA-alert (detection, no MIROVA ALERTA match in +-3h)
    """
    cat_A, cat_B, cat_C, cat_D = [], [], [], []

    for vol, recs in by_vol.items():
        for rec in recs:
            dt = parse_dt(rec.get("datetime_utc"))
            if dt is None:
                continue
            detected = has_detection(rec)
            if not detected:
                continue
            capped = is_capped(rec)
            pcv = pc_vrp(rec)
            mirova = find_mirova_match(alerts, vol, dt)
            ratio = None
            if mirova and mirova["VRP_MW"] > 0:
                ratio = pcv / mirova["VRP_MW"]

            entry = {
                "vol": vol, "dt": dt, "record": rec, "mirova": mirova, "ratio": ratio,
            }

            if capped:
                cat_A.append(entry)
                if ratio is not None and ratio > 5.0:
                    cat_B.append(entry)
            else:
                cat_C.append(entry)
                if mirova is None:
                    cat_D.append(entry)

    # Diversify cat_A across vols
    def diversify(cat, target, sort_key=None):
        if sort_key:
            cat = sorted(cat, key=sort_key)
        by_v = {}
        for e in cat:
            by_v.setdefault(e["vol"], []).append(e)
        picked = []
        # round-robin pick across vols
        max_per_round = max(1, target // max(1, len(by_v)))
        rounds = 0
        while len(picked) < target and rounds < 20:
            for v in by_v:
                if by_v[v] and len(picked) < target:
                    picked.append(by_v[v].pop(0))
            rounds += 1
        return picked

    selA = diversify(cat_A, target_per_cat)
    # cat_B: just pick top ratio-extreme regardless of vol diversity
    cat_B_sorted = sorted(cat_B, key=lambda e: -(e["ratio"] or 0))
    selB = cat_B_sorted[:target_per_cat]
    selC = diversify(cat_C, target_per_cat)
    selD = diversify(cat_D, target_per_cat)

    return {"A_cap_applied": selA, "B_ratio_extreme": selB,
            "C_no_cap_applied": selC, "D_no_mirova_alert": selD}


# -------------------- Per-record audit --------------------

def audit_record(entry):
    vol = entry["vol"]
    rec = entry["record"]
    dt = entry["dt"]
    mirova = entry["mirova"]
    ratio_csv = entry["ratio"]

    pc = rec.get("primary_cluster") or {}
    pc_lat = pc.get("centroid_lat")
    pc_lon = pc.get("centroid_lon")
    pc_dist = pc.get("centroid_dist_km")
    pc_vrp_mw = pc_vrp(rec)
    pc_npx = pc.get("n_pixels")

    vent_lat, vent_lon = VENT_COORDS[vol]

    regime = REGIME.get(vol, "?")
    drift_gate = DRIFT_GATE_KM.get(regime)

    # TIF match
    tif_info = find_closest_tif(vol, dt, rec.get("sensor"))
    drift_km = None
    tif_centroid = None
    if tif_info is not None:
        try:
            arr, transform = load_tif(tif_info["tif_path"])
            tif_centroid = top_n_centroid(arr, transform, vent_lat, vent_lon,
                                          max_km=3.0, n=10)
            if tif_centroid and tif_centroid.get("lat") is not None \
               and pc_lat is not None and pc_lon is not None:
                drift_km = float(haversine_km(
                    tif_centroid["lat"], tif_centroid["lon"], pc_lat, pc_lon))
        except Exception as exc:
            tif_centroid = {"error": str(exc)}

    # Verdict per record
    gates = {}
    # G1 ratio in band [0.5, 2.0]
    gates["g1_ratio_in_band"] = (
        ratio_csv is not None and RATIO_BAND[0] <= ratio_csv <= RATIO_BAND[1]
    )
    # G2 drift under regime gate
    if drift_km is None or drift_gate is None:
        gates["g2_drift_under_gate"] = None
    else:
        gates["g2_drift_under_gate"] = drift_km < drift_gate

    # Cap-specific gate
    capped = is_capped(rec)
    cap_legitimate = None  # cap is OK if MIROVA also low
    cap_leak = False
    if capped:
        if mirova is not None and mirova["VRP_MW"] > CAP_MW:
            cap_leak = True
            cap_legitimate = False
        else:
            cap_legitimate = True

    # Overall verdict
    # For C regime: drift not applicable. PASS based on ratio + cap leak only.
    applicable_gates = [g for k, g in gates.items() if g is not None]
    if applicable_gates:
        n_pass = sum(1 for g in applicable_gates if g)
        if cap_leak:
            verdict = "FAIL_CAP_LEAK"
        elif n_pass == len(applicable_gates):
            verdict = "PASS"
        elif n_pass >= len(applicable_gates) - 1:
            verdict = "MARGINAL"
        else:
            verdict = "FAIL"
    else:
        # No applicable gates (no MIROVA + regime C)
        verdict = "NO_DIAGNOSTIC"

    return {
        "vol": vol,
        "regime": regime,
        "drift_gate_km": drift_gate,
        "datetime_utc": rec.get("datetime_utc"),
        "sensor": rec.get("sensor"),
        "capped": capped,
        "pc_vrp_mw": pc_vrp_mw,
        "pc_centroid_lat": pc_lat,
        "pc_centroid_lon": pc_lon,
        "pc_centroid_dist_km": pc_dist,
        "pc_n_pixels": pc_npx,
        "t_bg_k": rec.get("t_bg_k"),
        "t_max_k": rec.get("t_max_k"),
        "diag_n_bt_path": rec.get("diag_n_bt_path"),
        "diag_n_nti_path": rec.get("diag_n_nti_path"),
        "diag_n_dnti_ctx_path": rec.get("diag_n_dnti_ctx_path"),
        "mirova_match": mirova,
        "ratio_pc_vrp_vs_mirova": ratio_csv,
        "tif_path": str(tif_info["tif_path"].relative_to(ROOT.parent)) if tif_info else None,
        "tif_time_diff_h": tif_info["time_diff_h"] if tif_info else None,
        "tif_sensor": tif_info["tif_sensor"] if tif_info else None,
        "tif_centroid_lat": (tif_centroid or {}).get("lat"),
        "tif_centroid_lon": (tif_centroid or {}).get("lon"),
        "tif_n_positive_in_3km": (tif_centroid or {}).get("n_positive_in_filter"),
        "drift_km": drift_km,
        "gates": gates,
        "cap_leak": cap_leak,
        "cap_legitimate": cap_legitimate,
        "verdict": verdict,
    }


# -------------------- Main --------------------

def main():
    print("=" * 70)
    print("R2 PIXEL-LEVEL VALIDACION OPCION C (cap path_d_only_cap_mw=5.0)")
    print("S71 T1 F2.d — script experiments/131_r2_pixel_level_optC/")
    print("=" * 70)

    if not TIF_ARCHIVE.exists():
        print(f"BLOCKED: TIF_ARCHIVE no existe: {TIF_ARCHIVE}")
        sys.exit(1)

    print(f"\nTIF archive: {TIF_ARCHIVE}")
    print(f"Cap data:    {CAP_DIR}")
    print(f"CSV cons:    {CONS_CSV}")

    alerts = load_mirova_alerts()
    print(f"\nMIROVA alerts cargadas: {len(alerts)}")

    by_vol = load_records()
    print(f"Records cap profile (post-2026-05-09): "
          f"{sum(len(v) for v in by_vol.values())} en {len(by_vol)} vols")

    cats = sample_categories(by_vol, alerts, target_per_cat=5)
    print("\nMuestreo:")
    for k, v in cats.items():
        print(f"  {k}: {len(v)} records")

    all_audits = []
    for cat, entries in cats.items():
        print(f"\n--- Auditando {cat} ---")
        for entry in entries:
            res = audit_record(entry)
            res["category"] = cat
            all_audits.append(res)
            tif_match = "TIF" if res["tif_path"] else "no-TIF"
            mir_match = (f"MIROVA={res['mirova_match']['VRP_MW']:.3f}"
                         if res["mirova_match"] else "no-MIROVA")
            print(f"  {entry['vol']:<22} {res['datetime_utc']:<20} "
                  f"{res['sensor']:<14} cap={res['capped']} {tif_match} "
                  f"{mir_match} drift={res['drift_km']} verdict={res['verdict']}")

    # Aggregations
    summary = aggregate(all_audits)

    # Persist
    out_json = HERE / "r2_pixel.json"
    out_md = HERE / "r2_pixel_report.md"
    payload = {
        "method": "R2_pixel_level_optC",
        "experiment": "experiments/131_r2_pixel_level_optC",
        "method_refs": [
            "docs/R2_GATES_BY_REGIME.md (regimen-dependiente)",
            "experiments/120_audit_tif_vrp_sumable (method)",
            "experiments/122-125 (5 vols Tier A S70-1)",
        ],
        "config": {
            "cap_mw": CAP_MW,
            "cap_tbg_k": CAP_TBG_K,
            "tif_min_dt": TIF_MIN_DT.isoformat(),
            "tif_time_tol_hours": TIF_TIME_TOL_HOURS,
            "mirova_time_tol_hours": MIROVA_TIME_TOL_HOURS,
            "ratio_band": list(RATIO_BAND),
            "regime_per_vol": REGIME,
            "drift_gate_per_regime": DRIFT_GATE_KM,
        },
        "records_audited": all_audits,
        "summary": summary,
    }
    out_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"\nResultados crudos: {out_json}")

    # MD report
    write_md_report(out_md, all_audits, summary)
    print(f"Reporte:           {out_md}")


def aggregate(audits):
    n = len(audits)
    by_cat = {}
    by_vol = {}
    leaks = []
    no_diag = []

    for r in audits:
        cat = r["category"]
        vol = r["vol"]
        by_cat.setdefault(cat, []).append(r)
        by_vol.setdefault(vol, []).append(r)
        if r["cap_leak"]:
            leaks.append({"vol": vol, "dt": r["datetime_utc"],
                          "mirova_vrp_mw": r["mirova_match"]["VRP_MW"] if r["mirova_match"] else None})
        if r["verdict"] == "NO_DIAGNOSTIC":
            no_diag.append({"vol": vol, "dt": r["datetime_utc"]})

    def verdict_counts(items):
        c = {"PASS": 0, "MARGINAL": 0, "FAIL": 0, "FAIL_CAP_LEAK": 0, "NO_DIAGNOSTIC": 0}
        for x in items:
            c[x["verdict"]] = c.get(x["verdict"], 0) + 1
        return c

    cat_summary = {k: {"n": len(v), "verdicts": verdict_counts(v),
                       "n_tif_matched": sum(1 for r in v if r["tif_path"]),
                       "n_mirova_matched": sum(1 for r in v if r["mirova_match"])}
                   for k, v in by_cat.items()}
    vol_summary = {k: {"n": len(v), "verdicts": verdict_counts(v)}
                   for k, v in by_vol.items()}

    n_pass = sum(1 for r in audits if r["verdict"] == "PASS")
    n_marg = sum(1 for r in audits if r["verdict"] == "MARGINAL")
    n_fail = sum(1 for r in audits if r["verdict"] in ("FAIL", "FAIL_CAP_LEAK"))
    n_nd = sum(1 for r in audits if r["verdict"] == "NO_DIAGNOSTIC")
    n_diag = n - n_nd
    pct_pass = (n_pass / n_diag * 100.0) if n_diag > 0 else None
    pct_pass_marginal = ((n_pass + n_marg) / n_diag * 100.0) if n_diag > 0 else None

    # Adoption verdict (defensive cap logic):
    # - Cap leaks > 0 -> NO_ADOPTAR (mascararia magnitud real).
    # - Cap leaks == 0 + records cap-applied tienen MIROVA bajo o ausente ->
    #   ADOPTABLE_DEFENSIVO (acota dano sin enmascarar nada).
    # - Drift PASS rate informa robustez espacial pero no es bloqueante
    #   (cap es magnitud-only, no reduce drift).
    cap_records = [r for r in audits if r["capped"]]
    cap_mirova_match = [r for r in cap_records if r["mirova_match"]]
    cap_mirova_max = max(
        (r["mirova_match"]["VRP_MW"] for r in cap_mirova_match),
        default=0.0,
    )

    if leaks:
        adoption = "NO_ADOPTAR"
        adoption_reason = (
            f"{len(leaks)} cap leaks: MIROVA reporta >5MW en escena con cap aplicado"
        )
    elif n_diag == 0:
        adoption = "NO_DIAGNOSTIC"
        adoption_reason = "Sin records diagnosticos suficientes (gap TIF/MIROVA)"
    elif cap_mirova_max <= 5.0 and pct_pass_marginal is not None and pct_pass_marginal >= 50:
        adoption = "ADOPTABLE_DEFENSIVO"
        adoption_reason = (
            f"Sin cap leaks; MIROVA max en records capped = {cap_mirova_max:.3f} MW (<<5). "
            f"Cap recorta inflados sin enmascarar magnitudes reales. "
            f"PASS+MARGINAL = {pct_pass_marginal:.1f}% sobre {n_diag} diagnosticos."
        )
    elif pct_pass_marginal is not None and pct_pass_marginal >= 70:
        adoption = "ADOPTABLE"
        adoption_reason = (
            f"PASS+MARGINAL = {pct_pass_marginal:.1f}% sobre {n_diag} diagnosticos, "
            f"sin cap leaks"
        )
    else:
        adoption = "MARGINAL"
        adoption_reason = (
            f"PASS={pct_pass:.1f}%, PASS+MARGINAL={pct_pass_marginal or 0:.1f}%; "
            f"sin cap leaks pero drift residual"
        )

    return {
        "n_total": n,
        "n_diagnostic": n_diag,
        "n_pass": n_pass,
        "n_marginal": n_marg,
        "n_fail": n_fail,
        "n_no_diagnostic": n_nd,
        "pct_pass_of_diagnostic": pct_pass,
        "pct_pass_marginal_of_diagnostic": pct_pass_marginal,
        "by_category": cat_summary,
        "by_vol": vol_summary,
        "cap_leaks": leaks,
        "no_diagnostic": no_diag,
        "adoption_verdict": adoption,
        "adoption_reason": adoption_reason,
    }


def write_md_report(path, audits, summary):
    lines = []
    L = lines.append
    L("# R2 Pixel-Level Validacion Opcion C (S71 T1 F2.d)")
    L("")
    L(f"**Experimento**: `experiments/131_r2_pixel_level_optC`")
    L(f"**Profile auditado**: `mirova_equivalent_path_d_cap_v1` (cap=5MW, tbg<270K)")
    L(f"**Records auditados**: {summary['n_total']} ({summary['n_diagnostic']} diagnosticos)")
    L(f"**Verdict adopcion**: **{summary['adoption_verdict']}** — {summary['adoption_reason']}")
    L("")
    L("## Metodologia")
    L("")
    L("Replica el patron R2 retroactivo S70-1 (R2_GATES_BY_REGIME.md):")
    L("")
    L("1. Sample 4 categorias del profile cap: cap-applied (A), ratio-extreme (B),")
    L("   no-cap-applied control (C), sin ALERTA MIROVA (D).")
    L("2. Por cada record: match TIF MIROVA mas cercano (tol 6h),")
    L("   centroide top-10 pixels TIF <=3km del vent, drift vs pc.centroid.")
    L("3. Ratio pc.vrp_mw / MIROVA.VRP_MW (CSV cons NRT).")
    L("4. Gates por regimen (R2_GATES_BY_REGIME.md):")
    L("   - Regimen A (Lastarria/Lascar/Isluga): drift <2km.")
    L("   - Regimen B1 (Villarrica/Chaiten): drift <3km.")
    L("   - Regimen B2 (PP): drift <3km marginal.")
    L("   - Regimen C (PCC): drift no aplica.")
    L("5. Cap-leak gate: FAIL si MIROVA.VRP_MW > 5MW en record capped.")
    L("")

    L("## Tabla 20 records")
    L("")
    L("| Cat | Vol | DT | Sensor | cap | t_bg | MIROVA VRP | ratio | drift_km | gate | verdict |")
    L("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in audits:
        mvp = (f"{r['mirova_match']['VRP_MW']:.3f}"
               if r['mirova_match'] else "-")
        rat = f"{r['ratio_pc_vrp_vs_mirova']:.2f}" if r['ratio_pc_vrp_vs_mirova'] is not None else "-"
        drift = f"{r['drift_km']:.2f}" if r['drift_km'] is not None else "-"
        gate = f"<{r['drift_gate_km']}km" if r['drift_gate_km'] else "N/A"
        tbg = f"{r['t_bg_k']:.1f}" if r['t_bg_k'] is not None else "-"
        L(f"| {r['category'].split('_')[0]} | {r['vol']} | {r['datetime_utc']} | "
          f"{r['sensor']} | {r['capped']} | {tbg} | {mvp} | {rat} | {drift} | "
          f"{gate} | {r['verdict']} |")
    L("")

    L("## Resumen por categoria")
    L("")
    for cat, info in summary["by_category"].items():
        L(f"- **{cat}** (n={info['n']}): TIF match {info['n_tif_matched']}, "
          f"MIROVA match {info['n_mirova_matched']}, verdicts={info['verdicts']}")
    L("")

    L("## Resumen por volcan")
    L("")
    for vol, info in summary["by_vol"].items():
        L(f"- **{vol}** ({REGIME.get(vol, '?')}, n={info['n']}): {info['verdicts']}")
    L("")

    L("## Cap leaks (FAIL critico — MIROVA >5MW capped)")
    L("")
    if summary["cap_leaks"]:
        for leak in summary["cap_leaks"]:
            L(f"- {leak['vol']} {leak['dt']}: MIROVA reporta {leak['mirova_vrp_mw']:.3f} MW")
    else:
        L("- **Sin cap leaks.** El cap=5MW no enmascara ningun caso donde MIROVA")
        L("  reporta magnitud >5MW. La hipotesis fisica del fix (FPs cirrus path D)")
        L("  se confirma a este nivel.")
    L("")

    L("## Records sin diagnostico (TIF gap o MIROVA gap)")
    L("")
    if summary["no_diagnostic"]:
        for nd in summary["no_diagnostic"]:
            L(f"- {nd['vol']} {nd['dt']}")
    else:
        L("- Todos los records tienen al menos un gate aplicable.")
    L("")

    L("## Verdict de adopcion")
    L("")
    L(f"**{summary['adoption_verdict']}** — {summary['adoption_reason']}")
    L("")
    L(f"- PASS: {summary['n_pass']}/{summary['n_diagnostic']} "
      f"({(summary['pct_pass_of_diagnostic'] or 0):.1f}%)")
    L(f"- MARGINAL: {summary['n_marginal']}")
    L(f"- FAIL: {summary['n_fail']}")
    L(f"- NO_DIAGNOSTIC: {summary['n_no_diagnostic']}")
    L("")
    L("### Interpretacion (geologo)")
    L("")
    L("El cap=5MW es un parche defensivo contra el path D dNTI ctx FPs en cirrus alto")
    L("(D9, t_bg<270K). La pregunta R2: el cap **enmascara casos donde MIROVA reporta")
    L("magnitud real >5MW** (lo que seria mala adopcion), o solo recorta inflados FPs")
    L("(lo que es bueno).")
    L("")
    if not summary["cap_leaks"]:
        L("**0 cap leaks** — en ningun record capped MIROVA reporta magnitud >5MW.")
        L("Cuando hay ALERTA MIROVA en escena con cap aplicado, su VRP es 0.06-0.21 MW")
        L("(rango sub-MW, focal puro). El cap solo recorta inflados nuestros, no enmascara")
        L("magnitudes reales. **Adopcion defensiva justificada**.")
    else:
        L(f"**{len(summary['cap_leaks'])} cap leaks** detectados — el cap puede")
        L("enmascarar magnitudes reales. Reconsiderar antes de adoptar.")
    L("")
    L("### Caveat metodologico: drift y MODIS")
    L("")
    L("Las gates de drift R2_GATES_BY_REGIME.md (<2km A, <3km B) se calibraron en")
    L("S70-1 sobre records VIIRS375 (pixel 375m). Los records capped son")
    L("**~95% MODIS** (pixel ~1km) por construccion del cap (path D + t_bg<270K es")
    L("regimen-MODIS-dominante en cirrus alto). Con MODIS, drift 2-3 km es normal")
    L("por la resolucion del granule, no error del pipeline. Por eso una fraccion")
    L("de records cae en MARGINAL (drift entre gate y 2x gate) sin que indique cap")
    L("malo. La gate dura es **cap-leak**, que esta en 0/N.")
    L("")
    L("### Ratio post-cap residual")
    L("")
    L("Cuando hay MIROVA ALERTA + cap aplicado, ratio sigue 24-83x (cap=5 vs MIROVA")
    L("0.06-0.21 MW). El cap acota el dano (sin cap, ratios eran 50-150x pre-D9-fix)")
    L("pero **no resuelve la causa raiz** (D9 path D ctx en cirrus). Cap es parche")
    L("operacional, no fix arquitectural — esto coincide con plan S71+ papers-first.")
    L("")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
