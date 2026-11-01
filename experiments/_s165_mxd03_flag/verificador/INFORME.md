# Verificación con contexto limpio: PR S165 «tres flags MxD03 de MODIS, apagados»

- Hora del servidor al empezar (header `Date` de `gh api repos/MendozaVolcanic/VRP-chile`): **Tue, 27 Oct 2026 17:27:09 GMT**.
- Commit medido: **4164d4547** (rama `claude/s165-mxd03-flags`); base d94f25191; tag anotado `pre-s165-mxd03-modis` resuelve a d94f25191 (`git rev-parse 'pre-s165-mxd03-modis^{commit}'`).
- Modelo y esfuerzo declarados: Claude Fable 5.1, esfuerzo medio-alto (lectura completa del diff y de los 9 instrumentos; re-corrí cada script que corre en Windows; regeneré el golden desde el tag; corrí la suite y la batería de mutaciones en árboles propios).
- Árboles usados (sólo lectura sobre el worktree del PR): `D:\vrp-trabajo\temporales\s165_mxd03_verificador\arbol` (4164d4547, suite y mediciones), `arbol_tag` (d94f25191, golden; retirado tras usarlo), `arbol_mut` (4164d4547, batería de mutaciones). Disco medido antes de cada corrida pesada: C: 12 GB, D: 7,4 GB al inicio y 5,0 GB con dos árboles; nunca bajo 3 GB.
- Lista de caminos escrita antes de leer el PR: `CAMINOS.md`, sha256 `786e52f23187652463da7d86510f84fccf1e836660b137997b2031dd13b2c2a4` (archivo `CAMINOS.sha256`).
- Qué NO miré: no despaché el workflow de la Tarea 4 ni bajé gránulos (sin credenciales, por límite); no corrí `calculate_vrp` sobre HDF reales (pyhdf no está en Windows); no verifiqué las cifras de MOD-B ni del censo MOD-D que el PR hereda (5.465 pasadas, CUMPLE SIN DAÑO), sólo lo que este PR calcula a partir de ellas; no revisé frontend ni `docs/MIROVA_DIVERGENCES.md` (el PR no los toca); no revisé la ortografía de la FICHA.

## En una pantalla

1. Apagados, el procesador MODIS es el del tag: regeneré el golden desde el código de d94f25191 con el arnés de hoy y es **idéntico como texto crudo** al `apagado_antes.json` del PR; la suite completa pasa sobre 4164d4547 (A1, A9).
2. Los tres flags se leen de `thresholds:` (`_t = _cfg["thresholds"]`, `profile.py:79`) y están en False en `mirova_equivalent`, `experimental`, `experimental_ndc_focus` y `experimental_lowT` (A2).
3. Cada flag encendido hace lo que dice en el arnés y la batería de mutaciones reproduce 22 de 22 atrapadas por aserción con sus dos controles (A3, A5). Pero el flag de distancia alcanza un **consumidor más** que la prueba de cableado no nombra: el filtro de píxeles por distancia y la geocerca de `store.py` (V165-01); medido sobre data/, hoy cambiaría 1 píxel en 1 record de PCC, uno de los 5 que la medición previa ya listaba.
4. Las dos mediciones previas sin red se reproducen exactas (223 de 5.465; 5 publicaciones, todas PCC, control 180 de 180) y la referencia de MOD-B se re-extrae idéntica de los artefactos (A6, A7, A8 en parte).
5. El criterio EQUIVALENTE de `equivalencia.py` es más débil que su docstring: compara publicación y `pc.vrp` a 0,001 MW, y en 14 de los 18 records de referencia K y X coinciden en las dos cosas, así que el lado «ON = X» sólo es distinguible en 4 records; la identidad del resumen se registra pero no decide (V165-02). Nada de esto toca producción con los flags apagados.

## Afirmaciones

