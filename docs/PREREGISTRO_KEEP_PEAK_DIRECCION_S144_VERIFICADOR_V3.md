# Tercer verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v3)

**Veredicto: la v3 todavía no es viable, pero por una sola razón de fondo.** El corte de la medida en
M1 y M2 resuelve el defecto que la ronda 2 calificó de gravedad 5, y M2 tiene muestra de sobra: 554
pasadas de negativos limpios fuera de Lastarria con todos los filtros puestos, 431 antes de #535 y 123
después. El brazo de fracciones con `zc_punto` es un instrumento justo: medido sobre puntos sorteados,
un instrumento ciego da +0,004 de diferencia. **El problema está en el otro brazo del veredicto.** El
control P' no es justo para la mediana pareada: en pasadas RUTINA ajenas a la muestra, poner un punto
donde suele caer nuestro cúmulo da una mediana pareada de **+0,1014 con intervalo [+0,018, +0,197], que
excluye el 0**, sin que haya nada que detectar. Como la salida "no se distingue de su reflejo" exige que
ese intervalo contenga el 0, el propio nulo la rompe en 43 de 60 repeticiones al n real. La salida que
podría llevar a apagar `keep_peak` es la que queda maltrecha, y las dos que sobreviven dejan todo como
está.

Documento verificado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v3 del 2026-09-19, rama `s144-prereg-keep-peak-direccion`, sobre el commit `9496cdaea`).

