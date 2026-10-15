# Horas de MIROVA y conversiones de hora del scraper Mirova-v1

Auditoría de sólo lectura, 2026-10-15, pedida por Nicolás. Se guarda aquí con sus scripts y salidas chicas; no se
copian los insumos grandes (`cons.csv`, `ocr.csv` y `commits_*.csv`, que `s2_listar_commits.py` regenera desde la API
de GitHub) ni las copias del código de Mirova-v1 (`src/`). Carpeta original:
`C:\Users\nmend\AppData\Local\Temp\claude\auditoria_horas\`.
Código de Mirova-v1 leído por la API de GitHub en el commit `9a51564bf6` (copias en `...\auditoria_horas\src\`).
CSV: copia de hoy (`cons.csv`, 42.722 filas, pasadas del 2026-01-10 al 2026-10-15; `ocr.csv`, 1.061 filas).

Scripts y salidas (cada número de este informe sale de una de ellas):

| script | salida | qué mide |
|---|---|---|
| `s1_hora_chile.py` | `s1_salida.txt` | `Fecha_Captura_Chile` y `timestamp` contra la hora oficial, por mes |
| `s2_listar_commits.py` | `commits_verano.csv`, `commits_invierno.csv`, `commits_inv_b.csv` | hora UTC de cada commit que tocó el consolidado |
| `s3_primera_aparicion.py` | `s3_salida.txt`, `s3_primera_aparicion.csv` | reloj independiente: primera aparición de cada fila, commit por commit |
| `s4_tabla_horas.py` | `s4_salida.txt`, `s4_tabla.csv` | tabla de horas de pasada y atraso de publicación |
| `s5_ocr_y_ambiguas.py` | `s5_salida.txt` | zona del OCR, horas ambiguas, cruce de cambio de horario |
| `s6_s114_impacto.py` | `s6_salida.txt` | efecto del corte día/noche de un experimento de S114 |

## 1. Tabla de horas (lo que pidió Nicolás)

Ventanas: **verano** = pasadas del 2026-09-07 al 2026-10-14 (UTC−3); **invierno** = 2026-07-26 al
2026-09-06 (UTC−4). Horas = mediana de las pasadas (entre paréntesis, percentiles 10 a 90). El atraso
se mide desde la pasada hasta el **commit** en que la pasada aparece por primera vez en el repo
(primera fila de cualquier volcán de esa pasada). Fuente: `s4_salida.txt`.

Cómo se sabe el satélite: de noche, cruzando la hora de la pasada con los records de VRP Chile
(`origin/main`, `data/mirova_equivalent/`) del mismo tipo de sensor a ±4 min. De día VRP Chile no
procesa, así que MODIS se separa por hora (Terra antes de las 16 UTC, Aqua después; es inferencia, no
cruce) y **VIIRS diurno queda con las tres plataformas mezcladas (SIN SEPARAR)**.

### Noche

| Sensor | Satélite | Pasada UTC | Chile verano | Chile invierno | Atraso mediana / p90 (verano) | Atraso mediana / p90 (invierno) | Queda publicada (hora Chile, mediana) verano / invierno |
|---|---|---|---|---|---|---|---|
| MODIS | Terra | 01:37 (00:55 a 02:30) | 22:37 | 21:43 | 1,9 h / 3,5 h | 2,3 h / 2,9 h | 00:51 / 23:51 |
| MODIS | Aqua | 08:00 (07:15 a 08:40) | 05:00 | 03:50 | 2,4 h / 3,1 h | 2,5 h / 3,0 h | 07:21 / 06:21 |
| VIIRS 375 | NOAA-21 | 05:42 (04:38 a 06:36) | 02:42 | 01:42 | 3,0 h / 4,5 h | 3,1 h / 5,8 h | 05:46 / 04:51 |
| VIIRS 375 | NOAA-20 | 05:42 (04:48 a 06:42) | 02:42 | 01:48 | 3,2 h / 5,1 h | 3,2 h / 5,6 h | 06:13 / 05:06 |
| VIIRS 375 | Suomi NPP | 06:30 (05:16 a 06:56) | 03:30 | 02:36 | 3,6 h / 5,9 h | 3,8 h / 8,5 h | 07:06 / 06:21 |
| VIIRS 750 | NOAA-21 | 05:42 (04:42 a 06:36) | 02:42 | 01:42 | 2,8 h / 4,1 h | 3,1 h / 5,6 h | 05:28 / 04:58 |
| VIIRS 750 | NOAA-20 | 05:42 (04:48 a 06:42) | 02:42 | 01:48 | 3,2 h / 5,2 h | 3,3 h / 5,0 h | 06:05 / 05:06 |
| VIIRS 750 | Suomi NPP | 06:06 (05:12 a 06:54) | 03:06 | 02:30 | 3,4 h / 5,9 h | 3,6 h / 6,4 h | 06:50 / 06:06 |

### Día

| Sensor | Satélite | Pasada UTC | Chile verano | Chile invierno | Atraso mediana / p90 (verano) | Atraso mediana / p90 (invierno) | Queda publicada verano / invierno |
|---|---|---|---|---|---|---|---|
| MODIS | Terra (por hora) | 13:00 (12:15 a 13:45) | 10:00 | 09:00 | 1,9 h / 3,4 h | 1,7 h / 2,3 h | 11:51 / 10:36 |
| MODIS | Aqua (por hora) | 20:40 (19:55 a 21:40) | 17:40 | 16:37 | 2,4 h / 4,1 h | 2,4 h / 3,8 h | 20:06 / 19:20 |
| VIIRS 375 | las tres, SIN SEPARAR | 18:42 (17:30 a 19:48) | 15:42 | 14:42 | 4,3 h / 7,4 h | 4,2 h / 6,2 h | 20:01 / 18:50 |
| VIIRS 750 | las tres, SIN SEPARAR | 18:48 (17:36 a 19:48) | 15:48 | 14:42 | 3,9 h / 6,4 h | 4,3 h / 6,0 h | 19:35 / 18:51 |

Lectura geológica: la hora UTC de cada satélite es la misma todo el año (órbitas heliosincrónicas);
lo único que cambia entre verano e invierno es la hora de Chile, una hora. Las noches útiles para MIR
se publican de madrugada: lo nocturno de VIIRS está en el repo entre las 05:00 y las 07:00 hora de
Chile (verano), MODIS Terra cerca de medianoche y MODIS Aqua cerca de las 07:00.

**Reparto del atraso entre MIROVA y el scraper.** El scraper (`main.yml`) no tiene `schedule`: sólo
`workflow_dispatch` (`.github/workflows/main.yml:3-4`), y algo externo lo dispara cada 5 minutos
(las últimas 40 corridas, todas `workflow_dispatch`, salen a :x0:1x y :x5:0x UTC). Medido:

- separación entre commits del scraper: mediana 5,0 min, p90 5,2 a 5,4 min (`s4_salida.txt`); huecos
  de más de 15 min: 16 en la ventana de verano (máximo 50 min) y 36 en la de invierno (máximo 237 min);
- entre la lectura de `latest.php` (que fija `Fecha_Proceso_GitHub`) y el commit: mediana 0,05 min,
  máximo 1,4 min (`s4_salida.txt`); y entre el disparo del job y esa lectura, unos 50 s (corridas
  12:20:10 UTC disparada, `Ultima_Actualizacion` 12:20:58 UTC);
- espera de una fila en `latest.php` antes de ser leída: como máximo el intervalo entre el commit
  anterior y el de su primera aparición, mediana 5,0 min y p90 5,2 a 5,7 min en todas las filas de la
  tabla (`s4_tabla.csv`, columnas `espera_scraper_max_*`).

Conclusión: el scraper aporta entre 1 y 6 minutos (salvo los huecos raros); **el atraso de 2 a 4 horas
es de MIROVA**. Lo que se separa es una cota: la hora exacta en que MIROVA publicó queda dentro de los
5 minutos previos a la primera aparición.

Ejemplo de la pregunta (Nevados de Chillán VIIRS 750, pasada 06:00:02 UTC): primera aparición en el
commit de 10:21:08 UTC, con `Fecha_Proceso_GitHub` 07:20:58 = 10:20:58 UTC, o sea **4 h 21 min** de
atraso. Su `Ultima_Actualizacion` 09:20:58 = 12:20:58 UTC coincide con el commit de 12:21:01 UTC.

## 2. Resultados de la auditoría de conversiones

### 2.1 `Fecha_Captura_Chile`: correcta en todas las filas

- Código: `scraper.py:199-201` y `scraper_ocr.py:531-533` hacen
  `dt_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Santiago'))`, o sea **zona
  `America/Santiago`**, no desfase fijo. La versión de enero (`0d305b9307`, l. 35) llamaba a
  `astimezone` sobre una fecha sin zona, lo que sólo es correcto si el runner está en UTC (lo está en
  GitHub Actions).
