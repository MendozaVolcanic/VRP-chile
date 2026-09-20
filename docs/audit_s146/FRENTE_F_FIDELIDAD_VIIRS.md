# Frente F (S146): la adaptación de MIROVA a VIIRS contra nuestro código VIIRS

> Auditoría de sólo lectura. No se modificó ningún archivo de `pipeline/`, `frontend/`, perfiles,
> `data/`, `tests/` ni docs preexistentes. Scripts propios en
> `experiments/_s146_auditoria/frente_F/`, páginas renderizadas en
> `experiments/_s146_auditoria/frente_F/paginas/`.
>
> **Regla de evidencia.** Lo que dice un paper sólo se da por bueno si la página fue renderizada a
> imagen con PyMuPDF (`get_pixmap`) y mirada. Las citas de texto extraído se usan para LOCALIZAR y van
> marcadas. Lo que hace el código se establece leyendo el archivo y trazando el llamador; el valor
> efectivo de cada bandera se leyó con
> `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.NOMBRE)"`, nunca del
> YAML. Lo no verificado va como SOSPECHA. SIN DATO no es FALLA ni OK.

---

## 1. Cobertura

### 1.1 Qué textos leí, y qué páginas vi como imagen

| Fuente | Qué es | Páginas vistas COMO IMAGEN (índice PDF base 0) | Páginas localizadas por texto extraído |
|---|---|---|---|
| **Campus et al. 2024**, Bull Volcanol 86:25, `documentacion/s00445-024-01721-z.pdf` | Vulcano, VIIRS I-band 375 m, "MIROVA-processed dataset". La única fuente MIROVA dedicada a 375 m | **1, 2, 3, 4, 5** (impresas 2 a 6), o sea todo el cuerpo | 0 y 6 (portada y referencias) |
| **Campus et al. 2022**, Sensors 22:1713, `documentacion/campus2022_sensors_22_1713.pdf` | "The transition from MODIS to VIIRS for global volcano thermal monitoring". La fuente de la adaptación a M-band 750 m | **5, 6** (impresas 6 y 7): Tabla 1 completa, §3.1, §3.2 con las Ecuaciones 1 y 2, §3.3 | las 24, mapeadas por un agente localizador |
| **Coppola et al. 2026**, Scientific Data (in press), `documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` | El archivo global OSF v2.5. Trae **la única tabla de parámetros POR SENSOR que existe** | **4, 5, 6, 7**: "Thermal anomaly detection", "Volcanic Radiative Power computation", "Data aggregation" y la Tabla 1 entera | 3, 8 a 15 (mapeadas por palabra clave) |
| **Tesis Massimetti**, `documentacion/THESIS_MASSIMETTI.pdf`, 204 pp | Tesis doctoral de Turín | ninguna (ver abajo) | las 204, mapeadas por un agente localizador |
| **Coppola 2025**, capítulo 11 "Thermal Monitoring of Volcanoes from Space", en `documentacion/978-3-031-86841-2.pdf`, páginas PDF 328 a 367 (impresas 325 a 364) | Capítulo de revisión. Trae **la tabla de saturaciones por sensor** y la ecuación general del VRP | **334, 339, 340, 352** (impresas 331, 336, 337, 349): Tabla 1, Tabla 2 con Eqs. 11 a 13, Eq. 17, y la sección 4.1.4 de falsas alertas | las 40 del capítulo, mapeadas por un agente localizador |
| **Aveni et al. 2024**, RSE 315:114388, `documentacion/Aveni_2024_TIRVolcH_RSE.pdf` | TIRVolcH | **0** (portada y resumen) | no aplica |

**Segundo hallazgo de cobertura**: el **capítulo Springer tampoco contiene el algoritmo de MIROVA**.
Es una revisión de la disciplina. No trae los Tests, ni el ETI, ni la regresión del NTI de fondo, ni la
grilla UTM, ni el radio del ROI, ni 0,003, ni 0,01, ni 5σ, ni 10σ, ni máscara de nube en Kelvin, ni
selección de cúmulo. Lo que sí aporta, y es citable, son cuatro cosas: la tabla de **saturaciones por
sensor**, la forma general del VRP con α y A_pix por sensor, el A_pix de la banda I, y la **tasa de
falsa alerta que MIROVA declara para sí misma**.

**Tercer hallazgo de cobertura**: **Aveni et al. 2024 no es la fuente de nuestro algoritmo**. Su título,
visto en la portada renderizada, es *"TIRVolcH: ... A single band TIR-based algorithm"*, y el resumen
dice *"an innovative and effective single band TIR-based (11.45 µm) algorithm"*. Lo que corre en
producción es MIR (`ENABLE_VRPTIR_AVENI = False`, `ENABLE_VRP_TIR_OUTPUT = False`). El docstring de
`process_viirs.py:23-24` afirma que el algoritmo está *"adapted from TIRVolcH (Aveni et al. 2024, RSE)"*,
y eso es falso para lo que se ejecuta. Ver F-10.

**Hallazgo de cobertura sobre Massimetti**: la **tesis de Massimetti no es una fuente
VIIRS**. Su título es *"Thermal remote sensing of volcanic activity by using Sentinel-2 and Landsat-8"*
y VIIRS aparece en 20 de 204 páginas, en todas salvo una como mención de paso. Toda su sustancia VIIRS
cabe en la página PDF 137 (impresa 130), que delega la adaptación a Campus et al. 2022. El "Thermal
Index" que recorre la tesis es el índice de reflectancias SWIR de Sentinel-2, **otro objeto distinto
del NTI**. Las siglas NTI y ETI no tienen definición ni ecuación en esa tesis. Quien la listó como
fuente de la adaptación a VIIRS en el encargo estaba trabajando con una creencia, no con el documento.

### 1.2 La estructura de autoridad que encontré (y que cambia cómo se lee todo lo demás)

Los tres textos VIIRS de MIROVA **no reexponen el detector**. Campus et al. 2022, §3.2, p. 7 (visto como
imagen), dice literal: *"The hot-spot detection algorithm is the same used for MODIS and based on
spectral indices and statistical thresholds"*, y remite a Coppola 2016a. Es decir:

- Para **umbrales de detección** (K1, C1, C2, N·σ) no existe fuente VIIRS. La única instrucción es
  "los mismos que MODIS". Copiarlos es lo que el texto manda; el problema no es copiarlos, es que
  **el mismo número no significa lo mismo a 375 m** (F-02).
- Para **geometría, área de píxel, coeficiente del VRP, bandas y agregación** sí hay fuente VIIRS
  explícita, y es específica por resolución.

### 1.3 Pasos del algoritmo cubiertos

Cubiertos con veredicto: bandas y longitudes de onda; saturación; conversión a radiancia; definición
del NTI; ETI y regresión; umbrales K1, C1, C2; extensión y forma del ROI; remuestreo; máscara de nube
y de no aptos; día contra noche; filtro cenital; fondo para la magnitud; coeficiente del VRP y área de
píxel; agregación de píxeles en cúmulo; clasificación por distancia; uso combinado de las bandas I y M;
piso de VRP por sensor.

**No cubiertos** (SIN DATO, declarados): el detalle interno de `compute_eti_scene_quadratic` contra la
regresión del paper (fuera de foco: es común a MODIS y no explica la brecha por sensor); la cadena
`fetch.py` de selección de gránulos; el capítulo Springer y Aveni 2024 (§1.4).

### 1.4 Lo que quedó pendiente en esta sesión

Anotado abajo en §6 como SIN DATO, con la ruta para cerrarlo.

---

## 2. La tabla, paso por paso

Convenciones: **IGUAL**, **DISTINTO**, **NO LO DICE** (el texto calla y nosotros elegimos algo: se dice
qué y de dónde salió), **SIN LOCALIZAR**. Los valores efectivos de banderas salen de `pipeline.profile`
con `VRP_PROFILE=mirova_equivalent`, no del YAML.

### 2.1 VIIRS I-band, 375 m (`pipeline/process_viirs.py`)

