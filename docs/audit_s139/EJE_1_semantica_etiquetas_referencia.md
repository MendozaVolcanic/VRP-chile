# S139 eje 1: qué significa de verdad cada etiqueta de la referencia MIROVA

Fecha: 2026-09-13 (hora del servidor, `date -u` en esta sesión: 19:48 a 20:00 UTC).
Alcance: sólo lectura. Nada del repositorio fue modificado salvo este informe y los scripts
en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje1\`.

## 0. Resumen para quien decide

1. **RUTINA no es un negativo.** Es una fila de `latest.php` con `VRP MW = 0.00`. En las
   imágenes de MIROVA esa misma pasada aparece como `VRP = NaN MW`, y NaN lo muestra MIROVA tanto
   para cielo despejado sin foco como para nube y para el borde del barrido del satélite (medio
   cuadro en blanco). Las 80 pasadas RUTINA que miré en imagen eran NaN; entre ellas hay pasadas
   con nube evidente y con borde de barrido. RUTINA garantiza "MIROVA procesó este gránulo y no
   informó VRP", no "MIROVA miró el cráter y no había anomalía".
2. **La tabla `latest.php` no lista todos los gránulos que MIROVA procesa.** De 120 adquisiciones
   que MIROVA dibuja en sus imágenes Latest10NTI, faltan en el consolidado 27: 14 de 60 en VIIRS375,
   13 de 40 en VIIRS750, 0 de 20 en MODIS. La ausencia de fila no es negativo, y una noche "sólo
   RUTINA" tampoco: en 96 noches de volcán así, el OCR recuperó una alerta nocturna de MIROVA en
   otro gránulo de la misma noche y sensor.
3. **FALSO_POSITIVO no es un falso positivo de MIROVA.** Es "MIROVA informó VRP > 0, pero a más de
   `limite_km` del centro". En vivo, MIROVA mostraba en su banner `LOW` y `VERY LOW` para dos de
   estas filas. **ALERTA_TERMICA tampoco es la alerta de MIROVA**: es "VRP > 0 dentro de
   `limite_km`", aunque el banner de MIROVA diga `NONE` (caso en vivo: Lastarria 0,04 MW).
4. **Clasificacion Mirova no viene de MIROVA**: la calcula el scraper con la escala de Coppola,
   cambió de escala en el tiempo y es la llave de filtrado del JSON que alimenta el dashboard, lo
   que deja fuera cualquier alerta de 10 MW o más.
5. Con esto, **hoy no existe un negativo confiable por pasada** en la referencia. Existe un
   "negativo condicionado" si se cruza RUTINA nocturna con una medida de cobertura válida propia
   (nuestro gránulo a la misma hora, sin nube ni borde sobre el radio interno). Definición en §3.

## 1. Cómo se asigna cada etiqueta (código del remoto)

Trabajé sobre `origin/main` de `MendozaVolcanic/Mirova-v1` (último commit 1bfba632d2,
2026-09-13 19:46 UTC). El checkout local estaba 102.948 commits atrás y con cambios propios en
dos workflows, así que no lo usé.

### Canal consolidado (`scraper.py`, lee `https://www.mirovaweb.it/NRT/latest.php`)

| Campo | Condición exacta | Quién lo decide |
|---|---|---|
| `Tipo_Registro = ALERTA_TERMICA` | `vrp > 0` y `dist <= conf["limite_km"]` (`scraper.py:144-150`) | scraper, con VRP y distancia de MIROVA |
| `Tipo_Registro = FALSO_POSITIVO` | `vrp > 0` y `dist > limite_km` (`scraper.py:151-152`) | scraper |
| `Tipo_Registro = RUTINA` | `vrp <= 0` (`scraper.py:153-154`) | scraper |
| `Clasificacion Mirova` | `clasificacion_mirova(vrp, es_alerta)`: `NULO` si no es alerta, si no escala <1 Muy Bajo, <10 Bajo, <100 Moderado, <1000 Alto (`volcanes.py:63-81`, llamado en `scraper.py:156`) | **scraper**, no MIROVA |
| `Fecha_Satelite_UTC` | columna "Time (UTC)" de la tabla (`scraper.py:135,181`) | MIROVA, hora del gránulo |
| `Fecha_Captura_Chile` | la misma hora del gránulo pasada a America/Santiago (`scraper.py:182-184`) | no es la hora de captura del scraper, pese al nombre |
| `Fecha_Proceso_GitHub` | hora Chile de la primera visita que vio la fila; se conserva en visitas siguientes (`scraper.py:166-171`) | scraper |
| llave de fila | `(timestamp, Volcan, Sensor)`, `drop_duplicates(keep='last')` (`scraper.py:199-201`) | una fila por gránulo, se sobrescribe si se revisita |

