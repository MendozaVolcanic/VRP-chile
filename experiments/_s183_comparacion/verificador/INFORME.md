# Informe verificador S183 (comparacion via/K/MIROVA)

## 0. Caminos por los que cada afirmacion podria estar mal (escritos ANTES de leer el codigo)

A1 (cuentas):
- Union de pasadas: clave (volcan, satelite, minuto) mal construida, o no solo nocturnas, o pasadas que solo un detector tiene.
- Fecha de la noche: UTC vs local, o noche que cruza medianoche mal asignada.
- Etiquetado: etiquetar llamado con otra tabla/ventana, o D-9 modo SN mal aplicado, o neg_limpio sin chequear FP.
- Fuente de K: dia de adopcion mal (< vs <=), guardia mal tomada, K con records de via incluidos o vice versa.
- Predicado del tablero: ejecutado sobre record equivocado (K vs via).
- Protegidas: umbral >=1 vs >1, perdidas contadas sobre noches y no sobre alertas.
- Clave del JSON mal rotulada (VIIRS750 vs VIIRS375), via y K intercambiados.
A2 (cache):
- K puro filtrado por clave via_codigo_mirova mal (valor false vs ausente), nocturno mal definido, fecha desde 03-01 inclusiva, corte de adopcion por sensor, sha calculado sobre otro archivo/finales de linea (CRLF), aviso nunca disparado.
A3 (frontend):
- JS intercambia via/K, etiquetas de referencia (tabla/OCR), ventanas; formateo de numeros; JSON cargado de ruta equivocada; pestañas viejas rotas por IDs duplicados.
A4 (workflow): nombre del workflow disparador, YAML 'on' Norway, dependencias (yaml, requests), node setup, commit solo de su salida, retry.
A5: archivos tocados fuera de lista; index.html linea 1600.
A6: pruebas que no atrapan mutaciones (asserts sobre estructuras, no valores).

## 1. A1 y A2: resultados de mis comandos (parcial, se completa abajo)
- Script propio: mi_conteo.py (tabla) y mi_conteo_comb.py (combinado), en esta carpeta. Reusan solo la vara: bp.cargar_nuestros, bp.indexar_referencia(MODO_MINIMAS=SN), bp.etiquetar, bp.parear, clase_mirova.alerta_protegida. El agrupado por noche, el pareo de claves, el corte de ventana, el filtro de K puro del tag y el conteo son propios.
- Referencia: scratchpad/ref_remota3 (consolidado+OCR) con cargar_referencia_unificada por defecto (capas historicas incluidas, igual que el script).
- Resultado: las 16 claves (tabla y combinado x historia/adopcion/guardia_viirs x sensores) coinciden exacto en TP, FN, FP, TN, protegidas, protegidas perdidas y n pasadas pareadas, para via y para K. "diferencias: 0" (dos corridas).
- Cache: 29063 filas, 0 duplicados, el conjunto (vol, sensor, dt) y los valores pub/disp/dc/d_mc coinciden con mi K puro recalculado desde el tag; fechas 2026-03-01 a 2026-11-10; MODIS max 2026-11-01, VIIRS max 2026-11-10 (< adopcion); 0 filas diurnas descartables. Tag: 74235 records, 354 con via_codigo_mirova (excluidos, todos True).
- sha_index_html del cache y del JSON = e11aa165...; coincide con `git hash-object frontend/index.html` y con `git rev-parse HEAD:frontend/index.html`.

# 2. Veredictos (todo corrido en esta sesion; el worktree quedo sin tocar: `git status --short` da 0 lineas)

Rutas: informe C:\Users\nmend\AppData\Local\Temp\claude\c6b6bc10b742515f\01216d56-1367-4023-8bb2-f40bc3458e17\scratchpad\verificador_s183\INFORME.md. Scripts propios en la misma carpeta: mi_conteo.py, mi_conteo_comb.py, consist.py, consist2.py, filas_check.py, ratio.py, mutar2.py, efecto.py. Copia parcial del repo (209 MB) en la subcarpeta copia.