Mis scripts están fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v3\`:
`common3.py` (índice, referencia, ΔL0 y z con las reglas de la v3, `Z` como máximo sobre el disco de
radio T, TIF usable), `pool3.py` (embudo de M2), `geom3.py` (geometría de P), `null3.py` (muestreo del
nulo), `analiza3.py` (umbrales, fracciones, bootstrap y perfil acimutal), `g3.py` (control G),
`m1_3.py` (anillo, `zc_anillo` y fuente persistente). No modifiqué ningún archivo del repo salvo este
informe.

## Aviso de contaminación (léelo antes de tocar la v3)

Para responder "¿es P' un control justo?" hay que medir el campo de radiancia en la banda donde vive P,
y eso **acota el resultado de M2**. Queda declarado:

1. Medí `Z` en puntos sorteados y en sus reflejos sobre **533 pasadas RUTINA disjuntas de la muestra de
   M2** (negativos limpios fuera de Lastarria que **no** tienen patrón o no publican). El sesgo nulo que
   reporto es una predicción directa de lo que dará el brazo de la mediana pareada.
2. Los puntos que uso salen de la distribución empírica de (radio, acimut) de **los P de la muestra de
   M2**. O sea, conozco dónde cae nuestro cúmulo, aunque no medí `Z` en ninguno de esos P.
3. Medí el embudo completo de M2 hasta el filtro "P y P' con ΔL0", que obliga a evaluar si `Z(P)` y
   `Z(P')` existen. **Guardé sólo el booleano, nunca el valor**: no calculé `Z(P)`, `Z(P')` ni `Z(F)` de
   ninguna pasada de la muestra del veredicto.
4. Medí `zc_punto` por volcán sobre el pool nulo, el control G completo con la redacción de la v3, y la
   alcanzabilidad **geométrica** de la clase `F` en M1. **No** clasifiqué ninguna pasada de M1.

---

## Hallazgos nuevos (ordenados por gravedad)

### H1. P' no es un control justo para la mediana pareada: en pasadas donde MIROVA no vio nada, el punto "como nuestro P" le gana a su reflejo por +0,10, con intervalo que excluye el 0

- **Dónde**: v3 l. 117-118 (definición de P'), l. 148-149 ("es el control correcto para '¿hay calor
  aquí?', porque comparte el ruido del granule y la banda de distancia"), l. 186-188 (la mediana pareada
  con bootstrap), l. 192-193 (la condición del veredicto).
- **Evidencia** (`null3.py` más `analiza3.py`, 533 pasadas RUTINA ajenas a la muestra de M2, 10
  volcanes). En cada pasada sorteo un par (radio, acimut) de la distribución empírica de nuestros P del
  mismo volcán, lo pongo en esa pasada y comparo con su reflejo a través del cráter:

  | pareja | n | mediana pareada | IC 95 % (bootstrap estratificado) | fracción ≥ `zc_punto` |
  |---|---|---|---|---|
  | sorteo uniforme en la banda contra su reflejo (**control de instrumento**) | 533 | -0,0584 | [-0,1391, +0,0494] | 0,060 contra 0,083 |
  | punto "como nuestro P" contra su reflejo (**el nulo que importa**) | 533 | **+0,1014** | **[+0,0177, +0,1971]** | 0,081 contra 0,077 |

  El signo es positivo en 8 de los 10 volcanes (Copahue +0,343, Láscar +0,133, Chaitén +0,119, NdC
  +0,113, Tupungatito +0,102, PCC +0,080, Llaima +0,079, Villarrica +0,044; Planchón-Peteroa -0,142 e
  Isluga con n = 4). Es direccional y no de radio: la ventaja ponderada por el sector donde cae nuestro
  P, medida a radio fijo de 2,8 km, es **positiva en los 9 volcanes con n ≥ 10** (+0,004 a +0,129,
  promedio +0,039), contra un baseline de sectores uniformes que da 0,000 por construcción.
- **Qué pasa (el fenómeno)**: en el cono nevado la radiancia sigue la altitud (A69) y el borde de cota
  baja del disco de 3 km es donde `keep_peak` conserva su píxel. El exceso local ΔL0 sí cancela ese
  gradiente **en promedio**, como midió la ronda 1, y eso lo confirmo: comparando **la celda exacta** en
  vez del máximo, la mediana pareada es -0,0023 con IC [-0,1207, +0,1302], o sea simétrica. Lo que no
  cancela es el **estadístico que usa M2**, que es un máximo sobre las 11 o 12 celdas del disco de radio
  T. Un flanco con más textura (roca, quebradas, borde de nieve) da un máximo más alto aunque su exceso
  medio sea el mismo, y ese flanco es justo el que atrae a nuestro P. La mediana pareada mide
  rugosidad direccional, no calor.
- **Cómo se ve en el resultado**: "el cúmulo lejano cae sobre calor del campo de MIROVA" con la parte del
  intervalo satisfecha por el terreno, y la lectura de §8 ("es un rasgo térmico real que MIROVA también
  ve", categoría b) aplicada a lo que A69 describe como artefacto topográfico. Es el error que A72 pide
  evitar: clasificar mal el dato antes de decidir si el fix es de algoritmo o de display.
- **Cómo reproducirlo**: `python pool3.py && python geom3.py && python null3.py && python analiza3.py`
  desde el scratchpad `v3`.
- **Cómo calibrarlo** (tres opciones, hay que elegir antes de medir):
  1. **Control pareado en el terreno, no en el reflejo**: comparar `Z(P)` de la pasada con `Z` en **el
     mismo punto P** en otra pasada RUTINA del mismo volcán a más de 3 días (el placebo que la v3 ya
     define para M1, l. 142-146). Ese control tiene el mismo terreno, la misma textura y la misma
     dirección, así que el sesgo de H1 se cancela por construcción y lo que queda es "¿hay calor esta
     noche?".
  2. **Restar el nulo**: mantener P' y pre-registrar el desplazamiento nulo medido aquí, exigiendo que
     la mediana pareada observada supere la del nulo (no el 0), con el nulo recalculado en la misma
     corrida sobre pasadas disjuntas.
  3. **Sacar la mediana pareada del veredicto** y dejar sólo el brazo de fracciones, que sí es justo
     (ver VERIFICADO LIMPIO), informando la mediana como descriptiva.
- **CONFIRMADO. Gravedad 4.**

### H2. La salida "no se distingue de su reflejo" es la única que llevaría a mover algo, y el propio nulo la rompe en 43 de 60 repeticiones al n real

- **Dónde**: v3 l. 190-196 (las tres salidas), l. 211-215 (la tabla de qué se hace con el resultado).
- **Evidencia** (`analiza3.py`, aplicando la regla literal de la v3 sobre el nulo de H1, 60
  repeticiones por tamaño, bootstrap de 400 réplicas):

  | n de la submuestra | "no se distingue" | INCONCLUSO | "cae sobre calor" | el IC excluye el 0 |
  |---|---|---|---|---|
  | 30 (el mínimo de la v3) | 40 | 19 | **1** | 10 de 60 |
  | 100 | 47 | 13 | 0 | 10 de 60 |
  | **554 (el n real)** | **17** | **43** | 0 | 43 de 60 |

  La diferencia de fracciones del nulo se queda en 0,000 (p95 de +0,030 a n = 554), así que el corte de
  0,15 no se alcanza por ruido. Lo que falla es la segunda condición: con 554 pasadas el intervalo de la
  mediana pareada es angosto y la asimetría de H1 lo corre fuera del 0.
- **Qué pasa**: la regla castiga la precisión. Cuanto más grande la muestra, menos alcanzable es "no se
  distingue", porque el criterio pide que un intervalo estrecho contenga el 0 en un campo que no es
  isótropo. Al n que la propia v3 declara en §8, un campo sin nada que detectar devuelve INCONCLUSO el
  72 % de las veces. Y mirando la tabla de §8: "cae sobre calor" lleva a "no apagar `keep_peak`",
  INCONCLUSO lleva a "no mover nada", y la única fila que abre la puerta a re-evaluar el A/B de S143 es
  la que queda coja. **El pre-registro está sesgado hacia dejar `keep_peak` como está.**
- **Además**, la condición del intervalo en la salida "cae sobre calor" (l. 192-193) es casi gratis: el
  nulo la cumple en 43 de 60 al n real, así que el veredicto positivo queda decidido sólo por la
  diferencia de fracciones. La garantía que el texto promete ("y la mediana de la diferencia pareada es
  positiva con intervalo que excluye el 0") no filtra lo que dice filtrar. Es el mismo vicio que la
  ronda 2 documentó en N4, con otra forma.
- **Cómo se ve en el resultado**: un INCONCLUSO que parece salir de los datos cuando lo fijó la regla, o
  un "cae sobre calor" que se lee como si dos condiciones independientes lo respaldaran.
- **Cómo reproducirlo**: el bloque de simulación del veredicto al final de `analiza3.py`.
- **CONFIRMADO. Gravedad 4.**

### H3. El veredicto se agrega sobre 10 volcanes con n muy distinto y el bootstrap no dice por qué variable estratifica; tres volcanes ponen el 58 % de la muestra

- **Dónde**: v3 l. 180-184 (estratificación por etiqueta, volcán y tramo), l. 187-188 ("bootstrap
  estratificado (2.000 remuestreos)"), l. 190 (el veredicto "sobre los negativos limpios fuera de
  Lastarria").
- **Evidencia** (`pool3.py`): la muestra final se reparte Copahue 127, Llaima 97, Villarrica 96,
  Chaitén 85, Nevados de Chillán 46, Planchón-Peteroa 42, Tupungatito 27, Cordón Caulle 17, Isluga 9,
  Láscar 8. Copahue, Llaima y Villarrica son el 58 % y con Chaitén el 73 %. En el nulo, la diferencia de
  fracciones por volcán va de **-0,041 (Cordón Caulle) a +0,051 (Tupungatito)**, o sea los volcanes se
  comportan distinto entre sí ya sin señal.
- **Qué pasa**: el texto manda estratificar pero el veredicto se toma sobre una fracción agrupada, que
  es exactamente lo que el docstring de `scripts/banco_paridad.py:25-27` advierte que no sirve por
  Simpson, y lo que la retroalimentación de S126 ("estratificar por volcán, no sólo por sensor")
  documenta como invertidor de veredictos. Y "bootstrap estratificado" no nombra la variable: por volcán,
  por tramo o por etiqueta dan intervalos distintos.
- **Cómo se ve en el resultado**: un veredicto global que describe a Copahue y a Llaima y se presenta
  como propiedad de `keep_peak` en los 11.
- **Cómo reproducirlo**: la salida por volcán de `pool3.py` y el bloque "por volcan" de `analiza3.py`.
- **CONFIRMADO. Gravedad 3.**

### H4. La unidad del bootstrap es la pasada, pero las 635 pasadas son 383 noches de volcán: el intervalo sale más angosto de lo que corresponde

- **Dónde**: v3 l. 186-188.
- **Evidencia** (`pool3.py`): las pasadas de M2 con TIF pareado fuera de Lastarria son 635 y
  corresponden a **383 pares (volcán, noche)**, o sea 1,66 pasadas por noche. Dos pasadas de la misma
  noche ven el mismo estado del volcán y casi la misma nube, así que no son réplicas independientes.
- **Qué pasa**: remuestrear pasadas trata datos correlacionados como independientes y angosta el
  intervalo, que es justo la condición que decide en H2. Además A94 es explícita: la unidad en que el
  operador vive una alerta es la noche, no el record.
- **Cómo se ve en el resultado**: un intervalo que excluye el 0 con más facilidad todavía que la de H2.
- **Cómo reproducirlo**: `m2.groupby(['vol','noche']).ngroups` sobre el `pool3.pkl`.
- **CONFIRMADO. Gravedad 3.**

### H5. El piso de z que la v3 le agrega al control G no excluye ninguna pasada, y la compuerta de la mediana pasa con 0,079 km de margen

- **Dónde**: v3 l. 126-132 (control G: semilla con `z ≥ zc_punto`, mediana ≤ 0,5 km, mediana del
  desplazamiento < 0,19 km por eje).
- **Evidencia** (`g3.py`, 43 pasadas con alerta CONS y VRP ≥ 0,3 MW en Láscar y Villarrica, TIF usable):

  | métrica | valor | tope de la v3 |
  |---|---|---|
  | n | 43 (Láscar 42, Villarrica 1) | ≥ 8 |
  | semilla a ≤ 0,75 km del cráter | 0,907 | ≥ 0,80 |
  | mediana de esa distancia | 0,273 km | ≤ 0,5 km |
  | mediana norte-sur | **+0,111 km** | < 0,19 km |
  | mediana este-oeste | -0,063 km | < 0,19 km |
  | semillas que cumplen `z ≥ zc_punto` | **43 de 43** | |

  **G pasa.** Pero el piso de z no filtra nada: `zc_punto` de Láscar es 2,48 y la pasada ruidosa que la
  ronda 2 señaló (semilla a 3,79 km con z = 4,31) lo supera cómodamente. El piso está calibrado para el
  máximo sobre un disco de 12 celdas en la banda y se aplica al máximo sobre un disco de 4 km, de unas
  350 celdas: en pasadas RUTINA ese máximo ya supera `zc_punto` en 0,48 (Chaitén) a 0,89 (Láscar) de los
  casos. Es el mismo desajuste de estadístico que la ronda 2 describió en N7, movido de lugar.
- **Además, la regla no se puede ejecutar como está escrita**: "la mediana del desplazamiento en
  norte-sur y en este-oeste es menor que 0,19 km" está sobre una cantidad **con signo**, y una mediana de
  -5 km la cumple. Tiene que decir valor absoluto.
- **Cómo se ve en el resultado**: "G pasa con un piso de z que descarta las semillas de ruido", cuando no
  descartó ninguna.
- **Cómo reproducirlo**: `python g3.py`.
- **CONFIRMADO. Gravedad 3.**

### H6. En M1, la clase `F` es geométricamente imposible en las 12 pasadas de Lastarria, y la celda que decide ya es el máximo del anillo en 1 de cada 5 pasadas RUTINA

- **Dónde**: v3 l. 159-165 (semilla en el anillo y clases), l. 174-176 (cómo se lee M1).
- **Evidencia** (`m1_3.py`):
  - La separación entre `mirova_center` y el cráter en Lastarria es **0,12 km** y los `Distancia_km` de
    sus pasadas de M1 son 2,19, 2,40 y 2,70 km. Para que el anillo `|r − D| ≤ 0,6` toque el cráter hace
    falta `|D − separación| ≤ 1,35` km (0,6 del anillo más T). No se cumple en ninguna: **`F` alcanzable
    en 0 de las 12 pasadas compatibles de Lastarria**. Las clases posibles quedan `P`, `otro`,
    `indefinido` y `sin identidad`. Es el espejo del defecto N1 de la ronda 2, que hacía imposible `P`.
  - Sobre 31 pasadas RUTINA de Lastarria con TIF usable, el máximo del anillo cae a **2,363 km del
    cráter en 5 de 31** (con D = 2,19 y 2,40) y en **7 de 31** con D = 2,70, más un puñado de celdas
    vecinas fijas (2,112, 2,155 y 2,224 km). Es la misma celda que la ronda 1 encontró como semilla en
    14 alertas y 11 RUTINA.
  - `zc_anillo` sale 6,13 (D = 2,19, 116 celdas), 6,09 (D = 2,40, 128 celdas) y 5,81 (D = 2,70, 146
    celdas), contra una mediana del máximo del anillo en RUTINA de 2,8 a 3,0.
- **Qué pasa**: en el volcán que aporta 12 de las 13 pasadas de M1, la lectura declarada ("si las
  semillas con identidad caen sobre P, la coincidencia de radio de S143 era el mismo objeto") se puede
  cumplir porque el campo fumarólico Lazufre es la celda más brillante del anillo también las noches en
  que MIROVA no publicó nada. No es una lectura falsa, es una lectura poco informativa: no separa "es el
  objeto que MIROVA publicó esa noche" de "es la fuente que está siempre".
- **Cómo se ve en el resultado**: M1 dice "las semillas caen sobre P" y se lee como confirmación del
  objeto, cuando la misma celda aparece sin objeto publicado.
- **Cómo reproducirlo**: `python m1_3.py`.
- **CONFIRMADO. Gravedad 3.** (M1 no tiene veredicto, lo que baja el daño; pero la lectura de l. 174-176
  hay que reescribirla.)

### H7. "Pasadas RUTINA" tiene dos lecturas que dan pools de calibración distintos por un factor de hasta 6, y `zc_punto` es un percentil 95 con intervalo muy ancho

- **Dónde**: v3 l. 104-108 (la calibración de `zc_punto` "en las pasadas RUTINA ... con TIF usable del
  mismo volcán").
- **Evidencia**:
  - La definición entre paréntesis ("fila CONS RUTINA con VRP 0, sin alerta ni falso positivo esa noche
    y sensor") es una propiedad de **la fila de MIROVA**, pero la etiqueta `neg_limpio` de
    `scripts/banco_paridad.py:268-288` exige además **un record nuestro a ±120 s**. Los dos pools
    difieren (`m1_3.py` y el bloque de pools): por fila de MIROVA con TIF propio hay hasta 80 pasadas en
    Isluga y 92 en Láscar; por record nuestro con TIF usable quedan **13 en Isluga y 36 en Láscar**.
  - Con ese n, el percentil 95 es casi el máximo de la muestra. El bootstrap del propio `zc_punto` da
    intervalos anchos incluso donde hay más datos: Chaitén 4,64 con IC [3,17, 6,26] sobre 76 pasadas,
    Láscar 2,48 con IC [1,99, 3,73] sobre 28.
- **Qué pasa**: el umbral que define el brazo que sí decide (las fracciones) se estima con ruido grande y
  la v3 no dice cuál de las dos poblaciones lo calibra. Mitiga que el mismo umbral se aplica a P y a P',
  así que la **diferencia** es robusta: recalculada con percentil 85, 90, 95 y 99 el nulo da -0,011,
  -0,017, +0,004 y +0,009.
- **Cómo reproducirlo**: los dos bloques finales de mi sesión sobre `null3.pkl` y el índice
  (`analiza3.py` y el bloque de pools por lectura).
- **CONFIRMADO. Gravedad 2.**

### H8. Los números de §0 y §9 sobre la compatibilidad de radio no reproducen, y en Cordón Caulle y Tupungatito la compatibilidad se cumple por la posición del centro de grilla, no por nuestro cúmulo

- **Dónde**: v3 l. 24-27 (la tabla "fuera de Lastarria 19 elegibles, 1 compatible") y l. 226-228 (el
  embudo, "fuera de Lastarria queda 1").
- **Evidencia** (`m1_3.py`, records de producción con alerta CONS, patrón, `d(P,F) ≥ 1,5` y TIF usable,
  o sea sin el filtro de región que aplicó la ronda 2): 39 pasadas, **24 fuera de Lastarria con 4
  compatibles** (Láscar 1, Cordón Caulle 3) y **15 en Lastarria con 12 compatibles**. El número de
  Lastarria coincide con el de la v3; el de afuera no (4 contra 1). La diferencia puede venir del filtro
  de región y del uso de records del brazo control en las noches de S143, que no repliqué.
  - Y las 3 de Cordón Caulle no son casos de la pregunta: ahí `mirova_center` está a **7,57 km** del
    cráter y los `Distancia_km` de MIROVA son 7,65, 7,73 y 8,10 km, o sea MIROVA está describiendo algo
    cerca del cráter. Cualquier punto nuestro cercano al cráter cumple `|r_P(mirova_center) − D| ≤ 0,55`
    por aritmética del centro de grilla. Lo mismo vale para Tupungatito (separación 4,86 km). La
    compatibilidad de radio sólo es informativa donde `mirova_center` casi coincide con el cráter.
- **Qué pasa**: la conclusión de fondo de la v3 (la coincidencia de radio es hoy un fenómeno de
  Lastarria) **se sostiene**, pero la cifra publicada y el motivo no. Un lector que use el "1" para
  justificar que M1 no se puede hacer afuera va a encontrar 4 pasadas y va a dudar de todo lo demás.
- **Cómo reproducirlo**: `python m1_3.py`.
- **CONFIRMADO para mi pool. Gravedad 2.**

### H9. El tamaño de la muestra que declara §8 está subestimado, y el embudo lo domina un filtro que el texto no nombra: el 43 % de las pasadas no tiene TIF

- **Dónde**: v3 l. 217-219 ("del orden de 850 pasadas con patrón y etiqueta `neg_limpio` aproximada,
  antes de exigir TIF usable").
- **Evidencia** (`pool3.py`, ventana 2026-05-09 a 2026-09-19, VIIRS 375 nocturno, 11 volcanes):

  | etapa | n |
  |---|---|
  | records nocturnos VIIRS 375 | 6.241 |
  | con patrón | 2.999 |
  | con patrón y publicados | 2.627 |
  | de esos, `neg_limpio` | 1.134 (1.113 fuera de Lastarria) |
  | con TIF a ±120 s | 635 |
  | con TIF usable | **554** |
  | con ΔL0 en P y en P' | **554** |

  Los descartes de usabilidad son: 478 sin TIF pareado, 58 por md5 repetido, 19 por mediana ≥ 0,2 y 4
  por más de 10 % de celdas sin dato en el disco de 4 km.
- **Qué pasa**: el número real antes de exigir TIF es 1.134 (o 1.258 si no se exige publicar), no 850. Y
  el filtro que más corta no es ninguno de los cinco criterios de "TIF usable" sino la ausencia de imagen
  en el archivo. Conviene decirlo, porque es el que un lector va a sospechar de selectivo.
- **CONFIRMADO. Gravedad 2.**

### H10. Detalles que no se pueden ejecutar como están escritos

- **"lecturas opuestas" entre tramos** (l. 198-199) no está definida: si un tramo da "no se distingue" y
  el otro INCONCLUSO, ¿son opuestas? Con 431 pasadas antes de #535 y 123 después, y con el
  comportamiento de H2, esa combinación es la más probable.
- **"X sorteado uniformemente en el anillo"** (l. 106-107) no dice si es uniforme en área o en radio. Yo
  usé área. Con uniforme en radio se sobremuestrea el borde interno y `zc_punto` cambia.
- **"un sorteo por pasada, `random.Random(144)`, orden de extracción por (volcan, datetime_utc)"**
  (l. 107-108) no dice si el generador es uno solo para todos los volcanes o uno por volcán. Son dos
  `zc_punto` distintos y los dos son "semilla 144".
- **"MAD de ΔL0 sobre las celdas con dato del raster"** (l. 96-97): "con dato" puede ser "con L" o "con
  ΔL0", que no son el mismo conjunto porque ΔL0 exige 5 vecinas. Yo usé las celdas con ΔL0.
- **CONFIRMADO (lectura del texto). Gravedad 1.**

---

## VERIFICADO LIMPIO

- **M2 tiene muestra de sobra y el corte de la v3 funciona**: 554 pasadas de negativos limpios fuera de
  Lastarria con patrón, publicadas, con TIF usable y con ΔL0 en P y en P'. Muy por encima del mínimo de
  30, y los dos tramos también lo superan (431 antes de #535 y 123 después).
- **El filtro "P y P' con ΔL0" no descarta nada**: 554 de 554. La geometría del reflejo no saca ninguna
  pasada por caer fuera del raster o sobre celdas vacías.
- **El brazo de fracciones es justo**: un sorteo uniforme y su reflejo dan 0,060 y 0,083 de exceso sobre
  `zc_punto`, con IC de la diferencia [-0,054, +0,008], que contiene el 0; y con el punto "como nuestro
  P" la diferencia nula es +0,004. El corte de 0,05 y el de 0,15 no se alcanzan por ruido al n real (p95
  de +0,030 en submuestras de 554). El problema de H1 es del otro brazo.
- **El radio del control es correcto**: el 96 % de nuestros P vive en la banda de 1,5 a 3,5 km donde se
  calibra `zc_punto`, con mediana de 2,79 km (el borde del disco de 3 km del Test 1), y el reflejo
  conserva el radio exactamente. La asimetría de H1 es de acimut, no de distancia.
- **El exceso local sí cancela el gradiente topográfico en la celda**: comparando la celda exacta en vez
  del máximo, la mediana pareada del nulo es -0,0023 con IC [-0,1207, +0,1302]. La afirmación de §2
  (l. 67-69) es correcta tal como está escrita; lo que la rompe es el máximo sobre el disco.
- **La celda y T son los que dice el texto**: entre 0,374 y 0,385 km en los 10 volcanes medidos, todos
  EPSG:4326 de 134 × 134. T = 0,75 km son dos celdas de radio y unas 11 o 12 celdas de disco.
- **El control G pasa con la redacción de la v3** (n = 43, 0,907 a ≤ 0,75 km, mediana 0,273 km,
  medianas de desplazamiento +0,111 y -0,063 km). El cambio de promedio a mediana que pidió la ronda 2
  resuelve el problema de la pasada única: el promedio norte-sur sigue en +0,165 km, la mediana baja a
  +0,111.
- **§9 acierta en los tramos de las pasadas con alerta**: de 65 pasadas con alerta, patrón y TIF pareado,
  **3** son posteriores a #535.
- **La disponibilidad de TIF no selecciona por calor**: hay imagen a ±120 s en el 48 % de las pasadas
  `pos` y en el 59 % de las `neg_limpio` (las `sin_info` bajan a 17 %, que es lo esperable porque MIROVA
  no procesó esa pasada).
- **La sensibilidad por latencia es viable**: el 78 % de las pasadas de M2 con TIF pareado tiene latencia
  ≤ 8 h, así que repetir todo con ese corte no deja la muestra vacía.
- **Los records del control siguen congelados**: 19 archivos en `git ls-files
  experiments/_s144_keep_peak_direccion/control_s143`.

**No verificado** (queda abierto): los `Z(P)`, `Z(P')` y `Z(F)` de la muestra de M2 y las clases de M1
(no los calculé a propósito); si el remuestreo geográfico de MIROVA corre la posición en los nevados
(G sigue validando casi sólo Láscar, igual que en las dos rondas anteriores); el embudo exacto de M1 con
el filtro de región y los records del brazo control de las noches de S143 (usé sólo producción, ver H8);
la representatividad del pool nulo, que por construcción son pasadas sin patrón o sin publicar y podrían
ser noches más nubladas.

---

## Correcciones para una v4, por gravedad

1. **(4) Arreglar el control de la mediana pareada (H1).** Elegir antes de medir entre: (a) reemplazar
   P' por el mismo punto P en otra pasada RUTINA del volcán a más de 3 días, que cancela el terreno por
   construcción; (b) mantener P' y pre-registrar la corrección del nulo (+0,10 medido acá,
   recalculándolo en la misma corrida sobre pasadas disjuntas); o (c) sacar la mediana pareada del
   veredicto y dejarla descriptiva. Si se mantiene P', decir explícitamente en §7 que el brazo pareado
   mide rugosidad direccional y no presencia de calor.
