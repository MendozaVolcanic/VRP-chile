# MIROVA — Citas literales detalladas (Anti-olvido)

> Documento creado S57 (2026-05-17) tras Nicolás señalar que durante la
> sesión maratón no extrajimos suficiente detalle de los papers MIROVA core.
> La cita "T_bk is retrieved from the pixels adjacent to the hot one"
> (Coppola 2024 L1129) estuvo ahí toda la sesión sin ser vista. Este doc
> recopila citas verbatim con ubicación archivo:línea. Lectura obligatoria al
> inicio de cada sesión que toque pipeline/.

Convención: `[file:line]` = `documentacion/<archivo>` línea de la cita.

---

## 1. Background calculation (T_bk / L_bg)

### 1.1 Coppola 2024 chapter (Springer 2025) — kernel local hot pixel

- **[coppola2024_chapter.txt:1129]** "If T bk is retrieved from the pixels
  adjacent to the hot one, Eq. 14 can be solved by assuming one of the two
  other unknowns (T hot or A hot)".
- **[coppola2024_chapter.txt:1051]** L_bk "generally calculated from pixel(s)
  surrounding the anomaly".
- **[coppola2024_chapter.txt:974-985]** spatial (contextual) algorithms:
  "the threshold based on the comparison of each pixel with its surroundings.
  When a pixel exceeds the radiance of the adjacent pixels by a certain
  value (threshold) this is considered hot".
- **Implicación operacional**: el background MIROVA NO es ring 5–25 km
  alrededor del vent. Es kernel local de pixels adyacentes al hot pixel
  (3×3 ó 5×5). Nuestro pipeline usa ring 5–25 km median desde vent — drift
  documental a documentar.

### 1.2 Coppola 2016a SP426.5 — L4_bk = arithmetic mean del cluster surrounding

- **[sp426_5.txt:357-359]** "L4bk is estimated from the arithmetic mean of
  all the pixels surrounding the active one (or around the active cluster)".
- **[sp426_5.txt:351]** "Once a pixel is flagged as active, the 'above
  background' at 4 mm radiance (ΔL4_PIX) is calculated as: ΔL4PIX = L4alert
  − L4bk (Eq. 6)".

### 1.3 Campus 2024 VIIRS 375m — same definition

- **[campus2024_extracted.txt:119-124]** "At each alerted pixel, a background
  radiance value (Lpixbk) is also associated, this last computed from the
  arithmetic mean of the radiance of the pixels surrounding the alerted
  one(s). The total background radiance (LMIRbk) is then obtained as the sum
  of Lpixbk".

### 1.4 NTI_bk regresión cuadrática (distinta de L_bk)

- **[sp426_5.txt:259-265]** "A quadratic best-fit regression allows this
  trend to be normalized so that a third empirical index (which we term
  NTIbk) is obtained according to: NTIbk = a·NTIapp² + b·NTIapp + c (Eq. 4).
  parameters a, b and c are obtained for each case, and distinct regression
  coefficients are retrieved from each single image".

---

## 2. Cluster aggregation y reporting

### 2.1 Cluster como suma — Coppola 2016a

- **[sp426_5.txt:387-394]** "When two or more pixels (a cluster of pixels)
  are alerted, the total radiative power is calculated as being the sum of
  the single RPPIX, so that: RP = Σ RPPIX (Eq. 8) where 'n alert' is the
  number of alerted pixels".
- **NO hay primary cluster** en MIROVA core: agregación = suma de TODOS los
  alerted pixels de la escena (después de Tests 1/2/3 + second-pass).

### 2.2 Coppola 2024 confirmando

- **[coppola2024_chapter.txt:1057-1071]** "ΔL_tot(λ) = Σ_{k=1}^{N_pix} ΔL_k
  (Eq. 13) where N_pix is the number of pixels above the background, and
  ΔL_k is the excess radiance of the k-th pixel".
- **[coppola2024_chapter.txt:1080-1090]** métricas reportadas: ΔL_tot,
  N_pix, ΔT_max. NO se reporta "vrp del primary cluster".

### 2.3 Campus 2024 — agregación scene-wide

