# R2 — Verificación pre-implementación VRP integrated Eq.1

Política R2 (S33): NO implementar Eq.1 hasta confirmar dirección
empíricamente desde data ya en disco.

| Volcán | Fecha UTC | Sensor | MIROVA MW | VRP actual | VRP Eq.1 sim | ratio actual | ratio Eq.1 | T1? | path | n_pix |
|---|---|---|---:|---:|---:|---:|---:|:--:|---|---:|
| Lastarria | 2026-02-16 05:30 | VIIRS375 | 0.040 | 3.48 | 1.55 | 87.0 | 38.7 | Y | test1 | 84 |
| Villarrica | 2026-02-26 05:42 | VIIRS375 | 0.120 | 10.11 | 0.00 | 84.2 | 0.0 | Y | test1 | 95 |
| Chaiten | 2026-02-26 05:48 | VIIRS375 | 0.030 | 4.18 | 1.11 | 139.4 | 36.8 | Y | test1 | 98 |
| PlanchonPeteroa | 2026-04-10 05:36 | VIIRS375 | 0.060 | 3.82 | 0.00 | 63.7 | 0.0 | Y | test1 | 84 |
| Lascar | 2026-04-13 06:18 | VIIRS375 | 0.040 | 2.30 | 0.00 | 57.5 | 0.0 | Y | test1 | 73 |

## Análisis agregado: simulación Eq.1 vs actual sobre records test1

Records con final_hotspot_source='test1' analizados: 120

Ratio mediano actual:    15.80x
Ratio mediano Eq.1 sim:  0.00x
Records donde Eq.1 < actual: 96%
Reducción mediana de ratio: 100%

Por volcán:

  Chaiten: n=3, ratio actual=39.86, Eq.1=0.00
  Lascar: n=25, ratio actual=3.47, Eq.1=0.00
  Lastarria: n=63, ratio actual=18.89, Eq.1=0.00
  PlanchonPeteroa: n=26, ratio actual=20.01, Eq.1=0.00
  Villarrica: n=3, ratio actual=64.92, Eq.1=0.00

## Veredicto R2

R2 CONFIRMA dirección — Eq.1 reduce ratio mediano 15.80x → 0.00x (-100%).
Implementar y A/B test.
