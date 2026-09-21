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

> **Actualización S128/S131.** La cobertura medida es **79,2 %**, no ~70 %
> (`docs/AUDIT_S128.md` §4), y el loader canónico CONS ∪ OCR (S86, `experiments/_s126_lib.py::cargar_mirova`)
> ya la mitiga de facto: las métricas del proyecto se calculan sobre esa unión. El
> «re-scrapear» pendiente de abajo quedó superado por `sync-mirova-csv.yml` (cron 1 h).
> Esta sección se conserva como quedó escrita el 2026-04-29.

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

> **S131**: los conteos de abajo (13.378 RUTINA, 407 Muy Bajo, 165 Bajo, 253 FP) son del
> 2026-04-29 y **no tienen instrumento que los recompute** (no hay entrada en
> `scripts/libro_de_cuentas.py`). Son conteos absolutos sobre un corpus vivo (A90): se
> conservan como fotografía de esa fecha; **no usar como línea base** sin volver a medir.

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
| Coppola 2016a §SP 426.5 | NO | Define dNTI ctx + umbrales C1/C2 + filtro `dNTI<−0.1`. Sin cloud mask previo, sin gate t_bg. Caso Gaua p.17: "<2% FPs, siempre <5 MW" — interpretativo post-hoc, no gate algorítmico. ⚠️ **S146: «Gaua» NO está en SP426.5; ver la nota bajo esta tabla (AUDIT_S146 V-07 y C-03).** |
| Coppola 2016b enhanced | NO | Sin discusión cirrus / fondo frío. |
| Campus 2024 thermal | NO | MIR captura solo 1-2% flujo hidrotermal real; no toca FPs dNTI sobre fondo frío. |
| Coppola 2024 cap Springer | NO | "MIROVA uses spectral + contextual" sin detalle de adaptación a escenas anómalas. Tabla 3 lista 19 sistemas NRT sin paso cloud mask explícito. |
| Aveni 2024 RSE TIRVolcH | NO | Problema TIR baja-T, no MIR cirrus. VSROI + R²>0.5 son filtros distintos. |

**Verdict**: papers MIROVA **NO resuelven D9 explícitamente**. Ningún cloud mask documentado, ningún gate t_bg, ninguna co-validación obligatoria. La única pista publicada es interpretativa (Coppola 2016a Gaua: <5 MW Tier A sospechoso).

> ⚠️ **La atribución «Gaua» cae, S146** (`docs/AUDIT_S146.md` §3 V-07 y frente C, C-03). La palabra
> «Gaua» tiene **cero apariciones** en las 25 páginas de `documentacion/sp426.5.pdf` y en
> `sp426_5.txt`, y «<2 %» tampoco está: ese dato viene de otro paper del grupo, Coppola et al.
> 2016, JVGR 322 (Vanuatu), p. 10, §4.6. Lo que **sí** está en SP426.5 p. 17 es la frase *«these
> false detections typically radiate less than 5 MW and can be easily identified by a visual
> inspection of the associated NTI map»*, pero referida a falsas alertas **diurnas**, en bordes de
> cuerpos de agua y nubes dispersas (p. 16), sin volcán nombrado. La tabla de arriba la escribió un
> subagente que leyó notas del Vault y no el PDF (lo dice el «Trigger» de la sub-sección S71 de
> más abajo). El texto original se conserva
> como historia. Nota: la misma cita errada vive en `pipeline/profiles/mirova_equivalent.yaml:482`
> y otros 23 perfiles (24 de 73 con `grep -l Gaua`); corregirla es de la Fase 2 del plan, porque
> toca archivos con A45.

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

**Cobertura física**: el cap acota magnitudes en cirrus alto (Wooster BT⁸ sobre fondo frío inflaba 20-150×). Ahora la magnitud máxima publicable en escena contextual-only + cirrus es 5 MW, alineado con Coppola 2016a Gaua "<5 MW Tier A sospechosos" y con el máximo MIROVA empírico en records que el cap atrapa (0.21 MW). ⚠️ **S146: la atribución «Gaua» es falsa (V-07, C-03; ver la nota tras la tabla de la Fase 1). El tope sigue siendo una mitigación propia, medida y adoptada acá; lo que cae es el respaldo de paper, no el tope.**

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

> ⚠️ **El «NO es un parche» cae, S146** (`docs/AUDIT_S146.md` §3 y frente C, **C-02**, página 17
> renderizada a imagen). La frase citada existe, pero leída completa (p. 16 y 17) dice otra cosa:
> las falsas alertas ocurren **principalmente de día**, en bordes de cuerpos de agua y nubes
> dispersas, irradian típicamente menos de 5 MW y el remedio que el paper propone es la
> **inspección visual**. El paper describe cuánto miden las falsas; **no propone recortar nada a
> 5 MW**. Y el caso que el tope ataca (registros nocturnos inflados 20 a 150 veces sobre cirrus)
> es el fenómeno opuesto al de la cita. El tope puede ser una buena mitigación, y su adopción
> tiene A/B propio acá arriba, pero es **propia**: no es la implementación programática de nada
> que el paper diga. El punto 5 de la lista de abajo («reemplaza programáticamente el QC visual
> que MIROVA hace manualmente») además choca con A105: el canal NRT de MIROVA no está supervisado
> a mano. Texto original conservado por historia.

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
| **F1.2** | NEW-7 + NEW-8 — Test 1 K1 retire + edge/dNTI<-0.1/dETI<-0.1 unsuitable | ⚠️ **PARCIALMENTE RECLASIFICADO S100**: el gap (1) NEW-7 (`enable_test1_k1_retire_from_hot_mask`) era una **LECTURA EQUIVOCADA** — ver nota S100 abajo: "discarded (unsuitable) for further steps" (SP 426.5 §298-300) = sacar los Test 1 del **pool estadístico** (los `suitable pixels` de §326-329 que alimentan m,σ de Tests 2/3), NO del **reporte de detecciones**. Nuestro código (flag OFF, los Test 1 entran al hot_mask reportable) **ya es fiel**. **Mantener OFF permanentemente.** ⚠️ **Esa última frase quedó rebajada S146 (AUDIT_S146 A-08 y C-08, frente E E-07)**: el flag gobierna el **pool de μ y σ**, y ahí el paper sí retira los píxeles del Test 1 mientras nuestro código no. Eso es el **GAP #A**, reabierto en S128, con guard `tests/test_guard_gap_a_pool_musigma_s128.py`. El «mantener OFF permanentemente» no es una decisión cerrada. Los gaps (2)(3)(4) NEW-8 (edge/dNTI<-0.1/dETI<-0.1) **siguen vigentes** — esos sí son sobre el pool estadístico de m,σ (§267-273), naturaleza distinta del malentendido ⚠️ **FALSO desde S72, verificado S146 (AUDIT_S146 V-05): los gaps (2)(3)(4) CORREN EN PRODUCCIÓN. Lo único abierto de este párrafo es el GAP #A. Ver la nota S146 bajo la tabla.** | NEW-7 cerrado; NEW-8 (gaps 2-4) sin cambio |
| **F1.3** | HT1.5-NEW-2 — L_bk kernel excluye TODOS hot pixels del cluster | ✅ **PASS** — `pipeline/vrp_regimes.py:compute_local_background` (líneas 21-89) excluye correctamente `hot_set = set(zip(hot_rows, hot_cols))`. Test sintético `test_two_adjacent_hot_pixels_each_excludes_the_other_hot` confirma | Descartado como causa drift |
| **F1.4** | NEW-5 — geofencing 5 km Stromboli aplica en Andes | ❌ **REFUTADO**. 21.79% records OSF v2.5 chilenos > 5 km del vent; cap empírico ~30 km coincide con `r_circunscrito` box MIROVA 51×51 km. La regla S14 (`radius_km=25 km` uniforme) cubre 98.27% records — empíricamente óptima. Stromboli 5 km es contexto isla pequeña, NO transferible | NO cambiar geofencing actual |
| **F1.5** | NEW-6 — reproducir Villarrica 24-Jun-2009 Fig. A6 SP 426.5 | ⏸️ **GAP OPERATIVO**: granule MODIS Terra/Aqua 2009-06-24 04:10/05:55 UTC disponible vía Earthdata pero pyhdf roto en Windows + falta instrumentación dump rasters NTI/NTIbk/dNTI/ETI. Costo: ~2h instrumentación + workflow GH Actions | Aplazado — no urgente |

##### Nota S146 (2026-09-20): NEW-8 (gaps 2 a 4) NO es un gap abierto, corre en producción desde S72

> ⚠️ **Verificado en S146** (`docs/AUDIT_S146.md` §2 y verificador **V-05**, por dos caminos: el
> flag leído de `pipeline.profile` y el trazado del consumo en los tres procesadores).
> `ENABLE_UNSUITABLE_FILTERS_267_273` vale **True** (default de `profile.py:676`, puesto en el
> commit `d58f7a46f`, S72 F2.3.a; la clave no está escrita en `mirova_equivalent.yaml`, así que
> manda el default, A89). Los **tres** procesadores lo consumen en las **dos** ramas, y las dos
> ramas están encendidas (`ENABLE_DNTI_CONTEXTUAL_PATH`, `ENABLE_FIRST_PASS_TESTS_2_AND_3`):
> `process_modis.py:696/704` y `:866-867`, `process_viirs.py:1071/1079` y `:1272-1273`,
> `process_viirs_mod.py:705/713` y `:854-855`. El filtro de borde va siempre activo dentro de
> `build_unsuitable_mask`.
>
> Consecuencia: el A/B **F2.1** que este bloque propone más abajo **no se puede correr como está**,
> porque su control ya tiene el filtro puesto (gravedad 2: el cierre no apaga trabajo, lo inventa).
> Lo único que sigue abierto del párrafo §267-273 es el **cuarto** elemento, retirar del pool de μ
> y σ los píxeles del Test 1, que es el **GAP #A**, reabierto en S128 (en este mismo archivo,
> bloque CIERRE S114 de D11, buscar «REABIERTO S128») y con guard propio (`tests/test_guard_gap_a_pool_musigma_s128.py`). Todo el texto de
> abajo se conserva como historia.

##### Nota S100 (2026-06-03) — NEW-7 / Drift #1 reclasificado: lectura equivocada

> ⚠️ **Rebajada en su CONCLUSIÓN, S146** (`docs/AUDIT_S146.md` §2, frente A **A-08** y frente C
> **C-08**). La lectura del paper que hace esta nota es buena y la página la respalda. Lo que **no**
> se sostiene es la frase con que termina, «queda OFF permanentemente; el código actual ya es
> fiel»: el flag gobierna el **pool de μ y σ**, y el paper sí retira de ese pool los píxeles del
> Test 1 mientras nuestro código no (`test1_mask=None`). Eso es el **GAP #A**, reabierto en S128 y
> registrado en este mismo archivo (bloque CIERRE S114 de D11, buscar «REABIERTO S128»), con guard
> `tests/test_guard_gap_a_pool_musigma_s128.py`. Tres frentes de S146 llegaron por separado a esta
> línea porque es la que se lee primero y no llevaba ninguna marca. Texto original intacto abajo,
> conservado por historia.

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

> ⚠️ **Nota S146, dos rebajas sobre el bloque que sigue** (`docs/AUDIT_S146.md`). (1) **V-05**: los
> gaps 2 a 4 de NEW-8 **no están pendientes**, corren en producción desde S72 en los tres
> procesadores (ver la nota S146 arriba, tras la tabla de la Fase 1); lo que queda abierto de
> §267-273 es sólo el GAP #A. (2) **E-01 / A-11**: el «killer A82» con que el veredicto de más
> abajo declara el A/B no accionable **hereda una premisa rebajada**. A82 quedó rebajada dos
> veces, por la vía geométrica en S124 (la auditoría S114 nunca miró la geometría del ROI) y por
> la vía espectral en S138 (los records se produjeron con la banda 21 primaria y la compuerta de
> 3 K, D21 y D22, abiertas en este mismo catálogo); la rebaja se anotó en A82 y **nunca bajó a las
> hijas**. El «irreducible» vale sólo bajo esa configuración. Texto original abajo, conservado por
> historia.
>
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