- Horario oficial sacado de tzdata 2026a con `zoneinfo` (`s1_salida.txt`): cambia a UTC−4 el
  2025-04-06 03:00 UTC y el **2026-04-05 03:00 UTC**; vuelve a UTC−3 el 2025-09-07 04:00 UTC y el
  **2026-09-06 04:00 UTC** (también 2024-04-07 y 2024-09-08, 2027-04-04).
- Consolidado: **0 de 42.722** filas con la hora de Chile mal; 17.428 con −3 y 25.294 con −4, cada una
  en su mes correcto (abril: 553 filas −3 hasta el día 5 y 4.342 −4; septiembre: 855 −4 y 4.571 −3).
  OCR: **0 de 1.061** mal. En ±36 h de los dos cambios de 2026 (453 y 541 filas del consolidado) el
  desfase pasa justo en el instante oficial (`s1_salida.txt`).

### 2.2 `timestamp`: es el epoch de `Fecha_Satelite_UTC` en todas las filas

42.722 de 42.722 y 1.061 de 1.061 coinciden exactamente (`s1_salida.txt`). Hoy `scraper.py:150`
lo calcula con UTC explícito; antes (`2d025de0a8`, l. 145) usaba la zona del sistema, correcto sólo
en CI. Ninguna fila quedó afectada.

