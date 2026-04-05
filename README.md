# VRP Chile — Volcanic Radiative Power Monitor

**Near-Real-Time thermal monitoring of Chilean volcanoes using MODIS and VIIRS satellite data.**

Independent implementation of the MIROVA algorithm (Coppola et al. 2015) with automated satellite data processing, anomaly detection, and a web dashboard — all self-hosted on GitHub.

**Live dashboard:** https://mendozavolcanic.github.io/VRP-chile/

---

## Volcanoes monitored

| Volcano | Coordinates | Altitude | ROI radius | Activity |
|---------|------------|----------|------------|----------|
| Puyehue - Cordon Caulle | 40.59S, 72.12W | 2236 m | 15 km | Persistent fumarolic anomaly since 2011 |
| Villarrica | 39.42S, 71.93W | 2847 m | 10 km | Open lava lake, frequent thermal anomalies |
| Lascar | 23.37S, 67.73W | 5592 m | 10 km | Fumarolic activity, occasional eruptions |
| Copahue | 37.86S, 71.18W | 2997 m | 10 km | Active crater lake, recurring thermal unrest |

---

## Features

### Pipeline
- **6 satellite sensors**: MODIS Terra/Aqua (1 km), VIIRS SNPP/NOAA-20 I-band (375 m), VIIRS SNPP/NOAA-20 M-band (750 m)
- **Wooster MIR radiance VRP** (Coppola 2015, Eq. 7): `VRP = 18.9 * A_pix * (L_hot - L_bg)` via Planck inversion
- **TIR VRP** for VIIRS I05 (11.45 um): Stefan-Boltzmann method (Aveni et al. 2024)
- **NTI dual-criteria detection** for VIIRS 375 m: pixel must pass both MIR BT threshold AND NTI anomaly threshold
- **Local ROI p95 filter**: prevents topographic false positives at high-altitude volcanoes
- **Triple nighttime barrier**: solar elevation check at download, processing, and storage stages
- **Multi-pixel anomaly tracking**: all anomalous pixels recorded with lat/lon/BT/VRP per pixel
- **Automated via GitHub Actions**: cron every 6 hours, no server needed

### Dashboard (frontend)
- **VRP time series chart** (Chart.js) with sensor color coding and log scale
- **Hotspot map** (Leaflet.js): multi-pixel markers per detection, sensor-colored, click for per-pixel details
- **Distance vs Time chart**: tracks how far anomalies appear from the crater center
- **VRE (Volcanic Radiated Energy)**: cumulative thermal energy integral in GJ
- **MIROVA comparison panel**: overlay our VRP against MIROVA reference data
- **CSV export**: download filtered data for external analysis
- **Global summary panel**: quick stats across all volcanoes (total detections, max VRP, active sensors)
- **Responsive design**: works on desktop and mobile

---

## Architecture

```
VRP-Chile/
|-- .github/workflows/nrt.yml    GitHub Actions NRT pipeline (cron 6h)
|-- pipeline/
|   |-- fetch.py                  Download granules from NASA Earthdata (earthaccess)
|   |-- process_modis.py          MODIS Terra/Aqua Band 21/22 (1 km, 3.93 um)
|   |-- process_viirs.py          VIIRS I-band I04/I05 (375 m, 3.74/11.45 um)
|   |-- process_viirs_mod.py      VIIRS M-band M13 (750 m, 4.05 um)
|   |-- store.py                  JSON persistence + nighttime gate (data/*.json)
|-- scripts/
|   |-- run_pipeline.py           CLI entry point
|-- frontend/
|   |-- index.html                Single-page dashboard (Chart.js + Leaflet)
|-- data/
|   |-- {Volcano}.json            VRP time series per volcano
|   |-- mirova/{Volcano}.json     MIROVA reference data for cross-validation
|-- volcanoes.yaml                Volcano configuration (coords, radius, sensors)
|-- requirements.txt              Python dependencies
|-- .env.example                  Template for NASA credentials
```

---

## Algorithm

### VRP calculation (MIR channel)

Based on the Wooster MIR radiance method as implemented by MIROVA (Coppola et al. 2015, Eq. 7):

```
VRP = 18.9 * A_pixel * (L_hot - L_bg)    [Watts]
```

Where:
- `L_hot`, `L_bg` = spectral radiance at ~4 um via Planck function: `L = C1 / (lambda^5 * (exp(C2 / (lambda * T)) - 1))`
- `A_pixel` = pixel area in m^2 (1 km^2 for MODIS, 140,625 m^2 for VIIRS 375 m, 562,500 m^2 for VIIRS 750 m)
- `T_bg` = median brightness temperature from background annulus (5-25 km from crater)
- 18.9 = empirical MIR radiance-to-power coefficient

### Anomaly detection

A pixel is flagged as anomalous if it passes **all** of:

1. **Background threshold**: `BT_pixel > T_bg + max(5 K, 3 * sigma_bg)`
2. **Local ROI filter**: `BT_pixel > p95_ROI + max(3 K, 2 * sigma_ROI)` — prevents topographic false positives
3. **NTI filter** (VIIRS 375 m only): `NTI_pixel > NTI_bg + max(0.005, 3 * sigma_NTI)` — cancels terrain effects

