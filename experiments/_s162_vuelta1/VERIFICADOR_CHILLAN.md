# Verificador de los hallazgos CH162-01 a CH162-05 (Chillán, A/B de D25 sobre K, ventana V1)

- Hora del servidor: inicio Sat, 24 Oct 2026 13:46:11 GMT; cierre de mediciones 13:59:17 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date).
- Commit medido: código del A/B `s157-d25-k-codigo` = `66961f65d261d8ea4197c2e4985edab7fd052b8e` (leído con `git show 66961f65d:<ruta>`, copias en `src/`). Producción comparada: `origin/main` (entre el tag y `origin/main` sólo cambia `pipeline/fetch.py`, `git diff 66961f65d origin/main --stat -- pipeline/`).
- Records: control K sha256 `927ebe6d…2b75`, brazo D sha256 `dc3bb4fd…9e5d` (Chillán), y los otros 10 volcanes de los mismos directorios. Referencia congelada de MIROVA: sha256 con fin de línea LF igual al MANIFIESTO (`5ae612a6…`, `904b331a…`); en disco están en CRLF, por eso el sha crudo difiere.
- Código de MIROVA: `C:\vrp-trabajo\s159-m\experiments\_s158_d17_diseno\osf_codigo_mirova\MIROVA_VIIRS750_VRP.m`, sha256 `af9e9115…0865`, md5 idéntico en las tres copias de s159-m, s159-n y s159-pruebas.
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo por configuración de la sesión, con todas las mediciones corridas por script.
- Qué NO miré: los gránulos L1B (no los bajé; sin ellos el mecanismo de índice de grilla queda en SOSPECHA), MODIS (el A/B no lo corre), la ventana V2, el brazo gemelo, la carpeta del auditor `vuelta1/chillan_p1b` (a propósito, para no heredar su razonamiento), y el fondo que el programa de MIROVA habría interpolado en esas pasadas (exige el gránulo remuestreado).
- Scripts y salidas: todo en esta carpeta (`m01*` a `m07*`, con su `_salida.txt`). Caminos escritos antes de releer: `caminos.md`.

## En una pantalla

1. CH162-01 CONFIRMADO, y es un defecto de K en producción, no de D25: el registro de `origin/main` publica 1,173 MW en V750 2026-10-14 06:18 con el píxel de 1,89 MW fuera del cúmulo. Con cualquier selección que incluya ese píxel (o con `vrp_max` en el brazo D), D queda sobre 1 MW, así que el cruce P1b de V750 depende de este defecto.
2. Hallazgo propio VC162-01 (gravedad 3): en pasadas oblicuas los cúmulos se arman por índice de grilla y no por geografía. En los 6 V750 multi-cúmulo de Chillán con cenit de 50° o más, dos píxeles de cúmulos distintos quedan más cerca entre sí (0,46 a 0,87 km) que los píxeles de un mismo cúmulo (1,07 a 1,38 km). En V375, con cenit de 50° o más, 26 de 51 records multi-cúmulo tienen píxeles de cúmulos distintos a menos de 0,30 km; bajo 30°, 3 de 91. El mecanismo de bow tie es SOSPECHA.
3. La protegida de V375 (2026-10-11 05:36) NO tiene ese problema: es un cúmulo único de 5 píxeles. D la baja porque el halo de vecinos (BT equivalente de 265,4 a 269,9 K, despejada de los records con control 65/65) es más tibio que el anillo (262,09 K). Esa sí es un efecto genuino de D25.
4. CH162-04 CONFIRMADO en el código: para 4 alertados o menos, MIROVA dilata 3x3 (aparta justo los 8 vecinos que D25 usa), interpola con `fillmissing2`, suma todos los alertados y no recorta. D25, tal como está, no es el fondo del programa de MIROVA para V750.
5. CH162-02 se reproduce exacto (57/61 y 33/33, contando las pasadas en que ambos brazos publican más de 0), pero es casi una identidad aritmética: con la suma de escena coincide 69/69 y 34/34. CH162-03 se confirma en parte: anillo frío y sigma alta sí; «despejadas» no tiene instrumento, porque la máscara de nube está apagada y `n_cloud_masked` vale 0 siempre. En CH162-05, V750 da 21/24 exacto; V375 da 24/34 sólo con `pc.vrp_mw`, y con el campo que publica el tablero (`f5_core`) da 25/34.

