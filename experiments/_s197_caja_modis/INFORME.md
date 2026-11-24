# S197: caja sensible de MODIS en el cráter o en el centro de la grilla (informe)

Pre-registro: `PREREGISTRO.md` (commit `062eb437f`, antes de correr). Todo número sale de un script de esta carpeta con
su salida al lado. Nada de producción cambió.

## Veredicto: **C empata** (regla del pre-registro)

Mover la caja sensible de MODIS a la celda del cráter no cambia ningún valor publicado ni ningún número de píxeles en
las 330 pasadas nocturnas MODIS de D36 (11 Tier A, 2026-03-01 a 2026-11-16). Según la regla sellada: no hay razón para
mover la caja, y se recomienda aceptar la pérdida de Chaitén 2026-11-19 02:30 (issue #1106).

| Métrica (`analisis_caja.py`, salida `analisis_caja_salida.txt` y `.json`) | A (caja en la grilla, producción) | C (caja en el cráter) |
|---|---|---|
| M1 noches con alerta protegida de MIROVA (≥ 1 MW) acertadas | 62 de 62 | 62 de 62 |
| M1 todas las noches con alerta de MIROVA | 93 de 96 | 93 de 96 |
| M2 razón nuestra/MIROVA en la misma pasada (mediana, n = 124) | 1,013 | 1,013 |
| M3 publicaciones en 162 pasadas negativas | 0 | 0 |
| M4 pasadas con valor publicado distinto de A | | 0 de 330 |
| M4 pasadas con número de píxeles distinto de A | | 0 de 330 |

## Por qué el empate es creíble

- **El brazo C actúa** (`control_c_actua.py`): en los volcanes con el cráter fuera de la celda central, el diagnóstico
  de C (umbrales o celda decisiva) difiere del de A en 15 de 16 pasadas de Cordón Caulle, 14 de 15 de Tupungatito, 9
  de 16 de Villarrica, 8 de 15 de Chaitén, 5 de 15 de Planchón-Peteroa y 6 de 105 de Láscar. Mueve la caja; no cambia
  la detección.
- **Control de construcción:** en Copahue, Isluga, Lastarria, Llaima y Nevados de Chillán (cráter en la celda central)
  C es igual a A en 142 de 142 pasadas.
- **Control contra Actions** (`control_a_local.py`): el brazo A local reproduce el A de Actions en todos los campos de
  detección y publicación en 329 de 330 pasadas. 73 difieren sólo en el diagnóstico numérico (los recortes nativos se
  guardaron en float32). Una cambia la detección: Cordón Caulle 2026-03-16 03:10 (Actions 2,535 MW, 1 píxel; local 0,
  «fondo_no_estimado»), un caso de borde de precisión que afecta igual a A y C locales, que se comparan entre sí.
- **Casi alertas de C** (margen ≥ 0,9 sin alerta): 4 pasadas; en dos de Cordón Caulle (2026-10-19 02:00 y 2026-11-13
  01:50) C sube el margen de 0,30 a 0,97 y 0,99. Ninguna cruza.

## Lectura geológica

En MODIS la caja de 5 × 5 km, aunque esté corrida una celda del cráter (Villarrica, Láscar, Chaitén) o varias (Cordón
Caulle, Tupungatito), igual contiene o no contiene el mismo calor que alcanza el umbral: las anomalías que MIROVA
publica en estos volcanes son lo bastante fuertes o lo bastante centradas para que la posición de la caja no decida.
La pasada de Chaitén del 19-nov es la excepción en el borde: una celda tibia justo en la columna que separa las dos
cajas, y aun dentro de la caja del cráter le falta 0,15 % de ETI (`experiments/_s197_1106/INFORME.md`).

## Recomendación

Aceptar la pérdida de Chaitén 2026-11-19 02:30 en `PERDIDAS_ACEPTADAS` de `scripts/auto_audit_weekly.py` (decisión de
Nicolás con su issue, #1106), sin cambiar la caja ni el piso de MODIS.

## Procedencia

- `ab_caja.py`: corre la vía de producción con `tipo_roi="def"` (A) y `"crater"` (C) sobre los recortes nativos de los
  artefactos s190-d36-p1-0, 1 y 2 del run 44016042341 (copia local en `D:\vrp-trabajo\temporales\s197\d36_art\`;
  vencen el 2026-12-17). Salida: `ab_caja_salida.txt`; resultados por pasada en
  `D:\vrp-trabajo\temporales\s197\caja_out\x\p1_resultados_0.json` (no se versiona).
- Ojo: los campos `controles.copia_igual` y `controles.produccion_igual` de `analisis_caja_salida.*` (330 de 330) son
  vacíos aquí: `ab_caja.py` los rellena para reusar el análisis de D36. El control válido es `control_a_local_salida.txt`.
- `analisis_caja.py`: copia de `experiments/_s190_d36/p1_analisis.py` con los brazos A y C (misma referencia MIROVA,
  misma réplica de lo publicado).
