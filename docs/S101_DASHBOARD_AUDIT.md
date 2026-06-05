# S101 — Auditoría del dashboard (3 vistas) + comparación por sensor

**Fecha**: 2026-06-05 · Pedido Nicolás (incongruencias + por qué el Diario no se parece
a MIROVA). Fuente de números: `experiments/_s99_audit/modis_diffuse/compare_by_sensor_magnitude.py`
+ inspección live de las 3 vistas (Chrome).

## INDEX (vista principal) — COHERENTE ✓
Tarjetas (última detección, magnitud baja 0.02–2.5 MW, dist al cráter, sensor, hora
local+UTC), tabla NRT (valores bajos VIIRS, gate de distancia OK), mapa. Los números
altos visibles ("500 MW", "695,431 MW") son texto del "Acerca de"/changelog y la leyenda
de bandas, NO magnitudes mostradas. La vista que el operador mira primero está bien.

## DIARIO (serie 90d) — 5 incongruencias

| # | Incongruencia | Causa | Fix |
|---|---|---|---|
| 1 | **MIROVA ref = 1 sola línea** (`buildDatasets`: `aggregateDailyMax` de TODOS los registros MIROVA sin separar sensor) vs nuestras 3 barras por sensor → comparación injusta | display | desglosar MIROVA por sensor (3 líneas) |
| 2 | **Barras nuestras ≫ MIROVA** (PCC MODIS 342, Copahue 38, Villarrica 25, Llaima 18) | frente sec³ + path D | **nadir-fijo** (en validación) |
| 3 | **"Max VRP" del header toma el artefacto** (Lastarria/Tupun "5.00 MW" = cap D9 de MODIS, no la señal real ~0.5) | display | usar máx de la señal real |
| 4 | **Toggle "Núcleo F5'" solo afecta VIIRS375** (MODIS/VIIRS750 muestran cluster crudo aunque diga "Núcleo") | display | aclarar/extender |
| 5 | **Grafica el MÁXIMO diario** (sensible a un pico aislado) en vez de la mediana | display | ofrecer mediana |

## MOSAICO
Comparte `buildDatasets` con el Diario → arrastra #1, #4, #5.

## Comparación por sensor (lo justo) — `compare_by_sensor_magnitude.py`
Ratio nuestro/MIROVA POR SENSOR (mediana global, 90d):

| Sensor | ratio | lectura |
|---|--:|---|
| MODIS | 2.79× | inflado (sec³ + path D) |
| VIIRS750 | 1.49× | inflado (sec³) |
| VIIRS375 | 2.16× | inflado (sec³); el ctxpeak curó la *mediana* per-record pero el *máximo* diario aún marca alto |

**Hallazgo clave**: los **TRES sensores** están inflados, no solo MODIS — coherente con
que el drift sec³ afecta los 3 (calibración S14 → MIROVA usa nadir-fijo en los 3). El
fix nadir-fijo acercaría los 3 a MIROVA. Casos extremos: Tupun/Villarrica VIIRS375
11–17× (máximo diario; la mediana está curada).

## Descargas TIF/KMZ — ARREGLADO (PR #351)
Los TIF/KMZ del índice apuntan a `../../mirova-tif-archive/` (sibling fuera del repo, no
publicado en GH Pages) → el botón "Descargar" fallaba con "archivo no disponible".
Ahora `archiveAvailable()` detecta el sitio público (github.io) y muestra **"solo local"**
(gris + tooltip + nota) en vez del link roto. En local (archivo montado) sigue
"Descargar". Verificado en preview.

## Plan
- **#2** se cura con el nadir-fijo (en validación, run 27022484062). No tocar display dos veces.
- **#1, #3, #4, #5** (display puro) → un único PR de dashboard DESPUÉS de adoptar nadir-fijo,
  sobre la magnitud ya curada. Replicar en las 3 vistas (S92 L5).
