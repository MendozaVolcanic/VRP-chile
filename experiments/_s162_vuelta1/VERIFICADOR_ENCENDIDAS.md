# Verificación de las «encendidas» de D25 en VIIRS 750 (S162, vuelta 1)

- Hora del servidor: inicio `Sat, 24 Oct 2026 13:48:25 GMT`, cierre `Sat, 24 Oct 2026 14:00:34 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit medido: tag `s157-d25-k-codigo` = `66961f65d261d8ea4197c2e4985edab7fd052b8e`. Los 22.758 records de los brazos (V1, V2a, V2b; K y D) llevan `regimen.codigo_sha` = 66961f65d (recup_dist_salida.txt, última línea). El tablero: `frontend/index.html` de ese commit (blob `85a0bd8d`, idéntico al que usó el evaluador en s159-evaluador; la diferencia de sha256 f711c61d contra b287eb68 es sólo CRLF, `diff` con `tr -d '\r'` da 0 líneas).
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo asignado por quien orquesta.
- Caminos escritos ANTES de releer datos: `caminos.md`, sha256 `985229b0162035377cb16c9d9c1983124f85993c6a335ce89bdf311c1a655225`.
- Ventanas y denominadores: V1 2026-08-29 a 2026-10-18 SIN 13, 17 y 18 de octubre (D-29); V2 2026-04-01 a 2026-06-12 (V2a+V2b, sin claves duplicadas). 11 volcanes Tier A. Los brazos no traen MODIS (`SENSOR_MODIS: false` en FLAGS_BRAZO).
- Qué NO miré: el gemelo K' (G); P1, P1b, M y el resto del veredicto; la regla SN en VIIRS 375 más allá de la afirmación 3; MODIS de producción (no está en los brazos); los GeoTIFF de MIROVA (ninguna posición con acimut); el código de Mirova-v1. No corrí el pipeline: todo sale de los records persistidos y del código leído en el tag.

Todos los scripts y salidas están en `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta1\verificador_encendidas\`. El código del tag se extrajo con `git archive 66961f65d pipeline volcanoes.yaml` a `src\` y los flags se leyeron con `pipeline.profile` (A89), no del YAML.

## En una pantalla

1. Las pasadas de VIIRS 750 que D publica y K no son **126** con las exclusiones de D-29 (V1 44, V2 82); el «127» sale sólo si se cuenta una pasada del 2026-10-17 (Tupungatito, sin_info), día que el evaluador excluye.
2. El mecanismo está confirmado en código y datos: cúmulo de 1 píxel, 0,0 MW en K (píxel más frío que la mediana del anillo en 125 de 126), primer pase vacío en 125 de 126, segundo pase sin condicionar, y **D publica el 100 % de los cúmulos de cumbre que K deja en 0 MW** (126 de 126): no selecciona nada.
3. Recuperadas y encendidas no se separan (mejor AUC 0,682, p corregido por barajado 0,146 sobre 49 variables), pero la prueba sólo tiene poder para separaciones fuertes (81 % con AUC 0,75; 44 % con 0,70).
4. Los números de la afirmación 3 se reproducen (32/37 con tabla y OCR; 37/37 con 375 del mismo barrido a 0,30 km), pero no distinguen encendidas de recuperadas (33/33 y 29/33) ni son independientes (A109); y en 29 de 37 MIROVA alertó en 375 en la **misma** pasada en que su 750 dijo RUTINA.
5. Una «recuperada» (Puyehue 2026-04-30 06:06, V2) es otro objeto: nuestro píxel está a 24,5 km del centro de MIROVA y su alerta a 7,83 km; y hay 9 publicaciones de D sobre pasadas RUTINA que P2 no cuenta.

## Veredictos

### Afirmación 1: mecanismo común de las 127 pasadas
**CONFIRMADO EN PARTE. Gravedad 2.**

Lo que se sostiene (af145_salida.txt, recorte_salida.txt, dist_salida.txt):
- Conteo: 126 sin los días de D-29, 127 con ellos (la extra: `Tupungatito|VIIRS750|2026-10-17 05:24`, sin_info, D 0,274 MW). El evaluador da 44 + 82 = 126 en el estrato 203 (v1.log l. 83, v2.log l. 108). El «127» mezcla un día excluido.
- `pc.n_pixels` = 1 en 126 de 126, en K y en D; `single_pixel_mode` True en 126; `distance_class` summit en los dos brazos; centroide idéntico en K y D en 126 de 126.
- Primer pase vacío (`diag_n_first_pass_pixels` = 0) en 125 de 126 (126 de 127 con el día excluido, como dice la afirmación). La excepción es `Lascar|VIIRS750|2026-05-28 05:36` (V2), con 1 píxel en el primer pase que no es el del cúmulo. Control positivo del campo: en las 279 pasadas V750 que K sí publica, el primer pase tiene píxeles en 171, así que el campo no está muerto.
- `ENABLE_SECOND_PASS_CONDITIONED` = False en `mirova_equivalent`, `_s157_ab_d25_k_control` y `_s157_ab_d25_k_on`, leído con `pipeline.profile` en el tag (la clave está en `profile.py:428`). El segundo pase (`detection_context.py:822` en adelante) no tiene condición de temperatura: con primer pase vacío equivale a los Tests 2 y 3 sin la compuerta.
- `detection_context.py:546` en el tag es `gate_bt = (bt > t_bg + bt_sanity_k) if apply_bt_gate else np.isfinite(bt)`, con `NTI_BT_SANITY_K` = 3,0 y V750 llamando con el default `apply_bt_gate=True` (`process_viirs_mod.py:882`). En 125 de 126 el píxel tiene `bt <= t_bg` (mediana bt − t_bg = −1,5 K, mín −6,3): la compuerta lo rechaza seguro. Control: en las 284 pasadas V750 de K con cúmulo de cumbre y magnitud > 0, bt − t_bg es positivo en las 284 (mín +0,12 K).
- `process_viirs_mod.py:1056` en el tag es `delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`: el recorte. `pc.vrp_mw` de K = 0,0 en 126 de 126. En D, `diag_L_bg_vecinos` < `diag_L_bg` (anillo) en 126 de 126: los vecinos son más fríos que el anillo, el exceso queda positivo.
- `index.html:1595` en el tag es `function isValidDetection(r)`, que con cúmulo devuelve `(pc.vrp_mw ?? 0) > 0`; además `mirovaEqVrp` devuelve 0. Mi predicado con node publica 0 en las 126 en K. D: 0,167 a 0,603 MW (`pc.vrp_mw` y lo que muestra el tablero coinciden), mediana 0,34.

Lo que no se sostiene tal cual:
- «Junto al cráter»: 110 de 126 a 1 km o menos y 122 a 2 km o menos, pero `PuyehueCordonCaulle|VIIRS750|2026-04-30 06:06` está a **17,64 km** del cráter (dentro del inner de 20 km, por eso es summit). Ver VE162-01.

Fenómeno: es la cumbre fría vista a 750 m. El píxel está más frío que el valle (el anillo de 5 a 25 km) pero más tibio que sus vecinos inmediatos; K mide el exceso contra el valle y da cero, D lo mide contra los vecinos y da 0,2 a 0,6 MW.

### Afirmación 2: recuperadas y encendidas no se distinguen
**CONFIRMADO, con alcance limitado por el poder. Gravedad 2.** (af2.py, af2_salida.txt)

- n = 33 recuperadas (pos) y 37 encendidas (neg_limpio), V1 + V2 sin días de D-29.
- 49 variables numéricas no constantes del record K, del record D, del cúmulo y derivadas (t_max − t_bg, L_vecinos/L_anillo, hora, mes); quité las idénticas entre K y D.
- Mejor AUC: `K:sensor_azimuth_deg` 0,682 (p sin corregir 0,014). Nulo **medido** del máximo |AUC − 0,5| sobre las 49, con 2.000 barajados: p95 = 0,207 (AUC 0,707), igual con barajado libre y dentro de cada volcán (los dos nulos no son el mismo arreglo: medias 0,1478 y 0,1500). p corregido del mejor: 0,146 libre, 0,149 dentro de volcán. Ninguna variable pasa.
- Coincide con la afirmación (0,67, no significativo), con otro conjunto de variables (49, no 29) y otra corrección (barajado del máximo, no Bonferroni).
- **Límite que la afirmación no dice**: poder medido inyectando una variable de AUC verdadera conocida: 44 % con 0,70, 81 % con 0,75, 96 % con 0,80, 100 % con 0,85. «No se distinguen» vale para un discriminante fuerte; uno moderado (AUC ≤ 0,70) quedaría invisible con 70 pasadas.
- Control trivial: «volcán = Isluga» da AUC 0,447; la composición por volcán está repartida (Isluga 9/14, Tupungatito 7/12, Láscar 7/5, Planchón 4/4, Puyehue 4/1).

### Afirmación 3: VIIRS 375 la misma noche y el mismo barrido
**CONFIRMADO EN PARTE (los números sí, la lectura no). Gravedad 3.** (af3.py, af3b.py, enc_dist.py y salidas)

Etiquetas: mi etiquetador propio desde los CSV congelados coincide con el del evaluador en las 5.626 pasadas V750 (V1 2.253, V2 3.373, 0 distintas).

Los números:
- «32 de 37»: se reproduce con tabla y OCR en las dos ventanas (32). Con la tabla sola, que es lo que decide en V2, son 31; con tabla sola y regla SN, 30; con tabla y OCR y SN, 32. Noche UTC y noche local (UTC − 12 h) dan lo mismo (32).
- «37 de 37 la VIIRS 375 del mismo barrido publica en K a unos 0,30 km»: CONFIRMADO. Mismo satélite y mismo minuto en 37 de 37; publica en K en 37; distancia entre centroides mediana 0,301 km, p90 0,452.
- Compatibilidad en radio: en las 31 encendidas con alerta 375 de MIROVA (tabla+OCR V1, tabla V2), alguna alerta queda a 1 km o menos en radio desde el centro de MIROVA. Es cota, no identidad (A93, A107).

Por qué la lectura no se sigue:
- **Tasa base**: MIROVA alertó en 375 esa noche en el 28 % de todos los negativos limpios de V750 (946 de 3.323), 50 % en los volcanes de las encendidas (807 de 1.602). Por volcán: Isluga 86 % contra 70 % de base, Tupungatito 92 % contra 52 %. Hay enriquecimiento, pero las **recuperadas dan 29 de 33 (88 %)** y las sin_info 47 de 56: es una propiedad de todo el conjunto, no de las encendidas.
- La 375 del mismo barrido publica en K en 33 de 33 recuperadas y 55 de 56 sin_info, contra 19 % de todos los negativos limpios (34 % en los mismos volcanes). Y por A109 no es evidencia independiente: mismo satélite, mismo instante, misma atmósfera y mismo suelo.
- **MIROVA misma pasada**: en 29 de 37 encendidas MIROVA alertó en 375 en la misma pasada (±2 min) en que su tabla de 750 dice RUTINA. Es decir, el propio MIROVA, mirando el mismo objeto en el mismo instante, alerta a 375 m y calla a 750 m. Que sea calor real es plausible (son fuentes persistentes, categoría b de A54), pero para la réplica la vara es lo que MIROVA publica en 750 (A115), y ahí MIROVA calla.

### Afirmación 4: ninguna noche nueva en el tablero
**CONFIRMADO EN PARTE. Gravedad 2.** (af145_salida.txt, sección AFIRMACION 4)

- En 126 de 126 hay otra publicación de K del mismo volcán la misma noche (UTC y local), con cualquier sensor VIIRS. Con MODIS de producción (que los brazos no tienen) sólo podría subir.
- Pero en **7 de 126** la única publicación de K esa noche es la 375 **del mismo barrido** (mismo satélite, mismo minuto): no es «otra pasada» sino el mismo paso del satélite en otra banda. Las 7: Láscar 2026-09-24 05:54, Planchón 2026-10-05 05:48, Villarrica 2026-09-17 05:42 (V1); Láscar 2026-04-02 05:30, Isluga 2026-04-06 05:54, Isluga 2026-06-02 05:42, Planchón 2026-05-17 05:42 (V2). Para el operador la noche ya tiene alerta, así que la afirmación se sostiene en el tablero; pero el apoyo es el mismo gránulo.
- Si se lee «noche nueva en VIIRS 750»: sólo 22 de 126 tienen otra publicación V750 de K esa noche, así que D sí agrega 104 noches-volcán a la serie de VIIRS 750.

### Afirmación 5: D25 no apaga publicaciones de VIIRS 750 ni mueve cúmulos
**CONFIRMADO (sólo VIIRS 750). Gravedad 1.** (af145_salida.txt, sección AFIRMACION 5)

- 5.626 pasadas V750: K publica y D no, 0; ambos publican, 279, con centroide movido más de 0,01 km en 0 y `n_pixels` distinto en 0; ninguna pasada con cúmulo creado, borrado o movido.
- Control positivo del instrumento: la misma medición en VIIRS 375 ve 4 cúmulos movidos (Tupungatito 2026-09-17 05:24 0,452 km; Isluga 2026-04-12 06:36; Tupungatito 2026-05-09 04:54 y 2026-05-13 05:00), 18 pasadas con cúmulo cambiado y 60 publicaciones nuevas de D. La afirmación es sobre 750 y ahí vale; en 375 D25 sí mueve (fuera del alcance de la afirmación).
- Lo que cambia en 750 es la magnitud de las 279 que ambos publican: razón D/K mediana 1,556 (0,333 a 38,4). No mueve, pero no es inocua para M.

### Qué implica para leer el BLOQUEA de P2 en V1 VIIRS 750

El neto +6 de V1 son exactamente las 16 encendidas menos las 10 recuperadas de un mismo mecanismo que no selecciona (D publica todo cúmulo de cumbre que K deja en 0 MW), así que el BLOQUEA no es ruido de un detector caprichoso sino la tasa con que MIROVA calla en 750 sobre esos píxeles (37 de 70 en total, 16 de 26 en V1), y con p PIERDE 0,16 no es evidencia estadística de que D sea peor. Tampoco es evidencia a favor: para la réplica, D25 cambia alertas débiles recuperadas por al menos tantas publicaciones donde el 750 de MIROVA calla (más 9 sobre pasadas RUTINA que P2 no cuenta, VE162-03), y que esas encendidas sean probablemente calor real no las rescata bajo la vara de la réplica, aunque sí las hace candidatas para el perfil `experimental`.

## Hallazgos propios

### VE162-01: una «recuperada» de D25 es otro objeto, a 17 km del de MIROVA
- SCRIPT:SALIDA: `recup_dist2.py` → `recup_dist2_salida.txt`; `dist_salida.txt`.
- QUÉ PASA: el 2026-04-30 06:06 en Puyehue-Cordón Caulle, MIROVA alertó en 750 (0,41 MW) a 7,83 km de su centro, que queda a 7,57 km de nuestro cráter: es decir, cerca del cráter. El píxel que D publica está a 17,64 km de nuestro cráter y a 24,51 km del centro de MIROVA. La separación es al menos 16,7 km: son objetos distintos, y el evaluador lo cuenta como alerta recuperada porque etiqueta por pasada sin mirar distancia (A107). Las otras 32 recuperadas son compatibles en radio (cota mediana 0,2 km, máx 0,54).
- CÓMO SE VE EN EL DASHBOARD: con D, una marca summit de Puyehue a 17,6 km del cráter (dentro del inner de 20 km) que coincide en hora con una alerta de MIROVA en otro lugar; el operador la leería como confirmada.
- CÓMO REPRODUCIRLO: `python -I recup_dist2.py` en CARPETA; pasada `PuyehueCordonCaulle|VIIRS750|2026-04-30 06:06` (V2).
- CONFIANZA: CONFIRMADO (cota inferior por radios desde el mismo centro; que sea el mismo objeto para las otras 32 queda SOSPECHA, A107).
- GRAVEDAD: 2 (V2 no decide P2 en V1; en V2 cambia el neto de −2 a −1).

### VE162-02: D25 no selecciona en VIIRS 750: publica el 100 % de los cúmulos de cumbre que K deja en 0 MW
- SCRIPT:SALIDA: `af145_salida.txt` («K summit con pc.vrp 0: 126» y «D publica y K no: 126»); `recorte_salida.txt`.
- QUÉ PASA: en la cumbre, el vecino inmediato de un píxel es siempre más frío que el valle del anillo (126 de 126), así que con el fondo por vecinos el exceso nunca es cero: cualquier píxel que el segundo pase sin condicionar deje en la cumbre pasa a publicarse con al menos ~0,17 MW. Las 126 pasadas V750 con cúmulo summit en 0 MW de K son exactamente las 126 que D publica y K no; ninguna queda fuera. La decisión de publicar la toma entonces el segundo pase sin compuerta (D19/D2), no D25.
- CÓMO SE VE EN EL DASHBOARD: con D, una barra de 0,2 a 0,6 MW en VIIRS 750 en cada pasada donde hoy el cúmulo de cumbre queda en cero (Isluga 40, Tupungatito 33, Láscar 28, Planchón 12, Puyehue 10 en las dos ventanas).
- CÓMO REPRODUCIRLO: `python -I af145.py` en CARPETA.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (lo que decide si estas pasadas se publican en la réplica es el segundo pase sin condicionar, no el fondo; mirar D25 solo sobre 750 es mirar el efecto de otra palanca).

### VE162-03: 9 publicaciones de D sobre pasadas RUTINA de MIROVA que P2 no cuenta
- SCRIPT:SALIDA: `sininfo_salida.txt` (campos `rutina_pasada` y `noche_con_alerta_sensor` de la tabla del evaluador).
- QUÉ PASA: de las 56 pasadas sin_info que D publica y K no, 9 (V1 5, V2 4) son pasadas que la tabla de MIROVA lista con RUTINA y 0 MW, en noches donde otra pasada de 750 sí alertó. Quedan fuera de las etiquetas (ni alerta ni negativo limpio), así que no suman al neto. Es el estrato de A118 (c). Otras 39 son pasadas que MIROVA no lista.
- CÓMO SE VE EN EL DASHBOARD: publicaciones de D en pasadas que MIROVA miró y declaró sin anomalía.
- CÓMO REPRODUCIRLO: el `python -I -c` de `sininfo_salida.txt` (lee `pasadas.json` y `conjunto_S.json`).
- CONFIANZA: CONFIRMADO el conteo; si deben contar como error es decisión de la regla (no lo decido).
- GRAVEDAD: 2 (si contaran, el neto de V1 pasaría de +6 a hasta +11; no cambia el sentido de BLOQUEA).

### VE162-04: el «127» incluye un día que D-29 excluye
- SCRIPT:SALIDA: `af145_salida.txt` primeras líneas; `dist_salida.txt` primera línea.
- QUÉ PASA: con las exclusiones del evaluador son 126 (V1 44, V2 82); el 127 suma `Tupungatito|VIIRS750|2026-10-17 05:24`. Lo mismo arrastra el «126 de 127» del primer pase (125 de 126 con D-29).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VE162-05: sospecha de geometría de barrido entre recuperadas y encendidas
- SCRIPT:SALIDA: `af2_salida.txt` (final) y Fisher con scipy en esta sesión (p = 0,016, razón de odds 3,5).
- QUÉ PASA: con el satélite al este del volcán (azimut del sensor < 180°) hay 24 recuperadas y 16 encendidas; al oeste, 9 y 21. Puede ser que el 750 de MIROVA alerte más según el lado del barrido (remuestreo y bow tie, D17). Es post hoc: salió como la mejor de 49 variables y no sobrevive la corrección (p corregido 0,146).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I af2.py` en CARPETA.
- CONFIANZA: SOSPECHA (hipótesis para probar con datos nuevos, no un resultado).
- GRAVEDAD: 1.

