# 4. Background: the MIROVA algorithm

MIROVA (Middle InfraRed Observation of Volcanic Activity) is the hotspot detection and
radiative power retrieval scheme introduced by Coppola et al. (2016a) for MODIS Level 1B
data and later extended by the same group to the two VIIRS resolutions (Campus et al., 2022,
2024). This section states what the algorithm does, in the terms and parameter values
published by its authors and citing primarily sources authored by the MIROVA group, because
the fidelity of our implementation (Section 5) is measured against these definitions.

<!-- src: [4.1] Coppola et al. 2016a, sp426.5.pdf, p. 181 impresa (visor 1), Abstract ; [4.2] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 7 impresa (visor 7), §3.2, 1.er párrafo ; [4.2] Campus et al. 2024, s00445-024-01721-z.pdf, p. 3 impresa (visor 3), §Methodology, 1.er párrafo (empieza al pie de la col. izq. y sigue en la der.) ; [4.3] afirmación sobre la propia sección: cita también a Wooster et al. 2003 y Wright et al. 2002, que no son del grupo -->

## 4.1 MIR radiative power and the Wooster approximation

Between roughly 600 and 1500 K, the range of most active lava surfaces, the
pixel-integrated middle infrared (MIR, near 4 μm) radiance is very nearly proportional to the
fourth power of the emitter temperature, so a single MIR band recovers the radiated power
without solving separately for the sub-pixel hot fraction and its temperature (Coppola, 2025,
Eq. 17, after Wooster et al., 2003). The resulting Volcanic Radiative Power (VRP) is
instrument-independent: any sensor with a MIR channel can yield it, by adapting the pixel
area and the wavelength-dependent proportionality constant.

<!-- src: [4.4] Coppola 2025, 978-3-031-86841-2.pdf, p. 337 impresa (visor 341), col. der., 2.º párrafo, Eq. 17 ; [4.4] Wooster et al. 2003, 1-s2.0-S0034425703000701-main.pdf, p. 87 impresa (visor 5), Fig. 3 ; [4.5] Coppola et al. 2016a, sp426.5.pdf, p. 197 impresa (visor 17), col. der., §Radiative power uncertainty ; [4.6] Coppola 2025, 978-3-031-86841-2.pdf, p. 337 impresa (visor 341), col. der., 3.er párrafo -->

For each alerted pixel the "above background" 4 μm radiance is the difference between the
radiance of that pixel and a background radiance estimated as the arithmetic mean of the
pixels surrounding the active pixel, or surrounding the active cluster (Coppola et al.,
2016a, Eq. 6). The radiative power is then RP_PIX = 18.9 · A_PIX · ΔL4_PIX, with A_PIX the
pixel size (1 km² for the resampled MODIS pixels), and a multi-pixel alert is the sum of its
pixel values (Eqs 7 and 8). The stated uncertainty is ±30 % above 600 K; for cooler bodies
the MIR method returns only a minimum estimate of the total thermal output.

<!-- src: [4.7] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), col. der., §'Excess' MIR radiance, Eq. 6 ; [4.8] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), col. der., Eq. 7 ; [4.8] Coppola et al. 2016a, sp426.5.pdf, p. 189 impresa (visor 9), col. izq., Eq. 8 ; [4.9] Coppola et al. 2016a, sp426.5.pdf, p. 197 impresa (visor 17), col. der., §Radiative power uncertainty -->

## 4.2 The Normalized Thermal Index and the spectral-spatial detection

Detection is hybrid: a spectral filter followed by a contextual spatial filter. The spectral
part starts from the Normalized Thermal Index of Wright et al. (2002),
NTI = (L_MIR − L_TIR)/(L_MIR + L_TIR) (Coppola et al., 2016a, Eq. 1). Because the NTI is
based on absolute radiances, its value varies with geography and season (Wright et al., 2002,
p. 141), so MIROVA normalises it per image: treating
each pixel as isothermal at the TIR brightness temperature gives an "apparent" NTI
(Eqs 2-3), and a quadratic regression of observed against apparent NTI yields a background
index NTI_bk = a·NTI_app² + b·NTI_app + c (Eqs 4-5), fitted separately for every image. The
Enhanced Thermal Index is the residual, ETI = NTI − NTI_bk, on which hotspots that are weak in
the raw NTI, and absent from NTI_bk, stand out clearly.

