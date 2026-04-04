# VRP Chile — Volcanic Radiative Power Monitor

Near-Real-Time thermal monitoring of Chilean volcanoes using MODIS and VIIRS satellite data.
Independent implementation of the MIROVA algorithm (Coppola et al. 2015).

## Volcanoes monitored
- Puyehue - Cordón Caulle
- Villarrica
- Láscar
- Copahue

## How it works

Every 6 hours, GitHub Actions:
1. Downloads MODIS L1B (MOD021KM/MYD021KM) and VIIRS L1B (VNP02IMG) granules from NASA LANCE
2. Extracts the pixels covering each volcano (±30 km)
3. Calculates VRP using Stefan-Boltzmann: `VRP = A × σ × (T_pix⁴ − T_bg⁴)`
4. Saves results to `data/{volcano}.json`
5. GitHub Pages serves the frontend

## Setup

### 1. NASA Earthdata credentials
Register free at https://urs.earthdata.nasa.gov/users/new

Copy `.env.example` to `.env` and fill in your credentials.

### 2. Install dependencies
```bash
conda create -n vrp python=3.11
conda activate vrp
conda install -c conda-forge pyhdf
pip install -r requirements.txt
```

### 3. Run locally
```bash
# Process Cordón Caulle for a specific date
python scripts/run_pipeline.py --volcano PuyehueCordonCaulle --date 2024-03-14

# Process all volcanoes for yesterday
python scripts/run_pipeline.py
```

### 4. GitHub Actions (NRT)
Add your NASA Earthdata credentials as GitHub secrets:
- `EARTHDATA_USERNAME`
- `EARTHDATA_PASSWORD`

The pipeline runs automatically every 6 hours.

## Algorithm

Based on MIROVA (Coppola et al. 2015):
- **MODIS**: Bands 21 (3.929 μm) and 22 (3.959 μm), 1 km resolution
- **VIIRS I4** (3.74 μm, 375 m): MIR-based VRP for high-temperature features
- **VIIRS I5** (11.45 μm, 375 m): TIR-based VRP for low-temperature features (TIRVolcH, Aveni et al. 2024)

## References
- Coppola et al. 2015, Geological Society Special Publication 426
- Campus et al. 2022, Sensors 22(5):1713
- Aveni et al. 2024, Remote Sensing of Environment 315:114388
