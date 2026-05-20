# Fix NRT cron — S70-0 T2 (2026-05-20)

## Qué pasaba (lectura del fenómeno)

NASA Earthdata mantiene el servidor de autenticación (`urs.earthdata.nasa.gov`)
detrás de un balancer que viene mostrando ventanas largas de degradación: el
paquete del runner GitHub Actions llega a NASA, pero el handshake TLS no
completa dentro de los 60 segundos del connect-timeout. No es un 5xx (no es
"el servidor responde mal"), es lisa y llanamente que NASA no devuelve nada —
como un balancer saturado que dropea SYN-ACKs. T1 (commit `c6373aa`) midió
19/20 runs consecutivos del cron `nrt.yml` fallando con este patrón, cada job
muriendo a ~31 minutos exactos. Esos 31 minutos eran ~9 minutos de setup
(checkout + pip install) más los 22 minutos de retry budget de `auth()`
(8 reintentos con backoff `0/10/30/60/120/240/360/480` + 60s connect-timeout
por intento).

El volcán que caía era distinto en cada run (7 únicos en 5 runs, ningún
repetido) → lotería de qué worker pega contra el balancer mientras está caído.
Es **el mismo evento físico** que tratamos en S47 (commit en `pipeline/fetch.py`
líneas 146-150). En esta ventana de mayo, los outages NASA están durando más
de los 22 min que nuestro retry budget cubría, y el siguiente cron sólo
intenta de nuevo 2h después, cuando ya pudo haberse recuperado.

## Qué cambió (decisión Nicolás)

**Política conservadora**: badge sigue rojo cuando NASA cae. Distinción visual
vía sufijo `[NASA_DOWN]` (warning annotation + job summary), pero el exit code
sigue siendo 1 — no contaminamos el comportamiento de alerta del cron. La
sesión nueva era hacer **el fallo más barato**, no esconderlo.

Tres cambios concretos:

### 1. `pipeline/fetch.py`: probe TCP rápido + budget acortado

- Nueva función `_probe_nasa_auth(timeout=5.0)`. Hace un `socket.create_connection`
  a `urs.earthdata.nasa.gov:443` con timeout de 5 segundos. Devuelve `True` si
  el handshake TCP completa, `False` ante cualquier error (timeout, OSError,
  connection refused).
- `auth()` ahora llama al probe al inicio:
  - **Probe OK** → comportamiento normal con `delays = [0, 10, 30, 60, 120, 240, 360, 480]`
    (8 reintentos, ~22 min total). Igual que S47.
  - **Probe falla** → budget corto `_PROBE_FAIL_DELAYS = [0, 30, 90]` (3 reintentos,
    ~2 min total). Si los 3 fallan, lanza `RuntimeError("NASA_AUTH_UNREACHABLE: ...")`
    con mensaje distinguible. Si NASA se recupera en uno de esos 3 intentos cortos,
    igual seguimos adelante normal.
- Tests: `tests/test_auth_probe.py` con 7 tests (probe TRUE/FALSE para distintos
  errores de red, auth() lanza unreachable cuando probe falla, auth() no lanza
  unreachable cuando el login se recupera, auth() normal con probe OK).

Costo de fallo cuando NASA está caída: **~3 min por job** en vez de ~31 min.
Reduce desperdicio de minutos GitHub Actions ×9 vols × cada cron 2h cuando
NASA está down. Sin cambios cuando NASA está OK (probe pasa en <1 segundo).

### 2. `.github/workflows/nrt.yml`: marker NASA_DOWN

- Los 3 steps que corren `python scripts/run_pipeline.py` ahora hacen
  `2>&1 | tee -a pipeline.log` con `set -o pipefail`. Captura la salida del
  pipeline a archivo sin perder el stream a stdout del runner.
- Nuevo step `Detect NASA_AUTH_UNREACHABLE (tag run as NASA_DOWN)` corre con
  `if: failure()`. Si encuentra `NASA_AUTH_UNREACHABLE` en `pipeline.log`,
  emite `::warning title=NASA_DOWN::...` (que aparece como annotation en el
  run summary del workflow) y agrega un bloque al `GITHUB_STEP_SUMMARY` con
  el volcán afectado.
