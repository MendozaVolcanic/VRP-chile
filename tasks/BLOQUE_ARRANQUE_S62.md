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
| **Lastarria** | **35** | **3.99× / pc 2.3×** | borderline tolerable (criterio ≤2.0× CLAUDE.md) — investigar opcional |
| **Isluga** | **26** | **4.80× / pc 1.5×** | ✓ **calibrado con pc.vrp_mw** — no requiere fix |
| **Tupungatito** | **22** | **9.80× / pc 7.0×** | gap moderado — investigar pixel BT edge mixing |
| Nevados de Chillán | 3 | 10.9× | n bajo — esperar más alertas, no A/B aún |
| **PCC** | **22** | **52.77× / pc 6.9×** | mecanismo distinto (ver sección PCC abajo, NO kernel-bg) |
| Chaiten | 1 | 28× | n=1 no representativo |

**Plan A/B sistemático S62** para los 4 candidatos prioritarios (Lastarria, Isluga,
Tupungatito, PCC):
1. Crear workflows análogos a `reproc-ab-local-kernel-bg-pp.yml` per vol
2. Reproc window 02-20/05-15 cada uno (~3h GH Actions)
3. Audit pre/post con script `experiments/105_*` adaptado
4. Si valida (recall sin regresión + ratio mediano <50% del LEGACY):
   - Cambiar `local_kernel_bg: true` en `volcanoes.yaml` per vol
5. Resultado esperado: ratio mediano global Tier A cerca de 1.5× post-adopción

**Plan revisado S62 (POST-investigación completa S61)**: **NINGÚN vol adicional necesita
kernel-bg**. Tupungatito también muestra patrón Test 1 sobre-detección (n_pix median 76,
src test1 87%). Los 4 vols con gap moderado-alto (Lastarria 4×, Isluga 5×, Tupungatito
10×, PCC 53×) comparten **1 problema arquitectural común**: Test 1 path sobre-detección.

**Costo total revisado**: 0 GH Actions adicionales kernel-bg. Solo investigación código
Test 1 + test sintético (estimado 1-2h trabajo local, sin reproc).

### Prioridad ALTA — Test 1 path sobre-detección (afecta Lastarria, Isluga, PCC y posiblemente más)

Análisis paralelo S61 reveló **patrón común** entre Lastarria, Isluga, PCC:

| Vol | n_anomalous_pixels median (summit anom records) | gap LEGACY/MIROVA |
|---|---:|---:|
| Lastarria | 71 | 3.99× |
| Isluga | 69 | 4.80× |
| **Tupungatito** | **76** | **9.80×** |
| PCC VIIRS_I (lacolito) | 200-470 | 28-34 MW vs MIROVA 0.23 (factor ~130×) |

**Hipótesis dominante (S62 H_S62_TEST1_OVERDETECTION)**:
- MIROVA Coppola 2015 §2.2 Eq.1 Test 1 integrated-ROI tiene threshold pixel-level que
  nuestro código no replica fielmente. Aceptamos 70-470 pixels donde MIROVA filtra a 1-5.
- Esto infla la suma VRP del cluster summit aún con localización correcta.
- Mismo mecanismo en 3 vols Tier A (Lastarria, Isluga, PCC). Posiblemente Tupungatito también.

**Plan S62 investigación Test 1**:
1. Leer `pipeline/process_viirs.py` función Test 1 integrated-ROI. Comparar con
   Coppola 2015 §2.2 línea por línea.
2. Identificar el threshold pixel-level específico que diferencia "anomalous" vs
   "background" según paper.
3. Test sintético con cluster conocido (28 px MIROVA vs nuestro 71 px) — verificar
   si threshold más estricto reduce n_anomalous a rango MIROVA.
4. Si confirma: fix arquitectural a Test 1 que beneficia 3-4 vols simultáneamente.

**NO disparar A/B kernel-bg para Lastarria/Isluga/PCC** — gastaría 9h GH Actions
sin curar el problema real.

### Prioridad ALTA — PCC inflación 52× requiere fix DISTINTO (NO kernel-bg)

⚠️ **Subagent investigation S61** refutó hipótesis "PCC necesita kernel-bg como Villarrica/PP".

**Razón**: gradient ring +4.5 K POSITIVO (S60 audit línea 588 HYPOTHESIS_LOG). Es decir,
nuestro ring 5-25 km está MÁS CALIENTE que el cráter, no más frío. El kernel local no
ayudaría (subiría background → bajaría VRP → no resuelve inflación 52×).

**Mecanismo real de la inflación 52×** (doble):

1. **D-PCC-1: Cluster selection lejano residual**. `inner_radius_km=20` en `volcanoes.yaml`
   (vs Villarrica=5, Lascar=5, Lastarria=3) clasifica clusters hasta 20 km del lacolito
   como `summit`. Records ejemplo MODIS:
   - 2026-05-17 06:55 AQUA: vrp=311 MW @ 19.83 km (109 px)
   - 2026-05-15 07:15 AQUA: vrp=312 MW @ 17.79 km (436 px)
   - 2026-05-15 03:00 TERRA: vrp=522 MW @ 19.59 km (105 px)

   Estos no son el lacolito 2011 (que está a <2 km). Son clusters dispersos en escena
   ancha (probable Antillanca/Mocho/ground burns/Lago Ranco signatures).

2. **D-PCC-2: Magnitud sobre-estimada VIIRS_I Test 1**. Aún con vent_anchored eligiendo
   lacolito correctamente, Test 1 path acepta 200-470 pixels anómalos en el cluster
   summit. vrp 28-34 MW vs MIROVA ~0.23 MW. Probable: nuestro Test 1 path suma pixels
   marginales que MIROVA filtra con threshold más estricto (Coppola 2016a fixed-ROI sum
   literal vs nuestro implementación).

**Plan S62 para PCC** (NO disparar A/B kernel-bg):

1. **Reducir `inner_radius_km` 20 → 7-10** en `volcanoes.yaml`. Reclasifica clusters
   >7-10 km como `far` (gris en dashboard, no infla summit median). Bajo riesgo:
   reverte fácil si rompe recall.
2. **Auditar `cluster_hotspots(vent_anchored)` PCC**: extraer 5 records MODIS summit
   y dump `clusters[]` completo. Verificar si vent_anchored elige el cluster correcto
   o si por tamaño gana lejano. Si bug: fix similar a D8.
3. **Investigar pixel-counting VIIRS_I Test 1**: 200-470 pixels anómalos sobre lacolito
   es mucho vs MIROVA. Comparar pixel-by-pixel contra TIF MIROVA (R2). Posible reducir
   sensibilidad Test 1 o aplicar second-pass más estricto.

**NO modificar S61** (mantener PCC config actual). Es problema arquitectural distinto
que merece sesión propia S62.

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

0. **USAR `pc.vrp_mw` (NO `record.vrp_mw`) para comparar con MIROVA NRT**:
   - `record.vrp_mw` = sum scene-wide de todos los hot_pixels del granule
   - `record.primary_cluster.vrp_mw` = solo del cluster summit selected (igual que MIROVA)
   - Dashboard usa `pc.vrp_mw` (frontend/index.html:680). REAUDITORIA_S52 documentó esto, S61 lo olvidé.
   - Gap real de los 4 vols controvertidos S61 con `pc.vrp_mw`:
     - Tupungatito 7.0× (no 9.8×)
     - Lastarria 2.3× (no 3.99×)
     - Isluga 1.5× ✓ calibrado (no 4.80×)
     - PCC 6.9× (no 52.77×)

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
