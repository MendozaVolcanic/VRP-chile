# Verificación de la investigación de MODIS en Chillán por cenit (S173): INFORME

## 1. Encabezado

- Fecha y hora del servidor (GitHub, cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`): 2026-11-03 01:15 UTC al empezar; 2026-11-03 01:30 UTC al cerrar. Disco al cerrar: C: 32 GB libres, D: 4,7 GB (no escribí en D:).
- Commit sobre el que medí: `origin/main` = `5de08ebf62d1ea092c485c0a030f323f2cbdcf2a` (copia por `git archive` en CARPETA/main_5de08eb/, con `COMMIT_ORIGEN.txt`); rama del auditor `origin/claude/s173-cenit-modis` = `f57972af692b396cb12851ea5e70ddc786843ee3`, un commit sobre ese main (sólo agrega `experiments/_s173_cenit_modis/` y `.github/workflows/s173-cenit-modis.yml`; sus archivos se extrajeron a la misma copia).
- Modelo y esfuerzo reales: Claude Fable 5.1 (claude-fable-5-1), esfuerzo medio (el que trae la sesión; no se me pasó `effort`).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/`. Dentro: `caminos.md` (sellado antes de abrir nada del auditor), `rerun/` (copia de los scripts e insumos del auditor con `SHA256_INSUMOS_COPIADOS.txt`, re-corridos sobre la copia de main), `v1_analisis_02.py`, `v2_estratos_03.py` y sus salidas, `v4_records_20261102_salida.txt`, `v6_probar_local_salida.txt`, `v7_mutaciones_salida.txt`, `v8_tmax_cirrus_salida.txt`, `hallazgos.csv`.
- Qué NO miré: no abrí `INFORME.md` del auditor (regla del verificador) ni los informes de `ver_v375/` y `ver_v750/`; no despaché el workflow ni usé credenciales; no reprocesé ningún gránulo (pyhdf no corre en Windows: los brazos K y V «por el pipeline» del arnés quedan SIN DATO acá); no leí los PDF de los papers; no medí VIIRS.

## 2. En una pantalla

1. Las seis afirmaciones se reproducen en el número: re-corrí 01, 02, 02b y 03 del auditor sobre la copia de main `5de08eb` y las salidas son idénticas byte a byte (diff vacío). El pareo es por pasada (`control_dt_max_s` 0 s en MODIS) y el cenit es `sensor_zenith_deg` del record.
2. Lo que NO se sostiene como está dicho: (a) el «0,014 sobre 30°» de FA es una mediana sobre 5 ceros de 10; condicional a detectar, FA baja la razón IGUAL bajo y sobre 30° (0,47 contra 0,465): la palanca del fondo de K con el cenit es el **recorte a cero** cuando ninguna celda alertada supera la mediana del anillo (5 de 10 pasadas oblicuas, 0 de 6 bajo 30°), no una magnitud que cae; (b) el Spearman −0,815 de NAT (afirmación 2) **cae dentro del rango del barajado del cenit dentro de cada volcán** ([−0,843; −0,241]), igual que el de K y el de todos los brazos: con este lote el cenit no se separa del volcán, y dentro de Láscar (n 8) ningún brazo sale del azar. El número es correcto; la conclusión sobre D17 no se puede extraer de este lote.
3. El arnés del PR #937 **nunca autentica** (`ablacion_cenit_modis.py` no llama a `pipeline.fetch.auth()` y `earthaccess.download` sin login devuelve `[]`): en el runner las 27 pasadas saldrían `no_bajado` y el job terminaría en rojo sin medir nada. No gasta credenciales indebidas ni pushea (A43, grupo propio, `contents: read`, sólo `EARTHDATA_TOKEN` confirmados), pero tal como está no sirve. Las dos mutaciones no atrapadas se reproducen (m2 anillo desde 0 km, m3 caja nativa toda sensible).
4. Producción con la vía el 2026-11-02 da 1,189 y 1,114 (n 2) y las filas de MIROVA de ese día están en el snapshot: CONFIRMADA. `03_ablacion.py` de S162 sólo recorre métodos de quitar duplicados del bow tie: CONFIRMADA.
5. Seguimiento fuera de mi eje con gravedad: el tablero oculta como «cirrus» todo record con `t_max_k` < 273,15 K y más de 10 MW (`frontend/index.html:1336`); la vía produce en las pasadas oblicuas celdas diluidas bajo 0 °C (6 de las 16 grillas) y el control X2 ya cayó en esa regla (2026-10-01 08:35, 11,4 MW, no publicado). Hoy ninguna V0 pasa de 10 MW con esa temperatura, pero un evento mayor sí lo haría.

## 3. Veredicto por afirmación

| # | afirmación del auditor | veredicto | número propio |
|---|---|---|---|
| 1 | FA hunde la razón sobre 30° de 1,075 a 0,014 (n 10) y bajo 30° de 0,926 a 0,47; pierde 5 de 16; anillo 7 a 8 K más tibio, sin tendencia con el cenit | CONFIRMADA EN PARTE | reproducido exacto (02 idéntico). Condicional a VRP > 0, FA/MIROVA es 0,47 (n 6, z<30) y 0,465 (n 5, z≥30): la caída oblicua son 5 ceros, uno a uno los de 02b con 0 celdas sobre el anillo (16/16 coinciden). anillo − fondo local: 8,22 / 7,28 K, Spearman −0,138 dentro de [−0,465; +0,479] |
| 2 | sin remuestreo (NAT) las protegidas sobre 30° caen de 0,992 a 0,52, Spearman −0,815; cenit y volcán confundidos | CONFIRMADA EN PARTE | reproducido exacto (03 idéntico, ver §5). Barajado dentro del volcán: NAT −0,815 en [−0,843; −0,241] (dentro); sólo Láscar (n 8): NAT −0,571 en [−0,738; +0,810] (dentro), medianas 1,246 / 0,561 (n 5 / 3). La confusión invalida la lectura de D17 con este lote |
| 3 | G5 (geolocalización de 5 km) reproduce la caída (0,699 / 0,171); halo y cúmulo no son palanca | CONFIRMADA EN PARTE | G5 reproducido; pero dentro de Láscar G5 da 0,699 / 0,921 (sube), y el 0,171 lo hacen las 3 de Chillán (0,07; 0,27; 0,00). FSH ≈ V0 medido (0,926 / 1,032 en 02). SC = V0 **por construcción**: las 16 grillas de 02 y las 13 pasadas con detección de 03 tienen un solo cúmulo 8-conexo (A116: ese cero no mide nada) |
| 4 | producción con la vía el 2026-11-02 da 1,189 y 1,114 a 41,4° y 52,0° | CONFIRMADA | records `via_codigo_mirova: true` con `pc.vrp_mw` 4,328 (z 41,41) y 12,823 (z 52,01); filas CONS de MIROVA 3,64 y 11,51 al mismo minuto; 4,328/3,64 = 1,189; 12,823/11,51 = 1,114. n 2, sin valor estadístico |
| 5 | `03_ablacion.py` de S162 sólo aísla el bow tie | CONFIRMADA | el bucle recorre `comun.ORDEN_METODOS` = `todos`, `A_centro_cubierto_ant`, `A_centro_cubierto_sig`, `A_huella_entera_ant`, `B_filas_borde`, `C_sin_det0` (`experiments/_s162_modis_bowtie/real/comun.py:46-47`), todos máscaras de píxeles a quitar antes de remuestrear (`mascara_quitar`, l. 173) |
| 6 | el workflow cumple A43, A71, grupo propio y no hace push; su prueba local pasa con dos mutaciones no atrapadas | CONFIRMADA EN PARTE | A43 (`'on'` string, `True not in wf`), sólo `workflow_dispatch`, `group: s173-cenit-modis`, `permissions: contents: read`, sin `git push`, sólo `EARTHDATA_TOKEN` y corte si viene vacío: CONFIRMADO leyendo el yml y con `yaml.safe_load`. Prueba local: 0 fallas en mi copia; mutaciones m2 y m3 no atrapadas: reproducido. **Pero el arnés no autentica** (VMODIS-01) y la prueba local no lo cubre |

## 4. Hallazgos

### VMODIS-01
- TÍTULO: El arnés del PR #937 nunca llama a `auth()`: en el runner no bajaría ningún gránulo y el job terminaría en rojo sin medir nada
- ARCHIVO:LÍNEA: `experiments/_s173_cenit_modis/ablacion_cenit_modis.py` (rama f57972af6), función `medir`, llamadas `P._bajar(l1b_short, jd, tmp)` y `P._bajar(geo_short, jd, tmp)` (copia en CARPETA/`_rama_ablacion_cenit_modis.py`, l. 118-119 del archivo extraído); `experiments/_s151_mxd03_etiquetas/probe_etiquetas.py:216-224` (`_bajar` → `earthaccess.search_data` + `pipeline.fetch.download_granules`, sin login) y `:243-246` (el `auth()` vive dentro de `main()`, que el arnés no llama); `pipeline/fetch.py:1086` (`earthaccess.download(...)`); `earthaccess 0.17.0, api.download`: `except AttributeError: logger.error("... You must call earthaccess.login() before you can download data"); return []`.
- QUÉ PASA: `earthaccess.search_data` consulta el CMR sin sesión y encuentra el gránulo; `earthaccess.download` sin `login()` no tiene `__store__`, atrapa el `AttributeError`, lo registra y devuelve `[]`; `download_granules` devuelve `[]` sin reintentar (no hay excepción); `_bajar` devuelve `None` y `medir` anota `estado: no_bajado` y sigue con la pasada siguiente. Las 27 pasadas salen `no_bajado`, `n_ok` = 0 y `main()` termina con `sys.exit(1)`. `grep -n auth` sobre el arnés da cero líneas; `pipeline/fetch.py` y `probe_etiquetas.py` no autentican a nivel de módulo (`grep -n '^auth()\|^earthaccess.login'` da cero).
- CÓMO SE VE EN EL DASHBOARD: invisible (el workflow no toca `data/`); lo que se pierde es la medición que decide la palanca.
- CÓMO REPRODUCIRLO: `grep -n "auth" C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/_rama_ablacion_cenit_modis.py` (sin resultado); `python -c "import inspect, earthaccess.api as a; print(inspect.getsource(a.download)[-700:])"`. Sin despachar: la rama no tiene todavía una corrida.
- CONFIANZA: CONFIRMADO en la lectura del código y de la biblioteca instalada (0.17.0, la misma versión que fija el yml); el comportamiento en el runner es SOSPECHA fuerte, porque no lo corrí.
- GRAVEDAD: 3 (no tuerce ninguna alerta; deja sin instrumento la decisión D17 contra D25, y el error aparecería como un run rojo que alguien podría leer como «NASA caída»).

### VMODIS-02
- TÍTULO: El «0,014 sobre 30°» del fondo de K es una mediana sobre ceros: condicional a detectar, el fondo de K baja la razón igual en todos los cenit (0,47); la palanca oblicua es el recorte a cero del exceso
- ARCHIVO:LÍNEA: `rerun/02_salida.json` leído por `v1_analisis_02.py` → `v1_analisis_02_salida.txt` (a) y (d); `pipeline/process_modis.py:1253` (`delta_L = np.maximum(hotpix_rad - L_bg, 0.0)`, el recorte que el brazo FA reproduce con `recortar=True`, `piezas.py:87-88`).
- QUÉ PASA: cuando el satélite mira de lado, las celdas que la vía alerta quedan diluidas (02b: T_max mediana 271,6 K sobre 30° contra 287,7 K bajo 30°) y en 5 de las 10 pasadas oblicuas ninguna celda alertada supera la mediana del anillo de 5 a 25 km (02b, `sobre_anillo` 0/n en exactamente esas 5; 16 de 16 coinciden con FA = 0). Con el fondo de K esas pasadas dan VRP 0 (recorte), y el 0,014 es la mediana de [0, 0, 0, 0, 0, 0,03, 0,35, 0,46, 0,47, 0,59]. En las 5 oblicuas que sobreviven la razón es 0,465, la misma que las 6 de bajo 30° (0,47): el anillo tibio (8,2 / 7,3 K sobre el fondo local, sin tendencia) resta lo mismo en todos los cenit.
- CÓMO SE VE EN EL DASHBOARD: es el mecanismo por el que K no publicó 4 de las 5 alertas de MIROVA sobre 57° (01_salida: 2026-09-29, 10-12, 10-15, 10-25, todas `pub 0`); con la vía se publican.
- CÓMO REPRODUCIRLO: `python -B C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/v1_analisis_02.py C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/rerun` (secciones (a) y (d)).
- CONFIANZA: CONFIRMADO (medido sobre la salida re-corrida).
- GRAVEDAD: 2 (no cambia el veredicto de que el fondo es palanca; cambia QUÉ parte del fondo: el recorte, no la mediana. Si alguien adoptara «fondo de K sin recorte» creyendo que el problema es la magnitud, se equivocaría de pieza).

### VMODIS-03
- TÍTULO: En el lote S162 el cenit está confundido con el volcán y el barajado estratificado lo muestra: ningún brazo, NAT incluido, sale del rango del azar; la conclusión sobre D17 no se puede extraer de ese lote
- ARCHIVO:LÍNEA: `v2_estratos_03.py` → `v2_estratos_03_salida.txt` (sobre el 03_salida.json re-corrido) y `v2_estratos_03_salida_auditor.txt` (sobre el del auditor, idéntico).
- QUÉ PASA: las 11 protegidas son 8 de Láscar (cenit 2,4 a 40,5°) y 3 de Chillán (50,5 a 58,2°). Barajando el cenit sólo dentro de cada volcán (200, semilla 173), el rango del azar para NAT es [−0,843; −0,241] y el observado −0,815 cae dentro; lo mismo K (−0,788 en [−0,825; −0,228]), G5, FA y todos. Dentro de Láscar (n 8) NAT da −0,571 en [−0,738; +0,810] con medianas 1,246 (n 5) y 0,561 (n 3); NAT/V0 (independiente de MIROVA) da −0,643 en [−0,738; +0,762]. Las dos pasadas de Chillán donde NAT da 0 (57,6° y 58,2°) son las que deciden el 0,52. Control positivo del instrumento: cos(z) sobre los cenit de Láscar da Spearman −1,000.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/v2_estratos_03.py C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/rerun/03_salida.json C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/v2_estratos_03_salida.txt`.
- CONFIANZA: CONFIRMADO. El auditor ya lo advierte en su propia salida («el cenit está confundido con el volcán»); lo que agrego es la medida de cuánto: todo.
- GRAVEDAD: 3 (si el proyecto tira de D17 citando el −0,815, la cita no sostiene la decisión; el instrumento que sí separa es el workflow sobre las 27 pasadas de Chillán, que hoy no corre por VMODIS-01).

### VMODIS-04
- TÍTULO: «El cúmulo no es palanca» no está medido: SC = V0 por construcción en las 16 grillas y en las 13 pasadas del lote, todas con un solo cúmulo 8-conexo
- ARCHIVO:LÍNEA: `v1_analisis_02_salida.txt` (b); `v3` dentro de este informe (§5); `piezas.py:94-99` (`cumulo` = componente del más radiante) y `:123` (sólo en SC y FA_SC).
- QUÉ PASA: SC recorta la suma al cúmulo 8-conexo del alertado más radiante; si la máscara ya es un solo cúmulo, SC devuelve V0 exacto. Conté los cúmulos en las celdas V0: 1 en las 16 grillas de 02 y 1 en las 13 pasadas con detección de 03. «SC: VRP distinto de V0 en 0 de 16» y «0 de 403» son ceros que el instrumento no podía dejar de dar (A116). La prueba local (`probar_local.py`, «SC = V0 con un solo cúmulo») también es un caso de igualdad obligada, no un control de que SC pueda cambiar algo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/v1_analisis_02.py C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/rerun` (sección (b)).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1 (la afirmación es verdadera en esta muestra, pero no vale como cierre del cúmulo como pieza).

### VMODIS-05
- TÍTULO: G5 «reproduce la caída» sólo por las 3 de Chillán: dentro de Láscar la geolocalización de 5 km sube la razón sobre 30°
- ARCHIVO:LÍNEA: `v2_estratos_03_salida.txt`, bloque «solo Lascar» y «Chillan solo».
- QUÉ PASA: G5 (la vía con la geolocalización interpolada de 5 km de K, `piezas.py:264-267`) baja la razón en todos los cenit en Láscar bajo 30° (0,699 contra 1,074 de V0) pero sobre 30° da 0,921 (n 3); el 0,171 del tramo oblicuo lo ponen las 3 de Chillán (V0 1,10 / 1,69 / 0,84 → G5 0,07 / 0,27 / 0,00). Como en Chillán la geolocalización corrida (S151, `_interp_geo`) mueve 1 a 3 km y el domo es un foco pequeño, es compatible con que G5 pierda el cráter en Chillán, no con una ley por cenit.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el mismo comando de VMODIS-03.
- CONFIANZA: CONFIRMADO en el número; la lectura física es SOSPECHA.
- GRAVEDAD: 2.

### VMODIS-06
- TÍTULO: La prueba local del arnés no atrapa dos mutaciones que cambian el fondo de K (anillo desde 0 km) y la caja del brazo nativo (todo sensible): reproducido
- ARCHIVO:LÍNEA: `v7_mutaciones_salida.txt` (re-corrida de `05_mutaciones_prueba_local.sh` sobre mi copia): m2 0 fallas, m3 0 fallas; m1 3 fallas y m4 1 falla (control de que el script muta).
- QUÉ PASA: en la escena sintética el anillo desde 0 km y la caja toda sensible dan el mismo VRP que sin mutar, así que la prueba no distingue un FA mal armado ni una caja nativa mal armada. Las mutaciones m1 y m4 sí fallan: el instrumento de mutación funciona.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `bash C:/Users/nmend/vrp-wt/s173_cenit/modis/05_mutaciones_prueba_local.sh C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/main_5de08eb`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

## 5. Re-corridas de los scripts del auditor (SCRIPT:SALIDA)

Pregunta 1 de cada re-corrida: si la salida del auditor dependiera de una copia local distinta o de un insumo cambiado, el diff lo vería. Pregunta 2: el diff de un archivo vacío contra sí mismo daría «idéntico» igual, así que cada diff va acompañado del `rc` del script y del tamaño de la salida.

| script | sobre | resultado | diff contra el auditor |
|---|---|---|---|
| `01_pasadas_y_salidas_existentes.py` | copia main 5de08eb + `s02_v_main_pasadas.csv` del auditor | rc 0 | `01_salida.txt` IDÉNTICO |
| `02_ablacion_grillas_chillan.py` | 512 grillas en `D:/vrp-trabajo/temporales/s170_ab*/` (16 de Chillán con alerta) | rc 0, 8 s | `02_salida.txt` IDÉNTICO |
| `02b_temperaturas_grilla.py` | ídem | rc 0 | `02b_salida.txt` IDÉNTICO |
| `03_ablacion_nativa_lote.py` | lote `C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181` (403 evaluables) | rc 0, 285 s (el auditor: 315 s); `03_salida.json` 886.878 bytes, el mismo tamaño que el del auditor | `03_salida.txt` IDÉNTICO salvo la línea del tiempo («315 s» contra «285 s»); `v2_estratos_03.py` da lo mismo sobre los dos JSON |
| `03b_controles_detalle.py`, `03c_fondo_qhull.py` | el 03_salida.json re-corrido / el lote | rc 0 | IDÉNTICOS (las 6 pasadas donde V0 y el port del lote difieren en VRP se explican por la triangulación Qhull anterior a la regla de empates de S163, 6 de 6) |
| `probar_local.py` (rama) | copia main + rama | rc 0, 0 fallas, 16 grillas comprobadas | igual al `probar_local_salida.txt` del auditor |
| `05_mutaciones_prueba_local.sh` | ídem | m2 y m3 con 0 fallas | igual |

Lo que NO re-corrí: `s02_pareo_por_pasada.py` de S172 (produce el CSV de partida; lo verifiqué por otro camino: las 2 filas del 2026-11-02 contra el CSV de MIROVA a mano, y la lista de la rama contra `01_salida.json`, 27 de 27 iguales).

## 6. SEGUIMIENTOS (fuera de mi eje)

- S-1. **La regla de cirrus del tablero puede ocultar alertas reales de la vía en pasadas oblicuas.** `frontend/index.html:1336-1340` (`isCirrusArtifact`: `t_max_k < 273.15` y `mirovaEqVrp > 10` → artefacto, salvo `_mirova_confirmed`, que el tablero pone en `:1572-1580` al cruzar con el CSV de MIROVA). La vía produce en las oblicuas celdas diluidas bajo 0 °C (6 de las 16 grillas, `v8_tmax_cirrus_salida.txt`); hoy ninguna V0 pasa de 10 MW ahí, pero el control X2 ya cayó en la regla (2026-10-01 08:35: 11,44 MW, `publica` 0, `v1_analisis_02_salida.txt` (c)). Un evento de Chillán de 2× el tamaño del 2026-10-01 a 50° quedaría en el tablero como cirrus. Los dos records de producción con la vía (2026-11-02) tienen `t_max_k` 274,66 y 284,18 K: no caen. CONFIANZA: CONFIRMADO el mecanismo; SOSPECHA que ocurra. Gravedad 3 (sí tuerce una alerta si pasa).
- S-2. `piezas.py` de la rama y la copia del auditor son idénticos salvo CRLF/LF (`diff --strip-trailing-cr` vacío; `diff` crudo marca las 284 líneas): el mismo autocrlf de S163. Gravedad 1.
- S-3. En el yml, `Upload artifact` con `if: always()` e `if-no-files-found: error`: si el paso «Token presente» corta antes de crear `out/`, el upload falla también y el run muestra dos errores por uno. Cosmético. Gravedad 1. SOSPECHA (no corrido).

## 7. VERIFICADO LIMPIO

- Pareo por pasada, no por noche: `s02_pareo_por_pasada.py` parea con `bp.parear(..., r["dt"])` a `TOL_S = VENTANA_S` (`scripts/banco_paridad.py:78,253`) y el resumen del auditor trae `control_dt_max_s: 0.0` en MODIS (`rerun/… s02_v_main_resumen.json`). Vara: la definición de «razón» de la tarea.
- Cenit = `sensor_zenith_deg` del record (`banco_paridad.cargar_nuestros`, l. 286; `process_modis.py:1760-1764`, `observation_geometry` en el punto reportado, desde la grilla de 5 km). Vara: definición de «cenit» de la tarea.
- Fidelidad de FA al fondo de K: `t_bg` del anillo en la grilla contra `t_bg_k` del record, n 16, mediana −0,02 K, rango [−2,10; +0,81] (02, re-corrido). `compute_bg_stats` (`pipeline/detection_context.py:1042-1098`) es mediana sobre `bg_mask` sin NaN, con `ENABLE_TEST1_K1_BG_EXCLUDE` leído de `profile.py:746` (default False). Vara: el código de K de hoy.
- Insumos del auditor contra el remoto: `modd_resultado_f4.json` sha256 `312e2050…` = `origin/loop/activo:experiments/_s172_chillan/auditor/modd_resultado_f4.json`; `pasadas_chillan_modis.json` de la rama = los 27 (dt, sensor, z, VRP de MIROVA, gránulo) de `01_salida.json` re-corrido, con 16 razones V de la lectura.
- Citas `archivo:línea` del `hallazgos.csv` del auditor: `process_modis.py:717` (`bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)`) y `:1253` (`delta_L = np.maximum(...)`), `mirova_v750_codigo.py:198` (`def remuestrear_grilla`), `MIROVA_DIVERGENCES.md:2861` (D25) y `:3034` (D28): las cinco calzan en main 5de08eb.
- Workflow: `yaml.safe_load` da claves `['name', 'on', 'concurrency', 'jobs']`, `'on' in d` True, `True in d` False; sólo `workflow_dispatch`; `group: s173-cenit-modis`, `cancel-in-progress: false`; `permissions: contents: read`; `grep -i 'push|gh api|git commit|schedule|cron'` sólo en comentarios. El brazo K y V del arnés escriben con `store.append_record` en un `TemporaryDirectory` con `store.DATA_DIR` parchado (`probe_etiquetas.py:109-111`): no toca `data/`.
- Brazo sin cambio = producción (A110, nulo del arnés): en 02, V0 recalculado sobre la grilla capturada da la misma máscara en 16 de 16 y |ΔVRP| máx 4,45e-4 MW contra la captura del A/B de MOD-D, y V0/MIROVA = `razon_b` de la lectura en 16 de 16; en 03, V0 = port `fisica` del lote en npix 403 de 403 y en VRP a 1e-3 en 397 de 403 (las 6 restantes, 03c). X2 = 2 × V0 en 16/16 y 13/13 sin mover celdas. Vara: el record del A/B y el port del lote, no el record de producción (que con K no es comparable con la vía); el record de producción con la vía sólo existe para las 2 pasadas del 2026-11-02 y en ésas el arnés usa el record como control, pero no se pudo correr acá (SIN DATO).
- Producción 2026-11-02: 2 de 1.388 records MODIS de Chillán con `via_codigo_mirova: true`, ambos `codigo_sha 79f410697`, `processed_utc` 2026-11-02T20:29 Z; el flag `enable_modis_codigo_mirova: true` está en `pipeline/profiles/mirova_equivalent.yaml:38` y se lee en `profile.py:909`.

## 8. SIN DATO

- Los brazos K y V «por el pipeline» del arnés (`calculate_vrp` sobre el gránulo): sin pyhdf en Windows no se pueden correr; sólo se verificó que el arnés no autentica.
- El tiempo del job (estimado < 30 min por el auditor): sin corrida.
- Si la caída de NAT dentro de Láscar sobre 30° (3 pasadas) es cenit o azar: n 3; el lote no alcanza.

## 9. FUERA DE ALCANCE

- VIIRS 375 y 750 (otros verificadores).
- La corrección de cualquiera de los hallazgos (regla A45; se decide aparte).
- `INFORME.md` del auditor (no abierto a propósito).
