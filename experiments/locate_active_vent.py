"""S21 experiment #39 — Localizar fumarola activa real (centroide ponderado VRP).

Hallazgo H_S21_3 (S21): distancias CSV Mirova-v1 son reales no bin visual
(clusters dominantes 4.89/5.21 km Tupungatito). Sugiere que la fumarola activa
está descentrada del vent_lat/lon nominal del YAML. Si offset >0.5 km, el ROI1
5×5 km centrado en vent NOMINAL no contiene la fumarola — relevante para D6.

Este script computa el centroide ponderado por VRP de los pixels detectados
dentro de 2× inner_radius del vent nominal y propone mirova_center_lat/lon
corregido si offset > threshold.

Schema:
- record JSON: 'anomaly_pixels' lista de {lat, lon, dist_km, bt_k, vrp_mw}
- volcanoes.yaml: lista bajo 'volcanoes', cada item con 'name', 'vent_lat',
  'vent_lon', 'inner_radius_km', opcionalmente 'mirova_center_lat/lon'

Uso CLI:
    python experiments/locate_active_vent.py \\
        --volcano Tupungatito \\
        --output-json experiments/39_active_vent_Tupungatito.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import yaml


EARTH_RADIUS_KM = 6371.0


# === Geometría ===

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# === Centroide ponderado ===

def weighted_centroid(pixels: Iterable[dict]) -> tuple[float, float]:
    """Centroide ponderado por vrp_mw. Si todos VRP=0 o lista vacía: fallback.

    - Empty → (nan, nan)
    - All VRP=0 → media aritmética
    """
    px = list(pixels)
    if not px:
        return float("nan"), float("nan")
    total_vrp = sum(float(p.get("vrp_mw") or 0.0) for p in px)
    if total_vrp <= 0:
        n = len(px)
        return (sum(p["lat"] for p in px) / n,
                sum(p["lon"] for p in px) / n)
    lat = sum(p["lat"] * float(p.get("vrp_mw") or 0.0) for p in px) / total_vrp
    lon = sum(p["lon"] * float(p.get("vrp_mw") or 0.0) for p in px) / total_vrp
    return lat, lon


# === Propose corrected center ===

def propose_mirova_center(*, observed_centroid: tuple[float, float],
                          nominal: dict, threshold_km: float = 0.5) -> dict | None:
    """Si offset entre observado y nominal > threshold, devuelve dict con propuesta."""
    lat_obs, lon_obs = observed_centroid
    if math.isnan(lat_obs):
        return None
    offset = _haversine_km(nominal["vent_lat"], nominal["vent_lon"],
                           lat_obs, lon_obs)
    if offset < threshold_km:
        return None
    return {
        "mirova_center_lat": round(lat_obs, 5),
        "mirova_center_lon": round(lon_obs, 5),
        "offset_km": round(offset, 3),
        "vent_nominal": [nominal["vent_lat"], nominal["vent_lon"]],
    }


# === Recolección de pixels ===

def collect_anomaly_pixels(records: list[dict], inner_radius_km: float,
                           vent_lat: float, vent_lon: float,
                           cutoff_factor: float = 1.0) -> list[dict]:
    """Recolecta anomaly_pixels dentro de cutoff_factor × inner_radius_km del vent.

    cutoff_factor=1.0 (default): solo pixels dentro del inner_radius — captura
    la fumarola real, EXCLUYE pixels far T4 (que son el problema D6, no la señal
    que queremos localizar).
    cutoff_factor=2.0: incluye anillo wider (debug/sensibilidad).
    """
    pixels: list[dict] = []
    cutoff = cutoff_factor * inner_radius_km
    for rec in records:
        for p in rec.get("anomaly_pixels", []) or []:
            d = _haversine_km(vent_lat, vent_lon, p["lat"], p["lon"])
            if d <= cutoff:
                pixels.append(p)
    return pixels


# === YAML loader ===

def load_volcano_cfg(yaml_path: Path, volcano: str) -> dict:
    """volcanoes.yaml puede ser {volcanoes: [...]} o {nombre: {...}}. Soporta ambos."""
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if isinstance(cfg, dict) and "volcanoes" in cfg and isinstance(cfg["volcanoes"], list):
        for v in cfg["volcanoes"]:
            if v.get("name") == volcano:
                return v
        return {}
    if isinstance(cfg, dict):
        return cfg.get(volcano, {})
    return {}


# === Pipeline ===

def run(*, volcano: str, records_json: Path, volcanoes_yaml: Path,
        offset_threshold_km: float = 0.5) -> dict:
    cfg = load_volcano_cfg(volcanoes_yaml, volcano)
    if not cfg:
        raise SystemExit(f"Volcán '{volcano}' no encontrado en {volcanoes_yaml}")

    vent_lat = float(cfg["vent_lat"])
    vent_lon = float(cfg["vent_lon"])
    inner_km = float(cfg.get("inner_radius_km", 5.0))

    records = json.loads(records_json.read_text(encoding="utf-8")).get("records", [])
    pixels = collect_anomaly_pixels(records, inner_km, vent_lat, vent_lon)

    centroid = weighted_centroid(pixels)
    proposed = propose_mirova_center(
        observed_centroid=centroid,
        nominal={"vent_lat": vent_lat, "vent_lon": vent_lon},
        threshold_km=offset_threshold_km,
    )

    # Comparar con mirova_center_lat/lon ya documentado en YAML si existe
    existing_mc = None
    if "mirova_center_lat" in cfg and "mirova_center_lon" in cfg:
        existing_mc = {
            "lat": float(cfg["mirova_center_lat"]),
            "lon": float(cfg["mirova_center_lon"]),
            "offset_from_vent_km": round(_haversine_km(
                vent_lat, vent_lon,
                float(cfg["mirova_center_lat"]),
                float(cfg["mirova_center_lon"])), 3),
        }

    return {
        "volcano": volcano,
        "n_records": len(records),
        "n_pixels_within_2x_inner": len(pixels),
        "vent_nominal": [vent_lat, vent_lon],
        "inner_radius_km": inner_km,
        "observed_centroid": list(centroid),
        "proposed_mirova_center": proposed,
        "existing_yaml_mirova_center": existing_mc,
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--records", default=None,
                    help="Path al JSON; default data/mirova_equivalent/<volcano>.json")
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--threshold-km", type=float, default=0.5)
    args = ap.parse_args()

    records = (Path(args.records) if args.records
               else Path(f"data/mirova_equivalent/{args.volcano}.json"))
    out = run(
        volcano=args.volcano,
        records_json=records,
        volcanoes_yaml=Path(args.yaml),
        offset_threshold_km=args.threshold_km,
    )

    Path(args.output_json).write_text(json.dumps(out, indent=2, default=str),
                                       encoding="utf-8")
    print(f"OK · {args.volcano}")
    print(f"  n_pixels={out['n_pixels_within_2x_inner']}")
    print(f"  vent_nominal={out['vent_nominal']}")
    print(f"  observed_centroid={out['observed_centroid']}")
    print(f"  proposed={out['proposed_mirova_center']}")
    print(f"  existing_yaml_mc={out['existing_yaml_mirova_center']}")


if __name__ == "__main__":
    _main()
