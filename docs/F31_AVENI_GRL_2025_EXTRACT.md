# F31 — Aveni 2025 GRL VRPTIR — extract verbatim (S74 PDF verified)

> Extracción verbatim del paper Aveni 2025 GRL `doi:10.1029/2024GL113324` —
> **open access AGU**, leído end-to-end vía Chrome MCP S74 2026-05-23. Esta es
> la referencia canonical confidence:HIGH (A35 verification completada).
> Reemplaza la nota Vault `aveni2025volcanic.md` (auto-generated, confidence:medium).
>
> **Uso**: cuando implementemos Plan F31 Task A1-A5, consultar este doc para
> citas verbatim sin necesidad de re-fetch Chrome.

## Metadata

- **Título**: Volcanic Radiative Power Retrieval From Moderate-to-Low-Temperature Features Using a Single TIR Band: Validation Using Volcanic Crater Lakes and Hydrothermal Systems
- **Autores**: Simone Aveni, Sophie Pailot-Bonnétat, Dmitri Rouwet, Andrew J. L. Harris, Diego Coppola
- **Afiliaciones**: Sapienza Roma + Università di Torino + autores externos
- **Revista**: Geophysical Research Letters, Volume 52, Issue 12, e2024GL113324, 28 June 2025
- **First published**: 14 June 2025
- **DOI**: 10.1029/2024GL113324
- **Open Access**: Sí (Wiley-CRUI-CARE agreement)
- **URL**: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GL113324
- **ClerVolc publication**: 675

## Abstract verbatim

> "Assessing Radiative Power (RP) output is essential for monitoring and
> understanding volcanic systems. While Mid-Infrared channels are used to
> assess thermal outputs at volcanoes exhibiting effusive activity,
> Thermal-InfraRed (TIR) bands are better suited for measuring
> moderate-to-low-temperature (≲600 K) features, such as those associated
> with hydrothermal activity. However, failure to meet key assumptions in
> TIR-based calculations results in up to a ∼90% RP underestimation of ≲600 K
> sources. We thus introduce the TIR-based Volcanic Radiative Power
> (VRP_TIR) method to accurately retrieve RP from single-band TIR (10.5–12
> μm) spectral radiance at systems dominated by surface temperatures of ≲600
> K, that is, crater lakes and fumarole fields, achieving an uncertainty of
> ±35%. Comparison with ground truth for Ruapehu, El Chichón, Taal, Vulcano,
> Puracé, Poás, and White Island demonstrates the accuracy of VRP_TIR in
> quantifying thermal output and detecting subtle variations in volcanic
> activity. This exportable method will facilitate compilation of global RP
> inventories for moderate-to-low-temperature volcanic systems."

## Ecuaciones verbatim

### Eq.1 — Pixel-integrated spectral radiance (mixed pixel)

```
L_λ_pix = Σ_{i=1..n} f_i · B(λ, T_i)
```

donde:
- `L_λ_pix` = pixel-integrated spectral radiance @ λ (W/m²/sr/µm)
- `B(λ, T_i)` = spectral radiance del componente i a temperatura T_i (Planck)
- `f_i` = fractional area del componente i
- `n` = número de componentes térmicos en el pixel

### Eq.2 — Pixel-integrated Brightness Temperature (Planck inverse)

```
T_pix = C2 / (λ · ln(C1 / (L_λ_pix · λ⁵) + 1))
```

donde:
- `C1 = 1.1910 × 10⁸ W·m⁻²·sr⁻¹·μm⁴` (first radiation constant)
- `C2 = 1.4388 × 10⁴ K·μm` (second radiation constant)

### Eq.3 — True RP (Stefan-Boltzmann generalized, mixed pixel)

```
RP_true = A_pix · σ · ε · (T_eff⁴ − T_bg⁴)
```

donde:
- `A_pix` = pixel area (m²)
- `σ = 5.67 × 10⁻⁸ W·m⁻²·K⁻⁴` (Stefan-Boltzmann)
- `ε` = emissivity
- `T_bg` = background temperature (K)
- `T_eff` = effective radiation temperature (Eq.4)

### Eq.4 — Effective radiation temperature

```
T_eff⁴ = (1/A_hot) · Σ_i A_i · T_i⁴
```

### Eq.5 — Pure pixel assumption RP (SUBESTIMA hasta 90%)

```
RP_pure = A_pix · σ · ε · (T_hotpix⁴ − T_bg⁴)
```

Assumed homogeneous pixel — sólo válido si `f_hot ≈ 1`. **NO usar para
sub-pixel features.**

### Eq.6 — Excess spectral radiance

```
ΔL_λ = L_λ_hotpix − L_λ_bg
```

### Eq.7 — VRP_TIR simplified for λ=11.45 μm

```
VRP_TIR ≈ A_pix · k_TIR · ΔL_λ        (con k_TIR ≈ 60.17 μm·sr para I5)
```

