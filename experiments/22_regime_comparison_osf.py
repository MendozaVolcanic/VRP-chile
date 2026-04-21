"""
S14 Paso 1a — Comparación de régimen estadístico VRP Chile vs MIROVA v2.5.

No requiere overlap temporal. Compara DISTRIBUCIONES de VRP por (volcán, sensor)
entre:
  - Nuestro pipeline: detecciones mirova_equivalent enero-abril 2026 (3.5 meses)
  - MIROVA v2.5:      últimos 12 meses disponibles (2024-12 a 2025-12)

Responde: "¿nuestro pipeline produce detecciones con el mismo régimen
poblacional que MIROVA en el mismo volcán?" Si sí → paridad de régimen.
Si no → sesgo sistemático a identificar.

Métricas por (volcán × sensor_res):
  - n detecciones positivas (VRP>0)
  - mediana y p25/p75 de VRP [MW]
  - KS-test bidireccional log10(VRP) para saber si vienen de la misma dist
  - ratio medianas (nuestra/MIROVA) — debería estar en [0.7, 1.4] para paridad

Autor: S14 2026-04-21. Read-only.
"""

import sys, io, json
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats as sps

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OSF_CSV = ROOT / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
OURS_DIR = ROOT / "data" / "mirova_equivalent"
OUT_JSON = ROOT / "experiments" / "22_regime_comparison.json"
OUT_PNG  = ROOT / "experiments" / "22_regime_comparison.png"

NAME_MAP = {
    "Lascar": "Láscar",
    "Chaiten": "Chaitén",
    "PuyehueCordonCaulle": "Puyehue-Cordón Caulle",
    "Lastarria": "Lastarria",
    "Villarrica": "Villarrica",
    "NevadosDeChillan": "Chillán, Nevados de",
    "Isluga": "Isluga",
    "Copahue": "Copahue",
    "PlanchonPeteroa": "Planchón-Peteroa",
    "Llaima": "Llaima",
}

# Mapeo sensor nuestro → (sensor_label, resolution OSF)
SENSOR_MAP = {
    "MODIS_TERRA":      ("MODIS", 1000),
    "MODIS_AQUA":       ("MODIS", 1000),
    "VIIRS_SNPP_750":   ("VIIRS_M", 750),
    "VIIRS_NOAA20_750": ("VIIRS_M", 750),
    "VIIRS_SNPP":       ("VIIRS_I", 375),
    "VIIRS_NOAA20":     ("VIIRS_I", 375),
}

# Ventana MIROVA: últimos 12 meses disponibles
MIROVA_CUTOFF = datetime(2024, 12, 1)   # inclusive

