# Verificacion de la investigacion VIIRS 375 en Tupungatito (cenit, K y via V375-E)

## 1. Encabezado

- Fecha y hora del servidor (cabecera `Date` de api.github.com): **2026-11-03 02:44 a 02:59 UTC** (inicio y fin de las mediciones).
- Commit medido: la copia del auditor `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/repo` (COMMIT_MAIN.txt: `f20495d374`), comprobada **identica a `origin/main` `f20495d374`** salvo CRLF en los 9 archivos que usan los scripts (Tupungatito.json, los dos CSV de la referencia, banco_paridad.py, clase_mirova.py, mirova_v750_codigo.py, process_viirs.py, index.html, volcanoes.yaml; sha256 tras `tr -d '\r'`). El checkout de trabajo esta en `loop/activo` `b9da9adb0`, cuyo Tupungatito.json difiere del de main: no lo use.
- Modelo: Claude Fable 5.1. Esfuerzo: el despacho no me paso un nivel explicito y no puedo leerlo desde adentro; lo declaro SIN DATO.
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_tupun375/` (caminos.md sellado antes de abrir nada; scripts `v01` a `v06`; re-corridas `r01` a `r06`).
- Que NO mire: el INFORME.md del auditor (a proposito; recibi solo los 5 enunciados del encargo y su hallazgos.csv); otros informes de verificadores; la sombra prospectiva de V375-E; MODIS y VIIRS 750 de Tupungatito (s01 los lista, n_pares 0 y 2, fuera de mi eje); el predicado del tablero en si (lo ejecute via node con banco_paridad en r01 y lo aproxime a mano en v01; no audite index.html); los PNG de MIROVA (no abri imagenes); el porque fisico de la fuente a 9 a 25 km (no es mi eje).
- Procesos pesados: uno a la vez (r01, r03, r05, v03 en serie). Disco al cierre: C: 26,8 GB, D: 4,69 GB; no escribi en D:.

## 2. En una pantalla

1. **Afirmacion 1 CONFIRMADA**: con mi pareo propio (sin banco_paridad ni node) salen los mismos 168 pares, 0,429 (82) bajo 30 grados y 0,243 (86) sobre 30, Spearman -0,522 fuera del barajado [-0,140; +0,159], insensible a la tolerancia (30, 60, 120 s); MIROVA contra el cenit +0,026; la magnitud de K sola cae (-0,442).
2. **Afirmacion 2 CONFIRMADA EN PARTE**: los numeros se reproducen (23 pares, 1,01 / 1,017, via/K 2,336 / 3,93) y los 23 representan a los 168 (K/M, cenit, VRP de MIROVA y plataformas sin diferencia: Mann-Whitney p 0,88 / 0,49 / 0,93). Lo que no se sostiene: «sin pendiente» con n 23 es ausencia de evidencia (el barajado admite Spearman hasta ±0,38); y 4 de las 28 alertas de los lotes no entran porque la via las clasifica `far` (dos de ellas K las publica en el crater con 0,016 y 0,0079 MW).
3. **Afirmacion 3 CONFIRMADA EN PARTE**: el brazo si cambia solo el fondo (mismo coeficiente, misma area, misma mascara) y reproduce a K **por pasada** (14 de 23 entre 0,8 y 1,25; nulo barajado [0; 2; 5]). Pero el instrumento que cita la afirmacion, las medianas por tramo 0,415 / 0,246, **no discrimina**: el fondo de K de otra pasada barajado da [0,10; 0,37; 0,56] y [0,02; 0,27; 0,57], que contienen el valor real. El recorte a cero casi no actua (1 cero de 24; sin recorte 0,415 / 0,217): la pieza es el **nivel** del fondo de anillo (3 a 11 K mas tibio que el fondo local de la via, mediana 6,86 K).
4. **Afirmacion 4 CONFIRMADA EN PARTE**: las 11 estan a 48,52 grados o mas; pero son 5 con cumulo summit a 0 MW, 4 sin ningun cumulo y 2 `far`; y «ninguna protegida» es falso en la letra: `clase_mirova.pasadas_protegidas` lista 2 de las 11 (2026-09-28 05:18, 2,51 MW; 2026-09-29 04:54, 1,86 MW), que son fuentes a 25 y 9 km.
5. **Afirmacion 5 CONFIRMADA**: los alertados de la via estan a 9,1 a 25,8 km del crater y K pone sus pixeles en la misma lat/lon en 3 de las 4; la distancia del OCR (2,97 a 5,68 km) viene de una imagen `Dist.png` capturada 20 a 25 dias despues (A119, hito 2026-10-09).

## 3. Veredicto por afirmacion

### Afirmacion 1 (K por pasada, 168 pares, 0,43 / 0,24, Spearman -0,52; tabla sola; MIROVA plano): CONFIRMADA

Instrumento propio `v01_pareo_propio.py` (salida `v01_salida.txt`), pareo a mano: llave (Tupungatito, VIIRS375) y |t| <= tolerancia, nocturna = `solar_zenith_deg >= 90` del record, alerta = Tipo_Registro ALERTA* salvo ALERTA_SIN_GEOMETRIA_OCR con VRP > 0, regla SN a mano (todas las alertas de la pasada <= 0,05 MW), publicada = `distance_class == "summit"` y magnitud > 0 con magnitud = `f5_core_vrp_mw` si > 0 si no `primary_cluster.vrp_mw`.
- P1 (roto, lo veria): razon x cos(z)^2 da Spearman -0,799; x2 dobla la mediana (0,671). P2 (instrumento muerto): referencia corrida +1 dia deja 55 pares de 168 (no 0: ver VTUPUN375-07, es el mismo numero del auditor).
- Resultado (ventana 2026-02-14 a 2026-11-02, 1086 records nocturnos, 179 con alerta SN): **168 pares, mediana 0,335; z < 30: 0,429 (82); z >= 30: 0,243 (86); Spearman -0,522 [-0,140; +0,159], mediana del barajado +0,008, FUERA**. Los 168 pares son exactamente los de s01 (0 en s01 y no mios, 0 mios y no en s01), el VRP de MIROVA coincide en los 168 y mi magnitud coincide con `disp` de node en los 168.
- Tolerancia 30 / 60 / 120 s: identico. Granulo doble: 0 filas de referencia usadas por mas de un record; 31 records parean con mas de una fila de alerta (CONS y OCR de la misma pasada; se toma CONS como el auditor).
- Tabla sola (C): 135 pares, 0,44 (66) / 0,241 (69), Spearman -0,570 FUERA. Re-corrida de s02 (`r02_salida.txt`): identica a `s02_salida.txt`, incluidas las ventanas desde 2026-04-01 (0,409 / 0,266, n 135) y desde 2026-06-13 (0,539 / 0,313, n 66) y el conjunto U-S.
- Por plataforma: NOAA-20 -0,552 FUERA (89), NOAA-21 -0,571 FUERA (48), Suomi NPP -0,436 dentro (31): la caida no es un confusor de plataforma.
- MIROVA contra el cenit: Spearman +0,026, medianas 0,17 / 0,16 MW. La magnitud de K sola contra el cenit: -0,442, medianas 0,077 / 0,040 MW: la pendiente es de K, no de MIROVA.
- A104: los 168 records estan todos escritos despues de K (`processed_utc` 2026-10-18T10:04 a 2026-11-02T20:13; 149 con sha `3695f67` del reproceso historico, 10 con `34cea39e`, 9 con sha posteriores de 1 record cada uno); con solo el sha `3695f67`: -0,521 FUERA (149).
- Ceros: las 11 alertas sin publicar (todas con z >= 48,5) quedan fuera de los pares; si entraran como razon 0 bajarian mas el tramo alto. No cambian el sentido.
- Razon de medianas (en vez de mediana de razones): 0,453 / 0,250. Mismo sentido.

### Afirmacion 2 (V375-E, 23 pares, 1,01 / 1,02, sin pendiente; V375-E/K 2,34 a 3,93): CONFIRMADA EN PARTE

- Re-corrida de s03 (`r03_v375e_resumen.json`, `r03_v375e_pasadas.csv`): identica a la del auditor (180 pasadas unicas, 70 con alertados, 28 con alerta de MIROVA). Re-corrida de s04 con mi r01 y mi r03: identica. B: **23 pares, via/MIROVA 1,017; z < 30: 1,01 (12); z >= 30: 1,017 (11); Spearman +0,12 [-0,342; +0,382] dentro; via/K 2,336 / 3,93; Spearman via/K +0,645 FUERA**. Reproducido.
- Representatividad (`v05_representatividad.py`, `v05_salida.txt`): B contra el resto de A (145): K/M 0,336 contra 0,333 (Mann-Whitney p 0,88); cenit mediana 28,1 contra 34,0 grados (p 0,49), fraccion z >= 50: 0,22 contra 0,21; VRP de MIROVA 0,16 contra 0,17 MW (p 0,93); plataformas 11 / 9 / 3 (NOAA-20 / NOAA-21 / NPP) contra 78 / 39 / 28; CONS 21 de 23 contra 114 de 145. Control: la diferencia real de medianas K/M (B menos resto) es +0,003 y 200 sorteos de 23 de A dan [-0,092; -0,005; +0,088]. Dentro de la ventana de los lotes (04-04 a 10-21): igual (p 0,78 / 0,30 / 0,52). **Los 23 son una muestra representativa de los 168 en lo que se puede medir**; subrepresentan Suomi NPP (13 % contra 19 %) y las filas solo OCR (9 % contra 21 %).
- Lo que no se sostiene: (a) «sin pendiente» con n 23: el intervalo del barajado va de -0,34 a +0,38, asi que una pendiente de la via de magnitud -0,3 seria invisible; es SIN EVIDENCIA de pendiente, no evidencia de ausencia. (b) «V375-E/K de 2,34 a 3,93» es la mediana de los cocientes por pasada; el cociente de las medianas da 2,56 / 4,05. (c) El conjunto B exige que las dos publiquen: de las 28 alertas de MIROVA de los lotes, la via no publica 4 (clase `far`, 9 a 25 km, VTUPUN375-04) y K no publica 2 de esas 4 y otra mas (04-06 06:30, 0,09 MW, que la via publica a 0,087). Sobre las 4 `far` la via da 1,006 a 1,026 contra MIROVA sin publicarlas.
- Codigo de los lotes (A104): los cuatro runs vienen de cuatro commits distintos (`v04_lotes_runs.txt`: 0e18e10 S159 2026-10-22, 798cac8 S162 y a9331d5 S162b 2026-10-24, a57b0dc FAR 2026-10-28; tres con conclusion `failure`, lo que explica las grillas que faltan) y las entradas no traen sello de codigo. La via se re-corre con `pipeline/mirova_v750_codigo.py` de origin/main sobre todas, asi que el codigo de la via es uno; lo que podria diferir es el remuestreo de la grilla. Medido sobre el unico granulo repetido (VJ1 2026-07-25 05:54, en S162, S162b y FAR): la grilla `mir` es identica (dif 0,0) en los tres lotes (`v03_salida.txt`). Es una sola prueba: VTUPUN375-05.

### Afirmacion 3 (cambiar solo el fondo por el t_bg de K con recorte reproduce a K: 0,415 / 0,246 contra 0,394 / 0,251): CONFIRMADA EN PARTE

- Re-corrida de s05 (`r05_salida.txt`): identica. ANIK_REC / MIROVA 0,415 (12) / 0,246 (12); K produccion 0,394 (12) / 0,251 (11). Reproducido.
- ¿Cambia solo el fondo? Si: la mascara es la de la via, el coeficiente es el mismo (`COEF_VRP_V375 = 1.80e7 * 0.140625 / 1e6` en `pipeline/mirova_v750_codigo.py:85` y `WOOSTER_COEFF = 18.0` con area nadir fija en `pipeline/process_viirs.py:77`, 1539), y solo entra `t_bg_k` del record K. El recorte a cero de K esta en `pipeline/process_viirs.py:1536` (`np.maximum(L_hot - L_bg, 0.0)`), TEXTO.
- Nulo medido (`v03_nulo_fondo.py`, `v03_salida.txt`, A110): con el t_bg de K de OTRA pasada (200 barajados, semilla 173) las medianas por tramo quedan en [0,10; 0,37; 0,56] bajo 30 y [0,02; 0,27; 0,57] sobre 30: **las medianas reales 0,415 / 0,246 caen dentro del nulo**. El instrumento que cita la afirmacion no distingue el fondo propio de uno ajeno, porque el t_bg de K varia poco entre pasadas (nivel). Lo que si distingue es el acuerdo por pasada K / ANIK_REC: real mediana 1,024, p10 0,788, p90 1,481, **14 de 23 entre 0,8 y 1,25**; barajado [0; 2; 5] pasadas y mediana [0,455; 0,694; 1,134]. Con un fondo constante (Tfl + 6,86 K) las medianas por tramo tambien «reproducen» (0,435 / 0,235) pero el acuerdo por pasada cae a 6 de 23 (p90 3,25). Conclusion: el enunciado es cierto, por el acuerdo por pasada, no por los dos numeros que cita.
- Recorte: ANIK sin recorte 0,415 / 0,217, 1 pasada de 24 queda en cero (04-24 06:12). El recorte no es la pieza; el nivel del anillo si (Kt_bg - Tfl de 3,25 a 11,15 K, mediana 6,86).
- Pendiente: Spearman de ANIK_REC -0,224 (dentro del barajado en s05: [-0,353; +0,436]) contra -0,503 FUERA de K sobre las mismas pasadas. Con n 24 no se puede decir que el brazo reproduzca la pendiente de rango de K, solo sus medianas por tramo y sus valores por pasada.

### Afirmacion 4 (11 alertas no publicadas, a 48 grados o mas, 9 con cumulo en el crater y 0 MW, ninguna protegida): CONFIRMADA EN PARTE

- Re-corrida de s06: identica, 11 alertas, cenit minimo 48,52 grados. CONFIRMADO.
- Leidas del JSON (`v02_claim4_5_salida.txt`): **5** con `primary_cluster` summit y `vrp_mw` 0,0 (03-27, 04-12, 03-04, 04-10, 03-06), **4 sin ningun cumulo** (`primary_cluster` None, `n_anomalous_pixels` 0: 05-03, 05-19, 04-06, 05-23) y **2 `far`** (09-28 a 21,6 km con 0,15 MW; 09-29 a 9,4 km con 1,11 MW). «9 con cumulo en el crater» no se sostiene: son 5 con cumulo y 4 sin cumulo.
- «Ninguna protegida»: `clase_mirova.pasadas_protegidas(ft)` (umbral 1 MW, lectura A) lista 5 pasadas de Tupungatito VIIRS375, y **2 estan entre las 11**: 2026-09-28 05:18 (2,51 MW) y 2026-09-29 04:54 (1,86 MW). REFUTADA en la letra. Se sostiene solo si se lee «ninguna alerta protegida DEL CRATER», porque esas dos son fuentes a 25 y 9 km (afirmacion 5).

### Afirmacion 5 (las 4 alertas grandes solo OCR de Suomi NPP antes del 2026-10-09 tienen sus alertados a 9 a 25 km): CONFIRMADA

- Alertados de la via con lat/lon y rumbo (`v03_salida.txt`): 09-28 05:18, 6 celdas a 25,1 a 25,8 km rumbo 195 (BT 278 a 296 K), VIA 2,525 contra MIROVA 2,51; 08-01 05:00, 3 celdas a 13,2 a 13,7 km rumbo 50, VIA 1,28 contra 1,25; 09-29 04:54, 4 celdas a 9,1 a 9,6 km rumbo 77, VIA 1,78 contra 1,86; 09-14 06:18, 2 celdas a 14,9 km rumbo 93 (BT 312 K), VIA 2,28 contra 2,22.
- Camino independiente, el record K (`v06_k_far_pixels_salida.txt`): 08-01 pixel de 0,89 MW en (-33,313; -69,715), 09-14 pixel de 2,28 MW en (-33,395; -69,665), 09-29 pixel de 1,11 MW en (-33,369; -69,728): las mismas celdas que la via (la distancia de K, 12,5 / 12,5 / 7,5 km, se mide desde `lat/lon` del volcan, -33,4 / -69,8, y la de la via desde `vent_lat/lon`, -33,389 / -69,826, `pipeline/mirova_v750_codigo.py:730`; el crater esta a unos 2,7 km del centro: no es desacuerdo de geolocalizacion). En 09-28 K no ve la fuente de 25 km S: alerta otro pixel a 21 km NNE con 0,15 MW (VTUPUN375-06).
- La distancia del OCR (2,97 / 5,41 / 5,27 / 5,68 km) sale de `Distancia_aprox_imagen` `20261008_...Dist.png` para la pasada del 09-14, `20260821` para 08-01, `20261022` para 09-28 y `20261023` para 09-29: imagenes de 20 a 25 dias despues. Coincide con el hito de `scripts/calidad_referencia_mirova.py:34-35`, TEXTO: «antes, en las filas solo OCR de Suomi NPP la distancia y la clase pueden ser de OTRA pasada (la imagen de una pasada posterior); el VRP si es de la suya. Arreglo en Mirova-v1#20, 2026-10-09 14:01 UTC». No hay fila CONS en esos minutos (0 filas a +-3 min).

## 4. Hallazgos (ID VTUPUN375-nn, de mayor a menor gravedad)

### VTUPUN375-01
- TÍTULO: «Reproduce a K» por medianas de tramo no distingue el fondo propio de uno ajeno; la prueba valida es el acuerdo por pasada, y el recorte a cero casi no actua
- ARCHIVO:LÍNEA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_tupun375/v03_nulo_fondo.py` : `v03_salida.txt` (bloques «NULO» y «acuerdo por pasada»); brazo del auditor en `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/s05_fondo_temperaturas.py:176-178`
- QUÉ PASA: el fondo de anillo de K (mediana de BT a 5 a 25 km del centro) es 3 a 11 K mas tibio que el fondo que la via interpola bajo los alertados, y ese nivel varia poco de una noche a otra; por eso el brazo con el t_bg de otra pasada da las mismas medianas por tramo (nulo [0,10; 0,37; 0,56] y [0,02; 0,27; 0,57] contiene 0,415 / 0,246). El brazo si reproduce a K, pero se ve en el acuerdo por pasada (14 de 23 entre 0,8 y 1,25 contra [0; 2; 5] barajado), no en los dos numeros citados. Sin recorte: 0,415 / 0,217, 1 cero de 24: la pieza es el nivel del fondo, no el recorte.
- CÓMO SE VE EN EL DASHBOARD: invisible (es un defecto del instrumento de la auditoria, no del tablero).
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_tupun375 && python -B v03_nulo_fondo.py C:/Users/nmend/vrp-wt/s173_cenit/tupun375/repo r03_v375e_pasadas.csv r01_k_pasadas.csv v03` (Tupungatito, 24 pasadas 2026-04-04 05:48 a 2026-09-18 06:42).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (si el proyecto tira de la palanca «recorte» en vez de «nivel del fondo», no corrige la magnitud; la decision de pieza depende de esto).

### VTUPUN375-02
- TÍTULO: Dos de los 168 pares de K comparan objetos distintos: K publica el crater con 0,016 y 0,0079 MW mientras MIROVA publica una fuente a 12,5 km que K tambien ve en su escena
- ARCHIVO:LÍNEA: `v06_k_far_pixels_salida.txt`; records `data/mirova_equivalent/Tupungatito.json` (VIIRS_SNPP 2026-08-01 05:00 y 2026-09-14 06:18); `r01_k_pasadas.csv` filas con `vrp_M` 1.25 y 2.22
- QUÉ PASA: una fuente termica a 12,5 km (BT 297 y 319 K, 0,89 y 2,28 MW en los pixeles de K) y un pixel tibio de 1 celda en el crater (253,8 K, 0,016 y 0,0079 MW); K elige como `primary_cluster` el del crater (anclaje al vent), lo etiqueta `summit` y publica 0,016 MW; MIROVA publica 1,25 y 2,22 MW (la fuente lejana, con distancia OCR de otra pasada). En el pareo entran como razon 0,013 y 0,004. Mecanismo A46 / A81 (dos representaciones del punto caliente), no el fondo.
- CÓMO SE VE EN EL DASHBOARD: el operador ve Tupungatito con 0,016 MW esa noche y MIROVA con 1,25 MW; la fuente de 12,5 km queda invisible (clase `far` oculta, inner 7 km).
- CÓMO REPRODUCIRLO: `python -B v06...` (es un heredoc; el script equivalente esta en `v02_claim4_5_salida.txt` y `v06_k_far_pixels_salida.txt`): leer `anomaly_pixels` de VIIRS_SNPP 2026-08-01 05:00 UTC y 2026-09-14 06:18 UTC en Tupungatito.json de origin/main `f20495d374`.
- CONFIANZA: CONFIRMADO (leido del record y del CSV).
- GRAVEDAD: 3 (dos noches con una fuente de 1 a 2 MW a 12 km publicadas como 0,01 MW en el crater; no decide una alerta del volcan, pero esconde una fuente que MIROVA si muestra).

### VTUPUN375-03
- TÍTULO: «9 con cumulo en el crater» son 5 con cumulo y 4 sin cumulo, y «ninguna protegida» contradice a `pasadas_protegidas` (2 de 11)
- ARCHIVO:LÍNEA: `v02_claim4_5_salida.txt` (bloque afirmacion 4); `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/repo/scripts/clase_mirova.py` (`pasadas_protegidas`, `UMBRAL_PROTEGIDA_MW = 1.0`)
- QUÉ PASA: de las 11 alertas de MIROVA que K no publica, 4 records no tienen `primary_cluster` (0 pixeles anomalos: K no detecto nada) y 5 tienen un cumulo summit con 0,0 MW; 2 son `far`. Las dos `far` (2,51 y 1,86 MW) son alertas protegidas para la lectura A tal como la implementa el repo. Son fuentes a 25 y 9 km (afirmacion 5), asi que no son alertas del crater perdidas, pero el criterio de victoria las cuenta como protegidas mientras la referencia diga 5,27 y 5,68 km.
- CÓMO SE VE EN EL DASHBOARD: en esas 11 noches el operador no ve nada en Tupungatito; en las 2 protegidas tampoco (la de 09-29 tiene un cumulo de 1,11 MW a 9,4 km, oculto por el inner de 7 km).
- CÓMO REPRODUCIRLO: el heredoc de `v02_claim4_5_salida.txt` (primeras 60 lineas) sobre `repo/`; `cm.pasadas_protegidas(ft)` con las filas de Tupungatito VIIRS375.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (cambia como se cuenta el recall protegido de Tupungatito: 2 de 5 protegidas no publicadas, no 0).

### VTUPUN375-04
- TÍTULO: La referencia da como alertas del crater (2,97 a 5,68 km) cuatro fuentes a 9 a 25 km, porque la distancia del OCR viene de una imagen de 20 a 25 dias despues
- ARCHIVO:LÍNEA: `repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (filas Tupungatito 2026-08-01 05:00, 09-14 06:18, 09-28 05:18, 09-29 04:54; columna `Distancia_aprox_imagen`); `repo/scripts/calidad_referencia_mirova.py:34-35`
- QUÉ PASA: cuatro focos nocturnos reales (BT 290 a 319 K, 1,25 a 2,51 MW, reproducidos por la via a 1,006 a 1,026 y vistos por K en 3 de 4) estan a 9 a 25 km del crater (rumbos 50 a 195); el scraper les pego la distancia de un `Dist.png` posterior (`20261008` para la pasada del 09-14, etc.), asi que la referencia los pone dentro de 7 km. Es el defecto que el hito A119 del 2026-10-09 ya describe; estas 4 filas son anteriores al arreglo y no estan reprocesadas.
- CÓMO SE VE EN EL DASHBOARD: el tablero no las muestra (clase `far`); el auto-audit y el criterio de victoria las cuentan como alertas del crater que K pierde.
- CÓMO REPRODUCIRLO: `grep -n "2026-09-14 06:18\|2026-09-28 05:18\|2026-09-29 04:54\|2026-08-01 05:00" repo/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` y leer `Distancia_aprox_imagen`; `v03_salida.txt` bloque «afirmacion 5».
- CONFIANZA: CONFIRMADO (posicion por dos instrumentos nuestros; la fecha de la imagen leida del CSV). SOSPECHA en que la posicion de MIROVA sea la nuestra: no abri los PNG.
- GRAVEDAD: 2.

