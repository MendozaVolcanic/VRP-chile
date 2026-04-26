# A/B P3.1 dual-ROI — Delta Report (S24)

Ventana: 2026-04-12 → 2026-04-25 (14d). Tolerancia match ±60 min.

Cada record con detección física se clasifica por `distance_class`:
- **summit**: ROI inner — P3.1 NO lo afecta (filtra solo SCENE).
- **far**: ROI scene — P3.1 lo reduce con threshold 3.3× más estricto.
  - **far+match**: detectado por nosotros y por MIROVA (señal real lejana, raro).
  - **far−match**: solo nosotros (FP lejano — lo que P3.1 debería matar).

## Por volcán

| Volcán | n_refs | summit en/dis | far en/dis | far−match (FP_far) en/dis | Δ FP_far |
|---|---:|---|---|---|---:|
| Lascar | 44 | 73/73 | 32/55 | 20/26 | -6 |
| Lastarria | 16 | 39/39 | 78/92 | 61/75 | -14 |
| Tupungatito | 16 | 23/23 | 88/121 | 53/81 | -28 |
| Chaiten | 0 | 52/50 | 55/100 | 55/100 | -45 |

## Agregado (4 volcanes)

| Métrica | Enabled (dual-ROI on) | Disabled (control) | Δ |
|---|---:|---:|---:|
| Records summit | 187 | 185 | +2 |
| Records far | 253 | 368 | -115 |
| TP_far (far+match MIROVA) | 64 | 86 | -22 |
| FP_far (far sin match) | 189 | 282 | -93 |

## Veredicto P3.1 dual-ROI

- **FP_far reduction**: 282 → 189 (+33.0% vs control).
- **⚠ Summit cambió**: 185 → 187 (no esperado; revisar implementación).

**Interpretación**:
- Si Δ FP_far ≪ 0 y summit estable → P3.1 cumple su rol diseñado: filtra ruido scene sin tocar señal summit. **MANTENER**.
- Si Δ FP_far ≈ 0 → P3.1 no aporta señal en la ventana. **EVALUAR si la ventana es informativa** (más volcanes / más días).
- Si Δ FP_far > 0 (enabled tiene MÁS FP) → bug. **INVESTIGAR**.