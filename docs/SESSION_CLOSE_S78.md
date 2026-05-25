---
title: "S78 cierre — brainstorm 7-mecanismos + Mirova-v1 parity"
session: S78
status: closed
ai_generated: true
confidence: high
explored: true
tags:
  - cierre
  - brainstorm
  - lagos
  - nti
  - bg-kernel
  - mirova-v1-parity
related:
  - docs/F60_VSROI_BRAINSTORM_S78.md
  - docs/F61_NTI_RIGOR_BRAINSTORM_S78.md
  - docs/F62_TEST1_K_SIGMA_BRAINSTORM_S78.md
  - docs/F63_CLUSTER_CONNECTIVITY_BRAINSTORM_S78.md
  - docs/F64_NTI_METHOD_BRAINSTORM_S78.md
  - docs/F65_APPROACHES_ALTERNATIVOS_S78.md
  - docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md
  - docs/F61_F63_F57_INTEGRATED_PLAN_S78.md
  - docs/MIROVA_V1_PARITY_PROPOSAL_S77.md
---

# S78 cierre — brainstorm 7-mecanismos MIROVA + Mirova-v1 parity

## Veredicto operacional

**Pipeline NRT post-S78**: estable. 507 tests passing, 24 skipped, 0 regresión.

**Dashboard post-S78**: 3 features Mirova-v1 parity mergeadas + bug raíz identificado.

## Sprint Mirova-v1 parity — features mergeadas

| PR | Feature | Esfuerzo | Impacto |
|---|---|---|---|
| [#202](https://github.com/MendozaVolcanic/VRP-chile/pull/202) | F1 mosaico panorámico 11 mini-cards | M | Alto |
| [#203](https://github.com/MendozaVolcanic/VRP-chile/pull/203) | F2 sombreado bandas MIROVA en charts | S | Alto |
| [#203](https://github.com/MendozaVolcanic/VRP-chile/pull/203) | F5 tags región CVZ/SVZ/AVZ + sort N→S | XS | Medio |
| [#201](https://github.com/MendozaVolcanic/VRP-chile/pull/201) | docs MIROVA_V1_PARITY_PROPOSAL | — | Plan |

## Brainstorm 7-mecanismos — Sumario

| # | Mecanismo | Status | Razón |
|---|---|---|---|
| F60 VSROI per-volcán | Postponed S79+ | Útil, secundario |
| **F61 NTI gate -0.85** | ❌ **INVALIDADO** | F64 demostró que destruye 98% TPs por física Planck. K1 del paper es saturación bg, NO gate detección. |
| F62 Test 1 K_sigma | Paper-literal OK | No bug |
| **F63 Cluster ranking S43** | ❌ **Rechazado post-TDD** | Trade-off legítimo Tup/Last/PP vs Copahue indistinguible sin metadata. |
| F64 NTI método real vs ours | Confirmado correcto | Sin drift cómputo |
| F65 5-10 approaches alt | Top 3 docs | Approach 5 viable, Approach 4 (TIRVolcH) definitivo |
| **F66 BG kernel local 3×3** | 🎯 **BUG RAÍZ identificado** | `compute_bg_stats` usa ring 5-25 km vs MIROVA kernel local 3×3. Fix híbrido 1 sesión, comprehensive 2-3. |

## Lección operacional clave S78

**El instinto "lagos persistentes = bug simple" es FALSO**. El brainstorm riguroso reveló:

1. F46/F47/F50/F52 S77 ya arreglaron los bugs CRÍTICOS de pipeline.
2. Lo que ves como FP "lago" en dashboard puede ser:
   - **Realidad física**: TPs con NTI<-0.85 son naturales en Andes (Planck puro, t_hot 285-295K)
   - **Drift bg ring 5-25 km vs MIROVA kernel local 3×3** — el verdadero bug raíz
3. **NO existen quick wins simples** para "lagos". Cada propuesta naive (exclude_zones, NTI gate global, F63 cluster ranking) tiene contraindicaciones documentadas vía 8 brainstorms paralelos.

## Plan S79+ (con prioridad)

### Prioridad 1: F66 híbrido — dual-bg consistency gate

**Concepto**: cuando `compute_bg_stats` (ring 5-25 km) sugiere hot pixel, también computar t_bg local (kernel 3×3) y descartar si ΔT_local < umbral. Si pixel es lago: vecinos también lago, ΔT_local≈0 → descartado. Si pixel es cráter: vecinos roca fría, ΔT_local>>0 → válido.

**Esfuerzo**: 1 sesión. A45 obligatorio + brainstorm gating + R1+R2+R3 S33 A/B.

### Prioridad 2: F66 comprehensive — migrar `compute_bg_stats` a kernel local 5×5

Reemplazar ring 5-25 km median por kernel 5×5 per-pixel. Approach MIROVA-faithful real. **Esfuerzo**: 2-3 sesiones. A/B exhaustivo.

### Prioridad 3: A5 piloto VRPTIR Aveni 2025

Cuando se de evento térmico con BT>300K en algún Tier A (verano sur). Pendiente desde S76.

### Prioridad 4: F60 VSROI polygonal

Aveni 2024 polygon-based ROI per-volcán. 5 vol con vent desplazado.

## Tags defensivos pusheados a origin

```
pre-s73-data-cleanup
pre-s75-vrptir-a2-integration
pre-s77-f46-vrp-tir-fix
pre-s77-f47-store-cluster-rescue
pre-s77-f47-distance-class-fix
pre-s77-f50-vrp-mw-cap
pre-s77-f51-fetch-probe-bypass
pre-s77-f52a-villarrica-cluster-cap
pre-s77-f52b-single-pixel-sub-mw
pre-s77-f55-profile-bypass
pre-s78-f53-test1-hot
pre-s78-f56-enable-exclude-zones  # rechazado (no MIROVA-faithful)
pre-s78-f63-cluster-rank          # rechazado (trade-off legítimo)
```

## Pendientes (no urgentes)

- F53 backlog: bug `test1_hot` unbound (1/14 granules, no bloqueante)
- F55 NRT auth deep: monkey-patch `Store.set_requests_session` (NRT funciona 28-30/30 jobs)
- Lascar reproc MODIS histórico: GH Actions Linux

## Métricas S78

- **14 PRs S78 mergeados**: #201, #202, #203, #206, #207, #208, #209, #210, #211, #212, #213, #214
- **7 docs brainstorm**: F60, F61, F62, F63, F64, F65, F66 + 1 integrado
- **3 features Mirova-v1 parity** mergeadas
- **0 cambios pipeline NRT** (todo doc + dashboard frontend)
- **8 brainstorms paralelos** rigorosos antes de cualquier cambio invasivo
- Filosofía MISSION-driven: cada fix candidato pasó por las 3 preguntas de `MISSION.md` antes de aceptar/rechazar

## Verificación

```bash
python -m pytest tests/ -q
# 507 passed, 24 skipped, 0 regresión
```

Pipeline NRT estable. Dashboard mejorado. Plan S79 con prioridad clara. Bug raíz documentado.
