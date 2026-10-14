# S150 meta-auditoría: verificador con contexto limpio, afirmaciones de datos D1 a D10

Fecha: 2026-10-09 (hora del servidor de GitHub en los commits leídos: hasta 2026-10-09 16:46 UTC).
Método: formé juicio propio y re-medí cada afirmación con scripts míos **antes** de abrir los informes de los
auditores (`AUDITOR_F1` a `F4`); sólo después los leí para ver de dónde salía cada número. Scripts y salidas
crudas en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\verif_datos\`.
No toqué nada del repo salvo este informe y esa carpeta. Los CSV del remoto los bajé por `raw.githubusercontent`
fijando el sha, al scratchpad; sin clonar ni hacer pull.

Gravedad 1 a 5 = qué decisión de alerta o del plan del loop puede torcer.

## Resumen

| # | afirmación | veredicto | gravedad | en una línea |
|---|---|---|---|---|
| D1 | 207 filas perdidas el 05/06-oct, tercera vez, 8 alertas, 3 nocturnas sin respaldo | **PARCIAL** | 4 | 207 y 8 al número; "tercera vez" es falso (son al menos **cinco** caídas); "sin respaldo" vale sólo para copias vivas, las 8 siguen en la historia git de los dos repos |
| D2 | 858 lejanas desde marzo, 498 diurnas, 360 nocturnas; NULO lo escribe el scraper | **CONFIRMADO** | 3 | 499/359 con mi corte, 498/360 si la fila de las 12:25 UTC cuenta como noche; NULO y toda la columna de clase las calcula el scraper |
| D3 | con tabla sola, D22 explica 12 de 24 pérdidas débiles de `max` | **CONFIRMADO** (número) / **PARCIAL** (verbo) | 2 | 12 de 24, las 12 bajo 0,10 MW; "explica" es fuerte: dependen del segundo pase, y por qué `max` las rechaza ahí no está medido |
| D4 | `max` conserva 119 de 119 alertas de 0,5 MW o más; las 8 pérdidas de 0,20 MW o más eran sólo OCR | **PARCIAL** | 3 | vale para VIIRS 375; en VIIRS 750 `max` pierde 4 alertas de tabla de 0,32 a 0,65 MW; "sin filas sólo OCR" no es la vara que da 119 |
| D5 | A119 dice 0 alertas MODIS dependientes del OCR; son 4 | **CONFIRMADO** con matiz | 2 | el "0" es falso; el número se mueve con las caídas del remoto: 3 antes del 06-oct, 5 hoy (4 nocturnas, o 4 desde marzo) |
| D6 | el 86 % de enero es Tupungatito en el denominador; sin él 97 a 100 % | **PARCIAL** | 2 | el mecanismo es cierto (más un día parcial); sin él da 95,2 a 99,5 %, no 97 a 100 (VIIRS 750 queda en 95 %) |
| D7 | el record no guarda perfil ni código | **CONFIRMADO** | 3 | 0 campos de perfil o de versión de código en 65.206 records; `product_version` es el producto L1B |
| D8 | `ENABLE_TEST1_NULL_CORRECTED` no lo lee ningún procesador | **CONFIRMADO** | 3 | los tres llamadores no pasan `null_corrected`; un brazo que lo encienda sale igual al control |
| D9 | el fondo por vecinos (D25) no excluye vecinos nublados bajo 255 K y el paper lo exige | **PARCIAL** | 2 | el código no excluye nube (cierto, V375 y V750); lo exige Coppola 2014 (IJRS p. 3412), **no** Coppola 2016a (p. 7, ec. 6), que es el canon MIROVA |
| D10 | el scraper aborta con VRP de 1.000 MW o más por la coma; issue #19 abierto | **CONFIRMADO** | 3 | `scraper.py:140` hace `float()` crudo, el `except` externo corta el ciclo entero; #19 OPEN; 36 ciclos caídos en la bitácora |

## D1. El consolidado remoto perdió 207 filas en silencio

**Lo que medí (VERIFICADO).**
- Historia del archivo por la API (`gh api repos/MendozaVolcanic/Mirova-v1/commits?path=monitoreo_satelital/registro_vrp_consolidado.csv`,
  982 commits del 04 al 07-oct, uno cada ~5 min) y tamaño por sha (`contents?ref=`). La caída está entre
  `e489b42f` (2026-10-06 01:41:01 UTC, 6.210.483 bytes, 41.361 filas) y `fec07850` (01:46:21 UTC, 6.179.713 bytes,
  41.154 filas). En medio hay un commit `8e049752` (01:42:03 UTC) con **42.429 filas (+1.068)**: el estado
  intermedio es más grande, no más chico. O sea que la pérdida es la resolución de dos estados divergentes, no un
  borrado (SOSPECHA de carrera, consistente con el `rebase -X ours` que describe el issue #19). En hora de Chile
  es la noche del 05-oct (22:41 a 22:46).
- `d1_filas_perdidas.py cons_e489b42f.csv cons_fec07850.csv cons_latest.csv`: **207 llaves** (fecha satélite,
  volcán, sensor) perdidas, **0 nuevas** en la versión posterior, 0 duplicados por llave en las tres versiones,
  **0 reaparecen** en el remoto de hoy (`9f628d55`, 16:46 UTC). Tipos: 196 RUTINA, **8 ALERTA_TERMICA**, 3
  FALSO_POSITIVO; fechas del 2026-01-12 al 2026-10-05; MODIS 93, VIIRS (750) 65, VIIRS375 49.
- Las 8 alertas: Láscar V375 09-19 19:06 (diurna, 0,36), PCC V750 08-18 05:48 (0,64), Isluga V375 08-05 05:42
  (0,34), **Láscar MODIS 04-18 01:50 (2,06)**, Láscar V750 03-16 06:24 (0,51), PCC V750 02-26 05:24 (0,75),
  Láscar MODIS 02-14 01:40 (3,43), PCC V750 01-23 06:00 (1,34). Siete nocturnas.
- `registro_vrp_positivos.csv` del remoto perdió las mismas 8 en ese commit (1.587 a 1.579 filas), y el
  `registro_Lascar.csv` remoto de hoy ya no trae la alerta V750 del 03-16 (sí la trae nuestra copia del snapshot).

**"Por tercera vez": REFUTADO, se queda corto.** `d1_tamano_historia.py` (tamaño cada 12 h, enero a octubre) más
diff por llave en cada caída encontrada:

| caída (UTC) | llaves perdidas | alertas | reaparecen hoy |
|---|---|---|---|
| 2026-01-21 00:00 a 12:00 | 37 (36 RUTINA, 1 FALSO_POSITIVO) | 0 | 0 |
| 2026-04-23 12:00 a 04-24 00:00 | (no la desglosé; S139 la documentó) | (S139) | |
| 2026-08-25 12:00 a 08-26 00:00 | 202 | 11 | 0 |
| 2026-08-26 12:00 a 08-27 00:00 | 186 | 10 | 0 |
| 2026-10-06 01:41 a 01:46 | 207 | 8 | 0 |

Son al menos **cinco** episodios (S139 contó la de abril y "la del 25 de agosto", que en realidad son dos noches
seguidas). Instrumento: una caída menor que el crecimiento del archivo en 12 h (~10 a 20 KB) no se ve, así que
cinco es un piso. Las caídas de abril, agosto y octubre caen entre las 20 y las 23 h de Chile (SOSPECHA de una
tarea nocturna que corre en paralelo con el scraper; no lo seguí).

**"3 nocturnas sin respaldo": PARCIAL.** Busqué cada alerta perdida (mismo volcán, ±10 min) en todas las copias
(`d1_respaldo.py`):
- En los archivos **vivos** del remoto (consolidado, OCR, positivos, maestro publicable, registros por volcán):
  Isluga V375 08-05 y Láscar V750 03-16 no tienen ninguna fila de alerta; PCC V750 01-23, 02-26 y 08-18 sólo
  tienen la alerta **V375** de la misma pasada (el producto V750 sí se perdió); Láscar MODIS 04-18 y 02-14 sólo
  quedan en el **OCR** (2,0 y 3,0 MW truncados, distancia 0,0 porque es anterior al 2026-06-13).
- El auditor F3 cuenta como respaldo el `registro_vrp_consolidado_respaldo_20260408.csv` local, que recupera 4
  (01-23, 02-14, 02-26, 03-16); quedan 3 nocturnas sin respaldo de tabla: 04-18, 08-05 y 08-18. Con esa
  definición su número es correcto y lo reproduje.
- Pero **las 8 tienen respaldo completo** en dos lugares que el enunciado no menciona: la historia git de
  Mirova-v1 (`e489b42fa4302949b4367d3eb7d76ebc4df47d9e`) y nuestra copia
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`, que quedó escrita por la auditoría
  semanal el 2026-10-05 18:05 UTC (commit `80b358f6d`), **antes** de la caída, y todavía está así en el árbol.
  Son recuperables; lo que no hay es una copia viva que las traiga.

