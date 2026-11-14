# F1. La vía MODIS «código MIROVA» en el NRT (auditoría S175)

## 1. Encabezado

- **Hora del servidor**: Sat, 07 Nov 2026 20:20:51 GMT (cabecera `Date` de `gh api -i`, llamada 3 de esta sesión; la
  primera llamada dio 20:19:34 GMT). Adelantado al 2026-11-07 por decisión de Nicolás: el audit semanal del
  2026-11-09 no existe todavía (SIN DATO, lo anexa el orquestador).
- **Commits**: código de la base `752d348bc67190e53b610989877e2405d238a1bc` (copia `git archive` en
  `C:\Users\nmend\vrp-temporales\s175_audit\main\`); records y JSON de vigilancia de SHA_CAMPO
  `e75a7d52d445c1dc0d933e3b7900e42f089befce` (`origin/main` al lanzar F1). `git diff --stat 752d348bc e75a7d52d --
  scripts/ frontend/ pipeline/ volcanoes.yaml` no devuelve nada: el código es el mismo en los dos, así que cada cita
  `archivo:línea` vale para ambos. Línea base roja 2 sobre `79f410697` (datos del 2026-11-02 19:29 UTC).
- **Referencia (vara)**: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` de la base (sha256
  `f833bfde…`, verificado con `sha256sum` sobre la copia que armé por `git show`) y `registro_vrp_ocr.csv` (`577a336e…`).
  Donde usé además `latest_consolidado.csv` de la raíz (sha256 `dee76837…`, la copia que el banco NO lee) lo digo
  en cada número y lo rotulo «fuera de la vara».
- **Modelo y esfuerzo**: Claude Fable 5.1 corriendo como subagente del orquestador. Esfuerzo: **SIN DATO** (no veo
  ninguna etiqueta de esfuerzo en mi contexto; la sonda de la ola 0 vio `reasoning_effort 25` en el suyo, el mío no
  trae ninguna).
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f1\`
  (instrumentos: `censo_via_modis.py`, `banco_via_vs_k.py`, `mutaciones_vigilancia.py`; este informe;
  `hallazgos.csv`). Salidas crudas en `C:\Users\nmend\vrp-temporales\s175_audit\f1\salidas\`; árbol de trabajo (código
  de la base + datos de SHA_CAMPO + referencia de la base) en `C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base\`.
- **Presupuesto**: 3 llamadas a la API de GitHub de 10 (jobs de dos corridas del NRT y la lista de issues; cabecera
  `X-Ratelimit-Remaining` 4982 al final). Disco: la carpeta temporal llegó a **2,1 GB** durante la batería de
  mutaciones (ocho copias de los 11 JSON de producción, 164 MB cada una) y la recorté a 368 MB al terminar
  (borré las copias mutadas y las extracciones de `752d348bc` y `79f410697`, reproducibles por `git show`): el tope
  de 2 GB se pasó por unos minutos y lo declaro. C: 13,4 GB libres, D: 4,9 GB al cierre.
- **Qué NO miré**: el audit semanal del 2026-11-09 (no corrió aún; corrí el mismo script sobre los datos de SHA_CAMPO
  con la referencia de la base como sustituto, §7); el log de las corridas rojas del NRT del 4 y 5 de noviembre (leí
  qué paso falló, no por qué); los gránulos L1B ni el MxD03 de ninguna pasada (MODIS no corre en Windows, pyhdf); el
  detector de la vía contra el `.m` de MIROVA (eso es S158, no este frente); C-05 (geolocalización a más de 40° de
  cenit): la vía lee el MxD03, no `_interp_geo`, pero no medí posiciones; VIIRS (F2); el tablero en un navegador real
  (el predicado lo ejecuté con node, que es la vara); la rama `loop/activo` y el PR #952.

## 2. En una pantalla

1. Lo que MODIS publica desde el encendido es lo que la vía dice producir: 140 de 140 records de la vía coherentes en
   marca y contenido, 0 records de K escritos después del encendido, 0 discrepancias entre «la vía dice» y el
   predicado del tablero con node (8 publicados de 140), y en Chillán 6 de 6 alertas de MIROVA publicadas con razón
   mediana 1,07 (datos `e75a7d52d`, referencia de la raíz).
2. La vigilancia de la guardia ve la regresión que la regla nombra (control positivo: REVERSION_CANDIDATA inyectada,
   detectada) pero es **ciega por volcán**: si la vía cae a K o deja de escribir en un solo volcán, da VERDE sin aviso
   (mutaciones M2 y M2c), y **no mira de qué detector es el record de producción**: una caída a K que calla dispara
   REVERSION_CANDIDATA contra la vía (M6). Hallazgos 151 y 152, gravedad 4.
3. El descarte de borde de la vía (171-01) no deja rastro en el log ni en la cobertura (`return None` sin aviso,
   `pipeline/process_modis.py:657-658`); caso de campo: Villarrica MODIS_AQUA 2026-11-04 07:10 UTC, cenit 65°, con
   record en la guardia y ninguno en producción, y el NRT verde. Hallazgo 153.
4. §4.1 y §4.7 de la regla de reversión suponen que el NRT re-escribe la ventana de 8 días; el almacén sólo reemplaza
   con `--overwrite` o en el upgrade NRT a estándar (`pipeline/store.py:699`), y los datos lo muestran (primera
   observación de la vía 2026-11-02 01:15, no 8 días antes). El «día después» de una reversión está mal modelado.
   Hallazgo 154.
5. Líneas base rojas: (1) 0 records `sin_grilla`/`sin_mxd03`/`geo_distinta` después del encendido, con un control
   sintético que el censo sí ve; (2) sobre `79f410697`, 0 records de la vía entre 14.855 de MODIS. Sobre-publicación
   de la vía: 0 de 108 negativos limpios en 5 noches (raíz, fuera de la vara) y 0 de 19 en 1 noche (vara), contra
   K 15 de 1.317 (1,14 %): **sin veredicto** (A111).

## 3. Hallazgos (ordenados por gravedad, el peor primero; IDs 151 a 199)

### 151. La vigilancia no comprueba que el record de producción sea de la vía: una caída a K que calla dispara la reversión pre-autorizada contra la vía

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py:200-203` (`calla` = `guardia_pub is True and prod_pub is
  False`; `candidatas` no mira `prod_via`), `:171` (`prod_via` se calcula y sólo lo usa `borde_del_encendido`).
  Regla: `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md:189`, TEXTO: «producción (la vía) **tiene
  record y no publica** («calla»)». SCRIPT:SALIDA: `mutaciones_vigilancia.py`, mutación M6 en
  `C:\Users\nmend\vrp-temporales\s175_audit\f1\salidas\mutaciones_base_v2.json`.
- **QUÉ PASA**: con el flag encendido, cuando la vía no puede correr (sin grilla, sin MxD03, MxD03 de otra forma) el
  record lo escribe K con la marca en texto (`pipeline/process_modis.py:643-650`). Ese record no es la vía; si calla
  una protegida que la guardia (también K) publica, la diferencia es entre dos corridas de K (producto NRT contra
  estándar, por ejemplo), no de la vía. El instrumento lo informa igual como REVERSION_CANDIDATA y la regla
  pre-autoriza el `git revert` del PR B ese mismo día. En M6 cambié el record de producción de Chillán 2026-11-05
  07:45 a `via_codigo_mirova: "sin_mxd03"` callado y la guardia publicando: veredicto REVERSION_CANDIDATA, sin aviso.
  La confirmación en la imagen de MIROVA (§4.3) no lo atrapa: la imagen sí muestra la alerta.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; se vería en el issue «Guardia K de MODIS: candidata a reversion» y en una
  reversión ejecutada por algo que la vía no hizo.
- **CÓMO REPRODUCIRLO**: `python experiments/_s175_audit/f1/mutaciones_vigilancia.py
  C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base 2026-11-07`, bloque `M6_prod_record_es_caida_K_...`
  (NevadosDeChillan MODIS 2026-11-05 07:45 UTC, MIROVA 25,0 MW).
- **CONFIANZA**: CONFIRMADO (leído y medido). Hoy no hay ningún record de caída a K en los datos (censo, 0 de 140),
  así que el defecto está latente.
- **GRAVEDAD**: 4 (puede torcer la decisión de revertir el detector de producción, pre-autorizada y del mismo día).

### 152. Vigilante ciego por volcán: si la vía cae a K o deja de escribir en un solo volcán, la vigilancia da VERDE sin aviso

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py:345-358` (`avisos_via`: compara la última noche de la vía
  con la última de MODIS **sumando los 11 volcanes**); `:304` (`avisos_produccion` mide frescura de MODIS, K o vía
  por igual). Contraste: `scripts/vigilancia_sombra.py:362-365`, TEXTO: «Frescura POR VOLCÁN Y SENSOR. Si un lado
  muere en un solo volcán o en un solo sensor, sumar todo lo deja verde». SCRIPT:SALIDA: mutaciones M2 y M2c en
  `…\salidas\mutaciones_base_v2.json`.
- **QUÉ PASA**: la vía puede morir en un volcán y no en otro (grilla de MIROVA ausente para ese volcán, MxD03 que no
  baja para su órbita, un gránulo que siempre queda al borde). Ahí producción vuelve a ser K sin que nadie lo diga, y
  la guardia (K) compara K con K: nunca va a publicar algo que producción calle. M2 (los 15 records de la vía de
  Chaitén pasados a `"sin_grilla"`) y M2c (los 11 records de Chaitén desde el 2026-11-04 sin la clave, como si la vía
  hubiera dejado de escribir): VERDE, 0 avisos, en los dos casos. Sólo cuando mueren los 11 volcanes a la vez aparece
  el aviso (M2b: aviso «no hay ningún record MODIS de la vía», veredicto INVESTIGAR por una pasada distinta en el
  nulo, no VIGILANCIA_CIEGA).
- **CÓMO SE VE EN EL DASHBOARD**: en ese volcán la serie MODIS vuelve a K sin marca de fin (la marca naranja de
  `primeraViaModis` sigue dibujada) y la caída a K con texto no cuenta «ni como vía ni como K»
  (`frontend/cambio_detector.js:155-156`); el operador no tiene cómo saberlo.
- **CÓMO REPRODUCIRLO**: mismo comando que 151, bloques `M2_via_cae_a_K_solo_en_Chaiten` y
  `M2c_via_detenida_desde_2026-11-04_solo_en_Chaiten`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4 (un volcán entero queda sin la vigilancia que justificó encender sin la sombra de 28 noches).

### 153. El descarte de borde de la vía (171-01) no deja rastro: ni línea en el log, ni incidencia de cobertura, ni record

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:657-658` (`if _rec is None: return None`, sin `print` ni
  `al_sin_dato`); `pipeline/mirova_v750_codigo.py:804-808` (los dos cortes: menos de 100 celdas a 45 km, celda más
  cercana a más de 5 km, `FAMILIAS["MODIS"]["dist_max_centro_km"] = 5.0` en `:112`);
  `scripts/revisar_errores_modis_nrt.py` sólo busca `ERROR processing`. Caso de campo: `data/guardia_k_modis/Villarrica.json`
  en `e75a7d52d`, record `MYD021KM.A2026308.0710.061.2026308191510.hdf` (MODIS_AQUA 2026-11-04 07:10 UTC, cenit
  65,03°, 0 píxeles anómalos, t_bg 263,28 K); `data/mirova_equivalent/Villarrica.json` no tiene esa pasada.
- **QUÉ PASA**: al borde del barrido el píxel MODIS mide varios kilómetros y la grilla de 1 km de MIROVA queda con
  pocas celdas o con la celda más cercana lejos del centro; la vía devuelve `None` y la pasada desaparece de
  producción sin que el log diga una palabra. El paso «Revisar errores de MODIS en el log» del NRT (regla §4.4 (a))
  sólo atrapa excepciones. La corrida del NRT que procesó esa hora (run 41812405190, 2026-11-04 10:10 UTC) tiene el
  job de Villarrica verde y su paso de revisión verde (`…\salidas\gh_jobs_run_41812405190.txt`). La guardia sí
  escribió la pasada (K), MIROVA la tiene como RUTINA 0,0 (`latest_consolidado.csv`, raíz). La vigilancia la cuenta
  en `borde_171_01` (`2026-W45: 1`) y, por diseño, no dispara.
- **CÓMO SE VE EN EL DASHBOARD**: invisible: una pasada que no existe se ve igual que una noche sin pasada.
- **CÓMO REPRODUCIRLO**: comparar claves `(volcán, sensor, datetime_utc)` de `data/guardia_k_modis/*.json` contra
  `data/mirova_equivalent/*.json` en `e75a7d52d` (bloque «en guardia y no en prod» de esta sesión, reproducible con
  diez líneas de Python; lo dejo descrito en §6).
- **CONFIANZA**: CONFIRMADO que no hay rastro y que la pasada falta; **SOSPECHA** que la causa sea 171-01 y no un
  MxD03 ausente en las 12 corridas que cubrieron esa fecha (sin leer los logs no se distingue; ese es justamente el
  defecto).
- **GRAVEDAD**: 3 (una protegida en esa pasada sería silencio; la vigilancia la vería recién a las 24 h y sólo si la
  guardia la publica).

### 154. §4.1 y §4.7 de la regla suponen una re-escritura de 8 días que el almacén no hace

- **ARCHIVO:LÍNEA**: `pipeline/store.py:695-699` (`is_upgrade` = NRT a estándar; `if overwrite or is_upgrade:`
  reemplaza; si no, el record existente queda), `scripts/run_pipeline.py:189` (`overwrite: bool = False`) y `:594`
  (`--overwrite` sólo por flag), `.github/workflows/nrt.yml:185,201` (`--overwrite` sólo si el input manual
  `overwrite` es `true`; el cron no lo pasa). Regla `REGLA_REVERSION_MODD_BORRADOR.md:162`, TEXTO: «El NRT
  re-escribe en cada corrida las 8 fechas que van del día a 7 atrás», y `:318`, TEXTO: «El NRT re-escribe con K las 8
  fechas de su ventana; lo observado antes queda con `via_codigo_mirova: true`».
- **QUÉ PASA**: el NRT vuelve a bajar y procesar los 8 días, pero `append_record` sólo reemplaza un record cuando el
  anterior era NRT y el nuevo es estándar. Datos de `e75a7d52d`: los 162 records K de MODIS del 2026-10-25 al
  2026-11-01 son todos `standard` y siguen siendo K; la primera observación de la vía es 2026-11-02 01:15 (no «hasta
  unos 8 días antes del merge»); el único record K NRT que quedaba (PlanchonPeteroa 2026-11-02 01:15) será
  reemplazado por la vía al llegar el estándar. Al revés, tras un `git revert` del PR B, K **no** re-escribe los 8
  días: los 119 records estándar de la vía quedan para siempre y sólo los 21 NRT de la vía (11-06 y 11-07) se
  reemplazan por K al llegar el estándar. El paso 1 de §4.7 (apartar «lo observado antes» de la ventana) deja afuera
  toda la ventana; la franja «retrospectiva» de §4.1 casi no existe (sólo upgrades).
- **CÓMO SE VE EN EL DASHBOARD**: tras una reversión, la serie MODIS mezclaría dos detectores durante más tiempo y en
  más pasadas de lo que el issue de la reversión diría; hoy, nada.
- **CÓMO REPRODUCIRLO**: `python experiments/_s175_audit/f1/censo_via_modis.py <carpeta e75a7d52d> e75a7d52d`
  (`primera_observacion_via`, `product_version_de_los_records_via…`) y el bloque por día y versión de producto de
  esta sesión (§6).
- **CONFIANZA**: CONFIRMADO (código y datos).
- **GRAVEDAD**: 3 (no tuerce una alerta de hoy; tuerce el día después de una reversión y la lectura de la frontera).

### 155. §4.3 pide confirmar en «la captura mirova-tif-archive», pero los TIF dejaron de capturarse el 2026-09-22; sólo siguen los PNG

- **ARCHIVO:LÍNEA**: `REGLA_REVERSION_MODD_BORRADOR.md:192`, TEXTO: «la sesión mira la cabecera de la imagen de MIROVA
  de esa pasada (la captura `mirova-tif-archive`; el 2026-11-02 seguía capturando, VR-06)». Insumos:
  `C:\Users\nmend\vrp-temporales\s175_audit\insumos\tif_index.csv` (21.873 filas, `captured_at_utc` máximo
  2026-09-22T11:01:36; `acquisition_utc` máximo 2026-09-22 07:40) y `png_index.csv` (167.626 filas, `captured_at_utc`
  máximo 2026-11-07T04:05:57; MODIS hasta 2026-11-07T04:05:55).
- **QUÉ PASA**: la confirmación de una candidata depende de una imagen con cabecera; la captura de TIF (la que lleva
  `acquisition_utc`) está detenida desde septiembre (memoria del proyecto: MIROVA sirve el mismo TIF). Lo que sigue
  vivo son los PNG `VRP`/`logVRP` por volcán y sensor, que no traen hora de adquisición en el índice (`last_modified_utc`
  sí). La regla no dice cuál de las dos capturas es «la imagen», y además la vigilancia no publica la procedencia
  (tabla u OCR) que D6 necesita (la regla lo reconoce en §4.3, «De dónde sale la procedencia»).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -c "import csv;..."` sobre los dos índices (bloque de esta sesión, §6).
- **CONFIANZA**: CONFIRMADO en los índices; SOSPECHA en que el PNG baste para «la cabecera de la imagen» (no lo
  ejercité).
- **GRAVEDAD**: 2 (retrasa o enreda la confirmación; con D6 la tabla basta para revertir).

### 156. El audit semanal deja de dar flag por las protegidas MODIS que K no publicó en cuanto la vía tiene records, sin anunciarlo como pérdida de vigilancia

- **ARCHIVO:LÍNEA**: `scripts/auto_audit_weekly.py:1023-1025` (`_de_vigente`: la protegida es del detector que decide
  en su sensor), `:427-429` (`detector_vigente_de` da VIA_MODIS en MODIS desde que hay records de la vía),
  `:1050-1059` (`flags_protegidas` filtra por `_de_vigente`). SCRIPT:SALIDA:
  `…\salidas\auto_audit_weekly_base_snapshot.txt` y `…\root_base\data\audit_continuous\latest.json`.
- **QUÉ PASA**: corrido el 2026-11-07 sobre los datos de SHA_CAMPO con la referencia de la base, el audit lista
  «protegida sin_publicar [K] NevadosDeChillan MODIS 2026-10-25 07:20 MIROVA 3.79 MW» y «2026-10-30 07:15 MIROVA 1.0
  MW», y aun así `flags: []` y VERDE: ya no son del detector vigente de MODIS. El 2026-11-02 (79f410697, detector K) eran
  flags. Es la regla S156 «un detector a la vez» aplicada a MODIS, pero el aviso «SIN JUZGAR» habla del recall, no de
  las protegidas: el lector ve VERDE donde la semana anterior había dos pérdidas (A87).
- **CÓMO SE VE EN EL DASHBOARD**: no se ve; se ve en el issue semanal, que pasa de FUERA DE BANDA a VERDE.
- **CÓMO REPRODUCIRLO**: `cd C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base && python scripts/auto_audit_weekly.py`
  (escribe en `data/audit_continuous/` de esa copia).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### 157. El recall de VIA_MODIS no puede dar flag hasta juntar 15 noches con alerta; a 2 noches en 5 días, son semanas sin banda

- **ARCHIVO:LÍNEA**: `scripts/auto_audit_weekly.py:94` (`MIN_N_RECALL = 15`), `:577-590` (aviso «sin juzgar» para
  VIA_MODIS). SCRIPT:SALIDA: `latest.json` de §7: `recall.MODIS.n_noches = 2`, aviso «MODIS sin juzgar: 2 noches…».
- **QUÉ PASA**: por diseño (S173, hallazgo 206) el recall de la vía arranca de cero. Con la referencia de la base
  (MODIS hasta el 2026-11-02 12:20) son 2 noches; con la de la raíz serían 5. Al ritmo de Chillán (la única con
  alertas MODIS en la ventana) el mínimo llega en 4 a 7 semanas. Mientras, la única protección es la lista nominal de
  protegidas (que sí funciona, §5). Lo informa, no degrada.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: como 156.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### 158. El encendido se cuelga de un solo record y un reproceso con `--overwrite` lo movería hacia adelante

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py:98-115` (`encendido_desde_datos`: mínimo de `processed_utc`
  de los records de la vía), `pipeline/store.py:541` (`processed_utc` se re-escribe en cada versión del record).
  SCRIPT:SALIDA: bloque «via processed primeros 5» de esta sesión: `2026-11-02T20:11:43Z` Isluga 2026-11-02 01:20
  (standard), después `20:11:45Z`, `20:12:57Z`.
- **QUÉ PASA**: el encendido (desde cuándo cuenta la reversión pre-autorizada y los 120 días) es el `processed_utc`
  más antiguo entre los records de la vía. Hoy lo lleva un único record, estándar, así que ningún upgrade lo toca y
  el valor es estable (5 días iguales en `guardia_modis_history.jsonl`). Pero un reproceso con `--overwrite` de la
  ventana de la vía, o un borrado y reposición (§4.7 paso 1), le pone `processed_utc` nuevo a todos y el encendido
  salta a esa fecha: las pasadas entre medio pasan a «retrospectivas» (no pre-autorizadas) y los 120 días se
  estiran. El diseño lo eligió a propósito contra `first_processed_utc` (MA172-206); el riesgo inverso no está
  escrito.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `censo_via_modis.py` (`encendido_remedido_min_processed_via`) sobre una copia con
  `processed_utc` alterado.
- **CONFIANZA**: CONFIRMADO el mecanismo; SOSPECHA que ocurra (requiere un reproceso que hoy nadie corre).
- **GRAVEDAD**: 2.

### 159. Con la vía muerta en los 11 volcanes el veredicto es INVESTIGAR, no VIGILANCIA_CIEGA, y el issue cambia de clase

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py:419-420` (`evaluar`: `if veredicto == "VERDE" and avisos:
  veredicto = "VIGILANCIA_CIEGA"`). SCRIPT:SALIDA: mutación M2b en `…\salidas\mutaciones_base_v2.json`.
- **QUÉ PASA**: la regla dice que un VERDE con avisos no es VERDE. Pero si además hay algo que investigar (en M2b el
  nulo da 1 pasada distinta porque los records mutados dejan de ser «vía» y entran al nulo), el veredicto es
  INVESTIGAR y el issue que se abre es «Guardia K de MODIS: investigar», con el aviso de ceguera en el cuerpo. La
  clase del issue no dice que la vigilancia está ciega.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: como 151, bloque `M2b_via_cae_a_K_en_todos`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

### 160. Un JSON de la guardia ausente vacía la guardia entera y el aviso culpa a los 11 volcanes

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py:363-378` (`cargar_insumos`, `:377` `except
  FileNotFoundError: guardia = []`); `scripts/banco_paridad.py` (`cargar_nuestros` abre los 11 archivos en un solo bucle). SCRIPT:SALIDA: mutación
  M3 (`Villarrica.json` borrado): 11 avisos «no hay records de la guardia (K) de <volcán>», veredicto
  VIGILANCIA_CIEGA.
- **QUÉ PASA**: el veredicto es el correcto (ciega), pero el diagnóstico apunta a los 11 volcanes y al nulo («0
  pares») cuando falta uno. Quien lea el issue va a buscar una guardia muerta, no un archivo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (el tablero no lee la guardia).
- **CÓMO REPRODUCIRLO**: como 151, bloque `M3_guardia_sin_Villarrica.json`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

### 161. Los píxeles anómalos de la vía no traen `vrp_mw` por píxel

- **ARCHIVO:LÍNEA**: `pipeline/mirova_v750_codigo.py` (`procesar_grilla`, lista `pix` con `lat, lon, dist_km, bt_k,
  fila, col`); `pipeline/store.py:609-614` (comentario S165: «Sus píxeles no traen vrp_mw por píxel»). SCRIPT:SALIDA:
  `censo_e75a7d52d.json` (huella `pix_sin_vrp` en los 8 records de la vía con píxeles).
- **QUÉ PASA**: la vía informa la suma de la unión de alertados (D32) y no reparte el VRP por píxel. El predicado no
  lo necesita (MODIS publica `pc.vrp_mw`, `frontend/index.html:1162-1180`), y `f5_core` no se escribe para la vía
  (`store.py:609`). Donde sí se lee por píxel (la tabla «Todos los pixels» del detalle, `vrp_mw_sum_active` si
  `ENABLE_SUM_VRP_REPORTING` se encendiera, `scripts/paper_numbers.py` según el comentario de store) saldría vacío o
  0. No cambia ninguna publicación.
- **CÓMO SE VE EN EL DASHBOARD**: SOSPECHA: columna de VRP por píxel vacía en el detalle de una pasada de la vía (no
  lo abrí en navegador).
- **CÓMO REPRODUCIRLO**: `censo_via_modis.py` (huellas) o leer `anomaly_pixels` de Chillán 2026-11-07 07:25 en
  `data/mirova_equivalent/NevadosDeChillan.json`.
- **CONFIANZA**: CONFIRMADO en los datos; SOSPECHA en el efecto visual.
- **GRAVEDAD**: 1.

## 4. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

- **S-1. La referencia que leen el banco y el audit (snapshot) envejece hasta 7 días.** `.github/workflows/sync-mirova-csv.yml:108-109`
  sincroniza cada hora `latest_consolidado.csv` y el OCR del snapshot, **no** `mirova_v1_snapshot/registro_vrp_consolidado.csv`;
  ese archivo sólo lo refresca `audit-weekly.yml:55-56` los lunes. En la base, el snapshot tiene MODIS hasta
  `2026-11-02 12:20:00` y la raíz hasta `2026-11-06 22:00:00` (34 contra 241 filas MODIS desde el 2026-11-02). Es la
  vara de esta auditoría, así que no la juzgo; la consecuencia para F1 está en §8. Para el audit del 2026-11-09 no
  importa (refresca antes de correr). Confianza: CONFIRMADO.
- **S-2. Corridas rojas del NRT del 4 y 5 de noviembre.** Runs 41812405190 (2026-11-04 10:10, Lascar y Llaima) y
  42016780200 (2026-11-05 11:10, Villarrica y Copahue): el paso que falla es «Run VRP pipeline» del perfil
  `mirova_equivalent`; el paso «Revisar errores de MODIS en el log» salió verde en los 22 jobs. Causa SIN DATO (no
  leí los logs). Otras 6 corridas rojas en `insumos\runs_nrt.json` sin mirar.
- **S-3. Dos protegidas MODIS de K sin publicar en Chillán** (2026-10-25 07:20, 3,79 MW; 2026-10-30 07:15, 1,0 MW,
  sólo OCR) siguen sin decisión escrita: la guardia tiene record y no las publica tampoco (K contra K coinciden), así
  que son pérdidas de K, no de la vía. Relacionado con 156.
- **S-4. `avisos_perfiles` de la vigilancia** (`scripts/vigilancia_guardia_modis.py:331-343`) cuenta records de la guardia con `perfil == mirova_equivalent` y al
  revés, pero un record sin marca de régimen (`regimen` ausente) no cuenta en ninguno. Hoy 286 de 286 records de la
  guardia traen `guardia_k_modis`. Confianza: CONFIRMADO lo leído, sin caso real.

## 5. VERIFICADO LIMPIO (qué miré, cómo, contra qué vara)

- **(a) Detector efectivo contra declarado**: `censo_via_modis.py` sobre `e75a7d52d`: 14.973 records MODIS, 140 con
  `via_codigo_mirova: true`, 14.833 sin la clave, **0** con la clave en texto. Los 140 traen `diag_codigo_mirova` y
  `final_hotspot_source == "codigo_mirova"` y ninguno de los 14.833 los trae (0 incoherencias declarado contra
  contenido). 140 de 140 con `processed_utc` igual o posterior al encendido y perfil `mirova_equivalent`; **0 records
  de K escritos después del encendido**. Control positivo: con `--control` el censo ve el record sintético
  `"sin_mxd03"` (1 caída). Vara: definición de `es_record_via_modis` (`scripts/auto_audit_weekly.py:455-456`), que es
  objeto de F1 y la contrasté con el contenido.
- **Línea base roja 2**: sobre `79f410697`, 14.855 records MODIS, 0 de la vía (`censo_79f410697.json`): #915 y #936
  juzgaron MODIS con K porque no había ningún record de la vía en los datos del 2026-11-02 19:29.
- **(b) La vía contra el predicado del tablero**: `banco_via_vs_k.py` (node sobre `frontend/index.html` de la base,
  `correr_node`, `banco_paridad.py:156`): 140 records de la vía, `dice=1 pub=1: 8`, `dice=0 pub=0: 132`, **0
  discrepancias**, donde «dice» = cúmulo más radiante en la cumbre con `pc.vrp_mw > 0` y centroide dentro del inner.
  Ningún record de la vía con `distance_class: far` y VRP > 0 (el caso en que la suma de MIROVA se publicaría como 0
  no ha ocurrido). Identidad del predicado: `[[0,1,1,1,0],[1,0]]` como el guard S139. Control positivo sobre Chillán
  2026-11-02 01:15 MODIS_TERRA: original pub 1; mutado a `far` 0; mutado `pc.vrp_mw 0` 0; mutado frío (t_max 250 K,
  20 MW) con marca de la vía 1 (exención S173) y sin marca 0 con artefacto 1 (filtro cirrus de K). La exención está
  replicada en las tres vistas: `frontend/index.html:1337,1356`, `diario.html:378,389`, `mosaico.html:363,374`.
- **Campo, Chillán** (referencia de la raíz, fuera de la vara): 6 de 6 alertas de MIROVA desde el encendido
  publicadas por la vía: 2026-11-02 01:15 (4,33 contra 3,64 MW), 07:30 (12,82 contra 11,51), 2026-11-04 08:45 (17,10
  contra 13,28), 2026-11-05 01:35 (24,63 contra 25,84), 07:45 (24,70 contra 25,49), 2026-11-06 08:25 (25,13 contra
  24,29); razones 1,19, 1,11, 1,29, 0,95, 0,97, 1,03, mediana 1,07. Las dos pasadas del 2026-11-07 (8,64 y 6,71 MW,
  cenit 42,7° y 58,2°) aún no tienen fila en la referencia (`sin_info`). Los 2 negativos limpios de Chillán de la
  vía (2026-11-03 01:55 y 08:10) no publican.
- **Pareo**: 18 alertas MODIS de MIROVA desde el 2026-10-19 (17 Chillán, 1 Láscar 0,29 MW), las 18 con record nuestro
  a 0 s (`alertas_sin_record` vacío): el pareo de ±120 s no pierde nada en MODIS.
- **Guardia**: 286 records MODIS en `data/guardia_k_modis/` (2026-10-26 a 2026-11-06), 286 con perfil
  `guardia_k_modis`, 0 con la clave de la vía; pasada a pasada coincide con producción salvo Villarrica 2026-11-04
  07:10 (sólo guardia, hallazgo 153), Copahue y Llaima 2026-10-26 (producción, antes del arranque de la guardia) y las
  22 pasadas del 2026-11-07 (la guardia corre a las 17:40). Nulo de la vigilancia: 167 pares, 0 distintas.
- **Vigilancia reproducida**: `scripts/vigilancia_guardia_modis.py` de la base sobre `root_base` con la referencia de
  la base: VERDE, encendido `2026-11-02 20:11:43`, primera observación `2026-11-02 01:15`, flag `true`, iguales al
  JSON commiteado en `e75a7d52d` (generado 2026-11-07 02:22 con la referencia viva). Difieren sólo por la referencia:
  15 contra 18 pasadas con alerta, 1 contra 4 protegidas vistas, `sobrepublicacion.n` 0 contra 89 (S-1).
- **Controles de la vigilancia que sí ven**: M1 (producción vía calla, guardia publica, Chillán 2026-11-05 07:45,
  25,0 MW) → REVERSION_CANDIDATA; M4 (producción sin record, guardia publica, más de 24 h) → INVESTIGAR con
  `protegidas_sin_record_produccion`; M3 (JSON de la guardia ausente) → VIGILANCIA_CIEGA; M5 (3 records de la guardia
  con marca de la vía) → VIGILANCIA_CIEGA.
- **Encendido estable**: el mínimo `processed_utc` lo lleva un record estándar (Isluga 2026-11-02 01:20), constante en
  las 11 líneas de `guardia_modis_history.jsonl` del 3 al 7 de noviembre.
- **Issues**: desde el 2026-11-01 sólo #936 (audit FUERA DE BANDA del 2026-11-02, con K), #941, #942 (sombras sin
  corrida verde, cerrados) y #943 (cese Suomi NPP): ningún issue «Guardia K de MODIS» (coherente con VERDE).