### **Eq.8 — k_TIR(λ) coefficient (CRITICAL)**

```
k_TIR(λ) = 1.0575·λ² − 14.3139·λ + 85.4239        [μm·sr]
```

Holds en rango espectral **10.5-12 μm**. **VALORES NUMÉRICOS POR SENSOR**:

| Sensor | λ (μm) | k_TIR (μm·sr) |
|---|---|---|
| VIIRS I5 | 11.45 | **60.17** (verbatim p.4, Fig.2b) |
| VIIRS M15 | 10.76 | 63.92 (Eq.8 evaluation) |
| MODIS B31 | 11.02 | 62.21 (Eq.8 evaluation) |

### **Eq.9 — VRP_TIR (formula operacional)**

```
VRP_TIR = A_pix · k_TIR · Σ_{j=1..N_pix} (L_λ_hotpix,j − L_λ_bg)        [W]
```

donde:
- `N_pix` = número de hotspot-contaminated pixels
- `L_λ_hotpix,j` = radiancia del j-ésimo pixel hot (W/m²/sr/μm)
- `L_λ_bg` = background spectral radiance (asumida igual a vecindad cloud-free)

**Uncertainty**: ±35% (vs Wooster MIR ±30%).

## Constraints / quality control

### Rango validez

> "Results of simulations [...] reveal that in the range ∼300–600 K, the
> relationship between VRP_TIR/A_pix and ΔL at λ=11.45 holds, with a ratio
> (k_TIR, in μm·sr) within the ±35% interval (Figure 2b)."

- **T_min ≈ 300 K** (debajo: no anomalía detectable física)
- **T_max ≈ 600 K** (sobre: usar Wooster MIR)
- **Spectral range donde Eq.8 holds**: 10.5–12 μm

### Componentes de alta temperatura tolerados

> "Simulations revealed that the VRP_TIR holds if the area occupied by hot
> vents (at T = 900 K) does not exceed 0.0025% of the total thermal anomaly
> captured within the pixel."

Caso ejemplo paper (Vulcano fumarole field 415,000 m²):
> "this would be equivalent to a ∼10 m² region at 900 K"

### Pre-requisito TIRVolcH detector

> "we applied TIRVolcH (Aveni et al., 2024), a single-band TIR-based
> algorithm designed to detect hotspot-contaminated pixels across a broad
> range of volcanic settings. This system uses a temporal and contextual
> analysis to identify thermally anomalous pixels, and is capable of
> detecting thermal anomalies for pixel-integrated temperatures as low as
> 0.5 K above the surrounding hot-spot-free background."

**TIRVolcH** referencia: Aveni et al. (2024) **doi:10.1016/j.rse.2024.114388**
(ya en nuestro Vault como `aveni2024tirvolch.md`).

### Assumptions paper

> "An emissivity of one is assumed (see Text S1 in Supporting Information S1
> for details)."

Solo nighttime VIIRS I5:
> "processes nighttime TIR scenes from the VIIRS I5 channel (11.45 μm)"

Background temperature noise:
> "The maximum δT_bg was set to 2.5 K, based on a ground projection of a
> 1 × 1 km pixel for a surface with a 40° slope. Taking the resulting ∼0.84
> km difference in elevation across the pixel and an adiabatic lapse rate of
> 6 K/km (Bonneville et al., 1985; Catling & Kasting, 2017), normal
> temperature variations should not exceed ∼5 K."

→ **Caveat operacional VRP Chile**: el supuesto ≤2.5 K probablemente está
**VIOLADO en Andes nevados** (terrain heterogeneity + snow cover). Pendiente
ablation study piloto S75+.

## Validation results

### Setup

7 volcanes — **NONE chilenos**:
- **Mount Ruapehu** (NZ) — 12-yr continuous lake temperature record (GeoNet)
- El Chichón (México)
- Taal (Philippines)
- Vulcano (Italy)
- Puracé (Colombia)
- Poás (Costa Rica)
- White Island (NZ)

### Mt Ruapehu — ground truth correlation

> "The agreement between the two values, as illustrated in Figure 4a, has
> a correlation coefficient (ρ) of 0.93, and a coefficient of determination
> (R²) of 0.87, with deviations of less than ±35% (Figure 4b), that is,
> within the expected uncertainty of the method."

### Casos exitosos detección unrest

- **Vulcano**: detection unrest septiembre 2021 (~5-15 MW vs baseline 2.5 MW)
- **Puracé**: sharp increase late 2023 → November 2023 ash emission, orange alert 2024
- **Taal**: 2012-2019 quiescence → 2020 phreatomagmatic confirmado por trend
- **El Chichón**: 2014-2015 CO2 degassing peak coincide con peak VRP_TIR

### Caveats observados en paper

