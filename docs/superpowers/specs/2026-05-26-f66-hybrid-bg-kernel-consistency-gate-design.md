---
title: "F66 híbrido — Dual-bg consistency gate"
session: S79
status: draft (pending Nicolás approval)
author: Claude (vía superpowers-brainstorming gate)
ai_generated: true
confidence: medium
explored: true
tags:
  - design
  - pipeline
  - bg-kernel
  - lagos
  - mirova-faithful
related:
  - docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md
  - docs/F64_NTI_METHOD_BRAINSTORM_S78.md
  - docs/F65_APPROACHES_ALTERNATIVOS_S78.md
  - docs/MIROVA_DETAILED_CITATIONS.md
  - docs/MISSION.md
  - pipeline/vrp_regimes.py
  - pipeline/detection_context.py
  - pipeline/process_modis.py
  - pipeline/process_viirs.py
  - pipeline/process_viirs_mod.py
---

# F66 híbrido — Dual-bg consistency gate

## 1. Contexto y motivación

### Fenómeno físico

VRP Chile clon MIROVA tiene falsos positivos persistentes en pixels asociados a
cuerpos de agua térmicamente "tibios" rodeados de terreno frío:

- **Caviahue / Laguna del Agrio (Copahue)**: ~14 km SE del vent, lago a 280-285 K
  rodeado de nieve/roca a 265-270 K.
- **Lago Conguillío (Llaima)**: idem.
- **Lacolito PCC (PuyehueCordonCaulle)**: 15-20 km del cráter principal.
- **Salar de Atacama (Lascar)**: halo halita con retención térmica.
- **Glaciar Tupungatito**: hielo parcialmente sublimado.

El pixel "lago" o "Salar" parece caliente al pipeline porque su firma BT en MIR
nocturno excede al background (ring 5-25 km median, mayoritariamente terreno
seco frío). Pero **localmente, ese pixel es indistinguible de sus vecinos** —
no es una anomalía espacial real, es retención térmica natural.

MIROVA NO confunde estos cuerpos de agua con anomalías térmicas. La razón
documental está en los papers canónicos:

| Paper | Cita verbatim | Implicación |
|---|---|---|
| Coppola 2024 chapter (Springer) L1129 | "If T_bk is retrieved from the **pixels adjacent to the hot one**..." | bg local |
| Coppola 2016a SP426.5 L357-359 | "L4_bk is estimated from the arithmetic mean of all the **pixels surrounding the active one** (or around the active cluster)" | bg local |
| Campus 2024 VIIRS 375m L119-124 | "...computed from the arithmetic mean of the radiance of the pixels surrounding the alerted one(s)" | bg local per-pixel + sum |

**MIROVA usa background local** (vecinos inmediatos). Nuestro pipeline usa
background ring annular 5-25 km (heredado de paradigma "scene-wide statistics"
de sistemas NO MIROVA como NHI/RSDF Catania). Es un drift documental real,
catalogado en `docs/MIROVA_DETAILED_CITATIONS.md §1`.

### Reframe físico clave (descubierto en brainstorming S79)

Una hipótesis tentadora (F61 / F65 TOP 1) era "agregar un threshold NTI absoluto
estricto para descartar agua". F64 demostró que **destruye 98% de los TPs
reales** porque en volcanes andinos chilenos nocturnos los TPs reales tienen
NTI=-0.88 a -0.95 por física pura del cuerpo negro (t_bg 250-270 K, t_hot
285-295 K).

Inspeccionando el código (S79 brainstorming) descubrí que **Path B (NTI absoluto
`nti > -0.8`) jamás dispara para estos volcanes**:

| Path | Trigger | TPs Tier A operacional |
|---|---|---|
| A (BT puro) | bt > t_bg + N·σ | 107/8,142 (1.3%) |
| B (NTI absoluto) | nti > -0.8 | **0/8,142 (0%)** |
| D (dNTI contextual 8-vec) | dnti > C1 | **7,070/8,142 (88%)** |
| Test 1 (integrated ROI) | ΔL_ROI > k_test1 | 4,060/8,142 (51%) |

Tanto los TPs reales como los FPs lago entran al `hot_mask` vía **Path D dNTI
contextual** o Test 1 integrated. Ambos paths usan el background ring para
computar el threshold y para el `L_bg` de Wooster, así que el drift bg-kernel
afecta ambos.