## A1 CONFIRMADO
- Conteo propio (mi_conteo.py). Reusa solo la vara: bp.cargar_nuestros, bp.indexar_referencia (SN), bp.etiquetar, bp.parear, clase_mirova.alerta_protegida. Es propio: el filtro de K puro del tag, la union de claves (vol, satelite, dt), el corte de ventana, el agrupado por noche, TP/FN/FP/TN y protegidas.
- Las 16 claves (tabla y combinado, historia/adopcion/guardia_viirs, por sensor) coinciden exacto con comparacion_via_k.json en TP, FN, FP, TN, protegidas, protegidas perdidas y n de pares, para via y K. Salida cruda: `diferencias: 0` (dos corridas). Ejemplos: tabla|historia|MODIS via 104/3/5/4912 prot 64 perdidas 0, K 93/14/44/4873 prot 64 perdidas 3; tabla|historia|VIIRS750 via 284/19/25/4875 prot 113 perd 0, K 229/74/71/4829 prot 113 perd 1; tabla|adopcion|MODIS via 19/1/1/230 prot 19 perd 0, K 17/3/5/226 prot 19 perd 2.
- Mediana del cociente recalculada en 3 claves y coincide (0,997 y 0,487 MODIS historia; 1,0 y 0,504 V750 historia; 1,035 y 0,405 MODIS adopcion; n 104/93, 292/236, 21/17), ratio.py.
- Filas de noches (2405) contra mis agregados de la tabla (filas_check.py): 0 discrepancias en lab_tabla, prot_tabla, via_vrp/dc/dmc, k_vrp/dc/dmc y k_fuente; 0 filas sin explicacion; 0 noches que debian estar y faltan. Las 402 filas cuyo via_pub/k_pub mi lado "tabla" no ve son noches con alerta solo en la referencia combinada (OCR): explicado.
- Reproducibilidad: el script corrido en la copia con un venv que solo tiene pyyaml reproduce meta (salvo generado_utc y referencia), resultados y noches del JSON del commit, identicos.
- Limites: no verifique que ref_remota3 sea la de los commits 00ade150 y d8493a7b que declara el JSON (no tengo esos blobs). La vara (etiquetar, predicado del tablero) la reuse tal cual, no la audite.

## A2 CONFIRMADO EN PARTE (contenido correcto; el aviso por sha da falso positivo, ver V183-01)
- Cache: 29063 filas, 0 duplicados, igual fila a fila (pub, disp, dc, d_mc, b) a mi K puro recalculado del tag; 0 filas con via_codigo_mirova (354 records del tag con la clave, todos True, excluidos); fechas 2026-03-01 a 2026-11-10; MODIS max 2026-11-01, VIIRS max 2026-11-10 (menor que la adopcion); 0 filas diurnas descartables.
- sha_index_html del cache = del JSON = e11aa165... = `git hash-object frontend/index.html` = `git rev-parse HEAD:frontend/index.html`.
- Cambiar el sha produce aviso: probado de punta a punta en la copia (index.html con una linea agregada): `avisos ['El predicado del tablero cambio ... c5759a5c... hoy ...']`.
- Pero el aviso salta con cualquier cambio del archivo (V183-01).

## A3 CONFIRMADO (navegador real: python -m http.server sobre el worktree, panel del navegador)
- Tarjetas: 96 celdas (2 refs x 3 ventanas x sensores x 6 filas, via en la 1a columna, K en la 2a), n de pasadas y nota "sin par": 0 diferencias contra el JSON.
- Grilla volcan x sensor (2x3x33 celdas): texto y colores (verde via arriba, naranja K abajo) = JSON; 0 diferencias.
- Franja noche a noche: 11 volcanes x 3 sensores x 6 combinaciones; la nota (alertas, silencios via/K) y el conteo de circulos rojos/verdes/naranjos y cruces del SVG = filas del JSON; 0 diferencias.
- Lista de desacuerdos: conteo, orden descendente, tope 300, filtro de protegidas, columna "Quien coincide" y texto de las 60 primeras filas por combinacion = filas del JSON; 221 comprobaciones, 0 diferencias. Ademas el conjunto de noches de la lista coincide exacto con las noches en que via y K difieren entre pasadas pareadas (consist2.py, 8 ventanas, 0 sobrantes, 0 faltantes).
- Las pestañas 1 a 3 siguen: el clic cambia el panel, canvas de 1193x525 y 1174x525, mapa Leaflet presente; read_console_messages onlyErrors: "No console logs".
- No verificado: diseño en celular (no abri vista movil); el aviso de calculo viejo (mas de 48 h) y la falla de fetch solo por lectura de frontend/comparacion_via_k.js:170-173 y :190-197.

