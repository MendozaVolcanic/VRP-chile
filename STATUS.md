# STATUS — VRP Chile
**Last updated:** 2026-04-05

---

## Current state

**Pipeline NRT operational** on GitHub Actions (every 6h).
- Repository: https://github.com/MendozaVolcanic/VRP-chile
- Dashboard: https://mendozavolcanic.github.io/VRP-chile/
- VRP formula: Wooster MIR radiance method (Coppola 2015, Eq. 7)
- Nighttime-only filtering active (triple barrier: fetch, process, store)
- NTI dual-criteria detection for VIIRS 375 m
- Local ROI p95 filter for all sensors (anti-topographic false positives)
- Multi-pixel anomaly tracking across all 3 processors
- NOAA-20 multi-version search (2.1/2/1) for VJ1 products

---

## Volcanoes and data

| Volcano | Records | Date range | Detections (VRP > 0) | MIROVA ref |
|---------|---------|------------|---------------------|------------|
| Puyehue-Cordon Caulle | 74 | 2024-03 to 2026-04 | 12 | 94 records |
| Villarrica | calibrating | Jan-Mar 2026 | pending | -- |
| Lascar | calibrating | Jan-Mar 2026 | pending | 203 records |
| Copahue | calibrating | Jan-Mar 2026 | pending | -- |

Recalibration (Jan-Mar 2026) running with corrected code for Villarrica, Lascar, and Copahue.

---

## Architecture

```
scripts/run_pipeline.py       Entry point CLI (nighttime filter, multi-sensor)
pipeline/fetch.py             Download granules NASA Earthdata (earthaccess)
pipeline/process_modis.py     MODIS Terra/Aqua Band 21/22 (1 km, 3.93 um)
pipeline/process_viirs.py     VIIRS I-band I04/I05 (375 m, NTI dual-criteria)
pipeline/process_viirs_mod.py VIIRS M-band M13 (750 m, 4.05 um)
pipeline/store.py             JSON persistence + nighttime solar gate
frontend/index.html           Dashboard (Chart.js + Leaflet.js)
.github/workflows/nrt.yml     GitHub Actions NRT (cron 6h + manual trigger)
volcanoes.yaml                Volcano config (4 active)
data/mirova/                  MIROVA reference data (JSON)
```

---

## VRP formula (corrected 2026-04-04)

### MIR channel — Wooster method (Coppola 2015, Eq. 7)
```
VRP = 18.9 * A_pix * (L_hot - L_bg)
L = C1 / (lambda^5 * (exp(C2 / (lambda * T)) - 1))
```
- Applies to: MODIS bands 21/22, VIIRS I04, VIIRS M13
- L_bg derived from Planck(T_bg) where T_bg = median BT of background annulus
- **Critical fix**: previous code used median(radiance) for L_bg, which differs from Planck(median(BT)) due to nonlinearity with heterogeneous terrain

### TIR channel — Stefan-Boltzmann (Aveni 2024)
```
VRP_TIR = A_pix * sigma * (T_alert^4 - T_bg^4)
```
- Applies to: VIIRS I05 (11.45 um) only

---

## Anomaly detection criteria

A pixel is flagged as anomalous only if it passes ALL of:

1. **BT threshold**: `BT > T_bg + max(5 K, 3 * sigma_bg)` — standard MIROVA threshold
2. **Local ROI p95**: `BT > p95_ROI + max(3 K, 2 * sigma_ROI)` — prevents topographic FP at high-altitude volcanoes
3. **NTI filter** (VIIRS 375 m only): `NTI > NTI_bg + max(0.005, 3 * sigma_NTI)` — cancels terrain effects

---

## Dashboard features (all implemented)

| Feature | Status | Details |
|---------|--------|---------|
| VRP time series | Done | Chart.js, log scale, sensor colors |
| Hotspot map | Done | Leaflet.js, multi-pixel markers, per-pixel popups |
| Distance vs Time | Done | Tracks anomaly distance from crater |
| VRE cumulative | Done | Volcanic Radiated Energy integral (GJ) |
| MIROVA comparison | Done | Overlay our VRP vs MIROVA reference |
| CSV export | Done | Download filtered data (full + anomalies only) |
| Global summary | Done | Cross-volcano stats panel |
| Nighttime filter | Done | Triple barrier (fetch/process/store) |

