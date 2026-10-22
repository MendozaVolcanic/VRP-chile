# P1 S159: relectura de los papers del linaje Coppola y MIROVA con el código de VIIRS 750 como llave

Auditoría de sólo lectura, 2026-10-21. No se tocó `pipeline/`, `data/` ni `frontend/`; todo lo escrito está en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\p1\`. Las citas a PDF se verificaron renderizando la página a imagen
(`render.py`, PNG en `png\`); `buscar.py` y `buscar_rango.py` sólo sirvieron para ubicar.

## 0. En una pantalla

**Por qué importa.** Para VIIRS 750 ahora hay un programa; para MODIS y VIIRS 375 sólo hay texto. La segunda ronda
(S158 R2) trasladó por analogía el fondo y la suma (pieza 1) y la geolocalización y el fondo de MODIS (pieza 5). La
pregunta de este frente es cuánto se le puede creer al texto donde no hay código.

**Respuesta.** Comparado paso a paso con el código de VIIRS 750, Coppola et al. 2016a (el único paper que describe el
algoritmo con detalle, y el que Coppola et al. 2026 designa como referencia para MODIS) coincide en **13 de los 20
pasos estructurales en que habla y difiere en 7** (`contar_matriz.py`). Los 7 no están repartidos al azar: caen justo
en el fondo (media local de 8 vecinos contra 3 × 3 con el central; fondo del VRP por media de los que rodean contra
halo dilatado más interpolación), en la conectiva de umbrales (`or` contra `max`), en el segundo pase (condicional y
sin rehacer la regresión contra incondicional y rehaciéndola), en el piso de -0,1 y en la ROI por volcán. Es decir:
el texto describe bien el esqueleto (grilla, NTI, ETI, Test 1 que sale del fondo, μ y σ de escena, suma de todos los
alertados, sin recorte, sin compuerta de temperatura, sin corrección por cenit) y **mal o nada las piezas que la
segunda ronda trasladó por analogía**. Para VIIRS 375 ninguna de las cuatro fuentes describe fondo, halo ni ROI.

**Lo único que las fuentes sí extienden explícitamente a los tres sensores** (Coppola et al. 2026, Scientific Data,
renderizado): la grilla UTM de 50 × 50 km centrada en la cumbre GVP con celda de 1000, 750 y 375 m; la detección por
NTI y ETI más análisis espacial; que se retienen todos los píxeles anómalos del recuadro; que el VRP de cada pasada es
la suma de todos los alertados; el coeficiente y el área nominal por sensor; y que MODIS usa la geolocalización con
corrección de terreno MOD03/MYD03 (y VIIRS, VNP03/VJ103).

## 1. Las dos preguntas del instrumento

Para la matriz (lectura): (1) si el paper dijera lo contrario del código en un paso, la matriz lo ve sólo si el paso
está en sus filas; las filas son las 15 del brief más las que aparecieron al leer (22 subfilas). Un paso que ni el
código ni yo listamos queda fuera. (2) Un CALLA podría ser «no lo leí»: para cada fuente barrí el PDF entero por
palabras clave (`buscar.py`, salida no persistida, sólo para ubicar) y rendericé toda página con una coincidencia
algorítmica. Lo que sigue CALLA después de eso es silencio del texto, con esa salvedad.

Para las mediciones con el OSF v2.5 (`osf_contra_tabla1.py`, `osf_maxdist_detalle.py`): control positivo, la identidad
VRP = (hot - bk) · k · A bajo 50° de cenit da **100,00 %** en las tres resoluciones (n 208.249 MODIS, 66.391 VIIRS 750,
163.935 VIIRS 375), así que las columnas se leen bien; control negativo, un umbral de 10^15 W deja el 100 % de las filas
«bajo umbral». Denominador: las 615.470 filas del CSV, 2001-01-01 a 2025-12-31, global, todas las clases.

## 2. Fuentes y una advertencia de archivo

| clave | fuente | páginas renderizadas (PNG en `png\`) | cómo cito |
|---|---|---|---|
| C16 | Coppola et al. 2016a, Geol. Soc. Spec. Publ. 426, `sp426.5.pdf` | pp. impresas 183 a 189 y 197 (`c16_idx2` a `c16_idx8`, `c16_idx16`; impresa = índice + 181) | p. impresa, columna, ecuación |
| CAP | Coppola 2025, cap. 11 de *Modern Volcano Monitoring*, dentro de `978-3-031-86841-2.pdf` | pp. impresas 335, 336, 337, 340, 346, 347, 348 (`book_idx338` a `book_idx351`; impresa = índice - 3) | p. impresa, ecuación |
| SD26 | Coppola et al. 2026, Scientific Data, `Coppola_2026_SciData_...pdf` (versión «article in press», sin folio impreso) | pp. del PDF 4 a 10, 21 y 22 (`sd26_idx3` a `sd26_idx9`, `sd26_idx20`, `sd26_idx21`) | p. del PDF (índice + 1) |
| UG | MIROVA Dashboard User Guide 2.5 | pp. 2, 3, 5, 7 (`ug_idx1`, `ug_idx2`, `ug_idx4`, `ug_idx6`); 1, 4, 6, 8 sólo por texto, sin contenido algorítmico | p. de la guía |

**Advertencia.** El brief apunta el capítulo a `978-3-031-86841-2_9.pdf`; ese archivo es el capítulo 9 (Campion, gases
volcánicos), no el de Coppola. El de Coppola está en el libro completo, pp. 325 a 364. El proyecto ya lo sabía
(`docs/s128/CORPUS_HIGIENE.md:94`, `docs/paper/sec5_methods.md:221`, `experiments/_s158_audit/f4/INFORME.md:200`); el
brief lo heredó. Sin efecto en esta lectura.

## 3. La matriz

Código: `MIROVA_VIIRS750_hotspot_detection.m` (H) y `MIROVA_VIIRS750_VRP.m` (V), en
`experiments/_s158_d17_diseno/osf_codigo_mirova/`. Veredicto respecto del código: IGUAL / DISTINTO / CALLA. UG calla en
todas las filas de algoritmo (es la guía del tablero del archivo); aparece sólo donde dice algo.

| # | paso | el `.m` (VIIRS 750) | MODIS | VIIRS 375 | VIIRS 750 |
|---|---|---|---|---|---|
| 1 | remuestreo: origen, celda, interpolador | entra ya remuestreado (`ZI_M13`, `ZI_M15`, H:19-23), 67 × 67; el interpolador no está en el código | C16 p. 183 col. der.: recorte y remuestreo a grilla de 1 km igualmente espaciada, 50 × 50 km centrada en la cumbre GVP, por el crecimiento del píxel con el ángulo y para tener escala homogénea: **IGUAL** en estructura. SD26 p. 5: «resampled onto a UTM grid centred on the summit coordinates provided by the Global Volcanism Program», 1000 m: **IGUAL**. Interpolador: **CALLA** en las tres fuentes; SD26 p. 21 dice que el remuestreo no se distribuye | SD26 p. 5: misma grilla UTM, 375 m: **IGUAL** en estructura; cuántas celdas (50 km / 375 m = 133,3) e interpolador: **CALLA** | SD26 p. 5, 750 m: **IGUAL** (67 × 0,75 = 50,25 km) |
| 2 | ROI y cajas | BOX 0/1/2; en el ejemplo la clase 2 es 7 × 7 celdas centrales (filas y columnas 30 a 36), la 1 un anillo de 21 × 19 (`box_ejemplo_salida.txt`); BOX 0 y 1 llevan los mismos umbrales; «ROI1 and ROI2 can be shifted, reshaped or resized» por volcán (H:120-125) | C16 pp. 183-184: ROI1 caja de 5 × 5 km en la cumbre, ROI2 el resto del marco: **IGUAL** (dos juegos de umbral). C16 p. 189 col. izq.: los parámetros pueden aplicarse a otros volcanes «by using the same spatial grid and ROIs»: **DISTINTO** del ajuste por volcán. SD26 y CAP: **CALLA** | **CALLA** en todas | **CALLA** en los papers; sólo el código |
| 3 | nubes y validez | sin máscara de nube; BT de M15 ≤ 200 K a NaN; escena rechazada con la mitad o más de NaN (H:147-167) | C16 p. 185 col. der. y p. 188 col. izq.: las nubes no se tratan: **IGUAL**. Filtro de 200 K y de escena: **CALLA**. CAP p. 346: la nube se juzga en la supervisión de la serie, no en la detección | **CALLA** | **CALLA** (SD26 p. 6: sin corrección atmosférica, TOA) |
| 4 | NTI y K1, día y noche | NTI (H:159); K1 noche -0,7, día -0,5 (H:178, 189); los del Test 1 son alerta y salen del fondo (H:202-206, 245, 276) | C16 p. 184 ec. 1: **IGUAL**. C16 p. 186 col. der.: los del Test 1 «flagged as 'active' and subsequently discarded»: **IGUAL**. K1 noche -0,8 y día -0,6 (Tabla 1, p. 187; CAP p. 336 Tabla 2 repite -0,8 / -0,6 para MODIS): números de otro sensor | **CALLA** | **CALLA** en los papers |
| 5 | ETI y regresión | NTI esperado desde la BT de M15 por Planck, polinomio de grado 2 sin las alertas (H:319-358) | C16 p. 185 ec. 2 a 5: **IGUAL** (la ec. 4 trae la errata `bNTI` por `bNTIapp`; la ec. 5 la corrige) | SD26 p. 5: NTI y ETI para los tres: **IGUAL** en estructura | ídem |
| 6 | dNTI, ventana 3 × 3, central | media de la ventana de 3 × 3 **con** el central, omitiendo alertados y fríos (H:279-287); piso de -0,1 sólo en el contraste de NTI (H:298); marco excluido (H:99-103) | C16 p. 185 col. der.: media aritmética de los **ocho** vecinos, y «all eight neighbouring pixels are used»: **DISTINTO**. Piso «dNTI or dETI < -0.1»: **DISTINTO**. Borde no apto: **IGUAL** | **CALLA** | **CALLA** |
| 7 | umbrales C1 y C2 por caja | `max(μ + Nσ, mínimo)` (H:306-312, 376-382); noche cumbre 5σ, 0,003 / 0,003; fuera 10σ, 0,02 en NTI y 0,01 en ETI; día 15σ, 0,02 (H:177-199); μ y σ de toda la escena | C16 p. 187: Tests 2 y 3 con **or**: **DISTINTO**. μ y σ «of all the suitable pixels within the image»: **IGUAL**. Tabla 1: cumbre 0,003 y 5, escena 0,01 y 10, día 0,02 y 15 (un solo C1 para dNTI y dETI) | **CALLA** | **CALLA** |
| 8 | compuerta de temperatura de brillo | no existe (H:389-399) | C16 p. 187: Tests 2 y 3 sin condición de temperatura: **IGUAL** (nosotros sí la tenemos, D22) | **CALLA** | **CALLA** |
| 9 | segundo pase | incondicional (H:228-235); excluye absolutas y primer pase y **rehace** la regresión (H:276-277, 328-345) | C16 pp. 187-188: «applied only if one or more pixels have been detected», repite «step 2 (spatial analysis)» y los Tests 2 y 3 sobre las nuevas dNTI y dETI eliminando los activos: condición **DISTINTO**; exclusión de activos **IGUAL**; regresión **DISTINTO por lectura** (el texto no nombra el paso espectral; nuestro pipeline, que reusa el ETI, sigue esta lectura) | **CALLA** | **CALLA** |
| 10 | rama diurna y reflejo solar | misma secuencia con otros umbrales; rechazo de toda la escena con ángulo de reflejo < 12° (H:83-89, 188-199) | C16 Tabla 1 tiene columna diurna: **IGUAL** en existencia, números de otro sensor. Reflejo solar: **CALLA** en C16, CAP, SD26 (búsqueda «glint» vacía en los cuatro). SD26 p. 8 Tabla 1: umbral de VRP diurno de 5 × 10^7 W para el archivo | **CALLA** el filtro; SD26 Tabla 1 trae día | ídem |
| 11 | fondo del VRP | alertados a NaN, hueco dilatado con cuadrado de 3, 5 o 7 según Npix ≤ 4, ≤ 30, > 30, interpolación lineal `fillmissing2`, ΔL sin recorte (V:63-85) | C16 p. 188 col. der.: L4bk «estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)»: **DISTINTO**. Ec. 6 sin recorte: **IGUAL**. CAP p. 336: fondo «generally calculated from pixel(s) surrounding the anomaly», genérico. SD26 p. 6: «L_bg is the estimated background radiance», sin método: **CALLA** | **CALLA** (SD26 sin método; ninguna fuente menciona halo ni dilatación) | **CALLA** en los papers |
| 12 | suma o máximo | suma de todos los alertados (V:83-85) | C16 p. 189 ec. 8: **IGUAL**. CAP p. 336 ec. 13: **IGUAL**. SD26 p. 6 y p. 8: suma de todos los alertados por pasada, para el proceso que corrió en los tres sensores: **IGUAL** | SD26 p. 6: **IGUAL** | SD26 p. 6: **IGUAL** |
| 13 | coeficiente y área | 1,97 × 10^7 × 0,5625 km² (V:88-91) | C16 p. 188 ec. 7: 18,9 × A, A = 1 km² (p. 189). SD26 p. 8 Tabla 1: 18,9 y 1,0 × 10^6 m² | SD26 Tabla 1: 18 y 1,4 × 10^5 m² | SD26 Tabla 1: 19,7 y 5,6 × 10^5 m²: **IGUAL**. CAP p. 337: α = 2,88 × 10^-19 (equivale a 19,7): **IGUAL**, pero **A = 0,75 × 10^6 m²: DISTINTO** |
| 14 | cenit o ángulo de barrido | ningún tratamiento; área fija | C16 p. 183: el remuestreo existe por el crecimiento del píxel con el ángulo; p. 197: más de 30° (69 % de los datos) degrada geolocalización, no se corrige: **IGUAL** (sin corrección). CAP pp. 347-348: sólo para interpretar; Fig. 10c usa clases > 0°, > 30°, > 50° como ilustración. SD26 p. 8 y p. 10: «nominal pixel size at nadir», cenit guardado para que el usuario filtre | igual que MODIS (SD26) | igual; **ninguna fuente menciona zonas de agregación ni un trato distinto sobre 50°** |
| 15 | qué se publica | `VRP_MW`, `npix = numel(alert)`, `deltaL_MIR`, fondo; sin alerta, NaN y no cero (V:1-22, 45-61) | SD26 pp. 8-10 Tabla 2 (archivo): Npix, Tot_Lmir_hot y bk, VRP, LAT/LON del píxel más caliente, Max_Dist al alertado más lejano, clase DBSCAN; UG p. 7 lo mismo. El banner NRT (NONE, LOW, ...) no aparece en ninguna de las cuatro fuentes: **CALLA** | ídem | ídem |

Geolocalización (sin fila en el brief): SD26 p. 4: MODIS con «MOD03 and MYD03 Terrain-Corrected Geolocation
products»; VIIRS con VNP03MOD/VJ103MOD y VNP03IMG/VJ103IMG.

## 4. Las cuatro preguntas del brief

**(a) ¿Alguna frase dice que VIIRS 375 y MODIS usan el mismo fondo, halo y suma que VIIRS 750, o que no?**
- **Suma: sí, explícita para los tres.** SD26 p. 6: «When more than one pixel is detected, pixel-level VRP values are
  subsequently summed [...] Each record [...] corresponds to the summed VRP of all alerted pixels», y el mismo párrafo
  dice que toda la secuencia MODIS y VIIRS se procesó «following the procedure described above», con conjuntos
  separados para MODIS, VIIRS 750 y VIIRS 375. SD26 p. 5: «All resampled pixels exhibiting anomalous thermal behavior
  within this area were retained for VRP calculation».
- **Fondo: no hay frase para ningún sensor que describa el del código.** SD26 sólo nombra L_bg. Para MODIS, la
  referencia que SD26 designa (p. 5: «Further details on the application of the algorithm to MODIS and VIIRS data
  are provided in refs. 6 and 7»; ref. 6 = Coppola 2016a, p. 22 renderizada) describe otro método (media de los que
  rodean). Para VIIRS 375, nada.
- **Halo o dilatación: ninguna fuente lo menciona**, en ningún sensor.

**(b) ¿Algún paper describe la ROI por volcán o que MIROVA la ajusta?** No. C16 p. 189 dice lo contrario (mismos grilla
y ROIs para otros volcanes); SD26 y CAP callan; UG p. 5 sólo describe el círculo de referencia de 25 km del mapa del
archivo, que «does not itself filter the data». El ajuste por volcán está únicamente en el comentario del código
(H:120-125).

**(c) ¿Zonas de agregación de VIIRS, ángulo de barrido o trato distinto sobre ~50°?** No. Lo único cercano es la
Fig. 10c de CAP p. 348 (clases de cenit > 50° para ilustrar el sesgo por acimut en Stromboli) y SD26 p. 19 (la
agregación semanal reduce el peso de cenits grandes; ubicado por la capa de texto, sin renderizar). Nada explica el escalón de 50° del OSF en VIIRS 750 (S158 F6).

**(d) Frases que el proyecto usa como autoridad y que el código (o la fuente primaria) contradice**, candidatas a
marca A113. Revisé `CLAUDE.md`, `docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md` y, al paso, los informes S158. Las ya
marcadas (8 vecinos en `CLAUDE.md:181`, A4 en `CLAUDE.md:231`, cúmulo contra píxel en `CLAUDE.md:1718`, día en D27,
máscaras en `MISSION.md:302`, «L1129» en `CLAUDE.md:323`) no se repiten. Sin marca:

| # | dónde | qué dice | qué lo contradice |
|---|---|---|---|
| d1 | `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:191-192`, `:211`, `:281`; hijo en `docs/MIROVA_DIVERGENCES.md:3314` | «La estructura, sí, con apoyo citable», incluyendo media de 3 × 3 con el central, `max`, segundo pase que recalcula regresión y fondo interpolado sin recorte; «Coppola 2026 p. 5 habla de un solo hotspot-detection code [...] para los tres sensores» | Para MODIS, la fuente que SD26 designa (C16) dice lo contrario en esos cuatro; SD26 p. 5 no dice «para los tres sensores», remite MODIS y VIIRS a las refs. 6 y 7. Ver H1 |
| d2 | `docs/MISSION.md:125` | «En 3 puntos el paper y el código no dicen lo mismo» | Son 7 contra C16 (`contar_matriz_salida.txt`), más K1 diurno y el reflejo solar. Ver H2 |
| d3 | `docs/MIROVA_DETAILED_CITATIONS.md:114-116` | VIIRS 750 «A_pix = 0,75×10⁶ m²» bajo «operacional MIROVA» | V:89 (0,5625 km²), SD26 Tabla 1 (5,6 × 10^5), identidad del OSF al 100 % con 562.500 m². Ver H3 |
| d4 | `CLAUDE.md:183` | «MIR solo nocturno (contaminación solar diurna)», en «Reglas científicas» | H:188-199 (rama diurna); SD26 Tabla 1 (umbral diurno); el OSF trae 38.297 filas diurnas (1.384 + 17.859 + 19.054, `osf_contra_tabla1_salida.txt`). La marca vive en D27 y no subió a `CLAUDE.md`. Ver H5 |
| d5 | `docs/MIROVA_DIVERGENCES.md:2385` (título de D18) | «El ROI1 del paper es una CAJA de 5 km igual para todos» | Cierto del paper (C16 p. 189), falso del sistema según H:120-125; ninguna marca S158 en la sección D18 (búsqueda de «S158», «reshap», «por volcán» en las líneas 2385 a 2521: sólo el título). Ver H7 |

## 5. Hallazgos, de mayor a menor gravedad

### H1. «Trasladar lo estructural con cita» no tiene cita en los pasos que la segunda ronda trasladó
- **Dónde**: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:191-192`, `:211`, `:281`; `docs/MIROVA_DIVERGENCES.md:3314`;
  `docs/AUDIT_S158_R2.md` piezas 1 y 5 (que sí dicen «trasladado»). Salida: `contar_matriz_salida.txt`.
