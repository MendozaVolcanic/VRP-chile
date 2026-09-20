# Verificador con contexto limpio del pre-registro del A/B "sin el Test 1 integrado" (S147)

> **Encargo**: verificar `experiments/_s146_ab_sin_test1/PREREGISTRO.md` antes de despachar el
> experimento. El verificador recibió sólo la ruta, con el preámbulo anti-fabricación entero, y se
> le pidió atacar cuatro ejes (los umbrales, el poder de cada vara de recall, la paridad de
> cobertura, y que los perfiles difieran sólo en lo declarado) más la pregunta transversal de qué
> no mide el pre-registro y debería. **Re-corrió los tres bancos**, no sólo los releyó.
>
> Commit auditado `cf5dd7cf7`. Corpus propio del verificador: 2.386 records en la ventana
> 2026-09-01 a 2026-09-20, etiquetados con `banco_paridad` y el predicado del dashboard ejecutado
> con node.

## Veredicto: NO despachar sin arreglar antes

Dos hallazgos dan vuelta el veredicto del experimento por sí solos, y los dos son de una línea.

## Hallazgos que bloquean

### H1. El piso de recall de VIIRS 750 rechaza el valor que el pre-registro dice aceptar (gravedad 5, CONFIRMADO)
`experiments/_s146_ab_sin_test1/parametros.json:20` (`"VIIRS750": 0.667`), aplicado en
`evaluar.py:450` con el redondeo de `evaluar.py:124`.

El pre-registro deriva el piso como "13 de 18 menos la pérdida segura de Cordón Caulle, o sea 12
de 18" y escribe `0.667`. Pero 12 dividido 18 es 0,6666..., que el evaluador redondea a `0.6667`,
y **`0.6667 >= 0.667` es falso**. El umbral escrito es mayor que el valor que pretende admitir.

> ```
> evaluar._tasa(12,18) = 0.6667   piso = 0.667   cumple? False
> 13/18 -> 0.7222  piso 0.722  cumple True
> 12/18 -> 0.6667  piso 0.667  cumple False
> ```

**Qué se decidiría mal**: el brazo B pierde exactamente la pasada que el pre-registro anticipa
como pérdida aceptable y sale **NO ADOPTAR por C1**. Se dejaría encendido un detector que la
Fase 1 identifica como sostén del 57,8 % de lo que publicamos donde MIROVA no vio nada, por un
error de redondeo en la tercera cifra. Y el lector concluiría "el brazo se lleva recall de VIIRS
750", que es falso: se lo lleva el umbral.

### H2. La pérdida que se le resta al piso no se puede perder (gravedad 4, CONFIRMADO)
`PREREGISTRO.md:322` y `parametros.json:21`.

La pasada de Cordón Caulle VIIRS 750 del 2026-09-07 05:30, que el piso descuenta como "pérdida
segura", **el control ya no la publica** (`pub = 0`). No se puede restar de las 13 publicadas algo
que no está entre ellas. La entrada sí es coherente en la unidad de **noche**, pero el piso de C1
está en la unidad de **pasada**. Sumado a H1, el piso efectivo tolera **cero** pérdidas en VIIRS
750.

### H3. Nada detecta un brazo de CONTROL con pasadas de menos (gravedad 4, CONFIRMADO)
`contar_pasadas.py:86-87` (`sobran` se calcula y no se usa), `evaluar.py:278`, `:344`, `:374-376`.

C0 compara cada brazo **contra el control** y falla sólo cuando al brazo le faltan pasadas. Si el
corte de red de NASA le pega al control, los brazos quedan con `sobran > 0` y `faltan = 0`, y el
script imprime "COBERTURA PAREJA". El control positivo tampoco lo ve, porque compara sólo la
**intersección** con producción: un control al que le falta el 30 % de las pasadas da fracción de
publicación idéntica 1,0.

El pre-registro cita A108 como la razón de existir de C0, y deja sin cubrir justo al brazo que es
la referencia de C1, C3, C4, C5 y del propio C0.

