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

**Referencias**: `experiments/127_path_d_tbg_calibration/`, `experiments/128_path_d_ab_audit/`, `experiments/130_r3_audit_independent_optC/`, `experiments/131_r2_pixel_level_optC/`.

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
| #1 | Test 1 K1 → `hot_mask` reportable | `process_*.py` nti_path_hot | sp426_5.txt:298: "discarded for further steps" — debe ser saturation mask |
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

### Hallazgo dist=0.84 km fijo Villarrica — METADATO no error

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