| # | Paso | Qué dice el texto de MIROVA (localizador) | Qué hace nuestro código (archivo:línea, valor efectivo) | Veredicto |
|---|---|---|---|---|
| 1 | Bandas y longitudes de onda | Campus 2024 p. 3, col. der., §Methodology: *"we use the two I-bands (namely I4 and I5), at 375-m resolution, acquiring in the MIR and TIR regions and centred at wavelengths of 3.74 and 11.45 µm"*. Coppola 2026 p. idx 4 y Tabla 1 (p. idx 7): I4 ~3.74 µm, I5 ~11.45 µm, 375 m | `process_viirs.py:80` `I04_LAMBDA = 3.740`; `:422` `{"I04": 3.740, "I05": 11.450}`; `:1114` y `:1166` pasan `lambda_tir_um=11.450` | **IGUAL** |
| 2 | Saturación de I4 e I5 | **Coppola 2025, cap. 11, Tabla 1, p. impresa 331 (PDF idx 334), vista como imagen**: fila VIIRS 375 m, `T_MAX` **MIR = 353 K**, **TIR = 343 K**. La nota al pie `**Fire Channel (Low-Gain MIR channel)` NO marca la fila de 375 m, o sea que la banda I no tiene canal de fuego. Coppola 2026 p. idx 4 lo dice en palabras: *"its lower saturation temperature makes it more susceptible to saturation"*; p. idx 6: *"single-gain design"* | `process_viirs.py:371-372` `BT_LUT_MAX = {"I04": 361.77, "I05": 423.33}`; `:396-401` el píxel al techo pasa a NaN. Los dos valores salen del techo de la LUT del VIIRS L1B User Guide | **DISTINTO**. MIROVA tiene número y es **353 K en I4** (nosotros 361,77) y **343 K en I5** (nosotros 423,33). Ver **F-12** |
| 3 | Conversión a radiancia | Coppola 2026 p. idx 5: *"The MIROVA system uses Level-1B top-of-atmosphere (TOA) radiance data for the entire workflow"*. No detalla si usa la radiancia del producto o la reconstruye desde la BT | Leemos **sólo la BT** por la LUT del producto (`:384-388`) y reconstruimos la radiancia con Planck monocromático en λ central (`:243-246`, `test1_integrated.py:48-60`). La radiancia del L1B, que está en el archivo, no se usa | **NO LO DICE** / SOSPECHA de sesgo pequeño: es un viaje de ida y vuelta por una transformación no lineal con longitud de onda efectiva. Ver F-08 |
| 4 | Definición del NTI | Coppola 2026 p. idx 4 nombra el NTI y el ETI pero no los define y remite a las refs. 4 y 6. **Ningún texto VIIRS da una versión del NTI para VIIRS** | `detection_context.py:625-687`: `NTI = (L_MIR − L_TIR)/(L_MIR + L_TIR)` con `L_TIR = Planck(11.45, BT_I05)` | **NO LO DICE** para VIIRS; la forma es la de MODIS, que es lo que Campus 2022 p. 7 manda ("same used for MODIS") |
| 5 | ETI y regresión de fondo | Coppola 2026 p. idx 4 nombra el ETI. Sin fórmula ni parámetros para VIIRS | `detection_context.py:699` `compute_eti_scene_quadratic`; `ENABLE_ETI_QUADRATIC_SCENE = False` (apagado). El ETI que corre es el `deti` del primer pase | **NO LO DICE** |
| 6 | Umbral K1 (piso absoluto del NTI) | SIN LOCALIZAR en texto VIIRS. El −0.8 nocturno es de Coppola 2016a (MODIS) | `NTI_K1_NIGHT = -0.8`; pero `ENABLE_NTI_RELATIVE_PATH = False` y `diag_n_nti_path` es 0 en 954 de 954 pasadas de la ventana de Fase 1 | **NO LO DICE**; sin efecto hoy |
| 7 | Umbrales C1 y C2 | **No existen para VIIRS en ningún texto MIROVA.** Campus 2022 p. 7 dice sólo "the same used for MODIS". Ninguna de las cuatro tablas de Campus 2022, ninguna de la tesis, ninguna de Coppola 2026 trae umbrales de detección | `DNTI_CONTEXTUAL_C1_SUMMIT = 0.003`, `..._SCENE = 0.01`, `C2_DNTI_SUMMIT_NIGHT = 5.0`, `..._SCENE = 10.0`, iguales a MODIS | **IGUAL a lo que el texto manda** (copiar MODIS), pero ver **F-02**: medido, C1 = 0.003 vale 0,43 σ en MODIS y 2,20 σ en VIIRS 375. El mismo número, cinco veces otra cosa |
| 8 | Extensión del ROI | Campus 2024 p. 3: *"an initial resampling of the original granule in a regular 50 × 50 km UTM grid"*. Coppola 2026 p. idx 4: *"the analysis was restricted to a 50 × 50 km subset, resampled onto a UTM grid centred on the summit coordinates provided by the Global Volcanism Program"* | `process_viirs.py:779` `roi_mask_bbox(..., radius_km)`; los 11 Tier A tienen `radius_km = 25` → caja de 50 × 50 km. Centro = `volcano_lat/lon` | **IGUAL** en extensión y forma de caja |
| 9 | **Remuestreo a grilla UTM** | Coppola 2026 p. idx 4, explícito y por sensor: *"resampled onto a UTM grid ... with sensor-dependent spatial resolution: 1000 m for MODIS, 750 m for VIIRS M-bands, and 375 m for VIIRS I-bands"*. Campus 2024 p. 3 lo repite para I-band | `ENABLE_UTM_REGRID = False`. La función existe y está escrita para esto (`process_viirs.py:488-550`, celda 0,375 km, medio lado 25,125 km) y **nunca se ejecuta** (`:735-736`) | **DISTINTO**. Ya catalogado como D17. **Los textos VIIRS lo SOSTIENEN con más fuerza que el de MODIS**, y en VIIRS el daño es mayor que en MODIS: ver **F-04** |
| 10 | Máscara de nube | Campus 2022 p. 8, §3.4: *"we have left the datasets 'as they are', that is without applying image inspections or filters that discard cloudy scenes"* (texto extraído, página no vista como imagen) | `CLOUD_MASK_BT_K = 0.0` → apagada | **IGUAL** |
| 11 | Filtros de "no aptos" 267/273 K y borde | Coppola 2016a §267-273 (MODIS). **Ningún texto VIIRS los menciona** | `ENABLE_UNSUITABLE_FILTERS_267_273 = True`; pisos `dNTI < −0.1` y `dETI < −0.1` y borde de matriz (`detection_context.py:60-61, 64-78`) | **NO LO DICE** para VIIRS. Ver F-09: el filtro de borde presupone una matriz remuestreada que aquí no existe |
| 12 | Día contra noche | Campus 2024 p. 5: *"2056 night-time VIIRS images were collected"*. Campus 2022 p. 6: *"We elaborated only the nigh time data"* (texto extraído) | `scripts/run_pipeline.py:116, 185-196, 446-448`: sólo noche por elevación solar. `ENABLE_DAYTIME_MODIS = False` | **IGUAL** |
| 13 | Filtro por ángulo cenital | Campus 2024 p. 4, col. der.: *"the data were not corrected atmospherically or filtered by a maximum value of zenith"*. (La tesis de Massimetti p. PDF 137 sí usa < 50°, pero es un filtro de estudio posterior, no del NRT) | No existe filtro cenital en ninguna parte del pipeline (comprobado por `grep zenith`: sólo alimenta el área de píxel, y esa rama está muerta) | **IGUAL** al canal NRT de Campus 2024 |
| 14 | Área de píxel | Campus 2024 p. 4, Eq. 3: *"where A_pix is the pixel size (140,625 m² for VIIRS I-bands)"*. Coppola 2026 Tabla 1: A_PIX = 1.4 × 10⁵ m² para 375 m. Fijo, sin corrección cenital | `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True`; `NADIR_PIXEL_AREA_M2 = 375² = 140.625` (`:67`); `scan_geometry.py:319` devuelve área uniforme | **IGUAL** (respalda A66/A67 con una fuente VIIRS, que hasta ahora no tenían) |
| 15 | Coeficiente del VRP | Campus 2024 p. 4: *"in the case of VIIRS I4 band has a value of 18.0 µm sr"*. Coppola 2026 Tabla 1: k_MIR = 18 para VIIRS 375 m | `WOOSTER_COEFF = 18.0` (`:77`). Producto efectivo 18,0 × 140.625 = 2.531.250, igual al de CLAUDE.md | **IGUAL**. Nota menor: el comentario de `:73` atribuye el 18.0 a *"Laiolo et al. 2024"*; el paper es **Campus** et al. 2024 (Laiolo es tercer autor). Ver F-10 |
| 16 | **Fondo para la magnitud** | Campus 2024 p. 3, Eq. 2 y su párrafo: *"At each alerted pixel, a background radiance value (L_pixbk ...) is also associated, this last computed from the arithmetic mean of the radiance of the pixels surrounding the alerted one(s)"*. Campus 2022 p. 7, Eq. 2: *"L_MIRbk is the background radiance, calculated as the arithmetic mean of pixels surrounding the active one/s"* | `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375 = False`. Hoy el fondo es el del anillo o el del kernel, no la media de los vecinos por píxel alertado | **DISTINTO**. Es D25, ya catalogada. **Los dos textos VIIRS la SOSTIENEN de forma literal y explícita**, y es la explicación directa del déficit de magnitud de A99 |
| 17 | **Agregación de píxeles** | Campus 2024 p. 3, Eq. 1: `L_MIRhot = Σ_{i=1}^{N_pix} L_alert`. Coppola 2026 p. idx 4: *"All resampled pixels exhibiting anomalous thermal behavior within this area were retained for VRP calculation"*; p. idx 5: *"pixel-level VRP values are subsequently summed ... Each record in the dataset therefore corresponds to the summed VRP of all alerted pixels"* | `ENABLE_SUM_VRP_REPORTING = False`. El dashboard publica `f5_core_vrp_mw` (el recorte del NÚCLEO del cúmulo, `pipeline/f5_core.py:61`), con `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True` y `FOCAL_CLUSTER_KEEP_PEAK = True` | **DISTINTO**, y es la divergencia más grande de esta tabla. Ver **F-05** |
| 18 | Clasificación por distancia | Campus 2024 p. 5 usa *"within a distance of 1 km radius from the La Fossa cone"* sólo para CONTAR alertas, no para clasificar. Coppola 2026 clasifica después, con DBSCAN, y **sobre el producto de archivo** (A105). Ningún texto VIIRS describe una clase summit/far en el NRT | `distance_class = "summit" if final_hotspot_dist_km <= inner_radius_km` (`process_viirs.py:1800-1801`), con `inner_radius_km` entre 3 y 20 km según el volcán | **NO LO DICE**. La geometría es nuestra (D18 ya catalogada) |
| 19 | Uso combinado de I y M | Coppola 2026 p. idx 6: *"For coincident VIIRS detections, the 750 m observation was retained because the higher-resolution I4 channel (375 m) is more prone to pixel saturation ... due to its single-gain design"* | No existe ninguna regla de preferencia entre sensores: los tres se publican en paralelo | **DISTINTO**, con la salvedad A105 de que es la agregación del archivo, no del NRT. Ver F-07 |
| 20 | Piso de VRP por sensor | Coppola 2026 Tabla 1, fila *Nighttime VRP threshold (W)*: MODIS 1,0 × 10⁵; VIIRS 750 m 5,0 × 10⁶; VIIRS 375 m 1,0 × 10⁴ | `MIN_VRP_MW_VIIRS375 = 0.0` (los tres en 0, quitados en S130) | **DISTINTO**, con salvedad A105. Medido: el piso de 0,01 MW sólo sacaría el 1,6 % de lo que publicamos en 375 m. Ver F-06 |
| 21 | **Test 1 integrado en el ROI** | **Ningún texto de MIROVA lo describe**, ni los de VIIRS ni los de MODIS que tengo. El propio código lo atribuye a Coppola et al. 2015, Bull Volcanol 77:55 §2.2 (`test1_integrated.py:17-18`), y **ese PDF no está en `documentacion/`** | `ENABLE_TEST1_PATH = True`, `TEST1_ROI_KM = 3.0`, `TEST1_K_SIGMA = 3.0`, `TEST1_MIR_RELATIVE = 0.02`. Llamado en `process_viirs.py:1128-1137` | **SIN LOCALIZAR** su fuente. Y ver **F-01**: su criterio dispara con ruido puro a 375 m por una razón puramente geométrica |

