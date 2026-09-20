# Pre-registro: ¿el cúmulo lejano de un píxel es el objeto que MIROVA vio? (S144)

> **Estado: v7 del 2026-09-19, escrita ANTES de medir.** Corrige los 11 hallazgos del sexto verificador
> (`..._VERIFICADOR_V6.md`). Historia de las versiones: v1 `f6a1cb962`, v3 `9496cdaea`, v4 `70d26d3c7`,
> v5 `c92171901`, v6 `32e9ca4b8`; **la v2 nunca se commiteó**. Cada ronda de verificación con contexto
> limpio refutó el diseño anterior con mediciones, y sus informes están versionados al lado de este
> archivo. Falta: una séptima pasada del verificador y, recién después, el script
> (`experiments/_s144_keep_peak_direccion/`, con tests) y la corrida.
>
> Origen: decisión 1 del traspaso `tasks/BLOQUE_ARRANQUE_S144.md`; Nicolás eligió el 2026-09-19 seguir
> con el rediseño de pasada cruzada.

## 0. Qué cambió en la v7, y por qué

La v6 medía el veredicto **contra el estrato hermano** (las pasadas con patrón donde MIROVA no publicó
fila o publicó un falso positivo), tratándolo como el nivel del instrumento. El sexto verificador lo
descompuso sobre las mismas 681 pasadas: ese nivel vale `+0,0120`, y se parte en **-0,0355 de suelo del
instrumento y +0,0476 de efecto del sitio**. O sea, el nivel contra el que yo restaba **contenía la
señal que la medida quiere estimar**, porque en ese estrato nuestro pipeline publicó exactamente el
mismo objeto. Simulado: si el fenómeno está por igual en los dos estratos, que es lo esperable de un
foco permanente (un lago de lava no sabe qué fila escribió MIROVA esa noche), el positivo **no sale
nunca**, ni con un efecto de +0,27.

La v7 simplifica el estadístico, siguiendo la opción (b) del verificador: **la comparación se hace
dentro del mismo ráster, entre nuestro punto y un punto sorteado**. Así el suelo del instrumento se
cancela por construcción y la banda vuelve a estar en cero, sin ningún nivel que haya que estimar
aparte. Los 5 sitios de referencia salen del veredicto (el sexto verificador midió que son una
población **sesgada**: la razón de tasas contra un punto sorteado llega a 27,8 en Láscar y 11,7 en
Cordón Caulle) y quedan como descriptivos.

Y se separan los dos ejes que hasta ahora se mezclaban:
- **Eje 1, el sitio**: ¿el lugar donde publicamos destaca en el campo de MIROVA, comparado con otro
  punto cualquiera de la misma banda en la misma imagen?
- **Eje 2, la noche**: ¿destaca **más esta noche** que en otras noches en el mismo lugar? La quinta
  ronda ya lo midió fuera de la muestra: `+0,0005`, o sea nuestro cúmulo no es un lugar
  persistentemente más caliente que los otros sitios donde publicamos.

## 1. Lo que ya se vio (contaminación declarada)

- **Lastarria no es ciega** (ronda 1: sus semillas se agrupan en celdas fijas a 1,065, 1,305, 1,396 y
  2,363 km del cráter; la de 2,363 es semilla en 14 alertas y 11 RUTINA).
- **Se conocen los niveles del instrumento fuera de la muestra del veredicto**: imagen propia +0,1091
  contra cruzada +0,0145 sobre las mismas 165 pasadas (ronda 5); con la ventana de la v6, en el estrato
  hermano, nuestro punto +0,0120 y un punto sorteado -0,0355 (ronda 6).
- **Se conoce la geometría de nuestros P**: radio mediano 2,79 km, máximo 3,00 km, y el 97,1 % tiene
  otro P nuestro a menos de 0,75 km en otra noche.
- **Se conoce el embudo**: 1.113 pasadas candidatas (patrón, publicadas, `neg_limpio`, fuera de
  Lastarria); con la ventana de 45 a 120 min quedan **601 pasadas en 349 noches de volcán**, y llegan a
  20 noches **6 volcanes** (Copahue 66, Llaima 63, Villarrica 55, Chaitén 52, NdC 38, PP 27).
- Ninguna ronda calculó el estadístico de §7 sobre la muestra del veredicto, ni las clases de M1.

