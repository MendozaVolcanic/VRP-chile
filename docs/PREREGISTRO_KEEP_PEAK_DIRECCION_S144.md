# Pre-registro: ¿el cúmulo lejano de un píxel es el objeto que MIROVA vio? (S144)

> **Estado: v5 del 2026-09-19, escrita ANTES de medir.** Corrige los 8 hallazgos del cuarto verificador
> (`..._VERIFICADOR_V4.md`), que siguió al tercero (`..._V3.md`), al segundo (`..._V2.md`) y al primero
> (`..._VERIFICADOR.md`). Versiones anteriores: v1 en `f6a1cb962`, v3 en `9496cdaea`, v4 en `70d26d3c7`;
> **la v2 nunca se commiteó** (la sobrescribí antes de pasarla por git). Falta: una quinta pasada del
> verificador y, recién después, el script (`experiments/_s144_keep_peak_direccion/`, con tests) y la
> corrida.
>
> Origen: decisión 1 del traspaso `tasks/BLOQUE_ARRANQUE_S144.md`; Nicolás eligió el 2026-09-19 seguir
> con el rediseño de pasada cruzada. Muestra: `experiments/_s144_conteo_tif/RESULTADO.md`. A/B que
> motiva la medida: `experiments/_s143_evaluador/`. Instrumento heredado: `experiments/_s142_ndc/`.

## 0. Por qué la v5 cambia el instrumento

La v4 comparaba el mismo punto en otras noches. El cuarto verificador midió que ese control **no tiene
sesgo propio** (nulo -0,0068, intervalo [-0,029, +0,016]) y que la regla de equivalencia sí deja
alcanzables las tres salidas. Pero encontró el problema de fondo:

**La maldición del ganador.** Nuestro detector conserva ese píxel porque fue el exceso local más alto de
ese gránulo VIIRS, y el TIF de MIROVA está hecho **del mismo gránulo**. Preguntarle a esa imagen "¿hay
algo ahí?" devuelve en parte lo que nuestro propio detector puso, sea lava, borde de nube o ruido del
detector. Medido fuera de la muestra del veredicto: **+0,0835, intervalo [+0,035, +0,136]**, del tamaño
del umbral con que se decidía. El control declarado no lo veía, porque sorteaba el punto en vez de usar
el nuestro.

Y el estadístico temporal tenía un segundo problema: **es ciego a los focos permanentes** (lago de lava,
Lazufre, lacolito), que son la categoría b que A54 pide no destruir. Preguntar "¿está más caliente esta
noche?" los deja fuera por construcción.

**La v5 cambia la imagen con que se mide**: en vez del TIF de la misma pasada, usa el TIF de **otra
pasada de la misma noche**. VIIRS pasa dos o tres veces por noche con satélites distintos, así que esa
imagen viene de un gránulo que **no** eligió nuestro píxel. Eso corta la maldición del ganador, y como
sigue siendo la misma noche, un foco permanente o una anomalía que dure la noche siguen ahí. Medido:
de 2.541 pasadas con el patrón, **1.824 tienen otra pasada esa noche con TIF** (Copahue 287, Villarrica
248, Llaima 242, NdC 209, Lastarria 206, PP 160, Chaitén 158, Tupungatito 123, Láscar 81, Isluga 71,
Cordón Caulle 39).

**Y el punto de comparación deja de ser el reflejo o la otra noche**: son **los P que nuestro propio
pipeline publicó otras noches en ese mismo volcán**, evaluados en la misma imagen. Mismo tipo de lugar
(misma textura de flanco, que es lo que refutó a la v3), misma imagen (mismo estado de nube y de nieve,
que es lo que la v4 no controlaba), y ninguno de los dos elegido por el gránulo que estamos mirando.

## 1. Lo que ya se vio (contaminación declarada)

- **Lastarria no es ciega**: la ronda 1 midió las semillas de sus alertas y RUTINA (celdas fijas a
  1,065, 1,305, 1,396 y 2,363 km del cráter; la de 2,363 es semilla en 14 alertas y 11 RUTINA).
- **Se conoce el orden de magnitud del sesgo de selección**: +0,0835 con la misma pasada (ronda 4), y
  las tasas de exceso de nuestros P fuera de la muestra (0,165 observada contra 0,081 de referencia).
- **Se conoce la geometría de nuestros P**: radio mediano 2,79 km, máximo 3,00 km (el borde del disco
  del Test 1), y el 97,1 % tiene otro P nuestro a menos de 0,75 km en otra noche, con mediana de 12
  noches. Ese dato es el que obliga a la regla de separación de §5.
