# S136 — resultado del probe de 3 brazos: **desenlace C, indeterminado por falta de sustrato**

> Run 34274884640, `success`, 20/20 pasadas con los tres brazos. Criterio de
> `docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md`, fijado antes de correr.
>
> **Corregido tras la auditoría de la sesión paralela (VRP 136)**, que trajo dos correcciones al
> resultado original de este documento. Las dos se verificaron acá por una vía independiente de
> la suya (`verificar_control_y_sustrato.py`) antes de aceptarlas — un par no es autoridad (A48).
> Su auditoría completa está en `AUDITORIA_PROBE_Y_CAMINOS.md`.

## Corrección 1 — el probe SÍ es válido; el control de validez estaba mal construido

La versión anterior de este documento concluyó «el probe no reproduce la producción, ningún
número es interpretable». **Era el comparador.**

El control comparaba el probe —que corre con el código de hoy— contra
`data/mirova_equivalent/`, que para las pasadas de junio y julio fue escrito por el código **de
entonces**: régimen previo a `#535`, con la máscara de nube encendida y el fondo global 6-8 K más
alto en nevados. **No podía reproducir por construcción.** Es el razonamiento del propio
pre-registro — «el régimen lo fija el código que procesa, no la fecha del granule» — aplicado al
revés en el control.

**Verificación independiente por el fondo.** Si la causa es el régimen, las pasadas que
reproducen deben tener el mismo fondo y las que no, uno corrido. Medido:

| grupo | n | \|Δ t_bg\| mediana |
|---|---|---|
| reproducen | 10 | **0,19 K** |
| no reproducen | 10 | **3,62 K** |

Un factor **20** de separación. La no-reproducción es del comparador, no del probe. (VRP 136 lo
verificó por otra vía: contra el brazo control del A/B de S135, que reprocesó esos mismos
granules con código post-`#535`, obtuvo **16/16 exacto**; las 4 sin referencia son de Villarrica,
que no está entre los 6 volcanes del A/B. Ese número es suyo, no reproducido acá.)

Nota: el conteo de 10/20 ya incorpora el arreglo del filtro por sensor (#611). La auditoría de
VRP 136 cita «0/15», que es la versión previa a ese arreglo.

## Corrección 2 — el desenlace es C, no A: sólo 3 pasadas de nevado tienen sustrato

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

El criterio pre-registrado dice textual: «**C — indeterminado**: menos de 4 pasadas útiles en los
nevados». Hay 3.

Y el «SIN_FILTRO no explota, ×1,07» de la versión anterior sale de promediar 13 pasadas de nevado
de las que **10 nunca pasaron por el filtro**. La mediana no se mueve porque el filtro no actuó,
no porque no cure. Es la tercera aparición del mismo problema en el proyecto
(`feedback_s130_medir_el_sustrato_antes_del_ab`): la pregunta previa a «¿mejora algo?» es «¿llega
a ejecutarse?».

**Ambigüedad que decide Nicolás, no nosotros.** El pre-registro no define «pasada útil»
operacionalmente. Leerlo como «con sustrato» da **C**; leerlo como «13 pasadas de nevado» da
**A**. La primera lectura es de validez y no de gusto —una pasada donde el filtro no actúa no
puede informar si el filtro cura, y meterlas diluye la mediana hacia «sin efecto» por
construcción— pero la elección hay que ponérsela por delante.

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

1. **Rehacer el control de validez contra datos del mismo régimen de código** — no contra lo
   persistido. Con eso, el probe queda validado y los ratios pasan a ser legibles.
2. **Ampliar la muestra en nevados eligiendo por sustrato**, no por `triggered_test1`: hacen falta
   pasadas donde el camino Test 1 gane la selección. Sin eso el desenlace seguirá siendo C por
   más pasadas que se agreguen.
3. Las tres sospechas de la versión anterior (`store.py`, granule distinto, `f5_core = None`)
   **quedan descartadas** como causa de la no-reproducción.

## Lección de método

Un control de reproducibilidad debe comparar contra **datos del mismo régimen de código**. La
fecha del dato no fija el régimen; lo fija el código que lo procesó. Y un criterio que filtra
casos («pasadas útiles») necesita su definición operacional escrita **en el pre-registro**, porque
si se deja para después, se elige mirando el resultado.