## 2. El fenómeno

En un cono nevado de noche la radiancia MIR sigue la altitud: dentro del disco de 3 km del Test 1 el
píxel más tibio suele ser el borde de cota baja, no el cráter (A69). `keep_peak` conserva ese píxel
aunque no sea contextual, y el record queda con un cúmulo primario de un solo píxel lejos del cráter
(D19). Apagarlo es lo único que baja la sobre-publicación en el A/B de S143, pero la regla de cero
pérdidas le cobró 5 noches donde MIROVA alertó y un cúmulo nuestro caía dentro de su cota de distancia.

- **La coincidencia fue entre pasadas distintas**: MIROVA alertó en una pasada y el cúmulo que coincidió
  es de otra pasada de la misma noche, de 18 a 78 minutos antes o después.
- **Láscar 2026-06-13 no es un cúmulo lejano** (cúmulo a 0,32 km del cráter, 0,49 km del
  `final_hotspot`): se informa aparte y no llega al pool de M1.
- **Dónde ocurre la coincidencia de radio**: 12 de 15 pasadas en Lastarria; fuera, las que parecen
  compatibles lo son por aritmética del centro de grilla (Cordón Caulle tiene `mirova_center` a 7,57 km
  del cráter, Tupungatito a 4,86 y Planchón-Peteroa a 2,02). **La compatibilidad de radio sólo informa
  donde el centro de grilla está casi sobre el cráter**, así que la coincidencia de S143 es hoy un
  fenómeno de Lastarria.

## 3. Las dos medidas

- **M1, dirección**: donde MIROVA publicó un objeto al mismo radio que nuestro cúmulo, ¿coincide el
  acimut? Sólo se puede hacer en Lastarria. **Sin veredicto** (§6).
- **M2, presencia**: en la imagen que MIROVA hizo de **otra pasada de la misma noche**, ¿el lugar donde
  publicamos destaca más que otro punto de la misma banda (eje 1), y más que en otras noches (eje 2)?
  Cientos de pasadas, **con veredicto sobre el eje 1** (§7).

## 4. Entradas, universo y definiciones

**Sensor: VIIRS 375 m en las tres puntas** (records con `banco_paridad.bucket == "VIIRS375"`, filas de
MIROVA con `sensor_bucket == VIIRS375`, TIF con `sensor == VIIRS375`). **Ventana**: 2026-05-09 hasta el
sha con que se corra.

- Índice y TIF de `mirova-tif-archive` en el commit `da4fe36e8920`, por la API, sin pull (17 GB).
- CONS y OCR de `Mirova-v1` por sha; `Distancia_km` de CONS (el residuo contra el radio de la semilla es
  0,08 km con CONS y 4,24 km con OCR en Cordón Caulle).
- **M1**: para las noches de S143, los records del brazo control congelados en
  `experiments/_s144_keep_peak_direccion/control_s143/` (**19 archivos versionados**); el resto y todo
  M2, producción en el sha de `origin/main` del momento de correr.
- Cráter: `vent_lat`/`vent_lon` de `volcanoes.yaml` (ancla del Test 1, `pipeline/geo_utils.py:53-78`).

**TIF usable**: `size_bytes > 0` y `acquisition_utc` no vacío, a ±120 s de la pasada; imagen propia (su
md5 no aparece bajo una adquisición anterior del mismo volcán); mediana del raster menor que
0,2 W/m² sr µm; CRS legible con rasterio; menos del 10 % de celdas sin dato en el disco de 4 km. La
latencia no excluye: todo se repite con latencia ≤ 8 h como sensibilidad.

**ΔL0** de una celda: L menos la media de sus vecinas con dato, exigiendo al menos 5 de las 8. **z** =
ΔL0 dividido por 1,4826 × MAD de ΔL0 sobre las celdas con ΔL0 del raster. **`Z(X)`** = máximo de z sobre
las celdas con ΔL0 a ≤ T de X, con **T = 0,75 km**.

