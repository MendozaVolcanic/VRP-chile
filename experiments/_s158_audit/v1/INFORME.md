# V1, verificador con contexto limpio: hallazgos F1 y F6 de la auditoría S158 contra el código de MIROVA (VIIRS 750)

Rama `s158-d17-diseno`, commit `56ec42c6b`, 2026-10-21. No leí los informes de F1 ni de F6. Usé dos piezas
de F1 como instrumento, después de leerlas: `f1/predicado_tablero.js`, que extrae el predicado de publicación de
`frontend/index.html` y lo corre con node (A97), y el oráculo `experiments/_s158_oraculo_mirova/mirova_v750.py`.
Las mediciones son scripts míos, todos en esta carpeta, cada uno con su `_salida.txt`.

**Ventana K** en todo lo que sigue: observaciones desde el 2026-09-18 00:00 UTC hasta el último record
(2026-10-21 06:48 UTC). Referencia: tabla `latest_consolidado.csv` más el OCR de
`data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`, con `Sensor == "VIIRS"` (750 m). Antes de usarla
corrí `calidad_referencia_mirova.avisar("2026-09-18", "2026-10-21")`: avisa por dos tramos del OCR (Suomi NPP antes
del 2026-10-09, y ALERTA_SIN_GEOMETRIA_OCR desde el 2026-10-10). Por eso separo la lectura A (sin SIN_GEOMETRIA)
de lo demás.

## Tabla de veredictos

| hallazgo | veredicto | mi gravedad | por qué |
|---|---|---|---|
| F1-H1 fondo escalar del VRP | **CONFIRMADO, CON MATIZ** | **4** | Con los mismos 5 píxeles de Etna: 2,748 MW contra 9,881 (razón 0,278). La causa es el fondo, no el recorte: sin recorte da 2,600, así que el recorte **sube** el valor un 6 %. En datos reales de K, la cara grave es otra: 30 records de cumbre detectados que se publican en 0, y 7 de ellos son alertas de MIROVA (V1-1) |
| F1-H2 VIIRS 750 diurno rechazado | **CONFIRMADO, CON MATIZ** | 3 | Las 3 alertas protegidas diurnas de Chillán se reproducen exactas. Hay una cuarta, del OCR (12 MW, sin geometría, que el scraper marca como posible artefacto). Es una divergencia conocida y abierta (D-10, A/B pendiente). En la unidad del operador, cada uno de esos días Chillán tuvo entre 1 y 5 pasadas V750 nocturnas publicadas en las 24 h previas |
| F1-H3 círculo contra caja de 7 × 7 | **CONFIRMADO el conteo; REFUTADA la premisa** | 2 (en lo que sí hay) | Los 15 de 67 se reproducen, todos de Cordón Caulle. Pero 50 de las 51 alertas V750 de MIROVA en Cordón Caulle (tabla completa) caen a 7,65 a 8,55 km de su referencia, o sea **fuera** de una caja de 7 × 7 centrada en la grilla: la caja de MIROVA para este volcán no es la del ejemplo, y el código permite moverla. 7 de los 15 están en el cráter, justo donde alerta MIROVA. Los otros 8 (cúmulo a 9,9 a 19 km del cráter) caen donde MIROVA nunca publicó una alerta V750. Eso sí es sobre-publicación, y la causa es el `inner_radius_km = 20`, no la forma de la caja |
| F1-H5 compuerta `bt > t_bg + 3 K` | **CONFIRMADO, AGRAVADO** | 3 | 19 de 67 publicados de K salen sólo del segundo pase, y en los 19 todos los píxeles tienen `bt <= t_bg + 3 K` (control: 0 de 48 en los que sí tienen primer pase). Con `conditioned=True` y la máscara activa vacía, el segundo pase devuelve vacío (`detection_context.py:906`). Agregado mío: 8 de esos 19 son alertas de MIROVA, **3 protegidas** (Chillán 2,66, 2,48 y 2,47 MW). Condicionar el segundo pase sin sacar la compuerta las apaga |
| F1-H7 5 alertas sin detección | **CONFIRMADO** | 3 | Las 5 son de la tabla, con record nuestro de 0 píxeles a menos de 2 s de diferencia. Una es protegida: Cordón Caulle 2026-10-10 05:54, NOAA-21, 1,19 MW. En ese record el máximo de la ROI está a +9,7 K sobre el fondo, así que la compuerta no explica la pérdida (mecanismo SOSPECHA). Fundido con V1-1: en K se pierden 11 de 19 alertas Muy Bajo; 4 son estas y 7 son ceros del VRP |
| F6-1 VRP del OSF sobre 50° de cenit | **CONFIRMADO** | 3 | 8.239 de 34.250 filas V750 sobre 50° de cenit (24,1 %); mediana de la razón 0,508; 0 de 66.391 filas en o bajo 50°. Con el k propio de cada sensor, VIIRS 375 y MODIS cumplen la identidad en el 100 % de las filas, sobre 50° también. Villarrica 2023-11-27 06:18 se reproduce: 77,11 contra 153,85 MW. No es una ley del cenit: dentro del escalón la razón no sigue el coseno (rango intercuartil 0,59) y sólo una de cada cuatro filas se desvía. Lo que decide cuáles, no lo sé |
| F6-2 ningún resultado publicado prueba los umbrales | **CONFIRMADO, CON MATIZ** | 2 | Los 5 píxeles de Etna están en la clase 2 del BOX (la caja central de 7 × 7, filas y columnas 30 a 36); 0 alertas absolutas. Matiz: el OSF V750 no es «sólo de noche». Trae noche desde 5 MW y día desde 50 MW (global y Chile). Ninguna fila bajo 5 MW, así que ninguna pone a prueba un umbral débil |

