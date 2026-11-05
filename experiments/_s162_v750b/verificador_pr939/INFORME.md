# Verificación con contexto limpio del PR #939 (rama `s169-roi-v750`, punta `56bdbe1df`, base `main` `82b55de0d`)

Hecha el 2026-11-03 entre las 19:15 y las 19:35 UTC (hora del servidor de GitHub, `gh api -i`, cabecera `Date`).
Sólo lectura sobre el worktree `C:/Users/nmend/vrp-wt/s173-roi-v750-b4` (árbol limpio antes y después, `git status`
vacío). Lo escrito por mí vive en `C:/Users/nmend/vrp-wt/verif_pr939/` (`suite_completa.txt`, `mut_yaml/`, este
informe). Sin `VRP_PROFILE` salvo donde se dice; `PYTHONIOENCODING=utf-8`.

## Veredicto global: CONFIRMADO EN PARTE

El PR hace exactamente lo que dice en el código y en las pruebas: el YAML cambia sólo en las 2 ROI y los 2 renglones
de comentario, byte a byte lo que produce el script con `--brazo B4`; los 34 siguen en `def`; producción no corre la
vía de VIIRS 750; las pruebas caen con el YAML de `main` y con cada mutación probada; la guarda de bytes de S172 fija
exactamente el bloque de los 11 con B4; la suite completa da 3.116 / 32 / 2 / 0 sobre la punta del PR; el CI está
verde; las citas al `.m` y a la regla de congelamiento dicen lo que el documento afirma; y los números que el PR
toma de la lectura de V750-B coinciden con `veredicto_v750b.txt` y con el informe del verificador. Lo que no se
sostiene tal como está escrito son afirmaciones de documento: una distancia redondeada hacia abajo (VPR939-01), un
«el lector separa» en presente que hoy es un pendiente (VPR939-03), un «CONFIRMA» global que el informe del
verificador no enuncia (VPR939-02), y la omisión de que producción sí lee el archivo modificado por la vía de MODIS
(VPR939-05, efecto nulo verificado). Nada de eso cambia la ROI ni lo que llega a la sombra.

## 1. Cobertura: qué se revisó y con qué

