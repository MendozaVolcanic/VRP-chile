# Diseño D17: remuestreo a la grilla UTM de MIROVA

> **Estado: DISEÑO, sin código de producción.** S158, 2026-10-21, rama `s158-d17-diseno`. No toca `pipeline/` (A45)
> ni despacha nada. Todo lo que aquí se propone para el pipeline necesita tag defensivo, pre-registro sellado y el
> «sí» escrito de Nicolás. Lo que es cita del canon va entre comillas con su localizador y se leyó **renderizando la
> página a imagen** en esta sesión (A95). Lo que es decisión propia lleva la marca **[DECISIÓN PROPIA]**. Lo medido
> en esta sesión tiene script en `experiments/_s158_d17_diseno/` (regla S91).

## 0. En una pantalla

**Por qué ahora.** Con el detector K la magnitud con el sensor oblicuo sigue corta frente a MIROVA, y la parte que
D25 (fondo por vecinos) no explica apunta a la geometría: el verificador de #880 vio a VIIRS 375 marcar ~310 K donde
M13 marca 273 K en la pasada del 18-oct 06:48 de Chillán (SOSPECHA, no medida), y #879 dejó el efecto del lado del
barrido como algo del procesamiento de MIROVA. D17 (MIROVA recorta y remuestrea cada escena a una grilla UTM regular
y nosotros no) es la gran divergencia literal que sigue abierta.

**Tres hallazgos de esta sesión, medidos sobre los GeoTIFF UTM que MIROVA publicó el 14 y 15 de septiembre (A106)**,
que cambian el diseño respecto de lo que D17 daba por hecho:

1. **El centro de la grilla de MIROVA NO es `mirova_center`.** En 8 de los 11 Tier A el `lat`/`lon` de
   `volcanoes.yaml` cae a unos **62,5 m al este y 62,5 m al norte** del centro de la grilla (62 a 63 m medidos), el mismo vector en los 8; `mirova_center`
   (derivado en S80 de los KMZ, que son reproyecciones geográficas) cae a 46 a 310 m. La premisa de D17 («F70 se
   centró en el punto equivocado, `get_grid_center` es el bueno») **cae en esos 8**: F70 usó el punto más cercano.
   Cablear `get_grid_center` tal como está no es el arreglo.
2. **La grilla es UTM verdadera** (EPSG:32719, y 32718 en Chaitén y Cordón Caulle), con 1,3 a 1,9° de giro respecto
   del norte geográfico en el sur. Nuestro F70 usa ejes alineados con latitud y longitud: a 25 km del centro la
   partición se corre unos 0,8 km, dos celdas de 375 m.
3. **MIROVA interpola; nuestro F70 deja huecos.** En pasadas de cenit 60 a 65° los TIF de MIROVA no repiten **ningún**
   valor entre celdas vecinas y tienen 9 a 236 celdas vacías de 17.956. A ese ángulo el vecino más cercano repetiría
   valores en casi la mitad de los pares y el remuestreo de F70 (`pipeline/regrid.py`, que pone cada muestra en la
   celda que contiene su centro) dejaría vacía entre el 43 y el 77 % de la grilla (sintético). F70 además pierde la
   energía del foco con el ángulo igual que la fórmula de hoy (0,23 de la energía nativa con huella de 0,79 km). El
   docstring de `regrid.py` lo llama «vecino más cercano» y no lo es (A89).

**Recomendación.** (a) Una Fase 0 de sólo lectura que reproduzca los TIF UTM de MIROVA desde nuestro L1B con cada
remuestreo candidato y elija el que los reproduce (A115: se le pregunta a la referencia). Se puede correr ya, porque
no adopta nada. (b) El A/B de adopción (Fase 1) sólo en VIIRS, sobre la base que deje D25, con la grilla leída de los
TIF y el interpolador que gane la Fase 0. (c) MODIS en una Fase 2, después de arreglar su geolocalización (`_interp_geo`,
1 a 3 km de error) y de decidir el bow tie. Decisiones para Nicolás en el §8.

## 1. El fenómeno

Un píxel de satélite no es un cuadrado fijo. Cerca del nadir el de VIIRS banda I mide 375 m de lado; hacia el borde
del barrido se estira a unos 800 m, y el de MODIS pasa de 1 km² a unos 10 km². Un foco de lava o un cráter caliente
casi siempre es **más chico que el píxel**: el sensor no ve el foco, ve la **media de la huella**, foco más roca fría
alrededor. Cuando la huella crece, el mismo foco queda diluido en más roca y el exceso de radiancia del píxel baja en
proporción.

La energía del foco es exceso de radiancia por área. Si el exceso se multiplica por el área **de la huella**, la cuenta
cierra a cualquier ángulo. Si se multiplica por un área fija de nadir, como hacemos hoy (A66, A67), la energía cae con
el ángulo justo en la proporción en que creció la huella. Es la caída que S130 midió (VIIRS 375 de 0,74 cerca del nadir
a 0,25 sobre 50°) y que AUDIT_S155 F5-03 vio aplanarse con «un modelo de área completa». La tarea 1.14 (§3.2) mostró
que parte de esa caída es fondo y la dejó **SIN ATRIBUIR**; este diseño no la atribuye a D17, propone cómo medirlo.

El paper lo dice como motivo del remuestreo (§2): la radiancia de un foco sub-píxel queda integrada sobre un área
variable y eso introduce un error «heredado». Remuestrear a celdas de área constante no inventa energía: reparte la
huella grande en varias celdas chicas, cada una con su área, y la suma vuelve a corresponder al área de la huella.

El segundo efecto es de contexto. Los Tests 2 y 3 comparan cada píxel con sus 8 vecinos. Sobre el barrido crudo, en
un cono nevado oblicuo, esos 8 vecinos son tiras de 800 m que mezclan nieve, roca y valle en proporciones distintas
cada noche. Sobre la grilla son siempre los mismos ocho cuadrados de terreno.

