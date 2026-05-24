# F50 — Audit MODIS_AQUA 2026-05-23 07:25 UTC: contaminación 5 volcanes simultánea

**Sesión**: S77 P3 (audit read-only)
**Fecha**: 2026-05-24
**Worktree**: `VRP-Chile-s77-p3-modis-audit/` (branch `claude/s77-p3-modis-audit`)
**Autoridad para fix**: bloqueado por A45 — requiere confirmación explícita de Nicolás antes de tocar `pipeline/process_modis.py` o `pipeline/process_viirs*.py`.

---

## 1. Síntoma

5 de 6 volcanes Tier A en el granule `MYD021KM.A2026143.0725.061.hdf` reportaron
`vrp_mw` scene-wide entre 81 y 511 MW mientras el `primary_cluster.vrp_mw` (la
señal contigua centrada en el vent) era ≤19 MW. Llaima en el mismo granule
reportó `vrp_mw == primary_cluster.vrp_mw == 16.4 MW` — coherente porque
disparó Test 1 con un cluster real de 10 píxeles a 1.2 km del cráter.

| Volcán | `vrp_mw` scene | `primary_cluster.vrp_mw` | `n_anomalous_pixels` | `t_bg_k` | `triggered_test1` |
|---|---:|---:|---:|---:|---|
| Villarrica | 132.8 | 4.54 | 83 | 269.65 | False |
| Copahue | 150.5 | 0.85 | 156 | 272.84 | False |
| PuyehueCordonCaulle | 510.9 | 5.00 (capped) | 556 | 262.11 | False |
| NevadosDeChillan | 81.2 | 0.62 | 132 | 275.32 | False |
| Chaiten | 210.9 | 18.82 | 217 | 271.30 | False |
| **Llaima** | **16.4** | **16.4** | 133 | 274.98 | **True** |

`t_bg_k` 262-275 K es escena **muy fría coherente** sobre toda la región
centro-sur de Chile (≈600 km de extensión). La pista física más limpia: cirrus
extendido (nube fina alta, T ≈ -40 °C) deflactando el background en todos los
volcanes simultáneamente. No es saturación L1B (`t_max_k ≤ 285 K`, lejos del
sentinel >500 K que produciría F2.8).

---

## 2. Veredicto sobre las hipótesis

- **H2 saturación MODIS L1B → REFUTADA**. `t_max_k` ≤ 285.45 K en los 5
  records, BTs de píxeles "anomalous" 270-285 K, ningún sentinel uint16.
  F2.8 guard funcionando.
- **H4 actividad real coordinada → REFUTADA**. Llaima fue el único con cluster
  contiguo real (Test 1 triggered). Los otros 5 tenían BTs sub-285 K (lava real
  daría >320 K en MIR). No es sismológicamente plausible.
- **H1 cirrus extendido → CONFIRMADA (causa física)**.
  - `t_bg ≈ 262-275 K` en los 6 volcanes a 600 km de distancia mutua.
  - `sigma_bg_k` 5-9 K (terreno + cirrus heterogéneo).
  - `diag_eff_threshold_k` 290-299 K queda alto pero el Path D contextual
    (`diag_n_dnti_ctx_path` 35-286 píxeles) pesca pixels relativamente "menos
    fríos" que el background regional deformado.
  - Path D dispara aún cuando los BTs absolutos son sub-volcánicos.
- **H3 bug pipeline → CONFIRMADA (causa estructural)**. La causa raíz física
  es H1; el síntoma `vrp_mw=510 MW` es un bug arquitectural: existe
  `PATH_D_ONLY_CAP_MW = 5.0` (S71 D9 Opción C, perfil `mirova_equivalent.yaml`)
  pero **solo se aplica a `primary_cluster.vrp_mw`, no al `vrp_mw` scene-wide**.

---

## 3. Causa raíz estructural (H3 detallada)

`pipeline/process_modis.py:693-700` define `_path_d_cap_active = True` cuando:

- `n_bt_path == 0` (ningún píxel disparado por BT absoluto, S58 Path A)
- `n_nti_path == 0` (ningún píxel disparado por NTI absoluto, S58 Path B)
- `t_bg < PATH_D_ONLY_CAP_TBG_MAX_K` (270 K en perfil actual → cirrus marker)
- `PATH_D_ONLY_CAP_MW is not None` (5.0 MW)

