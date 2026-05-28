# Fase B' — gate intra-radio sobre `second_pass_recapture`

**Sesión**: S85 (2026-05-28)
**Origen**: audit B0 (`docs/R3_RESIDUAL_BY_PATH.md`) refutó el plan original
Fase B (gates A/B/C). Reorientación a la causa real de 87.7% de R3
residuales: el `second_pass_adjacent` sin restricción espacial.

## 1. Fenómeno físico

El paper Coppola 2016a SP 426.5 (§347-356) propone el "second pass" así:
tras el primer pase, los pixels marcados como activos se excluyen del cálculo
de la media 8-vecinos. Se recomputan dNTI/dETI contextuales y Tests 2∧3
sobre la escena. La idea: pixels en el **borde** de la zona caliente real
fueron contaminados por vecinos activos durante el primer pase (la media
local subió, su dNTI/dETI quedó por debajo del umbral). Excluyéndolos del
kernel, esos pixels marginales "aparecen" como anómalos y se recapturan.

**Lo que el paper no exige** — y nuestra implementación tampoco — es que el
pixel recapturado sea **espacialmente adyacente** al cluster del primer
pase. La recaptura opera sobre **toda la escena**: cualquier pixel que
cumpla Tests 2∧3 con la media recomputada queda activado, independiente
de su distancia al volcán.

### Por qué esto genera R3 violators

Cuando una escena MODIS sobre un Tier A chileno tiene:
- pocos pixels activos del primer pase (típico: ninguno o 1-2 en el cono);
- una zona difusa de cirrus uniforme alto o glaciar parcialmente cálido
  lejos del cono;

el recompute del background tras excluir esos pocos activos apenas cambia.
Pero dentro de la zona difusa, los pixels "marginalmente más cálidos que
sus vecinos post-exclusión" cumplen Tests 2∧3 sin tener relación física
con el cráter. El cluster final agrupa esos pixels lejanos → R3 violator.

### Evidencia cuantitativa

Volcanes con más R3 son los que más recapturan en 45 días:

| Volcán | R3 violators | n_2nd_pass | recaptures / ALERTA MIROVA |
|---|---:|---:|---:|
| NevadosDeChillan | 24 | 1247 | 52 |
| PlanchonPeteroa | 11 | 776 | 71 |
| Copahue | 14 | 648 | 46 |
| Chaiten | 4 | 477 | 119 |
| Llaima | 18 | 432 | n/a |

Para comparar: ALERTAs MIROVA reales en la ventana son 0-25 por volcán.
Recapturas son 1-2 órdenes de magnitud más altas. Imposible que tanto
volcán activo "marginal" exista físicamente.

## 2. Auditoría B0 — refutación Fase B original

Tabla "Distribución por path EXCLUSIVO" en `docs/R3_RESIDUAL_BY_PATH.md`:

| Path único | # R3 exclusivos |
|---|---:|
| A_bt | 0 |
| B_nti | 1 |
| C_eti | 0 |
| D_dnti_ctx | 12 |
| **Ningún path 1er pase** | **93 (87.7%)** |

87.7% de R3 violators no tienen NINGÚN path del primer pase activo. La
única fuente compatible con esto es el `second_pass_recapture` (los
pixels recapturados por el segundo pase no incrementan los counters
`diag_n_*_path` del primer pase; solo `diag_n_second_pass_recapture`).

Hay otros mecanismos candidatos secundarios (`cluster_rescue`,
`vent_anchored rescue` del S77, Test 1 integrated en Villarrica) pero el
patrón cuantitativo (n_2nd_pass masivo + volcanes con cirrus/glaciar
frecuente) apunta primero al second pass.

## 3. Solución propuesta — gate intra-radio sobre pixels NUEVOS del 2nd pass

### Principio físico

Las **ALERTAs MIROVA reales** del CSV consolidado (1332 records VIIRS Tier
A según `docs/F_S81_B_SANITY_VIIRS.md` + ~250 MODIS de la ventana 45d)
caen **100% dentro del inner_radius_km del KMZ MIROVA**. Cero excepciones.
Eso es ground truth empírico, no supuesto.

Por tanto, cualquier pixel recapturado por el segundo pase que caiga
**fuera del inner_radius** es, con muy alta probabilidad, ruido cirrus/
glaciar/salar y NO actividad volcánica real. Mascarearlo no pierde TPs.

### Mecánica del gate

**Opción adoptada**: post-proc en el caller (process_modis / process_viirs /
process_viirs_mod), no en el helper `second_pass_adjacent`. Razones:

1. No modifica el helper genérico — sigue siendo MIROVA-literal puro.
2. El gate se aplica únicamente a los pixels **nuevos** del second pass
   (no a los del first pass, que ya pasaron sus propios filtros).
3. Trivialmente toggleable con un flag y A/B-able.

Pseudocódigo:

```python
# Antes del bloque de filtros downstream:
if (ENABLE_SECOND_PASS_INTRA_RADIO_GATE and inner_radius_km is not None):
    newly_active = final_active_mask & ~hot_mask_2d  # pixels nuevos del 2nd
    intra_radio = vent_dist_per_pixel <= inner_radius_km
    newly_active_intra = newly_active & intra_radio
    final_active_mask = hot_mask_2d | newly_active_intra  # recompose
    n_second_pass_recapture = int(np.sum(newly_active_intra))

hot_mask_2d = final_active_mask
```

### Diff esperado en operacional

- Pixels recapturados FUERA del cono: descartados → no entran a clustering.
- Pixels recapturados DENTRO del cono: intactos → siguen como hoy.
- First pass: intacto.
- ALERTAs MIROVA reales: cero pérdida (100% caen intra-radio).
- R3 violators del 87.7%: deberían bajar drásticamente (hipótesis A/B
  validará el número exacto).

