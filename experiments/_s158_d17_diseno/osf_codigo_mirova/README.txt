# MIROVA Algorithm for hotspot detection and VRP calculation

This repository provides a compact MATLAB implementation of the core MIROVA workflow for resampled VIIRS M-band observations at 750 m resolution:

1. contextual detection of volcanic thermal anomalies using M13 and M15 radiances;
2. estimation of volcanic radiant power (VRP) from above-background M13 radiance.

The code intentionally excludes operational components that are not required by these two calculations, including file-system logic, volcano databases, cloud outputs, quality-flag outputs, geolocation diagnostics and near-real-time reporting.

## Repository contents

```text
MIROVA_VIIRS750_hotspot_detection.m   Core hotspot detection
MIROVA_VIIRS750_VRP.m                 M13 background and VRP calculation
example/VIIRS750_example.mat           Reduced example input
example/run_example.m                  Reproducible example
CITATION.cff                           Software citation metadata
LICENSE                                MIT license
```

## Requirements

- MATLAB R2024a or newer;
- Image Processing Toolbox (`colfilt`, `imdilate`, `strel`);
- `fillmissing2`, included in current MATLAB releases.

## Minimal workflow

```matlab
S = load('example/VIIRS750_example.mat');

cosSunglint = ...
    cosd(S.sat_zen).*cosd(S.sun_zen) - ...
    sind(S.sat_zen).*sind(S.sun_zen).*cosd(S.sun_azi-S.sat_azi);
cosSunglint = max(-1,min(1,cosSunglint));
sunglint = acosd(cosSunglint);

alert = MIROVA_VIIRS750_hotspot_detection( ...
    S.ZI_M13,S.ZI_M15,S.BOX,S.dayflag,sunglint);

[VRP_MW,npix,deltaL_MIR,ZI_M13bk] = ...
    MIROVA_VIIRS750_VRP(S.ZI_M13,alert);
```

## Inputs

### Hotspot detection

- `ZI_M13`: resampled VIIRS M13 spectral radiance, in W m^-2 sr^-1 um^-1;
- `ZI_M15`: resampled VIIRS M15 spectral radiance, in W m^-2 sr^-1 um^-1;
- `BOX`: same-sized region mask containing classes 0, 1 and 2;
- `dayflag`: 0 for nighttime, non-zero for daytime;
- `sunglint`: sun-glint angle in degrees.

The output `alert` contains MATLAB linear indices of detected anomalous pixels.

### VRP calculation

The VRP function requires only `ZI_M13` and `alert`. It removes the detected pixels, expands the excluded region according to anomaly size, reconstructs the two-dimensional M13 background with `fillmissing2`, and calculates:

```text
deltaL_MIR = sum(L_M13,alert) - sum(L_M13,background at alert)
VRP = deltaL_MIR x 1.97e7 x 0.5625
```

VRP is returned in MW.

## Interpretation of missing detections

`VRP_MW` is returned as `NaN` when `alert` is empty. This is deliberate.

A value of zero would imply a valid observation demonstrating no thermal excess. An empty detection does not establish this: the volcanic target may be obscured, the scene may be unsuitable, or the signal may fall below the algorithm's detection criteria. Therefore, an undetermined VRP must not be treated as zero emission.

## Algorithm notes

The detection combines:

- a fixed normalized thermal index (NTI) threshold;
- a local 3 x 3 spatial-context test;
- a spectral-context test based on the M13 radiance expected from the M15 brightness temperature;
- separate daytime and nighttime thresholds;
- two contextual iterations;
- rejection of scenes with sun-glint angle below 12 degrees.

The Planck conversion constants and effective wavelengths are retained from the operational implementation to preserve numerical consistency:

- M13: 4.05 um;
- M15: 10.763 um.

## Scientific references

Coppola, D., Laiolo, M., Cigolini, C., Delle Donne, D. & Ripepe, M. (2016). Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system. In A. J. L. Harris, T. De Groeve, F. Garel & S. A. Carn (Eds.), *Detecting, Modelling and Responding to Effusive Eruptions*, Geological Society, London, Special Publications, 426, 181-205. DOI: 10.1144/SP426.5.

Campus, A., Laiolo, M., Massimetti, F. et al. (2022). The transition from MODIS to VIIRS for global volcano thermal monitoring. *Sensors*, 22, 1713. DOI: 10.3390/s22051713.

## Scope

This repository reproduces the essential scientific calculations and is not the complete operational MIROVA near-real-time processing chain. Quality screening, cloud assessment, input preparation and interpretation of missing observations remain the responsibility of the user.

## License

Released under the MIT License. See `LICENSE`.