<!-- src: [4.10] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), col. izq., 2.º párrafo ; [4.10] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3), col. der., 2.º párrafo ("hybrid and contextual approach") ; [4.11] Coppola et al. 2016a, sp426.5.pdf, Eq. 1: LOCALIZADOR PENDIENTE DE VERIFICAR EN IMAGEN (ver Notas para el editor); L_TIR = banda 32 sí verificada en p. 183 impresa (visor 3), lista (vii) ; [4.12] Wright et al. 2002, wright2002_rse_automated_volcanic_eruption_detection_10.1016-S0034-4257(02)00030-5.pdf, p. 141 impresa (visor 7), col. izq., párrafo bajo la Fig. 6 ; [4.13] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. izq., Eqs 2 a 5 (la Eq. 4 impresa trae la errata "+ bNTI + c") ; [4.14] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. der., 1.er párrafo -->

The spatial part subtracts from each pixel the arithmetic mean of its eight neighbours,
producing the dNTI and dETI matrices. Coppola et al. (2016a) are explicit that this is a plain
spatial filter: clouds are not taken into account, and all eight neighbours enter the average
regardless of the surface they image. Pixels at the edge of the resampled matrices, and those
with dNTI or dETI below −0.1, are declared unsuitable and excluded.

<!-- src: [4.15] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. der., §Spatial analysis, 1.er y 2.º párrafo ; [4.16] Coppola et al. 2016a, sp426.5.pdf, p. 185 impresa (visor 5), col. der., lista de viñetas -->

Thresholds are applied over two concentric regions of interest: an inner 5 × 5 km box centred
on the summit (ROI1), where small-scale activity is expected, and the surrounding 50 × 50 km
frame (ROI2). Test 1 is a fixed threshold, NTI_PIX > K1, with K1 common to both ROIs but
distinct for night and day, inherited from MODVOLC (Wright et al., 2002); pixels satisfying
it are flagged active and then discarded from the subsequent steps. Tests 2 and 3 are
contextual and must both hold: a pixel is flagged active when dNTI_PIX > C1 or
dNTI_PIX > μ_dNTI + C2·σ_dNTI, and simultaneously when the same disjunction holds for dETI,
μ and σ being the mean and standard deviation of all suitable pixels in the image. C1 and C2
differ between the ROIs (which differ in size and in prior probability of containing an
anomaly) and between night and day, because solar effects amplify the variability of both
matrices. Their published values (Table 1) are K1 = −0.8 night and −0.6 day; C1 = 0.003 in
ROI1 and 0.01 in ROI2 at night, 0.02 in both by day; C2 = 5 and 10 respectively at night, 15
in both by day.

<!-- src: [4.17] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), col. der., §Regions of interest, sigue en p. 184 impresa (visor 4) (ROI1 vista en imagen; ROI2 de 50 × 50 km sólo en capa de texto de p. 184) ; [4.18] Coppola et al. 2016a, sp426.5.pdf, p. 186 impresa (visor 6), §Fixed NTI threshold, col. izq. y der. ; [4.19] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), col. izq., Tests 2 y 3 y párrafo "where the subscript" ; [4.20] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), col. izq. último párrafo y col. der. 1.er párrafo ; [4.21] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), Tabla 1 -->

## 4.3 Second run and calibration of the thresholds

Active pixels perturb the neighbourhood average the spatial filter relies on, so the dNTI and
dETI values of pixels adjacent to a detection are artificially depressed. To recover them,
MIROVA repeats the spatial analysis with all previously detected active pixels removed and
reapplies Tests 2 and 3 to the new matrices, only when the first run produced at least one
detection.

<!-- src: [4.22] Coppola et al. 2016a, sp426.5.pdf, p. 187 impresa (visor 7), col. der., §Second run; sigue en p. 188 impresa (visor 8), col. izq. -->

The threshold set was calibrated on more than 20 000 images of Stromboli and Mt Etna as the
best compromise between omission (~10 %) and false detections (~5 %). The trade-off is
quantified for C2: visual inspection of night-time Etna images from 2006 shows that C2 ≥ 10
suppresses false detections but misses more than 25 % of small alerts (<10 MW), whereas
C2 ≤ 3 misses only 7 % at the cost of more than 7 % false detections. Because these values
describe the natural variability of dNTI and
dETI, they act as self-adapting thresholds, independent of local climate and topography,
which makes the scheme exportable without processing a historical archive. Later versions
keep the summation over the detected pixels (Coppola et al., 2020, p. 3; 2023, p. 3, Eq. 1);
the product's detectable floor is of the order of 1 MW.

