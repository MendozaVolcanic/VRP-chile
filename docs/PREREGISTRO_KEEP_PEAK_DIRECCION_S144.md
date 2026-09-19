# Pre-registro: ¿el cúmulo lejano de un píxel es el objeto que MIROVA vio? (S144)

> **Estado: v3 del 2026-09-19, escrita ANTES de medir.** Corrige los 14 hallazgos nuevos del segundo
> verificador con contexto limpio (`..._VERIFICADOR_V2.md`) sobre la v2, y los 13 de la primera ronda
> (`..._VERIFICADOR.md`). La v1 queda en el historial de git (`f6a1cb962`). **La v2 no quedó commiteada**:
> la escribí, la mandé a verificar y la sobrescribí con esta v3 sin pasarla por git, así que las citas
> `archivo:línea` del informe del segundo verificador apuntan a un archivo que ya no existe. El contenido
> de la v2 se reconstruye leyendo ese informe, que cita el texto de cada regla que revisa. Es un error de
> proceso mío, no del verificador. Falta: una tercera pasada del verificador, y recién después el script
> (`experiments/_s144_keep_peak_direccion/`, con tests) y la corrida.
>
> Origen: decisión 1 del traspaso `tasks/BLOQUE_ARRANQUE_S144.md`. Muestra:
> `experiments/_s144_conteo_tif/RESULTADO.md`. A/B que motiva la medida:
> `experiments/_s143_evaluador/RESULTADO_AB_S143.md` y `VERIFICADOR_VEREDICTO.md`. Instrumento heredado:
> `experiments/_s142_ndc/RESULTADOS.md` §0.

## 0. Qué cambió en la v3, y por qué

La v2 ataba la semilla al anillo del radio publicado por MIROVA. El segundo verificador mostró que eso
devuelve la medida a la cota escalar de S143: fuera de Lastarria la clase `P` era geométricamente
imposible en 18 de 19 pasadas, así que "es el objeto" no se podía alcanzar y "no es el objeto" salía por
construcción, sin que el TIF aportara nada que el CSV no dijera (N1). Y midió el motivo de fondo (N2):

| | pasadas elegibles | el radio de `P` coincide con `Distancia_km` (cota 0,55 de S143) |
|---|---|---|
| fuera de Lastarria | 19 | **1** (y ahí el cúmulo está a 0,15 km del cráter, o sea no es el caso de la pregunta) |
| Lastarria | 15 | **12** |

**La coincidencia de radio que sostuvo las 5 noches perdidas es, hoy, un fenómeno de Lastarria.** Eso
parte la medida en dos preguntas distintas, que la v3 separa en vez de mezclar:

- **M1, dirección**: en las pasadas donde MIROVA publicó un objeto al mismo radio que nuestro cúmulo,
  ¿el acimut coincide? Es la pregunta de A107, y sólo se puede hacer donde la coincidencia ocurre:
  Lastarria. Va **sin veredicto**, por contaminación (§1) y por n.
- **M2, presencia**: donde publicamos un cúmulo lejano de un píxel, ¿el campo de MIROVA tiene calor ahí,
  más que en un punto cualquiera a la misma distancia del cráter? No usa el radio publicado, tiene
  cientos de pasadas y **sí tiene veredicto**. No dice "es el objeto que MIROVA publicó"; dice si lo que
  publicamos corresponde a algo que también está en el campo de radiancia de MIROVA.

## 1. Lo que ya se vio antes de esta v3 (contaminación declarada)

- **Lastarria no es ciega.** La primera ronda midió las semillas de todas sus alertas y de sus pasadas
  RUTINA: se agrupan en celdas fijas (1,065, 1,305, 1,396 y 2,363 km del cráter), el `Distancia_km` de
  MIROVA suele seguirlas, y la celda de 2,363 km es semilla en 14 alertas y 11 RUTINA. En dos noches de
  M1 la semilla está a 1,065 km del cráter. Nadie clasificó `P`, `F` u `otro`.