## 4. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Divergencia del paper Coppola 2016a (que no exige restricción espacial) | Coherente con la decisión arquitectural F-S81-A ya adoptada S84 sobre el mismo principio (gates intra-radio justificados empíricamente por KMZ MIROVA + sanity 1332 ALERTAs 100% intra-radio). Documentar como "Drift S85 — restricción espacial al second pass" en `docs/DRIFTS_S17.md`. |
| Pérdida de TPs MIROVA reales en volcanes con cráter extendido | Sanity VIIRS S84 mostró 100% intra-radio. Para MODIS: validar en A/B que TPs Lascar (única vol con ALERTAs MODIS en ventana) no caen 25→<25. |
| PCC tiene `inner_radius=20km` (lacolito extenso) — comportamiento distinto | Misma situación que F-S81-A: PCC se beneficia menos (-26% reducción Path D vs -93-98% otros) pero no se daña. Esperable similar en second pass. |
| Tupungatito glaciar puede tener señal real en borde del inner=7km | Validar empíricamente. Si pierde TPs, override per-volcán en yaml (no aplicar gate a Tupungatito). |

## 5. Plan A/B

Idéntico a S83-S84:

1. **Profiles paralelos**:
   - `mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled.yaml`
   - `mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled.yaml`
   - Heredan de operacional (F-S81-A ya activo). Solo difieren en el flag
     nuevo `enable_second_pass_intra_radio_gate`.
   - `data_subdir` aislado.

2. **Workflow**: copiar `reproc-ab-f-s81-a-intra-radio.yml` con TOKEN +
   timeout 140 + `"on":` quoted (A43) + max-parallel 8. 45d × 11 Tier A
   × 2 profiles + Villarrica con profile test1 análogo (opcional fase 2).

3. **Audit**: extender `experiments/_s83_f_s81_a/audit.py` o duplicar a
   `experiments/_s85_f_s81_b_prime/audit.py`. Reportar:
   - R3 violators (objetivo: enabled << disabled, idealmente <30).
   - TPs Lascar (objetivo: 25/25 sin pérdida).
   - Recall/precision agregados.
   - Reducción `diag_n_second_pass_recapture` agregado por volcán.

4. **Adopción** si:
   - R3 violators enabled ≤ 30 (vs 106 disabled).
   - Cero pérdida TPs MIROVA en cualquier volcán.
   - Recall y precision sin regresión >5pp per-vol.
   - **Tag defensivo `pre-s85-f-s81-b-prime-adoption`** antes de tocar
     `pipeline/profiles/mirova_equivalent.yaml`.

## 6. Implementación concreta

### Cambios mínimos requeridos

1. **`pipeline/profile.py`**: nuevo flag
   `enable_second_pass_intra_radio_gate` (default `False`).

2. **`pipeline/process_modis.py`**: insertar el bloque pseudocódigo después
   del `if ENABLE_SECOND_PASS_ADJACENT:` (línea ~640-667), antes del
   `FINAL_PIXEL_FILTER` (línea ~669).

3. **`pipeline/process_viirs.py`** y **`pipeline/process_viirs_mod.py`**:
   inserción análoga (mismo helper `second_pass_adjacent`, mismo principio).

4. **2 profiles A/B** en `pipeline/profiles/`.

5. **Workflow** `.github/workflows/reproc-ab-f-s81-b-prime.yml`.

6. **Tests TDD** en `tests/test_second_pass_intra_radio_gate.py`:
   - Pixel del second pass intra-radio → preservado.
   - Pixel del second pass extra-radio → mascarado.
   - Pixel del first pass extra-radio → intacto (gate no aplica).
   - Flag OFF → comportamiento idéntico al actual.

### Estimación

- Refactor + tests: 2-3h.
- Profiles + workflow: 30 min.
- Disparo A/B + run: ~2.5h (paralelo).
- Audit + decisión adopción: 30-45 min.

**Total Fase B'**: ~6-7h, sesión completa.

## 7. Pendiente investigación (Fase C, S86+)

Los 12 R3 residuales con `diag_n_dnti_ctx_path > 0` aún con gate F-S81-A
activo (11.3% del total) NO se explican por el second pass — Path D ya
está mascarado intra-radio en el primer pase. Hipótesis a explorar:

- Leak del gate F-S81-A en edge cases (boundary del mascareado).
- Cluster ganador armado por pixels Path D intra-radio pero centroide
  ponderado fuera del cono (cluster grande con asimetría radial).
- `vent_anchored rescue` o `cluster_rescue` (S77) seleccionando cluster
  alternativo lejano.

Si Fase B' adopta y queda con ~12-30 R3 residuales, escalada a Fase C en
S86 con investigación per-volcán de esos casos.

## Refs

- Audit B0: `docs/R3_RESIDUAL_BY_PATH.md`
- Backlog refutado: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md` (con nota
  S85 al tope)
- Adopción F-S81-A: `docs/F_S81_A_ADOPTION_S84.md`
- Sanity VIIRS: `docs/F_S81_B_SANITY_VIIRS.md`
- Helper: `pipeline/detection_context.py:second_pass_adjacent`
- Callers: `pipeline/process_modis.py:639-667`,
  `pipeline/process_viirs.py:977-1011`,
  `pipeline/process_viirs_mod.py:709-743`
- Paper: Coppola 2016a SP 426.5 §347-356 (segundo pase, sin restricción
  espacial)
- Misión vinculante: `docs/MISSION.md` (3 preguntas — este cambio pasa
  porque (a) reduce ruido alejado del cono, (b) preserva 100% TPs MIROVA
  ground-truth-validados, (c) no usa parche que MIROVA prohíba).
