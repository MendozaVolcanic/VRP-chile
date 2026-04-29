# A/B MIROVA literal puro — Delta Report (S27)

Ventana: 2026-04-12 → 2026-04-25 (14d).

| Volcán | Refs | TP lit/leg | FN lit/leg | FP_far lit/leg | Recall lit/leg | Ratio med lit/leg |
|---|---:|---|---|---|---|---|
| Lascar | 44 | 34/42 | 10/2 | 22/20 | 0.77/0.95 | 1.35/166.27 |
| Lastarria | 16 | 4/16 | 12/0 | 68/66 | 0.25/1.00 | 6.07/64.45 |
| Tupungatito | 16 | 7/8 | 9/8 | 36/31 | 0.44/0.50 | 1.07/0.93 |
| Villarrica | 0 | 0/0 | 0/0 | 39/54 | —/— | —/— |

## Agregado

| Métrica | MIROVA Literal | Legacy (parches) | Δ |
|---|---:|---:|---:|
| TP | 45 | 66 | -21 |
| FN | 31 | 10 | +21 |
| FP_far(>1MW) | 165 | 171 | -6 |
| Recall | 0.592 | 0.868 | -0.276 |
| Ratio mediano | 1.35 | 69.74 | -68.39 |

## Veredicto

- FAIL Recall cae < 10 pp -> Δ = -27.6 pp.
- FAIL FP_far cae ≥ 40% -> caída = +3.5%.
- PASS Ratio mediano ≤ 30× -> ratio literal = 1.3×.

**NO APROBADO** -> persistir hallazgo, NO mergear.