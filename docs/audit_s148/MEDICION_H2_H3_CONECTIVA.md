# Medición de H2 y H3 del A/B de la conectiva (S148)

Qué es esto: el verificador de la lectura de la conectiva
(`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s148\VERIFICADOR_LECTURA_CONECTIVA.md`)
dejó dos salvedades leídas del código y no medidas. Este documento las mide.

- Scripts y salidas crudas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s148_h2_h3\`
  (`h3_segundo_pase.py` con `out_h3.txt`, `h2_magnitud.py` con `out_h2.txt`,
  `diff_perfiles_efectivo.py` con `out_diff_perfiles_efectivo.txt`, `base.py`).
- Datos: salidas del run 35548121381, que viven sólo en la rama de datos `origin/s146-ab/35548121381`
  (no en `main`), extraídas con ruta a un temporal fuera del repo y borradas al terminar.
- Tramo: 2026-09-01 a 2026-09-17. Brazo B = `_s146_ab_sin_test1` (`min`), brazo F =
  `_s147_ab_sin_test1_max` (`max`). Etiquetas y predicado del tablero: los del verificador
  (`experiments/_s148_verificador_conectiva/verif_base.py`), sin modificar.
- Fecha: 2026-09-21. No se corrió el pipeline ni se usaron credenciales de NASA: todo sale de lo
  que cada record persiste (`anomaly_pixels` con `bt_k` y `vrp_mw`, `t_bg_k`, y los contadores
  `diag_n_first_pass_pixels` y `diag_n_second_pass_recapture`).

## Resumen en cuatro frases

1. **H3 está medida y el mecanismo es la compuerta de temperatura, no la conectiva.** En las 401
   pasadas de VIIRS sin ningún píxel del primer pase (los dos brazos, los dos sensores), los 650
   píxeles detectados están TODOS a 3 K o menos sobre el fondo: el primer pase los bota por la
   compuerta `bt > t_bg + 3 K`, que no está en el paper, y el segundo pase, que no tiene esa
   compuerta y corre aunque no haya nada activo, los recoge.
2. **No es un efecto de `max`**: 28 de las 30 positivas ya vivían sólo del segundo pase con `min`.
   Lo que `max` cambia es que ese camino deja de publicar negativas: de 41 a 4 de 325 en VIIRS 375.
3. **Esas 30 pasadas son las más creíbles del conjunto**: cúmulo a 0,26 km del cráter (mediana),
   y magnitud 1,03 veces la de MIROVA, contra 0,60 en las 94 que sí tienen primer pase.
4. **H2 está medida**: con `max` se pierde el vecino tibio (32 píxeles en 22 pasadas, mediana 1,0 K
   sobre el fondo, 0,49 km del pico, un 23 % de la magnitud de la pasada). Pasada por pasada MIROVA
   se parece más al valor de B en 17 y al de F en 8 (p = 0,11): la señal va contra F pero no es
   concluyente, y 16 de las 25 son de un solo volcán, Cordón Caulle, donde da empate (9 contra 7).

## H3. Pasadas que publican sin ningún píxel del primer pase

### El fenómeno físico

Un cráter activo y débil, de noche, en un volcán alto, es un punto que **brilla de más en el
infrarrojo medio respecto del térmico** (un foco sub-píxel de algunos cientos de grados sube el MIR
y casi no mueve el TIR), pero cuya temperatura de brillo total **no supera a la del paisaje que lo
rodea**. La razón es la altitud: la cumbre está a 270 K o menos y el anillo de 5 a 25 km contra el
que se compara incluye valles y laderas bajas más tibias. El cráter de Villarrica el 15 de
septiembre aparece 2,6 K y 6,9 K **más frío** que la mediana de su anillo, y aun así MIROVA le
publica 0,16 MW y nosotros 0,20 MW. Es el mismo fenómeno que ya se describió en D22 y A69: el
contraste espectral (NTI) atenúa la topografía; la temperatura absoluta no.

MIROVA detecta sólo por contraste espectral contra los vecinos. No pide que el píxel sea más
caliente que el fondo regional. Por eso ve estos cráteres.

### El mecanismo en el código, trazado desde el llamador

El detector contextual se llama en dos pasos, y los dos pasos no piden lo mismo:

- **Primer pase** (`pipeline/process_viirs.py:1274`, VIIRS 750 en `pipeline/process_viirs_mod.py:856`):
  exige Test 2 y Test 3 y además `bt > t_bg + 3 K` (`pipeline/detection_context.py:546`; el llamador
  pasa `apply_bt_gate=not ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` en la línea 1297, y ese flag vale
  False en los dos brazos, o sea la compuerta está puesta). Esa compuerta no está en la fórmula del
  paper (D22).
- **Segundo pase** (`pipeline/process_viirs.py:1324`, VIIRS 750 en `pipeline/process_viirs_mod.py:903`):
  reaplica los Tests 2 y 3 con la misma conectiva (`pipeline/detection_context.py:943`) pero **sin
  compuerta de temperatura** (la función ni siquiera recibe la temperatura), y corre aunque el
  primer pase haya salido vacío, porque el llamador le pasa `conditioned=ENABLE_SECOND_PASS_CONDITIONED`
  (línea 1341) y ese flag vale False. La guarda que lo impediría está en
  `pipeline/detection_context.py:906` y no se ejecuta. El resultado reemplaza la máscara
  (`pipeline/process_viirs.py:1357`) y nada posterior lo filtra: `ENABLE_FINAL_PIXEL_FILTER` vale False.

Con el conjunto activo vacío, el segundo pase calcula exactamente los mismos dNTI y dETI que el
primero (no hay ningún activo que sacar del promedio de vecinos). O sea que en ese caso **no es un
refinamiento de bordes: es el primer pase repetido sin la compuerta de temperatura**. Hay una
segunda diferencia, menor: el segundo pase calcula media y desviación sobre todos los píxeles
finitos del recorte (`pipeline/detection_context.py:923`), sin los filtros de píxeles no aptos que sí
usa el primero (`pipeline/detection_context.py:492`). Esa diferencia no produjo ningún píxel por sí
sola, como se ve abajo.

Los valores efectivos de los flags salen de `pipeline.profile`, no del YAML
(`out_diff_perfiles_efectivo.txt`): los brazos B y F difieren en una sola constante de 143,
`ENABLE_TESTS_23_PROSE_BRANCH`.

```
  DISTINTA ENABLE_TESTS_23_PROSE_BRANCH     B False | F True
   ENABLE_SECOND_PASS_CONDITIONED         False
   ENABLE_TESTS_23_NO_BT_GATE_VIIRS375    False
   NTI_BT_SANITY_K                        3.0
   ENABLE_FINAL_PIXEL_FILTER              False
