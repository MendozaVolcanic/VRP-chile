# Verificador con contexto limpio: Mirova-v1 PR #25 (`Distancia_aprox_*`)

Fecha: 2026-10-16. Código verificado: cabeza del PR `e80f07b4` (traída a `refs/verif/pr25` sin tocar el worktree). El
worktree local `C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Mirova-v1-distaprox`
está en `ee4b54ca`, que es otra cadena de commits: el PR fue aplastado sobre un `main` más nuevo. Los archivos de código
son idénticos entre los dos (el diff entre ambos sólo toca datos), así que lo medido vale para el PR.

Todo lo de abajo corrió sobre copias en `C:\Users\nmend\AppData\Local\Temp\claude\verif_pr25\`. CSV reales tomados de
`origin/main` (`306d3980`, 2026-10-16 05:16 UTC): 1.076 filas OCR, 42.831 del consolidado.

## Veredicto global: MERGEABLE CON ARREGLOS

No hay un camino en que el backfill rompa el OCR ni deje el CSV a medio escribir, y `Distancia_km` queda intacta byte a
byte sobre el CSV real. Pero hay dos problemas de operación que conviene arreglar antes del merge (1a y 1b) y un umbral cuyo
fundamento no se replica (3).

## 1. Riesgo de producción: CON ARREGLOS

**Lo que está bien (medido):**
- Escritura atómica: `.tmp` + `os.replace`, una sola vez al final. Con presupuesto o timeout el CSV no queda a medias.
- Sobre la copia del CSV real, historia entera: 1.078 líneas antes y después, 0 líneas cuyo prefijo viejo cambió (cada
  línea nueva es la vieja + `,` + las seis columnas), cabecera = vieja + `COLUMNAS`, LF, sin BOM, mismo orden de filas
  (`churn.py`).
- Segunda corrida con `--dias 26`: 9,7 s, archivo idéntico (`cmp`), no escribe.
- `merger_maestro.py` selecciona `COLUMNAS_MAESTRO`: las columnas nuevas no llegan al maestro publicable ni a los
  `registro_<Volcan>.csv`.
- Ningún otro workflow escribe `registro_vrp_ocr.csv` (grep de escritores: sólo los pasos de `ocr_workflow.yml`), así que
  el `pull --rebase -X ours` no puede mezclar versiones de ese archivo.
- Un fallo del backfill no frena el OCR: `continue-on-error: true` y el CSV no se toca (`fallas.py`: 429, PNG corrupta,
  volcán desconocido, fecha ilegible, los cuatro dejan el CSV igual).

**1a. Catch-up dentro del job del OCR con `cancel-in-progress: true` (ARREGLAR).** El workflow no corre una vez por hora:
`gh run list` muestra despachos cada 30 min (:00 y :30) más el cron horario, que cae entre :09 y :20. Runs de hoy: 2 a
4 min. La primera vez el backfill gasta su presupuesto entero (15 min, más la fila en vuelo y la subida de la caché): el
job dura unos 18 min y el siguiente disparo llega a los 9 a 20 min. Con `cancel-in-progress: true` ese job se cancela:
se pierde el commit del OCR de esa corrida y la caché no se guarda (el `post` de `actions/cache` sólo guarda si el job
termina bien). El OCR sigue saliendo sólo de las corridas de :30, más o menos una por hora en vez de tres, mientras dure
la puesta al día. Para una pasada cuya estrella cambia antes de la corrida siguiente, perder la corrida es perder su
geometría, que es justo la población que este PR quiere rescatar.
Medido: historia entera **1.580 s (26 min) con las 433 PNG ya en caché**, o sea que el costo es el calado y no la bajada
(el comentario del workflow habla de 31 min con caché vacía). Propuesta: `--max-minutos 5` (cabe en el intervalo mínimo
entre disparos), o llenar la historia una vez a mano antes de activar el paso.

**1b. Todo o nada, y un insumo malo lo deja muerto en silencio (ARREGLAR).** Cualquier excepción en una fila aborta la
corrida entera sin escribir nada y sin guardar los calados: un 429 o 404 de raw, un md5 distinto al del índice, una PNG
ilegible (`UnidentifiedImageError`), un nombre de volcán que `volcanes.py` no conoce (`KeyError`, también desde el
consolidado al armar la tabla) o una `Fecha_Satelite_UTC` que no se puede leer (`DateParseError`); comprobado en
`fallas.py`. Si el error es transitorio, la corrida siguiente lo retoma. Si es persistente (una PNG del archivo dañada
cuyo md5 calza, un volcán nuevo), el paso falla en cada corrida y `continue-on-error` lo pinta verde: es el patrón de
pipeline zombi. Propuesta: `try/except` por fila con método `error` (o saltar la fila), y un aviso visible
(`::warning::`) cuando la corrida no escribe.

**Menores:**
- Ida y vuelta por pandas: `scraper_ocr.py` y `reconciliar_latest.py` reescriben el CSV con pandas. Simulado sobre el CSV
  rellenado: 710 celdas de `Distancia_aprox_pareos` pasan de `11` a `11.0`, y 29, 62 y 76 celdas de `_km`, `_min_km` y
  `_max_km` pierden el cero final (`24.80` a `24.8`). Las filas de los últimos 26 días las vuelve a formatear el backfill
  y las más viejas quedan con el formato de pandas: formatos mezclados y un churn de una vez. No cambia valores.
- `*.tmp` no está en `.gitignore`: si el proceso muere justo al escribir, `git add monitoreo_satelital/` subiría
  `registro_vrp_ocr.csv.tmp`. Probabilidad muy baja (escribir toma milisegundos, al minuto 15 y no al 20).
- Caché con clave `run_id`: una entrada nueva por corrida (unas 48 al día) y sin poda de PNG que ya no se usan; crece
  unos 5 MB al día. Funciona por desalojo LRU, pero restaurarla y guardarla se vuelve más lento con los meses.

## 2. `Distancia_km` intacta: SÍ

Sobre la copia del CSV real, historia entera: columna idéntica fila a fila, y también las 25 columnas viejas
(`churn.py`). A nivel de bytes, 0 líneas con el prefijo viejo cambiado.

## 3. Umbral `PAREOS_MINIMOS = 4`: MIDE LO QUE DICE, PERO NO SE SOSTIENE COMO "SALE DEL DATO"

- `scripts/umbral_pareos.py` reproduce la tabla del docstring: 1.549 pasadas, 1.240 decididas, 38 erradas (3,1 %); de 1
  a 7 pareos, 1 errada de 105.
- La regla es autorreferente: el techo es el error global del mismo control, que incluye a los subconjuntos que se
  evalúan, así que acepta casi siempre el piso de la búsqueda. Buscando desde 1, daría 1. El docstring lo admite («cae
  en el piso de la búsqueda»). El 4 no sale del dato: lo fija el rango de búsqueda.
- **Réplica con otra muestra de imágenes** (las 433 PNG que usó el backfill real; sólo 17 en común con las 331 del
  control del PR): 1.435 pasadas, 1.168 decididas, **44 erradas (3,8 %)**. Por pareos: 4 a 7 → **5 de 59 (8,5 %)**,
  8 a 11 → 2 de 48, menos de 5 → 3 de 20. **"El error no sube con pocos pareos" no se replica.** La regla vuelve a dar 4
  porque 3,7 % ≤ 3,8 %. En ALERTA, cráter leído como lejana: 24 de 773 (3,1 %), contra 17 de 772 (2,2 %) del README.
- Circularidad: el calado usa todas las pasadas de la tabla, incluida la evaluada. Está declarado y el verificador
  anterior lo midió (variante B), así que lo acepto con esa cita.
- **Sesgo de población no medido por el control.** El control son pasadas de la tabla cuyas vecinas de la noche están en
  la tabla. Las filas de destino son pasadas sólo-OCR, cuyas vecinas sólo-OCR **no se descuentan**. Medido en el CSV
  rellenado: **37 de las 270 filas `unico` (18 grupos) comparten el mismo marcador con otra fila de la misma noche**. Por
  ejemplo, Lastarria 2026-06-28 05:36 y 05:54, las dos «únicas» a 15,56 km, cuando la de 05:54 está en la tabla a
  2,70 km. Un marcador puede ser de dos pasadas reales a la misma distancia, pero `unico` ahí no significa atribución
  única, y el README no lo advierte.

Propuesta: o subir el umbral (con esta réplica, de 8 a 12) o reescribir el docstring y el README sin «sale del dato».
Además, marcar como `ambiguo` (o con un método aparte) el `unico` cuyo marcador lo reclama otra fila de la misma noche.

## 4. Casos ambiguos y lugar en el README: SE CUMPLE

- Recalculé los marcadores de las 389 filas VIIRS 375 con cifra OCR > 0 y lectura (`ambiguo.py`): **0 violaciones**. En
  ningún caso la columna trae un marcador a la cifra del OCR y la fila queda con otro valor sin pasar a `ambiguo`.
- El README dice «es un complemento, no una corrección» y da el control: OCR 192 de 192, serie 161 decididas y 158
  acertadas. **Lo reproduje exacto** (`lado.py`). El «197 de 197» del encargo es otra ventana (el informe
  `cambian_lado` de VRP Chile): no hay contradicción.
- Matiz: 78 filas con cifra OCR donde la serie no incluye esa cifra (no hay marcador a esa altura); en **17** las dos
  deciden lados opuestos de forma firme. La mayoría son pasadas diurnas (17-18 h) de Lastarria e Isluga. Esas no van a
  `ambiguo` por diseño. El README ya da la tasa con que acierta cada fuente, pero convendría decir explícitamente que,
  cuando discrepan, en el control acertó el OCR.

## 5. ¿Los tests fallan si se rompe lo que protegen?: EN PARTE

117 en verde en la cabeza del PR. Mutaciones (`mutar.sh`, sobre copias, sólo los 33 tests del PR):

| mutación | resultado |
|---|---|
| quitar `or pareos < D.PAREOS_MINIMOS` | falla `test_calado_debil_no_escribe_valor` (bien) |
| escribir `Distancia_km` alterada | falla `test_distancia_km_queda_byte_a_byte_igual` (bien) |
| `con_cifra_ocr` que no cambia nada | falla `test_marcador_a_la_cifra_ocr...` (bien) |
| **quitar la llamada a `con_cifra_ocr` en `calcular`** | **33 en verde** |
| **volver el `reindex` del scraper a `COLUMNAS_OCR`** | **33 en verde** (el test sólo mira la constante) |
| quitar la condición `!= 'ALERTA_SIN_GEOMETRIA_OCR'` | 33 en verde |

La segunda es la que importa: si alguien revierte ese `reindex`, cada corrida con eventos nuevos borra las seis columnas,
el backfill tiene que recalcular la historia (26 min) y vuelve el problema de 1a. Hace falta un test que corra el guardado
de `procesar` (o al menos busque `reindex(columns=COLUMNAS_GUARDADO)` con frontera de palabra), y otro del backfill con una
fila que tenga cifra OCR y un marcador lejano.

## Lo que no hice

No volví a correr `control_distancia_aprox.py` sobre la muestra del estudio (las 331 PNG no están en disco y bajarlas
duplica la réplica). En su lugar lo corrí sobre una muestra casi disjunta (punto 3). No probé el workflow en Actions:
lo de 1a es una inferencia de los horarios reales (`gh run list`) y de la duración medida en local. Un runner de GitHub
puede ser más rápido o más lento que este computador.

## Archivos

`C:\Users\nmend\AppData\Local\Temp\claude\verif_pr25\`: `churn.py`, `fallas.py`, `lado.py`, `ambiguo.py`, `mutar.sh`,
`mutar_salida.txt`, `run1\` (antes, después y simulación de pandas), `control\` (muestra, salida y log de la réplica).
