# `pc.classification`: qué se puede clasificar con lo que ya está escrito, y qué no (S145)

> Todos los números salen de
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_classification\sustrato_clasificacion.py`
> y viven en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s145_classification\sustrato_clasificacion.json`.
> Ninguno está escrito a mano (S91). Ventana **2026-09-01 a 2026-09-20**, los 11 Tier A:
> el régimen actual empieza con el PR #571 (2026-08-31) y una ventana que lo cruce mezcla
> dos regímenes (A104). Publicar = predicado del dashboard ejecutado con node desde
> `frontend/index.html` (A97).

## 1. Cobertura: qué cubrí y qué no

**Cubierto.** Las 2.285 pasadas nocturnas de los 11 Tier A en la ventana, las 1.050 que el
dashboard publica, el reparto de esas 1.050 en las categorías del marco A54, el inventario de
campos persistidos en la ventana, la evaluación de cinco reglas candidatas de artefacto, la
permanencia del sitio publicado por volcán y sensor, y el estado real del diseño S88 en el
código (`pipeline/store.py`, `pipeline/volcanic_features.yaml`, las cuatro vistas del frontend).

**No cubierto.**

- **Los 34 volcanes fuera del Tier A.** No entran al cron NRT y no tienen serie continua.
- **Cualquier ventana anterior al PR #571.** Medir ahí mezcla regímenes y no se puede leer.
- **La clasificación física real de cada record.** No existe etiqueta por record de (b), (c) ni
  (d) en ninguna parte del repo: la de S86 se hizo por volcán, a mano y a nivel de mecanismo.
  Eso no es una limitación de este trabajo, es el hallazgo central (§4).
- **El eje espacial contra imagen.** No comparé posiciones contra TIF de MIROVA ni contra Google
  Earth (A61). Este informe mide sustrato de campos, no ubicación.
- **No toqué `pipeline/`, no corrí reprocesos, no hice commits.** La medición es de solo lectura
  sobre el dato ya persistido.

**Controles del instrumento** (`sustrato_clasificacion.json`, clave `controles`):

- identidad del predicado de node contra los casos del guard S139: **en verde**
  (`[[0,1,1,1,0],[1,0]]`, el valor esperado).
- el cargador de este script es una copia del recorrido de `scripts/banco_paridad.py`; se corrió
  también el original sobre la misma ventana y coinciden en las tres cuentas: 2.285 records,
  1.050 publicadas y el mismo reparto de etiquetas. Si la copia hubiera derivado, todo lo de
  abajo mediría otra cosa.

La referencia se bajó del remoto de Mirova-v1 en el momento de correr (sha del consolidado
`847cced4`). El documento previo `docs/audit_s145/PARIDAD_Y_OBJETIVOS_S145.md` corrió con
`4b8521d4`, o sea el remoto se movió entremedio, pero sobre esta ventana no cambió nada: las
dos corridas dan el mismo reparto de etiquetas (162 `pos`, 1.433 `neg_limpio`, 32 `far_ref`,
658 `sin_info`). Vale la pena dejarlo anotado igual, porque la referencia está viva y una
corrida de mañana puede no coincidir.

## 2. Antes de medir: el campo no falta entero, falta la mitad y con otro nombre

`docs/MISSION.md` dice que la distinción entre los dos objetivos vive en `pc.classification`, y
es cierto que ningún record tiene una clave con ese nombre. Pero el diseño que ese texto cita,
`docs/superpowers/specs/2026-05-29-s88-pc-classification-design.md`, decidió en su §4.2 partir
el campo en dos mitades con nombres propios, y **las dos existen**:

| mitad del diseño | dónde está hoy | estado |
|---|---|---|
| geometría (`summit` / `extension` / `far`) | `pipeline/store.py:509-538`, campo `primary_cluster.geo_class`, persistido | implementado, 40.901 records de 62.880 lo tienen |
| cruce con MIROVA (`mirova_confirmed`) | `frontend/index.html:1415-1455`, campo transitorio `_mirova_confirmed`, calculado en el cliente | implementado solo en `index.html` |

Esto es A89 en estado puro: buscar `classification` da cero, y el cero se lee como ausencia. Lo
que falta no es el campo, es que **ninguna de las dos mitades sirve hoy para separar los dos
objetivos**, por razones distintas y las dos medidas más abajo. Conviene corregir la frase de
`docs/MISSION.md`, porque manda a implementar algo que ya está a medio construir.

