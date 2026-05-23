# F2.8 — Hypothesis Log

**Sesión**: S73 (2026-05-23)
**Estado**: post-investigación F2.8.a (ver `F28_SATURATION_INVESTIGATION.md` para verdict completo)

## Convenciones

- **Estado**: CONFIRMADA (✓), REFUTADA (✗), PARCIAL, ABIERTA
- **Confianza**: high (PDF primario + verificación empírica), medium (PDF primario), low (síntesis sin verificación)

## H1 — Causa raíz MODIS: filter L1B incompleto

**Hipótesis**: `pipeline/process_modis.py:184` solo filtra `dn >= 65535`, dejando pasar el sentinel 65533 (Detector saturated) y los otros 13 sentinels Table 5.6.1.

**Estado**: ✓ CONFIRMADA (high confidence)

**Evidencia**:
- MODIS L1B C7 UserGuide Sec 5.6 verbatim: "valid science data lie only in the range [0, 32767]"
- Audit pipeline code: `fill = attrs.get("_FillValue", 65535)` confirma fallback a 65535
- Reproducción matemática: 45 pixels @ SI=65533 + scale~0.003 + offset~-1577 → BT=575.06 K + Wooster + sec³(50°) elongation → 694,440 MW (match 99.86% con 695,431 observado)

**Acción**: fix línea 184 a `rad[dn > 32767] = np.nan`.

---

## H2 — Causa raíz VIIRS: quality_flags SDS no leído

**Hipótesis**: `pipeline/process_viirs.py` y `process_viirs_mod.py` filtran los 4 sentinels DN {65532-65535} correctamente, pero NO leen el SDS de quality flags, dejando pasar pixels con bit-2 (Saturation) que el L1B clampea al "Reported Range" en lugar de marcar con sentinel.

**Estado**: ✓ CONFIRMADA (high confidence)

**Evidencia**:
- VIIRS L1B UserGuide Aug 2021 Tabla C.1 verbatim: bit-2 = Saturation; "pixel radiance is set to 'Reported Range' value"
- BT LUT max I4 = 361.77 K, I5 = 423.33 K (UserGuide verbatim)
- Audit pipeline code: `FLAG_DNS = {65532, 65533, 65534, 65535}` solo cubre sentinels DN, no quality flags
- Reproducción matemática outliers `vrp_tir_mw`: 4-16 pixels I5 @ Stefan-Boltzmann × 423K @ A_pix=140625 → 1025-4097 MW. Match con 5 outliers observados (1037, 1111, 1890, 2536, 4020 MW) <2% error.

**Acción**: leer `f["observation_data"][f"{band}_quality_flags"]` y aplicar `bt[qf & 0b100 != 0] = np.nan` (bit-2 Saturation).

---

## H3 — Defensa secundaria BT-level (Coppola 2025 Cap.11 Table 1)

**Hipótesis**: agregar threshold post-Planck-inversion como red de seguridad redundante:
- MODIS B21: `bt_mir > 500 K → NaN` (Coppola 2025 valor canónico)
- VIIRS M13 750m: `bt > 634 K → NaN`
- VIIRS I4 375m: `bt > 361.77 K → NaN` (UserGuide LUT max, more precise than Coppola 353K)
- VIIRS I5 375m TIR: `bt > 423.33 K → NaN` (UserGuide LUT max)

**Estado**: ✓ CONFIRMADA viable, ABIERTA si adoptar como defensa adicional o solo L1B-spec primario

**Evidencia favor**:
- Coppola 2025 cap.11 Table 1 valores autoritativos
- UserGuide LUT max valores son los clipping ceilings exactos
- Costo: 4-6 líneas extra de código
- Redundancia útil para colección future donde sentinel scheme cambie

**Evidencia contra**:
- Si MIROVA pudiera detectar legitimamente un volcán con BT > 500 K (caso extremo, ej. Etna paroxismo), este filter lo descartaría. Pero: Wooster ya no es válido para BT > 500 K B21 saturado, así que el VRP-MIR no es confiable ahí de todos modos.

