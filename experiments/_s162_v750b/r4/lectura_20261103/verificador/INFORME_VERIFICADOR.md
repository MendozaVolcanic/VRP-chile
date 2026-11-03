# V750-B, lectura del 2026-11-03: informe del verificador con contexto limpio

Hecho el 2026-11-03 entre las 18:43 y las 19:10 UTC (hora del servidor de GitHub, `gh api -i`). Todo en modo sólo
lectura; el único archivo propio es `D:/vrp-trabajo/temporales/v750b_r4_20261103/verif/reagregar.py`, cuya salida
está en `verif/reagregar_salida.txt`. D: con 4,3 GB libres al empezar (`df -h /d`), sin cambio apreciable.

Método: re-agregación independiente. `reagregar.py` rehace por su cuenta la unión de los dos runs, la cobertura, las
etiquetas por canal, P1 (que veta, todas, N-3), E, los bloques de P2, la regla §6, los cuatro controles y los tres
informes aparte. Del analizador sellado reutiliza sólo las piezas de instrumento (`record_cumulo`, `slim`, `caja_de`,
`partida`, el predicado del tablero con node y la prueba de signos extraída del evaluador por `cargar_signos`). Todos
los números que imprime coinciden con `lectura/veredicto_v750b.txt` y con `lectura/informes_aparte.txt`.

## Veredicto por afirmación

| afirmación | veredicto | se sostiene en |
|---|---|---|
| A1 procedencia | CONFIRMADA | sha256 `7c9d3da5...` idéntico en `94f67fd6c` (tag), `dd8fc62b0`, el árbol y el manifiesto; 6.022 filas; `git log --format=%P -1 dd8fc62b0` = `94f67fd6c`; `git diff 94f67fd6c dd8fc62b0` = 1 archivo, 1 línea (`SOLO`); los 168 ids de esa línea son exactamente los 168 `error` de `resultados_28.json` del run 41615021658 (`reagregar.py`, y comparación directa en bash) |
| A2 unión y cobertura | CONFIRMADA | unión propia (sin `A.cargar`): 6.042 ids en el primer run, 168 en el relanzamiento, todos subconjunto; 6.022 sellados con resultado, 0 faltantes; único estado ni ok ni fuera: id 1884 (Láscar 2026-08-25 06:12, `neg_limpio`, no protegida), `error` en el primer run y `volcan_fuera_del_granulo` en el relanzamiento; `analizar_v750b.py:96` sólo deja que un `ok` reemplace; denominador 5.867, 1 SIN DATO = 0,017 % < 2 %; 0 protegidas SIN DATO; `sin_granulo` con 0 pasadas y sha atado a la lista |
| A3 controles | CONFIRMADA | nulo rehecho por mí: 1.224 publicaciones (caja × pasada) → 2.448 perturbaciones, 0 siguen publicando tras VRP 0 y 0 tras `far`; con las 50 inyecciones da los 2.498 del sellado. K = producción: 0 distintas de 5.866, con 281 publicadas en producción y 281 por K (no es un cero vacío). Censo: 5.527 iguales en B0 y en B1, de las cuales 211 (B0) y 296 (B1) tienen píxeles, y 339 observadas sin par en el censo. Control negativo: 0 bloques, y comprobé que B4 y B1 usan la misma caja en los dos volcanes. Control positivo: B0 pierde 11 de las 11 protegidas de Cordón Caulle y B1 publica las 11 |
| A4 veredicto | CONFIRMADA EN PARTE | regla aplicada a mano sobre mis propios números: elegibles B1, B2, B3, B4 (P1 que veta = 0 en TO decide y en O tabla); ningún GANA; B4 SIN SUSTRATO con neto -1 (decide y tabla), B2 EMPATE neto -4, B3 PIERDE neto 7; candidatos §6.3 en orden `[B4, B2, B1]` → B4; con y sin N-3 igual (las 4 N-3 sólo las pierden B0 y B5). **Lo que no se sostiene es la frase «ningún elegible PIERDE o BLOQUEA contra B1»: B3 es elegible y PIERDE** (ver VV750B-01) |
| A5 informes aparte | CONFIRMADA | mi script nombra las sensibles: Isluga 2026-04-07 05:36 y 2026-04-12 05:42, las dos `baja`, con `vrp_banda` [-0,0009; 0,1838] y [-0,0018; 0,1757]; en B0 a B4 publican con la base y el máximo y no con el mínimo, y B5 no publica con ninguna; la contribución a P2 de B4 contra B1 es 0 con cualquier triangulación; 0 protegidas sensibles. Cenit 30 y Tupungatito reproducidos número a número (K 2 de 10, B1 a B5 7 de 10, B0 0 de 10). El script reimplementa `etiqueta` (es un closure en el sellado) y la copia es textualmente la misma lógica; reutiliza `partida`, `record_cumulo`, `caja_de`, `slim`, `correr_node` y saca las pasadas con K distinto como el sellado |
| A6 orden temporal y oráculo | CONFIRMADA | `d38ea812a` 09:40:55 UTC y `7443cc73d` 09:59:07 UTC (autor = committer); run 41615021658 creado 09:56:01 y terminado 12:24:14 UTC; artefactos bajados a las 18:20 a 18:22 UTC (mtime de `art_41615021658/*`), relanzamiento terminado 18:37:21 y bajado 18:39 UTC; lectura 18:40 UTC. `grep -n "t_bg\|anillo\|inner\|25\.0"` sobre `experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py` del árbol: 0 coincidencias; la compuerta está en `experiments/_s162_v750c/oraculo_ablacion.py:177` (anillo) y `:180` (`bt13 > t_bg + 3.0`); `probe_v750b.py:36-38` toma `ORA` de `probe_n.py:52` (`mirova_v750_r2`) |

