# Corrimiento del píxel MODIS del cráter (tarea 1.15)

**Veredicto:** el corrimiento es real, es nuestro y no es paralaje. Lo produce la interpolación de la
geolocalización MODIS de 5 km a 1 km (`_interp_geo`, `pipeline/process_modis.py:342`), que estira la
grilla gruesa de punta a punta sin respetar que su primer punto corresponde al frame 2 del barrido. El
efecto mueve cada píxel hacia el nadir (hacia el sensor) entre 0,5 y 2 frames. Medido en Láscar con el
cráter como fuente limpia, el modelo geométrico explica el corrimiento con un coeficiente de **0,90
[0,81; 1,01]**: o sea, el defecto predice el tamaño casi exacto. VIIRS 375 no lo muestra, y MIROVA
tampoco. El arreglo no exige bajar nada nuevo: el pipeline **ya baja MxD03** (la geolocalización de 1 km
corregida por terreno) y se la pasa a `calculate_vrp` como `geo_path`, que la ignora (docstring, l. 470).

Estudio de sólo lectura: no toca `pipeline/`.

## 1. El fenómeno, primero en el volcán

MODIS barre de lado a lado con un espejo. Cada barrido tiene 1.354 frames de 1 km en el nadir, y los
píxeles se agrandan hacia los bordes: a 45° de cenit un píxel mide unos 2 km a lo largo del barrido, en el
borde casi 5. El producto MOD021KM/MYD021KM no trae la posición de cada píxel: trae una grilla de 271 × 2 por
barrido, uno de cada cinco frames. La documentación del producto dice cuáles: **el frame 2, el 7, el 12…
hasta el 1.352** (MODIS L1B Data Dictionary C7, sección 2.1.5, p. 66, figura 2.1.1: `DimensionMap` con
offset 2 e increment 5, verificado mirando la página renderizada).

`_interp_geo` hace un `scipy.ndimage.zoom` de orden 1, que alinea los extremos: le asigna al frame 0 la
posición del punto grueso 0 (que es el frame 2) y al frame 1.353 la del punto grueso 270 (frame 1.352).
Medido con una rampa de índices sobre la función real: el frame *s* recibe la posición verdadera del frame
**0,9978·s + 2**. En el lado del barrido donde está el frame 0, cada píxel queda rotulado con la posición
de un píxel hasta 2 frames más cerca del nadir; en el otro lado, hasta 1 frame más cerca del nadir. Como
los frames lejanos son anchos, el error en kilómetros crece con el ángulo: unos 1,0 km a 17°, 1,7 km a 31°,
3,0 km a 45° y más de 6 km en el borde, del lado del frame 0. Del otro lado es la mitad o menos, y bajo
unos 20° va levemente hacia afuera.

Para la geología esto significa que un foco térmico puntual, como el cráter de Láscar, aparece corrido
hacia el satélite, más cuanto más oblicua es la mirada, y que el corrimiento cambia de tamaño según de qué
lado de la traza quede el volcán ese día. Ningún fenómeno físico del volcán hace eso.

**Paralaje del terreno.** Una cumbre alta vista de lado, si se ubicara sobre el elipsoide, aparecería
**alejada** del sensor en altura × tan(cenit). MxD03 corrige por terreno píxel a píxel, y los puntos de la
grilla gruesa salen de MxD03, así que lo único que podría sobrar es la diferencia entre la altura del
cráter y la de los puntos vecinos de la grilla (relieve SRTM entre 0,04 km en Puyehue y 1,2 km en
Villarrica, `salidas/alturas_dem.json`). Ese residuo iría hacia afuera y sería igual de los dos lados de
la traza. Lo observado va hacia adentro y es asimétrico: no es paralaje.

**Convención de ángulos.** Antes de decir "hacia el sensor" había que saber hacia dónde apunta el acimut.
Dos pruebas independientes (`convencion_azimut.py`): el acimut solar guardado coincide con el Sol calculado
en el cráter con mediana de 0,25° en MODIS (y 180° con la convención opuesta), y en las pasadas nocturnas
con el sensor al este la hora solar local es menor que con el sensor al oeste (Aqua 26,4 contra 27,6 h),
que es lo que ocurre si el acimut va del píxel al sensor. Así que la convención está bien aplicada.

## 2. Qué se midió

