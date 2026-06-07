# BLOQUE ARRANQUE S103

**Sesión previa S102 (2026-06-06/07).** MUY larga, 11 PRs (#354-364). Cerró el frente
MODIS (nadir-fijo adoptado+promovido), mejoró el display, **resolvió el incidente NRT**
(cron fallaba ~50%), y dejó el frente VIIRS **decidido y listo-para-disparar**.
Registro completo: `project_s102_estado` (memoria). Docs:
`docs/S102_NADIR_PROMOTE_RESULTS.md`, `docs/superpowers/specs/2026-06-05-frente-modis-*`,
`docs/superpowers/specs/2026-06-06-viirs-nadir-ctxpeak-interaction-design.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat ../../[ruta]/memory/project_s102_estado.md   # o leer la memoria del proyecto
```
Worktree canónico: raíz `VRP Chile/` en `main`.

## ✅ Cerrado en S102 (en producción)
- **Nadir-fijo MODIS** adoptado (#354), reprocesado 4 meses, promovido (#356), R8 live OK.
  PCC 342→60MW, Tupun 133→0, Lascar 0.92→1.38× (n=62), 0 FN. Tag `pre-s102-nadir-fixed-modis`.
- **Display Diario** (#358 desglose MIROVA por sensor, #359 mediana + toggle aclarado).
- **NRT RESUELTO** (#362 instrumentación + #364 circuit-breaker). Verificado end-to-end
  (run 27089474584: 11/11, 2 CONNFAIL + 26 SKIP, LANCE caído tolerado con gracia).
  Tag `pre-s102-nrt-download-circuit-breaker`.

## §1 — PRIORIDAD: ADOPTAR nadir-fijo VIIRS (decidido S102, A45 — pedir OK Nicolás)
**Veredicto firme** (A/B 3-way run 27069747395 + 27079762282, design doc 2026-06-06 §5bis):
adoptar nadir VIIRS + **MANTENER ctxpeak** (hipótesis "ctxpeak=parche sec³" REFUTADA;
nadir-SIN-ctx da 2.43× peor). Global VIIRS375 1.95→**0.78×**, VIIRS750 1.63→0.80×, **0 FN
VIIRS375**. Undershoot leve Lascar 0.66 (área nadir, dentro de banda 0.7-1.4). Calibración
S14 confirma a_pix_mode=nadir_fijo los 2 sensores VIIRS. Reproc YA confiable (fix NRT).

**Procedimiento (espejo exacto de MODIS #354/#355/#356, A45 — OK Nicolás antes del flip):**
1. `git tag pre-s103-nadir-fixed-viirs $(git rev-parse HEAD)` + push.
2. TDD anti-revert en `tests/test_gr2_profile_invariants.py`: agregar
   `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS: True` a EXPECTED_OPERATIONAL_FLAGS + al mapeo
   const_to_yaml; verificar ctxpeak sigue True + pisos VIIRS intactos (0.02/0.15).
3. Flip en `pipeline/profiles/mirova_equivalent.yaml` (sección paths):
   `enable_nadir_fixed_pixel_area_viirs: true`. ⚠️ NO tocar ctxpeak ni pisos VIIRS.
   ⚠️ NO confundir con MODIS (ya está ON).
4. Reproc histórico: clonar `.github/workflows/reproc-s102-nadir-promote.yml` → perfil
   nuevo `_s103_viirs_nadir_promote.yaml` (extends mirova_equivalent, subdir aislado;
   nadir VIIRS heredado del flip). 11 vols × 2 chunks (2026-01-29..03-31, 04-01..06-04).
5. Promover SOLO records VIIRS (375+750) con guard anti-underfetch, MODIS intacto
   (espejo de `merge_promote_nadir.py` pero filtrando VIIRS). Verificar VIIRS750 byte-...
   (al revés que MODIS: ahora MODIS debe quedar byte-idéntico).
6. R2 (TIF) + R3 (`analyze_viirs_3way.py` o nuevo audit ratio) + R8 público + preview 3 vistas.
**Nota A53**: S102 cerró en 11 PRs (cap soft 12). VIIRS son ~3 PRs → arrancar fresco aquí.

## §2 — Frente path D (2ª palanca, scopeado S102 por agente; brainstorming + A45)
DOS sub-frentes distintos (NO mezclar):
- **VIIRS750 glaciar** (Tupun/PP/Isluga ~8-16× vs MIROVA, 56-99 recs Test1 c/u): dispara por
  **Test1 sub-píxel** (NO path D contextual) → cap D9 no aplica. **Mismo mecanismo que ctxpeak
  curó en VIIRS375 (S100)**. Recomendación agente: **portar ctxpeak a VIIRS750** (Opción B,
  uniforme-por-sensor MISSION Q1, A55-safe, keep-peak preserva cat-b).
  ⚠️ A48: VERIFICAR primero con datos que VIIRS750 dispara por Test1 (no contextual) antes
  de implementar — el agente pudo inventar heurística. `grep`/Counter sobre triggered_test1.
  ⚠️ Interactúa con la adopción nadir VIIRS §1 (hacer §1 primero, re-medir VIIRS750 después).
- **PCC MODIS** (2 recs 27+60MW, contextual-only, t_bg 270-272K escapa cap D9 umbral 270):
  recalibrar `path_d_only_cap_tbg_max_k` 270→273K (verificar vs TIF R2 que no enmascara
  magnitud real) O dejar documentado cat-b (=warm-scene S91). Opción C (gate intra-radio)
  VETADA A55. Detalle: respuesta agente en project_s102_estado.

## §3 — Limpieza carpetas (~6 GB, auditada S102, esperando OK)
`git worktree remove` de los hermanos VRP-Chile-* (commits/branches sobreviven en .git):
- 0 commits sin mergear (seguros): `VRP-Chile-s70`, `VRP-Chile-s74-frontend-plan`,
  nested `funny-mendeleev`.
- nested `nostalgic-aryabhata` (40 commits, Nicolás declaró descartable S81, tag existe),
  nested `hardcore-gauss` (1 commit, revisar).
- ⚠️ `VRP-Chile-s79-f66` (10 commits, F66 Tasks 7-15) y `VRP-Chile-s80-consolidation`
  (s81-vrp-tir-gate, 6 commits, S82): trabajo sin mergear, DECIDIR destino antes.
- KEEP: `VRP Chile/` (main) + `mirova-tif-archive` (4.5GB datos). Tag defensivo A38 antes.

## §4 — Pasivos / monitoreo
- **NRT**: el cron ahora tolera LANCE caído (11/11). Verificar que sigue verde los próximos
  días (`gh run list --workflow=nrt.yml`). Si LANCE se recupera, las SNPP-NRT vuelven solas.
  Los markers `[diag]` siguen activos (útiles; quitar en alguna sesión futura si molestan).
- Dashboard estaba clavado en 2026-06-04 por el incidente; con el fix debería avanzar.
- 3 vols del 3er brazo VIIRS A/B (Lastarria/NdC/Copahue) quedaron sin medir (colgados por el
  bug NRT) — se re-miden solos al reprocesar VIIRS en §1. No bloquean (veredicto 8/11 decisivo).
- Artifacts de experimentos en `experiments/_s99_audit/_*_art/` son locales (no commitear).

## Tags defensivos S102
`pre-s102-nadir-fixed-modis`, `pre-s102-nrt-diag-instrumentation`,
`pre-s102-nrt-download-circuit-breaker`. Para S103: crear `pre-s103-nadir-fixed-viirs`.

---
## Prompt copy-paste para S103
```
Sesión S103 — VRP Chile. Sincronizá (raíz "VRP Chile/" en main: git fetch origin --prune
&& git pull --ff-only) y leé tasks/BLOQUE_ARRANQUE_S103.md + project_s102_estado (memoria)
+ docs/superpowers/specs/2026-06-06-viirs-nadir-ctxpeak-interaction-design.md §5bis.

PRIORIDAD §1: ADOPTAR nadir-fijo VIIRS (decidido S102: adoptar + MANTENER ctxpeak, 0.78×
global, 0 FN). Es A45 — pedíme OK explícito antes de tocar mirova_equivalent.yaml.
Espejo exacto de MODIS: tag → TDD anti-revert → flip enable_nadir_fixed_pixel_area_viirs
→ reproc histórico 11 vols (ya confiable, fix NRT) → promover SOLO VIIRS (MODIS intacto)
→ R2/R3/R8. NO tocar ctxpeak ni pisos VIIRS. NO confundir con MODIS (ya ON).

Después: §2 path D (portar ctxpeak a VIIRS750 —verificar A48 primero— + PCC MODIS cap D9),
§3 limpieza carpetas (~6GB, decidir F66/S82 antes).

Recordá: explicame como geólogo; si dudás, refutá con datos antes de reafirmar (A62);
no mezcles MODIS con VIIRS.
```
