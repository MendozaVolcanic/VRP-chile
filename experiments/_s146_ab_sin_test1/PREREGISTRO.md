# Pre-registro del A/B "sin el Test 1 integrado en el ROI" (S146, Fase 2 del plan de paridad)

> **Estado: escrito ANTES de correr ningún brazo.** Los umbrales viven congelados en
> [`parametros.json`](parametros.json) y los aplica [`evaluar.py`](evaluar.py). Este documento y
> ese JSON se commitean antes del primer despacho: un sello sin historia de git no prueba el
> orden (hallazgo V-16 de la auditoría S146), y en este proyecto ya pasó más de una vez que el
> criterio se escribiera después de ver el resultado (H-A04, H-A07).
>
> **Falta para poder correr**: (a) que leas este documento y apruebes o corrijas los umbrales de
> la sección 6; (b) las tres decisiones de la sección 12; (c) que un verificador con contexto
> limpio lo revise. El workflow tiene un candado: no arranca sin el `si` explícito en
> `preregistro_aprobado`.
>
> **Ningún número de este documento está escrito a mano sin fuente.** Los de la Fase 1 salen de
> `docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` y su JSON; los del poder de las varas de
> recall, de `poder_recall.json`, medido en esta sesión sobre los records de producción; los del
> valor de reposo del Test 1, de una cuenta que se puede rehacer en tres líneas y que está abajo.

---

## Adenda S147: lo que cambió después del verificador con contexto limpio, ANTES de despachar

> Un verificador que no participó de S146 recibió sólo la ruta de este documento y lo auditó con el
> preámbulo anti-fabricación entero, re-corriendo los tres bancos. Entregó **18 hallazgos**, y dos
> de ellos daban vuelta el veredicto del experimento por sí solos. Informe completo:
> [`docs/audit_s147/VERIFICADOR_PREREGISTRO_AB.md`](../../docs/audit_s147/VERIFICADOR_PREREGISTRO_AB.md).
> Todo lo de abajo se aplicó **antes de correr ningún brazo** y está commiteado antes del despacho.

| # | qué estaba mal | qué se hizo |
|---|---|---|
| **H1** | El piso de recall de VIIRS 750 estaba escrito como tasa `0.667`, y el evaluador redondea `12/18` a `0.6667`: **`0.6667 >= 0.667` es falso**, o sea que el umbral rechazaba justo el valor que este documento decía aceptar, y el brazo salía NO ADOPTAR por la tercera cifra decimal | Los pisos de C1 pasan a **conteo**: `min_pasadas_positivas_publicadas` = 118 en VIIRS 375 y 12 en VIIRS 750. Sin redondeo no hay trampa posible y la derivación se comprueba a mano |
| **H2** | La holgura de VIIRS 750 se derivaba restando "la pérdida segura de Cordón Caulle", que **no está entre las 13 que el control publica** (esa pasada hoy tiene publicación 0), así que el piso efectivo toleraba **cero** pérdidas | La holgura se redefine sobre lo que el control **sí** publica: 13 menos 1 de holgura por reproceso NRT contra estándar |
| **H3** | Nada detectaba un **control** con pasadas de menos. C0 sólo falla si le faltan al brazo, y el control positivo comparaba sólo la intersección, así que un control al que le faltara el 30 % daba fracción idéntica 1,0 | `contar_pasadas.py` ahora falla también con `sobran`, y el control positivo exige cubrir al menos el 97 % de las pasadas de producción (`min_fraccion_cobertura_control`) |
| **H6** | Ni la ventana ni la referencia estaban fijadas: lo fijo eran **las fechas, no el contenido**. Entre dos corridas del mismo banco con horas de diferencia el corpus pasó de 2.360 a 2.386 records y una vara cambió de clasificación por el borde de su corte | Los tres insumos que no son los brazos quedan **congelados** en `_congelado/` por `congelar_produccion.py`, con el sha de git de cada uno. El evaluador compara contra eso, no contra el corpus vivo |
| **H5** | El techo de C3 del brazo C exigía apagar 3 de 3 pasadas en VIIRS 750, o sea **margen cero**, con C3 conjuntivo: NO ADOPTAR era casi seguro por construcción | El brazo C pasa a un **piso de pasadas apagadas** en su subclase (8 de 21 en VIIRS 375, 1 de 3 en VIIRS 750), que es lo que ese brazo puede mover |
| **H4** | C4 comparaba la mediana del control sobre lo que publica el control contra la del brazo sobre lo que publica el brazo, **sin parear**: un brazo que deja de publicar el 20 % más chico movía la mediana 0,23, más del doble del umbral, sin degradar nada | C4 pasa a `razon_magnitud_pareada`, sobre las pasadas que los **dos** publican. La versión sin parear se sigue informando y no decide |
| **H8** | El control de identidad del predicado se guardaba y **nunca se comparaba**: no podía fallar | Se pinea el esperado; si `frontend/index.html` cambió su predicado entre el pre-registro y la evaluación, el veredicto es INDECIDIBLE |
| **H11** | La posición del cúmulo y el nulo por etiquetas barajadas se calculaban y **no decidían nada**: un brazo que mueve el cúmulo varios kilómetros salía ADOPTAR igual | Entran como **C7** (posición estable, tope 0 cúmulos movidos más de 500 m) y **C8** (contraste fuera del nulo barajado). C8 no decide en el brazo C, donde no tiene poder |
| **H10** | El mecanismo es **bidireccional** y el documento sólo medía la baja: apagar el Test 1 también apaga su recómputo de magnitud, que cuando da 0 **tapa** la publicación. En el control hay 38 pasadas de VIIRS 750 y 3 de MODIS con el Test 1 disparando y publicación 0, y 3 de las de VIIRS 750 son positivas | Se agrega `ganancias_publicacion` al informe: las pasadas que el brazo publica y el control no, por sensor y etiqueta. Informa, no decide, pero sin eso C6 diría "la atribución queda refutada" cuando lo que pasó es un segundo mecanismo conocido |
| **H9** | El nulo de `poder_recall.py` baraja **por record**, lo que destruye la correlación intra-noche, que es real. Rebarajando por bloques de noche, el azar **alcanza y supera** el observado de VIIRS 750 | **La conclusión principal no cambia** (las dos varas de noche siguen sin discriminar y VIIRS 375 aguanta sin moverse), pero la vara de pasada de **VIIRS 750 se rotula DÉBIL, no fuerte**, y su resultado se lee con esa salvedad |
| **H12** | El piso de VIIRS 375 tolera perder hasta **25** pasadas con alerta mientras la Fase 1 predice perder 2, y la red de 0,5 MW cubre poco (126 de 143 están bajo ese valor) | Queda escrito con el número en `parametros.json`. El titular tiene que decir las pérdidas observadas **contra las 2 predichas**: "cumple C1" no significa "no perdimos recall" |
| **H14** | El estrato `sin_info` es el **31,7 % del corpus** (757 records, 417 publicados) y no lo juzga ningún criterio | Se informa por sensor en el resultado. No decide: la referencia no dice nada de esas pasadas, así que no hay contra qué medirlas |
| H13, H16, H17, H18 | Listas de noches inconsistentes entre sí, la fórmula del valor de reposo escrita de dos formas, la reparación de cobertura sin regla de parada, y dos parámetros que no pueden actuar | Corregidos abajo y en `parametros.json` |

