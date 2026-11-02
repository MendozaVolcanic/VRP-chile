# Frente 2, mini auditoría S172: promesa, supuesto y control del encendido de la vía MODIS

## 1. Encabezado

- Hora del servidor al empezar: Mon, 02 Nov 2026 00:46:15 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera
  `Date`). Hora al cerrar: al final del informe.
- Objeto, fijado por hash: base `d3cd0b2aeee70b99fbc5bd90e5fd2b0dff284f54` (tag `pre-s171-adopcion-modd`); PR A
  `c83882fcfdbd7fdb441e61a54a03c8f5fb3707b2`; PR B `b4282319446cfea944aa1a4621c0fec7da8649a0`; `origin/main` al medir
  `14fb62030a186fda02ce2ba172866cf01408eeb9`. Verificado con `git log --format='%H %P'`: el padre del primer commit
  del PR B (`479a30c18`) es `da67fa417`; `c83882fcf` no está en la historia del PR B; `git diff --stat da67fa417
  b42823194` da 21 archivos, entre ellos `pipeline/process_modis.py` (6 líneas: cabecera FICHA y un comentario).
- Referencia de MIROVA del worktree del PR B: `registro_vrp_consolidado.csv` sha256 `ab1a208c...7d88f` y
  `registro_vrp_ocr.csv` sha256 `d4ad8c44...5026e` (coinciden con el preámbulo). En los arneses la referencia es
  sintética, a propósito (escenas controladas); no usé alertas reales, así que A119 no aplica a ningún número de aquí.
- Modelo y esfuerzo: Opus 5.5 (`claude-opus-5-5`). Esfuerzo: el prompt pide alto; desde dentro no puedo leer el
  esfuerzo con que me lanzaron, lo declaro como no verificado. Python 3.12.10 de
  `C:\Users\nmend\AppData\Local\Programs\Python\Python312` (no encontré Anaconda en `C:\ProgramData\Anaconda3` ni en
  `C:\Users\nmend\Anaconda3`); node del sistema.
