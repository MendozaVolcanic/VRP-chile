# Fase 1 S146: verificación con contexto limpio del informe de sustrato

> Verificador independiente. No conocía el razonamiento del que midió: primero leí el código
> (`pipeline/process_viirs.py`, `process_modis.py`, `process_viirs_mod.py`, `pipeline/anchor.py`,
> `pipeline/clustering.py`, `pipeline/test1_integrated.py`, `pipeline/store.py`), los flags con
> `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`, el predicado de
> `frontend/index.html` y los records; recién entonces abrí
> `docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md`.
> Mis scripts: `experiments/_s146_fase1_sustrato/verificador/contra_medicion.py` y
> `.../subclase_t1_sobre_ctx.py`. Salidas: `contra_medicion.json`, `subclase_t1_sobre_ctx.json`.
> Sólo lectura. Ningún número de acá está transcrito a mano: cada uno va con su salida cruda.

## 0. Cómo ataqué cada afirmación

Enumeré por escrito los caminos por los que cada una podía estar mal, antes de medir:

1. Que la línea base no se reprodujera, o que el predicado no fuera el del dashboard.
2. Que el Test 1 sí entrara a la máscara por alguna rama que el informe no vio: el flag de retiro,
   la co-validación, el fondo, el `keep_peak`, o **la rama en que el primer pase no corre y la
   máscara queda en `combine_hot_paths`, que sí incluye `test1_hot`**.
3. Que el cero de `diag_n_bt_path` fuera un contador muerto y no un camino apagado.
4. Que "la fuente del cúmulo es `test1_roi`" no implicara "sin Test 1 no se publica": que el
   pipeline hubiera publicado igual un cúmulo contextual en esa pasada.
5. Que las 4 noches SIN DATO fueran pérdidas reales.
6. Que el resultado fuera de dos o tres volcanes (paradoja de Simpson).
7. Que los negativos limpios del final de la ventana estuvieran contaminados por el atraso del OCR.

## 1. El mecanismo, leído del código (esto es lo que decide los veredictos)

Lo verifiqué yo, línea por línea, y coincide con lo que dice el informe, con una salvedad que el
informe no menciona:

- `process_viirs.py` l. 1225-1233 arma `hot_mask_2d = combine_hot_paths(..., test1_hot=test1_hot, ...)`,
  o sea el Test 1 **sí** está en esa máscara. Pero la l. 1299 la **reemplaza entera** por `fp_hot`
  (primer pase, Tests 2 y 3) cuando corre el bloque de la l. 1242. Idéntico en
  `process_modis.py` l. 826 y 890, y en `process_viirs_mod.py` l. 810 y 878.
- **La salvedad**: si el bloque de la l. 1242 NO corre (falta I05, `inner_radius_km` None, `t_bg`
  NaN), la máscara se queda en la combinación, con el Test 1 adentro. Eso es un falsador real de la
  afirmación 2, y lo medí (sección 3).
- `clustering.py` l. 75-76: `cluster_hotspots` devuelve `[]` **sólo** si la máscara está vacía.
  De ahí sale mi eje independiente: primer pase + recaptura == 0 ⟺ no hay cúmulo contextual.
- `anchor.py` l. 79-89: la fuente `test1_roi` se emite **sólo** si no hay cúmulo contextual, o si lo
  hay pero su centroide está fuera del radio interno y el Test 1 pegó dentro.
- El Test 1 no toca el fondo ni el primer pase con los flags de hoy:
  `ENABLE_TEST1_K1_BG_EXCLUDE = False`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`
  (con ese último en False, `_test1_mask_for_fp = None`, l. 1268-1270),
  `ENABLE_TEST1_NTI_COVALIDATION = False`. `keep_peak` y el kernel de fondo actúan aguas abajo de
  `final_hotspot_source == "test1"`, no sobre la máscara contextual. Eso cierra el punto (b).
- `store.py` l. 363-367: el rescate de cúmulo **no** pisa las fuentes del ancla honesta
  (`ctx_cluster`, `test1_roi`, `test1_nti_peak`). Por eso en VIIRS no hay `cluster_rescue` y en
  MODIS (ancla honesta apagada) sí.

## 2. Afirmación 1: la línea base

Corrí el script del agente tal cual. Salida cruda de mi sesión (`scratchpad/rerun.txt`):

```json
{"identidad_predicado": true, "pub_identico_a_bp": true,
 "hoy_todo": {"MODIS": {"n_neg_limpio": 439, "tasa_pub_neg": 0.1139, "n_pos": 1},
 "VIIRS375": {"n_neg_limpio": 373, "tasa_pub_neg": 0.8633, "n_pos": 143},
 "VIIRS750": {"n_neg_limpio": 622, "tasa_pub_neg": 0.2138, "n_pos": 18}}}
