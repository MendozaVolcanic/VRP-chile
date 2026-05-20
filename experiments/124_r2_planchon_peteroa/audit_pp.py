"""R2 retroactivo PlanchonPeteroa (S70-1 T3) sobre 2026-05-18 05:24 UTC VIIRS_NOAA20.

Aplicación del método R2 S69 VERDADERO (validado en
`experiments/120_audit_tif_vrp_sumable/audit_lastarria_real_method.py` y
ampliado en `experiments/122_r2_chaiten/audit_chaiten.py` +
`experiments/123_r2_villarrica/audit_villarrica.py`) a un caso
ALERTA_TERMICA reciente de PlanchonPeteroa (PP), post-adopción S61 de
`local_kernel_bg: true`.

Contexto físico (geólogo)
-------------------------

PP no es un volcán único: es un COMPLEJO volcánico transfronterizo
Chile-Argentina con múltiples centros eruptivos a pocos km uno del otro:
Planchón Norte (apagado), Planchón Sur, Peteroa (cráter activo principal,
fumarolas, ácido sulfúrico) y Azufre. El `vent_lat/lon` (-35.241099,
-70.573345) apunta nominalmente al cráter activo Peteroa. La actividad
térmica monitoreada por MIROVA típicamente corresponde a fumarolas / lago
ácido en el cráter Peteroa.

Implicación para R2: si MIROVA detectó actividad en el mismo cráter que
nuestro pipeline → drift esperado <1 km. Pero si MIROVA detectó actividad
en un cráter vecino del complejo (Planchón Sur a ~3 km al N, por ejemplo)
mientras nuestro pipeline pegó en otro pixel del mismo halo termal, el
drift puede ser 1-3 km SIN que indique error metodológico — sería sólo
multi-cráter en un complejo activo.

Adopción S61: ratio LEGACY 11.80x → NEW 2.84x con `local_kernel_bg: true`
sobre 39 ALERTAS A/B, recall 39/39 (no degradó cobertura). PP es el
volcán con la SEGUNDA mejora más fuerte del fix kernel-bg (después de
Lastarria -84%). La hipótesis física del fix: el background regional
sobre-estimaba el calor de fondo porque promediaba sobre nieve heterogénea
+ valles + pixels parcialmente contaminados por la propia fumarola, dejando
el cráter Peteroa sub-umbral. El kernel local fuera del cráter aisla el
fondo no contaminado.

Caso elegido
------------

- Volcán: PlanchonPeteroa (vent -35.241099, -70.573345)
- ALERTA MIROVA: 2026-05-18 05:24:01 VIIRS375 VRP=0.16 MW dist=1.91 km
- Nuestro record: 2026-05-18 05:24 VIIRS_NOAA20
  pc.vrp_mw=0.333 pc.n_pixels=2 pc.centroid_dist≈2.05 km (lee dinámico)
- TIF paralelo: `mirova-tif-archive/data/tif/PlanchonPeteroa/20260518_052401_VIIRS375.tif`
  (timestamp coincide exactamente con MIROVA CSV)

Razón de elección de este caso: ratio pc.vrp_mw / MIROVA = 2.08x, cercano
a la media agregada S61 (2.84x). Es el caso más representativo de la
adopción dentro de la ventana del TIF archive (2026-05-09 al 2026-05-20).
Otros candidatos (e.g., 2026-05-09 ratio 1.51x, 2026-05-11 ratio 1.94x)
también validan el fix; este es el representativo cercano al agregado.

Método (replicado S70-1 T1.5)
-----------------------------

1. Magnitud: ratio `pc.vrp_mw / MIROVA.VRP_MW`. Banda [0.5, 2.0] aceptable.
2. Geometría: centroide ponderado de los top-10 pixels del TIF restringidos
   a <=3 km del vent (filtro principal). Drift vs `pc.centroid_lat/lon`.
   Tolerancia ESTRICTA: drift < 2 km. REVISADA: drift < 3 km.
3. Sensitivity: matriz (top_n × max_km) ∈ {5,10,20} × {2,3,5} km para
   caracterizar robustez. Para PP esperamos que max_km=5km arrastre
   pixels de cráteres vecinos del complejo (Planchón Sur, Azufre) si
   tienen señal residual; max_km=2km debería aislar al cráter Peteroa
   y dar drift más pequeño si el cluster coincide.

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
TIF_PATH = TIF_ARCHIVE / "data" / "tif" / "PlanchonPeteroa" / "20260518_052401_VIIRS375.tif"
PP_JSON = WORKTREE_ROOT / "data" / "mirova_equivalent" / "PlanchonPeteroa.json"
CSV_PATH = WORKTREE_ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
RESULTS_PATH = HERE / "results.json"

# PlanchonPeteroa vent (volcanoes.yaml). mirova_center existe (-35.2232, -70.5695)
# pero el método R2 mide drift contra pc.centroid, no contra mirova_center.
# Usamos vent_lat/lon como referencia espacial para el filtro top_n.
VENT_LAT = -35.241099
VENT_LON = -70.573345

# Caso a auditar
TARGET_DATETIME = "2026-05-18 05:24"
TARGET_SENSOR = "VIIRS_NOAA20"  # VIIRS375 en MIROVA CSV
MIROVA_CSV_TIMESTAMP = "2026-05-18 05:24:01"
MIROVA_SENSOR_CSV = "VIIRS375"

# Referencia agregada S61 (no es target per-record, sólo informativa)
TARGET_S61_AGGREGATE_RATIO = 2.84  # ratio mediano A/B post-adopción 39 ALERTAS
TARGET_S61_AGGREGATE_DRIFT_KM = None  # no había drift S61 per-record

# Sensitivity grid (heredado de S70-1 T1.5)
SENSITIVITY_N = [5, 10, 20]
SENSITIVITY_KM = [2.0, 3.0, 5.0]


def haversine_km(lat1, lon1, lat2, lon2):
    """Haversine en km, escalar o vector."""
    R = 6371.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(np.asarray(lat2) - np.asarray(lat1))
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def load_tif(tif_path: Path):
    """Carga TIF a (arr, transform). NaN→0."""
    with rasterio.open(tif_path) as src:
        arr = src.read(1)
        transform = src.transform
    arr = np.where(np.isnan(arr), 0.0, arr)
    return arr, transform


def top_n_centroid_from_array(
    arr: np.ndarray,
    transform,
    vent_lat: float,
    vent_lon: float,
    max_km: float = 3.0,
    n: int = 10,
) -> dict:
    """Centroide ponderado top-N pixels (arr ya cargado) restringido a max_km del vent."""
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


def sensitivity_matrix(
    arr: np.ndarray,
    transform,
    vent_lat: float,
    vent_lon: float,
    pc_centroid_lat: float,
    pc_centroid_lon: float,
) -> list[dict]:
    """Drift para cada combinacion (top_n x max_km) en SENSITIVITY_N x SENSITIVITY_KM."""
    matrix = []
    for n in SENSITIVITY_N:
        for max_km in SENSITIVITY_KM:
            res = top_n_centroid_from_array(
                arr, transform, vent_lat, vent_lon, max_km=max_km, n=n
            )
            if res["lat"] is None:
                matrix.append({
                    "top_n": n,
                    "max_km": max_km,
                    "n_pixels_available_within_max_km": res["n_positive_pixels_within_max_km"],
                    "n_pixels_used": 0,
                    "n_pixels_used_lt_top_n_requested": False,
                    "centroid_lat": None,
                    "centroid_lon": None,
                    "drift_km": None,
                })
                continue
            drift = float(haversine_km(
                res["lat"], res["lon"], pc_centroid_lat, pc_centroid_lon
            ))
            matrix.append({
                "top_n": n,
                "max_km": max_km,
                "n_pixels_available_within_max_km": res["n_positive_pixels_within_max_km"],
                "n_pixels_used": res["n_used"],
                "n_pixels_used_lt_top_n_requested": res["n_used"] < n,
                "centroid_lat": res["lat"],
                "centroid_lon": res["lon"],
                "drift_km": drift,
            })
    return matrix


def evaluate_gates(
    ratio_mag: float | None,
    drift_km: float | None,
    ratio_target: float | None = None,
    drift_target: float | None = None,
    ratio_target_tol: float = 0.5,
    drift_target_tol: float = 0.5,
) -> dict:
    """Devuelve dict con 6 gates evaluadas (4 ESTRICTOS + 2 REVISADOS)."""
    gates: dict[str, bool | None] = {}
    gates["g1_ratio_in_band_strict"] = (
        ratio_mag is not None and 0.5 <= ratio_mag <= 2.0
    )
    gates["g2_drift_under_2km_strict"] = drift_km is not None and drift_km < 2.0
    if ratio_target is not None and ratio_mag is not None:
        gates["g3_ratio_close_to_target_strict"] = (
            abs(ratio_mag - ratio_target) <= ratio_target_tol
        )
    else:
        gates["g3_ratio_close_to_target_strict"] = None
    if drift_target is not None and drift_km is not None:
        gates["g4_drift_close_to_target_strict"] = (
            abs(drift_km - drift_target) <= drift_target_tol
        )
    else:
        gates["g4_drift_close_to_target_strict"] = None
    gates["g5_ratio_in_band_revised"] = gates["g1_ratio_in_band_strict"]
    gates["g6_drift_under_3km_revised"] = drift_km is not None and drift_km < 3.0
    return gates


def find_pipeline_record() -> dict:
    """Encuentra el record de PlanchonPeteroa.json para 2026-05-18 05:24 VIIRS_NOAA20."""
    with open(PP_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"] if isinstance(data, dict) and "records" in data else data
    for r in records:
        if r.get("datetime_utc") == TARGET_DATETIME and r.get("sensor") == TARGET_SENSOR:
            return r
    raise RuntimeError(
        f"Record no encontrado: datetime={TARGET_DATETIME} sensor={TARGET_SENSOR}"
    )


def find_mirova_csv_row() -> dict:
    """Encuentra la fila MIROVA CSV para 2026-05-18 05:24:01 VIIRS375 PlanchonPeteroa."""
    df = pd.read_csv(CSV_PATH)
    pp = df[df["Volcan"].astype(str).str.contains("Planch", case=False, na=False)]
    pp = pp[pp["Sensor"] == MIROVA_SENSOR_CSV]
    m = pp[pp["Fecha_Satelite_UTC"] == MIROVA_CSV_TIMESTAMP]
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
    print("R2 RETROACTIVO PLANCHONPETEROA - 2026-05-18 05:24 UTC (S70-1 T3)")
    print("Dual verdict (estricto + revisado) + sensitivity analysis")
    print("=" * 70)

    # 0. Verificar paths
    print(f"\nTIF:                {TIF_PATH}")
    print(f"                    exists: {TIF_PATH.exists()}")
    print(f"PlanchonPeteroa JSON: {PP_JSON}")
    print(f"                    exists: {PP_JSON.exists()}")
    print(f"MIROVA CSV:         {CSV_PATH}")
    print(f"                    exists: {CSV_PATH.exists()}")

    if not TIF_PATH.exists():
        raise SystemExit("BLOCKED: TIF no existe")
    if not PP_JSON.exists():
        raise SystemExit("BLOCKED: PlanchonPeteroa.json no existe")
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
    print(f"\n--- Pipeline record (PlanchonPeteroa.json) ---")
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
    print(f"\n--- Magnitud (R2 metodo verdadero) ---")
    print(f"  pc.vrp_mw / MIROVA.VRP_MW = {pc_vrp_mw} / {mirova_vrp_mw}")
    print(f"  ratio = {ratio_mw}")
    print(f"  referencia agregada S61 (informativa): {TARGET_S61_AGGREGATE_RATIO}x")

    # 4. Cargar TIF una sola vez para principal + sensitivity
    arr, transform = load_tif(TIF_PATH)

    # 5. Calculo principal (top_n=10, max_km=3.0)
    print(f"\n--- Geometria principal: top10 TIF restringido a 3km del vent ---")
    print(f"  vent: ({VENT_LAT}, {VENT_LON})")
    tif_centroid = top_n_centroid_from_array(
        arr, transform, VENT_LAT, VENT_LON, max_km=3.0, n=10
    )
    print(f"  TIF total positive pixels: {tif_centroid['n_positive_pixels_full']}")
    print(f"  Positive pixels within 3km: {tif_centroid['n_positive_pixels_within_max_km']}")
    print(f"  top10 centroide:        ({tif_centroid['lat']}, {tif_centroid['lon']})")
    print(f"  top10 sum_mw (informativo, NO la magnitud R2): {tif_centroid['sum_mw']:.4f}")
    print(f"  n_used: {tif_centroid['n_used']}")
    if tif_centroid['n_used'] > 0:
        print(f"  top vals: [{tif_centroid.get('top_values_min'):.4f} .. {tif_centroid.get('top_values_max'):.4f}]")
        print(f"  top dists km: [{tif_centroid.get('top_dists_km_min'):.3f} .. {tif_centroid.get('top_dists_km_max'):.3f}]")

    # 6. Drift geometrico principal
    if tif_centroid["lat"] is None:
        drift_km = None
    else:
        drift_km = float(haversine_km(
            tif_centroid["lat"], tif_centroid["lon"],
            pc_lat, pc_lon,
        ))
    print(f"\n--- Drift geometrico principal (TIF top10 <3km vs pc.centroid) ---")
    print(f"  drift = {drift_km} km")

    # 7. 6 gates (4 estrictos + 2 revisados)
    gates = evaluate_gates(
        ratio_mag=ratio_mw,
        drift_km=drift_km,
        ratio_target=TARGET_S61_AGGREGATE_RATIO,
        drift_target=TARGET_S61_AGGREGATE_DRIFT_KM,  # None -> g4 = None
        ratio_target_tol=0.5,
        drift_target_tol=0.5,
    )
    print(f"\n--- 6 gates evaluadas ---")
    for k, v in gates.items():
        print(f"  {k}: {v}")

    strict_keys = [
        "g1_ratio_in_band_strict",
        "g2_drift_under_2km_strict",
        "g3_ratio_close_to_target_strict",
        "g4_drift_close_to_target_strict",
    ]
    revised_keys = [
        "g5_ratio_in_band_revised",
        "g6_drift_under_3km_revised",
    ]
    strict_results = [gates[k] for k in strict_keys if gates[k] is not None]
    revised_results = [gates[k] for k in revised_keys if gates[k] is not None]
    strict_pass = all(strict_results) and len(strict_results) > 0
    revised_pass = all(revised_results) and len(revised_results) > 0
    strict_n_pass = sum(1 for v in strict_results if v)
    revised_n_pass = sum(1 for v in revised_results if v)

    verdict_strict = "PASS" if strict_pass else "FAIL"
    verdict_revised = "PASS" if revised_pass else "FAIL"
    print(f"\n--- Verdict dual ---")
    print(f"  ESTRICTO ({len(strict_results)} gates aplicables): {verdict_strict} ({strict_n_pass}/{len(strict_results)} gates)")
    print(f"  REVISADO ({len(revised_results)} gates):           {verdict_revised} ({revised_n_pass}/{len(revised_results)} gates)")

    # 8. Sensitivity analysis (matriz 9 combinaciones)
    print(f"\n--- Parte 3: sensitivity analysis (top_n x max_km) ---")
    matrix = sensitivity_matrix(arr, transform, VENT_LAT, VENT_LON, pc_lat, pc_lon)
    print(f"  top_n  max_km  n_avail  n_used  drift_km")
    for row in matrix:
        drift_str = f"{row['drift_km']:.3f}" if row["drift_km"] is not None else "None"
        print(f"  {row['top_n']:>5}  {row['max_km']:>6.1f}  {row['n_pixels_available_within_max_km']:>7}  {row['n_pixels_used']:>6}  {drift_str:>8}")

    drifts_valid = [r["drift_km"] for r in matrix if r["drift_km"] is not None]
    if drifts_valid:
        drift_min = min(drifts_valid)
        drift_max = max(drifts_valid)
        drift_median = float(np.median(drifts_valid))
        print(f"\n  Sensitivity summary (9 combinaciones):")
        print(f"    drift_km min:    {drift_min:.3f}")
        print(f"    drift_km median: {drift_median:.3f}")
        print(f"    drift_km max:    {drift_max:.3f}")
    else:
        drift_min = drift_max = drift_median = None

    # 9. Persistir resultados
    summary = {
        "version": 2,
        "method": "R2_S69_verdadero_ampliado_S70_1_T3",
        "case": {
            "volcano": "PlanchonPeteroa",
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
            "reference_s61_aggregate_ratio": TARGET_S61_AGGREGATE_RATIO,
            "reference_s61_aggregate_drift_km": TARGET_S61_AGGREGATE_DRIFT_KM,
        },
        "geometry_r2_principal": {
            "top_n": 10,
            "max_km": 3.0,
            "tif_top10_within_3km_centroid_lat": tif_centroid["lat"],
            "tif_top10_within_3km_centroid_lon": tif_centroid["lon"],
            "tif_top10_within_3km_sum_mw_informative": tif_centroid["sum_mw"],
            "tif_top10_within_3km_n_used": tif_centroid["n_used"],
            "tif_positive_pixels_full": tif_centroid["n_positive_pixels_full"],
            "tif_positive_pixels_within_3km": tif_centroid["n_positive_pixels_within_max_km"],
            "tif_top_values_min": tif_centroid.get("top_values_min"),
            "tif_top_values_max": tif_centroid.get("top_values_max"),
            "drift_km_tif_top10_vs_pc_centroid": drift_km,
        },
        "gates": gates,
        "verdict_dual": {
            "strict": {
                "result": verdict_strict,
                "n_pass": strict_n_pass,
                "n_total": len(strict_results),
                "gate_keys": strict_keys,
                "note": "4 gates referencia Lastarria S69 original (banda + drift<2km + close-to-target ratio + close-to-target drift). g4 N/A para PlanchonPeteroa (sin drift S61 per-record).",
            },
            "revised": {
                "result": verdict_revised,
                "n_pass": revised_n_pass,
                "n_total": len(revised_results),
                "gate_keys": revised_keys,
                "note": "2 gates operacionales: ratio en banda + drift<3km (coherente con max_km del filtro espacial)",
            },
        },
        "sensitivity_analysis": {
            "grid_top_n": SENSITIVITY_N,
            "grid_max_km": SENSITIVITY_KM,
            "matrix": matrix,
            "drift_km_min": drift_min,
            "drift_km_median": drift_median,
            "drift_km_max": drift_max,
        },
    }
    RESULTS_PATH.write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nResultados: {RESULTS_PATH}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