### Por qué F65 TOP 1 (NTI threshold per-vol) era un noop

F65 TOP 1 propone "calibrar threshold NTI per-volcán contra distribución de
calma". Esto modifica el `NTI_K1_NIGHT` que se usa **solo en Path B**. Como
Path B nunca dispara en estos volcanes, el cambio es noop sobre TPs y noop
sobre FPs.

Hay un sub-uso adicional de `NTI_K1_NIGHT`: la exclusión de pixels "Test 1
active" del cómputo del background. Eso sí podría mover algo, pero el flag
`enable_test1_k1_bg_exclude` ya existe y es ortogonal al drift bg-kernel.

**Conclusión**: F65 TOP 1 ataca el path equivocado. El bug raíz es el background
ring vs kernel local, no el threshold NTI absoluto.

---

## 2. Solución: F66 híbrido (dual-bg consistency gate)

### Idea

Mantener el cómputo actual `t_bg_ring, std_bg_ring` (gate de detección y `L_bg`
de Wooster vienen del ring) y **agregar un gate de consistencia secundario**:
para cada pixel que el ring marcó como hot, computar adicionalmente `t_bg_local`
con `compute_local_background` (kernel 3×3, función ya existente en
`pipeline/vrp_regimes.py:21`). Solo aceptar el pixel si **ΔT_local =
bt - t_bg_local ≥ DT_MIN**.

### Pseudocódigo

```python
# En process_modis.py / process_viirs.py / process_viirs_mod.py
# ... existing flow hasta hot_mask computado por gates Path A/B/C/D/Test1 ...
hot_mask_ring = ...  # gate actual sin cambios

if PROFILE.get("enable_bg_kernel_consistency_gate", False):
    DT_MIN = PROFILE.get("kernel_consistency_dt_k", 5.0)  # default = anomaly_threshold_k
    KERNEL = PROFILE.get("kernel_consistency_size", 3)    # default 3×3 = 8-conn

    hot_rows, hot_cols = np.where(hot_mask_ring)
    t_bg_locals = compute_local_background(
        bt, hot_rows, hot_cols, kernel_size=KERNEL
    )  # NaN cuando todos los vecinos son hot o NaN
    delta_t_local = bt[hot_rows, hot_cols] - np.asarray(t_bg_locals)

    # Política edge case: si t_bg_local es NaN → fallback al ring (no vetar)
    nan_fallback = np.isnan(delta_t_local)
    passes = (delta_t_local >= DT_MIN) | nan_fallback

    hot_mask_consistent = np.zeros_like(hot_mask_ring)
    hot_mask_consistent[hot_rows[passes], hot_cols[passes]] = True
    hot_mask = hot_mask_ring & hot_mask_consistent  # ← AND con gate consistencia
else:
    hot_mask = hot_mask_ring  # comportamiento actual
```

### Por qué funciona (escenarios físicos)

| Escenario | Pixel BT | Vec 3×3 BT | t_bg_local | ΔT_local | Resultado |
|---|---:|---:|---:|---:|---|
| Lago Caviahue uniforme | 279 K | 278 K | 278 K | 1 K | **Vetado** ✓ |
| Lago Caviahue borde (mitad lago/orilla) | 279 K | 274 K (mix) | 274 K | 5 K | Borderline ⚠️ |
| Cráter Villarrica lava lake sub-pixel | 285 K | 270 K | 270 K | 15 K | **Válido** ✓ |
| Lava extendida grande (vecinos también hot) | 320 K | excluidos | NaN | NaN→fallback | Válido (ring decide) ✓ |
| Cirrus dispersa | 295 K | 245 K (cirrus) | 245 K | 50 K | Válido pero cap D9=5MW limita VRP ✓ |
| Salar borde halita caliente | 280 K | 277 K (Salar) | 277 K | 3 K | **Vetado** ✓ |
| Pixel borde ROI con vecinos NaN | 285 K | mayoría NaN | NaN | NaN→fallback | Válido (ring decide) ✓ |

