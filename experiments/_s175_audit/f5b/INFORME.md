# F5b S175: la lámina Latest10NTI de MIROVA como vara de posición después del 2026-09-22

> ⚠️ S175 V5B (marca A113, `experiments/_s175_audit/v5b/VERIFICACION.md`): lo de abajo es el texto del auditor. La conclusión de 351 no se sostiene: el selector de píxel borra la mancha saturada (V5B-01) y las clases no miden identidad del foco (V5B-04, nulo 73 y 77 %). Los veredictos vigentes están en `docs/AUDIT_S175.md` §11.4.

## 1. Encabezado

- Horas (reloj de la sesión en UTC; no hice llamadas a la API de GitHub, 0 de 10, así que no tengo cabecera `Date` propia; la de la ola 0 decía `Sat, 07 Nov 2026 04:10:45 GMT`): primera parte `Sun Nov  8 04:32:32 UTC 2026` a `05:23:30 UTC` (parada por disco); segunda parte, tras el reinicio del computador y el aviso de quien orquesta, `13:27:09 UTC` a `13:52:25 UTC`.
- Commit medido: base `752d348bc67190e53b610989877e2405d238a1bc`. Universo de aciertos, posiciones nuestras (`our_lat/our_lon` = `final_hotspot`) y distancias de la tabla tomados de `experiments/_s175_audit/f5/i2_pares.csv` (F5 los calculó sobre esa base con el predicado del tablero en node). `volcanoes.yaml` de la instantánea `C:\Users\nmend\vrp-temporales\s175_audit\main\`. Records de Láscar del árbol `C:\Users\nmend\vrp-temporales\s175_audit\f1\root_base\data\mirova_equivalent\Lascar.json` (datos de `e75a7d52d`).
- Modelo y esfuerzo: Fable 5.1 como subagente del Agent tool. El pedido fue `effort: high`; la etiqueta literal de mi contexto dice `reasoning_effort 25`. Si el high llegó: SIN DATO.
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5b\`. Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\f5b\` (145 MB al cerrar: 440 láminas en `png\`, 1 en `png_p9\`, 28 TIF en `tif_ref\`, 11 en `tif_val\`).
- Prompt: `C:\Users\nmend\vrp-temporales\s175_audit\prompts\f5b.txt`, sha256 `cdc4ffb869a63cff87903dff1bfaeb78ee47240366479bfa798e32989cb3e025` (coincide).
- Disco. Primera parte: C: pasó de 4,7 GB libres (04:32) a 2,83 GB (~05:10), con mi temporal en 6,2 MB; me detuve como manda la tarea con 2 de 305 aciertos clasificados y lo escribí. Quien orquesta informó después que era el archivo de paginación de Windows y que el computador se reinició; en la segunda parte C: tenía 16,5 GB y cerró con 15,6 GB. La guardia de `p8_clasificar.py` (parada bajo 3,2 GB o tras 1,2 GB bajados) no volvió a saltar.
- Bajadas: sólo láminas y TIF sueltos por `raw.githubusercontent.com` (md5 cotejado con los índices en todas); ningún pull ni clone de `mirova-tif-archive`. Sin git (ni lecturas), sin subagentes, sin workflows. Un proceso pesado propio a la vez (los tramos de `p8` corrieron en serie, de 590 s cada uno).
- Instrumento (todo en CARPETA, con su salida al lado): `p0_indices.py` (pareo TIF y lámina en los índices), `p1_georef.py` (primera georreferencia; `_v0` con el recorte entero del marco), `p2_fase_grilla.py` (fase por columnas duplicadas: negativo), `p3_regla_fija.py` (regla fija por correlación subpíxel, uno afuera), `p4_ocr.py` (etiquetas), `p5_universo.py` (universo post 22-sep), `p6_tif_referencia.py` (grilla prestada y estabilidad; `_v0` con la colisión de nombres), `p7_mas_casos.py` (validación con la biblioteca, 7 MODIS y los 4 de F5; `_v0` sin búsqueda de panel), `f5b_lib.py` (biblioteca), `p8_clasificar.py` (clasificación reanudable; salidas `p8_clasificar_t1` a `_t6_max8.out.txt`, `p8_clases.json`, `p8_clases.csv`, `p8_ocr_cache.json`), `p9_lascar_modis.py`, `p10_cobertura_laminas.py`, `p11_hallazgos_csv.py`, `p12_resumen.py` (tabla por volcán y sensor), `p13_estratos.py` (lectura de los (iv) y los (iii)).
- Qué NO miré, para que mi silencio no se lea como «todo bien»: las láminas «VRP», «logVRP» y «Dist» (sólo Latest10NTI); el valor de NTI que codifica el gris (sólo posición); la identidad del foco antes del 22-sep fuera de los casos de validación; nuestros píxeles secundarios (uso sólo el punto que publicamos, `our_lat/our_lon` de F5; «mismo cúmulo, otro píxel» no lo puedo separar de «otra fuente»); las láminas de Villarrica, Llaima y Copahue (sin aciertos post 22-sep); por qué el archivo dejó de capturar TIF y por qué le faltan días de láminas; qué punto usa MIROVA como origen de su `Distancia_km` (sección 3, hallazgo 352).

## 2. En una pantalla

1. **La lámina VIIRS sí sirve de vara de posición, con precisión de una celda y con un control que decide caso a caso.** Regla fija de recorte (imagen de 151 px, 1,5 px a la derecha del centro del marco, grilla prestada del TIF del mismo volcán y sensor, idéntica de junio a septiembre): el píxel más claro del panel cae a 0 o 1 celda del máximo del TIF en los 4 casos de F5 (0,0 / 0,37 / 0,0 / 0,0 km; tolerancias 0,75 y 1,5), validado uno afuera (4 de 4), correlación panel contra TIF 0,992 a 0,994. En MODIS no valida (hallazgo 354). Isluga 2026-09-22 05:42 da por lámina lo mismo que F5 por TIF: MIROVA a 2,01 km de nuestro punto, clase (iii).
2. **Clases de los 305 aciertos post 22-sep (2026-09-22 05:42 a 2026-11-06 05:48), 141 protegidas.** VIIRS 375 (214): 110 (i), 6 (iii), 98 (iv). VIIRS 750 (67): 47 (i), 3 (iii), 17 (iv). MODIS (24, sin validar): 15 (i), 6 (iii), 3 (iv). Chillán en erupción: VIIRS 375 46 (i), 1 (iii), 22 (iv) de 69; VIIRS 750 44 (i), 3 (iii), 8 (iv) de 55; MODIS 15 (i), 6 (iii), 2 (iv) de 23. Protegidas: 95 (i), 10 (iii), 36 (iv). Mediana de la distancia entre el píxel de MIROVA y nuestro punto en los (i) y (iii) VIIRS: 0,29 km (p90 1,01).
3. **Hallazgo principal (351): cuatro protegidas VIIRS de Chillán son (iii)**: en la misma pasada, el píxel más claro de MIROVA está a 1,0 a 2,5 km del punto que publicamos: VIIRS 375 2026-10-18 05:06 (21,25 MW, 1,02 km, píxel muy prominente) y VIIRS 750 2026-10-29 06:42 (29,35 MW, 2,16 km, prominente), más 2026-10-10 06:54 (15,26 MW, 1,83 km) y 2026-10-16 06:42 (14,02 MW, 2,54 km) con píxel poco prominente. Otras 6 protegidas MODIS de Chillán salen (iii) a 3,0 a 4,2 km pero MODIS no está validado (SOSPECHA). Si es otra fuente u otro píxel del mismo cúmulo no lo puedo separar con el punto único que publicamos.
4. **Los (iv) tienen dos caras.** En los volcanes con alertas débiles (Isluga 36 de 43, Tupungatito 11 de 14, Chaitén 8 de 9, Láscar VIIRS 375 6 de 23, Caulle 13 de 32) el píxel más claro del inner no es la anomalía (3 a 4 km de la tabla, prominencia negativa en la mayoría): la vara no alcanza y el control lo dice. En Chillán, en cambio, 22 de 22 (iv) VIIRS 375 y 8 VIIRS 750 fallan el control por poco: la mancha saturada cae en la celda central (0,02 km del centro de MIROVA) y la tabla dice 0,84 a 1,35 km; nuestro punto queda a 0,36 km (mediana) de esa mancha. En 18 + 6 de ellos la posición es compatible con (i) y el control falla por menos de una celda extra (hallazgo 352: qué origen usa MIROVA para su distancia es SOSPECHA).
5. **Dos alertas MODIS de Láscar y una protegida MODIS de Chillán no tienen lámina** (hallazgo 353): el archivo no capturó láminas MODIS del 23 al 30-sep ni del 8 al 11-oct en ningún volcán. La lámina MODIS redondea el VRP a entero y pinta gris una alerta de 0,29 MW (hallazgo 355).

## 3. Hallazgos (de peor a menos grave)

### 351
- TÍTULO: Cuatro protegidas VIIRS de Chillán son (iii): en la misma pasada, el foco de MIROVA está a 1,0 a 2,5 km del punto que publicamos
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `p8_clasificar.py` → `p8_clases.csv` (filas con `clase` iii), `p13_estratos.out.txt` (sección «(iii) por prominencia»). Origen de nuestro punto: `final_hotspot_lat/lon` del record (columnas `our_lat/our_lon` de `experiments/_s175_audit/f5/i2_pares.csv`).
- QUÉ PASA: en una erupción el calor puede estar en el cráter o en un flujo; el recall por noche dice que vimos lo que MIROVA vio, pero no mira dónde. Con la lámina georreferenciada (vara validada a 1 celda en VIIRS, sección 4), el píxel más claro de MIROVA dentro del inner, que además reproduce la `Distancia_km` de la tabla (control), queda a más de la tolerancia (0,75 km en 375 m, 1,5 km en 750 m) de nuestro punto en: Chillán VIIRS_NOAA21 2026-10-18 05:06 (21,25 MW; MIROVA a 1,02 km de nuestro punto; prominencia del píxel +82 niveles sobre el p99 del panel; tabla 1,35 km, medido 1,20), VIIRS_NOAA21_750 2026-10-29 06:42 (29,35 MW; 2,16 km; prominencia +50; tabla 2,37, medido 2,27), VIIRS_NOAA20_750 2026-10-10 06:54 (15,26 MW; 1,83 km; prominencia −10) y 2026-10-16 06:42 (14,02 MW; 2,54 km; prominencia −23). Los dos con prominencia negativa eligen un píxel que no destaca en el panel entero: SOSPECHA de elección débil. Fuera de Chillán, (iii) no protegidas: Isluga 2026-09-22 05:42 (0,41 MW, 2,01 km, igual que por TIF en F5), Lastarria 09-24, 10-02 y 10-22 (0,12 a 0,18 MW, 1,1 a 1,4 km; patrón de F5 302) y Tupungatito 09-28 (0,09 MW, 10,1 km, prominencia −57: elección débil). Universo: 305 aciertos del 2026-09-22 al 2026-11-06, base.
- CÓMO SE VE EN EL DASHBOARD: el operador ve la alerta de Chillán en el punto que publicamos; MIROVA la marcó 1 a 2,5 km más allá, en la misma pasada. Invisible en el recall.
- CÓMO REPRODUCIRLO: `cd C:\Users\nmend\vrp-temporales\s175_audit\f5b && python -I "<CARPETA>\p8_clasificar.py"` (reanuda desde `p8_clases.json`; para rehacer, borrarlo) y `python -I "<CARPETA>\p13_estratos.py"`. Casos: Chillán VIIRS_NOAA21 2026-10-18 05:06 UTC (lámina `ChillanNevadosde_20261018_070912_VIIRS375_Latest10NTI.png`, panel 1) y VIIRS_NOAA21_750 2026-10-29 06:42 UTC (`ChillanNevadosde_20261029_095820_VIIRS750_Latest10NTI.png`, panel 1).
- CONFIANZA: CONFIRMADO para la medición (posición del píxel de MIROVA a 1 celda, control de distancia superado). SOSPECHA en la lectura «otra fuente»: puede ser otro píxel del mismo cúmulo (F5 302 contó 22 así en Chillán por radio); no tengo nuestra extensión de píxeles en este instrumento.
- GRAVEDAD: 3. En erupción, 1 a 2,5 km separa cráter de flujo; y el recall cuenta estas pasadas como «vimos lo mismo».

### 352
- TÍTULO: En Chillán el control de distancia falla por poco en 30 protegidas: la mancha de MIROVA cae en la celda central y la tabla dice 0,84 a 1,35 km; el origen de la `Distancia_km` de MIROVA no es el centro de la grilla, o el píxel alertado no es el más claro
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `p13_estratos.out.txt` (sección «(iv) por control fallido», Chillán), `p8_clases.csv` (`motivo_iv` «el píxel más claro no reproduce la distancia de la tabla», `d_png_mirova_center_km` 0,018); `volcanoes.yaml` de la base: `NevadosDeChillan` `mirova_center` (−36,86483, −71,38068) y vent (−36,863, −71,377), a 0,39 km.
- QUÉ PASA: en Chillán la anomalía satura varios píxeles (mancha mediana 3 px, p90 9 px en VIIRS 375; 6 y 16 en VIIRS 750) y el centro de la mancha cae en la celda central de la grilla (0,018 km del centro de MIROVA) en 22 de 22 (iv) VIIRS 375, mientras la tabla da 0,84 (18 veces), 0,53, 1,06, 0,95, 1,19 y 1,35 km: todas distancias de la grilla (36 de 36 valores distintos de la tabla en VIIRS 375 son sqrt(i² + j²) por celda), nunca 0. Es decir, el píxel que MIROVA reporta nunca es la celda central, aunque la mancha sí lo sea. Dos lecturas posibles, ambas SOSPECHA: MIROVA mide su distancia desde un punto que no es el centro de la grilla (la cumbre o el cráter activo; el vent de `volcanoes.yaml` está a 0,39 km del centro), o reporta el píxel de mayor VRP y no el centro de la mancha saturada. Consecuencia: el control pre-registrado (± max(tol, 1 celda) = 0,75 km) falla por 0,07 a 0,6 km y manda a (iv) 22 protegidas VIIRS 375 y 8 VIIRS 750 cuya mancha está a 0,36 km (mediana, máximo 1,23) de nuestro punto; 18 + 6 de ellas fallan por menos de una celda extra y tienen nuestro punto dentro de la tolerancia. En los 46 (i) de Chillán VIIRS 375 el mismo desajuste existe (|medido − tabla| mediana 0,46 km) pero cabe en la tolerancia. F5 (hallazgo 302) usó esa misma `Distancia_km` contra el centro de MIROVA como vara de radio.
- CÓMO SE VE EN EL DASHBOARD: invisible. Afecta a quien use la `Distancia_km` de MIROVA como posición (F5 302, banco `frac_radio_a_2km`).
- CÓMO REPRODUCIRLO: `python -I "<CARPETA>\p13_estratos.py"`; caso Chillán VIIRS_NOAA20 2026-10-18 06:00 UTC (9,94 MW: medido 0,018 km, tabla 0,84, nuestro punto a 0,26 km de la mancha).
- CONFIANZA: CONFIRMADO el desajuste y la cuantización de la tabla; SOSPECHA la causa.
- GRAVEDAD: 2. No tuerce alertas; tuerce la vara con que se audita posición en el volcán con más protegidas.

### 353
- TÍTULO: El archivo no capturó láminas Latest10NTI MODIS en 12 de 46 días desde el 22-sep ni VIIRS en 2 a 3 días; dos alertas MODIS de Láscar y una protegida MODIS de Chillán no tienen lámina
- ARCHIVO:LÍNEA: `C:\Users\nmend\vrp-temporales\s175_audit\insumos\png_index.csv` (índice del archivo copiado en la ola 0, última captura `2026-11-07T04:05:55Z`); el poller vive en `MendozaVolcanic/mirova-tif-archive` (fuera de este repo). SCRIPT:SALIDA `p10_cobertura_laminas.py` → `p10_cobertura_laminas.out.txt`; `p9_lascar_modis.py` → `p9_lascar_modis_out.json`; `p8_clases.csv` (`motivo_iv` «pasada no hallada»).
- QUÉ PASA: la lámina es hoy la única huella de dónde marcó MIROVA el foco. No hay lámina MODIS con `last_modified` entre el 23 y el 30-sep ni entre el 8 y el 11-oct en los 11 volcanes (35 de 46 días con lámina); en VIIRS faltan el 13-oct y el 28-oct en los 11 y el 7-oct en VIIRS 375 de 8. La lámina muestra 10 pasadas, así que un hueco de un día se salva; los de 8 y 4 días de MODIS (2 a 3 pasadas al día) no. Sin lámina ni TIF: Láscar MODIS 2026-09-25 08:00 (0,56 MW; nuestro record MODIS_AQUA publica 0,273 MW a 0,79 km), Láscar 2026-10-08 08:00 (0,29 MW; nuestro record 0 MW) y Chillán MODIS_AQUA 2026-10-10 07:40 (3,95 MW, protegida; buscada en 8 láminas). La causa (poller caído, MIROVA sin servir, filtro `omitido`) no la miré: SIN DATO.
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta sólo a quien audite posición.
- CÓMO REPRODUCIRLO: `python -I "<CARPETA>\p10_cobertura_laminas.py"`; `python -I "<CARPETA>\p9_lascar_modis.py"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Sin lámina ni TIF, la identidad de esos aciertos no se puede medir nunca.

