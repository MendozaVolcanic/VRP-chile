# S142: Nevados de Chillán, tercer sistema (MOUNTS) y píxeles que suma MIROVA

Salidas: `mounts_ndc.py` escribe `mounts_ndc.json`; `pixeles_mirova.py` escribe `pixeles_mirova.json`.
Los números de este documento salen de esos JSON (regla S91). Descargas en `_dl_tif/`, `_dl_mounts/`,
`_dl_mirova/` (ignoradas por git).

## 0. Procedimiento del Frente B, escrito ANTES de correr la reconstrucción

**Qué es el valor del raster.** La leyenda de la página de mapa de MIROVA dice "MIR radiance (W/m² sr µm)"
(`_dl_mirova/map_ChillanNevadosde.html`, leída en S142). El README del archivo no documenta el valor. Se
toma como radiancia I04 en W/m² sr µm; que sea la radiancia sin fondo restado es lo que el propio raster
permite comprobar (mediana nocturna ~0,1, no ~0).

**Qué TIF entra.** Un TIF entra si (a) su CRS leído con rasterio es UTM (EPSG 327xx); (b) todas las filas de
`index.csv` con su mismo md5 y adquisición no vacía apuntan a UNA sola adquisición (si el archivo quedó
registrado con dos adquisiciones distintas, AMBIGUO, fuera); (c) la adquisición es nocturna (03 a 09 UTC) y la
mediana del raster es menor que 0,2 W/m² sr µm (las escenas diurnas de Nevados de Chillán dan ~0,3). Un TIF
de 0 bytes es SIN DATO, nunca cero.

**Qué publicó MIROVA en esa pasada.** Filas VIIRS375 del consolidado y del OCR de `Mirova-v1` (remoto) del
mismo volcán a ±60 s. ALERTA si hay alguna fila ALERTA_TERMICA u ALERTA_TERMICA_OCR (VRP y distancia del
consolidado si está, si no del OCR); CONTROL si todas son RUTINA con VRP 0; cualquier otra cosa (FALSO_POSITIVO)
queda fuera. Cenit del OCR si lo trae.

**Fondo (Coppola et al. 2016a, SP426.5, Eq. 6, l. 355-359 del `.txt`).** "L4bk is estimated from the
arithmetic mean of all the pixels surrounding the active one (or around the active cluster)". Dos variantes:
- BA: para cada celda del conjunto, media de sus 8 vecinas que no están en el conjunto.
- BB: una sola media para todo el conjunto, sobre las celdas 8-adyacentes al conjunto que no están en él.
Con una celda son idénticas.

**Magnitud.** VRP = 18,0 × 140.625 m² × Σ(L − L_bk) (coeficiente VIIRS 375 m validado S14, CLAUDE.md).

**Conjunto alertado.** Exceso local fijo ΔL0 = L − media de las 8 vecinas. Semilla = celda de mayor ΔL0 dentro
de un disco de radio R_v alrededor de la celda que contiene `mirova_center` (volcanoes.yaml), con
R_v = 0,6 km + la mayor distancia publicada por MIROVA en las alertas nocturnas de ese volcán en la ventana
(0 si no tiene). El mismo R_v se usa en alertas y controles del volcán. El conjunto crece de 1 a 6 celdas
agregando la vecina 8-conexa de mayor ΔL0.

**Cuántas celdas explican el VRP publicado.** Compatibles: k con |VRP_k − VRP_pub| ≤ 0,005 MW (el redondeo a
dos decimales). Se informa también el k más cercano.

**Controles.**
1. Instrumento: con las celdas que usó S141 en Nevados de Chillán 15-sep 06:18 ((68,66); (67,66); (68,67)) y
   BA, el script debe reproducir 0,030, 0,065 y 0,078 MW.
2. Especificidad: el mismo procedimiento en pasadas nocturnas donde MIROVA miró y no alertó. Si es específico,
   la semilla de los controles no destaca (z = ΔL0_semilla / σ_robusto de ΔL0 en la escena menor que en las
   alertas) y VRP_1 de los controles queda bajo 0,01 MW (límite de detección que declara MIROVA). Si los
   controles dan magnitudes como las alertas, el conteo es INCONCLUSO aunque alguna alerta calce.

---

## 1. Frente A: MOUNTS (Sentinel-2 SWIR, 20 m)

