# A4 · Aveni, Laiolo, Campus, Massimetti & Coppola 2023 — el molde MIROVA para un sensor nuevo

*The Capabilities of FY-3D/MERSI-II Sensor to Detect and Quantify Thermal Volcanic Activity:
The 2020–2023 Mount Etna Case Study.* **Remote Sens. 15, 2528**, DOI 10.3390/rs15102528.
Autores todos canon (Sapienza + Torino). PDF: `documentacion/The_Capabilities_of_FY-3DMERSI-II_Sensor_to_Detect.pdf`.
Páginas = las impresas del journal ("N of 24").

**Veredicto**: el mejor precedente de cómo MIROVA incorpora un sensor. Confirma que el
remuestreo a grilla UTM es paso obligado de la cadena, confirma con datos propios que **el VRP
baja cuando sube el cenit**, y deriva el coeficiente k **teóricamente** (Planck) — método que
reproduce exactos dos de nuestros tres coeficientes.

## 1. Área de píxel y geometría de vista

> "Following the MIROVA structure, MERSI-II bands 21 and 24 were resampled to a regular UTM
> 51 × 51 km grid, centred on the volcano's summit as per coordinates provided by the Global
> Volcanism Program [84]." (p. 8)

**UTM, 51 × 51 km, centrada en la cumbre, coordenadas del Smithsonian GVP v5.0.2.** Idéntico a
Campus 2022 para VIIRS 750 m: dos sensores, dos papers, la misma grilla → **el remuestreo no es
detalle de un paper, es el paso (ii) de la cadena NRT.** Nosotros no lo tenemos:
`ENABLE_UTM_REGRID` = `False` importando `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`
(el flag se lee de la sección `thresholds:`, `pipeline/profile.py:720`).