**Justificación trade-off lava lake borderline**: si el lava lake real Villarrica
fuera muy débil (BT=275K, vec=270K → ΔT=5K), pasa justo el threshold. Si está
más débil aún (BT=273K, vec=270K → ΔT=3K), lo perdemos. Es un FN aceptable
porque MIROVA tampoco vería ese pixel (su threshold "ΔL > C1 = 0.003" implica
ΔT efectivo similar). Confirmar empíricamente en validación.

---

## 3. Cambios en código

### 3.1 `pipeline/detection_context.py` (sin cambios)

`compute_bg_stats` se mantiene intacta. El gate ring sigue igual.

### 3.2 `pipeline/vrp_regimes.py` (sin cambios)

`compute_local_background` ya está implementada correctamente (líneas 21-110).
Solo la reutilizamos.

### 3.3 `pipeline/process_modis.py` (cambio ~15 líneas)

Agregar después del bloque que computa `hot_mask` final (línea ~411-430):

```python
# F66 dual-bg consistency gate (S79, design doc 2026-05-26)
# Filtra pixels donde el "calor" es un artefacto del background ring
# (lago tibio rodeado de terreno frío distante) vs señal espacial real.
from pipeline.vrp_regimes import compute_local_background

if profile.enable_bg_kernel_consistency_gate:
    hot_rows_arr, hot_cols_arr = np.where(hot_mask)
    if hot_rows_arr.size > 0:
        t_bg_locals = compute_local_background(
            bt, hot_rows_arr.tolist(), hot_cols_arr.tolist(),
            kernel_size=profile.kernel_consistency_size,
        )
        t_bg_locals_arr = np.asarray(t_bg_locals)
        delta_t_local = bt[hot_rows_arr, hot_cols_arr] - t_bg_locals_arr
        nan_fb = np.isnan(t_bg_locals_arr)
        passes = (delta_t_local >= profile.kernel_consistency_dt_k) | nan_fb
        hot_mask_new = np.zeros_like(hot_mask)
        hot_mask_new[hot_rows_arr[passes], hot_cols_arr[passes]] = True
        n_vetoed = int((~passes).sum())
        hot_mask = hot_mask & hot_mask_new
        # Persistir diagnóstico
        record_diag["f66_n_pixels_vetoed"] = n_vetoed
        record_diag["f66_n_pixels_evaluated"] = int(hot_rows_arr.size)
```

Idéntico para `process_viirs.py` y `process_viirs_mod.py` (mismo patrón).

### 3.4 `pipeline/profile.py` (cambio ~10 líneas)

Agregar 3 nuevos campos al `_PROFILE` parsing:

```python
# F66 dual-bg consistency gate (S79)
enable_bg_kernel_consistency_gate: bool = bool(
    _t.get("enable_bg_kernel_consistency_gate", False)
)
kernel_consistency_dt_k: float = float(
    _t.get("kernel_consistency_dt_k", _t.get("anomaly_threshold_k", 5.0))
)
kernel_consistency_size: int = int(_t.get("kernel_consistency_size", 3))
```

Default OFF en mirova_equivalent. Se activa solo en profiles dedicados.

### 3.5 Profile dedicado nuevo `pipeline/profiles/_f66_dt5k.yaml`

```yaml
extends: mirova_equivalent

profile: _f66_dt5k
description: >
  F66 híbrido dual-bg consistency gate ON con threshold 5K (= anomaly_threshold_k).
  Test S79: validar reducción FPs lago Copahue/Llaima/Villarrica sin
  perder TPs reales.
data_subdir: f66_dt5k

thresholds:
  enable_bg_kernel_consistency_gate: true
  kernel_consistency_dt_k: 5.0
  kernel_consistency_size: 3
```

### 3.6 `volcanoes.yaml` (sin cambios)

El gate aplica a todos los volcanes uniformemente. Si Fase 2 requiere
per-vol tuning, agregaremos `kernel_consistency_dt_k` per-vol entonces.

---

## 4. Edge cases y políticas

