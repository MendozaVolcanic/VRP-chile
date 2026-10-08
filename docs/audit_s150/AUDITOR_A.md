# Auditoría S150, frente A: operación de punta a punta

Auditor A, 2026-10-08 (hora del servidor GitHub al empezar: 18:14 UTC). Sólo lectura sobre el repo;
scripts y salidas en `experiments/_s150_audit/A/`. Toda frescura se midió contra el **remoto**
(`gh api`), no contra el checkout. Al empezar, el checkout local estaba en el mismo commit que
`origin/main` (`327621e2c`, 16:27 UTC), así que los JSON locales leídos para medir el pasado son los
del remoto a esa hora.

## 0. En una pantalla

**Por qué nadie se enteró.** Las alertas existieron y se dispararon a tiempo: el healthcheck abrió el
issue del token **diez días antes** de que venciera (#752, 2026-09-23 15:44 UTC), lo comentó al vencer
(10-03 15:23), el monitor abrió #754 a las 14 h del corte (10-03 21:39) y el de frescura #756 a las
33 h (10-04 16:07). **Ninguna llegó a nadie porque el repositorio no tiene ni un solo observador**:
`subscribers_count = 0` en VRP-chile y en los 29 repos del dueño (control: torvalds/linux da 8.454,
octocat/Hello-World 1.738). Un issue que abre `github-actions` sin asignado ni mención no notifica a
nadie que no vigile el repo. Además el monitor **cerró solo** su propio issue el 10-07 06:19 como
"Recuperado", citando corridas del **3 de septiembre**: la API le devolvió corridas viejas y el
monitor no lo comprueba. Y una sesión de Claude supo del token vencido el 10-04 01:29 (PR #755), pero
lo anotó como bloqueo de un experimento, no como "el NRT está caído en plena erupción".

**Lo que se repite seguro.** El token nuevo vence el 2026-12-07 18:03 UTC; el aviso saldrá el
~2026-11-27 al mismo canal sin lectores. Si no se cambia el canal, este apagón vuelve en 60 días.

**Recuperación.** El NRT despachado (run 37821953924) terminó `success` a las 18:54 UTC y rellenó el
hueco del 10-03 al 10-08 en los 11 Tier A y las tres familias, con una excepción: Llaima perdió las 6
pasadas VIIRS de la madrugada del 10-08 porque un timeout de LANCE dejó vetado también a LAADS (A-13) y
el job salió verde igual; entrarán en la próxima corrida. Detalle en §4.

**Nota de numeración.** A-13 está en §4 porque apareció al medir la recuperación.

## 1. Hallazgos, ordenados por gravedad

Cronología medida (todas las horas UTC, de `gh issue view`, `gh run list` y `gh pr view`):

| hora | qué pasó | fuente |
|---|---|---|
| 09-23 15:44 | healthcheck abre #752 "EARTHDATA_TOKEN por vencer" (estado `renovar`, 10 días) | issue #752 |
| 10-03 07:18 | vence el token | cuerpo de #752 (`exp` del JWT) |
| 10-03 07:36 | primera corrida NRT fallida (11 de 11 jobs, `401 Unauthorized` en CMR) | run 37106918690 |
| 10-03 15:23 | #752 pasa a `vencido` (comentario, notifica a quien vigile) | #752 |
| 10-03 21:39 | monitor abre #754 "3+ corridas fallaron" | #754 |
| 10-04 01:29 | una sesión de Claude abre PR #755 y escribe "venció el token de Earthdata" como bloqueo del experimento de abril; mergeado 01:46 | PR #755, `docs/S150_RESULTADO_MESES.md:196-198` |
| 10-04 16:07 | healthcheck abre #756 "staleness" (11 de 11 Tier A sin dato) | #756 |
| 10-05 19:52 | healthcheck no corre: "The job was not acquired by Runner" | run 37366212088 |
| 10-06 17:33 | #756 escala a 72 h (comentario) | #756 |
| 10-07 06:19 | el monitor **cierra #754 como "Recuperado"** citando corridas del 2026-09-03 | run 37580874629 |
| 10-07 23:15 | el monitor abre #758 (nuevo issue para el mismo incidente) | #758 |
| 10-08 18:07 | Nicolás rota el token; 18:08 despacha NRT (37821953924) y healthcheck (cierra #752) | runs y #752 |

### A-1. Las alertas se emiten a un repositorio que nadie vigila: no le llegan a nadie

- **SCRIPT:SALIDA**: `gh api repos/MendozaVolcanic/VRP-chile --jq .subscribers_count` da **0**; el mismo
  campo da 0 en los **29 de 29** repos de MendozaVolcanic (`experiments/_s150_audit/A/subscribers_count.txt`).
  Control positivo del instrumento: torvalds/linux 8.454, octocat/Hello-World 1.738. Ningún issue de los
  30 últimos tiene asignado (`gh issue list ... assignees`: 0) y ninguno menciona a una persona. En
  `.github/workflows/` no hay ningún canal de salida que no sea un issue de GitHub (grep de `slack`,
  `telegram`, `ntfy`, `smtp`, `webhook`, `discord`, `assignee`, `@MendozaVolcanic`: 0).
- **QUÉ PASA**: el sistema detectó el problema diez días antes y lo escribió en un lugar que no genera
  ninguna notificación. Un issue abierto por `github-actions` sólo notifica a quien vigila el repo o está
  asignado o mencionado. El fenómeno no es técnico: el aviso existió y nadie podía verlo sin ir a buscarlo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible como alerta. El tablero sí muestra por volcán "sin pasadas hace
  X h" en rojo (`frontend/index.html:1693-1695`), pero eso sólo lo ve quien entra.
- **CÓMO REPRODUCIRLO**: los dos comandos de arriba.
- **CONFIANZA**: CONFIRMADO el 0 de observadores y la ausencia de otro canal. **SIN VERIFICAR**: si a
  Nicolás le llegan los correos de "Run failed" de Actions (dependen de su configuración personal de
  notificaciones, que la API no expone sin el scope `notifications`). Las corridas programadas tienen como
  actor a MendozaVolcanic (run 37106918690: `actor` y `triggering_actor` = MendozaVolcanic), así que si esa
  opción está encendida le llegaron unos 23 correos de falla entre el 3 y el 8 de octubre.
- **GRAVEDAD 5**: decide si una erupción se ve. Es **seguro** que se repite: el token nuevo vence el
  2026-12-07 18:03 UTC y el aviso de `renovar` saldrá el ~2026-11-27 al mismo issue sin lectores.

### A-2. El monitor de fallas cerró solo su issue en plena caída, porque la API le devolvió corridas de un mes antes

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt-monitor.yml:31-38` (consulta `listWorkflowRuns` con
  `status: 'completed'`, `event: 'schedule'`, `per_page: 3`) y `:67-83` (cierra si las tres son verdes).
  No compara la fecha de las corridas con nada.
- **SCRIPT:SALIDA**: log del run 37580874629 (`experiments/_s150_audit/A/monitor_cierre_falso_37580874629.log`):
  a las 2026-10-07 06:19 la API devolvió las corridas del **2026-09-03** 14:08, 19:06 y 22:17, todas
  `success`; el monitor imprimió "Solo 0/3 fallaron" y cerró #754. Siete horas después (run 37630952820,
  13:44) la API devolvió otra vez las mismas corridas de septiembre. A las 23:14 (run 37701156191) volvió a
  dar las de octubre y el monitor abrió un issue NUEVO (#758). Repetida hoy la misma consulta tres veces
  (`consulta_monitor_replica.txt`) devuelve las corridas correctas: el defecto de la API es intermitente.
- **QUÉ PASA**: un aviso de "caído" se convirtió en un aviso de "recuperado" sin que el sistema se hubiera
  recuperado. Con lectores, ese comentario les habría dicho que ya no había nada que hacer.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (log).
- **GRAVEDAD 4**: es el único canal que mira las fallas y puede declarar sano un sistema caído. Arreglo
  barato: descartar corridas más viejas que, por ejemplo, 24 h, o exigir que la corrida verde sea
  posterior a la fecha de apertura del issue.

### A-3. La información del corte llegó a una sesión de Claude y se archivó como bloqueo de laboratorio

- **ARCHIVO:LÍNEA**: `docs/S150_RESULTADO_MESES.md:196-198` ("El NRT falla desde las 07:36 UTC de ese día
  ... Rotarlo es de Nicolás") y el cuerpo del PR #755, línea 6 ("repetir el job queda bloqueado porque venció
  el token"). PR creado 2026-10-04 01:29 UTC, 18 h después del corte; mergeado por MendozaVolcanic 01:46.
- **QUÉ PASA**: el canal que sí lee Nicolás (las sesiones) tuvo el dato a las 18 h, con Nevados de Chillán
  en actividad desde el 28-sep, y lo presentó como "no pude repetir abril", no como "el monitoreo
  operacional está caído". El efecto operacional no se nombró.
- **CONFIANZA**: CONFIRMADO lo escrito. SOSPECHA: que la sesión no lo haya dicho en el chat (no tengo el
  transcript).
- **GRAVEDAD 4**: es la diferencia entre 18 h y 5 días de apagón. Ningún hook de sesión
  (`~/.claude/hooks/check_*.py`) lee el vencimiento del token ni los issues abiertos del repo (grep de
  `earthdata`, `nrt-stale`, `token_edad`, `issue`: sólo coincide un recordatorio genérico de seguridad).

### A-4. La auditoría semanal contó los días sin datos como pérdidas y abrió un "FUERA DE BANDA" que es artefacto del corte

- **ARCHIVO:LÍNEA**: `scripts/auto_audit_weekly.py:330-336` (cada noche con alerta de MIROVA entra al
  denominador del recall, haya o no dato nuestro ese día) y `:388-409` (la cobertura se juzga en agregado:
  95,1 % de días con datos supera el mínimo de 80 %, `MIN_COVERAGE_PCT`, l. 84).
- **SCRIPT:SALIDA**: `data/audit_continuous/latest.json` del 2026-10-05 18:05: ventana 2026-08-06 a 10-05,
  58 de 61 días con datos, recall VIIRS 375 = 92,8 % sobre 194 noches (14 sin acierto), banda 93,4 %, issue
  #757. En el snapshot de referencia que usó esa corrida hay **15 noches volcán-día con alerta VIIRS 375 de
  MIROVA entre el 10-03 y el 10-05**, los tres días sin ningún dato nuestro (conteo propio, ver §5).
- **QUÉ PASA**: si esas noches entraron al denominador, las 14 "pérdidas" pueden ser enteras del corte y
  el recall de los días con datos estaría en banda. El instrumento no distingue "no detectamos" de "no
  miramos" (SIN DATO contado como FALLA).
- **CONFIANZA**: CONFIRMADO el mecanismo en el código y las 15 noches. SOSPECHA el número exacto (no corrí
  el script porque escribe en `data/`; la exclusión de alertas diurnas, 21 en esa ventana, puede sacar
  algunas).
- **GRAVEDAD 3**: falsa alarma de regresión del algoritmo justo cuando el problema era la operación; y el
  mismo defecto, al revés, haría que un corte corto pase desapercibido en la métrica.

### A-5. Un corte de más de 7 días no se recupera solo

- **ARCHIVO:LÍNEA**: `scripts/run_pipeline.py:384-397` y `:442-446`: sin fechas, el NRT procesa el día en
  curso y 7 hacia atrás (8 fechas).
- **QUÉ PASA**: el apagón duró ~5,4 días y el dato perdido arranca el 2026-10-02 07:35. La corrida despachada
  el 10-08 cubre del 10-01 al 10-08, así que alcanza; con la rotación el 10-10 las pasadas del 10-02 habrían
  quedado fuera para siempre salvo un backfill manual. El comentario de `scripts/medir_cadencia_cron.py`
  ("no implica pérdida de datos") y el plan del cron externo ("No se pierden datos") valen sólo dentro de
  esa ventana. Antecedente: el corte de julio (13 días) necesitó relleno aparte; hoy la serie no tiene
  huecos de más de 48 h por familia desde el 2026-06-01 (`huecos_por_sensor.py`), así que se rellenó.
- **CONFIANZA**: CONFIRMADO (código).
- **GRAVEDAD 3**: hoy no mordió, por 1,5 días de margen.

### A-6. El cron "cada 2 h" corre cada 5,2 h, y el "cada hora" del sync cada 4,8 h; nada alerta por eso

- **SCRIPT:SALIDA**: `experiments/_s150_audit/A/cadencia.py` sobre 1.000 corridas (ventana efectiva
  2026-09-14 19:55 a 2026-10-08 18:19, 23,9 días; tope de la API):

  | workflow | declarado | intervalo medio | p90 | máximo |
  |---|---|---|---|---|
  | `nrt.yml` | 2 h | 5,24 h | 7,71 h | 10,68 h |
  | `sync-mirova-csv.yml` | 1 h | 4,82 h | 6,99 h | 8,96 h |
  | `nrt-monitor.yml` | 6 h | 6,84 h | 9,08 h | 11,81 h |
  | `nrt-healthcheck.yml` | 24 h | 24,10 h | 26,31 h | 27,77 h |

  El healthcheck llega todos los días pero entre las 15:00 y las 19:52 UTC, no a las 12:00 declaradas.
- **QUÉ PASA**: el paso "Medir la puntualidad del cron" (`nrt-healthcheck.yml`, paso S133) sólo escribe el
  resumen del job; `scripts/medir_cadencia_cron.py:143` sale siempre con 0. Es una medición sin alerta.
- **Latencia que ve el operador** (`latencia_primera_aparicion.py`, Nevados de Chillán, pasadas del 09-24 al
  10-02, hora del primer commit que contiene cada pasada): mediana 4,4 h (V375, n = 39), 4,8 h (V750, n =
  39) y 6,5 h (MODIS, n = 18); p90 de 8,9 a 10,1 h; máximo 16,8 h. `processed_utc` no sirve para esto: se
  reescribe al promover NRT a standard (`pipeline/store.py:499` junto con `:623-624`), y de las pasadas de
  esa ventana sólo 37 a 42 por familia siguen como `nrt` (`latencia.py`).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 3**: en erupción, una pasada de madrugada puede llegar al tablero 9 a 10 h tarde.

### A-7. Nevados de Chillán, Llaima y Copahue van siempre en la segunda tanda del NRT

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt.yml:80` (`max-parallel: 8`) con la matriz de `:89-99`, donde
  NdC es el noveno.
- **SCRIPT:SALIDA**: commits "NRT update" del 09-15 al 10-03, 62 corridas: NdC llega con mediana **20,9 min**
  después del primer volcán de la misma corrida (Llaima 22,1, Copahue 23,6; los demás entre 1,8 y 6,9).
  En la corrida despachada hoy, NdC, Llaima y Copahue quedaron `queued` mientras corrían los otros ocho.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 2**: 20 min por corrida en el volcán que hoy está en erupción;
  reordenar la matriz o subir `max-parallel` a 11 lo resuelve (el comentario de `:77-79` cuida la contención
  de push, que el bucle de reintento de `:341-349` ya maneja; SOSPECHA que 11 no la empeore).

### A-8. Si el secret del token queda vacío, el NRT cae al usuario y clave vencidos y el healthcheck calla

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt.yml:172-174` sigue pasando `EARTHDATA_USERNAME` y
  `EARTHDATA_PASSWORD`; `pipeline/fetch.py:318` trata un token vacío como "sin token" y entonces
  `:334-347` reintenta `earthaccess.login(strategy="environment")` hasta 8 veces con el par usuario y clave.
  `REGISTRO_CREDENCIALES.md` fila 2: ese par está vencido y su uso **bloqueó la cuenta 10 min** (S146).
  Del lado de la alerta, `scripts/token_edad.py:46` devuelve `desconocido` y el paso del healthcheck no abre
  issue en ese estado (`nrt-healthcheck.yml`, paso "Issue de renovacion del token": "sin issue").
- **QUÉ PASA**: un secret borrado o mal pegado (un secret ausente se resuelve a cadena vacía, no a error)
  produce un NRT que martilla una credencial muerta y un monitor de token mudo.
- **CONFIANZA**: CONFIRMADO el código; SOSPECHA el bloqueo de la cuenta en este camino (no lo probé, y no
  debe probarse con la cuenta real). **GRAVEDAD 3**. Además el cuerpo del issue del monitor
  (`nrt-monitor.yml:116`) manda a revisar `EARTHDATA_USERNAME`/`PASSWORD`, que no es la credencial que usa
  el NRT: en este incidente apuntaba al lugar equivocado (gravedad 2).

### A-9. Ubuntu 26 llega el 2026-10-19 y el NRT instala HDF4 con apt sin fijar la imagen (SOSPECHA)

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt.yml:68` (`runs-on: ubuntu-latest`) y `:141-143`
  (`sudo apt-get install -y libhdf4-dev`, `pip install pyhdf`, Python 3.11 por `setup-python`).
- **SCRIPT:SALIDA**: anotación de GitHub en el run 37366212088: "The ubuntu-latest label will migrate to
  Ubuntu 26 beginning October 19, 2026".
- **QUÉ PASA**: si en la imagen nueva falta el paquete o la versión de Python, falla el paso compartido de
  instalación y se caen los tres sensores, no sólo MODIS. Sería ruidoso (fallas), pero las fallas hoy van a
  un canal sin lectores (A-1).
- **CONFIANZA**: SOSPECHA. **GRAVEDAD 4** si ocurre (11 días, con un volcán en erupción). Prueba barata:
  una corrida de prueba con `runs-on: ubuntu-26.04` antes del 19, o fijar `ubuntu-24.04` en `nrt.yml`.

### A-10. El healthcheck queda en rojo cada vez que abre un issue (la etiqueta ya existe)

- **ARCHIVO:LÍNEA**: `nrt-healthcheck.yml`, paso "Notificar por escalón": `gh label create` sin `--force`
  cuando no hay issue abierto; el fallo entra a `fallos_gh` y el paso sale con 1. Igual en el paso del token.
- **SCRIPT:SALIDA**: run 37215535362 (`healthcheck_label_bug.log`): "label with name nrt-stale already
  exists", "Issue creado (escalón 48 h)", "FAIL: 1 llamada(s) a gh fallaron; la alerta pudo no haberse
  emitido". El issue sí se creó (#756).
- **QUÉ PASA**: el job dice "la alerta pudo no haberse emitido" justo cuando se emitió bien. Un rojo que
  miente entrena a no mirar el rojo. **CONFIANZA**: CONFIRMADO. **GRAVEDAD 2**.

### A-11. El snapshot consolidado de la referencia se refresca una vez por semana; el sync no lo toca

- Respuesta al dato del orquestador. **El sync de MIROVA no se detuvo**: 23 corridas `success` entre el
  10-03 12:31 y el 10-08 16:26, y `latest_consolidado.csv` (raíz) tuvo 23 commits en ese tramo. Medido contra
  el remoto de Mirova-v1 a las ~18:20 UTC (`diff_referencia.py`): `latest_consolidado.csv` tiene **0 filas
  faltantes** de 41.576 (control positivo del instrumento). En cambio
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` tiene su último commit el
  2026-10-05 18:05 (el de `audit-weekly.yml:55`, que es el único que lo escribe) y le faltan **455 filas**
  (27 no RUTINA; de Nevados de Chillán 38, de ellas 2 alertas), con pasadas del 10-05 17:24 al 10-08 12:30.
  No reproduzco el "441 filas para NdC del 09-13 al 10-09" del orquestador: con la clave (Fecha_Satelite_UTC,
  Volcan, Sensor) son 38 para NdC. Además 207 filas del snapshot ya no existen en el remoto con la misma
  clave (Mirova-v1 reescribe horas, por ejemplo `18:00:02`), así que la clave de pareo no es estable.
- **ARCHIVO:LÍNEA**: `sync-mirova-csv.yml:65-70` y `:182-183` escriben `latest_consolidado.csv` y el OCR del
  snapshot, no el consolidado del snapshot. Lo leen `scripts/banco_paridad.py`,
  `scripts/referencia_mirova_unificada.py`, `pipeline/mirova_csv_loader.py` y los evaluadores de
  `experiments/_s149_prereg_invierno/` (grep). El encabezado del sync (`:3-12`) se escribió para quitar
  justo este atraso de hasta 7 días, pero sólo lo quitó para el OCR: hoy en la misma carpeta conviven un OCR
  de hace 2 h y un consolidado de hace 3 días.
- **CÓMO SE VE EN EL DASHBOARD**: no se ve (el tablero lee `data/mirova/<vol>.json`, que el sync sí
  reconstruye desde `latest_consolidado.csv`). Afecta a quien evalúe la erupción con los scripts.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 3** (pertenece al cruce con el frente D: un evaluador que lea esa
  ruta durante la erupción tiene hasta 7 días de referencia faltante y cuenta como "MIROVA no miró" pasadas
  que sí miró).

### A-12. Mirova-v1 ya tiene un disparador externo cada 5 min que no figura en el registro de credenciales

- **SCRIPT:SALIDA**: `gh run list --repo MendozaVolcanic/Mirova-v1`: "Monitor Volcanico VRP" corre por
  `workflow_dispatch` a las 18:00:16, 18:05:07, 18:10:10, 18:15:09, 18:20:10, 18:25:06 (actor y
  `triggering_actor` = MendozaVolcanic). Su propio cron `ocr_workflow.yml` (`5 * * * *`) entregó sólo **8**
  eventos `schedule` entre el 10-06 20:12 y el 10-08 16:23 (44 h, uno cada ~5,5 h).
- **QUÉ PASA**: dos cosas. (a) La degradación del cron de GitHub no es de VRP-chile: afecta a la cuenta, y
  en Mirova-v1 es aún peor (1 de cada ~5 ticks horarios). (b) Algún disparador externo con un token con
  permiso de Actions sobre Mirova-v1 funciona hoy y es puntual al minuto, pero `REGISTRO_CREDENCIALES.md`
  sólo registra el de VRP-chile, "por crear" (fila 31). Si ese token vence, la referencia de MIROVA pasa
  de 5 min a ~5 h de cadencia en silencio.
- **CONFIANZA**: CONFIRMADO el disparo externo y la cadencia; SIN VERIFICAR dónde vive el disparador
  (cron-job.org, Programador de tareas del computador de Nicolás u otro). **GRAVEDAD 2** para VRP-chile;
  regla 2 del mapa del workspace (credencial sin fila).

## 2. Qué otro apagón silencioso es posible hoy

| modo | ¿lo ve algún monitor? | evidencia | gravedad |
|---|---|---|---|
| token vencido o rotación olvidada | sí, pero el aviso no llega a nadie | A-1 | 5 |
| secret del token vacío o borrado | **no**: `token_edad` da `desconocido` y no abre issue; el NRT cae al par vencido | A-8 | 3 |
| un solo sensor deja de llegar (MODIS por HDF4, LAADS, LANCE) con el volcán fresco por los otros dos | **no**: el healthcheck y el gate A57 miran sólo `records[-1]` por volcán (`nrt-healthcheck.yml`, bloque "Detect stale Tier A"; `nrt.yml:288-299`) | no ha pasado desde 2026-06-01 (`huecos_por_sensor.py`: ningún hueco de más de 48 h por familia); SOSPECHA de diseño | 3 |
| cron de GitHub degradado aún más | se mide pero no alerta | A-6 | 3 |
| cambio de imagen Ubuntu 26 (10-19) | sería ruidoso, pero va al canal sin lectores | A-9 | 4 (SOSPECHA) |
| scraper Mirova-v1 detenido | el sync dice "sin cambios" y sale verde; el tablero avisa recién a los **14 días** (`frontend/index.html:417`); la auditoría semanal a los 7 (`auto_audit_weekly.py:83`) | hoy está sano: 0 fallas en sus últimas 200 corridas | 3 |
| Pages sirve dato viejo | el despliegue sale verde igual (corre tras cada NRT fallido: `pages-deploy.yml`, `workflow_run` sin filtrar por conclusión salvo `cancelled`) | `curl -I` del JSON de NdC en Pages: `Last-Modified` = hora del despliegue, no del dato | 2; el indicador por volcán del tablero sí lo muestra |
| monitor declara sano un sistema caído | no | A-2 | 4 |
| corte de más de 7 días | no se rellena solo | A-5 | 3 |
| `nrt-monitor` ciego a corridas despachadas | filtra `event: 'schedule'` (`nrt-monitor.yml:37`) | hoy irrelevante; con el cron externo, la mayoría de las corridas serían `workflow_dispatch` (§3) | 3 si se activa el cron externo |

Lo que **no** encontré como riesgo: un pusher sin `push-main` ni reintento (lo vigila
`tests/test_guard_declarado_vs_efectivo_s131.py`, no lo re-medí); y corridas del NRT o del sync
canceladas por desplazamiento en el grupo `push-main`: **0** en 24 días (`runs_30d.tsv`, 110 NRT
`schedule` y 119 sync).

## 3. El plan del cron externo (`docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md`) contra el código de hoy

**Sigue siendo correcto en lo central, con tres enmiendas.**

1. **Mecánica: correcta.** `nrt.yml:13-48` acepta `workflow_dispatch` con todos los inputs opcionales;
   sin inputs, `profile` toma `both` y corre el paso `mirova_equivalent` (`:164-166`), y el experimental
   sólo con `profile=experimental` (`:200`). El despacho de hoy (37821953924) se creó y arrancó en el mismo
   segundo (`created_at` = `run_started_at` = 18:08:16). Los scripts de verificación que cita existen
   (`scripts/medir_atraso_despacho_nrt.py`, `scripts/medir_cadencia_cron.py`). La premisa sigue valiendo y
   empeoró: el NRT corre cada 5,24 h (A-6), y la cuenta ya usa con éxito un disparador externo en Mirova-v1
   (A-12), lo que prueba el mecanismo.
2. **Enmienda 1, el monitor**: `nrt-monitor.yml:37` filtra `event: 'schedule'`. Con el cron externo, unas 12 de
   cada ~16,6 corridas diarias (72 %) serían despachadas y el monitor no las vería; hay que quitar ese filtro (y, de
   paso, arreglar A-2) en el mismo cambio.
3. **Enmienda 2, "No se pierden datos" y "no se pisan"**: lo primero vale sólo para cortes de menos de 7
   días (A-5). Lo segundo es inexacto: con `cancel-in-progress: false`, GitHub mantiene **una** corrida
   pendiente por grupo y la que llega después cancela a la pendiente (es la causa de la pérdida del job
   `merge` en S125 y S126 que cita el `CLAUDE.md` del proyecto). Hoy no pasa (0 cancelaciones), pero con 12
   despachos más al día de NRT de 36 a 50 min (duración de las 8 corridas verdes del 10-01 al 10-03,
   `nrt_runs.json`) y el sync en el mismo grupo, un NRT pendiente puede ser
   desplazado por un sync. Consecuencia: latencia, no pérdida (la ventana de 8 días lo recupera).
4. **Enmienda 3, no ataca el incidente.** El cron externo arregla la latencia, no el aviso: un despacho
   responde 204 aunque el pipeline falle por credencial, así que cron-job.org no se entera del corte. El
   arreglo de A-1 es independiente y más urgente.

## 4. ¿Se recuperó el sistema? (hueco del 2026-10-02 07:35 al 2026-10-08)

**Sí, salvo una noche de Llaima que quedó pendiente, y ésta muestra un modo de pérdida silenciosa.**

El NRT despachado (run 37821953924, `workflow_dispatch`, creado 2026-10-08 18:08:16) terminó `success` a
las 18:54:54 UTC con 11 de 11 jobs verdes y un commit por volcán entre las 18:27 y las 18:54 (remoto,
`gh api .../commits`). Procesó del 10-01 al 10-08 (ventana por defecto, A-5). Medido sobre el remoto en el
commit `4a39adaeb` con `relleno_hueco.py` (antes: `relleno_antes.txt`, todas las noches 10-03 a 10-08 en
HUECO en las tres familias y los 11 volcanes; después: `relleno_despues.txt`), contando volcanes por noche
contra la mediana de las 7 noches previas:

| familia | 10-03 | 10-04 | 10-05 | 10-06 | 10-07 | 10-08 |
|---|---|---|---|---|---|---|
| V375 | 11 ok | 11 ok | 11 ok | 11 ok | 11 ok | 10 ok, **Llaima 0** |
| V750 | 11 ok | 11 ok | 11 ok | 11 ok | 11 ok | 10 ok, **Llaima 0** |
| MODIS | 11 ok | 8 ok, 2 parcial, Láscar 0 | 11 ok | 11 ok | 11 ok | 10 ok, Llaima 1 de 2 |

- **Láscar MODIS 10-04 en 0 no es pérdida**: el log del job (`nrt_despacho_lascar.log`) dice "MODIS_TERRA:
  kept 0 of 2 granules (night filter)" y "MODIS_AQUA: kept 0 of 1": esa noche no hubo pasada MODIS nocturna
  sobre Láscar. Lastarria e Isluga con 1 en 10-04 son, con toda probabilidad, la misma geometría orbital
  (SOSPECHA: no leí sus logs). El 10-02 MODIS "parcial" en 7 volcanes ya estaba igual antes del despacho.
- **Nevados de Chillán quedó completo**: 10-03 a 10-08 con 2 a 3 pasadas MODIS y 4 a 6 VIIRS por noche;
  último record 2026-10-08 08:05.
- **Llaima 10-08 (A-13, abajo)**: último record 2026-10-08 01:25; las 6 descargas VIIRS de esa noche se
  saltaron.

### A-13. Un ConnectTimeout de LANCE marca caído también a LAADS y el job sale verde sin las pasadas

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:696-716`: ante un error de conexión, si el reprobe no da sano a
  **todos** los hosts del lote, marca caídos **todos** (`_DOWN_DOWNLOAD_HOSTS.update(hosts)`), y el lote de
  MODIS Aqua mezcla el L1B de LANCE con el GEO de LAADS. Desde ahí `:676-683` salta todo lote cuyos hosts estén todos marcados, o sea toda descarga de LAADS
  del resto de la corrida.
- **SCRIPT:SALIDA**: `nrt_despacho_llaima.log`, Llaima 2026-10-08: `DOWNLOAD_CONNFAIL ... host_down=
  ['data.laadsdaac.earthdatacloud.nasa.gov', 'nrt3.modaps.eosdis.nasa.gov'] err=ConnectTimeout ... nrt3.modaps`
  (188 s), y luego `DOWNLOAD_SKIP host caído ['data.laadsdaac...']` para VIIRS SNPP, NOAA-20 y NOAA-21 en
  375 y 750 m. El job terminó `success`. Copahue, en el mismo minuto, bajó de LAADS sin problema.
- **QUÉ PASA**: el host que falló fue el de tiempo casi real (LANCE); el archivo definitivo (LAADS) estaba
  sano, pero quedó vetado por compartir lote. La pasada de la noche más reciente se pierde en esa corrida
  y entra recién en la siguiente (hoy, ~5 h después; A-6). Ningún monitor lo ve: el volcán sigue "fresco"
  por la pasada de las 01:25 (§2, fila "un solo sensor").
- **CÓMO SE VE EN EL DASHBOARD**: Llaima sin las pasadas VIIRS de la madrugada del 8 hasta la próxima corrida.
- **CONFIANZA**: CONFIRMADO en esta corrida. SIN VERIFICAR con qué frecuencia pasa en el cron normal (no
  barrí logs viejos). **GRAVEDAD 3**: en el volcán en erupción, una noche de VIIRS llega horas tarde; el
  arreglo es marcar sólo los hosts que fallan el reprobe.

## 5. Pruebas de campo propuestas

| qué mirar | quién | qué decide |
|---|---|---|
| En github.com/MendozaVolcanic/VRP-chile, botón "Watch": ¿dice "Not watching" o "Participating"? Y en Settings > Notifications > Actions, ¿están encendidos los correos de corridas fallidas? | Nicolás (2 min) | Si no vigila, A-1 queda confirmada en su causa y el arreglo mínimo es "Watch: Custom > Issues". Si los correos de Actions estaban encendidos y llegaron ~23 entre el 3 y el 8, el problema es de lectura (filtro de correo), no de emisión |
| Buscar en el correo "Run failed: NRT VRP Pipeline" entre el 2026-10-03 y el 10-08 | Nicolás | Igual que arriba: distingue "no se emitió" de "se emitió y no se leyó" |
| Agregar en `nrt-healthcheck.yml` un asignado (`--assignee MendozaVolcanic`) o una mención en el issue de token y de staleness, y probarlo con `workflow_dispatch` cuando algo esté en rojo | sesión siguiente, con OK de Nicolás | Si a Nicolás le llega el correo, el canal queda cerrado; si no, hace falta un canal fuera de GitHub (ntfy, Telegram) |
| Antes del 2026-10-19: un workflow de prueba con `runs-on: ubuntu-26.04` que sólo corra el paso "Install dependencies" de `nrt.yml` e importe `pyhdf` | sesión siguiente | Si falla, fijar `ubuntu-24.04` en `nrt.yml` antes del 19 (A-9) |
| Mañana ~18 UTC: `gh issue list --repo MendozaVolcanic/VRP-chile --state open` | cualquiera | #756 debe cerrarse solo en el healthcheck del 10-09 y #758 al tercer `schedule` verde; si #758 se cierra citando corridas de septiembre, A-2 se repite |
| Calendario: recordatorio de rotación del token el **2026-11-27** (`docs/EARTHDATA_TOKEN_SETUP.md:42` ya lo pide: "Setear recordatorio calendar a 50 días") | Nicolás | Red de seguridad humana mientras A-1 no esté arreglada |
| Re-correr `auto_audit_weekly.py` (en una copia, no sobre `data/`) excluyendo los días 10-03 a 10-05 del denominador | sesión siguiente | Si el recall VIIRS 375 vuelve a banda, #757 es artefacto del corte (A-4) y se cierra con esa nota |

## 6. VERIFICADO LIMPIO

- **El NRT falla rápido y con el mensaje correcto ante un token vencido**: 23 corridas de 2 a 7 min, 11 de
  11 jobs en `failure`, `401 Unauthorized` en CMR (run 37106918690, `gh run view --log-failed`). No hubo
  minutos quemados ni bloqueo de cuenta; `pipeline/fetch.py:422-466` clasifica la credencial muerta.
- **El aviso del token se emitió a tiempo**: `scripts/token_edad.py` leyó el `exp` del JWT y el healthcheck
  abrió #752 diez días antes (09-23), lo pasó a `vencido` 8 h después del vencimiento y lo cerró a los 2 min
  de la rotación (#752). El defecto está en el destino del aviso, no en el detector.
- **El healthcheck de frescura funciona**: abrió #756 en la primera corrida con más de 48 h, escaló a 72 h y
  no notificó por cambios de edad (cuerpo editado). `records[-1]` es el más reciente porque
  `pipeline/store.py:625` y `:631` reordenan por `datetime_utc` en cada escritura.
- **El sync de MIROVA no se detuvo** y `latest_consolidado.csv` está al día con el remoto (0 filas faltantes,
  `diff_referencia.py`). Mirova-v1 sano: 0 fallas en sus últimas 200 corridas.
- **Pages despliega**: el JSON de NdC responde 200 en `mendozavolcanic.github.io/VRP-chile/` (`curl -I`).
- **El tablero sí muestra la edad del dato por volcán** ("sin pasadas hace X", `frontend/index.html:1693-1695`).
- **No hay huecos de más de 48 h por familia de sensor en ningún Tier A desde el 2026-06-01** fuera de este
  apagón (`huecos_por_sensor.py`): el corte de julio quedó rellenado.
- **El perfil resuelto como el código** tiene los tres sensores encendidos y escribe en `mirova_equivalent`
  (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`: `sensors=MODIS:True
  V375:True V750:True data_subdir=mirova_equivalent`).
- **0 corridas del NRT o del sync canceladas** por el grupo `push-main` en 24 días (`runs_30d.tsv`).
- **`nrt-retry.yml` no reintentó en vano**: sólo relanza con la anotación `NASA_DOWN`, que un 401 no produce.

## 7. Scripts y salidas (todos en `experiments/_s150_audit/A/`)

`nrt_runs.json`, `runs_30d.tsv` (corridas), `cadencia.py`, `latencia.py`, `latencia_primera_aparicion.py`,
`huecos_por_sensor.py`, `diff_referencia.py`, `noches_mirova_en_dias_muertos.py`, `relleno_hueco.py`
(`relleno_antes.txt`, `relleno_despues.txt`), `subscribers_count.txt`, `consulta_monitor_replica.txt`,
`monitor_cierre_falso_37580874629.log`, `healthcheck_label_bug.log`, `hc_37215535362.log`,
`nrt_commits.txt`, `nrt_despacho_lascar.log`, `nrt_despacho_llaima.log`, `nrt_despacho_copahue.log`.
