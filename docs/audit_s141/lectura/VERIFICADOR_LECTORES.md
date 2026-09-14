# S141, verificación con contexto limpio de las lecturas A, B, C y D

Verificador: subagente con contexto limpio, 2026-09-14. Sólo lectura: no se modificó ningún archivo del repo salvo este informe; no se tocó git.

**Método.** Las páginas se renderizaron con PyMuPDF a 200 dpi (página completa y cada mitad, para leer bien las dos columnas) en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\render_V\`
(script `r.py` en la misma carpeta; claves: C20 Coppola 2020 Front. Earth Sci. 7:362; CA22 Campus 2022 Sensors; FY Aveni 2023 FY-3D; RR Coppola 2025 Fernandina; F23 Coppola 2023 feart-11-1240107; M20 Massimetti 2020; A24 Aveni 2024 TIRVolcH; A25 Aveni 2025 GRL; R17 Aveni 2025 Remote Sens. 17, 2543; L26 Laiolo 2026; CA24 Campus 2024; KVG Coppola 2021; C13 Coppola 2013; VAN Coppola 2016 Vanuatu; SA17 Laiolo 2017). Toda cita de este informe la leí en la imagen con la herramienta Read. Lo del repo lo leí con sed/grep sobre el árbol de hoy.

Se verificaron los hallazgos de gravedad 3 o más de cada lector y todo hallazgo que afirma algo del repo. Informe escrito de forma incremental.

---

## Hallazgos verificados

### V-01 · origen A5 · CONFIRMADO CON MATIZ
- **Localizador**: C20 (Coppola et al. 2020, Front. Earth Sci. 7:362), p. 4 impresa y del visor, columna derecha, subsección "Distance From the Summit", 1.ª oración.
- **Cita vista**: "shows the distance from the farthest hot pixel to the summit of the volcano".
- **Qué cambia**: pregunta 11 del correo. Contesta la pregunta para la web descrita en 2020; el párrafo siguiente declara precisión de ubicación "± 1 km". Matiz: es la pantalla "Distance from summit" de la web de 2018-2019, no el campo que hoy raspa Mirova-v1.
- **Gravedad**: 3.
- **Propuesta para el catálogo / correo**: en el correo, reformular la pregunta 11 a "Coppola et al. 2020 (p. 4) describe la distancia al píxel caliente más lejano: ¿sigue siendo ese el campo publicado hoy por detección?".

### V-02 · origen A6 · CONFIRMADO CON MATIZ
- **Localizador**: C20, p. 4, columna derecha, subsección "VRP Time Series", 3.ª oración.
- **Cita vista**: "proximal (hotspots located within 5 km from the summit are represented by blue stems)".
- **Qué cambia**: D18 y D13. Es un criterio de color de la serie web, no de detección ni de filtro. Un corte fijo de 5 km en la web de 2020 no coincide con los `inner_radius_km` de 3 a 20 km del repo; pero la afirmación del lector de que eso "matiza" que los radios de los KML sean el criterio de la web queda como SOSPECHA (el paper no habla de KML).
- **Gravedad**: 3.
- **Propuesta para el catálogo**: en D18, nota: "Coppola 2020 p. 4 (VRP Time Series): la web de 2020 separa proximal/distal a 5 km fijos para todos los volcanes, como color de la serie; no es compuerta de detección."

### V-03 · origen A3 · CONFIRMADO CON MATIZ
- **Localizador**: CA22 (Campus et al. 2022, Sensors 22, 1713), p. 7 de 24 (visor 7), §3.2, 3.er párrafo, 1.ª oración; "slightly modified" en el 1.er párrafo, última oración.
- **Cita vista**: "The hot-spot detection algorithm is the same used for MODIS and based on spectral indices and statistical thresholds".
- **Qué cambia**: umbrales VIIRS 750 m. El 1.er párrafo dice también "steps 1 to 4 have been slightly modified from [28] and adapted to VIIRS", así que "el mismo" no excluye cambios de umbral. La afirmación del lector sobre `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:141-142` no la verifiqué línea a línea; sí vi en `:248-249` que la tabla atribuye "n=12 nocturno" a Di Bella 2024 para VIIRS, que es INGV Catania (A9).
- **Gravedad**: 3 (bajo del 4 del lector: la frase no fija umbrales y "slightly modified" deja abierta la pregunta).
- **Propuesta**: pregunta nueva o anexa a la 1 del correo: "Campus 2022 p. 7 says the VIIRS detector is the same as MODIS but steps were slightly modified: were the Table 1 thresholds of 2016a changed for VIIRS M-band and I-band?"

### V-04 · origen A12 (afirma error del repo) · CONFIRMADO
- **Localizador**: CA22, p. 7, §3.2, ecuación (1) y la oración siguiente; contra `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:133` y `:248`.
- **Cita vista**: "where A_pix is the pixel surface in km² (equal to 0.5625 for VIIRS M-bands)"; la ecuación (1) impresa es VRP = ΔL_MIR · 1.97 × 10⁷ · A_pix.
- **Repo**: `:133` dice "k_VIIRS750 = 1.11×10⁷ ⚠️ discrepancia con Campus 2022 (1.97×10⁷), a resolver"; `:248` escribe "1.97×10⁷/Apix". El paper multiplica. 1,97e7 × 0,5625 = 1,108e7: no hay discrepancia.
- **Qué cambia**: limpieza de la síntesis; ningún cambio de pipeline (`pipeline/process_viirs_mod.py:66` usa 19.7 con área nadir).
- **Gravedad**: 2.
- **Propuesta**: corregir la síntesis (no el catálogo): "k = 1,97e7 × A_pix; con 0,5625 km² da 1,11e7, el mismo número de Di Bella; sin discrepancia".

### V-05 · origen A1, B-01, D-06 (bow tie; fusionados) · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas** (tres textos del grupo):
  1. FY (Aveni et al. 2023, Remote Sens. 15, 2528), p. 8 de 24 (visor 8), §3.2, párrafo que viene de la p. 7, 5.ª y 6.ª oración de la p. 8: "Consistently with the MIROVA algorithm, we employed the approach proposed by [82] to identify and isolate the pixels affected by bow-tie distortions, ensuring that original granules were free from geometrical artefacts". La oración previa atribuye la importancia del paso a "[9]".
  2. F23 (Coppola et al. 2023, Front. Earth Sci. 11:1240107), p. 3, §2.1: el párrafo "MODIS Level 1B calibrated radiances..." empieza al pie de la columna izquierda y sigue en la derecha, líneas 1 a 5: "Once the scenes are geometrically corrected (i.e., pixels affected by bow-tie distortions are identified and removed; Coppola et al., 2010)".
  3. C13 (Coppola et al. 2013, JVGR 249), p. 46 impresa (visor 8), Apéndice 2, último párrafo de la columna izquierda: "Pre-processing of the original MODIS granules consists in the removal of the bow-tie effect and resampling into an equal area projection with 1 km pixel size".
- **Veredicto por pieza**:
  - Que MIROVA trata el bow tie de MODIS: confirmado por las tres.
  - Nombre del método (A1, Liu et al. 2008): la p. 8 dice "[82]"; la identidad de [82] la tomó el lector de la capa de texto de la lista de referencias y no la miré en imagen: **SOSPECHA razonable, no verificada**. Además hay tensión de fuentes: F23 cita **Coppola et al. 2010** (Piton de la Fournaise) para el mismo paso, no Liu 2008. El catálogo no debería nombrar un único algoritmo sin esa salvedad.
  - Orden: C13 (2013) y FY (2023, "original granules") ponen el bow tie sobre el gránulo original, antes del remuestreo. F23 (2023) redacta primero el remuestreo y después "once the scenes are geometrically corrected (i.e., ... bow-tie ... removed)", que se lee como aclaración de qué es "corregir geométricamente", no como paso posterior. El lector B lo dejó "ambiguo, no invertido": de acuerdo. Dos textos explícitos contra uno ambiguo: el orden bow tie antes de remuestreo queda bien sostenido.
  - Tratamiento: "identified and removed" (F23), "identify and isolate" (FY), "removal of the bow-tie effect" (C13). Ninguno dice que se promedien; se descartan píxeles duplicados.
  - Salvedad de C13: es 2013, previo al NRT de 2014 y con banda 32 y umbral NTI por erupción (esto último sí lo vi en la misma página, columna derecha arriba), así que no describe el algoritmo operacional; vale para el preproceso.
- **Qué cambia**: D28 sigue abierta y gana cita; D17 (`docs/MIROVA_DIVERGENCES.md:1937-1938`) ya afirma "bow-tie + regrid en ese orden" citando Coppola 2012: ahora hay dos fuentes más del grupo. Pregunta 6 del correo: la mitad bow tie queda contestada en lo esencial; quedaría sólo "¿qué método exacto?".
- **Gravedad**: 4.
- **Propuesta para el catálogo (D28)**: "Tres textos del grupo describen el paso: Coppola et al. 2013 (JVGR 249, p. 46, Apéndice 2: bow tie removido y luego remuestreo a 1 km de área igual), Coppola et al. 2023 (Front. Earth Sci. 11:1240107, p. 3, §2.1: píxeles con bow tie identificados y eliminados, citando Coppola et al. 2010) y Aveni et al. 2023 (Remote Sens. 15, 2528, p. 8, §3.2: 'consistently with the MIROVA algorithm', se aíslan los píxeles con bow tie en los gránulos originales, citando su ref. [82]). Los píxeles duplicados se descartan, no se promedian, y el paso va sobre el gránulo original antes del remuestreo."

### V-06 · origen B-05, A7 (ROI de cumbre; afirma error del repo) · CONFIRMADO (B-05) y CONFIRMADO CON MATIZ (A7)
- **Localizador**: F23, p. 3, columna derecha, mismo párrafo de V-05, líneas 9 a 15.
- **Cita vista**: "in the summit area (5 × 5 km) slightly lower thresholds are applied to detect the smallest thermal anomalies"; y "At greater distances, the algorithm uses slightly higher thresholds which reduce false alerts".
- **B-05**: confirmado. El ROI1 del grupo en 2023 sigue siendo 5 × 5 km, sin valores numéricos.
- **A7**: la afirmación del lector tiene dos mitades. (a) `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:91` escribe "Σ_ROI [...] (integrado-ROI)"; C20 p. 3 (columna derecha, ecuación sin número) define la suma sobre "npix is the number of alerted pixels", y F23 ec. (1) sobre "Npix is the number of detected pixels": **confirmado**, la síntesis describe mal la operación. (b) `:93` ("Umbrales menor-sensibilidad summit ≤5 km, mayor-sensibilidad flanco") **sí está respaldada, pero por Coppola 2023 p. 3**, no por 2020; el encabezado de la sección (`:89`) mezcla los dos papers. El lector lo dejó como SOSPECHA y la sospecha resulta cierta. Que Coppola 2020 no lo diga en ninguna página no lo verifiqué (sólo vi p. 3, 4 y 13).
- **Qué cambia**: D18 (caja de 5 km contra círculo de 3 a 20 km) gana una cita del grupo de 2023; la frase "which reduce false alerts" es relevante para la sobre-publicación: con `inner_radius_km` de hasta 20 km aplicamos umbrales de cumbre donde el grupo declara usar los más altos. Pregunta 6, mitad ROI: puede acortarse a "¿caja o disco?".
- **Gravedad**: 3.
- **Propuesta para el catálogo (D18)**: "Coppola et al. 2023 (Front. Earth Sci. 11:1240107, p. 3, §2.1, columna derecha): en la cumbre (5 × 5 km) umbrales algo más bajos; a mayor distancia, algo más altos 'which reduce false alerts'. Sin valores."

### V-07 · origen A2, B-06, D-06, D-07, G3-3 (fondo del VRP; fusionados) · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**:
  1. C20, p. 3, columna derecha, párrafo bajo la ecuación del VRP (sin número): "L_MIR,bk is the MIR radiance of the background (average radiance of pixels surrounding the anomaly)".
  2. CA22, p. 7, §3.2, párrafo bajo la ec. (2): "calculated as the arithmetic mean of pixels surrounding the active one/s".
  3. FY, p. 8, §3.3, párrafo bajo la ec. (3): "namely the average radiance of the surrounding, non-alerted pixels".
  4. F23, p. 3, columna derecha, §2.2, ec. (1), impresa con paréntesis dentro de la suma, y su definición: "generally calculated from pixel(s) surrounding the anomaly". F23 p. 6, Tabla 1, fila Tot_Lmir_bk: "Sum of MIR background radiance from all alerted pixels".
  5. RR (Coppola et al. 2025, Remote Sens. 17, 1191), p. 9, §2.3.1, ec. (3), impresa **sin** paréntesis, y "the averaged radiance of the surrounding, non-alerted pixels".
  6. C13, p. 46 impresa (visor 8), Apéndice 2, columna derecha, bajo la ec. (A.1): "estimated from the arithmetic mean of all the pixels surrounding the active one or cluster of active pixels".
  7. CA24 (Campus et al. 2024, Bull. Volcanol. 86:25), p. 3 de 7, columna derecha, párrafo bajo la ec. (1): "At each alerted pixel, a background radiance value (L_pixbk ...) is also associated, this last computed from the arithmetic mean of the radiance of the pixels surrounding the alerted one(s)". Y la ec. (2): L_MIRbk = Σ L_pixbk. CA24 p. 4, Tabla 1, fila 6: "Radiance in MIR channel of the background, measured in the Vulcanello area".
  8. A24 (Aveni et al. 2024, RSE 315, 114388), p. 11, §4.3.5, último párrafo de la columna izquierda: "The BT_bg is computed iteratively by removing the Candidate Alerts from the scene and interpolating the gaps using a bi-cubic interpolation". R17 (Aveni et al. 2025, Remote Sens. 17, 2543), p. 6, §2.3.1: fondo por "bi-cubic interpolation of the surrounding, non-thermally anomalous pixels".
- **Veredicto**:
  - Siete textos MIR del grupo (2013 a 2025, MODIS, VIIRS 750 y VIIRS 375) coinciden: fondo = media de los píxeles que rodean al alertado o al cúmulo; tres agregan "no alertados". Ninguno habla de mediana ni de anillo regional. D25 queda **confirmada** con fuentes independientes de SP426.5 y Fernandina.
  - Contra el código: `pipeline/detection_context.py:1064` es `t_bg = float(np.median(bg_vals))` sobre la máscara de fondo; D25 ya lo registra (`docs/MIROVA_DIVERGENCES.md:2297-2305`). Correcto.
  - **Matiz importante que ningún lector cerró (hallazgo propio, ver P-02)**: CA24 p. 3 dice explícitamente que cada píxel alertado tiene **su propio** fondo (media de sus vecinos) y que el fondo total es la **suma** de esos fondos por píxel. Eso es coherente con F23 Tabla 1 ("Sum ... from all alerted pixels") y con la ec. (1) de F23 con paréntesis. Por lo tanto la ec. (3) de RR sin paréntesis es tipográfica, como sugirió B-06.
  - D-07 (Vulcanello): las dos citas son reales. La tensión es entre el texto de p. 3 y la nota de la tabla de p. 4. SOSPECHA sin resolver; la lectura más probable es nota de tabla imprecisa, porque la ec. (2) de p. 3 define la columna como suma de fondos por píxel.
  - G3-3 (A24, R17): citas confirmadas, pero son el detector TIR (TIRVolcH, banda I5) con interpolación bicúbica, no la ec. MIR. Sirven como práctica del grupo, no como cita literal de D25. El "3.er párrafo" del lector C para A24 es en rigor el último párrafo de la columna izquierda de p. 11.
  - La SOSPECHA de A2 de que "recortar a cero" no aparece: en las páginas vistas ninguna ecuación ni texto menciona recorte; no prueba ausencia en todo el paper.
- **Qué cambia**: D25 (fondo) y pregunta 4 del correo: la mitad "8 vecinos o anillo" queda contestada por el grupo en siete textos; queda abierta la mitad "¿se recorta a cero el exceso negativo?" y el tamaño exacto de la vecindad. Tarea T7 de S140: `pipeline/process_modis.py:1513-1514` guarda `diag_L_bg_w_m2_sr_um` como una radiancia de fondo única (Planck de `t_bg`); `Tot_Lmir_bk` del archivo es una suma por píxel alertado. Para comparar hay que dividir `Tot_Lmir_bk` por `Npix` (B-06 tiene razón). Además, como MIROVA asigna un fondo por píxel, un único `t_bg` para todo el cúmulo es una segunda divergencia dentro de D25, no sólo mediana contra media.
- **Gravedad**: 4.
- **Propuesta para el catálogo (D25)**: "Confirmaciones adicionales del grupo, páginas renderizadas S141: Coppola 2013 (JVGR 249, p. 46), Coppola 2020 (Front. Earth Sci. 7:362, p. 3), Campus 2022 (Sensors 22, 1713, p. 7), Aveni 2023 (Remote Sens. 15, 2528, p. 8), Coppola 2023 (Front. Earth Sci. 11:1240107, p. 3 ec. 1 y p. 6 Tabla 1) y Campus 2024 (Bull. Volcanol. 86:25, p. 3, ec. 2). Campus 2024 precisa que el fondo se calcula **por píxel alertado** (media de sus vecinos) y que el fondo total es la suma de esos fondos; la columna Tot_Lmir_bk del archivo v1 es esa suma. Lo nuestro usa un único t_bg (mediana del anillo) para todos los píxeles: para comparar con Tot_Lmir_bk hay que dividirlo por Npix."

### V-08 · origen G4-1, G4-2, G3-4, A10, B-02, D-09 y parte de D-03 (ángulo cenital; fusionados) · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**:
  1. M20 (Massimetti et al. 2020, Remote Sens. 12, 820), p. 15 de 32, §3.2, 3.er párrafo: "The MODIS dataset is filtered to exclude images with poor viewing geometry (Zenith > 40°)". p. 21, §4, 1.er párrafo: "filtered data with Zenith angle < 40°".
  2. A24, p. 14, Tabla 2, nota **: "we discarded all alerted scenes acquired with a zenith angle >50°". La misma nota agrega un corte de distancia: escenas con anomalías a más de 0,75, 2 y 7 km de las coordenadas centrales de Vulcano, Agung y La Palma (el lector C no lo menciona; ver V-10).
  3. A24, p. 20, §7.3, columna izquierda: "is common practice to discard scenes acquired with a zenith angle >50°", y "especially in steep mountainous regions, scenes >30° should be rejected"; antes: "thermal anomalies located inside steep crater rims, are likely masked at high zenith angles"; y "allows improved accuracy even for scenes acquired with a zenith angle up to ~55° (Campus et al., 2022)".
  4. R17, p. 7 de 21, §2.3.2, último párrafo: "scenes acquired with zenith angles > 50° were discarded".
  5. FY, p. 15, §4.2.1, último párrafo, y p. 16, 1.er párrafo: "the only increase in the satellite zenith corresponds to a decrease in the VRP" y "Although this is partially corrected during the resampling step (see [9]), residual artefacts can hardly be removed entirely". Tabla 2 (p. 11): alertas 28,20 / 35,24 / 48,34 % en todas las escenas y 44,45 / 45,66 / 57,56 % con cenit ≤ 40° (MERSI-II / MODIS / VIIRS). Números confirmados.
  6. RR, p. 13, leyenda de la Fig. 5a: "These unfavorable viewing conditions did not allow us to ascertain whether effusive activity was ongoing inside the caldera, nor to quantify the VRP" (encabezado del panel: Sat Zen 64,6°). p. 9, §2.3.1: "excluding data contaminated by clouds or acquired in unfavorable viewing conditions". p. 21, §5, punto i: "Purely automatic systems ... lack indications of sub-pixel cloud contamination, unfavorable viewing geometry, or false alerts(s) detection".
  7. KVG (Coppola et al. 2021, Sci. Rep. 11:13090), p. 12, Methods, "Satellite thermal data", 2.º párrafo: "visually analyzed to discard the data contaminated by clouds, ash plumes, or poor viewing conditions (i.e., high satellite zenith)".
  8. CA24, p. 4 de 7, "Dataset", columna derecha, 1.er párrafo: "the data were not corrected atmospherically or filtered by a maximum value of zenith"; la misma frase sigue: "with the same method adopted by Coppola et al. (2022), also using the same approach of the analysis in NRT".
- **Veredicto**:
  - Todas las citas están en la página y el párrafo indicados.
  - **El alcance es el punto crítico.** Todos los cortes por cenit (40°, 50°, 30° sugerido) y las exclusiones visuales son **de análisis** de un paper (M20 compara contra Sentinel-2; A24 y R17 son TIRVolcH; RR, KVG y C13 son series supervisadas). El único texto que describe un dataset MIROVA procesado "con el mismo enfoque del análisis en NRT" (CA24) dice lo contrario: **sin filtro de cenit**. RR p. 21 describe al sistema automático como uno que no marca la geometría desfavorable. Conclusión: no hay evidencia de un corte cenital en el producto NRT publicado; hay evidencia de que el grupo **no confía** en la magnitud de pasadas oblicuas y las saca a mano cuando publica ciencia. G4-1 marcaba esto como SOSPECHA; los textos la inclinan a "el NRT no filtra".
  - Repo: comprobé que el pipeline no descarta por cenit. `grep` de comparaciones con `zenith|satzen|sz` en `pipeline/`, `scripts/run_pipeline.py` y los perfiles sólo encuentra `MAX_SENSOR_ZENITH_DEG = 70.0` (`pipeline/scan_geometry.py:81`) usado como `np.clip` del factor de área (`:99`, `:237`), no como descarte; ninguna clave de cenit en `pipeline/profiles/mirova_equivalent.yaml` ni en `pipeline/store.py`. `docs/AUDIT_S128.md:68` sigue vigente. Como no hay divergencia con el NRT, **no corresponde una D nueva por "filtro cenital"**; sí corresponde un control de comparación.
  - G3-4: la Tabla 1 de A24 (p. 3) no la miré en imagen; la frase "~55°" de §7.3 sí, y cita a Campus 2022. La inferencia cuantitativa ("el área explica sólo parte de 2,7×") es del lector: SOSPECHA.
  - G4-2 y FY p. 16 agregan un mecanismo que un remuestreo no corrige: oclusión por el borde del cráter ("masked by the topography", FY p. 16; "masked at high zenith angles", A24 p. 20). Esto sí matiza `docs/s130/GRADIENTE_CENITAL.md` y D17: la caída con el ángulo no es sólo área.
  - A10 contra S130: FY muestra VRP MIROVA (su algoritmo sobre Etna) que **sí** cae con el cenit (Fig. 9, p. 16), mientras S130 midió "MIROVA plano" en Chile. No es contradicción probada (Etna, alto flujo; Chile, flujo bajo), pero debilita la frase de D17 "su magnitud no depende del ángulo" (`docs/MIROVA_DIVERGENCES.md:1930-1931`): el propio grupo dice que el remuestreo lo corrige "partially".
- **Qué cambia**: D17 (explicación del gradiente cenital), control de paridad del gap de magnitud (~0,7) y pregunta nueva al correo. No cambia la detección.
- **Gravedad**: 4 (condiciona cómo leer el 0,7 y el diseño del A/B de D17), no por una divergencia de producción.
- **Propuesta para el catálogo (D17, nota S141)**: "El grupo reconoce que el remuestreo corrige 'partially' el efecto del cenit y que el VRP cae con el ángulo (Aveni et al. 2023, Remote Sens. 15, 2528, p. 15-16, §4.2.1), por atenuación atmosférica y por oclusión en bordes de cráter empinados (Aveni et al. 2024, RSE 315, p. 20, §7.3). En sus análisis descarta pasadas con cenit > 40° (Massimetti et al. 2020, p. 15) o > 50° (Aveni 2024 Tabla 2; Aveni 2025 Remote Sens. 17, 2543, p. 7; Coppola 2013 p. 46, a mano), pero el dataset VIIRS 375 m procesado 'with the same approach of the analysis in NRT' no filtra por cenit (Campus et al. 2024, Bull. Volcanol. 86:25, p. 4). No es divergencia de producción. Toda comparación de magnitud contra MIROVA debe reportarse también restringida a cenit ≤ 40° antes de atribuir el gap a un mecanismo; la frase 'su magnitud no depende del ángulo' queda matizada."

### V-09 · origen D-01 · CONFIRMADO CON MATIZ
- **Localizador**: L26 (Laiolo et al. 2026, Bull. Volcanol. 88:11), p. 4 de 21, "Methods and dataset", "Satellite thermal data", columna derecha, 2.º párrafo.
- **Cita vista**: "combined and filtered in terms of distance and/or intensity of the thermal anomaly to minimize the false alerts and the double counting (coming from different detectors acquiring at the same time)"; sigue "thus resulting in 9712 data points (ca. 12%; Online Resource 1)". El párrafo anterior da 82.329 imágenes.
- **Veredicto**: la cita es exacta. Matices: (a) el 12 % no es "12 % de las imágenes que quedan tras filtrar falsas alertas": las 82.329 imágenes incluyen todas las pasadas (con y sin anomalía), así que el 12 % mezcla detecciones con cobertura; no mide cuánto recorta el filtro. (b) Es la serie de un estudio (Stromboli, 25 años), y el mismo párrafo dice que no se aplica filtro automático de nube y que se evita la inspección visual. No hay texto que traslade el filtro al NRT de mirovaweb: SOSPECHA abierta, igual que dijo el lector.
- **Qué cambia**: pregunta 8 del correo (¿archivo filtrado por distancia o intensidad?). Da una respuesta para series de estudio, no para el NRT; y la parte "double counting" es relevante para contar noches frente a pasadas cuando se compara contra series publicadas en papers (A90, A93).
- **Gravedad**: 3 (bajo del 4 del lector: no toca el producto con que comparamos).
- **Propuesta (correo, pregunta 8)**: citar Laiolo et al. 2026 p. 4 y preguntar si el filtro "distance and/or intensity" y el de doble conteo se aplican también a las series NRT de la web y al CSV `latest`.

### V-10 · origen D-02 (más un hallazgo propio en A24 Tabla 2) · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**:
  1. CA24, p. 5 de 7, columna derecha, 1.er párrafo: "354 had at least one alerted pixel located within a distance of 1 km radius from the La Fossa cone (as per coordinates provided by the Global Volcanism Program". Sobre 2.056 imágenes nocturnas; frecuencia 17,22 %.
  2. A24, p. 14, Tabla 2, nota **: además del corte cenital, "we discarded scenes with thermal anomalies originating more than 0.75, 2, and 7 km away from the central coordinates of Vulcano, Agung, and La Palma, respectively".
- **Veredicto**: las citas están. Matiz: son cortes de distancia **de análisis por volcán** (1 km en un campo fumarólico chico; 0,75 / 2 / 7 km en TIRVolcH), elegidos según la actividad de cada caso, no una compuerta del NRT. Lo que sí prueban es que el grupo, cuando cuenta alertas "de un volcán", las cuenta con un radio al punto GVP ajustado al tamaño del objeto, en general mucho menor que nuestros `inner_radius_km`. Errata del paper: CA24 define la frecuencia como "N° alerted pixel/N° of overpasses", pero 354/2.056 = 17,22 % son imágenes, no píxeles.
- **Qué cambia**: frente de sobre-publicación VIIRS375 y D18. No autoriza un corte nuevo (MISSION: per-volcán excluido); sí autoriza, en las comparaciones de paridad contra conteos de papers, declarar el radio con que cuenta cada fuente.
- **Gravedad**: 3 (bajo del 4 del lector por el alcance de análisis).
- **Propuesta para el catálogo (D18, nota)**: "En sus datasets de estudio el grupo cuenta alertas con radios al punto GVP ajustados al objeto: 1 km en La Fossa (Campus et al. 2024, p. 5), 0,75 / 2 / 7 km en Vulcano, Agung y La Palma (Aveni et al. 2024, RSE 315, Tabla 2, p. 14). No describen el NRT; sirven para no comparar conteos de papers contra nuestro inner_radius."

> **Refuerzo de V-08 encontrado después** (CA22, p. 8, §3.4, **3.er** párrafo, dos últimas oraciones; el lector A lo ubicó en el 2.º): "we have left the datasets 'as they are', that is without applying image inspections or filters that discard cloudy scenes or scenes acquired in unfavorable geometric conditions (e.g., high satellite zeniths)" y "we test the potential efficiency of the algorithm in NRT applications where such supervision is not applied". Es la declaración más directa de que el NRT no filtra por cenit.

### V-11 · origen D-03, B-03, B-02 (parte supervisión), A9 (parte supervisión) (supervisión humana; fusionados) · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**:
  1. F23, p. 4, §2.5 "Supervision of the dataset", columna derecha: "The current version of the MIROVA database (v.1) consists exclusively of night-time data" y "the entire dataset has been supervised to remove obvious 'non-volcanic' thermal features". Mismo párrafo: "the VRP data provided by MIROVA are provided 'as-are'", por la dificultad de corregir "in NRT without compromising the latency".
  2. KVG, p. 12 (ver V-08, cita 7): series visualmente depuradas, "the supervised dataset consists of 2139 images for Klyuchevskoy".
  3. C13, p. 46, Apéndice 2, columna derecha: "A post processing and a visual inspection of all the images allows us to discard all the cases in which the VRP estimates are clearly affected by cloud attenuation and/or by extreme viewing geometry (with a satellite zenith >50°)". **El lector D recortó la cita antes de "(with a satellite zenith >50°)"**, que es justo lo relevante para V-08.
  4. VAN (Coppola et al. 2016, JVGR 322), p. 10 impresa (visor 5), §4.6, columna izquierda al pie y derecha arriba: "the authors underline that single data points provided by MIROVA cannot be trusted without a visual inspection of the image". **Matiz de atribución**: la frase empieza "In particular the authors underline" y se refiere a Coppola et al. 2015a, no es una afirmación nueva de 2016. Y "we have not checked manually the large number of images ... (more than 50,000 images)" sigue "with the exception of few cases related to the effusive activity of Lopevi ... and Ambrym ... as well as to the few hotspots detected at Gaua": el lector D omitió esa excepción.
  5. L26, p. 4 (ver V-09): "we avoid the visual inspection of the acquired dataset to discard cloud-contaminated images".
  6. C20, p. 13, columna izquierda, "Tinakula": "it was necessary the post-event supervision ... of the image of October 19, in order to exclude that it was a false alert".
  7. RR, p. 9 y p. 21 (ver V-08, cita 6).
- **Veredicto**: todas las citas están. B-03 tiene razón: F23 declara supervisada la **v.1** (MODIS, noche, 111 volcanes, 2000 a 2019); el texto no menciona v2.5 ni VIIRS. Sobre el NRT, los textos coinciden en una sola dirección: supervisión en archivos y casos de estudio, no en el canal automático (F23 "as-are"; CA22 p. 8 "NRT applications where such supervision is not applied"). Esto **confirma** la regla `feedback_s135_techo_artificial_supervision.md` y matiza la etiqueta "v2.5" de la nota de memoria. No verifiqué el texto de las notas de memoria del agente (no están en el repo): SOSPECHA sobre qué dicen exactamente sus líneas 21 a 37.
- **Qué cambia**: la regla S139 "conteos del OSF no valen para el NRT" gana base textual (v.1 supervisada); cualquier conteo de alertas sacado de un paper debe revisar primero si ese paper supervisó (2013, 2021, 2025 sí; 2016 casi no; 2022 y 2026 no).
- **Gravedad**: 3.
- **Propuesta (memoria o `docs/MISSION.md`, no catálogo)**: "Coppola et al. 2023 (Front. Earth Sci. 11:1240107, p. 4, §2.5) declara supervisada a mano la base MIROVA v.1 (MODIS nocturno 2000-2019), no una v2.5; la web se publica 'as-are'. Campus et al. 2022 (Sensors 22, 1713, p. 8, §3.4) describe el NRT como sin supervisión."

### V-12 · origen A9 (tasa de falsas alertas), D-04 · CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**:
  1. C20, p. 13, columna izquierda, "Tinakula", últimas oraciones: "generally comprised between 0 and 3% (number of false alerts/number of MODIS overpasses)" citando "Coppola et al., 2016b"; y "These false alerts depend on the regional and local environmental conditions as climate, elevation, topography and land cover type".
  2. VAN, p. 10, §4.6, columna derecha: "(typically less than 2% of the total MODIS overpasses), may be eventually triggered by the MIROVA algorithm in absence of any sign of volcanic activity (Coppola et al., 2015a)". Gaua: alertas "persistently radiant power < 5 MW" en la estación cálida. Aoba, §4.4, columna izquierda: "could be due to the contrast between the lake temperature and its surroundings".
- **Veredicto**: citas exactas. No verifiqué la p. 18 de VAN que el lector D cita para la conclusión (rendericé la p. 13 del visor pero no la miré): esa repetición queda sin comprobar. Matiz de unidades (A90, A93): las tasas están por **pasadas MODIS totales**, no por pasadas con detección ni por noches; y son tropicales o de latitud media. Nuestro "~63 %" del frente de sobre-publicación está en otra unidad (A9 lo dice bien). Otro matiz: C20 atribuye el 0 a 3 % a "Coppola et al., 2016b" y VAN el "< 2 %" a "Coppola et al., 2015a": podrían ser la misma fuente con distinta etiqueta; no lo resolví.
- **Qué cambia**: da una vara del propio grupo para la tasa de falsas alertas MODIS aceptada (≤ 2 a 3 % de las pasadas) y el mecanismo (altitud, topografía, lagos tibios), coherente con A69 y con la categoría "lago" de A54. No se transfiere tal cual a VIIRS 375 m.
- **Gravedad**: 3.
- **Propuesta**: en el doc del auto-audit de sobre-publicación, expresar además la tasa en "falsas / pasadas totales" para poder compararla con el 0 a 3 % declarado (Coppola 2020 p. 13; Coppola 2016 p. 10).

### V-13 · origen D-05, G3-1, G3-2, B-04 (grilla de remuestreo y tamaño de celda; fusionados) · CONFIRMADO; la tensión 50 contra 51 km queda resuelta
- **Localizadores y citas vistas**:
  1. CA24, p. 3, columna derecha, 2.º párrafo (VIIRS I4/I5): "after an initial resampling of the original granule in a regular 50×50 km UTM grid, first detects the thermally anomalous pixels".
  2. VAN, p. 8 impresa (visor 3), §3, columna derecha: "(ii) cropping and resampling into 50 × 50 km box centered on the volcano summit (iii) definition of Region of Interest (ROIs)".
  3. SA17 (Laiolo et al. 2017, JVGR 340), p. 173 impresa (visor 4), columna izquierda, 2.º párrafo: "produce 50 × 50 km NTI maps centered on the volcano summit".
  4. C20, p. 3, columna derecha: "resampled in regular grids of 50 × 50 km (in UTM coordinates)".
  5. CA22, p. 7, §3.2, 2.º párrafo: "Resampling is performed in a UTM 51 × 51 km grid ... by keeping the nominal resolution of 750 m. This results in matrices of 67 × 67 pixels".
  6. A24, p. 5, §3.2, columna derecha: "The original granules, as per MIROVA workflow, are resampled to a regular 134 × 134 UTM grid centred on the volcano summit according to the coordinates provided by the Global Volcanism Program". A24 p. 6, "Ancillary data": máscara tierra/agua "binary matrix 134 × 134 pixels"; y "Coordinates of Interest: the revised location of the volcano's summit (or active vent) to compensate for any offset in the GVP list".
  7. F23, p. 3, columna izquierda al pie: "resampled to regular 51 × 51 UTM grids" (sin unidad). RR p. 9: "51 × 51 km UTM grid". FY p. 8: "UTM 51 × 51 km grid".
- **Veredicto**:
  - Todas las citas están. Hallazgo propio que cierra la duda del lector D ("50 frente a 51, no lo resuelvo"): 67 × 0,75 km = 50,25 km y 134 × 0,375 km = 50,25 km. Es **la misma grilla**: 51 celdas de 1 km (MODIS), 67 de 750 m o 134 de 375 m, que miden entre 50 y 51 km según se cuente. "50 × 50" y "51 × 51" son redacciones de lo mismo; no hay divergencia.
  - B-04 decía que el tamaño de celda VIIRS estaba "SIN LOCALIZAR" y sugería Campus 2022: **CA22 p. 7 lo da para M-band** (se conserva la resolución nominal de 750 m, 67 × 67) y **A24 p. 5 lo da para I-band** (134 × 134 celdas, unos 2.500 km², o sea celdas de 375 m). El matiz de B-04 a H12 de S139 es correcto respecto de Fernandina, pero la respuesta sí estaba en el grupo.
  - G3-1: el grupo lo dice "as per MIROVA workflow"; la Fig. 2 de A24 rotula la entrada "MIROVA-pre-processed". Confirmado.
  - G3-2: confirmado en imagen, pero es la configuración de TIRVolcH, no del detector MIR.
  - D-05 sobre VIIRS 375 m: confirmado; CA24 es una segunda fuente I-band además de Fernandina.
- **Qué cambia**: D17 y D28: la grilla MIROVA de los tres sensores queda descrita por el grupo con celda nominal (1 km, 750 m, 375 m) sobre unos 50 km centrados en GVP. Pregunta 6 del correo: la parte de remuestreo VIIRS queda contestada. El orden de VAN (remuestreo, luego ROI, luego detección) coincide con D17.
- **Gravedad**: 3.
- **Propuesta para el catálogo (D17)**: "Celda de la grilla MIROVA por sensor: MODIS 51 × 51 celdas de 1 km (Coppola 2023 p. 3), VIIRS M-band 67 × 67 de 750 m (Campus 2022 p. 7), VIIRS I-band 134 × 134 de 375 m (Aveni 2024 RSE p. 5, 'as per MIROVA workflow'). Las tres cubren unos 50 km y varios papers lo redondean a 50 × 50 km (Coppola 2016 JVGR 322 p. 8; Laiolo 2017 p. 173; Coppola 2020 p. 3; Campus 2024 p. 3). Centro: cumbre GVP."

### V-14 · origen A4 · CONFIRMADO CON MATIZ
- **Localizador**: CA22, p. 16, §5, párrafo "The number of alerts", 3.ª y 4.ª oración; Tabla 4, p. 17.
- **Cita vista**: "It should be emphasized that the increase of VIIRS detections is inversely proportional to the average VRP (Table 4)". Tabla 4, fila "Whole": 6293 (36,0 %) VIIRS contra 3883 (28,9 %) MODIS; Nevados de Chillán noche 71,4 % contra 57,5 %; Sabancaya noche 69,5 % contra 55,0 %.
- **Veredicto**: números y cita exactos. Matices que el lector no dijo: (a) VIIRS tiene 30 % más pasadas (17.487 contra 13.416), aunque la frecuencia por pasada también sube (36,0 contra 28,9 %). (b) El mismo párrafo dice que muchas pasadas VIIRS superan 55° de cenit, y aun así se cuentan. (c) El 62 % es de alertas totales día más noche. (d) Es M-band 750 m con S-NPP y NOAA-20.
- **Qué cambia**: frente de sobre-publicación. En volcanes de bajo flujo el propio MIROVA publica bastante más con VIIRS que con MODIS; comparar contra una referencia de otro sensor mide otra cosa. Nada sobre 375 m.
- **Gravedad**: 3.
- **Propuesta**: nota en el doc de paridad de cobertura con esta cita y la fila de Nevados de Chillán.

### V-15 · origen B-08, A8 (banda TIR 31 contra 32; afirma que una nota del catálogo está mal) · CONFIRMADO (B-08); A8 CONFIRMADO CON MATIZ
- **Localizadores y citas vistas**: F23, p. 3, columna izquierda, penúltimas líneas: "the Thermal InfraRed (TIR[guion]12.02 µm) data matrices are first extracted" (el original separa con un guion largo; aquí va "[guion]"). C20, p. 3, columna derecha: "Thermal Infrared [TIR] at 12.02 µm". C13, p. 46, Apéndice 2: "original MODIS band 21/22 and 32".
- **Repo**: `docs/MIROVA_DIVERGENCES.md:2193-2195`, nota S140: "La divergencia queda sólo contra SP426.5 (banda 32, 2016)".
- **Veredicto**: B-08 tiene razón: el grupo escribe 12,02 µm en 2020 y en 2023; "sólo contra SP426.5" es demasiado fuerte. A8 afirma que el cambio a la 31 aparece entre 2020 y 2022 por las tablas de Campus 2022 y Aveni 2023; **esas tablas no las miré en imagen** (CA22 p. 6, FY p. 6): SOSPECHA. Pero Coppola 2023 dice 12,02 µm, lo que **contradice la cronología de A8**: no hay un cambio limpio en el tiempo sino descripciones inconsistentes del grupo. La tabla de Fernandina p. 6 con B31 no la miré esta sesión (S140 la verificó).
- **Qué cambia**: D20. Sin cambio de código (efecto despreciable, S128).
- **Gravedad**: 2.
- **Propuesta para el catálogo (D20, reemplazo de la nota S140)**: "El grupo describe la banda TIR de MODIS de forma inconsistente: 12,02 µm (banda 32) en Coppola 2020 (p. 3) y Coppola 2023 (Front. Earth Sci. 11:1240107, p. 3), banda 31 en Fernandina 2025 (p. 6). No se sabe cuál usa el NRT; efecto despreciable (S128)."

### V-16 · origen G1-1, G1-2 (dos localizadores del repo corridos) · CONFIRMADO
- **Vistos**: A24, p. 11, columna derecha, ec. (5) con "A is the pixel surface area, namely 140,625 m² for VIIRS I5 pixels". A25 (Aveni et al. 2025, GRL 52), p. 4: ecuaciones (8) y (9); p. 5, leyenda de la Figura 2: "for λ = 11.45, optimal k_TIR has a value of 60.17 µm · sr".
- **Repo**: `docs/DRIFTS_S17.md:83` dice "Aveni 2024 RSE Eq.5 p.12": está en la p. 11. `pipeline/vrptir.py:10` dice "60.17 μm·sr (verbatim p.4, Fig.2b)": la Figura 2 y el 60,17 están en la p. 5. Los coeficientes de `pipeline/vrptir.py:49-51` coinciden con la ec. (8) en imagen.
- **Gravedad**: 1.
- **Propuesta**: corregir los dos localizadores, sin cambio funcional.

### V-17 · origen B-07 · CONFIRMADO
- **Localizador**: F23, p. 4, §2.3, columna izquierda, 3.er párrafo.
- **Cita vista**: "In the case of MODIS with a resolution of 1 km, accurate values of VRP can be detected above ~1 MW (Coppola et al., 2016a)".
- **Veredicto**: límite de exactitud MODIS, no compuerta de publicación. VAN p. 8 ("high efficiency in detecting small hotspot (~1 MW)") y C20 p. 3 ("from less than ~1 MW") van en la misma línea. No reabre el piso VRP retirado en S130.
- **Gravedad**: 2 (bajo del 3 del lector: no cambia ninguna decisión).

### V-18 · origen A11, B-12 (atribución de α y coeficientes del repo) · CONFIRMADO CON MATIZ
- **Vistos**: FY p. 8, §3.3 ec. (2) "VRP = ΔL_MIR × σε/(αε_MIR) × A_pix" y §3.4 "Determination of α Coefficient for MERSI-II", que propone el método "for other sensors operating in the MIR region". RR p. 9, ec. (2) "α = −8.6344 × 10⁻¹⁰ × λ + 6.3796 × 10⁻⁹", introducida "According to [58]". Repo: `pipeline/process_viirs_mod.py:66` `WOOSTER_COEFF = 19.7`; `pipeline/process_viirs.py:77` `WOOSTER_COEFF = 18.0`.
- **Veredicto**: la derivación de α está en FY 2023; que la ref. [58] de RR sea ese paper lo tomaron A y B de la lista de referencias en capa de texto, no lo miré en imagen. La Figura 3 de FY (p. 9) no la miré: los valores 2,88e−9 y 2,96e−9 quedan como del lector. Líneas del repo correctas.
- **Gravedad**: 2.


### V-19 · origen D-01 (afirmación sobre el repo) · REFUTADO en la parte "el repo no lo cita"
- **Lo que afirma el lector D**: el repo cita el párrafo de Laiolo 2026 p. 4 "sólo por la frase de la nube", y `grep -rn "filtered in terms of distance"`, `"double counting"` y `"9712"` sobre `docs/` dan 0.
- **Lo que vi**: `docs/MIROVA_DIVERGENCES.md:1644-1649` transcribe el párrafo completo, incluidas "filtered in terms of distance and/or intensity" y "double counting ... 9712 data points (ca. 12%)"; y `:1652-1655` lo interpreta ("MIROVA SÍ filtra, por distancia y por intensidad, y se queda con el 12 %", y lo usa para validar la convención de un par por noche). Esa sección está en el bloque de verificación S128 de D14, fuera de las líneas 1552 y `docs/MISSION.md:58-59` que el lector revisó. El grep del lector no pudo dar cero sobre ese texto: es un falso negativo de instrumento (A89).
- **La cita del paper sigue confirmada** (V-09). Lo refutado es la novedad: el hallazgo ya estaba en el catálogo desde S128.
- **Pero el catálogo tiene su propio problema (hallazgo propio, ver P-01)**.
- **Gravedad**: 2 (como refutación); ver P-01 para lo que sí importa.

---

## (a) Hallazgos propios

### P-01 · `docs/MIROVA_DIVERGENCES.md:1652-1654` generaliza a MIROVA un filtro de una serie de estudio y lee mal el 12 % · gravedad 3
- **Qué dice el catálogo**: "1. MIROVA SÍ filtra, por distancia y por intensidad, y se queda con el 12 %. De 82.329 imágenes salen 9.712 puntos."
- **Qué dice el paper** (L26, p. 4, columna derecha, 2.º párrafo, visto en imagen): el filtro se aplica a "The VRP time series (Fig. 2) coming from the different sensors/detectors" de ese estudio de Stromboli, al combinar cuatro plataformas. No dice que el producto NRT de mirovaweb filtre así. Y 82.329 son **todas** las imágenes adquiridas (con y sin anomalía, p. 4, párrafo previo), así que 12 % no es "lo que queda después de filtrar falsas alertas": mezcla la frecuencia de detección con el filtro. Además, otro texto del grupo que describe su dataset "with the same approach of the analysis in NRT" (CA24 p. 4) no menciona filtro por distancia, y CA22 p. 8 describe el NRT como "as they are".
- **Por qué importa**: una frase del catálogo dice que MIROVA filtra por distancia e intensidad. Una sesión futura puede usarla para justificar una cerca por distancia o por intensidad como "clon literal", que MISSION rechaza. Es A93 en el catálogo: un conteo que nombra otro conjunto.
- **Propuesta**: "1. En la serie de estudio de Stromboli (Laiolo et al. 2026, p. 4) el grupo combina sensores y filtra por distancia y/o intensidad y por doble conteo; quedan 9.712 puntos sobre 82.329 imágenes adquiridas (12 %, que incluye las pasadas sin anomalía). No hay texto que diga que el NRT publicado aplique ese filtro (pregunta 8 del correo)."

### P-02 · Campus 2024 define el fondo por píxel alertado y el fondo total como suma (ya integrado en V-07) · gravedad 4
- CA24, p. 3, columna derecha, bajo la ec. (1) y ec. (2): cada píxel alertado tiene su L_pixbk (media de sus vecinos) y L_MIRbk = Σ L_pixbk. Ningún lector lo citó; B-06 lo dedujo de la Tabla 1 de F23. Consecuencia doble: explica `Tot_Lmir_bk` (suma, no media) y muestra que usar un único `t_bg` para todos los píxeles del cúmulo es una divergencia adicional dentro de D25.

### P-03 · Coppola 2013 da el umbral cenital > 50° del descarte manual; el lector D lo cortó · gravedad 2
- C13, p. 46, Apéndice 2, columna derecha: "clearly affected by cloud attenuation and/or by extreme viewing geometry (with a satellite zenith >50°)". Es la cuarta fuente del corte de 50°, aquí para una serie MODIS supervisada (ver V-08).

### P-04 · La grilla "50" y "51" es la misma (integrado en V-13) · gravedad 2
- 67 × 0,75 = 134 × 0,375 = 50,25 km. Resuelve la tensión que D-05 dejó abierta.

### P-05 · Errata de hora en Fernandina 2025 · gravedad 1
- RR p. 13: el encabezado del panel (b) dice "03 March 2024 07:30 UTC" y la leyenda "at 07:50 UTC"; el encabezado de (c) dice 15:41 y la leyenda 15:20, y el texto siguiente 15:36. Sin efecto; útil si alguien cruza esas pasadas con datos.

### P-06 · Campus 2024 define mal su frecuencia · gravedad 1
- CA24 p. 5: "(N° alerted pixel/N° of overpasses) of 17.22%", pero 354/2.056 = 17,22 % son imágenes con alerta, no píxeles.

### P-07 · Aveni 2024 (TIRVolcH) también recorta por distancia en su evaluación (integrado en V-10) · gravedad 2
- A24 p. 14, nota ** de la Tabla 2: 0,75 / 2 / 7 km para Vulcano, Agung y La Palma.

---

## (b) Errores de premisa de los lectores

1. **Lector C, M20**: señaló bien que `remotesensing-12-00820-v4.pdf` no es una validación VIIRS sino Sentinel-2 contra MIROVA MODIS. Confirmado en p. 15 (§3.2, comparación S2Pix contra VRP MODIS).
2. **Lector B, rs11131528.pdf**: señaló bien que es MOUNTS, no un paper del algoritmo MIROVA (no lo miré en imagen; su p. 3 y Tabla 1 quedan como del lector).
3. **Lector D, Vanuatu 2016**: atribuye a 2016 la frase "single data points provided by MIROVA cannot be trusted without a visual inspection"; en la página la frase es un reporte de Coppola et al. 2015a ("the authors underline"). Y omite la excepción ("with the exception of few cases related to ... Lopevi ... Ambrym ... Gaua").
4. **Lector D, D-01**: afirmó ausencia en el repo con un grep que no podía dar cero (V-19). A89.
5. **Lector A, A8**: construyó una cronología (32 en 2020, 31 desde 2022) que Coppola 2023 contradice (V-15).
6. **Lector B, B-04**: dio por "SIN LOCALIZAR" el tamaño de celda VIIRS cuando estaba en Campus 2022 p. 7 y Aveni 2024 p. 5, papers del mismo lote de lectura (A y C los tenían). No es error de lectura sino de cobertura entre lectores.
7. **Localizadores corridos menores**: A9 para Campus 2022 dice §3.4 "2.º párrafo": es el 3.º. G3-3 para A24 dice "3.er párrafo": es el último párrafo de la columna izquierda de p. 11. Leyenda de RR Fig. 5a dice 64° y el encabezado 64,6° (B-02 usa el encabezado; ambos están).

---

## (c) VERIFICADO LIMPIO (lo que busqué en las páginas renderizadas y no estaba, o no contradice al repo)

- **Ningún texto visto describe una compuerta cenital automática en el NRT de MIROVA.** Al contrario: CA22 p. 8 y CA24 p. 4 dicen que no se filtra. El pipeline tampoco filtra (V-08). No hay divergencia de producción por cenit.
- **Ningún texto visto usa mediana ni anillo regional para el fondo del VRP MIR** (siete textos, V-07).
- **Ningún texto visto menciona recorte a cero del exceso negativo** en las ecuaciones del VRP (C20 p. 3, CA22 p. 7, FY p. 8, F23 p. 3, RR p. 9, CA24 p. 3-4, C13 p. 46, VAN p. 8). Pregunta 4, segunda mitad: sigue abierta.
- **Ningún texto visto da K1, C1, C2, N·σ ni la conectiva de los Tests 2 y 3**; todos remiten a Coppola 2016a (coincide con los cuatro lectores).
- **Ningún texto visto dice que MIROVA promedie píxeles duplicados por bow tie**: los tres dicen identificar y eliminar o aislar.
- **Repo**: `pipeline/detection_context.py:1064` (mediana) y `pipeline/process_modis.py:1513-1514` (`diag_L_bg_w_m2_sr_um` como radiancia única) son como dicen los lectores. `Liu` no aparece en `docs/MIROVA_DIVERGENCES.md`, `docs/AUDIT_S138.md` ni `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` (A1 correcto). `Vulcanello` no aparece en `docs/` (D-07 correcto; sí en la síntesis, l. 120, por otro motivo).

**No verificado por mí** (quedan con el nivel de confianza del lector): A13 a A16 salvo lo visto en FY p. 8 y CA22 p. 17 (A15 cita confirmada), B-09 (la Tabla 1 de F23 p. 6 sí la vi: Lat/Lon "hottest alerted pixel", max Dist "alerted pixel furthest from the volcano summit", sin columna "class": **confirmado**), B-10 (figuras 4C y 5C de F23), B-11 ("as-are" confirmado en F23 p. 4; el filtro de mínimos locales también está en §2.4), B-13 a B-15, D-08, D-10 a D-14 (D-10: KVG p. 12 "errors in geolocation are less than 0.5 km for nadir acquisition" **confirmado**), G2-1 (M20 p. 15 "standard error of 30%" y "T > 500 K" **confirmado**), G2-2 (A24 p. 11, test 11, 0,5 / 0,75 / 1 K **confirmado**), G2-3 (A24 p. 20: la frase empieza al pie de la columna izquierda; el resto no lo vi).

---

## (d) Tabla resumen

| ID | Origen | Tema | Veredicto | Gravedad | Divergencia o pregunta |
|---|---|---|---|---|---|
| V-01 | A5 | distancia web = píxel más lejano | CONFIRMADO CON MATIZ | 3 | pregunta 11 |
| V-02 | A6 | web separa a 5 km fijos (color) | CONFIRMADO CON MATIZ | 3 | D18, D13 |
| V-03 | A3 | detector VIIRS "el mismo" que MODIS | CONFIRMADO CON MATIZ | 3 | umbrales VIIRS, pregunta 1 |
| V-04 | A12 | síntesis divide k de Campus 2022 | CONFIRMADO | 2 | síntesis |
| V-05 | A1, B-01, D-06 | bow tie: se eliminan duplicados, antes de remuestrear | CONFIRMADO CON MATIZ | 4 | D28, D17, pregunta 6 |
| V-06 | B-05, A7 | ROI1 5 × 5 km; síntesis mal atribuida | CONFIRMADO / CON MATIZ | 3 | D18, síntesis |
| V-07 | A2, B-06, D-06, D-07, G3-3 | fondo = media de vecinos, por píxel, suma | CONFIRMADO CON MATIZ | 4 | D25, pregunta 4, T7 |
| V-08 | G4-1, G4-2, G3-4, A10, B-02, D-09 | cenit: filtros de análisis, NRT sin filtro, oclusión | CONFIRMADO CON MATIZ | 4 | D17, gap 0,7 |
| V-09 | D-01 | Stromboli filtrado por distancia/intensidad | CONFIRMADO CON MATIZ | 3 | pregunta 8 |
| V-10 | D-02 (+P-07) | radios de conteo de 0,75 a 7 km en estudios | CONFIRMADO CON MATIZ | 3 | D18, sobre-publicación |
| V-11 | D-03, B-03, B-02, A9 | supervisión: v.1 y casos de estudio, no NRT | CONFIRMADO CON MATIZ | 3 | memoria, OSF |
| V-12 | A9, D-04 | falsas alertas 0 a 3 % de pasadas MODIS | CONFIRMADO CON MATIZ | 3 | sobre-publicación |
| V-13 | D-05, G3-1, G3-2, B-04 | grilla ~50 km, celda nominal por sensor | CONFIRMADO | 3 | D17, D28, pregunta 6 |
| V-14 | A4 | VIIRS 750 publica 62 % más que MODIS | CONFIRMADO CON MATIZ | 3 | paridad de cobertura |
| V-15 | B-08, A8 | TIR 12,02 µm aún en 2023 | CONFIRMADO / CON MATIZ | 2 | D20 |
| V-16 | G1-1, G1-2 | dos páginas mal citadas en el repo | CONFIRMADO | 1 | DRIFTS_S17, vrptir.py |
| V-17 | B-07 | "accurate above ~1 MW" | CONFIRMADO | 2 | piso VRP (S130) |
| V-18 | A11, B-12 | α de Aveni 2023; coeficientes | CONFIRMADO CON MATIZ | 2 | H2 S139 |
| V-19 | D-01 (repo) | "el repo no cita el filtro" | REFUTADO | 2 | D14 S128 |
| P-01 | propio | catálogo generaliza el filtro de Stromboli a MIROVA | hallazgo | 3 | D14 l. 1652 |
| P-02 | propio | fondo por píxel y suma (Campus 2024) | hallazgo | 4 | D25 |
| P-03 a P-07 | propios | cenit 50° en C13, grilla 50=51, erratas, radios TIRVolcH | hallazgo | 1 a 2 | V-08, V-13, V-10 |

**Conteo por veredicto (V-01 a V-19)**: CONFIRMADO 4 (V-04, V-13, V-16, V-17) · CONFIRMADO CON MATIZ 12 · mixtos CONFIRMADO y CON MATIZ 2 (V-06, V-15) · REFUTADO 1 (V-19) · NO VERIFICABLE 0. Hallazgos propios: 7.
