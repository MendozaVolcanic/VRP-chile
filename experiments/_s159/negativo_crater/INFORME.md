# S159, frente «negativo limpio con el cráter visto»

Fecha 2026-10-21. Sólo lectura: ningún archivo del repositorio se tocó fuera de esta carpeta.

## 0. Regla declarada ANTES de mirar el efecto (escrita a las 2026-10-21, antes de correr `medir.py`)

**Fenómeno.** De noche el satélite barre el volcán en franjas (gránulos) de 5 min (MODIS) o 6 min (VIIRS). Cuando
el ROI de 25 km cae en el límite entre dos gránulos de la misma órbita, procesamos los dos y MIROVA lista uno solo
(casi siempre el del sur). Si el cráter quedó en el otro, la fila RUTINA de MIROVA no dice «miré y no había nada»,
dice «no miré el cráter». Esa fila no debería contar como negativo limpio.

**Indicador (heredado del frente de pareo, sin copiar sus números).** `diag_n_bg_anillo` de cada record: píxeles
del anillo de fondo (5 a 25 km) que cayeron en ese gránulo. El anillo es simétrico respecto del cráter, así que el
miembro con la mitad o más del anillo de la pasada es el que tiene el cráter. Fracción f(r) = nbg(r) / (nbg(r) +
nbg(compañero)).

**Cadena.** Records nuestros del mismo volcán y la misma plataforma (campo `sensor`) separados exactamente 5 min
(MODIS) o 6 min (VIIRS). Una pasada «partida» es una cadena de dos.

**Regla NLC (negativo limpio con cráter).** Un record etiquetado `neg_limpio` por `banco_paridad.etiquetar` (sin
tocar el etiquetador, con la regla D-9 que use cada número que corrijo) sigue siendo negativo limpio sólo si el
gránulo que MIROVA listó contiene el cráter:

1. Si la fila de MIROVA es del mismo gránulo que el record (pareo de ±120 s, el de hoy):
   - record en cadena de dos con nbg total > 0: contiene el cráter si f(r) ≥ 0,5;
   - record en cadena de dos con nbg total = 0: «indeterminado», se queda (se cuenta aparte);
   - record solo (sin compañero): se queda (el indicador no dice nada; límite declarado, ver N-8 de Chaitén).
2. Si la fila de MIROVA es del gránulo vecino (sólo pasa con un pareo más ancho que ±120 s, p. ej. el de órbita
   o el de 8 min de R2.3): contiene el cráter si tenemos el record de ese gránulo y su f ≥ 0,5; si no lo tenemos
   (record nuestro solo), el cráter está en el nuestro, no en el de MIROVA, y la pasada sale.

Los que salen van a un estrato «MIROVA sin cráter»: ni positivo ni negativo; sus publicaciones (las del record
de MIROVA y las del compañero) se informan aparte.

**Por qué 0,5 y no otro corte (A115).** El 0,5 sale de la geometría (anillo simétrico), no de un gusto. Se
contrasta contra la propia referencia: si es el corte correcto, la tasa de alerta de MIROVA por tramo de f, en
pasadas partidas con un solo gránulo listado, tiene que saltar en 0,5 (debajo, MIROVA no ve el cráter). Se mide en
`medir.py` §1 antes de usar el corte; si el salto no está en 0,5 se dice y se usa el que dé la referencia.
Sensibilidad: cortes 0,4 y 0,6 (el indicador acierta ~94 % contra la posición del cúmulo según el verificador del
pareo; lo re-mido).

**Controles fijados de antemano.**
- Positivo 1 (del coordinador): Chillán MODIS Terra 2026-01-19 02:40. Predicción: con el pareo de ±120 s NO es
  negativo hoy (MIROVA listó 02:35, gránulo que no tenemos: el record es `sin_info`); con un pareo de ±390 s sí es
  negativo con la definición vieja y la regla 2 lo saca. Si con ±120 s fuera negativo, la predicción falla y lo digo.