---

## Sensors processed

| Sensor | Product | Band | Resolution | Pixel area |
|--------|---------|------|------------|------------|
| MODIS Terra | MOD021KM | 21/22 (3.93 um) | 1 km | 1,000,000 m^2 |
| MODIS Aqua | MYD021KM | 21/22 (3.93 um) | 1 km | 1,000,000 m^2 |
| VIIRS SNPP 375 m | VNP02IMG | I04 (3.74 um) | 375 m | 140,625 m^2 |
| VIIRS NOAA-20 375 m | VJ102IMG | I04 (3.74 um) | 375 m | 140,625 m^2 |
| VIIRS SNPP 750 m | VNP02MOD | M13 (4.05 um) | 750 m | 562,500 m^2 |
| VIIRS NOAA-20 750 m | VJ102MOD | M13 (4.05 um) | 750 m | 562,500 m^2 |

---

## Bug fixes and calibration history

### 2026-04-05 — Topographic false positive fix (Lascar)
- **Problem**: Lascar at 5592 m surrounded by warmer lower terrain. Background annulus 5-25 km included warm low-altitude terrain, producing artificially low T_bg and 59 false positive pixels (587 MW vs MIROVA 0.03-4.61 MW)
- **Fix**: Added NTI dual-criteria for VIIRS 375 m + local ROI p95 filter for all sensors
- **Result**: Eliminates terrain-induced false positives without masking real volcanic signals

### 2026-04-04 — MODIS radiance nonlinearity bug (CRITICAL)
- **Problem**: `L_bg = median(radiance)` differs from `Planck(median(BT))` because Planck is nonlinear. With heterogeneous terrain (mountains + valleys), this produced inconsistent L_bg values, inflating VRP by ~15x
- **Fix**: Changed to `L_bg = Planck(T_bg)` and convert all hot pixel BTs to radiance consistently
- **Before/After**: Cordon Caulle 2026-03-10 went from 1438 MW to 101 MW; VIIRS VRP_VENT from 6.3 MW to 0.06-0.31 MW (matches MIROVA range)

### 2026-04-04 — Daytime false positives
- **Problem**: 78 daytime records with VRP up to 4307 MW due to reflected solar radiation in MIR band
- **Fix**: Triple nighttime barrier (solar elevation > 0 degrees = reject)
- **Result**: All daytime records cleaned from data files

### 2026-04-04 — Wooster formula migration
- **Problem**: Original pipeline used Stefan-Boltzmann `VRP = A * sigma * (T^4 - T_bg^4)` for MIR bands, producing ~15x higher values than MIROVA
- **Fix**: Migrated all MIR VRP to Wooster method `VRP = 18.9 * A * delta_L` (Coppola 2015, Eq. 7)
- **Result**: VRP values aligned with MIROVA reference data

---

## Current work (in progress)

- Recalibrating Villarrica, Lascar, Copahue (Jan-Mar 2026) with all bug fixes applied
- After recalibration: validate VRP values against MIROVA reference data

---

## Pending (next steps)

### High priority
1. Review recalibration results vs MIROVA reference data
2. Push calibrated data to GitHub
3. Validate NTI detection statistics

### Medium priority
4. Cloud masking (NTI helps partially; proper cloud mask would improve reliability)
5. NTI for MODIS (needs Band 31 TIR at 11 um — not yet implemented)
6. Refine vent coordinates for Cordon Caulle (current offset ~8 km from caldera center)

### Low priority
7. Expand to more Chilean/global volcanoes
8. Historical data backfill (MODIS from 2000, VIIRS from 2012)
9. NRT email/push alerts for significant detections

---

## MIROVA energy scale

| VRP range | Classification |
|-----------|---------------|
| < 1 MW | Very Low |
| 1 - 10 MW | Low |
| 10 - 100 MW | Moderate |
| 100 - 1000 MW | High |
| > 1000 MW | Very High |

---

## References

- **Coppola 2015** — MIROVA core: Wooster method, NTI/ETI, coefficient 18.9
- **Campus 2022** — MODIS to VIIRS cross-calibration, Sensors 22(5):1713
- **Aveni 2024** — TIRVolcH: TIR detection with Stefan-Boltzmann for I05, RSE 315:114388
- **Coppola 2023** — MIROVA database, c_rad coefficients for global volcanoes
