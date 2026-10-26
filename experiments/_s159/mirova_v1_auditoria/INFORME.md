# Auditoría de Mirova-v1 (scraper de mirovaweb.it): cuánto vale como referencia y por qué se mueve

- **Hora del servidor al cerrar:** 2026-10-22 (UTC), sesión iniciada 2026-10-21. Commit medido:
  `MendozaVolcanic/Mirova-v1` `c48d24cad8` (2026-10-22 02:51 UTC), clon parcial `D:\vrp-trabajo\mirova-v1`
  (sin `graficos_tendencia`, `imagenes_satelitales`, `v_html`, `v_html_log`). `git status` del clon: limpio al cerrar.
- **Quién:** orquestador Opus 5.5 (frente 1, tabla); auditores Opus 5.5 esfuerzo high (frentes 2 y 3, OCR y etiquetas;
  frente 4, operación); verificadores con contexto limpio Fable 5.1 esfuerzo high (uno para la tabla, uno para el OCR).
  Los hallazgos de gravedad 4 de operación los verifiqué a mano (la guía lo permite a quien orquesta).
- **Guía aplicada:** `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` (commit `31b70f1`) y
  `C:\Users\nmend\OneDrive\Escritorio\claude\PLANTILLA_CAZA_DE_BRECHAS.md`, Parte D (bugs latentes). Preámbulo pegado
  entero en los cinco agentes: `D:\vrp-trabajo\mirova-v1-auditoria\PREAMBULO_AUDITOR_MIROVA.md`. Skills:
  `verification-before-completion` antes de cerrar; depuración sistemática (hipótesis, evidencia, causa) en la
  reproducción del frente 1, que pasó por seis hipótesis fallidas antes de reproducir (ver H-T1).
- **Sólo lectura.** Nada se escribió en el clon, en GitHub ni en el repo de VRP Chile. Sin API de GitHub. Una sola
  petición GET a `latest.php` (auditor de operación).
- **Qué NO miré:** las imágenes de MIROVA (fuera del clon a propósito), el tablero publicado, los registros de las
  corridas de Actions (sin API), el código de VRP Chile salvo `sync-mirova-csv.yml`, `clase_mirova.py` y
  `referencia_mirova_unificada.py`.

## En una pantalla

1. **La tabla pierde filas por culpa de Mirova-v1, no de MIROVA.** Las 1.948 filas perdidas en 60 días (y 2.165 en
   toda la historia, 18 alertas protegidas, 14 de Láscar) salen de 8 commits del propio scraper: el bucle de push
   (`git pull --rebase -X ours`) mezcla como TEXTO un CSV que el scraper reescribe entero y en otro orden en cada
   ciclo. Reproducido byte a byte con git real; con orden determinista la misma mezcla da 0 pérdidas. Sigue activo.
2. **El contenido de las filas de la tabla es confiable** (0 reescrituras en su historia, tipo calculado de VRP y
   distancia), pero la tabla es incompleta por diseño: `latest.php` muestra sólo la última pasada de cada volcán y
   sensor (una VIIRS queda visible 1,4 h de mediana), así que un hueco del scraper pierde pasadas para siempre.
3. **El OCR sirve como VRP y como hora; como clase (dentro o fuera del radio) sólo con el método de la estrella, de
   noche y desde V29.2.** El método de grupo de píxeles rojos, todavía activo, acierta 0,795 de noche y 0,104 de día.
   De las 184 alertas protegidas que sólo existen en el OCR, entre 40 y 90 serían falsas (centro ~55, extrapolado).
4. **Las 39 reescrituras que VRP Chile atribuyó al OCR son correcciones manuales** de Nicolás (15-jun y 4-ago), y la
   copia corrupta del 19-ago (822 duplicados) la fabricó **el sync de VRP Chile** con el mismo mecanismo del punto 1.
5. **Nadie se entera cuando algo falla:** el scraper y el OCR salen con código 0 en todo modo de falla de MIROVA (141
   ciclos reales con 0 filas terminaron «Proceso completado»), y los vigilantes miden actividad, no dato.

## 0. Inventario de cobertura (auditorías previas de este objeto)

| auditoría | qué miró | qué dejó abierto | qué hace esta |
|---|---|---|---|
| `tasks/AUDITORIA_OCR_EMPIRICA_2026-06.md`, `tasks/AUDITORIA_TECNICA_2026-06.md` (repo) | geometría del OCR, calibración, arquitectura | método de grupo no cuantificado | lo mide contra la tabla (H-O1) |
| VRP Chile S139, `MAPA_BASES_MIROVA_V1.md` | qué es cada archivo; pérdidas de abr y ago; mojibake; H202 coma de miles | mecanismo de la pérdida (SOSPECHA de carrera) | mecanismo demostrado (H-T1); H202 cerrado en el código (VERIFICADO LIMPIO); mojibake sigue abierto (H-O8) |
| VRP Chile S159, `referencia_estable\INFORME.md` y su verificador | estabilidad de las copias de VRP Chile | atribución de la pérdida; autor de las 39 reescrituras; 81dd25ce3 | atribución en commit exacto; 39 manuales (coincide con su verificador); 81dd25ce3 es de VRP Chile (H-V1) |
| ninguna | robustez operacional, vigilancia, `latest.php` como «última pasada» | | frente 4 (H-P1 a H-P6) |

