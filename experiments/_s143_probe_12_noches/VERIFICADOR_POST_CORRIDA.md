# Verificador con contexto limpio: RESULTADO del probe S143 de las 12 noches

> Auditoría del resultado ya corrido (`resultado.json` + `RESULTADO.md`) contra el criterio
> pre-registrado (`README.md`) y los artefactos crudos de los runs 35257515864 y 35260023218.
> Recuento independiente, sin usar `analizar.py`: cargador propio, corredor de node propio que
> extrae el predicado de `frontend/index.html`, haversine propia y lectura propia de los CSV de
> referencia. Scripts del verificador en el scratchpad de la sesión (`verif/recuento.py`,
> `verif/atribucion.py`, `verif/negativos.py`, `verif/cota.py`, `verif/cota_anclaje.py`,
> `verif/costo.py`). No se modificó ningún archivo del repo salvo este informe.

## Veredicto

**SE SOSTIENE CON MATICES.** Los números son exactos y se reproducen uno por uno; los cinco
controles de instrumento cumplen; el mecanismo de la pérdida de S135 está evidenciado en los
diagnósticos y no supuesto; y la pregunta de atribución (máscara contra filtro) se puede separar y
se separa limpio. Lo que **no** se sostiene es la regla de decisión construida sobre la diferencia
11 contra 10: esa diferencia depende por completo de con qué campo se mide la posición del objeto
publicado, y con el campo que el propio dashboard declara oficial para esos records las tres
variantes literales empatan en 10 y el control cae debajo de su propio umbral de instrumento.

## Tabla de hallazgos

| # | gravedad | hallazgo | estado |
|---|---|---|---|
| H1 | **4** | El orden 10 / 11 / 12 no sobrevive al cambio de campo de posición. La cota se calcula sobre `primary_cluster.centroid`; para los records `test1_roi` la regla del proyecto (S106 / A84, comentario dentro de `frontend/index.html` en `latestDetection`) dice que la posición oficial del record es `final_hotspot` y que el `pc` de un record test1 es el footprint de la integral (arrastre topográfico A69), no la posición. Separación mediana entre ambos campos en las pasadas que publican: **1,06 km** en records `test1_roi` (máx 2,97), 0,00 en `ctx_cluster`. Recalculando la MISMA cota sobre `final_hotspot`: control **12 a 10**, `s135_d_sin_compuerta_ctx` **11 a 8**, `literal` **10 a 10**, `literal_sin_compuerta_ctx` **11 a 10**, `literal_t1_sin_filtro` **12 a 10**. Las tres literales empatan y el control queda bajo el umbral 2a (>= 11), o sea el probe se leería INCONCLUSO. El campo es heredado de S135 (`evaluar_ab.py:275-276` usa el mismo), así que no es error nuevo, pero la frase «la de menor costo al A/B» descansa entera en él. | CONFIRMADO |
| H2 | 3 | El titular omite que `literal`, el brazo ya pre-registrado, NO llega a la barra (10 de 12). La lectura impresa es la fila 4 («ambas recuperan»), pero la fila 1 falló y la fila 2 («`literal` < 11 y `literal_sin_compuerta_ctx` >= 11») también se cumple literalmente: las filas del README no son excluyentes y la precedencia la resolvió el código. Compatible en la práctica, pero el titular esconde que el brazo de hoy se queda a una noche. | CONFIRMADO |
| H3 | 3 | La fila 5 de la tabla pre-registrada no está implementada en `analizar.py`. La cadena es `rl -> (rc and rf) -> rc -> rf -> else`; no hay rama que mire si las pasadas con filtro del Test 1 «caen a ~0». Si hubieran caído a 0, el analizador igual habría impreso la fila 4. El dato observado es 47 a 32 (baja 32 %), y «~0» nunca se definió, así que probablemente no habría disparado; el fondo de la pregunta lo contesta H7 con datos, pero el instrumento no implementa su propio pre-registro. | CONFIRMADO |
| H4 | 3 | «Noches recuperadas» es monótona en la tasa de publicación, así que no es independiente del eje de costo. La noche cuenta si CUALQUIER pasada publica algo que pase la cota, sobre hasta 4 pasadas y contra cualquier distancia de MIROVA de esa noche. Pasadas que publican de las 41 `perdida`: `literal` 27, `literal_sin_compuerta_ctx` 33, `s135_d_sin_compuerta_ctx` 32, control 41, `literal_t1_sin_filtro` 41. Sobre las 61: 34 / 43 / 39 / 53 / 54. `literal_t1_sin_filtro` llega a 12 de 12 publicando en 54 de 61, cerca del brazo degenerado «todo publica» que el propio banco usa como control trivial de recall (P1 de `banco_paridad`). Su 12 de 12 no es evidencia de mecanismo. | CONFIRMADO |
| H5 | 3 | El costo en negativos no es el mismo objeto que publicaba el control, y el conteo esconde un salto de tamaño. De las 12 `neg_artefacto`, **sólo 1** (Isluga 2026-07-03) la publican las variantes en el mismo punto que el control; las otras caen a 0,9 a 5,9 km de distancia. En varias el objeto de la variante queda **más cerca del cráter** que el del control (PP 2026-08-18: 0,481 km contra 2,67; Lastarria 2026-06-15: 0,116 contra 2,595), que para el operador es peor, no mejor, y el conteo no lo ve. Y `literal_t1_sin_filtro` publica cúmulos de mediana 33 px / 0,314 MW en las `perdida` y mediana 14 px / 0,132 MW con máximo **75 px / 1,37 MW** en los negativos, contra mediana 1 px / 0,03 a 0,05 MW de todas las demás. El «12 contra 9» subestima la diferencia: es cambio de régimen, no de grado. El orden que usa la lectura no cambia, se refuerza. | CONFIRMADO |
| H6 | 2 | Los controles 2a, 2b y 4 son comprobaciones de reproducibilidad sobre una muestra elegida justamente por esa propiedad: las 61 pasadas se seleccionaron como pasadas donde el brazo D de S135 no publica, y 53 de ellas como pasadas donde A sí. «Control >= 11» y «`s135_d` <= 1» no pueden fallar por razones de mecanismo. Lo que sí verificaron, y conviene decirlo porque es más fuerte que el umbral pedido: el control publica **exactamente** las 53 seleccionadas y ninguna de las 8 `neg_quieta`; `s135_d` publica **0 de 61**. El código de hoy reproduce los dos brazos de S135 pasada por pasada. | CONFIRMADO |
| H7 | 2 | La cota es una diferencia de radios, no una distancia (A93; el propio `evaluar_ab.py` lo dice: es cota INFERIOR de la separación). En Planchón-Peteroa el `mirova_center` está a **2,021 km** del cráter, así que el anillo que pasa mide ~1,1 km de ancho y por él caben tanto un objeto en el cráter como uno corrido ~0,8 km hacia el centro de la grilla, según qué número dé MIROVA esa noche (2,02 el 06-22 y el 08-09; 1,35 y 1,22 las dos noches en disputa). El CSV no trae acimut. | CONFIRMADO |
| H8 | 2 | La muestra no tiene ninguna clase donde el brazo D publique: son «A publica y D no» (41 + 12) y «ninguno publica» (8). Una variante que perdiera algo que D conserva sería invisible para este probe. Tampoco hay noches fuera de las 12. | CONFIRMADO |
| H9 | 1 | La `neg_quieta` que publican las tres variantes literales es la misma pasada y el mismo objeto en las tres (Isluga 2026-08-13 04:54, 1 px, 0,037 MW, `ctx_cluster`, 3,97 km del ancla, dentro del inner de 5 km). O sea es atribuible al perfil `literal` (D22 + D25 + segundo pase condicionado + sin keep_peak), no a la manipulación de máscara ni de filtro. Es una publicación donde ni A ni D publicaban: nueva, chica, y la única de 8. | CONFIRMADO |

