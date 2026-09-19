# Pre-registro: ¿el cúmulo lejano de un píxel es el objeto que MIROVA vio? (S144)

> **Estado: v4 del 2026-09-19, escrita ANTES de medir.** Corrige los 10 hallazgos del tercer verificador
> con contexto limpio (`..._VERIFICADOR_V3.md`), que a su vez corrigió los 14 del segundo
> (`..._VERIFICADOR_V2.md`) y los 13 del primero (`..._VERIFICADOR.md`). La v1 está en `f6a1cb962` y la
> v3 en `9496cdaea`; **la v2 nunca se commiteó** (la sobrescribí antes de pasarla por git, así que las
> citas de línea del segundo informe apuntan a un archivo que no existe; su contenido se reconstruye
> leyendo ese informe). Falta: una cuarta pasada del verificador, y recién después el script
> (`experiments/_s144_keep_peak_direccion/`, con tests) y la corrida.
>
> Origen: decisión 1 del traspaso `tasks/BLOQUE_ARRANQUE_S144.md`. Muestra:
> `experiments/_s144_conteo_tif/RESULTADO.md`. A/B que motiva la medida:
> `experiments/_s143_evaluador/RESULTADO_AB_S143.md` y `VERIFICADOR_VEREDICTO.md`. Instrumento heredado:
> `experiments/_s142_ndc/RESULTADOS.md` §0.

## 0. Qué cambió en la v4

El tercer verificador midió el nulo del control que usaba la v3 y lo refutó (H1). En 533 pasadas RUTINA
ajenas a la muestra, poner un punto donde suele caer nuestro cúmulo le gana a su reflejo por **+0,1014,
con intervalo [+0,018, +0,197]**, sin que haya nada que detectar, y el signo es positivo en 8 de 10
volcanes. El mecanismo es físico y vale la pena nombrarlo: el exceso local ΔL0 **sí** cancela el
gradiente de altitud celda por celda (mediana pareada -0,0023 con el intervalo conteniendo el 0), pero
el estadístico de la v3 era un **máximo sobre 12 celdas**, y el flanco donde `keep_peak` conserva su
píxel tiene más textura (roca, quebradas, borde de nieve). Un máximo sobre terreno rugoso es más alto
aunque no haya más calor. El control medía rugosidad direccional.

Además (H2), la regla de veredicto pedía que un intervalo **contuviera el 0**, lo que castiga la
precisión: al n real un campo sin nada que detectar daba INCONCLUSO en 43 de 60 repeticiones, y la única
salida que habría permitido re-evaluar el A/B de S143 era justamente la que se rompía.

La v4 hace tres cambios de fondo:
1. **El control deja de ser el reflejo y pasa a ser el mismo punto en otra noche** en que MIROVA miró y
   no publicó nada (§5). Mismo terreno, misma dirección, misma textura: el sesgo de H1 se cancela por
   construcción y lo que queda es "¿hay calor esta noche?".
2. **El veredicto se escribe como equivalencia** sobre la diferencia de tasas, no como "el intervalo
   contiene el 0" (§7), así que las tres salidas son alcanzables.
3. **La agregación es por volcán y el remuestreo por noche** (§7), no una fracción agrupada sobre
   pasadas: tres volcanes ponen el 58 % de la muestra y 635 pasadas son 383 noches.

## 1. Lo que ya se vio (contaminación declarada)

- **Lastarria no es ciega**: la ronda 1 midió las semillas de todas sus alertas y sus RUTINA (celdas
  fijas a 1,065, 1,305, 1,396 y 2,363 km del cráter; la de 2,363 es semilla en 14 alertas y 11 RUTINA).
- **Techos y nulos conocidos**: la ronda 2 midió la alcanzabilidad de las clases de M1; la ronda 3 midió
  el nulo del control reflejado, `zc_punto` por volcán, el embudo completo de M2 y el control G. Ninguna
  calculó `Z` sobre los P de la muestra del veredicto ni clasificó pasadas de M1.
- **La distribución de radio y acimut de nuestros P es conocida** (la usó la ronda 3 para construir el
  nulo). El 96 % vive en la banda de 1,5 a 3,5 km, con mediana 2,79 km.

## 2. El fenómeno

En un cono nevado de noche la radiancia MIR sigue la altitud: dentro del disco de 3 km del Test 1 el
píxel más tibio suele ser el borde de cota baja, no el cráter (A69). `keep_peak` conserva ese píxel
aunque no sea contextual, y el record queda con un cúmulo primario de un solo píxel lejos del cráter
(D19). Apagarlo es lo único que baja la sobre-publicación en el A/B de S143, pero la regla de cero
pérdidas le cobró 5 noches donde MIROVA alertó y un cúmulo nuestro caía dentro de su cota de distancia.

