# Handoff S40→S41 (cierre 2026-05-13)

**Estado al cierre**: Modelo operacional **S38+S39+S40+S41** adoptado en main.
Reproc final 30d con TODOS los fixes corriendo (run 25830992447). Pages
refresh pendiente cuando termine.

## Modelo operacional final (mirova_equivalent.yaml)

| Fix | Sesión | Flag |
|---|---|---|
| vent_anchored cluster selection | S38 | `enable_vent_anchored_clustering: true` |
| H8 pixel-level distance filter | S38 | `enable_pixel_level_distance_filter: true` |
| D4 per-volcano (Lascar+Lastarria) | S39 | `enable_test1_lbg_global: true` + field per-vol |
| Retirar bt_path_hot | S40 | `enable_bt_path_hot: false` |
| Sanity cap pc.vrp_mw (50k MW) | S41 | hardcoded en store.py |

## Métricas REALES con criterio correcto (window 15d 2026-04-27→05-11)

Con cross-match contra MIROVA CSV consolidado (Mirova-v1 scraper):
- TP = nuestro `vrp>0` (pc.vrp_mw filtered) + MIROVA `Tipo_Registro=ALERTA_TERMICA`
- FN = nuestro `vrp=0` + MIROVA `Tipo_Registro=ALERTA_TERMICA`
- FP = nuestro `vrp>0` + MIROVA `Tipo_Registro=FALSO_POSITIVO`
- (RUTINA y NULO se ignoran — son pasajes sin info significativa)

| Vol | TP | FN | FP | Precision | Recall |
|---|---|---|---|---|---|
| Lascar | 45 | 3 | 4 | 91.8% | 93.8% |
| PuyehueCordonCaulle | 14 | 0 | 0 | **100%** | **100%** |
| Isluga | 16 | 3 | 4 | 80.0% | 84.2% |
| Lastarria | 9 | 7 | 3 | 75.0% | 56.2% |
| Tupungatito | 2 | 6 | 1 | 66.7% | 25.0% |
| Planchón | 4 | 5 | 3 | 57.1% | 44.4% |
| Villarrica | 1 | 0 | 1 | 50.0% | 100% |
| **TOTAL** | **91** | **25** | **22** | **80.5%** | **78.4%** F1=79.5% |

## Lecciones críticas S40/S41

### Confusión audit RUTINA vs FALSO_POSITIVO

Mi audit inicial contó RUTINA como FP, dando precision 17% (falso). El doc
interno (`~memory/reference_mirova_csv_ground_truth.md`) ya documentaba:

> "Categorías (las dos que importan — ignorar RUTINA NULO):
> - ALERTA_TERMICA → TP real
> - FALSO_POSITIVO → detección lejana MIROVA descarta"

**Regla**: cuando cross-matching contra CSV consolidado, ignorar RUTINA y
NULO. Solo ALERTA_TERMICA cuenta para recall, FALSO_POSITIVO para FP.

### Confusión `record.vrp_mw` vs `primary_cluster.vrp_mw`

`record.vrp_mw` (campo raw) es la sum de TODOS los hot pixels detectados,
incluyendo pixels FP lejanos (Salar, lago, satélite). Inflado.
`primary_cluster.vrp_mw` es la sum del cluster seleccionado (vent_anchored
prioriza summit). El dashboard usa este via `mirovaEqVrp(r)`.

**Regla**: para auditorías externas, NUNCA usar `r.vrp_mw` directamente.
Usar `r.primary_cluster.vrp_mw` con guards de distance vs inner_radius_km.

## Bloque A — S41+ investigaciones pendientes

### A.1 Tupungatito recall 25% (6/8 alertas perdidas)
Pattern dominante: glaciar 5682m altitud, fumarola sub-pixel < threshold
absoluto. D4 fix per-vol DESCARTADO en Tupungatito (regresión en glaciar
combo S38 C.1). Posibles caminos:
- Lower threshold absoluto VIIRS 375m solo en Tupungatito
- Path adicional para sub-pixel extremo (< 0.1 MW MIROVA)
- O aceptar 25% recall (limitación física del sensor)

### A.2 Lastarria recall 56% (7/16 perdidas)
Volcán fumarólico permanente. D4 ON en Lastarria pero recall sigue bajo.
Investigar:
- ¿Falsos negativos por bt_sanity_k filter agresivo?
- ¿Pixels Lastarria tienen BT marginalmente sobre threshold pero no pasan
  el sanity check?

### A.3 Planchón-Peteroa recall 44% (5/9 perdidas)
Sub-pixel mismo patrón. Investigar.

### A.4 NdC al D4 per-vol (S40 pendiente)
Análisis S39 mostró que 2/3 alertas NdC son patrón D4 idéntico Lascar/
Lastarria. NO en A/B S39 actual. Agregar `lbg_global_compatible: true` a
NdC + reproc para validar.

### A.5 22 FPs persistentes (precision 80%)
Records con `pc.vrp > 0` y MIROVA `FALSO_POSITIVO`. Hipótesis:
- Clusters fumarólicos sub-pixel que detectamos pero MIROVA descarta por
  thresholding más estricto
- Investigar si están dentro de inner_radius (false summit positives) o
  fuera (clusters fronterizos)

## Bloque B — Verificación R8 dashboard cuando reproc termine

1. Pull `data/mirova_equivalent/`
2. `gh workflow run "Deploy GitHub Pages"`
3. Verificar URL pública con filtro **🆕 Solo post-S38** activado
4. Inspeccionar visualmente:
   - Volcán Lastarria: primary cerca del vent (no Salar)
   - PCC: primary en cráter (no lago lateral)
   - Tupungatito: vrp razonable (~0.3 MW si MIROVA reporta similar)
5. Inspeccionar caso Lastarria 2026-04-23 01:50: debe estar **excluido**
   por sanity cap pc (BT=566K garbage).

## Bloque C — Cosas que NO hay que tocar

- `enable_vent_anchored_clustering`: VALIDADO, NO desactivar
- `enable_pixel_level_distance_filter`: VALIDADO H8
- `enable_test1_lbg_global` + field per-vol: VALIDADO D4 selective
- `enable_bt_path_hot: false`: VALIDADO retirar (+1.7pp recall)
- `enable_test1_pixel_filter`: REFUTADO S33, mantener OFF
- `enable_eti_quadratic_scene` + secondpass + sum_vrp: REFUTADO S37, mantener OFF

## Bloque D — Errores metodológicos a evitar S42+

1. **NUNCA usar `record.vrp_mw` raw para auditorías**. Es sum scene-wide
   inflado por FP lejanos. Usar `primary_cluster.vrp_mw` filtered por
   distance.
2. **NUNCA contar RUTINA como FP**. Solo `FALSO_POSITIVO` es FP en CSV
   consolidado Mirova-v1.
3. **Cross-check múltiple antes de declarar adopción**: recall +
   precision + F1. Solo recall puede ser engañoso si precision tankea.
4. **Reportar max VRP vs MIROVA real ANTES de mostrar dashboard a Nicolás**.
   Si max nuestro > 100× MIROVA, hay bug oculto.

## URLs de referencia

- Dashboard publicado: https://mendozavolcanic.github.io/VRP-chile/
- Run reproc final S41: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/25830992447
- PR S41 sanity cap pc: https://github.com/MendozaVolcanic/VRP-chile/pull/35
- mirova-tif-archive: scraping cron 5min, 591+ filas TIFs disponibles
