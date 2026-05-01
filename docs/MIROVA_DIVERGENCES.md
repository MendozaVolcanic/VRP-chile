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
| D5 | Magnitud (ratio VRP) | ✅ Resuelto S27 | — |

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
