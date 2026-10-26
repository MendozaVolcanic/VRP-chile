# Verificador con contexto limpio: pre-registro de la tarea 1.23 (MxD03 sola)

PR https://github.com/MendozaVolcanic/VRP-chile/pull/846, rama `loop/1.23-prereg`, commit `4cc5e0134`
(CI `pytest` verde, `mergeStateStatus` CLEAN). Worktree revisado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-a2d13e6a2b33c4d82\`.
No edité ningún repo ni despaché nada. Scripts y salidas de esta verificación en
`C:\Users\nmend\AppData\Local\Temp\claude\verif_123\`.

## Veredicto: SELLABLE CON ARREGLOS

La vara VIIRS, el candado del workflow, la cobertura A108 y el evaluador de la regla 1 están bien. Hay
un defecto de instrumento en el nulo que afecta a todo lo que pasa sobre ~35° de cenit (la mitad de la
muestra), y una lectura del Test 1 que el README da por hecha y que los mismos artefactos de la 1.21
contradicen en parte. Los dos se arreglan antes de sellar, sin cambiar la muestra ni el costo.

## Lo que corrí

| qué | resultado |
|---|---|
| `python -m pytest tests/test_mxd03_sola_123.py` en el worktree | 37 pasan, 18,6 s |
| `sensibilidad_test1_121.py` sobre `C:\Users\nmend\AppData\Local\Temp\claude\probe_121\art\` | idéntico a `sensibilidad_test1_121_salida.txt` (`sens_rep.txt`) |
| `saltos_de_cumulo_121.py` sobre lo mismo | idéntico a `saltos_de_cumulo_121_salida.txt` (`saltos_rep.txt`) |
| composición de la vara de Láscar (`a_vara.py`) | `a_vara_salida.txt` |
| k con signo por etiqueta de MIROVA (`a_k.py`, `a_k2.py`) | `a_k_salida.txt`, `a_k2_salida.txt` |
| modelo del bow tie en la grilla de `_interp_geo` (`jac_bowtie.py`, `nulo_km.py`) | `jac_bowtie_salida.txt`, `nulo_km_salida.txt` |

## Bloqueante 1: el jacobiano en píxeles se mide sobre una grilla que el bow tie aplasta

**Fenómeno.** Hacia el borde del barrido la huella MODIS a lo largo de la traza crece de 1 a ~2 km y los
barridos consecutivos de 10 líneas se traslapan (bow tie). Las filas de amarre de 5 km del L1B (líneas
2 y 7 de cada barrido, offset 2) son posiciones reales de píxel, así que la fila 7 de un barrido y la
fila 2 del siguiente quedan casi en el mismo lugar en el borde. `_interp_geo` (zoom lineal) interpola
entre ellas: el resultado es una grilla cuyo espaciado a lo largo de la traza **alterna** entre f y
2 - f km por línea por tramos de 5 líneas, con f la huella.

**Mecanismo en el probe.** `jacobiano()` toma una diferencia centrada de ±2 líneas sobre esa grilla
(`probe_sola.py:75-93`), o sea que mide el espaciado de UN tramo. Medido con un modelo 1D que usa la
misma `zoom(order=1)` del pipeline (`jac_bowtie.py`): con f = 1,55 (~50°) el espaciado sale entre 0,45 y
1,55 km por línea según la fase de la línea en el barrido; con f = 1,95 (borde) entre 0,05 y 1,95. Un
corrimiento real de 0,5 km a lo largo de la traza pasa a valer hasta 10 píxeles. Como el nulo rota ese
módulo en píxeles y lo devuelve a km con el mismo jacobiano, en la dirección del barrido (píxel de ~4,5
km) el nulo sale de decenas de km.

Con los corrimientos reales que midió la 1.21 en el cráter (`nulo_km.py`, supuesto: traza ~ norte-sur):

| cenit | n | \|C - M\| mediana | mediana del nulo / real | p90 | gránulos con nulo > 2× real |
|---|---|---|---|---|---|
| 0-20 | 93 | 1,17 km | 1,01 | 1,04 | 0 |
| 20-35 | 85 | 1,45 | 1,07 | 1,17 | 0 |
| 35-50 | 69 | 2,31 | 1,16 | 1,72 | 3 |
| 50-60 | 121 | 3,40 | 1,33 | 3,25 | 33 |
| 60-90 | 102 | 6,42 | 1,34 | 8,52 | 34 |

Es un modelo (SIN VERIFICAR sobre un gránulo real), pero la geometría del traslapo es la de manual y el
cálculo usa la misma función que el pipeline. Lo que dice: bajo 35° el nulo es del tamaño de M; sobre
50°, en ~1 de cada 3 gránulos, el «nulo del mismo tamaño en píxeles» mueve la grilla de 2 a 8 veces más
km que MxD03. Es justo el tramo que la 1.23 dice corregir.

**Por qué los controles no lo ven.** Los dos INVALIDO del nulo son tautológicos: `medido_en()` mide la
traslación rígida en el mismo píxel donde se pidió, así que `km_aplicado == km` por construcción (salvo
redondeo float32, ~0,2 m), y `px_aplicado` se calcula con el mismo jacobiano que `modulo`. Verifican la
aritmética de `trasladar_ne`, no que el nulo tenga el tamaño de M. La prueba sintética usa grillas
regulares (`ANISO`), sin bow tie.

**A quién afecta.** La vara principal (33 + 29 de 76 gránulos bajo 35°, 2 sobre 50°) y casi todas las
protegidas de Láscar (cenit ≤ 47°) quedan casi intactas. Quedan comprometidas la lectura 5 (borde, el
caso «como Chillán», 222 de 470 gránulos sobre 50°), el rango del balance de la regla 2 (los negativos
limpios de cenit alto pesan) y cualquier protegida sobre 50° (Chillán 10-12). Un nulo que mueve 20 km
pierde publicaciones a mansalva: deja a M con «MENOS PERDIDAS QUE EL AZAR» o «BALANCE MEJOR QUE EL
AZAR» por un defecto del nulo, en la dirección que empuja a adoptar.

**Arreglo (barato, no cambia muestra ni tiempo).**
1. Derivar a lo largo de la traza sobre un barrido entero (±5 líneas, 10 líneas = un barrido), que
   promedia los dos tramos y da el espaciado medio; dejar ±2 a lo ancho.
2. Agregar a `probar_probe_sola.py` un caso con grilla en diente de sierra (el modelo de
   `jac_bowtie.py`) que falle hoy y pase con el arreglo.
3. Guardar y pre-registrar como anotación por cenit la razón km del nulo / km de M, y decir en el README
   que los INVALIDO del nulo son de aritmética.

**Cuestión de fondo que el README debería decir.** Todo lo que consume lat/lon en `process_modis.py`
lo hace por distancias en km al cráter (inner, ROI, disco y anillo del Test 1, radios). Para un círculo
grande frente al píxel, la cantidad de centros que cruzan el borde al trasladar la grilla d km es
~4R·d / área del píxel, **independiente de la dirección**: ahí el invariante correcto es el km (el nulo
de la 1.21), no el píxel. El píxel importa sólo para estructuras del tamaño del píxel (anillo de 1 km
del Test 1), que sobre ~30° ya no se calculan (n_bg < 20: 9 de 90 entre 30 y 50°, 0 de 222 sobre 50°).
O sea que la «anisotropía del 24 %» de la 1.21 se midió en una unidad que el pipeline no usa en el
tramo donde se midió. Con el arreglo 1 el nulo en píxeles sigue siendo más chico en km que M cuando M
va por el barrido; es una elección, y debería quedar escrita como tal (o correr la lectura 5 con un nulo
en km sobre 35°).

## Bloqueante 2: «la fragilidad es del Test 1, no de MxD03» no se sostiene tal como está escrita

Reproduje las cifras del autor (iguales). Pero:

- **«MxD03 mueve k menos que el azar (0,52 contra 0,60)»**: el intervalo bootstrap de la diferencia de
  medianas de |Δk| es [-0,21; +0,20] y el signo M>R contra R>M da 69 contra 72 (p = 0,87). Lo correcto
  es «no se distingue del azar», no «menos». Lo mismo con los cruces 36 contra 29 (±5 de ruido de conteo).
- **Con signo y separando por etiqueta de MIROVA** (`a_k2.py`, mismos 126 pares del autor):

| | n | Δk mediana M | Δk mediana R | M sube más que R / R más que M | sign test |
|---|---|---|---|---|---|
| MIROVA alertó | 51 | +0,15 | -0,09 | 33 / 18 | p = 0,049 |
| negativo limpio o sin info | 73 | -0,15 | +0,08 | 30 / 43 | p = 0,16 |

Lectura física: donde hay calor, MxD03 tiende a meterlo en el núcleo de 1 km del Test 1 y k sube; donde
no lo hay, tiende a bajar. Eso es lo que haría una posición **mejor**, y es lo opuesto a «M se comporta
como el azar». Es un indicio (un solo sorteo de R, p marginal), no una medida, pero basta para que el
README no presente como conclusión que la sensibilidad es sólo del Test 1. La magnitud de |Δk| sí es
propiedad del Test 1 en su piso (k de ruido ~2,1 contra umbral 3, bien derivado); la **dirección** no
está probada como azar.

**Arreglo.** (a) Reescribir esa frase del README como «M mueve k tanto como el azar; el signo por
etiqueta queda por medir». (b) Pre-registrar en la lectura 4 la versión con signo: mediana de Δk (y
cruces 0→1 / 1→0) de M contra los 20 nulos **por separado en alertas y en negativos limpios**. La
lectura 4 actual cuenta cruces sin dirección y sin etiqueta, y así pierde justo esta señal. Además, la
hipótesis del 04-20 («el píxel caliente entra al anillo e infla la desviación») es débil: el fondo es
mediana y MAD de ~25 píxeles, robustos a un píxel; y el píxel sigue sumando en ΔL porque el anillo está
dentro del disco de 3 km. El espía mide lo necesario para refutarla; conviene no anunciarla como la
explicación probable.

## Lo que está bien (atacado y en pie)

**La vara VIIRS (punto 2).** Las 127 pasadas estrictas de Láscar del conjunto principal son todas
`ctx_cluster`, de 1 a 4 píxeles, ninguna exactamente en el ancla; el centroide sale de las posiciones
VNP03IMG de los píxeles, no se pega al cráter. La selección anclada sólo elige qué cúmulo, y en Láscar
hay un solo objeto. Prueba de que la vara no está atada al ancla: en Lastarria cae a 2,26 km (Lazufre) y
en Isluga a 0,86. Que en Láscar caiga a 0,13 km dice que el objeto está en el cráter, no que la vara lo
ponga ahí. Compara posiciones 2D (norte, este), no radios: cumple A93 y A107 en la forma. El riesgo
A107 de fondo (que el píxel MODIS más caliente no sea el mismo objeto) queda acotado por exigir alerta
MIROVA en las dos pasadas; λ por gránulo lo deja ver.
Dos cosas a anotar: (1) el resultado es casi previsible: el probe de #828 ya midió el píxel brillante a
0,13-0,35 km del cráter con MxD03 y a 1,0-1,3 km con `_interp_geo`; la vara VIIRS agrega independencia
de la coordenada del ancla, no una pregunta nueva. (2) El centroide 3 × 3 pesado por el exceso sobre la
mediana de un disco de 5 km mete el gradiente de terreno de los vecinos (MIR absoluto, A69). El tirón es
común a C y M, pero si se acerca al tamaño de |C - M| proyecta sobre el eje C-M con signo opuesto en
Terra y Aqua, y saldría SESGO POR SATELITE. Recomiendo informar al lado la variante sin 3 × 3 (centro del
píxel caliente).

**Las tres reglas del autor (punto 3).** MIROVA no puede arbitrar geolocalización, así que no hay
referencia a la que preguntarle (A115 no aplica en su forma fuerte). Son elecciones de instrumento,
declaradas y con su poder simulado: k y k + 4 da una separación 1,18 veces |C - M| (más ancha que la de
C y M, conservadora; k + 3 daría 0,91); «superar las 20 medianas» equivale a p < 1/21; 5 gránulos por
satélite no muerde (Terra 30, Aqua 46). Aceptables. Nota: K = 19 también cumple el criterio `p ≤ 0,05`
del evaluador (1/20), así que la justificación «K = 20 es el primero» vale sólo con `<`. Y los 20 nulos
de un gránulo no son independientes (rumbos vecinos dan resultados parecidos); el p de 1/21 es nominal.

**Poder y estados (punto 5).** El README dice con claridad que M no puede salir adoptable por la letra y
que el probe sólo explica por qué cae y si la posición es mejor. Cada estado principal tiene un test que
lo produce y un control que no, incluido el nulo de la vara roto a propósito. Faltan tests de algunos
estados simétricos (MENOS GANANCIAS, NETO, BALANCE PEOR, SALTA MENOS, CRUZA MENOS, INTERP SIN CONTROL):
el código es simétrico, no bloquea.

**Workflow (punto 6).** Candado `preregistro_aprobado=si` en `plan`; token comprobado en `plan` y en cada
job; el env del probe sólo trae `EARTHDATA_TOKEN` (sin usuario ni clave, A71); `"on":` entre comillas;
grupo propio `probe-s151-mxd03-sola-123`, sin push; `pipefail` con `tee`; 75 min contra 50 de
presupuesto y peor caso predicho 27,2 (medido sobre la 1.17 y la 1.21, SIN VERIFICAR con 22 brazos, por
eso el medio job piloto); `procedencia()` guarda `GITHUB_SHA` y el evaluador da INCOMPLETO con más de un
commit. Correcto. Ojo operativo: GitHub mantiene un solo run pendiente por grupo, así que el segundo
despacho va recién cuando termine el piloto, como dice el README.

## Lo que Nicolás debe saber al sellar

1. Por la letra, MxD03 sola vuelve a dar PIERDE PROTEGIDA: el probe no la puede volver adoptable. Lo que
   puede dar es si la posición es mejor (vara) y si las 2 pérdidas de Láscar son lo que rompe cualquier
   corrimiento de ese tamaño.
2. La vara habla de Láscar y de cenit bajo y medio (70 de 76 gránulos, 2 sobre 50°). Es casi seguro que
   dé MXD03 MAS CERCA, porque #828 ya lo midió contra el cráter.
3. Sellar sólo con el arreglo del jacobiano (bloqueante 1). Sin él, todo lo que el probe diga del borde
   del barrido y del balance de la regla 2 sale de un nulo que en un tercio de los gránulos sobre 50°
   mueve la grilla varias veces más que MxD03.
4. La idea de que las pérdidas son «sólo fragilidad del Test 1» no está probada: los mismos artefactos
   sugieren que MxD03 sube k donde MIROVA ve calor y lo baja donde no. Con la lectura con signo, el probe
   lo puede medir.
