# P2 (S159): relectura de los papers de la adaptación a VIIRS con el código de MIROVA como llave

Ola 1 del plan posterior a la auditoría S158, frente P. Sólo lectura: no toqué `pipeline/`, `data/`, `frontend/` ni git.
Todo lo que escribí está en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\p2\`.

**Cómo se citó.** Cada cita a un PDF se verificó renderizando la página a 200 dpi (PNG en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\p2\png\`, abiertos uno por uno). La capa de texto se usó sólo para
ubicar (`ubicar.py`). Código de MIROVA: `MIROVA_VIIRS750_hotspot_detection.m` = **H**, `MIROVA_VIIRS750_VRP.m` = **V**,
en `C:\vrp-trabajo\s159-pruebas\experiments\_s158_d17_diseno\osf_codigo_mirova\`, leídos enteros en esta sesión.

**Fuentes leídas** (todas en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\`):

| sigla | fuente | archivo | sensor que trata |
|---|---|---|---|
| CA22 | Campus et al. 2022, Sensors 22:1713 | `campus2022_sensors_22_1713.pdf` (24 p.) | **sólo VIIRS M-band** (p. 6: «In this work we used M13 and M15») |
| CA24 | Campus et al. 2024, Bull. Volcanol. 86:25 | `s00445-024-01721-z.pdf` (7 p.). **El PDF sí existe**: el bloque común decía que sólo había `.txt` | VIIRS 375 (I4, I5) |
| MT | Tesis de Massimetti (UniTo, ciclo XXXIV) | `THESIS_MASSIMETTI.pdf` (204 p.) | S2/L8; VIIRS sólo como dato |
| MA24 | Massimetti et al. 2024, JGR Solid Earth 129 | `nuevos\JGR Solid Earth - 2024 - Massimetti - Thermal Emissions ....pdf` | MODIS y VIIRS como insumo |
| C26 | Coppola et al. 2026, Scientific Data (in press) | `Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf` | los tres (ayuda para (b) y (c)) |
| SAB | Coppola et al. 2022, Bull. Volcanol. (Sabancaya) | `s00445-022-01523-1.pdf` | cita de dónde sale VIIRS 375 |
| GEO | VIIRS Geolocation ATBD 2014 | `VIIRS_Geolocation_ATBD_2014.pdf` | zonas de agregación |
| RAD | JPSS VIIRS SDR Radiometric ATBD Rev C | `JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf` | agregación de M13 |

`The_Transition_from_MODIS_to_VIIRS_for_Global_Volc.md` es CA22 convertido a texto (mismo título, autores y resumen):
no es una fuente aparte. `massimetti2024_stromboli.md` es MA24. Las páginas de C26 se dan por índice del PDF, porque la
versión «in press» no imprime número de página.

---

## 1. Hallazgos, de lo más grave a lo menos grave

### H1. Para VIIRS 375 no hay ningún paper que describa la detección: «manda el paper» no tiene paper
- **ARCHIVO:LÍNEA**: `C:\vrp-trabajo\s159-pruebas\docs\MISSION.md:130` («para MODIS y VIIRS 375 manda el paper hasta tener
  su código o una medición»); `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:179-180` («Para MODIS y VIIRS 375 manda el paper,
  que renderizado dice «eight neighbouring pixels» (Coppola 2016a p. 5)»).
- **QUÉ PASA**: la cadena de citas de MIROVA para VIIRS 375 termina en un paper que no trata VIIRS 375. C26 (índice 5,
  párrafo que empieza «Further details») remite los detalles de VIIRS a su ref. 7, y la ref. 7 es CA22 (índice 22,
  lista de referencias). CA22 usa sólo M13 y M15 (p. 6, §3.1, penúltimo párrafo) y deja el 375 m como trabajo futuro:
  «the application of the MIROVA algorithm to VIIRS data at 375 m resolution has all the potential...» (p. 19, último
  párrafo de §6). SAB (p. 5 del PDF, columna derecha) atribuye el VIIRS 375 a «Campus et al., 2021», que es un póster.
  CA24, el único paper con método de VIIRS 375, dice de la detección sólo «spectral and spatial filters» (p. 3,
  columna derecha). Ninguna de mis fuentes trae K1, C1, C2, la ventana del contraste, la regresión ni el segundo pase
  para VIIRS 375 (búsqueda de `NTI|ETI|neighbo|second pass|K1` en CA22 y CA24: cero coincidencias; MT y MA24 no
  describen la detección). Lo que hoy gobierna VIIRS 375 «por el paper» es Coppola 2016a, que es de MODIS, por doble
  traslado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. El riesgo es de decisión: un cambio en VIIRS 375 (8 contra 9 vecinos, K1,
  mínimo de dNTI fuera de la cumbre) puede quedar bloqueado o justificado por una cita que no existe. Que el código de
  VIIRS 750 sea peor guía para VIIRS 375 que un paper de MODIS no está escrito en ningún lado.
- **CÓMO REPRODUCIRLO**: `python C:\vrp-trabajo\s159-pruebas\experiments\_s159\p2\ubicar.py campus2022_sensors_22_1713.pdf "NTI|ETI|neighbo|K1|375"`
  desde `documentacion\`; PNG `campus2022_p6.png`, `campus2022_p19b.png`, `coppola2026_pidx5.png`, `coppola2022_sabancaya_pidx5.png`.
- **CONFIANZA**: CONFIRMADO para las fuentes leídas. No leí Coppola et al. 2022 Front. Earth Sci. 10:964372 (primer uso
  de VIIRS 375 por MIROVA, ref. [103] de CA22): **no está en `documentacion\`** (búsqueda por `964372`: cero).
- **GRAVEDAD**: 3. VIIRS 375 es el sensor que lleva la mayor parte de las alertas, y su regla de autoridad descansa en
  una cita vacía.

### H2. «MIR solo nocturno» sigue como regla científica no negociable, sin marca, contra el código y contra CA22
- **ARCHIVO:LÍNEA**: `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:183` («**MIR solo nocturno** (contaminación solar diurna).»),
  dentro de «Reglas científicas (no negociables)».
- **QUÉ PASA**: MIROVA trata el día como un caso más del mismo algoritmo, con umbrales más altos: el código trae la rama
  diurna completa (H:173-199: K1 -0,5; 15σ; mínimos 0,02 en las tres regiones) y rechaza la escena entera si el ángulo
  de reflejo especular es menor de 12° (H:83-89). CA22 lo dice con palabras: procesa día y noche (p. 16, §5, 2.º párrafo)
  y la caída diurna se debe a «the higher thresholds of the daytime algorithm specifically settled to avoid false
  alerts due to the contribution of solar heating and reflection» (p. 17, párrafo «Nighttime vs daytime data»).
  `docs/MIROVA_DIVERGENCES.md:2920` ya lo corrigió (marca S151), pero la corrección no bajó a CLAUDE.md, que es lo que
  cada sesión lee primero (A113).
- **CÓMO SE VE EN EL DASHBOARD**: las alertas diurnas que MIROVA publica no tienen contraparte nuestra (según la marca
  S151 del catálogo, 40 pasadas protegidas diurnas usables; ese número no lo medí yo).
- **CÓMO REPRODUCIRLO**: `sed -n 183p C:\vrp-trabajo\s159-pruebas\CLAUDE.md`; H:173-199; PNG `campus2022_p16.png`, `campus2022_p17.png`.
- **CONFIANZA**: CONFIRMADO (texto, código y página leídos). La decisión de abrir el día es D-10, de Nicolás.
- **GRAVEDAD**: 3. Una regla marcada «no negociable» bloquea justo la decisión que está pendiente.

### H3. El escalón del OSF en VIIRS 750 está en 50,0° exactos, no en el límite de la zona de agregación (52,6°)
- **SCRIPT:SALIDA**: `escalon_fino.py` → `escalon_fino_salida.txt`; `zona_agregacion_cenit.py` → `zona_agregacion_cenit_salida.txt`;
  `escalon_cortes_npix.py` → `escalon_cortes_npix_salida.txt`; `escalon_npix.py` → `escalon_npix_salida.txt`.
- **QUÉ PASA**: la sospecha del coordinador era que las filas de VIIRS 750 que no cumplen la fórmula del código venían de
  la zona de agregación del borde. El instrumento VIIRS cambia de agregación 2:1 a 1:1 a 44,680° de ángulo de barrido
  (GEO p. 14 impresa, índice 36, PNG `viirs_geoloc_atbd_pidx36.png`), que desde 824 km de altura (CA22 Tabla 1) es
  **52,6° de cenit** en el suelo (52,7° con 834 km). Medido sobre todo el OSF v2.5 (615.470 filas, 2000-02 a 2025-12):
  - **ninguna** fila V750 bajo 50° deja de cumplir (máximo cenit de las que fallan bajo 50: ninguno; mínimo cenit de las
    que fallan: 50,013°). En tramos de 0,25° el cumplimiento cae de 1,0000 (49,75-50,0, n 224) a 0,8035 (50,0-50,25,
    n 229) y queda entre 0,59 y 0,74 de ahí a 54°, sin un segundo salto en 52,6°. El corte es un 50 escrito, no la
    zona de agregación;
  - la falla crece **suave** con Npix (Npix 1 a 3: 100 %; 4: 96,9 %; 8: 90,1 %; 30: 29,2 %) y **no** salta en los
    cortes de la dilatación del fondo (V:68-74, npix 4|5 y 30|31). Mi hipótesis de que el escalón fuera el fondo quedó
    refutada por mi propio dato;
  - de día cumple 36 a 40 % y de noche 83 a 84 % (sobre 50°, por signo del azimut);
  - en las que fallan, VRP / (ΔL × k) es **siempre menor que 1** (máximo 0,951, mediana 0,508, mínimo 0,027).
  La única pista física que encontré está en RAD p. 102 (PNG `atbd_radcal_pidx134.png`): **M13 es la única banda
  térmica de doble ganancia que se agrega en tierra**, en radiancia; I4 se agrega a bordo. Eso es exclusivo de VIIRS
  750, igual que el escalón, pero el corte de 50,0° no coincide con ningún límite de zona. Lectura propia (SOSPECHA):
  sobre 50° el VRP de MIROVA en VIIRS 750 se calcula con un subconjunto de los píxeles que entran a Tot_Lmir_hot y
  Tot_Lmir_bk (por eso cae con Npix y nunca supera 1), por una regla que ningún texto describe.
- **CÓMO SE VE EN EL DASHBOARD**: en V750 sobre 50°, la magnitud de MIROVA de las pasadas con varios píxeles es menor
  que la que da su propia fórmula; comparar nuestra magnitud contra esa columna sesga la razón hacia «sobrestimamos».
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python -I C:\vrp-trabajo\s159-pruebas\experiments\_s159\p2\escalon_fino.py`
  (lee `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv`).