Eje nuevo de esta auditoría: la **historia de git del scraper** como instrumento (firmas de commit leídas sólo de
árboles, sin bajar blobs), y la **cadena de copias** Mirova-v1 a VRP Chile como fuente de daño propia.

## 1. Hallazgos (lo peor primero)

IDs finales con su ID provisional entre paréntesis. Detalle y comandos en los informes de cada frente:
`D:\vrp-trabajo\mirova-v1-auditoria\frente2_ocr\INFORME.md`, `D:\vrp-trabajo\mirova-v1-auditoria\frente4_operacion\INFORME.md`,
`D:\vrp-trabajo\mirova-v1-auditoria\verificador_frente1\INFORME.md`, `D:\vrp-trabajo\mirova-v1-auditoria\verificador_ocr\INFORME.md`.
Lista filtrable: `D:\vrp-trabajo\mirova-v1-auditoria\hallazgos.csv`.

### H-T1 (101, 901, 903). La tabla pierde filas en la mezcla de texto del bucle de push de Mirova-v1
- **ARCHIVO:LÍNEA** `scraper.py:240` (orden sólo por `timestamp`, sin desempate, archivo entero reescrito cada ciclo);
  `.github/workflows/main.yml:67-71` (`git pull origin main --rebase --autostash -X ours || true` en el bucle de push).