## Lo que comprobé que sí está bien

- **P1. Cada número del informe sale de los artefactos crudos.** Recuento independiente, 366 JSON:
  noches con cota 12 / 0 / 11 / 10 / 11 / 12; sin cota 12 en las cinco variantes que publican;
  `neg_artefacto` 12 / 0 / 7 / 6 / 9 / 12; `neg_quieta` 0 / 0 / 0 / 1 / 1 / 1; pasadas con filtro del
  Test 1 50 / 53 / 53 / 47 / 32 / 0. **Cero discrepancias** con `resultado.json`, incluida la tabla
  noche por noche.
- **P2. Las 12 noches son exactamente la lista `criterio1_detalle` del brazo D de S135**
  (`experiments/_s135_ab_d1d2/resultado_final.json`): Isluga 07-01, 07-16, 08-19; Lastarria 07-02,
  08-28; PP 06-22, 06-26, 07-24, 08-09, 08-24; Tupungatito 07-07, 08-01.
- **P3. El pre-registro es real.** `README.md`, `analizar.py`, `probe.py` y `pasadas.json` entraron
  en `b01b88154` (2026-09-17 15:13:24 -0300) y el primer run arrancó 15:13:33 local. `analizar.py`
  no se tocó después (su único commit es ese). El commit de resultados `548400413` agrega
  únicamente `resultado.json` y `RESULTADO.md`, nada más.
- **P4. Los dos runs corrieron código idéntico.** Lastarria en `b01b88154` y los otros tres en
  `845357692`; el diff entre ambos son sólo los JSON de `data/mirova_equivalent/` que dejó el cron
  NRT, ningún archivo de `pipeline/`, `profiles/` ni del probe. Duraciones reales (24 a 41 min por
  job), no verdes instantáneos.