### 2.3 `Fecha_Proceso_GitHub` y `Ultima_Actualizacion`: hora de Chile, verificada contra commits

- Código: las dos salen de `ahora_cl = datetime.now(pytz.timezone('America/Santiago'))`
  (`scraper.py:117`; OCR `scraper_ocr.py:405`). `Fecha_Proceso_GitHub` = hora de la corrida que vio la
  fila **por primera vez** y no se vuelve a tocar (`scraper.py:183-188`, 209). `Ultima_Actualizacion`
  = hora de la **última corrida que la encontró en `latest.php`** (`scraper.py:210`, se reescribe en
  cada corrida).
- Reloj independiente (`s3_salida.txt`): 859 commits del 2026-10-10 al 2026-10-12, archivo leído en
  cada uno. 473 filas con primera aparición observada. Leyendo `Fecha_Proceso_GitHub` como
  `America/Santiago`, el commit llega 0,0 a 0,3 min después en **473 de 473**; como UTC, 180 min de
  diferencia (0 de 473); como −4 fijo, −60 min (0 de 473). Ninguna fila cambió su
  `Fecha_Proceso_GitHub` entre commits. `Ultima_Actualizacion` coincide con el commit en que toma su
  valor final (0,0 a 0,1 min). OCR (`s5_salida.txt`): 95 de 95 valores desde el 2026-09-15 caen 0,8
  min (mediana) antes de un commit del OCR leídos como Santiago.
- **Por qué van 2 h de diferencia en el ejemplo**: no es un desfase de zona. `latest.php` muestra sólo
  la última pasada de cada volcán y sensor (33 filas = 11 volcanes × 3 sensores; 33 filas comparten la
  última `Ultima_Actualizacion`). La fila del 06:00:02 entró a las 07:20:58 y siguió siendo la más
  reciente hasta la corrida de las 09:20:58, la última antes de bajar el CSV. La fila de Llaima de la
  misma pasada tiene `Ultima_Actualizacion` 08:46:08 porque a las 08:51 llegó otra pasada de VIIRS 375
  que la reemplazó en `latest.php`. Una fila se reescribió hasta 226 veces (s3).

## 3. Defectos encontrados (sólo propuesta, nada se cambió)

**D1. Horas locales sin desfase: ambiguas una hora cada abril.** `Fecha_Proceso_GitHub`,
`Ultima_Actualizacion` y `Fecha_Captura_Chile` se guardan como texto local sin zona
(`scraper.py:117`, `199-201`, `209-210`; `scraper_ocr.py:405`, `531-533`, `543-544`). La hora del
2026-04-04 23:00 a 23:59 existió dos veces. Afecta (`s5_salida.txt`): consolidado, 10 filas de
`Fecha_Proceso_GitHub`, 11 de `Ultima_Actualizacion` y 2 de `Fecha_Captura_Chile` (pasada 03:05 UTC,
escrita 23:05); OCR, 0. Además 8 filas tienen pasada y proceso a distinto lado de un cambio de hora, y
una resta de dos horas locales sin zona se equivoca ahí en 1 h. Hoy la conversión no está mal; el
problema es que el texto no se puede volver a UTC sin adivinar. Propuesta: agregar
`Fecha_Proceso_UTC` y `Ultima_Actualizacion_UTC` (o escribir las locales con `%z`, ej.
`2026-10-15 07:20:58-03:00`), sin borrar las columnas actuales.

