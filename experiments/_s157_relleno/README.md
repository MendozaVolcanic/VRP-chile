# S157: relleno de las pasadas que el histórico con K no trajo (preparado, NO despachado)

## De qué se trata

El ensayo del reemplazo (PR #866, `experiments/_s154_reproc_k/ensayo_s157/`) encontró 89 pasadas que la serie
operacional tiene y el histórico con K (run 39125546355, perfil `_s154_reproc_k_historico`) no trajo. Si se
reemplaza así, esas pasadas quedan con el detector viejo (C0). Antes de relanzar nada hay que saber si NASA
tiene hoy el producto estándar de cada una, porque un trozo puede salir verde y no traer nada (A108).

## Resultado

`armar_relleno.py` cruza cada pasada faltante con su record operacional (`product_version`, `granule`) y busca
el L1B y la geolocalización estándar con los mismos `short_name` y versiones de `pipeline/fetch.py::PRODUCTS`.

- **CMR no respondió**: la búsqueda de gránulos y `/search/health` dieron HTTP 500 durante toda la sesión
  (la búsqueda de colecciones sí respondía). Es la misma caída que dejó verde y vacía la segunda pasada de
  Chillán. Todas las decisiones de abajo salen del **listado público del archivo LAADS DAAC**, que es de
  donde se baja el estándar. Falta confirmar con CMR (ver «Antes de despachar»).
- **Las 31 pasadas `standard`**: L1B y geolocalización están en LAADS. Son cortes de NASA del run (A64,
  A108), y repetir esos días debería traerlas.
- **Las 58 pasadas `nrt` de Suomi NPP (5 y 6 de agosto de 2026, 375 y 750 m)**: el estándar **no existe**.
  En la colección 5200 de LAADS faltan enteros los días 216 y 217 de 2026 (4 y 5 de agosto) en
  VNP02IMG, y el día 218 (6 de agosto) empieza recién a las 16:30 UTC en VNP02IMG, VNP03IMG, VNP02MOD y
  VNP03MOD (75 archivos de 16:30 a 23:54, contra 240 del día 219). Las pasadas nocturnas, de 04 a 07 UTC,
  caen dentro del hueco. Relanzar el trozo no las trae: para el reemplazo, o quedan en C0 con su marca, o se
  procesan desde el NRT, y esa decisión no es de este encargo.

Detalle por pasada en `PLAN_RELLENO.md` (tabla) y `cmr_por_pasada.json`; resumen y despachos en
`plan_relleno.json`. Todo lo genera el script: ningún número está transcrito a mano.

## Plan de despachos

Diez ventanas de un día (no hay días contiguos que agrupar), una por despacho. Los comandos están en
`PLAN_RELLENO.md` y `plan_relleno.json`.

### Antes de despachar

1. **El PR #873 (merge que conserva la base) tiene que estar mergeado.** Con el merge anterior, relanzar un
   día de un volcán escribe su JSON sólo con ese día y borra en main el resto del histórico.
2. **Volver a correr `python experiments/_s157_relleno/armar_relleno.py` con CMR arriba** y comprobar que la
   decisión pasa a «existe (CMR)» para las 31. `fetch.py` busca por CMR (earthaccess): un archivo que está
   en LAADS pero que CMR no indexa, el pipeline no lo encontraría.
3. **En serie, uno a la vez**, esperando que termine cada run, incluido su job `merge`. Todos usan el perfil
   `_s154_reproc_k_historico`, o sea el grupo de concurrencia `reproc-chunked-_s154_reproc_k_historico`, el
   mismo de los relanzamientos de NevadosDeChillan. GitHub guarda un solo run pendiente por grupo, y un
   tercero despachado mientras otro espera lo expulsa. Empezar cuando terminen los de Chillán.
4. Después de cada run, contar las pasadas del volcán en esa fecha contra la serie operacional (A108).
