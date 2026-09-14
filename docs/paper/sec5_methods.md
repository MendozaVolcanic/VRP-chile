# 5. Methods: the VRP Chile implementation

## 5.1 Data sources and products

VRP Chile ingests calibrated Level-1B radiances directly; it does not consume any
pre-computed thermal-anomaly product such as MOD14/MYD14. For MODIS the pipeline reads
`MOD021KM` (Terra) and `MYD021KM` (Aqua) with their `MOD03`/`MYD03` geolocation files, and
uses band 21 (3.929 µm) as the primary mid-infrared (MIR) channel, band 22 (3.959 µm) where
band 21 saturates, and band 31 (11 µm) as the thermal-infrared (TIR) channel. For VIIRS it
reads two resolution families: the 375 m I-band products (`VNP02IMG` for Suomi-NPP,
`VJ102IMG` for NOAA-20, `VJ202IMG` for NOAA-21), using I04 (3.74 µm) as MIR and I05
(11.45 µm) as TIR; and the 750 m M-band products (`VNP02MOD`, `VJ102MOD`, `VJ202MOD`),
using M13 (4.05 µm) and M15 (10.76 µm). Every product is paired with its own geolocation
granule.

<!-- src: pipeline/process_modis.py:22-33 ; pipeline/process_viirs.py:27-28,78 ; pipeline/process_viirs_mod.py:20-27 ; pipeline/fetch.py:187-223 -->

Granules are retrieved from NASA Earthdata through `earthaccess`. The search is
Standard-first: for each product the pipeline queries the archived collection and, if no
granule exists yet for the requested date, falls back to the corresponding LANCE
near-real-time collection, whose latency is about three hours. The two families are named
differently, which matters for anyone reimplementing the fetch layer: MODIS NRT keeps the
Standard short name and changes the version (`MOD021KM` v`6.1NRT`), whereas VIIRS NRT
appends a suffix to the short name (`VNP02IMG_NRT`). Each record carries a
`product_version` field of `standard` or `nrt`, and the store upgrades it in place when the
Standard granule becomes available.

<!-- src: pipeline/fetch.py:168-223 ; [5.1] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), col. izq. ; [5.1] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3), col. der. ("latency of less than 3 h") -->

Detection is restricted to night overpasses. The MIR channel is unusable by day because
solar reflection off cloud tops mimics a hot pixel: bright at 3.7 µm, cold at 11 µm, hence
a large but spurious thermal index. Running the detector only at night removes that
artefact class at its source instead of filtering it afterwards.

<!-- src: scripts/run_pipeline.py:116,192 ; docs/FICHA_SDA_VRP_CHILE.md (artefactos solares diurnos) ; [H2] reflexión solar sobre nubes que sube el NTI: Coppola et al. 2014, coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf, p. 3410 impresa (visor 10), §2.4.2 Daytime algorithm, 1.er párrafo -->

## 5.2 Processing chain and operational architecture

The system runs entirely on free public infrastructure. A GitHub Actions workflow fires on
a two-hour cron (`0 */2 * * *`), bounding the staleness of the published series at two
hours against the roughly three-hour LANCE publication lag. A matrix strategy gives each
volcano its own job with `max-parallel: 8`, so a single hanging download cannot block the
rest of the network; the job budget is 80 minutes and the processing step 50.

<!-- src: .github/workflows/nrt.yml:12,69,80-81,179 -->

Each job performs the same four steps: fetch the L1B and geolocation granules covering the
volcano, process them with `process_modis.py`, `process_viirs.py` (I-band) or
`process_viirs_mod.py` (M-band), append the resulting records to a per-volcano JSON file
under `data/<profile>/`, and commit them back to the repository. Raw L1B files are never
committed. The dashboard is a static GitHub Pages site (Chart.js, Leaflet) that reads those
JSON files directly, so the published product and the scientific record are the same
artefact.

All tunable behaviour lives in YAML profiles rather than in code. The operational profile
`mirova_equivalent` holds the literal-clone configuration; a parallel `experimental`
profile and a few laboratory profiles write to their own data subdirectory and are never
run by the cron, so an experiment cannot contaminate the operational series.

<!-- src: pipeline/profiles/mirova_equivalent.yaml ; .github/workflows/nrt.yml:24-31 -->

## 5.3 Detection: fidelity to Coppola et al. (2016a)

The detector is the one described in Coppola et al. (2016a, SP 426.5); the values below
were read from the effective operational configuration (`pipeline.profile` under
`VRP_PROFILE=mirova_equivalent`), not from documentation.

