# VERIFICACION del frente F2 (VIIRS 375 contra MIROVA y sombra V375-E), verificador V2

## 1. Encabezado

- Fecha y hora del servidor (GitHub, header Date): sábado 7 de noviembre de 2026, 10:39:13 GMT al cerrar (10:28:33 GMT al sellar `caminos.md`).
- Commit sobre el que medí: 752d348bc67190e53b610989877e2405d238a1bc. El árbol del auditor
  `C:\Users\nmend\vrp-temporales\s175_audit\f2\arbol_752d348bc` coincide byte a byte con ese commit: `scripts/`, `frontend/index.html`,
  `volcanoes.yaml` y el snapshot (comparación de sha256 contra `git show`, sin diferencias), y por blob `git hash-object --no-filters`
  los 33 JSON de los 11 volcanes (`data/mirova_equivalent`, `data/mirova`, `data/sombra_codigo_mirova`) y todo `pipeline/` (sin diferencias).
  El lector `leer_sombra_v375e.py` de la copia `arbol_tag_lector` es idéntico al del tag `s172-v375e-lector-resellado`
  (sha256 903a43150c17e2cb...; el tag NO es ancestro de 752d348bc).
- Modelo: Claude Sonnet 5.5 (claude-sonnet-5-5). Esfuerzo con que corrí: SIN DATO (el entorno no me lo muestra y no lo pedí).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v2`
  (scripts propios `v2_*.py` y salidas en `...\v2\corridas\`). Tamaño temporal propio: 170 KB. Llamadas a la API de GitHub: 2 de 5 (solo para la hora del servidor).
- `caminos.md` escrito y sellado antes de abrir ningún archivo citado ni script del auditor. sha256 del archivo completo (con las 5 líneas
  de sellado): cae6bc083acf9bea4e9a2ad553e86ec314d8731a7863cf72dee621f1ab6ec70b. sha256 del contenido anterior al sellado
  (`head -n -5 caminos.md | sha256sum`): dfd4a708825eea4620062e6f54d82c0593ff20b920143b3057642422973c38e2. No lo volví a editar.
- No abrí `INFORME.md` ni `verificador\` de F2. Leí los `.py` del auditor y las salidas `.txt` de sus corridas; los re-corrí todos.
- Qué NO miré: `main` de hoy (solo el commit 752d348bc y el tag del lector); los 34 volcanes fuera de Tier A (no están en el árbol del auditor);
  MODIS y VIIRS 750 salvo lo que sale del predicado; el contenido de las láminas PNG de MIROVA (no las abrí); si el OCR de las 5 filas perdidas
  es correcto (no hay forma de verlo sin las láminas, que el índice `png_index.csv` no trae para esas pasadas); la API viva de Mirova-v1.

## 2. En una pantalla

1. Las ocho afirmaciones reproducen sus números exactos (5 de 171, 4 de 36, 3,9 %, 25,6 %, 647 de 2225, el CUMPLE sin negativos, la tabla que termina el 02-nov, `indexar_referencia` por defecto en "original"). Ninguna sale REFUTADA.
2. Siete quedan CONFIRMADAS EN PARTE y una CONFIRMADA (F2-207). El patrón común: el número es cierto, la lectura que lo acompaña exagera la gravedad.
3. F2-201 y F2-202 se explican por una sola capa: las 5 perdidas son filas solo OCR sin distancia medida o de Suomi NPP anterior al arreglo del 2026-10-09; con fila de la tabla de MIROVA se pierde 0 de 115, y las "de cráter" (V375-A, la lectura del propio proyecto) se publican 121 de 121.
4. F2-203: el 25,6 % de Lastarria es en sus dos tercios efecto de D-9; sin las alertas mínimas reetiquetadas Lastarria da 11,6 %, igual que Puyehue (11,8 %).
5. F2-204, F2-205 y F2-206 son riesgos latentes: en la ventana completa 0 records cambian de publicación por ellos (control positivo sí cambia). Hallazgos propios V2-01 a V2-05 abajo.

## 3. Veredictos por afirmación

Convención: gravedad propia 1 a 5 medida en qué decisión de alerta puede torcer. Todos los números son de la ventana 2026-03-01 a 2026-11-07, pasadas nocturnas V375 con record nuestro (denominador 11.525) salvo que se diga otra cosa (regla A90).

| ID | Veredicto | Gravedad auditor | Gravedad V2 |
|---|---|---|---|
| F2-201 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-202 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-203 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-204 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-205 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-206 | CONFIRMADO EN PARTE | 3 | 2 |
| F2-207 | CONFIRMADO | 2 | 2 |
| F2-212 | CONFIRMADO | 2 | 2 |

### F2-201: 5 de 171 pasadas protegidas V375 no publicadas (por noche 111 de 111): CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) Si lo medido estuviera roto, ¿se vería? Sí para las pasadas: forzar `pub=1` en las 5 perdidas sube el recall a 171/171 (`v2_indep_banco.py`, línea CONTROL positivo) y `todo_publica/nada_publica` del auditor dan 1 y 0. Para "por noche" no: la medición se contenta con cualquier pasada de la noche (ver abajo). (2) Si el instrumento estuviera muerto, ¿cambiaría? Sí: el script aborta con menos de 1.000 records; imprime 28.932 records nocturnos y 11.525 V375.

Qué reproduje. `python f2_banco_v375.py ... banco_base_0301_1107` re-corrido por mí da una salida byte a byte idéntica a la del auditor (`diff` sin diferencias; `corridas\v2_banco_base_salida.txt`). Con mi propio script (`v2_indep_banco.py`, `corridas\v2_indep_banco_salida.txt`): protegidas 171, publicadas 166 (97,08 %), perdidas 5; sin duplicados de (volcán, plataforma, instante) ni pasadas con dos records, así que 171 es el denominador de pasadas y no de filas. Perdidas: Láscar 2026-08-22 05:06 SNPP (cenit 59,3), Lastarria 2026-04-18 04:42 NOAA-20 (67,0), Lastarria 2026-05-02 05:06 SNPP (59,5), Tupungatito 2026-09-28 05:18 SNPP (48,8), Tupungatito 2026-09-29 04:54 SNPP (62,4).

Lo que cambia la lectura (cuatro caminos de `caminos.md`: C201b, C201c, C201d y la vara):

- Las 5 perdidas son todas filas solo OCR (ninguna tiene fila de la tabla en su pasada). Fuentes de las 171: solo OCR 56 (51 publicadas), solo tabla 85 (85), tabla y OCR 30 (30). Con alguna fila de la tabla: 115 de 115 publicadas. Solo OCR: 5 de 56 perdidas (Wilson 95 %: 3,9 % a 19,3 %).
- La clasificación del propio proyecto `scripts/clase_mirova.py::protegida_de_crater` (V375-A, "se informa AL LADO de la lectura A", l. 290 a 319 del commit) marca esas 5 como NO de cráter por `ocr_sin_distancia_medida` (filas solo OCR anteriores al 2026-06-13, antes de que el OCR midiera la distancia) o `ocr_snpp_antes_del_hito` (Suomi NPP antes del 2026-10-09, cuando la distancia y la clase del OCR pueden ser de otra pasada). `v2_de_crater.py`: de las 171, 121 son de cráter y se publican 121 de 121; las 50 no de cráter se publican 45 de 50 (`corridas\v2_de_crater_salida.txt`). La vara de la tarea (lectura A) cuenta las 171, así que el número de la afirmación es correcto; pero el defecto que sugiere ("perdemos alertas protegidas") solo existe en el estrato cuya geometría el proyecto ya declara no confiable.
- "Por noche 111 de 111" es cierto con la definición del banco (la noche cuenta publicada si cualquier pasada de esa noche publica). Con una definición estricta (la noche cuenta solo si una pasada protegida de esa noche publica) son 106 de 111: las 5 noches se salvan por otra pasada de otro satélite con display de 0,03 a 0,22 MW (`corridas\v2_noches_perdidas_salida.txt`), mientras la fila OCR perdida dice 1,29 a 2,51 MW. Esa diferencia de un orden de magnitud con las pasadas contiguas de la tabla es SOSPECHA de lectura OCR (no verificada: no abrí las láminas).
- Las 5 perdidas son, en el tablero, pasadas que el predicado clasifica `far` (el clúster elegido está a 8 a 22 km del cráter) con display 0.

Gravedad V2: 2. No hay evidencia de que una alerta con fila de la tabla se haya perdido en 8 meses; la pérdida está en el estrato OCR de geometría dudosa, y cada una de esas noches tuvo otra pasada publicada.

### F2-202: pérdidas concentradas en cenit 50 grados o más y en Suomi NPP: CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) El campo `sensor_zenith_deg` del record separa estratos de verdad (la línea base roja de Chillán del auditor y mi tabla por bin lo muestran); el control nulo (permutar el cenit dentro de cada volcán) pierde la brecha en parte (ver abajo). (2) Instrumento muerto: los 4 bins de cenit suman 171 y z? tiene 0.

Reproducción. 4 de 36 con cenit de 50 o más contra 1 de 135 con cenit menor: reproduce. Fisher exacto: p = 0,0073 (`v2_indep_banco.py`). SNPP: 4 de 51 contra 1 de 120, p = 0,028. Con z de 60 o más solamente: 2 de 21 contra 3 de 150, p = 0,11 (no significativo).

Qué debilita "concentradas":

- Son 5 eventos. La permutación del cenit dentro de cada volcán (5.000 repeticiones, semilla 175) da P(al menos 4 perdidas con cenit de 50 o más) = 0,071: condicionado al volcán, no se rechaza el azar al 5 %.
- Cenit y plataforma están confundidos: las protegidas de SNPP tienen mediana de cenit 42,0 contra 33,4 (NOAA-20) y 34,2 (NOAA-21), y 29 % de ellas sobre 50 contra 14 % y 22 %. Entre las solo OCR, SNPP pierde 4 de 44 contra 1 de 12 en las otras plataformas: Fisher p = 1,0. La atribución a Suomi NPP no es identificable con 5 eventos.
- Dentro del estrato solo OCR (el único donde hay pérdidas), cenit 50 o más pierde 4 de 13 contra 1 de 43 (p = 0,0084). Con tabla, 0 de 23 y 0 de 92.
- El "97,1 % lo esconde" es literal (166/171), pero el estrato afectado es el de F2-201.

Gravedad V2: 2.

### F2-203: sobre-publicación en negativos limpios (3,9 % agregado; 25,6 % Lastarria; 11,6 % Puyehue; por noche 13,5 / 54,9 / 41,9 %): CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) Control positivo: `todo_publica` da 4087/4087; mi control nulo (permutar `pub` entre los 4.087 negativos limpios) da una tasa media de Lastarria de 0,039 y un máximo de 0,089 en 2.000 repeticiones, contra 0,2565 observada: P = 0. (2) n impresos por volcán (Lastarria 191, Puyehue 371).

Reproducción exacta: 161 de 4087 (3,94 %, Wilson 3,4 % a 4,6 %); Lastarria 49 de 191 (25,65 %, Wilson 20,0 % a 32,3 %); Puyehue 43 de 371 (11,59 %); por noche 1.579 noches negativas, 213 publicadas (13,49 %), Lastarria 45 de 82 (54,9 %), Puyehue 57 de 136 (41,9 %). `d9_por_volcan.py` re-corrido: salida idéntica a la del auditor.

Qué cambia la lectura:

- El exceso de Lastarria es en su mayor parte D-9. De los 191 negativos limpios de Lastarria, 138 lo son con la regla original (RUTINA de la tabla) y 53 se vuelven negativos solo por D-9 (27 eran positivos con alerta mínima de 0,05 MW o menos y 26 sin_info). Publicados: 16 de 138 (11,6 %) en los de la regla original y 33 de 53 en los convertidos por D-9 (25 + 8). Sin los convertidos, Lastarria da 11,6 %, igual que Puyehue con la misma base (42 de 355, 11,8 %). `corridas\v2_indep_banco2_salida.txt`. En el agregado, 110 de 3939 (2,79 %) con la regla original contra 161 de 4087 (3,94 %) con SN; el control de identidad (55 convertidos pos a neg, 39 publicados) reproduce las cifras del auditor.
- La magnitud: 136 de los 161 publicados en negativos limpios muestran menos de 0,1 MW, 25 menos de 1 MW y ninguno 1 MW o más; en Lastarria 47 de los 49 con menos de 0,1 MW.
- "Por noche" usa de nuevo "cualquier pasada de la noche publica". Si cuenta solo que publique la pasada que es negativo limpio: agregado 133 de 1579 (8,4 %), Lastarria 38 de 82 (46,3 %), Puyehue 36 de 136 (26,5 %).
- Salud de la tabla de MIROVA (C203a): la tasa de Lastarria no depende del tramo, 3 de 10 antes del 2026-04-01 contra 46 de 181 después; no detecto un artefacto de la referencia. El aviso de calidad de `indexar_referencia` lista 8 tramos con defectos en la ventana (todos sobre el OCR salvo dos de la tabla).
- Es sobre-publicación contra una referencia que D-9 define; la regla A54 del proyecto dice que la mayoría de estos casos son anomalías reales débiles (fumarolas, lago tibio), y no puedo separarlas aquí.

Gravedad V2: 2 (el caso más alto son 0,1 a 0,4 MW en un volcán con campo fumarólico, en la marca de display más baja).

### F2-204: la confirmación de MIROVA del tablero (±60 min, sin distancia ni D-9; 647 de 2225 publicados sin alerta de su pasada, 143 con RUTINA propia, 113 solo mínimas): CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) Control positivo: el control de identidad del auditor (el port en Python da 3554 igual que la función real con node) lo reproduje; `confirmado_navegador.py` re-corrido: salida idéntica. (2) Instrumento muerto: el conteo de "artefacto" de la regla de exención es 0 en las 28.932 pasadas de los tres sensores, o sea que esta medición NO podía ver un cambio de publicación aunque lo hubiera: eso no es verificación de que la exención sea inocua, solo de que no tiene sustrato en la ventana.

Reproducción. Líneas citadas de `frontend/index.html` en 752d348bc: 1337 y 1356 (exención `r._mirova_confirmed` en `isCirrusArtifact` e `isDiffuseFieldArtifact`), 1422 (`computeMetrics`), 1452 y 1559 (`TOL_MS = 60 * 60000`), 1544 (`enrichWithMirovaConfirmation`), 1548 (descarta NULO y RUTINA): todas coinciden con el texto. Los datos que lee son `data/mirova/<volcán>.json` (l. 992), no el snapshot de CSV. Mi script `v2_conf204.py`: V375 publicados 2.632, confirmados 2.225, sin alerta de su pasada (±120 s) 647, con RUTINA propia en la tabla del snapshot 143. `confirmado_publicados.py` re-corrido: 113 con solo mínimas en 60 min y 105 con solo mínimas en su pasada.

Matices (C204c y C204e): la tolerancia de 60 min y la ausencia de distancia son decisión escrita (comentario de `index.html` l. 1532 a 1543: "NO se gatea por distancia"). La alerta que confirma está a una mediana de 30 min (p10 18, p90 54) y sale de otra plataforma de la misma noche: de los 647, NOAA-21 289, SNPP 247, NOAA-20 111. El efecto sobre qué se publica es nulo hoy: 0 records de 28.932 cambian de publicación con la marca puesta o quitada (con la marca, sin la marca y sin las filas de 0,05 MW o menos). Lo que sí ve el operador: anillo verde en el mapa (l. 3119), "✓ Confirmado por MIROVA" (l. 3142) y, en la columna de la tabla, el texto "MIROVA publicó alerta térmica en esta pasada" (l. 3942), que para 647 de 2225 (29 %) no es cierto de su pasada (hallazgo V2-04).

Gravedad V2: 2 (latente: si apareciera un artefacto frío confirmado por otra pasada, la exención lo dejaría pasar; hoy no hay ninguno).

### F2-205: la regla sellada de la sombra V375-E da (b) CUMPLE sin negativos y S7 no cae con clases vacías: CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) Control positivo (mío, `v2_criterio_b.py`, `corridas\v2_criterio_b_salida.txt`): la misma función da `NO CUMPLE` en (b) con silencio "ENCIENDE DE MAS" o con P2-L = PIERDE, y `control_s7` da `False` cuando 10 pasadas de cualquiera de las 5 clases que deciden están todas SIN DATO. La función puede fallar. (2) Instrumento muerto: no aplica a una función pura.

Reproducción. `criterios_sombra([], "SIN SUSTRATO", "SIN SUSTRATO (...)", "SIN SUSTRATO", CUMPLE, False, CUMPLE)` devuelve (b) CUMPLE y estado CUMPLE; con `regimen_ok=False` pasa a DECIDE NICOLAS. `control_s7` con una sola `pos_prot` con dato y cero negativos devuelve `ok=True`. Líneas en el tag (`lector_tag.py`, copia del tag): `criterios_sombra` 577 a 594 (la expresión de (b) en 584 a 586), `leer_brazo` 602 a 628 (`b_sin_evidencia` en 627), `control_s7` 357 a 366 (`n and len(s) / n > UMBRAL_COBERTURA` en 364: con n = 0 no cae).

Por qué lo bajo a 2:

- Es el diseño escrito: la docstring de `criterios_sombra` dice "(b) P2 contra K GANA, EMPATE o SIN SUSTRATO" (§11.7). Que S7 no caiga con una clase vacía también es coherente: es un control de cobertura, no de existencia.
- El lector lo declara: la línea (b) del informe agrega "| CUMPLE POR FALTA DE EVIDENCIA" cuando `b_sin_evidencia` (l. 750). La línea final "PAQUETE en la sombra (§11.7)" (l. 768 a 769) NO lo repite: quien lea solo el estado final ve CUMPLE sin el motivo.
- El estado final exige además (a), (c) y (d); (c) con M en SIN SUSTRATO pasa a DECIDE NICOLAS (`estado_c_sombra`).
- La parada de §11.8 evita la lectura: la corrida del auditor sobre la base termina "noches 3 de 30, alertas 9 de 40: NO ALCANZADA; no hay lectura" (`lector_base_stdout.txt`).

Se agrava combinado con F2-207 (hallazgo V2-05).

### F2-206: el lector sella el `index.html` del 2026-11-02; el de la base exime a la vía del filtro de cirro (S173 S1): CONFIRMADO EN PARTE, gravedad 2

Las dos preguntas. (1) Control positivo: un record de la vía, summit, frío (t_max 260 K) y de 20 MW publica en la base (`[1,1,0,20,1]`) y no publica en el tag (`[1,1,1,20,0]`): el instrumento ve la diferencia. (2) n impresos.

Reproducción. `v2_predicado_tag_base.py` sobre toda la ventana, no solo del 03 al 07: mirova_equivalent 11.525 V375, 11.429 V750, 5.978 MODIS (120 con marca de vía) y sombra_codigo_mirova 122 + 127 + 96: 0 diferencias de publicación entre el `index.html` de la base (blob 8ac54a2a...) y el del tag (blob b618b6cc...), salvo el control. La línea 71 de `leer_sombra_v375e.py` (en el tag) sella `frontend/index.html` con sha256 260b4a193075c772e02e1549566fbcbe85f608abef6131c5c808444f543e54b2, y es el contenido real de ese archivo en el tag.

Precisión sobre la fecha: ese sha256 corresponde al `index.html` de main desde el commit 3489e55c3 del 2026-10-22 (S159). El tag es del 2026-11-02 00:52 (-0300), anterior a fb1a66d39 (2026-11-02 10:24, MOD-D PR B, "el tablero reconoce codigo_mirova"), a ae252ee39 (2026-11-01) y a 91d1bf901 (2026-11-05, S173 S1). O sea: sella el tablero de antes de tres cambios de `index.html` de main, no solo del último. Hoy el efecto sobre lo publicado es 0 casos reales.

Gravedad V2: 2 (latente: cualquier record de la vía frío y sobre 10 MW cambiaría de estado entre el lector y el tablero).

### F2-207: la tabla de MIROVA del snapshot termina el 2026-11-02; sin negativos limpios desde el 03: CONFIRMADO, gravedad 2

Las dos preguntas. (1) El `awk` de la tarea cuenta solo V375, columna 5 y `substr($2,1,10)`; lo repetí con Python (`csv.DictReader`, sin comas internas: 0 líneas con número de comas distinto de 14): V375, 297 días distintos, último día 2026-11-02 con 19 filas (días previos 39 a 58 filas). (2) Un cero de "negativos" sin esta comprobación sería ambiguo; lo medí con el etiquetador: `v2_etiq_tras_corte.py` (`corridas\v2_etiq_tras_corte_salida.txt`) da por día: neg_limpio 17, 23, 13 y 12 del 30-oct al 02-nov, y 0 desde el 03 (22 a 32 pasadas sin_info cada día).

Último cambio del archivo: 79f410697 (2026-11-02 19:29, "audit(auto): paridad semanal"); sha256 f833bfdef7c3fc5f... igual en el commit y en la copia. Este snapshot se refresca por el auto-audit semanal, así que el retraso es de diseño y llega a 7 días. En el mismo commit, `latest_consolidado.csv` de la raíz (sha256 dee768374b84d49b...) y el snapshot OCR llegan al 2026-11-06 (V375). Las alertas que el banco ve del 04 al 06 de noviembre vienen solo del OCR (pos 3, 5 y 1; no hay RUTINA de la tabla). Los 11.525 de denominador incluyen 5 días (03 al 07-nov) sin vara de negativos: no inflan las tasas de negativos, pero sí el denominador de `sin_info` (5.531).

### F2-212: `banco_paridad.main` y `clasificacion_referencia` usan la etiqueta original y no D-9: CONFIRMADO, gravedad 2

`git grep -n "indexar_referencia(" 752d348bc -- scripts`: `scripts/banco_paridad.py:526` (en `main`) y `scripts/clasificacion_referencia.py:149` llaman sin `regla_minimas`; el valor por defecto de la función (l. 227) es "original". Otras llamadas: `auto_audit_weekly.py` l. 226 (original) y 230 (SN), `vigilancia_sombra.py` l. 447 (original) y 450 (SN), `vigilancia_guardia_modis.py` l. 388 (original). `banco_paridad.py` no tiene ninguna opción de línea de comandos para cambiarlo (`grep regla_minimas`: solo l. 63, 227 a 245).

C212a y C212d: la llamada existente sí implica la etiqueta original (nada la corrige después), pero el defecto es lectura del auditor: la docstring (l. 227 a 236) dice que el defecto "original" es A PROPÓSITO para reproducir los resultados ya publicados, y `docs/S151_CRITERIO_CLASE_MIROVA.md` (l. 8 a 30, D-9) dice que "un evaluador nuevo pasa el modo explícito". Efecto medido (V375, `v2_indep_banco2.py`): 239 pasadas cambian de etiqueta entre original y SN; recall de positivos 0,9313 (original) contra 0,9544 (SN); sobre-publicación en negativos 2,79 % contra 3,94 %; las protegidas no cambian (171 en las dos). `frontend` y `.github` no leen `data/clasificacion_referencia` (git grep sin resultados en `frontend`); el uso es el workflow `sync-mirova-csv.yml` y los documentos del proyecto.

Gravedad V2: 2 (coherencia del criterio de victoria D-9, no efecto sobre lo que ve el operador).

## 4. Hallazgos propios de V2

Formato: TÍTULO, ARCHIVO:LÍNEA o SCRIPT:SALIDA, QUÉ PASA, CÓMO SE VE EN EL DASHBOARD, CÓMO REPRODUCIRLO, CONFIANZA, GRAVEDAD. Rango V2-01 en adelante.

### V2-01: las 5 protegidas no publicadas son todas del estrato OCR sin geometría confiable
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py:290-319` (`protegida_de_crater`); SCRIPT:SALIDA `v2_de_crater.py:corridas\v2_de_crater_salida.txt`.
- QUÉ PASA: las 5 filas son solo OCR, anteriores al hito de distancia o de Suomi NPP; en un volcán el calor es real o es lectura de una lámina de otra pasada. De 121 protegidas de cráter se publican 121; de 50 no de cráter, 45.
- CÓMO SE VE EN EL DASHBOARD: invisible (el operador vio otra pasada publicada esa noche).
- CÓMO REPRODUCIRLO: `python v2_de_crater.py C:\Users\nmend\vrp-temporales\s175_audit\f2\arbol_752d348bc corridas\v2_de_crater_salida.txt` (13 s).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. Funde la objeción central a F2-201 y F2-202.