### A1. Apagados, `calculate_vrp` de MODIS da bit a bit lo del tag. **CONFIRMADO** (gravedad 0)
- Camino 1 (golden generado con código ya tocado): cerrado. El golden se commiteó en 7a806ffae, cuyo diff contra d94f25191 no toca `pipeline/` (`git diff --stat d94f25191 7a806ffae`: sólo `experiments/` y `tests/`). Además lo regeneré desde el código del tag en un árbol aparte (`arbol_tag`, HEAD d94f25191; `grep -c "leer_mxd03\|ENABLE_MODIS_GEO_MXD03" pipeline/process_modis.py` da 0 ahí) con el arnés de 4164d4547: `canonico (9 cifras) igual: True`, `texto crudo igual: True` (`golden_desde_tag.json`).
- Camino 3 (bit a bit con tolerancia): el test compara con `S142._redondear` a **9 cifras significativas** (`arnes_sintetico_s142.py:291`, decisión S142 por diferencias BLAS Windows/Linux de 1e-16). Es el instrumento declarado del proyecto; yo comprobé además la igualdad como texto crudo.
- Camino 2 (la escena no ejerce los caminos tocados): con los flags apagados las cuatro escenas dan el **mismo record** (vrp 4,636, `far`, `hotspot_dist` 5,01, `n_bg` 1872), porque `lat_m/lon_m` no se leen; es lo esperado y el test exige que el golden no sea trivial (vrp > 0 y `far`). Los caminos nuevos se ejercen en los controles (A3).
- Camino 8 (qué es «el tag»): tag anotado, `^{commit}` = d94f25191 = base del PR.
- El arnés corrido por mí en `arbol` con flags apagados (`arnes/apagado.json`) es la base contra la que los otros brazos sólo difieren en lo esperado.

### A2. Flags leídos de `thresholds:` y apagados en producción y laboratorio. **CONFIRMADO** (gravedad 0)
- `pipeline/profile.py:79`: `_t = _cfg["thresholds"]`; los tres `bool(_t.get(..., False))` (diff). YAML: las tres claves bajo `thresholds:` en `mirova_equivalent.yaml:135-140`, en `false`.
- Valor efectivo leído de `pipeline.profile` (no del YAML): `[False, False, False]` en `mirova_equivalent`, `experimental`, `experimental_ndc_focus` y `experimental_lowT` (`VRP_PROFILE=<perfil> python -c "import pipeline.profile as p; ..."`). El guard sólo mira los dos primeros; los otros dos los miré yo.
- El guard `test_flag_se_lee_de_thresholds_y_no_de_la_raiz` inyecta la clave con `yaml.safe_load` parchado y confirma `(True, True)` en `thresholds` y `(False, False)` en la raíz; la mutación `perfil_lee_la_raiz` la atrapa (A5).
- Camino 6 (default True): el default es False en los tres.

