#!/usr/bin/env python3
"""
extract_mirova_centroids.py — Phase 2 support (Session 9)

Parses every MIROVA KMZ under `kmz/` and extracts the LatLonBox center
of the GroundOverlay. That center corresponds to the geographic center
of MIROVA's processing grid for the volcano, which in practice is
anchored to the MIROVA reference coordinate (typically the GVP summit
but not always).

For each volcano:
  - averages the per-sensor centers (they differ at the 100–400 m level
    due to sensor-specific grid quantization)
  - loads the current `volcanoes.yaml` entry
  - computes haversine distance between MIROVA center and our `lat/lon`
  - also reports distance to our `vent_lat/vent_lon` if present
  - flags any volcano where |delta| > 0.5 km

Output:
  - stdout: per-sensor table + summary
  - experiments/mirova_centroids.md: machine-readable + human-readable
    report ready to cross-check against AUDIT_S9_baseline red flags.

Why this matters: the S9 audit (RF3) already discovered that PCC's
`vent_lat/vent_lon` points in the wrong direction. This script provides
an independent, cheap cross-check for the other 10 volcanoes using
MIROVA's own grid geometry as a reference.

Usage:
    python experiments/extract_mirova_centroids.py

Limitations:
  - The LatLonBox center is the MIROVA GRID center, NOT necessarily the
    active vent (cf. PCC where MIROVA centers the grid on the main
    Puyehue summit but real detections happen at the 2011 fissure
    7.7 km NNW). A discrepancy here is a *necessary but not sufficient*
    indicator of a misconfigured vent.
  - It does not touch the per-pass thermal detections inside the TIF
    rasters. Those are full GeoTIFFs with GeoKeys that PIL cannot read;
    if we ever need per-pixel VRP comparison we should add a rasterio
    path.
"""
from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # PyYAML

REPO_ROOT = Path(__file__).resolve().parent.parent
KMZ_DIR = REPO_ROOT / "kmz"
YAML_PATH = REPO_ROOT / "volcanoes.yaml"
OUT_MD = REPO_ROOT / "experiments" / "mirova_centroids.md"

# Map KMZ stems (the bit before `_<SENSOR>_Last_GE.kmz`) to volcanoes.yaml
# `name` field. MIROVA uses "ChillanNevadosde" for our "NevadosDeChillan".
STEM_TO_YAML_NAME = {
    "Chaiten": "Chaiten",
    "ChillanNevadosde": "NevadosDeChillan",
    "Copahue": "Copahue",
    "Isluga": "Isluga",
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Llaima": "Llaima",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "PuyehueCordonCaulle": "PuyehueCordonCaulle",
    "Tupungatito": "Tupungatito",
    "Villarrica": "Villarrica",
}

KMZ_NAME_RE = re.compile(
    r"^(?P<stem>[A-Za-z]+)_(?P<sensor>MODIS|VIIRS375|VIIRS750)_Last_GE\.kmz$"
)

LATLONBOX_RE = re.compile(
    r"<north>\s*([-\d.]+)\s*</north>\s*"
    r"<south>\s*([-\d.]+)\s*</south>\s*"
    r"<east>\s*([-\d.]+)\s*</east>\s*"
    r"<west>\s*([-\d.]+)\s*</west>",
    re.IGNORECASE,
)


@dataclass
class SensorCenter:
    sensor: str
    lat: float
    lon: float
    bbox_n: float
    bbox_s: float
    bbox_e: float
    bbox_w: float

    @property
    def dlat_deg(self) -> float:
        return self.bbox_n - self.bbox_s

    @property
    def dlon_deg(self) -> float:
        return self.bbox_e - self.bbox_w


@dataclass
class VolcanoResult:
    stem: str
    yaml_name: str | None
    sensors: list[SensorCenter] = field(default_factory=list)
    yaml_lat: float | None = None
    yaml_lon: float | None = None
    yaml_vent_lat: float | None = None
    yaml_vent_lon: float | None = None

    @property
    def mirova_lat(self) -> float:
        return sum(s.lat for s in self.sensors) / len(self.sensors)

    @property
    def mirova_lon(self) -> float:
        return sum(s.lon for s in self.sensors) / len(self.sensors)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_kmz(path: Path) -> tuple[str, SensorCenter] | None:
    m = KMZ_NAME_RE.match(path.name)
    if not m:
        return None
    stem = m.group("stem")
    sensor = m.group("sensor")
    with zipfile.ZipFile(path) as z:
        kml_name = next((n for n in z.namelist() if n.lower().endswith(".kml")), None)
        if kml_name is None:
            return None
        kml = z.read(kml_name).decode("utf-8", errors="replace")
    bbox = LATLONBOX_RE.search(kml)
    if not bbox:
        return None
    n, s, e, w = map(float, bbox.groups())
    center = SensorCenter(
        sensor=sensor,
        lat=(n + s) / 2,
        lon=(e + w) / 2,
        bbox_n=n,
        bbox_s=s,
        bbox_e=e,
        bbox_w=w,
    )
    return stem, center


