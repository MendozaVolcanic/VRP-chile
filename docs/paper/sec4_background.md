# 4. Background: the MIROVA algorithm

MIROVA (Middle InfraRed Observation of Volcanic Activity) is the hotspot detection and
radiative power retrieval scheme introduced by Coppola et al. (2016a) for MODIS Level 1B
data and later extended by the same group to the two VIIRS resolutions. This section states
what the algorithm does, in the terms and parameter values published by its authors and
citing only sources authored by the MIROVA group, because the fidelity of our implementation
(Section 5) is measured against these definitions.

## 4.1 MIR radiative power and the Wooster approximation

Between roughly 600 and 1500 K — the range of most active lava surfaces — the
pixel-integrated middle infrared (MIR, near 4 μm) radiance is very nearly proportional to the
fourth power of the emitter temperature, so a single MIR band recovers the radiated power
without solving separately for the sub-pixel hot fraction and its temperature (Coppola, 2025,
Eq. 17, after Wooster et al., 2003). The resulting Volcanic Radiative Power (VRP) is
instrument-independent: any sensor with a MIR channel can yield it, by adapting the pixel
area and the wavelength-dependent proportionality constant.

<!-- src: documentacion/coppola2024_chapter.txt:1101-1120, 1131-1143 -->

For each alerted pixel the "above background" 4 μm radiance is the difference between the
radiance of that pixel and a background radiance estimated as the arithmetic mean of the
pixels surrounding the active pixel, or surrounding the active cluster (Coppola et al.,
2016a, Eq. 6). The radiative power is then RP_PIX = 18.9 · A_PIX · ΔL4_PIX, with A_PIX the
pixel size (1 km² for the resampled MODIS pixels), and a multi-pixel alert is the sum of its
pixel values (Eqs 7 and 8). The stated uncertainty is ±30 % above 600 K; for cooler bodies
the MIR method returns only a minimum estimate of the total thermal output.

<!-- src: documentacion/sp426_5.txt:350-357, 374, 384-385, 388-398, 689-702 -->

## 4.2 The Normalized Thermal Index and the spectral–spatial detection

Detection is hybrid: a spectral filter followed by a contextual spatial filter. The spectral
part starts from the Normalized Thermal Index of Wright et al. (2002),
NTI = (L_MIR − L_TIR)/(L_MIR + L_TIR) (Coppola et al., 2016a, Eq. 1). Because the NTI is
sensitive to surface type, season and topography, MIROVA normalises it per image: treating
each pixel as isothermal at the TIR brightness temperature gives an "apparent" NTI
(Eqs 2–3), and a quadratic regression of observed against apparent NTI yields a background
index NTI_bk = a·NTI_app² + b·NTI_app + c (Eqs 4–5), fitted separately for every image. The
Enhanced Thermal Index is the residual, ETI = NTI − NTI_bk, on which hotspots stand out where
they are weak or absent in the raw NTI.

<!-- src: documentacion/sp426_5.txt:207-216, 220-232, 257-280, 310-313 -->

The spatial part subtracts from each pixel the arithmetic mean of its eight neighbours,
producing the dNTI and dETI matrices. Coppola et al. (2016a) are explicit that this is a plain
spatial filter: clouds are not taken into account, and all eight neighbours enter the average
regardless of the surface they image. Pixels at the edge of the resampled matrices, and those
with dNTI or dETI below −0.1, are declared unsuitable and excluded.

<!-- src: documentacion/sp426_5.txt:238-249, 266-283 -->

Thresholds are applied over two concentric regions of interest: an inner 5 × 5 km box centred
on the summit (ROI1), where small-scale activity is expected, and the surrounding 50 × 50 km
frame (ROI2). Test 1 is a fixed threshold, NTI_PIX > K1, with K1 common to both ROIs but
distinct for night and day, inherited from MODVOLC (Wright et al., 2002); pixels satisfying
it are flagged active and then discarded from the subsequent steps. Tests 2 and 3 are
contextual and must both hold: a pixel is flagged active when dNTI_PIX > C1 or
dNTI_PIX > μ_dNTI + C2·σ_dNTI, and simultaneously when the same disjunction holds for dETI,
μ and σ being the mean and standard deviation of all suitable pixels in the image. C1 and C2
differ between the ROIs — which differ in size and in prior probability of containing an
anomaly — and between night and day, because solar effects amplify the variability of both
matrices. Their published values (Table 1) are K1 = −0.8 night and −0.6 day; C1 = 0.003 in
ROI1 and 0.01 in ROI2 at night, 0.02 in both by day; C2 = 5 and 10 respectively at night, 15
in both by day.

<!-- src: documentacion/sp426_5.txt:186-208, 294-306, 315-343 -->

