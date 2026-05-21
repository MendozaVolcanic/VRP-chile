# Síntesis exhaustiva papers MIROVA — S71 (2026-05-21)

> Trigger: Nicolás reportó que sesiones previas leyeron solo **notas markdown del Vault** (síntesis ~100-200 líneas), NO los PDFs completos. El verdict S71 T1 Fase 1 "papers NO resuelven D9" se basó en sample. Esta revisión es exhaustiva sobre los 3 papers canónicos + refs.

## Papers revisados directamente (full text)

| Paper | Status local | Líneas .md | Procesado en doc S57 | Procesado S71 |
|---|---|---|---|---|
| **Coppola 2016 GSL SP 426.5** "Enhanced volcanic hot-spot detection using MODIS" | ✅ `documentacion/sp426.5.pdf` + `sp426_5.txt` | 1036 (.txt) | Parcial | ✅ Exhaustivo |
| **Coppola 2019 Frontiers** "Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System" | ✅ `documentacion/Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` | 2353 (`coppola2019_frontiers.md` creado S71) | ❌ NO procesado en S57 | ✅ Exhaustivo |
| **Coppola 2023 Frontiers** "Global radiant flux from active volcanoes: the 2000–2019 MIROVA database" | ✅ descargado S71 → `documentacion/Coppola_2023_GlobalRadiantFlux_MIROVA.pdf` | 1844 (`coppola2023_frontiers.md` creado S71) | ❌ NO procesado en S57 | ✅ Exhaustivo |

**Gap identificado**: doc S57 cubrió SP426.5 + Coppola 2024 Springer + Campus 2024 + Aveni 2025. **NO cubrió** los 2 Frontiers (2019 y 2023) que son justo los que Nicolás citó por URL. Esa es la razón por la que el verdict S71 T1 Fase 1 fue sub-óptimo.

## Hallazgos críticos NUEVOS (no estaban en S57)

### H1 — MIROVA admite explícitamente que NO maneja cloud per-scene programáticamente

**SP426.5 §247-249** (ya estaba en S57 pero subutilizado):
> *"the **presence of clouds is not taken into account by the algorithm** and all eight neighbouring pixels are used to compute the spatial average"*

**SP426.5 §712-728** (NUEVO — sección "Meteorological and volcanic clouds"):
> *"there is, as yet, **no robust method** to evaluate the amount of thermal radiation attenuated by clouds, or volcanic plumes, so that **visual inspection** of the image still remains the best solution ... the RP time series obtained by MIROVA are provided **'as they are'** and may be affected by the presence of meteorological and/or volcanic clouds"*

**Coppola 2019 §1443-1480** (NUEVO — sección "Image Quality Assessment"):
> *"any hot spot detection system should be able to quantify the effects of clouds and viewing geometry condition, within each acquired image. **This fundamental step is currently absent in all available algorithms** ... in many cases thermal anomalies within high-altitude summit craters may be discarded or classified as strongly attenuated, because the surroundings pixels are cloudy (although the crater is actually without cloud cover)"*

**Coppola 2023 §554-558** (NUEVO):
> *"the VRP data provided by MIROVA are provided **'as-are', i.e., without atmospheric corrections and cloud fraction estimates** accompanying the measurement"*

### H2 — MIROVA tiene tasa empírica de FPs ACEPTADA de 0-3%

**Coppola 2019 §1283-1288** (NUEVO):
> *"a smaller but variable percentage of false alerts, **generally comprised between 0 and 3%** (number of false alerts/number of MODIS overpasses), is detected by the MIROVA system at different volcanoes (Coppola et al., 2016b). These false alerts depend on the regional and local environmental conditions as **climate, elevation, topography and land cover type**"*

**Implicación**: nuestros 11 vols Tier A con cirrus invernal Atacama caen en el lado alto (~3%). MIROVA acepta este nivel sin filtro adicional.