## Veredictos

### CH162-01: el cúmulo publicado en V750 2026-10-14 06:18 no contiene al píxel más caliente. CONFIRMADO. Gravedad 3.

- Datos (`m01b_salida.txt`): tres píxeles alertados en el record NOAA-21 V750 06:18 (gránulo `VJ202MOD.A2026287.0618`), con A = (-36.8686, -71.37578), 275,81 K, 1,8896 MW en K, 0,63 km; B = (-36.86438, -71.38119), 270,27 K, 1,1729 MW, 0,40 km; C = (-36.86538, -71.36671), 268,21 K, 0,9462 MW, 0,95 km. `primary_cluster` tiene n_pixels 2 y centroide (-36.86488, -71.37395), que es exactamente la media de B y C. `n_hotspots_clustered` = 2. La membresía se infirió por búsqueda de subconjuntos con control positivo: el VRP del cúmulo se reproduce en 643/643 records V375 y 154/154 V750 (`m01_salida.txt`).
- Código: `clustering.py:149-158` en 66961f65d (`_vent_key` = dentro del inner, luego distancia del CENTROIDE, luego -vrp). El centroide de B y C, que están a lados opuestos del cráter, queda a 0,343 km y le gana al de A (0,63 km). La cita «144-154» del auditor cae en ese bloque (143 a 158). Después, `process_viirs_mod.py:1125` aplica `apply_single_pixel_mode` (umbral 5 MW, máximo 3 píxeles, `mirova_equivalent.yaml:532-534`) y publica el máximo de B y C: 1,173 en K y 0,632 en D.
- Suma de escena: 1,8896 + 1,1729 + 0,9462 = 4,0087 (record 4,009) en K; 1,3631 + 0,6318 + 0,3998 = 2,3947 (record 2,395) en D. MIROVA: fila CONS `ALERTA_TERMICA`, 2026-10-14 06:18:02, VIIRS (750), 2,0 MW a 1,06 km, mismo minuto. El pareo es correcto.
- ¿Defecto de K en producción? Sí. El perfil de control es `extends: mirova_equivalent` más los tres flags de K, y el record de `origin/main` (`data/mirova_equivalent/NevadosDeChillan.json`, `codigo_sha` 34cea39e) es idéntico: pc 2 píxeles, 1,173, centroide 0,343, escena 4,009. No depende de D25.
- Contrafactual (aritmética sobre el record, no una corrida): si A estuviera en el mismo cúmulo, el modo de un píxel publicaría A: 1,890 en K y 1,363 en D, y D no cruzaría 1 MW. Con `vrp_max`, K elige {B,C} (2,119 > 1,890) y sigue en 1,173; D elige {A} (1,363 > 1,032) y publica 1,363. El cruce P1b de V750 aparece sólo con la selección actual.
- Mismo patrón en V1 (`m01_salida.txt`, membresía inferida, «pico» = máximo de BT o de VRP entre los alertados a menos del `inner_radius_km` del centroide):
  - V750: 5 records con patrón, 4 de ellos protegidos (alerta de MIROVA de 1 MW o más en el mismo minuto), los 4 de Chillán: 2026-09-29 06:36 (CONS+OCR 2,03), 2026-10-10 06:30 (sólo `ALERTA_SIN_GEOMETRIA_OCR` 32), 2026-10-14 06:18 (CONS 2,0) y 2026-10-15 05:00 (sólo `ALERTA_SIN_GEOMETRIA_OCR` 14). Con etiqueta con geometría quedan 2. En el resto de los volcanes hay 0 protegidas en V750; el quinto caso es PCC 2026-09-17 06:30, que no está protegido (MIROVA 0,38).
  - V375: 5 protegidas con el patrón en `pc` (Isluga 2026-10-03 05:18, sólo OCR, y 4 de Chillán), pero en V375 el tablero publica `f5_core_vrp_mw`, que se ancla en el píxel de mayor VRP a menos de `inner_km` del centroide (`f5_core.py`). Incluye el pico por construcción, así que en V375 el patrón no llega al número publicado.

### CH162-02: el signo del cambio de D coincide con el signo de (vecinos menos anillo). CONFIRMADO, con una salvedad que le quita casi todo el peso. Gravedad 1.

