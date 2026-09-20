# Sexto verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v6)

**Veredicto: el instrumento sigue bien, pero el cambio central de la v6 rompe la medida. `R` no es el
nivel del instrumento: contiene el efecto que M2 quiere medir, y lo medí.** Sobre las mismas 681
pasadas del estrato hermano, con la ventana y la regla literales de la v6, poner nuestro `P` como
observado da `D = +0,0120` y poner un punto sorteado da `-0,0355`. La diferencia, **+0,0476**, es el
efecto del sitio, o sea la cantidad que el veredicto pretende estimar. Restarle `R` a `D` es restarle
la hipótesis a sí misma. Lo comprobé simulando: cuando el fenómeno está en los dos estratos por igual,
que es lo que cabe esperar de un foco permanente (categoría b de A54 vive justamente en las
`sin_info`), **el positivo no sale nunca**, ni siquiera con un efecto de `D = +0,27`, y la salida cae
entre "no se distingue" e INCONCLUSO. La primera es la que la tabla de §8 manda a apagar `keep_peak`.

Y la compuerta nueva **falla tal como está escrita**: con el pool literal de §5 ("pasadas sin patrón"),
`N1` da `D = -0,0984`, intervalo [-0,1162, -0,0809], muy fuera de la banda de ±0,05 que ella misma
exige. La medida quedaría INCONCLUSA antes de empezar.

Lo bueno: la ventana de 45 a 120 minutos **sí deja muestra** (601 pasadas, 349 noches de volcán, 6
volcanes con 20 noches o más, contra los mínimos de 30 y 3 que pide §7), y **sí baja el residuo a la
mitad**, de +0,0251 a +0,0120 con el intervalo ya incluyendo al cero. Lo que no hace es dejarlo en
cero, y la razón está medida abajo: la banda con que se eligió la ventana era un subconjunto
condicionado a la selección.

Documento verificado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v6 del 2026-09-19, rama `s144-prereg-keep-peak-direccion`, commit `32e9ca4b8`).

