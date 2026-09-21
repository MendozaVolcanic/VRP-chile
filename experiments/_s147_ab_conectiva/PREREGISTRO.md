# Pre-registro del A/B de la conectiva de los Tests 2 y 3 (S147)

> **Estado: escrito y commiteado ANTES de correr el brazo.** Las predicciones de abajo tienen
> número, y el resultado puede refutarlas. Todo lo que se cite como "medido" sale de
> `experiments/_s147_residual/` con su salida cruda guardada al lado.

## 1. El fenómeno, primero

De noche, sobre un volcán, el satélite mide cuánto brilla cada píxel en el infrarrojo medio y en
el térmico. El algoritmo de MIROVA busca píxeles que sobresalgan de sus vecinos. La pregunta que
decide todo es **cuánto tiene que sobresalir un píxel para contar**.

Hay dos respuestas posibles, y son físicamente distintas:

- **Un umbral fijo**: sobresalir más que un número dado, siempre el mismo. Simple, pero ciego a
  qué tan ruidosa es la escena. En una noche despejada y con el volcán justo debajo del satélite
  funciona bien. En una escena con nubes, o en el borde del barrido donde cada píxel es más
  ruidoso, el propio ruido cruza el umbral.
- **Un umbral que se adapta a la escena**: sobresalir más que varias veces la dispersión de toda
  la imagen. Si la escena es ruidosa, el umbral sube solo.

El paper de MIROVA (Coppola et al. 2016, `documentacion/sp426.5.pdf`, p. 7) **dice las dos
cosas**. Su fórmula une las dos condiciones con un "OR", o sea que basta con superar la más
fácil, que en la práctica es siempre el umbral fijo. Pero su prosa, tres líneas más abajo, dice
que el umbral fijo es un **mínimo** que hay que superar y que *"cuando se analizan escenas muy
variables, la detección se logra con el análisis estadístico de toda la escena"*, que es lo
contrario: manda la más exigente.

La réplica implementa la fórmula. Medido en S136: con ella el umbral fijo gobierna el **99,9 %**
de los records de VIIRS, o sea que la adaptación a la escena **nunca actúa**.

## 2. Lo que ya está medido, y por qué apunta acá

Quitado el Test 1 integrado (A/B S147, run 35521542153), la réplica todavía publica en el
**28,7 %** de las pasadas de VIIRS 375 en que MIROVA procesó el mismo gránulo y no vio nada
(105 de 366). Ese residual es del camino contextual, el que sí está en el paper. Disecado:

| qué | donde MIROVA alertó (n = 135) | donde MIROVA no vio nada (n = 105) |
|---|---|---|
| cúmulos de un solo píxel | 45 % | **92 %** |
| magnitud mediana | 0,103 MW | **0,028 MW** |
| bajo 0,05 MW | 21 % | **73 %** |
| distancia al cráter, mediana | 0,28 km | **2,88 km** |
| ángulo cenital, mediana | 35° | **56°** |
| temperatura del fondo, mediana | 266 K | **259 K** |

Y la tasa de publicación falsa, por zona del barrido y por temperatura del fondo:

| | fondo bajo 260 K | 260 a 270 K | sobre 270 K |
|---|---|---|---|
| nadir (cenital bajo 36°) | 24 % (9 de 37) | 20 % (12 de 59) | **9 %** (3 de 33) |
| medio (36° a 52°) | 16 % (3 de 19) | 37 % (10 de 27) | 18 % (4 de 22) |
| borde (sobre 52°) | **57 %** (43 de 75) | 32 % (16 de 50) | 12 % (5 de 43) |

O sea que el exceso vive **donde la escena es más ruidosa**. En el borde del barrido VIIRS banda I
no agrega muestras a bordo (agrega tres cerca del nadir y dos en la zona media), así que cada
píxel es raíz de tres veces más ruidoso. Y un fondo bajo 260 K es nube o cirrus, con bordes que
meten textura. Con un umbral fijo, más ruido son más cruces espurios.

**MIROVA hace lo contrario.** Con sus propios datos (archivo OSF, 32.669 detecciones de VIIRS 375
nocturno en volcanes de Chile) contra el reparto de nuestras 12.407 pasadas:

| zona | % de las pasadas | % de las detecciones de MIROVA | eficiencia |
|---|---|---|---|
| nadir | 33,3 % | 47,0 % | **1,41** |
| medio | 22,2 % | 24,0 % | 1,08 |
| borde | 44,6 % | 29,1 % | **0,65** |

MIROVA detecta 2,2 veces **menos** por pasada en el borde; nuestra tasa falsa es 2,1 veces
**mayor** ahí. Pendientes opuestas. Y MIROVA sí procesa esas pasadas (lista el 70 % de las del
borde contra el 78 % de las del nadir), así que calla por decisión del algoritmo.

