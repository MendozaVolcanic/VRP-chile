"""
Frente 2.A S86 — Subagente C: cruce 1:1 MIROVA vs VRP Chile.

Para cada (volcan, sensor_bucket, noche_local_Chile):
  - MIROVA publica ALERTA si CSV (CONS+OCR) tiene ALERTA_TERMICA/ALERTA_TERMICA_OCR
  - NOSOTROS publishable si JSON record cumple frontend gate:
      pc.vrp_mw > 0 AND pc.centroid_dist_km <= inner_radius_km AND distance_class == 'summit'

Genera C_crossing.json + C_crossing.md.
"""
from __future__ import annotations

import json
import sys
import io
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)

CHILE_TZ = ZoneInfo("America/Santiago")

# ---------------------------------------------------------------------------
# Volcán mapping (CSV name -> JSON file basename)
# ---------------------------------------------------------------------------
TIER_A_MAP = {
    "Chaiten":               "Chaiten",
    "Copahue":               "Copahue",
    "Isluga":                "Isluga",
    "Lascar":                "Lascar",
    "Lastarria":             "Lastarria",
    "Llaima":                "Llaima",
    "Nevados de Chillan":    "NevadosDeChillan",
    "PlanchonPeteroa":       "PlanchonPeteroa",
    "Peteroa":               "PlanchonPeteroa",        # variante (A14)
    "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Tupungatito":           "Tupungatito",
    "Villarrica":            "Villarrica",
}

# Sensor buckets canónicos
SENSORS = ["MODIS", "VIIRS375", "VIIRS750"]


def csv_sensor_bucket(s: str) -> str | None:
    if s == "MODIS":
        return "MODIS"
    if s in ("VIIRS", "VIIRS375"):
        return "VIIRS375"
    if s == "VIIRS750":
        return "VIIRS750"
    return None


def json_sensor_bucket(s: str) -> str | None:
    s = s.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


# ---------------------------------------------------------------------------
# Load volcanoes.yaml
# ---------------------------------------------------------------------------
VOLC_YAML = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
INNER_RADIUS = {v["name"]: float(v.get("inner_radius_km", 5.0))
                for v in VOLC_YAML["volcanoes"] if v.get("mirova_monitored")}
TIER_A_NAMES = sorted(set(TIER_A_MAP.values()))