> ⚠️ **D9 vuelve a estar ABIERTA en su cara de co-validación sobre fondo frío, S146**
> (`docs/AUDIT_S146.md` §3, verificador **V-01**, gravedad 4, con medición sobre el corpus y la
> referencia tal como estaban el 2026-06-19, commit `1d6b5b932`). Lo que cae de este bloque:
>
> - **Los denominadores SÍ se reproducen, exactos**: 199 `far` y 214 `summit`, con 0 `far` sobre
>   5 MW. Eso queda verificado limpio.
> - **El numerador no.** Con cualquier definición en que «confirmado» signifique que MIROVA
>   publicó una **alerta** (misma fecha, con o sin mismo sensor, con o sin OCR, con tolerancia de
>   5 a 60 min) el máximo es **80 de 214 (37,4 %)**, y 100 de 214 (46,7 %) si además se cuentan los
>   `FALSO_POSITIVO` del scraper. El rango 201 a 211 sólo aparece cuando «confirmado» cuenta
>   **cualquier fila de la referencia, incluidas las RUTINA**, o sea cuando significa «MIROVA miró
>   esa pasada», no «MIROVA vio algo». La definición exacta que da 207 quedó NO VERIFICABLE.
> - **El «0 fuga» es circular**: una fuga sería un record `far` visible, y el predicado del
>   dashboard esconde todo `far` por construcción. La parte no circular (0 records sobre 5 MW, tope
>   activo) **sí** se confirma.
> - **La lectura física tampoco se sostiene**: la población no es «fondo frío por altitud del
>   norte». El volcán con más records es **Puyehue Cordón Caulle (59 de 214, 2.236 m)** y tres de
>   cada cuatro son **VIIRS 750** (sensor medido sobre la población de hoy, 162 de 216; el 59 de
>   214 es la población de junio).
>
> Consecuencia: el argumento con que se descartó **para siempre** la co-validación del path D en
> fondo frío («mataría 207 detecciones reales») **no tiene respaldo**; entre 63 y 88 % de esa
> población no tiene alerta de MIROVA. Esa cara pasa a **REABIERTA** y va a la Fase 3 del plan
> `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`. Lo que **no** se reabre es el gate por `t_bg` (sigue
> descartado: es anti-MIROVA, Coppola 2016a §247 y 2023 §554) ni el tope de 5 MW, que funciona.
> Texto original intacto abajo, conservado por historia.

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
  - ⚠️ **El 207 de 214 NO se reproduce, S146 (AUDIT_S146 V-01)**: con «confirmado» = MIROVA
    publicó una alerta, el máximo es 80 de 214 (37,4 %); el rango 201 a 211 sale sólo contando
    filas RUTINA, que son «MIROVA miró», no «MIROVA vio». Y la población está dominada por
    Puyehue Cordón Caulle (2.236 m) y por VIIRS 750, no por los volcanes de altitud del norte.
    Ver la nota S146 al inicio de esta sección.
- **La amplificación de MAGNITUD (la otra cara de D9) — CURADA por las adopciones nadir/focal
  S102-S109** (verificado S113, ratio nuestro/MIROVA con pc.vrp_mw, A10, sobre 610 TP path-D-dominante
  visibles mayo-jun): **mediana 0.53×** (p25-p75 0.30-0.85), levemente sub-reportando = calibración
  clon-literal sana. S71 dejó "6-12× sistemático en cirrus"; hoy quedan **solo 2 records >5×** de 610,
  ambos VIIRS750 en cirrus (Tupungatito 05-24 4.41 vs MIROVA 0.19; PP 05-09 2.99 vs 0.18) — magnitud
  absoluta chica (3-4 MW, bajo el cap), = el "~30% residual VIIRS750 cirrus/glaciar" que la adopción
  focal V750 S112 ya documentó. NO es frente, es cola documentada.

**Estado D9 (actualizado S146): REABIERTA en la cara de co-validación sobre fondo frío**. El
«no quedan acciones abiertas» de abajo se apoyaba en el 207 de 214 y en el «0 fuga», y los dos
caen (AUDIT_S146 V-01: el numerador no se reproduce con ninguna definición basada en alertas, y
el «0 fuga» es circular porque el dashboard esconde todo `far`). Sigue en pie el tope de 5 MW
(medido, A/B propio) y sigue descartado el gate por `t_bg`. La acción abierta es la **Opción 2
(co-validación)**, con su sustrato re-medido en el régimen actual: Fase 3 de
`docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`. Adelanto de la Fase 1
(`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` §7 a §9, verificado en
`docs/audit_s146/FASE1_VERIFICADOR.md`): en el régimen actual el `dnti_ctx` legacy es sólo
diagnóstico y no entra a la máscara, el tope de 5 MW actúa sólo en MODIS, y el sustrato de un
brazo de co-validación es bajo en VIIRS 375 y MODIS y medio en VIIRS 750. Reabierta no quiere
decir prioritaria. Estado anterior, conservado por historia:

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
Coppola 2015 Eq.1 textual: VRP = ΔL_ROI · A_ROI · k (⚠️ **cita FALSA, S146, AUDIT_S146 V-06:
no existe ese «Coppola 2015»; en `sp426.5.pdf` la Ec. 1 es el NTI. Ver D30 y el encabezado
H_S27_1 de más abajo**). Posible: reportar
**VRP integrated** del trigger Test 1 en lugar de descomponer per-pixel
y sumar (que es lo que hacemos hoy y pierde señal sub-pixel distribuida).

## H_S27_1 — Test 1 integrated-ROI activado en `_mirova_literal` (S27 cierre D4)

> ⚠️ **S146 (AUDIT_S146 §3 V-06, gravedad 5): la cita «Coppola 2015 §2.2 Eq.1» es FALSA, y
> aparece muchas veces en todo este bloque.** El artículo 55 del volumen 77 de *Bulletin of
> Volcanology* es de Heap et al., mecánica de rocas en andesita; en `sp426.5.pdf` p. 6 el Test 1
> es por píxel contra K1, sin suma sobre el ROI. El Test 1 integrado en el ROI es un **detector
> propio**. **Esta marca cubre todas las apariciones de esa cita en la sección**, y no se repite
> línea por línea (A113 b). Ver el detalle en la pregunta 1 de más abajo y en **D30**, al final
> de este archivo. Nada de lo medido en el bloque cambia: lo que cae es el respaldo
> bibliográfico, no el resultado empírico de S27. Texto original intacto, conservado por
> historia.

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
   - ⚠️ **FALSO, verificado S146 (AUDIT_S146 §3 V-06, gravedad 5; ver D30 al final de este
     archivo).** El artículo 55 del volumen 77 de *Bulletin of Volcanology* es de **Heap et al.**,
     mecánica de rocas en andesita (DOI 10.1007/s00445-015-0938-7); Crossref y OpenAlex no
     registran ningún artículo de Coppola en esa revista en 2015 (con control de consulta: la
     misma búsqueda sin autor devuelve 12 artículos de ese número). El proyecto ya había
     establecido (por hash antes de S128, y por contenido en S128) que el «Coppola 2015» del
     proyecto **es** `sp426.5.pdf`, y ahí la Ec. 1 es el NTI (p. 4)
     y el Test 1 es `NTI_PIX > K1`, **por píxel** (p. 6): no hay §2.2, ni suma sobre el ROI, ni
     k = 3, ni piso relativo de 0,02. El Test 1 integrado en el ROI es un **detector propio** y por
     lo tanto **no pasa** la pregunta 1 de MISSION por esta vía. Nada de lo medido abajo cambia:
     lo que cae es el respaldo bibliográfico, no el resultado empírico de S27.
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

⚠️ **ESTA TABLA NO TIENE INSTRUMENTO, verificado S147** (`docs/audit_s147/VERIFICADOR_H_A01.md`,
hallazgos H1 y H1-bis, verificador con contexto limpio). El commit que la escribió
(`a7b567f00`, 2026-04-30) cambió **un solo archivo, y es este catálogo**: 46 líneas insertadas,
ningún script, ningún JSON de resultados, ninguna salida. En el árbol completo de ese commit no
existe ningún script de recall sobre 11 volcanes ni sobre 507 registros. Y no es sólo la búsqueda
del verificador: el propio **libro de cuentas** del proyecto ya la tenía fichada en su lista
`sin_instrumento` desde el 2026-08-30 (`docs/LIBRO_DE_CUENTAS.json`, entrada con el contexto
`"TOTAL ~50% 80% (406/507) +30 pp"`), o sea **21 días antes de que S146 la discutiera**, y nadie
conectó esa ficha con la adopción que este número justifica.

Tres cosas más que caen con ella:
- **La medición era circular** (H2): con el Test 1 encendido, su disparo fija por construcción
  `final_hotspot_source = "test1"`, `distance_class = "summit"` y el recómputo de VRP, que son
  las dos condiciones del predicado de acierto de la época. El brazo tratado escribía la hoja de
  respuestas. El commit de S26 ya lo decía en voz alta: el Test 1 **ya disparaba** antes (15 de
  19 gránulos) y el recall era 0 de 6 **sólo porque la etiqueta salía `far`**.
- **El único A/B limpio dio 6 contra 6** (H3, S25, `experiments/54_test1_ab/REFS_FORENSE.md`):
  ganancia cero. Los "+30 puntos" aparecen recién **después** de agregar la regla que fuerza la
  etiqueta summit.
- **No había un solo negativo limpio** (H6): el universo era `Tipo_Registro == "ALERTA_TERMICA"`
  y nada más, habiendo **11.680 filas RUTINA** en el mismo archivo y la misma ventana, en
  proporción 22,6 a 1. Una tasa sin tasa base no dice nada sobre discriminación.

Y la fila de Nevados de Chillán delata que los dos brazos **no vieron las mismas pasadas** (H9):
el denominador es el conteo de alertas de MIROVA y pasa de 3 a 4 entre brazos, cuando es la misma
referencia externa y no puede cambiar. La tabla se conserva por historia; **no se usa como
evidencia de nada**.

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
| ~~#1~~ | ~~Test 1 K1 → `hot_mask` reportable~~ — ❌ **NO ES DRIFT (S100)**: lectura equivocada de sp426_5.txt:298-300. "discarded (unsuitable) for further steps" = sacar del **pool estadístico** (m,σ de Tests 2/3, §326-329 "all the suitable pixels"), NO del **reporte**. Los Test 1 SÍ se reportan (son las detecciones fuertes). Código actual (flag OFF) ya fiel. Ver nota S100 arriba ⚠️ **El «ya fiel» cae S146 (AUDIT_S146 A-08, C-08, E-07)**: el flag gobierna el pool de μ y σ, donde el paper sí retira los píxeles del Test 1 y nuestro código no. Es el **GAP #A**, reabierto S128, con guard `tests/test_guard_gap_a_pool_musigma_s128.py`. Texto original conservado por historia | `process_*.py` nti_path_hot | sp426_5.txt:298-300 + 326-329 |
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

### D8 Background ring contaminado — RESUELTO ⚠️ **matizado S146: leer D25 antes de tomarlo por cerrado**

> ⚠️ **S146 (`docs/AUDIT_S146.md` §2, frente A **A-07**).** «RESUELTO» vale para el parche
> adoptado (el kernel local de vecinos), **no** para la divergencia de fondo contra el paper.
> **D25**, en este mismo archivo, dice textual que *«D8 quedó marcada resuelta por el kernel
> opt-in, pero la divergencia literal sigue vigente en 6 de 11 Tier A en MODIS, 11 de 11 en
> M-band y todo el camino Test 1»*. El kernel rige hoy en **5 de los 11** Tier A
> (`volcanoes.yaml`), o sea es opt-in por volcán, no un cambio global. Quien lea sólo este
> encabezado se lleva lo contrario de lo que el catálogo sabe. Además la tabla de regímenes de
> más abajo usa el ejemplo que A12 declara **FALSO** (Isluga 8,3 K y Láscar 16,9 K medidos en
> S128, no «más de 20 K»). Texto original intacto abajo, conservado por historia.

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

### D-PCC: inner_radius_km demasiado permisivo — RESUELTO S62 ⚠️ **NO: la adopción se revirtió a las nueve horas, en la misma S62 (PR #85, 2026-05-19); verificado S146**

**Hipótesis previa**: PCC gap 52× porque cluster lejano (Salar/Antillanca)
ganaba selección summit con inner=20 km.

**Validado**: PCC ratio mediano 3.51× con inner=20. Preview offline
inner=7 → 1.86× (-47%). Adoptado en `volcanoes.yaml` S62. Reproc
operacional corriendo.

