"""
S14 Paso 1b-paralelo — 4 diagnósticos que NO requieren fetch.

Contestan las hipótesis abiertas del Paso 1a sin reproceso:
  A) Npix comparado: ¿MIROVA clusteriza más pixels que nosotros?
     Si sí, explica sesgo VIIRS_M 0.01-0.33 sin bug de coeficiente.
  B) Distribución hotspot→vent distance: geofencing Copahue sospechoso.
  C) Review process_viirs_mod.py vs process_viirs.py — fuera de script, manual.
  D) Chaitén sobre-detección: distribución hotspot_dist_km nuestra vs MIROVA.

Autor: S14 2026-04-21.
"""

import sys, io, json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OSF_CSV = ROOT / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
OURS_DIR = ROOT / "data" / "mirova_equivalent"
OUT_JSON = ROOT / "experiments" / "23_parallel_diagnostics.json"
OUT_PNG  = ROOT / "experiments" / "23_parallel_diagnostics.png"

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
SENSOR_MAP = {
    "MODIS_TERRA":      ("MODIS", 1000),
    "MODIS_AQUA":       ("MODIS", 1000),
    "VIIRS_SNPP_750":   ("VIIRS_M", 750),
    "VIIRS_NOAA20_750": ("VIIRS_M", 750),
    "VIIRS_SNPP":       ("VIIRS_I", 375),
    "VIIRS_NOAA20":     ("VIIRS_I", 375),
}
MIROVA_CUTOFF = datetime(2024, 12, 1)

