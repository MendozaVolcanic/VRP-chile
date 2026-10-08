# Verificador con contexto limpio: auditoría S150

Fecha del servidor al empezar: `Date: Thu, 08 Oct 2026 19:05:50 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`).
Rama `main` en `5c540b066`. Scripts propios en `experiments/_s150_audit/verificador/`. No partí de las
conclusiones de los auditores: para cada hallazgo releí el código, consulté la API de GitHub o corrí la
función real. Todo número de abajo salió de un comando de esta sesión, y se indica cuál.

## Resumen de veredictos

| ID | Veredicto | Mi gravedad | En una línea |
|---|---|---|---|
| A-1 | MATIZADO | 4 | El canal de issues no tiene lectores (confirmado), pero el aviso del token SÍ le llegó a Nicolás por otra vía antes del vencimiento, y el correo de Actions queda SIN VERIFICAR |
| A-2 | CONFIRMADO | 3 | El monitor cerró #754 con corridas del 2026-09-03; pasó dos veces seguidas; reabrió solo 17 h después (#758) |
| A-3 | MATIZADO | 3 | La sesión sí escribió que el NRT estaba caído (no sólo el experimento); no existe ningún hook que lea el token ni los issues (confirmado) |
| A-9 | MATIZADO | 2 | La fecha es oficial, pero `pyhdf` se instala desde una rueda manylinux y Python 3.11 existe para 26.04: el riesgo HDF4 es mucho menor que el declarado |
| B-H4 | MATIZADO | 3 | El descarte de clases sobre «Bajo» se reproduce con la función real; no es silencioso en el log, y hoy no descarta ninguna fila porque el consolidado nunca trajo «Moderado» |
| C-02 | MATIZADO | 3 | El borrado del píxel saturado está en el código; la cita del paper es cierta pero su propósito es elegir banda, y el efecto nunca ocurrió (máximo 354,24 K contra techo 361,27 K) |
| C-03 | CONFIRMADO | 4 | Reproducido con la función real y con los tres records V750 de Chillán del 2026-10-01 |
| D-01 | MATIZADO | 3 | La vara «cráter» del aviso no mira `distance_class` (confirmado, 85,7 contra 28,6), pero MODIS tenía n = 7 < 15 y no podía decidir nada en esa ventana |
| D-02 | CONFIRMADO | 4 | 11 de los 14 fallos V375 que abrieron #757 son noches del apagón sin ningún record; sobre noches con dato el recall era 98,4 % |

---

## A-1. Los avisos van a un repositorio que nadie vigila

**Veredicto: MATIZADO. Gravedad 4.**

Lo que se confirma:

```
gh api repos/MendozaVolcanic/VRP-chile --jq '{subscribers_count,watchers_count,...}'
{"owner":"MendozaVolcanic","private":false,"stargazers_count":1,"subscribers_count":0,"watchers_count":1}
```

```
#752 created=2026-09-23T15:44:39Z closed=2026-10-08T18:09:34Z assignees=0 user=github-actions[bot]
#754 created=2026-10-03T21:39:29Z closed=2026-10-07T06:19:33Z assignees=0 user=github-actions[bot]
#756 created=2026-10-04T16:07:30Z closed=null                 assignees=0 user=github-actions[bot]
#757 created=2026-10-05T18:05:41Z closed=null                 assignees=0 user=github-actions[bot]
```

`grep -rniE 'slack|webhook|smtp|mail|telegram|discord|assignees|mention' .github/workflows/*.yml` sólo
devuelve líneas `git config user.email`: ningún workflow notifica fuera de GitHub ni asigna. Los avisos
salieron a tiempo: #752 diez días antes del vencimiento (el token venció 2026-10-03 07:18 UTC según el
propio issue), #754 catorce horas después de la primera corrida fallida (2026-10-03 07:36), #756 a las
~57 h del último dato (2026-10-02 07:35). La caída duró hasta la corrida manual verde del 2026-10-08 18:08
(`gh api .../workflows/nrt.yml/runs`): **5 días y 11 horas** sin datos nuevos, y en esos días MIROVA
publicó alertas de Chillán, Isluga, Lastarria, Llaima, Planchón Peteroa y Tupungatito (ver D-02).

