# Verificación independiente del PR Mirova-v1#26 y de la rama s163/d39-reposicion-y-bucle

Verificador con contexto limpio. No leí el razonamiento del autor; sólo sus scripts y salidas,
y los contrasté con mediciones propias.

Hora del servidor al empezar: `Mon, 26 Oct 2026 11:53:29 GMT` (`gh api -i repos/MendozaVolcanic/Mirova-v1 | grep -i ^date`).
Clon: D:\vrp-trabajo\s163-d39\mirova-v1 con main f5fe3b9a64, pr26 fb95c0e790, s163 2ad6dd8730,
refs/sim/merge26 d276e2a5d9, refs/sim/merge_s163 3c85f631e4. Disco D al empezar: 8,5 GB libres.

## 0. Caminos por los que cada afirmación podría estar mal (escritos ANTES de releer nada)

A1 (241 llaves perdidas en 53b1e6d3c0, 2 protegidas, ninguna en el CSV de reposición del PR; sin otra pérdida vigente desde la base).
- La llave (timestamp, Volcan, Sensor) puede normalizar algo (espacios, coma de miles, formato de hora, alias de volcán) y ocultar filas que cambiaron de forma sin perderse, o contar como perdida una fila que sólo cambió de formato.
- El muestreo cada 6 h (s04) puede saltarse pérdidas que vivieron menos de 6 h y que luego se repusieron con otros campos (pérdida y reposición con valores distintos).
- «Ninguna está en el CSV del PR» depende de cómo se compara (llave o fila entera); la firma de bitácora (s02) puede excluir filas legítimas.
- El clon puede estar atrasado respecto de origin/main de hoy: un commit posterior pudo reponer o perder más filas.
- Las 2 protegidas: el VRP puede estar en otra columna o con coma decimal; «protegida» se define por clase y VRP.
- Pérdidas de llaves duplicadas (misma llave dos veces en una versión y una vez en la siguiente) no cuentan como pérdida con un conjunto.

A2 (corrida 40117161109 hizo checkout de un sha viejo y rebasó -X ours).
- El registro del run puede mostrar el sha del checkout, pero el rebase con -X ours sólo pierde filas si hubo conflicto real; hay que ver en el log si el rebase reportó conflicto o si el archivo CSV se regeneró entero desde el estado viejo.
- Puede haber otro mecanismo (regeneración desde HTML viejo, dedup por llave) que explique la pérdida sin el rebase.
- La atribución «la corrida 40116786605 empujó e47b0d5b60» hay que verla en el log o en la API, no inferirla.

A3 (ciclo A vs B sobre el mismo CSV: 0 llaves desaparecen, 0 campos cambian, agrega exactamente las filas de reposición).
- La simulación sin red (HTML congelado del 22-oct) puede no ejercitar la rama que lee latest.php real hoy (formato de tabla nuevo, volcán nuevo, fila con coma de miles).
- El ciclo simulado puede saltar pasos del workflow (dedup, ordenamiento, `git pull --rebase`) que son justamente donde se pierde.
- Comparación por texto: un cambio de formato (CRLF, BOM, comillas, orden de columnas, coma decimal) puede esconderse o inventar diferencias.
- «Agrega exactamente las filas de reposición» puede ser verdadero sólo porque el CSV de partida ya tenía de todo lo demás; con otro CSV de partida (el de main hoy) el resultado podría diferir.
- La reposición puede aplicarse cada ciclo (idempotencia): si el archivo se vuelve a sumar cada 5 min, duplica.

A4 (OCR: sólo cambia Nota_Validacion en 647 filas y agrega Metodo_Clase vacía; 0 llaves desaparecen).
- «Mismo esqueleto ASCII» puede esconder un cambio de significado (acentos en palabras clave que otro script filtra por texto exacto).
- El consumidor (VRP Chile, build_c2ab_windows, banco_paridad) puede leer el OCR por posición de columna, y una columna nueva al final puede romperlo o no.
- El ciclo OCR simulado puede no ejercitar la rama del workflow que corre contra imágenes reales (0 imágenes en el clon blob:none).
- El OCR tiene su propio push con rebase; el PR cambia ese rebase (ver punto 3).

A5 (cada fila del archivo de reposición existe en un commit anterior y falta hoy; las 241 idénticas a 53b1e6d3c0^).
- «Existe en algún commit anterior» con llave normalizada no es «idéntica campo a campo»; hay que ver la comparación.
- Si una fila existió y luego fue corregida deliberadamente (versión del scraper, geometría), reponer la vieja reintroduce un dato ya corregido.
- Filas duplicadas dentro del archivo de reposición.
- Filas que faltan hoy porque un commit posterior las borró a propósito (dedup de llaves repetidas).

A6 (Chillán 15 y 16-oct sólo en OCR, nunca en tabla).
- Ventana de commits revisada puede no cubrir todas las versiones (el scraper corre cada 5 min; un commit intermedio pudo tenerlas).
- La hora en el OCR y en la tabla pueden estar en zonas distintas (UTC vs local) y la búsqueda por hora exacta no las encontraría.
- Nombre del volcán con variantes (A14).

A7 (suite pasa entera en los merges simulados: 167 y 170).
- La suite pudo correr sobre un árbol que no es el merge simulado (ruta equivocada), o con tests saltados (skipped) que cuentan como pasados.
- Los merges simulados pueden no coincidir con lo que GitHub haría (conflictos resueltos a mano).
- La suite puede no cubrir los workflows.

