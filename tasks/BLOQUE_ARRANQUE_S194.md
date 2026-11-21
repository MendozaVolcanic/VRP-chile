# Bloque de arranque S194 (escrito por S193, 2026-11-21 ~22:30 UTC)

> El bloque anterior (S193, escrito por S192) queda como histórico en `tasks/BLOQUE_ARRANQUE_S193.md`. El detalle
> de S193 está en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S193, arriba).
> **El estado se fijó con trabajo en curso** (filas «corriendo» de la tabla a): comprobarlo contra el remoto y `ps`.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha SDA **v1.66**, merge de #1085 (`3dd3aaaa9`, 22:25 UTC) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| PR mergeados en S193 (12) | #1073 (v1.57, cadena de S192), #1075 (v1.58), #1080 (tanda 7, sin ficha, aplicada), #1081 (v1.59), #1076 (v1.60), #1077 (v1.61), #1078 (v1.62), #1069 (v1.63, aplicado), #1079 (v1.64), #1082 (v1.65), #1083 (experimento, sin ficha), #1085 (v1.66) | logs `D:\vrp-trabajo\temporales\s192\merge\merge_<N>.log` y `D:\vrp-trabajo\temporales\s193\merge\` |
| Historia de los 34 | **completa**: tanda 7 (Hudson, MacaCay, Melimoyu, Mentolat) aplicada (run 44938602533, tag `pre-historia-34-tanda7`); los 32 activos desde 2025-02-15 | `experiments/_historia_34/TANDAS.md` §Tanda 7 |
| Fondo nulo | **cerrado**: los 15 MODIS viejos sin fondo pasaron a escena no medida (aplicador 44946628014); recuento en main: 0 MODIS con `L_bk == 0` y VRP > 0; 25 VIIRS conservan su VRP (decisión S192) | `D:\vrp-trabajo\temporales\s192\plan\fondo_nulo_lista.py`; sitio republicado y comprobado (Lastarria 2025-10-26 02:45 en 0 MW) |
| Codex ronda 2 | frentes 9 a 12 llevados a Nicolás y resueltos: docs (#1076), vigilancias (#1081), F9-106 docstring y criterio nocturno (#1082), «radiante» medida (#1083) y mantenida (#1085) | `D:\codex-vrp\_salida\ronda2\RESUMEN_F9_*`, `RESUMEN_F11_*`, `RESUMEN_F10_F12_*` |
| **Codex Cierre I** | **corriendo**: lanzador `esperar_estable_y_lanzar.sh cierre1` (PID 17531 al cerrar) espera memoria bajo 85 % (estaba en 88 a 90 %); acotado a ~10 M tokens porque la semana de Codex va en 90 % (se reinicia 2026-11-24 04:20 UTC). Lo preparó la sesión «Vigilancias» por Remote Control con Nicolás | `D:\vrp-trabajo\temporales\s190_codex_r2\encargos\cierre1.txt` |
| **A/B diurno** (#813, sesión local_1a9c0903) | veredicto con R-W7 lectura 2 y desviación D1 declarada: **DECIDE NICOLÁS CON M4**; Nicolás aceptó D2 (encender el día sólo en MODIS). **PR #1084** (resultado del A/B, CI verde, sin tocar producción) abierto, **mergear primero**. PR (a) frontend diurno en curso (rama `s193-frontend-dia`, subagente). PR (b) perfil (A45, tag `pre-s193-dia-modis`, prueba roja `878e83b0c`, rama `s193-perfil-dia-modis`) **sin terminar**: faltan 6 pasos | nota `...\side-session-notes\local_63e4043e-...\s193_diurno_veredicto.md` |
| **Laboratorio paso 1** (sesión local_90bc2df5) | **corriendo**: perfil `laboratorio` sobre la vía, zona A apagada, sin cron; tag `pre-s193-laboratorio-paso1`; 12 de 12 mutaciones; espera la suite para abrir PR | nota `s193_laboratorio_paso1.md` (cuando aparezca) |
| Tablero F5 restante (sesión local_b062c447) | **espera a Nicolás** (pregunta o permiso pendiente en esa sesión); tendrá que rebasar sobre #1079 | sesión «Tablero: resto del frente 5 de Codex» |
| Chaitén MODIS 2026-11-19 02:30 | juzgada «alerta marginal de MIROVA no reproducible» (#1085) | `D:\vrp-trabajo\temporales\s193\chaiten\INFORME.md` |
| Sesiones archivadas | 10 (las de S192 y lagos, A45, documentos, reemplazo); «Vigilancias» (local_f8b8ba7b) sigue viva por Remote Control **con su carpeta vaciada** | ver c |
| Disco | C: 14 GB libres (worktrees de las sesiones nuevas en C:), D: 35 GB | `df` |
| Sin commitear en `loop/activo` (no son de S193) | `experiments/_s140/`, `experiments/_s160_espacial/_censo_s159/`, `experiments/_s160_espacial/data/`, `experiments/_s176_codex/*` (nunca se commitea) | `git status --porcelain` |
| PR abiertos | #1084 (diurno, mergear), #1015 (miniaturas S184), #913 (plan S163) | `gh pr list` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Laguna del Maule: el punto del `volcanoes.yaml` cae dentro del lago (35 de 123 pasadas sobre agua) | mover el punto al centro eruptivo (no A45) / celdas NaN en la caja (A45) | Mover el punto; la coordenada la elige Nicolás |
| 2 | VIIRS de día | mirar en imagen 5 publicaciones de ≥1 MW fuera de Chillán y 19 protegidas V375 no recuperadas / dejar apagado | Mirar primero (lista en la nota diurna) |
| 3 | Reprocesar de día la historia MODIS tras encender | sí / sólo NRT hacia adelante | Sólo NRT por ahora; reprocesar es otra decisión con su costo |
| 4 | Tabla de episodios OVDAS para el laboratorio (D4 del plan S190) | la arma Nicolás desde RAV / seguir sólo con NHI | Que la arme (plantilla `docs/PLANTILLA_EPISODIOS_OVDAS_S190.md`) |
| 5 | Codex ronda 3 desde el 2026-11-24 | cierre I completo y segunda vuelta de 9, 3 y 5 (`PLAN_3_SEMANAS.md`) / sólo verificar correcciones | Empezar verificando las correcciones ya mergeadas (12 PR), después cierre I |
| 6 | Pendientes heredados | frente 6 de Codex, F1M-114, D15, D-10, D5/D13/D11 de los 34, FIRMS para detecciones lejanas de los 34, F3-110 («or» en MODIS) | ver `tasks/BLOQUE_ARRANQUE_S193.md` §b |
| 7 | Rotar el PAT de `C:\Users\nmend\.claude\settings.json` (sigue ahí) | | Sí (Nicolás) |

Preguntas de Nicolás de S193 sin respuesta explícita: ninguna. «¿cómo va el experimental?» se respondió (copia congelada del detector anterior, nada medido contra OVDAS; plan S190 aprobado; paso 1 lanzado).

## c. Lo aprendido

- **REGLA DEL LOOP (Nicolás, S193, textual):** «no necesitas pedirme permiso para mergear, si es lo que recomiendas puedes hacerlo tu mismo, siempre podemos volver atras». La dueña del loop mergea sola lo que recomienda (CLEAN, CI verde, ficha al mergear, `--match-head-commit`) e informa. A45 para EMPEZAR un cambio y las decisiones científicas siguen siendo de Nicolás. Memoria `feedback_s193_merge_sin_pedir.md`. **Pendiente: llevarla al `CLAUDE.md` del proyecto** (regla «todo PR con mergea #N» y A39) en un PR de main.
- **REGLA GENERAL (worktrees):** una sesión «done» sin archivar retiene su carpeta como cwd; `git worktree remove` vacía el contenido y falla en la carpeta. Archivar primero, quitar después. Cada sesión paralela crea ~1,7 GB en C:. Memoria `feedback_s182_worktrees_acumulados.md`.
- **Proyecto:** `reproc-historia-via.yml` hace checkout del commit del despacho, no de la rama: cada run es homogéneo en código (la tanda 7 mezcla dos versiones por run, no por trozo).
- **Proyecto:** las pruebas que fijan «nace vacío» o «nunca cambia desde el tag X» fallan cuando el cambio es a propósito; ajustarlas con marca A113 y una base nueva, no debilitarlas (#1078, #1085).
- **Proyecto:** el aplicador `aplicar-reemplazo.yml` commitea con GITHUB_TOKEN y no dispara Pages: despachar `pages-deploy.yml` y comprobar el JSON publicado (regla de publicación).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** la sesión «Vigilancias» (local_f8b8ba7b) sigue viva por Remote Control con su worktree vaciado (`.claude\worktrees\kind-hertz-28fdb9`); si se le pide trabajo de repo, recrear el worktree desde `claude/s193-vigilancias-avisos` o archivarla.
- **CONFIRMADO:** el perfil `experimental` no es laboratorio (vía apagada en los tres sensores, Test 1 encendido, `data/experimental_v2`); su YAML dice «idéntico al operacional salvo el directorio», que es falso; el aviso del tablero (pestaña Laboratorio) está desactualizado.
- **SOSPECHA:** MIROVA geolocaliza MODIS con la grilla de 5 km del MOD021KM (explicaría Chaitén 2026-11-19 a 3,6 km); pide otra sonda.
- **SOSPECHA:** Lanin feb-2025, Callaqui mar-2025 y Nevado de Longaví 2026-02-27 son incendios (heredada de S192, sin cotejar).
- **CONFIRMADO:** S192 seguía viva al abrir S193 y lanzó una sesión (mapas, #1079); dos coordinadoras a la vez (regla S153). #1079 se revisó y mergeó.

## e. Ya cerrado, no rehacer

- Tanda 7 y la historia de los 34: completa y aplicada (ensayo 30.860 nuevos, 0 tras el corte; 28 volcanes previos intactos).
- Fondo nulo en MODIS: código (#1065) y datos viejos (#1069, 15 de 15). No reabrir (b) o (c).
- «Radiante» se mantiene (#1085): la variante «cumbre primero» recupera 12 protegidas sólo OCR pero mueve 114 pasadas que la tabla pone lejos y baja la concordancia de 98,73 % a 93,59 %; idéntica en efecto a «cercano» (rechazada 2026-11-15).
- Chaitén 2026-11-19 02:30: juzgada; ninguna variante la recupera en lugar y magnitud (celda al 36 % del umbral).
- Lagos: no es falla del código de MIROVA (Coppola 2016a; el `.m` no tiene máscara de agua); 124 de 14.391 pasadas (0,9 %) con el pico sobre agua; máscara con margen cuesta 1.693 pasadas de cumbre (#1075, MEJ-8). El tablero ya marca «pico sobre agua» (#1079).
- Bow-tie del marcador: separado (#1077); F2-V303 y F3-107 (#1078; el 0,0 por nulo de F3-107 no se cambió a propósito: tocaría 66.236 records).
- Criterio de victoria: sólo nocturno mientras un sensor procese sólo de noche (#1082, MISSION).

## f. Prompt para S194

```
Retomas VRP Chile como sesión dueña del loop (S194). Español de Chile, sin guiones largos, rutas absolutas.
Primero: si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). Si S193 sigue viva, no trabaja más.

1. Verifica antes de creer:
   - git fetch --prune; git status -sb; ficha de main (esperado v1.66 o más); gh pr list.
   - ps -ef | grep esperar_estable (Codex Cierre I; log en D:\vrp-trabajo\temporales\s190_codex_r2\).
   - Estado de las sesiones: A/B diurno (local_1a9c0903), Laboratorio paso 1 (local_90bc2df5), Tablero F5 (local_b062c447),
     Vigilancias (local_f8b8ba7b, carpeta vaciada). Notas en
     C:\Users\nmend\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_63e4043e-88e1-4b47-b998-e7ecbfaf5413\
   - df de C: y D: (C: estaba en 14 GB).
2. Lee tasks/BLOQUE_ARRANQUE_S194.md (rama loop/activo) y la entrada S193 de tasks/LOOP_OBJETIVOS.md §6.
3. Trabajo, en orden:
   a. Día en MODIS: mergear #1084 (resultado del A/B); después el PR (a) del frontend diurno; después terminar el PR (b) del
      perfil (A45 ya autorizado por Nicolás; tag pre-s193-dia-modis; faltan los 6 pasos de la nota diurna) y mergearlo.
   b. Laboratorio paso 1: revisar el PR cuando llegue y mergearlo; paso 2 (sellar el criterio §6 con D5: 30 % y 4 de 9, p < 0,05).
   c. Tablero F5: cuando Nicolás responda en esa sesión, revisar y mergear.
   d. Llevar al CLAUDE.md del proyecto la regla de merge de S193 (memoria feedback_s193_merge_sin_pedir) en un PR.
   e. Codex: desde el 2026-11-24 04:20 UTC, ronda 3 según la decisión 5 de §b.
   f. Decisiones de §b con recomendación.
4. Reglas duras: A45 (tag y sí de Nicolás para EMPEZAR cambios en pipeline/process_*.py, store.py, mirova_equivalent.yaml,
   mirova_v750_codigo.py); los merges que recomiendas los haces tú (CLEAN, CI verde, ficha al mergear, --match-head-commit)
   e informas; nada de git stash; git add por archivo; nunca experiments/_s176_codex/; temporales y worktrees en D:;
   archivar una sesión ANTES de quitar su worktree; números sólo de scripts; .md con newline=""; scripts con rutas
   Windows escritos con Write.
5. Cierra con /cierre al llegar al umbral de contexto del hook.
```
