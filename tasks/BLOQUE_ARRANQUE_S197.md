# Bloque de arranque S197 (escrito por S196, 2026-11-23 ~22:45 UTC)

> El bloque anterior (S196, escrito por S195) queda como histórico en `tasks/BLOQUE_ARRANQUE_S196.md`. Detalle de S196
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S196, arriba) y en la nota viva de la sesión
> `C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_82fe0d09-30f3-4ac4-a70b-9a334fa376fe\s196_apertura.md`
> (decisiones textuales de Nicolás, números y rutas de cada salida).
> **Estado fijado CON TRABAJO EN VUELO:** corre la tanda 2b del barrido del piso (run 45280588605, Isluga, Tupungatito
> y Cordón Caulle, marzo) y un vigilante en segundo plano de la auditoría semanal (inofensivo: sólo consulta). Ningún
> merge ni subagente vivo. S196 cerró por el umbral de contexto del hook (406 mil tokens).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.85** | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| NHI-v1: Chillán estaba a 61 km, sobre Antuco | **corregido** (NHI-v1 #1, merge `55461a4`); serie regenerada desde 2026-01-27 en `4d24515` (109 escenas, 25 alertas; la vieja, 117 y 16, en `archivo/` de NHI-v1) | `gh pr view 1 -R MendozaVolcanic/NHI-v1` |
| #1098 re-sello de #1097 y del paso 2 con la caja nueva | MERGED, v1.79; desarrollo de #1097 igual byte a byte; paso 2: Chillán 16 a 23 alertas NHI | `experiments/_s195_viirs_dia_control/PREREGISTRO.md` cabecera |
| Paper R2 | `ffa6813` en main de vrp-chile-paper: recall MODIS 0,918 a 0,965, V750 0,94 a 0,957, V375 0,964 a 0,977 | `paper_vrp_chile\revisiones\REVISION_S196.md` |
| #1100 independencia paso 2 (latencia E2a, día MODIS en la comparación E3, CAMINO a main) | MERGED, v1.80 | `experiments/_s196_latencia/`, `experiments/_s196_e3/` |
| Barrido del factor s (S195) | **PAUSADO**: tanda 1 idéntica al control (947/947) pero plana: s 5 a 1 agrega 5 publicaciones en marzo en 3 volcanes | `D:\vrp-trabajo\temporales\s196\barrido\salida_contar_t1.txt` |
| #1101 pre-registro del piso (s_A = 3, 7 pisos 0,003 a 0,0015) | MERGED, v1.81; evaluador sha256 `16d0360e...` | `experiments/_s196_lab_piso/PREREGISTRO.md` |
| #1102 código del piso (A45, tag `pre-s196-laboratorio-piso` en `f8e82fe9a`) | MERGED, v1.82; identidad 0 distintos en producción, los 34, laboratorio; mutaciones 17/17 | `experiments/_s196_lab_piso/salida_identidad.txt` |
| Barrido del piso, tanda 1 (run 45189263109; Láscar, Chillán, Villarrica, PCC; marzo) | **VÁLIDA y se separa**: control 1.297/1.297 idéntico; donde no actúa 350/350; nuevas p300 4 a p150 62, sin pérdidas | `salida_contar_piso_t1.txt` |
| Tanda 2 (run 45220812538; los otros 7 + PCC) | **INVÁLIDA** por 14 trabajos caídos con HTTP 401 de NASA entre 17:23 y 17:55 UTC (transitorio: antes y después bajó con el mismo token; NRT sin 401). 2.046 pareados, 0 distintos, 12 sólo en el control (trozo muerto) | `salida_contar_piso_t2.txt`; logs `D:\vrp-trabajo\temporales\s196\diag_t2\logs\` |
| Tanda 2b (run 45280588605; Isluga, Tupungatito, PCC; marzo) | **CORRIENDO** al cerrar | `gh run view 45280588605` |
| #1103 plan de mejoras del experimental (P0 primero: que una anomalía conocida no esconda un foco nuevo) | MERGED, v1.83; §12 del plan por sensor ya en main | `docs/PLAN_EXPERIMENTAL_MEJORAS_S196.md` |
| #1104 retiro de la sombra C0 y MEJ-7 cerrada como paridad | MERGED, v1.84 | `data/experimental_v2/README.md` |
| #1105 visor de radios del edificio | MERGED, v1.85. Artifact https://claude.ai/artifact/YaZuZ3pWuxfAZQG2UJY7PL (base `radios`, se lee con ArtifactData); copia local `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\visor_radios_edificio\visor_radios.html` | guardado desde la página publicada SIN PROBAR |
| Auditoría semanal del 23-nov (primera con día MODIS) | **FUERA DE BANDA**, issue #1106: recall MODIS 94,6 % < 95 % (n = 37); protegida sin publicar Chaitén MODIS 2026-11-19 02:30 UTC, MIROVA 1,07 MW | `gh issue view 1106`; `data/audit_continuous/latest.json` |
| Issue #1099 sombra de los 34 | corrida del 22-nov falló sólo en Callaqui (31 verdes): 8 búsquedas o descargas fallidas del 22-nov | run 45065535656 |
| Día MODIS (desde 15-nov, 11 Tier A) | 166 diurnas, 1 con VRP > 0 (Chillán 22-nov 20:40, 6,654 MW; MIROVA 6,07) | `D:\vrp-trabajo\temporales\s196\dia_modis\salida_contar.txt` |
| Sesiones | archivadas S194, Paper, VIIRS día, Independencia; Mazos restaurada (se archivó en cascada). Las 6 de S196 (prereg-piso, paper-r2, indep-paso2, plan-experimental, visor-radios, retiro-c0) archivadas con el sí de Nicolás (2026-11-23 ~23:00 UTC) y sus 5 worktrees quitados a mano (archivar no los quitó) | `list_sessions linked` |
| PR abiertos | #1015 (miniaturas), #913 (plan S163) | `gh pr list` |
| Disco | C: 19 GB tras quitar los 5 worktrees de S196, D: 14 GB | `df` |
| Sin commitear en `loop/activo` (no son de S196) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Radios del edificio por volcán (D-H) | fijarlos en el visor | **Fijarlos en el visor** (Artifact, botón Guardar); el loop los lee y los pasa a `config/areas_laboratorio.yaml`. P0 entero depende de esto |
| 2 | (resuelta: archivadas el 2026-11-23) | | |
| 3 | Resto del §14 de #1103: D-A Laguna del Maule, D-C vara de Lastarria, D-D zona A de Cordón Caulle, D-F archivar MEJ-2/3 con disparador, D-G diseñar MEJ-6 ya | ver §14 | las del plan: A/B aislado de LdM antes de decidir; tabla OVDAS de Lastarria con TIR de Landsat en paralelo; radio de PCC que elijas; (a) en D-F y D-G |
| 4 | Independencia C1: quién del OVDAS fija el requisito de adopción y cuándo | | conversarlo con la jefatura; es lo único que destraba E1 |
| 5 | Mazos P2 a P8 y Q1 a Q5 | ver `...\congreso geologico 2026\2_PRESENTACIONES\ACTUALIZACION_S194.md` §4 y `ACTUALIZACION_S196.md` | |
| 6 | Heredadas: Laguna del Maule, episodios OVDAS (D4), rotar el PAT de `settings.json` | | |

**Preguntas de Nicolás de S196 sin respuesta explícita:** ninguna. Sus dos preguntas («qué tiene que hacer el NHI en
este proyecto» y «cómo vamos con el plan por sensor») se respondieron en texto en la sesión.

## c. Lo aprendido

- **REGLA GENERAL:** `gh run watch` consulta cada 3 s; dos vigilantes de la misma corrida agotaron la cuota de 5000/h
  de la API (05:21 a 05:36 UTC). Un vigilante por corrida, `--interval 60`, con run_in_background; para esperas
  largas, un bucle que consulta `gh run view --json status` cada 3 min y tolera cortes de red (memoria
  `feedback_s196_gh_watch_cuota.md`).
- **REGLA GENERAL:** archivar una sesión madre archiva también sus hijas inactivas sin PR; restaurar enseguida las que
  deben seguir vivas (memoria `feedback_s196_archivar_arrastra_hijas.md`).
- **REGLA GENERAL:** `git checkout origin/main --` sin ruta deja el checkout en HEAD separado (me pasó y lo corregí).
  Para traer un archivo de otra rama, siempre con ruta.
- **Proyecto:** un HTTP 401 de NASA en un barrido no prueba un token vencido: mirar si el mismo token bajó antes y
  después en la misma corrida y si el NRT tuvo 401. En S196 fue una ventana de 32 min.
- **Proyecto:** el checkout canónico está en `loop/activo`, que no contiene a main: un archivo recién mergeado a main no
  existe en esa ruta local. Para entregar un HTML de main a Nicolás, copiarlo con `git archive origin/main <carpeta>`
  a una carpeta fuera del repo.
- **Proyecto:** con el piso en 0,003 el factor s no mueve casi nada en el cráter (el piso manda); bajar el piso sí
  separa los brazos (tanda 1: 4 a 62 publicaciones nuevas en marzo, 3 volcanes).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** auditoría semanal fuera de banda (#1106): Chaitén MODIS 2026-11-19 02:30 UTC, MIROVA 1,07 MW, sin
  publicar y ninguna otra pasada de esa noche publicada; recall MODIS 94,6 % (n = 37). Sin diagnosticar.
- **CONFIRMADO:** tanda 2 del piso inválida sólo por cobertura (401 transitorio); detección 0 distintos en 2.046.
- **SOSPECHA:** las fallas de descarga de Callaqui (22-nov y días 18 a 21) son la misma ventana de 401 o algo propio de
  Callaqui; revisar la corrida programada del 23-nov.
- **SOSPECHA:** enmascaramiento en la detección (la anomalía grande y su halo suben mu y sd); `m0` muestra la firma pero
  no la separa de nubosidad y ángulo (P0 parte 3 del plan).
- **SIN VERIFICAR:** guardado del visor desde la página publicada.

## e. Ya cerrado, no rehacer

- NHI-v1 Chillán corregido y ambos pre-registros re-sellados (#1098); no volver a re-sellar por esto.
- Barrido del factor s: pausado por plano (5 publicaciones nuevas de s 5 a 1, 947 records); la palanca es el piso.
- MEJ-7 cerrada como paridad (producción la publica: 6 de 5.758 RUTINA, 4 de Láscar).
- Sombra C0 retirada (#1104); su vigilancia ya daba SIN_OBJETO.
- Control diurno VIIRS: una sola mirada, no antes del 2027-03-07 (Nicolás: «Sí, una sola mirada (Recomendado)»).
- Día MODIS: sin falsas alarmas diurnas en 166 pasadas.
- Paper R2 arreglado en el script del paper (`ffa6813`). Ojo: `scripts/paper_numbers.py` de VRP-chile sigue con el
  criterio viejo (no es el que usa el manuscrito).

## f. Prompt para S197

```
Retomas VRP Chile como sesión dueña del loop (S197). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S196 cerró y no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; ficha de main (esperado v1.85); gh pr list (esperado #1015 y #913).
   - gh run view 45280588605 (tanda 2b del piso): si quedó verde, corre
     D:\vrp-trabajo\temporales\s196\barrido\contar_brazos_piso.py 45280588605 y mira COMPARAR (control y «donde no actúa»).
   - gh issue view 1106 y 1099; df de C: (19 GB al cerrar) y D:.
2. Lee tasks/BLOQUE_ARRANQUE_S197.md (rama loop/activo), la entrada S196 de tasks/LOOP_OBJETIVOS.md §6 y la nota
   C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_82fe0d09-30f3-4ac4-a70b-9a334fa376fe\s196_apertura.md
3. Trabajo, en orden:
   a. #1106: diagnosticar Chaitén MODIS 2026-11-19 02:30 (protegida de 1,07 MW sin publicar) con
      superpowers-systematic-debugging; A8 (data fresca) y A54 (categoría física) antes de proponer nada.
   b. Barrido del piso: con 2b válida, seguir por tandas (abril en adelante, 10 volcanes + PCC para el control),
      revisando COMPARAR en cada una; con todo marzo a hoy, evaluar.py calibrar según el PREREGISTRO.
   c. #1099 Callaqui: ver si la corrida del 23-nov quedó verde.
   d. Codex ronda 3 (cuota desde 2026-11-24 04:20 UTC).
   e. Leer los radios que Nicolás guarde en el visor (ArtifactData, colección radios) y pasarlos a
      config/areas_laboratorio.yaml en un PR; luego P0 partes 1 y 2 del plan de mejoras.
4. Reglas duras: A45 (tag y sí de Nicolás para EMPEZAR cambios en pipeline/process_*.py, store.py,
   mirova_equivalent.yaml, mirova_v750_codigo.py); los merges que recomiendas los haces tú (CLEAN, CI verde, ficha al
   mergear con D:/vrp-trabajo/temporales/s195/merge/uno.sh, en cadena si hay varios, --match-head-commit) e informas;
   nada de git stash; git add por archivo; nunca experiments/_s176_codex/; temporales y worktrees en D:; números sólo de
   scripts; .md con newline=""; un vigilante por corrida con --interval 60.
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