**Umbral `zc_punto(vol)`** = percentil 95 de `Z(X)` con X sorteado **uniforme en área** en el anillo de
**1,5 a 3,0 km** alrededor del cráter, en las pasadas RUTINA con TIF usable del volcán, un sorteo por
pasada. Sorteo reproducible: un único `random.Random(144)`, volcanes en orden alfabético, pasadas por
`datetime_utc` ascendente, dos números por pasada (primero `u` para `r = sqrt(1,5² + u·(3,0² − 1,5²))`,
después el acimut). Medido por las rondas 5 y 6 con esta regla literal: Chaitén 4,22 [3,19, 4,66],
Cordón Caulle 4,25, Planchón-Peteroa 3,23, Nevados de Chillán 2,47, **Isluga 6,07 [2,04, 7,69] sobre 13
pasadas** (poco confiable, se informa aparte). El script imprime la tabla completa. **`zc_disco(vol)`**
(percentil 95 del máximo de z sobre el disco de 4 km, mismas pasadas) es el umbral del control G, y
**`zc_anillo(vol, d)`** el de M1. Los tres se calibran en rásteres propios y se aplican en cruzados, lo
que queda declarado como límite.

**Candidatos**: **P** es el centroide del cúmulo primario cuando tiene un solo píxel; **F** es el
`final_hotspot` del mismo record. **Patrón**: el record publica según el predicado del dashboard corrido
con node (A97), su cúmulo primario tiene un solo píxel y d(P, F) > 0,5 km. En M1 además d(P, F) ≥ 2T.

## 5. El instrumento de M2

**Imagen (pasada cruzada).** Para cada pasada medida `p`, la imagen es el TIF de otra pasada `q` del
mismo volcán con **45 min ≤ |t_q − t_p| ≤ 120 min** y TIF usable. Se toma la más cercana; empate, la
anterior. Si no existe, la pasada sale y se cuenta aparte. Esa imagen viene de un gránulo que **no**
eligió nuestro píxel, que es lo que corta la maldición del ganador: medido, la misma comparación da
+0,1091 con la imagen propia y +0,0145 con la cruzada. La ventana de 45 a 120 minutos sale de que el
residuo medido vale +0,047 debajo de 45 min. **Queda declarado que la ventana no lo deja en cero**: con
la regla literal el estrato hermano da `+0,0120` [-0,0121, +0,0356], porque 300 de esas 681 pasadas
cambian de pareja al aplicar la regla. Por eso el estadístico de abajo no depende de que ese residuo sea
cero. La ventana además sólo admite pasadas nocturnas, así que el filtro solar de A76 es redundante y se
mantiene sólo como comprobación.

**Punto de comparación (eje 1).** En el **mismo raster `q`** se evalúa, además de `Z_q(P_p)`, un punto
`X_p` sorteado uniforme en área en el anillo de 1,5 a 3,0 km alrededor del cráter, a más de 2T (1,5 km)
de `P_p`, con `random.Random(7144)` y el orden de extracción declarado como en §4.

- `e_p = 1` si `Z_q(P_p) ≥ zc_punto(v)`; `x_p = 1` si `Z_q(X_p) ≥ zc_punto(v)`.
- **Estadístico del eje 1**: `Δ_p = e_p − x_p`, pareado dentro de la misma imagen.

Qué controla: la misma imagen controla el estado de nube y de nieve de esa noche; el sorteo controla el
suelo del instrumento, **que se cancela por construcción** porque los dos puntos se miden con el mismo
umbral en el mismo raster; y la pasada cruzada controla la selección.

**Eje 2, la noche.** `Θ_p = e_p` menos la fracción de `e` en el **mismo punto `P_p`** evaluado en los
rásteres cruzados de otras noches del mismo volcán, a más de 3 días, tomando los 5 más cercanos. La
quinta ronda lo midió fuera de la muestra: `+0,0005` [-0,017, +0,018]. Informa si el sitio destaca más
esta noche que en las otras; **no entra en el veredicto**, orienta su lectura (§8).

**Descriptivo**: se informa también el estadístico de la v6 (nuestro punto contra 5 sitios donde
publicamos otras noches), con el sesgo medido de esa población escrito al lado (razón de tasas contra un
punto sorteado: 27,8 en Láscar, 11,7 en Cordón Caulle, 4,37 contra 6,70 agrupado con esta ventana).

**Controles**:
- **N1, nulo del instrumento (compuerta)**: se repite todo con **dos** puntos sorteados independientes
  en vez de `P_p` y `X_p`, sobre la misma muestra del veredicto. Por simetría debe dar 0; se exige que
  el intervalo del 95 % quede dentro de **±0,05** (la regla se aplica al intervalo, no al punto). Si
  no, la medida es INCONCLUSA.