## 4.3 Second run and calibration of the thresholds

Active pixels perturb the neighbourhood average the spatial filter relies on, so the dNTI and
dETI values of pixels adjacent to a detection are artificially depressed. To recover them,
MIROVA repeats the spatial analysis with all previously detected active pixels removed and
reapplies Tests 2 and 3 to the new matrices, only when the first run produced at least one
detection.

<!-- src: documentacion/sp426_5.txt:329-356 -->

The threshold set was calibrated on more than 20 000 images of Stromboli and Mt Etna as the
best compromise between omission (~10 %) and false detections (~5 %). The trade-off is
quantified for C2: at C2 ≈ 10 false detections are efficiently suppressed but more than 25 %
of small alerts (<10 MW) are lost, whereas at C2 ≈ 3 only 7 % are missed at the cost of more
than 7 % false detections. Because these values describe the natural variability of dNTI and
dETI, they act as self-adapting thresholds, independent of local climate and topography,
which makes the scheme exportable without processing a historical archive. Later operational
versions add an integrated-ROI formulation, summing the excess MIR radiance over the whole
ROI rather than over discrete alerted pixels; the product's detectable floor is of the order
of 1 MW.

<!-- src: documentacion/sp426_5.txt:400-445; documentacion/BIBLIOGRAPHY_SYNTHESIS.md:89-93 -->

## 4.4 Sensors, grids and products

Cropping and resampling precede detection and are not cosmetic: MODIS ground pixels grow with
scan angle — up to about 10 km² at 55° — so a sub-pixel hotspot would otherwise be integrated
over a variable area, and the contextual scheme requires a homogeneous pixel scale. MIROVA
crops the Level 1B data to a 50 × 50 km grid centred on the summit, taking coordinates from
the Global Volcanism Program database, and resamples onto an equally spaced 1 km grid. The MIR
channel is a composite band at 3.959 μm built from band 21 or band 22 depending on whether the
high-gain band saturates; the TIR channel of the NTI is band 32 at 12.02 μm.

<!-- src: documentacion/sp426_5.txt:140-145, 149-169, 173-183, 211-216 -->

The same algorithm was later applied to VIIRS. For the 750 m M-bands, Campus et al. (2022)
resample onto a UTM 51 × 51 km grid centred on the summit, keeping the nominal resolution and
producing 67 × 67 pixel matrices; the bands are M13 (3.973–4.128 μm) and M15
(10.263–11.263 μm). For the 375 m I-bands, Campus et al. (2024) use I4 at 3.74 μm with I5 at
11.45 μm over a pixel area of 140 625 m², reporting fumarolic detections between 0.02 and
1.11 MW. At Sabancaya the 375 m data revealed thermal anomalies about ten years earlier than
MODIS at 1 km (Coppola et al., 2022; Coppola, 2025).

<!-- src: documentacion/BIBLIOGRAPHY_SYNTHESIS.md:80-84, 98-105, 111-120, 273-275 -->

## 4.5 What MIROVA publishes, and what is not published

The near-real-time chain ingests MODIS-NRT granules from LANCE, which delivers Level 1 data
within about 3 h of acquisition, and posts updated NTI maps and radiative power time series
within 1–4 h of the overpass. Each detection is published as a radiative power value with a
thermal map, labelled on an intensity scale: Low below 1 MW, Moderate 1–10 MW, High
10–100 MW, Very High 100–1000 MW, Extreme 1000–10 000 MW.

<!-- src: documentacion/sp426_5.txt:639-673, 681-685 -->

Two published caveats bear on any attempt to reproduce the system. First, clouds are handled
a posteriori: the algorithm does not discriminate cloudy pixels, and cloud-affected data are
discarded by visual inspection after the fact; Campus et al. (2022) evaluate the unsupervised
near-real-time mode, leaving the raw data without such filters. Second, false alerts occur
mainly in daytime images at the edges of water bodies and within scattered clouds and
typically radiate less than 5 MW, while fires and anthropogenic heat sources are
indistinguishable from volcanic hotspots. Coppola et al. (2014) tested a 2 MW cutoff and
rejected it, because it reduced correct detections from about 79 % to below 59 % —
preferring, in their words, to keep some false alerts rather than miss real hotspots.

<!-- src: documentacion/sp426_5.txt:358-368, 689-712; docs/AUDIT_S128.md:518-534 -->

What none of these publications provides is executable code. The algorithm is fully specified
in the literature, but the system is distributed as a web product covering target volcanoes
chosen by its operators, and no reference implementation has been released for independent
use, audit or extension. That gap is what the present work addresses.

<!-- src: documentacion/sp426_5.txt:132-136, 659-673 -->

---

## References used in this section