```

`diff` contra la salida guardada del agente: **una sola línea distinta, el timestamp**. Todo lo demás
byte a byte igual. El predicado es el de `frontend/index.html` ejecutado con node
(`summit && valid && !art && disp > 0`), no un port a Python, y su control de identidad da `true`.

**CONFIRMADO. Gravedad 1.** El 0,114 de MODIS con n 439 (S145 tenía 438) es el corpus que creció,
no una discrepancia: al cortar por `processed_utc` de S145 vuelve a 0,1142 con n 438.

## 3. Afirmación 2: el Test 1 no entra a la máscara; los contadores legacy son diagnósticos

Medí el falsador que el informe no menciona, con el campo `diag_mu_dnti` como marca de "el primer
pase no corrió" (`process_viirs.py` l. 2142: sale de `fp_diag`, que es None si el bloque no corrió).
Salida cruda de `contra_medicion.py`:

```json
{"MODIS": {"n_pasadas": 457, "n_sin_first_pass": 0, "n_sin_first_pass_y_publicada": 0, "n_sin_first_pass_pub_y_test1": 0},
 "VIIRS375": {"n_pasadas": 954, "n_sin_first_pass": 5, "n_sin_first_pass_y_publicada": 0, "n_sin_first_pass_pub_y_test1": 0},
 "VIIRS750": {"n_pasadas": 949, "n_sin_first_pass": 0, "n_sin_first_pass_y_publicada": 0, "n_sin_first_pass_pub_y_test1": 0}}
```

Control C1 (si estuviera leyendo mal ese campo, fallaría): las 5 pasadas con `diag_mu_dnti` nulo
tienen `diag_n_first_pass_pixels == 0`, 0 incoherencias (`{"C1_sin_first_pass_n": 5,
"C1_incoherentes": 0, "C2_test1_source_sin_trigger": 0}`).

**CONFIRMADO CON MATIZ. Gravedad 1.** Hay una rama por la que el Test 1 sí entra a la máscara, y el
informe no la declara; pero son 5 de 2.360 pasadas y ninguna publica. No cambia nada.

## 4. Afirmación 3: el test de temperatura de brillo está apagado

`ENABLE_BT_PATH_HOT = False` leído de `pipeline.profile` con el perfil operacional (salida de mi
sesión, junto con `ENABLE_DUAL_ROI_BT = True`, que es lo que dice el YAML). Y busqué la ausencia con
la segunda herramienta que pide la regla: **todo el histórico, no la ventana**:

```json
{"campos_presentes": {"diag_n_bt_path": 60112, "n_bt_path": 47928}, "n_records_con_bt>0": {}}
```

**CONFIRMADO CON MATIZ. Gravedad 1.** El flag es la evidencia buena. El contador **no** lo es: nunca
fue mayor que cero en ningún record de ningún volcán de toda la historia del corpus, así que no puedo
distinguir "camino apagado" de "contador muerto" mirando datos. El informe presenta el cero del
contador como si confirmara el flag; en rigor el cero es **por construcción** (con el flag en False,
`bt_path_hot` es un array de ceros y el contador cuenta eso). La conclusión operativa del informe
("ese brazo de A/B tiene sustrato cero") **no** se ve afectada: se sostiene sola con el flag.

## 5. Afirmación 4: "sólo el Test 1 los sostiene"

Los conteos se reproducen exactos (186/322, 89/133, 8/50; banda 0,2145 a 0,3646). Lo que verifiqué es
si la atribución aguanta, porque **es una inferencia desde una etiqueta, no una simulación de la
etapa siguiente** (el propio informe lo declara en su sección 10, y el `docstring` del script dice
"por la LOGICA del codigo sobre campos persistidos (no por re-ejecucion)").

Mi eje independiente no usa la etiqueta: uso `primer pase + recaptura == 0`, que por
`clustering.py` l. 75-76 equivale a "no hay cúmulo contextual". Cruce con la clase del informe:

```json
{"VIIRS375": {"neg_limpio": {"n_pub": 322, "tabla": {"AMBOS|ctx_con_pixeles": 63,
  "CTX_SOLO|ctx_con_pixeles": 17, "T1_SOBRE_CTX|ctx_con_pixeles": 56,
  "T1_SOLO|ctx_con_pixeles": 28, "T1_SOLO|ctx_vacio": 158}}},
 "VIIRS750": {"neg_limpio": {"n_pub": 133, "tabla": {"AMBOS|ctx_con_pixeles": 9,
  "CTX_SOLO|ctx_con_pixeles": 24, "T1_SOBRE_CTX|ctx_con_pixeles": 11,
  "T1_SOLO|ctx_con_pixeles": 3, "T1_SOLO|ctx_vacio": 86}}},
 "MODIS": {"neg_limpio": {"n_pub": 50, "tabla": {"AMBOS|ctx_con_pixeles": 1,
  "CTX_SOLO|ctx_con_pixeles": 38, "RESCATE_SIN_DATO|ctx_con_pixeles": 3,
  "T1_SOLO|ctx_con_pixeles": 8}}}}
