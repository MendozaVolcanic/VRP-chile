# Verificador del INFORME.md del run 40945613044 (sombra del código MIROVA, Láscar, medir=true)

Verificador con contexto limpio, S168, 2026-10-29. Recibió sólo la carpeta, el run y el código del tag `s167-sombra-medir`
(`9533f00de`, sin diferencias con `origin/main` en `scripts/run_pipeline.py`, `scripts/revisar_sombra.py`,
`pipeline/mirova_v750_codigo.py`, `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`, `pipeline/process_modis.py`,
comprobado con `git diff --stat 9533f00de origin/main -- <archivo>`, salida vacía). La referencia de MIROVA la rebajé yo
a un directorio temporal del scratch; su md5 (`4ecbe2c36def1fe0efb7cac4c20f87fb`) es idéntico al CSV de la carpeta.

**Veredicto: CONFIRMADO CON RESERVAS.** Los conteos y los tiempos salen de los datos. Hay un error de premisa en el costo
(hallazgo 1, gravedad 3), y dos lecturas del informe que el log no sostiene tan limpiamente como dice (hallazgos 2 y 3).

## Lo que se confirma

- **Conteos por sensor.** Por mi cuenta, sin `contar.py`: sumé por bloque de día las líneas «kept N of M» y las líneas de
  record. Records: MODIS 17 (Terra 8, Aqua 9), VIIRS 750 32 (N20 12, SNPP 11, N21 9), VIIRS 375 28 (N20 10, SNPP 9, N21 9),
  total 77. Coincide con el informe. `contar.py` corrido contra mi copia de la referencia reproduce `salida.txt` byte a byte
  (`diff` vacío).
- **Log ciego de VIIRS 375.** Cierto. El dict del record de la vía (`pipeline/mirova_v750_codigo.py:704`) trae
  `vrp_mw`, `n_anomalous_pixels`, `t_max_k`, `vrp_vent_mw: 0.0` y no trae `vrp_mir_mw`, `vrp_tir_mw`, `t_max_i04_k` ni
  `n_vent_pixels`. La línea de log (`scripts/run_pipeline.py:324-326`) imprime justo esos campos con `.get`, y en los 28
  casos sale `VRP_MIR=None ... T_max=None K | VRP_VENT=0.0 MW (Nonepx)` (log líneas 589-592, 662-664, etc.). Tracé además
  `store.append_record`: el record de la vía se salta `_filter_pixels_by_distance` (`store.py:357-363`, `_via_mirova`), que es el
  único sitio que escribe `vrp_mir_mw` en el record, así que el almacén tampoco lo rellena. El log no puede mostrar una
  detección de 375 m, haya o no.
- **Tiempos.** `job_lascar.json` da 907 s de job y 801 s del paso del pipeline; 801 / 8 días = 100 s por día. Checkout 68 s
  e instalación 31 s. Coinciden con `tiempos.txt` y con `gh run view 40945613044 --json jobs`.
- **Referencia.** Las 7 alertas de la tabla (6 VIIRS375 de 0,04 a 0,16 MW, 1 MODIS de 0,29 MW) se reproducen; ninguna fila
  `VIIRS` (750) es alerta en la ventana.

## Hallazgos

### 1. El costo diario está mal calculado: el modo normal corre 8 días, no 1 (gravedad 3)

`INFORME.md` §3 dice que «un schedule diario sobre 1 día por volcán costaría del orden de 3 a 4 min de runner por job».
Pero el modo normal del workflow procesa **los 8 días de siempre**: `scripts/ventana_sombra.py:46`
(`return max(minima, hoy - timedelta(days=lookback)), hoy`, con `LOOKBACK_DIAS = 7`, l. 24), y el comentario del workflow lo
dice («la sombra procesa los mismos 8 dias que el NRT»). La corrida medida fue exactamente esa ventana (8 días). O sea que el
costo diario de régimen es el medido, **907 s ≈ 15 min por job, no 3 a 4**.

Cuentas con los datos: 11 jobs × ~15 min ≈ 165 min de runner al día; con `max-parallel: 4` (`sombra-codigo-mirova.yml:55`)
son 3 tandas, unos 45 min de reloj. `experiments/_s167_sombra/COSTO.md` §3 había estimado 20 a 22 min de mediana por job y
37 a 45 el peor: lo medido (15,1 min, 13,4 el paso) quedó por debajo, buena noticia que el informe no dice. En la primera
semana (desde el 2026-11-03) la ventana crece de 1 a 8 días, así que el costo parte bajo.

