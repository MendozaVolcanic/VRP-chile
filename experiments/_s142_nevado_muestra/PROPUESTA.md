# S142: muestra nevada para el probe del vecino del foco (VIIRS 375 m)

Estado: **no hay muestra nevada viable con los datos de hoy.** Requiere verificador con contexto limpio
antes de cualquier uso, y una decisión de Nicolás (backfill) antes de que exista algo que verificar.

## 1. El fenómeno y por qué importa el estrato

En un volcán de cumbre nevada, de noche, la nieve de la cumbre queda más fría que el valle, y el canal MIR
de 3,7 µm ve ese gradiente de altitud como si fuera "exceso" sobre el fondo (A69). Un foco sub-píxel real
(lago de lava, domo) calienta además a sus vecinos de 375 m sólo un poco. La pregunta del probe es qué test
deja fuera a esos vecinos tibios. En los nevados el fondo contra el que se miden está contaminado por la
topografía, así que la respuesta puede no ser la de los volcanes focales del altiplano. Por eso el
pre-registro pide el estrato por separado, con al menos 3 volcanes evaluables y 3 pasadas válidas cada uno
(`docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md:133` y `:142`).

## 2. Qué es "nevado" y qué ventana usó el v2 (anclado)

- Estratos: `scripts/build_c2ab_windows.py:41` FOCAL = Láscar, Lastarria, Isluga, Planchón-Peteroa,
  Puyehue-Cordón Caulle; `:42` NEVADO = Llaima, Copahue, Villarrica, Nevados de Chillán, Tupungatito,
  Chaitén. `muestra.py:63` marca "nevado" todo lo que no es FOCAL.
- Ventana: `scripts/descomponer_magnitud_osf.py:56` `T0, T1 = 2025-02-15, 2025-12-01`; `cargar` filtra el
  OSF por esa ventana, noche (`Dayflag == 0`) y nuestros records a ±7 h (`:75`, `:81`).
- Criterio (sin tocar): `muestra.py:78-79` candidato `Npix >= 3 & pub_n == 1`, control `Npix >= 3 &
  pub_n >= Npix`; `:94-103` exclusiones en orden `pasada_del_v1`, `sin_posicion_osf`,
  `sin_pico_persistido`, `foco_mirova_lejos` (> 0,75 km de nuestro pico, `:39`); `:107` espaciado a 6 y 2.
  Antes de eso `build` exige un record nuestro a ±10 min (`descomponer_magnitud_osf.py:92`) con cúmulo en el
  cráter (`:86-89`).

## 3. Qué hay disponible

- **OSF v2.5**: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, `timeUTC` de 2000-02-24 a 2025-12-31
  (salida de pandas en esta sesión).
- **Nuestros records**: los 11 Tier A empiezan el **2025-02-15** (primer `datetime_utc` de cada JSON en
  `data/mirova_equivalent/`). **No existe ningún record nuestro de 2024 ni de 2025-01-01 a 2025-02-14**
  (`seleccion_nevado.json`, `records_375_nuestros_en_ventana_mas_7h` = 0 en 2024; los 4 a 5 de
  "2025_antes_v2" son pasadas del 15-feb que caen en el margen de ±7 h). La ola P4 del backfill
  (2025-01-01 a 2025-02-15) figura sin hacer en `docs/BACKFILL_PLAN_S120.md:79`, y 2024 es la P5 opcional,
  "decisión Nicolás" (`:26`).
- **Diciembre 2025 tampoco sirve**: 0 records VIIRS 375 en 10 de los 11 volcanes; sólo Villarrica tiene
  141 (conteo mensual en esta sesión). Noviembre 2025 queda a medias (la ola P1 terminó el 2025-11-15).
  Y en diciembre el OSF no tiene ninguna pasada nevada con `Npix >= 3` (embudo de "2025_despues_v2").

## 4. Resultado de la selección con el mismo criterio

Script: `experiments/_s142_nevado_muestra/seleccion_nevado.py`, que importa `seleccionar`,
`resumen_muestra` y `_pico_persistido` de `muestra.py` y sólo cambia `T0/T1` y la lista de exclusión
(v1 + v2). Salida: `seleccion_nevado.json`.

**Control del instrumento**: la ventana del v2 con exclusión del v1 reproduce exactamente
`experiments/_s141_fase1_probe_v2/muestra_resumen.json` (`reproduce_muestra_resumen_v2: true`).

| ventana | filas de `build` | pasadas nevadas aptas | motivo |
|---|---|---|---|
| 2024 | 0 | 0 | sin records nuestros: nada que parear |
| 2025-01-01 a 2025-02-15 | 0 | 0 | sin records nuestros; el OSF tiene 4 de Villarrica con `Npix >= 3` |
| 2025-12-01 a 2026-01-01 | 2 | 0 | ningún nevado con `Npix >= 3` en el OSF; 10 volcanes sin records |

Por volcán, en ninguna ventana nueva hay candidatos, controles ni exclusiones que reportar: las filas no
llegan a `seleccionar`, se pierden antes, en el pareo. **El pre-registro (≥ 3 volcanes con ≥ 3 pasadas) no
se alcanza.** Si se corre el probe tal cual, el estrato nevado sale INDETERMINADO:pocos_volcanes.

