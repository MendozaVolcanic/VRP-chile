# A/B dual-ROI BT — Delta Report (S26)

Ventana: 2026-04-12 → 2026-04-25 (14d). Tolerancia ±60 min.

## Por volcán

| Volcán | Refs | TP en/dis | FN en/dis | FP_far en/dis | Recall en/dis | Ratio med en/dis |
|---|---:|---|---|---|---|---|
| Villarrica | 0 | 0/0 | 0/0 | 53/54 | nan/nan | nan/nan |
| Lascar | 44 | 42/42 | 2/2 | 20/20 | 0.95/0.95 | 166.27/166.27 |
| Lastarria | 16 | 16/16 | 0/0 | 62/66 | 1.00/1.00 | 45.93/64.45 |
| Tupungatito | 16 | 8/8 | 8/8 | 31/31 | 0.50/0.50 | 0.93/0.93 |

## Agregado

| Métrica | Enabled (dual-ROI BT) | Disabled (control 3σ) | Δ |
|---|---:|---:|---:|
| TP | 66 | 66 | +0 |
| FN | 10 | 10 | +0 |
| FP_far (vrp>1MW sin match) | 166 | 171 | -5 |
| Recall | 0.868 | 0.868 | +0.000 |
| Ratio mediano VRP | 64.56 | 69.74 | -5.18 |

## Veredicto criterios plan 2026-04-27

- ✓ **Recall agregado cae < 5 pp** → Δ = +0.0 pp.
- ✗ **FP_far cae ≥ 40%** → caída = +2.9%.
- ✗ **Ratio mediano ≤ 30×** → ratio enabled = 64.6×.

**RESULTADO: NO APROBADO** → no mergear. Persistir hallazgo y revisar plan.