- **Qué pasa**: el texto que describe MODIS (C16, designado por SD26 p. 5 como la referencia de MODIS) acierta el
  esqueleto pero difiere del código de VIIRS 750 en 7 de 20 pasos, y esos 7 son el fondo local, el fondo del VRP, la
  conectiva, el segundo pase, el piso y la ROI. Para MODIS no se puede saber si el operacional sigue al código o al
  paper; para VIIRS 375 ninguna fuente habla. Lo que sí tiene cita para los tres sensores es la grilla, la suma de
  todos los alertados, el área nominal y la geolocalización con corrección de terreno.
- **Cómo se ve en el tablero**: invisible hoy. El riesgo es de proceso: que el fondo interpolado, el 3 × 3 con central
  o el segundo pase con regresión se adopten en MODIS o VIIRS 375 rotulados «fieles, con cita».
- **Reproducir**: leer `png/c16_idx4.png` (8 vecinos, piso), `c16_idx6.png` (or, segundo pase), `c16_idx7.png`
  (fondo), `sd26_idx4.png` (refs. 6 y 7), `sd26_idx21.png` (ref. 6); `python contar_matriz.py`.
- **Confianza**: CONFIRMADO en lo leído. El veredicto de regresión del segundo pase es lectura (el texto no nombra el
  paso espectral). No leí Campus 2022 (lo cubre otro subagente del frente P): si Campus describe esos pasos para
  VIIRS, puede cambiar la columna de VIIRS 375.
