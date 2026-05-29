"""
S86 Frente 2.A — Caracterizacion empirica de lo que MIROVA publica.

Filtra CSV CONS + OCR a 11 Tier A + ALERTA_TERMICA(_OCR), produce
distribuciones para destilar el mecanismo de supresion de FPs MIROVA.

Output:
  experiments/_s86_f_precision_gap/A_mirova_published.md
  experiments/_s86_f_precision_gap/A_mirova_published.json
"""
from __future__ import annotations
import json
import sys
import io
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import numpy as np
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "_s86_f_precision_gap"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONS_PATH = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv"
OCR_PATH = ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
YAML_PATH = ROOT / "volcanoes.yaml"

# Tier A canonical names + all CSV variants observed (A14)
TIER_A_VARIANTS = {
    "Llaima": ["Llaima"],
    "Villarrica": ["Villarrica"],
    "Lascar": ["Lascar"],
    "Copahue": ["Copahue"],
    "NevadosDeChillan": ["Nevados de Chillan"],
    "Chaiten": ["Chaiten"],
    "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle"],
    "PlanchonPeteroa": ["PlanchonPeteroa", "Peteroa", "Planchon-Peteroa"],
    "Lastarria": ["Lastarria"],
    "Isluga": ["Isluga"],
    "Tupungatito": ["Tupungatito"],
}
NAME_TO_CANON = {v: k for k, vs in TIER_A_VARIANTS.items() for v in vs}

# Load yaml inner_radius
with open(YAML_PATH, "r", encoding="utf-8") as f:
    YDATA = yaml.safe_load(f)
INNER_RADIUS = {}
for v in YDATA["volcanoes"]:
    n = v.get("name", "")
    if n in TIER_A_VARIANTS:
        INNER_RADIUS[n] = v.get("inner_radius_km")

