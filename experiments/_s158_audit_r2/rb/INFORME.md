# Auditoría S158, segunda ronda, frente RB: lógica de detección e instrumentos

Auditor independiente (no leyó `docs/AUDIT_S158.md`, `experiments/_s158_audit/`, `_s158_oraculo_mirova/`,
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` ni veredictos del A/B de D25). Todo número sale de un script de esta
carpeta con su salida `.txt` al lado. Worktree: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2`
(rama `claude/s158-audit-r2-0eeee2`, HEAD `e81bfadd5`). Flags efectivos leídos de `pipeline.profile` con
`VRP_PROFILE=mirova_equivalent` (`01_flags_efectivos.txt`). Fecha de los datos de producción: `data/mirova_equivalent`
al 2026-10-21 06:48 UTC (último record VIIRS 750).

Convenciones comprobadas (A48): Counter de sensores en los 11 Tier A, 71.968 records: `MODIS_TERRA` 7.186,
`MODIS_AQUA` 7.379, `VIIRS_SNPP` 9.515, `VIIRS_NOAA20` 9.733, `VIIRS_NOAA21` 9.574 (375 m) y `*_750` 9.421 / 9.637 /
9.523 (`01_sustrato_v750.txt`). En la referencia de MIROVA, `Sensor = 'VIIRS'` es VIIRS 750 y `'VIIRS375'` es 375
(`scripts/referencia_mirova_unificada.normalize_sensor`, verificado en `06_chillan_v750_diurno.txt` línea 2).

Sobre el código de MIROVA (`experiments/_s158_d17_diseno/osf_codigo_mirova/`): la matriz de ejemplo dice que
**`BOX == 2` es el centro** (7 x 7 píxeles alrededor de (33, 33), 49 píxeles, radio máximo 3,2 km) y **`BOX == 1` es
el anillo** (350 píxeles, de 3,0 a 10,7 km) y `BOX == 0` lo de afuera (`00_box_mat.txt`). Los comentarios del `.m`
(l. 111 a 118) lo rotulan al revés. Así que en el `.m` los umbrales «ROI2» (noche: 5 sigma, mínimo dNTI 0,003,
mínimo dETI 0,003; l. 181, 184, 187) son los de la **cumbre**, y los «ROI1» (10 sigma, 0,02, 0,01; l. 180, 183, 186)
son los del anillo **y también de BOX 0** (l. 389 a 395). Todo lo que sigue usa esa lectura.

---

## Veredictos por afirmación

| # | Afirmación | Veredicto |
|---|---|---|
| 1 | La compuerta `bt > t_bg + 3 K` del primer pase y el segundo pase están acoplados en VIIRS 750 | **CON MATIZ**: el segundo pase no depende de que el primero haya dejado píxeles (corre siempre), pero deshace la compuerta: lo que ella bloquea en el primer pase sale por el segundo, que no la tiene. Confirmado en sintético; en producción el sustrato existe (1.257 de 28.581 records) pero no se puede atribuir a la compuerta con los campos persistidos |
| 2 | El código de MIROVA corre el segundo pase siempre y sobre toda la escena | **CONFIRMADA**, con precisión de qué es «toda la escena» y cuatro diferencias con el nuestro |
| 3 | Cero gránulos en una búsqueda se registra como «Cobertura: completa» | **CONFIRMADA** (reproducido sin red y encontrado en el log real del A/B) |
| 4 | Al A/B de D25 (run 39530508296) le falta el 2026-10-18 | **CONFIRMADA**, y falta más: también el 2026-10-13 entero y parte del 2026-10-12 (152 pasadas VIIRS de producción, 3,19 %) |
| 5 | La métrica M del evaluador de D25 da MEJORA con un placebo de ganancia constante | **CONFIRMADA para la regla M**; **CON MATIZ para el evaluador entero**: con la calibración sellada el placebo queda INDECIDIBLE; con la calibración de la adenda (propuesta, sin sello) el placebo pasa como MEJORA en 4 de 4 estratos |
| 6 | Rechazamos todo VIIRS 750 diurno y se perdieron alertas protegidas de Chillán | **CONFIRMADA**: 3 de 3 alertas protegidas diurnas de VIIRS 750 en Chillán sin record nuestro (y 9 de 9 en VIIRS 375); el `.m` procesa de día con otros umbrales y sólo rechaza por sun-glint |

---

## Afirmación 1. Compuerta de BT del primer pase y segundo pase (VIIRS 750)

**Qué dice el código (leído).**

- `pipeline/process_viirs_mod.py:882-903` llama a `first_pass_tests_2_and_3` **sin pasar `apply_bt_gate`**, así que
  rige el default `apply_bt_gate=True` (`pipeline/detection_context.py:437`) y la compuerta
  `gate_bt = bt > t_bg + bt_sanity_k` (`detection_context.py:546`, `NTI_BT_SANITY_K = 3.0`) entra en el AND final
  (l. 547 a 552). El flag `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 = False` es sólo de 375 y no toca a este procesador.
- `process_viirs_mod.py:911-951` llama a `second_pass_adjacent` con `active_mask=hot_mask_2d` (la salida del primer
  pase), `conditioned=ENABLE_SECOND_PASS_CONDITIONED` (**False** en producción) y `use_prose_branch=True`.
  `second_pass_adjacent` (`detection_context.py:822-967`) **no tiene compuerta de BT**: el píxel nuevo sólo exige
  Tests 2 y 3 y dNTI/dETI finitos (l. 958-959), y con `conditioned=False` no se restringe a la vecindad de lo ya
  detectado (l. 964-965) ni se salta cuando no hubo primer pase (l. 906-907).
- El bloque «ETI path» de `process_viirs_mod.py:801-833` sí aplica la compuerta DESPUÉS del segundo pase (l. 831-833),
  pero su resultado se pisa en la l. 904 (`hot_mask_2d = fp_hot`) cuando `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True`
  (lo es): sólo sobrevive como `diag_n_eti_path`.

**Qué significa «acoplados» acá.** Dos sentidos, con respuestas distintas:
(a) ¿El segundo pase sólo corre o sólo recaptura si el primero dejó píxeles? **No**: corre siempre
(`conditioned=False`), con máscara activa vacía inclusive. (b) ¿La compuerta del primero cambia lo que hace el
segundo? **Sí, y en la dirección contraria a su propósito**: el píxel que la compuerta rechaza no entra a la
máscara activa, por lo tanto (i) sigue dentro del fondo con que el segundo pase calcula mu y sigma y la media de 8
vecinos, y (ii) el segundo pase, que no tiene compuerta, lo captura si pasa los Tests 2 y 3. El resultado neto es
que la compuerta sólo cambia por cuál pase sale el píxel, no si sale.

**Control positivo sintético** (`01_sintetico_compuerta_segundo_pase.py`, salida `.txt`): escena de 101 x 101
píxeles de 750 m a 270 K, ROI de 50 x 50 km, `inner_radius_km = 5`, llamando a las dos funciones exactamente como
el procesador y con los flags del perfil.

| caso | bump MIR | compuerta (bt > t_bg + 3) | primer pase | segundo pase (producción) | segundo pase `conditioned=True` |
|---|---|---|---|---|---|
| A, píxel de cumbre | +2,0 K | **falla** (272,15 contra 273,01) | 0 píxeles | **1 píxel (el objetivo), nuevo** | 0 |
| A', misma escena, `apply_bt_gate=False` | +2,0 K | falla | 1 (objetivo) | 1 | 1 |
| B, control positivo | +6,0 K | pasa | 1 (objetivo) | 1 | 1 |
| C, mismo bump a 15 km (umbral scene 0,01) | +2,0 K | falla | 0 | 0 | 0 |
| D, mismo bump a 30 km, fuera del ROI | +2,0 K | falla | 0 | 0 | 0 |
| E, nulo sin bump | 0 | falla | 0 | 0 | 0 |

Lectura física: un píxel de cumbre con 2 K de exceso en MIR y TIR frío (lava sub-píxel) tiene dNTI 0,0072 contra un
umbral de cumbre `max(0,003; mu + 5 sigma) = 0,0031`: pasa los tests y lo detiene sólo la compuerta; el segundo pase
lo publica igual. El caso A' muestra que la compuerta es lo único que separa A de la detección en el primer pase.
Con `conditioned=True` (paper, apagado en producción) el píxel no sale: la compuerta sí decidiría.

**Sustrato en producción** (`01_sustrato_v750.py`, `01b`, `01c`; denominador: 28.581 records VIIRS 750 de los 11
Tier A, 2025-02-15 a 2026-10-21; desde 2026-09-18, datos con K: 1.553):

- Records con detección que existe **sólo por el segundo pase** (`diag_n_first_pass_pixels == 0` y
  `diag_n_second_pass_recapture > 0`): **1.257 de 28.581 (4,4 %)**; desde 2026-09-18, **53 de 1.553 (3,4 %)**.
  1.152 de los 1.257 son de un píxel. Por volcán (todo el corpus): Isluga 358, Láscar 303, PCC 260, Tupungatito
  220, PP 51, Chaitén 25, Lastarria 18, Villarrica 12, NdC 8, Llaima 2, Copahue 0.
- De esos, **643 (51,2 %) quedan `summit` con `pc.vrp_mw > 0`** (lo que el tablero puede mostrar; mediana 0,155 MW,
  máximo 0,572); desde 2026-09-18, 19 de 53 (35,8 %).
- En píxeles, la recaptura aporta el **49,7 %** de los píxeles alertados de VIIRS 750 (1.871 contra 1.895 del
  primer pase).
- **Lo que no se puede decir**: en 1.255 de esos 1.257 records `t_max_k - t_bg_k > 3 K`, o sea que el píxel más
  caliente del ROI pasaba la compuerta; como el record no guarda el BT del píxel recapturado ni por qué falló el
  primer pase, no se puede atribuir el «primer pase = 0» a la compuerta (puede ser ella sobre otro píxel, o la
  diferencia de pool de mu y sigma entre pases). Atribución en datos reales: **SIN DATO**; haría falta el gránulo.

**Hallazgo RB-1. El segundo pase sin compuerta ni condición anula la compuerta de BT del primer pase.**
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:546` (compuerta, primer pase); `:906-907`, `:958-967` (segundo pase
  sin compuerta ni vecindad con `conditioned=False`); `pipeline/process_viirs_mod.py:911-951` (llamada).
- QUÉ PASA: la compuerta pretende que un píxel «caliente por contraste» tenga además MIR sobre el anillo; como el
  segundo pase corre siempre, sobre todo el ROI y sin esa condición, un píxel de contraste con MIR tibio sale
  igual, y además sigue contaminando el fondo del segundo pase porque no fue marcado activo.
- CÓMO SE VE EN EL DASHBOARD: igual que una detección del primer pase; no hay marca que distinga una publicación
  que sólo pasó por el segundo pase (643 records `summit` con magnitud en el corpus).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/rb/01_sintetico_compuerta_segundo_pase.py` (caso A).
- CONFIANZA: CONFIRMADO en sintético; el peso en producción es SOSPECHA (1.257 records candidatos, sin
  atribución).
- GRAVEDAD: 2. Es una incoherencia de diseño (D22 ya discute que el paper no tiene compuerta): si la compuerta
  está mal, hoy no hace daño porque el segundo pase la deshace; si la compuerta está bien, hoy no protege.

---

## Afirmación 2. Segundo pase en el código de MIROVA

**CONFIRMADA.** `MIROVA_VIIRS750_hotspot_detection.m:228-235`: la segunda llamada a `contextualDetectionPass` no
está condicionada a que la primera haya devuelto algo (no hay `if` entre l. 220 y 228), y dentro de
`contextualDetectionPass` no hay restricción de vecindad: los alertas salen de `find(...)` sobre toda la matriz
enmascarada por dominio (l. 389 a 399).

**Qué es «toda la escena» en el `.m`:** la matriz de entrada (67 x 67 en el ejemplo; `00_box_mat.txt`), menos:
(1) el marco de 1 píxel (`BOX(:,[1 end]) = NaN; BOX([1 end],:) = NaN`, l. 102-103); (2) los NaN de `BOX`
(`excludedPixels`, l. 140); (3) TIR <= 200 K (l. 151-154). Los tres dominios se testean, incluido **BOX 0** (lo de
afuera de los dos ROI), con los umbrales del anillo (l. 389-391). Las estadísticas (media y desviación de los
contrastes) salen de **toda la escena** (l. 303-304, 373-374), con los alertas absolutos y los del primer pase
puestos a NaN (l. 275-277) y con `contraste < -0,1` puesto a NaN (l. 298). El ajuste espectral (polyfit, l. 343-345)
se **rehace** en el segundo pase sobre la población sin alertas.

**Lo que hace el nuestro** (`detection_context.py:822-967`, llamado desde `process_viirs_mod.py:932`): corre
siempre (`conditioned=False`), sobre el ROI de 50 x 50 km (`roi_mask_bbox(..., radius_km)`,
`process_viirs_mod.py:538`): fuera del ROI `compute_eti_scene_quadratic` deja ETI en NaN (`detection_context.py:795`)
y el segundo pase exige dETI finito, así que el dominio efectivo es el ROI. Cuatro diferencias leídas, ninguna
medida en su efecto (fuera del alcance arreglarlas):

| punto | `.m` de MIROVA | nuestro segundo pase |
|---|---|---|
| ETI del segundo pase | se reajusta excluyendo los alertas del primero (l. 275-277, 343-345) | reusa el ETI del primer pase (`process_viirs_mod.py:916`, `fp_diag["eti"]`) |
| pool de mu y sigma | toda la escena, sin contrastes < -0,1, sin marco | ROI, `~active & finito` (`detection_context.py:923`): sin el piso -0,1 y sin el marco que el primer pase sí aplica (`build_unsuitable_mask`) |
| píxeles ya alertados | quedan NaN (no se re-testean, no entran al fondo) | se excluyen de la media de vecinos (l. 910-911) y del pool (l. 923); su dNTI propio se calcula igual pero el OR final los conserva |
| mínimo de dNTI fuera de la cumbre, noche | **0,02** (`minimumNTIcontrastROI1`, l. 183, aplica a anillo y BOX 0) | **0,010** (`DNTI_CONTEXTUAL_C1_SCENE`) |

La última fila no es del segundo pase en particular (rige en los dos pases) y queda anotada en «Fuera de alcance».

CONFIANZA: CONFIRMADO (lectura del `.m` y del nuestro). GRAVEDAD de las diferencias: no medida.

---

## Afirmación 3. Cero gránulos se registra como «Cobertura: completa»

**CONFIRMADA.** Camino leído: `pipeline/fetch.py:734-800` (`search_granules`) devuelve `[]` en la l. 800 cuando
ninguna versión (standard ni NRT) trae resultados, **sin llamar a `_registrar_falla`**; `fetch_for_volcano`
(`fetch.py:1083-1086`) hace `if not l1b_granules: continue`, que tampoco registra nada. En la búsqueda por ventana
(`_buscar_ventana`, l. 650-668) un día sin gránulos termina en `resultado[d] = []` (l. 666-667), también sin falla.
`scripts/run_pipeline.py:416-418` imprime «Cobertura: completa» y devuelve 0 cuando `fallas` está vacía, aun con
`--estricto-cobertura`. En cambio un `Timeout`/`ConnectionError` de CMR sí se registra: con el breaker encendido
(`ENABLE_CMR_SEARCH_BREAKER = True`, valor en `fetch`) en `fetch.py:783-788`, y con el breaker apagado por el
`except Exception` de `fetch.py:1125-1128`.

**Reproducción sin red** (`03_cero_granulos_cobertura.py`, parche de `earthaccess.search_data`; Chaitén,
2026-10-18, sólo VIIRS):

| caso | fallas registradas | `informar_cobertura(estricto=True)` |
|---|---|---|
| (a) 0 gránulos en las 18 consultas (6 plataformas x versiones) | **0** | «Cobertura: completa», código **0** |
| (b) control positivo: `ReadTimeout`, breaker ON (producción) | 6 | «Cobertura INCOMPLETA», código 3 |
| (c) `ReadTimeout`, breaker OFF | 6 | INCOMPLETA, código 3 |
| (d) búsqueda por ventana con 0 gránulos para el día | **0** | «completa», código 0 |

**En el mundo real** (log del brazo control del A/B, Chaitén, `04_log_control_chaiten.txt`, l. 3688-3727 y
4108-4131): el 2026-10-13 las seis búsquedas VIIRS dieron `n_l1b=0` y el 2026-10-18 las ocho (MODIS incluido) dieron
`n_l1b=0`; las dos veces el job imprimió «Cobertura: completa» y terminó «Done.» con `--estricto-cobertura`
(`reproc-s146-ab-sin-test1.yml:191` de la rama). Producción sí tiene records esos días (ver afirmación 4).

**Hallazgo RB-2. Una búsqueda vacía es invisible para la cobertura.**
- ARCHIVO:LÍNEA: `pipeline/fetch.py:800` y `:1085-1086`; `scripts/run_pipeline.py:416-418`.
- QUÉ PASA: «CMR no tiene nada para este día» y «CMR tiene pasadas pero no las devolvió» (índice atrasado, LANCE
  aún no publicó, ventana que se repartió mal) se ven idénticos: lista vacía, sin falla, cobertura completa.
- CÓMO SE VE EN EL DASHBOARD: invisible; el día queda sin records y nadie lo marca. En el NRT la corrida siguiente
  vuelve a intentar (dos días recientes fuera de la ventana, `fetch.py:521-526`), en un reproceso o A/B no.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/rb/03_cero_granulos_cobertura.py`; y el log real citado.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 para reprocesos y A/B (un brazo puede quedar corto y el control de «cobertura pareja» entre brazos
  no lo ve, porque todos los brazos pierden lo mismo); 2 para el NRT (la corrida siguiente lo levanta).

---

## Afirmación 4. Fechas del A/B de D25 (run 39530508296)

**CONFIRMADA, y falta más que el 18.** Rama `origin/s146-ab/39530508296`, commit `4b6d7f5f2` (2026-10-21 09:11 UTC),
brazos `_s157_ab_d25_k_control`, `_s157_ab_d25_k_gemelo`, `_s157_ab_d25_k_on`, 11 volcanes, leídos con `git show`
(`04_fechas_ab_d25.py`, salida `.txt`). Ventana V1 del pre-registro: 2026-08-29 a 2026-10-18 (51 días,
`PREREGISTRO.md:104`).

- Los tres brazos traen **4.610 records cada uno**, todos dentro de V1, **49 días distintos**; sólo sensores VIIRS
  (375 y 750; MODIS 0, como declara el pre-registro). Conteo por día idéntico entre brazos en los 11 volcanes
  (0 diferencias): la «cobertura pareja» del run es verdadera entre brazos.
- Días de V1 **sin ningún record en ningún volcán ni brazo: 2026-10-13 y 2026-10-18**. Última pasada de cada
  sensor: 2026-10-17 05:24 a 06:24 UTC.
- Contra producción (`04b_control_vs_produccion.py`; clave = volcán, sensor, `datetime_utc`): producción tiene
  **4.762** pasadas VIIRS en V1 y al control le **faltan 152 (3,19 %)**, 0 sobran. Por día: 2026-10-12, 22 de 375 y
  22 de 750; 2026-10-13, 11 y 11; 2026-10-18, 43 y 43. Por volcán faltan entre 12 (Láscar, Lastarria) y 16 (PP).
- Mecanismo (log del control, `04_log_control_chaiten.txt`): el trozo 2026-09-30..10-15 se consultó por ventana el
  2026-10-21 07:56 UTC y la versión NRT para 10-12..10-13 dio `n=0` (l. 2700); el trozo 10-16..10-18 dio `n=5` en
  standard y `n=0` en NRT para el 18 (l. 3972-3973). El 18 de octubre a las 08:23 UTC del 21 ya no estaba en LANCE
  y todavía no estaba en LAADS para esa consulta; la cobertura lo registró como completa (afirmación 3).
- Nota: 3,19 % queda **bajo el 5 %** que el evaluador usa como tope de cobertura (`evaluar_d25.py:66`), así que el
  evaluador no lo marcaría INDECIDIBLE por esto. No calculé ninguna métrica ni abrí veredictos.

CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (Chillán tiene protegidas el 2026-10-18, ver afirmación 6, que el A/B no vio).

---

## Afirmación 5. Placebo de ganancia constante en la métrica M

**Qué es M** (`experiments/_s157_prereg_d25/evaluar_d25.py:159-160`): por par (K y D publican, MIROVA tiene VRP),
`d = |log10(D/M)| - |log10(K/M)|`; `regla_m` (l. 152-156): mediana de `d` con bootstrap por bloques noche-volcán
(10.000 réplicas, semilla 157; l. 120-149) y **MEJORA si el IC95 queda entero bajo 0**. Después (l. 399-414) el
estrato queda INDECIDIBLE si la calibración falla: la **sellada** (`calibrar`, l. 163-184, default `CALIB_MODO =
"sellada"`) sortea por bloque el signo de `e = |log10(D/K)|` y exige falsos MEJORA + EMPEORA <= 5 % de 200; la
**simétrica** (`calibrar_simetrico`, l. 187-199, adenda, «requiere el sello de Nicolás», l. 493) sortea el signo de
`d` y mide cada cola por separado, más la condición de 2 volcanes con mediana negativa (l. 411-412).

**Por qué un placebo da MEJORA:** `d` sólo mira la distancia a MIROVA. Si K está sistemáticamente por debajo de
MIROVA (lo está: razón mediana K/MIROVA 0,41 en VIIRS 750 V1, 0,55 en V2, 0,61 y 0,67 en VIIRS 375), cualquier
`D = g K` con `1 < g < (M/K)^2` acerca a MIROVA en cada par, sin ningún mecanismo físico. M no distingue «arreglé
el fondo» de «multipliqué por 1,2».

**Medición** (`05_placebo_metrica_m.py`, salida `.txt`; funciones copiadas verbatim del evaluador, pares reales de
producción contra `latest_consolidado.csv` + OCR, pasadas nocturnas, `summit`, `pc.vrp_mw > 0` o `f5_core_vrp_mw`
en 375, pareo +-120 s; **ningún dato del A/B**):

| ventana, sensor | n pares (noches) | razón K/M | g = 1,0 (control) | g = 1,2 | g = 0,8 | sellada con g = 1,2 | simétrica con g = 1,2 |
|---|---|---|---|---|---|---|---|
| V1 VIIRS 750 | 50 (29) | 0,405 | NEUTRO, IC [0, 0] | **MEJORA** [-0,079, -0,079] | EMPEORA | falsos 1,5 % + 4,5 % = 6,0 % -> INDECIDIBLE | 2,5 % y 3,5 %, 3 volcanes -> **MEJORA** |
| V1 VIIRS 375 | 294 (164) | 0,610 | NEUTRO | **MEJORA** | EMPEORA | 19,5 % -> INDECIDIBLE | 5,0 % y 3,0 % -> **MEJORA** |
| V2 VIIRS 750 | 102 (78) | 0,547 | NEUTRO | **MEJORA** | EMPEORA | 13,0 % -> INDECIDIBLE | 0,5 % y 2,5 % -> **MEJORA** |
| V2 VIIRS 375 | 553 (329) | 0,669 | NEUTRO | **MEJORA** | EMPEORA | 49,5 % -> INDECIDIBLE | 2,0 % y 2,5 % -> **MEJORA** |

Con jitter lognormal por par (sigma 0,05 en log10) el cuadro no cambia; con sigma 0,15 la regla pasa a NEUTRO en
VIIRS 375 (el ruido tapa 0,079) y sigue MEJORA en VIIRS 750. El control g = 1,0 da `d = 0` en todos los pares, IC
[0, 0], NEUTRO, y la calibración sellada no tiene nada que sortear (falsos 0 %, poder False): el instrumento
distingue «sin cambio».

**Veredicto.** La afirmación es CONFIRMADA para `regla_m`: una ganancia constante de 1,2 da MEJORA en los 4
estratos, con IC degenerado [-0,079, -0,079] (el bootstrap de una constante). Para el evaluador entero depende de
la calibración: la sellada (vigente) lo frena como MAL CALIBRADA en los 4 estratos (porque el nulo con signo por
bloque de una constante es bimodal y cae en EMPEORA con frecuencia); la simétrica de la adenda **lo deja pasar en 4
de 4**. Si Nicolás sella la adenda, el evaluador no distingue D25 de un factor 1,2.

**Hallazgo RB-3. M mide sesgo de magnitud, no mecanismo; la calibración de la adenda no lo frena.**
- SCRIPT:SALIDA: `05_placebo_metrica_m.py` : `05_placebo_metrica_m.txt`.
- QUÉ PASA: ver arriba. Un brazo que sube la magnitud de VIIRS 750 por cualquier causa (D25 o un coeficiente)
  recibe MEJORA mientras K esté bajo MIROVA. Además el IC95 de una constante es un punto: la regla no mide
  variabilidad del efecto, sólo su signo mayoritario.
- CÓMO SE VE EN EL DASHBOARD: invisible (es del instrumento de decisión).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/rb/05_placebo_metrica_m.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (decide una adopción en `pipeline/`; el veto P1 y la suma P2 siguen vigilando pérdidas, pero M es
  el único criterio de magnitud y no tiene control de mecanismo).

Matiz importante: mi pareo aproxima el predicado del tablero (`summit` y magnitud > 0) y no lo ejecuta con node
(A97), y mi «D» no es el brazo D del A/B. Lo que mido es la respuesta de la regla a una ganancia, no el A/B.

---

## Afirmación 6. Rechazo del VIIRS 750 diurno y Chillán

**Dónde y cómo se rechaza (leído).** Tres compuertas, todas con la misma definición de «diurno»: elevación solar
en el volcán a la hora de la pasada **> 0 grados**, por la fórmula de `pipeline/store.py:188-200`
(`_solar_elevation`; `fetch.py:151-163` y `run_pipeline.py:92` son copias).
1. Antes de bajar: `fetch.py:1090-1101`, `_filter_nighttime_granules` conserva sólo `elev < 0` (l. 1018), salvo que
   `aplica_filtro_nocturno` diga que no (`diurno.py:96-102`: VIIRS se libera sólo con `ENABLE_DAYTIME_VIIRS`).
2. Antes de procesar: `run_pipeline.py:184-196` (`_check_night`, salta si no es noche).
3. Al guardar: `store.py:636-645` llama a `_reject_daytime` (l. 203-223): con `solar_elev > 0` y
   `ENABLE_DAYTIME_VIIRS = False` (perfil, `01_flags_efectivos.txt`) el record **no se guarda**.
Es decir: hoy no se baja, no se procesa y no se guarda ninguna pasada VIIRS (375 ni 750) con el Sol sobre el
horizonte. El umbral es 0 grados de elevación, sin crepúsculo ni sun-glint.

**Qué hace el `.m` de día.** No rechaza: con `dayflag ~= 0` cambia los umbrales (l. 188-199: NTI absoluto -0,5 en
vez de -0,7; 15 sigma en los dos ROI; mínimos 0,02 en todo) y el algoritmo es «idéntico de día y de noche»
(l. 174-176). El único rechazo de escena es **sun-glint < 12 grados** (l. 83-89), calculado con geometría solar y
del satélite (`run_example.m:14-19`). Y MIROVA publica VIIRS 750 diurno en su propio archivo: en el OSF 2025, para
los volcanes chilenos que el nombre encuentra (PCC, Lastarria, Villarrica, Isluga, Copahue, Llaima), **107 de 1.210
filas de VIIRS 750 son diurnas** (`Dayflag = 1`; 67 de Villarrica, 35 de Copahue), todas de 5 MW o más porque el
OSF está filtrado (A105); globalmente 38.297 filas diurnas de 615.470 (`06b_osf_v750_diurno.txt`).

**Conteo en Chillán** (`06_chillan_v750_diurno.py`; referencia `latest_consolidado.csv` 42.297 filas + OCR 1.120;
NdC: 1.446 filas de tabla y 17 de OCR en VIIRS 750; pasada = (bucket, minuto); protegida = alguna fila
`ALERTA_TERMICA` o `ALERTA_TERMICA_OCR` con VRP >= 1 MW, lectura A, `clase_mirova.py:65`; diurna por la fórmula de
`store.py` en (-36,863; -71,377); «record nuestro» = record VIIRS 750 en `data/mirova_equivalent/NevadosDeChillan.json`
a +-120 s). A119: la ventana que decide empieza en marzo; se informan tres ventanas y el resultado es el mismo:

| ventana | pasadas 750 ref. noche / día | protegidas de noche (sin record nuestro) | protegidas de **día** (sin record nuestro) |
|---|---|---|---|
| 2026-01-10 a 2026-10-21 | 701 / 754 | 30 (0) | **3 (3)** |
| 2026-03-01 a 2026-10-21 | 617 / 635 | 30 (0) | 3 (3) |
| V1 2026-08-29 a 2026-10-18 | 163 / 141 | 30 (0) | 3 (3) |

Las tres: 2026-10-01 18:42 UTC (3,71 MW, elev. solar 46,8), 2026-10-10 18:18 (3,33 MW, 53,0) y 2026-10-18 19:06
(2,49 MW, 48,1), todas `ALERTA_TERMICA` de la tabla. En VIIRS 375 son **9 de 9** protegidas diurnas sin record
(de 6,46 a 15,81 MW, entre el 2026-10-01 y el 2026-10-18), con 32 de 32 nocturnas con record. Control del
instrumento: las pasadas de la referencia clasificadas de día caen a las 17 a 20 UTC y las de noche a las 4 a 7 UTC;
nuestros 2.674 records de VIIRS 750 de Chillán están todos entre las 4 y las 7 UTC (ninguno diurno).

**Veredicto: CONFIRMADA.** Denominador: 33 protegidas de VIIRS 750 en Chillán en toda la referencia, 3 diurnas,
las 3 sin record (y las 30 nocturnas con record). Si MIROVA las publica con umbrales diurnos y sun-glint, hoy la
réplica no puede verlas por construcción (compuerta 1: ni se bajan).

**Hallazgo RB-4. Chillán en erupción tiene 3 alertas protegidas diurnas de VIIRS 750 (y 9 de VIIRS 375) que la
réplica no puede producir.**
- ARCHIVO:LÍNEA: `pipeline/fetch.py:1018`, `scripts/run_pipeline.py:192`, `pipeline/store.py:218-223`.
- QUÉ PASA: de día el reflejo solar entra al MIR y MIROVA lo compensa subiendo umbrales y rechazando sun-glint
  bajo 12 grados; nosotros rechazamos todo. En una erupción con lava expuesta (Chillán desde el 28-sep) el día
  tiene señal de MW que de noche también se ve, pero la pasada diurna existe en MIROVA y no en el tablero.
- CÓMO SE VE EN EL DASHBOARD: una alerta de MIROVA a las 15 h de Chile sin punto nuestro; el operador que compare
  ve «MIROVA sí, VRP Chile no» tres veces en octubre en VIIRS 750.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/rb/06_chillan_v750_diurno.py`.
- CONFIANZA: CONFIRMADO (conteo); que esas 3 sean señal volcánica y no artefacto solar es SOSPECHA (A76: MIROVA
  publica artefactos diurnos; pero las 3 vienen de la tabla `latest.php`, no del OCR, y están entre 2,5 y 3,7 MW
  en una erupción en curso).
- GRAVEDAD: 3 (recall de protegidas, lectura A, en el volcán que hoy está en erupción); la decisión de abrir el
  diurno ya existe como flag (`ENABLE_DAYTIME_VIIRS`, D-10) y es de Nicolás.

---

## Fuera de alcance (anotado, no medido)

- **Mínimo de dNTI fuera de la cumbre**: el `.m` usa 0,02 (anillo y BOX 0, l. 183) y nosotros 0,010
  (`DNTI_CONTEXTUAL_C1_SCENE`), de noche. Afecta a los dos pases. SOSPECHA de sobre-publicación en `far`.
- **Etiquetas de ROI invertidas en los comentarios del `.m`** (l. 111-118 contra la matriz de ejemplo): quien lea el
  comentario y no la matriz pone los umbrales de cumbre en el anillo. CONFIRMADO con `00_box_mat.txt`.
- **Pool de mu y sigma del segundo pase** sin el piso -0,1 ni el marco (afirmación 2, tabla): el primer pase sí
  los aplica (`build_unsuitable_mask`). Diferencia entre pases nuestra, no de MIROVA.
- **El A/B perdió parte del 2026-10-12** además del 13 y el 18 (afirmación 4). Las tres fechas tienen records en
  producción porque el NRT las levantó en corridas posteriores; el A/B consultó el 2026-10-21 y LANCE ya no las
  tenía ni LAADS todavía. Un reproceso que corra con más de 7 a 14 días de retraso pisa esa grieta.
- **La búsqueda de nombres chilenos en el OSF** no encontró Láscar, Chaitén, Tupungatito, Chillán ni Planchón (acentos
  o grafía distinta en `Volc_Name`); el conteo diurno de 107 es un piso.

---

## VERIFICADO LIMPIO

- **El segundo pase sí corre siempre y el flag se lee del perfil**: `ENABLE_SECOND_PASS_ADJACENT = True`,
  `ENABLE_SECOND_PASS_CONDITIONED = False`, `ENABLE_DUAL_ROI_SECOND_PASS = True`, `ENABLE_TESTS_23_PROSE_BRANCH =
  True`, `NTI_BT_SANITY_K = 3.0`, `ENABLE_DAYTIME_VIIRS = False`, `ENABLE_TEST1_PATH = False`
  (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`, `01_flags_efectivos.txt`).
- **Los campos de diagnóstico del segundo pase existen en los 28.581 records VIIRS 750** (`sin_campo = 0`,
  `01_sustrato_v750.txt`), y la recaptura no es un contador muerto (1.648 records con recaptura > 0).
- **El registro de fallas de cobertura funciona para timeouts** (casos b y c de `03_cero_granulos_cobertura.txt`:
  6 fallas, código 3): lo roto es sólo el caso «lista vacía».
- **Los tres brazos del A/B tienen exactamente las mismas pasadas entre sí** (0 diferencias de conteo por día en
  11 volcanes, `04_fechas_ab_d25.txt`) y 0 records fuera de V1 ni de MODIS.
- **Control g = 1,0 de M**: `d = 0` en todos los pares, NEUTRO, calibración 0 % (`05_placebo_metrica_m.txt`).
- **Pareo nocturno de Chillán**: 30 de 30 protegidas nocturnas de VIIRS 750 y 32 de 32 de VIIRS 375 tienen record
  nuestro a +-120 s; ningún record nuestro de VIIRS 750 de Chillán es diurno (`06_chillan_v750_diurno.txt`).
- **Convención de sensores** (A48): verificada con Counter antes de clasificar; `VIIRS` del CSV = 750.
- **Las tres compuertas diurnas usan la misma fórmula de elevación solar** (`store.py:188`, `fetch.py:151`,
  `run_pipeline.py:92`, leídas): no hay una pasada que una acepte y otra rechace por fórmula distinta (la única
  asimetría es `elev == 0` exacto: fetch la descarta, store la guarda; sin efecto práctico).

## Lo que no pude medir

- **Atribuir a la compuerta el «primer pase = 0» en los 1.257 records reales**: el record no guarda el BT del píxel
  recapturado; `t_max_k - t_bg_k > 3` en 1.255 de ellos dice que el píxel más caliente pasaba, no que el
  recapturado pasara. Hace falta reprocesar gránulos con un probe por etapa (A75); no descargué gránulos (límite
  del encargo).
- **El efecto de las cuatro diferencias del segundo pase contra el `.m`** (ETI sin reajustar, pool, píxeles
  alertados, mínimo 0,02): leídas, no medidas; pide correr el `.m` o un oráculo, que quedó excluido de mi alcance.
- **El predicado del tablero con node** para los pares de M y para «visible» en la afirmación 1: usé `summit` y
  magnitud > 0 como aproximación.
- **Si las 3 protegidas diurnas de Chillán son señal o artefacto solar**: no hay gránulo diurno en disco (nunca se
  baja) y no bajé ninguno.
- **La razón exacta por la que CMR devolvió 0 el 12, 13 y 18 de octubre en el A/B**: el log muestra el `n=0`, no la
  respuesta de CMR; la hipótesis LANCE expirado y LAADS no publicado es SOSPECHA coherente con las fechas.