A8 (test nuevo falla con main.yml viejo y pasa con el del PR; 12 mutaciones atrapadas).
- Mutaciones «atrapadas» por caída (error de parseo) y no por aserción (A152).
- El test puede fijar texto y no comportamiento (pasa por subcadena, A92).
- El main.yml de la rama s163 puede diferir del de pr26.

A9 (sync-mirova-csv.yml en VRP Chile ya no rebasa; su test pasa).
- La copia local del worktree puede estar atrasada respecto de origin/main de VRP-chile.
- «No rebasa» puede ser verdad para un camino y no para otro (reintento, fallback).
- El test puede pasar por subcadena.

A10 (pausar main.yml y ocr_workflow.yml basta).
- Otro workflow (dependabot, limpieza, evidencia, distancia-aprox, cron de respaldo) puede escribir los CSV.
- Un `workflow_run` o `repository_dispatch` encadenado.
- Un script del propio repo ejecutado por otro workflow que haga `git add monitoreo_satelital`.
- Un push desde VRP-chile al repo Mirova-v1 (cross-repo).

Punto 3 (choques del rebase -X ours en ocr_workflow.yml): medir sobre logs de runs reales con gh; ventana y comando explícitos.


## 1. Material y método

- Clon f5fe3b9a64 (2026-10-26 10:33 UTC). El remoto al empezar iba en 7c2390adf9 (11:51 UTC): 23 commits de datos
  por delante, todos del scraper, del OCR, de gráficos y de Distancia aproximada (`gh api repos/.../commits?sha=main`).
  Ningún commit de código. El clon NO se tocó (ni checkout ni fetch); todo lo histórico se bajó por
  raw.githubusercontent.com a memoria, o se leyó con `git show` y `git diff --name-only --no-renames` sobre objetos ya
  presentes.
- Instrumentos propios (todos en D:\vrp-trabajo\s163-d39\verificador\): v03 (registros de Actions filtrados),
  v04 (barrido exhaustivo de TODAS las versiones del consolidado desde la base, no muestreo), v05 (reposición
  contra los padres), v06 (mutaciones y línea base roja, con clasificación por mensaje), v07 (choques del rebase
  del OCR, punto 3), v08 (Chillán 15 y 16 oct, todas las versiones), v09 (suite completa sobre copias de los dos
  merges simulados), a7_*.txt (archivos de los merges).
- Advertencia de proceso: para detener dos barridos atascados usé Stop-Process por línea de comando; en una de
  esas limpiezas el filtro fue demasiado ancho y mató varios `bash.exe` (uno era mi propia consola). Es posible
  que haya alcanzado un shell de otra sesión Claude; no lo pude comprobar. Lo anoto por honestidad.

## 2. Veredictos por afirmación (evidencia de esta sesión)

### A2. Corrida 40117161109: checkout de sha viejo y rebase -X ours sobre e47b0d5b60. CONFIRMADO. Gravedad 4.

- `gh run view 40117161109 --json headSha,createdAt,conclusion,workflowName`: headSha 19d428271f, createdAt
  2026-10-24T17:40:09Z, success, "Monitor Volcanico VRP".
- `gh run view 40116786605 --json ...`: headSha 39e16a1068, createdAt 17:35:06Z, conclusion `cancelled`,
  mismo workflow.
- run_40117161109.log l. 94: `git fetch ... +19d428271f...:refs/remotes/origin/`; l. 393 a 402: commit `d62696a`
  ("3 files changed, 22304 insertions(+), 22301 deletions(-)"), `19d4282..e47b0d5 main -> origin/main`,
  `Rebasing (1/1)`, `Successfully rebased`, `e47b0d5..53b1e6d main -> main`, `push OK (intento 1)`. Ninguna
  línea `Auto-merging` ni `CONFLICT` aunque e47b0d5b60 y d62696a tocaban el mismo CSV: con `-X ours` el rebase
  resuelve el choque sin imprimir nada (esto decide el método del punto 3).
- run_40116786605.log l. 401 a 406: `39e16a1..19d4282 main -> origin/main`, `Rebasing (1/1)`,
  `19d4282..e47b0d5 main -> main`, push OK a las 17:40:20 (11 s después de crearse la corrida 40117161109).
- `git log --first-parent` del clon, 17:25 a 17:50 UTC: 39e16a1068 (17:25:58 VolcanoBot), 19d428271f
  (17:38:49 VolcanoOCR), e47b0d5b60 (17:40:17 VolcanoBot), 53b1e6d3c0 (17:44:20 VolcanoBot). `git diff-tree` de
  e47b0d5b60: bitacora_robot.txt, consolidado, positivos; de 53b1e6d3c0: consolidado y positivos sin bitácora
  (la firma SIN_BITACORA de s02 se reproduce: el hunk de la bitácora lo perdió el `-X ours`).
- Matiz: 19d428271f no era "viejo" al despachar (era la punta a las 17:40:09); quedó viejo porque la corrida
  40116786605 empujó e47b0d5b60 8 s después y el runner tardó 3,4 min en arrancar. El mecanismo es el que dice A2.
- V1 (hallazgo propio, gravedad 2): la corrida 40116786605 figura como `cancelled` y sin embargo empujó
  e47b0d5b60. `cancel-in-progress: true` canceló una corrida que ya había empujado. Un conteo de pushes por
  conclusión de la API subestima los escritores; una auditoría futura debe contar por el registro o por git.