**Las dos preguntas del instrumento.** Si el remoto perdiera filas, ¿lo vería? Sí: comparación llave a llave entre
dos versiones fijadas por sha, con 0 llaves nuevas (descarta que sea un renombre de sensor o de hora). Si el
instrumento estuviera muerto, ¿se vería distinto? Sí: el mismo script da 0 pérdidas entre versiones sin caída
de tamaño (comprobado implícitamente: las 41.154 llaves posteriores están todas en la anterior).

**Gravedad 4.** No por las 8 alertas (son pocas y recuperables) sino porque la referencia que decide los A/B
pierde alertas cada pocas semanas sin aviso, y nuestro propio flujo amplifica el daño: ver hallazgo propio P1.

## D2. Las 858 detecciones lejanas

**VERIFICADO** con `d2_lejanas_dia_noche.py latest_consolidado.csv` (copia de la raíz sincronizada el
2026-10-09 16:10 UTC). Ventana 2026-03-01 01:35 a 2026-10-09 13:05 UTC, 35.806 filas; FALSO_POSITIVO = **858**,
0 duplicados por llave, distancia mediana 19,995 km (3,46 a 34,47), 0 con VRP 0. Con noche = hora UTC < 12:
**359 nocturnas, 499 diurnas**. La diferencia con 498/360 es una sola fila: Llaima MODIS 2026-05-20 12:25 UTC
(08:25 en Chile, 42,8 MW), una pasada de mañana que F2 cuenta como nocturna; yo la cuento diurna, pero es
borde. Las nocturnas son 332 V375, 17 V750, 10 a 11 MODIS.