- Ninguna ronda calculó `Z` sobre los P de la muestra del veredicto en pasadas cruzadas, ni las clases
  de M1.

## 2. El fenómeno

En un cono nevado de noche la radiancia MIR sigue la altitud: dentro del disco de 3 km del Test 1 el
píxel más tibio suele ser el borde de cota baja, no el cráter (A69). `keep_peak` conserva ese píxel
aunque no sea contextual, y el record queda con un cúmulo primario de un solo píxel lejos del cráter
(D19). Apagarlo es lo único que baja la sobre-publicación en el A/B de S143, pero la regla de cero
pérdidas le cobró 5 noches donde MIROVA alertó y un cúmulo nuestro caía dentro de su cota de distancia.

- **La coincidencia fue entre pasadas distintas**: MIROVA alertó en una pasada y el cúmulo que coincidió
  es de otra pasada de la misma noche, de 18 a 78 minutos antes o después.
- **Láscar 2026-06-13 no es un cúmulo lejano** (cúmulo a 0,32 km del cráter, 0,49 km del
  `final_hotspot`): se informa aparte y no llega al pool de M1, que exige d(P, F) ≥ 1,5 km.
- **Dónde ocurre la coincidencia de radio**: 15 pasadas en Lastarria con 12 compatibles y 24 fuera con
  4 compatibles, pero 3 de esas 4 son de Cordón Caulle, donde `mirova_center` está a 7,57 km del cráter
  y MIROVA publica distancias de 7,65 a 8,10 km: ahí cualquier punto cercano al cráter cumple la
  compatibilidad por aritmética del centro de grilla. Lo mismo vale para Tupungatito (4,86 km) y
  Planchón-Peteroa (2,02 km). **La compatibilidad de radio sólo informa donde el centro de grilla está
  casi sobre el cráter**, y entonces la coincidencia de S143 es hoy un fenómeno de Lastarria, con una
  pasada de Láscar (separación 0,83 km) como único caso fuera.

## 3. Las dos medidas

- **M1, dirección**: donde MIROVA publicó un objeto al mismo radio que nuestro cúmulo, ¿coincide el
  acimut? Es la pregunta de A107 y hoy sólo se puede hacer en Lastarria y en una pasada de Láscar.
  **Sin veredicto** (§6).
- **M2, presencia**: donde publicamos un cúmulo lejano, ¿la imagen que MIROVA hizo de **otra pasada de
  esa misma noche** tiene un exceso ahí, más que en los sitios donde nuestro pipeline publica otras
  noches? Cientos de pasadas, **con veredicto** (§7).

## 4. Entradas, universo y definiciones

**Sensor: VIIRS 375 m en las tres puntas** (records con `banco_paridad.bucket == "VIIRS375"`, filas de
MIROVA con `sensor_bucket == VIIRS375`, TIF con `sensor == VIIRS375`). **Ventana**: 2026-05-09 hasta el
sha con que se corra.

- Índice y TIF de `mirova-tif-archive` en el commit `da4fe36e8920`, por la API, sin pull (17 GB).
- CONS y OCR de `Mirova-v1` por sha. **`Distancia_km` se toma de CONS**; si la pasada sólo tiene fila
  OCR sale de M1 y se cuenta aparte; M1 se repite como sensibilidad con el valor del OCR.
- **M1**: para las noches de S143, los records del brazo control congelados en
  `experiments/_s144_keep_peak_direccion/control_s143/` (**19 archivos versionados**: `MANIFIESTO.json`
  con sha256 más 9 volcanes en cada tramo); el resto, producción. **M2**: producción en el sha de
  `origin/main` del momento de correr.
- Cráter: `vent_lat`/`vent_lon` de `volcanoes.yaml` (ancla del Test 1, `pipeline/geo_utils.py:53-78`).

**TIF usable**: `size_bytes > 0` y `acquisition_utc` no vacío, a ±120 s de la pasada; imagen propia (su
md5 no aparece bajo una adquisición anterior del mismo volcán); mediana del raster menor que
0,2 W/m² sr µm; CRS legible con rasterio; menos del 10 % de celdas sin dato en el disco de 4 km alrededor
del cráter. La latencia no excluye: todo se repite con latencia ≤ 8 h como sensibilidad.

**ΔL0** de una celda: L menos la media de sus vecinas con dato, exigiendo al menos 5 de las 8. **z** =
ΔL0 dividido por 1,4826 × MAD de ΔL0 sobre las celdas **con ΔL0** del raster. **`Z(X)`** = máximo de z
sobre las celdas con ΔL0 a ≤ T de X, con **T = 0,75 km**. El mismo estadístico en todas partes.

