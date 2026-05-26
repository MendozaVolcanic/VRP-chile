"""
F-S81-A Fase 1.1 — Clasificar FPs MODIS por path/cluster/distancia/VRP.

Input: experiments/_s81_v2_out/fp_genuine_all.csv (2768 FPs B+C agregados)
       data/mirova_equivalent/<volcan>.json (records con final_hotspot_source,
       n_vent_pixels, triggered_test1, primary_cluster, etc.)

Output:
  experiments/_s82_intra_radio/fase1_1_modis_classified.csv
  experiments/_s82_intra_radio/fase1_1_summary.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FP_CSV = ROOT / "experiments" / "_s81_v2_out" / "fp_genuine_all.csv"
DATA_DIR = ROOT / "data" / "mirova_equivalent"
OUT_DIR = ROOT / "experiments" / "_s82_intra_radio"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_records_by_volcano() -> dict[str, dict[str, dict]]:
    """Devuelve {volcan: {timestamp_iso: record}} para MODIS records."""
    by_vol: dict[str, dict[str, dict]] = {}
    for jf in DATA_DIR.glob("*.json"):
        try:
            d = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"WARN read {jf.name}: {exc}", file=sys.stderr)
            continue
        recs = d.get("records", []) if isinstance(d, dict) else []
        vol = jf.stem
        idx: dict[str, dict] = {}
        for r in recs:
            sensor = r.get("sensor", "")
            if "MODIS" not in sensor.upper():
                continue
            ts = r.get("datetime_utc")
            if not ts:
                continue
            idx[str(ts).replace("T", " ")[:16]] = r
        by_vol[vol] = idx
    return by_vol


def normalize_ts(ts: str) -> str:
    """Truncate to minute precision (records store 'YYYY-MM-DD HH:MM')."""
    return str(ts).replace("T", " ")[:16]


def classify_record(rec: dict) -> dict:
    """Extrae proxies del path/mecanismo desde un record MODIS."""
    fhs = rec.get("final_hotspot_source")
    triggered_test1 = bool(rec.get("triggered_test1", False))
    n_vent = int(rec.get("n_vent_pixels") or 0)
    n_anom = int(rec.get("n_anomalous_pixels") or 0)
    n_clusters = int(rec.get("n_hotspots_clustered") or 0)
    pc = rec.get("primary_cluster") or {}
    pc_npix = int(pc.get("n_pixels") or 0)
    pc_vrp = float(pc.get("vrp_mw") or 0.0)
    pc_dist = pc.get("centroid_dist_km")

    # Path A/B/D contribution (Coppola SP426.5 + S15 paths)
    diag_bt = int(rec.get("diag_n_bt_path") or 0)
    diag_nti = int(rec.get("diag_n_nti_path") or 0)
    diag_dnti = int(rec.get("diag_n_dnti_ctx_path") or 0)
    paths_active = []
    if diag_bt > 0:
        paths_active.append("A_BT")
    if diag_nti > 0:
        paths_active.append("B_NTI")
    if diag_dnti > 0:
        paths_active.append("D_dNTIctx")
    path_combo = "+".join(paths_active) if paths_active else "none"

    # Bucket path
    if fhs == "test1":
        path_bucket = "test1_integrated"
    elif fhs == "vent" or n_vent > 0:
        path_bucket = "vent_path"
    elif fhs == "cluster_rescue":
        path_bucket = "cluster_rescue"
    elif fhs == "eruption":
        path_bucket = "eruption_scene"
    else:
        path_bucket = f"other({fhs})"

    # Cluster size bucket (primary_cluster.n_pixels)
    if pc_npix == 0:
        cluster_bucket = "no_primary_cluster"
    elif pc_npix == 1:
        cluster_bucket = "1px"
    elif pc_npix <= 3:
        cluster_bucket = "2-3px"
    elif pc_npix <= 10:
        cluster_bucket = "4-10px"
    elif pc_npix <= 50:
        cluster_bucket = "11-50px"
    else:
        cluster_bucket = "50+px"

    return dict(
        final_hotspot_source=fhs,
        path_bucket=path_bucket,
        triggered_test1=triggered_test1,
        n_vent_pixels=n_vent,
        n_anom_px=n_anom,
        n_clusters=n_clusters,
        pc_n_pix=pc_npix,
        pc_vrp_mw=pc_vrp,
        pc_dist_km=pc_dist,
        cluster_bucket=cluster_bucket,
        diag_n_bt=diag_bt,
        diag_n_nti=diag_nti,
        diag_n_dnti=diag_dnti,
        path_combo=path_combo,
    )


def vrp_bucket(v: float) -> str:
    if v < 1:
        return "<1"
    if v < 10:
        return "1-10"
    if v < 100:
        return "10-100"
    if v < 1000:
        return "100-1000"
    return "1000+"


def dist_bucket(d: float | None) -> str:
    if d is None:
        return "unknown"
    if d < 2:
        return "0-2"
    if d < 5:
        return "2-5"
    if d < 10:
        return "5-10"
    if d < 20:
        return "10-20"
    return "20+"


def main() -> None:
    print("Loading FPs CSV...")
    fps = pd.read_csv(FP_CSV)
    fps_modis = fps[fps["sensor"] == "MODIS"].copy()
    print(f"  total FPs: {len(fps)}, MODIS subset: {len(fps_modis)}")

    print("Loading mirova_equivalent JSONs (MODIS records)...")
    by_vol = load_records_by_volcano()
    print(f"  volcanoes loaded: {len(by_vol)}")

    enriched_rows = []
    miss_count = 0
    for _, row in fps_modis.iterrows():
        vol = row["volcan"]
        ts = normalize_ts(row["dt"])
        rec = by_vol.get(vol, {}).get(ts)
        if rec is None:
            miss_count += 1
            enriched = dict(
                final_hotspot_source=None,
                path_bucket="MISSING_RECORD",
                triggered_test1=False,
                n_vent_pixels=0,
                n_anom_px=0,
                n_clusters=0,
                pc_n_pix=0,
                pc_vrp_mw=0.0,
                pc_dist_km=None,
                cluster_bucket="MISSING_RECORD",
            )
        else:
            enriched = classify_record(rec)
        out = dict(row)
        out.update(enriched)
        out["vrp_bucket"] = vrp_bucket(float(row["ours_vrp_mw"]))
        out["dist_bucket"] = dist_bucket(float(row["ours_dist_km"]))
        enriched_rows.append(out)

    print(f"  records missing in JSONs: {miss_count} (likely timestamp mismatch)")

    df = pd.DataFrame(enriched_rows)
    out_csv = OUT_DIR / "fase1_1_modis_classified.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv} ({len(df)} rows)")

    # ----- Summary stats -----
    lines = []
    lines.append("# F-S81-A Fase 1.1 — Clasificación FPs MODIS\n")
    lines.append(f"**Input**: {FP_CSV.name} ({len(fps)} FPs totales, {len(fps_modis)} MODIS)\n")
    lines.append(f"**Records sin match en JSONs**: {miss_count} ({100*miss_count/len(fps_modis):.1f}%)\n")
    lines.append("\n## Distribución por `path_bucket` (proxy del path que disparó)\n")
    lines.append("| Path | N | % |")
    lines.append("|---|---:|---:|")
    pb_counts = df["path_bucket"].value_counts()
    for p, n in pb_counts.items():
        lines.append(f"| {p} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Distribución por `cluster_bucket` (primary_cluster.n_pixels)\n")
    lines.append("| Cluster size | N | % |")
    lines.append("|---|---:|---:|")
    for c, n in df["cluster_bucket"].value_counts().items():
        lines.append(f"| {c} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Distribución por `dist_bucket` (ours_dist_km)\n")
    lines.append("| Distancia [km] | N | % |")
    lines.append("|---|---:|---:|")
    for d, n in df["dist_bucket"].value_counts().sort_index().items():
        lines.append(f"| {d} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Distribución por `vrp_bucket` (ours_vrp_mw)\n")
    lines.append("| VRP [MW] | N | % |")
    lines.append("|---|---:|---:|")
    for v, n in df["vrp_bucket"].value_counts().items():
        lines.append(f"| {v} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Distribución por `ours_dist_class`\n")
    lines.append("| Distance class | N | % |")
    lines.append("|---|---:|---:|")
    for d, n in df["ours_dist_class"].value_counts().items():
        lines.append(f"| {d} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Distribución por `path_combo` (Path A_BT / B_NTI / D_dNTIctx activos)\n")
    lines.append("| Path combo | N | % |")
    lines.append("|---|---:|---:|")
    for p, n in df["path_combo"].value_counts().items():
        lines.append(f"| {p} | {n} | {100*n/len(df):.1f}% |")

    lines.append("\n## Cross-tab: path_combo × dist_bucket\n")
    lines.append(pd.crosstab(df["path_combo"], df["dist_bucket"]).to_markdown())

    lines.append("\n## Cross-tab: path_combo × cluster_bucket\n")
    lines.append(pd.crosstab(df["path_combo"], df["cluster_bucket"]).to_markdown())

    lines.append("\n## Cross-tab: path_bucket × cluster_bucket\n")
    ct = pd.crosstab(df["path_bucket"], df["cluster_bucket"])
    lines.append(ct.to_markdown())

    lines.append("\n## Cross-tab: path_bucket × dist_bucket\n")
    ct2 = pd.crosstab(df["path_bucket"], df["dist_bucket"])
    lines.append(ct2.to_markdown())

    lines.append("\n## Cross-tab: cluster_bucket × dist_bucket\n")
    ct3 = pd.crosstab(df["cluster_bucket"], df["dist_bucket"])
    lines.append(ct3.to_markdown())

    lines.append("\n## FPs por volcán (top 10)\n")
    lines.append("| Volcán | N FPs |")
    lines.append("|---|---:|")
    for vol, n in df["volcan"].value_counts().head(10).items():
        lines.append(f"| {vol} | {n} |")

    lines.append("\n## Distribución `mirova` tag\n")
    lines.append("| MIROVA tag | N | % |")
    lines.append("|---|---:|---:|")
    # Bucket mirova tags: NO_RECORD vs RUTINA vs ALERTA_TERMICA etc.
    df["mirova_bucket"] = df["mirova"].str.split("(").str[0]
    for m, n in df["mirova_bucket"].value_counts().items():
        lines.append(f"| {m} | {n} | {100*n/len(df):.1f}% |")

    out_md = OUT_DIR / "fase1_1_summary.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_md}")

    # Console summary
    print("\n=== TOP-LEVEL FINDINGS ===")
    print(f"Total MODIS FPs: {len(df)}")
    print(f"Path bucket dominante: {pb_counts.idxmax()} = {pb_counts.max()} ({100*pb_counts.max()/len(df):.1f}%)")
    print(f"Cluster bucket dominante: {df['cluster_bucket'].value_counts().idxmax()}")
    print(f"Dist bucket dominante: {df['dist_bucket'].value_counts().idxmax()}")


if __name__ == "__main__":
    main()