- **[campus2024_extracted.txt:115]** "LMIRhot = Σ_{i=1}^{Npix} Lalert (Eq. 1)"
  — suma directa de todos los Npix alerted del scene, sin clustering.

---

## 3. Sub-pixel methods (two-component, Eq.14-16)

### 3.1 Two-component model — Coppola 2024 Eq.14-16

- **[coppola2024_chapter.txt:1121-1128]** "L_hotpix(λ, T_hotpix) = f_hot ·
  B(λ, T_hot) + (1 − f_hot) · B(λ, T_bk) (Eq. 14) where f_hot = A_hot / A_pix".
- **[coppola2024_chapter.txt:1132-1141]** "two-component model (Marsh et al
  1980; Dozier 1981) is often applied by assuming a range of realistic
  values for T_hot and calculating un upper and lower boundaries for the
  areas… A_hot = [L(λ) − B(λ, T_bk)] / [B(λ, T_hot) − B(λ, T_bk)] · A_pix
  (Eq. 15)".
- **[coppola2024_chapter.txt:1146]** "φ_rad = A_hot · σ·ε · (T_hot⁴ − T_bk⁴)
  (Eq. 16)" — Stefan-Boltzmann para radiant power una vez A_hot resuelto.
- **Aplicación NRT MIROVA**: NO usa Eq.14-16 en operativa (requiere asumir
  T_hot). Usa **Eq.17 VRP** (MIR method Wooster) directamente.

### 3.2 VRP MIR (Eq.17) — operacional MIROVA

- **[coppola2024_chapter.txt:1117-1122]** "VRP = ΔL_MIR · (σ·ε)/(α·ε_MIR) ·
  A_pix (Eq. 17)".
- **[coppola2024_chapter.txt:1136-1145]** "MODIS λ_MIR = 3.959 μm:
  A_pix = 1×10⁶ m², α = 2.96×10⁻¹⁹. VIIRS 750 m λ_MIR = 4.050 μm:
  A_pix = 0.75×10⁶ m², α = 2.88×10⁻¹⁹".
- **[coppola2024_chapter.txt:1159-1171]** "Eq.17 works with an error ±30%
  exclusively if the integrated temperature of the VTF is comprised between
  600–1500 K. The VRP is inadequate for estimating the radiant power of
  low-temperature VTFs… particularly indicated to measure radiant power
  emitted by the younger portion of the VTF having T_hot ≥ 600 K and
  emplaced for no more than 12–24 h".

### 3.3 VRPTIR (Aveni 2025) — extensión para low-temp

- **[aveni2025_crater_lakes.md:383-396]** "VRPTIR = A_pix · k_TIR · Σ_{j=1}^{Npix}
  (LTIR_hotj − LTIR_bg) (Eq. 9)".
- **[aveni2025_crater_lakes.md:413]** "for λ = 11.45, optimal k_TIR has a
  value of 60.17 μm·sr ±35% (gray shaded region; calculated via Eq. 8)".
- **[aveni2025_crater_lakes.md:355-361]** "in the range ~300–600 K, the
  relationship between RP*_True and ΔLTIR at λ = 11.45 holds, with a ratio
  (k_TIR) within the ±35% interval".
- **[aveni2025_crater_lakes.md:280-288]** "RP_Pixel = A_pix · ε · σ · (BT⁴_hot
  − BT⁴_bg) (Eq. 5)" — Stefan-Boltzmann pure pixel.
- **[aveni2025_crater_lakes.md:423-429]** "VRPTIR holds if the area occupied
  by hot vents (at T = 900 K) does not exceed 0.0025% of the total thermal
  anomaly captured within the pixel".

---

## 4. Test 1 / Test 2 / Test 3 details

### 4.1 Test 1: umbral NTI fijo K1

- **[sp426_5.txt:294-306]** "Fixed NTI threshold… NTIPIX > K1 (Test 1) where
  NTIPIX is the NTI pixel value and K1 is the threshold… settled according
  to the global application and validation of the NTI thresholds within the
  MODVOLC algorithm (Wright et al. 2002). Pixels that satisfy Test 1 are
  flagged as 'active' and subsequently discarded (unsuitable) for further
  steps".
