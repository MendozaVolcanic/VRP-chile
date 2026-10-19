# Auditoría espacial A61: PCC, NOAA-21, 2026-10-10 05:54 UTC

Auditor con contexto limpio, worktree de sólo lectura `D:\vrp-trabajo\worktrees\s156-sombra-verif` (commit `0026eb816`).
Scripts en `D:\vrp-trabajo\temporales\s156_sombra\a61\scripts\`, salidas en `D:\vrp-trabajo\temporales\s156_sombra\a61\salidas\`,
descargas (índice de TIF, 85 GeoTIFF de PCC, 29 láminas PNG) en `D:\vrp-trabajo\temporales\s156_sombra\a61\bajados\`.
Nada se escribió en el worktree; no hubo clone ni pull de `mirova-tif-archive` (índice y TIF por raw fijado al commit
`3660cdfa`, PNG uno a uno por la API).

## Veredicto

| pregunta | veredicto | firmeza |
|---|---|---|
| ¿El cúmulo de la sombra en VIIRS 750 (1,886 MW, 4 píxeles) es el objeto que MIROVA alertó en VIIRS 750 (1,19 MW, 7,83 km)? | **MISMO OBJETO** | alta |
| ¿El cúmulo de K en VIIRS 375 (0,283 MW, 2 píxeles) es el objeto que MIROVA alertó en VIIRS 375 (0,39 MW, 7,73 km)? | **MISMO OBJETO** | alta, algo más que la de VIIRS 750 |

Ninguno de los dos es «otro lugar». El caso no se puede descartar por el eje espacial: el objeto que la sombra publica
y producción calla en VIIRS 750 es el mismo foco que MIROVA alertó, en el mismo lugar.

## 1. El fenómeno

En Puyehue Cordón Caulle hay un solo foco térmico persistente que MIROVA alerta todo el año: está junto a nuestro
punto de anclaje (`vent_lat/vent_lon` = -40.525499, -72.146137, el que usa `get_detection_anchor`, `pipeline/geo_utils.py:53`),
en el Cordón Caulle, unos 7,6 km al NNO del centro de la grilla de MIROVA, que está sobre el edificio del Puyehue
(`mirova_center` = -40.5903, -72.1187). Por eso los dos sistemas describen el mismo calor con números que parecen
incompatibles: MIROVA mide desde el centro de su grilla y dice «7,83 km»; nosotros medimos desde el ancla y decimos
«0,15 km». Es la misma mancha vista desde dos puntos de referencia distintos.

## 2. Posición de cada píxel (script `s02_geometria.py`, salida `s02_geometria.txt`)

Distancias en UTM 18S. El ancla está a **7,564 km** de `mirova_center` (dE -2,09 km, dN +7,27 km).

**Sombra, VIIRS 750** (`data/experimental_v2/PuyehueCordonCaulle.json`, `VIIRS_NOAA21_750`, 05:54):

| píxel | lat, lon | VRP MW | al ancla km | a `mirova_center` km | celdas de 0,75 km (E, N) | distancia cuantizada |
|---|---|---|---|---|---|---|
| px0 | -40.52393, -72.14780 | 0,811 | 0,22 | 7,77 | (-2,97, +9,93) | **7,830** |
| px1 | -40.52708, -72.14095 | 0,585 | 0,47 | 7,27 | (-2,21, +9,44) | 6,915 |
| px2 | -40.52571, -72.15190 | 0,415 | 0,49 | 7,71 | (-3,44, +9,68) | **7,830** |
| px3 | -40.52525, -72.13666 | 0,076 | 0,80 | 7,38 | (-1,71, +9,70) | 7,649 |
| centroide | -40.52549, -72.14433 | 1,886 | 0,15 | 7,52 | (-2,58, +9,69) | **7,830** |

Los otros 4 píxeles del record (12 a 14 km del centro, VRP 0) no son del cúmulo publicado.

**K, VIIRS 375** (`data/mirova_equivalent/PuyehueCordonCaulle.json`, `VIIRS_NOAA21`, 05:54): px0 (-40.52493, -72.14333),
0,283 MW, a 0,25 km del ancla y 7,55 km de `mirova_center`, celdas de 0,375 km (-4,93, +19,53), distancia cuantizada
**7,731**; el centroide (0,283 MW, 2 píxeles) está a 0,10 km del ancla. Los cuatro píxeles de K son los mismos cuatro
primeros de la sombra en VIIRS 375 (misma posición y temperatura).

**Lacolito: INDETERMINADO.** El repo no lo ubica de forma coherente: `docs/S99_AUDIT_SYNTHESIS.md:68` lo pone en el
ancla, `docs/HYPOTHESIS_LOG.md:1386` dice que el ancla es «el cono» y el lacolito está unos 6 km al SE, y
`docs/F60_VSROI_BRAINSTORM_S78.md:86` le da (-40.582, -72.131), a 1,3 km de `mirova_center`. Contra este último punto
nuestros píxeles están a 6,2 a 6,6 km. No lo resolví; no cambia el veredicto, porque la comparación es directa entre
nuestros píxeles y el foco de MIROVA.

## 3. ¿Daría un objeto en la posición de la sombra la `Distancia_km` 7,83? (D15)

Sí. En VIIRS 750 el único par de enteros con `√(i²+j²)·0,75 = 7,83` es (3, 10). El offset de px0, px2 y del centroide
respecto de `mirova_center` redondea exactamente a (-3, +10) celdas, o sea 7,830 km. En VIIRS 375, 7,73 admite (5, 20),
(8, 19) y (13, 16); px0 de K redondea a (-5, +20), 7,731 km.

**Esto por sí solo no identifica el objeto (A93, A107):** el radio admite ocho direcciones en VIIRS 750 y la grilla de
MIROVA no está fijada al metro (el centro del ráster de sus TIF queda a 0,19 km de `mirova_center` en VIIRS 750 y a
0,17 km en VIIRS 375, `s04`). La identificación sale de las secciones 4 y 5.

## 4. Control: qué es «7,83» para MIROVA en PCC (scripts `s03_control_pares.py` y `s04_tif_control.py`)

**Pares tabla CONS + record nuestro de la misma pasada** (`s03`, referencia `D:\vrp-trabajo\temporales\s156_audit\ref\registro_vrp_consolidado.csv`,
252 alertas VIIRS de PCC, 2026-01-11 a 2026-10-19). Con K (`mirova_equivalent`) hay 216 pares con cúmulo publicado:

| banda | n | nuestro centroide al ancla, mediana (p90) | dist. de nuestro centroide al centro MIROVA menos su `Distancia_km`, \|dif\| mediana (p90) | rumbo desde el centro, p10 a p90 | `Distancia_km` de MIROVA, mediana (p10 a p90) |
|---|---|---|---|---|---|
| V750 | 40 | 0,31 km (0,49) | 0,22 km (0,73) | 342 a 347° | 7,83 (7,65 a 8,55) |
| V375 | 176 | 0,23 km (0,56) | 0,32 km (0,61) | 342 a 347° | 8,04 (7,65 a 8,46) |

O sea: **«7,83 de MIROVA contra 0,15 nuestro» es la relación normal para el mismo objeto en PCC.** En toda la tabla,
las alertas VIIRS de PCC caen entre 7,65 y 8,55 km en 227 de 252 (`s07_rango_distancias.py`).

**El foco en el GeoTIFF de MIROVA** (`s04`, 85 alertas con TIF de la misma pasada, adquisición ±120 s, md5 no
ambiguo, antes del congelamiento del 22-sep; método y módulo `comun_tif.py` del estudio 1.4, PR #809). Foco = máximo
del exceso local dentro del anillo de su `Distancia_km`:

| banda | n | foco a ≤ 1,5 km del ancla | z del foco, mediana | nulo (mismo disco girado 11 ángulos), mediana de máximos | nuestro centroide (K) al foco de MIROVA, mediana; ≤ 1 km |
|---|---|---|---|---|---|
| V750 | 16 | 15 de 16 | 7,5 | 2,5 | 0,56 km; 15 de 16 |
| V375 | 69 | 61 de 69 | 10,6 | 3,2 | 0,46 km; 60 de 67 |

**Las ocho veces que MIROVA dijo exactamente 7,83 km en VIIRS 750 con TIF** (`s06_v750_celda_783.py`, parte a), su foco
fue la celda (-40.52337, -72.1459) en 6 y la vecina (-40.52337, -72.1369) en 2. **El píxel más energético de la sombra
del 10-oct (px0) está a 0,17 km de la primera** y el centroide a 0,27 km: dentro de la misma celda de 0,75 km.

## 5. La miniatura de MIROVA de esa pasada (scripts `s05_miniaturas.py` y `s06_v750_celda_783.py`)

No hay TIF del 10-oct (congelados desde el 22-sep). Usé las láminas «Latest10NTI» del archivo:
`experiments/_s156_autoaudit/sombra/20261010_083116_VIIRS750_Latest10NTI.png` (VIIRS 750) y
`data/png/PuyehueCordonCaulle/20261010_081020_VIIRS375_Latest10NTI.png` (VIIRS 375). La celda 0 de las dos lleva la
cabecera «10-Oct-2026 05:54:02», ZEN 23°, AZI -81° y la leyenda VRP 1 MW (750) y 0,39 MW (375); nuestro record da
cenit 23,59° y acimut -80,45°. **Esa identificación de celda es lectura visual de la imagen, sin script.**

**Calibración de la georreferencia** (miniatura de 150 × 150 sobre el extent del TIF, contra el foco del TIF de la misma
pasada): VIIRS 750, 9 láminas con foco visible (z ≥ 10), corrimiento sistemático mediano dE +0,41, dN +0,38 km, módulo
mediano 0,56 km, máximo 0,83; VIIRS 375, 16 de 26 láminas con foco visible, corrimiento mediano 0,32 km, máximo 0,76.

**Resultado en la celda de las 05:54:02:**

| banda | máximo de toda la miniatura | distancia al píxel más energético nuestro | z en nuestro píxel | mismo punto girado (11 ángulos): mediana / máximo |
|---|---|---|---|---|
| V750 (sombra) | z 10,4 | 0,97 km sin corregir; **0,43 km** corregido por el corrimiento mediano | 8,1 | 1,3 / 7,4 |
| V375 (K) | z 18,3 | **0,59 km** | 18,3 | 0,5 / 3,9 |

El punto más caliente de toda la escena de 51 km que MIROVA dibujó para esa pasada cae sobre nuestros cúmulos, en las
dos bandas, dentro del error de calibración. En las otras nueve celdas de la lámina (otras pasadas), nuestro punto
tiene z entre 0,0 y 4,5 en VIIRS 750 (la celda 8 es la de las 06:18:02, recortada en blanco) y entre 0,2 y 7,3 en VIIRS 375: el calor estaba en esa pasada, no es un rasgo fijo
del dibujo. En VIIRS 750, la miniatura corregida queda a 0,34 km de la celda que MIROVA informa como «7,83» en sus TIF.

## 6. Qué tan firme es, y qué no cubre

- **Firme**: tres líneas independientes coinciden. (i) La distancia cuantizada de nuestros píxeles reproduce exactamente
  7,83 y 7,73; (ii) en 85 alertas con TIF, el objeto de MIROVA en PCC a esa distancia es, salvo 9 casos, el foco junto
  a nuestro ancla, y «7,83» en VIIRS 750 es justamente la celda donde cae px0 de la sombra; (iii) en la miniatura de la
  misma pasada el máximo global está a 0,43 km (750) y 0,59 km (375) de nuestro píxel más energético, con nulo girado
  bajo.
- **Más débil en VIIRS 750 que en 375**: la calibración de miniaturas 750 descansa en 9 láminas con un corrimiento
  sistemático de 0,56 km, y en el nulo girado el máximo (7,4) se acerca al z de nuestro píxel (8,1). Lo que sostiene la
  conclusión en 750 es que el máximo de toda la celda está ahí, más la línea (ii).
- **A109**: la miniatura sale del mismo gránulo que usó nuestro detector. Para la pregunta de identidad («¿es el mismo
  objeto?») eso no sesga; no dice nada sobre si el objeto es volcánico.
- **Fuera de alcance**: no revisé por qué K calla en VIIRS 750 (lo verifica el otro agente) ni la magnitud. Anoto sin
  analizar: la sombra publica 1,886 MW donde MIROVA dice 1,19, y K 0,283 MW donde MIROVA dice 0,39 (D32: MIROVA suma
  todos los píxeles alertados).
- **No se resolvió**: la ubicación del lacolito (sección 2).
- Una primera corrida de `s06` importaba `s05` y lo re-ejecutaba entero (mismo resultado); se corrigió el import y se
  volvió a correr. La salida vigente es la del archivo actual.

## Scripts y salidas

| script | salida | qué mide |
|---|---|---|
| `scripts/s01_records.py` | `salidas/s01_records.txt` | los records de las dos pasadas de esa noche en los dos perfiles |
| `scripts/s02_geometria.py` | `salidas/s02_geometria.txt`, `.json` | posición de cada píxel, distancias, celdas de D15 |
| `scripts/s03_control_pares.py` | `salidas/s03_control_pares.txt`, `.json` | control de los 216 pares tabla + record |
| `scripts/s04_tif_control.py` | `salidas/s04_tif_control.txt`, `.json` | foco de MIROVA en 85 GeoTIFF de PCC |
| `scripts/s05_miniaturas.py` | `salidas/s05_miniaturas.txt`, `.json` | calibración de miniaturas y la celda 05:54:02 |
| `scripts/s06_v750_celda_783.py` | `salidas/s06_v750_celda_783.txt` | la celda de «7,83» y la calibración 750 con vector |
| `scripts/s07_rango_distancias.py` | `salidas/s07_rango_distancias.txt` | cuántas alertas VIIRS de PCC caen entre 7,65 y 8,55 km |

Todos se corren con `python -I <script> <worktree> <csv>` (ver el docstring de cada uno).
