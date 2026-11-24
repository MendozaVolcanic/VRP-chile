# Verificación V1 del frente F1 (vía MODIS «código MIROVA» en producción), auditoría S175

## Encabezado

- Hora del servidor: inicio 2026-11-07 20:31:12 UTC (header `Date` de GitHub al sellar `caminos.md`); cierre de
  mediciones 2026-11-07 20:42:57 UTC (mismo header).
- Código medido: 752d348bc67190e53b610989877e2405d238a1bc. Comprobado por sha256 (con CRLF quitado) que los 9 archivos
  citados de `scripts/`, `pipeline/` y `.github/workflows/nrt.yml` de la copia
  `C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base\` son idénticos a `git show 752d348bc:<ruta>`; y
  `git diff --stat 752d348bc origin/main -- scripts pipeline .github frontend` sólo cambia `.github/workflows/tests.yml`
  (origin/main = e75a7d52d, 2026-11-07 19:38:23 UTC). El código de hoy es el medido.
- Datos medidos: los JSON de `data/mirova_equivalent/` y `data/guardia_k_modis/` de **e75a7d52d** (no de 752d348bc):
  la copia `root_base\data` coincide por sha256 con `git show e75a7d52d:` (Chaiten y Villarrica comprobados), igual que
  `C:\Users\nmend\vrp-temporales\s175_audit\f1\datos\e75a7d52d\`. La guardia es idéntica en los dos commits.
- Referencia: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (sha256 f833bfde...) y
  `registro_vrp_ocr.csv` (sha256 577a336e...), los de la vara del preámbulo.
- Modelo: Opus 5.5 (claude-opus-5-5). Esfuerzo real: SIN DATO (no lo veo desde dentro de la sesión).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v1\`
  (scripts, salidas, `caminos.md`, este informe, `hallazgos.csv`). Temporal:
  `C:\Users\nmend\vrp-temporales\s175_audit\v1\` (salidas del audit semanal en `audit\A_tal_cual\` y `audit\B_sin_via\`).
- `caminos.md` escrito antes de abrir ningún archivo citado; sha256 del cuerpo f4748bb2..., sellado 20:31:12 UTC.
- Llamadas a la API de GitHub: 2 de 5 (sólo el header `Date`).
- Qué NO miré: el `INFORME.md` del auditor y su `hallazgos.csv` (no los abrí); `f1\banco_via_vs_k.py` (ninguna
  afirmación lo cita); ninguna imagen PNG de MIROVA (no está en la lista de archivos que puedo bajar); los logs de los
  jobs de Actions (sólo el listado de pasos que el auditor guardó en `f1\salidas\gh_jobs_run_41812405190.txt`); ningún
  gránulo MODIS (pyhdf no corre en Windows), así que no reproduje el descarte de borde sobre el gránulo real.

## En una pantalla

1. 151 y 152 son reales en el código: la vigilancia nunca mira si el record de producción de una pasada posterior al
   encendido es de la vía (`prod_via` se calcula en l. 171 y sólo se usa en l. 273); re-corrí las mutaciones M6 y M2 y
   dan REVERSION_CANDIDATA y VERDE. Pero la caída a K que calla es casi inalcanzable hoy (K de respaldo y guardia son el
   mismo código con el mismo perfil) y «deja de escribir en un volcán» sí se ve (VIGILANCIA_CIEGA a los 4 días). Gravedad 2, no 4.
2. 154 CONFIRMADO con datos: el NRT no re-escribe 8 días; la primera observación de la vía es 19 h antes del
   encendido, no 8 días. La misma premisa falsa está en la ficha pública CPLT v1.18 (hallazgo nuevo V1-02).
3. 153 CONFIRMADO EN PARTE: el pipeline no deja rastro, pero la vigilancia sí lo cuenta por semana (W45: 1).
4. 155 REFUTADO en su consecuencia: los TIF se detuvieron el 2026-09-22, pero la «cabecera de la imagen» es la del PNG
   y los PNG de MODIS (Latest10NTI) se siguen capturando hasta el 2026-11-07 04:05 UTC.
5. 156, 157 y 158: mecanismos confirmados, efecto menor (gravedad 1): una protegida que la vía calle da flag
   individual de inmediato; el encendido sólo se mueve con un `--overwrite` masivo.

## Veredicto por afirmación

### 151. La vigilancia no comprueba que el record de producción sea de la vía

- Veredicto: **CONFIRMADO** en el código y en la mutación; la consecuencia práctica es **SOSPECHA de baja
  probabilidad**. Gravedad V1: **2** (auditor: 4).
- Evidencia leída: `scripts/vigilancia_guardia_modis.py` l. 200-201 (`calla` = `guardia_pub is True and prod_pub is
  False`), l. 203 (candidatas sin condición sobre `prod_via`), l. 171 (`prod_via` se calcula), l. 273 (único uso de
  `prod_via`, en `borde_enc`, lado retrospectivo). La regla, `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`
  l. 188-189, TEXTO: «producción (la vía) **tiene record y no publica**»: el paréntesis supone que todo record de
  producción es de la vía. El texto del issue (l. 437-439) dice «producción (la vía) calla».
- Re-corrida del auditor (`re_mutaciones.py`, que ejecuta `f1\mutaciones_vigilancia.py` sin tocar su lógica, sólo la
  carpeta de copias; salida `re_mutaciones_salida.json`): M0 VERDE (control), M1 REVERSION_CANDIDATA (control
  positivo), **M6 REVERSION_CANDIDATA** (record de producción marcado `sin_mxd03`, callado; guardia publica), NevadosDeChillan
  MODIS 2026-11-05 07:45, MIROVA 25 MW. Reproduce lo del auditor.
- Por qué baja la gravedad (caminos 151.7 y transversal):
  - Las marcas de caída a K se escriben en `pipeline/process_modis.py` l. 636-650. `sin_mxd03` es **inalcanzable** en
    producción: el único llamador, `scripts/run_pipeline.py` l. 247-250, salta el gránulo sin geolocalización antes de
    llamar a `calculate_vrp` (hallazgo V1-03). Quedan `sin_grilla` (configuración) y `geo_distinta` (forma del MxD03).
  - El K de respaldo de producción y el K de la guardia son el mismo detector sobre el mismo gránulo: el perfil
    `pipeline/profiles/guardia_k_modis.yaml` es `extends: mirova_equivalent` con sólo `enable_modis_codigo_mirova:
    false`, y `enable_modis_geo_mxd03: false` en `mirova_equivalent.yaml` l. 151. Para que el respaldo calle y la guardia
    publique hace falta además que procesen versiones distintas del gránulo (NRT contra estándar) o una diferencia no
    determinista. Dos condiciones raras a la vez.
  - Censo re-corrido sobre e75a7d52d (`censo_e75a7d52d_rerun.json`, idéntico a la salida del auditor): 14.973 records
    MODIS, 140 de la vía, **0 caídas a K** desde el encendido (control sintético con `--control`: 1, lo ve).
  - La acción que torcería es revertir la vía (reversible, con confirmación en la imagen de MIROVA), no perder una
    alerta: si el K de respaldo calló, revertir a K no la recupera.
- Fundo con 152 y V1-01 la raíz común: **`prod_via` no entra en ninguna decisión del lado prospectivo**.

### 152. Vigilante ciego por volcán

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad V1: **2** (auditor: 4).
- Parte confirmada (la vía cae a K en un solo volcán, VERDE): `avisos_via` (l. 345-360) toma `ultima_via` y `ultima` como
  máximos sobre **todos** los volcanes; contraste `scripts/vigilancia_sombra.py` l. 362-365, TEXTO: «Frescura POR VOLCÁN
  Y SENSOR. Si un lado muere en un solo volcán o en un solo sensor, sumar todo lo deja verde». Mutaciones: M2 del
  auditor (Chaitén, 15 records a `sin_grilla`) VERDE; mi V2e (`mutaciones_propias.py`, NevadosDeChillan, 13 records a
  `geo_distinta`, marca alcanzable) **VERDE, sin avisos**.
- Parte refutada (la vía deja de escribir en un solo volcán, VERDE): con el flag encendido, cuando la vía no corre el
  gránulo queda sin record (`process_modis.py` l. 657-658 devuelve None, no cae a K), así que producción deja de tener
  MODIS de ese volcán y `avisos_produccion` (l. 304-305, frescura por volcán vía `vs._avisos_frescura`) avisa. Mi V2d
  (Chaitén sin los 11 records de la vía desde el 2026-11-04, sin reponer) da **VIGILANCIA_CIEGA** con el aviso «producción
  de Chaiten en MODIS no produce hace 4 días». La M2c del auditor (records de la vía sin la clave) construye un estado
  que el pipeline no produce con el flag encendido: un record MODIS sin la clave sólo sale con el flag apagado.
- Por qué 2: la caída a K por volcán exige un cambio de configuración (grilla ausente en `pipeline/grillas_mirova.yaml`
  o coordenadas que `volcan_por_coordenadas`, `mirova_v750_codigo.py` l. 156-164, ya no reconozca) o un MxD03 de otra
  forma. Hoy los 11 volcanes tienen records de la vía (censo: 11 a 15 por volcán). Si pasa, el operador ve K, el
  detector que estuvo en producción hasta el 2026-11-02: no pierde lo que veía antes; lo que se pierde es la vigilancia
  y, peor, el plazo de 29 sigue avanzando (V1-01).

### 153. El descarte de borde de la vía no deja rastro

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad V1: **2** (auditor: 3).
- Confirmado por lectura: `pipeline/process_modis.py` l. 657-658 (`if _rec is None: return None`, sin llamar a
  `al_sin_dato`, a diferencia del camino K, l. 678-681); `pipeline/mirova_v750_codigo.py` l. 804-808 (menos de 100 celdas
  en 45 km, o el píxel más cercano a más de 5 km, l. 112: return None sin imprimir); `scripts/run_pipeline.py` l. 264-281
  (`if result:` sin `else`, nada al log); `scripts/revisar_errores_modis_nrt.py` l. 27 sólo busca `ERROR processing`.
- Caso de campo confirmado (`claves_guardia_vs_prod.py`, salida `claves_guardia_vs_prod_salida.txt`, MODIS desde
  2026-11-01, e75a7d52d): de 142 claves de la guardia, **1** sin record de producción a ±120 s: Villarrica MODIS_AQUA
  2026-11-04 07:10, guardia `vrp_mw` 0, estándar, gránulo `MYD021KM.A2026308.0710...`, `sensor_zenith_deg` 65,03 (borde
  del barrido). Control sintético: quitar de producción Llaima MODIS_TERRA 2026-11-02 01:15 la hace aparecer. Las 22 en
  sentido inverso son pasadas del 2026-11-07 que la guardia aún no procesa.
- Parte refutada: «ni rastro» no es exacto. La vigilancia cuenta esas pasadas por semana ISO (`disparadores`, l. 234-245)
  y el `guardia_modis_latest.json` de e75a7d52d trae `borde_171_01 = {"2026-W45": 1}`; una protegida en esa situación da
  INVESTIGAR a las 24 h (M4 del auditor re-corrida: INVESTIGAR, `sin_record`). El rastro existe sólo mientras corre la
  guardia y sin nombrar la pasada.
- SOSPECHA: que la causa de ese caso sea l. 804-808 y no otra; es coherente con el cenit de 65° y con el paso «Revisar
  errores de MODIS en el log» en verde en el job de Villarrica del run 41812405190 (listado guardado por el auditor),
  pero no lo reproduje (pyhdf). La pasada no tenía alerta (guardia 0 MW): ninguna decisión se torció ese día.

### 154. §4.1 y §4.7 suponen una re-escritura de 8 días que el almacén no hace

- Veredicto: **CONFIRMADO**. Gravedad V1: **2** (auditor: 3).
- Lectura: `pipeline/store.py` l. 695-699: un record existente se reemplaza sólo con `overwrite` o con el upgrade NRT a
  estándar; `scripts/run_pipeline.py` l. 189 y 594 (`overwrite` por defecto False); `.github/workflows/nrt.yml` l. 185 y
  201 (`--overwrite` sólo si el input del dispatch lo pide). La regla, l. 162-163, TEXTO: «El NRT re-escribe en cada
  corrida las 8 fechas que van del día a 7 atrás», y l. 318, TEXTO: «El NRT re-escribe con K las 8 fechas de su ventana».
- Medición propia (`reescritura_ventana.py`, salida `reescritura_ventana_salida.txt`, records observados desde
  2026-10-24, corpus e75a7d52d, último `processed_utc` 2026-11-07 18:58:33 UTC): en las últimas 24 h sólo se escribieron
  records observados el 2026-11-07 (MODIS 22, VIIRS 375 32, VIIRS 750 30); ningún record de los 7 días anteriores de la
  ventana. Los 21 records MODIS NRT de la vía del 2026-11-06 y 07 siguen NRT. Ningún record MODIS observado antes del
  2026-11-02 es de la vía. La primera observación de la vía es 2026-11-02 01:15, **19 h** antes del encendido (20:11:43),
  y llegó por upgrade a estándar (el record del encendido es `standard`). Control: los registros de la vía aparecen
  (140) y los VIIRS sí muestran upgrades tardíos (`post_enc` del 2026-10-31).
- Consecuencia: tras una reversión, la vía no se lava sola en 8 días: quedan de la vía todos sus records estándar (y
  los NRT hasta su upgrade). El paso 1 de §4.7 tiene que apartar todos los records con `via_codigo_mirova: true`, no
  sólo «lo observado antes» de la ventana. La franja de §4.1 es de horas, no de días (inofensivo para la vigilancia: su
  ventana, l. 81, sólo sobra).

### 155. §4.3 pide confirmar en mirova-tif-archive y los TIF dejaron de capturarse

- Veredicto: **REFUTADO** en lo que importa (el hecho de los TIF es cierto). Gravedad V1: **1** (auditor: 2).
- Medido (python sobre `C:\Users\nmend\vrp-temporales\s175_audit\insumos\tif_index.csv` y `png_index.csv`, todas las
  fechas con 32 caracteres, max lexicográfico válido): TIF 21.873 filas, máximo `captured_at_utc` 2026-09-22T11:01:36;
  PNG 167.626 filas, máximo 2026-11-07T04:05:57; MODIS `Latest10NTI` capturado hasta 2026-11-07T04:05:55 (262 capturas
  de MODIS Latest10NTI desde el 2026-11-02).
- La regla, l. 192, TEXTO: «la sesión mira la cabecera de la imagen de MIROVA de esa pasada (la captura
  `mirova-tif-archive`». La cabecera es de la imagen (PNG), no del GeoTIFF: `docs/S150_IMAGENES_SNPP.md` l. 23-24, TEXTO:
  «Su cabecera dice de qué pasada es ("Last Update", con el cenit del satélite en "Zen")». El índice TIF tiene
  `tif_path` y `kmz_path`, sin imagen con cabecera. La confirmación de §4.3 sigue siendo posible con las capturas PNG.
- SIN DATO: no miré un PNG de MIROVA capturado en noviembre para ver que trae la cabecera legible.

### 156. El audit semanal deja de dar flag por las protegidas MODIS de K en cuanto la vía tiene records

- Veredicto: **CONFIRMADO** el mecanismo; **CONFIRMADO EN PARTE** «sin anunciarlo». Gravedad V1: **1** (auditor: 2).
- Lectura: `scripts/auto_audit_weekly.py` l. 427-429 (`detector_vigente_de` da VIA_MODIS en MODIS), l. 1023-1025
  (`_de_vigente`), l. 1050-1059 (`flags_protegidas` sólo del vigente).
- Contrafactual propio (`audit_con_y_sin_via.py`, salida `audit_con_y_sin_via_salida.json` y
  `C:\Users\nmend\vrp-temporales\s175_audit\v1\audit\`, ventana 2026-09-08 a 2026-11-07): A tal cual, **VERDE, 0 flags**;
  B con `frontera_via_modis` en None, **FUERA_DE_BANDA, 6 flags**: recall MODIS de K 70 % (n = 20), magnitud
  NevadosDeChillan MODIS 0,485x (n = 13) y las 4 protegidas de Chillán (2026-10-12 07:20, 10-15 01:05, 10-25 07:20,
  10-30 07:15). El efecto es más amplio que lo afirmado: también caen los flags de recall y magnitud de K.
- Lo que sí se anuncia: el aviso «MODIS sin juzgar ... Las noches anteriores son de K, están en por_detector.K y no
  deciden» (l. 577-590) y las 4 protegidas siguen listadas en `alertas_protegidas.lista` y en la salida («protegida
  sin_publicar [K]», salida guardada por el auditor). Lo que no se dice es que esas pérdidas dejaron de dar flag.
- Por qué 1: son pasadas de octubre del detector que ya no corre en MODIS; la decisión de alerta de esas noches pasó, y
  el NRT no las re-escribe (154), así que el tablero seguirá mostrando el silencio de K en ellas.

### 157. El recall de VIA_MODIS no puede dar flag hasta 15 noches

- Veredicto: **CONFIRMADO**. Gravedad V1: **1** (auditor: 2).
- Lectura: l. 94 (`MIN_N_RECALL = 15`), l. 577-590. Corrida A: MODIS VIA_MODIS n = 2 noches con alerta (2026-11-02 a
  2026-11-07, snapshot de la referencia). A la tasa de K en la misma ventana (20 noches en 60 días) faltan unas 6 semanas.
- Mitigación medida (`audit_via_calla.py`, salida `audit_via_calla_salida.json`): callar en producción el record de la
  vía de NevadosDeChillan MODIS 2026-11-05 07:45 (25 MW) da **FUERA_DE_BANDA con 1 flag** («alerta protegida sin
  publicar ... detector VIA_MODIS») pese a n = 2. Lo que queda sin banda son las alertas bajo 1 MW, que la vigilancia de
  la guardia cubre con su cota Muy Bajo (l. 207-213).

### 158. El encendido se cuelga de un solo record y un `--overwrite` lo movería

- Veredicto: **CONFIRMADO EN PARTE**. Gravedad V1: **1** (auditor: 2).
- Lectura: `encendido_desde_datos` (l. 98-115) toma el mínimo `processed_utc`; `pipeline/store.py` l. 541 lo re-escribe
  en cada versión del record.
- Medición (`sensibilidad_encendido.py`, salida `sensibilidad_encendido_salida.txt`, función real sobre e75a7d52d):
  control 2026-11-02 20:11:43 (igual al publicado). Re-escribir el primer record lo mueve **2 s**; los 11 primeros, 3 min
  23 s; los 22 del 2026-11-02, a 2026-11-03 19:19:43; los 140 (un `--overwrite` de toda la vía), al instante del
  reproceso. «Se cuelga de un solo record» es formalmente cierto y prácticamente inocuo; el riesgo es el reproceso masivo.
- Efecto si se mueve: las protegidas entre el encendido viejo y el nuevo pasan al lado retrospectivo; si la vía las
  calla, `borde_del_encendido` (l. 273-274) pide INVESTIGAR en vez de REVERSION_CANDIDATA, y el plazo de 120 días se corre.

## Hallazgos nuevos (V1)

### V1-01

- TÍTULO: El plazo de 29 protegidas avanza con pasadas en que producción no corrió la vía
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 190-192 y 276-278
- QUÉ PASA: la vigilancia existe para medir si la vía pierde alertas que K ve; si en un volcán la vía cae a K, sus
  protegidas comparan K contra K y aun así cuentan como «vistas», y el plazo de §4.6 se puede cumplir con evidencia que
  no es de la vía. En el código, `vistas` filtra `protegida` y `guardia_pub is not None`, sin `prod_via`.
- CÓMO SE VE EN EL DASHBOARD: invisible; se ve en `guardia_modis_latest.json` como `fase: plazo_cumplido`.
- CÓMO REPRODUCIRLO: `python mutaciones_propias.py C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base 2026-11-07`;
  V2e (NevadosDeChillan con sus 13 records de la vía a `geo_distinta`) sigue con `vistas` 1, la protegida de Chillán
  2026-11-05 07:45 que ahora es K contra K.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (misma raíz que 151 y 152: `prod_via` no entra en el lado prospectivo)

### V1-02

- TÍTULO: La ficha pública CPLT v1.18 dice que la vía rige hasta 8 días antes del cambio; los datos dicen 19 horas
- ARCHIVO:LÍNEA: `docs/FICHA_SDA_VRP_CHILE.md` l. 7 y l. 25 (en 752d348bc y en origin/main)
- QUÉ PASA: la ficha de transparencia del SDA, TEXTO l. 7: «como cada corrida vuelve a procesar los últimos 8 días,
  también quedan con el método nuevo las pasadas observadas hasta unos 8 días antes». El almacén no re-escribe (154): la
  primera pasada MODIS con el método nuevo es 2026-11-02 01:15 UTC, 19 h antes de la primera corrida con la vía.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero (la marca `primeraViaModis` sale de los datos y es correcta); se
  ve en el documento público que lee un tercero.
- CÓMO REPRODUCIRLO: `python reescritura_ventana.py C:\Users\nmend\vrp-temporales\s175_audit\f1\datos\e75a7d52d\mirova_equivalent 2026-11-02T20:11:43Z`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (no tuerce una alerta; es una afirmación falsa en un documento exigido por la Resolución CPLT N°372).
  La misma premisa está en el docstring de `scripts/vigilancia_guardia_modis.py` l. 25 y en el comentario de l. 81 (inocuo).

### V1-03

- TÍTULO: La caída a K `sin_mxd03` es inalcanzable desde el NRT
- ARCHIVO:LÍNEA: `scripts/run_pipeline.py` l. 247-250; `pipeline/process_modis.py` l. 644-645
- QUÉ PASA: un gránulo sin geolocalización se salta (y se anota como incidencia) antes de llamar a `calculate_vrp`, así
  que la rama `geo_path is None` de la vía nunca corre; las únicas caídas posibles son `sin_grilla` y `geo_distinta`.
  Código muerto, documentado como posible en la vigilancia (l. 102) y en el audit (l. 446). Baja la probabilidad de 151.
- CÓMO SE VE EN EL DASHBOARD: invisible
- CÓMO REPRODUCIRLO: `grep -rn "process_modis.calculate_vrp" scripts pipeline` (un solo llamador, run_pipeline l. 253)
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### V1-04

- TÍTULO: Falta el JSON de la guardia de un volcán y la vigilancia declara ciegos los once
- ARCHIVO:LÍNEA: `scripts/vigilancia_guardia_modis.py` l. 375-378
- QUÉ PASA: `bp.cargar_nuestros` lanza FileNotFoundError por un archivo y `cargar_insumos` deja la guardia entera vacía;
  el veredicto es el correcto (VIGILANCIA_CIEGA, dirección segura) pero los avisos culpan a los 11 volcanes y anulan el
  nulo, lo que despista a quien diagnostica.
- CÓMO SE VE EN EL DASHBOARD: invisible; issue de vigilancia ciega con 12 avisos.
- CÓMO REPRODUCIRLO: M3 de `re_mutaciones.py` (salida `re_mutaciones_salida.json`).
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1 (seguimiento)

## SEGUIMIENTOS

- La vigilancia en producción lee la referencia remota viva (`.github/workflows/vigilancia-guardia-modis.yml` l. 52-63),
  así que el `guardia_modis_latest.json` commiteado (18 pasadas de alerta, 4 protegidas vistas) no se reproduce con la
  vara del snapshot (15 pasadas, 1 vista). No es defecto; quien compare con el snapshot verá números distintos.
- El rastro de 153 para el operador: la vigilancia cuenta por semana pero no nombra la pasada; nombrarla sería barato.

## VERIFICADO LIMPIO

- Copias contra commits: sha256 de 9 archivos de código (vara: `git show 752d348bc`) y de 4 JSON de datos (vara:
  `git show e75a7d52d`). Referencia: sha256 de los dos CSV contra los del preámbulo.
- Frescura por volcán de producción en la vigilancia: V2d da VIGILANCIA_CIEGA (vara: el aviso de l. 304-305 con
  `MAX_DIAS_SOMBRA_SIN_DATOS = 3`); M3 y M5 del auditor dan VIGILANCIA_CIEGA.
- Flag individual de una protegida de la vía en el audit semanal (`audit_via_calla.py`, vara: el predicado del tablero
  por `banco_paridad`, la misma ruta que usa `main`).
- Censo de detector efectivo (re-corrida idéntica a la del auditor, con control sintético que aparece).

## SIN DATO

- Causa exacta del descarte de Villarrica 2026-11-04 07:10 (no corrí el gránulo: pyhdf).
- Si las capturas PNG de noviembre traen la cabecera «Last Update» legible (no bajé ninguna).
- Si el workflow del audit semanal abre issue con el aviso «sin juzgar» (no leí `audit-weekly.yml`).

## FUERA DE ALCANCE

- `f1\banco_via_vs_k.py` y cualquier afirmación del auditor fuera de 151 a 158.
- Arreglos: ninguno aplicado.