- **Gravedad**: 3. Puede torcer la adopción de un fondo en MODIS y VIIRS 375 sin que su sustento sea el que se dice;
  la defensa es el A/B contra MIROVA (A115), que el plan ya exige.

### H2. `docs/MISSION.md:125` cuenta 3 diferencias paper contra código; son 7 contra Coppola 2016a
- **Dónde**: `docs/MISSION.md:125-130`.
- **Qué pasa**: además de los 3 que nombra (media local, fondo del VRP, piso), C16 difiere en la conectiva (`or`
  contra `max`), en que el segundo pase sea condicional, en la regresión del segundo pase y en la ROI igual para
  todos; y fuera de la Tabla 1 de noche, en K1 diurno (-0,6 contra -0,5) y en el filtro de reflejo solar (sólo en el
  código). La misma línea dice «para MODIS y VIIRS 375 manda el paper hasta tener su código o una medición»: la
  conectiva `max` de producción en MODIS y VIIRS 375 entra por el lado de «una medición» (adopción de K, S153), pero
  quien lea sólo esa línea cree que el paper y el código coinciden en todo lo demás.
- **Cómo se ve en el tablero**: invisible.
- **Reproducir**: `python contar_matriz.py`; `png/c16_idx6.png`.
- **Confianza**: CONFIRMADO. **Gravedad**: 2.

