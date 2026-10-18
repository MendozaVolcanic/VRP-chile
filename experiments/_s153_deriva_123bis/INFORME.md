# Tarea 1.23 bis: de dónde sale la deriva de los 8 records MODIS

Sólo lectura sobre `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile` (rama `loop/activo`,
HEAD `656ff67bf`). No se editó, no se commiteó, no se despachó nada. Scripts y salidas en
`C:\Users\nmend\AppData\Local\Temp\claude\deriva_123bis\`.

## Respuesta corta

La deriva no la produjo un cambio de código en `process_modis.py`, sino **dos flags del perfil**: los
gates intra-radio de S84/S85, encendidos en `pipeline/profiles/mirova_equivalent.yaml` del
**2026-05-28 (04:44 UTC, `752aed06c` #226; 16:39 UTC, `60de1bb27` #229)** al **2026-07-01 20:46 UTC
(`92fc4412c`, #474, flip OFF de S118)**. Con el gate del segundo pase encendido, los píxeles que el
segundo pase recaptura **fuera del `inner_radius_km`** se borran
(`pipeline/second_pass_intra_radio.py:48`, llamado en `pipeline/process_modis.py:954`). El flip de #474
los apagó para lo que se escribiera desde ese momento, **pero no se reprocesó la historia**: los records
MODIS que se escribieron por última vez dentro de esa ventana siguen guardados con el gate puesto. Hoy,
con el gate apagado, el mismo gránulo da más píxeles.

Por eso un `git log -p` sobre `pipeline/process_modis.py` no lo encuentra: el código del gate existe desde
`eb68f8c4c` (#224, 2026-05-26) y sigue ahí; lo que cambió dos veces fue el valor del flag.

## Los 8 records

Todos producto `standard`, ninguno con Test 1, todos negativos limpios, ninguno protegido. Las cuentas
son de `n_anomalous_pixels`: guardado en `data/mirova_equivalent/` contra el brazo C de los probes 1.17
(run 38894508138, commit `d9b10482`) y 1.21 (runs 39033482528 y 39034846297, commit `e472c673`), que
dan lo mismo en los 8.

| volcán | sensor | pasada (UTC) | gránulo | guardado | hoy | última escritura del record |
|---|---|---|---|---|---|---|
| Chaitén | Aqua | 2026-03-06 07:00 | MYD021KM.A2026065.0700 | 37 | 67 | `3c37c6e79` 2026-06-06 (S102 nadir MODIS) |
| Chaitén | Aqua | 2026-04-28 07:55 | MYD021KM.A2026118.0755 | 275 | 405 | `a271cd552` 2026-06-01 (S97 refresh) |
| Copahue | Terra | 2026-03-06 01:35 | MOD021KM.A2026065.0135 | 2 | 4 | `3c37c6e79` 2026-06-06 |
| Isluga | Aqua | 2026-05-09 08:15 | MYD021KM.A2026129.0815 | 48 | 71 | `a271cd552` 2026-06-01 |
| Isluga | Aqua | 2026-05-18 07:25 | MYD021KM.A2026138.0725 | 99 | 143 | `3c37c6e79` 2026-06-06 |
| Isluga | Aqua | 2026-05-19 08:05 | MYD021KM.A2026139.0805 | 64 | 122 | `a271cd552` 2026-06-01 |
| Llaima | Terra | 2026-03-11 01:35 | MOD021KM.A2026070.0135 | 7 | 11 | `a271cd552` 2026-06-01 |
| Nevados de Chillán | Terra | 2026-03-19 01:50 | MOD021KM.A2026078.0150 | 11 | 19 | `3c37c6e79` 2026-06-06 |

Los 8 se escribieron por última vez con los gates encendidos. Los commits de escritura son promociones
de reproceso histórico (S97, S102), no el NRT. La última escritura se obtuvo por bisección sobre la
historia git del JSON de cada volcán (`historia_todos.py`, campos comparados: `n_anomalous_pixels`,
`diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`, `product_version`, `t_bg_k`). Estos records
no tienen `processed_utc` ni `regimen` (anteriores a #785), por eso hubo que ir a la historia git.

Lo que hace que justo estos 8 cambien también la etiqueta o la publicación (y no sólo el conteo) es
que los píxeles recapturados fuera del inner arman cúmulos o mueven el hotspot (en Copahue, Llaima y
NdC, el cúmulo guardado era de 0 MW y el de hoy queda a 6,9 a 20,7 km, según el verificador de la
1.17). Es la misma deriva que en los otros 239: sólo la consecuencia es distinta.

## La prueba (con predicciones que podían fallar)

Sobre los 470 records de la muestra de la 1.17 (`analisis.py`, `analisis2.py`):

1. **Régimen de escritura contra resultado.** Si la causa es el gate, sólo los records escritos con el
   gate encendido tienen que derivar, y ninguno puede salir hoy con **menos** píxeles (el gate sólo
   quita):

   | escritos | igual hoy | más píxeles hoy | menos |
   |---|---|---|---|
   | antes del gate (< 2026-05-28 04:44) | 2 | 0 | 0 |
   | con el gate encendido | 3 | **247** | 0 |
   | después del flip (≥ 2026-07-01 20:46) | 217 | 1 | 0 |

   La única excepción posterior al flip (Láscar Aqua 2026-09-03 07:10, 40 contra 41) está guardada como
   producto `nrt` y el probe corrió sobre Standard. Ninguno de los 470 sale hoy con menos píxeles.

2. **La aritmética del gate.** En los 56 records con gate encendido cuya versión previa al gate tenía
   el mismo primer pase que la guardada, el conteo de hoy debería ser exactamente «primer pase guardado
   + recaptura que tenía antes del gate». Se cumple en **49 de 56**. Ejemplos: Isluga 05-19,
   56 + 66 = 122 (guardado con gate: 56 + 8 = 64); Chaitén 04-28, 260 + 145 = 405 (guardado:
   260 + 15 = 275); Isluga 05-18, 85 + 58 = 143 (guardado: 85 + 13 = 98, luego 99). Los 7 que no cuadran
   tienen otra versión de código entremedio (SIN VERIFICAR cuál).

3. **Dónde el gate no muerde.** El gate sólo borra lo que cae fuera del inner. Los 3 records con gate
   encendido que salen iguales son uno sin recaptura (Copahue 2026-06-24, 1 píxel, 0 recapturados) y dos
   de Puyehue Cordón Caulle, el único volcán con `inner_radius_km` de 20 km (19 de 21 cambian allí,
   contra 100 % en los demás volcanes).

4. **Serie mensual del corpus** (`serie_recaptura.py`, HEAD, MODIS con píxeles, sin Villarrica): la
   mediana de `diag_n_second_pass_recapture` es 38 a 74 en toda la serie de 2025 (escrita por el
   backfill de S120, después del flip), **8 a 10 de enero a junio de 2026** y 54 a 75 de julio de
   2026 en adelante. No es estacional: marzo a junio de 2025 dan 60 a 65.

Por qué el segundo gate y no el primero: el gate del camino D (#226) también estuvo encendido, pero en 56
de 68 records comparables el primer pase no cambió y la diferencia la explica entera la recaptura. Qué
parte de los 12 restantes es el gate del camino D y qué parte es otro cambio de código: SIN VERIFICAR.

## Alcance en el corpus

`corpus.py` compara cada record de HEAD con el mismo record en la última versión del JSON antes del gate
y en la última antes del flip, en los 11 Tier A. Un record igual al de antes del flip y distinto (o
ausente) antes del gate se escribió con el gate encendido y no se volvió a escribir:

| familia | escritos con gate ON (con píxeles) | sin píxeles |
|---|---|---|
| MODIS | **3.231** | 19 |
| VIIRS 375 | 2.563 | 2.939 |
| VIIRS 750 | 1.953 | 4.521 |

- **MODIS**: 3.231 records, casi todos con observación de enero a junio de 2026, en 10 volcanes. En
  Villarrica, ninguno: su MODIS se reescribió entero después del flip. Con la tasa de la muestra
  (247 de 250) se espera que casi todos tengan menos píxeles guardados que los que da el código de hoy.
  Cuántos cambian también la etiqueta o la publicación: en la muestra son 8 de 250 con gate encendido;
  la muestra está estratificada, así que extrapolar eso (unos 100) es SIN VERIFICAR.
- **VIIRS**: el mismo gate está en `process_viirs.py:1380` y `process_viirs_mod.py:955`, y estaba
  encendido con el mismo flag, así que esos ~4.500 records VIIRS con píxeles también quedaron escritos con
  el gate. Pero en la serie mensual no se ve el salto (mediana de recaptura 1 todo el año, fracción
  recapturada sin quiebre en julio). Si derivan, y cuántos: SIN VERIFICAR (ningún probe reprocesó VIIRS).
- **Cómo se cuenta**: con `corpus.py` (foto antes del gate en `2026-05-28T04:44Z`, foto antes del flip
  en `2026-07-01T20:46Z`, HEAD). La bisección por record (`historia_todos.py`) da el commit exacto, pero
  tarda ~25 min para 470 records. Para records nuevos con `regimen` (#785) basta leer `codigo_sha`.

Consecuencia para las comparaciones: toda serie MODIS de píxeles, recaptura o magnitud de cúmulo que
cruce el 2026-07-01 **por fecha de observación** mezcla dos detectores (A104), y lo mismo pasa con
cualquier A/B que compare records guardados de enero a junio de 2026 contra un reproceso de hoy. La
afirmación de A85 de que la recaptura «volvió 4-6× al dato persistido» vale sólo para lo escrito desde el
flip: la historia de enero a junio de 2026 nunca se reprocesó.

## Corrida mínima para confirmarlo (diseñada, NO despachada)

Los 8 gránulos de la tabla, código de hoy desde un tag, tres brazos sobre el mismo L1B, reusando
`procesar_brazo` de `experiments/_s151_mxd03_etiquetas/probe_etiquetas.py`. Los flags se importan por
valor (`pipeline/process_modis.py:125-126`), así que se parchean los atributos del módulo
`pipeline.process_modis`, no `pipeline.profile`:

- **A**: `ENABLE_PATH_D_INTRA_RADIO_GATE = True` y `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = True`.
  Predicción: `n_anomalous_pixels` y `diag_n_second_pass_recapture` iguales a los guardados en los 8.
- **B**: sólo el gate del segundo pase. Predicción: igual que A (separa los dos gates).
- **C**: los dos apagados (producción). Control: tiene que dar los valores de la 1.17 (67, 405, 4, 71,
  143, 122, 11, 19).

Qué la refuta: que A no reproduzca lo guardado. Ojo con dos registros: Chaitén 04-28 e Isluga 05-09/05-19
y Llaima 03-11 se escribieron el 2026-06-01, antes de nadir fijo MODIS (#354, 2026-06-05). Ninguno
dispara el Test 1, que es lo que nadir fijo toca, así que la predicción se mantiene; si alguno de esos
cuatro no cuadra en A, esa es la primera sospecha. Costo: un job de unos 15 min, 24 corridas.

## Lo que queda SIN VERIFICAR

- La confirmación por reproceso (diseñada arriba, sin correr).
- Si los records VIIRS escritos en la ventana derivan.
- Qué explica los 7 de 56 en que la aritmética del gate no cuadra, y los 12 en que cambió el primer pase.
- Cuántas etiquetas o publicaciones cambiarían en el corpus completo si se reprocesara enero a junio de 2026.