Detection is organised around two regions of interest: pixels within the volcano's
`inner_radius_km` form the summit ROI, pixels beyond it and out to the search radius the
scene ROI. The contextual index gate uses the paper's Table 1 thresholds differentiated by
ROI (at night C2 = 5 summit and 10 scene, 15 by day; C1 = 0.003 and 0.01, 0.02 by day).
That asymmetry keeps the detector sensitive to small summit anomalies while reducing false
alerts farther away (Coppola et al., 2023, p. 3). Our additional brightness-temperature gate
has no counterpart in Coppola et al. (2016a) and is listed as divergence D22.

<!-- src: pipeline/profile.py:104-105,204 ; pipeline/profiles/mirova_equivalent.yaml:119-120,129-130,251,278 ; [5.2] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), Tabla 1 (sólo K1, C1 y C2; ninguna compuerta de temperatura de brillo) ; [5.3] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), Tabla 1 ; [5.4] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3), col. der., 1.er párrafo ; docs/MIROVA_DIVERGENCES.md (D22) -->

The contextual first pass implements Tests 2 and 3 literally, as a conjunction that keeps
the statistical OR branch on each side: a pixel is active when
`dNTI > C1 or dNTI > μ+C2·σ` **and** `dETI > C1 or dETI > μ+C2·σ`. The normalised thermal
index NTI and its non-volcanic model NTI_bk are combined into the enhanced index ETI
through a quadratic best-fit regression fitted separately for each image, and both
differentials are taken against the arithmetic (not median) mean of the eight
neighbouring pixels, following the paper. The background statistics μ and σ are global per
image rather than drawn from a ring, and pixels declared unsuitable by the paper (matrix
edges, dNTI or dETI < −0.1, and pixels already flagged active by Tests 1 to 3) are excluded
from that pool; our implementation does not yet remove the Test 1 pixels. A second pass then
re-runs the spatial analysis with the pixels
already declared active removed, recovering the marginal pixels of a cluster whose
neighbourhood the cluster itself had contaminated.

<!-- src: pipeline/detection_context.py:423-470,669-760 ; pipeline/profile.py:653-660,722-723 ; effective: ENABLE_FIRST_PASS_TESTS_2_AND_3=True, ENABLE_DUAL_ROI_FIRST_PASS=True, ENABLE_SECOND_PASS_ADJACENT=True, ENABLE_DUAL_ROI_SECOND_PASS=True ; effective: ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False (pipeline/profile.py:513, GAP #A) ; [5.5] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), col. izq., Tests 2 y 3 ; [5.6] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. izq. ; [5.7] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. der., §Spatial analysis, 1.er párrafo ; [5.8] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), viñetas ; [5.8] Coppola et al. 2016a, sp426.5.pdf, p. 186 impresa (visor 6), Test 1 ; [5.8] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), col. der., 2.º párrafo ; [5.9] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), col. izq., 1.er párrafo -->

In Coppola et al. (2016a) Test 1 is a per-pixel threshold, NTI_PIX > K1. Our implementation
adds a path, not described in the MIROVA papers, that integrates MIR radiance over a fixed
3 km ROI around the vent to catch sub-pixel sources.

<!-- src: pipeline/test1_integrated.py (compute_test1_mir) ; effective: ENABLE_TEST1_PATH=True, TEST1_ROI_KM=3.0 ; [5.10] Coppola et al. 2016a, sp426.5.pdf, p. 186 impresa (visor 6), §Fixed NTI threshold -->

## 5.4 Radiative power

Radiative power in the MIR follows Wooster's mid-infrared method, VRP = k · A_pix ·
(L_MIR − L_bg), with a sensor-specific coefficient. The coefficients were not adopted from
the literature on authority: they were reconstructed by inverting the published MIROVA OSF
v2.5 dataset (48,360 Chilean rows), solving for k row by row from VRP and the tabulated
radiance excess. The reconstruction returns 18,900,000 for MODIS at 1 km
(k = 18.9 with A_pix = 10⁶ m²), 11,081,250 for VIIRS M-band at 750 m (k = 19.7), and
2,531,250 for VIIRS I-band at 375 m (k = 18.0 with A_pix = 140,625 m²), with residual
errors of 2×10⁻¹⁴ %, 0.17 % and 2×10⁻¹⁴ % against the closest published formula. It also
discriminates between competing published values: the k = 2.48×10⁷ proposed for VIIRS
375 m by Di Bella et al. (2024) does not reproduce the OSF rows and was discarded.

<!-- src: experiments/21_results.json (n_rows_total 48360; median_coef and matched_error_pct per sensor) ; pipeline/process_modis.py:82 ; pipeline/process_viirs.py:75 ; pipeline/process_viirs_mod.py:64 ; [5.11] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), Eq. 7 ; [5.11] Campus et al. 2024, s00445-024-01721-z.pdf, p. 4 impresa (visor 4), Eq. 3 ; [5.11] Wooster et al. 2003, 1-s2.0-S0034425703000701-main.pdf, p. 87 impresa (visor 5), Fig. 3 ; [5.12] MODIS: Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), Eq. 7 ; [5.12] MODIS: Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3), Eq. 2 ; [5.12] banda M: Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 7 impresa (visor 7), Eq. 1 ; [5.12] banda I: Campus et al. 2024, s00445-024-01721-z.pdf, p. 4 impresa (visor 4) ; [5.13] Di Bella et al. 2024, Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf, p. 7 impresa (visor 7), §3.7, Eq. 5 -->

