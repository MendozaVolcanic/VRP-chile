# BLOQUE ARRANQUE S102

**Sesión previa S101 (2026-06-05).** MUY larga (11 PRs #345-352). Resolvió el frente
MODIS a nivel diagnóstico + validó el fix nadir-fijo (NO adoptado aún). Registro:
`project_s101_estado` (memoria). Design doc: `docs/superpowers/specs/2026-06-05-frente-modis-campo-difuso-design.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## §1 — PRIORIDAD: ADOPTAR nadir-fijo MODIS (A45, OK Nicolás dado en principio S101)
El fix está **validado** (run 27022484062, 11/11). Veredicto en design doc §10.6:
- Lascar nadir = **0.92× MIROVA** (era 2.79× sec³). Clava.
- Piso 0.05 → **0 FN** en los 11 (el 0.27 perdía 5 reales de Lascar).
- Residuo path D acotado: PCC 60 MW (era 342), resto ≤19.
- Filtros display casi sin cambio (con magnitud curada los artefactos no inflan).

**Causa raíz (3 fuentes coinciden)**: el sec³(θ) activo es un DRIFT; MIROVA usa nadir-fijo
(calibración S14 `experiments/21_results.json` a_pix_mode=nadir_fijo). El WOOSTER_COEFF ya
es para nadir → activar nadir-fijo NO rompe calibración, la restaura.

### Procedimiento de adopción (design doc §10.7):
1. `git tag pre-s102-nadir-fixed-modis $(git rev-parse HEAD)` + push.
2. TDD: test nadir-fijo MODIS (área uniforme 1e6 m²) + piso 0.05.
3. Flip en `pipeline/profiles/mirova_equivalent.yaml`:
   `paths.enable_nadir_fixed_pixel_area_modis: true` + `thresholds.min_vrp_mw_modis: 0.05`.
   ⚠️ A45: confirmar con Nicolás ANTES del edit (es NRT operacional, 11 vols).
4. Reproc histórico MODIS 11 vols (clonar `reproc-s101-nadir-validation.yml`, ya en main)
   → promover a `data/mirova_equivalent/` (merge con guard, patrón #345).
5. Verif pixel-level (R2 vs TIF `../mirova-tif-archive`) + R3 audit + R8 público.
6. Replicar en dashboard si hace falta; verificar que acerca los 3 sensores a MIROVA.

## §2 — Frentes posteriores (en orden)
1. **PR dashboard display** (post-nadir): #1 desglose MIROVA por sensor (3 líneas, no 1
   agregada — observación Nicolás), #3 max-real (no artefacto), #4 toggle F5' claro,
   #5 mediana vs máximo. Ver `docs/S101_DASHBOARD_AUDIT.md`. Replicar 3 vistas (S92 L5).
2. **Residuo path D** (PCC 60 MW tibio, escena ~274K, escapa cap D9): 2ª palanca del
   frente MODIS. Brainstorming + papers-first (gate atm / co-validación / cap).
3. **Scope VIIRS**: tiene el MISMO drift sec³ (calibración S14, 3 sensores nadir-fijo).
   VIIRS750 1.49× / VIIRS375 2.16× vs MIROVA. Su propio A/B + recalibración (interactúa
   con ctxpeak/F5' ya adoptados). NO mezclar con MODIS.

## §3 — Pasivos
- NRT cron ahora 11 Tier A (#350): verificar que el próximo run sale limpio (sin los 4
  failures experimentales). Chaitén puede seguir fallando ocasional por fetch NASA.
- Descargas TIF/KMZ "solo local" (#351): verificar en sitio live post-deploy.
- 76 ramas remotas claude/sNN-* stale: dejar para revisión posterior (decisión S101).

## Tags defensivos S101
`pre-s101-nrt-remove-experimental` (NRT). Para S102: crear `pre-s102-nadir-fixed-modis`.

## Worktree canónico
Raíz `VRP Chile/` en main al día.