- **Techos conocidos**: la segunda ronda midió que la clase `P` es alcanzable en 1 de 19 pasadas fuera
  de Lastarria y en 12 de 15 en Lastarria, y la tasa de identidad real (12 de 19 y 8 de 15) contra la
  del placebo. No calculó ninguna clase ni ningún z de M2.
- **Control G** ya corrido dos veces (§5). Los umbrales de la v3 se fijan conociendo esos resultados.

## 2. El fenómeno

En un cono nevado de noche la radiancia MIR sigue la altitud: dentro del disco de 3 km del Test 1 el
píxel más tibio suele ser el borde de cota baja, no el cráter (A69). `keep_peak` conserva ese píxel
aunque no sea contextual, y el record queda con un cúmulo primario de un solo píxel lejos del cráter
(D19). Apagarlo es lo único que baja la sobre-publicación en el A/B de S143, pero la regla de cero
pérdidas le cobró 5 noches donde MIROVA alertó y un cúmulo nuestro caía dentro de su cota de distancia.

Dos precisiones sobre esas noches (ronda 1, hallazgo 6, reproducido por la ronda 2):
- **La coincidencia fue entre pasadas distintas**: MIROVA alertó en una pasada, y el cúmulo que coincidió
  es de otra pasada de la misma noche, de 18 a 78 minutos antes o después. En la pasada con alerta,
  nuestro cúmulo estaba sobre el `final_hotspot` en las 5 noches.
- **Láscar 2026-06-13 no es un cúmulo lejano** (cúmulo a 0,32 km del cráter, a 0,49 km del
  `final_hotspot`): sale de M1 y se informa aparte.

El TIF que MIROVA publica por pasada es su campo de radiancia MIR. Con él se ubica el calor en dos
dimensiones. El TIF trae el gradiente topográfico, pero el exceso local ΔL0 lo cancela en promedio
(medido en la ronda 1: ΔL0 medio por anillo del orden de 1e-5 más allá de 1,5 km, algo negativo en la
cumbre, y semillas RUTINA repartidas por área).

## 3. Entradas y universo

- **Sensor: VIIRS 375 m en las tres puntas** (N9): records con `banco_paridad.bucket == "VIIRS375"`,
  filas de MIROVA con `sensor_bucket == VIIRS375`, TIF con `sensor == VIIRS375` del índice.
- **Ventana**: 2026-05-09 (primera adquisición del índice) hasta el sha con que se corra.
- Índice y TIF de `mirova-tif-archive` en el commit `da4fe36e8920`, por la API, sin pull (17 GB).
- CONS y OCR de `Mirova-v1` por sha. **`Distancia_km` se toma de CONS** (N3): en las alertas donde la
  semilla cae al cráter, el residuo contra el radio de la semilla es 0,08 km con CONS y 4,24 km con OCR
  en Cordón Caulle. Si la pasada sólo tiene fila OCR, queda fuera de M1 y se cuenta aparte. Todo M1 se
  repite como sensibilidad con el valor del OCR.
- **M1**: records del brazo control del A/B S143, congelados en
  `experiments/_s144_keep_peak_direccion/control_s143/` (18 archivos, `MANIFIESTO.json` con sha256).
- **M2**: records de producción en el sha de `origin/main` del momento de correr.
- Cráter: `vent_lat`/`vent_lon` de `volcanoes.yaml` (ancla del Test 1, `pipeline/geo_utils.py:53-77`).
  Origen de `Distancia_km`: `mirova_center` del mismo archivo.

## 4. Definiciones

**TIF usable** (N10): `size_bytes > 0`, `acquisition_utc` no vacío, a ±120 s de la pasada; imagen propia
(su md5 no aparece bajo una adquisición anterior del mismo volcán); mediana del raster menor que
0,2 W/m² sr µm (S142 §0); CRS legible con rasterio; y **menos del 10 % de celdas sin dato en el disco de
4 km alrededor del cráter**. La latencia (primera `captured_at_utc` del md5 menos `acquisition_utc`) no
excluye: se informa como sensibilidad, repitiendo todo con latencia ≤ 8 h.