Lo que observa el scraper: la tabla `latest.php`. La bajé en vivo (528 filas, cabecera
`Time (UTC) | ID Volc | Volcano | VRP MW | Distance km | Sensor`, ventana 05:06 a 17:35 UTC del
13-sep). Muestra **la adquisición más reciente de cada volcán del mundo por sensor** (el máximo de
filas por par volcán-sensor fue 2). No trae nubosidad, cobertura, nivel del banner ni un NaN: 0 de
528 filas con VRP no numérico, y 0 filas con VRP 0 y distancia > 0.

Historia: el tipo `FALSO_POSITIVO` no existía antes del commit 2bd447787ac (2026-01-16 04:49
-0300). La versión c892cbb1063 (2026-01-11) etiquetaba RUTINA toda fila que no fuera alerta, incluso
con VRP > 0 lejano, y le ponía `Clasificacion = "FALSO POSITIVO"` (función `obtener_nivel_mirova`,
líneas 39-45 de esa versión). Tupungatito se agregó en 88349c68bb1 (2026-02-14) con
`"limite_km": 5.0`; hoy vale 7,0 (`volcanes.py:37-38`).

### Canal OCR (`scraper_ocr.py` + `ocr_utils.py`, cron `5 * * * *` en `ocr_workflow.yml:6`)

Lee las imágenes `Latest10NTI.png` (10 últimas adquisiciones con su VRP dibujado) y `Dist.png`
(distancia en función del tiempo, con una estrella para la última detección). Sólo guarda eventos
de las últimas 24 h (`scraper_ocr.py:217-239`) que no estén ya en el consolidado
(`ocr_utils.py:1304-1334`).

| Etiqueta | Condición | Fuente |
|---|---|---|
| `DUPLICADO_LATEST` (no se guarda) | mismo volcán y sensor a ±60 s de una fila del consolidado (`ocr_utils.py:723-746`, `1134-1153`) | scraper |
| `VRP_INVALIDO` (no se guarda) | VRP leído 0 o NaN (`ocr_utils.py:1159-1168`) | scraper |
| `ALERTA_TERMICA_OCR` confianza alta, FASE 1 | grupo de píxeles rojos en el ROI temporal de Dist.png con km ≤ `limite_km + 0,15` (`ocr_utils.py:1184-1218`; `TOLERANCIA_KM = 0.15` en `:923`) | scraper, leyendo el dibujo |
| `ALERTA_TERMICA_OCR` alta o media, FASE 2 | estrella **verde** (alta) o **gris** (media, "detección débil sub-umbral MIROVA") dentro del límite (`ocr_utils.py:1106-1109`) | scraper; la estrella es de la **última** detección |
| `FALSO_POSITIVO_OCR` | fuera del límite, o sin señal (`ocr_utils.py:1110-1111`, `1219-1236`, `1279-1301`), con `guardar=False` en el código actual | scraper |
| `FALSO_POSITIVO_OCR` por reconciliación | ALERTA_OCR con mismo `(timestamp, Volcan, Sensor)` marcado FALSO_POSITIVO en el consolidado (`reconciliar_latest.py:33-51`) | scraper |
| `Clasificacion Mirova` | `clasificacion_mirova(vrp, es_alerta=True)` siempre (`scraper_ocr.py:347`), así que un FALSO_POSITIVO_OCR también lleva clase de intensidad | scraper |
| `Nivel_Anomalia_MIROVA` | texto del banner de MIROVA, sólo desde V30 y sólo para la adquisición más reciente (`scraper_ocr.py:416-420`) | **único campo que sí viene de MIROVA** |
| marca diurna | `12 <= hora UTC <= 23` y VRP ≥ 10 MW baja confianza a media (`scraper_ocr.py:379-385`) | scraper, desde ago-2026 |