## Caminos por los que cada afirmación podía estar mal, y qué pasó

- A1: lista distinta entre tag y árbol (no: sha igual en 4 lugares); relanzamiento con otro código (no: un solo
  cambio de 1 línea); `SOLO` con ids de más o de menos (no: 168 = 168, conjunto idéntico); lista del run que no fuera
  sellada + suplementaria (no: 6.042 = 6.022 + 20, ids de la suplementaria desde 100000); tag ambiguo (hay rama y tag
  con el mismo nombre, `warning: refname ... is ambiguous`; los dos apuntan a `94f67fd6c`, así que no cambia nada).
- A2: resultados duplicados o faltantes (no); un «ok» del relanzamiento que no reemplazara (mi unión y `A.cargar`
  coinciden en los 6.022); pasadas nocturnas sin las 5 cajas (0, el hueco de la adenda 1 no apareció); `dayflag` ≠ 0
  entre las observadas (0).
- A3: ceros vacíos (medí el sustrato de cada control: 1.224 publicaciones, 281 publicadas de K, 211 y 296 cajas con
  píxeles en el censo); control negativo imposible de fallar (es por construcción, y así lo declara el §7; mide al
  evaluador, no a la ROI).
- A4: el código y el texto podían divergir en §6.1 (la condición extra de O con la tabla es redundante: en los 7
  brazos P1 en O con la tabla ≤ P1 en O con el canal que decide), en «no es peor» (código `reg in (GANA, EMPATE) or
  (SIN SUSTRATO and neto <= 0)` = texto) y en el orden `PREF` (`B4, B2, B5, B1, B3` = §6.3). El valor-p de B3
  (1 de 128 con 7 bloques todos a favor de B1) y de B2 (7 de 64 con 6 bloques) los rehíce con la prueba del evaluador
  (sha256 `2e557697...` = `s161-d25-lectura`).
- A5: identidad de las sensibles (no estaba en la salida; la saqué yo); que la copia de `etiqueta` difiriera (no);
  que el script leyera otro árbol (importa `analizar_v750b` de la carpeta sellada del árbol, sha `83b7159b...`).
- A6: commits fechados después de bajar artefactos (no); el documento podía citar líneas que no existen (las cinco
  citas de línea se verifican: `_fillmissing2_lineal` l. 179 a 198, `nearest` l. 195, `probe_n.py:52`,
  `_triangular_perturbado` l. 505, `isValidDetection` l. 1595).

## Hallazgos propios

- **VV750B-01 (gravedad 1).** La afirmación A4 dice que ningún elegible PIERDE o BLOQUEA contra B1. B3 es elegible
  (P1 = 0) y **PIERDE** contra B1 en T ∪ O tanto con el canal que decide como con la tabla sola (neto 7, 7 bloques,
  p = 1/128). La regla §6.3 lo excluye correctamente de los candidatos (`cand = [B4, B2, B1]`), así que la ROI no
  cambia; lo que está mal es la frase de la afirmación, no la lectura. Si se quiso decir «ningún candidato del §6.3»,
  entonces sí: B4 y B2 no son peores que B1 en ningún canal.
