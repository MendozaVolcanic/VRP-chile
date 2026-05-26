# MIROVA intra-radio gate faltante — hallazgo S81

**Fecha**: 2026-05-26
**Origen**: re-audit gap analysis con tags corregidos (S81 task #6).
**Evidencia**: `experiments/_s81_v2_out/REPORT_S81_GAP_V2.md` y CSVs.

## El hallazgo en 1 párrafo

VRP Chile produce ~2300 detecciones MODIS Tier A en 45 días que MIROVA
**procesó el mismo granule dentro del radio del volcán y decidió no
alertar** (publicó `RUTINA`, no `ALERTA_TERMICA` ni `FALSO_POSITIVO`).
Eso es 77% de los "FPs originales". MIROVA tiene **un gate intra-radio
que nosotros no aplicamos**. Es la fuente #1 de ruido del pipeline en
MODIS.

## Tabla por volcán (ventana 2026-03-17 → 2026-05-01)

| Volcán | MIROVA ALERTA MODIS | Nuestros MODIS | FP genuino (Subtipo B+C) | Ratio FP/MIROVA |
|---|---:|---:|---:|---:|
| Chaiten | 0 | 89 | 89 | ∞ |
| Copahue | 0 | 65 | 65 | ∞ |
| Llaima | 0 | 53 | 53 | ∞ |
| NdC | 0 | 67 | 67 | ∞ |
| PP | 0 | 89 | 89 | ∞ |
| PCC | 0 | 98 | 98 | ∞ |
| Tupungatito | 0 | 71 | 71 | ∞ |
| Villarrica | 0 | 78 | 78 | ∞ |
| Isluga | 0 | 72 | 72 | ∞ |
| Lastarria | 0 | 76 | 76 | ∞ |
| **Lascar** | **26** | **57** | **31** | **1.19** |

**Lectura geofísica**: 10/11 Tier A tienen 0 alertas MIROVA MODIS en la
ventana. Lascar es el único calibrado (recall 88%, precision 46%). Los
otros 10 son escenas donde MIROVA decidió "no hay nada aquí" pero
nosotros gritamos ~70-100 veces cada uno.

## Mecanismos candidatos del gate intra-radio MIROVA

### Candidato 1 — N·σ MODIS según Coppola 2016a Tabla 1

Coppola 2016a Tabla 1 declara los thresholds N·σ MODIS:
- **5σ summit** (ROI1, cerca del vent)
- **10σ scene** (ROI2, ROI más amplio)
- **15σ diurno** (luz solar)

Nuestro código actual (`pipeline/profiles/mirova_equivalent.yaml`):
- `n_sigma_mir_summit=5.0` ✅ MIROVA literal
- `n_sigma_mir_scene=10.0` ✅ MIROVA literal
- `enable_dual_roi_bt=true` ✅

Pero entonces ¿por qué tenemos 2295 FPs intra-radio?

**Hipótesis**: el problema no es N·σ del path BT (Path A) — está bien.
El problema puede ser otro path. **Path D contextual** tiene `c1=0.003`
summit y `c1=0.010` scene (Coppola 2016a Tabla 2), pero su cap actual
de 5 MW (S71 mitigación D9) puede no ser suficiente. **Path C NTI
absoluto >-0.8** puede estar disparando en escenas sin background MIR
fuerte.

**Acción**: separar los FPs MODIS por path que los disparó. Si la
mayoría son Path D o Path C, ese path es donde MIROVA tiene un gate
adicional.

### Candidato 2 — NDVI / land-cover gate

MIROVA puede pre-filtrar pixels con NDVI alto (vegetación) que
producen hot signals térmicos crónicos por evapotranspiración nocturna
o por re-emisión de calor diurno almacenado. No tenemos NDVI integrado.

**Acción**: cross-check los FPs MODIS contra producto NDVI MOD13A2 o
Landsat. Si los FPs están concentrados en pixels con NDVI>0.3, el gate
es land-cover.

### Candidato 3 — Cluster mínimo MODIS ≥2 px

MIROVA puede requerir cluster contiguo ≥2 pixels MODIS (1 km cada uno)
para reportar. Single-pixel hot signals serían descartados como ruido.

Nuestro código permite single-pixel MODIS por defecto (excepto donde
`enable_single_pixel_sub_mw_mode` aplica, que es VIIRS-I 375m).

**Acción**: contar cuántos FPs MODIS son single-pixel. Si la mayoría
lo son, ese gate aplicaría.

### Candidato 4 — MOD14 active fire cross-check

NASA MOD14 publica un producto independiente "Active Fire" que
identifica fuegos. MIROVA puede consultar MOD14 y descartar pixels
flagged como fire. No tenemos integración.

**Acción**: cross-check los FPs MODIS contra MOD14. Si la mayoría
están flagged active fire, el gate es ése.

## Hallazgo secundario — divergencia inner_radius VIIRS375

64 casos Subtipo A (concordancia far) son casi todos VIIRS375:

| Volcán | Casos | Nuestra dist (km) | Nuestro inner_radius yaml |
|---|---:|---|---:|
| Isluga | 18 | 0.4-5.5 | 5 |
| Lastarria | 11 | varios | 3 |
| PlanchonPeteroa | 9 | varios | 3 |
| Lascar | 6 | varios | 5 |

Nosotros clasificamos esos como `summit` (dentro de inner_radius). MIROVA
tagged `FALSO_POSITIVO` → MIROVA los considera fuera del radio del
volcán. Implica que **MIROVA usa un radio efectivo más chico que nuestro
inner_radius yaml para VIIRS375**.

**Acción**: extraer del KMZ VIIRS375 oficial MIROVA el `roi_radius`
exacto por volcán y comparar con nuestro `inner_radius_km` yaml.
Probablemente nuestros valores son ~1-2 km más generosos que MIROVA.

## Plan de implementación F-S81-A reformulado

### Fase 1 — diagnóstico (3-4h)

1. Sobre los ~800 FPs MODIS Subtipo B+C identificados, clasificar por:
   - Path que disparó la detección (A/B/C/D).
   - n_pixels del cluster.
   - distance_class (summit/far).
   - vrp_mw range.
2. Cross-check 100 casos contra MOD14 active fire.
3. Cross-check 100 casos contra NDVI (MOD13A2).
4. Hallazgo: identificar el mecanismo dominante (path / cluster / NDVI / MOD14).

### Fase 2 — gate implementation (4-8h dependiendo del mecanismo)

Según diagnóstico Fase 1:
- Si es **Path D over-trigger**: subir cap_mw o agregar requisito de
  co-validación path-A.
- Si es **cluster single-pixel**: agregar `enable_single_pixel_mode` a
  MODIS análogo a VIIRS-I S77.
- Si es **NDVI**: integrar producto NDVI como pre-filter.
- Si es **MOD14**: integrar producto Active Fire como pre-filter.

### Fase 3 — A/B test + adopción (3-4h)

Workflow A/B baseline vs F-S81-A sobre 45d Tier A. Métricas:
- Precision MODIS (debería subir).
- Recall vs MIROVA ALERTA (debería mantenerse — Lascar único calibrado).
- FPs MODIS por volcán (debería caer a ~10-20 por volcán de 70-100).

**Estimado total F-S81-A**: 10-16h. Mayor payoff del proyecto en MODIS.

## Conexión con otras frentes

- **F46 (VRP_TIR drift)**: ortogonal — solo VIIRS-I.
- **F66 (hybrid bg kernel)**: ortogonal — VIIRS, no MODIS.
- **D9 cap path D**: relacionado si Fase 1 confirma Path D over-trigger.
- **Single-pixel mode S77**: relacionado si Fase 1 confirma cluster
  single-pixel issue. Reutilizar arquitectura.

## Archivos relevantes

- `experiments/_s81_gap_analysis_v2_correct_tags.py` — script re-audit
- `experiments/_s81_v2_out/REPORT_S81_GAP_V2.md` — report completo
- `experiments/_s81_v2_out/per_volcano_sensor.csv` — 33 filas (11 vol × 3 sensores)
- `experiments/_s81_v2_out/fp_genuine_all.csv` — 2768 FPs B+C
- `experiments/_s81_v2_out/subtipo_a_all.csv` — 64 concordancias far
- `memory/reference_mirova_csv_scraper_tags.md` — interpretación correcta tags

## Estado

**ABIERTO P0 reformulado.** Antes era hipótesis "incendios forestales que
MIROVA filtra". Ahora es **gate intra-radio MIROVA con mecanismo a
determinar** (Fase 1 diagnóstico). Mayor payoff potencial del proyecto
después de F46.