## A4 CONFIRMADO EN PARTE
- El nombre "Vigilancia de la guardia K de VIIRS" existe tal cual en .github/workflows/vigilancia-guardia-viirs.yml:1. Ningun otro workflow usa el cron 25 23.
- Dependencias: un venv con solo pyyaml ejecuta el script completo (sin numpy ni earthaccess). ast.parse con feature_version 3.11 de los 10 modulos que importa: ok. node lo usa banco_paridad (subprocess); localmente v22.16.0; que ubuntu-24.04 lo traiga preinstalado es SIN DATO (no lo comprobe en un runner).
- Las capas historicas (respaldo y consolidado_filas_perdidas.csv) estan en git ls-files. Las dos URL raw de Mirova-v1 responden HTTP 200 (HEAD).
- Commitea solo data/audit_continuous/comparacion_via_k.json, con 5 reintentos (pull --rebase -X theirs + push). Los guards G4 y vecinos pasan (copia: 99 passed; las 3 fallas de la copia son por CLAUDE.md y docs ausentes en mi copia parcial; en el worktree, con -B y sin cacheprovider, 34 passed en test_guard_declarado_vs_efectivo_s131 + test_comparacion_via_k_s183 y 35 passed en los tres tests que citan audit_continuous).
- No ejecutado en Actions (despachar esta prohibido). La primera corrida tras el merge dara el aviso falso de V183-01.

## A5 CONFIRMADO
- `git diff --name-status 7c3f45c6d..17015d162`: 9 archivos, solo los listados (A: workflow, dos JSON de audit_continuous, plan, comparacion_via_k.js, script, test; M: FICHA, comparacion.html). `git diff --name-only main...HEAD` agrega solo experiments/_s183_comparacion/. 0 lineas en pipeline/, data/mirova_equivalent, data/guardia_k_*, frontend/index.html y frontend/cambio_detector.js. `sed -n 1600p frontend/index.html` da `function isValidDetection(r) {`.

## A6 REFUTADO: las pruebas casi no atrapan lo que ve el geologo
Copia, harness vivo (control M0, k_pub toma el valor de la via: "1 failed, 12 passed"). Linea base 15 passed. Diez mutaciones fuera de la lista dada: ninguna atrapada (`15 passed` en las 10). Efecto real de 5 de ellas, con el script completo, sobre el JSON (efecto.py):
- M1 dia_antes 2026-11-01 a 2026-11-02 (ventana historia): cambia 6 claves de resultados; no atrapada.
- M2 mediana del cociente a media: cambia 16 claves (todas); no atrapada (test_cociente_es_nuestro_sobre_mirova usa 0,25/0,75/0,5, donde media = mediana).
- M3 noche protegida si TODAS las pasadas lo son (any a all): cambia 14 claves y 57 filas de noches; no atrapada.
- M5 k_fuente invertida (historia/guardia): cambia 2388 de 2405 filas; no atrapada.
- M8 la ventana de adopcion parte en INICIO: cambia 6 claves; no atrapada.
Sobreviven tambien, sin medir su efecto: M4 corte INICIO exclusivo, M6 protegida con lectura B, M7 vrp_mirova = min, M9 discordantes sin filtro de protegida, M10 fila omitida si solo la via publica. Ver V183-02.

# 3. Hallazgos propios