ALERTA_TYPES = {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR"}


def load_and_filter(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    df["Volcan_canon"] = df["Volcan"].map(NAME_TO_CANON)
    df = df[df["Volcan_canon"].notna()].copy()
    df["Fecha_Satelite_UTC"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df["Fecha_Captura_Chile"] = pd.to_datetime(df["Fecha_Captura_Chile"], errors="coerce")
    return df


cons = load_and_filter(CONS_PATH)
ocr = load_and_filter(OCR_PATH)

# Filter to ALERTAs only (drop RUTINA, FALSO_POSITIVO)
cons_a = cons[cons["Tipo_Registro"].isin(ALERTA_TYPES)].copy()
ocr_a = ocr[ocr["Tipo_Registro"].isin(ALERTA_TYPES)].copy()

# Combine for distribution analysis (OCR has ALERTA_TERMICA_OCR)
combined = pd.concat([cons_a, ocr_a], ignore_index=True)

results: dict = {}

# 1. Temporal window
all_dates = pd.concat([cons["Fecha_Satelite_UTC"], ocr["Fecha_Satelite_UTC"]]).dropna()
date_min = all_dates.min()
date_max = all_dates.max()
n_days = (date_max - date_min).days
results["1_temporal_window"] = {
    "date_min_utc": str(date_min),
    "date_max_utc": str(date_max),
    "n_days_total": n_days,
    "n_rows_cons_total": len(cons),
    "n_rows_ocr_total": len(ocr),
    "n_alertas_cons": int(len(cons_a)),
    "n_alertas_ocr": int(len(ocr_a)),
}

# 2. TPs per volcano x sensor (CONS+OCR combined; ALERTAs only; Tier A)
pivot = (
    combined.groupby(["Volcan_canon", "Sensor"]).size().unstack(fill_value=0).astype(int)
)
# Ensure all sensors columns
for s in ["MODIS", "VIIRS", "VIIRS375", "VIIRS750"]:
    if s not in pivot.columns:
        pivot[s] = 0
pivot["TOTAL"] = pivot.sum(axis=1)
pivot = pivot.sort_values("TOTAL", ascending=False)
results["2_counts_by_vol_sensor"] = pivot.reset_index().to_dict(orient="records")

# 3. VRP_MW distribution per sensor (combined ALERTAs, Tier A)
vrp_dist = {}
for sensor, grp in combined.groupby("Sensor"):
    vals = grp["VRP_MW"].dropna()
    vals = vals[vals > 0]  # MIROVA never publishes VRP=0 with ALERTA
    if len(vals) == 0:
        continue
    vrp_dist[sensor] = {
        "n": int(len(vals)),
        "min": float(vals.min()),
        "p05": float(vals.quantile(0.05)),
        "p25": float(vals.quantile(0.25)),
        "p50": float(vals.quantile(0.50)),
        "p75": float(vals.quantile(0.75)),
        "p95": float(vals.quantile(0.95)),
        "max": float(vals.max()),
        "mean": float(vals.mean()),
    }
results["3_vrp_mw_distribution_by_sensor"] = vrp_dist

# 4. Distancia_km distribution per vol x sensor + cross with inner_radius
dist_dist: dict = {}
out_of_radius = []
for (vol, sensor), grp in combined.groupby(["Volcan_canon", "Sensor"]):
    vals = grp["Distancia_km"].dropna()
    if len(vals) == 0:
        continue
    inner = INNER_RADIUS.get(vol)
    n_out = int((vals > inner).sum()) if inner is not None else None
    key = f"{vol}|{sensor}"
    dist_dist[key] = {
        "n": int(len(vals)),
        "inner_radius_km": inner,
        "min": float(vals.min()),
        "p05": float(vals.quantile(0.05)),
        "p50": float(vals.quantile(0.50)),
        "p95": float(vals.quantile(0.95)),
        "max": float(vals.max()),
        "n_outside_inner_radius": n_out,
    }
    if n_out and n_out > 0:
        # Capture some examples
        offenders = grp[grp["Distancia_km"] > inner][
            ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro"]
        ].head(5)
        out_of_radius.append({
            "vol": vol, "sensor": sensor, "n_out": n_out,
            "examples": offenders.astype(str).to_dict(orient="records"),
        })
results["4_distance_distribution"] = dist_dist
results["4b_alertas_outside_inner_radius"] = out_of_radius

# 5. Persistence: episodes per volcano (gap <=2 days)
def episodes_for_vol(grp: pd.DataFrame, gap_days: int = 2) -> list:
    dates = grp["Fecha_Satelite_UTC"].dropna().dt.normalize().sort_values().unique()
    if len(dates) == 0:
        return []
    eps = []
    cur_start = dates[0]
    cur_end = dates[0]
    for d in dates[1:]:
        if (d - cur_end) / np.timedelta64(1, "D") <= gap_days:
            cur_end = d
        else:
            eps.append((cur_start, cur_end))
            cur_start = d
            cur_end = d
    eps.append((cur_start, cur_end))
    return eps

persistence = {}
duration_buckets_global = Counter()
for vol, grp in combined.groupby("Volcan_canon"):
    eps = episodes_for_vol(grp)
    durations = [int((e - s) / np.timedelta64(1, "D")) + 1 for s, e in eps]
    bucket = Counter()
    for d in durations:
        if d == 1:
            bucket["1 noche"] += 1
        elif d == 2:
            bucket["2 noches"] += 1
        elif d == 3:
            bucket["3 noches"] += 1
        elif d <= 7:
            bucket["4-7 noches"] += 1
        else:
            bucket["8+ noches"] += 1
        duration_buckets_global[
            "1 noche" if d == 1 else
            "2 noches" if d == 2 else
            "3 noches" if d == 3 else
            "4-7 noches" if d <= 7 else "8+ noches"
        ] += 1
    persistence[vol] = {
        "n_episodes": len(eps),
        "duration_buckets": dict(bucket),
        "max_duration_days": max(durations) if durations else 0,
        "mean_duration_days": float(np.mean(durations)) if durations else 0.0,
    }
results["5_persistence"] = persistence
results["5b_persistence_global"] = dict(duration_buckets_global)

# 6. Hora local histogram
hours = combined["Fecha_Captura_Chile"].dropna().dt.hour
hour_hist = hours.value_counts().sort_index().to_dict()
hour_hist = {int(k): int(v) for k, v in hour_hist.items()}
# Also per sensor
hour_per_sensor = {}
for sensor, grp in combined.groupby("Sensor"):
    h = grp["Fecha_Captura_Chile"].dropna().dt.hour.value_counts().sort_index().to_dict()
    hour_per_sensor[sensor] = {int(k): int(v) for k, v in h.items()}
results["6_hour_local_histogram"] = {
    "all_sensors": hour_hist,
    "per_sensor": hour_per_sensor,
}

# 7. Clasificacion Mirova breakdown (ALERTAs only)
clasif = combined["Clasificacion Mirova"].value_counts(dropna=False).to_dict()
clasif = {str(k): int(v) for k, v in clasif.items()}
# Also: do RUTINA records have any non-NULO classification? Sanity:
rutina = cons[cons["Tipo_Registro"] == "RUTINA"]
clasif_rutina = rutina["Clasificacion Mirova"].value_counts(dropna=False).to_dict()
clasif_rutina = {str(k): int(v) for k, v in clasif_rutina.items()}
results["7_clasificacion_mirova"] = {
    "alertas": clasif,
    "rutina_sanity": clasif_rutina,
}

# 8. OCR vs CONS overlap. Key = (Fecha_Satelite_UTC truncated to minute, Volcan_canon, Sensor)
def key(df):
    return list(zip(
        df["Fecha_Satelite_UTC"].dt.floor("min").astype(str),
        df["Volcan_canon"], df["Sensor"]
    ))

cons_keys = set(key(cons_a))
ocr_keys = set(key(ocr_a))
ocr_only = ocr_keys - cons_keys
cons_only = cons_keys - ocr_keys
overlap = ocr_keys & cons_keys
results["8_ocr_vs_cons_overlap"] = {
    "n_cons_alertas": len(cons_keys),
    "n_ocr_alertas": len(ocr_keys),
    "n_overlap": len(overlap),
    "n_ocr_only": len(ocr_only),
    "n_cons_only": len(cons_only),
    "interpretation": (
        "ocr_only = ALERTAs publicadas por MIROVA solo via imagen (no en latest.php JSON). "
        "Confirma o niega un segundo canal de publicacion."
    ),
}
# Sample of ocr-only
ocr_a_keyed = ocr_a.assign(_k=key(ocr_a))
ocr_only_sample = ocr_a_keyed[ocr_a_keyed["_k"].isin(ocr_only)].head(10)
results["8b_ocr_only_sample"] = ocr_only_sample[
    ["Fecha_Satelite_UTC", "Volcan_canon", "Sensor", "VRP_MW", "Distancia_km", "Clasificacion Mirova"]
].astype(str).to_dict(orient="records")

# Write JSON
def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return str(o)

with open(OUT_DIR / "A_mirova_published.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=_default)

# ========================== Write Markdown ==========================
md = []
md.append("# S86 Frente 2.A — Qué publica MIROVA empíricamente\n")
md.append(f"_Generado por `script_A.py`. CSV CONS={len(cons)} filas, OCR={len(ocr)} filas._\n")

md.append("## 1. Ventana temporal y volumen\n")
t = results["1_temporal_window"]
md.append(f"- Primera captura: **{t['date_min_utc']}** UTC")
md.append(f"- Última captura: **{t['date_max_utc']}** UTC")
md.append(f"- Duración: **{t['n_days_total']} días**")
md.append(f"- CONS total: {t['n_rows_cons_total']} filas — de las cuales **{t['n_alertas_cons']}** son ALERTA_TERMICA")
md.append(f"- OCR total: {t['n_rows_ocr_total']} filas — de las cuales **{t['n_alertas_ocr']}** son ALERTA_TERMICA_OCR\n")

md.append("## 2. Conteos por volcán × sensor (ALERTAs, CONS+OCR)\n")
md.append("| Volcán | MODIS | VIIRS | VIIRS375 | VIIRS750 | TOTAL |")
md.append("|---|---:|---:|---:|---:|---:|")
for row in results["2_counts_by_vol_sensor"]:
    md.append(
        f"| {row['Volcan_canon']} | {row.get('MODIS',0)} | {row.get('VIIRS',0)} | "
        f"{row.get('VIIRS375',0)} | {row.get('VIIRS750',0)} | {row['TOTAL']} |"
    )
md.append("")

md.append("## 3. Distribución VRP_MW publicada por sensor\n")
md.append("¿Hay un corte inferior? Si p05 ≫ 0.05 MW, MIROVA no publica anomalías débiles.\n")
md.append("| Sensor | N | min | p05 | p25 | p50 | p75 | p95 | max | mean |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for s, d in vrp_dist.items():
    md.append(
        f"| {s} | {d['n']} | {d['min']:.3f} | {d['p05']:.3f} | {d['p25']:.3f} | "
        f"{d['p50']:.3f} | {d['p75']:.3f} | {d['p95']:.3f} | {d['max']:.2f} | {d['mean']:.3f} |"
    )
md.append("")

md.append("## 4. Distancia al vent vs inner_radius_km\n")
md.append("Si MIROVA es estricto, n_outside_inner_radius debe ser 0 en todos los volcanes (confirma audit S85).\n")
md.append("| Volcán | Sensor | N | inner_km | min | p50 | p95 | max | N fuera |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
for key_str, d in dist_dist.items():
    vol, sensor = key_str.split("|")
    md.append(
        f"| {vol} | {sensor} | {d['n']} | {d['inner_radius_km']} | "
        f"{d['min']:.2f} | {d['p50']:.2f} | {d['p95']:.2f} | {d['max']:.2f} | {d['n_outside_inner_radius']} |"
    )
md.append("")

if out_of_radius:
    md.append("### 4b. ALERTAs FUERA del inner_radius (anomalía si > 0)\n")
    for o in out_of_radius:
        md.append(f"- **{o['vol']} / {o['sensor']}**: {o['n_out']} ALERTAs fuera de inner_radius")
    md.append("")
else:
    md.append("**4b. CERO ALERTAs fuera del inner_radius en los 11 Tier A** — confirma audit S85 empíricamente.\n")

md.append("## 5. Persistencia temporal de episodios (gap ≤2 días)\n")
md.append("Distribución global de duraciones de episodio:\n")
for k, v in results["5b_persistence_global"].items():
    md.append(f"- {k}: **{v}** episodios")
md.append("")
md.append("Por volcán:\n")
md.append("| Volcán | N episodios | Duración media (d) | Duración máx (d) |")
md.append("|---|---:|---:|---:|")
for vol, d in persistence.items():
    md.append(f"| {vol} | {d['n_episodes']} | {d['mean_duration_days']:.1f} | {d['max_duration_days']} |")
md.append("")

md.append("## 6. Hora local (Chile) de las ALERTAs\n")
md.append("Físicamente: MIR solo nocturno (contaminación solar), TIR 24h. ¿Se ve en la data?\n")
md.append("Histograma agregado (hora local Chile → N ALERTAs):\n")
md.append("| Hora | N |")
md.append("|---:|---:|")
for h in sorted(hour_hist.keys()):
    md.append(f"| {h:02d} | {hour_hist[h]} |")
md.append("")

md.append("## 7. Clasificación MIROVA en ALERTAs\n")
md.append("¿Hay categorías intermedias o solo NULO/Bajo/...? ¿NULO conviven con ALERTA?\n")
md.append("**ALERTAs (Tier A, CONS+OCR):**\n")
for k, v in results["7_clasificacion_mirova"]["alertas"].items():
    md.append(f"- `{k}`: {v}")
md.append("\n**Sanity RUTINA (CONS, Tier A):**\n")
for k, v in results["7_clasificacion_mirova"]["rutina_sanity"].items():
    md.append(f"- `{k}`: {v}")
md.append("")

md.append("## 8. OCR vs CONS — ¿segundo canal de publicación?\n")
o = results["8_ocr_vs_cons_overlap"]
md.append(f"- ALERTAs en CONS (latest.php JSON): **{o['n_cons_alertas']}**")
md.append(f"- ALERTAs en OCR (extraídas de imágenes por-vol): **{o['n_ocr_alertas']}**")
md.append(f"- Overlap (mismas claves): **{o['n_overlap']}**")
md.append(f"- Solo en OCR (publicadas SOLO vía imagen): **{o['n_ocr_only']}**")
md.append(f"- Solo en CONS: **{o['n_cons_only']}**")
md.append("")
md.append("Interpretación: si `n_ocr_only` es alto, MIROVA tiene un segundo canal de publicación que solo aparece en las imágenes por-volcán y no en `latest.php`. Universo MIROVA real = CONS ∪ OCR (regla A11).\n")

(OUT_DIR / "A_mirova_published.md").write_text("\n".join(md), encoding="utf-8")

print("OK ->", OUT_DIR / "A_mirova_published.md")
print("OK ->", OUT_DIR / "A_mirova_published.json")
print()
print("=== Highlights ===")
print(f"Ventana: {t['date_min_utc']} -> {t['date_max_utc']} ({t['n_days_total']}d)")
print(f"ALERTAs CONS: {t['n_alertas_cons']}, OCR: {t['n_alertas_ocr']}")
print(f"OCR-only ALERTAs: {o['n_ocr_only']} / {o['n_ocr_alertas']}")
print(f"VRP_MW p05 por sensor:")
for s, d in vrp_dist.items():
    print(f"  {s}: p05={d['p05']:.3f}, p50={d['p50']:.3f}, min={d['min']:.3f}")
total_out = sum(d["n_outside_inner_radius"] or 0 for d in dist_dist.values())
print(f"Total ALERTAs fuera de inner_radius: {total_out}")
print(f"Clasificacion MIROVA en ALERTAs: {results['7_clasificacion_mirova']['alertas']}")
