# Verificación con contexto limpio del RESULTADO de V375-B2 (run 40131572769)

- Hora del servidor (header Date de GitHub) al empezar: Sat, 24 Oct 2026 22:08:02 GMT.
- Commit medido: `8f2499fdc0d1bab158f39458054cafa3b3bec321` (rama `claude/s162-viirs375-c1b864`, árbol limpio al empezar). Runner: commit de disparo `a9331d51ce9f` (tag `s162-v375-b2-disparo-lote`), `pipeline/` idéntico a `ca034d66e` (diff vacío).
- Modelo: Sonnet 5.5 (claude-sonnet-5-5).
- Qué NO miré: el contenido físico de las 6 publicaciones (no abrí las grillas ni los TIF de MIROVA); el bloque V375-C de la salida (el pre-registro §7 dice que no se lee); las 7 plantillas de brazos distintos de M14; la corrección numérica de `brazos.py` (sólo comparé lo que el evaluador y mi script independiente leen de los JSON del runner); no re-bajé gránulos de NASA; no verifiqué los 35 «fuera del gránulo» contra los archivos MODIS/VIIRS de origen (sólo que el nombre del gránulo coincide con el del record de producción); el predicado node del tablero lo reemplacé con una versión mía de dos condiciones (ver §2), no lo ejecuté.
- Carpeta de trabajo propia: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs375-c1b864\3314638d-6b0b-401c-8eb1-92df9921586d\scratchpad\ver\`. Scripts copiados junto a este informe: `recuento.py` y `cota.py`.

## En una pantalla

1. Las cuatro afirmaciones se sostienen: recuento propio desde los JSON del runner da 6 de 1.165 pasadas ok de B2 que M14 publica (mismas 6 que el evaluador), y la cota de todos los negativos limpios recalculada a mano da 2,479 % contra 3,848 % (K): SILENCIO ACOTADO BAJO K.
2. El evaluador re-corrido con la caché da `evaluar_salida.txt` y `evaluar.json` idénticos byte a byte al commiteado; un recálculo fresco sin caché de una muestra de 50 pasadas (40 al azar, las 6 que publican y 4 del control) da lo mismo que el runner y que la caché en 50 de 50.
3. Las 35 «volcán fuera del gránulo» no sesgan el veredicto: están sobre todo a cenit alto (mediana 69,6° contra 52,1° de la muestra), pero harían falta unas 13 a 15 de las 35 publicando (tasa de 40 %) para cruzar los 3,85 %; la tasa observada con cenit mayor que 60° es 2 de 380.
4. El control de vida es real (20 de 20 re-medidas con M14 igual a S162 a 1e-9 MW, 16 con píxeles, referencias verificadas contra los resultados de S162) pero sólo prueba M14 en 6 de los 11 volcanes y deja a Villarrica, Copahue y Puyehue sin control; el pre-registro lo declara (H4, SOSPECHA).
5. El único cambio posterior al sello que toca código (`evaluar.py`, 5 líneas, control de vida obligatorio) no mueve ningún número ni el conjunto que decide; el runner y el archivo de objetivos son byte a byte los sellados. Hallazgos propios: todos de gravedad 1 a 2 (el «censo» de neg_pub no es censo, la unión no es una confirmación independiente, el run figura `failure` por diseño del código de salida).

## Caminos de ruptura escritos antes de abrir `evaluar_salida.txt`

Están en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\b2\resultado_run40131572769\verificador\CAMINOS_ANTES_DE_LEER.md` (escrito a las 22:08 GMT, antes de abrir la salida commiteada). Resumen: (1) pasadas que faltan o se cuentan dos veces; (2) las 35 fuera del gránulo; (3) el control de vida que compare otra cosa; (4) un conjunto que decide distinto de neg_resto de B2 + neg_pub de S162; (5) pesos y cota; (6) unión mal armada; (7) encendidos del port que el predicado no cuenta; (8) regla cambiada tras el sello; (9) caché de brazos obsoleta.

## 1. Diferencia entre el texto sellado y lo agregado después

