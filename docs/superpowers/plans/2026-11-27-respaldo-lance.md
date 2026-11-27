# Respaldo de búsqueda por LANCE cuando CMR falla o se congela: plan de implementación

> **Para quien ejecute:** TDD tarea por tarea (superpowers:executing-plans). Pasos con casillas `- [ ]`.

**Objetivo:** que una caída o un congelamiento del catálogo CMR de NASA no deje al NRT sin las pasadas que ya están en
LANCE, sin cambiar qué archivo se baja ni cómo se procesa.

**Por qué (el fenómeno antes que el código).** Las pasadas NRT de MODIS y VIIRS llegan primero a los servidores de
LANCE (nrt3 y su espejo nrt4) y segundos después el catálogo CMR las registra. El NRT busca sólo en CMR. Cuando el
indexador de CMR se cae (26-nov, aviso 3294; de nuevo el 27-nov desde ~07:00 UTC, `search/health` con
`indexer ok? false`), CMR responde «cero gránulos» o una lista congelada, sin error: el cortacircuito no salta y el
tablero queda atrasado como si el volcán no hubiera tenido pasada. El 27-nov a las 12:37 UTC LANCE tenía 59 gránulos
MYD021KM, 47 VJ102IMG_NRT y 41 VJ202IMG_NRT del día que CMR no listaba
(`D:\vrp-trabajo\temporales\s203\cmr27\lance_vs_cmr_331.txt`), entre ellos la pasada NOAA-20 de las 06:48 sobre
Láscar y la nocturna de Aqua. LANCE tiene su propio buscador espacial, anónimo e independiente de CMR
(`/api/v2/content/details?products=<p>&temporalRanges=<año>-<día>&regions=[BBOX]W.. N.. E.. S..`), que devuelve cada
gránulo con su `fileId` (el mismo número que CMR usa en `GranuleUR` = `LANCEMODIS:<fileId>`), su inicio, su polígono
y el nombre del archivo. Es lo que MIROVA lee (Coppola et al. 2019): mismos archivos, cero cambio científico.

**Arquitectura.** Un módulo nuevo `pipeline/lance_respaldo.py` (consulta a la API de LANCE, conversión de cada
respuesta a un `earthaccess.results.DataGranule` con la misma forma que el de CMR, y chequeo de salud de CMR una vez
por proceso). En `pipeline/fetch.py`, `search_granules` pasa a ser una envoltura: busca en CMR como hoy
(`_buscar_en_cmr`, el cuerpo actual sin cambios) y, sólo para productos NRT, días recientes y cuando CMR dio vacío, falló
o está congelado, completa con LANCE las pasadas que CMR no trae (por minuto de inicio, sin duplicar). Descarga, filtro
nocturno, pareo L1B con geolocalización y procesamiento no cambian.

**Tecnología:** Python 3.11, `urllib` (sin dependencias nuevas), earthaccess 0.17.0 (la del runner), pytest.

**Qué NO hace (YAGNI):** no toca el producto estándar (LAADS, 22 a 46 h de atraso, nunca es el que falta en NRT); no
cambia la cadencia del NRT; no usa NODD de NOAA (otra calibración, decisión 3 del bloque S203); no toca A45
(`process_*.py`, `store.py`, perfiles).

---

### Decisiones de diseño (con su porqué)

1. **Disparadores.** Se consulta LANCE si, para un producto con versión NRT y un día de los últimos
   `LANCE_DIAS = 10` (LANCE retiene ~7 a 14 días):
   a. CMR devolvió vacío (catálogo caído entero, como el 26-nov), o
   b. la búsqueda en CMR falló o la saltó el cortacircuito (timeout), o
   c. `search/health` de CMR dice `indexer ok? false` (congelado: lista vieja, como el 27-nov).
   Si CMR devolvió el producto **estándar**, no se consulta (ese día ya está definitivo).
   Por qué no siempre: con CMR sano el catálogo registra el gránulo segundos después de LANCE (medido en S202: Aqua
   05:25, 06:12:02 en LANCE y 06:12:04 en CMR), y la ayuda de LANCE advierte bloqueo de IP por pedidos excesivos.
2. **Unión, no reemplazo.** Lo que CMR trajo se queda; se agregan las pasadas de LANCE cuyo minuto de inicio no está.
3. **Enlace de descarga = el de CMR.** `https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/<conjunto>/<producto>/<año>/<día>/<archivo>`,
   con `<conjunto>` 61 (MODIS), 5201 (VJ1 y VJ2 v2.1) o 5200 (VNP). Es exactamente la forma de los enlaces GET DATA
   de CMR (verificado sobre `LANCEMODIS:3112662237`, VJ102IMG_NRT 2026-11-27 05:06), así que la descarga usa el mismo
   camino y el mismo token que ya funcionan.
4. **Cobertura honesta.** Si CMR falló y LANCE trajo pasadas, la falla de búsqueda de ese producto se quita de
   `_FALLAS` (los datos sí se buscaron y se encontraron) y queda una entrada en `respaldos_lance()`. Si LANCE no
   responde o da vacío, todo queda como hoy.
