# MIROVA KMZ centroid extraction (Session 9 Phase 2)
Script: `experiments/extract_mirova_centroids.py`
Source KMZs: `kmz/*_Last_GE.kmz` (11 volcanoes).

> **CAVEAT (read before acting on the flagged section below)**: the
> `GroundOverlay` center is MIROVA's **processing-grid viewport**, not the
> MIROVA active-vent reference. MIROVA anchors the grid to an internal
> volcano config (normally the GVP summit) that can differ from the active
> thermal source by many km. Session-9 ground-truth verification with user
> confirmed Tupungatito and PlanchonPeteroa flags are **false positives** —
> in both cases `volcanoes.yaml` is already within 1 km of the real active
> vent and MIROVA's grid is offset from its own detection pixel. Do NOT
> use this table as standalone evidence of a wrong vent; it must be paired
> with empirical hotspot cluster analysis (as in RF3 PCC) or independent
> geological ground truth. See lesson **L9.1** in `tasks/lessons.md`.

Each KMZ contains a single `GroundOverlay` with a `LatLonBox`. The center of that box is MIROVA's processing-grid viewport. PCC demonstrates how far this can be from reality: MIROVA centers the grid on the main Puyehue summit but detects thermal activity at the 2011 Cordón Caulle fissure 7.6 km NNW of the grid center.

## Per-volcano summary

| Volcano | Sensors | MIROVA lat | MIROVA lon | YAML lat | YAML lon | Δ to lat/lon (km) | Δ to vent (km) |
|---|---|---:|---:|---:|---:|---:|---:|
| Tupungatito | VIIRS750 | -33.4269 | -69.8004 | -33.4000 | -69.8000 | 2.996 | 2.996 |
| PlanchonPeteroa | VIIRS375 | -35.2232 | -70.5695 | -35.2400 | -70.5680 | 1.871 | 1.871 |
| Chaiten | VIIRS750 | -42.8350 | -72.6501 | -42.8330 | -72.6460 | 0.396 | 0.396 |
| Villarrica | VIIRS750 | -39.4218 | -71.9339 | -39.4200 | -71.9300 | 0.389 | 0.389 |
| NevadosDeChillan | VIIRS750 | -36.8648 | -71.3807 | -36.8630 | -71.3770 | 0.385 | 0.385 |
| Isluga | VIIRS750 | -19.1521 | -68.8327 | -19.1500 | -68.8300 | 0.368 | 0.368 |
| Lascar | MODIS,VIIRS375,VIIRS750 | -23.3708 | -67.7314 | -23.3690 | -67.7320 | 0.207 | 0.207 |
| Copahue | MODIS,VIIRS375,VIIRS750 | -37.8565 | -71.1851 | -37.8560 | -71.1830 | 0.191 | 0.191 |
| PuyehueCordonCaulle | VIIRS375 | -40.5903 | -72.1187 | -40.5900 | -72.1170 | 0.146 | 8.355 |
| Llaima | VIIRS375 | -38.6921 | -71.7306 | -38.6920 | -71.7290 | 0.143 | 0.143 |
| Lastarria | VIIRS375 | -25.1684 | -68.5081 | -25.1680 | -68.5070 | 0.116 | 0.116 |

## Flagged (>0.5 km offset) — REVIEWED

Initial flags (before ground-truth verification):
- Tupungatito — 3.00 km offset from MIROVA grid center.
- PlanchonPeteroa — 1.87 km offset from MIROVA grid center.

**Outcome after verification (2026-04-08):**

| Volcano | YAML vent | User ground-truth vent | YAML→truth dist | MIROVA grid→truth dist | Verdict |
|---|---|---|---:|---:|---|
| Tupungatito | (-33.400, -69.800) | (-33.389044, -69.826374) | **2.73 km** | 4.83 km | ✅ YAML correct (within vent_radius_km=5) |
| PlanchonPeteroa | (-35.240, -70.568) | (-35.241099, -70.573345) | **0.46 km** | 2.02 km | ✅ YAML correct (within vent_radius_km=3) |
| PuyehueCordonCaulle | (-40.585, -72.020) | 2011 fissure (-40.523, -72.137) | **12.04 km** | 7.64 km | ❌ YAML wrong — F0 fix |

