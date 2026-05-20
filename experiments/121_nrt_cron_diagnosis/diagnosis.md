# Diagnóstico NRT cron — 2026-05-20

## Datos

- Fallos consecutivos: 19/20 últimos runs del workflow `nrt.yml`.
- Issue abierto: #1 priority-high desde 2026-05-20T10:01Z.
- Última falla: run `26157715302` a 2026-05-20T10:49Z (display: "NRT VRP Pipeline (both profiles)").
- Sample inspeccionado: runs `26157715302`, `26148667212`, `26139504143` (3 más recientes) + check breve `26130523128`, `26125940440` para distribución de víctimas.

## Patrón identificado

**Rama C — NASA Earthdata auth endpoint inalcanzable / saturado (no LANCE, pero la misma familia)**

El símptoma exacto es `ConnectTimeout` sobre TCP/443 hacia `urs.earthdata.nasa.gov` en el endpoint `/api/users/find_or_create_token`. El endpoint **no responde el TLS handshake** dentro del timeout configurado (60 s). No es 401 (Rama B descartada: credencial vive y no devolvió error de auth), no es timeout de job per-se (Rama A descartada: el `timeout-minutes` del workflow no dispara, lo que muere es el proceso Python con `exit code 1` después de agotar los 8 reintentos de `pipeline/fetch.py:auth()`). El volcán que cae es distinto en cada run (Calbuco, CorcovadoYanteles, Callaqui, Tolhuaca, Huequi, Lascar, Hudson — 7 vols únicos en 5 runs, **cero repetidos**), lo cual descarta Rama D (vol-específico): es lotería de qué worker pega contra el endpoint mientras está caído.

Es **el mismo evento físico** que documentamos en S47 (2026-05-16) y que motivó el extended retry a 8 intentos / ~22 min total. La diferencia es que esta ventana de degradación de `urs.earthdata.nasa.gov` está durando más que esa cobertura (>30 min de outage por ventana, con outages reincidentes cada cron).

## Evidencia

Stack trace idéntico en los 5 jobs fallidos de los 3 runs más recientes (extracto representativo, run 26157715302 / job CorcovadoYanteles):

```
2026-05-20T12:18:52  TimeoutError: timed out
2026-05-20T12:18:52  urllib3.exceptions.ConnectTimeoutError: (<HTTPSConnection(host='urs.earthdata.nasa.gov', port=443)>, 'Connection to urs.earthdata.nasa.gov timed out. (connect timeout=60.0)')
2026-05-20T12:18:52  urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='urs.earthdata.nasa.gov', port=443): Max retries exceeded with url: /api/users/find_or_create_token
2026-05-20T12:18:52    File "/home/runner/work/VRP-chile/VRP-chile/pipeline/fetch.py", line 176, in auth
2026-05-20T12:18:52      raise last_err if last_err else RuntimeError("auth failed")
2026-05-20T12:18:52  requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='urs.earthdata.nasa.gov', port=443): ... /api/users/find_or_create_token
2026-05-20T12:18:52  ##[error]Process completed with exit code 1.
```

Timing observado job-por-job (start → fail):

| Run | Job | Start | Fail | Duración |
|---|---|---|---|---|
| 26157715302 | Calbuco | 11:41:33 | 12:12:44 | 31m11s |
| 26157715302 | CorcovadoYanteles | 11:47:52 | 12:18:54 | 31m02s |
| 26148667212 | Callaqui | 08:18:47 | 08:49:46 | 30m59s |
| 26139504143 | Tolhuaca | 04:10:02 | 04:41:01 | 30m59s |
| 26139504143 | Huequi | 04:28:04 | 04:59:05 | 31m01s |

Los 5 jobs mueren a ~31 minutos exactos. Eso coincide con: ~9 min de setup (checkout + pip install) + 8 intentos de `auth()` con backoffs `0/10/30/60/120/240/360/480` + un connect-timeout de 60 s por intento ≈ **22 min de reintentos efectivos**. No es muerte por `timeout-minutes` del workflow (ese sería más limpio); es muerte por el `raise last_err` después de agotar la budget de retries.

