# Divergencias actuales VRP-Chile vs MIROVA NRT

> Documento vivo. Actualizar cuando se agregue alineamiento o se descubra nueva
> divergencia. Estado al cierre 2026-04-29 (post-S27 análisis CSV consolidado).

## Objetivo

VRP-Chile busca ser un **clon operacional de MIROVA NRT** (objetivo 1) usando
SOLO metodologías documentadas en papers MIROVA (Coppola 2015, 2016a, 2020,
2024, 2025; Campus 2022, 2024; Aveni 2024 RSE; Laiolo 2026). Las divergencias
listadas acá son las que necesitamos cerrar para llegar a "comportamiento
similar a MIROVA".

## Divergencias estructurales

### D1 — Granularidad: MIROVA reporta 1 punto/pasada, nosotros reportamos N pixels

**MIROVA NRT (verificado en CSV consolidado scrapeado de latest.php, S27 2026-04-29)**:
- 14,215 registros distintos en grupos `(timestamp, volcán, sensor)`.
- **100% de los grupos son de tamaño exactamente 1.** Mediana=1, max=1.
- MIROVA emite UN registro por pasada × volcán × sensor, integrando todos los
  hotspots dentro del ROI 51×51 km en un VRP totalizado y un punto representativo.

**VRP-Chile**:
- Cada record JSON contiene un array `anomaly_pixels` con N pixels individuales
  detectados (5-50 típicamente, hasta cap top-100 desde S26).
- `vrp_mw` es la suma sobre el array → equivalente al VRP total MIROVA.
- `final_hotspot_lat/lon` es el pixel primario (el más caliente).

**Estado de cierre**:
- ✅ **Frontend (S27)**: render visual ya alineado — 1 marker/record por default
  ("Solo principal" toggle). Toggle "Todos los pixels" mantiene inspección forense.
- ⚠️ **Data layer**: el JSON sigue conteniendo el array de N pixels. No es
  divergencia metodológica (n_anomalous_pixels es info útil), pero el cruce
  contra MIROVA debe usar siempre `final_hotspot_*` o el primary pixel.
- 🔴 **Cluster aggregation**: MIROVA junta pixels contiguos (~1 km) en clusters
  antes de reportar `n_hotspots`. Nuestro `n_anomalous_pixels` no agrupa.
  Factor empírico observado: ~42× pixels nuestros por cluster MIROVA (S23 T14
  hallazgo, ver `experiments/50_FACTOR_42_HALLAZGO.md`). Implementar cluster
  aggregation es siguiente paso natural alineamiento.

### D2 — Cobertura del CSV ground truth incompleta

**Hallazgo Nicolás 2026-04-29**: el CSV scrapeado de `latest.php` NO está al 100%.
Cobertura estimada: **~70% para VIIRS** (375m y 750m).

**Implicación**:
- Nuestras métricas TP/FN/recall calculadas contra el CSV están sesgadas en
  VIIRS por ese 30% faltante.
- Si MIROVA detectó algo en VIIRS y NO está en el CSV, nosotros lo contamos
  como FP cuando podría ser TP no scrapeado.
- Recall real probablemente **mejor** que el reportado (algunos "FN" son
  detecciones nuestras que MIROVA sí hizo pero no scrapeamos).
- Precision real probablemente **peor** (algunos "TP" pueden ser FPs reales que
  MIROVA marcó pero no scrapeamos como FALSO_POSITIVO).

**Cobertura aproximada por sensor (verificable empíricamente)**:
- MODIS: ~100% (reportado por Nicolás).
- VIIRS 375m / 750m: ~70-80%.

**Pendiente**:
- Re-scrapear con script Mirova-v1 cubriendo gaps temporales.
- Comparar timestamps NRT actuales vs CSV actual para identificar pasadas
  faltantes específicas.

### D3 — MIROVA distingue FP explícito; nuestros JSONs no

**MIROVA NRT publica 4 categorías**:
- `RUTINA` + `NULO` (13,378 = 94%): pasadas sin nada.
- `ALERTA_TERMICA` + `Muy Bajo` (407 = 2.9%): VRP mediano 0.21 MW, dist 2 km.
- `ALERTA_TERMICA` + `Bajo` (165 = 1.2%): VRP mediano 1.79 MW, dist 1.5 km.
- `FALSO_POSITIVO` (253 = 1.8%): VRP mediano 1.56 MW, dist **20.8 km**.
- + 12 records `RUTINA`+`FALSO POSITIVO` (re-clasificación post-hoc).

**Patrón geográfico definitorio MIROVA**:
- Anomalías reales: hotspot a **<2 km del vent**.
- FPs MIROVA: hotspot a **>20 km del vent** mediana.
- Distancia es el criterio principal de FP en MIROVA NRT.

**VRP-Chile**:
- No emitimos categoría "FALSO_POSITIVO" — solo `vrp_mw=0` (no detectó) o
  `vrp_mw>0` con `distance_class={summit,far}`.
- `distance_class=far` es nuestra etiqueta más cercana a "FP" pero no es
  declarativa (no decimos "esto es FP", decimos "está fuera del summit").

**Validación cruzada (S27 2026-04-29)**:
- 234 FPs MIROVA en 10 Tier A.
- Solo **24 son FPs nuestros reales** (mismo hotspot, ±5 km dist).
- 47 son eventos distintos (MIROVA detectó FP a 20 km, nosotros detectamos
  cráter — son cosas diferentes en la misma pasada).
- 163 NO los detectamos (nuestro literal filtra mejor que el operacional con
  parches habría visto).
- De los 24 FPs reales: **23 quedan como `far`** ✓ correctos. **1 cuela como
  `summit`** (Tupungatito 2026-02-17, marginal).

### D4 — Cobertura de eventos: recall estratificado MIROVA por nivel

**Recall del literal puro 90d (post-S27, vs CSV consolidado)**:
- Nivel **"Bajo" (eruptivo, 1.79 MW mediano)**: 65% recall (92/141). Aceptable
  para operacional.
- Nivel **"Muy Bajo" (sub-pixel, 0.21 MW mediano)**: 60.7% recall (222/366).
  Bimodal extremo:
  - PCC 97% (inner_radius_km=20 grande).
  - Isluga 80%, Chaitén 73%, Tupungatito 72%, Lascar 71%.
  - **Lastarria 8%** (inner=5).
  - **PlanchónPeteroa 4%** (inner=3).

**Hipótesis abierta** (S28+): el colapso de recall en Lastarria/Planchón
correlaciona con `inner_radius_km` chico. PCC con inner=20 captura 97% mientras
Planchón con inner=3 captura solo 4%. Pendiente investigar si subir
`inner_radius_km` lo recupera **o** si MIROVA usa un mecanismo distinto que
todavía no replicamos.

### D5 — Magnitudes (ratio VRP)

**Estado pre-S27 operacional (con parches)**: ratio mediano `vrp_nuestro / vrp_mirova` = **70×**.

**Estado post-S27 literal puro**: ratio mediano = **1.35×**. Mejora drástica.

> ⚠️ **SIN RESPALDO PARA HOY — S125.** Este "1.35×" (sobre-reporte) describe un estado
> de S27, hace ~100 sesiones y antes de nadir-fijo (S102/S103), la ancla honesta (S98) y los
> gates OFF (S118). La tabla de brazos de hoy (`experiments/_s124_f70/04_tabla_brazos.py`)
> da mediana ≈**0,75×**, o sea **sub-reporte** — el signo opuesto. Esta divergencia marcada
> como resuelta describe, invertido, el frente principal abierto de S125. Rebajada de
> "calibración lograda" a **abierta pendiente de re-medición**. Ver
> `docs/AUDIT_S125_PROFUNDA.md` §0 y §3.

**Causas pre-S27 sobreestimación**:
- Vent-path reportaba VRP de pixels marginales sub-umbral.
- `MAX_SIGMA_COMPONENT_K=7K` mantenía thresholds bajos sobre detecciones que
  MIROVA descartaba.
- Pisos VRP por sensor empujaban magnitudes.

**Estado**: ✅ Calibración de magnitud lograda. Ratio 1.35× es excelente para
paridad MIROVA estricta.

### D6 — TIFs `mirova-tif-archive` son visualización de campo, no VRP per-pixel sumable

**Fenómeno físico**: los TIFs publicados por el repo `MendozaVolcanic/mirova-tif-archive`
(scraper paralelo que cada 5 min levanta los productos visualizables de la web MIROVA)
contienen el **campo continuo de radiancia/anomalía** sobre el ROI 50×50 km del volcán,
no un raster sparse donde cada pixel sea VRP per-pixel sumable. Pensar el TIF como "lo
que el dashboard MIROVA pinta en el mapa" — gradiente del campo térmico, no lista de
hotspots discretos.

**Observación operacional**: si uno suma ingenuamente todos los pixels del TIF (o
incluso el top-N global), obtiene una magnitud que sobrepasa lo que MIROVA publica en
el header del producto por **un factor de ~10×**, y el centroide así calculado cae a
distancias muy lejos del cráter porque el campo se extiende por el ROI completo.

**Evidencia (S70-0 T3 Parte 1, commit `b8408ac`)**: 5 ALERTAs Lastarria recientes
auditadas:
- Ratio mediano `top10_pixels_sum / MIROVA_CSV_VRP` = **11.5×** (rango 7.9-21.9×, n=5).
- Drift mediano centroide top10 (sin filtro espacial) vs coordenadas CSV NRT =
  **10.9 km** (vs distancias MIROVA típicas 1-3 km del vent).
- Los TIFs tienen **>99% de pixels positivos** en rango 0.035-0.10 (campo continuo,
  no raster sparse de hotspots).

**Origen del hallazgo**: commit local s15-dev `64bd37d` (S33+ cierre) sobre Lascar
detectó un TIF con 17,911 pixels positivos sumando 1680 MW, mientras el header MIROVA
del mismo producto reportaba "VRP: 0.2 MW @ 9.7 km". El factor ~10⁴× sobre Lascar y el
factor ~10× sobre Lastarria son consistentes con la lectura "campo de radiancia
visualizable, no scene-wide sumable".

**Cómo usar el TIF correctamente** (S70-0 T3 Parte 2, commit `3ead58d`):
- Para **magnitud**: NO sumar pixels del TIF. Usar `pc.vrp_mw` (output de NUESTRO
  pipeline, ya filtrado a `primary_cluster`) vs `MIROVA CSV NRT`. Ambos son productos
  ya filtrados, comparables 1:1.
- Para **geometría**: usar TIF top10 pixels ponderado **con filtro espacial obligatorio
  `<3km del vent`**. El filtro espacial es lo que convierte un TIF "no sumable
  globalmente" en un ground truth útil para validar el centroide LOCAL del cráter.
  Sin ese filtro, el field bleed scene-wide contamina el centroide.

**Caso replicado contra S69**: Lastarria 2026-05-14 05:48 UTC VIIRS375 (el mismo caso
del agente S69):
- Ratio magnitud `pc.vrp_mw / MIROVA_CSV` = **1.05×** exacto.
- Drift centroide TIF top10 (<3 km del vent) vs `pc.centroid` = **1.04 km**.
- Target S69: ratio 1.05× y drift 0.752 km. Ambos drifts <2 km tolerancia.

**Implicación operacional**: el R2 retroactivo Chaiten/PCC/Villarrica/PP planeado para
S70-1 puede usar con confianza el método R2 S69 verdadero, porque ese método NO suma
pixels del TIF como VRP. El patrón replicable de 5 pasos está documentado en
`experiments/120_audit_tif_vrp_sumable/README.md` Parte 2.

### D7 — Método R2 retroactivo tiene aplicabilidad limitada por régimen del vol

**Fenómeno físico**: el método R2 retroactivo S69 calcula un centroide ponderado de los top-N pixels TIF dentro de un radio del vent y compara contra `pc.centroid` (output del pipeline). Esto funciona bien cuando el "cluster activo" del vol es **focal y puntiforme** (un cráter compacto con señal térmica concentrada). Cuando el cluster es **difuso o extendido**, el centroide ponderado del campo no representa ningún cluster discreto y el "drift" resultante es artefacto del método, no error del pipeline.

**Casos observados (S70-1 T1-T4)**:
- **Focales puros (Lastarria)**: R2 PASS limpio. Drift <1.1 km.
- **Focales con cola térmica difusa (Chaiten, Villarrica, PP)**: R2 PASS bajo gates revisadas. Drift 2.0-2.2 km — el ruido es el halo termal del lava lake / domo activo, no error del cluster.
- **No focales / difusos (PCC lacolito Cordón Caulle)**: R2 con drift NO APLICA. La intrusión 2011 cubre ~707 km² sin pico claro; el centroide del campo está a 9-10 km del cluster MIROVA (que también es difuso).

**Cómo identificar régimen del vol antes de aplicar R2**:
- ΔT máxima del vol >20 K + cluster típico <2 km² → focal puro, R2 con drift `<2 km` aplicable.
- ΔT <12 K + cluster <5 km² → focal con halo, R2 con drift `<3 km` aplicable (gates revisadas).
- ΔT bajo + cluster >50 km² (intrusión, lacolito, domo extendido) → NO focal, R2 con drift NO aplica. Validar adopción por magnitud (ratio per-record vs agregado) + confirmar geometría (cluster nuestro EN la zona difusa).

**Bandas gates por régimen** (referencia operacional):

| Régimen | Ratio in band | Drift |
|---|---|---|
| Focal Tier A Alto (Lastarria, Lascar, Isluga) | [0.5, 2.0] | <2 km |
| Focal Tier A Muy Bajo (Chaiten, Villarrica, PP) | [0.5, 2.0] preferida | <3 km |
| No focal (PCC lacolito) | — | R2 no aplica; usar magnitud agregada |

**Implicación**: R2 retroactivo es herramienta válida pero NO universal. Antes de aplicarla a vols nuevos en S70+ o futuras adopciones, clasificar régimen.

**Referencias**: `experiments/120_audit_tif_vrp_sumable/`, `experiments/122-125/`, H_S70_R2_RETROACTIVO_4VOLS.

### D9 — Path D (dNTI contextual) dispara FPs y amplifica magnitud en cirrus alto frío

> Nota: D8 está reservado en este doc para la entrada histórica "Background ring contaminado — RESUELTO" (S60-S62). Esta es D9.

**Fenómeno físico**: en invierno austral, los volcanes del norte de Chile (Lastarria, Lascar, Isluga) sufren cobertura frecuente de **cirrus alto** (nubes finas a -25/-30°C, ~10 km altitud). Estas nubes son transparentes a la radiación térmica del volcán pero **enfrían el background MODIS** de los pixels vecinos a 245-270 K. El pixel del cráter (que irradia a su temperatura normal ~270 K) aparece **+25 K relativo al fondo enfriado**, disparando el path D dNTI contextual como anomalía. La fórmula Wooster `vrp_mw = 18.9 × A_pix × BT⁸` aplicada sobre BT=270 K produce un número grande **aunque NO hay radiación volcánica anómala** — es contraste térmico nube-roca amplificado por la potencia 8 de Wooster.

**Evidencia (S70-2 T4, cross-check 32 records Lastarria summit eqVrp>5 vs MIROVA NRT)**:
- 22/32 (68.8%) son **FPs nuestros confirmados** — MIROVA NO reporta ALERTA en esos timestamps (6 RUTINA explícita, 16 sin record MIROVA del granule).
- 10/32 (31.2%) son TPs reales pero **amplificados 21-150× sobre MIROVA** (ratio mediano 62×). Sugiere que path D suma pixels marginales que MIROVA descarta del cluster.
- **100% de los 32 records** disparan exclusivamente por path D (`diag_n_bt_path=0, diag_n_nti_path=0, diag_n_dnti_ctx_path` en 8-49).
- **91% (20/22) FPs** tienen `t_bg < 270K` (cirrus frío). Mediana FPs t_bg = 268.5 K.

**Doble modo de falla**:
1. **Firing espurio** sobre cirrus (predominante 91% FPs).
2. **Amplificación en TPs** (10 casos donde MIROVA y nosotros coincidimos en detección, pero magnitud nuestra 21-150× sobre MIROVA).

**Reconciliación con adopción S62 Lastarria**: la mediana global S62 (ratio 1.07× sobre 99 ALERTAS) es válida — la distribución es bimodal y la cola baja domina la mediana. La cola alta (32 records con path D firing) NO está calibrada y es lo que aparece en el dashboard como 20-30 MW.

**Generalización**: Lascar e Isluga comparten granules MODIS con Lastarria en algunos casos cirrus regional (S69 H_S69_MODIS_OUTLIERS_05_17 documentó patrón similar para Villarrica+Chaiten). PP/Tupungatito/PCC probable similar en granules con t_bg <270K.

**Path D es S15 P3.2** (`enable_dnti_contextual_path: true` en `mirova_equivalent.yaml`). Coppola 2016a §SP 426.5 introduce dNTI contextual como gate adicional, **sin discutir comportamiento en cirrus**. Nuestra implementación carece de gate atmosférico.

**Cómo fixear** (NO implementado — regla S33 vinculante, brainstorming obligatorio antes de tocar `enable_*`):
- **Opción 1**: gate atmosférico — `if t_bg_k < 260 K, skip path D` (o umbral a calibrar empíricamente).
- **Opción 2**: requerir co-validación — path D solo cuenta si BT path O NTI path también dispararon (no path D solo).
- **Opción 3**: cap de magnitud — limitar `pc.vrp_mw` a un máximo razonable cuando solo path D firing.

Cualquier fix requiere A/B test con profile flag aislado (`mirova_equivalent_path_d_atm_gate_v1.yaml` o similar) sobre Tier A completo + R2 pixel-level vs MIROVA antes de adoptar.

**Referencias**: `experiments/121_nrt_cron_diagnosis/diagnosis.md` (T1 NRT cron), `H_S70_PATH_D_CIRRUS_FP` (HYPOTHESIS_LOG), CSV cross-check `/tmp/cross_check_results.json`.

#### S71 T1 Fase 1 — verdict papers-first (2026-05-20)

Subagente Explore revisó 5 papers MIROVA canónicos buscando tratamiento explícito de cirrus / fondo frío / cloud mask previo a path D dNTI ctx:

| Paper | ¿Resuelve D9? | Hallazgo |
|---|---|---|
| Coppola 2016a §SP 426.5 | NO | Define dNTI ctx + umbrales C1/C2 + filtro `dNTI<−0.1`. Sin cloud mask previo, sin gate t_bg. Caso Gaua p.17: "<2% FPs, siempre <5 MW" — interpretativo post-hoc, no gate algorítmico. |
| Coppola 2016b enhanced | NO | Sin discusión cirrus / fondo frío. |
| Campus 2024 thermal | NO | MIR captura solo 1-2% flujo hidrotermal real; no toca FPs dNTI sobre fondo frío. |
| Coppola 2024 cap Springer | NO | "MIROVA uses spectral + contextual" sin detalle de adaptación a escenas anómalas. Tabla 3 lista 19 sistemas NRT sin paso cloud mask explícito. |
| Aveni 2024 RSE TIRVolcH | NO | Problema TIR baja-T, no MIR cirrus. VSROI + R²>0.5 son filtros distintos. |

**Verdict**: papers MIROVA **NO resuelven D9 explícitamente**. Ningún cloud mask documentado, ningún gate t_bg, ninguna co-validación obligatoria. La única pista publicada es interpretativa (Coppola 2016a Gaua: <5 MW Tier A sospechoso).

**Implicación operacional**: proceder a Fase 2 — A/B test 3 alternativas (Opción 1 atm gate, Opción 2 co-validación, Opción 3 cap magnitud) con profile flag aislado. Decisión metodológica Nicolás S70-2: "probar diferentes alternativas hasta llegar a la réplica de MIROVA".

