# F46 VRP TIR — Gate provisional S81

**Fecha**: 2026-05-26
**Decisión**: Nicolás explícito S81 — Opción D (gate provisional ahora + F46 dedicado después).
**Tag defensivo**: `pre-s81-vrp-tir-gate` (apunta a `origin/main` previo a este cambio).
**Branch**: `claude/s81-vrp-tir-gate`.

## Por qué este doc existe

La auditoría integral S81 frente #3 detectó **726 records en
`data/mirova_equivalent/*.json` con ratio `vrp_tir_mw / vrp_mir_mw > 1000×`**
post-S77 gate Opción A+B (F46 docs/F46_VRP_TIR_BUG_S76.md). Top casos:

| Volcán | Datetime UTC | Sensor | MIR (MW) | TIR (MW) | Ratio |
|---|---|---|---:|---:|---:|
| Villarrica | 2026-02-11 06:48 | VIIRS_SNPP | 0.98 | 5680.07 | **5802×** |
| Chaiten | 2026-03-26 06:12 | VIIRS_NOAA21 | 0.58 | 3028.19 | 5257× |
| Chaiten | 2026-02-04 05:36 | VIIRS_SNPP | 0.87 | 4415.60 | 5099× |
| Villarrica | 2026-02-10 05:24 | VIIRS_SNPP | 2.00 | 8740.90 | 4366× |
| PCC | 2026-05-16 06:06 | VIIRS_NOAA20 | 1.06 | 3790.79 | 3586× |

**Diagnóstico geofísico**: el VRP TIR actual aplica Stefan-Boltzmann
`σ · A_pix · (T_hot⁴ - T_bg⁴)` sobre la `hot5_mask_2d` filtrada por el
gate F46 S77 (Opción A+B). Pero el gate solo verifica que MIR/NTI haya
detectado algo en la escena y aplica un threshold subido — no resta el
background correctamente cuando la máscara es heterogénea (cirrus, nieve
parcial, lago caliente post-atardecer). El bug remanente es **arquitectural**:
la fórmula correcta para regimens de baja temperatura es la
**Coppola 2024 chapter Eq.15+16 (lava lake R2)** que primero estima
`A_hot` por unmixing de radiancia espectral Planck y después aplica
Stefan-Boltzmann sobre `A_hot · (T_e⁴ - T_bk⁴)` con `T_e` fijo.

`pipeline/vrp_regimes.py::compute_vrp_lava_lake_eq16` **ya implementa** la
fórmula correcta R2, pero solo para casos sub-pixel lava lake con `T_e=1000K`
asumido. El path TIR actual en `process_viirs.py` NO la usa — sigue con
Stefan-Boltzmann directo.

## Qué hace el gate provisional S81

**Mínimo posible para silenciar el bug sin romper nada**:

1. **Flag nuevo** en `pipeline/profile.py`:
   ```python
   ENABLE_VRP_TIR_OUTPUT: bool = bool(_cfg.get("enable_vrp_tir_output", True))
   ```
   Default `True` → comportamiento legacy. Profiles operacionales setean `False`.

2. **Parámetro nuevo** en
   `pipeline/process_viirs.py::_compute_vrp_tir_with_gate`:
   ```python
   def _compute_vrp_tir_with_gate(..., enable_output: bool = True) -> float:
       if not enable_output:
           return 0.0
       # ... resto igual (gate Opción A+B se ejecuta normal)
   ```

3. **Profile operacional** `pipeline/profiles/mirova_equivalent.yaml`:
   ```yaml
   enable_vrp_tir_output: false   # F46 provisional S81 — espera fix Coppola Eq.16
   ```

4. **Tests sintéticos** en `tests/test_vrp_tir_provisional_gate_s81.py`
   (6 tests: enable_output=False fuerza 0, default=True permite cómputo,
   profile silencia output).

## Lo que ESTE gate NO hace

- ❌ NO repara los 726 records históricos en
  `data/mirova_equivalent/*.json`. Esos quedan con `vrp_tir_mw` inflado
  hasta que se reprocesen post-F46.
- ❌ NO corrige la fórmula científica. Es silenciar, no curar.
- ❌ NO toca `data/experimental*/` ni perfiles experimentales (siguen con
  el comportamiento legacy si lo necesitan para investigar).
