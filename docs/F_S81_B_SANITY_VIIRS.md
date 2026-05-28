# Sanity F-S81-B intra-radio VIIRS

**Pregunta**: ¿Las ALERTAs VIIRS MIROVA caen dentro de `inner_radius_km` (gate intra-radio análogo a F-S81-A aplicable) o están dispersas hasta `radius_km=25` (gate mataría TPs reales)?

**Universo MIROVA** = CONS (latest_consolidado.csv) ∪ OCR (registro_vrp_ocr.csv)

**Totales**: 831 ALERTAs CONS + 501 ALERTAs OCR = **1332 ALERTAs Tier A**

## Umbrales de veredicto

- `GATE_OK`: ≤20% ALERTAs fuera de inner_radius (gate aplica sin perder TPs).
- `GATE_MATA_TPs`: ≥40% afuera (gate destruiría TPs reales — NO aplicar).
- `GATE_AMBIGUO`: entre 20-40% afuera.
- `INSUFICIENTE_DATA`: <5 ALERTAs.


## VIIRS-I 375m (`VIIRS375`)

| Volcán | inner_km | N tot | CONS | OCR | p50 | p95 | max | dentro | fuera | %fuera | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| PuyehueCordonCaulle | 20.0 | 164 | 102 | 62 | 7.73 | 8.55 | 12.11 | 164 | 0 | 0.0% | **GATE_OK** |
| Villarrica | 5.0 | 17 | 10 | 7 | 0.84 | 0.84 | 0.84 | 17 | 0 | 0.0% | **GATE_OK** |
| Lascar | 5.0 | 251 | 138 | 113 | 1.13 | 1.68 | 5.0 | 251 | 0 | 0.0% | **GATE_OK** |
| Copahue | 4.0 | 1 | 1 | 0 | 3.69 | 3.69 | 3.69 | 1 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| NevadosDeChillan | 5.0 | 5 | 4 | 1 | 0.38 | 4.28 | 4.28 | 5 | 0 | 0.0% | **GATE_OK** |
| Llaima | 5.0 | 3 | 1 | 2 | — | 1.88 | 1.88 | 3 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| Chaiten | 5.0 | 37 | 23 | 14 | 0.38 | 0.75 | 1.06 | 37 | 0 | 0.0% | **GATE_OK** |
| PlanchonPeteroa | 3.0 | 98 | 55 | 43 | 1.68 | 2.02 | 2.37 | 98 | 0 | 0.0% | **GATE_OK** |
| Lastarria | 3.0 | 182 | 104 | 78 | 1.45 | 2.52 | 2.7 | 182 | 0 | 0.0% | **GATE_OK** |
| Isluga | 5.0 | 143 | 85 | 58 | 0.53 | 1.13 | 3.09 | 143 | 0 | 0.0% | **GATE_OK** |
| Tupungatito | 7.0 | 110 | 82 | 28 | 5.1 | 5.41 | 6.55 | 110 | 0 | 0.0% | **GATE_OK** |
| **AGREGADO** | — | **1011** | — | — | — | — | — | **1011** | **0** | **0.0%** | **GATE_OK** |

## VIIRS-M 750m (`VIIRS`)

| Volcán | inner_km | N tot | CONS | OCR | p50 | p95 | max | dentro | fuera | %fuera | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| PuyehueCordonCaulle | 20.0 | 24 | 23 | 1 | 7.83 | 8.55 | 8.55 | 24 | 0 | 0.0% | **GATE_OK** |
| Villarrica | 5.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Lascar | 5.0 | 152 | 94 | 58 | 1.5 | 1.68 | 2.37 | 152 | 0 | 0.0% | **GATE_OK** |
| Copahue | 4.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| NevadosDeChillan | 5.0 | 1 | 1 | 0 | 3.35 | 3.35 | 3.35 | 1 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| Llaima | 5.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Chaiten | 5.0 | 1 | 1 | 0 | — | — | — | 1 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| PlanchonPeteroa | 3.0 | 3 | 3 | 0 | 2.37 | 2.37 | 2.37 | 3 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| Lastarria | 3.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Isluga | 5.0 | 19 | 18 | 1 | 0.75 | 1.06 | 3.18 | 19 | 0 | 0.0% | **GATE_OK** |
| Tupungatito | 7.0 | 10 | 10 | 0 | 4.7 | 5.41 | 5.41 | 10 | 0 | 0.0% | **GATE_OK** |
| **AGREGADO** | — | **210** | — | — | — | — | — | **210** | **0** | **0.0%** | **GATE_OK** |

## MODIS 1km (`MODIS`)

