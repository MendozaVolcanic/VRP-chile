# Quinto verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v5)

**Veredicto: el instrumento nuevo funciona y es el primero de las cinco rondas que lo hace, pero los
tres controles que lo vigilan están mal planteados y la regla de decisión no descuenta el residuo que
el propio instrumento deja.** Lo medí: la pasada cruzada corta el **87 %** del sesgo de selección
(de `D = +0,1091` con la imagen propia a `+0,0145` sobre las mismas 165 pasadas), el sitio donde cae
nuestro cúmulo **no** es un sitio persistentemente caliente (brazo de otra noche: `+0,0005`, intervalo
[-0,0173, +0,0178]) y el nulo con un punto sorteado da `-0,0046`. Lo que queda es un residuo de
**+0,0251, intervalo [+0,0049, +0,0472]**, que no incluye al cero, y que se concentra entero en las
pasadas separadas por menos de 45 minutos: es un transitorio de menos de una hora. Ese residuo es la
mitad del umbral con que se decide, la regla no lo resta, y la salida de equivalencia (± 0,05) declara
"no tiene correlato" justo por encima de él. Además **C1 atenúa el sesgo exactamente cinco veces**, así
que habría dejado pasar en verde al instrumento que la ronda 4 refutó, y **C2 no es un control**: mide
lo mismo que el veredicto en un estrato hermano, o sea falla precisamente cuando la hipótesis es
verdadera.

Documento verificado:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v5 del 2026-09-19, rama `s144-prereg-keep-peak-direccion`, sobre el commit `c92171901`).