**Umbrales**, calibrados con el mismo estadístico, en las pasadas **RUTINA** (fila CONS RUTINA con
VRP 0, sin alerta ni falso positivo esa noche y sensor, con TIF usable; la ronda 4 midió que exigir o no
record nuestro da el mismo conjunto) desde el 2026-05-09:
- **`zc_punto(vol)`** = percentil 95 de `Z(X)` con X sorteado en el anillo de **1,5 a 3,0 km** alrededor
  del cráter (H5: ningún P vive más allá de 3,00 km, que es el borde del disco del Test 1), **uniforme
  en área**. Procedimiento de sorteo, que fija el resultado (H8): un único `random.Random(144)`;
  volcanes en orden alfabético; dentro de cada volcán, pasadas por `datetime_utc` ascendente; por
  pasada se extraen exactamente dos números, primero `u` para el radio (`r = sqrt(1,5² + u·(3,0² −
  1,5²))`) y después el acimut en `[0, 2π)`.
- **`zc_disco(vol)`** = percentil 95 del máximo de z sobre el disco de 4 km alrededor del cráter, en las
  mismas pasadas (umbral del control G).
- **`zc_anillo(vol, d)`** = percentil 95 del máximo de z sobre el anillo |r − d| ≤ 0,6 km alrededor de
  `mirova_center`, por cada `Distancia_km` d que aparezca en M1.

Los tres se informan con su n y su intervalo por bootstrap. Queda declarado que con la regla literal
Chaitén da 3,63 [3,13, 4,66] y que **Isluga se calibra con 13 pasadas y su intervalo va de 2,50 a 7,69**
(H4): el umbral de ese volcán es poco confiable, y por eso la lectura por volcán de §7 lo informa
aparte.

**Candidatos**: **P** es el centroide del cúmulo primario cuando tiene un solo píxel (el record no marca
cuál píxel conservó `keep_peak`; puede ser un vecino recapturado por el segundo pase, a una celda). **F**
es el `final_hotspot` del mismo record; en `test1_roi` es el cráter. **Patrón**: el record publica según
el predicado del dashboard corrido con node (A97), su cúmulo primario tiene un solo píxel y
d(P, F) > 0,5 km; en M1 además d(P, F) ≥ 2T.

## 5. El instrumento de M2: pasada cruzada y sitios de referencia

**Imagen (pasada cruzada).** Para cada pasada medida `p` (volcán `v`, noche `n`), la imagen es el TIF de
otra pasada `q` de **la misma noche y el mismo volcán**, con |t_q − t_p| ≥ 15 min y TIF usable; se toma
la más cercana en el tiempo y, si hay empate, la anterior. Si no existe, la pasada sale de la muestra y
se cuenta aparte. Se informa la distribución de |t_q − t_p|. **La imagen no es del gránulo que eligió
P**, que es todo el punto.

**Sitios de referencia.** `R(p)` son **5 posiciones P que nuestro pipeline publicó en el mismo volcán en
otras noches**, con patrón, a más de 3 días de `n` y **a más de 2T (1,5 km) de P_p** (el 97,1 % de los P
tiene otro P a menos de 0,75 km en otra noche, así que sin esta separación el propio rasgo entraría al
denominador y volveríamos a la ceguera de la v4). Se eligen las 5 más cercanas en el tiempo; empate, la
anterior. Si quedan menos de 3, la pasada sale y se cuenta aparte. Todas se evalúan **en el mismo raster
`q`**.

- Observado: `e_p = 1` si `Z_q(P_p) ≥ zc_punto(v)`.
- Referencia: `r_p` = fracción de `R(p)` con `Z_q ≥ zc_punto(v)`.
- Diferencia: `d_p = e_p − r_p`.

Qué controla cada cosa: la misma imagen controla el estado de nube y de nieve de esa noche; los sitios
de referencia controlan la textura del flanco (son el mismo tipo de sitio); la pasada cruzada controla
la maldición del ganador.

**Controles de instrumento** (todos con `random.Random(2144)` declarado, y todos corridos en la misma
corrida):
- **C1, intercambio de roles**: se repite el procedimiento tomando como "observado" un sitio de
  referencia y como referencia los otros cuatro más el P de la pasada, en el mismo raster cruzado.
  Debe dar `D` dentro de ±0,05. Si no, el instrumento está sesgado y la medida es INCONCLUSA.