## V183-01 El aviso "el predicado cambio" salta con cualquier edicion de index.html: falso positivo seguro tras el merge (gravedad 3, CONFIRMADO)
- ARCHIVO:LINEA scripts/comparacion_via_k.py:221-227 (avisos_cache) y :306 y :341 (usa el sha de TODO frontend/index.html, bp.sha_git).
- QUE PASA: compara el sha del archivo entero, no el de las funciones del predicado. main ya trae un cambio de solo texto de un modal (PR #997, commits de2b52d4e y 3cd02eaee; `git diff HEAD main --stat -- frontend/index.html` = 1 insertion, 1 deletion; sha 44a408053...). Corriendo el script con ese index.html, resultados y noches salen identicos (`resultados iguales: True | noches iguales: True`) pero la salida trae el aviso. El cache solo se reconstruye a mano (necesita el tag de 176 MB), asi que el aviso queda fijo. index.html cambio 17 veces desde el 2026-10-15 (`git log --since=2026-10-15 --oneline -- frontend/index.html | wc -l`).
- COMO SE VE: banner naranjo "El predicado del tablero cambio desde que se evaluo la historia de K ... la columna K de la historia usa el predicado anterior" desde la primera corrida diaria tras el merge, sin que el predicado haya cambiado. Un aviso permanente se aprende a ignorar y tapa el dia en que si cambie.
- REPRODUCIR: `git show main:frontend/index.html > X`; copiar X sobre copia/frontend/index.html; `cd copia; python scripts/comparacion_via_k.py --cons <cons.csv> --ocr <ocr.csv> --out salida.json`; mirar meta.avisos y comparar resultados y noches con la salida hecha con el index.html del commit (mis archivos: salida_main_html.json, index_main.html).
- Arreglo posible (lo decide quien orquesta): hashear solo el texto de las funciones que extrae banco_paridad._JS (isValidDetection, isThermalArtifact, etc.).

## V183-02 Las pruebas no atrapan 10 de 10 mutaciones elegidas (gravedad 3, CONFIRMADO)
- ARCHIVO:LINEA tests/test_comparacion_via_k_s183.py (15 pruebas; el unico caso que pasa por etiquetar y node es test_punta_a_punta_via_acierta_y_k_calla, con una sola pasada MODIS de 2027).
- QUE PASA: etiquetar(), ventanas(), el k_fuente, la mediana, la protegida por noche, vrp_mirova y los filtros de fecha tienen cobertura nula o con casos que no distinguen; el e2e usa fechas de 2027 y nunca toca las ventanas reales.
- COMO SE VE: una regresion que cambie una tarjeta, la leyenda de fuente o la ventana pasaria la suite en verde.
- REPRODUCIR: en copia/, `python ../mutar2.py` (aplica 10 reemplazos de cadena uno a uno y corre `pytest tests/test_comparacion_via_k_s183.py -x`); `python ../efecto.py` mide el efecto en el JSON de 5 de ellas.

## V183-03 VIIRS del 2026-11-02 no entra en ninguna tarjeta; la franja del periodo guardia mezcla fuentes de K (gravedad 1, CONFIRMADO)
- ARCHIVO:LINEA scripts/comparacion_via_k.py:79-84 (historia termina 2026-11-01 para todos los sensores; guardia_viirs parte el 2026-11-03) y :248-252 (serie_k).
- QUE PASA: VIIRS 375 y 750 tienen 31 y 31 pasadas pareadas via-historia el 2026-11-02 que no estan en ninguna ventana (no hay guardia ese dia). En la ventana "VIIRS desde el 3 de noviembre" las tarjetas usan la guardia como K, pero la franja y la lista usan serie_k, que entre 11-03 y 11-10 toma K del cache del tag: de 89 filas VIIRS 11-03..11-10 con K, 7 (NOAA-20 del 9 de noviembre) tienen K del cache sin noche equivalente en la guardia. La lista de desacuerdos igual coincide con las tarjetas (11 y 7).
- COMO SE VE: "Historia: marzo a octubre de 2026" incluye el 11-01 y deja fuera el 11-02 de VIIRS; en la franja del periodo guardia aparecen puntos de K que ninguna tarjeta cuenta (el tooltip dice ", historia").
- REPRODUCIR: consist2.py y el bloque de pares del 11-02 (corrido en esta sesion con pasadas.pkl).

## Observacion (no es defecto del instrumento): la lectura depende de la referencia
- VIIRS 375 historia con la tabla: via pierde 0 de 105 protegidas, K 0. Con tabla mas OCR: via pierde 18 de 157, K 3 (combinado|historia|VIIRS375, mi_conteo_comb.py). La pagina abre por defecto en "tabla" (frontend/comparacion_via_k.js:20) y advierte que el OCR es menos creible, asi que es honesto, pero quien mire solo la tarjeta por defecto no ve esas 18. Coincide con la FICHA v1.25 ("algunas pasadas con alerta de 1 MW o mas ... quedan sin publicar").

# 4. VERIFICADO LIMPIO (vara entre parentesis)
- Cuentas de las 16 claves y 3 medianas (mi implementacion independiente sobre la misma vara bp).
- Cache K puro, nocturno, rango y adopcion (K recalculado desde cero del tag).
- Tarjetas, grilla, franja, lista de desacuerdos, pestañas antiguas y consola (DOM real contra el JSON, mas de 700 comprobaciones).
- Workflow: nombre disparador, "on" entre comillas, dependencias minimas, commit solo de su salida con reintento (grep, venv solo pyyaml, tests G4).
- Alcance del commit (git diff --name-status y --stat).


# 5. Segunda vuelta (worktree en b3fdb4b64, rebasado sobre main f7e7aa5c6; copia nueva en .\copia2; worktree sin tocar: `git status --short` da 0 lineas)

## (1) Mutaciones de A6 sobre el codigo nuevo (mutar3.py; control M0 cae; linea base 21 passed)
Atrapadas ahora (antes ninguna): M1 ventana historia termina el dia de la adopcion (adaptada a `_dia_antes(ADOPCION[b])`), M2 mediana a media, M3 any a all en protegida por noche, M5 k_fuente invertida, M8 ventana de adopcion desde INICIO. Ademas M12 (aviso compara el sha de index.html entero) y M13 (sha_predicado ignora cambio_detector.js), mutaciones nuevas sobre el codigo nuevo, tambien caen.
SOBREVIVEN (`21 passed`): M4 corte INICIO exclusivo en filtrar_records_k; M6 protegida con lectura B; M7 vrp_mirova = min de la tabla; M9 discordantes sin filtro de protegida; M10 filas_noches omite la fila si solo la via publica; y la nueva M11 (sha_predicado ignora las constantes F5_R_CORE_KM y F5_BT_EXT_K).
Efecto real medido sobre el JSON (efecto3.py): M6 y M7 no cambian ninguna clave de resultados ni fila con los datos de hoy (equivalentes hoy; M7 solo importaria con varias alertas de MIROVA en la misma pasada); M10 si cambia la lista de noches (el conteo posicional de filas que da efecto3.py, 2387, esta inflado por el corrimiento; el efecto es que desaparecen las noches donde solo la via publica); M9 afecta `protegidas_discordantes`, campo que la pagina no lee (`grep -c protegidas_discordantes frontend/comparacion_via_k.js` = 0) pero que esta en el JSON (3, 1, 4 en MODIS historia, V750 historia, MODIS adopcion). Quedan sin prueba: los cinco que importan para lo que ve el geologo son M10 y M4 (caché) y M11 (predicado); M6/M7 hoy son inocuas.

## (2) V183-01 CORREGIDO; V183-03 CORREGIDO
V183-01, con el script completo sobre copia2 (sha_predicado = sha256 de las constantes y funciones que extrae banco_paridad._JS mas cambio_detector.js):
- A) index.html tal cual: avisos [] (sha 1a7cd740...).
- B) texto de un modal cambiado ("Estado al 2026-11-13:" a otro texto): avisos [], resultados y noches identicos a la base (True, True). Es el caso que antes daba aviso falso.
- C) un comentario dentro de isValidDetection: 1 aviso, sha b539f6bc....
- D) una linea agregada a cambio_detector.js: 1 aviso, sha 58f8b3dd....
Limite: el sha usa la misma lista de nombres que banco_paridad._JS, asi que no ve una funcion que isValidDetection llame y que no este en esa lista (misma vara que el banco).
V183-03:
- Ventanas del JSON: historia MODIS 03-01 a 11-01, VIIRS 375 y 750 03-01 a 11-10; adopcion MODIS 11-02 a 11-14, VIIRS 11-11 a 11-14; contiguas, sin solape ni hueco (v3check.py); la ventana guardia_viirs ya no existe.
- 0 filas de noches cuyo K tenga fuente distinta a la de su ventana (historia = tag, adopcion = guardia).
- La lista de desacuerdos coincide exacto con las noches en que via y K difieren entre pasadas pareadas, en las 6 ventanas (60, 233, 148, 8, 3, 2; sobran 0, faltan 0).
- Pagina (navegador real): 2 botones de ventana ("Historia: desde marzo hasta la adopcion", "Desde la adopcion"); 72 comprobaciones de tarjetas (2 refs x 2 ventanas x 3 sensores x 6 filas, mas el rango mostrado) contra el JSON nuevo: 0 diferencias; avisos vacios.

## (3) Recalculo con mi conteo (mi2.py, sin usar funciones de comparacion_via_k.py) contra el JSON nuevo
tabla|historia|VIIRS750 (ventana 03-01 a 11-10): via TP 309, FN 20, FP 25, TN 5022, protegidas 131, perdidas 0; K TP 251, FN 78, FP 73, TN 4974, protegidas 131, perdidas 1; pares 11554. Coincide exacto con el JSON. Las otras 5 claves tabla (historia MODIS, historia VIIRS375, adopciones) tambien: `diferencias: 0`. Nota: use mi ref_remota3 (cons 00ade150) y el JSON nuevo declara cons 01eb56d6; con ventanas que terminan antes del 11-10 no hay diferencia, pero no verifique que esa referencia sea byte a byte la de 01eb56d6 en esas fechas (el coincidir exacto lo sugiere). Los datos de via y guardia son los del worktree actual.
