"""S21 experiment 41 - Validacion empirica D6: std_bg multi-ROI sobre granules T4.

Objetivo: para 3-5 granules T4 conocidos Tupungatito (clase forense T4 = nuestro
pipeline detectó pixels far pero ningún pixel summit, mientras MIROVA reportó
detección summit), descargar el granule via earthaccess, cargar BT (I04 o M13),
y computar `std_bg` sobre múltiples ROIs:

    annulus_global   : 2-25 km del centro (método actual)
    annulus_summit_5_8 : 5-8 km del mirova_center (anillo local más chico)
    annulus_summit_5_10: 5-10 km
    annulus_summit_3_5 : 3-5 km (entre vent y borde summit)

Si annulus_summit << annulus_global → confirma D6 viable. Si similar → refuta.

Uso CLI:
    python experiments/measure_local_bg_offline.py \\
        --volcano Tupungatito \\
        --forense-json experiments/38_forense_Tupungatito.json \\
        --max-granules 3 \\
        --output-json experiments/41_local_bg_Tupungatito.json
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

# Reuse pipeline loaders
sys.path.insert(0, str(Path(__file__).parent.parent))


# === Geometric helpers (puros, testeables) ===

def bbox_mask(lat: np.ndarray, lon: np.ndarray, center_lat: float,
              center_lon: float, half_km: float) -> np.ndarray:
    """Bbox cuadrado centrado en (lat, lon), half_km por lado."""
    lat_span = (lat - center_lat) * 111.0
    lon_span = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
    return (np.abs(lat_span) <= half_km) & (np.abs(lon_span) <= half_km)


def _haversine_km_array(lat1: float, lon1: float,
                        lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def annulus_mask(lat: np.ndarray, lon: np.ndarray, center_lat: float,
                 center_lon: float, inner_km: float, outer_km: float) -> np.ndarray:
    """Annulus circular: inner_km <= dist <= outer_km."""
    dist = _haversine_km_array(center_lat, center_lon, lat, lon)
    return (dist >= inner_km) & (dist <= outer_km)


def exclude_disk(mask: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                 center_lat: float, center_lon: float,
                 radius_km: float) -> np.ndarray:
    """Quita del mask los pixels dentro del disco radius_km."""
    dist = _haversine_km_array(center_lat, center_lon, lat, lon)
    return mask & (dist > radius_km)


def std_bg(bt: np.ndarray, mask: np.ndarray,
           min_pixels: int = 25) -> tuple[float, int]:
    """std de BT en mask, ignorando NaN. NaN si <min_pixels válidos."""
    valid = bt[mask & ~np.isnan(bt)]
    n = int(valid.size)
    if n < min_pixels:
        return float("nan"), n
    return float(np.std(valid)), n


# === Multi-ROI measurement ===

def measure_for_granule(*, lat: np.ndarray, lon: np.ndarray, bt: np.ndarray,
                        volcano_lat: float, volcano_lon: float,
                        mirova_center_lat: float, mirova_center_lon: float,
                        bg_inner_km: float = 2.0,
                        bg_outer_km: float = 25.0) -> dict:
    """Devuelve dict con std_bg + n por cada ROI candidata."""
    out = {}

    # ROI 1: anillo global actual (volcano center, 2-25 km)
    mask = annulus_mask(lat, lon, volcano_lat, volcano_lon,
                        inner_km=bg_inner_km, outer_km=bg_outer_km)
    s, n = std_bg(bt, mask)
    out["annulus_global"] = {"std_bg": s, "n": n,
                             "center": [volcano_lat, volcano_lon],
                             "inner_km": bg_inner_km, "outer_km": bg_outer_km}

    # ROI 2: annulus summit local 3-5 km del mirova_center
    mask = annulus_mask(lat, lon, mirova_center_lat, mirova_center_lon,
                        inner_km=3.0, outer_km=5.0)
    s, n = std_bg(bt, mask)
    out["annulus_summit_3_5"] = {"std_bg": s, "n": n,
                                 "center": [mirova_center_lat, mirova_center_lon],
                                 "inner_km": 3.0, "outer_km": 5.0}

    # ROI 3: annulus summit 5-8 km
    mask = annulus_mask(lat, lon, mirova_center_lat, mirova_center_lon,
                        inner_km=5.0, outer_km=8.0)
    s, n = std_bg(bt, mask)
    out["annulus_summit_5_8"] = {"std_bg": s, "n": n,
                                 "center": [mirova_center_lat, mirova_center_lon],
                                 "inner_km": 5.0, "outer_km": 8.0}

    # ROI 4: annulus summit 5-10 km (más amplio)
    mask = annulus_mask(lat, lon, mirova_center_lat, mirova_center_lon,
                        inner_km=5.0, outer_km=10.0)
    s, n = std_bg(bt, mask)
    out["annulus_summit_5_10"] = {"std_bg": s, "n": n,
                                  "center": [mirova_center_lat, mirova_center_lon],
                                  "inner_km": 5.0, "outer_km": 10.0}

    return out


# === YAML loader (paridad con experiment 39) ===

def load_volcano_cfg(yaml_path: Path, volcano: str) -> dict:
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if isinstance(cfg, dict) and "volcanoes" in cfg and isinstance(cfg["volcanoes"], list):
        for v in cfg["volcanoes"]:
            if v.get("name") == volcano:
                return v
        return {}
    if isinstance(cfg, dict):
        return cfg.get(volcano, {})
    return {}


# === Pipeline runner ===

def select_t4_targets(forense_json: Path, max_n: int) -> list[dict]:
    """Selecciona records T4 con granule disponible. Prioriza VIIRS_NOAA20 (más datos)."""
    data = json.loads(forense_json.read_text(encoding="utf-8"))
    targets = []
    for c in data["classifications"]:
        if c["class"] != "T4":
            continue
        rec = c.get("rec")
        if not rec or not rec.get("granule"):
            continue
        targets.append({
            "datetime_utc": rec["datetime_utc"],
            "sensor": rec["sensor"],
            "granule": rec["granule"],
        })
    # Filtrar a 375m I-band primero, M-band segundo
    i_band = [t for t in targets if not t["sensor"].endswith("_750")]
    m_band = [t for t in targets if t["sensor"].endswith("_750")]
    return (i_band + m_band)[:max_n]


def fetch_and_load_granule(target: dict, volcano_cfg: dict, tmp_dir: Path) -> dict | None:
    """Descarga el granule del target via earthaccess y carga BT/lat/lon.

    Returns dict con {bt, lat, lon, sensor} o None si falla.
    """
    from pipeline import fetch as fetch_mod
    from pipeline import process_viirs as p_viirs
    from pipeline import process_viirs_mod as p_viirs_mod

    dt_str = target["datetime_utc"].split(" ")[0]  # "YYYY-MM-DD"
    dt = datetime.strptime(dt_str, "%Y-%m-%d")

    # fetch_for_volcano descarga TODOS los sensores del dia. Filtramos al matching.
    print(f"  -> Fetching {dt_str} ({target['sensor']}) ...")
    paths_by_platform = fetch_mod.fetch_for_volcano(
        volcano_cfg, dt, tmp_dir, sensors=["VIIRS"], nighttime_only=True)

    # Buscar el l1b/geo que matchea el granule target
    target_granule = target["granule"]
    sensor = target["sensor"]
    l1b_path = geo_path = None
    for platform, paths in paths_by_platform.items():
        for p in paths:
            if target_granule in p.name or p.name in target_granule:
                # encontrado, buscar el match l1b/geo
                if "IMG" in p.name and "MOD" not in p.name and "M0" not in p.name:
                    if "02" in p.name:
                        l1b_path = p
                    elif "03" in p.name:
                        geo_path = p
                elif "MOD" in p.name or "M0" in p.name:
                    if "02" in p.name:
                        l1b_path = p
                    elif "03" in p.name:
                        geo_path = p

    # Fallback: buscar por timestamp del granule
    if l1b_path is None or geo_path is None:
        # Extraer hora del granule
        parts = target_granule.split(".")
        if len(parts) > 3:
            time_key = parts[2]  # ej "0612"
            for platform, paths in paths_by_platform.items():
                for p in paths:
                    if time_key not in p.name:
                        continue
                    if sensor.endswith("_750"):
                        if "MOD" in p.name or "M0" in p.name:
                            if "02" in p.name and l1b_path is None:
                                l1b_path = p
                            elif "03" in p.name and geo_path is None:
                                geo_path = p
                    else:
                        if "IMG" in p.name and "M0" not in p.name and "MOD" not in p.name:
                            if "02" in p.name and l1b_path is None:
                                l1b_path = p
                            elif "03" in p.name and geo_path is None:
                                geo_path = p

    if l1b_path is None or geo_path is None:
        print(f"    NO MATCH for {target_granule}")
        return None

    print(f"    L1B={l1b_path.name}  GEO={geo_path.name}")

    # Cargar bandas
    if sensor.endswith("_750"):
        bands = p_viirs_mod.read_viirs_l1b(l1b_path)
        geo = p_viirs_mod.read_viirs_geo(geo_path)
        bt_key = "M13"  # MIR 4.05 μm
    else:
        bands = p_viirs.read_viirs_l1b(l1b_path)
        geo = p_viirs.read_viirs_geo(geo_path)
        bt_key = "I04"  # MIR 3.74 μm

    if bt_key not in bands:
        print(f"    Band {bt_key} not loaded")
        return None

    return {
        "bt": bands[bt_key],
        "lat": geo["lat"],
        "lon": geo["lon"],
        "sensor": sensor,
        "granule": target_granule,
        "datetime_utc": target["datetime_utc"],
        "bt_key": bt_key,
    }


def run(*, volcano: str, forense_json: Path, volcanoes_yaml: Path,
        max_granules: int = 3) -> dict:
    cfg = load_volcano_cfg(volcanoes_yaml, volcano)
    if not cfg:
        raise SystemExit(f"Volcán '{volcano}' no encontrado")

    # Resolver mirova_center (fallback a vent_lat/lon)
    mc_lat = cfg.get("mirova_center_lat") or cfg.get("vent_lat") or cfg["lat"]
    mc_lon = cfg.get("mirova_center_lon") or cfg.get("vent_lon") or cfg["lon"]
    vol_lat = cfg["lat"]
    vol_lon = cfg["lon"]

    targets = select_t4_targets(forense_json, max_n=max_granules)
    print(f"Volcano: {volcano}")
    print(f"  vent_lat/lon = ({cfg.get('vent_lat')}, {cfg.get('vent_lon')})")
    print(f"  mirova_center = ({mc_lat}, {mc_lon})")
    print(f"  T4 targets: {len(targets)}")
    print()

    measurements = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, target in enumerate(targets, 1):
            print(f"[{i}/{len(targets)}] {target['datetime_utc']} {target['sensor']}")
            try:
                arrays = fetch_and_load_granule(target, cfg, tmp_dir)
            except Exception as e:
                print(f"    ERROR: {e}")
                continue
            if arrays is None:
                continue

            rois = measure_for_granule(
                lat=arrays["lat"], lon=arrays["lon"], bt=arrays["bt"],
                volcano_lat=vol_lat, volcano_lon=vol_lon,
                mirova_center_lat=mc_lat, mirova_center_lon=mc_lon,
            )
            measurements.append({
                "datetime_utc": target["datetime_utc"],
                "sensor": target["sensor"],
                "granule": target["granule"],
                "bt_key": arrays["bt_key"],
                "rois": rois,
            })
            print(f"    ROIs std_bg: " + " · ".join(
                f"{k.split('_', 1)[1]}={v['std_bg']:.2f}K (n={v['n']})"
                for k, v in rois.items()
            ))
            print()

    # Resumen mediano por ROI
    summary = {}
    roi_keys = ("annulus_global", "annulus_summit_3_5",
                "annulus_summit_5_8", "annulus_summit_5_10")
    for k in roi_keys:
        stds = [m["rois"][k]["std_bg"] for m in measurements
                if k in m["rois"] and not math.isnan(m["rois"][k]["std_bg"])]
        ns = [m["rois"][k]["n"] for m in measurements if k in m["rois"]]
        summary[k] = {
            "median_std_bg": float(np.median(stds)) if stds else float("nan"),
            "n_granules_with_data": len(stds),
            "median_n_pixels": int(np.median(ns)) if ns else 0,
        }

    return {
        "volcano": volcano,
        "vent_nominal": [cfg.get("vent_lat"), cfg.get("vent_lon")],
        "mirova_center_used": [mc_lat, mc_lon],
        "n_t4_targets": len(targets),
        "n_granules_processed": len(measurements),
        "summary": summary,
        "measurements": measurements,
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--forense-json", required=True)
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--max-granules", type=int, default=3)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    out = run(
        volcano=args.volcano,
        forense_json=Path(args.forense_json),
        volcanoes_yaml=Path(args.yaml),
        max_granules=args.max_granules,
    )
    Path(args.output_json).write_text(json.dumps(out, indent=2, default=str),
                                       encoding="utf-8")
    print()
    print("=== SUMMARY ===")
    for k, v in out["summary"].items():
        print(f"  {k}: median_std_bg={v['median_std_bg']:.3f} K "
              f"(n_granules={v['n_granules_with_data']}, median_pixels={v['median_n_pixels']})")
    g = out["summary"]["annulus_global"]["median_std_bg"]
    s = out["summary"]["annulus_summit_5_8"]["median_std_bg"]
    if g > 0 and not math.isnan(s):
        ratio = s / g
        print()
        print(f"  Ratio summit_5_8/global = {ratio:.2f}")
        if ratio < 0.5:
            print("  [OK] D6 VIABLE: std_bg local << global. Implementar fix.")
        elif ratio > 0.85:
            print("  [NO] D6 REFUTADO: std_bg local similar a global. Re-pensar causa.")
        else:
            print("  [?] Ratio intermedio. Revisar caso por caso.")


if __name__ == "__main__":
    _main()