# --- Load MIROVA ---
print(f"[1/3] Cargando OSF v2.5 y nuestros JSONs...")
osf = pd.read_csv(OSF_CSV)
osf["dt"] = pd.to_datetime(osf["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
osf = osf.dropna(subset=["dt"])
osf = osf[(osf["Volc_Name"].isin(NAME_MAP.values())) & (osf["dt"] >= MIROVA_CUTOFF)].copy()
osf["sensor_label"] = osf["Resolution"].map({1000:"MODIS", 750:"VIIRS_M", 375:"VIIRS_I"})

# --- Load ours ---
ours_rows = []
for fname, osf_name in NAME_MAP.items():
    fp = OURS_DIR / f"{fname}.json"
    if not fp.exists(): continue
    obj = json.load(open(fp, encoding="utf-8"))
    for rec in obj.get("records", []):
        sensor_raw = rec.get("sensor", "")
        if sensor_raw not in SENSOR_MAP: continue
        sensor_label, res = SENSOR_MAP[sensor_raw]
        vrp = rec.get("vrp_mw", 0.0) or 0.0
        if vrp <= 0: continue
        ours_rows.append({
            "volcano": fname, "osf_name": osf_name,
            "sensor_label": sensor_label, "resolution": res,
            "vrp_mw": vrp,
            "n_anom": rec.get("n_anomalous_pixels", 0),
            "hotspot_dist_km": rec.get("hotspot_dist_km"),
            "t_max_k": rec.get("t_max_k"),
            "t_bg_k": rec.get("t_bg_k"),
        })
ours = pd.DataFrame(ours_rows)
print(f"      MIROVA filas: {len(osf):,}  |  nuestras detecciones: {len(ours):,}")

# --- Diagnóstico A: Npix comparado ---
print(f"[2/3] Diagnóstico A — Npix comparado ours vs MIROVA...")
A_rows = []
for fname, osf_name in NAME_MAP.items():
    for sensor in ["MODIS","VIIRS_M","VIIRS_I"]:
        o = ours[(ours["volcano"]==fname) & (ours["sensor_label"]==sensor)]["n_anom"]
        m = osf[(osf["Volc_Name"]==osf_name) & (osf["sensor_label"]==sensor)]["Npix"]
        if len(o)<3 or len(m)<3: continue
        A_rows.append({
            "volcano": fname, "sensor": sensor,
            "n_ours": int(len(o)), "n_osf": int(len(m)),
            "npix_ours_med": float(o.median()),
            "npix_osf_med":  float(m.median()),
            "npix_ours_max": int(o.max()),
            "npix_osf_max":  int(m.max()),
            "ratio_median":  float(o.median() / m.median()) if m.median()>0 else None,
        })
A = pd.DataFrame(A_rows)

# --- Diagnóstico B: distribución hotspot_dist_km ---
print(f"[2/3] Diagnóstico B — distribución distancia vent→hotspot...")
B_rows = []
for fname, osf_name in NAME_MAP.items():
    o = ours[(ours["volcano"]==fname)]["hotspot_dist_km"].dropna()
    m = osf[osf["Volc_Name"]==osf_name]["Max_Dist"] / 1000.0  # OSF Max_Dist en metros
    if len(o)<3: continue
    B_rows.append({
        "volcano": fname,
        "n_ours": int(len(o)), "n_osf": int(len(m)),
        "dist_km_ours_med":  float(o.median()),
        "dist_km_ours_p90":  float(o.quantile(0.90)),
        "dist_km_ours_max":  float(o.max()),
        "dist_km_osf_med":   float(m.median())   if len(m) else None,
        "dist_km_osf_p90":   float(m.quantile(0.90)) if len(m) else None,
        "dist_km_osf_max":   float(m.max())      if len(m) else None,
    })
B = pd.DataFrame(B_rows)

# --- Diagnóstico D: Chaitén específico (detallar) ---
print(f"[2/3] Diagnóstico D — foco Chaitén sobre-detección...")
D = {}
chai_ours = ours[ours["volcano"]=="Chaiten"]
chai_osf = osf[osf["Volc_Name"]=="Chaitén"]
if len(chai_ours) and len(chai_osf):
    D = {
        "n_ours": int(len(chai_ours)),
        "n_osf": int(len(chai_osf)),
        "ours_hot_dist_km_hist": np.histogram(
            chai_ours["hotspot_dist_km"].dropna(),
            bins=[0,0.5,1,2,3,5,10,20])[0].tolist(),
        "osf_hot_dist_km_hist": np.histogram(
            (chai_osf["Max_Dist"]/1000).dropna(),
            bins=[0,0.5,1,2,3,5,10,20])[0].tolist(),
        "bins": [0,0.5,1,2,3,5,10,20],
        "ours_t_max_minus_bg_med": float((chai_ours["t_max_k"] - chai_ours["t_bg_k"]).median()),
        "ours_vrp_vs_dist_corr": float(chai_ours[["vrp_mw","hotspot_dist_km"]].dropna().corr().iloc[0,1]) if len(chai_ours.dropna(subset=["hotspot_dist_km","vrp_mw"])) > 2 else None,
    }

# --- PNG ---
print(f"[3/3] PNG...")
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # A: Npix mediana ratio
    ax = axes[0,0]
    if len(A):
        A_plot = A.sort_values(["sensor","volcano"])
        pos = range(len(A_plot))
        colors = {"MODIS":"tab:blue","VIIRS_M":"tab:orange","VIIRS_I":"tab:green"}
        ax.barh(pos, A_plot["ratio_median"], color=[colors[s] for s in A_plot["sensor"]])
        ax.axvline(1.0, color="k", ls="--", alpha=0.5)
        ax.set_yticks(pos)
        ax.set_yticklabels([f"{r['volcano']} / {r['sensor']}" for _,r in A_plot.iterrows()], fontsize=7)
        ax.set_xlabel("ratio Npix (ours/MIROVA)")
        ax.set_title("A — Clustering: ¿detectamos menos pixels?")
        ax.grid(alpha=0.3)

    # B: distribuciones distancia
    ax = axes[0,1]
    if len(B):
        x = range(len(B))
        ax.errorbar(x, B["dist_km_ours_med"], yerr=B["dist_km_ours_p90"]-B["dist_km_ours_med"],
                     fmt="o", label="ours", color="orangered")
        if B["dist_km_osf_med"].notna().any():
            ax.errorbar(x, B["dist_km_osf_med"], yerr=B["dist_km_osf_p90"]-B["dist_km_osf_med"],
                         fmt="s", label="MIROVA", color="steelblue")
        ax.set_xticks(x)
        ax.set_xticklabels(B["volcano"], rotation=45, fontsize=7, ha="right")
        ax.set_ylabel("distancia vent→hotspot [km]")
        ax.set_title("B — Geofencing: ¿cortamos detecciones lejanas?")
        ax.legend()
        ax.grid(alpha=0.3)

    # D: histograma Chaitén
    ax = axes[1,0]
    if D:
        bins = D["bins"]
        centers = [(bins[i]+bins[i+1])/2 for i in range(len(bins)-1)]
        width = [(bins[i+1]-bins[i])*0.4 for i in range(len(bins)-1)]
        ax.bar([c-w/2 for c,w in zip(centers,width)], D["ours_hot_dist_km_hist"],
                width=[w for w in width], label=f"ours n={D['n_ours']}", color="orangered", alpha=0.7)
        ax.bar([c+w/2 for c,w in zip(centers,width)], D["osf_hot_dist_km_hist"],
                width=[w for w in width], label=f"MIROVA n={D['n_osf']}", color="steelblue", alpha=0.7)
        ax.set_xscale("symlog")
        ax.set_xlabel("distancia [km]")
        ax.set_ylabel("n detecciones")
        ax.set_title("D — Chaitén: halo térmico vs vent")
        ax.legend()
        ax.grid(alpha=0.3)

    # A-numeric table
    ax = axes[1,1]
    ax.axis("off")
    if len(A):
        summary = A[A["ratio_median"].notna()].sort_values("ratio_median").head(15)
        tab = ax.table(cellText=[[f"{r['volcano'][:12]:<12s}", r['sensor'],
                                    f"{r['npix_ours_med']:.1f}", f"{r['npix_osf_med']:.1f}",
                                    f"{r['ratio_median']:.2f}"] for _,r in summary.iterrows()],
                         colLabels=["volcán","sensor","Npix_us","Npix_osf","ratio"],
                         loc="center", cellLoc="left")
        tab.auto_set_font_size(False); tab.set_fontsize(7)
        ax.set_title("A-tabla — los 15 casos con menor ratio Npix (clustering pobre)")

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=100)
    print(f"      PNG: {OUT_PNG.name}")
except Exception as e:
    print(f"      WARN PNG: {e}")

# --- Save ---
out = {
    "experiment": "23_parallel_diagnostics",
    "session": "S14",
    "generated_utc": datetime.now().isoformat() + "Z",
    "A_npix_comparison": A.to_dict(orient="records"),
    "B_distance_distribution": B.to_dict(orient="records"),
    "D_chaiten_focus": D,
}
json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)