- **B, tamaño del sesgo de selección (informado, no compuerta)**: el mismo procedimiento con la imagen
  propia en vez de la cruzada, sobre el estrato hermano con las dos imágenes usables.
- **G, georreferencia (compuerta)**: pasadas con alerta CONS con VRP ≥ 0,3 MW en Láscar y Villarrica con
  TIF usable (52 pasadas, 49 de Láscar); semilla = máximo de z en el disco de 4 km alrededor del cráter
  con `z ≥ zc_disco`. Pasa si n ≥ 8, la semilla cae a ≤ 0,75 km del cráter en al menos el 80 %, la
  mediana de esa distancia es ≤ 0,5 km y **el valor absoluto de la mediana** del desplazamiento es menor
  que 0,19 km en cada eje. Valida casi sólo Láscar. Si falla, las dos medidas terminan INCONCLUSAS.
- **H, alineación (compuerta blanda)**: pasadas con alerta, TIF usable y record con
  `primary_cluster.n_pixels ≥ 2`, `final_hotspot_source == "ctx_cluster"` y centroide dentro del
  `inner_radius_km` (110 pasadas, 50 de Cordón Caulle, que se informa con y sin él). La semilla debe
  caer a ≤ 0,75 km de nuestro centroide en al menos la mitad. Si no, todo veredicto baja a SOSPECHA.

## 6. M1: dirección, donde la coincidencia de radio ocurre

**Universo**: pasadas con alerta CONS, TIF usable, record con patrón y d(P, F) ≥ 2T, con P y F dentro de
la región de búsqueda (unión del disco de 3,4 km alrededor del cráter y el disco de `Distancia_km` + 1 km
alrededor de `mirova_center`), con |r_P(mirova_center) − `Distancia_km`| ≤ 0,55 km y en volcanes donde
`mirova_center` está a menos de 1 km del cráter. Eso da **12 pasadas, todas de Lastarria**.

**Semilla**: máximo de z sobre el anillo |r − `Distancia_km`| ≤ 0,6 km dentro de la región, con
`z ≥ zc_anillo`. Si no hay, la pasada queda **sin identidad**.

**Clases** (T = 0,75 km): `P` si d(semilla, P) ≤ T y d(semilla, F) > T; `F` si d(semilla, F) ≤ T y
d(semilla, P) > 2T; `otro` si d(semilla, P) > 2T y d(semilla, F) > T; `indefinido` en el resto, incluida
la corona entre T y 2T alrededor de P, que se informa aparte.

**Declarado de antemano**: en Lastarria la clase `F` es **geométricamente imposible** (su `mirova_center`
está a 0,12 km del cráter y sus `Distancia_km` son 2,19, 2,40 y 2,70 km), y como M1 son sólo pasadas de
Lastarria, `F` es inalcanzable en todo M1. **Contraste temporal**: por cada pasada se informa cuántas
veces la celda de la semilla es el máximo del mismo anillo en las pasadas RUTINA del volcán (la ronda 3
midió que la celda a 2,363 km lo es en 5 a 7 de 31). Sin eso, "la semilla cae sobre P" no separa el
objeto de esa noche de la fuente fumarólica permanente.

**Las noches de S143** se informan una por una (Isluga 2026-06-16, Lastarria 2026-06-07, 2026-06-14 y
2026-07-25), con todos los records del control con patrón de esa noche y cada par (semilla, record) con
su clase. Isluga no tiene TIF en sus pasadas con alerta; Lastarria 06-14 tampoco en la pasada del record
que coincidió. **M1 no tiene veredicto.**

## 7. M2: el veredicto (eje 1)