### A3. Cada flag encendido hace lo que debe y llega a sus consumidores; el anillo no cambia. **CONFIRMADO EN PARTE** (gravedad 2)
- Lo que se sostiene (arnés en `arbol`, carpeta `arnes/`, diff de campos por escena): `DIST` cambia exactamente `anomaly_pixels`, `hotspot_dist_km`, `final_hotspot_dist_km` y `distance_class` (5,01 a 4,33; far a summit) y nada más (ni `diag_n_bg_anillo`, ni `vrp_mw`, ni `diag_t_max_dist_km`); `GEO` en la escena sin corrimiento sólo agrega `geo_fuente: mxd03`; en `mxd03_corrido` mueve `final_hotspot_lat` 2 km al sur y las distancias; `SIN_DATO` solo no cambia nada; `GEO+SIN_DATO` devuelve `None` en `crater_relleno` y `crater_borde` y record en las otras dos. Con los flags apagados el record no gana claves.
- Trazado de `final_hotspot_dist_km` en producción (`process_modis.py:1461-1510`): con K (`triggered_test1` 0 en todo el corpus, marca S160), `ENABLE_VENT_PATH_MODIS=False`, `ENABLE_HONEST_ANCHOR_MODIS=False` y `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER=False` (valores leídos de `pipeline.profile`), la única fuente viva es `eruption`, que toma `hotspot_dist_km = anomaly_pixels[0]["dist_km"]` (l. 1277): el flag sí llega a la etiqueta. Las otras fuentes (`test1`, `vent`, `cluster_rescue`, `ctx_cluster`) ya miden desde el cráter o están apagadas.
- Lo que NO se sostiene en la forma «llega a todos sus consumidores»: `dist_km` del píxel tiene un **consumidor más** en `pipeline/store.py:259-307` (`_filter_pixels_by_distance`, activo: `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True`, cerca `radius_km` = 25 km en Tier A) y en la geocerca `hotspot_dist_km > MAX_HOTSPOT_DIST_KM` (l. 401). El flag los alcanza (cambia el `dist_km` que leen) y ni la prueba de cableado ni el docstring de `dist_de_etiqueta` ni la FICHA los nombran; sólo el docstring de `medir_dist_crater.py` lo declara «no emulado». Ver V165-01 con la medición.
- Anillo: `bg_mask` sigue en `dist` (l. 708) y la mutación `anillo_desde_el_crater` se atrapa por `diag_n_bg_anillo` 1874 contra 1872.
- Camino 4 (dependencia entre flags): `sin_dato_de_geolocalizacion` exige `geo_fuente == "mxd03"`; con `GEO` apagado o con MxD03 ilegible no actúa, y eso está escrito y probado.
- Camino 3 (el caller ignora el `None`): `scripts/run_pipeline.py:265` `if result:` no escribe; pero tampoco registra la pasada en ningún lado: ver V165-03.
- Camino 7 (flags leídos a nivel de módulo): las funciones leen el global de `pm` al llamarse, y el arnés y los tests parchan ese global; las mutaciones `geo_flag_ignorado` y `dist_flag_ignorado` se atrapan, así que el camino está vigilado.

### A4. La vía «código MIROVA» de MODIS no se rompe ni cambia. **CONFIRMADO** (gravedad 0)
- El bloque `if ENABLE_MODIS_CODIGO_MIROVA:` (l. 633-658) corre ANTES de `posicion_de_calculo`, lee su propio MxD03 con `_MV.leer_geo_mxd03` y retorna; cuando cae con marca (`sin_grilla`, `sin_mxd03`, `geo_distinta`) sigue por el camino de producción, que con los flags apagados es el de antes. Las funciones nuevas se insertaron tras el `return out` de `_regrid_modis_granule` sin comerlo (diff, A49).
- `tests/test_mirova_modis_codigo_s164.py` forma parte de la batería de mutaciones (control sin mutación «viva») y de la suite (A9), y pasa.

### A5. Batería de mutaciones: 22 de 22, controles «viva» y «caida», 1 no cubierta. **VEREDICTO ABAJO (sección «Corridas que cerraron después»)**
- Lectura del instrumento: clasifica por el prefijo del mensaje del JUnit (`AssertionError`/`assert` = aserción; lo demás = caída); un subproceso que muere levanta `RuntimeError` en los arneses (cambio de 4164d4547 respecto de 7a806ffae, que usaba `assert`), así que una caída no se cuenta como atrapada (S152, S156). `mutaciones_salida_v1.txt` muestra el caso que motivó ese cambio: `geo_fuente_no_se_escribe` daba `KeyError` (caída) y el test pasó a `.get`.
- Cada mutación exige `s.count(a) == 1` antes de aplicarse y restaura los tres archivos en `finally`.
- Cobertura: 22 mutaciones sobre 3 archivos (`profile.py` 1, YAML 2, `process_modis.py` 19), repartidas en las 4 piezas; la no cubierta (`build_anomaly_pixels` del Test 1) está declarada y su camino está apagado en producción (D30).
- La salida commiteada es coherente consigo misma y con la v1 (el `diff` entre ambas sólo cambia direcciones de memoria y el caso `geo_fuente_no_se_escribe`).

