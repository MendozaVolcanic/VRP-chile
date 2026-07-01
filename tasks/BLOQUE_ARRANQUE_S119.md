# BLOQUE ARRANQUE S119 — AUDITORÍA INTEGRAL post-S118

**S118 (2026-06-28)** ejecutó: (A) A/B real gates intra-radio C2 → **FLIP OFF operacional**
(PR #474, tag `pre-s118-c2-flip`, evidencia `docs/AUDIT_S118_C2_GATES_AB.md`: 0 robos de
cluster en 214 noches focales, run 28312968093 180/180) + (B) vista experimental
**Beyond MIROVA** (`frontend/experimental/beyond-mirova.html`, pestañas 2a zonas geo ·
1 fidelidad · 2b Eq.16 placeholder). PRs #470-474. Suite 797. Memoria: [project_s118_estado].

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## §1 — MISIÓN S119: auditoría integral (pedida explícitamente por Nicolás)

**Plan detallado completo (ejecutar tarea por tarea):**
[`docs/superpowers/plans/2026-06-28-s119-auditoria-integral.md`](../docs/superpowers/plans/2026-06-28-s119-auditoria-integral.md)

Orden vinculante:
1. **Eje 1 PRIMERO (bloqueante)**: verificación post-flip C2 en NRT/data/dashboard.
   El NRT corre con gates OFF desde 2026-06-28 ~20:00 UTC — a la fecha de S119 ya hay
   días de data nueva. Si hay regresión sistemática → **rollback**
   (`git checkout pre-s118-c2-flip -- pipeline/profiles/mirova_equivalent.yaml` +
   revertir guards de intención) y reportar ANTES de seguir.
2. Ejes 2/4/6 en subagentes paralelos read-only (paridad clon con ground truth
   refrescado A17 · integridad bases de datos · cabos sueltos S118).
3. Eje 3 con Nicolás en navegador real: validar beyond-mirova.html (nunca se vio con
   viewport real) + **afinar zonas 2a por volcán** (su criterio geológico) + persistir.
4. Eje 5 (docs vivos): DIVERGENCES → gates RESUELTO S118; MISSION tabla anti-patrones
   → "Removido S118"; regla A85 candidata; HYPOTHESIS_LOG.
5. Eje 7 al cierre: priorizar avance con Nicolás (clon: backfill VIIRS / GAP #A / NEW-8;
   beyond: Panel 2b Eq.16 reproc `_s99_test1_eq16` Villarrica / zonas 2a / OCR dist).

## Cabos sueltos S118 que el plan cubre (no perder)
- Mecanismo pathd_off VRP-difiere-con-píxeles-idénticos sin explicar (Eje 6.1).
- Cobertura A/B: 6 chunks/vol focales dropped, nevados control débil (Eje 2.5 — honestidad).
- beyond-mirova.html sin link desde experimental/index.html (Eje 3.5).
- `experiments/_s118_c2ab/_artifacts/` 86 MB local (Eje 4.2, pedir OK para borrar).
- Archivar `reproc-s118-c2-gates-ab.yml` (Eje 4.3).
- R2 nuevo sobre fecha post-flip cuando haya TIF comparable (Eje 6.5).

## 🚫 NO reabrir (anti-A8) — sin cambios
far→summit MODIS/D11/A69-como-bug (A82) · re-ancla ctx_cluster (A84) · inner PCC ·
Parte C NdC (A77, otro repo) · fondo-local-NTI (S105) · per-régimen C2 (MISSION l.77).

## Reglas vinculantes
A45 (tag+OK antes de pipeline; el flip S118 ya lo cumplió — NO tocar más pipeline sin
nuevo ciclo) · A61/A62 · A48/A50 · A10 (`pc.vrp_mw`) · S91 (números de scripts) ·
explicar como geólogo · preview headless viewport-0 (verificar por eval, no screenshot).

## Estado operacional al cierre S118
NRT cada 2h **con gates OFF** (primer cambio de pipeline-config desde S103 nadir).
Guard A46 LIVE. Suite **797 passed**. FICHA v1.2. Recall pre-flip: VIIRS375 98.4% /
V750 85% / MODIS-cráter 100% (re-medir en Eje 2 post-flip).
