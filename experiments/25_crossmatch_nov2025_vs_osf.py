"""
25_crossmatch_nov2025_vs_osf.py — S15 Paso 1b validación de paridad VRP.

Cross-match evento-a-evento entre nuestras detecciones VIIRS
(data/mirova_equivalent_backfill_nov2025/) y la DB OSF v2.5 MIROVA
(data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv) para Nov 2025.

Criterio de paridad (definido en status_s14_handoff.md):
    ratio mediano de VRP_ours/VRP_osf en [0.8, 1.25] sobre ≥50 pares.

Mapping sensor OSF ↔ local:
    Satellite=3, Resolution=375  → VIIRS_SNPP       (I-band 375m)
    Satellite=4, Resolution=375  → VIIRS_NOAA20     (I-band 375m)
    Satellite=3, Resolution=750  → VIIRS_SNPP_750   (M-band 750m)
    Satellite=4, Resolution=750  → VIIRS_NOAA20_750 (M-band 750m)
    Satellite={1,2}, Res=1000    → MODIS Terra/Aqua (no local en Windows)

Tolerancia temporal: ±15 min (mismo overpass, jitter de granule boundaries).

Output: experiments/25_crossmatch_nov2025.json + .png (scatter por sensor).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
OSF_CSV = ROOT / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
BACKFILL_DIR = ROOT / "data" / "mirova_equivalent_backfill_nov2025"
OUT_JSON = Path(__file__).parent / "25_crossmatch_nov2025.json"
OUT_PNG = Path(__file__).parent / "25_crossmatch_nov2025.png"

# Nombre local → Volc_Name OSF (con acentos UTF-8).
VOLCANO_MAP = {
    "Lascar":     "Láscar",
    "Villarrica": "Villarrica",
    "Copahue":    "Copahue",
    "Chaiten":    "Chaitén",
}

# (OSF Satellite, OSF Resolution) → sensor local.
SENSOR_MAP = {
    (3, 375): "VIIRS_SNPP",
    (4, 375): "VIIRS_NOAA20",
    (3, 750): "VIIRS_SNPP_750",
    (4, 750): "VIIRS_NOAA20_750",
}

WINDOW_MIN = 15  # tolerancia temporal para match


def load_osf_nov2025() -> pd.DataFrame:
    """Carga OSF filtrado a Nov 2025 nocturno para nuestros 4 volcanes."""
    df = pd.read_csv(OSF_CSV)
    df["t"] = pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
    df = df.dropna(subset=["t"])
    targets = set(VOLCANO_MAP.values())
    mask = (
        df["Volc_Name"].isin(targets)
        & (df["t"] >= "2025-11-01")
        & (df["t"] <= "2025-11-30 23:59")
        & (df["Dayflag"] == 0)
    )
    df = df.loc[mask].copy()
    # Unidades → MW, km.
    df["vrp_mw_osf"] = df["VRP"] / 1e6
    df["dist_km_osf"] = df["Max_Dist"] / 1e3
    # Clave sensor local.
    df["sensor_local"] = df.apply(
        lambda r: SENSOR_MAP.get((int(r["Satellite"]), int(r["Resolution"]))), axis=1
    )
    df = df.dropna(subset=["sensor_local"])  # drop MODIS (no backfill local)
    return df


def load_ours() -> pd.DataFrame:
    """Carga nuestros records Nov 2025 desde los JSONs del backfill."""
    rows = []
    for local_name in VOLCANO_MAP:
        f = BACKFILL_DIR / f"{local_name}.json"
        if not f.exists():
            print(f"  [WARN] missing {f.name} — backfill incompleto o aún corriendo")
            continue
        obj = json.loads(f.read_text(encoding="utf-8"))
        for r in obj.get("records", []):
            dt = pd.to_datetime(r.get("datetime_utc"), errors="coerce", utc=True)
            if pd.isna(dt) or dt.year != 2025 or dt.month != 11:
                continue
            rows.append({
                "volcano_local": local_name,
                "volcano_osf":   VOLCANO_MAP[local_name],
                "t":             dt.tz_convert(None),
                "sensor":        r.get("sensor"),
                "vrp_mw_ours":   r.get("vrp_mw", 0.0),
                "dist_km_ours":  r.get("final_hotspot_dist_km"),
                "distance_class": r.get("distance_class"),
            })
    return pd.DataFrame(rows)


def cross_match(osf: pd.DataFrame, ours: pd.DataFrame) -> pd.DataFrame:
    """Match por (Volc_Name, sensor_local, |Δt| ≤ WINDOW_MIN)."""
    pairs = []
    osf_matched_ids = set()
    window = pd.Timedelta(minutes=WINDOW_MIN)

    for _, o in ours.iterrows():
        if o["sensor"] not in set(SENSOR_MAP.values()):
            continue  # solo los sensores que existen en OSF
        cand = osf[
            (osf["Volc_Name"] == o["volcano_osf"])
            & (osf["sensor_local"] == o["sensor"])
            & (osf["t"].between(o["t"] - window, o["t"] + window))
        ]
        if cand.empty:
            pairs.append({**o.to_dict(), "matched": False, "vrp_mw_osf": np.nan,
                         "osf_id": None, "dt_sec": None})
            continue
        # Mejor match = mínima |Δt|.
        cand = cand.assign(dt_abs=(cand["t"] - o["t"]).abs())
        best = cand.sort_values("dt_abs").iloc[0]
        pairs.append({
            **o.to_dict(),
            "matched":     True,
            "vrp_mw_osf":  float(best["vrp_mw_osf"]),
            "osf_id":      int(best["id"]),
            "dt_sec":      (best["t"] - o["t"]).total_seconds(),
        })
        osf_matched_ids.add(int(best["id"]))

    # OSF records NO matched (recall denominator).
    for _, o in osf.iterrows():
        if int(o["id"]) in osf_matched_ids:
            continue
        pairs.append({
            "volcano_local": None,
            "volcano_osf":   o["Volc_Name"],
            "t":             o["t"],
            "sensor":        o["sensor_local"],
            "vrp_mw_ours":   np.nan,
            "dist_km_ours":  np.nan,
            "distance_class": None,
            "matched":       False,
            "vrp_mw_osf":    float(o["vrp_mw_osf"]),
            "osf_id":        int(o["id"]),
            "dt_sec":        None,
        })
    return pd.DataFrame(pairs)


def compute_metrics(pairs: pd.DataFrame) -> dict:
    """Métricas por sensor + global."""
    out = {"by_sensor": {}, "global": {}}

    def _block(sub: pd.DataFrame) -> dict:
        matched = sub[sub["matched"]].dropna(subset=["vrp_mw_ours", "vrp_mw_osf"])
        matched = matched[matched["vrp_mw_osf"] > 0]  # evitar /0
        n_matched = len(matched)
        # Nuestros totales = nuestros registros no-nulos con vrp_mw>0 filtrados a
        # distance_class!=far (far son lejanos, no son el volcán).
        ours_real = sub[(sub["volcano_local"].notna())
                        & (sub["vrp_mw_ours"] > 0)
                        & (sub["distance_class"] != "far")]
        osf_total = sub[sub["osf_id"].notna()]["osf_id"].nunique()
        n_ours = len(ours_real)

        res = {
            "n_pairs_matched":  n_matched,
            "n_ours_summit":    n_ours,
            "n_osf_total":      int(osf_total),
            "recall":           n_matched / osf_total if osf_total else None,
            "precision":        n_matched / n_ours if n_ours else None,
        }
        if n_matched >= 3:
            r = matched["vrp_mw_ours"] / matched["vrp_mw_osf"]
            res["ratio_median"] = float(r.median())
            res["ratio_p25"]    = float(r.quantile(0.25))
            res["ratio_p75"]    = float(r.quantile(0.75))
            res["ratio_mean"]   = float(r.mean())
            # Spearman sobre VRP en log (rango amplio).
            rho, p = stats.spearmanr(np.log(matched["vrp_mw_ours"]),
                                      np.log(matched["vrp_mw_osf"]))
            res["spearman_rho"]     = float(rho)
            res["spearman_pvalue"]  = float(p)
            res["parity_ok"]    = 0.8 <= res["ratio_median"] <= 1.25 and n_matched >= 50
        return res

    for sensor in sorted(pairs["sensor"].dropna().unique()):
        out["by_sensor"][sensor] = _block(pairs[pairs["sensor"] == sensor])
    out["global"] = _block(pairs)
    return out


def plot_scatter(pairs: pd.DataFrame, out_path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    matched = pairs[pairs["matched"]].dropna(subset=["vrp_mw_ours", "vrp_mw_osf"])
    matched = matched[matched["vrp_mw_osf"] > 0]
    sensors = sorted(matched["sensor"].unique())
    fig, axes = plt.subplots(1, max(len(sensors), 1), figsize=(5 * max(len(sensors), 1), 5),
                             squeeze=False)
    for ax, s in zip(axes[0], sensors):
        sub = matched[matched["sensor"] == s]
        ax.scatter(sub["vrp_mw_osf"], sub["vrp_mw_ours"], s=18, alpha=0.7)
        lo = max(1e-3, min(sub[["vrp_mw_osf", "vrp_mw_ours"]].min().min(), 0.01))
        hi = max(sub[["vrp_mw_osf", "vrp_mw_ours"]].max().max(), 1.0)
        ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="1:1")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel("VRP OSF (MW)"); ax.set_ylabel("VRP ours (MW)")
        ax.set_title(f"{s}  n={len(sub)}")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
    fig.suptitle("S15 Paso 1b — VRP Nov 2025 ours vs MIROVA OSF v2.5")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    print(f"  wrote {out_path}")


def main():
    if not OSF_CSV.exists():
        print(f"ERROR: OSF CSV no existe: {OSF_CSV}")
        sys.exit(1)
    if not BACKFILL_DIR.exists() or not any(BACKFILL_DIR.glob("*.json")):
        print(f"WARN: backfill vacío en {BACKFILL_DIR}. ¿Terminó el backfill? Continuando con lo que haya.")

    print("Cargando OSF Nov 2025...")
    osf = load_osf_nov2025()
    print(f"  OSF rows: {len(osf)}")

    print("Cargando nuestros records...")
    ours = load_ours()
    print(f"  ours rows (Nov 2025, todos los sensores/clases): {len(ours)}")

    print("Cross-match ±15 min...")
    pairs = cross_match(osf, ours)
    print(f"  total filas pairs: {len(pairs)}")
    print(f"  matched: {pairs['matched'].sum()}")

    print("Métricas...")
    metrics = compute_metrics(pairs)

    OUT_JSON.write_text(json.dumps({
        "config": {
            "osf_csv":      str(OSF_CSV.name),
            "backfill_dir": str(BACKFILL_DIR.relative_to(ROOT)),
            "window_min":   WINDOW_MIN,
            "date_range":   ["2025-11-01", "2025-11-30"],
            "volcanoes":    list(VOLCANO_MAP.keys()),
        },
        "metrics": metrics,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {OUT_JSON}")

    if pairs["matched"].sum() >= 3:
        plot_scatter(pairs, OUT_PNG)

    # Summary tabular a stdout.
    print("\n=== RESUMEN POR SENSOR ===")
    for s, m in metrics["by_sensor"].items():
        rm = m.get("ratio_median")
        print(f"{s:22s} n={m['n_pairs_matched']:3d}  recall={m['recall']}  "
              f"precision={m['precision']}  ratio_med={rm}")
    g = metrics["global"]
    print(f"\nGLOBAL n={g['n_pairs_matched']} "
          f"ratio_med={g.get('ratio_median')} parity_ok={g.get('parity_ok')}")


if __name__ == "__main__":
    main()