Matices que el informe tampoco trae: (a) es un solo volcán; Láscar procesó 81 gránulos nocturnos y el único otro job medido,
Copahue en el NRT, 83 (COSTO.md §1), así que no es un caso liviano, pero tampoco se midieron los otros 10; (b) la corrida no
contiene el día en curso: ningún producto `_NRT` aparece en el log (el único «NRT» del log es un comentario del `pip install`,
línea 258), todo vino de LAADS estándar. En régimen, `fin = hoy` y las pasadas de hoy sólo existen en LANCE (A64); su cola de
`ConnectTimeout` no está en esta medición; (c) la frase «lo que pesa es el lock del grupo» no vale para la sombra: tiene
grupo propio (`concurrency: group: sombra-codigo-mirova`) y no compite con `push-main`; lo que sí pesa son los commits.

### 2. 81 gránulos retenidos, 77 records: cuatro gránulos de VIIRS 375 se pierden en silencio (gravedad 2)

Suma de «kept» por sensor: 375 = 32 (N20 12, SNPP 11, N21 9) contra 28 records; 750 = 32 contra 32; MODIS 17 contra 17.
Los cuatro que faltan (N20 del 2026-10-22 y del 2026-10-24, SNPP del 2026-10-22 y del 2026-10-26)
salen por `return None` sin línea de log ni error: `process_viirs.py:773` y `:781` (lectura vacía o `calcular_vrp_granulo` None),
y `run_pipeline.py:310` (`if result:` no imprime nada si es None). `calcular_vrp_granulo` devuelve None cuando el gránulo no
cubre el volcán (menos de 100 píxeles en el recorte, o el píxel más cercano al centro a más de 5 km,
`mirova_v750_codigo.py:804-808`). Ni `revisar_sombra.py` (cuenta sólo records del JSON y líneas `ERROR processing`) ni
«Cobertura: completa» (sólo búsquedas, descargas e incidencias de geolocalización) los ven.

Consulta a CMR (bounding box del pipeline contra punto en el volcán, `cmr.py` en mi scratch): tres de los cuatro son
gránulos que tocan la caja de 25 km pero **no contienen el volcán** (SNPP 2026-10-22 06:00 y 2026-10-26 04:48, N20
2026-10-24 05:42). El cuarto (N20 del 2026-10-22, donde 04:42 y 06:24 contienen el volcán) queda SIN VERIFICAR.

Consecuencia para VIIRS 750: `FAMILIAS["VIIRS750"]` tiene `dist_max_centro_km: None` (`mirova_v750_codigo.py:109`), así que esos
mismos gránulos de borde sí producen record en 750. Los «32 gránulos sin detección» incluyen al menos 3 (probablemente 4) que
no vieron el volcán. Son pasadas distintas de las ~28 que tiene MIROVA. Es consistente con que 750 y 375 difieran en exactamente
esos cuatro días, pero los records no se guardaron, así que es inferencia. En régimen diario, esos records vacíos entrarían al
JSON como «noches sin alerta» sin haber mirado el volcán, y inflarían el denominador de negativos de la sombra.

### 3. Los ceros de MODIS y de VIIRS 750 no se pueden leer como «el detector miró y no vio» (gravedad 2)

Un record vacío de la vía es el mismo en el log sin importar la causa: `procesar_grilla` pone `t_bg_k: None`, `vrp_mw: 0.0`
siempre que `npix == 0` (`mirova_v750_codigo.py:709-714`), y `detectar_mirova` devuelve máscara vacía también por
`motivo = "sunglint"` (l. 414) o `"escena_invalida"` (l. 433, la mitad o más de la caja sin dato). El motivo sólo vive en
`diag_codigo_mirova.motivo_vacio` (l. 706) dentro del JSON, que con `medir=true` se descarta con el runner; el log no lo
imprime. En las 48 líneas vacías de MODIS y 750, nada distingue un cero físico de un cero por escena inválida (lo más probable
en los gránulos de borde del hallazgo 2).

Además la corrida **no tiene poder para VIIRS 750**: MIROVA no tuvo ninguna alerta 750 de Láscar en la ventana, así que 0 contra
0 no prueba sensibilidad. Para MODIS hay un positivo (hallazgo 4). La sensibilidad de la vía ya estaba medida contra MATLAB
fuera de esta corrida (comentario de `mirova_v750_codigo.py`, l. 462: 166 de 166 escenas contra MATLAB), así que no digo que esté rota: digo que esta corrida no
añade evidencia sobre ella. Un fallo silencioso concreto que el log no excluye: si faltaran los ángulos de observación en el
geo, `geom.get(..., 0.0)` da `sunglint = 0°` (<12) y todo sería vacío (`mirova_v750_codigo.py:811-812`, 414). MODIS lo descarta
(detectó), VIIRS 750 y 375 SIN VERIFICAR (los archivos GEO de VIIRS traen esas variables, pero no lo miré en un gránulo).