**Lo que el verificador declaró sano y no hay que volver a mirar**: los tres perfiles difieren
exactamente en su único flag declarado (143 atributos, resueltos como los resuelve el código, no
leyendo el YAML); la tabla de poder se reproduce exacta en sus seis filas; la elección de la
**pasada** como vara decisoria está justificada, incluso adelgazando las publicaciones al régimen
esperado del brazo; C1 y C3 juntos no los puede pasar un brazo que apague al azar (0,0 % y 0,1 %
sobre 2.000 sorteos); los records se escriben también cuando no hay nada que detectar, así que la
cobertura la fija la disponibilidad de gránulos; las etiquetas no dependen de nuestras
detecciones, o sea que no hay circularidad; y el evaluador no es un sello de goma.

**Regla de parada que faltaba (H17)**: un volcán con cobertura despareja se repite **a lo sumo dos
veces** con el mismo código. Si a la tercera sigue despareja, ese volcán **sale del análisis con su
nombre en el informe**, en vez de repetirse hasta que el instrumento dé el resultado que lo deja
pasar.

---

## 1. El fenómeno, primero

De noche, sobre una cumbre volcánica, el satélite mide dos cosas en cada píxel: cuánto brilla en
el infrarrojo medio (MIR, alrededor de 3,7 a 4 micrones, que responde muchísimo a un punto muy
caliente aunque ocupe una fracción diminuta del píxel) y cuánto brilla en el térmico (TIR, cerca
de 11 micrones, que responde a la temperatura promedio de todo el terreno del píxel). Con eso hay
**dos maneras físicamente distintas** de afirmar que el cráter está caliente.

**La primera es la del paper de MIROVA** (Coppola et al. 2016a, SP426.5): preguntarle a **un
píxel** si se despega de sus ocho vecinos en el índice que cruza MIR con TIR. Esa es la firma de
un foco puntual. Una colada, un lago de lava o una fumarola de alta temperatura que ocupe el 1 %
del píxel sube muchísimo el MIR y casi nada el TIR, y ese píxel queda fuera del grupo de los de
al lado. Es una pregunta **local y diferencial**: no le importa cuán tibio esté el cerro, le
importa el contraste con el vecindario inmediato.

**La segunda es nuestra, y no está en el paper**: el Test 1 integrado en el ROI. No le pregunta a
ningún píxel. Toma todo el disco de 3 km de radio alrededor del cráter, suma el exceso de
radiancia MIR de cada píxel respecto de la mediana de un anillo de fondo, y dispara si esa suma
supera tres veces la dispersión esperada. Es una pregunta **global y absoluta**: dice "la cumbre,
en conjunto, está un poco más tibia que su entorno". Un lago de lava sub píxel produce eso, y por
eso se adoptó en S27. Pero también lo produce una cumbre de roca oscura sin nieve rodeada de
glaciar, y sobre todo lo produce el gradiente de altitud entre el cono frío y el valle tibio de
más abajo, que es el artefacto topográfico que la regla A69 describe: en un nevado el cráter
puede estar a 272 K y el valle a 281 K sin que pase nada volcánico, y un método de MIR absoluto
lee eso como calor.

**Y hay un detalle aritmético que lo empeora, y que hasta la auditoría S146 nadie había mirado.**
La suma del Test 1 recorta a cero los excesos negativos: sólo suma `max(0, L - L_bg)`
(comprobado en esta sesión leyendo `pipeline/test1_integrated.py:420-437`). Tirar la mitad
negativa del ruido significa que el ruido puro **no suma cero**. La media de la mitad positiva de
un ruido normal es `sigma / raíz(2 pi) = 0,3989 sigma`, así que sobre una cumbre donde no pasa
absolutamente nada el estadístico tiene un valor de reposo de `0,3989 · raíz(N_ROI)`, que **crece
con el número de píxeles del disco**. Y el número de píxeles del disco depende sólo del tamaño
del píxel del sensor:

| sensor | área del píxel | píxeles en el disco de 3 km | valor de reposo con ruido puro | umbral del código |
|---|---|---|---|---|
| VIIRS 375 m | 0,1406 km² | 201 | **5,66** | 3,0 |
| VIIRS 750 m | 0,5625 km² | 50 | **2,83** | 3,0 |
| MODIS 1 km | 1,0 km² | 28 | **2,12** | 3,0 |

