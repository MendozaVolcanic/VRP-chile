# S158: el código operacional de MIROVA (VIIRS 750) contra nuestro detector

> **Estado: HALLAZGO e INFORME, sin código de producción.** S158, 2026-10-21. No toca `pipeline/` (A45) ni despacha
> nada. El código de MIROVA se bajó con permiso de Nicolás (2026-10-21) y se guarda tal cual, con su licencia MIT, en
> `experiments/_s158_d17_diseno/osf_codigo_mirova/` (hashes verificados contra OSF en `bajar_codigo_osf_salida.txt`).
> Las citas de nuestro código se comprobaron leyendo cada línea; las del código de MIROVA se dan como
> `archivo.m:línea`. Lo que es lectura propia lleva **[LECTURA PROPIA]** o **SOSPECHA**.

## 0. En una pantalla

**El hallazgo.** Desde el **2026-07-24** MIROVA publica en su repositorio OSF (`https://doi.org/10.17605/OSF.IO/ZM62W`,
carpeta `MIROVA_Code_Repository`, versión 1.0, licencia MIT, autor Diego Coppola) el código MATLAB de su detección y
de su VRP **para VIIRS 750 m**, con una matriz de ejemplo. Lo anuncia Coppola et al. 2026 (Scientific Data), p. 21,
«Code Availability»: «Custom code implementing the scientific core of MIROVA, the hotspot-detection algorithm used to
identify thermally anomalous pixels, was developed in MATLAB R2024 and is publicly available». El proyecto no lo
sabía: `docs/DATA_SOURCES.md` §3 decía «NO EXISTE código público» (verificado en S17, cierto entonces) y la lectura
del manuscrito de S141 (afirmación 4.44) dio por hecho que no había implementación de referencia.

**Lo que cambia.** Por primera vez la réplica tiene contra qué compararse que no sea un texto. En 13 puntos del
detector de VIIRS 750: **3 iguales, 10 distintos** (§3). Los distintos caen en tres familias:

1. **El paper lo decía y no lo seguimos** (5): retirar los píxeles del Test 1 del fondo (GAP #A), que el Test 1 sea
   alerta directa (D23), la compuerta de 3 K (D22), el refit iterativo (D29) y el recorte de ΔL a cero.
2. **El paper callaba y supusimos** (3): K1 de VIIRS 750 (-0,7 y no -0,8), el mínimo de dNTI fuera de la cumbre
   (0,02 y no 0,01) y el filtro de píxel frío y de escena incompleta. Usamos la Tabla 1 de MODIS para VIIRS porque
   Campus 2022 no publicó los suyos; el código revela que eran otros.
3. **El paper y el código no dicen lo mismo, y seguimos al paper** (3): la media local de 8 vecinos (el código usa
   los 9 de la ventana de 3 × 3, central incluido), el fondo del VRP (el paper dice media de los que rodean; el código
   interpola linealmente bajo un hueco dilatado) y el piso de -0,1 (el paper lo pone en dNTI y en dETI; el código
   sólo en el NTI).

**Lo que acertamos**, y ahora está confirmado por el código: la conectiva `max` de K (#850), los umbrales de la
cumbre (5σ y 0,003), el mínimo de ETI fuera (0,01), μ y σ de toda la escena, la regresión cuadrática, el coeficiente
1,97 × 10⁷ con el área nominal fija de 0,5625 km², y que MIROVA suma **todos** los píxeles alertados de la pasada (D32,
A10 rebajada en S147).

**Urgente para Nicolás** (⚠️ actualizado por F5: el run terminó con falla a las 13:55 UTC en su segundo intento, le
falta el 2026-10-18 entero y su métrica de magnitud da MEJORA con un brazo placebo; ver `experiments/_s158_audit/f5/INFORME.md`):
el brazo del A/B de D25 (run 39530508296) calcula el
fondo como la media de los vecinos no alertados de la ventana de 3 × 3; el código de MIROVA **excluye justo esos
vecinos** (agranda el hueco de los alertados con un cuadrado de 3, 5 o 7 celdas de lado, o sea 1, 2 o 3 celdas hacia
cada lado) e interpola por debajo, sin recortar (§4.3). El A/B sigue
midiendo algo útil, pero si D25 cumple no sería la adopción del fondo de MIROVA. Decisión tuya (§7).

## 1. Qué publicaron, dónde y cuándo

| repositorio | qué tiene | fecha | URL |
|---|---|---|---|
| OSF zm62w, `MIROVA_Code_Repository` | detección y VRP de VIIRS 750 (MATLAB), ejemplo `.mat`, README, MIT, CITATION | 2026-07-24 | https://osf.io/zm62w/ |
| OSF zm62w, `MIROVA Dataset v2.5` | `VRP_GLOBAL_ARCHIVE_2025.csv` (98,6 MB), `.sql` (138 MB), `MIROVA_Database_Schema_v2.5.docx` | 2026-03-05 | ídem |
| OSF zm62w, `MIROVA Dataset v1.0` | base MODIS 2000-2020 por volcán, paneles, ReadMe | 2023 | ídem |
| OSF jepv6 | Vulcano 2021-2023, **VIIRS 375 m procesado por MIROVA** (S1, S2, Read me) | 2024-02 | https://osf.io/jepv6/ |
| OSF j5pdx | VRP de Stromboli 2000-2024, MODIS y VIIRS, con codebook | 2025-08 | https://osf.io/j5pdx/ |
| OSF zdbyq | Stromboli, VRP SWIR (Sentinel-2, Landsat) | 2024-06 | https://osf.io/zdbyq/ |
| OSF 4cqrf | Piton de la Fournaise, tasas de efusión (Campus et al., JGR 2024JB030962) | 2024-11 | https://osf.io/4cqrf/ |
| OSF wv8yt | póster de Campus 2021 sobre VIIRS | 2021-04 | https://osf.io/wv8yt/ |

Barrido el 2026-10-21 (scripts de OSF en esta sesión; `bajar_codigo_osf.py` para la descarga): los proyectos públicos
de los cinco autores de zm62w (Coppola, Laiolo, Campus, Massimetti, Aveni) son exactamente esos siete. **GitHub**: ningún
repositorio del grupo (`gh search repos MIROVA`; el único relacionado es nuestro `Mirova-v1`). **Zenodo**: nada (el
`10.5281/zenodo.4545877` que cita Coppola 2026 es la base de deformación COMET). **mirovaweb.it**: no tiene página de
noticias; la página «Explore Archive» trae una sección «Resources» que enlaza a OSF zm62w, al paper de Scientific Data
y a la guía de usuario. Hay además una página «Trend Analysis» (`NRT/zscoretrend.php`, nivel de actividad por puntaje z
en 178 volcanes) que no estaba en `docs/DATA_SOURCES.md`.

**Dónde se entera uno de lo nuevo**: no hay canal de anuncios. El único registro con fecha es el historial de
actividad del proyecto OSF (`https://api.osf.io/v2/nodes/zm62w/logs/`), donde quedó el alta de la carpeta de código el
2026-07-24 08:58 UTC. **[LECTURA PROPIA]** Conviene vigilarlo: un aviso semanal que compare ese historial contra el
último visto cuesta una llamada a la API.

**Por qué sólo VIIRS 750.** No lo explican. El README lo presenta como «a compact MATLAB implementation of the core
MIROVA workflow for resampled VIIRS M-band observations at 750 m» y Coppola 2026 p. 5 remite a «the hotspot-detection
code used by MIROVA», en singular. Campus 2022 (p. 7, §3.2) dice que el algoritmo de VIIRS «is the same used for MODIS»
con pasos «slightly modified [...] and adapted to VIIRS». **SOSPECHA**: publicaron un sensor como ejemplar de un único
algoritmo cuyos parámetros cambian por sensor. **No está publicado**: el código de MODIS, el de VIIRS 375, ni el
remuestreo, la geolocalización, la nube o la cadena NRT («standard and readily reproducible but are specific to the
MIROVA infrastructure and are not distributed», Coppola 2026 p. 21).

## 2. Cómo leer este código (advertencias)

- ⚠️ **Auditoría S158, frente F6** (`experiments/_s158_audit/f6/INFORME.md`): sobre 50° de cenit el VRP que MIROVA publica
  en VIIRS 750 no es el que da este código en el 24 % de las filas del OSF v2.5 (mediana 0,51 del VRP del código; escalón
  exacto en 50°; nunca bajo 50°, nunca en VIIRS 375 ni MODIS). El código publicado no es toda la cadena. Y ningún
  resultado publicado pone a prueba sus umbrales de detección: para eso falta una pasada débil.

- Es una versión **compacta** («reproduces the essential scientific calculations and is not the complete operational
  MIROVA near-real-time processing chain», README). Dice conservar del operacional las constantes de Planck, las
  longitudes de onda, el orden de concatenación de las alertas y el uso de 3,14 en vez de π. Que lo demás sea idéntico
  al operacional es **declaración del autor**, no algo que podamos comprobar.
- **Los comentarios rotulan al revés las regiones.** El código llama «ROI 1» a la región central conservadora y «ROI 2»
  a la extendida sensible. La matriz de ejemplo dice otra cosa: la clase 2 es una caja de 7 × 7 celdas (5,25 km)
  centrada en la celda central de la grilla de 67, que recibe los umbrales sensibles; la clase 1 es un anillo de 21 × 19
  celdas alrededor, y la clase 0 el resto, las dos con los umbrales conservadores. Coincide con el paper (la cumbre, una
  caja de 5 × 5 km, con umbrales más bajos). Manda el dato.
- El código dice que las ROI «can be shifted, reshaped or resized» por volcán, para seguir la actividad esperada o
  excluir volcanes vecinos. La variación por objetivo está en la geometría, como ya decía `docs/MISSION.md`.
- El ejemplo es una pasada de NOAA-20 del 2023-05-19 casi a nadir (7,8°): no sirve para la firma del remuestreo (D17).

## 3. Punto por punto, VIIRS 750 de noche

MIROVA: `MIROVA_VIIRS750_hotspot_detection.m` (H) y `MIROVA_VIIRS750_VRP.m` (V). Nuestro: `pipeline/process_viirs_mod.py`
(pvm), `pipeline/detection_context.py` (dc), `pipeline/profiles/mirova_equivalent.yaml` (Y), con los valores efectivos
leídos de `pipeline.profile` con el perfil `mirova_equivalent`.

| # | qué | MIROVA | nosotros (producción, K) | |
|---|---|---|---|---|
| 1 | Test 1 (NTI absoluto) | K1 = **-0,7** (H:178); sus píxeles son **alerta directa** (H:245) y **salen del fondo** de los tests contextuales (H:276, H:328) | K1 = **-0,8** (Y:47, pvm:481); no son alerta directa (el primer pase reemplaza la máscara); no salen del fondo (`ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`) | DISTINTO |
| 2 | fondo local del contraste | media de la ventana de 3 × 3 **con el píxel central**, sobre la población sin alertas (H:281 a 287) | media de los **8 vecinos sin el central** (`_nanmean_8neighbors_fast`, dc:150 y siguientes) | DISTINTO |
| 3 | umbrales | `max(μ + Nσ, mínimo)`; cumbre 5σ, 0,003 en NTI y ETI; fuera 10σ, **0,02 en NTI** y 0,01 en ETI (H:180 a 187, 306 a 312, 376 a 382) | `max` (K); cumbre 5σ, 0,003 en los dos; fuera 10σ, **0,010 en los dos** (pvm:884 a 900; `DNTI_CONTEXTUAL_C1_SCENE = 0.01`) | conectiva y cumbre IGUAL; **mínimo de NTI fuera DISTINTO** |
| 4 | μ y σ del contraste | toda la escena de 67 × 67 sin el borde (H:303, 304), desviación con N-1 | caja de semilado `radius_km` sobre el **barrido nativo** (sin remuestreo, D17), desviación con N | DISTINTO (por D17; el N-1 es despreciable) |
| 5 | piso de -0,1 | sólo en el contraste de NTI (H:298) | en dNTI y en dETI, como dice el paper (Coppola 2016a p. 5, renderizada) | DISTINTO; seguimos al paper |
| 6 | compuerta `bt > t_bg + 3 K` | **no existe** | **activa** en el primer pase de VIIRS 750 y MODIS (dc:546; `apply_bt_gate` sólo se pasa en VIIRS 375, `process_viirs.py:1327`) | DISTINTO (D22) |
| 7 | regresión NTI esperado contra NTI | un solo `polyfit` de grado 2 sin las alertas (H:328 a 345) | refit iterativo a 3σ, con los alertados dentro (D29) | DISTINTO |
| 8 | constantes de Planck | h 6,6256e-34, c 2,9979e8, k 1,38e-23; 4,05 y 10,763 µm (H:144, 145, 410 a 412) | CODATA (`pipeline/constants.py:21-22`); mismas longitudes de onda | constantes DISTINTO (efecto chico, sólo cerca del umbral) |
| 9 | píxel frío y escena incompleta | BT de M15 ≤ 200 K pasa a NaN; escena rechazada con la mitad o más de NaN (H:150 a 154, 163 a 167) | no existe | DISTINTO |
| 10 | segundo pase | excluye absolutas y primer pase y **recalcula todo, también la regresión** (H:228 a 235) | excluye sólo el primer pase y **reusa el ETI del primero** (pvm:916) | DISTINTO (D26) |
| 11 | qué se publica | la **unión** de todas las alertas de la pasada (H:241 a 248) | el cúmulo `vent_anchored`, con el modo de un píxel y el tope D9 de 5 MW (`store.py`) | DISTINTO (D32, D8', D9) |
| 12 | fondo del VRP | M13 con los alertados y una **dilatación** por un cuadrado de 3, 5 o 7 celdas de lado (npix ≤ 4, ≤ 30, > 30) en NaN, rellenado por **interpolación lineal 2D** (`fillmissing2`); ΔL = Σ(L − L_bk) **sin recorte** (V:64 a 85) | escalar: Planck de la **mediana** de la BT de M13 en el anillo de 5 a 25 km; **recorte ΔL ≥ 0** por píxel (pvm:1056) | DISTINTO (D25) |
| 13 | ROI | **cajas en celdas**: cumbre de 7 × 7 (5,25 km) | círculo de `inner_radius_km`, 3 a 20 km según el volcán | DISTINTO (D18) |

Iguales sin discusión: el coeficiente (1,97 × 10⁷ por 0,5625 km², V:88 a 91, contra 19,7 por 562.500 m² en pvm), las
longitudes de onda y la conectiva `max`.

## 4. Dónde nos equivocamos de juicio

La pregunta útil no es cuántas diferencias hay sino **por qué** cada una sobrevivió. Separo tres causas, porque piden
remedios distintos.

### 4.1 El paper lo decía y no lo seguimos

| divergencia | lo que dice el paper (Coppola 2016a, `sp426_5.txt`) | lo que decidimos y cuándo | el código |
|---|---|---|---|
| **GAP #A**: retirar los píxeles del Test 1 del fondo | «Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded (unsuitable) for further steps» (`sp426_5.txt` l. 298 y 299) | S115 lo declaró «MISLABEL, no era un gap real»; S128 lo reabrió | los excluye (H:276, 328) |
| **D23**: el Test 1 como alerta directa | la misma frase: los marca «active» | nunca fue camino de detección por píxel; con K ni siquiera corre el integrado | son alerta (H:245) |
| **D22**: compuerta de 3 K | Tests 2 y 3 sin condición de temperatura (p. 7) | se mantuvo; el A/B de S143 dio NO ADOPTAR con el Test 1 encendido y `min` (rebajado por AUDIT_S155 F4-05) | no existe |
| **D29**: refit a 3σ | un solo ajuste (ec. 4) | refit propio, sin flag | un solo `polyfit` |
| **recorte de ΔL a cero** | ec. 6 sin recorte | S26: «clip ΔL ≥ 0, física de Wooster» | no recorta |

**Patrón.** Las cinco son decisiones que se tomaron leyendo el texto y que se apartaron de él con una razón propia
(«mejora el fondo», «paridad», «física»), o que una auditoría cerró sin medir. Es exactamente lo que A95 y A111
describen: un cierre que hereda una lectura. El código no aporta nada que el paper no dijera; sólo quita la excusa.

### 4.2 El paper callaba y supusimos

| | lo que hicimos | lo que hace MIROVA en VIIRS 750 | por qué lo supusimos |
|---|---|---|---|
| K1 | -0,8 (la Tabla 1 del paper, que es de **MODIS**) | -0,7 | Campus 2022 dice que adaptó el algoritmo a VIIRS sin publicar los valores; su Tabla 1 (p. 6) sólo trae características del sensor |
| mínimo de dNTI fuera de la cumbre | 0,010 (Tabla 1 de MODIS, un solo C1 para dNTI y dETI) | **0,02** para dNTI, 0,01 para dETI | ídem |
| píxel frío ≤ 200 K y escena con la mitad de NaN | nada | descartados | no figura en ningún paper leído |

**Patrón.** Aquí no hubo mala lectura: hubo una extrapolación razonable de MODIS a VIIRS que resultó falsa en dos
números. La lección es otra: **cuando un paper dice «adaptado» sin dar valores, el valor heredado es una conjetura, y
hay que marcarlo como tal** en el perfil, no como «fiel». Las dos cifras tocan de lleno la sobre-publicación (A98): un
mínimo de dNTI del doble fuera de la cumbre y un K1 más alto hacen que, fuera del cráter, MIROVA publique menos que
nosotros. Cuánto, no está medido.

### 4.3 El paper y el código difieren, y seguimos al paper

| | el paper | el código |
|---|---|---|
| fondo local | «the average (arithmetic mean) of the eight neighbouring pixels» (`sp426_5.txt` l. 242 a 245) | media de la ventana de 3 × 3 con el central (H:281 a 287). Efecto: el contraste de MIROVA es 8/9 del nuestro para el mismo píxel; μ y σ escalan igual, así que sólo pesa en los mínimos fijos, que en nuestras unidades equivalen a 9/8 de los de MIROVA |
| fondo del VRP | «the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)» (l. 357 a 359) | interpolación lineal bajo un hueco dilatado 3, 5 o 7 celdas según el tamaño de la anomalía (V:64 a 81) |
| piso de -0,1 | «all the pixels with dNTI or dETI < −0.1» (p. 5, renderizada en S158; la capa de texto, l. 273, lo corrompe a `,20.1`) | sólo en el NTI (H:298) |

**Patrón.** Aquí no nos equivocamos: el texto y el programa no dicen lo mismo. Lo que sí estuvo mal fue **suponer que
el paper describe el programa**. La regla MISSION 1 pide cita verbatim del paper como autoridad; con el código
publicado, la autoridad sobre «qué hace el sistema» es el código. Decisión de Nicolás (§7).

⚠️ **REFUTADO por la auditoría S158 (F3 H5 y F5-06; pendiente del verificador)**: la lectura física del párrafo que
sigue («el halo lleva calor y restarlo se come parte del exceso») no tenía respaldo y el único caso medido dice lo
contrario. En Etna el fondo de vecinos del brazo D sube el VRP (+2,65 % contra MIROVA) y sacar la dilatación también lo
sube (+0,8 %): los vecinos inmediatos están **más fríos** que el fondo interpolado. En VIIRS 375 nuestro fondo de 8
vecinos queda 3 a 8 % bajo el de MIROVA (F3). Lo que sí sigue en pie: el brazo D no es el fondo de MIROVA. Texto
original conservado:

El fondo del VRP es el caso más delicado, porque **D25 lo diseñamos leyendo el paper**: «media de los vecinos no
alertados», con ventana que crece hasta 7 × 7 sólo si no hay ninguno. El código hace casi lo contrario: **aparta el
halo** inmediato de la anomalía (la dilatación) y estima el fondo interpolando desde más afuera. Físicamente tiene
sentido: el halo de un foco sub-píxel todavía lleva calor (la huella de un píxel caliente se derrama en los vecinos),
y restarlo como fondo se come parte del exceso. D25 toma justo ese halo.

### 4.4 Lo que acertamos

La conectiva `max` (la decisión más discutida de K: S136 midió que `min` no reproduce a MIROVA y K la adoptó en
#850), los 5σ y 0,003 de la cumbre, el mínimo de ETI fuera (0,01), μ y σ de toda la escena (S114), la regresión
cuadrática, el coeficiente y el área nominal (S14, A66), y la suma de todos los alertados (D32, verificada en S147
renderizando tres papers). Son las decisiones que se tomaron midiendo contra la referencia de MIROVA, no leyendo.

## 5. ¿Se puede trasladar a MODIS y VIIRS 375?

**La estructura, sí, con apoyo citable.** Campus 2022 p. 7: el algoritmo de VIIRS «is the same used for MODIS»;
Coppola 2026 p. 5 habla de un solo «hotspot-detection code used by MIROVA» para los tres sensores. Lo estructural no
depende del sensor: el orden de los pasos, el Test 1 como alerta que sale del fondo, la media de 3 × 3 con el central,
`max(μ + Nσ, mínimo)` por región, el segundo pase que recalcula estadísticos y regresión, el filtro de escena, la unión
de alertas y el fondo interpolado sin recorte.

**Los números, no.** El código de VIIRS 750 demuestra que MIROVA cambió dos números respecto de la Tabla 1 de MODIS, así
que ningún número de VIIRS 750 vale por sí solo para VIIRS 375:

| parámetro | MODIS | VIIRS 750 | VIIRS 375 |
|---|---|---|---|
| K1 noche | -0,8 (paper, Tabla 1) | -0,7 (código) | **SIN DATO** |
| mínimo de dNTI fuera | 0,01 (paper, Tabla 1) | 0,02 (código) | **SIN DATO** |
| mínimo de dETI fuera | 0,01 (paper) | 0,01 (código) | **SIN DATO** |
| cumbre (5σ, 0,003) | paper | código | **SIN DATO**, probablemente igual |
| caja de cumbre | 5 × 5 km (paper) | 7 × 7 celdas = 5,25 km (código) | ¿13 o 14 celdas? **SIN DATO** |
| dilatación del fondo | ¿3, 5, 7 celdas? **SIN DATO** | 3, 5, 7 celdas | **SIN DATO**; en celdas de 375 m la misma cifra cubre la mitad de terreno |
| filtro de 200 K | ¿banda 31? **SIN DATO** | M15 | ¿I5? **SIN DATO** |

Para MODIS, además, la Tabla 1 del paper es de 2016; que siga vigente en el operacional de hoy es supuesto. **[LECTURA
PROPIA]** El orden de trabajo que se desprende: (1) adoptar lo estructural en los tres sensores, que tiene cita; (2) los
números de VIIRS 750 sólo en VIIRS 750; (3) para VIIRS 375 y MODIS, medir los números contra la referencia de MIROVA
(A115) o pedirlos (el autor da su correo en la web).

### 5.1 Lo que dicen de VIIRS 375 los datos publicados de Vulcano (OSF jepv6)

El archivo S1 de Campus et al. 2024 (OSF jepv6, sin licencia declarada: leído, no copiado al repo) trae, para cada una
de las 354 alertas de VIIRS 375 de MIROVA en Vulcano entre 2021 y 2023, el cenit, el azimut, Npix, la radiancia
caliente sumada, la de fondo y el VRP (`experiments/_s158_d17_diseno/jepv6_cenit.py`, salida al lado):

- **El coeficiente de VIIRS 375 queda confirmado**: VRP / (L_hot − L_bk) = 2.531.250 en las 354 (18,0 × 140.625 m²,
  el de la calibración S14). MIROVA usa el área nominal fija también en banda I.
- **L_MIRhot es la suma sobre los Npix** (la radiancia por píxel con Npix > 1 es la misma que con Npix = 1).
- **Npix casi no crece con el cenit** (ρ = +0,07; mediana 1 hasta 40° y 2 sobre 40°), y **el VRP de MIROVA cae** con
  el ángulo (1,28 a 0,72 relativo a su propia mediana móvil). En Chile pasa lo mismo y depende del volcán: ver
  `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6.

Para VIIRS 375 no da los umbrales de detección, pero confirma la parte de la magnitud que el código de VIIRS 750
no cubre.

## 6. Qué cambia en los frentes abiertos

| frente | antes | con el código |
|---|---|---|
| D25 (A/B en curso) | fondo por vecinos no alertados | el brazo no es el fondo de MIROVA; falta un brazo con dilatación más interpolación y sin recorte |
| D22 | NO ADOPTAR de S143, rebajado | el literal no tiene compuerta; es divergencia confirmada |
| D23, GAP #A | abiertos | confirmados por el código |
| D26 | sin medir bajo `max` | el segundo pase de MIROVA recalcula también la regresión |
| D29 | menor | confirmado |
| D32, D8', D9 | abiertos | MIROVA publica la unión de alertas, sin cúmulo ni tope |
| D18 | caja con veto en D1 | MIROVA usa cajas en celdas |
| D17 | diseño (`docs/DISENO_D17_REMUESTREO_UTM.md`) | el remuestreo no se publica; las entradas se llaman `ZI_M13` y `ZI_M15` («resampled»), el nombre clásico de la salida de `griddata` en MATLAB (**SOSPECHA**, coherente con la firma lineal de sus TIF) |
| divergencias nuevas | | K1 de VIIRS 750, mínimo de dNTI fuera, 3 × 3 con central, filtro de 200 K y de escena, constantes de Planck, piso de -0,1 sólo en NTI |

**Para D17 en particular**, el código abre la mejor Fase 0 posible: con un port a Python de estas dos funciones como
**oráculo**, se corre el detector **de MIROVA** sobre nuestras matrices remuestreadas y se compara con lo que MIROVA
publicó en esa pasada. Si coincide, nuestro remuestreo es el suyo; si no, la diferencia es del remuestreo y no del
detector. Separa los dos problemas por primera vez.

## 7. Recomendaciones y decisiones para Nicolás

1. **D25.** El run 39530508296 está en cola. Dejarlo terminar da un dato útil (cuánto mueve un fondo por vecinos),
   pero si cumple **no** es la adopción del fondo de MIROVA. Recomiendo dejarlo correr y no adoptar D25 sin un brazo
   que replique `MIROVA_VIIRS750_VRP.m` (dilatación más interpolación y sin recorte), al menos en VIIRS 750.
2. **¿El código pasa a ser la autoridad sobre el paper para VIIRS 750?** Recomiendo sí, con la advertencia del §2: es
   la declaración del propio autor sobre qué hace su sistema, y es más reciente que el paper. Toca la regla MISSION 1.
3. **Un port a Python verificado** de las dos funciones (`experiments/`, no `pipeline/`), con pruebas sobre la matriz
   de ejemplo y con el VRP impreso por `run_example.m` como control, si alguien con MATLAB puede correrlo una vez (el
   repositorio no trae la salida esperada).
4. **Un A/B «código MIROVA» en VIIRS 750**: lo estructural más los números del código, contra K. Pre-registro aparte.
5. **Preguntar al autor** por los números de MODIS y VIIRS 375 (§5), y por el interpolador del remuestreo: el
   borrador de S139 queda actualizado (Anexo A). Mandarlo es decisión tuya.
6. **Vigilar el historial de OSF** (§1) para enterarse de la próxima publicación.
7. **Bajar los datos de jepv6** (Vulcano en VIIRS 375 procesado por MIROVA): puede traer conteos o posiciones por
   píxel de VIIRS 375, lo que más falta para la paridad de ese sensor. Pide tu permiso de descarga.

## 7 bis. Plan revisado (Nicolás, 2026-10-21: «continua con todo lo que recomiendes, estas nuevas cosas cambian lo que estabamos haciendo»)

Lo que cambia de fondo: hasta hoy cada frente de paridad era una hipótesis sobre qué hace MIROVA, sacada del texto.
Para VIIRS 750 ahora hay un programa contra el cual medir, y para la magnitud de VIIRS 375 hay datos con Npix y
radiancias (OSF jepv6). El orden que recomiendo, y lo que ya está en marcha:

| # | frente | estado | por qué en este orden |
|---|---|---|---|
| 1 | port a Python del código de VIIRS 750 como oráculo | **en marcha** (sesión «Port a Python del detector MIROVA V750») | todo lo demás se mide con él |
| 2 | D25 | el A/B en cola sigue; **en marcha** la adenda con el fondo del código (sesión «Adenda D25») | el fondo es la diferencia de nivel más directa de la magnitud |
| 3 | A/B «detector del código» en VIIRS 750: K1 -0,7, mínimo de dNTI 0,02 fuera, 3 × 3 con central, Test 1 como alerta que sale del fondo, sin compuerta, segundo pase con regresión, filtro de 200 K y de escena | pre-registro después del oráculo | ataca la sobre-publicación con números que salen de MIROVA y no de un umbral elegido (A115) |
| 4 | D32 y lo que se publica (unión de alertas, sin cúmulo, sin tope) | después de 3 | es lo que hoy separa nuestro nivel del de MIROVA aun con el detector igual |
| 5 | D17 Fase 0: reproducir los TIF de VIIRS 375 y correr el oráculo sobre matrices remuestreadas en VIIRS 750 | después de 1 | con K la pendiente que D17 puede cerrar es como mucho un 23 % (§3.6 del diseño), así que va detrás del nivel |
| 6 | MODIS: geolocalización con MxD03, luego bow tie (Liu et al. 2008, Coppola 2012 p. 4) | sin cambio | prerrequisito de cualquier remuestreo de MODIS |
| 7 | trasladar lo estructural a MODIS y VIIRS 375 | después de 3, con su propio A/B | la estructura tiene cita; los números se miden contra la referencia |

**Lo que se deja de hacer**: diseñar umbrales de VIIRS 750 por cuenta propia; adoptar el brazo D de D25 como «el
fondo de MIROVA»; implementar D17 antes del oráculo.

Todo lo que toque `pipeline/` sigue necesitando tag defensivo, pre-registro sellado y tu «sí» (A45).

## Anexo A. El correo al autor

Ya existía un borrador (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`, S139, ajustado en S142 y S146, 14 preguntas, sin
enviar). En S158 se le agregó un ajuste: qué preguntas contesta ya el código de VIIRS 750, cómo reformularlas para
MODIS y VIIRS 375, y tres preguntas nuevas (números de MODIS y VIIRS 375, interpolador y origen de la grilla, media
local de 3 × 3). Enviarlo es decisión de Nicolás, desde su cuenta.

## 8. Lo que no se pudo verificar

- Que la versión compacta sea idéntica al operacional (declaración del autor).
- El VRP que imprime el ejemplo (no tenemos MATLAB y el repositorio no trae la salida esperada).
- Cuánto cambia la publicación nuestra con cada diferencia: nada de lo de este informe es una medición de efecto.

## 9. Reproducir

```
python -I experiments/_s158_d17_diseno/bajar_codigo_osf.py <carpeta destino vacía>
```

La comparación del §3 se hizo leyendo los dos códigos; las líneas de nuestro lado se comprobaron una por una el
2026-10-21 sobre `main` en `8471add4`.