**Qué mide.** MOUNTS no entrega VRP: su serie `swir` es el número de píxeles térmicamente anómalos de
Sentinel-2 L1C (S2Pix, Massimetti et al. 2020), con valor ~0,1 como marcador de "sin detección"
(`MOUNTS/METHODOLOGY.md:30`, `:61-68`; `MOUNTS/API.md:179-190`). El AOI es un recuadro de pocos km sobre el
cráter (`METHODOLOGY.md:79-81`) y es óptico: nubes dan falsos negativos, incendios falsos positivos
(`METHODOLOGY.md:100-102`). Sentinel-2 pasa de día (~14:30 UTC) cada 2 a 5 días: **una detección MOUNTS
confirma el día, nunca una pasada nocturna VIIRS concreta** (hay 8 a 9 h de diferencia).

**Fuente y frescura.** Salida publicada de `MendozaVolcanic/MOUNTS-Chile` (GitHub Pages,
`actividad_termica_so2.json`, generado 2026-09-15 11:54 UTC), contrastada punto a punto con el Plotly de
`mounts-project.com/timeseries/357070`: 43 puntos entre el 1-jun y el 15-sep, **0 discrepancias**
(`mounts_ndc.json` → `meta`). No se leyó el `data/` de MOUNTS por disco.

**Detecciones MOUNTS en la ventana (6 de 43)**, con lo que pasó la noche anterior del mismo día UTC:

| Sentinel-2 (UTC) | S2Pix | alerta MIROVA en el cráter esa noche | nuestros records de foco esa noche (≤0,5 km de Nicanor, f5 > 0) |
|---|---|---|---|
| 16-jun 14:37 | 6 | 05:30, 0,06 MW | 04:42, 05:30, 06:06 |
| 26-jun 14:37 | 4 | no | 05:42, 06:18, 06:36 |
| 01-jul 14:37 | 5 | no | 05:48, 06:24 (0,016 y 0,017 MW) |
| 03-jul 14:38 | 4 | no | 05:48, 06:06 |
| 11-jul 14:37 | 7 | no | 05:18, 06:00 |
| 14-sep 14:37 | 2 | 05:42, 0,09 MW | 05:42, 06:18, 06:36 |

"Records de foco" es una aproximación (summit, f5 > 0, a ≤0,5 km de Nicanor), **no** el predicado del
dashboard.

**Las preguntas concretas.**
- **14-sep (05:42 ambos publicamos; 06:18 y 06:36 sólo nosotros):** MOUNTS detecta 2 S2Pix el mismo día a las
  14:37 UTC. Eso confirma calor en el AOI ese día, 9 h después de las tres pasadas. No distingue entre
  ellas: no dice nada sobre si a las 06:18 o 06:36 el foco estaba por encima de lo que MIROVA considera
  alerta. Es coincidencia de fecha, no de pasada.
- **15-sep 06:18 (ambos):** MOUNTS no tiene adquisición el 15-sep (la última es del 14-sep). Sin testigo.
- **Contraejemplo que importa:** el 20-ago MIROVA alertó dos veces en el cráter (05:12 y 06:06) y MOUNTS a las
  14:37 dio no-detección. La imagen publicada de ese día se ve despejada, con nieve (juicio visual mío sobre
  el PNG, SOSPECHA). El 18-ago no hubo Sentinel-2.
- **Julio**: MOUNTS detecta 3 de 15 imágenes (1, 3 y 11 de julio) mientras MIROVA no publicó ninguna alerta
  en el cráter en todo el mes y nuestros records de foco fueron escasos y débiles. Coherente con A77 (un
  foco sub-píxel que Sentinel-2 resuelve y VIIRS no), pero sólo como coherencia, no como prueba.
- En los PNG del 14-sep y 16-jun no encontré píxeles rojo-anaranjados con un umbral de color simple
  (0 y 1 píxel, este último en el borde de la imagen); lo que se ve en el cráter es un punto blanquecino. La
  composición de colores del PNG no está documentada, así que esto no refuta ni confirma el conteo S2Pix.
- La página MSI de MIROVA (Sentinel-2 del grupo MIROVA) mostró "Image unavailable" el 15-sep 13:00 UTC.