A 375 m el detector tiene la aguja clavada: su valor de reposo casi **duplica** el umbral al que
debería dispararse, sin ninguna fuente de calor. A 750 m queda justo debajo, y a 1 km bien
debajo. Eso es un hallazgo de dos auditores independientes que llegaron a lo mismo por caminos
distintos (F-01 en `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md` y G-27 en
`FRENTE_G_INVENTARIO_DE_CAMINOS.md`, el segundo todavía sin verificador: **lo compruebo yo en el
código y lo cito como hallazgo de auditor**, no como hecho verificado). F-01 midió además el
valor observado real: **4,87 de mediana sobre 44.105 records**, y el Test 1 disparando en el
89,7 % de las pasadas de 375 m. Lo único que lo frena es el segundo criterio, el piso relativo
del 2 % de `L_bg`.

**Esa cuenta hace una predicción que se puede escribir antes de correr**, y por eso es un control
y no una anécdota: si el mecanismo es el que creemos, apagar el Test 1 tiene que bajar mucho la
publicación en VIIRS 375, algo en VIIRS 750 y casi nada en MODIS, **en ese orden**. Es el
criterio C6 de la sección 6.

---

## 2. Lo que ya está medido, y por qué hace falta igual una re-ejecución

La Fase 1 del plan (`docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md`), con su verificador de
contexto limpio (`FASE1_VERIFICADOR.md`), midió sobre los records ya guardados, en la ventana del
1 al 20 de septiembre de 2026:

| | VIIRS 375 | VIIRS 750 | MODIS |
|---|---|---|---|
| publicamos en negativos limpios | 322 de 373 = **86,3 %** | 133 de 622 = **21,4 %** | 50 de 439 = **11,4 %** |
| de eso, lo sostiene sólo el Test 1 | **186 (57,8 %)** | **89 (66,9 %)** | 8 (16,0 %) |
| tasa inferida sin el Test 1 | **21,4 % a 36,5 %** | **5,3 % a 7,1 %** | 8,9 % a 9,6 % |
| pasadas positivas que sostiene sólo el Test 1 | 2 de 143 | 0 de 13 | 0 de 1 |

El patrón no es de dos volcanes: el verificador estratificó por su cuenta y encontró T1\_SOLO en
**los once** Tier A en VIIRS 375 (de 1 a 39 pasadas) y en los once en VIIRS 750. En MODIS pasa lo
contrario y manda el camino del paper, concentrado en Cordón Caulle.

**Pero esa atribución es una inferencia sobre lo persistido, no una simulación**, y el
verificador fue explícito en qué no puede cerrar: **el VRP y el centroide del cúmulo contextual
que el Test 1 pisa no se guardan en ningún campo**. Cuando la fuente pasa a ser el Test 1, el
pipeline sobrescribe `primary_cluster`, `anomaly_pixels` y `vrp_mir_mw`, y el cúmulo rival se usa
y se descarta. Eso es exactamente lo que separa el 21,4 % del 36,5 %: las 56 pasadas de VIIRS 375
y 11 de VIIRS 750 de la clase T1\_SOBRE\_CTX, donde el Test 1 le ganó la fuente a un cúmulo
contextual que existía. Ningún número persistido puede reducir esa banda. Sólo una re-ejecución.

Lo que el A/B tiene que medir y lo persistido no puede, en el orden en que lo pidió el
verificador:

1. el VRP y el centroide del cúmulo contextual en las 56 más 11 pasadas T1\_SOBRE\_CTX;
2. las 4 noches SIN DATO pasada por pasada, más Cordón Caulle del 7 de septiembre en VIIRS 750,
   con el criterio de recall escrito de antemano **en la unidad que tenga poder**;
3. que apagar el Test 1 no mueva nada aguas arriba (hoy es un argumento de flags, no una
   medición): lo cierra el control positivo del brazo de control;
4. los 3 `cluster_rescue` y los 8 T1\_SOLO de MODIS, donde la cascada legacy hace que la
   inferencia sea cota y no hecho;
5. el nulo del brazo: una pasada sin nada no puede ganar publicación al apagar un detector.

**Y hay una razón de fondo para medir esto ahora**: el Test 1 integrado se adoptó en S27 porque
"subió el recall de 50 a 80 %", y ese número no sirve (H-A01). El acierto se contaba como
"`pc.vrp_mw > 0` **o** `triggered_test1`", o sea que el disparo del propio Test 1 contaba como
detección, que es circular; los falsos positivos se contaron sólo como detecciones `far`, nunca
como pasadas donde MIROVA calló; y la detección contextual contra la que se comparó ya no existe
(la reemplazaron los Tests 2 y 3 del paper en S46). Hoy se teme apagarlo por un número de otro
sistema.

---

## 3. Los brazos

Tres, todos con perfil aislado y su propio `data_subdir`, ninguno tocando `data/mirova_equivalent`.

| brazo | perfil | qué cambia respecto de producción |
|---|---|---|
| **A, control** | `_s146_ab_control` | nada. Producción de hoy, reprocesada con el mismo código que los demás |
| **B, sin el Test 1 integrado** | `_s146_ab_sin_test1` | `enable_test1_path: false` |
| **C, sin la prioridad por rival débil** | `_s146_ab_sin_prioridad_debil` | `enable_test1_priority_weak_cluster: false` |