- **P5. Comparabilidad pasada a pasada.** Mismos gránulos en las seis variantes en 61 de 61
  pasadas; `ok=true` en 366 de 366 salidas; un solo juego de flags efectivos por variante y
  coincide con el diseño declarado (el envoltorio de la máscara se llamó 1 vez por pasada en las
  dos `*_sin_compuerta_ctx` y 0 en las otras cuatro).
- **P6. El control de instrumento sí es del mismo mecanismo, y eso se ve en los diagnósticos, no en
  los conteos.** En `s135_d` el filtro contextual del Test 1 corrió en 53 pasadas y **vació la
  máscara en 53 de 53** (entraban 25 a 106 píxeles, salían 0). En el control corrió en 50 y dejó
  **exactamente 1 píxel en 50 de 50**: ese píxel es `keep_peak`. Al quitar la compuerta, la salida
  pasa a 1 a 14 píxeles. La cadena «el Test 1 encuentra la señal, la intersección con la máscara
  compuerteada se vacía, no se publica nada» es la real, y la diferencia entre control y D es
  `keep_peak`, como decía S135 (D19, A100).
- **P7. La atribución de la pregunta 3 se puede separar, y se separa.** Las **9** pasadas que
  `literal_sin_compuerta_ctx` gana sobre `literal` en las 61 (6 `perdida` y 3 `neg_artefacto`)
  tienen **todas** `final_hotspot_source = test1_roi` y **todas** con el filtro corriendo (su salida
  pasa de 0 a 1 o 2 píxeles). Cero pasadas perdidas. El confundido que avisaba el verificador previo
  (que la máscara apague el filtro por `only_test1_source`) **existe** en 12 de las 41 pasadas
  `perdida`, pero no produce ninguna de las ganancias: la única noche incremental (PP 2026-08-24) se
  gana en una pasada donde el filtro corrió (92 píxeles a 1). La máscara más grande tampoco produjo
  ninguna publicación nueva por la vía contextual pura: ninguna ganancia tiene fuente `ctx_cluster`.
- **P8. La cota nunca se apoyó en su propio escape.** El caso «sin dato de MIROVA o sin centroide,
  no se descarta la noche» no se usó en ninguna pasada publicante (0 de todas las variantes).
- **P9. El predicado es el del operador.** Lee un solo campo que el probe no le pasa,
  `_mirova_confirmed`, excluido a propósito y de forma uniforme en las seis variantes.

## Las dos noches que `literal` no recupera (pregunta 4)

**No son pérdidas de publicación: son fallas de la cota de mismo objeto.** `literal` publica en las
dos noches (por eso «sin cota» da 12 de 12 en todas las variantes que publican).

| noche | `literal` publica | ancla al cráter | radio desde `mirova_center` | MIROVA esa noche | cota |
|---|---|---|---|---|---|
| PP 2026-07-24 | 05:54 SNPP (`ctx_cluster`) | **0,249 km** | 2,111 km | 1,35 km (OCR, 05:54) | 0,761 |
| PP 2026-07-24 | 06:12 NOAA20 (`ctx_cluster`) | 0,498 km | 2,281 km | 1,35 km | 0,931 |
| PP 2026-08-24 | 05:36 NOAA21 (`ctx_cluster`) | **0,459 km** | 2,039 km | 1,22 km (OCR, 06:12) | 0,819 |
| PP 2026-08-24 | 06:12 SNPP (`ctx_cluster`) | 0,519 km | 2,285 km | 1,22 km | 1,065 |

O sea: lo que `literal` publica esas dos noches está **en el cráter**, a 0,25 a 0,52 km del ancla.
Lo que falla es el calce del radio contra la cifra de MIROVA, que esas dos noches apunta ~0,8 km más
cerca del centro de la grilla que en las noches de PP donde MIROVA informa 2,02 km (06-22 y 08-09,
que `literal` sí recupera con cotas de 0,016 a 0,30). Las variantes que sí las recuperan llegan con
objetos **más lejos** del cráter, no más cerca: en PP 08-24 06:30 el `pc` que pasa la cota es un
píxel solitario a **2,615 km del cráter** (el ancla del mismo record está a 0,0 km), y en PP 07-24
`literal_t1_sin_filtro` pasa con un cúmulo de 99 píxeles. Es el mismo efecto que H1: la cota no está
midiendo el objeto que el record declara como suyo.

## La lectura pre-registrada aplicada a estos números (pregunta 6)