## 5. Techo si Nicolás decide backfill (sólo OSF, `cota_osf_anual.py`)

Cuenta pasadas nevadas, nocturnas, de clase volcánica, con `Npix >= 3` y el foco de MIROVA a ≤ 0,75 km del
**cráter**. Es un techo optimista, no el criterio: H1 exige nuestro pico, y en Nevados de Chillán 2025 el
foco estaba a 15,46 km de mediana del cráter (embudo del control).

| año | volcanes con ≥ 3 | Chaitén | Nevados de Chillán | Villarrica |
|---|---|---|---|---|
| 2012 a 2016 | 2 | 57 a 185 | 0 | 14 a 94 |
| 2017 | 3 | 131 | 11 | 70 |
| 2018 a 2022 | 3 | 119 a 318 | 353 a 398 | 113 a 205 |
| 2023 | 2 | 45 | 0 | 173 |
| 2024 | 2 | 11 | 1 | 78 |

Copahue tiene como mucho 1 en todo el período, y ni Llaima ni Tupungatito aparecen (Llaima sólo 3 filas en
2012, `Npix` sin filtrar). **El estrato nevado depende siempre de los mismos tres volcanes, y los tres
superan el mínimo a la vez sólo entre 2017 y 2022.** Un backfill de 2024 no resuelve nada: da como mucho 2
volcanes (Villarrica, Chaitén) y Chillán queda con 1.

## 6. Riesgos de una muestra nueva

1. **Versión de código.** Los records de 2025 salen del backfill S120 (commits `data(backfill)` del
   2026-07-02 y 2026-07-15) y, en Villarrica, de la serie recomputada en #519 (2026-08-26). #535 es del
   2026-08-28 (`git log`). Ningún record de 2025 lleva `processed_utc` y `diag_L_bg_local_w_m2_sr_um`
   aparece sólo en records de 2026-09 (conteo en esta sesión). O sea: el pico persistido de cualquier
   muestra de 2025 es del régimen anterior a #535, y el probe reprocesa con el código de hoy. Un backfill
   hecho ahora quedaría en el régimen nuevo y **no sería homogéneo con v1 ni v2**. H7 del plan (tres
   "picos", `:168-170`) ya lo declara, pero entre ventanas la heterogeneidad crece.
2. **Estacionalidad.** En 2024 las 117 de Villarrica caen casi todas entre enero y mayo (embudo); en 2025
   las del v2 son de febrero a abril. Verano y otoño austral: menos nieve en la cumbre, así que el gradiente
   topográfico que define al estrato sería más débil justo en las pasadas disponibles. SOSPECHA: no medí
   cobertura nival.
3. **Fase eruptiva distinta.** 2018 a 2022 en Chillán es el período de crecimiento de domo con cientos de
   pasadas; Chaitén en esos años muestra señal sostenida. Mezclarlos con 2025 compara focos físicamente
   distintos (intensidad, tamaño). SOSPECHA: no verifiqué la cronología eruptiva en esta sesión.
4. **Cuantización del foco (D15).** `docs/MIROVA_DIVERGENCES.md:1768-1780`: la posición de MIROVA en 375 m
   está en celdas enteras de 0,375 km. El radio de 0,75 km son dos celdas, y las medianas de distancia al
   cráter se repiten en pocos valores (0,299, 0,333, 0,117). Pasar el filtro significa "misma celda o
   vecina", no coincidencia de posición.
5. **Sensores.** Antes de 2018 sólo hay S-NPP (SOSPECHA de fecha; no verificado aquí). Menos pasadas por
   noche y otra geometría de barrido que en v1/v2.

## 7. Qué puede y qué no puede afirmar

- Hoy: **nada sobre el estrato nevado.** Lo único afirmable es negativo e instrumental: con records desde
  2025-02-15, el OSF y el criterio H1 no dan volcanes nevados evaluables fuera de lo ya mirado.
- Con un backfill de 2017 a 2022 para Chaitén, Chillán y Villarrica, a lo más: un patrón en esos tres
  volcanes, en fase eruptiva de domo y lago de lava, con otro código que v1/v2. Sin margen: si uno de los
  tres pierde pasadas por H1 o por `pub_n`, vuelve a INDETERMINADO. No podría decir nada de Llaima, Copahue
  ni Tupungatito, que son justo los nevados con señal débil donde A69 pesa más.

## 8. Cambio mínimo en el probe (si se decide)

Sin tocar criterio: (a) en `muestra.py`, la ventana `T0/T1` del módulo importado (hoy fija en
`descomponer_magnitud_osf.py:56`) y la lista de exclusión ampliada a v1 + v2, que es exactamente lo que hace
`seleccion_nevado.py`; (b) la lista `pasadas.json` que lee el runner. Requisito previo que **no** es del
probe: records nuestros en la ventana (backfill P5 u otro), decisión de Nicolás. Antes de correr, el
verificador limpio debe revisar la homogeneidad de código (riesgo 1) y la fase eruptiva (riesgo 3).

## Archivos

- `experiments/_s142_nevado_muestra/seleccion_nevado.py` y `seleccion_nevado.json`
- `experiments/_s142_nevado_muestra/cota_osf_anual.py` y `cota_osf_anual.json`
- Nada descargado; ningún archivo existente modificado.
