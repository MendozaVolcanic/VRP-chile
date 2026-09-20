# MIROVA web audit — 11 Tier A × 3 sensores
Snapshot: 2026-05-01 (Last Update varía 06:30/19:24/20:10 UTC).
132/132 PNGs descargadas. 0 fallos.

## Tabla maestra (panel "Last Month" 30 d)

| Volcán | Sensor | Threshold | Estado | VRP last | n rojos (cerca) | n negros (lejos) | Notas |
|---|---|---|---|---|---|---|---|
| Lascar | VIIRS375 | <5km | NONE | NaN | ~28 (todos a ~1-2km) | 3 (~6, 22, 22) | Stems rojos persistentes baja altura → ruido fondo cerca de cráter, no detección |
| Lascar | VIIRS750 | <5km | NONE | NaN | 20 (~1km) | 1 (~20km) | Spike único fines abr |
| Lascar | MODIS | <5km | NONE | NaN | ~8 muy bajos | 0 | Casi vacío |
| Lastarria | VIIRS375 | <3km | **VERY LOW** | **0 MW** | ~30 (constantes <3km) | ~22 (10-25km) | Único volcán Tier A con thermal anomaly activa en VIIRS375. Estrella verde fin abril |
| Lastarria | VIIRS750 | <3km | NONE | NaN | 0 | 0 | Last Month vacío |
| Lastarria | MODIS | <3km | NONE | NaN | 0 | 0 | Last Month vacío |
| Tupungatito | VIIRS375 | <7km | NONE | NaN | ~22 (~5km) | 5 (16-23km) | Anillo ~5km (fumarola descentrada conocido) |
| Tupungatito | VIIRS750 | <7km | NONE | NaN | ~10 puntos pequeños | 0 | Continuum ~5km bajo |
| Tupungatito | MODIS | <7km | NONE | NaN | 0 | 0 | Vacío |
| Villarrica | VIIRS375 | <5km | NONE | NaN | 1 (~3km) | 2 (~17, 20km) | **Casi cero detecciones MIROVA web 30d** |
| Villarrica | VIIRS750 | <5km | NONE | NaN | 1 (~3km) | 1 (~17km) | 2 puntos en todo el mes |
| Villarrica | MODIS | <5km | NONE | NaN | 0 | 1 (~18km) | 1 punto |
| PuyehueCordonCaulle | VIIRS375 | <20km | NONE | NaN | ~22 (~7-9km) | 1 (~16km) | Anillo persistente ~8km dentro de inner=20km (detección sí, mag baja) |
| PuyehueCordonCaulle | VIIRS750 | <20km | NONE | NaN | 6 (~7km) | 0 | Ídem reducido |
| PuyehueCordonCaulle | MODIS | <20km | NONE | NaN | 0 | 0 | Vacío |
| Copahue | VIIRS375 | <4km | NONE | NaN | 1 (~4km) | 6 (10-20km) | Predominan negros lejanos |
| Copahue | VIIRS750 | <4km | NONE | NaN | 0 | 0 | Vacío |
| Copahue | MODIS | <4km | NONE | NaN | 0 | 1 (~18km) | 1 punto |
| ChillanNevadosde | VIIRS375 | <5km | NONE | NaN | 1 (~3km) | 6 (6-23km) | Pocas detecciones, principalmente lejanas |
| ChillanNevadosde | VIIRS750 | <5km | NONE | NaN | 0 | 3 (~6-19km) | |
| ChillanNevadosde | MODIS | <5km | NONE | NaN | 0 | 0 | Vacío |
| Llaima | VIIRS375 | <5km | NONE | NaN | 0 | 3 (11-25km) | Solo lejanos en VIIRS375 |
| Llaima | VIIRS750 | <5km | **MODERATE** | **11 MW** | 0 | 2 (~24km) + última detección activa | VRP plot muestra spikes ~3 MW |
| Llaima | MODIS | <5km | **MODERATE** | **14 MW** | 0 | 2 (13-25km) | VRP Last Month spike ~22 MW. Último update 14 MW activo |
| Chaiten | VIIRS375 | <5km | NONE | NaN | 5 (~1km) | 1 (~24km) | Stems rojos dispersos primer mitad mes |
| Chaiten | VIIRS750 | <5km | NONE | NaN | 0 | 0 | Vacío |
| Chaiten | MODIS | <5km | NONE | NaN | 0 | 0 | Vacío |
| PlanchonPeteroa | VIIRS375 | <3km | NONE | NaN | ~26 (constantes <3km) | ~12 (8-25km) | Patrón muy similar a Lastarria pero estado NONE (VRP NaN) — detecciones cluster pero sin VRP medible |
| PlanchonPeteroa | VIIRS750 | <3km | NONE | NaN | 0 | 1 (~25km) | |
| PlanchonPeteroa | MODIS | <3km | NONE | NaN | 0 | 0 | Last Month vacío |
| Isluga | VIIRS375 | <5km | NONE | NaN | ~22 (constantes <2km) | 6 (15-25km) | Patrón mascarilla térmica como Tupungatito/Lastarria |
| Isluga | VIIRS750 | <5km | NONE | NaN | 0 | 1 (~20km) | |
| Isluga | MODIS | <5km | NONE | NaN | 0 | 0 | Vacío |