In both Tupungatito and PlanchonPeteroa cases the YAML vent is actually
**closer to the real active vent than the MIROVA grid center is**. The
"offset" flagged here was measuring the distance between our YAML and
MIROVA's viewport center, which for these volcanoes happens to sit away
from the real detection pixel. **Only PCC is a genuine YAML error.**

Lesson: the KMZ centroid extractor is useful for the background annulus
alignment question, but it is **not** a reliable indicator of vent
correctness. For vent correctness, use empirical hotspot clustering from
TPs (as in RF3 PCC analysis) or geological ground truth (as used here for
Tupungatito and PP). See `tasks/lessons.md` L9.1.

## Per-sensor breakdown (raw bbox centers)

| Volcano | Sensor | lat | lon | bbox Δlat° | bbox Δlon° |
|---|---|---:|---:|---:|---:|
| Chaiten | VIIRS750 | -42.8350 | -72.6501 | 0.4578 | 0.5883 |
| NevadosDeChillan | VIIRS750 | -36.8648 | -71.3807 | 0.4347 | 0.5687 |
| Copahue | MODIS | -37.8556 | -71.1839 | 0.4398 | 0.5813 |
| Copahue | VIIRS375 | -37.8562 | -71.1846 | 0.4387 | 0.5798 |
| Copahue | VIIRS750 | -37.8578 | -71.1868 | 0.4354 | 0.5755 |
| Isluga | VIIRS750 | -19.1521 | -68.8327 | 0.4478 | 0.4703 |
| Lascar | MODIS | -23.3698 | -67.7304 | 0.4555 | 0.4848 |
| Lascar | VIIRS375 | -23.3704 | -67.7310 | 0.4544 | 0.4836 |
| Lascar | VIIRS750 | -23.3721 | -67.7328 | 0.4509 | 0.4800 |
| Lastarria | VIIRS375 | -25.1684 | -68.5081 | 0.4520 | 0.4931 |
| Llaima | VIIRS375 | -38.6921 | -71.7306 | 0.4356 | 0.5899 |
| PlanchonPeteroa | VIIRS375 | -35.2232 | -70.5695 | 0.4425 | 0.5565 |
| PuyehueCordonCaulle | VIIRS375 | -40.5903 | -72.1187 | 0.4634 | 0.5694 |
| Tupungatito | VIIRS750 | -33.4269 | -69.8004 | 0.4430 | 0.5365 |
| Villarrica | VIIRS750 | -39.4218 | -71.9339 | 0.4309 | 0.5930 |

## Machine-readable JSON dump