### VTUPUN375-05
- TÍTULO: Los cuatro lotes de la via salen de cuatro commits distintos y sin sello de codigo en las entradas; la identidad del remuestreo esta probada en un solo granulo
- ARCHIVO:LÍNEA: `v04_lotes_runs.txt` (head_sha 0e18e10, 798cac8, a9331d5, a57b0dc; tres runs `failure`); `v04_lotes_meta_salida.txt` (claves de las entradas, sin sha); `v03_salida.txt` (duplicadas: VJ1 2026-07-25 05:54 identica en S162, S162b y FAR, dif 0,0)
- QUÉ PASA: las grillas de 375 m se construyeron en cuatro corridas de Actions de distinto commit; la via se re-corre hoy con un solo codigo, asi que el unico camino de mezcla (A104) es el remuestreo. Verificado identico en el unico granulo repetido; en los otros 179 no hay prueba.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `for r in 40116289866 40131572769 39712862945 40773794395; do gh api repos/MendozaVolcanic/VRP-chile/actions/runs/$r --jq '[.id,.head_sha,.conclusion]|@tsv'; done`; `python -B v03_nulo_fondo.py ...` (primeras lineas).
- CONFIANZA: CONFIRMADO (los commits y la grilla repetida); SOSPECHA (que el remuestreo sea el mismo en los 179 restantes).
- GRAVEDAD: 1.