```

### La medición

Instrumento: cada píxel detectado guarda su temperatura de brillo MIR (`bt_k`) y cada record
guarda el fondo que usa la compuerta (`t_bg_k`), así que se puede reconstruir, píxel por píxel,
si habría pasado `bt > t_bg + 3 K`.

**Control del instrumento primero** (A110). En pasadas donde todo píxel vino del primer pase
(primer pase mayor que cero, recaptura cero), ninguno debería estar bajo la compuerta:

```
  VIIRS375 B pasadas 109 | pixeles 156 | con bt<=t_bg+3: 1 | exceso minimo 3.00 K
  VIIRS375 F pasadas 114 | pixeles 150 | con bt<=t_bg+3: 1 | exceso minimo 3.00 K
  VIIRS750 B pasadas 26 | pixeles 31 | con bt<=t_bg+3: 0 | exceso minimo 3.11 K
  VIIRS750 F pasadas 14 | pixeles 14 | con bt<=t_bg+3: 0 | exceso minimo 3.07 K
```

Un píxel de 156 cae justo en 3,00 K, que es el redondeo a dos decimales de los campos persistidos.
El instrumento puede dar distinto de cero y acá da cero: sirve.

**La medición.** En las pasadas SIN primer pase:

```
  VIIRS375 B pasadas 194 | pixeles 397 | bt<=t_bg+3: 397 (100.0 %) | pasadas con ALGUN pixel sobre la compuerta: 0
  VIIRS375 F pasadas 62 | pixeles 78 | bt<=t_bg+3: 78 (100.0 %) | pasadas con ALGUN pixel sobre la compuerta: 0
       exceso bt-t_bg: min -7.18 | p25 -0.70 | mediana 0.58 | p75 1.93 | max 2.99
  VIIRS750 B pasadas 111 | pixeles 138 | bt<=t_bg+3: 138 (100.0 %) | pasadas con ALGUN pixel sobre la compuerta: 0
  VIIRS750 F pasadas 34 | pixeles 37 | bt<=t_bg+3: 37 (100.0 %) | pasadas con ALGUN pixel sobre la compuerta: 0
       otros caminos con pixeles en esas pasadas: {}