## 2. Hallazgos

Ordenados por gravedad. Denominadores y ventanas en cada uno.

### H101. RUTINA incluye pasadas nubladas y bordes de barrido: no es "no había anomalía"
- **ARCHIVO:LÍNEA** `scraper.py:153-154`; `SCRIPT:SALIDA` `experiments/_s139_audit/eje1/imagen_vs_tabla.py` y `imagen_vs_tabla_ampliado.py` (salidas `salida_imagen_vs_tabla*.txt`).
- **QUÉ PASA** Físicamente, un satélite que pasa sobre un volcán cubierto de nubes, o que lo deja
  en el borde de su franja, no puede ver el cráter; MIROVA dibuja esas pasadas como `VRP = NaN MW`,
  igual que una pasada despejada sin foco, y `latest.php` las publica como `0.00`. El scraper las
  vuelve RUTINA sin ninguna distinción. Casos en vivo del 12 y 13 de septiembre: Villarrica
  VIIRS375 07:00:01 (medio cuadro blanco, fuera del barrido), Puyehue-Cordón Caulle y Llaima VIIRS
  07:00:01 (casi todo blanco), Isluga VIIRS375 19:24:00 (borde) y 18:48:02 (nubes brillantes):
  todas son filas RUTINA en el CSV remoto.
- **CÓMO SE VE EN EL DASHBOARD** invisible hoy (el dashboard excluye RUTINA de las métricas,
  `frontend/index.html:1312`). Se vería el día que un banco de prueba use RUTINA como negativo: toda
  detección nuestra en una noche nublada sobre el cráter contaría como falsa alarma, y toda noche
  nublada sin detección nuestra contaría como acierto.
- **CÓMO REPRODUCIRLO** `python experiments/_s139_audit/eje1/imagen_vs_tabla_ampliado.py <CSV remoto>`; comparar con `https://www.mirovaweb.it/OUTPUTweb/MIROVA/VIIRS375/VOLCANOES/Isluga/Isluga_VIIRS375_Latest10NTI.png` (las imágenes rotan cada pasada, se ven otras horas).
- **Números** 80 de 80 filas RUTINA revisadas en imagen eran NaN (32 de la muestra de 4 imágenes, 48 de la de 8). Denominador: 12 imágenes Latest10NTI de 7 volcanes, adquisiciones del 11 al 13 de septiembre de 2026. Control positivo: horas inventadas salen AUSENTE 12 de 12. Ninguna fila RUTINA tuvo VRP dibujado distinto de NaN.
- **CONFIANZA** CONFIRMADO (leído en código, visto en imagen, cruzado con el CSV).
- **GRAVEDAD 5** Un banco de negativos basado en RUTINA mediría la nubosidad de Chile, no nuestras falsas alarmas.

### H102. `latest.php` omite gránulos VIIRS que MIROVA sí procesa; noche "sólo RUTINA" no es negativa
- **ARCHIVO:LÍNEA** mecanismo de captura `scraper.py:114-201` (una fila por gránulo, sólo lo que la tabla muestra al momento de la visita); `SCRIPT:SALIDA` `imagen_vs_tabla*.py`, `medir_ocr.py` (`salida_ocr_snapshot.txt`).
- **QUÉ PASA** En una noche, VIIRS pasa varias veces sobre Chile y MIROVA procesa un gránulo por
  pasada. La tabla sólo muestra el último gránulo por volcán y sensor; los intermedios pueden no
  quedar nunca expuestos cuando el scraper la visita. De 120 adquisiciones dibujadas por MIROVA,
  27 no están en el consolidado: VIIRS375 14 de 60, VIIRS750 13 de 40, MODIS 0 de 20. Las 27
  ausentes eran NaN en la imagen, así que en esta muestra no se perdió ninguna detección, pero el
  canal OCR sí muestra que se pierden: 846 ALERTA_TERMICA_OCR, de las cuales 103 caen en una noche
  de volcán cuyo consolidado para ese sensor es sólo RUTINA (96 de ellas nocturnas) y 1 en una noche
  sin ninguna fila. El mecanismo exacto (lote de gránulos que se sobrescriben antes de la visita)
  es SOSPECHA; la omisión es medida.
