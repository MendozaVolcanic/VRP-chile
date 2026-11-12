# Unión de la vía «código MIROVA» para el reemplazo de la historia (S180)

Un archivo `<Volcan>.json.gz` por cada Tier A. Contiene los records del reproceso con la vía (perfil
`_s172_retro_paquete`) del 2025-02-15 al 2026-11-11. Los generó
`experiments/_s180_reemplazo_via/unir_trozos.py` y los consume `aplicar_via.py`, que se despacha con
`.github/workflows/aplicar-reemplazo.yml` mediante `aplicar_historia_via.sh`.

Están fuera de `data/` porque GitHub Pages copia `data/` entera y tiene un techo de 1 GB. Van comprimidos con gzip
y mtime 0, así que son reproducibles.

## Procedencia (artifacts de GitHub Actions)

| Despacho | Run | Qué cubre |
|---|---|---|
| D2 | 42507820590 | retrospectiva del paquete (S177) |
| D4 | 42601379627 | retrospectiva del paquete (S177) |
| P4 | 42749607584 | tramo hasta el 2026-11-09 |
| Tupungatito | 43146587816 | Tupungatito 2025-02-15 a 2026-02-22 (`reproc-historia-via.yml`) |
| G1 | 43146594080 | VIIRS y MODIS 2026-11-10 a 2026-11-11, 11 volcanes |

Todos usaron el perfil `_s172_retro_paquete`.

## Estado de la unión

`informe_union.json`: los 11 volcanes cubren 635 días cada uno (2025-02-15 a 2026-11-11), sin huecos de
calendario, y todos sus records traen `via_codigo_mirova: true`, sin caídas a K.

`../ensayo/informe_ensayo.json` es el ensayo en seco sobre los datos de main en `8250b68f1`, con tope de sin par
0,08. No se rehusó nada.

| Familia | Pasadas sin par por volcán | K restante antes del corte |
|---|---|---|
| MODIS | 1,84 a 3,32 % | 0 |
| VIIRS 375 | 1,84 a 6,22 % | 0 |
| VIIRS 750 | 0 % | 0 |

En VIIRS 750 la vía agrega 522 pasadas que K no tenía. Son bordes de franja: su cenital mediano es 69,5°,
contra 48,6° en las pasadas pareadas. Solo una de ellas trae VRP mayor que 0 (Nevados de Chillán, 2026-10-13
06:42, NOAA-21 750, 10,94 MW, cumbre).