2. **(4) Rehacer la regla de veredicto para que las tres salidas sean alcanzables al n real (H2).** Con
   el criterio actual, un campo sin nada que detectar da INCONCLUSO 43 de 60 veces con 554 pasadas, y la
   única salida que permitiría re-evaluar el A/B de S143 es la que se rompe. Una forma: usar un criterio
   de equivalencia declarado en unidades del objeto (por ejemplo, que el intervalo de la diferencia de
   fracciones quede entero dentro de ±0,05), en vez de pedir que un intervalo contenga el 0.
3. **(3) Decidir la agregación entre volcanes y nombrar la variable del bootstrap (H3).** Un veredicto
   por mediana de las diferencias por volcán, o un voto por volcán con n mínimo, evita que Copahue,
   Llaima y Villarrica decidan por los 11.
4. **(3) Remuestrear por noche de volcán, no por pasada (H4)**, que además es la unidad de A94: 635
   pasadas son 383 noches.
5. **(3) Arreglar el control G (H5)**: escribir la compuerta sobre el **valor absoluto** de la mediana, y
   o bien calibrar el piso de z con el mismo estadístico que usa G (el máximo sobre el disco de 4 km en
   pasadas RUTINA), o declarar que el piso no excluye nada y sacarlo.
6. **(3) Reescribir cómo se lee M1 (H6)**: decir que en Lastarria la clase `F` es geométricamente
   imposible, que las salidas reales son `P`, `otro`, `indefinido` y `sin identidad`, y que "la semilla
   cae sobre P" no separa el objeto publicado esa noche de la fuente fumarólica permanente, que ya es el
   máximo del anillo en 5 a 7 de 31 pasadas RUTINA.
