# Audit Phase 2 vs Phase 1 — REFUTADO

A/B test S33 Driver B Phase 2 (run 25401379853, 11 Tier A 90d).

## Resultado: catastrófico

| Métrica | Phase 1 (operacional) | Phase 2 | Δ |
|---|---:|---:|---:|
| **Recall global** | **73.6%** | **10.5%** | **−63.1pp** |
| Ratio mediano | 1.66× | 1.23× | −25% |

| Volcán | Phase 1 recall | Phase 2 recall |
|---|---:|---:|
| Lascar | 65.2% | 21.4% |
| Lastarria | 100% | **0.0%** |
| Tupungatito | 48.5% | **0.0%** |
| Villarrica | 100% | **0.0%** |
| PCC | 94.8% | 8.6% |
| Chaiten | 90.9% | **0.0%** |
| Planchón | 87.1% | **0.0%** |
| Isluga | 77.9% | 4.4% |
| Copahue | 100% | 0% |
| NdC | 0% | 0% |

## Causa raíz (predicha en investigación Tupungatito)

El filtro `dual_roi_bt_threshold` 5σ summit aplicado a la **mask final combinada**
(post-OR de todos los paths) elimina pixels reales en volcanes con
`std_bg` heterogéneo:

- Tupungatito: σ_bg=4.75K → threshold 5σ summit = 23.8K
- Pixel cráter ΔT=15.7K real → NO pasa threshold → eliminado

Phase 2 NO distingue entre pixels que vienen de paths con threshold
local (Test 1 dispara con su trigger integrado) y pixels marginales del
Path D dNTI. Los corta a todos por igual.

## Veredicto

**HIPÓTESIS REFUTADA**. Phase 2 NO debe adoptarse como está.

## Implicaciones

1. **Driver B Phase 1** sigue siendo el único fix válido (Test 1 only).
2. **Chaiten 14.5×, PCC 11.9×** residual queda como pendiente — no puede
   resolverse con filtro N·σ universal porque destroza volcanes con
   bg heterogéneo.
3. **Driver B Phase 2 alternativas** a investigar S33+:
   - Filtro 5σ solo cuando Path D dNTI domina el cluster (>50% pixels
     del cluster vienen de Path D).
   - Filtro variable por volcán según `std_bg` típico (caps adaptativos).
   - Cap de magnitud (no de pixels): si `pc_vrp > N × MIROVA típico`,
     scale down post-hoc.
4. **D4 fix Tupungatito (L_bg global)** sigue siendo dirección correcta
   — es la OPUESTA a Phase 2 (más permisivo, no más estricto).

## Profile mirova_equivalent_phase2.yaml

NO usar. Mantener en repo como documentación negativa. Default
`enable_final_pixel_filter` permanece OFF en operacional.