Cuando el predicado es True, líneas 802-803 (eruption) y 1017-1018 (Test 1
recompute) capean **`primary_cluster.vrp_mw`** a 5.0 MW y marcan
`d9_capped: true`.

Sin embargo, líneas 707 y 753:

```python
vrp_mw = 0.0
# ...
delta_L = np.maximum(hotpix_rad - L_bg, 0.0)
per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
vrp_mw = float(np.nansum(per_pixel_vrp_mw))   # ← suma scene-wide, sin cap
```

`vrp_mw` agrega todos los píxeles `hot_mask_2d` (Path D contextual incluido),
sin ningún filtro adicional ni gate de plausibilidad térmica, y sin
re-aplicar el cap D9. Bajo cirrus puro, 83-556 píxeles fríos (270-285 K)
producen un `delta_L` modesto pero distinto de cero que × `WOOSTER_COEFF=18.9`
× `hotpix_area≈10⁶ m²` × 83 píxeles → ~80-510 MW falsos.

**Diferencia conceptual**: `primary_cluster.vrp_mw` ya está corregido por D9
para no inflar la "anomalía detectada del volcán". `vrp_mw` scene-wide debería
ser una suma diagnostica pero el dashboard y los downstream consumers usan
`vrp_mw` como métrica primaria de actividad — el cap D9 quedó incompleto.

---

## 4. Scope del bug (¿solo este granule?)

**Sistémico**, no aislado al granule 07:25. Scan sobre `data/mirova_equivalent/`:

- **715 records totales** con el patrón
  (`t_bg < 270` + `n_bt_path==0` + `n_nti_path==0` + `n_dnti_ctx_path>20` +
  `vrp_mw>50` + `vrp_mw > 5×primary_cluster.vrp_mw`).
- **Por sensor**:
  - MODIS_AQUA: 331
  - MODIS_TERRA: 290
  - VIIRS_NOAA21_750: 45
  - VIIRS_SNPP_750: 25
  - VIIRS_NOAA20_750: 18
  - VIIRS_NOAA21: 3
  - VIIRS_SNPP: 2
  - VIIRS_NOAA20: 1
- **Por volcán**: Tupungatito 114, PuyehueCordonCaulle 107, Lastarria 105,
  Chaiten 79, Lascar 62, Villarrica 49, PlanchonPeteroa 48, Isluga 44,
  NevadosDeChillan 37, Llaima 35, Copahue 35.
- **Top outliers**: Villarrica 2026-01-31 06:35 MODIS_AQUA `vrp_mw=1288 MW`
  con `primary_cluster.vrp_mw=141.95 MW` y `t_bg=268.3 K`.
- VIIRS sufre el mismo patrón (`process_viirs.py:1018-1024`,
  `process_viirs_mod.py:768-774`): el cap D9 también solo aplica a
  `primary_cluster`.

Equivale a F46 (bug VIIRS I-band `vrp_tir_mw` Stefan-Boltzmann sobre 4σ-mask
sin gate de consistencia) trasladado a la suma `vrp_mw` Wooster con `hot_mask`
inflado por Path D contextual bajo cirrus.

---

## 5. Recomendación (no implementar sin A45 de Nicolás)

Cuatro opciones, ordenadas de menos a más invasivas:

**A. Extender D9 cap a `vrp_mw` scene-wide** (mínimo).
Una línea en process_modis.py:753 y simétricas en process_viirs.py / viirs_mod.py:

```python
vrp_mw = float(np.nansum(per_pixel_vrp_mw))
if _path_d_cap_active and vrp_mw > PATH_D_ONLY_CAP_MW:
    vrp_mw = PATH_D_ONLY_CAP_MW
```

Conserva semántica D9 (cirrus → señal capped 5 MW). Borra los outliers de
golpe pero también colapsa eventos reales que casualmente caen bajo
`t_bg < 270 K` sin disparar BT/NTI duro (raro pero no imposible: invierno
nocturno con cirrus + débil lava lake).