- Se reproducen exactamente 57/61 en V375 y 33/33 en V750, contando las pasadas de Chillán V1 en que ambos brazos publican más de 0 y D difiere de K (`m02c_salida.txt`, regla «pub>0 ambos»). Sobre todo V1 (alguno publica) da 65/69 y 34/34 (`m02_salida.txt`). Todos los records son nocturnos (cenit solar mínimo 123,06°).
- Cenit (`m02_salida.txt`): V375 23/26 bajo 30°, 18/19 entre 30° y 50°, 24/24 sobre 50°. Las 4 excepciones están a 20,0°, 23,2°, 29,8° y 38,9°. No hay dependencia que empeore con el cenit. CONFIRMADO.
- Salvedad: es casi una identidad. D resta un fondo mayor cuando los vecinos son más tibios que el anillo, y el VRP baja. Con la suma de escena el signo coincide en 69/69 y 34/34. Las 4 excepciones salen de que `diag_L_bg_vecinos_w_m2_sr_um` es la MEDIANA sobre todos los alertados de la escena (`process_viirs.py:1497`, `process_viirs_mod.py:1052`) y no el fondo del píxel publicado. Lo que sí informa es la fracción: en Chillán V1 el halo es más tibio que el anillo sólo en 15/61 (V375) y 4/33 (V750) de las pasadas (`m02d_salida.txt`). En la mayoría D sube la magnitud.

### CH162-03: las dos protegidas caen en noches de anillo frío con sigma alta; máscara de nube apagada. CONFIRMADO EN PARTE. Gravedad 2.

- Anillo (`m03_salida.txt`, `t_bg_k` = BT MIR del fondo: I04 en V375, M13 en V750): 10-11 05:36 da 262,09 K (V375) y 260,44 K (V750); 10-14 06:18 da 258,44 y 256,91. Sigma: 5,29 y 7,77 en V375 (percentiles 71 y 91 de 214), 5,02 y 7,63 en V750 (percentiles 79 y 92). Las noches enteras son frías: 10-11 va de 252,5 a 262,1 K y 10-14 de 252,6 a 263,6 K en V375. CONFIRMADO.
- «Frente a 268 a 276 K en noches despejadas»: en parte. Las otras pasadas con alerta de MIROVA de 1 MW o más quedan en 261,1 a 275,5 K (V375) y 263,0 a 274,5 K (V750); dos de V375 (2026-09-28 04:42 a 261,84 K y 2026-10-09 06:12 a 261,14 K) están tan frías como la del 11-oct. Lo que sí separa a las dos protegidas es la sigma: el resto anda entre 3,4 y 4,5 K. «Despejadas» no está definido por ningún instrumento.
- Máscara: `cloud_mask_bt_k: 0.0` en `thresholds:` (`mirova_equivalent.yaml:53`), leído de esa sección (`profile.py:89`, `_t.get("cloud_mask_bt_k", 260.0)`). CONFIRMADO. Pero `n_cloud_masked` vale 0 en 217/217 records V375 y NO existe en los 214 V750. Con umbral 0 K es un instrumento muerto: no distingue nube de despejado. La nube sigue en SOSPECHA y no hay dato en los records que la pruebe ni la refute.
- Relación con CH162-02 (`m03b_salida.txt`): las pasadas en que D baja tienen anillo más frío (mediana 261,6 K en V375 y 260,6 K en V750) que las pasadas en que D sube (270,8 y 269,8 K), y sigma más alta (5,23 contra 3,82 en V375). Es una tendencia, no una regla: hay pasadas con D subiendo a 232,6 K.

### CH162-04: el programa de MIROVA y D25 usan fondos distintos. CONFIRMADO en el código; la temperatura de los vecinos queda CONFIRMADA como BT equivalente. Gravedad 3 (para la decisión de adoptar D25 en V750).

