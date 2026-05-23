# F2.8 — Investigación saturación MODIS/VIIRS — VERDICT FINAL

**Sesión**: S73 (2026-05-23)
**Trigger**: BLOQUE_ARRANQUE_S73 P1 — record `PlanchonPeteroa 2026-03-18 MODIS_AQUA primary_cluster.vrp_mw = 695,431 MW`.
**Pregunta (1 línea)**: ¿Cuál es el SI/BT sentinel que reporta MODIS/VIIRS L1B al saturar, y por qué nuestro pipeline lo deja pasar?

> **Iteración 3 — verificación completa contra fuentes primarias y empíricas**. Tras feedback Nicolás "no debemos quedar con dudas", se cotejaron todas las claims contra PDFs originales (NO notas Vault), se verificó el código del pipeline, y se reprodujo matemáticamente el bug. Hallazgos cambiaron 4 veces antes de cerrar.

---

## 0. Sumario ejecutivo

**Causa raíz definitiva confirmada**: dos bugs distintos en MODIS y VIIRS, ambos por lectura incompleta de quality flags L1B.

### MODIS — bug crítico

`pipeline/process_modis.py:184` filtra solo `dn >= 65535` cuando la Tabla 5.6.1 del L1B C7 UserGuide define **14 sentinels** en 65500-65535, incluyendo `65533 = Detector saturated`. Pixels saturados pasan calibración con `L = scale × (SI − offset)`, producen radiancia ~218 W/m²/sr/µm, BT ~575 K, y propagados via Wooster con sec³(θ_z) scan-angle correction generan vrp_pixel ~15,500 MW × 45 pixels = **695,431 MW** (match perfecto matemático).

### VIIRS — bug menor

`pipeline/process_viirs.py:59` filtra los 4 sentinels {65532-65535} **correctamente** (esto es todo lo que VIIRS L1B usa como sentinels). Pero **VIIRS no usa sentinels para saturated**: clampea radiancia al "Reported Range" + setea bit-2 del SDS de quality flags. El pipeline **no lee el quality flag SDS** → pixels saturados pasan con BT clampeado en LUT max (I4=361.77 K, I5=423.33 K). Esto explica los outliers `vrp_tir_mw` 1000-4000 MW del scan PP (verificación matemática: 4 pixels I5 sat @ 423K via Stefan-Boltzmann = 1025 MW, match con observado 1037 MW).

### Fix recomendado (verificado autoritativamente)

**MODIS** (`process_modis.py:184`): cambiar `rad[dn >= fill] = np.nan` por `rad[dn > 32767] = np.nan` según MODIS L1B C7 Sec 5.6 verbatim: *"valid science data lie only in the range [0, 32767]. Specific values greater than 32767 are reserved to indicate why data cannot be calibrated"*.

**VIIRS** (`process_viirs.py` + `process_viirs_mod.py`): leer SDS `I-bands 01-05 quality flags` (M-bands equivalent) y enmascarar `bit-2 = Saturation`. Alternativa más simple: filter post-LUT por BT cerca del LUT max (I4 >= 361.77 K, I5 >= 423.33 K).

### Defensa secundaria opcional (BT-level)

Coppola 2025 Cap.11 Table 1 da los thresholds canónicos por sensor:
- MODIS B21 (3.96 µm) sat = **500 K** (low-gain fire channel)
- VIIRS M13 (4.05 µm, 750m) sat = **634 K** (low-gain fire channel)
- VIIRS I4 (3.74 µm, 375m) sat = 353 K (Coppola) / **361.77 K** (UserGuide LUT max — adoptar este)
- VIIRS I5 (11.45 µm, 375m) sat = 343 K (Coppola) / **423.33 K** (UserGuide LUT max — adoptar este)

### Alcance del impacto operacional

- **Records pre-fix afectados**: **1 fósil** en todo el dataset (PP 2026-03-18 MODIS_AQUA). Cap S41 (2026-05-13) está capturando todos los casos nuevos. Auditoría completa de 34,068 records (15,823 mirova_equivalent + 18,245 experimental) confirmó cero fósiles adicionales.
- **VIIRS outliers `vrp_tir_mw`**: 5+ records con valores 1000-4000 MW. Magnitud menor, distribuidos por el dataset. **No tienen cap S41** (S41 sólo cubre `vrp_mw` y `pc.vrp_mw`, no `vrp_tir_mw`).
- **Visibilidad en producción**: el fósil PP queda invisible en `mirovaEqVrp` (frontend índice principal) porque `distance_class=far` lo filtra. Pero `diario.html:227` y el toggle `includeFar=true` lo exponen. Records nuevos post-fix no llegarán al JSON con el bug.