Dos cosas más, verificadas:

- `_mirova_confirmed` se calcula **solo en `index.html`**. `frontend/diario.html` y
  `frontend/mosaico.html` no llaman nunca a `enrichWithMirovaConfirmation` (0 apariciones en
  los dos archivos) y lo tratan como falso siempre. Dos de las tres vistas live no tienen
  etiqueta.
- `geo_class = "extension"` disparó **5 veces en los 62.880 records de toda la historia**, las
  cinco en Lastarria, entre el 2025-10-26 y el 2026-09-19. El catálogo
  `pipeline/volcanic_features.yaml` tiene **2 entradas para 11 volcanes** (Lastarria y Puyehue
  Cordón Caulle), porque el propio archivo prohíbe inventar coordenadas y las de las otras
  features de S86 nunca se consiguieron.

## 3. Parte A: el reparto de lo que publicamos

De 2.285 pasadas nocturnas publicamos **1.050 (45,9 %)**. Ese es el denominador de todo lo que
sigue.

| categoría | n | de las 1.050 |
|---|---|---|
| (a) MIROVA publicó ALERTA **en esa misma pasada** | 157 | |
| (a) MIROVA publicó ALERTA en **la misma noche de ese volcán**, en otra pasada | 257 | |
| **(a) sumadas** | **414** | **39,4 %** |
| MIROVA vio calor **fuera del límite** del volcán (sin información para el cráter) | 15 | |
| **(b), (c) y (d) mezcladas, sin forma de separarlas** | **621** | **59,1 %** |

La segunda fila importa: son pasadas donde MIROVA no alertó en ese gránulo pero sí alertó esa
misma noche en otro. El evento es el mismo, así que contarlas como "extra nuestro" sería inflar
la brecha. Eso se decide con la referencia, no con el record.

### Por sensor

| sensor | publicadas | (a) | fuera de límite | pool (b)(c)(d) |
|---|---|---|---|---|
| MODIS | 52 | 26 | 0 | 26 |
| VIIRS 375 | 801 | 302 | 15 | 484 |
| VIIRS 750 | 197 | 86 | 0 | 111 |

### Por volcán (S126: una mediana agrupada acá invierte el veredicto)

| volcán | inner (km) | publicadas | (a) | pool |
|---|---|---|---|---|
| Isluga | 5 | 96 | 78 | 17 |
| Puyehue Cordón Caulle | 20 | 171 | 109 | 61 |
| Láscar | 5 | 80 | 44 | 35 |
| Tupungatito | 7 | 94 | 57 | 34 |
| Lastarria | 3 | 71 | 26 | 41 |
| Chaitén | 5 | 103 | 32 | 70 |
| Planchón Peteroa | 3 | 94 | 28 | 63 |
| Villarrica | 5 | 91 | 25 | 66 |
| Nevados de Chillán | 5 | 81 | 15 | 66 |
| **Llaima** | 5 | **84** | **0** | **84** |
| **Copahue** | 4 | **85** | **0** | **84** |

Llaima y Copahue son el caso límite: **en las 20 noches de la ventana, todo lo que publicamos ahí no tiene ni una
sola alerta de MIROVA detrás**. Son justamente los dos volcanes donde S86 identificó features
reales no publicadas (Pichi-Llaima, cráter El Agrio). Si son categoría (b) o son el artefacto
topográfico de A69, con el dato de hoy **no se puede decidir**, y ese es el punto del informe.

### Un dato que cambia cómo se lee todo lo anterior

**VIIRS 375 publica en las 19 de 19 noches en que tuvo pasada, en los 11 volcanes.** Doce de los 31
pares volcán-sensor publican todas las noches que tienen pasada. Publicar no es un evento en el
régimen actual: es el estado de base. Un operador que abra el dashboard cualquier noche va a ver
algo rojo en los 11 volcanes.

## 4. El hallazgo central: qué se puede separar y qué no

### (a) sí se separa, pero con una fuente externa y con retraso

La única etiqueta objetiva viene del CSV de MIROVA, que es externo al pipeline y llega tarde
(el canal OCR se publica después). Esto no es un defecto del diseño: es la naturaleza del dato.
Tiene una consecuencia de arquitectura que la §5.3 recoge.

### (c) geotermal o lacustre lejano ya está fuera, por construcción del predicado

