# S147: el Test 1 integrado medido contra su propio nulo

> Registro de decisión de la divergencia **D30** (`docs/MIROVA_DIVERGENCES.md`), abierta en S146
> con gravedad 5 y dejada "descrita, sin decisión". Este documento cubre **la cara del
> estadístico**, no la cara bibliográfica (la cita que no corresponde a ningún artículo
> localizable, que se trata aparte).
>
> Tag defensivo: **`pre-s147-test1-estadistico-corregido`** (A45), empujado antes del primer
> cambio en `pipeline/`. Punto de retorno:
> `git checkout pre-s147-test1-estadistico-corregido -- pipeline/`

## 1. El fenómeno, primero

Una fuente de calor más chica que el píxel, el lago de lava de Villarrica o un campo fumarólico,
no levanta ningún píxel lo suficiente como para cruzar un umbral por píxel, pero sí entibia un
poco a varios vecinos a la vez. El Test 1 integrado existe para eso: en vez de mirar píxel por
píxel, suma el exceso de radiancia MIR de todo un disco de 3 km alrededor del cráter y pregunta
si esa suma es "mucha".

Para decir si es mucha hace falta una vara, y la vara tiene que responder una pregunta física
concreta: **cuánto valdría esa suma en una noche en que no hay absolutamente nada caliente**, con
el volcán dormido y sólo el ruido del sensor y la aspereza del terreno. Si el estadístico no se
mide contra ese valor de reposo, no está midiendo calor: está midiendo otra cosa.

## 2. El defecto

La suma recorta a cero los excesos negativos. Eso es físicamente correcto: un volcán agrega
calor, no lo quita, así que un píxel más frío que el fondo no aporta evidencia negativa de
actividad. El problema es la vara con que se compara esa suma recortada.

En el código de hoy (`pipeline/test1_integrated.py`, función `compute_test1_mir`):

- se suma `max(0, L - L_fondo)` sobre los N píxeles del disco, y
- se compara contra `k · sigma_fondo · raíz(N)`, que es la desviación de la suma **sin** recortar.

Al recortar, el ruido puro deja de promediar cero. Cada píxel aporta, en promedio,
`sigma / raíz(2 pi) = 0,399 sigma`. La suma de N píxeles crece entonces **con N**, mientras la
vara crece sólo con **raíz(N)**. El cociente vale

```
k_observado(ruido puro) = 0,399 · raíz(N)
```

y `sigma` se cancela. El criterio deja de depender del calor y pasa a depender **del tamaño del
disco**: se cumple cuando `0,399 · raíz(N) > 3`, o sea con **N mayor que 56,6 píxeles**. El disco
de 3 km tiene unos 208 píxeles en VIIRS 375 m, 50 en VIIRS 750 m y 32 en MODIS. En el sensor más
fino, el criterio absoluto del Test 1 está satisfecho **antes de mirar el volcán**.

Eso explica el orden que se observa en producción y que de otro modo no tiene sentido físico: el
sensor de mejor resolución es el que más publica sobre noches en que MIROVA miró y no vio nada.

## 3. Reproducción independiente, en esta sesión

No se hereda el número de S146: se volvió a medir con un banco propio,
`tests/test_test1_estadistico_nulo_s147.py`, sobre 40 escenas sintéticas construidas **sin nada
caliente** (fondo uniforme de 265 K más ruido gaussiano de 1,5 K, grilla de 375 m, disco de 3 km).

| lo que mide | resultado |
|---|---|
| disparos del criterio absoluto con ruido puro | **38 o más de 40 escenas** |
| valor de reposo observado contra `0,399 · raíz(N)` | coincide dentro del **15 %** |

Los dos tests que miden esto pasan **contra el código de hoy**, sin ningún cambio: son la línea
base roja del arreglo. Si algún día fallan, el estadístico cambió y hay que volver a D30.

## 3b. El puente con producción: la misma firma en los records reales