MIROVA resamples each scene onto a grid of constant 1 km² pixels (Coppola et al., 2023,
p. 3); VRP Chile does not resample but uses the corresponding uniform nadir pixel area, which
the inversion supports: the reconstructed coefficient is invariant across sensor-zenith bins
(`a_pix_mode: nadir_fijo`). VRP Chile therefore disables the sec³(θ) off-nadir area
correction in the operational profile. This is a fidelity requirement, not a
simplification: because area multiplies the integrated radiance, the geometric area would
both inflate magnitudes and change which weak sources cross the detection threshold.

<!-- src: experiments/21_results.json (a_pix_mode) ; pipeline/scan_geometry.py:4-16,132-155 ; effective: ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS=True, ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS=True ; [5.14] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3), §2.1 final y col. der. ; [5.14] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3) -->

A TIR estimator applies pure Stefan-Boltzmann radiation per alerted pixel, as in Aveni et al.
(2024, p. 11, Eq. 5), with σ = 5.670374419×10⁻⁸ W m⁻² K⁻⁴ (CODATA 2018). The
alternative parameterisation of Aveni et al. (2025) with k_TIR = 60.17 is coded but not
enabled operationally.

<!-- src: pipeline/constants.py:11-14 ; effective: ENABLE_VRPTIR_AVENI=False, ENABLE_VRP_TIR_OUTPUT=False ; [5.15] Aveni et al. 2024, Aveni_2024_TIRVolcH_RSE.pdf, p. 11 impresa (visor 11), §4.4, Eq. 5 ; [5.15] Coppola 2025, 978-3-031-86841-2.pdf, p. 337 impresa (visor 341), col. izq., Eq. 16 (modelo de dos componentes; ya no se cita en la frase) ; [5.16] Aveni et al. 2025, Geophysical Research Letters - 2025 - Aveni - Volcanic Radiative Power Retrieval ....pdf, p. 5 impresa (visor 5), leyenda de la Fig. 2 -->

## 5.5 Geometry and the summit/far classification

Each target is defined by a search radius and an inner radius. The eleven Tier A volcanoes
use `radius_km = 25`, close to the inscribed radius (25-25.5 km) of MIROVA's 50-51 km UTM
grid; the other 34
configured volcanoes use 5 km. The inner radius is per-volcano, taken from MIROVA's own
published KML footprints: 3 km (Lastarria, Planchón-Peteroa), 4 km (Copahue), 5 km
(Láscar, Isluga, Nevados de Chillán, Llaima, Villarrica, Chaitén), 7 km (Tupungatito) and
20 km (Puyehue-Cordón Caulle).

<!-- src: volcanoes.yaml (45 entries; radius_km 25 on 11, 5 on 34; inner_radius_km per volcano, annotated "MIROVA KML oficial") ; [5.17] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 7 impresa (visor 7) (51 × 51) ; [5.17] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3) (51 × 51) ; [5.17] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3) (50 × 50) ; [5.17] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3) (50 × 50) ; [5.18] huellas KML de MIROVA: SIN LOCALIZAR (producto web, no hay PDF) -->

Detections are not filtered by that inner radius; they are labelled by it. A detection
whose resolved hotspot lies inside it is tagged `summit`, one outside `far`. This "detect
wide, classify visually" scheme keeps the detector uniform while letting the dashboard
separate a crater anomaly from a distant thermal feature, and it preserves in the record
detections that MIROVA does not publish but that are physically real: secondary craters,
chronic fumarolic fields, diffuse laccolith anomalies.

