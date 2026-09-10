# S136: resultado del probe de 3 brazos: **desenlace C, indeterminado por falta de sustrato**

> Run 34274884640, `success`, 20/20 pasadas con los tres brazos. Criterio de
> `docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md`, fijado antes de correr.
>
> **Corregido tras la auditoría de la sesión paralela (VRP 136)**, que trajo dos correcciones al
> resultado original de este documento. Las dos se verificaron acá por una vía independiente de
> la suya (`verificar_control_y_sustrato.py`) antes de aceptarlas, un par no es autoridad (A48).
> Su auditoría completa está en `AUDITORIA_PROBE_Y_CAMINOS.md`.

## Corrección 1: el probe SÍ es válido; el control de validez estaba mal construido

La versión anterior de este documento concluyó «el probe no reproduce la producción, ningún
número es interpretable». **Era el comparador.**

El control comparaba el probe (que corre con el código de hoy) contra
`data/mirova_equivalent/`, que para las pasadas de junio y julio fue escrito por el código **de
entonces**: régimen previo a `#535`, con la máscara de nube encendida y el fondo global 6-8 K más
alto en nevados. **No podía reproducir por construcción.** Es el razonamiento del propio
pre-registro ( «el régimen lo fija el código que procesa, no la fecha del granule» ) aplicado al
revés en el control.

**Verificación independiente por el fondo.** Si la causa es el régimen, las pasadas que
reproducen deben tener el mismo fondo y las que no, uno corrido. Medido:

| grupo | n | \|Δ t_bg\| mediana |
|---|---|---|
| reproducen | 10 | **0,19 K** |
| no reproducen | 10 | **3,62 K** |

Un factor **20** de separación. La no-reproducción es del comparador, no del probe.

**Confirmación directa, ya reproducida acá** (bajando el brazo control del A/B de S135, runs
34173711390 y 34208191011, que reprocesó esos mismos granules con código post-`#535`):

| comparación | resultado |
|---|---|
| probe vs **reproceso con el mismo código** | **16 / 16 coinciden al cuarto decimal** |
| probe vs producción (código de cuando se escribió el record) | 10 / 20 |
| producción vs reproceso, **mismo granule, código distinto** | **difieren 11 / 16** |

La tercera fila es la que cierra el caso: producción y reproceso difieren entre sí sobre el mismo
granule. El probe no se aparta de la producción por un defecto propio, sino porque **la producción
de junio-julio la escribió otro código**. Las 4 pasadas sin referencia son de Villarrica, que no
está entre los 6 volcanes del A/B.

(VRP 136 llegó a esto primero y reportó 9/16 en la tercera fila; acá dan 11/16, la diferencia es
de tolerancia o de conjunto y no cambia nada. El 16/16 coincide exacto entre las dos sesiones.)

**Con esto, las tres sospechas de la versión anterior quedan descartadas por medición, no por
argumento**: el A/B fue un reproceso real por `run_pipeline`, así que **pasó por `store.py`** y el
probe le coincide exacto (descarta la 1); Tupungatito 06-08 da 0,0930 en probe y en A/B, o sea
**el mismo granule**, el 0,0937 del SNPP de las 05:12 era otra pasada (descarta la 2); y
Lastarria 07-24 coincide exacto en 0,0421 (descarta la 3).