| Key | Reference | DOI |
|---|---|---|
| Campus et al., 2022 | Campus, A., Laiolo, M., Massimetti, F., Coppola, D. The transition from MODIS to VIIRS for global volcano thermal monitoring. *Sensors* 22(5):1713. | 10.3390/s22051713 |
| Campus et al., 2024 | Campus, A., Aveni, S., Laiolo, M., Massimetti, F., Coppola, D. Thermal unrest at La Fossa (Vulcano Island, Italy): the 2021–2023 VIIRS 375 m MIROVA-processed dataset. *Bull. Volcanol.* 86:25. | 10.1007/s00445-024-01721-z |
| Coppola et al., 2014 | Coppola, D. et al. Strombolian activity from space (*Int. J. Remote Sens.*; quoted pp. 3413, 3417–3418). | 10.1080/01431161.2014.903354 |
| Coppola et al., 2016a | Coppola, D., Laiolo, M., Cigolini, C. et al. Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system. *Geol. Soc. London Spec. Publ.* 426(1):181–205. | 10.1144/SP426.5 |
| Coppola et al., 2022 | Coppola, D., Valade, S., Masias, P., Laiolo, M., Massimetti, F., Campus, A. et al. Shallow magma convection … during the dome-forming Sabancaya eruption (2012–2020). *Bull. Volcanol.* 84:16. | 10.1007/s00445-022-01523-1 |
| Laiolo et al., 2026 | Laiolo, M. et al. *Bull. Volcanol.* 88:11 (cadena NRT de MIROVA sin filtrado automático de nubes; verificado verbatim S128, p. 4). Título completo por confirmar. | 10.1007/s00445-025-01932-y |
| Coppola, 2025 | Coppola, D. Thermal Monitoring of Volcanoes from Space. In: *Modern Volcano Monitoring*, Springer, pp. 325–364. | 10.1007/978-3-031-86841-2_11 |
| Wooster et al., 2003 | Wooster, M. J., Zhukov, B., Oertel, D. Fire radiative energy for quantitative study of biomass burning. *Remote Sens. Environ.* 86:83–107. | [DOI pendiente] |
| Wright et al., 2002 | Wright, R., Flynn, L. P., Garbeil, H., Harris, A. J. L., Pilger, E. Automated volcanic eruption detection using MODIS. *Remote Sens. Environ.* 82:135–155. | [DOI pendiente] |

<!-- src: documentacion/sp426_5.txt:1004-1011, 1026-1030; documentacion/BIBLIOGRAPHY_SYNTHESIS.md:34, 72, 98, 111, 271 -->

---

## Notas para el editor

Todo número de esta sección está anclado a archivo:línea. No quedó ningún placeholder
numérico pendiente. Lo que sigue son las afirmaciones que **no** pude verificar del todo, y
las contradicciones que aparecieron entre fuentes del repo.

1. **La banda TIR del NTI: B32 (12.02 μm) o B31 (11.03 μm).** `sp426_5.txt:214-216` dice
   textualmente que L_TIR es la radiancia del canal TIR, «L32», es decir 12.02 μm, y la
   Tabla 2 de `coppola2024_chapter.txt:1034-1037` repite «TIR (12.02 μm)». El `CLAUDE.md`
   del proyecto y la implementación usan la banda 31 (11 μm). No es un problema de esta
   sección —acá describo lo publicado—, pero **§5 tiene que declarar y justificar esa
   divergencia**, porque hoy queda como diferencia no explicada frente al canon.

2. **El tamaño de la grilla: 50 × 50 km o 51 × 51 km.** Coppola et al. (2016a) dice
   50 × 50 km para MODIS (`sp426_5.txt:164-167, 201`). Campus et al. (2022), verbatim en
   `BIBLIOGRAPHY_SYNTHESIS.md:99`, dice **UTM 51 × 51 km** y «matrices de 51 × 51 píxeles
   obtenidas de MODIS». Escribí 50 × 50 km para MODIS y 51 × 51 km para VIIRS 750 m porque
   es lo que dice cada fuente, pero las dos no pueden ser exactas a la vez. Conviene una
   nota al pie, o resolverlo contra el capítulo Springer.

3. **A_pix de VIIRS M-band: 0,5625 km² o 0,75 × 10⁶ m².** `coppola2024_chapter.txt:1141-1143`
   da «A_pix = 0.75 × 10⁶ m²» para las bandas de 750 m, pero 750 × 750 m son 562 500 m², que
   es lo que registra `BIBLIOGRAPHY_SYNTHESIS.md:101` citando a Campus 2022. Parece un desliz
   del capítulo. **No usé ninguno de los dos números en §4** para no propagarlo; el valor
   operativo va en Methods.