### A5. Reposición de la rama s163 (2.351 filas): existen en un commit anterior, faltan hoy, las 241 idénticas a 53b1e6d3c0^. CONFIRMADO (y más fuerte que lo afirmado). Gravedad 5.

- v05_salida.txt: `filas s163 2351 filas pr26 2110 las primeras 2110 de s163 == pr26: True`; `llaves distintas 2351
  repetidas 0`; `presentes hoy en main (clon f5fe3b9a64): 0`; `nombres no canonicos: Counter()`; tipos RUTINA 2191,
  ALERTA_TERMICA 107, FALSO_POSITIVO 53; protegidas 20 (listadas en la salida).
- Instrumento distinto al del autor: cada fila se comparó contra el padre de cada uno de los 17 commits de mezcla
  (los 16 del autor más 53b1e6d3c0), bajados por raw. `RESULTADO {'identica campo a campo a un padre': 2351}`:
  las 2.351 filas, incluidas las dos columnas UTC, son byte a byte iguales a una fila de algún padre. (El
  autor encontró 1.294 "con campo distinto" porque sólo miró el padre del episodio donde se perdió la llave; en
  otro padre, con el backfill ya corrido, la fila está idéntica.)
- `241 agregadas: en 53b1e6d3c0^ 241 identicas campo a campo 241`.
- Lo que NO prueba: que una fila sea la versión "más reciente" que existió (Ultima_Actualizacion puede haber
  cambiado entre versiones). No afecta la llave ni la clase ni el VRP.

### A8. Prueba nueva: roja con el main.yml de main, verde con el del PR; 12 mutaciones atrapadas. CONFIRMADO EN PARTE. Gravedad 2.

- v06_salida.txt (copia propia de mut/, clasificando por el mensaje de la falla, no sólo por el conteo JUnit):
  - control (main.yml del PR): 3 pasan. main.yml de la rama s163: 3 pasan.
  - línea base, main.yml de main: 2 fallan por AssertionError: `el push perdio 1 llaves` y
    `assert ('-X ours' not in ...)`. Roja como se afirma, y por la aserción prevista.
  - R2 vuelve el `pull -X ours`: `el push perdio 1 llaves` más la aserción estructural. Atrapada por aserción.
  - R2 ocr_workflow vuelve `-X ours`: aserción `'-X ours' not in`. Atrapada por aserción.
  - R2 sin `git reset --hard origin/main`: la prueba de comportamiento falla por la aserción `r.returncode ==
    0` (mensaje "Guarda de llaves OK..."; el push se rechazó 5 veces), que es aserción, aunque no la de llaves; y
    la estructural cae con `ValueError: substring not found` (`script.index("git reset --hard origin/main")`).
  - R3 sin guarda: la ÚNICA prueba que falla es la estructural, y falla por `ValueError: substring not
    found`, no por `assert`. pytest lo cuenta como `failure` en el JUnit, por eso el s15 del autor lo llamó
    "falla por aserción".
- V2 (gravedad 2): de las 4 mutaciones de workflow, 2 se "atrapan" en la prueba estructural por una
  excepción de `str.index`, no por una aserción (lección S152: mutación que cae no es atrapada). Para "R3 sin
  guarda" no hay otra prueba que la detecte. Arreglo barato: `assert "python guarda_llaves.py" in script` antes de
  los `index`. No invalida el PR: la línea base roja y la prueba de comportamiento sí funcionan.
- Las 8 mutaciones de módulos Python (orden, guarda, reponer, scraper, mojibake) no las re-corrí; s15_salida.txt
  las da como atrapadas por `failure` del JUnit. SIN RE-MEDIR por mí.

### A9. VRP Chile: sync-mirova-csv.yml ya no rebasa (PR #895) y su prueba pasa. CONFIRMADO. Gravedad 3.

- Worktree: `git log -1 origin/main` = b09a7b321 (2026-10-26 09:01 -03); `gh api repos/MendozaVolcanic/VRP-chile/
  commits/main` = b09a7b3216 (12:01:37Z): la copia local está al día.
- Sha del blob local = remoto: workflow 38ea78dda0..., prueba 88eb143a53... (`git rev-parse origin/main:<ruta>`
  contra `gh api .../contents/<ruta>?ref=main --jq .sha`).
- `git show origin/main:.github/workflows/sync-mirova-csv.yml` l. 101 a 113: `git fetch origin main || continue`,
  `git reset --hard origin/main`, add, commit, `git push && exit 0`. Sin `rebase`, sin `-X`.
- `gh pr view 895`: MERGED 2026-10-22T11:29:18Z, merge 6547f53151.
- `python -m pytest -q -p no:cacheprovider tests/test_sync_mirova_sin_rebase_s160.py`: `9 passed in 3.00s`.

### A10. Pausar main.yml y ocr_workflow.yml basta; ningún otro workflow escribe el consolidado ni el OCR por mezcla de texto. CONFIRMADO EN PARTE. Gravedad 3.

- Workflows en main (`git ls-tree main .github/workflows/`): archivar_evidencia, dependabot_automerge,
  deploy.yml.disabled, distancia_aprox_historia, graficos_completo, main, marcar_artefacto, ocr_workflow,
  validar_funcionalidades. En el PR se agrega vigilante_dato.yml (`contents: read`, sin git push).
