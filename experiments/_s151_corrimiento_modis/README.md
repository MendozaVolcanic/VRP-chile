# Corrimiento del píxel MODIS del cráter (tarea 1.15)

**Veredicto (corregido tras el verificador con contexto limpio, `verificador/INFORME.md`, PARCIAL):**

- **El defecto de código está CONFIRMADO.** La interpolación de la geolocalización MODIS de 5 km a 1 km
  (`_interp_geo`, `pipeline/process_modis.py:342`) estira la grilla gruesa de punta a punta sin respetar que
  su primer punto corresponde al frame 2 del barrido. Cada píxel queda rotulado con la posición de un píxel
  más cerca del nadir (hacia el sensor).
- **MxD03 se baja y se ignora: CONFIRMADO.** La geolocalización de 1 km corregida por terreno se pide en
  `pipeline/fetch.py:189-194,791-792`, se exige y se pasa en `scripts/run_pipeline.py:223-236`, y
  `calculate_vrp` no la lee (`pipeline/process_modis.py:470`).
- **El efecto sobre el cráter está medido en un solo brazo y casi un solo volcán.** Son las 91 pasadas MODIS
  del brazo K, 88 de ellas de Láscar. Ahí el modelo geométrico explica buena parte del corrimiento, pero el
  tamaño depende del modelo de ajuste (0,90 sin término libre, 1,20 con él) y queda un residuo que se aleja
  del sensor. En producción no se ve: está enmascarado (sección 3).
- **Lo que decide es el probe contra MxD03.** Está en el PR #827 y todavía no se ha corrido (sección 6).

Estudio de sólo lectura: no toca `pipeline/`.

## 1. El fenómeno, primero en el volcán

MODIS barre de lado a lado con un espejo. Cada barrido tiene 1.354 frames de 1 km en el nadir, y los
píxeles se agrandan hacia los bordes: a 45° de cenit un píxel mide unos 2 km a lo largo del barrido y en el
borde casi 5. El producto MOD021KM/MYD021KM no trae la posición de cada píxel. Trae una grilla de 271 × 2
por barrido, uno de cada cinco frames, y la documentación dice cuáles: **el frame 2, el 7, el 12… hasta el
1.352**. Está en el MODIS L1B Data Dictionary C7, sección 2.1.5, p. 66, figura 2.1.1 (`DimensionMap` con
offset 2 e increment 5), verificado en la página renderizada.

`_interp_geo` hace un `scipy.ndimage.zoom` de orden 1, que alinea los extremos. Al frame 0 le asigna la
posición del punto grueso 0, que en realidad es el frame 2, y al frame 1.353 la del punto grueso 270, que
es el frame 1.352. El verificador pasó una rampa por la función real (`verificador/v1_mapeo.py`) y obtuvo
que el frame *s* recibe la posición verdadera del frame **0,99778·s + 2,000**.

En kilómetros, del lado del barrido donde está el frame 0, el corrimiento es:

| cenit | 17° | 45° | 55° |
|---|---|---|---|
| lado del frame 0 | 1,00 km | 3,01 km | 4,97 km |
| otro lado | −0,09 km | 1,10 km | 2,21 km |

Siempre va hacia el nadir, salvo bajo unos 20° del otro lado.

Para la geología, esto quiere decir que un foco puntual como el cráter de Láscar debería aparecer corrido
hacia el satélite, más cuanto más oblicua es la mirada. Y el tamaño debería cambiar según de qué lado de la
traza quede el volcán ese día. Ningún fenómeno del volcán hace eso.

**Paralaje del terreno.** Una cumbre vista de lado, ubicada sobre el elipsoide, aparecería **alejada** del
sensor en altura × tan(cenit): para Láscar, 4,4 km a 40°. Ese término no está en los datos, lo que cuadra
con que MxD03 corrige por terreno. Lo que puede sobrar es la diferencia entre la altura del cráter y la de
los puntos vecinos de la grilla gruesa (relieve SRTM entre 0,04 km en Puyehue y 1,2 km en Villarrica,
`salidas/alturas_dem.json`). Ese residuo también se alejaría del sensor. El término dominante del
corrimiento observado va hacia el sensor, así que no es paralaje. Pero el residuo de la sección 3 tiene el
signo del paralaje residual, así que **algo de paralaje no se puede descartar**.