#### S71 T1 Fase 2 — A/B + adopción Opción C (2026-05-21)

3 reprocs A/B sobre 11 vols Tier A ventana 2026-02-20 → 2026-05-20 (PRs #103-#111, merged). Cada opción en profile aislado + audit cruzado vs MIROVA NRT CONS+OCR.

| Opción | Bug D9 count (vrp>5MW pD-only @ t_bg<260K) | Recall preservado | Adopción |
|---|---|---|---|
| baseline | 237 | — | (anterior) |
| A — atm gate t_bg<265K | **0** ✅ | 7/7 (NdC pierde 1 noche) | NO (ortogonal a C) |
| B — co-validación BT/NTI | 1 (Copahue residual) | **NdC colapsa 1.00→0.33**, Lastarria 0.99, PCC 0.96 | NO (rompe recall) |
| **C — cap 5MW @ t_bg<270K** | **0** ✅ | **7/7** sin perder ninguna noche | **SÍ — adoptado S71** |

**Validaciones regla S33 vinculante (cumplidas antes del push)**:
- **R1** tests sintéticos: 20/20 PASS (`tests/test_path_d_d9_fix.py`).
- **R2** pixel-level vs TIFs MIROVA archive sobre 20 records muestreados: **0 cap leaks**. Máximo MIROVA en records capeados = 0.21 MW. El cap NO enmascara magnitudes reales MIROVA >5MW. Detalle en `experiments/131_r2_pixel_level_optC/`.
- **R3** audit independiente sensor-aware ±60min (vs ±3h del primario): **COINCIDE**. C winner con 4/11 vols en ratio target (más fuerte que 2/11 primario). Detalle en `experiments/130_r3_audit_independent_optC/`.

**Adopción S71** en `pipeline/profiles/mirova_equivalent.yaml`: `path_d_only_cap_mw: 5.0` + `path_d_only_cap_tbg_max_k: 270.0`.

**Cobertura física**: el cap acota magnitudes en cirrus alto (Wooster BT⁸ sobre fondo frío inflaba 20-150×). Ahora la magnitud máxima publicable en escena contextual-only + cirrus es 5 MW, alineado con Coppola 2016a Gaua "<5 MW Tier A sospechosos" y con el máximo MIROVA empírico en records que el cap atrapa (0.21 MW).

**Estado D9 — PARCIALMENTE RESUELTO**: mitigación defensiva adoptada. Cubre 100% del bug original (records con magnitud absurda en cirrus). **Causa raíz arquitectural sigue ABIERTA** — ratios post-cap siguen 24-83× cuando MIROVA presente en cirrus. Drift remanente afecta Villarrica/Chaiten/PP/Tupungatito/NdC con ratios 6-12× independiente del cap. Hipótesis preliminar: cluster selection / first_pass re-firing. Investigación papers-first → **T1.5 abierta S72**.

**Aprendizaje S71 — A27 (regla operacional)**: el matching audit ±3h por noche oculta pérdidas de recall que aparecen con matching sensor-aware ±60min. Lascar y PCC pierden recall significativo (0.72→0.43, 0.96→0.87) post-fix path D — no detectado por audit primario, sí por R3. Para vols con muchas alertas MIROVA, usar matching estricto sensor-aware en auditorías futuras.

#### S71 revisión exhaustiva papers MIROVA — citas bibliográficas directas para D9 (2026-05-21)

> Trigger: Nicolás reportó que la Fase 1 leyó solo notas Vault, no PDFs completos. Esta sub-sección documenta las citas exactas que validan el cap S71 y reformulan D9 con autoridad bibliográfica.

**Coppola 2016 SP 426.5 §247-249** (book chapter Geological Society of London):
> *"the presence of clouds is not taken into account by the algorithm and all eight neighbouring pixels are used to compute the spatial average. This is a simple spatial filtering that does not take into account the type of surface imaged by each pixels (e.g. land, sea, clouds), just 'its variability with respect to the surroundings'."*

**Coppola 2016 SP 426.5 §675-696** (sección "False alerts" — base bibliográfica directa del cap 5 MW):
> *"these false detections typically radiate **less than 5 MW** and can be easily identified by a visual inspection of the associated NTI map ... reducing the false detection rate will cause numerous genuine alerts of low intensity (<10 MW) to be missed"*

**Coppola 2016 SP 426.5 §712-728** (sección "Meteorological and volcanic clouds"):
> *"there is, as yet, **no robust method** to evaluate the amount of thermal radiation attenuated by clouds, or volcanic plumes, so that visual inspection of the image still remains the best solution ... the RP time series obtained by MIROVA are provided **'as they are'**"*

**Coppola 2016 SP 426.5 Fig. A6** (caso Villarrica explícito en paper):
> *"Villarrica volcano (Chile) ... The clear thermal contrast between the ice-covered summit ... and the Villarrica lake ... is clearly visible on the NTI and NTIbk. However, a very small thermal anomaly (NTI ≤ -0.93) at the summit of Villarrica is easily detected after performing the spatial filtering (dNTI and dETI). **Note how the warm lake surface almost disappears in the ETI map**"*

→ Demuestra el mecanismo de defensa MIROVA: ETI = NTI − NTIbk (con regresión cuadrática per-imagen) absorbe contrastes regionales (lago, cirrus). Implementado en VRP Chile vía `pipeline/detection_context.py:compute_nti_and_nti_app` (`np.polyfit(x, y, 2)` + iterative re-fit, Eq.4 SP426.5). ✅

**Coppola 2019 Frontiers §1283-1288** (tasa empírica FPs MIROVA):
> *"a smaller but variable percentage of false alerts, **generally comprised between 0 and 3%** ... at different volcanoes (Coppola et al., 2016b). These false alerts depend on the regional and local environmental conditions as climate, elevation, topography and land cover type"*

**Coppola 2019 Frontiers §1443-1480** (sección "Image Quality Assessment"):
> *"any hot spot detection system should be able to quantify the effects of clouds and viewing geometry condition, within each acquired image. **This fundamental step is currently absent in all available algorithms** ... Quantification of cloud attenuation on a pixel per pixel basis would be an ideal solution **(Koeppen et al., 2011)**, but this would require the collection and analysis of many more bands ... A promising solution is provided by **machine learning (i.e., Valade et al., 2019)**"*

**Coppola 2023 Frontiers §554-558** (base de datos 2000-2019 "as-are"):
> *"the VRP data provided by MIROVA are provided **'as-are', i.e., without atmospheric corrections and cloud fraction estimates** accompanying the measurement"*

**Coppola 2023 Frontiers §530-540** (mecanismo MIROVA Method-2 — NO implementado en VRP Chile):
> *"**local VRP minima are removed from the weekly subset**, before performing the weekly energy calculation ... tends to **reduce the effect of cloud contamination**"*

→ MIROVA tiene **post-processing temporal** (Method-2) que VRP Chile NO replica. Es candidato para T1.5 S72 (drift remanente).

#### D9 — verdict reforzado con bibliografía directa

El cap 5 MW (Opción C) **NO es un parche** — es la implementación programática del trade-off explícitamente documentado en Coppola 2016a §675-696: *"these false detections typically radiate less than 5 MW"*. La adopción S71 está respaldada por:

1. **Cita literal**: FPs MIROVA típicos <5 MW (SP 426.5 §687).
2. **Confesión MIROVA**: cloud filter per-scene "ausente en todos los algoritmos" (Coppola 2019 §1449).
3. **Database 2023**: data MIROVA OSF v2.5 entregada "as-are" sin atmospheric corrections (Coppola 2023 §554).
4. **Mecanismos MIROVA que SÍ tenemos implementados**: NTIbk regresión cuadrática (Eq.4), ETI = NTI − NTIbk (Eq.5), Tests 2 ∧ 3 (dNTI ∧ dETI) con C2·σ auto-adaptive (Tabla 1: C2=5 summit / 10 scene).
5. **Mecanismos MIROVA que NO tenemos**: Method-2 weekly local minima removal (Coppola 2023 §537), QC visual a posteriori (Coppola 2016a §367, 2019 §1444). El cap 5 MW reemplaza programáticamente el QC visual que MIROVA hace manualmente.

#### Drift remanente — hipótesis nuevas derivables de la lit (T1.5 S72)

**HT1.5-NEW-1 (cluster selection)**: MIROVA agrega Σ ALL alerted pixels scene-wide (SP 426.5 Eq.8: `RP = Σ RP_PIX`, Coppola 2024 Eq.13: `ΔL_tot = Σ_{k=1}^{N_pix} ΔL_k`). Nuestro pipeline selecciona `primary_cluster` cerca del vent. En escenas Muy Bajo régimen donde MIROVA agrega N pixels distribuidos, nosotros podemos amplificar al elegir el cluster más brillante.

**HT1.5-NEW-2 (background del kernel)**: aunque `enable_local_kernel_bg: true` adoptado S61 (kernel 3×3 vecinos), verificar que excluye **todos** los hot pixels del cluster (SP 426.5 §357-359: *"L4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or **around the active cluster**)"*). Si solo excluye el alerted central pero no los otros del cluster, el background queda contaminado.

**HT1.5-NEW-3 (post-processing temporal)**: implementar Method-2 MIROVA — descartar mínimos locales semanales antes de publicar al dashboard. No es algorítmico per-scene, es post-processing per-vol per-semana.

#### Refs externas para perseguir (T1.5 / S72+)

| Ref | Aporte declarado | Relevancia D9/drift |
|---|---|---|
| **Koeppen et al. (2011)** | Quantification cloud attenuation pixel-per-pixel | Alta — solución ideal según Coppola 2019 (no implementada por MIROVA) |
| **Valade et al. (2019)** | ML cloud filter sistema MOUNTS | Alta — alternativa moderna (no implementada por MIROVA) |
| **Coppola et al. (2010)** | Effect of unfavorable geometric conditions on VRP | Media — viewing geometry |
| **Coppola et al. (2013)** | Cloud contamination effect on time series | Media |
| **Galetto et al. (2023)** | Database global eruptions vs MIROVA detection | Media — validation |

Status doc: vivo. Síntesis exhaustiva completa en `docs/PAPERS_MIROVA_SYNTHESIS_S71.md`.

#### A28 (aprendizaje meta de proceso S71)

Cuando un subagente reporte "papers NO resuelven X", verificar antes de aceptar:
1. ¿Procesó PDFs completos o solo notas Vault síntesis (~100-200 líneas)?
2. ¿Cubrió TODOS los papers que el usuario citó por URL?
3. ¿Buscó supplementary material?
4. ¿Cubrió refs externas que los papers citan?

Si alguna respuesta es NO → la conclusión es prematura. Releer directo el PDF antes de tomar decisión arquitectural. El verdict S71 T1 Fase 1 era correcto en lo nominal pero subutilizó información que estaba a 1 grep de distancia (FPs MIROVA <5 MW, trade-off C2 documentado, caso Villarrica en paper, Method-2 temporal).

**Referencias**: `experiments/127_path_d_tbg_calibration/`, `experiments/128_path_d_ab_audit/`, `experiments/130_r3_audit_independent_optC/`, `experiments/131_r2_pixel_level_optC/`.

#### S71 expansión revisión — Massimetti 2024 + Laiolo 2017 procesados (2026-05-21)

Procesamiento exhaustivo de 2 papers MIROVA-canónicos adicionales identificados en auditoría:

**Massimetti et al. 2024** JGR Solid Earth "Thermal Emissions of Active Craters at Stromboli — Spatio-Temporal Insights" (`documentacion/massimetti2024_stromboli.md`, 1966 líneas):

- **VTF definida** (`:230-232`): *"the magnitude and spatial information of any **Volcanic Thermal Feature (VTF; hereby defined as a sub-pixel spatial element with temperatures above the background)**"*. Unidad operativa MIROVA: sub-pixel element, NO cluster ni pixel.

- **MIROVA MIR usa geofencing 5 km + sum scene-wide** (`:561-562`): *"considering only alerts within a maximum distance of **5 km from volcano summit**"*. Confirmado para Stromboli. Para Andes los KMZ MIROVA usan box 50×50 km — pregunta abierta sobre filtro exacto en volcanes grandes.

- **MIR sin ROI per-crater** (`:801-832`): los 3 ROIs Stromboli (NE, C, SW) **se definen exclusivamente con SWIR 20m** (Sentinel-2/Landsat). En MIR (MODIS/VIIRS) el crater terrace se trata como una sola unidad. **→ HT1.5-NEW-1 VALIDADA**: MIROVA no selecciona primary_cluster en MIR.

- **MIROVA NO filtra cirrus en MIR** (`:573-575`): *"VIIRS MIR images represent a data set that is **not corrected for the acquisition conditions**, but it simply expresses a measurement of the thermal radiation reaching the MIR sensor as it is, **possibly including clouds and geometry effects**"*. **CONFIRMA D9 como limitación heredada, no bug propio**.

- **Threshold MIR uniforme** (no per-crater) — algoritmo Coppola 2016/Campus 2022 sin modificación per-vent.

- **Alert rate Stromboli MIR 39.8%** (`:597-598`): 2,696 / 6,772 overpasses. Reference rate para volcán muy activo.

**Laiolo et al. 2017** JVGR 340 "Evidences of volcanic unrest on high-temperature fumaroles by satellite thermal monitoring: The case of Santa Ana, El Salvador" (`documentacion/laiolo2017.md`, 988 líneas):

- **Sensibilidad nativa MIROVA = 1 MW floor** (`:208-213`): *"MIROVA combines a moderate temporal and spatial resolution (4 images per day; 1 km pixel resolution) with a **high efficiency in detecting small hotspots (~1 MW)**"*. Confirma que **NO se requiere C2 distinto per-régimen Muy Bajo** — sensibilidad nativa ya cubre fumaroles.

- **Detección fumaroles 1.6 MW** (`:325-330`): primer thermal alert Santa Ana = **1.6 MW** (Sept 21, 2004). Detectable desde **fumarole field** (NO lava, NO magma).

- **🚨 HALLAZGO CRÍTICO — lago cráter NO emite señal MIR detectable** (`:336-338`): *"In spite of the persistence of moderately high level of activity at the adjacent fumaroles (e.g. degassing), **no significant anomalous signals were observed in the temperature of the water lake**"*. En Santa Ana, MIROVA detecta los fumaroles laterales del rim, no el lago central.

**HT1.5-NEW-4 (NUEVA, derivada de Laiolo 2017)**: en volcanes Tier A Muy Bajo con lago cráter / lacolito / dome cooling (Villarrica, PCC, Chaiten), nuestro `vent_lat/lon` puede apuntar al **lago/dome geométrico** mientras la señal MIROVA real viene de **fumaroles del rim/flanco adyacente**. Si esto se confirma con un audit de coords vent vs centroides MIROVA observados, **el drift remanente sería geométrico, no algorítmico** — fix sería actualizar coords (similar S62 Tupungatito mirova_center fix). Verificable barato: cruzar coord vent con centroide records MIROVA NRT en cada vol Tier A Muy Bajo.

#### Orden de implementación T1.5 (decisión metodológica derivada)

Subagente identificó dependencia crítica:

> *"el orden correcto es **fix D9 primero (filtrar cirrus) → después adoptar scene-wide aggregation**. NO al revés."*

Razón: aplicar scene-wide aggregation sin filtro cirrus = D9 amplificado (sumamos más pixels FP scene-wide). El cap S71 debe seguir activo antes/durante migración a scene-wide. Esto valida la secuencia S71 (cap primero) → T1.5 (scene-wide después).

#### Refutación: thresholds NO son el problema

Laiolo 2017 prueba que MIROVA detecta fumaroles 1.6 MW con threshold standard. **Si nuestro pipeline falla en detectar señales 1-2 MW en Villarrica/PCC/Chaiten, el problema NO es C2/σ ni umbral — es geometría del cluster o cálculo de background o coord vent**. Esto descarta el sub-camino "tunear thresholds per-régimen" del plan T1.5.

#### Validación HT1.5-NEW-1/2/3/4 vs literatura

| Hipótesis | Veredicto post-Massimetti/Laiolo | Cita |
|---|---|---|
| HT1.5-NEW-1 (scene-wide vs primary cluster) | **VALIDADA** | massimetti2024:561-562, 801-832 |
| HT1.5-NEW-2 (L_bk excluye TODOS hot pixels) | PARCIAL — requiere lectura Campus 2022 detallada | massimetti2024:620 (referencia genérica) |
| HT1.5-NEW-3 (Method-2 weekly local minima) | SOPORTADA INDIRECTAMENTE | massimetti2024:914-916 (weekly aggregation) |
| **HT1.5-NEW-4 (coord vent vs fumarole rim)** | **NUEVA — verificar audit** | laiolo2017:336-338 (Santa Ana lake vs fumaroles) |

#### Auditoría Vault MIROVA-canónicos — verdict global

8 autores canónicos (Coppola, Laiolo, Massimetti, Campus, Aveni, Cigolini, Ripepe, Delle Donne):
- **6 papers procesados exhaustivos**: Coppola 2025 book, Coppola 2023, Campus 2024, Aveni 2025, Coppola 2022 Sabancaya, Campus 2022 transición VIIRS.
- **2 papers procesados S71** (este bloque): Massimetti 2024, Laiolo 2017.
- **3 Frontiers/SP426.5/2019/2023 procesados S71**: cubre core MIROVA NRT algorithm.
- **Sin gap real Cigolini**: retirado del frontline desde 2022 (confirmado triangulación Crossref+S2+OpenAlex). Papers 2022 Sabancaya y EPSL ya cubiertos.
- **Supplementary Coppola 2019 bajado**: Data_Sheet_1.pdf + Table_1.xlsx + Table_2.xlsx (665KB + 16KB + 20KB).
- **Supplementary Coppola 2023**: NO hay on Frontiers — apunta a OSF zm62w que YA tenemos en `data/mirova_reference/`.

**Conclusión bibliográfica S71**: tenemos cobertura MIROVA-canónica funcional para todas las decisiones T1.5+. Refs externas Valade 2019 (MOUNTS ML) bajadas para "futuras implementaciones" no-MIROVA; Koeppen 2011 paywall pero no es paper de cloud-filter exclusivo (es time-series hybrid, ya cubierto conceptualmente por Method-2 Coppola 2023).

#### S71 Fase 1 audits — verdicts cerrados (2026-05-21)

Ejecución sistemática del catálogo de divergencias (`docs/MIROVA_DIVERGENCES_CATALOG_S71.md`). 5 subagentes paralelos sobre 5 hipótesis priorizadas:

| Audit | Hipótesis | Verdict | Acción derivada |
|---|---|---|---|
| **F1.1** | HT1.5-NEW-4 coord vent vs centroide MIROVA fumarole rim | ❌ **REFUTADA 4/5 vols** (Villarrica/Chaiten/PCC/PP: p50 < 1 km del vent yaml; rumbo coincidente con cráter activo). Único caso real: **Tupungatito (CONS NRT p50 = 5.21 km SE)** → re-abrir decisión S65 PR #93 | F1.6 — propuesta de coord nueva |
| **F1.2** | NEW-7 + NEW-8 — Test 1 K1 retire + edge/dNTI<-0.1/dETI<-0.1 unsuitable | ⚠️ **PARCIALMENTE RECLASIFICADO S100**: el gap (1) NEW-7 (`enable_test1_k1_retire_from_hot_mask`) era una **LECTURA EQUIVOCADA** — ver nota S100 abajo: "discarded (unsuitable) for further steps" (SP 426.5 §298-300) = sacar los Test 1 del **pool estadístico** (los `suitable pixels` de §326-329 que alimentan m,σ de Tests 2/3), NO del **reporte de detecciones**. Nuestro código (flag OFF, los Test 1 entran al hot_mask reportable) **ya es fiel**. **Mantener OFF permanentemente.** Los gaps (2)(3)(4) NEW-8 (edge/dNTI<-0.1/dETI<-0.1) **siguen vigentes** — esos sí son sobre el pool estadístico de m,σ (§267-273), naturaleza distinta del malentendido | NEW-7 cerrado; NEW-8 (gaps 2-4) sin cambio |
| **F1.3** | HT1.5-NEW-2 — L_bk kernel excluye TODOS hot pixels del cluster | ✅ **PASS** — `pipeline/vrp_regimes.py:compute_local_background` (líneas 21-89) excluye correctamente `hot_set = set(zip(hot_rows, hot_cols))`. Test sintético `test_two_adjacent_hot_pixels_each_excludes_the_other_hot` confirma | Descartado como causa drift |
| **F1.4** | NEW-5 — geofencing 5 km Stromboli aplica en Andes | ❌ **REFUTADO**. 21.79% records OSF v2.5 chilenos > 5 km del vent; cap empírico ~30 km coincide con `r_circunscrito` box MIROVA 51×51 km. La regla S14 (`radius_km=25 km` uniforme) cubre 98.27% records — empíricamente óptima. Stromboli 5 km es contexto isla pequeña, NO transferible | NO cambiar geofencing actual |
| **F1.5** | NEW-6 — reproducir Villarrica 24-Jun-2009 Fig. A6 SP 426.5 | ⏸️ **GAP OPERATIVO**: granule MODIS Terra/Aqua 2009-06-24 04:10/05:55 UTC disponible vía Earthdata pero pyhdf roto en Windows + falta instrumentación dump rasters NTI/NTIbk/dNTI/ETI. Costo: ~2h instrumentación + workflow GH Actions | Aplazado — no urgente |

##### Nota S100 (2026-06-03) — NEW-7 / Drift #1 reclasificado: lectura equivocada

Verificación verbatim (A35) del texto SP 426.5 durante S99/S100, concordada con
Nicolás. El gap (1) de F1.2 (`enable_test1_k1_retire_from_hot_mask`) nació de leer
SP 426.5 §298-300 — *"Pixels that satisfy Test 1 are flagged as `active' and
subsequently discarded (unsuitable) for further steps"* — como "los Test 1 NO se
reportan". **Es incorrecto.** La frase clave está en §326-329: *"m and s are the
arithmetic mean and standard deviation **of all the suitable pixels** within the
image"*. "discarded (unsuitable) for further steps" significa que los pixels Test 1
quedan **fuera del pool estadístico** que alimenta m y σ de los tests contextuales
(Tests 2/3) — exactamente el mismo mecanismo, y con la misma palabra "unsuitable",
que §267-273 aplica a edge/dNTI<-0.1/dETI<-0.1 (NEW-8) y que el kernel de fondo ya
aplica a los hot pixels (F1.3, PASS). Los pixels Test 1 **son** las detecciones
fuertes y SÍ se reportan; sacarlos del `hot_mask` reportable (lo que haría el flag)
sería un drift, no un fix. **Decisión: `enable_test1_k1_retire_from_hot_mask` queda
OFF permanentemente; el código actual ya es fiel.** Esto NO afecta a NEW-8 (gaps
2-4), que sí es sobre el pool estadístico de m,σ y sigue su propio curso.

Lección de método (regla verbatim MISSION.md S99): un paper que *menciona* un paso
no implica que el SISTEMA NRT de MIROVA lo aplique al reporte; y "for further steps"
en SP 426.5 se refiere a los pasos estadísticos subsiguientes (m,σ), no al output.

##### Causa MÁS PROBABLE del drift remanente (post-Fase 1)

Los **4 gaps documentales F1.2** explican mejor el drift remanente Villarrica/Chaiten/PCC/PP que las otras hipótesis (descartadas):

- HT1.5-NEW-4 (coord) → descartada para 4 de 5 vols.
- HT1.5-NEW-2 (kernel L_bk) → ya correcto.
- NEW-5 (geofencing) → ya óptimo.

**Razonamiento físico-algorítmico**: si pixels con dNTI<-0.1 o dETI<-0.1 (típicamente cirrus o lagos fríos con anomalía NEGATIVA) entran al cálculo de `m` y `σ` de Tests 2/3, **inflan σ artificialmente**. El threshold `m + C2·σ` queda alto, permitiendo que pixels que MIROVA descarta entren a nuestro firing. Esto es exactamente consistente con D9 Lastarria/Lascar/Tier A Muy Bajo en cirrus invernal Atacama.

**Bibliografía**: SP 426.5 §267-273: *"these unsuitable pixels are: all the pixels at the edge of the resampled matrices; all the pixels with dNTI or dETI < -0.1 ... the second condition eliminates the negative outliers that would alter the contextual thresholds"*. Cita directa.

##### Plan ejecutivo S72 derivado

**F2.1 (top P1, en implementación)**: 4 filtros + flag wireados en `first_pass_tests_2_and_3` y `contextual_dnti_hot_mask`. Profile aislado `mirova_equivalent_unsuitable_filters_v1.yaml`. Workflow A/B `reproc-ab-unsuitable-filters.yml`. R1+R2+R3 antes de adopción (regla S33).

> **Nota S116 (AUDIT_S116 C4 — re-evaluar urgencia, NO declarar obsoleto):** NEW-8 (gaps 2-4,
> §267-273) sigue siendo un gap de **fidelidad literal** del pool m,σ. Pero su síntoma operacional
> principal (FPs contextuales por outliers negativos, p.ej. cirrus) ya está **mitigado por otros
> frentes** adoptados después de escribir F2.1: D9 cap path-D 5 MW @ t_bg<270K (S71) + gate/guard
> A46 (0 fuga al dashboard, S113) + nadir/focal (S102-S109, mediana ratio ~0.53×). Por eso la
> **urgencia bajó**: antes de correr el A/B F2.1, re-evaluar si todavía aporta sobre el estado
> curado (medir si quedan FPs contextuales atribuibles a outliers negativos no cubiertos por D9).
> NO se declara cerrado/obsoleto sin ese dato (A48/A50). Sigue abierto, prioridad rebajada.
>
> **MEDIDO S116 (investigación read-only, `docs/AUDIT_S116_FOLLOWUP.md` Hilo 2):** de 17 464 records
> Tier A solo **832** sobreviven el filtro path-D-dominante ∧ frío ∧ no-confirmado ∧ visible-en-dashboard,
> todos en 4 volcanes de baja altitud (Copahue 123, Villarrica 129, PCC 532, Chaitén 229). Al
> inspeccionarlos (A62): ~99 % ya con `pc.vrp ≤ 5 MW` (D9 los capa) y re-anclados al GVP (A61) caen
> **SOBRE el cráter** (Villarrica 129/129, Copahue 123/123) — son **cat-b real sub-umbral** (A54), NO
> outliers negativos de borde. **0 FPs contextuales residuales** no cubiertos por D9. Veredicto: **A/B
> F2.1 = baja prioridad / no accionable** (aplicarlo removería señal real, killer A82); NO obsoleto (el
> gap de fidelidad literal del pool m,σ persiste). Lever real de cirrus = discriminante NO-`t_bg` (S113).

**F1.6 (top P2, en análisis)**: Tupungatito restaurar/ajustar `mirova_center_lat/lon` basado en centroide CONS NRT (5.21 km SE del vent yaml actual). Re-evaluar decisión S65 con evidencia post-S65.

**Reservado P3 (post-F2.1)**: HT1.5-NEW-1 scene-wide aggregation. Solo si F2.1 no resuelve completo. Refactor mayor con riesgo regresión recall.

#### Refutaciones bibliográficamente argumentadas (no perseguir)

| Hipótesis | Refutación | Fuente |
|---|---|---|
| C2 distinto per-régimen Muy Bajo | MIROVA detecta fumaroles 1.6 MW con Tabla 1 estándar | Laiolo 2017 §208-213 |
| Two-component model Eq.14-16 en NRT | MIROVA NRT NO lo usa (requiere assumption T_hot) | Coppola 2024 §1159-1171 |
| Percentil bajo (p01-p05) ring vs kernel local | Kernel local lo supera empíricamente | S58 adopción `local_kernel_bg` |
| Aveni 2025 Eq.9 para Villarrica recall 0% | Refutado empíricamente S24 | H_S24_AVENI_NEGATIVE |
| Geofencing 5 km Stromboli en Andes | 21.79% OSF >5 km — pérdida masiva recall | F1.4 empírico |
| Fumarole rim vs lago cráter (Laiolo 2017) | 4/5 vols Tier A Muy Bajo centroide térmico p50 <1 km vent | F1.1 empírico |
| Kernel L_bk excluye solo central | YA excluye TODOS hot pixels del cluster | F1.3 code review |

#### S113 — re-verificación en vivo + aclaración de scope (2026-06-18)

Caracterización fresca (read-only) sobre data actual, raíz del frente "#2 cirrus" del bloque S113:
- **El impacto OPERACIONAL-VISIBLE está RESUELTO** (la cara FP de detección): cirrus FAR genuino
  (path-D dominante + `t_bg<262K` + far) = **199 records**, con **0 fuga al dashboard** (el gate
  `far` de `mirovaEqVrp` los esconde) y **0 con pc.vrp>5MW** (el cap C de S71 está activo, max=5.0).
- **Los 3 "candidatos" del bloque S113 para #2 = exactamente las 3 opciones A/B-testeadas en S71**
  (atm gate t_bg / co-validación BT-NTI / cap). A y B ya **rechazadas** (A = el cloud-mask
  anti-MIROVA removido S27, Coppola 2016a §247 / 2023 §554; B rompe recall NdC 1.00→0.33); C
  **adoptada y LIVE**. El bloque S112 reframeó como pendiente algo ya decidido — **no abrir un A/B
  de cirrus nuevo** (sería redo de S71, anti-A8).
- **TRAP confirmado en vivo (A68/A80)**: de los 214 records cold+path-D **visibles** (summit), 207
  (96.7%) son MIROVA-CONFIRMADOS reales = fondo frío por **altitud** (Láscar 5592m, Lastarria,
  Tupun), NO cirrus. Un gate por `t_bg` los mataría — por eso A fue (correctamente) rechazada.
- **La amplificación de MAGNITUD (la otra cara de D9) — CURADA por las adopciones nadir/focal
  S102-S109** (verificado S113, ratio nuestro/MIROVA con pc.vrp_mw, A10, sobre 610 TP path-D-dominante
  visibles mayo-jun): **mediana 0.53×** (p25-p75 0.30-0.85), levemente sub-reportando = calibración
  clon-literal sana. S71 dejó "6-12× sistemático en cirrus"; hoy quedan **solo 2 records >5×** de 610,
  ambos VIIRS750 en cirrus (Tupungatito 05-24 4.41 vs MIROVA 0.19; PP 05-09 2.99 vs 0.18) — magnitud
  absoluta chica (3-4 MW, bajo el cap), = el "~30% residual VIIRS750 cirrus/glaciar" que la adopción
  focal V750 S112 ya documentó. NO es frente, es cola documentada.

**Estado D9 (actualizado S113) — EFECTIVAMENTE RESUELTA en sus dos caras**: (1) FP de detección
capeado (C, S71) + oculto por el gate `far` (0 fuga verificada S113); (2) amplificación de magnitud
curada por nadir+focal S102-S109 (mediana 0.53×, residuo = 2 records VIIRS750 cirrus a 3-4 MW). El
candidato t_bg-gate quedó descartado (anti-MIROVA + trap A68/A80: mataría 207 detecciones reales de
fondo-frío-por-altitud). **No quedan acciones abiertas en D9.** Detalle: `~memory/reference_s113_cirrus_d9_scope`.

## Auditoría visual S27 (post-render fix, 90d)

Conteo de markers en hotspot-map por Tier A (toggle "Solo principal" + "Solo cráter"):

| Volcán | Markers | MIROVA esperado (90d) | Diagnóstico |
|---|---:|---|---|
| Lascar | 309 | 226 alertas reales | Coherente, erupción crónica activa |
| **Lastarria** | **11** | **71 alertas reales** | **Subdetección catastrófica** (D4 — recall 8% en "Muy Bajo") |
| Tupungatito | 87 | 64 "Muy Bajo" | Coherente |
| Villarrica | 41 | 5 alertas (3 Muy Bajo + 2 Bajo) | Sobre-detección moderada |
| **PCC** | **518** | 86 alertas reales | **6× MIROVA** — clusters esperados ~80-100 post-aggregation |
| Copahue | 26 | 1 alerta real, 13 FPs | Sobre-detección 23× |
| NdC | 65 (16 vent-path) | 4 alertas reales, 26 FPs | **Data legacy mixta** (NdC retry falló 4× — esperado) |
| **Llaima** | **81** | **0 alertas reales, 33 FPs** | **78 detecciones summit, MIROVA dice 0**. Sobre-detección extrema sin contexto eruptivo |
| Chaitén | 173 | 20 alertas reales, 5 FPs | Sobre-detección 8× |
| **Planchón-Peteroa** | **13** | **29 alertas reales** | **Subdetección catastrófica** (D4 — recall 4% en "Muy Bajo") |
| Isluga | 134 | 67 alertas + 26 FPs | Coherente |

### Hallazgos clave de la auditoría visual

**H1 — D4 confirmado en ambos extremos**:
- Subdetección: Lastarria + Planchón. Inner_radius pequeño (5 / 3 km) correlaciona pero también puede haber mecanismo de detección sub-pixel summit que MIROVA usa y no replicamos.
- Sobredetección: Llaima + Copahue. MIROVA descarta sistemáticamente lo que detectamos (Llaima 78 markers vs 0 alertas reales MIROVA). Posible filtro temporal/persistencia que no replicamos.

**H2 — Llaima patrón distinto**: `inner_radius=5` no es chico, no es D4 clásico. Las 78 detecciones MIROVA las marca todas como FALSO_POSITIVO (33 en CSV). Hipótesis: lago Conguillío al ENE genera anomalías térmicas persistentes que el literal puro detecta (sin exclude_zones) pero MIROVA filtra con un mecanismo automático que NO está en papers que auditamos.

**H3 — NdC con vent-path activo**: 16 markers vent (color violeta) son evidencia residual de data pre-S27. Se limpia automáticamente con el reproc 11×90d en curso (run 25110402836).

**H4 — Toggle "Solo cráter" funciona perfecto**: 0 markers `far` en TODOS los volcanes auditados ✓. La distancia como criterio principal (alineado con MIROVA) está implementada.

## Roadmap de cierre de divergencias

| ID | Divergencia | Estado | Próximo paso |
|---|---|---|---|
| D1 | 1 punto/pasada vs N pixels | ✅ **Cerrado S27** (pipeline + data + popup + tabla) | — |
| D2 | CSV ground truth ~70% VIIRS | Conocido | Re-scrape Mirova-v1 (S28+) |
| D3 | FP explícito MIROVA vs nuestro `far` | Conocido | Posible categoría `mirova_fp_match` en records (S28+) |
| D4 | Recall sub-pixel summit (Lastarria 8%, Planchón 4%) | ✅ **Cerrado S27** — H_S27_1 confirmada categóricamente | — |
| D5 | Magnitud (ratio VRP) | ⚠️ **Re-abierto S33** — el "1.35× S27" estaba contaminado por bug `mirovaEqVrp` (no validaba pc_dist contra inner_radius). Ratio real Driver A solo: 2.53× | Aceptable dentro de tolerancia ±2× MIROVA |
| **D8** | **Cluster selection diverge de MIROVA** | ⚠️ **NUEVO S35** (2026-05-10) — VRP-chile elige `primary_cluster` por VRP máximo / pixel count máximo, NO por relevancia volcánica. Caso Puyehue 2026-05-09 05:42: VRP-chile elige cluster cráter principal (99 px, vrp=4.94 MW) cuando MIROVA reporta lacolito (0.18 MW @ 7.7 km). Confirmado pixel-level con TIF mirova-tif-archive. | Pendiente: investigar criterio de cluster selection MIROVA (Coppola 2016a §). Opcional fase Z. |
| **H8** | **Filtro distance pixel-por-pixel en store.py** | ✅ **Implementado S35** (2026-05-10) — fix con flag `enable_pixel_level_distance_filter`. A/B en `_h8_pixel_filter_enabled` profile. Pre-fix descarta TODA `anomaly_pixels` cuando pixel más caliente individual > radius_km, perdía clusters summit válidos. Reach 13.7% records Tier A en 30d, 20+ ALERTA MIROVA confirmadas perdidas. | Esperar A/B 25d, R2 pixel-level, decisión adopción operacional. |

## S33+ — Análisis TIF MIROVA "Last" Lascar 2026-05-08 + decisión revert fix S33

### Hallazgo TIF MIROVA real (2026-05-08)

`Pruebas/mirova_real/Lascar_VIIRS375_I04.tif` (descargado público sin login):
- 134×134 float64 EPSG:4326. **17,911 pixels >0** (99.7% del raster).
- Valores 0.04-0.19 MW. **Sum total 1680 MW**. Pico 0.187 MW a 23-24 km del vent.
- Header MIROVA reporta **VRP: 0.2 MW @ Distance 9.7 km**.

**Implicación**: el TIF NO es VRP per-pixel sumable. Es producto de visualización
del campo de radiancia completo. El "VRP: 0.2 MW" del header viene de un cluster
específico (a 9.7 km) seleccionado por algún criterio MIROVA, NO la suma del TIF.

### Hallazgo crítico — MIROVA reporta clusters far como detecciones válidas

Plot Distance MIROVA Lascar (Last Year) muestra cientos de detecciones rojas
(<5km, summit) Y grises (>5km, far). **MIROVA NO descarta clusters far** — los
etiqueta con su clase de distancia y reporta VRP normal. La pasada actual
(estrella verde) está a 9 km y MIROVA la reporta válida.

### Decisión usuario: objetivo A (clon literal) + visualización C (toggle dual)

Mi fix S33 (descartar clusters con `pc.centroid_dist_km > inner_radius`)
**diverge de MIROVA real**. MIROVA reporta esos clusters; nosotros los
filtramos a 0.

### Plan próxima sesión (S34)

1. **Revertir fix S33** en `pipeline/audit_metrics.py` y `frontend/{index,diario}.html`.
   `mirova_eq_vrp` ya no descarta por `pc.centroid_dist_km` — solo respeta
   `distance_class === 'far'` heredado del pipeline.
2. **Tests actualizados**: el caso "Lascar Salar 19389 MW" YA devuelve 19389
   (no 0). Documentar como comportamiento esperado clon MIROVA literal.
3. **Toggle dual en `diario.html`** (replicar `includeFarDistance` que ya
   existe en `index.html` desde S26).
4. **Re-audit con métrica revertida** — esperado recall global subir a ~80%+,
   ratio reaparece outlier Lascar 19389 (síntoma D5 magnitud, no bug S33).
5. **D5 magnitud queda abierto**: la suma per-pixel inflada en clusters far
   (Salar 19389 MW) es problema separado. Hipótesis Eq.1 integrated a investigar
   con TIF reales MIROVA descargados (otros volcanes activos cráter — PCC, etc.).

## S33 — Refutación Driver B Phase 1 + D4 (sub-pixel L_bg global)

### Bug `mirovaEqVrp` (S33)

`frontend/index.html:mirovaEqVrp` y `experiments/65_audit:vrp_summit_only`
chequeaban `distance_class==='summit'` pero NO validaban
`primary_cluster.centroid_dist_km <= inner_radius_km`. Caso patológico:
Lascar 2026-02-14 con cluster Salar Atacama a 24km daba pc.vrp_mw=19389 MW
reportado como VRP del cráter. Audit S32 que "validó" Driver B Phase 1
estaba contaminado.

### Re-audit con métrica corregida (`pipeline/audit_metrics.py` + `experiments/76_audit_independent.py`)

A/B 11 Tier A 90d (run 25339969705 + 25401379853 + 25414145698):

| Profile | Recall global | Ratio mediano |
|---|---:|---:|
| Driver A solo (operacional S33+) | **74.2%** | **2.53×** |
| Driver A + Phase 1 (test1 pixel filter 5σ) | 55.6% | 1.39× |
| Driver A + Phase 2 (final mask filter 5σ) | 10.5% | 1.23× |
| Driver A + D4 (L_bg global) | 55.7% | 1.39× |

### Veredicto

- **Phase 1 REFUTADO** (S33): destruye recall −18.6pp porque elimina
  pixels Test 1 marginales que SÍ formaban el cluster contiguo del
  cráter en Lastarria/Villarrica/Planchón. Sin esos pixels, el cluster
  cae al siguiente mayor (lago/scene). Reverted operacional.

- **Phase 2 REFUTADO** (run 25401379853): filtro 5σ a mask final
  destroza recall −63pp en volcanes con std_bg heterogéneo (cráter
  pixel real ΔT=15K no pasa threshold 5σ_summit=23K). Catastrófico.

- **D4 REFUTADO** (run 25414145698): efecto despreciable post-fix S33.
  +0.1pp recall, sin cambio de ratio. Diseñado para resolver problema
  que el bug S33 ya había auto-creado.

### Implicaciones para D4 (recall sub-pixel summit)

D4 sigue siendo problema real: Lastarria 100% recall, pero Villarrica
33%, Tupungatito 37%, Planchón 96.8%. Inclusive sin Phase 1, hay
volcanes con sub-detección (Tupungatito, Villarrica). H_S27_1 cerró
parte de D4 (Test 1 trigger se activa) pero recall summit-only cuando
pc_dist > inner_radius sigue como FN.

Plan S33+: investigar mecanismo MIROVA NRT que reporta señal sub-pixel
en volcanes con bg heterogéneo (Villarrica glaciar, Tupungatito glaciar).
Coppola 2015 Eq.1 textual: VRP = ΔL_ROI · A_ROI · k. Posible: reportar
**VRP integrated** del trigger Test 1 en lugar de descomponer per-pixel
y sumar (que es lo que hacemos hoy y pierde señal sub-pixel distribuida).

## H_S27_1 — Test 1 integrated-ROI activado en `_mirova_literal` (S27 cierre D4)

**Hipótesis**: las señales sub-pixel summit que el literal puro pierde con 5σ
pixel-por-pixel se rescatan con Test 1 integrated-ROI (Coppola 2015 §2.2 Eq.1).
Test 1 integra la radiancia EXCESS sobre el ROI summit completo (~3km del
vent) y dispara cuando la suma supera un umbral por área del ROI — capta
señal espacialmente distribuida sub-σ pixel-individual.

**Evidencia que llevó a la decisión** (S27 análisis multi-sensor 2026-04-30):

1. **MODIS está fundamentalmente ciego** para los volcanes débiles
   (Lastarria 0/71, Villarrica 0/6, Chaitén 0/15, Tupungatito 0/64, PCC 0/86).
   Solo Lascar (eruptivo crónico, 1.3 MW mediana) tiene 60 alertas MODIS.
2. **VIIRS 750m capta parcialmente** PCC (17), Tupungatito (8), pero **ciego
   para Lastarria, Villarrica, Chaitén**.
3. **VIIRS 375m es el ÚNICO sensor** que captura sub-pixel summit en
   Lastarria (71), Villarrica (6), Chaitén (14).
4. **Test 1 está implementado SOLO en `process_viirs.py`** (VIIRS 375m con
   I04). Activarlo afecta exactamente el sensor crítico para los casos D4.
5. **Distribución espacial confirmada**: Lastarria con magnitud 0.11 MW
   recall 8%, Tupungatito con magnitud comparable 0.22 MW recall 72%. La
   diferencia no es magnitud sola — es que Tupungatito es hotspot
   concentrado (laguna), Lastarria es señal distribuida en fumarolas.
   Esa firma es exactamente Test 1 integrated-ROI.

**Implementación**:
- `pipeline/profiles/_mirova_literal.yaml`: `enable_test1_path: true`.
- Parámetros default Coppola 2015: `k_sigma=3, mir_relative=0.02,
  roi_km=3, inner_ring_km=1`.
- Validado pre-S27 contra Villarrica lava lake en S25 POC: 6/6 refs
  triggered en magnitudes 0.05-0.21 MW.

**Pasa las 3 preguntas de docs/MISSION.md**:
1. Test 1 ES Coppola 2015 §2.2 Eq.1, paper MIROVA core foundational.
2. Cierra D4.
3. Reusa código existente sin parches geográficos.

**Próximo paso**: reproc 11×90d con `_mirova_literal` actualizado, comparar
recall + FP_far por volcán contra el baseline literal puro actual. Si:
- Lastarria 8% → ≥40%: H_S27_1 confirmada, mergear a operacional.
- FPs scene aumentan dramáticamente: investigar parámetros Test 1 (k_sigma,
  mir_relative) — siempre dentro de Coppola 2015, sin parches.

### Resultado H_S27_1 — confirmada categóricamente (S27 madrugada 2026-04-30)

Reproc completado exitosamente: run principal 25148058512 (9/11 success
directo) + retries 25148326350+25148328814 (Chaitén, Tupungatito).
Delta report 90d (2026-01-29 → 2026-04-29):

```
Volcán                Pre-Test 1     Post-Test 1     Δ recall
====================================================================
Lastarria               8% (5/60)    100% (60/60)    +92 pp  ★
Planchón-Peteroa        4% (1/28)    100% (28/28)    +96 pp  ★
Chaitén                73% (8/11)    100% (11/11)    +27 pp
Villarrica              0% (0/3)     100% (3/3)      rescate total
Tupungatito            72% (46/64)    88% (56/64)    +16 pp
Lascar                 67%           63%             -4 (ruido)
PCC                    97%           97%             0 (saturado)
Isluga                 80%           83%             +3
NdC                    33% (1/3)     25% (1/4)       ruido (N=4)
Copahue               100% (1/1)    100% (1/1)       0
====================================================================
TOTAL                  ~50%          80% (406/507)   +30 pp
```

**Conclusión**: Test 1 (Coppola 2015 §2.2 Eq.1) era exactamente lo que
faltaba para los casos D4 catastróficos. La hipótesis se confirma sin
ambigüedad — los 3 casos predichos como "más afectados" (Lastarria,
Planchón, Villarrica) tuvieron rescate de 8%/4%/0% → 100% cada uno.

**Caveat FPs**: los counts de detecciones `far` post-Test 1 son ~3,840
totales (vs ~3,500 baseline). Increment moderado, NO explosión. El toggle
"Solo cráter" del dashboard filtra los `far` por default; el usuario solo
ve summit (4,060 detecciones).

**Edge case identificado para S28+**: cuando Test 1 dispara solo
(eruption-path descartado por Regla X y Test 1 rescata), `final_hotspot_source="test1"`
y `final_hotspot_dist_km` queda en summit, pero `vrp_mw=0` mientras
`vrp_mir_mw>0`. Bug menor de propagación VRP en ese path. NO afecta
recall (la métrica usa primary_cluster.vrp_mw + triggered_test1 como OR),
pero conviene fixear para coherencia data layer.

**Decisión consolidada**: mergear `enable_test1_path: true` también a
`mirova_equivalent` operacional — Test 1 es paper MIROVA core y debería
estar ON en todos los profiles, no solo `_mirova_literal`. Pendiente
para S28+.

### S28 — Test 1 extendido a VIIRS 750m (M13 4.05 µm)

Tras S27 H_S27_1 confirmada en VIIRS 375m, el residuo D4 mostró ~20 FNs
en VIIRS 750m (Tupungatito 8, Isluga 11, PCC 1) — banda donde Test 1 NO
estaba implementado. Extensión a `process_viirs_mod.py` con
`lambda_um=M13_LAMBDA=4.05`.

Resultado: Tupungatito 72% → 88% (+16pp), Isluga 80% → 83% (+3pp).
Recall global mantenido en 80%. Implementado en commit 82dcaa5.

### S29 — Test 1 extendido a MODIS Banda 21 (3.929 µm)

Tras S28, los 77 FNs Lascar MODIS quedaron como mayor residuo D4.
Análisis fino mostró que TODOS los granules estaban procesados pero
detectados como "far" (Salar de Atacama 22-29 km del vent contamina
primary_cluster). Hipótesis: Test 1 con `roi_km=3` desde vent ignora
el Salar y rescata cráter sub-pixel.

Coppola 2015 §2.2 fue diseñado **originalmente para MODIS L1B** —
extender Test 1 a MODIS es alineación con el sistema MIROVA original.

Resultado:
- **Tupungatito 88% → 95% (+7pp)**: Test 1 MODIS rescató ~5 FNs.
- **Isluga 83% → 89% (+6pp)**: idem ~4 FNs.
- **Lascar 63% → 64% (+1pp)**: hipótesis NO confirmada.
- TOTAL recall: 80% → **82.2%** (+2.2pp).

**Lección Lascar**: el cráter realmente NO tiene radiancia integrada
detectable en MODIS pixel 1km cuando σ_bg del ring 1-3km es alto
(Atacama heterogéneo). Es límite físico del sensor MODIS para sub-pixel
summit en terreno árido. **Lascar 64% queda como límite físico aceptado**
— ir más allá requeriría exclude_zones del Salar (parche, viola MISSION).

Test 1 ahora ON en los 3 sensores que MIROVA usa (commit ed75b7c):
- MODIS Banda 21 (3.929 µm)
- VIIRS I04 (3.74 µm)
- VIIRS M13 (4.05 µm)

D4 cierra al **límite del clon literal MIROVA**. Para mejorar más se
requiere divergencia metodológica.

## S28 — Test 1 extendido a VIIRS 750m M13

Tras milestone S27, el delta cuantitativo identificó ~20 FNs residuales
todos en VIIRS 750m (Tupungatito 8, Isluga 10, PCC 1). Test 1 estaba
implementado solo en `process_viirs.py` (VIIRS 375m I04 3.74µm). S28 lo
extendió a `process_viirs_mod.py` (VIIRS 750m M13 4.05µm) reusando el
helper agnóstico `compute_test1_mir(lambda_um=...)`.

**Delta S28 vs S27** (recall por volcán, 90d):

```
Volcán              S27 (375 solo)   S28 (375+750)   Δ
====================================================
Tupungatito           88%             95%            +7 pp ★
Isluga                83%             89%            +6 pp ★
Lascar                63%             64%            +1
Lastarria            100%            100%            0
Villarrica           100%            100%            0
PCC                   97%             97%            0
Chaitén              100%            100%            0
Planchón             100%            100%            0
====================================================
TOTAL                 80%             82%            +2 pp
```

**Lectura física**: la predicción era +20 FNs rescatados (10% del total).
Logramos +10 (4 Tupungatito + 4 Isluga + 2 ruido). El gain real es la
mitad de lo predicho. Razón probable: VIIRS 750m tiene ~4× menos pixels
en el ROI summit 3km que VIIRS 375m (30 vs 120 pixels), reduciendo el
statistical power de Test 1 (σ_ΔL = σ_bg × √N escala con √N). Los FNs
residuales tienen señal demasiado débil para superar el threshold `k_sigma=3`
en VIIRS 750m incluso con integración de ROI.

**Estado D4**: parcialmente cerrado pero no completamente.
- Casos catastróficos cerrados (Lastarria 100%, Planchón 100%, Chaitén 100%).
- Casos parciales (Tupungatito 95%, Isluga 89%) — gain pero residuo.
- Casos MODIS-dependientes (Lascar 64%) — Test 1 no aplica, requiere
  investigación separada en `process_modis.py`.

**Pendiente S29+**:
- Investigar Lascar 77 FNs MODIS (~44 son Bajo, magnitud >2 MW — debería ser fácil).
- Posible Test 1 también en MODIS (Coppola 2015 §2.2 fue diseñado originalmente
  para MODIS, no requiere adaptación física).

## Referencias

- CSV consolidado: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
- Análisis S27: en este documento + `~memory/project_s27_mirova_literal_negativo.md`
- Hipótesis arquitecturales H_S27_1 a H_S27_5: ver memoria.
- Frontend fix S27: `frontend/index.html` toggle "Solo principal vs Todos los pixels".

---

## S45 (2026-05-14) — D9 cluster selection MIROVA: summit-priority confirmado Lascar

**Contexto**: S44 cerró con recall 94.8% y 6 FN persistentes. Investigación
S45 con audit corregido (`pc.vrp_mw` filtered, FP solo vs FALSO_POSITIVO,
window 15d 2026-04-27→2026-05-11) dio TP=35, FN=6, FP=5 (P=87.5%, R=85.4%).
Los 6 FN tienen 3 mecanismos distintos.

### Mecanismo 1 (4 FN Lascar MODIS) — cluster selection diverge

**Patrón estructural confirmado** auditando los 4 granules Lascar MODIS:

| Caso | MIROVA reporta | Nuestro cluster | Píxel cráter en `anomaly_pixels`? |
|---|---|---|---|
| 04-30 07:30 | 0.99 MW @ 1.0 km | n_pix=1, dist=22.6 km W | SÍ (BT 273.58 K @ 0.59 km, vrp=1.34) |
| 04-28 07:50 | 1.31 MW @ 2.0 km | n_pix=2, dist=27.5 km NW | SÍ (BT 274.29 K @ 2.43 km, vrp=1.88) |
| 04-28 01:50 | 0.66 MW @ 1.4 km | n_pix=1, dist=27.4 km WSW | NO listed (anomaly_pixels=0) |
| 04-27 07:15 | 0.28 MW @ 1.4 km | n_pix=2, dist=30.0 km SW | SÍ (BT 272.46 K @ 1.81 km, vrp=1.57) |

**Diagnóstico**:
- Background MODIS B21 t_bg ≈ 265-268 K (incluye Salar de Atacama, ~25 km W).
- σ_bg = 4.5-6.5 K → eff_threshold = t_bg + 4σ ≈ 286-292 K.
- Píxeles Salar @ 20-30 km W tienen BT 278-283 K (térmica residual post-atardecer).
- Píxeles cráter @ <3 km tienen BT 272-274 K (anomalía sub-MW sub-pixel real).
- **Ningún path formal (n_bt=None, dnti_ctx=None, test1=False) dispara**.
  Pero anomaly_pixels llega con 75-83 pixels listados via un mecanismo previo
  no aislado en diag.
- Cluster centroid eligió siempre el grupo Salar (más caliente scene-wide)
  e ignoró el píxel cráter.

**Conclusión D9**: MIROVA tiene **summit-priority cluster selection** no
documentada explícitamente en Coppola 2016a SP426.5 pero operacional. La
evidencia es triangular:
1. **Indirecta paper**: dual-ROI con C1 summit=0.003 más permisivo que C1
   scene=0.010 (Coppola 2016a Table 2). Si summit dispara con su umbral
   permisivo, MIROVA reporta esa alerta.
2. **OSF v2.5 empírico**: 10,579 filas Chile Tier A, solo 2 timestamps con
   verdadero multi-cluster mismo sensor (NdC 2021-07-21). MIROVA emite
   1 alerta por (volcán, timestamp, sensor) — no es max-VRP global (caso PCC
   2026-05-09 lo refuta), por exclusión queda summit-priority.
3. **Lascar 4 FN**: nuestro pipeline detecta el píxel cráter en
   `anomaly_pixels` pero clustering lo entierra entre Salar; MIROVA en cambio
   reporta justo ese píxel cráter — consistente con ROI summit evaluado
   separadamente del scene.

**Acción S46+**: implementar flag `enable_summit_priority_eruption`. Lógica:
- Si hay píxel(es) dentro de `inner_radius_km` (summit ROI) con
  BT > t_bg_summit + 2σ_summit (umbral permisivo C1_summit ≈ 0.003), construir
  primary_cluster desde esos píxeles SIN considerar scene-wide.
- Si NO hay summit detection, fallback a comportamiento actual (cluster
  scene-max via vent_anchored).
- A/B reproc 30d × 11 Tier A vs `mirova_equivalent` baseline.

### Mecanismo 2 (1 FN Tupungatito VIIRS375) — Test 1 dispara con VRP MIR=0

**Caso**: 2026-04-27 05:18 VIIRS_NOAA20. Test 1 disparó 88 píxeles dentro del
summit ROI (`pc.centroid_dist_km=1.25 km`, n_pixels=88), pero
**`pc.vrp_mw=0.0`**. Wooster MIR formula correctamente da 0 porque ΔL_MIR ≈ 0
en los píxeles que Test 1 marca anómalos por NTI (NTI dispara con 4.77σ pero
σ=0.0036, contraste absoluto chico).

MIROVA reporta 0.11 MW @ 5.41 km — un píxel específico en zona "near-vent"
con MIR ligeramente sobre fondo que sí da VRP>0.

**Hipótesis**: el píxel @ 5.4 km que MIROVA reporta tiene NTI más alto y MIR
ligeramente sobre fondo. Nuestro clustering 8-conn agrupa los 88 píxeles de
NTI sutil incluyendo zonas "frías" donde ΔL_MIR=0; el centroid resultante no
representa el píxel caliente real. Investigación pixel-level específica
requiere re-procesar el granule VJ102IMG.A2026117.0518 con diag verbose
por píxel.

**Acción S46+**: backlog. Probable solución: filtrar `anomaly_pixels` por
`vrp_mw > 0` antes de clustering — ya parcialmente cubierto S43
vent_anchored prefiere vrp>0, pero parece no aplicar a Test 1 puro.

### Mecanismo 3 (1 FN Isluga VIIRS375) — granule VJ202IMG no procesado

**Caso**: 2026-04-29 05:24. MIROVA tiene VIIRS375 (alerta @ 0.84 km, vrp=0.10).
Nosotros solo tenemos VJ202MOD (NOAA-21 M-band 750), no VJ202IMG (I-band 375).
fetch.py SÍ está configurado para VJ202IMG (líneas 74-76). Probable gap NRT
LANCE puntual o fallo de descarga ese día. Patrón conocido (handoff S44
menciona similar para NdC).

**Acción S46+**: backlog. No hay fix mecánico — depende disponibilidad NASA
LANCE. Monitorear si patrón aumenta de frecuencia.

### Paths legacy retirables (P5 audit S45)

Auditoría empírica sobre 9,206 records con `n_anomalous_pixels>0`:

| Path | Records dispara | Único contributor |
|---|---|---|
| `test1` | 4554 | — |
| `dnti_ctx` | 5445 | — |
| `bt` | 429 | — |
| `nti` | **50** | **0** |
| `nti_rel` | **0** | **0** |

- `nti_rel_path` es **dead code** (0 records contribuyen).
- `nti_path_hot` tiene 50 records totales pero **0 son únicos contributors**
  (test1 y/o dnti_ctx siempre cubren). Retirable sin pérdida de recall.

**Acción S46+**: plan documentado, A/B reproc 30d antes de adoptar.

### Coords Tier A validados (P6 audit S45)

Barrido sistemático `volcanoes.yaml` vs centros de GroundOverlay MIROVA en KMZs:

| Volcán | dist vent → kml | Status |
|---|---|---|
| PCC | 7.57 km | Sin `mirova_center`, pero `inner_radius=20` absorbe |
| Tupungatito | 4.86 km | `mirova_center` configurado, MATCH KML |
| Planchón | 2.02 km | `mirova_center` configurado (Planchón W vs Peteroa E), MATCH KML |
| Lascar | 0.87 km | OK borderline |
| Otros 7 Tier A | <0.5 km | OK |

**Sin errores de configuración**. Offsets reflejan vulcanología real (volcanes
duales o vent desactualizado vs MIROVA anchor). Configuración ya manejada.

### Limitaciones evidence S45

- mirova-tif-archive: solo cubre 2026-05-08+ para casi todos los sensores.
  Los 4 FN Lascar (2026-04-27 a 04-30) están en gap.
- CSV consolidado más reciente: 01_05_2026 (latest 2026-05-01). Window audit
  efectivo: 2026-04-27 a 2026-05-01 (5 días, no 15 como afirmaba handoff S44).
- OSF v2.5 termina 2025-12-31, no cubre 2026.
- R2 pixel-level estricto vs MIROVA requiere ambos archivos sincronizados.
  S46+ accionable: configurar scraper Mirova-v1 + mirova-tif-archive con
  retención más larga, o capturar TIFs proactivamente al detectar FN.

---

## S45+R6 (2026-05-14 tarde) — Auditoría independiente pipeline vs papers + rescate s15-dev

Auditoría profunda R6 (regla `docs/PROCESS_RULES_S33.md`) comparando los 3
procesadores línea-por-línea con papers MIROVA core identificó **21 drifts**,
5 ALTA severidad. Trabajo independiente de la auditoría empírica S45.

### Insight TIF MIROVA rescatado de `s15-dev` (commit 64bd37d S33+ cierre)

`Pruebas/mirova_real/Lascar_VIIRS375_I04.tif` analizado S33+ (2026-05-08):
- 134×134 float64 EPSG:4326. **17,911 pixels >0** (99.7% del raster).
- Valores 0.04-0.19 MW. **Sum total 1680 MW**. Pico 0.187 MW a 23-24 km.
- Header MIROVA reporta **VRP: 0.2 MW @ Distance 9.7 km**.

**Implicación crítica**: el TIF NO es VRP per-pixel sumable scene-wide. Es
producto de **visualización del campo de radiancia completo**. El "VRP: 0.2 MW"
del header viene de **selección específica de cluster post-filtros**, NO suma
del TIF visible.

Plot Distance MIROVA Lascar Last Year confirma: MIROVA reporta clusters
far (>5km) como detecciones válidas (etiqueta clase distancia, NO descarta).

### Reinterpretación R6 drift #5 a la luz del insight TIF

R6 audit identificó como drift #5: "Reportamos `primary_cluster.vrp_mw`
cuando paper Eq.8 dice `RP = Σ RP_PIX` sobre `n_alert`". Interpretación
inicial: Σ scene-wide.

**Reinterpretación corregida**: Eq.8 aplica sobre `alerted pixels` =
pixels que pasaron filtros Tests 1∧2∧3∧second-pass. Con filtros completos
del paper, lo que queda es un cluster específico = "main alert" natural.
NO es Σ visualizable del TIF.

Si esta lectura es correcta, el verdadero drift no es "primary_cluster vs Σ"
— es que **NO ejecutamos los filtros Coppola 2016a completos**, por eso
nuestros `anomaly_pixels` quedan inflados (75-83 px en Lascar) y forzamos
parches S33-S44 para compensar.

### Drifts R6 ALTA severidad

| # | Drift | Localización pipeline | Paper |
|---|---|---|---|
| ~~#1~~ | ~~Test 1 K1 → `hot_mask` reportable~~ — ❌ **NO ES DRIFT (S100)**: lectura equivocada de sp426_5.txt:298-300. "discarded (unsuitable) for further steps" = sacar del **pool estadístico** (m,σ de Tests 2/3, §326-329 "all the suitable pixels"), NO del **reporte**. Los Test 1 SÍ se reportan (son las detecciones fuertes). Código actual (flag OFF) ya fiel. Ver nota S100 arriba | `process_*.py` nti_path_hot | sp426_5.txt:298-300 + 326-329 |
| #2+3 | Path D usa solo Test 2 (dNTI), falta Test 3 (dETI) + conjunción AND | `detection_context.py:85-142` | sp426_5.txt:316-325: Tests 2∧3 obligatorios |
| #4 | Second-pass adyacente OFF operacionalmente | `enable_second_pass_adjacent=false` | sp426_5.txt:347-356: Step obligatorio |
| #5 | `primary_cluster.vrp_mw` vs Σ alerted | `store.py` + dashboard | sp426_5.txt:374-398 Eq.8 — pero ver reinterpretación arriba |
| #7 | MODIS `sec³(θz)` scan-angle vs nadir-fijo | `scan_geometry.modis_pixel_areas` | sp426_5.txt:201-202: A_pix=1 km² fijo. Factor hasta 13× edge — probable causa ratio 1.21× |

### Drifts R6 MEDIA / BAJA

- #15: falta exclusión edge `dNTI/dETI < -0.1` (sp426_5.txt:271-273)
- #17: yaml VIIRS `enable_vent_path` sobreviviente (drift histórico)
- #18: `ENABLE_TEST1_PATH` mala nomenclatura — confunde con Test 1 del paper
- #21: bg ring no excluye pixels active antes de Wooster ΔL
- #12: falta emisividad ε≈0.95 explícita en Stefan-Boltzmann I05 (Aveni 2024 Eq.5)
- #20: bbox geográfico vs grilla UTM equiárea (~1% deformación)

### Hipótesis S46 reencuadrada — "Coppola 2016a literal puro"

Plan S46 reencuadre (post-brainstorming pendiente):

**Fase 1 — corregir filtros Coppola 2016a** (drifts #1, #2+3, #4):
- Test 1 K1 a saturation mask (no hot_mask)
- Implementar Test 3 (dETI) + conjunción AND + rama estadística C2·σ
- Activar second-pass adyacente operacional
- Esperado: `anomaly_pixels` se reduce drásticamente, queda "main alert" natural

**Fase 2 — A/B aislado drift #7 MODIS nadir-fijo** (independiente):
- `scan_geometry.modis_pixel_areas` → `np.full(shape, 1e6)` con flag
- A/B reproc 30d MODIS-heavy
- Esperado: ratio mediano 1.21× → ~1.0×

**Fase 3 — evaluar si parches S33-S44 siguen necesarios**:
- Con filtros completos, S38 vent_anchored / S43 vrp>0 priority / S41 cap /
  S44 final_hotspot_source pueden ser redundantes
- A/B reproc con filtros completos + parches OFF
- Si recall y ratio mantienen, deprecar parches

### Insight S33+ adicional rescatado de s15-dev

> "MIROVA reporta clusters far como detecciones válidas — los etiqueta con
> su clase de distancia y reporta VRP normal. La pasada actual (estrella
> verde) está a 9 km y MIROVA la reporta válida."

Esto refuta hipótesis D9 summit-priority exclusiva — MIROVA SÍ reporta
clusters far cuando los detecta. Lo que distingue es **qué pasa por los
filtros** (Coppola 2016a Tests completos), no "preferencia summit".

Caso PCC 2026-05-09 (lacolito 0.18 MW @ 7.7km reportado, cráter 4.94 MW
@ 0.69km ignorado por MIROVA): probablemente nuestro "cráter @ 0.69km"
es FP que MIROVA habría descartado vía Tests 2∧3 + second-pass. No es que
MIROVA "prefiera" lacolito — es que cráter no pasa filtros estrictos.


---

## S60-S62 — Consolidación divergencias resueltas + universo expandido OCR

**Cierre maratón 3 sesiones** (S60: audit per-vol kernel-bg, S61: adopción
operacional Villarrica+PP, S62: PCC inner_radius + A/B Lastarria/Tup +
Chaiten pendiente S63).

### D8 Background ring contaminado — RESUELTO

**Hipótesis inicial S52-S58** (refutada): "Lascar/Lastarria ring 5-25 km
sesgado por desierto Atacama frío → ΔL inflado en cráter".

**Hipótesis revisada S62** (CONFIRMADA): el problema NO es desierto en
general, es **régimen Muy Bajo (ΔT 10-12K)** + **ring background frío
local** → Test 1 integrated-ROI suma pixels marginales acumulándose en
suma VRP inflada.

**Patrón térmico Tier A identificado**:

| Régimen | ΔT mediano | Vols | Necesita fix |
|---|---:|---|---|
| Bajo-Medio | >20K | Lascar, Isluga | NO (calibrado natural) |
| Muy Bajo | 10-12K | Villarrica, PP, Lastarria, Tupungatito, Chaiten, PCC | SÍ (kernel-bg + opt) |

**Fix adoptado**: kernel local 3×3 (Coppola 2024 L1129 literal). Reemplaza
`median(ring 5-25km)` con `mean(8 vecinos directos del hot pixel)`.

**Resultados validados empíricamente**:
- Villarrica audit C 5 ALERTAS reales: 31.59× → **2.16×** (-93%)
- PlanchonPeteroa 39 ALERTAS: 11.80× → **2.64×** (-78%)
- Lastarria/Tupungatito A/B corriendo S62
- Chaiten pendiente S63

### Per-vol `local_kernel_bg` flag estado S62

| Vol | Flag | Razón |
|---|---|---|
| Villarrica | true | Lago norte cálido + cráter activo (S61 adopción) |
| PlanchonPeteroa | true | Glaciar heterogéneo + cráter (S61 adopción) |
| Lastarria | <pendiente A/B S62> | Patrón Muy Bajo confirmado |
| Tupungatito | <pendiente A/B S62> | Patrón Muy Bajo confirmado |
| Chaiten | false (S63 candidato) | Patrón Muy Bajo confirmado |
| Lascar | false | Calibrado natural (ratio 1.32×) |
| Isluga | false | Calibrado natural (ratio 1.11×) |
| Copahue | false | Calibrado (1.14×) — lago Caviahue dentro cráter |
| Llaima | false | Calibrado (1.01×) — Conguillío frío deshielo |
| NdC | false | Sin data MIROVA |

### D-PCC: inner_radius_km demasiado permisivo — RESUELTO S62

**Hipótesis previa**: PCC gap 52× porque cluster lejano (Salar/Antillanca)
ganaba selección summit con inner=20 km.

**Validado**: PCC ratio mediano 3.51× con inner=20. Preview offline
inner=7 → 1.86× (-47%). Adoptado en `volcanoes.yaml` S62. Reproc
operacional corriendo.

### Hallazgo dist=0.84 km fijo Villarrica — ⚠️ **REFUTADO S124, corregido acá en S125**

> El `Distancia_km` de Villarrica **no** es 0.84 fijo: sobre n=3338 vale **0.0 en 3284 casos
> (98,4 %)** y 0.84 sólo 15 veces. Además el campo está **cuantizado a la celda de la grilla**
> de MIROVA (D15), así que «0.0» significa «en la misma celda que su referencia», no «a 0 km
> del cráter». `CLAUDE.md` ya lo corrigió en S124 (regla A13); este catálogo no se había
> actualizado. Texto original abajo, conservado por historia:

#### (texto original) Hallazgo dist=0.84 km fijo Villarrica — METADATO no error

**MIROVA reporta `Distancia_km`** desde coord nominal Smithsonian GVP, NO
desde centroide variable del cluster. Para Villarrica (cráter ~150m, lava
lake muy localizado): coord Smithsonian (-39.42, -71.93) está a 0.85 km
del cráter actual (-39.420292, -71.939908). Por tanto MIROVA siempre
reporta dist=0.84 km. Es idiosincrasia metadato, NO bug nuestro.

Otros vols (Lascar, Lastarria, Isluga, etc.) muestran distancias variables
porque sus cráteres son grandes y centroides de cluster varían.

### Universo MIROVA NRT expandido OCR + CONS

S62 descubrimiento: el CSV OCR (`registro_vrp_ocr.csv`) tiene **457
ALERTA_TERMICA_OCR + 19 FALSO_POSITIVO_OCR**. Universo MIROVA real es
~2-3× mayor que solo consolidado.

**Significado correcto** (clarificación Nicolás S62):
- OCR NO captura errores de MIROVA.
- Es **complemento** del consolidado: MIROVA publica datos en `latest.php`
  (CSV consolidado) y otros datos solo visibles en imágenes por volcán
  (OCR los extrae).
- `FALSO_POSITIVO_OCR` es etiqueta del scraper Nicolás cuando OCR no pudo
  confirmar visualmente que era volcánico, NO etiqueta MIROVA.

**Para audits**: usar CONS+OCR como universo expandido. Validar que ratio
mediano de OCR coincide con CONS (S62 consistency check Lascar: CONS
1.31× / OCR 1.47×; Isluga: CONS 1.44× / OCR 1.11×).

### Universo audit Tier A consolidado (window 80 días)

**944 ALERTAS** total Tier A (CONS+OCR window 80d), recall global 85%.

Cuando S62+S63 completen:
- 3 vols ya calibrados: Lascar, Isluga, Villarrica
- 5-6 vols post-fix esperados ratio 2-3×: PP, Lastarria, Tupungatito, Chaiten, PCC, Tupungatito
- Total esperado: **~99% del universo Tier A en ratio ≤3×** = clon literal MIROVA NRT logrado.

---

## D8' Cluster selection Puyehue (S35) — RESUELTO S38

**Cierre formal S86** (resuelve auditoría I-C4).

**Hipótesis S35** (descrita en CLAUDE.md sección "Estado S35"): el pipeline elegía un cluster distinto al que MIROVA reportaba en PCC. Caso de referencia: nuestro pipeline elegía cluster cráter principal (99 px, vrp=4.94 MW) cuando MIROVA reportaba el lacolito (35 px, vrp=0.18 MW). Ratio inflado 27×. Hipótesis: criterio de selección MIROVA es proximity-al-vent o anomaly-score-relativo, no `vrp_mw desc` ni `n_pixels desc` como hacía `pipeline/clustering.py`.

**Resolución S38**: implementado `enable_vent_anchored_clustering` que selecciona el cluster más cercano al vent_lat/lon como `primary_cluster`. Verificado contra PCC + Lascar + otros Tier A con caída de ratio dentro de banda 0.5-2.0 para los vols focales (régimen Tier A Alto) y dentro de banda 0.5-3.0 para Tier A Muy Bajo.

**Verificación retroactiva S86** (Subagentes A+B+C+E): el cruce TP/FP con metodología corregida muestra que el cluster vent-anchored coincide con el reportado por MIROVA en los casos focales (Lascar 100% match) y en los casos difusos (PCC 7.99 km lacolito) cae dentro de la "cola térmica" del feature volcánico real que MIROVA también publica como ALERTA. Patrón A20 (anomalía difusa extendida — el centroide del cluster nuestro coincide con la región MIROVA aunque sea no-focal).

**Schema check**: la nomenclatura "D8" se usó dos veces en el proyecto — una en S35 (cluster selection PCC, resuelto S38) y otra en S52-S62 (background ring contaminado, resuelto S62). Ambas RESUELTAS al cierre S86. Próximas divergencias deben seguir desde D9 (`docs/D9_PATH_D_CIRRUS_FP.md`).


---

## D10 — Magnitud Test 1 sobre glaciar: ctxpeak (filtro contextual + keep-peak) — ADOPTADO S100

**Fenómeno**: el Test 1 integrado-ROI (Coppola 2015 §2.2 Eq.1) suma TODOS los píxeles del ROI sobre la mediana del fondo. Sobre el glaciar nevado de Tupungatito (5.682 m), en invierno, eso es el mosaico nieve/roca entero (anillo difuso 1-3 km) con un fondo regional sesgado frío → la magnitud se infla **8-19×** vs MIROVA, que reporta el foco compacto (~0.2 MW estable). Empezó abril 2026 (marzo daba 1.04× perfecto): mosaico nieve/roca invernal sobre el glaciar.

**Divergencia respecto al literal MIROVA**: el flagging contextual literal (dNTI/dETI vs vecinos, Coppola 2016a Tests 2/3) probado solo (`enable_test1_contextual_filter` sin keep-peak) da el mejor ratio (1.22×) PERO **crea 31 FN en Tupungatito** porque el cráter está EMBEBIDO en su halo de roca tibia y no es anómalo vs sus vecinos → MIROVA-literal lo borra. Nuestra detección no es idéntica a la de MIROVA (resolución/granule/embebido), así que aplicar el criterio literal píxel-a-píxel destruye el recall.

**Solución JUSTIFICADA (MISSION "cuándo SÍ divergir")**: `enable_test1_contextual_filter` + `enable_test1_contextual_keep_peak` — aplica el filtro contextual (recorta el halo) PERO conserva siempre el píxel pico (= cráter). Cura sin FN.

**Evidencia A/B paired 11 Tier A (S100, sin confounder, 416 pares; `docs/S100_TEST1_FULL_AB.md`)**:
- Tupungatito 18.94× → **1.33×** | Lastarria 1.31→1.02 | PP 2.23→1.83 | Llaima 6.12→2.01
- **d_recall +0 y d_FN +0 en los 11** (ninguna detección perdida, ningún FN nuevo)
- Controles intactos (Lascar 0.86→0.83); vols no-Test1 sin cambio (matched = path eruption)

**Alternativas descartadas** (S99): pixfilter (41 FN, recall 59→22); kernel-bg local (refutado S62/A19, empeora glaciar denso 10→18×); eq16 lava lake (anula sub-píxel, 192 Villarrica→0); contextual puro (31 FN cráter embebido). ctxpeak es el ÚNICO que cura sin destruir recall. Flag previo (default OFF) ya en código; adoptado a `mirova_equivalent.yaml` S100. Tag: `pre-s100-test1-magnitude-adopt`.


---

## S103 — nadir-fijo VIIRS adoptado + FN Isluga 750 (interacción Test1)

**Adopción** (espejo de nadir-fijo MODIS S102, A45): `enable_nadir_fixed_pixel_area_viirs:true`
en `mirova_equivalent`. VIIRS arrastra el mismo drift off-nadir que MODIS — el factor lineal
1-2× de `scan_geometry.viirs_pixel_areas` infla la magnitud VRP de los vols off-nadir del sur.
La calibración S14 (`a_pix_mode=nadir_fijo`) confirma que el WOOSTER_COEFF de los 2 sensores
VIIRS ya es para área nadir → activar nadir-fijo RESTAURA el clon, no rompe calibración.
Decisión A/B 3-way pre-registrada (runs 27069747395 + 27079762282, design doc 2026-06-06 §5bis):
adoptar nadir + **MANTENER ctxpeak** (hipótesis "ctxpeak=parche sec³" REFUTADA por datos:
nadir-sin-ctxpeak = 2.43× peor; mecanismos ortogonales A66 — área vs fondo del ROI).

**Resultado R3** (reproc histórico runs 27098410956 + 27140784929, `audit_viirs_nadir_promote_r3.py`):
VIIRS375 global **2.27×→0.78×**, VIIRS750 **1.59×→0.80×**, **0 FN nuevos VIIRS375**. Curados
PCC 2.38→0.95×, Tupun 11.19→0.71×, Villarrica 18.3→1.0×, Chaitén 6.9→1.2×, PP 7.3→1.1×.
MODIS byte-idéntico (promoción solo-VIIRS, `merge_promote_viirs_nadir.py`). Tag: `pre-s103-nadir-fixed-viirs`.

**Divergencia/costo aceptado (Nicolás S103): Isluga VIIRS750 +2 FN** (2026-03-09, 2026-04-07).
Mecanismo investigado (records crudos): el área nadir **no solo escala la magnitud — también
reduce la energía integrada del Test1** (el área es multiplicador en la integral de la radiancia
del ROI). Para 2 señales sub-píxel glaciar borderline, la energía cae bajo el umbral de disparo
→ `triggered_test1` True→False, la detección desaparece. Eran **sobre-detecciones pre-nadir**
(pc.vrp 5.0 y 2.56 MW vs MIROVA 0.19/0.25 MW) = el residuo glaciar Test1 de VIIRS750 (=§2 path D,
frente aparte). VIIRS375 quedó con 0 FN. Aceptado: 2 señales tiny glaciar VIIRS750 vs la cura
masiva de magnitud + reducción de sobre-detección en los 11.

**Nota (corrige registros previos)**: el nadir-fijo **reduce la CANTIDAD de detecciones**, no
solo la magnitud (vía el Test1): Villarrica 636→602, Isluga 550→535, Llaima 557→540. Es decir,
ayuda parcialmente a la sobre-detección. El residuo glaciar VIIRS750 (Tupun/PP 16.6×, Isluga 4.76×)
**persiste** y se ataca en §2 (portar ctxpeak a VIIRS750 + co-validación path D, A45).

## S98 — Fix del ancla de detección (regresión S65→S80 cerrada) — RESUELTO S98

`geo_utils.py` separa `get_grid_center` (mirova_center, grilla 50×50) de
`get_detection_anchor` (vent_lat = cráter físico). Detección dual-ROI, clustering
vent-anchored y distance_class anclan al CRÁTER. Cierra la regresión git-confirmada
S65→S80 (PR #220 regeneró mirova_center y revirtió el fix S65 sin saberlo, regla A63).
Guard anti-revert: `tests/test_detection_anchor.py`. Resultados: det→cráter Tupun
5.76→1.25 km, PCC 7.23→0.69, PP 2.69→1.14. Detalle: `docs/S98_ANCHOR_FIX_RESULTS.md`.
(Entrada agregada retroactivamente en S105 — AUDIT_S105 detectó que faltaba acá.)

## D11 — Sesgo topográfico de los paths MIR-absolutos (A69) — **CERRADA S114** (irreducible a 1 km; detección fiel a Coppola; todos los ejes agotados)

**Divergencia formal** (S104, formalizada S105 por AUDIT_S105): en volcanes nevados
(Villarrica/Tupungatito/Llaima) el campo nocturno BT MIR está dominado por el gradiente
topográfico de altitud (cumbre nevada fría ~272K vs valle tibio ~281K). Nuestro Test1
integrado mide "exceso sobre fondo de anillo" → capta el valle tibio como anomalía →
detecciones/centroides sesgados ~1 km al N del cráter + FP topográficos puros en noches
sin lava. **MIROVA es inmune** porque detecta por NTI con fondo local al cluster
(Coppola 2016a Tests; Coppola 2024 Eq.13) — la topografía se cancela por construcción.

Cronología del cierre (S104→S105, ground truth probe-based):
- **V1 co-validación NTI per-píxel — REFUTADO** (run 27186289487): apaga el Test1
  (la señal difusa sub-pixel no tiene firma per-píxel). Flag OFF.
- **V2 Test1 integra NTI con fondo de anillo — REFUTADO** (run 27223821692): corrige
  solo ~50 m de ~1000–1500 m. El NTI cancela el gradiente de gran escala pero el fondo
  de anillo entero deja pasar la estructura residual dentro del ROI 3 km. Inocuo
  (recall/magnitud preservados, controles sin cambio) pero insuficiente. Flag OFF.
- **k_sigma — REFUTADO offline**: la señal fuerte no está mejor anclada (el gatillo no
  mueve el centroide). **Anclas de brillo — REFUTADAS**: BT máx = valle (12–26 km).
- **Discriminante núcleo-anillo** (probes 27243090277 + 27244013547): separa lava/topo
  sin error en Villarrica pero NO generaliza como gate (Tupun cat-b real casi continuo,
  confirmado por Nicolás; Llaima lava débil con pico al lago). Pista, no fix.
- **Fondo LOCAL sobre NTI (Coppola 2024 Eq.13, uniforme) — REFUTADO S106** (S105 PR
  #386 flag OFF; A/B runs 27275241269 k=3.0 + 27276651420 barrido k=2.0/2.5, 30/30 jobs
  OK; predicciones pre-registradas design 2026-06-10 §12, A66): el sesgo SÍ se cura
  (offN nevados 1047/748/1097 → 182/170/206 m a k=2.0, Lastarria fumarólico conservado)
  PERO a TODO k del barrido el Test1 se apaga en noches de actividad REAL — Tupungatito
  pierde el trigger en 16/75 noches ALERTA (k=2.0; 58/75 a k=3.0 + 1 FN total el
  2026-03-31), Villarrica en 5/8 noches de lava confirmada. Mecanismo del límite: a
  escala del anillo local (0.5–1.5 km) la señal débil real es espacialmente SUAVE (la
  fuente sub-pixel templa a sus propios vecinos) e indistinguible de la suavidad
  topográfica; solo el contraste sub-pixel fuerte sobrevive (Láscar −8%). Veredicto por
  decisión pre-comprometida §12: NO promover a ningún k. Flag queda OFF (candidato a
  purga P2-8). Detalle: design doc §14–15.

**Estado S106**: los 3 fixes candidatos (V1, V2, fondo-local) compartían el supuesto de
que el sesgo topográfico es separable de la señal débil a alguna escala espacial — la
evidencia acumulada dice que a escala local NO lo es. La divergencia queda ABIERTA sin
candidato activo; el costo operacional es de POSICIÓN del ancla (~1–1.5 km N mediano en
nevados, A70), no de recall ni de magnitud (calibración 0.78–0.80× intacta S103).

Implicación al marco A54: el "extra" sobre MIROVA en nevados incluye FP topográficos
(cat-d), no solo cat-b real. Ver `docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md` (completo) y
`docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md`.

**CIERRE S114 (la cara MODIS far→summit; `docs/AUDIT_S114_PARITY_BY_SENSOR.md`)**: la
re-auditoría por sensor con data fresca destapó que el recall dashboard MODIS es 16% (vs 90%
pipeline-cráter) = bug de etiquetado A46 far→summit (el `final_hotspot` por MIR absoluto salta a
Salar/valle). Se exploró exhaustivamente cómo separar el foco real (Láscar) del difuso A69 (nevados)
y **se descartó TODO con datos**:
- **Discriminantes per-record** (barrido de 8 + escéptico ~17 single/~45 pares): AUC ~0.5; ninguno
  MISSION-puro separa. El único con AUC>0.8 (co-val VIIRS375-magnitud, 0.88) es cross-sensor (MISSION
  lo prohíbe). El hallazgo nuevo `roi95_nsigma` (0.87) lo mata el KILLER cat-b (focos reales en nevado
  Villarrica/Chaitén caen en la banda del difuso → cualquier umbral mata 40% de cat-b).
- **Frente B (N·σ Tabla 1)**: el N·σ canónico no separa (Láscar 3.5σ vs nevados 3.1σ, solapan); a 5σ
  literal Láscar-ALERTA queda 0/23 (apaga el foco real).
- **Auditoría de fidelidad file:line + adversarial**: la detección MODIS YA es FIEL a Coppola 2016a
  (dual-ROI 5/10 enable_dual_roi_bt, Tests 2∧3 OR `min(C1,μ+C2σ)`, σ global, second-run, ETI
  cuadrático, kernel 8-vec). **El difuso pasa GENUINAMENTE** (outlier espacial real a 1 km sobre
  topografía nival), no por bug. ~~Único gap de fidelidad literal: GAP #A (§298-300 retiro Test 1 K1
  del pool μ/σ, flag OFF) — backlog con A/B propio.~~ **GAP #A RESUELTO S115 = mislabel** (no es gap):
  §298-300 + Eq.6 → los Test 1 activos SÍ se reportan y reciben VRP; "discarded for further steps" =
  fuera del pool m,σ. ~~ya cubierto por el second-run~~ **⚠️ REABIERTO S128: las dos
  patas de este cierre son FALSAS, verificadas contra el código y el paper.** (a) El
  second-run recibe `active_mask=hot_mask_2d` y `hot_mask_2d = fp_hot` (sólo Tests 2∧3):
  los K1 (`nti_path_hot`) nunca entran, así que NO cubre el retiro del pool. (b) El flag
  citado
  `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` ~~controla el REPORTE (OFF = fiel), no el pool~~
  **gobierna el POOL de μ/σ, verificado S128**: decide si `nti_path_hot` se pasa como
  `test1_mask` a `first_pass_tests_2_and_3`, y adentro `build_unsuitable_mask` hace
  `unsuitable = unsuitable | test1_mask`. Se lo juzgó por su NOMBRE y no por cómo lo lee
  el código — A89. Está en `False`, así que hoy los píxeles más calientes de la escena
  entran al fondo, inflan μ y σ, y suben el umbral `μ + C2·σ`: el error va hacia el
  **falso negativo**. ~~No queda gap de fidelidad literal accionable; no amerita A/B.~~
  **SÍ amerita A/B** (pendiente #8 de `AUDIT_S128.md`). Guard:
  `tests/test_guard_gap_a_pool_musigma_s128.py`. Ver `AUDIT_S114` §6d y `AUDIT_S128.md` §6bis.
  - **✅ EL A/B SE CORRIÓ Y NO PUDO MEDIR NADA — S130. Decisión de Nicolás: queda
    DOCUMENTADO Y DIMENSIONADO, sin más inversión.** El A/B completo (dos chunks, 15 jobs,
    882 noches comunes, 13.766 records) dio las cuatro firmas **idénticas**: `pool` no
    movió **ninguna** de las suyas —conteo 883 vs 883, umbral 277,47 vs 277,47— y `bgmag`
    hizo lo contrario de lo predicho, tocando el conteo en 3 de 883 y no el ratio. Ninguno
    pierde noches MIROVA-confirmadas, pero eso no los salva: **no producen efecto**.
    - **La causa no es el flag sino el sustrato**: los píxeles K1 (NTI > −0,8) sobre los
      que el mecanismo opera aparecen en el **0,09 %** de las pasadas MODIS, **0,12 %** de
      VIIRS750 y **1,36 %** de VIIRS375. Por volcán, **Láscar 4,82 %** es el único con
      material y **Chaitén tiene CERO en 5.865 records** — el A/B eligió cinco volcanes de
      los cuales cuatro no tenían sobre qué actuar.
    - Se descartó primero lo barato: **no es A89** (los tres perfiles resuelven bien
      leyendo `pipeline.profile`) ni código que ignore los flags (los tres procesadores
      los consumen), y los brazos corrieron de verdad (hashes distintos).
    - **Físicamente es A80**: el NTI vive pegado a su piso (~−0,9) en señal débil sobre
      nieve; K1 = −0,8 fue calibrado contra volcanes con lava expuesta. Láscar —cráter
      caliente persistente, sin cobertura nival— es el único que lo cruza seguido.
    - **Esto NO cierra el GAP #A**: sigue siendo una divergencia real de fidelidad literal
      contra §298-300, y el guard de S128 se mantiene. Lo que hace es **acotar su alcance
      empírico** a menos del 0,1 % de las pasadas MODIS. Si algún volcán entra en fase
      efusiva, el sustrato cambia y vuelve a ser medible.
    - Si alguna vez se quisiera medir de verdad: **sólo tiene respuesta en Láscar**, con
      n≈219 pasadas V375, y **no se extrapola** a los otros diez. No repetir el A/B sobre
      más meses — el sustrato es estructural, no estacional.
    - Detalle: `docs/s130/AB_FONDOS_SIN_SUSTRATO.md` ·
      `experiments/_s130_ab_sustrato/medir_sustrato_k1.py` ·
      `experiments/_s129_ab_fondos/veredicto.py`.
- **Ejes ortogonales**: cap de magnitud REFUTADO (AUC 0.45; difuso entre Láscar y cat-b) y contexto
  temporal Method-2 REFUTADO (difuso tan variable como el foco, CV 0.84-1.22).

**Veredicto (A82)**: a 1 km el foco sub-píxel débil y el gradiente topográfico difuso son el mismo
objeto en todos los ejes medibles (espectral, magnitud, espacial, temporal); su única diferencia
(origen) no deja huella en el dato. **Irreducible dentro del clon literal.** Sin pérdida de alerta:
VIIRS375 (375 m) resuelve el foco y cubre el recall (A77). **NO reabrir** el far→summit MODIS con un
gate/discriminante/cap post-hoc (anti-A8). La cara POSICIÓN del ancla en nevados (~1-1.5 km N, A70)
queda como costo residual conocido, no de recall ni magnitud.

### D11-bis — El ancla honesta reporta `dist=0.0` para records Test1-only (divergencia formal, AUDIT_S106 P2.3)

El fix adoptado S106 (`enable_honest_anchor`, VIIRS375) ancla al **vent** los records
cuya única fuente es el Test1 integrado (`final_hotspot_source='test1_roi'`), reportando
`final_hotspot_dist_km=0.0` exacto. En producción son **2365 records** (Llaima 350,
Villarrica 343, Copahue 341, NdC 309, Tupungatito 259...). MIROVA **nunca** publica 0.0:
su `Distancia_km` es un offset variable volcán-específico (mediana global 1.68 km; de 969
ALERTAS solo 10 = 1.03% dan 0.0; Tupungatito mediana 5.21 km; incluso Villarrica "al
cráter" da 0.84 km fijo, A13). **Es divergencia literal de POSICIÓN** — trade-off
deliberado (evita el sesgo topográfico A69/D11; A/B run 27343409067 refutó la variante
NTI-peak), MIROVA-consistente en intención ("publicar el cráter") pero distinta en el
valor numérico. **NO toca magnitud (`pc.vrp_mw`) ni detección** (trig_t1 0-diffs pareados).
Pendiente (P2.3): tooltip en las 3 vistas declarando "dist=0.0 = posición = cráter por
semántica del Test1 integrado, no una medición" (hoy solo en comentario de código
index.html). Severidad: deuda de documentación + frontend, no rompe outputs primarios.

**Actualización S108 (A45, OK Nicolás): el ancla honesta se EXTENDIÓ a VIIRS750**
(flip `enable_honest_anchor_viirs750`, PR #416, A/B run 27468739388). Mismo `anchor.py`,
mismo trade-off de posición: nevados offN 753/125/562 → 0 m al cráter; Lastarria conserva
el NW de Lazufre (real); 32 flips far→summit (0 inflados pc.vrp>5). Detección/magnitud
intactas (diff del path-magnitud V750 = +157/−0; el único delta C1 fue 1 granule borderline
Villarrica 2026-06-07 lava lake = artefacto NRT-vs-Standard del producto L1B, NO el flag —
auditado en `experiments/_s106_fase2/audit_v750_paired.py`, A18-adyacente). Promovidos los
5 vols del A/B (`merge_promote_v750.py`); los 6 Tier A restantes en reproc (run 27482258622).
El espejo MODIS sigue OFF (D12, gateado por el fix de magnitud fondo-local §2). Tag rollback:
`pre-s108-honest-anchor-v750`.

### D12 — MODIS Láscar pierde ~70/79 alertas por `distance_class` del píxel Salar (AUDIT_S106 P1.1) — ⚠️ **SECCIÓN CONGELADA EN S106/S108; leer primero la nota S125**

> **Nota S125 (anti-A8).** Lo que esta sección presenta como fix pendiente —reprocesar la
> historia de Láscar MODIS derivando `distance_class` del cluster— **ya se probó y se
> rechazó**: `docs/AUDIT_S121_D12_AB.md` = **VEREDICTO NO ADOPTAR** (cura 76 noches de
> Láscar pero destapa el path-D, PCC 117 MW). El candidato siguiente (C2 peak-of-kernel)
> quedó **refutado en S122**. La divergencia sigue abierta como fenómeno; el camino que
> esta sección propone, no. Ejecutarlo sería reabrir trabajo cerrado.

Distinta de D11 (que es posición de nevados) y de A54 (real-no-publicada): acá **MIROVA SÍ
publica** y nosotros lo perdemos. El `primary_cluster` MODIS está en el cráter (mediana
1.46 km ≈ MIROVA 1.41 km) pero el píxel suelto más caliente cae en el **Salar de Atacama**
(16-32 km) → `distance_class='far'` → el gate `mirovaEqVrp`/`audit_metrics.py:79` lo anula.
El rescate F47 no dispara (`hotspot_dist<25 km`). Es el **espejo MODIS** del bug que el
ancla honesta resolvió en VIIRS375 — el espejo MODIS del ancla está flag-OFF, gateado por
el fix de magnitud fondo-local (design 2026-06-13). FN sobre señal confirmada = lo más
grave en monitoreo. Fix: reproc histórico F2 Láscar MODIS (pipeline actual nadir-fijo) →
`distance_class` desde el cluster. Corrige el "0 pérdida" fabricado de AUDIT_S95 (P1.2).

## S105 — Nota de decisión pendiente: gates intra-radio S84/S85 (A55)

AUDIT_S86 §C6 los declaró anti-patrón emergente (redundantes con la supresión
`mirovaEqVrp` del frontend desde S33). Siguen ON en `mirova_equivalent.yaml`.
**Decisión de Nicolás (S105): decidir con más datos al cerrar el frente Test1/
fondo-local** (toca la misma zona del pipeline). No revertir ni re-justificar aún.
Registrado para que no se pierda (AUDIT_S105 contradicción #1).

> **Actualización S116 (AUDIT_S116 C2 — investigado, ver `docs/AUDIT_S116_C2_GATES.md`):**
> workflow read-only de 4 ángulos. Hallazgos que **refinan** el framing "redundante → revertir":
> (1) son **PARCIALMENTE** redundantes con el frontend — mismo umbral espacial pero plano distinto
> (el gate cambia el DATO persistido `n_anomalous`/`pc.vrp_mw`/footprint/`distance_class`; el frontend
> solo la VISTA, devolviendo 0). (2) `path_d_intra_radio` es **MODIS-only** y SUPRIME path-D fuera del
> inner; `second_pass_intra_radio` (MODIS+VIIRS) PRESERVA el first-pass y solo recorta recaptura nueva
> fuera del inner (NO elimina el cluster near-crater artefacto A55 dentro del inner). (3) **Impacto
> BIMODAL**: de 4560 records summit-intra preservados, solo 26.7% MIROVA-confirmados, pero en
> focales/desérticos es **cat-b REAL** (Láscar 49%, Lastarria 46% → revertir destruiría recall) y en
> nevados ~puro artefacto A55/A69 (Llaima 0.4%, Villarrica 2%, cola pesada hasta 60 MW). **Veredicto:
> NO revertir global; respetar S105; A/B reproc estratificado por volcán cuando reabra el frente
> Test1/fondo-local** (desenlace probable: gate per-volcán ON-nevados/OFF-focales o discriminante
> no-geométrico, no flip global). El read-only mide lo que el gate PRESERVA, no lo que REMUEVE (exige
> reproc, A18). La contradicción C2 pasa de "standing sin decisión" a **decisión informada + plan**.

> **✅ RESUELTO S118 (flip OFF, PR #474, tag `pre-s118-c2-flip`).** El A/B real con reproc
> (`docs/AUDIT_S118_C2_GATES_AB.md`, run 28312968093, 180/180, criterio pre-registrado A66
> "robo de cluster espacial") midió lo que el read-only S116 no podía (la REMOCIÓN, A18):
> **0 robos de cluster en 214 noches focales MIROVA-confirmadas** en los 3 brazos — la cerca
> no protegía nada; el cráter conserva el cluster primario por sí solo (selección vent-anchored
> robusta). Ratio de magnitud mediano 1.000; costo = cola inflada 0.5-1.3% (mayormente far,
> 42/46 filtradas por frontend; peor caso difuso A69/A82 no-MIROVA-conf). El temor S116
> "revertir destruiría recall focal" no se materializó: el gate ON/OFF no cambia los records
> summit focales (el A/B los midió idénticos). El desenlace "gate per-volcán" quedó EXCLUIDO
> por MISSION l.77 (no conmuta método por régimen — mismo trap que Eq.16 por-volcán S99).
> Ambos gates → `false` en `mirova_equivalent.yaml`; guards de intención
> `test_operacional_flipped_off_S118` ×2 protegen contra re-encendido por consolidación (A63).
> Verificación post-flip S119 Eje 1: NRT 100% verde, recaptura estable, sin inflación summit
> sistemática, JSONs contenidos (`docs/AUDIT_S119.md` §1) → **MANTENER OFF, cerrado**.

## S105 — Residuo path D MODIS re-dimensionado (corrige diagnóstico inflado)

Un diagnóstico de subagente reportó "campo difuso MODIS universal ~280 recs/volcán a
16-24 km" — REFUTADO (usaba `final_hotspot_dist_km` corrupto + vrp scene-wide, A48/A10).
Cuadro real con `primary_cluster`: el cluster MODIS está al cráter (mediana 1.3–3.3 km)
y calibrado (pc.vrp mediana 0.6–1.9 MW). El residuo path D real = **131/3072 records
(4.3%) con pc.vrp>5 MW, 80% path-D-only, 0% confirmados MIROVA** (cruce loader
canónico) → artefacto de MAGNITUD acotado cerca del cráter, frente SECUNDARIO.
Detalle: design doc 2026-06-05 §11.

---

## D13 — La cerca `distance_class != summit` del frontend apaga el 31 % de la magnitud — **ABIERTA (documental)** S124

**Qué hace MIROVA.** Publica el hotspot **esté donde esté** dentro de su grilla de
51×51 km. Su producto per-volcán reporta la distancia (`Distancia_km`) como un
atributo del dato, no como un filtro: una anomalía a 12 km del cráter aparece
publicada, con su distancia al lado, y es el analista quien decide qué significa.

**Qué hacemos nosotros.** Las 3 vistas del frontend comparten el helper
`mirovaEqVrp` (`frontend/index.html:972`, replicado en `diario.html` y
`mosaico.html`), que **pone la magnitud en cero** para todo record cuyo
`distance_class` no sea `"summit"`. El dato sigue en el JSON; simplemente no se
dibuja salvo que el usuario active el toggle "incluir lejanas".

**Alcance medido** (script `experiments/_s124_observabilidad/`, sobre los 11 Tier A):

| condición del helper | records apagados | magnitud |
|---|---|---|
| `distance_class != "summit"` | **10.773 / 34.763 (31,0 %)** | 17.678 MW |
| `pc.centroid_dist_km > inner_radius` | **0 (0,0 %)** — no-op | — |

Dos cosas que corrigen creencias previas de sesiones anteriores:

1. **La segunda condición es un no-op hoy.** Existía para atrapar la asimetría
   A46 (un record `summit` por `final_hotspot` pero con el cluster lejos). El
   guard de coherencia de S113 (`store.py`) ya alinea ambas representaciones en
   origen, así que la cerca del frontend no encuentra nada que apagar. No es
   código muerto — es defensa en profundidad — pero **no** es la cerca que
   importa.
2. **La cerca que importa es la primera**, y es mucho más grande de lo que se
   había estimado. El reparto por volcán es notablemente plano (897 a 1192 por
   volcán), lo que apunta a un fondo sistémico de detecciones lejanas y no a una
   idiosincrasia de algún volcán.

**Por qué queda ABIERTA como documental y no se toca.** El 31 % apagado NO es
error: es en buena parte la categoría (b) de A54 —anomalías térmicas físicamente
reales que MIROVA no publica— más el artefacto topográfico A69 en los nevados,
que a 1 km es irreducible (A82). Levantar la cerca destaparía ambas cosas
mezcladas. Lo que se corrige acá es que **esta divergencia no estaba escrita en
ningún lado**: una decisión de display que mueve el 31 % de la magnitud publicada
merece estar en el catálogo, no vivir implícita en un helper de JavaScript.

**Anti-A8**: no reabrir como "hay que levantar la cerca" sin antes clasificar por
categoría A54 los records que se destaparían. Y ojo con A72: si lo que se destapa
es artefacto, la raíz es no generarlo en la detección, no la cerca.

### Clasificación cumplida — S126

Esa consigna se cumple acá. Lo que la hizo posible es un hallazgo de S126: existe
una **firma espacial** del artefacto topográfico — el clúster cae en el anillo
`[1,5–3] km`, que es justo donde el fondo autorreferente lo fabrica.

Sobre los 2.694 records que la cerca apaga (34 % de los 8.033 con VRP, 2026-05-01
a 2026-08-28, script `experiments/_s126_d13/01_que_apaga_la_cerca.py`):

| categoría | fracción |
|---|---|
| clúster en el anillo `[1,5–3] km` | **36,9 %** — misma firma que el artefacto documentado |
| clúster a menos de 1 km del cráter | **14,8 %** — candidato a señal real (cat-b, A54) |
| corroborados por una alerta de MIROVA | **41 de 2.694 (1,5 %)** |

Y el dato que explica la etiqueta: **el `final_hotspot` de estos records está a
19–24 km**, mientras su clúster está a **1,45–4,11 km**. Un salar, un lago o un
incendio le roba el máximo de escena y arrastra el `distance_class`, pero el
clúster sigue siendo crateriano. Es la asimetría A46/A81, no una detección lejana
de verdad.

**Lo que esto reencuadra.** La cerca **no protege del artefacto**: el mismo objeto
pasa cuando queda etiquetado `summit`. Villarrica publica 380 detecciones desde
mayo con el 92 % del clúster a más de 1,5 km del cráter, todas en rojo, porque
2,8 km < `inner_radius` 5 (`docs/S126_COSTO_FILTRO_CONTEXTUAL.md`). La cerca es
**ortogonal** al problema del artefacto.

**Consecuencia para la decisión.** Levantarla destaparía sobre todo más del mismo
artefacto (37 %) y corroboraría casi nada (1,5 %). Mantenerla tampoco resuelve
nada, porque el artefacto entra por el otro lado. **D13 deja de ser una palanca**:
la palanca es no generar el artefacto — el frente del fondo autorreferente.

**Estado S126**: clasificación **CERRADA**; la divergencia queda como documental
sin acción propia. No volver a plantearla como "levantar o no la cerca".

---

## D14 — La máscara de nube BT<260 K — **CERRADA** S128 (cita verificada verbatim contra el PDF)

**Qué dice MIROVA.** No filtra nube. Laiolo 2026, textual: *"no atmospheric
correction or cloud-contamination automatic filtering"*. Por eso
[`MISSION.md`](MISSION.md) l.127 lista `Cloud mask BT<260K` en la tabla de
parches **rechazados**, con estado *"Removido S27"*.

**Qué hace el código.** `pipeline/process_viirs.py:674-682` la aplica:

```python
CLOUD_BT_THRESHOLD = 260.0                      # K
cloud_free = bands["I05"] >= CLOUD_BT_THRESHOLD
roi_mask   = roi_mask & cloud_free              # <- modifica la DETECCIÓN
bg_mask    = bg_mask  & cloud_free              # <- y el FONDO
```

No es una anotación: saca píxeles del ROI donde se buscan anomalías **y** del
anillo que fija el umbral. Es la segunda contradicción doc-vs-código encontrada
en S124 (la otra, los pisos VRP, se corrigió en #523). Solo afecta a VIIRS
375 m; MODIS y VIIRS 750 no la tienen.

> ⚠️ **Corrección S125 — la última frase es imprecisa y esconde el fix.** MODIS
> **sí tiene** la máscara (`process_modis.py:505` y `:715`), sólo que la lee de la
> perilla del perfil `CLOUD_MASK_BT_K`, hoy en `0.0` — o sea el predicado queda
> tautológico y la máscara inerte. Lo mismo VIIRS 750. **El caso raro es VIIRS 375**:
> `process_viirs.py:674` tiene `CLOUD_BT_THRESHOLD = 260.0` **hardcodeado** e ignora
> la perilla, aplicándolo a `roi_mask` y `bg_mask` en `:678-681`.
>
> Consecuencia práctica que la sección no sacaba: **la perilla correcta ya existe y un
> solo sensor no la usa**. Retirar la máscara no es la decisión metodológica abierta
> que el texto plantea (opción 1) — es reemplazar un literal por la constante del
> perfil, una línea. Sigue requiriendo A45 por tocar `pipeline/`.
> Ver `docs/AUDIT_S125_PROFUNDA.md` §1 F3.

**Y además mide la cosa equivocada.** El hallazgo salió de que Nicolás no
reconocía como despejadas semanas que él sabe que fueron de temporal (A62: la
insistencia del experto es señal). Físicamente:

- Un umbral único a 260 K (−13 °C) detecta nube **alta y fría** — cirros, topes
  convectivos. La nube baja de una tormenta invernal tiene su tope entre −10 y
  0 °C, o sea **263-273 K**: pasa como cielo despejado.
- A la altitud de estos volcanes el **terreno nevado irradia en ese mismo
  rango**. Medido sobre NdC: en el **76 %** de las pasadas que el proxy llama
  despejadas el fondo está bajo 0 °C, donde nube baja y nieve son
  indistinguibles para un umbral de temperatura único. Mismo mecanismo que A68
  (el proxy cirrus `t_bg<270K` contaminado por altitud).

**Lo que NO explica.** Se probó si la máscara causa el déficit de paridad de
S124: la correlación entre el ratio per-volcán y los píxeles enmascarados es
**r = −0,23**, débil. No es el driver del gap.

**Por qué queda ABIERTA y no se toca todavía.** La máscara actúa sobre el
**fondo**, y el frente F70 (grilla UTM) también. Decidir la máscara antes de
saber qué hace la grilla sería apilar dos correcciones que interactúan — el
error que A66 documenta. Orden correcto: veredicto de F70 primero, máscara
después.

**Cuando se retome, las opciones son tres**, y la decisión es de MISSION, no
técnica:
1. **Quitarla** — es lo que dice el clon literal (MIROVA no filtra) y lo que
   `MISSION.md` ya declara hecho.
2. **Reemplazarla por la máscara oficial del sensor** — `MOD35_L2` y
   `CLDMSK_L2_VIIRS_{SNPP,NOAA20,NOAA21}`, verificadas disponibles en CMR con
   versión NRT (S124). Usan ~15 tests espectrales diseñados justamente para
   separar nube de nieve. Cuesta una descarga extra por granule. Sería
   **beyond-MIROVA**: mejor que el original, no un clon.
3. **Dejarla y corregir MISSION.md** — la salida honesta si se decide que el
   filtro aporta, pero exige justificar por qué divergimos.

**Lo que NO es la respuesta**: una API meteorológica (ERA5, GFS). Da cobertura
en celdas de ~28 km y por hora — no resuelve un ROI de 50 km ni el instante del
sobrevuelo, y es salida de modelo, no observación. La ventaja de la máscara del
propio granule es que mide *ese* píxel en *ese* momento; el problema actual no
es la fuente, es que el test es demasiado pobre.

**Gap de schema asociado (A7).** El pipeline persiste `n_cloud_masked` (cuántos
píxeles enmascaró) pero **no cuántos tenía el ROI**, así que del JSON no se
puede reconstruir una fracción. La variable existe local (`np.sum(roi_mask)`);
solo falta retornarla.

---

## ✅ VERIFICACIÓN S128 — la cita SÍ es textual; el PDF estaba en el repo

**Desenlace: D14 se cierra. La cita era correcta.**

`documentacion/s00445-025-01932-y.pdf` — *Bulletin of Volcanology* (2026) **88:11**,
21 páginas — estaba en el repositorio todo el tiempo, **nombrado por DOI**. Buscar
«laiolo» daba cero, y el cero se leyó como ausencia: es A89, cuarta instancia del día y
otra vez del lado de quien auditaba. El adjunto de Zotero (`M7NUCUVL`) apuntaba
directamente a esa ruta.

**Texto verificado, p. 4:**

> *"The VRP time series (Fig. 2) coming from the different sensors/detectors are combined
> and filtered in terms of distance and/or intensity of the thermal anomaly to minimize
> the false alerts and the double counting (coming from different detectors acquiring at
> the same time) thus resulting in 9712 data points (ca. 12%). **Importantly, no
> atmospheric correction or cloud-contamination automatic filtering is applied to the
> dataset.**"*

La atribución era correcta y la nota del Vault fiel. **El apagado de la máscara es
clon-literal**, con fundamento verificable. La reapertura queda anulada.

### Pero el párrafo dice tres cosas más que sí nos faltaban

**1. MIROVA SÍ filtra — por distancia y por intensidad — y se queda con el 12 %.** De
82.329 imágenes salen **9.712 puntos**. Lo que no hace es filtrar *nube*; sí descarta por
distancia, por intensidad, y por **doble conteo entre detectores que adquieren a la misma
hora**. Ese último punto **valida por escrito nuestra convención** de un par por noche con
el máximo de ambos lados, que hasta ahora era una decisión nuestra sin respaldo citado.

**2. Su mitigación de nube es tomar el MÁXIMO DIARIO, no enmascarar.** Textual:
*"we first calculated the daily maximum VRP values. This step minimize potential
underestimation due to cloud-contamination and unfavorable satellite viewing geometry"*.
Nosotros publicamos por pasada. Es la misma familia que el Método-2 de agregación semanal
ya documentado, y sigue sin implementarse.

**3. La incertidumbre declarada del propio MIR-method es ±30 %**, sobre emisores con
temperatura radiante efectiva **>600 K**. Nuestra banda de paridad es [0,5–2,0] y
perseguimos diferencias de factor 2: conviene tener presente que la referencia declara
±30 % de incertidumbre propia.

### ⚠️ Corrección al hallazgo del corte de 0,1 MW

La frase existe y es **verbatim** (p. 8):

> *"We do not consider minor inflections recognized at VRP < 0.1 MW because these values
> are likely associated to cloud and/or to bad geometry acquisition (Coppola et al. 2014;
> 2016)."*

**Pero yo la sobre-interpreté al reportarla.** No dice que MIROVA aplique un piso de
0,1 MW a lo que publica. Está en el análisis de los **puntos de inflexión de la
distribución de probabilidad de logVRP**, con el que definen cuatro niveles de actividad
térmica: lo que descartan son *inflexiones menores como frontera de régimen*, no
detecciones.

Lo que **sí** sostiene, y no es poco: el propio grupo MIROVA considera que **los valores
bajo 0,1 MW son probablemente nube o mala geometría**. Nuestro frente de artefacto vive en
0,04-0,06 MW y las 8 detecciones que perdió el brazo corona en S127 estaban en
0,021-0,042 MW. Es un argumento de autoridad para revisar el piso VRP — **no** una
instrucción de implementar un corte a 0,1 MW.

---

## Registro S127 — el A/B que respalda el apagado (evidencia empírica, intacta)

**Decisión de Nicolás (S127): sostener el apagado y documentarlo como decisión.**

Estado del código, verificado leyendo `pipeline.profile` y no el YAML:
`CLOUD_MASK_BT_K = 0.0` en el perfil operacional, o sea el predicado
`bt > CLOUD_MASK_BT_K` es tautológico y la máscara está inerte en los tres
sensores. El literal `260.0` que VIIRS 375 tenía hardcodeado —la anomalía que la
corrección S125 de arriba señalaba— **ya está reemplazado por la perilla**
(`process_viirs.py:772`), con dos guards: `tests/test_cloud_mask_from_profile_s125.py`
y `tests/test_cloud_mask_operacional_s126.py`.

**Por qué se sostiene el apagado**, en este orden:

1. Es lo que dice el clon literal. Laiolo 2026, textual: *"no atmospheric
   correction or cloud-contamination automatic filtering"*. `MISSION.md` ya lo
   declaraba removido desde S27, y el perfil lo declara en 0 desde S29
   (2026-05-01) — o sea el apagado no es una divergencia nueva, es alinear el
   código con lo que la metodología decía hace cuatro meses.
2. **Recupera 176 de 181 noches ciegas**, 157 de ellas con detección. El
   problema mayor de la máscara no era filtrar de más: era que ocultaba el hecho
   de que no estábamos mirando — esas noches figuraban como "sin señal" sin que
   nadie hubiera visto nada.
3. El costo medido es chico: el fondo baja entre medio grado y dos, y ningún
   volcán sale de banda.
4. Y mide la cosa equivocada de todos modos (sección de arriba): un umbral único
   a 260 K ve nube alta y fría, pero la nube baja de temporal tiene su tope en
   263-273 K y pasa como despejado — y a esta altitud el terreno nevado irradia
   en ese mismo rango.

**Cómo se llegó acá, que es la parte incómoda.** El apagado entró en producción
por el PR #535, cuyo comentario decía «no-op». No lo era. El A/B que debía
autorizarlo corrió después, en S126, y validó algo que ya estaba vivo. La
decisión de S127 es ratificar con el resultado en la mano; la alternativa
—revertir y re-encender formalmente— se evaluó y se descartó porque dejaría 181
noches ciegas mientras tanto para llegar al mismo destino.

Esa secuencia es la instancia #1 del eje T9 (`PROTOCOLO_AUDITORIA_PROFUNDA.md`)
y el origen de la regla: *un no-op necesita un test detrás, o es una intención.*

**Lo que esto NO cierra.** Apagar la máscara destapó 286 detecciones nuevas, de
las cuales **sólo 21 caen en noches que MIROVA confirma**, con distancia mediana
2,4-2,7 km al cráter — la firma exacta del artefacto del anillo autorreferente
[1,5-3] km. Eso **no es recall nuevo**: es el artefacto que dejó de estar tapado.
Se cierra por el frente del fondo, no por el de la máscara. Si el A/B de la
corona Eq.6 sale bien, buena parte de esas 286 debería desaparecer sola, porque
una fluctuación de terreno medida contra su corona inmediata da ΔL ≈ 0.

**Lo que queda anotado como mejora posible (no clon-literal).** La máscara
oficial del sensor —`MOD35_L2` y `CLDMSK_L2_VIIRS_{SNPP,NOAA20,NOAA21}`,
verificadas disponibles en CMR con versión NRT (S124)— usa ~15 tests espectrales
diseñados justamente para separar nube de nieve. Sería **beyond-MIROVA**: mejor
que el original, no un clon. No se adopta acá.

**Gap de schema que sigue abierto (A7)**: se persiste `n_cloud_masked` pero no el
total del ROI, así que del JSON no se puede reconstruir una fracción. Con la
máscara apagada `n_cloud_masked` es 0 siempre, así que hoy no molesta — pero si
alguna vez se enciende algo, el gap vuelve.

Evidencia: `docs/S126_CLOUDMASK_RESULTADO.md` (veredicto) y
`docs/S126_CLOUDMASK_YA_ESTA_VIVA.md` (cómo se descubrió).

---

## D15 — `Distancia_km` de MIROVA está CUANTIZADO a celdas de su grilla — **HALLAZGO** S124

**Origen.** Nicolás preguntó *"las distancias que me das de MIROVA, ¿respecto a
qué punto son?"*. Yo había **asumido** que medían desde la coordenada GVP.
Auditar en vez de asumir dio algo mejor que la respuesta buscada.

**El hallazgo.** El `Distancia_km` que MIROVA publica **no es una distancia
continua a un punto**: es el offset en **celdas enteras** de su grilla
resampleada. Cada valor es `√(i²+j²)·celda` con `i, j` enteros:

| sensor | celda | registros compatibles | valores distintos |
|---|---|---|---|
| MODIS | **1,000 km** | **10.085 / 10.085 = 100 %** | 40 |
| VIIRS375 | **0,375 km** | **11.810 / 11.810 = 100 %** | 450 |

Los valores crudos de MODIS lo muestran a simple vista:

```
0 · 1 · 1,41 · 2 · 2,24 · 3,16 · 3,61 · 6,40 · 7,81 · 8,06 · 9,06 · 9,49 · 10,63
0 · 1 ·  √2  · 2 ·  √5  ·  √10 ·  √13 ·  √41 ·  √61 ·  √65 ·  √82 ·  √90 ·  √113
```

Control: con celdas arbitrarias el ajuste cae (VIIRS375 a 0,5 km → 89 %; a
0,25 km → 93 %), así que el test no es trivial. Script:
`experiments/_s124_cuantizacion/01_distancia_es_celdas.py`.

**Por qué importa — tres consecuencias**

1. **Confirmación independiente del frente F70.** La grilla de MIROVA no es
   solo una afirmación de sus papers: está impresa en cada dato que publican, y
   sus celdas son **exactamente** 1 km (MODIS) y 375 m (VIIRS I-band) — las que
   F70.2 ya implementó (#525, #527). Esto vale como verificación externa del
   diseño, obtenida de la ground truth y no de la bibliografía.
2. **La referencia es una CELDA, no un punto.** *"Distancia 0,00 km"* NO
   significa "en el cráter": significa **"en la misma celda que la
   referencia"**, o sea en cualquier lugar de un cuadrado de 375 m. Coppola dice
   que la grilla va *"centred on the volcano's summit"* pero no publica esa
   coordenada, así que el centro exacto sigue siendo desconocido.
3. **Toda comparación de distancias contra MIROVA arrastra ±media celda.** Un
   ratio de distancias sub-celda no significa nada. Esto **matiza A13**
   (Villarrica 0,84 km fija): esa idiosincrasia es consistente con una celda
   fija de la grilla, no necesariamente con una coordenada GVP.

**Aplicación inmediata.** El mapa de NdC (`experiments/_s124_ndc_focus/`) dibuja
la celda **como regla de escala en una esquina, NO anclada al cráter**. La
primera versión la dibujó centrada en el cráter y Nicolás lo objetó con razón:
eso da a entender que la grilla de MIROVA está alineada con el cráter activo, y
**no lo sabemos**. Del dato se deduce el TAMAÑO de la celda; su POSICIÓN queda
indeterminada. Anclarla al cráter era volver a inventar precisión, solo que de
otra forma.

**RESUELTO en la misma sesión — los GeoTIFF del archivo TIENEN la grilla.**
Nicolás sugirió explorar los TIF/KMZ no explotados y ahí estaba la respuesta:
los TIF de `../mirova-tif-archive` están georreferenciados (EPSG:4326). De
`20260520_044801_VIIRS375.tif` (NdC):

- **Grilla 134×134** — confirma la deducción de F70.2b desde el producto real,
  no desde los papers. MODIS: **51×51** con celda ~1 km. Origen y extent FIJOS
  entre pasadas (grilla estática).
- **Centro de la grilla: (-36.863270, -71.378535)** — a 140 m del GVP y a
  **439 m al NORTE del cráter Nicanor**. La grilla NO está centrada en el
  cráter activo, y el cráter cae al borde de una celda (a ~56 m del borde N de
  la suya en la reproyección). La sospecha de Nicolás ("¿justo la celda cubre
  simétricamente el cráter?") era correcta: no lo cubre.
- **Caveat**: el TIF es una reproyección lat/lon de visualización de su grilla
  UTM (celdas 382×381 m, no 375 exactos). Se probó inferir la celda de
  referencia del `Distancia_km` contra las 4 alertas al cráter de NdC y **no
  cerró (0/4)** con las dos candidatas — la cuantización vive en la grilla UTM
  original, no en esta reproyección. Determinar la celda de referencia exacta
  requiere trabajar en UTM (pendiente menor).
- El KMZ es solo un PNG georreferenciado (GroundOverlay), mismo extent, sin
  vectores: no agrega sobre el TIF.

**Frente restante (menor) — la celda de referencia exacta del Distancia_km.** La
pregunta *"¿dónde caen sus bordes de celda?"* es respondible con los datos que
ya tenemos: hay **903 pares** (alerta MIROVA + detección nuestra en la misma
pasada, ±3 min) sobre los 11 Tier A. Si su hotspot y nuestro cluster son el
mismo objeto físico, cada par restringe el origen módulo el tamaño de celda; con
903 restricciones el origen queda determinado.

Importa para F70: **implementamos el tamaño de celda correcto, pero anclamos
nuestra grilla al `mirova_center`/cumbre nuestra**. Si el origen de MIROVA está
desplazado, nuestras celdas no coinciden con las suyas y el sustrato de
detección difiere aunque la resolución sea idéntica — dos píxeles del mismo
tamaño pero corridos median vecindarios distintos. Pendiente de diseñar; no
bloquea el A/B de F70.3, pero puede explicar un residual.

---

## D16 — La grilla UTM NO explica el sub-reporte — **CERRADA (refutada) S124**

**Qué se probó.** El frente F70 postuló que nuestro sub-reporte de magnitud
venía del sustrato geométrico: MIROVA detecta sobre una grilla UTM resampleada
y nosotros sobre el swath crudo, donde "los ocho vecinos" son objetos distintos
en cada pasada. A/B de 4 brazos con criterios pre-registrados (A66), 11 Tier A,
ventana 2026-06-25..08-24.

**Resultado: la hipótesis se refuta.** Detalle en
[`S124_F70_VEREDICTO.md`](S124_F70_VEREDICTO.md).

| | Láscar | Isluga | Lastarria | Tupungatito (juez) |
|---|---|---|---|---|
| control | 0,47 | 0,70 | 0,36 | 0,81 |
| **A** (grilla sola) | 0,46 | 0,69 | 0,34 | 0,82 |
| **B** (grilla + kernel) | 0,58 | 0,81 | 0,34 | **0,81** |
| C (kernel solo) | 0,58 | 0,81 | — | 0,81 |

Tres lecturas, todas con dato:

1. **La grilla sola es nula**: A ≡ control.
2. **B ≡ C**: todo el efecto viene del kernel de vecinos; la grilla no aporta
   nada encima. La hipótesis era que la grilla haría funcionar al kernel — no lo
   hace.
3. **El kernel tampoco alcanza**: Láscar 0,47→0,58, dirección correcta,
   insuficiente.
4. 🔴 **CORRECCIÓN (cierre S124)**: la tabla original omitía a
   **PuyehueCordonCaulle** por un bug de alias (trampa A14). Con PCC incluido:
   **control 0,75 ✓ → B 0,64** — el brazo B lo **saca de banda**. Es el único
   daño real del experimento, y refuerza el NO ADOPTAR. Las lecturas 1 y 2 de
   arriba quedaron además matizadas por la ADENDA 1 del veredicto (el efecto es
   MIXTO, no nulo).

**Verificación de que el regrid sí corrió** (no es un falso negativo por flag
apagado): las coordenadas de los píxeles anómalos pasan de estar dispersas en
el control (separaciones de 6-37 m, swath crudo) a estar **cuantizadas a 375 m
exactos** en A y B.

**Sin daño colateral**: recall VIIRS375 96 % → 96 %, sin migración de cluster
(±0,08 km), 0 de 19 eventos ancla perdidos.

**NO REABRIR** como "probemos la grilla" (anti-A8). Lo que queda vivo es otra
cosa: ver D17.

---

## D17 — Nuestra grilla F70 se centró en el punto equivocado — **ABIERTA (premisa probada, consecuencia NO)** S124/S125

> 🟢 **S130 — el mecanismo geométrico SÍ quedó probado, por otro eje: el ÁNGULO.**
> S128 concluyó que D17 y el gap de magnitud eran el mismo problema, pero le faltaba
> el control que separara «perdemos nosotros» de «MIROVA infla». Ese control ya está
> (`docs/s130/GRADIENTE_CENITAL.md`): el ratio nuestro/MIROVA cae de **0,740 cerca del
> nadir a 0,253 más allá de 50°** en VIIRS375 (n = 2.767, monótono en cinco bins), y
> mirando numerador y denominador por separado, **MIROVA es plano** (0,23–0,27 en los
> cinco) mientras **lo nuestro cae 2,7×**. VIIRS750 repite el patrón (n = 416). La
> explicación es Coppola 2014 §2.2: MIROVA **remuestrea** a malla de área constante, así
> que su magnitud no depende del ángulo; nosotros integramos sobre el píxel tal como
> viene. ⚠️ **En MODIS NO está probado** — sus bins no son monótonos (0,778 · 0,828 ·
> 0,862 · **1,253** · 0,400) y tienen 17-21 pares cada uno. Y ojo con el corolario:
> **D5 = 0,73 no es parejo**; es 0,74 a nadir y 0,25 en oblicuo, así que la mediana
> global promedia dos regímenes y esconde que el mecanismo es geométrico (A90 sobre el
> eje angular). El brazo fiel sería **bow-tie + regrid en ese orden** — Coppola 2012
> §3.2 pone el bow-tie como paso (i), y regridear sin de-solapar duplicaría píxeles
> calientes, inflando en dirección contraria al error. Es cirugía de núcleo, no un flag:
> S130 lo deja medido, no implementado.

> 🔴 **SEGUNDA CORRECCIÓN (28-ago, cierre).** La correlación que se citaba como
> apoyo empírico (r = −0,47) usaba el offset **contra el cráter**, la variable
> que esta misma sección declara equivocada. Con la correcta (vs
> `mirova_center`): **r = +0,054** — no hay señal. Y el caso decisivo la
> contradice: PCC tiene el offset más chico (147 m) y el mayor daño (−0,104).
> **La desalineación es real y está verificada; que cause el sub-reporte NO.**

> ⚠️ **CORREGIDA el 28-ago.** La primera versión midió el offset contra
> `vent_lat/lon` (el cráter) y presentó como hallazgo algo que **ya estaba
> documentado** en `pipeline/geo_utils.py:14-22` desde S98: que el frame de
> MIROVA está lejos del cráter en Tupungatito (4,86 km), PCC (7,57 km) y PP
> (2,02 km). Eso es una **separación deliberada de roles**, no un error —
> `mirova_center` es el marco de la imagen, `vent` es donde está el calor.
> Redescubrirlo fue una trampa A50: la respuesta estaba en el repo.

**El hallazgo que SÍ queda en pie**, con la medición correcta:

Nuestro regrid F70 se centró en `volcano["lat"]/["lon"]` (el centroide del
volcán, lo que `run_pipeline` pasa como `volcano_lat/lon`). MIROVA centra en
`mirova_center` (verificado: el `mirova_center_lat/lon` del yaml, derivado de
los KMZ en S80, coincide con el centro de los GeoTIFF dentro de 10-408 m).

| volcán | offset F70 vs MIROVA | | volcán | offset |
|---|---|---|---|---|
| **Tupungatito** | **2996 m** | | Isluga | 368 m |
| **Planchón-Peteroa** | **1873 m** | | Lascar | 186 m |
| Chaitén | 396 m | | PuyehueCordonCaulle | 147 m |
| Villarrica | 389 m | | Llaima | 142 m |
| NevadosDeChillán | 385 m | | Copahue | 140 m |
| | | | Lastarria | 115 m |

Mediana **368 m**, máximo 2996 m. Con celda de 375 m, **un offset > 187 m ya
desplaza la partición media celda**: eso ocurre en **6 de 11**.

**Y hay un cabo suelto que lo hace verosímil**: `pipeline/geo_utils.py` define
`get_grid_center()` justamente para esto — devolver el centro de grilla de
MIROVA con prioridad `mirova_center` → `vent` → `lat/lon`. **Nadie la llama.**
Existe desde S98, sin uso.

**Evidencia empírica a favor** (S124, brazo B): el efecto de la grilla
correlaciona con la desalineación medida contra el cráter — PCC −0,104 ·
Láscar +0,110 · Isluga +0,110 · r = −0,47 (n=8, p≈0,24). Sugestivo, sin poder.

**Test (brazo D)**: regrid centrado en `get_grid_center()` en vez de
`volcano["lat"/"lon"]`. Es un cambio de una línea en el llamador, y usa una
función que ya existe y está testeada.

**Test propuesto (brazo D)**: grilla ON + kernel global + centro de grilla
tomado del GeoTIFF de MIROVA, en los 6 volcanes con offset >500 m. Reusa toda
la infraestructura de F70.2; solo cambia el centro. Pendiente de confirmación.

**Caveat honesto**: el GeoTIFF es una reproyección lat/lon de su grilla UTM, así
que el centro que leemos aproxima el real a menos de media celda. Suficiente
para un A/B, no para afirmar el origen exacto.

---

## D18 — El ROI1 del paper es una CAJA de 5 km igual para todos; el nuestro es un CÍRCULO de 3 a 20 km por volcán — **ABIERTA (medida, sin A/B)** S129

**La cita**, Coppola 2016a SP426.5, verbatim:

> *«the inner region (ROI1) consists of a **box (5 × 5 km)** centred on the volcano's
> summit»*

Caja de 25 km², **uniforme**. El criterio del paper para tener dos regiones es que
tengan *«variable size and different chance of finding a thermal anomaly»*: el ROI1 es
chico a propósito.

**Lo nuestro**: círculo de radio `inner_radius_km`, per-volcán — 3 km (Lastarria, PP),
4 (Copahue), 5 (seis), 7 (Tupungatito), **20 (PCC)**.

**La medición** (`experiments/_s129_roi1/01_caja_vs_circulo.py`): de los **107.265**
píxeles que hoy reciben el umbral laxo de *summit*, sólo **33.354** caerían dentro del
ROI1 del paper. **El 68,9 % lo recibe por una geometría que el canon no respalda.**
PCC es el extremo: su ROI1 es **50,3×** el área del paper y perdería el 91 %. Ni el
radio «estándar» de 5 km se acerca — es 3,1×.

**Por qué importa**: el ROI1 decide qué umbrales rigen (N·σ 5 / C1 0,003 adentro contra
10 / 0,010 afuera). Agrandarlo afloja el umbral sobre más terreno. Y es **per-volcán**,
que MISSION excluye.

**Lo que NO dice**: esos píxeles no desaparecerían, pasarían a los umbrales de *scene*
—más estrictos— y algunos dejarían de pasar. **La dirección es menos detecciones**, lo
que choca con la prioridad declarada de `mirova_equivalent` (recall sobre precisión).
Es una decisión de misión, no técnica.

**Relación con A82**: A82 concluyó «irreducible» y S124 la rebajó porque la auditoría
S114 nunca miró la geometría del ROI. Esto **mide** la divergencia pero **no prueba**
que corregirla cure el far→summit. Es hipótesis falsable, no conclusión.

**Estado**: ~~registrada, sin A/B~~ → **MECANISMO IMPLEMENTADO Y A/B CORRIENDO — S130.**
El brazo fiel es una **caja** de 5 × 5 km uniforme, no un círculo de radio equivalente:
el paper dice caja y la forma importa en las esquinas (la esquina está a 3,54 km y un
círculo de igual área tiene radio 2,82, así que hay píxeles que sólo la caja incluye).

- **Implementación (PR #577)**: `roi1_summit_mask()` centraliza en un solo lugar la
  decisión «quién recibe trato de summit», que estaba escrita a mano en tres puntos de
  `detection_context.py`. Flag `enable_roi1_box_paper`, **default OFF y OFF en el
  operacional** — la dirección es menos detecciones y `mirova_equivalent` prioriza
  recall, así que adoptarlo es decisión de misión. Reusa `roi_mask_bbox`
  (`scan_geometry.py:150`), que S15 escribió para el mismo cambio en el ROI **exterior**:
  hay precedente. 7 tests, dos de ellos de **control de instrumento** (que la caja
  cambie el resultado de `dual_roi_bt_threshold`, y que el cableado exista en los tres
  sensores) — la lección del A/B de los fondos, hecha código.
- **Cuánto está en juego, en DETECCIONES** (no sólo píxeles): el **42 %** de las summit
  tienen su clúster fuera de la caja (11.116 de 26.446), concentradas en los nevados de
  señal débil — **Llaima 71,6 % · Copahue 69,5 % · Villarrica 66,4 %**, justo donde vive
  el sesgo topográfico A69. Pero también donde vive cat-b real: **Lastarria/Lazufre
  22,9 % · PCC/lacolito 40,6 %**. Láscar, con foco compacto real, sólo 11,3 %.
- **⚠️ D18 NO CURA EL far→summit — medido, no supuesto.** El píxel que roba la etiqueta
  en los 9.203 far→summit está a una **mediana de 22 km** del cráter (p10 = 11,8 km); NI
  UNO cae dentro del ROI1 actual ni de la caja. Ya reciben el umbral estricto de *scene*
  y lo seguirían recibiendo. **D18 es ortogonal a esa brecha** — refuta la hipótesis de
  que fuera la llave que A82 dejó abierta al no auditar la geometría.
- **✅ A/B CORRIDO Y LEÍDO — NO ADOPTAR** (run `33456630043`, 12/12 verdes; detalle en
  `docs/s130/VEREDICTO_AB_D18.md`). No por daño —no lo hay— sino por **ausencia de
  beneficio**.
  - **El control de instrumento pasa**: 366 de 5.551 records comunes (**6,59 %**)
    cambian de `pc.vrp_mw`; PCC llega al 17,98 %. Pero de esos 366 la caja da **más** en
    166 y **menos** en 200: **redistribuye, no recorta**.
  - **Ningún límite de no-adopción se cruza**: Lastarria pierde **0,0 %** (límite 20) y
    PCC **0,8 %** (límite 50). **Cero noches MIROVA-confirmadas perdidas** en los seis.
    La caja **no destruye cat-b**: el Lazufre y el lacolito sobreviven enteros.
  - **Pero el criterio de adopción tampoco se cumple**: pedía que el offset bajara en
    los tres nevados y Villarrica **sube** 1 m sobre 2,63 km; los otros dos bajan 9 y 14
    metros sobre 2,7 km — ruido. Lo único que se mueve es la paridad: **+0,040 en PCC**
    y **+0,020 en Copahue**, nulo en los otros cuatro.
  - **⚠️ La predicción previa erró por 50×.** Se había medido que el 42 % de las
    detecciones summit tienen su clúster fuera de la caja y se presentó como «lo que
    está en juego»; lo que se pierde de verdad es 0-0,8 %. El error fue de **qué se
    contaba**: dónde cae el clúster, no si la detección **sobrevive** al umbral más
    estricto. Casi todas sobreviven.
  - **El hallazgo real, más útil que el veredicto**: **el umbral laxo del ROI1 casi
    nunca es lo que decide.** Las detecciones de estos volcanes pasan con margen
    suficiente como para no depender de si el píxel recibe N·σ = 5 o N·σ = 10. La
    diferenciación summit/scene es fiel al paper en sus valores y **casi inerte** en la
    práctica — por eso Llaima, Villarrica y Láscar, con círculos de 3,1× el área del
    paper, no cambian **nada**.
  - **Estado**: D18 sigue abierta como divergencia de fidelidad literal; lo que cambia
    es su **prioridad**, porque su consecuencia empírica está medida y es marginal —
    igual que el GAP #A. El flag queda en el código, **OFF**, con sus 7 tests.

Detalle: `docs/s129/ROI1_CAJA_VS_CIRCULO.md`.
