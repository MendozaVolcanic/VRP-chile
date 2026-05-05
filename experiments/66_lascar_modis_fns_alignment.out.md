# P3 Lascar — alineamiento FNs MODIS

Window: 2026-01-29 -> 2026-04-29
Refs MIROVA Lascar (todas): 1058

MIROVA MODIS Lascar 90d:
  ALERTA_TERMICA (deteccion): 61
  RUTINA (no deteccion): 269
  FALSO_POSITIVO: 1
  Total MODIS records: 331

Nuestros records Lascar MODIS 90d: 171
  con vrp_mw>0: 88
  triggered_test1: 6

## Análisis: en records nuestros con vrp_mw=0, ¿qué reportó MIROVA?

Records nuestros vrp=0 totales: 83
Categoría:
  - RUTINA: 57 (68.7%)
  - ALERTA_TERMICA: 24 (28.9%)
  - FALSO_POSITIVO: 1 (1.2%)
  - no_pareo_csv: 1 (1.2%)

## Veredicto P3 Lascar MODIS

De los records donde NOSOTROS no detectamos pero MIROVA SÍ tiene observación:
  - FN reales (MIROVA detectó, perdimos): 24 (29.3%)
  - TN alineados (MIROVA tampoco detectó): 58 (70.7%)

**PARCIAL**: mayoría TN alineados pero 29% son FNs reales — vale la pena investigar.

## Matriz confusión Lascar MODIS — métrica SUMMIT-ONLY (Driver A frontend)

|        | MIROVA ALERTA | MIROVA RUTINA | MIROVA FALSO_POSITIVO |
|---|---:|---:|---:|
| Nuestro DET | 5 | 1 | 0 |
| Nuestro NO-DET | 56 | 104 | 1 |

- TP (ambos detectan): 5
- FP (nosotros sí, MIROVA no): 1
- FN (MIROVA sí, nosotros no): 56
- TN (ambos rutina): 104
- **Recall MODIS Lascar = TP/(TP+FN) = 5/61 = 8.2%**
- **Precision MODIS Lascar = TP/(TP+FP) = 5/6 = 83.3%**
- **Accuracy = (TP+TN)/total = 109/166 = 65.7%**

### Ejemplos FNs reales (MIROVA detectó, nosotros vrp=0):

| Fecha UTC | MIROVA MW | Sensor nuestro | n_anom_pix | T1? |
|---|---:|---|---:|:--:|
| 2026-02-09 01:40 | 1.670 | MODIS_TERRA | 14 | N |
| 2026-02-09 07:20 | 1.640 | MODIS_AQUA | 52 | N |
| 2026-02-12 02:00 | 2.300 | MODIS_TERRA | 15 | N |
| 2026-02-12 07:35 | 2.960 | MODIS_AQUA | 34 | N |
| 2026-02-14 01:40 | 3.430 | MODIS_TERRA | 36 | Y |
| 2026-02-14 07:15 | 3.940 | MODIS_AQUA | 36 | N |
| 2026-02-16 01:20 | 1.040 | MODIS_TERRA | 5 | N |
| 2026-02-19 07:10 | 0.760 | MODIS_AQUA | 38 | N |
| 2026-02-22 07:25 | 2.730 | MODIS_AQUA | 54 | N |
| 2026-02-27 07:20 | 0.650 | MODIS_AQUA | 74 | N |

(Total FNs reales: 24)