`git diff s162-v375-b2-listo HEAD -- experiments/_s162_v375/b2/PREREGISTRO_B2.md`: el diff de `PREREGISTRO_B2.md` son sólo dos secciones agregadas al final, «Sello» y «Adenda 1»; el texto sellado (`ae65eaaaf`) no cambió. Adenda 1 trae 5 puntos (H1 a H5). Sólo H1 tocó código: `git diff s162-v375-b2-listo HEAD -- experiments/_s162_v375/evaluar.py` son 5 líneas que declaran INVALIDO POR INSTRUMENTO si decide un lote nuevo y el archivo de objetivos no trae el control de vida. No cambia umbral, conjunto ni cota, y como el archivo de objetivos sí lo trae, no se activó. Probe, brazos, workflow y objetivos: diff vacío entre el tag sellado y el commit de disparo (`probe_v375.py`, `brazos.py`, `b2/probe-s162-v375-b2.yml`, `objetivos_v375_b2.json`). Los blobs de `objetivos_v375_b2.json` en el tag sellado, en el disparo y en el árbol actual coinciden (sha256 con LF `a7dd6b0d…e955`, con CRLF `f3285f3a…b419`, como dice la adenda).

## 2. Recuento propio (script `recuento.py`, `cota.py`)

Método: leí los 48 `resultados_VIIRS375_NN.json` del runner, sin usar `evaluar.py` ni `brazos.py`. Para «publica» usé una versión mía del predicado del tablero (`mirovaEqVrp` de `frontend/index.html:1162`): hay brazo M14 con `npix > 0`, VRP > 0 y distancia mínima del píxel al cráter ≤ `inner_radius_km` del volcán (leído por regex de `frontend/index.html`, como lo hace la copia de `banco_noches.py`). Esto equivale a la regla del «alertado más cercano» más el corte de `distance_class`.

| cosa | mi número | evaluador commiteado |
|---|---|---|
| registros en el runner | 1.220 ids únicos (3000 a 4199 y 5000 a 5019), 1.185 ok, 35 `volcan_fuera_del_granulo` | 1.185 ok y 35 sin dato |
| pasadas ok de la muestra B2 | 1.165 | 1.165 |
| pasadas de B2 con M14 `npix > 0` | 6 | |
| pasadas de B2 que M14 publica | 6 (todas con `npix`=1): Copahue 2026-07-27 05:18 (0,0273 MW), Copahue 2026-09-24 06:54 (0,0098), Tupungatito 2026-06-27 04:36 (0,0129), Nevados de Chillán 2026-05-02 05:24 (0,0288), Isluga 2026-05-25 06:30 (0,038), Llaima 2026-09-30 05:00 (0,0174) | «neg_resto [6, 1165]» |
| S162 (re-contado con el mismo código mío) | neg_pub 31 de 113; neg_resto 4 de 389 | «S162\|neg: 35/113/502» (31 + 4) |
| población neg_resto del marco | 3.323 (re-derivada de `poblacion_completa.json`, sha `c08602de`, con mi definición: VIIRS 375, `decide`, `neg_limpio`, `pub_prod` = 0, sin los días excluidos) | 3.323 |
| tasa ponderada neg_resto B2 | 0,005133; Wilson sobre Kish n efectivo 1163,95: [0,002351; 0,011171] | idéntico a 15 cifras |
| tasa ponderada neg_pub S162 | 0,27537; Wilson sobre Kish 110,44: [0,20068; 0,36517] | |
| cota de todos los negativos limpios | (133 × 0,36517 + 3.323 × 0,011171) / 3.456 = **0,024794**; punto 0,015533; inferior 0,009983 | `0.0155 [0.009983054041059437, 0.024794167871596145]` idéntico |
| vara de K | 133 / 3.456 = 0,038484 | 0,0385 |

Hechos de la muestra B2 que comprobé contra la población y el marco: las 1.200 existen en la población congelada con `lab` = `neg_limpio`, `decide`, sin `pub_prod`, sin protegida y con `sha` igual al del objetivo; ninguna cae en los días excluidos; las 1.200 `(volcán, hora)` son únicas y no se cruzan con S159 ni con S162 (0 y 0); todas tienen fila de MIROVA, las 1.200 de la tabla `CONS` y las 1.200 `RUTINA` con VRP 0 (el canal más creíble, A119, sin OCR); `dayflag` = 0 en las 1.185 ok.