### 354
- TÍTULO: La lámina MODIS no sirve de vara de posición con el píxel más claro; tampoco el TIF MODIS reproduce la distancia de la tabla en 4 de 7
- ARCHIVO:LÍNEA: `<CARPETA>\f5b_lib.py` (`pixel_mas_claro`), `<CARPETA>\p7_mas_casos.py`; la vara de F5 es `experiments/_s175_audit/f5/i2_tif.py` (sin casos MODIS). SCRIPT:SALIDA `p7_mas_casos_out.json`, `p7_mas_casos.out.txt`.
- QUÉ PASA: en MODIS la celda es de 1 km y una anomalía de 0,3 a 1 MW apenas sube el NTI del píxel; en el gris del panel no destaca frente a nubes y salares. En los 7 aciertos MODIS de Láscar anteriores al 22-sep con TIF y lámina (2026-06-14 a 07-30; 0,27 a 1,12 MW): luminancia del píxel elegido 89 a 117 contra p99 del panel 215 a 224; distancia al máximo del TIF 0,0 y 0,99 km en 2 casos y 3,6 a 5,8 km en 5; y el máximo del TIF dentro del inner cae a 3,9 a 5,0 km del centro de MIROVA en 4 de 7 (tabla 1,0 a 1,41), así que el control de F5 falla también. Con anomalías fuertes (Chillán 5 a 19 MW) la mancha sí satura (prominencia +58 a +69 en 2026-10-01 01:45 y 10-28 07:35) y el método podría servir, pero no está validado contra TIF: las clases MODIS de la sección 2 (15 (i), 6 (iii), 3 (iv)) se leen como SOSPECHA.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I "<CARPETA>\p7_mas_casos.py"`. Caso claro: Láscar MODIS_TERRA 2026-06-27 01:35 UTC (1,12 MW; lámina `Lascar_20260627_102822_MODIS_Latest10NTI.png`, panel 2, «VRP = 1 MW»; píxel más claro a 5,78 km del máximo del TIF).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Cierra una vía de verificación para el sensor con 23 protegidas en Chillán.

### 355
- TÍTULO: La lámina MODIS redondea el VRP a entero y pinta el marco gris en una alerta de 0,29 MW
- ARCHIVO:LÍNEA: `C:\Users\nmend\vrp-temporales\s175_audit\f5b\png_p9\20261026_103015_MODIS_Latest10NTI.png` (panel 1: «26-Oct-2026 07:55:00», «VRP = 0 MW», marco gris; cabecera «Thermal anomaly: VERY LOW» en verde); tabla: `C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_consolidado_base.csv`, fila Láscar MODIS `2026-10-26 07:55:00`, `VRP_MW 0.29`, `Distancia_km 1.0`, `ALERTA_TERMICA`, `Muy Bajo`. SCRIPT:SALIDA `p9_lascar_modis_out.json` (`marco_verde: false`); `p13_estratos.out.txt` (10 marcos grises, todos VIIRS 750, entre los 303 paneles de aciertos).
- QUÉ PASA: la tabla cuenta la pasada como alerta de 0,29 MW y la lámina la dibuja como «VRP = 0 MW» sin marco de color (en la lámina MODIS del 27-jun el panel de 1,12 MW dice «VRP = 1 MW»; en VIIRS se imprime con decimales). Quien lea el VRP desde la lámina MODIS pierde las alertas bajo 0,5 MW. Nuestro record de esa pasada publica 0 MW a 1,69 km. Además, 10 aciertos VIIRS 750 (alertas de la tabla) tienen marco gris en la lámina: la lámina y la tabla no marcan igual.
- CÓMO SE VE EN EL DASHBOARD: invisible en el nuestro. En el de MIROVA, el panel aparece sin alerta.
- CÓMO REPRODUCIRLO: `python -I "<CARPETA>\p9_lascar_modis.py"` y abrir la lámina. Láscar MODIS_AQUA 2026-10-26 07:55 UTC.
- CONFIANZA: CONFIRMADO en ese caso; que la regla sea «marco de color sólo si el entero es ≥ 1» es SOSPECHA.
- GRAVEDAD: 1. Detalle de presentación de MIROVA; importa si alguien usa la lámina como referencia de VRP (seguimiento para Mirova-v1).

## 4. Línea base roja: validación de la lámina contra el TIF (hecha antes de clasificar)

| # | Qué | Resultado | Salida |
|---|---|---|---|
| 1 | Pareo TIF y lámina en los índices | La lámina llega 1 a 44 s después del TIF de la misma pasada (`last_modified`); 4 de 4 pareadas tienen en «Last Update» la hora de adquisición del TIF (05:54:01, 05:48:00, 05:30:02, 05:42:01) | `p0_indices.out.txt`, `p4_ocr_validacion.out.txt` |
| 2 | ¿El panel es la grilla del TIF? Correlación panel contra TIF (log10), 8 orientaciones | Identidad 0,992 a 0,994 (subpíxel); volteos y rotaciones −0,30 a 0,75. Grilla entera, norte arriba, sin recorte | `p1_georef.out.txt`, `p3_regla_fija.out.txt` |
| 3 | Fase por columnas duplicadas (vecino más cercano) | NEGATIVO: 0 duplicadas en VIIRS 375 (dibujo interpolado); el instrumento sí distingue (34 en VIIRS 750) | `p2_fase_grilla.out.txt` |
| 4 | Regla fija de recorte por correlación subpíxel | Márgenes contra el bbox exterior del marco verde: L 3,0, R 0, T 1 a 2, B 1 a 2,25; imagen de 151 px. Expresada contra el centro de las líneas del marco (verde 3 px, amarillo 3 px, gris 1 px): imagen de `cxL + 1,5` a `cxR + 1,5` en x, de `cyT` a `cyB` en y | `p3_regla_fija.out.txt`, `f5b_lib.py` |
| 5 | **Control positivo, uno afuera**: píxel más claro con la regla de los otros tres contra el máximo del TIF | 4 de 4 a 1 celda: 0,375 / 0,375 / 0,748 / 0,374 km (tol 0,75 / 0,75 / 1,5 / 0,75) | `p3_regla_fija.out.txt` |
| 6 | Lo mismo con la biblioteca final | 4 de 4: 0,0 / 0,373 / 0,0 / 0,0 km | `p7_mas_casos.out.txt` |
| 7 | Control negativo: recortar el marco entero | Sesgo de 1 celda y la búsqueda fina pide escala 1,03 y (−1, −2) px | `p1_georef_v0.out.txt` |
| 8 | Grilla prestada estable en el tiempo | Transformación idéntica (diferencia 0,0) entre junio y el 22-sep en Lastarria VIIRS 375 y Láscar VIIRS 750; MODIS 1e-7°; 14 de 14 combos con la misma grilla 12-sep contra 22-sep; md5 de 28 TIF iguales al índice | `p6_tif_referencia.out.txt` |
| 9 | MODIS | 2 de 7 válidos; 4 de 7 sin control de distancia del TIF (hallazgo 354) | `p7_mas_casos_out.json` |
| 10 | Camino (iii) del clasificador | Isluga 09-22 por lámina: 2,01 km de nuestro punto, igual que por TIF en F5 (2,01); Lastarria 06-12: 0,83. El control sintético de `p8` (punto movido 3 km al norte) quedó mal diseñado: movió el punto hacia el píxel de MIROVA (1,78 → 1,50 km) y no demuestra nada; se declara y no se cuenta | `p7_mas_casos_out.json`, `p8_clasificar_t6_max8.out.txt` |
| 11 | Detector de marco | Primera versión sólo veía verde y gris: 63 aciertos de Chillán con marco amarillo («MODERATE») salieron «sin marco»; se generalizó a cualquier color saturado y se repitieron (0 «sin marco» al final). 10 marcos grises entre los 303 paneles de aciertos, todos VIIRS 750 | `p8_clasificar_t3.out.txt`, `_t5`, `p13_estratos.out.txt` |

Clases (prompt de F5, `C:\Users\nmend\vrp-temporales\s175_audit\prompts\f5.txt` l. 109 a 110, TEXTO: «(i) misma pasada y mismo foco; (ii) otra pasada, mismo foco; (iii) otra fuente dentro del círculo; (iv) SIN DATO de posición»). Todos los aciertos son de misma pasada (±120 s): (ii) no aplica. Regla pre-registrada en `p8_clasificar.py`: píxel más claro del panel dentro del inner de MIROVA y fuera del blanco de «sin dato»; control: su distancia al centro de MIROVA reproduce la `Distancia_km` de la tabla a ± max(tolerancia, 1 celda); (i) si queda a ≤ tolerancia de nuestro punto, (iii) si más lejos, (iv) si falla el control, no hay lámina o no hay distancia. Con distancia del OCR (F5 301) la clase lleva «?» (40 casos, 18 con panel).

Tabla completa por volcán y sensor (de `p12_resumen.out.txt`):

| volcán | sensor | n | (i) | (iii) | (iv) | prot n | prot (i) | prot (iii) | prot (iv) | con distancia OCR | mediana d(MIROVA, nuestro) km en (i)+(iii) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chillán | MODIS (sin validar) | 23 | 15 | 6 | 2 | 23 | 15 | 6 | 2 | 1 | 1,85 |
| Chillán | VIIRS 375 | 69 | 46 | 1 | 22 | 56 | 33 | 1 | 22 | 7 | 0,25 |
| Chillán | VIIRS 750 | 55 | 44 | 3 | 8 | 53 | 42 | 3 | 8 | 3 | 0,67 |
| Chaitén | VIIRS 375 | 9 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0,36 |
| Chaitén | VIIRS 750 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | sin casos |
| Isluga | VIIRS 375 | 43 | 6 | 1 | 36 | 2 | 1 | 0 | 1 | 1 | 0,22 |
| Láscar | MODIS (sin validar) | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | sin casos |
| Láscar | VIIRS 375 | 23 | 17 | 0 | 6 | 1 | 1 | 0 | 0 | 5 | 0,17 |
| Láscar | VIIRS 750 | 3 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0,33 |
| Lastarria | VIIRS 375 | 12 | 7 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0,19 |
| Planchón | VIIRS 375 | 20 | 14 | 0 | 6 | 0 | 0 | 0 | 0 | 3 | 0,19 |
| Cordón Caulle | VIIRS 375 | 24 | 17 | 0 | 7 | 2 | 2 | 0 | 0 | 0 | 0,42 |
| Cordón Caulle | VIIRS 750 | 8 | 2 | 0 | 6 | 4 | 1 | 0 | 3 | 0 | 0,31 |
| Tupungatito | VIIRS 375 | 14 | 2 | 1 | 11 | 0 | 0 | 0 | 0 | 1 | 0,22 |

Motivos de (iv): control de distancia fallido 108 (VIIRS 375 93, VIIRS 750 14, MODIS 1), pasada no hallada en hasta 8 láminas 2 (Chillán MODIS 10-10 07:40, Láscar MODIS 09-25 08:00), sin distancia de MIROVA 3. Láminas usadas: 288 distintas (panel 1 en 259 aciertos, otros paneles en 44); retardo lámina menos pasada: mediana 3 h, p90 7,5 h, máximo 26 h.

Lectura de los (iv) por control fallido (`p13_estratos.out.txt`): fuera de Chillán fallan lejos (|medido − tabla| mediana 3,2 a 6,1 km en Isluga, Láscar, Chaitén y Caulle; prominencia negativa en 41 de 73): la anomalía débil no es el píxel más claro del inner y la vara no alcanza. En Chillán fallan cerca (mediana 0,82 km en VIIRS 375, 1,71 en VIIRS 750) con nuestro punto a 0,36 y 0,62 km de la mancha (hallazgo 352).

## 5. SEGUIMIENTOS (fuera de mi eje)

- **Origen de la `Distancia_km` de MIROVA** (hallazgo 352): F5 302 y el banco (`frac_radio_a_2km`) la comparan contra el centro de la grilla; si MIROVA mide desde la cumbre o el cráter, hay un sesgo por volcán (0,39 km en Chillán entre `mirova_center` y vent de `volcanoes.yaml`). Quien revise D17 debería mirarlo. SOSPECHA.
- **Mirova-v1 (OCR)**: si el OCR del scraper lee el «VRP = N MW» de la lámina MODIS, lee un entero (hallazgo 355). Repo Mirova-v1. SOSPECHA (no miré qué imagen lee el OCR).
- **Poller de `mirova-tif-archive`**: huecos de láminas de 8 y 4 días en MODIS y de 1 día en VIIRS (hallazgo 353), además del fin de los TIF el 22-sep. Fuera de este repo. CONFIRMADO el hueco, SIN DATO la causa.
- **Orden de los paneles**: la lámina ordena por hora de adquisición, no de proceso (Láscar MODIS 2026-06-27 01:35 procesada a las 10:28 quedó en el panel 2, con la de las 08:15 en el 1; 44 de 303 aciertos estaban fuera del panel 1). Parear por `last_modified` y leer el panel 1 se equivoca de pasada. CONFIRMADO.
- **F5 (hallazgo 302)**: la vara «máximo del TIF dentro del inner» no sirve en MODIS (4 de 7). F5 no la aplicó a MODIS. CONFIRMADO.
- **Disco**: C: cayó 2 GB en 46 min sin que mi trabajo pasara de 7 MB; quien orquesta lo atribuyó al archivo de paginación. CONFIRMADO el consumo, la causa la dice quien orquesta.
- **Protegida de Chillán VIIRS_SNPP 2026-10-30 07:00 (31,3 MW) y VIIRS_SNPP_750 (30,85 MW)**: no estaban en las primeras 4 láminas y sí en 8; la lámina de una pasada puede tardar más de 7 h (p90 7,5 h, máximo 26 h). Quien use la lámina como referencia operativa no la tendrá a tiempo. CONFIRMADO.

## 6. VERIFICADO LIMPIO

- md5 de todo lo bajado igual al índice de la ola 0: 4 láminas y 4 TIF de validación (`p0_indices.out.txt`, `md5sum` de la sesión), 28 TIF de referencia y 11 de validación (`md5_ok: true` en `p6_tif_referencia_out.json` y `p7_mas_casos_out.json`), 423 láminas de `p8` (`p8_ocr_cache.json`, campo `md5`). Una primera corrida de `p6` dio `md5_ok: false` en 6 archivos por una colisión de nombres mía; el control la atrapó (`p6_tif_referencia_v0.out.txt`).
- OCR: 40 de 40 paneles y 4 de 4 cabeceras con fecha válida en las láminas de validación, cabecera igual a la hora del TIF en las 4 (`p4_ocr_validacion.out.txt`); 303 de 305 aciertos hallados por etiqueta en las láminas (los 2 restantes, sin lámina, hallazgo 353). En segundo plano tesseract murió una vez con 3221225773 (`p8_clasificar_v0_fondo.out.txt`); con 3 reintentos no volvió a fallar.
- Grilla del TIF estable (sección 4, fila 8). Vara: la transformación del TIF de junio.
- Universo de F5 reproducido: 881 pares, 305 desde el 22-sep (`p5_universo.out.txt`). Vara: el total que F5 declara.
- Isluga 2026-09-22 05:42: la lámina da el mismo píxel que el TIF (−19,16558, −68,84986) y la misma distancia a nuestro punto (2,01 km) que F5 (`p7_mas_casos_out.json`, `p8_clases.csv`).
- Red tras el reinicio: la primera corrida de la segunda parte falló entera por DNS (`getaddrinfo failed`, 301 filas); se purgó y se repitió (`p8_clasificar_t1.out.txt`).

## 7. SIN DATO

- Clase de 108 aciertos (iv) por control fallido: 78 fuera de Chillán donde la anomalía débil no destaca (la lámina no alcanza como vara), 30 protegidas de Chillán donde falla por el origen de la distancia (hallazgo 352). Para éstas la posición de la mancha sí está medida (`p8_clases.csv`, `png_lat/png_lon`, `d_png_nuestro_km`), sólo no pasa el control pre-registrado.
- «Otra fuente» contra «otro píxel del mismo cúmulo» en los (iii): hace falta nuestra extensión de píxeles por record (F5 302 la tenía por radio).
- Posición de MIROVA en Láscar MODIS 2026-09-25 y 2026-10-08 y Chillán MODIS 2026-10-10 07:40: sin lámina ni TIF.
- MODIS en general (hallazgo 354).
- Por qué el archivo dejó de capturar TIF el 22-sep y por qué faltan días de láminas.
- Si el `effort: high` llegó a esta sesión.

## 8. FUERA DE ALCANCE

- Los detectores (F1, F2), el banco de paridad, el recall y el OCR de Mirova-v1 (sólo anotados como seguimiento).
- Corregir el poller o el OCR; proponer cambios en `pipeline/`.
- La identidad del foco antes del 22-sep (F5) fuera de los casos usados como vara.
- El valor del gris de la lámina como NTI o VRP.

---
Comprobación de estilo: el conteo de guiones largos y medios de este archivo es 0 (verificado con grep al cerrar).