### A6. Regla «sin dato» sobre el censo MOD-D: 223 de 5.465 (221 borde, 2 relleno), ninguna que K publicara, 1 alerta bajo 1 MW. **CONFIRMADO** (gravedad 0, con una nota)
- Re-corrido por mí sobre `D:\vrp-trabajo\temporales\s162_modd\censo` (24 `ab_parte*.jsonl`): salida idéntica a la commiteada (`paso0_rerun.txt`, `paso0_borde_rerun.txt`; el `diff` sólo difiere en la sección 4, que la salida commiteada obtuvo con `--borde`): 5.465 records, 0 sin `crater_mxd03`, 223 sin dato (221/2), alertas en sin dato: 1 (Villarrica 2026-09-25 08:05 AQUA, `bajo1`, línea 0), K publicaba 0.
- Camino 2 (predicado): `pub.K` del censo sale de `probe_etiquetas.publica`, que ejecuta el predicado del tablero con node desde `frontend/index.html` vía `banco_paridad` (A97).
- Nota (SOSPECHA, no medida): la definición del censo no es literalmente la de `crater_cubierto`. El censo elige (i, j) con distancia equirectangular (`np.hypot`, `probe_etiquetas.py:143`) y mira los 8 vecinos **sólo en latitud** (`probe_paquete.py:139,145`); el pipeline usa `haversine_km` y exige latitud y longitud finitas. Como el lector pone NaN por separado en lat y lon (`mirova_v750_codigo.py:813-814`), las dos definiciones sólo pueden divergir en un píxel con lat válida y lon de relleno, o en un empate de distancia. Efecto esperado nulo; no se puede medir sin los MxD03 (V165-05).
- El paso 0 del plan pedía «cero con `vecinos_validos` falso fuera del borde y del relleno»: se cumple (los 2 sin borde son relleno). El plan también esperaba las cubiertas «a menos de ~0,7 km»; el dato da p50 0,54, p99 1,89 y máximo 2,63 km (773 sobre 1 km), y el PR lo transcribe como «2,6 km o menos» en el docstring de `crater_cubierto` (V165-06).

### A7. Flag de distancia sobre data/: 5 publicaciones cambian (2026-03-01 a 2026-10-27), todas PCC en negativos limpios; identidad 180 de 180. **CONFIRMADO** (gravedad 0, con V165-01 como límite declarado)
- Re-corrido por mí desde `arbol` (`medir_dist_crater_rerun.txt`): 5.733 records MODIS nocturnos, fuente `eruption` 180, etiqueta cambia 5 (todas far a summit, PCC, inner 20, d 20,2 a 24,2 km pasan a 15,0 a 18,0 km), publicación cambia 5 pasadas y 5 de 2.644 noches, todas `neg_limpio`; control de identidad 180 de 180; control positivo (ancla 30 km al norte) 155 etiquetas y 137 publicaciones cambian: el instrumento puede dar distinto de cero.
- Predicado: node sobre `frontend/index.html` (A97). Guarda A46 de `store.py` importada, no copiada.
- Límite que el script declara y que yo medí (V165-01): la geocerca y el filtro de píxeles de `store.py` no se emulan; de los 5 records, el de 2026-05-03 07:50 tiene un píxel descartado que con la distancia desde el cráter volvería a entrar.