Dos precisiones sobre esas noches (ronda 1, reproducidas por las rondas 2 y 3):
- **La coincidencia fue entre pasadas distintas**: MIROVA alertó en una pasada y el cúmulo que coincidió
  es de otra pasada de la misma noche, de 18 a 78 minutos antes o después. En la pasada con alerta
  nuestro cúmulo estaba sobre el `final_hotspot`.
- **Láscar 2026-06-13 no es un cúmulo lejano** (cúmulo a 0,32 km del cráter, a 0,49 km del
  `final_hotspot`): sale de M1 y se informa aparte.

**Dónde ocurre la coincidencia de radio.** Medido por la ronda 3 sobre records de producción con alerta
CONS, patrón y TIF usable: 15 pasadas en Lastarria con 12 compatibles y 24 fuera con 4 compatibles. Pero
3 de esas 4 son de Cordón Caulle, donde `mirova_center` está a 7,57 km del cráter y MIROVA publica
distancias de 7,65 a 8,10 km: ahí **cualquier** punto cercano al cráter cumple la compatibilidad por
aritmética del centro de grilla, no porque nuestro cúmulo tenga que ver. Lo mismo vale para Tupungatito
(4,86 km). **La compatibilidad de radio sólo informa donde `mirova_center` casi coincide con el cráter**,
y entonces la coincidencia de S143 es, hoy, un fenómeno de Lastarria.

## 3. Las dos medidas

- **M1, dirección**: donde MIROVA publicó un objeto al mismo radio que nuestro cúmulo, ¿coincide el
  acimut? Es la pregunta de A107 y sólo se puede hacer en Lastarria. **Sin veredicto** (§6).
- **M2, presencia**: donde publicamos un cúmulo lejano, ¿el campo de MIROVA tiene calor ahí esa noche,
  más que en el mismo punto otras noches en que MIROVA miró y no publicó? Cientos de pasadas, **con
  veredicto** (§7). No dice "es el objeto que MIROVA publicó"; dice si lo que publicamos tiene correlato
  en su campo de radiancia.

## 4. Entradas, universo y definiciones

**Sensor: VIIRS 375 m en las tres puntas**: records con `banco_paridad.bucket == "VIIRS375"`, filas de
MIROVA con `sensor_bucket == VIIRS375`, TIF con `sensor == VIIRS375`. **Ventana**: 2026-05-09 (primera
adquisición del índice) hasta el sha con que se corra.

- Índice y TIF de `mirova-tif-archive` en el commit `da4fe36e8920`, por la API, sin pull (17 GB).
- CONS y OCR de `Mirova-v1` por sha. **`Distancia_km` se toma de CONS**: el residuo contra el radio de la
  semilla es 0,08 km con CONS y 4,24 km con OCR en Cordón Caulle. Si la pasada sólo tiene fila OCR, sale
  de M1 y se cuenta aparte; M1 se repite como sensibilidad con el valor del OCR.
- **M1**: records del brazo control del A/B S143 para las noches de S143, congelados en
  `experiments/_s144_keep_peak_direccion/control_s143/` (18 archivos, `MANIFIESTO.json` con sha256); el
  resto, producción. **M2**: producción, en el sha de `origin/main` del momento de correr.
- Cráter: `vent_lat`/`vent_lon` de `volcanoes.yaml` (ancla del Test 1, `pipeline/geo_utils.py:53-77`).

**TIF usable**: `size_bytes > 0` y `acquisition_utc` no vacío, a ±120 s de la pasada; imagen propia (su
md5 no aparece bajo una adquisición anterior del mismo volcán); mediana del raster menor que
0,2 W/m² sr µm; CRS legible con rasterio; menos del 10 % de celdas sin dato en el disco de 4 km alrededor
del cráter. La latencia (primera `captured_at_utc` del md5 menos `acquisition_utc`) **no excluye**: todo
se repite con latencia ≤ 8 h como sensibilidad (el 78 % de las pasadas de M2 la cumple).

**ΔL0** de una celda: L menos la media de sus vecinas con dato, exigiendo al menos 5 de las 8; si no, la
celda queda sin ΔL0 y no participa de ningún máximo. **z** = ΔL0 dividido por 1,4826 × MAD de ΔL0 sobre
**las celdas con ΔL0** del raster (H10).

