"""S58-OSF-VILLARRICA-DEEP

Analisis profundo OSF v2.5 archive Villarrica (5211 filas 2005-2024)
para entender patron VRP MIROVA real y validar hipotesis local_kernel_bg.

Columnas:
  id, timeUTC, IDvolc, Dayflag, Satellite, Resolution, SatZen, SatAzi,
  Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP, LAT, LON, Max_Dist,
  Volc_Name, Volc_LAT, Volc_LON, class
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

OSF = Path(
    r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
)
VRP_JSON = Path(
    r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_equivalent\Villarrica.json"
)

print(f"[INFO] Reading {OSF.name} ({OSF.stat().st_size/1e6:.1f} MB)")

# Stream filter por Volc_Name (98MB, evitemos cargar todo)
chunks = []
for chunk in pd.read_csv(OSF, chunksize=100_000, low_memory=False):
    sub = chunk[chunk["Volc_Name"].astype(str).str.contains("Villarrica", case=False, na=False)]
    if len(sub):
        chunks.append(sub)
df = pd.concat(chunks, ignore_index=True)
print(f"[OK] Filas Villarrica: {len(df)}")
print(f"[OK] Cols: {list(df.columns)}")
print()

# Tipos
df["timeUTC"] = pd.to_datetime(df["timeUTC"], errors="coerce", utc=True)
for col in ["VRP", "Tot_Lmir_hot", "Tot_Lmir_bk", "Max_Dist", "Resolution",
            "SatZen", "Npix", "LAT", "LON", "class", "Dayflag"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ==================== (1) STATS GLOBALES ====================
print("=" * 70)
print("(1) STATS GLOBALES Villarrica")
print("=" * 70)

# Rango temporal
print(f"Rango temporal: {df['timeUTC'].min()} -> {df['timeUTC'].max()}")
print(f"Filas totales: {len(df)}")
print()

# Dist por resolution
print("Distribucion VRP (W) por Resolution:")
print(df.groupby("Resolution")["VRP"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).to_string())
print()

print("Distribucion Max_Dist (m) por Resolution:")
print(df.groupby("Resolution")["Max_Dist"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).to_string())
print()

# Dayflag distribution
print("Distribucion Dayflag (0=noche, 1=dia) por Resolution:")
print(df.groupby(["Resolution", "Dayflag"]).size().to_string())
print()

# Frec mensual
df["yyyymm"] = df["timeUTC"].dt.to_period("M")
mensual = df.groupby("yyyymm").size()
print("Frec mensual stats:")
print(f"  median  : {mensual.median():.1f}")
print(f"  p25/p75 : {mensual.quantile(0.25):.1f} / {mensual.quantile(0.75):.1f}")
print(f"  max     : {mensual.max()}  (mes: {mensual.idxmax()})")
print(f"  min     : {mensual.min()}  (mes: {mensual.idxmin()})")
print(f"  meses sin detecciones: {sum(mensual == 0)}")
print()

# Class distribution
print("Distribucion class:")
print(df["class"].value_counts(dropna=False).to_string())
print()

# Class por resolution
print("Class por Resolution:")
print(df.groupby(["Resolution", "class"]).size().unstack(fill_value=0).to_string())
print()

# ==================== (2) PATRON BG ====================
print("=" * 70)
print("(2) PATRON Tot_Lmir_bk vs Tot_Lmir_hot")
print("=" * 70)
df["bg_hot_ratio"] = df["Tot_Lmir_bk"] / df["Tot_Lmir_hot"].replace(0, np.nan)
df["delta_L"] = df["Tot_Lmir_hot"] - df["Tot_Lmir_bk"]
df["pct_signal"] = df["delta_L"] / df["Tot_Lmir_hot"].replace(0, np.nan) * 100

print("Ratio bg / hot por Resolution (1.0 = bg igual a hot, marginal):")
print(df.groupby("Resolution")["bg_hot_ratio"].describe(percentiles=[0.5, 0.9, 0.95, 0.99]).to_string())
print()

print("Tot_Lmir_bk magnitud por Resolution:")
print(df.groupby("Resolution")["Tot_Lmir_bk"].describe(percentiles=[0.5, 0.9]).to_string())
print()

print("Tot_Lmir_hot magnitud por Resolution:")
print(df.groupby("Resolution")["Tot_Lmir_hot"].describe(percentiles=[0.5, 0.9]).to_string())
print()

print(f"Casos marginales (bg/hot > 0.9): {(df['bg_hot_ratio'] > 0.9).sum()}")
print(f"Casos marginales (bg/hot > 0.95): {(df['bg_hot_ratio'] > 0.95).sum()}")
print(f"% senal mediano por Resolution:")
print(df.groupby("Resolution")["pct_signal"].describe(percentiles=[0.25, 0.5, 0.75]).to_string())
print()

# ==================== (3) MAGNITUDES VRP VIIRS-I ====================
print("=" * 70)
print("(3) Magnitudes VRP detecciones VIIRS-I (Resolution=375)")
print("=" * 70)
vi = df[df["Resolution"] == 375].copy()
print(f"# VIIRS-I detecciones: {len(vi)}")
vrp_mw = vi["VRP"] / 1e6
print(f"VRP (MW) percentiles:")
for p in [5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  p{p:>2}: {np.percentile(vrp_mw.dropna(), p):.3f} MW")
print(f"  mean: {vrp_mw.mean():.3f} MW   std: {vrp_mw.std():.3f}")
print()

# Si Max_Dist correlaciona con magnitud
vi["dist_bin"] = pd.cut(vi["Max_Dist"],
                       bins=[0, 500, 900, 1500, 3000, 10000, 50000],
                       labels=["<500", "500-900", "900-1500", "1500-3000",
                               "3000-10k", ">10k"])
print("VIIRS-I VRP (MW) por bin de Max_Dist:")
g = vi.groupby("dist_bin", observed=True)["VRP"].agg(["count", "median", "mean", "max"])
g["median_MW"] = g["median"] / 1e6
g["mean_MW"] = g["mean"] / 1e6
g["max_MW"] = g["max"] / 1e6
print(g[["count", "median_MW", "mean_MW", "max_MW"]].to_string())
print()

# ==================== (4) HIPOTESIS SNAP 838m ====================
print("=" * 70)
print("(4) Hipotesis snap pixel 838m para VIIRS-I (Resolution=375)")
print("=" * 70)
print(f"Max_Dist VIIRS-I describe:")
print(vi["Max_Dist"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_string())
print()

# Valores unicos / clusters
print("Top 15 valores Max_Dist VIIRS-I mas frecuentes:")
print(vi["Max_Dist"].round().value_counts().head(15).to_string())
print()

# Bin alrededor de 838
window = vi[(vi["Max_Dist"] >= 700) & (vi["Max_Dist"] <= 1000)]
print(f"Detecciones con Max_Dist en [700, 1000]: {len(window)} ({len(window)/len(vi)*100:.1f}%)")
window2 = vi[(vi["Max_Dist"] >= 800) & (vi["Max_Dist"] <= 900)]
print(f"Detecciones con Max_Dist en [800, 900]: {len(window2)} ({len(window2)/len(vi)*100:.1f}%)")
print()

# Histograma rapido
print("Histograma Max_Dist VIIRS-I:")
bins = [0, 200, 400, 600, 800, 900, 1000, 1500, 2000, 3000, 5000, 10000, 50000]
hist, edges = np.histogram(vi["Max_Dist"].dropna(), bins=bins)
for h, lo, hi in zip(hist, edges[:-1], edges[1:]):
    bar = "#" * int(h / max(hist) * 50)
    print(f"  [{lo:>5}, {hi:>5}): {h:>5}  {bar}")
print()

# Para MODIS y VIIRS-M tambien
print("Max_Dist MODIS top 15:")
mo = df[df["Resolution"] == 1000]
print(mo["Max_Dist"].round(-2).value_counts().head(15).to_string())
print()
print("Max_Dist VIIRS-M top 15:")
vm = df[df["Resolution"] == 750]
print(vm["Max_Dist"].round(-2).value_counts().head(15).to_string())
print()

# ==================== (5) COMPARATIVA VENTANA NUESTRA ====================
print("=" * 70)
print("(5) Comparativa ventana 2026-04-16 a 2026-05-15")
print("=" * 70)
win_start = pd.Timestamp("2026-04-16", tz="UTC")
win_end = pd.Timestamp("2026-05-15", tz="UTC")
print(f"OSF rango end: {df['timeUTC'].max()}")
in_win = df[(df["timeUTC"] >= win_start) & (df["timeUTC"] <= win_end)]
print(f"# OSF en ventana nuestra: {len(in_win)}")
if len(in_win) == 0:
    print("[INFO] OSF v2.5 termina antes de 2026, esperado")
    # Cuantas detections en 2024-Q4 (final OSF) y comparar magnitud
    last_year = df[df["timeUTC"].dt.year == df["timeUTC"].dt.year.max()]
    print(f"# detecciones year={df['timeUTC'].dt.year.max()}: {len(last_year)}")
    print(f"# per Resolution:")
    print(last_year["Resolution"].value_counts().to_string())
print()

# Nuestras detections recientes Villarrica
try:
    vrp = json.loads(VRP_JSON.read_text(encoding="utf-8"))
    records = vrp.get("records", [])
    recent = [r for r in records
              if r.get("timestamp_utc", "") >= "2026-04-16T00:00:00"
              and r.get("timestamp_utc", "") <= "2026-05-15T23:59:59"]
    print(f"# nuestros records Villarrica en ventana: {len(recent)}")
    detected = [r for r in recent if r.get("anomaly_detected")]
    print(f"# detections (anomaly_detected): {len(detected)}")
    if detected:
        mws = [r.get("vrp_mw", 0) for r in detected if r.get("vrp_mw") is not None]
        print(f"  vrp_mw mediana: {np.median(mws):.3f}")
        print(f"  vrp_mw rango: {min(mws):.3f} - {max(mws):.3f}")
except Exception as e:
    print(f"[WARN] No pude leer VRP_JSON: {e}")
print()

# ==================== (6) IMPLICACIONES ====================
print("=" * 70)
print("(6) Implicaciones para validacion S58 local_kernel_bg")
print("=" * 70)
print(f"OSF termina: {df['timeUTC'].max()}")
print(f"Nuestra ventana: {win_start} - {win_end}")
print(f"Overlap: {len(in_win)} filas")
print()
print("Detection rate VIIRS-I por year (proxy persistencia lava lake):")
vi_year = vi.groupby(vi["timeUTC"].dt.year).size()
print(vi_year.to_string())
print()

# Distribucion temporal noche/dia VIIRS-I
print("VIIRS-I Dayflag distribution:")
print(vi["Dayflag"].value_counts(dropna=False).to_string())
print()

# Output JSON resumen
summary = {
    "rows_total": int(len(df)),
    "time_range": [str(df["timeUTC"].min()), str(df["timeUTC"].max())],
    "by_resolution": {
        str(r): {
            "n": int((df["Resolution"] == r).sum()),
            "vrp_mw_median": float(np.nanmedian(df.loc[df["Resolution"] == r, "VRP"]) / 1e6),
            "vrp_mw_p90": float(np.nanpercentile(df.loc[df["Resolution"] == r, "VRP"].dropna(), 90) / 1e6),
            "max_dist_m_median": float(np.nanmedian(df.loc[df["Resolution"] == r, "Max_Dist"])),
            "max_dist_m_p90": float(np.nanpercentile(df.loc[df["Resolution"] == r, "Max_Dist"].dropna(), 90)),
        } for r in df["Resolution"].dropna().unique()
    },
    "bg_hot_ratio_median_by_res": {
        str(r): float(df.loc[df["Resolution"] == r, "bg_hot_ratio"].median())
        for r in df["Resolution"].dropna().unique()
    },
    "viirs_i_in_700_1000m": int(len(window)),
    "viirs_i_in_800_900m": int(len(window2)),
    "viirs_i_total": int(len(vi)),
    "our_window_overlap_osf": int(len(in_win)),
}
out = Path(
    r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\102_osf_villarrica_deep.json"
)
out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
print(f"[OK] Summary JSON: {out}")