Lo que cambia:

1. **El vencimiento SÍ llegó a Nicolás, por chat, antes de que ocurriera.** Búsqueda en las transcripciones
   de otras sesiones (`search_session_transcripts`, consulta «token de Earthdata»): las sesiones «vrp 144»
   (09-19/20), «vrp 145» y «vrp 146» (09-20), «vrp 147» (09-21), «vrp 148» (09-21) y «vrp 149» (09-22)
   contienen tablas del tipo «Token de Earthdata: vence el 2026-10-03 07:18 UTC | renovarlo esta semana.
   Es credencial, lo haces tú». El fragmento no me deja distinguir con certeza texto mostrado al usuario de
   salida de herramienta, pero el formato (tabla de pendientes con «lo haces tú») es de respuesta. La
   sesión «Holita» (`congreso geologico 2026`, última actividad 2026-10-07 02:59) contiene «...y anotar la
   nueva fecha de caducidad en el registro de credenciales. Si vas a hacer la medición manual pronto, el
   panel tiene que estar al día.», o sea que también hubo un aviso posterior al vencimiento; la fecha exacta
   de ese mensaje queda SIN VERIFICAR. «No le llegan a nadie» es demasiado fuerte para el token: le
   llegaron, y no bastó. Para el apagón en sí (#754, #756) no encontré otro canal.
2. **Correo de Actions: SIN VERIFICAR.** GitHub notifica las fallas de un workflow programado al usuario que
   escribió la línea `cron`; en `nrt.yml` la puso `ec87e5c9a` (2026-04-15, Nicolas Mendoza). Conté **23
   corridas fallidas** entre el 03 y el 08 de octubre (22 de `nrt.yml`, 1 de `nrt-retry.yml`, todas
   `schedule`). Si su configuración de notificaciones lo permite, le llegaron 23 correos; eso no lo puedo
   ver. El auditor A ya lo dejó como pregunta abierta y está bien planteada.

**Por qué mantengo 4**: el canal oficial de alerta de un SDA en producción no tiene lector, y la única vía que
funcionó fue el recordatorio informal de las sesiones de Claude, que depende de que haya una sesión abierta.

## A-2. El monitor cerró #754 como recuperado con el sistema caído

**Veredicto: CONFIRMADO. Gravedad 3.**

Log del run que cerró el issue (`gh run view 37580874629 --log`):

```
2026-10-07T06:19:32Z Últimas 3 corridas completadas del cron NRT:
2026-10-07T06:19:32Z   2026-09-03T22:17:38Z → success (.../runs/33812350375)
2026-10-07T06:19:32Z   2026-09-03T19:06:04Z → success (.../runs/33794434023)
2026-10-07T06:19:32Z   2026-09-03T14:08:58Z → success (.../runs/33765157161)
2026-10-07T06:19:32Z Solo 0/3 fallaron [guion largo en el original] sin alerta.
2026-10-07T06:19:34Z Issue #754 cerrado: cron recuperado.
```

En ese momento las tres últimas corridas programadas completadas eran fallas (2026-10-07 04:28, 2026-10-06
22:21 y 16:30, `gh api .../workflows/nrt.yml/runs?created=>=2026-10-05`). El código no compara fechas:
`nrt-monitor.yml:31-38` pide `per_page: 3, status: 'completed', event: 'schedule'` y `:67` cierra si
`failures.length === 0`, sin mirar `created_at`.

Lo que agrego:

- **No fue un solo tropiezo de la API.** El run siguiente (`37630952820`, 2026-10-07 13:44) recibió la misma
  lista vieja del 09-03. El run `37701156191` (23:15) recibió la lista correcta y abrió **#758**, que sigue
  abierto. La ventana sin issue abierto fue de 06:19 a 23:15, unas 17 h.
- **Hoy la API ya devuelve bien** la misma consulta: `?per_page=3&status=completed&event=schedule` da
  10-08 17:11, 08:26 y 00:00, las tres `failure`. No pude reproducir el retorno viejo; queda como hecho
  registrado en el log, no como comportamiento reproducible.
- **El filtro `event: 'schedule'`** (línea 37) es correcto en intención pero tiene un efecto colateral: la
  corrida manual verde de hoy (2026-10-08 18:08, `workflow_dispatch`) no cuenta, así que #758 seguirá
  abierto hasta tres corridas programadas verdes. Eso es conservador, no un error.

Gravedad 3 y no 4: el cierre falso duró 17 h y se corrigió solo; como nadie vigila el repo (A-1), el cierre
tampoco cambió lo que alguien vio. El defecto de diseño (no validar que la corrida más nueva sea reciente)
sí vale arreglarlo.

## A-3. La sesión supo del token vencido y lo archivó como bloqueo de laboratorio

**Veredicto: MATIZADO. Gravedad 3.**

- PR #755 (creado 2026-10-04 01:29, mergeado 01:46): el cuerpo dice sólo «repetir el job queda bloqueado
  porque venció el token de Earthdata». Confirmado.
- Pero `docs/S150_RESULTADO_MESES.md:196-198` dice: «el token de Earthdata venció el 2026-10-03. **El NRT
  falla desde las 07:36 UTC de ese día** (`EARTHDATA_CREDENTIAL_INVALID`, "Token ... has expired").
  Rotarlo es de Nicolás.» La sesión sí registró el apagón operacional, no sólo el bloqueo del experimento;
  lo que está mal es **dónde** lo dejó (un informe de laboratorio, sección de pendientes) y no **que** no
  lo supiera.
- ¿Se le avisó a Nicolás en esa misma sesión? **SIN VERIFICAR.** Busqué «EARTHDATA_CREDENTIAL_INVALID»,
  «token de Earthdata venció» y «S150_RESULTADO_MESES» en las transcripciones: cero resultados. El
  instrumento funciona (la consulta «MIROVA» devuelve 5 sesiones), así que el cero significa que esa sesión
  no está indexada o está excluida de la búsqueda, no que no avisara. Sí hay otra sesión («Holita», A-1)
  que le dijo que renovara.
- **Punto sistémico: CONFIRMADO.** Hooks configurados en `C:/Users/nmend/.claude/settings.json` (leí sólo
  eventos y comandos): `SessionStart` corre `check_mapa_workspace.py` y `check_traspaso.py`;
  `UserPromptSubmit` corre `session_counter.py` y `skill_suggester.py`; `PreToolUse` y `SessionEnd` no
  tienen relación. `grep -n -iE 'token|issue|gh |caduc|venc|credencial' ` sobre esos cuatro archivos sólo da
  en `check_mapa_workspace.py`, y ese hook **sólo mira la fecha de modificación de `MAPA_WORKSPACE.md`**
  (umbral 7 días; `os.path.getmtime(MAPA)`), sin red. El `.claude/settings.local.json` del proyecto no
  tiene clave `hooks`. Ningún hook lee el vencimiento del token ni los issues abiertos.

## A-9. `ubuntu-latest` pasa a Ubuntu 26.04 desde el 2026-10-19

**Veredicto: MATIZADO (la fecha se confirma; el riesgo se rebaja). Gravedad 2.**

- Anuncio oficial, `gh api repos/actions/runner-images/issues/14748` (abierto 2026-09-17 por un mantenedor
  de runner-images): «This change will be rolled out over a period of several weeks beginning October 19,
  2026. We plan to complete the migration by November 19, 2026.» Es gradual, no un corte el día 19.
- `nrt.yml:68` `runs-on: ubuntu-latest`; `:134` `python-version: "3.11"`; `:140-143`
  `pip install --upgrade pip`, `sudo apt-get install -y libhdf4-dev` (sin `apt-get update`),
  `pip install pyhdf` (sin versión).
- Lo que rebaja el riesgo:
  - `pyhdf` 0.11.7 (PyPI, 2026-07-11) publica `pyhdf-0.11.7-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl`:
    pip instala la rueda y **no compila contra el HDF4 del sistema**, así que el paquete apt casi seguro ni
    se usa.
  - `libhdf4-dev` existe en `resolute (26.04LTS)` versión 4.3.1-2 (packages.ubuntu.com), así que el `apt-get
    install` no debería fallar por paquete ausente.
  - `actions/python-versions` `versions-manifest.json`: 3.11.17 publicado para `['22.04', '24.04', '26.04']`.
- Riesgos que quedan (SOSPECHA, no probados): el `apt-get install` sin `update` (existe igual hoy), una
  futura versión de `pyhdf` sin rueda cp311, y cualquier otra diferencia del sistema base. Correr un job de
  prueba con `runs-on: ubuntu-26.04` sigue siendo barato y es la única verificación real; no lo despaché.

## B-H4. `rebuild_mirova_from_consolidado.py` sólo acepta «Muy Bajo» y «Bajo»

**Veredicto: MATIZADO. Gravedad 3.**

- Código: `scripts/rebuild_mirova_from_consolidado.py:76` `VALID_CLASSES = {"Muy Bajo", "Bajo"}`; `:87-89`
  descarta toda otra clase. Consumidor en producción: `.github/workflows/sync-mirova-csv.yml:139-172` lo corre
  para los 11 Tier A (cron horario) y escribe `data/mirova/<Vol>.json`, que el tablero carga en
  `frontend/index.html:975` y `frontend/mosaico.html:472`. Las clases de MIROVA son las del propio tablero
  (`frontend/index.html:780-782`: Muy Bajo < 1, Bajo < 10, Moderado < 100 MW).
- Reproducción con la función real, redirigiendo `REPO` a un temporal
  (`experiments/_s150_audit/verificador/v_bh4_rebuild_clases.py`):

  ```
  rejected by clasificacion: {'Moderado': 1, 'Alto': 1, 'NULO': 1}
  control positivo (Bajo 7 MW) presente: True
  Moderado presente: False
  Alto presente: False
  NULO presente (debe ser False): False
  ```

- Lo que cambia:
  - **No es silencioso en el log**: imprime `rejected by clasificacion: {...}` (`:115`). Sí es silencioso
    para el operador, porque nadie lee el log del sync y el job sale verde.
  - **Hoy no descarta nada real**: en `latest_consolidado.csv` (41.576 filas) las clases son NULO 39.969,
    Muy Bajo 1.347 (máximo 0,99 MW), Bajo 248 (máximo 7,86 MW), FALSO POSITIVO 12. Nunca hubo una fila
    «Moderado». El defecto es latente: se activa justo cuando un volcán cruza 10 MW en el canal de la tabla.
  - Las «Moderado» que sí existen están en el canal OCR (ver hallazgo propio V-1), que este script no lee por
    diseño.

## C-02. El píxel VIIRS 375 saturado se convierte en NaN

**Veredicto: MATIZADO. Gravedad 3.**

- Código, confirmado: `pipeline/process_viirs.py:372-373` (`SAT_BIT_MASK = 0b100`,
  `BT_LUT_MAX = {"I04": 361.77, ...}`), `:395-398` (bit 2 de calidad → NaN) y `:399-401` (`bt >= lut_max - 0.5`
  → NaN). En MODIS, `process_modis.py:250-256` pone NaN todo `dn > 32767`, incluido 65533.
- Techo por píxel, recalculado con Planck (`C2 = 1,4387752e4`, λ = 3,74 µm, área 140.625 m², k = 18,0):
  **9,69 / 9,63 / 9,51 MW** con fondo 250 / 260 / 270 K; a 336,5 K da 4,38 / 4,31 / 4,20 MW. Coincide con el
  auditor (9,6 MW; 4,31 contra el record de 4,21).
- **La cita, leída renderizando la página** (`sp426_p3.png`, PDF índice 2, impresa con la cabecera
  «ENHANCED VOLCANIC HOTSPOT DETECTION»): «eliminating, for each band, all the pixels with DN > 32 768 (i.e.
  the invalid data values), with the exception of the pixels with DN = 65 533, indicating saturated values.»
  La cita es exacta. Pero la misma página, columna derecha, dice el para qué: «we built a corrected spectral
  band ... by using the L21 or L22 radiance, depending on band 22 saturation (or not), respectively.» Es
  decir, el 65533 se conserva **para saber dónde cambiar de banda**, no para usar un píxel saturado como cota
  inferior. Nuestro MODIS hace eso mismo por otra vía (`merge_mir_bands`, `process_modis.py:337-339`, con
  `ENABLE_MODIS_B22_PRIMARY = False` en producción, leído con `pipeline.profile`). El paper no dice qué
  hace MIROVA si las dos bandas saturan, ni dice nada de VIIRS: la divergencia en V375 sigue SIN VERIFICAR,
  como el propio auditor anotó.
- **El efecto nunca ocurrió** (`v_c02_tmax_i04.py`, todo el corpus `data/mirova_equivalent/`, 23.389
  records VIIRS 375 con `t_max_i04_k`): máximo **354,24 K** (Chillán 2025-02-28 05:00, el incendio de febrero
  de 2025), 0 records sobre 355 K, 0 sobre 361,27 K. Control positivo presente: Chillán 2026-10-01 06:18
  VIIRS_NOAA20 con 336,51 K y 4,21 MW. Límite del instrumento: un píxel borrado no aparece en `t_max`, así que
  este cero no distingue «no saturó» de «saturó y se borró»; sólo dice que lo observado está a 7 K del techo.
- Gravedad 3: mecanismo real y latente, a un factor ~2 del régimen actual de Chillán, pero sin respaldo en
  el paper para VIIRS y sin caso observado.

## C-03. El modo de un solo píxel corta en 5 MW

**Veredicto: CONFIRMADO. Gravedad 4.**

`experiments/_s150_audit/verificador/v_c03_single_pixel.py`, función real
`pipeline.single_pixel_mode.apply_single_pixel_mode` con valores leídos de `pipeline.profile`
(`enabled=True threshold_mw=5.0 max_pixels=3`):

```
[1.6, 1.6, 1.6] -> (suma 4.8, publicado 1.6, modo True)
[1.7, 1.7, 1.7] -> (suma 5.1, publicado 5.1, modo False)
[2.49, 2.49]    -> (4.98, 2.49, True)
[2.51, 2.51]    -> (5.02, 5.02, False)
[1.0, 1.0, 1.0, 1.0] -> (4.0, 4.0, False)
control enabled=False [1.6]*3 -> (4.8, 4.8, None)
2026-10-01 05:24 VIIRS_NOAA21_750: pixeles=[2.6552, 1.828]  suma=4.4832 funcion=2.655 JSON pc.vrp_mw=2.655
2026-10-01 06:00 VIIRS_SNPP_750:   pixeles=[6.059, 4.1747, 0.8503] suma=11.084 funcion=11.084 JSON 11.084
2026-10-01 06:18 VIIRS_NOAA20_750: pixeles=[2.4907, 0.4315] suma=2.9222 funcion=2.491 JSON pc.vrp_mw=2.491
```

El control positivo (la función reproduce el `pc.vrp_mw` guardado) pasa en los tres. En 54 minutos de la misma
noche el tablero V750 de Chillán (que publica `pc.vrp_mw`, `frontend/index.html:1043-1061`) muestra 2,66,
11,08 y 2,49 MW: un factor 4 que es del corte y no del volcán. MIROVA para esas pasadas (OCR del snapshot):
9,0 / 10,0 / 7,06 MW. Agrego un matiz propio: la función tampoco es monótona en el **número de píxeles**: tres
píxeles de 1,6 publican 1,6, y cuatro de 1,0 publican 4,0. No verifiqué el conteo de exposición del auditor
(212 de 245 pasadas V750).

## D-01. El aviso de recall usa una vara «cráter» que no mira `distance_class`

**Veredicto: MATIZADO. Gravedad 3.**

- Código, confirmado: `scripts/auto_audit_weekly.py:316-324` agrega a `crater` todo cúmulo con
  `0 < pc.vrp_mw <= CAP` y `centroid_dist_km <= INNER`, y sólo `dash` exige `distance_class` summit;
  `:374-378` decide el flag con `recall_crater_pct`.
- Reproducción del 2026-10-05 con el `main()` real y los insumos de ese commit
  (`v_d02_estado_del_10_05.py`, extrae con `git show 80b358f6d:` los 11 JSON y los dos CSV):

  ```
  MODIS    {'n_noches': 7,   'recall_crater_pct': 85.7, 'recall_dash_pct': 28.6}
  VIIRS750 {'n_noches': 50,  'recall_crater_pct': 82.0, 'recall_dash_pct': 82.0}
  VIIRS375 {'n_noches': 194, 'recall_crater_pct': 92.8, 'recall_dash_pct': 92.8}
  ```

  Idéntico a `data/audit_continuous/latest.json` de ese commit (control positivo).
- Lo que cambia: con **n = 7 y `MIN_N_RECALL = 15`** (`:68`), MODIS no podía levantar ni bajar el aviso en
  esa ventana con ninguna de las dos varas; y en V375 y V750 las dos varas coinciden. En esta ventana la
  vara no decidió nada. El defecto es de diseño y real: cuando MODIS junte 15 noches, el audit verá 85 % donde
  el operador ve 29 %, y esa es justamente la etiqueta `far` que esconde el cráter (A46, A81). Con los datos
  de hoy (relleno del apagón incluido) la misma ventana da MODIS 100,0 / 42,9: parte del 28,6 era el apagón.

## D-02. La auditoría semanal confunde el apagón con una falla de detección

**Veredicto: CONFIRMADO. Gravedad 4.**

Mismo script, mismos insumos del commit `80b358f6d` (control positivo arriba):

```
ultimo dia con dato: 2026-10-02 | dias con dato: 58 | dias con deteccion crater (lo que cuenta el guard): 58
VIIRS375: n=194 fallos=14; de esos fallos, sin NINGUN record nuestro: 11
  [Isluga 10-03, 10-04, 10-05; Lastarria 10-03; Llaima 10-03; NevadosDeChillan 10-03, 10-04, 10-05;
   PlanchonPeteroa 10-04, 10-05; Tupungatito 10-03]
  | recall sobre noches con dato: 180/183 = 98.4 %
VIIRS750: fallos=9, sin record: 2 (Chillán 10-04, 10-05) | 41/48 = 85.4 %
MODIS:    fallos=1, sin record: 1 (Chillán 10-05)        | 6/6 = 100.0 %
```

- El issue #757 («recall VIIRS375 92.8% < banda 93.4%») se explica entero por el apagón: sobre las noches en
  que teníamos dato el recall era 98,4 %, sobre la banda. Y las noches perdidas incluyen tres de Chillán en
  plena fase eruptiva. Contraprueba con los datos de hoy, después del relleno del 10-08
  (`v_d01_d02_audit_semanal.py`): la misma ventana da V375 98,5 % (191/194), veredicto VERDE.
- **La guarda de cobertura**: confirmado que cuenta días con detección y no días con dato.
  `dias_nuestros` (`:390`) sale de las claves de `ours`, que sólo se crean dentro de la condición de cráter
  (`:319-320`; el `ours.get()` de `:336` no crea claves). En esta ventana los dos números coinciden (58 y 58),
  así que esa parte no cambió el resultado. Lo que falló fue el diseño de la guarda: un umbral de 80 % de los
  61 días no ve un apagón de 3 días al final de la ventana (95,1 %), aunque esos 3 días concentren 11 de 14
  fallos. La guarda mide la ventana completa; el daño estaba en la cola.
- **DEGRADADO no abre issue**: `audit-weekly.yml:85` sólo crea issue `if [ "$VERDICT" = "FUERA_DE_BANDA" ]`.
  Confirmado.

---

## Hallazgos propios

### V-1. Las alertas más fuertes de la fase eruptiva de Chillán no llegan a la referencia MIROVA del tablero

- **ARCHIVO:LÍNEA**: `scripts/rebuild_mirova_from_consolidado.py:1-25,150` (lee sólo el consolidado, la
  nota del JSON dice «OCR-derived records intentionally excluded»); `frontend/index.html:975` (el tablero
  carga sólo `data/mirova/<v>.json`).
- **QUÉ PASA**: MIROVA publicó para Chillán el 2026-10-01 05:24 (V750 9,0 MW, V375 6,28) y 06:00 (V750 10,0 MW
  rotulado «Moderado» por el OCR, V375 5,07) sólo en sus imágenes; el canal OCR las tiene
  (`data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`), el consolidado no. `data/mirova/NevadosDeChillan.json`
  (generado 2026-10-08 16:27) no trae ninguna de las dos pasadas: para el 10-01 tiene 01:45, 04:42, 06:18,
  08:35 y 18:42. En el OCR hay 5 filas `ALERTA_TERMICA_OCR` «Moderado» y 9 «Alto» en total (1.049 filas).
- **CÓMO SE VE EN EL DASHBOARD**: en la pasada más intensa de la noche, nuestra barra V750 (11,08 MW a las
  06:00) aparece sin el punto de MIROVA al lado, y la de las 05:24 también. El operador lee «MIROVA no lo vio»
  donde MIROVA sí lo vio.
- **CONFIANZA**: CONFIRMADO para el archivo que carga `index.html`; SOSPECHA sobre si otra vista
  (`comparacion.html`, `diario.html`) muestra el OCR, que no revisé.
- **GRAVEDAD 3**: no toca nuestra detección; sí la confirmación externa justo en el régimen que importa.
  Las rotulaciones de clase del OCR («Medio», «Alto» con 1 a 5 MW) no son las de MIROVA y no deben usarse como
  clase sin verificarlas.

### V-2. El modo de un solo píxel tampoco es monótono en el número de píxeles

Parte de C-03 que el auditor no midió: con el corte en 3 píxeles, `[1,6]×3` publica 1,6 y `[1,0]×4` publica
4,0 (misma salida de `v_c03_single_pixel.py`). Un cúmulo que gana un cuarto píxel débil puede triplicar la
magnitud publicada. CONFIRMADO. Gravedad 3.

### V-3. El cron del NRT corre unas 4 veces al día, no 12 (SOSPECHA de que ya esté medido)

`nrt.yml:12` pide `0 */2 * * *` (12 por día). Entre el 2026-09-25 y el 2026-10-02 hubo **34** corridas
(`gh api .../workflows/nrt.yml/runs?created=2026-09-25..2026-10-02`), unas 4,25 por día. No lo investigué: el
repo tiene `tests/test_cadencia_cron_s133.py` que mide la puntualidad del cron, así que puede ser conocido.
Afecta A-1 y A-2: el monitor cuenta «3 corridas» y con esta cadencia eso son ~17 h, no 6. Gravedad 2.

---

## VERIFICADO LIMPIO

- **No hubo pipeline zombie al inicio del apagón.** Entre el último record (2026-10-02 07:35) y la primera
  falla (2026-10-03 07:36) hubo cinco corridas verdes (10-02 11:55 a 10-03 00:56). Ninguna cubría una ventana
  nocturna nueva; la primera que la cubría ya falló por el token. Comando: `gh api .../nrt.yml/runs?created=2026-09-30..2026-10-05`.
- **La recuperación rellenó el hueco.** Con los datos de hoy la ventana 08-06 a 10-05 tiene 61 de 61 días con
  record (`v_d01_d02_audit_semanal.py`, bloque (b)).
- **El filtro del rebuild no deja pasar NULO** (control negativo de `v_bh4_rebuild_clases.py`), y su
  `assert` de defensa (`:121-122`) está presente.
- **El techo I4 del auditor C es correcto** (9,6 MW por píxel) y su comprobación a 336,5 K también.
- **El control positivo del audit semanal reproduce exacto** `latest.json` del commit `80b358f6d`, así que
  `scripts/auto_audit_weekly.py` es determinista con los mismos insumos.
- **Ningún archivo del repo fue modificado** fuera de `experiments/_s150_audit/verificador/` y este informe:
  `git status --short data/mirova data/audit_continuous` vacío después de correr los scripts. La carpeta
  `experiments/_s150_audit/verificador/snap_80b358f6d/` contiene copias de solo lectura extraídas con
  `git show` (11 JSON y 2 CSV) y puede borrarse. (Nota del orquestador, S150: se borró antes de commitear;
  se reconstruye con `git show 80b358f6d:<ruta>` de cada archivo.)
- **No leí ni copié valores de credenciales**: de `settings.json` sólo imprimí eventos de hook y comandos.

## Fuentes externas consultadas

- [actions/runner-images #14748](https://github.com/actions/runner-images/issues/14748), anuncio oficial de la
  migración de `ubuntu-latest`.
- [packages.ubuntu.com, libhdf4-dev](https://packages.ubuntu.com/search?keywords=libhdf4-dev&searchon=names&suite=all&section=all).
- PyPI JSON de `pyhdf` (`https://pypi.org/pypi/pyhdf/json`) y `actions/python-versions/versions-manifest.json`.
