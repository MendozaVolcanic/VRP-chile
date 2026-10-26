# Vuelta 2: la alerta protegida de Chillán del 2026-10-12 05:18 UTC sin record en el A/B de D25

Fecha de la medición: 2026-10-24 (consultas CMR anónimas hechas hoy). Carpeta:
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta2\record_faltante\`

## Resumen (cinco líneas)

1. La alerta es la pasada de **NOAA-21 de las 05:18 UTC** (fila del consolidado `latest.php`, no del OCR): VIIRS 750 con 8,44 MW a 1,68 km, clase Bajo, y la misma pasada en VIIRS 375 con 7,31 MW. Producción **sí** la tiene (375: 2,882 MW, 750: 3,46 MW, los dos `summit`), procesada el 12-oct con el gránulo original.
2. Causa: **no bajamos el gránulo porque la búsqueda volvió vacía**. NASA reprocesó Suomi NPP y NOAA-21 del 12-oct el 19-oct; cuando el job del A/B buscó (2026-10-21 04:50 UTC), CMR no devolvió ningún gránulo Standard de esas dos plataformas para el 12 y LANCE NRT ya no tenía el día (n=0). No es OCR, ni otra plataforma u hora, ni descarte del procesador.
3. El hueco pasó **en silencio** por cuatro filtros: la búsqueda vacía no se registra como falla, el job imprimió «Cobertura: completa», la cobertura del A/B compara brazos entre sí, y el evaluador sólo revisa protegidas que ya tienen record en algún brazo (y tolera 5 % de pasadas faltantes por volcán y sensor; Chillán pierde menos de 1 %).
4. Barrido de V1 (86 protegidas, 72 VIIRS): **9 VIIRS sin record en los tres brazos, todas de Chillán**; 2 son esta pasada (375 y 750) y 7 son del 18-oct, día que D-29 ya excluye. Por causa: 9 de 9 «la búsqueda en CMR no devolvió el gránulo»; 0 por descarte, 0 por pareo de hora o plataforma, 0 por OCR.
5. El 12-oct **no está en D-29** y a los tres brazos les faltan ese día 44 pasadas que producción tiene (11 volcanes, NOAA-21 y Suomi NPP, 375 y 750), 7 de ellas con alerta de MIROVA; el evaluador de V1 dijo igual «cobertura pareja: OK».

## 1. La fila de MIROVA

Referencia congelada de V1 (`C:\vrp-trabajo\s159-evaluador\experiments\_s157_prereg_d25\_congelado_v1\`, Mirova-v1@35a5ea86, MANIFIESTO del 2026-10-20 10:29 UTC):

- `registro_vrp_consolidado.csv:1129`: `2026-10-12 05:18:02, Nevados de Chillan, VIIRS, 8.44, 1.68, ALERTA_TERMICA, Bajo` (canal CONS).
- `registro_vrp_consolidado.csv:1125`: misma hora, `VIIRS375, 7.31, 0.84, ALERTA_TERMICA, Bajo`.
- `registro_vrp_ocr.csv:57`: la misma pasada por OCR, `VIIRS, 8.0, 1.76, ALERTA_TERMICA_OCR, Bajo`, método `roi_temporal_v26`, «geometría medida», confianza alta. Concuerda con el consolidado, así que **no** es el caso A119 (imagen de otra pasada) ni una fila `ALERTA_SIN_GEOMETRIA_OCR`.
- El CSV de MIROVA no trae plataforma. La identifico por la hora: CMR tiene `VJ202MOD.A2026285.0518...` (NOAA-21) que contiene el punto del cráter (consulta `point=-71.38,-36.86`, `cmr/VJ202MOD_2.1.json`), y producción tiene el record `VIIRS_NOAA21_750` a las 05:18. Las otras pasadas nocturnas de esa noche son NOAA-20 04:36 y 06:12 y Suomi NPP 05:54 (orden y desfase de -18 min/día contra el 11-oct, que sí está en los brazos).
- Esa misma noche hay otra alerta no protegida que también falta: Suomi NPP 05:54 (375: 0,85 MW; 750: 0,40 MW; `consolidado:1105` y `:1108`).

## 2. Qué records hay esa noche

| fuente | 2026-10-12, pasadas VIIRS de Chillán |
|---|---|
| brazos K, G y D del A/B (`d25\V1\_s157_ab_d25_k_{control,gemelo,on}\NevadosDeChillan.json`) | sólo NOAA-20: 04:36 (375), 06:12 (375 y 750), todas en 0. **Ni NOAA-21 ni Suomi NPP** |
| producción (`origin/main` 1f7ebfc9e, `data/mirova_equivalent/NevadosDeChillan.json`) | NOAA-20 04:36 y 06:12; **NOAA-21 05:18**: 375 `VJ202IMG.A2026285.0518.021.2026285102115.nc` pc.vrp 2,882 summit y 750 `VJ202MOD...2026285102115.nc` 3,46 summit; Suomi NPP 05:54: 375 0,39 summit, 750 0 |

Los records de producción del 12 tienen `first_processed_utc` 2026-10-12 09:18-09:19 UTC: los hizo el NRT ese día, con el sello de producción `2026285...` (12-oct).

## 3. Qué dicen los logs del A/B

Run 39530508296 (intento 2, commit 66961f65), job 119255786954 «reproc (NevadosDeChillan, 3, 2026-09-30, 2026-10-15)», arrancó 2026-10-21 04:47:44 UTC (`gh run view` y `gh api .../jobs/119255786954/logs`, copia en `gh\job_119255786954.log`). El brazo control hizo la búsqueda por ventana en vivo; G y D cargaron la caché de esa misma búsqueda (0 líneas `SEARCH_VENTANA` en sus logs), así que los tres heredaron la misma respuesta.

`d25\V1\logs\_s157_ab_d25_k_control_NevadosDeChillan.log`:

- l. 2619: `SEARCH_VENTANA [VIIRS_NOAA21_L1B] VJ202IMG v2.1 2026-09-30..2026-10-15 n=39`
- l. 2620: `SEARCH_VENTANA [VIIRS_NOAA21_L1B] VJ202IMG_NRT v2.1 2026-10-12..2026-10-13 n=0` (el respaldo NRT sólo se pide para los días que el Standard dejó vacíos: el 12 y el 13)
- l. 2659 y 2660: lo mismo en `VJ202MOD` (n=39) y `VJ202MOD_NRT` (n=0)
- l. 2589 y 2590: Suomi NPP `VNP02IMG` n=43 y `VNP02IMG_NRT 2026-10-12..2026-10-13 n=0`
- l. 3555: `SEARCH_DONE VIIRS_NOAA21 n_l1b=0`; l. 3567: `SEARCH_DONE VIIRS_NOAA21_750 n_l1b=0`; l. 3545 y 3557: Suomi NPP 375 y 750 en 0
- l. 3571: `Cobertura: completa (ninguna búsqueda ni descarga fallida).`
- Mismo patrón en `..._k_on_...log` l. 3483, 3495, 3499 y `..._k_gemelo_...log` l. 3483, 3495, 3499.

No hubo intento de descarga ni procesamiento de NOAA-21 ni Suomi NPP ese día: el procesador nunca recibió el gránulo. NOAA-20 sí se bajó y procesó (dos `DOWNLOAD_START` y tres líneas de VRP en el bloque del 12).

## 4. Qué gránulos existían (CMR, consultas anónimas de hoy)

Réplica exacta de la búsqueda del job (bbox de 25 km, `fetch.search_granules`; misma ventana):

`https://cmr.earthdata.nasa.gov/search/granules.umm_json?short_name=VJ202IMG&version=2.1&bounding_box=-71.60222522522523,-37.08822522522522,-71.15177477477476,-36.637774774774776&temporal=2026-09-30T00:00:00Z,2026-10-15T23:59:59Z&page_size=2000&sort_key=start_date`
(y lo mismo con `VJ202MOD`, `VNP02IMG`, `VNP02MOD`, `VJ102IMG`; salida en `cmr\ventana_0930_1015.json`).