```

650 de 650 píxeles bajo la compuerta, en 401 pasadas, y ningún otro camino de detección con
píxeles. Si la otra diferencia entre pases (el pool de media y desviación) produjera píxeles por
su cuenta, habría alguno sobre los 3 K que el primer pase no tomó: no hay ninguno. **La causa que
el verificador dejó como sospecha queda medida: es la compuerta de temperatura.**

Y el segundo pase hace casi sólo eso, también cuando sí hay primer pase: en VIIRS 375 del brazo B,
de 425 píxeles "recapturados" sólo 21 están sobre la compuerta (404 están bajo); en F,
sólo 12 de 84. O sea que entre el 86 y el 95 % de lo que el contador llama recaptura de vecinos es
en realidad el primer pase sin compuerta. (Cota: `anomaly_pixels` no dice por qué pase entró cada
píxel; el conteo de píxeles bajo la compuerta nunca supera al de recapturados salvo en 1 pasada de
132, atribuible al redondeo.)

### No es propio de `max`

```
  VIIRS375 pos      n= 129 | F publica  124, SIN primer pase  30 (de esas, tampoco tenian primer pase en B:  28) || B publica  125, SIN primer pase  28
  VIIRS375 neg      n= 325 | F publica   10, SIN primer pase   4 (de esas, tampoco tenian primer pase en B:   4) || B publica   95, SIN primer pase  41
  VIIRS375 sin_info n= 332 | F publica   39, SIN primer pase  14 (de esas, tampoco tenian primer pase en B:  13) || B publica  125, SIN primer pase  64
  VIIRS750 pos      n=  16 | F publica   11, SIN primer pase   8 (de esas, tampoco tenian primer pase en B:   7) || B publica   11, SIN primer pase   7
  VIIRS750 neg      n= 562 | F publica    3, SIN primer pase   3 (de esas, tampoco tenian primer pase en B:   2) || B publica   30, SIN primer pase  15
```

Con `min` ya había 28 positivas de VIIRS 375 y 7 de VIIRS 750 que vivían sólo del segundo pase. El
recall de la réplica descansa en este camino desde antes de este A/B. Lo que cambia con `max` es
la **selectividad del camino**: en VIIRS 375 publica por esa vía el 23 % de las positivas (30 de
129) y el 1,2 % de las negativas limpias (4 de 325); con `min` eran 22 % y 12,6 % (41 de 325). En
VIIRS 750: 8 de 16 positivas contra 3 de 562 negativas (0,5 %); con `min`, 15 de 562.

### ¿Son creíbles esas 30 pasadas?

```
  SIN primer pase en F n=30
     MIROVA MW min 0.020 p25 0.050 mediana 0.070 p75 0.110 max 0.450
     nuestra F MW mediana 0.0743 | razon F/MIROVA: min 0.054 p25 0.640 mediana 1.034 p75 1.277 max 2.320 (n=30)
     razon dentro de 0.5 a 2.0: 22 de 30 | distancia cumulo-crater km: mediana 0.26 max 1.23 | n_pixels mediana 1.0
     exceso del pixel mas caliente sobre el fondo (K): min -3.16 p25 0.57 mediana 1.84 p75 2.39 max 2.99
     volcan: Lascar 3, Lastarria 2, Isluga 2, Tupungatito 1, PlanchonPeteroa 5, NevadosDeChillan 1, Villarrica 3, PuyehueCordonCaulle 6, Chaiten 7
  CON primer pase en F n=94
     MIROVA MW min 0.030 p25 0.110 mediana 0.190 p75 0.360 max 2.220
     razon F/MIROVA: min 0.004 p25 0.397 mediana 0.601 p75 0.979 max 3.333 (n=94)
     razon dentro de 0.5 a 2.0: 53 de 94 | distancia cumulo-crater km: mediana 0.27 max 1.28