1. **El cráter como fuente limpia (`medir_corrimiento.py`).** En producción el píxel más caliente cerca
   del cráter muchas veces es un valle tibio (A69), así que no sirve para ubicar el cráter. Se usó el brazo
   K de los A/B de S149 (banda 22, sin Test 1, conectiva `max`), donde Láscar entrega uno o dos píxeles por
   pasada casi todos dentro de 2,5 km del cráter: 91 pasadas MODIS nocturnas (88 de Láscar, marzo a junio
   de 2026, y 3 de Nevados de Chillán, octubre) con un píxel a 8 km o menos del cráter (runs
   35632736532, 35648804271, 35671459235, 35679063864, 38560317428). Ajuste por mínimos cuadrados con un
   desplazamiento fijo por volcán (que absorbe un foco real corrido o un `vent_lat` impreciso) más los
   predictores de cada hipótesis, con IC por bootstrap.
2. **Control VIIRS 375**, que trae geolocalización por píxel corregida por terreno (VNP03IMG/VJ103IMG) y no
   pasa por `_interp_geo`: el mismo ajuste en los 11 Tier A de producción con alerta de MIROVA (1.138
   pasadas) y en el brazo K (345 pasadas de Láscar).
3. **Producción y el resto de los volcanes (`desplazamiento_por_familia.py`, `densidad_radial.py`).** Se
   intentó medir en los 11 Tier A comparando el mapa de todos los píxeles anómalos de las pasadas con el
   volcán a un lado de la traza contra el del otro lado. Da cero en todos, y la razón está en
   `densidad_radial.py`: en producción (y en el brazo sin Test 1 de S146) los píxeles anómalos son un disco
   de densidad 4 a 7 veces mayor **dentro de `inner_radius_km`** y plano afuera. Es el umbral de cumbre,
   que se aplica dentro de un círculo medido con nuestra propia geolocalización: el patrón viaja con el
   error y lo esconde. Por eso la medición directa vale sólo donde hay un foco real (Láscar), y para los
   demás volcanes el corrimiento se calcula con el modelo, que depende sólo del ángulo y del lado.
4. **MIROVA (`mirova_tif.py`).** GeoTIFF MODIS de Láscar (164) y Villarrica (217), mayo a septiembre de
   2026, leídos por raw.githubusercontent, uno por md5, con la hora de `acquisition_utc` y la geometría de
   nuestro record de la misma pasada. Casi todos en EPSG:4326 con grilla de 0,0097° × 0,0089° (dos en UTM,
   descartados). Se busca el máximo local de mayor contraste a 5 km o menos del cráter; quedan 41 pasadas
   nocturnas con contraste de 0,02 o más (33 de Láscar, 8 de Villarrica).
5. **Consecuencias (`consecuencias.py`).**

## 3. Números

**Brazo K, 91 pasadas MODIS, casi todas de Láscar** (`salidas/corrimiento_resumen_s149_ab_sin_test1_b22_max.txt`):

| modelo | coeficiente [IC 95 %] | rms |
|---|---|---|
| interpolación sola, frame 0 a la derecha de la traza | 0,90 [0,81; 1,01] | 0,94 km |
| interpolación con el frame 0 a la izquierda (lado equivocado) | coeficiente negativo | 0,94 km |
| sólo un término libre en tan(cenit) | 1,39 km [1,01; 1,85] | 1,06 km |
| paralaje absoluto (h × tan z) junto a la interpolación | +0,14 (hacia el sensor, no hacia afuera) | 0,93 km |

Con la interpolación descontada, el cráter de MODIS queda a (−0,02; +0,22) km de `vent_lat/vent_lon`, y el
de VIIRS a (+0,12; −0,09): coinciden.

Láscar sola: mediana del corrimiento hacia el sensor (km), observado contra predicho por la interpolación
(con paralaje residual, que sería −0,1 a −0,4 km en todas las filas):

