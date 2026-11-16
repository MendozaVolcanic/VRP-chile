# F3 S175: decisiones y cierres S160 a S174

## 1. Encabezado

- **Fecha y hora del servidor**: inicio 2026-11-07 08:47:48 GMT, cierre del informe 2026-11-07 09:04 GMT (header `Date` de `api.github.com`).
- **Commit medido**: base `752d348bc67190e53b610989877e2405d238a1bc` salvo donde se nombra otro. Bitácora y bloques de arranque: `loop/activo` en `06de6876a` (fuera de main); la entrada del merge de #945 se leyó en `395af8034` (fuera de main).
- **Modelo y esfuerzo**: Claude Opus 5.5 (`claude-opus-5-5`); esfuerzo real declarado por el sistema: `reasoning_effort` 15 (se pidió high; corrí en bajo).
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f3\`. Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\f3\` (copias de la bitácora y de los bloques S160 a S175 de `06de6876a`).
- **Llamadas a la API de GitHub**: 2 (PR #895 y #896). Búsquedas en transcripts de sesiones: 2.
- **Qué NO miré** (mi silencio no es «todo bien»):
  - Las decisiones de investigación cuyo efecto vive sólo dentro de evaluadores sellados (D-28 a D-46 de D25, adendas de V750-B, V375-E, MOD-D fases 3 y 4, A/B diurno W1 a W6, ROI B4): leí que existan y que los tags apunten donde dice la bitácora, no rehíce sus números.
  - Mirova-v1 (D-39, D-40, D-41): otro repositorio.
  - El contenido de cada uno de los 132 cierres que el censo lista en la base: los fecho (todos anteriores a S160 fuera de CLAUDE.md) pero no verifiqué uno por uno los anteriores a S160.
  - `HYPOTHESIS_LOG.md`, `META_RULES_S80.md`, `README.md` y la ficha SDA más allá de contar menciones.
  - Las 101 frases únicas de Nicolás del inventario: verifiqué contra código las que cambian producción, el tablero o un instrumento sellado (lista en §4); las de operación de sesiones (archivar, pausar, abrir sesiones, MATLAB, correo a Coppola) no tienen efecto en código y no las audité.
  - El tablero sólo en `index.html` publicado (no diario ni mosaico en vivo; sí su código).

## 2. En una pantalla

1. Las dos líneas base rojas se reencuentran con un instrumento nuevo (`rebajas_vs_datos.py`); el censo S145, que el plan da como piso, **no ve ninguna de las dos** (misma salida, 132 cierres, en `77e54e8e0^` y en la base).
2. Las decisiones que cambian producción desde S160 están en el código como se aprobaron: vía MODIS encendida (98 de 98 records MODIS desde el corte), congelamiento de `pipeline/` respetado, flags MxD03 apagados, exención de cirrus en las tres vistas, sombras fuera de Pages, paso 209, regla MOD-D sellada en main, 9 tags donde dice la bitácora.
3. **La rebaja más grande del período no llegó a `SINTOMAS.md`** (sin cambios desde el 2026-10-25): sigue diciendo que MODIS de producción es K y usa `_interp_geo`, y conserva la nota A85 que #950 corrigió sólo en `CLAUDE.md` (251, 252, gravedad 3).
4. Dos decisiones aprobadas no están en main: la 3 de S174 (`sin_grilla`/`sin_mxd03` como K con aviso; el lector los excluye y pone rojo) y «Sí, arréglalos» de los falsos verdes de cenit (vive en #952, fuera de main) (253, 254).
5. Además: la cola §5 de decisiones tiene cinco filas viejas (D-1, D-19, D-23, D-37, D-39), la memoria del agente conserva «MxD03 se baja y se ignora», y hay decisiones dentro de evaluadores sellados tomadas por la coordinadora sin frase de Nicolás, declaradas.

## 3. Línea base roja (hecha primero)

Instrumento: `rebajas_vs_datos.py` (en CARPETA), salida cruda `salida_rebajas_vs_datos.txt` y `rebajas_vs_datos_<commit>.json`.

**Las dos preguntas.** (1) Si la propagación de estas rebajas estuviera rota, ¿lo vería? Sí, pero sólo para los cuatro patrones que codifica (frontera de régimen escrita, nota A85 en `CLAUDE.md`, la misma nota en los demás rectores, MODIS de producción descrito como K o con `_interp_geo`); es un piso. (2) Si el instrumento estuviera muerto, ¿se vería distinto? Sí: cada chequeo informa su denominador (líneas leídas, records contados) y con 0 da SIN DATO. Control positivo: el conteo de records MODIS de ene-jun 2026 de los 11 Tier A da **4.286**, el número que `CLAUDE.md` atribuye a `f36a8fb98` (la primera corrida dio 3.884 porque escribí mal `NevadosDeChillan`: el control lo atrapó). Control negativo: `MODK` da SIN DATO en `d516b9d8c`, antes del encendido (0 records de la vía).

| commit | F281 | A85 (CLAUDE.md) | A85b (otros rectores) | MODK |
|---|---|---|---|---|
| `77e54e8e0^` | LIMPIA | **DESFASADA** (rojo 1 reencontrado) | DESFASADA | DESFASADA (74 de 74 de la vía) |
| `d516b9d8c` | **DESFASADA** (`docs/SINTOMAS.md:9`, rojo 2 reencontrado) | LIMPIA | DESFASADA | SIN DATO (0 de 0) |
| `752d348bc` | LIMPIA | LIMPIA | **DESFASADA** | **DESFASADA** (98 de 98) |

Ventana de datos: records de los 11 Tier A en cada commit; `datetime_utc` de 2025-02-15 01:40 a 2026-11-07 01:15 en la base.

Censo S145 (`censo_en_commit.py`, importa `tipos_de_cierre` y `respaldos_citados` del script original, no los copia; salidas `salida_censo_*.txt`, `censo_*.json`): 132 cierres y 74 sin respaldo en `77e54e8e0^` y también en la base; en ninguno de los tres commits lista la línea «C0 antes del» de `SINTOMAS.md` ni la línea A85 de `CLAUDE.md`. Ver hallazgo 257.

## 4. Inventario (cobertura auditable)

Comando: `python inventario.py` (en CARPETA) sobre `06de6876a`: líneas de §5 y §6 de `tasks/LOOP_OBJETIVOS.md` (entradas de S160 en adelante) y de `BLOQUE_ARRANQUE_S161.md` a `S175.md` que nombran a Nicolás junto a una marca de decisión. Salida `inventario.json` (188 líneas) e `inventario_citas.md` (101 frases únicas). Control: encuentra D-45 y la decisión de MODIS del 2026-10-31 (los dos True). Piso: una decisión escrita sin nombrar a Nicolás no sale.

Veredicto por ítem de lo verificado contra código (los números de hallazgo remiten a §5):

| Decisión o cierre | Frase y dónde | Veredicto |
|---|---|---|
| MODIS a la vía «código MIROVA» (#934) | «Sí, sellar y encender», bitácora 2026-11-02 17:18 | verificado (`mirova_equivalent.yaml:38`; 98 de 98 MODIS desde 2026-11-02T18 con `via_codigo_mirova` True, 0 caen a K) |
| Regla de reversión MOD-D sellada en main | misma frase | verificado (tag `s173-regla-modd-sellada` = base); salvedad 263 |
| D1 a D7 de la regla; 208 y 209 | «de1 a d7 si, en el resto hace lo que recomiendes» | verificado (paso «Revisar errores de MODIS en el log», `nrt.yml` l. 372 a 385) |
| Congelar `pipeline/` durante la sombra | «Sí, congelar», 2026-10-30 03:18 | verificado: 10 commits a `pipeline/` desde entonces, todos YAML de perfiles o `grillas_mirova.yaml`, ninguno toca código de vías |
| #920, tres flags MxD03 apagados | «Sí, los tres apagados» | verificado (`mirova_equivalent.yaml:151-153` false); salvedad 260 |
| Sombra V375-E: «Cercano decide» | bitácora 2026-10-30 00:20 | verificado fuera de main (tag `s172-v375e-lector-resellado` = `fc3912cb2`, `leer_posicion_v375e.py` l. 80) |
| Lector V375-E re-sellado | «Sí, sellar» | verificado (tag en `fc3912cb2`) |
| #926 sombra una vez al día 15:00 UTC | «Sí, mergea #926» | verificado (`sombra-codigo-mirova.yml` cron `0 15 * * *`; último dato 2026-11-06 21:01 UTC) |
| #935 decisión 4 (sombras fuera de Pages) | «Sí, mergear #935» | verificado (`pages-deploy.yml` l. 29 a 31 y `rm -rf` de las tres carpetas) |
| #935 decisión 3 (marca de vecino a 4 km) | ídem | en parte (262) |
| #944 vía exenta de cirrus y difuso | «Sí, merge #944» | verificado en index, diario y mosaico; las tres cargan `cambio_detector.js` |
| #945: «14 noches», «Ventana fija, una vuelta», «Sí, sexta vuelta» | bitácora 2026-11-06; merge «Sí, mergea el 945» | verificado (`evaluar_v750a.py` l. 110 a 127, 430 a 436, 771); salvedad 258 |
| 8 decisiones del bloque S174 | «Sí, a todo», 2026-11-05 20:23 | 1, 4, 5 y 7 verificadas; **3 no implementada (253)**; 2 y 6 sin despacho que mirar (SIN DATO); 8 corrida (bitácora 13:11) |
| Falsos verdes de cenit | «Sí, arréglalos», 2026-11-06 13:36 | **no en main** (254) |
| D-37 #892 y aviso de cese de Suomi NPP | (merge del 2026-10-22) | verificado en el tablero publicado; fila de la cola vieja (255) |
| D-38 patrón de la alarma de plataforma | PENDIENTE | verificado: el código conserva lo pedido (comentar mientras dure, `vigilar_plataformas.py` l. 233), sin implementación sin frase |
| A/B diurno (#813) | decide Nicolás | verificado: `enable_daytime_viirs: false` (l. 498), sin adopción sin frase |
| D25 NO SE ADOPTA (S162) | D-48, delegación general | verificado que no hay flag de D25 encendido; salvedad 259 |
| D35 MxD03 CUMPLE SIN DAÑO; rebaja S172 | | catálogo marcado (S172); memoria no (256); `SINTOMAS.md` no (251) |
| #950: D21, GAP #A, A85, A100 | «Sí, mergea ambos» | verificado contra código y datos (§6); propagación de A85 incompleta (252) |
| D-39 R13 (#895) | sin frase en la bitácora | SIN EVIDENCIA de frase (261) |
| Tags defensivos y de sello (9) | | verificados (`salida_tags.txt`) |

## 5. Hallazgos

### 251. `SINTOMAS.md` describe el MODIS de producción como K y con `_interp_geo` cinco días después del encendido de la vía
- ARCHIVO:LÍNEA: `docs/SINTOMAS.md:25` y `docs/SINTOMAS.md:127` en `752d348bc` (último cambio del archivo: `b498cffe8`, 2026-10-25).
- QUÉ PASA: desde el 2026-11-02 cada pasada MODIS de los 11 volcanes se detecta y se ubica con la vía «código MIROVA», que lee la posición de 1 km del MxD03; el documento que se lee «antes de proponer una palanca» sigue diciendo, en su «Régimen vigente» sin marca S172, «el detector K está en producción desde #850» con banda 22 en MODIS, y en l. 127 «producción usa `_interp_geo` hasta que MxD03 entre con el paquete MODIS». Una sesión que estratifique por régimen (A104) con ese texto mezcla K y la vía en MODIS. El catálogo (D35, marca S172) y `MISSION.md` sí tienen la marca; `SINTOMAS.md` tiene 0 menciones de la vía. Su propio encabezado dice «Se actualiza en el mismo PR en que cambia una divergencia (A113)».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python rebajas_vs_datos.py 752d348bc` (bloque MODK: 98 de 98 records MODIS desde 2026-11-02T18 con la vía; líneas 25 y 127). Control: en `d516b9d8c` da SIN DATO.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (tuerce la elección de palancas y la estratificación de cualquier medición MODIS posterior al 2026-11-02; no toca una alerta directamente).

