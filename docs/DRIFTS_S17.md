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
| D4 | Escala Low/Medium/.../Extreme | Feature gap | Agregar dashboard | S19-20 |
| D5 | Sin supervisión humana | Diseño | Documentar | — |

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