Dos explicaciones quedaron **descartadas** con datos: que MIROVA se salte las pasadas del borde
(no se las salta), y que el redondeo con que publica esconda sus detecciones (publica cuantizado
a 0,01 MW, pero sólo 8 de las 105 residuales están bajo 0,005 MW).

**Lo que exigiría la lectura de prosa**: la mediana de `mu + 5 sigma` del dNTI es 0,0056 a 0,0060
en el nadir y 0,0071 a 0,0074 en el borde, contra el 0,003 fijo que rige hoy. O sea el doble, y
más alto justo donde está el exceso.

## 3. El brazo

| brazo | perfil | qué cambia |
|---|---|---|
| **B, control de este A/B** | `_s146_ab_sin_test1` | nada respecto de S147: sin Test 1, conectiva de fórmula |
| **F** | `_s147_ab_sin_test1_max` | **una sola cosa**: `enable_tests_23_prose_branch: true` |

Comprobado resolviendo los dos perfiles como los resuelve el código (no leyendo el YAML, A89):
sobre 137 atributos, difieren en `ENABLE_TESTS_23_PROSE_BRANCH` y en el nombre y el directorio de
salida, nada más.

**Los dos brazos se corren en el MISMO run**, aunque el B ya existe. Motivo: la ventana termina
hoy y NASA va reemplazando gránulos de tiempo casi real por los estándar; correr el B de nuevo
junto al F garantiza que los dos vean los mismos gránulos (hallazgo H7 del verificador del
pre-registro anterior).

Ventana **2026-09-01 a 2026-09-20**, los 11 Tier A, los tres sensores. Referencia y producción
**congeladas**, las mismas del A/B anterior (`experiments/_s146_ab_sin_test1/_congelado/`).

## 4. Las predicciones, con número

Si la conectiva es el mecanismo del residual, al pasar de B a F:

| # | predicción | umbral | si falla |
|---|---|---|---|
| **P1** | la publicación en negativos limpios de VIIRS 375 baja | de 28,7 % a **18 % o menos** | la conectiva no explica el grueso del residual |
| **P2** | el exceso del borde desaparece: razón entre la tasa falsa del borde y la del nadir | de 2,05 a **1,3 o menos** | el ruido del borde no entra por el umbral: mirar el remuestreo (D17) |
| **P3** | la celda borde con fondo frío baja | de 57 % a **30 % o menos** | ídem, para la nube |
| **P4** | el recall por pasada de VIIRS 375 aguanta | **118 o más** de las 141 que publica el control de producción, y **ninguna** pérdida con 0,5 MW o más de MIROVA | la lectura de prosa cuesta detección real: NO ADOPTAR aunque P1 a P3 se cumplan |

**P2 es la que decide la hipótesis.** P1 podría cumplirse sólo porque un umbral más alto apaga
de todo un poco; P2 exige que lo apagado sea **selectivamente** lo del borde, que es lo que
distingue este mecanismo de un simple endurecimiento.

**Lo que NO se predice y se informa igual**: VIIRS 750 y MODIS (en MODIS la batería del Apéndice
A ya mostró que `max` con la banda 21 pierde tres casos reales, porque la banda 21 infla el
sigma; ahí la conectiva no se puede juzgar sola, va junto con D21), la magnitud pareada, la
posición del cúmulo, y el nulo por etiquetas barajadas.

## 5. Controles

- **Cobertura pareja, simétrica**, contada antes de mirar nada (A108). Si falla, INDECIDIBLE.
- **Control positivo**: el brazo B de este run tiene que reproducir al brazo B del run
  35521542153 en la decisión de publicar. Es el mismo perfil sobre la misma ventana, así que la
  diferencia permitida es sólo la de gránulos promovidos de tiempo casi real a estándar.
- **Identidad del predicado del tablero**, pineada.
- **El instrumento que mide P2 y P3** es `experiments/_s147_residual/estructura_del_residual.py`,
  el mismo que produjo la línea base, sobre el brazo nuevo.

## 6. Qué NO autoriza este experimento

Nada en producción. Si las cuatro predicciones se cumplen, lo que sigue es el gate del proyecto:
diseño revisado, verificación a nivel de píxel contra MIROVA y ciclo A45 con tag defensivo y
confirmación explícita de Nicolás. Este A/B decide si la hipótesis merece ese camino.

Y una salvedad de honestidad: **la ambigüedad es del paper**, no nuestra. Si algún texto
posterior del grupo de MIROVA re-enuncia los tests de forma inequívoca, eso pesa más que
cualquier A/B. Esa revisión bibliográfica corre en paralelo a este experimento.