Duplicados fundidos: F1-H7 con V1-1 (las dos son pérdidas de alertas Muy Bajo de VIIRS 750 en K), y F1-H1 con V1-1
(el cero del VRP es la consecuencia operacional de H1).

## Detalle por hallazgo

### F1-H1. El VRP de VIIRS 750 usa un fondo escalar del anillo de 5 a 25 km; MIROVA interpola un fondo local
- **Fuente leída**: `pipeline/process_viirs_mod.py:560` (`t_bg` = `compute_bg_stats`, que es la mediana,
  `detection_context.py:1083`, sobre el anillo `dist` 5 a 25 km, l. 539), `:1041` (`L_bg_rad` = Planck de ese
  escalar), `:1056` (`delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`). `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False`
  leído de `pipeline.profile`. MIROVA: `MIROVA_VIIRS750_VRP.m:63-85`, que enmascara las alertas, dilata (3, 5 o 7
  según `npix`), interpola con `fillmissing2` y resta sin recortar.
- **Fenómeno**: en una cumbre fría el anillo de 5 a 25 km es flanco bajo y más tibio. En Etna la mediana de L_M13
  sube con la distancia: 0,228 (1 a 3 km), 0,263, 0,314, 0,331, 0,353, 0,365 (20 a 25 km). El fondo escalar
  (0,346) queda 61 % sobre el fondo local de MIROVA bajo los píxeles (0,215).
- **Medición**: `v1/h1_fondo_etna.py` → `h1_fondo_etna_salida.txt`. Mismos 5 píxeles que alerta el oráculo:
  MIROVA 9,8809 MW; nuestra fórmula 2,7482 MW (razón 0,2781); sin recorte 2,5999. **Control positivo**: nuestro k
  (19,7 × 562.500 = 11.081.250) con el fondo de MIROVA da exactamente 9,8809, así que k y área son iguales y toda la
  brecha es el fondo. Barrido de intensidad, sólo magnitud y con los píxeles que MIROVA alerta en cada nivel: con
  f = 0,3 y 0,2 MIROVA da 2,881 y 1,881 MW (protegidas) y nuestra fórmula **0,000**, con los 5 de 5 píxeles bajo el
  fondo. Supuesto declarado: grilla de 750 m, porque producción corre en barrido nativo (D17).
- **Cómo podría estar mal**: (a) que el detector nuestro no alerte esos píxeles. La medición aísla la fórmula a
  propósito, y lo que alerta nuestro detector es otro hallazgo. (b) Que Etna no se parezca a Chile. Por eso medí K
  (V1-1): la razón publicado/MIROVA en 35 alertas nocturnas de la tabla es de mediana **0,41** (IQR 0,19 a 0,70;
  `recall_k_salida.txt`), en la dirección que predice H1, aunque esa razón también carga la diferencia de detección.
- **Dashboard**: magnitudes de VIIRS 750 bajas en cumbres frías (Chillán 0,41 de mediana sobre 28 pareos), y
  detecciones débiles que se publican en 0, es decir invisibles.