**Qué apaga exactamente el brazo B, leído en el código y no en los nombres de los campos.** Con
`ENABLE_TEST1_PATH` en falso, los tres procesadores dejan `test1_triggered` en falso y
`test1_hot` en ceros (`process_viirs.py:1099`, `process_modis.py:737`,
`process_viirs_mod.py:731`). Con eso desaparecen cinco cosas y sólo cinco: el disparo persistido,
los píxeles del Test 1, la prioridad de fuente que le entrega el cúmulo publicado, el recómputo
de magnitud que está gateado por `source == 'test1'`, y la excepción del dashboard que muestra un
record descartado cuando `triggered_test1` es verdadero. **No toca la máscara contextual**: con
`ENABLE_FIRST_PASS_TESTS_2_AND_3` encendido, `hot_mask_2d` se sobrescribe con la salida del
primer pase (`process_viirs.py:1299`) y el Test 1 nunca estuvo ahí; y **no toca el fondo**,
porque el `test1_mask` que recibe el primer pase es `nti_path_hot` (el camino por píxel, otro
objeto) y sólo cuando `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` está encendido, que no lo está.

El volcado completo de los 143 atributos de `pipeline.profile` de cada brazo contra producción
está en [`diff_perfiles_salida.txt`](diff_perfiles_salida.txt) y en `diff_perfiles.json`: el
control difiere en **cero** atributos, el brazo B sólo en `ENABLE_TEST1_PATH` y el brazo C sólo en
`ENABLE_TEST1_PRIORITY_WEAK_CLUSTER`, y cada uno escribe en su propio directorio.

### Por qué hay un tercer brazo, y qué NO aísla

El hallazgo G-19 de la auditoría dice que los contadores "diagnósticos" deciden la fuente
publicada: la regla `only_test1_source` exige que los contadores legacy estén en cero **aunque la
máscara contextual real tenga píxeles**, y como esos caminos legacy están apagados, la condición
es casi siempre verdadera. Medido por el auditor: 132 pasadas de VIIRS 375 y 16 de VIIRS 750 donde
el Test 1 gana por "fuente única" sin serlo (hallazgo sin verificador todavía).

Leyendo `test1_integrated.py:156-182` y `process_viirs.py:1735-1767`, el Test 1 gana la fuente por
tres ramas: (1) el píxel suelto más caliente quedó lejos y el Test 1 vio algo cerca, (2) "fuente
única", que es G-19, y (3) el cúmulo rival tiene menos de 0,01 MW. **Sólo la tercera tiene flag.**
Aislar G-19 pediría código nuevo en `pipeline/`, que está protegido por A45 y queda fuera de esta
tarea.

Así que el brazo C **no aísla G-19**, y lo digo acá para que nadie lea después que sí. Lo que
aísla es la otra mitad de la misma interacción, y **se justifica por sí solo**: esa rama se adoptó
en S111 y S112 contra su propio pre-registro, con un A/B que vio la sobre publicación en pasadas
RUTINA pasar de 24 a 54, y se adoptó igual el mismo día por evidencia externa
(`docs/S112_TEST1_LOWMAG_AB_RESULTS.md:37-48`, resumido en H-A07). Sigue encendida. Es la única
adopción del proyecto cuyo propio A/B vio duplicarse la sobre publicación.

El brazo C es chico por construcción: la Fase 1 lo dimensiona en 21 pasadas de las 322 publicadas
en negativos limpios de VIIRS 375 y 3 de las 133 de VIIRS 750 (subclase `rival_debil`). Por eso
tiene **umbrales propios**, pre-registrados en `parametros.json`, y por eso un ADOPTAR en el brazo
C significa otra cosa que en el brazo B: significa recomendar el flip de un flag mucho menor, con
su propio ciclo A45.

### El brazo que NO se construye ahora, y que sería el siguiente

Si el brazo B gana pero se lleva recall que no queremos perder, el paso siguiente **no es volver
atrás**: es **descontarle el nulo al Test 1**. La cuenta de la sección 1 dice que el estadístico
tiene un piso de `0,3989 · sigma · N_ROI` bajo ruido puro (⚠️ **ojo con la escala, H16 del
verificador S147**: ese piso es el de la **suma cruda**, y el `0,3989 · raíz(N_ROI)` de la sección
1 es el del estadístico ya **normalizado** por `sigma · raíz(N)`. Las dos son correctas para
objetos distintos, y restar una donde va la otra se equivoca por un factor raíz(N), entre 5 y 14
según el sensor. La receta completa, con su nulo medido y su control positivo, quedó escrita en
[`docs/S147_TEST1_ESTADISTICO_CORREGIDO.md`](../../docs/S147_TEST1_ESTADISTICO_CORREGIDO.md) y su
banco es `tests/test_test1_estadistico_nulo_s147.py`); restarlo, o directamente no recortar a
cero los excesos negativos, deja un detector que sigue viendo el calor real integrado pero ya no
dispara solo. Eso necesita **código nuevo detrás de un flag en `pipeline/`**, que está protegido,
así que acá queda **descrito y no construido**. Es el brazo natural de una fase posterior.

---

## 4. Universo, ventana y potencia

**Once volcanes Tier A** (Láscar, Lastarria, Isluga, Tupungatito, Planchón-Peteroa, Nevados de
Chillán, Llaima, Villarrica, Copahue, Puyehue-Cordón Caulle, Chaitén) y **los tres sensores**
(MODIS, VIIRS 375 m, VIIRS 750 m).

**Ventana: del 1 al 20 de septiembre de 2026, fija.** Tres razones, y la tercera es la que más
importa:

1. es régimen actual: toda ella posterior al 2026-08-28 23:00 UTC, el cambio de régimen de #535
   que la regla A104 obliga a no cruzar;
2. es **exactamente** la ventana que midió la Fase 1, así que el brazo de control se puede
   comparar pasada por pasada contra los records de producción y eso da un control positivo real,
   no una banda floja;
3. **no se mueve aunque el A/B se despache más tarde.** Un denominador que crece solo ya produjo
   tres falsos hallazgos en este proyecto (A90), y el corpus de este repo crece todos los días
   porque el cron NRT sigue escribiendo.

**Cuántos días hacen falta, y en qué me baso.** La pregunta de potencia no es la de la
sobre publicación sino la del recall, porque la primera está sobrada y la segunda no:

- **Sobre publicación**: con 373 negativos limpios en VIIRS 375 y una diferencia esperada de más
  de 40 puntos porcentuales, sobra. El error estándar de una proporción alrededor de 0,35 con
  n = 373 es de 2,5 puntos, y además la comparación es pareada sobre las mismas pasadas. Incluso
  con 100 pasadas alcanzaría. En VIIRS 750, n = 622 y diferencia esperada de 14 puntos: sobra
  también.
- **MODIS**: n = 439 y diferencia esperada de **2 puntos**. Eso **no** tiene potencia, y por eso
  MODIS queda declarado descriptivo antes de correr, no después.
- **Recall**: 78 noches de volcán con alerta, 90 noches de sensor, 162 pasadas positivas. Acá no
  hay estadística que valga: las noches en riesgo ya están identificadas una por una, y cada
  pérdida se lista con su magnitud.

Alargar la ventana hacia atrás hasta el 29 de agosto sumaría unos tres días (más o menos 15 % de
muestra) pero **rompería el control positivo**, porque la Fase 1 no midió ahí. No vale la pena.

### La vara de recall: cuál tiene poder y cuál no (medido antes de fijar el umbral)

Acá está el cambio más importante respecto de cómo se venía midiendo. El frente I de la auditoría
(I-01) sostiene que "78 de 78 noches" **no discrimina nada**, porque publicamos algo en casi todas
las noches de casi todos los volcanes. **Lo medí yo, sobre los records de producción de la misma
ventana**, barajando el vector "publica" dentro de cada volcán y sensor 200 veces
([`poder_recall.py`](poder_recall.py), salida en `poder_recall.json`):

| vara de recall | observado | nulo, mediana | nulo, mín a máx | el azar la alcanza | veredicto |
|---|---|---|---|---|---|
| noche de volcán, cualquier sensor | 78 de 78 | 78 | 77 a 78 | 98,5 % de las veces | **NO DISCRIMINA** |
| noche del sensor, VIIRS 375 | 75 de 75 | 75 | 74 a 75 | 98,5 % | **NO DISCRIMINA** |
| noche del sensor, VIIRS 750 | 13 de 14 | 11 | 7 a 14 | 13,5 % | débil |
| **pasada, VIIRS 375** | **143 de 143** | 132 | 124 a 137 | **0 %** | **DISCRIMINA** |
| **pasada, VIIRS 750** | **13 de 18** | 8 | 2 a 12 | **0 %** | **DISCRIMINA** |
| pasada, MODIS | 1 de 1 | 0 | 0 a 1 | 17 % | sin muestra |

La tasa base que hace esto posible: publicamos en el 87,3 % de las pasadas nocturnas de VIIRS 375,
el 21,8 % de VIIRS 750 y el 11,6 % de MODIS, y en **218 de 219** noches de volcán publicamos algo.
Con esa tasa, acertar las noches con alerta es casi una tautología.

**Un matiz propio, y a favor**: el auditor del frente I dijo que sólo VIIRS 750 por pasada
discrimina. Mi medición dice que **la pasada de VIIRS 375 también discrimina**, y con margen: 143
de 143 contra un nulo cuyo máximo en 200 barajados fue 137. La diferencia es que él barajó y miró
la noche; la pasada es más fina. Eso amplía la base del criterio en vez de angostarla.

**Consecuencia, escrita antes de correr**: la vara de recall que **decide** es la **pasada del
sensor en que MIROVA alertó**, para VIIRS 375 y VIIRS 750. Las dos varas de noche se informan
siempre, con su nulo al lado para que nadie lea "cero noches perdidas" como evidencia de nada,
y sirven sólo para lo contrario, que es barato y sí informa: una noche perdida **fuera** de la
lista que la Fase 1 predijo significa que hay un mecanismo que no entendemos.

---

## 5. Qué se mide, en las unidades del operador

"Publicamos" es **el predicado literal del dashboard ejecutado con node** desde
`frontend/index.html`, a través de `scripts/banco_paridad.correr_node`. No se porta a Python, no
se reconstruye a mano, y el sha del archivo viaja en la salida (A97). El evaluador reusa el
cargador y el etiquetado del banco de paridad y sólo agrega los campos que el banco no guarda
(posición del cúmulo, fuente del ancla, plataforma).

1. **Recall por pasada del sensor que alertó**, por sensor. La que decide.
2. **Recall por noche**, en las dos unidades (noche de volcán con cualquier sensor, y noche del
   sensor que alertó), con su nulo al lado. Informativas, salvo por la regla de "fuera de lo
   previsto".
3. **Publicación en negativos limpios por pasada**, por sensor y por volcán.
4. **Razón de magnitud contra MIROVA, estratificada por volcán y sensor.** La magnitud es la que
   ve el operador: la que devuelve `mirovaEqVrpDisplay`, que ya resuelve el núcleo F5 en VIIRS 375
   y `pc.vrp_mw` en los otros dos (A10 con su matiz de S132). No se recalcula.
5. **Posición del cúmulo publicado**: separación en kilómetros entre el punto del control y el del
   brazo en las pasadas que los dos publican, mediana y percentil 90, y la lista de los que se
   mueven más de 500 m. Se informa la separación **entre puntos**, no la diferencia de radios: una
   cota escalar no identifica el objeto (A93, A107).

Y tres estratos que **se informan y no deciden**, porque salieron del frente I y cambian cómo se
lee el 86,3 %, pero convertirlos en criterio sería inventar un piso:

6. **Por magnitud publicada** (bajo 0,02 MW, de 0,02 a 0,05, sobre 0,05). I-02: "publicamos"
   cuenta apariciones, no energía. La mitad de lo que publicamos en negativos limpios de VIIRS 375
   está bajo 0,041 MW, y MIROVA casi nunca alerta bajo 0,02 MW (un caso en 1.914). Con un piso de
   0,02 el 86,3 % ya bajaría a 74 % sin perder ninguna noche. Eso **no** es lo que este A/B
   propone: es contexto para no leer el 86,3 % como "energía de más".
