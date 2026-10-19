# Verificador con contexto limpio, frente 5 (Nevados de Chillán, detector K)

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f5` en `cb90031a` (origin/main), 2026-10-19 11:05 UTC.
No leí `experiments/_s155_audit/frente_5/`. Todo número de este informe sale de un script de esta carpeta,
con su salida cruda al lado (`vNN_salida*.txt`). Los flags se leyeron desde `pipeline.profile`
(`VRP_PROFILE=mirova_equivalent`): `ENABLE_SINGLE_PIXEL_SUB_MW_MODE True`, `SUB_MW_REGIME_THRESHOLD_MW 5.0`,
`SINGLE_PIXEL_MAX_CLUSTER_PIXELS 3`, `ENABLE_VENT_ANCHORED_CLUSTERING True`, `ENABLE_TEST1_PATH False`,
`ENABLE_MODIS_B22_PRIMARY True`, `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS True`, `ENABLE_UTM_REGRID False`,
`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375/750 False`, `ENABLE_FOCAL_CLUSTER_MAGNITUDE True`, `PATH_D_ONLY_CAP_MW 5.0`.

Ventana: observación 2026-09-28 a 2026-10-19, 229 records de `data/mirova_equivalent/NevadosDeChillan.json`.

## 0. El pareo (base de todo lo demás)

`v01_pareo.py`, pareo por minuto exacto y familia de sensor, igual que `razon_por_cenit.py` de S154.

| referencia | alertas MIROVA en ventana | pares | V375 / V750 / MODIS |
|---|---|---|---|
| `data/mirova_reference/mirova_v1_snapshot/` del worktree | 94 | **80** | 42 / 30 / 8 |
| CSV remoto de Mirova-v1 bajado hoy (md5 consolidado `a2c36be9…`, ocr `210610d6…`) | 125 | **105** | 51 / 40 / 14 |

El consolidado del snapshot del worktree termina para Chillán el **2026-10-14 08:35**; los 105 pares sólo
salen con el remoto. Las 20 alertas sin par son todas diurnas (12-20 UTC); ningún record nuestro cae a
±3 min de ellas (instrumento: si el pareo estuviera corrido un minuto lo vería). Control positivo: la
pasada 2026-10-18 06:48 V750 da 2,84 / 22,85, igual que la salida de S154.

## 1. Veredicto por hallazgo del auditor

### F5-01: magnitud parcial en V750 y MODIS. CONFIRMADO el defecto, PARCIAL la atribución y los factores. Gravedad 4

Método (`v02_reconstruir_cumulo.py`): el cúmulo primario se identifica EXACTO buscando entre los
`anomaly_pixels` el subconjunto de `n_pixels` cuyo centroide redondeado coincide con
`primary_cluster.centroid_lat/lon`. Calzó único en 38 de 38 V750 y 11 de 11 MODIS, y en los 49 el valor
publicado se reproduce como el máximo (modo de un píxel) o la suma del subconjunto: ninguna pasada
NO_CALZA. Ese es el control de que la reconstrucción no es una fórmula inventada.

- Código: `pipeline/clustering.py:149-158` ordena por (dentro del inner, distancia del centroide, -vrp);
  `pipeline/process_viirs_mod.py:1098-1130` y `pipeline/process_modis.py:1119-1203` publican el primero y
  le aplican `apply_single_pixel_mode` (`pipeline/single_pixel_mode.py`, condición `vrp < 5` y
  `n_pixels <= 3`, sin mirar régimen eruptivo). El tablero publica `pc.vrp_mw` en V750 y MODIS
  (`frontend/index.html:1162-1183`).
- V750 (`v09_salida.txt`): 13 de 37 pasadas con publicado > 0 quedan bajo la energía alertada; **11 por
  el modo de un píxel** (mediana ×1,17, máx ×2,21) y **8 por selección** (mediana ×1,88, máx ×5,98), 6 con
  ambos. En log, 36 % del déficit es el modo de un píxel y 64 % la selección. MODIS: 4 de 11 (3 por el
  modo, ×1,40 y ×1,42; 2 por selección).
- Por cenit (V750): afectadas 2 de 11 bajo 30°, 0 de 8 en 30-45°, 6 de 11 en 45-60° (mediana ×1,96),
  5 de 8 sobre 60° (×2,21). El auditor da 12 de 35, ×1,46 y ×1,92: no reproduzco esos factores; mi
  denominador sale del remoto de hoy (A90).
- Peor caso 2026-10-10 06:30 V750: CONFIRMADO publicado 4,33, alertado 25,89, MIROVA 32,0. Es selección
  pura: el cúmulo publicado tiene 2 píxeles (4,33 + 0,00) y el descartado 2 píxeles (16,24 + 5,31) a 0,77 km.
- 2026-10-18 06:48 V750: el ×2,41 (0,12 a 0,30) **no es sólo selección**: ×1,54 modo de un píxel por ×1,56
  selección.
- «Descarta vecinos con más energía»: sólo en 2 de 13 V750 un píxel descartado supera al cúmulo publicado
  (10-10 06:30 y 09-29 06:36), y en 3 la suma descartada lo supera. Lo típico es un fragmento menor.
- Salvedad que baja los factores a COTA SUPERIOR: ver V5-02.

### F5-02: fragmentación por topología del arreglo. PARCIAL (sigue SOSPECHA el origen). Gravedad 3

`v06_fragmentos_y_duplicados.py`. Distancias reproducidas: fragmentos V750 a 0,46 a 1,97 km del píxel más
cercano del cúmulo publicado (mediana 0,81; el 0,46-0,87 del auditor está dentro); V375 a 0,03-0,06 km
en cúmulos distintos (el «40 m» del auditor, CONFIRMADO). A favor del mecanismo: dos centros más cerca que
un paso de muestreo no pueden ser vecinos del mismo barrido, y el código convierte `Bowtie_Deleted`
(65533) en NaN (`pipeline/process_viirs_mod.py:68`, `:248`), lo que corta la conectividad 8 entre
barridos. En contra o sin resolver: mi prueba de dirección (desplazamiento a lo largo del vuelo debería
dar ~90° con el acimut del sensor) da mediana 53° en V750 y 59° en V375, no concluyente. Sin fila y
columna del L1B no se prueba.

### F5-03: el fondo no explica la caída en V375. CONFIRMADO la conclusión, PARCIAL los números. Gravedad 3 (4 para el pre-registro)

`v03_fondo_cero_v375.py`. Control de fórmula: reconstruyo la VRP de los 161 píxeles con
`area 140625 × 18,0 × (L(bt) − L(t_bg))` a 3,74 µm (`pipeline/process_viirs.py:1459-1507`; Chillán sin
`local_kernel_bg`, `scripts/run_pipeline.py:244`), error relativo mediano 0,0001; F5' reconstruido igual
al guardado en 51 de 51. Con fondo cero (cota superior de cualquier cambio de fondo sobre el MISMO
conjunto, D25 incluido), alertas de MIROVA ≥ 1 MW: razón **0,89 / 0,68 / 0,68 / 0,42** por banda
(auditor 0,47 en la última). Spearman cenit contra razón: −0,42 publicada, −0,44 con fondo cero (n 50).
Pero «D25 puede subir a lo más ×1,18 en nadir y ×1,49 en borde» está mal dicho: ×1,18 y ×1,35 son
**medianas** por pasada; el máximo por pasada llega a ×1,71 y ×2,32.
Área (`v04_area_modelo_v375.py`, modelo geométrico propio con agregación 3/2/1, da 4,70× a 70°, cerca del
4,38× del ATBD): razón × área = **0,90 / 0,91 / 1,02 / 0,90**, reproduce lo plano. Compatibilidad, no
causa: la atribución a D17 sigue SOSPECHA.

### F5-04: V750/V375 en la misma pasada. PARCIAL. Gravedad 2

`v05b_variantes.py`. El 1,06 / 0,62 sólo se reproduce como **doble razón** (nuestro/MIROVA en V750 sobre
nuestro/MIROVA en V375): 1,05 (n 11) y 0,61 (n 17). Leído como cociente crudo V750/V375 es engañoso:
MIROVA consigo misma cae igual (1,81 a 0,60). Con V750 total (todo lo alertado) la doble razón queda
1,06 a 0,82: F5-01 explica cerca de dos tercios; queda un residuo propio de V750.

### F5-05: MODIS protegidas no detectadas. CONFIRMADO. Gravedad 2

`v08_salida.txt`: 2026-10-12 07:20 Aqua (cenit 58,2, MIROVA 2,18) y 2026-10-15 01:05 Terra (57,6, 1,72),
nocturnas, `n_anomalous_pixels` 0 y el píxel más tibio del ROI a 24 y 29 km. Esas fechas UTC V375 publicó
2 y 4 pasadas.

### F5-06: tope D9. CONFIRMADO. Gravedad 2

42 de 110 records con detección cumplen la condición; sólo 1 tiene `pc.vrp_mw ≥ 5` y es el C0 de
2026-09-28 01:30 (topado en 5,0, `far`). Ninguna pasada pareada topada. Riesgo latente en noches frías.

### F5-07: lambda B21 con B22 primaria. CONFIRMADO, líneas corregidas. Gravedad 1

`pipeline/process_modis.py:1036` y `:1040` (no 1034/1039). Factor del exceso 0,950 a 0,970 según la
temperatura (`v08`). Ver V5-05.

### F5-08: 3 records C0 Terra. CONFIRMADO. Gravedad 1

2026-09-28 01:25, 01:30 y 2026-10-10 01:05, procesados antes del PR #850, los tres `far` (invisibles).

### F5-09: duplicados de bow-tie que cuentan doble. CONFIRMADO en V375 (origen inferido). Gravedad 3

`v07_f5_sin_duplicados.py`: en 6 de 51 pasadas V375, todas sobre 50° de cenit, el conjunto que suma F5'
tiene pares de píxeles a menos de 0,19 km. Sin el miembro menor F5' cae hasta ×1,88; 2026-10-10 06:30
pasa de 11,82 a 6,70 (MIROVA 12,17), así que la «paridad» de esa pasada es doble cuenta. Efecto en la
mediana de banda chico (60-90°: 0,32 a 0,26). En V750 no hay pares a menos de 0,37 km.

## 2. Hallazgos propios

- **V5-01 (3, CONFIRMADO)**: V375 no es «inmune» como dice F5-01. Es inmune a la selección por cúmulo
  pero expuesto a la doble cuenta de F5-09, que crece con el cenit. La curva V375 por cenit del
  pre-registro está levantada en el borde.
- **V5-06 (2, CONFIRMADO)**: F5' tiene su propia selección dependiente del ángulo. Su radio de núcleo es
  fijo en km (`F5_R_CORE_KM = 0.75`, `pipeline/f5_core.py`, pensado como «dos píxeles I-band» de nadir)
  y en el borde el píxel vecino ya está a más de 0,75 km. `v10_f5_excluidos.py`: 21 píxeles excluidos en
  15 de 51 pasadas, 17 de ellos a 0,75-1,43 km del pico con BT bajo 295 K (2,05 MW contra 192,37 MW
  publicados, 1 %), 13 de esos 17 sobre 60°. Por pasada pesa: 2026-10-17 04:42 publica 0,84 y deja fuera
  0,61 (×1,73), 2026-09-28 04:42 publica 0,49 y deja 0,17. Va en sentido opuesto a V5-01.
- **V5-02 (3, SOSPECHA)**: si los fragmentos V750 a 0,46-0,87 km son huellas solapadas (F5-02), sumar
  todo también cuenta doble. Los factores de selección de F5-01 (hasta ×5,98) son cota superior, y un
  arreglo «sumar todos los cúmulos» necesita deduplicar por huella (la grilla de MIROVA lo hace sola).
- **V5-03 (2, CONFIRMADO)**: la referencia no está congelada. El snapshot del worktree da 80 pares, el
  remoto de hoy 105, y mis conteos V750 (38) difieren de los del auditor (35). El pre-registro tiene que
  fijar el archivo por hash.
- **V5-04 (3, CONFIRMADO)**: el modo de un píxel se activa por fragmento, no por erupción: sobre 60° está
  en modo MAX en 7 de 7 pasadas V750 con publicado > 0 (3 de 11 bajo 30°), porque la suma del fragmento
  queda bajo 5 MW.
- **V5-05 (1, SOSPECHA)**: con B22 primaria, el NTI_app de la detección MODIS también usa la lambda de
  B21 (`pipeline/process_modis.py:773`, `:857`). La regresión cuadrática probablemente lo absorbe. Sin medir.
- **Propuesta, no hallazgo**: el área de VIIRS tiene dientes de sierra (la agregación cambia a 31,59° y
  44,68° de barrido, ~36° y ~54° de cenit). Si la razón contra MIROVA sigue esos saltos en toda la flota,
  la causa es área o remuestreo (D17); un confusor suave no los produce.

## 3. VERIFICADO LIMPIO

- Fórmula VRP V375 por píxel, área nadir fija y fondo del anillo: `python v03_fondo_cero_v375.py`
  (161 píxeles, error mediano 1e-4).
- `f5_core_vrp_mw` guardado igual al recalculado en 51 de 51 (`v03`). (Una afirmación de mi borrador,
  «F5' sólo deja fuera lo que está a más de 5 km», resultó FALSA al medirla con `v10`: ver V5-06.)
- `pc.vrp_mw` V750/MODIS reproducido como máximo o suma del cúmulo en 49 de 49; la magnitud focal MODIS
  no movió nada en la ventana; el ancla del ranking es `vent_lat/lon` en los 49 (`v02`, columna `anchor_ok`).
- El tablero usa `pc.vrp_mw` en V750 y MODIS y F5' sólo en I-band: `frontend/index.html:1162-1183` y `:1295-1315`.
- Las 20 alertas MIROVA sin par son diurnas, sin record nuestro a ±3 min (`v01_salida_remoto.txt`).
- `Bowtie_Deleted` va a NaN en V750: `pipeline/process_viirs_mod.py:68`, `:248`.
