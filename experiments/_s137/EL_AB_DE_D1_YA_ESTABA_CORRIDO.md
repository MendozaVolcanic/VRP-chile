# S137 · El A/B que recomendé correr ya estaba corrido, y su resultado apunta al mismo lugar que el paper

> Corrección de una recomendación propia, hecha en la misma sesión. Sin gastar el run.

## El error

Al presentarle a Nicolás las decisiones pendientes, puse D19 como «tres sesiones esperando» y
recomendé, entre las opciones, *«A/B de keep_peak OFF contra ON»*, diciendo que faltaba correrlo.
Nicolás lo aprobó. Antes de disparar el run verifiqué si ya existía, y **ya existía**:

- Pre-registro completo, en tercera versión, con la decisión de Nicolás incorporada:
  `docs/PREREGISTRO_AB_D1_D2_S135.md`.
- Los cinco perfiles de brazos, cada uno con su `data_subdir` aislado, verificados hoy: cada uno
  lee exactamente lo que declara.
- El workflow `reproc-s135-ab-d1d2.yml`, sin archivar.
- **Y los dos runs, ambos verdes**: 34173711390 (chunk 1) y 34208191011 (chunk 2), ventana
  completa 2026-06-01 al 2026-08-31, seis volcanes, 260 noches confirmadas.
- El veredicto escrito: `experiments/_s135_ab_d1d2/RESULTADO_FINAL.md`.

Lo que yo iba a mandar a correr estaba corrido desde el 8 de septiembre, con más ventana y mejor
criterio del que yo habría fijado.

**Por qué pasó.** Leí el traspaso de S136, que lista las decisiones pendientes de `AUDIT_S134.md`
sin marcar cuáles ya se habían ejecutado, y tomé «D1 sigue esperando decisión de Nicolás» como
«D1 sigue esperando el experimento». Son cosas distintas: el experimento corrió y lo que espera
es qué hacer con un resultado en el que **ningún brazo cumple**. Es A8 y A50 otra vez, y el propio
traspaso de S136 advierte de esto en su sección de aprendizajes, con el mismo caso: *«iba a gastar
un run de Actions midiendo el ruido de banda, y S133 lo había medido»*.

El síntoma que lo delata es el mismo que describió S136: la hipótesis se siente obvia y nueva a la
vez. Acá además había una pista más barata: una decisión que lleva tres sesiones abierta y es
puramente de flags rara vez sigue sin medirse.

## El resultado que ya existía

| brazo | pierde noches | quita el artefacto | paridad | falla en |
|---|---|---|---|---|
| A control | 0 | (control) | 0,708 | (es el control) |
| B sin `keep_peak` | 0 | 100 % | 0,692 | criterio 3, por dos centésimas |
| C sólo 2º pase condicionado | 0 | **peor 46,6 %** | 0,713 | criterio 2 |
| D ambos, el más fiel al paper | **12** | 100 % | 0,713 | criterio 1 |
| E 2º pase apagado | 0 | **peor 46,6 %** | 0,672 | criterios 2 y 3 |

Lo que dejó probado, y que no hay que volver a medir:

- **Apagar `keep_peak` elimina el artefacto por completo** y sin perder ninguna noche, siempre que
  el segundo pase siga suelto (brazo B). Falla el criterio de paridad por dos centésimas.
- **Tocar el segundo pase sin tocar `keep_peak` empeora el artefacto un 47 %**, en los dos brazos
  que lo hacen. Descartado por medición.
- **El brazo más fiel al paper pierde 12 noches** que MIROVA sí publica, y las cinco investigadas
  son un solo mecanismo: el Test 1 integrado encuentra la señal con 65 a 98 píxeles, el primer
  pase entrega entre 0 y 2, y lo que llega a publicarse depende de `keep_peak` o del segundo pase
  suelto.

Y su conclusión: *«el Test 1 integrado detecta la señal y algo aguas abajo la anula. Ese algo es la
intersección con la máscara contextual, que se introdujo en S99 y no está en el paper»*.

## Lo que aporta la lectura del paper de hoy

La conclusión de S135 y la lectura del PDF llegan al mismo punto desde lados distintos.

El paper, página 6, sección del umbral fijo, verbatim:

> *"Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded (unsuitable) for
> further steps."*

Y página 7, sobre los contextuales:

> *"In addition, pixels flagged as 'active' by means of tests 2 and 3 are subsequently eliminated
> from further analysis."*

En el algoritmo del paper los caminos de detección **se suman**: cada test marca activos y los
retira; ninguno filtra a otro. **La intersección no existe en el paper en ninguna parte.** Eso es
justo lo que S135 identificó como el lugar del problema.

**Con una salvedad que hay que hacer explícita, porque es el tipo de confusión que este proyecto
persigue.** El «Test 1» del paper SP426.5 es el umbral fijo `NTI > K1`. Nuestro «Test 1 integrado»
es otro objeto, de Coppola 2015, que **no está en este paper** (es la decisión 1 que S136 dejó
abierta). La cita de arriba respalda literalmente lo primero, no lo segundo. Lo que sí se puede
afirmar del paper es la forma general: los caminos son aditivos, no multiplicativos.

## El estado real de ese frente, que el traspaso de S136 reporta de dos maneras

El traspaso lista en «cerrado, no rehacer»: *«5. Retirar la intersección contextual. Los datos
apuntan a que sigue curando, no a que sobre»*. Pero su propia sección de sospechas dice, del mismo
asunto: *«Dirección clara, n insuficiente (3 contra el umbral de 4), así que formalmente sigue
indeterminado»*. Y el documento que lo midió
(`experiments/_s136/SUSTRATO_RESUELVE_EL_DESENLACE.md`) lo dice con todas las letras:

> *"Formalmente sigue siendo C porque n = 3 < 4, el umbral pre-registrado."*

Las dos afirmaciones conviven en el mismo traspaso. La resolución honesta es que **retirar la
intersección entera está desaconsejado por la dirección de la evidencia** (con n = 3, retirarla
lleva la paridad a 2,23, fuera de banda), pero **el desenlace formal es indeterminado** y el
mecanismo sigue siendo infiel al paper. «Desaconsejado con n = 3» no es lo mismo que «cerrado».

## Lo que NO se afirma acá

- No se afirma que haya que retirar la intersección. La única medición disponible dice lo
  contrario, y esa medición es la que manda hasta que haya otra con más n.
- No se afirma que el A/B de S135 esté mal. Está bien hecho y su criterio es mejor que el que yo
  habría escrito.
- No se propone reabrir D1 con un experimento nuevo sobre el mismo eje: S135 ya probó que **el eje
  no contiene la solución**.

## Lo que corresponde

D1 no espera un experimento, espera una decisión sobre un resultado donde ningún brazo cumple, y
esa decisión es de Nicolás. Las opciones reales son tres, y ninguna es «correr el A/B»:

1. **Adoptar B** aceptando que falla el criterio de paridad por dos centésimas. Quita el artefacto
   por completo y no pierde ninguna noche. El costo: conserva un segundo pase que sabemos infiel, y
   ajustar un criterio después de ver el dato es justo lo que el pre-registro prohíbe.
2. **No adoptar ninguno** y mover el frente al Test 1 integrado y su intersección contextual, que
   es lo que recomienda el resultado de S135 y adonde apunta la forma aditiva del paper. Requiere
   pasar por las tres preguntas de MISSION, porque el Test 1 integrado no está en este paper.
3. **Dejarlo como está** y documentar la convención, que es la opción que el propio A/B deja como
   estado de hecho desde el 8 de septiembre.