**Convención de ángulos.** Antes de decir "hacia el sensor" había que saber hacia dónde apunta el acimut.
Hay dos pruebas independientes (`convencion_azimut.py`):

- El acimut solar guardado coincide con el Sol calculado en el cráter, con mediana de 0,25° en MODIS. Con
  la convención opuesta la diferencia sería de 180°.
- En las pasadas nocturnas con el sensor al este, la hora solar local es menor que con el sensor al oeste
  (Aqua: 26,4 contra 27,6 h). Eso ocurre si el acimut va del píxel al sensor.

La convención está bien aplicada.

## 2. Qué se midió

1. **El cráter como fuente limpia (`medir_corrimiento.py`).** En producción, el píxel más caliente cerca
   del cráter muchas veces es un valle tibio (A69), así que no sirve para ubicar el cráter. Se usó el
   brazo K de los A/B de S149 (banda 22, sin Test 1, conectiva `max`). Ahí Láscar entrega uno o dos
   píxeles por pasada, casi todos a menos de 2,5 km del cráter.
   - Son 91 pasadas MODIS nocturnas con un píxel a 8 km o menos del cráter: 88 de Láscar (marzo a junio
     de 2026) y 3 de Nevados de Chillán (octubre).
   - Runs: 35632736532, 35648804271, 35671459235, 35679063864 y 38560317428.
   - Ajuste por mínimos cuadrados con un desplazamiento fijo por volcán (absorbe un foco real corrido o un
     `vent_lat` impreciso), más los predictores de cada hipótesis, con IC por bootstrap. El verificador
     lo reajustó por su cuenta desde el CSV (`verificador/v2_reajuste.py`).
2. **Control VIIRS 375.** VIIRS trae geolocalización por píxel corregida por terreno (VNP03IMG y VJ103IMG,
   `pipeline/process_viirs.py:444`) y no pasa por `_interp_geo`. El control comparable es VIIRS en el
   **mismo brazo K** (`verificador/v5_viirs_k.py`).
3. **Producción y el resto de los volcanes (`desplazamiento_por_familia.py`, `densidad_radial.py`).** Se
   comparó el mapa de todos los píxeles anómalos de las pasadas con el volcán a un lado de la traza contra
   el del otro lado, en los 11 Tier A. Da cero en todos.
4. **MIROVA (`mirova_tif.py`).** GeoTIFF MODIS de Láscar (164) y Villarrica (217), mayo a septiembre de
   2026, leídos por raw.githubusercontent.
   - Uno por md5, con la hora de `acquisition_utc` de `index.csv` (el TIF no la trae) y la geometría de
     nuestro record de la misma pasada.
   - EPSG:4326 con grilla de 0,0097° × 0,0089°; dos en UTM, descartados.
   - Se toma el máximo local de mayor contraste a 5 km o menos del cráter. Quedan 41 pasadas nocturnas con
     contraste de 0,02 o más: 33 de Láscar y 8 de Villarrica.
5. **Consecuencias (`consecuencias.py`).**

## 3. Números

**Brazo K, 91 pasadas MODIS, 88 de Láscar** (`salidas/corrimiento_resumen_s149_ab_sin_test1_b22_max.txt` y
`verificador/v2_salida.txt`). Desplazamiento fijo por volcán:

| modelo | coeficiente [IC 95 %] | rms |
|---|---|---|
| interpolación sola, frame 0 a la derecha de la traza | 0,90 [0,80; 1,01] | 0,937 km |
| interpolación sola, lado invertido | +0,15 [+0,01; +0,33] | 1,164 km |
| interpolación + término libre simétrico en tan(cenit) | interpolación 1,20 [1,04; 1,34]; libre −0,77 [−1,06; −0,47], o sea se aleja del sensor | 0,924 km |
| sólo término libre en tan(cenit) | 1,39 [1,01; 1,85] | 1,06 km |
| interpolación + columna −h·tan(cenit) | +0,14 sobre esa columna: el aporte es −0,14·h·tan(cenit), o sea **se aleja** del sensor (unos 0,7 km a 45° con h = 5,2 km) | 0,93 km |