**Universo**: pasadas VIIRS 375 nocturnas de producción con patrón, publicadas, con imagen cruzada
usable. Se estratifica por etiqueta (`pos`, `neg_limpio`, y aparte `far_ref` y `sin_info`), por volcán y
por tramo (antes y después de #535, A104). **El veredicto se toma sobre los negativos limpios fuera de
Lastarria**: con la ventana de la v6 son 601 pasadas en 349 noches y 6 volcanes con 20 noches.

**Estadístico**: `Δ_v` = media de `Δ_p` por volcán; `Δ` = estimación agrupada con **remuestreo por noche
de volcán** (A94), estratificado **por volcán**, 2.000 réplicas, `random.Random(144)`, estratos en orden
alfabético. El mismo estimador y la misma estratificación se usan en todos los controles.

**Veredicto**, con al menos 30 noches de volcán y al menos 3 volcanes con 20 noches:
- **"el cúmulo lejano cae sobre un exceso del campo de MIROVA"** si el intervalo del 95 % de `Δ` queda
  entero por encima de **+0,05** y `Δ_v > 0` en al menos dos tercios de los volcanes con 20 noches;
- **"no se distingue de otro punto de la misma banda"** si el intervalo del 95 % de `Δ` queda entero
  dentro de **±0,05**;
- en cualquier otro caso, INCONCLUSO. Con menos de 3 volcanes con 20 noches, la segunda condición del
  positivo no es evaluable y el veredicto es INCONCLUSO.

Las dos condiciones se evalúan sobre el **intervalo**, no sobre el punto, y en este orden: primero la
del positivo, después la de equivalencia.

**Mapa de potencia declarado** (medido por la ronda 6 con la estructura real de noches, para que nadie
lea un INCONCLUSO como hallazgo): con la regla contra cero, un efecto de +0,064 da el positivo el 13 %
de las veces, +0,083 el 87 % y +0,131 el 100 %; bajo el nulo la regla no produjo ningún falso positivo
en 200 repeticiones. El tramo posterior a #535 tiene 75 noches, ancho de intervalo 0,083 y **cero
volcanes con 20 noches**, así que ahí la condición por volcán no es evaluable: los tramos se informan y
el veredicto se toma sobre la muestra completa.

## 8. Qué se hace con el resultado

Compuertas: **G**, **N1** y, en blando, **H**. Si G o N1 fallan, INCONCLUSO; si H falla, todo baja a
SOSPECHA. (Los controles C1 y C2 de versiones anteriores ya no existen.)

| eje 1 (veredicto) | eje 2 (la noche) | Lectura | Siguiente paso propuesto |
|---|---|---|---|
| no se distingue | cualquiera | lo que `keep_peak` publica no destaca en el campo de MIROVA más que cualquier punto de la misma banda | pre-registrar una cota con dirección y re-evaluar el A/B S143 con ella, sin re-correrlo |
| cae sobre un exceso | ≈ 0 (como midió la ronda 5 fuera de la muestra) | el sitio destaca siempre, no esa noche: es un rasgo estable del campo (relieve tibio o fuente permanente), no un evento | no apagar `keep_peak` a ciegas; el frente pasa a separar relieve de fuente, que el TIF por sí solo no hace |
| cae sobre un exceso | claramente positivo | hay algo de esa noche en el lugar donde publicamos | no decide entre actividad y nube; pide un frente nuevo |
| INCONCLUSO, o G o N1 fallan | | | informar y no mover nada |

M1 acompaña y no decide.

## 9. Límites conocidos

- El eje 1 no distingue **relieve tibio** de **fuente volcánica**: mide si el lugar destaca en el campo
  de radiancia, no por qué. Esa separación es la que A83 declara agotada por vía física y sólo el eje
  espacial resuelve.
- La pasada cruzada corta el sesgo de selección, no los artefactos que duran lo que separa las dos
  pasadas: un borde de nube puede estar en las dos.
- Los umbrales se calibran en rásteres propios y se aplican en cruzados.
- `zc_punto` de Isluga se calibra con 13 pasadas y su intervalo va de **2,04** a 7,69: ese volcán se
  informa aparte.
- Los TIF geográficos son un remuestreo de MIROVA con método no documentado; G lo valida en Láscar.
- La hora de adquisición del índice puede no ser la de la imagen (A106); el md5 propio y la mediana
  nocturna lo acotan sin probarlo imagen por imagen.
- M1 son 12 pasadas de un solo volcán y no puede generalizar.
- El indicador es binario y tira a cero la mayoría de los `Δ_p` (la ronda 6 midió 72,1 % con el
  estadístico anterior). Se informa también el rango de `Z_q(P_p)` entre los `Z_q` de los sitios de
  referencia, cuyo nulo es 0,5, como estadístico continuo descriptivo.
