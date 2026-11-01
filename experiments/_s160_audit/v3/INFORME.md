# V3: verificación de los 9 hallazgos de F3 (dependencias externas con fecha de vencimiento)

## 1. Encabezado

- Hora del servidor: inicio 2026-10-22 03:41:57 UTC (cabecera `Date` de api.github.com); cierre 2026-10-22 04:01:24 UTC (cabecera `Date` de github.com) más el tiempo de redacción.
- Commit medido: `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956` (instantánea `D:\vrp-trabajo\temporales\s160_audit\main\`). `origin/main` ya avanzó a `954f0353` durante la sesión; no lo usé. PR #889 medido en `d0968e389`; rama del cese de Suomi NPP medida en `origin/s159-cese-snpp` = `f995d7101` (fechada abajo).
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo (el de la sesión).
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v3\`. Pesado en `D:\vrp-trabajo\temporales\s160_audit\v3\` (7,8 MB).
- `caminos.md` escrito y sellado antes de abrir los archivos citados (sha256 `96c298f7...`, 03:42:30 UTC).
- Plan: `git diff 06e0fad3b -- docs/PLAN_AUDITORIA_S160.md` muestra sólo §11.2b y una línea «PR del preámbulo ... #891»; `git log -L` atribuye esa línea al mismo commit `60762a939`. No toca F3. Sin hallazgo.
- Llamadas a la API de GitHub: 4 (2 de hora, `gh pr list` de la rama, `gh run view --log` de un run). CMR: 14 búsquedas públicas, sin autenticación. Web: 1 búsqueda y 2 páginas de LAADS (WebFetch).
- Qué NO miré: el contenido real del secret `EARTHDATA_TOKEN` (no tengo acceso; su fecha de vencimiento queda SIN DATO); corridas reales de `nrt-healthcheck.yml`; `nrt-retry.yml` y `reproc-*.yml` frente a token vacío; los planes de adquisición de Terra y Aqua (fin de misión); el contenido de MIROVA posterior al cese de Suomi NPP; los informes de F3 (no los abrí, por regla).

## 2. En una pantalla

- 241 se sostiene por otro camino (`run_pipeline.main` entero, parche en la capa HTTP de CMR, ventana S157 incluida): una plataforma o MODIS entero que CMR deje de servir da «Cobertura: completa» y código 0, incluso con `--estricto-cobertura`. Ningún vigilante de main cuenta por plataforma. Cae una parte: «todo vacío» sí lo ve el healthcheck a 48 h. Gravedad 4, no 5.
- Hallazgo propio V3-01 (gravedad 4): una alerta protegida de MIROVA sin ningún record nuestro (`sin_record`) no genera flag en el auto-audit, justo el caso de una plataforma callada.
- 242: «sin push» quedó REFUTADO 25 min después de que el auditor mirara: la rama se subió a las 03:33:02 UTC y es el PR #892 (abierto, sin merge). Su vigilante sí alarma por SNPP, NOAA-21 o MODIS callados (medido); el «completa» del NRT sigue igual.
- 243, 244, 246 y 247 CONFIRMADOS; 245 y 252 CONFIRMADOS EN PARTE (245: 1 de los 7 encogimientos no pierde filas; las auditorías ya usan la unión histórica, el tablero no). 248 CONFIRMADO y peor: el medidor de cadencia ignora `workflow_dispatch`, así que no puede ver la muerte del disparador externo.
- Informe: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v3\INFORME.md`.

## 3. Veredictos sobre la lista de F3

Cada medición lleva las dos preguntas del instrumento: (P1) si lo medido estuviera roto, ¿lo vería?; (P2) si el instrumento estuviera muerto, ¿el resultado sería distinto?

### 241: plataforma o colección que calla en CMR = «Cobertura: completa», código 0
- VEREDICTO: **CONFIRMADO EN PARTE**. GRAVEDAD V3: **4** (auditor: 5).
- Lectura del código (SHA_MAIN): `pipeline/fetch.py:799-800` devuelve `[]` sin `_registrar_falla` cuando todas las versiones responden vacío; `:1087-1088` hace `continue`; la búsqueda por ventana hace lo mismo (`:645-646`, días pendientes a `[]` sin falla); `:218-225` NOAA-21 sólo `"2.1"`; `:187-194` MODIS sólo `6.1`/`6.1NRT`; `scripts/run_pipeline.py:416-417` imprime «completa» si no hay fallas y `:441` devuelve 0 o 3 sólo según fallas.
- Medición por otro camino: `v3_e2e_cmr_http.py` corre `scripts/run_pipeline.py::main()` entero (fechas por defecto del NRT, 2026-10-15 a 2026-10-22, con la ventana S157 activa) y parcha `requests.Session.get` contra `cmr.earthdata.nasa.gov/search/granules`, así que earthaccess, `get_results` y la búsqueda por ventana corren de verdad. Salida `v3_e2e_cmr_http_salida.txt`:
  - todo vacío: «Cobertura: completa», código 0, y **también 0 con `--estricto-cobertura`**; 132 consultas, 22 productos, 0 consultas fuera del parche.
  - control (HTTP 500 sólo en VNP*): «Cobertura INCOMPLETA: 16», 0 normal y 3 estricto.
  - P1: el control demuestra que el instrumento ve una falla; P2: sin el parche habría consultas no parchadas (0). Primera corrida descartada: mi respuesta falsa no traía la cabecera `CMR-Hits` y la ventana se apagó por `KeyError` (64 fallas espurias); corregido y repetido, la salida guardada es la buena.
- Segundo camino buscado (¿alguien más lo ve?), leído en SHA_MAIN:
  - `nrt-healthcheck.yml:53` (48 h) y `nrt.yml:271-314` (A57, 72 h): edad del último record por volcán, de cualquier sensor.
  - `frontend/index.html:1769-1865`: frescura por volcán, cualquier record.
  - `scripts/auto_audit_weekly.py:344-359` (cobertura por días con cualquier record), `:362-379` (recall por bucket de sensor; `noches_sin_datos` se informa y no dispara flag: `:742-753`), `:796` y `:827` (ver V3-01).
  - Ninguno cuenta por plataforma. Una plataforma callada deja fresco al volcán por las otras. MODIS entero callado: el bucket MODIS queda en «noches sin datos», sin flag.
- Qué cae: «todo vacío» deja de producir records y lo ve el healthcheck a 48 h y A57 a 72 h (rojo). El job dice «completa», pero el silencio no dura.
- Por qué 4 y no 5: con una plataforma callada el tablero sigue publicando las otras; lo que se pierde en silencio son las pasadas (y las alertas) que sólo esa plataforma ve. Suomi NPP también sale de MIROVA, así que para la réplica el cese anunciado es neutro; el daño silencioso real está en NOAA-20, NOAA-21 o MODIS si callan sin aviso.
- Atenuante en curso: el vigilante del PR #892 sí lo ve (ver 242).
- Nota de instrumento: `f3/simular_dependencias.py` llama a `fetch_for_volcano` sin `configurar_ventana`, o sea no ejercita la búsqueda por ventana que usa el NRT real. Re-corrido (`v3_rerun_scripts_auditor_salida.txt`) reproduce sus filas; mi camino extremo a extremo confirma que la ventana no cambia la conclusión.

### 242: el arreglo del cese de Suomi NPP vive en una rama local sin push
- VEREDICTO: **CONFIRMADO EN PARTE**. «Sin push» REFUTADO a la hora de esta verificación. GRAVEDAD V3: **3** (auditor: 4).
- Fechado: reflog del worktree `C:\vrp-trabajo\s159-instrumentos`: `refs/remotes/origin/s159-cese-snpp@{2026-10-22T00:33:02-03:00}: update by push` (03:33:02 UTC); `gh pr list --head s159-cese-snpp`: PR **#892**, OPEN, creado 2026-10-22T03:33:12Z. `git ls-remote` a las 03:48 UTC: `f995d7101 refs/heads/s159-cese-snpp`. El auditor miró a las 03:08 UTC, cuando era cierto.
- Contenido, leído en `origin/s159-cese-snpp`: `scripts/vigilar_plataformas.py:84` `VENTANA_H = 72`; `nrt-healthcheck.yml` +280-302 agrega el paso `python scripts/vigilar_plataformas.py --issues`; `frontend/cese_plataformas.js` l. 28-29 `CESE_UTC = "2026-11-02T13:00:00Z"`; `scripts/ceses_esperados.json` con SNPP. El diff no toca `pipeline/` ni `scripts/run_pipeline.py`: el «completa» del NRT sigue (confirmado).
- Medición propia (`v3_vigilante_892.py` sobre los 71.968 records Tier A de SHA_MAIN, último 2026-10-21 08:10 UTC, ahora simulado 2026-10-22 02:00): control sin quitar nada = `ok`; SNPP callado desde el 19-oct = `alarma`; NOAA-21 callado = `alarma`; MODIS entero callado = `alarma`; SNPP callado con el cese ya cumplido = `ok` (informativo). P1 y P2 cumplidas (control y escenarios difieren).
- Matiz a «deja fuera la versión de colección»: no cambia la versión pedida, pero un cambio de versión de NOAA-21 callaría la plataforma y el vigilante alarmaría a las 72 h (medido con NOAA-21). Lo que sí queda fuera: el mensaje del job y la referencia.
- Matiz nuevo: el paso corre en `nrt-healthcheck.yml`, cron diario 12:00 UTC; una plataforma que calla sin aviso alarma entre 72 y unas 96 h después.

### 243: MODIS Colección 6.1 con decomiso anunciado y no ejecutado
- VEREDICTO: **CONFIRMADO**. GRAVEDAD V3: **3** (auditor: 4).
- Fuente: LAADS DAAC, alerta 2026-03-17 «Version 7.0 MODIS Calibrated Radiances and Geolocation Data Products: Now Available», leída en TEXTO a través de WebFetch (resumidor, no el HTML directo): «The Version 6.1 MODIS Level-1 collection will remain available for the next six months» y «before being decommissioned on September 30, 2026.» No dice nada de LANCE para la colección 7 (`v3_fuentes_externas_salida.txt`).
- CMR, por otro camino que el auditor (metadatos UMM de colección y conteo de gránulos sobre Villarrica en tres ventanas): v6.1 LAADS sigue ACTIVE, sin fin temporal ni texto de decomiso; MOD021KM v6.1 da 9, 8 y 7 gránulos el 20-22 sep, 5-7 oct y 15-17 oct, contra 9, 8 y 8 de v7: **el Standard 6.1 se sigue produciendo tres semanas después de la fecha**. No existe colección 7 NRT bajo esos nombres (3 colecciones por short_name). `v3_cmr_granulos_modis_salida.txt`.
- Código: `fetch.py:187-194` sólo pide 6.1; `store.py:683-684` hace el upgrade nrt a standard; `product_version` sólo lo leen el pipeline y `scripts/reparar_product_version_modis_s133.py` (grep en `scripts/`, `.github/workflows/`, `pipeline/`): nadie mide la proporción.
- Medición propia (`v3_proporcion_nrt_modis.py`, Tier A de SHA_MAIN): MODIS 0,0 % nrt de junio a septiembre; octubre 0,8 % (4 de 479, todos del 20-oct, a la espera de upgrade). La serie vería el decomiso (P1); el campo existe en todos los records (P2, columna `sin_campo` vacía). Hoy está sano.
- Por qué 3: hoy no hay efecto; si LAADS ejecuta el decomiso, MODIS sigue entrando por el NRT 6.1 (degradación sin aviso, no silencio); el silencio total exige además que LANCE cierre 6.1, y eso cae en 241.

### 245: la copia horaria de la tabla de MIROVA acepta encogimientos
- VEREDICTO: **CONFIRMADO EN PARTE**. GRAVEDAD V3: **3** (auditor: 4).
- Código: `sync-mirova-csv.yml:75-80` (cmp y mv, sin tamaño ni cabecera) contra `:99-116` del OCR (vacío, cabecera, no encogerse; rojo al final, `:198-205`); `:172` `WARN: rebuild ... (continuing)`.
- Medición por otro camino (`v3_encogimientos_todos.py`): toda la historia, 1.238 commits de `latest_consolidado.csv` desde 2026-05-23 hasta SHA_MAIN, por **clave de fila** (fecha UTC, volcán, sensor), no por líneas. Resultado: los mismos 7 encogimientos (ninguno antes del 19-ago); **uno es benigno** (`0e2dff5b2`, 2026-08-19: baja 659 líneas y no sale ninguna clave); los otros 6 sacan 194 a 630 claves cada uno. **1.948 claves salieron y no volvieron hasta SHA_MAIN**, 91 con ALERTA, 14 de ellas de 1 MW o más. P1: el par de commits benigno muestra que la medición distingue «baja de líneas» de «pérdida de filas»; P2: 1 sola cabecera y n>0 en cada commit.
- Al tablero: `git show d516b9d8c:data/mirova/Lascar.json` no tiene la alerta Láscar MODIS 2026-02-09 07:20 UTC (1,64 MW), perdida en `0c8848ff9`. Otras perdidas reaparecen como `source: ocr` (Láscar MODIS 2026-02-14 01:40, PCC 2026-01-23 06:00).
- Lo que cae: las auditorías ya no dependen de la copia sola. `auto_audit_weekly.py:54` y `:69` cargan `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv` (2.145 filas, 102 ALERTA según `procedencia.json`, hasta 2026-10-19). La pérdida queda en la capa de referencia del tablero y en cualquier script que lea `latest_consolidado.csv` sin la unión.

### 244: PR #889 cambia «completa» por «NO COMPLETA», pero se satura
- VEREDICTO: **CONFIRMADO**. GRAVEDAD V3: **2** (auditor: 3).
- Código (`d0968e389`): `pipeline/fetch.py:745` `TIPOS_INCIDENCIA = {"sin_granulos": False, ...}`; `:766-770` `dia_incompleto`; `:1119-1121` registra `dia_parcial` para el día en curso; `scripts/run_pipeline.py:459-460` «Cobertura NO COMPLETA»; `:481-482` código 3 sólo en estricto.
- Medición por otro camino (`v3_e2e_cmr_http.py` sobre un árbol de `d0968e389` extraído con `git archive`): con las fechas del NRT, todo vacío da «NO COMPLETA: 65 incidencias» (64 `sin_granulos` más 1 `dia_parcial`), código 0, y 3 en estricto **sólo por el día parcial**; con `--date 2026-10-10` (día cerrado) todo vacío da «NO COMPLETA: 8», **código 0 también en estricto**. El NRT siempre procesa el día en curso (`default_date_window`), así que el encabezado dice NO COMPLETA en toda corrida. Control: HTTP 500 en SNPP da INCOMPLETA y 3 en estricto en los dos casos. `v3_e2e_cmr_http_889_salida.txt`.
- Por qué 2: el PR no está en main; cambia un «completa» falso por un «NO COMPLETA» constante, que tampoco informa.

### 246: la sincronización horaria corre 5,2 veces por día y pierde 8 de 50
- VEREDICTO: **CONFIRMADO** (la causa de las que faltan, SOSPECHA). GRAVEDAD V3: **2** (auditor: 3).
- Insumos (`runs_sync-mirova-csv.tsv`, 50 corridas, 2026-10-12 07:19 a 2026-10-21 23:17 UTC): 5,17 por día, 42 success, 8 cancelled (todas canceladas a los :10 o :30, compatible con ser desplazadas en el grupo `push-main`, `sync-mirova-csv.yml:55`). Hueco máximo entre fines de corridas success: 22,3 h (desde 2026-10-17 00:00).
- Otro criterio: commits reales de `latest_consolidado.csv` en `origin/main` desde 2026-10-12 07:00: 42 commits, 4,34 por día, hueco máximo 22,3 h (mismo episodio). `v3_cadencia_commits_consolidado_salida.txt`. El auditor da 22,7 h midiendo entre creaciones; misma conclusión.
- «Invisible bajo 7 días»: `auto_audit_weekly.py:109` `MAX_GT_STALE_DAYS = 7`. Confirmado.
- SOSPECHA: de las 24 por día que pide el cron, unas 19 no aparecen en la lista ni como canceladas; eso apunta a eventos `schedule` que GitHub no crea, no al grupo `push-main`. No lo medí (requiere más llamadas a la API).
- Por qué 2: retrasa la capa de referencia del tablero menos de un día; MIROVA sigue publicando en su propio sitio.

### 247: EARTHDATA_TOKEN
- VEREDICTO: **CONFIRMADO** (fecha de vencimiento SIN DATO). GRAVEDAD V3: **3** (igual).
- `token_edad.py:43-50`: vacío, basura o JWT sin `exp` dan `desconocido` (mi prueba `v3_token.py`: vacío y basura `desconocido`; +5 d `renovar`; +30 d `ok`; −1 d `vencido`). `nrt-healthcheck.yml:316-318` (comentario) y el paso siguiente: `desconocido` sólo va al resumen.
- `nrt.yml:172-174` pasa token, usuario y clave sin guarda; `experimental-diario.yml:63-66` sí tiene la guarda. `fetch.py:318-345`: con token vacío, 8 intentos de `earthaccess.login(strategy="environment")` con esperas que suman 1.300 s. Medido con `auth()` de SHA_MAIN, sin netrc y con el probe forzado arriba: token vacío = 8 logins, 1.300 s, `RuntimeError: invalid_credentials`; control con token = 1 login, 0 s.
- Ampliación (fundida aquí, ver V3-03): la excepción de `auth()` sale de `process_date` (try/finally, `run_pipeline.py:198-368`), el job muere en la primera fecha; pero la matriz corre con `max-parallel: 8` (`nrt.yml:80`): hasta 64 logins simultáneos y 88 por corrida de 11 volcanes.
- No es silencioso: el job termina con traceback (rojo) y el healthcheck lo ve a 48 h. Por eso 3.
- Fecha de vencimiento: `secretos_nombres_y_fecha.txt` da el secret actualizado el 2026-10-08T18:07:05Z; con vida de 60 días (`token_edad.py:3`) vencería hacia el 2026-12-07 18:0x, compatible con lo que dice el auditor. No leí el JWT: SIN DATO.

### 248: la cadencia del NRT depende de cron-job.org
- VEREDICTO: **CONFIRMADO, y peor de lo descrito**. GRAVEDAD V3: **2** (auditor: 3).
- Insumos (`runs_nrt.tsv`, 50 corridas, 2026-10-19 03:23 a 2026-10-22 03:10 UTC): schedule 14 corridas, 4,97 por día, atraso mediano 68 min (máx 115); `workflow_dispatch` 36 corridas, 12,2 por día, todas creadas al minuto :10. `v3_cadencia_nrt_salida.txt`.
- `medir_cadencia_cron.py:63` descarta todo lo que no sea `schedule`, así que el disparador externo (dispatch) no entra en la medición: si cron-job.org muere, la cifra que mide no cambia. `:143-146` sale 0 siempre; `cadencia.json` sólo aparece en `nrt-healthcheck.yml:304` y ningún paso lo lee (grep en `.github/workflows/`). Nadie abre issue por cadencia.
- `REGISTRO_CREDENCIALES.md` §2 fila 31 (TEXTO): el PAT figura «⚠️ **sin vencimiento** (dicho por Nicolás el 2026-10-17)» y la misma fila dice que si falla «la latencia del NRT vuelve a la del cron de GitHub ... **sin pérdida de datos**».
- Por qué 2: cada corrida reprocesa 7 días; se pierde puntualidad, no alertas.

### 252: bibliotecas sin fijar (earthaccess)
- VEREDICTO: **CONFIRMADO EN PARTE**. GRAVEDAD V3: **2** (auditor: 3, SOSPECHA).
- `requirements.txt:1` `earthaccess>=0.9.0` (en `d516b9d8c`); `nrt.yml:143` `pip install earthaccess ...` sin versión. Última publicada: 0.19.0 (`pip index versions`); el NRT instala hoy **0.17.0** (log de `nrt.yml` run 39709899515, 2026-10-22 02:10 UTC). La razón por la que pip elige 0.17.0 no la medí (SOSPECHA: restricción de Python 3.11 o de dependencias).
- `tests/test_fetch_credential_dead_s123.py:43-46` usa una réplica del envoltorio, no earthaccess real.
- Medición propia (`v3_credencial_envoltorio.py`, earthaccess 0.17.0 real con 401 de CMR): `_is_credential_dead` da `(True, 401)` con cuerpo «Token has expired» y con cuerpo neutro. Envoltorios simulados: sin `__cause__` pero con «Token has expired» en el cuerpo: `(True, None)` (lo salva la regex, `fetch.py:430`); sin `__cause__` y cuerpo neutro: `(False, None)`; control ReadTimeout: `(False, None)`.
- Lo que cae: «si cambia el envoltorio, la credencial muerta vuelve a WARN» sólo vale si además el cuerpo deja de nombrar el token. Hoy el NRT corre la versión para la que se escribió el código.

## 4. Hallazgos propios

### V3-01
- TÍTULO: Una alerta protegida de MIROVA sin ningún record nuestro (`sin_record`) no genera flag en el auto-audit semanal
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:796` (asigna `sin_record`) y `:827` (`flags_protegidas` sólo marca `sin_publicar`); también `:742-753` (`noches_sin_datos` no dispara flag)
- QUÉ PASA: si un satélite deja de entregar y MIROVA alerta 1 MW o más en esa pasada, nosotros no tenemos el record. El audit la lista como «no miramos» y no levanta flag. Es justo la situación de 241 (plataforma o MODIS callado), y es la única vigilancia que mira alertas protegidas.
- CÓMO SE VE EN EL DASHBOARD: invisible; el issue del audit semanal no la menciona.
- CÓMO REPRODUCIRLO: `python -I C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v3\v3_protegida_sin_record.py D:\vrp-trabajo\temporales\s160_audit\main` (Láscar MODIS 2026-11-05 05:00 UTC, 2,5 MW, detector K): `sin_record -> []`, `sin_publicar -> [flag]`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 4 (apaga la vigilancia de protegidas en el caso de una plataforma callada; combinado con 241 en MODIS, una protegida se pierde sin que nadie lo note)

### V3-02
- TÍTULO: El medidor de cadencia ignora `workflow_dispatch`: no puede ver la muerte del disparador externo, y su JSON no lo lee nadie
- ARCHIVO:LÍNEA: `scripts/medir_cadencia_cron.py:63` y `:143-146`; `.github/workflows/nrt-healthcheck.yml:301-305`
- QUÉ PASA: hoy 12 de las ~17 corridas diarias del NRT vienen de cron-job.org por dispatch. El medidor sólo cuenta `schedule`, así que si el externo cae la medición queda idéntica; además sale 0 siempre y `cadencia.json` no tiene consumidor.
- CÓMO SE VE EN EL DASHBOARD: invisible; la tarjeta de frescura muestra la última pasada más vieja, sin explicar por qué.
- CÓMO REPRODUCIRLO: `grep -n 'event") != "schedule"' D:\vrp-trabajo\temporales\s160_audit\main\scripts\medir_cadencia_cron.py`; `grep -rn cadencia.json D:\vrp-trabajo\temporales\s160_audit\main\.github\workflows\`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 2 (fundido con 248)

### V3-03
- TÍTULO: Con `EARTHDATA_TOKEN` vacío, la matriz del NRT multiplica los logins con el par vencido: hasta 64 simultáneos y 88 por corrida
- ARCHIVO:LÍNEA: `pipeline/fetch.py:318-345`; `.github/workflows/nrt.yml:80` (`max-parallel: 8`) y `:172-174`
- QUÉ PASA: cada job hace 8 intentos en 1.300 s antes de morir; 8 jobs a la vez repiten eso contra la misma cuenta, lo que agrava el bloqueo A71.
- CÓMO SE VE EN EL DASHBOARD: datos que dejan de llegar; el NRT queda en rojo.
- CÓMO REPRODUCIRLO: `python -I C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v3\v3_token.py D:\vrp-trabajo\temporales\s160_audit\main` (8 logins, 1.300 s por job) y `grep -n max-parallel ...\nrt.yml`
- CONFIANZA: CONFIRMADO el conteo por job; SOSPECHA el efecto exacto sobre la cuenta (no probé contra Earthdata, por regla)
- GRAVEDAD: 3 (fundido con 247)

### V3-04
- TÍTULO: El simulador de F3 no ejercita la búsqueda por ventana que usa el NRT real
- ARCHIVO:LÍNEA: `experiments/_s160_audit/f3/simular_dependencias.py` (llama a `fetch.reiniciar_ventana()` y a `fetch_for_volcano` sin `configurar_ventana`; `run_pipeline.py:537` sí la configura)
- QUÉ PASA: el instrumento mide el camino por día; para los días viejos el NRT usa `_desde_ventana`. Mi corrida extremo a extremo muestra que la conclusión no cambia.
- CÓMO SE VE EN EL DASHBOARD: invisible (defecto de instrumento, no del sistema)
- CÓMO REPRODUCIRLO: comparar `v3_e2e_cmr_http_salida.txt` (diag `SEARCH_VENTANA ...`) con `v3_rerun_scripts_auditor_salida.txt` (sin líneas de ventana)
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

## 5. SEGUIMIENTOS (fuera de eje)

- LAADS lista «Terra MODIS Acquisition Plan Through December 2025» y «Aqua MODIS Acquisition Plan Through August 2026» (títulos vistos vía WebFetch). MODIS sigue entregando (gránulos hasta el 20-oct), pero el fin de misión de Terra y Aqua es otra dependencia con fecha que no está en la lista de F3. Confianza: SOSPECHA.
- `scripts/rebuild_mirova_from_consolidado.py` reconstruye la capa de MIROVA del tablero sólo desde la copia y el OCR, sin la unión histórica que ya usa el audit; por eso la alerta Láscar MODIS 2026-02-09 07:20 (1,64 MW) falta en `data/mirova/Lascar.json`. Confianza: CONFIRMADO para ese caso.

## 6. VERIFICADO LIMPIO

- Plan §3 F3 sin cambios desde el sello: `git -C C:\vrp-trabajo\s159-pruebas diff 06e0fad3b -- docs/PLAN_AUDITORIA_S160.md` y `git log -L` (todo es de `60762a939`). Vara: el texto sellado.
- Upgrade NRT a Standard de MODIS funcionando hoy: `v3_proporcion_nrt_modis.py` (0 % nrt en jun-sep). Vara: `store.py:683-684`.
- Fallas de búsqueda reales (HTTP 500) sí se registran y dan INCOMPLETA y código 3 en estricto, por día y por ventana: control de `v3_e2e_cmr_http.py`. Vara: `run_pipeline.py:441`.
- Detector de credencial muerta con earthaccess 0.17.0 real: `(True, 401)` con cualquier cuerpo. Vara: `fetch.py:437-452`.
- `token_edad.py` clasifica bien ok, renovar y vencido con JWT sintéticos. Vara: `DIAS_AVISO = 10`, `:27`.

## 7. SIN DATO

- Fecha exacta de vencimiento del `EARTHDATA_TOKEN` (no leí el secret).
- Causa de las ~19 corridas diarias de `sync-mirova-csv.yml` que no aparecen (sin más llamadas a la API).
- Si MIROVA seguirá publicando MODIS tras el decomiso de 6.1 (pasándose a C7): decide si 243 y V3-01 tocan la réplica.
- Por qué el NRT instala earthaccess 0.17.0 y no 0.19.0.

## 8. FUERA DE ALCANCE

- Arreglos (mergear #892, guarda de token en `nrt.yml`, validación de tamaño en la copia del consolidado, flag para `sin_record`): los decide quien orquesta.
- Corridas reales de workflows y autenticación contra Earthdata (prohibidas por la tarea).
