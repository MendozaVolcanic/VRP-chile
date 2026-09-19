# Cuarto verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v4)

**Veredicto: la v4 arregla lo que la ronda 3 pidió arreglar, y aun así todavía no es viable, por un
defecto nuevo que el control temporal no podía tener antes.** Los dos hallazgos de gravedad 4 de la
ronda 3 quedaron cerrados con datos: el control temporal **no tiene sesgo** (con un punto sorteado da
`D = -0,0068` con intervalo [-0,0290, +0,0163], y +0,0000 con referencias a más de 30 días), y la regla
de equivalencia **sí deja alcanzables las tres salidas** (sobre el nulo, con la estructura real de
noches, da "no se distingue" en 158 de 200 repeticiones y nunca un falso positivo). Lo que falla es
otra cosa: **el control de instrumento de §5 pone un punto sorteado, y la medida pone el punto donde
nuestro detector disparó, en el mismo gránulo que MIROVA usó para hacer ese TIF.** Medido fuera de la
muestra del veredicto, ese solo hecho ya da `D = +0,0835` con intervalo [+0,0352, +0,1358], que es del
tamaño del umbral de decisión. El control declarado pasa mientras la medida ya está inclinada.

Documento verificado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v4 del 2026-09-19, rama `s144-prereg-keep-peak-direccion`, sobre el commit `70d26d3c7`).