**Qué no dice**: el método de interpolación. `nearest`, `bilinear`, `interpolat` → **0
ocurrencias** en 24 páginas. El paso de destino se infiere 1 km ("the nominal resolution of a
given pixel (for MERSI-II 1 km²)", p. 7).

**El paso previo que nos falta**: antes de remuestrear eliminan los píxeles bow-tie (algoritmo
de Liu et al. 2008):

> "identiﬁcation and removal of pixels affected by the bow-tie phenomenon is a crucial step in
> thermal remote sensing of volcanic areas, as duplicate pixels might lead to overestimation of
> the thermal anomalies" (p. 8)

O sea: el remuestreo **no multiplica duplicados** — los duplicados se borran primero, y recién
después se reparte la energía del píxel elongado real sobre la grilla fija. En VIIRS eso viene
hecho a bordo (`pipeline/process_viirs.py:80`, `65533 = Bowtie_Deleted`); en MODIS no hacemos
nada equivalente (`grep -i "bow.\?tie\|overlap" pipeline/process_modis.py` sólo da un comentario
de footprint, línea 535).

**Cenit — confirman nuestro hallazgo S128 con sus propios datos:**

> "as in images acquired almost simultaneously, the only increase in the satellite zenith
> corresponds to a decrease in the VRP. This, as previously discussed by [92], is partially
> related to the attenuation of the MIR radiance in the function of the satellite zenith angle
> due to the increased path length affecting the atmospheric transmittance. Moreover … high
> satellite zenith make the radiance of a potential subpixel hotspot to be integrated over an
> area gradually increasing toward the end of the swath … **Although this is partially corrected
> during the resampling step (see [9]), residual artefacts can hardly be removed entirely**"
> (pp. 15–16)

Los dos mecanismos que nombran son los dos que nos importan: transmitancia atmosférica **y**
dilución del foco sub-píxel en un área que crece hacia el borde de barrido. Y la frase clave:
el remuestreo **corrige parcialmente** el segundo. Nosotros no remuestreamos → no corregimos →
el ratio cae de 0,796 a 0,570 entre nadir y 35-50°. **El paper predice el signo y la causa de
lo que medimos.**

La Tabla 3 (p. 16) lo cuantifica con 14 pasadas casi simultáneas de los tres sensores: mediana
del cociente MERSI/MODIS **2,07× con 22° medianos de diferencia de cenit** (calculado sobre la
tabla). Extremos: 463 MW @ 4° vs 80 MW @ 56° (22-dic-2022); 278 MW @ 5° vs 2 MW @ 68°
(30-ene-2023).

**Filtro de cenit**: no lo aplican al procesar, sí como estrato de análisis — **≤ 40°**, no 50°:

> "the relative sensitivity of MERSI-II is largely improved when considering only the scenes
> acquired with zenith angles ≤ 40°" (p. 10)

La frecuencia de detección sube 28,20 → 44,45 % (MERSI), 35,24 → 45,66 % (MODIS), 48,34 →
57,56 % (VIIRS). **Casi la mitad del "no detectamos" es geometría, no ausencia de calor.**
Leemos `sensor_zenith` pero no filtramos (`grep -rn -i "MAX_ZENITH\|zenith_max\|zenith >"
pipeline/ scripts/` → vacío).

## 2. El coeficiente k: derivación TEÓRICA, no empírica

Contradice A1 en este caso. Parten de Planck (Eq. 4, c₁ = 1,19 × 10⁸, c₂ = 1,44 × 10⁴), invocan
la aproximación de Wooster 2003 para 600–1500 K (Eq. 5, `L(λ~4 µm) ≈ αT⁴`) y ajustan α por
longitud de onda sobre 3,5–4,15 µm (Fig. 3):

> "2.88 × 10⁻⁹ (W m⁻⁴ sr⁻¹ µm⁻¹ K⁻⁴) both for MERSI and VIIRS bands 21 and M-13 … centred at
> 4.05 µm; and 2.96 × 10⁻⁹ … for MODIS band 21, centred at 3.959 µm" (p. 9)

con `VRP = ΔL_MIR × (σε / α ε_MIR) × A_pix` (Eq. 2, p. 8), ε/ε_MIR = 1, **A_pix en km²**. Y lo
ofrecen como receta general: *"we propose a simple method to calculate the same coefficient for
other sensors operating in the MIR region"* (p. 8).

| sensor | λ | σ/α del paper | nuestro | desvío |
|---|---|---|---|---|
| MODIS B21 | 3,959 µm | **19,155** | 18,9 | −1,33 % |
| VIIRS M13 / MERSI b21 | 4,05 µm | **19,688** | 19,7 | +0,06 % |
| VIIRS I04 | 3,74 µm | **17,986** (interpolado de Fig. 3) | 18,0 | +0,08 % |

El 18,0 de I-4 **no está en el paper**: sale de interpolar α(λ) entre sus dos puntos y da
17,986. Nuestros dos coeficientes VIIRS caen dentro del 0,1 %; el MODIS 18,9 (histórico de
Wooster) queda 1,3 % bajo. **No es el problema.**

## 3. El fondo

Casi no describen detección, pero la Eq. 3 nos interpela:

> "∆L_MIR = L_MIRhot − L_MIRbk … where L_MIRbk is the radiance of the background, namely the
> **average radiance of the surrounding, non-alerted pixels**." (p. 8)

**"non-alerted"**: el fondo excluye los píxeles alertados. Nuestro camino por defecto no lo
hace — `compute_bg_stats` recibe el anillo con `ENABLE_TEST1_K1_BG_EXCLUDE = False` (verificado
importando `pipeline.profile`; llamada en `process_modis.py:507-514`), y ese `L_bg_global` es el
que entra en `delta_L` (línea 987). Sólo el kernel local 3×3 excluye otros hot (línea 973,
opt-in en 5 volcanes). Apoyo textual directo al frente del fondo autorreferente de S126 — **y no
es el GAP #A cerrado en S115**, que era sobre el pool μ/σ de *detección*, no sobre el fondo de
la *magnitud*.

No hay N·σ, ni NTI (`grep -cw NTI` → **0**), ni umbrales, ni ROI dual: todo delegado a
Coppola 2016a.

## 4. Validación cross-sensor: su banda es más laxa que la nuestra

Spearman ρ 0,93–0,95; R² 0,79–0,84; **pendientes de mejor ajuste m entre 0,59 y 1,13** sobre
medias semanales (p. 12). Incertidumbre declarada de TADR y volumen: **± 30 %** (pie de Fig. 10,
p. 18). Sobre el régimen bajo:

> "the weekly VRP timeseries in Figure 6a revealed a systematic prevalence of MERSI-II
> detections in the lower thermal regime (<10 MW). **Despite this can be neglected for
> volcanological applications** and did not affect the results obtained in this work…" (p. 19)

Aceptan como "excelente acuerdo" pendientes de 0,59 a 1,13 entre sensores del propio grupo.
**Nuestro 0,73 global está adentro de esa banda.**

## 5. Sub-MW, piso y nube

- **No hay piso VRP declarado.** El eje de los histogramas parte en 0,1 MW ("The logarithmic
  scale span from 0.1 MW to 100 GW", p. 12) pero es escala de gráfico, no umbral. Moda 10–50 MW;
  > 100 MW = derrames y paroxismos (p. 12).
- **Nube: sin test automático.** Para el TADR, *"we visually inspected the elaborated scenes to
  discard those unsuitable"* (p. 10) — inspección **manual**, coherente con A76. Diagnostican con
  TIR, no MIR: *"clouds are better deﬁned … in the long-wave portion"* (p. 15).
- **Procesan día y noche** (Fig. 9 distingue *"day-time and night-time acquisitions"*, p. 16;
  Tabla 3 trae pasadas de 12:15–13:00 LT). Nosotros somos sólo nocturnos.

## 6. Contradicciones, silencios y bibliografía

**Nos contradice en**: (a) no remuestrear; (b) no descartar bow-tie en MODIS; (c) fondo con
píxeles alertados adentro; (d) sólo nocturno; (e) `A_pix` nadir fijo **sin** el remuestreo que
lo justifica — el nadir fijo de Coppola/Campus vive *dentro* de una grilla remuestreada, el
nuestro flota sobre el granule crudo.

**Qué NO dice, contra lo que podría atribuírsele**: no describe el algoritmo de detección (0
menciones de NTI, de desviación estándar, ni de umbrales que no sean de saturación); no da el
método de interpolación; **no usa máximo diario** (`daily max` → 0 ocurrencias; usan media
semanal para correlacionar y media móvil de 1 día para TADR), así que **no respalda el frente 6**
tal como lo plantea Laiolo 2026; y no filtra por cenit al procesar, sólo al analizar.

**Bibliografía que no tenemos**:
- **[9] Coppola et al. 2012**, *Radiative Heat Power at Stromboli 2000–2011*, JVGR 215, 48–60 —
  **la referencia del paso de remuestreo y del bow-tie.** Prioridad 1, frente 3.
- **[92] Coppola, James, Staudacher & Cigolini 2010**, Bull. Volcanol. 72, 341–356 — fuente de
  la atenuación MIR por cenit. Prioridad 1, frente de geometría.
- [82] Liu et al. 2008, *A New Prompt Algorithm for Removing Bowtie Effect of MODIS L1B Data*,
  DOI 10.1109/CISP.2008.31 — el algoritmo de bow-tie que usa MIROVA.
- [88] Coppola, Laiolo, Piscopo & Cigolini 2013, JVGR 249, 39–48 — `c_rad`.
- [83] Nishihama et al. 1997, MODIS L1A Earth Location ATBD SDST-092 — solape de barrido.