## VERIFICADO LIMPIO

| Ítem | Vara | Comando |
|---|---|---|
| Publicación K y D con el predicado literal del tablero del tag | Mi node sobre `index_66961.html` coincide con la tabla del evaluador en 4.610 + 4.610 (V1) y 6.769 + 6.769 (V2) pasadas, 0 distintas; control S139 da `[0,1]` y `[1,0]` como se espera | `python -I cargar.py` (cargar_salida.txt) |
| El tablero que usó el evaluador es el del tag | Mismo blob git `85a0bd8d`; diff sin CR = 0 líneas | `git rev-parse 66961f65d:frontend/index.html` y en s159-evaluador |
| Etiquetas del evaluador en V750 | Etiquetador propio desde CSV congelados: 5.626 de 5.626 iguales | `python -I af3.py` (primera parte) |
| Código que escribió los records | 22.758 records con `codigo_sha` 66961f65d | `python -I recup_dist.py` (última línea) |
| Flags de los brazos | `pipeline.profile` del tag: COND False en los tres perfiles; neighbor mean V375/V750 sólo en `_on`; Test 1 apagado | `git archive` + `VRP_PROFILE=... python -c "import pipeline.profile"` |
| Pasadas diurnas | cenit solar mínimo 124,5° en las 126: todas nocturnas | af145_salida.txt |
| «Mismo barrido» | 37 de 37 mismo satélite (sensor 375 + `_750`) y mismo minuto | af3_salida.txt |
| Regla SN contra original en V750 | No cambia el estrato 203 (v1.log l. 83 y l. 213: 44, 10, 16, 18 en las dos) | `grep -n "estrato 203" v1.log` |
| Recuperadas y encendidas de V1 = discordantes de P2 V750 | 10 + 16 = 26 discordantes, neto +6 (v1.log l. 53) | af145_salida.txt «etiqueta x ventana» |
| Segundo pase sin compuerta de BT | El cuerpo de `second_pass_adjacent` (`detection_context.py:822` en adelante) no usa `bt` ni `t_bg` | `awk 'NR>=900 && NR<=1010' src/pipeline/detection_context.py \| grep -n "bt\|t_bg"` |
| D25 no toca VIIRS 750 fuera del estrato | 0 apagadas, 0 movidas en 5.626, con control positivo en 375 | af145_salida.txt |

## SIN DATO

- Si las encendidas son calor real: no hay posición con acimut de MIROVA (GeoTIFF) ni SWIR de alta resolución mirados; los radios compatibles no identifican el objeto (A107).
- Si un discriminante moderado (AUC ≤ 0,70) separa recuperadas de encendidas: el poder con 70 pasadas es 44 %; no se puede afirmar ni negar.
- Afirmación 4 con MODIS de producción: los brazos no traen MODIS; sólo puede reforzar la afirmación.
- Por qué el 750 de MIROVA calla donde su 375 alerta en la misma pasada (29 de 37): no tengo el código ni los umbrales del 750 de MIROVA en esta sesión.