```

Sí. Son las alertas más débiles de MIROVA (mediana 0,07 MW contra 0,19), están encima del cráter
(0,26 km de mediana, máximo 1,23 km, que es Lastarria y su campo fumarólico), son de un píxel, y
su magnitud calza con la de MIROVA mejor que la del resto: razón mediana 1,03 y 22 de 30 dentro
de un factor 2, contra 0,60 y 53 de 94. Por volcán la mediana agrupada no engaña: en los 8
volcanes donde hay de los dos grupos, la razón del grupo sin primer pase es del mismo orden que la del
grupo con primer pase del mismo volcán (Chaitén 1,22 y 1,27; Isluga 0,48 y 0,47; Láscar 0,38 y
0,50; Villarrica 1,03 y 1,01; Cordón Caulle 1,05 y 0,80). Dominan los volcanes del sur de cumbre
fría y valle tibio: Chaitén 7 de 8, Villarrica 3 de 4, Planchón Peteroa 5 de 8. Una sola es
dudosa como magnitud: Nevados de Chillán 2026-09-15 06:18, 0,0027 MW contra 0,05 de MIROVA.
El detalle una por una está en `out_h3.txt`, sección 4.

Las negativas limpias que publican por este camino en F son 4 en VIIRS 375 (Lastarria 2, a 2,24 y
1,24 km; Planchón Peteroa 1; Chaitén 1) y 3 en VIIRS 750 (Láscar, Isluga, Tupungatito), todas de
un píxel entre 0,04 y 0,10 MW. En VIIRS 750 las 3 negativas que sobreviven en F vienen TODAS de
este camino.

### ¿Fiel al paper o accidente?

Página 7 del PDF `documentacion/sp426.5.pdf` (índice 6), columna derecha, sección "Second run",
leída en la página renderizada a imagen: *"The last step is applied only if one or more pixels have
been detected by the previous tests, and focuses on refining the hotspot detection for the pixels
adjacent to those already flagged."* Y en la misma página, los Tests 2 y 3 no llevan ninguna
condición de temperatura.

Entonces, por la letra del paper, en una pasada sin ningún píxel activo el segundo pase **no
corre**. Que acá corra es una divergencia nuestra (la que S135 ya documentó como D2 y D19 y dejó
detrás de un flag apagado). Pero el resultado no es un accidente que fabrique detecciones ajenas
al paper: es **la compensación de dos divergencias que se anulan**. El primer pase tiene una
compuerta que el paper no tiene, y bota cráteres fríos que MIROVA sí detecta; el segundo pase, que
el paper no correría, los recupera porque no tiene la compuerta. Un primer pase literal (sin
compuerta) seguido de un segundo pase literal (condicionado) vería esos mismos píxeles en el
primer pase. Esta última frase es una **deducción, no una medición**: con el conjunto activo vacío
los dNTI y dETI son idénticos entre pases, pero el pool de media y desviación no, y no se corrió
el pipeline para comprobarlo. El antecedente medido más cercano es el A/B D22/D25 de S143, que
probó sacar la compuerta bajo `min` y quedó en NO ADOPTAR; nadie lo ha probado bajo `max`.

Cota de lo que está en juego si alguien condiciona el segundo pase sin sacar la compuerta
(`out_h3.txt`, sección 6): el recall de F caería a lo más a 94 de 129 en VIIRS 375 y 3 de 16 en
VIIRS 750, y perdería justo las pasadas que mejor calzan con MIROVA. Y lo mismo le pasaría a `min`
(97 de 129): no es un riesgo de la conectiva.

## H2. La magnitud que baja con `max`

### El fenómeno físico

Una fuente caliente sub-píxel rara vez cae entera en un píxel de 375 m. La energía se reparte: un
píxel "pico" que se lleva la mayor parte y uno o dos vecinos que reciben la cola, porque la fuente
está sobre el borde entre píxeles, porque la respuesta del sensor se traslapa entre muestras
vecinas, o porque el cuerpo caliente es extenso (el campo de Cordón Caulle). Ese vecino es real
pero débil: apenas se despega del paisaje. MIROVA lo suma cuando lo alerta (A99, A103).

### El mecanismo

Con `min` basta que el vecino supere el piso fijo C1 = 0,003. Con `max` tiene que superar además
la estadística de la escena, media más 5 desviaciones. En las 25 pasadas que bajan ese umbral
estadístico está por encima del piso en las 25 para el dNTI (mediana 0,0069, más del doble del
piso) y en 23 de 25 para el dETI (`out_h2.txt`, sección 3b). El pico lo pasa con holgura; el vecino
queda entre los dos umbrales y se cae. Que el vecino estaba entre los dos umbrales es deducción
(la única constante que difiere entre brazos es la conectiva, y el gránulo y el fondo son
idénticos); el dNTI de cada píxel no se persiste, así que el valor exacto queda SIN VERIFICAR.

Hay un efecto de segundo orden que el verificador no vio. En los cinco volcanes que restan un
fondo local de 3 x 3 píxeles (Cordón Caulle, Villarrica, Chaitén, Planchón Peteroa, Lastarria,
según `volcanoes.yaml`), ese fondo excluye a los píxeles alertados (`pipeline/vrp_regimes.py:96`).
Cuando el vecino tibio deja de estar alertado, **entra al fondo del pico**, el fondo sube y el pico
pierde magnitud aunque siga detectado. Por eso 3 de las 25 pasadas bajan sin perder ningún píxel.

### La medición

Control del instrumento: la magnitud publicada de VIIRS 375 es el núcleo F5' (pico más píxeles a
0,75 km, `pipeline/f5_core.py`). Reconstruido desde `anomaly_pixels`, coincide con lo publicado en
los 248 records (0 diferencias sobre 0,0002 MW).

```
#### 1. CUANTAS BAJAN: 25 | suben 0 | identicas 99
  resumen: {'mismo pico': 21, 'pierde pixeles que F ya no detecta': 22, 'pierde pixeles que F detecta pero quedan fuera del nucleo': 0, 'gana pixeles': 2, 'cambia el pico': 4}