<!-- src: pipeline/process_viirs.py:693-697 (calculate_vrp docstring) -->

## 5.6 Reproducibility and governance

Three mechanisms keep the implementation honest. First, every methodological choice is a
named flag in a versioned YAML profile, and the profile module is the single point at which
flags become effective values, so any claim about system behaviour can be checked by
importing `pipeline.profile` rather than by reading prose. Second, the test suite
([NUM: n_tests_collected] tests) includes golden-file regression tests and executable guards
asserting that what the transparency record declares matches what the code does. Third,
`docs/MISSION.md` defines a binding three-question gate applied before any change to the
algorithmic pipeline: is the mechanism documented in one of the eleven core MIROVA papers,
with a verbatim citation showing that the operational NRT system applies it; if not, does
it close a catalogued divergence; if neither, it is not implemented. The gate exists
because the project's own history showed that individually reasonable patches accumulate
into a system that is no longer a clone.

<!-- src: docs/MISSION.md:41-120 ; tests/test_guard_declarado_vs_efectivo_s131.py -->

Because SERNAGEOMIN is a public body and the system informs volcanic alert assessment,
VRP Chile is treated as an Automated Decision System under Chilean transparency guidance
(CPLT Resolución Exenta N°372). A published record states the objective, the decision
logic, the input data categories, the effect of the main variables and the characterised
physical limits; sixteen pipeline modules carry a machine-readable header pointing back to
it. The system profiles no individuals and uses no machine learning: it is a deterministic
rule set, auditable end to end.

<!-- src: docs/FICHA_SDA_VRP_CHILE.md (v1.5, 2026-09-02) ; [5.19] CPLT Resolución Exenta N°372: SIN LOCALIZAR (el texto legal no está en documentacion\) -->

## 5.7 Known deviations from the literal clone

*(This subsection may be moved to the Discussion.)*

The divergence catalogue is maintained as a living document, and several entries remain
open. Ground-truth coverage is incomplete, and MIROVA's explicit false-positive labelling
has no counterpart in our records (D2, D3). The dashboard's `summit` fence suppresses part
of the detected magnitude from the published view, which is a reporting divergence rather
than a detector one (D13). Our per-image grid is not centred on the point MIROVA uses
(D17), and MIROVA's first ROI is a fixed 5 km box common to all targets whereas ours is a
per-volcano circle of 3 to 20 km; an A/B reprocessing of the box variant did not improve
parity, so the divergence is documented rather than removed (D18). One entry is active and
unresolved: a peak-preservation rule inside the Test 1 contextual filter can publish a
single pixel from the edge of the 3 km disc (colder than its own background) as a summit
detection at nominal zero distance (D19). Two departures from strict uniformity are
declared rather than hidden: the global-background variant of Test 1 is enabled per volcano
for three targets, and the ETI-normalised variant of the Test 1 integral is implemented but
disabled, so the topographic bias of the MIR-absolute paths on snow-capped summits remains
a characterised limit rather than a corrected one. Finally, the MODIS NTI is computed with band 31 (11.03 µm) as the
TIR channel whereas Coppola et al. (2016a) use band 32 (12.02 µm); a Planck-function estimate
puts the resulting NTI offset between 0.0001 and 0.0054 for scene temperatures of 250 to 290 K,
against a margin of about 0.14 to the K1 threshold, and the offset cancels in the contextual
differences, so it is declared rather than corrected (D20).

<!-- src: docs/MIROVA_DIVERGENCES.md (headers D2, D3, D13, D17, D18, D19, D20) ; docs/AUDIT_S128.md:654-660 ; volcanoes.yaml lbg_global_compatible ; effective: ENABLE_TEST1_LBG_GLOBAL=True, ENABLE_TEST1_NTI_INTEGRAL=False ; [5.20] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3) ; [5.20] Coppola et al. 2016a, sp426.5.pdf, p. 189 impresa (visor 9), col. izq., 3.er párrafo ; [5.21] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), lista (vii) ; [5.21] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3) -->

---

## Localizadores: archivos PDF y convención de página

