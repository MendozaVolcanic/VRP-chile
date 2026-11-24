# Bloque de arranque S199 (escrito por S198, 2026-11-24 ~15:10 UTC; ACTUALIZADO ~18:05 UTC)

> **ACTUALIZACIÓN S198 CONTINUADA (Nicolás: «continuemos aca mismo», 15:20 UTC). Manda sobre lo de abajo donde lo
> contradice.**
> - **Umbral de contexto:** el hook `C:\Users\nmend\.claude\hooks\aviso_contexto.py` tiene piso por proyecto
>   (`UMBRAL_MIN_POR_PROYECTO`, VRP Chile 550 mil), probado con 3 casos sintéticos; `C:\Users\nmend\.claude\CLAUDE.md`
>   actualizado.
> - **#1015 MERGED** 2026-11-24 17:42 UTC (ficha **v1.94**; tag `pre-s198-miniaturas`): panel «Últimas 10 pasadas».
>   PENDIENTE: ver `data/miniaturas/` en main y el panel en Pages tras el primer NRT posterior; `nrt-retry` no genera
>   miniaturas (el panel de un volcán reintentado se actualiza 2 h después).
> - **#1114 en Actions:** el NRT de 14:33 UTC subió los 11 artefactos `cobertura-<volcán>` (15 a 32 búsquedas fallidas
>   por volcán, CMR degradado). PENDIENTE: la primera decisión de `nrt-retry` (cron `30 1-23/2`, GitHub lo corre tarde).
> - **Cierre II de Codex HECHO** (17:08 a 17:29 UTC, 9,1 M tokens; el primer intento falló por red de Codex,
>   «workspace routing discovery failed», archivos en `corridas\c2_intento1`) y **verificado** (C2-101 EN PARTE g3, C2-102
>   y C2-104 g2, C2-103 g1, nuevo C2-V201 g2 fundido con R3F3-104). Registro: 331 filas. Resumen y **borrador de acta**:
>   `D:\codex-vrp\_salida\ronda3\RESUMEN_CIERRE2_PARA_NICOLAS.md`. **ACTA APROBADA por Nicolás (2026-11-24 ~18:20 UTC, «Sí, apruebo el
>   acta»)**: la auditoría Codex queda CERRADA con límites explícitos. S199: llevar el acta al repo (doc en `docs/` con la
>   tabla del acta y el par commit/corpus del cierre: main tras #1116 y el corpus de 517 filas) por PR con uno.sh, y hacer
>   los PR que el acta asigna (F6-112 fila «no medida»; marca «sin ángulo» con A45; declarar R3F3-104/C2-V201 y F1V-115
>   en la ficha y D36).
> - **#1116 (F7-V501)** abierto y encadenado a merge (`D:\vrp-trabajo\temporales\s198\merge_1116.sh`, ficha v1.95).
> - **Disco:** zip `D:\vrp-trabajo\archivo_s198_temporales.zip` (182 MB, 23.450 archivos de 96 carpetas, testzip OK) y
>   borrado (2,18 GB; 7 carpetas quedaron a medias, ver `D:\vrp-trabajo\temporales\s198\zip_y_borrar.log`). Total
>   liberado en temporales: 6,15 GB. Decisión 2 de §b: HECHA.
> - **F7-V501 en curso:** agente en `D:\vrp-trabajo\worktrees\s198-v501` (rama `s198-f7-v501`); al abrir PR, mergear
>   con uno.sh (v1.95) y quitar el worktree.
> - R3F3-V101 (aviso de alertados sin fondo en el tablero) sigue pendiente: va después de #1015 (mismo frontend).

> El bloque anterior (S198, escrito por S197) queda como histórico en `tasks/BLOQUE_ARRANQUE_S198.md`. Detalle de S198
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S198, arriba) y en la nota viva
> `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_6ced7c79-4228-43d8-9f26-bdab362c3082\s198_nota_viva.md`.
> **Estado fijado CON TRABAJO EN VUELO:** (1) la cadena del barrido del piso
> `D:\vrp-trabajo\temporales\s198\barrido\cadena_piso_s198b.sh` (tarea de fondo de S198) espera 3.600 s antes del
> quinto intento de la tanda 3 (run 45308651250, abril); (2) `esperar_r3.sh c2` espera memoria bajo 85 % para lanzar
> el Cierre II de Codex (relanzado ~13:05 UTC con 240 min; a las 15:07 la memoria estaba en 93 %). Las dos mueren si se
> cierra la app o la sesión S198: comprobar con `ps -ef | grep -E "cadena_piso|esperar_r3"` y relanzarlas (§f).
> S198 cerró por el umbral de contexto del hook (418 mil).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.93** (merges #1111 a #1115 hoy) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| Guardia K de MODIS | **plazo cumplido**, VERDE, 30 de 29, 0 candidatas; la vía publica 29 de 30 y K 21; razón vía/MIROVA mediana 1,043. **Decisión de Nicolás: sigue informativa hasta el 2027-03-02** | #1111 (v1.89) y #1113 (v1.90); `experiments/_s171_modd_adopcion/s198_cierre/INFORME_CIERRE_GUARDIA_MODIS.md` |
| R3F9-V101 (8 protegidas V375 sólo OCR sin alertado en el cráter) | **aceptadas** como distancia del OCR (Nicolás) | #1113, `docs/MIROVA_DIVERGENCES.md` D8' marca S198 |
| R3F5-101 y R3F5-V101 (tablero) | **en main**: «cráter no medido» en evolución, minigráfico y diario; fondo 0 K «sin fondo»; 10 de 38 mal dibujadas pasan a 0 | #1112 (v1.91), `experiments/_s198_r3f5_evolucion/` |
| F6-104 y F6-114 (NRT verde sin medir; pérdida a los 8 días) | **en main**: `nrt-retry` reintenta corridas verdes con fallas de cobertura (máx. 4 en 24 h, nunca un reintento); `barrido-huecos.yml` los domingos 20:43 UTC, días 9 a 30, sólo pasadas sin record | #1114 (v1.92). **SIN VERIFICAR en Actions** (ver d) |
| F7-318 / R3F9-107 (variantes D-9) | **en main**, script aparte (banco sellado intacto): protegidas iguales en las 5 lecturas (494 de 518); negativos limpios 74/4235 (SN) contra 18/4076 | #1115 (v1.93), `scripts/banco_paridad_variantes_d9.py` |
| Codex ronda 3 | frentes 9, 3 y 5 **cerrados y verificados** (326 filas en `D:\codex-vrp\_salida\ronda3\hallazgos_verificados.csv`); **falta el Cierre II** (copia refrescada a `4eeda1b37`, ficha v1.91) | `D:\codex-vrp\_salida\ronda3\ESTADO_COORDINACION.md` (traspaso 07:40) y `RESUMEN_F{9,3,5}_R3_PARA_NICOLAS.md` |
| Barrido del piso, tanda 3 (abril) | **4 intentos en rojo** por el CMR de NASA («An Internal Error has occurred», intermitente desde ~07:15 UTC); en el 3.º se recuperaron 4 de 8 trozos; quinto intento tras 3.600 s | run 45308651250; `D:\vrp-trabajo\temporales\s198\barrido\cadena.log` |
| Barrido del piso, mayo a nov | sin despachar (la cadena los despacha uno tras otro al quedar verde la tanda anterior) | `cadena_piso_s198b.sh` (TANDAS t4 a t10) |
| Disco | C: 13 GB, D: 15 GB. Se borró sólo lo regenerable de 96 carpetas temporales (3,97 GB: copias del repo, pytest, gránulos NASA) | `D:\vrp-trabajo\temporales\s198\borrado_regenerable.log`, `inventario_temporales.csv`, `clasificacion_candidatas.csv` |
| Issues | #1110 y #1099 **cerrados solos**; #1106 sigue abierto (lo cierra la auditoría del 2026-11-30) | `gh issue list` |
| PR abiertos | #1015 (miniaturas, A45, CONFLICTING), #913 (plan S163) | `gh pr list` |
| Radios del visor | **vacío** (24-nov ~05:15 UTC) | ArtifactData, Artifact YaZuZ3pWuxfAZQG2UJY7PL, colección `radios` |
| Sin commitear en `loop/activo` (no son de S198) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | #1015, panel «Últimas 10 pasadas» con miniatura NTI (toca `mirova_v750_codigo.py` y `nrt.yml`, A45) | A45 explícito y rebasar / esperar | **DECIDIDO: Nicolás dio A45 explícito el 2026-11-24 ~15:15 UTC («Sí, A45 para #1015»), después del cierre de S198.** S199: tag defensivo `pre-s199-miniaturas` y push, rebasar sobre main, resolver conflictos, pruebas, verificar en navegador y mergear con uno.sh |
| 2 | Las 96 carpetas temporales con contenido «único» (unos 3 GB, 2.928 .py/.md/.sh fuera del repo) | zip de lo textual y borrar / dejar | **Zip de .py .md .sh .txt .csv a `D:\vrp-trabajo\archivo_s199_temporales.zip`, luego borrar** |
| 3 | `C:\Users\nmend\AppData\Local\Temp-1` a `Temp-228` (1,8 GB, del 2026-04-19, no son de VRP) | borrar / dejar | Preguntar a Nicolás de qué programa son; si no lo sabe, borrar |
| 4 | R3F3-104: 23 pasadas históricas sin marca «no medido» que el tablero ve «sin anomalía» | reprocesar (A45) / declarar | **Declarar** en la ficha y D36 (no son protegidas); reprocesar sólo si Nicolás lo pide |
| 5 | R3F3-V101: aviso de `alertados_sin_fondo` en el tablero | PR de tablero / dejar | PR de tablero (fuera de A45) |
| 6 | F7-V501: las variantes D-9 faltan en `auto_audit_weekly`, `comparacion_via_k` y `clasificacion_referencia` | extender / dejar | Extender con el mismo patrón de #1115 (script que importa, sin tocar lo sellado) |
| 7 | Heredadas: radios del visor (P0), resto del §14 de #1103, independencia C1, fondo nulo, R-W7, marcador, LdM, PAT de `settings.json` | | las del bloque S198 §b |

**Preguntas de Nicolás de S198 sin respuesta explícita:** ninguna. «¿Algo más que mejorar del dashboard?» se respondió
(1: #1015; 2: fila «no medida» por pasada fallida, F6-112; 3: plan S176 del visualizador). «¿A qué te refieres sin
cita?» se respondió: carpeta que ningún documento del repo (main ni loop/activo), la memoria, las notas ni la auditoría
Codex nombra como evidencia.

## c. Lo aprendido

- **REGLA GENERAL:** «sin cita en el repo» no basta para borrar temporales: la bitácora vive en `loop/activo` (57
  carpetas, 1,9 GB, citadas sólo ahí) y la memoria, las notas entre sesiones y la auditoría Codex citan otras 12. Cruzar
  las cuatro fuentes y clasificar por contenido (copia del repo, NASA, pytest, único) antes de borrar; borrar primero
  sólo lo regenerable. Scripts: `D:\vrp-trabajo\temporales\s198\{inventario_temporales,candidatas,clasificar_candidatas,borrar_regenerable}.py`.
- **REGLA GENERAL:** una caída intermitente de un servicio externo (CMR de NASA) se come los relanzamientos inmediatos:
  la cadena debe esperar cada vez más (30 min, 1 h, 1,5 h...) antes de relanzar. Y el subshell de `$(esperar ...)`
  sobrevive al `kill` del padre: matar también los hijos (`ps -ef`, `$3==pid`).
- **REGLA GENERAL:** la memoria comprometida de Windows sube a 87 a 93 % con Chrome y varias sesiones Claude abiertas; el
  lanzador de Codex (techo 85 %) no arranca. Pedir a Nicolás cerrar Chrome o lanzar en horas sin uso.
- **Proyecto:** el NRT de 10:10 UTC del 2026-11-24 (run 45372241023) tuvo 344 líneas de «Internal Error» del CMR y quedó
  VERDE: caso vivo de F6-104, base de #1114.
- **Proyecto:** desde S193 producción procesa MODIS de día; la guardia K sólo noche, así que una protegida diurna (Chillán
  2026-11-22 20:40 UTC) no cuenta para el plazo de la guardia: es lo esperado.
- **Proyecto:** `uno.sh` en serie funcionó con un script que espera el MERGED del PR anterior antes de numerar la ficha
  (`D:\vrp-trabajo\temporales\s198\merge_1115.sh`).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** CMR de NASA con errores intermitentes desde ~07:15 UTC del 2026-11-24 para los runners (desde el PC
  responde 200). Tanda 3 roja en 4 intentos.
- **CONFIRMADO:** Cierre II sin lanzar por memoria (93 % a las 15:07 UTC).
- **SOSPECHA:** #1114 en Actions: que `gh run download --pattern` baje los resúmenes `cobertura-<volcán>`, que una corrida
  despachada por el GITHUB_TOKEN tenga actor `github-actions[bot]` y la duración real del barrido (tope 60 min). El
  primer `nrt-retry` tras el merge (14:03 UTC, success) no se revisó por dentro.
- **SOSPECHA:** el quinto intento de la tanda 3 volverá a fallar si el CMR sigue degradado; la cadena se detiene tras 5
  relanzamientos (`cadena.parada`).
- **SIN DATO:** qué trozos fallaron en el intento 4 (la API de GitHub dio 502 al consultarlo).

## e. Ya cerrado, no rehacer

- Guardia MODIS: plazo cumplido y decidido (sigue informativa hasta el 2027-03-02). No reabrir.
- R3F9-V101: aceptadas (D8' marca S198). R3F5-101/V101, F6-104/114, F7-318: en main (#1112, #1114, #1115).
- Rojos de la tanda 3: NO es el token ni el código; es el CMR (log de Villarrica 5 intento 2 y artefacto Chaitén 1).
- Disco: las 4 fuentes de cita ya cruzadas; lo regenerable ya borrado.
- Lo de §e del bloque S198 sigue valiendo.

## f. Prompt para S199

```
Retomas VRP Chile como sesión dueña del loop (S199). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S198 cerró y no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; ficha de main (esperado v1.93); gh pr list (esperado #1015 y #913); gh issue list.
   - Trabajo en vuelo de S198: ps -ef | grep -E "cadena_piso|esperar_r3". Si murieron:
     a) tanda 3: gh run view 45308651250 (attempt y rojos con la API de jobs por intento); relanza la cadena con
        bash D:/vrp-trabajo/temporales/s198/barrido/cadena_piso_s198b.sh 45308651250 t3 (en segundo plano; cerrojo
        cadena.lock; si existe cadena.parada, léela). Antes prueba el CMR mirando el log del último NRT (grep -c
        "Internal Error").
     b) Cierre II: bash /d/vrp-trabajo/temporales/s197_r3/esperar_r3.sh c2 vrp_r3 /d/vrp-trabajo/temporales/s197_r3/cierre2.txt 240 85 3
        en segundo plano (pide memoria bajo 85 %: pedir a Nicolás cerrar Chrome). La copia ya está en 4eeda1b37; si main
        cambió el tablero o los scripts, refrescar con refrescar_copia.py y actualizar BASE.txt, AGENTS.md y _comun.txt.
   - #1114 en Actions: el último nrt.yml debe subir artefactos cobertura-<volcán>; el nrt-retry siguiente debe decidir
     bien (verde con fallas: reintenta; despachado por el bot: no). barrido-huecos.yml corre el domingo 20:43 UTC.
   - df de C: y D:.
2. Lee tasks/BLOQUE_ARRANQUE_S199.md (rama loop/activo), la entrada S198 de tasks/LOOP_OBJETIVOS.md §6 y la nota
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_6ced7c79-4228-43d8-9f26-bdab362c3082\s198_nota_viva.md
3. Trabajo, en orden:
   a. Cierre II de Codex: cuando termine, verificador Claude limpio (hacer_verificador.py, frente C2, carpeta
      cierre2_verificacion, prefijo C2-V), consolidar_r3.py C2-r3 cierre2 cierre2_verificacion C2-V y
      RESUMEN_CIERRE2_PARA_NICOLAS.md; arreglos g3+ verificados como PR (A45 donde toque).
   b. Barrido del piso: que la cadena cierre abril y siga con mayo a noviembre; con todo verde, evaluar.py calibrar
      según experiments/_s196_lab_piso/PREREGISTRO.md.
   c. Decisiones de §b: #1015 YA TIENE A45 de Nicolás (rebasar sobre main, tag defensivo, uno.sh); zip y
      borrado de las 96 carpetas «únicas» si Nicolás dice que sí; Temp-N.
   d. F7-V501 y R3F3-V101 como PR fuera de A45; radios del visor si Nicolás los fijó.
4. Reglas duras: A45; merges con D:/vrp-trabajo/temporales/s195/merge/uno.sh (fetch con reintento, ficha al mergear
   con la versión siguiente a la de main y la fecha UTC del merge, --match-head-commit); en serie, esperar el MERGED del
   anterior; nada de git stash; git add por archivo; nunca experiments/_s176_codex/; temporales y worktrees en D:;
   números sólo de scripts; .md con newline=""; un vigilante por corrida; nunca pedir ni recibir tokens por el chat.
5. Cierra con /cierre al llegar al umbral de contexto del hook y deja el prompt de S200.
```