7. **(2) Fijar qué población es "pasada RUTINA" (H7)**: la fila de MIROVA o la etiqueta `neg_limpio` de
   `banco_paridad`. Informar el n por volcán y el intervalo de `zc_punto`, y declarar que en Isluga
   (13 pasadas por la lectura estrecha) el percentil 95 es casi el máximo.
8. **(2) Corregir §0 y §9 con el embudo reproducible (H8, H9)**: 1.134 pasadas con patrón, publicadas y
   `neg_limpio`; 554 con todos los filtros; y la compatibilidad de radio medida de nuevo, diciendo que en
   Cordón Caulle y Tupungatito se cumple por la separación entre `mirova_center` y el cráter y no por
   nuestro cúmulo.
9. **(1) Cerrar los detalles de H10**: qué son "lecturas opuestas", uniforme en área o en radio, un
   generador o uno por volcán, y qué conjunto es "celdas con dato".

**Resumen**: la v3 resolvió el defecto que hacía imposible una clase y consiguió una muestra grande y
limpia. Lo que queda por arreglar es el control: P' iguala la distancia pero no el terreno, y con el
estadístico de máximo eso basta para inclinar el brazo pareado antes de que haya nada que medir. Con la
corrección 1 y la 2 tomadas en serio, M2 queda en pie y puede decidir.