### H3. El capítulo Springer da un área de píxel de VIIRS 750 que no es la del código, y el proyecto la cita
- **Dónde**: CAP p. 337 (`png/book_idx340.png`): «750 m resolution bands [...] A_pix = 0.75 × 10^6 m²». Citado sin
  marca en `docs/MIROVA_DETAILED_CITATIONS.md:114-116` como «VRP MIR (Eq.17), operacional MIROVA».
- **Qué pasa**: el código usa 0,5625 km² (V:89), la Tabla 1 de SD26 5,6 × 10^5 m², y en el OSF la identidad con
  562.500 m² se cumple en el 100,00 % de 66.391 filas VIIRS 750 bajo 50° (`osf_contra_tabla1_salida.txt`). El 0,75 ×
  10^6 inflaría el VRP de VIIRS 750 en 1,33 veces. El α (2,88 × 10^-19, equivalente a 19,7) sí coincide.
- **Cómo se ve en el tablero**: invisible; ningún archivo de `pipeline/` contiene 750000, 0.75e6 ni 7.5e5 (grep).
- **Confianza**: CONFIRMADO. **Gravedad**: 2 (sólo si alguien lo toma de ese documento).

### H4. Coppola 2026 dice que MIROVA usa MOD03 en MODIS: respaldo citable para la pieza 5, no citado
- **Dónde**: SD26 p. 4 (`png/sd26_idx3.png`): MOD021KM y MYD021KM «together with the corresponding MOD03 and MYD03
  Terrain-Corrected Geolocation products»; VIIRS con VNP03MOD/VJ103MOD y VNP03IMG/VJ103IMG.
