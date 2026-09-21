# Verificador con contexto limpio: el mecanismo de la magnitud cero (S149)

Fecha: 2026-09-21. Sólo lectura sobre el repo. Scripts y salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_audit\verificador_magnitud_cero\`.
Los datos del A/B se extrajeron fuera del repo (carpeta temporal de la sesión, 64 MB, sólo la ruta pedida).
No leí los informes de los frentes C y D hasta terminar mis mediciones; al final los abrí sólo para comparar números (sección 6).

**Instrumento.** "Publica" es el predicado del tablero ejecutado con node desde `frontend/index.html`
(`scripts/banco_paridad.py`, función `correr_node`, l. 138; publica = summit y válida y no artefacto y magnitud de pantalla > 0, l. 124 a 129).
La referencia es el snapshot `data/mirova_reference/mirova_v1_snapshot/` (tabla y OCR) con el cargador unificado, pareo a más o menos 120 s, sólo pasadas nocturnas, etiquetas de `banco_paridad.etiquetar` (l. 275).
Lo que es mío: la clasificación de por qué no publica, el detalle campo por campo, el cruce con los dos brazos del A/B y los conteos en negativos.

## 1. Caminos por los que cada afirmación podía estar mal (enumerados antes de medir)

1. Que el "cero" fuera de otro campo que el que usa el tablero (`vrp_mw`, `f5_core_vrp_mw`, `primary_cluster.vrp_mw`). Revisado: `isValidDetection` (index.html l. 1466) exige `primary_cluster.vrp_mw > 0` cuando hay cúmulo, y `mirovaEqVrpCore` (l. 1166) sólo usa el núcleo F5 en VIIRS 375 y sólo si la base es > 0. En VIIRS 750 y MODIS el campo que decide es `primary_cluster.vrp_mw`. Descartado como error.
2. Que el cúmulo "en el cráter" no fuera el primario. Medí sobre `primary_cluster` directamente. Descartado.
3. Que el pareo tomara otra pasada. Tolerancia de 120 s y mismo sensor; en los 28 casos de VIIRS 750 hay exactamente una fila de la tabla por pasada. Descartado.
4. Que la referencia estuviera en un tramo defectuoso (`scripts/calidad_referencia_mirova.py`). La ventana desde el 2026-06-01 pisa los hitos del OCR del 06-11 y 06-13. No afecta a VIIRS 750 ni a MODIS: las 28 y las 68 pérdidas tienen fila de la TABLA (0 casos sólo OCR). Sí afecta a VIIRS 375 (varias pérdidas son sólo OCR).
5. Que "a menos de 1,4 km del cráter" midiera desde otro punto. **Confirmado como salvedad**: `centroid_dist_km` mide desde el ancla de detección, no desde la coordenada nominal (ver sección 2).
6. Que la lectura del código fuera incorrecta. Leído por mi cuenta; es correcta en lo grueso e imprecisa en un punto (sección 3).
7. Que la condición también fuera frecuente donde MIROVA no vio nada (tasa base). **Confirmado, y es lo más importante del informe** (sección 5).

## 2. Afirmación 1: VIIRS 750 pierde alertas por magnitud cero. SE SOSTIENE, con salvedades

Salida: `v1_produccion.py 2026-06-01 2026-09-21` y `v3_out_20260601.txt`.

- Pasadas nocturnas con alerta de MIROVA en VIIRS 750 desde el 2026-06-01: **120**. El tablero publica **92 (76,7 %)**. Alertas sin record nuestro: 0.
- Las **28 perdidas son, las 28, la misma clase**: `distance_class = summit`, cúmulo primario con `vrp_mw = 0.0`, `centroid_dist_km` entre 0,049 y 1,334 km, `discarded_reason` nulo, fuente `ctx_cluster`. Por volcán: Láscar 7, Isluga 7, Puyehue Cordón Caulle 7, Planchón Peteroa 3, Villarrica 3, Tupungatito 1.
- El píxel más caliente del cúmulo es menor o igual a `t_bg_k` en 28 de 28 (estrictamente menor en 24; en 4 es idéntico al centésimo, SIN VERIFICAR por qué). Mediana de la diferencia: 1,44 K bajo el fondo.
- Código que produce el cero: `pipeline/process_viirs_mod.py` l. 1017 a 1036. El fondo es la radiancia de `t_bg` (mediana del anillo) y el exceso se recorta con `np.maximum(L_hot - L_bg_rad, 0.0)` (l. 1034). El flag que cambiaría ese fondo por la media de vecinos (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750`, D25) existe y está apagado (leído de `pipeline.profile`).

