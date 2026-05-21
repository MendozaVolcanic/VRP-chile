# EARTHDATA_TOKEN setup — bypass throttling NASA-Azure GH Actions

> **Trigger**: F1.9 Perplexity Deep Research diagnóstico confirmó que NASA Earthdata aplica DoS-mitigation colateral sobre el endpoint `/api/users/find_or_create_token` por el patrón de tráfico CI/CD desde el bloque /16 de Azure GH-hosted runners (admitido en forum.earthdata.nasa.gov t=2764). Síntoma: NRT cron 0% success post-#103 con `ConnectTimeout` consistente. Solución: usar token persistente que NUNCA toca ese endpoint.

## Pasos para Nicolás

### 1. Generar token en Earthdata Login

1. Login en https://urs.earthdata.nasa.gov/ con tu cuenta (`EARTHDATA_USERNAME` actual).
2. Ir a **Profile** → tab **"Generate Token"**.
3. Botón "Generate Token". Si ya hay uno activo, "Revoke" + "Generate" otro fresh.
4. **Copiar el token** (string largo tipo JWT, ~200 caracteres). Vida útil: **60 días**.

### 2. Agregar a GH Secrets del repo

1. Repo VRP-chile → Settings → Secrets and variables → Actions.
2. **New repository secret**.
3. Name: `EARTHDATA_TOKEN`.
4. Value: pegar el token generado en paso 1.
5. **Add secret**.

NO eliminar `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` — quedan como fallback si el token expira.

### 3. Verificar que funciona

Después de mergear este PR + agregar el secret:

```
gh workflow run nrt.yml --ref main
```

(o esperar próximo cron 2h). Verificar success:

```
gh run list --workflow nrt.yml --limit 3 --json conclusion
```

Si los nuevos runs son `success` → fix validado.

### 4. Rotación cada 50 días (recordatorio)

Token vida 60 días. Setear recordatorio calendar a 50 días desde generación para rotar antes de expirar.

Cuando rote: revoke + generate nuevo + update GH Secret value.

## Por qué funciona técnicamente

`earthaccess 0.17.0` (instalado en CI vía requirements.txt) `_get_credentials` lógica:

```python
def _get_credentials(self, username, password, user_token):
    if user_token is not None:
        # Path A — token presente: setea token directamente
        self.token = {"access_token": user_token}
        self.authenticated = True
    elif username is not None and password is not None:
        # Path B — fallback legacy: llama find_or_create_token endpoint
        # (NASA throttle desde IPs Azure GH Actions)
        token_resp = self._find_or_create_token()
        ...
```

Si `EARTHDATA_TOKEN` env var está seteada → Path A → NUNCA llama el endpoint que falla.

Si solo `EARTHDATA_USERNAME`+`EARTHDATA_PASSWORD` → Path B → ConnectTimeout NASA-Azure.

## Aplicabilidad a otros workflows

Después de validar nrt.yml, los workflows reproc-ab-*.yml también pueden adoptar el mismo patrón:

- `reproc-ab-unsuitable-filters.yml` (S72 corriendo)
- `reproc-ab-path-d-cap.yml`
- `reproc-ab-path-d-atm-gate.yml`
- `reproc-ab-path-d-covalidation.yml`
- `reproc-ab-local-kernel-bg.yml`
- etc.

Update propuesto S73: agregar `EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}` a todos.

## Fallback estructural si token también falla

Probabilidad estimada ~20-30% (per F1.9): el throttling NASA-Azure podría afectar también otros endpoints. Si después del fix los runs siguen fallando:

1. **Self-hosted runner en tu PC local** (Chile IP residencial, verificado <1s TCP a urs.earthdata.nasa.gov en F1.9).
2. **VPS pequeño** (DigitalOcean/Hetzner en región distinta a Azure) — $5/mes.
3. **Cron local Windows Task Scheduler** + push periódico a repo desde tu máquina.

Si la opción 1 (token) funciona, no necesitamos las 3 estructurales.

## Referencias

- F1.9 diagnosis subagente — `experiments/129_nrt_cron_nasa_azure_diagnosis/diagnosis.md` (si fue commiteado).
- earthaccess docs: https://earthaccess.readthedocs.io/en/latest/user_guide/authenticate/
- NASA EDL Python user token script: https://urs.earthdata.nasa.gov/documentation/for_users/data_access/python_user_token_script
- Forum Earthdata t=2764 (NASA reconoce collateral damage CI/CD): https://forum.earthdata.nasa.gov/viewtopic.php?t=2764
- GitHub community #177686 (GH Actions IP ranges Azure): https://github.com/orgs/community/discussions/177686
