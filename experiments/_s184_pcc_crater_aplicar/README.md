# S184: reemplazo de la serie VIIRS 750 de Cordón Caulle con la caja del cráter (PR #999)

## Por qué

El PR #999 cambia la región sensible de la vía «código MIROVA» en VIIRS 750 de Puyehue-Cordón Caulle: deja de ser el
cuadrado `sens` (21 × 21 celdas centrado en el punto de referencia, que cae en el Puyehue) y pasa a ser `crater`
(7 × 7 celdas en el cráter). Desde el merge, el NRT escribe con `crater`. Si la historia sigue con `sens`, la serie
muestra un cambio que no es del volcán. El caso que lo motivó es el 2026-10-21 05:48 (NOAA-21): con `sens` se
publicaron 10,1 MW de 11 píxeles del flanco del Puyehue, cuando MIROVA publicó 0,36 MW.

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `historia_crater/PuyehueCordonCaulle.json.gz` | Unión de los 34 trozos del reproceso (run 43467764489, desde el commit `4b306b31e` de la rama de #999, perfil `_s172_retro_paquete`), hecha con `experiments/_s180_reemplazo_via/unir_trozos.py` |
| `historia_crater/informe_union.json` | 34 trozos, 2025-02-15 a 2026-11-13, 637 días, 0 huecos, 7.307 records (VIIRS 750: 2.994). Los trozos 23, 29, 33 y 34 son del intento 2 (el intento 1 falló por `FileExistsError` de descarga en runners de AWS us-west-2) |
| `aplicar_pcc_v750.py`, `aplicar_pcc_v750.sh` | Reemplazo sólo de VIIRS 750 de PCC; reglas en el docstring; lo corre `.github/workflows/aplicar-reemplazo.yml` con el sí de Nicolás |
| `ensayo/informe.json` | Ensayo (sin escribir) sobre la serie publicada de `origin/main` `f7e7aa5c6` |
| `efecto_reemplazo.py`, `efecto_reemplazo_salida.txt` | Qué cambia en la serie |

Pruebas: `tests/test_aplicar_pcc_crater_s184.py`.

## Resultado del ensayo (de `ensayo/informe.json` y `efecto_reemplazo_salida.txt`)

- 2.994 pasadas VIIRS 750 publicadas en la ventana, 2.994 con par en el reproceso: 0 sin par, 0 agregadas. Los otros
  4.319 records del archivo (MODIS y VIIRS 375) no cambian.
- 64 pasadas cambian de potencia: 50 suben y 14 bajan; 17 pasan de 0 a tener potencia y 10 de tener potencia a 0.
  Pasadas de 1 MW o más: 129 antes, 135 después.
- 2026-10-21 05:48 NOAA-21: 10,115 MW a 9,40 km, pasa a 0,345 MW a 2,85 km (`final_hotspot_dist_km`).
- 3 pasadas posteriores a la ventana (2026-11-14) quedan con `sens` hasta que se decida si se cubren con un reproceso
  corto entre el 2026-11-14 y el merge.

## Lo que no está comprobado

- Por qué suben 50 pasadas con una región sensible más chica. En la del 2025-08-29 05:36 los umbrales son iguales y con
  `crater` pasa un píxel más en la primera pasada (3 contra 2). Encaja con que el cuadro del cráter cubra celdas de la
  fisura que quedaban fuera del cuadrado `sens`. SOSPECHA: no se comprobó celda por celda.

## Verificación

Verificador limpio (Sonnet, esfuerzo alto) del script: CORRECTO CON OBSERVACIONES; las observaciones se corrigieron en
el commit `e44502a9e` (bitácora S184 en `tasks/LOOP_OBJETIVOS.md`, rama `loop/activo`).