```

Dos caminos independientes coinciden: **158 de los 186** T1_SOLO de VIIRS 375 y **86 de los 89** de
VIIRS 750 tienen la máscara contextual **vacía**. Ahí "sin Test 1 no hay cúmulo, no hay píxeles y no
hay magnitud" no depende de la etiqueta: sale del código. Para esos, sin Test 1 el record queda con
`primary_cluster` nulo, `vrp_mw` 0 y `triggered_test1` False, y `isValidDetection` da falso.

Los 28 (V375) y 3 (V750) restantes dependen **sólo** de la lógica de `anchor.py`: la fuente
`test1_roi` con cúmulo presente exige que ese cúmulo esté fuera del radio interno, y entonces el
dashboard lo apaga por `pc.centroid_dist_km > innerKm` (l. 1060 de `index.html`). Es una deducción
correcta, pero de una sola fuente.

**CONFIRMADO CON MATIZ. Gravedad 2.** La atribución es sólida para el 85 % de los T1_SOLO de VIIRS
por dos caminos, y para el resto por uno. La banda 21,4 a 36,5 % sale de tratar T1_SOBRE_CTX (56),
el rescate y "otro" como SIN DATO: mínimo = CTX_SOLO + AMBOS = 80/373, máximo = 136/373. El supuesto
que separa los extremos es **si un cúmulo contextual que el Test 1 pisó habría publicado solo**, y el
VRP de ese cúmulo no se persiste. Ver la sección siguiente: ese supuesto está peor descrito de lo que
el informe cree, y la verdad probablemente esté más cerca del máximo.

## 6. Hallazgo propio: la subclase "rival débil" está mal atribuida

El informe divide T1_SOBRE_CTX en `fuente_unica` y `rival_debil_lt_0.01MW`, y dice que
"`rival_debil` significa que sin Test 1 la pasada se publicaría con menos de 0,01 MW o no se
publicaría". Pero `resolve_test1_source_priority` (`test1_integrated.py` l. 175-182) tiene **tres**
ramas, y la primera no exige rival débil:

```
if test1_summit_hit and eruption_far: return True      <- el cúmulo contextual puede ser fuerte
if only_test1_source: return True
if weak_cluster_enabled and test1_summit_hit and cluster_vrp < 0,01: return True
```

`eruption_far` es `hotspot_dist_km > inner_radius_km`, y `hotspot_dist_km` **sí** está persistido.
Medido (`subclase_t1_sobre_ctx.py`):

```json
{"VIIRS375": {"neg_limpio": {"n_T1_SOBRE_CTX": 56, "rama1_eruption_far": 5,
  "rama2_only_test1_source": 35, "rama1_sin_rama2": 5,
  "ni_rama1_ni_rama2_(=>rival_debil)": 16, "subclase_informe_rival_debil": 21},
 "pos": {"n_T1_SOBRE_CTX": 23, "rama1_eruption_far": 15, "rama2_only_test1_source": 3,
  "rama1_sin_rama2": 15, "ni_rama1_ni_rama2_(=>rival_debil)": 5,
  "subclase_informe_rival_debil": 20}},
 "VIIRS750": {"neg_limpio": {"n_T1_SOBRE_CTX": 11, "rama1_eruption_far": 2,
  "rama2_only_test1_source": 8, "rama1_sin_rama2": 2,
  "ni_rama1_ni_rama2_(=>rival_debil)": 1, "subclase_informe_rival_debil": 3}}}