### 2.2 VIIRS M-band, 750 m (`pipeline/process_viirs_mod.py`)

Sólo las filas donde el veredicto difiere de 375 m.

| # | Paso | Texto de MIROVA (localizador) | Nuestro código | Veredicto |
|---|---|---|---|---|
| 1 | Bandas | Campus 2022 p. 6, §3.1 y Tabla 1 (vista como imagen): *"In this work we used M13 and M15 M-bands, covering respectively the MIR ... and TIR ... portion of the spectrum, with a 750 m spatial resolution"*, con los rangos de la Tabla 1: M13 de 3,973 a 4,128 µm y M15 de 10,263 a 11,263 µm. Coppola 2026 Tabla 1: M13 central ~4,04 µm | `M13_LAMBDA = 4.050`, `M15_LAMBDA = 10.763` (`process_viirs_mod.py:168-169`) | **IGUAL** (4,050 es el centro exacto del rango de Campus 2022; Coppola 2026 redondea a 4,04) |
| 2 | Saturación | Campus 2022 Tabla 1 (imagen): **M-13 = 634 K**, M-15 = **343 K**. Coppola 2025 cap. 11 Tabla 1 (imagen): M-13 = **634 K\*\*** (canal de fuego), M-15 = **340 K** | `BT_LUT_MAX_MBAND = {"M13": 634.0, "M15": 343.0}` (`:181`), píxeles al techo a NaN (`:184-191`) | **IGUAL** en M13. En M15 las dos fuentes MIROVA no coinciden entre sí (343 contra 340) y nosotros seguimos la de Campus 2022. Diferencia de 3 K, sin consecuencia práctica. Ver F-11 por el efecto colateral |
| 8 | Extensión del ROI | Campus 2022 p. 7, §3.2: *"Resampling is performed in a UTM 51 × 51 km grid, centered on the volcano summit (consistent with MODIS_MIROVA images)"*. Coppola 2026 p. idx 4 dice 50 × 50 km | caja de 50 × 50 km (`radius_km = 25`) | **IGUAL** salvo 1 km de discrepancia entre los dos textos de MIROVA. Ver §5, pregunta 2 |
| 9 | Remuestreo | Campus 2022 p. 7: *"by keeping the nominal resolution of 750 m. This results in matrices of 67 × 67 pixels rather than 51 × 51 pixels obtained from MODIS"* | `ENABLE_UTM_REGRID = False` | **DISTINTO** (D17). El texto es inequívoco: la matriz de trabajo es 67 × 67 |
| 14 | Área de píxel | Campus 2022 p. 7, Eq. 1: *"A_pix is the pixel surface in km² (equal to 0.5625 for VIIRS M-bands)"*. Coppola 2026 Tabla 1: 5,6 × 10⁵ m² | `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True`, nadir 562.500 m² | **IGUAL** |
| 15 | Coeficiente del VRP | Campus 2022 p. 7, Eq. 1: `VRP = ΔL_MIR · 1.97 × 10⁷ · A_pix`. Coppola 2026 Tabla 1: k_MIR = 19,7 | `WOOSTER_COEFF = 19.7` (`:66`); efectivo 19,7 × 562.500 = 11.081.250 = 1,97 × 10⁷ × 0,5625 km² | **IGUAL** |
| 16 | Fondo para la magnitud | Campus 2022 p. 7, Eq. 2 (vista como imagen) | `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False` | **DISTINTO** (D25) |
| 17 | Agregación | Campus 2022 p. 7 habla de *"the alerted pixel/s"* en plural indefinido, y para comparar con FIRMS dice *"for each satellite overpasses we aggregated the FRP of individual pixels"* (texto extraído). Coppola 2026 p. idx 5 lo dice sin ambigüedad: suma de todos los alertados | `ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750 = True`, se publica `primary_cluster.vrp_mw` | **DISTINTO** |
| 20 | Piso de VRP | Coppola 2026 Tabla 1: 5,0 × 10⁶ W nocturno para VIIRS 750 m | 0,0 | **DISTINTO**, pero el número del paper es sospechoso: ver F-06 |

---

## 3. Hallazgos

Gravedad de 1 a 5 medida en cuánto puede explicar de la sobre-publicación o de la magnitud en VIIRS.
El orden de exposición es el de descubrimiento; el orden de gravedad es este:

| gravedad | hallazgos |
|---|---|
| **5** | **F-01** Test 1 integrado, dispara con ruido y el umbral depende del tamaño de píxel |
| **4** | **F-03** fondo por vecinos (D25) literal en tres fuentes · **F-05** MIROVA suma todos los alertados, nosotros publicamos el núcleo |
| **3** | **F-02** C1 = 0,003 vale 0,43 σ en MODIS y 2,20 σ en VIIRS (riesgo de recall, no de sobre-publicación) · **F-04** sin remuestreo UTM (D17) · **F-06** pisos de VRP por sensor · **F-13** la vara que declara el propio grupo: ~5 % y ~1,8 % contra nuestro 86,3 % |
| **2** | **F-07** regla de preferencia entre I y M · **F-08** radiancia reconstruida desde la BT · **F-12** techo de saturación de la banda I |
| **1** | **F-09** filtro de borde sin remuestreo · **F-10** citas que no sostienen el camino · **F-11** descarte de M15 sobre 343 K · **F-14** trampa de lectura en la Eq. 17 del capítulo Springer |

Dos hipótesis mías quedaron **REFUTADAS por medición propia** dentro de la sesión (el número de
intentos en F-02 y la dependencia con el ángulo en F-04). Las dejo escritas con su refutación en vez de
borrarlas, porque la refutación es lo que deja a F-01 sin competencia.

---

### F-01 · El Test 1 integrado dispara con ruido puro, y el umbral al que lo hace depende del tamaño de píxel

**GRAVEDAD 5 · CONFIANZA ALTA** (derivación analítica + medición sobre 44.105 records)

**Qué pasa, en física primero.** El criterio absoluto del Test 1 integrado suma el exceso de radiancia
MIR de cada píxel del disco de 3 km alrededor del cráter contra el fondo de un anillo, y dispara si la
suma supera tres veces el desvío esperado (`pipeline/test1_integrated.py:420-437`):

```
delta_L = Σ sobre el ROI de  max(0, L − L_bg)
dispara si  delta_L > k_sigma · sigma_bg · raíz(N_ROI)
```

El recorte `max(0, ...)` tira la mitad negativa del ruido. Entonces, sobre una cumbre donde **no pasa
absolutamente nada**, el ruido puro no suma cero: la media de la mitad positiva de un ruido normal es
`sigma/raíz(2π) = 0,3989 sigma`. Así que, sin ninguna fuente de calor,

```
delta_L esperado = 0,3989 · sigma_bg · N_ROI
k observado      = 0,3989 · raíz(N_ROI)
```

El numerador crece como el número de píxeles y el umbral sólo como su raíz. El criterio deja de
preguntar si hay calor y pasa a preguntar **cuántos píxeles entran en el ROI**, o sea, qué sensor es.
Cruce con `k_sigma = 3`: `N_ROI > 56,5` píxeles.