7. **Por plataforma**. I-03: de SNPP MIROVA lista sólo el 41 % de las pasadas y **ninguna** de las
   04 UTC, así que el denominador está enriquecido en pasadas de buena geometría. Si el efecto del
   brazo fuera muy distinto entre plataformas, habría que mirarlo antes de generalizar.
8. **MODIS con y sin Cordón Caulle**. I-04: 31 de las 50 publicaciones de MODIS en negativos son
   de ese volcán, y sin él MODIS publica en 4,8 %. El agregado de MODIS no describe MODIS,
   describe un lacolito con radio interno de 20 km.

---

## 6. Los criterios, con sus umbrales y de dónde sale cada número

Los aplica `evaluar.py` con `parametros.json` congelado. Dos de ellos no son de mérito: si fallan,
el veredicto es INDECIDIBLE y no se interpreta nada.

### C0. Cobertura pareja (si falla: INDECIDIBLE)

Diferencia de claves `(volcán, sensor, fecha y hora)` entre cada brazo y el control. **Se cuenta
antes de mirar el veredicto**, en el propio workflow, y el job falla si un brazo tiene menos
pasadas que el control. Un run con todos los jobs en verde **no** prueba cobertura pareja: en S143
hubo 54 de 54 jobs verdes por tramo y 3 de 108 quedaron con pasadas de menos por cortes de NASA,
porque el cortacircuitos por host (A64) hace que el job termine bien igual (A108). Un volcán
desparejo se repite con el mismo código y se vuelve a contar.

### C1. Recall por pasada del sensor que alertó (DECIDE)

Dos condiciones, las dos obligatorias:

- **Ninguna pasada perdida que MIROVA publicó con 0,5 MW o más**, en ningún sensor. Una sola
  basta para NO ADOPTAR. El 0,5 sale de la prioridad declarada del perfil `mirova_equivalent`:
  se aceptan falsos negativos sub píxel bajo 0,5 MW, no sobre. Todas las pasadas perdidas se
  listan una por una con volcán, fecha, plataforma, sensor, la magnitud de MIROVA y la nuestra.
- **Piso de recall por pasada**: VIIRS 375 al menos **0,825**, VIIRS 750 al menos **0,667**. El
  primero es la cota pesimista de la Fase 1 (118 de 143 publicadas sin el Test 1). El segundo es
  13 de 18 menos la pérdida segura de Cordón Caulle, o sea 12 de 18. Si el brazo cae por debajo,
  la inferencia de la Fase 1 falló y no es cuestión de tolerancia.
- **MODIS queda fuera**: una sola pasada positiva en la ventana.

### C2. Ninguna noche perdida fuera de lo previsto (DECIDE, pero no certifica)

Las únicas noches que la Fase 1 predijo en riesgo son cuatro en la unidad de volcán (Isluga
19-sep, Lastarria 1-sep, Nevados de Chillán 18-sep, Villarrica 16-sep) y esas cuatro en VIIRS 375
más Isluga 5-sep y Cordón Caulle 7-sep en VIIRS 750. Una pérdida **fuera** de esa lista significa
que hay un mecanismo que no entendemos, y eso basta para NO ADOPTAR aunque la magnitud sea chica.

Esta vara **no puede certificar que el brazo sea bueno** (el azar la cumple, sección 4), y por eso
está redactada sólo en su dirección útil.

### C3. Baja la publicación en negativos limpios (DECIDE)

Techos absolutos: **VIIRS 375 por debajo de 0,45** y **VIIRS 750 por debajo de 0,12**. La Fase 1
acota la tasa sin Test 1 entre 21,4 % y 36,5 % y entre 5,3 % y 7,1 %. Los techos dejan margen a
que la inferencia se haya equivocado hacia el lado pesimista y aun así exigen una caída de más de
41 puntos y de más de 9 puntos, que sería el movimiento de paridad más grande medido en el
proyecto. **MODIS no entra** (sin potencia, y dominado por un volcán): se informa con y sin
Cordón Caulle.

Para el brazo C, que apaga una palanca mucho más chica, los techos son **0,82 y 0,21**: el máximo
posible según la Fase 1 es bajar de 0,863 a cerca de 0,807 y de 0,214 a cerca de 0,209. Pedirle
0,45 sería pedirle lo que no puede dar.

### C4. La magnitud no se aleja de 1 (DECIDE)

Mediana de la razón entre la magnitud del operador y el VRP de MIROVA, por volcán y sensor, sólo
en pasadas que **los dos** publican, con al menos 5 pares. El brazo no puede alejarse de 1 más de
**0,10** respecto del control en ningún estrato con muestra. Con 20 días los n por celda son
chicos, y por eso el mínimo es 5 y no 30: este criterio protege contra un empeoramiento grande, no
certifica una mejora.

### C5. El nulo estructural (si falla: INDECIDIBLE)

En las pasadas donde el control no tiene **ningún** píxel anómalo, ningún brazo puede publicar. De
la nada no sale una publicación. Si sale, el brazo o el evaluador están inventando. Esto es un
nulo **medido**, no argumentado (A110).

### C6. El orden por sensor que predice el mecanismo (no decide, pero sale en el titular)

La caída en puntos porcentuales tiene que ordenarse **VIIRS 375 igual o mayor que VIIRS 750 igual
o mayor que MODIS**, que es lo que predice la cuenta del valor de reposo de la sección 1. Si el
orden no se cumple, el beneficio de paridad puede ser real igual, pero **la atribución del
mecanismo queda refutada** y el verificador tiene que mirarlo antes de que nadie proponga nada.
Por eso el evaluador lo pega al veredicto y no a una nota al pie.