- MIROVA (`MIROVA_VIIRS750_VRP.m:63-85`): pone NaN en los alertados; dilata con `strel('square', k)`, con k = 3 si hay 4 alertados o menos, 5 hasta 30 y 7 sobre 30 (l. 68-78); interpola con `fillmissing2(…, 'linear')` (l. 81); `deltaL = sum(L_hot) - sum(L_bk)` sobre todos los alertados, sin recorte por píxel (l. 83-85). Con 4 alertados o menos, la dilatación 3x3 saca justo los 8 vecinos inmediatos, que son los que D25 promedia. Además opera sobre `ZI_M13` remuestreado (l. 10), no sobre el barrido nativo.
- Nuestro D25 (66961f65d): `vrp_regimes.py:110-176` (`neighbor_mean_radiance_background`, media de la radiancia de los vecinos no alertados en 3x3, que se agranda hasta 7x7 sólo si no queda ninguno); se llama en `process_viirs.py:1492-1497` y en `process_viirs_mod.py:1047-1052`, y se recorta por píxel con `np.maximum(L_hot - L_bg, 0)` (`process_viirs.py:1504`, `process_viirs_mod.py:1056`). Las citas del auditor (1492, 1047) caen en esos bloques. CONFIRMADO.
- «Vecinos a 265 a 270 K el 11-oct»: CONFIRMADO como BT equivalente de la radiancia media de los vecinos de cada píxel, despejada de los dos brazos (`m04_salida.txt`): 267,89 / 269,85 / 267,52 / 265,43 / 267,79 K en V375 10-11 05:36, contra un anillo de 262,09 K. Control positivo: la mediana despejada reproduce `diag_L_bg_vecinos` en 65/65 records. La BT de cada vecino individual no está en los records (SIN DATO). En V750 10-14 06:18 los tres píxeles dan 263,9 a 264,1 K contra un anillo de 256,91 K.
- «Halo tibio que el programa de MIROVA aparta»: CONFIRMADO lógicamente (dilatación 3x3 con 4 alertados o menos). Qué fondo habría interpolado MIROVA en esas pasadas: SIN DATO.

### CH162-05: D queda más cerca de MIROVA que K. CONFIRMADO EN PARTE. Gravedad 2.

- Pareo por volcán, banda y minuto UTC con filas CONS `ALERTA_TERMICA` y pasadas en que ambos brazos publican más de 0 (`m05_salida.txt`, `m05b_salida.txt`). V750: 21/24, exacto, con el campo publicado `pc.vrp_mw`. V375: 24/34 sale sólo si se usa `pc.vrp_mw`; con el campo que publica el tablero (`f5_core_vrp_mw`, respaldo `pc`) da 25/34. Sacando los días D-29 (10-13 y 10-17), 22/31. Con CONS+OCR: 30/41 y 23/27. La conclusión no cambia con la variante: D queda más cerca en 71 a 88 % de los pares.
- Contexto que el enunciado no dice: aun así las dos quedan bajo MIROVA (mediana de la razón CONS+OCR: V375 0,573 en K y 0,601 en D; V750 0,418 en K y 0,556 en D). Las dos protegidas en discusión están entre los pares en que K queda más cerca (10-11 05:36 V375: K 1,225, D 0,909, MIROVA 1,38; 10-14 06:18 V750: K 1,173, D 0,632, MIROVA 2,0).

## Hallazgos propios

### VC162-01: en pasadas oblicuas, el cúmulo se arma por índice de grilla del barrido y separa píxeles que en el terreno están juntos.