Cinco pasadas, campo por campo (`v4_cinco_pasadas.txt`):

| pasada (VIIRS 750) | MIROVA (MW, km) | píxeles anómalos (K) | t_bg (K) | t_max de escena (K, a km) | cúmulo primario | 1.er pase / recaptura | Test 1 |
|---|---|---|---|---|---|---|---|
| Láscar 2026-09-21 05:42 | 0,22 a 0,75 | 262,37 y 260,62 | 264,19 | 279,31 a 23,7 | 2 px, 0,0 MW, 0,049 km | 0 / 2 | no (1,51) |
| Isluga 2026-06-07 05:48 | 0,20 a 0,75 | 261,84 y 262,89 | 264,28 | 270,66 a 29,4 | 2 px, 0,0 MW, 1,086 km | 0 / 2 | no |
| Planchón Peteroa 2026-06-25 06:00 | 0,31 a 1,68 | 261,89 | 263,91 | 278,77 a 23,6 | 1 px, 0,0 MW, 0,649 km | 0 / 1 | sí (4,72) |
| Villarrica 2026-08-23 05:54 | 0,60 a 0,75 | 272,31 | 275,28 | 281,00 a 19,2 | 1 px, 0,0 MW, 0,317 km | 0 / 1 | no |
| Puyehue C. Caulle 2026-07-03 05:12 | 0,52 a 7,83 | 269,26 | 269,94 | 279,69 a 23,1 | 1 px, 0,0 MW, 0,255 km | 0 / 1 | no |

En las cinco: `vrp_mw = 0`, `f5_core_vrp_mw` nulo, `vrp_mir_mw` nulo. El `t_max_k` del record NO es el píxel del cráter: está a 19 a 29 km, en el valle tibio, así que no sirve para argumentar nada del cúmulo.

Salvedades que encontré:
- **Los 28 cúmulos no tienen ni un píxel de primer pase** (`diag_n_first_pass_pixels = 0` en 28 de 28; `diag_n_second_pass_recapture` 1 o 2). Todo lo que hay en el cráter lo puso el segundo pase, que corre sin condicionar (regla A118). "Sí se detecta" es cierto en el record, pero es la detección más débil que el pipeline tiene.
- "A menos de 1,4 km del cráter" es distancia al ancla de detección. En Puyehue Cordón Caulle el píxel está a 7,3 a 8,2 km de la coordenada nominal (`anomaly_pixels.dist_km`), coherente con los 7,65 a 7,83 km de MIROVA: es el lacolito, no el cráter. En Tupungatito el píxel está a 2,6 km y MIROVA a 5,03: ahí no hay coincidencia ni de radio. Y coincidir en radio no es coincidir en objeto (A93, A107).
- Con el Test 1 disparado (8 de 28) el cero persiste, porque la fuente interna sigue siendo el cúmulo contextual y el recómputo del Test 1 no entra.

## 3. Afirmación 2: el costo de apagar el Test 1 en VIIRS 375. SE SOSTIENE CON SALVEDADES

Salida: `v2_out.txt`. Ventana de los datos: 2026-09-01 a 2026-09-20; 2.362 pasadas en cada brazo, 2.362 claves comunes. Diferencia de perfiles verificada con `diff`: sólo `paths.enable_test1_path: false`.