**NULO lo escribe el scraper: VERIFICADO.** `scraper.py:144-154` (HEAD de Mirova-v1): `vrp > 0` y
`dist > limite_km` da `FALSO_POSITIVO`, `es_alerta_real = False`; y `volcanes.py:63-72`
(`clasificacion_mirova`) devuelve `"NULO"` si `not es_alerta`. Más fuerte que el enunciado: **toda** la columna
"Clasificacion Mirova" (Muy Bajo, Bajo...) la calcula el scraper a partir del VRP con la escala de Coppola; no
es una etiqueta que MIROVA publique en `latest.php`.

Instrumento: si las lejanas fueran nocturnas, el histograma por hora lo mostraría (sale bimodal, 04-07 UTC y
17-20 UTC); si el corte día/noche estuviera muerto, las ALERTA_TERMICA no saldrían casi todas nocturnas.

**Gravedad 3**: el pre-registro del A/B `vent_anchored` contra `vrp_max` debe dimensionarse con las ~360
nocturnas, no con 858. Que la fila lejana sea "la anomalía mayor de la escena" sigue sin medir (lo dice F2 como
SOSPECHA y coincido).

## D3. D22 y las pérdidas débiles de `max`

**VERIFICADO el número** con `d3_d4_perdidas_max.py` sobre `experiments/_s150_debiles/filas.json` (1.143
alertas de MIROVA que publica el brazo B, abril a 2026-08-27). Etiqueta "tabla" = alguna fila CONS con
ALERTA_TERMICA; camino D22 = B sin píxeles del primer pase (`diag_n_first_pass_pixels == 0`). VIIRS 375: 42
pérdidas, **24 con tabla, 12 de ellas por el camino D22**; las 12 están bajo 0,10 MW. Por satélite, las 24 de
tabla son 12 NOAA-20, 8 NOAA-21 y 4 Suomi NPP: "sin OCR de Suomi NPP" y "tabla sola" no son lo mismo (la tabla
sola también saca el OCR de NOAA-20 y 21).