- **CÓMO SE VE EN EL DASHBOARD** invisible: el operador no tiene forma de saber que para esa pasada
  MIROVA no dejó rastro en la tabla.
- **CÓMO REPRODUCIRLO** mismo script; ejemplo: Villarrica VIIRS375 2026-09-13 06:36:00, 05:00:00 y 2026-09-12 19:18:00 dibujadas en la imagen y ausentes en el CSV.
- **Ventanas** consolidado snapshot 36.255 filas, 2026-01-10 19:06 a 2026-09-07 13:30 UTC; OCR snapshot 937 filas, 2026-01-20 05:12 a 2026-09-07 06:54 UTC. Muestra de imágenes: 11 al 13 de septiembre de 2026, 12 pares volcán-sensor.
- **CONFIANZA** CONFIRMADO la omisión y el cruce; SOSPECHA el mecanismo y la tasa (muestra de 2 días).
- **GRAVEDAD 4** Contar "noches sin fila" o "noches sólo RUTINA" como negativas agrega falsos negativos a la referencia.

### H103. FALSO_POSITIVO significa "MIROVA vio algo lejos", no "MIROVA descartó una falsa alarma"
- **ARCHIVO:LÍNEA** `scraper.py:151-152`; comentario engañoso en `scripts/rebuild_mirova_from_consolidado.py:66,69` ("MIROVA-rejected", "MIROVA-confirmed false positive").
- **QUÉ PASA** Es un foco con VRP > 0 que MIROVA ubicó a más de `limite_km` del centro de su
  grilla: puede ser un incendio, un campo geotermal o una fuente volcánica lejana. MIROVA no lo
  llama falso positivo; en vivo el banner decía `LOW` para Láscar VIIRS375 06:36:00 (1,37 MW a
  24,93 km) y `VERY LOW` para Copahue 06:36:00 (0,28 MW a 10,88 km), las dos FALSO_POSITIVO en el
  CSV. Además, la tabla trae una sola distancia por gránulo: si MIROVA agrega o elige un foco lejano
  más fuerte, un foco débil dentro del radio podría quedar escondido bajo la etiqueta FALSO_POSITIVO
  (SOSPECHA, no verificado).
- **CÓMO SE VE EN EL DASHBOARD** invisible (clase `NULO`, excluida).
- **CÓMO REPRODUCIRLO** fila `2026-09-13 06:36:00,Lascar,VIIRS375,1.37,24.93,FALSO_POSITIVO` del CSV remoto vs `Lascar_VIIRS375_Latest10NTI.png` en vivo.
- **Números** 830 FALSO_POSITIVO en el snapshot; distancia mediana 19,56 km, mínima 3,77; 482 diurnos y 348 nocturnos; 12 a menos de `limite_km + 1` km.
- **CONFIANZA** CONFIRMADO la semántica; SOSPECHA el enmascaramiento de un foco interior.
- **GRAVEDAD 3** No sirve como negativo del radio sin probar el enmascaramiento; tampoco es positivo.

### H104. ALERTA_TERMICA no es el nivel de alerta de MIROVA: incluye detecciones con banner NONE
- **ARCHIVO:LÍNEA** `scraper.py:147-150`; `volcanes.py:71-81`.
- **QUÉ PASA** Cualquier VRP > 0 dentro del radio queda como ALERTA, aunque sea un píxel apenas
  sobre el umbral que MIROVA misma no eleva a anomalía. En vivo: Lastarria VIIRS375 2026-09-13
  06:36:00, 0,04 MW a 1,55 km, ALERTA_TERMICA, con banner de MIROVA `Thermal anomaly: NONE`.
- **CÓMO SE VE EN EL DASHBOARD** el operador ve estos puntos como alertas MIROVA de "Muy Bajo".
- **Números** CSV remoto (37.319 filas, hasta 2026-09-13 12:35 UTC): 1.450 ALERTA_TERMICA, 287 con VRP < 0,1 MW, 60 con VRP < 0,05 MW, mínimo 0,01.
- **CÓMO REPRODUCIRLO** `imagen_vs_tabla.py` (línea final) y la imagen `Lastarria_VIIRS375_Latest10NTI.png`.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 3** Un positivo del banco puede ser lo que MIROVA considera "nada"; hay que estratificar.