- Positivo 2: Isluga VIIRS 375 2026-02-04 05:54 (negativo de hoy con f = 0 según el frente de pareo) tiene que salir.
- Positivo 3 (independiente del indicador): los dos negativos de Chaitén V750 de N-8 (2026-06-30 06:12 y 2026-05-15
  04:24), cuyo píxel más cercano al volcán está a 10,4 y 23,5 km según la medición por red de N; si están en cadena
  de dos tienen que salir.
- Nulo: las pasadas enteras (records solos) se quedan todas; si el campo `diag_n_bg_anillo` estuviera muerto (0 en
  todos), no saldría ninguno por la regla 1 y lo vería como «indeterminado» masivo.

**Predicción escrita antes de medir.** El record del gránulo de MIROVA sin cráter casi nunca publica (no tiene el
cráter), y la publicación del gránulo norte ya hoy es `sin_info`, no negativo. Por lo tanto espero que la regla
nueva saque del orden de 1 a 2 % de los negativos y casi ninguna publicación de K: la tasa de publicación en
negativos limpios **sube** levemente, no baja. Si sale lo contrario, la hipótesis del coordinador gana.

## 1. Datos, scripts y ventanas

Records y referencia de `origin/main` en `d516b9d8c` (2026-10-22 01:49 UTC), extraídos con `git archive` a
`D:\vrp-trabajo\temporales\s159_negcrater\` junto con `scripts/`, `frontend/`, `pipeline/` y `volcanoes.yaml` de la
misma revisión (espejo; borrado al terminar). Referencia: snapshot unificado (45.337 filas, última 2026-10-20
17:30). Para el frente N, los datos del propio frente (`D:\vrp-trabajo\temporales\s159_n\data_main`, commit
`533398f8f`) y su `poblacion_completa.json`, `objetivos_censo.json` y `tabla_por_pasada.csv`. Predicado del tablero:
`mirovaEqVrp` + `isValidDetection` de `frontend/index.html` ejecutados con node vía `banco_paridad.cargar_nuestros`.

Todo en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\negativo_crater\`:

| script | qué mide | salida |
|---|---|---|
| `nlc.py` | biblioteca: cadenas, fracción del anillo, regla NLC | (sin salida) |
| `medir.py` | §1 corte contra la referencia; §2 ventana larga; §3 ventana del auto-audit; §4 frente N; §5 controles y pareo ±390 s | `medir_salida.txt`, `medir_salida.json`, `medir_stderr.txt` |
| `chequeo_57_vs_54.py` | por qué salen 57 negativos MODIS y el verificador del pareo contaba 54 | `chequeo_57_vs_54_salida.txt` |
| `solos_posthoc.py` | POST HOC: records solos con el anillo recortado | `solos_posthoc_salida.txt` |

Ventanas (A90, A119), cada número las lleva:
- **V-AA**, la del auto-audit (`ventana_falsas`: desde `INICIO_REGIMEN_FALSAS` = 2026-09-01, regla D-9 SN, sólo
  records con marca de K) hasta 2026-10-21. Limpia según A119 (después del 2026-06-13 y de abril). Con fin 10-19
  da exactamente lo mismo (no hay negativos limpios del 20 y 21).
- **V-N**, la del frente N: VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre, regla SN,
  commit `533398f8f`. VIIRS por pasada desde abril (A119).
- **V-L**, la del verificador del pareo (contexto, de donde vienen el 0,9 / 2,0 / 1,4 % del coordinador):
  2026-01-10 a 2026-10-21, regla original, todos los detectores. Cruza tramos defectuosos de la referencia (enero,
  marzo, OCR hasta junio, VIIRS por pasada antes de abril): sirve para contar casos, no para tasas comparables.

## 2. Resultado en una pantalla

La regla saca entre 1 y 2 % de los negativos limpios (todos de pasadas partidas con el gránulo de MIROVA sin el
cráter) y **casi ninguna publicación de K**: 0 en V-AA en los tres sensores, 0 en V-N, 1 en V-L (VIIRS 375, en el
borde del indicador). La razón es física: el record del gránulo que MIROVA listó es justamente el que no tiene el
cráter, así que casi nunca publica; y lo que publicamos desde el otro gránulo ya hoy queda `sin_info` (sin fila de
MIROVA a ±120 s), no como negativo. **La sobre-publicación de la réplica no es menor de lo que creemos: la tasa sube
entre 0,01 y 0,07 puntos** porque el denominador se achica y el numerador no.

| ventana | sensor | negativos viejos | K publica | % | negativos NLC | K publica | % | salen | pub. de K que salen | pub. del compañero (fuera de toda métrica) |
|---|---|---|---|---|---|---|---|---|---|---|
| V-AA | MODIS | 1.043 | 10 | 0,96 | 1.027 | 10 | 0,97 | 16 | 0 | 1 |
| V-AA | VIIRS 375 | 996 | 37 | 3,71 | 980 | 37 | 3,78 | 16 | 0 | 2 |
| V-AA | VIIRS 750 | 1.511 | 13 | 0,86 | 1.491 | 13 | 0,87 | 20 | 0 | 1 |
| V-N | VIIRS 750 | 5.476 | 54 | 0,99 | 5.400 | 54 | 1,00 | 76 | 0 | (no medido en V-N) |
| V-L | MODIS | 6.156 | 48 | 0,78 | 6.099 | 48 | 0,79 | 57 | 0 | 2 |
| V-L | VIIRS 375 | 4.260 | 114 | 2,68 | 4.176 | 113 | 2,71 | 84 | 1 | 8 |
| V-L | VIIRS 750 | 6.819 | 60 | 0,88 | 6.722 | 60 | 0,89 | 97 | 0 | 4 |

(En V-L los detectores van mezclados; en V-AA todo es K.)

Frente N con la definición nueva: **F sigue en +12** (de los 60 negativos que F enciende, 0 caen en pasadas que
salen; de los 59 `far`, 0), F publica 114 de 5.400 (2,11 %) en vez de 114 de 5.476 (2,08 %), K 54 de 5.400. **La cota
del oráculo no cambia en el numerador**: de los 34 negativos del lote con píxeles de algún oráculo (o `O_pub`), 0
caen en pasadas que salen, y las 1 y 4 publicaciones del oráculo en el censo son cúmulos de cumbre que se quedan.
Del lote salen sólo 2 negativos de `neg_resto` (Llaima 2026-09-25 06:36, peso 54, no publica en ningún brazo;
Chaitén 2026-06-30 06:12, peso 35,8, que el propio lote marcó `volcan_fuera_del_granulo`): cambian los pesos del
denominador, no los numeradores.

## 3. Hallazgos (lo peor primero)

### H1. La regla NLC no achica la sobre-publicación de K: con el pareo de hoy casi ninguna publicación cae en pasadas sin cráter

- SCRIPT:SALIDA `medir.py` → `medir_salida.txt` §2, §3, §4 (tabla de §2 de este informe).
- QUÉ PASA. Cuando el volcán cae entre dos gránulos y MIROVA lista el que no tiene el cráter, nuestro record de ese
  mismo gránulo tampoco tiene el cráter y casi nunca publica: en V-AA 0 de 52 negativos que salen publican; en V-L
  1 de 238 (Cordón Caulle VIIRS 375 2026-03-14 05:48, f = 0,486, donde publican los dos miembros: zona en que el
  indicador se equivoca). La publicación del gránulo con el cráter queda hoy `sin_info` (sin fila a ±120 s), así que
  nunca se contó como falsa. La regla sólo saca denominador.
- CÓMO SE VE EN EL DASHBOARD: invisible (es la vara de evaluación, no el tablero).
- CÓMO REPRODUCIRLO: `python -I medir.py <espejo de origin/main> --n D:\vrp-trabajo\temporales\s159_n`.
- CONFIANZA: CONFIRMADO (medido; el banco reproduce de forma independiente los 48 / 114 / 60 publicados en negativos
  y los 84 / 97 negativos de VIIRS que salen del verificador del pareo en V-L).
- GRAVEDAD 2: corrige una hipótesis del plan (la de que la sobre-publicación está inflada por estas pasadas). Ningún
  número de K, de F ni del oráculo se mueve más de 0,07 puntos, ningún veredicto cambia.

### H2. Con un pareo más ancho que ±120 s la regla sí es necesaria: sin ella el pareo ancho cuenta como falsas las publicaciones del gránulo con el cráter

- SCRIPT:SALIDA `medir.py` §5b (pareo ±390 s, V-L, regla original).
- QUÉ PASA. Con ±390 s el record del gránulo con el cráter se etiqueta con la RUTINA del gránulo vecino de MIROVA
  (que no miró el cráter) y su publicación pasa a falsa: K publica en negativos 52 / 122 / 64 (MODIS / V375 / V750)
  contra 48 / 114 / 60 con ±120 s. Con la regla NLC el pareo ancho baja a **48 / 113 / 60, exactamente lo mismo que
  el pareo de ±120 s con la regla**: la regla vuelve el numerador invariante al pareo. Las que el pareo ancho
  acusaba son, entre otras, Chillán MODIS Terra 2026-01-19 02:40, Chillán MODIS Aqua 2026-10-13 07:55, Láscar MODIS
  2026-05-05 01:30, Cordón Caulle MODIS Aqua 2026-06-26 07:40, Isluga V375 2026-02-04 05:48, 04-26 05:30 y 05-12
  05:30. El frente N usó el pareo de 8 min de R2.3 sólo para informar (`n/01_poblacion_salida.txt`: 143 negativos
  más), no para decidir, así que su línea base no está afectada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `medir.py`, bloque «§5b».
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 2 si alguien ensancha el pareo (lo que el frente de pareo ya recomendó no hacer): inflaría las falsas de K
  en 4 a 9 pasadas por sensor en V-L, todas con el cráter en nuestro gránulo y no en el de MIROVA.

### H3. La línea base de K del auto-audit #864 (MODIS 1,1 % de 658, VIIRS 375 3,0 % de 656, VIIRS 750 1,1 % de 949) era un subconjunto; con el corpus de hoy la ventana entera es K

- SCRIPT:SALIDA `medir.py` §3 («detectores en la ventana: {'K': 5716}» con fin 10-19) y
  `C:\vrp-trabajo\s159-pruebas\experiments\_s159\pareo_modis\audit_864_hoy.txt` líneas 31 a 36 (salida del
  auto-audit de #864 reproducida hoja por hoja por el frente de pareo).
- QUÉ PASA. En #864 la ventana V-AA (fin 10-19) tenía records de K y de C0; hoy los 5.716 records nocturnos de esa
  ventana llevan marca de K. Los denominadores de hoy son exactamente K + C0 de #864: MODIS 658 + 385 = 1.043,
  VIIRS 750 949 + 562 = 1.511, VIIRS 375 656 + 340 = 996. La línea base de K en negativos limpios de V-AA es hoy
  **MODIS 10 de 1.043 (0,96 %), VIIRS 375 37 de 996 (3,71 %), VIIRS 750 13 de 1.511 (0,86 %)**, no 1,1 / 3,0 / 1,1 %.
  Con la regla NLC: 0,97 / 3,78 / 0,87 %.
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta a quien cite la línea base de K del auto-audit de la semana pasada.
- CÓMO REPRODUCIRLO: `medir.py` §3.
- CONFIANZA: CONFIRMADO la suma exacta de denominadores y que hoy todo es K; SOSPECHA (apoyada en el índice de
  memoria, no medida aquí) que la causa sea el reemplazo del histórico por K de S158 (#883, #884).
- GRAVEDAD 2: VIIRS 375 sube de 3,0 a 3,7 % contra la cota del A/B de K (0,0166 a 0,0383, citada en el docstring
  de `resumir_falsas_por_detector`, `scripts/auto_audit_weekly.py`): sigue dentro, pero más cerca del techo.

### H4. (POST HOC) Records solos con el anillo recortado: otro 1 a 2 % de negativos sin cráter visible, también sin publicaciones

- SCRIPT:SALIDA `solos_posthoc.py` → `solos_posthoc_salida.txt`.
- QUÉ PASA. La regla de §0 deja todos los records solos porque el indicador necesita compañero. Como el perfil corre
  sin máscara de nube (`pipeline/profiles/mirova_equivalent.yaml:53`, `cloud_mask_bt_k: 0.0`, y
  `pipeline/process_modis.py:621` arma el anillo con `bt_mir > CLOUD_MASK_BT_K`), el anillo es casi geometría: un
  record solo con rho = nbg / mediana de los solos del mismo volcán, plataforma y cenit a ±3° bajo 0,5 tiene el ROI
  recortado. V-AA: 14 MODIS, 16 V375, 19 V750 negativos solos con rho < 0,5, **0 publicaciones de K**. V-L: 112 / 71
  / 94, 0 publicaciones. Control positivo: Chaitén 2026-05-15 04:24 (N-8, píxel más cercano a 23,5 km) da rho 0,008
  en V750 (nbg 10, el piso `min_bg_pixels`) y 0,010 en V375.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I solos_posthoc.py <espejo>`.