### A8. Tarea 4: script y workflow comparan ON con X y OFF con K; referencia fiel. **CONFIRMADO EN PARTE** (gravedad 3)
- Referencia fiel: re-extraída por mí desde `t1/t2/t3` (`referencia_mod_b_rerun.jsonl`): 18 records idénticos línea a línea y cabecera idéntica (5 archivos fuente con el mismo sha256). K difiere de X en los 18; la publicación de K y X coincide en los 18.
- Dirección de la comparación: ON (`patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True)`) contra `brazos["X"]` y `pub["X"]`; OFF contra `brazos["K"]` y `pub["K"]`; `procesar_brazo(..., latlon=None, ...)` deja que el pipeline lea el MxD03 él mismo, y el brazo X de MOD-B lo inyectaba en float32 en `data["lat"/"lon"]` (`probe_mxd03_ab.py:154-158`), que es lo que `posicion_de_calculo` reproduce (float32) y por lo que `observation_geometry` recibe ahora `lat, lon`. Correcto por lectura.
- Lo que no se sostiene: el docstring dice «los 36 records» y la referencia tiene 18 (V165-04). Y el criterio EQUIVALENTE no exige identidad del resumen en ON (V165-02).
- Workflow: `"on":` entre comillas (A43), sólo `EARTHDATA_TOKEN` y falla si viene vacío (patrón de otros 9 probes del repo; `fetch.auth` usa el token sin usuario y clave), `actions/checkout@v5` y `setup-python@v6` como otros 35 y 31 workflows vivos, `permissions: contents: read`, sin push. Sólo lectura: verificado por lectura; no lo despaché.

### A9. Suite completa 0 fallas sobre 4164d4547. **VEREDICTO ABAJO (sección «Corridas que cerraron después»)**
- Primera corrida en `arbol` (HEAD 4164d4547, árbol quieto, `-p no:cacheprovider`): `2 failed, 2676 passed, 29 skipped, 2 xfailed` en 365 s (`suite_arbol.log`). Las 2 fallas son `test_guard_libro_de_pruebas_s146.py::test_g1d/test_g2c`, con `ValueError: path is on mount 'C:', start on mount 'D:'`: `os.path.relpath` entre el `tmp_path` de pytest en C: y mi árbol en D:. Artefacto de dónde puse el worktree, no del PR: con `--basetemp` en D: los 7 tests del archivo pasan (`7 passed in 1.06s`). Nada en esos tests ni en lo que leen cambia en el PR (`git diff --stat`).
- Skips (29): insumos fuera de git (OSF, mirova-tif-archive, salidas de A/B en disco); ninguno es de los tests S165.

## Hallazgos propios

### V165-01. El flag de distancia alcanza un segundo consumidor (geocerca y filtro de píxeles de `store.py`) que la prueba de cableado, el docstring y la FICHA no nombran
- Archivo:línea: `pipeline/store.py:259-307` (`_filter_pixels_by_distance`, lee `p["dist_km"]` contra `max_dist_km`), `:368,401` (`hotspot_dist_km > MAX_HOTSPOT_DIST_KM`); `scripts/run_pipeline.py:268` (`max_hotspot_dist_km=volcano.get("radius_km")`); `pipeline/process_modis.py:566-572` (docstring de `dist_de_etiqueta` nombra sólo la etiqueta); `tests/test_guard_mxd03_flags_s165.py::test_dist_desde_el_crater_llega_a_todos_sus_consumidores`.
- Qué pasa: con `ENABLE_MODIS_DIST_DESDE_CRATER` encendido, el `dist_km` de cada píxel anómalo se mide desde el cráter, y `store.py` compara ese mismo campo con la cerca de 25 km para quitar píxeles y recomputar `vrp_mw`, y con la geocerca del hotspot. El ROI de MODIS es una caja (`roi_mask_bbox`, l. 707), así que hay píxeles a más de 25 km del centro que hoy el filtro quita; con la distancia desde el cráter el conjunto que queda puede cambiar.
- Cómo se ve (medido, `geocerca_pixeles.py` sobre `arbol/data/mirova_equivalent/`, MODIS, 11 Tier A, 2026-03-01 a 2026-10-27): 5.733 records, 175 con píxeles, 235 píxeles; **0 píxeles guardados saldrían** de la cerca; **1 píxel descartado volvería a entrar** (PCC 2026-05-03 07:50, record hoy `far`, vrp 2,225), que es uno de los 5 que A7 ya lista como publicación que cambia; 4 píxeles a menos de 1 km de la cerca con alguna de las dos distancias; desplazamiento máximo entre las dos distancias 7,59 km (PCC).
- Cómo reproducir: `python geocerca_pixeles.py <raiz> 2026-03-01 2026-10-27` (salida en `geocerca_pixeles_salida.txt`).
- Confianza: alta en el mecanismo (código leído) y en la medición (script propio, denominador explícito). Gravedad: **2** (hoy no actúa, flag apagado; cuando se encienda, el efecto medido es 1 píxel en 1 record, pero la afirmación «llega a todos sus consumidores» y la FICHA v1.15 quedan incompletas y el test no lo vigila).