### V2-02: "por noche 111 de 111" acepta cualquier pasada como cubridora
- SCRIPT:SALIDA `v2_indep_banco.py:corridas\v2_indep_banco_salida.txt` (NOCHES con protegida), `v2_noches_perdidas.py:corridas\v2_noches_perdidas_salida.txt`.
- QUÉ PASA: la noche cuenta publicada si publica cualquier pasada, aunque sea de otra plataforma y con display de 0,03 a 0,22 MW mientras la protegida perdida era de 1,3 a 2,5 MW. Estricto: 106 de 111.
- CÓMO SE VE EN EL DASHBOARD: el operador ve la pasada pequeña y no la grande (SOSPECHA: la grande puede ser lectura errónea del OCR).
- CONFIANZA: CONFIRMADO el número; SOSPECHA la causa (OCR). GRAVEDAD: 2.

### V2-03: el exceso de Lastarria es en dos tercios D-9
- SCRIPT:SALIDA `v2_indep_banco2.py:corridas\v2_indep_banco2_salida.txt` (NEGATIVOS LIMPIOS por origen).
- QUÉ PASA: de 49 publicados, 33 están en pasadas que la regla original llamaba positivas (25) o sin_info (8). Con la regla original, 16 de 138 = 11,6 %.
- CÓMO SE VE EN EL DASHBOARD: invisible; es el tamaño de la lectura A de D-9.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. Debería acompañar a F2-203 cuando se resuma.