- **Qué pasa**: la segunda ronda (R2-2, pieza 5) y `docs/SINTOMAS.md:118-129` proponen leer MxD03 por medición; nadie
  cita que el propio MIROVA declara usarlo. `docs/DISENO_D17_REMUESTREO_UTM.md:118` cita sólo la frase de VIIRS.
- **Cómo se ve en el tablero**: es la explicación citable de por qué el píxel MODIS del cráter cae corrido hacia el
  nadir sobre 25° y por qué dos protegidas de Chillán MODIS no tienen píxel (sospecha de R2).
- **Confianza**: CONFIRMADO (la frase); que usarlo cierre la brecha es SOSPECHA de R2. **Gravedad**: 2 (positivo:
  sube la pieza 5 de «medido» a «medido y declarado por MIROVA»).

### H5. `CLAUDE.md:183` sigue diciendo «MIR solo nocturno» como regla científica
- **Dónde**: `CLAUDE.md:183`; la corrección vive en `docs/MIROVA_DIVERGENCES.md:2875` y siguientes (D27).
- **Qué pasa**: el código tiene rama diurna completa (H:188-199) con rechazo por reflejo solar (H:83-89); SD26 Tabla 1
  fija un umbral diurno por sensor; el OSF trae 38.297 filas diurnas. Por A113 (c) la corrección debía subir primero a
  `CLAUDE.md`.
