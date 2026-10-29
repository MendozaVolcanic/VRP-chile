# Las 13 publicaciones diurnas sin pasada de MIROVA (VD167-01): clasificación

Investigación de sólo lectura, 2026-10-29. Nada del repo se editó, commiteó ni despachó. Todo vive en
`D:\vrp-trabajo\temporales\s167_diurnas_13\`. Ninguna clasificación de este informe cambia la regla sellada: es
información para la decisión de Nicolás sobre abrir el día en VIIRS (issue #813).

## 1. Qué se reprodujo y con qué

- **Lista de las 13**: `scripts\reproducir_13.py` (salida `reproducir_13_salida.txt`, records completos en
  `trece_records.json`). Usa el mismo evaluador que la lectura (`evaluar_diurno_k.py` y `sustrato_k.py` con sha1
  idéntico a `origin/main`, comprobado), las salidas de los cinco runs W2 a W6 ya bajadas por el lector en
  `D:\vrp-trabajo\temporales\s167_diurno_lectura\corridas\` y la referencia congelada de
  `D:\vrp-trabajo\temporales\s167_diurno_lectura\ref\` (el script imprime `ref distinta: []` contra `sustrato_k.json`).
  Da exactamente las 13 del verificador, 7 de 1 MW o más, con la misma regla de pareo (±120 s, mismo volcán y sensor).
- **Contexto por publicación**: `scripts\analizar_13.py` (salida `analizar_13_salida.txt`, `contexto_13.json`):
  geometría solar y ángulo de reflejo con `evaluar_diurno_k.angulo_reflejo` (fórmula del README de MIROVA, §7 del
  pre-registro), píxeles con distancia y rumbo al cráter (`vent_lat`/`vent_lon` de `volcanoes.yaml`), nocturnas
  propias ±72 h con el predicado del tablero (node) sobre el JSON de producción de `origin/main` `142ce3163`
  (bajado con `git -c core.autocrlf=false archive`, 91 MB, seis volcanes), filas de MIROVA ±72 h en los cuatro CSV.
- **Las otras pasadas de la misma tarde**: `scripts\mismo_dia.py` (`mismo_dia_salida.txt`).
- **Historia nocturna del punto**: `scripts\historia_puntos.py` (`historia_puntos_salida.txt`): cuántos records
  nocturnos de 2026 en producción tienen un píxel anómalo a 1 km o menos del punto diurno.
- **Clase del estudio 1.13** (magnitud diurna contra la mayor nocturna publicada, mismo sensor, ±72 h, T = 3,16):
  `clase_113_salida.txt`.
- **TIF de MIROVA**: índice remoto de `mirova-tif-archive` leído por la API (`tif_index\index.csv`, 5 MB, sin pull). Un
  solo TIF bajado (146 KB, `tif\pcc_20260613_1800.tif`, md5 igual al del índice).

Disco al terminar: C: 27 GB libres, D: 6,2 GB libres.

## 2. Lo que se ve en conjunto, antes de la tabla

Dos hechos ordenan todo:

1. **Ningún caso es reflejo especular.** El ángulo de reflejo va de 33,8° a 89,8°; el filtro de MIROVA corta bajo 12°.
   Lo que sí puede pasar de día es que la superficie misma se caliente al sol o refleje difuso en el infrarrojo medio,
   y eso no lo ve el ángulo.
2. **MIROVA tampoco tiene imagen de ninguno de los 13 gránulos.** El archivo de TIF no tiene ninguna adquisición a
   ±3 min de ninguna de las 13 pasadas, y sí tiene las pasadas vecinas que la tabla lista (por ejemplo Puyehue 06-13
   18:00 y 19:36, Villarrica 08-19 18:24). O sea que estas pasadas no son «MIROVA miró y no vio»: son pasadas que
   MIROVA no expuso. Límite: el archivo guarda sólo lo que el sondeo alcanzó a capturar, y está congelado desde el
   2026-09-22, así que para las de octubre es SIN DATO.

Y una regularidad física en Villarrica que conviene tener a la vista: **cada tarde en que el brazo publicó el cráter,
fue la pasada más cercana al nadir** (cenit del sensor 1,4° a 21°), y las otras de la misma tarde (35° a 70°) no
publicaron. Las dos tardes en que esa pasada cercana al nadir sí estaba en la tabla (08-21 18:54, cenit 21,3°, y
08-22 18:36, cenit 8,3°), **MIROVA también alertó** (1,56 y 0,53 MW) y el brazo también publicó (1,46 y 0,85 MW).
Mecanismo probable, SOSPECHA no medida: el lago de lava es sub-píxel y está al fondo del cráter; mirando casi vertical
el píxel es más chico y la pared no tapa el lago, así que la fracción caliente del píxel es máxima.

## 3. Tabla

Columnas: VRP publicado (lo que el tablero muestra, MW); distancia y rumbo del hotspot al cráter; Sol = elevación
solar; cen = cenit del sensor; refl = ángulo de reflejo; Tfondo / Tmáx en K; noches propias = publicaciones nocturnas
de producción ±72 h, todos los sensores (n publicadas / máximo MW); MIROVA = lo que la referencia trae ese día o ±72 h.

| # | volcán | sensor, plataforma | hora UTC | VRP | dist, rumbo | Sol / cen / refl | Tfondo / Tmáx | noches propias ±72 h | MIROVA | clase |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Puyehue C. Caulle | V375 SNPP | 06-13 19:18 | 0,41 | 17,5 km N | 17° / 41° / 90° | 276 / 297 | 19 / 0,53, todas a 0,1 a 17,7 km pero ninguna en ese punto | 18:00 RUTINA en el mismo punto (ver nota) | artefacto probable |
| 2 | Chaitén | V375 SNPP | 07-20 19:30 | 0,45 | 1,1 km NNE | 18° / 41° / 89° | 278 / 298 | 8 / 0,16, a 0,1 a 0,4 km | RUTINA 17:48, 18:06, 19:48; alertas nocturnas 0,06 a 0,07 | SIN DATO |
| 3 | Tupungatito | V375 NOAA-20 | 08-30 18:42 | 2,25 | 4,8 km S | 39° / 18° / 62° | 269 / 313 | 0 de 60 pasadas | **alerta diurna 18:24, 0,69 MW** a 2,65 km de su centro; ninguna nocturna | artefacto probable, con reserva |
| 4 | Villarrica | V375 SNPP | 08-18 18:42 | 0,38 | 0,25 km | 31° / 9° / 56° | 280 / 306 | 6 / 1,65, a 0,04 a 0,23 km | alertas nocturnas 0,67 a 1,86 MW | calor volcánico probable |
| 5 | Villarrica | V375 NOAA-20 | 08-19 18:48 | 2,41 | 0,15 km | 31° / 2° / 60° | 284 / 322 | 6 / 1,65 | ídem; diurnas 08-21 (1,56) y 08-22 (0,53) | calor volcánico probable |
| 6 | Villarrica | V375 SNPP | 08-23 18:54 | 2,34 | 0,06 km | 32° / 1° / 59° | 286 / 322 | 5 / 1,90, a 0,06 a 0,34 km | alertas nocturnas 0,6 a 2,21 MW | calor volcánico probable |
| 7 | Puyehue C. Caulle | V375 SNPP | 08-17 19:06 | 0,29 | 18,2 km NW | 28° / 16° / 69° | 278 / 294 | 15 / 0,66, casi todas a <0,6 km | RUTINA 17:42 y 19:24 | artefacto probable |
| 8 | Puyehue C. Caulle | V375 NOAA-20 | 08-24 18:54 | 0,18 | 12,7 km WSW | 31° / 7° / 62° | **256** / 278 | 9 / 1,28, casi todas a <0,4 km | RUTINA 17:54, 18:30, 20:12 | artefacto probable |
| 9 | Lastarria | V375 NOAA-21 | 10-12 17:42 | 1,63 | 2,1 km NNW | **63°** / 49° / 34° | **300** / 314 | 2 / 0,28 | nocturnas 0,07 y 0,18 MW; FALSO_POSITIVO 05:12 a 15 km | artefacto probable (de magnitud) |
| 10 | Nevados de Chillán | V375 NOAA-21 | 10-01 17:42 | 1,70 | 1,1 km SW | 53° / 59° / 50° | 288 / 318 | 23 / 11,1, a 0,4 a 2 km, rumbos 180 a 270 | **alerta diurna 18:42: 2,53 (V375) y 3,71 MW (V750)** a 0,38 y 0,75 km | calor volcánico probable |
| 11 | Nevados de Chillán | V375 SNPP | 10-01 18:18 | 4,21 | 0,52 km SW | 48° / 38° / 34° | 279 / 338 | ídem | ídem | calor volcánico probable |
| 12 | Nevados de Chillán | V750 SNPP | 10-01 18:18 | 2,99 | 0,24 km SW | 48° / 38° / 34° | 271 / 289 | ídem | ídem | calor volcánico probable |
| 13 | Puyehue C. Caulle | V375 SNPP | 10-01 18:18 | 0,11 | 16,2 km W | 44° / 46° / 39° | 267 / 282 | 8 / 5,0, a 5 a 19 km | RUTINA 18:42, 19:24, 20:00 | artefacto probable |

## 4. La evidencia de cada una

**1. Puyehue 06-13 19:18 (artefacto probable).** El píxel está 17,5 km al norte del cráter de 2011, dentro del radio
interior de 20 km (por eso «summit») pero lejos de todo lo que el volcán emite de noche: en 2026 sólo 1 de 3.505
records nocturnos tiene un píxel a 1 km de ese punto. La misma tarde, en la pasada de las 18:00, el brazo publicó **el
mismo punto** (17,3 km N, 1,14 MW) y MIROVA la listó como RUTINA; esa ya cuenta como negativo publicado. El TIF de
MIROVA de esa pasada de las 18:00 muestra el punto como lo más brillante de la escena (percentil 99,9, en el borde
norte de su grilla): MIROVA vio la misma superficie brillante y la juzgó sin anomalía. Lo que hay ahí de día no se ve
de noche: es una superficie calentada o iluminada por el sol (A109: el TIF es del mismo gránulo que nuestra
publicación de las 18:00, así que confirma el brillo, no que sea calor volcánico).

**2. Chaitén 07-20 19:30 (SIN DATO).** Un píxel a 1,1 km NNE del cráter, 20 K sobre el fondo, Sol bajo (17,5°). De
noche el domo se ve débil (0,05 a 0,16 MW a menos de 0,5 km) y ese punto aparece en 16 de 3.598 records nocturnos de
2026: hay fuente débil cerca. Pero la magnitud diurna es 2,8 veces la mayor nocturna, MIROVA dio RUTINA en tres
pasadas de esa tarde y el brazo no publicó en ninguna otra. No hay con qué separar calor débil real de una ladera al
sol de la tarde.

**3. Tupungatito 08-30 18:42 (artefacto probable, con reserva importante).** Dos píxeles 4,7 a 4,8 km al sur del
cráter y uno a 12 km, de 299 a 306 K sobre un fondo de 269 K. Es una señal sólo diurna: 0 publicaciones nocturnas en 60
pasadas ±72 h, ninguna alerta nocturna de MIROVA en esa ventana, y 2 de 3.135 records nocturnos de 2026 con píxel a 1
km del punto. El calor volcánico real se ve mejor de noche, no peor, y por eso lo clasifico como artefacto. **La
reserva**: MIROVA alertó en la pasada de las 18:24 de esa misma tarde (0,69 MW, 2,65 km de su centro). El centro de
la grilla de MIROVA está 4,9 km al SSE de nuestro cráter, y nuestro píxel queda a 2,0 km de ese centro: el radio es
compatible, pero un radio sin acimut no identifica el objeto (A93, A107). MIROVA tiene otras cuatro alertas diurnas en
Tupungatito en la referencia (04-05, 04-13, 08-15, 08-20 en V750) y en la del 08-15 el brazo también publicó (6,4 km
S). O sea: es probablemente la misma mancha diurna al sur del cráter que MIROVA también publica a veces. Contra la
vara de la réplica, si la pasada hubiera estado listada, MIROVA podría haber alertado.

**4 a 6. Villarrica 08-18, 08-19 y 08-23 (calor volcánico probable).** El lago de lava activo de agosto: un solo píxel
de 306 a 322 K a 0,06 a 0,25 km del cráter, el mismo lugar donde el brazo y producción publican de noche (57 records
nocturnos de 2026 en ese punto; 0,72 a 1,90 MW ±72 h) y donde MIROVA alerta de noche (0,67 a 2,21 MW). Las dos
grandes (2,41 y 2,34 MW) quedan dentro de 1,5 veces la mayor nocturna. Las tres son la pasada más cercana al nadir de
su tarde, y en las dos tardes en que esa pasada sí estaba en la tabla MIROVA alertó (ver §2).

**7. Puyehue 08-17 19:06 (artefacto probable).** 18,2 km al NW, 16 K sobre el fondo, 0,29 MW. Las noches de ±72 h
publican en el cráter (casi todas a menos de 0,6 km); en ese punto, 1 de 3.505 records nocturnos de 2026. MIROVA dio
RUTINA a las 17:42 y 19:24.

**8. Puyehue 08-24 18:54 (artefacto probable).** 12,7 km al WSW, tres píxeles de sólo 268 a 271 K sobre un fondo de
256 K: el fondo frío es la firma de nube (A23). 0 de 3.505 records nocturnos en ese punto. MIROVA dio RUTINA en tres
pasadas de esa tarde.

**9. Lastarria 10-12 17:42 (artefacto probable, de magnitud).** El lugar es real: 2,1 km al NNW del cráter, donde el
campo fumarólico se ve de noche (170 de 2.814 records nocturnos de 2026 con píxel a 1 km). La magnitud no lo es: casi
al mediodía (Sol a 63°) y con el suelo del desierto a 300 K, los píxeles cerca del cráter (306 a 312 K) no son más
calientes que los que el mismo gránulo marca a 16 y 20 km (305 a 308 K). La publicación, 1,63 MW, es 5,8 veces la
mayor nocturna (0,28 MW) y desproporcionada por el instrumento 1.13; MIROVA de noche da 0,07 a 0,18 MW. Es calor
solar del terreno sobre una fuente real débil: como alerta de 1,6 MW es falsa.

**10 a 12. Nevados de Chillán 10-01 (calor volcánico probable).** Día de erupción: MIROVA alertó esa madrugada hasta
10 MW y a las 18:42 de esa misma tarde alertó de día (2,53 MW en V375 y 3,71 MW en V750, a 0,38 y 0,75 km). Nuestras
tres caen a 0,24 a 1,1 km al SW del cráter, el mismo sector donde caen las nocturnas (rumbos 180 a 270), con 17 a
59 K sobre el fondo, y el brazo también publicó la pasada de las 18:42 (3,03 y 4,30 MW). Son la misma erupción vista
en pasadas que la tabla no lista.

**13. Puyehue 10-01 18:18 (artefacto probable).** 16,2 km al W, 0,11 MW, fondo de 267 K. Mismo gránulo SNPP que la
publicación 11 de Chillán, pero 300 km al sur; el punto aparece en 2 de 3.505 records nocturnos de 2026. MIROVA dio
RUTINA en tres pasadas de esa tarde. Nota: el instrumento 1.13 la llama «consistente» (y también a las 1, 7 y 8)
porque compara magnitudes y Puyehue publica de noche cosas de ese tamaño en el cráter; no mira la posición.

## 5. Resumen y balance

| clase | VIIRS 375 | VIIRS 750 | de 1 MW o más |
|---|---|---|---|
| calor volcánico probable | 5 (Villarrica 3, Chillán 2) | 1 (Chillán) | 5 |
| artefacto probable | 6 (Puyehue 4, Lastarria, Tupungatito) | 0 | 2 (Tupungatito 2,25; Lastarria 1,63) |
| SIN DATO | 1 (Chaitén) | 0 | 0 |

**Seis de las trece parecen falsas alarmas, todas en VIIRS 375**: las cuatro de Puyehue, lejos del cráter, en puntos
que de noche no se ven nunca; la de Lastarria, que está sobre una fuente real pero con magnitud de sol; y la de
Tupungatito, señal sólo diurna, con la reserva de que MIROVA publicó algo compatible esa misma tarde. Las seis de
Villarrica y Chillán son calor volcánico visto en pasadas que MIROVA no expuso; en Villarrica, las dos tardes en que
la pasada cercana al nadir sí estaba listada, MIROVA alertó, y en Chillán alertó en la pasada listada de esa misma tarde.

**Efecto en el balance de VIIRS 375 si se contaran como negativos** (informativo; la regla sellada no las cuenta y
§0 de este encargo lo mantiene):

- Hoy: neto 0 (5 negativos publicados contra 5 alertas bajo 1 MW recuperadas), caso b, ADOPTAR.
- Contando sólo las 6 artefacto probable: neto +6, negativos de 1 MW o más de 2 a 4, Q_d de 5/2.246 a 11/2.252
  (0,0049, sigue bajo Q_n 0,0367), D sigue cumpliendo (14 de 36 alertas). Neto > 0, P ≥ 1 y D cumple: **caso e**, y
  con la opción sellada e-ii, DECIDE NICOLÁS CON M4. Lo mismo con +7 (sumando Chaitén) o +12 (las doce).
- Basta una sola contada como negativo para pasar del caso b al e, porque el neto está en 0 exacto (VD167-02).
- Contar las seis reales como negativos sería contar como error calor volcánico que MIROVA, cuando lista la pasada
  equivalente, publica. Contarlas como alertas recuperadas tampoco se puede: no hay fila de MIROVA. Quedan fuera.

Lo que esto le dice a la decisión: el estrato sin etiqueta no es neutro. La mitad son falsas alarmas que la tabla no
castiga (seis, contra cinco negativos publicados que sí castiga), concentradas en Puyehue lejos del cráter, en el
radio interior de 20 km. La otra mitad es la señal que justifica abrir el día (lago de Villarrica cerca del nadir,
erupción de Chillán).

## 6. Lo no comprobado

- Ninguna imagen SWIR ni de alta resolución (Landsat, Sentinel-2) de esos días: el calor de Villarrica y Chillán se
  apoya en coherencia espacial y temporal con lo nocturno y con MIROVA, no en una observación independiente.
- Qué hay físicamente en los puntos de Puyehue y en la mancha al sur de Tupungatito (tipo de superficie, orientación
  de ladera): no lo sé y no lo adivino.
- El mecanismo del nadir en Villarrica es SOSPECHA: la regularidad está medida (3 de 3 tardes del brazo, 2 de 2 de
  MIROVA), la explicación no.
- Las publicaciones nocturnas de ±72 h salen del JSON de producción de `origin/main` `142ce3163` (detector K en todo
  el histórico); el brazo nocturno dentro de las ventanas da los mismos máximos donde se superponen.
