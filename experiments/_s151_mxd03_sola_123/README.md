# Probe S151, tarea 1.23: MxD03 sola, contra un nulo con distribución y una vara de otro instrumento

**Estado: versión 2, escrita y probada con datos sintéticos, NO corrida.** Este README fija la población,
los brazos, la vara, los estados y el criterio antes de la primera corrida. Lo sella Nicolás después de
que un verificador con contexto limpio lo revise (regla 1.6 del loop). La decisión de producción sigue
siendo suya (A45): nada de esto toca `pipeline/`, `pipeline/store.py` ni `pipeline/profiles/`.

La versión 1 (#846, head `4cc5e0134`) la revisó un verificador con contexto limpio y la dio por «sellable
con arreglos» (informe fuera del repo: `C:\Users\nmend\AppData\Local\Temp\claude\verif_123\VERIFICADOR.md`,
scripts en la misma carpeta). La versión 2 aplica:

1. **Bloqueante 1, el nulo en píxeles se rompía con el bow tie.** El nulo pasa a tener el **tamaño en km**
   del corrimiento real (sección «El nulo»), el jacobiano de la anotación en píxeles se calcula sobre un
   barrido entero, hay un caso sintético con la grilla en diente de sierra que falla con el jacobiano
   viejo, y se informa por cenit cuánto perturba el nulo frente a M en las unidades que consume el
   pipeline (anotación `tamano_del_nulo`).
2. **Bloqueante 2, «la fragilidad es del Test 1, no de MxD03» estaba sobredicha.** La frase se corrige y
   la lectura 4 se pre-registra con signo, separando alertas de negativos limpios, con su control.
3. Menores: la justificación de K = 20 se corrige (K = 19 también cumple p ≤ 0,05), la hipótesis del
   04-20 se baja a lo que es, y la vara se informa también con el centro del píxel caliente, sin 3 × 3.

## Por qué

La 1.21 (`experiments/_s151_mxd03_cumulo_121/`, resultado y verificador en `resultado/` de la rama
`loop/activo`) dejó a **MxD03 sola** (la posición oficial, con la etiqueta de producción) ni refutada ni
probada:

- Pierde 2 alertas protegidas de MIROVA, Láscar Terra 2026-04-20 y 2026-04-30 01:30. En el volcán no
  cambió nada: el cúmulo queda incluso más cerca del cráter. Lo que cambia es la etiqueta: el Test 1
  integrado deja de disparar (k de 4,81 a 2,56 y de 3,28 a 2,83), el hotspot de escena salta al borde del
  Salar de Atacama a 19 y 21 km, y la etiqueta MODIS sale de ese hotspot (asimetría A46).
- Un corrimiento al azar del mismo tamaño en km (brazo R, **un solo rumbo por gránulo**) pierde 4 por el
  mismo mecanismo, y coincide con M sólo en una. M gana 9 protegidas; R, 5.
- Chillán Aqua 2026-10-12 07:20 (cenit 59°, borde del barrido): con MxD03 la selección anclada al cráter
  elige otro cúmulo, a 9,7 km. Ésa sí es de posición.
- El verificador de la 1.21 midió que su nulo era anisótropo: sobre 50° de cenit movía la grilla 24 %
  más píxeles que MxD03. El de esta tarea (versión 2) mostró que esa unidad no es la que usa el pipeline
  en ese tramo (sección «El nulo»).

Con un solo sorteo no hay contra qué comparar «M pierde 2» y «M gana 9». Y la única vara de posición era
nuestra propia etiqueta, que es justo lo que está en duda. Este probe agrega las tres cosas que faltan:
un nulo con distribución y del tamaño correcto, una vara de otro instrumento y el mecanismo del Test 1.

## Lo que ya se midió, sin correr nada (artefactos de la 1.21)

Dos de las preguntas se pudieron medir sobre los JSON que la 1.21 ya guardó, sin bajar L1B. Son medidas,
no el veredicto: el veredicto sale del probe.

### El Test 1 MODIS vive en su propio piso de ruido; la dirección del cambio con MxD03 queda por medir

`sensibilidad_test1_121.py` (salida en `sensibilidad_test1_121_salida.txt`):

| cenit | gránulos | Test 1 calculado en C | k de C (mediana) | píxeles en el disco (geometría) | k del ruido puro |
|---|---|---|---|---|---|
| 0 a 10° | 31 | 30 | 1,79 | 28,0 | 2,11 |
| 10 a 20° | 62 | 59 | 2,33 | 25,7 | 2,02 |
| 20 a 30° | 64 | 51 | 1,93 | 21,5 | 1,85 |
| 30 a 50° | 90 | 9 | 1,87 | 13,6 | 1,47 |
| más de 50° | 222 | 0 | | 6,4 | 1,01 |

Lo que pasa en el píxel: el Test 1 suma el exceso de radiancia **recortado a cero** de los ~28 píxeles de
1 km del disco de 3 km y lo divide por la desviación del anillo de 1 a 3 km por la raíz de 28. Con el
recorte, el ruido solo ya da k ≈ 0,399·√28 ≈ 2,1 (el defecto que S146 midió como D30, con la corrección
`ENABLE_TEST1_NULL_CORRECTED` apagada). El umbral es 3. Las medianas de k medidas en C (1,8 a 2,3) caen
justo en ese piso: el Test 1 MODIS, la mayor parte del tiempo, está midiendo el tamaño del disco y no el
calor. Sobre ~30° de cenit ni siquiera se calcula, porque el anillo baja de los 20 píxeles mínimos.

Correr la grilla cambia qué píxeles caen en el disco y cuáles en el anillo, y con 25 píxeles la mediana y
la desviación del anillo se mueven. Medido, con el mismo tamaño de corrimiento en km (mediana 1,3 km):

| | n | \|Δk\| mediana | \|Δk\| por km | M mueve más / R mueve más | cruces del umbral respecto de C |
|---|---|---|---|---|---|
| M (MxD03) | 126 | 0,515 | 0,416 | 59 | 17 apagan + 19 encienden, de 149 |
| R (azar, 1 rumbo) | 126 | 0,595 | 0,462 | 65 | 15 apagan + 14 encienden, de 149 |

MxD03 mueve k **tanto como** el azar: el verificador midió el intervalo de la diferencia de medianas de
|Δk| en [-0,21; +0,20] y el signo M contra R en 69 contra 72 (p = 0,87); y los cruces (36 contra 29) están
dentro del ruido de conteo. Lo que **sí** es propiedad del Test 1 a 1 km es la magnitud: una protegida que
C publica con k = 3,28 tiene 0,28 de margen sobre un umbral que cualquier corrimiento de ese tamaño mueve
en 0,5.

Lo que **no** está probado es que la dirección sea azar. El verificador separó los mismos 126 pares por
etiqueta de MIROVA y con signo (`a_k2.py` en su carpeta): donde MIROVA alertó, M sube k más que R en 33
contra 18 (p = 0,049; mediana de Δk +0,15 contra -0,09); en los negativos y sin información, M lo baja
(30 contra 43, p = 0,16). En el volcán eso es lo que haría una posición **mejor**: meter el calor en el
disco donde lo hay y sacarlo donde no. Es un indicio de un solo sorteo de R, no una medida; por eso la
lectura 4 de abajo lo mide con los 20 nulos.

Lo que queda SIN VERIFICAR, y que el probe mide con un espía sobre `compute_test1_mir`: **por qué** el
salto del 04-20 es tan grande (2,25 con 0,39 km). Una hipótesis es que el píxel más caliente cruce el
borde del anillo de 1 km, pero es débil: el fondo es mediana y MAD de unos 25 píxeles, robustos a un
píxel, y el píxel sigue sumando en ΔL porque el anillo está dentro del disco de 3 km. No se anuncia como
la explicación probable. El espía guarda n del disco, n del anillo, fondo, desviación, ΔL integrado, k y
dónde cae el píxel caliente, en cada brazo, que es lo necesario para descartarla o no.

### El borde del barrido: cuántos más hay «como Chillán»

`saltos_de_cumulo_121.py` (salida en `saltos_de_cumulo_121_salida.txt`) cuenta los gránulos donde el
cúmulo publicado de M queda más lejos del de C que el propio corrimiento más 1,5 km (otro objeto, no el
mismo corrido; la tolerancia de `tipos_de_cambio` de la 1.21):

| cenit | M: otro objeto | R (1 rumbo): otro objeto | M: el mismo, reubicado |
|---|---|---|---|
| 0 a 20° | 15 | 17 | 31 |
| 20 a 35° | 12 | 10 | 25 |
| 35 a 50° | 11 | 10 | 12 |
| más de 50° | **41** | 30 | 16 |
| todos | 79 de 470 | 67 | 84 |

Chillán 10-12 07:20 es uno de 41 sobre 50°. Con la etiqueta de producción, de esos 79 saltos 6 apagan una
publicación y 2 encienden una; ninguna de las 6 es protegida (las únicas protegidas que M pierde son las
dos de Láscar, donde el cúmulo es el mismo). Dos cosas que no se ven en la pregunta original: en sólo
84 de 470 gránulos el cúmulo es el mismo reubicado (en el resto cambian sus píxeles o su magnitud, porque
las cercas del ROI dependen de la posición), y sobre 50° M salta más que el único sorteo de R. Con un
sorteo eso no es una medida: el probe da los 20.

## Los brazos

Todos con el pipeline de producción sobre el mismo L1B (`calculate_vrp` + `store.append_record` en un
directorio temporal + el predicado del tablero ejecutado con node, A97), con la **etiqueta de producción**
(`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`; el job guarda el valor que vio y el evaluador da
INVALIDO si no es `False`). Reutiliza `probe_etiquetas.py` (1.17) y `probe_cumulo.py` (1.21).

| brazo | posición | qué aísla |
|---|---|---|
| **C** | `_interp_geo` | producción |
| **M** | MxD03 | la posición oficial |
| **R00 a R19** | `_interp_geo` trasladada en bloque, 20 rumbos | el nulo: un corrimiento del mismo tamaño en km, sin información |
| **C'** | `_interp_geo` por el parche de M (2 gránulos por job) | que el parche no fabrica diferencias |

La etiqueta desde el cúmulo (brazos CC, MC, RC de la 1.21) no entra: la 1.21 ya midió que encenderla
publica unas 3.500 veces de más, y la pregunta acá es la posición sola.

### El nulo, en km (versión 2: el píxel no era la unidad correcta)

**Qué falló en la versión 1.** La versión 1 fijaba el tamaño del nulo en píxeles, con un jacobiano de ±2
líneas sobre la grilla de `_interp_geo`. Hacia el borde del barrido los barridos de 10 líneas se traslapan
(bow tie): las filas de amarre del L1B caen casi en el mismo punto y `_interp_geo` deja una grilla cuyo
espaciado a lo largo de la traza alterna tramos de 5 líneas de f y 2 - f km (f la huella, hasta ~1,95 km).
Con ±2 líneas el jacobiano medía un solo tramo (entre 0,05 y 1,95 km por línea). El verificador estimó,
con un modelo que usa la misma interpolación del pipeline y los corrimientos de la 1.21 (`nulo_km.py`,
SIN VERIFICAR sobre un gránulo real), que sobre 50° de cenit, en 67 de 223 gránulos, el nulo movía la
grilla más del doble de km que MxD03 (p90 de 3 a 8 veces), en la dirección que empuja a adoptar. Los
INVALIDO de entonces no lo veían, porque comparaban la traslación consigo misma.

**Por qué km.** Todo lo que el pipeline MODIS hace con la posición pasa por distancias en km al cráter:
el inner, el ROI de 25 km, el disco de 3 km y el anillo de 1 km del Test 1. Trasladar la grilla cambia
cuántos centros de píxel caen a cada lado de esos círculos, y eso es lo que mueve la detección. Para un
círculo grande frente al píxel, el área que barre el borde al trasladar d km es ~4 R d, igual en cualquier
dirección. Medido (`invariante_km.py`, `invariante_km_salida.txt`), sobre una grilla regular de píxeles de
1 × 2 km y 36 rumbos de 2 km:

| círculo | CV entre rumbos, tamaño fijo en km | fijo en píxeles |
|---|---|---|
| 3 km | 0,07 | 0,29 |
| 5 km | 0,06 | 0,30 |
| 25 km | 0,03 | 0,24 |

O sea que la «anisotropía del 24 %» de la 1.21 se midió en una unidad que el pipeline no usa en el tramo
donde se midió; el nulo de la 1.21 (en km) tenía la unidad correcta y le faltaba la distribución. El
píxel sólo importaría para estructuras del tamaño del píxel (el anillo de 1 km), y el Test 1 ya no se
calcula sobre ~30° (9 de 90 entre 30 y 50°, 0 de 222 sobre 50°).

**Lo que el km no arregla, dicho antes de correr.** Sobre la grilla con bow tie **ninguna** de las dos
unidades es invariante (CV de 0,18 a 0,49 en km y de 0,23 a 0,33 en píxeles, misma salida): los centros
de píxel de `_interp_geo` se amontonan de a pares cada 5 líneas, y cuántos cruzan un borde depende de si
la traslación va a lo largo o a lo ancho. Por eso la versión 2 mide, por gránulo, cuánto **perturba** cada
nulo frente a M en esa misma unidad (centros que cambian de lado del disco de 1 y 3 km y del inner) y lo
informa por cenit en `tamano_del_nulo`, junto con la razón de módulos en píxeles. Las lecturas que
dependen del borde del barrido (la 5 y los cortes sobre 50°) se leen con esa anotación al lado.

**Cómo se arma, por gránulo:**

1. el corrimiento real en el cráter (`_interp_geo` menos MxD03, en km, como la 1.21);
2. 20 rumbos geográficos equiespaciados cada 18°, con una fase al azar determinista por gránulo (sha1 de
   la clave con la sal `s151-tarea-1.23-rumbos`), todos con el **módulo en km** del corrimiento real;
3. traslación rígida de toda la grilla por ese vector (es un campo suave, no ruido píxel a píxel);
4. como anotación, el módulo en píxeles del real y de cada nulo con el jacobiano local sobre **un barrido
   entero** (±5 líneas a lo largo, ±2 frames a lo ancho), que promedia los dos tramos del diente de
   sierra y da el avance medio de 1 km por línea en cualquier fase.

El evaluador da INVALIDO si un nulo **pedido** no tiene el km del corrimiento real (es el chequeo del
diseño) o si el **aplicado** difiere del pedido en más de 10 m (es aritmética de la traslación: se mide
en el mismo píxel donde se pidió, así que sólo atrapa un error de código), o si los rumbos no quedan
cada 18°.

**Por qué 20.** Con K nulos, el p de Monte Carlo más chico posible es 1/(K+1). Con el criterio
p ≤ 0,05 del evaluador, K = 19 ya alcanza (1/20 = 0,050); se toman 20 porque dejan el mínimo un poco bajo
el corte (1/21 = 0,048) y caben en el presupuesto. No es el mínimo. Pasar a 40 casi no cambia el poder
(tabla de «Poder») y duplica el tiempo. Los 20 nulos de un gránulo no son independientes (rumbos vecinos
dan resultados parecidos), así que el p es nominal.

**Por qué equiespaciados.** Cada rumbo por sí solo es uniforme (un test lo comprueba con 4.000 claves),
y dentro de un gránulo los 20 cubren el círculo parejo, que es lo que importa para decir de cada pasada
protegida en cuántos rumbos se pierde.

## La vara de posición: VIIRS 375 de la misma noche

**Por qué VIIRS.** Es otro sensor, en otro satélite, con su propia geolocalización por píxel (VNP03IMG y
VJ103IMG), un píxel de 375 m, y pasa la misma noche que Terra y Aqua. No es nuestra etiqueta ni nuestro
predicado sobre MODIS. La pregunta física es simple: el objeto caliente de esa noche, ¿dónde lo pone
VIIRS, y cuál de las dos geolocalizaciones MODIS lo pone más cerca?

`construir_vara_viirs.py` la congela **antes de correr** en `vara_viirs.json` (commit de datos y commits
de Mirova-v1 guardados en `meta`; la referencia es la misma de `poblacion.json`). Una pasada VIIRS entra si:

- es VIIRS 375 (`VIIRS_SNPP`, `VIIRS_NOAA20`, `VIIRS_NOAA21`; A48), nocturna, a 6 h o menos del gránulo;
- el tablero la publica (predicado con node);
- su cúmulo **no** viene del Test 1. Con fuente Test 1 el cúmulo VIIRS es la componente conexa de los
  píxeles con exceso positivo del disco, y con el exceso recortado el ruido aporta en todo el disco: su
  centroide tiende al centro del disco, que es el ancla. Esa posición la pone el ancla, no el objeto, y
  premiaría a la geolocalización que deje el cúmulo MODIS más cerca del ancla.
- nivel **estricto**: además MIROVA alertó esa pasada VIIRS (el árbitro externo dice que hay un objeto).

La posición de cada pasada es el centroide de su cúmulo primario (no `final_hotspot_*`, que con fuente
`test1_roi` es el ancla misma: distancia 0,0 km en Láscar). La de la noche, la mediana por componente.

**Qué posición MODIS se compara.** La principal es el **píxel MIR más caliente cerca del cráter elegido
por índice** (el mismo píxel físico del L1B en todos los brazos), con su centroide de 3 × 3 pesado por el
exceso. Así se compara la geolocalización pura, sin la selección del cúmulo en el medio. Al lado se
informa la variante con el centro del píxel caliente solo (`pico_centro_estricta_pos`): el 3 × 3 pesado
por el exceso sobre la mediana mete el gradiente de terreno de los vecinos (MIR absoluto, A69), común a
C y M pero que, si se acercara al tamaño de |C - M|, proyectaría con signo opuesto en Terra y Aqua. La selección
es simétrica: entran los píxeles a menos del inner del cráter con `_interp_geo` **o** con MxD03. El
centroide del cúmulo publicado se informa al lado.

**Cobertura** (`construir_vara_viirs_salida.txt`): 166 de 471 gránulos tienen vara estricta y 312 amplia.
El **conjunto principal** (gránulo MODIS con alerta de MIROVA y vara estricta) tiene **76 gránulos en 63
noches: 70 de Láscar y 6 de Nevados de Chillán; 30 Terra y 46 Aqua**; por cenit, 33 bajo 20°, 29 de 20 a
35°, 12 de 35 a 50° y **sólo 2 sobre 50°**. Dentro de una noche las pasadas VIIRS estrictas quedan a
0,1 km de su mediana; en Láscar la vara cae a 0,13 km (mediana) del ancla del cráter
(`vara_estricta_al_ancla_mediana_km`).

**El control de sesgo de la vara.** De noche Terra y Aqua corren la grilla en sentidos opuestos (medido
sobre la 1.21, `saltos_de_cumulo_121_salida.txt`: bajo 35° la mediana de C → M es 0,32 km al norte y
0,41 al este en Terra, y 0,26 al sur y 0,50 al oeste en Aqua). Un sesgo constante de la
vara favorecería a M en un satélite y a C en el otro. Por eso un veredicto de posición exige el mismo
signo en los dos.

**El resultado de la vara es casi previsible, y se dice antes.** El probe de #828 ya midió el píxel
brillante a 0,13 a 0,35 km del cráter con MxD03 y a 1,0 a 1,3 km con `_interp_geo`, casi todo en Láscar.
La vara VIIRS no hace una pregunta nueva: agrega que la respuesta no dependa de la coordenada del ancla.

**Los TIF de MIROVA, descartados como vara principal.** La grilla UTM de MIROVA (A106) duró del
2026-09-14 06:36 al 2026-09-15 06:24, y en ese tramo la muestra tiene **un solo gránulo** (Chaitén, un
negativo limpio): sin poder. Los TIF en EPSG:4326 (mayo a 2026-09-22) exigen verificar antes su
georreferencia, que es otra tarea. Quedan como opción para validar la vara VIIRS, no para decidir.

## Qué se mide

Por gránulo, además de lo de la 1.21 (`resumir` de `probe_cumulo.py`):

- el jacobiano (±5 líneas, ±2 frames), el corrimiento real en km y en píxeles y, por nulo, rumbo,
  vector, km pedido, km aplicado, módulo en píxeles y su razón contra el de M;
- por brazo, cuántos centros de píxel cambian de lado del disco de 1 y 3 km y del inner frente a C;
- por brazo, lo que vio el Test 1 (espía sobre `compute_test1_mir`): `triggered`, `n_roi`, `n_bg`,
  `L_bg`, `sigma_bg`, `delta_L_integrated`, `k_sigma_observed`, la distancia y temperatura del píxel más
  caliente del disco, si cae en el anillo de fondo y qué fracción de ΔL aporta;
- el píxel por índice y su posición en cada brazo (centroide 3 × 3 y centro solo).

## Estados y criterio (fijados antes de correr)

**Veredicto global**, en este orden:

1. **INVALIDO**: algún C' difiere de su C; la etiqueta no es la de producción; un nulo pedido no tiene
   el km del corrimiento real o el aplicado difiere del pedido (10 m); los rumbos no quedan cada 18°; o
   el espía del Test 1 vio otra cantidad de llamadas en un brazo que en C.
2. **INCOMPLETO** (A108): los artefactos traen más de un commit o alguno no lo trae; falta un medio job;
   falta cualquier gránulo pedido (los de `experiments/_s151_mxd03_cumulo_121/archivo_cmr.json` no son
   pedidos); los brazos no tienen la misma cantidad de gránulos; o un medio job no corrió C'. Se repite el
   job sobre el mismo código.
3. Si no, **MEDIDO**, con las lecturas de abajo.

**«Adoptable en la réplica» no cambia de definición**: M no pierde ninguna protegida y su balance contra C
sale MEJORA (evaluador de la 1.21, sin tocar). **Se sabe de antemano que no va a salir**: M es
determinista (mismo L1B, mismo código) y repetirá las 2 pérdidas de Láscar, salvo deriva de código. Este
probe no busca volver adoptable a MxD03 por la letra; busca decirle a Nicolás **por qué** cae y si la
posición misma es mejor.

**Lectura 1, la regla 1 en las dos direcciones contra el nulo.** Se cuentan las protegidas que M pierde
de las que C publica (L) y las que C pierde de las que M publica (G), y lo mismo para cada nulo contra C.
Con el rango de Monte Carlo (p = (1 + nulos que igualan o pasan a M) / 21):

| estado | condición |
|---|---|
| PERDIDAS ESPECIFICAS DE MXD03 | p de la cola alta de L ≤ 0,05 |
| MENOS PERDIDAS QUE EL AZAR | p de la cola baja de L ≤ 0,05 |
| PERDIDAS COMO EL AZAR | ninguna de las dos |

y lo mismo para G (GANANCIAS ESPECIFICAS DE MXD03, MENOS GANANCIAS QUE EL AZAR, GANANCIAS COMO EL AZAR)
y para el neto G - L. Por pasada protegida se informa en cuántos de los 20 nulos se publica: es la
fragilidad de esa pasada, sin umbral.

**Lectura 2, el balance de la regla 2**: el Δ de M contra C con su intervalo (MEJORA / EMPEORA /
INDETERMINADO, como en la 1.21) y su rango entre los 20 Δ de los nulos (BALANCE MEJOR, PEOR o COMO EL
AZAR).

**Lectura 3, la vara.** Por gránulo, dd = |C - v| - |M - v| (km; positivo, M más cerca), λ = proyección
de (v - C) sobre (M - C) en unidades de |M - C| (1 donde dice M, 0 donde dice C) y el residuo
perpendicular. Intervalo al 95 % de la mediana de dd por bootstrap de noches (Terra y Aqua de una noche
comparten v), 1.000 remuestreos con semilla fija. **El nulo del estadístico se mide** (A110): los nulos k
y k + 4 son dos posiciones sin información separadas 1,18 veces |C - M|; intercambiarlos sólo cambia el
signo de su dd, así que su mediana es 0 por construcción, y las 20 medianas de esos pares dicen cuánto
«prefiere» la vara una posición sobre otra por azar con la geometría y el ruido reales. Estados, en este
orden:

| estado | condición |
|---|---|
| SIN VARA | menos de 10 gránulos o de 5 noches |
| MXD03 MAS CERCA | el intervalo queda sobre 0, la mediana de dd supera en valor absoluto las 20 medianas del nulo, y Terra y Aqua (con 5 gránulos o más cada uno) dan mediana positiva |
| INTERP MAS CERCA | lo mismo bajo 0 |
| (MXD03 o INTERP) MAS CERCA SIN CONTROL DE SESGO | como arriba, con un solo satélite con 5 gránulos o más |
| SESGO POR SATELITE | el intervalo y el nulo deciden, pero los satélites dan signos opuestos |
| INDECIDIBLE | cualquier otro caso |

La principal es la del píxel por índice, nivel estricto, gránulos MODIS con alerta. Se informan al lado:
todos los gránulos con vara estricta, el centroide del cúmulo, y la vara amplia. También el rango de la
mediana de |M - v| entre las de los 20 nulos (M MAS CERCA, MAS LEJOS o COMO EL AZAR) y los cortes por
satélite y cenit.

**Lectura 4, el Test 1, sin y con signo.** Sin signo: cuántos gránulos cambian el disparo del Test 1
respecto de C con M, contra la distribución de los 20 nulos (MXD03 CRUZA MAS QUE EL AZAR, MXD03 CRUZA
MENOS QUE EL AZAR, o PROPIEDAD DEL TEST 1). **Con signo** (versión 2, bloqueante 2), por separado en las
alertas de MIROVA (lab `pos`) y en los negativos limpios: la mediana de k_X - k_C en los gránulos con Test
1 calculado en los dos, y los cruces de 0 a 1 y de 1 a 0, de M y de cada nulo, con M ubicado entre los 20.
Por etiqueta: M SUBE K MAS QUE EL AZAR, M BAJA K MAS QUE EL AZAR o M COMO EL AZAR. Junto:

| alertas | negativos limpios | estado |
|---|---|---|
| M SUBE | M BAJA | SENAL DE POSICION MEJOR (el Test 1 ve más calor donde MIROVA lo vio y menos donde no) |
| M BAJA | M SUBE | SENAL DE POSICION PEOR |
| COMO EL AZAR | COMO EL AZAR | SIN DIRECCION (PROPIEDAD DEL TEST 1) |
| cualquier otra combinación | | MIXTO |

Control (A110, A116): con nulos que suben y bajan k por igual y M que sube en alertas y baja en negativos,
sale SENAL DE POSICION MEJOR; con M igual a un nulo, sale SIN DIRECCION
(`test_test1_con_signo_separa_alertas_de_negativos`). Además, la descomposición de
log k = log ΔL - log σ - ½ log n en los cambios C → M y C → nulos, y cuántas veces el píxel caliente
entra o sale del anillo, y cuántas de esas coinciden con un cruce del umbral.

**Lectura 5, el borde del barrido.** Por cenit, cuántos cúmulos de M son otro objeto (se mueven más que
el corrimiento más 1,5 km) contra los 20 nulos (el corrimiento de cada nulo es el suyo): MXD03 SALTA MAS,
MENOS o COMO EL AZAR, con la lista de los saltos de M que cambian la publicación.

**Anotaciones** que no cambian nada: el tamaño del nulo por cenit (`tamano_del_nulo`), C contra lo
guardado en `data/` (deriva) y, en local con `--art121`, C y M contra los de la 1.21.

## Lo que cada resultado le diría a Nicolás

| vara | pérdidas | lectura |
|---|---|---|
| MXD03 MAS CERCA | COMO EL AZAR | MxD03 pone el calor donde lo ve VIIRS, y las 2 pérdidas son lo que cualquier corrimiento de ese tamaño rompe en un Test 1 que vive en su piso de ruido. Si además la lectura 4 con signo da SENAL DE POSICION MEJOR, las pérdidas son el precio de una posición mejor sobre una etiqueta frágil. La letra de la regla 1 sigue bloqueando: adoptar MxD03 exige antes resolver esa fragilidad o que Nicolás decida la excepción (A45) |
| MXD03 MAS CERCA | ESPECIFICAS | MxD03 está mejor ubicada pero rompe más de lo que rompe el azar: mirar cada pasada antes de cualquier cosa |
| INTERP MAS CERCA | cualquiera | MxD03 no entra. Sería un resultado raro (MxD03 es el producto oficial): buscar primero un error en la vara o en el probe |
| INDECIDIBLE, SESGO POR SATELITE o SIN VARA | cualquiera | la vara no decide; queda la letra de la regla 1 y las lecturas contra el nulo |

En cualquier caso la vara habla **de Láscar** (70 de 76) y de cenit bajo y medio: no contesta el borde del
barrido (2 gránulos sobre 50°). El borde se contesta sólo con la lectura 5, contra el nulo, sin vara
externa.

## Poder, dicho antes de correr

**El rango de la regla 1** (`poder_nulo.py`, `poder_nulo_salida.txt`). M es determinista; lo incierto es el
nulo. Con nulos binomiales homogéneos (cada protegida que C publica se pierde con probabilidad qL; cada
una que no publica se gana con qG). El único sorteo de la 1.21 dio qL ≈ 0,44 y qG ≈ 0,135:

| | qL o qG | P(un nulo llega a lo de M) | P(estado ESPECIFICO), K = 20 | K = 40 |
|---|---|---|---|---|
| pérdidas (M: 2 de 9) | 0,10 | 0,225 | 0,006 | 0,000 |
| | 0,44 | 0,956 | 0,000 | 0,000 |
| ganancias (M: 9 de 37) | 0,10 | 0,009 | 0,830 | 0,947 |
| | 0,135 | 0,054 | 0,331 | 0,359 |
| | 0,20 | 0,314 | 0,001 | 0,000 |

Lectura: si el nulo se parece al único sorteo de la 1.21, las pérdidas de M saldrán COMO EL AZAR casi
seguro, y las ganancias saldrán ESPECIFICAS una de cada tres veces. Decir que M gana más que el azar
exige que el nulo gane bastante menos que 5 de 37. La población no da para más: hay 46 protegidas en
total y C publica sólo 9.

**La vara** (`poder_vara.py`, `poder_vara_salida.txt`, 60 simulaciones por escenario con la geometría real
del conjunto principal y la función de decisión del evaluador):

| verdad | ruido del píxel MODIS, de la vara | sesgo de la vara | estado |
|---|---|---|---|
| donde dice M | 0,3 / 0,15 km y 0,5 / 0,3 km | ninguno | MXD03 MAS CERCA 1,00 |
| donde dice C | 0,3 / 0,15 y 0,5 / 0,3 | ninguno | INTERP MAS CERCA 1,00 |
| a medio camino | 0,3 / 0,15 | ninguno | INDECIDIBLE 1,00 |
| donde dice M | 0,3 / 0,15 | 0,5 km al este | MXD03 MAS CERCA 1,00 |
| a medio camino | 0,3 / 0,15 | 1,0 km al este | INDECIDIBLE 0,98; SESGO 0,02 |
| donde dice M | 0,3 / 0,15 | 1,5 km al este | MXD03 0,93; INDECIDIBLE 0,03; SESGO 0,03 |

Con submuestras al azar (verdad M, ruido 0,5 / 0,3): 10 gránulos dan INDECIDIBLE la mitad de las veces,
20 dan MXD03 MAS CERCA 0,92, 40 dan 0,98. Con 76 la vara tiene poder de sobra **si el objeto es el mismo
para los dos sensores**; lo que la puede engañar no es el ruido sino un sesgo de la vara del tamaño del
corrimiento, y para eso está el control por satélite.

## Prueba del instrumento

`probar_probe_sola.py` pasa escenas de 81 × 81 píxeles por el pipeline real en los 22 brazos y C'. El
workflow la corre antes de cada job y `tests/test_mxd03_sola_123.py` también.

| caso | escena | qué debe salir | qué sale |
|---|---|---|---|
| POSICIÓN | foco de 335 K a 6 km al norte (inner 5), `_interp_geo` corrida 2 km al sur | C publica, M no; módulo 2 px; entre 1 y 19 nulos publican; el píxel por índice es el foco, a 6 km en M y 4 km en C, y en cada nulo es C más su vector | así (10 de 20 nulos publican) |
| ANISO | píxeles de 1 km a lo largo y 2 km a lo ancho, corrimiento de 2 km a lo ancho | módulo real 1 px; nulos todos de 2 km, de 1 a 2 px | así (y el Test 1 no se calcula: el anillo baja de 20 píxeles, como sobre 30° en los datos) |
| SIERRA | la grilla de `_interp_geo` con bow tie (huella 1,95 km, filas de amarre en 2 + 5t, la misma interpolación del pipeline), corrimiento de 1 km a lo largo | módulo real 1 px con el jacobiano de un barrido | así; con el de ±2 líneas falla (`test_con_el_jacobiano_viejo_la_prueba_sierra_falla`) |
| TEST1 | disco de +1 K sobre el cráter, `_interp_geo` corrida 1,2 km al sur | en C el píxel caliente cae en el anillo, en M en el centro; M dispara; el espía coincide con el record | así (C k = 2,96 sin publicar, M publica) |
| AUSENTE | geolocalizaciones iguales | módulo 0 y todos los brazos iguales | así |

Mutaciones: un nulo de la mitad del km real hace fallar la prueba
(`test_si_el_nulo_no_tuviera_el_km_del_real_la_prueba_falla`), y el jacobiano de ±2 líneas hace fallar
SIERRA. Cada estado del evaluador tiene un test que lo
produce y un control que no (A116), incluido el nulo de la vara roto a propósito: si diez nulos caen
justo en la vara, la vara deja de declarar a M aunque su efecto sea real.

## Tiempo y cómo correrlo

- **Tiempo medido, no supuesto** (`presupuesto_tiempo.py`, `presupuesto_tiempo_salida.txt`): de la 1.17 (2
  brazos) contra la 1.21 (6 brazos) sobre los mismos gránulos sale el costo de un brazo por gránulo (hasta
  0,044 min, Láscar) y el de bajar y leer (hasta 0,168 min, Chaitén). Con 22 brazos el job más cargado
  de la 1.17 (48 gránulos de Láscar) se predice en 43 a 54 min. Por eso **cada job se parte en dos**
  (`jobs_123.py`: gránulos pares e impares, 24 medios jobs de hasta 24 gránulos): peor caso **27,2 min**,
  propio 24,3. El script deja de bajar gránulos a los **50 min** (`sin_tiempo`) y el job tiene **75 min**
  (50 × 1,3 = 65, más la instalación, A15). Con `max-parallel: 4`, unas 5 horas de job en total, más o menos
  1,5 h de reloj. SIN VERIFICAR hasta correr: ni el espía ni los 20 nulos se cronometraron sobre un L1B real.
- **Primero un medio job suelto para cronometrar** (`Lascar-2a`, el más cargado), y sólo si termina bajo
  los 50 min, los otros 23, **desde el mismo tag**:

```
git tag s151-1.23-probe <commit de main tras el merge> && git push origin s151-1.23-probe
gh workflow run probe-s151-mxd03-sola-123.yml --ref s151-1.23-probe -f preregistro_aprobado=si -f jobs='["Lascar-2a"]'
gh workflow run probe-s151-mxd03-sola-123.yml --ref s151-1.23-probe -f preregistro_aprobado=si -f jobs='<los otros 23>'
```

- El evaluador de cada despacho saldrá INCOMPLETO porque sólo ve sus jobs; el veredicto se saca en local
  con los 24 artefactos: `python evaluar_sola.py <carpeta> --art121 <artefactos de la 1.21>`.
- **Autenticación**: sólo `EARTHDATA_TOKEN`; el job `plan` y cada job fallan al instante si viene vacío
  (A71). Nunca usuario y clave.
- **Concurrencia**: grupo propio `probe-s151-mxd03-sola-123`. No hace push.

## Archivos

| archivo | qué es |
|---|---|
| `probe_sola.py` | el probe (C, M, 20 nulos en píxeles, C', espía del Test 1, píxel por índice) |
| `evaluar_sola.py` | el criterio de arriba |
| `probar_probe_sola.py` | la prueba sintética |
| `jobs_123.py` | los 24 medios jobs |
| `construir_vara_viirs.py`, `vara_viirs.json`, `construir_vara_viirs_salida.txt` | la vara congelada |
| `sensibilidad_test1_121.py`, `sensibilidad_test1_121_salida.txt` | el Test 1 medido sobre la 1.21 |
| `saltos_de_cumulo_121.py`, `saltos_de_cumulo_121_salida.txt` | el borde del barrido medido sobre la 1.21 |
| `presupuesto_tiempo.py`, `presupuesto_tiempo_salida.txt` | el tiempo medido |
| `invariante_km.py`, `invariante_km_salida.txt` | en qué unidad el nulo tiene el tamaño de M |
| `poder_nulo.py`, `poder_vara.py` y sus salidas | el poder |

Los artefactos de la 1.17 y la 1.21 que leen los scripts de medición viven fuera del repo
(`C:\Users\nmend\AppData\Local\Temp\claude\mxd03_117\art\` y
`C:\Users\nmend\AppData\Local\Temp\claude\probe_121\art\`); se pasan como argumento.

## Límites conocidos y lo que queda SIN VERIFICAR

- **El objeto puede no ser el mismo** para MODIS y VIIRS: el píxel MODIS más caliente puede ser ruido en
  una noche débil. El filtro (MIROVA alertó la pasada MODIS y una VIIRS de la noche) lo acota; no lo
  elimina.
- **La vara VIIRS hereda la selección anclada al cráter** de nuestro pipeline VIIRS. Se sacaron los
  cúmulos del Test 1, pero el cúmulo contextual también se elige cerca del ancla. Si la vara estuviera
  sesgada hacia el ancla, favorecería a la geolocalización que deje el píxel MODIS más cerca del cráter.
  El control por satélite detecta un sesgo constante, no uno hacia el ancla. Es la primera afirmación a
  atacar.
- La precisión de la geolocalización VIIRS no se citó con número: SIN VERIFICAR.
- Que MIROVA use MxD03 sigue SIN VERIFICAR (SP426.5 p. 3 habla de «pixel(s) geolocation» sin nombrar el
  producto).
- El mecanismo del salto de k del 04-20 (el píxel caliente que entra al anillo) es hipótesis hasta que lo
  mida el espía.
- El poder del rango supone nulos binomiales homogéneos; el nulo real no lo es.
- La traslación del nulo es rígida; el campo real de corrimiento varía un poco dentro del ROI.
- Sobre la grilla con bow tie el nulo en km no perturba igual en todos los rumbos (invariante_km); la
  anotación `tamano_del_nulo` dice cuánto se aparta de M en cada cenit, pero no lo corrige.
- El caso SIERRA reproduce el modelo del verificador; que la grilla real de `_interp_geo` sea así en el
  borde está SIN VERIFICAR sobre un gránulo real (el probe guarda el jacobiano, que lo dirá).
- Las tres elecciones del criterio de la vara que no salen de MIROVA (pares k y k + 4, exigir que el
  efecto supere las 20 medianas del nulo, 5 gránulos por satélite) son de instrumento, no de física, y
  su efecto está medido en `poder_vara_salida.txt`; aun así son elecciones (A115).
- Del verificador de la 1.21 queda fuera de esta tarea identificar el commit de la deriva de los 8
  records que hoy salen con más píxeles anómalos que los guardados.