### H105. El dashboard compara contra MIROVA sin el canal OCR
- **ARCHIVO:LÍNEA** `.github/workflows/sync-mirova-csv.yml:50-52` (sólo baja `registro_vrp_consolidado.csv`), `:79-110` (reconstruye `data/mirova/<Volcan>.json` sólo desde ese CSV); el OCR sólo lo baja `audit-weekly.yml:57-58`.
- **QUÉ PASA** Las alertas que MIROVA dibuja en gránulos que `latest.php` no expuso (H102) no llegan
  al dashboard. En la métrica del navegador (`frontend/index.html:1249-1320`) una detección nuestra
  en esa pasada cuenta como FP y la alerta de MIROVA no cuenta como FN.
- **CÓMO SE VE EN EL DASHBOARD** puntos MIROVA ausentes en el gráfico de un volcán; precisión mostrada más baja y recall más alto que el real.
- **Números** 846 ALERTA_TERMICA_OCR; 307 comparten llave exacta con una ALERTA del consolidado; quedan 539 que sólo existen en el OCR (snapshot al 2026-09-07). No medí cuántas caen dentro de la ventana que muestra el dashboard.
- **CÓMO REPRODUCIRLO** `python experiments/_s139_audit/eje1/medir_ocr.py <ocr> <consolidado>`, sección "cruce".
- **CONFIANZA** CONFIRMADO que el workflow no lo consume; SOSPECHA el efecto numérico en la métrica (no reproduje el cálculo del navegador).
- **GRAVEDAD 3**

### H106. El JSON del dashboard descarta toda alerta MIROVA de 10 MW o más
- **ARCHIVO:LÍNEA** `scripts/rebuild_mirova_from_consolidado.py:76` (`VALID_CLASSES = {"Muy Bajo", "Bajo"}`) y `:86-89`.
- **QUÉ PASA** El filtro es por la clase de intensidad que calcula el scraper, no por el tipo. Una
  fase efusiva o una erupción con VRP de 10 MW o más queda como `Moderado` o `Alto` y se descarta
  en silencio del JSON que lee el dashboard: justo el caso que más importa ver comparado.
- **CÓMO SE VE EN EL DASHBOARD** el día de un evento fuerte, MIROVA desaparece del gráfico y de la métrica de ese volcán.
- **Números** hoy 0 filas afectadas: el máximo VRP de ALERTA_TERMICA en el snapshot es 4,75 MW. Latente.
- **CÓMO REPRODUCIRLO** leer las líneas citadas; inyectar una fila con VRP 15 y correr el script con `--source` sobre una copia.
- **CONFIANZA** CONFIRMADO (código). **GRAVEDAD 3** Latente, pero cae en el escenario de alerta real.

### H107. Diurnos y artefactos solares viven como ALERTA_TERMICA_OCR de confianza alta
- **ARCHIVO:LÍNEA** `scraper_ocr.py:379-385` (marca sólo desde ago-2026, sin reprocesar lo previo); el loader los toma igual: `pipeline/mirova_csv_loader.py:109,147-149` filtra sólo por tipo, sin mirar `Confianza_Validacion` ni hora.
- **QUÉ PASA** De día, la nube refleja el sol en el infrarrojo medio y MIROVA grafica VRP fantasma (regla A76). El OCR los guardó como alerta.
- **Números** 6 ALERTA_TERMICA_OCR diurnas de 10 MW o más, entre ellas Láscar 2026-06-15 17:24:01 VIIRS375 760,60 MW (alta), Isluga 2026-06-21 18:36:00 VIIRS 37 MW (alta), Láscar 2026-05-05 19:30:00 MODIS 15 MW (alta). En total 92 ALERTA_OCR diurnas de 846 (3 MODIS, 4 VIIRS, 85 VIIRS375).
- **CÓMO SE VE EN EL DASHBOARD** invisible (el dashboard no usa el OCR, H105); visible en auditorías que usan el loader.
- **CÓMO REPRODUCIRLO** `medir_ocr.py`, sección "dia/noche".
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 3** para un banco que no filtre día.