def load_yaml_volcanoes() -> dict[str, dict[str, Any]]:
    with YAML_PATH.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return {v["name"]: v for v in doc["volcanoes"]}


def main() -> int:
    # Windows consoles default to cp1252 which chokes on non-latin1 glyphs
    # (Δ, μ, etc). Force UTF-8 so the human-readable stdout report matches
    # the markdown file.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    if not KMZ_DIR.is_dir():
        print(f"error: {KMZ_DIR} not found", file=sys.stderr)
        return 1

    yaml_index = load_yaml_volcanoes()

    results: dict[str, VolcanoResult] = {}
    unknown_stems: list[str] = []
    for kmz_path in sorted(KMZ_DIR.glob("*.kmz")):
        parsed = parse_kmz(kmz_path)
        if parsed is None:
            print(f"skip (unparsed): {kmz_path.name}", file=sys.stderr)
            continue
        stem, center = parsed
        yaml_name = STEM_TO_YAML_NAME.get(stem)
        if yaml_name is None:
            unknown_stems.append(stem)
            continue
        if stem not in results:
            results[stem] = VolcanoResult(stem=stem, yaml_name=yaml_name)
        results[stem].sensors.append(center)

    # Attach yaml coords
    for r in results.values():
        if r.yaml_name and r.yaml_name in yaml_index:
            entry = yaml_index[r.yaml_name]
            r.yaml_lat = entry.get("lat")
            r.yaml_lon = entry.get("lon")
            r.yaml_vent_lat = entry.get("vent_lat")
            r.yaml_vent_lon = entry.get("vent_lon")

    # ---------------- stdout report ----------------
    print("MIROVA KMZ centroid extraction — Session 9 Phase 2 support")
    print("=" * 78)
    print()
    print("Per-sensor raw centers:")
    print(f"{'Volcano':<22s} {'Sensor':<9s} {'lat':>10s} {'lon':>11s} "
          f"{'bbox_dlat':>9s} {'bbox_dlon':>9s}")
    for stem in sorted(results):
        r = results[stem]
        for c in sorted(r.sensors, key=lambda x: x.sensor):
            print(f"{stem:<22s} {c.sensor:<9s} {c.lat:>10.4f} {c.lon:>11.4f} "
                  f"{c.dlat_deg:>9.4f} {c.dlon_deg:>9.4f}")

    print()
    print("Per-volcano summary (averaged across sensors):")
    print(f"{'Volcano':<22s} {'n':>2s} {'MIROVA lat':>11s} {'MIROVA lon':>12s} "
          f"{'YAML lat':>11s} {'YAML lon':>12s} {'Δ to lat/lon km':>17s} "
          f"{'Δ to vent km':>14s}")
    flagged: list[tuple[str, float]] = []
    summary_rows: list[dict[str, Any]] = []
    for stem in sorted(results):
        r = results[stem]
        if r.yaml_lat is None:
            continue
        d_main = haversine_km(r.mirova_lat, r.mirova_lon, r.yaml_lat, r.yaml_lon)
        if r.yaml_vent_lat is not None:
            d_vent = haversine_km(
                r.mirova_lat, r.mirova_lon, r.yaml_vent_lat, r.yaml_vent_lon
            )
            d_vent_str = f"{d_vent:>14.3f}"
        else:
            d_vent = None
            d_vent_str = f"{'—':>14s}"
        print(f"{r.yaml_name:<22s} {len(r.sensors):>2d} "
              f"{r.mirova_lat:>11.4f} {r.mirova_lon:>12.4f} "
              f"{r.yaml_lat:>11.4f} {r.yaml_lon:>12.4f} "
              f"{d_main:>17.3f} {d_vent_str}")
        summary_rows.append(
            {
                "volcano": r.yaml_name,
                "n_sensors": len(r.sensors),
                "mirova_lat": r.mirova_lat,
                "mirova_lon": r.mirova_lon,
                "yaml_lat": r.yaml_lat,
                "yaml_lon": r.yaml_lon,
                "yaml_vent_lat": r.yaml_vent_lat,
                "yaml_vent_lon": r.yaml_vent_lon,
                "dist_to_latlon_km": round(d_main, 3),
                "dist_to_vent_km": round(d_vent, 3) if d_vent is not None else None,
                "sensors": [c.sensor for c in sorted(r.sensors, key=lambda x: x.sensor)],
            }
        )
        if d_main > 0.5:
            flagged.append((r.yaml_name, d_main))

    print()
    if flagged:
        print("FLAGGED (MIROVA center differs from volcanoes.yaml lat/lon by >0.5 km):")
        for name, d in sorted(flagged, key=lambda x: -x[1]):
            print(f"  - {name:<22s} {d:>6.2f} km")
    else:
        print("No volcano flagged at >0.5 km offset.")

    if unknown_stems:
        print()
        print(f"Unknown KMZ stems (not mapped in STEM_TO_YAML_NAME): {sorted(set(unknown_stems))}")

    # ---------------- markdown report ----------------
    md_lines: list[str] = []
    md_lines.append("# MIROVA KMZ centroid extraction (Session 9 Phase 2)\n")
    md_lines.append("Script: `experiments/extract_mirova_centroids.py`\n")
    md_lines.append("Source KMZs: `kmz/*_Last_GE.kmz` (11 volcanoes).\n")
    md_lines.append("\n")
    md_lines.append("Each KMZ contains a single `GroundOverlay` with a `LatLonBox`. ")
    md_lines.append("The center of that box is MIROVA's processing-grid reference. ")
    md_lines.append("This is **not necessarily the active vent** — see the PCC case in ")
    md_lines.append("`ROOT_CAUSE_S9.md` RF3 where MIROVA centers the grid on the main ")
    md_lines.append("summit but detects thermal activity at the 2011 fissure 7.7 km NNW.\n")
    md_lines.append("\n")
    md_lines.append("## Per-volcano summary\n")
    md_lines.append("\n")
    md_lines.append("| Volcano | Sensors | MIROVA lat | MIROVA lon | YAML lat | YAML lon | Δ to lat/lon (km) | Δ to vent (km) |\n")
    md_lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for row in sorted(summary_rows, key=lambda x: -x["dist_to_latlon_km"]):
        sens = ",".join(row["sensors"])
        dv = f"{row['dist_to_vent_km']:.3f}" if row["dist_to_vent_km"] is not None else "—"
        md_lines.append(
            f"| {row['volcano']} | {sens} | "
            f"{row['mirova_lat']:.4f} | {row['mirova_lon']:.4f} | "
            f"{row['yaml_lat']:.4f} | {row['yaml_lon']:.4f} | "
            f"{row['dist_to_latlon_km']:.3f} | {dv} |\n"
        )
    md_lines.append("\n")

    if flagged:
        md_lines.append("## Flagged (>0.5 km offset)\n\n")
        for name, d in sorted(flagged, key=lambda x: -x[1]):
            md_lines.append(f"- **{name}** — {d:.2f} km offset from MIROVA grid center.\n")
        md_lines.append("\n")
        md_lines.append("These warrant cross-checking with `audit_s9/<volcano>.json` ")
        md_lines.append("to see whether the FN records cluster inside the MIROVA grid ")
        md_lines.append("but outside our ROI, similar to the PCC case (RF3).\n")
    else:
        md_lines.append("## Flagged (>0.5 km offset)\n\nNone.\n")
    md_lines.append("\n")

    md_lines.append("## Per-sensor breakdown (raw bbox centers)\n\n")
    md_lines.append("| Volcano | Sensor | lat | lon | bbox Δlat° | bbox Δlon° |\n")
    md_lines.append("|---|---|---:|---:|---:|---:|\n")
    for stem in sorted(results):
        r = results[stem]
        for c in sorted(r.sensors, key=lambda x: x.sensor):
            md_lines.append(
                f"| {r.yaml_name} | {c.sensor} | {c.lat:.4f} | {c.lon:.4f} | "
                f"{c.dlat_deg:.4f} | {c.dlon_deg:.4f} |\n"
            )
    md_lines.append("\n")

    # Machine-readable dump at the end for downstream scripts
    md_lines.append("## Machine-readable JSON dump\n\n```json\n")
    md_lines.append(json.dumps(summary_rows, indent=2, ensure_ascii=False))
    md_lines.append("\n```\n")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("".join(md_lines), encoding="utf-8")
    print(f"\nWrote {OUT_MD.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
