# Audit B0 — R3 violators residuales por path
**Profile**: `mirova_equivalent_f_s81_a_intra_radio_enabled` (operacional adoptado S84)
**Ventana**: 2026-04-12 → 2026-05-26 (45d)
**Definición R3 violator**: MODIS record con `final_hotspot_source='eruption'` + `pc.centroid_dist_km > inner_radius_km` + `pc.vrp_mw > 0`. Esto significa que el pipeline marcó actividad eruptiva pero el centroide del cluster cae FUERA del cono caliente esperado.

## Total: 106 R3 violators en 45d × 11 Tier A

### Distribución per-volcano

| Volcán | # R3 violators | inner_km |
|---|---:|---:|
| PuyehueCordonCaulle | 1 | 20.0 |
| Villarrica | 4 | 5.0 |
| Lascar | 5 | 5.0 |
| Copahue | 14 | 4.0 |
| NevadosDeChillan | 24 | 5.0 |
| Llaima | 18 | 5.0 |
| Chaiten | 4 | 5.0 |
| PlanchonPeteroa | 11 | 3.0 |
| Lastarria | 9 | 3.0 |
| Isluga | 6 | 5.0 |
| Tupungatito | 10 | 7.0 |

### Distribución por path activo (no exclusivo)

Un record puede tener varios paths activos simultáneamente. Esta tabla cuenta cuántos R3 violators tienen ese path activo (diag_n_*_path > 0), independiente de los demás.

| Path | Campo diag | # R3 con path activo | % del total |
|---|---|---:|---:|
| A_bt | `diag_n_bt_path` | 0 | 0.0% |
| B_nti | `diag_n_nti_path` | 1 | 0.9% |
| C_eti | `diag_n_eti_path` | 0 | 0.0% |
| D_dnti_ctx | `diag_n_dnti_ctx_path` | 12 | 11.3% |
| (ningún path 1er pase) | — | 93 | 87.7% |

### Distribución por path EXCLUSIVO (único path activo)

Records donde SOLO un path se disparó (otros 3 en 0). Indica qué path es el que ÚNICO causa el R3 violator → atacar ese path elimina ese record sin afectar otros.

| Path único | # R3 exclusivos | % del total |
|---|---:|---:|
| A_bt | 0 | 0.0% |
| B_nti | 1 | 0.9% |
| C_eti | 0 | 0.0% |
| D_dnti_ctx | 12 | 11.3% |
| (multi-path) | 0 | 0.0% |
| (no path 1er pase) | 93 | 87.7% |

### Per-vol × path (heatmap textual)

| Volcán | A_bt | B_nti | C_eti | D_dnti_ctx | n_first | n_2nd |
|---|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 0 | 0 | 0 | 0 | 4 | 2 |
| Villarrica | 0 | 0 | 0 | 1 | 355 | 354 |
| Lascar | 0 | 0 | 0 | 0 | 35 | 34 |
| Copahue | 0 | 0 | 0 | 1 | 817 | 648 |
| NevadosDeChillan | 0 | 1 | 0 | 1 | 759 | 1247 |
| Llaima | 0 | 0 | 0 | 1 | 336 | 432 |
| Chaiten | 0 | 0 | 0 | 3 | 774 | 477 |
| PlanchonPeteroa | 0 | 0 | 0 | 4 | 1220 | 776 |
| Lastarria | 0 | 0 | 0 | 0 | 158 | 90 |
| Isluga | 0 | 0 | 0 | 0 | 63 | 56 |
| Tupungatito | 0 | 0 | 0 | 1 | 163 | 237 |

## Recomendación priorización Fase B

Atacar paths en orden de cobertura R3 (mayor → menor):

1. **D_dnti_ctx**: 12 R3 (11.3%). Implementar gate intra-radio análogo al F-S81-A en `diag_n_dnti_ctx_path`.
2. **B_nti**: 1 R3 (0.9%). Implementar gate intra-radio análogo al F-S81-A en `diag_n_nti_path`.

⚠️  **93 R3 violators (87.7%) no tienen NINGÚN path 1er pase activo**. Probablemente vienen del second_pass_recapture o de paths sin diag_n_*_path field (Test 1 integrated, vent_anchored rescue, cluster_rescue). Estos NO los cubre ningún gate del primer pase — requieren investigación separada (Fase C o mecanismo distinto).


## Refs

- Profile auditado: `pipeline/profiles/{PROFILE_DIR}.yaml` (mergeado S84).
- Backlog Fase B: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`
- Helper actual Path D: `pipeline/path_d_intra_radio.py`
- Detalle JSON: `experiments/_s85_f_s81_b/r3_violators_detail.json`
