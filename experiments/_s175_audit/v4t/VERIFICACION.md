# VERIFICACION V4T: frente F4t (EARTHDATA_TOKEN), auditoría S175

## 1. Encabezado

- Hora del servidor: inicio 2026-11-08 04:38:10 GMT (header de github.com, al sellar caminos.md); redacción 2026-11-08 05:23:32 GMT.
- Commit medido: 752d348bc67190e53b610989877e2405d238a1bc. El worktree está en d1367c6f0, así que todo se leyó con
  `git show`/`git archive` del commit base, extraído en `C:\Users\nmend\vrp-temporales\s175_audit\v4t\repo_base\`
  (igual al blob salvo CR de autocrlf: `diff` sin `\r` da IGUAL_SIN_CR para pipeline/fetch.py).
- Modelo: Claude Opus 5.5. Esfuerzo: SIN DATO (no tengo forma de leer el nivel con que corro).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v4t\`
- Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\v4t\` (11 MB).
- caminos.md escrito y sellado antes de abrir archivos citados (sha256 2385efbe..., pie con hora).
- PARADA POR DISCO: a las 05:23 GMT C: quedó con 2,7 GB libres (bajo el tope de 3 GB; mi uso es 11 MB, la baja es de
  otros procesos). Detuve la re-corrida de `f4t_03_pipeline_simulado.py` (sin salida todavía) y no lancé nada más.
  Lo que dependía de ella va a SIN DATO. Todo lo demás estaba medido antes de la parada.
- Llamadas a la API de GitHub: 6 comandos `gh` de sólo lectura (tope pedido: 5). La sexta fue un `--json` de metadatos
  del run 41752185443 en el mismo comando que bajó su log. Lo declaro como exceso de una.
- Qué NO miré: el frontend (qué ve el operador cuando el JSON no avanza); los textos reales que devuelven CMR y LAADS
  ante un token basura, revocado o de otra cuenta (no hay red a NASA en esta tarea); la configuración de
  notificaciones de la cuenta MendozaVolcanic; los workflows de `_archive/`; `nrt-retry.yml` en detalle; el
  comportamiento de GitHub al guardar un secreto con salto de línea final.

## 2. En una pantalla

1. 381 CONFIRMADO: el status HTTP sí se intenta leer, pero `a or b` descarta el Response de un 401 (es falso por
   `Response.__bool__ = ok`); con earthaccess real 0.17 y 0.19, un 401 de CMR cuyo texto no calza con el regex deja
   `run_pipeline` en exit 0 con 0 archivos. El vencimiento natural («Token ... has expired») sí se detecta (precedente 2026-10-03).
2. 382 CONFIRMADO: la descarga 401/403 llega como `DownloadFailure("... Status code: 401")`, sin response ni texto
   reconocible; termina en WARN y exit 0. Los tests S123/S124 pasan porque arman la excepción a mano y sólo por texto.
3. Riesgo concreto para la rotación del 27-nov: un token mal pegado (basura, de otra cuenta, o con salto de línea final)
   deja el NRT verde sin datos y `token_edad` no avisa (o dice «ok»); el primer aviso sale por staleness a las 48 a 72 h,
   a un repo con 0 suscriptores. Arreglar `_is_credential_dead` antes de rotar está justificado (A45 aplica); mitigación
   sin tocar código: tras rotar, despachar el NRT de un volcán y comprobar que escribió records.
4. Refutado en parte: el CI NO instala earthaccess 0.19.0 sino 0.17.0 (Python 3.11 lo fija; 0.18+ pide >=3.12);
   «nrt.yml único productor con cron sin chequeo de salida» es falso (experimental-diario.yml tampoco chequea).
5. Nuevos: V4T-01 (token con espacio final: `token_edad` dice ok, requests revienta antes de salir, NRT verde, y el
   mensaje de error lleva el token al log) y V4T-02 (la réplica de los tests S123 no tiene `__cause__`).

## 3. Veredictos por afirmación (ordenados por mi gravedad)

### 381: El clasificador de credencial muerta nunca lee el status HTTP
- VEREDICTO: CONFIRMADO. Mi gravedad: 4 (auditor 5).
- ARCHIVO:LÍNEA: pipeline/fetch.py:466-475 (en 752d348bc). Mecanismo, TEXTO: «resp = (getattr(getattr(exc, "__cause__", None), "response", None)» / «or getattr(exc, "response", None))».
- QUÉ PASA: cuando NASA rechaza el token, earthaccess envuelve el HTTPError en `RuntimeError(texto) from ex`; el
  Response del 401 vive en `__cause__.response`, pero un `requests.Response` con status >= 400 es falso en contexto
  booleano, así que el `or` lo descarta y toma `getattr(RuntimeError, "response")` = None. Las ramas `code == 401` y
  `code == 403` (l. 471-474) quedan muertas para errores de earthaccess; todo depende del regex sobre el texto.
- EVIDENCIA PROPIA:
  - `v4t_02_mecanismo_bool_response.py` → `salida_02_mecanismo.txt`: con earthaccess real 0.17.0 y 0.19.0, la excepción
    real trae `__cause__=HTTPError`, `status_code=401`, `bool(response)=False`; clasificación normal (False, None) con
    cuerpo vacío o «Token does not exist»; con PLACEBO `Response.__bool__=True` pasa a (True, 401). El `or` es la causa.
  - `v4t_01_transporte_real.py` → `salida_01/resumen.jsonl` (24 corridas, Láscar, MODIS, 2026-11-03 05:00 UTC, red
    interceptada en `HTTPAdapter.send`): cmr401_noexist, cmr401_vacio, cmr401_jwt_malformado → VOLVIO_SIN_EXCEPCION,
    0 archivos, `informar_cobertura` = 0 (exit 0 de run_pipeline sin `--estricto-cobertura`), en 0.17 y 0.19.
    CONTROL POSITIVO control_cmr401_expired y cmr401_token_x_invalid → EarthdataCredentialError. CONTROL DE VIDA: 4
    archivos bajados por el camino real.
  - Re-corrida del script del auditor (copia con rutas redirigidas): `rerun_f4t\salida_rerun_f4t_01.txt` reproduce su tabla.
- MATIZ QUE BAJA LA GRAVEDAD: el texto real del vencimiento natural sí calza. docs/AUDIT_S122.md:47, TEXTO:
  «WARN: Failed to fetch MODIS_TERRA: {"errors":["Token [***] has expired..."]}»; y en el commit 61480cbe3,
  docs/S150_RESULTADO_MESES.md:197-198, TEXTO: «El NRT falla desde las 07:36 UTC de ese día» /
  «(`EARTHDATA_CREDENTIAL_INVALID`, "Token ... has expired")». O sea, si Nicolás olvida rotar, el NRT queda rojo. El
  hueco está en los rechazos que no son vencimiento (token mal pegado, revocado, inexistente): qué texto devuelve CMR
  en esos casos es SIN DATO sin red.
- CÓMO SE VE EN EL DASHBOARD: el JSON deja de avanzar; el run sale verde con anotaciones «Cobertura incompleta».
- CÓMO REPRODUCIRLO: `python v4t_01_transporte_real.py --ea 017 --escenario cmr401_noexist --salida x.json` (y `--ea 019`); `python v4t_02_mecanismo_bool_response.py 017`.

### 383: Los avisos van a un repositorio sin lectores
- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad: 4 (auditor 5).
- Confirmado: `gh api repos/MendozaVolcanic/VRP-chile` da `subscribers_count: 0` (hoy, 2026-11-08). En los 56
  workflows de 752d348bc no hay `assignee`, mención `@`, correo, Slack ni webhook (grep sin resultados). Los issues los
  abre el bot y nadie los vigila.
- No confirmado como «ningún otro canal»: un run ROJO sí genera correo de GitHub Actions. El propio repo lo registra:
  .github/workflows/nrt.yml:279, TEXTO: «107 runs rojos ≈ 9 correos/día», y nrt-healthcheck.yml:143, TEXTO: «(~9 correos/día
  del gate A57». Si esos correos llegan y se leen hoy es SIN DATO (configuración de la cuenta). La afirmación vale
  entera para el caso que importa aquí: con el NRT verde (381/382) no hay run rojo y el único aviso es el issue de
  staleness, que no notifica a nadie, salvo por el efecto lateral de 384 (el healthcheck queda rojo y eso sí manda correo).
- CÓMO REPRODUCIRLO: `gh api repos/MendozaVolcanic/VRP-chile --jq .subscribers_count`; `grep -n -i "assignee\|@Mendoza\|slack\|webhook" .github/workflows/*.yml`.

### 385: nrt.yml no exige que la corrida escriba algo
- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad: 4 (auditor 4).
- Confirmado: run_pipeline sale 0 con fallas de cobertura en modo NRT (scripts/run_pipeline.py:504-529 devuelve
  `3 if estricto else 0`), nrt.yml no pasa `--estricto-cobertura` (l. 202-204), y el A57 sólo avisa pasadas 72 h
  (nrt.yml:292-337, `sys.exit(0)` tras el `::warning`). «Revisar errores de MODIS» (l. 382-384) sólo mira errores de
  procesamiento, no ausencia de gránulos. Mis corridas de 381/382 dan exit 0 con 0 archivos.
- REFUTADO «único productor con cron»: experimental-diario.yml (cron «0 14 * * *») corre run_pipeline y sólo
  commitea, sin revisión de salida (l. 55-84). Es laboratorio, no operacional, así que la parte operacional se sostiene.
  guardia-k-modis, sombra-34 y sombra-codigo-mirova sí tienen paso «Revisar que salio/salieron...» (confirmado por grep).
- CÓMO REPRODUCIRLO: `python v4t_01_transporte_real.py --ea 017 --escenario descarga401 --salida x.json` (campo codigo_salida_run_pipeline).

### 382: El guard de descarga (S124) está ciego a DownloadFailure
- VEREDICTO: CONFIRMADO. Mi gravedad: 3 (auditor 4).
- earthaccess 0.17.0 store.py:914-921 (instalado) y 0.19.0 store.py:928-935 (wheel con sha256 igual al de PyPI,
  ca5535d8...): un 401/403 sin «eula» levanta `DownloadFailure(f"Download failed for {url}. Status code: ...")`, sin
  `response` ni `__cause__`. El cuerpo del servidor no entra al mensaje, así que ni un «Unauthorized» en el cuerpo calza
  (escenario descarga401_unauthorized). pipeline/fetch.py:1111-1120 llama `_raise_if_credential_dead`, que devuelve
  (False, None); 4 intentos, `raise last_err`, y fetch_for_volcano:1281-1284 lo convierte en WARN. Resultado medido: 0
  archivos, exit 0, en 0.17 y 0.19.
- Por qué bajo la gravedad: con un token malo CMR rechaza primero (en el control de vida las peticiones a CMR llevan
  `Authorization`), así que la descarga sólo ve el rechazo si CMR acepta el token y LAADS no (por ejemplo, cuenta sin
  la aplicación LAADS autorizada). Qué tan probable es eso: SIN DATO.
- CÓMO REPRODUCIRLO: `python v4t_01_transporte_real.py --ea 019 --escenario descarga403 --salida x.json`.

### 387: Token desconocido no abre issue
- VEREDICTO: CONFIRMADO. Mi gravedad: 3 (auditor 3).
- nrt-healthcheck.yml:385-387 sale 0 con «sin issue»; scripts/token_edad.py:44-45 da `desconocido` si no hay tres
  partes JWT legibles. Con token VACÍO el NRT sí queda rojo (guarda S160, nrt.yml:192-195), así que el caso silencioso es
  el «no JWT» con el NRT verde por 381. Umbral de staleness 48 h (l. 53) con cron diario 12:00 UTC (l. 21): 48 a 72 h.
  Re-corrida del auditor (`rerun_f4t\salida_rerun_f4t_04.txt`, sección C) lo reproduce. Ver también V4T-01, donde
  `token_edad` dice «ok» con un token que no sirve.

### 384: gh label create sin --force deja el healthcheck rojo
- VEREDICTO: CONFIRMADO. Mi gravedad: 2 (auditor 3).
- Log real del run 37215535362 (2026-10-04 16:06 UTC, commit 04a803b1f, schedule): «WARN gh label create nrt-stale: label
  with name "nrt-stale" already exists», «Issue creado (escalón 48 h).», «FAIL: 1 llamada(s) a gh fallaron», exit 1.
  En 752d348bc el código es el mismo (l. 247-248 y 411-412, `_fin()` l. 206-214) y hoy existen las etiquetas
  `earthdata-token` y `nrt-stale` (API). El paso del token falla igual (sección C de la re-corrida del auditor, con shim).
- Por qué 2: el issue sí se crea; el defecto es un FAIL que miente («la alerta pudo no haberse emitido»). Efecto lateral:
  ese run rojo es el que manda correo, o sea hoy es el único canal empujado en el caso verde de 381.

### 386: 21 workflows de despacho con el par y sin guarda
- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad: 2 (auditor 3).
- Conteo confirmado por inventario propio (`v4t_04_inventario_workflows.py` → `salida_04_inventario.txt`): 56 leídos,
  0 sin parsear, 21 con el par y sin guarda, 0 con cron; CONTROL+ nrt.yml con 2 de 2 pasos guardados. El test S160 sólo
  cubre cron (tests/test_guard_token_vacio_cron_s160.py:18-22). reproc-chunked.yml:136-137 pasa el par.
- Mecanismo distinto al supuesto: con `EARTHDATA_TOKEN=""` earthaccess NO hace `find_or_create_token`; toma la cadena
  vacía como token (auth.py:305, `if user_token is not None`). El par se manda igual: el bypass de /profile
  (fetch.py:110) exige token no vacío, así que `Store.set_requests_session` hace GET a urs.../profile con HTTP Basic.
  `v4t_03_token_vacio_logins.py` → `salida_03/`: 32 peticiones Basic a /profile en 8 intentos de `auth()` (4 por
  intento en mi mock, 0.17 y 0.19); CONTROL+ con la variable ausente: POST a find_or_create_token con Basic. El número
  exacto de peticiones reales depende de las respuestas de URS: SIN DATO. Sólo ocurre por despacho manual con el
  secreto borrado; hoy existe (insumo `secretos_nombres_fechas.txt`: actualizado 2026-10-08T18:07:05Z).

### 388: El pipeline nunca mira exp del JWT
- VEREDICTO: CONFIRMADO. Mi gravedad: 2 (auditor 2).
- `grep -rn -i "jwt|exp"` en pipeline/, scripts/ y workflows: el único lector es scripts/token_edad.py (control+: 2
  apariciones de `vencimiento_jwt`). earthaccess `_get_credentials` acepta cualquier valor (auth.py:305-307). Matiz: en el
  resultado no «se comportan igual», porque NASA responde «has expired» al JWT vencido (se detecta) y otra cosa al texto
  basura (puede no detectarse).

### 389: earthaccess sin pin
- VEREDICTO: CONFIRMADO EN PARTE. Mi gravedad: 1 (auditor 2).
- Sin pin: requirements.txt:1 «earthaccess>=0.9.0», nrt.yml:143 `pip install earthaccess`. REFUTADO «el CI instala
  0.19.0»: el log del run 41752185443 (2026-11-04 01:10 UTC) muestra 11 veces «earthaccess-0.17.0». Causa: nrt.yml:134
  usa Python 3.11 y PyPI declara `requires_python >=3.12` para 0.18.0 y 0.19.0 (>=3.11 para 0.17.0). Hay un pin implícito
  por la versión de Python. Además mis corridas dan resultados idénticos en 0.17 y 0.19 en todos los escenarios.

### 390: El primer aviso de renovar sale el 2026-11-28 12:00 UTC
- VEREDICTO: CONFIRMADO, condicionado al `exp`. Mi gravedad: 1 (auditor 1).
- token_edad.py:27 `DIAS_AVISO = 10`, `<=` en l. 48; cron 12:00 UTC (healthcheck l. 21). docs/S150_RESULTADO_MESES.md:213
  (752d348bc), TEXTO: «El token se rotó ese día; vence el 2026-12-07.» Si `exp` cae el 07-dic después de las 12:00 UTC
  (el secreto se actualizó a las 18:07 UTC del 08-oct), el primer `renovar` es el 28-nov 12:00 UTC con ~9,25 días; si
  cae antes de las 12:00, es el 27-nov. La hora exacta de `exp` es SIN DATO para mí (el auditor usa 18:03 sin que yo
  haya visto la fuente). El cron de GitHub puede llegar horas tarde.

## 4. Hallazgos nuevos

### V4T-01
- TÍTULO: Token con espacio o salto de línea final: token_edad dice «ok», requests falla antes de salir y el NRT queda verde sin datos
- ARCHIVO:LÍNEA: scripts/token_edad.py:32 (`(token or "").strip()`); pipeline/fetch.py:343 (`has_token` también con strip); earthaccess 0.17 auth.py:305-306 (usa el valor crudo); pipeline/fetch.py:1282 (`print(f"  WARN: Failed to fetch {platform}: {e}")`)
- QUÉ PASA: si el secreto queda con un salto de línea final, los dos lectores del proyecto lo limpian y lo dan por bueno,
  pero earthaccess arma `Authorization: Bearer <token>\n`; requests lanza `InvalidHeader` antes de enviar nada, que no
  es ni error de red ni credencial: va al WARN, 0 archivos, exit 0. El texto de esa excepción contiene el token, y la
  línea 1282 lo imprime entero en el log de un repo público (el enmascarado de GitHub depende de que reconozca el
  secreto multilínea: SIN DATO).
- CÓMO SE VE EN EL DASHBOARD: datos congelados; el healthcheck del token dice «ok»; sólo la staleness avisa (48 a 72 h).
- CÓMO REPRODUCIRLO: `python v4t_01_transporte_real.py --ea 017 --escenario vida --token "<jwt sintético>"$'\n' --salida salida_05/017_vida_token_con_salto.json` → `salida_05/`: 0 peticiones, 0 archivos, motivo `InvalidHeader`; `token_edad` → `{'estado': 'ok', ...}` (`salida_05/token_edad_con_salto.txt`).
- CONFIANZA: CONFIRMADO en el código y la simulación; SOSPECHA que GitHub conserve el salto final al guardar el secreto.
- GRAVEDAD: 3.

### V4T-02
- TÍTULO: La réplica de error de los tests S123/S124 no tiene __cause__ y por eso nunca ejercita la rama de status
- ARCHIVO:LÍNEA: tests/test_fetch_credential_dead_s123.py:43-55 (docstring TEXTO: «con __cause__ = HTTPError (que es donde sobrevive el status_code real)»; l. 55 `return RuntimeError(ex.response.text)` sin `from`); l. 153-162 usa esa forma para la descarga.
- QUÉ PASA: el test promete la forma de earthaccess pero entrega otra; todos los casos pasan por el regex del texto
  «has expired», y no hay test con `DownloadFailure` real ni con un 401 de texto neutro. Es la razón por la que 381 y
  382 siguen verdes en la suite. Relacionado con 381/382 (no duplicado: es el defecto del instrumento, no del código).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer l. 43-55; `salida_02_mecanismo.txt` muestra que con `__cause__` real el resultado no cambia (el status se pierde igual), o sea que un test con la forma real habría fallado con cuerpo neutro.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 3.

Duplicados: el mecanismo `bool(Response)` es la causa de 381 y el propio script del auditor lo nombra; lo fundo en 381.

## 5. SEGUIMIENTOS (fuera del eje)

- El mock de CMR con 0.19 repite el mismo gránulo en cada página (80 archivos en el control de vida): artefacto de mi
  instrumento con la paginación por `search-after` de 0.19, no del pipeline. No afecta a los veredictos (los casos de
  falla dan 0 archivos con cualquier paginación).
- earthaccess guarda en disco lo que LAADS devuelva con status 200; si un token malo se resolviera con redirección a
  una página HTML de login (200), el archivo sería HTML con nombre .hdf. No lo medí (sin red). SOSPECHA, gravedad SIN DATO.

## 6. VERIFICADO LIMPIO

- Vencimiento natural detectado: CONTROL+ control_cmr401_expired → EarthdataCredentialError en 0.17 y 0.19
  (`salida_01/resumen.jsonl`); vara: el texto real documentado en AUDIT_S122.md:47. Un EarthdataCredentialError no se
  atrapa en process_date (scripts/run_pipeline.py:216 sólo tiene `finally` en l. 374): el job queda rojo.
- 403 de EULA no aborta (cmr403_eula, descarga403_eula): correcto según el diseño de fetch.py:451-454.
- Guarda de token vacío en todos los pasos con el par de los workflows con cron: 0 sin guarda (`salida_04_inventario.txt`).
- Ningún otro lector de `exp` fuera de token_edad (grep con control positivo).

## 7. SIN DATO

- Texto real de CMR/LAADS ante token basura, revocado, de otra cuenta o sin la app LAADS: sin red a NASA por regla.
- Hora exacta de `exp` del token vigente (390).
- Si los correos de Actions llegan y se leen (383).
- Re-corrida de `f4t_03_pipeline_simulado.py` (corrida a nivel run_pipeline completo con sitecustomize): detenida sin
  salida por la parada de disco. Mi `v4t_01` cubre fetch_for_volcano más `informar_cobertura`, no el proceso entero.
- `f4t_02_guarda_token_vacio_shell.py`: copiado, no corrido (parada de disco).

## 8. FUERA DE ALCANCE

- Diseñar el arreglo de fetch.py (lo decide el orquestador con tag y sí de Nicolás, A45). Sólo anoto lo que el
  instrumento sugiere: leer el status sin `or` (`resp is None`), y clasificar `DownloadFailure` por el número de status
  de su mensaje o por `isinstance` más 401.
- Frontend y la experiencia del operador del OVDAS.