### VTUPUN375-06
- TÍTULO: K no detecta la fuente de 2,5 MW a 25 km al sur del 2026-09-28 05:18 que la via y MIROVA si ven; alerta otro pixel de 0,15 MW a 21 km NNE
- ARCHIVO:LÍNEA: `v06_k_far_pixels_salida.txt` (K: pixel (-33,234; -69,687), 273,6 K); `v03_salida.txt` (via: 6 celdas (-33,606 a -33,613; -69,894 a -69,902), 278 a 296 K); `repo/pipeline/process_viirs.py:839` (`roi_mask_bbox`, caja 50 x 50 km)
- QUÉ PASA: la fuente esta a 25,1 a 25,8 km del crater (unos 23 km del centro -33,4 / -69,8), dentro de la caja de 50 km de K segun el comentario de process_viirs.py:835-839; K no la alerta y la via si, con magnitud igual a MIROVA. No se por que (umbral, borde del barrido a 48,8 grados o borde de la caja); no lo persegui.
- CÓMO SE VE EN EL DASHBOARD: invisible en los dos casos (far).
- CÓMO REPRODUCIRLO: leer el record VIIRS_SNPP 2026-09-28 05:18 de Tupungatito.json y la fila de `v03_salida.txt`.
- CONFIANZA: SOSPECHA (fenomeno medido; causa sin probar).
- GRAVEDAD: 1.