Nota: el conteo de 10/20 ya incorpora el arreglo del filtro por sensor (#611). La auditoría de
VRP 136 cita «0/15», que es la versión previa a ese arreglo.

## Corrección 2: el desenlace es C, no A: sólo 3 pasadas de nevado tienen sustrato

El filtro contextual sólo actúa si el hotspot final viene del camino Test 1
(`process_viirs.py:1779`, valor **legacy**). Las 20 pasadas se eligieron por
`triggered_test1 == True`, **que no es lo mismo**: disparar el Test 1 no es ganar la selección. Si
el camino contextual gana, el filtro no tiene sobre qué actuar.

Comparando ACTUAL contra SIN_FILTRO pasada por pasada:

| | pasadas |
|---|---|
| la magnitud publicada cambia | **7 / 20** |
| de esas, en nevados | **3** |
| de esas, en el control no nevado | 4 |

El criterio pre-registrado dice textual: «**C, indeterminado**: menos de 4 pasadas útiles en los
nevados». Hay 3.

Y el «SIN_FILTRO no explota, ×1,07» de la versión anterior sale de promediar 13 pasadas de nevado
de las que **10 nunca pasaron por el filtro**. La mediana no se mueve porque el filtro no actuó,
no porque no cure. Es la tercera aparición del mismo problema en el proyecto
(`feedback_s130_medir_el_sustrato_antes_del_ab`): la pregunta previa a «¿mejora algo?» es «¿llega
a ejecutarse?».

**Ambigüedad que decide Nicolás, no nosotros.** El pre-registro no define «pasada útil»
operacionalmente. Leerlo como «con sustrato» da **C**; leerlo como «13 pasadas de nevado» da
**A**. La primera lectura es de validez y no de gusto ,una pasada donde el filtro no actúa no
puede informar si el filtro cura, y meterlas diluye la mediana hacia «sin efecto» por
construcción, pero la elección hay que ponérsela por delante.

## Donde sí hay sustrato, el efecto es grande y apunta hacia MIROVA

| pasada | ACTUAL | SIN_FILTRO | |
|---|---|---|---|
| Tupungatito 07-07 | 0,0701 | 0,1533 | ×2,19 |
| Tupungatito 08-18 | 0,1097 | 0,1857 | ×1,69 |
| Planchón-Peteroa 06-01 | 0,0844 | 0,1116 | ×1,32 |
| Láscar 07-10 | 0,2290 | 0,2645 | ×1,16 |
| Lastarria 06-01 | 0,0515 | 0,0800 | ×1,55 |
| Lastarria 06-25 | 0,0761 | 0,1428 | ×1,88 |
| Lastarria 07-24 | 0,0421 | 0,1828 | ×4,34 |

**Sube en las 7, sin excepción**, entre ×1,16 y ×4,34. Como el sistema sub-reporta contra MIROVA
(paridad global 0,708), la dirección es la correcta. Y ninguna se acerca al 8-19× de D10.

## Qué queda

1. **El probe ya está validado** (16/16 contra el reproceso del mismo régimen), así que los
   ratios son legibles. Lo que falta es muestra, no instrumento.
2. **Ampliar la muestra en nevados eligiendo por sustrato**, no por `triggered_test1`: hacen falta
   pasadas donde el camino Test 1 **gane la selección**. Sin eso el desenlace seguirá siendo C por
   más pasadas que se agreguen. Es el único cambio que el probe necesita.
3. El control de validez del evaluador debe apuntar al reproceso del mismo régimen, no a
   `data/mirova_equivalent/`.

## Lección de método

Un control de reproducibilidad debe comparar contra **datos del mismo régimen de código**. La
fecha del dato no fija el régimen; lo fija el código que lo procesó. Y un criterio que filtra
casos («pasadas útiles») necesita su definición operacional escrita **en el pre-registro**, porque
si se deja para después, se elige mirando el resultado.

## Apéndice: los errores de instrumento de S136, entre las dos sesiones

Ocho, todos de la misma familia (A93: el instrumento medía otra cosa que la que decía medir), y
**ninguno lo cazó leer el código con cuidado**. Se dejan listados porque el patrón, no cada caso,
es lo que vale:

| # | el instrumento | qué lo delató |
|---|---|---|
| 1 | `n_test1_pixels` como proxy del mosaico nival | un **control** (Láscar, desierto, mismo footprint que un glaciar) |
| 2 | el máximo global del TIF como «el foco» de Isluga | un **número imposible** (focos a 20-31 km del cráter) |
| 3 | `final_hotspot_source` persistido como registro de qué rama corrió | un **cero** (lo reasigna `resolve_honest_anchor`, línea 2006) |
| 4 | el comparador sin filtro de sensor (comparaba contra VIIRS750) | un **número imposible** (persistido 0,0000 contra probe 0,0930) |
| 5 | el control de validez contra el régimen viejo | la sesión paralela |
| 6 | elegir las pasadas por `triggered_test1` en vez de por sustrato | la sesión paralela |
| 7 | *(VRP 136)* fallback silencioso a producción para el volcán sin referencia | que **Villarrica no podía tener referencia** |
| 8 | parseo de rutas con `/` en Windows al cargar el A/B | un **cero** (0/0 comparaciones) |

Cinco de los ocho los delató un control o un valor que no podía ser; dos, la otra sesión; ninguno,
una revisión del método. El corolario para el proyecto: **poner el control primero no es cortesía
metodológica, es el único mecanismo que funcionó**.