### 4. La coincidencia MODIS sí es de pasada, no sólo de día: el informe se queda corto (gravedad 1)

El informe dice «SIN DATO» sobre si es la misma pasada. Se puede resolver sin el log: las horas de MIROVA para MODIS son el
inicio del gránulo. CMR (`MYD021KM`, `MOD021KM`, punto en Láscar, 2026-10-21 a 28, noche UTC < 11 h) da **exactamente 17
gránulos nocturnos** (Terra 8, Aqua 9), los mismos 17 del log. 16 de los 17 tienen fila MIROVA a la misma hora y todas son
RUTINA, salvo el Aqua del **2026-10-26 07:55**, que es la `ALERTA_TERMICA` de 0,29 MW. Es además el único gránulo Aqua nocturno de
ese día (el otro, 20:00, es de día y el filtro lo saca: «kept 1 of 2»). El Terra de 01:40 salió vacío en nuestro log y es RUTINA
en MIROVA. El 17.º, Aqua 2026-10-21 08:00, no tiene fila propia (MIROVA tiene la de 08:05). La plataforma se infiere de la hora,
no del log (el log no imprime hora). Magnitudes: 0,184 MW contra 0,29 MW, un píxel; la coincidencia es de presencia, no de valor.

### 5. `salida.txt` rotula como «vacio» a los 28 gránulos de 375 (gravedad 1)

`contar.py` clasifica 375 con `m.group(2) not in ("None","0","0.0")`; como el campo es siempre `None`, todos salen `vacio`
(`salida.txt`: `('VIIRS_NOAA20_375', 'vacio') 10`, etc.). El informe lo explica bien en el texto; la salida cruda, no. Quien lea sólo
`salida.txt` verá 28 vacíos reales.

### 6. La referencia trae más de lo que el informe cuenta (gravedad 1)

(a) Filas `FALSO_POSITIVO` de la tabla en la ventana, no mencionadas: tres nocturnas de VIIRS 375 con magnitudes mayores que las
seis alertas, 10-24 05:24 (0,46 MW, 27,4 km), 10-25 05:24 (0,56 MW, 27,9 km) y 10-26 05:06 (0,60 MW, 23,2 km; la única dentro de
la caja de 25 km). El scraper las etiqueta así por distancia, no por física. (b) De las 6 alertas 375, la de 2026-10-26 05:54 vale
0,04 MW y la regla D-9 de CLAUDE.md las trata como «MIROVA no vio nada» (≤ 0,05 MW). El «6 alertas» sube de peso si se
cuenta con la regla vigente: quedarían 5. (c) Las seis caen en pasadas de NOAA-20 o NOAA-21 (05:24, 05:06, 06:06, 06:12, 05:54,
06:12; hora de gránulo en CMR), y todas esas pasadas sí están entre los gránulos retenidos con record: el JSON de la sombra tenía
la respuesta de 375, y se perdió.

## Lo que no pude comprobar (SIN VERIFICAR)

- Cuántas de las 77 líneas vacías son `escena_invalida` o `sunglint` (los records no se guardaron).
- Qué pasó con el cuarto gránulo de 375 perdido (N20 del 2026-10-22).
- Qué detectó la vía de 375 en los 28 gránulos, incluidas las 6 pasadas de alerta de MIROVA. No hay token de Earthdata a mi
  alcance (y no lo usé), así que no reproduje el cómputo.
- El costo de los otros 10 volcanes y del día en curso por LANCE.

## Qué le cambia esto al dueño

Para decidir si encender a diario: el costo es ~15 min por job con 11 jobs y 3 tandas, no 3 a 4 min (hallazgo 1). Y la sombra
que se enciende **no resuelve sola** lo que esta corrida dejó sin responder: cada día escribirá records de 375 que nadie podrá
leer desde el log, y records vacíos de 750 de gránulos que no ven el volcán (hallazgo 2). Arreglos de bajo costo que propongo
(no los apliqué, es otro sí de Nicolás): subir el JSON como artefacto del job cuando `medir=true`, imprimir `motivo_vacio` y
`vrp_mw` de la vía en la línea de log, y dar a VIIRS 750 el mismo corte de distancia al centro que a 375 y MODIS o marcar
esos records.