- **VV750B-02 (gravedad 1).** `SESGOS_CONOCIDOS_V750B.md` (encabezado) dice que el veredicto «sigue siendo el del
  lector de la adenda 1 (adenda 2 §8)». La adenda 3 §3, sellada el 2026-10-29, dice que el veredicto es el de
  `leer_n3_v750b.py`. El docstring de `informes_aparte_v750b.py` lo dice bien. Es una frase desactualizada en un
  documento informativo; no toca nada sellado.
- **VV750B-03 (gravedad 1, observación).** Las dos pasadas sensibles a la triangulación tienen el mínimo de
  `vrp_banda` apenas bajo cero (-0,0009 y -0,0018 MW) y el máximo igual al VRP base: con la diagonal de producción
  publican (acierto, son `baja` con alerta), con la otra no publicarían. Como la sensibilidad es la misma en B0 a B4,
  el P2 contra B1 no se mueve; E subiría 2 en B0 a B4 y no en B5, que ya está vetado. Las razones VRP sí heredan
  VPCC750-01, como dice el documento.
- **VV750B-04 (gravedad 1, observación).** En el relanzamiento, el gránulo `VJ102MOD.A2026237.0612` dio `ok` para
  los otros 8 volcanes y `volcan_fuera_del_granulo` sólo para Láscar (id 1884), que en el primer run había caído con
  todos en `FileExistsError`. Con la regla de unión alternativa (cualquier estado reemplaza a un error) 1884 saldría
  del denominador como «fuera» en vez de contar como SIN DATO; en los dos casos es un negativo limpio no observado y
  el veredicto es el mismo.
- **VV750B-05 (gravedad 1, observación).** `7443cc73d` (09:59:07 UTC) es 3 minutos posterior a la creación del run
  (09:56:01 UTC) y 5 minutos posterior a la generación de la referencia (`ref/`, 09:54 UTC), pero 2 h 25 min
  anterior al fin del run y 8 h 20 min anterior a la descarga de artefactos; no existía ningún resultado. `d38ea812a`
  (09:40:55 UTC) es anterior a todo, incluida la referencia. Las fechas de los commits son del reloj local (autor =
  committer); las de los runs son del servidor.
- **VV750B-06 (gravedad 1, observación).** La copia de `informes_aparte_v750b.py` en el árbol de lectura tiene CRLF
  (sha256 distinto del blob de `7443cc73d`), pero es idéntica salvo el CR (`diff --strip-trailing-cr`). El informe
  aparte no exige sha256; el analizador que importa sí está atado (sha LF `83b7159b...`, igual al tag
  `s162-v750b-sellado`, a `s167-v750b-adenda3-sellada` y a `94f67fd6c`).
- **VV750B-07 (gravedad 1, observación).** La línea «control B0 y B1 = censo S159» imprime sólo los iguales (5.527).
  No dice cuántas de esas comparaciones tienen píxeles (211 en B0, 296 en B1) ni cuántas observadas quedan sin par
  (339). El control no es vacío, pero habría que medirlo aparte para saberlo, como hice.

## Lo que no pude verificar

- Que los runs de GitHub ejecutaran exactamente el código de `94f67fd6c` y `dd8fc62b0` más allá de `headSha` y del
  log (`log_chunk28.txt` muestra el `pip install` y los `DOWNLOAD_ERR` con `FileExistsError`; las versiones de
  earthaccess 0.17.0 y fsspec 2026.9.0 aparecen en el log, pero no comparé con el trozo 27 línea a línea).
- El origen de `pub_prod` más allá de `experiments/_s159/n/01_poblacion.py:122` (`r["pub"]`): el control K =
  producción compara contra ese campo; que ese campo sea el predicado del tablero sobre el record de producción lo
  asumo de `banco_paridad`, no lo tracé.
- La afirmación del documento de sesgos de que fue escrito «sin haber abierto la referencia»: sólo puedo decir que su
  commit es anterior a la generación de la referencia en el árbol del día.
- La fidelidad física del oráculo R2 y del probe (fuera del alcance de esta lectura; el control contra el censo S159
  sólo fija que no cambió desde S159).
- Que el relanzamiento no haya cambiado el resultado de pasadas que ya estaban `ok` (no las tocó: 168 ids pedidos,
  168 devueltos, todos del trozo 28).

## Supuestos

- Tomé como «canal que decide» T con la tabla y O con tabla más OCR, con la frontera `2026-06-13` del analizador.
- Tomé como vara de la regla el texto del §6 del pre-registro con las marcas VB-01, VB2-01, VB2-02 y VB3-01, y la
  adenda 3 §2 para el P1 que veta.
