# S141, lectura de papers MIROVA, segunda pasada: LECTOR C

Lector: subagente C, 2026-09-14, rama `main`. Lectura read-only: no se modificó ningún archivo del repo
salvo este informe; no se tocó git.

Renders (fuera del repo, no se commitean, derechos de autor):
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\0a44fda0-e659-4f4d-80af-9f8577f14092\scratchpad\render_C\`
(PyMuPDF, 150 dpi, archivo `<clave>_pNN.png`, NN = página del visor PDF). En los cuatro PDF la página
impresa coincide con la del visor (verificado en el folio de cada render mirado), así que se da una sola.

## Qué se leyó

| clave | PDF en `documentacion\` | título y autores (p. 1) | ¿MIROVA? |
|---|---|---|---|
| M20 | `remotesensing-12-00820-v4.pdf` (32 p.) | Massimetti, Coppola, Laiolo, Valade, Cigolini, Ripepe 2020, *Volcanic Hot-Spot Detection Using SENTINEL-2: A Comparison with MODIS-MIROVA Thermal Data Series* (el título lleva un signo tipográfico que aquí va como guion simple), Remote Sens. 12, 820 | Sí (Torino y Firenze; Valade TU Berlin/GFZ como coautor externo) |
| A24 | `Aveni_2024_TIRVolcH_RSE.pdf` (26 p.) | Aveni, Laiolo, Campus, Massimetti, Coppola 2024, *TIRVolcH*, RSE 315, 114388 | Sí (Sapienza y Torino, todos del grupo) |
| A25 | `Geophysical Research Letters - 2025 - Aveni - ...pdf` (13 p.) | Aveni, Pailot-Bonnétat, Rouwet, Harris, Coppola 2025, GRL 52, e2024GL113324 | Mixto: Sapienza y Torino dirigen; Clermont (Harris, Pailot-Bonnétat) e **INGV Bologna** (Rouwet) coautores |
| R17 | `remotesensing-17-02543-v2.pdf` (21 p.) | Aveni, Ganci, Harris, Coppola 2025, *Tracking Lava Flow Cooling from Space*, Remote Sens. 17, 2543 | Mixto: Sapienza y Torino dirigen; **Ganci es INGV Catania** (Osservatorio Etneo), grupo que A9 declara NO MIROVA |

**Páginas renderizadas** (todas): M20 1-3, 5-9, 13-16, 20-28; A24 1-12, 14-17, 19, 20; A25 1-9; R17 1-15.
**Páginas renderizadas y miradas en imagen** (las que sostienen citas de este informe): M20 p. 15 y 21;
A24 p. 3, 5, 11, 14, 20; A25 p. 4 y 5; R17 p. 6 y 7. El resto se inventarió por la capa de texto (sólo
prosa, nunca operadores ni números de fórmulas).

**Qué NO cubrí**: los materiales suplementarios (S1 a S5 de A24, S1 de A25 y R17) no están en
`documentacion\`; tablas de resultados de R17 (p. 9 a 21, volúmenes de lava, fuera del objeto); figuras
12 a 15 de M20 (sólo leídas por caption); las secciones 6.1.3 de A24 (La Palma) en imagen. No verifiqué
nada contra datos del pipeline: los números del repo que cito son los que ya están escritos en sus docs.

**Premisa del encargo que no se sostiene** (confianza 5): M20 **no es** «Massimetti et al. 2020, validación
VIIRS». Es un detector Sentinel-2 SWIR (20 m) comparado contra la serie **MODIS** de MIROVA, 2016-2019.
No contiene umbrales VIIRS ni validación VIIRS. Lo que sí trae de útil está en los hallazgos G4-1 y G3-3.

---

## Hallazgos por gravedad

### G4-1. MIROVA filtra MODIS por ángulo cenital > 40° en su propia comparación publicada; nosotros no filtramos y el catálogo no lo tiene como divergencia

- **Localizador**: M20, p. 15, §3.2, 3.er párrafo; y p. 21, §4, 1.er párrafo.
- **Cita** (p. 15): «The MODIS dataset is filtered to exclude images with poor viewing geometry (Zenith > 40°)».
  (p. 21): «maximum VRP recorded by MODIS images (filtered data with Zenith angle < 40°) in a time window of ±24 h».
- **Qué dice**: el grupo, al comparar MIROVA contra otra fuente, descarta las pasadas MODIS con cenit
  > 40° y remite a Coppola 2016a ([25]) para el motivo. Es la tercera fuente del grupo con el mismo corte:
  `docs/AUDIT_S128.md:59-66` ya lo había citado de la tesis de Massimetti (cap. 3 > 40°, cap. 4 < 50°) y
  concluyó que «no filtramos por cenit en ninguna parte» (`docs/AUDIT_S128.md:68`). Este informe verifica
  que eso sigue cierto hoy: `grep -i zenith` en `pipeline/`, `scripts/run_pipeline.py` y `pipeline/store.py`
  sólo encuentra lectura del ángulo y corrección de área, ningún descarte.
- **A qué responde**: al gap de magnitud (~0,7) y a D17. `docs/s130/GRADIENTE_CENITAL.md:52` mide el ratio
  VIIRS375 en 0,740 cerca del nadir y 0,253 más allá de 50°, con el bin oblicuo como el más poblado
  (1.144 de 2.767 pares). Si el propio grupo excluye esas pasadas cuando valida, **una mediana global que
  las incluye mide un régimen que MIROVA no usa para validar**. En `docs/MIROVA_DIVERGENCES.md` no hay
  ninguna entrada D sobre filtro cenital (el único `zenith/cenit` está en la nota S130 de D17, l. 1903).
- **Veredicto**: **confirma** `docs/AUDIT_S128.md:59-68` con un paper publicado (no sólo la tesis) y
  **matiza** la lectura de `docs/s130/GRADIENTE_CENITAL.md:52-63`: la comparación nuestra contra MIROVA
  debería reportarse al menos también con corte ≤ 40° (MODIS) antes de atribuir el 0,7 al mecanismo.
- **SOSPECHA** (no verificada): que MIROVA aplique ese corte **en el NRT publicado**. El texto dice
  «dataset is filtered» en un análisis; S130 encontró pares MIROVA en el bin 50°+, lo que sugiere que el NRT
  sí publica pasadas oblicuas. Es un filtro de análisis, no necesariamente de producción. Candidata a
  pregunta para Coppola.
- **Confianza** 5 en la cita, 3 en su alcance operacional. **Gravedad 4.**

### G4-2. En el TIR del grupo (Aveni 2024 y 2025) el corte cenital es > 50°, y A24 dice que en montaña empinada se sugiere > 30°

- **Localizador**: A24 p. 14, Tabla 2, nota **; A24 p. 20, §7.3, 1.er párrafo (columna izquierda); R17 p. 7, §2.3.2, último párrafo.
- **Cita** (A24 Tabla 2): «we discarded all alerted scenes acquired with a zenith angle >50°».
  (A24 §7.3): «is common practice to discard scenes acquired with a zenith angle >50° ... especially in steep mountainous regions, scenes >30° should be rejected».
  (R17 §2.3.2): «scenes acquired with zenith angles > 50° were discarded».
- **Qué dice**: los productos VIIRS 375 m del grupo (TIRVolcH y VRP_TIR) descartan escenas con cenit > 50°.
  A24 §7.3 da el mecanismo físico: a cenit alto las anomalías dentro de bordes de cráter empinados quedan
  enmascaradas y la anomalía proyectada se reparte en varios píxeles. Y cita autores que en montaña empinada
  rechazan desde 30°. Los once Tier A son estratovolcanes andinos empinados.
- **A qué responde**: al mismo frente que G4-1, ahora para VIIRS 375 m. Explica una causa **física**
  (enmascaramiento por el borde del cráter, dispersión) del sub-reporte oblicuo que no es el remuestreo.
  `docs/s130/GRADIENTE_CENITAL.md:60-63` atribuye la caída sólo al área del píxel y al remuestreo (Coppola 2014).
- **Veredicto**: **matiza** `docs/s130/GRADIENTE_CENITAL.md:60-63`. No refuta el remuestreo, agrega un
  segundo mecanismo que un regrid no cura (lo que el borde del cráter tapa no se recupera remuestreando).
- **Confianza** 5 (leído en imagen). **Gravedad 4** (condiciona el diseño del A/B de D17: sin corte cenital,
  el brazo de regrid se evalúa contra un sub-reporte que en parte es de oclusión).

### G3-1. La grilla VIIRS 375 m de MIROVA es 134 × 134 UTM centrada en la cumbre GVP, dicho por el grupo «as per MIROVA workflow»

- **Localizador**: A24 p. 5, §3.2 «Input data», 1.er párrafo (columna derecha).
- **Cita**: «The original granules, as per MIROVA workflow, are resampled to a regular 134 × 134 UTM grid centred on the volcano summit according to the coordinates provided by the Global Volcanism Program».
- **Qué dice**: VIIRS I5 procesado por MIROVA se remuestrea a 134 × 134 celdas UTM (unos 2.500 km²) centradas
  en la cumbre GVP, y la base guarda el ángulo cenital de cada pasada.
- **A qué responde**: D17 y D28 (remuestreo, centro de grilla) y pregunta 6 del correo.
- **Veredicto**: **confirma** `docs/MIROVA_DIVERGENCES.md:1815` (grilla 134 × 134 deducida del GeoTIFF real) y
  `docs/AUDIT_S128.md:169`, con una fuente escrita del grupo distinta de Fernandina 2025 (que es la citada en
  la nota S140 de D17, l. 1896). Para VIIRS 375 m la grilla ya no es deducción: está publicada.
- **Confianza** 5. **Gravedad 3** (no cambia el estado de D17, le da la cita que faltaba para 375 m).

### G3-2. El grupo separa el centro de la grilla (GVP) de las coordenadas donde busca el calor (cumbre o boca revisada)

- **Localizador**: A24 p. 6, §4.2.1 «Ancillary data», 1.er ítem (sólo capa de texto de prosa; la p. 6 está renderizada).
- **Cita**: «Coordinates of Interest: the revised location of the volcano's summit (or active vent) to compensate for any offset in the GVP list».
- **Qué dice**: la escena se centra en GVP (G3-1) pero los ROI de mayor sensibilidad se centran en unas
  coordenadas corregidas hacia la boca activa.
- **A qué responde**: D17 (centro de grilla) y la regla A63.
- **Veredicto**: **confirma** la separación de roles de `pipeline/geo_utils.py:3-13` (grid center vs detection
  anchor). Ojo con el alcance: es TIRVolcH, no SP426.5.
- **Confianza** 4 (prosa leída en capa de texto, sin operadores en juego). **Gravedad 3.**

### G3-3. El fondo del VRP en los productos VIIRS del grupo sale de los píxeles vecinos NO alertados, interpolados; no de una mediana de anillo

- **Localizador**: A24 p. 11, §4.3.5, 3.er párrafo (columna izquierda), y Eq. 5 con su definición (columna
  derecha); R17 p. 6, §2.3.1, último tercio del párrafo; A25 p. 5, 1.a línea.
- **Cita** (A24): «The BTbg is computed iteratively by removing the Candidate Alerts from the scene and interpolating the gaps using a bi-cubic interpolation».
  (R17): «Hotspot-contaminated pixels are removed from the scene to compute the theoretical background temperature».
- **Qué dice**: en el camino TIR del grupo, cada píxel alertado tiene su propio fondo, interpolado desde los
  vecinos sin alerta. Nunca una mediana regional.
- **A qué responde**: D25 (fondo = mediana de anillo de 5 a 25 km).
- **Veredicto**: **confirma el patrón** de D25 (`docs/MIROVA_DIVERGENCES.md:2254-2264`) con un tercer y cuarto
  testimonio del grupo, **pero en TIR y en otro algoritmo**: no es la Eq. 6 MIR de SP426.5. Sirve como
  evidencia de práctica del grupo, no como cita literal para el VRP MIR.
- **Confianza** 5 en la cita, 3 en la transferencia a MIR. **Gravedad 3.**

### G3-4. VIIRS I-band a borde de barrido mide 0,75 km, no «mucho más terreno», y la agregación mantiene la exactitud hasta ~55°

- **Localizador**: A24 p. 3, Tabla 1, filas «Pixel resolution at nadir» y «at the edge»; A24 p. 20, §7.3, 1.a oración.
- **Cita** (Tabla 1): «Pixel resolution at nadir (km) 0.375 ... Pixel resolution at the edge (km) 0.75».
  (§7.3): «The aggregation function implemented on VIIRS sensors ... allows improved accuracy even for scenes acquired with a zenith angle up to ~55°».
- **Qué dice**: por la agregación a bordo, el píxel I5 crece a lo sumo al doble en la dirección de barrido
  (0,375 a 0,75 km) y el grupo considera exactas las escenas hasta ~55°.
- **A qué responde**: a la explicación física de `docs/s130/GRADIENTE_CENITAL.md:60` («Un píxel VIIRS a 50° de
  nadir cubre mucho más terreno que uno a nadir») y al gap de magnitud.
- **Veredicto**: **matiza**. Con un crecimiento de área acotado (del orden de 2× en barrido; a lo largo de la
  traza no lo da la tabla), un área nadir fija explica sólo parte de una caída de 2,7× (0,740 a 0,253).
  **SOSPECHA**: que el resto sea la oclusión de G4-2 u otro efecto; no lo medí. `pipeline/scan_geometry.py:26`
  y `:200` ya documentan la agregación bow-tie, así que el código lo sabe; el doc de S130 no lo pondera.
- **Confianza** 4 (tabla leída en imagen; la inferencia cuantitativa es mía). **Gravedad 3.**

### G2-1. MIROVA declara para su VRP MODIS un error estándar de 30 % y sensibilidad sólo a superficies > 500 K

- **Localizador**: M20 p. 15, §3.2, 3.er párrafo, penúltimas oraciones.
- **Cita**: «The MIR method [70] applied by MIROVA to MODIS images detects the thermal flow radiated from the surfaces with T > 500 K solely and return the VRP with a standard error of 30%».
- **Qué dice**: el grupo fija el error del VRP MODIS en 30 % y el umbral de validez del método MIR en 500 K
  (Aveni 2025, A25 p. 3, lo pone en ~600 K: dos cifras del mismo grupo).
- **A qué responde**: gap de magnitud (0,7) y tolerancias de paridad.
- **Veredicto**: **matiza**. Un error estándar de 30 % es dispersión por medición; **no** autoriza leer un sesgo
  sistemático de 0,7 como «dentro del error». Útil como banda para pre-registrar criterios del A/B. No lo
  encontré citado en `docs/` (grep «standard error of 30» y «T > 500 K» sin coincidencias en ese sentido).
- **Confianza** 5. **Gravedad 2.**

### G2-2. TIRVolcH exige BT del candidato > BT de fondo + 0,5 a 1 K; es condición de temperatura, pero de un detector TIR, y no justifica los 3 K de D22

- **Localizador**: A24 p. 11, §4.3.5, 2.º párrafo, «[test 11]».
- **Cita**: «ΔTbg takes one of the following values: 0.5 K (for VSROI, ROI1, ROI2), 0.75 K (for ROI3) and 1 K (for ROI4)».
- **Qué dice**: en TIRVolcH hay una compuerta de temperatura sobre el fondo, graduada por distancia a la cumbre.
- **A qué responde**: D22 (`bt > t_bg + 3 K` dentro de los Tests 2 y 3, `docs/MIROVA_DIVERGENCES.md:2205-2230`).
- **Veredicto**: **no cambia D22**. Es otro algoritmo (TIR, una banda), el umbral es 0,5 a 1 K sobre un fondo
  interpolado sin alertas, y SP426.5 sigue sin condición de temperatura. Lo registro para que nadie lo use
  como respaldo de los 3 K: el orden de magnitud es otro y el fondo también.
- **Confianza** 5. **Gravedad 2.**

### G2-3. El archivo VIIRS nocturno de MIROVA: ~10.000 adquisiciones por volcán 2012-2023

- **Localizador**: A24 p. 20, §7.5, último renglón de la columna izquierda y 1.o de la derecha.
- **Cita**: «Considering that the MIROVA VIIRS archive contains ~10,000 nighttime VIIRS acquisitions (2012-2023), for a total of 1.7956 × 10^8 pixels, per volcano».
- **Qué dice**: 10.000 × 134² = 1,7956 × 10^8, coherente con la grilla de G3-1. Da el tamaño del archivo nocturno 375 m por volcán.
- **A qué responde**: pregunta 9 del correo (pocas entradas VIIRS 750 m en el archivo) sólo de forma lateral:
  confirma que el archivo VIIRS existe y es denso en 375 m; no dice nada de 750 m.
- **Veredicto**: dato de contexto, no cierra nada. **Confianza** 5. **Gravedad 2.**

### G1-1. Dos citas de página desplazadas en el repo

- **Localizador**: A24 p. 11, Eq. (5) (columna derecha); A25 p. 5, pie de la Figura 2, panel (b).
- **Cita** (A24): «ΦRad = Σ σ • ε • (BT⁴alert,i − BT⁴bg,i) • A ... namely 140,625 m² for VIIRS I5 pixels».
  (A25): «optimal kTIR has a value of 60.17 μm · sr».
- **Qué dice y a qué responde**:
  - `docs/DRIFTS_S17.md:83` dice «Aveni 2024 RSE Eq.5 **p.12**»: la Eq. 5 está en la **p. 11**. El contenido
    (Stefan-Boltzmann puro, área fija 140.625 m²) **confirma** `CLAUDE.md:102-105`.
  - `pipeline/vrptir.py:10` dice «60.17 μm·sr (verbatim **p.4**, Fig.2b)»: la Ec. 8 está en p. 4, pero el 60,17
    impreso y la Fig. 2b están en la **p. 5**. `docs/s129/PAPERS_AVENI2025_GRL_TIR.md` ya lo da bien (p. 5).
  - Coeficientes de la Ec. 8 leídos en imagen (A25 p. 4): 1,0575, −14,3139, 85,4239. **Confirman**
    `pipeline/vrptir.py:49-51`. Evaluada en 11,45 µm da 60,17.
- **Confianza** 5. **Gravedad 1.**

### G1-2. El área de píxel del VRP VIIRS del grupo es la nominal fija

- **Localizador**: A24 p. 11, definición bajo la Eq. (5).
- **Cita**: «A is the pixel surface area, namely 140,625 m² for VIIRS I5 pixels».
- **Veredicto**: **confirma** el área nadir fija de 375 m (`CLAUDE.md`, sección Reglas científicas; A66/A67),
  en un producto del grupo que además remuestrea (G3-1): área fija y remuestreo van juntos, como dice la
  salvedad S138 de A66. **Confianza** 5. **Gravedad 1.**

---

## VERIFICADO LIMPIO (buscado y no estaba)

- **Umbrales VIIRS 375 o 750 m de los Tests SP426.5 (K1, C1, C2, N·σ)**: no aparecen en ninguno de los cuatro.
  M20 es SWIR y MODIS; A24, A25 y R17 son TIR de una banda. Páginas: M20 1-28 (texto), A24 1-20, A25 1-9, R17 1-15.
- **Coeficiente de Wooster MIR (18,9 / 19,7 / 18,0) o la fórmula de α de Coppola 2025**: no está. A25 p. 3
  menciona el método MIR sin coeficientes; M20 p. 15 sólo el 30 % y los 500 K.
- **Conectiva min/max de los Tests 2 y 3 (pregunta 1), banda 21/22 (pregunta 2), K1 como camino propio
  (pregunta 5), bow tie MODIS (pregunta 6), refit a 3σ (pregunta 7), columna «class» OSF (pregunta 8),
  distancia publicada (pregunta 11), rótulo del ETI (pregunta 12)**: ninguno de los cuatro los trata.
- **Validación numérica de la magnitud VRP VIIRS contra MIROVA MIR**: no existe en estos cuatro. A24 valida
  su ΦRad contra ASTER (Agung, p. 15: R² 0,92, pendiente 0,75) y contra terreno (Vulcano), no contra el VRP MIR.
- **Piso de detección en MW**: ninguno fija uno. A24 da sólo 0,5 K sobre el fondo (p. 3 y p. 11) y un rango
  observado de ~0,5 MW a ~3 GW (p. 20, §8).
- **Contradicciones de A25 frente a `docs/s129/PAPERS_AVENI2025_GRL_TIR.md`**: ninguna. Ec. 5, 8, 9, el
  60,17, el ±35 %, el rango 300-600 K, el ruido de fondo 2,5 K (A25 p. 4) y el uso nocturno coinciden con lo
  que ese doc cita. Único detalle nuevo: las simulaciones de fondo van de 273,15 a 313,15 K (A25 p. 4) y la
  Fig. 1 usa un fondo fijo de 285 K; nuestro rango nocturno cae por debajo, como ya advirtió el doc de S129
  (l. 66). El pie de la Fig. 2 de A25 dice «Equation 1 (RPPixel)» donde debería decir Ec. 5: errata del paper, sin efecto.
- **Algo sobre volcanes chilenos con parámetros**: M20 incluye Villarrica y Láscar (p. 18-23) sólo como series
  S2Pix frente a VRP (Villarrica 10^7 a 10^8 W, Láscar < 10^7 W en 2016-2017; leído en la capa de texto de
  p. 20, donde los exponentes pierden el superíndice, no en imagen), sin umbrales ni fondo.
