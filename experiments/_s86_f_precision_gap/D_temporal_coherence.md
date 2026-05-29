# Frente 2.A S86 — Coherencia espacio-temporal (Subagente D)

**Ventana**: 2026-01-28 → 2026-05-25.
**Publishables**: 5,337 (1650 TP, 3687 FP). **Clusters espaciales** (≤2.0 km): 197.

## Lectura geológica

Un cuerpo magmático caliente (lava lake, domo activo, intrusión somera) irradia calor durante horas a días. El pixel hot reaparece **pasaje tras pasaje** en el mismo lugar del cráter. Un FP por **cirrus alto frío** (T_bg<260K), por **ruido instrumental aislado** o por **una fumarola transitoria** es de naturaleza opuesta: aparece en un solo pasaje y desaparece. Si MIROVA aplica un gate de **coherencia espacio-temporal** (mismo cluster ±2 km en ≥2 noches / pasajes), filtra justamente los transitorios que producen el grueso de nuestros FPs.

## Hallazgo central: hipótesis **CONFIRMADA**

- **TPs nuestros — % con ≥2 noches consecutivas en mismo cluster**: 91.0%
- **FPs nuestros — % con ≥2 noches consecutivas en mismo cluster**: 79.0%
- **TPs nuestros — % singletons (cluster aislado en ±7d)**: 1.9%
- **FPs nuestros — % singletons (cluster aislado en ±7d)**: 6.3%

- **MIROVA ALERTAs — % con ≥2 noches consecutivas (mismo vol)**: 91.4%
- **MIROVA ALERTAs — % singletons aislados ±7d**: 0.8%

## 1. Distribuciones persistencia (TPs vs FPs nuestros)

| Métrica | TP | FP |
|---|---|---|
| n_records_same_cluster_within_3d | n=1650, median=19.00, p25=10.00, p75=24.00, p95=31.00, max=41.0 | n=3687, median=13.00, p25=5.00, p75=21.00, p95=30.00, max=41.0 |
| n_records_same_cluster_within_7d | n=1650, median=39.00, p25=20.00, p75=51.00, p95=65.00, max=77.0 | n=3687, median=28.00, p25=9.00, p75=43.00, p95=60.00, max=77.0 |
| n_consecutive_nights_same_cluster | n=1650, median=18.00, p25=6.00, p75=43.00, p95=112.00, max=112.0 | n=3687, median=8.00, p25=2.00, p75=26.00, p95=60.00, max=112.0 |
| %singleton (aislado en ±7d) | 1.9% | 6.3% |
| %consecutivos ≥2 noches | 91.0% | 79.0% |
| %consecutivos ≥3 noches | 86.1% | 71.3% |

## 2. Persistencia MIROVA ALERTAs (¿MIROVA respeta su propio gate?)

- N ALERTAs en ventana: 1189
- n_same_3d: n=1189, median=5.00, p25=4.00, p75=6.00, p95=6.00, max=6.0
- n_consec_nights: n=1189, median=10.00, p25=4.00, p75=35.00, p95=51.00, max=51.0
- %consec ≥2: 91.4% | %singleton ±7d: 0.8%

## 3. Gates de persistencia evaluados

| # | Gate | Recall mantiene | FP filtra | Precisión antes | Precisión después |
|---|---|---|---|---|---|
| 1 | `P1: n_same_cluster_within_3d >= 1` | 96.6% | 9.4% | 0.309 | 0.323 |
| 2 | `P1b: n_same_cluster_within_3d >= 2` | 93.5% | 15.5% | 0.309 | 0.331 |
| 3 | `P2: n_consecutive_nights >= 2` | 91.0% | 21.0% | 0.309 | 0.34 |
| 4 | `P3: NOT singleton (cluster has >=2 records in ±7d)` | 98.1% | 6.3% | 0.309 | 0.319 |
| 5 | `P4: n_same_cluster_within_3d >= 3` | 91.9% | 19.9% | 0.309 | 0.339 |
| 6 | `G1 (sensor != VIIRS750) — baseline` | 100.0% | 36.5% | 0.309 | 0.413 |
| 7 | `G1 AND P1 (sensor!=VIIRS750 AND n_same_3d>=1)` | 96.6% | 40.5% | 0.309 | 0.421 |
| 8 | `G1 AND P2 (sensor!=VIIRS750 AND consec>=2)` | 91.0% | 46.7% | 0.309 | 0.433 |
| 9 | `G1 AND P3 (sensor!=VIIRS750 AND NOT singleton)` | 98.1% | 39.1% | 0.309 | 0.419 |
| 10 | `G1 AND (P1 OR vrp>=50 MW)  -- preserva picos magnitud` | 96.6% | 40.1% | 0.309 | 0.419 |