### V165-02. El criterio EQUIVALENTE de `equivalencia.py` no exige que ON reproduzca el resumen de X; sólo publicación y `pc.vrp` a 0,001 MW, y en 14 de 18 records K y X coinciden en las dos
- Archivo:línea: `experiments/_s165_mxd03_flag/equivalencia.py:137-140` (`ok` usa `on_pub_vrp`, `off_pub_vrp`, `control_negativo_ok`; `on_resumen` se cuenta pero no decide); docstring l. 1-9 («record por record», «sin tolerancia en la publicación»).
- Qué pasa: en los 18 records de referencia la publicación de K y de X es la misma, y `pc_vrp` difiere en más de 0,001 MW sólo en 4 (Láscar en 3 gránulos, Chillán en 1; medido desde el jsonl). Un ON que por cualquier defecto siguiera dando K pasaría `on_pub_vrp` en 14 de 18 y fallaría sólo en esos 4; el control negativo sí es fuerte (exige resumen OFF idéntico a K y distinto de X en los 18). Así que el veredicto EQUIVALENTE prueba «ON no es K» en 4 records y «OFF es K» en 18, no «ON es X» record por record.
- Cómo se ve: conteo sobre `referencia_mod_b.jsonl` en esta sesión: `n 18 pc_vrp distinto >0.001: 4 pub distinta: 0`; el jsonl de salida registra `on_resumen_identico` por record, así que el lector del artefacto podrá comprobarlo a mano.
- Cómo reproducir: contar en el jsonl los records con `|pc_vrp_K - pc_vrp_X| > 0.001`; leer `ok` en `equivalencia.py:137`.
- Confianza: alta. Gravedad: **3** (es el instrumento con que se va a certificar que «lo que se midió es lo que se adoptaría»; no afecta producción apagada). Corrección obvia: exigir `on_resumen == n` en `ok`, o declarar por qué no.

### V165-03. Con el flag «sin dato» encendido, la pasada descartada no queda registrada en el informe de cobertura de la corrida
- Archivo:línea: `pipeline/process_modis.py:674-676` (`print(...)` + `return None`); `scripts/run_pipeline.py:265` (`if result:` sin rama else); `:248-250` y `:389-394` (`_sin_geolocalizacion` sí llama a `fetch.registrar_incidencia`, pero sólo cuando falta el archivo MxD03 entero).
- Qué pasa: la FICHA v1.12 dice que el registro de cada corrida informa por volcán y día «lo que no se pudo ver aunque nada haya fallado» (S159, `registrar_incidencia`). Una pasada que el flag 2 deja sin record cae en la misma categoría (el sistema no miró el cráter) y hoy sólo deja un `print` en el log del job; `informar_cobertura` seguiría diciendo «completa» y el modo estricto de reproceso no la vería.
- Cómo se ve: por lectura; con el arnés, `GEO+SIN_DATO` devuelve `None` en `crater_borde` y `crater_relleno` (`arnes/`), y en `run_pipeline.py` ese `None` no toca `registrar_incidencia`.
- Cómo reproducir: `grep -n "if result:" scripts/run_pipeline.py`; `grep -n registrar_incidencia scripts/run_pipeline.py pipeline/process_modis.py`.
- Confianza: alta. Gravedad: **2** (no actúa con el flag apagado; medido en el censo serían 223 de 5.465 pasadas que desaparecerían sin rastro en el informe de cobertura).