| producto | hits hoy | insertados después del run | el run vio | faltan | cuáles |
|---|---|---|---|---|---|
| VJ202IMG (NOAA-21) | 45 | 3 (13-oct, el 22-oct) | 39 | 3 | los 3 del 12-oct |
| VNP02IMG (Suomi NPP) | 48 | 0 | 43 | 5 | 3 del 12-oct y 2 del 13-oct |
| VJ102IMG (NOAA-20) | 47 | 2 (13-oct, el 22-oct) | 45 | 0 | ninguno |

Los gránulos que el run no vio son justo los que hoy llevan sello de producción del **19-oct** (`VJ202IMG.A2026285.0518.021.2026292150831.nc`, `VNP02IMG.A2026285.0554.002.2026292155814.nc`): NASA reprocesó ese día. Los originales del 12 (`...2026285102115.nc`, `...2026285140512.nc`), que procesó producción, **ya no están** en CMR (consulta `readable_granule_name` dentro de su colección: 0 entradas). El NOAA-20 del 12 tiene sello del 16-oct y sí lo vio. El respaldo NRT (LANCE) da hoy 0 para el 12 en NOAA-21 y Suomi NPP (`cmr\VJ202IMG_NRT_2.1.json`, `cmr\VNP02IMG_NRT_2.1.json`).