- **Matiz al enunciado**: el recorte no es parte del problema. En Etna sube el valor (+6 %), y en un cero no cambia
  nada, porque un exceso negativo tampoco se publicaría. El defecto es el fondo escalar.

### F1-H2. VIIRS 750 diurno rechazado
- **Fuente**: `pipeline/store.py:203-224` (`_reject_daytime`: de día rechaza salvo flag), llamado en
  `store.py:637-645`; `ENABLE_DAYTIME_VIIRS = False`. MIROVA: rama diurna en
  `MIROVA_VIIRS750_hotspot_detection.m` §5 (`dayflag ~= 0`: K1 -0,5, 15σ, mínimos 0,02).
- **Medición**: `v1/cruce_v750_k.py` → `cruce_v750_k_salida.txt`. 62 alertas V750 de MIROVA en K (tabla y OCR,
  sin duplicar por volcán y minuto): 58 nocturnas y 4 diurnas, ninguna con record nuestro. Las de la tabla son
  Chillán 2026-10-01 18:42 (3,71 MW), 2026-10-10 18:18 (3,33) y 2026-10-18 19:06 (2,49), con elevación solar de 47
  a 53°. La cuarta es OCR 2026-10-14 18:42, 12,00 MW, `ALERTA_SIN_GEOMETRIA_OCR`, que el scraper anota como
  «CANDIDATO A ARTEFACTO». **Control**: 58 de 58 nocturnas sí tienen record a 8 min o menos.
- **Unidad del operador**: `v1/h2_noches.py`. En las 24 h previas a cada alerta diurna perdida hubo 3, 5, 1 y 4
  pasadas V750 nocturnas publicadas de Chillán. El volcán no queda sin señal. Lo que se pierde es la pasada de la
  tarde.
- **Matiz**: es la decisión D-10 (`docs/MIROVA_DIVERGENCES.md:2839`), cableada y apagada, con A/B pendiente. No
  es un defecto escondido. Lo nuevo son los tres casos protegidos con fecha. Gravedad 3, no 4, por la unidad noche
  (A94).

### F1-H3. Región sensible: círculo de `inner_radius_km` contra caja de 7 × 7
- **Fuente**: `pipeline/detection_context.py:299-325` (`roi1_summit_mask`: `dist_km <= inner_km`), con
  `ENABLE_ROI1_BOX_PAPER = False`. En el BOX del ejemplo de MIROVA la clase 2 es la caja central de 7 × 7 (filas y
  columnas 30 a 36, 49 celdas) y la clase 1 es un rectángulo de 21 × 19 sin esa caja (350 celdas). El código da los
  umbrales sensibles a la clase 2 (5σ, 0,003) y los conservadores a las clases 1 y 0 (10σ, NTI 0,02, ETI 0,01). Y
  dice explícitamente que **las ROI se pueden mover, cambiar de forma o de tamaño por volcán**
  (`.m`, comentario del §2).
- **Medición**: `v1/h3_caja.py` → `h3_caja_salida.txt`. 67 publicados V750 en K (predicado del tablero con node).
  Los 15 con todos sus píxeles fuera de una caja de ±2,625 km alrededor de `mirova_center` son de Cordón Caulle.
  **Control**: los 52 de los otros 6 volcanes tienen al menos un píxel dentro. Ninguno de los 15 está truncado a
  100 píxeles.
- **Por qué la premisa no se sostiene**: en toda la tabla, MIROVA publicó 51 alertas V750 de Cordón Caulle. Sus
  `Distancia_km` van de 2,25 a 8,55 (mediana 7,83), y sólo **1 de 51** queda dentro de la diagonal de la caja
  (3,71 km). El cráter está a unos 7,6 km de `mirova_center` (−40,5903, −72,1187 contra −40,5255, −72,1461). O sea
  que MIROVA alerta en el cráter, fuera de la caja por defecto. Entonces o movió la ROI para este volcán, o alerta
  igual con los umbrales conservadores. En cualquiera de los dos casos, «fuera de la caja del ejemplo» no quiere
  decir «MIROVA no lo publicaría».
