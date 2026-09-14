# LECTOR D: segunda pasada de papers de casos de estudio del grupo MIROVA (S141)

Auditor: agente de lectura D, 2026-09-14. **Lectura, no arreglo: no se modificó ningún archivo del
repositorio salvo este informe; no se tocó git.**

**Método.** Las páginas con método satelital, figuras o tablas con parámetros se renderizaron con
PyMuPDF a 150 dpi en
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\render_D\`
(fuera del repo) y se leyeron como imagen con `Read`. Toda cita textual de este informe sale de la
imagen, salvo las marcadas **[capa de texto]**, que son frases sin operadores ni números críticos. Las
páginas a renderizar se eligieron con un barrido de palabras clave sobre la capa de texto (MIROVA,
NTI, threshold, VIIRS, background, cloud, sigma, Wooster, night, 375, 750, manual, resampl, UTM,
saturat, zenith, filter). **Limitación de ese filtro**: una página con un parámetro que no use ninguna
de esas palabras no se habría renderizado.

**Autores y afiliación.** Se tomaron de la capa de texto de la p. 1 (y de la última página cuando la
afiliación va al final, Laiolo 2026 p. 21). Son nombres y direcciones, no operadores, así que la
corrupción conocida de la capa de texto no los afecta; aun así no se renderizó la p. 1 de los 11.

---

## 1. Encabezado: los 11 PDF

| # | PDF | Paper (según p. 1 y encabezado de página) | Autores del grupo MIROVA | Otras afiliaciones | ¿MIROVA? | Qué se leyó (páginas del visor) |
|---|---|---|---|---|---|---|
| 1 | `s41598-021-92542-z.pdf` | Coppola et al. 2021, Sci. Rep. 11:13090, grupo volcánico Klyuchevskoy (KVG) | Coppola, Laiolo (Torino); Massimetti | GFZ Potsdam, IVS Kamchatka, ISTerre | Sí | p. 3, 4, 6, 12, 13 |
| 2 | `1-s2.0-S0377027316305248-main.pdf` | Laiolo et al. 2017, JVGR 340:170-179, Santa Ana (El Salvador) | Laiolo (Firenze, Torino), Coppola, Cigolini (Torino) | UES, MARN El Salvador, La Réunion | Sí | p. 2, 3, 4, 6, 7, 9 (impresas 171, 172, 173, 175, 176, 178) |
| 3 | `1-s2.0-S0377027315003716-main.pdf` | Coppola, Laiolo, Cigolini 2016, JVGR 322:6-19, Vanuatu 2000-2015 | Los tres (Torino, Firenze) | ninguna | Sí | p. 3, 5, 6, 8, 13 (impresas 8, 10, 11, 13, 18) |
| 4 | `1-s2.0-S0377027322002384-main.pdf` | Morelli et al. 2022, JVGR 432:107707, infrasonido de Yasur | Campus (entonces CTBTO), Coppola (Torino) | Firenze (infrasonido), INGV Osservatorio Vesuviano | Coautoría MIROVA; paper de infrasonido | sólo §3.2, p. 8 |
| 5 | `s00445-009-0320-8.pdf` | Coppola, James, Staudacher, Cigolini 2010, Bull. Volcanol. 72:341-356, Piton de la Fournaise | Coppola, Cigolini | Lancaster, OVPF | Grupo sí, pero **anterior a MIROVA** (MODVOLC refinado) | p. 4, 5, 6, 7, 9 (impresas 344 a 347, 349) |
| 6 | `s00445-022-01523-1.pdf` | Coppola et al. 2022, Bull. Volcanol. 84:16, Sabancaya | Coppola, Laiolo, Massimetti, Campus, Cigolini (Torino) | UNAM, INGEMMET, UNSA, La Réunion | Sí | p. 4, 5 |
| 7 | `s00445-024-01721-z.pdf` | Campus, Aveni, Laiolo, Massimetti, Coppola 2024, Bull. Volcanol. 86:25, La Fossa (Vulcano), VIIRS 375 m | Todos | ninguna | Sí | p. 2, 3, 4, 5 (de 7) |
| 8 | `s00445-025-01932-y.pdf` | Laiolo et al. 2026, Bull. Volcanol. 88:11, Stromboli 25 años | Laiolo, Coppola (Torino), Aveni (Torino, Sapienza), Campus, Massimetti | Palermo, Firenze (Ripepe, Lacanna, Innocenti), Pisa | Sí | p. 3, 4, 5, 8, 16; p. 9 y 18 sólo capa de texto |
| 9 | `j.jvolgeores.2012.09.005.pdf` | Coppola, Laiolo, Piscopo, Cigolini **2013**, JVGR 249:39-48, densidad radiante (el DOI dice 2012, el volumen es 2013) | Todos (Torino) | ninguna | Sí | p. 8 (impresa 46, Apéndice 2) |
| 10 | `feart-11-1040199.pdf` | Campion y Coppola 2023, Front. Earth Sci. 11:1040199, lagos de lava | Coppola (Torino) | UNAM | Coautoría MIROVA | §2.2, p. 3 |
| 11 | `JGR Solid Earth - 2025 - Galetto - ...pdf` | Galetto et al. 2025, JGR Solid Earth 10.1029/2025JB031428, Semeru | Coppola (Torino) | Cornell, INGV ONT, CNR IREA | Coautoría MIROVA; usa productos MIROVA | p. 3, 4, 5, 12 (de 14) |

**Papers sin autores del grupo MIROVA**: ninguno. Los 11 tienen al menos a Coppola (Torino). Ninguno es de
INGV Catania ni de CNR Potenza. Morelli 2022, Campion 2023 y Galetto 2025 son de otros grupos con Coppola
como coautor y sólo consumen productos MIROVA: se leyó únicamente su sección MIROVA.

---

## 2. Hallazgos, por gravedad

### D-01 (gravedad 4). La serie publicada de Stromboli no es la salida cruda: MIROVA la filtra por distancia y/o intensidad y le quita el doble conteo entre sensores

- **Localizador**: `s00445-025-01932-y.pdf` (Laiolo et al. 2026), p. 4 de 21 (visor p. 4), sección
  «Methods and dataset», subsección «Satellite thermal data», columna derecha, segundo párrafo.
- **Cita textual**: «The VRP time series coming from the different sensors/detectors are combined and
  filtered in terms of distance and/or intensity of the thermal anomaly to minimize the false alerts and
  the double counting» (el mismo párrafo sigue: «thus resulting in 9712 data points (ca. 12%)», sobre
  82.329 imágenes).
- **Qué dice**: entre la detección y la serie que el grupo usa, hay tres pasos que no son el algoritmo
  de SP426.5: (a) combinar sensores, (b) filtrar por distancia y/o intensidad para bajar falsas alertas,
  (c) eliminar el doble conteo de detectores que adquieren a la misma hora. Queda el 12 % de las
  imágenes.
- **A qué responde**: al problema central de esta pasada (publicamos de más frente a MIROVA) y a la
  **pregunta 8** del `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` («is the published archive complete or
  filtered (for example by distance or intensity)?»): para esta serie de estudio, la respuesta impresa
  es «filtrada por distancia y/o intensidad». Toca también el cruce noche a noche (dos pasadas
  simultáneas de dos plataformas VIIRS cuentan una vez).
- **Confirma, contradice o matiza**: **matiza**. El repo cita este mismo párrafo sólo por la frase de
  la nube (`docs/MISSION.md:58-59`, `docs/MIROVA_DIVERGENCES.md:1552`), no por la del filtro:
  `grep -rn "filtered in terms of distance"`, `"double counting"` y `"9712"` sobre `docs/`,
  `CLAUDE.md` y `BIBLIOGRAPHY_SYNTHESIS.md` dan 0. El paper no dice qué distancia ni qué intensidad, ni
  si ese filtro se aplica también al feed NRT de mirovaweb (**SOSPECHA** abierta, no verificable desde
  el PDF).
- **Confianza** 5 en la cita; 3 en su alcance al NRT. **Gravedad 4.**

### D-02 (gravedad 4). El dataset VIIRS 375 m de MIROVA sobre La Fossa cuenta sólo alertas a menos de 1 km de las coordenadas GVP

- **Localizador**: `s00445-024-01721-z.pdf` (Campus et al. 2024), p. 5 de 7 (visor p. 5), columna
  derecha, primer párrafo, sobre la Fig. 2.
- **Cita textual**: «354 had at least one alerted pixel located within a distance of 1 km radius from
  the La Fossa cone (as per coordinates provided by the Global Volcanism Program»
- **Qué dice**: de 2.056 imágenes VIIRS nocturnas (marzo 2021 a marzo 2023), el paper declara alerta
  sólo cuando hay al menos un píxel alertado a menos de 1 km de la coordenada GVP, y con eso calcula la
  frecuencia de detección de 17,22 %. Es un criterio de distancia explícito, del propio grupo, sobre el
  mismo sensor (VIIRS I4, 375 m) donde nuestra sobre-publicación es mayor.
- **A qué responde**: a la sobre-publicación en VIIRS 375 m y a **D18** (ROI1 caja de 5 km frente a
  nuestro círculo de 3 a 20 km, `docs/MIROVA_DIVERGENCES.md:1975`). Contraste directo con
  `inner_radius_km` de 3 a 20 km por volcán (`CLAUDE.md:135`).
- **Confirma, contradice o matiza**: **matiza**. El repo cita Campus 2024 por el fondo (p. 3,
  `docs/DRIFTS_S17.md:16`) y por k = 18,0 (`docs/MIROVA_DETAILED_CITATIONS.md:277-283`), pero no por este
  radio (`grep "1 km radius"` y `"within a distance of 1 km"` dan 0). No prueba que el NRT use 1 km: es
  la elección de un estudio sobre un campo fumarólico chico. Sí prueba que, cuando el grupo publica un
  dataset VIIRS 375 m «MIROVA-processed», la cuenta de alertas pasa por una cerca de distancia al punto
  GVP mucho más estrecha que la nuestra.
- **Confianza** 5 en la cita; 3 en su transferencia al NRT. **Gravedad 4.**

### D-03 (gravedad 3). En los casos de estudio el grupo supervisa a mano, y en 2016 escribió que un punto suelto de MIROVA no es confiable sin mirar la imagen

- **Localizadores y citas** (cuatro papers, misma dirección):
  1. `s41598-021-92542-z.pdf` (Coppola 2021, KVG), p. 12, «Methods», «Satellite thermal data», segundo
     párrafo: «All the images were visually analyzed to discard the data contaminated by clouds, ash
     plumes, or poor viewing conditions (i.e., high satellite zenith)». Y a continuación: «the supervised
     dataset consists of 2139 images for Klyuchevskoy».
  2. `j.jvolgeores.2012.09.005.pdf` (Coppola 2013), p. impresa 46 (visor p. 8), Apéndice 2, columna
     derecha: «A post processing and a visual inspection of all the images allows us to discard all the
     cases in which the VRP estimates are clearly affected by cloud».
  3. `1-s2.0-S0377027315003716-main.pdf` (Coppola 2016, Vanuatu), p. impresa 10 (visor p. 5), §4.6,
     columna derecha: «single data points provided by MIROVA cannot be trusted without a visual
     inspection of the image». Y en el mismo párrafo: «we have not checked manually the large number of
     images processed at the five volcanoes (more than 50,000 images)».
  4. `s00445-025-01932-y.pdf` (Laiolo 2026), p. 4, mismo párrafo que D-01: «we avoid the visual
     inspection of the acquired dataset to discard cloud-contaminated images».
- **Qué dice**: la supervisión humana es la práctica corriente en los casos de estudio (2013, 2021),
  no una rareza del archivo OSF o de Fernandina; y el propio autor escribe que un dato individual de
  MIROVA sin inspección visual no es confiable. En 2016 y 2026 se declara explícitamente que NO se
  supervisó.
- **A qué responde**: a la nota durable `feedback_mirova_no_human_supervision.md` (memoria del agente,
  l. 21-30 y 37), que hoy dice que la supervisión aplica al OSF v2.5 (Coppola 2023) y a la respuesta
  rápida de Fernandina. Y al marco A54 de «falsos positivos» frente a MIROVA.
- **Confirma, contradice o matiza**: **matiza**, no contradice. Ninguna de las cuatro citas dice que el
  feed NRT de mirovaweb se supervise. Lo que agrega: (a) la lista de productos supervisados del grupo es
  más larga que la de la nota (casos de estudio 2013 y 2021), así que cualquier conteo de alertas sacado
  de un paper de caso de estudio no se transfiere al NRT sin mirar si ese paper supervisó; (b) la frase
  de 2016 es una admisión del autor de que la salida automática trae puntos no confiables, lo que
  vuelve plausible que MIROVA NRT tenga su propio ruido y no sea una vara limpia.
- **Confianza** 5 en las citas; 4 en el alcance declarado. **Gravedad 3.**

### D-04 (gravedad 3). El propio algoritmo MIROVA dispara sobre lagos cratéricos en estación cálida; el autor lo acota a menos de 2 % de las pasadas y menos de 5 MW

- **Localizador**: `1-s2.0-S0377027315003716-main.pdf` (Coppola 2016, Vanuatu), p. impresa 10 (visor
  p. 5), §4.5 y §4.6 (columna derecha, penúltimo párrafo), y p. impresa 18 (visor p. 13), §6, viñeta
  final. §4.4 (p. 10, columna izquierda) para Aoba.
- **Citas textuales**: «a limited number of "false" detections (typically less than 2% of the total
  MODIS overpasses), may be eventually triggered by the MIROVA algorithm in absence of volcanic
  activity» (p. 10). Sobre Aoba: «the "excess" of MIR radiance at the base of the MIR method, could be
  due to the contrast between the lake temperature and its surroundings» (p. 10).
- **Qué dice**: en Gaua (lago cratérico) las alertas son persistentemente menores a 5 MW, aparecen sobre
  todo en diciembre a marzo sin actividad reportada, y el autor las trata como ruido de fondo del
  sistema. En Aoba el exceso MIR puede ser contraste térmico del lago. La conclusión (p. 18) repite
  «less than 2% of false alerts».
- **A qué responde**: a la sobre-publicación y a la clasificación A54 (categorías de «FP» frente a
  MIROVA): lagos tibios post-atardecer son la categoría que el glosario de `CLAUDE.md` pone como ejemplo
  de FP. Complementa `docs/audit_s139/LECTURA_PDF_TABLAS_FIGURAS.md` H9 (Coppola 2014: 3,5 % de falsas).
- **Confirma, contradice o matiza**: **confirma** que el algoritmo del grupo, sin supervisión, también
  genera este tipo de alerta, y da un orden de magnitud de tolerancia (≤2 % de las pasadas, <5 MW). Es
  MODIS 1 km, régimen tropical: no se transfiere tal cual a VIIRS 375 m. `grep "Gaua"` en `docs/` da 0.
- **Confianza** 5 en la cita; 3 en su uso como vara para VIIRS 375 m. **Gravedad 3.**

### D-05 (gravedad 3). El remuestreo a grilla UTM centrada en la cumbre está escrito también para VIIRS 375 m, con tamaño 50 × 50 km; el repo dice 51 × 51

- **Localizadores y citas**:
  1. `s00445-024-01721-z.pdf` (Campus 2024), p. 3, columna derecha, segundo párrafo (VIIRS I4/I5):
     «after an initial resampling of the original granule in a regular 50 × 50 km UTM grid, first
     detects the thermally anomalous pixels».
  2. `1-s2.0-S0377027315003716-main.pdf` (Coppola 2016, Vanuatu), p. impresa 8 (visor p. 3), §3, MODIS:
     «cropping and resampling into 50 × 50 km box centered on the volcano summit».
  3. `1-s2.0-S0377027316305248-main.pdf` (Laiolo 2017, Santa Ana), p. impresa 173 (visor p. 4), §3.1,
     MODIS: «produce 50 × 50 km NTI maps centered on the volcano summit».
- **Qué dice**: el grupo describe el remuestreo previo a la detección como paso de MIROVA en MODIS
  (2016, 2017) y, lo nuevo para este frente, **en su dataset VIIRS 375 m** (2024), antes de los filtros
  espectrales y espaciales. El tamaño impreso en los tres es 50 × 50 km.
- **A qué responde**: a **D17** (`docs/MIROVA_DIVERGENCES.md:1894`, grilla y remuestreo, con
  `ENABLE_UTM_REGRID = False` según D28 l. 2284) y a la pregunta 6 del correo. El repo apoya el
  remuestreo VIIRS en Fernandina 2025 (51 × 51, D17 l. 1896-1898) y en `CLAUDE.md:132` («grilla MIROVA
  UTM 51×51 km»).
- **Confirma, contradice o matiza**: **confirma** que VIIRS 375 m también se remuestrea (segunda fuente
  independiente de Fernandina, específica del sensor I-band) y **matiza** el tamaño: 50 frente a 51. La
  diferencia es de un píxel de 1 km por lado y probablemente redacción (51 impar deja la cumbre en un
  píxel central); no la resuelvo, y no afecta el radio inscrito de 25 km de `CLAUDE.md:132` de forma
  medible. `grep "50 x 50 km"` sobre D17, `CLAUDE.md` y `MISSION.md` da 0.
- **Confianza** 5 en las citas. **Gravedad 3** (por el sensor; el 50/51 solo sería 1).

### D-06 (gravedad 3). Coppola 2013 pone el bow tie antes del remuestreo y define el fondo del VRP como media de los vecinos del activo o del cúmulo

- **Localizador**: `j.jvolgeores.2012.09.005.pdf` (Coppola et al. 2013, JVGR 249), p. impresa 46 (visor
  p. 8), Apéndice 2, columna izquierda (último párrafo) y columna derecha (primer párrafo, ecuaciones
  A.1 y A.2).
- **Citas textuales**: «Pre-processing of the original MODIS granules consists in the removal of the
  bow-tie effect and resampling into an equal area projection with 1 km pixel size». Y: «L4bk, is
  estimated from the arithmetic mean of all the pixels surrounding the active one or cluster of active
  pixels». Ec. (A.2): «VRP = 1.89 × 10⁷ × ΔL4».
- **Qué dice**: (a) orden del preproceso: primero bow tie, después remuestreo a área igual de 1 km; (b)
  fondo = media aritmética de los píxeles que rodean al activo o al cúmulo; (c) coeficiente 1,89×10⁷
  (el 18,9 con A_pix = 1 km²); (d) bandas 21/22 y 32; (e) **umbral NTI definido por erupción** a partir
  de la serie temporal («an appropriate NTI threshold which takes into account the normal fluctuation
  of this index due to the local and seasonal conditions»), que no es el algoritmo de SP426.5.
- **A qué responde**: pregunta 6 del correo (bow tie antes del remuestreo), **D28**
  (`docs/MIROVA_DIVERGENCES.md:2282`), **D17** (l. 1913-1914, que ya afirma el orden «bow-tie + regrid»
  citando «Coppola 2012 §3.2», otro PDF: `coppola2012_jvgr_stromboli_10.1016-j.jvolgeores.2011.12.001.pdf`)
  y **D25** (`docs/MIROVA_DIVERGENCES.md:2254`).
- **Confirma, contradice o matiza**: **confirma** D25 (cuarta fuente del grupo con «media de los que
  rodean») y **confirma con una segunda fuente** el orden bow tie antes de remuestreo que D17 apoya en
  una sola. **Advertencia**: (d) y (e) son de 2013, previos a SP426.5; la banda 32 y el umbral por
  erupción NO describen el MIROVA operacional (ver H8 de la lectura S139: Fernandina 2025 usa la 31). No
  sirven para cerrar D20 ni para importar un umbral.
- **Confianza** 5 en las citas; 4 en su vigencia para el bow tie (pre-MIROVA NRT). **Gravedad 3.**

### D-07 (gravedad 3). En Campus 2024 el fondo tiene dos descripciones: media de los vecinos (texto) y «medido en el área de Vulcanello» (Tabla 1)

- **Localizador**: `s00445-024-01721-z.pdf`, p. 3 (columna derecha, párrafo sobre la Ec. 2) contra p. 4,
  Tabla 1, fila 6.
- **Citas textuales**: p. 3: «computed from the arithmetic mean of the radiance of the pixels
  surrounding the alerted one(s)». Tabla 1, fila 6 (L_MIRbk): «Radiance in MIR channel of the
  background, measured in the Vulcanello area».
- **Qué dice**: el texto define el fondo local por vecinos; la nota de la tabla del archivo publicado
  S1 dice que la columna L_MIRbk se mide en Vulcanello, que es el píxel de referencia de fondo del
  segundo dataset (p. 4, columna derecha; Fig. 1a, cuadro azul, ~2 km al norte del cono).
- **A qué responde**: a **D25**. El repo usa Campus 2024 p. 3 como la cita VIIRS 375 m del fondo por
  vecinos (`docs/DRIFTS_S17.md:16`, `docs/MIROVA_DETAILED_CITATIONS.md:40-45`) y nunca cita la Tabla 1
  (`grep "Vulcanello"` en `docs/` da 0).
- **Confirma, contradice o matiza**: **matiza** la fuerza de esa cita: la única fuente VIIRS 375 m del
  fondo por vecinos tiene, en su propia tabla, una descripción distinta. Lo más probable es una nota de
  tabla imprecisa (el texto y la ecuación son explícitos), pero no lo puedo decidir desde el PDF.
  **SOSPECHA** sobre cuál describe el archivo S1 real; verificable abriendo la columna 6 del
  suplemento S1 si estuviera disponible.
- **Confianza** 5 en las dos citas; 2 en la interpretación. **Gravedad 3.**

### D-08 (gravedad 2). VIIRS 375 m satura en anomalías intensas, «VRP > 10 MW por píxel»

- **Localizador**: `s00445-022-01523-1.pdf` (Coppola 2022, Sabancaya), p. 5 de 19, sección «Volcanic
  Radiative Power (MODIS)», columna derecha, primer párrafo.
- **Cita textual**: «but suffer from saturation problems for more intense thermal anomalies (i.e.
  VRP > 10 MW per pixel)». El mismo párrafo: «we analyzed the night-time data acquired by the two
  infrared imaging bands of VVIRS [sic], having a spatial resolution of 375 m».
- **Qué dice**: el grupo usa VIIRS 375 m sólo de noche y reconoce saturación por encima de ~10 MW por
  píxel; combina MODIS y VIIRS (2.343 alertas, 0,72 por día, 2012 a 2020).
- **A qué responde**: a **D24** (saturados de MODIS, `docs/MIROVA_DIVERGENCES.md:2244`) por analogía en
  I-band, y a A37 (esquema de saturación VIIRS por bit de calidad). No dice qué hace MIROVA con los
  saturados de VIIRS.
- **Confirma, contradice o matiza**: **confirma** que la saturación I4 es un régimen real en su
  práctica, sin resolver el tratamiento. `grep "10 MW per pixel"` da 0. Irrelevante para el régimen de
  los 11 Tier A salvo paroxismo.
- **Confianza** 5. **Gravedad 2.**

### D-09 (gravedad 2). El dataset VIIRS 375 m de MIROVA no filtra por ángulo cenital ni corrige atmósfera

- **Localizador**: `s00445-024-01721-z.pdf`, p. 4, «Dataset», columna derecha, primer párrafo.
- **Cita textual**: «the data were not corrected atmospherically or filtered by a maximum value of
  zenith; thus, some of the data presented in this work may be partially attenuated»
- **Qué dice**: la serie publicada de La Fossa conserva pasadas oblicuas y nubladas; el archivo S1 trae
  cenit y acimut por fila (Tabla 1, filas 2 y 3).
- **A qué responde**: a **D17** en su eje angular (el ratio nuestro/MIROVA cae con el cenit en VIIRS
  375 m, `docs/MIROVA_DIVERGENCES.md:1899-1905`) y a D14 (sin máscara de nube).
- **Confirma, contradice o matiza**: **confirma** para VIIRS 375 m lo que Laiolo 2026 ya decía para la
  nube (D14 l. 1552). Confirma también que un filtro de cenit no es clon literal. Sin novedad de fondo.
- **Confianza** 5. **Gravedad 2.**

### D-10 (gravedad 2). Error de geolocalización declarado: menos de 0,5 km a nadir

- **Localizador**: `s41598-021-92542-z.pdf`, p. 12, «Methods», «Satellite thermal data», segundo
  párrafo.
- **Cita textual**: «Thermal anomalies detected by MIROVA were geolocated (errors in geolocation are
  less than 0.5 km for nadir acquisition) to discriminate the hotspots sourced by the three distinct
  volcanoes»
- **Qué dice**: el grupo usa la posición de la anomalía para asignarla a uno de tres volcanes a 10 a
  30 km entre sí, con un error declarado <0,5 km a nadir (no dice cuánto en oblicuo).
- **A qué responde**: a D15 (distancia cuantizada, `docs/MIROVA_DIVERGENCES.md:1759`) y a las reglas
  espaciales A61/A70: da una cota del error de posición que el propio grupo acepta.
- **Confirma, contradice o matiza**: **matiza** (dato nuevo, sin conflicto). `grep "0.5 km for nadir"`
  da 0.
- **Confianza** 5. **Gravedad 2.**

### D-11 (gravedad 2). Piton de la Fournaise 2010: método previo a MIROVA con otro fondo, otro umbral y validación manual; no importar

- **Localizador**: `s00445-009-0320-8.pdf`, p. impresa 346 (visor p. 6, «MODIS data»), 347 (visor p. 7,
  Fig. 4 y texto), 349 (visor p. 9, Ec. 4 y «Background temperature...»).
- **Citas textuales**: p. 347: «modified NTI threshold value of −0.86 can now be used for both daytime
  and nighttime images»; «the validity of these alerts were manually confirmed». p. 349: «the
  background temperature around the flow field is represented by the minimum BT12 recorded by the
  alerted pixels». Fig. 6 (p. 349): «Double counting» por bow tie a satzen ~53°.
- **Qué dice**: MODVOLC refinado para una erupción: corrección solar diurna (4,26 % de la radiancia a
  1,6 µm), umbral NTI único −0,86 ajustado a esa erupción y confirmado a mano, fondo = BT12 mínima de
  los alertados, L_flow = ΣL_alert − n·L_bk. Clasifica 8 condiciones de adquisición; nubes por
  inspección visual.
- **A qué responde**: a D25 (otra definición de fondo del grupo) y a D28 (mecanismo del doble conteo
  por bow tie, ilustrado).
- **Confirma, contradice o matiza**: **matiza** sólo como historia: es 2010, anterior a MIROVA; no
  describe el algoritmo que clonamos. Útil como ilustración de D28, no como parámetro. `grep "-0.86"` y
  `"minimum BT12"` dan 0.
- **Confianza** 5 en las citas. **Gravedad 2.**

### D-12 (gravedad 1). Agregaciones de los casos de estudio: máximo diario y máximo mensual contra la nube

- **Localizadores**: `s00445-025-01932-y.pdf` p. 9 **[capa de texto]**: «For each individual timeseries
  we first calculated the daily maximum VRP values. This step minimize potential underestimation due to
  cloud-contamination». `feart-11-1040199.pdf` (Campion y Coppola 2023), p. 3, §2.2, columna derecha:
  «the VRP values that are used in this study are the maximum values recorded each month».
- **Qué dice**: para series largas el grupo toma máximos (diarios o mensuales) para compensar la
  atenuación por nube.
- **A qué responde**: a cómo comparar magnitudes contra series de papers (A10, A90): una serie de caso de
  estudio puede ser de máximos, no de pasadas.
- **Confirma, contradice o matiza**: **matiza** el uso de figuras de papers como vara. No toca detección.
- **Confianza** 5 (Campion); 4 (Laiolo, capa de texto). **Gravedad 1.**

### D-13 (gravedad 1). Inconsistencias menores dentro de Laiolo 2026 y entre papers

- **Localizadores**: `s00445-025-01932-y.pdf` p. 8, texto columna derecha: «allowing to measure a VRP of
  3577 MW»; leyenda de la Fig. 5 (p. 8): «the anomaly produces a VRP of 3700 MW»; p. 9 **[capa de
  texto]**: «(3500 MW)». La Fig. 5a se rotula «MODIS Band 21» (radiancia a 3,9 µm) para ese paroxismo.
  Umbral de temperatura del emisor: «> 200 °C» en `s41598-021-92542-z.pdf` p. 12 y en
  `s00445-022-01523-1.pdf` p. 5, frente a «higher than 600 K» en Laiolo 2026 p. 4 y Galetto 2025 p. 3
  (§3.2) y «between 600 and 1500 K» en Coppola 2016 p. 8.
- **Qué dice**: tres valores para un mismo VRP; y dos descripciones del rango de validez del método
  MIR. La Fig. 5a con banda 21 en un paroxismo es coherente con SP426.5 (la 21 donde la 22 satura) y no
  dice nada sobre la banda primaria del régimen normal.
- **A qué responde**: a D21 (no la mueve) y a la higiene de citas (A35).
- **Confirma, contradice o matiza**: **matiza** (erratas del paper, nada del repo).
- **Confianza** 5. **Gravedad 1.**

### D-14 (gravedad 1). Confirmaciones sin novedad

- `1-s2.0-S0377027315003716-main.pdf` p. impresa 8 (visor p. 3), Ec. (1): «VRP_PIX = 18.9 × A_PIX ×
  (L4alert − L4bk)» con A_PIX = 1 km² del píxel remuestreado, y suma sobre el cúmulo. Confirma el
  coeficiente MODIS de `CLAUDE.md` y la suma por píxel. Mismo paper p. 11, leyenda Fig. 3b: el fondo MIR
  graficado es «the most radiant non-alerted pixel» sobre la cumbre (diagnóstico, no el fondo del VRP).
- `s00445-024-01721-z.pdf` p. 4, Ec. (3) y texto: k_MIR = 18,0 para I4 y A_pix = 140.625 m². Confirma
  `CLAUDE.md` (ya citado en `docs/MIROVA_DETAILED_CITATIONS.md:349`).
- `1-s2.0-S0377027322002384-main.pdf` (Morelli 2022) p. 8, §3.2: «In this study we use MODIS nighttime
  data (2 nighttime images/ day), elaborated by MIROVA algorithm»; 1.976 anomalías en Yasur 2008-2019.
  Sólo noche; sin parámetros.
- `s00445-022-01523-1.pdf` p. 5: MIROVA «is a fully automatic hot-spot volcano detection system».
- `JGR ... Galetto ...pdf` p. 3, §3.2: MIROVA automático, MODIS desde 2000 y VIIRS desde 2012; p. 5 y
  12: sin parámetros de detección.
- Confianza 5. Gravedad 1.

---

## 3. VERIFICADO LIMPIO

Qué se buscó en las páginas renderizadas y leídas (lista en la tabla del §1) y **no estaba**:

| Se buscó | Resultado | Dónde se miró |
|---|---|---|
| Valores de K1, C1, C2 o N·σ de los Tests 1, 2 y 3 | Ausentes. Ningún caso de estudio repite ni modifica la Tabla 1 de SP426.5; todos remiten a Coppola 2016a | Los 11, páginas de método listadas |
| Conectiva de los Tests 2 y 3 (`min`/`max`, `or`/`and`) | Ausente. Ninguno la escribe | ídem |
| Condición de temperatura dentro de los Tests (tipo `BT > T_bg + 3 K`, D22) | Ausente | ídem |
| Ventana o anillo de fondo para mu y sigma (D26), refit iterativo (D29) | Ausentes | ídem |
| Uso de VIIRS 750 m (M13) | Ninguno lo usa. Campus 2024 p. 3 describe las M-bands y declara usar sólo I4 e I5 | Campus 2024 p. 3; Sabancaya p. 5; Laiolo 2026 p. 4 |
| Uso diurno de VIIRS o de la Tabla 1 diurna (D27) | Ninguno de los que dan detalle usa día; Sabancaya, Campus 2024, Morelli y KVG declaran sólo noche | Sabancaya p. 5; Campus 2024 p. 4 y 5; Morelli p. 8; KVG p. 12 |
| Máscara automática de nube o filtro de cenit en MIROVA | Negado explícitamente (Laiolo 2026 p. 4; Campus 2024 p. 4); donde hay limpieza, es manual (D-03) | ídem |
| Tratamiento de píxeles saturados (D24) | Ausente; sólo se reconoce la saturación VIIRS (D-08) | Sabancaya p. 5 |
| Test 1 como camino propio (D23) | Ausente | Los 11 |
| Banda 22 frente a 21 como primaria (D21) | Ausente como definición; sólo «Band 21 or 22» (Campion p. 3) y la figura de Laiolo 2026 p. 8 | Campion p. 3; Laiolo 2026 p. 8 |

Barridos sólo por capa de texto (sin render, frases sin operadores): Laiolo 2026 p. 9 y 18; Piton p. 10 y
14; Vanuatu p. 12; KVG p. 8; Sabancaya p. 9; Galetto p. 10 y 13. Nada con parámetros de detección.

**Cobertura NO hecha, para que nadie la tome por limpia**: Coppola 2013 p. 1 a 7 y 9 a 10 (cuerpo sobre
densidad radiante); Sabancaya p. 6 a 19 (figuras de series térmicas, Fig. 3); Laiolo 2026 p. 6, 7 y 9 a
15 (tablas de estadísticas por tipo de evento, Tabla 1); Campus 2024 p. 6 y 7; Vanuatu p. 1, 2, 4, 7, 9 a
12 y 14; Santa Ana p. 1, 5, 8 y 10; KVG p. 1, 2, 5, 7 a 11 y 14 a 16; Campion p. 1, 2 y 4 a 16; Galetto
p. 1, 2, 6 a 11, 13 y 14; Piton p. 1 a 3, 8 y 10 a 16; Morelli salvo p. 8. Se eligió por palabras clave
(ver Método); una tabla con parámetros sin esas palabras no se habría visto.