# --- Carga OSF ---
print(f"[1/4] Cargando OSF v2.5...")
osf = pd.read_csv(OSF_CSV)
osf["dt"] = pd.to_datetime(osf["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
osf = osf.dropna(subset=["dt"]).copy()
osf = osf[osf["Volc_Name"].isin(NAME_MAP.values())].copy()
osf = osf[osf["dt"] >= MIROVA_CUTOFF].copy()
osf["vrp_mw"] = osf["VRP"] / 1e6
print(f"      MIROVA filas chilenas >= {MIROVA_CUTOFF.date()}: {len(osf):,}")

osf_label = {1000: "MODIS", 750: "VIIRS_M", 375: "VIIRS_I"}
osf["sensor_label"] = osf["Resolution"].map(osf_label)

# --- Carga nuestras ---
print(f"[2/4] Cargando nuestras detecciones...")
ours_rows = []
for fname, osf_name in NAME_MAP.items():
    fp = OURS_DIR / f"{fname}.json"
    if not fp.exists():
        continue
    obj = json.load(open(fp, encoding="utf-8"))
    for rec in obj.get("records", []):
        sensor_raw = rec.get("sensor", "")
        if sensor_raw not in SENSOR_MAP:
            continue
        sensor_label, resolution = SENSOR_MAP[sensor_raw]
        vrp_mw = rec.get("vrp_mw", 0.0) or 0.0
        if vrp_mw <= 0:
            continue
        ours_rows.append({
            "volcano": fname,
            "osf_name": osf_name,
            "sensor_label": sensor_label,
            "resolution": resolution,
            "vrp_mw": vrp_mw,
        })

ours = pd.DataFrame(ours_rows)
print(f"      nuestras detecciones positivas: {len(ours)}")

# --- Comparación por (volcán, sensor_label) ---
print(f"[3/4] Comparando régimen...")
rows = []
for fname, osf_name in NAME_MAP.items():
    for sensor_label in ["MODIS", "VIIRS_M", "VIIRS_I"]:
        ours_sub = ours[(ours["volcano"] == fname) & (ours["sensor_label"] == sensor_label)]
        osf_sub  = osf[(osf["Volc_Name"] == osf_name) & (osf["sensor_label"] == sensor_label)]

        def pct(a, q): return float(np.percentile(a, q)) if len(a) else float("nan")

        ours_vrp = ours_sub["vrp_mw"].values
        osf_vrp  = osf_sub["vrp_mw"].values

        if len(ours_vrp) < 3 or len(osf_vrp) < 3:
            ks_p = float("nan")
            ratio = float("nan")
        else:
            try:
                ks_p = float(sps.ks_2samp(np.log10(ours_vrp), np.log10(osf_vrp))[1])
            except Exception:
                ks_p = float("nan")
            ratio = float(np.median(ours_vrp) / np.median(osf_vrp)) if np.median(osf_vrp) > 0 else float("nan")

        rows.append({
            "volcano": fname,
            "sensor": sensor_label,
            "n_ours": int(len(ours_vrp)),
            "n_osf": int(len(osf_vrp)),
            "med_ours_mw": pct(ours_vrp, 50),
            "med_osf_mw":  pct(osf_vrp, 50),
            "p25_ours":    pct(ours_vrp, 25),
            "p75_ours":    pct(ours_vrp, 75),
            "p25_osf":     pct(osf_vrp, 25),
            "p75_osf":     pct(osf_vrp, 75),
            "min_ours":    float(np.min(ours_vrp)) if len(ours_vrp) else float("nan"),
            "min_osf":     float(np.min(osf_vrp))  if len(osf_vrp)  else float("nan"),
            "max_ours":    float(np.max(ours_vrp)) if len(ours_vrp) else float("nan"),
            "max_osf":     float(np.max(osf_vrp))  if len(osf_vrp)  else float("nan"),
            "ks_p_log10":  ks_p,
            "ratio_med":   ratio,
        })

comp = pd.DataFrame(rows)

def paridad(r):
    if r["n_ours"] < 3 or r["n_osf"] < 3:
        return "sin datos"
    ratio = r["ratio_med"]
    if np.isnan(ratio):
        return "sin datos"
    if 0.7 <= ratio <= 1.4:
        if r["ks_p_log10"] > 0.05:
            return "✅ paridad"
        else:
            return "⚠️ mediana ok, dist distinta"
    elif 0.4 <= ratio <= 2.5:
        return "⚠️ sesgo moderado"
    else:
        return "🔴 sesgo fuerte"

comp["veredicto"] = comp.apply(paridad, axis=1)

# --- PNG ---
print(f"[4/4] Generando figuras...")
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    volcanoes_with_data = [v for v in NAME_MAP if
                            (comp[comp["volcano"] == v][["n_ours", "n_osf"]].min().min() >= 3)]
    volcanoes_with_data = volcanoes_with_data[:10]

    fig, axes = plt.subplots(len(volcanoes_with_data), 3, figsize=(15, 3*len(volcanoes_with_data)))
    if len(volcanoes_with_data) == 1:
        axes = axes.reshape(1, -1)

    for i, v in enumerate(volcanoes_with_data):
        for j, sensor in enumerate(["MODIS", "VIIRS_M", "VIIRS_I"]):
            ax = axes[i, j]
            our_sub = ours[(ours["volcano"] == v) & (ours["sensor_label"] == sensor)]
            osf_sub = osf[(osf["Volc_Name"] == NAME_MAP[v]) & (osf["sensor_label"] == sensor)]
            if len(our_sub) >= 3 and len(osf_sub) >= 3:
                bins = np.logspace(
                    np.log10(max(1e-3, min(our_sub["vrp_mw"].min(), osf_sub["vrp_mw"].min()))),
                    np.log10(max(our_sub["vrp_mw"].max(), osf_sub["vrp_mw"].max())),
                    30,
                )
                ax.hist(osf_sub["vrp_mw"], bins=bins, alpha=0.5, color="steelblue",
                        label=f"MIROVA n={len(osf_sub)}", density=True)
                ax.hist(our_sub["vrp_mw"], bins=bins, alpha=0.5, color="orangered",
                        label=f"ours n={len(our_sub)}", density=True)
                ax.set_xscale("log")
                ax.legend(fontsize=7)
            ax.set_title(f"{v} / {sensor}", fontsize=9)
            ax.set_xlabel("VRP [MW]", fontsize=8)
            ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=90)
    print(f"      PNG: {OUT_PNG.name}")
except Exception as e:
    print(f"      WARN PNG: {e}")

# --- Save ---
out = {
    "experiment": "22_regime_comparison_osf",
    "session": "S14",
    "generated_utc": datetime.now().isoformat() + "Z",
    "our_window": "2026-01-01 to 2026-04-17 (3.5 meses)",
    "mirova_window": f"{MIROVA_CUTOFF.date()} to 2025-12-31 (13 meses)",
    "comparison": comp.to_dict(orient="records"),
}
OUT_JSON.parent.mkdir(exist_ok=True, parents=True)
json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)

# --- Stdout ---
print()
print("=" * 96)
print(f"RESULTADO Paso 1a — comparación régimen nuestra vs MIROVA")
print("=" * 96)
print(f"{'volcán':<22s} {'sensor':<8s} {'n_ours':>7s} {'n_osf':>7s} {'med_us':>8s} {'med_osf':>8s} {'ratio':>7s}  veredicto")
print("-" * 96)
for _, r in comp.sort_values(["volcano", "sensor"]).iterrows():
    if r["n_ours"] == 0 and r["n_osf"] == 0:
        continue
    med_u = f"{r['med_ours_mw']:.3f}" if not np.isnan(r["med_ours_mw"]) else "   -"
    med_o = f"{r['med_osf_mw']:.3f}"  if not np.isnan(r["med_osf_mw"])  else "   -"
    rat   = f"{r['ratio_med']:.2f}"   if not np.isnan(r["ratio_med"])   else "   -"
    print(f"{r['volcano']:<22s} {r['sensor']:<8s} {r['n_ours']:>7d} {r['n_osf']:>7d} {med_u:>8s} {med_o:>8s} {rat:>7s}  {r['veredicto']}")

print()
print(f"JSON: {OUT_JSON}")
print(f"PNG:  {OUT_PNG}")