**Exceso en un punto X**: `Z(X)` = máximo de z sobre las celdas con ΔL0 a ≤ T de X, con **T = 0,75 km**
(dos celdas de radio, unas 11 o 12 celdas de disco). El mismo estadístico en todas partes.

**Umbrales**, calibrados con el mismo estadístico y sobre la misma región donde se aplican, en las
pasadas **RUTINA de la fila de MIROVA** (fila CONS RUTINA con VRP 0, sin alerta ni falso positivo esa
noche y sensor, con TIF usable del volcán; no se exige record nuestro, H7), desde el 2026-05-09:
- `zc_punto(vol)` = percentil 95 de `Z(X)` con X sorteado **uniforme en área** en el anillo de 1,5 a
  3,5 km alrededor del cráter, un sorteo por pasada, un único `random.Random(144)` para todos los
  volcanes, orden de extracción por `(volcan, datetime_utc)` ascendente. Se informa con su intervalo por
  bootstrap (es un percentil 95 sobre pocas decenas de pasadas: Chaitén 4,64 con IC [3,17, 6,26]).
- `zc_disco(vol)` = percentil 95 del máximo de z sobre el disco de 4 km alrededor del cráter, en las
  mismas pasadas. Es el umbral del control G (§5).
- `zc_anillo(vol, d)` = percentil 95 del máximo de z sobre el anillo |r − d| ≤ 0,6 km alrededor de
  `mirova_center`, en las mismas pasadas, por cada `Distancia_km` d que aparezca en M1.

**Candidatos**: **P** es el centroide del cúmulo primario cuando tiene un solo píxel (el record no marca
cuál píxel conservó `keep_peak`; puede ser un vecino recapturado por el segundo pase, a una celda). **F**
es el `final_hotspot` del mismo record; en `test1_roi` es el cráter. **P'** (el reflejo de P a través del
cráter) **ya no es control del veredicto**: se informa sólo como descriptivo, junto al sesgo medido en
H1, porque compara terrenos distintos.

**Patrón**: el record publica según el predicado del dashboard corrido con node (A97), su cúmulo primario
tiene un solo píxel y d(P, F) > 0,5 km. En M1 además se exige d(P, F) ≥ 2T (si no, los discos se
traslapan y la pasada queda `cerca`).

## 5. Control temporal (el corazón de M2) y controles de instrumento

**Control temporal.** Para cada pasada medida `p` del volcán `v`, el conjunto de referencia `R(p)` son
las **5 pasadas RUTINA** de `v` con TIF usable más cercanas en el tiempo a `p` y a más de 3 días de
distancia (si hay menos de 3 disponibles, la pasada sale de la muestra y se cuenta aparte). En cada
referencia se evalúa `Z` **en las mismas coordenadas de P**. Mismo terreno, misma dirección, misma
textura, otra noche.

- Indicador observado: `e_p = 1` si `Z_p(P) ≥ zc_punto(v)`.
- Tasa de referencia del mismo punto: `r_p` = fracción de las referencias con `Z_k(P) ≥ zc_punto(v)`.
- Diferencia por pasada: `d_p = e_p − r_p`.

**G, georreferencia (compuerta de las dos medidas).** Pasadas con alerta CONS con VRP ≥ 0,3 MW en Láscar
y Villarrica, con TIF usable. La semilla es el máximo de z en el disco de 4 km alrededor del cráter y
debe cumplir `z ≥ zc_disco` (calibrado sobre ese mismo disco, H5). Pasa si: n ≥ 8; la semilla cae a
≤ 0,75 km del cráter en al menos el 80 %; la mediana de esa distancia es ≤ 0,5 km; y **el valor absoluto
de la mediana** del desplazamiento es menor que 0,19 km (media celda) en cada eje. Se informa también el
promedio. **Si G falla, las dos medidas terminan INCONCLUSAS.** Alcance declarado: G valida casi sólo
Láscar (42 de 43 pasadas), un cráter del desierto con señal fuerte; no valida nevados, señales débiles ni
bordes de disco.

**H, alineación** (no compuerta). Pasadas con alerta, TIF usable y record `ctx_cluster` de 2 o más
píxeles con centroide dentro del `inner_radius_km` (hay 110, de ellas 50 de Cordón Caulle, cuyo
`inner_radius_km` es 20 km, así que se informa con y sin él): la semilla del disco debe caer a ≤ 0,75 km
de nuestro centroide en al menos la mitad. Si no pasa, todo veredicto baja a SOSPECHA.

