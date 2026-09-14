# S141, lectura de papers MIROVA, segunda pasada: LECTOR A

## Encabezado

**Qué leí.** Tres PDF de `documentacion/`, los tres del grupo MIROVA (autoría y afiliación confirmadas en la p. 1 renderizada):

| PDF | paper | autores y afiliación (p. 1, imagen) | ¿grupo MIROVA? |
|---|---|---|---|
| `Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf` | Coppola et al. 2020, Front. Earth Sci. 7:362, doi 10.3389/feart.2019.00362 | Coppola, Laiolo, Cigolini (Torino), Massimetti, Delle Donne, Ripepe (Firenze) y 22 coautores de observatorios, entre ellos Bucarey Parra y Lara (SERNAGEOMIN) | Sí (se confirma la atribución que se suponía) |
| `campus2022_sensors_22_1713.pdf` | Campus, Laiolo, Massimetti, Coppola 2022, Sensors 22:1713 | los cuatro de Torino (NATRISK) | Sí |
| `The_Capabilities_of_FY-3DMERSI-II_Sensor_to_Detect.pdf` | Aveni, Laiolo, Campus, Massimetti, Coppola 2023, Remote Sens. 15:2528 | Aveni (Sapienza Roma), resto Torino | Sí |

En los tres la página impresa coincide con la del visor PDF (Frontiers numera desde 1; MDPI imprime "N of 24").

**Método.** Volqué la capa de texto de cada PDF a un archivo temporal **sólo para ubicar** las páginas con ecuaciones, tablas y parámetros (ningún valor de este informe sale de esa capa, salvo lo marcado). Renderizé las 69 páginas de los tres PDF a 150 dpi en el scratchpad (fuera del repo) y **miré en imagen** estas:

- Coppola 2020: p. 1, 3, 4, 13, 15.
- Campus 2022: p. 1, 4, 6, 7, 8, 9, 16, 17, 19.
- Aveni 2023 (FY-3D): p. 1, 6, 8, 9, 10, 11, 15, 16.

Control de corrupción: ninguno de los tres volcados de texto contiene el carácter `¼` (0 apariciones en los tres), así que el marcador de S139 da negativo; igual toda cita de este informe está leída en la imagen.

**Qué NO cubrí.** Las páginas no miradas en imagen (Coppola 2020 p. 2, 5 a 12, 14, 16 a 21; Campus 2022 p. 2, 3, 5, 10 a 15, 18, 20 a 24; FY-3D p. 2 a 5, 7, 12 a 14, 17 a 24) las revisé sólo por búsqueda de palabras clave en la capa de texto (threshold, background, ROI, NTI, ETI, sigma, K1, C1, C2, resampl, bow, saturat, night, zenith, false alert, supervision, 375). No leí el material suplementario de ninguno (no está en `documentacion/`). No leí Coppola 2023 (feart-11-1240107), que la síntesis del repo mezcla con Coppola 2020 en la misma sección.

**Resumen de lo que aportan.** Ninguno de los tres trae los umbrales K1, C1, C2, la conectiva de los Tests 2 y 3 ni la ecuación del ETI: los tres remiten a SP426.5. Lo que sí traen son descripciones del flujo operacional (fondo, bow tie, grilla, qué distancia publica la web, cuánta falsa alerta espera el propio grupo) y una tabla de frecuencia de alertas VIIRS contra MODIS que importa para el frente de sobre-publicación.

---

## Hallazgos, ordenados por gravedad

### A1. MIROVA elimina el bow tie con un algoritmo nombrado (Liu et al. 2008), antes de remuestrear (D28, pregunta 6 del correo)

