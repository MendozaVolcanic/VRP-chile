# Verificador con contexto limpio de D-29 en el evaluador de D25 (diff c44709e27..6f43ec624)

## 1. Encabezado

- Fecha y hora del servidor al empezar: Thu, 22 Oct 2026 06:35:58 GMT (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`); al cerrar: ver §8.
- Commit medido: `6f43ec624` en `C:\vrp-trabajo\s159-evaluador` (rama `s159-evaluador-d25`, igual a `origin/s159-evaluador-d25`; `git status --porcelain` vacío antes de empezar y, al cerrar, sólo `?? experiments/_s159/instrumentos/verificador_d29/`). Ningún git que cambie nada; las copias para mutar (`experiments/_verif_d29_pre/`, `experiments/_verif_d29_mut/`) se borraron (conteo 0 al final de cada corrida).
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo medio. La sesión se cortó una vez por un error 529 de la API y se reconstruyó desde el disco; la primera corrida sintética siguió corriendo sola y terminó (`sintetico_real_salida_cortada_529.txt`, 7 de 7 casos), y se repitió entera: las dos corridas dan números idénticos en los 7 casos (`sintetico_real_primera_corrida.json` contra `sintetico_real.json`, 0 diferencias).
- CARPETA: `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_d29\`.
- Lo que NO miré: ningún dato real del A/B de D25 (ni `v1.json`, ni `v2.json`, ni carpetas `_s157_ab_d25_*`, ni `D:\vrp-trabajo\temporales\s157d25`, ni `s158*`), ningún artefacto de runs, el razonamiento del auditor (abrí `experiments/_s159/instrumentos/d29/README.md` y `mutar_d29.py` sólo como material que la tarea cita, para re-correrlo); `evaluar_fk.py` fuera de las funciones que el evaluador de D25 llama (`archivos_ref`, `tabla`, `proteccion`, `etiquetas_regla`, `ocr_snpp`, `suma_errores`, `errores_por_pasada`); `armar_tabla.py` fuera de la clave y la ventana; `banco_paridad.indexar_referencia` y `etiquetar` por dentro; el resto del diff (carpeta `verificador_d34`, copias `raiz_falsa`); V2 con datos (no corrí V2, que no excluye nada); MODIS (el evaluador lo saca por construcción, `evaluar_d25.py:354`); la suite entera (no la re-corrí, ver afirmación 5); `--repeticion` y `--ruido-de` con datos (sólo lectura).
- Datos de los casos sintéticos: producción `data/mirova_equivalent/` del propio worktree (es K desde `FRONTERA_K` = 2026-09-18, `evaluar_d25.py:67`), siete volcanes (los de `probar_evaluar_d25.py`), VIIRS 375 y 750, ventana 2026-09-18 a 2026-10-18: 1.778 records base (Lascar 228, Isluga 224, NevadosDeChillan 261, Lastarria 233, Villarrica 282, PuyehueCordonCaulle 290, Tupungatito 260; `sintetico_real_salida.txt`). Producción en esa copia tiene, en los días excluidos y esos siete volcanes, 7+7 pasadas el 13, 27+27 el 17 y 26+26 el 18 (VIIRS 375 + 750), todas entre las 04 y las 06 UTC (conteo reproducible con el bloque de §6).

## 2. En una pantalla

1. El código hace lo que la fila D-29 dice: `DIAS_EXCLUIDOS["V1"]` = 13, 17, 18, 19 y 20 de octubre (19 y 20 inertes porque V1 termina el 18), V2 vacío, y la exclusión llega a la tabla K-brazo, a los crudos de cada brazo y a la referencia de cobertura; todo lo que decide (P1, P1b, P2, M, P4, P5, protección, etiquetas, cobertura, determinismo) sale de esos tres objetos ya filtrados. Las 5 afirmaciones: 1 CONFIRMADO, 2 CONFIRMADO, 3 CONFIRMADO EN PARTE, 4 CONFIRMADO, 5 CONFIRMADO EN PARTE.
2. Medido con datos sintéticos propios (7 casos + 2 extra, 2 corridas idénticas): un brazo sin el 17, sin el 18 o sin el 13, los tres brazos sin 13/17/18 contra producción que sí los tiene, `distance_class` cambiados y centroides movidos sólo el 17, K' apagado sólo esos días y una pasada a la 01:30 UTC del 13: en ninguno queda rastro (cobertura OK, P4 0, determinismo 834/834 y 824/824, 0 claves con fecha excluida en el JSON). Control positivo con `DIAS_EXCLUIDOS` vacío: todo eso aparece (60 pasadas más por sensor, `D: le faltan 54 de K`, P4 54 y 16, determinismo FALLA, cabecera ausente).
3. Lo que no se sostiene: el candado. Las 5 pruebas del repo atrapan 4 de mis 9 mutaciones; las 5 que pasan en verde son justo las que dejan pasar días excluidos en `evaluar` (resultado del filtro descartado en los crudos, `excl` reemplazado por `()` en la tabla o en la cobertura, fecha en hora de Chile, cabecera de V1 callada). Mi instrumento sintético las ve las 9 (V29-01, gravedad 2).
4. Artefactos: `rojo_d29.txt` salió de un borrador de la prueba, no de la commiteada (V29-02); con la commiteada re-medí 5 de 5 rojas por `AssertionError` sobre `c44709e27` y 5 de 5 verdes sobre `6f43ec624`; las 4 mutaciones del auditor se reproducen; 36 de 36 pruebas del evaluador; `probar` re-corrido (§8), sin caso de D-29 (V29-06).
5. Ningún hallazgo tuerce el veredicto de D25 con el código de hoy. El riesgo es futuro: una edición del evaluador que rompa el cableado pasaría las pruebas. Recomendación (la decide quien orquesta): sumar al candado un caso de punta a punta como `cobertura_sintetica.py` antes del tag de lectura.

## 3. Veredicto por afirmación

### Afirmación 1: los días excluidos de V1 son el 13, 17, 18, 19 y 20 de octubre de 2026 y V2 no excluye ninguno

**CONFIRMADO** (gravedad propia 1). `evaluar_d25.py:73`, TEXTO: `DIAS_EXCLUIDOS = {"V1": ("2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"), "V2": ()}`. Se lee por el nombre de la ventana, `evaluar_d25.py:750` `excl = DIAS_EXCLUIDOS.get(a.ventana, ())`, así que sigue a `--ventana`, no a `--desde/--hasta`. Matices que no cambian el veredicto:
- El 19 y el 20 son inertes en V1 por construcción: `VENTANAS["V1"]["hasta"] = "2026-10-18"` (`evaluar_d25.py:60`; `PREREGISTRO.md:104`, TEXTO: «V1, 2026-08-29 a 2026-10-18») y los tres lectores de pasadas cortan con `desde <= t[:10] <= hasta` (`crudos`, l. 352; `claves_cobertura`, l. 376 y 381; `armar_tabla.py:27` recibe la misma ventana). El comentario de la l. 71-72 lo declara. Sólo actuarían si alguien corriera `--ventana V1 --hasta 2026-10-20` (argumentos «sólo para la prueba del evaluador», l. 1021-1022).
- V2: `()`; con tupla vacía `filtrar_dias` devuelve la entrada sin tocarla (l. 336-337) y la cabecera calla (l. 752). Lo medí sólo en código; no corrí V2.
- Caminos de `caminos.md` cerrados: no es string contra date (todo es string `YYYY-MM-DD` contra `k.split("|")[2][:10]`, y la clave es `vol|bucket|YYYY-MM-DD HH:MM` por `ev.clave`, `experiments/_s146_ab_sin_test1/evaluar.py:110`, y por `crudos` l. 358 / `claves_cobertura` l. 377 y 382 con `datetime_utc[:16]`; `proteccion` la parsea con `"%Y-%m-%d %H:%M"`, `evaluar_fk.py:192`); el año y el mes son los de los datos (producción tiene pasadas esas fechas, §1); no hay una segunda copia del conjunto en `evaluar_fk.py` (grep `DIAS_EXCLUIDOS`: sólo `evaluar_d25.py` y la prueba, que lo fija por igualdad de tupla ordenada, `tests/test_evaluar_d25_dias_d29_s160.py:40-41`); la fecha es la UTC de la pasada (`datetime_utc`), no la de la referencia ni hora local (mutación p6, §4 V29-01).

### Afirmación 2: la exclusión llega a todos los consumidores de pasadas

**CONFIRMADO** (gravedad propia 1), por lectura de todos los puntos donde el evaluador lee pasadas y por medición sintética con control positivo. Puntos de lectura de archivos en `evaluar_d25.py` (grep `json.load|read_text|open(`): l. 135 (`volcanoes.yaml`, no pasadas), 326 (`fusionar`, sólo copia), 350 (`crudos`), 374 y 379 (`claves_cobertura`), 391 (logs de flags), 857 (`--ruido-de`: sólo `ruido_frac`, fracciones por sensor, no pasadas), 979 (`combinar`: JSON de resultados). Más `E.tabla` (subprocess `armar_tabla.py`, l. 773) y `E.tabla` para `--repeticion` (l. 862). Dónde llega el filtro:
- Tablas K-brazo (P1, P1b, P2, M, P4 movidas, determinismo): `T = {p: {k: v for k, v in filtrar_dias(t, excl).items() ...}}` (l. 775). Todo lo que sigue sale de `T`: `todas` (l. 780), `prot = E.proteccion(todas, ...)` (l. 781, itera `claves_`, `evaluar_fk.py:190`), `protegidas` (l. 791), `base`/`labs` (`E.etiquetas_regla(sorted(todas), ...)`, l. 864 y 869, itera `claves_`, `evaluar_fk.py:212`), `tabla_lab` (l. 865), `Tx` (l. 871), `contar` (l. 872: `TKD`, `TKG`; `E.suma_errores` y `E.errores_por_pasada` iteran `T`, `evaluar_fk.py:342` y 361; `contribuciones_p2` l. 434-435; `lista_p2` l. 466; M l. 645), P4 (l. 887), `sin_geometria(todas, ...)` (l. 918, itera `claves_`, l. 406).
- Crudos de cada brazo (cobertura entre brazos, versión, cableado, P4 `distance_class`, P5): `R[n] = filtrar_dias(R[n], excl)` (l. 779) y `claves_ = {n: set(R[n])}` (l. 785).
- Referencia de cobertura: `cob = {vs: filtrar_dias(ks, excl) ...}` (l. 794-795).
- Protección de alertas y etiquetas por regla: no leen pasadas por su cuenta; se evalúan sobre `todas` (l. 781, 864, 869), ya filtrado.
- `--repeticion`: `T_rep = E.tabla(...)` (l. 862) **no pasa por `filtrar_dias`**, pero sólo se consulta por `.get(k)` para claves `k` que ya recorren `TKD` filtrado (`contar`, l. 586 y 600); una pasada del 17 en la repetición nunca se visita. Benigno; hallazgo V29-03 de gravedad 1.
- `--ruido-de`: no son pasadas (l. 857).
- Medición propia (`cobertura_sintetica.py`; salidas `sintetico_real_salida.txt`, `sintetico_real_extra_salida.txt`; JSON `sintetico_real.json`, `sintetico_real_extra.json`; evaluador sin mutar, dos corridas idénticas). Cada caso toca SÓLO días excluidos en UN consumidor:

  | caso | consumidor | records tocados | cobertura_ok | P4 movidas / cambia dc | determinismo V375, V750 (pasadas, misma decisión) | cabecera en línea 1 | claves 13/17/18 en el JSON |
  |---|---|---|---|---|---|---|---|
  | nulo | ninguno | 0 | True | 0 / 0 | 834/834, 824/824 | sí | 0 / 0 / 0 |
  | d_sin_17 | R (D sin el 17) | 54 | True | 0 / 0 | 834/834, 824/824 | sí | 0 / 0 / 0 |
  | d_sin_18 | R | 52 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | d_sin_13 | R | 14 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | todos_sin_13_17_18 | cob (producción sí los tiene) | 120 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | dc_17_en_D | R (P4 distance_class) | 54 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | mov_17_en_D | T (P4 centroides +0,002°) | 22 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | g_apagado | T (K' con VRP 0 el 13/17/18) | 120 | True | 0 / 0 | igual | sí | 0 / 0 / 0 |
  | madrugada_13 | fecha UTC (pasada 01:30 UTC del 13 en los 3 brazos) | 6 | True | 0 / 0 | igual | sí | 0 / 0 / 0; `madrugada` 0 |

  Pregunta 1 del instrumento (si el filtro no llegara, ¿se vería?): sí, y está medido con el control positivo p1 (`DIAS_EXCLUIDOS` vacío, `mutaciones_propias_salida.txt`): `d_sin_17` → `cobertura_ok False`, `D: le faltan 54 de K y tiene 0 que K no`; `todos_sin_13_17_18` → `False` con «faltan 7 a 9 de 112 a 132» por volcán y sensor; `dc_17_en_D` → `cambia_distance_class 54`; `mov_17_en_D` → `movidas 16`; `g_apagado` → determinismo FALLA (894/869, 884/874); el determinismo pasa de 834 a 894 pasadas en V375 y de 824 a 884 en V750 (las 60 por sensor de los tres días); el JSON trae claves del 17 y del 18 (6 a 70 según el caso) y la cabecera desaparece. Pregunta 2 (instrumento vivo): la primera corrida de las mutaciones murió por una copia sin `_congelado_v1` y el comparador dijo «VE LA MUTACION» en 9 de 9 por nulos (`mutaciones_propias_salida_1_instrumento_caido.txt`); se corrigió marcando «EVALUADOR CAIDO» y copiando la referencia, y la segunda corrida da 0 caídas (A110: el instrumento se validó midiendo su nulo).
  Denominador y ventana: 1.778 records VIIRS de 7 volcanes, 2026-09-18 a 2026-10-18, producción del worktree en `6f43ec624`; no es el A/B real (11 volcanes, desde el 29-ago, tres brazos de verdad).

### Afirmación 3: la primera línea del veredicto combinado dice «EVALUADO SIN ... (D-29)» y la cabecera de V1 también

**CONFIRMADO EN PARTE** (gravedad propia 1). Lo que se sostiene: (a) `combinar` antepone `"EVALUADO SIN %s (D-29) | %s"` al veredicto (`evaluar_d25.py:999-1001`) y lo imprime en una sola línea `== VEREDICTO COMBINADO: EVALUADO SIN ... (D-29) | <estado> | por ventana ...` (l. 1002); la prueba del repo lo exige con `startswith("EVALUADO SIN")` sobre el valor devuelto (`tests/...:78`). (b) La cabecera de V1 es la **primera línea de stdout** del evaluador: medido, `cabecera_linea_idx [0]` en los 9 casos sintéticos (`primera_linea` = `== EVALUADO SIN 2026-10-13, 2026-10-17, 2026-10-18, 2026-10-19, 2026-10-20 (D-29: CMR no sirvió esos días; fuera en los tres brazos y en la cobertura)`, `D:\vrp-trabajo\temporales\verif_d29\real_extra\d_sin_18.txt` l. 1); los avisos de `pipeline.profile` y de la calidad de la referencia van a stderr (mismo archivo, después de `--- stderr ---`). La parte que NO se sostiene tal como está dicha: la declaración es de la **línea impresa**, no del JSON por ventana: `res["estado"]` (lo que `combinar` lee como estado de la ventana, l. 980) no lleva la declaración; va en `res["dias_excluidos"]` (l. 751), y es `combinar` quien la vuelve a armar. Si alguien lee `v1.json["estado"]` solo, no ve la exclusión (V29-04). Dos matices más: la cabecera se imprime siempre que `excl` no esté vacío, caiga o no alguna pasada (es lo que pide «declarados», no «excluidos de hecho»); y `combinar` une los días de todas las ventanas en un solo conjunto ordenado sin decir de qué ventana son (l. 999); hoy V2 no excluye nada.

### Afirmación 4: «el 13 parcial» se excluye entero en los tres brazos

**CONFIRMADO** como lectura admisible y la única simétrica (gravedad propia 1). Texto sellado, `tasks/LOOP_OBJETIVOS.md:534` (checkout principal), TEXTO: «D25 se evalúa sin el 17 al 20 de octubre ni el 13 parcial, declarados en el veredicto»; contexto de la misma fila, TEXTO: «Los días que CMR no sirve no se reponen ni se repite la ventana: se excluyen de V1 en los tres brazos por igual y el veredicto lo dice en su primera línea». La unidad que la fila nombra es el **día** y la condición es «en los tres brazos por igual». La otra lectura, «sólo la parte del 13 que faltó», exigiría saber qué gránulos faltaron en cada brazo, y no es simétrica si faltaron distintos; la fila no da ese dato, y la bitácora describe el 13 como hueco de la propia producción (`tasks/LOOP_OBJETIVOS.md:513`, TEXTO: «los huecos de producción del 13 y el 20 de octubre»; en mi copia de producción, 7+7 pasadas el 13 contra 23 a 34 por sensor los días vecinos). El implementador dejó la interpretación a la vista (`tasks/LOOP_OBJETIVOS.md:616-617`, TEXTO: ««sin el 13 parcial» = se excluye el día 13 entero, en los tres brazos por igual (una exclusión por pasada dependería de qué faltó en cada brazo)»), y el código la aplica: `"2026-10-13"` entero y el mismo `excl` en `T`, `R` y `cob`. Qué cambiaría con la otra lectura: entrarían a P1/P2/M las pasadas del 13 que los tres brazos sí tengan (en producción, 7 por sensor en siete volcanes: a lo más ~14 de 1.658 pasadas VIIRS de la ventana recortada, menos de 1 %), y la cobertura dejaría de comparar iguales si un brazo tuvo más que otro ese día. Nada en el texto sellado exige la lectura parcial. No vi el informe COB H2 que la fila cita (`experiments/_s159/cob/INFORME.md` no existe en este worktree; SIN DATO).

### Afirmación 5: pruebas rojas 5 de 5 por aserción antes y verdes después; mutaciones 4 de 4; probar 31 de 31; suite 2.378 con el árbol quieto

**CONFIRMADO EN PARTE** (gravedad propia 2 por la parte no sostenida).
- Rojas por aserción: CONFIRMADO por mi propia corrida con la prueba **commiteada** sobre una copia del evaluador en `c44709e27` (`git show c44709e27:experiments/_s157_prereg_d25/evaluar_d25.py` → `experiments/_verif_d29_pre/`, borrada al terminar; `D25_EVALUADOR_DIR` apuntando ahí): 5 fallas, las 5 `AssertionError` (`rojo_rerun.xml`, 5 `<failure`; mensajes «falta DIAS_EXCLUIDOS (D-29)» ×2, «falta filtrar_dias (D-29)» ×2, `[]` ×1; `rojo_rerun.txt`). PERO el artefacto del auditor `rojo_d29.txt` **no se produjo con la prueba commiteada**: su aserción de la cuarta prueba dice `assert ({'R','ks','t'} <= set() or {'crudos_n','ks','t'} <= set() or 0 >= 3)` (`rojo_d29.txt:64-74`) y la prueba commiteada no contiene `crudos_n` (grep: 0 en `tests/test_evaluar_d25_dias_d29_s160.py`, 3 en `rojo_d29.txt`). En sustancia la afirmación vale (mi corrida); su evidencia escrita no (V29-02).
- Verdes después: CONFIRMADO, 5 de 5 (`verde_rerun.txt`); y 36 de 36 con `tests/test_evaluar_d25_dias_d29_s160.py tests/test_evaluar_d25_p2_s159.py tests/test_evaluar_d25_placebo_s159.py` (`pruebas_evaluador_rerun.txt`, 184 s), que es el conteo del auditor.
- Mutaciones 4 de 4: CONFIRMADO re-corriendo `mutar_d29.py` tal cual (`mutaciones_auditor_rerun.txt`: 4 ATRAPADA, `RESUMEN: 4 de 4 atrapadas por asercion`, 0 copias `_mut_d29_*` después). Lo que las 4 NO miden: todas se atrapan por pruebas que miran la función aislada (m1, m4), el texto fuente (m2: la cuarta prueba es un guard por regex sobre el nombre del primer argumento, `tests/...:64-66`) o `combinar` con JSON inventado (m3). Ninguna corre `evaluar`. Mis 9 mutaciones (V29-01): 4 atrapadas por el repo, 5 no; las 9 vistas por el instrumento sintético.
- probar 31 de 31: re-corrido, resultado en §8 (`probar_rerun.txt`). `probar_evaluar_d25.py` no tiene ningún caso de D-29 (grep `excl|d29|D-29|EVALUADO|dias`: 0), así que sus OK prueban que el evaluador sigue corriendo con la exclusión puesta en todos los casos (todos usan `--ventana V1`), no que la exclusión haga algo (V29-06).
- Suite 2.378 con el árbol quieto: CONFIRMADO EN PARTE. `suite_d29.txt` termina en `2378 passed, 29 skipped, 1 xfailed, 50 warnings in 340.48s`; `suite_status_antes.txt` y `suite_status_despues.txt` son idénticos (` M experiments/_s157_prereg_d25/evaluar_d25.py`, `?? experiments/_s159/instrumentos/d29/`, `?? tests/test_evaluar_d25_dias_d29_s160.py`). Pero `git status` no distingue dos contenidos de un archivo que ya está en `M`: el instrumento no puede ver una edición de `evaluar_d25.py` durante la corrida (A112). No tengo evidencia de que la hubiera (V29-05, SOSPECHA de instrumento). No re-corrí la suite entera: el diff no toca `pipeline/`, y las pruebas que leen el evaluador son las tres que sí re-corrí.

## 4. Hallazgos

### V29-01
- TÍTULO: Las 5 pruebas de D-29 no ven una exclusión que no llega a `evaluar`: 5 de 9 mutaciones que dejan pasar días excluidos en la tabla, en los crudos, en la cobertura, por hora local o en la cabecera pasan en verde
- ARCHIVO:LÍNEA: `tests/test_evaluar_d25_dias_d29_s160.py:60-66` (guard por regex sobre el nombre del argumento) y `:69-79` (sólo `combinar`); SCRIPT:SALIDA `mutaciones_propias.py` → `mutaciones_propias_salida.txt`, `mutaciones_propias.json`
- QUÉ PASA: una pasada de un día que CMR no sirvió a los brazos entraría a la cobertura, a P1/P2/M, a P4 o al determinismo sin que ninguna prueba lo note, porque las pruebas verifican el conjunto, la función aislada y el texto fuente, no el efecto en `evaluar` (A116, A118). Hoy el código está bien cableado (afirmación 2); el hueco es del candado. Resultado por mutación (prueba del repo / instrumento sintético):

  | mutación | qué rompe | repo (5 pruebas) | sintético |
  |---|---|---|---|
  | p1 `DIAS_EXCLUIDOS` vacío (control positivo) | todo | ATRAPADA (prueba 1) | ve: 60 pasadas más por sensor, cobertura, P4, determinismo, cabecera |
  | p2 `filtrar_dias(R[n], excl)` sin asignar | crudos | **NO ATRAPADA** | ve: `D: le faltan 54 de K` |
  | p3 `filtrar_dias(t, ())` en la tabla | tabla | **NO ATRAPADA** | ve: movidas 16, determinismo 894/884, protegidas sin record |
  | p4 `filtrar_dias(ks, ())` en la cobertura | referencia de cobertura | **NO ATRAPADA** | ve: «faltan 7 a 9 de 112 a 132» ×14 |
  | p5 rama de `set` devuelve la entrada | cobertura | ATRAPADA (prueba 2) | ve |
  | p6 fecha en hora de Chile (UTC-3) | fecha | **NO ATRAPADA** | ve: la pasada 01:30 UTC del 13 entra (836 contra 834) |
  | p7 cabecera de V1 callada | declaración | **NO ATRAPADA** | ve: sin línea `== EVALUADO SIN` |
  | p8 sin el 18 | conjunto | ATRAPADA (prueba 1) | ve: `D: le faltan 52 de K` |
  | p9 `[:7]` en vez de `[:10]` | filtro | ATRAPADA (prueba 2) | ve |

  Sobre p6: con los datos de producción las pasadas de los días excluidos van de las 04 a las 06 UTC, así que en hora de Chile caen el mismo día; la mutación sólo se ve con la pasada sintética de la 01:30 UTC. Es equivalente bajo los datos reales de octubre, pero no bajo cualquier dato: el filtro está bien (UTC, `datetime_utc`), la prueba no lo fija.
- CÓMO SE VE EN EL DASHBOARD: invisible (el evaluador no publica; un veredicto de D25 torcido por cobertura o por pasadas sin datos sí podría cambiar lo que se adopta en producción).
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d29/mutaciones_propias.py --tmp D:\vrp-trabajo\temporales\verif_d29\mut --out experiments/_s159/instrumentos/verificador_d29/mutaciones_propias.json --real experiments/_s159/instrumentos/verificador_d29/sintetico_real_primera_corrida.json` (19 min; sintético, sin volcán ni pasada real; crea y borra `experiments/_verif_d29_mut/`)
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### V29-02
- TÍTULO: `rojo_d29.txt` se produjo con un borrador de la prueba, no con la commiteada
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/d29/rojo_d29.txt:64-74` (aserción con `crudos_n`) contra `tests/test_evaluar_d25_dias_d29_s160.py:66`
- QUÉ PASA: el artefacto que respalda «5 de 5 rojas por aserción» no corresponde al archivo que quedó en el repo. Mi corrida con la prueba commiteada sobre `c44709e27` sí da 5 de 5 `AssertionError` (`rojo_rerun.xml`), así que la afirmación vale; su evidencia escrita no.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -c crudos_n tests/test_evaluar_d25_dias_d29_s160.py experiments/_s159/instrumentos/d29/rojo_d29.txt` → 0 y 3.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2

### V29-03
- TÍTULO: `--repeticion` es el único lector de pasadas sin `filtrar_dias`; hoy benigno porque sólo se consulta por clave
- ARCHIVO:LÍNEA: `experiments/_s157_prereg_d25/evaluar_d25.py:862` (`T_rep = E.tabla(...)` sin filtro) y `:600` (`rp = (T_rep or {}).get(k)` con `k` de `TKD` filtrado)
- QUÉ PASA: la repetición dirigida de los jobs de K y D se carga entera; como sólo se mira para claves que ya pasaron el filtro, una pasada del 17 en la repetición no cuenta. Si alguien iterara `T_rep` (por ejemplo para cobertura de la repetición), entrarían días excluidos. La línea `repetición leída de %s: %d pasadas` (l. 863) ya informa un conteo SIN filtrar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "T_rep" experiments/_s157_prereg_d25/evaluar_d25.py` → l. 574, 600, 859, 862, 863, 872.
- CONFIANZA: CONFIRMADO (por lectura; no lo corrí con `--repeticion`: prohibido sobre datos reales y sin caso sintético)
- GRAVEDAD: 1

### V29-04
- TÍTULO: La declaración «EVALUADO SIN» vive en la línea impresa y en `dias_excluidos`, no en `estado` del JSON por ventana
- ARCHIVO:LÍNEA: `evaluar_d25.py:751` (`res["dias_excluidos"]`), `:753` (print), `:877` (`res["estado"]` sin la declaración), `:999-1001` (`combinar` la re-arma)
- QUÉ PASA: quien lea `v1.json["estado"]` sin pasar por `combinar` ni por stdout no ve la exclusión. Coherente con la fila D-29 (habla de la primera línea del veredicto), pero el JSON es lo que se archiva.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: cualquier caso sintético, `D:\vrp-trabajo\temporales\verif_d29\real\nulo\out.json`: `estado` empieza por `SIN EFECTO`, `dias_excluidos` trae los cinco días.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### V29-05
- TÍTULO: «Árbol quieto» medido con `git status`, que no ve ediciones de un archivo ya en `M`
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/d29/suite_status_antes.txt` y `suite_status_despues.txt`
- QUÉ PASA: el instrumento compara listas de archivos modificados, no contenidos; una edición de `evaluar_d25.py` durante los 5 min 40 s de la suite no cambiaría la salida (A112). No hay indicio de que pasara.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `diff` de los dos archivos → vacío por construcción aunque el archivo `M` cambie.
- CONFIANZA: SOSPECHA (de instrumento, no de hecho)
- GRAVEDAD: 1

### V29-06
- TÍTULO: `probar_evaluar_d25.py` no tiene caso de D-29: sus 31 OK no prueban la exclusión
- ARCHIVO:LÍNEA: `experiments/_s157_prereg_d25/probar_evaluar_d25.py` (grep `excl|d29|D-29|EVALUADO|dias` → 0 líneas)
- QUÉ PASA: la prueba de punta a punta del evaluador corre todos sus casos con `--ventana V1`, así que la exclusión está activa en todos, pero ningún caso toca sólo días excluidos ni mira `dias_excluidos`, la cabecera o la cobertura por esos días. `cobertura_sintetica.py` de esta carpeta es ese caso y queda como instrumento.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "excl\|d29\|D-29\|EVALUADO\|dias" experiments/_s157_prereg_d25/probar_evaluar_d25.py`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

Duplicados con otros auditores: ninguno que yo sepa (no leí el informe del auditor).

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. `combinar` usa `e.startswith(("INVALIDO", "NO CUMPLE", "INDECIDIBLE", "PENDIENTE"))` sobre `res["estado"]` (`evaluar_d25.py:981`). Si alguna vez la declaración «EVALUADO SIN» se antepusiera al `estado` por ventana (lo que V29-04 podría sugerir como «arreglo»), ese `startswith` dejaría de reconocer los estados malos y un INDECIDIBLE pasaría por bueno. Confianza CONFIRMADO por lectura; aviso para quien toque V29-04.
- S-2. El `estado` de los casos sintéticos sale `SIN EFECTO | ATENCIÓN: D25 no cambió ninguna magnitud (...)` con D = K más huella: esperado y fuera de mi eje.

## 6. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- `DIAS_EXCLUIDOS` y su lectura por `--ventana`: lectura `evaluar_d25.py:73, 750`; vara: fila D-29 (`tasks/LOOP_OBJETIVOS.md:534`).
- Cableado del filtro a `T`, `R`, `cob` y a todos los derivados: lectura l. 775, 779, 780-781, 785, 791, 794-795, 864-872, 887, 918, y `evaluar_fk.py:190, 212, 342, 361`; `grep -n "json.load\|read_text\|open(" experiments/_s157_prereg_d25/evaluar_d25.py`; vara: «en los tres brazos por igual y en la cobertura» (fila D-29). Medido con `cobertura_sintetica.py` (9 casos, control positivo p1).
- Clave `vol|bucket|YYYY-MM-DD HH:MM` y fecha UTC: `experiments/_s146_ab_sin_test1/evaluar.py:110`, `evaluar_d25.py:358, 377, 382`, `evaluar_fk.py:192`; producción: `datetime_utc` ejemplo `2026-10-21 08:05`.
- Inercia del 19 y el 20: `evaluar_d25.py:60, 352, 376, 381`; `PREREGISTRO.md:104`.
- Cabecera de V1 primera línea de stdout: 9 casos, `cabecera_linea_idx [0]`; `D:\vrp-trabajo\temporales\verif_d29\real_extra\d_sin_18.txt`.
- Veredicto combinado: `evaluar_d25.py:999-1002` y prueba 5 (`verde_rerun.txt`).
- Rojo con la prueba commiteada sobre `c44709e27`: `rojo_rerun.txt`, `rojo_rerun.xml` (5 `AssertionError`). Verde sobre `6f43ec624`: `verde_rerun.txt` (5), `pruebas_evaluador_rerun.txt` (36).
- Mutaciones del auditor re-corridas: `mutaciones_auditor_rerun.txt` (4 de 4, 0 copias sueltas).
- Mutaciones propias: `mutaciones_propias_salida.txt`, `mutaciones_propias.json` (9 vistas, 0 caídas, 0 copias sueltas); la corrida caída se conserva en `mutaciones_propias_salida_1_instrumento_caido.txt` y `mutaciones_propias_1_instrumento_caido.json`.
- Reproducibilidad del sintético: `sintetico_real_primera_corrida.json` = `sintetico_real.json` (0 diferencias en 7 casos).
- `probar_evaluar_d25.py` re-corrido sobre `6f43ec624` con tmp en `D:\vrp-trabajo\temporales\verif_d29\probar` (30 min 22 s): `RESUMEN: 31 de 31 casos OK` (`probar_rerun.txt`); el caso `nulo` imprime la cabecera `== EVALUADO SIN ...` (grep en `nulo.txt`: 1), o sea que todos sus casos corren con la exclusión puesta, como dice V29-06.
- Conteo de producción en los días excluidos (reproducible): `python -I -` con `json` sobre `data/mirova_equivalent/<vol>.json` de los 7 volcanes, filtrando `2026-10-11 <= datetime_utc[:10] <= 2026-10-18` y `"VIIRS" in sensor`; da 7+7 el 13, 27+27 el 17, 26+26 el 18, horas 04 a 06 UTC.
- Disco: C: 13 GB y D: 8,8 GB libres al empezar; ninguno bajó de 3 GB.

## 7. SIN DATO

- V2 con datos: no corrido (no excluye nada; sólo lectura).
- `--repeticion` y `--ruido-de` con datos: sólo lectura (V29-03).
- El informe COB H2 que cita la fila D-29 (`experiments/_s159/cob/INFORME.md`): no existe en este worktree.
- La suite entera sobre `6f43ec624`: no re-corrida (ver afirmación 5).
- Qué le faltó a cada brazo el 13 en el A/B real: prohibido mirar; la lectura «13 entero» no depende de eso.

## 8. FUERA DE ALCANCE y cierre

- Fuera de alcance: el resultado del A/B de D25 (no leído), D-42 (calibración de P2), D-35 (brazo de sensibilidad del 17 al 19 por LANCE), el resto del diff (`verificador_d34`).
- Llamadas a la API de GitHub: 3 (dos `gh api -i` para la hora del servidor al abrir y al sellar `caminos.md`, una al cerrar).
- `caminos.md` sellado antes de abrir ningún archivo citado: sha256 del archivo final `86ce35f20c8f4c712c80cfb9f5e3c83781b50d9e09a784eedd2c3ce7e3388e51`, hora del servidor Thu, 22 Oct 2026 06:37:17 GMT. No se editó después.
- Resultado de `probar_rerun.txt` y hora del servidor al cerrar:
- `probar_evaluar_d25.py` re-corrido sobre `6f43ec624` con tmp en `D:\vrp-trabajo\temporales\verif_d29\probar` (30 min 22 s): `RESUMEN: 31 de 31 casos OK` (`probar_rerun.txt`); el caso `nulo` imprime la cabecera `== EVALUADO SIN ...` (grep en `nulo.txt`: 1), o sea que todos sus casos corren con la exclusión puesta, como dice V29-06.
- Hora del servidor al cerrar: Thu, 22 Oct 2026 07:22:15 GMT. Árbol: `git status --porcelain` sólo `?? experiments/_s159/instrumentos/verificador_d29/`; copias de mutación en `experiments/`: 0.
