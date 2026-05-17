# S60 Audit B — Distribución magnitudes NEW vs OSF v2.5

**Fecha**: 2026-05-17
**Objetivo**: validar si la distribución de VRP en NEW (`enable_local_kernel_bg=true`) converge hacia la distribución de OSF v2.5 archive Villarrica, especialmente la mediana objetivo.
**Window NEW**: 2026-04-16 → 2026-05-15 (reproc S58).
**Referencia OSF**: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98 MB, no committed), 5211 filas Villarrica, 2001-2025.

## Distribución OSF v2.5 Villarrica por sensor (target histórico)

| Sensor | n | p10 | p25 | **median** | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| TODOS | 5211 | 0.248 | 0.829 | 3.342 | 13.937 | 46.319 | 70041.54 |
| VIIRS375 (I-band) | 1998 | 0.090 | 0.266 | **0.921** | 2.629 | 4.540 | 72.62 |
| VIIRS375 class=1 (curated) | 1817 | — | 0.280 | **1.056** | 2.813 | — | 53.02 |
| VIIRS375 class=0 (rejected) | 181 | — | 0.242 | 0.404 | 0.829 | — | 72.62 |
| VIIRS750 (M-band) | 659 | 6.366 | 9.482 | 22.075 | 57.949 | 98.504 | 10730.97 |
| MODIS | 2554 | 0.636 | 1.588 | 6.300 | 22.437 | 52.841 | 70041.54 |

> **Target operacional VIIRS375** = 1.056 MW (class=1 curado), no 0.921 MW global.
> El 0.92 MW del bloque arranque mezcla class=0 (rechazado por curación humana OSF).

## Distribución NEW vs LEGACY summit (≤5km) window 04-16/05-15

| Profile / sensor | n | p10 | p25 | **median** | p75 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NEW kernel-bg VIIRS375** | 111 | 0.498 | 1.110 | **2.098** | 3.309 | 4.086 | 7.37 |
| LEGACY median-ring VIIRS375 | 102 | 0.525 | 1.147 | 2.157 | 3.468 | 4.888 | 6.80 |
| NEW VIIRS750 | 30 | 0.448 | 1.703 | 5.159 | 6.994 | 9.401 | 14.96 |
| LEGACY VIIRS750 | 29 | 1.302 | 3.353 | 5.396 | 6.408 | 8.970 | 9.95 |
| NEW MODIS | 2 | — | — | 106.42 | 208.56 | — | 208.56 |
| LEGACY MODIS | 4 | — | 4.27 | 43.07 | 209.20 | — | 209.20 |

## Análisis

### VIIRS375 (sensor principal Villarrica)

| Métrica | OSF target | NEW | LEGACY | NEW vs target | NEW vs LEGACY |
|---|---:|---:|---:|---:|---:|
| median | 1.056 | 2.098 | 2.157 | **+99% sobre** | -2.7% mejor |
| p25 | 0.280 | 1.110 | 1.147 | +297% sobre | -3.2% mejor |
| p75 | 2.813 | 3.309 | 3.468 | +18% sobre | -4.6% mejor |
| p90 | — | 4.086 | 4.888 | — | -16% mejor |

**NEW mejora en TODAS las posiciones de la distribución vs LEGACY, pero la mejora es marginal
(2-16%). La inflación sistemática vs OSF persiste**: nuestra mediana summit duplica la del
histórico curado MIROVA. La cola alta (p75/p90) converge más que la mediana — el fix kernel
es más efectivo en outliers (caso paradigmático 2026-05-11) que en la distribución central.

### VIIRS750

LEGACY/NEW summit están por debajo del target OSF VIIRS750 (med 22 MW). Esperable: en
2026 Villarrica está en "Muy Bajo" sostenido sin lava lake observable, mientras OSF
histórico incluye episodios de alta actividad 2014-2018. No es bug del pipeline, es periodo.

### MODIS

n=2-4 demasiado bajo para conclusiones distribucionales. Los 2 records NEW con VRP=4.27
y 208.56 son outliers extremos — el de 208 MW es probable contaminación nube o pixel
bordeando salar. Se ignora para target.

## Veredicto S60-B

❌ **NEW no alcanza target OSF aún**. Mediana VIIRS375 summit sigue ~2× inflada (2.10 vs 1.06 MW).
✅ **NEW mejora marginal vs LEGACY** en toda la distribución (2-16%).
✅ **Cola alta converge mejor** (p75 NEW +18% vs target, p90 ya cercano a OSF p90 inferido).
⚠️ **Inflación sistemática persiste**: probable que el ring 5-25km todavía contamine en
   muchos noches no-paradigmáticas, o que la masa de detecciones NEW incluya pixels que
   OSF habría descartado en curación humana (class=0 OSF mediana 0.40 MW, muy por debajo de 1.06).

### Refinamientos pendientes (no bloquean adopción)

Si se quiere converger más a OSF median 1.06 MW VIIRS375:
- `kernel_size=5` (mean de 25 vecinos en lugar de 9) — más estabilidad estadística
- Percentile 25 del kernel en lugar de mean (más robusto a outliers vecinos calientes)
- O ambos en A/B controlado.

Pendiente para S61+ si Nicolás decide priorizarlo.

## Decisión adopción tentativa S60

NEW captura **idénticos TPs MIROVA NRT que LEGACY** (S60-A confirmó 4/5 = 100% ALERTA + 67% FP).
La mejora de calibración es real pero modesta, y el target OSF curado sigue lejos.

**Recomendación**: NO adoptar aún en `mirova_equivalent.yaml` operacional. Mantener flag
per-vol opt-in. Razones:
1. Mejora marginal vs LEGACY no justifica romper continuidad de la serie operacional.
2. NEW reduce magnitud caso paradigmático (18.8× → 1.61×) pero también empeora caso
   2026-05-14 (0.97× → 2.17×) — neto MIXTO en TPs MIROVA.
3. Inflación 2× sobre OSF target persiste — sugiere que el fix actual no es suficiente.

**Mejor camino**: investigar refinamientos (kernel_size=5, percentile p25) en S61+ antes
de adoptar. La task C (re-reproc window 2026-02) puede confirmar/refutar el patrón en los
3 casos paradigmáticos faltantes.