**PARCIAL en el verbo.** Que la pérdida "la explica D22" no está medido: el doc dice que la compuerta D22 bloquea
el primer pase en **los dos** brazos, B las rescata en un segundo pase sin compuerta y F las rechaza ahí con
μ₂ + 5σ₂, que no se persiste. Lo medido es "dependen del segundo pase"; por qué `max` las rechaza es una
hipótesis (el A/B de D22 la decidiría). Además `diag_n_first_pass_pixels` cuenta píxeles de toda la escena, no
el publicado (salvedad del propio doc). **Gravedad 2.**

## D4. `max` y las alertas fuertes con la vara corregida

**VERIFICADO para VIIRS 375**, sobre las alertas que publica B (`filas.json`):
- Con tabla sola: **115** alertas de 0,5 MW o más y 0 pérdidas; 349 de 0,20 MW o más y 0 pérdidas.
- Las pérdidas de 0,20 MW o más con cualquier etiqueta son **8, todas sólo OCR**: 6 Suomi NPP (Lastarria 05-02,
  Isluga 05-29, PCC 05-05, Láscar 06-25, 08-17 y 08-22) y 2 NOAA-21 en Lastarria (06-17 0,46 y 08-04 0,20). Al
  número.

**No reproduje el 119.** Viene de F3 (`r1_recall_tramo_vara_corregida.py`), con otro denominador (pasadas
positivas del **control**, no lo que publica B) y otra vara (L2: tabla antes del 06-13 y tabla más OCR después,
salvo el OCR de Suomi NPP). L2 **conserva** el OCR de NOAA-21, así que bajo L2 esas dos de Lastarria siguen
perdidas (F3 lo dice en su cuerpo). El enunciado "sin filas sólo OCR" mezcla L1 y L2.

**REFUTADO si se generaliza a la réplica entera.** En VIIRS 750, con etiqueta de tabla, `max` pierde 1 de 88
alertas de 0,5 MW o más y **4 de 133** de 0,20 MW o más: PCC 2026-08-22 06:18 (0,65 MW, NOAA-21), PCC 04-30 06:06
(0,41), PCC 05-02 06:18 (0,39) e Isluga 07-13 05:18 (0,32). Ninguna es OCR. **Gravedad 3**: si el loop lee
"`max` no cuesta alertas fuertes" sin la etiqueta de sensor, adopta en V750 con un costo que existe.

## D5. Alertas MODIS que dependen del OCR

**VERIFICADO** con `d5_modis_ocr.py` (OCR con ALERTA, sensor MODIS, sin fila ALERTA_TERMICA de tabla del mismo
volcán a ±10 min):
- Antes de la caída (remoto `e489b42f` y nuestro snapshot del 10-05): **3** (Láscar 05-05 19:30 diurna 15 MW,
  03-19 01:55 y 03-04 07:15). Es lo que S149 frente B ya había dicho ("falso por 2 nocturnas").
- Hoy (remoto `9f628d55` y `latest_consolidado.csv`): **5**, todas Láscar: las tres anteriores más 04-18 01:50 y
  02-14 01:40, que entraron por la caída de D1. Nocturnas: 4. Desde marzo: 4 (3 nocturnas y 1 diurna).

El "son 4" es correcto con cualquiera de esas dos ventanas, pero el número **no es una propiedad de MIROVA**: sube
cada vez que el remoto pierde filas. CLAUDE.md del proyecto l. 1494 dice "0 alertas MODIS dependen del OCR,
medido S149" (verificado con `grep -n`). **Gravedad 2**: MODIS sólo tiene sustrato en Láscar; 4 o 5 alertas sobre
~77 desde marzo.

## D6. "86 % de cobertura nocturna en enero"

