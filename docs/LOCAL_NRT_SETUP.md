# Setup local NRT — testing + cron Windows

> **Por qué local**: GH Actions NRT cron tiene throttling NASA-Azure (1/5 success post-EARTHDATA_TOKEN). Tu PC Chile tiene TCP <1s a `urs.earthdata.nasa.gov` (verificado F1.9). Correr NRT local da 100% confiabilidad.

## 1. Setup pruebas locales (.env)

### Crear el archivo `.env`

En el root del repo (mismo nivel que `pipeline/`, `docs/`, etc):

```bash
cp .env.example .env
```

Editar `.env`:
```
EARTHDATA_TOKEN=<token generado en urs.earthdata.nasa.gov/profile>
```

(`.env` ya está en `.gitignore` — no se commitea.)

### Verificar setup

```powershell
python -c "from pipeline.fetch import _load_dotenv_if_present; _load_dotenv_if_present(); import os; print('TOKEN:', 'YES' if os.environ.get('EARTHDATA_TOKEN') else 'NO')"
```

Debe imprimir `TOKEN: YES`.

### Correr una prueba

```powershell
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Villarrica --date 2026-05-21
```

- Solo VIIRS se procesa local (MODIS requiere `pyhdf` que está roto en Windows).
- Si `EARTHDATA_TOKEN` está OK, earthaccess autentica directo sin tocar `/api/users/find_or_create_token` (el endpoint que NASA throttle desde Azure runners).

## 2. Cron NRT Windows Task Scheduler (operacional confiable)

> Pendiente implementación. Plan:

### 2.1 Script bat wrapper

`scripts/nrt_local.bat` (a crear):
```bat
@echo off
REM VRP Chile NRT local cron — corre VIIRS pipeline + push a repo
cd /d "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70"
git pull --rebase origin main
python scripts/run_pipeline.py --profile mirova_equivalent
git add data/mirova_equivalent/
git diff --staged --quiet || git commit -m "NRT local update %date% %time%"
git push origin main
```

### 2.2 Task Scheduler XML

Crear tarea `VRP_Chile_NRT` que corra `nrt_local.bat` cada 2h. PC debe estar ON.

### 2.3 Logging

`scripts/nrt_local.bat` redirect stderr/stdout a `nrt_local.log` para diagnóstico.

### 2.4 Race condition con GH Actions NRT cron

El cron de GH Actions sigue corriendo. Si ambos pushean simultáneamente → conflict. Mitigación:
- Deshabilitar GH Actions NRT cron una vez local funciona (`# - cron:` en `nrt.yml`).
- O agregar `git pull --rebase` antes del push (ya en el script bat).

## 3. Limitaciones conocidas

| Item | Status |
|---|---|
| MODIS local Windows | ❌ pyhdf broken (constraint conocido CLAUDE.md) |
| VIIRS local Windows | ✅ funciona (h5py + earthaccess + netCDF4) |
| Sentinel-2 SWIR | N/A — no en scope VRP Chile actualmente |
| NRT Linux WSL | ⚠️ pyhdf debería funcionar en WSL Ubuntu — alternativa si MODIS local crítico |

## 4. Pipeline locally — comandos comunes

```powershell
# NRT 1 vol 1 día (yesterday default)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar

# Vol 1 día específico
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Villarrica --date 2026-05-21

# Vol rango días (reproc)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar --start 2026-05-01 --end 2026-05-21 --overwrite

# Profile A/B aislado (para experimentación)
python scripts/run_pipeline.py --profile mirova_equivalent_no_cap_v1 --volcano Lascar --date 2026-05-21

# Skip NOAA-20 cuando NASA throttle (fallback solo Suomi NPP + NOAA-21)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar --skip-noaa20

# Procesar daytime también (debug, MIROVA standard es solo noche)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Lascar --no-night-filter
```

## 5. Diagnóstico errores comunes

### "LoginAttemptFailure: invalid_credentials"

netrc tiene credentials viejas O `EARTHDATA_TOKEN` inválido.

Fix:
```powershell
# Regenerar token en urs.earthdata.nasa.gov/profile
# Actualizar .env con nuevo token
```

### "NASA_AUTH_UNREACHABLE: ConnectTimeout"

Probable solo en GH Actions (Azure throttle). Si pasa local → verificar firewall/VPN.

### "pyhdf not found" warning

Esperado en Windows. Pipeline auto-skips MODIS. No es error fatal.

### Empty granule list returned

NASA Earthdata aún no publicó el granule (latencia ~3h NRT). Esperar y reintentar.

## 6. Plan deployment local NRT (S73)

1. Task Scheduler Windows + bat script (~45 min setup).
2. Deshabilitar GH Actions NRT cron una vez local validado (~2 días observación).
3. Self-hosted runner GH Actions también opcional (más complejo pero más estándar).