**ΔL0** de una celda: L menos la media de las vecinas con dato, y exige al menos 5 de las 8. Si no, la
celda queda sin ΔL0 y no participa de ningún máximo. **z** = ΔL0 dividido por 1,4826 × MAD de ΔL0 sobre
las celdas con dato del raster.

**Exceso en un punto X**: `Z(X)` = máximo de z sobre las celdas con ΔL0 que están a ≤ T de X, con
**T = 0,75 km** (unas dos celdas de 0,377 km). El mismo estadístico se usa en todas partes (N7): un
máximo sobre un disco de radio T, nunca una celda suelta contra un umbral de máximos.

**Umbral de exceso `zc`, por volcán y por región**: se calibra con el mismo estadístico y sobre la misma
región donde se aplica (N6). En las pasadas RUTINA (fila CONS RUTINA con VRP 0, sin alerta ni falso
positivo esa noche y sensor) con TIF usable del mismo volcán:
- `zc_punto(vol)` = percentil 95 de `Z(X)` con X sorteado uniformemente en el anillo de 1,5 a 3,5 km
  alrededor del cráter (la banda donde vive el cúmulo lejano), un sorteo por pasada,
  `random.Random(144)`, orden de extracción por `(volcan, datetime_utc)` ascendente.
- `zc_anillo(vol, d)` = percentil 95 del máximo de z sobre el anillo |r − d| ≤ 0,6 km alrededor de
  `mirova_center`, evaluado en las mismas pasadas RUTINA, con d el `Distancia_km` de la pasada de M1 que
  se esté clasificando (se calcula por cada d distinto que aparezca).

Ambos quedan en la salida, con el n de pasadas y el número de celdas de cada región.

**Candidatos**: **P** es el centroide del cúmulo primario cuando tiene un solo píxel (el record no marca
cuál píxel conservó `keep_peak`: puede ser un vecino recapturado por el segundo pase, a una celda).
**F** es el `final_hotspot` del mismo record; en `test1_roi` es el cráter. **P'** es el reflejo de P a
través del cráter: misma distancia, dirección opuesta.

**Patrón**: el record publica según el predicado del dashboard corrido con node (A97, N13), su cúmulo
primario tiene un solo píxel y d(P, F) > 0,5 km. Si d(P, F) < 2T la pasada queda **cerca** y no entra a
M1 (los discos se traslapan); en M2 sí entra, porque ahí P se compara con P', no con F.

## 5. Controles

**G, georreferencia (compuerta de las dos medidas).** Pasadas con alerta de MIROVA (CONS) con VRP ≥ 0,3
MW en Láscar y Villarrica, TIF usable. La semilla es el máximo de z en el disco de 4 km alrededor del
**cráter** y debe cumplir z ≥ `zc_punto`. Pasa si: n ≥ 8; la semilla cae a ≤ 0,75 km del cráter en al
menos el 80 %; la mediana de esa distancia es ≤ 0,5 km; y **la mediana** del desplazamiento en norte-sur
y en este-oeste es menor que 0,19 km (media celda) en cada eje. Se informa también el promedio, que en
las dos corridas previas estuvo entre 0,065 y 0,166 km según la región y lo movía una sola pasada de
z ≈ 4 (N8): por eso la compuerta va sobre la mediana (A70) y con z mínimo. **Si G falla, las dos medidas
terminan INCONCLUSAS.** Alcance declarado: G valida casi sólo Láscar (42 de 43 pasadas), un cráter del
desierto con señal fuerte. No valida nevados, señales débiles ni bordes de disco.

**H, alineación con nuestra grilla** (no compuerta). Pasadas con alerta, TIF usable y record
`ctx_cluster` de 2 o más píxeles con centroide dentro del `inner_radius_km`: la semilla del disco debe
caer a ≤ 0,75 km de nuestro centroide en al menos la mitad. Hay 110 pasadas (50 de Cordón Caulle, cuyo
`inner_radius_km` es 20 km, así que se informa también sin él). Si H no pasa, todo veredicto baja a
SOSPECHA.