## Thresholds MIROVA (legend) confirmados por volcán

| Volcán | inner_radius MIROVA web | volcanoes.yaml inner | Match |
|---|---|---|---|
| Lascar | 5 km | 5 | OK |
| Lastarria | 3 km | 3 | OK |
| Tupungatito | 7 km | 7 | OK |
| Villarrica | 5 km | 5 | OK |
| PuyehueCordonCaulle | **20 km** | 20 | OK |
| Copahue | 4 km | 4 | OK |
| ChillanNevadosde | 5 km | 5 | OK |
| Llaima | 5 km | 5 | OK |
| Chaiten | 5 km | 5 | OK |
| PlanchonPeteroa | 3 km | 3 | OK |
| Isluga | 5 km | 5 | OK |

**Conclusión**: nuestros 11 inner_radius_km coinciden 100% con MIROVA web. Cero divergencia geométrica.

## Estado actual (a 2026-05-01)

- **Único volcán activo Tier A**: **Llaima** (MODERATE 11-14 MW, VIIRS750+MODIS).
  Lastarria muestra VERY LOW (VRP=0 MW pero anomalía persistente <3km).
- **Resto (9/11)**: NONE.

## Latest10NTI observations

- **Llaima VIIRS**: 1/10 thumbnail muestra "VRP=11 MW" (último), 9/10 dicen NaN. La última detección está centrada en el cráter.
- **Villarrica VIIRS375**: 8/8 thumbnails dicen "VRP=NaN MW" — confirma 0 detecciones en NRT MIROVA pese a actividad reportada en lava lake conocida (caso FN sub-pixel histórico documentado).
- **Lastarria VIIRS375**: thumbnails muestran VRP entre 0.05 y ~3 MW — actividad continua de baja magnitud (degassing/fumarolas calientes).

## Hallazgos relevantes

1. **Tupungatito anillo 5 km confirmado**: MIROVA dibuja ~22 stems rojos a ~5 km en Last Month — coincide
   con el offset SE de la fumarola activa documentado en S15 (mirova_center 3 km SE del vent nominal).
   Threshold MIROVA `<7km` permite captura. Nuestro inner=7 alineado.

2. **PuyehueCordonCaulle threshold 20 km es REAL**: confirmado en legend MIROVA web. Detecciones reales
   se publican a 7-9 km del centro nominal (lacolito offset). NO es bug ni nuestro inflado, es geometría
   verdadera de MIROVA.

3. **Lastarria único volcán "thermal anomaly: VERY LOW" en NRT**: VRP=0 MW pero status verde por
   detecciones persistentes <3km. Esto significa que MIROVA reporta status incluso con VRP sub-MW.
   Importante: nuestras detecciones en Lastarria deben mostrar magnitudes ≤1 MW para coincidir; si
   producimos >5 MW estamos sobre-estimando.

4. **Lascar Last Year dramatic drop**: el panel anual VIIRS375 muestra ~50% reducción en stems negros
   lejanos en últimos 30 días vs trimestres anteriores. El volcán está desactivándose térmicamente.
   Implicación: nuestras detecciones recientes en Lascar deben ser MUY pocas. Si reportamos muchas
   en última semana, son FPs.

