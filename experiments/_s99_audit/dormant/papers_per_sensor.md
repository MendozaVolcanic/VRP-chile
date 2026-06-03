# Auditoría de papers: ¿MIROVA NRT es por-sensor uniforme o por-volcán/régimen? (S99)

Pregunta de Nicolás (A62): ¿MIROVA conmuta de método por volcán/régimen (lava lake
Eq.16, crater lake Eq.25), o es UN algoritmo por SENSOR uniforme entre volcanes?
Citas VERBATIM de los papers locales (`documentacion/`). Veredicto: **uniforme por
sensor**; los métodos lava/crater lake son productos manuales de segundo nivel, NO el
pipeline NRT. → DF-1/DF-2 son drifts, no se adoptan operacionalmente.

## Q1 — Coppola 2016a (sp426_5.txt): algoritmo único, NO por volcán
- *"the main motivation for developing the MIROVA algorithm was to develop a hotspot
  detection system that does not require the analysis of historical data sets...
  without a case by case determination of adapted thresholds"* (~L98-119).
- *"self-adapting thresholds for each analysed scene 'independent' of the local
  conditions (climate, temperature and topography)"* … *"may also be applied to other
  volcanoes... by using the same spatial grid and ROIs"* (~L431-441).
- *"the MIROVA algorithm is completely autonomous and does not require historical
  (temporal) analysis... easily exportable to several target volcanoes"* (~L689-695).
- 5 pasos uniformes (extract / crop+resample / ROIs / hotspot detection / RP). VRP =
  Σ RPPIX Wooster (Eq.7-8). "lava lake"/"crater lake" como métodos del pipeline: NO
  encontrado (solo en bibliografía).

## Q2 — Coppola 2024 chapter: lava/crater lake = "Applications", manual, calibrado
- φ_rad two-component en voz pasiva: *"the radiant power of the VTF can be calculated
  as: φrad = Ahot σε (Thot⁴ − Tbk⁴)"* (~L1116-1144).
- Lava lake (Nyiragongo/Burgi), sección 5 "Applications": *"This approach requires
  specific calibrations based on the knowledge of the crater morphology... and an
  assumption of the effective temperature of the lava lake (Te)"* … *"after each
  drainage episode it is essential to recalibrate the model"* (~L2681-2724).
- Crater lake (Ruapehu, Eq.25): *"This simple approach was applied to the VIIRS
  data... at the Ruapehu volcano"* (~L2740-2806).
- Cierre: *"these second-level products are valid only within the limits of the
  assumptions underlying the models"* (~L2800).
- Ningún *"MIROVA applies/computes automatically"* — siempre *"can be / was applied /
  after a calibration"*.

## Q3 — "VRP inadequate for low-T VTFs" = caveat de validez, no cambio de algoritmo
- *"the method works well with an error ±30% exclusively if the integrated temperature
  of the VTF is comprised between 600–1500 K... this limit implies that the VRP is
  inadequate for estimating the radiant power of low-temperature VTFs, while is
  particularly indicated to measure... Thot ≥ 600 K"* (~L1158-1177).

## Q4 — Única variación por-objetivo: ROI/summit + SENSOR (no volcán)
- *"Eq.17 can be applied to any sensor with a MIR channel... by adapting Apix and α to
  the sensor specifications"* (MODIS α=2.96e-19, VIIRS750 α=2.88e-19) (~L1148-1155).
- No encontrado: selección de método/parámetros por volcán más allá de ROI + sensor.

## Veredicto operacional
MIROVA NRT = UN algoritmo por sensor, uniforme. El fix de magnitud fiel al clon es
uniforme por sensor sobre los píxeles alertados (Candidatos A/B), NO Eq.16 por-volcán.
