---
title: "Auditoría pre-reproc S77 — ADDENDUM v2 (corrección sensor bucket)"
session: S77
status: closed
ai_generated: true
confidence: high
explored: true
tags:
  - audit
  - sensor-bucket-fix
  - f52
related:
  - docs/AUDITORIA_PRE_REPROC_S77.md
  - PR #196
---

# Addendum v2 — corrección sensor bucket del audit PR #196

## Bug original (v1)

El subagente del audit comprehensivo PR #196 escribió en su script
`experiments/148_audit_pre_reproc/audit_pre_reproc.py`:

```python
def sensor_bucket_ours(sensor: str) -> str:
    if "375" in s or "VJ102IMG" in s or "VNP02IMG" in s or "_I" in s:
        return "VIIRS375"
    if "VIIRS" in s or "VJ102MOD" in s or "VNP02MOD" in s or "_M" in s:
        return "VIIRS"
```

Pero la convención real en `data/mirova_equivalent/*.json`:

| Sensor real | I-band 375m / M-band 750m |
|---|---|
| `VIIRS_SNPP`, `VIIRS_NOAA20`, `VIIRS_NOAA21` | **I-band 375m** |
| `VIIRS_SNPP_750`, `VIIRS_NOAA20_750`, `VIIRS_NOAA21_750` | **M-band 750m** |
| `MODIS_TERRA`, `MODIS_AQUA` | MODIS |

El regex v1 NO contiene "375" en `VIIRS_SNPP`, NO contiene "_I" en
ningún sensor real → cae a `"VIIRS" in s` y los I-band 375m se
clasificaron erróneamente como **M-band 750m**.

**Consecuencia v1**: el audit dijo "MIROVA emite 78% alertas en VIIRS375
bucket que nuestro pipeline no procesa". FALSO. **Sí procesamos** I-band
en VIIRS_SNPP/NOAA20/NOAA21. El audit no podía hacer matches en ese
bucket porque clasificaba mal nuestros sensores.

## Fix v2

```python
def sensor_bucket_ours_v2(sensor: str) -> str:
    if not sensor: return "UNKNOWN"
    s = sensor.upper()
    if s.startswith("MODIS_") or s == "MODIS": return "MODIS"
    if s.endswith("_750"): return "VIIRS"           # M-band 750m
    if s.startswith("VIIRS_"): return "VIIRS375"    # I-band 375m
    return "UNKNOWN"
```

Re-ejecutado el audit. Ver `experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py`
+ `master_table_v2.csv`.

## Resultados corregidos (ventana 30d hasta 2026-05-24)

Mejor bucket por volcán (mayor N matched):

| Volcán | Bucket | N matched | Ratio mediano | Veredicto v2 |
|---|---|---|---|---|
| Lascar | VIIRS375 | 83 | **0.78** | ✅ OK |
| Lastarria | VIIRS375 | 71 | **1.08** | ✅ OK |
| Llaima | VIIRS375 | 17 | **0.92** | ✅ OK |
| Isluga | VIIRS375 | 77 | **1.11** | ✅ OK |
| Copahue | VIIRS375 | 13 | **0.57** | ✅ OK |
| PCC | VIIRS375 | 76 | **0.59** | ✅ OK (F47 fix activo) |
| Chaitén | VIIRS375 | 28 | **2.33** | ⚠️ Over moderado |
| Villarrica | VIIRS375 | 17 | **4.81** | ⚠️ Over (pre-F52-A en records hist.) |
| PlanchónPeteroa | VIIRS375 | 70 | **2.55** | ⚠️ Over (pre-F52-B) |
| Tupungatito | VIIRS375 | 67 | **13.01** | 🔴 OVER (pre-F52-B) |
| NdC | (sin matches MIROVA fresh) | — | — | sin baseline |

## Interpretación física

- **6 volcanes calibrados** (Lascar, Lastarria, Llaima, Isluga, Copahue, PCC):
  ratio 0.5-1.2× en banda esperada vs MIROVA NRT fresh.
- **3 volcanes en banda over moderado** (Chaitén, PP, Villarrica): 2-5×.
  Los fixes F52-A (Villarrica cluster cap) y F52-B (single-pixel sub-MW
  drift T1.5 para Chaitén+PP+Tupungatito) ya están mergeados a main hoy
  y NRT cron post-2026-05-24 aplicará. Records históricos siguen
  inflados hasta reproc.
- **Tupungatito 13×** sigue siendo el peor case. F52-B esperado lo lleva
  a 1-3×.
- **NdC sin baseline**: 0 records MIROVA non-NULO ventana 30d, 1 record
  nuestro. F47 fix esperado reactivará detecciones (recall 0.20 → 0.60+
  esperado post-reproc).

## Decisión reproc

Con el audit v2 corregido, el reproc histórico es **menos urgente** de
lo que sugería v1:

- **6 Tier A ya están bien calibrados** sin necesidad de reproc.
- **3 con over moderado**: post-NRT-cron-suficiente (1-2 semanas) los
  fixes F52-A/B se aplicarán naturalmente sobre records nuevos. Reproc
  histórico opcional para "limpiar" backlog visual del dashboard.
- **1 grave (Tupungatito)** + 1 sin data (NdC): worth reproc dedicado
  (2 vol × 30d ≈ 1-2 h máquina, manejable).

## Recomendación operacional

**Opción A — Reproc focalizado** (recomendado, ~2h máquina):
```bash
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Tupungatito --start 2026-04-24 --end 2026-05-24
python scripts/run_pipeline.py --profile mirova_equivalent --volcano NevadosDeChillan --start 2026-04-24 --end 2026-05-24
# Después verificar ratios post-reproc con audit_pre_reproc_v2.py
```

**Opción B — Esperar NRT acumular 1-2 semanas + re-audit**: los fixes
se acumulan en records nuevos. Próximo audit verá ratios mediano
sobre records ya con F52-A/B aplicados. Cero esfuerzo, pero histórico
visual del dashboard tarda en limpiarse.

**NO recomendado**: reproc completo 11 Tier A × 30d (8-15 h) — ya no
es necesario, mayoría calibrados.

## Notas sobre el subagente

Bug bite-sized del subagente, no del pipeline. Datos crudos del v1
(CSVs en `experiments/148_audit_pre_reproc/`) siguen siendo válidos
para conteos brutos por sensor; solo la interpretación del bucketing
estaba mal. Conclusión #1 del PR #196 ("pipeline no procesa VIIRS375")
queda **REFUTADA** por este addendum.