**Lectura.** Un tercer sistema de otra física confirma que el cráter tuvo calor en 2 de los 4 días con
alerta MIROVA en el cráter que tienen imagen Sentinel-2 (16-jun y 14-sep), no lo vio en el tercero (20-ago)
y lo vio en días sin alerta MIROVA (26-jun, julio). No puede decidir la sobre-publicación de las 06:18 y 06:36
del 14-sep: la escala temporal de Sentinel-2 es de días y la pregunta es de horas.

## 2. Frente B: celdas que suma MIROVA

### 2.1 Inventario de TIF (`pixeles_mirova.json` → `inventario_tif`)

- CRS verificado con rasterio en cada archivo. Nevados de Chillán 14-sep 05:42 (la alerta de 0,09 MW) es
  EPSG:4326 float64: **no sirve para contar celdas**. Los archivos con contenido nuevo desde el 14-sep ~06:36 son UTM
  float32 (EPSG:32719; Chaitén y PCC 32718); algunos `_lm` escritos el 14-sep a las 08 UTC siguen en 4326
  porque repiten la imagen anterior, y quedaron fuera.
- **La etiqueta de adquisición del archivo no es confiable en la transición.** Los TIF rotulados 06:36 y
  06:42 del 14-sep en NdC, Chaitén, Isluga, Láscar, Lastarria, Llaima, PCC y Villarrica tienen medianas de
  0,22 a 0,73 W/m² sr µm, niveles de escena diurna, y fueron escritos ~17 h después de la adquisición
  declarada. Quedaron fuera por el criterio nocturno. En Copahue, Planchón-Peteroa y Tupungatito el archivo
  06:36 pasó el corte de mediana (0,2) pero también fue escrito 17 h después; quedan como controles según §0,
  y abajo se muestra el efecto de sacarlos (post-hoc).
- NdC 14-sep 06:18 no quedó archivado (no hay fila en `index.csv`). NdC 13-sep 05:18 es un TIF de 0 bytes:
  SIN DATO.
- Resultado: **6 alertas nocturnas VIIRS 375 con TIF UTM** (todas del 15-sep) y **19 controles**.

### 2.2 Control de instrumento P1

Con las celdas de S141 el script da 0,0298 / 0,0645 / 0,0783 MW (BA) contra 0,030 / 0,065 / 0,078
transcritos a mano en S141. Pasa. Nicanor cae en la celda (68, 66) y la semilla elegida por el procedimiento
en la alerta es esa misma celda. Ojo: en `volcanoes.yaml` el `vent` de NdC es la coordenada GVP, que cae en
(66, 67).

### 2.3 Tabla por alerta (VRP en MW; k = celdas; BA y BB según §0)

| pasada UTC 15-sep | volcán | cenit | MIROVA VRP / dist | z semilla | k=1 | k=2 (BA/BB) | k=3 (BA/BB) | máx k≤6 BA | k compatible ±0,005 | nuestro record (f5 / pc n) |
|---|---|---|---|---|---|---|---|---|---|---|
| 06:18 | Nevados de Chillán | 45° (OCR) | 0,05 / 0,38 km | 5,0 | 0,030 | 0,065 / 0,068 | 0,073 / 0,074 | 0,108 | ninguno (más cercano 2) | aún no procesado |
| 05:18 | Isluga | 44,7° (nuestro, NOAA-21) | 0,40 / 1,06 km | 14,1 | 0,088 | 0,189 / 0,200 | 0,301 / 0,313 | 0,326 | ninguno (no se alcanza) | 0,171 / 1 |
| 06:18 | Láscar | sin dato | 0,24 / 1,19 km | 21,1 | 0,089 | 0,141 / 0,149 | 0,195 / 0,205 | 0,323 | ninguno (más cercano 4: 0,235 / 0,247; BA justo en el borde del redondeo) | aún no procesado |
| 06:18 | Lastarria | sin dato | 0,03 / 1,19 km | 4,9 | 0,021 | 0,046 / 0,048 | 0,063 / 0,068 | 0,107 | ninguno (más cercano 1) | aún no procesado |
| 06:18 | Planchón-Peteroa | sin dato | 0,04 / 2,02 km | 8,2 | 0,047 | 0,067 / 0,067 | 0,090 / 0,090 | 0,119 | ninguno (más cercano 1) | aún no procesado |
| 05:24 | Tupungatito | 26,3° (nuestro, NOAA-21) | 0,15 / 4,89 km | 11,7 | 0,064 | 0,115 / 0,118 | 0,145 / 0,153 | 0,193 | BB k=3 | 0,080 / 1, pero a 0,05 km del cráter: otro objeto que la alerta a 4,89 km |