- **C2, maldición del ganador visible**: se corre el mismo procedimiento con el TIF de **la propia
  pasada** en vez del cruzado, sobre pasadas con patrón y publicadas **fuera de la muestra del
  veredicto** (`far_ref` y `sin_info` fuera de Lastarria, 194 pasadas). La diferencia entre esa corrida
  y la cruzada sobre las mismas pasadas es la medida directa del sesgo de selección, y se informa. La
  corrida **cruzada** sobre esas mismas pasadas debe quedar por debajo de +0,05; si no, la pasada
  cruzada no alcanzó a cortar el sesgo y la medida es INCONCLUSA.
- **G, georreferencia (compuerta)**: pasadas con alerta CONS con VRP ≥ 0,3 MW en Láscar y Villarrica,
  TIF usable; semilla = máximo de z en el disco de 4 km alrededor del cráter con `z ≥ zc_disco`. Pasa
  si n ≥ 8, la semilla cae a ≤ 0,75 km del cráter en al menos el 80 %, la mediana de esa distancia es
  ≤ 0,5 km y **el valor absoluto de la mediana** del desplazamiento es menor que 0,19 km en cada eje.
  Alcance declarado: valida casi sólo Láscar (42 de 43 pasadas). Si falla, las dos medidas terminan
  INCONCLUSAS.
- **H, alineación** (compuerta blanda): pasadas con alerta, TIF usable y record con
  `primary_cluster.n_pixels ≥ 2`, `final_hotspot_source == "ctx_cluster"` y centroide dentro del
  `inner_radius_km` (H7: `ctx_cluster` no es una clave del record, es el valor de ese campo; con esa
  definición hay 128 pasadas, 58 de Cordón Caulle, cuyo `inner_radius_km` es 20 km, así que se informa
  con y sin él). La semilla del disco debe caer a ≤ 0,75 km de nuestro centroide en al menos la mitad.
  Si no pasa, todo veredicto baja a SOSPECHA.

## 6. M1: dirección, donde la coincidencia de radio ocurre

**Universo**: pasadas con alerta CONS, TIF usable, record con patrón y d(P, F) ≥ 2T, con P y F dentro de
la región de búsqueda (unión del disco de 3,4 km alrededor del cráter y el disco de `Distancia_km` + 1 km
alrededor de `mirova_center`), con |r_P(mirova_center) − `Distancia_km`| ≤ 0,55 km (la cota del A/B S143)
y en volcanes donde `mirova_center` está a menos de 1 km del cráter. Con el pool de la ronda 3 eso da
**13 pasadas en 2 volcanes**: 12 de Lastarria y 1 de Láscar (H6).

**Semilla**: máximo de z sobre el anillo |r − `Distancia_km`| ≤ 0,6 km dentro de la región, con
`z ≥ zc_anillo`. Si no hay, la pasada queda **sin identidad**.

**Clases** (T = 0,75 km): `P` si d(semilla, P) ≤ T y d(semilla, F) > T; `F` si d(semilla, F) ≤ T y
d(semilla, P) > 2T; `otro` si d(semilla, P) > 2T y d(semilla, F) > T; `indefinido` en cualquier otro
caso, incluida la corona entre T y 2T alrededor de P, que se informa aparte.

**Declarado de antemano**: en **Lastarria** la clase `F` es geométricamente imposible (su
`mirova_center` está a 0,12 km del cráter y sus `Distancia_km` son 2,19, 2,40 y 2,70 km, así que el
anillo nunca toca el cráter); las salidas posibles ahí son `P`, `otro`, `indefinido` y `sin identidad`.
En la pasada de **Láscar** (`Distancia_km` 0,84 km) `F` sí es alcanzable.

**Contraste temporal de la semilla**: por cada pasada se informa cuántas veces la celda de la semilla es
también el máximo del mismo anillo en las pasadas RUTINA del volcán (la ronda 3 midió que la celda a
2,363 km lo es en 5 a 7 de 31). Sin ese contraste, "la semilla cae sobre P" no separa el objeto de esa
noche de la fuente fumarólica permanente.

**Las noches de S143** se informan una por una (Isluga 2026-06-16, Lastarria 2026-06-07, 2026-06-14 y
2026-07-25), con todos los records del control con patrón de esa noche como candidatos y cada par
(semilla, record) con su clase; no hay clase de noche. Isluga no tiene TIF en sus pasadas con alerta;
Lastarria 06-14 tampoco en la pasada del record que coincidió (05:00).

**M1 no tiene veredicto**: n chico, Lastarria contaminada y `F` inalcanzable ahí.

## 7. M2: el veredicto

