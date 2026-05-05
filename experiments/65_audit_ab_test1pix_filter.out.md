# Audit A/B test1 pixel filter

Window: 2026-01-29 -> 2026-04-29
Refs MIROVA ALERTA_TERMICA: 531

================================================================================

## Profile: filter_ON

| Volcán | Refs | TPs | Recall % | Ratio med | mediana MIROVA MW | mediana nuestro MW | n_T1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 14.47
| Copahue | 1 | 1 | 100.0 | 3.18
| Isluga | 68 | 53 | 77.9 | 1.05
| Lascar | 224 | 146 | 65.2 | 1.22
| Lastarria | 63 | 63 | 100.0 | 6.51

| PlanchonPeteroa | 31 | 27 | 87.1 | 2.53
| PuyehueCordonCaulle | 58 | 55 | 94.8 | 11.91
| Tupungatito | 68 | 33 | 48.5 | 0.57
| Villarrica | 3 | 3 | 100.0 | 2.21

**GLOBAL — Recall: 73.6% (391/531). Ratio mediano: 1.66x (n=391).**

## Profile: filter_OFF

| Volcán | Refs | TPs | Recall % | Ratio med | mediana MIROVA MW | mediana nuestro MW | n_T1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 18.29
| Copahue | 1 | 1 | 100.0 | 3.18
| Isluga | 68 | 53 | 77.9 | 1.07
| Lascar | 224 | 147 | 65.6 | 1.26
| Lastarria | 63 | 63 | 100.0 | 18.49

| PlanchonPeteroa | 31 | 30 | 96.8 | 16.03
| PuyehueCordonCaulle | 58 | 55 | 94.8 | 12.10
| Tupungatito | 68 | 33 | 48.5 | 0.71
| Villarrica | 3 | 3 | 100.0 | 64.92

**GLOBAL — Recall: 74.4% (395/531). Ratio mediano: 2.52x (n=395).**

================================================================================

## Comparación final A vs B

| Métrica | filter_OFF (control) | filter_ON (experimental) | Δ |
|---|---:|---:|---:|
| Recall global | 74.4% | 73.6% | -0.8 pp |
| Ratio mediano | 2.52x | 1.66x | -34% |

## Veredicto

- Recall ≥83.5%? **NO** (73.6%)
- Ratio ≤1.5x?   **NO** (1.66x)

**NO APROBADO** — analizar por qué falla criterio. Driver B requiere refinamiento.