**Control de instrumento del nulo.** En la misma corrida se repite todo el procedimiento de M2 sobre un
conjunto **disjunto** de pasadas RUTINA sin patrón, poniendo un punto sorteado de la distribución
empírica de nuestros P: la diferencia de tasas debe quedar dentro de ±0,05. Si no, el instrumento está
sesgado y la medida es INCONCLUSA. (Con el control reflejado de la v3 este nulo daba +0,10; con el
control temporal debería dar 0, y eso hay que comprobarlo, no suponerlo.)

## 6. M1: dirección, donde la coincidencia de radio ocurre

**Universo**: pasadas con alerta CONS, TIF usable, record con patrón y no `cerca`, con P y F dentro de la
región de búsqueda (unión del disco de 3,4 km alrededor del cráter y el disco de `Distancia_km` + 1 km
alrededor de `mirova_center`), con |r_P(mirova_center) − `Distancia_km`| ≤ 0,55 km (la cota del A/B
S143) **y en volcanes donde `mirova_center` está a menos de 1 km del cráter**. Esta última condición es
nueva: donde el centro de grilla está lejos (Cordón Caulle 7,57 km, Tupungatito 4,86 km) la
compatibilidad de radio se cumple por aritmética y no informa (§2).

**Semilla**: máximo de z sobre el anillo |r − `Distancia_km`| ≤ 0,6 km dentro de la región, con
`z ≥ zc_anillo`. Si no hay, la pasada queda **sin identidad**.

**Clases** (T = 0,75 km): `P` si d(semilla, P) ≤ T y d(semilla, F) > T; `F` si d(semilla, F) ≤ T y
d(semilla, P) > 2T; `otro` si d(semilla, P) > 2T y d(semilla, F) > T; `indefinido` en cualquier otro
caso, incluida la corona entre T y 2T alrededor de P, que se informa aparte.

**Declarado de antemano** (H6): en Lastarria la clase `F` es **geométricamente imposible**, porque su
`mirova_center` está a 0,12 km del cráter y sus `Distancia_km` son 2,19, 2,40 y 2,70 km, así que el
anillo nunca toca el cráter. Las salidas posibles ahí son `P`, `otro`, `indefinido` y `sin identidad`.

**Contraste temporal de la semilla** (H6): para cada pasada de M1 se informa cuántas veces la celda de la
semilla es también el máximo del mismo anillo en las pasadas RUTINA del volcán. La ronda 3 midió que la
celda a 2,363 km lo es en 5 a 7 de 31. Sin ese contraste, "la semilla cae sobre P" no separa "es el
objeto que MIROVA publicó esa noche" de "es la fuente fumarólica que está siempre".

**Las noches de S143** se informan una por una (Isluga 2026-06-16, Lastarria 2026-06-07, 2026-06-14 y
2026-07-25; Láscar sale, §2), con todos los records del control con patrón de esa noche como candidatos,
cada par (semilla, record) con su clase. No hay clase de noche. Isluga no tiene TIF en sus pasadas con
alerta; Lastarria 06-14 tampoco lo tiene en la pasada del record que coincidió (05:00).

**M1 no tiene veredicto**: n chico, Lastarria contaminada y `F` inalcanzable.

## 7. M2: presencia, donde publicamos un cúmulo lejano