En la ventana hay 423 pasadas con `distance_class = "far"` y **ninguna** de ellas se publica: el
predicado del dashboard exige `isSummitDetection`. Sobre las 1.050 publicadas,
`distance_class` tiene **un solo valor distinto**. O sea, la categoría (c) tal como A54 la
describe (lago, salar, campo geotermal fuera del cono) ya está filtrada desde S33 y no ensucia
el conteo. Lo que no tiene ningún campo es un (c) **dentro** del radio interno, por ejemplo un
lago cratérico: ahí no hay nada escrito que lo nombre.

### (b) contra (d): no hay campo. Y no es que discrimine mal, es que no existe

Esta es la conclusión que no hay que maquillar. La demostración tiene cuatro patas medidas
sobre las mismas 621 pasadas del pool, más una observación que las cierra.

**Primera: el campo que debía hacerlo es constante justo donde se hace la pregunta.**
`geo_class` vale `"summit"` en las **1.050 de 1.050** publicadas, con **0** `extension`. No es
que esté mal calculado: es que publicar exige que el cúmulo esté dentro del radio interno, y
`geo_class` dice exactamente eso. Sobre el conjunto publicado, el campo no tiene varianza. Lo
mismo pasa con `distance_class`, con `diag_n_bt_path`, con `diag_n_eti_path` y con
`n_excluded_water`: los cinco tienen **un solo valor distinto** sobre lo publicado.

**Segunda: el apoyo positivo de (b) es casi nulo.** De las 621 del pool, **6 (0,97 %)** caen
cerca de una feature catalogada. Con 2 entradas para 11 volcanes, el catálogo no puede sostener
la categoría.

**Tercera: la información de camino se colapsó.** De los cuatro contadores de camino
persistidos, `diag_n_bt_path` y `diag_n_eti_path` valen 0 en las 2.285 pasadas de la ventana, y
`diag_n_nti_path` dispara 5 veces. Queda un bit útil (dNTI contextual sí o no) más
`triggered_test1`, y la tabla cruzada es casi la misma en las dos clases:

| combinación | en (a), n=414 | en el pool, n=621 |
|---|---|---|
| Test 1 y dNTI contextual | 257 | 279 |
| solo Test 1 | 104 | 280 |
| solo dNTI contextual | 46 | 50 |
| ninguno de los dos | 7 | 12 |

**Cuarta, y la más dura: toda regla candidata de artefacto destruye lo que MIROVA confirmó.**
En vez de aplicar las reglas y repartir el pool como si eso fuera una medición, medí el costo de
cada una en el único estrato con etiqueta conocida, que son las 414 pasadas que MIROVA sí
respalda y que por lo tanto son reales sin discusión (A110: un control se valida midiendo su
nulo, no razonándolo).

| regla candidata | de dónde viene | destruye de (a) | marca del pool |
|---|---|---|---|
| `nti_max` en el piso (≤ -0,9) | A80 | **397 de 414** | 615 de 621 |
| cúmulo de un solo píxel | intuición común | 264 de 414 | 503 de 621 |
| `test1_k_observed` < 4 K | A83, el mejor discriminante hallado | 145 de 414 | 239 de 621 |
| `t_bg` < 260 K | diseño S87, ya refutado en S86 | 77 de 414 | 254 de 621 |
| sin camino BT | familia D9 / A23 | 414 de 414 | 621 de 621 |

La última fila es **degenerada, no refutada**: marca todo porque el camino BT no dispara nunca
en esta ventana. Las otras cuatro están refutadas por costo. La de A80 es el caso didáctico:
marca 397 de las 414 confirmadas por MIROVA, y por volcán marca **todas** las confirmadas en
Nevados de Chillán (15 de 15), Puyehue Cordón Caulle (109 de 109) y Chaitén (32 de 32). Esto confirma con datos de hoy el
refinamiento S116 de A80: el piso del NTI es compartido por lo real y lo artefacto.

**Y los campos que sí varían no alcanzan.** Midiendo cuánto separa cada campo numérico las 414
de (a) de las 621 del pool, que es la única comparación con etiqueta que existe, el mejor es
`f5_core_vrp_mw` con AUC 0,760 global, y por volcán va de **0,527 en Villarrica a 0,904 en
Puyehue Cordón Caulle**. `test1_k_observed` da 0,552 global y **se invierte** en 5 de los 9
volcanes con muestra suficiente (0,405 en Chaitén, 0,858 en Isluga): es régimen-dependiente,
exactamente como A83 predijo. El único eje con señal consistente es el geométrico:
`centroid_dist_km` da AUC 0,228, o sea invertido, que quiere decir que lo confirmado por MIROVA
está más cerca del cráter. Es el mismo resultado de A83: el único eje que separa es el espacial.