#### 3. COMO ES EL PIXEL QUE DEJA DE DETECTARSE (n=32 pixeles en 22 pasadas)
   exceso BT sobre el fondo (K): min -7.58 | mediana 1.00 | max 6.60 | bajo la compuerta de 3 K: 25 de 32
   exceso BT del pixel PICO de esas pasadas (K): mediana 6.08
   pixel perdido es mas frio que su pico en 28 de 28
   el pixel perdido ERA el pico de B en 4 casos
   distancia al pico (km): mediana 0.49 max 0.66
   MW del pixel perdido: mediana 0.0486 | suma 1.582 | razon perdido/pico mediana 0.31
   fraccion de la magnitud de B que aportaban, por pasada: min 0.05 | mediana 0.23 | max 1.00
```

El píxel que se pierde es el vecino tibio: a medio kilómetro del pico (uno a dos píxeles), 1,0 K
sobre el fondo contra 6,1 K del pico, siempre más frío que su pico (28 de 28), con un tercio de la
energía del pico. Aportaba el 23 % de la magnitud de la pasada (mediana). 25 de los 32 estaban
bajo la compuerta de 3 K, o sea que en B habían entrado por el segundo pase (enlace con H3). En 4
pasadas lo que se pierde es el propio pico de B y F publica otro píxel del mismo cúmulo (Láscar
09-03, Tupungatito 09-13, Cordón Caulle 09-08 06:30 y 09-14 06:42).

Descomposición de los 1,776 MW que bajan: 1,581 MW se van con píxeles que dejan de detectarse,
0,110 MW entran con píxeles nuevos, y 0,304 MW se pierden en píxeles que siguen detectados, por el
fondo local que sube. Ese último término existe sólo en Cordón Caulle (0,295), Villarrica y
Chaitén.

### ¿A quién se parece MIROVA, pasada por pasada?

Error de cada brazo = valor absoluto del logaritmo de la razón contra MIROVA.

```
   las que bajan          n= 25 | B mas cerca 17 | F mas cerca  8 | iguales   0 | razon mediana B 0.954 F 0.736 | error mediano B 0.371 F 0.333
   las 124                n=124 | B mas cerca 17 | F mas cerca  8 | iguales  99 | razon mediana B 0.781 F 0.716 | error mediano B 0.503 F 0.510
     Chaiten              n=  1 | B mas cerca  0 | F mas cerca  1
     Isluga               n=  1 | B mas cerca  1 | F mas cerca  0
     Lascar               n=  4 | B mas cerca  4 | F mas cerca  0 | razon mediana B 0.580 F 0.520
     PuyehueCordonCaulle  n= 16 | B mas cerca  9 | F mas cerca  7 | razon mediana B 1.105 F 0.811 | error mediano B 0.283 F 0.255
     Tupungatito          n=  2 | B mas cerca  2 | F mas cerca  0
     Villarrica           n=  1 | B mas cerca  1 | F mas cerca  0 | razon mediana B 0.990 F 0.736
   prueba del signo sobre las que bajan (sin empates): B 17 contra F 8, p dos colas = 0.1078
   {'B bajo MIROVA (F se aleja mas)': 14, 'B sobre, F cruza bajo MIROVA': 5, 'B sobre, F sigue sobre (F se acerca)': 6}
   diferencia de medianas F - B: observado -0.065 | IC 95 % -0.150 a -0.004