| Edge case | Política | Razón |
|---|---|---|
| Vecinos 3×3 todos NaN (pixel borde imagen) | Fallback ring (no vetar) | Sin info para decidir; ring conserva recall |
| Vecinos 3×3 todos hot (lava extendida grande) | Fallback ring (no vetar) | Cluster real grande; ring ya validó; second-pass S46 ya excluye active del bg |
| Algunos vecinos NaN, otros válidos | Usar válidos (≥1 vecino) | `compute_local_background` ya maneja esto |
| Pixel hot solo por Test 1 (integrated, no spatial) | Mismo gate aplica | Test 1 también puede inflar con bg ring contaminado |
| Pixel `distance_class=summit` (dentro inner_radius) | Mismo gate (no excepción) | Lago Caviahue está a 14km SE del vent — el inner_radius=4 Copahue ya lo excluye del summit, pero validar caso |
| dNTI dual-ROI ya tiene su propio kernel | Mantener (ortogonal) | F66 actúa sobre bg de detección espectral, dNTI sobre NTI residual |

---

## 5. Tests sintéticos (TDD obligatorio antes de implementación)

`tests/test_f66_bg_kernel_consistency.py` con escenarios canónicos:

```python
def test_lake_uniform_vetoed():
    """Lago Caviahue uniforme: ΔT_local ≈ 0 → vetado."""
    bt = np.full((10, 10), 278.0)  # lago uniforme
    bt[5, 5] = 279.0  # pixel central marginalmente más cálido
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True
    # apply F66 gate with dt_k=5.0
    # expect: hot_mask_final[5, 5] == False

def test_lava_lake_sub_pixel_passes():
    """Lava lake Villarrica sub-pixel: vecinos fríos, ΔT_local >> 5 → válido."""
    bt = np.full((10, 10), 270.0)  # roca/nieve fría
    bt[5, 5] = 285.0  # pixel central con lava lake sub-pixel
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True
    # apply F66 gate with dt_k=5.0
    # expect: hot_mask_final[5, 5] == True (ΔT=15K >> 5K)

def test_extended_lava_fallback():
    """Lava extendida 5×5 hot: todos vecinos hot → NaN → fallback ring (válido)."""
    bt = np.full((10, 10), 270.0)
    bt[3:8, 3:8] = 320.0  # cluster 5×5 lava extendida
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[3:8, 3:8] = True
    # apply F66 gate
    # expect: hot_mask_final preserves all 25 hot pixels (NaN fallback)

def test_cirrus_dispersed_passes_capped():
    """Cirrus fría con cráter caliente: ΔT_local exagerado pero cap D9 limita VRP."""
    # Verificar que gate F66 NO veta este caso (es válido)
    # El cap D9=5MW del profile maneja el VRP inflado

def test_border_pixel_nan_fallback():
    """Pixel en (0, 0) con vecinos fuera de la imagen: NaN → fallback ring."""
    bt = np.full((10, 10), 270.0)
    bt[0, 0] = 285.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[0, 0] = True
    # apply F66 gate
    # expect: hot_mask_final[0, 0] == True (NaN fallback)

def test_salar_lascar_partial_vetoed():
    """Salar borde halita: vecinos mitad Salar mitad roca, ΔT_local borderline."""
    bt = np.full((10, 10), 270.0)
    bt[3:6, 3:6] = 277.0  # halita Salar
    bt[4, 4] = 280.0  # pixel central marginalmente más
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[4, 4] = True
    # apply F66 gate with dt_k=5.0
    # expect: hot_mask_final[4, 4] == False (ΔT=3K < 5K)

def test_dnti_dual_roi_compat():
    """Verificar que F66 no rompe dNTI dual-ROI Path D existente."""
    # End-to-end test: hot_mask post-Path D → F66 gate → verificar coherencia
```

Total: 7 tests sintéticos cubriendo los escenarios físicos canónicos.

---

## 6. Plan validación empírica

### Fase 1 (esta sesión)

1. **Tests sintéticos verdes** (todos los 7 arriba).
2. **Profile A/B**: `_f66_dt5k.yaml` con `data_subdir: f66_dt5k`.
3. **Reproc 30d × 3 vol crítico** (Copahue, Llaima, Villarrica) — VIIRS-only
   por constraint Windows (pyhdf roto). Serial (A47, NO paralelo sobre data/).