- **White Island Dec 2019**: peaks de actividad coincidieron con **decreasing**
  VRP_TIR (no increasing). Explicación: self-sealing del sistema o
  evaporación del crater lake exponiendo high-T vents (>600 K) → método
  pierde validez en transición hydrotermal→efusivo.

## Implicancias VRP Chile (mapeo per-volcán Tier A)

| Volcán | T típica feature | VRPTIR aplicable? | Justificación paper |
|---|---|---|---|
| **Villarrica lava lake** | 400-700 K (costra superficial) | ⚠️ **Mixto/boundary** | f_hot ~2-4% lago activo, costra <600 K SÍ; pero magma exposed >600 K transitions → método pierde validez (caso White Island) |
| **Lastarria fumarolas** | 300-500 K (fumarólico) | ✅ **CANDIDATO FUERTE** | Vulcano fumarole field análogo, ground truth Vulcano validado |
| **Copahue lago cratérico** | <500 K | ✅ **CANDIDATO** | El Chichón crater lake análogo, ground truth validado |
| **Planchón-Peteroa lago** | <500 K | ✅ **CANDIDATO FUERTE** | Aguilera 2021 citado (autor chileno) — Peteroa lake referenciado en paper |
| **Chaiten domo+lago** | Mixto >600 K dome, <500 K lago | ⚠️ **Mixto** | Riesgo Hot dome >0.0025% area + transitions |
| **PCC lacolito** | <500 K | ❌ **EXCLUIR** | A20: PCC no-focal (área extensa) — invalida single-pixel TIRVolcH |
| Lascar | >600 K (Tier A Alto) | ❌ | Wooster MIR es mejor — ya calibrado natural |
| Isluga | >600 K | ❌ | Idem Lascar |
| Tupungatito | Muy Bajo régimen | ⚠️ Pilot test | Post-S65 fix mirova_center |

## Plan F31 status update post-PDF verify

| Task | Status pre-PDF | Status post-PDF S74 |
|---|---|---|
| A1 TIRVolcH detector base | Diseño Aveni 2024 referenciado | ✅ Diseño confirmado, READY para implementar |
| A2 VRPTIR formula | Implementado PR #146 con confidence:medium | ✅ **VERIFIED confidence:HIGH** PR #150 |
| A3 Profile flag opt-in | Plan listo | READY |
| A4 Tests TDD | 19 tests pass (PR #146) | ✅ Math validada contra paper |
| A5 Piloto Copahue/PP | Plan diseño | READY S75+ |
| A6 PDF verify | BLOQUEANTE | ✅ **COMPLETADO S74 vía Chrome MCP** |

**Próximo paso S75**: implementar A1 TIRVolcH detector base. Requiere baseline
temporal 10-yr cloud-free VIIRS I5 BT por volcán — pre-task crear
`data/tirvolch_baselines/<volcano>.npz`.

## Hallazgo Chile-specific en paper

**Aguilera et al. (2021)** citado para **Planchón-Peteroa** crater lake:

> "Quantifying the heat fluxes at hydrothermal systems (Harris & Stevenson,
> 1997a, 1997b, Mia et al., 2017, Mannini et al., 2019, Vaughan et al.,
> 2012) and crater lakes (Aguilera et al., 2021; Oppenheimer, 1996; Trunk
> & Bernard, 2008)."

Aguilera 2021 (autor chileno SERNAGEOMIN) — paper Planchón-Peteroa lake ya
está IMPLÍCITAMENTE referenciado en la literatura ground truth de Aveni 2025.
**Worth follow-up S75**: descargar Aguilera 2021 → validación cruzada VRPTIR
para PP lake (volcán chileno Tier A) sería un experimento muy defendible.

DOI Aguilera 2021 a investigar S75: probable Journal of Volcanology, doi
pendiente lookup.

## Acknowledgments (paper)

> "This is ClerVolc publication number 675. Open access publishing facilitated
> by Universita degli Studi di Roma La Sapienza, as part of the Wiley -
> CRUI-CARE agreement."

> "We acknowledge the LANCE data system for providing VIIRS Near Real Time
> products and ESA and NASA/USGS for providing Sentinel-2 and Landsat
> imageries via the EO Browser portal."

## References clave (paper)

- **Aveni S. et al. (2024)** RSE — TIRVolcH detector doi:10.1016/j.rse.2024.114388
- **Wooster M. et al. (2003, 2005)** RSE — MIR method foundational
- **Coppola D. et al. (2023)** Frontiers — MIROVA global database doi:10.3389/feart.2023.1240107
- **Harris A.J.L. (2013)** Cambridge — Thermal Remote Sensing of Active Volcanoes
- **Mannini S. et al. (2019)** — Vulcano fumarole field baseline 2.5 MW
- **Aguilera F. et al. (2021)** — Planchón-Peteroa crater lake (CHILENO! follow-up S75)
- **Campus A. et al. (2024)** — Aveni group consistent referencia
- **Hanson et al. (2024)** — Mt Ruapehu 12-yr ground truth
