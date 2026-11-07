# Verificación del frente F5 (identidad del pareo con MIROVA), auditoría S175

## 1. Encabezado

- Hora del servidor: Sat, 07 Nov 2026 08:59:44 GMT (header `Date` de la API de GitHub; al empezar 08:47:57 GMT).
- Base medida: `752d348bc67190e53b610989877e2405d238a1bc`. Comprobé que la copia privada del auditor
  (`C:\Users\nmend\vrp-temporales\s175_audit\f5\root`) es ese commit: 9 archivos clave (banco_paridad, auto_audit_weekly,
  clase_mirova, referencia_mirova_unificada, las tres vistas, audit-weekly.yml, volcanoes.yaml) son idénticos a
  `git show 752d348bc:<ruta>` una vez quitados los retornos de carro.
- Modelo y esfuerzo: Sonnet 5.5 (`claude-sonnet-5-5`). Esfuerzo: el arnés de esta sesión declara `reasoning_effort` 10 en
  su prompt de sistema; no puedo comprobar desde dentro el valor efectivo. Trátese como SIN DATO sobre el esfuerzo real.
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5\`
- `caminos.md` (escrito antes de abrir ningún archivo citado): `...\v5\caminos.md`. Sello: sha256 del contenido anterior a la
  línea de sello `4924f4fedc37beebe46ebedb924105e77830d8d0a90582ceafe492699f5b5e9c`, hora del servidor 08:48:36 GMT. (El sha256 del
  archivo completo con la línea de sello es `09a1c72e93564c4a...`; no volví a editarlo.)
- Lo que NO miré: INFORME.md ni `hallazgos.csv` del auditor (contexto limpio). Las afirmaciones 302, 308 y 310 (no se me
  asignaron). La vara de posición con TIF/PNG (I2 con lámina de MIROVA). Que el `mirova_center` del KMZ sea exactamente el
  origen de la distancia de MIROVA: lo mido por sus residuos (V5-A), no lo leí de ningún documento de MIROVA. La causa de que la
  tabla no liste Suomi NPP (sólo descarté cenit y convención de hora). Las tres copias de `mirovaEqVrpCore` y de
  `f5CoreMagnitude` (sólo diferencié `mirovaEqVrp`). Nada de pipeline/, data/ ni frontend/ fue modificado; no hice git add,
  commit, stash, checkout ni pull. API de GitHub: 3 llamadas (hora del servidor), de las 5 permitidas.
- Disco: C: 7,6 GB libres, D: 4,9 GB libres (sobre el mínimo de 3 GB). Mi temporal `C:\Users\nmend\vrp-temporales\s175_audit\v5\` pesa 9,8 MB.

## 2. En una pantalla

Las nueve afirmaciones se sostienen, pero cuatro son más chicas de lo que dice su título:
- CONFIRMADOS: 303 (origen vent contra centro de MIROVA), 304 (noche cuenta otra pasada), 305 (SNPP sin fila de la tabla), 306
  (snapshot del consolidado semanal con OCR horario), 309 (42 protegidas diurnas), 311 y 312 (documentadas, sin efecto hoy).
- CONFIRMADOS EN PARTE: 301 (el OCR discrepa de la tabla en 19 % de las pasadas con ambas, no "no sirve"; "casi todos" vale
  sólo tras descontar los que caen dentro de nuestros píxeles: 25 de 26) y 307 (las nueve existen, pero sólo 1 decide una pasada
  en la ventana sep a nov; y su nota es de piso, así que incluirlas es correcto).
- Ninguna sube de 2 en mi gravedad. Ninguna cambia una banda de `RECALL_MIN`. Hallazgo propio: la regex de I8 deja fuera 20 de 63 notas (V5-01).

## 3. Veredictos por afirmación

Todas las mediciones llevan las dos preguntas del instrumento en el encabezado de su script (carpeta `...\v5\`). Re-corrí los
scripts del auditor en copias dentro de `...\v5\rerun\` (para no escribir en su carpeta): `f5_medir.py` da JSON y `i2_pares.csv`
idénticos byte a byte en contenido a los del auditor; `i2_extension.py` e `linea_base_1102.py` también. `i7_dist_tabla_ocr.py` lo leí y
lo reemplacé por una medición propia (V5-A). `i3_vistas_y_pages.sh` no lo corrí tal cual porque escribe en el temporal del
auditor y baja páginas publicadas; hice la prueba diferencial con node (V5-L).

### 301: la distancia del OCR no sirve de vara de posición; casi todos los aciertos de otra fuente se apoyan en ella
**Veredicto: CONFIRMADO EN PARTE. Mi gravedad: 2** (la del auditor, 3).
- Línea citada correcta: `scripts/referencia_mirova_unificada.py:134` es `dist = parse_ocr_distance(r.get("Nota_Validacion", ""))`
  (en 752d348bc; la nota del OCR trae "Estrella verde en Y=284 -> 1.49 km", la distancia se lee de un gráfico).
- Parte que se sostiene (`v5_a_origen_y_ocr.py`, salida `v5_a_origen_y_ocr.out.txt`): sobre las 881 pasadas nuestras
  pos+pub (ventana 2026-06-11 a 2026-11-07), 200 tienen fila de alerta de la tabla y del OCR a ±120 s. En 38 de 200 (19 %) el
  OCR difiere de la tabla en más de 1 km, y en 33 de esas 38 la tabla queda más cerca de NUESTRO punto (medido desde
  `mirova_center`). Los desvíos son sistemáticos por volcán (Tupungatito unos -2,9 km, Puyehue unos -4,2 a -4,5 km, Láscar MODIS y
  VIIRS 750 unos +1,5 a +1,9 km, ver `i7_dist_tabla_ocr.out.txt` del auditor, que releí). Después del arreglo de Mirova-v1#20
  (2026-10-09 14:01) no desaparecen: 12 de 49 (24 %).
- Parte que NO se sostiene como está escrita: "no sirve" es demasiado. En el 81 % de las pasadas con ambas el OCR y la tabla
  coinciden (mediana |Δ| 0,06 km). Placebo: emparejando cada OCR con la tabla de otra pasada del mismo sensor (barajado) la mediana sube de 0,06 a 2,05 km
  en VIIRS 375, así que el OCR sí lleva información; lo que falla es una minoría con sesgo fijo por volcán.
- "Casi todos los aciertos de otra fuente": sobre las 83 pasadas clase (iii) por radio (origen `mirova_center`), 29 usan distancia
  OCR y 54 distancia de la tabla (tasas: OCR 29/161 = 18 %, tabla 54/715 = 7,6 %; el OCR tiene 2,4 veces más (iii)). "Casi todos" sólo es cierto
  tras el filtro de extensión de `i2_extension.py` (re-corrido, idéntico): de 83, 57 caen dentro de la extensión de nuestros
  píxeles anómalos y quedan 26 "fuera"; de esas 26, 25 son OCR y 1 es tabla (Chillán VIIRS 375 2026-10-18 06:48).
- Pregunta 1: ¿lo vería si estuviera todo roto? Sí, el placebo da residuos 30 veces mayores. Pregunta 2: instrumento muerto
  daría placebo = real; no ocurre. Denominador: 200 pasadas con ambas filas, 881 pasadas pos+pub, ventana 2026-06-11 a 2026-11-07.
  Control positivo: el estrato antes de V31 (151 pares, 26 con |Δ| > 1 km) contra desde V31.
- Consecuencia práctica: el OCR no entra a ninguna decisión de alerta como vara de posición (el banco sólo usa `dist_ref` en filas FALSO_POSITIVO,
  `banco_paridad.py:339`), así que el daño se limita a instrumentos que clasifiquen posición con OCR (la I2 del propio F5).

### 303: comparar nuestro radio con el de MIROVA mezcla orígenes (vent contra centro de MIROVA)
**Veredicto: CONFIRMADO. Mi gravedad: 2.**
- `scripts/banco_paridad.py:450`: `abs(r["pc_dist"] - r["dist_ref"]) <= 2`. `pc_dist` es `primary_cluster.centroid_dist_km`, medido
  desde `vent_lat/vent_lon` (`pipeline/clustering.py:105`); `dist_ref` es la `Distancia_km` de MIROVA. El comentario de la línea 449
  ("diferencia de RADIOS, no de posiciones, cota inferior de la separación") es falso con orígenes distintos: la cota inferior sólo vale con origen común.
- Medido (`v5_a_origen_y_ocr.py`, 715 pares con distancia de la tabla): mediana del residuo |nuestra - MIROVA| desde el vent 0,989 km (p90 7,6 km)
  contra desde `mirova_center` 0,319 km (p90 0,90 km). Por volcán, mediana desde vent contra desde centro: Puyehue 7,77 contra 0,34 km, Tupungatito 4,94 contra 0,22,
  Planchón-Peteroa 1,61 contra 0,13, Láscar 1,09 contra 0,40. En Chillán e Isluga el vent queda igual o mejor (0,42 contra 0,63; 0,18 contra 0,21), como se espera si ahí centro y vent casi coinciden.
- Efecto en la métrica citada (`v5_b_far_ref_origen.py`): reproduce primero `metrica_far_ref` de la base (control positivo: VIIRS 375 0,5228; VIIRS 750 0,7692, idéntico). Con origen
  común `frac_radio_a_2km` pasa de 0,523 a 0,610 en VIIRS 375 (241 pasadas far_ref) y de 0,769 a 1,000 en VIIRS 750 (13); Tupungatito de 4 a 21 de 31, Puyehue de 1 a 3 de 4.
  Placebo (centro corrido 10 km al azar): 0,166, o sea el instrumento ve el origen.
- Es una métrica diagnóstica de las 259 pasadas `far_ref`, no entra al criterio de victoria. Por eso 2.
- Refuerzo independiente: nuestro acierto V375 de Puyehue 2026-10-10 05:54 está a 0,101 km del vent y a 7,664 km de `mirova_center`; MIROVA dice 7,73 km (`rerun\i2_pares.csv`).

### 304: el recall por noche cuenta una pasada distinta en otro lugar (PCC V750 2026-10-10); con misma pasada baja 2 puntos en VIIRS
**Veredicto: CONFIRMADO. Mi gravedad: 2** (la del auditor, 3).
- `auto_audit_weekly.py:377`: `c += bool(o and o["crater"]); d += bool(o and o["dash"])`, con `ours` indexado por (volcán, familia, noche): no hay identidad de pasada.
- Reproducido por dos instrumentos. Port del audit (re-corrida de `f5_medir.py`): VIIRS 375 194 de 200 noches (97,0 %) contra 190 de 200 con misma pasada (95,0 %); VIIRS 750 42 de 53 (79,2 %)
  contra 41 de 53 (77,4 %); MODIS 16 de 22 en ambos. Predicado del tablero con node (`v5_d_noche_vs_pasada_banco.py` y `v5_e_noche_node.py`): cualquier pasada 194, 42, 16; misma pasada 190, 41, 16. Port y node coinciden,
  así que la diferencia es identidad de pasada y no de predicado. Control: con `pub` forzado a 1 noche y pasada coinciden (brecha 0).
- Los siete casos, abiertos a mano (`v5_c_casos_304.py`): PCC V750 2026-10-10: MIROVA alerta 05:54:02 (1,19 MW, 7,83 km); nuestra pasada de las 05:54 no tiene cúmulo y el acierto viene de SNPP 04:54, a 13,756 km del vent (18,5 km del centro). Lastarria 2026-09-04: alerta 06:24:01 sin cúmulo nuestro; los aciertos son de 05:24 y 06:00 (la tabla marca 05:24 RUTINA y no lista 06:00). Láscar 2026-10-28: alerta 06:12:01 con nuestro cúmulo a 21,7 km; acierto a las 05:12 (la tabla no lista ese gránulo). Lastarria 2026-09-21: la alerta de MIROVA es OCR 05:42 y nuestro cúmulo está a 24,5 km; el acierto cae a las 06:06, donde MIROVA anota 0,05 MW (mínima de D-9). Tupungatito 2026-09-29: alerta OCR 04:54 (1,86 MW, 5,68 km) y nuestro cúmulo a 9,4 km del vent; el acierto es de 05:18 y 06:00 con 0,02 y 0,04 MW.
- Matiz: son 4 noches de 200 en VIIRS 375 y 1 de 53 en VIIRS 750. Con n tan chico la caída de 2 puntos no tiene intervalo que la separe de cero. Ningún piso de `RECALL_MIN` (93,4 VIIRS 375; 79,5 VIIRS 750; 95,0 MODIS, `auto_audit_weekly.py:120`) cambia de lado: VIIRS 375 queda en 95,0 sobre 93,4; VIIRS 750 ya estaba bajo 79,5 (79,2) y sigue (77,4).
- Ventana: 2026-09-03 a 2026-11-02, detector K, 200 noches VIIRS 375 con alerta de MIROVA y record nuestro (53 en VIIRS 750, 22 en MODIS).

### 305: la tabla de MIROVA no lista la mayoría de las pasadas de Suomi NPP; el denominador de negativos se mueve por satélite y mes
**Veredicto: CONFIRMADO. Mi gravedad: 2.**
- `v5_i_snpp.py`: de nuestras pasadas 2026-06-11 a 2026-11-07, con fila CONS u OCR de MIROVA a ±120 s (`TOL_S` 120): SNPP VIIRS 375 786 de 2126 (37 %), SNPP VIIRS 750 690 de 2103 (33 %);
  NOAA-20 86 y 84 %, NOAA-21 82 y 80 %, MODIS 93 %.
- Descarté la convención de hora (`v5_j_snpp_offset.py`): histograma de desfase de las filas de MIROVA alrededor de nuestras pasadas SNPP, bins de 2 min, ±30 min: 38 % a 0 min, 1 % a +6, 63 % a +18 y 17 % a +24. El +18 es la fila de NOAA-20, que en su propio
  histograma aparece a -18 (16 %). No hay pico a ±6 min ni a ningún desfase fijo pequeño. Es cobertura, no reloj.
- Tampoco es cenit (`v5_k_snpp_zenit.py`): las SNPP con fila tienen cenit mediano 56,6 y las sin fila 46,1. La causa queda SIN DATO.
- Denominador de negativos (VIIRS 375, pasadas `neg_limpio` por pasadas totales): SNPP 63/317, 40/390, 91/448, 95/493, 75/462 (junio a octubre, 10 a 20 %); NOAA-20 161/302 a 288/504 (52 a 60 %); NOAA-21 134/317 a 294/477 (42 a 62 %).
- Efecto: la sobre-publicación en negativos limpios de SNPP se mide con entre 15 y 39 % (según el mes) de los negativos que tiene NOAA-20, y por mes varía a la mitad (SNPP julio 10 % contra agosto 20 %).
- Nota de método: el cuadro del auditor incluye noviembre (ahí el snapshot del consolidado acaba el 2026-11-02, ver 306), así que sus fracciones de noviembre son altas por eso; las de junio a octubre, que usé, no.

### 306: snapshot del consolidado semanal y del OCR horario; entre audits el banco con --snapshot ve alertas OCR sin RUTINA
**Veredicto: CONFIRMADO. Mi gravedad: 1.**
- `.github/workflows/audit-weekly.yml:55` baja `registro_vrp_consolidado.csv` al snapshot sólo cada lunes (cron `0 9 * * 1`, línea 11). El OCR llega al mismo directorio cada hora por
  `.github/workflows/sync-mirova-csv.yml` (cron `12 * * * *`, `scripts/sync_mirova_csv.sh:51-54`); ese cron escribe el consolidado en `latest_consolidado.csv` de la raíz (líneas 23 a 36), no en el snapshot.
- En la base: snapshot del consolidado termina 2026-11-02 12:20; el OCR llega a 2026-11-06 13:15. Hay 15 filas OCR posteriores (14 alertas térmicas), y las 14 tienen ALERTA en la tabla viva (`latest_consolidado_base.csv`), ninguna RUTINA.
  La tabla viva trae 655 filas que el snapshot no tiene (del 2 al 6 de noviembre; 57 alertas, 6 hasta el 2 de noviembre).
- Alcance: `banco_paridad.py:502,510` hace del snapshot una opción (`--snapshot`); por defecto el banco baja el remoto. El audit semanal refresca los dos archivos en su propia corrida
  (líneas 55 a 58), de modo que él no sufre el desfase. El efecto aplica a corridas manuales con `--snapshot` entre audits. Por eso 1.

### 307: nueve alertas OCR escritas 1,0 MW con nota de truncado deciden la lista de protegidas (Chillán MODIS 2026-10-30 07:15)
**Veredicto: CONFIRMADO EN PARTE. Mi gravedad: 1** (la del auditor, 2).
- Línea: `scripts/clase_mirova.py:65` es `alerta_protegida`, umbral `UMBRAL_PROTEGIDA_MW = 1.0` (línea 46), comparación `v < umbral` (línea 72).
- El número se sostiene (`v5_f_truncado.py`, sobre `snapshot_ocr_base.csv`): hay exactamente 9 filas `ALERTA_TERMICA_OCR` con VRP 1.0 y nota "real ∈ [1, 2) MW (±1)"
  (2026-06-17, 06-21, 06-27 ×2, 07-03, 07-06, 08-18, 10-25 y 10-30 07:15). Control positivo: la fila de Chillán MODIS 2026-11-06 13:15 (9,0 "[9, 10)") aparece.
- "Deciden la lista" es exagerado (`v5_g_protegidas_sin_nueve.py`): de 194 pasadas protegidas del 2026-09-01 al 2026-11-07 (aw.VOLS y aw.SENSORS), quitar las nueve deja 193; sólo Chillán MODIS 2026-10-30 07:15 depende de una de ellas. Desde el 2026-06-11: de 236 quedan 233 (también Láscar VIIRS 750 2026-06-27 05:54 y
  Puyehue VIIRS 750 2026-07-03 05:48). Seis de las nueve tienen fila de la tabla de ≥1 MW en la misma pasada. Control: quitar todo el OCR baja de 194 a 167.
- Dirección del truncado: la nota dice que el valor real está en [1, 2), o sea ≥ 1. El 1,0 escrito es un piso, así que contarlas como protegidas es lo correcto; el riesgo opuesto (una 0,x que sea ≥ 1) no lo cubre esta afirmación.
- Caso de partida: la tabla no lista ninguna fila Aqua a las 07:15 de ese día (sí las 08:55, 14,39 MW a 3,16 km); es una alerta "sólo OCR", y nuestro record Aqua de las 07:15 existe pero sin cúmulo (cenit 63,1). Esa pasada es la única protegida que depende de una de las nueve en la ventana sep a nov.

### 309: 42 protegidas diurnas fuera del criterio; las 36 de Chillán tienen protegida nocturna a menos de 12 h
**Veredicto: CONFIRMADO. Mi gravedad: 2.**
- `auto_audit_weekly.py:296` `es_pasada_diurna_descartada` (elevación solar > 0 sobre el volcán, `store._reject_daytime` línea 218; ramas diurnas de MODIS y VIIRS apagadas en producción, `pipeline/diurno.py` cabecera).
- `v5_h_diurnas.py`: 194 protegidas (lectura A, ≥ 1 MW, sep a nov); elevación solar con fórmula NOAA propia (difiere hasta 3,7 grados de `store._solar_elevation`, pero la clasificación coincide en las 194): 42 diurnas (elevación 22,7 a 62,1 grados), 152 nocturnas (máx -9,6 grados, control).
  Por volcán: Chillán 36, Isluga 2, Láscar 2, Chaitén 1, Villarrica 1. Ninguna de las 42 tiene record nuestro (el pipeline las descarta).
- Vecina nocturna: con ventana de 6 h, 7 de 42; de 12 h, 36; de 18 h, 36. Las 36 son todas de Chillán y la más cercana está entre 4,5 y 11,3 h; no hay ninguna entre 11,3 y 107 h, así que el corte de 12 h no es frágil. Las otras 6 (Isluga, Láscar, Chaitén, Villarrica): 5 tienen la protegida nocturna más cercana a 107 h o más y Chaitén no tiene ninguna.
- Lectura: el audit descarta por diseño pasadas donde no corremos, y esas 36 de Chillán son actividad real que el sistema no procesa de día. Es consistente con D-10 (#813) pendiente de Nicolás; no es un bug.

### 311: las tres copias de mirovaEqVrp difieren y el guard de tres vistas sólo compara isValidDetection
**Veredicto: CONFIRMADO. Mi gravedad: 1.**
- Diferencias de texto reales (752d348bc): `diario.html:255` mira `distance_class` antes del caso sin `primary_cluster`, no cae a `vrp_mir_mw`, y no aplica el tope de 50 000 MW al fallback; `index.html:1162` y `mosaico.html:255` hacen lo contrario.
- El guard (`tests/test_guard_predicado_tres_vistas_s147.py`) extrae sólo `isValidDetection` (función `_cuerpo_isvaliddetection`, línea 36) y su propio docstring (líneas 13 a 15) lo declara.
- No es nuevo: `tests/test_audit_metrics_paridad_frontend_s126.py` (docstring) describe exactamente estas tres divergencias, concluye "0 desacuerdos sobre 60.315 records" y las llama latentes; pero ese test fija la función Python, no compara las copias JS entre sí.
- Prueba diferencial con node (`v5_l_tres_copias.py`): 73 710 records reales de los 11 volcanes; con `innerKm` del volcán (como lo llaman todas las vistas: `index.html:1296, 1339, 1361, 3859`, `mosaico.html:343, 365, 379, 400`) hay 0 desacuerdos; si `index` o `mosaico` usaran el defecto 10, hay 290 (los de Puyehue con cúmulo a 10 a 20 km). Control positivo con 4 records sintéticos: los cuatro disparan una divergencia distinta (0,9 contra 0; 0,7 contra 0; 0 contra 60 000; 1 contra 0).
- Hoy sin efecto: los 60 326 records sin `primary_cluster` (conteo de la salida del auditor, `i3_vistas_y_pages.out.txt`, no lo repetí) tienen todos `vrp_mw` 0 y `distance_class` nulo.

### 312: n_misma_pasada del audit compara máximo contra máximo, no noches con acierto en la misma pasada
**Veredicto: CONFIRMADO. Mi gravedad: 1.**
- `auto_audit_weekly.py:821` `_misma_pasada(dt_nuestra, dt_mirova)`; su llamador (línea 861) pasa `o["dt_pub"][i]`, con `i` el máximo publicado de la noche, y la hora de la alerta máxima de MIROVA de la noche (`instantes_mirova`). Es máximo contra máximo, y el docstring (línea 822) lo dice así. Nada que arreglar; es una confusión de lectura.
- Re-corrí `linea_base_1102.py` sobre `root_1102`: reproduce idénticos 125/194 (VIIRS 375), 32/42 (VIIRS 750), 14/16 (MODIS) y el recall del `latest.json` del 2026-11-02. Las noches con acierto en la misma pasada de alerta son 190, 41 y 16 (V5-D, V5-E): 125 contra 190 en VIIRS 375.
- Observación sobre el plan, no sobre el auditor: `docs/PLAN_AUDITORIA_S175.md` (línea base roja 1) toma el 125 de 194 como "noches comunes con misma pasada" sin esta diferencia.

## 4. Hallazgos propios

Ver también `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5\hallazgos_v5.csv`.

### V5-01 (gravedad 1, CONFIRMADO): la regex de I8 deja fuera 20 de las 63 notas de truncado
- ARCHIVO:LÍNEA: `experiments\_s175_audit\f5\f5_medir.py` (función `i8`, regex `real\s*∈\s*\[(\d+),\s*(\d+)\)`); SCRIPT:SALIDA `v5_f_truncado.py:v5_f_truncado.out.txt`.
- QUÉ PASA: el OCR escribe el truncado de dos formas: "real ∈ [a, b)" (43 filas) y "real entre a y b MW" (20 filas `ALERTA_SIN_GEOMETRIA_OCR`). El auditor cuenta 43 (`R["I8"]["n_filas_ocr_con_nota_truncado"]`); el plan sellado dice 63 y yo cuento 63.
- CÓMO SE VE EN EL DASHBOARD: invisible. No afecta la lista de protegidas (esas 20 no son alerta de lectura A) pero el conteo "cerca del umbral" de I8 queda corto.
- CÓMO REPRODUCIRLO: `python -B "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5\v5_f_truncado.py"`.

### V5-02 (gravedad 2, SOSPECHA): el punto de 303 también torna dudosa la clase "summit/far" de Tupungatito y Puyehue frente a la tabla
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `v5_a_origen_y_ocr.py:v5_a_origen_y_ocr.out.txt` (residuos por volcán), `v5_c_casos_304.out.txt` (Tupungatito 2026-09-29).
- QUÉ PASA: nuestro cúmulo de Tupungatito 2026-09-29 04:54 SNPP está a 9,4 km del vent y se llama `far`, mientras MIROVA lo ubica a 5,68 km de su centro (summit en su inner de 7 km); desde `mirova_center` la mediana de residuo de Tupungatito es 0,22 km contra 4,94 km desde el vent.
  Es la misma diferencia de origen de 303, pero aplicada a `distance_class`. Es SOSPECHA en cuanto a si `distance_class` de producción sufre el mismo desfase (no medí el efecto en el recall; sólo vi los residuos).
- CONFIANZA: SOSPECHA. GRAVEDAD 2 (si fuera real, afecta recall de un volcán con inner de 7 km). Lo dejo como seguimiento para F5 o F2, no lo persigo.

## 5. SEGUIMIENTOS (visto fuera de mi eje)

- El script `i3_vistas_y_pages.sh` del auditor escribe en `C:/Users/nmend/vrp-temporales/s175_audit/f5/pages/` y baja páginas con `curl` (no API de GitHub). Es de su instrumento, no del repo; no lo corrí.
- `mirovaEqVrpCore` y `f5CoreMagnitude` también están copiadas tres veces y el guard no las compara; sólo diferencié `mirovaEqVrp`. Hacer la misma prueba diferencial para el Núcleo (VIIRS 375 publica `f5_core_vrp_mw`). Confianza: SOSPECHA de que haya diferencias; mi lectura de las tres funciones `mirovaEqVrpCore` no encontró ninguna de lógica.
- `pipeline/mirova_csv_loader.py:173` usa también `parse_ocr_distance` (el cargador del audit y de los instrumentos); no verifiqué qué consume esa distancia.
- `v5_h_diurnas.py` muestra que mi elevación solar difiere de `store._solar_elevation` hasta 3,7 grados; no cambia ninguna clasificación de las 194, pero no medí por qué. Confianza: CONFIRMADO el número, SIN DATO la causa.

## 6. VERIFICADO LIMPIO

- Reproducibilidad de los scripts del auditor: `f5_medir.py`, `i2_extension.py` y `linea_base_1102.py` re-corridos en copias; resultados idénticos a los guardados. Comando: `python -B ...\v5\rerun\f5_medir.py` (7,9 s). Vara: la propia salida del auditor (misma lógica, misma base); no prueba que la lógica esté bien, sólo que es repetible.
- Copia privada del auditor igual a 752d348bc modulo retornos de carro (9 archivos, `bash %TEMP%\cmp.sh`).
- Port del audit contra predicado del tablero con node: igual en las 275 noches (`v5_e_noche_node.py`): 194/42/16 por ambas vías.
- Clasificación diurna: 0 discrepancias en 194 protegidas con una fórmula solar independiente.
- `diario.html` `INNER_RADIUS_KM` igual a `volcanoes.yaml` (salida del auditor, `i3_vistas_y_pages.out.txt`; no la repetí).

## 7. SIN DATO

- Esfuerzo real con que corrí (ver encabezado).
- Causa de que la tabla no liste el 63 % de las pasadas SNPP.
- Si `mirova_center` es el origen oficial de la distancia de MIROVA (sólo evidencia empírica por residuos).
- Efecto de V5-02 sobre el recall.
- Páginas publicadas de GitHub Pages contra la base: no las bajé; usé la salida del auditor de las 04:32 GMT, sin repetirla.

## 8. FUERA DE ALCANCE

Afirmaciones 302, 308 y 310; detectores; reprocesos; arreglos.

## 9. Archivos de esta verificación

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v5\`:
`caminos.md`, `v5_a_origen_y_ocr.py`, `v5_b_far_ref_origen.py`, `v5_c_casos_304.py`, `v5_d_noche_vs_pasada_banco.py`, `v5_e_noche_node.py`, `v5_f_truncado.py`, `v5_g_protegidas_sin_nueve.py`, `v5_h_diurnas.py`, `v5_i_snpp.py`, `v5_j_snpp_offset.py`, `v5_k_snpp_zenit.py`, `v5_l_tres_copias.py`, cada uno con su `.out.txt`, más `rerun\` (copias de los scripts del auditor y sus salidas) y `hallazgos_v5.csv`.
Trabajo auxiliar (no citado): `C:\Users\nmend\vrp-temporales\s175_audit\v5\work\`.