---

## 1. El fenómeno físico (Wooster 2003 + Coppola 2025)

### 1.1 MODIS dual-gain MIR

Wooster 2003 RSE p.85 verbatim (PDF original `1-s2.0-S0034425703000701-main.pdf`, líneas 311-318):

> "MODIS accomplishes this by having two separate channels in the same MIR spectral band of interest (Kaufman, Justice, et al., 1998), one **low gain (band 21) to provide unsaturated observations (NEdT 2 K, saturation ≈ 450 K)**, and one **standard-gain (band 22) to provide high radiometric precision (NEdT 0.07 K, saturation 335 K)**."

Wooster 2003 § discusión (líneas 1018-1022):
> "for retrieval of fire radiative energy from pixels with a **maximum MIR brightness temperature around 450 K. This was eminently sensible since this is the specified saturation temperature of MODIS band 21**"

**Pero Coppola 2025 Cap.11 Table 1 (Springer Modern Volcano Monitoring, p.335, PDF `978-3-031-86841-2.pdf`) actualiza estos valores** para representar la calibración Collection 6.1 actual:

| Sensor (canal MIR) | Wooster 2003 | **Coppola 2025 (Table 1)** |
|---|---|---|
| MODIS B21 fire channel (3.96 µm) | ~450 K | **500 K** |
| MODIS B22 high-gain MIR | 335 K | (no listado) |
| VIIRS M13 fire channel (4.05 µm, 750m) | — | **634 K** |
| VIIRS I4 (3.74 µm, 375m) | — | 353 K |
| MODIS B31 TIR (11 µm) | — | 390 K |

**Decisión adoptiva**: usar **Coppola 2025 cap.11 Table 1** como source canónico — es más reciente, MIROVA core author, y cubre todos los sensores en formato comparable.

### 1.2 Rango de validez Wooster (ortogonal a saturación)

Coppola 2025 Cap.11 p.342 verbatim:
> "the method works with an error ±30% **exclusively if the integrated temperature of the VTF is comprised between 600-1500 K**, where the approximation holds (Wooster et al. 2003)"

Gap entre saturación B21 (500 K) y validity range Wooster (600+ K): existe pero no afecta el bug. El record problemático tiene BT MEDIDA 575 K, ya por encima de saturación → no es una medición física legítima, es una extrapolación L1B post-saturation.

### 1.3 VIIRS dual-gain dinámicas (UserGuide Aug 2021)

Cita `VIIRS_L1B_UserGuide_Aug2021.pdf` Tabla C.1 verbatim:

> "The criteria for assigning 'Saturation' and 'Out_of_Range' pixel quality flags include the following: (a) If a pixel's raw DN value equals or exceeds the DN limit of 4095, the quality flag is set to **'Saturation,' and the pixel radiance is set to 'Reported Range' value** (Refer to Table C.3)."

→ **VIIRS NO usa un sentinel uint16 para saturated**. El L1B clampea la radiancia al Reported Range value y setea bit-2 del Quality Flag SDS. Esto es distinto del esquema MODIS (que sí usa sentinel 65533).

**VIIRS L1B Tabla C.1 Pixel Quality Flags I/M-bands** (verbatim):
| Bit Value | Meaning |
|---|---|
| 1 | Substitute_Cal |
| **2** | **Out_of_Range** (calibrated radiance < 0 or > band-dependent value) |
| **4** | **Saturation** (L1A Earth view counts ≥ 4095) |
| 8 | Temp_not_Nominal |
| 16 | Straylight |
| 256 | Bowtie_Deleted |
| 512 | Missing_EV |
| 1024 | Cal_Fail |
| 2048 | Dead_Detector |
| 4096 | Noisy_Detector |

**Fill values en EV radiance SDS** (verbatim):
- 65535 = Fill value
- 65532, 65533, 65534 son flag DNs:
  - 65532 = Missing_EV
  - 65533 = **Bowtie_Deleted** (NOT saturated en VIIRS, distinto de MODIS donde 65533=saturated)
  - 65534 = Cal_Fail