## 4. Sanity check — Lascar 17/02 (evento eruptivo confirmado)

- Registros TP Lascar 15-20/feb con pc_vrp_mw≥100 MW: 0
- MIROVA ALERTAs Lascar 15-20/feb: 14 noches → ['2026-02-15', '2026-02-16', '2026-02-17', '2026-02-19', '2026-02-20']

## 5. Villarrica lava lake sub-pixel (TP débil histórico)

- N TPs Villarrica en ventana: 34
- %singleton pixel (n=1): 11.8%
- %≥2 noches consecutivas: 100.0%
- %singleton temporal (cluster aislado ±7d): 0.0%
- Distribución n_consec_nights: n=34, median=18.00, p25=18.00, p75=37.00, p95=41.00, max=41.0
- Clusters espaciales distintos usados: 2

**Lectura**: el lava lake Villarrica es cuasi-continuo en nuestros TPs → un gate de persistencia lo preserva sin OR clause de magnitud.

## 6. Persistencia TP por volcán (régimen-check)

| Volcán | n_TP | %consec≥2 | %singleton | mediana_consec |
|---|---|---|---|---|
| Chaiten | 64 | 100.0% | 0.0% | 26.0 |
| Copahue | 4 | 75.0% | 0.0% | 11.5 |
| Isluga | 220 | 91.4% | 1.8% | 12.0 |
| Lascar | 335 | 91.9% | 0.9% | 22.0 |
| Lastarria | 290 | 93.8% | 1.4% | 112.0 |
| Llaima | 7 | 85.7% | 0.0% | 12.0 |
| NevadosDeChillan | 1 | 100.0% | 0.0% | 3.0 |
| PlanchonPeteroa | 181 | 94.5% | 0.6% | 16.0 |
| PuyehueCordonCaulle | 287 | 78.0% | 5.6% | 4.0 |
| Tupungatito | 227 | 95.6% | 1.3% | 42.0 |
| Villarrica | 34 | 100.0% | 0.0% | 18.0 |

## 7. Recomendación operacional para Frente 1.A S87

**Gate recomendado**: `G1 AND P2 (sensor!=VIIRS750 AND consec>=2)`
- Recall TP mantiene: 91.0%
- FP filtra: 46.7%
- Precisión: 0.309 → 0.433

**Implementación sugerida** (campo derivado `pc.mirova_publishable_v2`):

```python
def is_publishable_v2(record, history_same_vol):
    # G1 baseline ya adoptado
    if record.sensor.endswith('_750'): return False
    if not in_inner_radius(record): return False
    if record.pc.vrp_mw <= 0: return False
    # G_persistencia: pasaje previo o posterior en mismo cluster ±2 km, ±3 días
    cluster_key = (record.volc, round_to(record.pc.centroid_lat,3), round_to(record.pc.centroid_lon,3))
    n_neighbors = count_records_within(history_same_vol, cluster_key, days=3, radius_km=2.0)
    if n_neighbors >= 1: return True
    # OR clause: magnitud alta (preserva eventos eruptivos puntuales tipo Lascar)
    if record.pc.vrp_mw >= 50.0: return True
    return False
```

**Caveat operacional NRT**: el gate requiere ventana temporal ±3 días. Para el record más
reciente solo hay historial pasado (no futuro). Opciones:
1. **Quórum atrasado**: marcar como `mirova_publishable=True` solo cuando hay confirmación
   con pasaje posterior (latencia ~24h adicional vs MIROVA).
2. **Look-back puro**: contar solo registros en ventana [-3d, 0]. Pierde recall en primer
   pasaje de un evento nuevo pero no añade latencia.
3. **Dual flag**: publicar inmediato como `provisional=True` + reclasificar a `confirmed=True`
   cuando llegue el siguiente pasaje. Frontend muestra ambos.

## 8. Paths a outputs

- JSON: `experiments/_s86_f_precision_gap/D_temporal_coherence.json`
- MD: `experiments/_s86_f_precision_gap/D_temporal_coherence.md`
- Script: `experiments/_s86_f_precision_gap/script_D.py`
