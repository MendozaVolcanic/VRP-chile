# H8 A/B reproceso — reporte final (S35)

**Fecha**: 2026-05-10
**Run**: [25626608687](https://github.com/MendozaVolcanic/2VRP-chile/actions/runs/25626608687) (7d window 2026-05-03 → 2026-05-09)
**Run anterior cancelado**: [25623575250](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/25623575250) (25d window, 19/22 timeout 50min)

## Métricas

| Métrica | baseline | h8_off | **h8_on** | Delta H8 |
|---|---:|---:|---:|---:|
| n records | 5643 | 977 | 661¹ | — |
| Recall vs ALERTA | 24.2% | 9.4% | **4.8%** | — |
| TP / FN | 162/507 | 63/606 | **32/637** | — |
| Ratio mediano VRP/MIROVA | 3.33× | 3.61× | **5.09×** | **+41%** ↑ |
| Ratio mean VRP/MIROVA | 37.3× | 29.0× | **49.5×** | **+71%** ↑ |
| Recovery cases (off=0 → on>0) | — | — | **86** | — |
| Regression (off>0 → on=0) | — | — | **0** | — |

¹ h8_on faltan 2-3 jobs por completar; cuando termine puede subir +10-20% records.

## Análisis

### Recovery cases — predominantemente RUTINA / FP

De los 86 records donde H8 cambia vrp_mw=0 → vrp_mw>0:

- **~70% son RUTINA** (MIROVA no reporta nada, VRP-chile ahora "rescata" detecciones — falsos positivos)
- **~25% sin entry MIROVA** (probablemente burst-loss de Mirova-v1, no alertas reales)
- **~5% sí coinciden con ALERTA_TERMICA** pero con magnitud sobre-dimensionada:
  - Lascar 2026-05-03 01:45: H8 dice **45 MW**, MIROVA dice **1.14 MW** → ratio 39×
  - PuyehueCordonCaulle 9-may lacolito: pendiente verificar (job en progreso)

### Por qué H8 solo empeora la situación

El bug H8 es real y se confirmó pixel-level con TIF MIROVA. Pero el fix preserva
clusters que VRP-chile elige incorrectamente:

1. VRP-chile elige `primary_cluster` por VRP máximo / pixel count máximo
2. Para Puyehue, ese cluster es el cráter principal (99 pixels, 5 MW, T_max=284K)
3. MIROVA reporta el lacolito (35 pixels, 0.18 MW, distinto cluster)
4. H8 fix preserva ambos clusters in-range; primary_cluster sigue siendo el equivocado
5. Ratio 27× resultante = bug D8 amplificado

**Sin fix D8 (cluster selection), H8 amplifica overdetection.**

## Decisión data-driven

**❌ NO adoptar H8 en operacional** ahora.

Criterios del handoff doc:
- ❌ Recall NO sube ≥10pp (de hecho baja, aunque parcialmente por data incompleta)
- ❌ Ratio mediano sube de 3.33× a 5.09× (+41%, criterio era mantener <5×)
- ❌ Recovery cases mayoritariamente RUTINA, no ALERTA reales

**Mantener H8 como flag opt-in** (`enable_pixel_level_distance_filter`) en
profiles A/B. Disponible para investigación, NO operacional.

## Próximos pasos S36

1. **Investigar D8 con prioridad alta** — sin fix D8, el bug H8 no se puede
   resolver sin causar daño colateral.
   - Leer Coppola 2016a §clustering algorithm
   - Sample 10 casos D8 candidatos (Tupungatito 21, Puyehue 16) y comparar coords
     primary_cluster VRP-chile vs cluster MIROVA reportado en latest.php
   - Hipótesis: MIROVA usa criterio "anomaly score relativo" o "primer cluster
     que cruza threshold local" en vez de "vrp_mw máximo absoluto"

2. **Considerar fix combinado H8+D8** una vez D8 esté entendido.
   - Ese sería el verdadero clon literal MIROVA pixel + cluster-correct.

3. **NO revertir fix S33** (`mirovaEqVrp`) hasta tener D8 resuelto.
   - Sino frontend va a mostrar tanto cluster cráter (equivocado) como cluster
     lejano (real lacolito) → confusión visual operacional.

4. **Documentar el bug H8 en docs/MIROVA_DIVERGENCES.md como abierto**:
   - Estado: detectado, fix disponible en perfil _h8_pixel_filter_enabled
   - Pendiente fix D8 antes de adopción
   - Reach 13.7% records Tier A (sigue activo en operacional)

## Lecciones meta

1. **H8 sin D8 es peor que H8 desactivado**. La interacción entre bugs
   arquitecturales debe evaluarse antes de aplicar fixes parciales.
2. **El A/B con ventana 25d no cabe en GitHub Actions 50min timeout**.
   Para futuros A/B usar chunks de 7d max para volcanes activos.
3. **El recovery case audit reveló dimensión nueva**: muchos recoveries son
   detecciones reales (TIF tiene valor) pero MIROVA correctamente las clasifica
   como FP/RUTINA. Eso significa **MIROVA tiene lógica adicional para excluir
   anomalías térmicas válidas pero no-volcánicas**. Investigar (¿MOUNTS?
   ¿base de datos de fuegos? ¿filtro espacial vegetación?).

---

**Comando para reproducir**: `python experiments/79_h8_ab_compare.py`
**Output CSV completo**: `reports/h8_ab_comparison.csv`