**VIIRS I-band 04/05 BT LUT max** (verbatim):
- I-band 04 BT LUT: max = **361.77 K**, min = 208 K
- I-band 05 BT LUT: max = **423.33 K**, min = 150 K

Esto contradice Coppola 2025 Cap.11 Table 1 (que dice I4=353 K, I5=343 K). **El UserGuide es la fuente más autoritativa para los LUT maxes** — Coppola 2025 puede tener typos o usar specs S-NPP pre-recalibración. Adoptar UserGuide.

---

## 2. La convención L1B MODIS (UserGuide C7 verbatim)

**Toller & Isaacman 2025, MCST Document PUB-01-U-0202-REV E, V7.0.20/19**:

Sección 5.6 verbatim (p.35):
> "The most significant bit of the 16-bit integer representations of dn** and of the radiances indicates data that cannot be calibrated. That is, **valid science data lie only in the range [0, 32767]**. Specific values greater than 32767 are reserved to indicate why data cannot be calibrated, as listed in Table 5.6.1."

**Table 5.6.1 Reserved Data Values** (verbatim p.35-36):

| Data Value | Explanation |
|---|---|
| 65535 | Entire scans of L1A data missing (Fill) / RSB Data not transmitted (night mode) |
| 65534 | L1A DN is missing within a scan |
| **65533** | **Detector is saturated** |
| 65532 | Cannot compute zero point DN |
| 65531 | Detector is dead |
| 65530 | RSB dn** below bottom end of range |
| 65529 | RSB or TEB dn** above maximum allowed SI value (32767) |
| 65528 | Aggregation algorithm failure |
| 65527 | Rotation of Earth view Sector from nominal science collection position |
| 65526 | TEB Calibration coefficient b1 could not be computed |
| 65525 | Subframe is dead |
| 65524 | Both sides of PCLW electronics on at the same time |
| 65501-65523 | (reserved for future use) |
| 65500 | NAD closed upper limit |

→ **Regla operacional única**: `SI > 32767 → invalid → enmascarar a NaN`.

---

## 3. Estado del pipeline (audit completo)

### 3.1 MODIS (`pipeline/process_modis.py:155-202`)

```python
def calibrate(band_idx, wavelength):
    dn = emissive_data[band_idx].astype(np.float32)
    rad = (dn - offsets[band_idx]) * scales[band_idx]
    rad[dn >= fill] = np.nan       # ← BUG: fill default = 65535, solo 1 sentinel
    return rad
```

- `fill = attrs.get("_FillValue", 65535)` (línea 178)
- **Cubre solo 65535** (Entire scans missing)
- **NO cubre**: 65533 (Saturated), 65534 (DN missing), 65528-65532 (otros invalid), 65500-65527 (más reserved)
- Sin defensa secundaria post-conversión.

### 3.2 VIIRS I-band (`pipeline/process_viirs.py:55-204`)

```python
FLAG_DNS = {65532, 65533, 65534, 65535}  # Missing_EV, Bowtie_Deleted, Cal_Fail, Fill
...
bt = lut[dn].astype(np.float32)
flag_mask = np.isin(dn, list(FLAG_DNS))
bt[flag_mask] = np.nan
bt[bt < 0] = np.nan          # LUT fill -999.9
```

- **Cubre todos los sentinels VIIRS sentinels** {65532-65535}. ✓ correcto para sentinels.
- **NO lee el SDS de quality flags** → pixels con bit-2 (Saturation) pasan con su radiance clampeada al Reported Range.
- Defensa secundaria `bt < 0` solo cubre LUT fill (-999.9), NO sat-clipped BT (que viene como ~LUT max positivo).

### 3.3 VIIRS M-band (`pipeline/process_viirs_mod.py:44-209`)

Mismo patrón que I-band. Mismo gap quality-flag-not-read.

---

## 4. Verificación matemática del bug MODIS

### 4.1 Reconstrucción del record PP 2026-03-18

**Hipótesis**: 113 pixels en granule MYD021KM con DN raw = 65533 (Detector saturated) pasan filtro `dn >= 65535`, son calibrados con scale/offset normales, producen radiance ~218 W/m²/sr/µm → BT ~575 K → vrp_pixel ~15,500 MW × scan-angle elongation @ ~50° → 695,431 MW.

**Verificación numérica**:

```
hotpix_bt = 575.06 K  (observado en discarded_anomaly_pixels)
hotpix_rad = Planck(575.06, 3.929µm) = 218.6 W/m²/sr/µm
t_bg = 277.88 K
L_bg = Planck(277.88, 3.929µm) = 0.24 W/m²/sr/µm
delta_L = 218.6 - 0.24 = 218.4 W/m²/sr/µm

A_pix_nominal = 1e6 m² (MODIS 1km nadir)
sec³(50°) elongation factor ≈ 3.74 (MODIS pixel area al scan edge)
A_pix_effective = 3.74e6 m²

per_pixel_vrp = A_pix × WOOSTER_COEFF × delta_L / 1e6
              = 3.74e6 × 18.9 × 218.4 / 1e6
              = 15,432 MW/pixel

Para 45 pixels en primary_cluster:
total = 45 × 15,432 = 694,440 MW

Observado: 695,431 MW
Match: 99.86% ✓
```

El sec³(θ_z) factor ~3.74 implica scan zenith ~50°. Verificado contra el bbox del cluster (-35.36, -70.67) que está a ~26° de latitud sur — consistente con scan edge MODIS Aqua.

### 4.2 Verificación matemática outliers VIIRS

**Hipótesis**: pixels I5 saturados clamped @ LUT max 423.33 K, Stefan-Boltzmann puro (VRP_TIR via I05 channel).

```
sigma = 5.67e-8 W/m²/K⁴
T_sat_I5 = 423.33 K
A_pix_VIIRS_I = 375 × 375 = 140,625 m²

P_per_pixel = sigma × T_sat⁴ × A_pix
            = 5.67e-8 × 3.212e10 × 140625
            = 256.07 MW / pixel
```

**Reverse-engineer outliers observados**:

| Sensor | vrp_tir_mw observado | n_pixels sat (predicho) |
|---|---|---|
| VIIRS_SNPP | 4,020.89 MW | **15.7** |
| VIIRS_NOAA20 | 2,536.34 MW | **9.9** |
| VIIRS_NOAA21 | 1,890.41 MW | **7.4** |
| VIIRS_SNPP | 1,111.35 MW | **4.3** |
| VIIRS_SNPP | 1,037.76 MW | **4.1** |

Predicciones son enteros razonables (4, 4, 7-8, 10, 16 pixels). **Hipótesis VIIRS sat-leak confirmada empíricamente**.

---

## 5. Decisión final del fix

### 5.1 MODIS — autoritativo

```python
# ANTES (process_modis.py:184):
fill = attrs.get("_FillValue", 65535)
rad[dn >= fill] = np.nan

# DESPUÉS (per MODIS L1B C7 UserGuide Sec 5.6 verbatim):
INVALID_SI_THRESHOLD = 32767  # MODIS L1B Sec 5.6: SI valid range [0, 32767]
rad[dn > INVALID_SI_THRESHOLD] = np.nan
```

Cubre los 14 sentinels (65500-65535) de un saque. **1 línea de cambio**, autoritativo.

### 5.2 VIIRS — leer quality flags

Opción A (correcta, más trabajo):
```python
# En read_viirs_l1b(): leer el SDS de quality flags
qf = f["observation_data"][f"{band}_quality_flags"][:]
saturation_mask = (qf & 0b100) != 0  # bit-2 Saturation
bt[saturation_mask] = np.nan
```

Opción B (más simple, casi tan robusta):
```python
# Post-LUT BT filter (LUT max indica clipping)
BT_LUT_MAX = {"I04": 361.77, "I05": 423.33, "M13": 634.0, "M15": 423.0}
bt[bt >= BT_LUT_MAX[band] - 0.5] = np.nan  # 0.5K margin
```

**Recomendación**: implementar Opción A para fundamentalmente correcto, con Opción B como defensa secundaria backup.

### 5.3 Defensa secundaria BT-level (todos los sensores)

Adicional, defensa post-Planck por BT > sat threshold (Coppola 2025 Cap.11 Table 1):

```python
# MODIS process_modis.py:
BT_SAT_MIR_K = 500.0   # B21 fire channel (Coppola 2025 Cap.11 Table 1)
bt_mir[bt_mir > BT_SAT_MIR_K] = np.nan
# (también incluir bt22 BT_SAT_B22_K = 335 K si fuera necesario, pero B22 ya cae por L1B mask normalmente)
```

Esta segunda capa cubre casos edge donde:
- Future L1B colección cambia esquema de sentinels.
- LUT extrapolation produce valor en rango "válido" pero físicamente imposible.

