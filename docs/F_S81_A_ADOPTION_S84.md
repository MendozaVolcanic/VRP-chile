# Adopción operacional F-S81-A — gate Path D MODIS intra-radio (S84)

**Fecha**: 2026-05-28
**Decisión**: ADOPTAR como Fase 1 del fix R3 violators
**Pair backlog**: Fase B Path A/B/C gates (no resuelto por este PR)

## Resumen ejecutivo

El gate F-S81-A mascarea pixels `dnti_ctx_hot` (Path D MODIS, 8-vecinos
contextual) que caen fuera del `inner_radius_km` del KMZ MIROVA por volcán.

**Validación A/B run [26540794992](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26540794992)**
(45 días, 22/22 jobs success, sin time-outs gracias a fix #226 timeout 50→140 min):

- Profiles paralelos: `mirova_equivalent_f_s81_a_intra_radio_{enabled,disabled}`.
- Ventana: 2026-04-12 → 2026-05-26 (45d).
- Ground truth: CSV consolidado MIROVA latest (25 ALERTAs MODIS Lascar).

## Resultados pixel-level (objetivo principal del gate)

| Volcán | inner_km | Σ dnti_ctx enabled | Σ dnti_ctx disabled | Δ |
|---|---:|---:|---:|---:|
| Copahue | 4 | 118 | 5,067 | **-97.7%** |
| NevadosDeChillan | 5 | 215 | 5,309 | **-96.0%** |
| Lastarria | 3 | 121 | 6,215 | **-98.1%** |
| PlanchonPeteroa | 3 | 106 | 7,084 | **-98.5%** |
| Tupungatito | 7 | 567 | 9,083 | **-93.8%** |
| Llaima | 5 | 306 | 5,112 | **-94.0%** |
| Villarrica | 5 | 303 | 6,468 | **-95.3%** |
| Chaiten | 5 | 488 | 7,705 | **-93.7%** |
| Isluga | 5 | 277 | 4,083 | **-93.2%** |
| Lascar | 5 | 191 | 3,500 | **-94.5%** |
| PuyehueCordonCaulle | 20 | 8,634 | 11,661 | -26.0% (inner grande) |

**El gate hace lo que dice**: -93 a -98% de pixels Path D contextual fuera del
cono caliente en TODOS los Tier A con inner ≤7 km. PCC con inner=20 km tiene
reducción menor pero la geometría es coherente (lacolito extenso difuso).

## Resultados precision/recall agregados

| Métrica | Enabled | Disabled | Baseline operacional |
|---|---:|---:|---:|
| TP Lascar (única vol con ALERTAs MODIS en ventana) | 25 | 25 | 25 |
| FP Lascar | 55 | 55 | 56 |
| FN Lascar | 0 | 0 | 0 |
| Recall Lascar | 1.000 | 1.000 | 1.000 |
| Precision Lascar | 0.312 | 0.312 | 0.309 |
| Ratio mediano | 1.483 | 1.483 | 1.274 |

**Sin regresión de TPs MIROVA**. Cambio en métricas agregadas es estadísticamente nulo.

## R3 violators a nivel cluster final (caveat conocido)

| Vol | R3 enabled | R3 disabled | R3 baseline |
|---|---:|---:|---:|
| Lascar | 5 | 5 | 23 |
| Copahue | 14 | 14 | 53 |
| NevadosDeChillan | 24 | 24 | 47 |
| Llaima | 18 | 18 | 41 |
| Tupungatito | 10 | 10 | 8 |
| (todos) TOTAL | **106** | **106** | **238** |

**Δ enabled vs disabled = 0** R3 violators. Reducción real (106 vs 238) es vs
baseline operacional (snapshot pre-S83). Esto **no era esperado** — el bloque
de arranque S84 pedía R3=0 en enabled.

### Por qué pasa

El cluster final lo arma `cluster_hotspots()` sobre **todos los pixels calientes**,
vengan de cualquier path:
- Path A: BT clásico (umbral absoluto Wooster).
- Path B: NTI absoluto > umbral.
- Path C: dNTI absoluto > umbral.
- **Path D: dNTI contextual 8-vecinos** ← único cubierto por F-S81-A.
- Test 1: Coppola 2015 integrated ROI MIR.

Aunque el gate quita 95% pixels Path D fuera del cono, **los otros 4 paths siguen
detectando pixels lejanos** (cirrus, glaciar, fumarola aislada, salar térmico)
que se agrupan en clusters fuera del inner_radius y ganan la selección.

**El gate F-S81-A es necesario pero NO suficiente** para R3=0. Hace falta Fase B
con gates análogos en Path A/B/C.

## Decisión

**Adoptar F-S81-A en `pipeline/profiles/mirova_equivalent.yaml`** (flag
`enable_path_d_intra_radio_gate: true`). Razones:

1. **Reduce 93-98% de pixels Path D ruidosos** fuera del cono — mejora interna
   del campo térmico que el dashboard renderiza, aunque no se vea en cluster
   selection downstream.
2. **Cero daño**: 0 regresión TPs MIROVA, 0 regresión recall/precision/ratio,
   0 cambio en R3 visible (los R3 vienen de otros paths, no del Path D que
   este gate cubre).
3. **No esperar Fase B** sería "perfect enemy of good": dilatar la mejora
   disponible por no tener la solución completa.
4. **Default operacional limpio** facilita el A/B futuro de Fase B (la
   reducción Path D ya estará en baseline).

## Validación post-merge

1. NRT cron próximo (~2h) confirma 0 errores nuevos.
2. Audit independiente sobre `data/mirova_equivalent/<vol>.json` próximos
   ~3 días debe mostrar `diag_n_dnti_ctx_path` reducido en Tier A
   (similar a enabled del A/B).
3. Dashboard GitHub Pages debería seguir renderizando idéntico (clusters
   finales no cambian).

## Tag defensivo

`pre-s84-f-s81-a-adoption` → `4d9b8771` (origin/main pre-adopción).

## Refs

- Run A/B: 26540794992
- Audit script: `experiments/_s83_f_s81_a/audit.py`
- Audit results: `experiments/_s83_f_s81_a/audit_results.{md,json}`
- Helper: `pipeline/path_d_intra_radio.py`
- Diagnosis Fase 1: `docs/F_S81_A_FASE1_DIAGNOSIS.md`
- Sanity p95 Fase 1b: `docs/F_S81_A_FASE1B_SANITY_P95.md`
- Sanity VIIRS (S84): `docs/F_S81_B_SANITY_VIIRS.md`
- Backlog Fase B: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`
