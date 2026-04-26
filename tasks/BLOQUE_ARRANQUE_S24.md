# Bloque de arranque S24

> **Pegar este bloque al inicio de la próxima sesión** para que Claude tenga
> contexto completo en 30 segundos sin re-derivar.

---

## Estado al cierre S23 (2026-04-26)

**Branch**: `s15-dev` y `main` ambos en `origin` con últimos commits S23.
**Suite tests**: **164/164 verde** (era 119, +45 nuevos en S23).
**Issue #1 NRT**: monitorear próximos 3-5 cron NRT (~12 hs) para confirmar fix
git push + H6 retry funcionan en producción de manera consistente.

## Lo cerrado en S23 (16/18 hallazgos audit)

✅ **CRÍTICOS (4/4)**: Regla D KeyError, divergencia MODIS-VIIRS local ROI (D7),
process_modis sin tests, **Factor 42 RESUELTO** (cluster vs pixel).

✅ **ALTOS (5/7)**: haversine None safety, NRT validación, store/scan_geometry
tests, M1 expand. **Pendientes**: E33 P3.1 reproceso, VRP_TIR Aveni 2025,
Di Bella k_VIIRS A/B.

✅ **MEDIOS (5/5)**: experimental.yaml audit (no obsoleto), NTI 0.005 origen,
P95 a profile, scripts README, JSON inflación.

✅ **BAJOS (2/2)**: constantes Planck centralizadas, Pages deploy.

## Pendientes S24+ (3 altos + 1 medio)

### Prioridad 1 — E33 reproceso P3.1 dual-ROI
S15 implementó pero validación cuantitativa NUNCA ejecutada. Plan:
1. Crear profile temporal `_p3_1_disabled` con `enable_dnti_dual_roi: false`.
2. Reproceso 14 días sobre 3 Tier A (Tup/Cha/Las).
3. Forense replicable comparativa baseline vs disabled.
4. Decisión: mantener / quitar / refinar.

### Prioridad 2 — VRP_TIR Aveni 2025 POC Villarrica
Villarrica recall 0% por sub-pixel <600K. Aveni 2025 GRL Eq.9 con k_TIR=60.17
podría capturarlo. POC standalone (NO integrar al pipeline) con 5 granules.

### Prioridad 3 — Di Bella 2024 k_VIIRS A/B
Di Bella k_VIIRS=2.48×10⁷ (10× distinto a Campus k=18.0). S14 calibró contra
OSF v2.5 que NO incluye Villarrica/Tupungatito. 10 pasadas Tupungatito,
correlación con MIROVA NRT.

### Prioridad 4 — 10 papers Vault sin auditar
Coppola 2010/2013/2020/2021/2025rapid, Massimetti×3, Laiolo 2026,
ATBD VIIRS Calibration. ~30 min/paper. Diferible.

## Recordatorios al arrancar S24

1. **Leer `~memory/MEMORY.md`** (15 archivos memoria persistente).
   Especialmente: `project_s23_findings.md`, `project_s22_findings.md`,
   `project_s21_findings.md`.
2. **Aplicar `docs/SESSION_CLOSE_CHECKLIST.md`** al cierre (instalado S21).
3. **Persistencia in-vivo**: cuando descubras un hallazgo, persistilo INMEDIATAMENTE
   en memoria/docs antes de continuar (regla meta-meta S21).
4. **Skills obligatorias** según CLAUDE.md trigger table:
   - Bug/anomalía → `superpowers-systematic-debugging`
   - Antes de fix `pipeline/` >20 líneas → `writing-plans`
   - Editar `process_*.py` → `test-driven-development`
   - 2+ investigaciones independientes → `dispatching-parallel-agents`

## Decisiones consolidadas (NO reabrir)

- **Tupungatito recall ~0.40-0.50** = límite físico del MIR puro nocturno
  automatizado. NO seguir cap MAX_VENT_SIGMA_CONTRIB_K A/B (S22.2 rechazado).
- **D6 background localizado REFUTADO** empíricamente (ratio summit/global=0.81,
  glaciar afecta toda el área). NO reabrir como hipótesis.
- **MIROVA NRT no supervisa humano** (servicio gratuito sin capacidad).
  Diferencias de recall son siempre algorítmicas, NUNCA por curaduría.
- **Factor 42 = diferencia de agregación** (cluster vs pixel). NO es bug.
- **D7 local ROI threshold MODIS+VIIRS750 vs VIIRS375**: divergencia documentada,
  fix algorítmico diferido S24+ (requiere A/B vs OSF).

## Archivos críticos para consultar

- **Plan formal S23**: `docs/superpowers/plans/2026-04-26-s23-audit-followup.md`
  (22 tasks, 7 fases, plan completo con criterios).
- **Handoff S24**: `tasks/handoff_s24_2026_04_26.md` (pendientes priorizados).
- **Hipótesis log**: `docs/HYPOTHESIS_LOG.md` (H1–H_S23_*).
- **Drifts**: `docs/DRIFTS_S17.md` (D1–D7).
- **Index sesiones**: `docs/SESSION_INDEX.md` (S1–S23).
- **Glosario**: `CLAUDE.md` "Glosario obligatorio" (incluye cluster vs pixel).

## Verificación 30-segundos al arranque

```bash
# 1. Branch al día
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin && git status --branch --short
# Expected: ## s15-dev...origin/s15-dev (sin diff)

# 2. Tests verde
pytest 2>&1 | tail -3
# Expected: 164 passed (o más si NRT cron agregó tests)

# 3. NRT health
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 5 \
  --json status,conclusion,createdAt --jq '.[] | "\(.createdAt[:19]) \(.conclusion // .status)"'
# Expected: mayoría success post-S22 fix git push + H6
```

## Comandos típicos S24

```bash
# Reprocesar 14 días Tier A con profile específico
python scripts/run_pipeline.py --profile mirova_equivalent \
  --volcano Tupungatito --start 2026-04-08 --end 2026-04-22 --overwrite

# Forense replicable (cualquier Tier A)
python experiments/forense_h17_replicable.py \
  --volcano Tupungatito --start 2026-04-08 --end 2026-04-22 \
  --output-json /tmp/forense.json --output-md /tmp/forense.md

# Verify post-reproceso (M2 S19)
python scripts/verify_reproc.py
```

---

**Token usage al cierre S23**: ~99% del límite Opus 4.7 1M. Próxima sesión
arrancar fresh para tener context cache caliente.