Todos los archivos están en `documentacion\`. "p. impresa" es el folio del artículo y "visor" la
página del PDF. Los localizadores de cada comentario `src` fueron verificados mirando la página
renderizada (`docs/audit_s141/lectura/VERIFICADOR_MANUSCRITO.md`); el número entre corchetes es la
fila de ese informe. Las fuentes de código y datos del repo quedan como estaban. Las columnas
"paper" y "convención de página" de Coppola et al. 2023, Di Bella et al. 2024, Aveni et al. 2024
y Aveni et al. 2025 vienen del localizador: **metadatos y convención sin segunda verificación**
(los localizadores de página de esas filas sí están verificados).

| ref | paper (autor, año, revista) | archivo PDF | convención de página |
|---|---|---|---|
| Coppola et al., 2016a | Coppola et al. 2016a, *Geol. Soc. London Spec. Publ.* 426 | `sp426.5.pdf` | p. impresa = visor + 180. **Deducida, no leída**: el PDF no imprime folios; el rango 181-205 sale de la lista de referencias de Campus et al. 2024 (p. 6) |
| Coppola, 2025 | Coppola 2025, capítulo 11 de *Modern Volcano Monitoring* (Springer) | `978-3-031-86841-2.pdf` (libro completo) | p. impresa = visor − 4 (p. 337 = visor 341). **`978-3-031-86841-2_9.pdf` NO es este capítulo** (es el de R. Campion sobre gases) |
| Coppola et al., 2014 | Coppola et al. 2014, *Int. J. Remote Sens.* 35(9) | `coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf` | p. impresa = visor + 3400 (visor 10 = p. 3410) |
| Coppola et al., 2020 | Coppola et al. 2020, *Front. Earth Sci.* 7:362 | `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` | p. impresa = visor |
| Coppola et al., 2023 | Coppola et al. 2023, *Front. Earth Sci.* (MIROVA database v1) | `feart-11-1240107.pdf` | p. impresa = visor |
| Campus et al., 2022 | Campus et al. 2022, *Sensors* 22:1713 | `campus2022_sensors_22_1713.pdf` | p. impresa = visor |
| Campus et al., 2024 | Campus et al. 2024, *Bull. Volcanol.* 86:25 | `s00445-024-01721-z.pdf` | p. impresa = visor |
| Wooster et al., 2003 | Wooster et al. 2003, *Remote Sens. Environ.* 86 | `1-s2.0-S0034425703000701-main.pdf` | p. impresa = visor + 82 (visor 5 = p. 87) |
| Di Bella et al., 2024 | Di Bella et al. 2024, *Remote Sens.* 16:2879 (INGV Catania, no es del grupo MIROVA) | `Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf` | p. impresa = visor |
| Aveni et al., 2024 | Aveni et al. 2024, *Remote Sens. Environ.* 315, 114388 (TIRVolcH) | `Aveni_2024_TIRVolcH_RSE.pdf` | p. impresa = visor |
| Aveni et al., 2025 | Aveni et al. 2025, *Geophys. Res. Lett.* | `Geophysical Research Letters - 2025 - Aveni - Volcanic Radiative Power Retrieval ....pdf` | p. impresa = visor |

---

## Notas para el editor

**Placeholders dejados (1):** `[NUM: n_tests_passed]` en §5.6. El esqueleto S72 decía «796
passed (S119)» y el prompt mencionaba 1211; no corrí la suite, así que el número lo debe
poner `scripts/paper_numbers.py`. No dejé placeholders de records ni de fechas de cobertura
porque esta sección no los necesita: van en §6 (Validation) y en la Tabla 2.

**Contradicciones entre el esqueleto S72 y el código de hoy:**

1. **«`radius_km = 25 km` uniforme» es falso.** `volcanoes.yaml` tiene 45 volcanes: 11 con
   `radius_km: 25` (los Tier A) y 34 con `radius_km: 5`. Corregido en §5.5.
2. **La corrección sec³(θ) por ángulo de escaneo ya no se aplica.** El esqueleto la daba
   por activa; hoy `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS` y `..._VIIRS` están en `True`, es
   decir área nadir fija en los tres sensores. Lo redacté como requisito de fidelidad y no
   como simplificación, porque el propio `experiments/21_results.json` reporta
   `a_pix_mode: nadir_fijo` para los tres sensores.
3. **El conteo de tests del esqueleto está obsoleto**, y por eso quedó como placeholder.

**Trampa de nombres que casi me hace afirmar algo falso** (conviene que quede registrada):
`ENABLE_ETI_QUADRATIC_SCENE` está en `False` en el perfil operacional, lo que a primera
vista contradice la afirmación de `CLAUDE.md` de que el ETI se calcula por regresión
cuadrática. No es contradicción: ese flag gatea un camino heredado de S37, y la regresión
cuadrática sí corre, dentro de `first_pass_tests_2_and_3`, que está en `True`
(`ENABLE_FIRST_PASS_TESTS_2_AND_3`, `ENABLE_DUAL_ROI_FIRST_PASS`). Es exactamente el patrón
A89. Verifiqué la ruta de llamada en `pipeline/detection_context.py:464` antes de escribir
el párrafo de §5.3.

**Lo que NO pude verificar y conviene revisar antes de enviar:**

- El texto dice que el dashboard usa Chart.js y Leaflet y que lee los JSON directamente: lo
  tomé de `CLAUDE.md` §Arquitectura, no abrí `frontend/index.html`.
- «Sixteen pipeline modules carry a FICHA header» viene del historial v1.5 de la ficha SDA,
  no de un conteo propio sobre `pipeline/`.
- El párrafo de §5.7 sobre D13 evita el «31 %» que aparece en el encabezado de la
  divergencia, porque ese porcentaje es de S124 y es un conteo sobre un corpus que creció
  desde entonces (regla A90). Si Nicolás quiere el número, hay que remedirlo.
- No incluí D12 (congelada) ni D15 (hallazgo, no divergencia accionable). Los dejé fuera a
  propósito para no dar por abierto algo que está congelado; si el editor prefiere
  listarlos, es una decisión de alcance, no de exactitud.
- El *timeout* de 80 minutos es del job y el de 50 minutos es del paso de procesamiento;
  `CLAUDE.md` menciona sólo el de 50 y dice «per-step», lo que es correcto pero incompleto.
- Las bandas MODIS y VIIRS, y la afirmación «no consume MOD14/MYD14», salen de los
  docstrings y de la ficha SDA v1.5; no rastreé la lectura de bandas dentro del cuerpo de
  `calculate_vrp`.

**Localizadores de literatura (S141):**

- **Fila 5.18 (SIN LOCALIZAR): localizador pendiente de verificar en imagen.** Que los radios
  internos vengan de las huellas KML publicadas por MIROVA no tiene fuente en `documentacion\`:
  es un producto web. Si se mantiene, citar el KML con fecha de descarga.
- **Fila 5.19 (SIN LOCALIZAR): localizador pendiente de verificar en imagen.** El texto legal de
  la «CPLT Resolución Exenta N°372» no está en `documentacion\`; conviene verificar también el
  nombre exacto (el `CLAUDE.md` del proyecto la llama «Resolución CPLT N°372», sin «Exenta»).
- **§5.3 ahora nombra dos caminos propios que §5.7 no declara explícitamente.** La compuerta de
  temperatura de brillo (D22) y el Test 1 integrado en 3 km (que el paper no describe: su Test 1
  es un umbral por píxel, p. 186). Tampoco figura en §5.7 que el código no retire los píxeles del
  Test 1 (GAP #A, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False`). Los textos de reemplazo del
  verificador remitían a «Section 5.7»; esa remisión se quitó para no apuntar a algo que §5.7 no
  dice. Agregar las tres a §5.7 y restituir la remisión.