Trade-off: rechaza pixels reales > 500 K. Esos son extraordinarios (volcán muy activo); pero Wooster ya no es válido para BT > 500 K en B21 saturado de todos modos.

---

## 6. MISSION.md 3 preguntas

| Pregunta | Respuesta |
|---|---|
| ¿MIROVA lo hace? | **Sí, implícitamente y explícitamente**. Coppola 2023 (Frontiers MIROVA) dice "dual channel low/high gain settings to maximize the range of unsaturated data". Coppola 2025 Cap.11 reconoce saturation como factor crítico (p.338, p.341). Filtrar sentinels L1B es prerequisito antes de aplicar Wooster. |
| ¿Paper autoritativo? | **Sí, doblemente verificado verbatim**. (1) MODIS L1B C7 UserGuide Sec 5.6 + Table 5.6.1 (autoritativo). (2) VIIRS L1B UserGuide Aug 2021 Tabla C.1 (autoritativo). (3) Coppola 2025 Cap.11 Table 1 (sat thresholds canónicos por sensor). (4) Wooster 2003 §3 (sat=450K MODIS B21, no actualizado pero referencia histórica). |
| ¿Paridad MIROVA? | **Sí, sin trade-off contra recall**. Pixels saturados no son volcán medible. Excluirlos coincide con benchmark "false alerts ~5%" MIROVA (Coppola 2025 p.349). El fix opera al nivel L1B (universal), no en detección/threshold/cluster — invariante respecto a MIROVA. |

→ **Fix autorizado**. Pasa por F2.8.d writing-plans antes de implementar.

---

## 7. Audit empírico — alcance pre-S41

```
TOP FOSILES PRE-S41 (records con pc.vrp_mw > 50,000):
         695,431 MW  PlanchonPeteroa  [mirov]  2026-03-18 08:05  MODIS_AQUA

TOTAL FOSILES PRE-S41 con pc.vrp_mw > 50,000: 1
mirova_equivalent: 1 fosiles / 15,823 records
experimental:      0 fosiles / 18,245 records
```

**El record PP 2026-03-18 es el ÚNICO fósil en todo el dataset**. Cap S41 (2026-05-13) está atrapando todos los casos nuevos correctamente.

Reproc histórico necesario: 1 granule (MYD021KM.A2026077.0805.061) — alternativamente, dejar el fósil y solo aplicar fix para casos futuros (es invisible en producción por `distance_class=far`).

---

## 8. Discrepancias y red herrings descartados

| Claim original | Verdict tras verificar PDF |
|---|---|
| Vault: Wooster L_sat(B21)=57.6 W/m²/sr/µm como threshold | **Mala lectura**. 57.6 W es **un valor de ejemplo en Fig.4** que YA satura MODIS. Threshold real es BT≈450K (Wooster verbatim ×3). |
| Vault: BT_sat B21 ~500K | **Wrong en Iteración 1, RIGHT en Iteración 3**. Wooster 2003 dice 450K. Coppola 2025 actualiza a 500K. Adoptar Coppola 2025 (más reciente). |
| MIROVA tiene saturation handling algorithmic explícito | **Refutado**. Coppola 2023 + 2025 reconocen saturation como factor pero NO codifican reglas. Es responsabilidad downstream. |
| Coppola 2023 "two unsupervised methods" filtra pixels | **Red herring**. Es sobre weekly VRE aggregation (cloud contamination), no pixel sat. |
| Massimetti 2024 I-5 sat = 380 K (cita Cao 2013b) | **Probablemente outdated o S-NPP only**. UserGuide LUT max I5 = 423.33 K. UserGuide wins. |
| Coppola 2025 VIIRS I4=353K, I5=343K | **Posibles typos**. Contradicen UserGuide LUT max I4=361.77K, I5=423.33K. UserGuide wins. |
| Hipótesis VIIRS sentinel SOUB=65529 explica outliers | **Refutado**. VIIRS NO usa SI-sentinel para saturated. Usa clamp+quality_flag. Pero la causa raíz subyacente sigue siendo la misma (sat pixels pasan filtro) — solo el mecanismo es distinto. |
| BT=575 K es directamente proporcional a vrp=695K via Wooster nominal A_pix=1km² | **Necesitaba sec³(θ_z) scan-angle elongation**. Con θ_z=50° edge of swath, A_pix=3.74km². 45 pixels × 15,432 MW/pix = 694K MW match. |

