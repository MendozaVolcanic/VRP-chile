# S139 tanda 2: mapa de las bases de datos que produce Mirova-v1

Fecha: 2026-09-14 (hora del servidor GitHub, `Date: Mon, 14 Sep 2026 11:50:53 GMT`).
Remoto auditado: `MendozaVolcanic/Mirova-v1`, rama `main`, commit `f51634e165` (2026-09-14 12:01 UTC).
Alcance: sólo lectura. Nada del repositorio fue modificado salvo este informe y los scripts de
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\bases_mirova_v1\`.
Este informe NO repite el eje 1 (`EJE_1_semantica_etiquetas_referencia.md`): allá está qué significa
cada etiqueta; acá está qué es cada archivo, desde cuándo sirve y qué se perdió en el camino.

## 0. Resumen para quien decide

1. **Hay cinco archivos, pero sólo dos son fuente.** `registro_vrp_consolidado.csv` (tabla `latest.php`)
   y `registro_vrp_ocr.csv` (imágenes) son las únicas bases primarias. `registro_vrp_positivos.csv` es
   el consolidado filtrado a ALERTA_TERMICA; `registro_vrp_maestro_publicable.csv` es la unión de las
   alertas de ambos canales; `registro_<Volcan>.csv` es el maestro partido por volcán. Los tres
   derivados se regeneran completos en cada ciclo y se verificaron llave por llave contra su
   definición: 0 diferencias (§1). Los "consolidados de lo que se publica en el dashboard" que
   recuerda Nicolás son el maestro publicable y los `registro_<Volcan>.csv`: es lo que dibuja
   `visualizador.py` y lo que descarga el botón del dashboard de Mirova-v1.
2. **El consolidado del remoto perdió filas en silencio, dos veces** (23-abr y 25-ago de 2026, las dos
   en commits del bot del scraper): la versión del 22-ago tenía 378 filas que hoy no existen (348
   RUTINA, 20 ALERTA_TERMICA, 10 FALSO_POSITIVO), y sumando las copias más viejas son **31 ALERTAS de
   MIROVA que la referencia ya no tiene**, de los 11 volcanes (Láscar 11, Lastarria 7, PCC 7). VRP
   Chile hereda la pérdida porque `latest_consolidado.csv` y `data/mirova/*.json` se copian del
   remoto (H201). Las copias viejas que VRP Chile y el disco de Nicolás conservan permiten recuperarlas.
3. **Un VRP de 1.000 MW o más aborta el ciclo entero del scraper** (`float('2,178.53')`): pasó dos
   veces, 36 ciclos, y las pasadas de esa hora sólo quedaron en el OCR (H202). Es latente para la
   erupción real que más importa.
4. **Las notas del OCR anteriores al 13-jun están en mojibake** desde un commit humano del 12-jun
   (`ffc7a97d8b`, reescribió las 652 filas): el regex del loader de VRP Chile no encuentra distancia
   en 578 ALERTA_TERMICA_OCR (H203). La copia local del 28-mar está limpia.
5. **FALSO_POSITIVO no dice que el cráter no tuviera nada.** MIROVA publica UNA fila por pasada y
   volcán con el VRP **integrado sobre todos los píxeles alertados**, `LAT/LON` del píxel **más
   caliente** y `Max_Dist` al píxel **más lejano** (esquema OSF v2.5, verbatim en §4). En el archivo
   OSF de Chile el 83 % de las pasadas tiene más de un píxel y en el 41 % de ésas el más lejano no es
   el más caliente. La distancia de `latest.php` tiene la misma cuantización que `Max_Dist`
   (SOSPECHA de que es esa columna). La memoria de Nicolás es correcta para la posición (píxel más
   caliente) y probablemente incorrecta para la distancia (H204).
6. **Desde cuándo sirve cada base** (§2): consolidado con tipos actuales desde 2026-01-16, cobertura
   nocturna 86 % en enero (10 volcanes), 95 % en febrero, 99 a 100 % desde marzo; Tupungatito desde
   2026-02-14 y con regla de 7 km desde 2026-02-23. OCR: existe desde 2026-01-20, versiones inestables
   hasta el 24-feb, V21 estable desde marzo, distancia medida sólo desde 2026-06-13, geometría de
   observación y banner sólo desde 2026-08-04.

## 1. Qué es cada archivo (código vigente del remoto)

Cadencias medidas en la bitácora y en GitHub Actions: `main.yml` (scraper) no tiene cron propio
(`main.yml:4`, sólo `workflow_dispatch`) y corre ~288 veces al día (bitácora: 288 INICIO/día desde el
2026-01-20; 8.910 corridas en julio y en agosto); `ocr_workflow.yml:6` declara `5 * * * *` pero
corrió 1.779 veces en julio y 1.939 en agosto (unas 60 al día, ~2,5 por hora: hay un disparo
externo además del cron, como dice el comentario de `ocr_workflow.yml:92`).

| Archivo | Quién lo escribe | Una fila es | Deriva de | Quién lo consume |
|---|---|---|---|---|
| `registro_vrp_consolidado.csv` | `scraper.py:205` (`df_final.to_csv`), cada ~5 min; se reescribe ENTERO en cada ciclo | un gránulo por volcán y sensor, llave `(timestamp, Volcan, Sensor)`, `drop_duplicates(keep='last')` (`scraper.py:201`); 13 columnas | `latest.php` (`scraper.py:114`); sólo lo que la tabla muestra al momento de la visita | Mirova-v1: `merger_maestro.py:63`, `reconciliar_latest.py:62`, `scraper_ocr.py:458` (dedup). VRP Chile: `sync-mirova-csv.yml:50-52` cada hora a `latest_consolidado.csv` y de ahí `data/mirova/<Vol>.json` (`:108-110`); `audit-weekly.yml:55-56` al snapshot semanal |
| `registro_vrp_positivos.csv` | `scraper.py:206`, mismo ciclo | fila del consolidado con `Tipo_Registro == ALERTA_TERMICA` | consolidado | Mirova-v1: `visualizador.py:513-517` sólo como fallback si no existe el maestro; `index.html:413` (sondeo de "datos nuevos"). VRP Chile: nadie |
| `registro_vrp_ocr.csv` | `scraper_ocr.py:496`, cada ~24 min; sólo AGREGA filas (`:491`), nunca reescribe las viejas salvo `reconciliar_latest.py:42-50` (cambia Tipo, Confianza, Distancia, Nota) y ediciones humanas (`Editado = SI`, 49 filas) | un evento leído de `Latest10NTI.png` de las últimas 24 h (`:217-239`) que no esté en el consolidado ni en el OCR (`ocr_utils.py:1304`); 23 columnas (`:55-66`) | imágenes por volcán y sensor | Mirova-v1: `merger_maestro.py:64`. VRP Chile: `audit-weekly.yml:57-58` al snapshot; `pipeline/mirova_csv_loader.py` (CONS unión OCR) |
| `registro_vrp_maestro_publicable.csv` | `merger_maestro.py:146`, tras cada corrida OCR (`ocr_workflow.yml:87`) | fila de consolidado u OCR con Tipo ALERTA_TERMICA o ALERTA_TERMICA_OCR, VRP > 0, `Confianza != invalido` (`:129-143`); dedup por llave con el consolidado primero (`:94-113`, `Origen_Dato = ambos` cuando está en los dos: 326 filas, y en las 326 gana la fila del consolidado); 17 columnas | consolidado + OCR | Mirova-v1: `visualizador.py:509-511` (gráficos de las 11 tarjetas), `index.html:412` |
| `registro_<Volcan>.csv` (11) | `merger_maestro.py:41-48`, mismo ciclo | fila del maestro publicable de ese volcán; nombre con `_` en vez de espacio y guión | maestro publicable | Mirova-v1: `index.html:389` (botón "descargar CSV"); `graficos_completo.yml:166` los copia al sitio. VRP Chile: nadie en código (tres copias de abril en `mirova_v1_snapshot/` sólo citadas en docs) |
| `registro_vrp_consolidado al 08042026.csv` | copia manual, sólo en el disco de Nicolás; nunca estuvo en el remoto (0 commits con esa ruta) | igual al consolidado del 2026-04-08 12:50 UTC, 11.319 filas, todavía con 65 filas `Peteroa` | consolidado | nadie. Hoy vale como **respaldo**: contiene 244 filas que el remoto perdió (§3 H201) |
| `anotaciones.csv` | `marcar_artefacto.yml:76-120` (formulario manual) | una marca `artefacto` o `dudoso` por `(timestamp, Volcan)`; 1 fila hoy (Láscar 760,6 MW del 2026-06-15, marcada 2026-07-15) | curaduría humana | `visualizador.py:48-70,113-131`: excluye del autoescalado y dibuja aparte; el dato crudo no se toca |
| `estado_sistema.json` | `visualizador.py:800-809` | heartbeat | | `index.html:795` (semáforo) |
| `bitacora_robot.txt` | `scraper.py:35-43`, una línea por evento; 218.018 líneas del 2026-01-11 al 2026-09-14 sin huecos > 6 h | | | nadie; es la única evidencia de los ciclos abortados (H202) |
| `graficos_tendencia/` | nadie desde el 2026-01-15 (último commit) | 10 PNG muertos | | nadie |
| `dashboard_interactivo.html` | nadie lo referencia en el remoto (grep 0) | | | huérfano |
| `v_html/`, `v_html_log/` | `visualizador.py`, vía `graficos_completo.yml:84-86`, sólo si cambió el hash de maestro + positivos + anotaciones | 11 HTML Plotly con la serie completa | maestro publicable | `index.html` (iframes) |

Verificación de las derivaciones (`01_mapa_archivos.py`, remoto de hoy, 37.474 filas): positivos =
consolidado[ALERTA] en 1.462 de 1.462 llaves; maestro publicable reconstruido con la regla del código =
2.005 de 2.005; los 11 `registro_<Volcan>.csv` = maestro[Volcan] en los 11 y suman 2.005. Control
positivo: quitar una fila a positivos deja 1 llave "solo en consolidado" (esperado 1).

Lo que el OCR aporta al maestro: de 870 ALERTA_TERMICA_OCR, 327 comparten llave exacta con una
ALERTA del consolidado (y las mismas 327 a ±60 s: no hay más solapes por desfase de segundos) y 543
existen sólo en el OCR. En las 327 compartidas el OCR escribió PRIMERO en 323 (mediana 5 min de
ventaja, p90 20 min): la imagen de MIROVA se actualiza antes que `latest.php`, así que el
`DUPLICADO_LATEST` del OCR no las ve, y el merger las resuelve después dándole la fila del consolidado.
En 61 de esas 327 el VRP difiere en más de 0,05 MW, todas VIIRS750 o MODIS (0 en VIIRS375): es el
truncado a entero de la imagen (eje 1 H111), por eso conviene que gane el consolidado, como hace el
loader de VRP Chile (`mirova_csv_loader.py:196-202`).

## 2. Historia de completitud: desde cuándo es confiable cada archivo

Denominadores: consolidado 37.474 filas (2026-01-10 19:06 a 2026-09-14 07:40 UTC); OCR 961 filas
(2026-01-20 05:12 a 2026-09-14 06:42). "Noche" = hora solar aproximada de Chile antes de las 06 o
desde las 18 (UTC antes de 10:42 o desde 22:42). Script `02_completitud_mensual.py`.

### 2.1 Consolidado

| mes | filas | noches de volcán con fila nocturna MODIS / VIIRS / VIIRS375 (%) | filas nocturnas por noche de volcán (media) M / V / V375 | déficit vs jun-ago (%) V / V375 |
|---|---|---|---|---|
| 2026-01 | 2.528 (10 volcanes) | 86,0 / 83,1 / 86,4 | 1,96 / 1,77 / 1,62 | 34 / 39 |
| 2026-02 | 3.514 | 94,2 / 95,5 / 95,1 | 2,02 / 1,77 / 1,70 | 34 / 36 |
| 2026-03 | 3.940 | 100 / 99,1 / 99,1 | 2,03 / 1,66 / 1,60 | 38 / 40 |
| 2026-04 | 4.923 | 99,1 / 99,7 / 100 | 2,02 / 2,59 / 2,31 | 3 / 13 |
| 2026-05 | 4.968 | 98,2 / 100 / 100 | 2,09 / 2,61 / 2,36 | 2 / 11 |
| 2026-06 a 08 | 4.981 / 5.008 / 5.246 | 100 / 99,7 a 100 / 99,7 a 100 | 2,1 / 2,3 a 3,1 / 2,4 a 3,0 | referencia |
| 2026-09 (14 días) | 2.366 | 100 / 100 / 100 | 2,08 / 3,38 / 3,23 | -27 / -22 |

Control positivo: borrar el 50 % de las filas de junio en una copia baja las noches con fila de 330 a
260 a 262 por sensor.

Lectura: la cobertura de noches (¿hubo al menos una fila?) es sana desde marzo. Lo que sí cambia es
**cuántos gránulos por noche expone la tabla**: VIIRS pasa de 1,6 a 1,8 filas nocturnas por noche de
volcán en enero a marzo, a 2,3 a 2,6 en abril a junio y 3,0 a 3,4 en agosto y septiembre; MODIS es
plano en 2,0 a 2,1 todo el año. El scraper visitaba la tabla cada 5 min desde el 2026-01-20 (bitácora,
288 ciclos/día), así que el salto de abril no es del scraper: es del lado de MIROVA (más gránulos
VIIRS listados, por ejemplo otro satélite) o de la tabla. **Causa: SOSPECHA**; el número es medido.
Consecuencia para el banco: una tasa "por pasada" de VIIRS de enero a marzo no es comparable con la
de agosto; hay que trabajar por noche de volcán (eje 1 §3) o normalizar por gránulos expuestos.

Hitos de reglas, todos verificados en el código o en los datos:
- **2026-01-10 a 01-15**: scraper en desarrollo (80 a 247 ciclos/día); 17 filas RUTINA con VRP > 0
  (regla vieja); `FALSO_POSITIVO` existe desde el commit `2bd447787a` del 2026-01-16 (eje 1 H109).
- **2026-01-16 a 01-19**: el scraper corrió 856 a 1.440 ciclos/día (cada minuto); desde el 01-20, 288/día.
- **Tupungatito**: primera fila 2026-02-14 06:06 UTC; límite 5 km hasta el commit `2d025de0a8` del
  2026-02-23 (7 km desde entonces).
- **Peteroa → PlanchonPeteroa**: 65 filas migradas en el remoto el 2026-06-12 (`62c34e27`); las copias
  anteriores a esa fecha (checkout local, backup del 08-abr, `01_05_2026_*.csv` de VRP Chile) siguen
  con `Peteroa`.
- **Clasificación**: 12 filas RUTINA con `Clasificacion Mirova = FALSO POSITIVO` y 228 ALERTA "Bajo"
  (escala vieja) siguen en el archivo; el máximo VRP de una ALERTA es 4,75 MW; el de un FALSO_POSITIVO,
  347,13 MW (Tupungatito VIIRS375 2026-06-19 17:30 UTC, diurno, a 24,66 km).

### 2.2 OCR

| mes | filas OCR | ALERTA_OCR / FALSO_OCR | Version_OCR dominante | Confianza alta / media / baja | `Distancia_km` = 0 ("no medida") | ALERTAS OCR ÷ ALERTAS consolidado |
|---|---|---|---|---|---|---|
| 2026-01 | 31 | 18 / 13 | 1.0 (31) | 25 / 4 / 2 | 31 de 31 | 18 ÷ 70 = 0,26 |
| 2026-02 | 47 | 39 / 8 | 1.0, 17, 20, 21 mezcladas | 41 / 3 / 3 | 45 de 47 | 39 ÷ 134 = 0,29 |
| 2026-03 | 164 | 160 / 4 | 21.0 (164) | 160 / 0 / 4 | 160 de 164 | 160 ÷ 179 = 0,89 |
| 2026-04 | 123 | 107 / 16 | 21.0 | 107 / 0 / 16 | 107 de 123 | 107 ÷ 213 = 0,50 |
| 2026-05 | 206 | 183 / 23 | 21.0 | 183 / 0 / 23 | 183 de 206 | 183 ÷ 260 = 0,70 |
| 2026-06 | 163 | 150 / 13 | 21.0 (81), 29.1 (4), 29.2 (78) | 147 / 3 / 13 | 79 de 163 | 150 ÷ 226 = 0,66 |
| 2026-07 | 76 | 69 / 7 | 29.2 | 66 / 3 / 7 | 0 de 76 | 69 ÷ 142 = 0,49 |
| 2026-08 | 98 | 92 / 6 | 29.2 (14), 30.0 (84) | 83 / 9 / 6 | 1 de 98 | 92 ÷ 139 = 0,66 |
| 2026-09 | 53 | 52 / 1 | 30.0 | 50 / 2 / 1 | 4 de 53 | 52 ÷ 99 = 0,53 |

Métodos de validación: enero y febrero mezclan 12 métodos distintos (`sin_pixeles_roi`,
`negro_dominante_con_estrella`, `desconocido`, `rgb_analysis`...); desde marzo el 100 % es
`roi_temporal_v26`. Las filas se escriben el mismo mes del satélite (la matriz mes satélite × mes de
proceso es diagonal salvo 5 filas de fin de mes): **no hubo reprocesos retroactivos del OCR**, así
que lo que enero y febrero no capturaron no se recuperó nunca.

Cuantificación de "los primeros meses la base no estaba completa": el canal OCR no existe antes del
2026-01-20; entre el 01-20 y el 02-24 corrió con siete versiones distintas (commits `Create
scraper_ocr.py` 2026-01-20 a `0bee904c0a` 2026-02-24; 94 corridas fallidas de 1.873 en febrero) y
agregó 0,26 a 0,29 alertas por cada alerta del consolidado, contra 0,50 a 0,89 en marzo a junio. Con
la tasa de marzo a junio como referencia (~0,66), a enero y febrero les faltarían del orden de 25 y
50 alertas OCR respectivamente (estimación por proporción, SOSPECHA: la actividad real de esos meses
no tiene por qué ser igual). El consolidado de enero tiene además un 14 % de noches de volcán sin
fila y ningún Tupungatito.

Hitos del OCR verificados:
- **2026-01-20**: nace (`fa4c7fdc16`); primer commit del CSV 2026-01-31.
- **2026-02-24**: última de las versiones "Update scraper_ocr.py"; V21 estable desde marzo.
- **2026-06-11**: calibración corregida (`7727c751fb`): Tupungatito `Y_LIMITE_PX` 257 → 243 (antes
  equivalía a 5,1 km, no 7), eje 0 km 335 → 295, fórmula de distancia de FASE 1 invertida
  (`tasks/AUDITORIA_OCR_EMPIRICA_2026-06.md` §B, README changelog V5.1). Todo lo clasificado antes usó
  esa geometría.
- **2026-06-12 19:26 UTC**: commit humano `ffc7a97d8b` reescribe las 652 filas y deja las notas en
  mojibake (H203).
- **2026-06-13**: V29.2 persiste `Distancia_km` medida (`723a846c7e`); antes era 0,0 fijo.
- **2026-06-15**: reconciliación contra `latest.php` (`c9026a94bc`) + 49 filas reclasificadas a mano
  (`Editado = SI`, `b88e7cb45f` y `2a34d8e42e`); 23 más reclasificadas por el sweep automático
  (`Editado = AUTO`).
- **2026-08-04**: V30 agrega `Zenith_Sat_deg`, `Azimut_Sat_deg`, `Nivel_Anomalia_MIROVA`,
  `Confianza_Geometria` (`68c413283d`); pobladas en 135 de 961 filas (0 antes de agosto);
  `backfill_geometria_v30.py` existe pero se subió al remoto recién el 2026-09-13 (`90a2e06c48`) y no
  hay evidencia de que haya corrido sobre el CSV publicado (0 filas de enero a julio con geometría).

## 3. Hallazgos (ordenados por gravedad)

### H201. El consolidado del remoto perdió filas en silencio en dos episodios; 31 ALERTAS de MIROVA ya no están en la referencia, y VRP Chile heredó la pérdida
- **ARCHIVO:LÍNEA** `scraper.py:199-205` (reescribe el archivo entero cada ciclo); `main.yml:58` (`git pull origin main --rebase --autostash -X ours` en el bucle de reintento; en abril era `git add -A` + `pull --rebase -X ours`, commit `7a971efd09`:39-43). `SCRIPT:SALIDA` `06_perdidas_y_carreras.py`, `07_cronologia_perdidas.py`, `08_bisect_commit_perdida.py` (`salida_08_bisect_abril.txt`, `salida_08_bisect_agosto.txt`) y el inventario en la sesión (bloque "archivo histórico -> llaves ausentes").
- **QUÉ PASA** El scraper no agrega filas: vuelve a escribir los 37 mil registros en cada ciclo, y cada
  commit cambia la mitad de las líneas (los 4 últimos commits del remoto: `+19062/-19062` cada uno
  sobre 37.474 filas; el 23-abr alternaban `+6924/-6924` y `+7040/-7040`). Con dos corridas
  concurrentes y un `rebase -X ours` que resuelve conflictos solo, el archivo puede quedar con menos
  filas de las que tenía. Medido contra la historia del propio remoto: la versión del 2026-04-21
  20:25 tenía 316 llaves que hoy no existen; la del 2026-08-21 20:50, 378 (348 RUTINA, 20
  ALERTA_TERMICA, 10 FALSO_POSITIVO, repartidas de enero a agosto); la del 2026-08-28 y todas las
  posteriores, 0. Los dos commits en que empieza la caída son de `VolcanoBot`: `9d70bc2d53`
  (2026-04-23 14:38 UTC, con la caída continuando hasta las 19:20: 14.201 → 13.845 filas) y
  `fb2a3123f8` (2026-08-25 18:44 UTC, `+1326/-252`, seguido a los 2 min por `d09d570eac`
  `+17487/-18763`). Ninguna de las filas perdidas reaparece con otro timestamp (0 a ±120 s). Unión
  de ALERTAS recuperables desde las copias viejas: **31** (Láscar 11, Lastarria 7, PCC 7, Isluga 2,
  Tupungatito 2, Chaitén 1, Planchón-Peteroa 1; VIIRS375 18, VIIRS750 7, MODIS 6), lista completa en
  la salida del inventario. Ejemplo: Láscar MODIS 2026-03-04 07:15 UTC, 2,28 MW a 1,41 km, presente
  en el remoto hasta el 22-abr y en el backup local del 08-abr, ausente en `data/mirova/Lascar.json`
  de VRP Chile (grep 0). El mecanismo exacto (qué par de corridas colisionó) es SOSPECHA; la pérdida,
  sus fechas y su magnitud son medidas.
- **CÓMO SE VE EN EL DASHBOARD** En el de VRP Chile, 31 noches en que MIROVA sí publicó alerta
  aparecen sin punto MIROVA: una detección nuestra esa noche cuenta como falsa alarma en la métrica
  del navegador, y su ausencia cuenta como acierto. En el de Mirova-v1, esas 31 alertas ya no
  están en los gráficos ni en los CSV descargables.
- **CÓMO REPRODUCIRLO** `python 07_cronologia_perdidas.py --remoto <dir con el CSV de hoy> --historico <dir con cons_YYYY-MM-DD.csv>` (los históricos se bajan con `curl https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/<sha>/monitoreo_satelital/registro_vrp_consolidado.csv`, sha de `gh api ".../commits?path=...&until=<fecha>"`). Comparar `cons_2026-08-22.csv` (33.814 filas) con el de hoy.
- **CONFIANZA** CONFIRMADO (pérdida, fechas, commits, conteos); SOSPECHA (mecanismo de la carrera).
- **GRAVEDAD 4** Toca la hoja de respuestas del banco de prueba y la métrica que ve el operador; y el mecanismo sigue activo (la reescritura completa continúa hoy), aunque desde el 2026-08-29 no se midió ninguna pérdida nueva.

### H202. Un VRP con separador de miles aborta el ciclo entero del scraper para los 11 volcanes; las pasadas de esa hora quedan sólo en el OCR
- **ARCHIVO:LÍNEA** `scraper.py:140` (`vrp = float(cols[3].text.strip())`), `:109-211` (un solo `try` alrededor de todo el ciclo; el `except` sólo escribe la bitácora). `SCRIPT:SALIDA` bitácora del remoto: 21 líneas `ERROR: could not convert string to float: '2,178.53'` entre 2026-06-15 17:05 y 18:45 hora Chile y 15 con `'1,357.39'` entre 2026-07-08 17:05 y 18:15; `06_perdidas_y_carreras.py` bloque (B).
- **QUÉ PASA** Físicamente, un foco de miles de MW es o una erupción mayor o un artefacto solar
  diurno (A76). MIROVA lo imprime como `2,178.53` y el parseo revienta antes de guardar nada: en la
  ventana del 15-jun, 21 ciclos seguidos sin `Proceso completado` (3 completados en las dos horas,
  todos fuera de la ventana). Las filas de esa hora nunca entraron al consolidado: Láscar VIIRS375
  2026-06-15 17:24:01 UTC (760,60 MW a 1,08 km) y Lastarria 17:24:01 (19,26 MW a 1,49 km) existen
  sólo como ALERTA_TERMICA_OCR; Tupungatito VIIRS375 2026-07-08 17:36:02 (1.357,39 MW a 24,86 km)
  sólo como FALSO_POSITIVO_OCR. El valor `2,178.53` no quedó en ningún CSV. El consolidado tiene 0
  filas con VRP ≥ 1.000 en toda su historia.
- **CÓMO SE VE EN EL DASHBOARD** Los tres casos son diurnos (13 a 14 h local), así que hoy es
  invisible. El día que un volcán chileno supere 1.000 MW de noche, el consolidado (y con él
  `latest_consolidado.csv`, `data/mirova/*.json` y el dashboard de Mirova-v1 vía positivos) no lo
  tendrá; sólo el OCR, que además lo baja a confianza media si es diurno.
- **CÓMO REPRODUCIRLO** `grep "could not convert" bitacora_robot.txt`; `python -c "float('2,178.53')"`.
- **CONFIANZA** CONFIRMADO.
- **GRAVEDAD 4** Latente, pero cae exactamente en el escenario de alerta mayor.

### H203. Las notas del OCR anteriores al 2026-06-13 están en mojibake: el loader de VRP Chile no les encuentra distancia
- **ARCHIVO:LÍNEA** commit `ffc7a97d8b` (NMendoza, 2026-06-12 19:26 UTC, "invalidar 2 lecturas OCR erróneas de Isluga", `registro_vrp_ocr.csv +652/-652`); `pipeline/mirova_csv_loader.py:91` (`_OCR_DIST_RE = r"(?:dist[≈~=]|->|→)\s*(\d+\.?\d*)\s*km"`). `SCRIPT:SALIDA` bloque de bytes en la sesión: en el remoto, 606 notas con `distâ‰ˆ` (mojibake) y 98 con `dist≈` bien codificado; en la copia local del 28-mar, 195 bien y 0 mojibake; `07_cronologia_perdidas.py` última tabla.
- **QUÉ PASA** Un script corrido en Windows leyó el CSV como cp1252 y lo escribió como UTF-8: todas
  las filas procesadas hasta 2026-06-12 12:01 quedaron con `pÃ­xeles`, `lÃ­mite`, `distâ‰ˆ`; las
  escritas desde 2026-06-13 00:31 están limpias, y las 49 reclasificadas a mano el 15-jun tienen la
  parte vieja corrupta y el texto agregado limpio. El regex del loader exige `dist≈` y no matchea
  `distâ‰ˆ`: sobre las 870 ALERTA_TERMICA_OCR, quedan **sin distancia 578** (enero 18, febrero 39,
  marzo 160, abril 107, mayo 183, junio 71; 0 desde julio), aunque 507 de ellas sí traen `dist≈X km`
  en la nota. En las 327 llaves compartidas con el consolidado, la distancia del loader existe sólo
  desde junio y ahí coincide con `latest.php` (ratio mediano 1,02, error mediano 0,07 km).
- **CÓMO SE VE EN EL DASHBOARD** Invisible (el dashboard no usa el OCR, eje 1 H105). Se ve en toda
  auditoría que cruce posición contra la referencia OCR: esas 578 alertas entran sin `dist_km`.
- **CÓMO REPRODUCIRLO** `python - <<EOF` con `open(csv,'rb').read().count(b'dist\xc3\xa2\xe2\x80\xb0\xcb\x86')`; o `parse_ocr_distance('Estrella en Y=282 (dentro lÃ\xadmite Y=257, distâ‰ˆ3.40 km)')` devuelve `None`.
- **CONFIANZA** CONFIRMADO. Atribución al commit: CONFIRMADA por fechas y por el `+652/-652`; no se leyó el script que Nicolás corrió.
- **GRAVEDAD 3** No tuerce una alerta; tuerce cualquier estadística espacial de la referencia OCR de enero a junio. Además, las distancias de esas notas se midieron con la geometría anterior al 11-jun (eje 0 km en 335 en vez de 295, infladas ~2× según `AUDITORIA_OCR_EMPIRICA` §B2): aun decodificadas no valen como distancia.

### H204. MIROVA publica UNA fila por pasada con el VRP de TODOS sus píxeles y una sola distancia, que probablemente es la del píxel MÁS LEJANO: una fila FALSO_POSITIVO puede tener el cráter adentro
- **ARCHIVO:LÍNEA** `scraper.py:135-142` (una fila de `latest.php` = un `Time`, un `VRP MW`, un `Distance km`; llave única en 37.474 de 37.474 filas); `ocr_utils.py:450-505` (la imagen trae 10 celdas, una fecha y un VRP por celda); esquema OSF `data/mirova_reference/MIROVA_Database_Schema_v2.5.docx`, verbatim: *"Each row corresponds to a single satellite overpass associated with a target volcano"*, `Npix`: *"Number of alerted pixels contributing to the detection"*, `VRP`: *"Radiance values are integrated over the set of alerted pixels"*, `LAT/LON`: *"Latitude of the hottest alerted pixel"*, `Max_Dist`: *"Maximum distance between the volcano summit and the farthest alerted pixel (meters)"*. `SCRIPT:SALIDA` `05_osf_una_fila_por_pasada.py`.
- **QUÉ PASA** En una pasada con un incendio a 20 km y el cráter tibio, MIROVA suma los dos en un
  VRP y publica una distancia. En el archivo OSF de los 10 volcanes chilenos con datos (48.360
  pasadas, 2012 a 2025, 0 duplicados por pasada), el 83 % tiene `Npix > 1` y en 16.342 de esas 40.003
  el píxel más lejano está a más de 0,5 km del más caliente. Los valores de `Max_Dist` de MODIS son
  exactamente la serie cuantizada que D15 midió en `Distancia_km` de `latest.php` (0, 1, 1,41, 2,
  2,24, 3,16, 3,61, 9,49...). Eso hace SOSPECHA fuerte que la distancia publicada sea `Max_Dist`, no la
  del píxel más caliente; no se pudo cruzar pasada a pasada (OSF termina en 2025). Cruce empírico en el
  consolidado: de 360 FALSO_POSITIVO nocturnos, 47 tuvieron la misma noche una ALERTA dentro del radio
  en otro sensor (MODIS 3 de 10, VIIRS750 4 de 17, VIIRS375 40 de 333), y 84 VIIRS375 tuvieron ALERTA en
  otra pasada del mismo sensor: el cráter estaba activo mientras esa pasada se etiquetaba "lejano".
  Control: 326 de 48.360 filas OSF tienen píxel más caliente a más de 0,5 km por fuera de `Max_Dist`
  (0,7 %, atribuible a `Volc_LAT/LON` con 3 decimales); no invalida la conclusión.
- **CÓMO SE VE EN EL DASHBOARD** Invisible: FALSO_POSITIVO se excluye. Se ve en el banco: usar
  FALSO_POSITIVO como "el cráter no tenía nada" mete negativos falsos; usar su VRP como "magnitud del
  foco lejano" mete el cráter en la suma.
- **CÓMO REPRODUCIRLO** `python 05_osf_una_fila_por_pasada.py --remoto <dir>`; leer el DOCX con `markitdown`.
- **CONFIANZA** CONFIRMADO (una fila por pasada, VRP integrado, LAT/LON del más caliente, `Max_Dist` al más lejano, en el esquema y en los datos OSF); SOSPECHA (que `Distance km` de `latest.php` sea `Max_Dist`).
- **GRAVEDAD 3**

### H205. Los "falsos positivos de MODIS en otros volcanes" son pocos y casi todos diurnos; el grueso de FALSO_POSITIVO es VIIRS375 y no trae posición
- **ARCHIVO:LÍNEA** `scraper.py:151-152`. `SCRIPT:SALIDA` `03_falsos_positivos.py`.
- **QUÉ PASA** 852 FALSO_POSITIVO en el consolidado (2026-01-15 a 2026-09-14): VIIRS375 733, VIIRS750
  79, **MODIS 40** (10 nocturnos). Por volcán, MODIS: Llaima 14, Copahue 5, Villarrica 5, Chaitén 4,
  Isluga 3, Tupungatito 3, y 1 a 2 en el resto; distancia mediana 24,5 km (mín 6,4, máx 31,9), o sea
  el borde de la grilla de 51 km de MIROVA; VRP mediano 3,7 MW, máx 96 MW (Llaima). Diurnos: 492 de
  852. Ninguna fila trae lat/lon ni acimut: sólo VRP y distancia (columnas del CSV: 13). Los
  FALSO_POSITIVO_OCR son 91 (VIIRS375 86), 74 de confianza baja, 54 diurnos, 19 con distancia 0 ("no
  medida"), y llevan clase de intensidad en vez de NULO (eje 1 H110).
- **CÓMO SE VE EN EL DASHBOARD** Invisible.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2** (informativo para el banco: no hay un problema "MODIS" separado; hay un problema "foco lejano" que es VIIRS375 y diurno en su mayoría).

### H206. Copias congeladas en uso o al alcance que hoy engañan
- **ARCHIVO:LÍNEA** `04_local_vs_remoto.py` (salida completa en `salida_04_local_vs_remoto.txt`).
- **QUÉ PASA**
  1. Checkout local `Automatizacion web\Mirova-v1`: HEAD `131245012a2` del 2026-03-28, con 10 archivos
     modificados sin commitear (workflows, `scraper.py`, `ocr_utils.py`...). Sus CSV terminan el
     2026-03-28; su `registro_vrp_ocr.csv` tiene 6 filas etiquetadas ALERTA que el remoto ya
     reclasificó a FALSO_POSITIVO_OCR; su `registro_Peteroa.csv` (1 fila) no existe en el remoto. Pero
     es la única copia con las notas OCR sin mojibake (H203) y contiene 177 filas del consolidado que el
     remoto perdió (H201). `scripts/rebuild_mirova_lascar.py:45` de VRP Chile apunta a este archivo por
     ruta absoluta; está marcado legacy y nadie lo llama.
  2. `Mirova-v1-codigo`: HEAD `f6a8139` del 2026-09-13, código al día, sin `monitoreo_satelital/`.
  3. VRP Chile `data/mirova_reference/registro_vrp_ocr.csv`: congelado 2026-03-28 (LEEME lo declara,
     guard `test_ground_truth_mismo_snapshot_s126.py`), y limpio de mojibake.
  4. VRP Chile `01_05_2026_registro_vrp_consolidado.csv`: fallback del frontend
     (`diario.html:195`, `comparacion.html:171`); tiene 170 filas (16 ALERTAS) que el remoto perdió.
  5. VRP Chile `mirova_v1_snapshot/registro_{Chaiten,Lascar,Tupungatito}.csv`: del 2026-04-26, no los
     lee ningún script (sólo docs).
  6. `latest_consolidado.csv` (raíz de VRP Chile): idéntico al remoto en las 37.341 llaves comunes,
     133 filas detrás (cron horario): sano, pero hereda H201.
  7. Snapshot semanal `mirova_v1_snapshot/registro_vrp_{consolidado,ocr}.csv`: del 2026-09-07,
     idénticos al remoto en sus llaves (0 diferencias de tipo o VRP), 1.219 y 24 filas detrás: sano,
     hereda H201 y H203.
- **CONFIANZA** CONFIRMADO. **GRAVEDAD 2**

### H207. Lo que el OCR clasificó antes del 2026-06-11 usó una geometría equivocada y distancia no medida
- **ARCHIVO:LÍNEA** `tasks/AUDITORIA_OCR_EMPIRICA_2026-06.md` §B (B1 Tupungatito 257 px = 5,1 km; B2 eje en 335 en vez de 295, distancias de las notas ~2×); README changelog V5.1 ("fórmula de distancia FASE 1 estaba invertida"); `scraper_ocr.py:364-368` (distancia no medida = 0,0 hasta V29.2). `SCRIPT:SALIDA` `02_completitud_mensual.py` (`Distancia_km == 0`: 526 de 571 filas hasta mayo, 79 de 163 en junio, 5 de 227 desde julio).
- **QUÉ PASA** El dentro/fuera del OCR de enero a mayo se decidió en píxeles fijos con dos errores
  conocidos; el remoto corrigió 72 filas (49 a mano `Editado = SI`, 23 `AUTO`) pero sólo las que
  `latest.php` también tenía como FALSO_POSITIVO. Las 543 ALERTA_OCR que sólo existen en el OCR no
  tienen contra qué reconciliarse.
- **CONFIANZA** CONFIRMADO (código, docs del repo y conteos). **GRAVEDAD 2** para un banco que use el OCR de enero a mayo como positivo "dentro del radio".

### H208. Artefactos muertos o huérfanos en el remoto
- `graficos_tendencia/` (10 PNG, último commit 2026-01-15); `dashboard_interactivo.html` (0 referencias en el remoto; sólo carga Plotly de CDN); `backfill_geometria_v30.py` subido el 2026-09-13 sin rastro de haberse aplicado (0 filas con geometría antes de agosto). **CONFIRMADO. GRAVEDAD 1.**

## 4. Qué usar para el banco de prueba de VRP Chile

Unidad de decisión: la noche de volcán por sensor (eje 1 §3). Fecha inicial y archivo por uso:

| Uso | Archivo | Filtro | Desde cuándo | NO usar |
|---|---|---|---|---|
| Positivos con distancia y VRP fiables | consolidado (remoto o `latest_consolidado.csv`), `Tipo == ALERTA_TERMICA`, recalculando el tipo desde VRP y distancia con el límite vigente | nocturno | **2026-01-16** (tipos); MODIS y VIIRS con cobertura ≥ 95 % desde **2026-02-01**, ≥ 99 % desde **2026-03-01**; Tupungatito desde **2026-02-23** | `Clasificacion Mirova`; `positivos.csv` (es lo mismo pero sin RUTINA ni FP para condicionar) |
| Positivos adicionales (gránulos que la tabla no listó) | OCR `ALERTA_TERMICA_OCR`, `Confianza == alta`, excluyendo los 9 grupos de estrella compartida (eje 1 H108) | nocturno | **2026-03-01** (V21 estable); con distancia medida sólo desde **2026-06-13**; en VIIRS750 y MODIS con ±1 MW | enero y febrero del OCR (7 versiones, 12 métodos); `Distancia_km` de antes de junio (0 = no medida); las notas de antes del 13-jun como distancia (H203 y H207) |
| Reponer las 31 ALERTAS perdidas (H201) | unión de `cons_2026-08-22` (historia del remoto), backup local del 08-abr y `01_05_2026_*.csv` | por llave, renombrando `Peteroa` | | tratar el remoto de hoy como completo para enero a agosto |
| Negativo condicionado | consolidado `RUTINA` nocturna sin ALERTA, FP ni ALERTA_OCR esa noche y sensor, más cobertura propia (eje 1 §3) | | igual que positivos | FALSO_POSITIVO como negativo del cráter (H204); RUTINA de antes del 2026-01-16 |
| Sin información | noche sin fila; sólo FALSO_POSITIVO; diurnas; gránulos sólo en imagen | | | |
| Magnitud de referencia | VRP del consolidado; en llaves compartidas gana el consolidado (61 de 327 difieren por truncado) | | | VRP de una fila FALSO_POSITIVO como "magnitud del foco lejano" (H204: puede incluir el cráter); VRP OCR de VIIRS750 y MODIS sin la banda ±1 |
| Artefactos conocidos | `anotaciones.csv` (1 fila: Láscar 2026-06-15 760,6 MW) y la marca diurna del OCR (`Confianza == media` con nota "CANDIDATO A ARTEFACTO", desde ago-2026) | | | |

Lo que el maestro publicable y el positivos aportan que consolidado + OCR no: **nada**. Son
derivados exactos (§1). Sirven sólo como atajo (el maestro ya trae la unión con `Origen_Dato`), pero
heredan cualquier defecto de las fuentes y descartan RUTINA y FALSO_POSITIVO, que el banco necesita
para condicionar. El `registro_vrp_consolidado al 08042026.csv` sí aporta: 244 filas que el remoto
perdió, 17 ALERTAS.

Supuestos usados: noche = hora solar de Chile antes de las 06 o desde las 18 (lon −70,5°); "cadencia
madura" = media de junio a agosto de 2026 del propio consolidado, no un número de paper.

## 5. VERIFICADO LIMPIO

| Qué | Resultado | Cómo se confirma |
|---|---|---|
| positivos = consolidado[ALERTA_TERMICA] | 1.462 = 1.462, 0 diferencias | `01_mapa_archivos.py`, derivación 1 (control: quitar 1 fila da 1) |
| maestro publicable = dedup(consolidado + OCR) con los 3 filtros del merger | 2.005 = 2.005, 0 diferencias; en las 326 llaves "ambos" gana el consolidado | derivación 2 |
| `registro_<Volcan>.csv` = maestro[Volcan], los 11 | 11 de 11 OK, suma 2.005 | derivación 3 |
| Duplicados por llave en los 4 archivos y los 11 por volcán | 0 en todos | `01_mapa_archivos.py` |
| Nombres de volcán en el remoto | 11 canónicos, 0 `Peteroa` en los 4 CSV | idem |
| `latest_consolidado.csv` de VRP Chile contra el remoto | 0 llaves propias, 0 tipos o VRP distintos, 133 filas detrás (cron 1 h) | `04_local_vs_remoto.py` (d) |
| Snapshot semanal de VRP Chile contra el remoto | 0 diferencias en 36.255 y 937 llaves comunes | (c) |
| `data/mirova/*.json` regenerados | mtime 2026-09-13 20:39, commit `546504209` 23:29 UTC | `ls`, `git log` |
| Bitácora sin huecos | 0 huecos > 6 h entre 2026-01-11 02:34 y 2026-09-14 08:51 (218.018 líneas) | bloque python en la sesión |
| Cobertura nocturna del consolidado desde marzo | 99,1 a 100 % en los 3 sensores | `02_completitud_mensual.py` (control: borrar 50 % de junio baja 330 → 260) |
| OCR sin reprocesos retroactivos | matriz mes satélite × mes proceso diagonal salvo 5 filas | idem |
| Ninguna pérdida nueva del consolidado desde el 2026-08-29 | versiones 08-29, 09-03, 09-06 y snapshot 09-07: 0 llaves ausentes en el remoto de hoy | inventario histórico |
| OSF v2.5: una fila por pasada | 0 duplicados por (timeUTC, IDvolc, Satellite, Resolution) en 48.360 filas de Chile | `05_osf_una_fila_por_pasada.py` |
| Frescura del remoto | último commit 2026-09-14 12:01 UTC; el consolidado creció entre dos descargas de la sesión (5.623.426 → 5.628.367 bytes) | `gh api commits`, `ls` |
| Radio del scraper igual al de VRP Chile | ya verificado en el eje 1; no se repitió | |

Scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\bases_mirova_v1\`
(`comun.py`, `00_descargar_remoto.py`, `01_mapa_archivos.py` a `08_bisect_commit_perdida.py`,
`pipeline_loader_shim.py`, `salida_*.txt`). Los CSV del remoto y sus 18 versiones históricas quedaron
en el scratchpad de la sesión, no en el repo; `00_descargar_remoto.py` los vuelve a bajar y deja el
sha en `remoto_meta.txt`. Todos los scripts aceptan `--remoto DIR` y por defecto usan el snapshot
semanal del repo.
