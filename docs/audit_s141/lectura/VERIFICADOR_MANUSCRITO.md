# Verificador del localizador de citas del manuscrito VRP Chile

Auditoría S141, verificación con contexto limpio de
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s141\lectura\LOCALIZADOR_MANUSCRITO.md`.
Fecha: 2026-09-14. No se tocó el manuscrito, git ni ningún otro archivo del repo.

## Método

Cada fila se comprobó mirando la página renderizada a 200 dpi (`page.get_pixmap(dpi=200)`), imágenes en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\render_V2\`.
La capa de texto se usó sólo para buscar páginas candidatas (caminos alternativos de cada NO DICE ESO).
Lo que no pude mirar en imagen va como **NO VERIFICABLE** o **SOSPECHA**.

"p." = página impresa; "v." = página del visor. Veredictos míos: CORRECTO / LOCALIZADOR CORRIDO /
VEREDICTO ERRÓNEO / NO VERIFICABLE.

---

## Sección 4: `docs\paper\sec4_background.md`

| # | archivo:línea | Localizador | Mi veredicto | Localizador final | Cita vista | Reemplazo (inglés) |
|---|---|---|---|---|---|---|
| 4.1 | sec4:3-5 | CONFIRMA | CORRECTO | Coppola et al. 2016a, `sp426.5.pdf`, p. 181 (v. 1), Abstract | "a new volcanic hotspot detection system, named Middle InfraRed Observation of Volcanic Activity (MIROVA)" | |
| 4.2 | sec4:4-5 | CONFIRMA | LOCALIZADOR CORRIDO (sólo en Campus 2024) | Campus 2022, p. 7 (v. 7), §3.2, 1.er párrafo. Campus 2024, `s00445-024-01721-z.pdf`, p. 3 (v. 3), §Methodology, **1.er párrafo** (empieza al pie de la col. izq. y sigue en la der.), no el 2.º | 2024: "enriched through the years to operate using acquisitions from different sensors such as the VIIRS" | (sólo agregar cita) |
| 4.3 | sec4:6-8 | MATIZA | CORRECTO | No aplica: la sección cita Wooster 2003 (King's College/Berlín) y Wright 2002 (Hawaii), visto en sus portadas | | "citing primarily sources authored by the MIROVA group" |
| 4.4 | sec4:12-16 | CONFIRMA | CORRECTO | Coppola 2025, `978-3-031-86841-2.pdf`, p. 337 (v. 341), col. der., 2.º párrafo, Eq. 17; Wooster 2003, p. 87 (v. 5), Fig. 3 | 2025: "for this range of temperatures, the MIR radiance can be approximate by L_MIR ≈ αT⁴". Wooster Fig. 3: "In the range 600-1500 K, the ratio has a value 19.68 µm·sr ± 30%" | |
| 4.5 | sec4:12-13 | CONFIRMA | CORRECTO | 2016a, p. 197 (v. 17), col. der., §Radiative power uncertainty | "(which applies to most active lava surfaces: cf. Wright et al. 2010)" | |
| 4.6 | sec4:16-18 | CONFIRMA | CORRECTO | Coppola 2025, p. 337 (v. 341), col. der., 3.er párrafo | "Eq. 17 can be applied to any sensor with a MIR channel, independently from the spatial resolution" | |
| 4.7 | sec4:22-25 | CONFIRMA | CORRECTO | 2016a, p. 188 (v. 8), col. der., §'Excess' MIR radiance, Eq. 6 | "estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)" | |
| 4.8 | sec4:25-27 | CONFIRMA | CORRECTO | 2016a, p. 188 (v. 8), col. der., Eq. 7; p. 189 (v. 9), col. izq., Eq. 8 | "RP_PIX = 18.9 × A_PIX × ΔL_4PIX"; "(1 km² for the resampled MODIS pixels)" | |
| 4.9 | sec4:27-28 | CONFIRMA | CORRECTO | 2016a, p. 197 (v. 17), col. der., §Radiative power uncertainty | "provides only a minimum value for the whole thermal output" | |
| 4.10 | sec4:34 | CONFIRMA | CORRECTO; hay fuente literal mejor para "hybrid" | 2016a, p. 188 (v. 8), col. izq., 2.º párrafo; **Coppola et al. 2020**, `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf`, p. 3 (v. 3), col. der., 2.º párrafo (ver H1) | 2020: "thus constituting a hybrid and contextual approach for any environmental condition" | |
| 4.11 | sec4:35-36 | CONFIRMA | NO VERIFICABLE (no logré ver la imagen de p. 184, v. 4) | 2016a, p. 184 (v. 4), Eq. 1. SOSPECHA de que es correcto: p. 183 (v. 3), lista (vii), sí dice banda 32 a 12.02 µm como TIR | p. 183: "radiance of band 32 (L32), centred at 12.02 µm (TIR channel)" | |
| 4.12 | sec4:36-37 | MATIZA | CORRECTO | Wright et al. 2002, p. 141 (v. 7), col. izq., párrafo bajo la Fig. 6 | "As the NTI is based on absolute radiance values, variations in geography and season will influence its value" | "Because the NTI is based on absolute radiances, its value varies with geography and season (Wright et al., 2002, p. 141)" |
| 4.13 | sec4:37-40 | CONFIRMA | CORRECTO; se ve la errata "+ bNTI + c" en la Eq. 4 | 2016a, p. 185 (v. 5), col. izq., Eqs 2 a 5 | "distinct regression coefficients are retrieved from each single image" | |
| 4.14 | sec4:40-42 | MATIZA | CORRECTO | 2016a, p. 185 (v. 5), col. der., 1.er párrafo | "absent from the background NTI_bk maps (Fig. 3b, e) or weak on the NTI maps (Fig. 3a, d)" | "on which hotspots that are weak in the raw NTI, and absent from NTI_bk, stand out clearly" |
| 4.15 | sec4:46-49 | CONFIRMA | CORRECTO | 2016a, p. 185 (v. 5), col. der., §Spatial analysis, 1.er y 2.º párrafo | "the presence of clouds is not taken into account by the algorithm and all eight neighbouring pixels are used" | |
| 4.16 | sec4:49-50 | CONFIRMA | CORRECTO | 2016a, p. 185 (v. 5), col. der., lista de viñetas | "all the pixels with dNTI or dETI < -0.1" | |
| 4.17 | sec4:54-56 | CONFIRMA | CORRECTO para ROI1 (imagen p. 183); ROI2 de 50 × 50 km sólo capa de texto de p. 184 | 2016a, p. 183 (v. 3), col. der., §Regions of interest, sigue en p. 184 | "inner region (ROI1) consists of a box (5 × 5 km) centred on the volcano's summit" | |
| 4.18 | sec4:56-58 | CONFIRMA | CORRECTO | 2016a, p. 186 (v. 6), §Fixed NTI threshold (col. izq. y der.) | "Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded (unsuitable) for further steps." | |
| 4.19 | sec4:59-61 | CONFIRMA | CORRECTO | 2016a, p. 187 (v. 7), col. izq., Tests 2 y 3 y párrafo "where the subscript" | "μ and σ are the arithmetic mean and standard deviation of all the suitable pixels within the image" | |
| 4.20 | sec4:61-64 | CONFIRMA | CORRECTO | 2016a, p. 187 (v. 7), col. izq. último párrafo y col. der. 1.er párrafo | "because solar effects amplify the variability in NTI and ETI matrices in daytime data" | |
| 4.21 | sec4:64-66 | CONFIRMA | CORRECTO (Tabla 1 leída en imagen) | 2016a, p. 187 (v. 7), Tabla 1 | K1 -0.8/-0.8/-0.6/-0.6; C1 0.003/0.01/0.02/0.02; C2 5/10/15/15 | |
| 4.22 | sec4:72-76 | CONFIRMA | CORRECTO | 2016a, p. 187 (v. 7), col. der., §Second run; sigue en p. 188 (v. 8), col. izq. | "The last step is applied only if one or more pixels have been detected by the previous tests" | |
| 4.23 | sec4:80-81 | CONFIRMA | CORRECTO | 2016a, p. 189 (v. 9), col. izq., §Performance and exportability, 2.º párrafo | "the best compromise between omitted (c. 10%) and false (c. 5%) detections" | |
| 4.24 | sec4:81-84 | MATIZA | CORRECTO | 2016a, p. 189 (v. 9), col. izq., 1.er párrafo | "a value of C2 ≥ 10 will efficiently avoid false detections but will cause the omission of more than 25% of the small alerts" | "Visual inspection of night-time Etna images from 2006 shows that C2 ≥ 10 suppresses false detections but misses more than 25 % of small alerts (<10 MW), whereas C2 ≤ 3 misses only 7 % at the cost of more than 7 % false detections" |
| 4.25 | sec4:84-86 | CONFIRMA | CORRECTO | 2016a, p. 189 (v. 9), col. izq., 3.er párrafo | "self-adapting thresholds for each analysed scene 'independent' of the local conditions (climate, temperature and topography)" | |
| 4.26 | sec4:86-88 | NO DICE ESO + SIN LOCALIZAR (Coppola 2020) | **VEREDICTO ERRÓNEO en la mitad "SIN LOCALIZAR"**: Coppola 2020 sí está en el repo (H1) y tampoco lo dice. El NO DICE ESO se sostiene. Caminos revisados: Coppola 2020 p. 3, Coppola 2023 p. 3, Campus 2022 p. 7, Campus 2024 p. 3, Coppola 2025 p. 337. Todos suman sobre píxeles alertados | Coppola 2023, `feart-11-1240107.pdf`, p. 3 (v. 3), §2.2, Eq. 1; Coppola 2020, p. 3 (v. 3), col. der., ecuación del VRP | 2023: "where N_pix is the number of detected pixels". 2020: "where npix is the number of alerted pixels" | "Later versions keep the summation over the detected pixels (Coppola et al., 2020, p. 3; 2023, p. 3, Eq. 1)", o borrar la frase |
| 4.27 | sec4:88-89 | CONFIRMA | CORRECTO | Coppola 2023, p. 4 (v. 4), col. izq., 2.º párrafo; también Coppola 2020, p. 3, col. der., último párrafo | 2023: "In the case of MODIS with a resolution of 1 km, accurate values of VRP can be detected above ~1 MW" | |
| 4.28 | sec4:95-97 | CONFIRMA | CORRECTO | 2016a, p. 183 (v. 3), col. der., §Cropping and resampling, 1.er párrafo | "(up to c. 10 km² for scan angles of 55°: Nishihama et al. 1997)" | |
| 4.29 | sec4:97-99 | CONFIRMA | CORRECTO; la nota 50/51 km tiene más fuentes (H3) | 2016a, p. 183 (v. 3), col. der., 2.º párrafo | "resampled (into an equally spaced 1 km grid) the MODIS Level 1B data that fall within a grid (50 × 50 km)" | |
| 4.30 | sec4:99-101 | CONFIRMA | CORRECTO; precisión de lugar | 2016a, p. 183 (v. 3): lista (iv)-(v) en col. izq.; banda compuesta en col. der., párrafo "Lastly, we built" | "by using the L21 or L22 radiance, depending on band 22 saturation (or not), respectively" | |
| 4.31 | sec4:105-107 | CONFIRMA | CORRECTO | Campus 2022, `campus2022_sensors_22_1713.pdf`, p. 7 (v. 7), §3.2, 2.º párrafo | "Resampling is performed in a UTM 51 × 51 km grid, centered on the volcano summit" | |
| 4.32 | sec4:107-108 | CONFIRMA | NO VERIFICABLE (no logré ver p. 6) | Campus 2022, p. 6 (v. 6), §3.1 y Tabla 1 | | |
| 4.33 | sec4:108-109 | CONFIRMA | CORRECTO | Campus 2024, p. 3 (v. 3), col. der., 1.er párrafo | "centred at wavelengths of 3.74 and 11.45 µm, respectively" | |
| 4.34 | sec4:109 | CONFIRMA | CORRECTO | Campus 2024, p. 4 (v. 4), col. izq., Eq. 3 | "A_pix is the pixel size (140,625 m² for VIIRS I-bands)" | |
| 4.35 | sec4:109-110 | CONFIRMA | CORRECTO | Campus 2024, p. 6 (v. 6), col. izq., 2.º párrafo | "the VRP values range between 0.02 and 1.11 MW" | |
| 4.36 | sec4:110-111 | NO DICE ESO | CORRECTO. Caminos revisados: Coppola 2022 p. 7; capítulo 2025 p. 342 y Fig. 6; Coppola 2020 p. 11 (Sabancaya, sin comparación entre sensores). Ninguno da diez años | Coppola 2025, p. 342 (v. 346), §3.2.1, col. der., 1.er párrafo, y Fig. 6; Coppola et al. 2022, p. 7 (v. 7), §The unrest period (2012-2016), 1.er párrafo | 2025: "Starting from 2012 ... VIIRS ... and only two years later they were also detected by MODIS" | "At Sabancaya the 375 m data detected thermal anomalies from January 2012, about two years before MODIS at 1 km (Coppola et al., 2022, p. 7; Coppola, 2025, p. 342)" |
| 4.37 | sec4:117-119 | CONFIRMA | CORRECTO | 2016a, p. 196 (v. 16), col. izq., 1.er párrafo | "delivers Level 1 granules within 3 h of real time"; "within 1-4 h of a satellite overpass" | |
| 4.38 | sec4:119-121 | MATIZA | CORRECTO | 2016a, p. 196 (v. 16), leyenda Fig. 11 | "The colour of the thermal anomaly box (upper right) is automatically set according to the radiative power scale" | "The web page shows the latest radiative power and thermal map, with an anomaly label coloured on an intensity scale: Low below 1 MW, ... (Coppola et al., 2016a, p. 196, Fig. 11)" |
| 4.39 | sec4:125-127 | CONFIRMA | CORRECTO | 2016a, p. 188 (v. 8), col. izq. 2.º párrafo y col. der. 2.º párrafo | "cloud-affected data to be discarded (a posteriori)" | |
| 4.40 | sec4:127-128 | CONFIRMA | CORRECTO | Campus 2022, p. 8 (v. 8), §3.4, 3.er párrafo | "we test the potential efficiency of the algorithm in NRT applications where such supervision is not applied" | |
| 4.41 | sec4:128-130 | CONFIRMA | CORRECTO | 2016a, p. 196 (v. 16) col. der., §False alerts, sigue en p. 197 (v. 17) col. izq. | "these false detections typically radiate less than 5 MW" | |
| 4.42 | sec4:130-131 | MATIZA | CORRECTO | 2016a, p. 197 (v. 17), col. izq., §Fires and anthropogenic heat sources | "cannot be distinguished from genuine volcanic activity ... However, they can be identified during post-analysis (Fig. 9)" | "while fires and anthropogenic heat sources cannot be distinguished by the algorithm and are identified only in post-analysis" |
| 4.43 | sec4:131-133 | MATIZA | CORRECTO | Coppola 2014, p. 3413 (v. 13), §3 Algorithm performance, último párrafo | "such a cutoff will also produce a strong reduction of the efficiency of the algorithm, with the 'Correct' detections decreasing from ~79% to less than 59%" | "Coppola et al. (2014, p. 3413) noted that a 2 MW cutoff would remove the night-time false detections but reduce correct detections from ~79 % to below 59 %, and preferred to keep some false alerts rather than miss real hotspots" |
| 4.44 | sec4:137-140 | SIN LOCALIZAR | CORRECTO (ausencia no localizable). Apoyo positivo para "target volcanoes": Coppola 2020, p. 3 (v. 3), col. izq., 2.º párrafo | 2020: "the data processing chain actually operates only for a list of selected target volcanoes" | |
| R4.1 | sec4:150 | CONFIRMA | CORRECTO (visto en lista de referencias de Campus 2024, p. 6) | | "Sensors 22(5):1713. https://doi.org/10.3390/s22051713" | |
| R4.2 | sec4:151 | CONFIRMA | CORRECTO para revista y número (encabezado "Bulletin of Volcanology (2024) 86:25"); autores no vistos en imagen | | | |
| R4.3 | sec4:152 | NO DICE ESO | CORRECTO | Coppola 2014, v. 1 (portada T&F) | "Hot-spot detection and characterization of strombolian activity from MODIS infrared data, International Journal of Remote Sensing, 35:9, 3403-3426" | "Coppola, D., Laiolo, M., Delle Donne, D., Ripepe, M., Cigolini, C. Hot-spot detection and characterization of strombolian activity from MODIS infrared data. *Int. J. Remote Sens.* 35(9):3403-3426." Las "pp. 3417-3418" no las vi; lo usado en §4 está en p. 3413 |
| R4.4 | sec4:153 | CONFIRMA | CORRECTO | 2016a, p. 181 (v. 1) | "Geological Society, London, Special Publications, 426, http://doi.org/10.1144/SP426.5" | |
| R4.5 | sec4:154 | CONFIRMA | CORRECTO | Coppola 2022, encabezado p. 7 | "Bulletin of Volcanology (2022) 84: 16" | |
| R4.6 | sec4:155 | MATIZA | CORRECTO | Laiolo 2026, v. 1 (título y DOI); p. 4 (v. 4), col. der., párrafo "The VRP time series" | "no atmospheric correction or cloud-contamination automatic filtering is applied to the dataset"; "we avoid the visual inspection" | Título: "Switching between ordinary and non-ordinary activity at Stromboli volcano: insights from short- and long-term thermal trends recorded from space" |
| R4.7 | sec4:156 | CONFIRMA | CORRECTO | Coppola 2025, p. 325 (v. 329) | "Thermal Monitoring of Volcanoes from Space"; "https://doi.org/10.1007/978-3-031-86841-2_11" | |
| R4.8 | sec4:157 | DOI completable | CORRECTO; además el título está truncado (H5) | Wooster 2003, p. 83 (v. 1), pie | "doi:10.1016/S0034-4257(03)00070-1" | Título completo: "Fire radiative energy for quantitative study of biomass burning: derivation from the BIRD experimental satellite and comparison to MODIS fire products" |
| R4.9 | sec4:158 | DOI completable | CORRECTO | Wright 2002, p. 135 (v. 1), pie | "PII: S0034-4257(02)00030-5" | DOI 10.1016/S0034-4257(02)00030-5 |

---

## Sección 5: `docs\paper\sec5_methods.md`

| # | archivo:línea | Localizador | Mi veredicto | Localizador final | Cita vista | Reemplazo (inglés) |
|---|---|---|---|---|---|---|
| 5.1 | sec5:20-21 | CONFIRMA | CORRECTO | 2016a, p. 196 (v. 16), col. izq.; Coppola 2020, p. 3, col. der. ("latency of less than 3 h") | "delivers Level 1 granules within 3 h of real time" | |
| 5.2 | sec5:70-72 | NO DICE ESO | CORRECTO. Caminos revisados: Tabla 1 y §Contextual thresholds (2016a pp. 186-187), Coppola 2014 p. 3413 (su BT11 es condición de nube diurna), Aveni 2024 p. 11 test 11 (compuerta BT, pero de TIRVolcH, 0.5-1 K, no MIROVA MIR). Ninguno pone una compuerta BT con la Tabla 1 | 2016a, p. 187 (v. 7), Tabla 1 | Tabla 1 trae sólo K1, C1 y C2 | "The contextual index gate uses the paper's Table 1 thresholds differentiated by ROI (at night C2 = 5 summit and 10 scene, 15 by day; C1 = 0.003 and 0.01, 0.02 by day). Our additional brightness-temperature gate has no counterpart in Coppola et al. (2016a) and is listed as divergence D22." |
| 5.3 | sec5:71-72 | CONFIRMA | CORRECTO | 2016a, p. 187 (v. 7), Tabla 1 | C1 0.003/0.01/0.02/0.02; C2 5/10/15/15 | |
| 5.4 | sec5:72-74 | MATIZA | CORRECTO | Coppola 2023, p. 3 (v. 3), col. der., 1.er párrafo | "in the summit area (5 × 5 km) slightly lower thresholds are applied ... slightly higher thresholds which reduce false alerts" | "That asymmetry keeps the detector sensitive to small summit anomalies while reducing false alerts farther away (Coppola et al., 2023, p. 3)" |
| 5.5 | sec5:78-80 | CONFIRMA | CORRECTO | 2016a, p. 187 (v. 7), col. izq., Tests 2 y 3 | "dNTI_PIX > C1 or dNTI_PIX > μ_dNTI + C2σ_dNTI (Test 2) and" | |
| 5.6 | sec5:80-83 | MATIZA | CORRECTO | 2016a, p. 185 (v. 5), col. izq. | "A quadratic best-fit regression allows this trend to be normalized"; "retrieved from each single image" | "through a quadratic best-fit regression fitted separately for each image" |
| 5.7 | sec5:83-84 | CONFIRMA | CORRECTO | 2016a, p. 185 (v. 5), col. der., §Spatial analysis, 1.er párrafo | "the average (arithmetic mean) of the eight neighbouring pixels" | |
| 5.8 | sec5:84-86 | MATIZA | CORRECTO | 2016a, p. 185 (v. 5) viñetas; p. 186 (v. 6) Test 1; p. 187 (v. 7), col. der., 2.º párrafo | "pixels flagged as 'active' by means of tests 2 and 3 are subsequently eliminated from further analysis" | "and pixels declared unsuitable by the paper (matrix edges, dNTI or dETI < -0.1, and pixels already flagged active by Tests 1 to 3) are excluded from that pool; our implementation does not yet remove the Test 1 pixels (Section 5.7)" (lo último es SOSPECHA de CLAUDE.md, GAP #A, no verificado en código) |
| 5.9 | sec5:86-88 | CONFIRMA | CORRECTO | 2016a, p. 188 (v. 8), col. izq., 1.er párrafo | "step 2 (spatial analysis) is performed a second time, being particularly careful to eliminate all of the 'active' pixels" | |
| 5.10 | sec5:92-94 | NO DICE ESO | CORRECTO. Caminos revisados: 2016a p. 186; Coppola 2014 pp. 3410 y 3413 (tests diurnos por umbral NTI); Coppola 2020 p. 3, Coppola 2023 p. 3, Campus 2024 p. 3 (todos suman sobre píxeles alertados). Ninguno integra en una ROI de 3 km | 2016a, p. 186 (v. 6), §Fixed NTI threshold | "a simple test based on a fixed NTI threshold: NTI_PIX > K1 (Test 1)" | "In Coppola et al. (2016a) Test 1 is a per-pixel threshold, NTI_PIX > K1. Our implementation adds a path, not described in the MIROVA papers, that integrates MIR radiance over a fixed 3 km ROI around the vent to catch sub-pixel sources; it is declared in Section 5.7." |
| 5.11 | sec5:100-101 | CONFIRMA | CORRECTO | 2016a, p. 188, Eq. 7; Campus 2024, p. 4, Eq. 3; Wooster 2003, p. 87, Fig. 3 | "VRP = k_MIR * A_pix * ΔL_MIR" | |
| 5.12 | sec5:104-107 | CONFIRMA | CORRECTO | 2016a p. 188 Eq. 7; Coppola 2023 p. 3 Eq. 2; Campus 2022 p. 7 Eq. 1; Campus 2024 p. 4 | Campus 2022: "VRP = ΔL_MIR·1.97 × 10⁷·A_pix"; "(equal to 0.5625 for VIIRS M-bands)"; Campus 2024: "VIIRS I4 band has a value of 18.0 µm sr" | |
| 5.13 | sec5:108-109 | CONFIRMA | CORRECTO | Di Bella 2024, p. 7 (v. 7), §3.7, Eq. 5 | "k_VIIRS375 = 2.48 × 10⁷ Wm⁻²sr⁻¹µm⁻¹K⁻⁴" (ver H4) | |
| 5.14 | sec5:113-118 | MATIZA | CORRECTO | Coppola 2023, p. 3 (v. 3), §2.1 final y col. der.; 2016a, p. 183 | "This step is crucial to ensure that all pixels represent a ground area of 1 km²" | "MIROVA resamples each scene onto a grid of constant 1 km² pixels (Coppola et al., 2023, p. 3); VRP Chile does not resample but uses the corresponding uniform nadir pixel area, which the inversion supports" |
| 5.15 | sec5:122-123 | MATIZA | CORRECTO, con un matiz: la objeción (c) vale sólo para el capítulo; Aveni 2024 Eq. 5 sí es un estimador por píxel sobre BT | Coppola 2025, p. 337 (v. 341), col. izq., Eq. 16; Aveni 2024, p. 11 (v. 11), §4.4, Eq. 5 | Aveni: "σ is the Stefan-Boltzmann constant (5.67 × 10⁻⁸ W m⁻² K⁻⁴), ε ... here assumed to be unity" | "A TIR estimator applies pure Stefan-Boltzmann radiation per alerted pixel, as in Aveni et al. (2024, p. 11, Eq. 5), with σ = 5.670374419×10⁻⁸ W m⁻² K⁻⁴ (CODATA 2018)" |
| 5.16 | sec5:123-125 | CONFIRMA | CORRECTO | Aveni 2025, p. 5 (v. 5), leyenda Fig. 2 | "for λ = 11.45, optimal k_TIR has a value of 60.17 µm · sr" (rango ~300-600 K, ±35 %) | |
| 5.17 | sec5:131-133 | MATIZA | CORRECTO | Campus 2022, p. 7; Coppola 2023, p. 3 (51 × 51); 2016a p. 183 y Coppola 2020 p. 3 (50 × 50) | Coppola 2020: "resampled in regular grids of 50 × 50 km (in UTM coordinates)" | "use radius_km = 25, close to the inscribed radius (25-25.5 km) of MIROVA's 50-51 km UTM grid" |
| 5.18 | sec5:133-136 | SIN LOCALIZAR | CORRECTO | | | |
| 5.19 | sec5:167-168 | SIN LOCALIZAR | CORRECTO. SOSPECHA: `GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md` (fuera del repo, no es el texto legal) la nombra "Resolución Exenta CPLT N°372, Diario Oficial 30-ago-2024" | | | |
| 5.20 | sec5:185-186 | CONFIRMA | CORRECTO | 2016a, p. 183 (v. 3); p. 189 (v. 9), col. izq., 3.er párrafo | "(by using the same spatial grid and ROIs)" | |
| 5.21 | sec5:194-196 | CONFIRMA | CORRECTO | 2016a, p. 183 (v. 3), lista (vii); Coppola 2020, p. 3 | "radiance of band 32 (L32), centred at 12.02 µm (TIR channel)" | |

---

## Sección 6: `docs\paper\sec6_validation.md`

| # | archivo:línea | Localizador | Mi veredicto | Localizador final | Cita vista | Reemplazo (inglés) |
|---|---|---|---|---|---|---|
| 6.1 | sec6:16-18 | MATIZA | CORRECTO | Coppola 2023, p. 3 (v. 3), col. izq., 3.er párrafo | "can be freely downloaded from the website www.mirovaweb.it, or from a dedicated repository hosted at https://osf.io/zm62w/" | "MIROVA does not distribute a reprocessed Chilean archive covering 2026, the period of this comparison" |
| 6.2 | sec6:29-32 | MATIZA | **VEREDICTO ERRÓNEO en el fundamento**: la literatura MIROVA sí describe la reflexión solar sobre nubes que sube el NTI. Queda MATIZA porque no dice "near solar noon" ni "cold in the thermal band" | Coppola et al. 2014, p. 3410 (v. 10), §2.4.2 Daytime algorithm, 1.er párrafo | "Solar reflection perturbs NTI as well, especially for pixels sampling reflective surfaces (i.e. water, snow, sand, cloud, etc.), thus causing an increase in its value" | "by day, sunlight reflected by clouds and other reflective surfaces raises the MIR radiance and hence the NTI without any hot source (Coppola et al., 2014, p. 3410)" |
| 6.3 | sec6:36-39 | MATIZA | CORRECTO; se agrega el apoyo más directo | Coppola 2023 p. 4 (v. 4) §2.5; Campus 2022 p. 8 §3.4; 2016a p. 196 col. der. ("completely autonomous") y p. 197 col. izq. §Metereological and volcanic clouds; Laiolo 2026 p. 4; Coppola 2025 p. 346 §4.1 y p. 347 | 2016a p. 197: "the RP time series obtained by MIROVA are provided 'as they are'"; 2023: "This step was done manually" | "The visual supervision described in the MIROVA literature is applied to curated archives (Coppola et al., 2023, p. 4), while the automatically posted time series are provided 'as they are' (Coppola et al., 2016a, p. 197)" |
| 6.4 | sec6:39-40 | CONFIRMA | CORRECTO | Campus 2022, p. 7; Coppola 2020, p. 3 ("216 units"); Coppola 2023, p. 3 (">200") | "a list of ~220 active volcanoes" | |
| 6.5 | sec6:40 | NO DICE ESO | CORRECTO. Caminos revisados: 2016a p. 181 y p. 196; Coppola 2020 p. 3 (LANCE cada 5 min, latencia <3 h); Coppola 2023 p. 3-4. Ninguno dice "cada una o dos horas" | 2016a, p. 196 (v. 16), col. izq. | "scans the LANCE ftp site every 5 min"; "within 1-4 h of a satellite overpass" | "within 1-4 h of each overpass (Coppola et al., 2016a, p. 196)" |
| 6.6 | sec6:40 | SIN LOCALIZAR | **VEREDICTO ERRÓNEO**: es localizable (MATIZA: se habla de acceso libre al sitio, no de "free of charge" del servicio NRT) | Coppola et al. 2020, p. 11 (v. 11), col. izq., último párrafo; Coppola 2023, p. 3 ("freely downloaded") | "The MIROVA website is freely accessible to observers" | "freely accessible on the web (Coppola et al., 2020, p. 11)" |
| 6.7 | sec6:40-41 | CONFIRMA | CORRECTO | Coppola 2023, p. 4 (v. 4), col. der., 1.er párrafo; Coppola 2025, p. 347 (v. 351), col. izq. | 2025: "supervising each image will be increasingly difficult and inconvenient" | |
| 6.8 | sec6:41-42 | SIN LOCALIZAR | CORRECTO (Coppola 2020 p. 11 habla del conocimiento de los observadores, no del operador) | | | |

---

## (a) Hallazgos propios

- **H1.** Coppola et al. 2020 (*Front. Earth Sci.* 7:362, doi 10.3389/feart.2019.00362) **está en el repo** como `documentacion\Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` (nombre sin autor ni DOI, patrón A89). El localizador lo dio por ausente en 4.26. Sirve para 4.10, 4.26, 4.27, 4.44, 5.17, 6.4 y 6.6.
- **H2.** Coppola 2014, p. 3410, describe la reflexión solar sobre nubes que sube el NTI. Apoya 6.2 y también sec5:30-33 (no revisada por el localizador). Ojo con sec5:30-33: dice que el MIR es "unusable by day", pero MIROVA procesa el día con umbrales propios (Tabla 1, columnas diurnas); la restricción nocturna es decisión nuestra.
- **H3.** Grilla: 50 × 50 km en 2016a (p. 183), en Coppola 2020 ("50 × 50 km (in UTM coordinates)", p. 3) y en Campus 2024 ("50×50 km UTM grid", p. 3); 51 × 51 en Campus 2022 (p. 7) y Coppola 2023 (p. 3). El grupo usa las dos cifras incluso para la misma grilla UTM.
- **H4.** Di Bella 2024, p. 7, Eq. 5, también da k_MODIS = 1.89 × 10⁷ y k_VIIRS750 = 1.11 × 10⁷, que coinciden con 18,9 × 10⁶ y 11 081 250 del repo. No es error del manuscrito, pero si se cita a Di Bella para descartar 2.48 × 10⁷ conviene saber que sus otros dos valores sí coinciden.
- **H5.** sec4:157: el título de Wooster et al. 2003 está truncado (falta ": derivation from the BIRD experimental satellite and comparison to MODIS fire products").
- **H6.** Fuera de encargo: el manuscrito contiene guiones largos (sec4:12, 62; sec5:71, 83; sec6:36-37, 93, 110, 117), contra la regla del dueño.

## (b) Convenciones de paginación, títulos y DOI

- **sp426.5.pdf, impresa = visor + 180: CONFIRMADA por deducción, no por folio.** Las páginas renderizadas no imprimen número (encabezados "ENHANCED VOLCANIC HOTSPOT DETECTION" / "D. COPPOLA ET AL."). La p. 1 da el volumen 426 y el DOI pero no el rango. El rango 181-205 lo vi en la lista de referencias de Campus 2024, p. 6 ("426:181-205"). Dos controles coherentes: el PDF tiene 25 páginas (181 a 205) y los encabezados alternan como recto/verso (v. 3, 5, 7, 9, 17 con "ENHANCED...", impares 183, 185...; v. 6, 8, 16 con "D. COPPOLA", pares).
- **Capítulo Coppola 2025: el archivo correcto es `978-3-031-86841-2.pdf` y la relación es impresa = visor − 4 (visor = impresa + 4).** La redacción del encargo ("impresa = visor + 4") está invertida; la tabla del localizador tiene el sentido correcto. Visto: v. 329 = p. 325 (título, DOI _11), v. 341 = p. 337, v. 346 = p. 342, v. 350 = p. 346, v. 351 = p. 347, v. 369 = p. 365 (capítulo de Sandri et al., DOI _12). `978-3-031-86841-2_9.pdf` es "Remote Monitoring of Volcanic Gases" de R. Campion, p. 261, DOI _9: **no** es el capítulo.
- Títulos y DOI que el localizador dio "sólo capa de texto", ahora vistos en imagen: Coppola 2014 (título, 35:9, 3403-3426, doi 10.1080/01431161.2014.903354), Laiolo 2026 (título, 88:11, doi 10.1007/s00445-025-01932-y), DOI del capítulo (_11), Wooster 2003 (doi:10.1016/S0034-4257(03)00070-1), Wright 2002 (PII S0034-4257(02)00030-5). Todos correctos.

## (c) VERIFICADO LIMPIO

Todas las filas marcadas CORRECTO en las tablas, con cita vista en imagen. En particular las que citan ecuación, tabla o coeficiente: Eqs 2-8 y Tabla 1 de 2016a; Eq. 17 y A_pix = 0.75 × 10⁶ m² del capítulo (p. 337); Eq. 1 de Campus 2022 (1.97 × 10⁷, 0.5625 km²); Eq. 3 y 18.0 µm sr de Campus 2024; Eq. 5 de Di Bella (2.48 × 10⁷); Eq. 5 de Aveni 2024 (5.67 × 10⁻⁸); Fig. 2 de Aveni 2025 (60.17); Fig. 3 de Wooster (19.68 ± 30 %); 79 % a 59 % de Coppola 2014.

## (d) Conteo por veredicto (82 filas verificadas)

| Veredicto | Filas |
|---|---|
| CORRECTO | 76 |
| LOCALIZADOR CORRIDO | 1 (4.2, párrafo de Campus 2024) |
| VEREDICTO ERRÓNEO | 3 (4.26 parte "SIN LOCALIZAR"; 6.2 fundamento; 6.6) |
| NO VERIFICABLE | 2 (4.11 y 4.32: la imagen de sp426.5 p. 184 y Campus 2022 p. 6 no llegó a verse) |