**Recomendación**: implementar como defensa secundaria opt-in via flag `enable_bt_sat_secondary_guard: true`. Default operacional ON.

---

## H4 — Reproc fósil histórico

**Hipótesis**: el record PP 2026-03-18 con `pc.vrp_mw=695,431` debe ser limpiado del JSON operacional via reproc de 1 granule.

**Estado**: ABIERTA, dependent de decisión adopción

**Evidencia favor**:
- Audit confirma 1 SOLO fósil en 34,068 records totales
- Costo reproc: ~5 min con fix aplicado (1 granule, 1 día)
- Beneficio: dataset operacional limpio post-fix

**Evidencia contra**:
- El fósil es invisible en producción default (`distance_class=far`)
- Pero es visible con `includeFar=true` toggle y en `diario.html`

**Recomendación**: reproc en F2.8.f junto con A/B test del fix.

---

## H5 — Frontend hardening (diario.html + includeFar toggle)

**Hipótesis**: `frontend/diario.html:227` retorna `pc.vrp_mw ?? 0` sin filtros, y `mirovaEqVrp(r, innerKm, true)` con `includeFar=true` también salta filtros — ambos casos pueden exponer valores corruptos pre-fix.

**Estado**: ✓ CONFIRMADA, ABIERTA si hard-block sat values en frontend o confiar en pipeline fix

**Evidencia favor**:
- Defense-in-depth: si pipeline mete un error nuevo, frontend lo atrapa
- Costo: 5-10 líneas JS

**Evidencia contra**:
- Si el pipeline fix es robusto (L1B + quality_flags + BT defense), el frontend ya no recibe valores absurdos
- Cambios al frontend requieren coordinar deploy GH Pages

**Recomendación**: implementar guard simple en frontend usando el `SANITY_CAP_VRP_MW=50000` ya documentado en `pipeline/store.py`. Agregar JS: `if (pc.vrp_mw > 50000) return 0`. F2.8.g.

---

## H6 — No-op: cap S41 ya protege, no implementar fix upstream

**Hipótesis**: el cap downstream S41 (50K MW clamp) ya captura el bug en records nuevos. El fósil PP es invisible en producción. No vale la pena tocar pipeline.

**Estado**: ✗ REFUTADA

**Por qué REFUTADA**:
1. El cap actúa solo sobre `vrp_mw` y `pc.vrp_mw`, NO sobre `vrp_tir_mw` (VIIRS outliers no están capeados — siguen contaminando JSONs operacionales).
2. Aunque la magnitud se clampea, los **síntomas colaterales persisten**: σ_bg=128 K envenenado, n_anomalous_pixels=113 fake, cluster geometry distorted. Estos contaminan métricas y dashboards.
3. Cap S41 es defensa de últim recurso. Filter L1B upstream es la solución arquitectural correcta. Costo bajo (1 línea MODIS + 1 SDS read VIIRS).
4. Records nuevos siguen produciendo el bug, solo que con magnitud clampeada. No es "no problem".

**Cap S41 se mantiene** como red de seguridad — defense-in-depth, no se desactiva.

---

## H7 — Per-volcán opt-in fix saturation guard

**Hipótesis**: ¿Hacer el saturation guard opt-in por volcán (yaml flag) como hicimos con `local_kernel_bg`?

**Estado**: ✗ REFUTADA

**Por qué REFUTADA**:
- El bug es L1B-level: afecta a TODOS los granules de TODOS los volcanes por igual.
- No hay caso defensible donde un volcán "necesite" pixels saturados.
- Diferente a `local_kernel_bg` que tiene físicamente sentido per-vol (depende de terreno).
- Costo de mantener 11+ flags `enable_sat_guard_<vol>: true` >>> beneficio cero.

**Acción**: implementar globalmente, sin flag opt-in.

---

## H8 — sec³(θ_z) scan-angle factor podría amplificar otros bugs

**Hipótesis**: si pipeline ya usa `modis_pixel_areas` con sec³ correction, ¿hay otros patrones donde un error de cómputo se amplifique por scan angle?

