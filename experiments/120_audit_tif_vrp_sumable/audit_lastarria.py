"""Auditoria del hallazgo S33+ "TIF MIROVA != VRP sumable".

Metodo R2 del agente S69: para un evento Lastarria con TIF MIROVA disponible,
calcular el centroide ponderado de los top-N pixels del TIF y comparar contra
el VRP y la distancia que MIROVA reporta para ese mismo overpass.

Adaptaciones vs plan original:
  - Los KMZ MIROVA son GroundOverlay-only (no Placemark/Point/header VRP).
    Inspeccion directa: ningun KMZ tiene texto "VRP" ni "MW".
    Ground truth correcto = CSV consolidado MIROVA (registro_vrp_consolidado.csv).
  - Match por timestamp exacto entre nombre TIF (YYYYMMDD_HHMMSS) y
    Fecha_Satelite_UTC del CSV.
  - Distancia de comparacion: haversine(top10_centroid -> vent_lat,vent_lon)
    contra CSV.Distancia_km. VRP de comparacion: top10_sum_mw vs CSV.VRP_MW.

Verdict binario:
  - REFUTADO: ratio top10/CSV_VRP en [0.5, 2.0] en >=3/5 casos -> TIF es sumable.
  - CONFIRMADO: ratio >>10x consistente -> TIF NO es sumable como VRP per-pixel.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd
import rasterio

# Rutas relativas al worktree S70-0
HERE = Path(__file__).parent
WORKTREE_ROOT = HERE.parent.parent  # VRP-Chile-s70/
TIF_ARCHIVE = WORKTREE_ROOT.parent / "mirova-tif-archive"
TIF_DIR = TIF_ARCHIVE / "data" / "tif" / "Lastarria"
KMZ_DIR = TIF_ARCHIVE / "data" / "kmz" / "Lastarria"
CSV_PATH = WORKTREE_ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
RESULTS_PATH = HERE / "results.json"

# Lastarria vent (volcanoes.yaml)
VENT_LAT = -25.168
VENT_LON = -68.507


# ---------------------------------------------------------------------------
# TIF / KMZ readers
# ---------------------------------------------------------------------------

def load_tif(path: Path):
    """Lee TIF y devuelve (array, transform). NaNs convertidos a 0."""
    with rasterio.open(path) as src:
        arr = src.read(1)
        transform = src.transform
    arr = np.where(np.isnan(arr), 0.0, arr)
    return arr, transform


def parse_kmz_latlonbox(kmz_path: Path) -> dict:
    """Extrae LatLonBox del KMZ (GroundOverlay-only). No hay Placemark/Point/VRP."""
    with zipfile.ZipFile(kmz_path) as zf:
        kml_name = next(n for n in zf.namelist() if n.endswith(".kml"))
        kml = zf.read(kml_name).decode("utf-8", errors="replace")
    out = {
        "north": None, "south": None, "east": None, "west": None,
        "has_placemark": "<Placemark" in kml,
        "has_vrp_header": "VRP" in kml.upper() and "MW" in kml.upper(),
    }
    for tag in ("north", "south", "east", "west"):
        m = re.search(rf"<{tag}>\s*([-\d.]+)\s*</{tag}>", kml)
        if m:
            out[tag] = float(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Metodo R2 S69: top-N pixels ponderado
# ---------------------------------------------------------------------------

def top_n_centroid(arr: np.ndarray, transform, n: int = 10):
    """Centroide ponderado de los top-N pixels con valor positivo.

    Devuelve (lat_centroid, lon_centroid, total_mw, n_used).
    """
    flat = arr.flatten()
    pos_idx = np.where(flat > 0)[0]
    if len(pos_idx) == 0:
        return None, None, 0.0, 0
    n_used = min(n, len(pos_idx))
    # argsort sobre los valores positivos, tomar los n_used mayores
    top_pos = pos_idx[np.argsort(flat[pos_idx])[-n_used:]]
    rows, cols = np.unravel_index(top_pos, arr.shape)
    weights = flat[top_pos]
    xs, ys = rasterio.transform.xy(transform, rows.tolist(), cols.tolist())
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    lon_c = float((xs * weights).sum() / weights.sum())
    lat_c = float((ys * weights).sum() / weights.sum())
    return lat_c, lon_c, float(weights.sum()), int(n_used)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))


# ---------------------------------------------------------------------------
# Matching TIF <-> CSV
# ---------------------------------------------------------------------------

def parse_tif_timestamp(name: str) -> str | None:
    """Extrae timestamp del nombre TIF: '20260509_054202_VIIRS375.tif' -> '2026-05-09 05:42:02'."""
    m = re.match(r"(\d{8})_(\d{6})_VIIRS375", name)
    if not m:
        return None
    date, hms = m.group(1), m.group(2)
    return f"{date[:4]}-{date[4:6]}-{date[6:8]} {hms[:2]}:{hms[2:4]}:{hms[4:6]}"


def load_mirova_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    last = df[df["Volcan"].str.contains("Lastarria", case=False, na=False)]
    return last[last["Sensor"] == "VIIRS375"].copy()


# ---------------------------------------------------------------------------
# Audit per case
# ---------------------------------------------------------------------------

def audit_case(tif_path: Path, kmz_path: Path, csv_df: pd.DataFrame) -> dict:
    arr, transform = load_tif(tif_path)
    lat_top10, lon_top10, mw_top10, n_used = top_n_centroid(arr, transform, n=10)
    full_sum_mw = float(arr[arr > 0].sum())
    full_pos_pixels = int((arr > 0).sum())
    full_max_mw = float(arr.max())

    # KMZ box (validar georef TIF dentro de box)
    kmz_box = parse_kmz_latlonbox(kmz_path)
    tif_inside_box = None
    if kmz_box["north"] is not None and lat_top10 is not None:
        tif_inside_box = bool(
            kmz_box["south"] <= lat_top10 <= kmz_box["north"]
            and kmz_box["west"] <= lon_top10 <= kmz_box["east"]
        )

    # Match contra CSV
    ts_iso = parse_tif_timestamp(tif_path.name)
    csv_match = csv_df[csv_df["Fecha_Satelite_UTC"] == ts_iso]
    csv_vrp_mw = None
    csv_dist_km = None
    csv_tipo = None
    if len(csv_match) > 0:
        r = csv_match.iloc[0]
        csv_vrp_mw = float(r["VRP_MW"])
        csv_dist_km = float(r["Distancia_km"])
        csv_tipo = str(r["Tipo_Registro"])

    # Distancia top10_centroid -> vent
    dist_top10_to_vent_km = None
    if lat_top10 is not None:
        dist_top10_to_vent_km = haversine_km(lat_top10, lon_top10, VENT_LAT, VENT_LON)

    # Drift centroide vs MIROVA-reported distance (no tenemos cluster_lat/lon,
    # comparamos magnitudes de distancia al vent).
    drift_km = None
    if csv_dist_km is not None and dist_top10_to_vent_km is not None:
        drift_km = abs(dist_top10_to_vent_km - csv_dist_km)

    ratio_mw = None
    if csv_vrp_mw is not None and csv_vrp_mw > 0 and mw_top10 > 0:
        ratio_mw = mw_top10 / csv_vrp_mw

    return {
        "tif": tif_path.name,
        "kmz": kmz_path.name,
        "ts_iso": ts_iso,
        "top10_centroid_lat": lat_top10,
        "top10_centroid_lon": lon_top10,
        "top10_sum_mw": mw_top10,
        "top10_n_used": n_used,
        "full_tif_sum_mw": full_sum_mw,
        "full_tif_pos_pixels": full_pos_pixels,
        "full_tif_max_mw": full_max_mw,
        "kmz_latlonbox": kmz_box,
        "kmz_has_placemark": kmz_box["has_placemark"],
        "kmz_has_vrp_header": kmz_box["has_vrp_header"],
        "tif_centroid_inside_kmz_box": tif_inside_box,
        "csv_vrp_mw": csv_vrp_mw,
        "csv_dist_km": csv_dist_km,
        "csv_tipo": csv_tipo,
        "dist_top10_to_vent_km": dist_top10_to_vent_km,
        "drift_km_top10_vs_csv": drift_km,
        "ratio_top10_vs_csv_vrp": ratio_mw,
    }


# ---------------------------------------------------------------------------
# Main: 5 casos con TIF + KMZ + CSV match
# ---------------------------------------------------------------------------

def main():
    csv_df = load_mirova_csv()
    print(f"CSV Lastarria VIIRS375: {len(csv_df)} filas")
    print(f"Date range: {csv_df['Fecha_Satelite_UTC'].min()} -> {csv_df['Fecha_Satelite_UTC'].max()}")

    # Iterar TIFs y quedarse con los que tienen match en CSV
    tifs = sorted(TIF_DIR.glob("*VIIRS375.tif"))
    print(f"TIFs disponibles: {len(tifs)}")

    matched = []
    for tif in tifs:
        ts = parse_tif_timestamp(tif.name)
        if ts is None:
            continue
        m = csv_df[csv_df["Fecha_Satelite_UTC"] == ts]
        if len(m) > 0:
            matched.append((tif, m.iloc[0]))

    print(f"TIFs con match exacto en CSV: {len(matched)}")

    # Preferir ALERTA_TERMICA (VRP > 0) sobre RUTINA (VRP = 0) para que ratio sea computable
    alerta = [(t, r) for t, r in matched if r["Tipo_Registro"] == "ALERTA_TERMICA"]
    rutina = [(t, r) for t, r in matched if r["Tipo_Registro"] != "ALERTA_TERMICA"]
    print(f"  ALERTA_TERMICA: {len(alerta)}, RUTINA: {len(rutina)}")

    # Tomar 5 casos: priorizar ALERTAs (los que importan para verdict)
    chosen = alerta[-5:] if len(alerta) >= 5 else alerta + rutina[: 5 - len(alerta)]
    if len(chosen) == 0:
        print("BLOCKED: ningun TIF con match CSV")
        return

    results = []
    for tif, _ in chosen:
        kmz = KMZ_DIR / tif.name.replace(".tif", ".kmz")
        if not kmz.exists():
            results.append({"tif": tif.name, "error": "kmz missing"})
            print(f"  SKIP {tif.name}: KMZ paralelo no existe")
            continue
        try:
            r = audit_case(tif, kmz, csv_df)
            results.append(r)
            print(f"\n{tif.name}  ({r['csv_tipo']})")
            print(f"  TIF total:   sum={r['full_tif_sum_mw']:.2f} MW  "
                  f"pos_pix={r['full_tif_pos_pixels']}  max={r['full_tif_max_mw']:.4f}")
            print(f"  TIF top10:   sum={r['top10_sum_mw']:.4f} MW  "
                  f"centroide=({r['top10_centroid_lat']:.4f}, {r['top10_centroid_lon']:.4f})")
            print(f"  MIROVA CSV:  VRP={r['csv_vrp_mw']} MW  dist={r['csv_dist_km']} km")
            print(f"  dist top10->vent: {r['dist_top10_to_vent_km']:.2f} km   "
                  f"drift vs CSV: {r['drift_km_top10_vs_csv']:.2f} km")
            print(f"  ratio top10/CSV_VRP: {r['ratio_top10_vs_csv_vrp']}")
            print(f"  KMZ has_placemark={r['kmz_has_placemark']}  "
                  f"has_vrp_header={r['kmz_has_vrp_header']}  "
                  f"tif_in_box={r['tif_centroid_inside_kmz_box']}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {tif.name}: {e}")
            results.append({"tif": tif.name, "error": str(e)})

    # Verdict agregado
    valid = [r for r in results if r.get("ratio_top10_vs_csv_vrp") is not None]
    if valid:
        ratios = [r["ratio_top10_vs_csv_vrp"] for r in valid]
        drifts = [r["drift_km_top10_vs_csv"] for r in valid if r.get("drift_km_top10_vs_csv") is not None]
        in_band = sum(1 for x in ratios if 0.5 <= x <= 2.0)
        verdict = {
            "n_cases_valid": len(valid),
            "ratio_top10_vs_csv_vrp_median": float(np.median(ratios)),
            "ratio_top10_vs_csv_vrp_min": float(np.min(ratios)),
            "ratio_top10_vs_csv_vrp_max": float(np.max(ratios)),
            "drift_km_median": float(np.median(drifts)) if drifts else None,
            "n_in_band_0p5_to_2": in_band,
            "n_above_10x": sum(1 for x in ratios if x > 10.0),
            "verdict_binario": (
                "REFUTADO_TIF_ES_SUMABLE"
                if in_band >= max(3, int(0.6 * len(valid)))
                else "CONFIRMADO_TIF_NO_ES_SUMABLE"
            ),
        }
    else:
        verdict = {"n_cases_valid": 0, "verdict_binario": "INDETERMINADO_NO_MATCHES"}

    summary = {"verdict": verdict, "cases": results}
    RESULTS_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 60)
    print("VERDICT AGREGADO:")
    print(json.dumps(verdict, indent=2, default=str))
    print(f"\nResultados guardados en: {RESULTS_PATH}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
