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

## Roadmap de cierre de divergencias

| ID | Divergencia | Estado | Próximo paso |
|---|---|---|---|
| D1 | 1 punto/pasada vs N pixels | Frontend ✓, data parcial | Cluster aggregation en pipeline |
| D2 | CSV ground truth ~70% VIIRS | Conocido | Re-scrape Mirova-v1 |
| D3 | FP explícito MIROVA vs nuestro `far` | Conocido | Posible categoría `mirova_fp_match` en records |
| D4 | Recall sub-pixel summit | A investigar | Estudio inner_radius o mecanismo MIROVA equivalente |
| D5 | Magnitud (ratio VRP) | ✅ Resuelto S27 | — |

## Referencias

- CSV consolidado: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
- Análisis S27: en este documento + `~memory/project_s27_mirova_literal_negativo.md`
- Hipótesis arquitecturales H_S27_1 a H_S27_5: ver memoria.
- Frontend fix S27: `frontend/index.html` toggle "Solo principal vs Todos los pixels".