<!-- src: [4.23] Coppola et al. 2016a, sp426.5.pdf, p. 189 impresa (visor 9), col. izq., §Performance and exportability, 2.º párrafo ; [4.24] Coppola et al. 2016a, sp426.5.pdf, p. 189 impresa (visor 9), col. izq., 1.er párrafo ; [4.25] Coppola et al. 2016a, sp426.5.pdf, p. 189 impresa (visor 9), col. izq., 3.er párrafo ; [4.26] Coppola et al. 2023, feart-11-1240107.pdf, p. 3 impresa (visor 3), §2.2, Eq. 1 ; [4.26] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3), col. der., ecuación del VRP ; [4.27] Coppola et al. 2023, feart-11-1240107.pdf, p. 4 impresa (visor 4), col. izq., 2.º párrafo ; [4.27] Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3), col. der., último párrafo -->

## 4.4 Sensors, grids and products

Cropping and resampling precede detection and are not cosmetic: MODIS ground pixels grow with
scan angle (up to about 10 km² at 55°), so a sub-pixel hotspot would otherwise be integrated
over a variable area, and the contextual scheme requires a homogeneous pixel scale. MIROVA
crops the Level 1B data to a 50 × 50 km grid centred on the summit, taking coordinates from
the Global Volcanism Program database, and resamples onto an equally spaced 1 km grid. The MIR
channel is a composite band at 3.959 μm built from band 21 or band 22 depending on whether the
high-gain band saturates; the TIR channel of the NTI is band 32 at 12.02 μm.

<!-- src: [4.28] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), col. der., §Cropping and resampling, 1.er párrafo ; [4.29] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), col. der., 2.º párrafo ; [4.30] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), lista (iv)-(v) en col. izq. y banda compuesta en col. der., párrafo "Lastly, we built" ; [5.21] Coppola et al. 2016a, sp426.5.pdf, p. 183 impresa (visor 3), lista (vii) (banda 32 a 12.02 µm) -->

The same algorithm was later applied to VIIRS. For the 750 m M-bands, Campus et al. (2022)
resample onto a UTM 51 × 51 km grid centred on the summit, keeping the nominal resolution and
producing 67 × 67 pixel matrices; the bands are M13 (3.973-4.128 μm) and M15
(10.263-11.263 μm). For the 375 m I-bands, Campus et al. (2024) use I4 at 3.74 μm with I5 at
11.45 μm over a pixel area of 140 625 m², reporting fumarolic detections between 0.02 and
1.11 MW. At Sabancaya the 375 m data detected thermal anomalies from January 2012, about two
years before MODIS at 1 km (Coppola et al., 2022, p. 7; Coppola, 2025, p. 342).

<!-- src: [4.31] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 7 impresa (visor 7), §3.2, 2.º párrafo ; [4.32] Campus et al. 2022, bandas M13 y M15: LOCALIZADOR PENDIENTE DE VERIFICAR EN IMAGEN (ver Notas para el editor) ; [4.33] Campus et al. 2024, s00445-024-01721-z.pdf, p. 3 impresa (visor 3), col. der., 1.er párrafo ; [4.34] Campus et al. 2024, s00445-024-01721-z.pdf, p. 4 impresa (visor 4), col. izq., Eq. 3 ; [4.35] Campus et al. 2024, s00445-024-01721-z.pdf, p. 6 impresa (visor 6), col. izq., 2.º párrafo ; [4.36] Coppola 2025, 978-3-031-86841-2.pdf, p. 342 impresa (visor 346), §3.2.1, col. der., 1.er párrafo, y Fig. 6 ; [4.36] Coppola et al. 2022, s00445-022-01523-1.pdf, p. 7 impresa (visor 7), §The unrest period (2012-2016), 1.er párrafo -->

## 4.5 What MIROVA publishes, and what is not published