### H6. Ni la ventana ni la referencia están fijadas: el corpus se movió mientras auditaba (gravedad 4, CONFIRMADO)
`parametros.json:4-5` dice "FIJA: no se mueve aunque el A/B se despache más tarde", pero lo fijo
son **las fechas, no el contenido**. El verificador volvió a correr `poder_recall.py` con los
mismos argumentos unas horas después del pre-registro: **2.360 records pasaron a 2.386**,
`sin_info` de 732 a 757, las noches de 218 de 219 a 220 de 220. El último día de la ventana es
**hoy** y está a medias (113 records contra 121 a 129 de los días anteriores).

Ya hay un efecto visible: la clasificación de poder de la vara noche-sensor agregada pasó de
DÉBIL a DISCRIMINA entre las dos corridas, por el borde del corte.

**Qué se decidiría mal**: los techos de C3 son tasas absolutas calibradas sobre 373 y 622
negativos limpios. Si al evaluar hay 390 y 640, el brazo puede cruzar un techo por movimiento del
denominador y no por efecto del flag.

### H5. El techo de C3 del brazo C exige margen cero en VIIRS 750 (gravedad 4, CONFIRMADO)
> ```
> VIIRS375  control 322/373=0.8633 techo 0.82 -> apagar AL MENOS 17 de 322 (Fase 1 predice 21) -> margen 4
> VIIRS750  control 133/622=0.2138 techo 0.21 -> apagar AL MENOS  3 de 133 (Fase 1 predice  3) -> margen 0
> ```
C3 es conjuntivo sobre los dos sensores, así que si el brazo C apaga 2 de las 3 pasadas de VIIRS
750, falla. NO ADOPTAR para el brazo C es casi seguro por construcción, y se leería como "la
prioridad por rival débil no aporta nada" cuando el umbral no dejaba lugar a que aportara.

## Hallazgos de instrumento y de cobertura de criterios

### H4. C4 compara medianas sobre conjuntos distintos (gravedad 4, CONFIRMADO)
`evaluar.py:213-231` y `:484-492`, umbral en `parametros.json:45`. La mediana del control se
calcula sobre lo que publica **el control** y la del brazo sobre lo que publica **el brazo**, que
es un subconjunto, sin pareo. Si el brazo deja de publicar el 20 % de menor magnitud, sin que
cambie ni un vatio de las que sobreviven, la mediana se corre hasta 0,23, **más del doble del
umbral de 0,10**:

> ```
> Lastarria|VIIRS375    n=9  mediana 1.195 -> n=8  1.424  (delta |r-1| = +0.229)
> Tupungatito|VIIRS375  n=26 mediana 0.608 -> n=21 0.838  (delta |r-1| = -0.230)
> ```

Segunda cara: un estrato que cae bajo los 5 pares **desaparece** del criterio en vez de contar.
Hoy sólo 9 estratos llegan a 5 pares y cuatro están entre 5 y 9. El mismo archivo ya hace el pareo
bien en `posicion_cumulo` (`evaluar.py:240-247`), así que la inconsistencia es interna.

### H8. El control de identidad del predicado no puede fallar (gravedad 3, CONFIRMADO)
`evaluar.py:556` guarda el valor en `meta` y **nunca lo compara**. El evaluador de la sesión
anterior sí lo hacía (`experiments/_s143_evaluador/evaluar.py:704`). Hoy los valores siguen
siendo los correctos, así que lo que falta es el pin, no la salud del predicado. Es el modo de
falla de A110: un control que pasa en verde sobre un instrumento cambiado.

### H9. El "DISCRIMINA" de la vara de pasada en VIIRS 750 no sobrevive a un nulo mejor (gravedad 3, CONFIRMADO)
`poder_recall.py:115-128` baraja la publicación **por record** dentro de cada volcán y sensor, lo
que destruye la correlación intra-noche, que es real (si el cráter está caliente, publican todas
las pasadas de esa noche). Rebarajando por **bloques de noche**:

> ```
> A. por record:  pasada_VIIRS750  obs 13/18 | nulo med  7  min 3 max 11 | alcanza 0.000
> B. por bloque:  pasada_VIIRS750  obs 13/18 | nulo med 10  min 5 max 15 | alcanza 0.040
> ```

Con la estructura preservada el azar **alcanza y supera** el observado (máximo 15 contra 13), y la
etiqueta queda a 0,01 del corte. VIIRS 375 aguanta sin moverse y las dos varas de noche siguen sin
discriminar, **así que la conclusión principal del documento se sostiene**: lo que no se sostiene
es la fuerza declarada de la vara de VIIRS 750.

### H10. El mecanismo es bidireccional y el pre-registro sólo mide la baja (gravedad 3)
Apagar el Test 1 también apaga el recómputo de magnitud gateado por `source == 'test1'`. Cuando
ese recómputo da 0, **tapa** la publicación; apagarlo devuelve el cúmulo contextual, que puede
traer magnitud mayor que cero. Medido en el control:

> ```
> VIIRS375  t1=True y pub=0:   0 de 962
> VIIRS750  t1=True y pub=0:  38 de 957  (neg_limpio 23, sin_info 12, pos 3)
> MODIS     t1=True y pub=0:   3 de 467  (neg_limpio 3)
> ```

Las 3 positivas de VIIRS 750 son de Cordón Caulle. O sea que el brazo B podría **subir** el recall
de VIIRS 750 de 13 a 16 de 18, y a la vez subir la publicación en 23 negativos limpios. C6
declararía "la atribución del mecanismo queda refutada" cuando lo que pasó es un segundo
mecanismo, conocido y declarado en la misma sección, que el criterio no contempló. CONFIRMADO en
las 41 pasadas expuestas; SOSPECHA en que efectivamente ganen publicación.

### H11. Dos instrumentos declarados como controles no entran en ningún veredicto (gravedad 3, CONFIRMADO)
`posicion_cumulo` (con `n_movidos_mas_de_500_m`) y `nulo_barajado` (con `fuera_del_nulo`) se
calculan y no aparecen en el bloque de criterios. Un brazo que mueve el cúmulo publicado varios
kilómetros sale ADOPTAR igual. En un proyecto donde A61 nació porque dos auditorías completas se
perdieron el eje espacial, y donde el operador mira un mapa, ese es el eje que menos conviene
dejar sin criterio.

### H12. El piso de VIIRS 375 tolera perder 25 pasadas con alerta (gravedad 3, CONFIRMADO)
Con 143 positivas, el piso 0,825 admite bajar a 118. La red de 0,5 MW cubre poco: la mediana del
VRP de MIROVA en esas pasadas es 0,150 MW y **126 de 143 están bajo 0,5**. Es defendible como
política declarada (el perfil acepta falsos negativos sub píxel), pero el documento no lo dice con
el número, y quien lea "cumple C1" entenderá "no perdimos recall".

### H7. C0 cuenta con el nombre del gránulo, que cambia si NASA promueve NRT a estándar (gravedad 3)
`contar_pasadas.py:56` incluye el gránulo en la clave; `evaluar.py:107-108` no. Hoy 347 de los
2.386 records de la ventana son NRT, y los jobs corren entre 9 y 18 horas, así que el control de
un volcán y su brazo pueden estar separados por medio día. CONFIRMADO en sus dos partes medibles;
SOSPECHA en que la promoción ocurra dentro de la ventana.

### H13, H14, H15, H16, H17, H18 (gravedad 2 y 1, todos CONFIRMADOS)
- **H13**: las dos listas de noches esperadas de C2 no son consistentes entre sí (6 entradas
  contra 4). Hoy no muerde, pero puede.
- **H14**: el estrato `sin_info` es el **31,7 % del corpus** (757 records, 417 publicados) y no lo
  juzga ningún criterio. El operador los ve igual en el tablero.
- **H15**: C5 casi no puede fallar para un brazo que sólo apaga un detector. El nulo está bien
  construido, su valor informativo para este brazo es bajo.