Con `TEST1_ROI_KM = 3,0` km el disco mide 28,27 km², así que:

| sensor | A_píxel (km²) | N_ROI | k predicho sólo con ruido | ¿dispara con ruido? | **k mediano MEDIDO** | % `triggered_test1` medido |
|---|---|---|---|---|---|---|
| MODIS | 1,0000 | 28,3 | 2,12 | no | **1,94** | 12,6 % |
| VIIRS 750 m | 0,5625 | 50,3 | 2,83 | no, al filo | **2,42** | 27,1 % |
| VIIRS 375 m | 0,1406 | 201,1 | **5,66** | **SÍ** | **4,87** | **89,7 %** |

La predicción sale de una cuenta de una línea; los tres valores medidos salen del campo
`test1_k_observed` que el pipeline ya persiste, sobre todos los records de
`data/mirova_equivalent/` (n = 3.637 / 19.563 / 20.905, ventana 2025-02-15 a 2026-09-20).
Script: `experiments/_s146_auditoria/frente_F/test1_ruido_vs_resolucion.py`. Los medidos quedan un
poco por debajo de los predichos, que es exactamente lo que se espera si el ruido real está
espacialmente correlacionado y el número de píxeles independientes es algo menor que N_ROI.

El orden reproduce la brecha que motivó este frente: **12,6 / 27,1 / 89,7 %** contra
**11,4 / 21,4 / 86,3 %** de sobre-publicación. Y la Fase 1 ya había medido, por otro camino, que el
Test 1 sostiene el 57,8 % de lo publicado en negativos limpios de 375 m y que sin él la tasa cae de
86,3 % a entre 21,4 % y 36,5 %.

**Contra el texto.** Ningún texto de MIROVA describe este detector, ni para MODIS ni para VIIRS. El
código lo atribuye a Coppola et al. 2015, Bull Volcanol 77:55 §2.2, y ese PDF **no está en
`documentacion/`** (busqué por año, por revista, por volumen y por título: SIN LOCALIZAR). Aunque
existiera y dijera esto, estaría calibrado para MODIS, donde N_ROI ≈ 28 y el criterio se porta bien.
Portarlo sin tocar a 375 m, donde N_ROI ≈ 201, lo convierte en un detector de ruido. Es el caso puro
de "el texto de VIIRS no lo dice y nosotros seguimos a MODIS", agravado porque el parámetro que
importa (el tamaño de píxel) es justamente lo que cambia entre sensores.

**Cómo se ve en el dashboard.** Una detección de cumbre, clase summit, de unas décimas de MW, casi
todas las noches, en volcanes donde MIROVA no publica nada. El campo
`final_hotspot_source = 'test1_roi'` la delata. Ejemplo verificado en esta sesión, último record
VIIRS 375 de Villarrica (`data/mirova_equivalent/Villarrica.json`, 2026-09-20 06:24):
`test1_k_observed = 5,25` (el ruido puro predice 5,66), `nti_max = −0,9602` (el índice espectral en el
piso, o sea ninguna firma de material caliente, A78/A80), y aun así se publica 0,059 MW como summit.

#### F-01b · Prueba independiente: el valor de reposo baja cuando el satélite mira de costado

La fórmula no sólo predice tres números: predice que **k tiene que bajar al alejarse del nadir**.
Cuando VIIRS mira de costado el píxel crece (el ATBD de geolocalización, 423-ATBD-002 Tabla 2.2-1,
citado en `scan_geometry.py:210-214`, da 0,144 km² en nadir y 0,631 km² en el borde, factor 4,38), así
que caben menos píxeles en el disco de 3 km, así que `k = 0,3989·raíz(N_ROI)` baja por un factor
raíz(4,38) = 2,09. **Ninguna otra explicación de la sobre-publicación predice esto**: si k midiera
calor, no tendría por qué depender del ángulo con que el satélite mira el mismo volcán la misma noche.

Medido (`experiments/_s146_auditoria/frente_F/f01_prueba_por_angulo.py`), mediana de
`test1_k_observed` por tramo de `sensor_zenith_deg`:

| sensor | 0-15° | 15-30° | 30-42° | 42-52° | 52-62° | 62-90° | caída |
|---|---|---|---|---|---|---|---|
| MODIS | 1,94 | 1,93 | 1,87 | n<30 | n<30 | n<30 | 1,04× |
| VIIRS 750 m | 2,75 | 2,58 | 2,39 | 2,23 | 2,34 | 1,92 | 1,43× |
| VIIRS 375 m | **5,82** | 5,46 | 5,09 | 4,59 | 4,74 | **3,66** | **1,59×** |

Dos cosas. Primero, **en el nadir los tres valores medidos coinciden con los tres predichos**: 5,82
contra 5,66; 2,75 contra 2,83; 1,94 contra 2,12. Una sola fórmula de una línea, tres sensores, error
menor al 10 % en los tres. Segundo, **la caída con el ángulo está y tiene el signo predicho**, con un
tamaño (1,59× en 375 m) algo menor que el 2,09× del borde extremo, que es lo esperable porque el
último tramo mezcla ángulos y no llega al extremo del barrido. En MODIS el brazo de palanca es corto
(no hay pasadas nuestras por encima de 42°) y sale plano, como corresponde.

**Esto también explica el resultado de F-04b** (abajo): la tasa de publicación de VIIRS 375 cae de
82,3 % cerca del nadir a 62,9 % de costado. No es que de costado se vea peor: es que de costado
entran menos píxeles al disco y el detector de ruido deja de alcanzar su umbral.

**Qué más se puede medir sin tocar el pipeline.** (a) Correlacionar `test1_k_observed` con `nti_max`
por sensor: si F-01 es cierto, en 375 m no debe haber correlación, porque el disparo no viene del
calor. (b) Contar qué fracción de lo publicado en 375 m tiene `triggered_test1 = True` y
`nti_max < −0,95` a la vez.

**Nota de honestidad.** Que el criterio dispare con ruido no prueba que TODO lo que dispara sea ruido.
En una cumbre con lava el mismo criterio también dispara, y por la razón buena. Lo que el cálculo
prueba es que en 375 m el criterio **ya no distingue**: su valor de reposo está por encima de su propio
umbral. Es un instrumento cuya aguja está clavada.

---

### F-02 · El piso absoluto C1 = 0,003 vale 0,43 σ en MODIS y 2,20 σ en VIIRS 375: el mismo número, otra cosa

**GRAVEDAD 3 · CONFIANZA ALTA** (medición sobre 57.642 records). **Ojo al signo**: medido, esto es
riesgo de RECALL en VIIRS, no causa de sobre-publicación. Ver el subapartado de refutación.

**El fenómeno.** El paso contextual (Tests 2 y 3) compara cada píxel con la media de sus ocho vecinos
en el índice espectral, y lo marca si el salto supera **o** un piso absoluto C1 **o** la estadística
`μ + C2·σ`. Como es un "o", manda el más bajo de los dos. Coppola 2016a fijó C1 = 0,003 mirando
escenas MODIS de 1 km. El desvío del salto entre vecinos depende de cuánto se parecen dos píxeles
contiguos, y eso depende del tamaño del píxel: a 1 km dos vecinos sobre terreno quebrado son objetos
muy distintos; a 375 m se parecen mucho más.

Medido sobre `diag_sd_dnti`, que el pipeline persiste
(`experiments/_s146_auditoria/frente_F/c1_vs_sigma_por_sensor.py`):

| sensor | n | σ_dNTI mediano | C1 summit (0,003) en σ | C1 scene (0,010) en σ | % de records donde manda C1 summit |
|---|---|---|---|---|---|
| MODIS | 12.169 | 0,006970 | **0,43 σ** | 1,43 σ | 100,0 % |
| VIIRS 750 m | 23.869 | 0,001644 | **1,83 σ** | 6,08 σ | 99,9 % |
| VIIRS 375 m | 21.604 | 0,001367 | **2,20 σ** | 7,32 σ | 99,9 % |

El piso absoluto gobierna la decisión en prácticamente todos los records de los tres sensores, o sea
que la rama estadística del "o" (μ + C2·σ) **no decide casi nunca**: es letra muerta. Eso, de paso,
refina D26 y la conclusión de S136 sobre la conectiva, y encaja con lo que S142 midió (C1 = 0,003 como
umbral efectivo en los 70 casos).

**Contra el texto.** Campus 2022 p. 7 manda copiar el detector de MODIS, y eso hicimos. Pero ningún
texto de MIROVA dice que C1 sea el mismo número para los tres sensores, porque ningún texto de MIROVA
publica C1 para ningún sensor. La única tabla por sensor que existe (Coppola 2026, Tabla 1) trae
bandas, resolución, área, k_MIR y pisos de VRP, **y no trae umbrales de detección**. O sea: la fuente
que sí se tomó el trabajo de separar por sensor cada parámetro que cambia con la resolución, no
publica el que más cambia con la resolución.