---

## 7. Los controles, y el nulo de cada uno

| control | qué comprueba | qué lo hace fallar |
|---|---|---|
| **Positivo del brazo de control** | que el control reprocesado reproduzca producción campo por campo (publicación, magnitud mostrada, clase de distancia, VRP y distancia del cúmulo, disparo del Test 1, fuente) en al menos el 98 % de las pasadas comunes, y que sus tres tasas caigan en la banda pre-registrada | cualquier cosa del reproceso o del evaluador. Si falla, **todo** el A/B es INDECIDIBLE |
| **Del cargador** | que el vector de publicación que produce `evaluar.py` sea idéntico al de `banco_paridad.cargar_nuestros` sobre el mismo directorio | una divergencia entre mi cargador y el del banco |
| **Identidad del predicado** | los 7 casos del guard de S139 ejecutados con node | que `index.html` haya cambiado su predicado |
| **Cobertura pareja** | C0, ya descrito | un corte de NASA |
| **Nulo estructural** | C5, ya descrito | un brazo que inventa publicaciones |
| **Nulo por etiquetas barajadas** | que el contraste entre la caída en negativos y la caída en positivos no sea lo que da el azar. Se baraja **dentro de cada volcán y sensor**, 1.000 veces, semilla 146, porque barajar en bloque mezcla volcanes con distinta tasa de positivos y eso es paradoja de Simpson (V-03) | un brazo que apaga publicaciones al azar daría las dos caídas iguales |
| **Nulo de cada vara de recall** | ya medido, sección 4, antes de fijar los umbrales | una vara que el azar cumple sola queda descartada como criterio |

La banda del control positivo es 0,80 a 0,92 en VIIRS 375, 0,16 a 0,27 en VIIRS 750 y 0,07 a 0,16
en MODIS. La Fase 1 midió 0,8633, 0,2138 y 0,1139 sobre producción; el control se **reprocesa**,
así que puede diferir por gránulos NRT contra estándar y por disponibilidad, y la holgura cubre
eso. Fuera de esas bandas, algo está mal y se arregla antes de interpretar nada.

**El evaluador está probado contra una salida sintética** con cuatro casos cuyo veredicto se sabe
de antemano: uno bueno que tiene que dar ADOPTAR, uno que pierde una noche de 3,0 MW y tiene que
dar NO ADOPTAR por recall, **uno idéntico al control** que tiene que dar NO ADOPTAR por
publicación (si diera ADOPTAR, el evaluador estaría roto), y uno que publica donde no hay píxeles
y tiene que dar INDECIDIBLE. La salida cruda está pegada en [`README.md`](README.md).

---

## 8. La regla de decisión

1. Si el **control positivo** falla, o la **cobertura** es despareja y no se puede reparar
   repitiendo el job, o el **nulo estructural** falla: **INDECIDIBLE**. No se interpreta nada, se
   arregla el instrumento y se vuelve a correr. Un resultado malo no es INDECIDIBLE; INDECIDIBLE
   es cuando el instrumento no midió.
2. Si el brazo cumple **C1, C2, C3 y C4**: **ADOPTAR**, con el aviso de C6 si el orden por sensor
   no se cumplió.
3. Si falla cualquiera de los cuatro: **NO ADOPTAR**, nombrando cuál falló.
4. **ADOPTAR no es el flip.** Ver la sección 9.
5. El veredicto se anota el mismo día en `docs/HYPOTHESIS_LOG.md` (y se corre la suite después de
   editarlo: hay tests que leen ese archivo, A39 enmendada en S142), y lo revisa un verificador
   con contexto limpio antes de proponer nada.

---

## 9. Lo que este A/B NO decide

- **No autoriza el flip.** Cambiar `enable_test1_path` en `pipeline/profiles/mirova_equivalent.yaml`
  es tocar el perfil operacional del NRT, que corre doce veces al día sobre once volcanes: exige
  el ciclo A45 completo, o sea tag defensivo, tu confirmación explícita, test que capture el
  cambio, reproceso en Actions por volcán y en serie, y verificación en el dashboard.
- **No decide si lo que perderíamos es real.** "MIROVA calló" no es "artefacto" (A54). Los
  T1\_SOLO de Villarrica y Copahue son, con toda probabilidad, en parte calor real (lago de lava,
  lago cratérico ácido) que MIROVA no publica. Este A/B mide **paridad**, no verdad física.
- **Si se pierde calor real que MIROVA no publica, la salida prevista es mudar el Test 1 al perfil
  `experimental`, no borrarlo.** Es la regla de S143 aplicada: primero igualar a MIROVA en
  `mirova_equivalent`, y lo que vemos de más va separado y con nombre propio, con
  `pc.classification` como lenguaje para el operador. Esa es la Fase 2b del plan y es decisión
  tuya, no técnica.
- **No mide la compuerta de 3 K (D22) ni la banda 22 (D21)**, que actúan dentro del camino
  contextual y necesitan su propio probe.
- **No mide el test de temperatura de brillo con N·σ 5 y 10.** Ya está apagado por flag y su
  contador es cero en las 2.360 pasadas de la ventana: sustrato cero, no se corre (Fase 1 §9).
- **No mide MODIS con potencia.** Se informa y no decide.
- **No construye el brazo del nulo descontado** (sección 3), que necesita código en `pipeline/`.

---

## 10. La contaminación, declarada

**Ya conozco los números de la Fase 1 antes de escribir este criterio.** Sé que el Test 1 sostiene
186 de 322 negativos publicados en VIIRS 375, sé que la cota pesimista es 36,5 % y sé cuáles son
las cuatro noches en riesgo. Los umbrales de la sección 6 están construidos **a partir de** esas
cotas, y eso no lo puedo deshacer: sería deshonesto presentar este pre-registro como ciego.

