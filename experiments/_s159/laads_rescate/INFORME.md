# laads_rescate (S159): ¿existen en el depósito los gránulos que CMR no devuelve?

Fecha del servidor al medir: **2026-10-22, 02:19 a 02:45 UTC** (`date -u`; el pedido decía 2026-10-21, regla A86).
Carpeta: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\laads_rescate\`. Sin credenciales, sin git (sólo `git show
origin/main`, commit `d516b9d8c`, 2026-10-22 01:49 UTC), sin descargas. Consultas: 40 a CMR público, 112 listados de
LAADS y 112 de LANCE (pausa 1,5 s, caché en `_cache\`), más 7 HEAD de archivos sueltos.

Scripts: `01_listar.py` (consultas, salida `01_listar_resultado.json`), `02_analizar.py` (cruce, salida
`02_analizar_salida.txt`, lista `02_rescatables.json`), `03_head_chillan.txt`, `04_recheck_cmr.txt`.

## 0. Resumen

| día | qué pasa con los gránulos nocturnos sobre los 11 Tier A | ¿recuperable? |
|---|---|---|
| 2026-10-12 | NASA **reprocesó** SNPP y NOAA-21 de ese día el 2026-10-19 (sello `2026292...`). LAADS tiene sólo el archivo nuevo; CMR Standard sigue entregando la entrada vieja (`2026285...`), cuyo enlace da **404**. LANCE ya lo purgó (404). | Sí, desde LAADS con el nombre nuevo. Incluye la **protegida de Chillán 05:18** |
| 2026-10-17 a 20 | CMR Standard no indexa hoy 66 gránulos nocturnos que **sí están en LAADS Standard**, con el mismo sello que nuestros records. CMR NRT (LANCE) los tiene todos hoy. | Sí: hoy por CMR NRT (el fallback actual sirve), siempre por LAADS |
| 2026-10-20 SNPP | Faltan en LAADS, LANCE y CMR todos los gránulos de 04:18 a 07:48 UTC (36 seguidos), justo la pasada nocturna sobre Chile. | **No**: no existen en ningún depósito |

## 1. Las dos preguntas del instrumento

1. *Si el gránulo no existiera, ¿lo vería?* Sí. Los listados diarios de LAADS y LANCE traen todo el día; el total se
   imprime (sano: 240 VIIRS, 288 MODIS) y un hueco aparece como horas faltantes (así salió el de SNPP del 20).
2. *¿Distingue «no medí» de «no hay»?* Todo código distinto de 200 queda como SIN DATO, no como 0.
   - Control negativo: 2026-10-30 (futuro) da 404 en los 32 listados (16 LAADS, 16 LANCE). Un archivo inventado
     (`...0518.021.2099999999999.nc`) da 404; el nombre real nuevo da 200 (`03_head_chillan.txt`).
   - Control positivo, día sano 2026-10-15: los gránulos de nuestros records están en CMR Standard, CMR NRT y LAADS
     en 8 de 8 productos (Terra 4/4, Aqua 2/2, SNPP 375 y 750 4/4, NOAA-20 3/3, NOAA-21 4/4); en LANCE 26 de 28
     (Terra 2 de 4; LANCE MODIS trae 274 de 288 ese día).
   - Geometría: para saber qué gránulo cubre a un Tier A uso la huella de CMR del mismo día; si CMR no la tiene, la del
     mismo HHMM 16 días antes (ciclo de repetición). Validada en el 2026-10-15 contra la huella real: VIIRS 42 de 44
     coinciden, 0 predichas de más. **En MODIS falla** (Terra 0 de 8, Aqua 0 de 4: ya no mantienen el ciclo), así que
     en MODIS sólo cuento lo que CMR (Standard o NRT) muestra el mismo día.

Denominador de todo lo que sigue: gránulos L1B nocturnos (bandera NIGHT de CMR) cuya huella contiene el cráter de al
menos uno de los 11 Tier A, días 12, 15, 17, 18, 19 y 20 de octubre de 2026, consultados el 2026-10-22 ~02:30 UTC.

## 2. Tabla día × producto × fuente (nocturnos sobre Tier A)

REL relevantes; REC con record nuestro en `origin/main`; CMRs y CMRn CMR público Standard y NRT; LAADS y LANCE con L1B
y GEO presentes. VIIRS 375 (IMG) y 750 (MOD) dan los mismos números en cada fila.

| día | producto | REL | REC | CMRs | CMRn | LAADS | LANCE |
|---|---|---|---|---|---|---|---|
| 10-12 | Terra / Aqua | 4 / 3 | 4 / 3 | 4 / 3 | 0 / 0 | 4 / 3 | SIN DATO (404) |
| 10-12 | SNPP / NOAA-20 / NOAA-21 | 2 / 4 / 2 | 2 / 4 / 2 | 2* / 4 / 2* | 0 | 2 / 4 / 2 | SIN DATO (404) |
| 10-15 | Terra / Aqua | 4 / 2 | 4 / 2 | 4 / 2 | 4 / 2 | 4 / 2 | 1 / 2 |
| 10-15 | SNPP / NOAA-20 / NOAA-21 | 4 / 3 / 4 | 4 / 3 / 4 | 4 / 3 / 4 | 4 / 3 / 4 | 4 / 3 / 4 | 4 / 3 / 4 |
| 10-17 | Terra / Aqua | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 | 2 / 2 |
| 10-17 | SNPP / NOAA-20 / NOAA-21 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 | 2 / 4 / 2 |
| 10-18 | Terra / Aqua | 2 / 3 | 2 / 2 | **0 / 0** | 2 / 3 | 2 / 3 | 2 / 3 |
| 10-18 | SNPP / NOAA-20 / NOAA-21 | 2 / 4 / 4 | 2 / 3 / 4 | **0 / 0 / 0** | 2 / 4 / 4 | 2 / 4 / 4 | 2 / 4 / 4 |
| 10-19 | Terra / Aqua | 2 / 2 | 2 / 2 | **0 / 0** | 2 / 2 | 2 / 2 | 2 / 2 |
| 10-19 | SNPP / NOAA-20 / NOAA-21 | 3 / 2 / 4 | 3 / 2 / 4 | **0 / 0 / 0** | 3 / 2 / 4 | 3 / 2 / 4 | 3 / 2 / 4 |
| 10-20 | Terra / Aqua | 4 / 2 | 3 / 2 | **0** / 2 | 4 / 2 | 4 / 2 | 4 / 2 |
| 10-20 | SNPP / NOAA-20 / NOAA-21 | 4 / 2 / 4 | **0** / 2 / 4 | 0 / 0 / 0 | **0** / 2 / 4 | **0** / 2 / 4 | **0** / 2 / 4 |

\* Entrada vieja con enlace muerto (§3, H1). SNPP del 20: REL sale de la predicción de 16 días (validada para VIIRS).

## 3. Hallazgos

### H1. CMR entrega para el 2026-10-12 entradas que apuntan a archivos que NASA ya reemplazó; la protegida de Chillán 05:18 existe en LAADS con otro nombre
- SCRIPT:SALIDA: `02_analizar_salida.txt` («Casos nombrados» y «enlace muerto»), `03_head_chillan.txt`.
- QUÉ PASA: NASA reprocesó el 2026-10-19 los gránulos de SNPP y NOAA-21 del 12 (los 11 records de cada producto de ese
  día tienen otro sello de producción en LAADS; NOAA-20 y MODIS no cambiaron, 0 de 57). LAADS borró el archivo
  original y dejó el nuevo, pero CMR Standard sigue sirviendo la entrada vieja (actualizada el 2026-10-12T10:31). Son 8
  entradas nocturnas sobre Tier A con enlace muerto: SNPP 05:48 y 05:54, NOAA-21 05:12 y 05:18, en 375 y 750.
  Chillán 05:18: CMR da `VJ202MOD.A2026285.0518.021.2026285102115.nc` (404 en LAADS y en la nube); LAADS tiene
  `VJ202MOD.A2026285.0518.021.2026292150831.nc` y su geolocalización `VJ203MOD.A2026285.0518.021.2026292145235.nc`
  (HEAD 200 sin credenciales). Listado: `https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5201/VJ202MOD/2026/285/`.
  Lo mismo para Isluga 05:48 y Chillán 05:54 (`.../5200/VNP02MOD/2026/285/`, sello `2026292155815` y `2026292155814`).
- Sobre la discrepancia con el frente N: su probe (run 39693661527, `probe_2.log:206`) a las ~23:40 UTC del 21 vio «0
  candidatos»; hoy a las 02:26 y 02:45 UTC CMR da 7 entradas de VJ202MOD para el 12 (`04_recheck_cmr.txt`). Que CMR
  cambiara entre esas horas es SOSPECHA; lo que sí está medido es que hoy la entrada existe y su descarga no.
- CÓMO SE VE EN EL DASHBOARD: invisible (producción ya procesó el original el 12). Afecta reprocesos y A/B.
- CÓMO REPRODUCIRLO: `python -I 01_listar.py` (borrar `_cache\` para consultar de nuevo) y `python -I 02_analizar.py`.
- CONFIANZA: CONFIRMADO (listados y HEAD). GRAVEDAD: 3 (deja SIN DATO una alerta protegida en toda evaluación
  retroactiva; además, el archivo nuevo no es el que procesó producción, así que el control «K = producción» no vale
  para esas pasadas).

### H2. CMR Standard perdió 66 gránulos nocturnos del 17 al 20 que siguen intactos en LAADS; hoy CMR NRT los cubre, pero LANCE los borra en días
- SCRIPT:SALIDA: `02_analizar_salida.txt` («LAADS Standard que CMR Standard no indexa hoy», total 66, con URL por fila).
- QUÉ PASA: los archivos Standard tienen el mismo sello que nuestros records (0 cambios en 18 a 20), o sea no hubo
  reproceso, pero CMR Standard da 0 para el 18 y el 19 (`CMR-Hits: 0`, VNP02MOD) y le faltan Terra y VIIRS del 20 y
  Aqua del 17. CMR NRT tiene los 66 hoy (28 hits en VNP02MOD_NRT el 18 y 19), cuando ayer a las 18:41 UTC no tenía
  ninguno (`cob\INFORME.md` §4). La retención de LANCE es corta: el 12 ya da 404. Si CMR Standard no reindexa, en
  una o dos semanas sólo el listado de LAADS los encuentra.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (producción los procesó a tiempo).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (la exclusión de esos días en D25, D-29, se decidió por un estado de CMR que hoy
  ya no es el mismo; ventana de rescate con plazo).

### H3. SNPP del 2026-10-20: no existe en ningún depósito
- SCRIPT:SALIDA: `02_analizar_salida.txt` (listado LAADS VNP02MOD/VNP02IMG del 20: faltan 0418 a 0748, 36 gránulos;
  LAADS 204 de 240, LANCE 206 de 240, CMR 0 nocturnos).
- QUÉ PASA: falta toda la órbita nocturna sobre Chile de Suomi NPP en los tres lugares. Es un hueco de NASA (adquisición
  o bajada), no nuestro. Las 4 pasadas nocturnas previstas quedan como «no observado», no «no detectado».
- CONFIANZA: CONFIRMADO (ausencia en los tres; la causa en NASA es SIN DATO). GRAVEDAD: 2.

### H4. El pipeline no tiene más fuente que CMR, y una búsqueda vacía sale sin registrar falla
- ARCHIVO:LÍNEA: `pipeline/fetch.py:767-806` (`search_granules`: Standard y después NRT, ambos por
  `earthaccess.search_data`; termina en `return []`), `pipeline/fetch.py:1087-1088` (`if not l1b_granules: continue`,
  sin `_registrar_falla`), `pipeline/fetch.py:923` (`download_granules` baja sólo lo que trajo CMR).
- QUÉ PASA: con un hueco de CMR como el del 18 y 19 (H2, en la hora en que ni el NRT estaba) la plataforma se salta en
  silencio; con una entrada muerta (H1) la descarga falla y queda registrada como falla de descarga, pero no se busca
  el archivo nuevo.
- CONFIANZA: CONFIRMADO (leído). GRAVEDAD: 3 (ya conocido como R2-9; lo cito porque es el punto donde iría el arreglo).

### H5. Doce gránulos diurnos del 12 sobre Chile están en LAADS y no en CMR
- `02_rescatables.json`: SNPP 18:12, 18:18, 19:54 y NOAA-21 17:36, 17:42, 19:18 (375 y 750), sólo reprocesados.
  Irrelevantes para producción (filtro nocturno); importan sólo a la rama diurna. CONFIRMADO. GRAVEDAD: 1.

## 4. Qué haría falta para recuperarlos (decisión de Nicolás, no implementado)

1. **Para el A/B del frente N, hoy**: las tres pasadas del 12 se pueden bajar desde LAADS por URL directa (nombres de
   H1), con el token y no con el par usuario y clave (A71). Ojo: son el archivo reprocesado; el brazo K hay que
   compararlo contra sí mismo, no contra el record publicado.
2. **Para D25 (D-29)**: los días 17 a 20 están hoy completos en CMR NRT, así que el fallback actual de
   `fetch.py:767-806` los encuentra sin tocar código. El dato sería NRT y no Standard (diferencia de BT bajo 0,1 K
   según el CLAUDE.md del proyecto, no medida aquí). Si se quiere, hay que hacerlo antes de que LANCE los borre.
3. **Arreglo durable, para `pipeline/fetch.py` (A45: tag y confirmación)**: después del último intento de
   `search_granules` (`fetch.py:806`) o ante un 404 de descarga, listar
   `archive/allData/{colección}/{producto}/{año}/{día}.json` de LAADS y tomar el archivo con el mismo `AYYYYDDD.HHMM`.
   Límite: el listado no trae huella. Con una entrada de CMR (aunque muerta) la huella sale de ahí; sin ninguna, en
   VIIRS sirve la del día −16 (validada aquí) y en MODIS no (el `geoMeta` de LAADS pide aceptar una licencia, 303 a
   `/profiles/licenses/`, y no lo hice). Y registrar como falla la búsqueda vacía de `fetch.py:1087`.

## 5. Lo que no medí

- La causa del reproceso del 19 ni si CMR reindexará el 18 y 19 Standard. «Ausente en CMR» vale para las 02:30 UTC
  del 22.
- Si un gránulo reprocesado cambia la detección (no bajé nada).
- Los 34 volcanes fuera de Tier A, y el día 13 y 14 (no pedidos).
- Terra del 20 a las 02:35 y 02:40 cubre volcanes sin record propio en ese gránulo (tienen record en otro gránulo de la
  misma noche); no lo investigué.

## 6. VERIFICADO LIMPIO

- Las 40 consultas a CMR y los 192 listados de días pasados dieron 200 salvo LANCE del 12 (404, purgado):
  `02_analizar_salida.txt`, bloque «Estado de las consultas» y «Listados diarios».
- LAADS tiene completos (288 MODIS, 240 VIIRS) los días 15, 18 y 19 en los 16 productos, y NOAA-20 los seis días.
- NOAA-20 y MODIS del 12 no fueron reprocesados (0 de 57 records con sello distinto).
- Todos los records del 17 al 20 tienen su archivo en LAADS con el mismo sello (0 ausentes, 0 cambios salvo 4 Terra del
  20 que eran NRT): bloque «sello de producción».
- Ningún gránulo nocturno sobre Tier A está en un depósito y falta a la vez en CMR Standard y NRT en los días 15 a 20
  (los «recuperables» de `02_rescatables.json` son todos diurnos del 12).