## 3. Re-corrida del evaluador

Comando exacto del encargo, con copia de la caché de brazos en mi carpeta: `evaluar_salida.txt` y `evaluar.json` idénticos a los commiteados (`diff` sin diferencias; `json ==` verdadero). Además corrí `muestra_sin_cache.py` (esta carpeta): recalculo fresco de los diez brazos sin caché en 50 pasadas (40 al azar con semilla 7, las 6 que publican y 4 del control): 0 diferencias contra el runner y 0 contra la caché. Una corrida completa sin caché (1.185 pasadas × 10 brazos) la dejé en marcha y no terminó mientras escribía este informe (más de 14 minutos); queda SIN DATO.

## 4. Veredicto por afirmación

**(a) Instrumento OK y control de vida 20 de 20. CONFIRMADO (gravedad de lo que queda: 2).**
- Cobertura: 2.032 ok de 2.078 objetivos; el control 2.1 (recálculo sin red = runner) da 19.277 de 19.277, y recompuse el denominador a mano: 447 (S159, 3 brazos × 149) + 6.980 (S162, 10 × 698) + 11.650 (B2, 10 × 1.165) + 200 (control, 10 × 20) = 19.277.
- Control de vida: las 20 referencias (`ref_M14`) de `objetivos_v375_b2.json` las contrasté yo contra `M14` de los resultados de S162 (run 40116289866, ids de referencia en el lote S162): 20 de 20 iguales (hasta 1e-9 MW) y el mismo nombre de gránulo en el run nuevo; 12 protegidas de Láscar y Chillán más 4 neg_resto que M14 publicó y 4 en cero. Como las referencias no salen de este run, el control no es tautológico. Dentro de este run, M14 reprodujo exactamente `npix` y VRP en las 20.
- El control sólo cubre 6 volcanes (Láscar, Chillán, Tupungatito, Llaima, Lastarria, Chaitén). Un fallo propio de Villarrica, Copahue, Puyehue, Planchón-Peteroa o Isluga no lo vería (H4 de la adenda, ya declarada como SOSPECHA).
- El run en GitHub figura `failure` (26 de 48 jobs en rojo), pero es por diseño: `probe_v375.py` termina con código 2 si alguna pasada del trozo no está `ok` (`probe_v375.py:153`), y los 26 trozos en rojo son exactamente los 26 que contienen alguna de las 35 pasadas `volcan_fuera_del_granulo`. Ningún log tiene `Traceback`; los 48 traen «PRUEBA SIN RED OK» y «CONTROL SIN RED OK».