**B. Gate de plausibilidad térmica per-píxel** (físicamente más limpio).
Antes de sumar a `vrp_mw`, filtrar `per_pixel_vrp_mw` exigiendo
`hotpix_bt[idx] >= max(t_bg + N·sigma_bg, MIR_MIN_HOT_BT_K)` con
`MIR_MIN_HOT_BT_K ≈ 295-300 K` (umbral físico para lava). Coppola 2016a Table 2
usa thresholds absolutos para Path A. Aquí lo aplicaríamos como **gate de
plausibilidad sobre la SUMA**, no para detección. Mantiene el cluster D9 y
solo descuenta los píxeles contextual sin firma térmica volcánica.

**C. Reportar `vrp_mw_path_d_only` como campo aparte** (más conservador).
No tocar `vrp_mw` actual; agregar `vrp_mw_excl_path_d = sum(per_pixel donde
disparó BT o NTI duros)`. Dashboard cambia el campo que consume. Preserva
contrato histórico de `vrp_mw` pero requiere doble migración (pipeline +
frontend) y dejaría 715 records "raros" en el JSON hasta el reproceso.

**D. Cluster-only reporting** (más alineado con MIROVA).
Hacer `vrp_mw := primary_cluster.vrp_mw` y mover la suma scene-wide a
`vrp_mw_scene_total` (diagnostic). Coppola 2016a reporta cluster-based VRP,
no scene-wide. Esto es lo más cercano al espíritu MIROVA pero rompe contratos
históricos del dashboard y de auditorías A/B previas.

**Mi recomendación operacional**: combinar **A + B** en un fix bite-sized,
con flag `enable_path_d_scene_cap` default True solo en `mirova_equivalent`.
Mantener un perfil `experimental_path_d_uncapped` para auditoría.

Antes de implementar:

1. Pasar las 3 preguntas de `docs/MISSION.md` (clon MIROVA literal).
2. Revisar si MIROVA reporta `vrp_mw` scene-wide o cluster-only (probablemente
   cluster-only — esto refuerza la opción D como tarea ulterior).
3. Definir si el reproceso histórico (715 records) corre en GitHub Actions
   matrix o en local (regla A2 — 715 records >> 1 día, debe ser local).

---

## 6. Caveat operacional inmediato (mientras no haya fix)

El dashboard `frontend/index.html` ya hardenea `pc.vrp_mw > 50K` (F2.8) pero
no filtra `vrp_mw` scene-wide en el rango 50-2000 MW (cirrus territory).
Recomendado en lo inmediato (no requiere A45 porque es frontend-only y
visual):

- Mostrar warning visual en cards/sparklines cuando
  `vrp_mw > 10 × primary_cluster.vrp_mw` y `t_bg_k < 270`. Etiqueta tipo
  "posible contaminación por cirrus".
- Alternativamente, usar `primary_cluster.vrp_mw` como métrica primaria de
  display y `vrp_mw` solo como tooltip diagnostic.

---

## 7. Referencias

- `pipeline/process_modis.py:670-1032` (Path D cap + vrp_mw scene-wide suma)
- `pipeline/process_viirs.py:615-1442` (mismo patrón)
- `pipeline/process_viirs_mod.py:768-849` (mismo patrón)
- `pipeline/profiles/mirova_equivalent.yaml:284-285` (`path_d_only_cap_mw: 5.0`,
  `path_d_only_cap_tbg_max_k: 270.0` — S71 D9 Opción C)
- F46 (precedente directo, VIIRS I-band Stefan-Boltzmann)
- F2.8 saturation guard PR #133 (precedente filosófico: defensa de extracción)
- CLAUDE.md A45 (regla sobre cambios en pipeline NRT crítico)

---

## 8. Próximo paso

PR documental sin tocar pipeline. Cuando Nicolás dé A45 sobre el fix:

1. Tag defensivo `pre-f50-path-d-scene-cap` apuntando a HEAD actual.
2. Worktree dedicado `VRP-Chile-s78-f50-fix`.
3. Plan bite-sized con `writing-plans` (opción A+B).
4. Tests unitarios sintéticos primero (`test-driven-development`): granule
   sintético con cirrus + 0 píxeles hot reales debe dar `vrp_mw ≤ 5 MW`.
5. Implementar fix en los 3 procesadores simétricamente.
6. Reproc local de los 715 records identificados + diff vs baseline.
7. Push + PR con métrica before/after por volcán.
