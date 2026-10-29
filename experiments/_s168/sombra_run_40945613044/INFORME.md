# Lectura del run 40945613044 (sombra del código MIROVA, `medir=true`, Láscar 2026-10-21 a 2026-10-28)

S168, 2026-10-29. Despacho desde el tag `s167-sombra-medir` (`9533f00de`, el squash de #925). Sólo Láscar; los otros
10 jobs salen en segundos por el filtro de volcán. `medir=true` no commitea ni sube los records: lo único que queda es
el log del job (`log_job_lascar.txt`) y sus tiempos (`job_lascar.json`, `tiempos.txt`).

Script: `contar.py` (salida en `salida.txt`). Referencia: `registro_vrp_consolidado_20261029.csv`, bajado de
Mirova-v1 `main` el 2026-10-29 ~20:50 UTC (sólo la tabla, sin OCR, A119 y feedback S159). El CSV no se commitea
(`.gitignore`); se rebaja de
`https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv`.

## 1. ¿Corrió la vía de verdad?

Sí. `revisar_sombra.py` en el job: «77 records, 77 de la vía, 0 de otra fuente, 0 errores de gránulo»; el log dice
«Cobertura: completa». Por sensor (líneas de cada gránulo en el log): MODIS 17 (Terra 8, Aqua 9), VIIRS 750 32,
VIIRS 375 28. O sea que MODIS y VIIRS 750 pasaron por la vía en gránulos reales, sin caída a K.

## 2. Qué detectó, contra MIROVA (tabla)

| sensor | gránulos | con píxeles alertados | MIROVA, alertas de la tabla en la ventana |
|---|---|---|---|
| MODIS | 17 | 1 (Aqua, 2026-10-26, 0,184 MW, 1 píxel) | 1 (2026-10-26 07:55 UTC, 0,29 MW) |
| VIIRS 750 | 32 | 0 | 0 |
| VIIRS 375 | 28 | **no se puede leer del log** | 6 (0,04 a 0,16 MW, todas nocturnas) |

- MODIS coincide en el día; que sea la misma pasada queda SIN DATO (el log no imprime la hora del gránulo, y MIROVA
  rotula «MODIS» sin plataforma).
- VIIRS 375: la línea del log para 375 m imprime `vrp_mir_mw` y `t_max_i04_k`, que el record de la vía no llena
  (`pipeline/mirova_v750_codigo.py`, el dict de la l. 704 en `origin/main`), así que sale `None` siempre, haya o no
  detección. No es una falla de la vía: es un log ciego para ese sensor. Con records no commiteados, la detección de
  VIIRS 375 en esta corrida queda SIN DATO.

## 3. Costo

Job de Láscar 907 s; el paso del pipeline 801 s para 8 días (~100 s por día y volcán). Checkout 68 s e instalación 31 s
por job. Un schedule diario sobre 1 día por volcán costaría del orden de 3 a 4 min de runner por job, 11 jobs: estimación
por proporción, no medida (el repo es público, minutos ilimitados; lo que pesa es el lock del grupo y los commits, que
disparan pages-deploy, según la nota de S167).

## 3 bis. Corrección tras el verificador (`VERIFICADOR.md`, CONFIRMADO CON RESERVAS)

- **El §3 partía de una premisa falsa (gravedad 3 del verificador, comprobada):** el modo diario no corre 1 día sino
  8, porque `scripts/ventana_sombra.py:46` en `origin/main` devuelve `hoy - LOOKBACK_DIAS` (7) a `hoy`. Esta corrida
  ya ES el costo de un job diario: ~15 min de job (907 s) para Láscar. Con 11 jobs y `max-parallel: 4`
  (`sombra-codigo-mirova.yml:55`) son del orden de 165 min de runner y ~45 min de reloj (estimación por
  proporción, un solo volcán medido). Queda bajo lo que estimó `experiments/_s167_sombra/COSTO.md` (mediana 20 a 22
  min). La sombra tiene grupo propio (`group: sombra-codigo-mirova`, l. 44), así que no ocupa el lock de `push-main`:
  la frase del §3 sobre el lock no vale. La corrida no incluyó pasadas de LANCE del día en curso.
- **81 gránulos retenidos, 77 records (gravedad 2):** 4 de VIIRS 375 no dejaron record y nada lo avisa; según el
  verificador (CMR), 3 no contienen el volcán; el cuarto SIN VERIFICAR. VIIRS 750 no tiene corte de distancia, así que
  sus 32 incluyen al menos 3 pasadas que no vieron Láscar.
- **Los ceros no distinguen** «miró y no vio» de escena inválida o reflejo solar (el motivo está en el JSON, que
  `medir=true` no guarda). VIIRS 750 no tiene poder acá: 0 contra 0 no prueba sensibilidad.
- **MODIS (gravedad 1):** según el verificador, por CMR el Aqua nocturno del 26-oct es la pasada de las 07:55 UTC, la
  misma de la alerta de MIROVA; la coincidencia es de pasada, no sólo de día.
- `salida.txt` rotula «vacio» a los 28 de VIIRS 375: el log no lo puede saber. Una de las 6 alertas de VIIRS 375
  (0,04 MW) cae bajo D-9.

## 4. Lo que esta corrida no prueba

- Los otros 10 volcanes (sólo corrió Láscar).
- El valor de las detecciones de VIIRS 375 (log ciego, records no guardados).
- El paso de commit (`Commit sombra data` quedó `skipped`, como corresponde a `medir=true`).