- **Cómo se ve en el tablero**: las alertas diurnas de MIROVA no tienen record nuestro (R2 #11: 3 protegidas de
  Chillán V750). La línea no las causa, pero sostiene que no se busquen.
- **Confianza**: CONFIRMADO. **Gravedad**: 2.

### H6. En el OSF, LAT/LON (píxel más caliente) y Max_Dist (alertado más lejano) no se refieren al mismo punto
- **Dónde**: `osf_contra_tabla1_salida.txt`, `osf_maxdist_detalle_salida.txt`; definición en SD26 pp. 9-10 Tabla 2 y
  UG p. 7.
- **Qué pasa**: con Npix = 1 los dos campos deberían dar la misma distancia a la cumbre. En MODIS la mediana de la
  diferencia es 8 m (p95 370 m); en VIIRS 375 la diferencia va de -401 a +394 m (percentiles 1 a 99, n 45.285) y en el
  9,64 % de todas las filas VIIRS 375 el píxel más caliente queda más de media celda **más lejos** que el «más lejano».
  O Max_Dist se mide desde otro punto (centro de grilla, como `Distancia_km` en el NRT, D15) o LAT/LON no es la celda.
- **Cómo se ve en el tablero**: invisible. Afecta a quien pareé posiciones con el OSF bajo una celda.
- **Reproducir**: `python osf_maxdist_detalle.py`.
- **Confianza**: CONFIRMADO el desacuerdo; el mecanismo es SOSPECHA. **Gravedad**: 1.

