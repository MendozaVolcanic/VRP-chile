# AUDIT_S118 — A/B gates intra-radio C2: robo de cluster espacial

Criterio pre-registrado (A66): gate→OFF si NO hay robo de cluster en focales en
noches MIROVA-confirmadas; gate→ON uniforme si lo hay. Re-anclado al vent (A61).
Generado por experiments/_s118_c2ab/analyze.py (S91: números del script).

## _c2ab_pathd_off

| Volcán | régimen | noches MIROVA | robos de cluster | veredicto local |
|---|---|---|---|---|
| Lascar | focal | 55 | 0 | ok |
| Lastarria | focal | 46 | 0 | ok |
| Isluga | focal | 44 | 0 | ok |
| PlanchonPeteroa | focal | 30 | 0 | ok |
| PuyehueCordonCaulle | focal | 39 | 0 | ok |
| Llaima | nevado | 1 | 0 | — |
| Copahue | nevado | 1 | 0 | — |
| Villarrica | nevado | 11 | 0 | — |
| NevadosDeChillan | nevado | 6 | 0 | — |
| Tupungatito | nevado | 43 | 0 | — |
| Chaiten | nevado | 14 | 0 | — |

**Veredicto _c2ab_pathd_off: OFF (clon-literal — sin robo en focales)** (robos en focales = 0).

*Magnitud (secundaria):* ratio mediano per-vol = 1.0 · cola inflada >1.5× = **19/3544** records (0.5%), de esos 16 son `far` (el frontend ya los filtra) y 9 MIROVA-confirmados. Peores casos summit en `results.json > magnitude`.

## _c2ab_2pass_off

| Volcán | régimen | noches MIROVA | robos de cluster | veredicto local |
|---|---|---|---|---|
| Lascar | focal | 55 | 0 | ok |
| Lastarria | focal | 46 | 0 | ok |
| Isluga | focal | 44 | 0 | ok |
| PlanchonPeteroa | focal | 30 | 0 | ok |
| PuyehueCordonCaulle | focal | 39 | 0 | ok |
| Llaima | nevado | 1 | 0 | — |
| Copahue | nevado | 1 | 0 | — |
| Villarrica | nevado | 11 | 0 | — |
| NevadosDeChillan | nevado | 6 | 0 | — |
| Tupungatito | nevado | 43 | 0 | — |
| Chaiten | nevado | 14 | 0 | — |

**Veredicto _c2ab_2pass_off: OFF (clon-literal — sin robo en focales)** (robos en focales = 0).

*Magnitud (secundaria):* ratio mediano per-vol = 1.0 · cola inflada >1.5× = **20/3544** records (0.6%), de esos 19 son `far` (el frontend ya los filtra) y 8 MIROVA-confirmados. Peores casos summit en `results.json > magnitude`.

## _c2ab_both_off

| Volcán | régimen | noches MIROVA | robos de cluster | veredicto local |
|---|---|---|---|---|
| Lascar | focal | 55 | 0 | ok |
| Lastarria | focal | 46 | 0 | ok |
| Isluga | focal | 44 | 0 | ok |
| PlanchonPeteroa | focal | 30 | 0 | ok |
| PuyehueCordonCaulle | focal | 39 | 0 | ok |
| Llaima | nevado | 1 | 0 | — |
| Copahue | nevado | 1 | 0 | — |
| Villarrica | nevado | 11 | 0 | — |
| NevadosDeChillan | nevado | 6 | 0 | — |
| Tupungatito | nevado | 43 | 0 | — |
| Chaiten | nevado | 14 | 0 | — |

**Veredicto _c2ab_both_off: OFF (clon-literal — sin robo en focales)** (robos en focales = 0).

*Magnitud (secundaria):* ratio mediano per-vol = 1.0 · cola inflada >1.5× = **46/3544** records (1.3%), de esos 42 son `far` (el frontend ya los filtra) y 19 MIROVA-confirmados. Peores casos summit en `results.json > magnitude`.

## Cola inflada visible (summit) — brazo both_off

| Volcán | fecha | sensor | base MW | off MW | MIROVA conf |
|---|---|---|---|---|---|
| Lastarria | 2026-04-18 | MODIS_TERRA | 1.192 | 2.245 | sí |
| PuyehueCordonCaulle | 2026-01-28 | MODIS_AQUA | 0.792 | 56.459 | no |
| Villarrica | 2026-05-10 | MODIS_AQUA | 1.843 | 2.827 | no |
| Chaiten | 2026-01-22 | MODIS_AQUA | 1.615 | 2.877 | no |