### 252. La nota A85 que #950 corrigió en `CLAUDE.md` sigue vigente en `SINTOMAS.md`
- ARCHIVO:LÍNEA: `docs/SINTOMAS.md:195-197` en `752d348bc`.
- QUÉ PASA: la nota S153 decía que los records MODIS de enero a junio de 2026 quedaron escritos con los gates intra-radio y que no se reprocesaron; #883 los reprocesó (4.286 de 4.286 con `processed_utc` de 2026-10) y #950 lo dejó OBSOLETA sólo en la línea A85 de `CLAUDE.md`. `SINTOMAS.md` la sigue dando como frontera de régimen a no cruzar, sin marca. Es el mismo defecto de la línea base roja 1, vivo en otro documento rector: la rebaja no se propagó por `grep` a sus hijos (A113).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python rebajas_vs_datos.py 752d348bc` (bloque A85b: DESFASADA, `docs/SINTOMAS.md:196`; `processed_utc_por_mes` = `{"2026-10": 4286}`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (hace que una sesión parta en dos una ventana MODIS de ene-jun 2026 que es de un solo régimen, o descarte esos meses).

### 253. Decisión 3 de S174 aprobada y no implementada: el lector de la retrospectiva excluye y pone en rojo los records `sin_grilla`/`sin_mxd03` en vez de tratarlos como K con aviso
- ARCHIVO:LÍNEA: `experiments/_s172_retro_paquete/leer_retro.py:270-271` (estado `via_sin_marca:<valor>`), `:354` (sólo `ok` es evaluable), `:544` (C-via ROJO si hay alguno fuera de R25), en `752d348bc`.
- QUÉ PASA: cuando la vía no puede correr en un gránulo (falta la grilla o el MxD03) producción escribe K y lo marca; Nicolás aprobó («Sí, a todo», bitácora `06de6876a` l. 654 y 657: «se tratan como K y se listan como aviso. NO IMPLEMENTADO todavía») que la retrospectiva los lea como K con aviso. En la base el lector hace lo contrario: los saca de la evaluación y el control C-via falla. Ningún commit posterior a #946 (`f36a8fb98`) toca el lector salvo #945, que es de otro lector. Falla ruidosa, no silenciosa.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:experiments/_s172_retro_paquete/leer_retro.py | sed -n 260,275p` y `sed -n 530,545p`; `git grep -n -E "sin_grilla|sin_mxd03" 752d348bc -- experiments/_s172_retro_paquete` (sólo `controles_via.py:50`, un docstring). Sustrato hoy: 0 records MODIS de producción desde el corte caen a K (`salida_via_modis.txt`), así que hoy no muerde.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 254. «Sí, arréglalos» (falsos verdes de los controles de cenit) no está en main; la base sigue publicando SIN SUSTRATO como OK
- ARCHIVO:LÍNEA: `experiments/_s172_retro_paquete/leer_retro.py:1227` («OK (sin sustrato: la curva no se lee)») y `:1019` (una excepción de la razón doble se rotula SIN SUSTRATO), en `752d348bc`.
- QUÉ PASA: la decisión (bitácora l. 575, 2026-11-06 13:36) pedía que SIN SUSTRATO no cuente como OK, que un insumo vacío sea ROJO y que una excepción sea ERROR INTERNO. El arreglo vive en el PR #952 (rama `claude/s174-cenit-falsos-verdes`, `dd17fd97d` no es ancestro de la base; punta remota `adc1c06e4`), **fuera de main**, en su segunda vuelta según `395af8034`. Si la retrospectiva (D3) se despacha o se lee desde main antes de #952, sus controles de cenit dan verde sin haber leído nada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:experiments/_s172_retro_paquete/leer_retro.py | sed -n 1225,1228p`; `git merge-base --is-ancestor dd17fd97d 752d348bc` (sale 1).
- CONFIANZA: CONFIRMADO (que no está en main); SOSPECHA (que se lea antes de #952: SIN DATO del calendario de D3).
- GRAVEDAD: 3 (la retrospectiva es evidencia de una decisión de adopción por sensor).

### 255. La cola de decisiones §5 de `loop/activo` tiene cinco filas que ya no dicen la verdad
- ARCHIVO:LÍNEA: `tasks/LOOP_OBJETIVOS.md` en `06de6876a` (fuera de main): l. 528 (D-37 «PENDIENTE, con plazo 2026-11-02»), l. 526 (D-39 «PENDIENTE»), l. 540 (D-23 «EN CURSO», con 3.231 records), l. 545 (D-1 «pendiente»), l. 543 (D-19 sin estado).
- QUÉ PASA: es la tabla donde Nicolás contesta. #892 está en main desde el 2026-10-22 (`3489e55c3`); D-39 se cerró el 2026-10-27 (misma bitácora l. 2534); el reproceso de D-23 está hecho (4.286 records MODIS de ene-jun 2026, todos con `processed_utc` de 2026-10, no 3.231); la conectiva `max` de D-1 entró con K (`mirova_equivalent.yaml:290`, `enable_tests_23_prose_branch: true`); D-19 quedó en D35 (CUMPLE SIN DAÑO). Una sesión que lea la cola le vuelve a preguntar a Nicolás lo ya decidido, o cree pendiente lo hecho.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 06de6876a:tasks/LOOP_OBJETIVOS.md | sed -n 516,570p`; contraste `git log --oneline 752d348bc --grep=892` y `python rebajas_vs_datos.py 752d348bc` (A85).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 256. La memoria del agente sigue diciendo que el MxD03 «se baja y se ignora»
- ARCHIVO:LÍNEA: `C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\project_modis_geo_interp_offset.md` (descripción y «How to apply», `modified: 2026-10-15`), enlazada desde `MEMORY.md` («Referencias estables»: «MxD03 se baja y se ignora; probe pendiente»).
- QUÉ PASA: desde el 2026-11-02 la posición de MODIS de producción viene del MxD03 (`pipeline/mirova_v750_codigo.py::leer_geo_mxd03`, l. 842 en `752d348bc`), y el A/B de D35 dio CUMPLE SIN DAÑO en S162. La memoria, que se carga en cada sesión, no tiene ninguna de las dos rebajas. A113 incluye la memoria (tarea de F3).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "se ignora" <ruta de arriba>`; `git show 752d348bc:pipeline/mirova_v750_codigo.py | sed -n 842,850p`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (una auditoría espacial MODIS que parta de la memoria mide la posición equivocada, A61).

### 257. El censo S145, piso que el plan da para este frente, no ve las dos líneas base rojas ni los cierres de S160 en adelante
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `experiments/_s145_censo_cierres/censo.py` (PATRONES l. 54 a 66), corrido sin escribir en su carpeta con `censo_en_commit.py`; salidas `salida_censo_77e54e8e0_padre.txt`, `salida_censo_752d348bc.txt`, `salida_censo_d516b9d8c.txt`, `salida_cierres_desde_s160.txt`.
- QUÉ PASA: busca palabras de cierre; un desfase entre un documento y los datos no es una palabra, así que da 132 cierres y 74 sin respaldo antes y después de #950. Tampoco atrapa los cierres nuevos del período: «NO SE ADOPTA» (D25, S162) no calza con `\bNO ADOPTAR\b` y «CUMPLE SIN DAÑO» (D35) no tiene patrón; fechado con `git blame`, 0 de sus 132 cierres fuera de `CLAUDE.md`/historia es posterior al 2026-10-21. Una auditoría que lo tome como vara declara limpio el período.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python censo_en_commit.py 77e54e8e0^` y `python censo_en_commit.py 752d348bc` (mismos n); `python cierres_desde_s160.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 258. Decisiones del lector sellado de V750-A tomadas por la coordinadora sin frase de Nicolás (declaradas)
- ARCHIVO:LÍNEA: bitácora `06de6876a` l. 605 («Defaults de la coordinadora, sin elección de Nicolás: umbral 5 por semana y exigencia sólo en conjunto y cambiados») y l. 643 («sin frase explícita de Nicolás sobre ese punto», `--sha-desde` obligatorio); en el código `experiments/_s162_v750a/evaluar_v750a.py:117-118` (`NOCHES_MIN_SEMANA = 5`, `SEMANA_EXIGE_SIN_CAMBIO = False`) en `752d348bc`.
- QUÉ PASA: el veredicto CUMPLE de la sombra de V750-A es la compuerta para llevar la vía a VIIRS 750 de producción; tres de sus parámetros los fijó la coordinadora y se le informaron a Nicolás, sin su frase (guía §6: el sello se registra con la frase del dueño). El «no deciden» de la exigencia por volcán se corrigió después con frase («Sí, sexta vuelta», `NOCHES_MIN_SIN_CAMBIO = 14`, l. 126); los otros dos siguen como defaults. El merge de #945 sí tiene frase («Sí, mergea el 945», `395af8034`), que cubre el código pero no nombra esos puntos.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:experiments/_s162_v750a/evaluar_v750a.py | sed -n 108,128p`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 259. D25 «NO SE ADOPTA» se cerró bajo una delegación general, no con una frase sobre D25
- ARCHIVO:LÍNEA: `docs/MIROVA_DIVERGENCES.md` marca S162 de D25 (l. 2863 a 2865 en `752d348bc`, TEXTO): «decisión de Nicolás: «sobre las decisiones mías haz lo que tú recomiendes», sobre la recomendación de no adoptar»; la frase es D-48 (bitácora l. 3682), dada sobre «las 14» del programa.
- QUÉ PASA: un cierre que apaga una palanca entera («la palanca deja de ser la media de los vecinos del paper») descansa en una autorización amplia. No es una aprobación reenviada entre sesiones, pero tampoco es la frase del dueño sobre ese sello. En código no hay efecto: ningún flag de D25 encendido en producción.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:docs/MIROVA_DIVERGENCES.md | sed -n 2861,2866p`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 260. La A45 de #920 («Sí, los tres apagados») quedó en el repositorio sólo de segunda mano
- ARCHIVO:LÍNEA: commit `4164d4547` («Sí explícito de Nicolás en el chat de esta sesión (A45)», sin la frase); bitácora `06de6876a` l. 2468 («Según la sesión: A45 dado por Nicolás en su chat»).
- QUÉ PASA: #920 toca `pipeline/` de producción. La frase existe de primera mano en el transcript de la sesión `local_f2be5b7f` («MxD03 en MODIS: tres flags apagados según el plan»), encontrada con la búsqueda de transcripts; en git no está escrita donde se dijo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log -1 --format=%B 4164d4547`; búsqueda de transcripts «Sí, los tres apagados».
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 261. #895 (R13 del sync de la referencia) entró a main sin frase de Nicolás en la bitácora mientras D-39, que lo incluía, decía «sólo con el sí de Nicolás»
- ARCHIVO:LÍNEA: `.github/workflows/sync-mirova-csv.yml:90-102` en `752d348bc` (R13); squash `6547f5315`, 2026-10-22 11:29:18 UTC; fila D-39 de la cola (`06de6876a` l. 526).
- QUÉ PASA: la API dice `merged_by` MendozaVolcanic, la misma cuenta con que mergean las sesiones; la bitácora no trae frase. Un transcript de la auditoría S160 dice «hazla tú después de que Nicolás lo mergee», lo que sugiere que lo mergeó Nicolás desde la web. SIN EVIDENCIA de frase.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `gh api repos/MendozaVolcanic/VRP-chile/pulls/895 --jq .merged_by.login,.merged_at`; `grep -n "895" tasks/LOOP_OBJETIVOS.md` en `06de6876a`.
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 1.

### 262. Decisión 3 de la sombra de los 34 implementada con otro radio que el aprobado
- ARCHIVO:LÍNEA: squash `438a010ab` (#935); bitácora `06de6876a` l. 959 («marcar en la lectura las pasadas con píxeles a menos de 4 km del vecino») contra l. 934 a 937 (radio = max(4 km, `inner_radius_km` del vecino), «El arreglo no pasó por otro verificador»).
- QUÉ PASA: el cambio es razonable (el lacolito de Cordón Caulle a ~7 km en la grilla de Antillanca) y Nicolás mergeó la punta final («Sí, mergear #935»), pero no hay constancia de que se le presentara el cambio de la regla aprobada. En parte.
- CÓMO SE VE EN EL DASHBOARD: invisible (sombra).
- CÓMO REPRODUCIRLO: `git show --format=%B 438a010ab | head -30`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 263. El texto sellado de la regla MOD-D cambió en una línea al sellarse y el archivo se sigue llamando BORRADOR
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`; `sello_regla_modd.py`, `salida_sello_regla_modd.txt`.
- QUÉ PASA: la cabecera dice que el sha256 LF del texto sellado «antes de esta cabecera» es `7f300a14` (ronda 5, `3a3b5e495`, control: lo reproduzco) y que «el texto no se cambia»; además de la cabecera, el mismo commit editó la línea «Falta la frase de sello de Nicolás» a «… (dada, ver la cabecera)», así que la base sin cabecera ya no da `7f300a14`. Lo sellado por regla no cambió (el cambio es una nota); el tag `s173-regla-modd-sellada` es idéntico a la base.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python sello_regla_modd.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 264. #951 se mergeó con CI rojo (rama de V750, fuera de main)
- ARCHIVO:LÍNEA: bitácora `06de6876a` l. 637 («CI con 1 falla ajena al cambio: `test_csv_max_age_under_48h`»); squash `c8152580b` en `origin/claude/s162-viirs750-2-918174`.
- QUÉ PASA: A39 pide checks verdes para mergear; la falla se explicó como dato viejo de la rama, y la frase «Sí, mergea ambos» la dio Nicolás. Es la rama donde vive el medidor del sello de V750-A.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log -1 --format='%h %D %s' c8152580b`.
- CONFIANZA: CONFIRMADO (por la bitácora; el run no lo miré).
- GRAVEDAD: 1.

### 265. El índice de memoria tiene el estado de S174 desfasado
- ARCHIVO:LÍNEA: `MEMORY.md` de la memoria del proyecto, línea «Estado vivo: S174 … #950/#951 esperan frase; #945 en R2»; `project_s174_estado.md` (`modified: 2026-11-05T22:15`).
- QUÉ PASA: #950 está en main (`77e54e8e0`), #951 en la rama de V750 (`c8152580b`) y #945 en main desde el 2026-11-07 03:31 UTC (`235ba7918`).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --oneline 752d348bc --grep="#945\|#950"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 6. VERIFICADO LIMPIO

Cada uno con su vara. Los conteos son de los 11 Tier A en el commit nombrado.

- **Cierres del CLAUDE.md corto de S174 (#950) contra datos** (`cierres_claude_datos.py`, salida `salida_cierres_claude_datos.txt`). Vara: los records. Control: en `f36a8fb98` reproduce los 73.620 records y los 74 de 74 MODIS de la vía que cita `CLAUDE.md`. En la base: 73.710 records (2025-02-15 01:40 a 2026-11-07 01:15), 0 con `final_hotspot_source` test1/test1_roi, 98 de 98 MODIS desde 2026-11-02T18 de la vía, 0 sin marca de régimen (68.072 `_s154_reproc_k_historico`, 5.638 `mirova_equivalent`). Pregunta 1: un record test1 aparecería en la tabla de valores (cuenta por valor); no hay control de un commit con test1 (SIN DATO de ese control).
- **D21**: `pipeline/mirova_v750_codigo.py:831-839` llama `merge_mir_bands(b21, b22, True)` siempre. Vara: el código.
- **GAP #A**: `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` se lee en `pipeline/profile.py:592` con default False y `mirova_equivalent.yaml` no trae la clave; se importa en los tres procesadores (`process_modis.py:161`, `process_viirs.py:150`, `process_viirs_mod.py:122`).
- **Vía MODIS en producción** (`via_modis.py`, `salida_via_modis.txt`): 98 records MODIS desde el corte, todos de la vía; antes del corte 14.833 sin la clave (K) y 22 de la vía (pasadas del 2 de noviembre reescritas por el NRT posterior al merge). El tablero publicado (`index.html`, leído en el navegador el 2026-11-07) muestra el aviso de la vía con fecha desde los datos (`viaModisDesde` 2026-11-02T01:15Z), el de K desde el 15 feb 2025 y el del cese de Suomi NPP.
- **Congelamiento de `pipeline/`** (vara: §12.6 citado en la bitácora l. 1641 a 1645): `git log --since=2026-10-30T03:00Z 752d348bc -- pipeline/` da 10 commits, todos perfiles YAML o `grillas_mirova.yaml` (ROI B4, sombra de los 34, guardia K, encendido); ninguno toca código de las vías.
- **Flags MxD03 apagados** (#920): `mirova_equivalent.yaml:151-153`.
- **Exención de cirrus y difuso de la vía** (#944): `index.html:1337,1356`, `diario.html:378,389`, `mosaico.html:363,374`; las tres cargan `cambio_detector.js` (l. 12, 10, 24), sin lo cual la exención se apagaría.
- **Sombras fuera de Pages** (#935, decisión 4): `pages-deploy.yml` l. 29 a 31 (disparo) y `rm -rf` de las tres carpetas antes del artefacto.
- **Paso 209**: `nrt.yml` l. 372 a 385.
- **Regla MOD-D**: sellada en main con la frase; tag igual a la base (`salida_sello_regla_modd.txt`).
- **Tags** (`salida_tags.txt`): `s170-modd-f4-candado-n01`, `s173-regla-modd-sellada`, `s173-prereg-retro-sellado`, `pre-s173-adopcion-modd`, `pre-s172-retro-paquete`, `s172-v375e-lector-resellado`, `pre-s165-mxd03-modis`, `pre-s168-encender-sombra` apuntan al commit que dice la bitácora.
- **#945**: las tres decisiones están en `evaluar_v750a.py` (l. 110, 111, 126, 127, 436); merge con frase en `395af8034`.
- **Decisiones 4 y 5 de S174**: `leer_retro.py:586-587` (Tier A sin F26 en K, rojo) y l. 518 a 521 (`--separa-v750` sin valor por defecto, única candidata PROVISIONAL).
- **D-38 y el A/B diurno, pendientes**: el código no los implementó sin frase (`vigilar_plataformas.py:233`, `enable_daytime_viirs: false`).
- **Frontera de régimen en documentos** (F281) y **A85 en `CLAUDE.md`**: limpias en la base (las marcas S160 y #950 están).
- **R13 en el sync** (#895): implementado (`sync-mirova-csv.yml:90-102`); su aprobación es el hallazgo 261.
- **Cese de Suomi NPP en `MAPA_WORKSPACE.md`** y cambio de detector MODIS: la ficha de VRP Chile lo dice (l. 152, edición 2026-11-03).

## 7. SEGUIMIENTOS (fuera de mi eje, sin perseguir)

- `scripts/banco_paridad.py` y el auto-audit leen `mirova_v1_snapshot/registro_vrp_consolidado.csv`, que en la base no tiene filas después del 2026-11-02 (lo avisó F2 en las notas compartidas; no lo medí yo). SOSPECHA heredada.
- La instantánea compartida `C:\Users\nmend\vrp-temporales\s175_audit\main\` no trae `data/` (no pude usarla; leí los datos con `git show` del commit). Para frentes que lean datos desde ahí: SIN DATO.
- Bitácora l. 1043 («sigue atrapando cualquier excepción de la vía sin dejar el job rojo (pipeline/ congelado…)»): para MODIS lo cubre el paso 209; para la vía de VIIRS en las sombras no lo miré. SOSPECHA, confianza baja.
- `DATOS_K_DESDE_UTC` del tablero dice que todo desde el 15 feb 2025 es K; para MODIS desde el 2 nov 2026 no lo es. El aviso de la vía lo compensa en el texto; la frase del aviso de K («Los datos con fecha de observación desde el 15 feb 2025 son del detector K») queda inexacta para MODIS. `frontend/cambio_detector.js:32`. Gravedad 1, CONFIRMADO por lectura del tablero publicado.

## 8. SIN DATO

- Decisiones 2 y 6 de S174 (lectura del §7 rotulada post hoc; tags de C-montaje antes de D3): no hay lectura ni despacho de D3 que mirar.
- Si D3 de la retrospectiva se despacha antes de que entre #952 (hallazgo 254).
- Quién apretó el merge de #895 (la cuenta es compartida).
- Que el resto de las 101 frases (operación de sesiones) tenga efecto en código: no lo tienen por su naturaleza, no las audité una por una.
- El run de CI del merge de #951.

## 9. FUERA DE ALCANCE

- Mirova-v1 (D-39 a D-41), `vrp-chile-paper` y `vrp-chile-metodologia`.
- Rehacer los números de los evaluadores sellados (D25, V750-B, V375-E, MOD-D, diurno).
- Arreglar cualquiera de los hallazgos: ninguno se tocó.

## 10. Archivos de esta carpeta

`inventario.py` (+ `inventario.json`, `inventario_citas.md`), `rebajas_vs_datos.py` (+ `salida_rebajas_vs_datos.txt`, `rebajas_vs_datos_*.json`), `censo_en_commit.py` (+ `salida_censo_*.txt`, `censo_*.json`), `cierres_desde_s160.py` (+ `salida_cierres_desde_s160.txt`, `cierres_desde_s160.json`), `via_modis.py` (+ `salida_via_modis.txt`), `cierres_claude_datos.py` (+ `salida_cierres_claude_datos.txt`), `sello_regla_modd.py` (+ `salida_sello_regla_modd.txt`), `salida_tags.txt`, `hallazgos.csv`.