Mis scripts están fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v6\`:
`c6.py` (el instrumento con la regla literal de la v6: ventana 45 a 120 min, cruzada nocturna, sobre
el estrato hermano y sobre el pool de `N1`), `a6.py` (análisis e intervalos), `e6.py` (embudo de la
muestra del veredicto, sólo conteo), `v6sim.py` (simulación de la regla contra `R` con la
incertidumbre de `R`), `post6.py` (tramos), `par6.py` (el nulo del instrumento sobre las mismas
pasadas del estrato hermano), `isl6.py` (Isluga y el reparto obs contra ref por volcán), `s0_6.py` y
`s0b_6.py` (conteos de §0-bis), `g6.py` (pool del control G). Reusan `common3.py` y `pool3.pkl` de la
ronda 3, `base4.py` de la ronda 4 y `zc5.pkl`, `cruz5.pkl` y `embudo5.pkl` de la ronda 5. No modifiqué
ningún archivo del repo salvo este informe.

## Aviso de contaminación (léelo antes de tocar la v6)

1. Corrí el procedimiento completo de §5, con la regla literal de la v6, sobre las **1.289 pasadas con
   patrón, publicadas, fuera de Lastarria, con etiqueta `far_ref` o `sin_info`**, que son el estrato
   hermano y quedan **fuera de la muestra del veredicto**. De ahí salen `R` y casi todos los números
   de H1, H4 y H6.
2. Corrí el mismo procedimiento con un punto **sorteado** sobre esas mismas 681 pasadas (H1) y sobre
   las **3.614 pasadas sin patrón** del pool literal de `N1` (H3).
3. Evalué `Z` en **posiciones P** que pertenecen a pasadas de la muestra del veredicto, porque esas
   posiciones son sitios de referencia de otras pasadas. Nunca en el ráster que le corresponde a esa
   pasada, así que ningún `e_p` del veredicto quedó calculado.
4. Conté el embudo de la muestra del veredicto con la ventana de la v6 (601 de 1.113). Eso obliga a
   abrir los rásteres cruzados, pero **no evalué `Z` en el `P` de ninguna de esas pasadas** y **no
   clasifiqué ninguna pasada de M1**.

---

## Hallazgos nuevos (ordenados por gravedad)

### H1. `R` no es el nivel del instrumento: sobre las mismas pasadas, el nivel del instrumento es -0,0355 y `R` es +0,0120, o sea `R` ya contiene +0,048 del efecto que M2 mide

- **Dónde**: v6 l. 209-212 (`R`, residuo del instrumento, "da el nivel que el instrumento marca donde
  no se reclama nada"), l. 282-291 (la regla mide contra `R`), l. 293-297 (el porqué).
- **Evidencia** (`python c6.py && python par6.py`, todo sobre el estrato hermano, fuera del veredicto):

  | sobre las MISMAS 681 pasadas, ventana 45 a 120 min | n | `D` | IC 95 % | tasa obs | tasa ref |
  |---|---|---|---|---|---|
  | observado = **nuestro `P`** (esto es `R`) | 681 | **+0,0120** | [-0,0121, +0,0356] | 0,084 | 0,072 |
  | observado = **punto sorteado** del anillo | 681 | **-0,0355** | [-0,0530, -0,0176] | 0,037 | 0,072 |
  | diferencia (el efecto del sitio) | | **+0,0476** | | | |

  Por volcán, esa diferencia va de -0,061 (Isluga) a +0,137 (Tupungatito) y +0,131 (Cordón Caulle),
  con Llaima +0,081, Nevados de Chillán +0,081, Chaitén +0,070, Láscar +0,089, Planchón-Peteroa
  +0,043, Villarrica +0,041 y Copahue -0,029.
- **Qué pasa (el fenómeno y el mecanismo)**: el estrato hermano son pasadas donde nuestro pipeline
  publicó exactamente el mismo objeto que en la muestra del veredicto, con el mismo patrón y la misma
  publicación. Lo único distinto es qué escribió MIROVA esa noche. Si nuestro cúmulo lejano cae sobre
  algo que existe en el campo de radiancia, eso ocurre igual en las `sin_info`, que es donde A54 dice
  que vive la categoría b. La medición de arriba lo separa: de los +0,0120 de `R`, **-0,0355 es el
  suelo del propio instrumento y +0,0476 es el sitio**. La v6 lo dice ella misma dos veces, en l. 38-41
  y en l. 216-218: "un valor alto significaría que la hipótesis es cierta, no que el instrumento
  falle". Y a renglón seguido usa ese mismo estrato como el nivel contra el que se decide.
- **Cómo se ve en el resultado**: `D` en los negativos limpios sale parecido a `R`, el intervalo cae
  dentro de `R ± 0,05`, se escribe "no se distingue de los sitios donde publicamos otras noches", y la
  fila 1 de la tabla de §8 manda a pre-registrar una cota y re-evaluar el A/B de S143, o sea hacia
  apagar `keep_peak`. Pero lo que se restó no era el ruido del instrumento: era la señal.
- **Cómo reproducirlo**: `python c6.py && python par6.py`.
- **CONFIRMADO. Gravedad 5.**

### H2. Si el fenómeno está en los dos estratos por igual, el positivo es inalcanzable: simulado, 0 de 100 hasta un efecto de `D = +0,27`

- **Dónde**: v6 l. 282-291 (las dos salidas) y l. 320-325 (la tabla de §8).
- **Evidencia** (`python v6sim.py`, sección 3, con la estructura real de noches de la muestra del
  veredicto con la ventana de la v6 y con `R` remuestreado en cada repetición):

  | señal inyectada en los dos estratos | `D` medido | `R` medido | "cae sobre un exceso" | "no se distingue" | INCONCLUSO |
  |---|---|---|---|---|---|
  | 0,02 | +0,008 | +0,032 | **0 %** | 57 % | 43 % |
  | 0,05 | +0,037 | +0,062 | **0 %** | 45 % | 55 % |
  | 0,10 | +0,084 | +0,112 | **0 %** | 33 % | 67 % |
  | 0,20 | +0,180 | +0,212 | **0 %** | 17 % | 83 % |
  | 0,30 | +0,274 | +0,312 | **0 %** | 9 % | 91 % |

  Y al revés, con la señal sólo en la muestra del veredicto y `R` limpio, la regla sí funciona, aunque
  con menos potencia que la de la v5: `D = +0,064` da el positivo el 13 % de las veces, `+0,083` el
  56 % (la v5 daba 87 % a ese nivel) y `+0,131` el 100 %.
- **Qué pasa**: la única forma de que la regla entregue el positivo es que el efecto sea **más fuerte
  en los negativos limpios que en las `sin_info`**, y no hay razón física para eso. Un lago de lava,
  un campo fumarólico o un lacolito no saben qué fila publicó MIROVA esa noche. La regla, entonces, no
  puede decir que sí, y la salida se reparte entre la que apaga `keep_peak` y la que no mueve nada.
- **Cómo se ve en el resultado**: un "no se distingue" o un INCONCLUSO presentados como resultado de
  la medición, cuando son la consecuencia aritmética de restar un estrato que contiene el efecto.
- **Cómo reproducirlo**: `python v6sim.py`, sección 3.
- **CONFIRMADO. Gravedad 5.**

### H3. `N1` falla su propia compuerta con el pool que la v6 escribe: `D = -0,0984`, y el -0,0046 que cita viene de otro pool y de otra ventana

- **Dónde**: v6 l. 204-208 ("un punto sorteado del anillo ... en pasadas **sin patrón**, con imagen
  cruzada y los mismos 5 sitios de referencia ... `D` debe quedar dentro de ±0,05 (la quinta ronda
  midió -0,0046 sobre 654 pasadas). Si no, la medida es INCONCLUSA").
- **Evidencia** (`python c6.py && python a6.py`), todas con la ventana de 45 a 120 min:

  | lectura del pool de `N1` | n | `D` | IC 95 % | tasa obs | tasa ref |
  |---|---|---|---|---|---|
  | **literal**: todas las pasadas sin patrón (3.614 candidatas) | 1.857 | **-0,0984** | [-0,1162, -0,0809] | 0,055 | 0,153 |
  | sin patrón, fuera de Lastarria | 1.695 | -0,0783 | [-0,0945, -0,0608] | 0,041 | 0,119 |
  | sin patrón, sólo `neg_limpio`, fuera de Lastarria (el pool de la ronda 5) | 549 | -0,0233 | [-0,0458, -0,0032] | 0,044 | 0,067 |

  El pool literal incluye **416 pasadas con etiqueta `pos`**, o sea noches en que MIROVA alertó, donde
  los sitios de referencia se encienden (tasa ref 0,153 contra 0,055 del punto sorteado). El -0,0046
  de la ronda 5 se midió sobre el pool de la última fila y con la ventana de 15 minutos; con la ventana
  de la v6 ese mismo pool ya da -0,0233 con el intervalo fuera del cero.
- **Qué pasa**: la compuerta que la v6 crea para reemplazar a C1 y C2 se pone en rojo apenas se corre,
  y el documento declara que en ese caso "la medida es INCONCLUSA". O sea el resultado está fijado
  antes de mirar la muestra del veredicto. Y el pool no está definido: no dice si excluye Lastarria, si
  excluye las noches con alerta, ni si exige que el record exista. Tres implementadores honestos
  obtienen -0,098, -0,078 y -0,023, y sólo el tercero pasa.
- **Cómo se ve en el resultado**: "la medida es INCONCLUSA porque el nulo del instrumento dio -0,10",
  escrito como si fuera un problema del instrumento, cuando es la mezcla del pool.
- **Cómo reproducirlo**: `python c6.py && python a6.py`, bloque "N1".
- **CONFIRMADO. Gravedad 5.**

### H4. La ventana de 45 a 120 min no deja el residuo en cero: da +0,0120, porque la banda con que se eligió era un subconjunto condicionado a la selección

- **Dónde**: v6 l. 27-33 (el desglose por separación y la elección de la ventana), l. 177-180 ("la
  ventana ... está fijada por la medición de la quinta ronda"), l. 295-297 ("ese residuo debería quedar
  en cero").
- **Evidencia** (`python c6.py && python a6.py`, y el cruce de la selección en
  `python -c` sobre `cruz5.pkl` y `c6.pkl`):

  | | n | `D` | IC 95 % |
  |---|---|---|---|
  | `R` con la regla literal de la v6 (45 a 120 min) | **681** | **+0,0120** | [-0,0121, +0,0356] |
  | banda [45, 60) dentro de esa corrida | 278 | +0,0108 | [-0,0239, +0,0504] |
  | banda [60, 120] dentro de esa corrida | 403 | +0,0129 | [-0,0156, +0,0428] |

  El mecanismo está medido: de las 884 pasadas que la ronda 5 midió con "la más cercana a 15 min o
  más", **681 sobreviven** a la ventana y **300 de esas 681 cambian de pareja**, porque su pareja de
  la ronda 5 estaba a menos de 45 min. Esas 300 daban +0,0527 con la pareja vieja y **siguen dando
  +0,0327 con la pareja nueva**. Las 381 que ya tenían su pareja dentro de [45, 120] dan -0,0042. La
  suma ponderada es justo el +0,0120 observado.
- **Qué pasa (el porqué)**: la tabla de bandas de la ronda 5 no comparaba ventanas, comparaba
  **poblaciones**. Una pasada cuya pareja más cercana ya estaba a 50 minutos es una pasada de una
  noche con cierta constelación y cierto estado de escena; una pasada que tenía una pareja a 20
  minutos es otra cosa. Al convertir la banda en regla, entran las segundas con una pareja distinta, y
  traen consigo la mayor parte del residuo. Es el mismo error de leer un subconjunto seleccionado como
  si fuera el efecto de una intervención que la ronda 4 le encontró a la maldición del ganador.
- **Cómo se ve en el resultado**: el pre-registro anuncia que con esta ventana el residuo se va a
  cero, la corrida da +0,012, y como la regla decide contra `R` nadie lo nota, porque el número que
  falló es el mismo que después se usa como referencia.
- **Cómo reproducirlo**: `python c6.py && python a6.py`, y el bloque de comparación de selección.
- **CONFIRMADO. Gravedad 4.**

### H5. Los sitios de referencia no son una población equivalente: el 5,20 contra 5,66 es un promedio agrupado que se rompe por volcán, y con la ventana de la v6 ya no se sostiene ni agrupado

- **Dónde**: v6 l. 20-23 y l. 190-193 ("Qué sostiene la comparación ... son la misma población de
  sitios: un punto sorteado del anillo excede el umbral el 5,20 % de las veces y los sitios P el
  5,66 %").
- **Evidencia** (`python a6.py` y `python isl6.py`), tasa de exceso del punto sorteado contra la de los
  sitios `P`, siempre dentro de las mismas pasadas y los mismos rásteres:

  | corrida | punto sorteado | sitios `P` |
  |---|---|---|
  | ronda 5 tal como se publicó (pool `neg_limpio`, ventana 15 min) | 0,0520 | 0,0566 |
  | **mismo pool, ventana de la v6** | **0,0437** | **0,0670** |
  | pool literal de `N1` de la v6 | 0,0549 | **0,1534** |

  Estratificado por volcán en el pool literal, la razón entre las dos tasas es **27,8 en Láscar**
  (0,005 contra 0,136), **11,7 en Cordón Caulle** (0,022 contra 0,262), 2,7 en Villarrica, 2,6 en
  Planchón-Peteroa, 2,5 en Lastarria y 2,4 en Tupungatito. El caso extremo es Isluga en el estrato
  hermano: sus `zref` llegan a **32,2** con p90 = 12,1 mientras sus `zobs` no pasan de 5,92, así que
  con `zc = 6,07` la tasa observada es **0,000** y la de referencia **0,161**, y `D_Isluga = -0,161`.
- **Qué pasa (el fenómeno)**: los sitios de referencia son lugares donde **nuestro pipeline publica**.
  En los volcanes con un rasgo térmico real (lava de Láscar, lacolito de Cordón Caulle) el pipeline
  publica ahí una y otra vez, así que ese rasgo entra al denominador de todas las demás pasadas del
  mismo volcán. La separación de 1,5 km de §5 impide que entre **el propio** rasgo, no que entre
  **otro** rasgo real del mismo volcán. El resultado es que `r_p` está inflado justo en los volcanes
  donde vive la categoría b, y `d_p = e_p - r_p` queda sesgado hacia abajo, en contra de la hipótesis.
- **Cómo se ve en el resultado**: `D` agrupado bajo o negativo, tirado por dos o tres volcanes, y una
  lectura por volcán donde Isluga y Láscar contradicen al resto sin que nada lo explique.
- **Cómo reproducirlo**: `python a6.py` (bloques por volcán) y `python isl6.py`.
- **CONFIRMADO. Gravedad 4.**

### H6. `D` y `R` se miden sobre mezclas de volcanes distintas, y el residuo depende fuertemente del volcán: re-ponderar mueve `R` de +0,0120 a +0,0268

- **Dónde**: v6 l. 209-212 (`R` sobre `far_ref` y `sin_info`), l. 270-280 (el veredicto sobre
  `neg_limpio`, con remuestreo por noche de volcán estratificado por volcán).
- **Evidencia** (`python e6.py`, bloque de composición): la distancia L1 entre la composición por
  volcán de la muestra del veredicto y la del estrato hermano es **0,409**. Copahue pesa 0,189 en el
  veredicto y 0,135 en `R`; Planchón-Peteroa 0,077 contra 0,135; Isluga 0,017 contra 0,095;
  Tupungatito 0,052 contra 0,097. Y `R` por volcán va de **-0,161** (Isluga) a **+0,103** (Cordón
  Caulle) y **+0,102** (Tupungatito). Con eso:
  - `R` agrupado tal cual: **+0,0120**
  - `R` re-ponderado a la mezcla del veredicto: **+0,0268**
- **Qué pasa**: la v6 define con todo detalle el estimador de `D` (remuestreo por noche de volcán,
  estratificado por volcán, 2.000 réplicas, semilla y orden fijados) y para `R` dice solamente "con su
  intervalo". Dos implementaciones legítimas mueven el centro de la banda de equivalencia en 0,015, que
  es un tercio de la tolerancia entera, y ninguna de las dos está escrita.
- **Cómo se ve en el resultado**: dos personas con el mismo dato discuten si `D = +0,05` cae dentro o
  fuera de la banda.
- **Cómo reproducirlo**: `python e6.py`, último bloque.
- **CONFIRMADO. Gravedad 3.**

### H7. La tabla de §8 sigue decidiendo sobre C1 y C2, que §5 eliminó y degradó, y no menciona `N1`, que es la única compuerta nueva

- **Dónde**: v6 l. 325 ("| INCONCLUSO, o G o H fallan, o **C1 o C2** se salen de ±0,05 | | | informar y
  no mover nada |"), contra l. 34-41 (C1 se elimina, C2 deja de ser compuerta y pasa a llamarse `B`) y
  l. 204-208 (`N1` es la compuerta).
- **Evidencia**: `grep -n "C1\|C2" docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md` devuelve las líneas 35,
  38, 39, 219 y 325. Las cuatro primeras hablan de C1 y C2 en pasado, para explicar por qué se sacaron.
  La 325 los usa en presente como criterio de decisión.
- **Qué pasa**: la tabla que traduce el resultado en acción se quedó en la versión anterior. Un
  implementador que la lea al pie de la letra va a buscar dos controles que el documento borró, no va a
  encontrarlos, y va a tener que decidir por su cuenta qué hacer con `N1`.
- **Cómo se ve en el resultado**: una fila de la tabla de acción que no se puede evaluar, y la
  compuerta real sin ninguna fila que diga qué hacer cuando falla.
- **Cómo reproducirlo**: el `grep` de arriba.
- **CONFIRMADO. Gravedad 3.**

### H8. La regla contra `R` multiplica por veinticinco los INCONCLUSO del nulo y pierde un tercio de la potencia, sin ganar protección contra falsos positivos

- **Dónde**: v6 l. 282-291 (la regla) contra la simulación de la ronda 5, que sobre el nulo daba "no se
  distingue" 197 veces, INCONCLUSO 3 y el positivo 0, de 200.
- **Evidencia** (`python v6sim.py`, secciones 1, 2 y 4), con la estructura real de noches de la muestra
  de la v6 y `R` remuestreado en cada repetición:

  | | "cae sobre un exceso" | "no se distingue" | INCONCLUSO |
  |---|---|---|---|
  | nulo puro, regla de la v5 (ronda 5) | 0 % | 98,5 % | **1,5 %** |
  | nulo puro, regla de la v6 | **0 %** | 60,5 % | **39,5 %** |

  Potencia con señal sólo en el veredicto: `D = +0,035` da el positivo 0 % (equivalencia 50 %),
  `+0,064` lo da 13 %, `+0,083` lo da **56 %** (la v5 daba 87 %) y `+0,131` lo da 100 %. Y si `R` se
  estima con menos bloques, el ancho de su intervalo sube a 0,097 con n = 159 y a 0,186 con n = 40, y
  entonces el nulo entrega INCONCLUSO entre el 46 % y el 74 % de las veces según el sorteo de `R`, o
  sea la conclusión se lee del error de muestreo de `R` y no del dato del veredicto.
- **Qué pasa (el trade-off, dicho con todas sus letras)**: medir contra `R` compra protección contra
  declarar equivalencia sobre un residuo real, y paga con dos cosas: el umbral del positivo sube a
  `máx(0,05, R_hi)`, y el centro de la banda de equivalencia se vuelve una variable aleatoria. Con el
  `R` que esta muestra produce (ancho 0,048) el costo es un tercio de la potencia; con un `R` más
  ruidoso el veredicto pasa a depender de `R`. Lo que **no** se degrada es el lado del falso positivo:
  0 en 200 repeticiones del nulo.
- **Cómo se ve en el resultado**: un INCONCLUSO que la tabla de §8 manda a "informar y no mover nada",
  después de tres meses de corrida.
- **Cómo reproducirlo**: `python v6sim.py`, secciones 1, 2 y 4.
- **CONFIRMADO. Gravedad 3.**

### H9. No está dicho si `R ± 0,05` usa el punto o el intervalo, y es el mismo defecto que la ronda 5 marcó en C2

- **Dónde**: v6 l. 286-288 ("si el intervalo del 95 % de `D` queda entero dentro de **`R` ± 0,05**"),
  contra l. 284-286, que para el positivo sí dice "extremo superior del intervalo de `R`".
- **Evidencia**: la asimetría está en el texto. Para el positivo se nombra el extremo del intervalo de
  `R`; para la equivalencia se nombra `R` a secas. Con los números medidos, `R` vale +0,0120 y su
  intervalo [-0,0121, +0,0356]: leer "el punto" da la banda [-0,038, +0,062] y leer "el intervalo" da
  [-0,062, +0,086], que es un 46 % más ancha. `python v6sim.py` implementa la primera lectura.
- **Qué pasa**: es literalmente el hallazgo H4 de la ronda 5 ("el pre-registro no dice si el corte se
  aplica al estimador o al intervalo"), trasladado del control a la regla de decisión. La ronda 5 lo
  marcó, la v6 lo arregló en el positivo y lo dejó abierto en la equivalencia.
- **Cómo reproducirlo**: lectura de las líneas 284 a 288.
- **CONFIRMADO. Gravedad 2.**

### H10. Números de hecho que no reproducen, tres de ellos ya señalados por la ronda 5 y conservados

- **Dónde y evidencia**:

  | v6 dice | dónde | lo que mide mi corrida | script |
  |---|---|---|---|
  | "de **2.541** pasadas con patrón" | l. 32 | 2.999 sin exigir publicación, **2.627** exigiéndola (que es como §4 define patrón), 2.475 fuera de Lastarria. Ninguna da 2.541 | `s0_6.py` |
  | "**1.824** tienen cruzada a 15 min o más" | l. 32 | 1.902 con la lectura de misma noche sobre 2.627, 2.164 sobre 2.999; con filtro de usabilidad la ronda 5 midió 1.962 y 1.744 | `s0_6.py` |
  | "**1.594** a 45 min o más" | l. 33 | 1.667 y 1.895 sin usabilidad; **1.396** y **1.577** con usabilidad y ventana [45, 120]. Sin tope superior el conteo es degenerado (siempre hay otra pasada usable algún día) | `s0_6.py`, `s0b_6.py` |
  | control G "valida casi sólo Láscar (**42 de 43** pasadas)" | l. 226 | **52 pasadas**, 49 de Láscar y 3 de Villarrica, el 94 % de Láscar. El alcance declarado se sostiene, el conteo no | `g6.py` |
  | "`zc_punto` de Isluga ... su intervalo va de **2,50** a 7,69" | l. 337, §9 | el propio §4 l. 160 dice [**2,04**, 7,69], que es lo que reproduce `zc5.pkl`. El 2,50 es el valor viejo de la ronda 4 | `zc5.pkl` |

- **Qué pasa**: el 1.824 y el "42 de 43" ya estaban en el informe de la ronda 5 (H8 y el bloque
  VERIFICADO LIMPIO), y la v6 los conservó; el 1.594 es nuevo y tampoco reproduce; y el intervalo de
  Isluga quedó corregido en §4 y sin corregir en §9, así que el documento se contradice consigo mismo
  en la misma página. Es la tercera vez seguida que un número sobrevive a su propia refutación, que es
  exactamente lo que A95 describe.
- **Cómo reproducirlo**: los scripts de la columna derecha.
- **CONFIRMADO. Gravedad 2.**

### H11. Detalles que dejan dos implementaciones legítimas, o que están de más

- **El filtro diurno de §5 es redundante dada la ventana** (l. 173-176). Las tres pasadas de las 19:36
  UTC que la ronda 5 encontró estaban a 768 y 816 minutos de la pasada medida, así que el tope de 120
  minutos ya las saca. En mis corridas el estado `cruzada_diurna` no apareció ni una vez sobre 1.289
  más 3.614 pasadas. No hace daño, pero conviene decir que lo que las corta es la ventana.
- **"los mismos 5 sitios de referencia" de `N1`** (l. 206) no se puede implementar así: los sitios se
  derivan de `P_p` por la separación de 1,5 km, y en `N1` el observado es un punto sorteado, de modo que
  los sitios se re-derivan de ese punto. Yo implementé lo segundo, que es lo único coherente.
- **La zona donde las dos condiciones del veredicto se cumplen a la vez no se alcanza con este n**: la
  comprobé (`v6sim.py`, sección 6) y dio 0 de 300 repeticiones, porque exige que el intervalo de `D`
  mida menos de 0,026 y el ancho real es 0,041. O sea el orden de las dos condiciones no cambia nada
  hoy, pero el texto igual debería fijarlo, porque el ancho depende del n.
- **`zc_punto` se calibra en rásteres propios y se aplica en cruzados**, que la ronda 5 ya marcó
  (H14) y la v6 no declara.
- **El indicador binario sigue tirando a cero la mayoría de los `d_p`**: con la ventana de la v6, el
  **72,1 %** en el estrato hermano y el 63,0 % en el pool de `N1`.
- **CONFIRMADO (lectura del texto y medición). Gravedad 1.**

---

## VERIFICADO LIMPIO

Lo que la v6 arregló y lo que medí y quedó en pie:

- **La ventana deja muestra de sobra, y esa era la pregunta 2.** Con la regla literal de la v6, la
  muestra del veredicto pasa de 1.113 candidatas a **601 pasadas** (se pierden 428 porque no hay pareja
  en [45, 120] y 84 porque la pareja no es usable), repartidas en **349 noches de volcán** contra el
  mínimo de 30 que pide §7. Llegan a 20 noches **6 volcanes** (Copahue 66, Llaima 63, Villarrica 55,
  Chaitén 52, Nevados de Chillán 38, Planchón-Peteroa 27) contra el mínimo de 3; quedan fuera
  Tupungatito 18, Cordón Caulle 17, Láscar 7 e Isluga 6. **Sí siguen habiendo 3 volcanes con 20
  noches, y con holgura.** Respecto de la regla de la v5 (711 pasadas, 378 noches, los mismos 6
  volcanes) la ventana cuesta el 15 % de la muestra, así que "cuesta poco" es justo, aunque el número
  con que el documento lo justifica no sea el que corresponde (H10).
- **Los 5 sitios de referencia se consiguen siempre**: `n_ref = 5` en las 1.113 candidatas, ninguna
  queda con menos de 3.
- **La ventana sí baja el residuo a la mitad.** De `+0,0251` [+0,0049, +0,0472] con la regla de 15
  minutos a `+0,0120` [-0,0121, +0,0356] con la de la v6, y el intervalo pasa a incluir al cero. Lo
  que no hace es dejarlo en cero (H4), pero la dirección del cambio es la correcta y el cambio es real.
- **Las dos bandas de la ventana son consistentes entre sí**: [45, 60) da +0,0108 sobre 278 pasadas y
  [60, 120] da +0,0129 sobre 403. No hay un borde escondido dentro de la ventana, que era el riesgo
  que motivó el cambio.
- **La regla no produce falsos positivos**: 0 de 200 repeticiones del nulo, igual que la de la v5.
- **El tramo posterior a #535 sigue siendo el declarado**: con la muestra de la v6 tiene **75 noches**
  y el ancho medio del intervalo es **0,083**, que reproduce el "cercano a 0,086" de l. 305-307, y la
  equivalencia aparece 15 de 80 veces bajo el nulo, o sea sí es alcanzable. Eso sí, ese tramo tiene
  **cero volcanes con 20 noches**, así que la segunda condición del positivo no es evaluable ahí; el
  documento ya dice que el veredicto se toma sobre la muestra completa, así que no es un defecto, pero
  conviene escribirlo.
- **La tabla de `zc_punto` de §4 reproduce exacto** con la regla literal: Chaitén 4,22 [3,19, 4,66],
  Cordón Caulle 4,25, Planchón-Peteroa 3,23, Nevados de Chillán 2,47, Isluga 6,07 [2,04, 7,69] sobre 13
  pasadas. La corrección que la ronda 5 pidió quedó hecha (salvo el rastro en §9, H10).
- **El n del control H quedó corregido**: con TIF usable son **110** pasadas, **50 de Cordón Caulle**,
  que es exactamente lo que dice l. 230.
- **El control congelado son 19 archivos** (`git ls-files experiments/_s144_keep_peak_direccion/control_s143 | wc -l`
  da 19) y el rango `pipeline/geo_utils.py:53-78` es correcto: `get_detection_anchor` empieza en la 53
  y su último `return` está en la 78.
- **Las correcciones de redacción de la ronda 5 están hechas**: la frase "misma textura de flanco" fue
  reemplazada por la de población de sitios con los 101 grados de acimut declarados (l. 190-193),
  C1 quedó eliminado con su razón escrita, y §1 informa el embudo real de 1.113 y 711.
- **Ninguna evaluación de `Z` falló** por caer el punto fuera del ráster o sin `ΔL0`, en ninguna de mis
  corridas (681 más 681 más 1.857 pasadas, con 5 referencias cada una).

**No verificado** (queda abierto y lo marco como SOSPECHA): los `Z(P)` de la muestra del veredicto y
las clases de M1, que no calculé a propósito; si los controles G y H pasan sus criterios, porque sólo
conté sus pools; si el sesgo de la población de referencia (H5) cambia cuando se excluyen los volcanes
con rasgo térmico permanente, que no corrí; la sensibilidad de `Distancia_km` con OCR; y si el
estimador de `B` (la comparación de imagen propia contra cruzada) se sostiene con la ventana de la v6,
porque el subconjunto con las dos imágenes usables se achica y no lo medí.

---

## Correcciones para una v7, por gravedad

1. **(5) Sacar `R` de la regla de decisión (H1 y H2).** Está medido: `R = +0,0120` se descompone en
   **-0,0355 de suelo del instrumento y +0,0476 de efecto del sitio**, y ese segundo término es la
   cantidad que M2 quiere estimar. Las opciones, y hay que elegir una por escrito antes de medir:
   (a) comparar contra el **nulo del instrumento corrido sobre las mismas pasadas del veredicto**
   (observado = punto sorteado, mismos rásteres, mismos sitios de referencia), que es el único nivel
   que no contiene la hipótesis, y que sobre el estrato hermano vale -0,0355;
   (b) declarar que el estadístico **es** la diferencia entre el brazo con `P` y el brazo con punto
   sorteado sobre la misma muestra, con lo que el suelo se cancela por construcción y la banda vuelve
   a estar en cero;
   (c) dejar la regla contra cero como en la v5 y escribir en §8 que la salida de equivalencia no
   autoriza a apagar `keep_peak`, que era la opción (c) que la ronda 5 ya ofrecía.
   **No vale** seguir usando el estrato hermano: la propia v6 escribe dos veces que un valor alto ahí
   significa que la hipótesis es cierta.
2. **(5) Redefinir el pool de `N1` y volver a medirlo antes de escribirlo (H3).** Tal como está
   ("pasadas sin patrón") da `D = -0,0984` [-0,1162, -0,0809] y la compuerta se pone en rojo sola,
   porque el pool arrastra 416 noches con alerta. Si la intención era el pool de la ronda 5
   (`neg_limpio`, fuera de Lastarria), hay que decirlo con esas palabras, y aun así con la ventana de
   la v6 da **-0,0233** [-0,0458, -0,0032], no -0,0046: el número citado hay que reemplazarlo.
   Y hay que decir si la banda de ±0,05 se aplica al punto o al intervalo.
3. **(4) Corregir el párrafo que justifica la ventana (H4).** La ventana no deja el residuo en cero:
   deja **+0,0120** [-0,0121, +0,0356]. La razón está medida: 300 de las 681 pasadas cambian de pareja
   al aplicar la regla y conservan +0,0327. Escribir el número medido, no el de la banda, y decir que
   la banda era un subconjunto condicionado a la selección y no una predicción de lo que hace la regla.
4. **(4) Tratar el sesgo de los sitios de referencia (H5).** El 5,20 contra 5,66 es un promedio
   agrupado. Por volcán la razón llega a 27,8 en Láscar y 11,7 en Cordón Caulle, y con la ventana de la
   v6 el propio promedio agrupado ya es 4,37 contra 6,70. Opciones a elegir por escrito: excluir del
   pool de referencia los sitios que superan el umbral en una fracción alta de sus propias noches;
   exigir que las 5 referencias sean sitios distintos (hoy la mediana es 4 y en 21 pasadas es 1, H9 de
   la ronda 5); o declarar el sesgo y su signo, que va en contra de la hipótesis.
5. **(3) Decir con qué estimador y sobre qué mezcla de volcanes se calcula `R`, o el nivel que lo
   reemplace (H6).** Agrupado da +0,0120 y re-ponderado a la mezcla del veredicto +0,0268, y la
   distancia L1 entre las dos composiciones es 0,409. Lo natural es exigir el mismo estimador que `D`
   y la misma estratificación por volcán.
6. **(3) Arreglar la fila final de la tabla de §8 (H7)**: hoy decide sobre C1, que se eliminó, y sobre
   C2, que dejó de ser compuerta, y no menciona `N1`, que es la única compuerta nueva.
7. **(3) Escribir en §8 el mapa de potencia de la regla nueva (H8)**, para que nadie lea el INCONCLUSO
   como hallazgo: bajo el nulo la v6 entrega INCONCLUSO el 39,5 % de las veces contra el 1,5 % de la
   v5, y el positivo pide `D` del orden de +0,13 para salir siempre (a +0,083 sale el 56 %).
8. **(2) Fijar si "`R` ± 0,05" usa el punto o el intervalo (H9)**, que es el mismo defecto que la ronda
   5 marcó en C2 y que la v6 arregló sólo del lado del positivo.
9. **(2) Reemplazar los números que no reproducen (H10)**: el denominador de §0-bis (2.627 con la
   definición de patrón de §4, no 2.541), los conteos de cruzada (1.396 con la ventana de la v6 sobre
   ese denominador, o el que corresponda a la lectura que se elija), el pool del control G (52
   pasadas, 49 de Láscar) y el intervalo de Isluga en §9, que debe decir 2,04 como ya dice §4.
10. **(1) Cerrar los detalles de H11**: que la ventana ya corta las pasadas diurnas y el filtro es
    redundante; que en `N1` los sitios de referencia se re-derivan del punto sorteado; que `zc_punto`
    se calibra en rásteres propios y se aplica en cruzados; fijar el orden de las dos condiciones del
    veredicto aunque hoy no se toquen; y decidir antes de medir si se pasa a un estadístico continuo,
    porque el binario sigue tirando a cero el 72,1 % de los `d_p`.

**Resumen**: el instrumento de la v5 sigue en pie y la ventana de la v6 lo mejora de verdad, a la
mitad del residuo y sin quedarse sin muestra (601 pasadas, 349 noches, 6 volcanes elegibles). Lo que
la v6 rompió es la regla. `R` no es el nivel del instrumento: medido sobre las mismas pasadas, el
suelo del instrumento es -0,0355 y `R` es +0,0120, así que `R` lleva adentro +0,048 del efecto que se
quiere medir, y restarlo hace que el positivo sea inalcanzable cuando el fenómeno es uniforme entre
estratos, que es el caso físicamente esperable para un foco permanente. Y la compuerta `N1`, tal como
está escrita, falla sola. **No es viable tal como está.** Con las correcciones 1 y 2 hechas antes de
medir, más los números de la 3 y la 4 puestos al día, M2 vuelve a poder decidir: el instrumento existe,
la muestra alcanza, y el nulo del punto sorteado sobre las mismas pasadas es el nivel honesto contra
el que comparar.