Mis scripts están fuera del repo, en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v5\`:
`base5.py` y `var5.py` y `var5b.py` y `s0_5.py` (conteos de §0), `zc5.py` (`zc_punto` con la regla
literal de la v5), `cruz5.py` (el instrumento completo de §5: imagen cruzada, sitios de referencia,
C1 y C2), `analiza5.py` (el análisis y el arranque de los intervalos), `persist5.py` (brazo de otra
noche), `embudo5.py` (muestra del veredicto), `dia5.py` (día contra noche de la imagen cruzada),
`ver5.py` (simulación de la regla), `misc5.py` y `misc5b.py` y `h5.py` y `resid5.py`. Reusan
`common3.py` y `pool3.pkl` de la ronda 3 y `base4.py` y `pools4.pkl` de la ronda 4. No modifiqué
ningún archivo del repo salvo este informe.

## Aviso de contaminación (léelo antes de tocar la v5)

Para contestar "¿la pasada cruzada corta de verdad el sesgo?" hay que correr el procedimiento entero
con `Z` puesto en nuestro propio P. Queda declarado:

1. Corrí el procedimiento completo de §5 con imagen cruzada y con imagen propia sobre las **1.289
   pasadas con patrón, publicadas, fuera de Lastarria, con etiqueta `far_ref` o `sin_info`**, o sea
   **fuera de la muestra del veredicto**. De ahí salen todos los números de la tabla de H1. Esto acota
   y predice el orden de magnitud de M2, igual que hizo la ronda 4, y es la contaminación más fuerte
   de este informe.
2. Corrí el mismo procedimiento con un punto **sorteado** sobre 654 pasadas `neg_limpio` **no**
   (con patrón y publicadas), que son ajenas a la muestra del veredicto.
3. Evalué `Z` en las **posiciones P** de pasadas que sí pertenecen a la muestra del veredicto, porque
   esas posiciones son sitios de referencia de otras pasadas. Nunca en el ráster que le corresponde a
   esa pasada, así que ningún `e_p` del veredicto quedó calculado.
4. Conté el embudo de la muestra del veredicto (imagen cruzada usable y cantidad de sitios de
   referencia). Eso obliga a abrir los rásteres cruzados, pero **no evalué `Z` en el P de ninguna de
   esas 1.113 pasadas** y **no clasifiqué ninguna pasada de M1**.

---

## Hallazgos nuevos (ordenados por gravedad)

### H1. La pasada cruzada corta el 87 % del sesgo, pero deja un residuo de +0,025 cuyo intervalo no incluye al cero, y la regla sigue midiendo contra el cero

- **Dónde**: v5 l. 31-34 (la pasada cruzada corta la maldición del ganador), l. 149-151 (`e_p`, `r_p`,
  `d_p`), l. 164-167 (el control C2), l. 228-232 (las dos salidas del veredicto).
- **Evidencia** (`python cruz5.py && python analiza5.py && python persist5.py`, todo sobre pasadas
  fuera de la muestra del veredicto):

  | qué se mide, con el procedimiento completo de §5 | n | `D` | IC 95 % | tasa obs | tasa ref |
  |---|---|---|---|---|---|
  | imagen **propia** (lo que la ronda 4 refutó), todas las que la tienen | 194 | **+0,1031** | [+0,0481, +0,1588] | 0,149 | 0,046 |
  | imagen **propia**, intersección con las que tienen cruzada | 165 | **+0,1091** | [+0,0512, +0,1693] | 0,152 | 0,042 |
  | imagen **cruzada**, esas mismas 165 | 165 | **+0,0145** | [-0,0287, +0,0556] | 0,091 | 0,076 |
  | imagen **cruzada**, las 884 que la tienen | 884 | **+0,0251** | [+0,0049, +0,0472] | 0,092 | 0,067 |
  | **otra noche** (ráster a más de 3 días, mismo P, los mismos 5 sitios) | 1289 | **+0,0005** | [-0,0173, +0,0178] | 0,078 | 0,077 |
  | **nulo**: punto sorteado del anillo, imagen cruzada | 654 | **-0,0046** | [-0,0257, +0,0162] | 0,052 | 0,057 |

- **De dónde viene el residuo** (`python resid5.py`): no es del sitio. El brazo de otra noche da
  `+0,0005`, o sea nuestro P **no** es un lugar persistentemente más caliente que los otros sitios
  donde publicamos. Y no es de la población de referencia: dentro de las mismas pasadas y los mismos
  rásteres, un punto sorteado del anillo excede el umbral el **5,20 %** de las veces y los sitios P el
  **5,66 %**, o sea son poblaciones equivalentes (esto, de paso, es la refutación empírica del defecto
  que hundió a la v3). El residuo es **de esa noche y de corta duración**:

  | separación entre las dos pasadas | n | `D` | tasa obs | tasa ref |
  |---|---|---|---|---|
  | menos de 45 min | 477 | **+0,0470** | 0,107 | 0,060 |
  | 45 a 60 min | 247 | -0,0097 | 0,065 | 0,074 |
  | 60 a 120 min | 134 | +0,0060 | 0,082 | 0,076 |
  | más de 120 min | 26 | +0,0538 | 0,115 | 0,062 |

- **Qué pasa (el fenómeno)**: una fuente térmica permanente (lago de lava, campo fumarólico,
  lacolito, que es la categoría b de A54) estaría en el ráster de cualquier noche, y el brazo de otra
  noche la habría visto. Dio cero. Lo que sí hay es algo que está en la pasada de al lado y se apaga
  en menos de una hora. Eso es la firma de una nube o de un estado de escena de esa noche, no de un
  foco. Es exactamente el límite que §9 declara con todas sus letras, sólo que ahora está medido y
  **no es despreciable**: vale la mitad del umbral con que se decide.
- **Cómo se ve en el resultado**: `D` en los negativos limpios sale del orden de +0,02 a +0,03, el
  intervalo cabe dentro de ± 0,05, el veredicto dice **"no se distingue de los sitios donde publicamos
  otras noches"**, y la fila 1 de la tabla de §8 lo manda a "no tiene correlato en el campo de MIROVA,
  pre-registrar una cota y re-evaluar el A/B S143", o sea hacia apagar `keep_peak`. Pero el mismo
  instrumento, en el estrato hermano, midió un correlato de +0,025 con el intervalo por encima de
  cero. La equivalencia se declara sobre un efecto que existe.
- **Cómo reproducirlo**: `python zc5.py && python cruz5.py && python analiza5.py && python persist5.py
  && python resid5.py`.
- **Cómo arreglarlo** (elegir antes de medir): (a) medir la banda de equivalencia **contra el nivel del
  instrumento**, no contra cero, o sea declarar que "no se distingue" exige que el intervalo quede
  dentro de ± 0,05 **alrededor del residuo medido**, y que el positivo exija superarlo; o (b) fijar el
  estadístico sobre la **diferencia entre estratos** (negativos limpios contra `sin_info`), que es la
  única comparación donde el residuo se cancela; o (c) declarar en §8 que la salida de equivalencia
  **no autoriza a apagar `keep_peak`** cuando el residuo del estrato hermano es positivo.
- **CONFIRMADO. Gravedad 4.**

### H2. C2 no es un control de instrumento: mide lo mismo que el veredicto en un estrato hermano, así que se pone rojo justo cuando la hipótesis es verdadera

- **Dónde**: v5 l. 163-167 (C2, "la corrida cruzada sobre esas mismas pasadas debe quedar por debajo de
  +0,05; si no, la pasada cruzada no alcanzó a cortar el sesgo y la medida es INCONCLUSA").
- **Evidencia**: las pasadas que C2 usa (`far_ref` y `sin_info` fuera de Lastarria) son pasadas **con
  el mismo patrón y publicadas**, exactamente como las del veredicto; lo único que las separa es la
  etiqueta que MIROVA puso esa noche. Medí sobre ellas, con imagen cruzada, `D = +0,0251`
  [+0,0049, +0,0472], y sobre el mismo instrumento con un punto sorteado, `D = -0,0046`. O sea: el
  procedimiento **sí** tiene un nulo bien definido (el punto sorteado), y no es el que C2 usa.
- **Qué pasa**: si nuestro cúmulo lejano cae de verdad sobre excesos del campo de MIROVA, ese hecho
  ocurre también en las `sin_info` (ahí MIROVA no publicó ninguna fila, que es justamente donde A54
  dice que puede vivir la categoría b). Entonces la corrida cruzada de C2 sube por encima de +0,05 y
  la regla declara INCONCLUSA la medida **porque la hipótesis es cierta**. Y al revés, que C2 pase con
  +0,025 no dice que el instrumento esté limpio: dice que el efecto es chico en ese estrato. El
  control y la medida son la misma cantidad.
- **Cómo se ve en el resultado**: un INCONCLUSO presentado como "el instrumento no alcanzó a cortar el
  sesgo" cuando lo que ocurrió es que se midió señal; o un "C2 en verde" presentado como certificado
  de limpieza cuando es una estimación del tamaño del efecto.
- **Cómo reproducirlo**: comparar las filas 4 y 6 de la tabla de H1 (`analiza5.py`, secciones 1 y 2).
- **Cómo arreglarlo**: el control de instrumento es el **punto sorteado con imagen cruzada** (fila 6);
  las `far_ref` y `sin_info` deben reportarse como **estrato de comparación**, no como compuerta.
- **CONFIRMADO. Gravedad 4.**

### H3. C1 atenúa el sesgo exactamente cinco veces: pasa en verde sobre el instrumento que la ronda 4 refutó

- **Dónde**: v5 l. 159-162 ("C1, intercambio de roles ... Debe dar `D` dentro de ± 0,05. Si no, el
  instrumento está sesgado y la medida es INCONCLUSA").
- **Evidencia**: con el observado `p_obs` y la referencia `p_ref`, al intercambiar roles el esperado es
  `p_ref − (4·p_ref + p_obs)/5 = −(p_obs − p_ref)/5`, o sea **menos un quinto del sesgo**. Medido
  (`analiza5.py`, sección 3):

  | corrida | n | C1 | IC 95 % | sesgo real de esa corrida |
  |---|---|---|---|---|
  | imagen **propia** fuera de muestra | 194 | **-0,0206** | [-0,0318, -0,0096] | **+0,1031** |
  | imagen cruzada fuera de muestra | 884 | -0,0050 | [-0,0094, -0,0010] | +0,0251 |
  | nulo con punto sorteado | 654 | +0,0009 | [-0,0032, +0,0051] | -0,0046 |

  El -0,0206 del brazo propio es -0,1031/5 con tres decimales. La banda de ± 0,05 de C1 tolera
  entonces un sesgo de **± 0,25**, cinco veces el umbral con que se decide.
- **Qué pasa**: si la v5 hubiera conservado la imagen propia, C1 habría dado -0,021, adentro de la
  banda, y la medida habría salido adelante con el sesgo de +0,10 intacto. Es el mismo defecto que la
  ronda 4 le encontró al control anterior (pasa en verde mientras la medida ya está inclinada), sólo
  que ahora está cuantificado.
- **Cómo se ve en el resultado**: "C1 dio -0,02, el instrumento está limpio" escrito al lado de un
  veredicto positivo.
- **Cómo reproducirlo**: `python analiza5.py`, sección 3.
- **Cómo arreglarlo**: o se declara la banda de C1 en ± 0,01 (que es ± 0,05 dividido por 5), o se
  reescribe C1 como `5 × |C1|` contra ± 0,05, o se lo saca y se deja el nulo del punto sorteado como
  único control de instrumento, que es el que sí mide de frente.
- **CONFIRMADO (analítico y medido). Gravedad 4.**

### H4. "Esas mismas pasadas" de C2 son tres conjuntos distintos, y C2 pasa o falla según cuál y según si el corte es el punto o el intervalo

- **Dónde**: v5 l. 164-167 ("sobre pasadas con patrón y publicadas fuera de la muestra del veredicto
  (`far_ref` y `sin_info` fuera de Lastarria, 194 pasadas) ... La corrida **cruzada** sobre esas mismas
  pasadas debe quedar por debajo de +0,05").
- **Evidencia** (`analiza5.py`, sección 1): el estrato `far_ref` más `sin_info` fuera de Lastarria tiene
  **1.289 pasadas**, no 194. Las 194 son las que tienen **TIF propio usable**, que es lo que necesita
  el brazo de imagen propia y no el cruzado. Con imagen cruzada hay **884**. En las dos a la vez hay
  **165**. Y los resultados no coinciden:

  | conjunto | n | `D` cruzado | IC 95 % | ¿pasa el corte de +0,05? |
  |---|---|---|---|---|
  | las 194 del texto, intersectadas con las que tienen cruzada | 165 | +0,0145 | [-0,0287, **+0,0556**] | sí por el punto, **no** por el extremo del intervalo |
  | todas las que tienen cruzada | 884 | +0,0251 | [+0,0049, +0,0472] | sí por los dos |

- **Qué pasa**: el pre-registro no dice si el corte se aplica al estimador o al intervalo, ni cuál de
  los tres conjuntos es "esas mismas pasadas". Dos implementadores honestos obtienen INCONCLUSA y
  ejecutable respectivamente, sobre el mismo dato.
- **Cómo se ve en el resultado**: una discusión sobre si C2 pasó, resuelta después de mirar el número.
- **Cómo reproducirlo**: `python analiza5.py`, sección 1.
- **CONFIRMADO. Gravedad 3.**

### H5. El residuo depende de la separación temporal entre las dos pasadas, y la muestra del veredicto se concentra justo en el borde donde cambia

- **Dónde**: v5 l. 136-139 ("se toma la más cercana en el tiempo ... Se informa la distribución de
  |t_q − t_p|"). Se informa, pero no se fija ni se estratifica.
- **Evidencia**: la tabla de brechas de H1 (menos de 45 min da `+0,0470` sobre 477 pasadas; de 45 a
  60 min da `-0,0097` sobre 247). Y en la muestra del veredicto (`embudo5.py`) la separación tiene
  mediana **48 min**, con p25 = 42 y p75 = 54, o sea el grueso de la muestra cae repartido a los dos
  lados de ese borde. Qué brecha le toca a cada pasada depende de qué par de satélites pasó esa noche,
  que es ajeno al fenómeno.
- **Qué pasa**: el valor de `D` que va a salir depende de una variable de mezcla que nadie fijó. Dos
  ventanas de fechas con distinta constelación disponible dan `D` distintos sin que cambie el volcán.
  Es la misma clase de problema que A104 resolvió partiendo por tramos.
- **Cómo se ve en el resultado**: un `D` global que no se puede comparar con el de ningún otro corte
  de la misma muestra.
- **Cómo reproducirlo**: `python resid5.py` y el bloque de |dt| de `python embudo5.py`.
- **Cómo arreglarlo**: declarar antes de medir un tope de |t_q − t_p| (por ejemplo 90 min) y reportar
  `D` estratificado por brecha, o al menos informar `D` por bin como medida principal.
- **CONFIRMADO. Gravedad 3.**

### H6. El filtro de región de §6 saca la única pasada de Láscar: M1 son 12 pasadas en un volcán, y ahí la clase `F` es inalcanzable en todo M1

- **Dónde**: v5 l. 186-187 ("**13 pasadas en 2 volcanes**: 12 de Lastarria y 1 de Láscar (H6)"),
  l. 196-199 (el declarado de antemano, que separa Lastarria de "la pasada de Láscar, donde `F` sí es
  alcanzable"), l. 79 (§3, "hoy sólo se puede hacer en Lastarria y en una pasada de Láscar").
- **Evidencia** (`python misc5b.py`, último bloque): la pasada de Láscar del pool es la del
  **2026-05-19 06:24 UTC**, con `Distancia_km` = 0,84 km. Su `P` está a 0,45 km del cráter (dentro del
  disco de 3,4 km) pero su **`F` está a 4,44 km del cráter y a 3,72 km de `mirova_center`**, mientras
  el segundo disco mide `Distancia_km` + 1 = 1,84 km. `F` queda fuera de los dos discos, y §6 exige
  "con **P y F** dentro de la región de búsqueda". La pasada sale del universo.
- **Y hay más**: ese caso no es un cúmulo lejano. Es `P` pegado al cráter y `F` a 4,44 km, o sea el
  patrón A46 y A81 al revés (el `final_hotspot` se fue lejos), no el objeto que D19 describe.
- **Qué pasa**: M1 queda reducida a **12 pasadas de Lastarria**, el volcán que §1 declara contaminado,
  y la clase `F` pasa a ser inalcanzable **en todo M1**, no sólo en Lastarria. Esto es exactamente el
  matiz que la ronda 4 marcó como no comprobado, y va en contra del texto.
- **Cómo reproducirlo**: `python m1_3.py` desde el scratchpad `v3` (reproduce el pool: Lastarria 15 con
  12 compatibles, 24 fuera con 4 compatibles, de ellas Láscar 1 y Cordón Caulle 3) y después el último
  bloque de `python misc5b.py`, que aplica el filtro de región a esa pasada de Láscar.
- **CONFIRMADO. Gravedad 3.**

### H7. `zc_punto` no reproduce con la regla literal de la propia §4: Chaitén da 4,22 y no 3,63, y la tabla entera se mueve

- **Dónde**: v5 l. 112-117 (la regla nueva: anillo de **1,5 a 3,0 km**, `random.Random(144)`, volcanes
  alfabéticos, dos números por pasada), l. 123-125 ("Queda declarado que con la regla literal Chaitén
  da **3,63** [3,13, 4,66] y que Isluga se calibra con 13 pasadas y su intervalo va de **2,50** a
  7,69").
- **Evidencia** (`python zc5.py`, que implementa la regla tal como está escrita):

  | volcán | n | `zc_punto` v5 | IC 95 % | valor citado (ronda 4, anillo 1,5 a 3,5) |
  |---|---|---|---|---|
  | Chaitén | 161 | **4,22** | [3,19, 4,66] | 3,63 |
  | Cordón Caulle | 91 | **4,25** | [3,23, 5,11] | 3,65 |
  | Planchón-Peteroa | 86 | **3,23** | [2,41, 4,77] | 2,99 |
  | Nevados de Chillán | 147 | **2,47** | [2,07, 3,17] | 2,67 |
  | Tupungatito | 66 | 3,38 | [2,51, 3,72] | 3,43 |
  | Láscar | 36 | 3,74 | [2,69, 3,91] | 3,71 |
  | Villarrica | 152 | 2,89 | [2,41, 3,81] | 2,81 |
  | Llaima | 167 | 2,38 | [2,16, 2,81] | 2,36 |
  | Copahue | 168 | 2,67 | [2,21, 2,80] | 2,63 |
  | Isluga | **13** | 6,07 | **[2,04, 7,69]** | 6,07 [2,50, 7,69] |

  Los n por volcán sí reproducen exactos los de la ronda 4 (Chaitén 161, Copahue 168, Llaima 167,
  Villarrica 152, NdC 147, CC 91, PP 86, Tupungatito 66, Láscar 36, Isluga 13).
- **Qué pasa**: la v5 corrigió el anillo (era la recomendación 5 de la ronda 4) y conservó los números
  que la ronda 4 había medido **con el anillo viejo**. Es literalmente el mismo error que esa ronda
  marcó como H4, repetido una versión después. El umbral es el que decide `e_p` y `r_p`, así que no es
  cosmético: Chaitén se mueve 0,59 y Cordón Caulle 0,60.
- **Cómo se ve en el resultado**: alguien comprueba el umbral de Chaitén, encuentra 4,22 donde el
  pre-registro anunció 3,63, y deja de confiar en el resto de la tabla.
- **Cómo reproducirlo**: `python zc5.py`.
- **CONFIRMADO. Gravedad 2.**

### H8. Los conteos de §0 no reproducen, y el número que importa para el veredicto no es 1.824 sino 711 de 1.113

- **Dónde**: v5 l. 34-37 ("de 2.541 pasadas con el patrón, **1.824 tienen otra pasada esa noche con
  TIF** (Copahue 287, Villarrica 248, Llaima 242, NdC 209, Lastarria 206, PP 160, Chaitén 158,
  Tupungatito 123, Láscar 81, Isluga 71, Cordón Caulle 39)").
- **Evidencia**:
  - El denominador no existe con ninguna lectura. §4 define patrón incluyendo que el record publique,
    así que "pasadas con el patrón" son **2.627**; sin exigir publicación son **2.999**
    (`python base5.py`). Ninguna da 2.541.
  - El numerador, con el mismo filtro de usabilidad que el resto del documento (`python s0_5.py`), da
    **1.962** sobre las 2.999 y **1.744** sobre las 2.627. Por volcán acierta exacto en los dos más
    grandes (Copahue 287, Villarrica 248) y se va lejos en otros: Chaitén 198 contra 158, Isluga 116
    contra 71, Cordón Caulle 68 contra 39.
  - **Lo que sí medí y es lo que decide**: la muestra del veredicto son **1.113** pasadas (patrón,
    publicadas, `neg_limpio`, fuera de Lastarria) y **711** sobrevivieron con imagen cruzada usable
    (`python embudo5.py`). El 1.824 de §0 no describe la muestra del veredicto.
- **Qué pasa**: §0 es el párrafo que justifica el cambio de instrumento ("hay muestra"). El argumento
  se sostiene igual con 711, pero el número publicado no se puede auditar.
- **Cómo reproducirlo**: `python base5.py && python s0_5.py && python embudo5.py`.
- **CONFIRMADO. Gravedad 2.**

### H9. Las cinco referencias no son cinco sitios, y en 21 pasadas son uno solo

- **Dónde**: v5 l. 142-147 (los 5 sitios de referencia) y l. 150 (`r_p` como fracción de los 5).
- **Evidencia** (`python misc5.py`): aglomerando las 5 posiciones a 0,75 km, los sitios **distintos**
  por pasada son {1 sitio: 21 pasadas, 2: 133, 3: 300, 4: 428, 5: 231}. O sea la mediana es 4 y en 21
  pasadas las cinco referencias caen en el mismo lugar. Nada en §5 prohíbe que dos referencias vengan
  de noches distintas pero del mismo sitio, ni que dos vengan de la misma noche (sólo se exige que la
  noche esté a más de 3 días de `n`).
- **Qué pasa**: `r_p` tiene menos independencia de la que sugiere "fracción de 5". Si el único sitio de
  referencia de una pasada está caliente, `r_p` salta a 1 y `d_p` a -1; en el otro extremo, 5 miradas
  al mismo punto no promedian nada. Eso ensancha la varianza de `d_p` sin que el n lo muestre.
- **Cómo se ve en el resultado**: intervalos más anchos de lo que el n sugiere, y volcanes con pocos
  sitios distintos (Copahue y Láscar, mediana 3) más ruidosos que el resto.
- **Cómo reproducirlo**: `python misc5.py`, bloque "geometria de los 5 sitios de referencia".
- **CONFIRMADO. Gravedad 2.**

### H10. La imagen cruzada puede ser una pasada diurna, porque "la misma noche" sólo se puede implementar como fecha UTC y el filtro de mediana no las corta

- **Dónde**: v5 l. 136-137 ("el TIF de otra pasada `q` de **la misma noche** y el mismo volcán"), sin
  definición de noche, sin filtro de día y de noche y sin tope de |t_q − t_p|; l. 100-103 (el filtro de
  usabilidad, que sí tiene "mediana del raster menor que 0,2").
- **Evidencia** (`python dia5.py`): en la muestra del veredicto la hora UTC del TIF cruzado elegido se
  reparte {04 h: 81, 05 h: 286, 06 h: 316, 07 h: 25, **19 h: 3**}. Los tres de las 19:36 UTC son
  pasadas de la tarde en Chile, y pasaron el filtro con mediana 0,146 a 0,173, debajo del corte de 0,2
  (Copahue 2026-05-11 dos veces y Llaima 2026-05-11, todas a 768 y 816 min de la pasada medida). El
  máximo de |t_q − t_p| es **816 min**.
- **Qué pasa**: A76 documenta que MIROVA publica artefactos solares diurnos en su producto por volcán
  (nube que refleja el sol en el MIR, TIR frío, NTI enorme). Medir "exceso" en un ráster diurno es
  medir reflexión solar. Son 3 de 711, así que el daño es chico, pero el pre-registro no lo prohíbe y
  la próxima corrida con otra ventana puede traer más.
- **Cómo se ve en el resultado**: un `e_p = 1` que es reflexión solar sobre nube.
- **Cómo reproducirlo**: `python dia5.py`.
- **Cómo arreglarlo**: definir la noche por hora UTC (todas nuestras pasadas caen entre las 04 y las
  07) o por elevación solar, y poner un tope a |t_q − t_p|, que además arregla H5.
- **CONFIRMADO. Gravedad 2.**

### H11. El declarado de §7 sobre el tramo posterior a #535 es falso con el instrumento nuevo: el intervalo mide 0,086 y la equivalencia sí es alcanzable

- **Dónde**: v5 l. 237-240 ("con el n de hoy, el tramo posterior a #535 tiene intervalos de ancho
  cercano a **0,12**, así que **no puede dar la salida de equivalencia**").
- **Evidencia** (`python ver5.py`, último bloque, sobre el nulo con la estructura real de noches del
  tramo): el tramo posterior tiene **85 noches** (no 70) y el ancho medio del intervalo es **0,086**,
  con lo que la salida "no se distingue" aparece en **23 de 80** repeticiones del nulo. El tramo
  anterior tiene 293 noches y ancho 0,049.
- **Qué pasa**: el 0,12 es el número que la ronda 4 midió con el instrumento anterior y con otra
  muestra. Tercera vez en este documento que un número cambia de instrumento y el texto no (ver H7 y
  H12).
- **Cómo reproducirlo**: `python ver5.py`, bloque "tramo posterior a #535 aislado".
- **CONFIRMADO. Gravedad 2.**

### H12. El "128 pasadas, 58 de Cordón Caulle" del control H es el conteo sin el filtro de TIF usable que la propia definición exige

- **Dónde**: v5 l. 174-178 (control H: "pasadas con alerta, **TIF usable** y record con ... con esa
  definición hay **128 pasadas, 58 de Cordón Caulle**").
- **Evidencia** (`python h5.py`, restringido al bucket VIIRS375): sin el filtro de usabilidad da
  **130** por `primary_cluster` de 2 o más píxeles dentro del `inner`, y **128** exigiendo además
  `final_hotspot_source == "ctx_cluster"`, con Cordón Caulle 58, que es exactamente lo que dice el
  texto. **Con** el filtro de usabilidad puesto son **112** y **110**, con Cordón Caulle 50.
- **Qué pasa**: H es compuerta blanda (si falla, todo baja a SOSPECHA), así que su n importa para
  saber si la compuerta es informativa. El texto anuncia un n que su propia definición no produce.
- **Cómo reproducirlo**: `python h5.py`.
- **CONFIRMADO. Gravedad 2.**

### H13. "Mismo tipo de lugar, misma textura de flanco" no es exacto: la separación de 1,5 km empuja las referencias al otro lado del cono

- **Dónde**: v5 l. 40-42 ("Mismo tipo de lugar (misma textura de flanco, que es lo que refutó a la
  v3)").
- **Evidencia** (`python misc5.py`): respecto del cráter, la diferencia de acimut entre las
  referencias y `P` tiene **mediana 101 grados**, con p10 = 55 y p90 = 154, y la distancia mediana de
  una referencia a `P` es **3,96 km**. O sea el control típico está en otro sector del cono, con otra
  exposición y otro estado de nieve.
- **El matiz que salva al diseño**: empíricamente **no** se reproduce el fallo de la v3. Dentro de las
  mismas pasadas y los mismos rásteres, un punto sorteado del anillo excede el umbral 5,20 % de las
  veces y los sitios P 5,66 %: son poblaciones equivalentes, no una más fría. Lo que hay que corregir
  es la frase, no el instrumento.
- **Cómo reproducirlo**: `python misc5.py` y `python resid5.py`.
- **CONFIRMADO. Gravedad 2.**

### H14. Detalles que dejan dos implementaciones legítimas

- **Cuál de las 5 referencias es el "observado" de C1** (l. 159-161) no está dicho. Yo promedié los 5
  papeles posibles. Tomar sólo uno, o sortearlo, da otro número.
- **En el intercambio de C1 no se exige la separación de 1,5 km respecto del nuevo observado**, así
  que el propio rasgo puede volver al denominador, que es justo lo que §5 quiso evitar.
- **`zc_punto` se calibra en rásteres propios y se aplica en rásteres cruzados** (§4 contra §5). Como
  el mismo umbral se usa a los dos lados de la resta, `D` es robusto, pero el nivel de `e_p` no lo es,
  y el texto no lo declara.
- **"Dos o tres veces por noche" (l. 32)**: en los records, la mediana de pasadas VIIRS 375 por noche
  y volcán es **4** (distribución 2: 30, 3: 226, 4: 679, 5: 458, 6: 71, 7: 9, 8: 1). No cambia nada,
  pero conviene decirlo bien.
- **El estadístico binario pierde casi toda la potencia**: el **73,3 %** de los `d_p` es exactamente
  cero y la tasa de exceso vive entre 5 % y 10 %. Con la media de `z` o con un rango, la misma muestra
  daría intervalos bastante más angostos. Vale la pena decidirlo antes de medir y no después.
- **CONFIRMADO (lectura del texto y medición). Gravedad 1.**

---

## VERIFICADO LIMPIO

Lo que la v5 arregló, y lo que medí y quedó en pie:

- **La pasada cruzada hace lo que promete.** Sobre las mismas 165 pasadas, `D` cae de **+0,1091**
  [+0,0512, +0,1693] con la imagen propia a **+0,0145** [-0,0287, +0,0556] con la cruzada. Es una
  reducción del 87 %, y es el primer instrumento de las cinco rondas que ataca el mecanismo en vez de
  rodearlo.
- **El nulo del instrumento está en cero.** Con un punto sorteado del anillo de 1,5 a 3,0 km y la
  imagen cruzada, sobre 654 pasadas ajenas a la muestra: `D = -0,0046` [-0,0257, +0,0162].
- **El sitio no es persistentemente especial.** El brazo de otra noche (mismo `P`, los mismos cinco
  sitios, ráster a más de 3 días) da `D = +0,0005` [-0,0173, +0,0178] sobre 1.289 pasadas. Esto cierra
  de frente la pregunta que la ronda 4 dejó abierta y refuta la idea de que la selección opere sobre
  una propiedad permanente del terreno.
- **La población de referencia no está sesgada.** Punto sorteado 0,0520 contra sitios P 0,0566, en las
  mismas pasadas y los mismos rásteres. El defecto que hundió a la v3 (el control medía otra textura)
  no se reproduce.
- **La regla de separación de 1,5 km es gratis.** Ninguna de las 1.113 pasadas del veredicto se queda
  con menos de 3 sitios de referencia; de hecho **todas consiguen los 5**, y siguen consiguiéndolos
  con la separación subida a 3,0 km. Recién a 4,0 km empiezan a caer 27.
- **La muestra alcanza, con holgura, para el veredicto.** De 1.113 candidatas quedan **711** con imagen
  cruzada usable (se pierden 345 porque esa noche no hay otra pasada con TIF y 57 porque el TIF
  cruzado no es usable), repartidas en **378 noches de volcán** contra el mínimo de 30 que pide §7.
  Llegan a 20 noches **6 volcanes** (Copahue 75, Llaima 70, Villarrica 59, Chaitén 55, NdC 41,
  Planchón-Peteroa 28), contra el mínimo de 3 que pide §7; quedan fuera Tupungatito 18, Cordón Caulle
  18, Isluga 7 y Láscar 7. Los tramos son 536 pasadas y 293 noches antes de #535, y 175 y 85 después.
- **Las tres salidas son alcanzables y el nulo no produce falsos positivos.** Simulando la regla de §7
  sobre el nulo con la estructura real de noches (200 repeticiones): "no se distingue" 197,
  INCONCLUSO 3, "cae sobre un exceso" **0**. Ancho medio del intervalo 0,042.
- **Mapa de potencia** (señal uniforme inyectada sobre el nulo, 120 repeticiones por punto):
  `D = +0,02` da "no se distingue" el 70 % de las veces, `+0,025` el 50 %, `+0,05` da INCONCLUSO el
  99 %, `+0,08` da el positivo el 47 %, `+0,10` el 87 % y `+0,15` el 100 %. O sea el positivo pide
  `D` del orden de **+0,10**, y el rango donde cae el efecto plausible (+0,02 a +0,03) está repartido
  entre "no se distingue" e INCONCLUSO. Conviene escribirlo en §8 para que nadie lea el INCONCLUSO
  como hallazgo, y para que nadie lea el "no se distingue" como ausencia de correlato.
- **La señal concentrada sigue bloqueada** (límite heredado de la ronda 4, no defecto): con señal sólo
  en Villarrica y Chaitén, aun con tasa 0,60 el veredicto sale positivo en 70 de 100 repeticiones y
  nunca "no se distingue". Si la categoría b vive en dos o tres volcanes, como A83 y A54 hacen
  esperar, la regla la manda a INCONCLUSO un tercio de las veces.
- **La geometría de §1 reproduce exacto**: radio mediano de `P` **2,788 km**, máximo **3,000 km**, el
  **97,12 %** tiene otro `P` nuestro a 0,75 km o menos en otra noche, con mediana de **12** noches.
- **El pool de M1 de la ronda 3 reproduce**: 39 pasadas, Lastarria 15 con 12 compatibles, 24 fuera con
  4 compatibles (Láscar 1 y Cordón Caulle 3), `F` alcanzable en 4 de las 16. Y las separaciones de
  `mirova_center` contra el cráter que cita §2: Lastarria 0,12, Láscar 0,83, Planchón-Peteroa 2,02,
  Tupungatito 4,86, Cordón Caulle 7,57 km.
- **El control congelado son 19 archivos** (`git ls-files experiments/_s144_keep_peak_direccion/control_s143 | wc -l` da 19), como dice §4, y el rango
  `pipeline/geo_utils.py:53-78` es correcto (la función `get_detection_anchor` termina en el `return`
  de la línea 78). Los dos detalles que la ronda 4 pidió quedaron arreglados.
- **El control G valida casi sólo Láscar**, como dice §5, aunque el "42 de 43" no reproduce: con filas
  CONS de VRP mayor o igual a 0,3 MW desde el 2026-05-09 y TIF usable, cuento **49 pasadas de Láscar y
  3 de Villarrica**, o sea 52 con el 94 % de Láscar. El espíritu del alcance declarado se sostiene.
- **Ninguna evaluación de `Z` falló** por caer el punto fuera del ráster o sin `ΔL0`, en ninguna de las
  corridas (884 más 654 más 1.289 pasadas, con 5 referencias cada una).

**No verificado** (queda abierto y lo marco como SOSPECHA): los `Z(P)` de la muestra del veredicto y
las clases de M1, que no calculé a propósito; **si el control G pasa sus criterios** (sólo conté su
pool, no corrí la semilla del disco ni medí el desplazamiento por eje); la sensibilidad de
`Distancia_km` con OCR; si la regla de desempate de la imagen cruzada ("empate, la anterior") cambia
algo, porque no encontré ningún empate exacto; y si el residuo de +0,025 cambia cuando se excluyen las
tres pasadas diurnas de H10, que no volví a correr.

---

## Correcciones para una v6, por gravedad

1. **(4) Decidir contra qué se compara `D` (H1).** El instrumento deja un residuo medido de
   **+0,0251** [+0,0049, +0,0472] en el estrato hermano, que es un transitorio de menos de una hora,
   no un foco. Las opciones, y hay que elegir una por escrito antes de medir: (a) correr las bandas,
   o sea el positivo exige superar el residuo y la equivalencia se evalúa alrededor de él; (b) hacer
   el estadístico sobre la **diferencia entre estratos** (`neg_limpio` contra `sin_info`), donde el
   residuo se cancela; o (c) dejar la regla como está pero escribir en §8 que la salida "no se
   distingue" **no autoriza a apagar `keep_peak`**, porque a ese nivel de residuo la equivalencia es
   compatible con un correlato real.
2. **(4) C2 deja de ser compuerta (H2).** El control de instrumento es el **punto sorteado con imagen
   cruzada** (mide -0,0046). Las `far_ref` y `sin_info` son un **estrato de comparación**, no un nulo:
   como comparten patrón y publicación con las del veredicto, un C2 en rojo significaría que la
   hipótesis es cierta, no que el instrumento falla.
3. **(4) Arreglar la banda de C1 (H3).** El intercambio de roles atenúa el sesgo exactamente cinco
   veces (`C1 = −sesgo/5`, comprobado: sesgo +0,1031 da C1 = -0,0206). O la banda baja a ± 0,01, o el
   criterio se escribe sobre `5 × |C1|`, o se saca C1 y queda el nulo del punto sorteado. Tal como
   está, C1 habría certificado como limpio al instrumento que la ronda 4 refutó.
4. **(3) Decir cuáles son "esas mismas pasadas" y si el corte es el punto o el intervalo (H4)**: el
   estrato tiene 1.289 pasadas, 194 con TIF propio usable, 884 con cruzada usable y 165 con las dos, y
   el resultado de C2 cambia entre lecturas (sobre las 165 el intervalo llega a +0,0556 y el corte
   falla).
5. **(3) Fijar un tope a |t_q − t_p| y estratificar por brecha (H5)**, porque el residuo vale +0,047
   debajo de 45 min y -0,010 entre 45 y 60, y la muestra del veredicto se concentra en 42 a 54 min.
6. **(3) Corregir §3 y §6 sobre M1 (H6)**: con el filtro de región que la propia §6 define, la pasada
   de Láscar sale (su `F` está a 4,44 km del cráter y a 3,72 km de `mirova_center`, con el disco en
   1,84 km), así que M1 son **12 pasadas de Lastarria** y la clase `F` es inalcanzable en todo M1. De
   paso, ese caso es `P` en el cráter y `F` lejos, que no es el objeto de D19.
7. **(2) Recalcular la tabla de `zc_punto` con la regla literal de §4 (H7)**: Chaitén 4,22 [3,19,
   4,66], Cordón Caulle 4,25, Planchón-Peteroa 3,23, NdC 2,47, Isluga 6,07 [2,04, 7,69] sobre 13
   pasadas. Los valores del texto son del anillo viejo de 1,5 a 3,5 km.
8. **(2) Reemplazar los conteos de §0 (H8)** por los que se pueden auditar: la muestra del veredicto
   es de **1.113** pasadas y quedan **711** con imagen cruzada usable, en 378 noches de volcán y 6
   volcanes con 20 noches o más.
9. **(2) Declarar que las 5 referencias pueden repetir sitio (H9)** (mediana 4 sitios distintos, 21
   pasadas con uno solo) y decidir si se exige diversidad espacial entre ellas.
10. **(2) Definir la noche y filtrar las pasadas diurnas (H10)**: hoy entran 3 rásteres de las 19:36
    UTC con mediana bajo el corte de 0,2, que es el artefacto solar de A76.
11. **(2) Corregir el declarado del tramo posterior a #535 (H11)**: el ancho es 0,086 y la equivalencia
    sí es alcanzable (23 de 80 corridas del nulo), no 0,12 e inalcanzable.
12. **(2) Corregir el n del control H (H12)**: con TIF usable son **110**, con Cordón Caulle 50; el 128
    con 58 es el conteo sin ese filtro.
13. **(2) Corregir la frase "misma textura de flanco" (H13)**: las referencias están a 101 grados de
    acimut en mediana. Lo que sostiene el control no es que sean el mismo flanco sino que son la misma
    población (5,20 % contra 5,66 % de tasa de exceso), y eso conviene escribirlo así.
14. **(1) Cerrar los detalles de H14**: cuál referencia hace de observado en C1 y si ahí rige la
    separación de 1,5 km, que `zc_punto` se calibra en rásteres propios y se aplica en cruzados, que la
    mediana de pasadas por noche es 4 y no "dos o tres", y si conviene pasar de un indicador binario a
    un estadístico continuo (hoy el 73,3 % de los `d_p` es exactamente cero).

**Resumen**: la v5 es la primera versión cuyo **instrumento** está bien. La pasada cruzada corta el
87 % de la maldición del ganador, el nulo está en cero, la población de referencia no está sesgada, la
muestra alcanza (711 pasadas, 378 noches, 6 volcanes elegibles) y las tres salidas son alcanzables sin
falsos positivos. Lo que queda mal son los **controles y la regla**: C1 atenúa el sesgo cinco veces y
habría dejado pasar el instrumento anterior, C2 mide la hipótesis en vez del instrumento, y el umbral
de ± 0,05 se aplica contra cero cuando el instrumento deja un residuo medido de +0,025 que es un
transitorio de menos de una hora. Con las correcciones 1, 2 y 3 escritas antes de medir, y con los
números de §0 y §4 puestos al día, **M2 queda en pie y puede decidir**. Sin ellas, la salida más
probable es un "no se distingue" que la tabla de §8 manda a apagar `keep_peak` sobre una equivalencia
que el propio instrumento ya contradijo.