4. **Audit comparativo** `data/f66_dt5k/` vs `data/mirova_equivalent/`:
   - `n_records_f66 / n_records_mirova_eq` (recall preservado?)
   - `n_far_30d_f66 / n_far_30d_mirova_eq` (FPs lago reducidos?)
   - Distribución `vrp_mw` (no inflada, no excesivamente atenuada)
   - Match contra `latest_consolidado.csv` (MIROVA NRT) — recall por volcán
5. **Validación pixel-level R2** (regla CLAUDE.md S33): 5 records canónicos por
   volcán, comparar pixel-por-pixel con MIROVA web (mirovaweb.it).

### Métricas de éxito Fase 1

Para mergear a `mirova_equivalent`:

- **Recall preservado**: vs `latest_consolidado.csv` ≥ recall pre-F66 - 5%.
- **FPs lago reducidos**: `n_far_30d` Copahue/Llaima ≤ 50% del pre-F66.
- **Ratio VRP estable**: mediana `vrp_mw / vrp_mw_mirova` cambia <30%.
- **R2 pixel-level**: ≥4/5 records por volcán coinciden con MIROVA web.

### Fase 2 (opcional, si Fase 1 deja residual)

Si reducción FPs lago <30% en Fase 1, clonar el profile a:
- `_f66_dt3k.yaml` (threshold más permisivo)
- `_f66_dt_2sigma.yaml` (adaptativo σ_local)
- `_f66_per_vol.yaml` (per-volcán calibrado)

Reproc paralelo (serial por A47) sobre mismos 3 vol × 30d. Análisis
comparativo. Elegir ganador.

### Fase 3 (rollout)

Merge a `mirova_equivalent` con flag `enable_bg_kernel_consistency_gate: true`
y `kernel_consistency_dt_k: <ganador>`. NRT cron empieza a aplicar el gate
automáticamente sobre nuevos granules.

Reproc histórico mirova_equivalent NO necesario inmediato (puede correrse
después para limpieza visual; dashboard refleja gradualmente nuevos records
con el gate aplicado).

---

## 7. Riesgos y mitigación

| Riesgo | Probabilidad | Mitigación |
|---|:---:|---|
| Destruir TPs lava lake Villarrica sub-pixel | Baja | Tests sintéticos cubren caso BT=285K vec=270K → ΔT=15K pasa cómodo. Si en validación ΔT real <5K, ajustar threshold a 3K |
| Exacerba cirrus dispersa (vecinos cirrus aún más fríos) | Alta (en escenario) | Cap D9=5MW S71 ya activo. F66 doc anticipa este caso. Validación monitorea outliers VRP |
| PCC lacolito legitimate signal vetoed | Media | El lacolito está a 15-20 km del cráter. Validar con MIROVA web archivo. Si MIROVA lo reporta como TP y nosotros lo vetamos, ajustar (per-vol exception) |
| Bug en `compute_local_background` con vecinos hot | Baja | Función ya existente, ya tested para L_bg Wooster, recall S57+. Reutilización es low risk |
| Performance impact (compute extra per pixel) | Baja | `compute_local_background` es ya O(N) en hot pixels. Granule típico tiene <100 hot pixels. Costo ~1-5 ms por granule |
| NRT cron rompe semánticas inesperadas | Crítica si pasa | A45 estricto: profile aislado en Fase 1+2, NO toca mirova_equivalent hasta Fase 3 con evidencia. Tag defensivo + confirmación Nicolás antes de cada paso |

---

## 8. Rollback plan

Si Fase 1 muestra resultados negativos:

1. **No mergear PR**. Branch `claude/s79-f66-hybrid-bg-gate` queda colgado;
   `data/f66_dt5k/` queda como archivo histórico A/B.
2. Documentar en `docs/F66_RESULTS_S79.md` los hallazgos negativos.
3. Pivot a Fase 2 con threshold distinto, o pivotar a F65 TOP 2 (sensor fusion).

Si Fase 3 (rollout) muestra problemas post-merge:

1. Tag defensivo `pre-s79-f66-rollout` cubre rollback git.
2. `git revert` del commit de Fase 3.
3. NRT cron vuelve a comportamiento pre-F66 en próxima ventana 2h.
4. `data/mirova_equivalent/` queda con records mezclados (pre-rollout + post-rollback) — opcional reproc 30d para limpieza visual.

---

## 9. Decisiones pendientes (gating points)

Cada decisión requiere aprobación explícita de Nicolás (A45):

