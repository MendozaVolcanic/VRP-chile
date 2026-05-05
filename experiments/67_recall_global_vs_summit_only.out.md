# Recall global (vrp_mw>0) vs summit-only (Driver A) por volcán × sensor

Window: 2026-01-29 -> 2026-04-29
Refs MIROVA ALERTA_TERMICA: 531

| Volcán | Sensor | Refs | TP global | TP summit | Recall global | Recall summit | Δ pp |
|---|---|---:|---:|---:|---:|---:|---:|
| Lascar | MODIS | 61 | 37 | 5 | 60.7% | 8.2% | -52.5 ⚠️ |
| Lascar | VIIRS750 | 66 | 64 | 59 | 97.0% | 89.4% | -7.6 |
| Lascar | VIIRS375 | 97 | 82 | 83 | 84.5% | 85.6% | +1.0 |
| Lastarria | VIIRS375 | 63 | 61 | 63 | 96.8% | 100.0% | +3.2 |
| Tupungatito | VIIRS750 | 8 | 0 | 0 | 0.0% | 0.0% | +0.0 |
| Tupungatito | VIIRS375 | 60 | 32 | 33 | 53.3% | 55.0% | +1.7 |
| Villarrica | VIIRS375 | 3 | 3 | 3 | 100.0% | 100.0% | +0.0 |
| PuyehueCordonCaulle | VIIRS750 | 8 | 5 | 6 | 62.5% | 75.0% | +12.5 |
| PuyehueCordonCaulle | VIIRS375 | 50 | 42 | 49 | 84.0% | 98.0% | +14.0 |
| Copahue | VIIRS375 | 1 | 1 | 1 | 100.0% | 100.0% | +0.0 |
| NevadosDeChillan | MODIS | 1 | 0 | 0 | 0.0% | 0.0% | +0.0 |
| NevadosDeChillan | VIIRS750 | 1 | 0 | 0 | 0.0% | 0.0% | +0.0 |
| NevadosDeChillan | VIIRS375 | 2 | 0 | 0 | 0.0% | 0.0% | +0.0 |
| Chaiten | VIIRS375 | 11 | 9 | 10 | 81.8% | 90.9% | +9.1 |
| PlanchonPeteroa | VIIRS375 | 31 | 30 | 30 | 96.8% | 96.8% | +0.0 |
| Isluga | VIIRS750 | 12 | 3 | 3 | 25.0% | 25.0% | +0.0 |
| Isluga | VIIRS375 | 56 | 47 | 50 | 83.9% | 89.3% | +5.4 |

## Interpretación

- Δ pp negativo = summit-only (Driver A) pierde recall vs global. ⚠️ si <-20pp.
- TP global = nuestro vrp_mw>0 coincide temporalmente con ALERTA_TERMICA MIROVA.
- TP summit = nuestro primary_cluster está dentro inner_radius_km del cráter.
- Caso esperado: TP summit < TP global (algunos clusters lejos cráter).
- Caso peligroso: TP summit << TP global (la mayoría de detecciones lejos cráter).
