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

<!-- src: pipeline/fetch.py:168-223 -->

Detection is restricted to night overpasses. The MIR channel is unusable by day because
solar reflection off cloud tops mimics a hot pixel — bright at 3.7 µm, cold at 11 µm, hence
a large but spurious thermal index. Running the detector only at night removes that
artefact class at its source instead of filtering it afterwards.

<!-- src: scripts/run_pipeline.py:116,192 ; docs/FICHA_SDA_VRP_CHILE.md (artefactos solares diurnos) -->

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
scene ROI. Both the brightness-temperature gate and the contextual index gate use the
paper's Table 1 thresholds differentiated by ROI — at night, N·σ = 5 summit and 10 scene
(15 by day), contextual floor C1 = 0.003 summit and 0.010 scene (0.02 by day). That
asymmetry is how MIROVA stays sensitive to a weak crater source while remaining strict
about lakes, salt flats and fires elsewhere in the scene.

<!-- src: pipeline/profile.py:104-105,204 ; pipeline/profiles/mirova_equivalent.yaml:119-120,129-130,251,278 -->

The contextual first pass implements Tests 2 and 3 literally, as a conjunction that keeps
the statistical OR branch on each side: a pixel is active when
`dNTI > C1 or dNTI > μ+C2·σ` **and** `dETI > C1 or dETI > μ+C2·σ`. The normalised thermal
index NTI and its non-volcanic model NTI_bk are combined into the enhanced index ETI
through a second-order least-squares regression fitted over the whole scene, and both
differentials are taken against the arithmetic — not median — mean of the eight
neighbouring pixels, following the paper. The background statistics μ and σ are global per
image rather than drawn from a ring, and pixels below the paper's unsuitability floors are
excluded from that pool. A second pass then re-runs the spatial analysis with the pixels
already declared active removed, recovering the marginal pixels of a cluster whose
neighbourhood the cluster itself had contaminated.

<!-- src: pipeline/detection_context.py:423-470,669-760 ; pipeline/profile.py:653-660,722-723 ; effective: ENABLE_FIRST_PASS_TESTS_2_AND_3=True, ENABLE_DUAL_ROI_FIRST_PASS=True, ENABLE_SECOND_PASS_ADJACENT=True, ENABLE_DUAL_ROI_SECOND_PASS=True -->

Alongside the contextual path, Test 1 integrates MIR radiance over a fixed 3 km ROI around
the vent. This is what allows a sub-pixel source too weak to trigger any single-pixel test
to be detected as an excess of integrated energy.

<!-- src: pipeline/test1_integrated.py (compute_test1_mir) ; effective: ENABLE_TEST1_PATH=True, TEST1_ROI_KM=3.0 -->

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

<!-- src: experiments/21_results.json (n_rows_total 48360; median_coef and matched_error_pct per sensor) ; pipeline/process_modis.py:82 ; pipeline/process_viirs.py:75 ; pipeline/process_viirs_mod.py:64 -->

The same inversion also shows that MIROVA uses a **fixed nadir pixel area** for all three
sensors: the reconstructed coefficient is invariant across sensor-zenith bins
(`a_pix_mode: nadir_fijo`). VRP Chile therefore disables the sec³(θ) off-nadir area
correction in the operational profile. This is a fidelity requirement, not a
simplification: because area multiplies the integrated radiance, the geometric area would
both inflate magnitudes and change which weak sources cross the detection threshold.

<!-- src: experiments/21_results.json (a_pix_mode) ; pipeline/scan_geometry.py:4-16,132-155 ; effective: ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS=True, ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS=True -->

A TIR estimator follows pure Stefan–Boltzmann radiation with σ = 5.670374419×10⁻⁸
W m⁻² K⁻⁴ (CODATA 2018), as in Coppola (2024, Eq. 16) and Aveni et al. (2024, Eq. 5). The
alternative parameterisation of Aveni et al. (2025) with k_TIR = 60.17 is coded but not
enabled operationally.

<!-- src: pipeline/constants.py:11-14 ; effective: ENABLE_VRPTIR_AVENI=False, ENABLE_VRP_TIR_OUTPUT=False -->

## 5.5 Geometry and the summit/far classification

Each target is defined by a search radius and an inner radius. The eleven Tier A volcanoes
use `radius_km = 25`, the inscribed radius of MIROVA's 51×51 km UTM grid; the other 34
configured volcanoes use 5 km. The inner radius is per-volcano, taken from MIROVA's own
published KML footprints: 3 km (Lastarria, Planchón-Peteroa), 4 km (Copahue), 5 km
(Láscar, Isluga, Nevados de Chillán, Llaima, Villarrica, Chaitén), 7 km (Tupungatito) and
20 km (Puyehue-Cordón Caulle).

<!-- src: volcanoes.yaml (45 entries; radius_km 25 on 11, 5 on 34; inner_radius_km per volcano, annotated "MIROVA KML oficial") -->

Detections are not filtered by that inner radius; they are labelled by it. A detection
whose resolved hotspot lies inside it is tagged `summit`, one outside `far`. This "detect
wide, classify visually" scheme keeps the detector uniform while letting the dashboard
separate a crater anomaly from a distant thermal feature, and it preserves in the record
detections that MIROVA does not publish but that are physically real — secondary craters,
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

<!-- src: docs/FICHA_SDA_VRP_CHILE.md (v1.5, 2026-09-02) -->

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
single pixel from the edge of the 3 km disc — colder than its own background — as a summit
detection at nominal zero distance (D19). Two departures from strict uniformity are
declared rather than hidden: the global-background variant of Test 1 is enabled per volcano
for three targets, and the ETI-normalised variant of the Test 1 integral is implemented but
disabled, so the topographic bias of the MIR-absolute paths on snow-capped summits remains
a characterised limit rather than a corrected one. Finally, the MODIS NTI is computed with band 31 (11.03 µm) as the
TIR channel whereas Coppola et al. (2016a) use band 32 (12.02 µm); a Planck-function estimate
puts the resulting NTI offset between 0.0001 and 0.0054 for scene temperatures of 250–290 K,
against a margin of about 0.14 to the K1 threshold, and the offset cancels in the contextual
differences, so it is declared rather than corrected (D20).

<!-- src: docs/MIROVA_DIVERGENCES.md (headers D2, D3, D13, D17, D18, D19, D20) ; docs/AUDIT_S128.md:654-660 ; volcanoes.yaml lbg_global_compatible ; effective: ENABLE_TEST1_LBG_GLOBAL=True, ENABLE_TEST1_NTI_INTEGRAL=False -->

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