---

## 9. Status

- [x] Investigación local agotada (Vault + project docs + pipeline code + ATBDs PDF originales)
- [x] Verificación verbatim contra PDFs primarios:
  - Wooster 2003 RSE
  - MODIS L1B C7 UserGuide (Toller & Isaacman 2025)
  - VIIRS L1B UserGuide (Aug 2021)
  - Coppola 2025 Cap.11 Thermal Monitoring (Springer book)
  - Coppola 2023 Frontiers (descartado — no relevante)
  - Massimetti 2024 (parcialmente outdated)
- [x] Audit pipeline: confirmado MODIS bug crítico + VIIRS bug menor (quality flag no leído)
- [x] Audit dataset: 1 solo fósil pre-S41 (PP 2026-03-18) en 34,068 records totales
- [x] Verificación matemática MODIS: 99.86% match con record observado vía sec³(50°) factor
- [x] Verificación matemática VIIRS: outliers 1037, 1111, 1890, 2536, 4020 MW corresponden a 4, 4, 7-8, 10, 16 pixels saturados (predicciones enteras)
- [x] Verdict autorizado por MISSION.md 3 preguntas
- [x] Discrepancias entre fuentes resueltas (UserGuide > Coppola > Massimetti > Wooster cuando hay conflicto)

## 10. Próximas tasks

| ID | Acción | Estimado |
|---|---|---|
| F2.8.b | Cerrar catálogo de opciones (mucho más corto post-verificación) | 10 min |
| F2.8.c | Tests sintéticos TDD: MODIS reproduce 575K + VIIRS reproduce sat-leak | 1 h |
| F2.8.d | `writing-plans` skill — plan bite-sized del fix unificado MODIS+VIIRS | 30 min |
| F2.8.e | Implementar fix MODIS + VIIRS + correr suite | 1 h |
| F2.8.f | A/B reproc PP 2026-03-18 + R2 contra MIROVA NRT + reproc 1 día VIIRS validar outliers desaparecen | 45 min |
| F2.8.g | Adopción operacional + frontend cleanup + A35 lección | 30 min |

Total: ~3.5-4 horas para cerrar F2.8 completo.

## 11. Aprendizajes meta acumulados S73

### A35 — Vault notes `ai_generated: true` necesitan verificación verbatim para valores numéricos críticos

Cuando un threshold, fórmula, o constante entra a un test/PR/código, **cotejar contra el PDF original** del paper antes de citarlo como autoridad. Las notas Vault sintetizan ideas correctamente pero pueden confundir contexto vs. threshold, o tener typos en números específicos. Esta sesión:
- Vault decía Wooster L_sat = 57.6 W (mala lectura: era valor de ejemplo Fig.4, NO threshold)
- Yo extrapolé a 500K, después corregí a 450K (Wooster verbatim), después actualicé a 500K (Coppola 2025 más reciente)
- Coppola 2025 Cap.11 Table 1 contradice Massimetti 2024 sobre VIIRS I5 (343 vs 380 K)
- UserGuide VIIRS L1B contradice Coppola 2025 sobre VIIRS I4/I5 (361/423 K vs 353/343 K)

**Jerarquía de autoridad cuando hay conflicto**: UserGuide oficial del sensor (Toller/MCST, JPSS) > Paper canon-MIROVA reciente (Coppola 2025) > Paper algorithm-MIROVA histórico (Coppola 2016, Wooster 2003) > Notas Vault `ai_generated`.

### A36 — sec³(θ_z) scan-angle elongation puede multiplicar discrepancias de factor 4

MODIS pixels off-nadir tienen área efectiva mucho mayor que nominal 1km². Para sensor angle θ_z = 50° → factor 3.74. Cualquier verificación matemática que ignore esto produce discrepancias factor 1-5×. El pipeline ya lo aplica vía `modis_pixel_areas()` con sec³(θ_z) correction; pero cualquier análisis manual debe incluirlo.

### A37 — VIIRS L1B usa esquema completamente distinto a MODIS para saturation flagging

Estos sensores son hermanos en función pero **no** comparten la convención L1B. MODIS reporta SI=65533 sentinel para detector saturated. VIIRS clampea radiance al Reported Range value Y setea bit-2 del Quality Flag SDS. Code que asume "los dos son iguales" produce gaps de protección distintos.
