# Segundo verificador, contexto limpio, del pre-registro `keep_peak` con dirección (S144, v2)

**Veredicto: la v2 todavía NO es viable.** Las 13 observaciones de la primera ronda están casi todas
atendidas en el texto, y cinco de ellas quedan cerradas de verdad. Pero la corrección principal (el
anillo de identidad, que ata la semilla al radio que MIROVA publicó) volvió a meter el radio escalar
en el centro de la medida y produjo un defecto nuevo, más grande que los dos que cerró: **fuera de
Lastarria, la clase `P` es geométricamente imposible en 18 de las 19 pasadas elegibles**, así que
"es el objeto" no se puede alcanzar y "no es el objeto" es lo único que puede salir, sin que el TIF
aporte nada que el CSV de MIROVA no dijera antes. La única pasada donde `P` sí es alcanzable tiene el
cúmulo **a 0,15 km del cráter**, o sea no es el píxel lejano del que trata la pregunta.

Documento verificado: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md`
(v2 sin commitear, rama `s144-prereg-keep-peak-direccion`, sobre el commit `f6a1cb962`).

Mis scripts están fuera del repo, en
`...\3a2a7912-9e56-4be4-b449-f2c2c5bbe439\scratchpad\v2\`: `common.py` (índice, referencia, raster,
ΔL0, z, semilla), `zmin.py` (z_min por volcán), `pool.py` (pareo record-alerta-TIF), `partB.py`
(embudo de la Parte B), `ident.py` (alcanzabilidad, identidad real y placebo), `plac_var.py`
(variabilidad del placebo), `g2.py` (control G con las dos redacciones), `partA.py` (las 4 noches).
No modifiqué ningún archivo del repo salvo este informe.

## Aviso de contaminación (léelo antes de tocar la v2)

Para poder responder "¿hay un veredicto imposible de alcanzar?" tuve que medir propiedades que
**acotan** el resultado, aunque no clasifiqué ninguna pasada. Queda declarado:

1. Medí, pasada por pasada, si existe alguna celda del anillo de identidad a ≤ T de `P` y a > T de `F`
   (o sea, si la clase `P` es alcanzable). Eso fija un techo para la fracción `P`: fuera de Lastarria
   el techo es 1 de 19. No calculé dónde cae realmente la semilla en ninguna pasada.
2. Medí la tasa de identidad real y la del placebo por volcán (12 de 19 contra 5 de 19 fuera de
   Lastarria con la semilla 144). Eso adelanta el resultado de la compuerta del placebo.
3. Corrí el control G completo con la redacción de la v2 (pasa, con poco margen en un eje).
4. **No** calculé la clase P/F/otro/indefinido de ninguna pasada de la Parte A ni de la Parte B, ni la
   fracción `P`, ni los z de la Parte A2 ni los de la Parte C.

---

## Estado de las 13 observaciones de la primera ronda

| # | Tema (ronda 1) | Estado | Evidencia mía de esta sesión |
|---|---|---|---|
| 1 | La latencia dejaba 2 noches y §7 hacía INCONCLUSA la medida entera | **cerrado** | v2 l. 89-92 la baja a sensibilidad; l. 173 declara la Parte A descriptiva y l. 196-201 ya no la usan para decidir. Con las reglas v2, Lastarria 06-14 06:06 (latencia 13,3 h) es usable: `own=True`, mediana 0,053 (`partA.py`). Quedan 3 noches, las 3 de Lastarria |
| 2 | El disco centrado en `mirova_center` dejaba a `P` fuera | **cerrado, con efecto nuevo** | Región unida (l. 111-113): `P` queda dentro en las 56 pasadas del pool. Ahora el que queda fuera es `F`: 5 pasadas (PCC 3, Tupungatito 1, Láscar 1), todas fuera de Lastarria (`partB.py`) |
| 3 | "azar" y "≤ 1/3" eran el resultado por defecto; el placebo no lo atrapaba | **parcial** | z_min y la regla numérica del placebo sí frenan el ruido puro (una celda fija supera z_min en 0,000 a 0,009 de las pasadas RUTINA, `zmin.py`). Pero el defecto de fondo sigue: "≤ 1/3" es el default por geometría (N1) y la segunda condición del veredicto es vacía (N4) |
| 4 | La semilla ignoraba el radio publicado | **cerrado en la forma, abierto en el fondo** | El anillo es ahora principal (l. 115-120). Es justo lo que produce N1, N2 y N3 |
| 5 | Los records del control vencían el 2026-10-02 | **cerrado** | `experiments/_s144_keep_peak_direccion/control_s143/` está versionado (19 archivos en `git ls-files`) y los 18 sha256 del `MANIFIESTO.json` coinciden con los `.json.gz` (recalculados en esta sesión) |
| 6 | Láscar 06-13 no era un píxel lejano; la coincidencia fue entre pasadas | **cerrado** | §1 l. 38-43 lo dice. Reproduje los números: record 04:42, `P` a 0,32 km del cráter, d(P,F) = 0,49 (`partA.py`). En las 5 noches el record de la pasada con alerta tiene d(P,F) = 0 (0,19 en 06-14) |
| 7 | T no separaba a `P` de `F` en los `ctx_cluster` de Lastarria; faltaba la regla por noche | **cerrado, con residuo** | Regla `cerca` (l. 108-109) y agregación por noche (l. 166-167). Residuo: el conjunto de candidatos por noche es ambiguo (N11). Con las reglas v2 quedan `cerca` 11 de 26 pasadas de Lastarria y 6 de 30 fuera |
| 8 | La Parte B mezclaba regímenes que la Parte A excluye | **parcial** | l. 132-133 manda informar por tramo, pero sólo 2 de las 19 pasadas elegibles fuera de Lastarria son post #535 (N5): el veredicto describe el código viejo |
| 9 | Ruido compartido: la Parte C no condicionaba la lectura | **parcial** | l. 186-192 la vuelve condición, pero sólo rebaja "es el objeto", que es inalcanzable (N7) |
| 10 | G validaba casi sólo Láscar y no veía un corrimiento de una celda | **parcial** | Tope de desplazamiento medio agregado (l. 140). Con la redacción literal de la v2 me da 0,166 km en norte-sur contra un tope de 0,19 (N8). Alcance declarado correcto: 42 pasadas de Láscar y 1 de Villarrica |
| 11 | Definición y cita de la latencia | **cerrado** | l. 89-92: primera `captured_at_utc` del md5 y cita a §2.1 |
| 12 | "el píxel de `keep_peak`" era una inferencia | **cerrado** | l. 104-106: "el centroide del cúmulo primario cuando tiene un solo píxel", con el caveat del segundo pase |
| 13 | "mismo satélite" no se podía calcular | **cerrado** | l. 215-216. Comprobado en las noches de la Parte A: las pasadas de la misma noche están a 18 min o más (Lastarria 06-07: 04:54, 05:30, 05:48, 06:36), así que ±120 s separa |

---

## Hallazgos nuevos (ordenados por gravedad)

### N1. El anillo devuelve la medida al radio escalar: fuera de Lastarria la clase `P` es imposible en 18 de 19 pasadas, y "es el objeto" no se puede alcanzar

- **Dónde**: v2 l. 115-120 (semilla dentro del anillo `|r − Distancia_km| ≤ 0,6`), l. 122-130
  (clasificación con T = 0,75) y l. 178-181 (veredicto).
- **Evidencia** (`ident.py`, sobre las pasadas elegibles: patrón, TIF usable, `P` y `F` dentro de la
  región, no `cerca`). Cuento, sin mirar valores del raster, si existe alguna celda del anillo a
  ≤ 0,75 km de `P` y a > 0,75 km de `F` (clase `P` alcanzable) y lo mismo para `F`:

  | | `P` alcanzable | `F` alcanzable | ninguna |
  |---|---|---|---|
  | fuera de Lastarria (n = 19) | **1** | 15 | 3 |
  | Lastarria (n = 15) | 12 | 4 | 0 |

  Con la otra `Distancia_km` de la misma pasada (ver N3) fuera de Lastarria da 1 igual.
- **Qué pasa**: el anillo tiene 1,2 km de ancho y está centrado en el radio que MIROVA publicó. Si
  `P` está a 2,7 km de `mirova_center` y MIROVA publicó 0,53 km, ninguna celda del anillo puede caer
  a menos de 0,75 km de `P`. O sea, el radio escalar decide la clase antes de abrir el TIF, y el TIF
  sólo elige entre `F` y `otro`. La regla de veredicto exige fracción `P` ≥ 2/3 sobre ≥ 10
  clasificables para "es el objeto": con a lo más 1 pasada capaz de dar `P`, **esa fila de la tabla
  de §7 es inalcanzable**. Quedan dos salidas posibles: "no es el objeto" o INCONCLUSO.
- **Cómo se ve en el resultado**: "medimos con dirección y el cúmulo lejano casi nunca es el objeto de
  MIROVA", cuando lo que se midió fue otra vez el radio, que es exactamente lo que A93 y A107 dicen
  que no identifica un objeto. La dirección, que es el aporte del TIF, sólo se usa para separar `F`
  de `otro`.
- **Cómo reproducirlo**: `python zmin.py && python pool.py && python partB.py && python ident.py`
  desde el scratchpad `v2`.
- **CONFIRMADO. Gravedad 5.**

### N2. La población de la Parte B no es la población de la pregunta: la coincidencia de radio que motivó la medida ocurre en 1 de 19 pasadas fuera de Lastarria y en 12 de 15 en Lastarria, que es la que no tiene veredicto

- **Dónde**: v2 §1 l. 45-51 (la pregunta es si la coincidencia de radio era el mismo objeto), l. 175-184
  (Parte B), §0 l. 22 (Lastarria sólo descriptiva).
- **Evidencia** (`ident.py` más el bloque de cota): aplico la cota del A/B S143
  (`experiments/_s143_evaluador/parametros.json`, `cota_km = 0.55`) al radio de `P` desde
  `mirova_center`. Fuera de Lastarria la cumple **1 de 19** (PCC 2026-05-23, y ahí `P` está a
  **0,15 km del cráter**, con `F` a 10,96 km, o sea el patrón está invertido respecto de §1). En
  Lastarria la cumplen **12 de 15**.
- **Qué pasa**: la Parte B mide sobre pasadas donde el propio CSV de MIROVA ya dice que su objeto no
  está al radio de `P`. Ahí "no es P" no es un hallazgo, es el dato de entrada. Las pasadas que sí
  plantean la pregunta están casi todas en Lastarria, que la v2 excluye del veredicto por
  contaminación (§0) y por ser fuente persistente (l. 153-155).
- **Cómo se ve en el resultado**: un veredicto "no es el objeto" que se lee como generalización de las
  5 noches de S143 y que en realidad se construyó con pasadas de otra clase.
- **CONFIRMADO. Gravedad 4.**

### N3. No está fijado si la `Distancia_km` es la de CONS o la del OCR, y en 17 de 56 pasadas son distintas (hasta 5,21 contra 2,30 y 7,65 contra 3,51)

- **Dónde**: v2 l. 111-118 usan `Distancia_km` para la región y para el anillo, sin decir de qué fuente;
  §3 l. 69 nombra a CONS y OCR juntos.
- **Evidencia** (`partB.py`): de las 56 pasadas del pool, 17 tienen dos valores distintos a ±120 s, con
  el mismo VRP, uno por fuente. Ejemplos crudos: Tupungatito 2026-08-21 06:30 CONS 5,21 y OCR 2,30;
  PCC 2026-07-18 06:24 CONS 7,65 y OCR 3,51; Lastarria 2026-05-25 06:30 CONS 2,40 y OCR 0,00.
  La identidad cambia con la elección: fuera de Lastarria 12 de 19 con el valor menor y 14 de 19 con
  el mayor (`ident.py`).
- **Además, el OCR es poco confiable para esto** (`g2.py`): en las alertas donde la semilla cae al
  cráter y supera z_min, la mediana de `|r_semilla(mirova_center) − Distancia_km|` es 0,08 km con CONS
  y **4,24 km con OCR en PCC**; en Planchón-Peteroa OCR da 1,83 km (n chico, 2).
- **Qué pasa**: el ancho del anillo es 0,6 km y la diferencia entre fuentes llega a 4 km. Elegir
  después de ver los datos cambia qué pasadas tienen identidad y qué clase pueden tomar.
- **CONFIRMADO. Gravedad 4.**

### N4. La segunda condición de "no es el objeto" es aritméticamente vacía

- **Dónde**: v2 l. 178-179: "si la fracción `P` es ≤ 1/3 **y** al menos la mitad de las clasificables
  son `F` u `otro`", con clasificables = `P` + `F` + `otro` (l. 128).
- **Qué pasa**: si `P` ≤ 1/3 de las clasificables, entonces `F` + `otro` ≥ 2/3, que siempre es ≥ 1/2.
  La condición no puede fallar nunca. La "evidencia positiva" que el texto dice agregar (l. 128-130)
  la aportan las definiciones de clase (el 2T), no esta regla.
- **Cómo se ve en el resultado**: el informe final dirá "además exigimos evidencia positiva" sobre una
  cláusula que no filtró ninguna posibilidad.
- **CONFIRMADO (aritmética sobre el texto). Gravedad 3.**

### N5. La estratificación por tramo es decorativa: 2 de 19 pasadas elegibles fuera de Lastarria son posteriores a #535

- **Dónde**: v2 l. 132-133 y l. 183-184 (tramos con ≥ 5 clasificables cada uno).
- **Evidencia** (`partB.py`, `ident.py`): de las 56 pasadas del pool, 3 son post #535 (Isluga 1,
  Nevados de Chillán 1, Tupungatito 1); una de ellas queda `cerca`. De las 19 elegibles fuera de
  Lastarria, **2** son post #535, así que la regla de "los dos tramos con al menos 5" no se activa
  nunca y el veredicto queda hecho con el régimen pre #535.
- **Qué pasa**: es el mismo motivo por el que la Parte A no usa producción (§3 l. 72-73: "los records
  de junio y julio se generaron con otro código"), aplicado al revés.
- **CONFIRMADO. Gravedad 3.**

### N6. z_min se calibra en un disco fijo y se aplica a anillos de 8 a 419 celdas; el placebo no es raro en los volcanes de fuente persistente y la compuerta depende de la semilla del sorteo

- **Dónde**: v2 l. 97-101 (z_min = percentil 90 del z de la semilla RUTINA en un disco de 3,4 km),
  l. 118 (identidad) y l. 149-155 (placebo).
- **Evidencia**:
  - Celdas del disco de calibración: 257 en un TIF típico. Celdas del anillo donde se aplica el mismo
    umbral, por volcán (`ident.py`): Isluga 9 a 30, Chaitén 22 a 196, Lastarria 8 a 146, Tupungatito
    116 a 284, PCC 177 a 419. El umbral es un máximo sobre 257 celdas usado como corte de un máximo
    sobre 9 o sobre 419, así que la tasa de identidad por azar no es comparable entre volcanes.
  - Placebo (`plac_var.py`): calculé la identidad del placebo contra **todos** los TIF nocturnos
    candidatos de cada pasada. La tasa esperada es 0,49 a 0,51 en Isluga, 0,35 en Tupungatito, 0,36 y
    0,01 en PCC, 0,03 a 0,14 en Chaitén. La afirmación de l. 150-151 ("con el placebo la identidad
    casi nunca debería cumplirse") es falsa para Isluga y Tupungatito, que tienen fuente persistente
    al radio del anillo igual que Lastarria.
  - Con 2.000 sorteos, la identidad placebo media es 0,34 (percentiles 5 y 95: 0,16 y 0,47) y en
    **12,6 %** de los sorteos la diferencia contra el real cae bajo el 0,20 que exige la compuerta.
    La semilla 144 da 5 de 19, o sea pasa.
- **Qué pasa**: la compuerta del placebo depende de qué noche salió sorteada, y su premisa ("el
  placebo casi nunca da identidad") no se cumple donde el cráter está caliente todas las noches.
- **CONFIRMADO. Gravedad 3.**

### N7. La Parte C no puede cambiar ningún veredicto alcanzable, y compara una celda contra un umbral de máximos

- **Dónde**: v2 l. 186-192.
- **Qué pasa**: (a) la condición sólo rebaja "es el objeto", que por N1 es inalcanzable, así que la
  Parte C queda sin efecto sobre cualquier resultado posible; (b) mide `z(P) ≥ z_min` en **una** celda,
  mientras z_min es el percentil 90 del **máximo** sobre ~257 celdas. Medido: una celda al azar del
  disco supera z_min en 0,000 de las pasadas RUTINA en 10 de los 11 volcanes y en 0,009 en Tupungatito
  (`zmin.py`). El mismo desajuste afecta a la Parte A2 (l. 170-171), que pregunta si "hay exceso donde
  está P" con un umbral construido para máximos: la respuesta por defecto es "no".
- **Nota de tamaño**: la Parte C tiene muestra de sobra (852 pasadas con patrón y `neg_limpio`
  aproximado, todas `summit`), así que el problema no es el n.
- **CONFIRMADO. Gravedad 3.**

### N8. El tope de desplazamiento de G depende de la redacción y de una sola pasada: con el texto de la v2 da 0,166 km contra un tope de 0,19

- **Dónde**: v2 l. 137-141.
- **Evidencia** (`g2.py`, mismas 43 pasadas en los dos casos, sólo cambia la región de búsqueda):

  | región de la semilla | n | frac ≤ 0,75 km | mediana | norte-sur medio | este-oeste medio |
  |---|---|---|---|---|---|
  | disco de 4 km al cráter (texto v2, l. 138) | 43 | 0,907 | 0,273 | **0,166** | -0,093 |
  | disco `max(4, Dist+1)` a `mirova_center` (ronda 1) | 43 | 0,930 | 0,230 | 0,087 | -0,128 |

  El promedio lo manda una sola pasada: Láscar 2026-06-03 06:12 con la semilla a 3,79 km (3,50 km al
  norte) y z = 4,31. Sacarla deja el promedio en 0,065.
- **Qué pasa**: el tope se fijó conociendo el 0,067 de la ronda 1 (§0 l. 23-24), que salió de otra
  región de búsqueda. Con la redacción que quedó escrita el margen es de 0,024 km, y una pasada más
  con la semilla lejos lo cruza. Además la compuerta usa **promedio** sobre una distribución con cola
  (A70 pide mediana) y no exige z mínimo a la semilla de G, así que semillas de z ~3 a 4, que son
  ruido, entran al promedio.
- **CONFIRMADO. Gravedad 3.**

### N9. El sensor no está especificado en ninguna parte, y los records VIIRS 750 parean con el mismo TIF de 375 m

- **Dónde**: la v2 nunca nombra el sensor de los records ni el del TIF (la única mención de 375 es
  l. 55, sobre la grilla UTM).
- **Evidencia** (`pool.py`): el índice del archivo tiene 7.657 TIF VIIRS375, 8.179 VIIRS750 y 5.532
  MODIS. Pareando records de producción con TIF VIIRS375 a ±120 s salen 2.060 pasadas VIIRS375,
  **2.051 VIIRS750** y 18 MODIS, porque la banda M y la banda I son de la misma pasada. Con el patrón
  y alerta quedan 56 VIIRS375, 2 VIIRS750 y 1 MODIS.
- **Qué pasa**: quien escriba el script puede incluir los records de 750 m (píxel 4 veces más grande,
  otro `primary_cluster`) contra el TIF de 375 m sin violar nada de lo escrito.
- **CONFIRMADO. Gravedad 2.**

### N10. Las celdas sin dato no están en la definición de "TIF usable" ni en la de ΔL0

- **Dónde**: v2 l. 81-87 (usable) y l. 94-95 (ΔL0 y z).
- **Evidencia** (`pool.py`, `zmin.py`): de 2.060 TIF usables únicos, **6,5 % tienen más de 10 % de
  celdas NaN y 2,9 % más de 50 %** (por ejemplo `Villarrica/20260603_053001_VIIRS375.tif` con 90 %
  y `Chaiten/20260625_051801_VIIRS375.tif` con 72 %). En 19 pasadas RUTINA del pool de z_min el disco
  de 3,4 km queda **entero sin dato**, y mi script las descarta en silencio porque no hay regla.
- **Qué pasa**: "ΔL0 = L menos la media de las 8 vecinas" no dice qué hacer cuando faltan vecinas
  (promedio de las presentes, NaN, o cero, que daría un ΔL0 enorme). En las pasadas elegibles de la
  Parte B el efecto es chico (máximo 15 % de NaN, en Lastarria), pero en z_min y en el placebo sí pesa.
- **CONFIRMADO. Gravedad 2.**

### N11. El conjunto de candidatos de la Parte A es ambiguo, y con una de las dos lecturas la noche de Lastarria 06-07 puede empatar

- **Dónde**: v2 l. 164-167: "contra el P y el F del record que coincidió en S143 (el de la otra
  pasada)" y, dos líneas después, "si hay varios candidatos esa noche (Lastarria 06-07 tiene tres)".
- **Evidencia** (`partA.py`): en Lastarria 06-07 los records con patrón son 04:54 (d(P,F) = 2,91),
  05:30 (2,37) y 06:36 (0,96). El tercero queda `cerca` por l. 108-109, así que quedan **dos** pares
  clasificables y, si discrepan, la noche queda `indefinido` por l. 167. En 06-14 hay tres candidatos
  (05:00, 05:18 y 06:36) y el que coincidió en S143 fue el de 05:00, que no tiene TIF; §6 no lo dice.
  Para la A2, además del listado de l. 170, existe TIF propio en Lastarria 06-14 05:18 (latencia 10,1 h).
- **CONFIRMADO. Gravedad 2.**

### N12. Las cifras de muestra de §0 y §8 quedaron de la v1 (venían del filtro de latencia)

- **Dónde**: v2 l. 25-26 ("del orden de 37 pasadas usables, 15 de ellas en Lastarria") y l. 208
  ("del orden de 20 pasadas usables fuera de Lastarria").
- **Evidencia** (`partB.py`, `ident.py`), con las reglas de la v2 (sin latencia):

  | etapa | total | Lastarria | fuera |
  |---|---|---|---|
  | patrón + alerta + TIF usable | 56 | 26 | 30 |
  | menos `P` o `F` fuera de la región | 51 | 26 | 25 |
  | menos `cerca` (d(P,F) < 1,5) | **34** | 15 | **19** |
  | con identidad (z ≥ z_min, distancia menor) | 20 | 8 | 12 |

- **Qué pasa**: el texto subestima el pool bruto y sobreestima lo que queda después de los filtros
  nuevos. Con 12 pasadas con identidad fuera de Lastarria, el mínimo de 10 clasificables (l. 177)
  queda a dos pasadas de no alcanzarse, antes de descontar `indefinido`.
- **CONFIRMADO. Gravedad 2.**

### N13. La Parte B no exige que el record esté publicado, aunque §1 habla de "cuando publicamos"

- **Dónde**: §1 l. 45 y Parte B l. 175-177 (la Parte C sí lo exige, l. 186-187).
- **Evidencia**: corrí el predicado del dashboard con node sobre los 34 records elegibles
  (`banco_paridad.correr_node`, `frontend/index.html`): **33 publican**, el que no es de Lastarria.
  El control de identidad del predicado da `([0,1,1,1,0], [1,0])`, lo esperado.
- **Qué pasa**: hoy el filtro casi no mueve la muestra, pero está sin escribir y toca la pregunta.
- **CONFIRMADO. Gravedad 2.**

### N14. Detalles menores sin fijar

- La ventana temporal de las Partes B y C no está escrita (z_min sí dice "desde el 2026-05-09",
  l. 98). Mi pool arranca el 2026-05-01 y no cambia nada, pero es una elección libre.
- El sorteo del placebo (l. 150) no dice el generador ni el orden de las extracciones, así que "semilla
  fija 144" no reproduce por sí sola.
- El placebo no exige que la pasada sorteada sea RUTINA, así que puede caer sobre una noche con alerta.
- `indefinido` (l. 126) se queda con la corona T a 2T alrededor de `P`, que sale del denominador. Eso
  sube la fracción `P` y no la baja, o sea empuja a favor de "es el objeto" y no de "azar".
- **CONFIRMADO (lectura del texto). Gravedad 1.**

---

## VERIFICADO LIMPIO

- **Los records del control están de verdad congelados**: 19 archivos versionados en el commit
  `f6a1cb962` (`git ls-files experiments/_s144_keep_peak_direccion/control_s143`), rama subida a
  `origin/s144-prereg-keep-peak-direccion`, y los 18 sha256 del `MANIFIESTO.json` coinciden con el
  contenido descomprimido. La observación 5 de la ronda 1 está cerrada de verdad, no sólo en el texto.
- **Los números que la v2 escribe sobre Láscar 06-13 son correctos**: record 04:42, `P` a 0,32 km del
  cráter, `F` a 0,17 km, d(P,F) = 0,49, o sea fuera del patrón. Y en las 5 noches el record de la
  pasada con alerta tiene el cúmulo sobre el `final_hotspot` (d(P,F) = 0, salvo 0,19 en 06-14).
- **Isluga 2026-06-16 no tiene TIF en sus pasadas con alerta** (05:24 y 06:00): confirmado contra el
  índice; el único TIF nocturno de esa noche es el de 06:18, que es la pasada donde publicamos `P`,
  con md5 propio y latencia 6,4 h. La A2 de Isluga es factible.
- **El control G pasa con la redacción de la v2**: 43 pasadas (42 de Láscar, 1 de Villarrica), semilla
  a ≤ 0,75 km del cráter en 90,7 %, mediana 0,273 km, desplazamientos 0,166 y -0,093 km. Cumple los
  cuatro requisitos de l. 138-141, con el margen flaco que describe N8.
- **z_min es calculable y no queda vacío en ningún volcán**: n de pasadas RUTINA con TIF usable entre
  69 (Isluga) y 188 (Chaitén); z_min entre 3,97 (Llaima) y 8,74 (Láscar). Las pasadas RUTINA que uso
  son todas "puras" (ninguna trae además una fila de alerta), así que la ambigüedad "fila CONS RUTINA"
  contra "pasada RUTINA" no muerde hoy.
- **El umbral protege contra el ruido puro**: una celda cualquiera del disco supera z_min en 0,000 a
  0,009 de las pasadas RUTINA, así que la identidad no se cumple por azar de una celda suelta. Lo que
  sí varía mucho es el tamaño del anillo (N6).
- **El control H tiene muestra**: 110 pasadas con alerta, TIF usable y record `ctx_cluster` de 2 o más
  píxeles con el centroide dentro del `inner_radius_km` (PCC 50, Isluga 20, Láscar 19, Chaitén 11).
  La mitad que pide l. 147 es medible. Aviso: 50 de las 110 son PCC, cuyo `inner_radius_km` es 20 km.
- **El predicado de publicación corre** y su control de identidad da lo esperado (N13).
- **El pareo por tiempo es limpio**: ±120 s no confunde satélites (separación mínima observada entre
  pasadas de una misma noche: 18 minutos).

**No verificado** (queda abierto): los z de la Parte A2 y de la Parte C (no los calculé a propósito);
si el remuestreo geográfico de MIROVA corre la posición en los nevados (G sólo valida Láscar, igual
que en la ronda 1); las afirmaciones de §2 sobre el perfil radial de ΔL0 (las midió la ronda 1, no las
repetí); la ventana UTM de A106 (idem).

---

## Correcciones recomendadas para una v3, por gravedad

1. **(5) Decidir qué mide el anillo.** Tal como está, el anillo convierte la medida en la cota escalar
   de S143 más un desempate de acimut que sólo se usa para separar `F` de `otro`. Dos salidas posibles,
   y hay que elegir **antes** de medir:
   - **(a) Restringir la Parte B a la población de la pregunta**: pasadas donde el radio de `P` es
     compatible con `Distancia_km` (la cota de 0,55 km de S143). Ahí sí "¿es P o es otra cosa al mismo
     radio?" es una pregunta que el TIF contesta con dirección. Hoy esa población es 1 pasada fuera de
     Lastarria y 12 en Lastarria: la consecuencia honesta es que **la medida sólo se puede hacer en
     Lastarria**, y entonces hay que decidir qué hacer con la contaminación de §0 (por ejemplo, correrla
     igual y declararla descriptiva, o esperar a que la muestra crezca).
   - **(b) Sacar el anillo de la definición principal** y volver al máximo en la región, con el anillo
     como control de identidad **informado**, no como filtro. Eso reabre la observación 4 de la ronda 1,
     así que hay que decir por qué se acepta.
   En cualquiera de las dos, **declarar en §7 qué veredictos son alcanzables con el n y la geometría de
   hoy**. Un pre-registro que sólo puede salir "no es el objeto" o INCONCLUSO no debe presentar la fila
   "es el objeto" como si fuera una salida posible.
2. **(4) Fijar la fuente de `Distancia_km`** (propongo CONS, por el residuo de 0,08 km contra 4,24 km
   del OCR), decir qué se hace cuando hay dos valores y repetir todo como sensibilidad con el otro.
3. **(3) Arreglar la regla de veredicto**: sacar la cláusula vacía de l. 179 y reemplazarla por una
   condición que pueda fallar (por ejemplo, que la mayoría de las clasificables sean `F` u `otro`
   **sobre el total de pasadas con TIF usable**, contando `sin identidad` e `indefinido` en el
   denominador).
4. **(3) Calibrar z_min sobre la misma región donde se aplica** (el anillo de esa pasada, no un disco
   fijo), o declarar el número de celdas del anillo en cada pasada y aceptar la tasa de falsa identidad
   que eso implica. Y corregir l. 150-151: Isluga y Tupungatito también son fuentes persistentes; el
   placebo no separa ahí. Si la compuerta se mantiene, fijar el generador del sorteo y reportar la
   sensibilidad a la semilla (12,6 % de los sorteos la hacen fallar).
5. **(3) Decidir el tramo antes de medir**: o se restringe todo a post #535 y se acepta que hoy hay 2
   pasadas (o sea, esperar), o se declara explícitamente que el veredicto describe el régimen pre #535.
   La redacción actual promete una estratificación que no se puede ejecutar.
6. **(3) Poner la Parte C a condicionar el veredicto que sí es alcanzable**, o declararla informativa.
   Y comparar `P` contra `P'` con el mismo estadístico (máximo del disco de radio T en torno a cada uno,
   no la celda exacta), con un umbral calibrado para ese estadístico.