```

El informe rotula 21 negativos como "rival débil" cuando sólo 16 lo exigen, y **20 de los 23
positivos** cuando 15 se explican por `eruption_far` con un cúmulo contextual que puede tener
magnitud real. **Gravedad 2.** No mueve ningún número de titular (T1_SOBRE_CTX es SIN DATO igual),
pero sí mueve la lectura: donde manda `eruption_far`, sin Test 1 el cúmulo contextual habría
publicado, o sea la verdad del contrafactual está más cerca de 36,5 % que de 21,4 %.

## 7. Afirmación 5: las 4 noches

Reproducido: 78 noches positivas, 78 publicadas hoy, 74 siguen seguro, 4 SIN DATO, 0 pérdidas
seguras. Miré las 4 pasada por pasada (`contra_medicion.json`, `noches_SIN_DATO_detalle`). Ejemplo,
Villarrica 2026-09-16: la pasada con alerta (V375 06:00) es T1_SOBRE_CTX con
`fp=0 sp=2 dnti_ctx=0 pc_vrp=0.105 pc_d=0.299`; con los cuatro contadores legacy en cero el Test 1
ganó por `only_test1_source`, así que sin él el cúmulo publicado sería el de los 2 píxeles de la
recaptura, con VRP desconocido. SIN DATO de verdad, no pérdida.

Pero el agregado por "cualquier sensor" tapa una pérdida segura que sí existe por sensor:

```json
{"VIIRS750": {"n_noches_pos": 14, "publicada_hoy": 13, "sinT1_sigue_publicada": 11,
  "sinT1_SIN_DATO": 1, "sinT1_se_pierde": 1, "no_publicada_hoy": 1}}