**VERIFICADO el mecanismo** con `d6_cobertura_enero.py` (misma noche y `noche_id` que
`experiments/_s139_audit/bases_mirova_v1/comun.py`). El script de S139 (`02_completitud_mensual.py`) usa como
denominador `días observados × 11 volcanes`, con Tupungatito, que no tiene filas antes del 2026-02-14, y cuenta
desde el 10-ene, día cuyo scraper arrancó de tarde (sin noche). Las dos cosas son del denominador.

| enero (desde el 11), noche | 11 volcanes | sin Tupungatito |
|---|---|---|
| MODIS | 90,0 % (208/231) | **99,0 %** (208/210) |
| VIIRS 375 | 89,6 a 90,5 % | **98,6 a 99,5 %** |
| VIIRS 750 | 86,6 a 87,0 % | **95,2 a 95,7 %** |

(el rango es snapshot del 10-05 contra remoto de hoy; la caída de D1 se llevó filas de enero). Con el 10-ene en
el denominador sale exactamente el 86,0 % de MODIS de S139 (208/242). Febrero sin Tupungatito: 98,2 a 99,6 %.
**PARCIAL**: "97 a 100 %" es optimista para VIIRS 750 (95 %); F3 da 97,1 % y no encontré la diferencia de tres
noches. La conclusión práctica (enero no está "incompleto" al 86 %) se mantiene. Control: marzo da 99 a 100 %
con los dos denominadores. **Gravedad 2.**

## D7. El record no guarda perfil ni código

**VERIFICADO.** Barrí los 45 JSON de `data/mirova_equivalent/` (65.206 records, 81 claves distintas, nivel
superior sólo `volcano`, `updated`, `records`). Claves que podrían ser procedencia: `product_version` (65.206,
valores `standard` 64.906 y `nrt` 300: es el producto L1B de NASA, no el código), `processed_utc` (4.370) y
`first_processed_utc` (117). Ninguna clave de perfil, sha de git, versión del pipeline ni flags.
`pipeline/store.py:499` escribe sólo la hora. El perfil sólo se infiere por el directorio (`data_subdir`), y el
código sólo por la historia git del commit que escribió el JSON, que no sirve para reprocesos locales.
**Gravedad 3**: un loop que reprocesa y compara brazos no puede saber, mirando un record, con qué se produjo.

## D8. `ENABLE_TEST1_NULL_CORRECTED`

**VERIFICADO** (trazado por la lectura, A89): `pipeline/profile.py:301` lo lee de la clave
`enable_test1_null_corrected`; ningún perfil YAML la declara. El parámetro `null_corrected` existe en
`compute_test1_nti` (`test1_integrated.py:220`) y `compute_test1_mir` (`:361`), con default `False`. Los tres
llamadores lo omiten: `process_modis.py:743-751`, `process_viirs.py:1112-1121` y `:1129-1139`,
`process_viirs_mod.py:734-742`. No hay `**kwargs`, `partial` ni `getattr` sobre el perfil en `pipeline/`
(`grep` de `null_corrected`, `NULL_CORRECTED`, `partial(` y `getattr(.*profile`). Un brazo que lo encienda
corre el Test 1 idéntico al control. Matiz: en los brazos con el Test 1 apagado (B y F de S147 a S150) el flag
es irrelevante de todos modos. **Gravedad 3**: es un día de A/B que no mide nada (A118).

## D9. El fondo por vecinos y la nube

**Código: VERIFICADO.** `vrp_regimes.neighbor_mean_radiance_background` (l. 110-176) promedia los vecinos con
`usable = ~alert & isfinite(ventana)`: sólo excluye alertados y NaN. Lo llaman `process_viirs.py:683-698`
(V375) y `process_viirs_mod.py:431` (V750). La máscara de nube (`process_viirs.py:827-832`) actúa sobre
`roi_mask` y `bg_mask`, no sobre la grilla `bt`, y además está en 0,0 K en producción
(`VRP_PROFILE=mirova_equivalent python -c ...` da `CLOUD_MASK_BT_K 0.0`, `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375
False`). Así que con D25 encendido un vecino nublado entra al fondo.