- **Localizador**: FY-3D (Aveni 2023), p. 8 (visor p. 8), §3.2 "MERSI-II Data Pre-Processing", párrafo que empieza en la p. 7 y termina en la p. 8, 3.ª a 5.ª oración de la p. 8. Referencia [82] de la lista final (sólo capa de texto): Liu, Wen, Dong, Dai, "A New Prompt Algorithm for Removing Bowtie Effect of MODIS L1B Data", CISP 2008, pp. 663 a 667.
- **Cita textual**: "Consistently with the MIROVA algorithm, we employed the approach proposed by [82] to identify and isolate the pixels affected by bow-tie distortions".
- **Qué dice**: el grupo declara que MIROVA identifica y aísla los píxeles duplicados por bow tie, con un método publicado para MODIS L1B, y lo hace sobre los gránulos originales, antes del remuestreo a la grilla de 51 × 51 km descrito en §3.3. La misma página dice que los píxeles duplicados sobreestiman la anomalía y la energía.
- **A qué responde**: **confirma D28** (`docs/MIROVA_DIVERGENCES.md:2282`: "El bow tie de MODIS no se trata en ningún paso del perfil operacional") y le agrega lo que el catálogo no tiene: el nombre del algoritmo y el orden (de-solapar, luego remuestrear), coherente con lo que `docs/MIROVA_DIVERGENCES.md:1913-1914` atribuye a Coppola 2012 §3.2. Contesta en buena parte la mitad "bow tie" de la **pregunta 6** del correo (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md:37-39`). El repo no cita a Liu et al. 2008 (búsqueda de "Liu" en `docs/MIROVA_DIVERGENCES.md`, `docs/AUDIT_S138.md` y `documentacion/BIBLIOGRAPHY_SYNTHESIS.md`: 0 resultados).
- **Salvedad**: la frase la escribe un paper de MERSI-II diciendo que actúa "consistently with" MIROVA; no es una descripción directa del procesamiento MODIS de MIROVA. Que MIROVA use literalmente Liu 2008 para MODIS es la lectura natural, no una afirmación explícita.
- **Confianza** 4. **Gravedad** 4 (da el paso concreto que falta para un brazo fiel de D17/D28).

### A2. Tres papers del grupo definen el fondo del VRP como el PROMEDIO de los píxeles que rodean al alertado; FY-3D agrega "no alertados" (D25, pregunta 4)

- **Localizadores**:
  - Coppola 2020, p. 3, columna derecha, párrafo tras la ecuación del VRP (la ecuación no está numerada).
  - Campus 2022, p. 7, §3.2, párrafo tras la ecuación (2).
  - FY-3D, p. 8, §3.3, párrafo tras la ecuación (3).
- **Citas textuales**:
  - Coppola 2020: "is the MIR radiance of the background (average radiance of pixels surrounding the anomaly)".
  - Campus 2022: "calculated as the arithmetic mean of pixels surrounding the active one/s".
  - FY-3D: "namely the average radiance of the surrounding, non-alerted pixels".
- **Qué dice**: el fondo es la media de los vecinos del activo, sin alertados. Ninguno de los tres usa la palabra mediana ni habla de un anillo regional, y ninguno menciona recortar a cero un exceso negativo.
- **A qué responde**: **confirma D25** (`docs/MIROVA_DIVERGENCES.md:2254`) con confirmaciones anteriores a Fernandina 2025 (2020 y 2022), y la de 2023 coincide en la exclusión de alertados. Contradice el código de hoy: `pipeline/detection_context.py:1064` (`t_bg = float(np.median(bg_vals))`). Sobre el recorte a cero (segunda mitad de la pregunta 4): los tres callan, así que **no la contestan**.
- **Confianza** 5 (media, vecinos). **Gravedad** 4.

### A3. Campus 2022: el detector de MIROVA para VIIRS es "el mismo usado para MODIS"; no hay umbrales propios de VIIRS (umbrales VIIRS, sobre-publicación)

- **Localizador**: Campus 2022, p. 7, §3.2, 3.er párrafo, 1.ª oración; y 1.er párrafo, última oración ("steps 1 to 4 have been slightly modified").
- **Cita textual**: "The hot-spot detection algorithm is the same used for MODIS and based on spectral indices and statistical thresholds".
- **Qué dice**: para VIIRS M13/M15 (750 m) MIROVA aplica el detector de SP426.5 sin publicar umbrales distintos. El mismo apartado dice que los cuatro pasos fueron "slightly modified" y adaptados a VIIRS, pero no dice cuáles; lo único concreto adaptado es la grilla (67 × 67 píxeles de 750 m) y el coeficiente del VRP.
- **A qué responde**: es la única declaración del grupo sobre umbrales VIIRS en estos tres papers. **Matiza** a favor de usar la Tabla 1 de SP426.5 también en VIIRS y **contradice** la sugerencia de `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:141-142` ("Track A `mirova_equivalent` debería usar n=12 nocturno VIIRS"), que viene de Di Bella 2024 (INGV Catania, no MIROVA, regla A9). No hay nada sobre 375 m: el paper es de 750 m y sólo menciona 375 m como potencial (p. 19, última oración, citando [103], Coppola, Valade et al., Sabancaya).
- **SOSPECHA**: que "slightly modified" incluya algún cambio de umbral. El texto no permite afirmarlo ni descartarlo; es una buena pregunta para el correo.
- **Confianza** 3 (la frase es clara, el alcance de "slightly modified" no). **Gravedad** 4.

### A4. En MIROVA, VIIRS publica muchas más alertas que MODIS, y la diferencia crece en volcanes de bajo flujo (frente de sobre-publicación)

- **Localizador**: Campus 2022, p. 16, §5, párrafo "The number of alerts", 3.ª y 4.ª oración; Tabla 4, p. 17.
- **Cita textual**: "It should be emphasized that the increase of VIIRS detections is inversely proportional to the average VRP".
- **Qué dice**: sobre 9 volcanes en 2021, MIROVA con VIIRS (750 m, Suomi-NPP y NOAA-20, día y noche) da 6293 alertas contra 3883 de MODIS (+62 %), con más de 100 % de aumento en Manam, Bagana y Sabancaya. En la Tabla 4, Nevados de Chillán tiene frecuencia nocturna de alerta 71,4 % VIIRS contra 57,5 % MODIS, y Sabancaya 69,5 % contra 55,0 %. Los autores lo atribuyen a mejor resolución, menor NEdT y la agregación de VIIRS, no a falsas alertas.
- **A qué responde**: al diagnóstico "publicamos de más frente a MIROVA en VIIRS 375 m". **Matiza**: el propio MIROVA espera una frecuencia de alerta mucho mayor en VIIRS que en MODIS, sobre todo en volcanes débiles, así que parte de lo que parece sobre-publicación puede ser comparar contra una referencia de otro sensor o de otra resolución. No dice nada de 375 m (la tabla es 750 m). Útil para el control de paridad de cobertura por sensor (memoria `feedback_s135_paridad_de_cobertura_antes_de_comparar.md`).
- **Confianza** 5 (números leídos en la tabla). **Gravedad** 3.

### A5. La pantalla "Distance from summit" de la web MIROVA grafica el píxel caliente MÁS LEJANO (pregunta 11 del correo)

- **Localizador**: Coppola 2020, p. 4, columna derecha, subsección "Distance From the Summit", 1.ª oración.
- **Cita textual**: "shows the distance from the farthest hot pixel to the summit of the volcano".
- **Qué dice**: la serie de distancia de la web no es la del píxel más caliente sino la del más lejano; la precisión de ubicación declarada es ±1 km (mismo apartado, párrafo siguiente).
- **A qué responde**: **confirma** lo que S139 dedujo empíricamente en `docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md:35-36` ("se comporta como `Max_Dist`: la distancia de la cumbre al píxel alertado más lejano"). Contesta la **pregunta 11** del correo (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md:45-46`) para la web de 2020; se podría quitar o bajarla a "¿sigue siendo así?".
- **Salvedad**: describe la web de 2018 a 2019 (capturas "accessed on 19 November 2018"); no prueba que el campo que raspa Mirova-v1 hoy sea el mismo.
- **Confianza** 4. **Gravedad** 3.