```

Es PCC 2026-09-07: en VIIRS 750 la única pasada publicada de esa noche es la de las 05:12
(`test1_roi`, `pc_vrp 0.45`); las otras cinco de ese sensor tienen `pc_vrp 0.0`. La noche sobrevive
en el agregado porque VIIRS 375 publica 0,098 a 0,536 MW y MODIS también. El informe lo declara
explícitamente en su línea 106, así que no es un número escondido.

**CONFIRMADO CON MATIZ. Gravedad 2.** La frase es cierta en la unidad declarada (la noche de volcán,
cualquier sensor). En la unidad por sensor, VIIRS 750 pierde con certeza 1 de sus 14 noches con
alerta. Si el criterio del A/B exige que la alerta se conserve **en el sensor en que MIROVA la
publicó**, esa noche cuenta como pérdida y hay que escribirlo en el criterio antes de correrlo.

## 8. Afirmación 6: MODIS

Reproducido exacto: de 50 negativos limpios publicados en MODIS, 38 son CTX_SOLO y 28 de ellos son
de PCC (`por_volcan_neg_limpio`, mi salida: `PuyehueCordonCaulle n_neg=46 n_pub=31 T1_SOLO=1
CTX_SOLO=28`). PCC concentra 31 de las 50 publicadas.

Dos matices propios sobre el 8 de T1_SOLO de MODIS, que el informe declara a medias:
- El rescate de `store.py` puede haber reetiquetado como `cluster_rescue` a records cuya fuente
  legacy era `test1` (3 casos) → el 8 es cota inferior. Eso el informe sí lo declara.
- En MODIS los 8 T1_SOLO tienen todos máscara contextual con píxeles, y **4 de 8 tienen
  `diag_n_first_pass_summit > 0`**, o sea había píxeles del primer pase dentro del radio interno
  (`{"MODIS": {"n_T1_SOLO_neg_pub": 8, "ctx_vacio": 0, "ctx_con_pixeles": 8,
  "ctx_con_pixeles_y_first_pass_summit>0": 4}}`). En la cascada legacy de MODIS eso es compatible con
  la rama de rival débil, donde sin Test 1 el cúmulo contextual cercano igual podría publicar. La
  inferencia T1_SOLO ⟹ no publica es **más floja en MODIS que en VIIRS**, y el informe no lo dice.

**CONFIRMADO. Gravedad 1** para la afirmación 6 tal como está escrita (es sobre CTX_SOLO y PCC, no
sobre el Test 1).

## 9. Los otros dos ataques

**(d) ¿Es de dos o tres volcanes?** No. Estratifiqué yo (mi salida, `por_volcan_neg_limpio`):
en VIIRS 375 T1_SOLO aparece en **los 11** volcanes, entre 1 y 39 pasadas
(Copahue 39, Villarrica 27, NdC 26, Llaima 26, PP 21, Chaitén 17, Lastarria 13, Láscar 8,
Tupungatito 6, PCC 2, Isluga 1). En VIIRS 750, en los 11 también (2 a 13). El patrón no es de un
volcán. Donde sí es de uno es en MODIS, y ahí lo que manda es el camino contextual (PCC).
El propio informe cuantificó la paradoja de Simpson con un nulo barajado dentro de cada volcán, y el
contraste de T1_SOLO en V375 queda fuera del intervalo (0,5637 contra 0,2506 a 0,3718). El nulo de
MODIS no tiene poder con 1 positivo, y el informe lo llama SIN DATO, que es lo correcto.

**(e) ¿Contaminan los negativos limpios del final?** No, y la premisa que me dieron está vencida: la
copia de referencia que usa el banco llega al **2026-09-19 06:24** en OCR y 2026-09-20 02:45 en CONS,
no al 14 de septiembre (que es hasta donde llega el snapshot del repo). Cortando por noche:

```json
{"2026-09-14": {"VIIRS375": {"n_neg": 287, "n_pub": 249, "tasa": 0.8676, "T1_SOLO": 147, "frac_T1_SOLO": 0.5904},
                "VIIRS750": {"n_neg": 487, "n_pub": 101, "tasa": 0.2074, "T1_SOLO": 74, "frac_T1_SOLO": 0.7327}},
 "2026-09-19": {"VIIRS375": {"n_neg": 373, "n_pub": 322, "tasa": 0.8633, "T1_SOLO": 186, "frac_T1_SOLO": 0.5776},
                "VIIRS750": {"n_neg": 622, "n_pub": 133, "tasa": 0.2138, "T1_SOLO": 89, "frac_T1_SOLO": 0.6692}}}