### V165-04. El docstring de `equivalencia.py` dice «36 records» y la referencia tiene 18
- Archivo:línea: `experiments/_s165_mxd03_flag/equivalencia.py:17-18`; `referencia_mod_b.jsonl` (cabecera `"n": 18`); `extraer_referencia_mod_b.py:4-5` explica que la primera versión duplicaba los 18.
- Qué pasa: texto desactualizado; `ok` exige `tot["n"] == len(ref)`, así que el número no afecta el veredicto.
- Confianza: alta. Gravedad: **1**.

### V165-05. La definición de «cráter cubierto» del censo (con que se midió A6) no es literalmente la del pipeline
- Archivo:línea: `experiments/_s164_modis_codigo/verificador/insumos/probe_paquete.py:139,145` (vecinos sólo de `latlon_m[0]`), `experiments/_s151_mxd03_etiquetas/probe_etiquetas.py:143` (equirectangular); `pipeline/process_modis.py:539-552` (haversine, lat y lon). `paso0_regla_sin_dato.py:7-9` afirma «la misma definición».
- Qué pasa: ver la nota de A6. Divergencia posible sólo con lon de relleno y lat válida, o empate de distancia; el lector de MxD03 enmascara lat y lon por separado (`mirova_v750_codigo.py:813-814`).
- Confianza: media (mecanismo leído; efecto no medible sin HDF). Gravedad: **1**. SOSPECHA en cuanto al efecto.

### V165-06. El umbral de «cubierta normal» que el plan fijó (~0,7 km) no es el del dato (p99 1,89 km, máximo 2,63 km, 773 pasadas sobre 1 km) y la corrección quedó sólo en el docstring del pipeline
- Archivo:línea: `PLAN_copia.md` Tarea 3 paso 0 («una cubierta normal está a menos de ~0,7 km», «si el dato contradice la regla, se corrige la regla aquí, por escrito»); `paso0_regla_sin_dato_salida.txt` sección 2; docstring de `crater_cubierto` («2,6 km o menos»).
- Qué pasa: la regla no cambió (y el dato no la contradice en lo que pedía: 0 fuera de borde y relleno), pero la expectativa numérica del plan sí cayó y la corrección no quedó en el plan.
- Confianza: alta en los números (salida re-corrida). Gravedad: **1**.

## VERIFICADO LIMPIO (contra qué vara)
- Golden `apagado_antes.json` contra el código del tag regenerado por mí (texto crudo y canónico de 9 cifras).
- Diff `d94f25191..4164d4547` contra A49 (ningún `return` comido en las inserciones): leído el contexto de cada hunk.
- `_t = _cfg["thresholds"]` contra A89 forma 2 (clave en otra sección): valor efectivo leído de `pipeline.profile` en 4 perfiles.
- `observation_geometry(lat, lon, ...)` contra el brazo X de MOD-B (que inyectaba el MxD03 en `data["lat"/"lon"]`): coherente.
- Referencia `referencia_mod_b.jsonl` contra los artefactos t1/t2/t3 (re-extracción idéntica, sha256 de los 5 archivos fuente).
- `paso0` y `medir_dist_crater` contra sus salidas commiteadas (re-corridos: idénticos) y contra un control positivo que sí mueve el conteo (A116).
- Citas `process_modis.py:1182` y `:64` del guard S131 contra el archivo (tokens presentes).
- Workflow contra A43 (`"on":`), A71 (sólo token, falla vacío), versiones de actions contra las de los workflows vivos.
- Vía «código MIROVA» contra el flujo de `calculate_vrp` (retorna antes de `posicion_de_calculo`).
- Los árboles propios quedaron limpios tras cada corrida (`git status --short` vacío al final de la suite; el de la batería se reporta abajo).