```

Lectura estratificada, que es la que importa:

- **Fuera de Cordón Caulle (9 pasadas en 5 volcanes): B gana 8 a 1.** Son volcanes donde ya
  quedábamos bajo MIROVA (Láscar 0,58, Tupungatito 0,63) y perder el vecino nos aleja más. Esto es
  coherente con A99: el déficit era de vecinos tibios, y `max` bota más vecinos tibios.
- **En Cordón Caulle (16 de las 25): empate, 9 a 7**, y el error mediano de F es algo menor (0,255
  contra 0,283), porque ahí B sobre-estimaba (1,10) y F sub-estima (0,81). Es el volcán de anomalía
  extensa donde el cúmulo es grande y el fondo local amplifica el efecto.
- **En 99 de 124 pasadas no cambia nada**, y en 6 de los 9 volcanes la mediana no se mueve. La
  caída de la paridad agrupada de 0,781 a 0,716 es real (el intervalo no cruza cero, por poco) pero
  sale de 25 pasadas, 16 de un volcán.
- Por zona del barrido: en el nadir B gana 8 a 0; en el medio y el borde es empate (4 a 4, 5 a 4).
  En el nadir el píxel es chico y el vecino tibio es energía real de la misma fuente; hacia el
  borde el píxel crece y es más probable que el "vecino" sea ruido. Son 8, 8 y 9 casos: es
  una pista, no un resultado.

Veredicto de H2: **la pérdida es del vecino tibio, MIROVA se parece algo más a B, y la evidencia
es débil** (17 contra 8, p = 0,11, n chico y concentrado en un volcán). No alcanza para decir que
`max` empeora la magnitud de forma establecida; alcanza de sobra para no decir que la deja igual.

## Qué implica para la propuesta de adopción

1. **H3 no es una objeción a `max`.** El recall que sostiene el segundo pase existe igual con
   `min` (28 de esas 30), las pasadas son físicamente las mejores del conjunto, y con `max` ese
   camino se vuelve selectivo (1,2 % de las negativas contra 23 % de las positivas). La propuesta
   debe decirlo así y no como "el recall de F descansa en una diferencia de implementación".
2. **Pero la propuesta debe amarrar una dependencia**: el recall de la réplica, con cualquier
   conectiva, depende de que el segundo pase siga corriendo sin condición MIENTRAS el primer pase
   tenga la compuerta de 3 K. Condicionar el segundo pase (D2, D19) sin sacar la compuerta (D22)
   cuesta hasta 30 de 124 positivas en VIIRS 375 y 8 de 11 en VIIRS 750. Las dos divergencias se
   tienen que tocar juntas o no tocarse.
3. **H2 se declara como costo conocido y acotado**: baja en 25 de 124, nunca sube, 8,5 % de la
   suma; el píxel que se pierde es energía real de la misma fuente; MIROVA se parece más a B en 17
   de 25, sin significancia. El costo se concentra en Cordón Caulle y en los volcanes donde ya
   estamos bajo MIROVA. Queda como criterio a vigilar en la ventana completa, con la prueba
   pareada por volcán y no con la mediana agrupada.
4. El segundo pase no está haciendo el trabajo que su nombre dice: entre 86 y 95 % de lo que
   recaptura son píxeles bajo la compuerta, no vecinos de un activo. Cualquier texto que explique
   el detector tiene que describirlo como lo que es hoy.

## LO QUE NO CUBRÍ

- **No corrí el pipeline.** La compuerta de temperatura como causa de H3 está medida por
  reconstrucción desde campos persistidos (650 de 650, con control), no por una corrida con la
  compuerta apagada. Que un primer pase sin compuerta vería esos mismos píxeles bajo `max` es
  deducción: SIN VERIFICAR.
- **El dNTI y el dETI por píxel no se persisten**: que el vecino tibio de H2 quede "entre el piso
  C1 y media más 5 desviaciones" es deducción por descarte (una sola constante distinta entre
  brazos, comprobada en `pipeline.profile`), no lectura del valor.
- `anomaly_pixels` no dice por qué pase entró cada píxel ni guarda más de 100 por record; la
  atribución al segundo pase es por conteo (píxeles bajo la compuerta contra recapturados).
- **MODIS**: fuera de alcance. Con `max` el detector MODIS se apaga (lo dice la lectura original).
- **VIIRS 750 en H2**: no medido; sólo 11 positivas publicadas.
- La ventana del 18 al 20 de septiembre, el run de reparación 35558196104 y los brazos G y H.
- La **posición con dirección** contra MIROVA (TIF UTM, A106, A107): las distancias al cráter son
  escalares. Que el cúmulo esté a 0,26 km del cráter no prueba que sea el mismo objeto que MIROVA
  alertó; la coincidencia de magnitud (razón 1,03) es el segundo apoyo, no una prueba.
- Si MIROVA reportó más de una alerta a 2 minutos de la pasada se usó la mayor, igual que el
  verificador; no revisé cuántas pasadas tienen más de una.
- La magnitud de MIROVA del scraper viene redondeada a 0,01 MW: en alertas de 0,02 a 0,05 MW la
  razón tiene un error de redondeo de 10 a 25 %, que afecta sobre todo al grupo sin primer pase.
- El diff efectivo de perfiles lo corrí sobre el `main` de hoy, no sobre el commit con que corrió
  el run (SIN VERIFICAR que sean el mismo código).
- No leí el resto del paper buscando otra mención de temperatura en los Tests 2 y 3; me apoyé en
  la página 7 renderizada y en lo ya documentado en D22.