**Estado**: PARCIAL — anotada para sesiones futuras

**Evidencia**:
- Verificación matemática: factor 3.74× para θ_z=50° contribuyó a magnitud del bug PP
- VIIRS también tiene equivalente (pero usa A_pix nadir fijo per CLAUDE.md S14: paridad MIROVA)
- Posibles patrones a auditar: vent-only detections con sec³ amplification, t1_vrp en process_modis:968

**Acción**: tarea backlog. Auditar `experiments/` con focus sobre records `final_hotspot_dist_km > 20` y scan angle alto, ver si patrones similares aparecen.

---

## H9 — DefensaDual: σ_bg sanity gate

**Hipótesis**: agregar gate `if std_bg > 30 K: discard scene` con `discarded_reason="sigma_bg_unphysical"`.

**Estado**: ✗ REFUTADA (innecesaria post-H1+H2)

**Por qué REFUTADA**:
- El σ_bg=128 K que vimos en el fósil PP es CONSECUENCIA de pixels saturados envenenando el ring BG.
- Con H1 (L1B filter MODIS) y H2 (quality flags VIIRS) aplicados, los pixels saturados se enmascaran a NaN ANTES del cómputo σ_bg.
- σ_bg sano sería ~1-5 K post-fix, automáticamente.
- Gate σ_bg redundante con causa raíz ya resuelta.

**Si fix H1+H2 NO se aplica**, entonces H9 sería defensa válida. Pero las priorizamos al revés.

---

## H10 — VIIRS Opción B simple (BT >= LUT max) en vez de leer quality_flags

**Hipótesis**: en lugar de leer el SDS de quality flags (Opción A), agregar simplemente `bt[bt >= LUT_max_per_band - 0.5] = np.nan`.

**Estado**: ABIERTA, opción de simplificación

**Evidencia favor**:
- Mucho más simple: 1 línea en lugar de SDS read + bit mask
- No requiere conocer la estructura del archivo NetCDF VIIRS
- Cualquier BT clamped al LUT max indica clipping → defensa válida

**Evidencia contra**:
- Si un volcán emite exactamente al LUT max naturalmente (improbable pero teórico), lo descartamos
- Menos preciso que leer quality flag directamente
- Si NASA cambia el LUT max en future colecciones, threshold sale del rango sin warning

**Recomendación**: implementar **AMBAS**, con leer quality_flags como primaria y BT >= LUT_max como defensa secundaria redundante. Costo de hacer ambas: 4-6 líneas extra.

---

## Decisión consolidada

**Plan ejecutivo conservador a implementar**:

1. **H1 MODIS L1B fix** (1 línea, autoritativo) — IMPLEMENTAR
2. **H2 VIIRS quality_flags read** (Opción A primaria, 5-8 líneas por procesador) — IMPLEMENTAR
3. **H3 BT defense secondary** (4-6 líneas total) — IMPLEMENTAR con flag `enable_bt_sat_secondary_guard: true` default
4. **H4 reproc fósil** (1 granule en F2.8.f) — IMPLEMENTAR
5. **H5 frontend hardening** (5-10 líneas JS) — IMPLEMENTAR
6. **H6 no-op** — REFUTADA
7. **H7 per-vol opt-in** — REFUTADA, fix global
8. **H8 sec³ amplification audit** — BACKLOG
9. **H9 σ_bg gate** — REFUTADA (redundante post-H1+H2)
10. **H10 VIIRS Opción B BT >= LUT_max** — IMPLEMENTAR como defensa secundaria sobre Opción A

**Cap S41 NO se desactiva** — red de seguridad downstream.

**Total scope final**:
- 1 línea fix MODIS (H1)
- ~8 líneas VIIRS quality_flags (H2) × 2 procesadores
- ~4 líneas BT defense secundaria (H3+H10) × 3 procesadores
- 1 reproc granule (H4)
- ~6 líneas JS frontend (H5)

≈ **40-50 líneas de código nuevo** + tests TDD + A/B reproc + docs. Estimado 3.5-4 horas total para cerrar F2.8.