**Universo**: pasadas VIIRS 375 nocturnas de producción con patrón, publicadas, con pasada cruzada
usable y con los 5 (o al menos 3) sitios de referencia. Se estratifica por **etiqueta**
(`banco_paridad.etiquetar`: `pos`, `neg_limpio`; `far_ref` y `sin_info` se informan aparte), por
**volcán** y por **tramo** (antes y después de #535, A104).

**El veredicto se toma sobre los negativos limpios fuera de Lastarria.** En las pasadas con alerta,
MIROVA publicó algo esa noche y la lectura se confunde con la de M1; se informan, no deciden.

**Estadístico**: `D_v` = media de `d_p` en el volcán `v`; `D` = estimación agrupada con **remuestreo por
noche de volcán** (A94), estratificado **por volcán**, 2.000 réplicas, `random.Random(144)`, orden de
estratos alfabético.

**Veredicto**, con al menos 30 noches de volcán fuera de Lastarria y al menos 3 volcanes con 20 noches:
- **"el cúmulo lejano cae sobre un exceso del campo de MIROVA"** si el intervalo del 95 % de `D` queda
  entero por encima de **+0,05** y `D_v > 0` en al menos dos tercios de los volcanes con al menos 20
  noches;
- **"no se distingue de los sitios donde publicamos otras noches"** si el intervalo del 95 % de `D`
  queda entero dentro de **±0,05**;
- en cualquier otro caso, INCONCLUSO. Si hay menos de 3 volcanes con 20 noches, la segunda condición del
  positivo **no es evaluable** y el veredicto es INCONCLUSO (H3: dos tercios de un conjunto vacío
  admite dos lecturas, y así queda cerrado).

**Declarado de antemano sobre los tramos** (H3): con el n de hoy, el tramo posterior a #535 tiene
intervalos de ancho cercano a 0,12, así que **no puede dar la salida de equivalencia**. El veredicto se
toma sobre la muestra completa y los tramos se informan; una diferencia entre tramos se lee como
descriptiva, no como contradicción.

**Qué significa cada salida** (H1 y H2, la lectura corregida): la imagen no fue elegida por nuestro
detector, así que un exceso ahí no es el eco de nuestra propia selección; y como es la misma noche, un
foco permanente o una anomalía que dure la noche siguen presentes. Entonces "cae sobre un exceso"
significa que el sitio que publicamos corresponde a algo que está en el campo de radiancia de MIROVA esa
noche, sea permanente (categoría b de A54) o transitorio de varias decenas de minutos (por ejemplo, un
borde de nube, que es artefacto). **Distinguir permanente de transitorio no lo hace M2**: lo informa el
contraste temporal, que se reporta al lado (fracción de las 5 noches de referencia del mismo sitio con
exceso), sin entrar al veredicto.

## 8. Qué se hace con el resultado

| M2 (negativos limpios, fuera de Lastarria) | contraste temporal del mismo sitio | Lectura | Siguiente paso propuesto |
|---|---|---|---|
| no se distingue | cualquiera | lo que `keep_peak` publica no tiene correlato en el campo de MIROVA | pre-registrar una cota con dirección y re-evaluar el A/B S143 con ella, sin re-correrlo |
| cae sobre un exceso | alto (el sitio también destaca otras noches) | rasgo permanente que MIROVA ve y no publica: categoría b | no apagar `keep_peak` sin medir qué se pierde; el frente pasa a ser de etiquetado |
| cae sobre un exceso | bajo (sólo esa noche) | algo de esa noche, que puede ser actividad o nube | no decide; pide un frente nuevo que separe nube de calor |
| INCONCLUSO, o G o H fallan, o C1 o C2 se salen de ±0,05 | | | informar y no mover nada |

M1 acompaña y no decide.

## 9. Límites conocidos

- La pasada cruzada corta el sesgo de selección, **no** los artefactos que duran lo que separa las dos
  pasadas (decenas de minutos): un borde de nube puede estar en las dos. Por eso la tabla de §8 no
  concluye "es calor volcánico" sino "hay un exceso en el campo de MIROVA".
- Los sitios de referencia son lugares donde nuestro pipeline publica, o sea están sesgados hacia el
  borde de cota baja del disco. Eso es deliberado (controla la textura), pero significa que la
  comparación es "contra otros sitios como este", no "contra el volcán entero".
- `zc_punto` de Isluga se calibra con 13 pasadas y su intervalo va de 2,50 a 7,69: ese volcán se
  informa aparte.
- Los TIF geográficos son un remuestreo de MIROVA con método no documentado; G lo valida en Láscar.
- La hora de adquisición del índice puede no ser la de la imagen (A106); el md5 propio y la mediana
  nocturna lo acotan sin probarlo imagen por imagen.
- M1 son 13 pasadas en 2 volcanes y no puede generalizar.
