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
| Villarrica | 0 | 18/15 | 105/105 | 105/105 | +0 |
| Lascar | 44 | 73/73 | 32/32 | 20/20 | +0 |
| Lastarria | 16 | 39/39 | 78/78 | 61/61 | +0 |
| Tupungatito | 16 | 23/23 | 88/88 | 53/53 | +0 |

## Agregado (4 volcanes)

| Métrica | Enabled (dual-ROI on) | Disabled (control) | Δ |
|---|---:|---:|---:|
| Records summit | 153 | 150 | +3 |
| Records far | 303 | 303 | +0 |
| TP_far (far+match MIROVA) | 64 | 64 | +0 |
| FP_far (far sin match) | 239 | 239 | +0 |

## Veredicto Test 1 integrated-ROI

- **Villarrica target**: TP_summit (matches MIROVA) 0 → 0 (+0) sobre 0 refs.

**Controles (no debería disparar en pasadas sin sub-pixel real):**
- Lascar: Δ summit +0, Δ far +0, Δ FP_far +0
- Lastarria: Δ summit +0, Δ far +0, Δ FP_far +0
- Tupungatito: Δ summit +0, Δ far +0, Δ FP_far +0

**Interpretación**:
- Si Villarrica recall ≥ 0.50 con Test 1 ON, controles Δ FP_far ≤ +5% → **INTEGRAR a mirova_equivalent**.
- Si Villarrica recall sube y controles inflan FPs > 10% → trade-off, evaluar refinamiento (k_sigma más alto, restricción summit).
- Si Villarrica recall NO sube → bug en integración o algoritmo no captura en pipeline real (revisar vs POC offline).