- **Las dos preguntas**: (1) si el escalón estuviera en 52,6°, los tramos finos lo mostrarían; (2) control negativo:
  VIIRS 375 y MODIS dan 1,0 en los mismos tramos; control positivo: el tramo 50-55 repite el 0,6835 de `ra2/03` (8.753 filas).
- **CONFIANZA**: CONFIRMADO el lugar del escalón, la dependencia con Npix y con el día; SOSPECHA la causa.
- **GRAVEDAD**: 2. Cambia la hipótesis con que arranca el frente S, no una alerta.

### H4. La nota de la Tabla 1 de CA24 («measured in the Vulcanello area») no es literal: el fondo es local
- **SCRIPT:SALIDA**: `vulcanello_fondo.py` → `vulcanello_fondo_salida.txt`.
- **QUÉ PASA**: CA24 describe el fondo de dos maneras: cada alertado tiene su propio fondo, media de los píxeles que lo
  rodean, y el total es la suma (p. 3, columna derecha, Ec. 2); y la Tabla 1 (p. 4) dice que L_MIRbk está «measured in
  the Vulcanello area», un sitio fijo fuera del cono. S141 (D-07) lo dejó SIN RESOLVER. Los dos archivos del propio
  paper (OSF jepv6, S1 y S2, en `C:\vrp-trabajo\s159-pruebas\data\mirova_reference\campus2024_vulcano\`) lo resuelven: si
  la nota fuera literal, L_MIRbk / Npix sería la radiancia I4 de la temperatura del píxel de Vulcanello (S2) en la misma
  pasada. No lo es: razón mediana **0,890**, p5 0,776, p95 1,061, y sólo **5,6 %** de las 354 pasadas queda a menos de
  2 %. Control positivo: con Npix = 1 (n 191), L_MIRhot contra la radiancia de la temperatura de Gran Cratere da mediana
  **0,9949** y 71 % a menos de 2 %: el pareo y la función de Planck funcionan, y el fondo no es Vulcanello. Coincide con
  la estructura del código (V:84: `L_MIRbk = sum(ZI_M13bk(alert))`, un fondo por cada alertado).
- **CÓMO SE VE EN EL DASHBOARD**: invisible; cierra una duda de lectura que podía hacer creer que MIROVA usa un píxel de
  referencia fijo en VIIRS 375.
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python -I C:\vrp-trabajo\s159-pruebas\experiments\_s159\p2\vulcanello_fondo.py`.
- **CONFIANZA**: CONFIRMADO para Vulcano 2021-2023 (354 pasadas). Hijos a marcar (A113):
  `C:\vrp-trabajo\s159-pruebas\docs\audit_s141\lectura\LECTOR_D.md:193`,
  `C:\vrp-trabajo\s159-pruebas\docs\audit_s141\lectura\VERIFICADOR_LECTORES.md:82`,
  `C:\vrp-trabajo\s159-pruebas\docs\audit_s146\FRENTE_F_FIDELIDAD_VIIRS.md:347` y `:668`.
- **GRAVEDAD**: 2.

### H5. El texto sobre el fondo no distingue «media de vecinos» de «interpolación bajo un hueco dilatado»
- **ARCHIVO:LÍNEA**: CA22 p. 7, §3.2, bajo la Ec. 2 («calculated as the arithmetic mean of pixels surrounding the active
  one/s»); CA24 p. 3, Ec. 2; código V:63-85; uso en `C:\vrp-trabajo\s159-pruebas\docs\MIROVA_DIVERGENCES.md:2803` (lista
  S141: «fondo = media de los píxeles que rodean al alertado»).
- **QUÉ PASA**: para VIIRS 750 la misma frase de CA22 corresponde, en el código, a borrar los alertados, agrandar el
  hueco con un cuadrado de 3, 5 o 7 celdas y rellenarlo por interpolación lineal 2D desde más afuera, sin recorte. O sea
  que «los píxeles que rodean» no quiere decir «los vecinos inmediatos». CA24 usa la misma familia de palabras para
  VIIRS 375. El texto no sirve, entonces, para elegir entre el brazo de vecinos de D25 (flag S142) y el fondo del código
  trasladado a VIIRS 375: ninguno de los dos queda respaldado ni contradicho por CA24. El catálogo ya marcó D25 en S158
  (`MIROVA_DIVERGENCES.md:2797`); lo que falta decir es que, para VIIRS 375, la lista de citas de S141 no puede usarse
  como autoridad de ningún estimador concreto.
- **CÓMO SE VE EN EL DASHBOARD**: magnitud de VIIRS 375 (los cúmulos en 0,0 MW que el tablero oculta, R2 §1).
- **CONFIANZA**: CONFIRMADO (páginas y código leídos).
- **GRAVEDAD**: 2. La salida es medir contra la referencia (A115), no elegir por la cita.

### H6. Dos punteros de CLAUDE.md mandan a buscar en fuentes que no tienen lo que dicen
- **ARCHIVO:LÍNEA**: `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:73` («`THESIS_MASSIMETTI.pdf` ... tesis con detalle VIIRS
  adaptation»); `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:181` («Kernel 8-vecinos dNTI contextual: `np.mean` aritmética
  (Coppola 2016a + Campus 2024)»).
- **QUÉ PASA**: (1) la tesis es sobre Sentinel-2 y Landsat 8. VIIRS aparece en 20 páginas y en todas como cita de CA22,
  como dato de entrada o como filtro de estudio (p. 130 impresa, índice 138: «MODIS and VIIRS image with a Zenith
  scanning angle < 50°»; p. 84: MODIS con cenit > 40° fuera). No hay ningún paso de la adaptación a VIIRS. El bloque de
  este mismo frente la listaba como fuente de la adaptación: el puntero ya está desviando trabajo. (2) CA24 no menciona
  ningún kernel ni vecinos para el contraste (búsqueda `eight|neighbo|kernel|window|NTI|ETI`: cero coincidencias de
  método; leí las pp. 3 y 4 renderizadas). La marca S158 de las l. 175-180 corrigió el conteo de vecinos pero dejó la
  atribución a CA24.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO. PNG `massimetti_tesis_pidx138.png`, `massimetti_tesis_pidx92.png`, `campus2024_p3.png`.
- **GRAVEDAD**: 1.

### H7. C26 atribuye el coeficiente de VIIRS 375 a un paper que no lo tiene
- **ARCHIVO:LÍNEA**: C26 índice 8, Tabla 1, fila kMIR: «18 (ref7)» para VIIRS 375; ref. 7 = CA22 (índice 22).
- **QUÉ PASA**: CA22 no da ningún coeficiente de banda I (búsqueda `18\.0|I4|I-band` en CA22: sólo la descripción del
  sensor, p. 6). El valor sí está bien: CA24 p. 4 da 18,0 µm sr con 140.625 m², y en el OSF las filas VIIRS 375 cumplen
  VRP = ΔL × 18,0 × 140.625 en todos los tramos de 48 a 54° de `escalon_fino_salida.txt`. La cita correcta para el k de
  VIIRS 375 es CA24 p. 4, no CA22.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (el número no cambia).

---

## 2. Matriz paso del código × sensor × fuente

Veredicto: **IGUAL** al código, **DISTINTO**, **CALLA** (la fuente no lo trata). «Compatible» = el texto no contradice
al código pero tampoco lo describe. MODIS sólo donde una de mis fuentes lo trata.

| # | paso | lo que hace el `.m` | VIIRS 750 (CA22, C26) | VIIRS 375 (CA24, C26, SAB) | MODIS (C26, MT, MA24) |
|---|---|---|---|---|---|
| 1 | remuestreo: origen, celda, interpolador | entradas «Resampled» (H:19-23), ventana de 67 × 67 (H:125, H:161-162); el remuestreo no está en el código | CA22 p. 7 §3.2 ¶2: grilla UTM «51 × 51 km», centrada en la cumbre, 750 m, 67 × 67: **IGUAL** en tamaño; origen sólo «centered on the volcano summit»; interpolador **CALLA**. C26 idx 5: 50 × 50 km, cumbre GVP | CA24 p. 3: «regular 50 × 50 km UTM grid»; C26 idx 5: 375 m, cumbre GVP; nº de celdas e interpolador **CALLA** | C26 idx 5: 1000 m, misma grilla; interpolador **CALLA** |
| 2 | ROI y cajas | BOX 0/1/2 con umbrales por región; «can be shifted, reshaped or resized» por volcán (H:105-125) | CA22 **CALLA** (sin ROI ni caja); C26 idx 5: todo píxel anómalo del área de 50 km entra al VRP | CA24 **CALLA** sobre cajas; p. 5: el dataset toma alertas a 1 km del cono (selección del estudio, no del detector) | **CALLA** |
| 3 | nube y validez | sin máscara de nube; BT de M15 ≤ 200 K a NaN (H:147-154); escena fuera con la mitad o más de NaN (H:161-167); README: la nube queda a cargo del usuario | CA22 p. 8 §3.4 ¶3: datos «as they are», sin filtro de nube ni de cenit: **IGUAL** (no hay máscara); 200 K y escena **CALLA** | CA24 p. 4: sin corrección atmosférica ni filtro de cenit, puede haber nube: **IGUAL**; 200 K **CALLA** | MA24 p. 7 §3.2 y MT p. 84 y 130: filtros de **estudio** (noche, cenit, 5 km), no del detector |
| 4 | NTI y K1, día y noche | NTI H:159; K1 -0,7 noche, -0,5 día (H:177-189) | CA22: «the same used for MODIS ... (see [28])» p. 7; números **CALLA** | CA24 «spectral and spatial filters» p. 3: **CALLA** | C26 idx 5 nombra NTI y ETI; números **CALLA** |
| 5 | ETI y regresión | `polyfit` grado 2 sin alertados (H:319-358) | **CALLA** | **CALLA** | C26 nombra ETI: **CALLA** |
| 6 | dNTI: ventana 3 × 3, con o sin central | `colfilt` 3 × 3, media con el central (H:281-288, 362-363) | **CALLA** | **CALLA** | (Coppola 2016a «eight», fuera de mi lote) |
| 7 | C1 y C2 por caja | H:180-187, 306-312, 376-382 | **CALLA** | **CALLA** | **CALLA** |
| 8 | compuerta de temperatura de brillo | no existe | **CALLA** (no la menciona, lo que es coherente con que no exista) | **CALLA** | **CALLA** |
| 9 | segundo pase | recalcula estadísticos y regresión sin las alertas del primero (H:223-235) | **CALLA** | **CALLA** | **CALLA** |
| 10 | rama diurna y reflejo solar | rama diurna H:188-199; escena fuera si reflejo < 12° (H:83-89) | CA22 p. 16-17: procesa el día, umbrales más altos: **IGUAL** en sentido; números y 12° **CALLA** | CA24: sólo noche (p. 4) | **CALLA** en mis fuentes |
| 11 | fondo del VRP: halo, interpolación, recorte | alertados a NaN, dilatación 3/5/7 según npix ≤ 4 / ≤ 30 / > 30, `fillmissing2` lineal, ΔL sin recorte (V:63-85) | CA22 p. 7: «arithmetic mean of pixels surrounding»: **DISTINTO** en el estimador (no menciona hueco ni interpolación); recorte **CALLA** | CA24 p. 3 Ec. 2: un fondo por alertado, sumado: **IGUAL** en estructura (V:84); estimador como CA22: halo **CALLA**; nota de Tabla 1 p. 4 «Vulcanello»: **refutada como literal** (H4) | MA24 p. 8 Ec. 1: Σ ΔL(i) por alertado, sin recorte: compatible |
| 12 | suma o máximo | suma sobre todas las alertas (V:83-85), unión de pasadas (H:241-248) | CA22 p. 7: «radiance of the alerted pixel/s»: compatible. C26 idx 6 ¶2: «summed VRP of all alerted pixels»: **IGUAL** | CA24 p. 3 Ec. 1 y 2: sumas: **IGUAL** | MA24 p. 8 Ec. 1: **IGUAL** |
| 13 | coeficiente y área | 1,97e7 × 0,5625 km² (V:88-91) | CA22 p. 7 Ec. 1: **IGUAL** | CA24 p. 4: 18,0 µm sr y 140.625 m²; sin código; OSF lo cumple (H7) | C26 idx 8: 18,9 y 10⁶ m² |
| 14 | cenit, barrido, bow tie, zonas de agregación | nada | CA22 p. 6 §3.1: agregación de 2 o 3 muestras, borde 1,5 a 0,75 km; p. 16: muchas pasadas sobre 55°; p. 8: sin filtro de cenit. **Ningún tratamiento distinto sobre 50°**; bow tie **CALLA** | CA24 p. 4: sin filtro de cenit; bow tie **CALLA** | MT p. 130: filtro de estudio < 50° (MODIS y VIIRS); MA24 p. 7: filtro > 40° por «thermal bleeding» |
| 15 | qué se publica | VRP, npix, ΔL, fondo (V:1-17) | C26 idx 5-6: todos los alertados del área, clase volcánica posterior | CA24 Tabla 1 p. 4: fecha, cenit, azimut, Npix, L_hot, L_bk, VRP | C26 |

**Fila que falta en el código y que los textos sí tienen**: la clasificación posterior volcánico / no volcánico (C26
idx 5, último párrafo de la sección de detección). No está en el `.m` y no es del detector.

**Lectura de la matriz.** Donde los textos hablan (grilla, suma, coeficiente, sin máscara de nube, rama diurna) dicen lo
mismo que el código. En el detector (filas 4 a 9) callan todos para VIIRS, también para VIIRS 750: CA22 remite a Coppola
2016a. La hipótesis del frente P («donde el paper describe un paso que el código fija, también dice si vale para 375 y
MODIS») queda **refutada por su propio criterio**: los pasos clave de detección, halo y cenit quedan sin fuente para
VIIRS 375.

---

## 3. Las cuatro preguntas

**(a) ¿VIIRS 375 usa el mismo fondo, halo y suma que el `.m` de VIIRS 750?** La **suma**, sí: CA24 Ec. 1 y 2 (p. 3) y C26
(idx 6) suman la radiancia y el fondo de cada alertado, igual que V:83-85. La **estructura del fondo** (un valor por
alertado, sumado) también coincide con V:84. El **halo y la interpolación** no los menciona nadie: CA24 dice «media de
los píxeles que rodean», que es la misma frase que en VIIRS 750 corresponde a la interpolación bajo un hueco dilatado
(H5). La nota «Vulcanello» de la Tabla 1 no es literal (H4). Conclusión: el traslado de la segunda ronda no tiene texto
en contra, pero tampoco a favor en lo del halo; se mide.

**(b) ¿Qué grilla y qué remuestreo?** VIIRS 750: UTM, centrada en la cumbre, celda de 750 m, 67 × 67 (CA22 p. 7; CA22
escribe «51 × 51 km», que con 67 celdas de 750 m son 50,25 km). VIIRS 375: UTM regular de 50 × 50 km (CA24 p. 3), celda
de 375 m con centro en las coordenadas GVP (C26 idx 5). **Origen exacto de la grilla e interpolador: ninguna fuente lo
dice.** El código tampoco: recibe las matrices ya remuestreadas.

**(c) ¿Zonas de agregación, bow tie o un tratamiento distinto sobre ~50°?** CA22 nombra la función de agregación como
ventaja del instrumento (p. 6 §3.1; p. 16; p. 19), sin ningún tratamiento propio. Bow tie: ninguna de mis fuentes.
El único 50° del grupo es un **filtro de estudio** que saca filas (MT p. 130), no un cambio de fórmula. Y el escalón
del OSF está en **50,0° exactos**, no en el límite de la zona de agregación, que cae en 52,6° (H3). Ningún texto lo explica.

**(d) Frases usadas hoy como autoridad que el código contradice** (candidatas a marca A113):

| uso | archivo:línea | qué contradice | estado |
|---|---|---|---|
| «MIR solo nocturno», regla no negociable | `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:183` | H:173-199, H:83-89; CA22 p. 16-17 | **sin marca** (H2) |
| «para MODIS y VIIRS 375 manda el paper» | `C:\vrp-trabajo\s159-pruebas\docs\MISSION.md:130`; `CLAUDE.md:179-180` | para VIIRS 375 no hay paper de detección (H1) | sin marca |
| atribución del kernel de 8 vecinos a Campus 2024 | `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:181` | CA24 no lo dice; el código usa 9 | marcada en el conteo, no en la cita (H6) |
| «tesis con detalle VIIRS adaptation» | `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:73` | la tesis no lo tiene | sin marca (H6) |
| fondo = «media de los píxeles que rodean» como autoridad de un estimador | `C:\vrp-trabajo\s159-pruebas\docs\MIROVA_DIVERGENCES.md:2803` | V:63-85 hace otra cosa bajo la misma frase | D25 marcado en S158 (l. 2797); la lista de citas no (H5) |
| fondo de Vulcanello como pregunta abierta | `docs\audit_s141\lectura\LECTOR_D.md:193`, `VERIFICADOR_LECTORES.md:82`, `docs\audit_s146\FRENTE_F_FIDELIDAD_VIIRS.md:347` y `:668` | refutada como literal por los datos del paper (H4) | sin marca |

---

## 4. Lo que no pude medir

- **Coppola et al. 2022, Front. Earth Sci. 10:964372** (Vulcano con VIIRS 375, primer uso de banda I por MIROVA según
  CA22 [103] y MT p. 21): no está en `documentacion\`. Es el candidato más probable a describir la adaptación a 375 m.
  Tampoco está el póster «Campus et al. 2021» (OSF wv8yt).
- Aveni et al. 2024 RSE (134 × 134 para VIIRS 375) y la Guía de Usuario del tablero 2.5 (filtro de cenit elegible por el
  usuario, l. 171 del `.md`): ubicadas, **no renderizadas** por mí; no las uso como evidencia.
- La causa del escalón de 50° (H3): sólo dejé descartadas dos explicaciones (zona de agregación y cortes de la
  dilatación). Lo que haga MIROVA sobre 50° en VIIRS 750 no está en ningún texto ni en el código.
- H4 vale para Vulcano: con un solo volcán no puedo decir si el fondo de VIIRS 375 es dilatación e interpolación o
  media de vecinos; sólo que no es un píxel fijo.
- La conversión barrido a cenit (H3) es geometría esférica sin elipsoide ni relieve; el margen frente a 50° (2,6°) es
  mucho mayor que ese error.

## 5. VERIFICADO LIMPIO

- **La suma de todos los alertados** (A10 rebajada, `C:\vrp-trabajo\s159-pruebas\CLAUDE.md:283-287`): CA24 Ec. 1 y 2
  (p. 3), MA24 Ec. 1 (p. 8), C26 idx 6 ¶2 y el código V:83-85 dicen lo mismo. No hay que volver a leerlo.
- **El coeficiente y el área de VIIRS 750**: CA22 p. 7 Ec. 1 = V:88-91 (1,97e7 × 0,5625 km²).
- **El k de VIIRS 375 = 18,0 × 140.625 m²**: CA24 p. 4 y el OSF (`escalon_fino_salida.txt`, columna VIIRS_375 = 1,0 de
  48 a 54°). La lista de `docs/MISSION.md:143` («Campus 2022 / Campus 2024 (k VIIRS)») es correcta en el número.
- **«El canal NRT no filtra por cenit»** (`docs/MIROVA_DIVERGENCES.md:2302`): CA22 p. 8 §3.4 y CA24 p. 4 lo dicen, y el
  código no tiene filtro de cenit. Lo que sí hay es el escalón del OSF (H3), que no es un filtro.
- **Sin máscara de nube en el detector**: CA22 p. 8, CA24 p. 4 y el código coinciden.
- **Campus 2022 es sólo VIIRS 750**: p. 6, penúltimo párrafo de §3.1.
- **MA24 y la tesis no describen el detector de VIIRS**: barridas página por página por `VIIRS`; su contenido de VIIRS
  son filtros de estudio y citas a CA22. No hace falta releerlas para este tema.
- Comandos: `ubicar.py <pdf> <regex>` para ubicar; `render.py <pdf> <página> <png>` para verificar; los cuatro scripts
  del OSF y `vulcanello_fondo.py` imprimen su control positivo y su control negativo en la salida.
