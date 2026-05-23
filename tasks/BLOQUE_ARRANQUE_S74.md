# Bloque arranque S74 — VRP Chile (post cierre S73 2026-05-23)

> Continuación tras cierre S73. PR #133 listo para review/merge con fix F2.8 saturation guard MODIS+VIIRS triple-verificado. Tests 413+24sk passed. Reproc empírico post-merge pendiente.

## 1. Estado al cierre S73

### F2.8 Saturation Guard — COMPLETO (excepto reproc post-merge)

- ✅ **F2.8.a**: Investigación triple-verificada contra PDFs primarios (Wooster 2003, MODIS L1B C7 UserGuide, VIIRS L1B UserGuide Aug 2021, Coppola 2025 cap.11). Doc `F28_SATURATION_INVESTIGATION.md` con citas verbatim.
- ✅ **F2.8.b**: 10 hipótesis (8 implementadas, 2 refutadas). Doc `F28_HYPOTHESIS_LOG.md`.
- ✅ **F2.8.c**: 33 tests TDD (`test_saturation_guard_f28.py` 27 + `test_pipeline_integration_f28.py` 6). Match matemático 99.86% con record observado.
- ✅ **F2.8.d**: Plan bite-sized 9 tasks en `docs/superpowers/plans/2026-05-23-f28-saturation-guard.md`.
- ✅ **F2.8.e**: Implementación 5 commits limpios:
  - MODIS L1B sentinel filter `dn > 32767` (Task 1, H1)
  - VIIRS I/M-band quality_flags bit-2 read (Tasks 2-3, H2+H10)
  - BT secondary defense MODIS B21 > 500K (Task 4, H3)
  - Frontend diario.html guard pc.vrp_mw > 50K (Task 5, H5)
  - CLAUDE.md A35/A36/A37 (Task 9)
- ✅ **F2.8.g**: Adopción operacional + CLAUDE.md
- 🟡 **F2.8.f**: workflow `reproc-f28-pp-saturation.yml` listo en la branch. Bloqueado por GH limitation: `workflow_dispatch` requiere yml en default branch. **Ejecutar post-merge PR #133**.

### PR #133

URL: https://github.com/MendozaVolcanic/VRP-chile/pull/133
Estado: open, listo para review.
Branch: `claude/s73-f28-saturation-guard`
Commits: 7 (76227da → a9b40fa).

### Tests

- 413 passed, 24 skipped (baseline S72 era 380; +33 nuevos F2.8)
- 0 regresiones operacional
- Match matemático MODIS bug 99.86%
- Match matemático VIIRS outliers <2% error

### Skills nuevas instaladas (subagente background S73)

- `xarray` — para NetCDF VIIRS processing (ya disponible en harness)
- `claude-scientific-writer` (4 subskills): scientific-writing, literature-review, citation-management, venue-templates — para paper VRP Chile S72 en draft

## 2. Priorización S74

### P1 — F2.8.f reproc empírico (URGENTE post-merge)

**Pre-requisito**: PR #133 merged a main.

**Comando**:
```bash
gh workflow run reproc-f28-pp-saturation.yml \
  --ref main \
  -f start=2026-03-18 \
  -f end=2026-03-18 \
  -f profile=mirova_equivalent
```

**Esperado** (~5-10 min runtime):
- 9 records PP 2026-03-18 reprocesados con fix activo
- Fósil `MODIS_AQUA 08:05 pc.vrp_mw=695,431 MW` eliminado
- A/B audit inline en el workflow log: BEFORE vs AFTER snapshot guardados en `experiments/138_f28_saturation_ab/`
- Commit automático del JSON saneado + snapshots

Si verdict matches predicción → cerrar F2.8 al 100% y documentar en `docs/F28_REPROC_PP_2026_03_18.md`.

### P2 — Task Scheduler Windows NRT local + observación 48h

Una vez F2.8.f confirma fix empírico:

```powershell
schtasks /Create /TN "VRP_Chile_NRT" /TR "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70\scripts\nrt_local.bat" /SC HOURLY /MO 2 /F
```

Setup cron cada 2h Windows. Observar 48h:
- Logs en `logs/nrt_local/`
- Push exitoso a main
- Race con GH Actions cron mitigado con `git pull --rebase -X theirs` antes de push

Si 48h funciona → comentar `cron:` en `.github/workflows/nrt.yml` (deshabilitar GH Actions cron). Mantener `workflow_dispatch` para reprocs manuales.

### P3 — T1.5: drift remanente Villarrica/Chaiten/PP/PCC

**Estado actual**: ratios 6-12× contra MIROVA NRT en régimen Tier A Muy Bajo (objetivo REAL desde S71).

