# F52-B — Single-pixel mode régimen sub-MW (drift T1.5 S72 fix)

**Status**: implementado S77, PR contra `main` (A45 autorizado por Nicolás).
**Tag defensivo**: `pre-s77-f52b-single-pixel-sub-mw`.
**Refs**: PRs #191 (Villarrica) + #192 (Tupungatito/PCC), experiments/146 + 147,
CLAUDE.md A45.

## El fenómeno físico

En régimen sub-MW (0.21-0.45 MW canónicos MIROVA NRT) el cráter emite señal
térmica anómala pero el satélite captura **un solo pixel hottest** por
granule. MIROVA NRT reporta exactamente ese pixel. Nuestro path D
dNTI-contextual, en cambio, marca como hot 2-3 pixels vecinos cuando el
contraste relativo dNTI supera el threshold local, aunque cada uno aporte
solo ~0.5-2 MW residual. La suma de esos pixels llega a 2-30× el valor
MIROVA — no porque detectemos más energía real, sino porque agregamos
diferente.

Caso opuesto PCC (ratio 0.48×): MIROVA reporta el pixel más caliente del
cluster contiguo, nosotros sumábamos los 2-3 pixels del cluster — lo cual
suena análogo pero ocurre con la fuente fría del lacolito donde MIROVA
hace single-pixel mientras nuestro sum + filtros distintos terminaban
debajo del reporte MIROVA. Es el mismo bug arquitectural manifestado al
revés.

## Volcanes afectados (audit PRs #191 + #192)

Régimen sub-MW dominante:

| Volcán | Ratio mediano pre-fix | Causa |
|---|---|---|
| Tupungatito | 30.15× | path D 2-3 pixels suma factor 30 vs single-pixel MIROVA |
| Chaitén | 2.53× | mismo patrón, menor magnitud relativa |
| PlanchonPeteroa | 2.10× | mismo patrón |
| PCC | 0.48× (sub-estimación) | patrón opuesto, misma causa raíz |

**NO afectados** (régimen alto-MW o sin path D dominante): Villarrica
(diagnosticado F52-A, otro fix), Copahue, Isluga, Lascar, Lastarria,
Llaima, NdC.

## El fix

Cuando `primary_cluster.vrp_mw < threshold` **Y** `n_pixels <= max_pixels`,
reportar `pc.vrp_mw = max(per_pixel_vrp)` en vez de `sum`. Mantiene
`n_pixels` (informativo) y agrega `single_pixel_mode=True` flag para audit
downstream.

Implementación: `pipeline/single_pixel_mode.py` (pura, sin side effects)
llamada desde los 3 procesadores (process_modis, process_viirs,
process_viirs_mod) en ambos sitios donde se construye `primary_cluster`
(eruption path + Test 1 path).

## Flags en `mirova_equivalent.yaml`

```yaml
enable_single_pixel_sub_mw_mode: true      # default ON post-fix
sub_mw_regime_threshold_mw: 5.0            # vrp_mw_sum < 5 MW
single_pixel_max_cluster_pixels: 3         # n_pixels <= 3
```

Constantes expuestas en `pipeline/profile.py`:
`ENABLE_SINGLE_PIXEL_SUB_MW_MODE`, `SUB_MW_REGIME_THRESHOLD_MW`,
`SINGLE_PIXEL_MAX_CLUSTER_PIXELS`.

## Tests (TDD primero)

`tests/test_single_pixel_mode_f52b.py` — 11/11 PASS:

- `test_sub_mw_regime_triggers_single_pixel` — cluster [1.2, 0.8, 0.5] MW → max=1.2
- `test_above_threshold_passthrough` — sum >= 5 MW → passthrough
- `test_large_cluster_passthrough` — n_pixels=5 → passthrough
- `test_disabled_flag_passthrough` — flag OFF → passthrough sin marcar flag
- `test_edge_single_pixel_exact_threshold` — boundary 5.0 == threshold passthrough
- `test_single_pixel_just_below_threshold` — 4.99 MW → activa
- `test_none_primary_cluster` — None → None
- `test_empty_per_pixel_vrp_passthrough` — defensa contra vacío
- `test_nan_filtered_in_per_pixel_vrp` — NaN se ignora
- `test_does_not_mutate_input_dict` — pure function
- `test_tupungatito_canonical_case` — escenario real Tupungatito

**Suite global**: 496 passed, 24 skipped, 0 regresión (baseline S75 = 456 passed).

## Plan A/B post-merge (30d operacional)

Una vez mergeado el PR, monitorear durante 30 días NRT y comparar contra
historial MIROVA scrapeado (CSV consolidado).

### Métricas a comparar

| Métrica | Pre-fix | Esperado post-fix |
|---|---|---|
| Ratio mediano Tupungatito | 30.15× | **1.0-3.0×** |
| Ratio mediano Chaitén | 2.53× | **1.0-1.5×** |
| Ratio mediano PP | 2.10× | **1.0-1.5×** |
| Ratio mediano PCC | 0.48× | **0.5-1.0×** |
| Recall Tier A (5 vols no afectados) | (baseline) | **igual ±2pp** |
| Precision Tier A | (baseline) | **igual ±2pp** |

### Reproc empírico

Re-correr `experiments/146` o `experiments/147` (audit ratio ours/MIROVA)
con un día Test del último mes operacional y comparar pre/post-fix con
profile flag ON vs OFF (clone perfil `_f52b_off.yaml` con
`enable_single_pixel_sub_mw_mode: false`).

Si los ratios convergen al rango esperado **sin** caer recall en los
5 vols NO afectados → fix valida en operacional.

### Riesgo conocido

Si MIROVA NRT en algún día puntual reportara un cluster real de 4-5 pixels
en régimen 3-5 MW (límite de threshold), nuestro fix podría sub-reportar
ese cluster real. Mitigación: el `single_pixel_max_cluster_pixels=3` corta
exactamente para evitar ese caso. Si aparece evidencia empírica del falso
sub-reporte → subir threshold a 4 px o bajar threshold MW.

## No mergear automáticamente

Esperar review humano sobre el PR. Justificación: cambio en pipeline NRT
operacional crítico (A45 + A38 + A39 aplicados — tag defensivo creado,
tests baseline OK, autorización explícita). El paso de mergear queda al
reviewer humano para preservar la regla R2 (validación pixel-level
opcional pre-adopción operacional).