**Dirección del efecto, y acá me equivoqué de hipótesis y la medición me corrigió.** En unidades de σ,
MODIS es el LAXO (0,43 σ) y VIIRS 375 el ESTRICTO (2,20 σ). Mi primera explicación fue que el número de
intentos compensa: en la caja de 50 × 50 km hay unos 2.500 píxeles MODIS y unos 17.800 de 375 m, y con
siete veces más intentos un umbral más estricto puede producir más cruces. **Lo medí y es falso.**

`experiments/_s146_auditoria/frente_F/cierre_f02_f04.py`, tasa de píxeles marcados por el primer pase
sobre los píxeles efectivamente evaluados (`diag_n_first_pass_pixels / diag_n_bg_used_first_pass`):

| sensor | n records | tasa mediana | tasa media |
|---|---|---|---|
| MODIS | 12.175 | **0,035303** | 0,051645 |
| VIIRS 750 m | 23.869 | **0,000000** | 0,000090 |
| VIIRS 375 m | 21.613 | **0,000000** | 0,000108 |

MODIS marca el 3,5 % de los píxeles que evalúa; los dos VIIRS marcan, en la mediana, **ninguno**, y en
promedio uno de cada diez mil. El camino contextual en VIIRS es **quinientas veces más selectivo** que
en MODIS, no más laxo. La hipótesis del número de intentos queda **REFUTADA** con dato propio.

**Qué queda entonces de F-02, y es lo contrario de lo que parecía.** El desajuste de C1 es real y está
documentado, pero su signo es de **riesgo de recall, no de sobre-publicación**: en VIIRS el piso
heredado de MODIS está 2,2 σ arriba y el camino contextual casi no dispara. Y el corolario es que
**F-02 no compite con F-01: lo refuerza**, porque descarta al otro candidato y deja al Test 1 integrado
como la única explicación en pie de la sobre-publicación en VIIRS, que es justo lo que la Fase 1 midió
por su lado (57,8 % de T1_SOLO en 375 m, y la tasa cayendo de 86,3 % a 21,4-36,5 % sin él).

**Cómo se ve en el dashboard**: no se ve. Es el hallazgo invisible: un camino de detección que casi
nunca dispara en el sensor de mayor resolución. **Qué medir para cerrarlo**: si alguna vez se toca el
Test 1, hay que mirar el recall del camino contextual en VIIRS antes y después, porque hoy ese camino
no está sosteniendo casi nada y no puede absorber lo que el Test 1 deje de detectar.

---

### F-03 · Los dos textos VIIRS dicen literalmente que el fondo de la magnitud es la media de los vecinos del píxel alertado, y lo tenemos apagado

**GRAVEDAD 4 · CONFIANZA ALTA** (dos citas verbatim vistas como imagen)

D25 ya está catalogada y sus banderas existen apagadas desde S142/S145. Lo que este frente aporta es
que **las dos fuentes VIIRS lo dicen de forma explícita y con la misma palabra**, "arithmetic mean of
pixels surrounding":

- Campus et al. 2024, p. 3, col. der., párrafo bajo la Eq. 1: *"At each alerted pixel, a background
  radiance value (L_pixbk ...) is also associated, this last computed from the arithmetic mean of the
  radiance of the pixels surrounding the alerted one(s)."* Y la Eq. 2 lo suma: `L_MIRbk = Σ L_pixbk`.
- Campus et al. 2022, p. 7, bajo la Eq. 2: *"L_MIRbk is the background radiance, calculated as the
  arithmetic mean of pixels surrounding the active one/s."*

Las dos páginas están vistas como imagen. Es fondo **por píxel alertado**, calculado **con sus
vecinos**, no el fondo del anillo regional. Nuestro `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` y
`..._VIIRS750` están los dos en `False`.

Eso conecta con A99 (magnitud ~0,7; el déficit está en que MIROVA suma vecinos tibios que nosotros no
sumamos) y con lo que S145 midió: factor 3,2 de punta a punta en VIIRS 750. El fondo de un anillo
regional es más frío que la media de los ocho vecinos de un píxel caliente, y un fondo más frío da un
exceso **mayor**, no menor. Que nuestro déficit sea de magnitud y no de exceso indica que el efecto
neto viene del otro término, el conteo de píxeles. **Lo dejo así, sin resolver**: el A/B de S143 ya
dio NO ADOPTAR para D25 y no voy a reabrirlo desde acá. El aporte del frente es sólo que el respaldo
documental de D25 en VIIRS es **más fuerte** de lo que el catálogo refleja, porque es literal en las
dos fuentes VIIRS y no una extrapolación desde MODIS.

**Salvedad que encontré y que hay que anotar**: el propio Campus 2024 se contradice. La Tabla 1 de la
p. 4 describe la columna `L_MIRbk` como *"Radiance in MIR channel of the background, **measured in the
Vulcanello area**"*, o sea un píxel fijo de referencia fuera del volcán, no la media de los vecinos. Un
texto, dos definiciones distintas del mismo símbolo, en páginas contiguas. Va a §5 como pregunta 1.

---

### F-04 · No remuestrear a UTM (D17) castiga a VIIRS por tres mecanismos que MODIS no tiene, pero medido no es lo que manda

**GRAVEDAD 3 · CONFIANZA ALTA en las citas, hipótesis del tamaño REFUTADA por medición propia**

La cita más fuerte y más reciente está vista como imagen, Coppola et al. 2026, p. idx 4: *"the analysis
was restricted to a 50 × 50 km subset, resampled onto a UTM grid centred on the summit coordinates ...
with sensor-dependent spatial resolution: 1000 m for MODIS, 750 m for VIIRS M-bands, and 375 m for
VIIRS I-bands"*. Campus 2022 p. 7 lo dice para M-band con el resultado concreto (*"matrices of 67 × 67
pixels"*) y Campus 2024 p. 3 para I-band. Nuestro `ENABLE_UTM_REGRID = False`.

Por qué en VIIRS duele más que en MODIS, y son tres mecanismos distintos, ninguno presente en MODIS:

1. **Borrado de bow-tie.** VIIRS descarta píxeles duplicados en los bordes de cada barrido. El código
   los pasa a NaN (`process_viirs.py:83`, `FLAG_DNS` incluye 65533 `Bowtie_Deleted`, y `:390-391`).
   En la grilla del gránulo eso deja **franjas de NaN**. El kernel de ocho vecinos ignora los NaN y
   promedia con los que queden (`detection_context.py:182-189`): junto a una franja, el "fondo" de un
   píxel se calcula con tres o cinco vecinos en vez de ocho, así que es más ruidoso, así que cruza
   C1 más seguido. MODIS no tiene bow-tie deletion.
2. **Agregación en tres zonas.** VIIRS cambia el tamaño de píxel en **saltos discretos** a lo largo del
   barrido (agrega 1, 2 o 3 muestras). En los dos bordes de zona, dos píxeles contiguos del arreglo
   son objetos de tamaño distinto: el salto entre vecinos tiene una componente geométrica que no es
   térmica. MODIS crece de forma suave.
3. **Anisotropía.** Fuera del nadir el píxel se estira en el eje del barrido y no en el otro, así que
   los ocho vecinos no están a la misma distancia física del centro. A 51° de cenit, que es la mediana
   medida de nuestras pasadas VIIRS (`sensor_zenith_deg` mediano 48,7° en 375 m y 48,6° en 750 m,
   contra 44,2° en MODIS), el estiramiento ya es apreciable.

Remuestrear a una grilla UTM regular elimina los tres de un golpe, y es exactamente lo que MIROVA hace
antes de detectar. Nosotros corremos el kernel sobre el gránulo crudo.

#### F-04b · Lo medí, y el efecto va al revés: el mecanismo existe pero no manda

Si el bow-tie y la anisotropía pesaran, la tasa de publicación en VIIRS tendría que **crecer con el
ángulo cenital**, porque lejos del nadir hay más franjas borradas y más estiramiento. Medido
(`cierre_f02_f04.py`, proxy de publicación `distance_class == summit` y magnitud > 0, sobre todos los
records; es un proxy, no el predicado del dashboard, y el universo no está restringido a negativos
limpios, así que sirve para la TENDENCIA y no para el nivel):

| sensor | 0-20° | 20-35° | 35-45° | 45-55° | 55-90° |
|---|---|---|---|---|---|
| MODIS | 17,6 % | 13,2 % | 8,7 % | 8,3 % | 8,1 % |
| VIIRS 750 m | 37,5 % | 29,0 % | 27,6 % | 23,5 % | 16,4 % |
| VIIRS 375 m | 82,3 % | 79,8 % | 79,4 % | 74,3 % | 62,9 % |

**Baja de forma monótona en los tres.** La hipótesis queda **REFUTADA como explicación dominante**:
D17 sigue siendo una divergencia real y bien documentada, pero su daño en VIIRS no se manifiesta como
un exceso que crezca con el ángulo. **Le bajo la gravedad de 4 a 3.**

Y la bajada tiene dueño: es **la firma de F-01**. Lejos del nadir el píxel VIIRS crece, caben menos
píxeles en el disco de 3 km del Test 1, y su valor de reposo `0,3989·raíz(N_ROI)` baja. Medido en
F-01b: en 375 m la mediana de `test1_k_observed` cae de 5,82 cerca del nadir a 3,66 de costado, y la
tasa de publicación cae con ella. Los dos números bajan juntos porque son el mismo fenómeno.