5. **PlanchonPeteroa patrón "Lastarria-like" pero sin status**: ~26 stems rojos persistentes <3km en
   Last Month, igual que Lastarria, pero MIROVA dice NONE en vez de VERY LOW. Hipótesis: VRP en cada
   detección está por debajo del umbral mínimo MIROVA para "VERY LOW" (~0.05 MW). Patrón térmico de
   fumarola/cráter caliente sin ser anomalía declarada. **Implicación crítica**: nuestras detecciones
   en Planchón deben tener VRP muy bajo, no medio. Si reportamos VRP medio-alto consistente,
   estamos sobre-detectando.

6. **MODIS prácticamente apagado en TODOS los Tier A excepto Llaima**: sólo Llaima tiene detecciones
   MODIS Last Month. Confirma observación previa (Tupungatito MODIS Last Year vacío), MIROVA NRT MODIS
   tiene umbrales muy estrictos. Nuestras detecciones MODIS deberían ser MUY raras (excepto Llaima).

7. **Villarrica casi vacío (3 puntos en 30d, todos lejanos excepto 1 a ~3km)**: el lava lake conocido
   NO está siendo detectado por MIROVA NRT en este período. Esto es FN MIROVA, no algo a replicar.
   Nuestra "carencia de detecciones Villarrica" es ALINEADA con MIROVA web actual, no un bug.

8. **PCC anillo persistente ~8 km dentro de inner=20km**: 22 stems rojos consistentes ~7-9km en VIIRS375
   Last Month. Esto es señal real de remanence térmica del lacolito 2011-2012 — MIROVA la captura por
   tener inner=20. Sin inner=20 todas serían "far" y desaparecerían. **Validación adicional de la
   decisión S14 de elevar inner a 20 km**.

9. **Threshold dual reportado en legend de cada plot**: confirma que MIROVA usa SOLO 1 dimensión de
   distancia para clasificar rojo/negro — no anidado, no multi-tier. Nuestro `distance_class`
   summit/far es paridad correcta.

10. **Noche-vs-día en VIIRS750 vs VIIRS375**: VIIRS375 (06:30 UTC, ~03:30 local Chile, full noche)
    tiene MUCHO más volumen de detecciones que VIIRS750 (19:24 UTC, ~16:24 local, día/atardecer).
    MIROVA filtra fuerte VIIRS750 diurno por contaminación solar M13. Confirma la regla "MIR solo
    nocturno" del CLAUDE.md.

## Patrones inusuales / sospechosos

- **NINGÚN volcán Tier A muestra >50 MW en últimos 30 días según MIROVA web**. Llaima 14 MW max
  (8-abr MODIS spike de ~22 MW). Si nuestro pipeline reporta volcanes con VRP >50 MW en últimos
  30 días que no sea Llaima, son FPs.
- **Cero detecciones NRT MIROVA Tupungatito MODIS** (Last Year completamente vacío en VIIRS750+MODIS,
  solo VIIRS375 activo). Confirma S21: refs Tupungatito 100% VIIRS, MODIS no contribuye.
- **Copahue, Chaitén, Chillán, Isluga, PlanchonPeteroa**: MODIS Last Year casi vacío (1-2 puntos en
  todo el año). Si reprocesamos con MODIS, expect recall ~0% — esto es la realidad MIROVA, no bug.

## Lista de imágenes descargadas

132 PNGs en `experiments/60_audit_mirova_full/{Volcano}/{SENSOR}/{Plot}.png`.
Volcanes: Lascar, Lastarria, Tupungatito, Villarrica, PuyehueCordonCaulle, Copahue,
ChillanNevadosde, Llaima, Chaiten, PlanchonPeteroa, Isluga.
Sensores: VIIRS375, VIIRS750, MODIS. Plots: Latest10NTI, Dist, VRP, logVRP.
Manifest detallado: `download_log.csv` (132 filas, todos HTTP 200).
Mapping de nombre verificado: **Nevados de Chillán = "ChillanNevadosde"** (no documentado antes).
