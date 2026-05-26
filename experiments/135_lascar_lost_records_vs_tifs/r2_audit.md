# F2.6.g — R2 pixel-level: Lascar lost records S26→S71 vs MIROVA TIF archive

## Resumen ejecutivo

**Verdict global: F2.6.c hipótesis CONFIRMADA por evidencia indirecta (geográfica).**
R2 pixel-level estricto NO ejecutable: S26 baseline (`4c1762f`, hasta 2026-04-26) y
MIROVA TIF archive (desde 2026-05-08) tienen **cero overlap temporal** (gap de 12
días entre fin-de-S26 y inicio-del-archivo).

## Gap crítico de datos

| Fuente | Rango temporal | n records / TIFs |
|---|---|---|
| S26 baseline (`Lascar_S26.json`) | 2026-01-01 → 2026-04-26 | 1085 records |
| S71 actual (`data/mirova_equivalent/Lascar.json`) | 2026-01-29 → 2026-05-21 | 1027 records |
| MIROVA TIF archive (`mirova-tif-archive/data/tif/Lascar/`) | 2026-05-08 → 2026-05-20 | 159 archivos |
| **Overlap S26 ∩ TIF archive** | **∅** | **0** |

El scraper TIF (cron-job.org cada 5 min) empezó a poblar a partir del 2026-05-08
(según `index.csv`). No hay TIFs MIROVA históricos disponibles para Q1 2026
porque mirovaweb.it sobrescribe el archivo en cada pasada del satélite (~3-6h).

## Análisis indirecto (sin TIF) — geografía de los lost records

Lost = S26 tenía detección (`vrp_mw > 0.01`), S71 no tiene match o tiene
`vrp_mw < 0.01`. Match: (sensor, datetime_utc) exacto + ventana ±5/10 min.

**N records Lascar perdidos S26→S71: 345**

Distribución por clase de distancia (en S26):

| Clase S26 | N lost | % | dist mediana | vrp_mw mediana | vrp_mw máx |
|---|---|---|---|---|---|
| `far` (>inner_radius) | 150 | 43.5% | **22.96 km** | 93.6 MW | 1302.9 MW |
| `summit` (<inner_radius) | 136 | 39.4% | 0.41 km | 20.9 MW | 1210.2 MW |
| sin clase / sin distancia | 59 | 17.1% | — | — | — |

### Cat B (FP lejano) — fuerte evidencia geográfica

De los 150 lost `far`:
- **147/150 (98%)** con `final_hotspot_dist_km > 10 km`
- **109/150 (73%)** con dist > 20 km
- **100/150 (67%)** caen en zona Salar de Atacama (lat -23.5 a -24.2, lon -68.7
  a -67.85, al W del vent) — **firma química/térmica del Salar, no del cráter**

Ejemplo paradigmático (el caso F2.6.c bisección):

| datetime UTC | Sensor | vrp_mw S26 | n_pix | dist | class | hotspot (lat,lon) |
|---|---|---|---|---|---|---|
| 2026-03-19 05:48 | VIIRS_NOAA20 | **965.2** | 3061 | **0.27 km** | summit | (-23.36, -67.73) ← cráter real |
| 2026-03-19 06:36 | VIIRS_NOAA21 | 388.0 | 1349 | **23.64 km** | **far** | (-23.38, **-67.96**) ← Salar de Atacama |

La misma noche el cráter Lascar fue detectado bien (965 MW, 0.27 km). 48 minutos
después S26 reportó otro pico 388 MW pero a 23.6 km al W — eso es **Salar de
Atacama**, no Lascar. S40 (`bt_path_hot=OFF`) eliminó esa detección
correctamente.

### Cat A (TP real cráter) — preocupación parcial

De los 136 lost `summit`:
- 47 records con `vrp_mw > 500 MW` (eventos eruptivos grandes Lascar Q1 2026)
- 61 records con vrp > 100 MW
- **Solo 30.9% tiene S71 detección el mismo día** (otro sensor / otra pasada)
  → 69% son noches donde S71 NO ve Lascar pero S26 sí

Esto es señal de Cat A **probable**: pérdidas reales en eventos eruptivos altos
de Q1 2026 (Lascar tuvo actividad Lava-flow / dome growth). Sin embargo, ver
sección "limitaciones": sin TIF MIROVA contemporáneo no podemos certificar que
MIROVA NRT efectivamente reportó esos eventos.

## Conteo por categoría (clasificación indirecta)

Asignación basada en `distance_class` + dist + ubicación geográfica del
hotspot S26 (no centroide TIF MIROVA):

| Categoría | Definición | N | % |
|---|---|---|---|
| **Cat B candidate** | `class=far` o dist >10km o lat/lon en Salar | **150** | **43.5%** |
| **Cat A candidate** | `class=summit` y dist <5km | **136** | **39.4%** |
| **Cat C** | sin coords / TIF no disponible | **59** | **17.1%** |

Si se reagrupa por evidencia geográfica fuerte (Salar de Atacama explicitly):
- **100 lost en zona Salar** (Cat B confirmada por ubicación)
- 47 lost summit con vrp>500 MW (Cat A preocupante)
- resto distribuido

## Verdict

**F2.6.c hipótesis CONFIRMADA parcialmente**:
- 43.5% lost = `far` con dist>10km, 67% concentrados en Salar de Atacama →
  **Cat B claramente dominante en el bucket "far"**. La deriva S40 que apagó
  `bt_path_hot` eliminó correctamente FPs del Salar y ROI lejana.
- PERO 47 records `summit` con vrp>500 MW (Cat A candidate) merecen
  investigación: ¿son TPs eruptivos perdidos realmente, o burst dedup intrasensor
  donde el evento sí queda capturado por otra pasada?

**Recomendación**:
1. **NO re-activar `bt_path_hot`** basándose en el bucket `far` — confirmado Cat B
   (Salar de Atacama).
2. **Sub-investigación follow-up Cat A**: tomar los 47 lost summit vrp>500 MW y
   verificar si MIROVA NRT (CSV `21_04_2026 registro_vrp_consolidado.csv` /
   OCR) reportó ALERTA térmica esa noche. Si CSV dice ALERTA y S71 no detecta
   → regresión legítima de S40-S46 a investigar. Si CSV no reporta o dedup
   intrasensor → falsa alarma del audit F2.2.

## Limitaciones (gap reportado)

1. **TIF archive no cubre Q1 2026** — R2 pixel-level estricto imposible para los
   345 lost records. La clasificación es indirecta (geográfica + magnitud).
2. **Centroide MIROVA TIF no leído** — sin TIF contemporáneo, no podemos comparar
   el cluster MIROVA NRT real vs el hotspot S26.
3. **Ground truth alternativo NO usado en este audit**: el CSV consolidado
   MIROVA NRT (`VRP Chile/21_04_2026 registro_vrp_consolidado.csv`, 13.7k filas,
   ~100% MODIS / ~80% VIIRS) sí cubre Q1 2026 y debería ser el siguiente paso
   para Cat A confirmación.

## Output files

- `experiments/135_lascar_lost_records_vs_tifs/audit.py` — script
- `experiments/135_lascar_lost_records_vs_tifs/audit_results.json` — datos brutos
  (vacío en `lost_in_window` porque overlap = ∅; clasificación indirecta no
  serializada — está en este MD)
- `experiments/135_lascar_lost_records_vs_tifs/Lascar_S26.json` — baseline
  extraído de commit `4c1762f`