- CONFIANZA: CONFIRMADO el conteo; SOSPECHA que todos sean recorte geométrico (no se validó caso a caso; rho también
  baja con la exclusión K1 del anillo, que en negativos debería ser mínima). Post hoc: no entra a la regla de §0.
- GRAVEDAD 1: con esto el denominador bajaría otro 1,3 a 1,6 % en V-AA (VIIRS 375: 37 de 964, 3,84 %); mismo sentido
  que H1.

### H5. El corte 0,5 se sostiene contra la referencia en VIIRS 375; en MODIS y VIIRS 750 la referencia no alcanza para probarlo

- SCRIPT:SALIDA `medir.py` §1.
- QUÉ PASA. Tasa de alerta de MIROVA por tramo de f, en pasadas partidas con un solo gránulo listado (V-L, regla
  original): VIIRS 375 **0 de 114 bajo 0,5 y 22 de 109 sobre 0,5** (la alerta de f más baja: 0,537); MODIS 0 de 55 y
  1 de 75 (f 0,512); VIIRS 750 0 de 103 y 1 de 82 (f 0,76). Contra una medición independiente (miembro de partida con
  cúmulo con VRP > 0 a menos de 3 km del cráter): f ≥ 0,5 en 2 de 2 MODIS, 73 de 76 V375 y 11 de 12 V750. Sensibilidad
  del resultado al corte (0,4 / 0,6): las publicaciones de K que salen en V-L van de 0 a 2 en VIIRS 375 (0,6 agrega
  Chaitén V375 2026-08-12 06:06, f 0,565) y siguen en 0 en MODIS y VIIRS 750.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO para VIIRS 375; en MODIS y VIIRS 750 el corte descansa en la geometría y en el indicador, no
  en la referencia (una alerta por sensor).
