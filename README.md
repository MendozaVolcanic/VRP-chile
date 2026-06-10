# VRP Chile — Volcanic Radiative Power Monitor

[![NRT Pipeline](https://github.com/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml/badge.svg)](https://github.com/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml)
[![Pages Deploy](https://github.com/MendozaVolcanic/VRP-chile/actions/workflows/pages-deploy.yml/badge.svg)](https://github.com/MendozaVolcanic/VRP-chile/actions/workflows/pages-deploy.yml)

**Near-Real-Time thermal monitoring of Chilean volcanoes using MODIS and VIIRS satellite data.**

Independent implementation of the MIROVA algorithm (Coppola et al. 2016, SP 426.5) with
automated satellite data processing, anomaly detection, and a web dashboard — all
self-hosted on GitHub. Goal: a literal MIROVA clone for the Chilean Tier A volcanoes,
operationally independent of mirovaweb.it.

**Live dashboard:** https://mendozavolcanic.github.io/VRP-chile/

---

## Volcanoes monitored

**11 Tier A volcanoes** (those actively monitored by MIROVA, with reference data for
calibration), uniform 25 km ROI radius, per-volcano `inner_radius_km` from the official
MIROVA KMLs:

| Volcano | inner (km) | Volcano | inner (km) |
|---------|-----------|---------|-----------|
| Lascar | 5 | Llaima | 5 |
| Lastarria | 3 | Villarrica | 5 |
| Isluga | 5 | Chaitén | 5 |
| Tupungatito | 7 | Puyehue–Cordón Caulle | 20 |
| Planchón–Peteroa | 3 | Copahue | 4 |
| Nevados de Chillán | 5 | | |

34 additional volcanoes are configured under the `experimental` profile (outside the
operational dashboard).

---

## Features

### Pipeline
- **8 satellite streams**: MODIS Terra/Aqua (1 km), VIIRS SNPP/NOAA-20/NOAA-21 I-band
  (375 m) and M-band (750 m)
- **Wooster MIR radiance VRP** per sensor, with empirically validated coefficients
  against the official MIROVA OSF v2.5 archive (error ≤0.17%): MODIS 18.9,
  VIIRS 750 m 19.7, VIIRS 375 m 18.0
- **Nadir-fixed pixel area** (MIROVA literal clone): constant-area grid like MIROVA,
  no sec³ off-nadir scaling (adopted after A/B validation vs MIROVA ground truth)
- **Detection anchored to the physical crater** (`vent_lat/lon`), while the 50×50 km
  grid uses the official MIROVA grid center — these are decoupled on purpose
- **Detection paths**: NTI absolute, dNTI contextual (8-neighbor kernel, Coppola 2016a
  Tests 2–3 with dual-ROI summit/scene thresholds), ETI quadratic scene + second-pass,
  and the **integrated-ROI Test 1** for spatially-extended sub-pixel anomalies
  (lava lakes ~0.05–0.5 MW that no individual pixel can reveal)
- **Vent-anchored cluster aggregation**: `primary_cluster` is what MIROVA reports
  (the summit cluster), kept separate from scene-wide totals
- **TIR VRP** (VIIRS I05, 11.45 µm): Stefan-Boltzmann (Aveni et al. 2024, TIRVolcH)
- **Night-time only MIR processing** (solar contamination barrier at fetch, process and
  store stages)
- **Resilient NRT fetch**: NASA auth probe with budget, per-host circuit breaker for
  LANCE outages, NRT→Standard product auto-upgrade
- **Automated via GitHub Actions**: cron every 2 hours, matrix per volcano, no server

### Dashboard (frontend — 3 standalone views)
- **`index.html`** — main dashboard: VRP time series (Chart.js), hotspot map (Leaflet)
  with crater-distance classification, MIROVA reference overlay, VRE cumulative energy,
  CSV export
- **`diario.html`** — 90-day per-volcano trend view with MIROVA per-sensor comparison
- **`mosaico.html`** — 48 h / 30 d overview across all volcanoes
- Display toggles: cluster vs core magnitude, "crater only" vs include-far detections,
  artifact suppression for known cirrus/diffuse-field cases

---

## Architecture

```
VRP-Chile/
|-- .github/workflows/
|   |-- nrt.yml                   NRT pipeline (cron 2h, matrix 11 volcanoes)
|   |-- pages-deploy.yml          Dashboard deploy on push
|   |-- sync-mirova-csv.yml       MIROVA reference CSV sync
|   |-- _archive/                 One-off A/B and reproc workflows (history)
|-- pipeline/
|   |-- fetch.py                  NASA Earthdata download (earthaccess) + circuit breaker
|   |-- process_modis.py          MODIS Band 21/22 (1 km, 3.93 um)
|   |-- process_viirs.py          VIIRS I-band I04/I05 (375 m)
|   |-- process_viirs_mod.py      VIIRS M-band M13 (750 m)
|   |-- test1_integrated.py       Integrated-ROI Test 1 (sub-pixel detection)
|   |-- clustering.py             Vent-anchored cluster aggregation
|   |-- scan_geometry.py          Pixel areas, haversine, ROI masks
|   |-- geo_utils.py              Grid center vs detection anchor (crater)
|   |-- detection_context.py      dNTI contextual kernel
|   |-- store.py                  JSON persistence + gates
|   |-- profile.py                Profile/flag system (mirova_equivalent, experimental, A/B)
|   |-- mirova_csv_loader.py      Canonical MIROVA reference loader (CONS + OCR)
|-- scripts/run_pipeline.py       CLI entry point
|-- frontend/                     3 standalone views (see above)
|-- data/
|   |-- mirova_equivalent/        Operational records per volcano (11 Tier A)
|   |-- experimental/             34 additional volcanoes
|   |-- mirova_reference/         MIROVA OSF v2.5 + scraped reference data
|-- docs/                         Living documentation (see docs/INDEX.md)
|-- volcanoes.yaml                Volcano configuration
```

---

## Algorithm (MIROVA-equivalent)

### VRP (MIR)

Wooster MIR radiance method (Coppola et al. 2016a):

```
VRP = k_sensor * A_pix_nadir * (L_hot - L_bg)    [W]
```

- `L` via Planck inversion at the MIR band; `L_bg` = background from the annulus
- `A_pix_nadir` = **fixed nadir pixel area** (1 km² MODIS, 140,625 m² VIIRS-I,
  562,500 m² VIIRS-M) — MIROVA resamples to a constant-area grid, so does this pipeline
- `k_sensor` empirically validated against MIROVA OSF v2.5 (48k Chilean rows)

### Detection

Per-pixel paths (NTI absolute > K1; dNTI contextual vs 8 neighbors with summit/scene
dual thresholds; ETI quadratic + second-pass adjacent recapture) **plus** the
integrated-ROI **Test 1** that sums the MIR excess over the 3 km summit ROI and fires
on the propagated σ — this is what detects sub-pixel lava lakes that no single pixel
reveals. Detections are clustered (≈1 km connectivity) and the vent-anchored
`primary_cluster` is reported, mirroring MIROVA's per-overpass product.

### Night-time only

MIR is solar-contaminated by day. Three barriers: granule day/night flag at fetch,
solar elevation at processing, and a final gate at store.

---

## Setup

### NASA Earthdata
Register free at https://urs.earthdata.nasa.gov. Locally use `.env` / `.netrc`;
on GitHub Actions set the secrets `EARTHDATA_USERNAME` / `EARTHDATA_PASSWORD`
(optionally `EARTHDATA_TOKEN`).

### Install

```bash
conda create -n vrp python=3.11 && conda activate vrp
conda install -c conda-forge pyhdf        # MODIS HDF4 — Linux/Actions only on Windows
pip install -r requirements.txt
```

### Run

```bash
# NRT window (default: last days including today)
python scripts/run_pipeline.py --volcano Villarrica

# Historical reprocess (run on Actions for long windows)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar \
    --start 2026-04-01 --end 2026-06-01
```

Note: `pyhdf` is broken on Windows — MODIS processing runs on GitHub Actions (Linux).
Long reprocesses must be chunked (Actions soft timeout) or run via the archived
reproc workflows pattern.

---

## Data format (per record, simplified)

```json
{
  "sensor": "VIIRS_NOAA20",
  "datetime_utc": "2026-05-22 05:54",
  "vrp_mw": 0.55,
  "primary_cluster": {
    "vrp_mw": 0.51, "n_pixels": 3,
    "centroid_lat": -39.4203, "centroid_lon": -71.9400,
    "centroid_dist_km": 0.19, "geo_class": "summit"
  },
  "final_hotspot_lat": -39.4203, "final_hotspot_lon": -71.9400,
  "final_hotspot_dist_km": 0.19, "final_hotspot_source": "test1",
  "triggered_test1": true, "n_anomalous_pixels": 3,
  "anomaly_pixels": [{ "lat": -39.4203, "lon": -71.94, "dist_km": 0.19,
                       "bt_k": 295.1, "vrp_mw": 0.31 }],
  "t_bg_k": 268.4, "t_max_k": 295.1,
  "product_version": "standard"
}
```

`primary_cluster.vrp_mw` is the MIROVA-comparable magnitude (summit cluster);
`vrp_mw` at record level is the scene-wide sum (diagnostic). Sensor naming:
`VIIRS_<SAT>` = I-band 375 m, `VIIRS_<SAT>_750` = M-band.

---

## MIROVA energy scale

| VRP | Class |
|-----|-------|
| < 1 MW | Very Low |
| 1–10 MW | Low |
| 10–100 MW | Moderate |
| 100–1000 MW | High |
| > 1000 MW | Very High |

---

## Known limitations / open fronts

Tracked formally in `docs/MIROVA_DIVERGENCES.md` (open: D2, D3, D9, D11):

1. **Topographic bias of MIR-absolute paths on snow-capped volcanoes** (D11): the
   integrated Test 1 can drift ~1 km toward warm low-altitude terrain on
   Villarrica/Tupungatito/Llaima. Position-only (alerting and magnitude unaffected).
   A uniform local-background fix is under A/B validation.
2. **Path D contextual on warm/cirrus scenes** (D9): can inflate cluster magnitude on
   MODIS for a small fraction of records (~4%); mitigated by caps, root cause open.
3. MIROVA reference CSVs are scraped NRT data (~70–80% VIIRS coverage) — comparisons
   are operationally meaningful but not archival-complete.
4. MODIS 1 km cannot resolve weak sub-pixel signals (faint lava lakes are
   VIIRS 375 m territory).

---

## References

- **Coppola et al. 2016a** — MIROVA system (Wooster MIR method, NTI, Tests 1–3).
  *Geol. Soc. London Special Publication 426.5*
- **Coppola et al. 2024** — Thermal monitoring chapter (integrated cluster background,
  Eq. 13). *Springer*
- **Aveni et al. 2024** — TIRVolcH TIR detection. *Remote Sensing of Environment 315*
- **Wooster et al. 2003** — MIR radiance method foundations. *Remote Sens. Environ.*
- MIROVA OSF v2.5 archive — empirical coefficient validation (615k global rows)

---

## License

Research and educational purposes. Satellite data: NASA LANCE/Earthdata.
Developed for volcanic surveillance support (SERNAGEOMIN/OVDAS context) — not an
official monitoring product.
