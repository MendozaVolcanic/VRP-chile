# Bitácora de las tandas de la historia de los 34

Plan: `docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md`. Una fila por despacho; los números salen del
informe de `unir_trozos.py` y de la API de Actions (suma de `completed_at - started_at` de los jobs `reproc`).

## Piloto (2026-11-14)

| campo | valor |
|---|---|
| run | 43614240705 (main `ce8b20ca5`, `reproc-historia-via.yml`) |
| volcanes y ventana | Calbuco y Parinacota, 2025-03-01 a 2025-03-31 |
| trozos | 4 de 4 en verde, todos con intento 1 |
| runner | 90 min (14 + 19 + 31 + 26), o sea 1,45 min por volcán y día; Tupungatito dio 1,46 (run 43146587816). La tabla de costo del plan (~520 h para los 34) se mantiene |
| unión | Calbuco 355 records, Parinacota 270; 31 días cada uno, 0 huecos, todas las marcas `true` |
| ensayo del aplicador | 355 y 270 nuevos, 0 tras el corte; sin escribir (modo ensayo) |
| detecciones | Calbuco 1 (0,16 MW a 29 km del centro). Parinacota 14, casi todas a 18 a 32 km de los volcanes; la mayor, 6,03 MW (MODIS Aqua, 03-19 07:40), a 10,7 km de Guallatiri. Mismo patrón de detecciones lejanas que la sombra diaria; el radio de cumbre del tablero (5 km) las deja fuera de la cumbre |
| se aplica | NO: el piloto sólo mide. Su ventana vuelve a correr en la tanda 1 (Parinacota) y la 6 (Calbuco); la carpeta del piloto no se mezcla con la de esas tandas, porque `unir_trozos.py` rehúsa una clave repetida |

Copia local: `D:/vrp-trabajo/temporales/historia_34/piloto/` (fuera del repo).

## Antes de la tanda 1

- Decisiones H1 a H3 de Nicolás (§2 del plan).
- `FileExistsError` en `partial_*`: en el run 43467764489 (S182) tumbó 3 de 34 jobs enteros (todas las descargas del job,
  0 `DOWNLOAD_DONE`), y a Mentolat en la sombra el 2026-11-03. Causa SIN VERIFICAR; S182 propuso una sesión aparte para
  diagnosticarlo. Con 165 trozos por tanda, una tasa así dejaría ~15 trozos para relanzar en cada una.