Mis scripts están fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v4\`:
`base4.py` (pools de referencia y conteos), `null4.py` (nulo del control temporal, `Z` del punto en la
pasada y en todas las RUTINA del volcán), `analiza4.py` (`zc_punto`, armado del control, bootstrap),
`ver4.py` y `ver4b.py` (simulación de la regla de veredicto, potencia y tramos), `pers4.py` y
`prox_an.py` (persistencia de P y proxy de selección), `misc4.py` (comprobaciones sueltas). Reusan
`common3.py`, `pool3.pkl` y `geomP.pkl` de la ronda 3. No modifiqué ningún archivo del repo salvo este
informe.

## Aviso de contaminación (léelo antes de tocar la v4)

Para responder "¿el control temporal tiene su propio sesgo?" hay que medir el campo donde vive P, y
para responder si el control **ve** el sesgo que importa hubo que medir el procedimiento completo con
el punto puesto donde cae nuestro cúmulo. Queda declarado:

1. Corrí el procedimiento entero de §5 y §7 con un punto **sorteado** de la distribución empírica de
   nuestros P sobre **533 pasadas RUTINA disjuntas de la muestra de M2** (las mismas que usó la ronda
   3). Eso es una predicción directa de lo que dará el control de instrumento de §5.
2. **Corrí el mismo procedimiento con `Z` evaluado en NUESTRO PROPIO P**, sobre 194 pasadas con patrón
   y publicadas **fuera de la muestra del veredicto** (etiquetas `far_ref` y `sin_info`, fuera de
   Lastarria) y sobre 50 pasadas `neg_limpio` con patrón **no publicadas**. Esto **acota y predice el
   signo y el orden de magnitud de M2**. Es la contaminación más fuerte de las cuatro rondas y no había
   otra forma de contestar la pregunta que me hiciste.
3. Evalué `Z` en puntos **sorteados** dentro de rásteres que sí pertenecen a pasadas de la muestra de
   M2, porque esas pasadas aparecen como referencias temporales de otras. Nunca en su P.
4. Recalculé `zc_punto` por volcán con la definición nueva de §4 y reproduje el pool de M1 de la ronda
   3. **No** calculé `Z(P)` en ninguna pasada `neg_limpio` con patrón y publicada fuera de Lastarria, y
   **no** clasifiqué ninguna pasada de M1.

---

## Hallazgos nuevos (ordenados por gravedad)

### H1. El control de instrumento de §5 no puede ver el sesgo del que depende todo: nunca pone el punto donde nuestro detector disparó, en el gránulo que MIROVA usó para ese TIF

- **Dónde**: v4 l. 158-162 (el control de instrumento del nulo), l. 140-142 (el indicador `e_p`),
  l. 205-207 ("En las pasadas con alerta MIROVA y nosotros leemos el mismo granule, así que el ruido
  compartido infla cualquier coincidencia: esas se informan, no deciden"), l. 214-220 (el veredicto).
- **Evidencia** (`null4.py`, `analiza4.py`, `pers4.py`, `prox_an.py`):

  | qué se mide con el procedimiento completo de §5 y §7 | n | `D` | IC 95 % | tasa observada | tasa de referencia |
  |---|---|---|---|---|---|
  | punto **sorteado** de la distribución de nuestros P (**el control que la v4 declara**) | 533 | **-0,0068** | [-0,0290, +0,0163] | 0,064 | 0,071 |
  | **nuestro propio P**, pasadas `neg_limpio` con patrón NO publicadas | 50 | **+0,0760** | [-0,0000, +0,1636] | 0,140 | 0,064 |
  | **nuestro propio P**, pasadas publicadas fuera de la muestra (`far_ref` y `sin_info`) | 194 | **+0,0835** | [+0,0352, +0,1358] | 0,165 | 0,081 |
  | de esas, sólo `sin_info` (MIROVA no publicó ninguna fila esa pasada) | 168 | **+0,0940** | | 0,173 | 0,079 |

- **Qué pasa (el fenómeno)**: el TIF que se usa para medir es la imagen que MIROVA hizo **del mismo
  gránulo VIIRS** que leyó nuestro pipeline esa noche. Cuando `keep_peak` conserva un píxel es porque
  ahí hubo un exceso local de radiancia MIR en ese gránulo; sea lava, sea un borde de nube, sea ruido
  del detector, ese mismo exceso está en el ráster de MIROVA. La noche siguiente el gránulo es otro y
  el transitorio no está. Es decir: el control temporal **restituye por construcción** lo que nuestro
  propio detector puso, y no necesita que MIROVA haya visto nada. La v4 nombra este mecanismo con todas
  sus letras en l. 205-207 para sacar del veredicto a las pasadas con alerta, y después lo deja entrar
  por la puerta de los negativos limpios, que comparten el gránulo exactamente igual.
- **Por qué el control declarado no lo detecta**: el control de §5 sortea el punto de la distribución
  de radios y acimutes de nuestros P, o sea copia **dónde** suele caer el cúmulo, pero no **cuándo**
  disparó el detector. Con eso da -0,0068 y pasa la compuerta de ±0,05 con holgura. La diferencia entre
  las dos primeras filas de la tabla es justamente lo que el control no mide.
- **Cómo se ve en el resultado**: "el intervalo de `D` queda entero por encima de +0,05" con el nulo del
  instrumento en verde, y la fila 2 de la tabla de §8 leída como "el cúmulo lejano es un rasgo térmico
  real que MIROVA también ve y no publica (categoría b)". Aplicado a lo que A69 y A80 describen como
  artefacto topográfico o de nube, y con A72 pidiendo que el fix sea de algoritmo justo cuando el dato
  es artefacto. En los `sin_info` MIROVA no publicó ninguna fila, así que ahí no hay ninguna lectura
  posible en la que "+0,094" signifique "MIROVA ve algo y no lo alerta".
- **Cómo reproducirlo**: `python null4.py && python analiza4.py` (fila 1) y
  `python pers4.py && python prox_an.py` (filas 3 y 4); la fila 2 sale del bloque final de `ver4.py`.
- **Cómo arreglarlo** (elegir antes de medir):
  1. **Mover el nulo al lugar correcto**: el control de instrumento debe correr el procedimiento con
     `Z` en **nuestro propio P**, sobre pasadas con patrón y publicadas **fuera de la muestra del
     veredicto** (las `far_ref` y `sin_info` fuera de Lastarria sirven, ya son 194), y el veredicto
     positivo debe exigir que `D` supere **ese** nivel, no el 0. Es la opción (b) que la ronda 3
     proponía para P', trasladada al control nuevo.
  2. **O declarar qué significa el positivo**: escribir en §7 y en §8 que "cae sobre calor" quiere
     decir "nuestro cúmulo corresponde a un exceso local presente en ese gránulo y ausente otras
     noches", que es compatible con artefacto transitorio, y **no** que sea categoría b. Con eso la
     fila 2 de §8 ya no puede concluir "no apagar `keep_peak`".
- **CONFIRMADO. Gravedad 4.**

### H2. La tabla de §8 lee al revés las dos salidas: el artefacto transitorio da "cae sobre calor" y el rasgo real permanente da "no se distingue"

- **Dónde**: v4 l. 237-241 (la tabla de qué se hace con el resultado), l. 204-207 (qué significa el
  veredicto sobre los negativos limpios), contra l. 184-187 (el contraste temporal de la semilla en M1,
  que dice lo contrario).
- **Evidencia**:
  - Por la definición del estadístico (`d_p = e_p − r_p`, l. 140-142), una fuente **permanente** está
    también en las 5 referencias, así que `r_p` sube, `d_p` baja y `D` tiende a 0. Un **transitorio**
    está sólo en la pasada medida y da `d_p` cercano a 1.
  - Los P no son puntos cualesquiera: son sitios recurrentes. Medido sobre las 1.113 pasadas con
    patrón, publicadas y `neg_limpio` fuera de Lastarria (`pers4.py`, pura geometría, ningún ráster),
    el **97,1 %** de los P tiene otro P nuestro a 0,75 km o menos **en otra noche**, con mediana de
    **12 noches** (Copahue 22, Llaima 18, Villarrica 15, Chaitén 8). O sea, lo que `keep_peak` publica
    lejos del cráter vuelve al mismo lugar noche tras noche.
  - Y el 26,9 % de las pasadas de M2 tiene al menos una de sus 5 referencias en una noche en que
    nosotros publicamos un P a 0,75 km o menos del mismo punto (Copahue 44,9 %), o sea el propio rasgo
    se cuela en el denominador.
- **Qué pasa (el fenómeno)**: el lago de lava de Villarrica, el campo fumarólico del Lazufre y el
  lacolito de Cordón Caulle, que son los ejemplos de categoría b que A54 pide no destruir, son
  permanentes. Un control que pregunta "¿está más caliente **esta** noche que las otras?" está ciego
  justo a ellos. La v4 ya sabe esto: en M1 (l. 184-187) exige el contraste temporal de la semilla
  precisamente porque "la semilla cae sobre P" no separa el objeto de esa noche de la fuente que está
  siempre. En M2 esa misma distinción pasó a ser la hipótesis nula sin decirlo.
- **Matiz honesto, medido**: empíricamente el efecto es chico en esta muestra, porque en nuestros P la
  tasa de exceso de las noches de referencia es 0,081, apenas por encima del 0,064 a 0,071 de un punto
  sorteado. O sea, hoy los P **no** son persistentemente calientes en el campo de MIROVA. Eso no salva
  la lectura de §8: la salida "no se distingue" seguirá significando las dos cosas a la vez, y la tabla
  la manda a "no tiene correlato, re-evaluar el A/B para apagar `keep_peak`".
- **Cómo se ve en el resultado**: un "no se distingue" que se lee como permiso para apagar `keep_peak`
  en un volcán donde lo que se está apagando es un rasgo real permanente, que es exactamente el daño
  que A54 y A83 dicen que no hay que hacer.
- **Cómo reproducirlo**: `python pers4.py` (bloque de persistencia) y el bloque de referencias
  contaminadas al final de mi sesión, que usa `null4.pkl` más `pool3.pkl`.
- **CONFIRMADO. Gravedad 3.**

### H3. El tramo posterior a #535 no puede dar la salida de equivalencia, y ahí la condición de los dos tercios se queda sin volcanes elegibles

- **Dónde**: v4 l. 200-201 (estratificación por tramo, A104), l. 214-220 (el veredicto), l. 222-223
  ("los tramos se informan por separado" y la definición de lecturas opuestas), l. 243 (431 antes y 123
  después).
- **Evidencia** (`ver4b.py`, remuestreo por noche estratificado por volcán, 120 repeticiones sobre el
  nulo con la estructura real de noches de cada tramo):

  | tramo | pasadas | noches | volcanes con ≥ 20 noches | ancho medio del IC | veredicto sobre el nulo |
  |---|---|---|---|---|---|
  | pre #535 | 431 | 278 | 6 | 0,063 | "no se distingue" 81, INCONCLUSO 39 |
  | **post #535** | **123** | **70** | **0** | **0,119** | **INCONCLUSO 118, "no se distingue" 2** |

- **Qué pasa**: la salida "no se distingue" pide que un intervalo entero quepa dentro de ±0,05, o sea
  que el intervalo mida menos de 0,10 de ancho. En el tramo posterior mide 0,119, así que **no cabe
  nunca**, haya o no haya señal. Y como ningún volcán llega a 20 noches en ese tramo, la segunda
  condición del positivo ("`D_v > 0` en al menos dos tercios de los volcanes con al menos 20 noches")
  se evalúa sobre un conjunto vacío: un implementador la dará por cumplida (dos tercios de cero es
  cero) y otro la dará por fallada. Las dos lecturas son defendibles y dan veredictos distintos en el
  único tramo que A104 dice que refleja el régimen de hoy.
- **Cómo se ve en el resultado**: "el tramo posterior queda INCONCLUSO" presentado como resultado de
  los datos cuando estaba decidido por el tamaño de muestra, y una discusión sobre lecturas opuestas
  que no puede ocurrir porque una de las dos lecturas es inalcanzable de ese lado.
- **Cómo reproducirlo**: `python ver4b.py`, bloque "tramo pre / tramo post".
- **CONFIRMADO. Gravedad 3.**

### H4. El `zc_punto` que cita §4 no reproduce con el pool que la propia §4 define, y el arreglo de H7 no ensancha ningún pool: las dos lecturas de "pasada RUTINA" son la misma

- **Dónde**: v4 l. 110-116 (calibración de los umbrales "en las pasadas RUTINA de la fila de MIROVA ...
  no se exige record nuestro, H7"; "Chaitén 4,64 con IC [3,17, 6,26]").
- **Evidencia**:
  - `base4.py`: el pool por **fila de MIROVA** (RUTINA CONS con VRP 0, sin alerta ni falso positivo esa
    noche y sensor, con TIF a ±120 s) y el pool por **record nuestro `neg_limpio`** dan **exactamente el
    mismo número en los 11 volcanes**: Láscar 45 y 45, Lastarria 46 y 46, Isluga 19 y 19, Tupungatito
    79 y 79, Planchón-Peteroa 96 y 96, NdC 178 y 178, Llaima 206 y 206, Villarrica 183 y 183, Copahue
    197 y 197, Cordón Caulle 98 y 98, Chaitén 185 y 185. Es lo esperable: nuestro pipeline procesa todos
    los gránulos, así que toda fila de MIROVA tiene record nuestro a ±120 s. El filtro que corta no es
    el record sino el TIF (Isluga tiene 34 filas RUTINA y sólo 19 con imagen).
  - Con el filtro de usabilidad puesto (`null4.py`), el pool de calibración queda Chaitén 161, Copahue
    168, Llaima 167, Villarrica 152, NdC 147, Cordón Caulle 91, Planchón-Peteroa 86, Tupungatito 66,
    **Láscar 36 e Isluga 13**. Esos dos últimos son exactamente los números que la ronda 3 atribuyó a
    la lectura **estrecha** y que la v4 creyó estar dejando atrás.
  - `zc_punto` con la regla literal de §4: Chaitén **3,63** con IC [3,13, 4,66], no 4,64 con
    [3,17, 6,26]. El valor citado sale del pool nulo de la ronda 3, que es otro conjunto. El resto:
    Copahue 2,63, Llaima 2,36, NdC 2,67, Villarrica 2,81, PP 2,99, Tupungatito 3,43, Cordón Caulle
    3,65, Láscar 3,71, **Isluga 6,07 con IC [2,50, 7,69]** sobre 13 pasadas.
- **Qué pasa**: la v4 cambió el pool de calibración citando H7 y conservó el número que H7 había
  medido en el pool viejo. Y el cambio no compra nada: el n por volcán es el mismo antes y después, así
  que la advertencia de la ronda 3 ("en Isluga el percentil 95 es casi el máximo") sigue viva sin que
  el texto lo diga.
- **Cómo se ve en el resultado**: un lector que quiera comprobar el umbral de Chaitén encuentra 3,63 y
  desconfía de los otros números; y el intervalo de Isluga, de 2,50 a 7,69, no aparece declarado.
- **Cómo reproducirlo**: `python base4.py` (los dos pools) y la primera sección de `python analiza4.py`.
- **CONFIRMADO. Gravedad 2.**

### H5. El anillo donde se calibra `zc_punto` no es la región donde se aplica: un tercio de los sorteos cae a radios donde ningún P puede vivir

- **Dónde**: v4 l. 110-111 ("calibrados con el mismo estadístico y sobre la misma región donde se
  aplican"), l. 114-115 (X sorteado uniforme en área en el anillo de 1,5 a 3,5 km).
- **Evidencia** (`misc4.py`): sobre los P de la muestra, el radio máximo es **3,00 km** y el percentil
  99 es 2,99 km, porque el disco del Test 1 tiene 3 km y `keep_peak` no puede conservar nada más lejos.
  El 95,96 % vive entre 1,5 y 3,5 km (el complemento está **debajo** de 1,5, no encima de 3,5). Un
  sorteo uniforme en área sobre [1,5, 3,5] pone el **32,5 %** de los puntos de calibración entre 3,0 y
  3,5 km, o sea en un anillo donde ningún P cae nunca.
- **Qué pasa**: el umbral se estima en parte sobre terreno que la medida no visita. No es fatal (la
  diferencia `e_p − r_p` usa el mismo umbral en los dos lados, que es la mitigación que §9 invoca con
  razón), pero la frase "sobre la misma región donde se aplican" no es cierta y el corte natural sería
  [1,5, 3,0].
- **Cómo reproducirlo**: `python misc4.py`, bloque "§1: banda de r(P)".
- **CONFIRMADO. Gravedad 2.**

### H6. §8 dice que M1 son "del orden de 12 pasadas, todas de Lastarria, con `F` inalcanzable", y con el filtro nuevo de §6 hay una pasada de Láscar donde `F` sí es alcanzable

- **Dónde**: v4 l. 243-247 (veredictos alcanzables), l. 180-182 (el declarado de antemano, que habla
  sólo de Lastarria y está bien escrito), l. 170-171 (el filtro nuevo "volcanes donde `mirova_center`
  está a menos de 1 km del cráter").
- **Evidencia**:
  - Reproduje el pool de M1 de la ronda 3 (`python m1_3.py` en el scratchpad `v3`): 39 pasadas, 15 en
    Lastarria con 12 compatibles y 24 fuera con 4 compatibles, de las cuales **Láscar 1** (con
    `Distancia_km` = 0,84 km) y Cordón Caulle 3. El mismo script informa "F alcanzable" en 4 de las 16
    compatibles: **Láscar 1, Lastarria 0, Cordón Caulle 3**.
  - Las separaciones `mirova_center` contra cráter (`volcanoes.yaml`): Lastarria 0,12, Llaima 0,14,
    Copahue 0,14, Chaitén 0,24, Isluga 0,37, NdC 0,39, Villarrica 0,54, **Láscar 0,83**,
    Planchón-Peteroa 2,02, Tupungatito 4,86, Cordón Caulle 7,57. El filtro de §6 deja fuera a Cordón
    Caulle y Tupungatito, como dice §2, pero **Láscar pasa** con 0,83 km.
  - La pasada de Láscar de M1 no es la que §2 saca a mano (Láscar 2026-06-13, cúmulo a 0,32 km del
    cráter y 0,49 km del `final_hotspot`): esa no llega al pool porque no cumple `d(P,F) ≥ 1,5`.
- **Qué pasa**: el universo de M1 son 13 pasadas en 2 volcanes, no 12 en uno, y la afirmación "con `F`
  inalcanzable" vale para Lastarria (donde §6 la declara bien) y no para el conjunto. §2 tampoco
  menciona a Planchón-Peteroa (2,02 km), que también cae por el filtro nuevo.
- **Matiz**: §6 agrega un filtro de región (unión del disco de 3,4 km y el disco de `Distancia_km` + 1
  km) que la ronda 3 no aplicó, y que podría sacar esa pasada de Láscar. No lo pude comprobar.
- **Cómo reproducirlo**: `python m1_3.py` desde el scratchpad `v3`, y el bloque de separaciones de mi
  sesión sobre `volcanoes.yaml`.
- **CONFIRMADO para el pool de la ronda 3. Gravedad 2.**

### H7. El control H nombra un campo que el record no persiste, y el conteo de §4 sobre el control congelado es 18 donde git dice 19

- **Dónde**: v4 l. 153-156 (control H: "record `ctx_cluster` de 2 o más píxeles con centroide dentro
  del `inner_radius_km` (hay 110, de ellas 50 de Cordón Caulle)"), l. 93 ("18 archivos,
  `MANIFIESTO.json` con sha256").
- **Evidencia**:
  - `git ls-files experiments/_s144_keep_peak_direccion/control_s143 | wc -l` devuelve **19**
    (`MANIFIESTO.json` más 9 volcanes en `t1` y 9 en `t2`). La ronda 3 ya había reportado 19 en su
    sección VERIFICADO LIMPIO.
  - Los records no tienen ninguna clave `ctx_cluster`: en
    `data/mirova_equivalent/PuyehueCordonCaulle.json` las claves con "cluster" son
    `n_hotspots_clustered` y `primary_cluster`. `ctx_cluster` es una variable interna del pipeline
    (`pipeline/anchor.py:67-84`, `pipeline/process_modis.py:1012`), y lo que queda persistido es
    `final_hotspot_source == "ctx_cluster"`. Las dos reconstrucciones posibles no dan lo mismo: sobre
    las pasadas VIIRS 375 con alerta y TIF pareado, "primary_cluster de 2 o más píxeles con centroide
    dentro del inner" da **130** (Cordón Caulle 58) y exigiendo además `final_hotspot_source ==
    "ctx_cluster"` da **128** (Cordón Caulle 58). El 110 con 50 de Cordón Caulle del texto es
    compatible con esos 130 y 58 después del filtro de usabilidad, así que la cifra no está mal: lo que
    falta es decir de qué campo sale.
- **Qué pasa**: H es compuerta blanda (si falla, todo baja a SOSPECHA), así que la ambigüedad decide
  sobre la confianza de las dos medidas. Y el 18 contra 19 es el tipo de número que hace dudar del
  resto sin necesidad.
- **Cómo reproducirlo**: el `git ls-files` de arriba y el bloque "control H" de `misc4.py` más su
  versión con filtro de sensor.
- **CONFIRMADO. Gravedad 2.**

### H8. Detalles de ejecución que dejan dos implementaciones legítimas

- **La semilla de `zc_punto` no fija el resultado** (l. 114-116). Un `random.Random(144)` con el orden
  de extracción declarado sólo reproduce si además se fija **cuántos números se sacan por pasada y en
  qué orden**. Yo saqué dos (radio al cuadrado uniforme y acimut, en ese orden) y ordené los volcanes
  alfabéticamente; otro orden de volcanes o un sorteo en coordenadas cartesianas da otro `zc_punto` con
  la misma "semilla 144".
- **El sorteo del control de instrumento no tiene semilla declarada** (l. 158-162), aunque es el que
  decide si la medida entera es INCONCLUSA.
- **Qué población alimenta `R(p)`** (l. 134-136) no está dicho: §4 define "pasada RUTINA" para los
  umbrales y §5 vuelve a usar la palabra sin apuntar a esa definición. Aquí no importa, porque medí que
  las dos lecturas son el mismo conjunto (H4), pero conviene apuntarlo.
- **Nada prohíbe que una referencia sea otra pasada de la muestra de M2**, y de hecho lo será a menudo:
  en el nulo, entre 0,8 y 3,7 de las 5 referencias por pasada pertenecen al universo de M2 según el
  volcán. No es un defecto, pero hay que decirlo.
- **Empates de cercanía temporal** (dos referencias a la misma distancia) no tienen regla.
- **`pipeline/geo_utils.py:53-77`** (l. 95): la función `get_detection_anchor` va de la línea 53 a la
  78; el 77 corta justo antes del último `return`.
- **CONFIRMADO (lectura del texto y medición). Gravedad 1.**

---

## VERIFICADO LIMPIO

Lo que la v4 arregló, y lo que medí y quedó en pie:

- **El control temporal no tiene sesgo propio.** Con el punto sorteado de la distribución de nuestros P
  sobre 533 pasadas RUTINA ajenas a la muestra: `D = -0,0068` con IC 95 % [-0,0290, +0,0163] (brecha
  mayor que 3 días), `-0,0105` [-0,0319, +0,0131] con 10 días y `+0,0000` [-0,0217, +0,0214] con 30
  días. El +0,1014 que hundía al control reflejado de la v3 desapareció. Por volcán va de -0,039
  (Villarrica) a +0,064 (Láscar, n = 28), y el único que se sale es Isluga con n = 4.
- **Las referencias RUTINA no son una población más nublada.** En pasadas **con alerta** de MIROVA, un
  punto sorteado supera `zc_punto` el **2,97 %** de las veces (n = 337) contra el 5 % que da por
  construcción en las RUTINA: si algo, las RUTINA tienen algo más de textura. Y sobre todo, las pasadas
  del veredicto **son ellas mismas RUTINA** (`neg_limpio` es una fila CONS RUTINA con VRP 0), así que
  los dos lados de la resta vienen de la misma población. La preocupación por la nube no se sostiene.
- **La regla de equivalencia de §7 arregla H2 de la ronda 3.** Aplicada al nulo con la estructura real
  de noches por volcán (348 noches, 554 pasadas), en 200 repeticiones da **"no se distingue" 158,
  INCONCLUSO 42, "cae sobre calor" 0**. Con la unidad de pasada en vez de noche son 189 y 11. El ancho
  medio del intervalo es 0,057 remuestreando noches y 0,046 remuestreando pasadas.
- **Las tres salidas son alcanzables en la medida global**, con este mapa de potencia (inyectando señal
  uniforme sobre el nulo, 120 repeticiones por punto): `D = +0,035` da INCONCLUSO el 82 % de las veces,
  `+0,063` da "cae sobre calor" el 12 %, `+0,081` el 34 %, `+0,100` el 63 % y `+0,129` el 92 %. O sea
  el positivo pide `D` del orden de **+0,10 o más**, y entre +0,03 y +0,09 lo más probable es
  INCONCLUSO. Conviene escribirlo en §8 para que nadie lea el INCONCLUSO como hallazgo.
- **La condición de los dos tercios es alcanzable y no es la que manda.** Llegan a 20 noches **7
  volcanes de 10** (Copahue 76, Llaima 64, Villarrica 54, Chaitén 46, NdC 35, Planchón-Peteroa 26,
  Tupungatito 20; quedan fuera Cordón Caulle 15, Isluga 6, Láscar 6), así que el corte es 5 de 7. Bajo
  el nulo la mediana es 2 de 7, y con señal uniforme se cumple el 95 al 99 % de las veces: la condición
  que decide es la del intervalo sobre +0,05, no ésta.
- **Pero bloquea la señal concentrada**: con señal sólo en Villarrica y Chaitén, incluso subiendo la
  tasa 0,60, el veredicto sale "cae sobre calor" en 38 de 120 repeticiones y nunca "no se distingue".
  Si la categoría b vive en dos o tres volcanes (que es lo que A83 y A54 hacen esperar), la regla la
  manda a INCONCLUSO. Vale la pena declararlo como límite, no como defecto.
- **El procedimiento se puede ejecutar tal como está escrito.** De las 554 pasadas de M2, **ninguna**
  pierde la muestra por falta de referencias: el mínimo disponible a más de 3 días es **9** (Isluga), y
  los demás volcanes van de 28 (Láscar) a 152 (Llaima). De 64.117 evaluaciones de `Z` en referencias,
  **0** fallaron por caer el punto fuera del ráster o sin ΔL0 (era de esperar: el ráster cubre unos 50
  km y ningún P pasa de 3,0 km). La separación temporal mediana de las referencias es **4,1 días**
  (p90 8,0), así que la nieve casi no alcanza a moverse; el 22,9 % tiene las 5 referencias de un solo
  lado, por borde del archivo.
- **El percentil del umbral no mueve el nulo del control nuevo**: `D` del nulo da +0,024 con percentil
  85, -0,004 con 90, -0,007 con 95 y -0,004 con 99. La mitigación que §9 invoca (el mismo umbral a los
  dos lados) vale para el control temporal igual que valía para el reflejado, aunque el número que cita
  sea del control viejo.
- **El embudo de §7 reproduce exacto**: 6.241 records nocturnos VIIRS 375, 2.999 con patrón, 2.627
  publicados, 1.134 `neg_limpio` (1.113 fuera de Lastarria), 635 con TIF a ±120 s, 554 con TIF usable,
  con descartes 478 sin imagen, 58 por md5 repetido, 19 por mediana alta y 4 por celdas sin dato. Los
  tramos son 431 y 123. La muestra tiene **348 noches de volcán**, muy por encima del mínimo de 30 que
  pide §7, repartidas Copahue 76, Llaima 64, Villarrica 54, Chaitén 46, NdC 35, PP 26, Tupungatito 20,
  Cordón Caulle 15, Isluga 6, Láscar 6.
- **La geometría de §1 y §2 reproduce**: el 95,96 % de los P está entre 1,5 y 3,5 km con mediana 2,788
  km; las separaciones `mirova_center` contra cráter son Lastarria 0,12, Tupungatito 4,86 y Cordón
  Caulle 7,57 km, como dice el texto; el pool de M1 de la ronda 3 da 15 en Lastarria con 12
  compatibles y 24 fuera con 4, de las cuales 3 de Cordón Caulle.
- **La contaminación de las referencias por nuestras propias detecciones repetidas es moderada**: en
  promedio 0,36 de las 5 referencias de cada pasada de M2 es una noche en que publicamos un P a 0,75 km
  o menos del mismo punto (26,9 % tiene al menos una, Copahue 44,9 %, Láscar y Cordón Caulle 0).

**No verificado** (queda abierto): los `Z(P)` de la muestra del veredicto y las clases de M1 (no los
calculé a propósito); si el filtro de región de §6 saca la pasada de Láscar de M1; si el control G pasa
con la redacción nueva de la v4 (piso `zc_disco` en vez de `zc_punto`), que no volví a correr porque la
ronda 3 lo midió con la redacción vieja; los números de §0 sobre el control reflejado, que sólo
comprobé como transcripción del informe de la ronda 3 y no volví a medir porque ese control ya salió
del veredicto; el residuo de `Distancia_km` con CONS y con OCR en Cordón Caulle (0,08 y 4,24 km, l. 89-90).

---

## Correcciones para una v5, por gravedad

1. **(4) Poner el nulo del instrumento donde está el sesgo (H1).** El control de §5 tiene que correr el
   procedimiento con `Z` en **nuestro propio P** sobre pasadas con patrón y publicadas fuera de la
   muestra del veredicto (hay 194 entre `far_ref` y `sin_info` fuera de Lastarria), no con un punto
   sorteado. Y el veredicto positivo tiene que exigir que `D` supere **ese nivel de selección**
   (medido acá en +0,0835 [+0,0352, +0,1358]), no el 0. Si se prefiere no cambiar la regla, entonces
   §7 y §8 deben declarar que "cae sobre calor" significa "el cúmulo corresponde a un exceso local del
   mismo gránulo, ausente otras noches", que es compatible con artefacto transitorio, y la fila 2 de la
   tabla de §8 no puede concluir categoría b.
2. **(3) Reescribir la tabla de §8 (H2).** Decir explícitamente que "no se distingue" abarca dos casos
   opuestos, el punto sin nada y el rasgo permanente (lago de lava, fumarolas, lacolito: la categoría b
   de A54, que por ser permanente también está en las referencias), y que por lo tanto **no autoriza
   por sí sola a apagar `keep_peak`**. Es la misma advertencia que §6 ya escribió para la semilla de M1.
   Un contraste barato: informar junto al veredicto la tasa de referencia `r_p` por volcán, porque una
   `r_p` muy por encima del 5 % de fondo es la firma de la fuente permanente.
3. **(3) Arreglar el tramo posterior a #535 (H3).** Con 70 noches el intervalo mide 0,119 y la salida
   de equivalencia es inalcanzable: o se declara que el tramo posterior sólo puede dar "cae sobre
   calor" o INCONCLUSO, o se le pone un criterio propio. Y hay que decidir por escrito qué pasa con la
   condición de los dos tercios cuando ningún volcán llega a 20 noches, que es el caso de ese tramo.
4. **(2) Corregir `zc_punto` (H4)**: reemplazar el 4,64 de Chaitén por el valor del pool que §4 ahora
   define (3,63 con IC [3,13, 4,66]), informar el n y el intervalo por volcán (Isluga 6,07 sobre 13
   pasadas, IC [2,50, 7,69]), y decir que la lectura ancha de H7 **no ensancha nada**, porque toda fila
   RUTINA de MIROVA tiene record nuestro: lo que corta es el TIF.
5. **(2) Ajustar el anillo de calibración a [1,5, 3,0] km o borrar la frase "sobre la misma región
   donde se aplican" (H5)**, porque ningún P pasa de 3,00 km y el 32,5 % de los sorteos cae más lejos.
6. **(2) Corregir §8 sobre M1 (H6)**: son 13 pasadas en 2 volcanes (12 de Lastarria y 1 de Láscar, que
   pasa el filtro nuevo con 0,83 km), y `F` es inalcanzable **en Lastarria**, no en M1 entero. Agregar
   Planchón-Peteroa (2,02 km) a la lista de volcanes que el filtro de §6 deja fuera.
7. **(2) Arreglar el control H y el conteo del control congelado (H7)**: decir de qué campo sale el
   "`ctx_cluster` de 2 o más píxeles" (el record persiste `primary_cluster` y
   `final_hotspot_source == "ctx_cluster"`, y las dos lecturas difieren en 2 pasadas), y cambiar 18 por
   **19** archivos.
8. **(1) Cerrar los detalles de H8**: cuántos números se sacan por pasada y en qué orden para que la
   semilla 144 signifique algo, la semilla del sorteo del control de instrumento, a qué definición de
   "pasada RUTINA" apunta §5, que una referencia puede ser otra pasada de M2, el desempate de cercanía
   temporal y el rango de líneas de `geo_utils`.

**Resumen**: la v4 dejó el control temporal sin sesgo y la regla de veredicto con las tres salidas
alcanzables, que era lo que la ronda 3 pedía, y la medida se puede ejecutar tal como está escrita
(ninguna pasada se pierde por falta de referencias y ninguna evaluación falla). Lo que queda es de
interpretación, no de aritmética: el punto donde se mide es el punto donde nuestro propio detector
disparó, en la imagen del mismo gránulo, y eso solo ya mueve `D` a +0,08 en pasadas donde MIROVA no
publicó nada. Mientras el control de instrumento siga poniendo un punto sorteado, va a salir verde
mientras la medida ya está decidida. Con la corrección 1 y la 2 escritas antes de medir, M2 queda en
pie y puede decidir.
