"""R2 retroactivo Chaiten (S70-1 T1) sobre 2026-05-18 05:30 UTC VIIRS_NOAA20.

Aplicación del método R2 S69 VERDADERO (validado en
`experiments/120_audit_tif_vrp_sumable/audit_lastarria_real_method.py`) a un
caso ALERTA_TERMICA reciente de Chaiten, post-adopción S63 de
`local_kernel_bg: true`.

Contexto físico (geólogo)
-------------------------

Chaiten quedó dentro del grupo Tier A "Muy Bajo" (ΔT < 12 K, baja diferencia
térmica del domo activo frente al background invernal patagónico). Para esos
volcanes mostramos en S61-S63 que el background regional ROI por defecto
sobre-estimaba el calor de fondo, dejando los pixels reales sub-umbral. El
fix `local_kernel_bg: true` cambia el cálculo del fondo a un kernel local
fuera del cráter; resultado agregado S63 fue ratio LEGACY 9.78× → NEW 2.23×
(-77%) sobre 20 ALERTAS A/B.

Esa adopción se hizo SIN R2 pixel-level previo. Acá replicamos el método R2
S69 verdadero (ratio magnitud + drift geométrico vs centroide TIF top10 <3km
del vent) sobre una ALERTA reciente para validar que el ajuste no
sólo agrega bien, sino que también acierta pixel por pixel contra MIROVA.

Caso elegido
------------

- Volcán: Chaiten (vent -42.8344815, -72.6528875)
- ALERTA MIROVA: 2026-05-18 05:30:01 VIIRS375 VRP=0.22 MW dist=0.75 km
- Nuestro record: 2026-05-18 05:30 VIIRS_NOAA20, distance_class=summit
- TIF paralelo: `data/tif/Chaiten/20260518_053001_VIIRS375.tif`

Método (replicado de S69)
-------------------------

1. Magnitud: ratio `pc.vrp_mw / MIROVA.VRP_MW`. Banda [0.5, 2.0] aceptable.
2. Geometría: centroide ponderado de los top-10 pixels del TIF restringidos
   a <=3 km del vent, comparado contra `pc.centroid_lat/lon` del JSON.
   Tolerancia plan: drift < 2 km.

NO hardcodeamos `pc.centroid` ni `pc.vrp_mw`: se leen dinámicamente del
JSON. La validación es independiente.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

HERE = Path(__file__).parent
WORKTREE_ROOT = HERE.parent.parent  # VRP-Chile-s70/
TIF_ARCHIVE = WORKTREE_ROOT.parent / "mirova-tif-archive"
TIF_PATH = TIF_ARCHIVE / "data" / "tif" / "Chaiten" / "20260518_053001_VIIRS375.tif"
CHAITEN_JSON = WORKTREE_ROOT / "data" / "mirova_equivalent" / "Chaiten.json"
CSV_PATH = WORKTREE_ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
RESULTS_PATH = HERE / "results.json"

# Chaiten vent (volcanoes.yaml)
VENT_LAT = -42.8344815
VENT_LON = -72.6528875

# Caso a auditar
TARGET_DATETIME = "2026-05-18 05:30"
TARGET_SENSOR = "VIIRS_NOAA20"  # VIIRS375 en MIROVA CSV
MIROVA_CSV_TIMESTAMP = "2026-05-18 05:30:01"
MIROVA_SENSOR_CSV = "VIIRS375"

# Referencia agregada S63 (no es target per-record, solo informativa)
TARGET_S63_AGGREGATE_RATIO = 2.23  # ratio mediano A/B post-adopción


def haversine_km(lat1, lon1, lat2, lon2):
    """Haversine en km, escalar o vector."""
    R = 6371.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(np.asarray(lat2) - np.asarray(lat1))
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def top_n_centroid_near_vent(
    tif_path: Path,
    vent_lat: float,
    vent_lon: float,
    max_km: float = 3.0,
    n: int = 10,
) -> dict:
    """Centroide ponderado top-N pixels del TIF restringido a max_km del vent."""
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        transform = src.transform
    arr = np.where(np.isnan(arr), 0.0, arr)

    rows, cols = np.where(arr > 0)
    if len(rows) == 0:
        return {
            "lat": None, "lon": None, "sum_mw": 0.0, "n_used": 0,
            "n_positive_pixels_full": 0,
            "n_positive_pixels_within_max_km": 0,
        }

    xs_all, ys_all = rasterio.transform.xy(transform, rows.tolist(), cols.tolist())
    xs_all = np.asarray(xs_all, dtype=float)  # lon
    ys_all = np.asarray(ys_all, dtype=float)  # lat
    vals_all = arr[rows, cols]

    dists = haversine_km(ys_all, xs_all, vent_lat, vent_lon)
    near = dists <= max_km
    n_pos_full = int(len(rows))
    n_pos_near = int(near.sum())

    if n_pos_near == 0:
        return {
            "lat": None, "lon": None, "sum_mw": 0.0, "n_used": 0,
            "n_positive_pixels_full": n_pos_full,
            "n_positive_pixels_within_max_km": 0,
        }

    xs_n = xs_all[near]
    ys_n = ys_all[near]
    vals_n = vals_all[near]
    dists_n = dists[near]

    # Top-N por valor
    n_used = min(n, len(vals_n))
    top_idx = np.argsort(vals_n)[-n_used:]
    xs_t = xs_n[top_idx]
    ys_t = ys_n[top_idx]
    vals_t = vals_n[top_idx]
    dists_t = dists_n[top_idx]

    lon_c = float((xs_t * vals_t).sum() / vals_t.sum())
    lat_c = float((ys_t * vals_t).sum() / vals_t.sum())
    return {
        "lat": lat_c,
        "lon": lon_c,
        "sum_mw": float(vals_t.sum()),
        "n_used": int(n_used),
        "n_positive_pixels_full": n_pos_full,
        "n_positive_pixels_within_max_km": n_pos_near,
        "top_values_min": float(vals_t.min()),
        "top_values_max": float(vals_t.max()),
        "top_dists_km_min": float(dists_t.min()),
        "top_dists_km_max": float(dists_t.max()),
    }


def find_pipeline_record() -> dict:
    """Encuentra el record de Chaiten.json para 2026-05-18 05:30 VIIRS_NOAA20."""
    with open(CHAITEN_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"] if isinstance(data, dict) and "records" in data else data
    for r in records:
        if r.get("datetime_utc") == TARGET_DATETIME and r.get("sensor") == TARGET_SENSOR:
            return r
    raise RuntimeError(
        f"Record no encontrado: datetime={TARGET_DATETIME} sensor={TARGET_SENSOR}"
    )


def find_mirova_csv_row() -> dict:
    """Encuentra la fila MIROVA CSV para 2026-05-18 05:30:01 VIIRS375 Chaiten."""
    df = pd.read_csv(CSV_PATH)
    chait = df[df["Volcan"].str.contains("Chait", case=False, na=False)]
    chait = chait[chait["Sensor"] == MIROVA_SENSOR_CSV]
    m = chait[chait["Fecha_Satelite_UTC"] == MIROVA_CSV_TIMESTAMP]
    if len(m) == 0:
        raise RuntimeError(f"MIROVA CSV: no hay match para {MIROVA_CSV_TIMESTAMP}")
    r = m.iloc[0]
    return {
        "Fecha_Satelite_UTC": str(r["Fecha_Satelite_UTC"]),
        "VRP_MW": float(r["VRP_MW"]),
        "Distancia_km": float(r["Distancia_km"]),
        "Tipo_Registro": str(r["Tipo_Registro"]),
    }


def main():
    print("=" * 70)
    print("R2 RETROACTIVO CHAITEN — 2026-05-18 05:30 UTC (S70-1 T1)")
    print("=" * 70)

    # 0. Verificar paths
    print(f"\nTIF:           {TIF_PATH}")
    print(f"               exists: {TIF_PATH.exists()}")
    print(f"Chaiten.json:  {CHAITEN_JSON}")
    print(f"               exists: {CHAITEN_JSON.exists()}")
    print(f"MIROVA CSV:    {CSV_PATH}")
    print(f"               exists: {CSV_PATH.exists()}")

    if not TIF_PATH.exists():
        raise SystemExit("BLOCKED: TIF no existe")
    if not CHAITEN_JSON.exists():
        raise SystemExit("BLOCKED: Chaiten.json no existe")
    if not CSV_PATH.exists():
        raise SystemExit("BLOCKED: MIROVA CSV no existe")

    # 1. Cargar record del pipeline
    rec = find_pipeline_record()
    pc = rec["primary_cluster"]
    pc_vrp_mw = float(pc["vrp_mw"])
    pc_lat = float(pc["centroid_lat"])
    pc_lon = float(pc["centroid_lon"])
    pc_dist_km = pc.get("centroid_dist_km")
    pc_dist_km = float(pc_dist_km) if pc_dist_km is not None else None
    print(f"\n--- Pipeline record (Chaiten.json) ---")
    print(f"  datetime_utc:        {rec['datetime_utc']}")
    print(f"  sensor:              {rec['sensor']}")
    print(f"  distance_class:      {rec.get('distance_class')}")
    print(f"  vrp_mw (record):     {rec.get('vrp_mw')}")
    print(f"  pc.vrp_mw:           {pc_vrp_mw}")
    print(f"  pc.centroid:         ({pc_lat}, {pc_lon})")
    print(f"  pc.centroid_dist_km: {pc_dist_km}")
    print(f"  pc.n_pixels:         {pc.get('n_pixels')}")

    # 2. Cargar MIROVA CSV
    csv_row = find_mirova_csv_row()
    mirova_vrp_mw = csv_row["VRP_MW"]
    mirova_dist_km = csv_row["Distancia_km"]
    print(f"\n--- MIROVA CSV NRT ---")
    print(f"  Fecha_Satelite_UTC:  {csv_row['Fecha_Satelite_UTC']}")
    print(f"  VRP_MW:              {mirova_vrp_mw}")
    print(f"  Distancia_km:        {mirova_dist_km}")
    print(f"  Tipo_Registro:       {csv_row['Tipo_Registro']}")

    # 3. Ratio magnitud
    ratio_mw = pc_vrp_mw / mirova_vrp_mw if mirova_vrp_mw > 0 else None
    print(f"\n--- Magnitud (R2 método verdadero) ---")
    print(f"  pc.vrp_mw / MIROVA.VRP_MW = {pc_vrp_mw} / {mirova_vrp_mw}")
    print(f"  ratio = {ratio_mw}")
    print(f"  referencia agregada S63 (informativa): {TARGET_S63_AGGREGATE_RATIO}x")

    # 4. Centroide TIF top10 <3km del vent
    print(f"\n--- Geometria: top10 TIF restringido a 3km del vent ---")
    print(f"  vent: ({VENT_LAT}, {VENT_LON})")
    tif_centroid = top_n_centroid_near_vent(
        TIF_PATH, VENT_LAT, VENT_LON, max_km=3.0, n=10
    )
    print(f"  TIF total positive pixels: {tif_centroid['n_positive_pixels_full']}")
    print(f"  Positive pixels within 3km: {tif_centroid['n_positive_pixels_within_max_km']}")
    print(f"  top10 centroide:        ({tif_centroid['lat']}, {tif_centroid['lon']})")
    print(f"  top10 sum_mw (informativo, NO la magnitud R2): {tif_centroid['sum_mw']:.4f}")
    print(f"  n_used: {tif_centroid['n_used']}")
    if tif_centroid['n_used'] > 0:
        print(f"  top vals: [{tif_centroid.get('top_values_min'):.4f} .. {tif_centroid.get('top_values_max'):.4f}]")
        print(f"  top dists km: [{tif_centroid.get('top_dists_km_min'):.3f} .. {tif_centroid.get('top_dists_km_max'):.3f}]")

    # 5. Drift geometrico TIF top10 vs pc.centroid
    if tif_centroid["lat"] is None:
        drift_km = None
    else:
        drift_km = float(haversine_km(
            tif_centroid["lat"], tif_centroid["lon"],
            pc_lat, pc_lon,
        ))
    print(f"\n--- Drift geometrico (TIF top10 <3km vs pc.centroid) ---")
    print(f"  drift = {drift_km} km")

    # 6. Verdict 4 gates
    ratio_in_band = ratio_mw is not None and 0.5 <= ratio_mw <= 2.0
    drift_ok = drift_km is not None and drift_km < 2.0
    # Gate 3: ratio cerca del target agregado S63 (+/-0.5x — tolerancia mayor
    # que en Lastarria porque la referencia S63 es agregada, no per-record).
    ratio_close_to_target = (
        ratio_mw is not None and abs(ratio_mw - TARGET_S63_AGGREGATE_RATIO) <= 0.5
    )
    # Gate 4: informativo — no había drift S63 per-record para comparar.
    drift_close_to_expected = drift_ok  # mismo gate, sin target previo
    replicated = ratio_in_band and drift_ok and ratio_close_to_target

    print(f"\n--- Verdict ---")
    print(f"  ratio in band [0.5, 2.0]:                       {ratio_in_band}")
    print(f"  drift < 2 km:                                   {drift_ok}")
    print(f"  ratio close to S63 aggregate target (+/-0.5x):  {ratio_close_to_target}")
    print(f"  drift close to expected (sin target, == drift<2km gate): {drift_close_to_expected}")
    verdict = "PASS" if replicated else "FAIL"
    print(f"  VERDICT: {verdict}")

    summary = {
        "case": {
            "volcano": "Chaiten",
            "datetime_utc": rec["datetime_utc"],
            "sensor": rec["sensor"],
            "distance_class": rec.get("distance_class"),
            "mirova_csv_timestamp": csv_row["Fecha_Satelite_UTC"],
            "mirova_sensor": MIROVA_SENSOR_CSV,
            "tipo_registro": csv_row["Tipo_Registro"],
            "tif_path": str(TIF_PATH.relative_to(WORKTREE_ROOT.parent)),
        },
        "vent": {"lat": VENT_LAT, "lon": VENT_LON},
        "pipeline_primary_cluster": {
            "vrp_mw": pc_vrp_mw,
            "centroid_lat": pc_lat,
            "centroid_lon": pc_lon,
            "centroid_dist_km": pc_dist_km,
            "n_pixels": pc.get("n_pixels"),
        },
        "mirova_csv": {
            "vrp_mw": mirova_vrp_mw,
            "distancia_km": mirova_dist_km,
        },
        "magnitude_r2": {
            "ratio_pc_vrp_vs_mirova_vrp": ratio_mw,
            "ratio_in_band_0p5_to_2p0": ratio_in_band,
            "reference_s63_aggregate_ratio": TARGET_S63_AGGREGATE_RATIO,
            "ratio_close_to_target": ratio_close_to_target,
        },
        "geometry_r2": {
            "tif_top10_within_3km_centroid_lat": tif_centroid["lat"],
            "tif_top10_within_3km_centroid_lon": tif_centroid["lon"],
            "tif_top10_within_3km_sum_mw_informative": tif_centroid["sum_mw"],
            "tif_top10_within_3km_n_used": tif_centroid["n_used"],
            "tif_positive_pixels_full": tif_centroid["n_positive_pixels_full"],
            "tif_positive_pixels_within_3km": tif_centroid["n_positive_pixels_within_max_km"],
            "tif_top_values_min": tif_centroid.get("top_values_min"),
            "tif_top_values_max": tif_centroid.get("top_values_max"),
            "drift_km_tif_top10_vs_pc_centroid": drift_km,
            "drift_ok_under_2km": drift_ok,
        },
        "verdict": verdict,
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nResultados: {RESULTS_PATH}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