---

### F-05 · MIROVA suma TODOS los píxeles alertados de la pasada; nosotros publicamos el núcleo de un cúmulo

**GRAVEDAD 4 · CONFIANZA ALTA** (tres citas verbatim, dos vistas como imagen)

- Campus 2024 p. 3, Eq. 1 (imagen): `L_MIRhot = Σ_{i=1}^{N_pix} L_alert`.
- Coppola 2026 p. idx 4 (imagen): *"All resampled pixels exhibiting anomalous thermal behavior within
  this area were retained for VRP calculation."*
- Coppola 2026 p. idx 5 (imagen): *"pixel-level VRP values are subsequently summed to obtain a single
  VRP value representing the radiative power of the entire thermal anomaly for that overpass. Each
  record in the dataset therefore corresponds to the summed VRP of all alerted pixels."*

No hay agrupamiento, ni conectividad, ni selección de un cúmulo primario, ni recorte al entorno del
píxel pico, en ninguno de los textos VIIRS. "Dentro de esta área" es la caja de 50 × 50 km entera.
Campus 2022 p. 7 lo confirma de refilón cuando, para poder comparar contra FIRMS, dice que agregó el
FRP de los píxeles individuales *"to be consistent with the VRP measured by the MIROVA system"*.

Nuestro camino publicado es otro: `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True`,
`FOCAL_CLUSTER_KEEP_PEAK = True`, y el dashboard de 375 m publica `f5_core_vrp_mw`, que es el recorte
del núcleo del cúmulo (`pipeline/f5_core.py:61`). `ENABLE_SUM_VRP_REPORTING = False`.

**Esto contradice de frente la premisa de A10**, que dice que `pc.vrp_mw` "es lo que MIROVA reporta".
Ningún texto VIIRS lo respalda; los tres dicen lo contrario. Puede que el NRT de MIROVA haga algo
distinto de su propio archivo, y por eso esto va también a §5 como pregunta 3. Pero mientras no haya
un texto que lo diga, **A10 es una creencia sin respaldo citable** en lo que toca a VIIRS, y por A111
la salida honesta es SIN EVIDENCIA, no "cerrado".

**Cómo se ve en el dashboard**: magnitudes sistemáticamente por debajo de MIROVA en pasadas con más de
un píxel caliente, que es exactamente el déficit ~0,7 de A99 y su explicación medida ("a igual conteo
la razón es 0,995"). **Cómo medirlo**: para las pasadas con referencia de MIROVA, comparar la suma de
`vrp_mw` sobre todos los `anomaly_pixels` del record contra `f5_core_vrp_mw` y contra el valor de
MIROVA. Ese primer número es el predicado del paper y ya está persistido.

---

### F-06 · Coppola 2026 publica pisos de VRP por sensor; el de VIIRS 750 m no puede ser el del NRT

**GRAVEDAD 3 · CONFIANZA ALTA en la cita, ALTA en la medición, y la conclusión es NO ADOPTAR**

Tabla 1 de Coppola et al. 2026 (p. idx 7, vista como imagen), fila *Nighttime VRP threshold (W)*:
MODIS 1,0 × 10⁵ W (0,1 MW), VIIRS 750 m **5,0 × 10⁶ W (5 MW)**, VIIRS 375 m 1,0 × 10⁴ W (0,01 MW).
Nuestros tres pisos están en 0,0 (quitados en S130).

Medido (`experiments/_s146_auditoria/frente_F/umbral_vrp_tabla1_scidata.py`, ventana 2026-09-01 a
2026-09-20, proxy de publicación `distance_class == summit` y magnitud > 0, que es una cota y no el
predicado exacto del dashboard):

| sensor | piso del paper | proxy publicadas | sobreviven | % |
|---|---|---|---|---|
| MODIS | 0,1 MW | 54 | 54 | 100,0 % |
| VIIRS 750 m | 5,0 MW | 207 | **0** | **0,0 %** |
| VIIRS 375 m | 0,01 MW | 833 | 820 | 98,4 % |

Dos lecturas, las dos útiles:

1. **El piso de 375 m no es la palanca.** Aplicarlo sacaría el 1,6 % de lo que publicamos. Cierra una
   vía tentadora antes de que alguien la abra.
2. **El de 750 m borra el 100 %, incluidos los verdaderos positivos.** Eso no puede ser el
   comportamiento del NRT: MIROVA publica alertas de VIIRS 750 m muy por debajo de 5 MW en volcanes
   chilenos, y está en el CSV que usamos como referencia. La secuencia 1,0 × 10⁵ / 5,0 × 10⁶ / 1,0 × 10⁴
   además no es monótona con la resolución de ninguna manera sensata. **Sospecho una errata del paper**
   (¿5,0 × 10⁴?), y va a §5 como pregunta 4.

Y la salvedad que manda A105: la Tabla 1 es del producto de archivo OSF v2.5, que es filtrado, no del
canal NRT que clonamos. El número mide el tamaño de un efecto, no una obligación.

---

### F-07 · MIROVA tiene una regla de preferencia entre I-band y M-band; nosotros publicamos las dos en paralelo

**GRAVEDAD 2 · CONFIANZA ALTA en la cita, con salvedad A105**

Coppola 2026, p. idx 6 (imagen): *"For coincident VIIRS detections, the 750 m observation was retained
because the higher-resolution I4 channel (375 m) is more prone to pixel saturation over intense thermal
sources, due to its single-gain design."* Las detecciones de 375 m sin su par de 750 m se conservan, y
viceversa; cuando coinciden, **manda la de 750 m**.

Nosotros no tenemos ninguna regla así: los tres sensores escriben records independientes y el dashboard
muestra los tres. Como 375 m es justo el sensor que sobre-publica y 750 m el que menos, una regla de
preferencia como esa **reduciría la sobre-publicación de las pasadas coincidentes sin tocar ningún
umbral**. Cuántas son, no lo medí: SIN DATO.

Salvedad A105: es la regla de agregación del archivo, no necesariamente la del NRT. Y es lo que explica
por qué el CSV de referencia puede traer una sola fila donde nosotros tenemos dos: si el cruce contra
MIROVA no lo contempla, parte de la "sobre-publicación" de 375 m podría ser esto. **Cómo medirlo**:
contar las noches donde nuestro 375 m y nuestro 750 m publican dentro de la misma media hora, y ver
cuántas de esas tiene MIROVA con una sola fila y de qué resolución.

---

### F-08 · Reconstruimos la radiancia desde la temperatura de brillo pudiendo leerla del archivo

**GRAVEDAD 2 · CONFIANZA MEDIA · efecto no medido**

El L1B de VIIRS trae la radiancia observada. Nosotros leemos sólo la temperatura de brillo por la LUT
del producto (`process_viirs.py:384-388`) y después reconstruimos la radiancia con Planck a una sola
longitud de onda (`:243-246`, y `test1_integrated.py:48-60`). La BT del producto salió de la radiancia
pasando por la **función de respuesta espectral completa de la banda**; volver de la BT a la radiancia
con una λ central es un viaje de ida y vuelta por una transformación no lineal que no cierra.

En el NTI el error se cancela en parte, porque es un cociente y las dos bandas se desvían en el mismo
sentido. En el VRP no se cancela: `ΔL` entra lineal. Coppola 2026 p. idx 5 dice que k_MIR *"is derived
by integrating Planck radiance over the sensor spectral response"*, o sea que el coeficiente 18,0
está pensado para la radiancia **de banda**, no para la monocromática. Si las dos difieren, el 18,0
está aplicado a un número que no es el que lo calibró.

No lo medí. **Cómo medirlo**: SIN DATO desde los records persistidos, porque no guardamos la radiancia
del L1B. Requiere abrir un gránulo, que es lectura pura y no toca el pipeline.

---

### F-12 · MIROVA sí publica el techo de saturación de la banda I, y es 353 K: el nuestro está 9 K arriba, y 80 K arriba en el TIR

**GRAVEDAD 2 · CONFIANZA ALTA** (tabla vista como imagen) · afecta la magnitud en eventos fuertes

Coppola 2025, capítulo 11, **Tabla 1, p. impresa 331 (PDF idx 334), vista como imagen**, fila
VIIRS / Suomi NPP-JPSS-1 / 375 m: `T_MAX` **MIR = 353 K**, `T_MAX` **TIR = 343 K**. La nota al pie
`**Fire Channel (Low-Gain MIR channel)` marca las filas de MODIS MIR (500 K) y de VIIRS 750 m MIR
(634 K), y **no marca la fila de 375 m**: la banda I no tiene canal de fuego, y por eso satura bajo.

Nuestros techos son otros (`process_viirs.py:372`): `I04 = 361,77 K` y `I05 = 423,33 K`, los dos
tomados del tope de la LUT del VIIRS L1B User Guide.

**Lo incómodo es que el propio código ya sabe que eso está mal.** En la banda M, el comentario de
`process_viirs_mod.py:178-180` razona exactamente al revés y con razón: *"El VIIRS L1B UserGuide da
374,6 K para la LUT de M15: ese es el techo del contenedor, no el del detector, y por eso no
contradice al 343,0 operacional"*. El argumento es correcto y por eso en M-band se usa el valor de
MIROVA. En la banda I nunca se aplicó el mismo argumento, y quedó el techo del contenedor. Es una
inconsistencia interna, no una decisión.

**Qué produce.** Los píxeles de I04 entre 353 y 361,77 K entran hoy al cálculo como medición buena,
cuando MIROVA los considera saturados. Son **los más calientes de la escena**, así que su ΔL pesa
mucho: es el mecanismo de F28, inflación de magnitud en el evento fuerte. En I05 el margen es de 80 K.
No es una causa de sobre-publicación (un píxel saturado es un píxel muy caliente, y esas noches
MIROVA también alerta): es una causa de magnitud equivocada hacia arriba, y sólo cuando pasa algo.

**Cómo medirlo sin tocar el pipeline**: contar records de 375 m con `t_max_i04_k` entre 353 y 362, y
ver qué fracción de ellos son parte de una alerta publicada por MIROVA. Es un `grep` sobre los JSON.

---

### F-13 · El propio grupo MIROVA declara una tasa de falsa alerta de ~5 %, y TIRVolcH de ~1,8 % en VIIRS 375: nosotros estamos en 86,3 %

**GRAVEDAD 3 · CONFIANZA ALTA** (dos citas vistas como imagen) · no es un defecto de código, es la vara

No es un hallazgo de fidelidad línea por línea: es el número contra el cual se mide todo este frente, y
sale de la boca de los autores.

- Coppola 2025, cap. 11, §4.1.4 "False Alerts", p. impresa 349 (PDF idx 352), visto como imagen:
  *"Similar percentages were also obtained for MIROVA (~5%; Coppola et al. 2016)"*, en una comparación
  donde VAST da ~21 %, MODVOLC ~3 % y RST ~6 %.
- Aveni et al. 2024, resumen de la portada (imagen): TIRVolcH, sobre VIIRS **375 m**, detecta anomalías
  *"as low as 0.5 K above the background, while maintaining a false positive rate of ~1.8 %"*.

Es decir: el algoritmo más sensible que el grupo publicó para VIIRS 375 m declara 1,8 % de falsas
alertas. Nosotros publicamos en el **86,3 %** de las pasadas de 375 m donde MIROVA miró y no vio nada.
La distancia no es de calibración fina, es de dos órdenes de magnitud, y eso descarta por sí solo que
la brecha se cierre moviendo un umbral. Encaja con F-01: un detector cuyo valor de reposo está por
encima de su umbral no se arregla corriendo el umbral un poco.

Dos salvedades honestas. El ~5 % de MIROVA es de Coppola 2016 y es MODIS. Y su definición de "falsa
alerta" no es la nuestra: ellos cuentan alertas no volcánicas, nosotros contamos pasadas donde
publicamos y su consolidado no. No son el mismo denominador (A90). Como orden de magnitud, igual manda.

---

### F-14 · Trampa de lectura: la ecuación 17 del capítulo Springer imprime un área de píxel de VIIRS 750 m que es un tercio más grande de lo que corresponde

**GRAVEDAD 1 · CONFIANZA ALTA** · aviso para que nadie lo adopte

Coppola 2025, cap. 11, p. impresa 337 (PDF idx 340), vista como imagen, párrafo bajo la Eq. 17:
*"in the case of VIIRS ..., 750 m resolution bands at λ_MIR = 4.050 µm, the parameters become,
A_pix = 0.75 × 10⁶ m² and α = 2.88 × 10⁻¹⁹"*.

Pero 750 m × 750 m = **0,5625 × 10⁶ m²**, no 0,75 × 10⁶. Parece que se escribió el lado lineal (0,75 km)
con la unidad del área. Las otras dos fuentes MIROVA son coherentes entre sí y con nosotros: Campus
2022 p. 7 (*"0.5625 for VIIRS M-bands"*) y Coppola 2026 Tabla 1 (5,6 × 10⁵ m²). **Nuestro código está
bien y el capítulo está mal**, en un factor 1,33. Lo anoto porque una sesión futura que llegue primero
a este capítulo tiene cómo equivocarse en un 33 % de magnitud creyendo que se alinea con el paper.

En la misma página, la Eq. 17 parametriza el VRP con `σε/(α ε_MIR)` en vez del `k_MIR` de Wooster. Los
valores 1,97 × 10⁷, 18,9 y 18,0 **no aparecen** en el capítulo: la correspondencia entre las dos formas
existe pero no la comprobé numéricamente (SIN DATO, y sin consecuencia, porque las otras dos fuentes dan
los `k` directamente y coinciden con el código).

---

### F-09 · El filtro de borde de matriz presupone un remuestreo que no hacemos

**GRAVEDAD 1 · CONFIANZA ALTA**

`detection_context.py:64-78` marca como no apto el borde de un píxel del arreglo, citando a Coppola
2016a: *"all the pixels at the edge of the resampled matrices are considered unsuitable"*. La razón
física es que en el borde de la matriz de 51 × 51 el kernel de ocho vecinos no tiene vecinos. Pero
nosotros **no remuestreamos** (F-04), así que el arreglo es el gránulo entero y su borde queda a cientos
de kilómetros del volcán: el filtro no marca nada útil, y los píxeles del borde real del ROI (que sí
tienen vecinos, porque el gránulo sigue) no se marcan. Es inocuo hoy, pero si D17 se cierra el filtro
empieza a morder y hay que revisarlo junto.

---

### F-10 · El código atribuye a Laiolo un coeficiente que es de Campus

**GRAVEDAD 1 · CONFIANZA ALTA**

`process_viirs.py:73-74` dice *"For VIIRS I4 ... use 18.0 per Laiolo et al. 2024 (s00445-024-01721-z,
Vulcano VIIRS 375m)"*. El DOI es correcto y el valor es correcto, pero el paper es **Campus** et al.
2024; Laiolo es el tercer autor. Y el docstring del módulo (`:23-24`) presenta el algoritmo como
*"adapted from TIRVolcH (Aveni et al. 2024, RSE)"*, cuando TIRVolcH es un detector de banda TIR única y
lo que corre en producción es MIR. Lo mismo la ficha SDA de la cabecera (`:9-10`). No cambia ningún
número, pero es exactamente el patrón que el encargo advierte: caminos en producción citando papeles
que no los sostienen. Corregir comentarios no es tarea de auditoría; queda anotado.