- **La cita a «Coppola (2024, Eq. 16)» se quitó del estimador TIR.** La Eq. 16 del capítulo
  (Coppola 2025, p. 337) es un modelo de dos componentes, no un estimador por píxel sobre
  temperatura de brillo, y ninguna de las dos fuentes usa el σ de CODATA 2018 (Aveni 2024 escribe
  5.67 × 10⁻⁸). La frase queda anclada sólo a Aveni et al. (2024, p. 11, Eq. 5).
- **Hallazgo H2 del verificador sobre §5.1.** Coppola et al. 2014, p. 3410, describe la reflexión
  solar sobre nubes que sube el NTI, lo que respalda el mecanismo. Pero la frase «The MIR channel
  is unusable by day» va más allá de la literatura: MIROVA procesa también el día, con umbrales
  propios (Tabla 1 de Coppola et al. 2016a, columnas diurnas, p. 187). La restricción nocturna es
  decisión nuestra y conviene redactarla así.
- **Faltan filas de referencias para §5.** Di Bella et al. 2024, Aveni et al. 2024, Aveni et al.
  2025, Coppola et al. 2020 y 2023 se citan en §5 y no hay tabla de referencias en esta sección.
  Hallazgo H4 del verificador: Di Bella 2024 (p. 7, Eq. 5) también da k_MODIS = 1.89 × 10⁷ y
  k_VIIRS750 = 1.11 × 10⁷, que coinciden con los del repo; sólo el valor de 375 m difiere.