```

Mismo cuadro en los dos cortes. **Sin efecto medible.**

## 10. Error propio, para que no quede sin decir

En mi primera pasada usé `diag_n_first_pass_summit` para comprobar, en VIIRS, que los T1_SOLO con
píxeles contextuales no tenían ninguno dentro del radio interno. Me dio 0 de 28 y casi lo reporto
como confirmación independiente. **Ese campo no existe en los records VIIRS**: sólo en MODIS
(medido: `('MODIS','tiene_campo') 133`, `('V375','NO_tiene_campo') 277`,
`('V750','NO_tiene_campo') 276`). Mi `or 0` convertía la ausencia en un cero, y el cero se leía como
hallazgo. Es A89 exacta, cometida por el que verificaba. Lo corregí: para esos 28 la atribución
descansa sólo en la lógica de `anchor.py`, y así quedó escrito en la sección 5. En MODIS, donde el
campo sí existe, el mismo cruce dio 4 de 8 y es lo que me hizo bajarle la confianza al T1_SOLO de
ese sensor.

## 11. Tabla de veredictos

| # | afirmación | veredicto | gravedad |
|---|---|---|---|
| 1 | línea base 0,8633 / 0,2138 / 0,114 con el predicado en node | CONFIRMADO (reproducción byte a byte) | 1 |
| 2 | el Test 1 no entra a la máscara; los contadores legacy son diagnósticos | CONFIRMADO CON MATIZ (hay una rama sin primer pase: 5 pasadas, 0 publicadas) | 1 |
| 3 | el test de temperatura de brillo está apagado | CONFIRMADO CON MATIZ (lo prueba el flag, no el contador: ese cero es por construcción) | 1 |
| 4 | 186/322, 89/133, 8/50; sin Test 1 la tasa cae a 21,4 a 36,5 % | CONFIRMADO CON MATIZ (85 % por dos caminos; la banda es inferencia, y su lectura se corrige con §6) | 2 |
| 5 | 74 de 78 noches siguen, 4 SIN DATO, ninguna pérdida segura | CONFIRMADO CON MATIZ (cierto por noche de volcán; por sensor, V750 pierde 1 de 14) | 2 |
| 6 | en MODIS manda el contextual, 28 de 38 en PCC | CONFIRMADO | 1 |

Hallazgos propios, además de los matices: la subclase "rival débil" mal atribuida (§6), el T1_SOLO de
MODIS más flojo que el de VIIRS (§8), y mi propio cero vacuo (§10).

## 12. ¿Está justificado correr el A/B con el brazo "sin Test 1 integrado"?

**Sí.** No porque el informe lo haya probado (no lo probó: es inferencia sobre campos persistidos),
sino justamente porque lo que queda sin probar es grande y sólo una re-ejecución lo cierra. El
sustrato existe y no es de dos volcanes: 186 y 89 pasadas en los 11 Tier A. La cota inferior del
beneficio (86,3 % → 36,5 %, que es el extremo pesimista) ya sería el movimiento de paridad más
grande medido en el proyecto, y la cota superior del costo son 4 noches SIN DATO más 1 pérdida segura
en V750. Ningún número persistido puede reducir esa incertidumbre: el VRP del cúmulo contextual que
el Test 1 pisa **no se guarda en ningún campo** (lo verifiqué: cuando la fuente legacy es `test1`, el
pipeline sobrescribe `primary_cluster`, `anomaly_pixels` y `vrp_mir_mw`, y el snapshot
`ctx_cluster_anchor` se usa y se descarta).

Lo que el A/B tiene que medir, y que lo persistido no puede responder:

1. **El VRP y el centroide del cúmulo contextual en las 56 + 11 pasadas T1_SOBRE_CTX**, que es
   exactamente lo que separa el 21,4 % del 36,5 %. Sin esto el A/B confirma el titular pero no
   explica la banda.
2. **Las 4 noches SIN DATO, pasada por pasada, más PCC 2026-09-07 en V750**, con el criterio de
   recall escrito de antemano en las dos unidades: noche de volcán y noche del sensor en que MIROVA
   alertó. Sin esa segunda unidad, la pérdida segura de V750 desaparece por agregación.
3. **Que apagar el Test 1 no mueva nada aguas arriba.** Hoy es un argumento de flags
   (`ENABLE_TEST1_K1_BG_EXCLUDE`, `..._RETIRE_FROM_HOT_MASK`, `..._NTI_COVALIDATION` en False), no una
   medición. El control positivo del brazo de control debe reproducir el record persistido campo por
   campo (lo que el informe ya especifica en su sección 9, punto 4).
4. **Los 3 `cluster_rescue` de MODIS y los 8 T1_SOLO de MODIS**, donde la cascada legacy y el rescate
   hacen que la inferencia sea cota y no hecho.
5. **El nulo del brazo**: pasadas sin detección alguna no deben ganar publicación al apagar el Test 1
   (A110: un control se valida midiendo su nulo).

Y el brazo que **no** hay que correr es el de "sin test de temperatura de brillo": ya está apagado
por flag, y correrlo gastaría semanas para reproducir el control.

Una advertencia que no es sobre la medición sino sobre qué se hace con ella: A54 sigue en pie. Los
T1_SOLO de Villarrica y Copahue son en buena parte calor real que MIROVA no publica, y el Test 1 se
adoptó en S27 por eso mismo. El A/B mide paridad, no verdad física. Si el brazo gana, la salida
prudente es mudar ese camino al perfil `experimental`, no borrarlo, y esa es decisión de Nicolás.