### H108. El OCR asigna a varios eventos la distancia de otra adquisición, y guarda la estrella gris como alerta
- **ARCHIVO:LÍNEA** `ocr_utils.py:1037-1044` (la estrella marca "la distancia de la última detección"), `:1106-1109` (gris dentro del límite pasa a ALERTA_TERMICA_OCR media), `scraper_ocr.py:289-300` (se aplica evento por evento).
- **QUÉ PASA** Cuando un evento no tiene grupo de píxeles propio, se valida con la estrella, que
  describe sólo el último foco. Si en la misma corrida hay varios eventos, todos heredan la misma
  distancia, aunque sean de pasadas de otra hora o de día. La estrella gris es, según el propio
  código, una detección que el banner de MIROVA no eleva.
- **Números** 9 grupos (volcán, sensor, corrida) con más de una fila validada por estrella, 18 filas, y en los 9 grupos una sola posición Y para todas. Ejemplo: Isluga VIIRS375 2026-08-31 17:30:02 (15,44 MW, diurna) y 2026-09-01 05:36:01 (0,26 MW), ambas Y=291 en la corrida 2026-09-01 05:01:34. 15 ALERTA_OCR por estrella gris; 367 más con notas de estrella de versiones antiguas sin color identificable.
- **CÓMO SE VE EN EL DASHBOARD** invisible.
- **CÓMO REPRODUCIRLO** `medir_ocr.py`, sección "reutilizacion de la misma estrella".
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2**

### H109. Filas históricas con etiqueta de otra regla: Tupungatito (límite 5 km) y RUTINA con VRP > 0
- **ARCHIVO:LÍNEA** versión 88349c68bb1 de `scraper.py` línea 26 (`"limite_km": 5.0`); hoy `volcanes.py:37-38` (7,0); versión c892cbb1063 líneas 39-45 y 96-101. `SCRIPT:SALIDA` `medir_consolidado.py`, sección "coherencia".
- **QUÉ PASA** El CSV no se reetiqueta cuando cambia la regla. 5 filas de Tupungatito entre
  2026-02-16 05:30:01 y 2026-02-22 05:18:01 (VRP 0,09 a 0,47 MW a 5,03 a 5,41 km) quedaron
  FALSO_POSITIVO y hoy serían ALERTA; desde 2026-02-23 las filas a 5 a 7 km ya son ALERTA (100).
  El cambio de límite está fechado en el código: el commit 2d025de0a8c (2026-02-23 16:24 -0300)
  pasa `scraper.py:26` de `"limite_km": 5.0` a `7.0`, lo que coincide con el corte que muestran los datos.
  17 filas RUTINA entre 2026-01-10 19:24:01 y 2026-01-14 17:54:00 tienen VRP 0,43 a 18,66 MW
  (focos lejanos de antes de que existiera FALSO_POSITIVO).
- **CÓMO SE VE EN EL DASHBOARD** 5 alertas MIROVA de Tupungatito que no aparecen.
- **Números** 22 discrepancias de 36.255 (snapshot) y 22 de 37.319 (remoto), todas antes de 2026-02-23. Control positivo: fila incoherente inyectada detectada.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2**

### H110. `Clasificacion Mirova` es un campo del scraper y cambió de escala
- **ARCHIVO:LÍNEA** `volcanes.py:63-81`; `scraper_ocr.py:345-347`; versión c892cbb1063 `obtener_nivel_mirova`.
- **QUÉ PASA** No viene de MIROVA. En el consolidado hay 17 filas "Bajo" con VRP < 1 (2026-01-11 a 2026-01-15); en el OCR hay 196 ALERTA "Medio" (1,00 a 4,98 MW, hasta 2026-06-10) de una escala ya retirada, y los FALSO_POSITIVO_OCR llevan clases de intensidad (Alto 4, Bajo 35, Medio 41, Muy Alto 1, Muy Bajo 10) en vez de NULO. Cualquier filtro por clase (H106, `frontend/index.html:1312`) hereda estas mezclas.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2**