### TIR VRP (VIIRS I05 only)

For low-temperature anomalies detected in the thermal infrared (11.45 um):

```
VRP_TIR = A_pixel * sigma * (T_alert^4 - T_bg^4)    [Watts]
```

Following the TIRVolcH approach (Aveni et al. 2024).

### Nighttime filtering

MIR channels (~4 um) are contaminated by reflected solar radiation during daytime. The pipeline enforces nighttime-only processing at three stages:
1. **fetch.py**: skips daytime granules before download
2. **run_pipeline.py**: solar elevation check before processing
3. **store.py**: rejects records where solar elevation > 0 degrees

Solar elevation calculated using Spencer (1971) approximation.

---

## Sensors

| Sensor | Product | Band | Wavelength | Resolution | Pixel area |
|--------|---------|------|------------|------------|------------|
| MODIS Terra | MOD021KM | 21/22 | 3.93 um | 1 km | 1,000,000 m^2 |
| MODIS Aqua | MYD021KM | 21/22 | 3.93 um | 1 km | 1,000,000 m^2 |
| VIIRS SNPP | VNP02IMG | I04 | 3.74 um | 375 m | 140,625 m^2 |
| VIIRS NOAA-20 | VJ102IMG | I04 | 3.74 um | 375 m | 140,625 m^2 |
| VIIRS SNPP | VNP02MOD | M13 | 4.05 um | 750 m | 562,500 m^2 |
| VIIRS NOAA-20 | VJ102MOD | M13 | 4.05 um | 750 m | 562,500 m^2 |

Up to 6+ VIIRS observations per day (multiple orbits x 2 satellites). MODIS provides 2-4 passes per day.

---

## Setup

### 1. NASA Earthdata credentials

Register free at https://urs.earthdata.nasa.gov/users/new

```bash
cp .env.example .env
# Edit .env with your username and password
```

### 2. Install dependencies

```bash
conda create -n vrp python=3.11
conda activate vrp
conda install -c conda-forge pyhdf
pip install -r requirements.txt
```

### 3. Run locally

```bash
# Process all volcanoes for yesterday (default)
python scripts/run_pipeline.py

# Process a specific volcano and date
python scripts/run_pipeline.py --volcano Villarrica --date 2026-03-15

# Skip nighttime filter (for analysis/debugging)
python scripts/run_pipeline.py --no-night-filter
```

### 4. GitHub Actions (NRT)

Add these GitHub Secrets to your repository:
- `EARTHDATA_USERNAME`
- `EARTHDATA_PASSWORD`

The pipeline runs automatically every 6 hours. You can also trigger it manually from the Actions tab with optional volcano/date parameters.

GitHub Pages serves the dashboard automatically after each pipeline run.

---

## Data format

Each `data/{Volcano}.json` contains an array of records:

```json
{
  "vrp_mw": 0.35,
  "n_anomalous_pixels": 2,
  "hotspot_lat": -39.4201,
  "hotspot_lon": -71.9298,
  "hotspot_dist_km": 0.85,
  "anomaly_pixels": [
    {"lat": -39.4201, "lon": -71.9298, "dist_km": 0.85, "bt_k": 312.5, "vrp_mw": 0.22},
    {"lat": -39.4195, "lon": -71.9305, "dist_km": 1.02, "bt_k": 308.1, "vrp_mw": 0.13}
  ],
  "t_bg_k": 265.3,
  "t_max_k": 312.5,
  "sensor": "VIIRS_SNPP_375",
  "granule": "VNP02IMG.A2026074.0530.002.2026074120000.nc",
  "datetime_utc": "2026-03-15 05:30"
}
```

---

## MIROVA energy scale reference

| VRP range | Classification |
|-----------|---------------|
| < 1 MW | Very Low |
| 1 - 10 MW | Low |
| 10 - 100 MW | Moderate |
| 100 - 1000 MW | High |
| > 1000 MW | Very High |

---

## Known limitations

1. No cloud masking (NTI helps partially for VIIRS; cloudy pixels produce cold BT, generally below threshold)
2. NTI only implemented for VIIRS I-band (not MODIS — would need Band 31 TIR)
3. No scan angle correction (pixel elongation at swath edges)
4. MODIS 1 km resolution cannot detect weak fumarolic signals
5. Approximate vent coordinates for Cordon Caulle (8 km offset from caldera center)

---

## References

- **Coppola et al. 2015** — MIROVA system: Wooster MIR method, NTI, coefficient 18.9. *Geological Society Special Publication 426*
- **Campus et al. 2022** — MODIS-to-VIIRS cross-calibration. *Sensors 22(5):1713*
- **Aveni et al. 2024** — TIRVolcH: TIR-based thermal detection, Stefan-Boltzmann for I05. *Remote Sensing of Environment 315:114388*
- **Coppola et al. 2023** — MIROVA database and c_rad coefficients for global volcanoes

---

## License

This project is for research and educational purposes. Satellite data provided by NASA LANCE/Earthdata.
