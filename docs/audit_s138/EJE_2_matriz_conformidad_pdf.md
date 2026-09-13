# EJE 2 (S138): matriz de conformidad construida DESDE el PDF de Coppola et al. 2016 (SP 426.5)

Auditor: agente Eje 2, sesion S138, 2026-09-13. Repo en `main` limpio (HEAD `6b1dd91ef`).
Fuente primaria: `documentacion/sp426.5.pdf`, 25 paginas, leido con PyMuPDF
(`experiments/_s138_audit/eje2/sp426_5_pymupdf.txt` es el volcado pagina a pagina).
Regla de trabajo: la seccion 1 se escribio ANTES de abrir cualquier documento del proyecto; la
seccion 5.D (cruce con el catalogo) se hizo al final. Las paginas citadas son las del PDF (1 a 25).
Flags: todos los valores "efectivo" salen de `VRP_PROFILE=mirova_equivalent python -c "import
pipeline.profile as p; ..."` (volcado completo en
`experiments/_s138_audit/eje2/profile_efectivo_mirova_equivalent.txt`, 139 constantes), nunca del YAML.
Parametros por volcan: `volcanoes.yaml` leido con `yaml.safe_load` para los 11 `mirova_monitored`, e
inyectados por `scripts/run_pipeline.py:234-247` (MODIS), `:277-292` (I-band), `:324-338` (M-band):
`inner_radius_km`, `local_kernel_bg`, `lbg_global_compatible`, `max_cluster_pixels`, `radius_km=25`,
y el ancla `get_detection_anchor()` (`pipeline/geo_utils.py:53`: el vent gana).

Scripts propios de esta sesion (solo escriben en su carpeta):
- `experiments/_s138_audit/eje2/01_controles_sinteticos_detection_context.py` (salida `01_..._resultado.json`)
- `experiments/_s138_audit/eje2/02_records_operacionales_extras.py` (salida `02_..._resultado.json`)

## 1. Los pasos del algoritmo tal como los describe el paper (PASO A)

