# F4T (S175): qué hace cada workflow el día que EARTHDATA_TOKEN falte o venza

## 1. Encabezado

- Fecha y hora del servidor: `Sat, 07 Nov 2026 04:10:45 GMT` (insumo `C:\Users\nmend\vrp-temporales\s175_audit\insumos\hora_servidor.txt`; no gasté una llamada en repetirla). Reloj local al medir: madrugada del 2026-11-08 (hora de Chile); los `[diag ...Z]` de los logs dicen 04:19 a 04:27 UTC del 2026-11-08.
- Commit medido: `752d348bc67190e53b610989877e2405d238a1bc`. Instantánea `C:\Users\nmend\vrp-temporales\s175_audit\main\`, comprobada igual al commit salvo CRLF y `__pycache__` (`diff -rq --strip-trailing-cr` sobre `pipeline/`, `scripts/` y `.github/`: sin diferencias). Los workflows se leyeron con `git show 752d348bc:...` a `C:\Users\nmend\vrp-temporales\s175_audit\f4t\base_wf\`. Línea base roja (1) sobre `git show 79b4e3af6^:.github/workflows/nrt.yml`.
- Modelo y esfuerzo: Claude Fable 5.1; el esfuerzo real con que corrí es SIN DATO (no veo el parámetro; el pedido decía high).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f4t\`
- Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\f4t\` (copia privada de `pipeline/`, `scripts/` y `volcanoes.yaml` de la base en `repo_base\`, 3,5 MB; workflows extraídos en `base_wf\`; rueda de earthaccess 0.19.0 en `earthaccess_0190\`; logs y marcas de cada escenario en `tmp_01\` a `tmp_04\`). Disco al cerrar: C: 5,3 GB y D: 4,9 GB libres (sobre el piso de 3 GB).
- Red: ninguna llamada a NASA ni a Earthdata (los sockets quedaron interceptados en cada corrida del pipeline y cada intento bloqueado quedó anotado). Una descarga desde PyPI (`pip download earthaccess==0.19.0 --no-deps`, para leer la versión que instala el CI). Cinco llamadas a la API de GitHub de un tope de diez (repo, labels, issues con etiqueta `earthdata-token`, y dos para el log del run 37215535362). Ningún workflow despachado, ningún token real: los tokens de prueba son texto inventado o JWT sintéticos con firma falsa.
- Qué NO miré: la respuesta real de CMR y de LAADS/LANCE a un token inválido, no JWT o revocado (prohibido probarlo, A71; sólo tengo lo que el repo documentó del 2026-10-03); la configuración personal de notificaciones de Nicolás; los runners de GitHub (sin `act`: los bloques `run:` de shell se ejecutaron con bash y un shim, los bloques Python de los pasos se ejecutaron tal cual con un shim de `gh`, y el encadenamiento de pasos con `if:` se aplicó leyendo el YAML, no con un runner); `scripts/vigilar_plataformas.py --issues` y `scripts/vigilancia_guardia_modis.py` (leídos, no corridos); los workflows archivados en `.github/workflows/_archive/`; Mirova-v1 y la referencia.

## 2. En una pantalla

1. **Token vacío**: los seis workflows con cron que corren el pipeline (nrt, guardia-k-modis, sombra-34, sombra-codigo-mirova, experimental-diario) se detienen en el shell con exit 1 sin invocar python (medido); el NRT queda ROJO 11 jobs cada 2 h, `nrt-monitor` abre issue a las ~6 h y `nrt-healthcheck` a las 48 a 72 h. La línea base roja (1) se reencontró: el nrt.yml de antes de #894 sí llega a python y auth() hace 8 intentos de login con el par vencido.
2. **Token no JWT o JWT vencido**: el pipeline no mira `exp` y earthaccess (0.17.0 local, 0.19.0 en el CI) autentica sin red con cualquier texto; todo depende de cómo responda NASA. Si CMR responde 401 con un texto que diga expired, invalid, revoked o unauthorized (lo visto el 2026-10-03), el NRT queda ROJO. Si el 401 trae otro texto, o si CMR acepta la búsqueda y la descarga responde 401 o 403, **nrt.yml y experimental-diario quedan VERDES sin escribir un record** (medido: exit 0, «Cobertura INCOMPLETA», 0 records, revisor de MODIS en 0); guardia-k-modis, sombra-34 y sombra-codigo-mirova quedan ROJOS igual porque su revisor exige records de la corrida.
3. Dos defectos del clasificador de credencial muerta (`pipeline/fetch.py`): el status HTTP nunca se lee (un `Response` 401 es falso en Python y el `or` lo descarta), así que sólo el regex del cuerpo decide (381); y la forma real del error de descarga de earthaccess (`DownloadFailure("... Status code: 401")`) no calza con ese regex (382). El test de S124 del camino de descarga usa la forma de CMR, no la de descarga.
4. **Quién se entera**: nadie por diseño. El repo tiene 0 suscriptores (API hoy), ningún issue lleva asignado y no hay otro canal (A-1 de S150 sigue igual). El aviso de `renovar` saldrá el 2026-11-28 12:00 UTC (9,25 días antes del vencimiento) a ese issue sin lectores, y además dejará el job del healthcheck ROJO con «FAIL: la alerta pudo no haberse emitido» porque `gh label create` falla si la etiqueta existe (ya pasó el 2026-10-04 con `nrt-stale`, run 37215535362). Un token «desconocido» (vacío o no JWT) no abre issue (línea base roja 2, reencontrada).
5. 21 workflows de despacho manual (reprocesos y probes) llevan `EARTHDATA_USERNAME`/`PASSWORD` y no tienen la guarda: despachados con el secret ausente caen al par vencido (8 intentos de login por job, medido) y pueden bloquear la cuenta que usa el NRT (A71).

## 3. Hallazgos (IDs 381 a 399), de peor a menor gravedad

### 381
- TÍTULO: El clasificador de «credencial muerta» nunca lee el status HTTP: un 401 cuyo cuerpo no diga expired, invalid, revoked o unauthorized deja el NRT verde sin datos
- ARCHIVO:LÍNEA: `pipeline/fetch.py:467-469` (`resp = (getattr(getattr(exc, "__cause__", None), "response", None) or getattr(exc, "response", None))`; `code = getattr(resp, "status_code", None)`), `:471` (`if code == 401`), `:455-458` (`_CRED_DEAD_PAT`). SCRIPT:SALIDA `f4t_01_formas_error_credencial_salida.txt` (fila «CMR 401 'Token does not exist'»: `dead=False`) y `f4t_03_pipeline_simulado_salida.txt` (escenario `cmr401_noexist`).
- QUÉ PASA: el fenómeno es un token rechazado por NASA, que es permanente hasta que alguien rote el secret; el código lo trata como falla de red y sigue. `requests.Response.__bool__` devuelve `ok`, así que un `Response` con status 401 es falso y el `or` lo descarta: `code` queda `None` y la rama «un 401 ya es inequívoco» (`:471`) no corre nunca. Sólo el regex del cuerpo decide. Con un 401 de CMR con cuerpo `{"errors":["Token does not exist"]}` la búsqueda cae al catch-all de `fetch_for_volcano` (`:1281-1284`, `WARN: Failed to fetch`), la cobertura queda incompleta y `informar_cobertura` devuelve 0 en el NRT (`scripts/run_pipeline.py`, bloque `informar_cobertura`, «El NRT no usa el modo estricto: avisa y sigue»). Medido: exit 0, 6 WARN, 0 records, nrt.yml VERDE. El control positivo con el texto «Token [ABC] has expired» (el de los tests de S123 y el de la caída del 2026-10-03 según `docs/audit_s150/AUDITOR_A.md:40`) sí da `EarthdataCredentialError` y exit 1.
- CÓMO SE VE EN EL DASHBOARD: nada cambia; las series dejan de crecer y el tablero muestra «sin pasadas hace X h» sólo a quien entre (`docs/audit_s150/AUDITOR_A.md`, A-1). El badge del NRT sigue verde.
- CÓMO REPRODUCIRLO: `python experiments\_s175_audit\f4t\f4t_01_formas_error_credencial.py` (tabla) y `python experiments\_s175_audit\f4t\f4t_03_pipeline_simulado.py` (escenario `cmr401_noexist`: Láscar, `--date 2026-11-03`, red interceptada).
- CONFIANZA: CONFIRMADO el defecto del código y el verde de punta a punta en la simulación. SOSPECHA qué texto devuelve CMR para un token no JWT o revocado (A71 impide medirlo); para un JWT vencido el texto observado el 2026-10-03 sí calzó con el regex.
- GRAVEDAD 1-5: 5. Es el mismo modo de falla de julio de 2026 (13 días verdes sin dato); una erupción no se vería.

### 382
- TÍTULO: El guard de descarga (S124) está ciego a la forma real del error de earthaccess: un 401 o 403 en la descarga se reintenta 4 veces y termina como WARN, y nrt.yml queda verde sin records
- ARCHIVO:LÍNEA: `pipeline/fetch.py:1111-1120` (`except Exception` de `download_granules` con `_raise_if_credential_dead(e, "download")`); forma real en earthaccess 0.17.0 instalado (`earthaccess/store.py::_download_file`: `raise DownloadFailure(f"Download failed for {url}. Status code: {r.status_code}")`, TEXTO) y en 0.19.0 de PyPI (`C:\Users\nmend\vrp-temporales\s175_audit\f4t\earthaccess_0190\src\earthaccess\store.py:934-935`, TEXTO), sin atributo `response` ni `__cause__`. El test `tests/test_fetch_credential_dead_s123.py::test_download_aborta_con_credencial_muerta` construye el error con `_earthaccess_style_error` (forma de CMR: `RuntimeError` con `__cause__` y cuerpo «has expired»), no con `DownloadFailure`. SCRIPT:SALIDA `f4t_01_formas_error_credencial_salida.txt` (filas DESCARGA, «DownloadFailure genérico tras 4 intento(s)») y `f4t_03_pipeline_simulado_salida.txt` (`descarga401`, `descarga403`, `descarga401_jwt_vencido`).
- QUÉ PASA: la credencial se usa en la descarga, no en la búsqueda (comentario `:1112-1113`); si NASA rechaza ahí, el mensaje «Download failed for <url>. Status code: 401» no contiene ninguna de las palabras del regex y, por 381, el status tampoco se lee. Resultado: 4 intentos por par de gránulos, `WARN: Failed to fetch <plataforma>` por cada una de las 6 plataformas activas, «Cobertura INCOMPLETA: 6 búsquedas o descargas fallidas», exit 0. En nrt.yml los pasos siguientes no lo ven: «Assert Tier A records fresh» sólo avisa a las 72 h y sale 0 (`nrt.yml:323-335`), «Commit» sale 0 sin cambios (`:360`), «Revisar errores de MODIS» sólo mira `ERROR processing` (`scripts/revisar_errores_modis_nrt.py:28-33,74`; exit 0 medido). El test de S124 pasa con una forma que la descarga nunca produce: verificación contra la vara equivocada.
- CÓMO SE VE EN EL DASHBOARD: igual que 381, invisible como alerta.
- CÓMO REPRODUCIRLO: `python experiments\_s175_audit\f4t\f4t_03_pipeline_simulado.py` (escenarios `descarga401`, `descarga403`); log en `C:\Users\nmend\vrp-temporales\s175_audit\f4t\tmp_03\descarga401_pipeline.log` (líneas 22 a 108).
- CONFIANZA: CONFIRMADO el mecanismo (leído en las dos versiones de earthaccess y medido). SOSPECHA la exposición real: que CMR acepte la búsqueda con un token que LAADS rechace (el 2026-10-03 CMR rechazó primero). Puede darse con un token válido en EDL pero sin autorización de la aplicación de LAADS, o si una versión futura de earthaccess deja de mandar el token a CMR.
- GRAVEDAD 1-5: 4.

### 383
- TÍTULO: Los avisos siguen yendo a un repositorio sin lectores: 0 suscriptores, ningún asignado ni otro canal; el aviso de renovar del 2026-11-28 saldrá ahí (A-1 de S150 sin cambios en la base)
- ARCHIVO:LÍNEA: `.github/workflows/nrt-healthcheck.yml:413-414` (`gh issue create ... --label earthdata-token`, sin `--assignee`), `:249-250` (staleness), `nrt-monitor.yml` (issue `nrt-alert`); `grep -i "assignee\|slack\|telegram\|ntfy\|smtp\|webhook\|discord\|@MendozaVolcanic"` sobre los 56 workflows de la base: 0 líneas. SCRIPT:SALIDA `api_repo.json` (`subscribers_count: 0`, `watchers_count: 1`), `api_issues_token.json` (#752: `assignees: []`).
- QUÉ PASA: el sistema detecta el vencimiento con 9,25 días de margen (`f4t_04_healthcheck_token_issue_salida.txt`, sección B: primera corrida en `renovar` el 2026-11-28 12:00 UTC) y lo escribe donde nadie recibe notificación. En octubre eso costó 5 días de apagón con el aviso emitido a tiempo (`docs/audit_s150/AUDITOR_A.md:38-47`). Nicolás dice que rotará antes del 2026-11-27, o sea antes de que el sistema avise: el aviso no participa de la rotación.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `gh api repos/MendozaVolcanic/VRP-chile --jq .subscribers_count`; `git show 752d348bc:.github/workflows/nrt-healthcheck.yml | grep -n -i assignee` (vacío).
- CONFIANZA: CONFIRMADO lo anterior. SIN VERIFICAR si a Nicolás le llegan los correos «Run failed» de Actions (actor de los cron = MendozaVolcanic según S150; depende de su configuración personal).
- GRAVEDAD 1-5: 5 (es lo que convierte cualquiera de los otros hallazgos en días de apagón).

### 384
- TÍTULO: El primer issue de cada incidente deja el healthcheck en ROJO con «FAIL: la alerta pudo no haberse emitido» aunque el issue sí se creó: `gh label create` sin `--force` falla cuando la etiqueta ya existe, y las tres etiquetas ya existen
- ARCHIVO:LÍNEA: `.github/workflows/nrt-healthcheck.yml:247-248` (`gh("label", "create", LABEL, ...)` para `nrt-stale`) y `:411-412` (para `earthdata-token`); `:190-194` y `:376-377` acumulan el error en `fallos`; `:206-214` y `:380-383` salen con 1. SCRIPT:SALIDA `api_labels.json` (existen `earthdata-token`, `nrt-alert`, `nrt-stale`); `api_run_healthcheck_20261004_logfailed_full.txt` líneas 471 a 475 (run real 37215535362, 2026-10-04 16:07 UTC: `WARN gh label create nrt-stale: label with name "nrt-stale" already exists`, `Issue creado (escalón 48 h).`, `FAIL: 1 llamada(s) a gh fallaron; la alerta pudo no haberse emitido.`, `##[error]Process completed with exit code 1`); `f4t_04_healthcheck_token_issue_salida.txt` sección C (reproducido con shim para `earthdata-token`: exit 1 con `gh issue create` ejecutado) y sección D (ídem para `nrt-stale` con 11 volcanes a 50 h).
- QUÉ PASA: `gh label create --help`: «-f, --force Update the label color and description if label already exists» (TEXTO); sin `--force` el comando falla si la etiqueta existe. La primera vez funcionó (09-23, etiqueta nueva) y desde entonces toda apertura de issue falla el paso. El insumo `runs_nrt-healthcheck.json` muestra exactamente dos corridas en `failure` en 50: la del 2026-10-04 16:06 (apertura de #756) y la del 10-05 (runner no asignado). Efecto doble: un rojo por incidente que no es falla, y un texto que dice que la alerta pudo perderse cuando no se perdió; quien lea el log aprende a no creerle. El 2026-11-28 12:00 UTC, si nadie rotó, el aviso de `renovar` saldrá así.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `gh run view 37215535362 --repo MendozaVolcanic/VRP-chile --log-failed | grep -i "already exists"`; `python experiments\_s175_audit\f4t\f4t_04_healthcheck_token_issue.py` (casos «etiqueta YA existe»).
- CONFIANZA: CONFIRMADO (log real y simulación).
- GRAVEDAD 1-5: 3.

### 385
- TÍTULO: nrt.yml no tiene ningún paso que exija «esta corrida escribió algo»: es el único productor con cron que puede quedar verde sin producir; guardia, sombras y reprocesos estrictos no pueden
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:292-337` (A57 avisa y `sys.exit(0)` con stale, comentario `:274-291` explica por qué dejó de fallar), `:339-371` (commit sale 0 sin cambios), `:382-384` (`revisar_errores_modis_nrt.py`, sólo `ERROR processing`); comparar con `guardia-k-modis.yml:150-153` y `sombra-34.yml:159-162` (`revisar_guardia_modis.py` y `revisar_sombra.py`: «ningún record ... escrito en esta corrida» y «cobertura incompleta ... del último día» son FALLA, `scripts/revisar_guardia_modis.py:97,108-109`, `scripts/revisar_sombra.py:206,214-215`) y con `reproc-retro-paquete.yml:122` y `reproc-chunked.yml:154` (`--estricto-cobertura`, exit 3 con fallas, `scripts/run_pipeline.py::informar_cobertura`). SCRIPT:SALIDA `f4t_03_pipeline_simulado_salida.txt`, tabla final: en `cmr401_noexist`, `descarga401`, `descarga403` y `descarga401_jwt_vencido` nrt.yml queda VERDE y el revisor de la guardia da ROJO con la misma cobertura y el mismo log. Inventario en `inventario_workflows_token.tsv`: `experimental-diario.yml` tampoco tiene revisor ni modo estricto.
- QUÉ PASA: la decisión S123 de que A57 «avise pero no falle» (`nrt.yml:274-291`) y la de que el NRT no use el modo estricto (`run_pipeline.py`, docstring de `informar_cobertura`) dejan al productor operacional sin ningún control de «produjo»; los demás productores sí lo tienen desde S167 a S172. Por eso 381 y 382 son silenciosos sólo en nrt.yml y experimental-diario.
- CÓMO SE VE EN EL DASHBOARD: igual que 381.
- CÓMO REPRODUCIRLO: tabla final de `f4t_03_pipeline_simulado.py`; `git show 752d348bc:.github/workflows/nrt.yml | grep -n "revisar_\|estricto"` (sólo `revisar_errores_modis_nrt.py`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 4.

### 386
- TÍTULO: 21 workflows de despacho manual llevan EARTHDATA_USERNAME y PASSWORD y no tienen la guarda de token vacío: despachados con el secret ausente hacen 8 intentos de login por job con el par vencido (A71, bloqueo de la cuenta que usa el NRT)
- ARCHIVO:LÍNEA: lista en `dispatch_sin_guarda_con_usuario.txt` (`backfill-geometry.yml`, `backfill-tier-a.yml`, `probe-s136-3brazos.yml`, `probe-s136-conformidad-a6.yml`, `probe-s136-conformidad-apendice.yml`, `probe-s137-etapa-apendice.yml`, `probe-s137-sigma-dnti.yml`, `probe-s141-vecinos-v2.yml`, `probe-s141-vecinos.yml`, `probe-s143-12-noches.yml`, `reproc-chunked.yml`, `reproc-s120-eq16-villarrica.yml`, `reproc-s121-d12-modis-ab.yml`, `reproc-s124-ndc-focus.yml`, `reproc-s124-villarrica-op-ab.yml`, `reproc-s129-ab-fondos.yml`, `reproc-s130-d18-roi1.yml`, `reproc-s133-area-ab.yml`, `reproc-s133-b22-ab.yml`, `reproc-s135-ab-d1d2.yml`, `reproc-s143-ab-d22d25.yml`); por ejemplo `reproc-chunked.yml:136-137`. `tests/test_guard_token_vacio_cron_s160.py:22-25` sólo recorre workflows con `schedule`. SCRIPT:SALIDA `inventario_workflows_token.tsv`; `f4t_03_pipeline_simulado_salida.txt` escenario `token_vacio_pre894` (8 `LOGIN`, 8 conexiones a `urs.earthdata.nasa.gov:443` bloqueadas, exit 1).
- QUÉ PASA: con el token vacío `fetch.auth()` hace el probe TCP y, si NASA responde, 8 intentos de `earthaccess.login(strategy="environment")` (`pipeline/fetch.py:343-373`), cada uno con el par vencido contra URS; S160 midió que eso bloquea la cuenta. El pipeline de un probe viejo comparte la cuenta con el NRT: el daño no queda en el reproceso. Son workflows de despacho manual, así que hace falta que alguien los dispare justo con el secret ausente; `reproc-chunked.yml` y `backfill-tier-a.yml` son los que se usan.
- CÓMO SE VE EN EL DASHBOARD: si la cuenta se bloquea, el NRT deja de bajar datos (rojo o verde según 381/382).
- CÓMO REPRODUCIRLO: `awk -F'\t' 'NR>1 && $2==0 && $5>0 && $6==0 {print $1}' experiments\_s175_audit\f4t\inventario_workflows_token.tsv`; escenario `token_vacio_pre894` de `f4t_03_pipeline_simulado.py`.
- CONFIANZA: CONFIRMADO el inventario y los 8 intentos (en sandbox, con el probe simulado OK). SOSPECHA que hoy el bloqueo ocurra con exactamente 8 intentos (S160 lo midió; no lo repetí, A71).
- GRAVEDAD 1-5: 3.

### 387
- TÍTULO: Un token «desconocido» (secret ausente o texto que no es JWT) no abre issue; si además el pipeline queda verde (381/382), nadie recibe nada hasta el issue de staleness a las 48 a 72 h, que tampoco tiene lectores (línea base roja 2, reencontrada: hallazgo 124 de F0)
- ARCHIVO:LÍNEA: `.github/workflows/nrt-healthcheck.yml:385-387` (`if ESTADO == "desconocido": print("Estado del token desconocido (secret ausente o no-JWT): sin issue."); sys.exit(0)`), `scripts/token_edad.py:44-45` (estado `desconocido`), `nrt-healthcheck.yml:21` (cron 12:00 UTC) y `:53` (`THRESHOLD_H = 48`). SCRIPT:SALIDA `f4t_04_healthcheck_token_issue_salida.txt` sección A (vacío, «hola» y JWT sin `exp` dan `desconocido`) y sección C (`desconocido`: exit 0, ninguna llamada a `gh`).
- QUÉ PASA: con el secret ausente la guarda del shell deja el NRT rojo y el monitor avisa a las ~6 h (`nrt-monitor.yml`, 3 corridas), así que el silencio total no ocurre; pero un texto no JWT pasa la guarda (no está vacío), earthaccess lo acepta sin red, y el único canal queda en manos de la respuesta de NASA. La latencia mínima del staleness es 48 h desde el último record más lo que falte hasta las 12:00 UTC (hasta 24 h más).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments\_s175_audit\f4t\f4t_04_healthcheck_token_issue.py` (caso «LÍNEA BASE ROJA (2)»).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 3.

### 388
- TÍTULO: El pipeline nunca mira el `exp` del JWT: un JWT vencido y un texto cualquiera se comportan igual (auth() sin red, OK); el único lector de `exp` es `token_edad.py`, una vez al día
- ARCHIVO:LÍNEA: earthaccess 0.17.0 `auth.py::_get_credentials` (instalado) y 0.19.0 (`earthaccess_0190\src\earthaccess\auth.py:313-315`, TEXTO: `if user_token is not None: self.token = {"access_token": user_token}; self.authenticated = True`); `pipeline/fetch.py:343-350` (con token se salta el probe y `earthaccess.login(strategy="environment")` retorna). SCRIPT:SALIDA `f4t_03_pipeline_simulado_salida.txt` (`descarga401_jwt_vencido` idéntico a `descarga401`; en todos los escenarios con token `logins=1`, `AUTH_OK` en el log).
- QUÉ PASA: no es un defecto en sí (el vencimiento lo dice NASA al usar el token), pero explica por qué no hay un corte temprano: un JWT vencido pasa la guarda del shell, pasa `auth()` y llega a buscar y descargar; todo el diagnóstico depende de 381 y 382. Un chequeo de `exp` antes de `auth()` (reusando `token_edad.vencimiento_jwt`) daría rojo inmediato y con causa, sin tocar la red.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: escenario `descarga401_jwt_vencido` de `f4t_03_pipeline_simulado.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2.

### 389
- TÍTULO: earthaccess va sin pin en los workflows y el CI instala hoy 0.19.0 mientras los tests locales corren con 0.17.0; el único mecanismo de detección que queda (el regex sobre el texto del error) depende de un texto que cada versión puede cambiar
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:143` (`pip install earthaccess numpy h5py scipy pyyaml pyproj`), `guardia-k-modis.yml:91`, `sombra-34.yml:100`; `requirements.txt:1` (`earthaccess>=0.9.0`). SCRIPT:SALIDA `pip index versions earthaccess` (0.19.0 es la última en PyPI al medir); `f4t_01_formas_error_credencial_salida.txt` (`earthaccess instalado: 0.17.0`).
- QUÉ PASA: hoy las dos versiones producen las mismas formas (leídas: `store.py::_download_file` y `search.py` envuelven igual), así que 381 y 382 valen para el CI. Pero la detección descansa en que el texto de CMR y el de earthaccess no cambien; un pin (o un test que construya el error con la clase real `DownloadFailure`) cerraría esa deriva.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:.github/workflows/nrt.yml | grep -n "pip install earthaccess"`; `pip index versions earthaccess`.
- CONFIANZA: CONFIRMADO lo leído; SOSPECHA que una versión futura cambie el texto.
- GRAVEDAD 1-5: 2.

### 390
- TÍTULO: El aviso de vencimiento llega a tiempo pero el 2026-11-28 12:00 UTC, con 9,25 días de margen y no 10: la regla «rotar a los 50 días» del repo (2026-11-27) cae un día antes del primer aviso del sistema
- ARCHIVO:LÍNEA: `scripts/token_edad.py:27` (`DIAS_AVISO = 10`), `nrt-healthcheck.yml:21` (cron `0 12 * * *`), `docs/EARTHDATA_TOKEN_SETUP.md:40-42` («Rotación cada 50 días (recordatorio)»). SCRIPT:SALIDA `f4t_04_healthcheck_token_issue_salida.txt` sección B.
- QUÉ PASA: el token vence el 2026-12-07 18:03 UTC (insumo y #752 de octubre). A las 12:00 UTC del 11-27 quedan 10,25 días (estado `ok`); la primera corrida en `renovar` es la del 11-28 12:00 UTC. Si Nicolás rota el 11-27 como dice, el sistema nunca avisará de este token: bien, pero entonces el aviso automático no participa de la rotación y no se probará otra vez hasta el token siguiente. Si no rota, el aviso llega con 9,25 días y con el rojo de 384.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: sección B de `f4t_04_healthcheck_token_issue.py`.
- CONFIANZA: CONFIRMADO (cálculo con el código de la base y la fecha del insumo).
- GRAVEDAD 1-5: 1.

## 4. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

- `scripts/run_pipeline.py::informar_cobertura` devuelve 0 en el NRT con descargas fallidas por decisión escrita («avisa y sigue, porque la corrida siguiente vuelve a intentar»). Es la decisión que vuelve silenciosos 381 y 382; cambiarla (o agregar a nrt.yml un revisor como el de la guardia) es de Nicolás y toca `scripts/` y `nrt.yml`, no `pipeline/`. Confianza: CONFIRMADO lo leído.
- `scripts/vigilar_plataformas.py` (paso «Vigilancia por plataforma» de `nrt-healthcheck.yml:295-301`): el comentario `:289-291` dice que si callan todas las plataformas «es caída general y la cubre el paso de frescura, así que no abre nada propio». Con token muerto callan todas; no lo corrí. SIN DATO sobre qué imprime en ese caso.
- `.github/workflows/nrt-retry.yml:58-60` sólo relanza si la última corrida de nrt.yml concluyó `failure` y busca la anotación NASA_DOWN; con 401 no la hay (S150 ya lo verificó). No medido ahora.
- La corrección de 381 es de una línea (`resp = a if a is not None else b`) y la de 382 de un regex o de leer la clase `DownloadFailure`, pero ambas tocan `pipeline/fetch.py`: tag defensivo y confirmación de Nicolás (A45). El test nuevo debería construir el error con `earthaccess.exceptions.DownloadFailure` real y con un `Response` 401 de cuerpo vacío.
- Durante la simulación, la única conexión que el pipeline intentó fuera de CMR y de la descarga fue a `169.254.169.254:80` (metadatos de AWS, `earthaccess.store.Store` al decidir si corre en us-west-2); quedó bloqueada y no afecta nada en el runner de GitHub. Dato para quien audite la huella de red del NRT.
- El hallazgo 124 de F0 clasificó 247 como «resuelto salvo un borde» con gravedad 1; con 381 y 382 el borde «no JWT» ya no es inocuo: F0 debería heredar esta rebaja (A113).

## 5. VERIFICADO LIMPIO (qué miré, contra qué vara, con qué comando)

- **Guarda de token vacío en el shell**, vara: el bloque `run:` real ejecutado con bash y un shim de python. `nrt.yml`, `guardia-k-modis.yml`, `sombra-34.yml`, `experimental-diario.yml` (y `sombra-codigo-mirova.yml` por texto, mismo bloque): exit 1, `::error::EARTHDATA_TOKEN vacío`, python no invocado; control positivo con token «x»: python invocado. `f4t_02_guarda_token_vacio_shell_salida.txt`. Línea base roja (1): `79b4e3af6^` sin guarda llega a python (reencontrada).
- **auth() con token vacío llega a 8 intentos de login** (nivel Python, probe simulado OK, red bloqueada): `f4t_03_pipeline_simulado_salida.txt`, escenario `token_vacio_pre894` (`logins=8`, 8 conexiones bloqueadas a `urs.earthdata.nasa.gov:443`, exit 1 con traceback). Vara: `pipeline/fetch.py:347-373` (lista `delays` de 8 esperas y bucle de login).
- **CMR 401 con texto «has expired» deja el NRT ROJO**: `EarthdataCredentialError`, traceback, exit 1 (escenario `cmr401_expired`); coincide con lo observado el 2026-10-03 (`docs/audit_s150/AUDITOR_A.md:40,352`). Vara: el mismo texto de `tests/test_fetch_credential_dead_s123.py:58`.
- **Un gránulo que no es HDF llega al procesador y `revisar_errores_modis_nrt.py` lo pone en ROJO** (control positivo del encadenamiento): escenario `descarga_ok_archivo_falso`, 6 `ERROR processing`, revisor exit 1.
- **Los revisores de guardia y sombra ven el verde vacío**: `scripts/revisar_guardia_modis.py` da exit 1 con «cobertura incompleta ... del 2026-11-03» y «ningún record de MODIS escrito en esta corrida» en los cuatro escenarios donde nrt.yml queda VERDE. Vara: la misma cobertura.json y el mismo pipeline.log de la corrida simulada.
- **`scripts/token_edad.py`**: vacío, «hola» y JWT sin `exp` dan `desconocido`; JWT a 30,6 días `ok`; a 5 días `renovar`; vencido ayer `vencido`. Vara: el propio código de la base con hora fija del servidor. `f4t_04_...salida.txt` sección A.
- **Transiciones del issue del token**: `vencido` sin issue abierto y sin etiqueta previa crea label e issue (exit 0); `vencido` con issue abierto en `renovar` edita y comenta; `ok` con issue abierto comenta y cierra. Vara: el bloque Python real del paso con shim de `gh`. Sección C.
- **Detección de staleness**: 11 JSON con último record a 50 h dan `stale_count=11`, `max_age_h=50.0`; a 20 h, 0 y «OK: sin stale y sin issue abierto». Sección D.
- **La instantánea `main\` es la base**: `diff -rq --strip-trailing-cr` sin diferencias en `pipeline/`, `scripts/`, `.github/` (sólo `__pycache__`).
- **Con token, el pipeline no toca URS al autenticar**: `logins=1`, `AUTH_OK`, ninguna conexión a `urs.earthdata` en las marcas de los escenarios con token (sólo la de metadatos AWS, bloqueada). Vara: `earthaccess.auth._get_credentials` leído en 0.17.0 y 0.19.0.
- `nrt-monitor.yml` usa `scripts/nrt_monitor_decision.js` con tope de 12 h para la corrida más nueva (A-2 de S150 corregido en la base): leído, no corrido.

## 6. SIN DATO

- Qué status y qué texto devuelven CMR y LAADS/LANCE a un token no JWT, revocado o vencido (A71: no se prueba). Para un JWT vencido, el repo documenta «401 Unauthorized en CMR» el 2026-10-03 con rojo en 11 de 11 jobs, lo que implica un texto que calzó con el regex; el texto exacto no está en el repo.
- Si a Nicolás le llegan los correos «Run failed» de Actions de las corridas programadas (actor MendozaVolcanic).
- Qué imprime `scripts/vigilar_plataformas.py --issues` cuando callan todas las plataformas, y qué veredicto da `scripts/vigilancia_guardia_modis.py` cuando guardia y producción quedan sin datos nuevos a la vez (leído: `VIGILANCIA_CIEGA` si hay avisos, `:419-420`; no corrido).
- El encadenamiento de pasos con `if:` de nrt.yml no corrió en un runner (sin `act`); se aplicó leyendo `nrt.yml:171-173, 253, 295-297, 340, 383`.
- Si hoy el bloqueo de la cuenta de Earthdata ocurre con los 8 intentos (S160 lo midió; no se repite).

## 7. FUERA DE ALCANCE

Mirova-v1 y `sync-mirova-csv.yml`; `pages-deploy.yml`; `vigilar-osf-mirova.yml`; `.github/workflows/_archive/`; la calidad de la referencia; el detector. El cron externo (cron-job.org) que despacha nrt.yml a las :10 no se miró: usa el mismo nrt.yml.

## 8. Resumen por workflow: token muerto, color y quién se entera

| workflow (cron) | token vacío | no JWT o JWT vencido, NASA responde 401 con texto del regex | ídem con otro texto, o 401/403 en la descarga | quién se entera |
|---|---|---|---|---|
| nrt.yml (cada 2 h) | ROJO en el shell, 11 jobs, 0 logins | ROJO (EarthdataCredentialError) | **VERDE sin records** | rojo: `nrt-monitor` issue a las ~6 h, staleness 48 a 72 h; verde: sólo staleness 48 a 72 h. Issues sin lectores (383) |
| experimental-diario.yml (14:00) | ROJO en el shell | ROJO | **VERDE sin records** | nadie (no hay vigilancia propia) |
| guardia-k-modis.yml (17:40) | ROJO en el shell | ROJO | ROJO por `revisar_guardia_modis.py` | `vigilancia-guardia-modis` (leído, no corrido) |
| sombra-34.yml (13:07) y sombra-codigo-mirova.yml (15:00) | ROJO en el shell | ROJO | ROJO por `revisar_sombra.py` | `vigilancia-sombra-34` / `vigilancia-sombra` (leídos) |
| nrt-healthcheck.yml (12:00) | token `desconocido`: sin issue | `vencido`: issue o comentario (con el rojo de 384 al crear) | ídem | issue sin lectores |
| reproc-retro-paquete.yml (manual) | ROJO en el shell | ROJO | ROJO (exit 3, estricto) | quien lo despachó |
| reproc-chunked.yml, backfill-tier-a.yml, backfill-geometry.yml y 18 probes/reprocs (manual) | **8 logins con el par vencido por job (A71)** | ROJO | reproc-chunked ROJO (estricto); los demás VERDE posible | quien lo despachó |

## 9. Instrumentos y salidas (todos en CARPETA)

- `f4t_01_formas_error_credencial.py` y `_salida.txt`: `_is_credential_dead` y `download_granules` contra las formas reales de earthaccess; control positivo con la forma de CMR.
- `f4t_02_guarda_token_vacio_shell.py` y `_salida.txt`: bloques `run:` reales con bash y shim de python; base y pre-#894.
- `f4t_03_pipeline_simulado.py`, `_salida.txt` y `_resultados.json`: `run_pipeline.py` de la base con sockets, DNS, `time.sleep`, `earthaccess.search_data`, `earthaccess.download` y `earthaccess.login` interceptados; 7 escenarios; después `revisar_errores_modis_nrt.py` y `revisar_guardia_modis.py` sobre la misma salida. Logs en `C:\Users\nmend\vrp-temporales\s175_audit\f4t\tmp_03\`.
- `f4t_04_healthcheck_token_issue.py` y `_salida.txt`: `token_edad.estado_token`, calendario del aviso, y los tres bloques Python de `nrt-healthcheck.yml` con shim de `gh`.
- `inventario_workflows_token.tsv`, `dispatch_sin_guarda_con_usuario.txt`: los 56 workflows de la base.
- `api_repo.json`, `api_labels.json`, `api_issues_token.json`, `api_run_healthcheck_20261004_logfailed_full.txt` (y el recorte `_logfailed.txt`): las 5 llamadas a GitHub.
- `escribir_csv.py` y `hallazgos.csv`.
