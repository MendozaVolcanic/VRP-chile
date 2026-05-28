> **ACTUALIZACIÓN S85 (2026-05-28) — el plan original quedó refutado por el audit B0**.
>
> Audit `experiments/_s85_f_s81_b/audit_r3_by_path.py` sobre los 106 R3 residuales del
> profile operacional `mirova_equivalent_f_s81_a_intra_radio_enabled` mostró:
>
> - Path A activo en 0/106 R3 (0.0%)
> - Path B activo en 1/106 R3 (0.9%)
> - Path C activo en 0/106 R3 (0.0%)
> - Path D activo en 12/106 R3 (11.3%) — posible leak del gate F-S81-A (revisar)
> - **NINGÚN path 1er pase activo en 93/106 R3 (87.7%)** ← causa real
>
> Implementar gates A/B/C según este doc atacaría 1 de 106 violators → no-op.
>
> La causa real del 87.7% es el **`second_pass_recapture`** (volcanes con más
> R3 tienen n_2nd masivo: NDC=1247, PP=776, Copahue=648) y posibles
> `cluster_rescue`/`vent_anchored rescue` (S77).
>
> **Nuevo plan**: ver `docs/R3_RESIDUAL_BY_PATH.md` sección "Recomendación
> priorización Fase B" + reorientación a Fase B' (gate sobre second pass) y
> Fase C (rescue mechanisms). Backlog Fase B original queda como referencia
> histórica de qué NO atacar primero.

# Backlog Fase B — gates intra-radio Path A/B/C MODIS

**Origen**: cierre S84. Adopción F-S81-A redujo 93-98% pixels Path D fuera del
cono pero R3 violators a nivel cluster final **no bajaron** (106 idénticos
enabled vs disabled). Causa: cluster final agrega pixels de TODOS los paths
(A, B, C, D, Test 1). El gate F-S81-A cubre solo Path D.

## Problema

Para alcanzar R3 = 0 en operacional (criterio del bloque arranque S84) hace
falta extender el gate intra-radio a los paths restantes que también producen
pixels fuera del cono:

| Path | Mecanismo | Probable contribución a R3 residuales |
|---|---|---|
| **A** — BT clásico | umbral absoluto Wooster | alto en cirrus + nieve parcial cálida |
| **B** — NTI absoluto | NTI > -0.8 | alto en escenas frías (NTI saturado por def) |
| **C** — dNTI absoluto | dNTI > k1 | medio |
| **D** — dNTI contextual 8-vecinos | **YA cubierto F-S81-A** | -95% reducido |
| **Test 1** — Coppola 2015 integrated ROI | suma exceso radiancia ROI 3 km | bajo (ROI ya restringe) |

## Sanity VIIRS (S84) — datos relevantes

`docs/F_S81_B_SANITY_VIIRS.md` mostró que **1332 ALERTAs MIROVA Tier A
(CONS + OCR) caen 100% dentro de inner_radius**. Cero excepciones. Eso
significa que gates intra-radio análogos en VIIRS también son seguros (sin
pérdida de TPs MIROVA).

## Plan Fase B (orientativo, próxima sesión)

### B0 — Audit cuántos R3 residuales vienen de cada path

Antes de implementar gates nuevos, medir cuántos de los 106 R3 residuales
provienen de cada path. Por ejemplo:

```python
# Pseudocódigo del audit B0
for record in r3_violators_enabled:
    paths_contributing = []
    if record['diag_n_bt_path'] > 0:        paths_contributing.append('A')
    if record['diag_n_nti_path'] > 0:       paths_contributing.append('B')
    if record['diag_n_dnti_ctx_path'] > 0:  paths_contributing.append('D')  # debería ser 0 con gate
    ...
```

Si 90% R3 residuales tienen Path A activo → gate Path A es prioridad 1.

### B1 — Diseñar helper `apply_intra_radio_gate_path_X`

Reusar el helper genérico `pipeline/path_d_intra_radio.py:apply_intra_radio_gate`
parametrizando el `_hot` array de entrada. Cambio chico: refactor a función
genérica + 4 wrappers (uno por path).

### B2 — Flags separados o flag único

Opciones:
- **A**: flag único `enable_intra_radio_gate_all_paths` (más simple, todo-o-nada).
- **B**: flags separados `enable_path_a_intra_radio_gate`, `enable_path_b_*`, etc
  (más granular, permite A/B per-path).
- **C** (recomendada): un solo flag global + bitmask por path
  `intra_radio_gate_paths: ["A","B","C","D"]`.

### B3 — A/B reproc + audit

Mismo patrón validado en S83-S84: profiles paralelos, data_subdir aislados,
workflow A/B con max-parallel 8 + timeout 140.

### B4 — Adopción + Tag defensivo

Si A/B confirma reducción R3 a ~0 sin perder TPs MIROVA → adoptar igual que
F-S81-A.

## Riesgo a evaluar

Los paths A/B son los más "MIROVA-literal" (umbrales Wooster y NTI absolutos,
papers Coppola 2016a). Caparlos a inner_radius puede perder TPs en eventos
extendidos (lava flow lejano, lahar térmico). Validar empíricamente con A/B
antes de adoptar.

**Mitigación**: si Path A intra-radio pierde TPs en algún vol, mantener Path A
sin gate solo para ese vol via override per-volcán en `volcanoes.yaml`.

## Estimación

- B0 (audit): 1-2h offline puro.
- B1-B2 (refactor helper + flags): 2-3h código + tests.
- B3 (A/B + audit): ~3-4h (1h disparo + 2.5h run + 30 min audit).
- B4 (adopción): 30 min.

**Total Fase B**: ~7-10h, una sesión completa o partida.

## Referencias

- Adopción F-S81-A: `docs/F_S81_A_ADOPTION_S84.md`
- Sanity VIIRS: `docs/F_S81_B_SANITY_VIIRS.md`
- Helper Path D: `pipeline/path_d_intra_radio.py`
- Profile flag actual: `pipeline/profile.py:154`
