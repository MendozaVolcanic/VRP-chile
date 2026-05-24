# F51 — NRT cron down investigation (S77)

**Fecha**: 2026-05-24
**Tarea**: diagnóstico read-only del bloqueo NRT cron tras reportar Nicolás "el NRT no está funcionando".
**Modo**: investigación only. NO se modificó workflow ni pipeline.
**Predecesor**: `experiments/129_nrt_cron_nasa_azure_diagnosis/diagnosis.md` (S71, 2026-05-20) — propuso el fix TOKEN, implementado S72 commit `137371b1`, pero **insuficiente**: ver causa raíz §3.

---

## Diagnóstico ejecutivo (TL;DR)

NRT cron dispara cada ~2h sin problema (scheduler GH Actions sano), pero **falla 90 % de las corridas** (10/100 success en las últimas 100). Causa raíz consistente: `RuntimeError: NASA_AUTH_UNREACHABLE` lanzado por `pipeline/fetch.py:auth()` cuando un probe TCP a `urs.earthdata.nasa.gov:443` falla desde los runners Azure de GitHub.

El fix S72 (`EARTHDATA_TOKEN` bypass, commit `137371b1`) sí está aplicado (secret presente desde 2026-05-21, exportado en `nrt.yml` líneas 176/202/222), **pero está blindado por un probe-gate previo (S70-0 commit `c777db79`) que aborta antes de que `earthaccess.login()` pueda usar el token**. El probe corre incondicionalmente → cuando NASA throttle TCP al endpoint desde IPs Azure (DoS-mitigation colateral confirmado forum.earthdata.nasa.gov t=2764), aborta sin probar el camino token que precisamente está diseñado para no tocar ese host.

Tier A (11 volcanes) tienen último record `2026-05-23 07:25 UTC` — **delta ≈ 40 h** vs ahora (2026-05-24 23:00 UTC). NRT operacional roto: PRs F46/F47 mergeados no se ven en data nueva.

---

## Cuándo dejó de funcionar

- **Último success real con commits de data**: run `26354576212` el `2026-05-24T06:58:38Z`. Commiteó NRT de 11 Tier A entre 04:00-04:34 UTC (procesando día 2026-05-23 noche).
- **Último success anterior**: `2026-05-22T10:50:24Z`.
- **Patrón en 100 runs**: 10 success / 90 failure. Failures consecutivas tras último success: 7. Total fallos > success en ratio 9:1 desde mediados de mayo.
- **NRT-monitor.yml** (workflow alerta 3+ fallos): corre OK pero no eleva alerta visible a Nicolás (verificar destino de alerta).
- **nrt-retry.yml**: dispara cada ~2h, pero termina en 5-9s — probablemente detecta NASA aún down y aborta sin hacer trabajo.

---

## Causa raíz — top 3 hipótesis ordenadas por probabilidad

### H1 (≈ 80 %) — Probe-gate invalida el token-bypass

**Mecanismo**: en `pipeline/fetch.py`, función `auth()`:

```python
probe_ok = _probe_nasa_auth(timeout=5.0)   # ← TCP a urs.earthdata.nasa.gov:443
if probe_ok:
    delays = [0, 10, 30, 60, 120, 240, 360, 480]
else:
    delays = list(_PROBE_FAIL_DELAYS)       # ~2 min

# ... retry loop ...
if not probe_ok:
    raise RuntimeError("NASA_AUTH_UNREACHABLE: ...")   # ← aborta SIEMPRE si probe falló
```

El bloque final `if not probe_ok: raise` **aborta incluso si el retry loop adentro consiguió autenticar con token**, y aun si consiguiera, el budget se acortó a 2 min reduciendo la ventana del token para responder.

Concretamente: cuando NASA throttle TCP al endpoint desde Azure (que es exactamente el escenario S71-S72 documentado), el probe falla → `probe_ok=False` → el flujo `earthaccess.login(strategy="environment")` con token jamás consigue ejecutarse libre del bloqueo TCP, porque la lógica está estructurada como "probe primero, si falla = abort".

**El token bypass se diseñó para NO tocar `urs.earthdata.nasa.gov`** durante auth (línea 230 de `earthaccess/auth.py`: solo setea Bearer header en sesión). Pero el probe-gate lo bloquea antes.

**Evidencia**: 5 logs de fallos consecutivos (runs 26370345192, 26367325353, 26358078088, 26350871596, 26345702310) muestran el mismo `RuntimeError: NASA_AUTH_UNREACHABLE` con `ConnectTimeoutError(host='urs.earthdata.nasa.gov')`. Si el token-bypass funcionara, el error sería distinto (o sería un success).

Verificación local (red Chile residencial Nicolás 2026-05-24 23:05 UTC): `curl https://urs.earthdata.nasa.gov/profile` → HTTP 302 en 0.65s. NASA upstream OK. Problema localizado en runners Azure.

### H2 (≈ 12 %) — `EARTHDATA_TOKEN` expirado o inválido