- VIIRS 375, pasadas con alerta: 146. Control publica 146, sin Test 1 publica 140. **Pierde 6, gana 0**. Confirmado.
- De las 6, **4 conservan cúmulo summit con 0,0 MW** (Isluga 09-13, Tupungatito 09-17, Nevados de Chillán 09-05 y 09-14) y 2 pasan a `far` con el cúmulo a 7,9 y 20,2 km (Isluga 09-19, Nevados de Chillán 09-18). Confirmado el 4 más 2.
- **"En el mismo lugar" vale para 2 de las 4, no para las 4.** Nevados de Chillán: mismas coordenadas en ambos brazos (0,407 y 0,387 km). Isluga 09-13: el control publica un cúmulo a **2,995 km** y el brazo deja uno a 0,821 km. Tupungatito 09-17: control a **2,514 km**, brazo a 0,233 km (y MIROVA a 5,2 km). En esas dos el control publicaba con otro píxel, lejos del ancla; lo que se pierde ahí no es "la misma detección con otra magnitud".
- Código (`pipeline/process_viirs.py`): el recómputo sólo corre si la fuente interna es `"test1"` (l. 1919 y 1946), o sea cuando el Test 1 gana la fuente (l. 1762 a 1782; la prioridad sobre cúmulo rival débil está encendida). El fondo de ese recómputo sale de una cascada (l. 1873 a 1896 y `pipeline/test1_integrated.py` l. 148 a 172): anillo intermedio de 1,5 a 3 km, luego anillo global, luego el fondo local del Test 1. Los dos primeros sólo valen para los volcanes con `lbg_global_compatible` (Láscar, Nevados de Chillán, Lastarria; `volcanoes.yaml` l. 129, 270, 653). **Decir "el fondo propio del Test 1" es exacto para 8 volcanes e inexacto para esos 3**, y 2 de los 4 casos son de Nevados de Chillán: ahí el fondo es el anillo de 1,5 a 3 km. Sin Test 1, el fondo vuelve a ser la mediana del anillo regional y el exceso se recorta a cero: eso sí es correcto. El equivalente en VIIRS 750 está en `process_viirs_mod.py` l. 1234 a 1263 (sin anillo intermedio).
- Ojo: el `final_hotspot_source` que queda en el JSON lo reescribe el ancla honesta (S106), así que `ctx_cluster` en el record no dice si el Test 1 ganó por dentro. Se deduce del número: en Nevados de Chillán 09-05 el píxel está 3,6 K bajo `t_bg` y aun así el control da 0,096 MW.
- El otro lado del mismo A/B, que hay que leer junto: en negativos limpios de VIIRS 375 el brazo baja la publicación de 334 a 113 de 387, y los cúmulos summit con 0,0 MW suben de 4 a **29**. Son negativos que hoy callan por el cero.

## 4. Afirmación 3: MODIS. SE SOSTIENE en los números, y la tasa base la vacía de valor

Salida: `v1_produccion.py 2026-03-01 2026-09-21`.

- Alertas MODIS nocturnas de MIROVA desde el 2026-03-01: **77** (76 de Láscar, 1 de Villarrica). Publica **9 (11,7 %)**.
- Las **68 perdidas son todas de Láscar**, todas `far` con `discarded_reason = partial_eruption_hotspot_too_far`, todas con cúmulo primario con energía (0,06 a 4,85 MW) a **0,456 a 3,22 km** (mediana 1,55). Por mes: marzo 25, abril 19, mayo 9, junio 12, julio 2, agosto 1. Todas con fila de la tabla.
- Pero la misma condición (etiqueta `far` y cúmulo con energía dentro del radio interior) está en **3.559 de 4.555 negativos limpios (78,1 %)** de la misma ventana. Desde junio y sólo en Láscar: 15 de 16 alertas contra **158 de 181 negativos (87,3 %)**. La condición no separa: destapar la etiqueta publicaría casi todas las noches sin actividad. Coincide con la rebaja de A82 en `CLAUDE.md`.

## 5. Lo que pidió el punto (d): los negativos limpios en la misma condición

Ventana 2026-06-01 a 2026-09-21 (`v3_out_20260601.txt`).