La fila que imprimió el analizador (fila 4, «ambas recuperan, comparar costo») es defendible pero
incompleta, y la fila 2 se cumple igual de literalmente. La afirmación operativa que sí aguanta,
sobre los conteos y reforzada por H5, es que entre las dos candidatas **`literal_sin_compuerta_ctx`
cuesta menos** (9 + 1 publicaciones en negativos, objetos de 1 píxel) que `literal_t1_sin_filtro`
(12 + 1, cúmulos de hasta 75 píxeles y 1,37 MW). Lo que no aguanta es la premisa de la fila: que
«ambas recuperan >= 11» mientras `literal` se queda en 10, porque ese 11 contra 10 se da vuelta a un
empate en 10 con el campo de posición del propio dashboard (H1).

## Conclusiones habilitadas

1. El código de hoy **reproduce exactamente** los brazos A y D de S135 sobre estas 61 pasadas (53 de
   53 y 0 de 61). No hubo deriva de código entre S135 y S143.
2. El mecanismo de las 12 noches perdidas es el declarado: sin `keep_peak`, la intersección de los
   píxeles del Test 1 con la máscara contextual compuerteada **se vacía siempre** (53 de 53), y
   quitar la compuerta la deja con 1 a 14 píxeles.
3. **D22 + D25 solos (el brazo `literal`, el ya pre-registrado) recuperan 10 de las 12 noches** que
   perdió el brazo D de S135, y las 2 que no recupera las publica igual: fallan la cota, no la
   detección. Esta es la conclusión más robusta del probe porque es la única que no cambia al mover
   el campo de posición (10 con los dos campos).
4. La recuperación extra de `literal_sin_compuerta_ctx` sobre `literal` es atribuible **a la
   máscara** (los píxeles del Test 1 sobreviven la intersección), no a que el filtro se apague:
   9 de 9 ganancias con el filtro corriendo y fuente `test1_roi`, 0 pérdidas.
5. Entre las dos candidatas, la de menor costo en negativos es `literal_sin_compuerta_ctx`, y el
   margen es mayor que el que muestran los conteos (tamaño del cúmulo publicado).

## Conclusiones NO habilitadas

1. **«`literal_sin_compuerta_ctx` recupera 11 y `literal` 10, así que el brazo hay que cambiarlo.»**
   Esa diferencia es de una noche, en muestra, y desaparece (empate en 10) si la cota se mide sobre
   `final_hotspot`, que es lo que la regla del proyecto manda para records `test1_roi`. Antes de
   rearmar los brazos por este número, hay que decidir con cuál campo se mide y volver a correr el
   analizador; es barato, los artefactos ya están.
2. **«`literal_t1_sin_filtro` es el que más recupera, así que es el mejor candidato.»** Publica en 54
   de 61 pasadas, incluidas las 12 de 12 `neg_artefacto` con cúmulos de hasta 75 píxeles. Está cerca
   del brazo trivial «todo publica», donde el recall vale 1 por construcción.
3. **Cualquier tasa.** 61 pasadas, 12 noches en muestra (nacieron de que D las perdió), 4 volcanes de
   los 11 Tier A, un solo sensor (VIIRS 375) y una ventana de tres meses. El probe contesta «qué
   mecanismo», nunca «cuánto». En particular no se puede estimar sobre-publicación con 8 `neg_quieta`
   (2 por volcán).
4. **«Ninguna de estas variantes pierde nada.»** La muestra no contiene ni una pasada donde el brazo D
   publique, así que un falso negativo nuevo introducido por cualquiera de las variantes es
   estructuralmente invisible acá (H8). Eso sólo lo puede medir el A/B con su ventana completa.
5. **«Las noches recuperadas son el cráter.»** En el control las 41 pasadas `perdida` publican un
   objeto de **1 píxel** y 0,03 a 0,10 MW, que es el píxel que retiene `keep_peak` (D19, A100: daba
   paridad por accidente con un píxel a ~3 km del cráter). Que una variante «recupere la noche»
   significa que publica algo cuyo radio calza con el de MIROVA dentro de 0,55 km, no que haya
   detectado el cráter.
6. **Extrapolación a régimen focal.** Los cuatro volcanes son Isluga, Lastarria, Planchón-Peteroa y
   Tupungatito. No hay Láscar ni Villarrica ni Chaitén, y S135 midió 0 pérdidas en Láscar y PCC. La
   estratificación focal contra nevado que pide A83 no se puede hacer con esta muestra.

## Recomendación al que decida los brazos

No hace falta repetir el probe. Con los artefactos que ya están se puede cerrar H1 en minutos:
correr el mismo `analizar.py` con la posición tomada de `final_hotspot` para los records cuya fuente
sea `test1_roi` o `ctx_cluster` (la regla S106), y ver si la decisión cambia. Si con ese campo las
tres literales empatan en 10, la pregunta «¿hay que agregar el brazo de la máscara?» deja de tener
respuesta en este probe y pasa a depender del costo, donde `literal_sin_compuerta_ctx` gana igual.
