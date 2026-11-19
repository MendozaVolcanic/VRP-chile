# Bloque de arranque S191 (escrito por S190, 2026-11-19 ~16:30 UTC)

> El bloque anterior (S190, escrito por S189) queda como histórico en `tasks/BLOQUE_ARRANQUE_S190.md`. El detalle de
> cada paso de S190 está en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entradas S190, de la más nueva arriba).
> **El estado se fijó con trabajo en curso** (ver tabla a, filas «corriendo»): nada de esto es definitivo hasta
> comprobarlo contra el remoto y contra `ps`.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | `618d0c93e`, ficha SDA **v1.46** (2026-11-19) | merge de #1058 a las 15:32:51 UTC |
| `loop/activo` | commit de este cierre, sobre `3c0701342` | `git ls-remote origin -h refs/heads/loop/activo` |
| PR de S190 en main | #1041 a #1046, #1048 a #1051, #1053 a #1059 (ficha v1.37 a v1.46) | bitácora 2026-11-19 14:05 y 15:40 |
| NRT con checkout al día (#1051) | en main; primera corrida (44521415639, 12:10 UTC) verde tras 2 relanzamientos por el espejo de Ubuntu; 0 duplicados en los 11 Tier A | bitácora 2026-11-19 12:45 |
| Historia de los 34: tandas 1 a 4 | **aplicadas**: 18 volcanes en `data/historia_34/` (tanda 4: run 44528546156, commit `4e6e873fa`, tag `pre-historia-34-tanda4`) | bitácora 2026-11-19 14:05 |
| Tanda 5 (Lanin, MochoChoshuenco, CarranLosVenados, AntillancaCasablanca, Osorno) | **corriendo**: run 44512397201; a las 15:20 UTC 71 de 165 terminados, 26 rojos, todos «Install deps» de la caída del espejo de Ubuntu de las 12:08 UTC | `D:\vrp-trabajo\temporales\s190\t5_fallas.txt` |
| Cadena de tandas 5 a 7 | **corriendo**: `D:\vrp-trabajo\temporales\s187_tanda2\cadena_5a7_s190d.sh` (PID 1148 al cierre; log al lado). Relanza rojos hasta 3 veces y sólo con 0 rojos despacha 6 y 7 | `ps -ef \| grep cadena_5a7` |
| Marcador de dato faltante sobre el cráter (paso A del plan F1M G3; Nicolás: «Sí, prepáralo») | **a medias, sin commit**: worktree `D:\vrp-trabajo\worktrees\s190-marcador-crater` (rama `s190-marcador-crater`, tag `pre-s190-marcador-crater` = `618d0c93e`) con `pipeline/mirova_v750_codigo.py` modificado, `tests/test_via_dato_faltante_crater_s190.py` y `tests/datos_s190_dato_crater/`. Lo hizo un subagente de S190 que al cierre corría la suite completa (pytest PID 23971). Salidas en `D:\vrp-trabajo\temporales\s190\marcador\` (`rojo_antes.txt`, `verde_despues.txt`, `mutaciones*.txt`, `nulo.txt`, `pruebas_del_modulo.txt`, `suite_completa.txt`) | `git -C D:/vrp-trabajo/worktrees/s190-marcador-crater status` |
| Auditoría Codex, ronda 2 | frentes 4, 6, 7, 8, 1 MODIS y 1 VIIRS cerrados y verificados; **frente 2**: pase ciego congelado en `D:\codex-vrp\_salida\ronda2\f2_auditoria_paseA` (8 hallazgos sin verificar; F2-101, gravedad 4 según Codex: en MODIS la cumbre de PCC y Tupungatito cae en la región conservadora). Codex en 59 % de la semana (reinicia 2026-11-24 04:20 UTC) | `D:\codex-vrp\_salida\ronda2\ESTADO_COORDINACION.md` §«TRASPASO 2026-11-19 ~14:40 UTC»; `hallazgos_verificados.csv` |
| A/B del día de la vía (sesión «Pasadas diurnas con la vía (#813)», local_1a9c0903) | **corriendo** en esa sesión: W2 a W4 cuadradas; W5 en segunda reparación (run 44558718517); W6 (44518650784) en cola; `cadena_ventanas.sh` (PID 1662) | su bitácora; issue #1052 |
| Programa por sensor | §12.10 escrita (estado al 2026-11-19, Tupungatito V750 medido, F4-101 medido, mejoras por sensor desde Codex) | `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` en `loop/activo` |
| Panel nuevo del #1046 (FP sólo con RUTINA, «sin distancia») | código publicado en Pages; **falta** que `sync-mirova-csv.yml` regenere `data/mirova/*.json` con `pasadas_tabla` (último sync 13:00 UTC, antes del merge) | `git show origin/main:data/mirova/Lascar.json` sin `pasadas_tabla` a las 15:20 |
| Sin commitear en `loop/activo` (no son de S190, no se commitean) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea, regla del proyecto) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | F4-101: la vía publica VRP sin restar fondo cuando el fondo no se puede estimar (`L_bk` 0): 19 de 73.952 records, 12 de 1 MW o más, un FP probado (PCC 2026-03-16 MODIS 2,5 MW, MIROVA sin alerta) | (a) tratar `L_bk` 0 como escena no medida; (b) sólo marcar; (c) dejar como MIROVA | (a), después de mirar si MIROVA publicó los 9 casos de 2025 (es copia fiel del `.m`, así que MIROVA puede tener el mismo FP). Cambia detecciones: ficha y A45 en espíritu |
| 2 | Paso B del marcador del cráter (qué hace el tablero con la marca) | B1 «sin dato» en vez de noche negativa; B2 sólo avisar | Esperar unas semanas de marcas del paso A y decidir con el conteo |
| 3 | Decisiones del frente 6 (cuándo el NRT se pone rojo y cuánto busca: F6-103, F6-104, F6-107, F6-114, F6-V301) | ver `D:\codex-vrp\_salida\ronda2\PENDIENTES_F6_PARA_NICOLAS.md` | Rojo cuando un volcán no mide nada y fila «no medida» por pasada fallida (F6-104, F6-112); el resto según el documento |
| 4 | F1M-114: docstring de `pipeline/process_modis.py` l. 27 y 28 (cita retirada y fórmula Stefan-Boltzmann en vez de Wooster sobre ΔL) | autorizar A45 para un commit sólo de docstring | Sí: sin efecto numérico |
| 5 | 34 archivos de abril de los 34 en `data/mirova_equivalent/` (2.843 records del detector anterior, sin marca de régimen, 476 con VRP > 0; nadie los lee) | archivar a una carpeta de legado con tag, borrar, o dejar | Archivar con tag (A38) |
| 6 | Reintento automático en `sombra-34.yml` y `sombra-codigo-mirova.yml` (un CMR caído en un volcán abre issue de alerta falsa) | sí o no | Sí, reintento de los jobs caídos dentro del workflow |
| 7 | D-10 (#813): abrir el día en la réplica | esperar el A/B del día (W5 a W7) | Decidir con el A/B completo |
| 8 | Rotar el PAT que sigue en `C:\Users\nmend\.claude\settings.json` | | Sí (pendiente de arrastre, lo hace Nicolás) |

Preguntas de Nicolás de S190 sin respuesta explícita: ninguna detectada. La última («Sí, prepáralo») se está ejecutando (fila del marcador).

## c. Lo aprendido (S190, ya en memoria salvo donde se dice)

- **REGLA GENERAL (workflows):** `actions/checkout` sin `ref` baja el SHA del despacho; una corrida encolada en un grupo de concurrencia parte de un commit viejo y duplica datos. Usar `ref: ${{ github.ref }}`. Memoria `feedback_s190_checkout_sha_congelado.md`; guard `tests/test_nrt_checkout_rama_s190.py`.
- **REGLA GENERAL:** `gh run download -D /d/...` con `MSYS_NO_PATHCONV` escribe en `C:\d\` en silencio (memoria `feedback_s190_gh_ruta_msys.md`).
- **Reincidencia S91 (números a mano):** S190 escribió «10» en la §12.10 y el script daba 12; corregido. Todo número va con su script citado.
- **Reincidencia rutas Windows:** `\r` de `\ronda2` se volvió retorno de carro dos veces al escribir la bitácora con Python. Construir las rutas con `chr(92)` o leerlas de un archivo.
- **API de Actions:** `jobs?per_page=100` da «Server Error» en runs de 166 jobs; con 30 por página responde. `run_attempt` es del run, no del job: los relanzados se cuentan por el nombre del artifact (`intento-N`).
- **Merges con ficha en serie:** `D:\vrp-trabajo\temporales\s190\lote7\prep.py` y `uno.sh` (une main, numera la ficha desde la fila de la descripción del PR, corre las 201 pruebas que leen la ficha y `CLAUDE.md`, empuja, espera la CI y mergea con `--match-head-commit`). Un conflicto entre filas vecinas de la ficha se resuelve tomando de cada fila el lado que se apartó de la base común.
- **El PC suspendido retrasa la cadena:** la tanda 4 terminó a las 19:45 del 11-18 y la cadena lo vio a las 11:10 del 11-19 (SOSPECHA: suspensión nocturna).
- **Proyecto:** el espejo `azure.archive.ubuntu.com` cayó el 2026-11-19 a las 12:08 UTC; tumbó 7 de 11 trabajos del NRT y 26 trozos de la tanda 5 en «Install deps». Es pasajero: `gh run rerun --failed`.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** el almacén no limpia duplicados ya escritos (`store.append_record` arma el índice con la última copia); el arreglo de #1051 evita que se creen, no limpia.
- **CONFIRMADO:** el bucle de push de `nrt.yml` usa `git pull --rebase -X theirs`; en un rebase «theirs» es el commit propio, al revés de su comentario. Sin efecto con el checkout al día; sin arreglar.
- **CONFIRMADO:** F4-101 (19 records con `L_bk` 0 y VRP > 0) y Tupungatito V750 con la vía (8 de 14 alertas de MIROVA publicadas, K 2; 6 perdidas débiles 0,11 a 0,25 MW). Scripts en `D:\vrp-trabajo\temporales\s190\f4_101_contar.py` y `tupungatito_v750.py`.
- **SOSPECHA:** el 401 de Chillán en la reparación de W5 del A/B del día es parte de la caída de NASA, no un token vencido (el NRT siguió verde; token vence 2027-01-14 según el healthcheck). El pipeline trata 401 como fatal.
- **SOSPECHA:** `sombra-34.yml` y `sombra-codigo-mirova.yml` no fijan `ref` en el checkout; no están en `push-main`, sin medir si se encolan.
- **SOSPECHA:** las 6 noches débiles de Tupungatito V750 que la vía no publica se explican por la caja `sens` de D36 o el umbral cerca del fondo.
- **SIN DATO:** si el marcador del cráter quedó completo y verde: el subagente no había entregado al cierre.
- **SIN DATO:** estado de #1052 al cierre (el watchdog lo cerró a las 13:14; la sesión del día dijo después que lo dejaba abierto con diagnóstico).

## e. Ya cerrado, no rehacer

- Duplicados de Copahue del 2026-11-18 (06:18 y 06:24 VIIRS 750): causa probada (checkout con SHA congelado), limpiados en #1051; 0 duplicados en los 11 Tier A al 2026-11-19 12:45.
- #1047: las 134 noches faltantes del A/B del día eran Isluga por CMR, no un defecto; W4 cuadra con 2.223 noches por brazo.
- F8-V201 (semana de abril de los 34): no bloquea publicar la historia (el plan publica desde `data/historia_34` + `data/sombra_34`); comentario corregido en #1048.
- Regla de posición de la vía: «radiante», decidida 2026-11-15 (#1022).
- Techo de BT de VIIRS 750 en el almacén: 683 K (#1043, ficha v1.39).
- #1046 revisado en el navegador por S190 (JSON viejos cuentan como antes; JSON nuevos muestran «sin dato» y «fuera de radio»; index, diario y mosaico sin errores).
- Los tres hallazgos de gravedad 5 de Codex en MODIS y los dos de VIIRS bajaron a 3 o menos con verificador limpio; ninguno aparece en los 14.843 records MODIS ni en los 58.936 VIIRS de la vía.

## f. Prompt para S191

```
Retomas VRP Chile como sesión dueña del loop (S191). Trabajas en español de Chile, sin guiones largos, con rutas
absolutas. Una sola sesión dueña del loop: si otra sesión lo es, pregunta antes de tocar nada.

1. Verifica antes de creer:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" && git fetch origin --prune
   git status -sb   (debes estar en loop/activo; compara git rev-parse HEAD con git ls-remote origin -h refs/heads/loop/activo)
   ps -ef | grep -v grep | grep -E "cadena|pytest"   (al cierre de S190 vivían cadena_5a7_s190d.sh y cadena_ventanas.sh)
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i '^date'   (hora del servidor, A86)
   Compara el CLAUDE.md de loop/activo con el de main (memoria feedback_s190_claudemd_de_loop_activo).
2. Lee, en orden: tasks/BLOQUE_ARRANQUE_S191.md (este), la bitácora tasks/LOOP_OBJETIVOS.md §6 (entradas S190), la
   §12.10 de docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md y el MEMORY.md del proyecto.
3. Trabajo, en este orden:
   a. Marcador del cráter (worktree D:/vrp-trabajo/worktrees/s190-marcador-crater, sin commit): lee las salidas en
      D:\vrp-trabajo\temporales\s190\marcador\ (rojo_antes, verde_despues, mutaciones, nulo, suite_completa). Si la
      suite no terminó o falta algo, complétalo. Revisa el diff tú mismo: sólo claves nuevas en diag_codigo_mirova,
      ninguna detección ni potencia cambia. Pasa un verificador limpio (subagente, contexto limpio, scripts propios,
      con el plan D:\codex-vrp\_salida\ronda2\PLAN_F1M_G3_PARA_NICOLAS.md). Commit, push y PR con su fila de ficha en
      la descripción (se numera al mergear). No mergear sin «mergea #N».
   b. Tanda 5: cuando la cadena la deje limpia, bajar_trozos.sh <run> D:/vrp-trabajo/temporales/historia_34/tanda5/run1,
      touch .completa, BASE=.../tanda5 WT=D:/vrp-trabajo/worktrees/s191-tanda5 RAMA=s191-historia34-tanda5 bash
      D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh <run>; TANDAS.md con la fila «aplicada» de la tanda 4
      (run 44528546156, commit 4e6e873fa, tag pre-historia-34-tanda4) y la tabla de la tanda 5 (números con script, los
      relanzados por nombre de artifact); verificador limpio; PR; con «mergea #N», aplicar con aplicar-reemplazo.yml
      (tag pre-historia-34-tanda5). Igual para 6 y 7.
   c. Revisar que el sync de MIROVA regeneró data/mirova/*.json con pasadas_tabla y que el panel del #1046 aparece en
      el sitio.
   d. Auditoría Codex: la tarjeta «Auditoría Codex, ronda 2: frente 2 y siguientes» (task_c8159ee6) la abre Nicolás;
      no dupliques ese trabajo.
   e. Llevar a Nicolás las decisiones de la sección b de este bloque, con recomendación.
4. Reglas duras: A45 (tag y sí de Nicolás antes de pipeline/process_*.py, store.py, mirova_equivalent.yaml; el detector
   pipeline/mirova_v750_codigo.py se trata igual), todo PR con «mergea #N» explícito, merge commit con
   --match-head-commit, ficha numerada al mergear, nada de git stash, git add por archivo, nada de
   experiments/_s176_codex/, temporales y worktrees en D:, números siempre con script, rutas Windows sin sed.
5. Si la sesión no alcanza: deja la bitácora al día en cada paso y cierra con /cierre al 50 % del contexto.
```
