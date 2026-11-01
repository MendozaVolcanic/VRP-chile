# Verificador con contexto limpio, frente 3 (instrumentos de medición), S155

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f3`, detached en `cb90031a` (origin/main). Hora del servidor al
empezar: 2026-10-19 11:04 UTC (`gh api -i`, cabecera Date). No leí `experiments/_s155_audit/frente_3/`. No
modifiqué nada fuera de este directorio.

## Instrumento usado y sus dos preguntas

Todo número de abajo sale de `scripts/auto_audit_weekly.main()` **sin portar**, redirigiendo `OUTDIR`, `ROOT`,
`CONS`, `OCR` y los argumentos por defecto de `alertas_mirova` y `cargar_referencia_unificada` a este directorio
(`simular_cron.py`). El régimen de cada record se toma de `regimen.codigo_sha`: los 11 sha observados descienden de
`34cea39e` (git merge-base, salida en esta sesión); un record sin `regimen` es C0.

1. Si lo medido estuviera roto, ¿lo vería? Sí para recall, magnitud y falsas: es el mismo código del cron.
   Control de instrumento: con la referencia del repo (snapshot del 14-oct) reproduce exacto los números del
   auditor (V375 95,6 % n=204, V750 78,4 %, Chillán 0,684, Tupungatito 0,54, falsas V375 33,3 % n=877), y
   `magnitud_por_noche.py` reproduce exacto los runs viejos (0,707 n=24 al 12-oct, 0,647 n=23 al 14-oct; "CONTROL OK"
   en 4 de 4 configuraciones).
2. ¿Instrumento muerto? Cada corrida imprime n por bucket; la separación por régimen tiene control: la raíz K tiene
   0 records antes del 2026-09-18 y la C0 tiene 0 records con `regimen` (`simular_cron_salida.txt` l. 47).

Ventanas (hoy = 2026-10-19): recall y magnitud 2026-08-20 a 2026-10-19; falsas 2026-09-01 a 2026-10-19.

**Defecto de mi simulación que declaro**: el cron regenera la unión histórica por la API de GitHub; yo la aproximé
con la unión commiteada (14-oct) más el snapshot del 14-oct (`historico_combinado.csv`). El consolidado remoto de hoy
tiene 42.006 filas contra 42.614 del snapshot (perdió unas 150 por mes de mayo a septiembre).

## Veredictos sobre la lista del auditor

| ID | Veredicto | Mi gravedad | Nota |
|---|---|---|---|
| F3-01 | PARCIAL | 4 | Mezcla confirmada (48,6 % de records C0 en la ventana). Pero los números del auditor salen de la referencia **sin refrescar**; el cron baja la del remoto primero. Con referencia fresca: V375 95,8 % mezcla, 99,1 % C0 (n=110), 92,3 % K (n=104); V750 80,0 %, **sobre** la banda 79,5: el cron abriría con **2 flags** (Chillán 0,653, Tupungatito 0,52), no 3. El flag V750 está al filo y depende de la referencia. Y con D-9 el V375 de K sube a 96,7 % (n=91): el déficit escondido real está en V750 (73,3 %, n=30, todas bajo 0,4 MW) y MODIS (66,7 %, n=12, con una protegida). |
| F3-02 | CONFIRMADO | 4 | 33,3 % (n=877) con referencia del repo; 31,1 % (n=940) con la fresca = 86,5 % C0 (n=325, 9-01 a 9-17) y 1,8 % K (n=615). `linea_historial` l. 353 lo escribe a history.jsonl. Disparador §4.9 (iii) de REGLA_ADOPCION l. 148-150: cota 0,0383; la mezcla da ~8 veces, no ~10. La parte C0 sale de la ventana el 2026-11-17 (inicio = hoy − 60 ≥ 9-18), salvo que el reproceso histórico (#852) la reescriba antes. El propio script declara el principio (l. 56-61) y no lo aplicó a K. |
| F3-03 | CONFIRMADO | 4 | `cambio_detector.js:16` = 2026-10-18T09:57:30Z; la línea se dibuja en esa fecha del eje x (l. 71-78). El escalón cae en 9-18: V375 en negativos limpios 86,5 % (9-01 a 9-17, n=325) a 1,9 % (9-18 a 10-17, n=590); V375 todas las pasadas 87,3 % a 19,1 %. No reproduzco el 87,1/14,9 ni el 90,6/6,2 de Chillán (otra definición); la fecha del escalón sí. |
| F3-04 | CONFIRMADO | 4 | MIROVA MODIS 2026-10-12 07:20, 2,18 MW a 2,24 km, ALERTA "Bajo" (consolidado). K: 0 píxeles, sin cúmulo. Sombra (`experimental_v2`): cúmulo 1,376 MW a 1,683 km etiquetado `far`; el predicado del tablero (node) da publica = 0 en los dos. MODIS n ≤ 14 en los 12 runs desde 2026-08-03 (14 hoy con referencia fresca): con `MIN_N_RECALL = 15` (l. 91) el flag MODIS no puede salir. No hay criterio de protegidas en el script. |
| F3-05 | CONFIRMADO | 3 | 0,707/24 y 0,647/23 reproducidos desde los commits `0a3b4e3ac` y `f3b414213`. C0 hoy: 0,835 (n=8) antes del 12-sep y 0,395 (n=6) desde el 12-sep. Mezcla 0,52 a 0,54; K 0,364 (n=10) con referencia fresca, 0,281 (n=9) con la del repo. n chicos. |
| F3-06 | PARCIAL | 3 | Usa `pc.vrp_mw` (l. 413) y junta sensores (l. 440): confirmado; Chillán K = MODIS 0,485 (7), V750 0,687 (13), V375 0,553 (17) en una sola mediana 0,635. "En las mismas pasadas K/C0 da 1,0": vale en 7 de 8 volcanes con pares contra la sombra (10-02 a 10-18), **no en Láscar: 0,705 (n=18)**. La caída por menos pasadas por noche es compatible (la sombra publica cúmulos que K no, 36 a 115 por volcán) pero no la medí como causa. |
| F3-07 | CONFIRMADO | 2 | l. 157-159 pega "déficit de régimen débil S124" a todo sub-banda (Tupungatito C0 antes del 12-sep está en banda, 0,835). El cuerpo del issue dice "magnitud [0.5-2.0]x" (workflow) y el código juzga (0,7; 1,4) (l. 132). FUERA_DE_BANDA no deduplica (a diferencia de DEGRADADO); #779 sigue abierto y hoy saldría FUERA_DE_BANDA. |
| F3-08 | CONFIRMADO | 3 | El flag usa `recall_crater_pct` (l. 469-470). C0 MODIS 100 % cráter contra 30 % tablero (latest.json del 14-oct, n=10). K V375: 5 de 8 pérdidas ≤ 0,05 MW (0,01, 0,02, 0,01, 0,01, 0,05); con D-9, 96,7 %. |
| F3-09 | CONFIRMADO | 3 | Ningún script, workflow ni vista lee `codigo_sha` (sólo `store.py` lo escribe; `reemplazar_ventana_reproceso.py:59` lee `regimen.perfil`). latest.json sólo menciona "regimen" como focal/nevado. |
| F3-10 | CONFIRMADO | 2 | `evaluarCorrida` mide `created_at` del run. Run 39125546355: creado 2026-10-18 12:01, `queued`, 177 jobs, 138 terminados, job más largo 2,14 h; ~23 h de edad a las 11:05 UTC. #824: 25 comentarios del 15 al 19 de octubre, abierto. |
| F3-11 | CONFIRMADO | 1 | `pipeline/audit_metrics.py` replica `mirovaEqVrp` (cúmulo), no `isValidDetection`/f5_core/artefactos. Sólo lo importan tests y experimentos. |
| F3-12 | CONFIRMADO | 1 | Los avisos A119 salen por stderr (`simular_cron_stderr.txt`); 0 apariciones en el latest.json simulado. |

## Hallazgos propios

**V3-01. La simulación del cron sin el paso de refresco no es la del cron** (gravedad 2, CONFIRMADO). El primer
paso de `audit-weekly.yml` baja el consolidado y el OCR del remoto. Con el snapshot del repo (14-oct) el K de V375
da 91,5 % (n=94) y V750 78,4 % con flag; con la referencia fresca 92,3 % (n=104) y V750 80,0 % sin flag. Cualquier
predicción de "qué issue abre el lunes" tiene que bajar la referencia. Script: `regimen_ref_repo.py`.

**V3-02. 26 records C0 siguen dentro de la ventana "reprocesada con K"** (gravedad 2, CONFIRMADO). Todos MODIS
Terra NRT, del 28-sep, 2-oct y 10-oct, sin `regimen`, que el reproceso no reemplazó (el reproceso no trajo esa
pasada). El tablero publica 2: Puyehue-Cordón Caulle 2026-09-28 01:25 (0,852 MW) y 2026-10-10 01:05 (0,378 MW).
Control: el mismo predicado publica 105 de 334 records K de Chillán. El reproceso histórico (#852) conserva las
pasadas ausentes por diseño, así que va a dejar más huérfanos repartidos en la serie. Script: `huerfanos_c0_salida.txt`.

**V3-03. Con D-9 el diagnóstico de F3-01 cambia de sensor** (gravedad 3, CONFIRMADO). El "déficit de K tapado" en
V375 es casi todo alertas de 0,05 MW o menos, que la regla decidida (D-9) saca del recall: 88 de 91 = 96,7 %. Lo que
la mezcla sí esconde es V750 (22 de 30) y MODIS (8 de 12, con Chillán 2,18 MW). Script: `perdidas_k.py`.

**V3-04. Separar por régimen dentro de este script lo vuelve DEGRADADO por construcción** (nota de diseño, no
defecto). Las corridas C0 y K salen con cobertura 52,5 % y C0 con "9 días sin datos al final". Quien arregle F3-01
tiene que adaptar la guarda de cobertura, o el veredicto separado nunca sale.

**V3-05. El cron programado corre 6 a 10 h tarde** (gravedad 1, CONFIRMADO). `0 9 * * 1` y los runs de schedule
arrancan entre 15:43 y 18:42 UTC (`gh run list`). Sin efecto en los números; sólo en cuándo se entera alguien.

## VERIFICADO LIMPIO

- El "dash" reconstruido del audit (l. 415-420) coincide con el predicado real del tablero ejecutado con node en
  **todas** las noches con alerta de la ventana: MODIS 14, V750 55, V375 214, 0 discordantes (`dash_vs_node.py`).
- El recall excluye noches sin ningún record nuestro (`noches_sin_datos`, l. 316-334): en la mezcla de hoy, 0.
- La magnitud del audit es reproducible desde commits viejos con el código de hoy (control OK en 4 de 4).
- Perfil de producción hoy: `ENABLE_TEST1_PATH False`, `ENABLE_TESTS_23_PROSE_BRANCH True`,
  `ENABLE_MODIS_B22_PRIMARY True`, diurnos apagados (leído de `pipeline.profile`).
- La sombra `experimental_v2` es C0: `enable_test1_path: true`, `prose_branch: false`, `b22: false`
  (`pipeline/profiles/experimental.yaml` l. 71-76); cubre 2026-10-02 a 2026-10-18 en Chillán.

## Archivos

Scripts: `simular_cron.py`, `magnitud_por_noche.py`, `regimen_ref_repo.py`, `escalon_marca.py`, `perdidas_k.py`,
`dash_vs_node.py`, `k_vs_sombra.py`. Salidas crudas: `*_salida.txt`, `simular_cron_resumen.json`,
`magnitud_por_noche.json`, `run_39125546355.json`, `out_*/latest.json`. Referencia bajada: `ref_fresca/`
(fecha en `fecha_descarga.txt`). Las carpetas `raiz_*` son copias filtradas de los JSON (desde 2026-08-01), borrables.