**El 0,90 depende del modelo.** Con un término libre en tan(cenit), la interpolación sube a 1,20 y aparece
un residuo de −0,77 km por unidad de tan(cenit) que se aleja del sensor. Tiene el signo del paralaje
residual. La interpolación sigue siendo el término que explica la mayor parte, pero el tamaño exacto no
está fijado.

**Lo que distingue un lado del otro.** Hay tres evidencias, y una es más débil que las otras dos:

- **Modelo invertido.** Con el lado correcto, el rms es 0,937 km; con el lado invertido, el coeficiente cae
  a +0,15 y el rms sube a 1,164 km. Si el desplazamiento fijo es por volcán **y satélite**, la diferencia
  casi se borra: lado correcto 0,77 [0,65; 0,88] con rms 0,914, invertido +0,68 [0,54; 0,89] con rms 0,935.
- **Contraste este/oeste entre Aqua y Terra.** Del lado del frame 0, el sensor de Aqua queda al este y el
  de Terra al oeste. Los dos corren hacia su sensor, con mediana de +1,34 km Aqua y +1,32 km Terra: o sea,
  en direcciones geográficas opuestas. Un foco real corrido o un `vent_lat` mal puesto movería ambos hacia
  el mismo lado.
- **Asimetría dentro de cada satélite.** En Aqua se ve: 2,16 [1,28; 2,62] km por tan(cenit) del lado del
  frame 0, contra 0,74 [0,31; 1,22] del otro. **En Terra no se distingue un lado del otro**: 1,41 [0,58;
  2,35] contra 1,20 [0,09; 2,23].

Láscar sola, mediana del corrimiento hacia el sensor (km), observado contra lo que predice la interpolación
con coeficiente 1:

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

**Nulo de producción.** En producción, en las pasadas con alerta MODIS de MIROVA (95 pasadas, 86 de
Láscar), el término libre en tan(cenit) da **−0,38 km [−1,42; +0,70]** según el verificador, y
−0,38 [−1,55; +0,64] con el bootstrap de `salidas/corrimiento_resumen_produccion.txt`. **No se ve el
corrimiento.** La razón es que en producción los píxeles anómalos cerca del cráter no son rasgos del
terreno. Son un disco que pone el umbral de cumbre dentro de `inner_radius_km`, más los que marca el Test 1
integrado dentro de un círculo en torno al cráter. Los dos círculos se miden con nuestra propia
geolocalización corrida, así que el patrón viaja con el error y lo tapa. `densidad_radial.py` lo muestra:
la densidad es 4 a 7 veces mayor dentro de `inner_radius_km` y plana afuera, en producción y en el brazo
sin Test 1 de S146. Por eso **toda la evidencia directa descansa en el brazo K, con 88 de 91 pasadas de
Láscar**. Para los otros diez volcanes, el corrimiento es el del modelo, que depende sólo del ángulo y del
lado.

**Control VIIRS 375.** En el brazo K, el término libre en tan(cenit) da **+0,011 km [−0,053; +0,070]** en 345
pasadas, con bootstrap por noche: VIIRS no tiene el corrimiento, y MODIS en el mismo brazo da +1,39
[+0,91; +1,80]. El control de producción (−0,06 km [−0,11; −0,01] en 1.138 pasadas con alerta en los 11
Tier A) es menos limpio. Ahí el Test 1 enmascara igual que en MODIS, así que vale sólo como indicio.

**MIROVA** (`salidas/mirova_tif_resumen.txt`). El pico de MIROVA cae en las mismas celdas de su grilla con
el volcán a cualquier lado de la traza:

| satélite | dE mediano, lado del frame 0 | dE mediano, otro lado | diferencia MIROVA | diferencia con nuestra geolocalización |
|---|---|---|---|---|
| Aqua | +1,18 km (n = 15) | +2,16 km (n = 11) | −0,99 km | +3,00 km |
| Terra | +0,19 km (n = 3) | +0,19 km (n = 4) | 0 | −2,44 km |

MIROVA no muestra la firma del defecto. Terra tiene muy pocas pasadas, y que los picos de Aqua caigan 1 a
2 km al este del cráter con los dos lados por igual queda sin explicar.

**Producción, 11 Tier A** (`salidas/consecuencias.txt`). El corrimiento que predice el modelo en los records
MODIS nocturnos es:

- mediana de 1,6 a 2,1 km y percentil 90 de 5 a 7,5 km, en todos los volcanes y en los dos satélites;
- entre 41 y 51 % de las pasadas pasan de 2 km.

Etiqueta summit/far con la posición movida:

- por el `final_hotspot`, de 6.878 records, 90 pasarían de summit a far y 50 de far a summit;
- por el centroide del cúmulo, 1.389 y 61.

Ese segundo conteo **no predice** el pipeline corregido: el cúmulo es en buena parte el disco de ruido del
umbral de cumbre, que con la geolocalización corregida se volvería a centrar en el cráter. En las 95 pasadas
con alerta MODIS de MIROVA cambian 0 etiquetas por el `final_hotspot` y 3 por el cúmulo.

## 4. Qué decide esto

- **El veto de la caja (D18, PR #825) queda en duda; no está refutado.** Las dos pasadas que la caja apaga
  quedarían a 0,85 y 0,69 km del cráter si se deshace el corrimiento, o sea dentro de la caja: la del 03-27
  07:10 (Aqua, 39,9°) estaba a 3,20 km al este y la del 03-14 07:05 (44,6°) a 3,47. Pero esa cuenta tiene
  tres debilidades:
  - aplica el modelo con coeficiente 1, cuando el ajuste da entre 0,90 y 1,20 según el modelo;
  - ignora la componente a lo largo de la traza;
  - son píxeles débiles, de 0,7 y 0,9 K sobre el fondo.

  La caja hay que volver a medirla con la geolocalización corregida (A95, A111), después del probe.
- **Auditorías espaciales de MODIS (A61, A70).** Si el probe confirma, toda auditoría que haya medido
  posiciones MODIS contra el cráter tiene un error de 1 a 7 km que depende del ángulo y del lado. VIIRS no.
- **D17 (remuestreo UTM).** `_regrid_modis_granule` usa la misma `lat/lon` interpolada, así que remuestrea
  sobre la geolocalización corrida.
- **A46, A81 y D11 (summit/far de MODIS).** El círculo de cumbre, el anillo de fondo y la caja se miden con
  esta geolocalización. Cuánto de la cara far→summit viene de aquí sólo lo dice el A/B.

## 5. Propuesta de arreglo (no implementada; toca `pipeline/`, regla A45)

**Antes de tocar `pipeline/` hay que correr el probe de la sección 6.**

**Arreglo.** Un flag `enable_modis_geo_mxd03`, apagado por defecto. Con el flag encendido, `calculate_vrp`
lee `Latitude`, `Longitude` y los cuatro ángulos de `geo_path` (MxD03, 1 km, corregido por terreno) en vez
de interpolar la grilla de 5 km. Si `geo_path` falta o no calza en forma con la banda, vuelve al
comportamiento de hoy y lo anota en el record. El lector ya existe en `scripts/backfill_geometry.py:106`.

**Plan B.** Corregir el `zoom` para que respete el offset 2 y el increment 5. Arregla el desfase de frames,
pero no el bow tie entre barridos ni el paralaje residual entre los puntos de la grilla.

**A/B pre-registrable:**

- **Brazos:** control (producción) contra producción + MxD03; y, para ver el cráter limpio, K contra
  K + MxD03.
- **Ventana:** marzo de 2026 (sustrato MODIS de Láscar, S149) más una ventana con Villarrica activo, en los
  11 Tier A para medir etiquetas.
- **Criterios:**
  1. En K + MxD03, el término en tan(cenit) del píxel del cráter cae bajo 0,3 km, y la diferencia entre los
     dos lados también.
  2. Ninguna alerta MODIS protegida de MIROVA se pierde (criterio de victoria de `docs/MISSION.md`).
  3. Se cuentan aparte summit→far y far→summit, por `final_hotspot` y por cúmulo, y las publicaciones en
     negativos limpios antes y después.
  4. Se repite la caja (KC contra K) con MxD03 sobre la ventana D1.
- **Qué cambiaría:** la latitud y longitud de todo píxel, hotspot, cúmulo y distancia en los records MODIS.
  Y potencialmente qué píxeles pasan los umbrales de cumbre, porque el círculo de cumbre se recentra.

## 6. El probe que decide (PR #827), con el criterio escrito antes de correrlo

El probe compara píxel a píxel la geolocalización que da hoy `_interp_geo` contra la de MxD03 en 7
gránulos MODIS de Láscar:

| gránulo | satélite | lado de la traza | cenit | por qué |
|---|---|---|---|---|
| 2026-03-14 07:05 | Aqua | lado del frame 0 | 44,6° | pasada del veto |
| 2026-03-27 07:10 | Aqua | lado del frame 0 | 39,9° | pasada del veto |
| 2026-03-15 07:45 | Aqua | otro lado | 30,5° | |
| 2026-04-23 08:00 | Aqua | otro lado | 43,2° | |
| 2026-03-19 01:55 | Terra | lado del frame 0 | 31,2° | |
| 2026-03-16 01:35 | Terra | otro lado | 10,4° | |
| 2026-03-18 01:15 | Terra | otro lado | 46,8° | |

Los 14 archivos (L1B y MxD03) están en CMR (consultado el 2026-10-15). Script, prueba sintética y workflow
`.github/workflows/probe-s151-mod03.yml` en `experiments/_s151_probe_mod03/`. **Todavía no se ha corrido.**

**Criterio, fijado antes de correr** (copiado del README del probe):

- **CONFIRMA** si se cumplen las dos condiciones, en el píxel MxD03 más cercano al cráter de cada gránulo:
  - en los 7 gránulos, la diferencia entre `_interp_geo` y MxD03 a lo largo del barrido coincide con la
    que predice la regla 0,99778·s + 2 (posición MxD03 del frame fraccionario contra la del frame *s*)
    dentro de 0,3 km;
  - en los gránulos del lado del frame 0 con cenit de 30° o más, esa diferencia es de 1,0 km o más hacia
    el sensor.
- **REFUTA** si la diferencia en el píxel del cráter queda bajo 0,3 km en los 7 gránulos, o si su signo
  contradice al predicho en algún gránulo donde la predicción pase de 1 km.
- **Cualquier otro resultado es PARCIAL.**

Además, el probe responde tres cosas que hoy están SIN VERIFICAR, sin que entren al veredicto:

- con qué offset (0 a 4) los puntos gruesos de L1B coinciden con MxD03 en cada eje, incluido el eje a lo
  largo de la traza;
- si el frame 0 queda a la derecha de la traza;
- dónde cae el píxel más brillante en banda 22 con cada geolocalización.

## 7. SIN VERIFICAR

- **La comparación directa contra MxD03**, que es lo que decide (sección 6).
- **El offset a lo largo de la traza.** El documento sólo muestra el mapa de los frames. La rampa da 2
  líneas en los bordes del gránulo y 0 en el centro, pero que el punto grueso corresponda a la línea 2 de
  cada barrido no está en la documentación.
- **Que el frame 0 quede a la derecha de la traza.** Se infirió de los datos, no de la documentación.
- **El modelo fuera de Láscar.** La medición limpia es de un volcán (más 3 pasadas de Nevados de Chillán).
  El residuo de paralaje en los volcanes de mucho relieve (Villarrica 1,2 km, Llaima 1,0 km) no se midió.
- **El tamaño exacto.** Entre 0,90 y 1,20 según el modelo, con un residuo que se aleja del sensor.
- **La hora de los TIF de MIROVA.** Sale de `index.csv` del archivo, no del TIF.
- **El sesgo de Aqua hacia el este en MIROVA**, de 1 a 2 km e igual en los dos lados, no está explicado.
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
| `verificador/` | informe del verificador con contexto limpio y sus scripts `v1`, `v2` y `v5`, con salidas (rutas relativas) |
| `salidas/` | salidas de lo anterior |

Sobre `salidas/`: `corrimiento_pasadas_s149_ab_sin_test1_b22_max.csv` (una fila por pasada del brazo K) va
con `git add -f`, porque el repo ignora los CSV. `corrimiento_pasadas_produccion.csv` (3,7 MB) no se sube y
se regenera con `medir_corrimiento.py`.

Para repetir: los brazos de A/B se bajan de los runs citados a una carpeta `<run_id>/<brazo>/<vol>.json` y
se pasa con `--cache`; los TIF van a una carpeta temporal con `--tmp`.