| Volcán | inner_km | N tot | CONS | OCR | p50 | p95 | max | dentro | fuera | %fuera | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| PuyehueCordonCaulle | 20.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Villarrica | 5.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Lascar | 5.0 | 107 | 75 | 32 | 1.0 | 2.0 | 2.24 | 107 | 0 | 0.0% | **GATE_OK** |
| Copahue | 4.0 | 1 | 0 | 1 | — | — | — | 1 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| NevadosDeChillan | 5.0 | 2 | 1 | 1 | 0.7 | 1.41 | 1.41 | 2 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| Llaima | 5.0 | 1 | 0 | 1 | — | — | — | 1 | 0 | 0.0% | **INSUFICIENTE_DATA** |
| Chaiten | 5.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| PlanchonPeteroa | 3.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Lastarria | 3.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Isluga | 5.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| Tupungatito | 7.0 | 0 | 0 | 0 | — | — | — | 0 | 0 | — | **INSUFICIENTE_DATA** |
| **AGREGADO** | — | **111** | — | — | — | — | — | **111** | **0** | **0.0%** | **GATE_OK** |

## Síntesis por volcán (VIIRS combinado: 375 + 750)

| Volcán | inner_km | N VIIRS tot | %fuera VIIRS | Veredicto VIIRS combinado |
|---|---:|---:|---:|---|
| PuyehueCordonCaulle | 20.0 | 188 | 0.0% | **GATE_OK** |
| Villarrica | 5.0 | 17 | 0.0% | **GATE_OK** |
| Lascar | 5.0 | 403 | 0.0% | **GATE_OK** |
| Copahue | 4.0 | 1 | 0.0% | **INSUFICIENTE_DATA** |
| NevadosDeChillan | 5.0 | 6 | 0.0% | **GATE_OK** |
| Llaima | 5.0 | 3 | 0.0% | **INSUFICIENTE_DATA** |
| Chaiten | 5.0 | 38 | 0.0% | **GATE_OK** |
| PlanchonPeteroa | 3.0 | 101 | 0.0% | **GATE_OK** |
| Lastarria | 3.0 | 182 | 0.0% | **GATE_OK** |
| Isluga | 5.0 | 162 | 0.0% | **GATE_OK** |
| Tupungatito | 7.0 | 120 | 0.0% | **GATE_OK** |

## Conclusión y decisión (S84, datos)

**Veredicto agregado los 3 sensores: `GATE_OK` al 0.0% afuera.**

- VIIRS-I 375m: 1011/1011 dentro inner_radius (100%).
- VIIRS-M 750m: 210/210 dentro inner_radius (100%).
- MODIS 1km: 111/111 dentro inner_radius (100%).
- **Total Tier A: 1332/1332 ALERTAs MIROVA dentro de inner_radius (cero excepciones).**

### Interpretación física

MIROVA publica ALERTAs únicamente dentro del cono caliente per-volcán definido por
el `inner_radius_km` del KMZ. El radio NO es nuestro parámetro: es la geometría
operacional MIROVA, calibrada per-volcán al rango físico real del edificio
(Lascar 5 km, PCC 20 km lacolito, Lastarria 3 km compacto, Tupungatito 7 km
para absorber offset 3 km SE A24, Villarrica 5 km para idiosincrasia 0.84 km A13).

### Decisión

**F-S81-B (VIIRS intra-radio) está empíricamente justificado** (pendiente validar
en próxima sesión post-S84 con el plan de adopción F-S81-A MODIS):

1. Si el audit S84 confirma adopción F-S81-A MODIS sin regresión → diseñar
   F-S81-B análogo para VIIRS-I y VIIRS-M (mismo helper `path_d_intra_radio.py`,
   flag separado `ENABLE_PATH_D_INTRA_RADIO_GATE_VIIRS` o reusar la misma con
   sensor-aware logic).
2. Antes de implementar F-S81-B medir cuántos `final_hotspot_source='eruption'`
   con `pc_dist > inner_radius` ocurren en VIIRS baseline. Si son significativos
   (paralelo al baseline MODIS = 232 R3 violators) → fix con alto impacto. Si
   son ~0 → no hace falta.

### Caveats

- El sanity midió "dónde MIROVA publica", no "dónde existe actividad térmica".
  MIROVA tiene su propio filtrado post-detección que probablemente descarta
  anomalías legítimamente no-volcánicas fuera del cono (incendios, salinas).
  Para el objetivo (1) "clon literal MIROVA" esto está alineado. Para
  objetivo (2) "herramienta independiente" la pregunta se reabre.
- Volcanes con N<5 (Copahue, NdC, Llaima, Chaiten VIIRS-M, PP VIIRS-M, Lastarria
  VIIRS-M, Villarrica VIIRS-M) son `INSUFICIENTE_DATA`. Decisión per-vol debe
  esperar más data o usar el agregado del sensor.