- CARPETA: `D:\vrp-trabajo\temporales\s172_miniaud\f2` (scripts con su salida al lado: `arnes\`, `tablero\`,
  `revert\`, `tiempos\`, `pyproj_check\`).
- Llamadas GET a la API de GitHub: unas 25 (tope 30). Nada despachado, nada empujado, ningún tag ni rama con nombre.
- Qué NO miré (mi silencio aquí no es «todo bien»): el detector `VIA_MODIS` de `scripts/auto_audit_weekly.py` (sólo sé
  que existe); `scripts/revisar_guardia_modis.py` más allá de su docstring; las tres vistas renderizadas en un navegador
  (corrí `frontend/cambio_detector.js` con node y el predicado de `index.html` con node, no las páginas); el tamaño real
  del escalón de magnitud de Chillán con la vía; el censo de consumidores del flag y la cobertura de pruebas de la vía
  (frente 1); crons, concurrencia, herencia de perfiles y el lector de V375-E (frente 3).

## 2. En una pantalla

1. El PR B enciende la vía sin agregar `pyproj` al runner del NRT: la vía lo importa en cada gránulo MODIS y el NRT no
   lo instala (resolución de pip: ausente; control con pyproj pedido: presente). Sin él la vía revienta, el gránulo no
   deja record ni cae a K: MODIS desaparece del tablero desde el merge (MA172-201, gravedad 5).
2. La vigilancia sólo llama «calla» a un record de producción que no publica: si la vía no escribe record (descarte de
   borde 171-01, que la regla llama el peor caso, o el caso 1) la protegida que la guardia publica da VERDE y ningún
   issue (MA172-202, gravedad 4).
3. Otros tres casos ciegos medidos con el arnés dan VERDE: guardia muerta hasta 3 días, referencia de MIROVA sin filas
   MODIS con VIIRS fresco, nulo de la guardia con 0 pares. El control positivo dispara: el arnés vive.
4. Tras una reversión la marca del tablero sigue diciendo que MODIS viene de la vía y el escalón de vuelta queda sin
   marca; y el «encendido desde los datos» cae hasta ~4,5 días ANTES del merge por el upgrade NRT a estándar.
5. El revert del PR B sale limpio hoy en las cuatro simulaciones, y la suite completa tras el revert da 2888 verdes y 2
   rojas que son del entorno (temporal en C:, repo en D:), rojas igual en la base y verdes con el temporal en D:.

## 3. Hallazgos (lo peor primero)

### MA172-201

- TÍTULO: el NRT no instala pyproj y la vía de MODIS lo importa en cada gránulo: con el PR B, producción deja de
  escribir MODIS
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml` l. 140 a 143 (en `b4282319` y en `origin/main` `14fb62030`: `pip install
  pyhdf` y `pip install earthaccess numpy h5py scipy pyyaml`, sin pyproj); `pipeline/mirova_v750_codigo.py` l. 814
  (`remuestrear_grilla` dentro de `calcular_vrp_granulo`) y l. 204 (`from pyproj import Transformer`);
  `scripts/run_pipeline.py` l. 279 a 280 (`except Exception as e: print(f"  ERROR processing {l1b.name}: {e}")` y sigue
  con el gránulo siguiente). El PR B no toca ningún workflow (`git diff --stat da67fa417 b42823194`: ningún archivo bajo
  `.github/`). SCRIPT:SALIDA: `pyproj_check\resolucion_nrt_deps.txt`, `arnes\arnes_via_pyproj_salida.txt`.
- QUÉ PASA: cada pasada MODIS sobre los 11 volcanes se pierde entera. La vía tiene que pasar el gránulo a la grilla UTM
  de MIROVA y para eso usa pyproj, que el runner del NRT no tiene. El import está dentro de la función, así que el módulo
  carga bien y el error aparece al procesar: `ModuleNotFoundError` dentro de `calculate_vrp`, que `run_pipeline.py`
  atrapa por gránulo. No hay record de la vía ni caída a K (la caída a K existe sólo para `sin_grilla`, `sin_mxd03` y
  `geo_distinta`, `pipeline/process_modis.py` l. 641 a 650). El proyecto ya lo sabía para la sombra: «# pyproj: la via
  lo usa para pasar el granulo a la grilla UTM de MIROVA (remuestrear_grilla); el NRT no lo instala»
  (`.github/workflows/sombra-codigo-mirova.yml` l. 90, TEXTO), y `tests/test_sombra_codigo_mirova_s167.py` l. 170 lo
  exige para la sombra; nada lo exige para el NRT.
- CÓMO SE VE EN EL DASHBOARD: desde la primera corrida del NRT tras el merge, ninguna pasada MODIS nueva en las tres
  vistas; VIIRS sigue. En Chillán no aparecen ni las alertas MODIS que el encendido prometía recuperar ni las que K
  publicaba. El NRT queda verde: la aserción A57 (`nrt.yml` l. 285 a 331) mira el último record de cualquier sensor y
  VIIRS lo mantiene fresco. La vigilancia de la guardia sí lo ve, pero como «vigilancia ciega» (aviso «el flag de la vía
  de MODIS está encendido en producción y no hay ningún record MODIS de la vía», escena S7), no como candidata a
  reversión: la regla pre-autoriza revertir sólo la candidata (y ver MA172-202).
- CÓMO REPRODUCIRLO: `python -m pip install --dry-run --ignore-installed --report r.json --platform manylinux2014_x86_64
  --python-version 3.11 --only-binary=:all: earthaccess numpy h5py scipy pyyaml` (37 paquetes, pyproj ausente; control
  con `pyproj` agregado a la lista: 38, presente). Después `python
  D:\vrp-trabajo\temporales\s172_miniaud\f2\arnes\arnes_via_pyproj.py` (gránulo sintético de Láscar, nombre
  `MYD021KM.A2026115.0735`): brazo A con pyproj da `via_codigo_mirova = True`, 8,962 MW, y el predicado del tablero lo
  publica (`[1, 1, 0, 8.962, 1]`); brazo B sin pyproj da `ModuleNotFoundError` en `mirova_v750_codigo.py` l. 814 → 204.
- CONFIANZA: CONFIRMADO (lista leída, resolución medida con control positivo, excepción reproducida, captura por
  gránulo leída). SOSPECHA residual mínima: no comprobé que la imagen `ubuntu-24.04` traiga o no pyproj en el Python de
  `setup-python` (el workflow de la sombra afirma que no).
- GRAVEDAD 1-5: 5. Apaga MODIS de producción entero, con Chillán en erupción, y la reversión pre-autorizada no se
  dispara.

### MA172-202

- TÍTULO: la vigilancia no cuenta como «producción calla» una pasada sin record de producción; el peor caso que nombra
  la regla no dispara la reversión ni abre issue
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 185 a 189 (`calla(p)` exige `p["prod_pub"] is False`);
  `scripts/vigilancia_sombra.py` l. 128 a 129 (`_publica` devuelve None si no hay record a ±120 s);
  `pipeline/process_modis.py` l. 657 a 658 (`if _rec is None: return None`) con `pipeline/mirova_v750_codigo.py` l. 804
  a 808 (menos de 100 píxeles a 45 km, o centro a más de 5 km: `return None`); `.github/workflows/vigilancia-guardia-
  modis.yml` l. 128 a 137 (con VERDE: «sin issue»). La prueba del implementador fija este comportamiento:
  `tests/test_vigilancia_guardia_modis_s172.py::test_mutacion_produccion_sin_record_o_guardia_que_calla_no_es_reversion`.
  SCRIPT:SALIDA: `arnes\arnes_vigilancia_salida.txt`, escena S1.
- QUÉ PASA: la regla dice que el peor caso es «una señal **débil o de borde de barrido** que K publica y la vía no. La
  vía descarta en silencio los gránulos que no cubren el volcán» (`REGLA_REVERSION_MODD_BORRADOR.md` l. 25 a 27, rama
  `loop/activo`, TEXTO), y su disparador es que «MIROVA publica, la guardia K publica y producción (la vía) calla»
  (l. 96 a 97). Para el operador, una pasada sin record es silencio igual que una que no publica. El código las separa:
  sin record, `prod_pub` es None, `calla` da False, la pasada no es candidata ni entra en
  `protegidas_sin_publicar_produccion`; sólo suma 1 en `borde_171_01.total`, que no cambia el veredicto, y con VERDE el
  workflow no abre issue, así que ese contador queda en un JSON que nadie lee. Lo mismo para MA172-201 (escena S7: la
  protegida que la guardia publica no sale como candidata).
- CÓMO SE VE EN EL DASHBOARD: una alerta de MIROVA de 2,5 MW en Chillán que K habría publicado no aparece en el tablero,
  y la vigilancia dice VERDE.
- CÓMO REPRODUCIRLO: `python D:\vrp-trabajo\temporales\s172_miniaud\f2\arnes\arnes_vigilancia.py`, escena
  `S1_via_sin_record_borde_171_01` (Nevados de Chillán, MODIS 2026-11-10 06:40 UTC, MIROVA 2,5 MW, la guardia publica,
  producción sin record): `VERDE ... rev=[] borde171=1`. Control positivo `S0` (la misma pasada con record de
  producción que no publica): `REVERSION_CANDIDATA`.
- CONFIANZA: CONFIRMADO el comportamiento (medido). SOSPECHA sobre la frecuencia: el docstring de
  `test_via_sin_cobertura_no_cae_a_k` dice que en el censo, en 144 pasadas con el volcán fuera del gránulo, K tampoco
  publicó; no lo verifiqué.
- GRAVEDAD 1-5: 4. Es la pérdida que la guardia existe para ver; si ocurre, la reversión no se dispara y nadie recibe
  aviso.

### MA172-203

- TÍTULO: una guardia muerta hasta 3 días deja la vigilancia en VERDE aunque haya una protegida que producción calla; el
  rojo del job de la guardia nadie lo convierte en issue
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py` l. 61 (`MAX_DIAS_SOMBRA_SIN_DATOS = 3`) y l. 379 (`if dias >
  MAX_DIAS_SOMBRA_SIN_DATOS`); `scripts/vigilancia_guardia_modis.py` l. 277 a 278; `.github/workflows/vigilancia-guardia-
  modis.yml` l. 14 a 16 (`workflow_run ... types: [completed]`, sin mirar la conclusión de la guardia).
  SCRIPT:SALIDA: `arnes\arnes_vigilancia_salida.txt`, escenas S2 y S2b.
- QUÉ PASA: si la guardia deja de producir (secret vacío: `exit 1`, `guardia-k-modis.yml` l. 106 a 108; token vencido o
  NASA caída: `revisar_guardia_modis.py` deja el job rojo), la vigilancia corre igual, pero no lee el color del job:
  sólo la frescura de los records, con 3 días completos de tolerancia. En esos días una protegida que MIROVA publica y
  producción calla no tiene `guardia_pub` y no es candidata; queda en `protegidas_sin_publicar_produccion`, pero con
  VERDE no hay issue. Al cuarto día salta «vigilancia ciega». No se pierde para siempre si la guardia vuelve antes de 8
  días (re-procesa hoy y 7 atrás, `guardia-k-modis.yml` l. 117 a 118), pero lo prometido al OVDAS es «se vuelve atrás
  el mismo día y se avisa» (`PR_B_CUERPO.md` l. 103, TEXTO).
- CÓMO SE VE EN EL DASHBOARD: invisible; el efecto es una reversión que llega hasta tres días tarde.
- CÓMO REPRODUCIRLO: `arnes_vigilancia.py`, escena `S2_guardia_muerta_3_dias` (último dato de la guardia 2026-11-17, hoy
  2026-11-20, protegida de Chillán 2026-11-18 06:40 UTC que producción calla): `VERDE`, sin avisos,
  `sin_pub=[('NevadosDeChillan', '2026-11-18 06:40', False)]`. Control `S2b` (4 días): `VIGILANCIA_CIEGA` con 11 avisos.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 3.

### MA172-204

- TÍTULO: si la referencia de MIROVA deja de traer MODIS pero sigue con VIIRS, la vigilancia de la guardia queda ciega y
  da VERDE
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py` l. 395 a 406 (`avisos_referencia` mide la frescura sobre TODAS las
  filas, sin separar sensor), usada por `scripts/vigilancia_guardia_modis.py` l. 366. SCRIPT:SALIDA:
  `arnes\arnes_vigilancia_salida.txt`, escena S4.
- QUÉ PASA: la vigilancia sólo dispara donde MIROVA publicó una alerta MODIS. Si el scraper de Mirova-v1 o la tabla de
  MIROVA dejan de traer MODIS (fin de misión de Terra o Aqua, cambio del sitio), las filas VIIRS mantienen fresca la
  referencia y no hay alertas MODIS contra las cuales comparar: VERDE indefinido.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `arnes_vigilancia.py`, escena `S4_referencia_sin_modis_desde_08nov` (filas MODIS cortadas desde el
  2026-11-08, VIIRS diario, pasada de Chillán 2026-11-18 06:40 UTC que la guardia publica y producción calla): `VERDE
  ... alertas=0/0`, sin avisos.
- CONFIANZA: CONFIRMADO el mecanismo; SOSPECHA sobre cuándo podría pasar (no verifiqué fechas de fin de MODIS).
- GRAVEDAD 1-5: 3.

### MA172-205

- TÍTULO: tras una reversión, la marca del tablero sigue diciendo que MODIS viene de la vía y el escalón de vuelta a K
  queda sin marca
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js` l. 152 a 167 (`primeraViaModis`: primera pasada de la vía con una de K
  antes, sin fin) y l. 169 a 176 (texto «Desde el ... la serie de MODIS viene de la vía ... que reemplazó al detector
  K»); `PR_B_CUERPO.md` l. 65 a 68 (el revert deja el PR A en pie). SCRIPT:SALIDA: `tablero\marca_modis_salida.txt`,
  caso C.
- QUÉ PASA: el día de la reversión la magnitud de MODIS vuelve a bajar (con K, Chillán queda en 0,56 de MIROVA según la
  regla, l. 19). El revert del PR B no toca la marca (vive en el PR A) y la marca sale de los datos: los records de la
  vía quedan en `data/mirova_equivalent/` y los nuevos de K van sin la clave. La línea del encendido y su texto siguen,
  y el escalón de bajada no tiene marca. El cuerpo del PR B reconoce que la marca «sigue en la primera pasada de la vía»
  (l. 68), no que su texto pasa a ser falso.
- CÓMO SE VE EN EL DASHBOARD: en Chillán, una caída de la magnitud de MODIS en la fecha de la reversión sin aviso, que se
  lee como «la erupción declina»: el error que la marca de S153 vino a evitar (`cambio_detector.js` l. 6 a 7).
- CÓMO REPRODUCIRLO: `node D:\vrp-trabajo\temporales\s172_miniaud\f2\tablero\marca_modis.js`, caso
  `C_K_via_reversion_K` (K hasta el 2026-11-04, vía del 05 al 14-nov, K desde el 15-nov): marca
  `2026-11-05T05:30:00.000Z` y el texto completo de la vía.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 3.

### MA172-206

- TÍTULO: el «encendido desde los datos» cae hasta ~4,5 días ANTES del merge: el upgrade NRT a estándar re-escribe con
  la vía pasadas viejas y hereda el `first_processed_utc` de K
- ARCHIVO:LÍNEA: `pipeline/store.py` l. 677 a 684 (todo reemplazo hereda `first_processed_utc`) y l. 686 a 700 (el
  upgrade `nrt` a `standard` reemplaza sin `--overwrite`); `scripts/vigilancia_guardia_modis.py` l. 86 a 102 (encendido =
  mínimo `first_processed_utc` de los records de la vía) y l. 33 a 36 (docstring: «Como la primera corrida del NRT
  llega después del merge, las pasadas entre el merge y esa corrida quedan del lado retrospectivo», TEXTO);
  `PR_B_CUERPO.md` l. 43 a 44 («no hay reproceso histórico (la vía corre desde el merge hacia adelante)», TEXTO) y
  l. 98. SCRIPT:SALIDA: `arnes\medir_upgrade_desde_2026-10-15.txt`, `arnes\arnes_vigilancia_salida.txt` (S6, S6b),
  `tablero\marca_modis_salida.txt` (caso D).
- QUÉ PASA: casi toda pasada MODIS se escribe dos veces: primero con el gránulo NRT de LANCE y horas o días después con
  el estándar. Medido en `data/mirova_equivalent/` del PR B (records MODIS observados del 2026-10-15 al 2026-11-01 con
  `first_processed_utc`): 418 de 442 se reemplazaron después de su primera escritura, atraso mediano 13,7 h, p90
  55,6 h, máximo 108,7 h. Tras el merge esos reemplazos los hace la vía, sobre pasadas de hasta ~4,5 días antes, y
  heredan la fecha de K. Consecuencias: (a) el encendido que calcula la vigilancia queda antes del merge (al revés de lo
  que dice el docstring), una pasada observada antes del merge pasa a prospectiva y puede dar REVERSIÓN CANDIDATA
  pre-autorizada, contra la regla: «Lo anterior se informa como retrospectivo y no dispara»
  (`REGLA_REVERSION_MODD_BORRADOR.md` l. 93 a 94, TEXTO); el plazo de 120 días también se corre; (b) la marca del
  tablero queda en la primera pasada re-escrita y retrocede durante unos días, y valores ya vistos cambian; (c) el aviso
  al OVDAS fecha el escalón en «[fecha del merge]» y el cuerpo del PR dice que no hay reproceso, cuando el escalón
  empieza días antes.
- CÓMO SE VE EN EL DASHBOARD: en los días que siguen al merge, valores de MODIS de días anteriores que cambian y una
  línea naranja que retrocede de fecha.
- CÓMO REPRODUCIRLO: `python arnes\medir_upgrade.py 2026-10-15`; `arnes_vigilancia.py` escenas `S6` (encendido calculado
  `2026-10-31 09:40:00` con merge simulado el 2026-11-05 21:00) y `S6b` (protegida de Chillán 2026-11-03 06:40 UTC,
  anterior al merge, re-escrita por la vía: `REVERSION_CANDIDATA`); `node tablero\marca_modis.js`, caso D (marca en
  `2026-11-01T05:30Z`).
- CONFIANZA: CONFIRMADO (mecanismo leído, atraso medido en los datos, efecto medido en el arnés).
- GRAVEDAD 1-5: 2. No esconde pérdidas (las adelanta), pero la regla diría una cosa y el código otra, y el aviso al OVDAS
  fecha mal el escalón.

### MA172-207

- TÍTULO: la regla de reversión cuenta desde `CAMBIO_DETECTOR_MODIS_UTC` (la hora del merge) y esa constante no existe;
  el código usa otra frontera
- ARCHIVO:LÍNEA: `REGLA_REVERSION_MODD_BORRADOR.md` l. 93 («**Cuenta desde el encendido** (`CAMBIO_DETECTOR_MODIS_UTC`,
  la hora del merge al segundo)», TEXTO, rama `loop/activo`); `git grep -n CAMBIO_DETECTOR_MODIS_UTC b42823194 -- .`
  da 0 líneas; el diseño la reemplazó por la fecha de los datos (`docs/superpowers/specs/2026-11-01-encendido-modd-
  design.md`, decisión 3, en `c83882fcf`).
- QUÉ PASA: el borrador que se va a sellar y el código que lo implementa no miden desde el mismo instante (la diferencia
  real va en sentido contrario al que supone el diseño, MA172-206). Sellado tal cual, el disparador sellado no es el
  implementado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el `git grep` de arriba y `git show
  loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md | sed -n 93,94p`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2.

### MA172-208

- TÍTULO: el nulo de la guardia con 0 pares no avisa: si el PR A y el PR B entran casi juntos, el «nulo medido» no se
  mide y la vigilancia dice VERDE
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 232 a 248 (cuenta pares sólo con producción sin la marca de la
  vía; `pares == 0` no produce aviso) y l. 267 (sólo `distintas` cambia el veredicto). SCRIPT:SALIDA:
  `arnes\arnes_vigilancia_salida.txt`, escena S5.
- QUÉ PASA: el diseño promete que dejar correr la guardia antes del PR B da «el nulo medido de la guardia (A110),
  gratis»; el cuerpo del PR B lo recomienda (l. 89 a 90) pero nada lo exige. Si la guardia arranca con el encendido, la
  ventana del nulo no tiene pares (y por MA172-206 las pasadas de los últimos días ya son de la vía) y sale VERDE, igual
  que un nulo sano: un cero que no distingue «no hay diferencias» de «no medí».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `arnes_vigilancia.py`, escena `S5_nulo_sin_pares_guardia_desde_encendido`: `VERDE ...
  nulo={'pares': 0, 'distintas': 0}`, sin avisos. Control `S9` (todo sano): `nulo={'pares': 143, 'distintas': 0}`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2.

### MA172-209

- TÍTULO: el «1,1 a 1,25 veces K» no es una medición de la vía de MODIS; el margen contra el paso de 50 min está medido
  para K y supuesto para la vía; VR172-04 (paso compartido entre sensores) se confirma
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml` l. 179 y 195 (un solo `run_pipeline.py` con todos los sensores bajo
  `timeout-minutes: 50`) y l. 332 a 333 (el commit no lleva función de estado, así que GitHub le aplica `success()` y
  tras un timeout no corre: se pierden los records de esa corrida en los tres sensores del volcán);
  `REGLA_REVERSION_MODD_BORRADOR.md` l. 138 a 139 («la vía cuesta 1,1 a 1,25 veces K, pre-mortem 171-03», TEXTO);
  origen en `D:\vrp-trabajo\temporales\audit_s171_dia3\INFORME.md` l. 44 («Láscar 13,3 min contra 10,7 y 11,9 en el
  NRT de hoy», TEXTO). SCRIPT:SALIDA: `tiempos\api_jobs_40945613044.tsv`, `tiempos\api_jobs_41034796854.tsv`,
  `tiempos\log_lascar_40945613044.txt`, `tiempos\log_lascar_41034796854.txt`, `tiempos\nrt_pasos_resumen.txt`.
- QUÉ PASA: el factor sale de UNA corrida de la sombra de Láscar (run 40945613044, paso 20:05:22 a 20:18:43 UTC =
  13,35 min, ventana 2026-10-21 a 10-28, modo medir) que corre las TRES vías (V750, V375 y MODIS), contra dos jobs del
  NRT. La otra corrida de la sombra de Láscar (run 41034796854, 8,6 min) tuvo ventana de 3 días (2026-10-28 a 10-30) y
  no compara. El paso de K de Láscar varía solo entre 10,0 y 16,3 min en 6 corridas verdes del NRT del 2026-11-01
  (`tiempos\nrt_pasos_resumen.txt`): 13,35 cae dentro de ese ruido (razón 0,82 a 1,34). No hay medición del costo de la
  vía de MODIS, y Láscar es de los volcanes más rápidos (Chaitén 15,4 a 20,3 min en las mismas 6 corridas; Chillán 14,0
  a 20,5). Con estos números el margen no parece en riesgo (20,5 × 1,25 = 25,6 contra 50), pero es aritmética sobre un
  factor sin respaldo, no medición.
- CÓMO SE VE EN EL DASHBOARD: si un paso pasara de 50 min, ese volcán perdería los records de la corrida en MODIS y en
  VIIRS hasta la corrida siguiente (la ventana de 8 días los recupera).
- CÓMO REPRODUCIRLO: `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/40945613044/jobs` y
  `.../41034796854/jobs` (job «process (Lascar)», paso «Run VRP pipeline»); logs de esos jobs (`VRP_START`,
  `VRP_END`); `gh api "repos/MendozaVolcanic/VRP-chile/actions/workflows/nrt.yml/runs?per_page=12&status=success"` y
  los jobs de las 6 primeras (41353423746, 41327034950, 41305194107, 41300697146, 41296298732, 41290080234).
- CONFIANZA: CONFIRMADO el origen del factor y VR172-04 (leído y medido); SOSPECHA el costo real de la vía (nadie lo
  midió).
- GRAVEDAD 1-5: 2.

### MA172-210

- TÍTULO: la caída de la vía a K por gránulo no se ve en el tablero; la marca afirma que toda la serie MODIS es de la vía
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js` l. 160 a 162 (los records con `via_codigo_mirova` de texto no cuentan ni
  como vía ni como K) y l. 172 a 175 (texto); `pipeline/process_modis.py` l. 641 a 650 (`sin_grilla`, `sin_mxd03`,
  `geo_distinta` siguen con K). SCRIPT:SALIDA: `tablero\marca_modis_salida.txt`, caso E.
- QUÉ PASA: cuando la vía no puede correr en un gránulo, ese record es de K, con la magnitud más baja de K, intercalado
  entre records de la vía. El tablero no distingue el punto y el aviso dice que desde la fecha la serie es de la vía: un
  punto bajo suelto en Chillán se puede leer como una baja del volcán.
- CÓMO SE VE EN EL DASHBOARD: puntos MODIS bajos sueltos después de la línea naranja, sin rótulo.
- CÓMO REPRODUCIRLO: `node tablero\marca_modis.js`, caso `E_via_con_caidas_a_K`: la marca y el texto no cambian.
- CONFIANZA: CONFIRMADO el comportamiento de la marca; SOSPECHA la frecuencia de `sin_mxd03` en el NRT (SIN DATO).
- GRAVEDAD 1-5: 1.

### MA172-211

- TÍTULO: diferencias transitorias de versión de producto entre guardia y producción pueden dar INVESTIGAR falsos en el
  nulo
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 236 a 246 (el nulo compara `pub` sin mirar
  `product_version`); `.github/workflows/guardia-k-modis.yml` l. 25 (la guardia corre una vez al día; el NRT, cada
  hora).
- QUÉ PASA: para las pasadas de las últimas horas, la guardia puede haber leído el gránulo NRT mientras producción ya
  tiene el estándar, o al revés (MA172-206: el reemplazo tarda 13,7 h de mediana). Una pasada justo en el borde del
  umbral podría publicarse en un lado y no en el otro, y el nulo pediría investigar sin que haya nada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: no lo reproduje.
- CONFIANZA: SOSPECHA.
- GRAVEDAD 1-5: 1.

(MA172-212 quedó sin uso: la suite tras el revert no dejó hallazgo propio; su resultado está en §5, «Reversión».)

## 4. SEGUIMIENTOS (fuera de mi eje)

- Para el frente 1 (consumidores del flag): `.github/workflows/nrt.yml` es un consumidor implícito de la vía (necesita
  pyproj) y no está en la lista del PR B; ver MA172-201. Confianza CONFIRMADO.
- Para el frente 3 (crons y workflows): la vigilancia de la guardia se engancha por `workflow_run` y no lee la
  conclusión del job (MA172-203); el cron de respaldo de las 22:45 corre igual. Confianza CONFIRMADO (leído).
- El lector re-sellado de V375-E (`aa3fdcf1e`) difiere de `origin/main` en 147 archivos (`git diff --stat
  14fb62030 aa3fdcf1e`: 56.865 inserciones, 103.180 borrados), o sea que la rama está atrasada respecto de main; el merge
  sobre main+A+B salió sin conflictos. No lo seguí. Confianza CONFIRMADO el número, sin juicio.
- `tests/test_guard_libro_de_pruebas_s146.py` (g1d y g2c) falla cuando el repo y el temporal de pytest están en
  unidades distintas de Windows (`scripts/libro_de_pruebas.py:322`, `os.path.relpath`): con los worktrees en D: como
  manda la memoria del proyecto, esas dos pruebas dan rojo falso en cualquier línea base local. Confianza CONFIRMADO
  (reproducido en la base y su control con `--basetemp` en D:).
- `git rev-parse loop/activo` en el repositorio compartido da `fa22f4b87` al momento de mi medición, no el `44338fb7d`
  del estado de git del arranque de la sesión que me lanzó: la rama se movió durante la auditoría. Leí la regla de
  reversión en `loop/activo` en ese momento. Confianza CONFIRMADO.

## 5. VERIFICADO LIMPIO

- Lectura del flag desde `pipeline.profile` (A89), vara: el comando del preámbulo. En el worktree del PR B:
  `ENABLE_MODIS_CODIGO_MIROVA = True` (`arnes\arnes_via_pyproj_salida.txt`, primera línea útil; también
  `ENABLE_V750_CODIGO_MIROVA = False`). En la base `d3cd0b2ae` (worktree de reversión antes de tocarlo): `False`.
- Control positivo de la vigilancia (línea base roja), vara: el disparador de §4 de la regla. Escena S0: una protegida
  que la guardia publica y producción (con record de la vía) calla da `REVERSION_CANDIDATA`. Control negativo S0b (las
  dos publican): VERDE. El arnés vive.
- La vigilancia ve, con aviso propio: guardia con 4 días sin datos (S2b), un JSON de la guardia ausente (S3: cae toda la
  guardia y avisa los 11 volcanes; el mensaje es grueso pero dispara), flag de producción encendido sin records de la
  vía (S7), flag ilegible (S8). Todo sano y sin alertas da VERDE sin avisos (S9, nulo con 143 pares).
- La marca de MODIS sale de los datos y no de una fecha fija, vara: el predicado escrito en el diseño (decisión 5). Sin
  records de la vía no dibuja nada (caso A: `null`); con K y después vía marca la primera pasada de la vía (caso B).
  Con el PR A solo (flag apagado) no hay records de la vía, así que es inerte, como declara el diseño.
- El JSON liviano `_recent` que cargan las tres vistas conserva el record entero, incluida la clave de la vía:
  `scripts/build_recent_json.py` l. 51 a 61 (`filter_recent` sólo filtra por fecha, copia los records sin tocarlos).
- Un record de la vía pasa el predicado del tablero (node, `index.html` del PR B): `[1, 1, 0, 8.962, 1]` (summit,
  válido, no artefacto, magnitud mostrada, publica) para el gránulo sintético de Láscar.
- Reversión, vara: «`git revert` del merge del PR B sobre el main del día, sin conflictos y con las pruebas verdes».
  Sin conflictos en las cuatro simulaciones (en `D:\vrp-trabajo\worktrees\s172-miniaud-rev`, sin push): (1) base
  `d3cd0b2ae` + merge commit de A + merge commit de B + `git revert -m 1` (`revert\sim1_merge_commit_base.txt`; el árbol
  del revert es idéntico al de main+A); (2) lo mismo sobre `origin/main` `14fb62030` (`revert\sim2_sim3_origin_main.txt`,
  árbol idéntico); (3) squash de A y squash de B sobre `origin/main` (el repo usó squash en #925 a #931) + `git revert`
  del squash de B (árbol idéntico al de main+A); (4) `origin/main` + A + B + merge del re-sellado `aa3fdcf1e` + merge de
  `loop/activo` (`fa22f4b87`) + `git revert -m 1` del merge de B: sin conflictos (`revert\sim4_ramas_pendientes.txt`).
  La parte «pruebas verdes»: suite completa, una sola corrida, sobre el revert de la simulación 2 (`a1dad755c`,
  `revert\suite_head.txt`): `2 failed, 2888 passed, 31 skipped, 2 xfailed ... in 421.79s`
  (`revert\suite_tras_revert.txt` y `.xml`). Las dos rojas son
  `tests/test_guard_libro_de_pruebas_s146.py::test_g1d_mutacion_prueba_que_g1_de_verdad_falla` y `::test_g2c_...`, con
  `ValueError: path is on mount 'C:', start on mount 'D:'` (`scripts/libro_de_pruebas.py:322`, `os.path.relpath` entre
  el temporal de pytest en C: y el worktree en D:). Regla A50: corridas sobre la base `d3cd0b2ae` dan las mismas 2 rojas
  y, con `--basetemp` en D:, 7 de 7 verdes; sobre el revert con `--basetemp` en D:, 7 de 7 verdes
  (`revert\rojas_sobre_base_d3cd0b2ae.txt`, `revert\rojas_tras_revert_basetemp_D.txt`). Son del entorno de esta
  máquina, no del revert. Pregunta 1 del instrumento: si el revert dejara una prueba rota, la suite la vería (corre
  las 2.923 pruebas colectadas); pregunta 2: el instrumento está vivo porque detectó las 2 rojas de entorno.

## 6. SIN DATO

- El costo real de la vía de MODIS en el runner (nadie lo midió; la sombra que la corre arranca en serio el 2026-11-03).
- El tamaño del escalón de magnitud en Chillán con la vía (no lo medí).
- La frecuencia de los descartes de borde 171-01 y de las caídas `sin_mxd03` en MODIS de producción (no hay records de la
  vía en el repo: 0 en `data/mirova_equivalent/`, contados con un barrido de la clave).
- Las vistas renderizadas en un navegador sin cabeza: no las cargué; mi evidencia del tablero es `cambio_detector.js` y
  el predicado de `index.html` corridos con node.
- Si GitHub avisa por correo de las corridas programadas fallidas de la guardia (relevante para MA172-203).
- Si el revert seguirá limpio el día real de la reversión: el PR B edita `CLAUDE.md`, `docs/MISSION.md`,
  `docs/MIROVA_DIVERGENCES.md` y `docs/FICHA_SDA_VRP_CHILE.md`, que cambian a menudo; hoy sale limpio incluso con las
  ramas pendientes, pero eso no garantiza el día del revert (S157: el revert de K dejó de salir limpio).

## 7. FUERA DE ALCANCE

El censo de consumidores del flag y la cobertura de pruebas de la vía (frente 1); crons, concurrencia, herencia de
perfiles y el lector de V375-E (frente 3); el detector `VIA_MODIS` del auto-audit semanal.
Hora del servidor al cerrar: Mon, 02 Nov 2026 01:09:46 GMT (`gh api -i`, cabecera `Date`).