- Escritores de main (grep de `git push`): main.yml (consolidado, positivos, bitácora; rebase `-X ours`),
  ocr_workflow.yml (OCR, maestro, registro_<vol>.csv; rebase `-X ours` en el push del OCR; el paso "Distancia
  aproximada" ya usa fetch y reset), graficos_completo.yml (`workflow_run` tras main.yml; `git pull --no-rebase
  --strategy-option=ours`; sólo v_html, estado_sistema.json, .graficos_hash, volcanes.js), archivar_evidencia.yml
  (sólo `workflow_dispatch`; `git rm` de carpetas de imágenes; `git pull --rebase --autostash -X ours || true`),
  marcar_artefacto.yml (`workflow_dispatch`; anotaciones.csv; rebase sin -X). distancia_aprox_historia.yml copia el
  OCR a /tmp y no empuja. validar_funcionalidades no empuja. dependabot_automerge mergea PRs de dependabot.
- Confirmado: ninguno de los otros escribe el consolidado ni el OCR. Dos matices que la afirmación no dice:
  - V3 (gravedad 2): archivar_evidencia.yml y graficos_completo.yml siguen mezclando con `-X ours` (rebase y
    merge). No tocan CSV, así que no corrompen la referencia, pero son el mismo patrón que el PR erradica y
    quedan fuera del PR (archivar es manual; gráficos corre tras cada ciclo).
  - V4 (gravedad 2): pausar un workflow no cancela la corrida en vuelo. Una corrida de main.yml con el código
    viejo que esté corriendo al pausar puede empujar después del merge con `pull --rebase -X ours`. Como el merge
    del PR no toca el consolidado (A7: 0 archivos del PR cambiados también en main desde la base), ese rebase no
    mezcla datos, pero sí correría una vez más el scraper viejo. Esperar a que no haya corridas "in progress"
    (`gh run list --status in_progress`) antes de mergear cierra el hueco.

### A7. Suite entera verde sobre los dos merges simulados (167 y 170). CONFIRMADO EN PARTE (conteo verificado en los XML del autor; mi re-corrida completa está en v09, ver más abajo). Gravedad 2.

- s13_suite_merge26.xml: `errors="0" failures="0" skipped="0" tests="167"`; s18: `tests="170"`, 0 skipped.
- Los merges simulados son limpios: `git diff --name-only main refs/sim/merge26` == `git diff --name-only
  c48d24cad8 pr26` (diff vacío, "IGUALES"); `git diff --name-only pr26 refs/sim/merge26 -- <archivos del PR>` da
  0; lo mismo para merge_s163. `comm -12` de los archivos del PR con los que main cambió desde la base: vacío (no
  hay archivo tocado por los dos lados, así que GitHub tampoco encontrará conflicto).
- El clon está en HEAD = refs/sim/merge_s163 con `git status --short` vacío: el autor corrió s18 sobre ese árbol.

### A3. Ciclo del scraper, código de main (A) contra main + PR (B), mismo CSV de partida: 0 llaves desaparecen, 0 campos cambian en filas existentes, se agregan exactamente las filas de reposición (2.110 con el PR, 2.351 con s163). CONFIRMADO, con tres límites del instrumento que la afirmación no dice. Gravedad 4.

- Insumos del autor verificados: `scripts/cons_main_original.csv` md5 94ccb8430862... = `git show main:...consolidado.csv`;
  `ocr_main_original.csv` fbd0d13715... = main. Código de sim/A = main en 9 módulos; sim/B = pr26 en los 9; sim/B2 =
  pr26 con el archivo de reposición de s163 (diff -q contra `git show`).
- Re-corrida propia (v10_ciclos.sh, copias ciclo_A y ciclo_B con los CSV originales, md5 comprobado antes de
  correr; red simulada del autor s08: latest.php del 2026-10-22, imágenes 404, hora fija 2026-10-26 12:00 UTC):
  A: scraper main, 528 filas leídas, backfill "sin cambios". B: `reponer_filas: 2351 filas repuestas`, scraper PR
  (`SystemExit 0`), backfill "escrito", `Guarda de llaves OK` (contra el original), y un segundo `reponer_filas`:
  `0 filas repuestas` (idempotente).
- Comparación propia a nivel de TEXTO, por línea entera y llave cruda sin normalizar (v11_salida.txt):
  consolidado O 42.991, A 42.991, B 45.342 filas; repetidas 0/0/0; cabecera igual; sin BOM.
  O->A: 0 perdidas, 0 nuevas, 33 líneas con campo distinto (`Ultima_Actualizacion` y `_UTC` de las 33 últimas
  pasadas, que el scraper refresca en cada ciclo: comportamiento de main, no del PR).
  O->B: 0 perdidas, 2.351 nuevas, las mismas 33 líneas distintas y ninguna más.
  A->B: 0 perdidas, 2.351 nuevas, 0 campos distintos en filas comunes; las 2.351 nuevas están todas en el archivo
  de reposición; 2.051 difieren del archivo SOLO en `Fecha_Proceso_UTC` y `Ultima_Actualizacion_UTC`, que en el
  archivo vienen vacías y el backfill llena desde la hora de Chile (comprobado campo a campo: 2.050 en las dos
  columnas, 1 en una; ningún otro campo). positivos: A 1.696, B 1.803 (107 ALERTA_TERMICA repuestas, 0 cambios).
- V7 (artefacto de mi plataforma, gravedad 0): en ciclo_A el consolidado salió con CRLF (42.992) porque pandas en
  Windows escribe `os.linesep` cuando el backfill no reescribe; en CI (ubuntu) es LF. No es del PR.
- Límites del instrumento del autor, heredados por mi re-corrida:
  - V8 (gravedad 2): el HTML de latest.php es del 22-oct y el CSV de partida del 26-oct, así que el scraper no
    inserta NINGUNA fila nueva en ningún brazo (sólo refresca 33). El camino "pasada nueva + concat +
    drop_duplicates + orden total" no se ejercitó con datos reales; lo cubre sólo tests/test_orden_determinista.py
    con datos sintéticos (verde en v09). La lógica de inserción no la cambia el PR; el orden sí.
  - La simulación no ejecuta `git fetch/reset/push` ni la guarda contra `origin/main` (sólo `--anterior`): el
    bucle real lo cubre tests/test_bucle_push_main_yml.py en un repo de juguete (A8).
  - Las imágenes no se descargan (404), así que `git add monitoreo_satelital/` con imágenes nuevas no se simuló.

### A4. OCR: el código del PR sólo cambia Nota_Validacion en 647 filas (mojibake) y agrega Metodo_Clase vacía al final; 0 llaves desaparecen. CONFIRMADO para las filas existentes; CONFIRMADO EN PARTE como descripción del PR (cambia también lo que escribirán las filas futuras). Gravedad 3.

- v11 sobre mi re-corrida (s10 del autor: guardar_ocr sin eventos, backfill, [reparar_mojibake], reconciliar,
  merger): OCR O 1.147, A 1.147, B 1.147; repetidas 0; `columnas nuevas en B: ['Metodo_Clase']`, orden de las
  viejas igual; O->B 0 perdidas, 0 nuevas; 647 líneas sólo `Nota_Validacion` (mojibake a UTF-8 legible), 499
  líneas distintas sin campo distinto (la coma final de la columna nueva) y 1 línea con `Zenith_Sat_deg` 24 ->
  24.0 que también la produce el brazo A (pandas al reescribir; de main, no del PR). `Guarda de llaves OK` para el
  OCR contra el original. `reparar_mojibake: 647 notas reparadas`.
- Efecto en VRP Chile de la reparación: `pipeline/mirova_csv_loader.py` l. 94 (origin/main de VRP-chile):
  `_OCR_DIST_RE = re.compile(r"(?:dist(?:[≈~=]|â‰ˆ)|->|→)\s*(\d+\.?\d*)\s*km")`, acepta las dos formas. Ejecutado
  con la nota en mojibake y con la reparada: 2.76 y 2.76; con la nota nueva del método de grupo (con el sufijo
  "| metodo de grupo: ...") y con una nota reconciliada: 1.55 y 1.55. Nadie en VRP Chile lee
  `Confianza_Validacion` ni `Requiere_Verificacion` (grep sobre origin/main sin experiments/docs/tests: 0 usos).
  Ningún consumidor lee el OCR por posición de columna (grep de usecols/iloc/header=None: 0).
- V6 (gravedad 1, informativo): el PR cambia `ocr_utils.clasificar_confianza` para el método de grupo de píxeles:
  `confianza` 'alta' -> 'baja', `requiere_verificacion` False -> True y nota con sufijo. Esto NO toca filas
  existentes (por eso A4 no lo ve) pero sí todas las ALERTA_TERMICA_OCR futuras de ese método. Consumidores que
  filtran por confianza: merger_maestro.py l. 146 sólo descarta 'invalido' (las 'baja' siguen pasando al maestro);
  VRP Chile no filtra. Sin efecto en la referencia; conviene saberlo al leer el CSV.
- V9 (gravedad 1, informativo): el maestro (`registro_vrp_maestro_publicable.csv`, producto propio de Mirova-v1,
  no lo consume VRP Chile) cambia en B respecto de A en 419 llaves comunes: 391 por la nota reparada y 28 porque
  la reposición devuelve filas de tabla que el merger prefiere sobre la fila OCR de la misma llave (de
  `ALERTA_TERMICA_OCR` a `ALERTA_TERMICA`, con Distancia_km y VRP de la tabla; ej. Puyehue VIIRS 1780637762: VRP
  1.0 -> 1.09, dist 0.0 -> 7.83), más 79 llaves nuevas. Es el efecto esperado de reponer la tabla, no una pérdida.

### A7 (complemento, re-corrida propia). CONFIRMADO. Gravedad 2.

- v09_salida.txt: copia del árbol del clon (HEAD = refs/sim/merge_s163, sin .git ni imágenes): `170 passed, 1
  warning in 283.53s`. Copia derivada con los 5 archivos en su versión pr26 (igual a refs/sim/merge26 archivo a
  archivo, salvo el test nuevo que se borra): `167 passed, 1 warning in 271.74s`. 0 saltadas (`-q`, sin
  `skipped` en la línea final).

## 3. Punto 3: choques del `git pull --rebase -X ours` del push del OCR

Pregunta: en los registros de ocr_workflow.yml de los últimos días, cuántas veces el rebase tuvo que resolver un
choque. Respuesta en dos capas, porque el registro solo no puede contestarla.

- Comando: `gh run list -R MendozaVolcanic/Mirova-v1 -w ocr_workflow.yml --limit 300 --json
  databaseId,createdAt,conclusion,headSha,event,status` y, por corrida, `gh run view <id> -R ... --log` (v03,
  filtrado a las líneas de checkout, rebase y push; copias en verificador\ocr_logs\<id>.txt). Ventana:
  2026-10-20T21:00:10Z a 2026-10-26T12:00:09Z, 300 corridas (270 `workflow_dispatch`, 30 `schedule`; 288
  success, 12 cancelled), 300 con registro.
- Capa 1, huellas textuales (lo único que el registro muestra; excluido el eco del guion):
  `CONFLICT` 0, `Cannot merge binary` 0, `could not apply` 0, `Pull falló` 0, `rebase --abort` 0.
  `error: failed to push some refs` en 2 corridas (39932310796 y 40296234819: push rechazado una vez y reintento
  verde). Con `-X ours` git NO imprime nada cuando resuelve un choque (verificado en run_40117161109.log: rebase
  sobre un commit que tocaba el mismo CSV, salida `Rebasing (1/1)` y `Successfully rebased` sin `Auto-merging`),
  así que el 0 de arriba no significa 0 choques: el instrumento es ciego por diseño.
- Capa 2, reconstrucción con git (v07_choques_ocr.py, v07_salida.txt): por cada push `A..B main -> main` del
  registro, X = headSha de la corrida (sha del despacho), archivos que el remoto cambió en X..A contra los que el
  commit del OCR cambia en A..B (`git diff --name-only --no-renames`). Resultado: 332 pushes en 294 corridas; 314
  rebasados (el remoto se movió desde el despacho); 296 sin ningún archivo en común; **18 con el mismo CSV cambiado
  por los dos lados (5,7 % de los rebasados; 6 % de las corridas)**. En los 18 el commit remoto es un `OCR:
  Captura de eventos satelitales` de OTRA corrida del OCR, hecho entre 3 s y 5,5 min DESPUÉS de crearse la
  corrida analizada: dos corridas del OCR solapadas. Causa visible: el cron `5 * * * *` (que GitHub ejecuta con
  retraso de 1 a 33 min) cae encima del despacho externo de :00 y :30; 19 pares de corridas creadas a menos de 6
  min una de otra en la ventana, y `cancel-in-progress: true` cancela a la vieja cuando ya empujó (mismo mecanismo
  que V1). Archivos en común: `registro_vrp_ocr.csv` en 11 casos (remoto 165 a 199 líneas cambiadas, local 1 a 97,
  sobre un archivo de 1.147 líneas), y los `registro_<volcán>.csv` más el maestro en 7 casos.
- Lectura: no puedo probar que esos 18 produjeron hunks en conflicto (haría falta el commit original antes del
  rebase, que nunca se empujó); con 165 a 199 líneas cambiadas en el remoto y 33 a 97 en el local sobre el mismo
  archivo ordenado sólo por timestamp (orden inestable, R1 del PR), un conflicto es lo probable: SOSPECHA fuerte.
  Hoy `-X ours` lo resolvió en silencio dejando la versión remota en los hunks en disputa (en un rebase "ours" es
  la rama remota); la siguiente corrida del OCR vuelve a leer las imágenes, así que el daño es un ciclo del OCR y
  no una pérdida permanente, pero nadie se enteró.
- V5 (gravedad 3): con el PR, esos 18 casos (6 % de las corridas) dejan la corrida del OCR en rojo
  (`rebase --abort` y `exit 1`) en vez de resolverse a ciegas, salvo que el orden total del PR haga que los dos
  lados cambien hunks disjuntos (SIN MEDIR: no hay dos corridas con el código del PR para comparar). Dos filas
  nuevas iguales escritas por dos corridas difieren en `Fecha_Proceso_UTC`, así que cuando las dos corridas
  detectan el mismo evento el conflicto es seguro. Es el comportamiento que el PR busca (rojo antes que mezcla),
  pero conviene (a) sacar el cron del OCR de la grilla del despachador o quitar uno de los dos, y (b) tratar un
  rojo del OCR como "ciclo repetido", no como pérdida. No afecta al consolidado.
- Dos "push cuyo padre no es la base del rango" de v07 son artefactos míos: `edb248e` es abreviatura ambigua en
  el clon (`git log dc0b360..edb248ee75` da un solo commit, padre correcto) y `90c3b5d..7501aca` es posterior al
  main del clon (corrida de las 12:00Z). Sin consecuencia.

### A1. 53b1e6d3c0 perdió 241 llaves que siguen ausentes hoy, 2 protegidas, ninguna en el CSV del PR; desde la base no hay otra pérdida vigente. CONFIRMADO (el episodio, con instrumento propio); el "ninguna otra pérdida vigente desde la base" queda CONFIRMADO EN PARTE: exhaustivo en los tramos ya barridos al cerrar, y por la firma de mezcla en los 1.239 commits. Gravedad 5.

- Instrumento propio v12_episodio_53b1.py (llave cruda sin normalizar; versiones bajadas por raw, main del clon):
  padre e47b0d5b60 42.871 filas (42.871 llaves) | 53b1e6d3c0 44.195 filas, 42.630 llaves, **1.565 repetidas** |
  main f5fe3b9a64 42.991 filas, 0 repetidas. `llaves del padre ausentes en 53b1e6d3c0: 241 | de esas, ausentes
  hoy en main: 241 | repuestas despues: 0`; `llaves nuevas en 53b1e6d3c0: 0`; tipos RUTINA 232, ALERTA_TERMICA 5,
  FALSO_POSITIVO 4; `protegidas perdidas: 2`: ('1780084500', 'Villarrica', 'MODIS') 2026-05-29 19:55:00 VRP 1.83
  dist 2.0 y ('1792820881', 'Nevados de Chillan', 'VIIRS375') 2026-10-24 05:48:01 VRP 2.36 dist 0.84.
  `perdidas en el PR (2110): 0 | perdidas == las 241 agregadas en s163: True`. Timestamps no enteros: 0 en las
  tres versiones (la llave no normaliza nada que importe).
- v13_duplicados_53b1.py: las 1.565 llaves repetidas tienen exactamente 2 copias **idénticas campo a campo** (0
  llaves con copias distintas) y la fila de hoy es igual a esas copias en las 1.565. El dedup posterior del
  scraper no eligió una copia peor. V10 (gravedad 1, informativo): el episodio duplicó 1.565 filas además de
  borrar 241; el duplicado era inocuo, la pérdida no.
- "Desde la base no hay otra pérdida que siga ausente hoy": barrido exhaustivo versión por versión (v04d_fragmento.py, 4 fragmentos
  paralelos; v04_perdidas_exhaustivo.py, lento, cubrió las versiones 0 a 350). Al momento de cerrar este informe
  los fragmentos iban en 200/310, 150/311, 150/311 y 150/311 (cada uno parte de la versión anterior al tramo, así
  que no hay hueco entre tramos), es decir ~55 % de las 1.239 versiones. En todo lo barrido la ÚNICA versión con
  llaves perdidas o repetidas es 53b1e6d3c0 (versión 750 de 1.240): `filas 44195 rep 1565 perdidas 241 nuevas 0
  raras 0`, idéntico a v12. Los procesos siguen corriendo y escriben `v04d_resultado_<a>_<b>.json`; para cerrar el
  100 % basta `python v04e_combinar.py` en esta carpeta cuando los cuatro digan FIN (el combinador ya está
  escrito y verifica que los tramos sumen 1.239 pasos). Hasta ese momento, el "no hay otra pérdida" para el 45 %
  restante se apoya en (a) el muestreo cada 6 h del autor (s04: 20 muestras, unión 241) y (b) la firma de mezcla
  de abajo, que es exhaustiva.
- Exposición a la mezcla (v14_firma_mezcla.sh, firma SIN_BITACORA de s02 que reproduje en 53b1e6d3c0):
  `commits del scraper al consolidado desde la base: 1239 ; con firma de mezcla: 1` (53b1e6d3c0
  2026-10-24 17:44:20). La firma es exhaustiva sobre los 1.239 commits y mecánicamente necesaria para una mezcla
  del consolidado: para mezclar hay que rebasar sobre OTRO commit del scraper, y los dos agregan líneas al final
  de bitacora_robot.txt, así que el hunk de la bitácora siempre choca y `-X ours` lo descarta (verificado en
  53b1e6d3c0 contra e47b0d5b60). Un solo episodio de mezcla desde la base.

### A6. Chillán 15 y 16 oct, alertas sólo-OCR (05:00, 19:00, 06:18, 18:42): nunca tuvieron fila de tabla; la reposición no puede devolverlas. CONFIRMADO EN PARTE: el barrido exhaustivo (v08b, todas las versiones del 15-oct 03:00 al 17-oct 03:00, sin muestreo horario) iba en 300 de 562 al cerrar, con 16 llaves de Chillán vistas y ninguna a las horas de las alertas sólo-OCR impresas hasta ahí; el autor lo midió con 44 muestras horarias (s07: {}). Gravedad 3.

- v08b_rapido.py sigue corriendo (escribe v08b_resultado.json al terminar; imprime las llaves de Chillán del
  15 y 16 ausentes hoy y las filas a las horas objetivo). Hasta la versión 300 (2026-10-16 04:26 UTC) había
  visto 16 llaves de Chillán de esos días; el consolidado de hoy tiene 29 (s06). El resultado de las horas
  objetivo se lee en la línea "filas a las horas de las alertas solo-OCR" de v08b_salida.txt.
- Observación propia (SOSPECHA, no medida contra MIROVA): las 8 filas sólo-OCR de esos días son
  `ALERTA_SIN_GEOMETRIA_OCR` (`vrp_sin_geometria_propia`, "VRP de la celda de esta pasada en Latest10NTI") o
  `ALERTA_TERMICA_OCR` con hora leída de la imagen, y cada una tiene una fila de tabla a 15 a 25 min con VRP
  parecido: OCR 15-oct 05:00 VIIRS 14.0 MW contra tabla 05:18:01 VIIRS 14.02 ALERTA_TERMICA; OCR 16-oct 12:45
  MODIS 13.0 ("VRP truncado por MIROVA") contra tabla 12:45:00 MODIS 13.63; OCR 16-oct 18:42 VIIRS375 7.5 contra
  tabla 19:00:01 VIIRS375 6.84; OCR 16-oct 06:18 VIIRS 13.0 contra tabla 06:42:01 VIIRS 14.02. Es compatible con
  que sean las MISMAS pasadas con la hora leída gruesa del eje de la imagen, no pasadas que la tabla perdió. En
  cualquier lectura, la conclusión de A6 se sostiene: no hay fila de tabla que reponer.

## 4. Hallazgos propios (resumen)

| ID | Gravedad | Qué | Dónde está la evidencia |
|---|---|---|---|
| V1 | 2 | Una corrida `cancelled` (40116786605) empujó igual; contar escritores por conclusión de la API subestima | gh run view, run_40116786605.log l. 405 |
| V2 | 2 | 2 de las 12 mutaciones se atrapan por `ValueError` de `str.index`, no por aserción; "R3 sin guarda" sólo así | v06_salida.txt |
| V3 | 2 | archivar_evidencia.yml y graficos_completo.yml conservan `-X ours`; no tocan CSV | grep de los yml en main |
| V4 | 2 | Pausar no cancela corridas en vuelo; una vieja puede empujar tras el merge (sin mezclar datos, porque el merge no toca el consolidado) | A7 comm vacío |
| V5 | 3 | 18 de 314 pushes rebasados del OCR (6 % de las corridas) tenían el mismo CSV cambiado por dos corridas solapadas (cron :05 contra despacho :00/:30); con el PR irían a rojo | v07_salida.txt |
| V6 | 1 | El PR baja a 'baja' la confianza del método de grupo en filas futuras; ningún consumidor filtra por eso | diff ocr_utils.py; grep VRP Chile y merger |
| V7 | 0 | CRLF en mi brazo A es artefacto de pandas en Windows | v11 |
| V8 | 2 | La simulación A/B no inserta ninguna pasada nueva (HTML del 22-oct contra CSV del 26-oct) | v10, v11 |
| V9 | 1 | El maestro cambia 28 llaves de OCR a tabla al reponer; efecto esperado | v11 |
| V10 | 1 | 53b1e6d3c0 duplicó 1.565 filas idénticas además de borrar 241 | v13 |
| V11 | 1 | Los registros de Actions son ciegos a los choques que `-X ours` resuelve: no vale un grep de CONFLICT para medirlos | run_40117161109.log l. 398 a 402 |

## 5. Cierre

VERIFICADO LIMPIO: A2, A5, A9 (confirmados con instrumento propio distinto al del autor); A3 y A4 para las
filas existentes y las repuestas (0 llaves perdidas, 0 campos cambiados fuera de los que main ya cambia, reposición
idempotente); A7 (suite re-corrida por mí: 170 y 167 verdes, merges sin archivo en común con main); A8 en su línea
base roja y en las mutaciones de `-X ours`; A10 en lo que afirma (ningún otro workflow escribe los dos CSV); A1 en
el episodio mismo (241, 2 protegidas, 0 en el CSV del PR, == las 241 de s163) y en la firma de mezcla (1 de 1.239).

SIN DATO: si las 18 corridas solapadas del OCR produjeron hunks en conflicto (nunca se
empujó el commit original); si con el orden total del PR esas corridas seguirían chocando; las 8 mutaciones de
módulos Python de s15 (no re-corridas); el 45 % final del barrido exhaustivo del consolidado y el 47 % final del
de Chillán (en curso al cerrar, con sus instrumentos y combinador dejados listos en la carpeta).

QUÉ NO MIRÉ:
- Las 8 mutaciones de módulos Python de s15 (sólo las 4 de workflow, más una propia, se re-corrieron).
- El comportamiento del bucle del PR en Actions real (sólo en repo de juguete y en simulación sin red).
- El OCR con imágenes reales (clon blob:none, sin PNG): el ciclo OCR se simuló sin eventos nuevos.
- Lo que hace MIROVA en latest.php con un sensor nuevo: el PR deja el ciclo en rojo (`TablaInesperada`) para
  cualquier sensor distinto de MODIS, VIIRS, VIIRS375 en una fila chilena; es por diseño, no lo evalué.
- Los consumidores del maestro y de los `registro_<volcán>.csv` (productos de Mirova-v1 que VRP Chile no lee).
- Las 65 filas "Peteroa" que el docstring de reponer_filas.py descarta: no comprobé que no sean pérdidas.
- Si el hueco entre ventanas del escritorio (ventana de v03: 2026-10-20 21:00 a 2026-10-26 12:00) representa el
  año: la tasa de 6 % de corridas solapadas del OCR es de esos 5,6 días.

## 6. Adenda al cierre: barrido exhaustivo del consolidado terminado (v04e_salida.txt)

Los 4 fragmentos de v04d terminaron y el combinador los unió: `pasos evaluados en total: 1239 (esperados 1239)`
(todas las versiones del consolidado en la línea principal de main desde la base c48d24cad8 hasta f5fe3b9a64, sin
muestreo). `pasos con perdidas: [('53b1e6d3c0', 44195, 241)] | con repetidas: [('53b1e6d3c0', 1565)] | con
lineas raras: 0`. `llaves perdidas en algun paso: 241 | repuestas antes de hoy: 0 | siguen ausentes hoy: 241`,
todas perdidas en 53b1e6d3c0; `protegidas ausentes hoy: 2` (Villarrica MODIS 1780084500 2026-05-29 19:55:00 1.83
y Nevados de Chillan VIIRS375 1792820881 2026-10-24 05:48:01 2.36); `ausentes hoy que estan en el archivo de
reposicion de s163: 241 de 241`. Con esto, **A1 pasa a CONFIRMADO entero**: desde la base del PR no hay ninguna
otra pérdida, ni transitoria ni vigente, y la rama s163 repone exactamente lo que falta. El barrido de Chillán
(v08b) iba en 500/562 al cerrar; A6 queda como se dijo arriba.

## 7. Adenda al cierre: barrido exhaustivo de Chillán terminado (v08b_salida.txt)

562 versiones del consolidado entre 2026-10-15 03:01 y 2026-10-17 02:57 UTC, todas leídas (no muestreo horario):
`llaves de Chillan 15-16 oct vistas en alguna version: 29` (las mismas 29 que tiene main hoy), `ausentes hoy en
main: 0`, `filas a las horas de las alertas solo-OCR: {}`. Ninguna versión del consolidado tuvo jamás una fila de
Chillán a las 05:00 ni 19:00 del 15 ni a las 06:18 ni 18:42 del 16, y ninguna fila de Chillán de esos dos días se
perdió en ningún momento. **A6 pasa a CONFIRMADO entero.**
