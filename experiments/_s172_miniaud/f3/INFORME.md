# Frente 3, mini-auditoría S172: integración entre programas del encendido de la vía «código MIROVA» en MODIS

## 1. Encabezado

- Fecha y hora del servidor: al empezar `Mon, 02 Nov 2026 00:46:15 GMT`; al redactar `Mon, 02 Nov 2026 01:03:18 GMT`
  (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date`).
- Objeto medido, fijado por hash:
  - base `d3cd0b2aeee70b99fbc5bd90e5fd2b0dff284f54` (tag `pre-s171-adopcion-modd`); `origin/main` al medir:
    `14fb62030a186fda02ce2ba172866cf01408eeb9` (`git ls-remote origin main`).
  - PR A: rama `claude/s172-modd-encendido`, punta `c83882fcfdbd7fdb441e61a54a03c8f5fb3707b2`.
  - PR B: rama `claude/s172-modd-flip`, punta `b4282319446cfea944aa1a4621c0fec7da8649a0`. Verificado: el padre del
    primer commit de B (`479a30c18`) es `da67fa417`; `git merge-base c83882fcf b42823194` = `da67fa417...`, o sea que
    `c83882fcf` (informe del implementador y salida de pruebas, 2 archivos) no está en la historia de B.
  - «A más B» = el worktree de sólo lectura `D:/vrp-trabajo/worktrees/s172-miniaud-b` en `b42823194` (contiene los
    commits de A hasta `da67fa417` y los tres de B).
  - Lector de V375-E re-sellado: rama `claude/s172-v375e-relector`, punta `aa3fdcf1e`.
- Modelo y esfuerzo: pedido Opus, esfuerzo alto. Corrí como Claude Opus 5.5 (`claude-opus-5-5`); el esfuerzo de
  razonamiento efectivo de esta sesión fue bajo, no alto (lo declaro porque el pedido decía alto).
- Python: `C:/Users/nmend/AppData/Local/Programs/Python/Python312/python` 3.12.10 (el `python` del PATH, no el de
  Anaconda que nombra el material); node v22.16.0.
- CARPETA: `D:/vrp-trabajo/temporales/s172_miniaud/f3`. Scripts y salidas al lado (`m*.py`, `m*.out`, `m*.json`,
  `m6_marcas_tablero.js`, `s8/`, `ctl_g4/`, `base_tree/`).
- Qué NO miré (mi silencio no es «todo bien»): el censo de consumidores y la cobertura de pruebas de la vía (frente 1);
  lo que ve el operador, la regla de reversión, el tiempo del NRT y la simulación del revert (frente 2); el cálculo
  físico de la vía (`pipeline/mirova_v750_codigo.py`) más allá de su dependencia de `pyproj`; `store.py` con records de
  la vía; las vistas `index.html`, `diario.html` y `mosaico.html` en un navegador real (las marcas se midieron en node
  con DOM y canvas de prueba); el contenido de los issues abiertos hoy en GitHub; la batería entera
  `probar_sombra.py` y `mutar_sombra.py` (corrí el S8 y el S0 aparte, ver abajo).

## 2. En una pantalla

1. **El NRT no instala `pyproj` y la vía lo importa**: con el PR B, cada gránulo MODIS que cubre el volcán falla con
   `ModuleNotFoundError`, `run_pipeline` lo atrapa, no escribe record y el job sale verde. MODIS de producción se queda
   mudo en los 11 volcanes (MA172-301, CONFIRMADO, gravedad 4). El CI no lo ve porque instala `requirements.txt`.
2. **La vigilancia de la sombra de K (S156) toma los records MODIS de la vía por K**: una protegida MODIS que C0
   publica y la vía calla abre «Sombra de K: candidata a reversion» y manda revertir K (#850), no el PR B (MA172-302,
   CONFIRMADO con las funciones reales, gravedad 3).
3. 55 perfiles derivados pasan en silencio de vía apagada a encendida (MA172-303); el audit semanal tras un revert del
   PR B deja de evaluar las noches MODIS sin aviso (MA172-304); los cron reales llegan 4 a 5,7 h tarde y el argumento de
   horarios de la guardia no se sostiene (MA172-305).
4. Limpio: G4 y G5 miran los workflows nuevos y G4 falla con un mutante; el S8 del lector de V375-E pasa con A más B y
   marca en 7 casos construidos para fallar; la sombra de V750 no cambia de valor; las tres marcas del tablero conviven.

## 3. Hallazgos (lo peor primero)

### MA172-301

- TÍTULO: Con el PR B, el NRT corre la vía de MODIS sin `pyproj`: todo gránulo MODIS que cubre el volcán falla en
  silencio y producción deja de escribir MODIS
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:143` (`pip install earthaccess numpy h5py scipy pyyaml`, sin `pyproj`);
  `pipeline/process_modis.py:637` (`if ENABLE_MODIS_CODIGO_MIROVA:`) y l. 652 (`_MV.calcular_vrp_granulo(`);
  `pipeline/mirova_v750_codigo.py:814` (`remuestrear_grilla(...)` dentro de `calcular_vrp_granulo`) y l. 204
  (`from pyproj import Transformer`); `scripts/run_pipeline.py:279-280` (`except Exception as e:` /
  `print(f"  ERROR processing {l1b.name}: {e}")`). SCRIPT:SALIDA `m6_pyproj_nrt.py` → `m6_pyproj_nrt.out`;
  `m6_nrt_job_log.txt` l. 451; `m6_workflows_run_pipeline_pyproj.out`.
- QUÉ PASA: el volcán sigue emitiendo igual, pero la serie MODIS del tablero deja de recibir pasadas nuevas: la vía
  necesita pasar el gránulo a la grilla UTM de MIROVA y para eso importa `pyproj`, que el runner del NRT no tiene. La
  excepción ocurre dentro de `calculate_vrp`, antes de la caída a K (la caída sólo cubre «sin grilla», «sin MxD03» y
  «geo distinta», l. 642 a 650), así que no hay record ni de la vía ni de K; `run_pipeline` imprime `ERROR processing`
  y sigue, y `nrt.yml` no tiene un paso que revise ese texto (su único `grep` es `NASA_AUTH_UNREACHABLE`, l. 248), así
  que el job queda verde. El propio repositorio ya lo sabía para la sombra: `sombra-codigo-mirova.yml:90` dice «la via
  lo usa para pasar el granulo a la grilla UTM de MIROVA (remuestrear_grilla); el NRT no lo instala», y la guardia
  (`guardia-k-modis.yml:90`) dice «la guardia es K: no corre la via, asi que no necesita pyproj (las mismas
  dependencias que el NRT)». El PR B no toca `nrt.yml` (`git diff --stat da67fa417 b42823194` no lo lista) y ninguna
  prueba lo vigila; `tests.yml:42` instala `requirements.txt`, que sí trae `pyproj>=3.5`, así que el CI pasa.
- CÓMO SE VE EN EL DASHBOARD: desde el primer ciclo NRT tras el merge, ninguna pasada MODIS nueva en los 11 volcanes;
  las barras MODIS de los días previos quedan con lo que escribió K (nadie las reemplaza) y la marca naranja de la vía
  no aparece (no hay records con `via_codigo_mirova: true`). El operador ve VIIRS y nada nuevo de MODIS, sin aviso en
  el tablero. Quien lo delata es la vigilancia de la guardia: `scripts/vigilancia_guardia_modis.py:304-306` abre
  «Guardia K de MODIS: vigilancia ciega» cuando el flag está encendido y no hay ningún record de la vía (no lo corrí
  sobre datos reales; leí el código).
- CÓMO REPRODUCIRLO: `python -B D:/vrp-trabajo/temporales/s172_miniaud/f3/m6_pyproj_nrt.py` (con `pyproj` disponible
  remuestrea a 51 × 51 en Láscar; con `pyproj` bloqueado: `ATRAPADA por except Exception: ModuleNotFoundError: import
  of pyproj halted`). Evidencia del runner: log del job 124988304474 del run 41353423746 de `nrt.yml` (schedule,
  2026-11-01 21:42:59 UTC, sha `ffccf6c9f`), l. 451 «Successfully installed ...» sin `pyproj`
  (`gh api repos/MendozaVolcanic/VRP-chile/actions/jobs/124988304474/logs`). Volcán y pasada: cualquiera de los 11,
  cualquier pasada MODIS nocturna posterior al merge del PR B. Las dos preguntas: (1) si la vía corriera sin `pyproj`,
  el caso bloqueado devolvería arrays; (2) control positivo: el mismo llamado con `pyproj` remuestrea. Lo que NO medí:
  una corrida real de `nrt.yml` con el flag encendido (prohibido despachar workflows); que `pyproj` no venga ya en la
  imagen `ubuntu-24.04` de `setup-python` lo infiero del log (no aparece en lo instalado), no lo comprobé importándolo
  en el runner.
- CONFIANZA: CONFIRMADO (dependencia ausente leída en el log real del NRT y en `nrt.yml`; el import y su captura,
  medidos).
- GRAVEDAD 1-5: 4. Apaga MODIS de producción entero, sin error, el mismo día del encendido; la alerta protegida que
  sólo MODIS ve (el caso que el encendido quiere ganar) no se publica. No llega a 5 porque VIIRS sigue y la vigilancia
  de la guardia debería abrir un issue de vigilancia ciega en su primera corrida.

### MA172-302

- TÍTULO: La vigilancia de la sombra de K (S156) cuenta los records MODIS de la vía como K: tras el encendido puede
  pedir revertir K (#850) por una pérdida de la vía, o pedir dos reversiones distintas para la misma pasada
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py:432` (`prod = [r for r in bp.cargar_nuestros(coords, inner, win) if
  r.get("sha")]   # sólo records de K`); `pipeline/store.py:89-94` (`_marca_regimen` pone `codigo_sha` en todo record,
  también en los de la vía); `scripts/vigilancia_sombra.py:132-177` (pareo por volcán y sensor, MODIS incluido,
  `aa.SENSORS` en `scripts/auto_audit_weekly.py:118`); `.github/workflows/vigilancia-sombra.yml:134-135` (título «Sombra
  de K: candidata a reversion» y «pre-autoriza revertir K con git revert del PR de adopcion»). SCRIPT:SALIDA
  `m5_vigilancias_cruzadas.py` → `m5_vigilancias_cruzadas.out`.
- QUÉ PASA: la sombra C0 sigue mirando MODIS con el detector anterior, pero lo que compara contra ella como
  «producción (K)» pasa a ser la vía. Si MIROVA publica una protegida MODIS que C0 ve y la vía calla, la vigilancia de K
  la lee como «K perdió lo que C0 veía» y abre el issue que pre-autoriza revertir el PR de K. Con la guardia K también
  callando (E2), es el único issue que se abre y apunta al PR equivocado: revertir #850 no apaga la vía. Con la guardia
  publicando (E1), se abren dos issues de reversión pre-autorizada para la misma pasada, uno por cada PR. El plazo de
  K sigue vigente (adopción 2026-10-18 09:57:30 + 120 días). El diseño dice que `vigilancia_sombra.py` «vigila K» y no
  se modifica (`docs/superpowers/specs/2026-11-01-encendido-modd-design.md` l. 46-47), y el PR B protege su lado de la
  sombra (`experimental` en false) pero no su lado de producción. Los títulos no chocan entre sí («Sombra de K:» y
  «Guardia K de MODIS:», deduplicados por prefijo exacto), así que nada fusiona los dos avisos.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero; se ve en GitHub como un issue «Sombra de K: candidata a
  reversion» que nombra una pasada MODIS, con la instrucción de revertir K.
- CÓMO REPRODUCIRLO: `python -B D:/vrp-trabajo/temporales/s172_miniaud/f3/m5_vigilancias_cruzadas.py` (funciones
  reales del worktree A más B; Nevados de Chillán MODIS 2026-11-10 07:20 UTC, 2,18 MW sintético, encendido supuesto
  2026-11-05 22:10, hoy 2026-11-20). Salida: E0 (la vía publica) VERDE en las dos; E1 REVERSION_CANDIDATA en las dos;
  E2 REVERSION_CANDIDATA sólo en la de K; E3 (control positivo, VIIRS 375, donde producción sigue en K)
  REVERSION_CANDIDATA en la de K, que ahí es correcta. En los cuatro, el filtro de la l. 432 acepta 1 de 1 record de
  producción como K, también el que trae `via_codigo_mirova: true`. Las dos preguntas: (1) si la vigilancia
  distinguiera detectores, E2 daría VERDE en la de K; (2) E0 y E3 muestran que el instrumento puede dar los dos
  resultados. Lo que NO medí: sobre datos reales (aún no hay records de la vía en producción).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 3. Tuerce la decisión de reversión: un issue pre-autorizado puede llevar a revertir K en VIIRS (el
  detector que sigue bien) por una pérdida de la vía en MODIS. Lo modera que la regla pide confirmar en la cabecera de
  la imagen de MIROVA y que lo ejecuta una persona.

### MA172-303

- TÍTULO: 55 perfiles derivados pasan de la vía de MODIS apagada a encendida sin que nadie lo escriba, entre ellos
  varios con «k» en el nombre, y sus workflows de despacho no instalan `pyproj`
- ARCHIVO:LÍNEA: `pipeline/profile.py:48-66` (`extends` con mezcla profunda) y l. 909; `pipeline/profiles/
  mirova_equivalent.yaml` (línea nueva `enable_modis_codigo_mirova: true` en `thresholds:`). SCRIPT:SALIDA
  `m1_herencia_perfiles.py` → `m1_herencia_perfiles.out` y `.json`; `m6_workflows_run_pipeline_pyproj.out`.
- QUÉ PASA: un brazo de A/B o una sonda que se vuelva a correr después del merge ya no mide lo que medía: en MODIS
  corre la vía. Resuelto con el cargador real, de 101 perfiles (100 en la base), 57 tienen
  `ENABLE_MODIS_CODIGO_MIROVA` distinto entre base y A más B: `mirova_equivalent` (escrito), `guardia_k_modis` (nuevo,
  False) y 55 que heredan sin escribirlo, todos con `extends: mirova_equivalent` (54 brazos y sondas `_s*`/`_f70_*` más
  `experimental_lowT`). Ningún otro flag vecino cambia (V750, V375, los tres de MxD03, banda 22, Test 1 y conectiva
  iguales). Con nombre que promete K: `_s154_reproc_k_historico` (su yaml dice «IDENTICO A LA REPLICA», l. 8, y su
  workflow es `reproc-chunked.yml`), `_s154_ab_diurno_k_control` y `_s154_ab_diurno_k_on`, `_s150_k_etiqueta`,
  `_s150_k_etiqueta_sin_tope`; los cuatro `_s157_ab_d25_k_*` heredan True pero corren sin MODIS (`SENSOR_MODIS=False`).
  Es una decisión declarada («Los brazos viejos de A/B ... no se tocan: sus workflows son de despacho manual y ya
  corrieron», `experiments/_s171_modd_adopcion/PR_B_CUERPO.md` l. 35-36), y el guard nuevo cubre sólo los perfiles
  que nombra un workflow programado (`tests/test_guard_modis_codigo_mirova_encendido_s172.py:98-110`). Lo que la
  decisión no dice: los 9 workflows de despacho que corren esos perfiles (`reproc-chunked`, `reproc-s120`,
  `reproc-s124-villarrica-op-ab`, `reproc-s135-ab-d1d2`, `reproc-s143-ab-d22d25`, `reproc-s146-ab-sin-test1`,
  `reproc-s151-ab-caja`, `reproc-s151-ab-diurno`, `probe-s157-busqueda-ventana`) no instalan `pyproj`
  (`m6_workflows_run_pipeline_pyproj.out`, 0 en todos), así que despachados hoy darían MODIS vacío y verde por la
  misma vía que MA172-301. Además, `tests/test_guard_perfiles_congelados_s153.py:40-42` exige a todo derivado declarar
  sólo los tres flags de K, no el de la vía: «congelado en K» ya no implica K en MODIS.
- CÓMO SE VE EN EL DASHBOARD: invisible (son perfiles no operacionales, en carpetas propias).
- CÓMO REPRODUCIRLO: `python D:/vrp-trabajo/temporales/s172_miniaud/f3/m1_herencia_perfiles.py` (carga el
  `profile.py` de cada árbol con `VRP_PROFILE=<perfil>` en `python -I`). Control positivo: `mirova_equivalent` cambia
  False → True; 0 errores de carga en 201 resoluciones; `sombra_codigo_mirova` sale True en los dos árboles.
- CONFIANZA: CONFIRMADO (los valores); el uso futuro de esos perfiles es SOSPECHA.
- GRAVEDAD 1-5: 2. No toca producción; tuerce la lectura de un A/B o un reproceso que alguien despache después del
  merge creyendo que mide K en MODIS.

### MA172-304

- TÍTULO: El audit semanal deja fuera, sin aviso, los records MODIS de K que caen en noches de la vía: tras un revert
  del PR B las noches MODIS nuevas no se evalúan, y antes del revert tampoco las caídas a K de la vía
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:471-475` (`frontera_via_modis`: la fecha mínima de cualquier record
  de la vía), l. 432-437 (`detector_de_noche`: noche MODIS desde esa fecha = `VIA_MODIS`), l. 655-657 (`if d_rec !=
  d_noche: fuera[...] += 1; continue`), l. 1138-1147 (sólo hay aviso para «K en noche C0», no para «K en noche
  VIA_MODIS»). SCRIPT:SALIDA `m5b_audit_tras_reversion.py` → `m5b_audit_tras_reversion.out`.
- QUÉ PASA: si se revierte el encendido, el NRT vuelve a escribir K en MODIS, pero la frontera de la vía queda fija en
  la primera pasada de la vía que siga en los datos; desde ahí toda noche MODIS es «de la vía» y los records de K de esas
  noches se descartan del recall y la magnitud. En la escena (Láscar, vía del 5 al 9 de noviembre y K del 10 al 14)
  quedan 5 de 10 noches vistas y `fuera_de_detector={'K en noche VIA_MODIS': 5}`; sin la vía, 10 de 10. Lo mismo, en
  menor escala, para las caídas a K de la vía mientras siga encendida (`via_codigo_mirova` = `"sin_grilla"`,
  `"sin_mxd03"`, `"geo_distinta"`): son records que el tablero publica y el audit no evalúa. El docstring lo reconoce
  («quedan en `fuera_de_detector`: ese día cambia también», l. 446-447) y el cuerpo del PR B también (l. 67-68), pero
  ningún aviso degrada el veredicto y el semanal no dice que MODIS dejó de medirse.
- CÓMO SE VE EN EL DASHBOARD: invisible; el issue semanal pierde la medición de MODIS (o lo deja con n menor) sin
  decirlo.
- CÓMO REPRODUCIRLO: `python -B D:/vrp-trabajo/temporales/s172_miniaud/f3/m5b_audit_tras_reversion.py`. Control: el
  escenario sin la vía da 10 de 10 noches vistas y 0 fuera. Lo que NO medí: el veredicto entero del audit (sólo
  `nuestros_por_noche`) ni cuántas caídas a K habrá (SIN DATO: aún no hay records de la vía).
- CONFIANZA: CONFIRMADO (mecanismo); el efecto sobre el veredicto semanal es SOSPECHA.
- GRAVEDAD 1-5: 2. Tras un revert, el instrumento que mira MODIS semana a semana queda ciego en MODIS justo cuando más
  hace falta mirar.

### MA172-305

- TÍTULO: Los cron reales llegan 4 a 5,7 h tarde: la separación de horarios que justifica las 17:40 de la guardia no
  existe, y la guardia se va a solapar con el laboratorio, la sombra y el NRT
- ARCHIVO:LÍNEA: `.github/workflows/guardia-k-modis.yml:15-18` («17:40 queda despues de la sombra y en un minuto que no
  usa ningun otro cron») y l. 25; `.github/workflows/experimental-diario.yml:21` (`0 14 * * *`);
  `.github/workflows/sombra-codigo-mirova.yml:25` (`0 15 * * *`). SCRIPT:SALIDA `m2_duraciones_runs.out`,
  `m2_barrido_workflows.out`.
- QUÉ PASA: GitHub arranca los cron cuando puede. En los 8 últimos runs programados, `experimental-diario` (cron 14:00)
  empezó entre 17:21 y 19:41 UTC y la sombra (cron 15:00) entre 19:09 y 19:52 UTC (3 runs programados con dato). Si la
  guardia se atrasa igual, arrancará hacia las 21:40 a 23:30 UTC con 11 jobs en tandas de 4 (hasta 75 min de paso
  cada uno), encima del laboratorio (4 en paralelo, 55 a 86 min de run observados), de la sombra y del NRT horario
  (8 en paralelo). El test que fija la hora (`tests/test_guardia_k_modis_s172.py`, citado en l. 18) mide el minuto
  declarado, no el arranque real. El cron de respaldo de la vigilancia (22:45) caería de madrugada; su disparo
  principal es `workflow_run`, que no depende del reloj.
- CÓMO SE VE EN EL DASHBOARD: invisible salvo que el solapamiento atrase un ciclo del NRT (SOSPECHA: con 8 del NRT,
  4 del laboratorio, 4 de la sombra y 4 de la guardia se llega a 20 jobs simultáneos; no verifiqué el límite de jobs
  concurrentes de la cuenta ni medí colas).
- CÓMO REPRODUCIRLO: `gh api "repos/MendozaVolcanic/VRP-chile/actions/workflows/experimental-diario.yml/runs?per_page=8"
  --jq '.workflow_runs[] | [.event, .run_started_at, .updated_at, .conclusion] | @tsv'` (y lo mismo con
  `sombra-codigo-mirova.yml`).
- CONFIANZA: CONFIRMADO (el atraso de los cron vecinos); SOSPECHA (que la guardia se atrase igual y el efecto del
  solapamiento).
- GRAVEDAD 1-5: 2. La vigilancia del mismo día sigue llegando (por `workflow_run`), pero la carga de LANCE y de runners
  a esa hora no es la que el diseño supuso.

### MA172-306

- TÍTULO: Si la vía de MODIS empieza el mismo minuto que el cese de Suomi NPP, las dos líneas verticales caen en el
  mismo píxel y la del cese se dibuja encima
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js:241-256` (línea naranja `[6, 3]`, rótulo en `area.top + 34`);
  `frontend/cese_plataformas.js:98-125` (línea azul `[2, 3]`, rótulo en `area.top + 22`; se registra después, l. 135).
  SCRIPT:SALIDA `m6_marcas_tablero.js` → `m6_marcas_tablero.out`.
- QUÉ PASA: es sólo dibujo. En C1 (vía desde 2026-11-02 13:00) las dos líneas van en x = 884 y la azul punteada queda
  sobre la naranja; los rótulos «MODIS: vía MIROVA» y «sin Suomi NPP» van a 12 px de altura de distancia y no se pisan.
  Los tres avisos aparecen en el orden K, MODIS, cese; en un gráfico de sólo VIIRS la marca de MODIS no se dibuja. Con
  la vía en otra fecha (C2, 27-oct, el re-escrito de 8 días del NRT) las líneas quedan separadas (x 813 y 884). La
  frontera de K (2025-02-15) cae fuera de 90 días y no se dibuja.
- CÓMO SE VE EN EL DASHBOARD: una sola línea de aspecto mixto en vez de dos, con los dos rótulos legibles.
- CÓMO REPRODUCIRLO: `node D:/vrp-trabajo/temporales/s172_miniaud/f3/m6_marcas_tablero.js`. Controles: ventana de
  48 h sin las fechas da 0 líneas; sin records de la vía, 1 línea (sólo el cese).
- CONFIANZA: CONFIRMADO (en node con DOM y canvas de prueba; no en navegador).
- GRAVEDAD 1-5: 1.

### MA172-307

- TÍTULO: El nulo de la guardia (guardia K contra producción K antes del encendido) puede dar diferencias que no son
  del detector, porque las dos corren a horas distintas sobre la misma pasada
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py:232-247` (pareo por pasada y comparación de `pub`);
  `.github/workflows/guardia-k-modis.yml:117-118` (ventana de 8 días, una vez al día) frente al NRT horario.
- QUÉ PASA: la producción procesa cada pasada MODIS con el producto NRT de LANCE y la sube a estándar cuando aparece;
  la guardia la procesa horas después y puede tomar otra versión. Una pasada en el borde de un umbral podría publicarse
  en un lado y no en el otro, y el nulo («deben publicar lo mismo») lo informaría como diferencia de detector.
- CÓMO SE VE EN EL DASHBOARD: invisible; a lo más un issue «Guardia K de MODIS: investigar» por el nulo.
- CÓMO REPRODUCIRLO: no lo reproduje; habría que parear `product_version` de `data/guardia_k_modis/` contra
  `data/mirova_equivalent/` tras unos días de guardia corriendo.
- CONFIANZA: SOSPECHA.
- GRAVEDAD 1-5: 1.

## 4. SEGUIMIENTOS (fuera de mi eje)

- `pipeline/profiles/sombra_codigo_mirova.yaml:21-22` dice que `sombra-codigo-mirova.yml` «no tiene schedule», y el
  workflow tiene `cron: "0 15 * * *"` (l. 25) y corre a diario (runs del 30-oct al 1-nov). Comentario viejo. CONFIRMADO.
- `scripts/auto_audit_weekly.py:473` dice que `frontera_via_modis` «Es la misma regla que la marca de MODIS del
  tablero»; la del tablero (`frontend/cambio_detector.js:151-167`) exige además una pasada MODIS de K antes. Coinciden
  mientras el JSON completo tenga K antes de la vía; no medí cuándo divergen. SOSPECHA, frente 1 o 2.
- El borrador para `MAPA_WORKSPACE.md` del cuerpo del PR B (l. 115) dice «diario 17:40 UTC» para la guardia; el
  arranque real va a ser horas después (ver MA172-305). CONFIRMADO para los vecinos.
- La historia de PR B no contiene `c83882fcf`; cómo se mergean A y B (squash o merge) cambia qué deshace el revert.
  Frente 2.
- El material pide el Python de Anaconda; el del PATH es el de `AppData/Local/Programs/Python/Python312`. Medí con ese.

## 5. VERIFICADO LIMPIO

- **G4 mira el workflow nuevo y puede fallar.** `python -m pytest -p no:cacheprovider -q
  "tests/test_guard_declarado_vs_efectivo_s131.py::test_g4_pusher_a_main_tiene_push_main_o_retry"
  "...::test_g5_clave_on_quoted_en_todos_los_workflows"` en el worktree: `2 passed` (`m2_pytest_g4_g5.out`). El guard
  no acepta otra carpeta por argumento, pero su `ROOT` es variable de módulo y se cambia al importarlo
  (`m2_control_g4.py` → `.out`): carpeta vacía PASA con 0 pushers (no cuenta como verificación); `guardia-k-modis.yml`,
  `vigilancia-guardia-modis.yml` y `nrt.yml` reales PASAN; la guardia sin grupo ni bucle FALLA nombrándola; la guardia
  con el `git push` a más de 6 líneas del `for attempt` FALLA (borde del regex); `nrt.yml` solo (grupo `push-main`)
  PASA. Vara: la condición de G4 (grupo `push-main` o bucle de reintento), no una lista.
- **Barrido de workflows** (`m2_barrido_workflows.py` → `.out`): 52 en A más B, 50 en la base; los dos nuevos son
  `guardia-k-modis.yml` (cron 17:40, grupo propio, `git push` con `for attempt in 1 2 3 4 5` y `pull --rebase`) y
  `vigilancia-guardia-modis.yml` (cron 22:45 y `workflow_run`, grupo propio, bucle de reintento). Pushers existentes que
  ya cumplen G4: `nrt.yml`, `sync-mirova-csv.yml`, `backfill-*` (grupo `push-main`) y `audit-weekly.yml`,
  `sombra-codigo-mirova.yml`, `vigilancia-sombra.yml`, `experimental-diario.yml` (bucle). Ningún minuto de cron
  declarado choca (17:40 y 22:45 no los usa nadie más). Los archivos que pushean no se cruzan:
  `data/guardia_k_modis/<volcán>.json` y `data/audit_continuous/guardia_modis_{latest.json,history.jsonl}` frente a
  `latest.json`, `history.jsonl` y `sombra_*` (`ls data/audit_continuous/`).
- **Norway problem y autenticación**: en los 52 yml `yaml.safe_load` da la clave `"on"` como texto (ninguno como
  `True`); G5 en verde. `guardia-k-modis.yml:97` usa sólo `EARTHDATA_TOKEN` y corta si viene vacío (l. 106-109), sin
  usuario ni clave; `vigilancia-guardia-modis.yml` no toca NASA (0 credenciales). Vara: CLAUDE.md, «Todo workflow
  nuevo autentica sólo por token, falla al instante si viene vacío».
- **El `workflow_run` engancha**: `vigilancia-guardia-modis.yml:15` escucha `"Guardia K de MODIS (11 Tier A)"`, que es
  el `name:` de `guardia-k-modis.yml:1`. Títulos de issues: «Guardia K de MODIS:», «Sombra de K:», «Vigilancia de la
  sombra de K:», «⚠ Auto-audit semanal ...» y «Union historica ...»: ningún prefijo de uno es prefijo de otro, así que
  la deduplicación por `startswith` no mezcla clases (leído en los tres yml).
- **S8 del lector de V375-E, de punta a punta con su propio git** (`m3b_s8_punta_a_punta.py` → `.out`, copia por
  `git show aa3fdcf1e:...` en `s8/`): base → A más B, base → A y A → A más B dan «sin cambio» (los 6 archivos de
  `RUTAS_REGIMEN` que cambian, entre ellos `process_modis.py` sólo en comentarios y `mirova_equivalent.yaml` sólo en la
  clave de la lista, no cuentan; `guardia_k_modis.yaml`, `experimental.yaml`, `experimental_ndc_focus.yaml` y
  `_s146_ab_control.yaml` no están en `PERFILES_REGIMEN`). Puede fallar: marca régimen con la clave de la vía en la
  raíz del perfil (F1), con `enable_v375_codigo_mirova: true` (F2), con un cambio de código en `process_modis.py`
  (F3), con un umbral de la sombra (F4), con `enable_modis_b22_primary` en la raíz (F5), con el commit real
  `5b676337d` que metió la vía de 375 (F6), y con un sha inexistente (N0, «git no lo resuelve»). Por diseño no marca un
  cambio en la guardia ni en el laboratorio (I1, I2) ni apagar la vía de MODIS en la sombra (I3). Vara: §11.14 de
  `PREREGISTRO_E.md` (falla cerrada en otra sección y ante claves fuera de la lista).
- **S0 del lector**: los 16 sha256 coinciden en `aa3fdcf1e` (16 de 16) y en la base 15 de 16 (falta sólo
  `leer_posicion_v375e.py`, que vive en las ramas de experimentos); en A más B no coinciden `scripts/auto_audit_weekly.py`,
  `frontend/index.html` y `pipeline/profiles/mirova_equivalent.yaml` (`m3a_s0_sellos.py` → `.out`). No es defecto: §11.14
  dice que el S0 se calcula «sobre el checkout del lector, no sobre `main`». Queda como condición: el lector no puede
  correr sobre un checkout que tenga A o B.
- **La sombra de V750** (`sombra_codigo_mirova`): `ENABLE_MODIS_CODIGO_MIROVA` True en la base y en A más B (la escribe
  en `thresholds:`; `m1_herencia_perfiles.json`), así que el encendido no le cambia nada de lo que corre ni publica. Su
  evaluador de V750-A (`git show loop/activo:experiments/_s162_v750a/evaluar_v750a.py`) no menciona MODIS; su revisión
  (`scripts/revisar_sombra.py`) se mide contra sí misma, no contra producción. Tras el encendido su MODIS es idéntico a
  producción; no encontré ningún programa que compare sombra MODIS contra producción MODIS
  (`git grep -l sombra_codigo_mirova loop/activo -- experiments scripts`).
- **El laboratorio `experimental` queda en False** en A más B (no aparece entre los 57 que cambian), que es lo que
  protege el lado de la sombra de la vigilancia de K (el otro lado es MA172-302).

## 6. SIN DATO

- Comportamiento real de la vía en el runner del NRT: no se puede despachar ningún workflow; MODIS real no corre en
  Windows (pyhdf).
- Cuántas caídas a K de la vía habrá y cuánto pesan en el audit semanal: no hay records de la vía en producción todavía.
- Límite de jobs concurrentes de la cuenta y colas reales en el solapamiento de MA172-305.
- El arranque real de la guardia: aún no corre (PR A sin mergear).

## 7. FUERA DE ALCANCE

Censo de consumidores y cobertura de pruebas de la vía (frente 1); lo que ve el operador, regla de reversión, tiempo
del NRT y simulación del revert (frente 2); física y fidelidad de la vía contra el código de MIROVA.