**Placebo (sólo M1, informativo, no compuerta)** (N6). Se repite M1 con el TIF de otra pasada nocturna
del mismo volcán a más de 3 días, sobre **2.000 sorteos** (`random.Random(144)`), y se informa la
distribución de la tasa de identidad, no un sorteo único. Queda escrito de antemano: en volcanes con
fuente persistente al radio del anillo (Lastarria, Isluga, Tupungatito) el placebo **no** separa una
fuente fija de un instrumento ciego, así que ahí no se interpreta.

**Control de M2**: el propio P' (mismo raster, misma pasada, misma distancia al cráter). Es el control
correcto para "¿hay calor aquí?", porque comparte el ruido del granule y la banda de distancia.

## 6. M1: dirección, donde la coincidencia de radio ocurre

**Universo**: pasadas con alerta CONS, TIF usable, record del brazo control (noches de S143) o de
producción (el resto) con patrón, no `cerca`, con P y F dentro de la región de búsqueda (la unión del
disco de 3,4 km alrededor del cráter y el disco de `Distancia_km` + 1 km alrededor de `mirova_center`) y
**con el radio de P compatible con `Distancia_km`**: |r_P(mirova_center) − `Distancia_km`| ≤ 0,55 km, que
es la cota del A/B S143 (`parametros.json`). Esa es la población de la pregunta (N2).

**Semilla**: el máximo de z sobre el anillo |r − `Distancia_km`| ≤ 0,6 km dentro de la región, con
z ≥ `zc_anillo`. Si no hay, la pasada queda **sin identidad** y se cuenta aparte.

**Clases** (T = 0,75 km): `P` si d(semilla, P) ≤ T y d(semilla, F) > T; `F` si d(semilla, F) ≤ T y
d(semilla, P) > 2T; `otro` si d(semilla, P) > 2T y d(semilla, F) > T; `indefinido` en cualquier otro
caso. La corona entre T y 2T alrededor de P queda en `indefinido` y se informa aparte, porque excluirla
del denominador empujaría a favor de `P` (N14).

**Las noches de S143** se informan una por una (Isluga 2026-06-16, Lastarria 2026-06-07, 2026-06-14 y
2026-07-25; Láscar sale, §2). Los candidatos de cada noche son **todos** los records del control con
patrón de esa noche, cada par (semilla, record) con su clase; no hay clase de noche (N11). Isluga no
tiene TIF en sus pasadas con alerta (05:24 y 06:00). Lastarria 06-14 tampoco lo tiene en la pasada del
record que coincidió (05:00).

**M1 no tiene veredicto.** Es descriptiva: n chico y Lastarria contaminada (§1). Lo que sí se declara de
antemano es cómo se lee: si en Lastarria las semillas con identidad caen sobre P, la coincidencia de
radio de S143 era el mismo objeto en ese volcán, lo que es esperable si el objeto es el campo fumarólico
Lazufre; si caen lejos de P, la coincidencia era de radio.

## 7. M2: presencia, donde publicamos un cúmulo lejano