- SCRIPT:SALIDA: `m01c_bowtie.py` → `m01c_salida.txt`; `m01d_v750_partidos.py` → `m01d_salida.txt`. Código: `clustering.py:96` (`ndi_label(hot_mask_2d, structure=8)` sobre índices fila y columna), llamado en `process_viirs_mod.py:1098` y `process_viirs.py`.
- QUÉ PASA: lejos del nadir, dos barridos sucesivos de VIIRS se solapan en el terreno (efecto bow tie). Un mismo foco puede caer en filas que no son vecinas en la matriz. `cluster_hotspots` une píxeles por vecindad en la matriz, no por distancia, así que un foco puede quedar repartido en dos cúmulos, y la selección `vent_anchored` publica un fragmento. Medido: en V375, la fracción de records multi-cúmulo con píxeles de cúmulos distintos a menos de 0,30 km es 3/91 bajo 30° de cenit, 15/67 entre 30° y 50° y 26/51 sobre 50°. El control (dos píxeles del MISMO cúmulo a menos de 0,30 km) da 1/67. En V750 de Chillán, en los 6 records multi-cúmulo con cenit de 50° o más, la distancia mínima entre cúmulos (0,46 a 0,87 km) es MENOR que la distancia mínima dentro del cúmulo (1,07 a 1,38 km): la vecindad de la matriz está invertida respecto del terreno. El caso más extremo: Chillán V375 2026-10-15 05:00 (cenit 62,4°), dos píxeles a 0,026 km en cúmulos distintos.
- CÓMO SE VE EN EL DASHBOARD: en V750 (que publica `pc.vrp_mw`) la magnitud de pasadas oblicuas sale de un fragmento del foco; es el caso de CH162-01. En V375 el `f5_core` lo amortigua porque agrupa por distancia geográfica. La suma de escena (`vrp_mw`) puede contar dos veces el terreno solapado (SOSPECHA).
- CÓMO REPRODUCIRLO: `cd <CARPETA> && python m01c_bowtie.py && python m01d_v750_partidos.py`; caso Chillán V750 NOAA-21 2026-10-14 06:18 UTC.
- CONFIANZA: CONFIRMADO el hecho geográfico (sobre las lat/lon persistidas y la membresía validada); el mecanismo (bow tie, filas no contiguas o borradas por `Bowtie_Deleted`, `process_viirs.py:83`) es SOSPECHA hasta mirar los índices en el gránulo. D28 del catálogo trata el bow tie de MODIS, no este efecto sobre el agrupamiento en VIIRS (`git grep` sin coincidencias de `ndi_label` ni de agrupamiento por índice en `docs/MIROVA_DIVERGENCES.md`).
- GRAVEDAD: 3. Tuerce la magnitud V750 que ve el operador en pasadas oblicuas (Chillán 10-14: 1,17 MW publicado con un píxel de 1,89 al lado) y decide el único cruce P1b de V750 del A/B.

### VC162-02: P1b mira sólo hacia abajo; en V750 D sube más protegidas sobre 1 MW de las que baja.

- SCRIPT:SALIDA: `m07_cruces.py` → `m07_salida.txt`; `m06_v750_protegidas.py` → `m06_salida.txt`.
- QUÉ PASA: en V1, entre las protegidas con record (alerta CONS u OCR de 1 MW o más, sin las SIN_GEOMETRIA), D baja de 1 MW a 1 en V375 (Chillán 10-11 05:36) y a 1 en V750 (Chillán 10-14 06:18, la que depende de CH162-01). En V750 sube 3 sobre 1 MW (PCC 2026-09-18 05:24: 0,536 a 1,011, MIROVA 1,43; Chillán 2026-09-29 06:00: 0,717 a 1,697, MIROVA 2,52; Chillán 2026-09-29 06:36: 0,329 a 1,095, MIROVA 2,03). De 26 protegidas V750 con `pc`, K muestra 1 MW o más en 19 y D en 21.
- CÓMO SE VE EN EL DASHBOARD: lo que el operador ve en V750 sobre 1 MW cuando MIROVA alerta sobre 1 MW mejora con D, salvo una pasada.
- CÓMO REPRODUCIRLO: `python m07_cruces.py`.
- CONFIANZA: CONFIRMADO (conteo propio). No es un defecto del evaluador: el prerregistro define P1b sólo hacia abajo a propósito. Es contexto para la decisión.
- GRAVEDAD: 2.

### VC162-03: en V750, el modo de un píxel deja bajo 1 MW protegidas que la suma de los alertados (lo que suma MIROVA) deja sobre 1 MW.

- SCRIPT:SALIDA: `m06_salida.txt`. Código: `single_pixel_mode.py` (publica el máximo del cúmulo si pesa menos de 5 MW y tiene 3 píxeles o menos) contra `MIROVA_VIIRS750_VRP.m:83-85` (suma).
- QUÉ PASA: Chillán V750 2026-10-11 05:36, MIROVA 1,03, ya en K: suma 1,664, publicado 0,870. En 26 protegidas V750 la mediana de la razón contra MIROVA es 0,380 para lo publicado en K y 0,416 para la suma en K; en D, 0,551 publicado y 0,706 suma. La suma de todos los alertados ya está catalogada como D32/D34; lo nuevo es medir su peso en las protegidas V750 de esta ventana.
- CÓMO SE VE EN EL DASHBOARD: magnitudes V750 más bajas que MIROVA en régimen de 1 a 5 MW.
- CONFIANZA: CONFIRMADO (aritmética de los records). GRAVEDAD: 2.