## SIN DATO
- Que ON reproduzca al brazo X sobre HDF reales (Tarea 4): requiere Linux, pyhdf y credenciales; no corrido.
- Efecto real de V165-05 (haversine y lat+lon contra hypot y lat) sobre el censo: no medible sin los MxD03.
- Las cifras heredadas de MOD-B y del censo MOD-D (CUMPLE SIN DAÑO, 5.465 pasadas) no se verificaron aquí.

## SEGUIMIENTOS fuera de alcance
- Decidir si la geocerca y el filtro de píxeles de `store.py` deben medir desde el cráter cuando se encienda el flag 3 (V165-01), y agregar esa aserción al guard de cableado.
- Registrar la pasada «sin dato» con `registrar_incidencia` (V165-03) antes de encender el flag 2.
- Endurecer `ok` en `equivalencia.py` (V165-02) antes de despachar el workflow.
- `test_guard_libro_de_pruebas_s146` falla si el repo y el `tmp_path` de pytest están en discos distintos (observado con worktree en D:); no es del PR, pero vale saberlo para los árboles en D: (regla S154).

## Corridas que cerraron después

### A9. **CONFIRMADO** (gravedad 0)
- Segunda corrida completa en `arbol` (HEAD 4164d4547, árbol quieto, `-p no:cacheprovider --basetemp=../pytmp` en D:): **`2678 passed, 29 skipped, 2 xfailed, 84 warnings in 394.88s`**, `rc=0`, `git status --short` vacío al terminar (`suite_arbol_v2.log`). Las 2 fallas de la primera corrida eran el artefacto de discos distintos descrito arriba (los mismos 2 tests pasan en la segunda).
- Comando: `VRP_PROFILE=mirova_equivalent PYTHONIOENCODING=utf-8 python -m pytest tests -p no:cacheprovider -q --no-header -rfE --basetemp=../pytmp`.

### A5. **CONFIRMADO** (gravedad 0)
- Batería re-corrida por mí en `arbol_mut` (HEAD 4164d4547, árbol quieto, 17:43 a 17:55 UTC; `mutaciones_rerun.txt`): **`mutaciones reales atrapadas por aserción: 22 de 22`**, `controles: sin mutación viva, caída caida`, `declaradas no cubiertas: ['dist_no_llega_al_test1']`, `todo como se esperaba`, `rc=0`. Salida idéntica a la commiteada salvo direcciones de memoria (`diff` tras normalizar `0x...`). 0 archivos `_junit_*` residuales y `git status --short` vacío: la batería restauró los tres archivos.
- Camino 1 (atrapada por caída): ninguna; las 22 muestran un `AssertionError`/`assert` como primera prueba fallida, y el control de caída sale `caida` (no `atrapada`), así que el clasificador distingue las dos cosas sobre este árbol.
- Comando: `VRP_PROFILE=mirova_equivalent PYTHONIOENCODING=utf-8 python experiments/_s165_mxd03_flag/mutaciones.py` en el árbol propio.

## Archivos de esta verificación (todos en `D:\vrp-trabajo\temporales\s165_mxd03_verificador\`)
`INFORME.md`, `CAMINOS.md`, `CAMINOS.sha256`, `PLAN_copia.md`, `golden_desde_tag.json`, `arnes\*.json` (seis combinaciones de flags), `paso0_rerun.txt`, `paso0_borde_rerun.txt`, `medir_dist_crater_rerun.txt`, `referencia_mod_b_rerun.jsonl`, `geocerca_pixeles.py` y `geocerca_pixeles_salida.txt`, `suite_arbol.log`, `suite_arbol_v2.log`, `mutaciones_rerun.txt`. Los worktrees `arbol`, `arbol_tag` y `arbol_mut` se retiraron con `git worktree remove --force` al terminar.