- GRAVEDAD 1.

## 4. Controles (preguntas 1 y 2, leídos antes de concluir)

| control | predicción de §0 | resultado |
|---|---|---|
| Positivo 1: Chillán MODIS Terra 2026-01-19 02:40 | con ±120 s no es negativo; con ±390 s sí, y la regla 2 lo saca | ±120 s: `sin_info`, sin fila a ±120 s; ±390 s: `neg_limpio` con la fila de las 02:35, sale por `vecino_que_no_tenemos`; nuestro record publica. **Se cumple; el control tal como se pidió (que hoy sea negativo) no aplica con el pareo de hoy** |
| Positivo 2: Isluga V375 2026-02-04 05:54 | sale | `neg_limpio`, f 0,0, sale (`partida_sin_crater`) con ±120 y con ±390 s |
| Positivo 3: Chaitén V750 N-8 | si está en cadena de dos, sale | 2026-06-30 06:12: cadena de dos (compañero 06:06), f 0,229, **sale**; el lote de N lo marcó `volcan_fuera_del_granulo` (medición independiente por red). 2026-05-15 04:24: record solo (nbg 10), se queda por la regla; lo atrapa el post hoc H4 (rho 0,008) |
| Nulo: records solos | se quedan todos con ±120 s | 16.785 solos en `neg_limpio` en V-L, salen 0 |
| Instrumento vivo | campo no muerto, cadenas presentes | 0 de 71.968 records con `diag_n_bg_anillo` nulo; 1.714 cadenas de dos y 68.540 de uno en toda la historia (ninguna de tres); 0 fracciones indeterminadas entre los que salen; el predicado del tablero publica 48 / 114 / 60 en negativos de V-L, igual que el verificador del pareo |
| Reproducción de la línea base de N | 54 de 5.476 | 54 de 5.476 desde `poblacion_completa.json` |
| 57 contra 54 negativos MODIS que salen (verificador del pareo) | diferencia de definición, no de datos | 54 con compañero `sin_info` + 3 con compañero también `neg_limpio` (MIROVA listó los dos gránulos): `chequeo_57_vs_54_salida.txt` |

