# Auditoría de #900 y medición para la decisión 3 de #897

- **Hora del servidor** (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date`): `Sat, 24 Oct 2026 13:21:53 GMT`.
- **Commits medidos**: PR #900 head `a7d1c0b91` (base `3bbd18d2c`), worktree `.claude\worktrees\nice-ishizaka-62d0a8` limpio antes y después (`git status --short` vacío). Datos de producción: `origin/main` = `e850152b5` (entre la base del PR y este commit sólo hay commits de datos: `git diff --stat 3bbd18d2c origin/main -- scripts/ tests/test_auto_audit_* .github/workflows/audit-weekly.yml pipeline/fetch.py` vacío). PR en borrador, `mergeStateStatus=CLEAN`, check `pytest` SUCCESS.
- **Modelo y esfuerzo**: Claude Opus 5.5, esfuerzo bajo asignado por quien orquesta; todo lo que sigue sale de comandos de esta sesión.
- **Qué NO miré**: la causa física de los silencios de plataforma (maniobras, LANCE, LAADS); el contenido del frente S159 (`experiments/_s159/cese_snpp/INFORME.md`, rama `s159-pruebas`) más allá de lo que cita el PR; el frontend; los 34 volcanes fuera de Tier A; la cobertura que escribe `pipeline/fetch.py` en los logs del NRT (no está en `data/`); las alertas de MIROVA posteriores al cese (no existen todavía).
- **Scripts y salidas** (todo en esta carpeta): `tools\correr_audit.py`, `tools\comparar.py`, `tools\dias_sin_granulos.py`, `tools\silencio_en_vivo.py`, `rojas\test_base_s161.py`, `corridas\`, `bordes\`, `parteB_dias_sin_granulos.json`, `parteB_salida.txt`, `parteB_silencio_en_vivo.json`, `parteB_silencio_salida.txt`. `root\` es un `git archive` de `origin/main` (data/mirova_equivalent, data/mirova_reference, scripts, pipeline, frontend, volcanoes.yaml).

## En una pantalla

1. #900 hace lo que dice: antes del corte no cambia nada (con los datos reales, simulando el lunes 2026-10-26 y el 2026-11-02, `latest.json`, historial y consola son idénticos a main salvo la clave nueva), MODIS queda intacto, y las 6 pruebas nuevas que deben fallar sin el cambio fallan por aserción contra el código base.
2. El corte es correcto y coherente con el NRT: primer día juzgado 2026-11-03 UTC, la misma regla que `pipeline/fetch.py::cese_cumplido`; el informe del lunes 2-nov no recorta, el del 9-nov sí.
3. El costo que el PR menciona pero el audit no dice en su salida: desde el 9-nov VIIRS queda sin juzgar en recall y magnitud entre ~1 (VIIRS 375) y ~3 semanas (VIIRS 750), y los flags vigentes de #864 salen del veredicto sin ningún aviso (en la simulación del 9-nov, 11 flags pasan a 6). Recomiendo **mergear con un cambio chico**: un aviso informativo de «VIIRS sin juzgar, n bajo el mínimo desde el cese» en consola y en el cuerpo del issue, antes del lunes 9-nov.
4. Parte B: MODIS no tuvo ninguna pasada nocturna en **7 de 2.607 volcán-días** (0,27 %, 2026-03-01 a 2026-10-23, sólo Láscar 3 e Isluga 4, nunca dos días seguidos, nunca los 11 volcanes a la vez); en vivo (10 al 23-oct) **0 de 154** volcán-días de MODIS llegaron con más de 24 h. Por plataforma sí hay silencios: Terra 117 (4,5 %, 11,5 % en octubre), Aqua 72 (2,8 %), Suomi NPP 220 (8,4 %, con 20 días de silencio en los 11 volcanes), NOAA-20 0, NOAA-21 11 (un día).
5. Un día sin record significa «sin gránulo nocturno procesable», no «gránulo sin nada» (el 84,9 % de los records nocturnos no trae cúmulo con magnitud). Pero el archivo de hoy esconde los silencios en vivo, porque los backfills los rellenan: el 2026-10-13 VIIRS estuvo ciego en los 11 volcanes y en el archivo no se nota. Un modo estricto se tiene que diseñar y medir con `first_processed_utc` (existe sólo desde octubre) o con la cobertura del fetch, no con el archivo.

---

## Parte A: revisión de #900

### Qué cambia (leído en `gh pr diff 900` y `git diff 3bbd18d2c a7d1c0b91`)

`scripts/auto_audit_weekly.py`: `leer_ceses` (lee `scripts/ceses_esperados.json`, lleva los sensores a buckets con `our_bucket`, primer día sin la plataforma = día siguiente al cese salvo cese a medianoche), `juzga_desde` (último cese cumplido por sensor), `es_aparte`, `partir_por_plataformas`. En `main()` (líneas 948 a 952 del PR) se parten `mir` y `mir_original` antes de evaluar; las pasadas de falsas se filtran con `es_aparte` (línea 1066); `latest.json` gana `plataformas` (ceses, juzga_desde, error, aparte); el historial gana `plataformas_juzga_desde`; una línea de consola por sensor recortado; si la lista no se lee, aviso de cobertura y DEGRADADO.

### Consumidores de la tasa (regla A118), leídos en `main()` del PR

| consumidor | ¿recortado? | vara |
|---|---|---|
| `evaluar_detector` (recall y magnitud por detector) vía `mir` | sí | `scripts/auto_audit_weekly.py:951,960` |
| `recall_regla_original` vía `mir_original` | sí | `:952,963-965` |
| estratos por cenit y régimen (`agregar_estratos(out, mir, ...)`) | sí (usa `mir` ya partido) | `:1100` |
| falsas publicaciones (historial que lee la sombra) | sí | `:1066-1067` |
| alertas protegidas | no, a propósito (pasadas, no tasas) | `:1004-1006` sin cambio |
| cobertura por días | no, a propósito | `:1005` sin cambio |
| `inst_mir`, `ours`, `vistos` | no hace falta: sólo se consultan con claves de `mir` | `:960,1100` |

Fuera del audit, los únicos scripts de workflow que calculan tasas contra MIROVA son `auto_audit_weekly.py` y `vigilancia_sombra.py` (`git grep -oE "scripts/[a-z_0-9]+\.py" origin/main -- .github/workflows/...`). La sombra no se toca en este PR (ver PR162-06).

### Pruebas

- **Suite relacionada en el worktree**: `python -m pytest tests/test_auto_audit_*.py tests/test_vigilancia_sombra_s156.py -q -p no:cacheprovider --basetemp=<CARPETA>\pt1` dio **135 passed**. `tests/test_cese_plataforma_nrt_s161.py tests/test_cese_plataformas_s159.py tests/test_vigilar_plataformas_s159.py tests/test_auto_audit_cese_plataforma_s161.py` dio **57 passed**. Árbol quieto durante las dos corridas (A112: no edité nada del worktree).
- **Rojas sin el cambio**: `git show 3bbd18d2c:scripts/auto_audit_weekly.py` a `rojas\old\auto_audit_weekly_base.py` y la prueba nueva copiada a `rojas\test_base_s161.py` cargando ese módulo. Resultado: **6 failed, 3 passed**. Las 6 que deben fallar fallan **por aserción** (`assert (55, 94.5) == (20, 85.0)`, `assert (52, 1.0) == (17, 0.5)`, `n_neg_limpio 20 != 10`, `None == '2026-11-03'`, etc.), no por import; las 3 de control pasan con el código base, como dice su docstring. Pregunta 1: si el recorte no existiera, estas pruebas lo ven (control positivo: el código base). Pregunta 2: el insumo es sintético y no depende del reloj real (reloj fijo derivado de `ceses_esperados.json`).
- **Sobre datos reales** (`tools\correr_audit.py` + `tools\comparar.py`, salidas en `corridas\`): `main()` de origin/main y del PR sobre `root\` (origin/main `e850152b5`), reloj fijo y salida a CARPETA.
  - 2026-10-26 y 2026-11-02: claves distintas (sin `plataformas`) = `[]`, historial igual, consola sin diferencias, `juzga_desde` todo None. **El informe del lunes 26-oct no cambia.**
  - 2026-11-09 y 2026-11-23 (control positivo: datos sólo hasta el 24-oct, así que VIIRS queda sin noches juzgadas): VIIRS 375 y 750 pasan a n = 0; MODIS idéntico en recall, magnitud, falsas, estratos por cenit y por régimen; protegidas y cobertura idénticas.

### Fechas y zona horaria

- El corte es UTC en todos los lados: `desde_utc` termina en `Z` (`scripts/ceses_esperados.json`), las noches de MIROVA son `fecha_utc[:10]` (`auto_audit_weekly.py:547`), las nuestras `datetime_utc[:10]` y las del banco `dt.strftime("%Y-%m-%d")` (`scripts/banco_paridad.py:282`). Las pasadas nocturnas sobre Chile caen en un solo día UTC, así que partir por día UTC no corta una noche.
- `pipeline/fetch.py:803-812` (origin/main): `datetime(día) >= instante del cese`. Con cese 13:00 da 2026-11-03; con cese a medianoche da el mismo día. `leer_ceses` da lo mismo en los dos casos (medido en `bordes\`: `medianoche` → `primer_dia_sin 2026-11-02`, real → `2026-11-03`).
- El workflow corre los lunes 09:00 UTC (`.github/workflows/audit-weekly.yml:10`). `juzga_desde` con hoy 2026-11-02 da todo None; con 2026-11-03 da VIIRS desde 2026-11-03 (medido). El primer informe recortado es el del 2026-11-09, con 7 días de VIIRS.

### Hallazgos, de peor a menor

**PR162-01. Tras el cese VIIRS queda semanas sin juzgar y el audit no lo dice; los flags vigentes de #864 salen del veredicto**
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:951,960` (PR) junto con `MIN_N_RECALL = 15` y `MIN_N_RATIO = 5` (`:94-95`) y `flags_de_evaluacion` (`:792-810`); cuerpo del issue en `.github/workflows/audit-weekly.yml` (sólo lista `flags` y `cobertura.avisos`).
- QUÉ PASA: con una plataforma menos, MIROVA y nosotros tenemos menos noches con alerta por semana, y la ventana juzgada parte de cero el 3-nov. Mientras `n` esté bajo el mínimo, los flags de recall y magnitud de VIIRS no pueden dispararse y el veredicto puede salir VERDE por falta de muestra, que es justo el modo que el propio bloque S124 del script llama «asimetría perversa» (líneas 97 a 108). La consola dice «se juzga desde», pero ni `cobertura.avisos` ni el issue dicen que VIIRS no se pudo juzgar. El PR lo reconoce en su descripción; el audit no lo reconoce en su salida.
- Tamaño: en la ventana 2026-09-24 a 2026-10-24 (31 días con datos, corrida `main_2026-11-23`) hubo 83 noches con alerta en VIIRS 375 (D-9 SN) y 24 en VIIRS 750, o sea 2,7 y 0,77 por día **con tres plataformas**. Para llegar a 15 hacen falta unos 6 días en VIIRS 375 y unos 20 en VIIRS 750, más con dos plataformas. Por volcán, Chillán VIIRS 375 tuvo 17 noches en esos 31 días: unos 9 días o más para llegar a 5. El PR estima 5 y 16 días; mis números dan algo más, con el denominador declarado.
- CÓMO SE VE EN EL DASHBOARD: invisible para el operador (el audit no sale al tablero). En el issue semanal del 9-nov, con los datos de hoy, desaparecerían «recall VIIRS750 < banda» y las magnitudes de Chillán VIIRS 375 y 750 y Tupungatito VIIRS 375 que hoy están en #864 (simulación: 11 flags en main, 6 en el PR; `corridas\main_2026-11-09\latest.json` contra `corridas\pr_2026-11-09\latest.json`). Los números siguen en `plataformas.aparte`, que nadie imprime.
- CÓMO REPRODUCIRLO: `python tools\correr_audit.py <CARPETA>\root tools\aaw_pr.py 2026-11-09 corridas\pr_2026-11-09` y lo mismo con `aaw_main.py`; `python tools\comparar.py <CARPETA>`.
- CONFIANZA: CONFIRMADO el mecanismo (leído y simulado); el tamaño exacto con dos plataformas es estimación.
- GRAVEDAD: 2. No tuerce una alerta del operador (las protegidas siguen juzgándose desde el primer día), pero deja la vigilancia de la réplica en VIIRS ciega y callada hasta tres semanas.
- Arreglo sugerido (para quien orquesta): por cada sensor con `juzga_desde` y `n_noches < MIN_N_RECALL`, una línea informativa en consola y en el cuerpo del issue («VIIRS 750 sin juzgar: n = 4 desde el cese del 2026-11-03; lo de antes en plataformas.aparte»), sin degradar, o bien imprimir los flags que daría `plataformas.aparte` marcados como «antes del cese, no deciden».

**PR162-02. Los silencios de plataforma no anunciados mezclan la ventana igual que el cese, y el PR sólo cubre el corte anunciado**
- SCRIPT:SALIDA: `tools\dias_sin_granulos.py` (`parteB_salida.txt`): Suomi NPP sin ningún record en los 11 volcanes a la vez en **20 días** de calendario entre 2026-03-01 y 2026-10-23 (2026-03-10 a 12, 04-28 a 30, 06-01 a 02, 07-11 a 16, 08-03 a 06, 10-13, 10-20), con NOAA-20 presente; NOAA-21 1 día (10-13); Terra 5; Aqua 1.
- QUÉ PASA: en esos días el recall por noche de VIIRS se jugó con dos plataformas, el mismo cambio de muestreo que motiva el PR, pero sin recorte. Hoy son 8,5 % de los días de la ventana; tras el cese, un silencio de NOAA-20 o NOAA-21 deja una sola.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO que los silencios existen en el archivo; SOSPECHA que muevan el recall de forma medible (no lo medí).
- GRAVEDAD: 2. Es materia de la decisión 3, no un defecto del PR.

**PR162-03. Después del cese, el OCR de MIROVA podría seguir registrando alertas desde imágenes viejas de Suomi NPP**
- Antecedentes en `CLAUDE.md` A106 (MIROVA vuelve a servir imágenes viejas bajo una hora nueva) y memoria S150 (OCR con la imagen de otra pasada).
- QUÉ PASA: si una alerta «sólo OCR» con fecha posterior al 2-nov viene de una imagen vieja de Suomi NPP, entra al denominador del recall de VIIRS como noche con alerta que nadie pudo ver, y la ventana recién partida (n chico) la amplifica.
- CONFIANZA: SOSPECHA, sin datos todavía. Verificable desde el 3-nov mirando las filas OCR de VIIRS posteriores al cese contra las pasadas de NOAA-20 y NOAA-21.
- GRAVEDAD: 2.

**PR162-04. `leer_ceses` puede tumbar el audit o no recortar en silencio con una lista mal formada**
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:457-475` (PR). Captura `OSError, ValueError, KeyError, TypeError`, no `AttributeError`.
- SCRIPT:SALIDA (`bordes\`): sensor `null` → **AttributeError no capturado** (el audit muere antes de escribir `latest.json`, y el paso de issue no corre); `"sensores": "VIIRS_SNPP"` (cadena en vez de lista) o un sensor desconocido → `sensores: []`, **sin recorte y sin aviso**; fecha con `+00:00` → error capturado y DEGRADADO (bien).
- CÓMO SE VE EN EL DASHBOARD: invisible; en el peor caso, un lunes sin informe.
- CONFIANZA: CONFIRMADO (medido). Probabilidad baja: el archivo lo vigilan otras pruebas.
- GRAVEDAD: 1.

**PR162-05. Lo de antes del cese queda a medias**
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:1089-1091,1066-1067,1100` (PR).
- QUÉ PASA: `plataformas.aparte` trae recall y magnitud del detector vigente, pero las falsas publicaciones de VIIRS anteriores al cese se descartan sin informarse, y los estratos por cenit y régimen de VIIRS pierden las noches previas. `aparte` no se imprime en consola. En la simulación del 9-nov, falsas VIIRS 375 pasa de 3,9 % sobre 785 negativos a `None` sobre 0.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (información, no veredicto).

**PR162-06. La vigilancia de la sombra cruza el cese sin partirlo**
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py:452` (`win = (frontera, hoy)`), disparadores en `:256-345`.
- QUÉ PASA: sus tasas (Muy Bajo y negativos) son por pasada, que el número de plataformas no sesga por construcción; pero la persistencia («tres noches seguidas») es por noche y con dos plataformas se vuelve menos sensible, y las cotas del A/B se midieron con tres. Dirección conservadora (dispara menos).
- CONFIANZA: SOSPECHA (leído, no medido). GRAVEDAD: 1. Fuera del alcance del PR; lo dejo por A118.

**PR162-07. Si NASA mueve la fecha y nadie actualiza la lista, el NRT (#897) deja de buscar Suomi NPP mientras MIROVA la sigue usando**
- Lo dice la nota de `scripts/ceses_esperados.json` («sujeto a cambio»). En ese caso el audit lo delataría por las protegidas sin record (`avisos_protegidas_sin_record`, DEGRADADO), pero las noches salvadas sólo por Suomi NPP contarían como fallos de recall.
- CONFIANZA: SOSPECHA. GRAVEDAD: 1. Riesgo de #897, no de #900.

### Recomendación

**Mergear con un cambio chico**: agregar el aviso informativo de PR162-01 (sensor sin juzgar por n bajo el mínimo desde el cese, con un puntero a `plataformas.aparte`) en la consola y en el cuerpo del issue. Opcional en el mismo PR: capturar `AttributeError` y avisar cuando un cese no mapea a ningún sensor (PR162-04). Si se prefiere no tocarlo, mergear tal cual y abrir la tarea del aviso como pendiente con fecha: tiene que estar antes del lunes **2026-11-09 09:00 UTC**, el primer informe recortado. Para el informe del 2026-10-26 y del 2026-11-02 da lo mismo mergear o no (verificado). El PR no necesita rebase: desde su base sólo entraron commits de datos.

---

## Parte B: días sin gránulos, para la decisión 3

### Qué cuenta como «día sin gránulos» y qué significa (pregunta 2)

- **Definición**: un volcán-día UTC de una plataforma está «sin pasadas» si en `data/mirova_equivalent/<Volcán>.json` de origin/main no hay ningún record de esa plataforma con elevación solar ≤ 0 (la regla de `store._reject_daytime`; con `ENABLE_DAYTIME_MODIS` y VIIRS diurno apagados, leídos de `pipeline.profile` y `pipeline.diurno`). Para un sensor, sin pasadas de ninguna de sus plataformas. Ventana 2026-03-01 a 2026-10-23 (el 24-oct se excluye por estar incompleto), 11 Tier A, 2.607 volcán-días.
- **¿Se escriben records sin detección?** Sí. `pipeline/store.py:332-333` sólo descarta `record is None`; `:636-648` (bloque que llama a `_reject_daytime`) descarta diurnos; el resto se escribe. `scripts/run_pipeline.py:252-265` llama a `append_record` con todo `result` no vacío, y los procesadores devuelven `None` sólo si el ROI no cae en el gránulo o si hay menos de 10 píxeles de fondo (`pipeline/process_modis.py:584-585,630-631`). Medido: **23.363 de 27.523** records nocturnos (84,9 %) no traen cúmulo con magnitud (`pc.vrp_mw ≤ 0`); en MODIS 5.504 de 5.661 (97,2 %). Por lo tanto **un día sin record es «sin gránulo nocturno procesable»** (no encontrado, no bajado, sin geolocalización pareada, ROI fuera del gránulo, fondo insuficiente o error de proceso), **no «gránulo sin nada»**.
- **Pregunta 1 (¿lo vería si estuviera roto?)**: sí a nivel plataforma. Control positivo: Suomi NPP aparece muda en los 11 volcanes en 20 días; NOAA-21 en el 2026-10-13. **Pero** el archivo es el estado final tras backfills y reprocesos: la fila TODOS da 0 % en todos los meses aunque hubo apagones del NRT, así que esta tabla **no ve silencios en vivo que después se rellenaron**. Para eso está la segunda medición.

### Tabla 1: volcán-días sin ninguna pasada nocturna (k de n), archivo de origin/main

| | 2026-03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 (1-23) | total |
|---|---|---|---|---|---|---|---|---|---|
| **MODIS** | 0/341 | 2/330 | 3/341 | 0/330 | 0/341 | 0/341 | 1/330 | 1/253 | **7/2.607 (0,27 %)** |
| Terra | 20 | 12 | 12 | 17 | 0 | 3 | 24 | 29 (11,5 %) | 117 (4,5 %) |
| Aqua | 5 | 12 | 17 | 6 | 16 | 6 | 5 | 5 | 72 (2,8 %) |
| VIIRS 375 y 750 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Suomi NPP (375 = 750) | 33 | 33 | 0 | 22 | 66 | 44 | 0 | 22 | 220 (8,4 %) |
| NOAA-20 (375 = 750) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NOAA-21 (375 = 750) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 11 (0,4 %) |
| todas las plataformas | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Los 7 volcán-días sin MODIS: Láscar 2026-05-04, 05-24, 10-04; Isluga 2026-04-24, 04-29, 05-24, 09-29. En los 7 VIIRS sí tiene records; nunca dos seguidos; ningún día sin MODIS en los 11 a la vez. Que sean los dos volcanes más al norte apunta a los huecos entre barridos de MODIS a baja latitud (SOSPECHA, no lo verifiqué). Plataformas mudas en los 11 volcanes con otras presentes: Terra 2026-03-27, 06-02, 09-28, 10-02, 10-10; Aqua 2026-07-21; nunca las dos el mismo día. Pasadas nocturnas medias por volcán-día con dato: 1,1 por plataforma MODIS, 1,4 a 1,5 por plataforma VIIRS, estables mes a mes.

### Tabla 2: silencio en vivo, con `first_processed_utc` (2026-10-10 a 2026-10-23)

`tools\silencio_en_vivo.py`. Latencia de la primera aparición de cada volcán-día con dato (el campo existe en 0 records de marzo a julio y en 478 de 719 de octubre en una muestra de 3 volcanes, por eso la ventana empieza el 10-oct; dentro de ella todos los records lo traen).

| | volcán-días | mediana | p90 | > 12 h | > 24 h |
|---|---|---|---|---|---|
| **MODIS (cualquier plataforma)** | 154 | 2,0 h | 6,9 h | 1 | **0** |
| Terra | 140 | 2,2 h | 6,9 h | 0 | 0 |
| Aqua | 151 | 3,2 h | 11,8 h | 15 | 0 |
| VIIRS 375 (cualquiera) | 154 | 2,4 h | 6,5 h | 12 | 12 |
| NOAA-20 | 154 | 2,6 h | 9,8 h | 12 | 12 |

Control positivo: la masa de latencias está en 2 a 4 h, como la latencia LANCE conocida. Los 12 volcán-días tardíos de VIIRS son el **2026-10-13** (Suomi NPP y NOAA-21 nunca llegaron en ninguno de los 11 volcanes; NOAA-20 apareció recién el 2026-10-19, producto estándar) y uno de Láscar el 2026-10-20: ese día VIIRS estuvo ciego en vivo en los 11 volcanes y el archivo de hoy no lo muestra (tabla 1, fila TODOS en 0).

### Qué tamaño tiene el problema que el modo estricto querría vigilar

- **MODIS como sensor**: casi inexistente hoy. 7 volcán-días en casi ocho meses, aislados, sólo en el norte; en vivo, ninguno pasó de 24 h en dos semanas. Un modo estricto por sensor MODIS no habría disparado nunca por silencio total de MODIS.
- **Por plataforma**: es donde vive el problema. En el archivo, una plataforma completa muda en los 11 volcanes con las demás presentes ocurrió en 27 días de calendario (Suomi NPP 20, Terra 5, Aqua 1, NOAA-21 1), y en vivo hay silencios que el archivo esconde (2026-10-13). Hoy esos silencios son invisibles para la guarda de cobertura por días, porque las otras plataformas siguen dando datos (lo mismo que dice el bloque S160 de `avisos_protegidas_sin_record`).
- **Después del 3-nov**: Suomi NPP muda todos los días es esperado y tiene que salir de la lista de ceses; VIIRS queda con dos plataformas, y un silencio de una deja una sola. Terra viene subiendo (7,3 % en septiembre, 11,5 % en octubre; causa SIN DATO).
- **Para diseñarlo**: medir con `first_processed_utc` o con `fetch.cobertura_por_plataforma()` (`pipeline/fetch.py:780`), por plataforma y no por sensor; el archivo sirve para el tamaño histórico, no para el disparo.

---

## VERIFICADO LIMPIO

- **Antes del corte el audit da exactamente lo mismo**: `python tools\comparar.py <CARPETA>` sobre corridas de main y PR con reloj 2026-10-26 y 2026-11-02: 0 claves distintas fuera de `plataformas`, historial igual salvo la clave nueva, 0 líneas de consola distintas.
- **MODIS intacto después del corte**: mismas corridas con 2026-11-09 y 2026-11-23: recall, magnitud publicada, falsas, estratos por cenit y por régimen de MODIS, protegidas y cobertura iguales (`True` en los 7 chequeos).
- **Las pruebas nuevas fallan sin el cambio y por aserción**: `rojas\test_base_s161.py` contra `git show 3bbd18d2c:scripts/auto_audit_weekly.py`: 6 failed (aserción), 3 passed (controles).
- **Suite relacionada verde**: 135 + 57 passed (comandos arriba), árbol quieto.
- **Misma regla de día que el NRT** (A102): `pipeline/fetch.py:803-812` contra `leer_ceses`, más los casos de borde de `bordes\` (cese 13:00 y cese a medianoche).
- **El corte no parte una noche**: noches de MIROVA, nuestras y del banco, todas por día UTC (`auto_audit_weekly.py:547`, `banco_paridad.py:282`).
- **El lunes del cese no recorta**: `juzga_desde(..., 2026-11-02)` todo None; `2026-11-03` VIIRS desde 2026-11-03.
- **Conteo del PR**: 501 de 1.516 records VIIRS 375 y 497 de 1.504 VIIRS 750 de Suomi NPP entre 2026-09-18 y 2026-10-20 en origin/main de hoy (el PR dice 1.514 y 1.501: el corpus creció, A90).
- **Los records se escriben sin detección**: `store.py:332-333` y `run_pipeline.py:252-265` leídos; 84,9 % de los records nocturnos sin cúmulo con magnitud.
- **No hay records diurnos ni sensores fuera de convención** en los 11 Tier A desde marzo: 0 y `{}` en `parteB_salida.txt`.

## SIN DATO

- La causa de los silencios de Suomi NPP, Terra, Aqua y NOAA-21 (maniobra, LANCE, LAADS, nuestro fetch): el archivo no lo dice.
- Silencios en vivo antes del 2026-10-10: `first_processed_utc` no existe antes (sello de S150).
- El recall real con dos plataformas: no hay datos posteriores al cese.
- Si los 7 volcán-días sin MODIS de Láscar e Isluga son huecos de barrido o `return None` del procesador (ROI fuera del gránulo o fondo insuficiente): el archivo no distingue.
- Qué saltó en el CI del PR (33 skipped en toda la suite, sin `-rs`): localmente la prueba que importa `pipeline.fetch` corrió y pasó.