- ❌ NO modifica el caller F31 `_compute_vrptir_aveni_diagnostic`
  (Aveni 2025 GRL Eq.9 con `k_TIR=60.17`) — ese es un path separado que
  emite a `vrptir_aveni_mw`, no a `vrp_tir_mw`.

## Lo que ESTE gate SÍ hace

- ✅ A partir del próximo run NRT post-merge, **todos los records nuevos
  tendrán `vrp_tir_mw = 0`**.
- ✅ El dashboard frontend ya tiene mitigación parcial S76/S77 (marker
  cap'd, CSV con caveat). Con `vrp_tir_mw=0` el caveat queda ocioso pero
  no daña.
- ✅ Es **reversible con un solo commit** — basta cambiar
  `enable_vrp_tir_output: true` cuando F46 esté listo.
- ✅ Honesto: emitir 0 dice "no sabemos" en vez de mentir con 5680 MW.

## Plan F46 completo (sesión dedicada futura)

Ver `docs/F46_VRP_TIR_BUG_S76.md` para el plan original. Resumen mínimo:

1. Migrar el cómputo VRP TIR de Stefan-Boltzmann directo sobre máscara
   contaminada → llamar a `compute_vrp_lava_lake_eq16` (Coppola 2024
   Eq.15+16) con `T_e=1000K` para regimens sub-pixel.
2. Decidir si MODIS y VIIRS-M deberían también producir `vrp_tir_mw`
   (hoy solo VIIRS-I lo emite). Probablemente no — MIROVA NRT no publica
   TIR como métrica primaria.
3. Tests R1 sintéticos + R2 pixel-level contra `mirova-tif-archive`.
4. Reproc retroactivo Tier A para curar los 726 records históricos.
5. Validación A35 PDF Aveni 2025 GRL paywalled (k_TIR=60.17 sigue
   pendiente verificación verbatim, ver `docs/F31_AVENI_GRL_2025_EXTRACT.md`).
6. Cuando todo esté validado: setear `enable_vrp_tir_output: true` en
   `mirova_equivalent.yaml`.

**Estimado F46 completo**: 14-16h.

## Cómo revertir este gate (si fuera necesario)

```bash
# Revertir solo el gate provisional (mantiene tests + doc para referencia):
git checkout pre-s81-vrp-tir-gate -- pipeline/profiles/mirova_equivalent.yaml
# Edita pipeline/profile.py y process_viirs.py para quitar el flag/parámetro
# (o simplemente settear enable_vrp_tir_output: true en el yaml)
```

## Checklist adopción operacional del fix F46 completo (futuro)

Cuando se implemente F46 dedicado, el checklist de adopción debe incluir:

- [ ] R1: tests sintéticos sobre la nueva fórmula Coppola 2024 Eq.16.
- [ ] R2: pixel-level vs `mirova-tif-archive` ≥5 records × 3 vols.
- [ ] R3: audit independiente (script en `experiments/`).
- [ ] A45 confirmación explícita Nicolás.
- [ ] Tag `pre-f46-complete-adoption`.
- [ ] PR aislado.
- [ ] Setear `enable_vrp_tir_output: true` en `mirova_equivalent.yaml`.
- [ ] Reproc histórico Tier A 30d (workflow_dispatch SERIAL, A47).
- [ ] Re-audit anomalías post-reproc: 726 records deben caer a <50 outliers
      o quedar todos explicables por física.
- [ ] Actualizar este doc: status → CERRADO.

## Referencias

- Auditoría que detectó el problema: `docs/AUDIT_INTEGRAL_S81.md` frente #3.
- Plan original F46: `docs/F46_VRP_TIR_BUG_S76.md`.
- Fórmula MIROVA correcta: Coppola 2024 chapter Springer §"Lava lakes" L1115-1170,
  ya implementada en `pipeline/vrp_regimes.py::compute_vrp_lava_lake_eq16`.
- Aveni 2024 RSE Eq.5 (Stefan-Boltzmann sobre ΔT⁴, no T⁴ absoluta):
  `docs/F31_AVENI_2024_TIRVOLCH_VERIFY.md`.
- Misión vinculante clon MIROVA: `docs/MISSION.md` (3 preguntas).