- [x] Approach: F66 híbrido dual-bg consistency (aprobado S79 brainstorming).
- [x] Kernel: 3×3 (8-conn, MIROVA-faithful via Coppola 2016a dNTI).
- [x] Threshold: 5K (reutilizar `anomaly_threshold_k`).
- [x] Scope: profile aislado `_f66_dt5k.yaml` con `data_subdir: f66_dt5k`.
- [ ] **Aprobación del diseño completo** (este doc) — gating point antes de implementación.
- [ ] **Tag defensivo `pre-s79-f66-hybrid`** + push (antes de implementación).
- [ ] **Confirmación final** antes de Fase 3 rollout a mirova_equivalent operacional.

---

## 10. Próximos pasos post-aprobación

Una vez Nicolás apruebe este doc:

1. Invocar skill `writing-plans` para plan bite-sized de implementación.
2. Tag defensivo `pre-s79-f66-hybrid` apuntando a `origin/main` (= `9d4dd082`).
3. Skill `test-driven-development` para los 7 tests sintéticos (rojos primero).
4. Implementar cambios en `process_*.py` + `profile.py` + profile yaml.
5. Tests sintéticos verdes.
6. Reproc Fase 1 (3 vol × 30d × 1 profile = ~30 min wall clock).
7. Audit comparativo + R2 pixel-level.
8. PR con resultados + decisión Fase 2/3.

---

## 11. Sanity check final (self-review obligatorio del skill brainstorming)

### Placeholders / TODO no resueltos
Ninguno. Todos los valores numéricos definidos. Todos los archivos identificados
con paths absolutos. Default threshold = `anomaly_threshold_k` evita
"magic number" sin justificación.

### Contradicciones internas
Ninguna. El doc reconoce el trade-off lava lake borderline (sección 2 tabla) y
plantea Fase 2 si Fase 1 lo confirma como FN.

### Ambigüedad
- "Lava extendida grande" en Edge cases: definida operacionalmente como
  "todos los 8 vecinos también flagged como hot por hot_mask_ring".
- "Borderline" en lago borde: caso explicado, threshold 5K lo limita; si
  validación muestra que cae demasiado seguido, Fase 2 ajusta.

### Scope (YAGNI ruthless)
- NO incluye migración comprehensiva del bg ring a kernel local (Approach
  comprehensive de F66 doc). Eso es S80+ si Fase 1+2 dejan residual.
- NO incluye per-vol calibration (Fase 2 si necesario).
- NO incluye sensor fusion (Approach C F65). Ortogonal.
- NO incluye refactor compute_bg_stats. Aditivo solo.

### MIROVA-faithful audit
- Kernel 3×3 = Coppola 2016a L240-249 verbatim (dNTI/dETI).
- Background local = Coppola 2024 chapter L1129 verbatim.
- Dual-bg como "gate consistency" es extensión defensiva, NO migración —
  preserva el comportamiento histórico (ring) y solo agrega filtro.
- Justificable como "implementación parcial F66 comprehensive con safety
  rollback inmediato vía profile flag".

### Reglas CLAUDE.md compliance
- A44 worktree dedicado: ✓ `../VRP-Chile-s79-f66/`.
- A45 tag defensivo + confirmación Nicolás antes de pipeline: ✓ planeado paso 2.
- A47 NO paralelo sobre data/: ✓ reproc serial planeado.
- R1 tests sintéticos antes de TDD: ✓ 7 escenarios canónicos especificados.
- R2 pixel-level vs MIROVA: ✓ obligatorio en métricas éxito.
- R3 audit independiente: ✓ planeado post-implementación.
- Misión "clon literal MIROVA": ✓ kernel 3×3 verbatim Coppola, bg local verbatim
  Coppola.
- Comunicar como geólogo: ✓ secciones 1, 2, 4 (escenarios físicos primero).

### Confidence assessment
**Medium-high**. Aprobado el bug raíz (F66 doc S78), aprobado el approach
(F66 híbrido), código base existente (`compute_local_background` ya tested).
Confidence baja del 100% por el caveat del lava lake borderline que requiere
validación empírica en Fase 1. Si validación positiva → high. Si negativa →
Fase 2 con threshold ajustado.