7. **(3) Endurecer G**: usar mediana además de promedio para el desplazamiento (A70), exigir z mínimo a
   la semilla de G, y escribir con precisión la región de búsqueda, porque el resultado del tope cambia
   de 0,087 a 0,166 km según cómo se lea.
8. **(2) Escribir el sensor** (VIIRS 375 en los records, en las filas de MIROVA y en los TIF) y la
   ventana temporal de las Partes B y C.
9. **(2) Definir las celdas sin dato**: qué cuenta como TIF usable (por ejemplo, menos de 10 % de NaN en
   la región de búsqueda), qué pasa si la región queda vacía y cómo se calcula ΔL0 con vecinas faltantes.
10. **(2) Cerrar la ambigüedad de la Parte A** (candidato único o todos los candidatos con patrón de la
    noche), completar la lista de TIF de la A2 (falta Lastarria 06-14 05:18) y decir que 06-14 tiene tres
    candidatos igual que 06-07.
11. **(2) Exigir en la Parte B que el record esté publicado**, como en la Parte C. Hoy cambia 1 de 34
    pasadas, o sea sale gratis.
12. **(1) Actualizar los tamaños de §0 y §8** con el embudo real (56, 34, 19 y 12 fuera de Lastarria).

**Resumen**: con la corrección 1 tomada en serio, la medida vuelve a tener sentido; sin ella, la v3
produciría un "no es el objeto" que ya está escrito en el CSV de MIROVA y que no necesita ningún TIF.