### A6. La web MIROVA separa proximal y distal con un corte FIJO de 5 km para todos los volcanes (D13, D18)

- **Localizador**: Coppola 2020, p. 4, columna derecha, subsección "VRP Time Series", 3.ª oración.
- **Cita textual**: "proximal (hotspots located within 5 km from the summit are represented by blue stems) and distal anomalies".
- **Qué dice**: el color de la serie temporal separa a 5 km del cráter, igual para todos. Es un criterio de visualización, no de detección; el párrafo no filtra nada.
- **A qué responde**: el repo separa summit/far con `inner_radius_km` por volcán, de 3 a 20 km (CLAUDE.md del proyecto, tabla de `inner_radius_km`; D13 en `docs/MIROVA_DIVERGENCES.md:1468` y D18 en `:1975`). **Matiza** la idea de que esos radios sean el criterio de la web: en 2020 la web del grupo usaba 5 km para todos. Que los radios de los KML sean otra cosa (región de la imagen) no está verificado aquí: **SOSPECHA**.
- **Confianza** 4. **Gravedad** 3 (toca cuántas detecciones se pintan como cráter, sobre todo PCC con 20 km).

### A7. La síntesis bibliográfica atribuye a Coppola 2020 dos cosas que ese paper no dice

- **Localizador**: Coppola 2020, p. 3, ecuación del VRP (columna derecha) y p. 4 (subsección "VRP Time Series"); contra `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:91` y `:93`.
- **Cita textual** (p. 3, definición de la suma): "where npix is the number of alerted pixels".
- **Qué dice**: la suma del VRP de 2020 corre sobre los **píxeles alertados**, con `A_pixel` de 1 km² "for the resampled MODIS pixels" y coeficiente 18.9. La síntesis dice en l. 91 "`L_MIR_total = Σ_ROI [...]` (integrado-ROI)", que es otra operación (integrar toda la región). La l. 93 dice "Umbrales menor-sensibilidad summit ≤5 km, mayor-sensibilidad flanco": en Coppola 2020 el único 5 km es el color de la serie (A6); no hay umbrales por región en las páginas miradas ni en la búsqueda de texto del resto.
- **A qué responde**: a la calidad de la fuente de verdad bibliográfica (A35, A95). La sección mezcla 2020 con 2023 ("MIROVA v1.0", no leído); puede que la l. 93 venga de 2023: **SOSPECHA**, no verificado. Lo verificado es que 2020 no lo dice.
- **Confianza** 4 (sobre 2020). **Gravedad** 3 (una sesión futura podría justificar integrar el ROI o umbrales regionales citando este paper).