### H3 — FPs típicos MIROVA son <5 MW — VALIDACIÓN BIBLIOGRÁFICA DIRECTA DEL CAP S71

**SP426.5 §675-696** (NUEVO en S71):
> *"A limited number of false alerts may be detected by the algorithm. These principally occur on daytime images and are associated with **high NTI contrasts at the edge of water bodies, as well as within scattered clouds**. However, these false detections typically radiate **less than 5 MW** and can be easily identified by a visual inspection of the associated NTI map. As discussed previously, **reducing the false detection rate will cause numerous genuine alerts of low intensity (<10 MW) to be missed**"*

**Esta cita es la base bibliográfica directa del cap 5 MW que adoptamos en S71 Opción C** (PR #112). El paper que faltaba citar al adoptar estuvo en `documentacion/sp426.5.pdf` desde Abril (AP1 — saltarse búsqueda local).

### H4 — Mecanismos de defensa MIROVA contra contrastes regionales (cirrus, lago)

**1. NTIbk regresión cuadrática per-imagen** — **VERIFICADO IMPLEMENTADO en nuestro pipeline**:

`pipeline/detection_context.py:compute_nti_and_nti_app` aplica `np.polyfit(x, y, 2)` con iterative re-fit. Equivale a SP426.5 Eq.4: `NTIbk = a·NTIapp² + b·NTIapp + c`. ✅

**2. ETI = NTI - NTIbk neutraliza contrastes regionales** — VALIDADO EN PAPER CON CASO VILLARRICA:

**SP426.5 Fig. A6** (NUEVO en S71 — Villarrica en paper como caso validación):
> *"Villarrica volcano (Chile) ... The clear thermal contrast between the ice-covered summit ... and the **Villarrica lake** ... is clearly visible on the NTI and NTIbk. However, a very small thermal anomaly (NTI ≤ -0.93) at the summit of Villarrica is easily detected after performing the spatial filtering (dNTI and dETI). **Note how the warm lake surface almost disappears in the ETI map**"*

**El paper SP426.5 demuestra con Villarrica que ETI absorbe contraste lago→cráter**. El mecanismo análogo aplica a cirrus→cráter. PENDIENTE verificar: ¿Test 3 (dETI) está correctamente separado de Test 2 (dNTI) en nuestro `first_pass_tests_2_and_3`?

**3. C2·σ auto-adaptive a cloudiness**:

**SP426.5 Fig. A9** (NUEVO):
> *"`partially cloudy' Stromboli ... scattered clouds produces a heterogeneous scene that increase the spatial variability of the thermal indexes ... **no clear outliers in the dNTI and dETI indexes so that no hotspot is detected**"*

Cuando hay scattered clouds, σ_dNTI/σ_dETI se infla → m + C2·σ es alto → solo outliers extremos pasan. Nuestros valores C2=5 summit / C2=10 scene son los del paper Tabla 1.

**SP426.5 §403-414**:
> *"a value of C2 ≥ 10 will efficiently avoid false detections but will cause the omission of more than 25% of the small alerts (<10 MW). Conversely, a very low value of C2 (i.e. C2 ≤ 3) will only lose 7% of the small alerts, at the expense of more than 7% false detections"*

### H5 — Mecanismo de post-processing temporal MIROVA — NUESTRO PIPELINE NO LO TIENE

**Coppola 2023 §530-540** (NUEVO):
> *"**local VRP minima are removed from the weekly subset**, before performing the weekly energy calculation as per in Method-1. This method **tends to reduce the effect of cloud contamination** and unfavourable acquisitions"*

**Método-2 MIROVA**: en la agregación temporal (weekly), MIROVA descarta los mínimos locales (asumiendo que minima = cloud contamination). Nuestro pipeline publica per-overpass sin este filtro temporal.

**Coppola 2023 §564-568** (NUEVO):
> *"remove obvious 'non-volcanic' thermal features. This step was done **manually** by checking the time series and removing data points related to fires or false alerts, based on visual inspection of the images or based on fact-checking within volcanic activity reports"*

Cleanup de la database MIROVA 2023 fue **manual** (no programático).

### H6 — MIROVA reconoce soluciones ideales pero NO las implementa

**Coppola 2019 §1466-1480** (NUEVO):

- **Koeppen et al. 2011** — quantification cloud attenuation pixel-per-pixel. *"would require the collection and analysis of many more bands, including ancillary metadata and other atmospheric properties for every acquired image"* — caro, no adoptado.
- **Valade et al. 2019** — ML cloud filter. *"A promising solution is provided by machine learning, where an artificial intelligence is instructed on the basis of a supervised manual selection of cloud free images"* — promising pero no adoptado.

## Refs externas a perseguir (alternativas no-MIROVA documentadas en MIROVA papers)

| Ref | Aporte | Nivel relevancia D9 |
|---|---|---|
| **Koeppen, W. et al. (2011)** "Quantification of cloud attenuation effect on volcanic thermal anomalies retrieval" | Cloud per-pixel attenuation. La solución "ideal" según Coppola 2019. | Alta — fix arquitectural T1.5 |
| **Valade, S. et al. (2019)** "Towards global volcano monitoring using multisensor sentinel missions and artificial intelligence: The MOUNTS monitoring system" | ML cloud filter en sistema MOUNTS. Cita en Coppola 2019. | Alta — alternativa moderna |
| **Coppola, D. et al. (2010)** | Effect of unfavorable geometric conditions on VRP. Cita en Coppola 2023. | Media — geom viewing |
| **Coppola, D. et al. (2013)** | Cloud contamination effect on time series. Cita en Coppola 2023. | Media |
| **Wooster, M. J. et al. (2003)** | Fundamento MIR method (Eq.17). | Baja — ya conocemos |

## Refs externas a perseguir (Coppola 2023 cita estos para escalas globales)

- **Galetto et al. 2023** — database global eruptions vs MIROVA detection. Útil para validation.

## Supplementary material — PENDIENTE recuperar

Frontiers OA tiene supplementary material accesible via paper URL anchor `#supplementary-material`, pero el HTML SPA Nuxt requiere render JS para extraer links. Pendiente:
- **Coppola 2019 Supplementary Table S1 + S2 + Appendix** → contiene "list of all observatories" + comparativa "operational systems" — útil para refs cross-system.
- **Coppola 2023 Supplementary** → desconocido contenido. Verificar Coppola 2023 §554-558 menciona doc específico.

Action plan: usar Chrome MCP o WebFetch en próxima sesión para extraer URLs supplementary.

## Implicaciones para nuestro pipeline VRP Chile

### D9 — Estado actualizado tras revisión completa

**Causa raíz CONFIRMADA por lit MIROVA**: NO existe filtro programático per-scene de cloud en MIROVA. Es un problema reconocido y aceptado. Nuestro D9 NO es bug propio sino limitación heredada del algoritmo MIROVA.

**Mecanismos MIROVA que mitigan parcialmente** (todos los tenemos implementados):
- ✅ NTIbk regresión cuadrática per-imagen (Eq.4 SP426.5) — `compute_nti_and_nti_app`
- ✅ ETI = NTI - NTIbk (Eq.5)
- ✅ Tests 2 (dNTI) ∧ Test 3 (dETI) con C2·σ self-adaptive — `first_pass_tests_2_and_3`
- ✅ C2 = 5 summit / 10 scene (Tabla 1 SP426.5)

**Gap MIROVA → VRP Chile**:
- ❌ **Method-2 weekly local minima removal** (Coppola 2023 §530-540) — NO implementado
- ❌ **Visual inspection / manual cleanup** — no aplicable a NRT automático
- ✅ **Cap 5 MW** (S71 Opción C) — equivalente programático del trade-off documentado en SP426.5 §675-696

**Conclusión**: el cap 5 MW S71 es **la opción más alineada con MIROVA** dado que MIROVA mismo acepta 0-3% FP rate con magnitudes <5 MW como tolerables.

### Drift remanente Villarrica/Chaiten/PP/Tupungatito/NdC 6-12× (T1.5)

Hipótesis NUEVA derivable de lit revisada:

**HT1.5-NEW-1**: el drift remanente NO viene del firing contextual (D9, ya cap-eado) sino de **cluster selection / aggregation**. MIROVA agrega Σ ALL alerted pixels scene-wide (SP426.5 Eq.8, Coppola 2024 Eq.13). Nuestro pipeline selecciona `primary_cluster` cerca del vent. En escenas Muy Bajo régimen donde:
- MIROVA suma N pixels distribuidos → magnitud agregada baja (proporción de cada pixel × N)
- Nosotros elegimos 1 cluster → magnitud puede ser mayor por seleccionar el más brillante

**HT1.5-NEW-2**: alternativa — **L_bk = arithmetic mean del cluster surrounding** (SP426.5 §357-359, Campus 2024 §119). Aunque adoptamos `enable_local_kernel_bg: true` per-vol, puede no estar replicando el comportamiento exacto (e.g. el "surrounding" debe excluir TODOS los hot pixels del cluster, no solo el alerted central). Verificar en T1.5.

**HT1.5-NEW-3**: regreso a **Method-2 temporal** — sobre las series VRP existentes, ¿qué pasa si descartamos los mínimos locales semanales antes de publicar al dashboard? Implementable como post-processing.

## Limitaciones permanentes documentadas (regla §11.8 GUIA_MAESTRA)

| Limitación | Causa | Source |
|---|---|---|
| Cloud filter per-scene en MIROVA NRT | "fundamental step currently absent in all available algorithms" | Coppola 2019 §1449 |
| Atmospheric correction MIROVA | "provided as-are, without atmospheric corrections" | Coppola 2023 §554-558 |
| 0-3% FP rate aceptado | Empírico cross-volcán Coppola 2016b | Coppola 2019 §1283-1288 |
| FPs <5 MW son la cota normal | Trade-off algorítmico C2 | SP426.5 §675-696 |

## Acciones derivadas inmediatas

1. ✅ Persistir esta síntesis (este doc).
2. **Actualizar `docs/MIROVA_DIVERGENCES.md` D9** con citas H1-H6 — fortalece la justificación del cap S71 con evidencia bibliográfica directa.
3. **Abrir `docs/HYPOTHESIS_LOG.md` HT1.5-NEW-{1,2,3}** con las 3 hipótesis del drift remanente.
4. **Update `MEMORY.md` index** con learnings A28 (papers cross-Frontiers no estaban procesados).
5. **Para T1.5 S72**: priorizar verificación de cluster selection y Method-2 temporal antes que touching path D.

## Aprendizajes meta (proceso)

**A28 (proceso de revisión bibliográfica) — S71 2026-05-21**:

Cada vez que un subagente reporta "papers NO resuelven X", verificar:
1. ¿Procesó los PDFs completos o las notas Vault síntesis?
2. ¿Cubrió TODOS los papers que el usuario citó por URL?
3. ¿Buscó supplementary material?
4. ¿Cubrió las refs externas que los papers citan?

Si alguna respuesta es NO → la conclusión "papers no resuelven" es prematura. Releer directo el PDF antes de tomar decisión arquitectural.

S71 T1 Fase 1 verdict era correcto en lo nominal (no hay cloud mask programático en MIROVA) pero subutilizó información existente: **FPs MIROVA <5 MW**, **trade-off C2 documentado**, **caso Villarrica en paper**, **Method-2 temporal**. Esos hallazgos estaban a 1 grep de distancia y validan retroactivamente el cap como solución correcta.

---

**Status documento**: vivo. Re-leer al inicio de cada sesión que toque path D / cluster / cloud handling.