5. **Aviso.** Una vez por proceso, en Actions, `::warning::` «Catálogo CMR de NASA congelado o caído: N pasadas
   tomadas de LANCE» y una línea en el resumen del job; fuera de Actions, sólo `_diag`.
6. **Filtro espacial generoso (agregado al ejecutar, tras la prueba en vivo).** La búsqueda por región de LANCE devuelve
   también gránulos lejanos (Láscar 27-nov: NOAA-21 04:12 con el borde a 573 km), y su polígono GRing de cuatro
   esquinas no reproduce a CMR. Calibrado contra CMR sano (21, 23 y 25-nov; 4 volcanes, 4 productos, 176 gránulos;
   `D:\vrp-trabajo\temporales\s203\lance_vivo\salida_calibrar_filtro.txt`): con 25 km de tolerancia se pierden 5 de
   123 pasadas de CMR; con 100 km, 1 (diurna) y entran 23 de más. Se usa 100 km: uno de más no hace daño, porque si no
   cubre el volcán la vía devuelve None y no hay record (`calcular_vrp_granulo`); sólo cuesta su descarga.
7. **Interruptor.** `VRP_LANCE_RESPALDO=0` apaga todo (variable de infraestructura, como `VRP_CMR_BREAKER`).

### Archivos

- Crear: `pipeline/lance_respaldo.py` (consulta, conversión, salud de CMR).
- Modificar: `pipeline/fetch.py` (`search_granules` como envoltura; cabecera FICHA, «Datos entrada» y «Lógica»).
- Crear: `tests/test_fetch_respaldo_lance_s203.py` (sin red: todo con monkeypatch).
- Ficha SDA: fila al mergear (regla S185), texto en la descripción del PR.

### Tarea 1: conversión de una respuesta de LANCE a DataGranule

- [ ] Prueba: con el item real de VJ102IMG_NRT 05:06 del 27-nov (fileId 3112662237), `a_granulo` da
  `GranuleUR == "LANCEMODIS:3112662237"`, `BeginningDateTime == "2026-11-27T05:06:00.000Z"`,
  `CollectionReference == {"ShortName": "VJ102IMG_NRT", "Version": "2.1"}` y `data_links()` igual al enlace GET DATA
  de CMR para ese gránulo. Con MYD021KM 08:30 da conjunto 61 y versión 6.1NRT.
- [ ] Implementar `a_granulo(item, short_name, version)` y `CONJUNTO` por prefijo de producto.

### Tarea 2: consulta a la API con espejo

- [ ] Prueba: `consultar` arma la URL con el BBOX en el orden W N E S, filtra por `products == short_name`,
  `resourceType == File`; si nrt3 lanza error, usa nrt4; si los dos fallan, lanza `LanceNoResponde`.
- [ ] Implementar con `urllib.request.urlopen(url, timeout=60)`.

### Tarea 3: salud de CMR

- [ ] Prueba: JSON con `indexer.ok? false` (HTTP 503) da True; `ok? true` da False; error de red da False; se consulta
  una sola vez por proceso.
- [ ] Implementar `catalogo_congelado()` con caché y `reiniciar()` para las pruebas.

### Tarea 4: envoltura en search_granules

- [ ] Pruebas (con `_buscar_en_cmr` y `lance_respaldo.consultar` falsos): vacío de CMR da los de LANCE; estándar de CMR
  no consulta LANCE; NRT de CMR con catálogo congelado da la unión sin duplicar por minuto; día de hace 11 días no
  consulta; `VRP_LANCE_RESPALDO=0` no consulta; falla de CMR más LANCE con pasadas quita la falla y registra el
  respaldo; LANCE caído devuelve lo de CMR sin excepción; producto sin NRT no consulta.
- [ ] Pruebas de integración liviana: `_match_granules` parea L1B y GEO de LANCE; `_filter_nighttime_granules` los
  filtra; `_minuto_granulo` lee el minuto del nombre.
- [ ] Implementar; mutaciones a mano sobre copia (quitar la deduplicación, invertir la condición del estándar, quitar el
  límite de días): cada una tiene que hacer fallar una prueba por aserción.

### Tarea 5: prueba en vivo (fuera del CI)

- [ ] Script en `D:\vrp-trabajo\temporales\s203\lance_vivo\` que llama `consultar` para Láscar 2026-11-27 en VJ102IMG_NRT
  y MYD021KM, y comprueba de forma anónima que cada archivo aparece en el listado
  `details/allData/<conjunto>/<producto>/<año>/<día>` (la descarga misma pide el token, que sólo existe en Actions).

### Tarea 6: verificador limpio, PR y comprobación en producción

- [ ] Verificador con contexto limpio sobre el diff (regla del proyecto para PR propios del pipeline).
- [ ] PR con fila de ficha; merge con `uno.sh`.
- [ ] Tras el merge, la corrida NRT siguiente: buscar `LANCE_RESPALDO` en el log y las pasadas nuevas del 27-nov (Aqua
  nocturna, NOAA-20 06:48) en `data/mirova_equivalent/`. Si CMR ya se recuperó, decirlo: la prueba en producción
  queda para la próxima caída.