### H7. El título de D18 da por regla del sistema lo que es sólo del paper
- **Dónde**: `docs/MIROVA_DIVERGENCES.md:2385`.
- **Qué pasa**: «caja de 5 km igual para todos» es fiel a C16 p. 189, pero el código dice que la ROI se mueve y
  redimensiona por volcán (H:120-125), y R2 (pieza 4) muestra que Cordón Caulle necesita otra caja. La sección no
  tiene marca S158.
- **Cómo se ve en el tablero**: invisible; puede inducir a medir la caja centrada como «la de MIROVA».
- **Confianza**: CONFIRMADO. **Gravedad**: 2.

## 6. Lo que no pude medir

- Campus et al. 2022, Campus 2024, la tesis de Massimetti, Coppola 2019 y 2023: no estaban en mi asignación; si
  describen VIIRS 375 o la ROI, pueden cambiar las columnas CALLA.
- Si el MODIS operacional de hoy sigue al código de VIIRS 750 o a Coppola 2016a en los 7 pasos distintos: ninguna
  fuente lo dice. Se puede medir con el OSF (Tot_Lmir_bk por fila contra media de vecinos y contra interpolación), no
  lo hice.
- Que la versión compacta del `.m` sea la operacional (declaración del autor).
- El banner NRT (NONE, LOW, MODERATE, HIGH) y su corte: no aparece en ninguna de las cuatro fuentes.
- El mecanismo de H6.