# --- Stdout ---
print()
print("=" * 96)
print("DIAGNÓSTICO A — Npix mediano ours vs MIROVA (ratio <1 = clustering pobre)")
print("=" * 96)
if len(A):
    A_s = A.sort_values(["sensor","ratio_median"])
    print(f"{'volcán':<22s} {'sensor':<8s} {'Npix_us':>8s} {'Npix_os':>8s} {'ratio':>7s}  {'n_ours':>7s}")
    for _, r in A_s.iterrows():
        rat = f"{r['ratio_median']:.2f}" if r['ratio_median'] else "-"
        print(f"{r['volcano']:<22s} {r['sensor']:<8s} {r['npix_ours_med']:>8.2f} {r['npix_osf_med']:>8.2f} {rat:>7s}  {r['n_ours']:>7d}")

print()
print("=" * 96)
print("DIAGNÓSTICO B — Distancia vent→hotspot [km]")
print("=" * 96)
if len(B):
    print(f"{'volcán':<22s} {'med_us':>7s} {'max_us':>7s} {'med_os':>7s} {'max_os':>7s}   comentario")
    for _, r in B.iterrows():
        med_o = f"{r['dist_km_osf_med']:.2f}"  if pd.notna(r['dist_km_osf_med']) else "-"
        max_o = f"{r['dist_km_osf_max']:.2f}"  if pd.notna(r['dist_km_osf_max']) else "-"
        # flag si radio nuestro << MIROVA
        flag = ""
        if pd.notna(r['dist_km_osf_max']) and r['dist_km_ours_max'] * 1.5 < r['dist_km_osf_max']:
            flag = "🔴 cortamos hits lejanos"
        print(f"{r['volcano']:<22s} {r['dist_km_ours_med']:>7.2f} {r['dist_km_ours_max']:>7.2f} {med_o:>7s} {max_o:>7s}   {flag}")

print()
if D:
    print("=" * 96)
    print(f"DIAGNÓSTICO D — Chaitén (ours n={D['n_ours']}, MIROVA n={D['n_osf']})")
    print("=" * 96)
    print(f"Bins [km]:  0-0.5  0.5-1  1-2  2-3  3-5  5-10  10-20")
    print(f"Ours     :  {' '.join(f'{h:>5d}' for h in D['ours_hot_dist_km_hist'])}")
    print(f"MIROVA   :  {' '.join(f'{h:>5d}' for h in D['osf_hot_dist_km_hist'])}")
    print(f"ΔT mediana (t_max - t_bg) nuestras Chaitén: {D['ours_t_max_minus_bg_med']:.2f} K")

print()
print(f"JSON: {OUT_JSON}")
print(f"PNG:  {OUT_PNG}")