**(b) Cobertura completa con 35 no observadas. CONFIRMADO (gravedad 1).**
1.185 de 1.220 ok (1.165 de la muestra más 20 de control). Las 35 que faltan: las 35 tienen el mismo nombre de gránulo que el record de producción (regla de #904), ninguna tiene clúster en el record de producción (`pc_n` nulo), el volcán queda a 5,8 a 30,5 km del borde del gránulo. Son 2,9 % de la muestra (S162: 11 de 400, 2,75 %), bajo el umbral de 10 %. Sesgo posible: están sobre todo a cenit alto (mediana 69,6° contra 52,1° de la muestra; 80 % tiene cenit mayor que 40°, contra 67 % de la muestra) y por volcán pesa Chillán (10 de 144 = 6,9 %). Sensibilidad que calculé: si se incluyen los 35 como pasadas con los pesos nominales y se hace publicar a los k de mayor cenit, la cota total cruza 3,848 % con k = 13 a 15 (k = 10 da 3,47 %; k = 15 da 3,96 %). La tasa observada en pasadas ok con cenit mayor que 60° es 2 de 380 (0,5 %), y en cenit mayor que 40° es 5 de 778 (0,6 %). Un 40 % de publicación entre las 35 no es creíble con esos datos (SOSPECHA, no medido directamente porque esas pasadas no tienen grilla).

**(c) VEREDICTO B = SILENCIO ACOTADO BAJO K con 6 de 1.165 y cota 2,48 % contra 3,85 %. CONFIRMADO (gravedad de lo que queda: 1).**
Recuento propio y cota propia coinciden con el evaluador a 15 cifras (§2). La línea «VEREDICTO B (S162b (neg_pub de S162) decide, unión confirma): SILENCIO ACOTADO BAJO K» está en la sección 4b y es la que el pre-registro dice que decide. La regla aplicada es la de `PREREGISTRO_B.md` §5 sin cambios en la cuenta: cota conservadora = suma de los extremos de Wilson de cada clase ponderada por N. La lectura estricta (z = 2,241) también queda bajo la vara (2,65 %).

**(d) La unión lo confirma. CONFIRMADO EN PARTE (gravedad 2, ver H2).**
La línea «B: … DE ACUERDO» está y es literal. Pero la unión (S159 + S162 + B2, 2.012 pasadas, neg_resto 10 de 1.599, cota 2,20 %) contiene las 1.165 pasadas que deciden y las 389 + 45 que ya se habían visto; no es una confirmación independiente, y en el pre-registro es un mero chequeo de coherencia. Que «DE ACUERDO» salga es casi automático cuando el lote que decide pesa 73 % de la unión.

## 5. Hallazgos propios

**H1. El «censo» de neg_pub sigue siendo una muestra de 113 de 133, y 3 de las 133 noches quedan sin representar. Gravedad 1. Confianza alta.**
`evaluar_salida.txt` línea «decisión sobre: lotes S162b (DECIDE)…»: `N representado por clase: {… 'neg_pub': 130.0 …}`. En el conjunto que decide, neg_pub sale sólo de S162 (113 pasadas), así que 3 unidades de población caen en estratos que sólo tenían pasadas de S159 y no se representan; la fórmula igual pondera la tasa por `N_neg["neg_pub"]` = 133. El efecto es de tercer decimal. La sección 3 del mismo archivo rotula «neg_pub (censo): publica 38 de 133», que es el pool S159 + S162 y no el que decide (31 de 113). Reproducir: `python -I cota.py` (en esta carpeta) para la cuenta, o leer el bloque «decisión sobre» del archivo. Dirección del sesgo: conservador, porque el censo de 133 daría tasa 38/133 = 28,6 % con Wilson más angosto.

**H2. La «confirmación» por la unión no es independiente. Gravedad 2. Confianza alta.**
Ver afirmación (d). No cambia el veredicto (la regla sellada la define así), pero el informe no debe leerse como «dos mediciones que coinciden». La única medición independiente es la de neg_resto de B2 contra la vara, y esa sola ya cumple.

**H3. Las 6 publicaciones de B2 y las 4 de S162 son todas de un solo píxel y de 0,01 a 0,052 MW. Gravedad 1. Confianza alta.**
`python -I recuento.py` (en esta carpeta). Magnitud máxima observada en neg_resto: 0,052 MW (Lastarria 2026-09-27, S162). Es información útil para el operador: los «puntos nuevos» que el port encendería en noches sin nada serían de pocos centésimos de MW, en su mayoría bajo el piso de 0,05 MW con que D-9 llama NONE a una alerta de MIROVA (9 de 10; Lastarria 2026-09-27 pasa por 0,002). No estaba pedido en el pre-registro; no cambia el veredicto.

**H4. La cuenta mide «menos publicaciones que K», no «ninguna publicación nueva». Gravedad 2. Confianza alta.**
K publica en las 133 noches neg_pub (por definición) y nada en neg_resto; el port publica en 27,5 % de las neg_pub (31 de 113) y en 0,51 % de neg_resto (6 de 1.165). La tasa agregada del port (1,55 %) queda bajo la vara de K (3,85 %) sobre todo porque calla donde K publica. Lo que el operador vería como «punto falso nuevo» es sólo la parte neg_resto: 17 noches estimadas en 3.323 (cota de Wilson 1,12 %, o 37 noches). Que la lectura de B esté bien hecha no implica que el port no añada puntos falsos; implica que su balance contra K es favorable. Si la pregunta de producto es «¿enciende puntos que K no enciende?», la respuesta es sí, entre 0,2 % y 1,1 % de las noches limpias (cota Wilson al 95 %).

**H5. Heterogeneidad por volcán que el intervalo agrupado no modela. Gravedad 1. SOSPECHA.**
Los 6 eventos de B2: Copahue 2 de 175, Chillán 1 de 134, Tupungatito 1 de 75, Isluga 1 de 17, Llaima 1 de 176, Lastarria 0 de 40 (dato mío con `recuento.py`, estratos de `objetivos_v375_b2.json`). En S162, Lastarria tenía 2 de 12. Isluga con 1 de 17 (6 %) y Lastarria no se pueden separar de ruido con esos n. La binomial ponderada por estrato asume tasa pareja dentro del estrato; el pre-registro §3 lo declara como supuesto.

**H6. La caché de brazos podría esconder un recálculo desactualizado. Gravedad 2 si fuera cierto; probado en muestra, sin hallazgo. Confianza media.**
`evaluar.py:223 recalcular()` reutiliza `cache[id|sha de la grilla]` si todos los brazos están. Si la caché se hubiera calculado con un `brazos.py` anterior, el control 2.1 compararía el runner contra su propia versión vieja. Lo probé con la muestra de 50 pasadas (0 diferencias fresco contra caché y contra runner), así que no hay indicio de caché vieja; la verificación completa quedó SIN DATO. No existe un chequeo de versión de `brazos.py` en la clave de caché (sólo id y sha de la grilla), lo que deja la puerta abierta a futuro.

## 6. VERIFICADO LIMPIO (con contra qué vara)

- 1.220 resultados del runner, ids únicos, sin duplicados entre lotes: contra los ids de `objetivos_v375_b2.json` (3000 a 4199, 5000 a 5019) y contra los ids de `objetivos_v375_bc.json` (cruce vacío).
- Muestra B2 en el marco: contra `poblacion_completa.json` (sha `c08602de`), sha de cada pasada, `neg_limpio`, `pub_prod` = 0, no excluidas, sin cruce con S159 ni S162.
- Referencia de MIROVA de la muestra: contra los campos `mirova` de los objetivos, 1.200 de 1.200 filas `RUTINA` de la tabla `CONS`, ninguna con VRP positivo.
- Publicaciones de M14 en B2: 6, igual al evaluador, contra mi predicado propio sobre el JSON del runner.
- Conteo de S162 (neg_pub 31 de 113, neg_resto 4 de 389): igual al «35/113/502» del evaluador.
- Pesos (N por estrato desde la meta de objetivos, 3.323 = 3.323 en las dos metas) y cota 0,024794: recalculados a mano, igual a 15 cifras.
- Salida del evaluador re-corrida con la caché del encargo: texto y JSON byte a byte iguales.
- Texto sellado del pre-registro: sin cambios; sólo se agregaron «Sello» y «Adenda 1».
- Archivo de objetivos del disparo: igual al sellado (sha256 con LF y con CRLF).
- Árbol de `pipeline/` del runner: diff vacío contra `ca034d66e`.
- Control de vida: referencias contrastadas contra los resultados de S162, 20 de 20.
- Resultado `failure` del run: explicado por el código de salida 2 del probe; los 26 trozos en rojo son los 26 con pasadas fuera del gránulo.

## 7. SIN DATO

- Si las 35 pasadas fuera del gránulo publicarían: no tienen grilla; sólo se acota (§4b).
- Si un port roto sólo en Villarrica, Copahue, Puyehue, Planchón-Peteroa o Isluga pasaría el control de vida (límite de diseño, H4 de la adenda).
- Dependencia temporal o por noche entre pasadas (H6 de verificadores anteriores): no modelada ni medida aquí.
- Que el predicado de dos condiciones mío sea idéntico al predicado node de `banco_paridad` en todos los casos: coincide en las 6 + 35 + 4 + 31 del conjunto leído, no se probó en más.
- Recálculo completo sin caché de las 1.185 pasadas (la muestra de 50 sí): corrida de más de 14 minutos que corté sin resultado.
- Contenido físico de las 6 publicaciones (si son lava real sub-umbral o artefacto): no abrí las grillas.