| qué | cómo | resultado |
|---|---|---|
| Diff completo `origin/main...HEAD` | `git diff --stat`; 8 archivos, 483 inserciones, 6 borrados | igual a la lista de archivos de `gh pr view 939` |
| YAML: sólo 2 ROI y 2 comentarios | diff línea a línea en Python (8 líneas: 4 viejas, 4 nuevas) | las 2 líneas de volcán y los 2 renglones del comentario, nada más |
| YAML: 34 en `def` | conteo `roi_v750: def}` 43 y `sens}` 2 en HEAD (45 y 0 en main); cola del archivo desde el byte 3.907 idéntica a la de main desde el 3.805 | los 34 no cambian ni un byte |
| YAML = script | `variante(main, "B4") == blob HEAD` | `True` (byte a byte, incluido el LF) |
| Guarda de bytes S172 | `sha256(HEAD_LF[:3907])` | `b1ad85fb...` = el del test; el byte 3.907 cae justo tras `Villarrica: {... roi_v750: def}\n`, antes de `# S172, sombra de los 34`; `sha256(main_LF[:3805])` = `da755f3e...` (el valor histórico) |
| Producción no corre V750 | `pipeline.profile` por perfil (A89) | `mirova_equivalent`: V750 False, V375 False, MODIS **True**; `experimental`: las tres False; `sombra_codigo_mirova` y `sombra_34`: las tres True; sin `VRP_PROFILE`: `mirova_equivalent`, False |
| Quién lee `roi_v750` | `grep` de `grilla_del_volcan`, `clave_roi`, `roi_v750`, `grillas_mirova` en pipeline, scripts, tests, workflows, frontend | `process_viirs_mod.py:507` (sólo comprueba que la grilla exista) y `mirova_v750_codigo.py:797` con `cfg["clave_roi"]` = `roi_v750` para la familia VIIRS750; MODIS lee `roi_modis` (`process_modis.py:641`), VIIRS 375 lee `roi_v375` y arma siempre `caja_v375` (`mirova_v750_codigo.py:817-818`) |
| El valor llega a la caja | `caja_roi("sens")` en los dos volcanes | 441 celdas sensibles (21 × 21); el cráter de volcanoes.yaml cae en ellas en los dos; con `def` no caía en ninguno |
| B4 de la lectura = `sens` del YAML | `probe_v750b.cajas()` contra `MV.caja_roi` | `B0 == caja_roi("def")` True y `B1 == caja_roi("sens")` True sobre 67 × 67; el analizador arma B4 con B0 y B1 (docstring del probe l. 7 a 8) |
| Pruebas nuevas | `pytest` de los dos archivos en el worktree | 104 passed (38 + 66) |
| Nulo de mutaciones | `python experiments/_s169_roi_v750/mutar_roi_v750b.py` desde el worktree (escribe en TEMP) | 11 líneas idénticas a `mutar_roi_v750b_salida_s173.txt`, mismos conteos de fallas por mutación; M8 atrapada (7 failed) |
| Mutaciones del YAML (no del script) | copia del árbol en `verif_pr939/mut_yaml/`, 8 variantes del YAML, 41 pruebas | YAML de main: 4 fallan; Láscar a `sens`: 3; Antuco (sombra) a `sens`: 2 (`test_hoy_rige_b4` y `test_las_34_entradas_son_exactamente_las_de_la_regla`); Tupungatito vuelve a `def`: 3; nota del brazo dice B1: 2; `x0` de Cordón Caulle +1 m: 1 (la guarda de bytes); todo en CRLF: 0 (ver VPR939-07) |
| Suite completa | árbol quieto, `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, sobre `56bdbe1df` | **3116 passed, 32 skipped, 2 xfailed**, 0 failed, 382 s (el PR lo dice sobre `a2a8a171d`; el commit siguiente agrega sólo M8 y su salida: `git show --stat 56bdbe1df`, 2 archivos, 15 líneas) |
| CI | `gh pr checks 939` | `pytest pass 7m22s` (run 41701990810) |
| Tag defensivo | `git rev-parse pre-s173-roi-v750-b4^{commit}` y `ls-remote` | `82b55de0d` local y remoto (tag anotado `e678be2ab` → `82b55de0d`) = `merge-base origin/main HEAD` |
| Cita del `.m` l. 120 a 125 | `sed -n 118,126p` con numeración | la cita es verbatim; el texto citado ocupa las l. 120 a 123, el párrafo sigue hasta la 125 (la frase sobre excluir volcanes vecinos, no citada); el bloque de BOX parte en la l. 105 como dice el doc |
| Regla de congelamiento | `git show origin/loop/activo:docs/.../2026-10-24-programa-replica-por-sensor.md`, l. 440 a 475 | §12.6 parte en la l. 452; «Sí, congelar» en la l. 454; la excepción «la ROI que elija V750-B en `pipeline/grillas_mirova.yaml` (clave `roi_v750`)» en las l. 460 a 461; «l. 458» cae en el «Por qué» de la misma sección |
| Lectura de V750-B | `git show` de `veredicto_v750b.txt`, `INFORME_VERIFICADOR.md`, `manifiesto.json` en `origin/claude/s162-viirs750-2-918174` (commits `70c5b2808`, `1c10db660`, `d7d15b450`, los tres en el remoto) | compuerta ABIERTA; 1 SIN DATO (Láscar 2026-08-25, negativo limpio) sobre 5.867; controles en verde; P1 = 0 en B1, B2, B3 y B4 en las tres ventanas y los tres canales; ningún GANA; B4 SIN SUSTRATO neto -1; control positivo: B0 pierde 11 de 11 protegidas de Cordón Caulle y B1 publica las 11; verificador: A1, A2, A3, A5, A6 CONFIRMADA, A4 CONFIRMADA EN PARTE (B3 elegible y PIERDE, la regla lo excluye bien); VV750B-01 a 07, los siete de gravedad 1 |
| Orden del §6.3 | `PREREGISTRO_V750B.md` l. 124 a 146 | «B4, B2, B5, B1, B3»; con B3 fuera por PIERDE quedan `[B4, B2, B1]` → B4; el §6.5 exige documentar que B2 o B4 es fidelidad al `.m`, que es el §3 del doc de adopción |
| Frase de Nicolás | bitácora `tasks/LOOP_OBJETIVOS.md` §6 en `loop/activo`, entradas 18:55 y 18:56 UTC del 2026-11-03 | «Sí, confirmo B4» relayada; «El merge a main pide frase aparte» |
| Régimen en los records | `pipeline/store.py:89-93` y `mirova_v750_codigo.py:708` | cada record lleva `regimen.{perfil, codigo_sha}` y `diag_codigo_mirova.roi`: el lector puede separar B0 de B4 |
| Estado de la sombra | `gh run list` de `sombra-codigo-mirova.yml`, `gh api contents` de `data/sombra_codigo_mirova` | últimos runs 10-30, 10-31, 11-01 y 11-02 23:00 UTC, todos `success`; `data/sombra_codigo_mirova/` no existe en `main` (404); el yml dice que hasta el 2026-11-03 cada job sale sin ventana; a las 19:29 UTC de hoy el cron de las 15:00 no había corrido |

## 2. Hallazgos (gravedad 1 menor, 2 media, 3 bloqueante)

- **VPR939-01 (gravedad 1).** El PR y `ADOPCION_ROI_B4.md` §1 dicen que en Tupungatito «el cráter está a unos 4 km
  del centro». Medido con la grilla y `volcanoes.yaml` (`vent_lat`/`vent_lon`): **4,86 km**, desvío de 6 filas y 3
  columnas; el pre-registro (l. 33) dice 4,9 km. Es un redondeo hacia abajo, no un error de método; en Cordón Caulle
  el cráter está a 7,63 km (el pre-registro dice 7,6) y el «4,6 a 10,5 km» del calor de MIROVA viene del
  pre-registro l. 30 (no lo re-medí: sale del censo S159).
- **VPR939-02 (gravedad 1).** El PR y el doc dicen «Verificador limpio (Fable): CONFIRMA». El informe del verificador
  no enuncia un veredicto global ni nombra el modelo: trae cinco afirmaciones CONFIRMADA y una CONFIRMADA EN PARTE, y
  el commit `d7d15b450` lleva `Co-Authored-By: Claude Opus 5.5`. El «CONFIRMA» es síntesis de la coordinadora; lo que
  sí se sostiene es el detalle que el doc da (A4 en parte sólo por la frase sobre B3, siete hallazgos de gravedad 1).
- **VPR939-03 (gravedad 2).** `ADOPCION_ROI_B4.md` §5 afirma en presente que «el lector de la sombra separa las
  pasadas de Cordón Caulle y Tupungatito por la ROI con que se procesaron (antes o después de esa corrida, o por el
  sha de `main`)». Ningún script de `experiments/_s162_v750a/` (14 `.py` en `origin/main`) lee `regimen`,
  `codigo_sha` ni el `roi` del record (0 coincidencias; el único que filtra por `codigo_sha` es
  `scripts/revisar_sombra.py:171`, que revisa la corrida, no lee la sombra). Los insumos para separar existen
  (store.py:89-93 y mirova_v750_codigo.py:708), pero la separación es un **requisito pendiente del lector**, no un
  hecho; conviene escribirlo como tal, porque el PR dice «el lector no debe mezclarlas con las de B0» y hoy nada lo
  impide por código.
- **VPR939-04 (gravedad 1, observación).** «La sombra de los 11 corre con B0 hasta el merge» describe el código, no
  datos: `data/sombra_codigo_mirova/` no existe en `main` (404), la sombra arranca el 2026-11-03 por diseño
  (`sombra-codigo-mirova.yml` l. 13 y 117) y a las 19:29 UTC de hoy el cron de las 15:00 UTC no había corrido (el
  último run es del 11-02 a las 23:00 UTC, ya 8 h tarde respecto de su cron; lección S171). Si el merge ocurre antes de
  esa corrida, toda la sombra de VIIRS 750 corre con B4 y la noche mixta de la §5 no existe; igual hay que anotar la
  primera corrida con el sha, como el PR pide.
- **VPR939-05 (gravedad 1).** «Producción no cambia» es cierto en efecto, pero el PR calla que producción **sí lee**
  el archivo modificado: `mirova_equivalent` tiene `ENABLE_MODIS_CODIGO_MIROVA = True` y la vía de MODIS llama a
  `grilla_del_volcan(..., clave_roi="roi_modis")` sobre `pipeline/grillas_mirova.yaml`. Verificado con
  `VRP_PROFILE=mirova_equivalent`: `roi_modis` no existe en el YAML y resuelve `def` en los dos volcanes (el
  `roi_v750` de la misma entrada da `sens`); las demás claves de las 45 entradas son idénticas (prueba
  `test_variante_cambia_solo_roi_v750` y mi diff); la suite completa pasa. Es transparencia, no defecto.
- **VPR939-06 (gravedad 1).** La regla de congelamiento (§12.6, l. 460 a 461) exige anotar cada excepción «en
  `tasks/LOOP_OBJETIVOS.md` §6 con su commit y qué sensor toca». La bitácora tiene las entradas de las 18:55 y 18:56
  UTC (sin sha, el PR no existía) y el doc §4 promete el sha al mergear. Queda para el merge, no para el PR.
- **VPR939-07 (gravedad 1, por diseño).** La guarda de bytes de S172 normaliza `\r\n` a `\n` antes de hashear y
  `.gitattributes` no fija `eol` para el YAML: un archivo entero en CRLF pasa las 41 pruebas (medido). No mide el fin
  de línea; el blob de HEAD es LF y el script escribe con `newline=""`. Sólo para que nadie crea que la guarda cubre
  eso.
- **VPR939-08 (gravedad 1).** La cita «l. 458» del doc §4 cae en el cuerpo de §12.6 (que parte en la l. 452; la
  frase de la excepción está en las l. 460 a 461). Correcta en sustancia, imprecisa en número.
- **VPR939-09 (gravedad 1, observación).** `sens` hace sensible el 21 × 21 (semilado 7,875 km) alrededor del centro
  de la grilla, mientras el pre-registro ubica el calor de Cordón Caulle a 4,6 a 10,5 km: B4 cubre ese campo sólo en
  parte. Lo medido basta para las protegidas (11 de 11 con B1 y B4) y el doc §3 ya dice que B4 no es la ROI exacta de
  MIROVA. No es un hallazgo contra el PR; es el límite de lo adoptado.
- **VPR939-10 (gravedad 1).** El texto citado del `.m` ocupa las l. 120 a 123; el doc lo rotula «l. 120 a 125»
  (el párrafo sí llega a la 125). La cita es verbatim.

## 3. Lo que se confirma tal cual (sin hallazgo)

Diff del YAML exacto (2 ROI + 2 comentarios, 0 bytes más); los 34 en `def`; el script reproduce el blob byte a byte;
el hash nuevo de S172 es `sha256` de los primeros 3.907 bytes LF del YAML de HEAD, que terminan justo en la línea de
Villarrica, y el resto del archivo es el de `main`; el valor anterior (3.805, `da755f3e...`) se reproduce sobre
`main`; `mirova_equivalent` no corre la vía de VIIRS 750 y ninguna ruta de producción lee `roi_v750`; el valor llega
a la caja y mueve la caja en Tupungatito; `probe_v750b` B1 es `caja_roi("sens")`; 38 de 38 pruebas nuevas, 4 caen
con el YAML de `main`; nulo 9 de 9 atrapadas con identidad y control, salida idéntica a la commiteada; suite
3.116 / 32 / 2 / 0; CI verde; tag `pre-s173-roi-v750-b4` = `82b55de0d` = base del PR; cron de la sombra `0 15 * * *`;
`sombra_34` con los 34 en `def`; cobertura, controles, elegibles, orden del §6.3 y hallazgos del verificador tal
como los resume el PR.

## 4. Lo que no verifiqué

- La frase «Sí, confirmo B4» de Nicolás: sólo la vi relayada en la bitácora de `loop/activo` (18:56 UTC) y en el
  doc; no tengo el chat.
- Que los runs 41615021658 y 41693265163 hayan ejecutado el código sellado: lo tomo del informe del verificador de
  la lectura (A1 y A6), no lo rehíce.
- El origen físico del «4,6 a 10,5 km» de Cordón Caulle (censo S159, `origin/s159-pruebas`): no lo re-medí.
- Si el cron de la sombra de hoy corre más tarde y con qué sha (sólo el estado a las 19:29 UTC).
- El diseño del lector de la sombra de V750-A fuera de `origin/main` (busqué en `loop/activo` y en la rama de V750
  archivos con «lector» o «sombra» en `_s162_v750a`: ninguno).
- La ejecución del paso «Commit sombra data» del workflow: `gh run view --log` no devolvió líneas; la ausencia de
  datos la verifiqué por la API de contenidos y por `git ls-tree`.
