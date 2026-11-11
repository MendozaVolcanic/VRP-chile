# Verificador del frente D (planes pendientes contra la misión), auditoría S179

## 1. Encabezado

- Hora del servidor: inicio Wed, 11 Nov 2026 01:59:02 GMT; cierre de mediciones Wed, 11 Nov 2026 02:10:07 GMT (cabecera `Date` de api.github.com).
- Commits sobre los que medí: código en main `438a60a1e` (instantánea `D:\vrp-trabajo\temporales\s179-audit\main\`, y `git show 438a60a1e:<ruta>`); documentos del loop en `0472cd95e` (instantánea `D:\vrp-trabajo\temporales\s179-audit\loop\`); plan de reemplazo en `62ccb8830` (punta de #981, fuera de main); lectura de la retrospectiva en `ff8a39972` (rama `claude/s178-retro-lectura`, fuera de main); B1 en `bbbe2068d` (#974) y B2 sobre B1 en `e68819484` (#983), los dos fuera de main.
- Datos: la carpeta base del auditor `D:\vrp-trabajo\temporales\s179-audit\d\base\` (sólo lectura). Comprobé que es la de 438a60a1e: `latest_consolidado.csv` sha256 `40b1b928c602b37f...7fdf6`, OCR `7e54155a3e0ddd0a...1e75` (los del preámbulo) y `data/mirova_equivalent/Isluga.json` y `Lascar.json` iguales byte a byte a `git show 438a60a1e:...`. Artefactos de la vía D2 y D4 leídos directo de `C:\Users\nmend\vrp-temporales\s177_d2\` y `C:\Users\nmend\vrp-temporales\s177_d4\`.
- Modelo: Claude Opus 5.5 (`claude-opus-5-5`). Esfuerzo: el arnés no me lo declara en esta sesión; no lo afirmo.
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vd\`. Temporal: `D:\vrp-trabajo\temporales\s179-audit\vd\` (40 MB).
- Caminos escritos antes de abrir nada: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vd\caminos.md` (sha256 del contenido sellado `5dcad87e...27d5fe`).
- API de GitHub: 2 llamadas, las dos para la cabecera `Date`. La primera la hice antes de leer `insumos\` (el encargo pedía leerlos antes); no cambió ningún dato, sólo dio la hora.
- Qué NO miré: el informe del auditor y su `hallazgos.csv` (obstáculo deliberado); P4 (no está bajado, salvo lo que diga `C:\Users\nmend\vrp-temporales\s178_historia\`, que no abrí); el contenido de la vía en los días del 2026-11-10 en adelante; VIIRS 750 y MODIS en el eje de posición (en los dos la retrospectiva decide con el mismo brazo que escribe producción, `V`, ver VERIFICADO LIMPIO); la imagen de MIROVA de las 5 pasadas.

## 2. En una pantalla

- 551: CONFIRMADO EN PARTE, gravedad 3. Producción con B1 publica con la posición «radiante» y la retrospectiva decidió con «cercano»; el 5 de 72 se reproduce por otro camino. Pero las 5 son sólo del OCR, con distancia de MIROVA dudosa, y con la tabla sola la vía radiante pierde 0 de 44.
- DEC-14: REFUTADO en lo central, gravedad 1. La misma lectura con candado calculó «radiante» y dio la misma fila 6, sin protegida perdida.
- 552 y 553: CONFIRMADOS, gravedad 2 y 3. El reemplazo deja el nulo en 0 pares y la vigilancia pasa de VERDE a VIGILANCIA_CIEGA. En VIIRS el encendido de la regla sellada retrocede al 2026-11-08 18:04:23 UTC. Hallazgo propio VD-01: las pasadas reprocesadas entre esa hora y el merge real entran al disparador de reversión pre-autorizado.
- 554: CONFIRMADO EN PARTE (2): el plan no cuenta qué deja de publicarse, pero marzo a octubre sí se leyeron contra MIROVA dentro de muestra. DEC-1: CONFIRMADO EN PARTE (2). DEC-7: CONFIRMADO (2). DEC-17: REFUTADO (1).

## 3. Veredictos por afirmación

### 551. B1 enciende la posición radiante; la evidencia que lo autoriza es de cercano; con el predicado del tablero la vía calla 5 de 72 protegidas VIIRS 375 que K publica

Veredicto: **CONFIRMADO EN PARTE**. Mi gravedad: **3** (auditor: 4).

Lo que se confirma:
- Producción escribe «radiante». `pipeline/mirova_v750_codigo.py` (438a60a1e) l. 670 a 684, `_cumulo_del_mas_radiante`, y l. 717 a 726: la clase `summit`/`far` sale del centroide del cúmulo de la alertada de mayor M13. B1 no toca ningún `.py` de `pipeline/`: `git diff --stat 557dbd05d bbbe2068d` sólo cambia perfiles, docs y pruebas; `git diff --stat 438a60a1e e68819484 -- pipeline/` sólo perfiles.
- La retrospectiva decide VIIRS 375 con «cercano»: `experiments/_s172_retro_paquete/leer_retro.py` l. 1274 (438a60a1e), TEXTO: «"VIIRS375": "V-cercano"». La lectura con candado (`git show ff8a39972:experiments/_s178_lectura/lectura.json`) dice `"brazo": "V-cercano"`, fila 6 (`vd5_lectura_retro_v375_salida.txt`).
- El 5 de 72 se reproduce por otro camino (`vd1_cercano_vs_radiante.py`): leo los records de la vía directo de los trozos D2 y D4, no la unión del auditor. F26: 49 protegidas, K publica 47, la vía radiante calla 3. DM: 23 protegidas, K publica 23, la vía radiante calla 2. Mismas 5 pasadas que el auditor. Con «cercano» la vía calla 0 en las dos ventanas. Controles: placebo (radiante aplicado por la función igual al record crudo) OK; control positivo (reproduce el 5) OK.

Lo que no se sostiene como lo dice el título:
- **Con la tabla sola la vía radiante no pierde ninguna protegida**: 0 de 44 (26 en F26 y 18 en DM tienen fila de la tabla; ninguna de las 5 perdidas la tiene; `vd1_cercano_vs_radiante_salida.txt`). La retrospectiva decide con la tabla sola («Decide la tabla sola (source CONS); la unión con el OCR informa», `leer_retro.py` l. 26 a 27, TEXTO) y calculó el brazo radiante: `otros_brazos.radiante._fila_regla = 6`, `P1_veto = []`, `cercano_y_radiante_difieren = false` (`vd5_lectura_retro_v375_salida.txt`). O sea, la evidencia que autoriza el encendido también existe para «radiante», con el mismo veredicto.
- **Las 5 descansan en filas sólo del OCR cuya distancia es dudosa** (`vd3_filas_ocr_cinco_salida.txt`):
  - las 3 de F26 (Isluga 2026-03-20 05:06 y 03-24 05:30, Láscar 03-15 05:00) son de Suomi NPP, OCR versión 21.0, con `Distancia_km` 0.0 y la distancia sólo en la nota («dist≈2.95 km» y similares). La propia lectura avisa que antes del 2026-06-11 «la geometria del OCR estaba mal calibrada» y antes del 06-13 «el OCR no media la distancia» (`git show ff8a39972:experiments/_s178_lectura/lectura_salida.txt`, TEXTO). Son las N-3 que la regla excluye (`leer_retro.py` l. 159 y l. 423 a 431).
  - Isluga 2026-10-03 05:18 es de Suomi NPP antes del 2026-10-09: `vigilancia_sombra.pasadas_de_alerta` la marca `referencia_sospechosa` (la distancia puede ser de otra pasada). Además, la tabla trae en ese mismo minuto una fila «VIIRS» RUTINA con 0.0 MW (ver VD-04).
  - Láscar 2026-10-01 05:18 (NOAA-21) es la única sin marca. Su distancia complementaria es «ambiguo» con rango 1.22 a 20.19 km; la vía pone el cúmulo más radiante a 18.99 km. En Isluga 10-03 el rango llega a 22.9 km y la vía lo pone a 22.78 km.
  - 2 de las 5 son de DM, que la retrospectiva usa como control de montaje, no como evidencia (pre-registro, `git show 0472cd95e:experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` l. 183, TEXTO: «**control de montaje**, no evidencia»).
- El desacuerdo cercano contra radiante ya era conocido y se llevó a Nicolás: bitácora `tasks/LOOP_OBJETIVOS.md` l. 2256 (0472cd95e), «Cercano decide», para la sombra de V375-E; l. 2273 a 2274: la elección de cercano «cuelga de 2 protegidas NOAA-21 sólo del OCR»; l. 610 y la cabecera de la regla sellada: Nicolás eligió «C-rad (14/17)», las cotas medidas con «el brazo radiante, el que cuenta la vigilancia».

Por qué dejo gravedad 3 y no 2: el mecanismo es real y va a repetirse en producción (un píxel débil en el cráter con una fuente más radiante a 7 a 34 km, bitácora l. 3003 a 3005). Ningún texto que Nicolás firme al mergear B1 le dice que la posición que publica no es la que decidió (VD-03).

### DEC-14. «Retro primero» (2026-11-10 01:17), juzgada DEBILITADA porque la condición se cumplió con «cercano» y producción escribe «radiante»

Veredicto: **REFUTADO** en lo central. Mi gravedad: **1** (auditor: 4).

La frase está en la bitácora (l. 687 a 689, 0472cd95e). La condición es «encender VIIRS si no pierde protegidas». La misma lectura con candado calculó el brazo de producción: radiante da fila 6, `P1_veto` vacío y la misma decisión que cercano (`vd5_lectura_retro_v375_salida.txt`). Las únicas pérdidas de radiante en F26 son 3 sólo del OCR de Suomi NPP de marzo, todas N-3. La regla pre-registrada las excluye aunque decida el brazo radiante (`leer_retro.py` l. 428 a 429). La condición se cumple con los dos brazos. El residuo (DM, Láscar 10-01) queda en 551.

### 552. El paso MODIS del plan de reemplazo deja ciega la vigilancia de la guardia K de MODIS (nulo 167 a 0 pares, VERDE a VIGILANCIA_CIEGA)

Veredicto: **CONFIRMADO**. Mi gravedad: **2** (auditor: 3).

- Re-corrí `m3_vigilancia_tras_reemplazo.py` del auditor con salida en mi carpeta (`rerun_m3_salida.txt`). Base: VERDE, encendido 2026-11-02 20:11:43, nulo 167 pares, igual a lo que el workflow guardó en 438a60a1e (control OK). Simulación: nulo 0 pares, `sin_medir=True`, VIGILANCIA_CIEGA; el encendido no cambia.
- El mecanismo, en `scripts/vigilancia_guardia_modis.py` (438a60a1e): l. 296 a 313, el nulo sólo cuenta pasadas de producción con `via` distinta de True en los 14 días previos al encendido; l. 374 a 379, 0 pares da aviso; l. 526 a 528, un aviso convierte VERDE en VIGILANCIA_CIEGA.
- El plan reemplaza justo esos días: `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` (62ccb8830) l. 142, MODIS «`desde = 2025-02-15`, `hasta = 2026-11-02`»; P4 cubre «2026-10-17..11-09» (l. 57).
- Matiz: «ciega» es la etiqueta, no la detección. `veredicto` sólo cambia si era VERDE (l. 527), así que una REVERSION_CANDIDATA sigue saliendo. El costo es un issue «Guardia K de MODIS: vigilancia ciega» que se comenta cada día (`.github/workflows/vigilancia-guardia-modis.yml` l. 139 a 145, 438a60a1e) hasta que venza el plazo (120 días desde el 11-02). Es un falso aviso diario que acostumbra a ignorarlo. La simulación supone la regla A (apartar los K sin par), que es la recomendada (bloque S179 §b6). Con «dejar», quedarían unos pocos pares de borde.

### 553. El paso VIIRS del plan de reemplazo corre el encendido de la regla sellada al 2026-11-08 18:04 UTC y borra el nulo de la guardia K de VIIRS (223 a 0 pares)

Veredicto: **CONFIRMADO**. Mi gravedad: **3** (auditor: 3).

- La regla sellada define el encendido por `processed_utc`: `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md` (438a60a1e) l. 57, TEXTO: «**Encendido** de cada sensor = el menor `processed_utc` de un record de producción de ese sensor con `via_codigo_mirova: true`». El código lo hace igual: `scripts/vigilancia_guardia_modis.py` l. 124 a 146.
- Medí por otro camino el menor `processed_utc` de la vía directo en los artefactos (`vd2_processed_utc_salida.txt`): D2 VIIRS 375 `2026-11-08T18:04:23Z`, VIIRS 750 `2026-11-08T18:04:36Z`, todos con la marca. El reemplazo conserva el `processed_utc` del reproceso: `scripts/reemplazar_ventana_reproceso.py` l. 72 a 77 sólo hereda `first_processed_utc`. El plan aplica VIIRS «SÓLO después de su encendido» (l. 282), así que el menor `processed_utc` pasa a ser el del reproceso, anterior al merge real de B1.
- El plan no lo ve: su paso 10 toma el encendido como la «primera pasada con `via_codigo_mirova: true`» (l. 284), no el menor `processed_utc` de la regla.
- Re-corrí `m3b_vigilancia_viirs_tras_reemplazo.py` (`rerun_m3b_salida.txt`): S0 reproduce el guardado (VERDE, nulo 223); S1 encendido ficticio con 223 pares; S2 encendido 2026-11-08 18:04:23, nulo 0, VIGILANCIA_CIEGA. Idéntico al auditor.
- Lo que la simulación del auditor no puede mostrar lo pongo como VD-01 (posible duplicado de su texto, que no vi).

### 554. El plan de reemplazo no cuenta qué deja de publicarse y se aplicaría sobre meses sin lectura contra MIROVA (P4)

Veredicto: **CONFIRMADO EN PARTE**. Mi gravedad: **2** (auditor: 3).

- Confirmado: el plan sólo mide cobertura. `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` (62ccb8830) l. 6 a 7, TEXTO: «Alcance de lo medido: sólo COBERTURA ... No se leyó ningún veredicto ni se comparó la vía con K o con MIROVA». El ensayo que va a Nicolás antes del sí trae «reemplazados, apartados por motivo, caídas a K, agregados, sha256 intacto» (l. 272 a 274), no qué pasadas cambian de publicada a no publicada. `docs/MISSION.md` l. 113 (438a60a1e), TEXTO: «En la réplica no se acepta ningún cambio que pierda una alerta protegida». En las ventanas con artefacto, el reemplazo de VIIRS 375 dejaría sin publicar las 5 protegidas sólo OCR de 551.
- Refutado en parte: «meses sin lectura contra MIROVA» no vale para marzo a octubre de 2026. Los A/B leyeron esos meses contra MIROVA dentro de muestra: MOD-D 2026-03-01 a 10-26, V375-E 2026-04-01 a 10-21, V750-B 2026-04-01 a 11-02 (pre-registro de la retrospectiva, 0472cd95e, l. 130 a 136, TEXTO de la tabla). Lo que sí falta es una lectura fuera de muestra y una con el código despachado (`a7a6ae360`) en esos meses. Enero no tiene referencia usable («enero no se usa», A119). La cola 2026-10-22 a 11-09 en VIIRS 375 no la leyó nadie.
- Mitigación: cada paso que escribe la serie pide el sí de Nicolás y tag (l. 3 a 4, l. 272 a 276).

### DEC-1. «Sí, prepáralo» del 2026-11-02 00:30, juzgada APLICADA DISTINTO

Veredicto: **CONFIRMADO EN PARTE**. Mi gravedad: **2** (auditor: 2).

- La frase está: bitácora l. 1621 a 1623 (0472cd95e). El plan fija las compuertas: `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` l. 397 a 401, la Compuerta A abre la sombra de los 34 sólo si la retrospectiva da CUMPLE en cada sensor; la Compuerta B abre la publicación (l. 13 a 14, l. 44).
- La sombra de los 34 se abrió antes de la Compuerta A, pero con una frase posterior de Nicolás: bitácora l. 1598 a 1604 (2026-11-02 01:24 UTC), «continúa con todo para que avancemos más rápido», que la sesión «Se lee como sí a la sombra de los 34 con las vías desde ya». Es una interpretación, no una frase directa, pero está registrada con su hora y #932 entró con «Sí, mergear #932» (l. 1494 a 1495).
- Lo que no sigue el plan y no tiene frase es la página preliminar (DEC-7). Hoy la Compuerta A tampoco se abriría: la retrospectiva dio MODIS y VIIRS 750 en fila 4 (bitácora l. 633 y 635).

### DEC-7. Publicación de la página preliminar de los 34 (#972, 2026-11-09 23:05) sin frase de Nicolás citada, juzgada SIN RESPALDO

Veredicto: **CONFIRMADO**. Mi gravedad: **2** (auditor: 2).

- La bitácora l. 699 (0472cd95e) dice «con la frase de Nicolás» y no la cita. El cuerpo de #972 (insumo `api_pr_972.json` del auditor) no menciona a Nicolás; el commit de merge `bfab7c8c0` tampoco. El bloque S178 l. 25 a 26 y l. 74 sólo dicen PUBLICADA. `merged_by` es la cuenta `MendozaVolcanic`, que comparten Nicolás y las sesiones, así que no prueba quién lo decidió.
- Lo más cercano es una pregunta de Nicolás («¿por qué no publicamos la sombra con todos los volcanes?», bitácora l. 802) y la recomendación de la sesión («los 34 en sección aparte», l. 804). Una pregunta no es la frase que pide la vara.
- La página está enlazada desde el tablero principal (`frontend/index.html` l. 419, 438a60a1e) y declarada en la ficha SDA v1.20 (`docs/FICHA_SDA_VRP_CHILE.md` l. 51). Lleva el rótulo de la Compuerta B («sin referencia de MIROVA, paridad no medida», `frontend/preliminar_34.html` l. 39), o sea, adelanta la forma de la Compuerta B sin su decisión.

### DEC-17. Orden de encendido del bloque S179 §b1, §b2 y §g.6 (3 noches de guardia, #974, #983, reemplazo después), juzgado SIN RESPALDO tal como está escrito

Veredicto: **REFUTADO**. Mi gravedad: **1** (auditor: 3).

- El bloque no lo presenta como decidido. Está en «## b. Decisiones que espera el dueño» (`tasks/BLOQUE_ARRANQUE_S179.md` l. 34 a 39, 0472cd95e), con opciones y recomendación, y §g.6 (l. 110) pide «"mergea #974" y luego "mergea #983"».
- «3 noches» tiene respaldo en la regla sellada: `REGLA_REVERSION_V375E_BORRADOR.md` l. 51 (438a60a1e), TEXTO: «**al menos tres noches** antes de pedir cada B». Nicolás la selló con «Sello la regla», 2026-11-10 10:12:44 UTC (l. 3 de la regla), y la mergeó con «Mergea #982» (bitácora l. 579).
- #974 antes de #983 es técnico: #983 contiene B1 y B2 (bitácora l. 581 a 582, comprobado por la sesión).
- «Reemplazo después» sigue el plan (l. 282). Que ese orden choque con la regla sellada es 553, no falta de respaldo.
- Residuo: la l. 12 del bloque dice que el encendido «sólo espera las 3 noches verdes de la guardia K y su frase». No menciona que VIIRS 750 salió en fila 4, DECIDE NICOLÁS, aunque §b2 lo pone como decisión. Tampoco menciona el desacuerdo de posición en VIIRS 375 (VD-03).

## 4. Hallazgos propios (orden por gravedad)

### VD-01
- TÍTULO: Tras el reemplazo de VIIRS, las pasadas reprocesadas entre el 2026-11-08 18:04 UTC y el merge real de B1 entran al disparador de reversión pre-autorizado y a las cotas
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 221 a 223 (438a60a1e); `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md` l. 57 a 59 y §4.3; `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` l. 284 a 286 (62ccb8830)
- QUÉ PASA: la regla separa lo retrospectivo de lo prospectivo por la hora del encendido. Con el encendido retrocedido al `processed_utc` del reproceso, las noches entre el 11-08 y el merge real (unas 4 a 5 si B1 entra tras las 3 noches del 11-10 al 11-12) quedan del lado prospectivo. El paso 11 del plan cubre justo esas noches con records de un reproceso de la vía. El código separa con `pros = [p for p in pasadas if p["instante_utc"] >= corte]`. Una protegida que la vía reprocesada calle en esas noches dispararía una REVERSION_CANDIDATA pre-autorizada sobre datos retrospectivos, y sumaría a las cotas Muy Bajo y sobre-publicación. Es lo que la regla excluye a propósito en §4.1 («esa franja es retrospectiva y no dispara la reversión»).
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero. Se vería como un issue «Guardia K de VIIRS 375: candidata a reversion» o como cotas que avanzan sin noches nuevas.
- CÓMO REPRODUCIRLO: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\d\m3b_vigilancia_viirs_tras_reemplazo.py" D:\vrp-trabajo\temporales\s179-audit\main D:\vrp-trabajo\temporales\s179-audit\d\base <sim> <salida.json>`. En S2 el encendido sale 2026-11-08 18:04:23. Para medir el contenido haría falta el reproceso del 11-10 en adelante, que no existe.
- CONFIANZA: CONFIRMADO el mecanismo (código y regla leídos, encendido medido en `vd2_processed_utc_salida.txt`); SOSPECHA que dispare algo, porque depende de lo que publique la vía en esas noches.
- GRAVEDAD 1-5: 3 (una reversión pre-autorizada sobre la base equivocada apaga la vía de VIIRS 375 en producción). Posible duplicado de 553: el título del auditor no lo nombra.

### VD-03
- TÍTULO: El PR de B1 (#974) no dice que producción publicará con la posición «radiante» mientras la retrospectiva decidió con «cercano»
- ARCHIVO:LÍNEA: `D:\vrp-trabajo\temporales\s179-audit\insumos\pr_974.json` (cuerpo de 9.976 caracteres); SCRIPT:SALIDA `vd4_pr974_983_busqueda_posicion_salida.txt`
- QUÉ PASA: el frente de calor de un volcán puede convivir con otra fuente más caliente a decenas de km. Con «radiante» la vía clasifica la pasada por la fuente más fuerte; con «cercano», por el píxel más cerca del cráter. La búsqueda de «radiante», «cercano» y «posici» en el cuerpo de #974 y de #983 da 0 coincidencias. Quien mergea B1 no lee en el PR que la posición publicada no es la que decidió la lectura.
- CÓMO SE VE EN EL DASHBOARD: invisible hasta el merge. Después, una pasada con un píxel débil en el cráter y una fuente más radiante lejos sale «far» y no se publica.
- CÓMO REPRODUCIRLO: ver el comando de `vd4` en la sección 6.
- CONFIANZA: CONFIRMADO. Mitigación: Nicolás eligió las cotas C-rad sabiendo que la vigilancia cuenta «radiante» (bitácora l. 610).
- GRAVEDAD 1-5: 2.

### VD-02
- TÍTULO: La lectura de la retrospectiva informa las pérdidas sólo OCR únicamente del brazo que decide; las del brazo de producción no se muestran
- ARCHIVO:LÍNEA: `experiments/_s172_retro_paquete/leer_retro.py` l. 1309 y l. 1330 a 1333 (438a60a1e)
- QUÉ PASA: `extra["solo_ocr_que_k_publica"]` se calcula con `brazo` (V-cercano en VIIRS 375). Para radiante sólo se guarda la fila de la regla. En F26 las 3 pérdidas sólo OCR de radiante son N-3 y no habrían cambiado nada. Pero la lectura no deja ver, para el brazo que va a producción, ni esas pérdidas ni las de DM.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python vd1_cercano_vs_radiante.py ...` (sección 6) da F26 radiante 3 pérdidas OCR y cercano 0; `vd5_lectura_retro_v375_salida.txt` muestra `solo_ocr_que_k_publica: []` y el bloque `radiante` sin ese campo.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2.

### VD-04
- TÍTULO: Las 5 «protegidas perdidas» de VIIRS 375 tienen una referencia de MIROVA débil o contradictoria
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `vd3_filas_ocr_cinco_salida.txt`
- QUÉ PASA: las 3 de marzo traen `Distancia_km` 0.0, de un OCR anterior a la calibración de distancia. Las 2 de octubre traen distancia complementaria «ambiguo», con máximo 22.9 y 20.19 km. La vía pone su cúmulo más radiante a 22.78 y 18.99 km. En Isluga 2026-10-03 05:18 la tabla tiene en el mismo minuto una fila «VIIRS» RUTINA con 0.0 MW. No está comprobado que esa fila sea de VIIRS 375 y no de 750 (el CSV no trae el satélite). Es posible que MIROVA haya visto la misma fuente lejana que la vía, y entonces no hay pérdida.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python vd3_filas_ocr_cinco.py D:\vrp-trabajo\temporales\s179-audit\d\base\latest_consolidado.csv D:\vrp-trabajo\temporales\s179-audit\d\base\data\mirova_reference\mirova_v1_snapshot\registro_vrp_ocr.csv`
- CONFIANZA: CONFIRMADO lo que dicen las filas; SOSPECHA la lectura (que MIROVA miró la fuente lejana). Para decidirlo hay que mirar la imagen de MIROVA de cada pasada.
- GRAVEDAD 1-5: 2.

## 5. SEGUIMIENTOS (fuera de mi eje)

- La autorización de la sombra de los 34 descansa en una frase interpretada («Se lee como sí», bitácora l. 1602 a 1604), que además abrió una excepción al congelamiento de `pipeline/grillas_mirova.yaml`. Confianza: CONFIRMADO que es interpretación.
- Fecha del «Sí, prepáralo»: el plan de los 34 dice «2026-11-01» (l. 21) y la bitácora «2026-11-02 00:30 UTC» (l. 1621). Probablemente una es hora de Chile. Confianza: SOSPECHA, menor.
- Conflicto tabla contra OCR en Isluga 2026-10-03 05:18 (VD-04): si la fila RUTINA de la tabla es de VIIRS 375, la unión de la referencia etiqueta protegida una pasada en que la tabla dice que MIROVA no vio nada. `scripts/referencia_mirova_unificada.py`. Confianza: SOSPECHA.

## 6. VERIFICADO LIMPIO

- Copia de datos del auditor igual a 438a60a1e: `sha256sum` de las dos referencias contra el preámbulo, y `git show 438a60a1e:data/mirova_equivalent/{Isluga,Lascar}.json | sha256sum` contra la base (80b7c996..., 57eebc52...). Vara: el preámbulo.
- B1 y #983 no cambian código de `pipeline/`: `git diff --stat 557dbd05d bbbe2068d` y `git diff --stat 438a60a1e e68819484 -- pipeline/` (sólo `pipeline/profiles/*.yaml`). Vara: «el merge ES el encendido» (bitácora l. 643).
- En MODIS y VIIRS 750 la retrospectiva decide con el brazo `V` (radiante), el mismo que escribe producción: `leer_retro.py` l. 1274 y `--posicion-v750` por defecto «radiante» (l. 1389); lectura: `MODIS_brazo: V`, `VIIRS750_brazo: V` (`vd5`). El desacuerdo de posición es sólo de VIIRS 375.
- Scripts del auditor m3 y m3b: corren y reproducen exactos sus números (`rerun_m3_salida.txt`, `rerun_m3b_salida.txt`), con sus controles de base en OK. Comprobé con `find -newer` que no escribieron en la instantánea compartida `D:\vrp-trabajo\temporales\s179-audit\main\`.
- El plan #981 vigente es `62ccb8830`: `headRefOid` de `insumos\pr_981.json` y `git log origin/claude/s178-plan-reemplazo`.

Comandos (desde `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\vd\`, con `T=/d/vrp-trabajo/temporales/s179-audit`):
- `python vd1_cercano_vs_radiante.py $T/main $T/d/base /c/Users/nmend/vrp-temporales/s177_d2 /c/Users/nmend/vrp-temporales/s177_d4 $T/vd vd1_cercano_vs_radiante_salida.json` (necesita `$T/vd/lp.py` = `git show 438a60a1e:experiments/_s172_retro_paquete/reglas/leer_posicion_v375e.py`)
- `python vd2_processed_utc.py /c/Users/nmend/vrp-temporales/s177_d2 /c/Users/nmend/vrp-temporales/s177_d4`
- `python vd3_filas_ocr_cinco.py $T/d/base/latest_consolidado.csv $T/d/base/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`
- vd4: búsqueda con `re.finditer(r'(?i)(radiante|cercano|posici)', body)` sobre `insumos/pr_974.json` y `pr_983.json`
- vd5: `git show ff8a39972:experiments/_s178_lectura/lectura.json`, campo `sensores.VIIRS375`
- `python ../d/m3_vigilancia_tras_reemplazo.py $T/main $T/d/base $T/vd/sim_modis rerun_m3_salida.json` y lo mismo con `m3b` y `$T/vd/sim_viirs`

## 7. SIN DATO

- Si la vía reprocesada calla alguna protegida en las noches entre el 2026-11-08 y el merge de B1 (VD-01): ese reproceso no existe todavía.
- Qué deja de publicarse en P4 (enero, abril a septiembre y 2026-10-17 a 11-09): los artefactos de P4 no están bajados.
- Si Nicolás dio de palabra el sí a #972 fuera de la bitácora y del PR: la vara sólo acepta lo registrado.
- Las imágenes de MIROVA de las 5 pasadas (VD-04).

## 8. FUERA DE ALCANCE

- Posición en VIIRS 750 (la decide V750-A, no sellado) y su encendido (#983).
- La corrección de los 3 huecos del plan #981 que ya anotó su verificador (tercera regla del script, desfase con main, tope de 1 GB de Pages).