Ojo con la lectura de estos AUC: separar (a) del pool **no es** separar (b) de (d). Sirven como
cota. Un campo que ni siquiera distingue lo que MIROVA confirmó de lo que no, menos va a
distinguir una fumarola crónica real de un gradiente topográfico dentro del pool.

**Y de yapa.** La única maquinaria de etiquetado de artefacto que existe hoy, las
dos reglas de display `isCirrusArtifact` e `isDiffuseFieldArtifact` de `frontend/index.html`,
**disparó 0 veces en las 2.285 pasadas de la ventana**. En el régimen actual no está aportando
nada.

### Lo que la permanencia agrega

Medí, por volcán y sensor, cuán fijo es el lugar que publicamos. El resultado ordena el
problema: en Láscar el cúmulo se para siempre en el mismo punto (mediana 0,35 km del cráter,
dispersión 0,38 km en VIIRS 375) y MIROVA lo confirma seguido. En Villarrica y Nevados de
Chillán la mediana está en 2,8 y 2,4 km con dispersión de 2,2 y 2,5 km, o sea el cúmulo se
mueve por el cono noche a noche, y MIROVA casi nunca confirma. Eso **no** es un discriminante
(S144 midió que el 86 % del exceso de `keep_peak` era permanente, y permanente no quiere decir
artefacto), pero sí es la descripción honesta de lo que el operador está viendo: un estado de
base, no una secuencia de eventos.

## 5. Parte B: cómo se derivaría `pc.classification`

### 5.1 Lo que la medición prohíbe

Ninguna de las tres cosas siguientes es defendible con el dato de hoy:

1. **Un valor llamado `artifact` o `artifact_candidate`.** Cualquier regla que lo asigne destruye
   entre 77 y 414 de las 414 pasadas que MIROVA confirmó (§4). Marcar como dudoso lo que el sistema
   de referencia dio por bueno es peor que no marcar nada.
2. **`volcanic_extension` derivado del catálogo de features.** Con 2 entradas para 11 volcanes,
   alcanza para el 0,97 % del pool. La categoría (b) de S86 no es "cerca de un punto catalogado":
   es una fuente crónica distribuida, y eso el catálogo no lo modela.
3. **Un umbral físico, aunque se calibre.** El mejor campo va de 0,53 a 0,90 de AUC según el
   volcán. Un corte global no sirve y un corte por volcán es exactamente lo que `docs/MISSION.md`
   llama drift ("MIROVA NRT es UN algoritmo por sensor, uniforme entre volcanes").

### 5.2 Lo que sí se puede derivar hoy, sin campo nuevo del pipeline

**Propuesta: `pc.classification` sale entero del eje de referencia, que es el único con etiqueta,
y son cinco valores que el repo ya calcula.** `scripts/banco_paridad.py:etiquetar` produce
hoy, por pasada, exactamente la partición que hace falta. No hay que inventar nada: hay que
**persistir lo que ese script ya sabe**.

| valor | de qué sale | qué le dice al operador | n en la ventana |
|---|---|---|---|
| `mirova_confirmed` | fila ALERTA de MIROVA (consolidado u OCR) del mismo volcán y bucket de sensor a ±2 min | objetivo (1): esto es el clon, MIROVA publicó lo mismo | 157 |
| `mirova_same_night` | no hay ALERTA en esa pasada pero sí en la misma noche del volcán | objetivo (1): el mismo evento, otra pasada | 257 |
| `mirova_silent` | MIROVA listó esa pasada con RUTINA y VRP 0, sin alerta ni falso positivo esa noche | objetivo (2): MIROVA miró y no publicó. **Esto es el valor agregado, o el ruido, y el dato no distingue cuál** | 433 |
| `mirova_saw_outside` | MIROVA marcó calor fuera del límite del volcán | no hay información sobre el cráter | 15 |
| `no_reference` | MIROVA no listó esa pasada | no se puede afirmar nada | 188 |

Las cinco son verificables contra un CSV, no embeben ninguna física y ninguna filtra nada. Suman
las 1.050 publicadas de la ventana, y el reparto está en la clave `reparto_bajo_la_propuesta` del
JSON. Fíjate en el corte que importa: lo que hoy se cuenta como un bloque de 621 extras se parte
en 433 pasadas donde la referencia efectivamente miró y calló, y 188 donde la referencia
sencillamente no estaba. Son dos cosas distintas y hoy se ven igual.