- **Exit code se mantiene en 1** — el job sigue fallando, badge rojo. Esto es
  decisión Nicolás S70-0: alerto siempre, distingo visualmente.

### 3. `.github/workflows/nrt-retry.yml` (nuevo): cron secundario

- Trigger: `30 1-23/2 * * *` (01:30, 03:30, ..., 23:30 UTC). Offset +30 min
  respecto al cron principal `nrt.yml` (00, 02, 04, ...).
- Inspecciona el último run de `nrt.yml` vía `gh run list` + `gh api`. Si
  concluyó en `failure` **y** tiene la annotation `NASA_DOWN`, dispara
  `gh workflow run nrt.yml` para retriggerear el cron principal.
- Si NASA sigue caída, el retry también fallará rápido (~3 min por job) gracias
  al cambio #1, pero no acumula runs porque sólo lo dispara su propio cron
  schedule.
- Beneficio: captar recuperación de NASA dentro del mismo ciclo de 2h sin
  esperar al próximo cron base, sin riesgo de loops.

## Política de badge (confirmada)

Conservador: badge rojo cuando NASA cae, con sufijo visual `[NASA_DOWN]` en
warnings + step summary. NO cambia comportamiento de alerta. Si Nicolás decide
después que el ruido es excesivo, queda el camino abierto para volver el
warning a `exit 0` cambiando solo el exit code (no requiere rediseño).

## Plan de validación

1. Push del fix y revisión spec/quality del controller.
2. Disparo manual: `gh workflow run nrt.yml` desde la rama mergeada.
3. **Si NASA sigue caída en el momento del push**:
   - Cada job termina ahora en ~3 min (no 31).
   - Badge rojo, pero warning `NASA_DOWN` visible en cada job fallido.
   - 30 min después: `nrt-retry.yml` debería ejecutarse automáticamente y
     retriggerear `nrt.yml` una vez más.
   - Si NASA se recuperó entre el principal y el retry, el retry debería verde.
4. **Criterio de aceptación**: ≥4/5 success en próximos 5 runs (~10 horas después
   del fix). Si todos siguen rojos por NASA_DOWN, el comportamiento esperado es:
   - Cada fallo es barato (~3 min/job, no ~31 min).
   - Warnings claramente identifican el outage upstream.
   - El issue auto-abierto correlaciona con el sufijo NASA_DOWN.
5. Si la mejora no es ≥80%, volver a diagnóstico — puede haber una segunda
   causa raíz no cubierta por el probe (DNS, runner network, etc.).

## Archivos modificados/creados

- `pipeline/fetch.py` — `_probe_nasa_auth()` + branch corto en `auth()` + constantes
  `NASA_AUTH_HOST`, `NASA_AUTH_PORT`, `_PROBE_FAIL_DELAYS`.
- `tests/test_auth_probe.py` — 7 tests TDD (probe + auth() integration).
- `.github/workflows/nrt.yml` — `tee -a pipeline.log` en 3 steps + step
  `Detect NASA_AUTH_UNREACHABLE`.
- `.github/workflows/nrt-retry.yml` — nuevo workflow con cron +30 min.
- `experiments/121_nrt_cron_diagnosis/fix_applied.md` — este reporte.

## Lo que NO se tocó

- Coeficientes Wooster, umbrales NTI, paths A/B/C/D — nada del pipeline
  científico. Esto es plumbing puro de auth.
- `EARTHDATA_USERNAME` / `EARTHDATA_PASSWORD` secrets — la credencial vive y
  funciona, el problema es upstream.
- Monkeypatch `_request_with_nasa_timeout` (S47) — sigue intacto, los 60s de
  read-timeout cubren bien el caso "NASA lento pero responde".
- IPv4 force `_ipv4_only_getaddrinfo` (S35) — sigue intacto, mitiga otra
  causa diferente (routing IPv6 degradado en runners).