## 2. Lo que dice el canon (renderizado en S158)

**Coppola et al. 2016a, SP426.5** (`documentacion/sp426.5.pdf`, p. 3, columna derecha, sección «Cropping and
resampling of original MODIS granules»):

> «Cropping and resampling of the original Level 1B MODIS data is necessary for two main reasons. First, because high
> scan angles contribute to the growth of the projected ground spatial element (up to c. 10 km² for scan angles of
> 55°: Nishihama et al. 1997). This leads to the radiance of a potential subpixel hotspot being integrated over a
> variable area (depending on the scan angle) introducing an 'inherited' error source in estimating its thermal
> output. Secondly, because the hotspot detection scheme, described below, requires homogenous pixel scale.»

> «Thus, we cropped and resampled (into an equally spaced 1 km grid) the MODIS Level 1B data that fall within a grid
> (50 × 50 km) centred on the volcano's summit (Fig. 1). For this purpose we used the Global Volcanism Program
> volcano database (http://www.volcano.si.edu/) as the reference source for the volcano nomenclature and for the
> summit latitude and longitude.»

Y en la misma página, columna izquierda al pie y derecha arriba, el bow tie va **antes**:

> «The georeferred data were also scanned in order to remove the bow-tie effect that produces the so-called 'scan to
> scan' overlapping at the edge of the swath (Nishihama et al. 1997). Once the effects of invalid and bow-tie related
> pixels had been removed, [...]»

**Coppola et al. 2014, IJRS** (doi 10.1080/01431161.2014.903354; `documentacion/coppola2014_ijrs_strombolian_*.pdf`,
p. 3406, §2.2, tercer párrafo), la única frase del canon que dice qué le pasa a un píxel caliente al remuestrear:

> «This means that one hot-spot pixel, whose area is 2 km² in the original image, becomes two pixels with equal areas
> of 1 km² in the resampled image.»

**Coppola et al. 2013, JVGR 249** (`documentacion/j.jvolgeores.2012.09.005.pdf`, p. 46, Apéndice 2):

> «Pre-processing of the original MODIS granules consists in the removal of the bow-tie effect and resampling into an
> equal area projection with 1 km pixel size.»

**Coppola et al. 2023, Front. Earth Sci. 11:1240107** (`documentacion/feart-11-1240107.pdf`, p. 3, §2.1, final de la
columna izquierda y comienzo de la derecha), el porqué en una línea y el orden:

> «[...] resampled to regular 51 × 51 UTM grids centred on the volcano's summit, as per coordinates provided by the
> Global Volcanism Program. (2023). This step is crucial to ensure that all pixels represent a ground area of 1 km²,
> minimizing the effect of geometrical distortions and making the VRP calculation easier (see Section 2.3). Once the
> scenes are geometrically corrected (i.e., pixels affected by bow-tie distortions are identified and removed;
> Coppola et al., 2010), the MIR and TIR bands are employed to run the hotspot detection algorithm.»

y en §2.3 (misma página, Ec. 2): «where A_pix is the area of the pixel in km² (for resampled MODIS image A_pix =
10⁶ m)». El área de la fórmula es la de la celda remuestreada.

**Campus et al. 2022, Sensors 22:1713** (`documentacion/campus2022_sensors_22_1713.pdf`, p. 7, §3.2, segundo párrafo),
VIIRS M-band, voz activa del sistema NRT:

> «Resampling is performed in a UTM 51 × 51 km grid, centered on the volcano summit (consistent with MODIS-MIROVA
> images) by keeping the nominal resolution of 750 m. This results in matrices of 67 × 67 pixels rather than 51 × 51
> pixels obtained from MODIS (Figures 2 and 3).»

**Aveni et al. 2024, RSE** (`documentacion/Aveni_2024_TIRVolcH_RSE.pdf`, p. 5, §3.2), VIIRS banda I, y la
geolocalización que usa MIROVA:

> «[...] associated geolocation data products (VNP03IMG and VJ103IMG Imagery Resolution Terrain-Corrected
> Geolocation 6-Min L1 Swath 375 m, respectively) [...] The original granules, as per MIROVA workflow, are resampled
> to a regular 134 × 134 UTM grid centred on the volcano summit according to the coordinates provided by the Global
> Volcanism Program (2023).»

**Campus et al. 2024, Bull. Volcanol. 86:25** (`documentacion/s00445-024-01721-z.pdf`, p. 3, columna derecha):

> «The hierarchical elaboration of the MIROVA algorithm, after an initial resampling of the original granule in a
> regular 50×50 km UTM grid, first detects the thermally anomalous pixels (N_pix) by applying spectral and spatial
> filters to the resampled scene.»

Citados por sesiones anteriores, **no re-renderizados en S158**: Fernandina 2025 (Remote Sens. 17:1191, p. 9, §2.3.1,
grilla UTM de 51 × 51 km con coordenadas GVP; S140), y Aveni et al. 2023 (Remote Sens. 15:2528, p. 15, §4.2.1), que
escribe que el remuestreo corrige el efecto del cenit sólo «partially» (S141).

**Lo que el canon NO dice** (y por eso es decisión propia o se mide):

- **El interpolador.** Ningún texto lo nombra. La frase de Coppola 2014 (un píxel de 2 km² se vuelve dos de 1 km²)
  descarta un remuestreo que deje una celda llena y otra vacía, pero es compatible con el vecino más cercano y con
  una interpolación.
- **El método del bow tie** (D28: Coppola 2010 contra la referencia [82] de Aveni 2023, SOSPECHA de S141).
- **El origen exacto de la grilla, la zona UTM y qué hace con un número par de celdas** (134 y 67 no tienen celda
  central; 51 sí). Se midió (§3.1).

## 3. Lo que miden los datos de MIROVA (S158)

Entre el 2026-09-14 06:36 y el 2026-09-15 06:24 MIROVA publicó sus TIF de VIIRS 375 en su grilla UTM nativa (A106).
`experiments/_s158_d17_diseno/grilla_tif.py` baja uno por volcán por la API de GitHub (nunca `git pull` del archivo
de TIF) y lee su georreferencia con rasterio; salida en `grilla_tif_salida.txt`.

### 3.1 La grilla

| volcán | EPSG | convergencia | `lat`/`lon` del yaml | `mirova_center` | `vent` |
|---|---|---|---|---|---|
| Chaitén | 32718 | +1,60° | 89 m (+62, +63) | 310 m | 512 m |
| Nevados de Chillán | 32719 | -1,43° | 89 m (+63, +63) | 300 m | 89 m |
| Copahue | 32719 | -1,34° | 89 m (+63, +63) | 87 m | 89 m |
| Isluga | 32719 | +0,06° | 89 m (+63, +63) | 279 m | 89 m |
| Lastarria | 32719 | +0,21° | 89 m (+62, +63) | 51 m | 89 m |
| Llaima | 32719 | -1,71° | 89 m (+63, +63) | 90 m | 89 m |
| Cordón Caulle | 32718 | +1,87° | 89 m (+62, +63) | 90 m | 7.621 m |
| Villarrica | 32719 | -1,86° | 89 m (+63, +63) | 304 m | 787 m |
| Láscar | 32719 | +0,50° | 225 m | 46 m | 851 m |
| Planchón-Peteroa | 32719 | -0,90° | 1.824 m | 83 m | 1.991 m |
| Tupungatito | 32719 | -0,44° | 2.843 m | 294 m | 4.850 m |

Distancias al centro de la grilla del TIF, en UTM; entre paréntesis (este, norte) en metros. Las 11 grillas son de
134 × 134 celdas de 375,0 m, sin rotación en su propio sistema, y **fijas entre pasadas**: en Láscar, Llaima,
Tupungatito y Villarrica dos TIF de pasadas distintas tienen el mismo origen al decímetro.

**Lectura.** (a) En los 8 volcanes cuyo `lat`/`lon` del yaml parece ser la coordenada GVP redondeada (sin cambios
deliberados), la grilla de MIROVA está centrada unos 62,5 m al oeste y 62,5 m al sur de ese punto (62 a 63 m medidos), siempre el
mismo vector. Es un sexto de celda; el mecanismo (convención de origen, redondeo de la coordenada) **NO está explicado**, pero
la regla se cumple en los 8 a un metro. (b) En Láscar, Planchón-Peteroa y Tupungatito nuestro `lat`/`lon` se movió en
sesiones pasadas (S65, S98) y ya no es el punto de MIROVA; `mirova_center` queda a 46 a 294 m. (c) **Ningún campo del
yaml es la grilla**: `mirova_center` falla por hasta 310 m (casi una celda) en 5 de 11. (d) Que la coordenada de esos
8 sea la de GVP es inferencia (los valores tienen la forma redondeada de GVP); no se consultó GVP en esta sesión.

### 3.2 La firma del remuestreo

En los 15 TIF leídos, **0,0 %** de los pares de celdas vecinas (este-oeste y norte-sur) tienen valor idéntico, hay
17.690 a 17.934 valores distintos de 17.956 celdas, y 9 a 236 celdas vacías (valor ≤ 0 o NaN). Los valores (0,02 a
1,4) tienen el orden de magnitud de la radiancia nocturna a 3,74 µm en W m⁻² sr⁻¹ µm⁻¹; que sea radiancia de I4 y no
otra variable es SOSPECHA. El software declarado en la etiqueta del TIF es MATLAB R2024b, Mapping Toolbox.

Las pasadas son oblicuas: nuestros records de esas mismas pasadas dan cenit del sensor 60,0° (Isluga 06:36), 60,4°
(Llaima 06:42), 63,3° (Tupungatito 06:36), 63,7° (Lastarria 06:36), 64,9° (Láscar 06:36) y 45,6° (Villarrica 15-sep
06:18). Ojo (A106): la hora del nombre del TIF puede no ser la de la pasada; el pareo por hora es razonable porque en
estos casos hay una sola pasada a esa hora, pero no se verificó con la hora de adquisición interna del TIF.

### 3.3 Qué firma deja cada remuestreo (sintético)

`experiments/_s158_d17_diseno/firma_interpolador.py` (salida en `firma_interpolador_salida.txt`) remuestrea un
barrido sintético girado, con un foco sub-píxel en una sola muestra, con tres métodos: **F70** (el de
`pipeline/regrid.py`: cada muestra va a la celda que contiene su centro), **vecino** (cada celda toma la muestra más
cercana a su centro) y **lineal** (interpolación lineal de datos dispersos sobre una triangulación). Extracto, VIIRS
375 (celda 0,375 km):

| huella | método | celdas vacías | vecinas iguales | energía / energía nativa | celdas sobre 0,05 |
|---|---|---|---|---|---|
| 0,38 × 0,38 km (nadir) | F70 | 6,7 % | 0,0 % | 1,02 | 1 |
| | vecino | 0,0 % | 3,3 % | 1,02 | 1 |
| | lineal | 0,7 % | 0,0 % | 1,40 | 3 |
| 0,79 × 0,78 km (borde) | F70 | 77,3 % | 0,0 % | **0,23** | 1 |
| | vecino | 0,0 % | **46,9 %** | 1,13 | 5 |
| | lineal | 1,1 % | 0,0 % | 1,33 | 13 |

VIIRS 750 y MODIS repiten el patrón (MODIS con huella de 4,8 × 2,0 km: F70 deja 89,6 % vacío y 0,10 de la energía).

**Lectura.** Sólo la interpolación lineal deja la firma de MIROVA (§3.2) a 60 a 65° de cenit: ni repite valores ni
deja huecos. El vecino más cercano repetiría casi la mitad; F70 dejaría vacías tres cuartas partes. Es sintético: el
barrido real tiene solape de barridos y huellas que no son rectángulos, por eso la Fase 0 lo mide sobre gránulos
reales. Dos advertencias que el sintético sí deja claras: (1) F70 conserva la energía sólo a nadir y la pierde con el
ángulo igual que el área fija de hoy, así que **el A/B de S124 (D16) no probó un remuestreo que pudiera corregir la
magnitud oblicua**; (2) la interpolación lineal **infla a nadir** (1,40 con un foco aislado de un píxel) y conserva
aproximadamente en oblicuo: el A/B tiene que mirar la magnitud en las dos direcciones y por tramo de cenit.

**Tensión abierta con la tarea 1.14 §3.2**: en el OSF de 2025 el Npix de MIROVA no crece hacia el borde (medianas 3,
5, 5 y 4). Con un umbral fijo de exceso, el lineal haría crecer el conteo (3 a 13 en el sintético). Pero MIROVA no
detecta con umbral fijo sino contra los 8 vecinos, y una interpolación sube también a los vecinos del foco, así que el
conteo contextual puede quedar plano. No se resuelve en el escritorio: la Fase 0 y el A/B miden Npix por tramo de
cenit en cada brazo. Además el OSF es un producto filtrado (A105).

### 3.4 Consecuencias para D17

- La premisa de D17 (centro equivocado, `get_grid_center` como arreglo) **cae en 8 de 11**; en los otros 3 ningún
  campo del yaml sirve. La grilla se toma **medida**, del TIF (A5: los valores de MIROVA son datos).
- F70 tenía tres defectos, y el que D17 nombraba es el menor: **huecos** (dominante en oblicuo), **giro** (ejes
  geográficos en vez de UTM) y, sólo en 3 volcanes, el centro.
- El «NO REABRIR» de D16 queda todavía más acotado: lo refutado fue un remuestreo que no podía corregir la magnitud
  oblicua.

### 3.5 Lo que agrega el código publicado por MIROVA (S158, mismo día)

Después de escribir lo anterior apareció el código operacional de MIROVA para VIIRS 750 (OSF zm62w, 2026-07-24, MIT;
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`). Para D17 aporta tres cosas y deja una sin resolver:

- **El remuestreo no está publicado** (Coppola 2026 p. 21: las rutinas de «image resampling» «are not distributed»).
  El interpolador sigue siendo una pregunta para la Fase 0.
- **Las entradas son las matrices ya remuestreadas**, con nombre `ZI_M13` y `ZI_M15` («resampled VIIRS M13 spectral
  radiance», README). `ZI` es el nombre clásico de la salida de `griddata` en MATLAB. **SOSPECHA**, coherente con la
  firma lineal de los TIF (§3.2), no una prueba.
- **El área de la fórmula es la nominal de la celda** (0,5625 km², `MIROVA_VIIRS750_VRP.m`), y la caja de cumbre es de
  7 × 7 celdas centrada en la celda central de la grilla de 67 (matriz de ejemplo). Con 67 celdas la grilla de VIIRS 750
  tiene celda central; con 134 la de VIIRS 375 tiene una esquina en el centro. Si las dos comparten el centro, cada celda
  de 750 m contiene exactamente 2 × 2 celdas de 375 m. Es la hipótesis del §4.1 para VIIRS 750, ahora con un motivo
  geométrico, todavía sin medir.
- **Un oráculo para la Fase 0** (§5, P0-6): con un port a Python de las dos funciones se corre el detector de MIROVA
  sobre nuestras matrices remuestreadas y se compara con lo que MIROVA publicó. Si coincide, el remuestreo es el suyo.

## 4. El diseño propuesto

### 4.1 La grilla

**VIIRS 375**: la grilla de cada volcán es la del TIF: EPSG, esquina superior izquierda, celda de 375 m, 134 × 134.
Se guarda en `volcanoes.yaml` como dato medido, con la ruta del TIF y su md5 de procedencia, por ejemplo
`mirova_grid: {epsg: 32719, ul_x: 222583.9, ul_y: 5657578.2}` **[DECISIÓN PROPIA: guardar el dato medido y no una
regla de centro, porque la regla de los 62,5 m no está explicada y no vale en 3 volcanes]**. Un test fija los 11
valores contra la salida de `grilla_tif.py`.

**VIIRS 750 y MODIS**: no hay TIF UTM de esos sensores (A106). Hipótesis **[DECISIÓN PROPIA]**: el mismo centro que la
grilla de 375 m, con celda de 750 m y 67 × 67 (Campus 2022 p. 7) y celda de 1 km y 51 × 51 (Coppola 2023 p. 3). Con 67
celdas, 67 × 0,75 = 134 × 0,375 = 50,25 km: si la esquina es la misma, el centro también lo es; con 51 celdas de 1 km
la grilla mide 51 km y la esquina no puede coincidir. Se valida en la Fase 0 con la cuantización del `Distancia_km`
(D15) antes de usarla.

**Proyección**: UTM verdadero con `pyproj` (instalado, 3.7.2), en la zona que usa MIROVA para cada volcán. Reemplaza a
`_utm_like_xy`, cuyo comentario ya preveía cambiarlo «si F70.2 detecta que la diferencia importa»: importa (§3.1,
giro de hasta 1,87°).

### 4.2 El interpolador: tres alternativas

| | A. vecino más cercano | B. lineal (recomendado como candidato) | C. conservativo por áreas |
|---|---|---|---|
| qué hace | cada celda copia la muestra más cercana | cada celda interpola entre las tres muestras que la rodean | cada celda promedia las huellas que la cubren, pesadas por área |
| energía de un foco oblicuo | se conserva (la huella se replica en varias celdas) | se conserva aproximadamente; infla a nadir | se conserva por construcción |
| radiancias | sólo valores medidos | mezcla valores vecinos | mezcla valores vecinos |
| firma frente a MIROVA (§3.2) | **no la reproduce** (repetiría ~47 % a 60°) | **la reproduce** | probablemente la reproduce; no medido |
| Coppola 2014 p. 3406 | compatible | compatible | compatible |
| costo | bajo (`cKDTree`) | bajo (`scipy.interpolate.griddata` sobre el recorte) | alto: necesita el polígono de cada huella |
| riesgo | ninguno nuevo | puede pasar un foco de un píxel a dos celdas tibias que no superen a sus vecinos | el más complejo de probar |

**Recomendación [DECISIÓN PROPIA]: B como candidato primario, A como alternativa, C fuera salvo que la Fase 0 descarte
a las dos.** No se elige por gusto: la Fase 0 compara cada uno contra los TIF de MIROVA celda a celda y entra al A/B el
que los reproduce (§5). F70 (`regrid_to_utm`) queda fuera: su firma (huecos) es la que MIROVA no tiene. Si la Fase 0
encuentra que MIROVA usa otro esquema (bilineal sobre una grilla intermedia, cúbico), se agrega como candidato antes
del A/B, no después.

### 4.3 El bow tie

**VIIRS**: el instrumento borra a bordo las muestras repetidas del borde del barrido, y nuestro lector ya las marca
como NaN (`FLAG_DNS` incluye 65533, `Bowtie_Deleted`, `pipeline/process_viirs.py:83` y `process_viirs_mod.py:68`).
Queda un solape residual entre barridos que hoy cuenta doble en el borde (AUDIT_S155 F5-09: 6 de 51 pasadas de
Chillán, todas sobre 50°, hasta ×1,88). Remuestrear lo resuelve de por sí, porque cada celda recibe un solo valor.
Lo que queda por decidir es si se descartan las muestras del solape residual antes de interpolar (dos muestras casi en
el mismo lugar con valores distintos hacen triángulos degenerados) **[DECISIÓN PROPIA: decide la Fase 0, la variante
que mejor reproduce los TIF]**.

**MODIS**: no hay borrado a bordo; el solape llega a la mitad del barrido en el borde. El canon dice «identified and
removed» antes de remuestrear (Coppola 2016a p. 3; Coppola 2023 p. 3) sin decir cómo (D28). Propuesta **[DECISIÓN
PROPIA, Fase 2]**: en cada columna del barrido, descartar las filas de detector de un barrido cuya posición a lo largo
de la traza queda dentro del barrido siguiente, conservando el orden monótono. Se mide contra los TIF geográficos de
MODIS por correlación espacial, que no requiere la grilla exacta.

### 4.4 Saturación, ángulos y celdas sin dato

- **VIIRS**: el lector pone NaN donde el bit 2 de `quality_flags` marca saturación. Con interpolación ese NaN
  desaparece y sus vecinos lo rellenan: se perdería justo el píxel más caliente. Propuesta **[DECISIÓN PROPIA]**:
  interpolar con la radiancia recortada que entrega el sensor y llevar la marca de saturación a la celda por vecino
  más cercano. Pesa poco hoy (Chillán: 0 saturados en 385 gránulos, tarea 1.18) y se cruza con D24.
- **MODIS**: se conserva el contrato de F70 (la banda 21 saturada es NaN y la 22 es el respaldo,
  `tests/test_regrid_modis_f70.py`): la 22 se interpola siempre, la marca de NaN de la 21 va por vecino.
- **Ángulos**: el cenit se interpola como número; el **azimut** cruza ±180° y se interpola por seno y coseno. #879
  usa `sensor_azimuth_deg`.
- **Celdas fuera del barrido**: quedan NaN y no aptas, sin relleno (la interpolación lineal no extrapola fuera de la
  envolvente de las muestras).

### 4.5 Dónde entra en el código (para el plan de implementación, no para este PR)

- **`pipeline/regrid.py`**: función nueva `regrid_to_mirova_grid(lat2d, lon2d, bands, grid, method, required)`. No se
  toca `regrid_to_utm`, que reproduce F70 y lo usan `_f70_a.yaml` y `_f70_b.yaml`. Recorta primero el barrido a la
  caja de la grilla más un margen de dos huellas, para que la triangulación sea chica.
- **Los tres procesadores**, en el punto donde hoy está el gancho de F70 (`process_viirs.py:762`,
  `process_viirs_mod.py:502`, `process_modis.py:551`): con el flag nuevo encendido, se llama a la función nueva con la
  grilla del volcán. La salida mantiene el contrato de F70 (mismo esquema que los lectores), así que la detección
  corre sin cambios sobre las matrices regulares, y la latitud y longitud de cada celda salen de la proyección inversa
  de su centro UTM.
- **`scripts/run_pipeline.py`** (l. 235, 278 y 325): pasa la grilla del volcán (`volcano["mirova_grid"]`) como
  argumento nuevo de `calculate_vrp`. Hoy el centro de F70 sale del `volcano_lat`/`volcano_lon` posicional.
- **Flags nuevos, bajo `thresholds:`** (A89: leer desde `pipeline.profile`, nunca del YAML): `enable_d17_regrid`
  (apagado por defecto y en `mirova_equivalent`), `d17_regrid_method` (`lineal` o `vecino`) y
  `d17_regrid_sensores` (por defecto sólo VIIRS). **[DECISIÓN PROPIA: flag propio y no reutilizar
  `enable_utm_regrid`, para que F70 siga siendo reproducible.]**

### 4.6 Consumidores que el flag tiene que alcanzar (A118)

| consumidor | qué cambia con la grilla | qué hacer |
|---|---|---|
| área del píxel (`resolve_viirs_pixel_areas`, `modis_pixel_areas`) | debe ser el área de la celda | con el flag, forzar el área de la celda aunque `enable_geolocated_pixel_area` esté encendido; test que falle si no |
| distancia al cráter y al centro (`dist`, `vent_dist_per_pixel`) | se mide a centros de celda (±media celda, D15) | nada; se informa |
| ROI1, círculo o caja D18 (`roi1_summit_mask`, `roi_mask_bbox`) | la caja de 5 × 5 km pasa a ser de celdas | caja en celdas cuando haya grilla; test |
| Tests 2 y 3, kernel de 8 vecinos, `second_pass_adjacent`, `cluster_hotspots` | los vecinos pasan a ser celdas iguales | nada en el código; es el objetivo |
| borde no apto de un píxel (`_edge_unsuitable_mask`) | el borde pasa a ser el de la grilla | nada |
| fondo de D25 (ventana de hasta 7 × 7 **en píxeles**) | en oblicuo la ventana se achica en km (de ~5,6 a 2,6 km) | se informa; por eso D17 se mide sobre la base que deje D25 (§6.1) |
| núcleo F5' (radio de 0,75 km) | en km, ve más celdas en oblicuo | nada; se informa F_rec por tramo de cenit |
| `FOCAL_CLUSTER_KEEP_PEAK` y modo de un píxel (MODIS y VIIRS 750) | el pico pasa a ser una celda | se informa |
| saturación VIIRS (bit 2) y MODIS (banda 21 NaN) | ver §4.4 | test por sensor |
| `anomaly_pixels`, `final_hotspot_*`, `primary_cluster.centroid` persistidos | coordenadas de centros de celda | el tablero los dibuja igual; verificar en el navegador (`frontend/index.html`, `diario.html`, `mosaico.html`) |
| `sensor_zenith_deg`, `sensor_azimuth_deg` del record | interpolados | azimut por seno y coseno (§4.4) |
| fondo del anillo de 5 a 25 km | la grilla mide 25,125 km de semiancho: el anillo cabe | nada |
| filtros del tablero `isCirrusArtifact`, `isDiffuseFieldArtifact` | leen magnitud y conteo | P1 y P2 con el predicado del tablero ejecutado con node (A97) |

Antes de escribir el código, `grep` de `inner_radius_km`, `is_summit`, `pixel_areas` y `sensor_zenith` en los tres
procesadores para completar esta tabla (A118 a): la lista de arriba sale de leer los ganchos de F70 y de D25, no de un
barrido completo.

### 4.7 MODIS: lo que tiene que pasar antes

1. **Geolocalización.** `_interp_geo` (`pipeline/process_modis.py:385`) ignora el desfase de la grilla de 5 km y corre
   el píxel 1 a 3 km hacia el nadir (S151, PR #826 y #828). Remuestrear con esa posición pone cada muestra en la celda
   equivocada. El pipeline ya baja MxD03 (1 km, con corrección de terreno) y no lo usa; no hay flag para leerlo. Es
   prerrequisito.
2. **Bow tie** (§4.3) y **origen de la grilla de 51 × 51** (§4.1).
3. Además MODIS sólo corre en Linux (pyhdf), así que su Fase 0 va en GitHub Actions.

Por eso el A/B de la Fase 1 es **sólo VIIRS** **[DECISIÓN PROPIA]**.

## 5. Fase 0: identificar el remuestreo contra la referencia (sólo lectura)

No reprocesa ni escribe en `data/`. Es un probe con controles escritos antes de correr, en GitHub Actions o local
(VIIRS no necesita pyhdf), autenticando sólo por `EARTHDATA_TOKEN` (A71).

- **P0-1, reproducir los TIF.** Para cada TIF UTM de la ventana de A106 (el número exacto sale de `index.csv` del archivo
  de TIF leyendo el CRS de cada uno, como en S144), bajar el gránulo VIIRS de esa pasada (VNP02IMG y VNP03IMG, o los de NOAA-20 y NOAA-21), remuestrear
  I4 a la grilla del TIF con cada candidato (vecino, lineal, y las dos variantes del solape residual) y comparar celda a
  celda: correlación, mediana de la diferencia relativa, firma (vecinas iguales, vacías). Si el TIF no es radiancia de
  I4 sino temperatura u otra variable, se ve aquí.
- **Piso de ruido, medido y no elegido (A115).** La diferencia entre remuestrear la versión NRT y la estándar del mismo
  gránulo con el mismo método (CLAUDE.md: delta < 0,1 K) es lo más cerca que podemos estar de MIROVA sin ser MIROVA.
- **Regla de elección [DECISIÓN PROPIA, para el sello]**: entra al A/B el candidato con menor diferencia mediana
  contra los TIF, **si** su diferencia queda dentro de tres veces el piso de ruido en la mayoría de las celdas del
  círculo de 5 km del cráter; si ninguno lo logra, el interpolador se declara NO IDENTIFICADO y el A/B corre con B
  advirtiéndolo en la primera línea del veredicto.
- **P0-2, huecos de F70 en gránulos reales**: confirma o refuta el sintético del §3.3.
- **Intento previo, NO CONCLUYENTE** (`experiments/_s158_d17_diseno/distancia_vs_grilla.py`): con la grilla exacta de los
  TIF de VIIRS 375 se buscó desde qué celda mide MIROVA su `Distancia_km`. Sólo hay 10 pares alerta-TIF UTM, y ubicar el
  foco como la celda de mayor exceso de radiancia MIR es débil para alertas de 0,03 a 0,4 MW (MIROVA detecta por NTI).
  Ninguna celda de referencia coincide en más de 3 de 10. Con el oráculo (P0-6) el foco sale del detector de MIROVA.
- **P0-3, grilla de VIIRS 750 y MODIS**: con la grilla hipotética del §4.1, el `Distancia_km` de las alertas de MIROVA
  de esos sensores debe caer en `√(i² + j²) · celda` desde la celda central (D15). Si no cierra, la hipótesis cae.
- **P0-4, el caso de #880**: Chillán 2026-10-18 06:48, I4 y M13 remuestreados a sus grillas, energía co-ubicada en
  las dos bandas. Diagnóstico, no decide.
- **P0-5, costo**: segundos por gránulo de cada candidato.
- **P0-6, oráculo (VIIRS 750)**: port a Python de `MIROVA_VIIRS750_hotspot_detection.m` y `MIROVA_VIIRS750_VRP.m`
  (con pruebas sobre la matriz de ejemplo), corrido sobre nuestras matrices de M13 y M15 remuestreadas con cada
  candidato, en las pasadas de VIIRS 750 de V1 con alerta de MIROVA. Se compara el VRP y el `Distancia_km` del oráculo
  contra lo publicado. Separa por primera vez el error del remuestreo del error del detector.

**Controles antes de mirar el resultado**: (1) positivo, remuestrear el TIF de MIROVA consigo mismo (submuestreado a
huella oblicua sintética) y recuperar su propio método; (2) negativo, comparar contra el TIF de **otra** pasada de la
misma noche (A109: el TIF de la misma pasada sale del mismo gránulo; el de otra pasada fija cuánto acuerdo da el
terreno solo); (3) cableado, la grilla usada es la del TIF al decímetro.

## 6. Fase 1: A/B de adopción, pre-registrable (VIIRS 375 y 750)

### 6.1 Orden respecto de D25

D17 se mide **sobre la base que deje D25** (tarea 1.36: D17 queda como hipótesis si después de D25 sigue la caída con el
cenit). Con D25 en la base, la ventana de vecinos interactúa con la grilla (§4.6) y el A/B mide lo que operaría en
producción. La Fase 0 no tiene que esperar a D25 porque no adopta nada.

### 6.2 Brazos

| brazo | perfil (nombre propuesto) | qué es |
|---|---|---|
| B | `_s1xx_ab_d17_base` | la base: K, o K más D25 si D25 se adopta |
| B' | `_s1xx_ab_d17_gemelo` | gemelo de B, mide el ruido de corrida |
| R | `_s1xx_ab_d17_regrid` | B más `enable_d17_regrid`, grilla del TIF, interpolador de la Fase 0, sólo VIIRS |
| R2 (opcional) | `_s1xx_ab_d17_regrid_alt` | el segundo candidato de la Fase 0, sólo si quedó a menos de una vez el piso de ruido del primero |

MODIS apagado en todos los brazos (Fase 2). Perfiles con `data_subdir` aislado (patrón S24), un solo pipeline por
ventana desde un tag (S152: argsort y runners).

### 6.3 Ventanas (A119)

Las mismas de D25 para que las dos palancas se lean juntas:

- **V1, 2026-08-29 a 2026-10-18**: decide la tabla y el OCR. Trae a Chillán en erupción y **contiene la ventana de los
  TIF UTM** (14 y 15 de septiembre), donde además se puede mirar celda a celda.
- **V2, 2026-04-01 a 2026-06-12**: decide **la tabla sola**; el OCR se informa aparte (antes del 2026-06-13 no mide
  distancia). Es la de más poder de veto en Láscar. VIIRS por pasada sólo desde abril (hito de A119).

Referencia congelada por hash como en D25 (`_congelado_v1/`, `_congelado_v2/`). Cobertura igual entre brazos antes de
mirar el veredicto (A108).

### 6.4 Métricas, por sensor, por tramo de cenit y por ventana

Se reusa el evaluador de D25 (`experiments/_s157_prereg_d25/evaluar_d25.py`) con los mismos predicados: publicado es lo
que publica `frontend/index.html` ejecutado con node (A97), alerta protegida es la lectura A (1 MW o más, D-4), y rige
la regla SN de las alertas mínimas (D-9), informando también la original.

- **P1, veto**: protegidas que B publica y R no. Una pérdida neta veta (criterio de victoria de `docs/MISSION.md`).
- **P2, suma bajo 1 MW**: alertas Muy Bajo perdidas más publicaciones en negativos limpios, por pasada y por
  noche-volcán (A94). El ruido es la discordancia B contra B'.
- **M, magnitud**: razón publicada contra MIROVA, mediana con bootstrap por bloques noche-volcán, en dos tramos de
  cenit (≤ 40° y > 40°, el corte del grupo, Massimetti 2020 citado en D17) y la curva informativa en cuatro (≤ 20, 20
  a 40, 40 a 50, > 50). En VIIRS 375 los cinco volcanes con kernel local se miden aparte, como en D25.
- **S, pendiente con el cenit** (la firma propia de D17): `S = R(> 40°) / R(≤ 40°)`. Si el remuestreo es lo que falta,
  S sube hacia 1 sin que R(≤ 40°) se aleje de 1.
- **G, fidelidad geométrica**: fracción de las alertas de MIROVA pareadas en que nuestra celda del cúmulo da exactamente
  su `Distancia_km` (`√(i² + j²) · 0,375` desde la celda central de su grilla). Con la grilla de MIROVA esta fracción
  debería subir mucho; sobre el barrido crudo no puede ser alta. Es el control de que la grilla es la suya.
- **N, conteo**: Npix por tramo de cenit en B y R, frente a la tensión del §3.3.
- **Posición (A61)**: distancia mediana del cúmulo al cráter por volcán, que no empeore.

### 6.5 Criterio de adopción [DECISIÓN PROPIA, para el sello]

| resultado | veredicto |
|---|---|
| P1 sin pérdida neta, P2 sin PIERDE en ningún sensor ni ventana, S MEJORA fuera del ruido en VIIRS 375 sin kernel o en VIIRS 750 **en las dos ventanas**, en al menos dos volcanes, y M(≤ 40°) no EMPEORA en ningún estrato que decide | **CUMPLE**: se abre el ciclo de adopción (tag defensivo, R2 por píxel, verificador independiente, «sí» de Nicolás) |
| ídem pero S mejora en una sola ventana | decide Nicolás con la tabla por estrato y por volcán |
| P1 y P2 bien, S sin cambio fuera del ruido | **NO CUMPLE por falta de beneficio**: D17 queda como divergencia literal sin consecuencia medida en magnitud; G y N se informan |
| P1 vetado, o P2 PIERDE, o M(≤ 40°) EMPEORA (la inflación a nadir del §3.3) | **NO CUMPLE**; cada pérdida se diagnostica con la cabecera de la imagen de MIROVA (A61) |

MEJORA y EMPEORA se miden contra el ruido de B contra B' y la calibración con signo al azar que el evaluador de D25 ya
trae; los umbrales salen de esos nulos, no se eligen (A115). G no decide: si no sube, la grilla no es la de MIROVA y
el A/B no midió D17 (se declara INDECIDIBLE, A116).

### 6.6 Controles antes de mirar ningún resultado

1. **Cableado (A118)**: la línea `FLAGS_BRAZO` de cada job trae el flag, el método, la fuente de la grilla y el área
   de celda; las coordenadas de los `anomaly_pixels` de R caen en centros de celda de la grilla del TIF.
2. **Instrumento (A116)**: R cambia records (cuántos, por sensor); un brazo R corrido sobre un día con un gránulo a
   nadir alineado da casi lo mismo que B.
3. **Saturación de la métrica (A114)**: la publicación en negativos limpios de B varía entre tramos de cenit; si no
   varía, algo la satura y el A/B no puede medir.
4. **Cobertura (A108)**: pasadas por brazo iguales a las de B; los jobs cortos se repiten.

### 6.7 Costo

Con D25 se estimó V1 en 33 jobs de ~112 min y 22 a 31 h de grupo ocupado. El remuestreo agrega lo que mida P0-5.
Para lanzar el reemplazo de datos si se adopta existe el workflow de #884 (`aplicar-reemplazo`).

### 6.8 Lo que este A/B no puede decir

- MODIS (Fase 2).
- Si el TIF es la matriz con que MIROVA detecta o una versión para mostrar; se asume lo primero porque su grilla es la
  que cuantiza el `Distancia_km` (D15), pero es SOSPECHA.
- El efecto del lado del barrido (#879): en VIIRS lado y hora son la misma variable. Se informa S por lado, sin
  decidir. Como MIROVA usa la misma geolocalización con corrección de terreno que nosotros (Aveni 2024 p. 5;
  `pipeline/fetch.py:198`, VNP03IMG), el paralaje no debería ser una diferencia entre los dos en VIIRS: razonado, no
  medido.

## 7. Las tres preguntas de `docs/MISSION.md`

1. **¿Está en los papers core?** Sí, en voz activa del sistema: Coppola 2016a p. 3 («we cropped and resampled»),
   Campus 2022 p. 7 («Resampling is performed»), Aveni 2024 p. 5 («as per MIROVA workflow, are resampled»), Campus
   2024 p. 3, Coppola 2023 p. 3. El centro por volcán es la variación por objetivo que MISSION admite (geometría ROI,
   centro GVP); no es un parámetro por régimen.
2. **El interpolador no está en los papers**: cierra la divergencia documentada D17 (y D28 para MODIS), y se elige
   midiendo contra los TIF de MIROVA, no por gusto.
3. Se adopta sólo con el A/B del §6 y el «sí» de Nicolás.

## 8. Decisiones para Nicolás

1. **¿Correr la Fase 0 ya, antes del veredicto de D25?** Recomendado: sí; es de sólo lectura y no adopta nada.
2. **¿Guardar la grilla medida del TIF en `volcanoes.yaml`** (11 valores) en vez de una regla de centro? Recomendado:
   sí (§4.1).
3. **¿Fase 1 sólo VIIRS y MODIS después de MxD03?** Recomendado: sí (§4.7).
4. **La regla de elección del interpolador y el criterio de adopción** (§5 y §6.5) se sellan en el pre-registro, no
   aquí.
5. **Marcas A113 de este PR** (§10): revisar que el texto de D16, D17 y `docs/SINTOMAS.md` diga lo que se midió.

## 9. Cita y decisión propia

**Cita del canon** (renderizada en S158): que MIROVA recorta y remuestrea antes de detectar, el porqué (error heredado
del área variable, escala homogénea), el orden bow tie y luego remuestreo, que el área de la fórmula es la de la celda,
las tres grillas (51 × 51 de 1 km, 67 × 67 de 750 m, 134 × 134 de 375 m), centro GVP, la geolocalización VNP03IMG, y
que un píxel de 2 km² se vuelve dos celdas de 1 km².

**Medido en S158** (scripts en `experiments/_s158_d17_diseno/`): la grilla de los TIF y su relación con el yaml; la
firma de los TIF; la firma y la energía de tres remuestreos en sintético.

**Decisión propia**: guardar la grilla medida; el interpolador candidato y la regla para elegirlo; el método del bow
tie de MODIS y del solape residual de VIIRS; el manejo de saturación y azimut; los flags nuevos; la grilla de VIIRS 750
y MODIS; el orden respecto de D25; el alcance sólo VIIRS; los brazos, el estadístico S y el criterio de adopción.

## 10. Propagación (A113)

En este mismo PR: marca en el encabezado de D17 y en el «NO REABRIR» de D16 (`docs/MIROVA_DIVERGENCES.md`), y una
línea en `docs/SINTOMAS.md` §1. Fuera de alcance (toca `pipeline/`, A45): el docstring de `pipeline/regrid.py`, que
llama «vecino más cercano» a lo que es asignar cada muestra a su celda, y el de `pipeline/geo_utils.py`, que llama a
`mirova_center` «el centro de la escena de MIROVA».

## 11. Reproducir

```
python -I experiments/_s158_d17_diseno/grilla_tif.py . <carpeta temporal>
python -I experiments/_s158_d17_diseno/firma_interpolador.py .
```

El primero necesita `gh` autenticado (lee el archivo de TIF por la API) y `rasterio` y `pyproj`; el segundo, `scipy`.
