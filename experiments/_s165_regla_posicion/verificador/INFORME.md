# Verificador con contexto limpio: S165, regla de posición «más radiante» contra «cercano»

Verificado el 2026-10-27 sobre `loop/activo` (`cdf2c1b95`) con `origin/main` en `bd711db63` (#921 ya mergeado). Sólo
lectura; mis scripts y salidas viven en esta carpeta (`experiments/_s165_regla_posicion/verificador/`), los
temporales en `D:\vrp-trabajo\temporales\s165_regla_posicion_verif\`. No hubo commit, push, workflow ni stash.

Scripts propios (cada uno escribe `<nombre>_salida.txt` al lado):

| script | qué mide |
|---|---|
| `01_referencia_y_offsets.py` | qué trae la copia de hoy de la referencia que los universos no miran; ceros de `Distancia_km`; desfase cráter contra X0, Y0 por volcán |
| `02_universo_v375.py` | de qué lotes y clases está hecho el universo de VIIRS 375, quiénes son las 66 SIN DATO, cobertura contra la población completa |
| `03_nulo_instrumento.py` | si la cadena variante, almacén y predicado con node PUEDE dar la dirección «calla» (A116) |
| `04_reproduccion_independiente.py` | el conteo de cambios en los tres sensores con reglas escritas de nuevo (`scipy.ndimage.label`), más los cruces del inner sin mirar la publicación |
| `05_far_ref_fuera_del_universo.py` | las pasadas `FALSO_POSITIVO` nocturnas de la tabla por sensor, que en VIIRS están fuera del universo |

## 1. Cobertura: cada afirmación del informe y qué la sostiene

| # | afirmación de `INFORME.md` | respaldo del autor | mi comprobación | veredicto |
|---|---|---|---|---|
| 1 | La vía mide desde el centroide del cúmulo de la alertada más radiante y la frontera es inclusiva (`dcen <= inner_km`) | `pipeline/mirova_v750_codigo.py` l. 717 a 725 | leído el código en `origin/main`; `git diff` de los nueve archivos importados contra `origin/main` vacío; los tres llamadores de producción (`process_modis.py:648`, `process_viirs.py:776`, `process_viirs_mod.py:512`) pasan `vent_lat/lon` que `run_pipeline.py:252/295/344` saca de `get_detection_anchor`, el mismo ancla que `comun.py` | CONFIRMADO |
| 2 | Regla importada idéntica a `origin/main` (97ef53aa) | `misma_regla_que_main` en cada salida | repetido en `04` contra `bd711db63`: `true, true`; el worktree de V375-E (`65458a830`) no difiere de `origin/main` en esos archivos (diff vacío) | CONFIRMADO |
| 3 | MODIS: 5.321 evaluadas de 5.465, 144 fuera del gránulo; clases 50 / 42 / 5.018 / 211 | `modis_salida.txt` | `04`: mismos conteos; las 144 son 92 `neg_limpio` y 52 `sin_info`, ninguna alerta ni `far_ref` | CONFIRMADO |
| 4 | MODIS: cambia 1 de 5.321 (Láscar 2026-03-30 07:25, `far_ref`), con las dos versiones de «cercano», dirección «publica de más» | `modis_salida.txt`, `modis_cambios.json` | `04` con reglas propias: id 1563, mismas distancias (26,221 / 0,255 / 1,0 km), 0 cruces sin cambio, 0 «calla»; en el censo los tres alertados son (6,6) a 302,95 K y 26,87 km y dos celdas a 275,3 y 273,4 K a 1,0 y 1,4 km de X0, Y0 | CONFIRMADO |
| 5 | MODIS: máscara de la vía igual al port «fisica» en 5.321 de 5.321; la reconstrucción reproduce `procesar_grilla` en 109 de 109 | `modis_salida.txt` | sólo 109 pasadas tienen alertados, así que 5.212 de las 5.321 son iguales por estar vacías; en las 109 mis reglas difieren de `comun.reglas` en 0 y del record en 0 | CONFIRMADO (el 5.321 cuenta vacías) |
| 6 | VIIRS 750: 5.640 evaluadas de 5.746, 106 fuera del gránulo; 93 / 177 / 5.370 / 0 | `v750_salida.txt` | `04`: idéntico; las 106 son todas `neg_limpio`; el oráculo guardó dos cajas (`geo_linear`, `geo_linear_anillo_sensible`) y la vía usa `def` = `geo_linear`, que `grillas_mirova.yaml` declara en los 11 | CONFIRMADO |
| 7 | VIIRS 750: cambia 1 con `cerc_cr` (Láscar 2026-08-26) y 2 con `cerc_ref` (más PP 2026-08-15, por el punto de medida, un solo píxel) | `v750_salida.txt` | `04`: ids 1892 y 4139, mismas distancias; PP: 1 píxel a 4,019 km del cráter y 2,25 de la celda (33,33); el cráter de PP está a 2,07 km de X0, Y0 (`01`), por eso el punto de medida decide | CONFIRMADO |
| 8 | VIIRS 750: la máscara es la del oráculo (sin grilla), igual a la de la vía según V750-A | SIN DATO declarado | V750-A se corrió al crear el módulo (`fb87ef554`); desde entonces `detectar_mirova` y `_pasada_contextual` cambiaron (parametrización por familia; diff `fb87ef554..origin/main`, 381 líneas); el guard que queda en `tests/test_mirova_v750_codigo_s162.py` cubre Etna y sintéticos, no las 510 grillas | SIN DATO (bien declarado) |
| 9 | VIIRS 375: 2.012 evaluadas, 66 sin resultado ok; 80 / 200 / 1.732 / 0 | `v375_salida.txt` | `02`: las 66 son 46 `neg_resto` fuera del gránulo y 20 `control_vida` del lote CTL (que no son pasadas del universo); ninguna alerta queda sin evaluar; `04`: 2.012 evaluadas, 329 con alertados | CONFIRMADO EN PARTE (el «66 SIN DATO» mezcla 20 controles con 46 pasadas) |
| 10 | VIIRS 375: cambian 8 de 2.012 (4 protegidas, 4 bajo 1 MW), iguales con `cerc_ref` y `cerc_cr`, control cruzado con V375-E `True` | `v375_salida.txt`, `v375_cambios.json` | `04` con reglas propias y el `pipeline/` de `main`: los mismos 8 ids, 0 diferencias contra `comun.reglas` en 329, 0 cruces sin cambio, 0 «calla» (§3) | CONFIRMADO |
| 11 | VIIRS 375 es una muestra estratificada sin pesos; los 8 no se extrapolan | texto | `02`: `pos_prot` 80 de 80 y `neg_pub` 133 de 133 son CENSO; `pos_bajo` 200 de 949 y `neg_resto` 1.599 de 3.323 son muestra. O sea que «4 de 80 protegidas» es un número de población (ventana abril a octubre sin los días excluidos), no de muestra; el informe lo trata igual que a las bajo 1 MW | CONFIRMADO EN PARTE (más fuerte de lo que dice para las protegidas) |
| 12 | En los tres sensores ningún cambio va en la dirección «calla» | las tres salidas | `03`: la cadena produce «calla» con `cerc_cr` (anillo de radio 8 celdas en Láscar: vía summit, cercano far, publica `True`/`False`) y con `cerc_ref` (píxel de PP a 2,79 km del cráter y 4,85 de X0, Y0): el cero NO es por construcción. `04`: 0 pasadas con la vía dentro y «cercano» fuera en MODIS y VIIRS 750 | CONFIRMADO (con nulo medido) |
| 13 | El almacén no cambió la `distance_class` de ninguna variante; el predicado responde a `distance_class` (`[True, False]`) | salidas | `03` repite el control; producción además pasa `volcano_lat/lon` (rechazo diurno, inocuo en censos nocturnos) y `volcanic_features` (sólo `geo_class`, que el tablero usa para el color, no para publicar: `frontend/index.html:3040-3048`) | CONFIRMADO |
| 14 | Referencia de hoy: consolidado `cb91eb5` (45.513 filas), OCR `cfc57c4` (1.160); pareo a 120 s | `referencia_salida.txt` | `VENTANA_S = 120` en `scripts/clase_mirova.py:112`; Mirova-v1 sigue commiteando cada 5 min (último visto `30d5bf06a`, 21:51 UTC), así que la copia está fijada por sha, bien | CONFIRMADO |
| 15 | Cotejo (a), las dos reglas dentro del inner: la tabla sigue al cúmulo radiante, 38 de 38 en VIIRS 375 y 3 de 3 en VIIRS 750 | `cotejo_por_configuracion_salida.txt` | leído el detalle en `v375.json` / `v750.json`: en VIIRS 375 `via_ref` queda a media celda de MIROVA en sólo 12 de 39 (mediana del error 0,46 km, más de una celda) y `cerc_ref` en 0; `pico_ref` del propio informe lo hace mejor (56 / 3, 20 a media celda). En VIIRS 750 las 3 son Chillán con MIROVA en 1,68 / 2,37 km y las dos reglas en 0,0 a 1,0 km: no calza ninguna, `via_ref` «gana» sólo porque `cerc_ref` es 0 | CONFIRMADO EN PARTE: «más cerca del centroide que del borde» sí; «sigue al cúmulo» no, la mejor descripción es el píxel más radiante, y el 3 de 3 no informa |
| 16 | Cotejo (b): 3 filas de la tabla en total; 2 dan distancia de cráter, 1 (MODIS) ubica la lejana a 26,87 km como `FALSO_POSITIVO`; las 7 OCR apuntan al cráter | salidas | reproducido en los JSON; A119: las 7 OCR son posteriores al 2026-06-13 (válidas); `FALSO_POSITIVO` es etiqueta del scraper por distancia (A54), o sea que MIROVA PUBLICÓ 11,31 MW a 26,87 km en `latest.php`: la lectura «como la vía» vale | CONFIRMADO (con la aclaración de la etiqueta) |
| 17 | SIN DATO: las clases no se recalcularon con la copia de hoy | texto | las 11 filas `mirova_hoy` de las salidas son coherentes con la clase del censo (p. ej. Isluga 228 protegida con OCR 1,64 MW; PP 4139 bajo1 con 0,09 MW) | CONFIRMADO |

## 2. Hallazgos propios

**H1 (gravedad 4). Los universos de VIIRS 750 y VIIRS 375 excluyen por construcción la configuración que decide.**
`poblacion_completa.json` de S159 (de donde salen los censos de VIIRS) sólo trae `neg_limpio` y `pos`: una pasada
cuya única fila de la tabla es `FALSO_POSITIVO` (MIROVA publicó una fuente lejana) no está. En MODIS esa clase existe
(`far_ref`, 10 pasadas) y es donde cayó el ÚNICO cambio. En la copia de hoy (`05_far_ref_fuera_del_universo_salida.txt`)
hay **338 pasadas nocturnas `FALSO_POSITIVO` en VIIRS 375** (distancia mediana 20 km; Láscar 57, Lastarria 57, Isluga 56,
PP 40, Tupungatito 38) y **19 en VIIRS 750**, contra 1.028 y 259 alertas. El «resto 0» de las dos tablas de VIIRS se
lee como «no hay pasadas de esa clase» y en realidad quiere decir «no se miraron». Lo que sí se puede decir: en
ninguna de esas 338 + 19 el OCR de la misma pasada trae una alerta a menos del inner (0 de 357), así que MIROVA no
resolvió el cráter en su imagen ahí; que NUESTRO detector tenga o no un píxel en el cráter en esas pasadas es SIN DATO
(no hay grillas). Cómo reproducirlo: `python 05_far_ref_fuera_del_universo.py`. Consecuencia para Nicolás: el 8 de
2.012 y el 1 de 5.640 son cotas inferiores del efecto de «cercano» en VIIRS; el único sensor con la clase cubierta es
MODIS.

**H2 (gravedad 2). El cotejo (a) no dice lo que el informe le hace decir.** «La distancia de MIROVA sigue al cúmulo
radiante» se apoya en que `via_ref` le gana a `cerc_ref` 38 a 0; pero `via_ref` calza a media celda con MIROVA en 12 de
39 y el error mediano es 0,46 km (1,2 celdas). El propio informe trae la fila que lo explica: `pico_ref` (la alertada
más radiante, no el centroide) gana 56 a 3 y calza a media celda en 20 de 59. Y en VIIRS 750 el «3 de 3» son tres
pasadas de Chillán donde MIROVA informa 1,68 y 2,37 km y las dos reglas dan 0,0 y 0,8 a 1,0 km: ninguna reproduce la
distancia de MIROVA (A61: eso pide mirar la posición, no el escalar). Reproducir: `python -c` sobre
`D:\vrp-trabajo\temporales\s165_regla_posicion\v375.json` y `v750.json`, clave `cotejo["via_ref|cerc_ref"]["CONS"]`.
No cambia el conteo de cambios; cambia la fuerza de la SOSPECHA sobre la regla de MIROVA.

**H3 (gravedad 2). «4 de 80 protegidas» en VIIRS 375 es un número de población, no de muestra.** `02`: las 80
protegidas de la población de S159 (ventana 2026-04-01 a 10-21 sin los seis días excluidos, lectura A) están todas
evaluadas, igual que las 133 `neg_pub`; la muestra es sólo en `pos_bajo` (200 de 949) y `neg_resto` (1.599 de 3.323).
El informe rebaja las cuatro protegidas a «muestra, no se extrapola» cuando son el censo.

**H4 (gravedad 1). Los «66 SIN DATO» de VIIRS 375 son 46 pasadas y 20 controles.** Los 20 `control_vida` del lote CTL
(ids 5000 a 5019) no son pasadas del universo y no tienen resultado en los tres lotes; las 46 restantes son `neg_resto`
con el volcán fuera del gránulo. Ninguna alerta quedó sin evaluar.

**H5 (gravedad 1). Etiqueta.** El informe dice que MIROVA «marca `FALSO_POSITIVO`» la pasada de Láscar MODIS. La marca
es del scraper (A54: filtrada por `limite_km`); lo que MIROVA hizo fue publicar 11,31 MW a 26,87 km. La lectura del
informe (MIROVA ubica la fuente lejana, como la vía) sigue en pie, con la autoría de la etiqueta corregida.

**Lo que busqué y NO encontré** (para que nadie lo repita): el punto desde donde mide la vía es el mismo de producción
(`get_detection_anchor` en los tres llamadores); la frontera `<=` es la de main; el predicado y el almacén responden a
`distance_class` en las dos direcciones (`03`); los cruces del inner que no cambian la publicación son 0 en MODIS y
VIIRS 750 (`04`), o sea que el predicado no esconde cambios; `inner_desde_html` coincide con `volcanoes.yaml` en los 11;
las 7 filas OCR de (b) son posteriores a la calibración del OCR (A119); el desfase cráter contra X0, Y0 es menor que el
inner en los 11 volcanes (`01`, máximo relativo PP 2,07 de 3 km), así que un píxel en el cráter nunca queda far por el
punto de medida.

## 3. Reproducción independiente (script 04)

Reglas reescritas (`ndimage.label` con estructura 3 x 3, semilla en el argmax de la radiancia, centroide y mínimo con
numpy), cotejadas con `comun.reglas` y con el record de `procesar_grilla` pasada por pasada, y la publicación por la
misma cadena del informe (validada en `03`).

| sensor | pasadas | con alertados | reglas propias contra `comun` | cambios `cerc_cr` | cambios `cerc_ref` | ids | cruces sin cambio | «calla» |
|---|---|---|---|---|---|---|---|---|
| MODIS | 5.321 | 109 | 0 difieren | 1 | 1 | 1563 | 0 | 0 |
| VIIRS 750 | 5.640 | 216 | 0 difieren | 1 | 2 | 1892, 4139 | 0 | 0 |
| VIIRS 375 | 2.012 | 329 | 0 difieren | 8 | 8 | 228, 233, 293, 298, 1570, 1638, 1647, 1662 | 0 | 0 |

VIIRS 375 corrió con el `pipeline/` de `main` (`bd711db63`, familia `VIIRS375` y `caja_v375` ya mergeadas por #921),
no con el worktree de V375-E que usó el autor, y da los mismos 8 ids y las mismas 329 pasadas con alertados: el cambio
de árbol no mueve nada. Salida completa: `04_reproduccion_independiente_salida.txt`; detalle por pasada en
`D:\vrp-trabajo\temporales\s165_regla_posicion_verif\04_detalle.json`.

## 4. Veredicto global

Los números que Nicolás va a usar (MODIS 1 de 5.321; VIIRS 750 1 por la regla y 2 con el punto de MIROVA, de 5.640;
VIIRS 375 8 de 2.012, 4 de ellas en el censo de protegidas) se reproducen con código independiente y el cero en la
dirección «calla» tiene nulo medido: son confiables PARA LOS UNIVERSOS MEDIDOS.
Lo que no son es completos en VIIRS: los dos universos excluyen por construcción las pasadas en que MIROVA publicó
una fuente lejana (338 nocturnas en VIIRS 375, 19 en VIIRS 750), que es la clase donde cayó el único cambio de MODIS;
ahí el efecto de «cercano» está SIN MEDIR y los conteos de VIIRS son cotas inferiores.
Del cotejo con `Distancia_km` vale lo de la configuración (b) (3 filas de la tabla, 2 a 1, no decide); la frase «MIROVA
sigue al cúmulo radiante» en (a) está sobredicha: lo que mejor calza es el píxel más radiante, y en Chillán no calza
ninguna de las dos reglas.
