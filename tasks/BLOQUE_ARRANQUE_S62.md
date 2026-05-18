# BLOQUE DE ARRANQUE S62 — VRP Chile

> Documento pre-escrito S61 (workflow PP corriendo). Finalizar valores `<X>`,
> `<Y>`, `<Z>` post-audit Task 3.

---

## 1. Lectura obligatoria al inicio S62

1. **Este doc** (`tasks/BLOQUE_ARRANQUE_S62.md`) — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S61.md`** — contexto S61 + workflow C Villarrica
3. **`tasks/BLOQUE_ARRANQUE_S60.md`** — contexto histórico maratón S52-S58
4. **`experiments/104_s60_*.md`** (4 docs) — audits A+B+B2+per-vol Villarrica
5. **`experiments/105_s61_audit_planchon_results.md`** — A/B PlanchonPeteroa
6. **`docs/HYPOTHESIS_LOG.md`** entries `H_S60_KERNEL_BG_HELPS_MIROVA_DAYS` + `H_S61_PLANCHON_KERNEL_BG`
7. **`pipeline/profiles/mirova_equivalent.yaml`** — confirmar flags actuales

---

## 2. Estado al cierre S61

### 2.1 Adopción operacional

`enable_local_kernel_bg: <true|false>` en `mirova_equivalent.yaml` operacional.
Decisión final dependía de Task 3 (audit PlanchonPeteroa).

Per-vol flags en `volcanoes.yaml` post-S61:

| Vol | local_kernel_bg | Razón |
|---|---|---|
| Villarrica | true | Audit C S60: ratio 33× → 2.16× sobre 5 ALERTAS |
| PlanchonPeteroa | <true/false> | Audit S61: ratio <Z>× sobre <39> ALERTAS |
| Copahue | false | Calibrado 1.14× (revertido S61 PR #71) |
| Llaima | false | Calibradísimo 1.01× (revertido S61 PR #71) |
| Tupungatito | false | Ring frío glaciar (excluido S59) |

### 2.2 Métricas finales S61

- Villarrica audit C: ratio mediano LEGACY 33× → NEW 2.16× sobre 5 ALERTAS
- PlanchonPeteroa audit S61: ratio mediano LEGACY <X>× → NEW <Y>× sobre 39 ALERTAS
- Tests: 335 passed / 16 skipped

### 2.3 NRT operacional

Cron NRT cada 2h aplica el nuevo comportamiento si Task 5 ejecutado. Si Task 5
NO ejecutado (workflow PP no validó): solo Villarrica per-vol queda en true pero
profile flag false → comportamiento idéntico a pre-S61.

---

## 3. Pendientes priorizados S62

### Prioridad ALTA (extender Task 7 S61)

1. **Monitorear próximos 5-10 ciclos cron NRT** desde adopción Task 5.
   - Verificar Villarrica + PlanchonPeteroa procesan OK
   - Comparar magnitudes vs últimos pre-deploy (no salto x10, no 0)
   - Dashboard cross-check GitHub Pages

### Prioridad MEDIA (refinamientos)

2. **Refinamiento kernel_size=5 A/B Villarrica** (investigación S61 subagent disponible):
   - **Pre-trabajo S61 ya hecho**:
     - Función `pipeline/vrp_regimes.py:21-89` ya acepta `kernel_size` parametrizable (default 3)
     - Test `tests/test_local_kernel_background.py:125-139` ya valida kernel_size=5 (24 vecinos)
     - Call sites hardcoded en `pipeline/process_viirs.py:801` y `pipeline/process_modis.py:664`
   - **Cambio requerido**: ~5 líneas en 2 archivos + flag profile `local_kernel_size` en `profile.py:244`
   - **Hipótesis física**: NEW Villarrica median ALERTA = 1.51 MW vs target OSF curated 1.06 MW (gap 42% sobre target). Kernel 5×5 (~1.9×1.9 km en VIIRS 375m) podría capturar borde lago norte → t_bk sube → ΔL baja → VRP más cerca target.
   - **Riesgo**: kernel 5 podría sobre-corregir y bajar magnitud por debajo de target en casos donde 3×3 ya estaba calibrado.
   - **Plan A/B**: similar a S61 PP, crear `_local_kernel_bg_5x5_enabled` profile, reproc Villarrica window 02-20/05-15.

3. **NO investigar p25 percentile** — dirección de bias incorrecta:
   - NEW SOBRE target 1.51 vs 1.06 → bajar t_bk con p25 ampliaría gap, no lo cerraría.
   - Razonamiento subagent S61 (sección D) confirma anti-recomendación.

### Prioridad ALTA — extender A/B a 4 vols adicionales (hallazgo offline S61)

⚠️ **Audit completo Tier A VIIRS375 window 04-16/05-15 reveló gaps significativos**:

| Vol | MIROVA n | LEGACY/MIROVA gap | Acción S62 |
|---|---:|---:|---|
| Lascar | 43 | 1.04× ✓ calibrado | mantener `false` (no fix) |
| Copahue | 7 | 1.14× ✓ | mantener `false` (S61 PR #71) |
| Llaima | 10 | 1.01× ✓ | mantener `false` (S61 PR #71) |
| **Lastarria** | **35** | **3.99×** | A/B candidato — fumarolas crónicas, ring posiblemente contaminado |
| **Isluga** | **26** | **4.80×** | A/B candidato — actividad permanente, ring posiblemente afectado |
| **Tupungatito** | **22** | **9.80×** | A/B revisar S59 ("ring frío glaciar empeoraría") |
| Nevados de Chillán | 3 | 10.9× | n bajo — esperar más alertas, no A/B aún |
| **PCC** | **22** | **52.77×** ‼️ | **A/B alto impacto** — lacolito + lago Caulle norte |
| Chaiten | 1 | 28× | n=1 no representativo |

**Plan A/B sistemático S62** para los 4 candidatos prioritarios (Lastarria, Isluga,
Tupungatito, PCC):
1. Crear workflows análogos a `reproc-ab-local-kernel-bg-pp.yml` per vol
2. Reproc window 02-20/05-15 cada uno (~3h GH Actions)
3. Audit pre/post con script `experiments/105_*` adaptado
4. Si valida (recall sin regresión + ratio mediano <50% del LEGACY):
   - Cambiar `local_kernel_bg: true` en `volcanoes.yaml` per vol
5. Resultado esperado: ratio mediano global Tier A cerca de 1.5× post-adopción

**Costo total**: 4 vols × ~3h GH Actions = 12h (en paralelo: 1 día calendario).

### Prioridad MEDIA-ALTA — revisar Tupungatito (hallazgo S61)

⚠️ **Audit window-aligned 04-16/05-15 reveló**:
- Tupungatito: 22 ALERTA MIROVA VIIRS375 con median **0.19 MW**
- LEGACY summit VIIRS375 window: n=93, median **1.87 MW**
- **Gap LEGACY/MIROVA mediano = 9.8×** (sobre-estima, similar a Villarrica 5.68×)

Pero S59 PR #65 lo excluyó con `local_kernel_bg: false` ("ring frío glaciar empeoraría").
La razón S59 asumió kernel 3×3 sobre vecinos glaciar fríos → ΔL inflado. Pero si el pixel
hot está EN el cráter, sus 8 vecinos directos pueden ser roca caliente residual (no
glaciar), por lo que L_bg sería ALTO y ΔL bajo (corrigiendo la inflación 9.8×).

**Pendiente S62**:
- Confirmar geometría real Tupungatito: ¿cráter rodeado por glaciar o por roca?
- Si hay roca adyacente: A/B Tupungatito local_kernel_bg=true. Costo ~3h GH Actions.
- Si pure glaciar: confirmar S59 decisión, investigar otro mecanismo.

NO PRIORITARIO S61 porque mantener Tupungatito en false no es regresión (mantiene
comportamiento actual), pero es deuda técnica clara.

### Prioridad BAJA

4. **R2 pixel-level validation Villarrica casos paradigmáticos**
   - Caso 2026-05-11: TIF MIROVA debería mostrar 1 píxel cráter ~500m, NEW 0.50 MW @ 0.79km matchea
   - Caso 2026-05-14 (regresión 0.97×→2.17×): investigar por qué LEGACY estaba mejor
   - Casos 2026-04-09, 2026-03-08, 2026-02-26: confirmar cluster cráter en TIF

5. **Investigar gap recall 53%** Villarrica audit C
   - Causa estructural: 6/15 MIROVA refs son daytime UTC (13-19) que nuestro pipeline NO procesa (regla MIR-nocturno Coppola). Esto es decisión metodológica documentada, no bug.
   - Recall solo-ALERTAS noche: 5/5 = 100%.
   - Decisión: aceptar gap como costo metodológico, NO investigar fix daytime.

6. **PlanchonPeteroa magnitudes investigación adicional**
   - 39 ALERTAS window con magnitud MIROVA mediana muy baja (0.1-0.3 MW)
   - Si NEW logra ratio mediano <3×, validar contra TIF MIROVA
   - Si NEW recall regresiona vs LEGACY (improbable según teoría): revertir per-vol

---

## 4. Errores S61 a NO repetir S62

1. **Buscar nombre vol en CSV con TODAS las variantes**: S60 perdió PlanchonPeteroa
   porque busqué `'Planchon-Peteroa'` (con guión). El correcto es `'PlanchonPeteroa'`
   sin guión. Variantes a probar siempre: con/sin guión, con/sin tilde.

2. **Verificar workflow timeout vs duración esperada antes de disparar**: S60 disparó
   workflow con timeout 110 min para reproc ~228 min. PR #68 extendió a 300 min, pero
   verificar siempre antes.

3. **Comparar contra MIROVA CSV NRT window-aligned, no OSF agregado**: OSF mezcla
   25 años de historia que sesga el target. Para audit operacional, MIROVA NRT actual
   es lo único válido.

4. **No asumir que un vol "tiene lago en ring" → necesita fix kernel-bg**: el mecanismo
   importa (lago cálido vs glaciar heterogéneo vs lago frío) Y el gap empírico debe
   validar antes de marcar `local_kernel_bg: true`.

5. **Subagent investigación contradicciones**: en sección D del reporte refinamientos
   S62, el subagent inicialmente predijo p25 ayudaría, luego se autocorregió en mitad
   del razonamiento. Validar siempre dirección del bias antes de implementar.

---

## 5. Estado git al cierre S61

- Branch principal: `main`
- PRs S61 mergeados:
  - PR #70: workflow A/B PlanchonPeteroa + plan
  - PR #71: revert Copahue/Llaima flags
  - PR #72 (cierre): Task 5 adopción + Task 6 cierre <pendiente>
- Workflow A/B activos: ninguno (PP completó)

---

## 6. Persistencia in-vivo (regla meta-meta)

Cuando descubrás hallazgo durante S62: persistir INMEDIATAMENTE en
`docs/HYPOTHESIS_LOG.md`. NO esperar al cierre. La sesión puede cortarse
abruptamente.

---

## 7. Quick reference comandos comunes

```bash
# Check workflow status
gh run list -R MendozaVolcanic/VRP-chile --limit 5 --json status,name,createdAt

# Trigger A/B
gh workflow run <name>.yml -f start=YYYY-MM-DD -f end=YYYY-MM-DD -R MendozaVolcanic/VRP-chile

# Run audit comparison
python experiments/105_s61_audit_planchon_kernel_bg.py

# Test suite
python -m pytest tests/ -x -q

# PR creation pattern
git push && gh pr create --title "..." --body "..."
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```
