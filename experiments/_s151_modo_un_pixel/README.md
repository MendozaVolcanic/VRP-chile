# Tarea 1.8: el modo de un solo píxel, en reposo y en erupción

> Escrito 2026-10-14 por el loop (tarea 1.8 de `tasks/LOOP_OBJETIVOS.md`). Sin correr el pipeline: sólo records
> en disco. Lo declarado antes de mirar está en `DECLARACION.md`, en su propio commit (7b2171ca0). Todo número
> de este documento sale de `medir_modo_un_pixel.py`, con su salida en `salida.txt` y `resultado.json`.
> No toca `pipeline/` ni los perfiles. No despacha nada.
>
> **Correcciones posteriores al resultado** (verificador con contexto limpio de #799, mismo día). Confirmó la
> conclusión y la recomendación y pidió cinco arreglos y uno menor, todos aplicados después de ver el resultado y
> marcados en §8: (D1) un cúmulo con más de un conjunto de píxeles posible pasa a no reconstruible; (D2) MODIS sí
> cambia de magnitud en negativos limpios; (D3) la frase sobre la subestimación de la erupción era falsa en VIIRS
> 750; (D4) el "62 de 211" no contaba pasadas donde el número cambia; (D5) la recomendación del brazo extra se
> matiza; y se agrega el intervalo por volcán que pedía la declaración. Ninguna cifra de las pasadas con alerta
> se movió; sí el control y las sumas MODIS en negativos limpios.

## 1. La pregunta

¿Qué regla de magnitud para cúmulos chicos se acerca más a lo que publica MIROVA, en reposo y en erupción, sin
cambiar qué se publica? Se compara la regla actual (pico si el cúmulo tiene 3 píxeles o menos y su magnitud es
menor a 5 MW) con el modo apagado, la suma de todo el cúmulo, un umbral de 1 MW sobre la suma y un umbral de
1 MW sobre el pico.

## 2. El fenómeno y el mecanismo

**Fenómeno.** En reposo, un cráter con fumarolas calientes o un lago de lava chico calienta un solo píxel de
verdad; los vecinos que nuestro detector contextual agrega quedan apenas sobre el fondo, y sumarlos infla la
magnitud. Por eso nació el modo en S77. En erupción pasa lo contrario: el material caliente (bordes de flujo,
cráter incandescente) llena varios píxeles, y quedarse con el más caliente subestima. AUDIT_S150 (C-03) lo vio en
Chillán, VIIRS 750 el 2026-10-01: 2,66, 11,08 y 2,49 MW en 54 minutos contra 9,0, 10,0 y 7,06 de MIROVA.

**Mecanismo, lo que encontró esta medición y que el planteamiento no traía.** El modo cambia `pc.vrp_mw`, pero
lo que ve el operador no siempre es ese número:

- **VIIRS 375**: el tablero publica el núcleo F5' (`f5_core_vrp_mw`), que se calcula desde los píxeles guardados
  y no pasa por el modo. De 1.281 pasadas con alerta que publicamos, 395 tienen el modo activo con 2 o 3
  píxeles, y **en ninguna** el número publicado cambia con ninguna variante.
- **MODIS**: la magnitud focal (`cluster_focal_vrp_mw`) corre antes que el modo; cuando ningún píxel del cúmulo
  es contextual, el foco ya es el píxel pico y apagar el modo no cambia nada. **En las pasadas con alerta** no
  llega al tablero: de 88 pasadas MODIS con alerta desde marzo publicamos 11, **todas con más de 3 píxeles**; las
  77 que no publicamos, incluidas las 16 con cúmulo de 2 o 3 píxeles, llevan la etiqueta `far` (el problema de
  A82, otro frente). **En los negativos limpios sí llega** (corrección D2): en reposo MODIS publica 536 pasadas
  donde MIROVA no vio nada, y ahí la magnitud cambia con las variantes (§4).
- **VIIRS 750** es el único sensor donde el modo puede decidir el número publicado en una pasada con alerta: de
  211 publicadas, 62 tienen un cúmulo identificado de 2 o 3 píxeles, y entre los 1.304 pares que deciden el
  número cambia con alguna variante en **28** (corrección D4: la versión anterior presentaba los 62 como pasadas
  donde el modo decide; no se desglosó por qué los demás no cambian).
- El tope D9 de 5 MW se aplica **antes** que el modo, y todas las variantes dejan los cúmulos de 1 a 3 píxeles
  bajo 5 MW salvo los que ya estaban sobre 5. Ninguna variante cruza la regla de cirrus (10 MW con `t_max` bajo
  273,15 K) ni lleva una magnitud a cero.

**Por qué no es monótono, en una frase.** La regla mira a la vez la suma (menos de 5 MW) y el número de píxeles
(3 o menos): tres píxeles de 1,6 MW suman 4,8 y publican 1,6; cuatro de 1,0 suman 4,0 y publican 4,0. Y el umbral
se llama "sub-MW" pero vale 5 MW.

## 3. Control de la reconstrucción

Los píxeles de cada cúmulo se aíslan buscando entre `anomaly_pixels` y `discarded_anomaly_pixels` el conjunto cuyo
promedio simple reproduce el centroide persistido (así lo calcula `pipeline/clustering.py`), y se exige que ese
conjunto sea **único**. Se identifican exacto 1.069 cúmulos MODIS de 2 o 3 píxeles (240 no, porque tienen
píxeles con VRP 0 que no se guardan, y 12 ambiguos), 675 de VIIRS 375 (1 no) y 282 de VIIRS 750 (13 no).

| control | resultado | criterio fijado antes |
|---|---|---|
| regla actual reconstruida contra `pc.vrp_mw` persistido, producción | **2.019 de 2.021 (99,90 %): PASA** | 0,0015 MW, 99 % |
| lo mismo, brazo de control C0 de la prueba de Chillán | 42 de 42: PASA | igual |
| control negativo: la suma reproduce lo persistido | 425 de 2.021 (los cúmulos con vecinos de VRP casi 0) | debe ser minoría |
| sin modo, sin foco ni tope: la suma reproduce lo persistido | 4 de 4 | |

Las 2 fallas son un Villarrica MODIS con magnitud focal y un Chaitén MODIS cuyos píxeles guardados no son los que
sumó el cúmulo (asimetría A46); están listadas en `resultado.json`. Los records no reconstruibles (266 en
producción) se dejan fuera de toda comparación; entre las pasadas con alerta que publicamos hay sólo uno (VIIRS
750).

**Corrección D1, posterior al resultado.** La primera versión tomaba el primer conjunto que reproducía el
centroide. El verificador encontró 12 cúmulos MODIS con más de un conjunto posible, 10 de ellos con distinto pico
o suma; una de las 3 fallas del control original (Planchón Peteroa 2026-07-11 02:30) era esto, porque el conjunto
alternativo da pico 1,0157 contra 1,016 persistido. Ahora un cúmulo ambiguo queda no reconstruible. El control
pasó de 2.030 de 2.033 (99,85 %) a 2.019 de 2.021 (99,90 %). Ninguno de los 12 está entre las pasadas con alerta
que publicamos (uno es una alerta MODIS no publicada, etiqueta `far`), así que la tabla de §4 no se mueve; sí se
mueven las sumas MODIS en negativos limpios.

## 4. Resultado

Pares: pasada nuestra publicada con alerta de MIROVA a +-2 min, de marzo (MODIS) o abril (VIIRS) al 2026-10-14.
Deciden 1.472 de 1.674 (las 202 alertas sólo del OCR antes del 13 de junio van aparte, A119); 1.304 se publican
en todas las variantes. **Sólo 28 cambian de magnitud con alguna variante (2,1 %), todos de VIIRS 750: 21 en
reposo y 7 en la erupción de Chillán.** Razón = nuestra / MIROVA; "dif" es la media pareada de |log10 razón|
de la variante menos la de la regla actual, con intervalo de 95 % por remuestreo de noches de volcán (negativo =
más cerca de MIROVA).

| estrato | n | actual (A) | modo apagado (B_off) | suma (B_sum) | umbral 1 MW (C) | pico 1 MW (D) |
|---|---|---|---|---|---|---|
| reposo, todos | 1.247 | 0,704 | 0,705, dif -0,0009 [-0,0020, 0,0001] | igual a B_off | 0,704, dif +0,0001 [-0,0005, 0,0009] | 0,704, dif +0,0002 [-0,0002, 0,0008] |
| reposo, VIIRS 750 | 175 | 0,572 | 0,576, dif -0,0067 [-0,0142, 0,0008] | igual | 0,575, +0,0009 | 0,572, +0,0012 |
| reposo, sólo los 21 afectados | 21 | 0,659 | **0,898**, dif -0,0554 [-0,1136, 0,0062] | igual | 0,700, +0,0073 | 0,659, +0,0104 |
| erupción, todos | 57 | 0,578 | 0,578, dif -0,0013 [-0,0134, 0,0119] | igual | 0,578, -0,0042 [-0,0151, 0,0066] | 0,578, -0,0066 [-0,0170, -0,0001] |
| erupción, VIIRS 750 | 21 | 0,418 | 0,498, dif -0,0037 [-0,0398, 0,0335] | igual | 0,498, -0,0113 | 0,498, -0,0180 [-0,0475, -0,0001] |
| erupción, sólo los 7 afectados | 7 | 0,587 | 0,813, dif -0,0110 [-0,0924, 0,0960] | igual | 0,813, -0,0340 | 0,813, -0,0539 [-0,1064, -0,0025] |
| erupción, brazo C0 (todos) | 34 | 0,561 | 0,561, dif -0,0044 | igual | -0,0092 [-0,0251, -0,0] | -0,0092 [-0,0251, -0,0] |

El intervalo por volcán que pedía la declaración se agregó después del resultado (`salida.txt` §5, "por volcán",
y `resultado.json`): en ningún volcán cambia la mediana salvo Láscar VIIRS 750 (0,52 a 0,53 con la suma, 99
pares) y Puyehue Cordón Caulle VIIRS 750 (0,68 a 0,70, 37 pares), las dos dentro de su intervalo.

Por tramo A119, en VIIRS 750 de reposo: de marzo al 12 de junio el modo apagado mejora con intervalo entero bajo
cero (dif -0,0155 [-0,0269, -0,0040], 94 pares, 17 afectados); del 13 de junio en adelante no (+0,0037, 81 pares,
4 afectados). VIIRS 375 y MODIS: diferencia exactamente cero en todos los estratos.

**Publicaciones que cambian: ninguna**, en ninguna variante ni extremo, ni en pasadas con alerta ni en
negativos limpios; **alertas protegidas afectadas: 0 en la lectura A y 0 en la B.** En negativos limpios cambia
sólo la magnitud de lo que ya publicamos, y ahí sí entra MODIS (corrección D2):

| negativos limpios de reposo | publicaciones | actual (A) | modo apagado | suma | C | D |
|---|---|---|---|---|---|---|
| MODIS, mediana / suma (MW) | 536 | 1,5695 / 1.437,6 | 1,676 / 1.452,7 | 1,7815 / 1.473,5 | 1,676 / 1.451,1 | 1,665 / 1.448,0 |
| VIIRS 750, suma (MW) | 1.226 | 643,0 | 667,9 | 668,6 | 660,4 | 654,7 |

En MODIS son 10 records menos que en la primera versión (243 excluidos contra 233) por la corrección D1.

**La secuencia de AUDIT_S150, reconstruida.** Con la suma, las tres pasadas del 2026-10-01 dan 4,48, 11,08 y
2,92 MW contra 9,0, 10,0 y 7,06 de MIROVA: el salto baja de 4,2 veces a 2,5 veces pero no desaparece. Lo que
queda es que el cúmulo de las 05:24 y 06:18 tiene 2 píxeles y el de las 06:00 tiene 3, y en las 05:24 y 06:18
MIROVA ve más energía que la que suman todos nuestros píxeles. El modo explica parte del primer salto, no la
subestimación de la erupción.

**Veredicto contra la regla declarada: ninguna variante gana con claridad.** Las que más se acercan son el modo
apagado (en reposo, intervalo [-0,0020, 0,0001], que toca el cero) y D (en erupción, intervalo bajo cero por un
pelo, -0,0001, y sin mejora en reposo). No hay pre-registro de A/B (`PREREGISTRO.md` no se escribe), porque la
regla de la declaración pide intervalo entero bajo cero en los dos regímenes.

## 5. Lo que esto dice y lo que no

- **El modo de un solo píxel es casi inerte para la paridad de magnitud**: toca el 2 % de los pares y sólo en
  VIIRS 750. En la erupción la mediana de la razón sí sube con la suma en VIIRS 750 (0,418 a 0,498), pero el
  error típico no baja: la mediana de |log10 razón| queda en 0,381 con la regla actual y con la suma (0,378 con
  C y D), y en todos los sensores juntos la razón mediana queda en 0,578 con cualquier variante. Lo que falta
  está en cuántos píxeles alerta nuestro detector, no en cómo se suman (corrección D3: la versión anterior decía
  que la subestimación era igual en todas las variantes, y en VIIRS 750 la mediana no lo es).
- La premisa de S77 (sumar infla en reposo) **no se sostiene hoy en VIIRS 750**: en los 21 pares de reposo
  afectados la suma lleva la mediana de 0,66 a 0,90 de MIROVA. Son 21 pares, casi todos de marzo a junio, y el
  intervalo toca cero: es SOSPECHA, no hallazgo.
- El barrido descriptivo del umbral (`salida.txt` §6) apunta a lo mismo: en VIIRS 750 de reposo, cuanto más bajo
  el umbral (más suma), menor el error (0,272 con 0,25 MW contra 0,287 con 5 MW); en erupción el mínimo está
  entre 1 y 3 MW (0,378 contra 0,381). Un umbral leído de esa curva no gana nada aquí (A115).
- Los records no reconstruibles (266: píxeles de VRP 0 no guardados o conjunto ambiguo) quedan fuera. Afectan
  casi sólo a MODIS, que no publica cúmulos de 2 o 3 píxeles con alerta, así que no mueven la razón contra
  MIROVA, pero sí faltan en las sumas de negativos limpios.
- Chillán en erupción son 21 pares de VIIRS 750 en 10 días: casos, no tasas.

## 6. Recomendación

No cambiar el modo ahora. No hay variante que gane con la regla declarada, no cambia ninguna publicación y el
efecto de magnitud es chico frente a la subestimación de la erupción, que viene de otra parte. Si se quiere
simplificar después, el candidato es **apagarlo** (sale de la réplica una regla que no está en los papers de
MIROVA, A10 rebajada: MIROVA suma los píxeles alertados). Para decidirlo no hace falta una corrida: la
reconstrucción offline ya es exacta en el 99,90 % de los cúmulos afectados y nada aguas abajo del modo depende de
su valor (ni la detección, ni la etiqueta, ni la publicación, que no cambia en ninguna variante). Un brazo extra
en la corrida F/K de 11 volcanes (#797) sólo agregaría los 266 no reconstruibles y los datos futuros (corrección
D5: la versión anterior lo presentaba como la medición que decidiría). El frente que sí mueve la magnitud en
erupción es el del número de píxeles alertados (conectiva `max`, fondo por vecinos D25).

## 7. Reproducir

```
git archive origin/s146-ab/38560317428 experiments/_s146_ab_sin_test1/salidas/38560317428/_s146_ab_control | tar -x -C <temporal fuera del repo>
python experiments/_s151_modo_un_pixel/medir_modo_un_pixel.py --c0 <temporal>/experiments/_s146_ab_sin_test1/salidas/38560317428/_s146_ab_control/NevadosDeChillan.json
```

Necesita `node` (predicado del tablero). Tarda unos dos minutos. La referencia es el snapshot del repo (última
fila 2026-10-14 08:35), con la unión histórica y el respaldo de abril.

## 8. Registro de cambios posteriores al resultado

Todos del 2026-10-14, pedidos por el verificador con contexto limpio de #799, que confirmó la conclusión y la
recomendación. Se hacen después de ver el resultado, por eso se marcan: ninguno cambia la regla de decisión ni las
variantes de `DECLARACION.md`.

| id | qué cambió | por qué | efecto en cifras |
|---|---|---|---|
| D1 | `identificar` exige un conjunto único; si hay más de uno, el cúmulo es "ambiguo" y no reconstruible | 12 cúmulos MODIS tenían más de un conjunto posible, 10 con distinto pico o suma | control 99,85 % a 99,90 %; no reconstruibles 254 a 266; sumas MODIS en negativos limpios; nada en pasadas con alerta |
| D2 | se dice que MODIS sí cambia de magnitud en negativos limpios | la frase "no llega al tablero" valía sólo para las alertas | ninguno (texto) |
| D3 | se corrige la frase sobre la subestimación de la erupción | en VIIRS 750 la mediana sube de 0,418 a 0,498; lo que no baja es la mediana de \|log10\| | ninguno (texto) |
| D4 | "62 de 211" pasa a "62 identificados, 28 donde el número cambia" | 62 contaba cúmulos, no pasadas afectadas | ninguno (texto) |
| D5 | se matiza la recomendación del brazo extra | la reconstrucción offline ya es exacta y nada aguas abajo depende del valor | ninguno (texto) |
| menor | intervalo de 95 % por volcán | lo pedía `DECLARACION.md` §4 y el script no lo calculaba | sólo agrega intervalos; los intervalos de C0 se mueven en el tercer decimal porque la semilla del remuestreo se consume en otro orden |