- **Lo que sí queda**: de los 15, 7 tienen el cúmulo a menos de 1 km de nuestro cráter, a 7,4 a 8,3 km del centro,
  en el mismo lugar que las alertas de MIROVA. Los otros 8 tienen el cúmulo a 9,9 a 19,0 km del cráter (2026-09-21,
  09-22, 09-26, 09-29, 10-04, 10-07, 10-10 04:54 y 10-21 05:48), donde MIROVA nunca publicó una alerta V750 (máximo 8,55 km). Esa
  sobre-publicación sale del radio de 20 km del KML, que pone esos píxeles bajo umbral sensible. El operador ve
  alertas «de cumbre» de Cordón Caulle a 10 a 19 km del cráter. Gravedad 2: Cordón Caulle es una anomalía
  persistente y ya documentada (A20, A68).

### F1-H5. La compuerta del primer pase lo vacía en cumbres frías; el segundo pase rehace la detección sin ella
- **Fuente**: `pipeline/detection_context.py:546` (`gate_bt = bt > t_bg + bt_sanity_k`, `apply_bt_gate` no se pasa
  desde `process_viirs_mod.py`, así que vale el default True); `:958` (`newly_active = pass_2 & pass_3 & finitos`,
  sin compuerta); `:906-907` (con `conditioned` y la máscara vacía devuelve vacío);
  `ENABLE_SECOND_PASS_CONDITIONED = False`. El código de MIROVA no tiene ninguna condición sobre la BT de M13 (§3
  sólo filtra BT de M15 ≤ 200 K).
- **Medición**: `v1/h5_compuerta.py` → `h5_compuerta_salida.txt`. De 67 publicados en K, 19 tienen
  `diag_n_first_pass_pixels == 0` y `diag_n_second_pass_recapture > 0`. En los 19, 0 píxeles superan `t_bg + 3 K`
  (mediana `bt_max - t_bg` = 1,22 K). **Control**: en los 48 con primer pase, los 48 tienen algún píxel sobre la
  compuerta (mediana 16,2 K).
- **Agregado**: `v1/h5_cruce.py` → `h5_cruce_salida.txt`. De los 19, 8 coinciden con alerta de MIROVA, 4 con
  RUTINA y 7 no tienen fila. Tres de las alertas son protegidas: Chillán 2026-10-05 06:48 (2,66 MW), 2026-10-10
  04:54 (2,48) y 2026-10-17 04:42 (2,47). Nosotros publicamos 0,26, 0,24 y 0,22 MW (razón ~0,1, otra cara de H1).
  Encender el segundo pase condicionado sin sacar la compuerta apagaría esas 3 protegidas.

### F1-H7. Alertas V750 de MIROVA sin detección nuestra
- **Medición**: `cruce_v750_k_salida.txt` (bloque «CON RECORD PERO 0 PIXELES») y `recall_k_salida.txt`. Son 5 de la
  tabla, todas con record nuestro a 0 a 2 s de diferencia y 0 píxeles. Cordón Caulle 10-14 06:24 (0,31 MW), 10-10
  05:54 (**1,19**), 09-28 05:36 (0,38); Chillán 10-12 05:54 (0,40) y 09-28 04:42 (0,23).
- **Cordón Caulle 10-10 05:54**: `t_bg` 271,85 K, `t_max` 281,53 K, `sd_dnti` 0,0028, 3.695 píxeles de fondo. En
  algún lugar de la ROI hay un píxel 9,7 K sobre el fondo, así que la compuerta no basta para explicarlo (no sé si
  ese píxel está en el cráter). Con `max` y 5σ, el umbral dNTI de cumbre ronda
  0,014 contra el mínimo de 0,003. **SOSPECHA**: lo que tumbó la detección son los umbrales contextuales. Hace
  falta el gránulo para saberlo.
- **Recall V750 de K** (`recall_k_salida.txt`, nocturnas): protegidas 36 de 39 en total y 30 de 31 en la lectura
  A. Muy Bajo 8 de 19.

### F6-1. VRP del OSF v2.5 para VIIRS 750 sobre 50° de cenit
- **Medición**: `v1/f6_1_cenit.py` → `f6_1_cenit_salida.txt`, y `v1/f6_1_otros_sensores.py`. VIIRS 750, n = 100.641
  (2012-01-19 a 2025-12-31). 8.239 filas fuera de la identidad (|r − 1| ≥ 1e-4), **todas** sobre 50° de cenit: 0
  de 8.084 entre 45 y 50°, y 113 de 485 entre 50,0 y 50,5°. Es un escalón. Mediana de r en las filas fuera: 0,508.
  **Controles**: con k750, 0 filas de VIIRS 375 y 0 de MODIS cumplen la identidad (el instrumento distingue); con
  el k propio, cumplen 252.374 de 252.374 de VIIRS 375 y 262.455 de 262.455 de MODIS, en los dos lados de 50°.