Token tiene vida 60 días. Creado 2026-05-21 → expira ~2026-07-20, **aún válido**. Pero si fue revocado manualmente o nunca se completó la generación, `earthaccess` haría fallback silencioso a USERNAME/PASSWORD que sí golpea `find_or_create_token` y falla. No es la hipótesis principal porque el log muestra que la falla ocurre antes (probe), no en la fase de auth-with-credentials. Pero validable.

### H3 (≈ 8 %) — Degradación NASA real más larga que budget retry

S47 ya subió retries a 22 min totales por degradaciones de 5+ min observadas. Si NASA está caída para Azure desde hace 36h continuas, ningún retry alcanza. **Pero** local Chile sigue respondiendo OK, lo que hace muy improbable que la causa sea outage NASA absoluto. Apunta a throttling por origen ASN, que el token bypass debería resolver — volviendo a H1.

---

## Plan fix con ETA

| Paso | Responsable | ETA | Riesgo |
|---|---|---|---|
| **1. Hacer probe-gate condicional al modo de auth** | Claude (S77 T2) | 30 min | Bajo. Cambio de ~10 líneas en `pipeline/fetch.py`. Si `EARTHDATA_TOKEN` está seteado: skip probe (porque token no toca host probado). Si no: comportamiento actual. | 
| 2. Test local con TOKEN seteado | Claude | 10 min | Validar que `auth()` retorna OK sin TCP al endpoint. |
| 3. Validar en GH Actions con workflow_dispatch | Claude | 5 min cron + observar | Si éxito → automated NRT vuelve solo. |
| 4. Verificar token EARTHDATA_TOKEN realmente sirve | Nicolás (5 min) | hoy | Login `urs.earthdata.nasa.gov` → Profile → ver "Generate Token" → si dice "expired" / no muestra el actual, regenerar y actualizar secret. |
| 5. Si todo lo anterior falla → self-hosted runner local Nicolás | Nicolás | 1-2 h | Plan en S71 diagnosis §4. Fallback fuerte. |

**Fix mínimo propuesto** (NO aplicado en este PR, solo documentado):

```python
# pipeline/fetch.py:auth()
has_token = bool(os.getenv("EARTHDATA_TOKEN"))
# Si tenemos token, skip probe: earthaccess no toca urs.earthdata.nasa.gov en este modo.
if has_token:
    probe_ok = True   # asumir OK, fail-fast si login() falla con error distinto
else:
    probe_ok = _probe_nasa_auth(timeout=5.0)
```

Y el `if not probe_ok: raise NASA_AUTH_UNREACHABLE` final debe gatear por `not has_token and not probe_ok`.

---

## Workaround corto plazo

1. **Reproc local Nicolás (1 hora)**: `python scripts/run_pipeline.py --profile mirova_equivalent --start 2026-05-23 --end 2026-05-24` sobre los 11 Tier A. Recupera los 2 días de gap. Local funciona porque NASA Earthdata responde sub-segundo desde Chile residencial.
2. **No depender del NRT GitHub para validar F46/F47 hasta que se aplique el fix**: validación de fixes recientes debe correr localmente.
3. **Verificar manualmente que `sync-mirova-csv.yml` (PR #187 recién mergeado) sí corrió** una vez al menos — listado actual no muestra runs.

---

## Workflows asociados (estado)

| Workflow | Estado | Notas |
|---|---|---|
| `nrt.yml` | ROTO (90 % failure) | Causa raíz H1 |
| `nrt-monitor.yml` | Corre OK | Verificar a dónde envía alerta |
| `nrt-retry.yml` | Corre pero termina en 5-9s | Probable mismo bloqueo NASA, abort early |
| `sync-mirova-csv.yml` (PR #187) | Activo, sin runs aún | Verificar trigger (cron / dispatch only?) |

---

## Secrets verificados (sin leer valores)

- `EARTHDATA_USERNAME` ✅ (set 2026-04-04)
- `EARTHDATA_PASSWORD` ✅ (set 2026-04-04)
- `EARTHDATA_TOKEN` ✅ (set 2026-05-21, vida útil ~60 días → ~2026-07-20)

Imports pipeline OK: `from pipeline import process_modis, process_viirs, store, fetch` sin error (excepto warning pyhdf esperado en Windows).

---

## Apéndice — comandos de reproducción

```bash
# Listar últimas corridas NRT
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml --limit 20

# Ver log de la falla más reciente
gh run view <id> -R MendozaVolcanic/VRP-chile --log-failed | grep -E "(RuntimeError|NASA_AUTH)" | head -5

# Verificar timestamp último record por volcán
python -c "import json, pathlib, datetime as dt; ..."  # script en este diagnóstico §"Cuándo dejó de funcionar"

# Verificar NASA upstream desde local
curl -sS -o /dev/null -w "HTTP=%{http_code} time=%{time_total}s\n" --connect-timeout 10 https://urs.earthdata.nasa.gov/profile
```