**"El paper lo exige": PARCIAL**, verificado renderizando las páginas a imagen con PyMuPDF:
- **Coppola et al. 2014, IJRS 35:3403-3426, p. 3412** (`documentacion/coppola2014_ijrs_strombolian_...pdf`,
  índice 11): "L4bk is estimated from the arithmetic mean of all pixels surrounding the alerted one (or around
  the alerted cluster) not contaminated by clouds", con `cloud = [BT11 < 255]` (condición 4, noche, Giglio
  2003). **Sí lo exige.** Es la cita de `AUDIT_S128.md:553`.
- **Coppola et al. 2016a, SP 426, p. 7, ec. 6** (`documentacion/sp426.5.pdf`, índice 7), el canon MIROVA que cita
  el propio código: "the arithmetic mean of all the pixels surrounding the active one (or around the active
  cluster)", y a continuación que las nubes pueden introducir error y que los datos afectados se descartan **a
  posteriori por inspección visual**. **No exige** la exclusión automática.
No revisé Fernandina 2025 ni Campus 2024, que el docstring también cita. **Gravedad 2**: el flag está apagado; la
exclusión de 255 K es un brazo legítimo a probar, pero no es "fidelidad literal al paper MIROVA" sino a su
precursor de 2014.

## D10. El scraper y la coma de los miles

**VERIFICADO.** `scraper.py:140` en HEAD: `vrp = float(cols[3].text.strip())`, sin quitar comas; todo el bucle de
filas está dentro de un `try` cuyo `except` (l. 211-212) sólo registra el error, así que el ciclo entero cae y
no se escribe ninguna fila de ningún volcán en esa corrida. `gh issue view 19 -R MendozaVolcanic/Mirova-v1`:
**OPEN**, creado 2026-09-14, punto 2 describe exactamente esto. La bitácora remota (`bitacora_robot.txt`, sha
`9f628d55`) tiene **36** `could not convert string to float`: 21 el 2026-06-15 (`'2,178.53'`) y 15 el
2026-07-08 (`'1,357.39'`). Que `latest.php` use coma de miles lo infiero del error, no lo vi en la página.
**Gravedad 3**: la referencia pierde la tabla justo en las erupciones grandes (quedan sólo en el OCR); no afecta
al tablero de VRP Chile, que no depende del scraper para detectar.

## Hallazgos propios

**P1. Dos "referencias MIROVA" del repo discrepan desde el 06-oct, y la buena se va a sobrescribir.**
`latest_consolidado.csv` (raíz, sincronizado cada hora, post-caída) y
`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (pre-caída, 41.328 filas) difieren en las
207 filas. Los scripts de S149 y `auto_audit_weekly.py` leen el snapshot; `clasificacion_referencia.py` lee la
raíz. Y `audit-weekly.yml:55-56` reescribe el snapshot desde el remoto en su próxima corrida, con lo que la copia
buena desaparece del árbol (queda en git, `80b358f6d`). Toda referencia que se congele desde el 06-oct (el A/B
`vent_anchored` contra `vrp_max`, un despacho MODIS) nace sin esas alertas. Arreglo barato: reponer las llaves
perdidas desde `e489b42f` antes de congelar, y guardar en el congelado el sha del remoto. **Gravedad 4.**

**P2. Las caídas son más y más grandes de lo que circula.** Cinco episodios como piso (enero 37, abril, 25-ago 202,
26-ago 186, 06-oct 207), ninguna fila recuperada por el remoto. A119 y `calidad_referencia_mirova.py` no lo
tienen como hito. **Gravedad 3.**

**P3. La clase de MIROVA del CSV no es de MIROVA.** Toda la columna "Clasificacion Mirova" la calcula el scraper
desde el VRP (`volcanes.py:63`); cualquier análisis que la use como juicio de MIROVA mide la escala de Coppola
aplicada por nosotros. **Gravedad 2.**

## Lo que no verifiqué

- La caída del 23-abr llave a llave (sólo su tamaño; S139 la desglosó).
- Por qué F3 obtiene 97,1 % en V750 de enero y yo 95,2 a 95,7 %.
- El 119 de F3 con su propia vara y denominador (no corrí su script).
- Las citas de Fernandina 2025 y Campus 2024 del docstring de D25.
- Si `latest.php` imprime de verdad la coma (sólo el error del log).