### VC162-04: alertas nocturnas protegidas de MIROVA sin record en ninguno de los dos brazos.

- SCRIPT:SALIDA: `m06_salida.txt`, filas «SIN RECORD».
- QUÉ PASA: Chillán V750 2026-10-12 05:18 (alerta de 1 MW o más) no tiene record en K ni en D, y las de 2026-10-18 caen fuera del rango de los records (último record 2026-10-17 06:18, mientras la referencia congelada llega al 2026-10-18). Las de 18:xx UTC son diurnas y el pipeline es nocturno, así que esas están bien fuera. No lo investigué más allá (podría ser falta de gránulo). La memoria del proyecto ya registra que cero gránulos se reporta como cobertura completa (`run_pipeline.py:417`, AUDIT_S158).
- CONFIANZA: SOSPECHA en la causa; CONFIRMADO que no hay record. GRAVEDAD: 2.

## VERIFICADO LIMPIO

- Pareo con MIROVA de las dos protegidas: misma banda y mismo minuto, filas CONS `ALERTA_TERMICA` (V750 10-14 06:18:02, 2,0 MW, 1,06 km; V375 10-11 05:36:02, 1,38 MW, 0,53 km, más OCR con 1,38 a 0,54 km). Vara: `grep -i chill registro_vrp_consolidado.csv | grep 2026-10-1[14]` en `_congelado_v1`.
- Integridad de la referencia congelada: sha256 con LF igual al MANIFIESTO. Vara: `tr -d '\r' < f | sha256sum`.
- Brazo de control = producción K en lo que importa: perfil `extends: mirova_equivalent` más `enable_test1_path: false`, `enable_tests_23_prose_branch: true` y `enable_modis_b22_primary: true`; entre el tag y `origin/main`, en `pipeline/` sólo cambia `fetch.py`. Los 4 records discutidos son idénticos en `origin/main`. Vara: `git diff 66961f65d origin/main --stat -- pipeline/` y lectura de `git show origin/main:data/mirova_equivalent/NevadosDeChillan.json`.
- Brazo D: único cambio declarado, `enable_vrp_bg_neighbor_mean_viirs375/750: true`; los records D llevan `diag_L_bg_vecinos_w_m2_sr_um` y `diag_bg_vecinos_n_sin_vecinos` (0 en la pasada 06:18). Vara: `git show 66961f65d:pipeline/profiles/_s157_ab_d25_k_on.yaml`.
- Inferencia de membresía del cúmulo: 643/643 (V375) y 154/154 (V750) reproducen `pc.vrp_mw` (máximo en modo de un píxel, suma en el resto). Vara: `python m01_cumulo_sin_pico.py`.
- Inversión del fondo por vecinos desde los dos brazos: 65/65 reproducen la mediana persistida. Vara: `python m04_fondo_vecinos.py`.
- Suma de escena = suma de los VRP por píxel en la 06:18 V750 (4,0087 a 4,009 y 2,3947 a 2,395). Vara: `m01b_salida.txt`.
- Todos los records de Chillán en V1 son nocturnos (cenit solar mínimo 123,06°). Vara: primera línea de `m02_salida.txt`.
- `cloud_mask_bt_k` = 0,0 se lee de `thresholds:` (no es el caso A89 de una clave en la sección equivocada). Vara: `git show 66961f65d:pipeline/profile.py | grep -n cloud_mask`.
- En V375, `f5_core_vrp_mw` incluye el píxel de mayor VRP cercano al cúmulo por construcción, así que el patrón de CH162-01 no llega al número publicado de V375. Vara: lectura de `src/f5_core.py` (`peak` sobre `cand` a menos de `inner_km` del centroide).

## SIN DATO

- BT de cada vecino individual y fondo interpolado por MIROVA en las pasadas del 11 y 14-oct (exigen el gránulo).
- Índices fila y columna de los píxeles (para confirmar que VC162-01 es bow tie y no otra cosa).
- Nubosidad real de las noches del 11 y 14-oct: no hay instrumento en los records (máscara apagada, `n_cloud_masked` muerto con umbral 0 y ausente en V750).
- MODIS: el patrón de CH162-01 y VC162-01 podría existir ahí (publica `pc.vrp_mw` con píxel de 1 km), pero el A/B no corre MODIS.
- El motivo por el que falta el record V750 de Chillán del 2026-10-12 05:18.
