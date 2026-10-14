# Pre-registro S151 (tarea 1.7 del loop): la caja de 5 × 5 km (D18), medida por primera vez

> **VERSIÓN 1, SIN APROBAR, SIN DESPACHAR.** Escrito y commiteado antes de correr ningún brazo. Falta el verificador
> con contexto limpio y el "sí" de Nicolás (el candado `preregistro_aprobado` del workflow es suyo). Todos los
> números salen de los scripts de esta carpeta, con su salida al lado: `cableado_salida.txt`,
> `sustrato_salida.txt`, `prediccion_mirova_salida.txt` y `probar_salida.txt`.

## 1. El fenómeno, y la pregunta

**El fenómeno.** De noche, un píxel tibio cerca de un volcán puede ser lava, una fumarola de alta temperatura, o
nada: roca oscura sin nieve, el borde de una nube, ruido del sensor. MIROVA resuelve esa ambigüedad con dos
umbrales según el lugar. En una **caja de 5 × 5 km sobre la cumbre**, donde una fuente de calor es esperable, usa
el umbral permisivo (de noche C1 = 0,003 y C2 = 5); en todo lo demás usa el estricto (C1 = 0,010 y C2 = 10),
"slightly higher thresholds which reduce false alerts" (Coppola et al. 2023, Front. Earth Sci. 11:1240107, p. 3;
la caja, Coppola 2016a p. 6). La réplica aplica el permisivo en un **círculo de `inner_radius_km`**, de 3 a 20 km
según el volcán (los radios del KML de MIROVA, que en MIROVA clasifican, no fijan umbrales). Es la divergencia D18.

**Qué dice la base de MIROVA** (`prediccion_mirova.py`, A115). Si MIROVA usa la caja, sus alertas tienen que caer
casi todas adentro: afuera sólo pasa calor fuerte. En V1, en los 8 volcanes cuyo punto de referencia de MIROVA es
el cráter, de 223 alertas VIIRS 375, **218 están a 2,5 km o menos** (dentro de la caja con cualquier acimut), 3
entre 2,5 y 3,54 km (depende del acimut, que el CSV no trae, A93) y 2 sobre 3,54 km (fuera con cualquier
acimut). VIIRS 750: 34 de 34 adentro; MODIS: 8 de 8. De abril a octubre, sólo la tabla: 573 de 600, 165 de 166 y
59 de 59. O sea, **entre 0,9 y 2,2 % de las alertas VIIRS 375 de MIROVA en V1 caen fuera de su caja**. El control
de ese script (que toda fila FALSO_POSITIVO del scraper esté sobre el límite de su volcán) falló en la primera
versión porque supuse 5 km para todos; Lastarria y Planchón Peteroa tienen 3: corregido, da 0 de 73 y 0 de 340.

**Qué hace hoy la réplica** (`sustrato.py`, mismos 8 volcanes, cúmulo publicado fuera de la caja). El brazo B
(sin Test 1, conectiva `min`) publica fuera de la caja el **25,6 %** de sus pasadas VIIRS 375 en lo que hay en
disco de V1 (70 de 273; 50 de sus 89 negativos limpios publicados), y el 20,0 % de abril a septiembre. El
candidato F/K (sin Test 1, conectiva `max`, banda 22 en MODIS) publica fuera **1,6 %** (2 de 128) y 1,5 % (16 de
1.086): **ya está en la banda de MIROVA**. La conectiva `max` y la caja atacan la misma población: el calor
débil de la corona, que con `max` ya no pasa.