### A8. Coppola 2020 da la banda TIR 32 (12,02 µm); Campus 2022 y FY-3D 2023 ya dan la 31; nada decide la banda MIR primaria (D20, D21)

- **Localizadores**:
  - Coppola 2020, p. 3, columna derecha, 2.º párrafo de "Download, Data Processing, and Sensibility", 1.ª oración; y columna izquierda, "Architecture of the System", 4.ª oración (canal dual MIR).
  - Campus 2022, p. 6, Tabla 1 (fila "ID TIRBand(s)": M-15 y 31) y 2.º párrafo bajo la tabla ("bands 21/22 (MIR) and 31 (TIR)").
  - FY-3D, p. 6, Tabla 1 (fila "ID TIR Band (s)": 24, 31, M-15/I-5; fila "ID MIR Band (s)": 21, 21/22, M-13/I-4).
- **Cita textual** (Coppola 2020): "Middle Infrared [MIR] at 3.959 µm and Thermal Infrared [TIR] at 12.02 µm) are resampled in regular grids of 50 × 50 km".
- **Qué dice**: en 2020 el grupo todavía describe la TIR de MODIS a 12,02 µm (banda 32); en 2022 y 2023 sus tablas asignan la 31. Para la MIR, los tres dan "3,959 µm" o "21/22", que es la longitud central nominal de las **dos** bandas y no dice cuál manda. Coppola 2020 sólo agrega que el canal dual tiene "low/high gain settings".
- **A qué responde**: **matiza D20** (`docs/MIROVA_DIVERGENCES.md:2150-2154`, nota S140 basada en Fernandina 2025): el cambio de 32 a 31 en la descripción del grupo aparece entre 2020 y 2022, no recién en 2025. No aporta a **D21** (`:2180`): la pregunta 2 del correo sigue abierta. Además, la grilla aparece como **50 × 50 km** en 2020 contra 51 × 51 km en Campus 2022 p. 7 y FY-3D p. 8: diferencia de redacción, relevante sólo si alguien reconstruye la grilla desde 2020 (D15, D17).
- **Confianza** 5 (lo que dicen), 2 (sobre lo que implica para D21). **Gravedad** 2.

### A9. El grupo espera 0 a 3 % de falsas alertas por pasada MODIS, dependientes de altitud y topografía, y reconoce supervisión posterior (sobre-publicación, techo de "supervisión")

- **Localizador**: Coppola 2020, p. 13, columna izquierda, subsección "Tinakula, Solomon Islands", últimas cinco oraciones del párrafo; y Campus 2022, p. 8, §3.4, 2.º párrafo, dos últimas oraciones.
- **Citas textuales**:
  - Coppola 2020: "generally comprised between 0 and 3% (number of false alerts/number of MODIS overpasses)".
  - Coppola 2020, misma página: "These false alerts depend on the regional and local environmental conditions as climate, elevation, topography and land cover type".
  - Campus 2022: "we test the potential efficiency of the algorithm in NRT applications where such supervision is not applied".