### H111. En VIIRS750 y MODIS la imagen trunca el VRP a entero: el OCR no ve detecciones bajo 1 MW
- **ARCHIVO:LÍNEA** documentado en `tasks/AUDITORIA_OCR_EMPIRICA_2026-06.md` §J1 y §K del repo Mirova-v1; comprobado en vivo.
- **QUÉ PASA** Puyehue-Cordón Caulle VIIRS 2026-09-13 06:00:02 y 05:18:01 aparecen dibujadas como `VRP =0 MW` y en la tabla son 0,45 y 0,63 MW a 7,83 km (ALERTA_TERMICA). El canal OCR, en esos dos sensores, sólo agrega positivos de 1 MW o más, y ninguna imagen sirve para inferir un negativo en ellos.
- **CONFIANZA** CONFIRMADO (2 casos en vivo más la auditoría del repo). **GRAVEDAD 2**

### H112. El scraper primario falla en verde y no tiene cron propio
- **ARCHIVO:LÍNEA** `scraper.py:210-211` (captura toda excepción, sólo escribe bitácora); `.github/workflows/main.yml:3-4` (sólo `workflow_dispatch`, lo dispara un cron externo según `tasks/AUDITORIA_TECNICA_2026-06.md:13`).
- **QUÉ PASA** Si `latest.php` cambia de formato o no responde, el job termina bien sin filas nuevas. Mitigado aguas abajo: `scripts/auto_audit_weekly.py:309-319` mide la frescura del CSV entero.
- **Números** históricamente sano: 241 de 241 días con filas; por volcán y sensor, noches con al menos una fila nocturna entre 97,9 % (Isluga MODIS, 235 de 240) y 100 %.
- **CONFIANZA** CONFIRMADO el código; sin falla observada. **GRAVEDAD 2**

### H113. Nombres de columnas de hora que inducen a error
- **ARCHIVO:LÍNEA** `scraper.py:182-184`.
- **QUÉ PASA** `Fecha_Captura_Chile` es la hora del satélite en hora chilena, no la hora en que se capturó el dato; la primera visita del scraper es `Fecha_Proceso_GitHub`. Latencia primera visita menos adquisición: mediana 3,34 h, p95 9,35 h, máximo 39,69 h, ninguna negativa (36.151 filas con ambas fechas).
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 1**

### H114. Borde del radio distinto entre canales
- **ARCHIVO:LÍNEA** `scraper.py:144` (`dist <= limite_km`) vs `ocr_utils.py:923,1089,1188` (`<= limite_km + 0.15`).
- **QUÉ PASA** Un foco a 5,1 km de un volcán con límite 5 es FALSO_POSITIVO si viene de la tabla y ALERTA_OCR si viene de la imagen. **CONFIANZA** CONFIRMADO. **GRAVEDAD 1**

## 3. Conclusión operativa: definiciones para el banco de prueba

**Unidad base: la pasada** (una fila del consolidado es un gránulo por volcán y sensor; mediana 2
por noche en los 3 sensores). **Unidad de decisión: la noche de volcán por sensor**, porque así
lo vive el operador (regla A94) y porque H102 hace poco fiable la pasada individual. Sólo noche:
VRP Chile no procesa día y MIROVA publica artefactos solares de día (H107). Supuesto que usé:
noche = hora solar local antes de las 06 o desde las 18.

**Positivo válido (noche de volcán, sensor S):** al menos una pasada nocturna con
- `ALERTA_TERMICA` del consolidado, fechada desde 2026-01-16 (Tupungatito desde 2026-02-23, o
  reetiquetada con 7 km), o
- `ALERTA_TERMICA_OCR` nocturna, `Confianza_Validacion = alta`, validada por grupo de píxeles o
  estrella verde, fuera de los 9 grupos con estrella compartida, y en VIIRS750 o MODIS con la
  advertencia de ±1 MW.
Estratificar por VRP (bajo 0,1 MW y resto) porque parte de estos positivos tienen banner NONE (H104).

**Negativo válido:** en la referencia sola, **no existe**. RUTINA mezcla despejado, nube y borde
de barrido (H101), y faltan gránulos (H102). Lo más cercano que se puede construir:
"negativo condicionado" = noche de volcán y sensor S con
1. al menos una fila RUTINA nocturna del consolidado,
2. ninguna ALERTA ni FALSO_POSITIVO del consolidado en esa noche y sensor, ni ALERTA_OCR de ningún tipo,
3. **y** una prueba independiente de que el cráter se vio: un gránulo nuestro a ±10 min de esa
   RUTINA cuyo radio interno esté dentro del barrido y sin nube. Esa condición la tiene que medir
   nuestro pipeline; la referencia no la trae.