**El nombre importa.** `mirova_silent` describe lo que se midió: que la referencia miró y no
publicó. No afirma "extensión real" ni "artefacto", que es justo lo que no se puede afirmar. La
tentación de llamarlo `volcanic_extension` es la trampa: convertiría una ausencia de dato en una
afirmación positiva.

### 5.3 Dónde se calcula: post-proceso, no pipeline, y tampoco solo frontend

El diseño S88 §4.2 ya argumentó que el cruce con MIROVA no debe entrar a `store.append_record`,
para no acoplar el NRT a un CSV de scraping de otro repo. Ese argumento sigue en pie y lo
refuerzo. Pero la conclusión de S88, "entonces va en el frontend", **falló en la práctica y la
medición lo muestra**: dos de las tres vistas live nunca lo calculan, y el número que se publica
no queda escrito en ningún JSON, así que no es auditable. Es el mismo problema que S132 resolvió
con `f5_core_vrp_mw`: mientras la cifra vivía solo en JavaScript, la cifra publicada no era la
cifra auditable.

Propuesta concreta: **un job programado, hermano de `.github/workflows/sync-mirova-csv.yml`, que
recorre una ventana móvil y escribe `primary_cluster.classification` en los JSON**. No toca
`pipeline/`, no toca la detección, no necesita A45.

Un detalle que no es menor: **la etiqueta cambia con el tiempo**. El canal OCR de MIROVA llega
tarde, así que un record que hoy es `mirova_silent` puede ser `mirova_confirmed` mañana. Por eso
tiene que ser un recálculo sobre ventana móvil y no un sello de una sola vez, y por eso no puede
vivir en el pipeline, que escribe cada record una sola vez cuando procesa el gránulo.

### 5.4 El segundo eje, separado y declarado como drift

Lo que el operador realmente necesita para leer el 59 % restante no es "real o artefacto", que no
se puede responder, sino "¿esto es el estado de base de este volcán, o cambió algo?". Eso sí es
derivable del dato persistido, pero **no de un record solo**: necesita la propia historia del
volcán (magnitud y posición contra su distribución reciente). Es lo que la §4 midió como
permanencia.

Si se implementa, va en un campo **aparte** de `classification`, nunca mezclado, y hay que
declararlo explícitamente: **es un criterio por volcán, o sea un drift respecto del objetivo (1)**.
Se sostiene solo porque es una etiqueta descriptiva de la capa de reporte, que no filtra, no
gatea y no toca la detección, es decir puerta 3 de las tres preguntas de `docs/MISSION.md`. Si
alguna vez alguien lo usa para suprimir algo, deja de pasar la puerta 3 y hay que volver acá.

Y lleva su propia advertencia escrita al lado: permanente no quiere decir artefacto. El lago de
lava de Villarrica y el campo fumarólico Lazufre son permanentes y son reales.

### 5.5 Qué hacer con `geo_class`

Dejarlo. No está mal ni sobra: es degenerado sobre lo **publicado**, pero las 423 pasadas `far`
de la ventana son precisamente donde ese campo trabaja, y ahí vive el toggle "incluir lejanas"
del dashboard. Lo que no corresponde es renombrarlo a `classification` y dar el frente por
cerrado: sería cambiar la etiqueta de la caja sin cambiar lo que hay adentro.

### 5.6 Las tres preguntas de `docs/MISSION.md`

1. ¿Está en papers MIROVA core? **No.**
2. ¿Cierra una divergencia documentada? **No.** No es una divergencia con MIROVA, es una carencia
   de reporte nuestra.
3. ¿Es alineación interna no metodológica? **Sí.** Es un campo derivado y descriptivo, calculado
   fuera del pipeline, que no filtra, no gatea, no altera la detección ni la magnitud. Puerta 3.

## 6. La lectura en una frase

De las 1.050 pasadas que publicamos en las 20 noches de la ventana, 414 tienen una alerta de MIROVA detrás y 621 no
la tienen, y para esas 621 **no existe hoy ningún campo persistido que permita decir si son la
extensión volcánica real que justifica el proyecto o un artefacto**, así que la etiqueta que
corresponde implementar es la que sale del cruce con la referencia y no una que prometa un juicio
físico que el dato no sostiene.
