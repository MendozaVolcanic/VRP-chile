# S97 — inventario de limpieza de dirs de staging (A38)

Tras promover el refresh operacional (#306), los directorios de staging del reproc
ya no se necesitan: su contenido fue ensamblado y promovido a `data/mirova_equivalent`.
Esta limpieza los saca del repo. Protocolo A38: inventario (este doc) + tag defensivo
`pre-s97-staging-cleanup` + confirmación Nicolás (dada) antes del `git rm`.

## Inventario

| Dir | Tamaño | Tracked | Origen | Recomendación |
|---|---|---|---|---|
| `data/_s94_reproc_modis` | 27M | 11 | MODIS staging S94/S95 (#297), reusado en el refresh S97 | **Eliminar** (ya promovido) |
| `data/_s94_reproc_viirs` | 13M | 11 | VIIRS mayo staging S94/S95 (validación F2) | **Eliminar** (superado por _s97_refresh_viirs*) |
| `data/_s97_refresh_viirs` | 14M | 11 | VIIRS feb chunk 1 del refresh S97 | **Eliminar** (ya promovido) |
| `data/_s97_refresh_viirs_mar` | 13M | 11 | VIIRS mar chunk del refresh S97 | **Eliminar** (ya promovido) |
| `data/_s97_refresh_viirs_apr` | 13M | 11 | VIIRS abr chunk del refresh S97 | **Eliminar** (ya promovido) |
| `data/_s97_refresh_viirs_may` | 14M | 11 | VIIRS may chunk del refresh S97 | **Eliminar** (ya promovido) |
| `data/_s94_reproc` | 33M | 0 (local) | combinado local S94, sin trackear | **Eliminar local** (no está en git) |
| `data/_s97_refresh` | 78M | 0 (local) | snapshot ensamblado S97, sin trackear | **Eliminar local** (no está en git) |

Total trackeado a remover: 6 dirs, 66 archivos, ~94 MB.

## Perfiles asociados (se CONSERVAN)
`pipeline/profiles/_s94_reproc*.yaml` y `_s97_refresh_viirs*.yaml` se conservan (son
KB, documentan la metodología del reproc y permiten re-generar el staging si hiciera
falta). No estorban.

## Recovery
- Pre-promoción de la data operacional: tag `pre-s97-refresh-promote`.
- Pre-limpieza de staging: tag `pre-s97-staging-cleanup` (este cleanup).
- `git checkout pre-s97-staging-cleanup -- data/<dir>/` restaura cualquier dir.

## No interferencia
Único workflow activo al momento del cleanup: NRT cron (toca `data/mirova_equivalent`
y `data/experimental`, NO los dirs de staging). Sin race.