Lo que sí se puede hacer, y es lo que se hizo, es que cada umbral sea **derivable de la cota de la
Fase 1 por una regla explícita y escrita antes**: el techo de publicación es la cota pesimista más
un margen (0,365 más 0,085), el piso de recall **es** la cota pesimista (118 de 143), y la lista de
noches perdidas admisibles **es** la lista de la Fase 1, sin agregados. Si mañana alguien quiere
discutir un umbral, puede discutir la regla, no el número suelto.

Lo que **no** está contaminado, y por eso es el corazón del criterio: el poder de las varas de
recall lo medí en esta sesión, sobre producción, y **cambió la vara que decide** respecto de lo
que el plan proponía. Si me hubiera quedado con "cero noches perdidas", habría escrito un criterio
que casi cualquier brazo cumple.

---

## 11. Costo, riesgos y límites

- **33 jobs** (11 volcanes por 3 brazos), un volcán y un brazo por job, cada uno en su
  `data_subdir` (A47: dos procesos sobre el mismo directorio corrompen los JSON). `max-parallel`
  6, para dejarle lugar al cron NRT dentro del tope de 20 jobs concurrentes y no saturar a NASA.
- **Duración estimada: 1,5 a 3 horas por job**, y de 9 a 18 horas de reloj para la corrida
  completa. La base: S135 midió de 72 a 153 minutos por job de 45 días con un solo sensor, y el
  cron NRT procesa un día de los tres sensores para un volcán dentro de su timeout de 50 minutos,
  típicamente en bastante menos. Acá son 20 días por los tres sensores. `timeout-minutes` 330 para
  el job y 300 para el paso del reproceso, o sea más de 1,3 veces lo esperado y muy por debajo del
  tope duro de 6 horas de GitHub (A15).
- **El token de Earthdata vence el 2026-10-03.** El A/B tiene que terminar antes. El workflow
  autentica **sólo** con `EARTHDATA_TOKEN` y falla al instante si viene vacío: el par usuario y
  clave de los secretos está vencido y su reintento de login **bloqueó la cuenta diez minutos**
  (A71). No se reintenta ningún login.
- **Las salidas no van a `main`.** Cada job sube su JSON y su log como artefacto con 90 días de
  retención, y el job de recolección las publica además en una rama propia de la corrida
  (`s146-ab/<run_id>`), porque los artefactos caducan y en este proyecto ya se perdieron salidas
  así. El push a la rama lleva su propio reintento.
- **Riesgo de cobertura despareja** por cortes de NASA: el job de recolección lo mide y falla; la
  reparación es repetir el volcán con la lista corta del input y el mismo código.
- **Límite de muestra**: 20 días de fines de invierno. Llaima y Copahue no tienen ninguna noche
  positiva en la ventana, así que el recall que sostiene cada camino en esos dos volcanes es SIN
  DATO, no cero. MODIS tiene una sola pasada positiva.
- **Límite de la referencia**: los negativos limpios de los últimos días son más blandos porque el
  canal OCR llega con atraso. La Fase 1 lo midió cortando al 14 de septiembre y dio el mismo
  cuadro.
- **Disco**: nada de esto corre en local. MODIS no corre en Windows y el reproceso largo va a
  Actions por definición (aprendizaje S15).

### La puerta de las tres preguntas de `docs/MISSION.md`

Este A/B **no implementa** nada en `pipeline/`: crea perfiles nuevos que apagan flags existentes.
Aun así, lo que mide es si se **quita** un mecanismo que no está en los papers core:

1. **¿Está documentado en papers MIROVA core?** El Test 1 integrado en el ROI: **no**. Ningún
   texto de MIROVA lo describe, y la cita con que se justificó (`test1_integrated.py:17-18`)
   apunta a un artículo que no es (hallazgo V-06, que el plan propone abrir como divergencia D30).
   El Test 1 del paper es **por píxel**.
2. **¿Lo que se propone acerca al literal?** Sí: quitar un detector propio es acercarse.
3. **¿Se puede medir?** Sí, y es justamente lo que este A/B hace.

Quitar un parche propio no necesita las tres preguntas para **autorizarse**; las necesita para
**no reintroducirse**. Lo que sí exige A45 es el flip posterior, que este A/B no hace.

---

## 12. Decisiones tuyas antes de correr

| # | pregunta | recomendación |
|---|---|---|
| 1 | **¿Van los tres brazos, o sólo A y B?** El brazo C cuesta 11 jobs más y unas 6 horas de reloj | **los tres.** El brazo C mide la única adopción del proyecto cuyo propio A/B vio duplicarse la sobre publicación y que sigue encendida (H-A07). Si prefieres ahorrar, se corre con `brazos` sin el tercero: eso reduce el alcance, no cambia ningún criterio, y queda dicho acá |
| 2 | **¿Aceptas que la vara de recall que decide sea la PASADA y no la noche?** Es más estricta que "no perder noches" y puede dar NO ADOPTAR a un brazo que no pierde ninguna noche | **sí.** La vara de noche no distingue este brazo de uno que publicara al azar: el azar da 78 de 78 en el 98,5 % de los barajados. Un criterio que el azar cumple no es un criterio |
| 3 | **¿Aceptas el techo de 0,45 en VIIRS 375?** Es una caída de más de 41 puntos, pero deja el sistema todavía muy por encima del 5 % que declara el propio grupo de MIROVA (F-13) | **sí, para este A/B.** Este brazo no puede cerrar la brecha entero: el piso que queda es del camino contextual, que es el del paper, y eso es otra fase |

Y una que no es decisión sino aviso: si el brazo B gana y pierde recall que no quieres perder, el
camino no es descartarlo sino la Fase 2b (mudar al perfil `experimental`) o el brazo del nulo
descontado de la sección 3. Ninguno de los dos está construido.