| sensor | alertas en la condición | negativos limpios en la condición | negativos que hoy publican |
|---|---|---|---|
| VIIRS 750 (summit, 0,0 MW) | 28 de 120 (23,3 %) | **268 de 3.118 (8,6 %)**; 171 a 1,4 km o menos | 716 (23,0 %) |
| VIIRS 375 (summit, 0,0 MW) | 19 de 690 (2,8 %) | 115 de 2.050 (5,6 %) | 1.291 (63,0 %) |
| MODIS (far con energía dentro) | 15 de 17 | 2.014 de 2.596 (77,6 %) | 308 (11,9 %) |

Lectura para VIIRS 750: si el arreglo del cero hiciera publicar a todos los cúmulos summit que hoy dan cero, se recuperan 28 alertas y se agregan hasta 268 publicaciones en negativos limpios (de 23,0 a 31,6 %), más 27 en pasadas de rutina de noches con alerta. **Casi diez falsas por cada alerta recuperada, como techo.** Y por volcán la condición ni siquiera favorece a las alertas: en Láscar está en 7 de 50 alertas (14 %) y en **43 de 174 negativos (24,7 %)**; en Isluga 7 de 21 contra 49 de 227. Los cúmulos en cero de los negativos son iguales a los de las alertas: 264 de 268 sin primer pase, píxel bajo el fondo en 199 de 204 con píxeles guardados, mediana 1,8 K bajo el fondo. No medí cuánta magnitud les daría un fondo distinto: eso es SIN VERIFICAR y es la pregunta que decide.

## 6. Hallazgos propios

1. **VIIRS 375 tiene el mismo cero en producción, con el Test 1 encendido**: 19 de las 33 alertas perdidas desde junio son cúmulo summit de 1 píxel con 0,0 MW, fuente `test1_roi`, Test 1 disparado en 19 de 19, y son sólo de Lastarria (14) y Láscar (5), los volcanes cuyo fondo es el anillo de 1,5 a 3 km. En Lastarria ese anillo cae sobre el campo fumarólico (los cúmulos están a 1,1 a 3,0 km). En negativos limpios, 99 de los 115 ceros son también `test1_roi`. El recómputo del Test 1 no es una garantía contra el cero: depende de qué fondo le toque. Las otras 14 pérdidas no tienen cúmulo alguno (ahí sí es detección), varias con referencia sólo de OCR.
2. Los 28 ceros de VIIRS 750 son recaptura pura del segundo pase (sección 2). Cualquier plan que "arregle la magnitud" está apostando a píxeles que el primer pase rechazó.
3. "Mismo lugar" en el A/B vale para 2 de 4 (sección 3).
4. El `t_max_k` del record está a 19 a 29 km del volcán en los casos revisados: no describe al cúmulo.

Comparación con los auditores (abiertos al final): el frente C da 23 perdidas desde el 13 de junio con 20 bajo el fondo; con mi ventana desde el 1 de junio son 28, y restringiendo a su ventana me dan 23, con 20 estrictamente bajo el fondo y 3 iguales. MODIS 9 de 77: idéntico. El frente D dice "4 en el mismo píxel": mis coordenadas dan 2 de 4.

## 7. Veredictos

| afirmación | veredicto | gravedad que le pongo |
|---|---|---|
| 1. VIIRS 750, magnitud cero | SE SOSTIENE el hecho y el mecanismo de código. Salvedades: recaptura sin primer pase, distancia al ancla y no al cráter, y la condición está en 8,6 % de los negativos (más frecuente en negativos que en alertas en Láscar) | alta como diagnóstico, **riesgo alto como palanca**: sin medir los negativos con el fondo nuevo no es adoptable |
| 2. A/B sin Test 1, VIIRS 375 | CON SALVEDADES: 6, 4 y 2 confirmados; "mismo lugar" sólo 2 de 4; "fondo propio del Test 1" es inexacto para Láscar, Nevados de Chillán y Lastarria | media; n = 6 no sostiene un plan por sí solo |
| 3. MODIS, Láscar, etiqueta far | SE SOSTIENE en los números; como palanca CAE, porque la condición está en 78 a 87 % de los negativos | alta como advertencia: no destapar la etiqueta |