- **[sp426_5.txt:336-343] Table 1**: K1 night = **−0.8** (ROI1 y ROI2),
  K1 day = **−0.6** (ROI1 y ROI2).
- **[coppola2024_chapter.txt:1034-1037] Table 2**: NTI = (L_3.9 − L_12)/(L_3.9
  + L_12), threshold nighttime −0.8, daytime −0.6 (Terra/Aqua MODIS, Wright
  et al. 2002).

### 4.2 Test 2 (dNTI) y Test 3 (dETI): contextuales

- **[sp426_5.txt:316-324]** "a pixel is flagged as 'active' when: dNTI_PIX >
  C1 **or** dNTI_PIX > m_dNTI + C2·s_dNTI (Test 2) **and** dETI_PIX > C1
  **or** dETI_PIX > m_dETI + C2·s_dETI (Test 3)".
- **[sp426_5.txt:326-329]** "m and s are the arithmetic mean and standard
  deviation of all the suitable pixels within the image".
- **[sp426_5.txt:336-343] Table 1 valores**:
  - C1 night: **0.003** (ROI1 summit) / **0.01** (ROI2 scene)
  - C1 day:  **0.02** (ROI1) / **0.02** (ROI2)
  - C2 night: **5** (ROI1) / **10** (ROI2)
  - C2 day:  **15** (ROI1) / **15** (ROI2)
- **[sp426_5.txt:340-343]** Tabla original (parseo confuso, valores
  confirmados S33): ROI1 night 5σ, ROI2 night 10σ, day 15σ.

### 4.3 Definición dNTI/dETI (kernel 8-vecinos aritmético)

- **[sp426_5.txt:240-246]** "Step 2 consists of the spatial analysis… one
  pixel at a time, and consists of subtracting from its value (NTI or ETI)
  the **average (arithmetic mean) of the eight neighbouring pixels**".
- **[sp426_5.txt:247-249]** "the presence of clouds is not taken into
  account by the algorithm and **all eight neighbouring pixels are used to
  compute the spatial average**".

### 4.4 Pixels unsuitable (descartados antes de Tests 2/3)

- **[sp426_5.txt:267-273]** unsuitable pixels son: "all the pixels at the
  edge of the resampled matrices; all the pixels with dNTI or dETI < −0.1".
- **[sp426_5.txt:298-300]** los pixels que satisfacen Test 1 también se
  marcan unsuitable para Tests 2/3 ("subsequently discarded").

### 4.5 Second pass (re-aplica Tests 2/3 a pixels adyacentes)

- **[sp426_5.txt:330-356]** "The last step is applied only if one or more
  pixels have been detected by the previous tests, and focuses on **refining
  the hotspot detection for the pixels adjacent to those already flagged**…
  step 2 (spatial analysis) is performed a second time, being particularly
  careful to **eliminate all of the 'active' pixels already detected**.
  Hence, the previous step (contextual threshold: tests 2 and 3) are applied
  again to the new dNTI and dETI matrices".

---

## 5. NTI / ETI calculation

### 5.1 NTI — Eq.1

- **[sp426_5.txt:211]** "NTI = (LMIR − LTIR) / (LMIR + LTIR) (Eq. 1) where
  LMIR is the radiance recorded by the MIR channel (L21ok) and LTIR is the
  radiance of the TIR channel (L32)".

### 5.2 NTI_app — Eq.3 (apparent NTI asumiendo BT homogéneo en TIR)

- **[sp426_5.txt:222-236]** "we assumed that each pixel was characterized by
  an apparent and homogeneous surface temperature (Tapp) equal to the
  brightness temperature (BT) recorded in the TIR channel (Tapp ≈ BT_TIR)…
  we calculated an apparent MIR radiance: LMIR,app = P_MIR(T_app) (Eq. 2)…
  NTIapp = (LMIR,app − LTIR)/(LMIR,app + LTIR) (Eq. 3)".

### 5.3 NTI_bk — Eq.4/5 (regresión cuadrática por imagen)