**D2. Mezcla de zonas dentro del mismo repo.** El CSV de rechazos de cabecera usa UTC
(`scraper_ocr.py:116`, `195`) y la marca de reconciliación también (`reconciliar_latest.py:60`), mientras
las columnas del CSV y la bitácora (`scraper.py:37`) van en hora de Chile sin decirlo. No hay fila mal,
pero el nombre `Fecha_Proceso_GitHub` sugiere un reloj de GitHub (UTC) y no lo es. Propuesta: documentar
la zona en el README o renombrar en la cabecera (`..._CL`), coordinando con los lectores.

**D3. 104 filas sin `Fecha_Proceso_GitHub` (y 96 sin `Ultima_Actualizacion`).** Todas con pasada del
2026-01-10 19:06 al 2026-01-12 12:25 UTC (`s5_salida.txt` y verificación en consola), antes de que la
columna existiera. No es error de conversión; sólo impide medir su atraso. Sin corrección necesaria.

**D4. El scraper no tiene cron propio.** `main.yml:3-4` sólo declara `workflow_dispatch`; la cadencia de
5 min depende de un disparador externo que no está en el repo (cuál es: SIN VERIFICAR). Huecos de hasta
237 min en invierno (36 de más de 15 min). Como `latest.php` sólo guarda la última pasada por volcán y
sensor, un hueco largo puede perder una pasada que fue reemplazada mientras tanto (cuántas: SIN
VERIFICAR). Propuesta: un `schedule` de respaldo en `main.yml` o un registro de dónde vive el disparador.

## 4. Uso de `Fecha_Captura_Chile` en VRP Chile

Búsqueda en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile` (`pipeline/`, `scripts/`,
`frontend/`, `experiments/`, `tests/`):

- **`pipeline/mirova_csv_loader.py:195`** la copia a `fecha_local`, pero ningún archivo `.py`, `.html` ni
  `.js` lee `fecha_local`. Sin efecto. Las claves y cruces usan `timestamp` y `Fecha_Satelite_UTC`.
- **`scripts/referencia_mirova_unificada.py:73,100`** desduplica por la `Ultima_Actualizacion` «más
  reciente» comparando el texto local. Sólo puede equivocarse dentro de la hora ambigua de D1 (11 filas).
- **`experiments/_s114_audit/viirs375_deepdive.py:16,61,71`** dice que la hora local es «UTC−4» (falso en
  verano) y llama diurna sólo a la hora local 10 a 15. Pasadas diurnas VIIRS 375 a las 16 o 17 locales
  quedan como nocturnas: 791 filas del consolidado hasta el 2026-06-20 (`s6_salida.txt`), **ninguna
  alerta**; como ese script usa el día/noche sólo sobre alertas, sus conclusiones no cambian.
- **`experiments/_s86_f_precision_gap/script_A.py:214-220`** hace histogramas por hora local, mezclando
  −3 y −4 (corrimiento de 1 h entre meses). Sólo descriptivo.
- **`experiments/_s139_audit/eje1/medir_consolidado.py:128`** y
  **`experiments/_s146_auditoria/frente_I/i01_referencia.py:45`** restan `Fecha_Proceso_GitHub` menos
  `Fecha_Captura_Chile`, las dos locales: correcto salvo las 8 filas de D1 que cruzan un cambio (1 h).
- **`experiments/_s86_audit_profundo/script_F.py:164`** acepta diferencias de 3 o 4 h: correcto.
  **`experiments/_s150_latencia/pair.py:17`** localiza en `America/Santiago` y descarta lo ambiguo:
  correcto.

Recomendación: que todo análisis nuevo use `timestamp` o `Fecha_Satelite_UTC`, y si necesita la hora de
proceso, la pase a UTC con `America/Santiago` (como `pair.py`), nunca con un −3 o −4 fijo.

## 5. Límites

- La plataforma de día de MODIS es inferida por hora, no cruzada; la de VIIRS diurno no se separó.
- La ventana de invierno incluye las pasadas del 2026-09-06 posteriores a las 04:00 UTC, que ya son
  UTC−3, convertidas con −4 en la tabla (un día de 42; efecto despreciable en medianas).
- El atraso por commit de las 6 semanas usa `Fecha_Proceso_GitHub` pasado a UTC y ajustado al commit
  siguiente; esa equivalencia se comprobó fila a fila sólo en 3 días (473 de 473), y en las 6 semanas
  la distancia al commit fue de mediana 0,05 min y máximo 1,4 min.
