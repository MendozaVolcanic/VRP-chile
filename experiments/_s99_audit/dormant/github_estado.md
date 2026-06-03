# Auditoría de estado GitHub — trabajo colgado / hallazgos sin registrar (S99)

Fecha: 2026-06-03. Repo: MendozaVolcanic/VRP-chile. Ejecutado con `gh` CLI.

## TL;DR
- **1 issue abierto** (#1, NRT cron fails) — semi-stale, pero el cron SIGUE fallando intermitentemente hoy → vale revisar.
- **0 PRs abiertos**. Todo mergeado.
- En las últimas 200, **1 solo PR cerrado-sin-merge** (#223) y fue **deliberado** (cierre de fase de diagnóstico, no trabajo perdido).
- **~70 ramas remotas stale** sin mergear (claude/* y sNN-*), residuos de worktrees/sesiones viejas; el trabajo ya está en main. Candidatas a poda.
- **47 tags** `pre-*` defensivos; todos parecen tener PR/fix asociado. Ninguno sugiere trabajo perdido.

---

## 1. Issues abiertos (1)

### #1 — "NRT cron: 3+ corridas consecutivas fallaron" (labels: nrt-alert, priority-high; creado 2026-04-25)
- Issue **auto-generado** por `.github/workflows/nrt-monitor.yml`, con auto-comentarios acumulados desde 2026-04-25 hasta **2026-05-25**.
- El origen (abril) fue la racha de fallos OSError 101 que se arregló en S35 (fix H7, fetch.py IPv4 monkey-patch + retries). El issue nunca se cerró ni se silenció el monitor.
- **VERIFICACIÓN HOY (runs nrt.yml)**: estado **intermitente** — alterna success/failure:
  - 2026-06-03 04:01 (in progress/—), 06-02 22:22 success, 06-02 19:39 success, 06-02 14:01 success, **06-02 08:37 failure**, 06-02 03:54 success, 06-01 23:26 success, **06-01 20:19 failure**.
- **Lectura**: NO es la caída total de abril (eso ya está resuelto). Hay un patrón de fallos esporádicos (¿LANCE latencia / granule no disponible en una pasada / timeout per-step?) que conviene diagnosticar. **El issue #1 debería cerrarse (su causa original murió en S35) y, si los fails intermitentes molestan, abrir uno nuevo y específico** — o el auto-monitor seguirá engordando #1.
- **Valor: MEDIO-ALTO** (operacional, NRT es el producto live).

---

## 2. PRs abiertos (0)
Ninguno. Sin trabajo colgado en PRs vivos.

## 3. PRs cerrados sin mergear (últimos 200) → 1
### #223 — "S82: F-S81-A Fase 1 diagnóstico gate intra-radio MIROVA MODIS" (cerrado 2026-05-31, sin merge)
- **Cierre deliberado, NO trabajo perdido.** Era una PR de Fase 1 (diagnóstico, sin tocar pipeline). Sus outputs YA están en main: `docs/F_S81_A_FASE1_DIAGNOSIS.md`, design doc `2026-05-26-f_s81_a_gate_path_d_intra_radio.md`, scripts `experiments/_s82_intra_radio/`, `tasks/BLOQUE_ARRANQUE_S83.md`.
- **Hallazgo valioso pero ya analizado y archivado en S86 como A55 (anti-patrón "gate intra-radio por path")**: 857 FPs MODIS, 99.5% Path D puro, 89% a >10 km del cráter, 98% MIROVA `RUTINA(vrp=0.0)`. La Fase 2 (implementar gate intra-radio Opción A) quedó **bloqueada a propósito** — S86 (A55) la marcó como redundante/riesgosa (el frontend ya suprime intra-radio). 
- **Valor de reabrir: BAJO** — está conscientemente parqueado, no olvidado.

Los otros ~58 PRs cerrados en la ventana están **todos mergeados** (#265–#324). Sin descartes ocultos.

---

## 4. Ramas remotas stale (~70, no mergeadas)
Residuos de sesiones S33–S95 y worktrees Claude (`claude/s7x-*`, `claude/s8x-*`, `s72-*`, `s70-*`, `s71-*`, `s95/*`). El trabajo correspondiente ya está en main vía PRs mergeados. Notables por nombre (no por valor pendiente):
- `claude/research-workflow-refactor`, `claude/s73-lit-search-*`, `claude/s74-aveni-*`, `claude/s75-f31-tirvolch-detector` — investigación/extracción que terminó en docs.
- `claude/sweet-austin-b5413b`, `claude/funny-mendeleev-99b1f4`, `claude/hardcore-gauss-68c3db` — worktrees huérfanos ya conocidos (MEMORY.md S82-prep los marca descartables).
- `s15-dev` — branch histórico stale (S33), ya documentado.
- **Acción sugerida**: poda con `clean_gone` / `git push origin --delete` tras confirmar 0 commits únicos no-mergeados. **Valor de trabajo recuperable: muy bajo** (todo lo bueno llegó a main).

## 5. Tags (47, todos `pre-*` defensivos + algunos `sNN-frontier`)
Cada `pre-sNN-<feature>` corresponde a un fix/PR mergeado (patrón A45/A38). Spot-check: `pre-s98-detection-anchor`/`pre-s98-promote-operational`→#318/#320; `pre-s96-nrt-current-day`→#300; `pre-s94-*`→#294. **Ningún tag huérfano que sugiera un fix nunca aplicado.** Son red de seguridad de rollback, funcionando como diseñado.

---

## RANKING por valor potencial a revisar
1. **Issue #1 (NRT fails)** — único item con acción operacional real. Cerrar el issue stale (causa abril ya resuelta S35) + diagnosticar los fails intermitentes de jun-02/01 si molestan. **MEDIO-ALTO.**
2. **Poda de ~70 ramas stale** — higiene, no recupera trabajo. **BAJO.**
3. **PR #223 / Fase 2 gate intra-radio** — conscientemente bloqueada por A55; reabrir solo si se reconsidera la decisión. **BAJO.**
4. Tags `pre-*` — nada que recuperar. **NULO.**

**Conclusión**: NO hay trabajo valioso colgado/olvidado en GitHub. Lo único accionable es el issue #1 (limpieza + posible diagnóstico de fails intermitentes del NRT).