> ⚠️ **El «adoptado» es falso desde la misma S62, verificado S146** (`docs/AUDIT_S146.md` §2 y
> frente A **A-06**; `volcanoes.yaml` tiene hoy `inner_radius_km: 20` para
> PuyehueCordonCaulle, con el comentario «MIROVA KML oficial»). El `git log -S"inner_radius_km: 7"`
> muestra las dos caras: `fab02ec1c` («PCC inner_radius 20->7», PR #79) y, a la mañana siguiente,
> `5d2bea4b9` («S62 CIERRE: ... revertir PCC inner_radius», **PR #85**), porque el reproceso real
> empeoró el ratio (es el caso de manual de A18: el preview offline no predice la selección de
> cúmulo). El catálogo nunca anotó la reversión. Importa hoy: D18 señala que un radio interior de
> 20 km aplica umbrales de cumbre donde MIROVA usa los de escena, y eso toca la sobre-publicación,
> así que quien lea «resuelto» acá no va a ir a mirar. Texto original conservado por historia.

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

**Fenómeno**: el Test 1 integrado-ROI (Coppola 2015 §2.2 Eq.1 ⚠️ **cita FALSA, S146, AUDIT_S146 V-06: el Test 1 integrado en el ROI es un detector propio; ver D30 y la marca del encabezado H_S27_1**) suma TODOS los píxeles del ROI sobre la mediana del fondo. Sobre el glaciar nevado de Tupungatito (5.682 m), en invierno, eso es el mosaico nieve/roca entero (anillo difuso 1-3 km) con un fondo regional sesgado frío → la magnitud se infla **8-19×** vs MIROVA, que reporta el foco compacto (~0.2 MW estable). Empezó abril 2026 (marzo daba 1.04× perfecto): mosaico nieve/roca invernal sobre el glaciar.

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

## D11 — Sesgo topográfico de los paths MIR-absolutos (A69) — **CERRADA S114, CONDICIONADA S138** (el «irreducible a 1 km» y el «todos los ejes agotados» valen sólo bajo banda 21 primaria y compuerta de 3 K, D21 y D22, abiertas en este mismo catálogo; la «detección fiel a Coppola» es falsa en el código de hoy: la fórmula de los Tests 2 y 3 del paper no tiene condición de temperatura y `detection_context.py:532` la impone. Ver `docs/AUDIT_S138.md` §8 C2. No se reabre el frente far→summit por la vía espectral hasta consolidar D21/D22)

> ⚠️ **S146 (AUDIT_S146 V-02 y V-08).** El «90 % pipeline-cráter» del cierre S114 de abajo no
> tiene tasa base: con negativos limpios hay cúmulo con magnitud dentro del inner en 89,1 % de
> 4.800 pasadas MODIS, contra 93,7 % de 158 cuando MIROVA alertó (ventana 2026-01-29 a
> 2026-08-28; después de #535, 86,0 % de 500 negativos y sólo 2 positivos; 144 de las 158
> positivas son de Láscar). Mide presencia de cúmulo, no detección. Y el «dual-ROI 5/10» que el
> mismo bloque cita como fidelidad no está en la Tabla 1 (ver D31). Texto original intacto
> abajo, conservado por historia.

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

> ⚠️ **Nota S146, dos rebajas sobre la nota S125 que sigue** (`docs/AUDIT_S146.md`).
> (1) **V-09**: las «76 noches de FN recuperadas (reales)» de `AUDIT_S121_D12_AB.md` **no son
> FN**. El script de S121 no carga ninguna referencia: «curada» ahí significa «cúmulo dentro del
> inner», sin cruzar con nada, así que llamarlas FN usa una palabra que exige una alerta de
> MIROVA que nadie miró. El CSV del scraper tiene **0 filas** de Láscar en esa ventana
> (2025-02-15 a 05-15). El fenómeno **sí** queda corroborado por una referencia independiente
> para cerca de la mitad: el OSF v2.5 (producto filtrado, A105) trae 79 detecciones MODIS
> nocturnas en **55 noches** de Láscar ahí, y 39 de 73 noches candidatas tienen detección OSF.
> El **76 exacto es NO VERIFICABLE** (los artefactos del run vivían en un scratchpad que ya no
> existe). El «NO ADOPTAR» del A/B no cambia: lo que cambia es qué se creía haber recuperado.
> (2) **A-11 / E-01**: el «reabrir trabajo cerrado» se apoya en el veredicto de S122, que dice
> «irreducible a 1 km» y hereda la misma premisa que A82, rebajada por la vía geométrica en S124
> y por la espectral en S138 (banda 21 primaria y compuerta de 3 K, D21 y D22, abiertas en este
> catálogo). Texto original de la nota S125, conservado por historia:
>
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
`mirovaEqVrp` del frontend desde S33). ~~Siguen ON en `mirova_equivalent.yaml`~~ → **OFF desde S118** (flip PR #474, verificado S119 y S131; ver bloque «RESUELTO S118» más abajo).
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

## D13 — La cerca `distance_class != summit` del frontend apaga el 31 % de la magnitud — **ABIERTA (documental)** S124 ⚠️ **El título mezcla unidades, S146 (AUDIT_S146, frente A A-12 y frente E): ese 31 % es fracción de RECORDS (10.770 de 34.739); en MAGNITUD la cerca apaga el 70,7 % (medido S145, control reproducido en `docs/audit_s146/FRENTE_D_CIERRES_CON_NUMERO.md`). Título original conservado por historia**

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
que a 1 km es irreducible (A82). ⚠️ **S146 (AUDIT_S146 §2, A-11 / E-01): ese
«irreducible» hereda una premisa rebajada. A82 quedó rebajada por la vía
geométrica en S124 (la auditoría S114 nunca miró la geometría del ROI) y por la
espectral en S138 (los records se produjeron con la banda 21 primaria y la
compuerta de 3 K, D21 y D22, abiertas en este catálogo); la rebaja se anotó en
A82 y nunca bajó acá.** Levantar la cerca destaparía ambas cosas
mezcladas. Lo que se corrige acá es que **esta divergencia no estaba escrita en
ningún lado**: una decisión de display que mueve el 31 % de la magnitud publicada
(⚠️ **S146: ese 31 % son RECORDS; en magnitud son 70,7 %, medido S145**)
merece estar en el catálogo, no vivir implícita en un helper de JavaScript.

**Anti-A8**: no reabrir como "hay que levantar la cerca" sin antes clasificar por
categoría A54 los records que se destaparían. Y ojo con A72: si lo que se destapa
es artefacto, la raíz es no generarlo en la detección, no la cerca.

### Clasificación cumplida — S126

> ⚠️ **El «1,5 % corroborado» cae como argumento, S146; la conclusión se sostiene por otra vía**
> (`docs/AUDIT_S146.md` §3, verificador **V-10**, medición propia con loader independiente).
> Lo que se reproduce: **41 de 2.704 (1,5 %)** hoy (S126 tenía 41 de 2.694; el corpus creció, el
> porcentaje es el mismo), y el 95,2 % de lo apagado es MODIS. Lo que
> el número **no** mide: la calidad de lo que la cerca esconde. En cuatro meses MIROVA tiene **18
> alertas MODIS nocturnas**, así que casi ningún record MODIS puede corroborarse por mismo sensor;
> de hecho el MODIS que **sí** se publica se corrobora **0,6 %**, todavía menos que el apagado
> (1,0 %). La causa es de la referencia, no nuestra, y el 1,5 % mide la rareza de las alertas
> MODIS de MIROVA. Por eso **«corroboraría casi nada» no vale como evidencia de artefacto**.
> Lo que sí sostiene el veredicto, y nadie había escrito, está en la unidad del operador (A94):
> de las 1.266 noches con algo apagado, sólo **92** no tienen ya algo publicado esa misma noche,
> y de esas 92 **sólo 1** coincide con una alerta de MIROVA. Levantar la cerca agregaría **una
> noche** con respaldo. (El «33 % contra 43 %» que circuló en los informes de S146 es por record;
> por noche real la diferencia es **36,1 % contra 38,8 %**.) Límite de la medición: «publicado» ahí
> es `distance_class == summit`, no el predicado completo del dashboard (A97). Texto original
> intacto abajo, conservado por historia.

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

**Qué hace el código.** `pipeline/process_viirs.py:702-710` la aplica:

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
> **sí tiene** la máscara (`process_modis.py:507` y `:715`), sólo que la lee de la
> perilla del perfil `CLOUD_MASK_BT_K`, hoy en `0.0` — o sea el predicado queda
> tautológico y la máscara inerte. Lo mismo VIIRS 750. **El caso raro es VIIRS 375**:
> `process_viirs.py:702` tiene `CLOUD_BT_THRESHOLD = 260.0` **hardcodeado** e ignora
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

> ⚠️ **S141, verificador con contexto limpio (P-01): el punto 1 de abajo generaliza de más.** Laiolo et al.
> 2026 (Bull. Volcanol. 88:11, p. 4, «Satellite thermal data», columna derecha, 2.º párrafo) aplica el filtro
> por distancia y/o intensidad y por doble conteo a **su serie de estudio de Stromboli**, al combinar sensores.
> No dice que el NRT publicado lo aplique, y el 12 % (9.712 puntos sobre 82.329 imágenes) cuenta también las
> pasadas sin anomalía, así que no mide lo que recorta el filtro. Otros textos del grupo describen el canal
> NRT sin supervisión ni filtros: Campus et al. 2022 (Sensors 22, 1713, p. 8, §3.4, 3.er párrafo) y Campus et
> al. 2024 (Bull. Volcanol. 86:25, p. 4, «Dataset»). **No usar este párrafo para justificar una cerca por
> distancia o intensidad como clon literal.** Detalle: `docs/audit_s141/lectura/VERIFICADOR_LECTORES.md` P-01.

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
(`process_viirs.py:800`), con dos guards: `tests/test_cloud_mask_from_profile_s125.py`
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

## D16 — La grilla UTM NO explica el sub-reporte — **CERRADA (refutada) S124** ⚠️ **título rebajado S146: lo refutado fue el regrid F70, no la grilla de MIROVA**

> ⚠️ **S146** (`docs/AUDIT_S146.md` §2 y verificador **V-04**, gravedad 4). Todo lo factual del
> A/B de abajo se sostiene, y lo que sigue vivo está dicho al final de esta misma D («ver D17»).
> Lo que cae es el **título** y el **NO REABRIR**, que dicen más que lo medido:
>
> - El experimento fue **sólo VIIRS 375** (`04_tabla_brazos.py` l. 40 descarta todo lo demás),
>   **61 días**, y con **n = 1 en Copahue y n = 2 en Nevados de Chillán**. No tocó MODIS ni
>   VIIRS 750.
> - El remuestreo probado es el **F70**, que **D17 declara mal centrado** (se centró en
>   `volcano["lat"]/["lon"]` en vez del centro de la celda, `get_grid_center`) y **sin el paso de
>   bow tie** (D28). O sea, se refutó **«el regrid F70 arregla la magnitud»**, no **«la grilla de
>   MIROVA explica el sub-reporte»**.
> - La nota S130 de D17 dice lo contrario del título: el mecanismo geométrico **sí quedó
>   probado**, por otro eje, el **ángulo** (la razón contra MIROVA cae de 0,740 cerca del nadir a
>   0,253 más allá de 50° en VIIRS 375, n = 2.767), y el **brazo fiel (bow tie más remuestreo, en
>   ese orden y bien centrado) nunca se corrió**. Una mediana de 61 días promedia justo ese eje.
> - Añadido **A-13**: la ventana 2026-06-25 a 08-24 es **entera anterior a #535**, así que en el
>   régimen actual esto es **SIN DATO**, no una refutación.
>
> El frente vive en la **Fase 4** de `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`. Texto original
> intacto abajo, conservado por historia.

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

> ⚠️ **S146 (V-04): este «NO REABRIR» cubre el regrid F70 tal como se corrió, no el brazo fiel.**
> Bow tie más remuestreo, en ese orden y centrado en `get_grid_center`, **nunca se corrió**, y
> sobre MODIS y VIIRS 750 no hay medición. Ver la nota S146 al inicio de esta D y la Fase 4 del
> plan.

---

## D17 — Nuestra grilla F70 se centró en el punto equivocado — **ABIERTA (premisa probada, consecuencia NO)** S124/S125

> **S141, lectura de papers verificada renderizando las páginas** (`docs/audit_s141/lectura/VERIFICADOR_LECTORES.md` V-08 y V-13).
> **Grilla por sensor.** MODIS 51 × 51 celdas de 1 km (Coppola et al. 2023, Front. Earth Sci. 11:1240107, p. 3, §2.1);
> VIIRS M-band 67 × 67 celdas de 750 m, conservando la resolución nominal (Campus et al. 2022, Sensors 22, 1713, p. 7, §3.2,
> 2.º párrafo); VIIRS I-band 134 × 134 celdas de 375 m, «as per MIROVA workflow» (Aveni et al. 2024, RSE 315, 114388, p. 5,
> §3.2). Las tres cubren unos 50 km (67 × 0,75 = 134 × 0,375 = 50,25 km), por eso otros papers escriben «50 × 50 km»
> (Coppola et al. 2020, Front. Earth Sci. 7:362, p. 3; Campus et al. 2024, Bull. Volcanol. 86:25, p. 3): es la misma grilla.
> **Ángulo cenital: matiza la frase «su magnitud no depende del ángulo» de la nota S130.** El grupo escribe que el
> remuestreo corrige el efecto del cenit sólo «partially» y que el VRP cae con el ángulo (Aveni et al. 2023, Remote Sens.
> 15, 2528, p. 15 §4.2.1 último párrafo y p. 16 1.er párrafo), también por oclusión en bordes de cráter empinados (Aveni
> et al. 2024, RSE 315, p. 20, §7.3). En sus análisis descarta pasadas sobre 40° (Massimetti et al. 2020, Remote Sens. 12,
> 820, p. 15, §3.2, 3.er párrafo) o sobre 50° (Aveni 2024, Tabla 2 nota **, p. 14; Coppola et al. 2013, JVGR 249, p. 46,
> Apéndice 2, a mano), pero el canal NRT **no filtra por cenit** (Campus 2022 p. 8 §3.4; Campus 2024 p. 4). No es
> divergencia de producción. **Toda comparación de magnitud contra MIROVA se reporta también restringida a cenit ≤ 40°**
> antes de atribuir el gap de ~0,7 a un mecanismo.

> **S140, cita del grupo MIROVA verificada renderizando la página.** Fernandina 2025 (Remote Sens. 17, 1191), p. 9, §2.3.1:
> las bandas MIR y TIR se remuestrean a una grilla UTM regular de 51 × 51 km centrada en la cumbre del volcán, con las
> coordenadas del Global Volcanism Program. Es la descripción más reciente del flujo NRT escrita por el propio grupo.

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

## D18 — El ROI1 del paper es una CAJA de 5 km igual para todos; el nuestro es un CÍRCULO de 3 a 20 km por volcán — **ABIERTA (A/B corrido S130 → NO ADOPTAR; divergencia de fidelidad literal, prioridad baja)** S129/S130

> ⚠️ **S148: el «NO ADOPTAR, redistribuye y no recorta» de S130 y el «0 de 51» del brazo G de S148
> NO miden la caja: miden un defecto de cableado.** `enable_roi1_box_paper` entrega la caja sólo
> al primer pase. El segundo pase (`second_pass_adjacent`) recibe
> `is_summit_mask = vent_dist_per_pixel <= inner_radius_km`, o sea el círculo de siempre
> (`pipeline/process_viirs.py:1313`, y el mismo patrón en `process_modis.py:923` y
> `process_viirs_mod.py:892`), corre sin condicionar sobre toda la escena y vuelve a capturar con
> el umbral permisivo lo que el primer pase acaba de rechazar con el estricto. Medido en los 51
> negativos limpios de fuera de la caja: el primer pase cae de 86 a 7 píxeles y la recaptura sube
> de 98 a 175; el cúmulo publicado queda idéntico en los 51. **D18 nunca se ha medido con la caja
> en los dos pases**, así que su «prioridad baja» no tiene respaldo. Que S130 corrió con este
> mismo cableado es SOSPECHA razonable (el código del flag es de S130), no verificada.
> Evidencia: `docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md`. Arreglarlo toca `pipeline/process_*.py`
> (A45: tag y confirmación de Nicolás). El texto que sigue se conserva por historia.


> **S141, citas del grupo verificadas renderizando las páginas** (`VERIFICADOR_LECTORES.md` V-02, V-06, V-10).
> (1) El ROI de cumbre sigue siendo una caja de 5 × 5 km en 2023: «in the summit area (5 × 5 km) slightly lower thresholds
> are applied», y a mayor distancia umbrales algo más altos «which reduce false alerts», sin valores (Coppola et al. 2023,
> Front. Earth Sci. 11:1240107, p. 3, §2.1, columna derecha). Con `inner_radius_km` de hasta 20 km aplicamos umbrales de
> cumbre donde el grupo declara usar los más altos: toca la sobre-publicación. (2) La web de 2020 separa proximal y distal
> a 5 km fijos para todos los volcanes, como color de la serie, no como compuerta (Coppola et al. 2020, Front. Earth Sci.
> 7:362, p. 4, «VRP Time Series»). (3) En sus datasets de estudio el grupo cuenta alertas con radios al punto GVP ajustados
> al objeto: 1 km en La Fossa (Campus et al. 2024, Bull. Volcanol. 86:25, p. 5, columna derecha, 1.er párrafo) y 0,75 / 2 /
> 7 km en Vulcano, Agung y La Palma (Aveni et al. 2024, RSE 315, Tabla 2 nota **, p. 14). No describen el NRT: sirven para
> no comparar conteos de papers contra nuestro inner_radius, no para adoptar un radio (MISSION excluye lo per-volcán).

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
⚠️ **S146 (AUDIT_S146 §2, A-11 / E-01): falta acá la SEGUNDA rebaja de A82, la de S138 por la vía
espectral (los records se produjeron con la banda 21 primaria y la compuerta de 3 K, D21 y D22,
abiertas en este catálogo). Y el A/B de esta D (ventana 2026-05-29 a 08-24) es entero anterior a
#535: en el régimen actual es SIN DATO, no refutación (A-13).**

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

## D19 — `keep_peak` publica como *summit* a 0,0 km un píxel del borde del disco del Test 1, más frío que el fondo; y el second pass corre sin conjunto activo — **ABIERTA (CONFIRMADA gravedad 5 por verificador limpio; probe A75 corrido S135: el cráter no está en el Test 1, y los conteos son del régimen de fondo previo a #537; decisión D1/D2 de Nicolás pendiente)** S134/S135

**Medido S144 en el campo de MIROVA (frente cerrado, `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md`).** El
lugar donde `keep_peak` conserva su píxel **sí destaca** en la radiancia de MIROVA, medido en la imagen
de otra pasada de la misma noche (que no eligió ese píxel): +0,0514 [+0,0264, +0,0766] de tasa de exceso
contra otro punto de la misma banda. Pero el **86 % de ese efecto es permanente** (+0,0441 con rásteres
de otras noches) y lo de esa noche vale +0,0073 [-0,0241, +0,0385]; tres cuartos lo pone el máximo sobre
el disco y no la celda. O sea: **es un sitio tibio estable del terreno, no una anomalía de esa noche**.
Eso NO autoriza a apagar `keep_peak`, porque la radiancia sola no separa relieve tibio de fuente
permanente (A83): el frente que queda es de etiquetado (A72). Y la coincidencia de radio que sostuvo
las 5 noches del A/B S143 resultó ser un fenómeno de **Lastarria** (12 de 15 pasadas; 1 de 19 fuera, y
ahí el cúmulo está a 0,15 km del cráter).

**El fenómeno.** En un cono nevado la temperatura MIR nocturna sigue la altitud: dentro de un
disco de 3 km alrededor de la cumbre, el píxel más caliente es el borde del disco (cota más
baja), no el cráter (A69).

**Lo nuestro** (`pipeline/process_viirs.py:1832-1841`, flags efectivos
`ENABLE_TEST1_CONTEXTUAL_FILTER=True` y `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True`, adopción
S100 #340 «ctxpeak»): el Test 1 marca ~la mitad del disco (exceso sobre la mediana del anillo
1-3 km, `test1_integrated.py:376,412,420`), el filtro contextual lo intersecta con `dNTI_ctx`
—vacía en esas noches— y `keep_peak` conserva sólo `argmax(BT)`. Ese único píxel es el
`primary_cluster`; el ancla honesta (`anchor.py:89`) lo publica como `test1_roi` **en el vent a
0,0 km**; su magnitud (0,011-0,618 MW, mediana 0,046) es el exceso de ese píxel sobre un anillo
que solapa el ROI que mide (fondo autorreferente, S126), con la corona Eq. 6 apagada
(`ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375=False`).

**La medición** (S134 F3 + verificador, records V375 summit publicados desde 2026-06-01):
Villarrica 245/289 son `test1_roi`, 100 % de 1 píxel, mediana 2,80 km del cráter, 198/245 en la
corona 2,5-3,0 km (≈30 % esperable por área), **`bt_k < t_bg_k` en 172/245, mediana −2,95 K**.
Está en los **11 Tier A** (56-266 records cada uno), Láscar incluido (2,63 km): la diferencia
Láscar/Villarrica del anillo de S133 es la mezcla de fuentes (Láscar 138 `test1_roi` / 152
`ctx_cluster`; Villarrica 245 / 44). Control positivo: `ctx_cluster` de Láscar 0,18 km (n=152).
MIROVA corrobora más los `ctx_cluster` que los `test1_roi` dentro de cada volcán en 10 de 11.

**Lo que MIROVA hace**: Coppola 2016a integra el ROI y publica el cúmulo; la posición «en el
cráter» de una integral de ROI es una convención que el frontend declara
(`frontend/index.html:2779-2784`). **La magnitud del píxel único no la cubre ninguna convención.**

**Segunda cara** (`detection_context.py:877-879` vs `:518-523`): `second_pass_adjacent` corre con
conjunto activo vacío en 2.295/3.164 records, sin restricción de adyacencia y sin la compuerta
`bt > t_bg + 3 K` del first pass. Coppola 2016a (`sp426_5.txt:329-341`): *«applied only if one or
more pixels have been detected by the previous tests, and focuses on … the pixels adjacent to
those already flagged»*. 438 records publicados así en los 11 (Chaitén 89/323), a 3,2-3,9 km.

**Tensión, no fix (A83/A84)**: el mismo `keep_peak` devuelve pasadas MIROVA-confirmadas en
Lastarria (60 %), Tupungatito (34 %), Isluga (30 %). Cualquier cambio es régimen-dependiente y
debe medir FN sobre cat-b real. Pasa por MISSION.md (3 preguntas), A45 y el probe A75 en CI
(`experiments/_s134_audit/f3/probe_etapas_ci.md`).

**Guards**: `tests/test_guard_keep_peak_s134.py` (2 xfail estrictos: si alguien lo cura, XPASS
rompe la suite y obliga a actualizar esto). Detalle: `docs/AUDIT_S134.md` §3, §5.3, §D (D1, D2).

**Probe A75 en CI — S135** (`experiments/_s135_probe_etapas/RESULTADOS.md`, run 34071793829, las
6 pasadas de `tabla_6_pasadas.json`). Criterio pre-registrado aplicado tal cual: **H1 REFUTADA por la
rama que el diseño previó** — en Villarrica 2026-07-01 el cráter **no está en `mask_contributing`**
(0 px a <0,5 km; el más cercano, a 0,177 km, está 27 K bajo el fondo global; gradiente radial en
los 8 octantes). `keep_peak` no descarta el cráter: el Test 1 dispara sobre un disco frío sin señal en el cráter
(gradiente A69 **o tope de nube**: 27 K bajo el fondo es más de lo que da la cota, y el probe no
capturó I05), y el pico es el borde. El criterio refuta con esa sola pasada; es asimétrico por diseño. En las otras dos noches el cráter está en la máscara pero en el
rango 24/36 y 33/49 por BT, siempre bajo el fondo. **Tres noches, tres fenómenos**: 07-01 gradiente
del cono; 08-14 flanco S tibio (hoy dispara el first pass, 5 px, y `keep_peak` no corre); 08-31 un
objeto discreto a 2,97 km E, +8 K sobre un disco plano, dNTI-positivo, donde **`keep_peak` es
inerte** (los 2 px ya estaban en la intersección). Control Láscar 3/3: cráter rango 1 de la máscara,
+9 a +27 K sobre el fondo; `keep_peak` ni se invoca. **H2 confirmada con n=2** (07-01: 2/2 nuevos
≤ 3 K) y en el régimen vigente esa recaptura **fija la posición publicada** (3,789 km, summit).
**Hallazgo no previsto**: 2 de 3 pasadas de Villarrica no reproducen el record persistido con el
código de hoy sobre el mismo granule (08-14: t_bg 262,78 → 252,42 K; path `test1_roi` → `ctx_cluster`):
hasta #535 (2026-08-28 23:00 UTC; #537 fue documentación) `process_viirs.py` fijaba `CLOUD_BT_THRESHOLD = 260 K` a mano y el
fondo global excluía lo más frío; hoy lee `cloud_mask_bt_k: 0.0` (D14, cerrada, correcta). Villarrica
y Llaima bajan 6-8 K de fondo mediano en producción (396 → 40 records; Láscar no se mueve). **Los
conteos de arriba (245/289) son del régimen viejo**; el mecanismo sigue en el nuevo (08-31 reproduce
exacto) pero su tamaño hoy no está medido. Consecuencias para D1/D2 en `RESULTADOS.md` §4.

**Paso 0 corrido (S135, run 34091969140, `RESULTADOS_PASO0.md`)**: 9 pasadas cat-b (Lastarria,
Tupungatito, Isluga: `test1_roi` con alerta MIROVA en la misma pasada, ±20 min) + 3 controles de
Láscar con first pass vacío, con I05 y sin nube sospechada en ninguna. Veredicto pre-registrado
**INTERMEDIA**: 0 pasadas se pierden con `keep_peak` OFF teniendo el pico en el cráter; 4/9 se
pierden con el pico en el borde. **Corrección del verificador limpio (gravedad 5)**: `off_pierde`
ignoraba el second pass, que corre antes del filtro y no depende de `keep_peak`; con D2 como está
(permisivo) el second pass rescata 3 de las 4 (Lastarria 08-28 con el píxel idéntico; Tupungatito
08-21 con el cráter) y la cuarta (Isluga 08-19) no es señal (−3,8 K, cota A93 2,56 km del hotspot
de MIROVA, que era el cráter). Con D2 condicionado como manda Coppola 2016a, esos rescates
desaparecen y `keep_peak` OFF pierde el campo fumarólico de Lastarria (08-27 cota 0,08; 08-28
0,64, presupuesto 0,55 km) y el cráter de Tupungatito 08-21. **La tensión A83/A84 es real sólo
bajo D2 fiel, y está localizada en Lastarria (A84).** Además: 11/12 pasadas persistidas como `test1_roi` son hoy
`ctx_cluster` (first pass vacío 11/12 → 4/12; t_bg mediano 264,6 → 260,1 K): el régimen D14 ya
movió la mayor parte de D19 al path contextual, y el second pass sin conjunto activo (D2) es hoy
el que pone el cúmulo en el cráter de Tupungatito 08-21. **D1 y D2 hay que diseñarlos juntos**
(4 brazos, OFF/ON × D2 condicionado/no), sobre el régimen nuevo y estratificado por volcán. H2:
13/13 `newly_active` con first pass vacío ≤ 3 K (era 2/2).

**Relación con lo ya catalogado**: cierra la lectura de `docs/s133/ANILLO_TIER_A.md` (el anillo
no explica el déficit de paridad: F1 y F2 de S134 lo refutan por dos vías); D10 (S100) justificó
`keep_peak` con «pico = cráter», que es falso en los nevados de señal débil; D11/A82 quedan
intactas (esto es VIIRS375 y vía geométrica, no espectral).
⚠️ **«D11/A82 quedan intactas» ya no vale, S146 (AUDIT_S146 §2, E-01).** Se escribió en S134 y
cuatro sesiones después, en S138, D11 quedó **CONDICIONADA en este mismo archivo** (encabezado de
D11) y A82 quedó rebajada también **por la vía espectral**: el «irreducible» y el «todos los ejes
agotados» valen sólo bajo banda 21 primaria y compuerta de 3 K (D21 y D22, abiertas). La frase de
arriba no se tocó entonces; se conserva y se marca ahora.

## D20 — El NTI de MODIS se calcula con la banda 31 (11,03 µm); Coppola 2016a y Wright 2002 usan la banda 32 (12,02 µm) — **HALLAZGO, despreciable (cuantificado S128), registrado S135** ⚠️ **«despreciable» rebajado S146 a «chico y no medido»**

> ⚠️ **S146** (`docs/AUDIT_S146.md` §3, verificador **V-11**, cálculo de Planck propio e
> independiente). El cálculo de S128 se reproduce exacto (el corrimiento del NTI entre las dos
> bandas va de 0,0001 a 250 K a 0,0054 a 290 K), pero **la vara con que se declaró despreciable es
> la equivocada**: se midió contra el margen de ~0,14 al umbral K1, que es la ruta del NTI
> absoluto, cuando en MODIS lo que decide es el piso **C1 = 0,003**, unas 47 veces más chico. Y
> «en el dNTI se cancela» es falso como enunciado: queda un residuo que llega a 0,74 C1. Ahora
> bien, **la unidad «fracción de C1» también exagera**: el residuo es grande sólo cuando el dNTI
> ya es grande (ese caso tiene dNTI 0,024, ocho veces el piso, y alerta con cualquiera de las dos
> bandas). Lo que decide es el cambio **relativo** del dNTI: **6 a 9 % para contraste de terreno y
> 1 a 3 % para lava**. Sólo cambia de lado un píxel cuyo dNTI esté a menos de ese porcentaje del
> piso. Cuántos píxeles reales viven en esa franja es **SIN DATO** (hay que abrir gránulos).
> Hallazgo nuevo del verificador, con su signo: **la banda 32 amplifica más el terreno que la
> lava**, así que pasarse a la banda del paper empujaría hacia más alertas topográficas en los
> nevados, no hacia más lava. Es orden de magnitud (cuerpo negro, sin respuesta espectral ni
> atmósfera). No cambia ninguna decisión hoy; la marca es por método (un cierre calculado contra
> la vara que no gobierna, A95). Texto original intacto abajo, conservado por historia.

> ⚠️ **S141, corrige la nota S140 de abajo** (`VERIFICADOR_LECTORES.md` V-15). «La divergencia queda sólo contra SP426.5»
> es demasiado fuerte: el grupo describe la banda TIR de MODIS de forma inconsistente. Escribe 12,02 µm (banda 32) en
> Coppola et al. 2020 (Front. Earth Sci. 7:362, p. 3, columna derecha) y en Coppola et al. 2023 (Front. Earth Sci.
> 11:1240107, p. 3, columna izquierda), y banda 31 en Fernandina 2025 (p. 6). No se sabe cuál usa el NRT; el efecto sigue
> siendo despreciable (S128).

> **S140, verificado renderizando la página: el grupo MIROVA describe hoy la banda 31.** Fernandina 2025
> (Remote Sens. 17, 1191), p. 6, §2.2.1: de MODIS, MIROVA ingiere las bandas MIR B21 y B22 y el canal TIR
> **B31**. La divergencia queda sólo contra SP426.5 (banda 32, 2016); contra la descripción más reciente del
> propio sistema nuestro código coincide. No se propone cambio: el efecto ya era despreciable (S128) y ahora
> tampoco hay divergencia con el flujo NRT declarado en 2025.

**Lo que dice el canon.** `documentacion/sp426_5.txt:182-183` («radiance of band 32 (L32), centred
at 12.02 µm (TIR channel)») y `:211-216` (NTI = (L21ok − L32)/(L21ok + L32)); la Tabla 2 del
capítulo Springer (`coppola2024_chapter.txt:1035`) repite «TIR (12.02 µm)». Es la elección
original de MODVOLC (Wright et al. 2002).

**Lo nuestro.** `pipeline/process_modis.py:74-78` calibra la banda 31 (índice 10 de
`EV_1KM_Emissive`, λ = 11,03 µm) para el NTI, desde el commit `59846e897` (2026-04-08, «E3: add NTI
dual-criteria detection to MODIS (Band 31 TIR)»). Ningún documento del proyecto lo justificó; la
síntesis bibliográfica decía «B31/B32» sin distinguir. VIIRS no está afectado: I05 (11,45 µm) y
M15 (10,76 µm) son las que MIROVA usa.

**Cuantificación (S128, `docs/AUDIT_S128.md:654-660`, Planck):** el corrimiento del NTI entre las
dos bandas va de 0,0001 (250 K) a 0,0054 (290 K), contra un margen de ~0,14 entre el NTI típico de
escena y el umbral K1 = −0,8; en el dNTI se cancela porque es casi uniforme en la escena. **Real,
nunca registrado, numéricamente despreciable.**

**Por qué entra al catálogo recién en S135.** S128 lo anotó en la prosa de su auditoría «para no
re-descubrirlo», y el redactor de §4 del paper lo re-descubrió igual desde `sp426_5.txt` en S135:
una nota en una auditoría no es un registro. Queda acá para que §5.7 del manuscrito lo declare y
para que nadie lo vuelva a encontrar como novedad. **No se propone cambio**: pasa por MISSION
(puerta 1, cita verbatim) y sería un flip trivial (índice 11 en vez de 10), pero un A/B honesto
tendría que mostrar un efecto que el cálculo de S128 dice que no existe a la precisión de los
umbrales. Si algún día se hace, medir también el ETI (regresión NTI vs NTI_bk) y el `t_bg` TIR.

## D21: La banda MIR de MODIS: usamos la 21 como primaria; Coppola 2016a usa la 22 y la 21 sólo donde la 22 satura. **ABIERTA (medida S133 en magnitud y S137 en detección; ningún brazo cumple aún la batería)** S137 ⚠️ **El «ningún brazo cumple» cayó S146 (AUDIT_S146 §4, frente E E-08)**: con la vara corregida en el caso A2 el mejor brazo (banda 22, sin compuerta de temperatura, fondo local, conectiva `max`) pasa de 8 a **9 de 9**, y producción baja de 6 a **5 de 9**. Eso **levanta el bloqueo de criterio** que pesaba sobre D21, D22 y D11; no autoriza adoptar nada (9 de 9 en nueve escenas MODIS es fidelidad al Apéndice A, no dice nada de la sobre-publicación). Tres brazos quedan INDECIDIBLES por no guardar posición. Texto original conservado por historia

**El paper** (`documentacion/sp426.5.pdf`, p. 3, verbatim): *"we built a corrected spectral band
centred at 3.959 um (hereby called band L21ok), by using the L21 or L22 radiance, depending on band 22
saturation (or not), respectively"*. La 22 manda; la 21 entra sólo donde la 22 satura.

**Lo nuestro**: `ENABLE_MODIS_B22_PRIMARY = False` (B21 primaria). El flag existe, cableado, desde
S133; `process_modis.py:327` documenta que el ON es el que sigue al paper.

**El fenómeno.** La banda 21 es de ganancia baja (llega a ~500 K); de noche, sobre roca y nieve a
250-270 K, trabaja en el fondo de su escala con escalones gruesos. El dNTI, que resta a cada píxel el
promedio de sus vecinos, amplifica esa textura.

**La medición** (S137, `experiments/_s137/`):
- Probe de sigma, 84 pares, Láscar y Villarrica 12-31 ago 2026: sigma dNTI 0,0079 → 0,0017 (Láscar) y
  0,0071 → 0,0020 (Villarrica); el primer paso pasa de ~55-60 píxeles por escena a vacío en 80 de 84.
- En la escena exacta de la figura A6 del paper: sigma dNTI 0,0076 (B21), 0,0016 (B22); el del autor,
  medido en su figura, ~0,0008.
- Batería del Apéndice A: B22 con la fórmula 4/6 y 2/3; B22 con la prosa 4/6 y 3/3 (hoy 6/6 y 0/3).
  La pérdida de Villarrica la causa D22, no la banda; la de Eyjafjallajökull es de la evaluación.
- S133 ya había medido la magnitud: cae a un décimo en Láscar y a un cuarto en Villarrica.

**Próximo paso**: batería con B22 y sin D22 (pre-registro en `RESULTADO_ETAPA_Y_FIGURAS.md`). Adoptar
exige A45 y un A/B en los Tier A.

## D22: La compuerta de temperatura `bt > t_bg + 3 K` dentro de los Tests 2 y 3; la fórmula del paper no tiene condición de temperatura. **ABIERTA (divergencia literal confirmada; la atribución de S137 fue CORREGIDA en S138: la compuerta NO es lo que pierde a Villarrica A6)** S137, S138

> ⚠️ **Corrección S138** (`docs/AUDIT_S138.md` §8 y verificador §3.b, sobre las salidas commiteadas de la batería, sin reprocesar): la compuerta sólo actúa en el primer pase. El segundo pase (`second_pass_adjacent`, `detection_context.py:803`) recibe NTI, ETI y la máscara de activos, sin temperatura, y corre aunque no haya activos (`ENABLE_SECOND_PASS_CONDITIONED = False`, D19): rescata el píxel que la compuerta rechazó. En A6 con compuerta el cúmulo ya está a 0,8 km del cráter y publica 0,0 MW; quitar la compuerta no mueve ese cero; cambiar el fondo del anillo por vecinos da 0,539 MW (D25). Medido en producción: 14 % de los records VIIRS375 y 17 % de los VIIRS750 se detectan sólo en el segundo pase. **Un brazo de A/B que quite sólo la compuerta no devuelve ninguna alerta.** D22, D19/D2 y D25 no se pueden A/B-ear por separado. La divergencia literal sigue siendo real (la fórmula del paper no la tiene) y sigue abierta como fidelidad.

**El paper** (`sp426.5.pdf`, p. 7): los Tests 2 y 3 son dNTI y dETI contra `C1` o contra
`mu + C2 sigma`. Sin condición sobre la temperatura del píxel.

**Lo nuestro**: `first_pass_tests_2_and_3` exige además `bt > t_bg + bt_sanity_k`, con
`NTI_BT_SANITY_K = 3.0` (perfil `mirova_equivalent.yaml:44`). La misma constante aparece en unos 13
lugares de los tres sensores.

**Origen**: commit `59846e897`, 2026-04-08, "E3: add NTI dual-criteria detection to MODIS", para el
camino del NTI absoluto (`nti > -0,8 AND bt > t_bg + 3`). El comentario de ese commit dice *"We don't
implement dNTI/dETI (would need full spatial-contrast machinery)"*: se diseñó para un camino sin
contraste espacial y se heredó a los contextuales.

**El fenómeno.** En una cumbre helada el píxel que contiene un lago de lava sub-píxel sigue más frío
que la mediana de la escena, que incluye lagos y valles a baja altura. La compuerta descarta justo el
objeto que el contraste espectral delata. Es la imagen especular de A69.

**La medición** (probe por etapa S137, run 34746870643, Villarrica 24 jun 2009 05:55, la pasada de la
figura A6): con B22 el cráter tiene dNTI 0,0121 y dETI 0,0140, pasa los Tests 2 y 3 incluso con la
conectiva de la prosa, y cae sólo por la compuerta: BT 268,32 K contra fondo + 3 K = 275,25 K.

**S142, flag (OFF en producción).** `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` (`pipeline/profile.py`, sección `paths:`) quita la compuerta en VIIRS 375 en tres helpers (`contextual_dnti_hot_mask`, `dual_roi_contextual_dnti_hot_mask`, `first_pass_tests_2_and_3`, parámetro `apply_bt_gate`) y en el camino ETI (inerte). **No** la quita del camino B (NTI > K1, D23) ni en MODIS o VIIRS 750. Test sintético de punta a punta: sola, mueve los píxeles del segundo pase al primero y no cambia lo publicado (confirma S138). Brazos: `pipeline/profiles/_s142_ab_*.yaml` (S143). Plan: `docs/superpowers/plans/2026-09-15-flags-d22-d25.md`.

**Lo que no se sabe**: cuántos falsos positivos devuelve quitarla, en los negativos del apéndice y en
los Tier A. Hay que medirlo antes de proponer nada.

---

## D23: El Test 1 (NTI > K1) del paper no es un camino de detección en producción; sus píxeles sólo cuentan si además pasan los Tests 2 y 3. **ABIERTA (registrada S138, AUDIT_S138 H-S138-04)** S138

**El paper** (p. 6): los píxeles con `NTI > K1` se declaran activos por el Test 1 y se descartan como no aptos para los pasos siguientes (eso último es el GAP #A dentro de D11, reabierto S128).

**Lo nuestro**: K1 se calcula (`process_modis.py:662-668`) y entra a `combine_hot_paths` (l. 824), pero `hot_mask_2d = fp_hot` (l. 888) lo pisa con la salida del primer pase; `test1_mask=None` (l. 857-859). Igual en `process_viirs.py` (971-976, 1188, 1259) y `process_viirs_mod.py` (619-624, 783, 851). Control sintético (`experiments/_s138_audit/eje2/01_controles_sinteticos_detection_context.py`, M3): bloque 7x7 a 400 K sobre 280 K, el paper marcaría 49, el pipeline 28; interior 3x3, 1 de 9.

**Fenómeno**: en una colada o lago de lava de varios píxeles, los interiores están rodeados de píxeles igual de calientes, su dNTI es ~0 y no son anómalos respecto de sus vecinos; el paper los captura por NTI absoluto. Frecuencia de K1 en records operacionales: MODIS 0,09 %, VIIRS375 1,34 %, VIIRS750 0,12 % (pocos, pero son los eventos más energéticos). **Efecto**: sub-estimación de magnitud justo en fase efusiva fuerte. Gravedad 4 en magnitud de erupción, 2 en detección (el borde siempre dispara). No reprocesado sobre granules reales: la magnitud del efecto es SOSPECHA.

---

## D24: Los píxeles saturados de MODIS (DN 65533) se eliminan; el paper los conserva explícitamente. **ABIERTA (registrada S138, H-S138-09)** S138

**El paper** (p. 3): descarta los DN inválidos "with the exception of the pixels with DN = 65 533" (saturación), que se conservan marcados.

**Lo nuestro**: `rad[dn > 32767] = NaN` (`process_modis.py:246-252`), guard BT > 500 K a NaN (l. 555), y en `merge_mir_bands` (l. 331-333) el NaN de B21 cae a B22, que también satura. Origen: corrección F28 (S73) a un caso de basura (PP 2026-03-18).

**Fenómeno**: en un paroxismo el píxel del foco satura la banda 21 (~500 K) y es el más caliente de la escena; queda NaN, no entra al NTI, al pool ni al hot mask, y no aporta radiancia: agujero en el centro de la anomalía. Sin casos en la ventana medida (`sanity_cap_tocado = 0`), invisible hoy; sólo actúa en paroxismos, pero ahí resta. Gravedad 3.

---

## D25: El fondo del VRP es la mediana de un anillo regional de 5 a 25 km, no la media de los píxeles que rodean al activo; y el exceso se recorta a cero. **ABIERTA (registrada S138, H-S138-01; es la palanca real detrás de A6 y del cráter en 0,0 MW)** S138

**El paper** (p. 8, ecuación 6): el fondo es "the arithmetic mean of all the pixels surrounding the active one"; no necesita recorte.

**S140, confirmación posterior del mismo grupo** (Fernandina 2025, Remote Sens. 17, 1191, p. 9, ecuación 3, página renderizada): el fondo es la radiancia promediada de los píxeles vecinos **no alertados**. Coincide con SP426.5 y agrega que los alertados quedan fuera del promedio.

**S141, siete textos más del grupo, páginas renderizadas** (`docs/audit_s141/lectura/VERIFICADOR_LECTORES.md` V-07 y P-02): fondo = media de los píxeles que rodean al alertado o al cúmulo, nunca mediana ni anillo regional. Coppola et al. 2013 (JVGR 249, p. 46, Apéndice 2, bajo la ec. A.1); Coppola et al. 2020 (Front. Earth Sci. 7:362, p. 3, bajo la ecuación del VRP); Campus et al. 2022 (Sensors 22, 1713, p. 7, §3.2, bajo la ec. 2); Aveni et al. 2023 (Remote Sens. 15, 2528, p. 8, §3.3, bajo la ec. 3: vecinos «non-alerted»); Coppola et al. 2023 (Front. Earth Sci. 11:1240107, p. 3, §2.2, ec. 1, y p. 6, Tabla 1, fila Tot_Lmir_bk); Campus et al. 2024 (Bull. Volcanol. 86:25, p. 3, columna derecha, bajo la ec. 1, y ec. 2). **Segunda divergencia dentro de D25**: Campus 2024 precisa que cada píxel alertado tiene **su propio** fondo (media de sus vecinos) y que el fondo total es la **suma** de esos fondos; la columna Tot_Lmir_bk del archivo v1 es esa suma («Sum of MIR background radiance from all alerted pixels», Coppola 2023 Tabla 1). Lo nuestro usa un único `t_bg` para todos los píxeles del cúmulo. Para comparar `diag_L_bg_w_m2_sr_um` (T7, S140) con Tot_Lmir_bk hay que dividir este último por Npix. Ningún texto visto menciona recortar a cero el exceso negativo: esa mitad de la pregunta 4 del correo sigue abierta.

**Lo nuestro**: `np.median` sobre el anillo (`detection_context.py:1064`; `process_modis.py:571-579`, 1023; `process_viirs_mod.py:1012`, sin alternativa en M-band); kernel 3x3 sólo para los 5 volcanes opt-in del YAML (`local_kernel_bg`: PCC, Villarrica, Chaitén, PP, Lastarria; `process_modis.py:1044-1052`); `delta_L` recortado a 0 (`process_modis.py:1060`). D8 quedó marcada resuelta por el kernel opt-in, pero la divergencia literal sigue vigente en 6 de 11 Tier A en MODIS, 11 de 11 en M-band y todo el camino Test 1.

**S142, flag (OFF en producción).** `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` calcula, en VIIRS 375, el fondo de cada píxel alertado como la media de la **radiancia** de sus vecinos no alertados (`pipeline/vrp_regimes.py:neighbor_mean_radiance_background`). Cuando los 8 vecinos están alertados, la ventana crece hasta `vrp_bg_neighbor_max_half_px` (3 = 7x7, decisión abierta), y si aun así no hay vecinos, se usa el fondo de hoy como respaldo, contado en `diag_bg_vecinos_n_sin_vecinos`. Entra en el bloque contextual (`anomaly_pixels`, cúmulo, F5) y en los dos recomputes del Test 1. Pisa al kernel 3x3 opt-in. El recorte a cero **no** cambia. MODIS y VIIRS 750 siguen con la mediana. En la escena sintética del plan, el cráter pasa de 0,0 a ~0,097 MW. Brazos: `pipeline/profiles/_s142_ab_*.yaml` (S143). Plan: `docs/superpowers/plans/2026-09-15-flags-d22-d25.md`.

**Fenómeno**: en una cumbre helada el cráter con lava sub-píxel está más frío en MIR que la mediana de un anillo lleno de valle tibio; su exceso sale negativo y se recorta a 0,0 MW aunque los Tests 2 y 3 lo hayan aceptado (Villarrica A6 con B22; Tupungatito 2026-08-21 05:30 UTC VIIRS_SNPP_750, cúmulo de 1 píxel summit en 0,0 MW, fondo 256,4 K). En noches-sensor: VIIRS750 33 de 246 noches ALERTA de MIROVA con el cráter en cero (ventana 2026-01-11 a 2026-09-07); **en noches de volcán, 0 de 33**: todas cubiertas por otra pasada (verificador S138 §3.d). Es fidelidad y magnitud, no recall. Y al revés, infla donde el anillo es más frío que el entorno del foco (glaciar de Tupungatito, A19). Gravedad 4.

**S145, sustrato de M-band medido antes de cualquier A/B** (`experiments/_s145_d25_v750/sustrato.py`
→ `sustrato.json`; ventana 2026-03-01 a 2026-09-20, los 11 Tier A, publicar = predicado del
dashboard con node). Sobre **9338 pasadas nocturnas de VIIRS 750**: **1035** tienen el cúmulo en el
cráter con 0,0 MW (las que el fondo por vecinos podría despegar) y **2301** ya tienen magnitud
(2299 publican, y a ésas el cambio se la sube). Pero en **noches** (A94) el premio es **cero**: de
las 48 pasadas de rescate con alerta de MIROVA, **ninguna** cae en una noche-volcán que otra pasada
no cubra ya, y en cambio **20 noches** que MIROVA miró sin ver nada se estrenarían. De las 2299 que
ya publican, MIROVA no vio nada en 1130 y alertó en 223. **Lectura**: en M-band D25 es fidelidad de
magnitud, no recall, y su efecto dominante cae del lado de la sobre-publicación (A98). Se suma a
que la razón de magnitud a igual conteo ya está en 0,995 (A99 ⚠️ **rebajada S146, AUDIT_S146
V-12**: ese 0,995 compensa dos factores opuestos, 1,140 de píxel caliente contra 0,873 de fondo
sobre n = 342 pares, y compensa además entre volcanes, de 0,66 en Copahue a 1,39 en Villarrica;
sólo 156 de 342 pares quedan entre 0,8 y 1,25, así que **A99 ya no apaga la búsqueda en k, área,
banda ni Planck**) y a que en VIIRS 375 el fondo del
cúmulo **ya se midió con criterio pre-registrado y no cerró la brecha en ningún volcán**
(`docs/HYPOTHESIS_LOG.md`, H_S141_VECINO_FOCO_V2, resuelta como no confirmada en S142). Los 1035
son un **techo de exposición, no una predicción**: el script clasifica, no corre el pipeline.
Plan con el flag apagado y A/B pre-registrado (criterio primario = sobre-publicación):
`docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md`.

**S145, flag de M-band IMPLEMENTADO y APAGADO** (plan ejecutado, tag `pre-s145-d25-v750`, A45
confirmado). `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750` (`pipeline/profile.py`, clave en `paths:` del
perfil) cablea `vrp_bg_neighbor_mean_v750` en los tres sitios donde M-band resta fondo: el bloque
contextual y los dos recomputes del Test 1, todos **posteriores** a que `hot_mask_2d` quede fijado,
así que el cambio es de magnitud y no toca detección. Los dos bloques del Test 1 promedian sobre la
**unión** de `hot_mask_2d` con `test1_hot_filtered`. Diagnósticos `diag_L_bg_vecinos_w_m2_sr_um` y
`diag_bg_vecinos_n_sin_vecinos`, que sólo aparecen con el flag ON. Comparte
`VRP_BG_NEIGHBOR_MAX_HALF_PX` con I-band. **Con el flag OFF la salida es idéntica** (golden de S142
verde). Medido de punta a punta sobre la escena `nevado` del arnés: el fondo cae de 0,204 a 0,105
W/m²/sr/µm y la magnitud sube de 0,705 a 2,291 MW, **un factor 3,2**, que es la escala del riesgo de
sobre-publicación si se adoptara. **MODIS sigue con la mediana del anillo**: ahí D25 queda abierta y
su sustrato son 11 pasadas de rescate con 0 alertas de MIROVA, así que no hay ni qué medir.

---

## D26: El segundo pase calcula mu y sigma sin los filtros de no-aptos del paper (borde, dNTI < -0,1, K1). **ABIERTA, efecto nulo bajo la conectiva `min` (registrada S138)** S138 ⚠️ **el «efecto nulo» cayó en S145; marcado acá en S146**

> ⚠️ **S145, recogido en S146** (`docs/AUDIT_S146.md` §2). El «efecto nulo» de este encabezado se
> derivó de un script que lee **sólo el dNTI**: midió el Test 2 y atribuyó la conclusión a los
> dos. Medido después, **el sigma gobierna en el 58,7 % de VIIRS 375 y en el 75,0 % de VIIRS
> 750**, o sea el piso C1 no manda siempre y el efecto de esta divergencia **no es nulo** fuera de
> MODIS. Es el caso de manual de A95 (un cierre hereda las premisas de la lectura con que se
> derivó) y por eso encabeza el porqué de `experiments/_s145_censo_cierres/censo.py`. El texto de
> abajo, que acota el enunciado a MODIS bajo `min`, se conserva entero.

**El paper** (p. 6-7): los no aptos se excluyen de "the subsequent steps", incluido el segundo cálculo.

**Pieza para el frente de la conectiva (S140, sin cerrarlo).** Coppola 2014 (IJRS, p. 3409 de la revista, p. 9 del PDF, renderizada) escribe su test 2 con un `and` explícito entre las dos condiciones: superar el máximo de los píxeles de referencia **y** superar su media más 3 desviaciones. Ojo con el alcance: es el algoritmo de Stromboli de 2014 (ROI2/ROI3, umbrales estacionales de NTI), no el de SP426.5, así que muestra cómo escribía el grupo esa conjunción, no qué conectiva usa MIROVA en los Tests 2 y 3.

**Lo nuestro**: `detection_context.py:904` contra 81-140 y 477 (el primer pase sí los aplica). Control sintético M4: un solo outlier con dNTI << -0,1 multiplica el sigma del segundo pase por 12 (0,00085 a 0,0104) mientras el primer pase lo excluye. Bajo `min(C1, mu + C2 sigma)` el piso gobierna y el efecto sobre el umbral es nulo (S136 midió que `mu + C2 sigma > C1` en el 100 % de MODIS). Gravedad 1 hoy; 3 si se adopta la rama de la prosa (`ENABLE_TESTS_23_PROSE_BRANCH`).

---

## D27: El día no existe: la Tabla 1 diurna (K1 = -0,6, C1 = 0,02, C2 = 15) está escrita y nunca se ejecuta. **DELIBERADA (MISSION: sólo noche), registrada S138 para que conste como divergencia literal** S138

`_select_thresholds` (`process_modis.py:357-380`), `ENABLE_DAYTIME_MODIS = False`, `run_pipeline.py:185-195`, `store.py:171-182`. El paper procesa pasadas diurnas y advierte que ahí están la mayoría de sus falsas alertas (p. 16-17; A76). MIROVA publica detecciones diurnas de MODIS que el operador no verá acá. Gravedad 2 (recall de día; riesgo de falsos positivos si se activara). No se propone cambiar.

---

## D28: El bow tie de MODIS no se trata en ningún paso del perfil operacional. **ABIERTA, parte de D17 (registrada S138 como paso propio)** S138

El paper (p. 3) corrige el solapamiento de barridos antes de remuestrear; el código no tiene el paso (`process_modis.py:501-512` sin regrid; `ENABLE_UTM_REGRID = False`, leído de `thresholds:`, `profile.py:606`). Consecuencia junto con D17: los 8 vecinos son píxeles nativos de tamaño variable y la magnitud usa un área que no es la del píxel (S131). Gravedad 3 dentro de D17.

**S141, tres textos del grupo, páginas renderizadas** (`docs/audit_s141/lectura/VERIFICADOR_LECTORES.md` V-05): los píxeles duplicados por bow tie se **identifican y eliminan** sobre el gránulo original, antes del remuestreo; ninguno dice que se promedien. Coppola et al. 2013 (JVGR 249, p. 46, Apéndice 2, último párrafo de la columna izquierda: «removal of the bow-tie effect and resampling into an equal area projection with 1 km pixel size»); Coppola et al. 2023 (Front. Earth Sci. 11:1240107, p. 3, §2.1: «pixels affected by bow-tie distortions are identified and removed», citando Coppola et al. 2010); Aveni et al. 2023 (Remote Sens. 15, 2528, p. 8, §3.2: «Consistently with the MIROVA algorithm», citando su referencia [82]). Tensión de fuentes sobre el método exacto (Coppola 2010 contra la ref. [82] de Aveni 2023, que un lector identificó como Liu et al. 2008 sólo desde la capa de texto: SOSPECHA). La pregunta abierta se reduce a «¿qué método exacto?».

---

## D29: Refit iterativo a 3 sigma en la regresión cuadrática de NTIbk. **ABIERTA, menor (registrada S138)** S138

`detection_context.py:685-688` y 745-765: la regresión NTI contra NTIapp se reajusta excluyendo residuos mayores a 3 sigma. El paper (p. 5, ecuación 4) describe un solo ajuste. Probablemente mejora el fondo, pero no está en el paper y no tiene flag. Gravedad 1.

---

## D30: El Test 1 integrado en el ROI es un detector PROPIO; el Test 1 del paper es por píxel y su cita bibliográfica no corresponde a ningún artículo localizable. **ABIERTA (registrada S146, AUDIT_S146 V-06, gravedad 5; descrita, sin decisión)** S146

**El fenómeno, primero.** Una fuente térmica más chica que el píxel (el lago de lava de Villarrica,
un campo fumarólico) no levanta ningún píxel lo bastante como para cruzar un umbral por píxel, pero
sí calienta un poco a varios vecinos a la vez. Nuestro Test 1 integrado aprovecha eso: suma el
exceso de radiancia MIR de todo un disco de 3 km sobre el fondo de un anillo de 1 km y dispara si
esa suma supera 3 sigmas propagadas. Es el mecanismo que en S27 subió el recall de 50 a 80 % (⚠️
**ese número quedó SIN EVIDENCIA en S147**, no tiene script; ver la rebaja al final de esta D) y
cerró D4, y es también el que A69 identifica como el que capta el valle tibio en los nevados,
porque trabaja sobre **MIR absoluto**.

⚠️ **Y la vara del disparo está mal armada, medido S147** (`docs/S147_TEST1_ESTADISTICO_CORREGIDO.md`):
la suma **recorta** los excesos negativos a cero pero se compara contra la desviación de la suma
**sin** recortar. Con ruido puro la suma recortada vale `0,399·N·sigma`, sigma se cancela y el
criterio depende del **tamaño del disco**: se cumple con N mayor que 56,6, y el disco tiene ~201
píxeles en VIIRS 375, 50 en VIIRS 750 y 28 en MODIS. Reproducido en S147 por dos caminos propios:
un banco sintético sin nada caliente dispara en **38 o más de 40 escenas**
(`tests/test_test1_estadistico_nulo_s147.py`), y sobre los records persistidos la mediana de
`test1_k_observed` se sienta en **0,83 a 0,91 veces** el valor de reposo en los tres sensores
pese a que sus discos difieren por un factor 7
(`experiments/_s147/reposo_test1_en_records_reales.py`).

**El paper** (`documentacion/sp426.5.pdf` p. 6, renderizada a imagen y leída así, no por la capa de
texto, A95), verbatim:

> *«NTI_PIX > K1 (Test 1), where NTI_PIX is the NTI pixel value and K1 is the threshold»*

> *«Pixels that satisfy Test 1 are flagged as "active" and subsequently discarded (unsuitable) for
> further steps.»*

Es un umbral fijo **por píxel** sobre el NTI. No hay suma sobre el ROI en ninguna parte del
algoritmo de detección del paper: la única suma es la de la magnitud (`RP = Σ RP_PIX`, Ec. 8).

**La cita que lo respaldaba, y por qué cae.** `MIROVA_DIVERGENCES.md` (bloque H_S27_1) lo hace
pasar la pregunta 1 de `docs/MISSION.md` con «Test 1 ES Coppola 2015 §2.2 Eq.1», y la cabecera
FICHA del código (`pipeline/test1_integrated.py:12-18`, `pipeline/process_modis.py:16`) cita
«Coppola et al. 2015, *MIROVA: a new hotspot detection system based on MODIS Level 1B data*,
Bulletin of Volcanology 77:55, §2.2». Verificado en S146 por dos bases bibliográficas
independientes:

- El artículo **55 del volumen 77** de *Bulletin of Volcanology* (2015) es **Heap et al.**,
  *Fracture and compaction of andesite in a volcanic edifice*, DOI **10.1007/s00445-015-0938-7**
  (mecánica de rocas, nada que ver).
- **Crossref y OpenAlex: 0 artículos de Coppola en esa revista en 2015**, con control de consulta
  (la misma búsqueda sin autor devuelve 12 artículos de ese número, así que el cero no es de la
  consulta). Buscando el título citado, lo más parecido que devuelve Crossref es el propio
  **SP426.5**.
- El proyecto ya había establecido (por hash antes de S128, y por contenido en S128) que su
  «coppola2015.pdf» **es** `sp426.5.pdf`
  (`documentacion/BIBLIOGRAPHY_SYNTHESIS.md:36-47`). Ahí la Ec. 1 es el NTI (p. 4), no un test
  integrado, y no existe ningún §2.2 con esa fórmula.
- Ningún texto del grupo cita un «Bull. Volcanol. 77:55»: todos citan el algoritmo como «Coppola
  et al. 2016».

**Lo nuestro, en producción**: `ENABLE_TEST1_PATH = True` en `mirova_equivalent`, con
`TEST1_K_SIGMA 3.0`, `TEST1_ROI_KM 3.0`, `TEST1_MIR_RELATIVE 0.02`.

**Cómo entra al dato publicado, que no es como suena.** El Test 1 **no entra a la máscara** de
píxeles calientes: **compite por la fuente del cúmulo publicado**. Si no hay cúmulo contextual, o
el que hay cae fuera del radio interno, el Test 1 pone el ancla en el cráter
(`final_hotspot_source = test1_roi` en VIIRS, `test1` en MODIS) y arma él solo el cúmulo que el
dashboard muestra (Fase 1 §0, leyendo `process_viirs.py` l. 1763 a 1786 y `anchor.py` l. 67 a 89).
Por eso se puede atribuir desde lo persistido y no sólo contar disparos.

**Cuánto sostiene, medido** (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` §4 y §8, ventana
2026-09-01 a 2026-09-20, entera posterior a #535; unidad de la sobre-publicación = pasada en
negativo limpio, unidad del recall = noche de volcán. **Verificado en
`docs/audit_s146/FASE1_VERIFICADOR.md`: sus seis afirmaciones salen CONFIRMADAS, cuatro con
matiz, gravedad máxima 2. Leer sus §5 y §6 antes de usar la banda 21,4 a 36,5 %, y su §7 antes
de usar el 74 de 78**):

| sensor | negativos limpios publicados sólo por el Test 1 | tasa hoy | tasa sin Test 1 (cota mínima a máxima) |
|---|---|---|---|
| VIIRS 375 | **186 de 322** (57,8 %), de n = 373 | 86,3 % | 21,4 % a 36,5 % |
| VIIRS 750 | **89 de 133** (66,9 %), de n = 622 | 21,4 % | 5,3 % a 7,1 % |
| MODIS | 8 de 50 (16,0 %) | 11,4 % | 8,9 % a 9,6 % |

Y del otro lado de la cuenta, que es la mitad que decide si se puede apagar algo: de las **78
noches positivas** de la ventana, hoy se publican las 78 y sin el Test 1 **74 siguen publicadas
con certeza, 4 quedan SIN DATO y ninguna se pierde con certeza** (las 4: Isluga 2026-09-19,
Lastarria 2026-09-01, Nevados de Chillán 2026-09-18, Villarrica 2026-09-16). En VIIRS 375 sólo
**2 de 143** pasadas positivas publicadas dependen sólo del Test 1, contra el 57,8 % del lado
negativo, y ese contraste queda **fuera del nulo** de etiquetas barajadas dentro de cada volcán
(observado 0,5637 contra un intervalo de 0,2506 a 0,3718, que ya descuenta la paradoja de
Simpson). En **MODIS es al revés**: 38 de las 50 negativas publicadas (76,0 %) las sostiene el
camino contextual, el que **sí** está en el paper, y se concentran en Puyehue Cordón Caulle.

**Lo que aporta el verificador con contexto limpio** (`docs/audit_s146/FASE1_VERIFICADOR.md`,
seis afirmaciones CONFIRMADAS, cuatro con matiz):

- La atribución **no depende de la etiqueta** en la mayoría de los casos: **158 de los 186**
  T1_SOLO de VIIRS 375 y **86 de los 89** de VIIRS 750 tienen la máscara contextual **vacía**, y
  por `clustering.py` l. 75-76 eso equivale a «sin Test 1 no hay cúmulo». Los 28 y 3 restantes
  descansan sólo en la lógica de `anchor.py` (§5).
- El patrón **no es de dos o tres volcanes**: T1_SOLO aparece en **los 11** Tier A en VIIRS 375
  (Copahue 39, Villarrica 27, NdC 26, Llaima 26, PP 21, Chaitén 17, Lastarria 13, Láscar 8,
  Tupungatito 6, PCC 2, Isluga 1) y en los 11 en VIIRS 750 (§9).
- La subclase **«rival débil» está mal atribuida**: `resolve_test1_source_priority` tiene tres
  ramas y la primera (`eruption_far`) no exige rival débil. El informe rotula 21 negativos como
  rival débil cuando sólo 16 lo exigen, y 20 de los 23 positivos cuando 15 se explican por
  `eruption_far`. Donde manda `eruption_far`, sin Test 1 el cúmulo contextual habría publicado,
  o sea **el contrafactual está más cerca del 36,5 % que del 21,4 %** (§6).
- **Por sensor, VIIRS 750 pierde con certeza 1 de sus 14 noches** con alerta (PCC 2026-09-07);
  la noche sobrevive en el agregado porque VIIRS 375 y MODIS publican. Si el criterio del A/B
  exige conservar la alerta **en el sensor en que MIROVA la publicó**, eso cuenta como pérdida y
  hay que escribirlo antes de correr (§7).
- El verificador **recomienda correr el A/B del brazo «sin Test 1 integrado»**, justamente
  porque la atribución es inferencia sobre campos persistidos y no simulación de la etapa
  siguiente: el VRP del cúmulo contextual que el Test 1 pisa no se guarda en ningún campo, así
  que ningún número persistido puede cerrar la banda (§12).

**Lo que ese número NO dice** (A54): «MIROVA calló» no es «artefacto». Los sostenidos sólo por el
Test 1 en Villarrica y Copahue son en buena parte calor real que MIROVA no publica, que es
justamente para lo que se adoptó en S27; la mediana publicada de esa clase es de centésimas de MW
en VIIRS 375. La tabla dice dónde está la palanca de **paridad**, no qué es real. Por eso el
desenlace natural es la **Fase 2b** (mudar lo propio al perfil `experimental`, no borrarlo), que
es decisión de Nicolás.

**Por qué importa.** (1) Es el único camino de detección del perfil «clon literal» cuyo respaldo
bibliográfico nadie ha tenido nunca en la mano, y entró por la puerta 1 de MISSION («está en un
paper MIROVA»), que es justamente la pregunta que apaga la sospecha de parche propio. (2) Es
dominante en el sensor que sostiene el recall: S138 midió `triggered_test1` en el **77,89 % de
los records VIIRS 375** y en el **22,21 % de los VIIRS 750**
(`docs/audit_s138/EJE_2_matriz_conformidad_pdf.md:112`, citado por el auditor C de S146; no pasó
por el verificador). En la ventana de la Fase 1 son 800 de 954 (83,9 %) y 200 de 949 (21,1 %). (3) Es un Sistema de Decisiones Automatizadas bajo la Resolución CPLT
N°372 y la ficha publicable declara una fuente que no se puede mostrar.

**Lo que esta D NO dice**: no dice que el Test 1 integrado esté mal ni que haya que apagarlo. ⚠️
**La frase que sigue CAYÓ en S147** (`docs/audit_s147/VERIFICADOR_H_A01.md`, hallazgos H1, H2 y
H3, verificador con contexto limpio): (a) el "50 a 80 %" **no tiene instrumento**, el commit que
lo declara (`a7b567f00`) cambia un solo archivo y es este catálogo, y en el árbol de ese commit no
existe ningún script de recall sobre 11 volcanes ni sobre 507 registros; queda **SIN EVIDENCIA, no
refutado**; (b) la medición **sí es circular**, aunque no por la disyunción que se le achacaba
sino por la etiqueta: con el Test 1 encendido, su disparo fija por construcción
`final_hotspot_source = "test1"`, `distance_class = "summit"` y el recómputo de VRP, que son las
dos condiciones del predicado de acierto de la época; (c) el único A/B limpio del Test 1 encendido
contra apagado (S25, `experiments/54_test1_ab/REFS_FORENSE.md:15-18`) dio **6 contra 6**, o sea
ganancia cero, y los "+30 puntos" aparecen recién **después** de agregar la regla que fuerza la
etiqueta summit. Texto original conservado por historia: El
resultado empírico de S27 (recall 50 a 80 %) no se toca. Lo que sigue abierto es **cuánto de las
4 noches SIN DATO y de las pasadas donde el Test 1 pisó a un cúmulo contextual (`T1_SOBRE_CTX`:
56 en VIIRS 375, 11 en VIIRS 750, en negativos limpios publicados; más 23 en positivos de VIIRS
375) sobreviviría sin él**, que no se puede saber desde lo
persistido porque el VRP del cúmulo contextual no se guarda cuando el Test 1 lo reemplaza. Eso
pide el probe de sólo lectura especificado en §9 de la Fase 1 (patrón A75, en GitHub Actions). El
brazo «sin Test 1 integrado» es el que tiene más sustrato de todo el plan y va primero en la
Fase 2; el brazo «Test 1 por píxel literal en reemplazo» tiene sustrato casi cero
(`diag_n_nti_path > 0` en 5 pasadas de VIIRS 375 y 0 en el resto), así que no recupera lo que el
integrado sostiene. Estado: **ABIERTA, descrita, sin decisión**.

**Pendiente fuera de esta fase** (archivos con A45, van con tag): la cabecera FICHA de
`pipeline/test1_integrated.py`, la de `pipeline/process_modis.py` y
`docs/FICHA_SDA_VRP_CHILE.md`.

---

## D31: El test de temperatura de brillo con N·σ = 5 / 10 no está en el paper; los números son los de C2, que en la Tabla 1 multiplican otra variable. **ABIERTA como divergencia de ATRIBUCIÓN; el camino está APAGADO y su sustrato es CERO (registrada S146, AUDIT_S146 V-08 más Fase 1)** S146

**El fenómeno, primero.** Hay dos maneras distintas de preguntarle a un píxel si está caliente.
Una es mirar **cuánto brilla en 4 µm respecto de su entorno** por la vía del NTI, que es una razón
entre dos bandas y por eso se lleva bien con el terreno. La otra es mirar **su temperatura de
brillo absoluta** y compararla con la del fondo. La segunda es la que A69 señala como vulnerable:
en un volcán nevado la cumbre está fría y el valle de baja altitud está tibio, así que el campo de
temperatura absoluta está dominado por la altitud y no por el volcán.

**El paper** (`documentacion/sp426.5.pdf` p. 7, renderizada a imagen). Los Tests 2 y 3 son, en la
página:

> Test 2: `dNTI_PIX > C1` **or** `dNTI_PIX > μ_dNTI + C2·σ_dNTI`
>
> Test 3: `dETI_PIX > C1` **or** `dETI_PIX > μ_dETI + C2·σ_dETI`

Y en la **Tabla 1** («Parameters used in the MIROVA algorithm»), de noche, ROI1 / ROI2:
**K1 = −0,8 / −0,8**, **C1 = 0,003 / 0,01**, **C2 = 5 / 10** (de día: −0,6, 0,02 y 15). O sea
**C2 multiplica la desviación estándar de dNTI y de dETI**, no otra cosa. La única aparición de
«brightness» en las 25 páginas está en la p. 5, definiendo la NTIapp (Tapp = BT del TIR). **El
paper no tiene ningún test sobre temperatura de brillo.**

**Lo nuestro**: `pipeline/profiles/mirova_equivalent.yaml:128-134` define
`n_sigma_mir_summit: 5.0` y `n_sigma_mir_scene: 10.0` rotulados «N·sigma differential
summit/scene (Coppola 2016a Tabla 1)», y `:279-282` enciende `enable_dual_roi_bt: true` con la
misma atribución. Ese 5 / 10 se aplica a la **BT del MIR**, no al dNTI ni al dETI. Es un préstamo
de los números de C2 a otra variable.

**El camino está APAGADO hoy: la divergencia es de atribución, no de comportamiento.** Medido en la
Fase 1 (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` §0 y §9; **verificado en
`docs/audit_s146/FASE1_VERIFICADOR.md`: seis afirmaciones CONFIRMADAS, cuatro con matiz, y ésta
es una de las que llevan matiz, ver su §4**) y comprobado de nuevo acá al escribir esta D:

- `ENABLE_BT_PATH_HOT = False` leído de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`, no
  del YAML (A89). `ENABLE_DUAL_ROI_BT = True` **sí** construye la máscara, pero
  `process_viirs.py:997` la pone en cero (lo mismo en `process_modis.py:660` y
  `process_viirs_mod.py:640`), así que el `true` del YAML no significa que el
  camino decida.
- El contador `diag_n_bt_path` vale 0 en las 2.360 pasadas nocturnas de la ventana desde el
  2026-09-01 (457 MODIS, 954 VIIRS 375, 949 VIIRS 750), pero eso **no es evidencia
  independiente**: con el flag en False el contador cuenta un arreglo de ceros, y nunca fue
  mayor que cero en ningún record de toda la historia del corpus (60.112 records con el campo
  presente, `docs/audit_s146/FASE1_VERIFICADOR.md` §4). **La evidencia es el flag.**

O sea: **un brazo de A/B «sin test de temperatura de brillo» tiene sustrato cero y no hay que
correrlo**. Lo que queda es corregir los documentos que lo dan por activo y por canónico.

**Por qué importa igual.** (1) La atribución convierte un camino propio en canon: `CLAUDE.md` lo
presenta dentro de la frase «la detección MODIS es FIEL a Coppola 2016a», y el perfil lo rotula
«Coppola 2016a Tabla 1». Eso es falso lo encienda quien lo encienda. (2) Si alguien lo enciende
por creerlo canónico, estaría metiendo un test de **BT absoluta**, que es exactamente la clase de
camino que A69 identifica como vulnerable al gradiente topográfico de los nevados. (3) Es distinto
de D22 (la compuerta `bt > t_bg + 3 K` dentro de los Tests 2 y 3), que **sí** está activa: acá el
camino entero es de BT y está apagado.

**Lo que esta D NO dice**: no propone tocar el código, porque no hay nada que apagar. Estado:
**ABIERTA, descrita, sin decisión**; la acción es documental (los rótulos del perfil y de
`CLAUDE.md`, que van con A45).

## D32: MIROVA publica la SUMA del VRP de todos los píxeles alertados de la pasada; nosotros publicamos un recorte (el cúmulo, y en banda I su núcleo). **ABIERTA (registrada S147, verificada con contexto limpio, gravedad 4; prioridad MEDIA, no es la palanca del 0,7)** S146/S147

**El fenómeno, primero.** Una anomalía térmica volcánica no ocupa un píxel: ocupa un puñado. El
lago de lava calienta su propio píxel y entibia a los vecinos, y una colada reciente se extiende
por el flanco. Cuánta energía se le atribuye al volcán depende entonces de una decisión que parece
menor y no lo es: cuántos de esos píxeles se suman al informar la pasada.

**Lo que hace MIROVA**, verificado renderizando las páginas a imagen (A95), no por la capa de texto:

> Campus et al. 2024, *Bull. Volcanol.* 86:25, página impresa 3, §Methodology, Ec. 1: *«the
> algorithm extracts the radiance of each alerted pixel ... and calculates the total MIR radiance
> ... by summing the contribution of each pixel»*, `L_MIRhot = Σ L_alert`.

> Campus et al. 2022, *Sensors* 22:1713, página impresa 7, §3.2: *«The NRT processing chain is made
> of 4 successive steps: (i) download; (ii) resampling; (iii) hot-spot detection and (iv)
> calculation of the VRP.»*

> Coppola et al. 2026, *Scientific Data*, página índice 4: *«All resampled pixels exhibiting
> anomalous thermal behavior within this area were retained for VRP calculation.»*

La tercera cita viene del conjunto de datos publicado, así que por sí sola no valdría para el canal
de tiempo casi real (A105). La segunda cierra esa objeción: la suma es el paso (iv) **de la cadena
de tiempo casi real**, dicho con esas palabras. Lo exclusivo del archivo es el umbral de VRP por
sensor y la clasificación por DBSCAN, y ninguno de los dos es la regla de suma.

**Lo nuestro**: `ENABLE_SUM_VRP_REPORTING = False`. El tablero publica `f5_core_vrp_mw` (el núcleo
del cúmulo) en banda I de VIIRS, y `primary_cluster.vrp_mw` en MODIS y VIIRS 750. Son **dos
recortes encadenados**: primero el cúmulo de 8 conexos, después el núcleo.

**Cuánto vale, medido** (verificador S147, 1.512 pares publicados, ventana 2026-03-01 a 2026-09-20
partida por #535, magnitud publicada calculada con node ejecutando el propio `index.html`, A97):

| | VIIRS 375 | VIIRS 750 |
|---|---|---|
| mediana de la razón, publicado | 0,706 | 0,572 a 0,725 según agregación |
| mediana de la razón, sumando | 0,783 | 0,642 |
| razón **agregada** (energía total) | 0,647 a **0,856** | 0,725 a **1,153** |

O sea que cierra el **26 %** de la brecha en VIIRS 375, y en VIIRS 750 **la pasa de largo**: el
17,4 % de los pares superaría 1,5 veces a MIROVA y el 7,3 % la superaría 10 veces.

**Por qué NO es la palanca del déficit 0,7, y esto es lo que más importa de esta D.** Estratificado
por volcán, la ganancia **no está donde está el déficit**. Láscar e Isluga, que son 538 de los
1.285 pares de VIIRS 375, se mueven +0,031 y +0,015 y se quedan en 0,56 y 0,62. En 5 de 11
volcanes el delta es exactamente 0,000, porque el record es de un solo píxel y la suma ya es el
núcleo. El que más gana, Puyehue Cordón Caulle, **ya estaba en paridad** (1,037) y pasaría a
sobreestimar un 72 % (1,719). Es la misma compensación entre volcanes que la rebaja S146 de A99.
El déficit de Láscar e Isluga hay que buscarlo en el **fondo** (D25) o en la detección.

**Tres cosas que hay que saber antes de intentar el A/B:**
1. **El camino ya está andado**: `ENABLE_SUM_VRP_REPORTING` existe desde S37 y persiste
   `vrp_mw_sum_active`. No hay que escribir el cálculo, sólo encender y reprocesar.
2. **Pero suma una lista truncada**: `anomaly_pixels` es un top 100 por VRP en los dos
   procesadores. Inmaterial en la población de hoy (mediana de la razón suma sobre escena 1,0000,
   97,0 % dentro del 2 %), pero en un reproceso eruptivo mordería.
3. **No toca la sobre-publicación**: la puerta de publicación usa `primary_cluster.vrp_mw` y
   `distance_class`, no la magnitud mostrada. Cambiar de núcleo a suma no abre ni cierra
   detecciones. Baja el riesgo de adoptarlo y baja también su premio.

**Dato que acota la divergencia**: el archivo de MIROVA (`VRP_GLOBAL_ARCHIVE_2025.csv`) trae `Npix`
y `Max_Dist`. En volcanes chilenos y pasadas nocturnas, la mediana de `Npix` es 3 en MODIS, 6 en
VIIRS 750 y 3 en VIIRS 375, con `Max_Dist` mediana de 1,4 a 1,9 km. O sea que «todos los píxeles
alertados de la caja de 50 por 50 km» es, en la práctica, **un puñado dentro de unos 2 km**: no es
una suma de escena. Y nuestro conjunto alertado es comparable al suyo (mediana 2 contra 2): lo que
difiere es **cuánto de él publicamos**. Eso da un criterio de aceptación que hoy no existe para
este frente: comparar nuestro `Npix` contra el de MIROVA, no sólo la razón de magnitud.

**Lo que esta D NO dice**: no dice que haya que encender la suma. La decisión no puede ser un
encendido uniforme (rompería VIIRS 750), y por sensor es legítimo mientras por volcán siga excluido
por MISSION. Estado: **ABIERTA, descrita, sin decisión**, prioridad media, por debajo de D25 y del
frente del Test 1.

**Consecuencia sobre las reglas**: rebaja la premisa de **A10** en `CLAUDE.md` (ver la marca ahí).
