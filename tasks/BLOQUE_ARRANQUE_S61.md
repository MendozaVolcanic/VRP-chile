# BLOQUE DE ARRANQUE S61 — VRP Chile

> Documento creado al cierre de S60 (2026-05-17).
> Sesión S60 cerró con audit A+B+B2 completo + offline per-vol opt-in audit.
> Workflow C corriendo asíncrono (run 25998365888, ETA 21:43 UTC), terminación pendiente.

---

## 1. Lectura obligatoria al inicio S61

1. **Este doc** (`tasks/BLOQUE_ARRANQUE_S61.md`) — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S60.md`** — contexto histórico maratón S52-S58 (sigue vigente)
3. **`experiments/104_s60_*.md`** (4 docs) — audits S60 completos:
   - `104_s60_audit_a_recall_new_vs_csv.md` — recall sin regresión
   - `104_s60_audit_b_distribution_vs_osf.md` — distribución vs OSF
   - `104_s60_audit_b2_decompose_by_mirova_day.md` — descomposición clave
   - `104_s60_per_vol_opt_in_offline_audit.md` — solo Villarrica necesita fix
4. **`docs/HYPOTHESIS_LOG.md`** entry `H_S60_KERNEL_BG_HELPS_MIROVA_DAYS`
5. **`pipeline/profiles/mirova_equivalent.yaml`** — verificar flags actuales
6. **Workflow C resultado**: `gh run view 25998365888 -R MendozaVolcanic/VRP-chile`

---

## 2. Estado al cierre S60

### 2.1 Evidencia recolectada

**Audit A (recall NEW vs MIROVA CSV)**:
- ✅ Sin regresión: NEW detecta 4/5 refs MIROVA = LEGACY (2 ALERTA 2/2, 2/3 FP).
- ✅ Caso paradigmático 2026-05-11: ratio 18.8× → 1.61× (cura inflación extrema).

**Audit B (distribución vs OSF v2.5)**:
- ⚠️ Mediana NEW VIIRS375 summit 2.10 MW vs target curado 1.06 MW (gap 99%).
- ✅ Mejora marginal vs LEGACY 2.16 (-2.7%).

**Audit B2 (descompuesto por MIROVA-day status — HALLAZGO CLAVE)**:
- ✅ Días MIROVA reportó (n=17): NEW med **1.51 MW** vs LEGACY 1.88 MW (**-20%**, gap a OSF 42%).
- = Días RUTINA (n=94): NEW = LEGACY 2.19 MW (fix no actúa sin lago contaminando).
- Top 10 outliers NEW son TODOS días RUTINA = sobre-detección sub-MIROVA, no FP propio.

**Per-vol opt-in offline audit**:
- 🔴 **Solo Villarrica necesita el fix**. Window-aligned VIIRS375 ratio LEGACY/MIROVA:
  - Villarrica: **5.68×** (sobre-estima — fix necesario)
  - Copahue: **1.14×** (calibrado — fix marginal o dañino)
  - Llaima: **1.01×** (calibradísimo — fix dañino)
  - PlanchónPeteroa: sin scraper CSV (no decidible offline)

### 2.2 Workflow C asíncrono

[Run 25998365888](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/25998365888):
- Comando: `reproc-ab-local-kernel-bg.yml` start=2026-02-20 end=2026-05-15
- Timeout aumentado a 300 min (PR #68 mergeado S60)
- ETA finalización: 2026-05-17 21:43 UTC (~3h48m post-trigger 17:55 UTC)
- Si termina OK: validar fix Villarrica sobre 5 ALERTAS (no solo 2 del window S58)

### 2.3 Pipeline operacional intacto

```yaml
# pipeline/profiles/mirova_equivalent.yaml
enable_local_kernel_bg: false   # NO adoptado operacional aún
```

```yaml
# volcanoes.yaml (S59 per-vol opt-in)
- Villarrica: local_kernel_bg: true
- Copahue: local_kernel_bg: true       # ⚠️ revisión recomendada S61
- Llaima: local_kernel_bg: true         # ⚠️ revisión recomendada S61
- PlanchonPeteroa: local_kernel_bg: true  # ⚠️ revisión recomendada S61
- Tupungatito: local_kernel_bg: false   # excluido por ring frío
```

---

## 3. Pendientes priorizados S61

### Prioridad ALTA

1. **Validar resultado workflow C** (run 25998365888)
   - Adaptar audit A para window 02-20/05-15 sobre 5 ALERTAS MIROVA Villarrica
   - Confirmar que fix mantiene recall + mejora calibración en MIROVA-days
   - Si confirma: adopción operacional defendible

2. **Decisión adopción operacional `mirova_equivalent.yaml`**
   - Opción A: cambiar `enable_local_kernel_bg: false` → `true` (solo afecta vols con `lbg_compatible`)
   - Opción B: mantener flag profile false + dejar per-vol Villarrica only
   - Riesgo opción A: si flag profile=true Y per-vol Villarrica/Copahue/Llaima/Planchón=true, fix aplicará a los 4 sin validación previa
   - Riesgo opción B: pipeline operacional NO usa el fix; flag queda como "infraestructura disponible"

3. **Revisión `volcanoes.yaml` per-vol**
   - Cambiar `local_kernel_bg: false` para Copahue, Llaima (gap calibrado, fix dañino)
   - PlanchónPeteroa: pendiente CSV scraper update o audit con A/B
   - Mantener Villarrica: true

### Prioridad MEDIA

4. **Si adopción Villarrica only**: dashboard verificación
   - Confirmar que magnitudes Villarrica post-adopción no rompen frontend
   - Re-validar contra MIROVA web casos individuales

5. **A/B Copahue / Llaima opcional**
   - Solo si Nicolás quiere confirmar empíricamente que el fix NO daña
   - Costo: 2× ~3h cada uno en GH Actions
   - Saltable: la evidencia offline ya muestra gap calibrado

### Prioridad BAJA

6. **Refinamientos kernel** (solo si Villarrica adoptado y se busca converger más)
   - `kernel_size=5` (25 vecinos vs 9) — más estabilidad estadística
   - Percentile p25 del kernel en lugar de mean — robusto a outliers vecinos

7. **PlanchónPeteroa scraper completion**
   - Coordinar con Nicolás para que Mirova-v1 scraper incluya este vol
   - Sin CSV, no se puede auditar empíricamente

---

## 4. Errores S60 a NO repetir S61

1. **Disparar workflow sin verificar timeout vs duración real**: el reproc 90d con
   timeout 110 min original habría muerto a los 110 min. Verificar siempre que
   `timeout-minutes >= duración_esperada × 1.3` margen.

2. **Comparar contra OSF agregado en lugar de MIROVA NRT window-aligned**: el target
   correcto para audit operacional es MIROVA CSV NRT (lo que MIROVA publica actualmente),
   no OSF v2.5 (curado histórico, sesgado a episodios antiguos).

3. **Asumir mediana agregada como medida de calibración**: la mediana mezclada
   MIROVA-day + RUTINA-day infla artificialmente. Decomponer SIEMPRE.

4. **Marcar opt-in per-vol por presencia geométrica de agua sin validar gap empírico**:
   S59 PR #65 puso 4 vols en `local_kernel_bg: true` por presencia de lago. S60 descubrió
   que solo Villarrica realmente lo necesita (Copahue/Llaima ya calibrados).

---

## 5. Estado git al cierre S60

- Branch: `claude/quizzical-zhukovsky-ceadfa` (worktree)
- PR mergeado S60: **#68** (S60 audit + widen workflow C timeout)
- Último commit main: post-merge #68
- Workflow C corriendo: run 25998365888 (timeout 300 min)
- Cierre PR adicional pendiente con per-vol audit + bloque arranque S61

---

## 6. Persistencia in-vivo (regla meta-meta)

Cuando termine workflow C en S61, persistir resultado audit inmediatamente en
`experiments/105_s61_*.md` antes de proceder con decisión adopción. NO acumular
hallazgos en contexto, escribir a docs.
