# Pre-registro S151 (tarea 1.7 del loop): la caja de 5 × 5 km (D18), medida por primera vez

> **VERSIÓN 2, SIN APROBAR, SIN DESPACHAR.** La versión 1 la revisó un verificador con contexto limpio: confirmó el
> cableado, el workflow, el sustrato, la prueba y la suite, y dijo "no vale la pena despachar V1 tal como está" por
> cuatro defectos (D1 a D4). La versión 2 los corrige (§10). Falta el "sí" de Nicolás (el candado
> `preregistro_aprobado` del workflow es suyo). Todos los números salen de los scripts de esta carpeta, con su salida
> al lado: `cableado_salida.txt`, `sustrato_salida.txt`, `prediccion_mirova_salida.txt`, `distancia_mirova_salida.txt`
> y `probar_salida.txt`.
>
> ⚠️ **Nota del 2026-10-15 (D-9, issue #811), posterior al sello; no cambia ningún criterio de este documento.**
> Nicolás decidió que las alertas del scraper de VIIRS 375 con VRP de 0,05 MW o menos (las que el banner de MIROVA
> llama NONE) cuenten como "MIROVA no vio nada" (regla SN), con SE y la regla original informadas. Este pre-registro
> se escribió antes: **decide con la regla original** (la etiqueta del scraper), tal como está escrito en §6 y §7.
> `evaluar_caja.py` ganó una sección 11 que INFORMA el veredicto de cada ventana con SN, SE, la original y las
> variantes con umbral 0,04 (0,05 exacto como alerta), y lo mismo en `--combinar`; marca "DISTINTO del que decide"
> cuando no coincide. El veto (P1) no depende de la etiqueta; lo que puede moverse es el mecanismo (Q1, Q2, P4), P2 y
> P3. Las salidas de los runs ya despachados se leen igual: el JSON conserva todas sus claves y suma `reglas_d9`.

## 1. El fenómeno, y la pregunta

**El fenómeno.** De noche, un píxel tibio cerca de un volcán puede ser lava, una fumarola de alta temperatura, o
nada: roca oscura sin nieve, el borde de una nube, ruido del sensor. MIROVA resuelve esa ambigüedad con dos
umbrales según el lugar. En una **caja de 5 × 5 km sobre la cumbre**, donde una fuente de calor es esperable, usa
el umbral permisivo (de noche C1 = 0,003 y C2 = 5); en todo lo demás, el estricto (C1 = 0,010 y C2 = 10),
"slightly higher thresholds which reduce false alerts" (Coppola et al. 2023, Front. Earth Sci. 11:1240107, p. 3;
la caja, Coppola 2016a p. 6). La réplica aplica el permisivo en un **círculo de `inner_radius_km`**, de 3 a 20 km
según el volcán (los radios del KML de MIROVA, que en MIROVA clasifican, no fijan umbrales). Es la divergencia D18.

**Hallazgo previo al A/B: desde dónde mide MIROVA, y cuánto publica fuera de su caja** (`distancia_mirova.py`).
- `Distancia_km` la calcula MIROVA (el scraper la copia de `latest.php`; Mirova-v1, `reconciliar_latest.py`) y es un
  desplazamiento en celdas enteras de su grilla (D15: 100 % de 10.085 filas MODIS y 11.810 VIIRS 375).
- **Se mide desde el centro de su grilla, no desde el cráter.** Donde el centro de grilla está lejos del cráter, las
  alertas se amontonan a esa distancia: en Tupungatito (centro a 4,86 km del cráter, D17) la mediana es 5,21 km y
  **34 de 40** alertas VIIRS 375 de V1 caen a menos de 1 km de 4,86 km, contra **0 de 40** a menos de 1 km de 0; en
  Puyehue Cordón Caulle (7,57 km) la mediana es 7,83 km, 38 de 50 contra 0; en Planchón Peteroa (2,02 km), 17 de 17
  contra 0. El calor está en el cráter y la distancia se cuenta desde el centro de grilla.
- **Dónde centra MIROVA su caja no se puede establecer con estos datos.** Coppola 2016a centra la grilla y la caja en
  lo mismo, "the volcano's summit", sin dar la coordenada. Dos lecturas, con su número (VIIRS 375):

| lectura | centro de la caja de MIROVA | V1, 11 volcanes, fuera de su caja | abril a octubre, tabla sola |
|---|---|---|---|
| **L1** | el centro de grilla (el mismo punto desde el que mide) | **82 de 330 (24,8 %)**, con las ambiguas de 2,5 a 3,54 km **95 (28,8 %)**; 80 de las 107 de Tupungatito, Puyehue Cordón Caulle y Planchón Peteroa | 268 de 941 (28,5 %) a 290 (30,8 %) |
| **L2** | el cráter | **9 de 330 (2,7 %)** fuera con seguridad (cota inferior por desigualdad triangular) | 4 de 941 (0,4 %) |
| las dos | en los **8 volcanes con el centro de grilla junto al cráter** | **5 de 223 (0,9 a 2,2 %)** | 27 de 600 como máximo (4,5 %) |

  En VIIRS 750, L1 da 12 de 47 en V1 (25,5 %) y L2 0; en MODIS, 0 de 8 con las dos.
- **Lo que esto significa.** La premisa "MIROVA calla fuera de la caja" **se sostiene en los 8 volcanes centrados y
  no se puede afirmar para los 11**. Si L1 es cierta, en Tupungatito y Puyehue Cordón Caulle el cráter queda **fuera**
  de la caja de MIROVA: MIROVA lo detecta con el umbral estricto y aun así publica ahí un cuarto de todas sus alertas
  VIIRS 375, y esas alertas no son más fuertes que las de adentro (mediana 0,14 MW contra 0,18 en V1; 0,18 contra
  0,17 de abril a octubre, `prediccion_mirova_salida.txt`), así que el umbral estricto no se nota en lo que publica
  (el VRP no es la variable del test: es una pista, no una prueba). Y nuestra caja, centrada en el cráter, haría lo
  contrario que la de MIROVA en esos volcanes: les daría el umbral permisivo. **Esto pesa más que el A/B**: para esos
  tres volcanes, ninguna caja centrada en el cráter puede acercar la réplica a MIROVA si L1 es cierta, y centrarla en
  el centro de grilla (`get_grid_center()`, D17) es tocar `pipeline/process_*.py` (A45). Por eso el A/B **decide sólo
  en los 8 centrados** (§7) y los otros tres se informan aparte.

**Qué hace hoy la réplica** (`sustrato.py`, 8 centrados, cúmulo publicado fuera de la caja). El brazo B (sin Test 1,
conectiva `min`) publica fuera de la caja el **25,6 %** de sus pasadas VIIRS 375 en lo que hay en disco de V1 (70 de
273; 50 de sus 89 negativos limpios) y el 20,0 % de abril a septiembre. El candidato F/K (sin Test 1, conectiva
`max`, banda 22 en MODIS) publica fuera **1,6 %** (2 de 128) y 1,5 % (16 de 1.086): **ya está en la banda de MIROVA**.

**La pregunta.** Con el Test 1 apagado (A114) y la caja en los dos pases (#738, A118): en los 8 volcanes donde la caja
del brazo coincide con la de MIROVA, ¿(a) la caja hace lo que el paper dice, y (b) sobre el candidato, pierde alguna
alerta protegida (criterio de victoria de `docs/MISSION.md`, lecturas A y B de `docs/S151_CRITERIO_CLASE_MIROVA.md`)?

**Lo que ya se midió de la caja, y por qué no vale.** S130 con el Test 1 encendido (A114); S148 con la caja sólo en
el primer pase (A118: 0 de 51 negativos cambiaron). La adenda S149 (`experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md`
§0) planeó repetir G y H en septiembre y nunca se despachó; este pre-registro la reemplaza.

## 2. ¿Llega el flag a todos sus consumidores? (`cableado.py`)

Tres caminos que no comparten supuestos:

1. **Flags efectivos** leídos de `pipeline.profile` con `VRP_PROFILE` de cada brazo (A89): los cuatro brazos tienen
   umbral dual en los dos pases, C1 0,003 contra 0,010 y C2 5 contra 10, ningún override, Test 1 apagado; K contra KC y
   B contra BC difieren **sólo** en `ENABLE_ROI1_BOX_PAPER`.
2. **Traza de llamadas por AST**: `_roi1_mask = roi_mask_bbox(lat, lon, vent_lat, vent_lon, ROI1_BOX_HALF_KM)` se arma
   bajo `if ENABLE_ROI1_BOX_PAPER` en los tres procesadores, y las **24 llamadas** a funciones de umbral dual (8 por
   procesador: primer pase, segundo pase, umbral de BT, dNTI dual) reciben la caja.
3. **Efecto con las funciones reales** (escena sintética de S148, máscara armada como en los procesadores): un píxel a
   3,38 km con un exceso entre los dos umbrales se publica con el círculo y no con la caja, con `min` y con `max`; uno
   a 1,5 km, en los dos casos.

**Respuesta: sí, a todo consumidor de umbral.** Los que siguen con el círculo no son umbrales y no deshacen la caja:

| consumidor | dónde | ¿necesita la caja? |
|---|---|---|
| etiqueta `distance_class` | `process_viirs.py:1808/2104`, `process_viirs_mod.py:1213/1392`, `process_modis.py:320` | No: el círculo es el radio del KML de MIROVA, que clasifica; la caja fija umbrales. Un píxel de la corona que pasa el umbral estricto es alerta también en MIROVA |
| gate del tablero | `frontend/index.html:1063/1067` | No, por lo mismo; es nuestro equivalente del límite del scraper, que también es `inner_radius_km` (control de `prediccion_mirova.py`) |
| selección del cúmulo | `clustering.py:150` | No: elige entre lo ya alertado |
| ancla honesta | `resolve_honest_anchor`; `process_modis.py:912` | No: posición, no umbral |
| magnitud | `store.py:559`, `f5_core.py:85`, `store.py:484/534` | No: cambia sólo por el conjunto de píxeles, que ya trae la caja |
| Test 1, gates intra-radio | | apagados en los cuatro brazos |

**No hay prerequisito A45 para medir la caja centrada en el cráter.** Faltaba la clave de la caja en la línea
`FLAGS_BRAZO` del workflow; este PR la agrega (como #794). **Sí lo habría para la caja de MIROVA bajo L1** en los tres
volcanes corridos (centrarla en el centro de grilla), y queda fuera de esta prueba (§9).

## 3. Brazos, y por qué cada uno

| brazo | perfil | dónde corre | por qué está |
|---|---|---|---|
| **B** | `_s146_ab_sin_test1` | V1 | control del mecanismo: aquí la caja tiene sustrato (43 negativos expuestos en los 8 centrados en lo que hay en disco de V1) |
| **BC** | `_s147_ab_sin_test1_caja` (existe desde S147, sin cambios) | V1 | B más la caja; lo que cambió desde S148 es el código (#738) |
| **K** | `_s149_ab_sin_test1_b22_max` | D1, D2 | el candidato vivo; la caja sólo puede actuar sin el Test 1 |
| **KC** | `_s151_ab_sin_test1_b22_max_caja` (nuevo, YAML de experimento) | D1, D2 | K más la caja |

**Por qué K y KC no corren en V1** (arreglos D2 y D3 del verificador). En los 8 centrados, la caja casi no tiene
dónde actuar sobre el candidato, y lo poco se cancela: de abril a septiembre, F en VIIRS 375 tiene **5 negativos
expuestos contra 4 Muy Bajo y 1 protegida expuestas** (la caja ganaría 5 y perdería 5); en VIIRS 750, 3 contra 1; en
MODIS, K tiene 0 contra 1 Muy Bajo y 1 protegida (`sustrato_salida.txt`, "CENTRADOS CONTRA CORRIDOS"). El techo de lo
que la caja puede mover la suma en 41 días es **3, 1 y 1 pasadas**. Además, P4 de KC ya se cumple sin la caja (K
publica fuera 1,6 %, bajo el techo de MIROVA de 5,1 %), y en V1 **ninguna protegida publicada por el candidato está
expuesta**, así que el veto en V1 no puede fallar por la caja. Ningún resultado de K contra KC en V1 cambiaría la
decisión; las dos únicas protegidas del candidato que la caja puede perder están fuera de V1 y se miden en D1 y D2.
**El gemelo de K salió con ellos** (y su perfil, del repo). El evaluador conserva las reglas de K, KC y KG en V1 con
los arreglos de ruido (§7) por si alguien los corre después; la prueba las ejercita.

## 4. Sustrato (`sustrato.py`)

**La cuenta.** Para cada pasada publicada, con la posición de cada píxel alertado: **intacta** si tiene al menos un
píxel dentro del círculo y de la caja (conserva el umbral permisivo y el cúmulo de la cumbre sobrevive);
**expuesta** si todo su calor del círculo cae en la corona (círculo menos caja): sólo ésas puede apagar la caja. Es un
**techo**: cuántas sobreviven al umbral estricto no se sabe sin el dNTI por píxel.

**Datos**: ramas de salida de los A/B ya corridos (`origin/s146-ab/<run>`, con `git show`): B y F de abril a
septiembre en los 11 volcanes, K en Láscar de marzo a junio, y C0, B, F y K de Chillán (run 38560317428). Referencia:
la congelada de V1 para septiembre y octubre; la unión del repo antes, con la tabla sola hasta el 2026-06-12 (A119).

**Controles, los cuatro pasan**: C1 la geometría reproduce el área teórica de la caja dentro del círculo en los 11
volcanes; C2 reproduce **los seis números** de S148 (`origen_43_de_135_salida.txt`), que con la caja centrada en la
coordenada nominal darían otros (43 de 135): puede fallar; C3 ningún píxel en caja menos círculo donde el radio es de
3,6 km o más; C4 el radio del tablero y el de `volcanoes.yaml` coinciden.

**Poder.**
- **Mecanismo (B contra BC, 8 centrados)**: en lo que hay en disco de V1, B publica 89 negativos limpios VIIRS 375, 43
  de ellos expuestos y el resto con calor en la caja; extrapolado a 41 días, unos 100 expuestos. Q1 compara dos proporciones
  de ese tamaño: tiene poder de sobra.
- **Veto (K contra KC)**: sin sustrato en V1. En seis meses hay **dos** protegidas expuestas del candidato, Láscar
  MODIS 2026-03-27 07:10 (1,0 MW, un píxel a 3,2 km del cráter) e Isluga VIIRS 375 2026-06-10 04:48 (2,15 MW, un píxel
  a 3,25 km), más la Muy Bajo MODIS de Láscar del 2026-03-14 (0,97 MW). Las dirigidas D1 y D2 son exactamente esas.
  Con dos casos, el veto detecta una pérdida si ocurre en ellos; no dice nada de una tasa.

## 5. Ventanas y despacho (no despachar sin el "sí" de Nicolás)

- **V1, 2026-08-29 a 2026-10-08**, 11 volcanes, **B y BC**: régimen de hoy (después de #535, A104), decide tabla y OCR
  (A119), con la misma referencia congelada que F y K (`experiments/_s151_prereg_fk_11/_congelado_v1`).
- **D1, 2026-03-14 a 2026-03-27, Láscar**, y **D2, 2026-06-10, Isluga**, K y KC. Antes del 2026-06-13: decide la
  tabla sola, con `_congelado_v2` de F y K (2026-03-01 a 06-12). Sin gemelo: una pérdida queda PENDIENTE DE
  REPETICIÓN y se repite el job una vez.

```
ONCE='["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]'
DOS='["_s149_ab_sin_test1_b22_max","_s151_ab_sin_test1_b22_max_caja"]'
gh workflow run reproc-s151-ab-caja.yml --ref main -f preregistro_aprobado=si -f start=2026-03-14 -f end=2026-03-27 -f vols='["Lascar"]' -f brazos="$DOS" -f control=_s149_ab_sin_test1_b22_max
gh workflow run reproc-s151-ab-caja.yml --ref main -f preregistro_aprobado=si -f start=2026-06-10 -f end=2026-06-10 -f vols='["Isluga"]' -f brazos="$DOS" -f control=_s149_ab_sin_test1_b22_max
gh workflow run reproc-s151-ab-caja.yml --ref main -f preregistro_aprobado=si -f start=2026-08-29 -f end=2026-10-08 -f vols="$ONCE" -f brazos='["_s146_ab_sin_test1","_s147_ab_sin_test1_caja"]' -f control=_s146_ab_sin_test1
```

**Cambio de infraestructura (S151, después de la aprobación D-8 del 2026-10-15, issue #801).** Los comandos de arriba
despachaban por `reproc-s146-ab-sin-test1.yml`; ahora van por `reproc-s151-ab-caja.yml`, copia de aquel con su propio
grupo de concurrencia. Ventanas, brazos, controles y criterio **no cambian**: el reproceso, la línea `FLAGS_BRAZO`, la
cuenta de cobertura y el guard son los mismos pasos. La razón es de cola: GitHub guarda un solo run pendiente por grupo,
y el grupo `s146-ab-sin-test1` lo ocupa el A/B de F y K (V1 corriendo, V2a pendiente); un despacho de la caja ahí
habría desplazado a V2a. Lo que sí cambia es dónde quedan las salidas: rama `s151-ab-caja/<run>`, con el árbol bajo
`experiments/_s151_prereg_caja/salidas/<run>/` (`<brazo>/<volcán>.json` y `logs/<brazo>_<volcán>.log`), y artefactos
`s151caja-*`. `evaluar_caja.py` no depende del nombre del workflow ni de la rama: se apunta con
`--raiz experiments/_s151_prereg_caja/salidas/<run> --logs experiments/_s151_prereg_caja/salidas/<run>/logs` sobre un
checkout de esa rama (o una copia de la carpeta).

**Desde `main` con este PR mergeado** (el perfil de KC y la línea de `FLAGS_BRAZO` tienen que estar en `main`; un run
despachado antes deja los brazos ROTOS por falta de la clave, y eso es lo correcto). Autentica sólo con
`EARTHDATA_TOKEN`. **Grupo de concurrencia**: `s151-ab-caja` corre uno a la vez y guarda **un solo run pendiente**: un
despacho nuevo desplaza al que espera, también entre D1, D2 y V1. El A/B de F y K va en su propio grupo
(`s146-ab-sin-test1`) y corre en paralelo, así que hay a lo más dos A/B vivos. Regla: antes de cada despacho,
`gh run list --workflow reproc-s151-ab-caja.yml --json status -q '[.[]|select(.status!="completed")]|length'` tiene
que dar **0**. Orden: D1 y D2 primero (son cortos y deciden el veto), V1 después.

**Duración** (`experiments/_s151_prereg_fk_11/duracion_runs_salida.txt`: 2,20 min por día de ventana y job sin Test 1;
el job más lento, 1,42 veces la mediana): D1, 2 jobs de ~31 min; D2, 2 jobs de minutos (**~35 min las dos**); V1, **22
jobs** de ~90 min (peor ~128, bajo el tope de 300 con el margen de A15), con 6 en paralelo **~6 h**. Total ~6,6 h de
grupo (la versión 1 pedía ~16 h).

## 6. Controles, antes de mirar ningún resultado (secciones 1 a 5 de `evaluar_caja.py`)

1. **Cobertura** (A108): las mismas pasadas en los brazos de cada despacho, toda protegida con record en todos, y el
   primer brazo contra producción (si en un volcán y sensor le falta más del 5 % de las pasadas de producción, la
   cobertura es corta; el 5 % es del instrumento, heredado, elegido). Si falla, INDECIDIBLE y se repite el job corto.
2. **Versión del producto**: ninguna protegida con versión distinta entre brazos.
3. **Cableado** de la línea `FLAGS_BRAZO` de cada job: perfil, directorio y los cinco flags declarados (Test 1,
   conectiva, banda 22, caja, semilado 2,5), más los de producción que traiga; **un log sin la clave de la caja es
   ROTO**; ningún record con `triggered_test1`.
4. **Huella de la caja** (A116, A118): BC tiene que tener **menos** píxeles alertados en la corona que B. Si no, la caja
   no actuó: mecanismo INDECIDIBLE y, antes de escribir nada, la traza por etapa de `experiments/_s148_caja_traza/`. Y
   como D1 y D2 corren el mismo código, **un mecanismo INDECIDIBLE deja INDECIDIBLE también el veto** (`--combinar`):
   un CUMPLE de KC sin prueba de que la caja actúa no vale.
5. **Referencia congelada** entera (sha256 LF de los CSV y de las capas contra el manifiesto).

## 7. Predicciones y reglas (secciones 6 a 10 de `evaluar_caja.py`, que las implementa tal cual)

Todo por pasada, por sensor, **en los 8 volcanes centrados**; Tupungatito, Puyehue Cordón Caulle y Planchón Peteroa se
imprimen aparte y no deciden. "Publica" es el predicado del tablero ejecutado con node (A97).

| # | qué | regla | predicción, y de dónde sale |
|---|---|---|---|
| **Q1** mecanismo | de los negativos limpios que B publica, los que BC apaga: los expuestos contra los que tienen calor en la caja | CUMPLE si la fracción apagada de los expuestos supera a la de adentro con la prueba exacta de Fisher a una cola, p < 0,05; FALLA si no; SIN SUSTRATO si un grupo está vacío. **El nulo es la tasa de cambio de lo de adentro, medida en el mismo run** (arreglo D4: la versión 1 exigía "la mitad o más", elegido; se sigue informando) | **CUMPLE**: el residual tiene exceso mínimo (mediana +0,31 K sobre su fondo, S147), su dNTI apenas pasa 0,003 y no debería pasar 0,010 |
| **Q2** control | de los negativos limpios de B con calor en la caja, los que BC cambia | CUMPLE con el 12 % o menos. **Umbral del instrumento, elegido** (heredado de S147, 5 de 42), sin nulo medido. FALLA deja todo INDECIDIBLE | CUMPLE |
| **P4** posición, contra MIROVA | fracción de publicaciones de BC con el cúmulo fuera de la caja | CUMPLE si no supera el Wilson superior al 95 % de lo que MIROVA tiene fuera de su caja en los 8 centrados en V1 (VIIRS 375: 5 de 223, **5,1 %**; VIIRS 750: 0 de 34; MODIS: 0 de 8) | **CUMPLE**: si la caja es lo que separa a MIROVA de B, el 25,6 % de B cae a la banda de MIROVA. Si BC queda sobre el 5,1 %, nuestro umbral estricto deja pasar más que el de MIROVA |
| **P1** veto, D1 y D2 | protegidas que K publica y KC no | VETADO con una pérdida que la repetición confirma; PENDIENTE DE REPETICIÓN sin repetición; CUMPLE con cero; SIN SUSTRATO si K no publica ninguna | **D2 (Isluga): CUMPLE**: MIROVA la ubica a 3,75 km de su centro de grilla (0,37 km del cráter): con L1 está fuera de su caja con cualquier acimut, o sea que la detectó con su umbral estricto; con L2 queda entre 3,38 y 4,12 km del cráter, probablemente fuera. **D1 (Láscar 03-27): sin predicción**: MIROVA la ubica a 1,41 km de su centro (dentro de su caja, umbral permisivo) y nuestro píxel MODIS cae a 3,2 km del cráter; si KC la pierde, la causa es la posición del píxel (D17), no la caja, y el veto la cuenta igual |

**Si alguien corre K, KC y KG en V1** (fuera de este despacho), el evaluador aplica además, en los 8 centrados:
- **Determinismo**: las pasadas discordantes K contra KG tienen que ser **menos que el techo** de §3 (3, 1 y 1). Con el
  98 % de la versión 1 se admitían unas 16 discordantes en 832 pasadas, el doble de lo que la caja puede mover.
- **P2 suma**: GANA si KC < K menos el ruido; PIERDE si KC > K más el ruido; EMPATE **sólo** si las sumas son iguales y
  el ruido es cero; **un cambio que no supera el ruido es INDECIDIBLE** (la versión 1 lo leía como "inerte").
- **P3 magnitud**, **sólo sobre los pares cuya magnitud cambia**: con todos los pares, la caja perfecta daba d = 0
  [0, 0] por construcción, y en la prueba un caso con 6 pares divididos por 20 da mediana 0,000 [0,0, 0,0] sobre los 22
  pares (CUMPLE falso) y FALLA sobre los 6 que cambian. Con menos de 5 pares que cambian, SIN SUSTRATO.
- El veredicto "inerte" sale sólo si las tres P2 son EMPATE exacto.

**Veredicto de KC por ventana y lectura** (`global_ventana`, en D1 y D2): controles o cableado fallidos, INDECIDIBLE;
una pérdida confirmada, NO CUMPLE (veto); una sin repetición, PENDIENTE DE REPETICIÓN; ninguna, CUMPLE (veto); K sin
protegidas publicadas, SIN SUSTRATO. **Mecanismo** (V1): LA CAJA ACTÚA (Q1 CUMPLE), LA CAJA NO APAGA (Q1 FALLA) o
INDECIDIBLE (sin huella o Q2 FALLA). **Final** (`--combinar v1.json d1.json d2.json`): el peor estado de D1 y D2 por
lectura, y INDECIDIBLE si el mecanismo de V1 no pasó su control (salvo un veto, que es definitivo).

**Predicción global**: KC **CUMPLE (veto)** con las dos lecturas y el mecanismo **LA CAJA ACTÚA** con P4 de BC en la
banda de MIROVA. Lo que se aprendería: la caja hace lo que el paper dice, sobre el candidato no cuesta las dos alertas
que podía costar, y no queda nada más que medirle en los 8 centrados porque `max` ya apagó esa población. Lo que no se
aprendería es qué hacer en los tres volcanes corridos: eso lo decide primero dónde centra MIROVA su caja (§1).

## 8. La prueba del evaluador (`probar_evaluar_caja.py`, salida en `probar_salida.txt`)

Brazos fabricados desde los records de producción de V1 (11 volcanes, `triggered_test1` en falso), la referencia
congelada de V1 y la línea `FLAGS_BRAZO` como la escribe el workflow con este PR. "Aplicar la caja" es quitar los
píxeles de la corona y apagar las pasadas expuestas: la caja perfectamente eficaz. Cada veredicto tiene un caso que lo
produce y otro que no:

- **Con el despacho de la versión 2**: `mec` (BC con la caja: sin veredicto de KC, LA CAJA ACTÚA con Fisher, Q2
  CUMPLE); `mec_nulo` (BC igual a B: sin huella, INDECIDIBLE); `noapaga` (corona quitada sin apagar: LA CAJA NO APAGA);
  `q2` (la caja toca lo de adentro: Q2 FALLA); D1 con CUMPLE, PENDIENTE, NO CUMPLE y CUMPLE con la repetición; y
  `combinar` (mecanismo y D1: CUMPLE (veto); mecanismo sin huella y D1: INDECIDIBLE; con un veto: NO CUMPLE).
- **Con K, KC y KG en V1**: `nulo`, `inerte` (EMPATE con ruido 0 y P3 SIN SUSTRATO porque ningún par cambia), `veto`,
  `gemelo`, `corrido` (una pérdida en un volcán corrido no decide), `gana` (y P2b fuera del techo), `pierde`,
  **`ruido_chico`** (KC cambia 1 dentro de un ruido de 2: INDECIDIBLE, no inerte), **`gana_ruido`** (5 contra ruido 1:
  GANA), **`ruido_grande`** (20 discordantes, no menos que el techo: determinismo FALLA), **`p3_cambian`** (6 pares
  divididos por 20: FALLA sólo con los pares que cambian), `p4`, y los controles `sinclave`, `cajafalsa`, `cobert`,
  `determ`, `capa_mod` y `log_real` (los logs reales del run 38560317428, sin la clave de la caja: K ROTO).

> ⚠️ **Nota del 2026-10-15 (D-9), posterior al sello**: la autoprueba ganó 3 comprobaciones de la sección 11
> informativa (el autocontrol de la regla original en `mec`, `d1` e `inerte`, y el caso `minimas`, donde decide PIERDE
> y la sección 11 informa SN GANA y SE EMPATE) y hoy da **32 de 32**; las 29 de antes siguen OK con las mismas líneas
> (`probar_salida.txt`). Texto original:

Resultado: **29 de 29**. Uso: `python probar_evaluar_caja.py <TMP> <DIR_NDC>`, con `<DIR_NDC>/logs` bajado de la rama
`s146-ab/38560317428`.

## 9. Lo que este A/B no puede decir

- **Si adoptar.** Eso es A45: verificador limpio sobre el resultado, tag defensivo y el "sí" de Nicolás. Y la caja sólo
  tiene sentido junto con K: sobre producción (Test 1 encendido) no tiene dónde actuar.
- **Dónde centra MIROVA su caja** (L1 o L2), y por lo tanto **nada sobre Tupungatito, Puyehue Cordón Caulle y
  Planchón Peteroa**. Para medir la caja de MIROVA bajo L1 hay que centrarla en el centro de grilla, que es código de
  `pipeline/process_*.py` (A45); antes conviene una prueba que distinga L1 de L2 (por ejemplo, si MIROVA alerta en la
  esquina de su grilla con la misma energía que en el centro).
- **La suma, la magnitud y la posición de KC sobre el candidato**: no se miden (§3); el sustrato las deja en un neto
  de cero a tres pasadas en los 8 centrados.
- **El veto como tasa**: son dos pasadas, no una muestra.
- **Cuál cúmulo es el de MIROVA**: P4 compara fracciones; `Distancia_km` no trae acimut (A93).
- **La dirección inversa** (caja menos círculo, donde la caja afloja): sólo en Lastarria y Planchón Peteroa; de abril a
  septiembre, B tiene 19 y 22 pasadas MODIS sin publicar con calor ahí (columna `rev` de `sustrato_salida.txt`).
- **Los otros 34 volcanes** no corren.

## 10. Qué cambió de la versión 1 a la 2 (verificador con contexto limpio del PR #800)

| defecto | cambio | dónde se ve |
|---|---|---|
| D1 (grave): el 0,9 a 2,2 % excluía los volcanes donde la distancia sí ubica la alerta respecto de la caja de MIROVA | `distancia_mirova.py`: la distancia se mide desde el centro de grilla (34 de 40, 38 de 50 y 17 de 17 alertas a la distancia centro-cráter); con los 11, 24,8 a 28,8 % fuera bajo L1 y 2,7 % bajo L2; la premisa vale sólo en los 8 centrados | §1, `distancia_mirova_salida.txt`, cabecera del perfil KC |
| D2: P2 lo decidía Puyehue Cordón Caulle, donde la caja del brazo está descentrada | todo decide en los 8 centrados; los 3 se informan aparte; techos recalculados (3, 1 y 1) | §3, §7, caso `corrido` |
| D3: veredictos casi seguros por construcción | P3 sólo sobre pares que cambian; dicho que P4 de KC ya se cumple y que el veto en V1 no tiene sustrato; K y KC salen de V1 | §3, §7, casos `inerte` y `p3_cambian` |
| D4: el ruido se leía como "inerte"; umbrales elegidos | cambio dentro del ruido es INDECIDIBLE; discordantes menos que el techo; Q1 por Fisher contra el nulo del propio run; Q2 marcado como umbral del instrumento | §7, casos `ruido_chico`, `gana_ruido`, `ruido_grande` |
| Despacho | D1 y D2 con K y KC (~35 min) y V1 sólo con B y BC (22 jobs, ~6 h); el perfil del gemelo sale del repo | §5 |
