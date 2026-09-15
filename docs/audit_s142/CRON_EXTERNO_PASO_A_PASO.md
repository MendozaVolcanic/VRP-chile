# Cron externo del NRT: paso a paso (S142)

Decisión de Nicolás en S142: **opción A** de `docs/audit_s141/NRT_CRON_EXTERNO.md` (servicio externo que
dispara `workflow_dispatch`), dejando el cron de GitHub como respaldo. Este documento es lo que falta para
activarlo. La parte con credenciales la haces tú: yo no creo cuentas ni tokens, y el valor del token no
se escribe en ningún archivo del workspace.

## Por qué (el fenómeno)

El cron declarado en `nrt.yml` no es un reloj propio: GitHub crea el evento programado con una mediana de
56 min de atraso y funde franjas, así que hoy hay ~4,75 corridas diarias de las 12 declaradas
(`experiments/_s141_cron/atraso_despacho.json`). No se pierden datos, porque cada corrida reprocesa siete
días, pero una anomalía de madrugada puede llegar al dashboard horas tarde. Un `workflow_dispatch` nace en
el momento de la llamada y arranca en ~3 s.

## 1. Token (lo haces tú, en GitHub)

1. GitHub, Settings, Developer settings, Personal access tokens, **Fine-grained tokens**, Generate new token.
2. Nombre: `vrp-chile-cron-externo`. Expiración: 90 días (anótala).
3. Resource owner: `MendozaVolcanic`. Repository access: **Only select repositories**, sólo `VRP-chile`.
4. Permisos del repositorio: **Actions: Read and write**. Nada más (Metadata: Read queda puesto solo).
5. Copia el token. No lo pegues en ningún chat ni archivo del workspace.

## 2. Trabajo en cron-job.org (lo haces tú)

1. Crea la cuenta en https://cron-job.org (gratuita) y un cron job nuevo.
2. **URL**: `https://api.github.com/repos/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml/dispatches`
3. **Horario**: personalizado, expresión `10 1-23/2 * * *`, zona **UTC** (01:10, 03:10, ..., 23:10). Por qué
   impares: las pasadas nocturnas útiles de VIIRS caen a las 04, 05 y 06 UTC y LANCE las publica unas 3 h
   después; las corridas de 07:10 y 09:10 las toman apenas existen, y las horas pares siguen cubiertas por el
   cron de GitHub.
4. Pestaña Advanced:
   - Request method: **POST**
   - Headers:
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer <el token del paso 1>`
     - `X-GitHub-Api-Version: 2022-11-28`
   - Request body: `{"ref":"main"}`
5. Guarda y usa "Test run". GitHub responde **204 No Content** si funcionó.

## 3. Verificación (me la puedes pedir a mí)

- Justo después del test: `gh run list -R MendozaVolcanic/VRP-chile --workflow nrt.yml --limit 3` debe
  mostrar una corrida con evento `workflow_dispatch` creada en ese minuto.
- A la semana: `python scripts/medir_atraso_despacho_nrt.py --n 60` y comprobar ~12 corridas diarias en total
  y el healthcheck con el dato del Tier A a menos de 3 h.

## 4. Qué pasa si falla o vence

El disparador deja de llamar y la latencia vuelve a la del cron de GitHub, que sigue declarado. **No se
pierden datos.** Dos corridas cercanas no se pisan: el grupo `push-main` las serializa y el store no duplica
records. El token está anotado en `REGISTRO_CREDENCIALES.md` §2 (sin el valor), con su vencimiento.

## 5. Lo que NO cambia

`nrt.yml` no se toca: ya acepta `workflow_dispatch` y conserva su `schedule`. Por eso no aplica A45 (no hay
cambio en el pipeline, el perfil ni el workflow).
