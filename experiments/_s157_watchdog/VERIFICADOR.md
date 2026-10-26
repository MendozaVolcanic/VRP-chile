# Verificador con contexto limpio: reproc-watchdog por job (S157)

Fecha del servidor al verificar: `Tue, 20 Oct 2026 03:43:29 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`).
Worktree revisado (sólo lectura): `D:\vrp-trabajo\s157-watchdog`, rama `s157-watchdog-por-job`, sin commitear.
Copia de trabajo para correr pruebas: `D:\vrp-trabajo\temporales\verif_s157_watchdog\` (yml, los dos tests, el fixture y `mutaciones.py` copiados; además `casos_borde.py`, `live_jobs_all.tsv` y `live_jobs_latest.tsv` escritos por mí).

## Veredicto por afirmación

### A1. CONFIRMADA
- `python -m pytest -p no:cacheprovider -q tests` en la copia: `26 passed in 1.37s`.
- El fixture es el run real, sin retoques: bajé los jobs en vivo (`gh api --paginate "repos/MendozaVolcanic/VRP-chile/actions/runs/39125546355/jobs?per_page=100"`), 178 jobs, `ids match True 178 178`, `time diffs []` (mismo `started_at` y `completed_at` que el fixture). Con `filter=all` también salen 178 (un solo attempt).
- Duración máxima de un job: 2,861 h (`reproc (NevadosDeChillan, 7, ...)`, `failure`); ningún job con fechas nulas. Distribución: 172 `success`, 6 `failure`.
- El test barre cada hora de la vida del run más las dos horas de los comentarios falsos de #824, con control positivo (un job corriendo desde la creación del run sale `colgada`). `test_job_que_pasa_el_techo_si_es_colgado` comprueba que un job de 8 h sale colgado y es el único nombrado.
- Matiz: el barrido es una reconstrucción a partir de inicio y fin de cada job, no una lectura de la API a cada hora. Como el fixture coincide exacto con la API, la reconstrucción es fiel salvo en cómo GitHub muestra los jobs en cola (ver A2, coincide).

### A2. CONFIRMADA (con dato real)
- `gh api "repos/MendozaVolcanic/VRP-chile/actions/runs/39362883773/jobs?per_page=100"` (NRT en curso, `max-parallel` 8): los jobs `queued` traen `started_at` poblado e igual a su `created_at`, por ejemplo `process (NevadosDeChillan)  queued  2026-10-20T03:16:45Z  2026-10-20T03:16:45Z`; los `in_progress` traen `started_at` 2 s después. O sea que GitHub sí pobla `started_at` en jobs en cola, y el filtro por `status === 'in_progress'` es necesario y correcto. M02 (contar los no completados) queda atrapada por tres tests.
- El run 39363796988 está `pending` con `total_count` 0: un run que espera el grupo de concurrencia no tiene jobs, y el script lo trata como sano (correcto).

### A3. CONFIRMADA
- `lineaProblema` no lleva edades: fallida = nombre + `created_at` + `conclusion` + URL; colgada = nombres de jobs + `started_at` + URL. `test_la_linea_del_aviso_no_cambia_con_la_hora` y la simulación punta a punta (log2 y log4 sin comentario) lo prueban; M07 y M08 atrapadas.
- `debeComentar` filtra por `MARCA` y toma el último; los comentarios de la API vienen en orden ascendente de id (comprobado en #824: ids 6256387083 < ... < 6279823950 en orden de fecha). Comentarios viejos sin marca y humanos no cuentan (casos en `test_no_repite_un_comentario_igual`; M10 atrapada).
- Excepción menor, ver H4.

### A4. CONFIRMADA (en simulación; el rojo real descansa en la semántica de `core.setFailed`)
- `test_simulado_502_no_cierra_el_issue`: con 502 en la lectura de jobs, `cerrados == []` y `fallo` contiene «sin dato». Control `test_simulado_sin_problemas_cierra`: con jobs legibles sí cierra. M04, M13 y M15 atrapadas.
- Que el job de Actions quede en rojo depende de `core.setFailed` (pone el código de salida 1); en la simulación `core` es falso. No lo vi fallar en Actions real.

### A5. CONFIRMADA (por código fuente)
- `action.yml` de `actions/github-script@v7` declara el input `retries` (default `"0"`) y `retry-exempt-status-codes` (default `400,401,403,404,422`).
- `src/retry-options.ts@v7`: con `retries > 0` devuelve `{enabled: true, doNotRetry: [...]}` y `request.retries = retries`; `src/main.ts@v7` construye `getOctokit(token, opts, retry, requestLog)`.
- `@octokit/plugin-retry` v6.0.1, `src/error-request.ts`: `if (error.status >= 400 && !state.doNotRetry.includes(error.status))` reintenta, con espera `(retryCount+1)^2` s. Un 502 se reintenta 3 veces. `paginate` llama a `octokit.request` por página, así que cada página hereda los reintentos.
- Límite: un error de red sin `status` (ECONNRESET) no se reintenta (no cumple `>= 400`). Queda como SIN DATO, que es el comportamiento seguro.
- Comandos: `gh api repos/actions/github-script/contents/action.yml?ref=v7`, `.../src/retry-options.ts?ref=v7`, `.../src/main.ts?ref=v7`, `gh api "repos/octokit/plugin-retry.js/contents/src/error-request.ts?ref=v6.0.1"`.

### A6. CONFIRMADA (por código fuente y forma real de la respuesta)
- La respuesta real de jobs tiene exactamente las claves `['total_count', 'jobs']` (`gh api ".../runs/39363796988/jobs?per_page=1"`).
- `@octokit/plugin-paginate-rest` v9.2.1 (la línea que trae `@actions/github` 6, dependencia de github-script v7): `iterator.ts` pasa cada respuesta por `normalizePaginatedListResponse`, que si hay `total_count` y no hay `url` borra `total_count`, toma `Object.keys(data)[0]` (acá `jobs`) y lo pone como `data`; `paginate.ts` hace `results.concat(result.value.data)`. Resultado: arreglo plano de jobs, `Array.isArray` da true.
- No ejecuté la librería real contra la API (eso requería bajar paquetes de npm, no lo hice sin permiso). Los tests simulan `paginate` devolviendo un arreglo, o sea que asumen A6; si A6 fuera falsa, ningún test lo vería. La lectura del código fuente cubre ese hueco, pero conviene mirar el primer run real del watchdog tras el merge: con el reproceso de Chillán en curso, el log debe decir «sin problemas» o comentar, y NO «sin dato de jobs». Caso borde verificado: si `jobs` llegara como objeto `{total_count, jobs}`, `evaluarCorrida` da `sin_dato` (falla ruidosa y segura, no silenciosa).

### A7. CONFIRMADA
- Re-corrí `python experiments/_s157_watchdog/mutaciones.py` en la copia: salida idéntica a `mutaciones_salida.txt` (BASE 0 y 0; M00 `CAIDA` con 20 caídas; M01 a M18 `ATRAPADA`; `TOTAL 19: atrapadas=18 caidas=1 vivas=0`).
- La regla de conteo en `correr()`: un fallo cuenta como caída si es `error`, si su texto contiene `out.returncode == 0` (la aserción de los ayudantes que lanzan node) o si no contiene `AssertionError` (por ejemplo, un `JSONDecodeError`). Sólo las fallas por aserción de comportamiento cuentan como atrapadas, y M00 demuestra que una caída pura no se cuenta como atrapada.
- Matiz: M16 (`retries: 0`) y parte de M17 sólo los atrapan aserciones estáticas sobre el texto del yml (`int(retries) >= 3`, regex de `paginate(`). Son atrapadas legítimas según la regla, pero no prueban comportamiento: que los reintentos funcionen lo sostiene A5, no la batería.

## Hallazgos propios

**H1 (gravedad 2). El mensaje de cierre afirma algo falso.** Al no haber problemas, el script comenta «Sin reprocesos fallidos ni jobs colgados en los ultimos 14 dias. Cerrando.». Pero sólo mira la ÚLTIMA corrida terminada (`runs[0]`) y las que están en curso. Hoy mismo `reproc-chunked.yml` tiene `39363796988 pending`, `39363774747 in_progress` y `39125546355 completed failure` (creada el 2026-10-18, dentro de los 14 días): esa falla no se reporta porque hay corridas más nuevas, y si cerrara ahora el texto diría que no hubo fallas en 14 días. El comentario de cabecera repite la imprecisión («el workflow volvio a correr en verde, o la falla envejecio»): en realidad también cierra cuando la corrida más nueva sólo está en cola o corriendo. El comportamiento de cerrar es igual al viejo; lo que empeora es el texto. Arreglo sugerido: algo como «La ultima corrida de cada reproceso no fallo y ningun job pasa el techo de 6 h. Cerrando.» y ajustar la cabecera.

**H2 (gravedad 2). Un re-run de una corrida vieja queda invisible.** `evaluarCorrida` descarta por `created_at` del run, que no cambia al relanzar. Caso probado en `casos_borde.py`: run creado el 2026-09-30, re-run (`run_attempt: 2`, `run_started_at` 2026-10-20T02:00Z) con un job en curso hace 9 h: devuelve `null`. Con la convención del proyecto de relanzar trozos caídos, un «re-run failed jobs» de un run de más de 14 días no avisaría ni si falla ni si se cuelga. Ojo además que `listWorkflowRuns` ordena por creación, así que ese run tampoco estaría entre los 3 primeros. Era así antes del cambio, pero el cambio declara medir por job y deja esta puerta. Arreglo barato: usar `r.run_started_at || r.created_at` para la ventana.

**H3 (gravedad 3). Cobertura que se pierde respecto del watchdog viejo.** Ahora nunca salen avisados (todos dan `null` en `casos_borde.py`): un run `waiting` por aprobación de environment (hoy ningún `reproc-*` usa `environment:`, sólo `pages-deploy.yml`), un run huérfano `in_progress` con todos sus jobs terminados, y un run con jobs en `queued` indefinidamente (runner que no llega). El viejo los habría marcado a las 7 h. Es una decisión de diseño defendible (en cola detrás de `max-parallel` es normal), pero conviene decirla en voz alta o poner un techo amplio por edad del run (por ejemplo 72 h sin ningún job `in_progress`). SIN VERIFICAR cuánto tarda GitHub en cancelar un job en cola en runners alojados.

**H4 (gravedad 3). La dedup confía en la marca, no en el autor.** Un comentario humano que contenga el texto crudo `<!-- reproc-watchdog -->` (copiar y pegar el markdown del aviso) pasa a ser «el último del watchdog» (`humano_cita: true` en `casos_borde.py`) y provoca un comentario de más. Reforzar con `c.user && c.user.login === 'github-actions[bot]'` lo cierra. Poco probable.

**H5 (gravedad 3). Un camino donde el ruido podría volver.** Con problemas reales presentes y un SIN DATO intermitente (502 que sobrevive los 3 reintentos una hora sí y otra no), el cuerpo alterna entre llevar y no llevar la línea SIN DATO, y cada alternancia es un comentario nuevo. Los reintentos lo hacen raro. Un 404 en jobs (run borrado entre listar y leer) también deja un SIN DATO y un rojo de una hora; transitorio.

**H6 (gravedad 3). `per_page: 3`.** Si hay más de 3 corridas recientes y una de las más viejas sigue en curso (relanzar trozos uno por uno), su job colgado no se ve. Hoy hay 2 relanzamientos; con 3 o más se pierde la cuarta.

**Qué pasará en el primer run tras el merge (razonado, no ejecutado).** `reproc-s151-ab-caja.yml` (vivo en main) tiene su última corrida `38698329137 failure` del 2026-10-15T07:22:38Z, dentro de los 14 días. Habrá un problema, así que #824 (abierta, 28 comentarios, ninguno con marca) recibe UN comentario nuevo (se compara contra el cuerpo viejo de la issue) con esa falla; `reproc-chunked` no aparece porque su última corrida está en cola o corriendo. Las horas siguientes, silencio. #824 se cerraría hacia el 2026-10-29 07:22 UTC, cuando esa falla salga de la ventana, con el texto de H1.

**Menor.** `tests/test_reproc_watchdog_vivos_s133.py` conserva 3 guiones largos (líneas 2, 6 y 7), anteriores a este cambio; los archivos nuevos y el yml dan 0.

## Lo que no miré
- No ejecuté el script en Actions real ni la librería Octokit real (A6 y el rojo de A4 quedan por código fuente y simulación).
- No verifiqué cómo se comporta `filter: 'latest'` con un «re-run failed jobs» en curso (qué jobs del attempt anterior aparecen); para el criterio sólo importan los `in_progress`, así que el riesgo es bajo.
- No revisé el resto del yml fuera del bloque `script` más allá del `name:` y los comentarios de cabecera.
- No corrí la suite completa del repo; sólo los dos tests del watchdog (nadie más lee `reproc-watchdog.yml`: `grep -rl` en `tests/`, `scripts/`, `.github/`, `docs/*.md` sólo da esos dos tests y el yml).
