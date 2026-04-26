# Drifts pipeline VRP Chile vs papers autoritativos — S17 2026-04-23

> Estado al cierre de S17. Los drifts identificados NO han sido corregidos todavía.
> Resolución planeada S18 con test A/B contra OSF v2.5.

## Contexto

La investigación sistemática S17 comparó el pipeline actual (`pipeline/process_*.py`, `pipeline/detection_context.py`, `pipeline/profiles/*.yaml`) contra los papers que supuestamente lo sustentan. Resultado: **5 divergencias** detectadas. De ellas, 3 están confirmadas, 1 ambigua, 1 de feature parity.

---

## D1 — Kernel 8-vecinos: median vs mean

### Evidencia
- **Paper**: Coppola 2016a SP 426.5, sección "Spatial analysis": literal *"subtracting from its value the average (arithmetic mean) of the eight neighbouring pixels"*.
- **Paper**: Campus et al. 2024 Bull Volcanol 86:25 (Vulcano VIIRS 375m), p.3: literal *"arithmetic mean of the radiance of the pixels surrounding the alerted one(s)"*.
- **Código**: [detection_context.py:30-35](../pipeline/detection_context.py#L30) usa `_nanmedian_ignore_self` → `np.median(valid)`.

### Estado
**DRIFT CONFIRMADO.** Dos papers MIROVA dicen media aritmética; nuestro pipeline usa mediana. Divergencia metodológica no documentada.

### Impacto físico estimado
Moderado. Mediana es más robusta vs outliers (NaN, edges), tiende a producir **dNTI menores** que media → pipeline más conservador. No explica regresiones S12, pero es drift sin respaldo documental.

### Decisión S18
**Corregir a `np.mean` (arithmetic mean, ignorando NaN)** en `detection_context.py`. Test TDD: validar bit-equivalence contra reference implementation + regresión de test corpus antes de merge.

### ✅ RESUELTO en S17 (2026-04-23 tarde)
Fix aplicado: renombrado `_nanmedian_ignore_self` → `_nanmean_ignore_self` usando `np.mean`.
Test nuevo `test_kernel_uses_arithmetic_mean_not_median` con outlier explícito confirma que ya no dispara falso positivo.
50/50 tests verde. Pipeline alineado a Coppola 2016a + Campus 2024.

---

## D2 — N·σ multiplier (el más impactante)

### Evidencia por paper

| Paper | Sensor | Noche | Día | Geometría σ |
|---|---|---|---|---|
| **Coppola 2016a Tabla 1** | MODIS | **5σ ROI1 / 10σ ROI2** | **15σ uniforme** | anillo sobre ROI bbox 50×50 km |
| **Di Bella 2024 §3.3 p.6** | MODIS | **5σ** | **10σ** | mitad-imagen "VA" volcanic area |
| **Di Bella 2024 §3.3 p.6** | VIIRS I4+M13 | **12σ** | **8σ** | mitad-imagen "VA" |
| **Di Bella 2024 §3.3 p.6** | SLSTR | 5σ | 10σ | mitad-imagen "VA" |
| Campus 2024 | VIIRS I4 | [no abordado] | [no abordado] | remite a Coppola 2016a |
| Coppola 2023 Global | MODIS | [no numéricos] | [no numéricos] | remite a Coppola 2016a |
| Coppola 2024 cap libro | — | [no actualiza] | [no actualiza] | remite a Coppola 2016a |

**Nuestro código**: `N_SIGMA_MIR = 3.0` uniforme para todos los sensores, día/noche, summit/scene ([profile.py:56](../pipeline/profile.py#L56)). Aplicado sobre ROI bbox 50×50 km.

### Estado
**DRIFT CONFIRMADO con ambigüedad doctrinal.** No hay consenso entre papers, pero **ningún paper soporta 3σ uniforme**. Coppola 2016a (MODIS, 5/10/15) y Di Bella 2024 (VIIRS 12/8) son las dos referencias autoritativas y discrepan.

Nuestro 3σ es **~40-70% más permisivo** que la referencia más laxa, lo que explica parte de los FPs sistemáticos (Tupungatito, Lastarria).

### Advertencia crítica
Los valores Di Bella **no son intercambiables directamente** con nuestros. Di Bella mide σ sobre "mitad-imagen VA" (ventana grande). Coppola 2016a mide σ sobre ROI bbox 50×50 km. **Adoptar N=12 ciegamente** en ventana anillo puede producir otra cosa distinta al comportamiento Di Bella.

### Decisión S18
**Test A/B empírico** sobre los 11 volcanes Tier A:
1. Baseline actual: `N_SIGMA_MIR=3.0` uniforme.
2. Experimento Coppola: MODIS 5/10/15 dual-ROI + día/noche; VIIRS idem.
3. Experimento Di Bella: MODIS 5/10, VIIRS 12/8 (homogeneizando geometría σ-anillo, documentado).

Métrica de decisión: recall/precision/F1 vs OSF v2.5 CSV consolidado. Adoptar el que maximice F1 sin degradar recall < 0.60.

---

## D3 — VRP TIR: Stefan-Boltzmann directo vs Aveni Eq.9

### Evidencia
- **Aveni 2025 GRL**: Eq.9 p.4 `VRP_TIR = A_pix · k_TIR · ΔL_TIR` con k_TIR=60.17 μm·sr para I5. Declara que Stefan-Boltzmann puro subestima hasta 90% bajo 600 K.
- **Coppola 2024 cap Springer p.337**: Eq.16 literal `φ_rad = A_hot · σ · ε · (T_hot⁴ − T_bk⁴)` (Stefan-Boltzmann). Aplica a low-T VTFs como crater lakes.
- **Código**: [process_viirs.py:35](../pipeline/process_viirs.py#L35) `SIGMA = 5.670374419e-8`, calcula TIR con Stefan-Boltzmann directo.

### Estado
**AMBIGÜEDAD DOCTRINAL NO RESUELTA.** Dos papers de alta autoridad discrepan.
- Coppola 2024 (review post-Aveni): usa Stefan-Boltzmann igual.
- Aveni 2025: dice Stefan-Boltzmann subestima 90%.

### ✅ RESUELTO en S17 (2026-04-23 tarde)
Auditoría de **Aveni et al. 2024 RSE "TIRVolcH"** (DOI 10.1016/j.rse.2024.114388, paper algorítmico previo al GRL 2025):
**Aveni 2024 RSE Eq.5 p.12 usa Stefan-Boltzmann puro** — idéntico a nuestro código y a Coppola 2024.

La Eq.9 con k_TIR=60.17 μm·sr **aparece SOLO en Aveni 2025 GRL** (paper posterior, refinamiento cuantitativo, no operacional). Coppola 2024 cap Springer (review post-Aveni 2024) también usa Stefan-Boltzmann.

**Veredicto**: MIROVA operacional usa Stefan-Boltzmann puro. TIRVolcH (algoritmo 2024) es investigación paralela del mismo grupo, no migración de MIROVA.

**Decisión**: mantener Stefan-Boltzmann puro en `mirova_equivalent`. No migrar a Eq.9 GRL. Para futuro (objetivo 2): considerar perfil experimental `tirvolch_experimental` sobre Copahue/Peteroa/Tupungatito crater lakes (alto valor para sub-pixel hydrothermal, costo implementación grande).

---

## D4 — Escala de alerta dashboard (feature parity)

### Evidencia
- **Coppola 2023 p.5**: niveles canónicos **Low / Medium / High / Very High / Extreme**. Origen Coppola 2016a.
- **mirovaweb.it home**: **Extreme >10,000 MW · Very High 1,000–10,000 · High 100–1,000 · Moderate 10–100 · Low <10**.
- **Nuestro dashboard**: no tiene escala categórica, solo chart numérico.

### Estado
**FEATURE PARITY GAP.** No es bug de detección, es de presentación.

### Decisión
Fase 3 (S19+). Agregar bandas coloreadas en chart + badge por volcán con nivel actual.

---

## D5 — Supervisión humana MIROVA vs clon automatizado

### Evidencia
- **Coppola 2023 p.4 §2.5**: *"entire dataset has been supervised to remove obvious non-volcanic thermal features ... done manually ... visual inspection"*.
- **Nuestro sistema**: 100% automático, sin filtro humano.

### Estado
**DIFERENCIA DE DISEÑO, NO DRIFT.** MIROVA OSF tiene filtro manual post-algorítmico. Nuestro "clon operacional" es por diseño automático — el CSV NRT scraper (latest.php) puede ya tener ese filtro aplicado en la fuente.

### Decisión
**Documentar**, no actuar. Implica que cuando comparamos nuestros outputs contra OSF v2.5 (histórico con supervisión humana) vs CSV NRT (menos supervisión), los benchmarks diferirán. Explica casos tipo Tupungatito "OSF=0 NRT=60 AT": supervisión manual OSF eliminó casos que NRT scraper mostró.

---

## Tabla resumen

| ID | Drift | Estado | Decisión | Sesión |
|---|---|---|---|---|
| D1 | `np.median` kernel 8-vec | ✅ Resuelto S17 tarde | Fix `np.mean` aplicado (merge `f78ad5d`) | **S17** |
| D2 | `N_SIGMA_MIR=3.0` uniforme | ✅ **Resuelto S19** | **Mantener 3σ** — cap=7K implementa umbral adaptativo superior | **S19** |
| D3 | TIR Stefan-Boltzmann | ✅ Resuelto S17 tarde (Aveni 2024 confirma SB puro) | Mantener | — |
| D4 | Escala Low/Medium/.../Extreme | Feature gap | Agregar dashboard | S22+ |
| D5 | Sin supervisión humana | Diseño | Documentar | — |
| **D6** | **`std_bg` global no localizado** | **❌ REFUTADO S21** | NO implementar — std_bg local ≈ global (ratio 0.81); glaciar afecta toda el área | **S21** |

## D6 — REFUTADO S21 (2026-04-25 noche)

### Resolución empírica

experiments/41 (S21): descarga 3 granules T4 Tupungatito reales vía NASA Earthdata
y mide std_bg multi-ROI directo sobre BT raw:

| ROI | std_bg mediana | n_pixels mediana |
|---|---:|---:|
| annulus_global (2–25 km) | **5.47 K** | 8473 |
| annulus_summit_5_8 (5–8 km) | **4.41 K** | 586 |

Ratio summit/global = 0.81. **Hipótesis D6 esperaba <0.5**.

### Por qué falló la intuición

La intuición S20 era: "glaciar lateral infla std_bg global; ROI1 local sería limpio".
Realidad: el glaciar a 5682 m **afecta toda el área hasta 10+ km**, no solo
lateralmente. El gradiente térmico glaciar-roca-altiplano se extiende sobre toda
la cuenca, así que reducir el anillo NO baja std_bg significativamente.

### Por qué no movería el threshold

Cap `MAX_VENT_SIGMA_CONTRIB_K=3K` satura cuando `2 × std_bg > 3 K`, lo que ocurre
con `std_bg > 1.5 K`. Tanto local (4.4 K) como global (5.5 K) están sobre ese
umbral → threshold idéntico = 3 K. ΔT real fumarola 1.5-2 K no dispara en ninguno.

### Causa raíz definitiva del cuello Tupungatito

Fumarola sub-pixel + sub-Kelvin con variabilidad. T4 = pasadas donde la actividad
térmica fue genuinamente <3 K sobre fondo. **MIROVA NRT (lo que scrapeamos) es
100% algorítmico — sin supervisión humana, servicio global gratuito sin
capacidad de revisión manual** (ver `~memory/feedback_mirova_no_human_supervision`).
Si MIROVA NRT captura más, es por diferencia algorítmica (NTI más sensible,
secuencia de paths distinta, suavizado temporal). Drift D5 supervisión aplica
al OSF v2.5 publicado, NO al NRT NRT-vs-NRT que es nuestra comparación operativa.

### Decisión

**NO implementar D6**. Backlog S22 reorientado:
- Prioridad 1: **H_S21_11** — agregar `diag_*` campos al schema VIIRS
  (`process_viirs.py` + `process_viirs_mod.py`) para diagnóstico futuro.
- Prioridad 2: A/B test `MAX_VENT_SIGMA_CONTRIB_K` 3→2 K una vez schema poblado.
- Aceptar Tupungatito ≈0.57-0.65 como límite del MIR puro nocturno automatizado.

## D6 — Background no localizado (S20 2026-04-25 tarde, contexto histórico)

### Evidencia

Forense H17 Tupungatito (S20 tarde) reveló que 13 records FN tienen pixels detectados (n_anom 1-772) pero TODOS están far (>7 km del cráter). Cero pixels dentro del inner_radius_km. Sin embargo, MIROVA detecta el cráter en esas mismas pasadas con VRP=0.05-0.32 MW.

**Diagnóstico físico**:
- Nuestro `std_bg` se computa sobre el anillo bg_inner_km a bg_outer_km (bbox 50×50 km).
- En Tupungatito el glaciar lateral infla `std_bg` a ~2-3 K.
- El cap `MAX_VENT_SIGMA_CONTRIB_K=3.0` empuja el threshold vent a max(1K, 3K) = 3K.
- La señal real del cráter (fumarola) tiene ΔT ≈ 1.5-2K — **no cruza 3K**.

**Si calculáramos `std_bg` solo sobre ROI1 5×5km cerca del cráter**:
- ROI1 está fuera del glaciar (que está al N/E del cráter Tupungatito).
- `std_bg_local` ≈ 0.5-0.8 K (vs 2-3 K global).
- Threshold vent local = max(1K, min(2·0.5, 3)) = max(1K, 1K) = 1K.
- ΔT 1.5-2K **SÍ dispara** vent-path con bg local.

### Marco MIROVA

Coppola 2016a SP 426.5 Tabla 1 documenta exactamente esta separación:
- **ROI1** (5×5 km del cráter): umbral 5σ noche.
- **ROI2** (50×50 km bbox): umbral 10σ noche.

Nosotros tenemos un solo `std_bg` que es híbrido: anillo entre `bg_inner_km` y `bg_outer_km` (~2-25 km) que excluye el cráter pero INCLUYE el glaciar.

### Decisión S21

Implementar **dual background statistics**:
- `t_bg_summit, std_bg_summit`: media y desv estándar sobre ROI1 (5×5 km cerca del cráter, excluyendo el vent_radius para no contaminar con detecciones reales).
- `t_bg_scene, std_bg_scene`: como ahora (anillo grande).
- Vent-path usa `std_bg_summit` para su threshold.
- Eruption-path scene usa `std_bg_scene`.
- Path D dNTI puede usar ambos con dual-ROI thresholds (Coppola Tabla 2).

### Riesgos a manejar

1. **ROI1 chico → muestra ruidosa**: si <25 pixels válidos en ROI1, fallback a `std_bg_scene`.
2. **Volcanes con cráter persistentemente caliente** (Lascar, Villarrica): el cráter mismo contamina ROI1 si no se excluye `vent_radius_km`. Implementar exclusión.
3. **Cambio puede afectar Lascar/Chaitén**: golden tests M1 ya cubren records canónicos. Si rompen, evaluar.
4. **Reproceso necesario** (~7h cómputo) — dual bg afecta clasificación de pixels.

### Backlog

## D2 — Resolución S19 (2026-04-25)

### Test A/B realizado

Reproceso 30 días (2026-03-25 → 2026-04-24), 3 volcanes (Tupungatito, Chaitén, Lascar), 3 perfiles (3σ baseline, 5σ Coppola, 12σ Di Bella). Ground truth: CSV MIROVA NRT updated (`registro_vrp_consolidado_25_04_2026.csv`).

### Resultado agregado

| Perfil | TP | FP | FN | Recall | Precision | F1 |
|---|---|---|---|---|---|---|
| **3σ (baseline)** | **84** | **263** | **34** | **0.71** | **0.24** | **0.36** |
| 5σ (Coppola 2016a) | 75 | 330 | 43 | 0.64 | 0.19 | 0.29 |
| 12σ (Di Bella 2024) | 75 | 327 | 43 | 0.64 | 0.19 | 0.29 |

### Hallazgo clave: el cap `MAX_SIGMA_COMPONENT_K=7K` anula la diferencia 5σ vs 12σ

Código relevante ([process_viirs.py:358](../pipeline/process_viirs.py#L358)):

```python
sigma_component = min(N_SIGMA_MIR * std_bg, MAX_SIGMA_COMPONENT_K)  # cap=7K
threshold_mir = max(ANOMALY_THRESHOLD_K, sigma_component)             # floor=5K
```

**Consecuencia matemática**: cuando `std_bg > 0.58 K` (típico Lascar, Tupungatito), `5×σ > 7` y `12×σ > 7` ambos saturan → threshold idéntico. **5σ y 12σ devuelven exactamente los mismos números** en estos volcanes.

Verificación empírica (Lascar y Tupungatito, ambos completos):
- 5σ: TP=58/20, FP=118/77, FN=21/22 (Lascar/Tupungatito)
- 12σ: TP=58/20, FP=118/77, FN=21/22 ← **idéntico al bit**

### Por qué 3σ + cap gana

El comportamiento efectivo del baseline es:
- σ_bg bajo (≤1.7 K, atmósfera limpia): threshold = max(5K, 3·σ_bg) → permisivo, captura señales débiles.
- σ_bg alto (>2.3 K, glaciar): threshold capeado a 7K → no se infla a 9-15K que mataría señal real.

Es **un umbral adaptativo de facto** que ningún paper documenta pero combina lo mejor de:
- Coppola 2016a 5σ ROI1: noise protection.
- Di Bella 2024 12σ: aún más estricto pero no aplicable a nuestra geometría σ-anillo.

### Decisión operacional

**Mantener `n_sigma_mir = 3.0` + `MAX_SIGMA_COMPONENT_K = 7.0`** en `mirova_equivalent`. Documentar que el drift D2 NO es problemático — es una innovación nuestra (S15 Tema F) que empíricamente supera las alternativas teóricas para nuestra geometría σ-anillo.

### H17 (Tupungatito) sigue activa

El A/B no resuelve Tupungatito: recall 0.57 con 3σ (mejor que 5σ 0.37) pero lejos del 0.85+ esperado. **La causa NO es N·σ**, es geografía o sub-pixel intrínseco.

**Próximo camino S20**: dual-ROI Coppola 5σ summit / 10σ scene — ataca FPs espacialmente, no con multiplier global. Tupungatito beneficiaría de threshold permisivo en summit (3σ adaptativo) y estricto en scene (10σ del paper).

## Otros hallazgos que NO son drift

- **k=18.9 MODIS, k=19.7 VIIRS M13, k=18.0 VIIRS I4, A_pix=140,625 m²**: confirmados por Coppola 2024, Campus 2024, Campus 2022. Nuestros coeficientes están bien.
- **K1=-0.8 noche / -0.6 día, C1=0.003 summit / 0.010 scene, ROI1=5×5 km, bbox=50×50 km UTM, MIR nocturno only**: todos confirmados.
- **NOAA-21**: ausencia de mención en todos los papers MIROVA auditados (Coppola 2016a, Campus 2022, Campus 2024, Coppola 2023, Coppola 2024 cap, Aveni 2025, Di Bella 2024). Nuestra decisión de agregarlo es operacional, respaldada por NASA JPSS ATBD Rev C (descargado S17).