- **[sp426_5.txt:259-265]** "NTIbk = a·NTIapp² + b·NTIapp + c (Eq. 4)…
  parameters a, b and c are obtained for each case, and distinct regression
  coefficients are retrieved from each single image".

### 5.4 ETI — Eq.5

- **[sp426_5.txt:275-280]** "the so-called Enhanced Thermal Index (ETI) is
  obtained by subtracting the background NTIbk (Eq. 4) from the observed
  NTI (Eq. 1) so that: ETI = NTI − NTIbk (Eq. 5)".

---

## 6. Alert criteria operacional NRT

### 6.1 Cadena Coppola 2016a SP426.5

1. Resample 50×50 km UTM @ 1 km grid centrado en summit
   ([sp426_5.txt:160-184]).
2. ROIs: ROI1 = inner 5×5 km box; ROI2 = outer 50×50 km menos ROI1
   ([sp426_5.txt:188-206]).
3. Calcular NTI, NTIapp, NTIbk, ETI, dNTI, dETI.
4. Test 1 (NTI > K1) → pixel active.
5. Tests 2 ∧ 3 (dNTI Y dETI superan C1 o m+C2σ) → pixel active.
6. Second pass Tests 2/3 sobre vecinos adyacentes a active pixels.
7. RP_PIX = 18.9 · A_pix · ΔL4_PIX (Eq.7, MODIS 1 km²); RP = Σ RP_PIX (Eq.8).

### 6.2 Definición de "alert" / overpass productivo

- **[sp426_5.txt:397-399]** "MIROVA system detected 2063 alerts over a total
  of 20 494 MODIS overpasses between 2000 and 2013 (~10.1%)".
- Una "alert" = overpass donde al menos 1 pixel pasó Tests, NO 1 alert por
  cluster.

### 6.3 Coppola 2024 — control parámetros

- **[sp426_5.txt:402-409]** "effectiveness of the detection (omission vs
  false alerts) is essentially controlled by the values of parameters K1,
  C1 and C2. In particular, parameter C2 defines the number of standard
  deviations (σ) used to identify the outliers in each ROI. For example,
  the visual inspection of night-time images collected on Etna during 2006
  reveals that a value of C2 ≥ 10 will efficiently avoid false detections".

---

## 7. Casos especiales por sistema

### 7.1 Lava lakes / lava flows (Coppola 2024)

- **[coppola2024_chapter.txt:1166-1171]** "VRP is particularly indicated to
  measure the radiant power emitted by the younger portion of the VTF
  having T_hot ≥ 600 K and emplaced for no more than 12–24 h (Coppola
  et al. 2009)".

### 7.2 Crater lakes / fumarole fields (Aveni 2025)

- **[aveni2025_crater_lakes.md:97-101]** "VRPTIR method to accurately
  retrieve RP from single-band TIR (10.5–12 μm) spectral radiance at
  systems dominated by surface temperatures of <600 K, that is, crater
  lakes and hydrothermal systems".
- **[aveni2025_crater_lakes.md:443-456]** "intended for systems dominated
  by temperatures typical of non-eruptive processes: (1) crater lakes
  (<373 K), (2) fumarole fields (<600 K), (3) hybrid systems".
- **[aveni2025_crater_lakes.md:464]** "detect anomalies for pixel-integrated
  temperatures as low as **0.5 K above the surrounding hot-spot-free
  background**".

### 7.3 Vulcano fumarolic field (Campus 2024)

- **[campus2024_extracted.txt:115-156]** VRP_VIIRS_I4 = k_MIR · A_pix · ΔL_MIR
  con k_MIR (I4) = **18.0 m·sr**, A_pix = 140,625 m². Confirma agregación
  scene-wide (Σ Lalert sin clustering).
- **[campus2024_extracted.txt:118-119]** "ordinary level of VRP (~0.32 MW)
  has been overcome starting in September 2021, to reach a peak of 1.11 MW
  on 4 October 2021".

---

## 8. Discrepancias entre papers (consistencias y drifts)

### 8.1 Consistencias

- L_bk = mean(pixels surrounding hot/cluster) — consistente Coppola 2016a,
  Coppola 2024, Campus 2024, Aveni 2025.