Lo anterior es sintético. Para que decida algo hay que verlo en el dato que el sistema publica de
verdad. El pipeline persiste `test1_k_observed`, que es exactamente el cociente que la derivación
predice. Instrumento: `experiments/_s147/reposo_test1_en_records_reales.py`, ventana desde el
2026-08-29 (entera posterior al cambio de régimen de #535, A104), población **todos** los records
de los 11 Tier A, no negativos limpios (A90: por eso no es comparable con el 1,056 de
`docs/audit_s146/`, que usó otra población).

| sensor | N del disco | reposo `0,399·raíz(N)` | mediana observada | razón | supera 3 sigma | n |
|---|---|---|---|---|---|---|
| VIIRS 375 | 201 | 5,66 | 4,70 | **0,831** | **90,9 %** | 1048 de 1099 |
| VIIRS 750 | 50 | 2,83 | 2,37 | **0,838** | **27,7 %** | 902 de 1092 |
| MODIS | 28 | 2,12 | 1,94 | **0,912** | **11,9 %** | 168 de 535 |

Dos cosas que leer ahí, y las dos importan.

**La razón es casi la misma en los tres sensores**, 0,83 a 0,91, aunque sus discos difieren por un
factor 7 en número de píxeles. Si el estadístico estuviera midiendo calor volcánico, no habría
ninguna razón para que tres poblaciones distintas, de tres sensores distintos, se sentaran todas
al mismo porcentaje de una curva que sólo depende del tamaño del disco. Se sientan ahí porque es
eso lo que están midiendo. (Que la razón sea algo menor que 1 es esperable: el ruido real no es
gaussiano puro ni independiente entre píxeles vecinos, así que la suma recortada queda un poco por
debajo del nulo ideal.)

**La fracción que supera el umbral reproduce el orden de la sobre-publicación medida en S146.**
Lado a lado, con la salvedad de que son poblaciones distintas:

| sensor | supera 3 sigma por ruido (acá) | publica en negativos limpios (S146) |
|---|---|---|
| VIIRS 375 | 90,9 % | 86,3 % |
| VIIRS 750 | 27,7 % | 21,4 % |
| MODIS | 11,9 % | 11,4 % |

Esa correspondencia no estaba medida antes: la auditoría S146 tenía el mecanismo por un lado y las
tasas por sensor por otro. Acá se ven como lo mismo. Y explica por qué en MODIS el Test 1 no
sostiene la brecha: con 28 píxeles en el disco, su valor de reposo (2,12) **no alcanza** el umbral
de 3, así que ahí el que publica de más es el camino contextual, que es el que sí está en el
paper.

## 4. El arreglo

Se conserva el recorte, que es físicamente correcto, y se corrige la vara: se compara el
estadístico recortado contra **su propio** nulo. Para `X ~ N(0, sigma)`:

```
E[max(0, X)]   = sigma / raíz(2 pi)        = 0,398942 sigma
Var[max(0, X)] = sigma² (1/2 - 1/(2 pi))   = 0,340845 sigma²
```

de donde el estadístico corregido es

```
z = (suma_recortada - N · 0,398942 · sigma) / (sigma · raíz(N · 0,340845))
```

Con ruido puro, `z` tiene media 0 y desviación 1 **para cualquier N**, así que el umbral `k = 3`
recupera el significado que dice tener. Con una fuente real el numerador crece con la energía de
la fuente y el disparo sobrevive.

Dos propiedades que el arreglo **no** toca, y que el banco verifica explícitamente: no cambia qué
píxeles contribuyen, ni el centroide. Es una corrección de la vara, no de la selección. Eso
importa porque la posición del Test 1 alimenta el ancla del cúmulo publicado.

### 4b. Cuánto cambiaría, medido sin reprocesar

El estadístico corregido resulta ser una **transformación lineal** del campo que el pipeline ya
persiste: `z = 1,7127 · (k_obs − 0,399·raíz(N))`. Eso permite medir su efecto sobre el dato real
sin reprocesar nada. El criterio `z > 3` equivale a exigir `k_obs > 0,399·raíz(N) + 1,75`, o sea
**7,41 en VIIRS 375, 4,58 en VIIRS 750 y 3,87 en MODIS**, contra el 3,0 fijo de hoy.

Instrumento: `experiments/_s147/efecto_del_estadistico_corregido.py`, misma ventana.

| sensor | disparos del Test 1 hoy | sobreviven al corregido | |
|---|---|---|---|
| VIIRS 375 | 927 | 109 | **11,8 %** |
| VIIRS 750 | 238 | 60 | **25,2 %** |
| MODIS | 20 | 11 | 55,0 % |

**Esto cambia cómo hay que leer la decisión.** El arreglo parecía el camino intermedio entre
dejar el Test 1 como está y apagarlo. No lo es: en VIIRS 375 apaga casi 9 de cada 10 disparos, así
que se parece mucho más al brazo "sin Test 1" que al control. La diferencia entre los dos no está
en cuánto recortan, sino en **qué** recortan: el corregido conserva el 11,8 % que sí supera el
ruido, y ese 11,8 % es justamente el candidato a ser calor real.

Es una **cota sobre lo persistido, no una re-ejecución**: marcar SOSPECHA. El script declara sus
tres límites (N nominal contra N efectivo tras descartar píxeles inválidos, el criterio relativo
que no se rehace, y que apagar un disparo no equivale a no publicar porque otro camino puede
publicar igual). La unidad que decide sigue siendo la **pasada**, y la mide el evaluador del A/B.

## 5. Cómo entra, y por qué apagado

Entra como argumento `null_corrected` de las funciones puras, expuesto por el perfil como
`enable_test1_null_corrected`, **apagado por omisión**. Con el flag apagado, cada campo numérico
de la salida es idéntico al de hoy: eso también es un test, porque en este proyecto ya pasó que
un cambio declarado no-op sí cambiaba producción (regla S126).

Apagado, porque el número que falta no es el de la derivación sino el operacional: **cuántas
noches con actividad real se perderían**. Ese número lo da el A/B, no el escritorio. El orden
correcto es dejar el arreglo disponible y medido en laboratorio, y que el experimento decida
entre tres salidas posibles:

1. **Apagar el Test 1 entero** (el brazo que ya está pre-registrado en
   `experiments/_s146_ab_sin_test1/`), si resulta que no sostiene ninguna detección que
   interese conservar.
2. **Dejarlo con el estadístico corregido**, si sí sostiene detecciones reales: es la salida
   elegante, porque conserva el mecanismo físico (la fuente sub-píxel entibia a varios vecinos)
   y le quita el piso espurio.
3. **Dejarlo como está**, si el A/B mostrara que la sobre-publicación no viene de acá. La
   auditoría S146 midió que el Test 1 es el único sostén de 186 de 322 publicaciones en
   negativos limpios de VIIRS 375, así que esta salida es improbable, pero es la que el
   experimento tiene que poder elegir.

## 6. Lo que este documento NO afirma

- **No** afirma cuánta sobre-publicación desaparece con el arreglo. Eso es una cota superior
  medida sobre lo persistido (S146), no una re-ejecución: lo decide el A/B.
- **No** afirma que el Test 1 integrado sea infiel al paper por tener un defecto estadístico. Es
  infiel por otra razón, independiente: el Test 1 de `sp426.5.pdf` p. 6 es **por píxel** contra un
  umbral fijo de NTI y no tiene ninguna suma sobre el ROI. El integrado es un detector propio del
  proyecto. Esa es la cara de D30 que este documento no cierra.
- **No** toca `compute_test1_nti`, que tiene el mismo defecto en su rama pero está apagada en
  producción (`ENABLE_TEST1_NTI_INTEGRAL = False`). Se corrige en el mismo cambio por coherencia,
  también detrás del mismo flag.