Sin la condición 3, esa noche es "negativo débil" y no debería entrar a una tasa de falsas alarmas.

**Sin información:** noche sin fila nocturna para ese sensor; noche con sólo FALSO_POSITIVO
(hasta probar si puede esconder un foco interior, H103); filas diurnas; RUTINA antes de 2026-01-16;
Tupungatito antes de 2026-02-23 con distancia entre 5 y 7 km; gránulos que MIROVA dibuja y la tabla
no lista.

**Advertencias para el banco:**
- La distancia de MIROVA se mide desde su centro de grilla y el radio es el del scraper; ambos coinciden con `inner_radius_km` del frontend, pero no con la distancia a nuestro cráter.
- El CSV no se reetiqueta al cambiar reglas: fijar la versión de la regla y recalcular el tipo desde VRP y distancia, no leer `Tipo_Registro`.
- No filtrar por `Clasificacion Mirova` (H106, H110).
- Las muestras de imagen son de 2 días de septiembre; la tasa de gránulos omitidos (27 de 120) debe medirse sobre más días antes de usarse como número.

## 4. VERIFICADO LIMPIO

| Qué | Resultado | Cómo se confirma |
|---|---|---|
| Radio del scraper igual a `inner_radius_km` del frontend | Coinciden los 11: Isluga 5, Láscar 5, Lastarria 3, Tupungatito 7, Planchón-Peteroa 3, NdC 5, Copahue 4, Llaima 5, Villarrica 5, PCC 20, Chaitén 5 | `volcanes.py:28-54` (remoto) contra `frontend/index.html:714-755` |
| Duplicados por `(timestamp, Volcan, Sensor)` | 0 en 36.255 | `medir_consolidado.py`, sección duplicados |
| Pares a 5 min mismo volcán y sensor | 12, todos MODIS con VRP 0: gránulos consecutivos de 5 min, no filas repetidas | idem |
| Tipo coherente con la regla actual | 36.233 de 36.255; las 22 restantes son H109, todas previas a 2026-02-23 | idem, sección coherencia |
| Distancia en filas VRP 0 | 0 de 33.994 con distancia > 0; 0 VRP NaN | idem, sección geometría |
| VRP de la tabla igual al dibujado en VIIRS375 | 8 de 8 detecciones idénticas al centésimo | `imagen_vs_tabla_ampliado.py` |
| MODIS completo en la tabla | 20 de 20 adquisiciones de imagen presentes | `imagen_vs_tabla.py` |
| Cobertura diaria | 241 de 241 días con filas; sin huecos de días | `medir_consolidado.py` |
| Latencia | nunca negativa | idem |
| Reconciliación OCR contra tabla | 0 ALERTA_OCR con la misma llave marcada FALSO_POSITIVO en la tabla (las 307 coincidencias exactas son ALERTA) | `medir_ocr.py`, sección cruce |
| Nombre `Peteroa` | 0 filas, sólo `PlanchonPeteroa` | `medir_consolidado.py`, sección Volcan |
| Sensores del CSV y el mapeo del loader | Sólo `MODIS`, `VIIRS`, `VIIRS375`; `normalize_sensor` los manda a MODIS, VIIRS750, VIIRS375 | `pipeline/mirova_csv_loader.py:63-83` y crosstab por sensor |
| Distancia 0 en filas OCR | 588 de 846 ALERTA_OCR con 0; el loader ya no hereda ese 0 (`mirova_csv_loader.py:163-171`) | `medir_ocr.py`, última línea |
| Snapshot local contra remoto | misma semántica: mismas 22 discrepancias y mismas categorías; el remoto sólo suma 1.064 filas hasta 2026-09-13 | `salida_consolidado_remoto.txt` |

Scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje1\`
(`medir_consolidado.py`, `medir_ocr.py`, `imagen_vs_tabla.py`, `imagen_vs_tabla_ampliado.py` y
sus `salida_*.txt`). Las imágenes de MIROVA quedaron en el scratchpad de la sesión y no se
guardaron en el repo; las horas y valores transcritos están escritos dentro de los dos scripts de imagen.