**Universo**: pasadas VIIRS 375 nocturnas de producción con patrón, publicadas, con TIF usable de la
misma pasada, con ΔL0 en P y con al menos 3 referencias temporales. Se estratifica por **etiqueta** de
`banco_paridad.etiquetar` (`pos`, `neg_limpio`; `far_ref` y `sin_info` se informan aparte), por **volcán**
y por **tramo** (antes y después de #535, A104).

**El veredicto se toma sobre los negativos limpios fuera de Lastarria**, donde MIROVA miró y no publicó
nada: ahí "hay calor donde publicamos" significa que el rasgo existe en su campo aunque no lo alerte
(categoría b de A54), y "no hay" significa que lo que publicamos no tiene correlato. En las pasadas con
alerta MIROVA y nosotros leemos el mismo granule, así que el ruido compartido infla cualquier
coincidencia: esas se informan, no deciden.

**Estadístico**: `D_v` = media de `d_p` en el volcán `v` (o sea, la tasa observada menos la tasa del
mismo punto en otras noches). `D` = estimación agrupada, con **remuestreo por noche de volcán**
(635 pasadas son 383 noches; A94), estratificado **por volcán**, 2.000 réplicas, un único
`random.Random(144)`.

**Veredicto** (equivalencia, H2), con al menos 30 noches de volcán fuera de Lastarria:
- **"el cúmulo lejano cae sobre calor del campo de MIROVA"** si el intervalo del 95 % de `D` queda
  **entero por encima de +0,05** y `D_v > 0` en al menos dos tercios de los volcanes con al menos 20
  noches;
- **"no se distingue del mismo punto en otras noches"** si el intervalo del 95 % de `D` queda **entero
  dentro de ±0,05**;
- en cualquier otro caso, INCONCLUSO.

Los tramos se informan por separado. **"Lecturas opuestas"** (que fuerzan INCONCLUSO) significa que un
tramo da "cae sobre calor" y el otro "no se distingue"; cualquier otra combinación no es oposición.
Lastarria, Isluga y Tupungatito se informan aparte por fuente persistente, y Lastarria además por
contaminación. La mediana pareada `Z_p(P) − mediana_k Z_k(P)` y la comparación contra `P'` se informan
como descriptivas, con el sesgo de H1 escrito al lado.

**Embudo declarado** (H9, medido por la ronda 3 en la ventana 2026-05-09 a 2026-09-19): 6.241 records
nocturnos VIIRS 375, 2.999 con patrón, 2.627 publicados, 1.134 con etiqueta `neg_limpio` (1.113 fuera de
Lastarria), 635 con TIF a ±120 s y **554 con TIF usable**. El filtro que más corta no es ninguno de los
cinco criterios de usabilidad sino **la ausencia de imagen en el archivo** (478 pasadas). Eso no
selecciona por calor: hay imagen en el 48 % de las pasadas con alerta y en el 59 % de los negativos
limpios. Los demás descartes son 58 por md5 repetido, 19 por mediana alta y 4 por celdas sin dato.

## 8. Qué se hace con el resultado

| M2 (negativos limpios, fuera de Lastarria) | M1 (Lastarria, descriptiva) | Lectura | Siguiente paso propuesto |
|---|---|---|---|
| no se distingue del mismo punto en otras noches | semillas lejos de P, o sobre P pero también en RUTINA | lo que `keep_peak` publica no tiene correlato en el campo de MIROVA, y la coincidencia de radio no era el mismo objeto | pre-registrar una cota con dirección y re-evaluar el A/B S143 con ella, sin re-correrlo |
| cae sobre calor | semillas sobre P y no en RUTINA | el cúmulo lejano es un rasgo térmico real que MIROVA también ve y no publica (categoría b) | no apagar `keep_peak` sin medir qué se pierde; el frente pasa a ser de etiquetado, no de detección |
| INCONCLUSO, o G o H fallan, o el nulo del instrumento se sale de ±0,05 | | | informar y no mover nada |

**Veredictos alcanzables**: M2 tiene 554 pasadas (431 antes de #535 y 123 después) y las tres salidas son
posibles con el criterio de equivalencia. M1 tiene del orden de 12 pasadas, todas de Lastarria, con `F`
inalcanzable: **no puede generalizar y no tiene veredicto**. Ninguna medida puede concluir "es el objeto
publicado por MIROVA" fuera de Lastarria: esa pregunta necesita pasadas donde la coincidencia de radio
ocurra en un volcán con el centro de grilla sobre el cráter, y hoy no las hay.

## 9. Límites conocidos

- El control temporal supone que el terreno no cambia entre noches. La nieve sí cambia: una nevada entre
  la pasada y sus referencias mueve la textura. Por eso las referencias son las 5 más cercanas en el
  tiempo, y se informa la separación temporal mediana.
- El pool nulo de la ronda 3 son pasadas sin patrón o sin publicar, que podrían ser noches más nubladas.
  El control de instrumento de §5 hereda ese límite.
- Los TIF geográficos son un remuestreo de MIROVA con método no documentado; G lo valida en Láscar.
- La semilla de M1 es el mayor exceso local del anillo, no el cúmulo que MIROVA sumó (S142 no logró
  reconstruirlo).
- La hora de adquisición del índice puede no ser la de la imagen (A106); el md5 propio y la mediana
  nocturna lo acotan sin probarlo imagen por imagen.
- `zc_punto` es un percentil 95 sobre pocas decenas de pasadas y su intervalo es ancho. Mitiga que el
  mismo umbral se aplica al punto observado y a sus referencias, así que la **diferencia** es robusta: la
  ronda 3 la recalculó con percentiles 85, 90, 95 y 99 y el nulo se movió entre -0,017 y +0,009.