Distribución de víctimas (5 runs):

```
26157715302  Calbuco, CorcovadoYanteles
26148667212  Callaqui
26139504143  Tolhuaca, Huequi
26130523128  Lascar
26125940440  Hudson
```

7 vols únicos, 0 repetidos → **no es vol-específico**, es lotería de qué worker pega contra el endpoint mientras está caído.

## Root cause

**El servidor de auth de NASA Earthdata (`urs.earthdata.nasa.gov:443`, endpoint `/api/users/find_or_create_token`) está rechazando conexiones TLS — no devuelve error 5xx, simplemente no responde el handshake dentro de 60 s**. Pensado como fenómeno: es exactamente lo que pasa cuando un balancer de NASA está saturado o un mantenimiento dropea SYN-ACKs, no como cuando "el servidor responde 503". El paquete sale del runner, llega a NASA, y nada vuelve dentro del minuto.

Esto **ya nos pasó en S47** (ver `pipeline/fetch.py:146-150`, comentario "9 runs consecutivos fallidos 2026-05-16"). El fix en S47 fue extender retries a 8 intentos cubriendo ~22 min. En esta ventana de degradación 2026-05-20 esos 22 min no alcanzan: la ventana de outage de NASA está siendo más larga que nuestra budget, **o el cron cae justo durante una de esas ventanas y no se vuelve a intentar hasta el próximo cron 2 h después** (cuando ya pudo recuperarse). Pero porque la ventana de outage parece estar reincidiendo cada par de horas en los runs auditados (10:49, 07:42, 03:31, 23:01, 21:18), la mayoría de los crons caen dentro de ventana de outage.

No hay nada que arreglar en nuestro código de lógica MIROVA — esto es infraestructura NASA. Hay que **hacer el fallo más barato** (no perder 31 min por job, no ensuciar el dashboard) y **tener cobertura más amplia para outages largos**.

## Fix propuesto

Para T2, tres cambios concretos, en orden de impacto:

1. **Detección rápida del outage en `pipeline/fetch.py:auth()`**: antes de entrar en el retry loop largo, hacer un probe HTTPS rápido (5 s) a `urs.earthdata.nasa.gov`. Si el probe ya falla por connect-timeout en el primer intento, **acortar la budget a 2-3 reintentos rápidos** (~3 min total) en vez de los 8 actuales (22 min), y salir con un `RuntimeError("NASA_AUTH_UNREACHABLE")` distinguible. Esto reduce el costo de fallo de 31 min/job a <5 min/job — el cron tarda menos en darse cuenta y deja runners libres más rápido.

2. **Tratar `NASA_AUTH_UNREACHABLE` como `neutral` (no `failure`) en el workflow**: en `.github/workflows/nrt.yml`, capturar ese exit code distinguible y emitir `exit 0` con un warning, para que el dashboard NO marque el cron como fallo cuando el outage es upstream. Mantenemos el log para auditoría pero no contaminamos el badge ni gatillamos issue auto-abierto. (Alternativa más conservadora: dejar `exit 1` pero adornar el title del run con `[NASA_DOWN]` para que el monitor agente lo skipee al alertar.)

3. **Cobertura de ventanas largas**: agregar un cron secundario "retry-failed-nrt" que dispare 90 min después del cron principal solo si el anterior falló, para captar la recuperación de NASA dentro del mismo ciclo de 2 h. Hoy si el cron principal cae dentro del outage, perdemos esa franja entera; con el retry tenemos una segunda chance sin esperar al siguiente cron base.

No tocamos `EARTHDATA_PASSWORD` (la credencial no es el problema), no agregamos `--no-retry`, no cambiamos los coeficientes Wooster ni nada del pipeline científico. Esto es plumbing de auth puro.

## Criterio de validación

≥80% success rate en próximos 5 runs después del fix (al menos 4/5 verdes). Si la ventana de outage NASA persiste, los runs que caigan dentro de ella deben marcar `neutral`/skip — no `failure` — y no gatillar issue auto-abierto.