- **Qué dice**: el grupo cuantifica su tasa de falsas alertas MODIS (citando "Coppola et al., 2016b") en unidades de **pasadas**, la hace depender de altitud y topografía (el mecanismo de A69), dice que los incendios no se separan espectralmente, y cuenta que en Tinakula hizo falta supervisión posterior para descartar una falsa alerta. Campus 2022 evalúa sin supervisión a propósito y dice que así es el NRT.
- **A qué responde**: al denominador del frente de sobre-publicación: nuestro ~63 % es sobre "pasadas donde MIROVA miró y no vio nada", otra unidad; los dos números no se comparan directamente (A90, A93). **Confirma** la regla de memoria `feedback_s135_techo_artificial_supervision.md` y A76: el canal NRT es algorítmico y la supervisión es posterior. La referencia completa de "Coppola et al., 2016b" no la resolví en la lista: **SIN LOCALIZAR**.
- **Confianza** 5 (lo citado). **Gravedad** 3.

### A10. El ángulo cenital baja el VRP y el remuestreo lo corrige "parcialmente", según el propio grupo (D17, gradiente cenital S130)

- **Localizador**: FY-3D, p. 15, §4.2.1, último párrafo, 3.ª a 5.ª oración, continuando en p. 16, 1.ª y 2.ª oración; y p. 10, §4.1, 3.er párrafo (cenit ≤ 40°), con la Tabla 2 en p. 11.
- **Citas textuales**:
  - p. 15: "the only increase in the satellite zenith corresponds to a decrease in the VRP".
  - p. 16: "Although this is partially corrected during the resampling step (see [9]), residual artefacts can hardly be removed entirely".
- **Qué dice**: en escenas casi simultáneas, más ángulo cenital da menos VRP; el grupo lo atribuye a la atenuación atmosférica por camino óptico más largo (citando [92]) y a que un foco sub-píxel se integra sobre un área que crece hacia el borde del barrido. El remuestreo (ref. [9], Coppola et al. 2012, Stromboli) lo corrige sólo en parte. En la Tabla 2, restringir a cenit ≤ 40° sube la frecuencia de alerta de 28,20 / 35,24 / 48,34 % a 44,45 / 45,66 / 57,56 % (MERSI / MODIS / VIIRS).
- **A qué responde**: **matiza** D17 y el hallazgo S130 (`docs/MIROVA_DIVERGENCES.md:1900-1905`: en nuestro cruce "MIROVA es plano" frente al ángulo). El grupo reconoce que su VRP sí cae con el cenit, al menos en Etna 2022 a 2023. **SOSPECHA**, no medida aquí: si MIROVA sale plano en Chile, el mecanismo del gap no puede ser sólo "ellos corrigen el ángulo y nosotros no".
- **Confianza** 4. **Gravedad** 3.

### A11. FY-3D 2023 publica la recta de α contra longitud de onda (la misma de Coppola 2025) con VIIRS I-4 marcado; es la fuente más antigua de H2

- **Localizador**: FY-3D, p. 8, §3.3, ecuación (2); p. 9, §3.4, 2.º párrafo, y Figura 3 con la ecuación del ajuste impresa dentro del gráfico.
- **Cita textual** (p. 9): "we obtained the sensors' specific α coefficients, namely 2.88 × 10−9 ... both for MERSI and VIIRS bands 21 and M-13".
- **Qué dice**: `VRP = ΔL_MIR × σε/(α ε_MIR) × A_pix`, con α de la recta impresa en la Figura 3, "α = −8.6344·10^−10 · x + 6.3796·10^−9", R² = 0.99987, válida en 3,5 a 4,15 µm y 600 a 1500 K; α = 2,88e−9 para M13 (4,05 µm) y 2,96e−9 para MODIS banda 21 (3,959 µm). La figura marca VIIRS I-4 en 3,74 µm, cerca de 3,15e−9 leído a ojo en el eje. σ/α da 19,69 (M13) y 19,16 (MODIS), aritmética mía con σ = 5,67e−8.
- **A qué responde**: **confirma** H2 de S139 (`docs/audit_s139/LECTURA_PDF_TABLAS_FIGURAS.md:94-112`), que la atribuía a Coppola 2025: la misma recta ya estaba en 2023. Respalda `WOOSTER_COEFF = 19.7` (`pipeline/process_viirs_mod.py:66`) y `18.0` (`pipeline/process_viirs.py:77`). Para MODIS repite la diferencia de 1,3 % con nuestro 18,9; la etiqueta "MODIS band 21" es de la figura, no una afirmación sobre la banda primaria (no mueve D21).
- **Confianza** 5. **Gravedad** 2.