- **Perfiles por A89**: `VRP_PROFILE=mirova_equivalent` da `ENABLE_MODIS_CODIGO_MIROVA True`, `DATA_SUBDIR
  mirova_equivalent`; `guardia_k_modis` da `False`, `guardia_k_modis` (importado desde `root_base`).

## 6. Cómo se reprodujeron los bloques sueltos (sin script propio)

Todos corren con Python 3.12 desde `C:\Users\nmend\vrp-temporales\s175_audit\f1\` sobre `datos\e75a7d52d\` (extraído con
`git show e75a7d52d:data/mirova_equivalent/<Volcán>.json` y `…guardia_k_modis/<Volcán>.json`):
- Conteo por día, detector y `product_version` desde el 2026-10-25 (hallazgo 154): agrupar los records MODIS por
  `datetime_utc[:10]`, `via_codigo_mirova is True` y `product_version`.
- Claves en guardia y no en producción (hallazgo 153): conjuntos de `(volcán, sensor, datetime_utc)` de los dos
  directorios.
- Índices TIF y PNG (hallazgo 155): `csv.DictReader` sobre `insumos\tif_index.csv` y `png_index.csv`, máximo de
  `captured_at_utc` y de `acquisition_utc`.
- Frescura de la referencia (S-1): máximo de `Fecha_Satelite_UTC` por `Sensor` en los tres CSV de `insumos\`.

## 7. Sustituto del audit del 2026-11-09

`scripts/auto_audit_weekly.py` de la base corrido el 2026-11-07 20:23 UTC sobre `root_base` (datos `e75a7d52d`,
referencia de la base): VERDE; `detector.vigente_por_sensor.MODIS = VIA_MODIS`, `frontera_via_modis = 2026-11-02`;
VIA_MODIS recall MODIS 100 % sobre 2 noches (0 sin datos), magnitud publicada Chillán|MODIS razón mediana 1,051 (2
noches, 2 pasadas por noche); `fuera_de_detector: {"K en noche VIA_MODIS": 1}` (el record K NRT de PlanchonPeteroa
2026-11-02 01:15); falsas publicaciones VIA_MODIS 0,0 % de 19 negativos limpios; avisos «MODIS sin juzgar: 2
noches»; protegidas MODIS de la vía: 3, las 3 publicadas; `flags: []` (hallazgo 156). Salida en
`…\salidas\auto_audit_weekly_base_snapshot.txt` y `…\root_base\data\audit_continuous\latest.json`. El resultado
real del lunes, con la referencia refrescada, lo anexa el orquestador.

## 8. SIN DATO

- **Sobre-publicación de la vía bajo la vara**: 0 publicados de 19 negativos limpios en 1 noche (2026-11-02), porque
  el snapshot de la base termina ahí (S-1). Fuera de la vara (`latest_consolidado.csv` de la raíz): 0 de 108 en 5
  noches y 11 volcanes (Chaitén 12, PCC 12, Copahue 11, Llaima 11, Villarrica 11, Láscar 10, Lastarria 10, Isluga 10,
  Tupungatito 10, PP 9, Chillán 2). K antes del encendido, mismos volcanes y mismo predicado: 15 de 1.317 (1,14 %)
  del 2026-09-01 al 2026-11-01 y 11 de 623 (1,77 %) en los 30 días previos. Con la tasa de K se esperarían 1,2 a 1,9
  publicaciones en 108: un cero es compatible con «igual» y con «mejor». **Sin veredicto** (A111); el denominador que
  pide la regla (§4.4 (ii)) lo mide la vigilancia con la referencia viva: `sobrepublicacion.n = 89, k = 0` al
  2026-11-07 02:22.
- Resultado del audit semanal del 2026-11-09 contra la regla §4 (anexo del orquestador).
- Causa de las corridas rojas del NRT (S-2) y causa exacta de la ausencia de Villarrica 2026-11-04 07:10 (153).
- Si «la cabecera de la imagen de MIROVA» de §4.3 se puede leer hoy desde los PNG (155): no lo ejercité.
- C-05 (geolocalización MODIS sobre 40° de cenit con la vía): no medido; la vía usa el MxD03
  (`pipeline/mirova_v750_codigo.py`, `leer_geo_mxd03`), que es otro camino que el de C-05.

## 9. FUERA DE ALCANCE

VIIRS 375 y 750 (F2, F3); D11 y D12; la fidelidad del detector de la vía al `.m` de MIROVA (S158); `sombra_34` y la
sombra de los 34 volcanes; el histórico K anterior al 2026-10-25; la rama `loop/activo`, el PR #952 y las carpetas de
S174.