---

### F-11 · Descartar M15 por encima de 343 K puede borrar el píxel más caliente, no sólo el saturado

**GRAVEDAD 1 · CONFIANZA MEDIA · afecta recall, no sobre-publicación**

`process_viirs_mod.py:181-191` pone a NaN toda BT de M15 mayor o igual a 342,5 K, citando bien la
Tabla 1 de Campus 2022 (`T_MAX` de M-15 = 343 K, verificado como imagen). El razonamiento del comentario
es correcto: un píxel saturado no es un píxel caliente. El efecto colateral es que en una colada activa
el M15 del píxel central es justo el que pasa de 343 K, y al ponerlo en NaN **el NTI de ese píxel deja
de existir**, así que el píxel más caliente de la escena desaparece de la detección. Ningún texto de
MIROVA dice qué hacer con el saturado (lo único parecido es Coppola 2026 p. idx 4 para MODIS: *"MODIS
band 22 ... is replaced by band 21 when saturation occurs"*, o sea que MIROVA **sustituye**, no
descarta). No lo medí. **Cómo medirlo**: contar records de 750 m con `t_max_i05_k` cerca del techo, o
con `t_max_k` alto y NTI ausente.

---

## 4. Lo que el frente dice sobre las divergencias ya catalogadas

El encargo pide no contarlas como nuevas, pero sí decir si un texto de VIIRS las sostiene o las
contradice.