4. **«Laiolo 2026» SÍ está en el repo — corregido S135.** La nota original de esta sección
   decía que no existía. Es el falso negativo de la regla A89: el archivo está nombrado por
   DOI, `documentacion/s00445-025-01932-y.pdf` (Laiolo et al., *Bull. Volcanol.* 88:11), y
   buscar «laiolo» devuelve cero. `docs/MISSION.md:38-60` lo lista entre los once papers
   canónicos y registra que S128 verificó **verbatim** contra la p. 4 del PDF la afirmación
   de que la cadena NRT de MIROVA no aplica filtrado automático de nubes. El texto de §4.5
   está anclado a Coppola et al. (2016a) (`sp426_5.txt:247-249` y `:362-368`), que sostiene
   lo mismo y es la fuente primaria del algoritmo; **queda pendiente** agregar Laiolo como
   cita directa y su fila a la tabla de referencias con el DOI 10.1007/s00445-025-01932-y.

5. **Las citas de Coppola et al. (2014) son de segunda mano.** Los pasajes del corte de 2 MW
   y del 79 % → 59 % los tomé de `docs/AUDIT_S128.md:518-534`, que los declara verificados
   verbatim contra el PDF (`coppola2014_ijrs_strombolian_*.pdf`, que está en
   `documentacion/`). **No los verifiqué yo mismo contra el PDF** porque el texto extraído no
   está en el repo. Antes de enviar, cotejar esas dos frases contra el original: son las que
   sostienen el argumento de «recall sobre precisión» del paper entero. El título que puse en
   la tabla de referencias para ese paper es tentativo — falta completarlo.

6. **«Ninguna implementación de referencia publicada» es la única afirmación de la sección
   sin fuente positiva.** Es un argumento de ausencia: `sp426_5.txt:132-136` y `:659-673`
   describen el sistema como servicio web sobre una lista de volcanes objetivo, y ninguna
   fuente del repo menciona código distribuido. Es defendible, pero un revisor puede pedir una
   búsqueda explícita (Zenodo/GitHub del grupo de Turín) antes de afirmarlo en letra de molde.

7. **Coppola 2015 vs Coppola 2016a.** El prompt sugería un «Test 1 integrated-ROI (Coppola
   2015)». `BIBLIOGRAPHY_SYNTHESIS.md:36-47` documenta que los dos nombres son **el mismo
   paper** (SP426.5) y que el Test 1 está dentro de `sp426_5.txt:300`. La formulación
   integrada sobre la ROI entera no es de ahí: viene de las versiones operacionales
   posteriores (`BIBLIOGRAPHY_SYNTHESIS.md:89-93`, Coppola 2020/2023). Redacté §4.3 con esa
   separación; si el paper quiere citar la Eq. 1 integrada, hay que citar Coppola et al.
   2020/2023, no 2016a. **Esas dos referencias todavía no están en la tabla de arriba** porque
   no tengo su cita completa verificada en el repo.

8. **La escala de intensidad está en inglés en la fuente.** Coppola et al. (2016a) `:684-685`
   da Low / Moderate / High / Very High / Extreme. El «Muy Bajo» que usa el producto
   per-volcán de mirovaweb.it (y nuestro dashboard) **no aparece en ninguna fuente de
   `documentacion/`** — es la etiqueta del sitio web actual, no del paper. No la usé en §4; si
   el paper la menciona en §6, hay que decir de dónde sale.

9. **El esqueleto del borrador S72 tenía un error de física que corregí.**
   `docs/PAPER_VRP_CHILE_DRAFT_S72.md:138` define el NTI sobre temperaturas de brillo
   (`BT_MIR`, `BT_TIR`). El paper lo define sobre **radiancias** (`sp426_5.txt:211-216`).
   También describe el ETI como «extended TIR test for high-T regimes where MIR saturates»,
   que no es lo que dice la fuente: el ETI es NTI menos el fondo NTI_bk de la regresión
   cuadrática (`sp426_5.txt:275-280`). Ambas cosas quedaron corregidas en esta prosa.

10. **MIROVA no es night-only.** El prompt pedía «night-only» en §4.4, pero la fuente
    describe procesamiento **diurno y nocturno con parámetros distintos**
    (`sp426_5.txt:302-306, 315-321`, y la Tabla 1 tiene columna Daytime). La restricción a
    pasadas nocturnas es una decisión **nuestra**, así que va en §5, no acá. §4.2 ya deja
    dicho que los umbrales se separan día/noche.

11. **§4.2 remite a «Table 1» del manuscrito** para los umbrales, y además los repite entre
    paréntesis. Si esa tabla termina existiendo (está prevista en el esqueleto S72), sacar el
    paréntesis; si no, dejarlo y quitar la remisión.
