> Nota de quien orquesta (S157): los scripts que este informe cita en `D:\vrp-trabajo\temporales\verif_s157\` se copiaron a `verificador/scripts/` con la raíz del repo relativa al archivo; `publicadas.py Llaima Villarrica` se re-corrió desde ahí y dio los mismos números. El resto del informe es del verificador, sin cambios.

# Verificador con contexto limpio del ensayo del reemplazo (tarea 1.24, paso c, S157)

Árbol auditado: `D:\vrp-trabajo\s157-ensayo-reemplazo`, rama `s157-ensayo-reemplazo`, HEAD `5c26fb7c2` (el commit
del ensayo, sobre `57d18ad78`). No modifiqué ningún archivo del repo salvo este informe. Mis scripts y salidas
están en `D:\vrp-trabajo\temporales\verif_s157\` (`analisis.py`, `frontera.py`, `duplicados.py`,
`publicadas.py`, `rerun\`).

Pregunta: ¿de qué maneras puede estar mal el ensayo, o engañar a quien aplique el reemplazo (paso d)?

Resumen en una línea: **la mecánica del reemplazo está sana** (fuera de la ventana no cambia un byte, no hay claves
repetidas, no hay pasadas duplicadas con hora distinta, todo el reproceso es de un solo commit de K y coincide en
comportamiento con los records de K que ya están en producción). **Lo que engaña está en lo que el PASA no dice**:
la frontera única del tablero queda mal se mueva o no, el tope del 2 % es ciego a un sensor entero perdido en un
trozo, y las 89 pasadas que quedan en C0 publican 40 veces en una serie que el operador leerá como K.

Los números de publicación de este informe salen de un port en Python de `mirovaEqVrp`
(`frontend/index.html:1162`), no del predicado del tablero ejecutado con node (A97). Por eso los marco como
aproximados: el criterio es el mismo (summit, centroide del cúmulo dentro del `inner_radius_km`, `pc.vrp_mw > 0`,
tope 50.000), pero no lo corrí en el navegador.

---

## 1. No existe una frontera de detector correcta si se aplica a 10 volcanes y Chillán queda aparte

- **ARCHIVO:LÍNEA**: `frontend/cambio_detector.js:26` (`const DATOS_K_DESDE_UTC = "2026-09-18T00:00:00Z";`, una sola
  fecha para todos los volcanes); `scripts/auto_audit_weekly.py:415-435` (`detector_de_noche` y `_detector` usan esa
  misma fecha global); `tests/test_cambio_detector_frontera_s155.py` (`test_la_frontera_declarada_es_la_de_los_datos`,
  recorre los 11 Tier A con la misma fecha).
- **QUÉ PASA**: la frontera es global, pero después del reemplazo los 10 volcanes tendrán K desde el 2025-02-15 y
  Nevados de Chillán seguirá en C0 hasta el 2026-09-17. Ninguna fecha única es verdad para los 11. El plan
  (`tasks/BLOQUE_ARRANQUE_S157.md` en `loop/activo`, punto 2: «En el mismo PR mover DATOS_K_DESDE_UTC») supone
  que sí la hay. Ni `ensayo.py` ni el `README.md` del ensayo lo mencionan.
- **CÓMO SE VE EN EL TABLERO**: si la frontera no se mueve, la línea amarilla y el aviso dicen que los datos de los
  10 volcanes anteriores al 18-sep son del detector viejo cuando ya son de K (incluidos los 74 días del hueco que
  nunca existieron). Si se mueve al 2025-02-15, el aviso le dice al operador que la historia de **Chillán, que es el
  volcán en erupción**, es de K cuando es C0 (5.561 de 5.898 records sin marca). En los dos casos un escalón de
  detector se puede leer como un cambio del volcán, que es justo lo que la marca existía para evitar. Además el
  auto-audit y `scripts/vigilancia_sombra.py:443` siguen esa misma fecha: sin mover, la historia K de los 10 queda
  como «K en noche C0» y sale de la evaluación (`auto_audit_weekly.py:507-509`); movida, los C0 de Chillán quedan
  como `sin_marca`.
- **CÓMO REPRODUCIRLO**:
  ```
  python -c "import json; r=json.load(open('data/mirova_equivalent/NevadosDeChillan.json',encoding='utf-8'))['records']; ..."
  Chillan records desde 2025-02-15 5898 con marca 337 antes 09-18 con marca 0
  ```
  El test exige, con la fecha que se elija, 0 records con marca antes de ella y al menos 95 % con marca después.
  Con 2025-02-15, Chillán da 337 de 5.898 (5,7 %) y falla; con 2026-09-18, los 10 volcanes reemplazados traen marca
  antes (por ejemplo Chaitén: 6.060 reemplazados + 881 agregados con `codigo_sha`) y fallan.
- **CONFIANZA**: CONFIRMADO (código leído, conteo de Chillán corrido). El estado post-aplicación de los 10 lo deduzco
  del resultado en memoria de `reemplazar_ventana` (todos los records del reproceso traen `codigo_sha`, ver §Limpio).
- **GRAVEDAD**: 4.

## 2. El PASA no certifica cobertura: un sensor entero perdido en un trozo de 37 días pasa el tope del 2 %

- **ARCHIVO:LÍNEA**: `scripts/reemplazar_ventana_reproceso.py:118-121` (la fracción es global por volcán:
  `solo_operacional / operacional_en_ventana`, tope `0.02` en la línea 106); `ensayo.py:70` (el veredicto es sólo el
  código de salida de ese tope).
- **QUÉ PASA**: el tope compara contra toda la ventana de 19 meses y 8 sensores. Un trozo es 1/16 de la ventana y un
  sensor 1/8 de las pasadas, así que perder un sensor completo en un trozo entero es del orden de 1 % y pasa. El
  `README.md` del ensayo dice «Los 10 pasan el tope del 2 % con margen»; eso es cierto y no dice nada de si el
  reproceso está completo. Quien sí lo dice es `cobertura.py`, pero su salida no es una compuerta: nadie la exige.
- **CÓMO SE VE EN EL TABLERO**: si pasa, el operador vería durante un mes un sensor con su historia vieja (C0, que en
  VIIRS 375 publica en 85 a 88 % de las pasadas en que MIROVA no vio nada) intercalado con los demás en K. Hoy no pasó
  (ver §Limpio: 89 pasadas faltantes en total, máximo 20 por volcán), pero el riesgo es real para el reemplazo de
  Chillán, cuyos trozos se están relanzando partidos (runs 39363774747 y 39363796988, trozos de 16 a 19 días).
- **CÓMO REPRODUCIRLO**: `python D:\vrp-trabajo\temporales\verif_s157\publicadas.py <10 volcanes>`, que quita del
  reproceso en memoria todo `VIIRS_SNPP` entre 2025-07-13 y 2025-08-18 (el trozo 5) y llama a `reemplazar_ventana`:
  ```
  Chaiten  SINTETICO sin VIIRS_SNPP en 2025-07-13..08-18: quitados 60, solo_op 69 de 6069 = 0.0114 -> PASA
  Llaima   ... quitados 57, solo_op 63 de 5747 = 0.0110 -> PASA
  Villarrica ... quitados 55, solo_op 55 de 6590 = 0.0083 -> PASA
  Villarrica SINTETICO sin SNPP 375+750 en ese trozo: solo_op 110 = 0.0167 -> PASA
  ```
  Los 10 volcanes dan PASA con un sensor entero perdido en ese trozo; Villarrica da PASA aun perdiendo los dos
  sensores de Suomi NPP.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3.

## 3. Las 89 pasadas que quedan en C0 publican 40 veces, y el tablero no las distingue

- **ARCHIVO:LÍNEA**: `scripts/reemplazar_ventana_reproceso.py:79-81` (la pasada sin par se conserva tal cual, sin
  `regimen`); `frontend/index.html:1162-1183` (`mirovaEqVrp` no lee `regimen`).
- **QUÉ PASA**: el `README.md` del ensayo (punto 2) reconoce las 89 pasadas C0 y dice que «se distinguen por esa
  marca». Se distinguen en el JSON, no en pantalla. Ningún script del ensayo cuenta cuántas de ellas publican. Con el
  port de `mirovaEqVrp`, publican 40, y pesan mucho porque el fondo K casi no publica en algunos volcanes.
- **CÓMO SE VE EN EL TABLERO**: en Llaima quedarían 17 publicaciones en 19 meses, 2 de ellas C0 (12 %); en Copahue 46,
  5 de ellas C0 (11 %). El caso más visible: **Puyehue Cordón Caulle 2026-07-13 02:05 MODIS_TERRA a 5,0 MW** (el tope
  D9 exacto), una pasada `standard` que el reproceso no trajo. También Planchón Peteroa 2025-04-09 05:48 NOAA-21 750 a
  0,745 MW y PCC 2026-09-11 05:54 NOAA-20 a 0,662 MW. Son barras de C0 dentro de una historia K, sin marca visual.
- **CÓMO REPRODUCIRLO**: `python D:\vrp-trabajo\temporales\verif_s157\publicadas.py ...` (salida cruda, columna
  «islas C0 en ventana N (publicadas M)»):
  ```
  Chaiten 9 (5)  Copahue 11 (5)  Isluga 6 (3)  Lascar 6 (4)  Lastarria 6 (0)  Llaima 6 (2)
  PlanchonPeteroa 20 (10)  PuyehueCordonCaulle 17 (10)  Tupungatito 8 (1)  Villarrica 0 (0)
  ```
  De las 89, 31 tienen record operacional `standard` (el gránulo existía; repetir el trozo debería traerlas, como
  dice el README) y 58 son `nrt` de Suomi NPP del 2026-08-05/06 (`deficit_por_trozo.md`). Que el estándar de esas 58
  no exista en CMR lo dejé SIN VERIFICAR, igual que el README.
- **CONFIANZA**: CONFIRMADO el conteo de islas y de su magnitud; las 40 publicaciones son aproximadas (port de
  `mirovaEqVrp`, no node).
- **GRAVEDAD**: 3.

## 4. El ensayo no mide el cambio en la unidad del tablero, y su docstring dice que sí

- **ARCHIVO:LÍNEA**: `experiments/_s154_reproc_k/ensayo_s157/ensayo.py:13-14` («cuantos reemplazos cambian `vrp_mw` o
  `distance_class` (que es lo que el tablero publica)») y `:66` (compara `record.vrp_mw`); el tablero publica
  `primary_cluster.vrp_mw` (`frontend/index.html:1181`) y el núcleo F5 en VIIRS 375.
- **QUÉ PASA**: `reemplazos_que_cambian_vrp_mw` mide un campo que el tablero no publica (A10). El `README.md`, punto 3,
  lo corrige a medias («no se pasó por `isValidDetection`»), pero el docstring sigue diciendo lo contrario y
  `resumen.json` no trae ningún conteo de publicaciones. El cambio real es grande y nadie lo puso por escrito.
- **CÓMO SE VE EN EL TABLERO**: publicaciones en la ventana, antes y después (port de `mirovaEqVrp`):
  ```
  Chaiten 2414 -> 399    Copahue 2096 -> 46    Isluga 2231 -> 1399   Lascar 2446 -> 2674
  Lastarria 1785 -> 1087 Llaima 2133 -> 17     PlanchonPeteroa 2160 -> 620
  PuyehueCordonCaulle 3884 -> 1796   Tupungatito 2067 -> 989   Villarrica 2761 -> 86
  ```
  Es el efecto buscado de K (los negativos limpios dejan de publicar), pero el operador verá desaparecer del 70 al
  99 % de la historia publicada de Llaima, Copahue, Villarrica y Chaitén en un solo commit. Lo que **no está probado
  por nadie en este ensayo**: cuántas alertas protegidas de MIROVA (1 MW o más) de estos 19 meses pasan de publicadas
  a no publicadas. La regla de adopción midió dos ventanas (V1 y V2), no toda la historia. No lo corrí.
- **CÓMO REPRODUCIRLO**: `publicadas.py`, línea «publicadas en ventana antes N -> despues M».
- **CONFIANZA**: CONFIRMADO que el campo medido no es el publicado; números de publicación aproximados (port);
  el cruce con alertas protegidas, NO PROBADO.
- **GRAVEDAD**: 3.

## 5. El script no comprueba que todos los records vengan del mismo código

- **ARCHIVO:LÍNEA**: `scripts/reemplazar_ventana_reproceso.py:59-61` (sólo exige `regimen.perfil`; `codigo_sha` no se
  mira).
- **QUÉ PASA**: un reproceso armado con trozos de commits distintos pasa igual. Hoy no importa para los 10: todos los
  records traen el mismo sha (abajo). Pero los relanzamientos de Chillán corren sobre `57d18ad78`, no sobre el commit
  del run original `3695f675` (el bloque decía «sobre el MISMO commit del run»). Entre esos dos commits `pipeline/`,
  `volcanoes.yaml` y `scripts/run_pipeline.py` sólo difieren en dos perfiles nuevos de A/B, así que el detector es el
  mismo; el script no lo habría detectado si no lo fuera.
- **CÓMO SE VE EN EL TABLERO**: nada hoy. Si algún día un trozo se relanza sobre un código con otro detector, la
  serie mezclaría dos detectores con la misma etiqueta de perfil.
- **CÓMO REPRODUCIRLO**:
  ```
  gh api repos/MendozaVolcanic/VRP-chile/actions/runs/39363774747 --jq ...  -> head_sha 57d18ad782ff...
  git diff --stat 3695f67580e8 b5ed4f1e9 -- pipeline/ volcanoes.yaml scripts/run_pipeline.py
   pipeline/profiles/_s154_ab_diurno_k_control.yaml | 22 ++++  _s154_ab_diurno_k_on.yaml | 20 ++++
  ```
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

## 6. La escritura con `--aplicar` no es atómica, a diferencia de `store._save`

- **ARCHIVO:LÍNEA**: `scripts/reemplazar_ventana_reproceso.py:131-132` (`open(op_path, "w")` y `json.dump` directo);
  `pipeline/store.py:252-256` (escribe a `.json.tmp` y hace `os.replace`, justo por este motivo, S120).
- **QUÉ PASA**: un corte a mitad de escritura deja truncado un JSON de 15 a 28 MB.
- **CÓMO SE VE EN EL TABLERO**: el volcán aparece vacío o el tablero no carga su serie, si el archivo truncado se
  llegara a commitear. Se recupera con git.
- **CÓMO REPRODUCIRLO**: lectura de las dos funciones.
- **CONFIANZA**: CONFIRMADO (leído).
- **GRAVEDAD**: 2.

## 7. Récords C0 sin marca después de la ventana: el ensayo no los nombra

- **ARCHIVO:LÍNEA**: fuera del script (están después del 2026-09-17, que el reemplazo no toca).
- **QUÉ PASA**: entre 1 y 4 records MODIS_TERRA `nrt` por volcán, del 2026-09-28, 10-02 y 10-10, siguen sin
  `regimen` dentro del tramo K. Es el F2-08 conocido (lo cita el docstring de `auto_audit_weekly.py:424-427`). No lo
  causa el reemplazo, pero después de aplicarlo serán, junto con las 89 islas, lo único C0 de la serie, y nadie los
  lista en el ensayo.
- **CÓMO SE VE EN EL TABLERO**: en PCC dos de ellos publican (2026-09-28 01:25, 0,852 MW; 2026-10-10 01:05, 0,378 MW).
- **CÓMO REPRODUCIRLO**: `frontera.py` y `publicadas.py` («C0 sin marca despues de la ventana»).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

## 8. Los agregados no tienen ningún tope ni control

- **ARCHIVO:LÍNEA**: `scripts/reemplazar_ventana_reproceso.py:82-83` (todo lo que sobra se agrega, sin límite).
- **QUÉ PASA**: el script se niega si faltan pasadas pero acepta cualquier cantidad de pasadas nuevas. Aquí son 7.518
  (de 2 en Villarrica a 1.303 en PCC). Comprobé que son legítimas: casi todas caen en el hueco 2025-11-16 a 2026-01-28
  (V-15), ninguna está a 10 minutos de una pasada operacional del mismo sensor, y sus posiciones caen a menos de 35 km
  del volcán declarado. Pero un reproceso con records de más por un error de ensamblado pasaría igual. Detalle menor:
  los agregados traen `first_processed_utc` de 2026-10 para pasadas de 2025-11; es coherente con la semántica de
  `store.append_record` («primera vez que la vimos»), pero cualquier estudio de latencia que use ese campo
  (`experiments/_s150_latencia/`) vería latencias de casi un año. No encontré consumidor de producción del campo.
- **CÓMO SE VE EN EL TABLERO**: hoy, 74 días nuevos de datos (111 en PCC), reales y con K. El README lo dice.
- **CÓMO REPRODUCIRLO**: `analisis.py` (`agregados_a_10min_de_op: 0`, `fpu_agregados: 2026-10`) y la comprobación de
  distancias (máximo 32,5 a 34,7 km, 0 sobre 60 km en los 10).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

## 9. Detalles del arnés del ensayo

- `ensayo.py:46-54`: no borra `informe_<Volcan>.json` antes de correr. Si el script cae antes de escribirlo, se leería
  el informe de una corrida anterior; el veredicto saldría ERROR (código 1), pero con números viejos. Gravedad 1,
  CONFIRMADO por lectura.
- `reemplazar_ventana_reproceso.py:62`: claves repetidas en el reproceso se resuelven en silencio (gana la última) y
  un `datetime_utc` vacío cuenta como «fuera de ventana». No pasa en estos datos (0 repetidas, 0 vacíos en los 10).
  Gravedad 1, CONFIRMADO.
- `resumen.json` guarda el sha256 del operacional pero no el del reproceso, y el operacional cambiará con cada NRT
  antes del paso d: los conteos del ensayo describen una foto, no lo que se aplicará. Gravedad 1.

## Sin probar (SOSPECHA o fuera de alcance)

- **Aplicación sobre un checkout atrasado**: el script copia los records fuera de la ventana tal como los leyó. Si el
  paso d corre sobre un archivo más viejo que el remoto, el commit borraría los records NRT escritos entre la lectura
  y el push, o el rebase de un JSON de 28 MB terminaría resuelto a mano. No lo probé; el bloque prevé «aplicar entre
  corridas del NRT» y un `verificar_ventana.py` que no leí. SOSPECHA, gravedad potencial 3.
- **Alertas protegidas de MIROVA en los 19 meses** (punto 4): no crucé contra la referencia.
- **Existencia del estándar en CMR** para las 58 pasadas `nrt` de Suomi NPP del 2026-08-05/06: no consultado.
- **Predicado del tablero ejecutado con node** (A97): usé un port en Python de `mirovaEqVrp`.
- El registro diurno de MODIS Aqua del 2026-07-20 21:45 que el reproceso agrega en Chaitén y PCC: no investigué por
  qué la operacional no lo tenía. Es un efecto del pipeline (mismas opciones de `run_pipeline.py` en
  `reproc-chunked.yml:138-143` y `nrt.yml:188-190`, salvo `--overwrite` y las fechas), no del reemplazo.

---

## VERIFICADO LIMPIO

- **Reproducibilidad**: re-corrí `cobertura.py` y `ensayo.py` con la salida redirigida a
  `D:\vrp-trabajo\temporales\verif_s157\rerun\`. `cobertura.json`, `cobertura.md` y los informes son idénticos byte a
  byte; `resumen.json` es igual salvo `commit_del_arbol` (ahora `5c26fb7c2`, el commit del propio ensayo). El árbol
  quedó limpio (`git status` vacío).
- **Fuera de la ventana no cambia nada**: en memoria, para los 10, la lista de records fuera de la ventana es idéntica
  a la operacional, la salida queda ordenada, las claves son únicas y el conjunto es exactamente operacional unido con
  reproceso. Las llaves de primer nivel son sólo `volcano` y `updated`. Y `json.dumps(op, indent=2)` reproduce el
  archivo en disco byte a byte en los 10, así que la escritura con `indent=2` no reformatea nada fuera de la ventana.
- **Pasadas duplicadas con hora distinta**: 0 pares C0 y K del mismo sensor a 10 minutos o menos en el resultado
  (`duplicados.py`). Los pares de 5 minutos que existen son gránulos MODIS contiguos que ya están igual en la
  operacional (Villarrica: 139 en la operacional, 139 en el reproceso, 139 en el resultado). Ningún día-sensor tiene a
  la vez faltantes y sobrantes (intersección vacía en `cobertura.json`), como afirma el README.
- **Un solo detector en el reproceso**: los records de los 10 traen
  `_s154_reproc_k_historico|3695f67580e8de5fcf3653786ea61def0187ecb4|actions`, que es el `head_sha` del run
  39125546355 (`gh api .../runs/39125546355`, intento 1). Entre `34cea39e4` (adopción de K, el código que escribió los
  records K de producción) y `3695f675` sólo se agrega el perfil aislado, y `pytest tests/test_reproceso_historico_k_s154.py`
  pasa (11 de 11), incluido el que resuelve las constantes del perfil igual a la réplica. La única rama por nombre de
  perfil en el código (`scripts/run_pipeline.py:464`) sólo aplica sin `--volcano`, y el workflow siempre lo pasa.
- **El reproceso se comporta como K de producción**: en la ventana 2026-08-15 a 09-17, el reproceso da por sensor
  píxeles anómalos por record, presencia de `f5_core_vrp_mw`, de `discarded_*` y fracción de publicación del mismo
  orden que los records K de producción posteriores al 18-sep (Villarrica, Llaima, Láscar), y muy distinto de la
  operacional C0 de las mismas fechas (por ejemplo Villarrica MODIS_AQUA 55,05 píxeles por record en C0 contra 0,03 en
  el reproceso y 0,03 en K de producción). Los campos que «faltan» en el reproceso (`f5_core_vrp_mw`, `discarded_*`,
  `diag_vrp_floor_*`) faltan igual en K de producción; los que sobran son geometría de observación y la marca.
- **Frontera de datos contigua**: en los 10, el último record sin marca dentro de la ventana es del 2026-09-17 07:50 a
  07:55, el primero de K del 2026-09-18 01:30 a 01:35, y no hay ningún record con marca dentro de la ventana.
- **Producto**: ningún reemplazo baja de `standard` a `nrt` (pares `standard->standard` y `nrt->standard` solamente);
  todos los agregados son `standard`.
- **Pertenencia al volcán**: las posiciones de hotspot del reproceso caen a menos de 35 km del volcán declarado en los
  10 (ninguna sobre 60 km), así que no hay records de otro volcán colados en el ensamblado.
- **`first_processed_utc`**: ningún record operacional de la ventana lo trae, y el script lo quita de los reemplazos,
  igual que `store.append_record` (`pipeline/store.py:664-669`).
- **Cuentas del README**: 7.518 agregados, 89 faltantes (58 `nrt` de Suomi NPP en el trozo 15 más 31 `standard`),
  74 y 111 días de hueco, 160 trozos verdes de los 10 volcanes y 6 caídos todos de Chillán (5, 6, 7, 9, 11 y 12, según
  la API), todo comprobado contra mis propias salidas.