## 7. VERIFICADO LIMPIO

- **Tabla 1 de Coppola 2026 contra el OSF v2.5**: los seis umbrales de VRP (MODIS 10^5 / 5 × 10^7, VIIRS 750 5 × 10^6
  / 5 × 10^7, VIIRS 375 10^4 / 5 × 10^7 W, noche / día) se cumplen en el 100 % de las filas, y el mínimo de cada grupo
  es exactamente el umbral (`python osf_contra_tabla1.py`). Consecuencia que conviene recordar: en el OSF, VIIRS 750
  nocturno parte en 5 MW.
- **Coeficientes y áreas de la Tabla 1 de Coppola 2026** (18,9 / 19,7 / 18 y 10^6 / 5,6 × 10^5 / 1,4 × 10^5 m²):
  identidad 100,00 % bajo 50° en los tres sensores (mismo script). Coinciden con `CLAUDE.md:108-110`.
- **Suma de todos los alertados**: C16 ec. 8, CAP ec. 13, SD26 p. 6 y el código dicen lo mismo; D32 está bien parada.
- **Sin recorte del exceso**: C16 ec. 6 y V:85 coinciden; el recorte de producción es nuestro (D25).
- **Sin compuerta de temperatura**: C16 p. 187 y el código coinciden; D22 está bien parada.
- **Grilla 50 × 50 km centrada en la cumbre GVP y UTM**: C16 p. 183 y SD26 p. 5; el ejemplo es 67 × 67 de 750 m.
- **Caja de cumbre del ejemplo**: BOX 2 de 7 × 7 celdas en filas y columnas 30 a 36, BOX 1 de 350 celdas
  (`box_ejemplo_salida.txt`, `scipy.io.loadmat` sobre `Example/VIIRS750_example.mat`; cenit 7,75°, noche).
- **μ y σ de toda la escena, ETI por regresión cuadrática, Test 1 que sale del fondo, borde excluido**: C16 y código
  coinciden.
- **Ninguna fuente corrige por cenit** ni menciona zonas de agregación (búsqueda en los cuatro PDF y páginas
  renderizadas de C16 p. 197, CAP pp. 347-348, SD26 pp. 8 y 10).
- **El archivo `_9.pdf` no es el capítulo de Coppola**: ya documentado en el repo, no hay que volver a mirarlo.

## Archivos

Scripts y salidas en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\p1\`: `buscar.py`, `buscar_rango.py`,
`render.py`, `osf_contra_tabla1.py` y `_salida.txt`, `osf_maxdist_detalle.py` y `_salida.txt`,
`matriz_c16_vs_codigo.csv`, `contar_matriz.py` y `_salida.txt`, `box_ejemplo_salida.txt`, `png\` (páginas renderizadas).