The near-real-time chain ingests MODIS-NRT granules from LANCE, which delivers Level 1 data
within about 3 h of acquisition, and posts updated NTI maps and radiative power time series
within 1-4 h of the overpass. The web page shows the latest radiative power and thermal map,
with an anomaly label coloured on an intensity scale: Low below 1 MW, Moderate 1-10 MW, High
10-100 MW, Very High 100-1000 MW, Extreme 1000-10 000 MW (Coppola et al., 2016a, p. 196,
Fig. 11).

<!-- src: [4.37] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), col. izq., 1.er párrafo ; [4.38] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), leyenda de la Fig. 11 -->

Two published caveats bear on any attempt to reproduce the system. First, clouds are handled
a posteriori: the algorithm does not discriminate cloudy pixels, and cloud-affected data are
discarded by visual inspection after the fact; Campus et al. (2022) evaluate the unsupervised
near-real-time mode, leaving the raw data without such filters. Second, false alerts occur
mainly in daytime images at the edges of water bodies and within scattered clouds and
typically radiate less than 5 MW, while fires and anthropogenic heat sources cannot be
distinguished by the algorithm and are identified only in post-analysis. Coppola et al.
(2014, p. 3413) noted that a 2 MW cutoff would remove the night-time false detections but
reduce correct detections from ~79 % to below 59 %, and preferred to keep some false alerts
rather than miss real hotspots.

<!-- src: [4.39] Coppola et al. 2016a, sp426.5.pdf, p. 188 impresa (visor 8), col. izq. 2.º párrafo y col. der. 2.º párrafo ; [4.40] Campus et al. 2022, campus2022_sensors_22_1713.pdf, p. 8 impresa (visor 8), §3.4, 3.er párrafo ; [4.41] Coppola et al. 2016a, sp426.5.pdf, p. 196 impresa (visor 16), col. der., §False alerts, sigue en p. 197 impresa (visor 17), col. izq. ; [4.42] Coppola et al. 2016a, sp426.5.pdf, p. 197 impresa (visor 17), col. izq., §Fires and anthropogenic heat sources ; [4.43] Coppola et al. 2014, coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf, p. 3413 impresa (visor 13), §3 Algorithm performance, último párrafo ; docs/AUDIT_S128.md:518-534 -->

What none of these publications provides is executable code. The algorithm is fully specified
in the literature, but the system is distributed as a web product covering target volcanoes
chosen by its operators, and no reference implementation has been released for independent
use, audit or extension. That gap is what the present work addresses.

<!-- src: [4.44] ausencia de código: SIN LOCALIZAR (argumento de ausencia, ver nota 6) ; [4.44] volcanes objetivo: Coppola et al. 2020, Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf, p. 3 impresa (visor 3), col. izq., 2.º párrafo -->

---

## References used in this section

| Key | Reference | DOI |
|---|---|---|
| Campus et al., 2022 | Campus, A., Laiolo, M., Massimetti, F., Coppola, D. The transition from MODIS to VIIRS for global volcano thermal monitoring. *Sensors* 22(5):1713. | 10.3390/s22051713 |
| Campus et al., 2024 | Campus, A., Aveni, S., Laiolo, M., Massimetti, F., Coppola, D. Thermal unrest at La Fossa (Vulcano Island, Italy): the 2021-2023 VIIRS 375 m MIROVA-processed dataset. *Bull. Volcanol.* 86:25. | 10.1007/s00445-024-01721-z |
| Coppola et al., 2014 | Coppola, D., Laiolo, M., Delle Donne, D., Ripepe, M., Cigolini, C. Hot-spot detection and characterization of strombolian activity from MODIS infrared data. *Int. J. Remote Sens.* 35(9):3403-3426. | 10.1080/01431161.2014.903354 |
| Coppola et al., 2016a | Coppola, D., Laiolo, M., Cigolini, C. et al. Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system. *Geol. Soc. London Spec. Publ.* 426(1):181-205. | 10.1144/SP426.5 |
| Coppola et al., 2020 | Coppola, D. et al. Thermal remote sensing for global volcano monitoring (título completo y autores por verificar en imagen). *Front. Earth Sci.* 7:362. | 10.3389/feart.2019.00362 |
| Coppola et al., 2022 | Coppola, D., Valade, S., Masias, P., Laiolo, M., Massimetti, F., Campus, A. et al. Shallow magma convection … during the dome-forming Sabancaya eruption (2012-2020). *Bull. Volcanol.* 84:16. | 10.1007/s00445-022-01523-1 |
| Coppola et al., 2023 | Coppola, D. et al. MIROVA database v1 (título completo, autores, volumen y DOI por verificar en imagen). *Front. Earth Sci.* Archivo `feart-11-1240107.pdf`. | [DOI pendiente] |
| Laiolo et al., 2026 | Laiolo, M. et al. Switching between ordinary and non-ordinary activity at Stromboli volcano: insights from short- and long-term thermal trends recorded from space. *Bull. Volcanol.* 88:11. | 10.1007/s00445-025-01932-y |
| Coppola, 2025 | Coppola, D. Thermal Monitoring of Volcanoes from Space. In: *Modern Volcano Monitoring*, Springer, pp. 325-364. | 10.1007/978-3-031-86841-2_11 |
| Wooster et al., 2003 | Wooster, M. J., Zhukov, B., Oertel, D. Fire radiative energy for quantitative study of biomass burning: derivation from the BIRD experimental satellite and comparison to MODIS fire products. *Remote Sens. Environ.* 86:83-107. | 10.1016/S0034-4257(03)00070-1 |
| Wright et al., 2002 | Wright, R., Flynn, L. P., Garbeil, H., Harris, A. J. L., Pilger, E. Automated volcanic eruption detection using MODIS. *Remote Sens. Environ.* 82:135-155. | 10.1016/S0034-4257(02)00030-5 |

