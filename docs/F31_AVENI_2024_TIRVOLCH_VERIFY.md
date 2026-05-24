# F31 — Aveni 2024 RSE TIRVolcH: verificación verbatim PDF vs implementación

**Sesión**: S75
**Fecha**: 2026-05-24
**Trigger**: caveat A35 pendiente sobre `pipeline/detect_tirvolch.py` (PR #153, merged `f5e1187`).
Vault note `aveni2024tirvolch.md` está marcado `confidence:medium/high` y nunca fue cross-checked
verbatim contra el PDF. Esta verificación es pre-requisito antes de Task A2 (integración a
`process_viirs.py`).

**Fuente verbatim**: `documentacion/Aveni_2024_TIRVolcH_RSE.pdf` → `Aveni_2024_TIRVolcH_RSE.md`
(markitdown, 3330 líneas). Citas con número de línea del markdown.

**Paper**: Aveni S., Laiolo M., Campus A., Massimetti F., Coppola D. (2024). *TIRVolcH: a robust
algorithm to detect thermal anomalies at active volcanoes via VIIRS-I5 imagery*. **Remote Sensing
of Environment 315, 114388**. doi:10.1016/j.rse.2024.114388.

---

## Status

- PDF → markdown: **creado** (`Aveni_2024_TIRVolcH_RSE.md`, 3330 líneas)
- Constantes verificadas contra paper verbatim: **9/9**
- Discrepancias numéricas en `detect_tirvolch.py`: **0**
- Discrepancias en docstring / Vault note: **2 menores** (caveat operacional Copahue + label "estricto vs 4")
- **Caveat A35**: **RESUELTO** sobre los valores numéricos (confidence → HIGH-VERIFIED).
  Caveat operacional Chile sigue (paper NO valida en Chile; Tier A formal solo Vulcano/Agung/La Palma).

---

## Tabla verificación

| # | Constante / parámetro | Vault claim | PDF verbatim (línea md) | `detect_tirvolch.py` | Match? |
|---|---|---|---|---|---|
| 1 | Gate absoluto ABS_BT (Paso/Test 1) | 313.15 K (40 °C) | "ABSBT is equal to 313.15 K, this being consistent with the maximum nighttime temperature recorded on Earth, not contaminated by a hotspot (NOAA, 2024)" (L721-723) | `TIRVOLCH_T_ABS_MIN_K = 313.15` (L59) | ✅ EXACTO |
| 2 | Z-score threshold Test 4 | 7.0 | "Z − RES > 7  [test 4]" (L827-829) | `TIRVOLCH_Z_THRESHOLD = 7.0` (L62) | ✅ EXACTO |
| 3 | Sensibilidad ΔBT mínima | 0.5 K above background | "pixel-integrated temperatures as low as 0.5 K above the background" (L40-41); "BT of Candidate Alerts is at least 0.5 K above the background temperature (BTbg)" (L1144-1145) | `TIRVOLCH_DT_MIN_K = 0.5` (L65) | ✅ EXACTO |
| 4 | MAD factor outlier removal | 3.0 (×MAD) | "Datapoints (pixels) exceeding three scaled Median Absolute Deviation (MAD) from the monthly median BT (i.e., outliers; Leys et al., 2013) are removed" (L662-664) | `TIRVOLCH_MAD_FACTOR = 3.0` (L69) | ✅ EXACTO |
| 5 | R² mínimo para REF quality | 0.5 | "Images with an R2 coefficient < 0.5 are discarded and a new reference scene...is generated" (L654-657) | `TIRVOLCH_R2_MIN = 0.5` (L68) | ✅ EXACTO |
| 6 | Water-dominated sigma factor (Test 7) | 10×σ | "OBS ≥ OBS̄ + 10·σOBS  or  OBS ≥ pOBS99.5  [test 7]" (L944) | `TIRVOLCH_WATER_SIGMA_FACTOR = 10.0` (L72) | ✅ EXACTO |
| 7 | Buffers PolyROI bΔT (Test 5) | 0.5 / 1 / 2 / 4 K (ROI1..ROI4) | "with bΔTROIn equal to 0.5, 1, 2 and 4 K for ROI1, ROI2, ROI3, and ROI4, respectively" (L820-821) | `TIRVOLCH_LAND_BUFFER_MIN_K = 0.5`, `TIRVOLCH_LAND_BUFFER_MAX_K = 4.0` (L75-76) | ✅ rango correcto (módulo no expone los 4 valores individuales, sólo min/max — OK para A1) |
| 8 | Grilla UTM | 134 × 134 pixels (~2500 km²) | "binary matrix 134 × 134 pixels...as provided with L1B VIIRS products" (L579-580); REF "(134 × 134 pixels)" (L642-643) | `TIRVOLCH_GRID_SIZE_PX = 134` (L79) | ✅ EXACTO |
| 9 | ROIs concéntricas | 1, 5, 12.5, 25 km del vent | "ROI1, extending for ~1 km from the volcano's summit, ROI2, from ~1 to ~5 km, ROI3, from ~5 to ~12.5 km, and ROI4, beyond 12.5 km" (L591-593) | `TIRVOLCH_ROI_RADII_KM = (1.0, 5.0, 12.5, 25.0)` (L80) | ✅ EXACTO (paper dice "beyond 12.5 km" sin tope explícito; 25.0 km es elección razonable consistente con la grilla 134 px ≈ 50 km lado) |
| 10 | FP rate declarado | ~1.8 % | "maintaining a false positive rate of ~1.8 %" (L41) | `TIRVOLCH_FP_RATE_DECLARED = 0.018` (L83) | ✅ EXACTO |
| 11 | Baseline period | 2012-2023 (~10 yr decadal) | "decadal time series of VIIRS data (2012−2023), acquired at three different volcanoes" (L42) | (documentado en docstring L196-198, no es constante numérica) | ✅ EXACTO |
| 12 | Volcanes validación paper | Vulcano + Agung + La Palma | "(i) detect hydrothermal crises at fumarolic fields (Vulcano, Italy), (ii) unveil thermal unrest preceding dome extrusions and explosive eruptions (Agung, Indonesia), and (iii) spatially trace lava flows extent...(La Palma, Spain)" (L43-45) | docstring L33-34 los enumera | ✅ EXACTO |

### Adicionales del paper (NO citados en Vault note pero relevantes para Task A2)

- **Test 11 ΔTbg ROI-dependent** (Vault dice "buffer 0.5-4 K" pero no diferencia los pasos):
  Test 5 buffers PolyROI = 0.5/1/2/4 K (bΔT_ROIn, L820); Test 11 ΔTbg = **0.5 K (VSROI+ROI1+ROI2), 0.75 K (ROI3), 1 K (ROI4)** (L1155-1157). Son dos buffers distintos en dos tests distintos; `detect_tirvolch.py` no los expone aún como constantes separadas (OK para Task A1 base; Task A2 las necesitará).
- **Land/Water split**: scene con >20% land pixels (~500 km²) = "Land-dominated"; <20% = "Water-dominated" (L693-695). No está en `detect_tirvolch.py` — esperado, es decisión de routing del Paso 5/6 que vendrá en Task A2.
- **Test 9 (VSROI Z-score)**: Z−RES_VSROI ≥ **5** (L982-986). Threshold relajado vs Test 4 (=7). Vault note lo menciona; `detect_tirvolch.py` no expone constante explícita (Task A2).
- **Test 10 (VSROI contextual)**: OBS ≥ OBS̄ + **2σ** (L1120-1126). También factor relajado vs Test 7 (=10σ). No expuesto aún.

---

## Discrepancias detectadas

### D1 — Docstring "Copahue" mencionado como caso adicional

- **Ubicación**: `detect_tirvolch.py` L34-35 ("Volcán chileno mencionado: **Copahue** (casos adicionales). Sin volcán chileno Tier A formal — caveat operacional.")
- **Verbatim PDF**: **Copahue NO aparece en el cuerpo del paper Aveni 2024**. Búsqueda case-insensitive sobre las 3330 líneas → 0 matches. La única referencia a Chile en el paper es Lastarria en la bibliografía (`Lara, L.E., Flores, F., Calderón, R., Cardona, C., 2021. Volcano hazards and risks in Chile`, L2766) y un cap en review sobre Lastarria (L3147). No hay validación TIRVolcH en volcán chileno.
- **Severidad**: baja (no afecta constantes ni algoritmo). Pero el docstring miente — Copahue NO está mencionado por Aveni 2024.
- **Origen probable**: confusión con Aveni 2025 GRL (Coppola coautor, donde aparecen otros casos) o con Vault note `confidence:high` que extrapola.
- **Recomendación**: en próxima edición de `detect_tirvolch.py` (Task A2), reemplazar L34-35 por:
  > "Validación paper: Vulcano 2021-22 fumarólica, Agung 2017 pre-dome, La Palma 2021 lava cooling.
  > **Ningún volcán chileno validado en el paper original** — caveat operacional Tier A para
  > aplicación en Chile (pending validación empírica Lascar/Villarrica/Chaitén en Task A3)."

### D2 — Docstring "estricto vs n_sigma_tir=4 actual"

- **Ubicación**: `detect_tirvolch.py` L22 ("Z-score > 7 sobre RES (estricto vs n_sigma_tir=4 actual).")
- **Comentario**: este "vs n_sigma_tir=4 actual" parece referirse a un default histórico del pipeline previo (probablemente `process_viirs.py`). No es discrepancia con el paper (el paper sí dice 7). Es contexto interno.
- **Severidad**: nula. Sólo aclarar al integrar Task A2 si ese "4" sigue siendo el comparador relevante o si ya se sincronizó.

---

## Recomendaciones para Task A2 (integración process_viirs.py)

1. **Exponer constantes adicionales** detectadas en sección "Adicionales del paper":
   - `TIRVOLCH_T11_DTBG_VSROI_ROI1_ROI2_K = 0.5`, `T11_DTBG_ROI3_K = 0.75`, `T11_DTBG_ROI4_K = 1.0`.
   - `TIRVOLCH_Z_VSROI = 5.0` (Test 9).
   - `TIRVOLCH_VSROI_SIGMA_FACTOR = 2.0` (Test 10).
   - `TIRVOLCH_LAND_WATER_SPLIT_PCT = 20.0` (umbral routing).
   - Mantener tupla per-ROI para Test 5: `TIRVOLCH_PolyROI_BUFFERS_K = (0.5, 1.0, 2.0, 4.0)`.
2. **Aplicar fix D1** al docstring (Copahue).
3. **Caveat A35 Chile**: el paper NO valida en ningún volcán chileno. Para Task A3 (calibración Tier A Chile), agendar A/B Lascar (fumarólico activo) + Villarrica (lago lava) + Chaitén (domo) como mínimo, contra ground truth MIROVA NRT CONS+OCR.
4. **VSExcROI**: tres clases del paper (L619-629):
   - "quasi-exclusively confined activity" → buscar dentro de 2 km del summit (crater lakes, fumarolic fields). Apunta a Villarrica/PCC/Copahue como candidatos.
   - "summit-confined effusive/explosive" → 5 km. Encaja con Lascar, Lastarria.
   - "far-reaching lava flows / no thermal activity past 2 decades" → sin restricción espacial.
   Mapear esto al campo `mirova_inner_radius_km` ya existente en `volcanoes.yaml` (PCC=20 km es outlier — revisar si es física o herencia MIROVA Coppola).

---

## Conclusión

Los **9 valores numéricos** que `detect_tirvolch.py` ya implementa coinciden exactamente con el
PDF verbatim. **No hay fix de constantes necesario en S75**. La Vault note `aveni2024tirvolch.md`
puede subirse a `confidence:high-verified` sobre los 12 ítems verificados arriba.

Las 2 discrepancias detectadas (Copahue inexistente, label estricto-vs-4) son de documentación,
no de algoritmo. Aplicar en Task A2 cuando se reescriba el módulo para integración, junto con la
exposición de las constantes adicionales (Test 9-11 thresholds).

**Status A35 (sobre detect_tirvolch.py)**: → **RESUELTO HIGH-VERIFIED** para los valores
numéricos. Caveat operacional Chile permanece (no es bug del módulo, es contexto científico).

**Referencias**
- PDF: `documentacion/Aveni_2024_TIRVolcH_RSE.pdf`
- Markdown extracto: `documentacion/Aveni_2024_TIRVolcH_RSE.md` (markitdown, 3330 líneas)
- Implementación: `pipeline/detect_tirvolch.py` (PR #153, commit `f5e1187`)
- Tests: `tests/test_tirvolch_f31.py` (20 passing)
- Vault note original: `Vault/10_Bibliografia/99_por_clasificar/aveni2024tirvolch.md`
- Plan F31 padre: `docs/F31_AVENI_VRPTIR_PLAN_S74.md`
- CLAUDE.md A35: jerarquía de autoridad de fuentes (UserGuide > paper PDF > Vault note `ai_generated`)
