# Diagnosis NRT cron failure — NASA Earthdata desde GH Actions (Azure)

**Fecha**: 2026-05-20  
**Tarea**: S71 T1 — diagnóstico read-only del bloqueo persistente NRT cron post PR #103.  
**Modo**: solo investigación, NO modificar código, NO commitear.

---

## Resumen ejecutivo (TL;DR)

- **Verdict**: NO hay precedente público documentado de "NASA Earthdata bloquea
  Azure / GH Actions runners" como política. La causa más probable es **DoS
  mitigation de NASA disparada por el patrón de tráfico shared egress de Azure
  GH-hosted runners** (muchos jobs CI/CD del mundo entero saliendo por el
  mismo bloque /16 Azure, NASA reacciona a la suma agregada → "collateral
  damage" que la propia NASA reconoce en su forum).
- **Mitigación recomendada (1)**: switch a auth por **token persistente
  `EARTHDATA_TOKEN`** en `earthaccess`. La librería 0.17.0 que ya tenemos
  instalada lo soporta de fábrica y **evita el POST a
  `/api/users/find_or_create_token`** que es exactamente el endpoint que
  timeout-ea. El token tiene vida útil de ~60 días, se genera 1 vez localmente
  (donde NASA sí responde), se guarda en GH Secrets, y `auth()` solo lo lee
  del env — no hace request a EDL hasta que llega el momento de bajar el
  granule (que va contra LAADS DAAC, otro hostname).
- **Costo de implementación**: ~30 minutos. Diff < 15 líneas en
  `pipeline/fetch.py` + setear secret + recordatorio de rotación cada 50 días.
- **Si el token también falla** (porque NASA bloquea Azure a nivel de red,
  no de endpoint): fallback estructural recomendado = **self-hosted runner en
  máquina local de Nicolás** (Chile). Costo: 1h setup + electricidad. Es la
  única opción que garantiza la IP origen que sabemos funciona.

---

## Sección 1 — Verdict sobre bloqueo NASA-Azure

### Evidencia recolectada

**A favor de "NASA bloquea Azure intencionalmente"**: ninguna directa.

**A favor de "es DoS mitigation colateral, no bloqueo intencional"**:

1. Forum oficial NASA Earthdata thread t=2764 ("Connection to
   urs.earthdata.nasa.gov timed out"): NASA reconoce que
   - "errors are often transient, retry over 24-hour period"
   - "NASA has to employ measures to prevent denial-of-service attacks, so
     there can be collateral damage when a site tries to connect too many
     times in a short period"
   - menciona específicamente "client software combined with enterprise
     firewalls" como factor.
2. GitHub Actions runners comparten un pool de IPs de Azure que es
   gigantesco y se rota constantemente. Cualquier servicio externo que mire
   "requests por /16 Azure por minuto" verá cifras altísimas porque sale CI
   de medio mundo por esos bloques.
3. No hay anuncio público de NASA Earthdata en 2024-2026 sobre bloqueo
   intencional de Azure ASN. Si fuera política, lo habrían anunciado: NASA
   Earthdata depende de proveedores cloud para que sus propios datasets se
   procesen (AWS, GCP, Azure). Bloquear a Azure sería contra su misión.
4. El patrón observado (timeout 5s consistente en cron 15Z, 18Z, 21Z, 23Z,
   02Z) calza con rate-limit/firewall por origen-ASN, no con un bloqueo
   estático: si fuera bloqueo estático, los timeouts serían inmediatos (RST)
   en lugar de TCP timeout (paquetes silenciosamente dropeados, que es lo
   que hace un firewall DoS).

**Hipótesis alternativa más fuerte que "NASA bloquea Azure"**: NASA tiene un
WAF/rate-limiter (probablemente Akamai o similar) que mira "POSTs a
`/api/users/find_or_create_token` por bloque /16 origen por minuto" y al
superar un umbral mete a ese bloque en greylist temporal (drop silencioso).
Como Nicolás hace 5 crons al día y comparte IP pool con miles de otros CI
jobs, el bloque /16 está crónicamente en greylist desde el punto de vista
del cron VRP.

**Por qué importa la distinción**: si fuera bloqueo permanente de Azure por
política, no nos serviría usar token — fallaría también el POST de descarga.
Si es DoS-mitigation contra el endpoint de tokens específicamente, **evitar
ese endpoint es la cura completa**. La evidencia (descargas funcionaron
históricamente en este mismo pipeline antes del régimen actual de fallos)
apunta a lo segundo.

### Veredicto

**Probabilidad subjetiva NASA-bloquea-Azure-intencional**: ~10%  
**Probabilidad DoS-mitigation-colateral-sobre-endpoint-de-tokens**: ~70%  
**Probabilidad routing-intermitente-Azure-NASA**: ~15%  
**Otros (cert expirado, DNS, etc.)**: ~5%

Las 3 hipótesis más probables convergen en la misma mitigación: **evitar
golpear `find_or_create_token` desde el runner**.

---

## Sección 2 — earthaccess auth modes (análisis código fuente)

### Hallazgo crítico

**`earthaccess 0.17.0` (la que ya tenemos instalada) soporta nativamente
auth por token preexistente que NO golpea `find_or_create_token`.**

Path en filesystem:
`C:\Users\nmend\AppData\Local\Programs\Python\Python312\Lib\site-packages\earthaccess\auth.py`

### Modos de auth disponibles

`login(strategy="...")` acepta 3 estrategias:

| strategy | Lee de | Llama a `find_or_create_token`? |
|---|---|---|
| `interactive` | stdin (user/pass) | **SÍ** (`_get_credentials` → `_find_or_create_token`) |
| `netrc` | `~/.netrc` o `~/_netrc` (user/pass) | **SÍ** |
| `environment` | env vars | **CONDICIONAL** — ver abajo |

### El modo "environment" tiene dos sub-modos (líneas 284-297 de auth.py):

```python
def _environment(self) -> bool:
    username = os.getenv("EARTHDATA_USERNAME")
    password = os.getenv("EARTHDATA_PASSWORD")
    token = os.getenv("EARTHDATA_TOKEN")

    if (not username or not password) and not token:
        raise LoginStrategyUnavailable(...)

    return self._get_credentials(username, password, token)
```

Y en `_get_credentials` (líneas 299-325):

```python
def _get_credentials(self, username, password, user_token) -> bool:
    if user_token is not None:                    # <-- camino TOKEN
        self.token = {"access_token": user_token}
        self.authenticated = True
    elif username is not None and password is not None:  # <-- camino user/pass
        self.username = username
        self.password = password
        token_resp = self._find_or_create_token()  # <-- AQUÍ está el endpoint que falla
        ...
```

**Conclusión literal del código**: si seteamos `EARTHDATA_TOKEN` en el env
del runner, `_get_credentials` toma el camino del `if user_token is not None`
y **nunca llama a `_find_or_create_token`**. La sesión queda autenticada con
el header `Authorization: Bearer <token>` (línea 230 de auth.py: `session.headers["Authorization"] = f"Bearer {self.token['access_token']}"`).

### Implicancia operativa

- El probe TCP a `urs.earthdata.nasa.gov:443` puede seguir fallando — no
  importa. earthaccess con token no toca ese host (al menos no durante la
  fase de auth).
- Las descargas reales van a hostnames de los DAACs
  (`ladsweb.modaps.eosdis.nasa.gov`, `nsidc-cumulus-prod-protected.s3.amazonaws.com`,
  etc.), que son distintos de `urs.earthdata.nasa.gov` y han funcionado en
  el pipeline históricamente.
- Si NASA estuviera bloqueando ASN Azure completo (no solo el endpoint de
  tokens), las descargas también fallarían — pero PR #103 documenta que la
  fase que falla es **`auth()`**, no `download_granules()`. Eso es exactamente
  el síntoma esperado bajo la hipótesis "DoS-mitigation sobre el endpoint
  de tokens".

### Cómo generar un token

Dos opciones:

**Opción A (recomendada, online, sin Python)**: dashboard EDL.
1. Login en https://urs.earthdata.nasa.gov/
2. Profile → "Generate Token"
3. Copy → guardar en GH Secret `EARTHDATA_TOKEN`.
4. Vida útil: 60 días, renovable.

**Opción B (programática, una sola vez localmente)**:
```python
import earthaccess
auth = earthaccess.login(strategy="environment")  # usa USERNAME/PASSWORD locales
print(auth.token["access_token"])
# copiar → GH Secret
```

---

## Sección 3 — Diff propuesto para `pipeline/fetch.py`

**No se aplica. Solo pseudo-código documentado.**

### Estado actual (líneas 85-122)

```python
def auth():
    """..."""
    netrc_path_unix = os.path.expanduser("~/.netrc")
    netrc_path_win = os.path.expanduser("~/_netrc")
    has_netrc = os.path.exists(netrc_path_unix) or os.path.exists(netrc_path_win)

    delays = [0, 5, 15, 45]
    last_err = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        try:
            earthaccess.login(strategy="environment")  # <-- llama find_or_create_token si solo hay USER/PASS
            return
        except Exception as e:
            last_err = e
        if has_netrc:
            try:
                earthaccess.login(strategy="netrc")    # <-- también llama find_or_create_token
                return
            except Exception as e:
                last_err = e
    raise last_err if last_err else RuntimeError("auth failed")
```

### Cambio propuesto (NO aplicado)

```python
def auth():
    """Authenticate with NASA Earthdata.

    S71 T1: orden de preferencia ajustado para evitar find_or_create_token
    cuando NASA bloquea/rate-limita ese endpoint desde IPs Azure (GH Actions).
    Si EARTHDATA_TOKEN está seteado, earthaccess lo usa directo como Bearer
    sin POST a urs.earthdata.nasa.gov/api/users/find_or_create_token.
    """
    import os
    import time
    has_token = bool(os.getenv("EARTHDATA_TOKEN"))
    netrc_path_unix = os.path.expanduser("~/.netrc")
    netrc_path_win = os.path.expanduser("~/_netrc")
    has_netrc = os.path.exists(netrc_path_unix) or os.path.exists(netrc_path_win)

    delays = [0, 5, 15, 45]
    last_err = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        # PRIMARIO: si hay token, lo usa directo (no toca find_or_create_token)
        try:
            earthaccess.login(strategy="environment")  # internamente prioriza TOKEN sobre USER/PASS
            return
        except Exception as e:
            last_err = e
        # FALLBACK: netrc si existe (solo dev local)
        if has_netrc:
            try:
                earthaccess.login(strategy="netrc")
                return
            except Exception as e:
                last_err = e

    # Mensaje de error mejorado: distinguir "no había token" de "fallaron todos los modos"
    if not has_token:
        raise RuntimeError(
            f"auth failed and EARTHDATA_TOKEN not set. "
            f"Regenerá el token en https://urs.earthdata.nasa.gov/profile y "
            f"actualizá el secret. Último error: {last_err}"
        )
    raise last_err if last_err else RuntimeError("auth failed")
```

**Notas**:
- La función `_environment()` de earthaccess ya prioriza `EARTHDATA_TOKEN`
  sobre `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` (líneas 284-297). El cambio
  en `auth()` es mínimo: agregar `has_token` para el mensaje de error, pero
  no hay que cambiar la llamada a `login(strategy="environment")`.
- Setear el secret en GH: Settings → Secrets and variables → Actions → New
  repository secret → `EARTHDATA_TOKEN`.
- El workflow `nrt.yml` debe exportar el secret: agregar
  ```yaml
  env:
    EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}
  ```
  al step que invoca el pipeline (junto a las dos vars existentes).
- Dejar `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` como fallback. Si el token
  expira (60 días) y no fue renovado, el pipeline cae en username/password
  que volverá a fallar — el mensaje de error guía la solución.

### Plan de rotación

- Token vida útil 60 días. Crear un workflow_dispatch manual que solo Nicolás
  invoca al recibir alerta "<10 días para expirar" (vía email del propio EDL
  o un cron de chequeo en máquina local).
- O setear un recordatorio en calendario cada 50 días.

---

## Sección 4 — Alternativas estructurales (priorizadas)

### 1. Self-hosted runner en máquina local (Nicolás Chile) — **fallback fuerte**

**Pros**:
- IP origen Chile residencial: comprobada hoy que NASA responde <1s.
- Sin límite de tiempo por job (vs 6h hard limit GH-hosted).
- Tests locales pyhdf (MODIS) viables — actualmente bloqueados por
  Windows-pyhdf-roto, pero un self-hosted Linux WSL resuelve eso.
- Costo monetario: ~$0 (PC ya prendida la mayoría del tiempo).

**Cons**:
- Disponibilidad atada al uptime del PC de Nicolás. Si apaga el PC, no
  hay cron.
- Setup inicial: instalar runner agent, configurar systemd o Task Scheduler,
  exponer al repo, manejar secrets locales.
- Si se accede al repo desde otro lugar (laptop), hay que repetir.
- Setup ~1-2 h primera vez. Mantenimiento ~30 min al mes (updates).

**Cuándo escalar a esto**: si el token tampoco resuelve el problema (porque
NASA esté bloqueando el ASN Azure entero, no solo el endpoint de tokens).

### 2. VPS pequeño en región fuera de Azure-US (DigitalOcean, Hetzner)

**Pros**:
- Independiente del PC local de Nicolás (uptime ~99.9%).
- IP estática conocida: si esa IP individual cae en greylist, se puede
  pedir review a NASA.
- Costo: ~$4-6/mes (instancia 1 vCPU + 1 GB).

**Cons**:
- Costo monetario continuo.
- Setup similar a self-hosted runner.
- Si NASA es restrictivo con datacenters cloud en general (no solo Azure),
  podría caer en el mismo problema.

**Cuándo escalar a esto**: si el self-hosted local no es viable por uptime
del PC, y el token no resuelve.

### 3. Tarea programada Windows local + push a repo

**Pros**:
- Más simple que self-hosted runner: solo Task Scheduler + script que
  corre `python -m pipeline.run_pipeline ... && git commit && git push`.
- Sin runner agent ni nada de GH Actions.

**Cons**:
- Pierde la matriz por volcán (paralelización GH Actions).
- 45 volcanes serialmente desde el PC local: ~50-90 min por cron.
- Git auth desde el PC local con token PAT que hay que rotar también.
- Si Nicolás está trabajando, el cron compite por CPU/red.

**Cuándo escalar a esto**: si todo lo anterior falla y querés algo bare-bones
que solo funciona el 80% del tiempo. No es la mejor opción.

### 4. Migrar a GitLab CI / Cloudflare Workers / otro proveedor

**Pros**:
- GitLab usa Google Cloud como runner. ASN distinto. Probablemente sin
  greylist.
- Cloudflare Workers tiene IPs distintas.

**Cons**:
- Cambio de plataforma significativo. Workflows hay que rescribirlos.
- Tiempo de setup: 4-8 h.
- Costo de mantener dos plataformas (GitHub para repo, GitLab para CI).
- No es seguro que su IP no esté también en greylist NASA — habría que
  testear primero.

**Cuándo escalar a esto**: nunca, salvo desastre absoluto. Sobre-ingeniería.

### Priorización

1. **HOY S71 T1**: implementar mitigación token (Sección 3). Costo 30 min.
   Probabilidad de éxito: ~70-80%.
2. **Si falla**: validar empíricamente con 2-3 runs manuales antes de
   escalar. El token podría exponer que el problema es ASN-completo
   y no endpoint-específico.
3. **Si la hipótesis token cae**: self-hosted runner local (opción 1). Costo
   1-2 h setup, $0 monetario.
4. **Solo si Nicolás explícitamente quiere uptime 24/7 sin depender de su
   PC**: VPS Hetzner $5/mes (opción 2).

---

## Apéndice — Comandos de verificación post-fix (sin implementar)

Para validar la hipótesis del token rápidamente:

```bash
# En máquina local de Nicolás (donde NASA sí responde):
python -c "
import earthaccess, os
os.environ['EARTHDATA_TOKEN'] = '<token_pegado_aqui>'
# Borrar USER/PASS para forzar camino TOKEN
os.environ.pop('EARTHDATA_USERNAME', None)
os.environ.pop('EARTHDATA_PASSWORD', None)
auth = earthaccess.login(strategy='environment')
print('authenticated:', auth.authenticated)
print('token preview:', auth.token['access_token'][:20] + '...')
# Hacer una búsqueda real para confirmar que el token es válido
from datetime import datetime
results = earthaccess.search_data(
    short_name='VNP02IMG_NRT',
    version='2.1',
    bounding_box=(-72, -42, -71, -41),
    temporal=('2026-05-19','2026-05-19'),
    count=2,
)
print('granules found:', len(results))
"
```

Si esto imprime `authenticated: True` y devuelve granules, el token funciona
y el fix de Sección 3 es válido.

Para confirmar en GH Actions: workflow_dispatch manual con el secret seteado
+ un step extra `python -c "import earthaccess, os; print(os.getenv('EARTHDATA_TOKEN', '')[:10])"` para verificar el secret está disponible
sin filtrarlo en logs.