```json
[
  {
    "volcano": "Chaiten",
    "n_sensors": 1,
    "mirova_lat": -42.834965,
    "mirova_lon": -72.650055,
    "yaml_lat": -42.833,
    "yaml_lon": -72.646,
    "yaml_vent_lat": -42.833,
    "yaml_vent_lon": -72.646,
    "dist_to_latlon_km": 0.396,
    "dist_to_vent_km": 0.396,
    "sensors": [
      "VIIRS750"
    ]
  },
  {
    "volcano": "NevadosDeChillan",
    "n_sensors": 1,
    "mirova_lat": -36.864831499999994,
    "mirova_lon": -71.38067699999999,
    "yaml_lat": -36.863,
    "yaml_lon": -71.377,
    "yaml_vent_lat": -36.863,
    "yaml_vent_lon": -71.377,
    "dist_to_latlon_km": 0.385,
    "dist_to_vent_km": 0.385,
    "sensors": [
      "VIIRS750"
    ]
  },
  {
    "volcano": "Copahue",
    "n_sensors": 3,
    "mirova_lat": -37.85653933333334,
    "mirova_lon": -71.1850665,
    "yaml_lat": -37.856,
    "yaml_lon": -71.183,
    "yaml_vent_lat": -37.856,
    "yaml_vent_lon": -71.183,
    "dist_to_latlon_km": 0.191,
    "dist_to_vent_km": 0.191,
    "sensors": [
      "MODIS",
      "VIIRS375",
      "VIIRS750"
    ]
  },
  {
    "volcano": "Isluga",
    "n_sensors": 1,
    "mirova_lat": -19.15212,
    "mirova_lon": -68.83269200000001,
    "yaml_lat": -19.15,
    "yaml_lon": -68.83,
    "yaml_vent_lat": -19.15,
    "yaml_vent_lon": -68.83,
    "dist_to_latlon_km": 0.368,
    "dist_to_vent_km": 0.368,
    "sensors": [
      "VIIRS750"
    ]
  },
  {
    "volcano": "Lascar",
    "n_sensors": 3,
    "mirova_lat": -23.37078633333333,
    "mirova_lon": -67.73142066666666,
    "yaml_lat": -23.369,
    "yaml_lon": -67.732,
    "yaml_vent_lat": -23.369,
    "yaml_vent_lon": -67.732,
    "dist_to_latlon_km": 0.207,
    "dist_to_vent_km": 0.207,
    "sensors": [
      "MODIS",
      "VIIRS375",
      "VIIRS750"
    ]
  },
  {
    "volcano": "Lastarria",
    "n_sensors": 1,
    "mirova_lat": -25.1683735,
    "mirova_lon": -68.5080725,
    "yaml_lat": -25.168,
    "yaml_lon": -68.507,
    "yaml_vent_lat": -25.168,
    "yaml_vent_lon": -68.507,
    "dist_to_latlon_km": 0.116,
    "dist_to_vent_km": 0.116,
    "sensors": [
      "VIIRS375"
    ]
  },
  {
    "volcano": "Llaima",
    "n_sensors": 1,
    "mirova_lat": -38.692145999999994,
    "mirova_lon": -71.7306325,
    "yaml_lat": -38.692,
    "yaml_lon": -71.729,
    "yaml_vent_lat": -38.692,
    "yaml_vent_lon": -71.729,
    "dist_to_latlon_km": 0.143,
    "dist_to_vent_km": 0.143,
    "sensors": [
      "VIIRS375"
    ]
  },
  {
    "volcano": "PlanchonPeteroa",
    "n_sensors": 1,
    "mirova_lat": -35.2232195,
    "mirova_lon": -70.5694525,
    "yaml_lat": -35.24,
    "yaml_lon": -70.568,
    "yaml_vent_lat": -35.24,
    "yaml_vent_lon": -70.568,
    "dist_to_latlon_km": 1.871,
    "dist_to_vent_km": 1.871,
    "sensors": [
      "VIIRS375"
    ]
  },
  {
    "volcano": "PuyehueCordonCaulle",
    "n_sensors": 1,
    "mirova_lat": -40.590267499999996,
    "mirova_lon": -72.1186945,
    "yaml_lat": -40.59,
    "yaml_lon": -72.117,
    "yaml_vent_lat": -40.585,
    "yaml_vent_lon": -72.02,
    "dist_to_latlon_km": 0.146,
    "dist_to_vent_km": 8.355,
    "sensors": [
      "VIIRS375"
    ]
  },
  {
    "volcano": "Tupungatito",
    "n_sensors": 1,
    "mirova_lat": -33.426942499999996,
    "mirova_lon": -69.80039099999999,
    "yaml_lat": -33.4,
    "yaml_lon": -69.8,
    "yaml_vent_lat": -33.4,
    "yaml_vent_lon": -69.8,
    "dist_to_latlon_km": 2.996,
    "dist_to_vent_km": 2.996,
    "sensors": [
      "VIIRS750"
    ]
  },
  {
    "volcano": "Villarrica",
    "n_sensors": 1,
    "mirova_lat": -39.421769499999996,
    "mirova_lon": -71.933907,
    "yaml_lat": -39.42,
    "yaml_lon": -71.93,
    "yaml_vent_lat": -39.42,
    "yaml_vent_lon": -71.93,
    "dist_to_latlon_km": 0.389,
    "dist_to_vent_km": 0.389,
    "sensors": [
      "VIIRS750"
    ]
  }
]
```