### A12. La "discrepancia" k_VIIRS750 1,11e7 contra Campus 1,97e7 que anota el repo no existe: es el mismo número multiplicado por el área

- **Localizador**: Campus 2022, p. 7, §3.2, ecuación (1) y la oración que la sigue; contra `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:133` y `:248`.
- **Cita textual**: "where Apix is the pixel surface in km2 (equal to 0.5625 for VIIRS M-bands)".
- **Qué dice**: `VRP = ΔL_MIR · 1.97 × 10^7 · A_pix`; con A_pix = 0,5625 km², 1,97e7 × 0,5625 = 1,108e7 (aritmética mía), que es el 1,11e7 de Di Bella y el 11.081.250 del CLAUDE.md del proyecto. La l. 133 lo marca "discrepancia ... a resolver" y la l. 248 escribe "1.97×10⁷/Apix", dividiendo, cuando el paper multiplica.
- **A qué responde**: limpieza de la síntesis; no cambia el pipeline (el coeficiente de producción ya es el correcto).
- **Confianza** 5. **Gravedad** 2.

### A13. La grilla se centra en las coordenadas GVP ya en 2023 (D17)

- **Localizador**: FY-3D, p. 8, §3.3, 1.er párrafo, 3.ª oración. También Campus 2022, p. 7, §3.2, 2.º párrafo ("centered on the volcano summit"), sin decir de qué base.
- **Cita textual**: "resampled to a regular UTM 51 × 51 km grid, centred on the volcano's summit as per coordinates provided by the Global Volcanism Program".
- **Qué dice / a qué responde**: **confirma** la cita de Fernandina 2025 que S140 puso al inicio de D17 (`docs/MIROVA_DIVERGENCES.md:1896-1898`), con una versión dos años anterior. Nada nuevo en contenido.
- **Confianza** 5. **Gravedad** 2.

### A14. Coppola 2020: con nubes alrededor de un cráter alto la anomalía puede quedar "descartada" o "atenuada", sin decir si es automático (D14, fondo)

- **Localizador**: Coppola 2020, p. 15, columna izquierda, subsección "Image Quality Assessment", penúltima oración.
- **Cita textual**: "thermal anomalies within high-altitude summit craters may be discarded or classified as strongly attenuated, because the surroundings pixels are cloudy".
- **Qué dice**: los observatorios reportan que un cráter despejado rodeado de nubes puede quedar descartado o marcado como atenuado. El mismo párrafo dice que la evaluación de nubosidad "is currently absent in all the operational systems", así que "discarded" suena más a interpretación del usuario o a efecto del fondo que a una máscara.
- **A qué responde**: al papel de las nubes en el anillo de fondo (D14 cerrada, D25). **SOSPECHA** en cualquier lectura mecánica: el texto no dice qué paso descarta.
- **Confianza** 2 (sobre el mecanismo). **Gravedad** 2.

### A15. MIROVA VIIRS procesa también de día, y Campus 2022 atribuye los umbrales diurnos a una referencia ajena al algoritmo (D27)

- **Localizador**: Campus 2022, p. 17, párrafo "Nighttime vs daytime data", 2.ª y 3.ª oración; Tabla 4 (columnas f% nighttime y daytime). Referencia [26] de la lista (sólo capa de texto): Dean, Servilla, Roach, Foster, Engle 1998, Eos 79, "Satellite monitoring of remote volcanoes improves study efforts in Alaska".
- **Cita textual**: "this strong reduction is due to the higher thresholds of the daytime algorithm specifically settled to avoid false alerts".
- **Qué dice**: el MIROVA VIIRS de 2021 corre de día con umbrales más altos (frecuencia de alerta VIIRS 51 % noche contra 20,4 % día). La cita [26] apunta a un artículo de Alaska de 1998, no a SP426.5 (que es [28]): **SOSPECHA** de error de numeración del paper.
- **A qué responde**: **confirma D27** (`docs/MIROVA_DIVERGENCES.md:2276`) como divergencia literal: MIROVA publica detecciones VIIRS diurnas que nosotros no generamos. No da los valores diurnos.
- **Confianza** 4. **Gravedad** 2.