- VRP = Σ pixel contributions (scene-wide, sin primary cluster) — consistente
  los 4 papers.
- Stefan-Boltzmann puro para low-T (Eq.5/16): Aveni 2025 y Coppola 2024.
- Tests 2/3 con **C2·σ over scene** (no kernel local): SP426.5 explícito.

### 8.2 Drifts respecto a nuestro pipeline (documentados)

- **D-bk**: nuestro `std_bg` y `mean_bg` se computan sobre ring 5–25 km
  desde vent — papers usan **pixels adyacentes al hot pixel** (kernel local
  3×3 o vecindad de cluster). Documentar en `docs/MIROVA_DIVERGENCES.md`
  como D10.
- **D-cluster**: nuestro `vent_anchored` selecciona primary cluster cercano
  al vent. Papers NO seleccionan primary — agregan scene-wide. Pero MIROVA
  web reporta un único valor VRP por overpass: la suma de toda la escena,
  no del cluster cráter. Re-confirmar S57+ con OSF v2.5.
- **D2 (S17)**: C2 valores. SP426.5 Tabla 1: ROI1 night = **5σ**, ROI2 night
  = **10σ**. Nuestro pipeline usaba 3σ universal. Drift previo confirmado.
- **D3 RESUELTO S17**: TIR usa Stefan-Boltzmann puro (Aveni 2024 RSE eq.5 +
  Coppola 2024 Eq.16). k_TIR = 60.17 (Aveni 2025) es alternativa, NO adopción
  operacional.

### 8.3 Implicación inmediata para S57+

Si MIROVA NRT realmente computa L_bk desde pixels adyacentes al hot (no
ring-medio): nuestro pipeline está midiendo background a una **escala
distinta**. Esto puede sub-explicar nuestros ratios MW elevados en escenas
con vent cerca de lago/glaciar (ring incluye superficie fría que infla
ΔL frente a lo que mediría el kernel local).

Próximos pasos:
1. Confirmar en Tabla 3 Coppola 2024 si MIROVA reporta "annular background"
   o "local kernel" como práctica.
2. Test pixel-level vs MIROVA TIF en 3 casos canónicos (Puyehue lacolito,
   Villarrica lago cráter, Lascar cráter) comparando L_bk computado con
   nuestro ring vs L_bk kernel 3×3.
3. Si diferencia >30% → registrar como D10 y plan A/B kernel local.

---

## 9. Referencias rápidas (no leer paper completo — ir directo al snippet)

| Topic | Paper | Líneas/Eq |
|-------|-------|-----------|
| T_bk = pixels adyacentes | Coppola 2024 | L1129 + L1051 |
| L4_bk = mean del cluster surrounding | SP426.5 | L357-359 + Eq.6 |
| Σ scene-wide (no primary cluster) | SP426.5 + Coppola 2024 | Eq.8 + Eq.13 |
| Two-component A_hot | Coppola 2024 | Eq.14-16 (L1121-1146) |
| VRP MIR operacional | Coppola 2024 | Eq.17 (L1117-1122) |
| VRPTIR low-T crater lakes | Aveni 2025 | Eq.9 (L383-396) |
| Test 1 NTI > K1 | SP426.5 | Eq. test + L294-306 |
| Tests 2/3 dNTI/dETI ROI dual | SP426.5 | L316-324 + Tabla 1 |
| C1/C2 valores | SP426.5 | Tabla 1 (L336-343) |
| kernel 8-vecinos arithmetic mean | SP426.5 | L240-249 |
| second-pass adyacentes | SP426.5 | L330-356 |
| ROI1 = 5×5 km, ROI2 = 50×50 km | SP426.5 | L186-208 |
| k_MIR VIIRS I4 = 18.0 | Campus 2024 | L155-156 |
| k_TIR = 60.17 μm·sr | Aveni 2025 | L413 |
| Δ0.5 K min detectable TIR | Aveni 2025 | L464 |

---

> **Regla de oro post-S57**: antes de hipotetizar sobre comportamiento
> MIROVA, buscar la cita literal en este doc. Si no está, leer el paper.
> Si el paper no responde, decirlo explícitamente — NO inferir.
