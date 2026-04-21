"""
S14 Paso 0 — Calibración empírica de k_MIR por sensor contra MIROVA v2.5 (OSF).

Método directo: MIROVA publica `Tot_Lmir_hot` y `Tot_Lmir_bk` junto al VRP final
en cada fila. Reconstruir el coeficiente efectivo que MIROVA usó haciendo
`coef_emp = VRP / (Tot_Lmir_hot - Tot_Lmir_bk)` y comparar contra las fórmulas
candidatas publicadas:

  MODIS 1km     → Coppola 2016a Wooster k=18.9 × A_pix(1e6 m²) =  18,900,000
  VIIRS 750m    → Campus 2022    k=1.97e7 (embebido)          =  19,700,000
  VIIRS 750m    →                k=18.0 × A_pix(562500)       =  10,125,000
  VIIRS 750m    → Di Bella 2024  k=1.11e7                     =  11,100,000
  VIIRS 375m    → Laiolo 2024    k=18.0 × A_pix(140625)       =   2,531,250
  VIIRS 375m    → Di Bella 2024  k=2.48e7                     =  24,800,000

Si el coef_emp de MIROVA coincide (≤1% error) con alguna candidata, esa es la
fórmula que MIROVA implementa.

No requiere overlap temporal entre nuestro pipeline y OSF — es calibración
sobre los números publicados por MIROVA mismo.

Resolución del coeficiente válida para todos los registros = rige en NRT.

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
OUT_JSON = ROOT / "experiments" / "21_results.json"
OUT_PNG  = ROOT / "experiments" / "21_ratio_distribution.png"

CHIL_VOLCANOES = {
    "Láscar", "Chaitén", "Puyehue-Cordón Caulle", "Lastarria", "Villarrica",
    "Isluga", "Copahue", "Planchón-Peteroa", "Llaima", "Chillán, Nevados de",
}

# Fórmulas candidatas (coef efectivo = k × A_pix)
CANDIDATES = {
    "MODIS_1000m": [
        ("Coppola2016_Wooster_k18.9_Apix1e6", 18.9 * 1e6),
        ("Wooster2003_k1.89e7",              1.89e7),
    ],
    "VIIRS_750m": [
        ("Campus2022_k1.97e7",               1.97e7),
        ("Laiolo_k18.0_Apix562500",          18.0 * 562500),
        ("DiBella2024_k1.11e7",              1.11e7),
    ],
    "VIIRS_375m": [
        ("Laiolo2024_k18.0_Apix140625",      18.0 * 140625),
        ("DiBella2024_k2.48e7",              2.48e7),
        ("Wooster2003_k1.89e7",              1.89e7),
    ],
}

def match_candidate(coef_emp, candidates, tol=0.01):
    """Devuelve la candidata cuyo coef efectivo está dentro de tol·100% del empírico."""
    for name, val in candidates:
        if abs(coef_emp - val) / val <= tol:
            return name, val
    return None, None

# --- Carga ---
print(f"[1/3] Cargando OSF v2.5 ({OSF_CSV.name})...")
df = pd.read_csv(OSF_CSV)
sub = df[df["Volc_Name"].isin(CHIL_VOLCANOES)].copy()
sub["delta"] = sub["Tot_Lmir_hot"] - sub["Tot_Lmir_bk"]
sub = sub[sub["delta"] > 0].copy()
sub["coef_emp"] = sub["VRP"] / sub["delta"]
print(f"      filas chilenas con delta>0: {len(sub):,}")

# --- Análisis por resolución ---
print(f"[2/3] Analizando por sensor/resolución...")
results = {}
for res, label in [(1000, "MODIS_1000m"), (750, "VIIRS_750m"), (375, "VIIRS_375m")]:
    grp = sub[sub["Resolution"] == res]
    if len(grp) == 0:
        print(f"      {label}: sin filas, skip")
        continue
    coef = grp["coef_emp"]
    med = float(coef.median())
    q25 = float(coef.quantile(0.25))
    q75 = float(coef.quantile(0.75))
    name, val = match_candidate(med, CANDIDATES[label])
    spread_pct = (q75 - q25) / med * 100 if med > 0 else 0.0
    zenith_var = float(grp.groupby(pd.cut(grp["SatZen"], bins=[0,20,40,60,80]))["coef_emp"].median().std())
    results[label] = {
        "n": int(len(grp)),
        "median_coef": med,
        "q25": q25, "q75": q75,
        "spread_iqr_pct": spread_pct,
        "zenith_bin_stddev_of_median": zenith_var,
        "matched_formula": name,
        "matched_value": val,
        "matched_error_pct": (abs(med - val) / val * 100) if val else None,
    }
    print(f"      {label}: n={len(grp):,}  mediana={med:,.0f}  IQR_spread={spread_pct:.3f}%")
    if name:
        print(f"         → match: {name}  (error {results[label]['matched_error_pct']:.3f}%)")
    else:
        print(f"         → NO match ninguna candidata conocida")
    print(f"         → variabilidad por zenith (std de medianas): {zenith_var:,.0f}")

# --- Test A_pix: nadir fijo vs zenith-corrected ---
# Si MIROVA usara zenith-corrected, el coef_emp NO sería constante (variaría con SatZen).
# Si es constante (spread ~0%) → MIROVA usa A_pix nadir fijo.
print(f"[3/3] Test A_pix nadir vs zenith-corrected...")
for res, label in [(1000, "MODIS_1000m"), (750, "VIIRS_750m"), (375, "VIIRS_375m")]:
    if label not in results:
        continue
    r = results[label]
    if r["spread_iqr_pct"] < 0.1 and r["zenith_bin_stddev_of_median"] < 1000:
        a_pix_mode = "nadir_fijo"
    elif r["zenith_bin_stddev_of_median"] > r["median_coef"] * 0.05:
        a_pix_mode = "zenith_corrected"
    else:
        a_pix_mode = "incierto"
    r["a_pix_mode"] = a_pix_mode
    print(f"      {label}: A_pix_mode = {a_pix_mode}")

# --- PNG ---
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (res, label) in zip(axes, [(1000,"MODIS_1000m"),(750,"VIIRS_750m"),(375,"VIIRS_375m")]):
        grp = sub[sub["Resolution"]==res]
        if len(grp)==0: continue
        coef = grp["coef_emp"]
        ax.hist(coef, bins=100)
        ax.set_title(f"{label}  (n={len(grp):,})")
        ax.set_xlabel("coef_emp = VRP / ΔL_MIR")
        ax.set_ylabel("n")
        for name, val in CANDIDATES[label]:
            ax.axvline(val, lw=1.5, alpha=0.7, ls="--", label=name[:25])
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=100)
    print(f"      PNG: {OUT_PNG.name}")
except Exception as e:
    print(f"      WARN PNG: {e}")

# --- Save JSON ---
out = {
    "experiment": "21_calibrate_k_mir_empirical_via_osf",
    "session": "S14",
    "generated_utc": datetime.utcnow().isoformat() + "Z",
    "method": "reconstruct coef = VRP / (Tot_Lmir_hot - Tot_Lmir_bk) directly on OSF v2.5 rows; match against published formulas",
    "n_rows_total": int(len(sub)),
    "candidates": {k: [{"name":n, "value":v} for n,v in lst] for k,lst in CANDIDATES.items()},
    "results": results,
}
OUT_JSON.parent.mkdir(exist_ok=True, parents=True)
json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# --- Resumen ---
print()
print("=" * 76)
print("RESULTADO Paso 0 — coeficiente k_MIR empírico de MIROVA v2.5")
print("=" * 76)
for label in ["MODIS_1000m", "VIIRS_750m", "VIIRS_375m"]:
    if label not in results: continue
    r = results[label]
    print(f"\n  {label}  (n={r['n']:,}, IQR_spread={r['spread_iqr_pct']:.3f}%)")
    print(f"    coeficiente empírico mediano: {r['median_coef']:>14,.0f}")
    if r["matched_formula"]:
        print(f"    fórmula que lo reproduce:     {r['matched_formula']}")
        print(f"    error:                        {r['matched_error_pct']:.3f}%")
    else:
        print(f"    NO coincide con ninguna candidata publicada")
    print(f"    A_pix mode:                   {r['a_pix_mode']}")

print()
print(f"JSON completo: {OUT_JSON}")
print(f"PNG:            {OUT_PNG}")