<!-- src: [R4.1] Campus et al. 2022: lista de referencias de Campus et al. 2024, s00445-024-01721-z.pdf, p. 6 impresa (visor 6) ; [R4.2] Campus et al. 2024, s00445-024-01721-z.pdf, encabezado "Bulletin of Volcanology (2024) 86:25" (autores no vistos en imagen) ; [R4.3] Coppola et al. 2014, coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf, visor 1 (portada Taylor & Francis) ; [R4.4] Coppola et al. 2016a, sp426.5.pdf, p. 181 impresa (visor 1) ; [R4.5] Coppola et al. 2022, s00445-022-01523-1.pdf, encabezado de p. 7 impresa (visor 7) ; [R4.6] Laiolo et al. 2026, s00445-025-01932-y.pdf, visor 1 (título y DOI) ; [R4.7] Coppola 2025, 978-3-031-86841-2.pdf, p. 325 impresa (visor 329) ; [R4.8] Wooster et al. 2003, 1-s2.0-S0034425703000701-main.pdf, p. 83 impresa (visor 1), pie ; [R4.9] Wright et al. 2002, wright2002_rse_automated_volcanic_eruption_detection_10.1016-S0034-4257(02)00030-5.pdf, p. 135 impresa (visor 1), pie (PII S0034-4257(02)00030-5) ; Coppola et al. 2020: revista, volumen y DOI según el hallazgo H1 del verificador (docs/audit_s141/lectura/VERIFICADOR_MANUSCRITO.md), sin página de portada citada -->

---

## Localizadores: archivos PDF y convención de página