Esto concuerda con lo que midió otra sesión el 2026-10-22 02:30 UTC (`origin/main:experiments/_s159/laads_rescate/INFORME.md` §0 y H1, no re-medido aquí): el 12-oct NASA reprocesó Suomi NPP y NOAA-21, LAADS borró el original y dejó el nuevo, y en ese momento CMR servía todavía la entrada vieja con enlace 404; LANCE ya había purgado el día. Un probe del 21 a las ~23:40 UTC vio 0 candidatos.

**Costo para el operador**: ninguno en el tablero (producción procesó el original a tiempo). El costo es para el A/B: una alerta protegida del volcán en erupción queda fuera de la evaluación de D25 sin que nada lo diga. Y un reproceso hoy bajaría el archivo reprocesado (`2026292...`), no el que procesó producción, así que para esa pasada «K igual a producción» no se puede dar por hecho.

## 5. Por qué nadie lo vio

1. `pipeline/fetch.py:1087-1088` en el commit del A/B (66961f65): `if not l1b_granules: continue`, sin registrar falla. Una búsqueda vacía es indistinguible de «no pasó el satélite». (En `origin/main` hoy, `fetch.py:1176-1181` cuenta la plataforma como `sin_granulos` desde S161 #897; si eso hubiera hecho saltar la cobertura del día 12 es SOSPECHA, leído y no ejecutado.)
2. `scripts/run_pipeline.py:449-450` (main): sin fallas imprime «Cobertura: completa». Así salió el día 12 en los tres brazos.
3. `d25\V1\cobertura.txt`: «COBERTURA PAREJA: los brazos y el control tienen exactamente las mismas pasadas». Un hueco común a los tres brazos no se ve comparando brazos entre sí.
4. Evaluador (`C:\vrp-trabajo\s159-evaluador\experiments\_s157_prereg_d25\evaluar_d25.py`, commit ded217af4):
   - l. 988 y 999 a 1001: las protegidas que revisa salen de `todas`, la unión de las claves de la tabla; la tabla se arma recorriendo **records** (`experiments\_s149_prereg_invierno\armar_tabla.py:37-43`). Una alerta sin record en ningún brazo no es clave de la tabla, así que «protegidas sin record en algún brazo» no puede encontrarla.
   - l. 1006-1007 con `MAX_FALTA_COBERTURA = 0.05` (l. 81): contra producción tolera 5 % por volcán y sensor. Chillán tiene 215 pasadas VIIRS 375 y 212 de 750 en producción fuera de los días D-29 (conteo sin filtro diurno) y le faltan 2 de cada una: menos de 1 %.
   - l. 74-79: D-29 excluye el 13, 17, 18, 19 y 20, no el 12.
   - Resultado: `lectura_s162\salidas\v1.log` l. 16, «cobertura pareja: OK».

## 6. Barrido de las protegidas de V1 en los once volcanes

Script `barrer_protegidas.py` (usa el cargador, el indexador, el pareo de ±120 s y `clase_mirova.alerta_protegida(lectura="A")` del evaluador, con las capas congeladas). Salida `protegidas_v1.json`.

- Protegidas (lectura A, 2026-08-29 a 2026-10-18): **86**; VIIRS **72**; MODIS 14 (los brazos tienen MODIS apagado, `SENSOR_MODIS: false` en `FLAGS_BRAZO`; fuera de alcance).
- VIIRS sin record en algún brazo: **9**, y en los 9 falta en los **tres** brazos y producción sí tiene record:

| pasada | D-29 | MIROVA (CONS) | producción (pc.vrp) |
|---|---|---|---|
| Chillán 375 2026-10-12 05:18 | no | 7,31 MW, 0,84 km | NOAA-21, 2,882 |
| Chillán 750 2026-10-12 05:18 | no | 8,44 MW, 1,68 km | NOAA-21, 3,46 |
| Chillán 375 2026-10-18 05:06 | sí | 21,25 | NOAA-21, 5,672 |
| Chillán 375 2026-10-18 06:00 | sí | 9,94 | NOAA-20, 7,196 |
| Chillán 375 2026-10-18 06:48 | sí | 25,79 | NOAA-21, 4,075 |
| Chillán 750 2026-10-18 05:06 | sí | 19,63 | NOAA-21, 8,102 |
| Chillán 750 2026-10-18 05:42 | sí | 20,87 | Suomi NPP, 14,028 |
| Chillán 750 2026-10-18 06:00 | sí | 18,98 | NOAA-20, 13,603 |
| Chillán 750 2026-10-18 06:48 | sí | 22,85 | NOAA-21, 2,841 |

Causa del 18-oct, del log de control (bloque del 2026-10-16, job 4): `VJ202IMG v2.1 2026-10-16..2026-10-18 n=7` y `VJ202IMG_NRT v2.1 2026-10-18..2026-10-18 n=0`, y lo mismo en Suomi NPP, NOAA-20 y en 750. Hoy CMR tiene 4 de NOAA-21 Standard del 18 (contando 10-16 + 10-17 da exactamente los 7 que vio el run) y también los NRT (`cmr\ventana_1016_1023.json`). Mismo mecanismo: CMR no devolvió el día.

**Conteo por causa (9 protegidas VIIRS sin record)**: la búsqueda en CMR no devolvió el gránulo, ni Standard ni NRT: **9**. Descarte del procesador: 0. Pareo de hora o plataforma: 0 (producción tiene record a la misma hora en los 9). Fila del OCR con hora o geometría de otra pasada: 0 (las 9 son filas CONS). Fuera de D-29: **2** (la misma pasada, en los dos sensores).

Tamaño del hueco del 12-oct (`hueco_vs_produccion.py`, salida `hueco_vs_produccion.json`): producción tiene 4.762 pasadas VIIRS nocturnas en V1 y K 4.610; K no tiene ninguna que producción no tenga. Las 152 que faltan son del 12 (44: NOAA-21 375 y 750, Suomi NPP 375 y 750, 11 cada una), del 13 (22, NOAA-20) y del 18 (86). De las 44 del 12, 42 tienen fila de MIROVA y 7 son alerta (`alertas_del_12.py`): Isluga 375 05:12 (0,31) y 05:48 (0,19), Isluga 750 05:48 (0,24), y las cuatro de Chillán (05:18 y 05:54 en los dos sensores). Sólo la de Chillán 05:18 es protegida.

## 7. SIN DATO y SOSPECHA

- **SIN DATO**: por qué CMR no devolvió a las 04:50 UTC del 21 las entradas `2026292...` del 12-oct, cuya `revision-date` dice 2026-10-19 15:30. Las fechas de CMR no sirven para reconstruir qué se veía en un momento pasado: los gránulos Standard del 18-oct tienen hoy `revision-date` del 18-oct, y sin embargo el run del 21 a las 05:11 no los vio y `laads_rescate` midió 0 el 22 a las 02:30. Que CMR reindexó después con las fechas originales es SOSPECHA.
- **SIN DATO**: qué habría hecho D25 (o K) con la pasada de las 05:18; no bajé ni procesé nada.
- **SIN DATO**: si el record de producción de las 05:18 se publica en el tablero (no corrí el predicado).
- **SOSPECHA**: que con el código de hoy (`fetch.py` de S161) el día 12 habría salido con cobertura no completa por NOAA-21 y Suomi NPP.
- Fuera de alcance, no revisado: las 14 protegidas MODIS de V1 y la ventana V2.

## 8. VERIFICADO LIMPIO

- Los tres brazos tienen exactamente las mismas 4.610 pasadas (`d25\V1\cobertura.json`); la falta es común, no de un brazo.
- K no tiene ninguna pasada VIIRS nocturna que producción no tenga (0 de 4.610).
- La fila protegida es del consolidado y la del OCR concuerda (VRP, distancia y geometría medida): no es error del OCR.
- La hora y la plataforma calzan: NOAA-21 05:18, igual en CMR, en producción y en MIROVA (05:18:02).
- NOAA-20 del 12-oct sí se buscó, bajó y procesó en los brazos; el problema es sólo de las dos plataformas reprocesadas.
- El 17-oct, que D-29 excluye, no tiene hueco en los brazos (86 records).
- No hubo `SEARCH_VENTANA_TRUNCADA`, `_ERR` ni `_OFF` en el log de Chillán, ni falla de descarga.
- No modifiqué el repositorio ni el worktree del evaluador (`git status` limpio en `C:\vrp-trabajo\s159-evaluador`; corrí sus módulos con `python -B`). En el repo principal hice `git fetch` (sólo actualiza `origin/main`, quedó en 1f7ebfc9e) y lecturas con `git show` y `gh` de sólo lectura. Sin credenciales de Earthdata.

## Archivos de esta carpeta

`barrer_protegidas.py`, `protegidas_v1.json`, `hueco_vs_produccion.py`, `hueco_vs_produccion.json`, `alertas_del_12.py`, `cmr\` (respuestas de CMR), `gh\job_119255786954.log`, `prod\` (copia de los JSON de producción en 1f7ebfc9e, `prod\SHA.txt`).