**Hipótesis F2.6 actualizada**:
- HT1.5-NEW-5 (NUEVA post-F2.8): ¿C2·σ contextual de Tests 2&3 demasiado permisivo en régimen Muy Bajo? Massimetti 2024 §561-562 dice MIROVA usa Tabla 1 C2=5/10 estándar. Pero σ_bg está distinto por sensor (VIIRS I-band 375m vs MIROVA referencia MODIS 1km).

**Sub-tareas**:
- F3.1 — análisis per-record drift Vill/Chaiten/PP/PCC: ¿ratio inflado viene de pixels marginales o brillantes?
- F3.2 — A/B Tests 2&3 con C2=10 summit / C2=15 scene (más estricto)
- F3.3 — verificar dual_roi_first_pass per-vol Muy Bajo

### P4 — M-band kernel-bg implementation (TODO F2.9 ya casi cerrado)

`process_viirs_mod.calculate_vrp` acepta `local_kernel_bg_compatible` como **no-op**. Implementar block real replicando `process_viirs.py:856-867`. Simetría I-band/M-band para vols opt-in (Villarrica/PP/Lastarria/Chaiten/PCC).

### P5 — Paper open source VRP Chile iteración

`docs/PAPER_VRP_CHILE_DRAFT_S72.md` (PR #119). 3 decisiones pendientes:
- **Venue**: Frontiers Earth Sci Vulcanology (recomendado) vs RS MDPI vs JVGR vs GMD.
- **Authorship**: Nicolás lead. Co-autores SERNAGEOMIN/MIROVA team. Claude/Anthropic NO co-author (policy 2026) → Acknowledgments + Code availability.
- **Scope**: literal-clone vs incluir extensions D9 cap + Tupungatito + AVTOD + F2.8 saturation guard.

**Skills nuevas disponibles** para acelerar paper:
- `claude-scientific-writer:scientific-writing` (IMRAD structure)
- `claude-scientific-writer:literature-review`
- `claude-scientific-writer:citation-management` (Zotero integration)
- `claude-scientific-writer:venue-templates`

Iteración requiere T1.5 cerrado.

## 3. Backlog adicional (sin urgencia)

- AVA ASTER Volcano Archive scrapear (F1.11 backlog) — combinable con AVTOD para validation multi-sensor.
- AVTOD Table S1 supplementary descarga manual.
- Cigolini 2022 EPSL (DOI 10.1016/j.epsl.2022.117726) — Cloudflare 4 fuentes bloqueadas, pedir a autor via ResearchGate.
- Massimetti THESIS extracción exhaustiva (ya convertido a .md).
- Bug get_effective_vent fallback chain (F1.6 hallazgo arqueológico) — post-S65 cae a `volcano_lat` en lugar de `vent_lat` cuando `mirova_center` ausente.
- VIIRS M15 sat threshold verificación contra JPSS L1B Section 5.X (asumimos 423K por simetría con I05, pero confirmar).
- H8 — sec³(θ_z) amplification audit: revisar otros patrones donde scan-angle pueda amplificar bugs similares.

## 4. Quick start S74

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"

# Sync con main (PR #133 debe estar merged)
git fetch origin --prune
git checkout main && git pull --ff-only

# Verificar PR #133 estado
gh pr view 133

# F2.8.f reproc (P1)
gh workflow run reproc-f28-pp-saturation.yml --ref main \
  -f start=2026-03-18 -f end=2026-03-18 -f profile=mirova_equivalent

# Monitor
gh run list --workflow=reproc-f28-pp-saturation.yml --limit 3
gh run watch <RUN_ID>

# Tests baseline
python -m pytest tests/ -q
# Target: 413 passed (+ los del PR #133 mergeados)
```

**Arrancar S74 leyendo**:
- Este doc + `docs/F28_SATURATION_INVESTIGATION.md` (verdict final F2.8) + `docs/F28_HYPOTHESIS_LOG.md`.
- Si F2.8.f reproc OK: persistir `docs/F28_REPROC_PP_2026_03_18.md` con resultados.

## 5. Aprendizajes meta S73

| ID | Aprendizaje | Source |
|---|---|---|
| **A35** | Notas Vault `ai_generated` necesitan verificación verbatim PDF para valores numéricos críticos. Jerarquía: UserGuide > Coppola 2025 > Wooster 2003 > Vault. | F2.8 S73 (1ra → 3ra iteración de threshold post-Nicolás push) |
| **A36** | sec³(θ_z) scan-angle elongation puede multiplicar discrepancias factor 1-5× | F2.8 S73 (cálculo 185K vs real 695K MW = 3.74× match con θ_z=50°) |
| **A37** | VIIRS y MODIS L1B usan esquemas distintos para saturation flagging (sentinel uint16 vs quality_flag bit-2). NO extrapolar | F2.8 S73 cross-sensor audit |

## 6. PRs S72-S73 mergeados (referencia)

| # | PR | Contenido | Estado |
|---|---|---|---|
| 112-131 | S72 close (20 PRs) | Investigación F2.5-F2.6, NRT local, cap S71, AVTOD validation | Merged |
| 132 | S72 worktree canonical convention | Auto-load CLAUDE.md sessions | Merged |
| **133** | **S73 F2.8 + cleanup + dashboard** | **MODIS+VIIRS L1B-spec + BT defense + workflows archive + About modal + data inventory + tag defensivo** | Merged S73 (Claude self-merge) |

## 7. Cierre S73 — métricas finales

### Fix F2.8 saturation guard
- **10 commits** limpios en branch `claude/s73-f28-saturation-guard` (PR #133, +2737/-21 LOC, 37 archivos)
- **4 docs nuevos** F2.8 (investigation, hypothesis log, plan, archive inventory)
- **3 learnings meta** documentados (A35-A37 en CLAUDE.md)
- **33 tests nuevos** F2.8 saturation_guard (todos passing)
- **413 / 24 sk** suite total (baseline S72 = 380, +33)
- **0 regresiones operacional**
- **1 fósil pre-S41** identificado y reproc disparado post-merge (PP 2026-03-18 695,431 MW)

### Cleanup S73 (sin tocar data)
- **Branches local**: 69 → 38 (clean_gone skill)
- **Workflows activos**: 32 → 12 (20 movidos a `.github/workflows/_archive/`)
- **About modal**: actualizado S68→S73 + 3 fuentes validación + F2.8 + Di Bella reclassification
- **`applyS38Filter`**: muerto eliminado (7 ubicaciones frontend/index.html)
- **data/_*/ inventario** (`docs/F28_DATA_ARCHIVE_INVENTORY.md`): 41 subdirs clasificados
  - 27 SÍ-safe archivar (~390 MB) — diferido S74+, no es urgente
  - 11 EVALUAR (~190 MB) — valor beyond-MIROVA, conservar
  - 3 NO archivar (~121 MB) — referencias retro citadas en docs activos
- **Tag defensivo git**: `pre-s73-data-cleanup` pusheado (snapshot 696 MB recuperable)
- **2 skills nuevas** instaladas (xarray + claude-scientific-writer 4 subskills)

### Tareas paralelas ejecutadas (3 subagentes background)
1. Búsqueda skills útiles que faltaban (output: instalación selectiva de 5 skills)
2. Audit dashboard frontend (output: identificó cleanup safe + 6 bugs backlog + 14 workflows obsoletos)
3. Archive workflows obsoletos (output: 20 ymls a `_archive/`, commit `078afb6`)
4. Inventario data/_*/ clasificatorio (output: tabla 41 subdirs en `F28_DATA_ARCHIVE_INVENTORY.md`)

## 8. Errores S73 a no repetir

- **Confiar en threshold de notas Vault sin verificar PDF** (A35). 1ra iteración propuse 500K, después 450K, finalmente 500K — Coppola 2025 actualiza Wooster 2003. Verificar siempre primary source antes de citar.
- **Asumir uniformidad de schema L1B entre MODIS y VIIRS** (A37). Cada sensor tiene su propia convención de quality flags y sentinels.
- **Olvidar sec³(θ_z) scan-angle correction** al verificar matemáticamente bugs (A36). Pipeline ya lo aplica pero análisis ad-hoc también deben incluirlo.
- **Casi lancé subagente para `git rm` masivo data/_*/** sin pensar bien beyond-MIROVA value. Nicolás me paró a tiempo — frenar y razonar antes de acciones destructivas. **Regla S74+**: cualquier `git rm`/borrado masivo requiere (a) inventario clasificatorio previo, (b) tag git defensivo, (c) backup local o confirmación explícita usuario.
- **No olvidar PRs pendientes**: Claude es responsable de mergear PRs (no esperar a Nicolás). Si hay CI y está CLEAN, ejecutar merge tras verificaciones.

## 9. Cosas que aprendimos sobre el flujo de trabajo (proceso, no ciencia)

- **Verificación contra fuentes primarias** vale más que iterar sobre síntesis. Push de Nicolás "estás leyendo MD, pueden estar incompletos" → 3 iteraciones de threshold corregido. Sin ese push, hubiera cementado 450 K vs 500 K real.
- **Paralelismo con subagentes**: 4 subagentes esta sesión, todos completaron con valor. La regla "no overlap de archivos" se respetó.
- **Tag defensivo > cleanup destructivo** cuando hay duda. `git tag -a` + push es 1-comando, costo cero, recovery completo.
- **Inventario antes de borrar** es siempre el orden correcto. Saber QUÉ tenemos > tener menos.
- **`writing-plans` + `executing-plans` skills**: el plan 9-tasks bite-sized hizo la ejecución trivial. 100% recomendado para cualquier cambio >20 LOC con riesgo.