- **SCRIPT:SALIDA** orquestador: `01_bisect_perdidas.py`/`salida_01.txt`, `01b_bisect_resto.py`/`salida_01b.txt`,
  `02_anatomia_commit.py`/`salida_02.txt`, `04_firma_commits_mezcla.py`/`salida_04.txt`, `05_retraso_rebase.py`/`salida_05.txt`,
  `06_geometria_dups.py`/`salida_06.txt`, `07_reproduccion_vrp_sync.py`/`salida_07.txt`, `08_censo_historia.py`/`salida_08.txt`,
  todos en `D:\vrp-trabajo\mirova-v1-auditoria\`. Verificador: `verificador_frente1\v01` a `v08`.
- **QUÉ PASA.** El fenómeno: en una sola versión desaparecen cientos de filas viejas, repartidas de enero a hoy, y
  nunca vuelven. El mecanismo: el scraper reescribe el CSV entero ordenado sólo por `timestamp`; 98 % de las filas
  comparte timestamp con otras, así que cada ciclo permuta el orden de casi todo el archivo (80 a 82 % de las filas
  cambia de vecina en un ciclo normal, `v07`). Cuando una corrida parte de una base más vieja que `main` y al empujar
  rebasa sobre OTRO ciclo del scraper, git mezcla tres permutaciones del mismo archivo y, en hunks que considera
  limpios (0 marcadores de conflicto, `v06`), deja filas dos veces o ninguna. El ciclo siguiente borra los
  duplicados; nadie repone las pérdidas de pasadas que `latest.php` ya no muestra.
- **Evidencia.**
  - Las 1.948 pérdidas de 60 días salen 100 % de 8 commits de VolcanoBot: `fb2a3123f8`, `f843a1ead6`, `8e04975286`,
    `dc5e5c0121`, `81c06c52ab`, `f1eaeaf74f`, `c292d6b267` y `ecdc09e4d6` (cascada sobre `c292d6b267`, base
    `b2782fe682`). Ventana de control del 20-oct: 0.
  - `scraper.py:232-243` no puede escribir eso: `concat` conserva toda llave vieja y `drop_duplicates` por llave
    impide duplicados; los commits de pérdida traen 1.141 a 3.146 llaves duplicadas con copias idénticas.
  - Firmas leídas de la historia: 7 de los 8 no tocan `bitacora_robot.txt`, que todo ciclo del scraper modifica
    (control: 6 de 6 pérdidas marcadas, 0 de 6 ciclos normales); 6 de 7 tienen 2 a 8 s entre fecha de autor y de
    commit, contra 0 a 1 s en 17.382 de 17.398 ciclos normales (`8e04975286` tiene 1 s: la firma de retraso no es
    universal). Duplicados a 2 a 23 líneas de su copia; pérdidas sólo en grupos de filas con el mismo timestamp.
  - **Reproducción con git real** (línea base roja): tres ternas de versiones SANAS consecutivas de Mirova-v1
    rebasadas con `-X ours` como `main.yml:68` dan 831 a 1.784 duplicados y 74 a 250 pérdidas; las mismas ternas en
    orden determinista (timestamp, Volcan, Sensor): 0 y 0 (`verificador_frente1\v08_salida.txt`). Los bytes exactos
    de los 8 commits no se pueden reproducir: el commit local de cada corrida lo reescribió el rebase.
  - Sólo daña el rebase sobre otro ciclo del scraper: 16 rebases sobre commits del OCR salieron sanos (902).
- **Tamaño.** Toda la historia: 2.165 llaves ausentes hoy, **18 alertas protegidas distintas** (14 de ago a oct, 4 del
  23-abr; 14 Láscar, 3 Puyehue-Cordón Caulle, 1 Villarrica) (`v02`). Mi archivo `filas_recuperadas.csv` trae 2.230
  porque suma filas de enero con esquema de desarrollo (42 `EVIDENCIA_DIARIA`, 15 sin tipo); quedan 8 de diferencia
  sin explicar (SOSPECHA: llave distinta entre los dos censos).
- **CÓMO SE VE EN LA REFERENCIA.** Alertas de MIROVA que estaban y ya no están, sin marca. En el tablero de VRP Chile,
  la noche en que MIROVA sí alertó aparece sin punto MIROVA (Láscar MODIS 2026-02-09 07:20, 1,64 MW, comprobado por
  el verificador de S159). En el de Mirova-v1, desaparecen de los gráficos y de los CSV descargables.
- **Disparador.** Que la corrida parta de una base vieja está demostrado sin API: `ecdc09e4d6` corrió el scraper 3,5
  min después de que `c292d6b267` estaba en `main` y aun así partió de `b2782fe682`. Por qué pasa (checkout del sha del
  despacho, carrera de `cancel-in-progress`) es SIN DATO; lo cierra
  `gh run list -R MendozaVolcanic/Mirova-v1 --workflow main.yml --created "2026-10-18T17:15:00Z..2026-10-18T17:40:00Z" --json databaseId,headSha,createdAt,runStartedAt,conclusion,event`.
- **CONFIANZA** CONFIRMADO (verificador: A1, A3, A4 CONFIRMADO; A2 CONFIRMADO EN PARTE por la redacción de dos
  commits, ya corregida aquí). **GRAVEDAD 5**: tuerce alertas protegidas en silencio y sigue activo.

### H-O1 (201). El método de «grupo de píxeles rojos» del OCR pone focos lejanos dentro del radio y sigue activo
- **ARCHIVO:LÍNEA** `ocr_utils.py:293` (ordena grupos por Y), `ocr_utils.py:307-312` (los asigna a las pasadas por
  índice), `ocr_utils.py:1266-1311` (FASE 1); camino vivo `ocr_workflow.yml:81` → `scraper_ocr.py:530/558`.
- **QUÉ PASA.** En el panel de Dist.png la Y es distancia, no tiempo; el código asigna el grupo más cercano al cráter
  a la pasada más reciente que no esté en la tabla, sin relación física entre punto y hora. Contra la tabla, donde la
  tabla tiene la misma pasada: su ALERTA acierta 62/78 = 0,795 de noche y 5/48 = 0,104 de día (0,588 y 0,073 en
  protegidas); las 59 falsas están en la tabla a 22 km de mediana con el OCR diciendo 1,44 km. V31 no lo corrige:
  9 filas V31.0 desde el 9-oct, 2 FALSO_POSITIVO en la tabla (Tupungatito 16-oct a 17,78 km; Láscar 10-oct a 24,73 km).
- **CÓMO SE VE EN LA REFERENCIA.** Alertas OCR «dentro del radio» que MIROVA tiene a 10 a 30 km. Donde la tabla lista
  la pasada, `reconciliar_latest.py` la corrige en ~0,5 h; donde no la lista (alertas sólo OCR), queda para siempre.
- **CONFIANZA** CONFIRMADO (código y cifras reproducidas exactas por el verificador con otra vara); qué representan
  los píxeles rojos: SOSPECHA (sin imágenes). **GRAVEDAD 5.**

### H-P1 (401, 402, 404, 407). El scraper y el OCR fallan en silencio, y los vigilantes miden actividad
- **ARCHIVO:LÍNEA** `scraper.py:130-248` (un solo `try`; el `except` sólo escribe la bitácora y sale 0);
  `scraper_ocr.py:762-771` (traga la excepción de cada volcán y sigue); `visualizador.py:819-828` (estado
  «Operativo» fijo); `scripts/heartbeat_site.py:29-33` (hora del runner); `graficos_completo.yml:4-6`.
- **QUÉ PASA.** En los 11 modos de falla simulados con el código de HEAD (caída, timeout, 200 vacío, 500, sin
  `tbody`, tabla vacía, columnas cambiadas, fecha ISO, coma decimal, sensor renombrado) el scraper sale 0 y hay commit
  (la bitácora cambia), así que el repo siempre parece vivo. En producción: **141 ciclos con «Filas leídas desde
  latest.php: 0» terminaron «Proceso completado correctamente.»** (enero a octubre; lo conté con `grep` en esta
  sesión). La señal que delataría un zombie en minutos, `Ultima_Actualizacion_UTC`, no la usa nadie (414).
- **CONFIANZA** CONFIRMADO (orquestador, a mano: código leído y conteo de bitácora). **GRAVEDAD 4.**

### H-P2 (406). `latest.php` es «la última pasada de cada volcán y sensor», no un historial
- **QUÉ PASA.** 528 filas = una por par volcán y sensor (comprobé 527 pares distintos en la copia del auditor). Una
  pasada sale de la tabla cuando llega la siguiente del mismo par: visible 1,42 h de mediana en VIIRS, 7 % 15 min o
  menos, 40 % una hora o menos; MODIS 5,4 h. Un hueco de 65 min pierde ~1 pasada; el de 237 min del 2026-08-06, ~10,6
  (0,57 alertas). Subestimado por supervivencia: el OCR tiene gránulos sin ninguna fila en la tabla y sin hueco del
  scraper a esa hora.
- **CÓMO SE VE EN LA REFERENCIA.** Pasadas que MIROVA publicó y la tabla nunca tuvo; la ausencia no deja marca y no se
  puede reconstruir desde Mirova-v1.
- **CONFIANZA** CONFIRMADO la estructura y las ventanas; la pérdida por hueco es estimación. **GRAVEDAD 3.**

### H-V1 (102). La copia corrupta 81dd25ce3 la fabricó el sync de VRP Chile con el mismo mecanismo
- **SCRIPT:SALIDA** `07_reproduccion_vrp_sync.py`/`salida_07.txt`; `verificador_frente1\v03`, `v08`.
- **QUÉ PASA.** Mirova-v1 tuvo 33.420 filas y 0 duplicados en sus 30 versiones del 19-ago de 15:31 a 17:56. VRP Chile
  pasó de `10fa8a934` (33.420, 0) a `81dd25ce3` (34.079, 822 duplicados, 163 llaves menos) dos minutos después. Un
  `git pull --rebase -X theirs` (como `sync-mirova-csv.yml:191` de VRP Chile) de base `dd61de872`, ours `10fa8a934` y
  theirs la versión `f9a99409f9` de Mirova-v1 da un archivo **idéntico byte a byte** a `81dd25ce3` (sha1
  `e96b118b0638`), por dos caminos de git real. Con `-X ours` las mismas entradas dan 787 duplicados y 122 pérdidas;
  en orden determinista, 0 y 0. El bucle sigue igual en VRP Chile.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 3** (2 h de daño medido; el mecanismo sigue disponible en VRP Chile).

### H-O2 (202). Antes de V31 la «estrella» de una pasada se copiaba a otras celdas de la misma corrida
- `ocr_utils.py:1130-1204` (`validar_con_estrella_verde` no recibe la pasada), `scraper_ocr.py:475-486`. 29 de 29
  corridas con 2 o más pasadas comparten la misma Y. Arreglado por V31 (`scraper_ocr.py:593-613`, fail-closed). Con
  certeza 23 copias protegidas sólo OCR, 20 diurnas. CONFIRMADO EN PARTE (el nulo de 0,497 es débil). **GRAVEDAD 3**
  (arreglado hacia adelante, no hacia atrás).

### H-O3 (208). Alertas OCR diurnas sin filtro bajo 10 MW
- `scraper_ocr.py:63`, `:669-675`: sólo las diurnas de 10 MW o más se marcan (nota, confianza media); el tipo no
  cambia. 74 de las 184 protegidas sólo OCR son diurnas; de día la tabla da 0,937 de FALSO_POSITIVO con VRP de 1 MW o
  más (403 de 430). La causa es la geometría (H-O1, H-O2); la hora es el indicador. CONFIRMADO. **GRAVEDAD 3.**

### H-O4 (951). `Metodo_Validacion` no dice qué método decidió la clase
- `scraper_ocr.py:701` escribe `roi_temporal_v26` para todas; el método real (`ocr_utils.py:1308/1364`) se descarta.
  VRP Chile no puede excluir el método de grupo sin interpretar la nota. CONFIRMADO. **GRAVEDAD 3.**

### H-O5 (203). Las 39 reescrituras de VRP Chile son manuales; el rastro es incompleto
- 34 de `b88e7cb45f` (2026-06-15) y 5 de `52ff007401` (2026-08-04), ninguna del código (coincide con el verificador de
  S159, que llegó a lo mismo por su cuenta). En toda la historia: 76 reescrituras, 55 manuales y 21 de
  `reconciliar_latest.py`, todas ALERTA a FALSO_POSITIVO. 75 de 76 dejan marca, pero 5 manuales usan `Editado=AUTO`
  (la marca del código) y la confianza previa se pierde siempre. CONFIRMADO. **GRAVEDAD** 4 según el auditor, 2 para
  mí: no tuerce datos, tuerce trazabilidad (sin verificador propio).

### H-P3 (405). El scraper depende de un disparador externo sin respaldo ni registro
- `main.yml:3-4` sólo tiene `workflow_dispatch`; la credencial del disparador no está en `REGISTRO_CREDENCIALES.md`.
  Si se apaga, no hay corrida ni aviso. CONFIRMADO. **GRAVEDAD 3.**

### H-P4 (403). Si MIROVA renombra un sensor, el scraper abre una serie paralela en silencio
- `scraper.py:168`, `:184-188`. Simulado: 11 filas `VIIRS-I`. CONFIRMADO (simulado). **GRAVEDAD 3.**

### H-O6 a H-O9 (204, 205, 206, 207), gravedad 3
- 204: la corrección automática sólo baja alertas y sólo si la tabla lista la pasada (`reconciliar_latest.py:35-44`).
- 205: la corrección manual `2a34d8e42e` dio a dos filas VIIRS750 de Isluga (2026-05-30) la distancia de otra pasada
  y otro sensor.
- 206: 647 notas en mojibake desde el commit manual `ffc7a97d8b` (sigue abierto desde S139 H203).
- 207: 592 de 987 ALERTA_TERMICA_OCR con `Distancia_km` 0 (571 con la distancia sólo en la nota).

### Gravedad 2 y 1 (publicados con su conteo, sin verificador: entrada de la próxima auditoría)
- Gravedad 2 (9): 209 clase de intensidad del OCR en otra escala (549 filas); 210 el OCR no ve nada bajo 1 MW en
  VIIRS750 y MODIS; 211 el OCR no escribe FALSO_POSITIVO para pasadas nuevas desde febrero; 212 fila borrada a mano
  recreada por el OCR con otra clase; 213 ALERTA_SIN_GEOMETRIA_OCR (41) se publica como alerta sin distancia; 414
  nadie usa `Ultima_Actualizacion_UTC`; 408 el OCR descarta pasadas de más de 24 h aunque sigan en la imagen; 409 el
  scraper sobrescribió 24 imágenes que el OCR guardó verificadas; 410 Dependabot puede mergear solo un parche de bs4,
  requests o pandas y ningún test ejecuta el parseo de `scraper.py`; 952 el comentario de `ocr_utils.py:291-303`
  contradice el código.
- Gravedad 1 (7): 214 Zenith y Azimut cambian de formato en cada reescritura; 411 `cancel-in-progress` cancela en
  gris; 412 la ficha de Mirova-v1 en `MAPA_WORKSPACE.md` está desactualizada; 413 `marcar_artefacto.yml:131`
  interpola un input en el shell; 415 el PR agrupado de Dependabot retiene parches; 904 y 905 notas de instrumento
  (abajo).

## 2. VERIFICADO LIMPIO (y contra qué vara)

- **El código no quita filas de la tabla por lo que haga MIROVA:** `scraper.py:232-243` sólo agrega o actualiza;
  `backfill_horas_utc.py` reescribe fila por fila y aborta si el archivo está roto; los demás sólo leen (lectura del
  código, orquestador y verificador).
- **Contenido de filas de la tabla:** 0 reescrituras de tipo, VRP, distancia o clase (S159, 1.238 versiones; no lo
  repetí). Ciclo normal: 0 pérdidas, 0 duplicados, 33 líneas refrescadas (`v01`).
- **H202 de S139 (coma de miles) cerrado:** `scraper.py:54-63` lee «2,178.53» y la fila entra como ALERTA_TERMICA
  (simulación del auditor de operación con el código de HEAD).
- **Nombres:** 11 canónicos y 0 duplicados en la tabla de HEAD (42.440 filas); 0 pares de la misma pasada con dos
  horas a menos de 120 s (control: 16 pares de gránulos vecinos a 121 a 400 s) (`11_casi_duplicados.py`).
- **Gránulos de pasadas partidas:** el scraper no fusiona ni descarta (llave al segundo); la tabla guarda 17 pares a
  menos de 15 min (auditor OCR).
- **OCR:** 0 duplicados en 740 versiones; 0 bajas del código (las 7 de la historia son manuales, de febrero); VRP
  idéntico a la tabla en VIIRS375 (441 pasadas compartidas; VIIRS750 y MODIS difieren hasta 0,98 MW por truncado);
  0 contradicciones de clase hoy entre OCR y tabla; V31 y V31.1 cierran sin escribir cuando dudan.
- **Merges del visualizador:** 0 de 5.555 imponen un CSV de datos a `main`; un solo escritor bot por CSV en 60 días.
- **Cadencia:** 288 ciclos al día (mínimo 265), 0 huecos de más de 6 h y 2 de más de 1 h en 60 días; último ciclo y
  último dato coinciden.
- **Riesgo de `clase_mirova.py`:** 0 casos hoy (ver §4).

## 3. Arreglos recomendados para el scraper (no implementados: los decide Nicolás)

En orden de lo que más protege la referencia. Cada uno con su prueba vista en rojo cuando existe.

| # | arreglo | dónde | por qué y prueba |
|---|---|---|---|
| R1 | Orden total determinista al escribir todo CSV de datos: `sort_values(["timestamp","Volcan","Sensor"], ascending=[False,True,True], kind="mergesort")` | `scraper.py:240`; también `guardar_ocr`, `merger_maestro.py:117`, `merger_maestro.py:43` | Quita la causa de H-T1. Probado: 0 duplicados y 0 pérdidas en 12 mezclas reales (`v08`, `salida_07.txt`). El primer commit reordena todo una vez |
| R2 | No mezclar datos como texto: si el push se rechaza, `git fetch` + `git reset --hard origin/main` y volver a correr `scraper.py` sobre el archivo fresco | `main.yml:67-71`; mismo patrón en `ocr_workflow.yml:135` y `archivar_evidencia.yml:109` | Es el patrón que ya usa el paso «Distancia aproximada» (`ocr_workflow.yml:187-203`). Con R1 y R2 una corrida vieja no puede dañar |
| R3 | Guarda antes del push: si el CSV nuevo pierde alguna llave de `origin/main` o trae llaves repetidas, no empujar y dejar la corrida en rojo | paso nuevo en `main.yml` y `ocr_workflow.yml` | Prototipo `09_guarda_llaves.py`: FALLA en los 3 commits de pérdida probados (202, 299, 403 llaves) y PASA en ciclos normales y en el nulo (`salida_09.txt`) |
| R4 | Reponer las filas perdidas desde la historia | una vez, commit de datos | `10_recuperar_filas.py` arma `filas_recuperadas.csv` desde los padres de los episodios; recupera las 18 protegidas (14 de 14 de S159) |
| R5 | Fallar fuerte: salida distinta de 0 si `latest.php` no responde, no tiene `tbody`, trae 0 filas chilenas o una columna irreconocible; no commitear si sólo cambió la bitácora | `scraper.py:130-248`, `scraper_ocr.py:762-771` | H-P1: 141 ciclos reales en 0 filas cerraron OK |
| R6 | Vigilante de dato, fuera del pipeline: avisar si el máximo de `Ultima_Actualizacion_UTC` tiene más de 30 min | workflow programado aparte | H-P1, 414: la señal ya existe y se congela a los 5 min de una falla |
| R7 | Cron de respaldo para `main.yml` y fila de la credencial del disparador en `REGISTRO_CREDENCIALES.md` | `main.yml:3-4` | H-P3; regla 2 del CLAUDE.md global |
| R8 | Lista cerrada de sensores: uno desconocido es error, no serie nueva | `scraper.py:168` | H-P4 |
| R9 | El método de grupo de píxeles rojos no escribe ALERTA (o la escribe con confianza baja y marca de método) | `ocr_utils.py:1266-1311` | H-O1: 0,104 de precisión de día |
| R10 | Guardar en `Metodo_Validacion` el método real (estrella o grupo) | `scraper_ocr.py:701` | H-O4: sin eso VRP Chile no puede filtrar |
| R11 | Reconciliación con rastro completo: guardar la confianza previa; marca distinta para correcciones manuales | `reconciliar_latest.py:46-54` | H-O5 |
| R12 | Reparar el mojibake de las notas anteriores al 13-jun desde una copia limpia | commit de datos | H-O8, abierto desde S139 |
| R13 (VRP Chile) | El sync no debe rebasar el CSV: reset a `origin/main` y volver a bajar | `sync-mirova-csv.yml:191` de VRP Chile | H-V1, reproducido byte a byte |

## 4. Qué significa para VRP Chile

**Qué canal y qué filas usar para evaluar la réplica.**
- **Tabla, canal principal.** Confiable en contenido; incompleta por tres causas distintas que no se arreglan igual:
  (a) pérdidas por mezcla (H-T1): se recuperan desde la historia; (b) pasadas que la tabla nunca tuvo porque
  `latest.php` sólo muestra la última de cada par (H-P2): no se recuperan desde Mirova-v1 y entran como «sin
  información», nunca como negativo; (c) `Tipo_Registro` lo pone el scraper con el `limite_km` vigente al escribir
  (`scraper.py:170-180`): recalcular el tipo desde VRP y distancia (ya lo dice `MAPA_BASES_MIROVA_V1.md` §4).
- **OCR, sólo como complemento y filtrado.** VRP y hora, sí. Clase dentro o fuera del radio, sólo si salió del
  método de la estrella, de noche y desde V29.2 (2026-06-13). Como `Metodo_Validacion` no lo dice (H-O4), hoy hay que
  leer el método en la nota. Las 184 protegidas sólo OCR: 10 confirmadas por la tabla histórica, y entre 40 y 90
  falsas estimadas (centro ~55; supone que la precisión medida donde la tabla tiene la pasada vale donde no la tiene).
  Recomendación: sacarlas del criterio de victoria salvo las de estrella nocturna desde V29.2, y contarlas aparte.
- **Riesgo latente en `scripts/clase_mirova.py:65-75`.** `alerta_protegida` mira una fila a la vez, y
  `scripts/referencia_mirova_unificada.py:172-177` deja que la fila OCR principal le gane a la fila histórica de la
  tabla con la misma llave. Si la tabla perdiera una fila FALSO_POSITIVO cuyo gemelo OCR dijera ALERTA, VRP Chile la
  contaría protegida. Hoy: 0 casos (29 de 2.230 filas perdidas tienen gemelo OCR, las 29 con el mismo tipo; control:
  441 gemelos en la tabla de HEAD, 0 contradicciones; `12_ocr_vs_perdidas.py`/`salida_12.txt`). Gravedad 2: latente.
- **Correcciones a S159.** H1 (39 reescrituras): manuales, no del OCR ni de MIROVA. H2 (pérdida): confirmada y
  atribuida al commit exacto del scraper. H4 (81dd25ce3): es daño del sync de VRP Chile, no una versión de la tabla.
  `MAPA_BASES_MIROVA_V1.md:142` y `:340` («sin reprocesos retroactivos»): vale para recapturas, no para ediciones
  manuales (como dijo el verificador de S159).

**Cómo congelar la referencia.**
1. Leer de la historia de **Mirova-v1** por sha, no de las copias de VRP Chile (que tienen daño propio, H-V1).
2. Vara de la tabla = HEAD del sha congelado ∪ los padres de los commits de episodio (lista en `08_censo_historia.py`;
   `10_recuperar_filas.py` lo hace en una corrida, sin bajar cientos de versiones), deduplicada por llave, con la guarda
   de `09_guarda_llaves.py` sobre el resultado (0 llaves repetidas). La unión de VRP Chile desde sus copias horarias
   recupera 1.946 de 1.948; desde los padres de episodio, todas.
3. Guardar sha256 de los archivos usados (el congelado `_s151_prereg_fk_11/_congelado_v1/MANIFIESTO.json` ya existe:
   usarlo por defecto en `banco_paridad`, como pidió el verificador de S159).
4. Ventana de asentamiento de 48 h (S159, no la re-medí).
5. Mientras R1 a R3 no estén puestos, revisar antes de cada evaluación si apareció un commit nuevo con la firma de
   `04_firma_commits_mezcla.py` (toca el consolidado sin la bitácora): es un piso, no un detector completo (no ve
   cascadas como `ecdc09e4d6`), pero en 60 días no dejó daño fuera (`v05`).

## 5. Pruebas de campo y decisiones para Nicolás

| ID | qué mirar | qué decide | qué desbloquea |
|---|---|---|---|
| C1 | `gh run list` de la ventana del 18-oct 17:15 a 17:40 UTC (comando en H-T1): `headSha` y `runStartedAt` | por qué una corrida parte de una base vieja | si R2 basta o además hay que cambiar el checkout |
| C2 | 10 imágenes Dist.png de alertas del método de grupo (lista en `frente2_ocr\precision_A_detalle.csv`) | qué son los píxeles rojos | cerrar la SOSPECHA de H-O1 |
| C3 | tras R1 a R3: contar corridas que la guarda deja en rojo durante una semana | si el mecanismo sigue apareciendo | quitar la revisión manual de §4 punto 5 |

| decisión | opciones | recomendación |
|---|---|---|
| Arreglar el bucle de push | R1 solo; R1+R2+R3; nada | **R1+R2+R3**: R1 quita la causa, R3 es la guarda que demuestra que no vuelve |
| Reponer filas perdidas en Mirova-v1 | commit de datos con `filas_recuperadas.csv`; dejarlo sólo en VRP Chile | reponer en Mirova-v1 (es lo que publica su tablero), con nota en el commit |
| Alertas sólo OCR en el criterio de VRP Chile | todas; sólo estrella nocturna desde V29.2; ninguna | **sólo estrella nocturna desde V29.2**, el resto contado aparte |
| Método de grupo en el OCR | apagarlo; marcarlo con confianza baja | marcarlo (R9 + R10): no se pierde la pista y VRP Chile puede filtrar |

## 6. SEGUIMIENTOS, SIN DATO y fuera de alcance

- **SEGUIMIENTOS:** `registro_vrp_positivos.csv` y el maestro heredan el daño de H-T1 (no medido aparte); los dos
  syncs del 19-ago (17:39 y 17:41) no son del cron de VRP Chile; el auditor de operación dejó dos copias de prueba
  (`frente4_operacion\sandbox_m08`, `sandbox_m11`, 124 MB) que se pueden borrar.
- **SIN DATO:** disparador exacto de H-T1 (C1); qué representan los píxeles rojos (C2); estado de los PR de
  Dependabot; causa del hueco del 2026-08-06; último run verde por workflow (requiere `gh run list`).
- **Notas de instrumento:** `git merge-file` NO reproduce los bytes de un rebase real (905): mis cinco intentos de
  simulación con él, y con un ciclo simulado casi igual al padre, devolvieron el padre entero (scripts `03*.py`, se
  conservan como registro de lo que no reproduce). Mi script 07 se caía por el largo de la abreviatura de hash (904);
  corregido y re-corrido en esta sesión.

## 7. Lo que la guía no me dio

Primera auditoría con la guía mejorada fuera de VRP Chile y ARSAND. Lo que eché de menos, en orden de costo:

1. **Qué hacer cuando la línea base roja no sale.** Pasé por seis variantes de simulación que no reprodujeron nada
   antes de entender por qué: mi ciclo simulado era casi idéntico al padre, así que no había nada que mezclar (un
   instrumento vivo que medía otra cosa, regla 8b de la plantilla), y `git merge-file` no es el mismo instrumento que
   un rebase. Lo que destrabó fue **reproducir con entradas reales donde las tres se conocen** (la copia de VRP Chile;
   el verificador lo hizo con ternas reales de Mirova-v1). Propongo a §3: «antes de simular, buscar un caso real con
   todas sus entradas conocidas; una simulación que no reproduce se audita como instrumento antes de descartar la
   hipótesis».
2. **La historia de git como instrumento.** El censo más barato y más decisivo fueron firmas leídas sólo de árboles
   y metadatos (qué archivos toca un commit, fecha de autor contra fecha de commit), sin bajar blobs: 83.146 commits
   del consolidado en segundos, en un clon de 13,9 GB con el disco al 95 %. La guía no tiene un frente «por historia»
   ni dice cómo medir con restricciones de disco o de API. Propongo agregarlo a §4.
3. **La cadena de copias es un instrumento más.** §0 dice que la referencia externa tiene su propia política; no dice
   que la copia local de la referencia puede fabricar daño propio. Aquí una «versión corrupta de la referencia» era
   del consumidor. Propongo a §0: «antes de atribuir un defecto a la referencia, buscarlo en la fuente por sha».
4. **Mensajes de otras sesiones a mitad de auditoría.** Llegó una conclusión de otra sesión mientras los auditores
   corrían. La guía protege la independencia del verificador, pero no dice qué hacer con una conclusión externa que
   llega a un auditor en vuelo. Se la pasé como hipótesis explícita para comprobar (la comprobó con sus herramientas);
   eso cuesta independencia. Propongo una regla: una conclusión externa se le pasa al auditor marcada como hipótesis,
   y el verificador no la recibe.
5. **El preámbulo canónico es de ARSAND.** Trae voseo, «CÓMO SE VE EN LA MESA» y «un informe corto y todo sólido
   vale más que uno largo», que §5 de la propia guía llama filtro de severidad disfrazado. §8 dice que basta ajustar
   la primera frase; no basta. Conviene un preámbulo neutro con huecos para el síntoma visible y el dominio.
6. **Presupuesto.** Nada sobre cuándo cortar una línea de investigación ni sobre límites de API o de disco como
   restricciones de diseño del instrumento. Aquí decidieron qué se podía medir.
7. **§3b no aplicó.** No comparé versiones de un sistema contra una referencia; sí probé el arreglo R1 con brazos
   (producción, orden estable, nulo), pero sin pre-registro commiteado. Lo declaro: esa prueba es *post hoc*.

Lo que sí funcionó como dice la guía: el verificador con contexto limpio encontró cosas nuevas en los dos frentes
(901, 903, 904, 905; 951, 952), rebajó dos gravedades, ensanchó el rango de protegidas falsas y corrigió dos frases
mías; y el preámbulo con «sin relleno no quiere decir corto» dio informes de 14 y 15 hallazgos con todo anclado.

## 8. Archivos

- Este informe: `D:\vrp-trabajo\mirova-v1-auditoria\INFORME.md`; lista filtrable: `D:\vrp-trabajo\mirova-v1-auditoria\hallazgos.csv`.
- Scripts y salidas del frente 1: `D:\vrp-trabajo\mirova-v1-auditoria\01_*.py` a `12_*.py` y `salida_*.txt`;
  `log_cons_bitacora.txt` (insumo de 04, 05 y 08); `filas_recuperadas.csv` (salida de 10).
- Frentes 2 y 3: `D:\vrp-trabajo\mirova-v1-auditoria\frente2_ocr\`. Frente 4: `D:\vrp-trabajo\mirova-v1-auditoria\frente4_operacion\`.
- Verificadores: `D:\vrp-trabajo\mirova-v1-auditoria\verificador_frente1\`, `D:\vrp-trabajo\mirova-v1-auditoria\verificador_ocr\`.
- Preámbulo usado: `D:\vrp-trabajo\mirova-v1-auditoria\PREAMBULO_AUDITOR_MIROVA.md`.