**La pregunta.** Con el Test 1 apagado en el control (donde la palanca puede actuar, A114) y la caja en los dos
pases (#738, A118): ¿la caja acerca la réplica a MIROVA según el criterio de victoria de `docs/MISSION.md`
(ninguna alerta protegida perdida; bajo 1 MW, menor suma de alertas perdidas y publicaciones de más; en las dos
direcciones, por sensor, con recall, publicación en negativos limpios y razón de magnitud), con las dos lecturas
de alerta protegida de `docs/S151_CRITERIO_CLASE_MIROVA.md` (A por defecto, B pendiente en #782)?

**Lo que ya se midió de la caja, y por qué no vale.** S130 la cerró como NO ADOPTAR con el Test 1 encendido, que
publica por su cuenta y satura la métrica entre 80 y 92 % (A114). S148 la corrió sin Test 1, pero el flag sólo
llegaba al primer pase y el segundo recapturaba con el umbral permisivo (A118): 0 de 51 negativos cambiaron. La
adenda S149 al pre-registro de S147 (`experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md` §0) planeó repetir G y
H en septiembre y nunca se despachó. Este pre-registro la reemplaza: suma el criterio de victoria, el candidato K
como control, el gemelo, la referencia congelada de la unión y las dirigidas al veto.

## 2. ¿Llega el flag a todos sus consumidores? (`cableado.py`)

Tres caminos que no comparten supuestos:

1. **Flags efectivos** leídos de `pipeline.profile` con `VRP_PROFILE` de cada brazo (A89). Los cinco brazos tienen
   umbral dual en los dos pases (`ENABLE_DUAL_ROI_FIRST_PASS` y `ENABLE_DUAL_ROI_SECOND_PASS` en verdadero), C1
   0,003 contra 0,010 y C2 5 contra 10, ningún override que achique la diferencia, Test 1 apagado. K contra KC y B
   contra BC difieren **sólo** en `ENABLE_ROI1_BOX_PAPER`; K contra KG en nada.
2. **Traza de llamadas por AST** en los tres procesadores. `_roi1_mask = roi_mask_bbox(lat, lon, vent_lat,
   vent_lon, ROI1_BOX_HALF_KM)` se arma bajo `if ENABLE_ROI1_BOX_PAPER` en los tres. Las **24 llamadas** a
   funciones de umbral dual (`first_pass_tests_2_and_3`, `dual_roi_bt_threshold`,
   `dual_roi_contextual_dnti_hot_mask`, `second_pass_adjacent`), 8 por procesador, reciben la caja: por
   `roi1_mask=_roi1_mask` o por un `is_summit` armado con `roi1_summit_mask(..., _roi1_mask)`.
3. **Efecto con las funciones reales** sobre la escena sintética de S148, con la máscara armada como la arman hoy
   los procesadores: un píxel a 3,38 km (en el círculo de 5, fuera de la caja) con un exceso entre los dos
   umbrales se publica con el círculo y **no** con la caja, con `min` (exceso 0,006) y con `max` (0,015); uno
   idéntico a 1,5 km (dentro de la caja) se publica en los dos casos.

**Respuesta: sí, a todo consumidor de umbral.** Los consumidores que siguen con el círculo no son umbrales y,
uno por uno, no deshacen la caja:

| consumidor | dónde | qué hace con el círculo | ¿necesita la caja? |
|---|---|---|---|
| etiqueta `distance_class` | `process_viirs.py:1808/2104`, `process_viirs_mod.py:1213/1392`, `process_modis.py:320` | summit si el hotspot final cae en el círculo | No. El círculo es el radio del KML de MIROVA, que en MIROVA clasifica; la caja del paper fija umbrales, no qué se publica. Un píxel de la corona que pasa el umbral estricto es alerta en MIROVA también (Coppola 2023: el estricto existe para detectar coladas en los flancos) |
| gate del tablero | `frontend/index.html:1063/1067` (`mirovaEqVrp`) | publica si `distance_class` es summit y el cúmulo cae en el círculo | No, por lo mismo; es nuestro equivalente del límite del scraper, que también es el `inner_radius_km` (control de `prediccion_mirova.py`) |
| selección del cúmulo | `clustering.py:150` (`vent_anchored`) | prefiere cúmulos con centroide en el círculo | No: elige entre lo ya alertado, no vuelve a alertar nada |
| ancla honesta | `resolve_honest_anchor` en los tres; `process_modis.py:912` (semillas del primer pase en el círculo) | decide la posición publicada | No: posición, no umbral. Con la caja, menos semillas de la corona pasan, y eso se ve en P4 |
| magnitud | `store.py:559` y `f5_core.py:85` (núcleo VIIRS 375), `store.py:484/534` (reetiquetado A46, `geo_class`) | ancla el núcleo y etiqueta | No: la magnitud cambia sólo por el conjunto de píxeles, que ya trae la caja |
| Test 1, gates intra-radio | `process_viirs.py:1744`, `apply_*intra_radio_gate` | | Apagados en los cinco brazos |

**No hay prerequisito A45.** Lo único que faltaba era de instrumento, no de pipeline: la línea `FLAGS_BRAZO` del
workflow no traía la caja, así que el evaluador no podía probar el cableado desde el artefacto. Este PR agrega
`ENABLE_ROI1_BOX_PAPER` y `ROI1_BOX_HALF_KM` a esa línea (como hizo #794 con el ancla). La prueba del evaluador
lo confirma con los logs **reales** del run 38560317428: sin esa clave, el brazo sale ROTO.

**Límite declarado, que este A/B no toca.** La caja se centra en el ancla de detección (el cráter). MIROVA la
centra en el centro de **su** grilla, que según los TIF está a 4,78 km del cráter en Tupungatito, 7,58 en Puyehue
Cordón Caulle y 2,00 en Planchón Peteroa (S147; D15, D17). En esos tres la caja de este A/B no cae donde cae la de
MIROVA: P4 los excluye y Q1 los informa aparte en la lectura.

## 3. Brazos, y por qué cada uno

| brazo | perfil | qué es | por qué está |
|---|---|---|---|
| **K** | `_s149_ab_sin_test1_b22_max` | el candidato vivo | el control de la decisión. La caja sólo puede actuar sin el Test 1 (A114), y lo adoptable sin Test 1 es K (en VIIRS es F; en MODIS, F con banda 21 apaga el detector, S147). Si la caja no se mide sobre el candidato, no se mide sobre nada que se vaya a adoptar |
| **KC** | `_s151_ab_sin_test1_b22_max_caja` (nuevo, YAML de experimento) | K más la caja | el brazo |
| **KG** | `_s151_ab_sin_test1_b22_max_gemelo` (nuevo) | K otra vez | el efecto esperado es de pocas pasadas (§4): una sola pasada que cambie entre dos jobs idénticos fabricaría una "mejora". El ruido del brazo B se midió en S149/S150 (100 %), el de K no |
| **B** | `_s146_ab_sin_test1` | sin Test 1, conectiva `min` | control positivo de la palanca: aquí la caja tiene sustrato de sobra (55 negativos expuestos en 18 días). Si la caja no apaga nada en B, un cero en K no dice "inerte" sino "instrumento roto" (A116, A118) |
| **BC** | `_s147_ab_sin_test1_caja` (existe desde S147, sin cambios) | B más la caja | el mismo perfil del A/B de S148; lo que cambió es el código (#738) |

**Brazos que no están.** F y FC: en VIIRS son K y KC (la banda 22 sólo la lee `process_modis.py`). H (F más la
caja): es FC. El control de producción: con el Test 1 encendido la palanca no tiene dónde actuar (A114).

## 4. Sustrato: dónde puede actuar la caja (`sustrato.py`)

**La cuenta.** Para cada pasada publicada, con la posición de cada píxel alertado del record: **intacta** si tiene
al menos un píxel dentro del círculo y de la caja (ese píxel conserva el umbral permisivo, el cúmulo de la cumbre
sobrevive); **expuesta** si todo su calor del círculo cae en la corona (círculo menos caja): sólo ésas puede
apagar la caja. Es un **techo**: cuántas sobreviven al umbral estricto no se sabe sin el dNTI por píxel, que el
record no guarda (S130 pagó por confundir dónde cae con si sobrevive).

**Datos**: las ramas de salida de los A/B ya corridos (`origin/s146-ab/<run>`, leídas con `git show`): B y F de
abril a septiembre en los 11 volcanes, K en Láscar de marzo a junio, y C0, B, F y K de Chillán (run
38560317428). Referencia: la congelada de V1 para septiembre y octubre; la unión del repo antes, con la tabla sola
hasta el 2026-06-12 (A119).

**Controles, los cuatro pasan**: C1 la geometría reproduce el área teórica de la caja dentro del círculo en los 11
volcanes (por ejemplo 0,3170 contra 0,3183 con 5 km; Lastarria 0,8499 contra 0,8420, la diferencia es la de 111
km por grado contra el radio terrestre que el pipeline también usa); C2 reproduce **los seis números** de S148
(`origen_43_de_135_salida.txt`: VIIRS 375 0 de 135 y 58 de 105, VIIRS 750 1 de 13 y 21 de 36, MODIS 0 de 1 y 15
de 39), que con la caja centrada en la coordenada nominal darían 43 de 135: el control puede fallar; C3 ningún
píxel en caja-menos-círculo en volcanes con radio de 3,6 km o más; C4 el radio del tablero y el de
`volcanoes.yaml` coinciden.

**Lo que hay en disco de V1** (septiembre 1 a 18 en los 11, Chillán hasta el 10-07):

| brazo | sensor | negativos publicados | expuestos | Muy Bajo expuestas | protegidas expuestas (A / B) |
|---|---|---|---|---|---|
| B | VIIRS 375 | 119 | **55** | 0 | 0 / 1 |
| B | VIIRS 750 | 36 | **19** | 1 | 0 / 0 |
| B | MODIS | 36 | **11** | 0 | 0 / 0 |
| F (= K en VIIRS) | VIIRS 375 | 11 | **1** | 0 | 0 / 0 |
| F | VIIRS 750 | 3 | **0** | 1 | 0 / 0 |
| K | MODIS (sólo Chillán en disco) | 0 | 0 | 0 | 0 / 0 |

De abril a septiembre, F publica en VIIRS 375 **22 negativos expuestos** (4,4 por mes de abril a agosto) y 5 Muy
Bajo expuestas; en VIIRS 750, 13 y 2. Más de la mitad de lo expuesto de F es Puyehue Cordón Caulle.

**Poder.** (a) **El veto no tiene sustrato en V1**: ninguna protegida publicada por el candidato está expuesta, así
que la caja sólo podría perder una por un cambio de selección del cúmulo, que el A/B mide igual. En los seis meses
hay **dos** protegidas expuestas del candidato: Láscar MODIS 2026-03-27 07:10 (1,0 MW, un píxel a 3,2 km) e Isluga
VIIRS 375 2026-06-10 04:48 (2,15 MW, un píxel a 3,25 km), más 8 Muy Bajo expuestas. Por eso hay dos dirigidas (§5).
(b) **La suma**: el techo extrapolado a 41 días es de unas 8 pasadas en VIIRS 375 (6 negativos y 1 a 2 Muy Bajo),
4 en VIIRS 750 y 25 en MODIS (el techo de B; el de K fuera de Láscar no se conoce). Contra un control que en V1
publica unos 25 negativos limpios de VIIRS 375 en 41 días (11 en 18), la caja puede mover la suma del candidato
**a lo más un tercio**, y lo más probable es mucho menos. (c) **El mecanismo** (B contra BC) sí tiene poder: 55
negativos expuestos en 18 días, unos 125 en V1.

## 5. Ventanas y despacho (no despachar sin el "sí" de Nicolás)

- **V1, 2026-08-29 a 2026-10-08**, 11 volcanes, los cinco brazos. Régimen de hoy (después del 2026-08-28 23:00 UTC,
  #535, A104); posterior al 2026-06-13, así que decide tabla y OCR (A119), con las filas sólo del OCR de Suomi NPP
  como en el pre-registro de F y K (no deciden con la lectura A). Es la misma ventana y **la misma referencia
  congelada** que F y K (`experiments/_s151_prereg_fk_11/_congelado_v1`, con sus capas y manifiesto): los dos
  A/B quedan comparables y no se congela otra copia.
- **D1, 2026-03-14 a 2026-03-27, Láscar**, K y KC: la protegida MODIS expuesta del 03-27 y la Muy Bajo del 03-14.
  **D2, 2026-06-10, Isluga**, K y KC: la protegida VIIRS 375 expuesta. Las dos antes del 2026-06-13: decide la
  tabla sola, con la referencia congelada de V2 de F y K (`_congelado_v2`, 2026-03-01 a 06-12). Sin gemelo: una
  pérdida queda PENDIENTE DE REPETICIÓN y se repite el job una vez (mismo camino que F y K, §5 de su pre-registro).
  Las dirigidas sólo tienen veto: no hay suma ni magnitud que leer en 14 días de un volcán.

```
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
CINCO='["_s149_ab_sin_test1_b22_max","_s151_ab_sin_test1_b22_max_caja","_s151_ab_sin_test1_b22_max_gemelo","_s146_ab_sin_test1","_s147_ab_sin_test1_caja"]'
DOS='["_s149_ab_sin_test1_b22_max","_s151_ab_sin_test1_b22_max_caja"]'
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-08-29 -f end=2026-10-08 -f vols="$ONCE" -f brazos="$CINCO" -f control=_s149_ab_sin_test1_b22_max
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-03-14 -f end=2026-03-27 -f vols='["Lascar"]' -f brazos="$DOS" -f control=_s149_ab_sin_test1_b22_max
gh workflow run reproc-s146-ab-sin-test1.yml --ref main -f preregistro_aprobado=si -f start=2026-06-10 -f end=2026-06-10 -f vols='["Isluga"]' -f brazos="$DOS" -f control=_s149_ab_sin_test1_b22_max
```

**Desde `main` con este PR mergeado** (los dos perfiles nuevos y la línea de `FLAGS_BRAZO` tienen que estar en
`main`; un run despachado antes deja todos los brazos ROTOS por falta de la clave, y eso es lo correcto).
Autentica sólo con `EARTHDATA_TOKEN`. **Grupo de concurrencia**: `s146-ab-sin-test1` corre uno a la vez y GitHub
guarda **un solo run pendiente**: un despacho nuevo desplaza al que espera. El A/B de F y K (tres despachos, unas
28 h, espera su sello en #798) comparte el grupo. Regla: antes de cada despacho,
`gh run list --workflow reproc-s146-ab-sin-test1.yml --json status -q '[.[]|select(.status!="completed")]|length'`
tiene que dar **0**; así ningún despacho desplaza a otro, venga de este pre-registro o del de F y K, y nunca hay
más de dos A/B vivos. El orden entre los dos pre-registros lo decide el que se selle primero.

**Duración** (de `experiments/_s151_prereg_fk_11/duracion_runs_salida.txt`: 2,20 min por día de ventana y job sin
Test 1, el job más lento 1,42 veces la mediana): V1, 55 jobs de ~90 min (peor ~128, bajo el tope de 300 con el
margen de A15), con 6 en paralelo **~15 h**; D1, 2 jobs de ~31 min; D2, 2 jobs de minutos. Total ~16 h de grupo.

## 6. Controles, antes de mirar ningún resultado (secciones 1 a 5 de `evaluar_caja.py`)

1. **Cobertura** (A108): las mismas pasadas en los brazos, toda protegida con record en todos, y K contra
   producción (`data/mirova_equivalent/`): si en un volcán y sensor a K le falta más del 5 % de las pasadas que
   producción tiene, cobertura corta (el 5 % es del instrumento, heredado, elegido). Si falla, INDECIDIBLE y se
   repite el job corto con el mismo código.
2. **Versión del producto**: ninguna protegida con versión distinta entre brazos.
3. **Cableado**, de la línea `FLAGS_BRAZO` de **cada** job: perfil, directorio y los cinco flags declarados (Test 1,
   conectiva, banda 22, caja, semilado 2,5), más los de producción que el log traiga; **un log sin la clave de la
   caja es ROTO**; y ningún record con `triggered_test1`.
4. **Huella de la caja en los records** (A116, A118): BC tiene que tener **menos** píxeles alertados en la corona
   que B. Si no, la caja no actuó: todo INDECIDIBLE y, antes de escribir nada, la traza por etapa de
   `experiments/_s148_caja_traza/`. La de KC contra K se informa (puede no tener sustrato).
5. **Determinismo**: KG contra K, misma decisión de publicar en 98 de cada 100 pasadas o más, por sensor (umbral
   heredado de S149 y S150). Y la **referencia** es la congelada, entera (sha256 LF de los CSV y de las capas).
6. **Q2, control interno del mecanismo**: de los negativos limpios que B publica con calor **dentro** de la caja,
   BC cambia la publicación en el 12 % o menos (heredado de S147, 5 de 42: elegido, no medido). La caja no
   debería tocar lo que está adentro; si lo toca, el resultado no se interpreta.

## 7. Predicciones y reglas (secciones 6 a 10 de `evaluar_caja.py`, que las implementa tal cual)

Todo por pasada, por sensor y por lectura (A y B), contra K. "Publica" es el predicado del tablero ejecutado con
node (A97). Alerta protegida: `scripts/clase_mirova.alerta_protegida`.

| # | qué | regla | predicción, y de dónde sale |
|---|---|---|---|
| **P1** veto | protegidas que K publica y KC no | VETADO con una pérdida neta; INDECIDIBLE si sólo hay ruidosas (KG también cambia); PENDIENTE DE REPETICIÓN sin gemelo (D1, D2); CUMPLE con cero o todas descartadas por la repetición; SIN SUSTRATO si K no publica ninguna | **V1: CUMPLE** con las dos lecturas (cero protegidas expuestas en disco). **D2 (Isluga): CUMPLE**: MIROVA alertó esa pasada a 3,75 km, fuera de su propia caja con cualquier acimut, o sea que la detectó con su umbral estricto. **D1 (Láscar 03-27): sin predicción**: MIROVA la ubica a 1,41 km (dentro de su caja, umbral permisivo) y nuestro píxel MODIS cae a 3,2 km; si KC la pierde, la causa es la posición del píxel (D17), no la caja, y el veto la cuenta igual |
| **P2** suma bajo 1 MW | Muy Bajo perdidas + publicaciones en negativos limpios; ruido = pasadas discordantes K contra KG | GANA si KC < K − ruido; PIERDE si KC > K + ruido; si no, EMPATE | **VIIRS 375: GANA por 1 a 8 pasadas**; VIIRS 750: EMPATE o GANA por 4 o menos; MODIS: sin predicción (el sustrato de K fuera de Láscar no se conoce) |
| P2b techo (informa) | \|suma KC − suma K\| contra el techo de §4 (8, 4 y 25) | DENTRO o FUERA | **DENTRO** en los tres. FUERA quiere decir que la caja actúa por un camino que el sustrato no ve (selección del cúmulo, píxeles que no están en el record) y se traza antes de leer |
| **P3** magnitud | d = \|log10(KC/MIROVA)\| − \|log10(K/MIROVA)\| en alertas que publican los dos; ruido = mediana de d del gemelo | FALLA si el intervalo bootstrap al 95 % de la mediana de d queda sobre 0 **y** la mediana supera el ruido; con menos de 5 pares, SIN SUSTRATO | **CUMPLE** (7 Muy Bajo de F en disco tienen calor dentro y fuera de la caja, todas de Puyehue Cordón Caulle) |
| **P4** posición, contra MIROVA | fracción de publicaciones con el cúmulo fuera de la caja, 8 volcanes centrados | CUMPLE si no supera el Wilson superior al 95 % de lo que MIROVA tiene fuera de su caja en V1 (VIIRS 375: 5 de 223, **5,1 %**; VIIRS 750: 0 de 34; MODIS: 0 de 8) | **KC CUMPLE** (K ya está en 1,6 %). **BC CUMPLE**: si la caja es lo que separa a MIROVA de B, la fracción de B (25,6 %) cae a la de MIROVA. Si BC queda sobre el 5,1 %, nuestro umbral estricto deja pasar más que el de MIROVA y la caja no basta |
| **Q1** mecanismo | negativos limpios expuestos que B publica: los que BC apaga | CUMPLE con la mitad o más (la regla Q1 de S147); FALLA si menos; SIN SUSTRATO si no hay | **CUMPLE**: el residual tiene exceso mínimo (mediana +0,31 K sobre su fondo, S147), su dNTI apenas pasa 0,003 y no debería pasar 0,010 |

**Veredicto de KC por ventana y lectura** (`global_ventana`), en este orden: controles o cableado de K, KC o KG
fallidos, INDECIDIBLE; sin huella en BC o Q2 FALLA, INDECIDIBLE (el control positivo no pasó); un P1 VETADO, NO
CUMPLE (veto); un P1, P2 o P3 INDECIDIBLE, INDECIDIBLE; un P1 PENDIENTE, PENDIENTE DE REPETICIÓN; un P2 PIERDE, NO
CUMPLE (suma); ningún P2 GANA, **NO CUMPLE (no mejora el criterio: la caja es inerte sobre el candidato)**; si no,
CUMPLE, que se degrada a "CUMPLE EN DETECCIÓN, FALLA EN MAGNITUD (decide Nicolás)" con un P3 FALLA, y anota "veto
sin sustrato" y "publica fuera de la caja más que MIROVA (P4)" cuando corresponde. En D1 y D2 sólo el veto.
**Final** (`--combinar`): el peor estado de V1, D1 y D2, por lectura (NO CUMPLE por veto, NO CUMPLE por suma,
INDECIDIBLE, PENDIENTE, NO CUMPLE por inerte, CUMPLE EN DETECCIÓN, CUMPLE). **Mecanismo** aparte: LA CAJA ACTÚA
(Q1 CUMPLE), LA CAJA NO APAGA (Q1 FALLA) o INDECIDIBLE.

**Predicción global**: KC **CUMPLE por un margen chico** (entre 1 y 10 pasadas sumando los tres sensores) en las
dos lecturas, y el mecanismo **LA CAJA ACTÚA**. Lo que se aprendería: la caja hace lo que el paper dice, pero sobre
el candidato casi no queda qué hacerle, porque `max` ya apagó esa misma población. Si en vez de eso KC sale
"inerte", la conclusión es la misma con otro número; si sale VETADO, la caja cuesta una alerta y no se adopta.

## 8. La prueba del evaluador (`probar_evaluar_caja.py`, salida en `probar_salida.txt`)

Brazos fabricados desde los records de producción de V1 (11 volcanes, `triggered_test1` en falso), la referencia
congelada de V1 y la línea `FLAGS_BRAZO` como la escribe el workflow con este PR. "Aplicar la caja" a un brazo
fabricado es quitarle los píxeles de la corona y apagar las pasadas expuestas: la caja perfectamente eficaz.
Cada veredicto tiene un caso que lo produce y otro que no:

- **nulo** (cinco brazos idénticos): sin huella en BC, global INDECIDIBLE. Un brazo igual a su control no puede
  pasar por una caja que no hace nada.
- **efectiva**: controles y huella OK, Q1 y Q2 CUMPLE, LA CAJA ACTÚA; P1 y P2 los que dicta la base, calculados
  por otro camino (la base de producción tiene 6 protegidas VIIRS 375 expuestas: sale VETADO, como debe).
- **inerte** (KC igual a K, BC con la caja): NO CUMPLE (inerte), mecanismo ACTÚA, P2 EMPATE en los tres sensores.
- **veto**, **gemelo**: VETADO; INDECIDIBLE si KG también la oculta. **gana**, **pierde**, **empate** (10 contra 20
  discordantes), **magnitud** (VIIRS 750 por 20: FALLA EN MAGNITUD), **p4** (cúmulos corridos 4 km: P4 FALLA y el
  global lo anota), **noapaga** (corona quitada sin apagar: LA CAJA NO APAGA), **q2** (la caja apaga también lo de
  adentro: Q2 FALLA, INDECIDIBLE).
- **Controles**: log sin la clave de la caja, ROTO; log con la caja apagada, ROTO; una pasada de menos, cobertura
  despareja; gemelo distinto en 100 pasadas, determinismo FALLA; capa histórica alterada, referencia_ok falso.
- **Dirigida D1**: K y KC iguales, CUMPLE (veto); KC pierde una protegida MODIS, PENDIENTE DE REPETICIÓN; la
  repetición la vuelve a perder, NO CUMPLE (veto); no la pierde, CUMPLE (veto).
- **Logs reales** del run 38560317428 (workflow sin la clave de la caja): K ROTO, INDECIDIBLE.
- **Combinar** inerte, D1 y veto: NO CUMPLE (veto); inerte y D1: NO CUMPLE (no mejora).

Resultado: **28 de 28**. Dos fallas de la primera corrida eran de la prueba, no del evaluador, y quedan dichas en
el código: la semilla de D1 (la pasada del 03-27) no está publicada en los records de producción, así que el caso
no probaba nada; y ocultar una pasada sólo con la etiqueta `far` no la despublica en MODIS (el tablero la acepta
por el cúmulo), así que ahora también se lleva a cero la magnitud del cúmulo. Uso:
`python probar_evaluar_caja.py <TMP> <DIR_NDC>`, con `<DIR_NDC>/logs` bajado de la rama `s146-ab/38560317428`.

## 9. Lo que este A/B no puede decir

- **Si adoptar.** Eso es A45: verificador limpio sobre el resultado, tag defensivo y el "sí" de Nicolás. Y la caja
  sólo tiene sentido junto con K: sobre producción (Test 1 encendido) no tiene dónde actuar.
- **El veto en V1**: sin sustrato de exposición. Lo que el veto puede decir viene de dos pasadas dirigidas.
- **La caja de MIROVA en Tupungatito, Puyehue Cordón Caulle y Planchón Peteroa**: centrada en otro punto (§2).
- **Cuál cúmulo es el de MIROVA**: P4 compara fracciones, no pasadas; `Distancia_km` no trae acimut (A93).
- **K en MODIS fuera de Láscar**: no hay datos previos; P2 en MODIS no tiene predicción.
- **La dirección inversa** (caja menos círculo, donde la caja afloja): sólo existe en Lastarria y Planchón
  Peteroa, y un cúmulo a más de 3 km queda fuera del gate del tablero; de abril a septiembre, B tiene 19 y 22
  pasadas MODIS sin publicar con calor ahí (columna `rev` de `sustrato_salida.txt`). Si KC publica alguna nueva de esas, se ve como recuperada en P1 o como cambio en P2.
- **El borde de 0,05 MW y la simetría en logaritmo de P3**: los mismos límites del pre-registro de F y K (§8 allá).
- **Los otros 34 volcanes** no corren.