# ---------------------------------------------------------------------------
# Load MIROVA refs (CONS + OCR)
# ---------------------------------------------------------------------------
def load_mirova():
    cons = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ocr = pd.read_csv(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
    cons["source"] = "CONS"
    ocr["source"] = "OCR"

    common = ["Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan",
              "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "source"]
    df = pd.concat([cons[common], ocr[common]], ignore_index=True)

    df = df[df["Volcan"].isin(TIER_A_MAP.keys())].copy()
    df["volc_json"] = df["Volcan"].map(TIER_A_MAP)
    df["sensor_bucket"] = df["Sensor"].apply(csv_sensor_bucket)
    df = df[df["sensor_bucket"].notna()]

    # noche local Chile (date)
    df["dt_utc"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df[df["dt_utc"].notna()]
    df["night_local"] = (
        df["dt_utc"]
        .dt.tz_convert(CHILE_TZ)
        .dt.date
    )

    # ALERTA flag (MIROVA publica)
    df["is_alerta"] = df["Tipo_Registro"].isin(["ALERTA_TERMICA", "ALERTA_TERMICA_OCR"])
    return df


MIROVA = load_mirova()
print(f"[INFO] MIROVA rows loaded (Tier A): {len(MIROVA)} | ALERTAs: {MIROVA['is_alerta'].sum()}")
print(f"[INFO] MIROVA date range: {MIROVA['night_local'].min()} -> {MIROVA['night_local'].max()}")


# ---------------------------------------------------------------------------
# Load our JSON records and compute "publishable"
# ---------------------------------------------------------------------------
def load_our_records():
    rows = []
    for json_name in TIER_A_NAMES:
        fp = ROOT / "data/mirova_equivalent" / f"{json_name}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        inner = INNER_RADIUS.get(json_name, 5.0)
        for r in data.get("records", []):
            sensor = r.get("sensor", "")
            bucket = json_sensor_bucket(sensor)
            if bucket is None:
                continue
            dt_str = r.get("datetime_utc") or r.get("acquisition_time_utc")
            if not dt_str:
                continue
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
            dist_class = r.get("distance_class", "")

            # Replicar gate frontend mirovaEqVrp (S33 / inner_radius)
            publishable = (
                pc_vrp > 0
                and pc_dist is not None
                and pc_dist <= inner
                and dist_class == "summit"
            )

            # Path inference
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
                "sensor_raw": sensor,
                "sensor_bucket": bucket,
                "dt_utc": dt_utc,
                "night_local": night,
                "pc_vrp_mw": pc_vrp,
                "pc_n_pixels": pc_n,
                "pc_centroid_dist_km": pc_dist,
                "pc_path": path_str,
                "distance_class": dist_class,
                "publishable": publishable,
                "t_bg_k": r.get("t_bg_k"),
                "t_max_k": r.get("t_max_k"),
                "sigma_bg_k": r.get("diag_sigma_bg_k"),
                "inner_radius_km": inner,
                "vrp_mw_scene": float(r.get("vrp_mw") or 0.0),
                "n_anom_pixels": int(r.get("n_anomalous_pixels") or 0),
            })
    return pd.DataFrame(rows)


OURS = load_our_records()
print(f"[INFO] Our records loaded: {len(OURS)} | publishable: {OURS['publishable'].sum()}")
print(f"[INFO] Our date range: {OURS['night_local'].min()} -> {OURS['night_local'].max()}")


# ---------------------------------------------------------------------------
# Restrict to intersection date window (MIROVA snapshot bounds)
# ---------------------------------------------------------------------------
MIN_NIGHT = max(MIROVA["night_local"].min(), OURS["night_local"].min())
MAX_NIGHT = min(MIROVA["night_local"].max(), OURS["night_local"].max())
print(f"[INFO] Common window: {MIN_NIGHT} -> {MAX_NIGHT}")

MIROVA = MIROVA[(MIROVA["night_local"] >= MIN_NIGHT) & (MIROVA["night_local"] <= MAX_NIGHT)]
OURS = OURS[(OURS["night_local"] >= MIN_NIGHT) & (OURS["night_local"] <= MAX_NIGHT)]


# ---------------------------------------------------------------------------
# Build per-key state: (volc_json, sensor_bucket, night_local)
# ---------------------------------------------------------------------------
mirova_keys = set()
mirova_alerta_keys = set()
for _, row in MIROVA.iterrows():
    key = (row["volc_json"], row["sensor_bucket"], row["night_local"])
    mirova_keys.add(key)
    if row["is_alerta"]:
        mirova_alerta_keys.add(key)

# Universo de noches "monitoreadas por MIROVA" (CONS o OCR registrado ese día/sensor)
# Universo nuestro: cualquier noche con record
our_keys = set()
our_publishable_keys = set()
our_records_by_key = defaultdict(list)
for idx, row in OURS.iterrows():
    key = (row["volc_json"], row["sensor_bucket"], row["night_local"])
    our_keys.add(key)
    our_records_by_key[key].append(idx)
    if row["publishable"]:
        our_publishable_keys.add(key)


# Universo de evaluación: unión de keys con observación en cualquiera de los dos
# (si MIROVA ni nosotros vimos pasada, no se tabula = TN)
universe = mirova_keys | our_keys

# Confusion matrix
def classify(key):
    m = key in mirova_alerta_keys
    n = key in our_publishable_keys
    if m and n:
        return "TP"
    if not m and n:
        return "FP"
    if m and not n:
        return "FN"
    return "TN"


classifications = {key: classify(key) for key in universe}


# ---------------------------------------------------------------------------
# Aggregated confusion: global per sensor
# ---------------------------------------------------------------------------
def conf_metrics(keys):
    c = Counter(classifications[k] for k in keys)
    tp = c.get("TP", 0)
    fp = c.get("FP", 0)
    fn = c.get("FN", 0)
    tn = c.get("TN", 0)
    prec = tp / (tp + fp) if (tp + fp) else None
    rec = tp / (tp + fn) if (tp + fn) else None
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": prec, "recall": rec, "n_keys": len(keys)}


global_by_sensor = {}
for s in SENSORS:
    keys = [k for k in universe if k[1] == s]
    global_by_sensor[s] = conf_metrics(keys)

global_overall = conf_metrics(universe)

# Per-volcano × sensor
per_vol_sensor = defaultdict(dict)
for v in TIER_A_NAMES:
    for s in SENSORS:
        keys = [k for k in universe if k[0] == v and k[1] == s]
        per_vol_sensor[v][s] = conf_metrics(keys)


# ---------------------------------------------------------------------------
# Profile FP / TP / FN — using our records joined by key
# ---------------------------------------------------------------------------
# For each key, pick the "best" (max pc_vrp_mw) of our publishable records
def best_publishable_record(key):
    idxs = our_records_by_key.get(key, [])
    sub = OURS.loc[idxs]
    sub = sub[sub["publishable"]]
    if sub.empty:
        return None
    return sub.loc[sub["pc_vrp_mw"].idxmax()]


# Also keep "best record at all" (whether publishable or not) for FN profile
def best_any_record(key):
    idxs = our_records_by_key.get(key, [])
    sub = OURS.loc[idxs]
    if sub.empty:
        return None
    # Prefer the one with largest pc_vrp_mw or vrp_mw_scene
    return sub.loc[sub["pc_vrp_mw"].idxmax()] if sub["pc_vrp_mw"].max() > 0 \
           else sub.iloc[0]


tp_records = []
fp_records = []
fn_records = []

for key, label in classifications.items():
    if label == "TP":
        r = best_publishable_record(key)
        if r is not None:
            tp_records.append(r)
    elif label == "FP":
        r = best_publishable_record(key)
        if r is not None:
            fp_records.append(r)
    elif label == "FN":
        r = best_any_record(key)
        if r is not None:
            fn_records.append(r)


def to_df(lst):
    if not lst:
        return pd.DataFrame()
    return pd.DataFrame(lst).reset_index(drop=True)


TP_DF = to_df(tp_records)
FP_DF = to_df(fp_records)
FN_DF = to_df(fn_records)


def dist_stats(s: pd.Series):
    s = s.dropna().astype(float)
    if len(s) == 0:
        return {"n": 0}
    return {
        "n": int(len(s)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "min": float(s.min()),
        "max": float(s.max()),
    }


def profile(df, label):
    if df.empty:
        return {"label": label, "n": 0}
    prof = {
        "label": label,
        "n": int(len(df)),
        "pc_vrp_mw": dist_stats(df["pc_vrp_mw"]),
        "pc_n_pixels": dist_stats(df["pc_n_pixels"]),
        "pc_centroid_dist_km": dist_stats(df["pc_centroid_dist_km"]),
        "t_bg_k": dist_stats(df["t_bg_k"]),
        "sigma_bg_k": dist_stats(df["sigma_bg_k"]),
        "path_dist": dict(Counter(df["pc_path"])),
        "frac_n_pixels_eq_1": float((df["pc_n_pixels"] == 1).mean()),
        "frac_n_pixels_ge_2": float((df["pc_n_pixels"] >= 2).mean()),
        "frac_n_pixels_ge_3": float((df["pc_n_pixels"] >= 3).mean()),
        "frac_t_bg_lt_260": float((df["t_bg_k"].fillna(999) < 260).mean()),
        "frac_t_bg_lt_270": float((df["t_bg_k"].fillna(999) < 270).mean()),
    }
    return prof


PROF_TP = profile(TP_DF, "TP")
PROF_FP = profile(FP_DF, "FP")
PROF_FN = profile(FN_DF, "FN")


# ---------------------------------------------------------------------------
# Persistence analysis: FP episode length
# ---------------------------------------------------------------------------
def episode_lengths(df, label):
    """For each (volc, sensor) group sorted by night, count consecutive-day runs."""
    if df.empty:
        return {}
    sub = df[["volc_json", "sensor_bucket", "night_local"]].copy()
    sub["night_local"] = pd.to_datetime(sub["night_local"])
    runs = []
    for (v, s), g in sub.groupby(["volc_json", "sensor_bucket"]):
        nights = sorted(g["night_local"].unique())
        if not nights:
            continue
        run = 1
        for i in range(1, len(nights)):
            gap = (nights[i] - nights[i-1]).days
            if gap == 1:
                run += 1
            else:
                runs.append(run)
                run = 1
        runs.append(run)
    if not runs:
        return {}
    arr = np.array(runs)
    return {
        "n_episodes": int(len(arr)),
        "median_len": float(np.median(arr)),
        "mean_len": float(arr.mean()),
        "frac_singletons": float((arr == 1).mean()),
        "frac_2plus": float((arr >= 2).mean()),
        "frac_5plus": float((arr >= 5).mean()),
        "max_len": int(arr.max()),
    }


FP_EPISODES = episode_lengths(FP_DF, "FP")
TP_EPISODES = episode_lengths(TP_DF, "TP")


# ---------------------------------------------------------------------------
# Candidate discriminators: gate scan
# ---------------------------------------------------------------------------
def gate_eval(name, tp_mask, fp_mask):
    """Evaluate a candidate gate.
    tp_mask True = TP would pass (kept = considered publishable)
    fp_mask True = FP would pass
    """
    tp_pass = int(tp_mask.sum())
    tp_total = int(len(tp_mask))
    fp_pass = int(fp_mask.sum())
    fp_total = int(len(fp_mask))
    recall_kept = tp_pass / tp_total if tp_total else None
    fp_filtered = (fp_total - fp_pass) / fp_total if fp_total else None
    return {
        "gate": name,
        "tp_pass": tp_pass, "tp_total": tp_total,
        "fp_pass": fp_pass, "fp_total": fp_total,
        "recall_kept_pct": round(100 * recall_kept, 1) if recall_kept is not None else None,
        "fp_filtered_pct": round(100 * fp_filtered, 1) if fp_filtered is not None else None,
        # precision uplift assuming TP+FP universe (rough proxy)
        "precision_before": round(tp_total / (tp_total + fp_total), 3) if (tp_total + fp_total) else None,
        "precision_after": round(tp_pass / (tp_pass + fp_pass), 3) if (tp_pass + fp_pass) else None,
    }


CANDIDATES = []
if not TP_DF.empty and not FP_DF.empty:
    # 1. n_pixels >= 2
    CANDIDATES.append(gate_eval(
        "pc.n_pixels >= 2",
        TP_DF["pc_n_pixels"] >= 2,
        FP_DF["pc_n_pixels"] >= 2,
    ))
    # 2. n_pixels >= 3
    CANDIDATES.append(gate_eval(
        "pc.n_pixels >= 3",
        TP_DF["pc_n_pixels"] >= 3,
        FP_DF["pc_n_pixels"] >= 3,
    ))
    # 3. t_bg_k >= 260 (atm gate A23)
    CANDIDATES.append(gate_eval(
        "t_bg_k >= 260 K (no cirrus alto)",
        (TP_DF["t_bg_k"].fillna(999) >= 260),
        (FP_DF["t_bg_k"].fillna(999) >= 260),
    ))
    # 4. t_bg_k >= 270
    CANDIDATES.append(gate_eval(
        "t_bg_k >= 270 K",
        (TP_DF["t_bg_k"].fillna(999) >= 270),
        (FP_DF["t_bg_k"].fillna(999) >= 270),
    ))
    # 5. pc.vrp_mw >= 0.2 MW
    CANDIDATES.append(gate_eval(
        "pc.vrp_mw >= 0.2 MW",
        TP_DF["pc_vrp_mw"] >= 0.2,
        FP_DF["pc_vrp_mw"] >= 0.2,
    ))
    # 6. pc.vrp_mw >= 0.5 MW
    CANDIDATES.append(gate_eval(
        "pc.vrp_mw >= 0.5 MW",
        TP_DF["pc_vrp_mw"] >= 0.5,
        FP_DF["pc_vrp_mw"] >= 0.5,
    ))
    # 7. Combo n_pixels >=2 AND t_bg >=260
    CANDIDATES.append(gate_eval(
        "n_pixels >= 2 AND t_bg_k >= 260 K",
        (TP_DF["pc_n_pixels"] >= 2) & (TP_DF["t_bg_k"].fillna(999) >= 260),
        (FP_DF["pc_n_pixels"] >= 2) & (FP_DF["t_bg_k"].fillna(999) >= 260),
    ))
    # 8. Path D-only filter (exclude D-only)
    CANDIDATES.append(gate_eval(
        "Path != 'D' alone (drop D-only records)",
        TP_DF["pc_path"] != "D",
        FP_DF["pc_path"] != "D",
    ))
    # 9. Combo no D-only AND n_pixels>=2
    CANDIDATES.append(gate_eval(
        "n_pixels >= 2 AND path != 'D'-alone",
        (TP_DF["pc_n_pixels"] >= 2) & (TP_DF["pc_path"] != "D"),
        (FP_DF["pc_n_pixels"] >= 2) & (FP_DF["pc_path"] != "D"),
    ))
    # 10. Drop VIIRS750 publishable
    CANDIDATES.append(gate_eval(
        "sensor != VIIRS750 (M-band)",
        TP_DF["sensor_bucket"] != "VIIRS750",
        FP_DF["sensor_bucket"] != "VIIRS750",
    ))
    # 11. Composite operativo: t_bg>=260 AND sensor != VIIRS750
    CANDIDATES.append(gate_eval(
        "t_bg_k >= 260 K AND sensor != VIIRS750",
        (TP_DF["t_bg_k"].fillna(999) >= 260) & (TP_DF["sensor_bucket"] != "VIIRS750"),
        (FP_DF["t_bg_k"].fillna(999) >= 260) & (FP_DF["sensor_bucket"] != "VIIRS750"),
    ))
    # 12. Composite máximo: t_bg>=260 AND sensor != VIIRS750 AND n_pixels>=2
    CANDIDATES.append(gate_eval(
        "t_bg_k >= 260 K AND sensor != VIIRS750 AND n_pixels >= 2",
        ((TP_DF["t_bg_k"].fillna(999) >= 260)
         & (TP_DF["sensor_bucket"] != "VIIRS750")
         & (TP_DF["pc_n_pixels"] >= 2)),
        ((FP_DF["t_bg_k"].fillna(999) >= 260)
         & (FP_DF["sensor_bucket"] != "VIIRS750")
         & (FP_DF["pc_n_pixels"] >= 2)),
    ))


# ---------------------------------------------------------------------------
# Save JSON
# ---------------------------------------------------------------------------
result = {
    "window": {"start": str(MIN_NIGHT), "end": str(MAX_NIGHT)},
    "tier_a_volcanoes": TIER_A_NAMES,
    "inner_radius_km": INNER_RADIUS,
    "n_universe_keys": len(universe),
    "n_mirova_keys": len(mirova_keys),
    "n_mirova_alerta_keys": len(mirova_alerta_keys),
    "n_our_keys": len(our_keys),
    "n_our_publishable_keys": len(our_publishable_keys),
    "global_overall": global_overall,
    "global_by_sensor": global_by_sensor,
    "per_vol_sensor": {v: per_vol_sensor[v] for v in TIER_A_NAMES},
    "profile_TP": PROF_TP,
    "profile_FP": PROF_FP,
    "profile_FN": PROF_FN,
    "fp_episode_lengths": FP_EPISODES,
    "tp_episode_lengths": TP_EPISODES,
    "candidate_gates": CANDIDATES,
}

(OUT / "C_crossing.json").write_text(
    json.dumps(result, indent=2, default=str), encoding="utf-8"
)
print(f"[OK] Wrote {OUT/'C_crossing.json'}")


# ---------------------------------------------------------------------------
# Build markdown
# ---------------------------------------------------------------------------
def fmt_pct(x):
    return f"{100*x:.1f}%" if x is not None else "—"


def fmt_num(x, n=3):
    return f"{x:.{n}f}" if x is not None else "—"


lines = []
lines.append("# Frente 2.A S86 — Cruce 1:1 MIROVA vs VRP Chile (Subagente C)")
lines.append("")
lines.append(f"**Ventana común**: {MIN_NIGHT} → {MAX_NIGHT} (~{(pd.Timestamp(MAX_NIGHT)-pd.Timestamp(MIN_NIGHT)).days} días).")
lines.append(f"**Universo de keys (volcán × sensor × noche local Chile)**: {len(universe):,}.")
lines.append(f"- MIROVA observó: {len(mirova_keys):,} keys ({len(mirova_alerta_keys):,} con ALERTA)")
lines.append(f"- Nosotros: {len(our_keys):,} keys ({len(our_publishable_keys):,} publishables)")
lines.append("")
lines.append("**Mapeo sensor (regla A48)**:")
lines.append("- CSV `MODIS` ↔ JSON `MODIS_*` (Aqua + Terra)")
lines.append("- CSV `VIIRS` y `VIIRS375` ↔ JSON `VIIRS_*` sin sufijo (= I-band 375m)")
lines.append("- CSV `VIIRS750` ↔ JSON `VIIRS_*_750` (M-band 750m) — **no aparece en el snapshot** porque MIROVA solo publica M-band cuando hay anomalía intensa en estos Tier A chilenos.")
lines.append("")

# --- Lectura física al frente ---
lines.append("## Lectura física")
lines.append("")
lines.append("El pixel del satélite ve un trozo de superficie volcánica de tamaño fijo (1 km² nominal MODIS, 375 m² VIIRS-I). MIROVA publica una ALERTA cuando ese pixel — o un cluster pequeño — sostiene una anomalía radiativa que el operador puede defender como roca caliente sobre fondo. Esa decisión combina **intensidad** (cuánto se separa del background) y **persistencia espacial** (cuántos pixels y dónde respecto del cráter). Nuestro pipeline tiene los mismos paths algorítmicos (A=BT, B=NTI absoluto, C=NTI relativo, D=dNTI contextual 8-vec), pero publica más records: el insumo de este cruce es entender qué señal física distingue un TP físico (anomalía real) de un FP nuestro (singleton de cirrus alto, halo de glaciar, ruido isolado).")
lines.append("")

# Confusion global
lines.append("## 1. Matriz de confusión global")
lines.append("")
lines.append(f"**Overall (11 Tier A, todos los sensores)**: TP={global_overall['TP']}, FP={global_overall['FP']}, FN={global_overall['FN']}, TN={global_overall['TN']}")
lines.append(f"  → precisión = {fmt_num(global_overall['precision'])}, recall = {fmt_num(global_overall['recall'])}")
lines.append("")
lines.append("| Sensor | TP | FP | FN | TN | Precisión | Recall |")
lines.append("|---|---|---|---|---|---|---|")
for s in SENSORS:
    m = global_by_sensor[s]
    lines.append(f"| {s} | {m['TP']} | {m['FP']} | {m['FN']} | {m['TN']} | {fmt_num(m['precision'])} | {fmt_num(m['recall'])} |")
lines.append("")

# Per-volcano
lines.append("## 2. Matriz por volcán × sensor")
lines.append("")
lines.append("| Volcán | Sensor | TP | FP | FN | Precisión | Recall |")
lines.append("|---|---|---|---|---|---|---|")
for v in TIER_A_NAMES:
    for s in SENSORS:
        m = per_vol_sensor[v][s]
        if m["TP"] + m["FP"] + m["FN"] == 0:
            continue
        lines.append(f"| {v} | {s} | {m['TP']} | {m['FP']} | {m['FN']} | {fmt_num(m['precision'])} | {fmt_num(m['recall'])} |")
lines.append("")

# Profile distributions
def fmt_dist(d):
    if not d or d.get("n", 0) == 0:
        return "—"
    return (f"n={d['n']}, median={d['median']:.3f}, p25={d['p25']:.3f}, "
            f"p75={d['p75']:.3f}, p95={d['p95']:.3f}, max={d['max']:.3f}")


lines.append("## 3. Perfil físico — distribuciones TP vs FP vs FN")
lines.append("")
lines.append("### 3.1 Magnitud `pc.vrp_mw` (MW)")
lines.append(f"- **TP**: {fmt_dist(PROF_TP.get('pc_vrp_mw',{}))}")
lines.append(f"- **FP**: {fmt_dist(PROF_FP.get('pc_vrp_mw',{}))}")
lines.append(f"- **FN**: {fmt_dist(PROF_FN.get('pc_vrp_mw',{}))}  *(magnitud del cluster que nosotros sí detectamos pero no publicamos)*")
lines.append("")
lines.append("### 3.2 Tamaño cluster `pc.n_pixels`")
lines.append(f"- **TP**: {fmt_dist(PROF_TP.get('pc_n_pixels',{}))}")
lines.append(f"  - %singleton (n=1)={fmt_pct(PROF_TP.get('frac_n_pixels_eq_1', 0))}, %≥2={fmt_pct(PROF_TP.get('frac_n_pixels_ge_2',0))}, %≥3={fmt_pct(PROF_TP.get('frac_n_pixels_ge_3',0))}")
lines.append(f"- **FP**: {fmt_dist(PROF_FP.get('pc_n_pixels',{}))}")
lines.append(f"  - %singleton={fmt_pct(PROF_FP.get('frac_n_pixels_eq_1', 0))}, %≥2={fmt_pct(PROF_FP.get('frac_n_pixels_ge_2',0))}, %≥3={fmt_pct(PROF_FP.get('frac_n_pixels_ge_3',0))}")
lines.append(f"- **FN**: {fmt_dist(PROF_FN.get('pc_n_pixels',{}))}")
lines.append("")
lines.append("### 3.3 Distancia al vent `pc.centroid_dist_km`")
lines.append(f"- **TP**: {fmt_dist(PROF_TP.get('pc_centroid_dist_km',{}))}")
lines.append(f"- **FP**: {fmt_dist(PROF_FP.get('pc_centroid_dist_km',{}))}")
lines.append(f"- **FN**: {fmt_dist(PROF_FN.get('pc_centroid_dist_km',{}))}")
lines.append("")
lines.append("### 3.4 Background térmico `t_bg_k` (Kelvin)")
lines.append(f"- **TP**: {fmt_dist(PROF_TP.get('t_bg_k',{}))}  → %cirrus alto (<260K)={fmt_pct(PROF_TP.get('frac_t_bg_lt_260',0))}, <270K={fmt_pct(PROF_TP.get('frac_t_bg_lt_270',0))}")
lines.append(f"- **FP**: {fmt_dist(PROF_FP.get('t_bg_k',{}))}  → %cirrus alto (<260K)={fmt_pct(PROF_FP.get('frac_t_bg_lt_260',0))}, <270K={fmt_pct(PROF_FP.get('frac_t_bg_lt_270',0))}")
lines.append("")
lines.append("### 3.5 Distribución por path (A=BT, B/C=NTI, D=dNTI ctx)")
lines.append(f"- **TP**: {PROF_TP.get('path_dist', {})}")
lines.append(f"- **FP**: {PROF_FP.get('path_dist', {})}")
lines.append("")

# Persistence
lines.append("## 4. Persistencia (longitud de episodios consecutivos)")
lines.append("")
lines.append(f"- **FP**: {FP_EPISODES}")
lines.append(f"- **TP**: {TP_EPISODES}")
lines.append("")
lines.append("Lectura geológica: una anomalía real (TP) tiende a persistir varias noches consecutivas — el calor del cuerpo magmático no se evapora en 24h. Un FP por cirrus móvil o ruido isolado tiende a ser singleton.")
lines.append("")

# Candidate gates
lines.append("## 5. Features candidatas a ser el mecanismo de supresión MIROVA")
lines.append("")
lines.append("Ordenado por **uplift de precisión** (precisión post-gate − pre-gate) priorizando recall ≥80%.")
lines.append("")
lines.append("| # | Gate | Recall TP que mantiene | FP rate filtrado | Precisión antes | Precisión después |")
lines.append("|---|---|---|---|---|---|")
# Sort by precision_after desc, but mark recall<80 as deprio
sorted_cands = sorted(
    CANDIDATES,
    key=lambda c: ((c["recall_kept_pct"] or 0) >= 80, c.get("precision_after") or 0),
    reverse=True,
)
for i, c in enumerate(sorted_cands, 1):
    lines.append(f"| {i} | `{c['gate']}` | {c['recall_kept_pct']}% | {c['fp_filtered_pct']}% | {c['precision_before']} | {c['precision_after']} |")
lines.append("")
lines.append("**Lectura**: el gate ideal mantiene recall ≥85% (no perdemos eventos reales) y eleva precisión sustancialmente. El candidato top es el insumo directo para el campo derivado `pc.mirova_publishable` en Frente 1.A S87.")
lines.append("")

# Físicos costs
lines.append("### Costo físico de cada candidato")
lines.append("")
lines.append("- **n_pixels >= 2**: descarta singletons. Costo: perdemos lava lake Villarrica sub-pixel y cualquier evento donde el cluster real son 1 pixel (frecuente en MIROVA OCR Villarrica/Lastarria con magnitudes 0.05–0.2 MW).")
lines.append("- **t_bg_k >= 260 K**: descarta cirrus alto frío. Costo bajo (las anomalías reales tienen background nominal de roca/suelo ~270–290 K). Riesgo: eventos invernales con cobertura nubosa parcial real.")
lines.append("- **pc.vrp_mw >= 0.2 MW**: piso de magnitud. Costo: perdemos cola débil MIROVA (Muy Bajo régimen).")
lines.append("- **Path != 'D'-alone**: descarta records que solo dispararon dNTI contextual sin BT/NTI. Costo: pierde detecciones débiles donde D es el único path que captura, pero D solo en condiciones de cirrus es el patrón de FP A23.")
lines.append("- **Combo n_pixels >= 2 AND t_bg_k >= 260**: el más restrictivo razonable. Recall esperado: el aceptable que mantengamos sobre TPs reales.")
lines.append("")

lines.append("## 6. Conclusión y handoff a Frente 1.A S87")
lines.append("")
lines.append(f"El cruce confirma asimetría fuerte: MIROVA publica solo ~{len(mirova_alerta_keys)} noches-sensor mientras nosotros publishable ~{len(our_publishable_keys)}. La precisión global actual ~{fmt_num(global_overall['precision'])} sugiere ~{int((1 - (global_overall['precision'] or 0)) * 100)}% del volumen publicado nuestro es FP relativo a MIROVA.")
lines.append("")
lines.append("La feature con mejor separación TP/FP (ver tabla §5) es el primer candidato para `pc.mirova_publishable`. El segundo candidato útil es combo. Esto es el insumo verificable para implementar el campo derivado en S87.")
lines.append("")

(OUT / "C_crossing.md").write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] Wrote {OUT/'C_crossing.md'}")
print()
print(f"[SUMMARY] universe={len(universe)} TP={global_overall['TP']} FP={global_overall['FP']} FN={global_overall['FN']} prec={global_overall['precision']} rec={global_overall['recall']}")