**Universo**: pasadas VIIRS 375 nocturnas de producción con patrón, publicadas, con TIF usable de la
misma pasada, en las que P y P' tienen ΔL0. Se estratifica por **etiqueta** de
`banco_paridad.etiquetar` (`pos` = MIROVA alertó, `neg_limpio` = MIROVA miró y dijo RUTINA con VRP 0;
`far_ref` y `sin_info` se informan aparte y no entran al veredicto), por **volcán** y por **tramo**
(antes y después de #535, A104).

**Medida**: `Z(P)`, `Z(P')` y `Z(F)` en cada pasada. Se informa, por estrato: la fracción con
`Z(P) ≥ zc_punto`, la misma para P' y para F, y la mediana de la diferencia pareada `Z(P) − Z(P')` con
intervalo por bootstrap estratificado (2.000 remuestreos, `random.Random(144)`).

**Veredicto**, sobre los negativos limpios fuera de Lastarria, con al menos 30 pasadas:
- **"el cúmulo lejano cae sobre calor del campo de MIROVA"** si la fracción con `Z(P) ≥ zc_punto` supera
  a la de P' en 0,15 o más **y** la mediana de la diferencia pareada es positiva con intervalo que
  excluye el 0;
- **"no se distingue de un punto cualquiera a la misma distancia del cráter"** si esa diferencia de
  fracciones es menor que 0,05 **y** el intervalo de la diferencia pareada contiene el 0;
- en cualquier otro caso, INCONCLUSO.

Los dos tramos se informan por separado; si ambos tienen al menos 30 pasadas y dan lecturas opuestas, el
veredicto es INCONCLUSO. Lastarria, Isluga y Tupungatito se informan aparte por fuente persistente, y
Lastarria además por contaminación.

**Qué NO dice M2**: no dice que P sea el objeto que MIROVA **publicó**. En una pasada con alerta,
MIROVA y nosotros leemos el mismo granule, así que un píxel alto por ruido o por un foco sub-umbral
destaca en los dos (ruido compartido). Por eso el veredicto se toma sobre **negativos limpios**, donde
MIROVA miró y no publicó nada: ahí "hay calor donde publicamos" significa que el rasgo existe en su
campo aunque no lo alerte (categoría b de A54), y "no se distingue de su reflejo" significa que lo que
publicamos no tiene correlato en el campo de MIROVA.

## 8. Qué se hace con el resultado

| M2 (negativos limpios, fuera de Lastarria) | M1 (Lastarria, descriptiva) | Lectura | Siguiente paso propuesto |
|---|---|---|---|
| no se distingue de su reflejo | semillas lejos de P | lo que `keep_peak` publica no tiene correlato en el campo de MIROVA, y la coincidencia de radio no era el mismo objeto | pre-registrar una cota con dirección y re-evaluar el A/B S143 con ella, sin re-correrlo |
| cae sobre calor | semillas sobre P | el cúmulo lejano es un rasgo térmico real que MIROVA también ve y no publica (categoría b) | no apagar `keep_peak` sin medir qué se pierde; el frente pasa a ser de etiquetado, no de detección |
| las dos partes discrepan, o INCONCLUSO, o G o H fallan | | | informar y no mover nada |

**Veredictos alcanzables con el n y la geometría de hoy** (N1 pide declararlo): M2 tiene muestra de sobra
(del orden de 850 pasadas con patrón y etiqueta `neg_limpio` aproximada, antes de exigir TIF usable), así
que sus tres salidas son posibles. M1 tiene del orden de 12 pasadas en Lastarria y 1 fuera, así que **no
puede generalizar** y por eso no tiene veredicto. Ninguna medida puede concluir "es el objeto publicado
por MIROVA" fuera de Lastarria: esa pregunta necesita pasadas donde la coincidencia de radio ocurra, y
hoy no las hay.

## 9. Límites conocidos

- El embudo de M1 medido por la ronda 2 con las reglas de la v2: 56 pasadas con patrón, alerta y TIF
  usable; 51 con P y F en la región; 34 sin `cerca`; 20 con identidad (12 fuera de Lastarria). Al
  agregar la compatibilidad de radio de §6, fuera de Lastarria queda 1.
- La estratificación por tramo de M2 puede quedar coja: de las pasadas con alerta sólo 3 son posteriores
  a #535. En negativos limpios el n por tramo se informa y decide si la comparación se hace.
- Los TIF geográficos son un remuestreo de MIROVA con método no documentado; G lo valida en Láscar.
- La semilla es el mayor exceso local del anillo, no el cúmulo que MIROVA sumó (S142 no logró
  reconstruirlo).
- La hora de adquisición del índice puede no ser la de la imagen (A106); el md5 propio y la mediana
  nocturna lo acotan sin probarlo imagen por imagen.