- **H16**: la fórmula del valor de reposo aparece de dos formas (`0,3989·raíz(N)` en `:52` y
  `0,3989·sigma·N` en `:184`). Las dos son correctas para objetos distintos, pero la de `:184` es
  la receta del brazo siguiente, y quien la lea restaría una cantidad con la escala equivocada por
  un factor raíz(N), entre 5 y 14 según el sensor.
- **H17**: la reparación de una cobertura despareja no tiene regla de parada, y cada repetición
  cambia los datos (H6).
- **H18**: dos parámetros que no pueden activarse por separado, y una cita corrida en una línea
  (`process_viirs.py:1299`, no `:1300`).

## Verificado limpio (lo que NO hay que volver a mirar)

- **Los perfiles.** `diff_perfiles.py` reproduce carácter por carácter: 143 atributos, producción
  contra sí misma **0** diferencias, el control **0**, cada brazo **exactamente su único flag**.
  La resolución evita la trampa A89: los tres usan `extends` y escriben el flag bajo `paths:`, que
  es de donde lo lee `pipeline/profile.py`, y el volcado se hace con `VRP_PROFILE` en un
  subproceso, no leyendo el texto del YAML. No hay otros lectores del perfil.
- **La tabla de poder se reproduce exacta**, las seis filas. No hay ningún número transcrito
  torcido en la sección 4.
- **La conclusión central sobre la vara de noche aguanta una prueba que el documento no hizo**:
  adelgazando las publicaciones al azar hasta p = 0,5, que es la tasa esperada del brazo,
  sobreviven 74,25 noches de 78. La vara de noche sigue sin poder incluso al régimen del brazo.
  **La elección de la pasada como vara decisoria está justificada.**
- **C1 y C3 juntos no los puede pasar un brazo que apague publicaciones al azar**: 2.000 sorteos
  por cada p entre 0,3 y 0,9 dan 0,0 % en VIIRS 375 y 0,1 % en VIIRS 750. La pareja sí exige que
  la caída sea **selectiva**.
- **Los records se escriben también cuando no hay nada que detectar** (143 de 228 records de
  septiembre de Llaima tienen 0 píxeles anómalos), así que la cobertura la fija la disponibilidad
  de gránulos y no la detección. Era el riesgo mayor para C0.
- **Las etiquetas no dependen de nuestras detecciones**: salen sólo de la referencia pareada al
  timestamp. No hay circularidad.
- **El evaluador no es un sello de goma**: `sintetico.py` pasa entero, con cuatro veredictos por
  criterios distintos. Un brazo copia byte a byte del control da NO ADOPTAR por C3.
- **El mecanismo físico de la sección 1 resiste la lectura del código**, y lo que podría haberlo
  invalidado (la co-validación NTI que restringiría la suma) está **apagada** en producción.
- **La afirmación "desaparecen cinco cosas y sólo cinco" se verifica en los tres procesadores.**
- **La red de 0,5 MW no tiene el agujero del `or 0`**: de las 157 positivas publicadas, cero
  tienen el VRP de referencia en `None`.
- **El workflow está bien armado**: `"on"` entre comillas, candado de aprobación, sólo token con
  fallo inmediato si viene vacío, un volcán y un brazo por job con directorio propio, conteo de
  cobertura antes de publicar nada, salida por dos caminos.
- **El pre-registro declara su propia contaminación** (sección 10: los umbrales se derivaron de
  las cotas de la Fase 1 ya conocidas, con la regla de derivación de cada uno). Eso es lo que hizo
  auditable la aritmética de H1, H2 y H5.

## Lo mínimo que hay que arreglar antes de despachar, según el verificador

H1 y H2 son de una línea cada uno y son los únicos que por sí solos dan vuelta el veredicto. H3 y
H6 se arreglan con un conteo simétrico del control contra producción y congelando la copia de los
CSV y de `data/mirova_equivalent` en un directorio sellado con sha. H5 pide decidir si el brazo C
se corre con un techo que puede no cumplirse, o si se le cambia el criterio.