"Aún no procesado": a las 13:05 UTC del 15-sep (hora del servidor) el último NRT en `origin/main` es de las
07:53 y ningún JSON tiene todavía la pasada de las 06:18.

### 2.4 Control de especificidad

- z de la semilla: mediana **10,0** en alertas contra **2,7** en controles (2,0 sin los tres archivos
  sospechosos, post-hoc). La semilla destaca más cuando MIROVA alerta.
- Pero VRP con una celda en los controles: sólo **8 de 19** quedan bajo 0,01 MW (8 de 16 sin los
  sospechosos). Chaitén (05:24 y 06:24, z 6,5 y 7,9), Isluga 06:12 (z 6,6) y Tupungatito 06:18 (z 6,3) dan
  0,03 a 0,04 MW con una sola celda en pasadas donde MIROVA dijo RUTINA, lo mismo que la alerta de NdC.
- **Veredicto según §0: el conteo es INCONCLUSO.** El procedimiento encuentra exceso local en el cráter tanto
  cuando MIROVA alerta como cuando no, y sólo 1 de 6 alertas calza con algún k dentro del redondeo.

### 2.5 Lo que sí se puede decir (con su grado)

- **No hay un número fijo de celdas.** NdC queda entre 1 y 2; Lastarria y Planchón-Peteroa en 1; Láscar
  cerca de 4; Isluga no se alcanza ni con 6 celdas y fondo local.
- **Isluga 05:18 es el único caso con record nuestro del mismo objeto** (MIROVA a 1,06 km, nosotros a 0,92
  km). Nuestro fondo (`diag_L_bg_w_m2_sr_um` 0,0836) es prácticamente el de las 8 vecinas de la semilla en
  el TIF de MIROVA (0,0835). Con ese fondo, una celda da 0,088 y nuestro f5 da 0,171 (1 píxel); MIROVA
  publica 0,40, que exige sumar 4 o más celdas con fondo local y aun así no llega (tope 0,33). **En este
  caso la diferencia no viene del fondo de la celda caliente sino de cuánta área suma MIROVA, o de un
  fondo más bajo aplicado a varias celdas.** Un solo caso: SOSPECHA, no conclusión.
- **Post-hoc, fondo implícito** (`posthoc_fondo_implicito`): para que una sola celda dé lo publicado, en
  Isluga y Láscar el fondo tendría que ser negativo o bajo todo el campo (percentil 0); en NdC, 0,008 bajo el
  anillo (percentil 28 de la escena). Con 4 celdas el fondo implícito queda a ±0,005 del anillo local en 4 de
  los 6 casos (NdC, Láscar, Lastarria, Tupungatito); Isluga queda 0,0053 bajo el anillo y Planchón-Peteroa
  0,0057 sobre él. Es decir: los números publicados de Isluga y Láscar son más compatibles con **sumar
  varias celdas con fondo local** que con una celda y un fondo bajo; en Lastarria y Planchón-Peteroa una
  celda ya basta. Esto no estaba pre-registrado y lo contradice en parte el
  control de especificidad, que muestra que 3 celdas de exceso local aparecen también sin alerta.
- **SOSPECHA sin verificar:** el TIF es un remuestreo a la grilla UTM. En NdC las celdas (67,66) y (68,66)
  tienen radiancia casi idéntica (0,0869 y 0,0871), lo que es compatible con un píxel L1B repartido en dos
  celdas. Si MIROVA calcula el VRP sobre el L1B y no sobre este raster, contar celdas del TIF no cuenta
  píxeles de su cálculo. No encontré documentación que lo resuelva.

### 2.6 Qué haría falta para cerrarlo

1. Más alertas UTM: el archivo lleva ~1 día en el formato nuevo. Con una semana hay decenas de alertas
   nocturnas en los 11 volcanes; basta volver a correr `pixeles_mirova.py` tras descargar los TIF nuevos.
2. Esperar el NRT de las 06:18 del 15-sep para tener nuestros records de NdC, Láscar, Lastarria y
   Planchón-Peteroa.
3. Filtrar por latencia de escritura en el procedimiento (pre-registrarlo esta vez): los archivos escritos
   más de 8 h después no son la adquisición que dicen.