### A16. Límites físicos declarados del método MIR (sin efecto en decisiones)

- **Localizador**: Coppola 2020, p. 3, columna derecha, dos últimos párrafos; Campus 2022, p. 7, §3.2, última oración del párrafo que sigue a la ecuación (2).
- **Cita textual** (Coppola 2020): "the lower detection limit (1 MW) would correspond to two end-member cases".
- **Qué dice**: el método MIR mide superficies sobre 500 K (Coppola 2020) o 600 K (Campus 2022), con error ±30 %, y un piso nominal de ~1 MW. Campus 2022 p. 9 dice igual que las distribuciones de Láscar van de 0,1 a unos 20 MW, bajo ese piso nominal.
- **A qué responde**: contexto para A77/A78 y para el piso de VRP retirado en S130; no cambia nada.
- **Confianza** 5. **Gravedad** 1.

---

## VERIFICADO LIMPIO

Lo que busqué y **no está** en estos tres papers (en las páginas vistas en imagen, y en el resto por búsqueda de texto; la búsqueda de texto no ve lo que sólo está dentro de figuras):

1. **Conectiva de los Tests 2 y 3** (`min` o `max`, `and` u `or`): no está. Los tres remiten a Coppola 2016a. Coppola 2020 p. 3 sólo dice "a series of spatial operations"; Campus 2022 p. 7 "statistical thresholds"; FY-3D p. 8 "spectral and spatial filters". Pregunta 1 del correo: sigue abierta.
2. **Valores de K1, C1, C2, N·σ**: ningún número de umbral de detección en los tres, ni para MODIS ni para VIIRS 750 ni 375 m.
3. **Umbral o adaptación para VIIRS 375 m**: no hay. Campus 2022 es 750 m; FY-3D compara con VIIRS NOAA-20 sin decir qué resolución usó para el VRP (su Tabla 1, p. 6, lista M-13/I-4 "for completeness").
4. **Ecuación del ETI o definición de NTIbk / NTIapp**: Coppola 2020 p. 3 nombra el ETI y remite a 2016a; los otros dos no lo nombran. Pregunta 12: abierta.
5. **Recorte a cero del exceso de radiancia** (mitad de la pregunta 4): no aparece.
6. **Tamaño o forma del ROI1 / ROI2**: la sigla "ROI" no aparece en ninguno. Pregunta 6, mitad ROI: abierta (SP426.5 p. 3 la contesta para 2016).
7. **Píxeles saturados en la suma del VRP** (D24, pregunta 5): FY-3D p. 11 y p. 19 hablan del límite de saturación de MERSI-II sólo para decir que no afectó en Etna; ninguno dice si el píxel saturado entra a la suma.
8. **Test 1 como camino propio** (D23): no aparece.
9. **Regresión iterativa a 3 σ** (D29): no aparece.
10. **Fondo global contra local por volcán** (pregunta 10): no aparece.
11. **Columna "class" del OSF, Tupungatito, cobertura VIIRS 750 en Chile** (preguntas 8 y 9): no aparecen. Campus 2022 usa Láscar y Nevados de Chillán como casos, y rotula Sabancaya como "(Chile)" en la Tabla 4 (p. 17), error del paper (el texto de p. 16 no le asigna país; Coppola 2020 p. 9, capa de texto, lo da en Perú). Nada sobre Tupungatito.
12. **Banda MIR primaria de MODIS** (D21, pregunta 2): los tres dicen "21/22" o "3,959 µm", que no distingue. No está.
13. **Máscara de nubes automática en la detección**: Coppola 2020 p. 15 dice que la evaluación de nubosidad está ausente en todos los sistemas operacionales; FY-3D p. 10 descarta escenas nubladas **a mano** y sólo para el TADR. Ninguno describe una máscara en la detección.
14. **Filtro por distancia en la detección**: ninguno. El 5 km de Coppola 2020 es color de la serie (A6); Campus 2022 p. 9 verifica a ojo que las alertas débiles de Láscar 2012-2013 caen dentro del cráter, sin filtro.

**Control del instrumento**: el volcado de texto se usó sólo para ubicar páginas. Los 0 `¼` en los tres volcados indican que su capa de texto no tiene la corrupción de SP426.5, pero ningún valor citado arriba sale de ella, salvo lo marcado explícitamente como "capa de texto" (listas de referencias de Campus 2022 y FY-3D, y el país de Sabancaya en Coppola 2020 p. 9).