El paper organiza el procesamiento en cinco bloques (p. 3: "(i) data extraction; (ii) cropping and
resampling; (iii) definition of regions of interest (ROIs); (iv) hotspot detection; and, lastly, (v)
calculation of the excess MIR radiance and radiative power"). Desglosados en pasos auditables:

| # | Paso | Pag. | Cita corta (PyMuPDF) |
|---|---|---|---|
| P01 | Extraccion de fecha/hora, geometria de vista (cenit, acimut), geolocalizacion y DN de 7 bandas: R1, R2, L6 (solo dia), L21, L22, L31, L32 | 3 | "the digital number (DN) related to seven spectral bands of interest" |
| P02 | Filtro de DN invalidos: se elimina por banda todo pixel con DN > 32768, salvo DN = 65533 (saturado), que se conserva | 3 | "eliminating, for each band, all the pixels with DN > 32 768 ... with the exception of the pixels with DN = 65 533, indicating saturated values" |
| P03 | Remocion del bow tie (solape scan a scan en el borde del swath) | 3 | "scanned in order to remove the bow-tie effect that produces the so-called scan to scan overlapping" |
| P04 | Conversion DN a radiancia con scale y offset del L1B | 3 | "we used the conversion coefficients for each selected band (scale and offset)" |
| P05 | Banda MIR compuesta L21ok: L22 (alta ganancia) por defecto, L21 (baja ganancia) donde la 22 satura | 3 | "band L21ok, by using the L21 or L22 radiance, depending on band 22 saturation (or not), respectively" |
| P06 | Recorte y remuestreo a grilla equiespaciada de 1 km, 50 x 50 km, centrada en la cumbre GVP; motivacion: area de pixel homogenea (hasta ~10 km2 a 55 grados) y escala homogenea para la deteccion | 3 | "cropped and resampled (into an equally spaced 1 km grid) ... within a grid (50 x 50 km) centred on the volcano's summit"; "Global Volcanism Program volcano database ... for the summit latitude and longitude" |
| P07 | ROI1: caja de 5 x 5 km centrada en la cumbre. ROI2: el resto de los 50 x 50 km. Umbrales distintos por ROI | 3-4 | "inner region (ROI1) consists of a box (5 x 5 km) centred on the volcano's summit"; "ROI2 ... includes the whole scene with the exception of the ROI1" |
| P08 | NTI = (L_MIR - L_TIR)/(L_MIR + L_TIR) con L_MIR = L21ok y **L_TIR = L32 (12.02 um)** | 4 | "LMIR is the radiance recorded by the MIR channel (L21ok) and LTIR is the radiance of the TIR channel (L32)" |
| P09 | NTIapp: T_app = BT del canal TIR (L32); L_MIR,app = Planck_MIR(T_app); NTIapp = (L_MIR,app - L_TIR)/(L_MIR,app + L_TIR) | 5 | "Tapp = BTTIR"; "LMIR,app = PMIR(Tapp)" (Eq. 2 y 3) |
| P10 | Regresion cuadratica NTI vs NTIapp por imagen: NTIbk = a NTIapp^2 + b NTIapp + c, coeficientes nuevos en cada imagen | 5 | "A quadratic best-fit regression ... parameters a, b and c are obtained for each case ... from each single image" (Eq. 4/5) |
| P11 | ETI = NTI - NTIbk | 5 | "obtained by subtracting the background NTIbk (equation 4) from the observed NTI (equation 1)" |
| P12 | dNTI y dETI: a cada pixel se le resta la media aritmetica de sus 8 vecinos; no se excluyen nubes ni tipo de superficie | 5 | "subtracting from its value (NTI or ETI) the average (arithmetic mean) of the eight neighbouring pixels"; "the presence of clouds is not taken into account" |
| P13 | Pixeles no aptos: todos los del borde de la matriz, y todos con dNTI o dETI < -0.1 | 5 | "all the pixels at the edge of the resampled matrices; all the pixels with dNTI or dETI < -0.1" |
| P14 | Test 1: NTI_pix > K1, K1 igual en ambas ROI, distinto dia/noche (Tabla 1: -0.8 noche, -0.6 dia). Los pixeles activos por Test 1 se **retiran** de los pasos siguientes (quedan fuera del pool de mu/sigma) | 6 | "Pixels that satisfy Test 1 are flagged as active and subsequently discarded (unsuitable) for further steps" |
| P15 | Test 2 (dNTI) **y** Test 3 (dETI), ambos a la vez; cada uno es (X > C1) **o** (X > mu + C2 sigma); mu y sigma sobre TODOS los pixeles aptos de la imagen | 7 | "must be satisfied at the same time for each pixel"; "dNTI_PIX > C1 or dNTI_PIX > mu_dNTI + C2 sigma_dNTI (Test 2) and dETI_PIX > C1 or dETI_PIX > mu_dETI + C2 sigma_dETI (Test 3)"; "mu and sigma are the arithmetic mean and standard deviation of all the suitable pixels within the image" |
| P16 | Tabla 1: noche ROI1 C1 = 0.003, C2 = 5; noche ROI2 C1 = 0.01, C2 = 10; dia ambas ROI C1 = 0.02, C2 = 15 | 7 | Tabla 1 |
| P17 | Los pixeles activos por Tests 2 y 3 se eliminan del analisis posterior | 7 | "pixels flagged as active by means of tests 2 and 3 are subsequently eliminated from further analysis" |
| P18 | Segunda corrida: solo si hubo detecciones; se repite el filtro espacial (paso P12) **excluyendo los pixeles activos** ya detectados y se reaplican los Tests 2 y 3 a las nuevas matrices dNTI/dETI | 7-8 | "step 2 (spatial analysis) is performed a second time, being particularly careful to eliminate all of the active pixels already detected. Hence, the previous step (contextual threshold: tests 2 and 3) are applied again" |
| P19 | Ninguna etapa discrimina nubes: se detectan outliers estadisticos de la escena, no tipos de superficie | 8 | "we are not interested in discriminating cloudy pixels, but only in detecting pixels were two indexes are anomalously high" |
| P20 | Exceso de radiancia: dL4_pix = L4_alert - L4_bk, con L4_bk = media aritmetica de los pixeles que rodean al pixel activo (o al cumulo activo) | 8 | "L4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)" |
| P21 | RP_pix = 18.9 x A_pix x dL4_pix, A_pix = 1 km2 (pixel remuestreado) | 8-9 | Eq. 7; "APIX is the pixel size (1 km2 for the resampled MODIS pixels)" |
| P22 | RP total = suma de RP_pix de todos los pixeles alertados ("n alert"), sin distinguir ROI | 9 | Eq. 8; "the total radiative power is calculated as being the sum of the single RPPIX" |
| P23 | Nubes y datos de mala calidad se descartan **a posteriori por inspeccion visual**, no por el algoritmo; la serie se entrega "as they are" | 8, 17 | "a visual inspection of the images allows ... cloud-affected data to be discarded (a posteriori)"; "the RP time series obtained by MIROVA are provided as they are" |
| P24 | Los mismos parametros de Tabla 1, la misma grilla y las mismas ROI se exportan a otros volcanes sin calibracion historica | 9 | "may also be applied to other volcanoes ... (by using the same spatial grid and ROIs)" |

Lo que el paper NO contiene y conviene dejar escrito para que nadie lo herede como "canonico":
(a) ninguna condicion de temperatura de brillo (BT) en ningun test; (b) ningun radio de exclusion,
mascara de nube, piso de VRP ni tope de magnitud; (c) ningun filtro solo-noche (el algoritmo corre de dia
con otra Tabla 1); (d) la banda TIR del NTI es la 32, no la 31; (e) el fondo del VRP es una media de los
vecinos del pixel o del cumulo, no el anillo de la escena; (f) la deteccion no usa la posicion del pixel
salvo para elegir la columna de Tabla 1 (ROI1 vs ROI2).

## 2. Matriz paso a paso: que hace el codigo en cada sensor (PASO B)

Abreviaturas: PM = `pipeline/process_modis.py`, PV = `pipeline/process_viirs.py` (I-band 375 m),
PVM = `pipeline/process_viirs_mod.py` (M-band 750 m), DC = `pipeline/detection_context.py`,
SG = `pipeline/scan_geometry.py`. Veredictos: **C** conforme, **Cp** conforme con adicion que el paper
no tiene, **D** divergente, **A** ausente, **n/a** el paper es de MODIS y el paso no tiene equivalente
literal en VIIRS (adaptacion fuera de este paper). Columna "efectivo" = valor leido de `pipeline.profile`.

| Paso | MODIS | VIIRS375 | VIIRS750 | Flag y valor efectivo | Veredicto M / V375 / V750 |
|---|---|---|---|---|---|
| P01 bandas | Lee B21, B22 y **B31** (PM:75-76 `BAND31_IDX=10`, 11.03 um; PM:253-255). No lee B32. R1/R2/L6 no aplican (solo noche) | I04 + I05 (PV:338-405) | M13 + M15 (PVM:207-297) | sin flag | **D** (B31 en vez de B32) / n/a / n/a |
| P02 DN invalidos y saturados | `rad[dn > 32767] = NaN` (PM:244-250): **elimina tambien el 65533 saturado** que el paper conserva. Encima, guard BT > 500 K a NaN (PM:555) | Saturado via bit 2 de `quality_flags` y techo LUT a NaN (PV:361-378) | idem + techos 634/343 K (PVM:176-190) | `ENABLE_BT_SAT_SECONDARY_GUARD=True`, `BT_SAT_MIR_K_MODIS=500.0` | **D** / n/a (esquema distinto, pero el saturado tambien se borra) / n/a |
| P03 bow tie | Ningun tratamiento; el granule se usa tal cual (PM:499-506). El unico camino que lo aborda, `_regrid_modis_granule` (PM:396-462), esta detras de `ENABLE_UTM_REGRID` | Bow tie borrado a bordo: DN 65533 `Bowtie_Deleted` a NaN (PV:81, 371) | idem (PVM:66) | `ENABLE_UTM_REGRID=False` (se lee de `thresholds:`, `profile.py:606`) | **A** / C (por producto) / C (por producto) |
| P04 DN a radiancia | scale/offset del L1B (PM:246-248) | LUT de BT del producto (PV:365-367) | LUT (PVM:227-230) | sin flag | **C** / C / C |
| P05 L21ok (B22 manda) | `merge_mir_bands(rad21, rad22, ENABLE_MODIS_B22_PRIMARY)` (PM:317-333, 544-547): con el flag OFF manda la **B21** y la 22 solo rellena NaN de la 21 | no aplica (una sola banda MIR) | no aplica | `ENABLE_MODIS_B22_PRIMARY=False` (clave top-level o `paths:`, `profile.py:358`) | **D** / n/a / n/a |
| P06 recorte + remuestreo 1 km, 50x50 km, centro GVP | Caja 50x50 km si (`roi_mask_bbox`, PM:532, SG:158, `radius_km=25` en los 11); **sin remuestreo**: cada pixel conserva su tamano real y se le asigna area fija 1 km2 (PM:508-510, SG:132-149). Centro de la caja = `lat/lon` del YAML; el ROI1 y las distancias se centran en el **vent** (PM:512-516, 527-530): dos centros (PCC 7.6 km entre ambos) | igual, caja 50 km, celda nativa 375 m sin remuestreo, area 140 625 m2 fija (PV:716-723, 751) | igual, 750 m, 562 500 m2 (PVM:459-466, 488) | `ENABLE_UTM_REGRID=False`; `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS=True`, `..._VIIRS=True`; `ENABLE_GEOLOCATED_PIXEL_AREA=False` | **A** (remuestreo) / A / A |
| P07 ROI1 caja 5x5 km | Circulo de radio `inner_radius_km` (3 a 20 km segun volcan) centrado en el vent, `roi1_summit_mask` (DC:287-313); la caja del paper existe pero solo con flag (PM:527-530) | idem (PV:741-744) | idem (PVM:479-482) | `ENABLE_ROI1_BOX_PAPER=False`, `ROI1_BOX_HALF_KM=2.5` | **D** / D / D |
| P08 NTI con L32 | `nti = (L21 - L31)/(L21 + L31)` (PM:562-563) con B21 primaria y **B31** | (I04 - I05)/(I04 + I05) a 11.45 um (PV:829-834) | (M13 - M15)/(M13 + M15) a 10.763 um (PVM:504-508) | sin flag | **D** (banda TIR y banda MIR distintas) / n/a / n/a |
| P09 NTIapp | `compute_nti_and_nti_app(rad_mir, bt31, 3.929, 11.03)` (DC:606-676; PM:850-855) | (PV:1225-1230) | (PVM:807-812) | sin flag (corre dentro del primer pase) | **C** / C / C |
| P10 regresion cuadratica por imagen | `compute_eti_scene_quadratic` (DC:680-775): `np.polyfit` orden 2 sobre los pixeles aptos de la caja, **mas un refit iterativo** (hasta 3 vueltas, descarta residuos > 3 sigma; DC:685-688, 745-765) que el paper no describe | idem | idem | sin flag para el refit | **Cp** / Cp / Cp |
| P11 ETI | `eti = nti - polyval(coeffs, nti_app)` (DC:769-771) | idem | idem | sin flag | **C** / C / C |
| P12 dNTI/dETI 8 vecinos, media aritmetica | `_nanmean_8neighbors_fast` (DC:162-190), media ignorando NaN (el paper usa los 8 porque ya no hay invalidos) | idem | idem | sin flag | **C** / C / C |
| P13 no aptos (borde, < -0.1) | Primer pase: `build_unsuitable_mask` (DC:81-140) excluye borde y dNTI/dETI < -0.1 del pool (PM:864-865, 884-885). El "borde" es el del granule entero, no el de una matriz de 51x51 que no existe. **Segundo pase**: pool = `~active & finito`, sin borde ni pisos (DC:904) | idem (PV:1235-1236, DC:904) | idem (PVM:827-828) | `ENABLE_UNSUITABLE_FILTERS_267_273=True` | **Cp** primer pase / **A** segundo pase (los tres) |
| P14 Test 1 (NTI > K1) activa y retira | `nti_path_hot = nti > -0.8 AND bt > t_bg + 3 K` (PM:660-666) se calcula, entra al `combine_hot_paths` (PM:824) y **acto seguido `hot_mask_2d = fp_hot` lo pisa** (PM:888): los pixeles K1 no son activos salvo que pasen ademas los Tests 2 y 3. Tampoco se retiran del pool: `test1_mask=None` (PM:857-859) | igual (PV:971-976, 1188, 1259; `_test1_mask_for_fp` PV:1231-1233) | igual (PVM:619-624, 783, 851, 823-825) | `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False`, `ENABLE_TEST1_K1_BG_EXCLUDE=False` | **D** / D / D (dos caras: no activa, no retira) |
| P15 Tests 2 y 3, OR interno, AND entre ambos, mu/sigma de la imagen | `first_pass_tests_2_and_3` (DC:399-544): `combinar = min` = la formula del paper (DC:510); AND (DC:529-532); mu/sigma sobre pool apto de la caja (DC:477-493). **Extra**: `& (bt > t_bg + bt_sanity_k)` (DC:532) | idem (PV:1237-1259) | idem (PVM:829-851) | `ENABLE_FIRST_PASS_TESTS_2_AND_3=True`, `ENABLE_TESTS_23_PROSE_BRANCH=False`, `NTI_BT_SANITY_K=3.0` | **Cp** / Cp / Cp (la adicion es D22) |
| P16 Tabla 1 | Noche: `DNTI_CONTEXTUAL_C1_SUMMIT=0.003`, `_SCENE=0.010`, `C2_*_SUMMIT_NIGHT=5`, `C2_*_SCENE_NIGHT=10`, `NTI_K1_NIGHT=-0.8` (PM:866-887). Dia: valores existen (`_select_thresholds` PM:355-378) pero **nunca se usan**: `ENABLE_DAYTIME_MODIS=False`, `run_pipeline.py:185-195` salta las pasadas diurnas y `store.py:171-182` las rechaza | noche igual; dia no existe | noche igual; dia no existe | `ENABLE_DAYTIME_MODIS=False`, `ENABLE_DUAL_ROI_FIRST_PASS=True` | **C** noche / **A** dia (los tres) |
| P17 activos eliminados del analisis posterior | `second_pass_adjacent` los pone a NaN en la media de vecinos y los excluye del pool (DC:898-904) | idem | idem | (parte de P18) | **C** / C / C |
| P18 segunda corrida | `second_pass_adjacent(active_mask=hot_mask_2d, conditioned=False)` (PM:919-951; DC:803-948). Con `conditioned=False`: corre **aunque el primer pase este vacio** (DC:887), **sin restringirse a la vecindad** de lo activo (DC:946), **sin la compuerta BT** ni los filtros de no-aptos (DC:904, 938-940). Recompone el hot mask entero (PM:951) | idem (PV:1284-1317) | idem (PVM:876-909) | `ENABLE_SECOND_PASS_ADJACENT=True`, `ENABLE_SECOND_PASS_CONDITIONED=False`, `ENABLE_DUAL_ROI_SECOND_PASS=True` | **D** / D / D |
| P19 sin discriminar nubes | `bg_cloud_free = ... & (bt_mir > CLOUD_MASK_BT_K)` con 0.0 = sin efecto (PM:568) | `cloud_free = I05 >= 0.0` = todo True (PV:795-803) | sin mascara (PVM) | `CLOUD_MASK_BT_K=0.0` | **C** / C / C |
| P20 L4bk = media de los vecinos del pixel o cumulo | `L_bg` desde `t_bg` = **mediana del anillo 5 a 25 km** (PM:569-577, 1023; DC:1064), salvo `local_kernel_bg` por volcan (media 3x3 sin hot, PM:1041-1049; `vrp_regimes.py:38`) activo en PCC, Villarrica, Chaiten, PP, Lastarria; los otros 6 Tier A usan el anillo. La corona del cumulo (Eq. 6 literal, `cluster_corona_background`) existe y esta OFF (PM:1132-1147) | camino contextual: igual que MODIS (PV:1398-1409; kernel en los mismos 5); camino Test 1: cascada anillo intermedio [1.5, 3] km > global > local 1 a 3 km (PV:1817-1835), ninguna es "vecinos"; corona OFF (PV:1487-1494) | **solo anillo 5 a 25 km** (PVM:981); el kernel no esta implementado para M-band (PVM:433-441 lo declara TODO) | `ENABLE_LOCAL_KERNEL_BG=True` (+ `local_kernel_bg` por volcan), `ENABLE_LOCAL_CLUSTER_MAGNITUDE=False`, `..._VIIRS375=False`, `ENABLE_TEST1_INTERMEDIATE_BG=True`, `ENABLE_TEST1_LBG_GLOBAL=True` (+ `lbg_global_compatible`: Lascar, NdC, Lastarria) | **D** / D / D |
| P21 RP_pix = 18.9 A_pix dL | `WOOSTER_COEFF=18.9` (PM:82), `A_pix=1e6` (SG:148), Planck a 3.929 um (PM:1023-1057). **Extra**: `delta_L = max(., 0)` (PM:1056) | 18.0 x 140 625 (PV:75, 1416-1419), clip igual | 19.7 x 562 500 (PVM:64, 985-986), clip igual | `ENABLE_NADIR_FIXED_PIXEL_AREA_*=True` | **Cp** (clip) / n/a (coeficiente empirico S14) / n/a |
| P22 RP total = suma de todos los alertados | `vrp_mw = nansum(per_pixel)` (PM:1058) **existe pero no es lo que se publica**: el dashboard lee `primary_cluster.vrp_mw` (`frontend/index.html:1043-1064`) = cumulo `vent_anchored` (PM:1101-1107; `clustering.py:116-160`), luego `cluster_focal_vrp_mw` (PM:1151-1155), tope D9 (PM:1158-1160), `apply_single_pixel_mode` (PM:1179-1184). Y `store.py:313` recorta `anomaly_pixels` a 25 km (circulo dentro de la caja de 50), `:339-401` rescate/zero-out por distancia, `:405-412` `max_cluster_pixels`, `:414` `vrp_mw = max(eruption, vent)` | idem, mas `f5_core_vrp_mw` que el dashboard prefiere (`store.py:552`, `frontend/index.html:1121-1126`) | idem (PVM:1023-1057) | `ENABLE_VENT_ANCHORED_CLUSTERING=True`, `ENABLE_FOCAL_CLUSTER_MAGNITUDE=True` (MODIS), `..._VIIRS750=True` (solo camino Test 1), `FOCAL_CLUSTER_KEEP_PEAK=True`, `ENABLE_SINGLE_PIXEL_SUB_MW_MODE=True` (5 MW, 3 px), `PATH_D_ONLY_CAP_MW=5.0` con `t_bg<270`, `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True`, `ENABLE_SUM_VRP_REPORTING=False` | **D** / D / D (en el numero publicado) |
| P23 descarte visual a posteriori | no hay supervision humana; la serie va al dashboard tal cual (con los extras de P22) | idem | idem | | n/a |
| P24 misma grilla y ROIs para todos | `inner_radius_km` 3 a 20 km, `local_kernel_bg`, `lbg_global_compatible`, `max_cluster_pixels=12` (solo Villarrica), `exclude_zones` (OFF por `ENABLE_EXCLUDE_ZONES=False`, `exclusion_zones.py:62`) son **por volcan** | idem | idem | `ENABLE_EXCLUDE_ZONES=False` | **D** / D / D |

Nota sobre el orden real de ejecucion (los tres procesadores, mismo esqueleto): fondo del anillo
(P20) -> caminos legacy calculados solo para diagnostico (BT path OFF, K1, dNTI contextual) -> Test 1
integrado de Coppola 2015 (no es de este paper) -> `combine_hot_paths` -> **primer pase Tests 2 y 3
pisa el combine** -> segundo pase sin condicion -> cumulo vent-anchored -> magnitud con sus recortes ->
cascada de fuente (`test1` puede ganar y recomputar la magnitud con otro fondo) -> ancla honesta
(ON en VIIRS375 y VIIRS750, OFF en MODIS) -> `store.py` (filtro 25 km, rescate, `max_cluster_pixels`,
guard A46 summit->far).

## 3. Lo que el codigo tiene y el paper NO (PASO C)

Todo leido en esta sesion; peso medido con `02_records_operacionales_extras.py` sobre los 11 Tier A,
ventana 2025-02-15 a 2026-09-13 07:00 UTC, n = 12 025 MODIS / 23 729 VIIRS375 / 23 540 VIIRS750.

| # | Mecanismo | Donde | Efectivo | Peso medido |
|---|---|---|---|---|
| X1 | Compuerta `bt > t_bg + 3 K` dentro de los Tests 2 y 3 (y en K1, dNTI ctx, ETI path) | DC:532, 269; PM:665, 821; PV:976, 998, 1178; PVM:624, 643 | `NTI_BT_SANITY_K=3.0` | ver H1: la anula el segundo pase |
| X2 | Segundo pase sin condicion de existencia ni de adyacencia | DC:887, 946; PM:919; PV:1284; PVM:876 | `ENABLE_SECOND_PASS_CONDITIONED=False` | records con deteccion SOLO del 2do pase (`fp=0, sp>0`): MODIS 40 (0.33 %), V375 3 313 (13.96 %), V750 4 058 (17.24 %) |
| X3 | Test 1 integrado de ROI (Coppola 2015 BV, no SP426.5) decide la fuente y recomputa la magnitud | `test1_integrated.py:317-475`; PM:737-752, 1279-1302, 1360-1363; PV:1096-1106, 1708-1713, 1869; PVM:706-720, 1205 | `ENABLE_TEST1_PATH=True`, `TEST1_ROI_KM=3.0`, `TEST1_K_SIGMA=3.0` | `triggered_test1`: MODIS 3.76 %, V375 77.89 %, V750 22.21 %; `final_hotspot_source=test1`: 2.40 / 1.29 / 0.13 % |
| X4 | Interseccion contextual del Test 1 + `keep_peak` | PV:1784-1796; `test1_contextual_filter.py:35-60` | `ENABLE_TEST1_CONTEXTUAL_FILTER=True`, `..._KEEP_PEAK=True` (solo I-band) | D19 (catalogo) |
| X5 | Magnitud focal (`dnti_ctx` U {pico}) | `vrp_regimes.py:273-300`; PM:1151, 1401; PVM:1251 | `ENABLE_FOCAL_CLUSTER_MAGNITUDE=True`, `..._VIIRS750=True`, `FOCAL_CLUSTER_KEEP_PEAK=True` | `pc.focal_magnitude`: MODIS 94.62 %, V750 11.86 % |
| X6 | Modo pixel unico bajo 5 MW y <= 3 px (publica el maximo, no la suma) | `single_pixel_mode.py:94-176`; PM:1179; PV:1518, 1951; PVM:1050, 1276 | `ENABLE_SINGLE_PIXEL_SUB_MW_MODE=True` | `pc.single_pixel_mode`: 47.62 / 79.89 / 24.82 % |
| X7 | Tope 5 MW si el disparo es solo contextual y `t_bg < 270 K` (D9) | `path_d_cap.py`; PM:1064, 1158; PV:1424; PVM:989 | `PATH_D_ONLY_CAP_MW=5.0`, `..._TBG_MAX_K=270.0` | `pc.d9_capped`: MODIS 11.58 %, V750 0.15 % |
| X8 | Seleccion de cumulo `vent_anchored` (el mas cercano al vent gana, no la suma de la escena) | `clustering.py:116-160`; PM:1101; PV:1463; PVM:1023 | `ENABLE_VENT_ANCHORED_CLUSTERING=True` | `pc.vrp_mw != vrp_mw`: 87.78 / 16.82 / 18.21 % |
| X9 | Magnitud "nucleo" F5' (I-band) preferida por el dashboard | `f5_core.py`; `store.py:552`; `frontend/index.html:1121-1126` | siempre (sin flag) | `f5_core != pc.vrp_mw`: 16 238 de 17 919 records con el campo (90.6 %) |
| X10 | Filtro de pixeles a 25 km del centro (circulo) dentro de la caja de 50 km, rescate por cumulo y zero-out | `store.py:217-270, 313, 339-401` | `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True`, `max_hotspot_dist_km=radius_km=25` | `partial_eruption_hotspot_too_far`: MODIS 11 040 (91.8 %), V375 448, V750 197; `eruption_hotspot_too_far`: 29 / 51 / 72; rescate: 113 / 492 / 38 |
| X11 | `max_cluster_pixels=12` (Villarrica) anula la magnitud | `store.py:405-412` | por volcan | `cluster_too_large_for_volcano`: MODIS 219, V750 273 |
| X12 | Etiqueta `distance_class` far/summit derivada del pixel MIR maximo, con guard A46 unidireccional; el dashboard oculta lo `far` | PM:1305-1307, 289-315; `store.py:470-478`; `frontend/index.html:1043-1064` | `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER=False`, `ENABLE_HONEST_ANCHOR_MODIS=False` | MODIS `far` con cumulo `summit`: 9 422 (78.35 %) |
| X13 | Ancla honesta (posicion publicada = vent a 0.0 km para Test 1) | `anchor.py:67-96`; PV:1990; PVM:1289 | `ENABLE_HONEST_ANCHOR=True`, `..._VIIRS750=True`, `..._MODIS=False` | D11-bis / D19 |
| X14 | Refit iterativo 3 sigma en la regresion NTIbk | DC:685-688, 745-765 | siempre | no medido |
| X15 | `delta_L` recortado a >= 0 | PM:1056; PV:1416; PVM:985 | siempre | no medido (es lo que deja en 0.0 MW un pixel mas frio que el anillo) |
| X16 | Tope de cordura 50 GW y pisos por sensor | `store.py:64, 73-105, 108-153` | pisos = 0.0 (apagados); cap activo | `piso_vrp_aplicado`: 0 en los tres buckets; `sanity_cap_tocado`: 0 |
| X17 | Fondo t_bg = mediana (no media) del anillo, con `min_bg_pixels=10` | DC:1064; PM:569-577 | siempre | (P20) |
| X18 | Solo noche (elevacion solar < 0 sobre el volcan) | `run_pipeline.py:185-195`; `store.py:171-182` | `ENABLE_DAYTIME_MODIS=False` | 100 % de las pasadas diurnas descartadas |

Caminos que existen en el codigo pero que **no participan** en el perfil operacional (verificado por
flag): BT path (`ENABLE_BT_PATH_HOT=False`, PM:657-658), vent path (`ENABLE_VENT_PATH=False`,
`_MODIS=False`), NTI relativo (`ENABLE_NTI_RELATIVE_PATH=False`), ETI path S37
(`ENABLE_ETI_QUADRATIC_SCENE=False`), gates intra-radio (ambos False), co-validacion y gate atmosferico
D9 (None/False), filtro final de pixeles (False), Test 1 sobre NTI (False), Eq. 16 lava lake (False),
VRP TIR (`ENABLE_VRP_TIR_OUTPUT=False` -> `_compute_vrp_tir_with_gate` devuelve 0.0, PV:299-300),
exclusion zones (False). El dNTI contextual legacy (`ENABLE_DNTI_CONTEXTUAL_PATH=True`) se calcula pero
el primer pase lo pisa: hoy solo alimenta la magnitud focal (X5) y el filtro contextual (X4).

## 4. Conteo con denominador (PASO D)

Denominador: **24 pasos** del paper (P01 a P24, seccion 1).

| Sensor | Conforme (C) | Conforme con adicion (Cp) | Divergente (D) | Ausente (A) | n/a (fuera del paper) |
|---|---|---|---|---|---|
| MODIS | 8 (P04, P09, P11, P12, P17, P19, P16-noche, P21-coef) | 4 (P10, P13-1er pase, P15, P21-clip) | 10 (P01, P02, P05, P07, P08, P14, P18, P20, P22, P24) | 3 (P03, P06, P16-dia, P13-2do pase se cuenta dentro de P18) | 1 (P23) |
| VIIRS375 | 8 (P03, P04, P09, P11, P12, P17, P19, P16-noche) | 3 (P10, P13-1er, P15) | 6 (P07, P14, P18, P20, P22, P24) | 2 (P06, P16-dia) | 6 (P01, P02, P05, P08, P21, P23) |
| VIIRS750 | 8 (idem V375) | 3 | 6 (idem V375) | 2 | 6 |

Los pasos con dos caras (P13, P16, P21) se cuentan una vez por su cara dominante en la fila; el detalle
esta en la matriz. Regla del recuento: un paso es "conforme" solo si su funcion corre en el perfil
operacional con los valores del paper, no si existe detras de un flag apagado.

**Cruce con `docs/MIROVA_DIVERGENCES.md`** (leido al final; encabezados `## D1` a `## D22` y sus
cuerpos D19-D22 en `:2058-2218`; `GAP #A` en `:1318-1352`):

| Divergencia literal de la matriz | D# en el catalogo |
|---|---|
| P05 B21 primaria | D21 |
| P06 sin remuestreo / area nadir sobre pixel elongado / dos centros | D17 (grilla; menciona bow tie en `:1909-1910`), D16 (refutada) |
| P07 ROI1 circulo per-volcan | D18 |
| P08 NTI con B31 | D20 |
| P14b K1 no retirado del pool | GAP #A dentro de D11 (`:1318-1352`, reabierto S128) |
| P15 compuerta BT | D22 |
| P18 segundo pase sin condicion ni adyacencia | D19 (segunda cara) |
| P20 fondo del anillo | D8 (marcada RESUELTA con el kernel opt-in; la divergencia literal "media de vecinos" sigue en 6 de 11 en MODIS, 11 de 11 en M-band, y en todo el camino Test 1) |
| P22 numero publicado != suma de la escena | D1 (cumulo), D13 (cerca far), D9 (tope) |
| P24 parametros por volcan | D18 parcial; MISSION.md l.77 |
| **P02 saturado 65533 eliminado (+ guard 500 K)** | **ninguno** |
| **P03 bow tie MODIS ausente como paso propio** | **ninguno** (solo una nota dentro de D17) |
| **P14a K1 no es camino de deteccion (el primer pase pisa el combine)** | **ninguno** |
| **P16 dia ausente (Tabla 1 dia nunca se usa)** | **ninguno** |
| **P13 segundo pase sin filtros de no-aptos** | **ninguno** (D19 nombra la compuerta y la adyacencia, no el pool) |
| **P10 refit iterativo 3 sigma** | **ninguno** |
| **P20 mediana del anillo en vez de media de vecinos, como divergencia literal vigente** | **ninguno abierto** (D8 cerrada) |
| **P21 clip delta_L >= 0** | **ninguno** |

**Divergencias literales sin D#: 8 de 18** (las ocho en negrita). De las 18, las tres que mas mueven
lo que ve el operador (H1, H2, H3 abajo) tienen D# vecino pero **mal atribuido** (D22) o **cerrado**
(D8) o **no las nombra** (P14a).

## 5. Hallazgos (ordenados por gravedad, lo peor primero)

### H1. La compuerta de temperatura (D22) no decide la deteccion en produccion: el segundo pase la anula; y la perdida de Villarrica A6 esta atribuida al paso equivocado
- ARCHIVO:LINEA: `pipeline/detection_context.py:532` (compuerta, primer pase) vs `:887-948` (segundo pase: sin `conditioned`, sin compuerta, pool `:904`). Llamadas: PM:919-951, PV:1284-1317, PVM:876-909. SCRIPT: `01_controles_sinteticos_detection_context.py` -> `M1_compuerta_bt`.
- QUE PASA. Fenomeno: en una cumbre helada el pixel con lava sub-pixel es mas frio en BT que la mediana de una escena de 50 km con valles y lagos; lo delata el contraste espectral (dNTI, dETI), no la temperatura. Codigo: el primer pase exige `bt > t_bg + 3 K` y descarta ese pixel; pero el segundo pase, tal como se llama en produccion (`conditioned=False`), recalcula dNTI/dETI sobre toda la caja aunque el primer pase este vacio y marca todo pixel con dNTI > C1 y dETI > C1 **sin la compuerta**. Control sintetico: pixel con dNTI 0.0078 (C1 = 0.003) y BT = t_bg + 1 K: primer pase 0 pixeles, segundo pase en modo produccion lo marca (1 pixel); con `conditioned=True` no lo marca. Control positivo: el mismo pixel a +8 K pasa el primer pase. Consecuencia sobre D22: la batería B22 de S137 (`experiments/_s137/RESULTADO_BATERIA_B22.md`, tabla Villarrica) reporta "cumulo en el crater (0.8 km) de **0.0 MW**, pixeles 1er paso 0 y 0": el crater SI entra al hot mask (por el segundo pase, que la probe por etapa de S137 no envolvio: `probe_etapa_apendice.py:145` solo envuelve `first_pass_tests_2_and_3`), y lo que lo deja en cero es la magnitud: `delta_L = max(L_pix - L_bg(anillo 5 a 25 km), 0)` con un pixel mas frio que el anillo (P20 + X15). El operador no lo ve porque `isValidDetection` exige `vrp_mw > 0` (`frontend/index.html:1466-1470`).
- COMO SE VE EN EL DASHBOARD: en VIIRS375 el 13.96 % y en VIIRS750 el 17.24 % de los records (MODIS 0.33 %) tienen deteccion producida SOLO por el segundo pase (`diag_n_first_pass_pixels=0`, `diag_n_second_pass_recapture>0`); son detecciones publicadas por un mecanismo que el paper no tiene en esa forma. En sentido contrario, un crater frio detectado asi se publica con 0.0 MW y desaparece.
- COMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent python experiments/_s138_audit/eje2/01_controles_sinteticos_detection_context.py` (M1). Para el caso real: re-correr la probe por etapa de S137 sobre Villarrica 2009-06-24 05:55 UTC (MODIS Aqua, figura A6) envolviendo ademas `second_pass_adjacent` y capturando `delta_L` del bloque de magnitud.
- CONFIANZA: CONFIRMADO el mecanismo (codigo + sintetico + conteo operacional); SOSPECHA la atribucion exacta del caso A6 hasta correr la probe ampliada.
- GRAVEDAD: 4. Cambia que se quita para curar Villarrica: quitar la compuerta no cambia la deteccion operacional (ya esta anulada) y no publica el crater; lo que hace falta es el fondo de vecinos del paper (P20). Y condicionar el segundo pase como manda el paper (D19) reactivaria la compuerta con toda su fuerza.

### H2. El Test 1 del paper (NTI > K1) no es un camino de deteccion en produccion: sus pixeles solo cuentan si ademas pasan los Tests 2 y 3, y el interior de un cuerpo caliente extenso se pierde
- ARCHIVO:LINEA: PM:660-666 (K1 se calcula), PM:824 (entra al combine), PM:888 (`hot_mask_2d = fp_hot` lo pisa), PM:857-859 (`test1_mask=None`); PV:971-976, 1188, 1259, 1231-1233; PVM:619-624, 783, 851, 823-825. SCRIPT: `01_...` -> `M2_retiro_test1_pool`, `M3_bloque_7x7`.
- QUE PASA. Fenomeno: en una colada o un lago de lava que ocupa varios pixeles, los pixeles interiores estan rodeados de pixeles igual de calientes: su dNTI es ~0 y no son "anomalos respecto de sus vecinos". El paper los captura con el Test 1 (NTI > -0.8 es lava franca) y los declara activos. Codigo: K1 no entra al hot mask final y tampoco retira nada del pool. Control sintetico: bloque 7x7 a 400 K sobre fondo de 280 K: Test 1 marcaria 49/49; primer pase 27, tras el segundo pase 28; interior 3x3: 1 de 9. Pool: `n_bg_used` 2393 con `test1_mask=None` vs 2392 con la mascara (el K1 esta adentro).
- COMO SE VE EN EL DASHBOARD: en la fase efusiva fuerte (la que importa para la alerta) la magnitud publicada suma el borde del cuerpo y no su interior, o sea sub-estima justo cuando MIROVA reporta mas. Frecuencia de K1 en records operacionales: MODIS 11, VIIRS375 317, VIIRS750 28 (0.09 / 1.34 / 0.12 %): pocos, pero son los eventos mas energeticos del periodo.
- COMO REPRODUCIRLO: script 01, M3. Caso real: cualquier record con `diag_n_nti_path > 0` y `n_anomalous_pixels` menor que `diag_n_nti_path` (comparar contra el hot mask con K1 incluido reprocesando un granule).
- CONFIANZA: CONFIRMADO en codigo y sintetico; SOSPECHA la magnitud del efecto en records reales (no se reprocesaron granules).
- GRAVEDAD: 4 en magnitud de erupcion; 2 en deteccion (el borde siempre dispara).

### H3. El fondo del VRP es la mediana de un anillo regional, no la media de los vecinos del pixel o del cumulo; en M-band no hay ninguna alternativa implementada
- ARCHIVO:LINEA: DC:1064 (`median`), PM:569-577 y 1023 (anillo 5 a 25 km), PM:1041-1049 (kernel 3x3 solo si `local_kernel_bg` por volcan: PCC, Villarrica, Chaiten, PP, Lastarria), PVM:981 (solo anillo), PVM:433-441 (TODO declarado), PV:1817-1835 (cascada del Test 1), `vrp_regimes.py:109` (corona Eq. 6, OFF).
- QUE PASA. Fenomeno: el anillo de 5 a 25 km alrededor de un nevado esta lleno de valle tibio; el pixel del crater helado queda mas frio que ese fondo y su exceso de radiancia se recorta a cero (X15). El paper mide el exceso contra los pixeles que rodean al activo, que en la cumbre son hielo tan frio como el crater. Codigo: seis de once Tier A en MODIS (Lascar, Copahue, NdC, Llaima, Isluga, Tupungatito) y los once en M-band usan el anillo; el camino Test 1 usa otros tres fondos, ninguno "vecinos".
- COMO SE VE EN EL DASHBOARD: magnitudes 0.0 MW en cumbres frias con deteccion real (el crater de Villarrica A6 con B22, S137) y magnitudes infladas donde el anillo es mas frio que el entorno del foco (glaciar de Tupungatito, A19). Es la pata de magnitud de D19 y el motivo por el que el numero publicado depende de `local_kernel_bg` por volcan (P24).
- COMO REPRODUCIRLO: reprocesar Villarrica 2009-06-24 05:55 UTC (MODIS) con `ENABLE_MODIS_B22_PRIMARY=True` y comparar `delta_L` con fondo de anillo vs `cluster_corona_background`.
- CONFIANZA: CONFIRMADO (codigo, flags, YAML); el efecto numerico en A6 es SOSPECHA hasta el reproceso.
- GRAVEDAD: 3.

### H4. Los pixeles saturados de MODIS (DN 65533) se eliminan; el paper los conserva
- ARCHIVO:LINEA: PM:244-250 (`rad[dn > 32767] = NaN`), PM:555 (guard BT > 500 K a NaN), PM:331-333 (`merge_mir_bands`: el NaN de B21 cae a B22, que satura a ~331 K y tambien es NaN).
- QUE PASA. Fenomeno: en un paroxismo el pixel del foco satura la banda 21 (~500 K); ese pixel es el mas caliente de la escena. El paper lo conserva marcado como saturado (con la excepcion explicita "with the exception of the pixels with DN = 65 533"). Codigo: queda NaN en las dos bandas MIR, no entra al NTI, al pool ni al hot mask, y no aporta radiancia: agujero en el centro de la anomalia. El origen es la correccion F28 (S73) a un caso de basura (PP 2026-03-18).
- COMO SE VE EN EL DASHBOARD: en el evento mas grande posible, el cumulo publicado tiene un hueco en el pixel mas energetico y la magnitud queda por debajo de lo que MIROVA publicaria. No hay records asi en la ventana medida (`sanity_cap_tocado` = 0 en los tres buckets), asi que hoy es invisible.
- COMO REPRODUCIRLO: granule MODIS con DN = 65533 en B21 dentro de la caja (por ejemplo el de PP 2026-03-18 citado en PM:236-243) y comparar `n_anomalous_pixels` y `vrp_mw` con y sin el filtro.
- CONFIANZA: CONFIRMADO en codigo; SOSPECHA el efecto (no hay caso en data).
- GRAVEDAD: 3 (solo actua en paroxismos, pero ahi resta).

### H5. Sin remuestreo ni bow tie, con area fija de 1 km2 sobre pixeles que no miden 1 km2
- ARCHIVO:LINEA: PM:499-510 (sin regrid, area fija), SG:132-149, `ENABLE_UTM_REGRID=False` (leido de `thresholds:`, `profile.py:606`), PV:707-723, PVM:452-466.
- QUE PASA: el paper remuestrea para que la deteccion vea vecinos de igual tamano y para que A_pix = 1 km2 sea verdad. Codigo: los 8 vecinos son pixeles nativos de tamano variable con el angulo, y la magnitud usa un area que no es la del pixel (S131 lo midio como el gradiente cenital completo del sub-reporte). El bow tie de MODIS no se trata en ningun paso del perfil operacional.
- COMO SE VE EN EL DASHBOARD: magnitud dependiente del angulo de la pasada (misma fuente, distinto numero segun la orbita).
- COMO REPRODUCIRLO: `docs/s131/REMUESTREO_LEY_DE_AREA.md` ya lo cuantifica; para verificar el paso: `grep -n "ENABLE_UTM_REGRID" pipeline/process_modis.py` y el valor efectivo.
- CONFIANZA: CONFIRMADO. Catalogado en D17 (abierta).
- GRAVEDAD: 3.

### H6. El dia no existe: la Tabla 1 diurna esta escrita y nunca se ejecuta
- ARCHIVO:LINEA: PM:355-378 (`_select_thresholds`), `ENABLE_DAYTIME_MODIS=False`, `run_pipeline.py:185-195`, `store.py:171-182`.
- QUE PASA: el paper procesa pasadas diurnas con K1 = -0.6, C1 = 0.02, C2 = 15 y advierte que ahi estan la mayoria de sus falsas alertas (p. 16-17). El proyecto descarta todo lo diurno por decision (MISSION). Es una divergencia literal deliberada, no registrada como D#.
- COMO SE VE EN EL DASHBOARD: MIROVA publica detecciones diurnas de MODIS que el operador nunca vera aca (la mitad de las pasadas de Terra/Aqua).
- COMO REPRODUCIRLO: contar en `data/mirova_reference/` alertas MIROVA MODIS con hora local diurna y buscar su record en `data/mirova_equivalent/`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (recall de dia; riesgo de FP diurnos si se activara).

### H7. El segundo pase calcula mu y sigma sin los filtros de no-aptos del paper
- ARCHIVO:LINEA: DC:904 vs DC:81-140 y DC:477. SCRIPT: `01_...` -> `M4_pool_segundo_pase`: un solo outlier con dNTI << -0.1 multiplica sigma del segundo pase por 12 (0.00085 -> 0.0104) mientras el primer pase lo excluye (n_bg 2400 de 2401).
- QUE PASA: el paper aplica los no-aptos a "the subsequent steps"; el segundo pase los ignora (borde, < -0.1, K1). Con la conectiva `min(C1, mu + C2 sigma)` el piso C1 gobierna y el efecto sobre el umbral es nulo mientras `mu + C2 sigma > C1` (S136 midio que eso pasa en el 100 % de MODIS); solo importaria en escenas muy homogeneas o si se adoptara la lectura de la prosa (`max`).
- COMO SE VE EN EL DASHBOARD: invisible hoy.
- COMO REPRODUCIRLO: script 01, M4.
- CONFIANZA: CONFIRMADO (efecto nulo bajo `min`, tambien confirmado).
- GRAVEDAD: 1 hoy; 3 si se adopta la rama de la prosa (`ENABLE_TESTS_23_PROSE_BRANCH`).

### H8. El ROI1 es un circulo per-volcan de 3 a 20 km y su centro no es el de la escena
- ARCHIVO:LINEA: DC:287-313, PM:527-533 (caja en `lat/lon`, ROI1 en vent), `volcanoes.yaml` (PCC inner 20 km, vent a 7.6 km del `lat/lon`).
- QUE PASA: el paper usa una caja de 25 km2 igual para todos y un solo centro (GVP). Codigo: hasta 1 257 km2 (PCC) reciben el umbral laxo, y la escena y el ROI1 tienen centros distintos. D18 lo cataloga (A/B S130 -> NO ADOPTAR); la parte de los dos centros esta en D17.
- COMO SE VE EN EL DASHBOARD: mas pixeles con umbral summit de los que el paper daria; la etiqueta "summit" cubre el lacolito de PCC entero.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### H9. El numero que ve el operador no es la suma de la escena del paper en la mayoria de los records
- ARCHIVO:LINEA: seccion 3, X5 a X12. SCRIPT: `02_records_operacionales_extras.py`.
- QUE PASA: `pc.vrp_mw != vrp_mw` en 87.78 % MODIS / 16.82 % V375 / 18.21 % V750; `single_pixel_mode` en 47.62 / 79.89 / 24.82 %; `focal_magnitude` en 94.62 % MODIS; `d9_capped` 11.58 % MODIS; `f5_core != pc.vrp_mw` en 90.6 % de los I-band con el campo; `partial_eruption_hotspot_too_far` en 91.8 % de MODIS; `far` con cumulo summit 78.35 % de MODIS (invisibles por `mirovaEqVrp`). Cada uno tiene su justificacion en el repo (D1, D9, D11/A81, D13, F52); ninguno esta en el paper.
- COMO SE VE EN EL DASHBOARD: es el dashboard.
- CONFIANZA: CONFIRMADO (conteos con denominador y ventana arriba).
- GRAVEDAD: 3 como conjunto (la ficha SDA debe declararlos; ninguno por separado tuerce una alerta que los otros no toquen).

### H10. Detalles menores sin D#
- B31 en vez de B32 (PM:75-76; D20, cuantificado despreciable en S128). Gravedad 1.
- Refit iterativo 3 sigma en la regresion (DC:685-688, 745-765): probablemente mejora el ajuste del fondo, pero no esta en el paper y no tiene flag. Gravedad 1.
- `delta_L` recortado a 0 (PM:1056): consecuencia operativa de H3; el paper no lo necesita porque su fondo es local. Gravedad 1.
- Mediana (no media) en el fondo del anillo (DC:1064). Gravedad 1.

## 6. VERIFICADO LIMPIO

Lo que se miro y esta sano, con el comando que lo confirma (todo en esta sesion):

1. **Tabla 1 nocturna, valores exactos del paper**: `C1 = 0.003 / 0.010`, `C2 = 5 / 10`, `K1 = -0.8`. `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.DNTI_CONTEXTUAL_C1_SUMMIT, p.DNTI_CONTEXTUAL_C1_SCENE, p.C2_DNTI_SUMMIT_NIGHT, p.C2_DNTI_SCENE_NIGHT, p.C2_DETI_SUMMIT_NIGHT, p.C2_DETI_SCENE_NIGHT, p.NTI_K1_NIGHT)"` -> `0.003 0.01 5.0 10.0 5.0 10.0 -0.8`. Sin overrides: `C1_SUMMIT_OVERRIDE=None`, `C2_SUMMIT_OVERRIDE=None`, `VIIRS_C2_OVERRIDE_NIGHT=None`.
2. **Conectiva de los Tests 2 y 3 = la formula del paper** (OR interno, AND entre tests): DC:510 y DC:924 `combinar = min` con `ENABLE_TESTS_23_PROSE_BRANCH=False`; AND en DC:529-532 y DC:938-940.
3. **Kernel de 8 vecinos con media aritmetica**: DC:162-190 (`_nanmean_8neighbors_fast`, convolucion con centro 0). Sin mediana.
4. **NTIapp y regresion cuadratica por imagen, ETI = NTI - NTIbk**: DC:606-676 y 680-775; `np.polyfit(x, y, 2)` recalculado en cada granule.
5. **mu y sigma del primer pase sobre todos los pixeles aptos de la caja de 50 km** (no del anillo): DC:477-493 con `roi_mask` de PM:532.
6. **No aptos del primer pase (borde y < -0.1) activos**: `ENABLE_UNSUITABLE_FILTERS_267_273=True`; DC:64-140; control M4 del script 01 (el outlier queda fuera del pool: 2400 de 2401).
7. **El segundo pase excluye los activos de la media de vecinos y del pool** (P17): DC:898-904.
8. **Coeficiente y area de MODIS**: `WOOSTER_COEFF = 18.9` (PM:82), `A_pix = 1.0e6` (SG:148 con `nadir_fixed=True`). Planck a 3.929 um consistente en deteccion y magnitud (PM:1023, 1032).
9. **Sin mascara de nube en los tres sensores**: `CLOUD_MASK_BT_K = 0.0`; PM:568 y PV:795-803 quedan sin efecto; PVM no tiene mascara. Coincide con P19 y con D14 (cerrada).
10. **Solo noche, coherente en las dos capas**: `run_pipeline.py:185-195` y `store.py:171-182` con `ENABLE_DAYTIME_MODIS=False`.
11. **Caja de 50 x 50 km en los 11 Tier A**: `radius_km = 25` en los 11 (`volcanoes.yaml` via `yaml.safe_load`), `roi_mask_bbox(half_km=25)` en PM:532, PV:751, PVM:488.
12. **Nadie usa la banda 32 a medias**: `grep -rn -i "band32|B32|12.02|L32" pipeline/ tests/ scripts/` -> 0 resultados (la divergencia D20 es limpia, no hay una implementacion parcial).
13. **Los flags se leen de donde `profile.py` dice** (regla A89, verificado por importacion y no por YAML): `ENABLE_UTM_REGRID` sale de `thresholds:` (`profile.py:606`), `ENABLE_MODIS_B22_PRIMARY` y `ENABLE_SINGLE_PIXEL_SUB_MW_MODE` del nivel raiz (`:358`, `:566`), el resto de `paths:`; los 139 valores efectivos estan en `experiments/_s138_audit/eje2/profile_efectivo_mirova_equivalent.txt`.
14. **Los caminos legacy apagados estan realmente apagados**: `ENABLE_BT_PATH_HOT=False` (PM:657-658 pone la mascara en ceros), `ENABLE_VENT_PATH=False`, `ENABLE_VENT_PATH_MODIS=False`, `ENABLE_NTI_RELATIVE_PATH=False`, `ENABLE_ETI_QUADRATIC_SCENE=False`, `ENABLE_PATH_D_INTRA_RADIO_GATE=False`, `ENABLE_SECOND_PASS_INTRA_RADIO_GATE=False`, `ENABLE_FINAL_PIXEL_FILTER=False`, `ENABLE_EXCLUDE_ZONES=False` (`exclusion_zones.py:62` devuelve `None, None`), `ENABLE_VRP_TIR_OUTPUT=False` (PV:299-300 devuelve 0.0).
15. **Pisos de VRP apagados y tope de cordura sin uso en la ventana**: `MIN_VRP_MW_*=0.0`; script 02: `piso_vrp_aplicado = 0`, `sanity_cap_tocado = 0` en los tres buckets (n = 12 025 / 23 729 / 23 540).
16. **Los diagnosticos que sostienen los conteos estan en el 100 % de los records** (control positivo del instrumento): `diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`, `diag_n_nti_path`, `primary_cluster`, `final_hotspot_source`, `distance_class`, `triggered_test1` presentes en n = n_records en los tres buckets (script 02, bloque `campos_presentes`). `f5_core_vrp_mw` solo en I-band (17 919 de 23 729), que es lo esperado por diseno (`store.py:551-554`).
17. **El ancla de deteccion es el crater** (`get_detection_anchor`, `geo_utils.py:53-77`): el vent gana sobre `mirova_center`; los tres `run_pipeline.py:234, 277, 324` lo usan.

Lo que NO se verifico en esta sesion y queda declarado: ningun granule real se reproceso (los
controles son sinteticos sobre `detection_context` y conteos sobre records persistidos); la equivalencia
Planck/LUT de VIIRS no se comprobo numericamente; no se midio el peso de H2 ni de H4 sobre eventos reales.
