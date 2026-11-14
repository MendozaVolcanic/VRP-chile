# VERIFICACION V33A: 18 afirmaciones de F0 y F1 de la auditoria S175 (verificador con contexto limpio)

## 1. Encabezado

- Hora del servidor (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile/commits/main`): **Sun, 08 Nov 2026 14:15:00 GMT**.
- Base sobre la que medi: `752d348bc67190e53b610989877e2405d238a1bc`. `origin/main` de hoy: `cc32ab1fc85df430ec0887f81630482cc2b178e8`
  (el ref local coincide con la API). **Entre la base y main de hoy el unico cambio fuera de `data/` es
  `.github/workflows/tests.yml` (+38/-1)** (`git diff --stat 752d348bc cc32ab1fc -- pipeline/ frontend/ scripts/ .github/ requirements.txt`):
  ninguna de las 18 afirmaciones que citan codigo se arreglo despues de la base.
- Datos: para los escaneos propios use los 11 JSON de `data/mirova_equivalent/` del worktree en `14dfb0d2e` (ultimo
  `datetime_utc` 2026-11-06 08:25, 73.708 records Tier A); para re-correr el instrumento de F1 use la copia
  `root_base` del auditor (sus `data/` coinciden byte a byte con `e75a7d52d`, sus `scripts/` con la base salvo CRLF).
- Modelo: Claude Fable 5.1. Esfuerzo con que corri: **SIN DATO** (no tengo acceso al nivel efectivo; el pedido no lo declara en el prompt).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v33a\`
  Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\v33a\` (204 MB al cerrar; borre las copias `mutaciones/` que genera el
  instrumento de F1 para quedar bajo el tope de 0,5 GB; se regeneran al re-correrlo).
- Llamadas a la API de GitHub: 2 de 5 (head de main y issue #943). Ninguna a NASA. Ningun workflow, subagente ni git que escriba.
  Disco al cerrar: C: 17 GB libres, D: 4,5 GB (ninguno bajo 3 GB).
- `caminos.md` escrito antes de abrir ningun archivo citado; sha256 `56836b26…4833` anotado al pie; no se volvio a editar.
- **Que NO mire**: ningun `INFORME.md` ni columnas de razonamiento de `hallazgos.csv` de los auditores (por diseno); los PDF en RENDER
  (la unica cita de paper es TEXTO de una extraccion .txt y queda marcada); la carpeta `documentacion/` solo para la vara de la VRE;
  la API de LAADS (251); los datos crudos con que se adopto K (128); `diario.html` y `mosaico.html` mas alla de los greps que se citan.

## 2. En una pantalla

1. **18 de 18 con veredicto: 15 CONFIRMADO, 3 CONFIRMADO EN PARTE (118 latente, 120 la fila falta pero la misma noche tiene
   otra alerta VIIRS en la tabla, 126 la parte «en MIROVA» es indirecta), 0 REFUTADO, 0 SIN DATO.** Ninguno se arreglo entre la base y main de hoy.
2. Lo mas grave sigue siendo de gravedad 2 y todo es visible o latente, no una alerta torcida hoy: 116 (popup «al crater» mide desde el
   centro, hasta 7,58 km en PCC), 117 (VRE con 6 h fijas sobre ~10 records por noche cuando MIROVA integra por trapecios), 119, 121, 161.
3. **Hallazgo nuevo V33A-01 (gravedad 2, reproducido en navegador):** con el toggle «Todos los pixels» el mapa de detalle lanza
   `TypeError … toFixed` en `frontend/index.html:3157` sobre los pixeles de la via (sin `vrp_mw`, hallazgo 161) y deja de dibujar
   los records posteriores: en Nevados de Chillan desaparecen los ultimos 5 dias (39 records) de la ventana de 30 dias.
4. Re-corri los tres instrumentos de los auditores que tenian script (f0_245, mutaciones_vigilancia, censo_via_modis): los tres
   corren y dan lo que la afirmacion dice; medi por otro camino 116, 117, 118, 126 y 161 (escaneo propio) y 255 (cadencia propia).
5. Para quien orquesta: 112, 124 y 125 son decisiones documentadas en el codigo, no defectos sin dueno; 159 y 160 son del
   vigilante (clase de issue y aviso que culpa a los 11), gravedad 1.

## 3. Veredictos por afirmacion (ordenados por gravedad; dentro de cada gravedad, por numero)

### [f0] 116: V2-10, `anomaly_pixels.dist_km` desde el centro y el popup dice «Distancia al crater»: **CONFIRMADO**, gravedad 2
- ARCHIVO:LINEA: `pipeline/process_viirs_mod.py:548` (`dist = haversine_km(volcano_lat, volcano_lon, lat, lon)`) y `:1106`
  (`"dist_km": round(float(dist[r, c]), 2)`); `pipeline/process_viirs.py:812` (misma `dist`) y `:1562`; `frontend/index.html:3159`
  (`Distancia al crater: ${px.dist_km …}`). En MODIS no aplica: K usa `dist_etiqueta` (`process_modis.py:701`) y la via mide desde el
  crater (`pipeline/mirova_v750_codigo.py:730`, `pos_crater`).
- QUE PASA: en VIIRS 375 y 750 la distancia por pixel se mide desde `lat/lon` del volcan (centro) y el popup la rotula como «al
  crater». Donde el vent y el centro coinciden es de forma; donde no, el operador lee una distancia corrida.
- CAMINOS COMPROBADOS: C1 (podria medirse desde el ancla) NO: la linea 548 usa `volcano_lat/lon`; `vent_dist_per_pixel` (l. 552) existe
  pero solo se usa para el keep-peak (l. 1425) y los gates. C3 (centro == vent) PARCIAL: `v33a_escaneo_datos_salida.txt` §116, desde
  `volcanoes.yaml`: PCC 7,58 km, Tupungatito 2,73, Villarrica 0,85, Lascar 0,68, Chaiten 0,59, PP 0,50; Lastarria, Isluga, NdC, Llaima y
  Copahue 0,00. C4 (arreglado en main) NO (sin diff).
- COMO SE VE EN EL DASHBOARD: popup del mapa de detalle de cualquier pixel VIIRS de PCC, Tupungatito, Villarrica, Lascar, Chaiten o PP.
- COMO REPRODUCIRLO: `python -I v33a_escaneo_datos.py <data/mirova_equivalent> <commit> <volcanoes.yaml>` (seccion 116); abrir
  `frontend/index.html?volcano=PuyehueCordonCaulle` y un pixel VIIRS.
- GRAVEDAD: 2 (etiqueta, no deteccion; en PCC el corrimiento es del orden del inner_radius de otros volcanes).

### [f0] 117: V2-11, la VRE del tablero suma 6 h por deteccion: **CONFIRMADO**, gravedad 2
- ARCHIVO:LINEA: `frontend/index.html:2490` (`const DT_HOURS = 6;`), `:2500` (caja «VRE acumulada», `v_mw * DT_HOURS * 3.6`), `:3319`
  (curva, `cumulative += vrp * DT_HOURS * 3.6`). `diario.html` y `mosaico.html` no tienen VRE (grep `DT_HOURS|VRE` vacio).
- QUE PASA: la energia radiada se integra en el tiempo; el tablero le da a cada record 6 h («4 passes/day», comentario l. 2486) sin
  mirar cuantas pasadas hubo. Hoy una noche trae mediana 9 a 12 records nocturnos por volcan con 8 cadenas sensor-satelite
  (`v33a_escaneo_datos_salida.txt` §117, 61 noches, ventana 2026-09-07 a 2026-11-06, `solar_zenith_deg > 90`): 10 records × 6 h = 60 h
  de «tiempo» por noche de 12 h. La VRE crece con el numero de sensores encendidos, no con la energia.
- VARA: MIROVA integra por trapecios. Cita TEXTO (capa de texto de la extraccion `documentacion/coppola2024_chapter.txt` l. 2352,
  pagina del PDF marcada BOOK_PAGE 350 justo despues; A95 pide RENDER para un PDF, asi que la literalidad queda SOSPECHA):
  «Energy (VRE, calculated through trapezoidal integration of the VRP; Fig. 12b)».
- COMO SE VE EN EL DASHBOARD: caja «VRE acumulada» (GJ) y pestana «VRE Acumulada».
- COMO REPRODUCIRLO: `git show 752d348bc:frontend/index.html | grep -n DT_HOURS`; escaneo §117.
- GRAVEDAD: 2 (no toca alertas; distorsiona una magnitud que el operador compara entre volcanes y con MIROVA).

### [f0] 119: V0b-03, el minimo de cumbre 0,003 gobierna tambien el umbral del dETI: **CONFIRMADO**, gravedad 2
- ARCHIVO:LINEA: `pipeline/process_viirs.py:1318` (`_c1_sum = C1_SUMMIT_OVERRIDE if … else DNTI_CONTEXTUAL_C1_SUMMIT`), `:1340-1341`
  (`c1_dnti_summit=_c1_sum, c1_deti_summit=_c1_sum`), `:1392-1393` (segundo pase, igual); `pipeline/detection_context.py:531` y `:538`
  (`thr_deti = combinar(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)`); valor `pipeline/profiles/mirova_equivalent.yaml:136`
  (`dnti_contextual_c1_summit: 0.003`), sin clave propia para el dETI (grep `deti` en el YAML: solo un comentario, l. 440).
- QUE PASA: el piso absoluto del contraste en la banda MIR (dNTI) y el del indice que mezcla MIR con TIR (dETI) son fisicamente
  distintos (el dETI tiene otra escala), pero reciben el mismo numero en las cuatro llamadas. Caminos C1 y C2 (override o piso
  aparte) NO: no hay otra clave ni reasignacion. C3: la vara es diseno propio (el dETI no esta en la Tabla 1 de MIROVA), asi que el
  hallazgo es de parametrizacion, no de fidelidad.
- COMO SE VE EN EL DASHBOARD: invisible (umbral de deteccion VIIRS 375).
- COMO REPRODUCIRLO: `git show 752d348bc:pipeline/process_viirs.py | sed -n 1336,1345p`.
- GRAVEDAD: 2.

### [f0] 121: la regla con que se adopto K sigue igual; vigilancia-sombra usa el paso 9: **CONFIRMADO**, gravedad 2
- SCRIPT:SALIDA: `git diff --stat d516b9d8c 752d348bc -- experiments/_s151_prereg_fk_11/` = solo `v1_cobertura/cobertura.txt` (+6) y
  `v1_cobertura/detalle_cobertura.txt` (+100). `.github/workflows/vigilancia-sombra.yml:135` y `:139` citan «REGLA_ADOPCION.md, paso 9»;
  el yml no menciona P2 (grep `P2` vacio); sigue en main de hoy con cron `40 23 * * *` (l. 22).
- `REGLA_ADOPCION.md` l. 96 (TEXTO): «sumas de P2» con «los **mismos conteos**»; l. 187: «P3 esta anulado por construccion en VIIRS 375».
  Es la version 2 (§8, l. 217). Que V1a-01/04/06, 164 y 165 sigan «abiertos» lo verifico solo en lo factual: el texto no cambio.
- COMO SE VE EN EL DASHBOARD: invisible.
- GRAVEDAD: 2 (regla de reversion vigente apoyada en un criterio que la auditoria S160 califico de debil; sin cambio).

### [f0] 161: los pixeles anomalos de la via no traen `vrp_mw` por pixel: **CONFIRMADO**, gravedad 2 (ver V33A-01)
- ARCHIVO:LINEA: `pipeline/mirova_v750_codigo.py:726-732` (lista `pix`: `lat, lon, dist_km, bt_k, fila, col`); `pipeline/store.py:609-614`
  (comentario S165 V375-E: «Sus pixeles no traen vrp_mw por pixel» y `not _via_mirova` salta el nucleo F5).
- SCRIPT:SALIDA: `v33a_escaneo_datos_salida.txt` §161 (datos `14dfb0d2e`): 118 records de la via, 46 pixeles, todos con claves
  `('bt_k','col','dist_km','fila','lat','lon')`; 6 records con >1 pixel, los 6 sin `vrp_mw` en ningun pixel, todos NdC
  (2026-11-02 01:15 y 07:30, 11-04 08:45, 11-05 01:35 y 07:45, 11-06 08:25). Control: 225 records MODIS no-via con >1 pixel, ninguno sin `vrp_mw`.
  `rerun_censo_via_modis_e75a7d52d.json` (instrumento del auditor re-corrido): 140 records VIA, 0 incoherentes, la huella `pix_sin_vrp`
  solo se emite por record incoherente, asi que ese censo no resume el total (lo mide el escaneo propio).
- COMO SE VE EN EL DASHBOARD: en «Solo principal» (defecto) no se ve: `pixelesDelMarcador` (`index.html:1632-1637`) pone primero el
  ancla `codigo_mirova` con `vrp_mw: r.vrp_mw`. En «Todos los pixels» rompe el mapa (V33A-01).
- COMO REPRODUCIRLO: escaneo §161; `git show 752d348bc:pipeline/mirova_v750_codigo.py | sed -n 726,732p`.
- GRAVEDAD: 2 (sube de 1 por V33A-01).

### [f0] 112: 241 a medias, plataforma muda con codigo 0 tambien en modo estricto: **CONFIRMADO**, gravedad 2
- ARCHIVO:LINEA: `scripts/run_pipeline.py:468` (`cuentan = any(i.get("cuenta_estricto") for i in incidencias)`), `:470-471`
  (`sin_granulos` por plataforma, nota), `:479-481` («Cobertura: faltan plataformas enteras (nota, no es busqueda fallida)»), `:497`
  (`return 3 if (estricto and cuentan) else 0`); `pipeline/fetch.py:789` (`TIPOS_INCIDENCIA = {"sin_granulos": False, …}`).
- QUE PASA: una plataforma que dio cero granulos en toda la corrida se informa como nota y `::warning`, pero no entra en `cuentan`,
  asi que un reproceso con `--estricto-cobertura` sale 0. Es deliberado y esta escrito: docstring l. 455-456 (TEXTO): «Que el modo
  estricto falle por una plataforma muda queda como decision aparte.» C5: nrt-healthcheck.yml tiene «Vigilancia por plataforma»
  (l. 295) que si abre issue por cese (issue #943), lo que acota la gravedad al reproceso (A108).
- COMO SE VE EN EL DASHBOARD: invisible (codigo de salida de Actions).
- COMO REPRODUCIRLO: `git show 752d348bc:scripts/run_pipeline.py | sed -n 451,505p`.
- GRAVEDAD: 2.

### [f0] 122: inventario S160 de VIIRS y unidades sin cambio (F2-210, 212, 230 a 236): **CONFIRMADO**, gravedad 1 a 2
- Cada linea citada existe tal cual en la base y no cambio en main: `pipeline/store.py:74` (`BT_PHYSICAL_MAX_K = 500.0`);
  `pipeline/process_viirs_mod.py:947` (`eti_for_second_pass = fp_diag.get("eti")`, con `if … is not None` en 948: el None se maneja,
  F2-212 queda como «el segundo pase se salta sin aviso», gravedad 2 sostenida solo si eso es lo que S160 decia; no lo lei);
  `pipeline/process_viirs.py:77` (`WOOSTER_COEFF = 18.0   # W/m² per (W/m²/sr/µm)`); `frontend/index.html:2927-2928` (`111.0`);
  `index.html:1162` (`innerKm = 10`) y `diario.html:265` (`?? 5`); `index.html:792-799` LEVELS con 6 entradas (nd + 5 clases, la 5a
  «Muy Alto» con `cls: "badge-high"`) contra la leyenda de `:2465-2467` (4 bandas con MW) y `:3617-3618` (empieza en Alto);
  `pipeline/store.py:218` (`solar_elev_deg <= 0`) contra `scripts/run_pipeline.py:136` (`< 0.0`); `pipeline/detection_context.py:508` y
  `:510` (`np.std` sin `ddof`).
- VARA de F2-235: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:110` (TEXTO): MIROVA usa «desviacion con N-1», nosotros «desviacion con N»,
  y el propio documento la llama «despreciable»: gravedad 1 se sostiene.
- COMO SE VE EN EL DASHBOARD: F2-233 si (badge «Muy Alto» sin banda en la leyenda); el resto invisible.
- GRAVEDAD: F2-210 y F2-212 2; el resto 1.

### [f0] 123: inventario S160 de dependencias sin cambio (249, 251, 252, 254, 255): **CONFIRMADO**, gravedad 1 a 2 (251 SIN DATO en lo externo)
- `.github/workflows/nrt-retry.yml:5` y `:65-66` (solo reintenta con marker NASA_DOWN); `pipeline/fetch.py:226` (`"versions": ["2.1", "2", "1"]`:
  que sea la lista correcta de LAADS hoy no lo puedo medir sin NASA, SIN DATO); `requirements.txt:1` (`earthaccess>=0.9.0`) y ademas
  `nrt.yml:143` instala `pip install earthaccess numpy h5py scipy pyyaml pyproj` sin pin ninguno (segundo camino sin pin);
  `scripts/sync_mirova_csv.sh:110` (`|| echo "  WARN: rebuild $stem failed (continuing)"`) y `:113` `exit 0`.
- 255 medido por otro camino, `v33a_cadencia_healthcheck_salida.txt` (insumo `runs_nrt-healthcheck.json`, 50 corridas, 2026-09-19 a
  2026-11-06): 49 `schedule` creadas entre las **14:34 y las 20:59 UTC** con cron `0 12 * * *` (`nrt-healthcheck.yml:21`); atraso
  mediano 4,97 h, maximo 8,98 h; hueco maximo **27,77 h**. Control: `runs_nrt.json` da huecos de 7 a 9 h entre sus 10 `schedule`
  (el resto son `workflow_dispatch`). Coincide con la salida del auditor (`f0_cadencias_salida.txt`).
- COMO SE VE EN EL DASHBOARD: invisible.
- GRAVEDAD: 255 y 252 2; 249, 251, 254 1.

### [f0] 118: V2-12 latente, el tope de 50 GW juzga `t_max_k` antes de que exista en VIIRS 375: **CONFIRMADO EN PARTE (latente)**, gravedad 1
- ARCHIVO:LINEA: `pipeline/store.py:165-166` (`t_max = record.get("t_max_k")`; `bt_imposible = t_max is None or …`), `:177` (anula
  `vrp_mw` si `vrp > SANITY_CAP_VRP_MW` y BT imposible), `:559` (`_apply_sanity_cap(record)`) antes de `:564-565` (copia de
  `t_max_i04_k` a `t_max_k`). `pipeline/process_viirs.py` no escribe `t_max_k` (grep vacio); `process_viirs_mod.py:1487` y
  `process_modis.py:1718` si.
- QUE PASA: un VIIRS 375 con VRP sobre 50 GW llegaria al tope sin `t_max_k`, se leeria como «sin BT» y se anularia a 0,0 MW aunque la BT
  fuera fisica. Camino C3 (t_max_k puesto antes) NO. Camino C4 (inalcanzable) SI en los datos: `v33a_escaneo_datos_salida.txt` §118,
  73.708 records, 0 con `diag_rejected_sanity_cap_mw`, 0 con `vrp_exceeds_sanity_cap`; VRP maximo VIIRS 375 94,2 MW (NOAA-20, NdC
  2025-02-28 05:48), maximo global 211,3 MW. El codigo esta como se afirma; el fenomeno no ha ocurrido.
- COMO SE VE EN EL DASHBOARD: hoy invisible; si ocurriera, un 0 MW en la erupcion mas grande.
- COMO REPRODUCIRLO: `git show 752d348bc:pipeline/store.py | sed -n 555,566p`; escaneo §118.
- GRAVEDAD: 1 (latente; el auditor puso 2 y el docstring de `_apply_sanity_cap` llama a ese cero «el error mas caro»: si quien orquesta
  pesa el costo y no la probabilidad, 2).

### [f0] 120: V0b-02, la alerta de Lascar del 2026-03-04 05:06 sigue fuera de la tabla: **CONFIRMADO EN PARTE**, gravedad 1
- SCRIPT:SALIDA: `grep -i lascar … | grep -c "2026-03-04 05:0"` = **0** en `latest_consolidado_base.csv` (sha `dee76837…`) y en
  `snapshot_consolidado_base.csv` (sha `f833bfde…`, la que lee el banco); `snapshot_ocr_base.csv` (sha `577a336e…`) si la trae:
  `2026-03-04 05:06:00,Lascar,VIIRS,1.0,…ALERTA_TERMICA_OCR` y `…,VIIRS375,0.55,…`. Los tres sha coinciden con la vara del preambulo.
- Caminos: C1 (formato) NO, la tabla usa `AAAA-MM-DD HH:MM:SS` y el grep lo respeta; C2 (variante de nombre) NO, solo `Lascar` (3.870 filas);
  C4 (otra pasada): **SI hay algo que el auditor no dice**: la tabla tiene `2026-03-04 05:30:01,Lascar,VIIRS,2.3,ALERTA_TERMICA` (y
  `VIIRS375,0.0,RUTINA`) la misma noche, 24 min despues, fuera de `TOL_S` (`banco_paridad.py:78` = `VENTANA_S`, 120 s segun el comentario l. 76).
  La fila de las 05:06 falta; la noche no esta sin alerta VIIRS en la tabla. C5: la inferencia «la cota cero negativos sobre -0,8
  depende de la referencia» necesita el razonamiento del auditor, que no abri: no la juzgo.
- COMO SE VE EN EL DASHBOARD: invisible (referencia).
- GRAVEDAD: 1.

### [f0] 124: 247 salvo un borde, token «desconocido» sin issue: **CONFIRMADO**, gravedad 1
- ARCHIVO:LINEA: `.github/workflows/nrt-healthcheck.yml:364` (`ESTADO = … or "desconocido"`), `:385-387` (`if ESTADO == "desconocido":
  print("Estado del token desconocido (secret ausente o no-JWT): sin issue."); sys.exit(0)`). Deliberado: l. 340-341 (TEXTO): «`desconocido`
  (secret ausente o no legible como JWT) va solo al resumen del job: no es evidencia de vencimiento y abrir issue por eso seria ruido.»
  Sin cambio en main.
- Camino C2 (un secret ausente haria fallar el NRT y el paso «Detect stale Tier A» abriria issue por staleness): no lo medi, SOSPECHA.
- COMO SE VE EN EL DASHBOARD: invisible.
- GRAVEDAD: 1.

### [f0] 125: 245 en parte, la copia que se encoge avisa y entra igual; 37 perdidas, ninguna alerta: **CONFIRMADO**, gravedad 1
- ARCHIVO:LINEA: `scripts/sync_mirova_csv.sh:32-36` (`python scripts/avisar_llaves_perdidas_consolidado.py … || true` y luego `mv`;
  comentario l. 32-33: «Avisa, no rechaza (puede congelar la referencia) … el ultimo paso del workflow pone la corrida en rojo»).
- SCRIPT:SALIDA: re-corri `f0_245_perdidas_vuelven.py` (`rerun_f0_245_salida.txt`): «filas en la union de perdidas: 37; copia vigente:
  47006; perdidas que siguen fuera: 37; con ALERTA: 0; ALERTA >= 1 MW: 0». La union vive en
  `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv`. Denominador: 47.006 filas de la copia del 7-nov.
- COMO SE VE EN EL DASHBOARD: invisible.
- GRAVEDAD: 1.

### [f0] 126: Suomi NPP se callo ~31 h antes del cese; el vigilante informo a las 54 h: **CONFIRMADO** (la parte «en MIROVA» EN PARTE), gravedad 1
- SCRIPT:SALIDA propia: `v33a_escaneo_datos_salida.txt` §126: ultimo `VIIRS_SNPP` y `VIIRS_SNPP_750` **2026-11-01 06:24** (Chaiten);
  NOAA-20 y NOAA-21 siguen hasta 2026-11-06 (control). Cese anunciado `scripts/ceses_esperados.json`: `2026-11-02T13:00:00Z` →
  30,6 h antes. Issue #943 (API): `created_at 2026-11-04T19:01:09Z`, titulo «Cese esperado confirmado: Suomi NPP dejo de producir
  records (informativo)» → 54,0 h despues del cese anunciado (84,6 h despues del ultimo record). Coincide con `f0_pasadas_por_satelite_salida.txt` §1 y §3.
- «En MIROVA tambien»: la tabla de MIROVA no rotula el satelite (`Sensor` = VIIRS/VIIRS375); §4b del auditor solo muestra con que
  satelite nuestro pareo cada fila y §4c no lista filas VIIRS sin record nuestro en 2026-11-01/02. Es evidencia indirecta: EN PARTE.
- COMO SE VE EN EL DASHBOARD: aviso de cese (`frontend/cese_plataformas.js`, no lo abri).
- GRAVEDAD: 1.

### [f0] 127: decision 2 resuelta por otra via; el placebo del 1 % nunca entro al evaluador: **CONFIRMADO**, gravedad 1
- `experiments/_s157_prereg_d25/evaluar_d25.py:112` (`PLACEBO_GANANCIAS = (1.2, 0.8)`); todos los `placebo` del archivo (l. 21, 23, 102-117,
  154, 157, 296-301, 699-757) son K×1,2 y K×0,8; nada apaga al azar el 1 %. `git grep -i placebo 752d348bc -- scripts/ tests/` filtrado por
  `azar|random|0.01|1 %`: vacio. `d7d36aa3e` (2026-10-22, «S160: placebo del 1 % agregado como control…») toca solo `tasks/LOOP_OBJETIVOS.md`
  (+12). `docs/AUDIT_S160.md:12-13` y `:114` piden ese placebo. `docs/MIROVA_DIVERGENCES.md:2861-2864`: D25 «NO SE ADOPTA» (S162);
  `c8423ce9a` no aparece como texto en el archivo: es el commit que metio ese parrafo (`git log -S "NO SE ADOPTA"` → `c8423ce9a 2026-10-24`).
- GRAVEDAD: 1.

### [f0] 128: V1a-05 en parte, `v1_cobertura/` llego a main; datos de adopcion SIN VERIFICAR: **CONFIRMADO**, gravedad 1
- `git log d516b9d8c..752d348bc -- experiments/_s151_prereg_fk_11/v1_cobertura` → `dab267552 2026-10-16 Loop vuelta 88: F/K V1 cobertura
  despareja; decision D-13`. `cobertura.txt` dice «::error::COBERTURA DESPAREJA» con 4 brazos (4.754 a 4.798 pasadas). Que esten los datos con
  que se adopto K sigue SIN DATO: `experiments/_s153_fk_v2/` tiene 59 archivos (1,15 MB: scripts, informes y logs), no los records.
- GRAVEDAD: 1.

### [f0] 129: los 12 pendientes de proceso de F1b siguen como se escribieron: **CONFIRMADO**, gravedad 1
- `git diff --stat d516b9d8c 752d348bc -- <los 11 paths>` vacio, y los 11 existen en la base (`git ls-tree`: 1, 1, 1, 17, 52, 37, 1, 17, 5, 1, 26
  archivos), asi que el vacio es igualdad, no inexistencia (camino C2 descartado). Que no tengan arreglo en codigo es lo que el diff dice;
  si se cerraron por documento en otro archivo no lo busque.
- GRAVEDAD: 1.

### [f1] 159: con la via muerta en los 11 volcanes el veredicto es INVESTIGAR, no VIGILANCIA_CIEGA: **CONFIRMADO**, gravedad 1
- SCRIPT:SALIDA: re-corri `mutaciones_vigilancia.py` sobre mi copia de `root_base` (`rerun_mutaciones_vigilancia_resumen.txt`): bloque
  «M2b_via_cae_a_K_en_todos (140 records; esperado VIGILANCIA_CIEGA)» → **veredicto INVESTIGAR**, con el aviso «el flag de la via de MODIS esta
  encendido en produccion y no hay ningun record MODIS de la via…». M0 sin mutar da VERDE (control).
- MECANISMO (`scripts/vigilancia_guardia_modis.py`): con la via muerta `encendido` sale `null` (el encendido se lee de los datos, docstring
  l. 33-35), la ventana entera pasa a «antes del encendido» y el nulo guardia-produccion da `distintas: 1` de 285 pares → `disparadores`
  l. 289-290 devuelve INVESTIGAR; `evaluar` l. 419-420 solo convierte a VIGILANCIA_CIEGA cuando el veredicto era VERDE. El issue cambia de
  clase (`vigilancia-guardia-modis.yml:135-138`), aunque el cuerpo si imprime los avisos (l. 104+24, `for a in d.get("avisos", [])`).
  Camino C4 (ventana de 1 dia sin pasadas) no aplica: la mutacion quita la clave a 140 records de la ventana entera.
- COMO SE VE EN EL DASHBOARD: invisible (issue de GitHub de otra clase).
- GRAVEDAD: 1.

### [f1] 160: un JSON de la guardia ausente vacia la guardia entera y el aviso culpa a los 11: **CONFIRMADO**, gravedad 1
- ARCHIVO:LINEA: `scripts/banco_paridad.py:284-286` (`for vol in VOLS: with open(… / f"{vol}.json")`: el lazo abre los 11 y el primero que
  falte lanza); `scripts/vigilancia_guardia_modis.py:375-378` (`try: guardia = [… bp.cargar_nuestros(…, data=GUARDIA) …] except
  FileNotFoundError: guardia = []`: el `except` envuelve la llamada entera).
- SCRIPT:SALIDA: bloque «M3_guardia_sin_Villarrica.json» → VIGILANCIA_CIEGA con **11 avisos** «no hay records de la guardia (K) de <volcan> en
  MODIS en la ventana» (uno por volcan, tambien los 10 que tienen JSON) y `n_con_guardia: 0`. En produccion es latente mientras
  `guardia-k-modis.yml` escriba los 11 (SOSPECHA: no medi el workflow).
- GRAVEDAD: 1.

## 4. Hallazgos nuevos (rango V33A)

### V33A-01: con «Todos los pixels» el mapa de detalle lanza TypeError sobre los pixeles de la via y deja de dibujar los records posteriores
- TITULO: `px.vrp_mw.toFixed(4)` sin `vrp_mw` en los pixeles de la via rompe el bucle de marcadores del mapa de detalle.
- ARCHIVO:LINEA: `frontend/index.html:3157` (`${px.vrp_mw.toFixed(4)}`), `:3068` (`Math.log10(Math.max(px.vrp_mw, 0.001))` → radio NaN),
  `:3063-3067` (`renderPixels` toma hasta 10 pixeles cuando `onlyPrimaryPixel` es false), `:3017` (`hotspots.forEach` sin try/catch;
  `hotspots = filtered`, l. 3006, en el orden del JSON, el mas antiguo primero); origen de los datos: hallazgo 161.
- QUE PASA: la via escribe pixeles sin energia por pixel (MIROVA suma los alertados, D32); el tablero, al desplegar todos los pixeles, calcula
  tamano y popup con esa energia. El primer record de la via con mas de un pixel lanza la excepcion dentro del `forEach` y el resto de
  records de la ventana no se dibuja.
- COMO SE VE EN EL DASHBOARD: reproducido en navegador (servidor local sobre el worktree `14dfb0d2e`, `index.html?volcano=NevadosDeChillan`,
  ventana por defecto 30 dias): tras pulsar «⊛ Todos los pixels» la consola da `Uncaught TypeError: Cannot read properties of undefined
  (reading 'toFixed') at index.html:3157:57 … at 3067:20 … at 3017:14` y `Error: <path> attribute d: Expected number, "MNaN,…"`. Sin aviso
  visible. Marcadores `.leaflet-interactive`: 217 en «Solo principal», 651 en «Todos los pixels» (se dibuja lo anterior al fallo). En la
  ventana de 30 dias de NdC (309 records), el primer record de la via con >1 pixel es 2026-11-02 01:15: desde ahi quedan **39 records de 5
  dias (2026-11-02 a 11-06) sin dibujar**, los mas recientes del volcan en erupcion. En «Solo principal» (defecto) no ocurre.
- COMO REPRODUCIRLO: `python -m http.server 8765` en la raiz del repo; abrir `http://127.0.0.1:8765/frontend/index.html?volcano=NevadosDeChillan`;
  pulsar «Todos los pixels»; mirar la consola. Datos: cualquier record con `via_codigo_mirova: true` y `n_anomalous_pixels > 1`
  (escaneo §161 lista 6).
- CONFIANZA: CONFIRMADO (reproducido; conteo de records perdidos por script).
- GRAVEDAD: 2 (el toggle no es el defecto; pero la perdida es silenciosa y afecta justo los dias mas recientes).

## 5. SEGUIMIENTOS (fuera de mi eje, sin perseguir)

- `experiments/_s175_audit/f0/f0_cadencias.py:12`: `SyntaxWarning: invalid escape sequence '\{'` (f-string con `\{`); corre igual. Confianza CONFIRMADO.
- `frontend/index.html:991`: pide `data/mirova_equivalent/<vol>_recent.json` y en el worktree no existe (11 × 404, luego cae al JSON completo).
  Si en GitHub Pages tampoco existe, son 11 peticiones fallidas por carga. Confianza SOSPECHA (no mire Pages).
- `.github/workflows/nrt.yml:143`: `pip install earthaccess numpy h5py scipy pyyaml pyproj` sin version: el pin de `requirements.txt`
  (252) no es el unico camino sin pin. CONFIRMADO.
- 120: la tabla trae `2026-03-04 05:30:01 Lascar VIIRS 2,3 MW` y el OCR `05:06 VIIRS 1,0 MW`: dos pasadas VIIRS a 24 min en la misma noche
  (dos satelites). Si alguien usa esa noche como ejemplo de «referencia incompleta», que lo diga por pasada y no por noche (A93). CONFIRMADO.
- `f0_pasadas_por_satelite_salida.txt` §3 pone como «ultima fila MIROVA del mismo sensor» para SNPP la ultima fila VIIRS de MIROVA
  (2026-11-06): MIROVA no rotula satelite, la columna no mide lo que su titulo dice. CONFIRMADO (lectura de la salida).

## 6. VERIFICADO LIMPIO

- `git diff --stat 752d348bc cc32ab1fc -- pipeline/ frontend/ scripts/ .github/ requirements.txt` → solo `tests.yml`: la base y main de hoy
  son el mismo codigo para las 18 afirmaciones (vara: el repo).
- Los tres sha256 de la referencia (`snapshot_consolidado_base.csv`, `latest_consolidado_base.csv`, `snapshot_ocr_base.csv`) coinciden con
  el preambulo (vara: el preambulo).
- `root_base` del auditor F1: `data/` = `e75a7d52d` byte a byte (Chaiten.json), `scripts/vigilancia_guardia_modis.py`, `banco_paridad.py` y
  `vigilancia_sombra.py` = base salvo CRLF (`diff … | tr -d '\r'` → 0 lineas).
- Los tres instrumentos con script re-corridos (`f0_245_perdidas_vuelven.py`, `mutaciones_vigilancia.py`, `censo_via_modis.py`) corren con
  exit 0 y reproducen lo afirmado (sus salidas estan en CARPETA y en el temporal).
- Control de mutacion de la vigilancia (M0 sin mutar → VERDE; M1 → REVERSION_CANDIDATA; M4 → INVESTIGAR): el instrumento distingue.
- `anomaly_pixels` de MODIS K: 225 records con >1 pixel, los 225 con `vrp_mw` por pixel (control de 161).

## 7. SIN DATO

- 251: si `["2.1", "2", "1"]` es la lista vigente de LAADS (sin NASA).
- 128: si los datos con que se adopto K existen en algun lado (no los encontre en `_s153_fk_v2/`; no busque fuera del repo).
- 124 camino C2 y 160 «latente en produccion»: no medi los workflows.
- Esfuerzo efectivo de esta sesion.
- La inferencia de 120 sobre la cota «cero negativos sobre -0,8» (requiere el razonamiento del auditor).

## 8. FUERA DE ALCANCE

Los otros 15 hallazgos de S175 (frentes F2 a F5); arreglar cualquier cosa; `diario.html`/`mosaico.html` mas alla de los greps; RENDER de PDF.

## 9. Archivos en CARPETA

`caminos.md` (sellado), `VERIFICACION.md`, `hallazgos.csv`, `escribir_hallazgos_csv.py`, `v33a_escaneo_datos.py` + `_salida.txt` + `_stderr.txt`,
`v33a_cadencia_healthcheck.py` + `_salida.txt`, `rerun_censo_via_modis_e75a7d52d.json`.
Temporal `C:\Users\nmend\vrp-temporales\s175_audit\v33a\`: `rerun_f0_245_salida.txt`, `rerun_mutaciones_vigilancia_salida.txt` (JSON),
`rerun_mutaciones_vigilancia_resumen.txt`, `rerun_mutaciones_vigilancia_stderr.txt`, `rerun_censo_stderr.txt`, `http_server.log`, `f1/root_base/`.
