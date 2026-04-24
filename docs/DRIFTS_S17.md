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

### Decisión S18/S19
**Auditoría pendiente de Aveni et al. 2024 TIRVolcH RSE** (`1-s2.0-S0034425724004140-main.pdf`), que es el paper algorítmico previo al GRL 2025. Debería clarificar si Aveni propone REEMPLAZAR Stefan-Boltzmann o es un método complementario.

**Por ahora**: mantener Stefan-Boltzmann (consistente con Coppola 2024). **No** migrar a Eq.9 hasta tener evidencia de que MIROVA oficial lo adoptó.

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
| D1 | `np.median` kernel 8-vec | Confirmado | Cambiar a `np.mean` | S18 |
| D2 | `N_SIGMA_MIR=3.0` uniforme | Confirmado, ambiguo entre papers | Test A/B 3 configs vs OSF | S18 |
| D3 | TIR Stefan-Boltzmann | Ambigüedad | Mantener, auditar Aveni 2024 RSE | S19 |
| D4 | Escala Low/Medium/.../Extreme | Feature gap | Agregar dashboard | S19-20 |
| D5 | Sin supervisión humana | Diseño | Documentar | — |

## Otros hallazgos que NO son drift

- **k=18.9 MODIS, k=19.7 VIIRS M13, k=18.0 VIIRS I4, A_pix=140,625 m²**: confirmados por Coppola 2024, Campus 2024, Campus 2022. Nuestros coeficientes están bien.
- **K1=-0.8 noche / -0.6 día, C1=0.003 summit / 0.010 scene, ROI1=5×5 km, bbox=50×50 km UTM, MIR nocturno only**: todos confirmados.
- **NOAA-21**: ausencia de mención en todos los papers MIROVA auditados (Coppola 2016a, Campus 2022, Campus 2024, Coppola 2023, Coppola 2024 cap, Aveni 2025, Di Bella 2024). Nuestra decisión de agregarlo es operacional, respaldada por NASA JPSS ATBD Rev C (descargado S17).