## 5. Lo que no medí

- La regla de §0 deja los records solos; el post hoc H4 los mide, pero sin validación caso a caso.
- Las publicaciones del compañero en V-N no las conté (no son negativos; el lote de N no las necesita).
- No reproduje #864 con su corpus (`2e1bc0e31`); comparo contra su salida reproducida por el frente de pareo.
- El frente N es sólo VIIRS 750: no hay F ni oráculo de VIIRS 375 o MODIS que corregir.

## 6. VERIFICADO LIMPIO

- El banco con el espejo de hoy reproduce los conteos del verificador del pareo en V-L (negativos 6.156 / 4.260 /
  6.819; K publica 48 / 114 / 60; salen 84 VIIRS 375 y 97 VIIRS 750): `python -I medir.py <espejo>` §2.
- `diag_n_bg_anillo` está en todos los records (0 nulos de 71.968) y el anillo no depende de nubes en el perfil
  operacional (`pipeline/profiles/mirova_equivalent.yaml:53`; `pipeline/process_modis.py:621`).
- Las cadenas nunca pasan de dos gránulos: `medir.py`, línea «P2: cadenas por largo».
- La regla no toca positivos ni alertas protegidas (sólo actúa sobre `neg_limpio`): recall y protegidas de cualquier
  evaluación quedan igual por construcción (`nlc.crater_en_granulo_mirova` sólo se llama si `lab == "neg_limpio"`).
