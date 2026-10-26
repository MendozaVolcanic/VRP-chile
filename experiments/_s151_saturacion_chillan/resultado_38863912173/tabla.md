# Saturacion en Nevados de Chillan (tarea 1.18), tabla generada

Referencia MIROVA: snapshot (remoto fallo: CalledProcessError).

Avisos de calidad de la referencia (A119):

- 2026-10-09 (ocr, Suomi NPP): antes, en las filas solo OCR de Suomi NPP la distancia y la clase pueden ser de OTRA pasada (la imagen de una pasada posterior); el VRP si es de la suya. Arreglo en Mirova-v1#20, 2026-10-09 14:01 UTC; evidencia en el commit 9a305c9db (#774)
- 2026-10-10 (ocr, VIIRS y MODIS): antes no hay filas ALERTA_SIN_GEOMETRIA_OCR: una pasada que la tabla se salta y cuya imagen de distancia ya era de una pasada posterior se perdio (V31, desde el 2026-10-09) o trajo la distancia de otra (antes, hito de Suomi NPP). Desde aqui V31.1 guarda su VRP sin distancia y el backfill recupera las del log de rechazos (13 al 2026-10-15). Son un estrato aparte: no son alerta de la lectura A

## Resumen por familia y noche/dia

```
{
 "MODIS_dia": {
  "pasadas": 43.0,
  "estado_ok": 43.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 0.0,
  "pasadas_publica_con": 0.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 0.0,
  "suma_tablero_vrp_con_mw": 0.0,
  "pasadas_con_mirova_alerta": 1.0,
  "suma_mirova_vrp_alertas_mw": 6.0
 },
 "MODIS_noche": {
  "pasadas": 36.0,
  "estado_ok": 36.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 5.0,
  "pasadas_publica_con": 5.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 17.576,
  "suma_tablero_vrp_con_mw": 17.576,
  "pasadas_con_mirova_alerta": 6.0,
  "suma_mirova_vrp_alertas_mw": 21.11
 },
 "V375_dia": {
  "pasadas": 75.0,
  "estado_ok": 75.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 0.0,
  "pasadas_publica_con": 0.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 0.0,
  "suma_tablero_vrp_con_mw": 0.0,
  "pasadas_con_mirova_alerta": 6.0,
  "suma_mirova_vrp_alertas_mw": 38.35
 },
 "V375_noche": {
  "pasadas": 77.0,
  "estado_ok": 77.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 72.0,
  "pasadas_publica_con": 72.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 118.295,
  "suma_tablero_vrp_con_mw": 118.295,
  "pasadas_con_mirova_alerta": 37.0,
  "suma_mirova_vrp_alertas_mw": 169.3
 },
 "V750_dia": {
  "pasadas": 75.0,
  "estado_ok": 75.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 0.0,
  "pasadas_publica_con": 0.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 0.0,
  "suma_tablero_vrp_con_mw": 0.0,
  "pasadas_con_mirova_alerta": 3.0,
  "suma_mirova_vrp_alertas_mw": 19.04
 },
 "V750_noche": {
  "pasadas": 79.0,
  "estado_ok": 79.0,
  "pasadas_con_mir_borrado_interior": 0.0,
  "pixeles_mir_borrados_interior_bit": 0.0,
  "pixeles_mir_borrados_interior_techo": 0.0,
  "pixeles_mir_borrados_escena": 0.0,
  "pixeles_tir_bit_interior": 0.0,
  "pasadas_publica_sin": 45.0,
  "pasadas_publica_con": 45.0,
  "pasadas_cambia_tablero": 0.0,
  "suma_tablero_vrp_sin_mw": 117.743,
  "suma_tablero_vrp_con_mw": 117.743,
  "pasadas_con_mirova_alerta": 25.0,
  "suma_mirova_vrp_alertas_mw": 179.99
 }
}
```

## Pasadas con algun pixel MIR borrado en el radio interior, o con alerta de MIROVA

