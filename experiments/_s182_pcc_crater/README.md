# S182: la caja del cráter en Cordón Caulle (VIIRS 750)

Decisión de Nicolás del 2026-11-13: «Probar la del cráter» y después «Yaml y reproceso PCC».

## El fenómeno

El calor que MIROVA publica en Puyehue-Cordón Caulle está en la zona de la fisura, de 7 a 8,5 km del punto de
referencia del volcán (centro de la grilla de 67 × 67 celdas de 750 m), que cae en el Puyehue. La caja de producción
`sens` (brazo B4 de V750-B) es el anillo de 21 × 21 celdas centrado en ese punto, entero con el umbral sensible. El
cráter, celda (23, 30), queda en su borde norte (filas 23 a 43): la caja deja fuera la fila 22, al norte de la fisura,
y pone el umbral sensible en todo el flanco sur del Puyehue. El 2026-10-21 05:48 UTC (NOAA-21) eso publicó 10,1 MW con
11 píxeles del flanco sur; MIROVA publicó 0,36 MW a 6,45 km (fila de la tabla).

## Lo medido (todo con el port de producción, sha256 `62d6538b`, igual a `origin/main`)

| archivo | qué | resultado |
|---|---|---|
| `11_cajas_pcc.py` | crater, sens, sens con el sur conservador y sens con el sur en 0 sobre las 535 grillas PCC de V750-B (2026-04-01 a 2026-11-02); referencia: filas ALERTA de la tabla y del OCR (`objetivos_run_v750b.json`) | las cuatro ven 45 de 53 alertas de MIROVA, 0 protegidas perdidas; sólo cambian 10-21, 04-07 y 10-09 (sur) y la fila 22 en 6 pasadas (crater) |
| `12_diag_crater_mas_pix.py` | por qué crater alerta más píxeles en algunas pasadas | la fila 22 (al norte de la fisura) entra con umbral sensible; los umbrales de cada pase son prácticamente iguales |
| `correr_b4c.py` | el analizador SELLADO de V750-B, sin modificar el archivo, con B4 cambiado en memoria a B4c (crater sólo en Cordón Caulle) y el control negativo restringido a Tupungatito | compuerta ABIERTA; TO canal decide: 101/101 protegidas, P1 0, E 29 contra 31 del B4 sellado; contra B1 EMPATE (no significativo) |

Cambian 2 pasadas de Cordón Caulle entre B4 y B4c: 2026-10-21 05:48 NOAA-21 (baja de 0,36 MW que pasa a publicarse
con 0,49 MW en vez del cúmulo de 10,3 MW) y 2026-10-09 06:54 SNPP (negativo limpio de 0,42 MW que deja de publicarse).

Verificadores Sonnet con contexto limpio, scripts propios: `D:\vrp-trabajo\temporales\s182_verif_pcc\`,
`D:\vrp-trabajo\temporales\s182_verif_cajas\` (0 diferencias en 2.140 pasada × caja) y
`D:\vrp-trabajo\temporales\s182_verif_b4c\`; los tres CORRECTO CON OBSERVACIONES (bitácora de `loop/activo`,
`tasks/LOOP_OBJETIVOS.md` §6, entradas del 2026-11-13).

## Límites

- B4c NO es un brazo sellado: es una lectura descriptiva post hoc. La mejora es chica y no significativa.
- La ROI que usa MIROVA de verdad sigue SIN DATO (0,345 no es 0,36; crater se aparta de MIROVA en otras pasadas,
  más cerca en 4 de 6 y más lejos en 2).
- «Sur en 0» no excluye nada: el port, como el `.m`, evalúa BOX 0 con el umbral conservador.
- Las rutas de los scripts apuntan a los artefactos de V750-B en `D:\vrp-trabajo\temporales\v750b_r4_20261103\`
  (no versionados).

## Lo que sigue

1. PR con `pipeline/grillas_mirova.yaml` en B4c (`scripts/roi_v750b_a_grillas.py --brazo B4c --escribir`), con
   `tests/test_roi_v750b_variantes_s169.py` midiendo el efecto en la caja de Cordón Caulle. Merge: Nicolás.
2. Reproceso de la historia VIIRS 750 de Cordón Caulle con la caja nueva (`reproc-historia-via.yml`) y reemplazo en
   `data/` con su sí aparte (A45).