- V-AA con fin 10-19 y con fin 10-21 da lo mismo (la tabla no trae negativos del 20 y 21).
- F del frente N no enciende ningún negativo de pasada sin cráter, ni de cumbre ni `far`: `medir.py` §4.

## 7. Candidatas para BEYOND_MIROVA_EXTENSIONS §12

1. **Estrato «MIROVA sin cráter» en las evaluaciones.** En V-L hay 238 pasadas partidas en que MIROVA listó el
   gránulo sin el cráter (57 MODIS, 84 V375, 97 V750); en 14 publicamos desde el otro gránulo (2 / 8 / 4) y en V-AA
   en 4 (Chillán MODIS Aqua 2026-10-13 07:55, Lastarria V375 2026-09-22 05:42, Cordón Caulle V375 2026-10-12 06:12,
   Láscar V750 2026-09-03 05:42). Ninguna métrica contra MIROVA las ve; se validan contra OVDAS o SWIR de alta
   resolución, no contra MIROVA.
2. **Declarar «no observado» cuando el ROI está recortado** (H4): 49 negativos solos en V-AA con menos de la mitad
   del anillo. Un SDA que separa «no vi» de «no miré» es más honesto que la tabla de MIROVA; la marca sería barata
   (`diag_n_bg_anillo` contra la mediana del volcán y cenit).
3. **Hacer la regla exacta guardando la línea y la muestra del cráter en el gránulo** (ya propuesto por el frente de
   pareo, hallazgo 5): quitaría la zona gris de f ≈ 0,5, donde cae la única publicación de K afectada (Cordón Caulle
   V375 2026-03-14 05:48, f 0,486).