| UTC | familia | noche | MIR bit | MIR techo | TIR bit | tablero sin | tablero con | pc sin | pc con | cota decl | MIROVA |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-28 04:42 | V375 | si | 0 | 0 | 0 | 0.4933 | 0.4933 | 0.493 | 0.493 | 0.0 | ALERTA_TERMICA 2.58 MW; ALERTA_TERMICA_OCR 2.58 MW |
| 2026-09-28 04:42 | V750 | si | 0 | 0 | 0 | 0.549 | 0.549 | 0.549 | 0.549 | 0.0 | ALERTA_TERMICA 0.23 MW |
| 2026-09-28 05:18 | V375 | si | 0 | 0 | 0 | 0.1159 | 0.1159 | 0.045 | 0.045 | 0.0 | ALERTA_TERMICA_OCR 0.05 MW |
| 2026-09-28 06:18 | V375 | si | 0 | 0 | 0 | 0.2627 | 0.2627 | 0.263 | 0.263 | 0.0 | ALERTA_TERMICA 0.6 MW; ALERTA_TERMICA_OCR 0.6 MW |
| 2026-09-29 05:00 | V375 | si | 0 | 0 | 0 | 0.2064 | 0.2064 | 0.206 | 0.206 | 0.0 | ALERTA_TERMICA_OCR 1.41 MW |
| 2026-09-29 05:18 | V375 | si | 0 | 0 | 0 | 3.1673 | 3.1673 | 3.167 | 3.167 | 0.0 | ALERTA_TERMICA 5.73 MW |
| 2026-09-29 05:18 | V750 | si | 0 | 0 | 0 | 2.11 | 2.11 | 2.11 | 2.11 | 0.0 | ALERTA_TERMICA 5.48 MW |
| 2026-09-29 06:00 | V375 | si | 0 | 0 | 0 | 2.3134 | 2.3134 | 2.313 | 2.313 | 0.0 | ALERTA_TERMICA 3.92 MW |
| 2026-09-29 06:00 | V750 | si | 0 | 0 | 0 | 0.717 | 0.717 | 0.717 | 0.717 | 0.0 | ALERTA_TERMICA 2.52 MW |
| 2026-09-29 06:36 | V375 | si | 0 | 0 | 0 | 2.683 | 2.683 | 1.297 | 1.297 | 0.0 | ALERTA_TERMICA 2.11 MW; ALERTA_TERMICA_OCR 2.11 MW |
| 2026-09-29 06:36 | V750 | si | 0 | 0 | 0 | 0.329 | 0.329 | 0.329 | 0.329 | 0.0 | ALERTA_TERMICA 2.03 MW; ALERTA_TERMICA_OCR 2.0 MW |
| 2026-09-29 07:20 | MODIS | si | 0 | 0 | 0 | 0 | 0 | 0.328 | 0.328 | 0.0 | ALERTA_TERMICA 0.13 MW |
| 2026-09-29 17:36 | V750 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | FALSO_POSITIVO 0.95 MW |
| 2026-10-01 01:45 | MODIS | si | 0 | 0 | 0 | 4.167 | 4.167 | 4.167 | 4.167 | 0.0 | ALERTA_TERMICA 6.17 MW |
| 2026-10-01 04:42 | V375 | si | 0 | 0 | 0 | 0.2348 | 0.2348 | 0.11 | 0.11 | 0.0 | ALERTA_TERMICA 0.88 MW |
| 2026-10-01 04:42 | V750 | si | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | ALERTA_TERMICA 0.09 MW |
| 2026-10-01 05:24 | V375 | si | 0 | 0 | 0 | 3.2538 | 3.2538 | 2.578 | 2.578 | 0.0 | ALERTA_TERMICA_OCR 6.28 MW |
| 2026-10-01 05:24 | V750 | si | 0 | 0 | 0 | 2.655 | 2.655 | 2.655 | 2.655 | 0.0 | ALERTA_TERMICA_OCR 9.0 MW |
| 2026-10-01 06:00 | V375 | si | 0 | 0 | 0 | 8.3662 | 8.3662 | 8.366 | 8.366 | 0.0 | ALERTA_TERMICA_OCR 5.07 MW |
| 2026-10-01 06:00 | V750 | si | 0 | 0 | 0 | 11.084 | 11.084 | 11.084 | 11.084 | 0.0 | ALERTA_TERMICA_OCR 10.0 MW |
| 2026-10-01 06:18 | V375 | si | 0 | 0 | 0 | 4.2099 | 4.2099 | 4.21 | 4.21 | 0.0 | ALERTA_TERMICA 7.28 MW |
| 2026-10-01 06:18 | V750 | si | 0 | 0 | 0 | 2.491 | 2.491 | 2.491 | 2.491 | 0.0 | ALERTA_TERMICA 7.06 MW |
| 2026-10-01 08:35 | MODIS | si | 0 | 0 | 0 | 0 | 0 | 2.293 | 2.293 | 0.0 | ALERTA_TERMICA 5.18 MW |
| 2026-10-01 18:42 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 2.53 MW |
| 2026-10-01 18:42 | V750 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 3.71 MW |
| 2026-10-03 06:24 | V375 | si | 0 | 0 | 0 | 0.3754 | 0.3754 | 0.375 | 0.375 | 0.0 | ALERTA_TERMICA 0.54 MW |
| 2026-10-04 05:06 | V375 | si | 0 | 0 | 0 | 0.2447 | 0.2447 | 0.188 | 0.188 | 0.0 | ALERTA_TERMICA_OCR 0.58 MW |
| 2026-10-04 06:06 | V375 | si | 0 | 0 | 0 | 1.8992 | 1.8992 | 1.899 | 1.899 | 0.0 | ALERTA_TERMICA 2.54 MW |
| 2026-10-04 06:06 | V750 | si | 0 | 0 | 0 | 1.812 | 1.812 | 1.812 | 1.812 | 0.0 | ALERTA_TERMICA 2.3 MW; ALERTA_TERMICA_OCR 2.0 MW |
| 2026-10-04 06:42 | V375 | si | 0 | 0 | 0 | 0.4925 | 0.4925 | 0.289 | 0.289 | 0.0 | ALERTA_TERMICA 0.86 MW |
| 2026-10-05 04:48 | V375 | si | 0 | 0 | 0 | 0.0448 | 0.0448 | 0.045 | 0.045 | 0.0 | ALERTA_TERMICA_OCR 0.04 MW |
| 2026-10-05 05:06 | V375 | si | 0 | 0 | 0 | 2.9223 | 2.9223 | 2.761 | 2.761 | 0.0 | ALERTA_TERMICA 5.77 MW |
| 2026-10-05 05:06 | V750 | si | 0 | 0 | 0 | 1.435 | 1.435 | 1.435 | 1.435 | 0.0 | ALERTA_TERMICA 3.43 MW; ALERTA_TERMICA_OCR 3.0 MW |
| 2026-10-05 05:48 | V375 | si | 0 | 0 | 0 | 3.2772 | 3.2772 | 3.277 | 3.277 | 0.0 | ALERTA_TERMICA 4.35 MW |
| 2026-10-05 05:48 | V750 | si | 0 | 0 | 0 | 7.152 | 7.152 | 7.152 | 7.152 | 0.0 | ALERTA_TERMICA 7.86 MW; ALERTA_TERMICA_OCR 7.0 MW |
| 2026-10-05 06:24 | V375 | si | 0 | 0 | 0 | 4.4681 | 4.4681 | 3.682 | 3.682 | 0.0 | ALERTA_TERMICA_OCR 8.24 MW |
| 2026-10-05 06:24 | V750 | si | 0 | 0 | 0 | 3.983 | 3.983 | 3.983 | 3.983 | 0.0 | ALERTA_TERMICA_OCR 7.0 MW |
| 2026-10-05 06:48 | V375 | si | 0 | 0 | 0 | 1.5127 | 1.5127 | 1.513 | 1.513 | 0.0 | ALERTA_TERMICA 4.71 MW; ALERTA_TERMICA_OCR 4.71 MW |
| 2026-10-05 06:48 | V750 | si | 0 | 0 | 0 | 0.259 | 0.259 | 0.259 | 0.259 | 0.0 | ALERTA_TERMICA 2.66 MW; ALERTA_TERMICA_OCR 2.0 MW |
| 2026-10-05 07:50 | MODIS | si | 0 | 0 | 0 | 2.031 | 2.031 | 2.031 | 2.031 | 0.0 | ALERTA_TERMICA 3.5 MW |
| 2026-10-06 01:45 | MODIS | si | 0 | 0 | 0 | 0 | 0 | 5.0 | 5.0 | 0.0 | FALSO_POSITIVO 0.58 MW |
| 2026-10-08 05:48 | V375 | si | 0 | 0 | 0 | 0.6417 | 0.6417 | 0.642 | 0.642 | 0.0 | ALERTA_TERMICA 0.82 MW; ALERTA_TERMICA_OCR 0.82 MW |
| 2026-10-08 19:30 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 6.46 MW |
| 2026-10-09 05:12 | V375 | si | 0 | 0 | 0 | 0.2273 | 0.2273 | 0.156 | 0.156 | 0.0 | ALERTA_TERMICA_OCR 0.21 MW |
| 2026-10-09 05:30 | V375 | si | 0 | 0 | 0 | 0.319 | 0.319 | 0.286 | 0.286 | 0.0 | ALERTA_TERMICA 0.5 MW |
| 2026-10-09 05:30 | V750 | si | 0 | 0 | 0 | 0.396 | 0.396 | 0.396 | 0.396 | 0.0 | ALERTA_TERMICA 0.35 MW |
| 2026-10-09 06:12 | V375 | si | 0 | 0 | 0 | 0.8505 | 0.8505 | 0.585 | 0.585 | 0.0 | ALERTA_TERMICA 1.22 MW; ALERTA_TERMICA_OCR 1.22 MW |
| 2026-10-09 06:12 | V750 | si | 0 | 0 | 0 | 0.851 | 0.851 | 0.851 | 0.851 | 0.0 | ALERTA_TERMICA 0.82 MW |
| 2026-10-10 04:54 | V375 | si | 0 | 0 | 0 | 0.7574 | 0.7574 | 0.757 | 0.757 | 0.0 | ALERTA_TERMICA 5.72 MW; ALERTA_TERMICA_OCR 5.72 MW |
| 2026-10-10 04:54 | V750 | si | 0 | 0 | 0 | 0.243 | 0.243 | 0.243 | 0.243 | 0.0 | ALERTA_TERMICA 2.48 MW |
| 2026-10-10 05:12 | V375 | si | 0 | 0 | 0 | 2.5832 | 2.5832 | 2.583 | 2.583 | 0.0 | ALERTA_TERMICA 8.75 MW |
| 2026-10-10 05:12 | V750 | si | 0 | 0 | 0 | 1.747 | 1.747 | 1.747 | 1.747 | 0.0 | ALERTA_TERMICA 6.42 MW |
| 2026-10-10 05:54 | V375 | si | 0 | 0 | 0 | 5.5624 | 5.5624 | 5.562 | 5.562 | 0.0 | ALERTA_TERMICA 7.55 MW |
| 2026-10-10 05:54 | V750 | si | 0 | 0 | 0 | 10.481 | 10.481 | 10.481 | 10.481 | 0.0 | ALERTA_TERMICA 13.13 MW |
| 2026-10-10 06:30 | V375 | si | 0 | 0 | 0 | 11.822 | 11.822 | 6.62 | 6.62 | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 12.17 MW |
| 2026-10-10 06:30 | V750 | si | 0 | 0 | 0 | 4.332 | 4.332 | 4.332 | 4.332 | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 32.0 MW |
| 2026-10-10 06:54 | V375 | si | 0 | 0 | 0 | 7.87 | 7.87 | 4.305 | 4.305 | 0.0 | ALERTA_TERMICA 13.78 MW |
| 2026-10-10 06:54 | V750 | si | 0 | 0 | 0 | 1.916 | 1.916 | 1.916 | 1.916 | 0.0 | ALERTA_TERMICA 15.26 MW |
| 2026-10-10 07:40 | MODIS | si | 0 | 0 | 0 | 0 | 0 | 0.786 | 0.786 | 0.0 | ALERTA_TERMICA 3.95 MW |
| 2026-10-10 18:18 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 4.04 MW |
| 2026-10-10 18:18 | V750 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 3.33 MW |
| 2026-10-10 18:54 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 5.27 MW |
| 2026-10-11 04:54 | V375 | si | 0 | 0 | 0 | 0.4059 | 0.4059 | 0.835 | 0.835 | 0.0 | ALERTA_TERMICA 0.3 MW |
| 2026-10-11 05:36 | V375 | si | 0 | 0 | 0 | 1.4233 | 1.4233 | 1.423 | 1.423 | 0.0 | ALERTA_TERMICA 1.38 MW; ALERTA_TERMICA_OCR 1.38 MW |
| 2026-10-11 05:36 | V750 | si | 0 | 0 | 0 | 2.478 | 2.478 | 2.478 | 2.478 | 0.0 | ALERTA_TERMICA 1.03 MW |
| 2026-10-11 06:12 | V375 | si | 0 | 0 | 0 | 0.2479 | 0.2479 | 0.074 | 0.074 | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 0.42 MW |
| 2026-10-11 19:36 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA 15.81 MW |
| 2026-10-12 05:18 | V375 | si | 0 | 0 | 0 | 2.8817 | 2.8817 | 2.882 | 2.882 | 0.0 | ALERTA_TERMICA 7.31 MW |
| 2026-10-12 05:18 | V750 | si | 0 | 0 | 0 | 3.46 | 3.46 | 3.46 | 3.46 | 0.0 | ALERTA_TERMICA 8.44 MW; ALERTA_TERMICA_OCR 8.0 MW |
| 2026-10-12 05:54 | V375 | si | 0 | 0 | 0 | 0.4319 | 0.4319 | 0.432 | 0.432 | 0.0 | ALERTA_TERMICA 0.85 MW; ALERTA_TERMICA_OCR 0.85 MW |
| 2026-10-12 05:54 | V750 | si | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 | ALERTA_TERMICA 0.4 MW |
| 2026-10-12 07:20 | MODIS | si | 0 | 0 | 0 | 0 | 0 | 1.376 | 1.376 | 0.0 | ALERTA_TERMICA 2.18 MW |
| 2026-10-14 05:36 | V375 | si | 0 | 0 | 0 | 0.0837 | 0.0837 | 0.084 | 0.084 | 0.0 | ALERTA_TERMICA 0.12 MW |
| 2026-10-14 06:18 | V375 | si | 0 | 0 | 0 | 2.9744 | 2.9744 | 1.681 | 1.681 | 0.0 | ALERTA_TERMICA 2.54 MW |
| 2026-10-14 06:18 | V750 | si | 0 | 0 | 0 | 1.173 | 1.173 | 1.173 | 1.173 | 0.0 | ALERTA_TERMICA 2.0 MW |
| 2026-10-14 13:05 | MODIS | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_TERMICA_OCR 6.0 MW |
| 2026-10-14 18:42 | V375 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 4.24 MW |
| 2026-10-14 18:42 | V750 | no | 0 | 0 | 0 | None | None | None | None | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 12.0 MW |
| 2026-10-15 05:00 | V375 | si | 0 | 0 | 0 | 10.3611 | 10.3611 | 5.109 | 5.109 | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 22.13 MW |
| 2026-10-15 05:00 | V750 | si | 0 | 0 | 0 | 1.876 | 1.876 | 1.876 | 1.876 | 0.0 | ALERTA_SIN_GEOMETRIA_OCR 14.0 MW |