| satélite, lado | cenit | n | observado | predicho |
|---|---|---|---|---|
| Aqua, lado del frame 0 (sensor al este) | 0 a 20° | 11 | +1,14 | +0,84 |
| | 20 a 35° | 5 | +1,34 | +1,33 |
| | 35 a 50° | 6 | +2,78 | +2,47 |
| Aqua, otro lado | 0 a 20° | 12 | −0,48 | −0,24 |
| | 20 a 35° | 9 | −0,28 | +0,18 |
| | 35 a 50° | 7 | +0,05 | +0,82 |
| Terra, lado del frame 0 (sensor al oeste) | 0 a 20° | 3 | +1,07 | +0,94 |
| | 20 a 35° | 16 | +1,36 | +1,49 |
| Terra, otro lado | 0 a 20° | 14 | −0,21 | −0,18 |
| | 20 a 35° | 5 | +0,07 | +0,12 |

El paralaje predice lo mismo de los dos lados; lo observado cambia entre 1,3 y 2,7 km según el lado, a
igual satélite y cenit, como predice la interpolación.

Las dos pasadas que la caja apaga (PR #825) quedan dentro de la caja al deshacer el corrimiento: la del
03-27 07:10 (Aqua, 39,9°) pasa de 3,20 km al este a 0,85 km, y la del 03-14 07:05 (44,6°) de 3,47 a 0,69 km.

**Control VIIRS 375.** Término libre en tan(cenit): −0,06 km [−0,11; −0,01] en los 11 Tier A con alerta de
MIROVA (1.138 pasadas, rms 0,60 km) y +0,01 [−0,04; +0,06] en Láscar del brazo K. A 45° eso es menos de
0,1 km: VIIRS no tiene el corrimiento. El fenómeno es de MODIS y de nuestro código, no de la convención de
ángulos ni del terreno.

**MIROVA** (`salidas/mirova_tif_resumen.txt`). El pico de MIROVA cae en las mismas celdas de su grilla con
el volcán a cualquier lado de la traza. Aqua: dE mediano +1,18 km del lado del frame 0 (n = 15) contra
+2,16 km del otro (n = 11), diferencia −0,99 km, cuando nuestra geolocalización daría +3,00. Terra: +0,19
contra +0,19, diferencia 0, cuando la nuestra daría −2,44. MIROVA no tiene el defecto. Queda sin explicar
que los picos de Aqua de MIROVA caigan 1 a 2 km al este del cráter con los dos lados por igual, y los de
Terra no (SIN VERIFICAR; no es la firma de la interpolación porque no depende del lado).

**Producción, 11 Tier A** (`salidas/consecuencias.txt`). Corrimiento predicho en los records MODIS
nocturnos: mediana 1,6 a 2,1 km y percentil 90 de 5 a 7,5 km en todos los volcanes y en los dos
satélites; entre 41 y 51 % de las pasadas pasan de 2 km. Es el mismo en todos los volcanes porque depende
del ángulo, no del volcán. Etiqueta summit/far: con la posición movida, 90 records cambiarían de summit a
far y 50 de far a summit por el `final_hotspot` (de 6.878), y 1.389 y 61 por el centroide del cúmulo. Ese
segundo conteo **no predice** el pipeline corregido: el cúmulo es en buena parte el disco de ruido del
umbral de cumbre, que con la geolocalización corregida se volvería a centrar en el cráter. En las 95
pasadas con alerta MODIS de MIROVA cambian 0 etiquetas por el `final_hotspot` y 3 por el cúmulo.

## 4. Qué decide esto

- **El veto de la caja (D18, PR #825)** pierde su premisa: las dos pérdidas son el corrimiento, no la caja.
  La caja hay que volver a medirla con la geolocalización corregida (A95, A111).
- **Toda auditoría espacial de MODIS (A61, A70)** que haya medido posiciones contra el cráter tiene un error
  de 1 a 7 km que depende del ángulo y del lado. VIIRS no.
- **D17 (remuestreo UTM)**: `_regrid_modis_granule` usa la misma `lat/lon` interpolada; el remuestreo sobre
  una geolocalización corrida reproduce el corrimiento.
- **A46, A81, D11 (summit/far de MODIS)**: el círculo de cumbre, el anillo de fondo y la caja se miden con
  esta geolocalización, así que en pasadas oblicuas el ROI de cumbre queda centrado hasta varios km al lado
  del cráter real. Cuánto de la cara far→summit viene de aquí sólo lo dice el A/B.

## 5. Propuesta de arreglo (no implementada; toca `pipeline/`, regla A45)

**Arreglo:** con un flag `enable_modis_geo_mxd03` (apagado por defecto), que `calculate_vrp` lea
`Latitude`, `Longitude` y los cuatro ángulos de `geo_path` (MxD03, 1 km, corregido por terreno) en vez de
interpolar la grilla de 5 km; si `geo_path` falta o no calza en forma con la banda, que vuelva al
comportamiento de hoy y lo anote en el record. El lector ya existe en `scripts/backfill_geometry.py:106`.
Corregir el `zoom` para respetar offset 2 e increment 5 sería el plan B: arregla el desfase de frames
pero no el bow tie entre barridos ni el paralaje residual entre puntos de la grilla.

**A/B pre-registrable:**
- Brazos: control (producción) y producción + MxD03; y, para ver el cráter limpio, K y K + MxD03.
- Ventana: marzo de 2026 (sustrato MODIS de Láscar, S149) más una ventana con Villarrica activo; los 11
  Tier A para medir etiquetas.
- Criterios: (1) en K + MxD03, el término en tan(cenit) del píxel del cráter cae bajo 0,3 km y la diferencia
  entre los dos lados bajo 0,5 km; (2) ninguna alerta MODIS protegida de MIROVA perdida (criterio de
  victoria de `docs/MISSION.md`); (3) se cuentan aparte summit→far y far→summit por `final_hotspot` y por
  cúmulo, y las publicaciones en negativos limpios antes y después; (4) se repite la caja (KC contra K) con
  MxD03 sobre D1.
- Qué cambiaría: la latitud y longitud de todo píxel, hotspot, cúmulo y distancia de los records MODIS
  (casi la mitad de las pasadas se mueve más de 2 km), y potencialmente qué píxeles pasan los umbrales de
  cumbre, porque el círculo de cumbre se recentra.

## 6. SIN VERIFICAR

- **Comparación directa contra MxD03.** No había `EARTHDATA_TOKEN` en el entorno local y no se usó usuario y
  clave (A71). Queda propuesto el probe `probe_mod03.py` con su workflow `probe_mod03_propuesta.yml` (sólo
  token, sin push), **no despachado**: hay que copiarlo a `.github/workflows/`.
- **El modelo fuera de Láscar.** La medición limpia es de un volcán (más 3 pasadas de Nevados de Chillán).
  Para los otros diez el corrimiento es el del modelo, que no depende del volcán; el residuo de paralaje en
  los de mucho relieve (Villarrica 1,2 km, Llaima 1,0 km) no se pudo medir.
- **El coeficiente 0,90.** Cerca de 1 pero no exactamente; puede venir del modelo simple de tamaño de píxel
  o de la cuantización a píxel entero. La componente a lo largo de la traza (dispersión de 2 km en MODIS
  contra 0,2 km en VIIRS) es compatible con el mismo desfase en líneas, pero no se puede predecir sin la
  línea del gránulo, que el record no guarda.
- **El pico de MIROVA** es un máximo local en un campo de radiancia, no su píxel de alerta.

## Archivos

| archivo | qué hace |
|---|---|
| `comun.py` | geometría común: modelo de la interpolación, Sol, lado de la traza, carga de records |
| `convencion_azimut.py` | comprueba la convención de los acimuts |
| `alturas_dem.py` | alturas SRTM del cráter y de dos anillos (API pública opentopodata) |
| `medir_corrimiento.py` | ajuste por pasada del píxel del cráter (producción o un brazo de A/B) |
| `desplazamiento_por_familia.py` | correlación de mapas de densidad entre los dos lados de la traza |
| `densidad_radial.py` | por qué el patrón de producción no sirve para medir |
| `mirova_tif.py` | pico del cráter en los GeoTIFF MODIS de MIROVA |
| `consecuencias.py` | tamaño del corrimiento en producción, etiquetas, pérdidas de la caja |
| `probe_mod03.py`, `probe_mod03_propuesta.yml` | probe propuesto contra MxD03, no corrido |
| `salidas/` | salidas de todo lo anterior (sin `corrimiento_pasadas_produccion.csv`, 3,7 MB, que se regenera con `medir_corrimiento.py`) |

Para repetir, los brazos de A/B se bajan de los runs citados a una carpeta `<run_id>/<brazo>/<vol>.json` y se
pasa con `--cache`; los TIF van a una carpeta temporal con `--tmp`.