### V2-04: el texto del tablero dice "en esta pasada" y la lógica busca ±60 min
- ARCHIVO:LÍNEA `frontend/index.html:3942` (tooltip) contra `:1559` y `:1544-1548`; SCRIPT:SALIDA `v2_conf204.py:corridas\v2_conf204_salida.txt`.
- QUÉ PASA: 647 de 2225 marcadas "MIROVA publicó alerta térmica en esta pasada" no tienen fila de alerta de su propia pasada (143 tienen RUTINA propia); la alerta está a una mediana de 30 min, en otra plataforma. El comentario de l. 1532 a 1543 dice que es a propósito, el texto al operador no lo dice.
- CÓMO SE VE EN EL DASHBOARD: anillo verde y "✓ Confirmado por MIROVA" en la ficha de pasadas donde MIROVA dijo RUTINA (143).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### V2-05: sombra V375-E y snapshot congelado se componen mal
- ARCHIVO:LÍNEA `leer_sombra_v375e.py:71` y `:627` (en el tag) con `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (hasta 2026-11-02); `DESDE_P = "2026-11-03"` (l. 78).
- QUÉ PASA: la ventana P de la sombra empieza el 2026-11-03 y la referencia congelada que lee el lector no tiene filas de la tabla desde esa fecha; los negativos limpios exigen RUTINA de la tabla, así que las clases negativas están vacías y (b) da CUMPLE por falta de evidencia hasta que el snapshot se refresque. SOSPECHA: no corrí el lector con la ventana cumplida (parada no alcanzada).
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta la decisión de adopción de Nicolás.
- CONFIANZA: SOSPECHA (compuesta de dos hechos CONFIRMADOS: `v2_etiq_tras_corte.py` y `v2_criterio_b.py`). GRAVEDAD: 2.

## 5. SEGUIMIENTOS (fuera de mi eje, sin perseguir)

- Las 8 advertencias de calidad de la referencia que `indexar_referencia` imprime a stderr (por ejemplo el tramo 2026-06-13 sin distancia OCR) se imprimen dos veces por corrida (`corridas\v2_banco_stderr.txt`): cosmético, confianza CONFIRMADO.
- `v2_conf204.py` encontró que `data/mirova/<volcán>.json` no contiene filas RUTINA (clasificaciones presentes en Lastarria: Muy Bajo, Bajo, Medio, SIN_GEOMETRIA); el tablero nunca puede mostrar "MIROVA vio RUTINA en esta pasada". Confianza CONFIRMADO, gravedad 1.
- `data/mirova/*.json` llega al 2026-11-06 19:06 en el mismo commit en que el snapshot CSV llega al 02-nov: dos copias de MIROVA con fechas distintas dentro del mismo árbol.

## 6. VERIFICADO LIMPIO

| Qué | Comando | Contra qué vara |
|---|---|---|
| El árbol del auditor es el commit 752d348bc | `git hash-object --no-filters` y `git show ... \| sha256sum` contra cada archivo (scripts, index.html, snapshot, 33 JSON de Tier A, pipeline) | `git cat-file` del commit; sin diferencias |
| Salida de `f2_banco_v375.py`, `d9_por_volcan.py`, `perdidas_protegidas.py`, `confirmado_publicados.py`, `confirmado_navegador.py` | re-corrida y `diff` | las salidas del auditor; idénticas (las dos últimas con mismas cifras) |
| 171/166, 4/36 y 1/135, 49/191, 43/371, 213/1579 | `v2_indep_banco.py` (código propio, no el del auditor) | etiquetado de la vara, sin duplicados de pasada |
| Líneas citadas de `frontend/index.html` | `sed -n Np` sobre el blob del commit | 1337, 1356, 1422, 1452, 1544, 1548, 1559: coinciden con lo que dice la afirmación |
| El tag del lector es byte a byte la copia del auditor | `git show tag:ruta \| sha256sum` | 903a43150c17e2cb...; igual |
| 143 con RUTINA propia | `v2_conf204.py` (tabla del snapshot) | reaparece 143 |

## 7. SIN DATO

- Si el OCR de las 5 filas perdidas es correcto: no abrí las láminas (no están en `png_index.csv`).
- La lectura real del lector de la sombra con la ventana cumplida: no se alcanza la parada de §11.8, no hay lectura posible.
- La hipótesis de que el 25 % de Lastarria sea calor real (fumarolas): no hay vara ajena a MIROVA en el árbol.
- Esfuerzo con que corrí: SIN DATO.

## 8. FUERA DE ALCANCE

MODIS, VIIRS 750, `main` de hoy, volcanes fuera de Tier A, y arreglar nada (no toqué `pipeline/`, `data/`, `frontend/` ni git).

## 9. Reproducción rápida

```
cd C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v2
python v2_indep_banco.py  C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc 2026-03-01 2026-11-07 corridas/v2_indep_banco_salida.txt
python v2_indep_banco2.py C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc 2026-03-01 2026-11-07 corridas/v2_indep_banco2_salida.txt
python v2_de_crater.py    C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc corridas/v2_de_crater_salida.txt
python v2_conf204.py      C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc 2026-03-01 2026-11-07 corridas/v2_conf204_salida.txt
python v2_predicado_tag_base.py C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_tag_lector 2026-03-01 2026-11-07 corridas/v2_predicado_tag_base_salida.txt
python v2_criterio_b.py   C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_tag_lector corridas/v2_criterio_b_salida.txt
python v2_etiq_tras_corte.py C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc corridas/v2_etiq_tras_corte_salida.txt
python v2_noches_perdidas.py C:/Users/nmend/vrp-temporales/s175_audit/f2/arbol_752d348bc corridas/v2_noches_perdidas_salida.txt
```