- **Otras explicaciones probadas**: (a) no es una ley continua del cenit (r/cos θ tiene IQR 0,59; la mediana de r casi no sube
  de 50-52° a 65-70°, de 0,45 a 0,54); (b) aparece en los dos satélites, de día y de noche, y en todos los años de 2012 a
  2025; las filas fuera tienen el doble de píxeles (mediana 19 contra 10). Lo que decide cuáles de las filas sobre
  50° se desvían **no lo sé**. Villarrica 2023-11-27 06:18, NOAA-20, 50,51°, 17 píxeles: OSF 77,11 MW, código
  153,85 MW.
- **Gravedad 3, no 4**: no tuerce una alerta del NRT por sí solo. Sí invalida cualquier comparación de magnitud
  contra el OSF sobre 50° en VIIRS 750, y dice que el código publicado no es toda la cadena que produjo el OSF. Que
  el NRT (`latest.php`) tenga el mismo factor es SIN DATO.

### F6-2. Ningún resultado publicado pone a prueba los umbrales de detección
- **Medición**: los 5 píxeles de Etna (filas 35 y 36, columnas 32 a 34, en `h1_fondo_etna_salida.txt`) están en la
  clase 2 del BOX (filas y columnas 30 a 36). El oráculo da 0 absolutas, y las 5 alertas salen de la lista
  `alertsROI2` en los dos pases (pase 1 [0, 0, 4], pase 2 [0, 0, 1]; esa salida de diagnóstico es de
  `f1/etna_k_contra_mirova_salida.txt`, que leí y que coincide con mis 5 píxeles). `v1/f6_2_poblacion.py`: OSF V750
  de noche desde 5,0000 MW y de día desde 50,0028 MW (global, n = 100.641); Chile, de noche desde 5,0015 y de día
  desde 50,1279 (n = 2.515). 0 filas bajo 5 MW.
- **Matiz**: el enunciado dice «sólo de noche». No es así: hay 17.859 filas diurnas globales y 215 en Chile, todas
  de 50 MW o más. La conclusión no cambia, porque una población de 5 MW o más no pone a prueba umbrales de señal
  débil, y el OSF no trae información por píxel.

## Hallazgos propios

### V1-1. En K, el VRP de VIIRS 750 deja en cero detecciones de cumbre reales, y es la causa principal de las alertas Muy Bajo perdidas
- **SCRIPT**: `v1/h1_ceros_reales.py` → `h1_ceros_reales_salida.txt`; `v1/recall_k.py` → `recall_k_salida.txt`.
- **Qué pasa**: en un píxel de cumbre fría apenas más tibio que su entorno inmediato, la BT queda bajo la mediana
  del anillo de 5 a 25 km. El exceso sale negativo, se recorta a 0 y el cúmulo se publica en 0 MW.
  En K (n = 118 records V750 con píxeles), 51 se publican en 0. De esos, 30 son `summit` con `pc.vrp_mw == 0`, y en
  los 30 **todos** los píxeles tienen `bt <= t_bg`. Por volcán: Láscar 12, Isluga 11, Planchón-Peteroa 3,
  Tupungatito 2, Chillán 1, Cordón Caulle 1. **7 de los 30 son alertas de MIROVA en la misma pasada** (0,09 a 0,36
  MW: Isluga 09-20 y 10-12, Láscar 09-20, 09-21, 09-22 y 10-08, Chillán 10-01 04:42). De las 11 alertas Muy Bajo
  nocturnas perdidas en K, 7 son esto y 4 son F1-H7.
- **Dashboard**: invisible. El pipeline detectó el cráter y el tablero no muestra nada.
- **Reproducir**: `node experiments/_s158_audit/f1/predicado_tablero.js data/mirova_equivalent experiments/_s158_audit/v1/pub_v750.json <Vol:inner ...>`,
  después `python -B experiments/_s158_audit/v1/cruce_v750_k.py`, `h1_ceros_reales.py` y `recall_k.py`. Caso:
  Láscar 2026-10-08 05:42, VIIRS_NOAA20_750, MIROVA 0,36 MW.
- **Confianza**: CONFIRMADO el conteo y que todos los píxeles quedan bajo `t_bg`. SOSPECHA que con el fondo local
  de MIROVA esos 7 darían más de 0, porque el mecanismo es el que muestra Etna. Para afirmarlo hace falta el
  gránulo.