| divergencia | ¿la sostiene un texto VIIRS? | localizador |
|---|---|---|
| **D17** (sin remuestreo UTM) | **La SOSTIENE, con la cita más explícita y más reciente que existe, y por sensor** | Coppola 2026 p. idx 4; Campus 2022 p. 7; Campus 2024 p. 3. (El capítulo Springer no lo menciona: cero ocurrencias de UTM, "resampl" y "grid" en sus 40 páginas) |
| **D25** (fondo por vecinos) | **La SOSTIENE de forma literal en TRES fuentes**, dos de ellas VIIRS | Campus 2024 p. 3 (bajo Eq. 1); Campus 2022 p. 7 (bajo Eq. 2); **Coppola 2025 cap. 11 p. 336** (imagen): *"L_bk and T_bk are the pixel-integrated radiance and temperature of the background (generally calculated from pixel(s) surrounding the anomaly)"* |
| **D18** (ROI1 caja 5 × 5 contra círculo per-volcán) | Ningún texto VIIRS menciona un ROI interno. Ni lo sostiene ni lo contradice | SIN LOCALIZAR |
| **D19** (`keep_peak`) | **La CONTRADICE en CUATRO fuentes**: todas dicen suma de todos los alertados, ninguna menciona cúmulos, conectividad ni recorte al pico | Coppola 2026 p. idx 4 y 5; Campus 2024 Eq. 1; **Coppola 2025 cap. 11 p. 336 Eq. 13** (imagen): *"the total excess radiance ΔL_tot(λ), sourced by the whole VTF, is calculated as the sum of the excess radiance of all the hotspot-contaminated pixels"*, con `N_pix` definido como *"the number of alerted pixels in each scene"* |
| Umbral K1 del NTI (−0,8 noche, −0,6 día) | **Lo SOSTIENE**, y con una fuente de 2025, aunque atribuido a MODIS | Coppola 2025 cap. 11, **Tabla 2, p. impresa 336** (imagen): fila NTI, `Threshold Nighttime −0.8 / Daytime −0.6`, columna Satellite `Terra(MODIS) / Aqua(MODIS)`, referencia Wright et al. 2002. Coincide con `NTI_K1_NIGHT = -0.8` y `NTI_K1_DAY = -0.6` |
| **D21** (banda primaria en MODIS) | Fuera del frente, pero Coppola 2026 p. idx 4 lo dice para MODIS: *"MODIS band 22 provides greater sensitivity to weaker thermal anomalies but is replaced by band 21 when saturation occurs"*. **Sostiene D21** con una fuente de 2026, no sólo con el paper de 2016 | Coppola 2026 p. idx 4 |
| **D22** (compuerta `bt > t_bg + 3 K`) | Ningún texto VIIRS la menciona ni la excluye. Sigue siendo lo que S137 estableció contra el paper de MODIS | SIN LOCALIZAR |
| **Test 1 integrado** | **Ningún texto de MIROVA lo describe**, y el paper que el código cita no está en `documentacion/` | SIN LOCALIZAR |
| Área nadir fija (A66/A67) | **La SOSTIENE con fuente VIIRS**, que hasta ahora no tenía | Campus 2024 p. 4 (140.625 m²); Campus 2022 p. 7 (0,5625 km²); Coppola 2026 Tabla 1 |

---

## 5. Preguntas que sólo el autor puede responder (para el correo a Coppola)

1. **El fondo de la magnitud en VIIRS 375 m.** Campus et al. 2024 define `L_MIRbk` de dos maneras
   distintas en páginas contiguas: el párrafo bajo la Eq. 1 (p. 3) dice *"the arithmetic mean of the
   radiance of the pixels surrounding the alerted one(s)"*, y la Tabla 1 (p. 4) dice *"measured in the
   Vulcanello area"*, que es un sitio fijo fuera del volcán. ¿Cuál corresponde al NRT? Y si es la media
   de los vecinos: ¿cuántos vecinos, en qué radio, y se excluyen del fondo los píxeles que también
   fueron alertados?

2. **La extensión del recorte.** Campus et al. 2022 (p. 7) dice 51 × 51 km; Campus et al. 2024 (p. 3) y
   Coppola et al. 2026 dicen 50 × 50 km. ¿Cuál es el valor operativo, y la grilla es de 67 × 67 en
   VIIRS 750 m y de 134 × 134 en 375 m?

3. **Qué se informa como VRP de la pasada en el NRT.** Coppola et al. 2026 es inequívoco para el
   archivo: la suma de todos los píxeles alertados de los 50 × 50 km. ¿Es lo mismo en el NRT
   per-volcán de mirovaweb, o ahí se informa un subconjunto (el cúmulo del cráter)? Es la pregunta que
   decide si nuestra magnitud está mal por construcción.

4. **El piso de VRP nocturno de VIIRS 750 m.** La Tabla 1 de Coppola et al. 2026 da 5,0 × 10⁶ W, que es
   cincuenta veces el de MODIS y quinientas veces el de VIIRS 375 m. Aplicado a nuestros datos borra el
   100 % de las detecciones de 750 m, incluidas las que coinciden con alertas publicadas por MIROVA.
   ¿Es 5,0 × 10⁶ o hay una errata?

5. **Los umbrales de detección en VIIRS.** Campus et al. 2022 (p. 7) dice que el detector es *"the same
   used for MODIS"*. ¿Eso incluye los valores numéricos de C1 y C2 de la Tabla 1 de Coppola et al.
   2016a sin recalibrar, aunque el desvío del contraste entre vecinos cambie por un factor de cinco
   entre 1 km y 375 m? ¿Se rehizo alguna calibración de C1 para VIIRS?

6. **El píxel saturado.** Para MODIS, Coppola et al. 2026 dice que la banda 22 se reemplaza por la 21.
   Para VIIRS I4, que es de ganancia única, ¿qué se hace con el píxel saturado: se descarta, se clampea
   al techo, o se sustituye por M13?

7. **El Test 1 integrado en el ROI.** ¿Existe en MIROVA un criterio de detección que integre el exceso
   de radiancia MIR sobre todo un disco alrededor del cráter y lo compare contra N·σ del fondo, además
   de los tests por píxel? Si existe, ¿con qué radio y con qué N, y se reajusta por resolución?

---

## 6. Lo que quedó SIN DATO, y cómo cerrarlo

Cerrados dentro de esta misma sesión, y dos de ellos refutando mi propia hipótesis:

| era pendiente | resultado |
|---|---|
| Capítulo Springer de Coppola 2025 | **CERRADO**: localizado (PDF 328-367), cuatro páginas vistas como imagen. No contiene el algoritmo de MIROVA; aporta F-12, F-13, F-14 y tres refuerzos de la §4 |
| Aveni et al. 2024 (TIRVolcH) | **CERRADO**: es un algoritmo de banda TIR única, no es la fuente de nuestro camino MIR. Alimenta F-10 y F-13 |
| Cuenta del número de intentos (F-02) | **CERRADO y REFUTADO**: el camino contextual en VIIRS marca ~1 de cada 10.000 píxeles evaluados contra 3,5 % en MODIS. No es la causa |
| Tamaño del efecto de F-04 | **CERRADO y REFUTADO**: la tasa BAJA con el ángulo cenital en los tres sensores. D17 baja de gravedad 4 a 3, y la bajada resulta ser la firma de F-01 |

Quedan abiertos, declarados:

| pendiente | por qué importa | cómo cerrarlo |
|---|---|---|
| **Coppola et al. 2015, Bull Volcanol 77:55** | Es la **única** fuente que el código alega para el Test 1 integrado, el detector que este frente identifica como causa principal, y **no está en `documentacion/`** (busqué por año, revista, volumen y título) | conseguirlo. Hasta entonces el Test 1 queda SIN LOCALIZAR, y el hallazgo F-01 se sostiene igual, porque la cuenta del ruido no depende de qué diga ese paper |
| Equivalencia entre `k_MIR` y la forma `σε/(α ε_MIR)` de la Eq. 17 | Curiosidad de consistencia; sin consecuencia, porque las otras dos fuentes dan los `k` directos y coinciden | cuenta de unidades sobre la Eq. 17 |
| Radiancia de banda contra Planck monocromático (F-08) | Sesgo pequeño y sistemático en la magnitud | abrir un gránulo y comparar; es lectura pura, no toca el pipeline |
| Cuántas pasadas tienen 375 m y 750 m coincidentes (F-07) | Dice cuánto rendiría la regla de preferencia de MIROVA | cruce por volcán y media hora sobre los JSON |

---

## 7. VERIFICADO LIMPIO

Pasos donde el código VIIRS hace exactamente lo que el texto de MIROVA dice, comprobado contra la
página renderizada y contra el valor efectivo de la bandera:

1. **Bandas y longitudes de onda**, los cuatro canales, en los dos sensores.
2. **Área de píxel nadir fija**: 140.625 m² en I-band y 562.500 m² en M-band, sin corrección cenital.
3. **Coeficiente del VRP**: 18,0 en 375 m y 19,7 en 750 m, con el producto efectivo idéntico al de las
   ecuaciones de los papeles.
4. **Forma de la ecuación del VRP**: `A_pix · k_MIR · (L_MIR − L_bg)`.
5. **Extensión del recorte**: caja de 50 × 50 km centrada en la cumbre.
6. **Sólo noche.**
7. **Sin filtro por ángulo cenital** y **sin máscara de nube**, que es lo que el canal NRT de MIROVA
   declara explícitamente.
8. **Techo de saturación de la banda M13**: 634 K, confirmado en dos fuentes MIROVA independientes
   (Campus 2022 Tabla 1 y Coppola 2025 cap. 11 Tabla 1), las dos vistas como imagen.
9. **Umbral K1 del NTI**: −0,8 de noche y −0,6 de día, exactamente los valores de la Tabla 2 del
   capítulo Springer (aunque hoy ese camino no decide nada, porque `ENABLE_NTI_RELATIVE_PATH = False`).
10. **Forma del NTI**: índice normalizado `(MIR − TIR)/(MIR + TIR)`, que es la Eq. 9 del capítulo.

Y una advertencia final de método. Tres de los catorce hallazgos de este frente aparecieron **porque
la medición contradijo lo que yo acababa de escribir**: la hipótesis del número de intentos (F-02), la
del ángulo cenital (F-04) y la atribución del 18,0 a Laiolo (F-10). Ninguna se habría caído sin correr
el script. Y el hallazgo principal, F-01, no salió de leer un paper: salió de mirar una fórmula del
código y preguntarle **cuánto vale cuando no pasa nada**. Esa pregunta no se la había hecho nadie en
146 sesiones, y la respuesta estaba en un campo que el pipeline ya venía persistiendo.
