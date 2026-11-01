# COB (S159, ola 1): pasadas que MIROVA tiene y nosotros no

Fecha del servidor al medir: 2026-10-21, 18:00 a 19:10 UTC (`date -u` y cabecera `Date` de `gh api`, regla A86). Carpeta de trabajo:
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob\`. No se tocó nada fuera de ella ni se hizo git. CMR se consultó sólo en su API pública
(sin credenciales, pausa de 1 s entre consultas, caché en `_cache_cmr2\`).

## 0. Resumen

La segunda ronda contó 411 de 2.934 pasadas del OSF v2.5 de 2025 (14 %) sin record nuestro y no midió la causa (R2-16). Medida la causa:

| causa | pasadas | % de las 411 | ¿es pérdida de recall por cobertura? |
|---|---|---|---|
| F: anteriores al 2025-02-15, el día en que parte nuestra serie. La ola P4 del backfill (2025-01-01 a 2025-02-15) nunca se ejecutó | 357 | 86,9 % | No es fallo de descarga. Es trabajo no hecho. CMR tiene el gránulo (55 de 55 muestreadas) |
| C: diurnas. 49 con Dayflag=1 de MIROVA (el sol está sobre el horizonte en el volcán) y 4 con Dayflag=0 de MIROVA pero con el sol a 12 a 33 grados sobre el horizonte; el filtro nocturno las descarta | 53 | 12,9 % | No. Es decisión de diseño (`ENABLE_DAYTIME_MODIS/VIIRS = False`) |
| A: CMR no tiene el gránulo (Lascar, Terra, 2025-07-15 02:15) | 1 | 0,2 % | Sí, una, y no es nuestra: NASA no lo sirve |
| B: CMR tiene L1B y GEO y no hay record nuestro | 0 | 0 % | Ninguna |
| D: L1B sin geolocalización (VB-1) | 0 | 0 % | Ninguna |

Dentro de la ventana en que nuestra serie existe (desde 2025-02-15), faltan 54 de 2.577 pasadas OSF (2,1 %) y, de las 2.528 nocturnas según
MIROVA, sólo 5, todas MODIS y ninguna VIIRS (0 de 2.263 pasadas nocturnas VIIRS). Cordón Caulle: sus 84 faltantes caen todas antes del 2025-02-15;
dentro de la ventana faltan 0 de 352. No hay efecto de `radius_km` ni de caja de búsqueda.

Con los últimos 45 días (VB-4): ninguno de los huecos de producción señalados es falla de descarga de nuestro lado que CMR pueda probar.
El 13-oct y el 20-oct coinciden con ausencia de gránulos en CMR; el 18 y 19-oct son al revés (producción tiene records y CMR hoy no tiene
nada). Detalle y límites en §5.

## 1. Reproducción del conteo (script propio)

`01_conteo_faltantes.py` -> `01_conteo_faltantes.txt`, `osf_pareo.csv`, `faltantes.csv`.

- Pregunta 1 (¿vería el defecto si estuviera roto?): el mapa Satélite/Resolución del OSF a sensor nuestro sale del dato (argmax de coincidencias)
  y se contrasta con el prefijo del nombre del gránulo de cada record (MOD, MYD, VNP, VJ1): 0 discrepancias en 65.544 records. Pregunta 2
  (¿distinguiría instrumento muerto?): `assert len(rec) > 0`; con los records sin cargar saldrían 2.934 de 2.934 sin par, no 411.
- Control positivo: las 2.523 pasadas pareadas dan dt = 0 exacto (mín 0, máx 0, 0 con dt distinto de 0): el OSF usa la hora de inicio del
  gránulo, la misma que `datetime_utc`.
- Ventana: filas OSF con `timeUTC` en 2025 (el archivo termina el 2025-12-31). Universo: 10 volcanes Tier A presentes en el OSF (Tupungatito no
  está), 2.934 filas, 2.880 con Dayflag=0 y 54 con Dayflag=1. Records nuestros: 65.544 en total, 34.440 en 2025. Sensores del OSF a sensor nuestro: (1,1000) Terra,
  (2,1000) Aqua, (3,375) SNPP, (3,750) SNPP_750, (4,375) NOAA20, (4,750) NOAA20_750. NOAA-21 no está en el OSF.
- Pareo: mismo volcán, misma plataforma y resolución, |dt| <= 10 min. Ningún vecino cae entre 10 y 30 min (histograma sin masa en esa banda),
  así que 10 y 30 min dan el mismo conteo: 2.523 pareadas, **411 sin par**. Reproduce el número de la segunda ronda.
- Causa a primera vista: la fecha. Ningún record nuestro existe antes del 2025-02-15 (primer record: 2025-02-15 01:40 UTC en los 11 Tier A,
  `05_huecos_historicos.txt`), y la mediana de |dt| al vecino más cercano de las 411 es de 20 días; ninguna tiene vecino a menos de 30 min.
  `docs/BACKFILL_PLAN_S120.md:25` define P4 como 2025-01-01 a 2025-02-15 y la línea 79 la deja sin marcar («P3 verificación -> P4 ... -> cierre backfill 2025»).

## 2. Clasificación

`02_clasificar_cmr.py` -> `02_clasificar_cmr.txt`, `clasificacion.csv`. Consultas puntuales a CMR (ventana de +-1 min alrededor de la hora OSF) con
la misma caja que `pipeline/fetch.py:751-753` (`lon/lat +- radius_km/111`, `radius_km = 25` en los 10 volcanes según `volcanoes.yaml`) y los short names de
`pipeline/fetch.py:187-225` (leídos a mano; réplica en `cmrpub.py`). Se consultó CMR para las 54 faltantes posteriores al 2025-02-15 (todas), 55
anteriores (muestra estratificada, 6 por volcán) y 30 controles. Elevación solar con `pipeline.fetch._solar_elevation`, la misma función del filtro
nocturno de producción (`fetch.py:997-1024`).

- Control positivo: 30 de 30 pasadas con record: CMR tiene L1B (30) y GEO (30), elevación < 0 (30), y el `producer_granule_id` de CMR
  coincide en plataforma y `AYYYYDDD.HHMM` con el `granule` del record (30 de 30). En las 2.523 cubiertas: 0 con Dayflag=0 y elevación >= 0, 0 con Dayflag=1 y elevación < 0.
- Control negativo: hora OSF + 180 min (sin pasada de esa plataforma): 0 de 10 con gránulo en CMR. El instrumento da vacío cuando debe.
- Límite: las 302 filas F restantes no tienen consulta CMR propia. Con 55 de 55 con L1B y GEO la cota superior (95 %) de
  gránulos F que CMR no sirva es ~5 %: no demuestra 357 de 357. La clase F se define por fecha, no por CMR; CMR sólo dice si recuperarla es posible.

Resultado (411): F 357 (352 con Dayflag=0, 5 con Dayflag=1), C 53, A 1, B 0, D 0.

- C: 49 con Dayflag=1 (elevación 28 a 78 grados; NASA marca DAY en los 49) y 4 con Dayflag=0 de MIROVA: Chaitén Aqua 2025-05-14 20:10 (1,27 MW), Copahue Terra
  2025-08-13 12:40 (1,53 MW), Villarrica Terra 2025-03-26 13:55 (14,39 MW; CMR no tiene ese gránulo) y 2025-04-07 13:35 (0,99 MW). En tres de las cuatro
  la bandera `day_night_flag` de CMR dice DAY. O sea que MIROVA etiquetó como nocturnas tres pasadas diurnas de Terra y Aqua.
- A: Lascar, Terra, 2025-07-15 02:15 UTC (1,10 MW en MIROVA). CMR Standard no tiene ese gránulo ni ningún otro de Terra sobre los 11 volcanes ese día
  (`11_cuatro_dias_dudosos.txt`), y nuestra serie tampoco tiene Terra ese día (`05_huecos_historicos.txt`). El hueco es de NASA. Cómo lo tuvo MIROVA queda sin explicar.

## 3. Reparto por volcán, plataforma y mes

`06_donde_se_concentra.py` -> `06_donde_se_concentra.txt`. Denominador de cada tabla: filas OSF del tramo.

| tramo | OSF | faltan | tasa |
|---|---|---|---|
| A: antes de 2025-02-15 | 357 | 357 | 100 % |
| B: desde 2025-02-15 | 2.577 | 54 | 2,1 % |

- Tramo A por volcán (todo OSF del tramo falta): Puyehue-Cordón Caulle 84 (35 días distintos), Lastarria 56, Planchón-Peteroa 55, Láscar 50, Isluga 40,
  Copahue 31, Chaitén 23, Villarrica 10, Chillán 7, Llaima 1. El orden es el de la actividad que MIROVA vio esas semanas, no el de ninguna propiedad de nuestra búsqueda.
  Por plataforma: NOAA20 184, SNPP 166, Aqua 3, Terra 1, NOAA20_750 2, SNPP_750 1. Por mes: enero 251, febrero 106.
- Tramo B por volcán: Chillán 24 de 102 (23,5 %), Copahue 11 de 86, Láscar 6 de 765, Planchón-Peteroa 4 de 240, Lastarria 3 de 400, Llaima 2 de 33, Villarrica 2 de 32,
  Chaitén 1 de 86, Isluga 1 de 481, **Puyehue-Cordón Caulle 0 de 352**. De las 54, 49 son Dayflag=1 (las 24 de Chillán son todas diurnas: 22 entre el 2025-02-15 y el 2025-03-25, una el 04-09 y una el 10-30). Las 5 de Dayflag=0 son 4 C y la A.
- Tramo B nocturno por plataforma: VIIRS 0 de 2.263 (SNPP 0 de 1.087 y 23, NOAA20 0 de 1.131 y 22); MODIS Aqua 1 de 140 (C) y Terra 4 de 125 (3 C y la A).
- Cordón Caulle: su concentración (84 de 436 en el conteo original) es aritmética de fechas. Todas sus faltantes están en enero y los primeros 14 días de febrero de 2025; con la ventana en que
  tenemos serie la tasa es 0 de 352. `radius_km` es 25 como en los otros 9 (`volcanoes.yaml`), la caja de búsqueda es la misma, y no hay faltantes dentro de la serie que pudieran deberse a ella.
- Magnitud que MIROVA asigna a lo que falta (VRP del OSF): tramo A nocturno 352 pasadas, mediana 0,22 MW, 34 con 1 MW o más (24 en Cordón Caulle); tramo B diurno 49 pasadas, mediana 127 MW, las 49 con 1 MW o más
  (máximo 2.178 MW), sospechosas de reflejo solar (regla A76); cubiertas: mediana 0,42 MW, 663 con 1 MW o más.

## 4. Huecos recientes (VB-4)

`03_huecos_produccion.py` y `05_huecos_historicos.py` (datos del remoto bajados el 2026-10-21 con `gh api`, no del checkout; último record 2026-10-21 08:10 UTC),
`04_huecos_vs_cmr.py`, `07_conteo_global_cmr.py`, `09_hueco_cmr_y_vb1.py`, `10_dias_cero_vs_cmr.py`, `11_cuatro_dias_dudosos.py`, `12_chaiten_aqua_0721.py`.

Records por día UTC, 11 Tier A, 2026-09-07 a 2026-10-20 (44 días completos). Mediana del total diario 117. Bajo 0,5 x mediana: sólo el **13-oct (46)**. Bajo 0,75 x mediana: 13-oct y
**20-oct (75)**. El 18-oct (109) y el 19-oct (121) están en la banda normal. Por plataforma: Terra 0 el 09-28, 10-02 y 10-10; SNPP (V375 y V750) 0 el 10-13 y el 10-20; NOAA21 0 el 10-13; NOAA20 10 de 14 el 10-20.

Cruce con CMR hoy (`04`, 4 volcanes: Isluga, Láscar, Villarrica, Chaitén; 45 días; 1.772 gránulos nocturnos de CMR, elevación < 0):

| clase | n | lectura |
|---|---|---|
| ok (en CMR y con record) | 1.732 | |
| sin record, CMR con L1B y GEO | 40 | 36 con el volcán FUERA de la huella del gránulo (0,1 a 24,9 km), 4 dentro pero a 1 a 22 km del borde (`08_poligonos.txt`); ver H3 |
| L1B sin GEO (D, VB-1) | 0 | |
| record sin gránulo en CMR hoy | 108 | todos en 13, 18, 19 y 20-oct |
| diurnos | 1.818 | descartados por diseño |

Control: los 79 gránulos `ok` muestreados (80, uno sin polígono) tienen el volcán dentro de la huella (mínimo 16,0 km al borde); los 40 sin record sólo 4. El instrumento distingue.

Por día:
- **13-oct**: CMR hoy no tiene ningún gránulo nocturno (00 a 10 UTC) de SNPP ni de NOAA-21 en la caja de Chile (`10_dias_cero_vs_cmr.txt`, ambas colecciones 0), con los días vecinos con 5 a 7. Producción
  tampoco tiene records de esas dos plataformas. Los 46 records del día son MODIS y NOAA20; NOAA20 ya no figura en CMR hoy (producción lo procesó, con `first_processed_utc` hasta el 2026-10-19). Conclusión:
  hueco de NASA/CMR, no de descarga.
- **18-oct y 19-oct**: producción tiene 109 y 121 records (Standard, procesados 2,4 h después de cada pasada en mediana); **CMR hoy no devuelve ningún gránulo de ningún producto** en la caja de Chile para esos
  dos días ni para el tramo que va desde el 2026-10-17 (entre las 06 y las 20 UTC según el producto) hasta el 2026-10-20 (entre las 12 y las 19 UTC; MODIS NRT hasta el 10-21 01:35) (`09_hueco_cmr_y_vb1.txt`: saltos de 69 a 84 h en VNP02IMG, VJ102IMG y MOD021KM, Standard y NRT). Confirma R2-13 con una consulta
  independiente (cabecera `CMR-Hits`, caja de todo Chile, `07_conteo_global_cmr.txt`: 0 en los 14 productos L1B (y sus GEO) para el 18 y el 19).
- **20-oct**: mismo hueco de CMR hasta ~18 UTC. Producción tiene 75 records (42 Standard, 33 NRT) de Terra, Aqua, NOAA20 y NOAA21 que CMR hoy no lista. SNPP tiene 0 en producción y 0 en CMR: **SIN DATO**
  si NASA no publicó SNPP o si lo publicó y lo retiró.
- Los 33 días-plataforma con 0 records desde 2025-02-15 (Terra 8, Aqua 2, NOAA21 2, SNPP 21, NOAA20 0): en 29 CMR tiene 0 gránulos nocturnos de esa plataforma en la caja de Chile (`10`); en los 4 restantes CMR
  tiene gránulos en la caja grande de Chile pero ninguno sobre los 11 volcanes (Terra 2025-07-15 y 2026-06-02, Aqua 2025-11-16) o uno solo a 2,1 km fuera de la huella (Chaitén, Aqua, 2026-07-21, `12`).
  Ningún día de producción cero se explica por un fallo nuestro que CMR pueda mostrar. SNPP concentra 21 de 33: 2026-03-10 a 12, 04-28 a 30, 06-01 y 02, 07-11 a 16, 08-03 a 06, 10-13 y 10-20.
- VB-1 reproducido sin caja (todo el mundo, 2026-10-20, NRT): MOD021KM 72 contra MOD03 68, VNP02MOD_NRT 67 contra VNP03MOD_NRT 64, VNP02IMG_NRT 67 contra 64. Dentro de la caja de Chile, 0 L1B sin GEO en 1.772 gránulos
  nocturnos de los 4 volcanes y L1B-GEO <= 0 en los 8 días de `07`. Aparece, en el mundo, el desbalance que VB-1 describe, y en nuestra zona no apareció en el periodo medido.

## 5. Hallazgos

### H1. Un 12 % de las pasadas OSF de 2025 están fuera de nuestra serie porque la ola P4 del backfill no se ejecutó
- ARCHIVO:LÍNEA: `docs/BACKFILL_PLAN_S120.md:25` y `:79`; SCRIPT:SALIDA `01_conteo_faltantes.txt` («FALTANTES antes del inicio de la serie nuestra: 357»), `06_donde_se_concentra.txt`.
- QUÉ PASA: el OSF registra 357 pasadas de enero y los primeros 14 días de febrero de 2025 (352 nocturnas, 34 de 1 MW o más, 24 de ellas en Cordón Caulle) y nuestros 11 Tier A parten el 2025-02-15. No es fallo de descarga:
  CMR tiene L1B y GEO en las 55 muestreadas. Es el tramo de backfill que el plan dejó sin hacer. R2-16 lo presentó como pasadas que «no tenemos» y lo ató a una causa de cobertura; la causa es de calendario.
- CÓMO SE VE EN EL DASHBOARD: invisible; el tablero no muestra 2025. Cualquier recall o magnitud retrospectiva contra el OSF 2025 que no recorte desde 2025-02-15 incluye 357 pasadas sin contrapartida como si fueran falsos negativos.
- CÓMO REPRODUCIRLO: `python -I experiments\_s159\cob\01_conteo_faltantes.py` (desde el worktree, con `PYTHONIOENCODING=utf-8`).
- CONFIANZA: CONFIRMADO (calendario y conteo); SOSPECHA acotada para «CMR tiene las 357» (55 de 55).
- GRAVEDAD: 3 (no torcería una alerta en vivo, pero sesga las evaluaciones de recall que respaldan decisiones; arreglo: recortar la evaluación o ejecutar P4 con `backfill-tier-a.yml`).

### H2. Un hueco de CMR de unas 70 horas (desde el 2026-10-17 hasta el 2026-10-20) deja sin verificación independiente las noches 18, 19 y 20, y deja SNPP del 20-oct sin explicación
- ARCHIVO:LÍNEA: `09_hueco_cmr_y_vb1.txt` (saltos de 69,3 a 84,2 h), `07_conteo_global_cmr.txt` (0 gránulos el 18 y 19 en los 14 productos L1B), `04_huecos_vs_cmr.txt` (clase `rec_sin_cmr`: 108).
- QUÉ PASA: NASA/CMR hoy no sirve nada de esos días en Chile, aunque producción tiene 109, 121 y 75 records de ellos con `first_processed_utc` el mismo día. Si el cron NRT corriera durante un hueco así, `pipeline/fetch.py` devolvería cero gránulos y la cobertura diría «completa» (R2-9, ya confirmada). Esta medición no puede decir si SNPP no existió el 20-oct o si existió y fue retirado.
- CÓMO SE VE EN EL DASHBOARD: normal el 18 y 19; el 20-oct sin SNPP (V375 y V750), con 75 de ~117 records.
- CÓMO REPRODUCIRLO: `python -I experiments\_s159\cob\09_hueco_cmr_y_vb1.py` (la respuesta depende de la hora de consulta; la de este informe es 2026-10-21 18:41 UTC).
- CONFIANZA: CONFIRMADO (el hueco hoy); SIN DATO (causa y SNPP del 20).
- GRAVEDAD: 3 (una plataforma entera sin noche, sin que nada lo avise).

### H3. 40 gránulos nocturnos que CMR sirve no producen record; 36 tienen el volcán fuera de la huella y 2 de los 4 restantes dejan sin explicar el borde
- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `08_poligonos.txt`, `poligonos_resultado.csv`.
- QUÉ PASA: la caja de búsqueda de `fetch.py:751-753` (+-25 km) basta para que la huella de un gránulo de borde de barrido la toque, pero la huella no contiene al volcán (36 de 40, a 0,1 a 24,9 km fuera): no hay píxeles
  que procesar y no hay record, que es lo correcto. 16 de los 40 son MODIS (barrido más angosto). Quedan 4 con el volcán dentro: Isluga Terra 2026-10-14 02:05 (1,1 km del borde), Láscar Terra 2026-10-09 02:05 (6,5 km), Villarrica Aqua 2026-09-16 08:55
  (19,7 km) y Láscar Terra 2026-10-14 02:05 (21,6 km). El control `ok` más cercano al borde con record está a 16,0 km, así que los dos últimos no se explican por esa razón.
- CÓMO SE VE EN EL DASHBOARD: una pasada menos, en el borde del barrido.
- CÓMO REPRODUCIRLO: `python -I experiments\_s159\cob\08_poligonos.py`.
- CONFIANZA: CONFIRMADO para los 36; SOSPECHA para los 2 de 19,7 y 21,6 km (causa no probada).
- GRAVEDAD: 2.

### H4. MIROVA etiqueta como nocturnas (Dayflag=0) cuatro pasadas MODIS que NASA marca como diurnas; nuestro filtro nunca las verá
- SCRIPT:SALIDA: `02_clasificar_cmr.txt` («faltantes con Dayflag=0 de MIROVA y elevacion >= 0»), `clasificacion.csv`.
- QUÉ PASA: Villarrica Terra 2025-03-26 13:55 UTC (14,39 MW según MIROVA), Villarrica Terra 2025-04-07 13:35 (0,99 MW), Copahue Terra 2025-08-13 12:40 (1,53 MW) y Chaitén Aqua 2025-05-14 20:10 (1,27 MW) tienen el sol a 12 a 33 grados sobre el horizonte
  en el volcán; para tres, CMR marca `DAY`. El filtro `fetch.py:997-1024` (elevación < 0) las descarta, como debe.
- CÓMO SE VE EN EL DASHBOARD: invisible. En una auditoría de recall son 4 FN aparentes de MIROVA que no son FN nuestros.
- CÓMO REPRODUCIRLO: `python -I experiments\_s159\cob\02_clasificar_cmr.py`.
- CONFIANZA: CONFIRMADO (los números); la definición del Dayflag de MIROVA: SIN DATO.
- GRAVEDAD: 2.

### H5. Las 49 pasadas diurnas que MIROVA registró en 2025 son todas de 1 MW o más y no las vemos por diseño
- SCRIPT:SALIDA: `06_donde_se_concentra.txt` («B dia faltan n= 49 mediana= 127.202 ... >=1 MW: 49»), `pipeline.profile` con `ENABLE_DAYTIME_MODIS = False` y `ENABLE_DAYTIME_VIIRS = False` (leído con `VRP_PROFILE=mirova_equivalent`).
- QUÉ PASA: sol a 28 a 78 grados sobre el horizonte, VRP mediano de MIROVA 127 MW, 24 de las 49 en Chillán. Por A76 son probablemente reflejo solar sobre nube, pero no lo medí aquí.
- CÓMO SE VE EN EL DASHBOARD: invisible. Pasa a ser visible si se enciende la rama diurna.
- CONFIANZA: CONFIRMADO (que faltan y por qué); SOSPECHA (que sean artefactos).
- GRAVEDAD: 2.

### H6. Terra y SNPP tienen huecos propios de NASA que se repiten, sin aviso en la cobertura
- SCRIPT:SALIDA: `05_huecos_historicos.txt`, `10_dias_cero_vs_cmr.txt`.
- QUÉ PASA: desde 2025-02-15, 33 días-plataforma sin ningún record: Terra 8, Aqua 2, NOAA21 2, SNPP 21, NOAA20 0. SNPP tiene 7 episodios en 2026 (de 1 a 6 días) y 1 en 2025. En 29 de 33 CMR tiene 0 gránulos nocturnos, en 4 la plataforma pasa por Chile pero no sobre
  los volcanes. No medí si algún volcán quedó sin ninguna pasada VIIRS esas noches.
- CÓMO SE VE EN EL DASHBOARD: menos barras en esos días. Nada marca que el hueco es de NASA y no del pipeline.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### H7. VB-1 existe en CMR global, pero en 1.772 gránulos nocturnos de 4 volcanes durante 45 días no apareció ninguno
- SCRIPT:SALIDA: `09_hueco_cmr_y_vb1.txt` (sección VB-1), `04_huecos_vs_cmr.txt` (clase `sin_geo_D` = 0), `07_conteo_global_cmr.txt`.
- QUÉ PASA: el 2026-10-20 CMR mundial tiene 72 MOD021KM NRT contra 68 MOD03 NRT y 67 contra 64 en VIIRS 375 NRT. En la zona de nuestros volcanes, la diferencia L1B menos GEO nunca fue positiva en los 8 días medidos ni en los gránulos nocturnos de los 4 volcanes.
  El riesgo de VB-1 (descarte silencioso) es de código, y sigue válido; la frecuencia en nuestra zona en este periodo es 0 de 1.772. No mide los 7 volcanes no cruzados ni los días del hueco.
- CONFIANZA: CONFIRMADO (medida), con ese alcance.
- GRAVEDAD: 1.

## 6. Lo que no pude medir

- La cobertura de pasadas sin alerta de MIROVA entre 2025-02-15 y 2026-09-06. El OSF sólo lista pasadas con alerta; fuera de las 54 posteriores a 2025-02-15 y de los 33 días-plataforma en cero, un gránulo perdido en un día parcial no sería visible. El cruce completo con CMR de 45 días cubre
  sólo 4 de 11 volcanes (Isluga, Láscar, Villarrica, Chaitén) por tiempo de consulta (cada consulta de CMR tardó 2 a 12 s); los otros 7 volcanes sólo están en los conteos de records (`03`, `05`).
- Si CMR hoy es lo que CMR servía el día de la pasada. Los días 18 a 20-oct muestran que no. «Gránulo ausente en CMR» significa «ausente hoy»; no distingue «nunca existió» de «fue retirado».
- Las 302 pasadas F sin consulta propia a CMR y la recuperabilidad real de P4 (descargar y procesar). Sólo medí existencia en catálogo.
- Por qué los dos gránulos con el volcán 19,7 y 21,6 km dentro de la huella no tienen record (H3).
- Cómo MIROVA tuvo Terra 2025-07-15 02:15 sobre Láscar y cómo define Dayflag (H4).
- Si el SNPP del 2026-10-20 se publicó (H2).
- Reflejo solar en las 49 diurnas (H5): no hay medición propia.

## 7. VERIFICADO LIMPIO

- Mapa Satélite/Resolución a sensor nuestro y prefijo del gránulo: 0 discrepancias en 65.544 records. `python -I 01_conteo_faltantes.py`, líneas «records cuyo prefijo ...» y «pareadas cuyo prefijo ...».
- Pareo por hora: 2.523 de 2.523 con dt = 0 exacto, sin masa entre 10 y 30 min. `01_conteo_faltantes.txt`.
- Producción, VIIRS, tramo con serie (desde 2025-02-15): 0 de 2.263 pasadas nocturnas del OSF sin record (SNPP y NOAA20, 375 y 750). `06_donde_se_concentra.txt`.
- Cordón Caulle y `radius_km`: 0 de 352 dentro de la serie; mismo `radius_km = 25` que los otros 9 en `volcanoes.yaml`; sin efecto de caja. `06_donde_se_concentra.txt`.
- Nombres de producto de `pipeline/fetch.py:187-225` contra CMR: los 30 controles encontraron L1B y GEO con esos short names y versiones, y el `producer_granule_id` coincide con el `granule` del record (30 de 30). `02_clasificar_cmr.txt`.
- Filtro nocturno `fetch.py:997-1024`: sobre las 2.523 pasadas cubiertas, 0 con elevación >= 0; sobre CMR, `day_night_flag` = NIGHT en las 30 cubiertas consultadas. `02_clasificar_cmr.txt`.
- Días sin hueco de producción: en la serie de 44 días, 42 de 44 totales diarios entre 95 y 136; ningún día bajo 0,5 x mediana salvo el 13-oct, y el 20-oct bajo 0,75. `03_huecos_produccion.txt`.
- Gránulos con L1B sin GEO en nuestra zona: 0 de 1.772. `04_huecos_vs_cmr.txt`.
- NOAA20: 0 días sin records desde 2025-02-15. `05_huecos_historicos.txt`.
- Cada 0 de este informe vino con control: pareadas con dt = 0, 30 controles positivos y 10 negativos en CMR, 79 `ok` con el volcán dentro de la huella, y los 33 días-cero contra días vecinos con gránulos en CMR.