- **Gravedad 3**: son alertas Muy Bajo, que pesan lo mismo que una publicación de más. Láscar e Isluga pierden su
  señal débil persistente.

### V1-2. (Conocido, no nuevo.) La relectura del código confirma tres divergencias ya catalogadas
Leído en `MIROVA_VIIRS750_hotspot_detection.m` contra `pipeline/`. (a) La alerta absoluta (NTI > −0,7 de noche, sin
compuerta) es parte del conjunto de alertas y sale de la población de fondo. En nosotros, el primer pase reemplaza
la máscara (`process_viirs_mod.py:904`) y `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`. (b) Fuera de la región sensible, MIROVA
usa mínimos de 0,02 en dNTI y 0,01 en dETI; nosotros, 0,010 en los dos (`process_viirs_mod.py:891-893`,
`DNTI_CONTEXTUAL_C1_SCENE = 0.01`). El de dNTI es la mitad del de MIROVA. (c) El contraste de MIROVA es contra la media
de 3 × 3 con el central; el nuestro, contra los 8 vecinos. Las tres están en `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`
(filas 1, 2 y 3 de la tabla de la l. 107). No las cuento como hallazgo nuevo.

### V1-3. (Latente, flag apagado.) El K1 diurno de VIIRS no es el del código
`NTI_K1_DAY = -0.6` (de `pipeline.profile`); el código de VIIRS 750 usa −0,5 de día (§5). Hoy no actúa
(`ENABLE_DAYTIME_VIIRS = False`, y la alerta absoluta tampoco entra a la máscara, V1-2a). Le importa al A/B diurno
de D-10. CONFIRMADO por lectura. Gravedad 1.

## VERIFICADO LIMPIO
- **Coeficiente y área del VRP de VIIRS 750**: el nuestro (`WOOSTER_COEFF = 19.7`, `process_viirs_mod.py:66`, área
  fija de 562.500 m², `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True`) da k = 11.081.250, igual al de MIROVA
  (1,97e7 × 0,5625). Con el mismo fondo reproduce 9,8809 MW (`h1_fondo_etna_salida.txt`).
- **Oráculo**: 5 píxeles y 9,8809 MW en Etna, el control del README (`h1_fondo_etna_salida.txt`, primera línea).
- **Conectiva y umbrales de cumbre**: `combinar = max` (`detection_context.py:525`, `ENABLE_TESTS_23_PROSE_BRANCH =
  True`) es la misma `max(μ + Nσ, mínimo)` del código. 5σ y 0,003 en la región sensible, y 10σ y ETI 0,01 fuera,
  coinciden. Sólo difiere el mínimo de dNTI fuera (V1-2b).
- **Ingesta de VIIRS 750 en K**: 58 de 58 alertas nocturnas de MIROVA tienen record nuestro a 8 min o menos
  (`cruce_v750_k_salida.txt`). No hay huecos de descarga ni de proceso en esta ventana.
- **Lógica del rechazo diurno**: de noche nunca rechaza; de día rechaza VIIRS sólo con el flag apagado
  (`store.py:203-224`, leído). Coincide con D-10.
- **Identidad del OSF fuera de VIIRS 750 sobre 50°**: 100 % de las filas de VIIRS 375 y MODIS con su k, y 100 % de
  las de VIIRS 750 en o bajo 50° (`f6_1_*_salida.txt`).
- **Predicado del tablero**: `predicado_tablero.js` corre el JS real de `frontend/index.html`. Da 28.581 records V750
  evaluados y 1.764 publicados en toda la historia, y 67 en K, el mismo número que F1.

## Lo que no pude verificar
- Qué BOX usa MIROVA para cada volcán chileno: no está publicado. En Cordón Caulle el dato de sus alertas descarta
  la caja por defecto centrada en la grilla.
- Si los 7 ceros de V1-1 y las 5 pérdidas de F1-H7 se resolverían con el fondo local o con los umbrales del código.
  Hace falta correr el oráculo sobre esos gránulos, remuestreados a la grilla de MIROVA.
- Qué decide cuáles de las filas V750 del OSF sobre 50° llevan el factor ~0,5, y si el NRT lo tiene.
- Las 7 pasadas «sin fila» de MIROVA en `h5_cruce_salida.txt`: no sé si MIROVA no procesó esos gránulos o si es una
  diferencia de hora mayor a 8 min.