Todos los archivos están en `documentacion\`. "p. impresa" es el folio del artículo y "visor" la
página del PDF. Los localizadores de cada comentario `src` fueron verificados mirando la página
renderizada (`docs/audit_s141/lectura/VERIFICADOR_MANUSCRITO.md`); el número entre corchetes es la
fila de ese informe.

| ref | paper (autor, año, revista) | archivo PDF | convención de página |
|---|---|---|---|
| Coppola et al., 2016a | Coppola et al. 2016a, *Geol. Soc. London Spec. Publ.* 426 | `sp426.5.pdf` | p. impresa = visor + 180. **Deducida, no leída**: el PDF no imprime folios; el rango 181-205 sale de la lista de referencias de Campus et al. 2024 (p. 6), y lo confirman las 25 páginas del PDF y la alternancia de encabezados recto/verso |
| Coppola, 2025 | Coppola 2025, capítulo 11 de *Modern Volcano Monitoring* (Springer) | `978-3-031-86841-2.pdf` (libro completo) | p. impresa = visor − 4 (p. 325 = visor 329; p. 337 = visor 341; p. 342 = visor 346). **`978-3-031-86841-2_9.pdf` NO es este capítulo**: es "Remote Monitoring of Volcanic Gases" de R. Campion (p. 261, DOI _9) |
| Campus et al., 2022 | Campus et al. 2022, *Sensors* 22:1713 | `campus2022_sensors_22_1713.pdf` | p. impresa = visor |
| Campus et al., 2024 | Campus et al. 2024, *Bull. Volcanol.* 86:25 | `s00445-024-01721-z.pdf` | p. impresa = visor |
| Coppola et al., 2014 | Coppola et al. 2014, *Int. J. Remote Sens.* 35(9) | `coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf` | p. impresa = visor + 3400 (visor 1 es la portada de Taylor & Francis; visor 13 = p. 3413) |
| Coppola et al., 2020 | Coppola et al. 2020, *Front. Earth Sci.* 7:362 | `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` | p. impresa = visor |
| Coppola et al., 2022 | Coppola et al. 2022, *Bull. Volcanol.* 84:16 | `s00445-022-01523-1.pdf` | p. impresa = visor |
| Coppola et al., 2023 | Coppola et al. 2023, *Front. Earth Sci.* (MIROVA database v1) | `feart-11-1240107.pdf` | p. impresa = visor |
| Laiolo et al., 2026 | Laiolo et al. 2026, *Bull. Volcanol.* 88:11 | `s00445-025-01932-y.pdf` | p. impresa = visor |
| Wooster et al., 2003 | Wooster et al. 2003, *Remote Sens. Environ.* 86 | `1-s2.0-S0034425703000701-main.pdf` | p. impresa = visor + 82 (visor 1 = p. 83; visor 5 = p. 87) |
| Wright et al., 2002 | Wright et al. 2002, *Remote Sens. Environ.* 82 | `wright2002_rse_automated_volcanic_eruption_detection_10.1016-S0034-4257(02)00030-5.pdf` | p. impresa = visor + 134 (visor 1 = p. 135; visor 7 = p. 141) |

---

## Notas para el editor

Todo número de esta sección está anclado a archivo:línea. No quedó ningún placeholder
numérico pendiente. Lo que sigue son las afirmaciones que **no** pude verificar del todo, y
las contradicciones que aparecieron entre fuentes del repo.

1. **La banda TIR del NTI: B32 (12.02 μm) o B31 (11.03 μm).** `sp426_5.txt:214-216` dice
   textualmente que L_TIR es la radiancia del canal TIR, «L32», es decir 12.02 μm, y la
   Tabla 2 de `coppola2024_chapter.txt:1034-1037` repite «TIR (12.02 μm)». El `CLAUDE.md`
   del proyecto y la implementación usan la banda 31 (11 μm). No es un problema de esta
   sección (acá describo lo publicado), pero **§5 tiene que declarar y justificar esa
   divergencia**, porque hoy queda como diferencia no explicada frente al canon.

2. **RESUELTA (S141).** ~~El tamaño de la grilla: 50 × 50 km o 51 × 51 km.~~ El grupo usa las
   dos cifras, incluso para la misma grilla UTM: 50 × 50 km en Coppola et al. 2016a, p. 183
   impresa (visor 3), col. der., 2.º párrafo; en Coppola et al. 2020, p. 3; y en Campus et al.
   2024, p. 3. 51 × 51 km en Campus et al. 2022, p. 7, §3.2, 2.º párrafo, y en Coppola et al.
   2023, p. 3. La prosa queda como está (cada fuente con su cifra); una nota al pie sigue siendo
   opcional. Texto original de la nota: Coppola et al. (2016a) dice
   50 × 50 km para MODIS (`sp426_5.txt:164-167, 201`). Campus et al. (2022), verbatim en
   `BIBLIOGRAPHY_SYNTHESIS.md:99`, dice **UTM 51 × 51 km** y «matrices de 51 × 51 píxeles
   obtenidas de MODIS». Escribí 50 × 50 km para MODIS y 51 × 51 km para VIIRS 750 m porque
   es lo que dice cada fuente, pero las dos no pueden ser exactas a la vez. Conviene una
   nota al pie, o resolverlo contra el capítulo Springer.

3. **RESUELTA (S141) como confirmación del desliz.** El capítulo sí dice «A_pix = 0.75 × 10⁶
   m²»: Coppola 2025, p. 337 impresa (visor 341), visto en imagen. El valor de Campus et al.
   2022 (0.5625 km²) está en p. 7, Eq. 1. Sigue sin usarse en §4. Texto original: A_pix de
   VIIRS M-band: 0,5625 km² o 0,75 × 10⁶ m². `coppola2024_chapter.txt:1141-1143`
   da «A_pix = 0.75 × 10⁶ m²» para las bandas de 750 m, pero 750 × 750 m son 562 500 m², que
   es lo que registra `BIBLIOGRAPHY_SYNTHESIS.md:101` citando a Campus 2022. Parece un desliz
   del capítulo. **No usé ninguno de los dos números en §4** para no propagarlo; el valor
   operativo va en Methods.

4. **«Laiolo 2026» SÍ está en el repo (corregido S135).** La nota original de esta sección
   decía que no existía. Es el falso negativo de la regla A89: el archivo está nombrado por
   DOI, `documentacion/s00445-025-01932-y.pdf` (Laiolo et al., *Bull. Volcanol.* 88:11), y
   buscar «laiolo» devuelve cero. `docs/MISSION.md:38-60` lo lista entre los once papers
   canónicos y registra que S128 verificó **verbatim** contra la p. 4 del PDF la afirmación
   de que la cadena NRT de MIROVA no aplica filtrado automático de nubes. El texto de §4.5
   está anclado a Coppola et al. (2016a) (`sp426_5.txt:247-249` y `:362-368`), que sostiene
   lo mismo y es la fuente primaria del algoritmo; **queda pendiente** agregar Laiolo como
   cita directa y su fila a la tabla de referencias con el DOI 10.1007/s00445-025-01932-y.
   **Actualización S141**: título verificado en imagen (visor 1) y completado en la tabla. Matiz
   (fila R4.6 del verificador): la p. 4 (visor 4), col. der., párrafo "The VRP time series", dice
   que no se aplica corrección atmosférica ni filtrado automático de nubes **al dataset** y que se
   evita la inspección visual; no habla de «la cadena NRT». Si se cita, citarlo por el dataset.

5. **RESUELTA (S141).** Las dos frases de Coppola et al. (2014) quedaron cotejadas contra la
   imagen: p. 3413 impresa (visor 13), §3 Algorithm performance, último párrafo. El paper las
   plantea como efecto previsto de un corte sobre el algoritmo nocturno, no como ensayo, y la
   prosa de §4.5 se ajustó a eso («noted that a 2 MW cutoff would…»). Título corregido en la
   tabla («Hot-spot detection and characterization of strombolian activity from MODIS infrared
   data», 35(9):3403-3426, visto en la portada). Las «pp. 3417-3418» que citaba la fila anterior
   no se verificaron y se quitaron. Texto original: Los pasajes del corte de 2 MW
   y del 79 % → 59 % los tomé de `docs/AUDIT_S128.md:518-534`, que los declara verificados
   verbatim contra el PDF (`coppola2014_ijrs_strombolian_*.pdf`, que está en
   `documentacion/`). **No los verifiqué yo mismo contra el PDF** porque el texto extraído no
   está en el repo. Antes de enviar, cotejar esas dos frases contra el original: son las que
   sostienen el argumento de «recall sobre precisión» del paper entero. El título que puse en
   la tabla de referencias para ese paper es tentativo, falta completarlo.

6. **«Ninguna implementación de referencia publicada» es la única afirmación de la sección
   sin fuente positiva.** Es un argumento de ausencia: `sp426_5.txt:132-136` y `:659-673`
   describen el sistema como servicio web sobre una lista de volcanes objetivo, y ninguna
   fuente del repo menciona código distribuido. Es defendible, pero un revisor puede pedir una
   búsqueda explícita (Zenodo/GitHub del grupo de Turín) antes de afirmarlo en letra de molde.
   **S141**: la ausencia de código sigue SIN LOCALIZAR (no es localizable en un PDF). La parte
   positiva, «volcanes objetivo», sí tiene localizador: Coppola et al. 2020, p. 3, col. izq.,
   2.º párrafo. Matiz del localizador: los **datos** sí se liberan (Coppola 2023 en OSF).

7. **RESUELTA (S141): la formulación integrada sobre la ROI entera no existe en Coppola 2020 ni
   2023.** El verificador revisó Coppola 2020 p. 3, Coppola 2023 p. 3 (Eq. 1), Campus 2022 p. 7,
   Campus 2024 p. 3 y Coppola 2025 p. 337: todos suman sobre los píxeles alertados o detectados.
   La frase de §4.3 se reemplazó por «Later versions keep the summation over the detected
   pixels». Coppola 2020 (`Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf`) sí estaba en
   el repo, con nombre sin autor ni DOI (A89). Ambas referencias se agregaron a la tabla, con los
   metadatos que faltan marcados como pendientes. Texto original: Coppola 2015 vs Coppola 2016a.
   El prompt sugería un «Test 1 integrated-ROI (Coppola
   2015)». `BIBLIOGRAPHY_SYNTHESIS.md:36-47` documenta que los dos nombres son **el mismo
   paper** (SP426.5) y que el Test 1 está dentro de `sp426_5.txt:300`. La formulación
   integrada sobre la ROI entera no es de ahí: viene de las versiones operacionales
   posteriores (`BIBLIOGRAPHY_SYNTHESIS.md:89-93`, Coppola 2020/2023). Redacté §4.3 con esa
   separación; si el paper quiere citar la Eq. 1 integrada, hay que citar Coppola et al.
   2020/2023, no 2016a. **Esas dos referencias todavía no están en la tabla de arriba** porque
   no tengo su cita completa verificada en el repo.

8. **La escala de intensidad está en inglés en la fuente.** Coppola et al. (2016a) `:684-685`
   da Low / Moderate / High / Very High / Extreme. El «Muy Bajo» que usa el producto
   per-volcán de mirovaweb.it (y nuestro dashboard) **no aparece en ninguna fuente de
   `documentacion/`**: es la etiqueta del sitio web actual, no del paper. No la usé en §4; si
   el paper la menciona en §6, hay que decir de dónde sale.

9. **El esqueleto del borrador S72 tenía un error de física que corregí.**
   `docs/PAPER_VRP_CHILE_DRAFT_S72.md:138` define el NTI sobre temperaturas de brillo
   (`BT_MIR`, `BT_TIR`). El paper lo define sobre **radiancias** (`sp426_5.txt:211-216`).
   También describe el ETI como «extended TIR test for high-T regimes where MIR saturates»,
   que no es lo que dice la fuente: el ETI es NTI menos el fondo NTI_bk de la regresión
   cuadrática (`sp426_5.txt:275-280`). Ambas cosas quedaron corregidas en esta prosa.

10. **MIROVA no es night-only.** El prompt pedía «night-only» en §4.4, pero la fuente
    describe procesamiento **diurno y nocturno con parámetros distintos**
    (`sp426_5.txt:302-306, 315-321`, y la Tabla 1 tiene columna Daytime). La restricción a
    pasadas nocturnas es una decisión **nuestra**, así que va en §5, no acá. §4.2 ya deja
    dicho que los umbrales se separan día/noche.

11. **§4.2 remite a «Table 1» del manuscrito** para los umbrales, y además los repite entre
    paréntesis. Si esa tabla termina existiendo (está prevista en el esqueleto S72), sacar el
    paréntesis; si no, dejarlo y quitar la remisión.

12. **Fila 4.11 (NO VERIFICABLE): localizador pendiente de verificar en imagen.** La definición
    del NTI como Eq. 1 de Coppola et al. 2016a no se llegó a ver en imagen; el candidato es la
    p. 184 impresa (visor 4). Lo que sí se vio es la p. 183 impresa (visor 3), lista (vii): la
    banda 32 a 12.02 µm como canal TIR.

13. **Fila 4.32 (NO VERIFICABLE): localizador pendiente de verificar en imagen.** Los rangos de
    M13 (3.973-4.128 µm) y M15 (10.263-11.263 µm) de Campus et al. 2022 no se llegaron a ver en
    imagen; el candidato es la p. 6 (visor 6), §3.1 y Tabla 1.

14. **Fila 4.17, mitad ROI2: localizador pendiente de verificar en imagen.** La ROI1 de 5 × 5 km
    se vio en la p. 183 impresa (visor 3); la ROI2 de 50 × 50 km sólo se leyó en la capa de texto
    de la p. 184 impresa (visor 4).

15. **Metadatos pendientes en la tabla de referencias.** Coppola et al. 2020: el título completo
    y los autores no se vieron en imagen (revista, volumen y DOI vienen del hallazgo H1 del
    verificador). Coppola et al. 2023: título, autores, volumen y DOI sin verificar. Campus et al.
    2024: los autores no se vieron en imagen (revista y número sí).