### VTUPUN375-07
- TÍTULO: El control negativo «referencia corrida un dia» no es nulo (55 de 168), en mi pareo igual que en el del auditor
- ARCHIVO:LÍNEA: `v01_salida.txt` («control P2 (referencia +1 dia): pares 55 (de 168)»); `r01_k_resumen.json` (`control_neg_shift1d_n_pares` 55)
- QUÉ PASA: los satelites repiten la hora de paso a +-2 min en dias consecutivos, asi que correr la referencia un dia entero vuelve a parear la misma plataforma; el control mide persistencia de la actividad, no el instrumento. Es duplicado del CTUPUN375-06 del auditor (fundido). Un control nulo valido seria correr +37 min o parear otra plataforma.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B v01_pareo_propio.py repo v01`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje)

- Mirova-v1: las 4 filas OCR de Tupungatito VIIRS375 anteriores al 2026-10-09 con VRP >= 1 MW llevan distancia de otra pasada (VTUPUN375-04); si el scraper no las reprocesa, cualquier recall protegido de Tupungatito las cuenta mal. Confianza CONFIRMADO.
- `pipeline/process_viirs.py` seleccion de cumulo (A46/A81): en 08-01 05:00 y 09-14 06:18 K publica 1 celda del crater de 0,01 MW teniendo una fuente de 0,9 a 2,3 MW a 12,5 km en la misma escena (VTUPUN375-02). Es la regla de la anomalia mayor decidida por Nicolas el 2026-10-09 (A85, marca S151), A/B `vent_anchored` contra `vrp_max` pendiente. Confianza CONFIRMADO en el dato.
- Distancias con anclas distintas (A3): `anomaly_pixels[].dist_km` de K se mide desde `lat/lon` del volcan (-33,4 / -69,8; `process_viirs.py:812`, `haversine_km(volcano_lat, volcano_lon, ...)`) y el de la via desde el crater (`mirova_v750_codigo.py:730`, `pos_crater`); en Tupungatito difieren hasta 2,7 km. Quien compare posiciones entre K y la via tiene que restarlo. Confianza CONFIRMADO.
- K sin la fuente de 25 km S del 09-28 (VTUPUN375-06). SOSPECHA.
- Records de Tupungatito VIIRS375 escritos por 11 commits distintos posteriores a K (149 del reproceso, 10 de `34cea39e`, 9 de otros 9 commits con 1 record cada uno): el NRT escribe con el commit del dia. Sin efecto medido aqui (con solo `3695f67`: -0,521). Confianza CONFIRMADO en el conteo.

## 6. VERIFICADO LIMPIO

- Copia `repo/` del auditor = `origin/main f20495d374` salvo CRLF en los 9 archivos usados (sha256 tras `tr -d '\r'`). Vara: `git show origin/main:<archivo>`.
- Re-corridas identicas (diff vacio tras quitar CR): s01 (`r01_k_resumen.json`, `r01_k_pasadas.csv`), s02 (`r02_salida.txt`), s03 (`r03_v375e_resumen.json`, `r03_v375e_pasadas.csv`), s04 con mi r01 y con mi r03 (`r04_salida.txt`, `r04b_salida.txt`), s05 (`r05_salida.txt`), s06 (`r06_salida.txt`). Vara: la salida del auditor.
- Pareo propio sin helpers (`v01`): mismos 168 pares, mismo VRP de MIROVA en los 168, misma magnitud que `disp` de node en los 168; insensible a la tolerancia (30 / 60 / 120 s); 0 filas de referencia usadas dos veces; 0 duplicados (sensor, minuto) en los 2.622 records VIIRS375. Vara: s01 y el JSON.
- Cenit: `sensor_zenith_deg` existe en los 1.086 records nocturnos (0 sin cenit). Vara: el JSON.
- A104 sobre K: 0 records VIIRS375 de Tupungatito con `processed_utc` anterior al merge de K (2.622 de 2.622 posteriores a 2026-10-18T10:04Z). Vara: el JSON.
- El brazo de la afirmacion 3 aisla el fondo: mismo coeficiente (2,53125 MW por unidad de radiancia en los dos codigos), misma area nadir, misma mascara. Vara: `mirova_v750_codigo.py:85` y `process_viirs.py:77,1539`.
- Grillas de los lotes son L1B (granulos `VNP02IMG`, `VJ102IMG`, `VJ202IMG`), no TIF de MIROVA; todas con `dayflag` 0 (noche) salvo 3 `None` con estado no ok. Vara: `v04_lotes_meta_salida.txt`.
- Barajado centrado: mediana del barajado +0,008 (U), -0,000 (C). Vara: `v01_salida.txt`.

## 7. SIN DATO

- Si MIROVA ubica esas 4 fuentes donde las ubica la via: no abri las imagenes PNG del scraper.
- Pendiente de la via con el cenit: n 23 solo excluye pendientes mas fuertes que ±0,38 de Spearman.
- Remuestreo identico entre lotes mas alla del granulo repetido.
- Esfuerzo con que corri: no me llego en el despacho.
- Por que K no alerta la fuente de 25 km S del 09-28.

## 8. FUERA DE ALCANCE

MODIS y VIIRS 750 de Tupungatito; la sombra prospectiva de V375-E; el predicado del tablero (`index.html`) como objeto de auditoria; el mecanismo fisico de las fuentes a 9 a 25 km (fuego, mineria, otra cosa); cualquier arreglo.

## 9. Archivos de esta carpeta

`caminos.md` (sellado: sha256 0da03bde..., 02:44:35 UTC), `v01_pareo_propio.py` + `v01_salida.txt/json`, `v02_claim4_5_salida.txt`, `v03_nulo_fondo.py` + `v03_salida.txt/json`, `v04_lotes_meta_salida.txt`, `v04_lotes_runs.txt`, `v05_representatividad.py` + `v05_salida.txt/json`, `v06_k_far_pixels_salida.txt`, re-corridas `r01_*`, `r02_*`, `r03_*`, `r04_*`, `r04b_*`, `r05_*`, `r06_*`, `_tmp_via_data/` (records de la via para node, generado por r03), `hallazgos.csv`.
