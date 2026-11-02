# Frente 1 (mini-auditoría S172): consumidores del flag de la vía «código MIROVA» en MODIS

## 1. Encabezado

- Hora del servidor: inicio Mon, 02 Nov 2026 00:46:15 GMT; cierre Mon, 02 Nov 2026 01:31:33 GMT
  (`gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date`).
- Objeto medido, fijado por hash: base main `d3cd0b2aeee70b99fbc5bd90e5fd2b0dff284f54` (tag pre-s171-adopcion-modd);
  PR A punta `c83882fcfdbd7fdb441e61a54a03c8f5fb3707b2`; PR B punta `b4282319446cfea944aa1a4621c0fec7da8649a0`.
  origin/main al medir: `14fb62030` (sólo sincronización de datos).
- Topología verificada (`00_git_topologia.txt`): el padre de `479a30c18` (primer commit del PR B) es `da67fa417`;
  `c83882fcf` NO es ancestro de `b42823194`; `git diff --stat da67fa417 b42823194` da 21 archivos, entre ellos
  `pipeline/process_modis.py`. El PR B contiene los commits del PR A salvo el informe del implementador.
- Modelo y esfuerzo realmente usados: Opus 5.5 (`claude-opus-5-5`) con esfuerzo de razonamiento BAJO (no el «alto»
  pedido). Lo declaro para que el filtrado lo pondere.
- CARPETA: `D:/vrp-trabajo/temporales/s172_miniaud/f1` (scripts en `scripts/`, salidas al lado; copias privadas
  `copia_b` = b42823194, `copia_da67` = da67fa417, `copia_flip` = da67fa417 más sólo la línea del flag en
  `mirova_equivalent.yaml`, `copia_mut` = b42823194 para mutaciones; `data/` y `experiments/` de b42823194 en
  `comun/`, enlazados por junction en cada copia).
- Incidente propio, declarado: la primera corrida de `m1_perfiles.py` (00:47 UTC) escribió
  `pipeline/__pycache__/profile.cpython-312.pyc` en el worktree compartido `D:/vrp-trabajo/worktrees/s172-miniaud-b`
  (archivo ignorado por git). Lo borré de inmediato (sólo ese archivo y su carpeta, creada por mí: la marca de tiempo
  era la de mi corrida) y desde ahí todo corrió en copias propias con `PYTHONDONTWRITEBYTECODE=1`. Al cierre,
  `git status --short --ignored` del worktree sale vacío y HEAD sigue en b42823194.
- Qué NO miré (mi silencio aquí no es «todo bien»): la suite completa (prohibida; corrí 82 + 49 archivos explícitos);
  MODIS real (pyhdf roto en Windows: todo es sintético); el resultado del CI en GitHub del PR B (no consulté la API
  por eso); `docs/*.md` fuera de README, SINTOMAS, INDEX y STATUS; scripts de `experiments/`; lo del frente 2
  (tablero, simulación de reversión) y del frente 3 (crons, concurrencia, lector V375-E) salvo lo que tropecé y anoto.

## 2. En una pantalla

1. El PR B deja un consumidor vivo que cree que el MODIS de producción es K: `scripts/vigilancia_sombra.py:432` cuenta
   los records de la vía como «producción (K)»; medido, una protegida que C0 publica y la vía calla abre el issue de
   reversión de K igual que si K callara (MA172-101).
2. La punta del PR B tiene una prueba roja que el implementador no corrió: `tests/test_guard_adopcion_k_s153.py:45-48`
   (verde en da67 y con sólo el flag; roja en b42823194); el CI del PR la va a mostrar (MA172-103).
3. El mapa del tablero no reconoce `final_hotspot_source = "codigo_mirova"`: medido, un record «summit» de la vía con
   el cúmulo a 0,32 km dibuja su marcador rojo a 14,89 km (MA172-102, el efecto visual es del frente 2).
4. La vía en sí está cubierta: 7 mutaciones semánticas atrapadas por aserción y el control de caída sale sólo con
   caídas; la línea base roja del censo se encontró entera; el cambio a `process_modis.py` es sólo comentario (AST igual).
5. Faltan propagaciones A113 y declaraciones: perfil «reproceso histórico con K» que hereda la vía, README, SINTOMAS,
   aviso del tablero y cabeceras FICHA que siguen diciendo K o APAGADA.

## 3. Hallazgos (ordenados por gravedad)

### MA172-101
- TÍTULO: la vigilancia de la sombra de K cuenta los records MODIS de la vía como «producción (K)» y dispara contra K
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py:432` (`prod = [r for r in bp.cargar_nuestros(coords, inner, win) if
  r.get("sha")]   # sólo records de K`); `pipeline/store.py:549` (`record["regimen"] = _marca_regimen()`, sin condición,
  así que todo record de la vía trae `codigo_sha`); texto del issue en `.github/workflows/vigilancia-sombra.yml:135`.
  SCRIPT:SALIDA `scripts/m3_vigilancia_sombra_ve_la_via_como_k.py` → `m3_salida.txt`, `m3_trabajo/m3_resultado.json`.
- QUÉ PASA: si una noche MIROVA alerta en MODIS, el laboratorio C0 lo ve y la vía nueva calla, el sistema de
  vigilancia de K lo atribuye a K, porque el filtro «sólo records de K» es «trae marca de régimen», y desde el PR B los
  records MODIS de la vía también la traen. Medido sobre datos sintéticos con el predicado del tablero (node): E1 (vía
  calla) da REVERSION_CANDIDATA igual que E2 (K calla); E3 (vía publica) da VERDE; E4 (sin marca) queda fuera del filtro.
  Con los datos reales el plazo de K ya está cumplido (`data/audit_continuous/sombra_latest.json` generado
  2026-11-01T19:44:13Z: `"protegidas_vistas_en_sombra": 54, "objetivo": 29, "cumplida": true`), así que hoy saldría
  como «Sombra de K: candidata fuera de plazo» o como persistencia, siempre rotulado K. El diseño
  (`docs/superpowers/specs/2026-11-01-encendido-modd-design.md` l. 46-47, TEXTO: «sin modificar ese archivo (vigila K»)
  deja el archivo como está y ni el diseño, ni el cuerpo del PR B, ni el informe del implementador declaran este efecto.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero; se ve como un issue de GitHub que culpa a K (cuyo texto
  pre-autoriza revertir el PR de adopción de K) por algo que hizo la vía, al mismo tiempo que la vigilancia de la
  guardia puede no decir nada (si la guardia K también calla).
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/s172_miniaud/f1/copia_b && PYTHONDONTWRITEBYTECODE=1 python
  ../scripts/m3_vigilancia_sombra_ve_la_via_como_k.py . ../m3_trabajo`; Láscar, pasada MODIS 2026-11-05 07:35 UTC
  (sintética), adopción 2026-10-18 09:57:30.
- CONFIANZA: CONFIRMADO (medido; denominador: 4 escenarios sintéticos, 1 pasada cada uno; ventana 2026-11-01 a
  2026-11-10). Que en datos reales caiga como «fuera de plazo»: CONFIRMADO por la lectura del JSON de hoy; que llegue a
  pasar en la operación: SOSPECHA (depende de que C0 publique una protegida que la vía calle).
- GRAVEDAD 1-5: 3 (puede llevar a decidir sobre el detector equivocado: revertir o investigar K por una pérdida de la
  vía, con dos vigilancias que atribuyen distinto).

### MA172-102
- TÍTULO: el tablero no reconoce `codigo_mirova` como ancla honesta: el marcador del mapa de un record de la vía cae en
  el primer píxel alertado en orden de barrido, que puede estar lejos del cúmulo publicado
- ARCHIVO:LÍNEA: `frontend/index.html:1631` (lista `["test1_roi", "test1_nti_peak", "ctx_cluster"]`), repetida en
  l. 1697, 2735, 2766, 3283, 3677 y 3683; el registro de la vía la escribe en `pipeline/mirova_v750_codigo.py:742`
  (`"final_hotspot_source": "codigo_mirova"`) y ordena `anomaly_pixels` por `np.nonzero` (l. 727). SCRIPT:SALIDA
  `scripts/m10_marcador_mapa_via.py` → `m10_salida.txt`, `m10_marcador.json`.
- QUÉ PASA: la vía suma todos los píxeles alertados de la grilla, también los lejanos, y etiqueta summit/far por el
  centroide del cúmulo más radiante. El tablero sólo usa el ancla del record si la fuente es una de las tres de K; con
  la vía cae a `anomaly_pixels[0]`, que es el primer alertado de la grilla de norte a sur, no el más caliente ni el del
  cráter. Medido con el procesador real y la función `pixelesDelMarcador` ejecutada en node: record `summit`, cúmulo a
  0,318 km, marcador por defecto a 14,89 km (fila 10); el control con `ctx_cluster` da el cúmulo (0,318 km). Las
  distancias de tabla y dispersión usan `hotspot_dist_km` (píxel pico) en vez del centroide (l. 2737, 3285, 3684).
- CÓMO SE VE EN EL DASHBOARD: un marcador rojo de «cráter» a 15 km del cráter en una pasada MODIS de la vía con calor
  en el flanco y en la cumbre a la vez. Lo que ve exactamente el operador lo debe medir el frente 2.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/s172_miniaud/f1/copia_b && PYTHONDONTWRITEBYTECODE=1 python
  ../scripts/m10_marcador_mapa_via.py . ../m10_marcador.json`; Láscar, gránulo sintético MYD021KM.A2026115.0735
  (2026-04-25 07:35 UTC), píxeles de 300 K en el cráter y 290 K a 15 km al norte.
- CONFIANZA: CONFIRMADO para la función medida (1 record sintético); el efecto en datos reales (cuántas pasadas de la
  vía traen alertados lejanos antes que los del cráter): SOSPECHA.
- GRAVEDAD 1-5: 3 (ubicación de la anomalía mal dibujada en el mapa con color de cumbre).

### MA172-103
- TÍTULO: la punta del PR B tiene una prueba roja: el guard de la adopción de K exige que laboratorio y producción
  difieran exactamente en los tres flags de K
- ARCHIVO:LÍNEA: `tests/test_guard_adopcion_k_s153.py:45-48` (TEXTO: «assert difieren == set(K), difieren»).
  SCRIPT:SALIDA `m8_guard_adopcion_k.txt`; `m4_pytest_copia_b.txt` l. 27 (`AssertionError: {'ENABLE_MODIS_B22_PRIMARY',
  'ENABLE_MODIS_CODIGO_MIROVA', 'ENABLE_TEST1_PATH', 'ENABLE_TESTS_23_PROSE_BRANCH'}`).
- QUÉ PASA: el PR B declara la vía apagada en `experimental` y encendida en producción, así que ahora difieren en
  cuatro flags; ajustó `tests/test_experimental_congelado_s150.py` (misma pregunta) pero no este archivo. Pasa en
  `copia_da67` y en `copia_flip`, falla sólo en `copia_b`. El informe del implementador lista dos fallas de ambiente
  (libro de pruebas) y no esta: su lista de archivos no la incluyó. `.github/workflows/tests.yml` corre `pytest tests/`
  en `pull_request` (l. 14 y 49), así que el CI del PR B saldrá rojo por esto (SOSPECHA hasta verlo en GitHub).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/s172_miniaud/f1/copia_b && python -m pytest -p no:cacheprovider -q
  tests/test_guard_adopcion_k_s153.py` (y lo mismo en `copia_da67`, verde).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2 (no tuerce una alerta; obliga a mergear sobre rojo o a otro commit, A39 enmienda S142).

### MA172-104
- TÍTULO: el perfil del «reproceso histórico con K» hereda la vía y su prueba de identidad sigue verde
- ARCHIVO:LÍNEA: `pipeline/profiles/_s154_reproc_k_historico.yaml:1` (TEXTO: «REPROCESO HISTORICO CON K») y l. 12
  (`extends: mirova_equivalent`, sin la clave); lo usan `scripts/reemplazar_ventana_reproceso.py:7` y
  `.github/workflows/reproc-chunked.yml` (perfil por entrada). SCRIPT:SALIDA `m1_perfiles_salida.txt` (fila
  `_s154_reproc_k_historico ... via=True modis=True`).
- QUÉ PASA: es la herramienta viva para reescribir la historia de la réplica. Tras el PR B, un reproceso histórico
  «con K» escribe MODIS con la vía, y `reemplazar_ventana_reproceso.py` sólo exige `regimen.perfil` igual al esperado,
  así que esa historia entra a `data/mirova_equivalent/` rotulada como el perfil de K. El diseño dice (TEXTO, l. 75-76:
  «Ningún reproceso histórico: la vía corre desde el merge del PR B hacia adelante») y el cuerpo del PR B (l. 35-36)
  despacha los brazos viejos como «de despacho manual y ya corrieron»; este no es un brazo viejo y nadie lo decidió.
- CÓMO SE VE EN EL DASHBOARD: invisible hasta que alguien aplique un reproceso; después, historia MODIS de la vía
  donde el texto dice K.
- CÓMO REPRODUCIRLO: `cd copia_b && VRP_PROFILE=_s154_reproc_k_historico python -c "import pipeline.profile as p;
  print(p.ENABLE_MODIS_CODIGO_MIROVA)"` da True.
- CONFIANZA: CONFIRMADO (valor); que se vuelva a usar: SOSPECHA.
- GRAVEDAD 1-5: 2.

### MA172-105
- TÍTULO: textos que siguen diciendo que el MODIS de producción es K, sin marca A113
- ARCHIVO:LÍNEA: `README.md:52-56` («la banda 22 primaria en MODIS ... reprocesado con K»), `docs/SINTOMAS.md:25-28`
  («Régimen vigente: el detector K está en producción ... banda 22 primaria en MODIS»), `frontend/index.html:544`
  (aviso visible: «Desde el 18 oct 2026 la réplica usa el detector K»). SCRIPT:SALIDA `m5_docs_modis_es_k.txt`.
- QUÉ PASA: el PR B marcó MISSION, CLAUDE y MIROVA_DIVERGENCES, pero `docs/SINTOMAS.md` es lo que CLAUDE.md manda leer
  antes de proponer una palanca, y el aviso de `index.html:544` lo lee el operador en la sección de métricas.
- CÓMO SE VE EN EL DASHBOARD: el aviso de métricas dice que la réplica usa K sin excepción para MODIS.
- CÓMO REPRODUCIRLO: `grep -n "detector K" README.md docs/SINTOMAS.md frontend/index.html` en `copia_b`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2.

### MA172-106
- TÍTULO: cabeceras FICHA SDA y comentarios POR QUÉ de archivos que ahora corren en producción siguen diciendo APAGADA
- ARCHIVO:LÍNEA: `pipeline/mirova_v750_codigo.py:5-6` (TEXTO: «APAGADA por flag en cada sensor ...; con los flags
  apagados no corre nada de este archivo»); `pipeline/store.py:351-356` (TEXTO: «enable_v750_codigo_mirova, APAGADO» y
  «Con el flag apagado ningún record trae la marca»).
- QUÉ PASA: el PR B actualizó sólo la cabecera de `process_modis.py`; el archivo que hace la detección MODIS de
  producción y la rama del almacén que la deja pasar sin las compuertas de K siguen descritos como apagados. La
  convención de la Resolución CPLT N°372 del proyecto pide que la cabecera diga lo que corre.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sed -n 1,8p pipeline/mirova_v750_codigo.py; sed -n 350,357p pipeline/store.py` en `copia_b`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2 (transparencia algorítmica).

### MA172-107
- TÍTULO: el cuerpo del PR B no declara el cambio del ancla pre-K ni los ajustes de arneses de prueba
- ARCHIVO:LÍNEA: `experiments/_s171_modd_adopcion/PR_B_CUERPO.md:27-44` (sección «Qué cambia», cierra con «Nada más»).
- QUÉ PASA: el diff (`01_diff_B_codigo.patch`) cambia `pipeline/profiles/_s146_ab_control.yaml`,
  `tests/produccion_pre_k.py` (FLAGS_POSTERIORES), los tres arneses (`arnes_mxd03_s165.py`, `arnes_sin_dato_s165.py`,
  `arnes_sintetico_s142.py`), un fixture autouse en `tests/test_process_modis_core.py` y
  `tests/test_experimental_congelado_s150.py`; el cuerpo sólo nombra experimental, ndc_focus y dos pruebas. El informe
  del implementador (`c83882fcf`, puntos 1 y 2) sí lo declara, pero ese archivo no viaja en la historia del PR B.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git diff --stat da67fa417 b42823194` contra la sección citada.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1.

### MA172-108
- TÍTULO: el conteo «28 pruebas ajustadas, 26 fijan K» no se reproduce: con el flag solo fallan 33 en mi conjunto
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `m4_fallas_causadas_por_flip.txt` (33 = fallas de `copia_flip` menos las 2 de ambiente
  de `copia_da67`), `m4_pytest_copia_flip.txt`, `m4_pytest_copia_da67.txt`, `m4_pytest_copia_b.txt`.
- QUÉ PASA: sobre 82 archivos (lista `m4_lista_archivos_da67.txt`), el flag solo rompe 33: 4 que fijan el valor del
  flag (2 parametrizaciones de s164, `test_flag_se_lee...`, sombra s167) y 29 que corren MODIS con producción (9
  crater_sin_dato, 6 mxd03_cumulo_121, 3 mxd03_sola_123, 1 mxd03_etiquetas, 2 guard_mxd03_flags, 2
  apagado_no_cambia_nada, 4 process_modis_core, 2 de s164). Las 33 pasan en `copia_b`. La diferencia con 28/26 se
  explica en parte porque el implementador midió con `experimental` ya apagado (eso rompe test_experimental_congelado
  y no las dos parametrizaciones de `experimental`); el resto no lo pude atribuir. No hay ninguna de las 33 sin arreglar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -m pytest -p no:cacheprovider -q -rfE --tb=line $(cat m4_lista_archivos_da67.txt)` en
  `copia_flip` y en `copia_da67`; restar.
- CONFIANZA: CONFIRMADO (mi conteo); la causa de la diferencia: SOSPECHA.
- GRAVEDAD 1-5: 1.

### MA172-109
- TÍTULO: el reconocimiento del volcán por coordenadas, puerta de entrada de la vía, sólo lo vigila una caída
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:640` (`volcan_nombre = _MV.volcan_por_coordenadas(volcano_lat,
  volcano_lon)`). SCRIPT:SALIDA `scripts/m6_mutaciones.py` (M9) → `m6_m9_salida.txt`.
- QUÉ PASA: la vía reconoce el volcán por igualdad exacta con `volcanoes.yaml`; si una refactorización le pasara el
  ancla de detección, en todo volcán con ancla distinta la vía caería a K con la marca `sin_grilla` sin que nada
  falle por aserción: la mutación M9 da 1 falla, y es una caída (la excepción centinela `_K` de
  `test_flag_encendido_devuelve_el_record_de_la_via`), 0 por aserción. En operación lo atraparía el aviso
  «flag encendido sin records de la vía» de `scripts/vigilancia_guardia_modis.py:304-306` sólo si la vía cae en todos.
- CÓMO SE VE EN EL DASHBOARD: invisible (MODIS volvería a K en esos volcanes).
- CÓMO REPRODUCIRLO: `python scripts/m6_mutaciones.py copia_mut copia_b m6_mutaciones_m9 M9_reconoce_volcan_por_el_ancla`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1.

### MA172-110
- TÍTULO: `experimental_lowT` hereda la vía y no lo cubre ni el guard ni la declaración del implementador
- ARCHIVO:LÍNEA: `pipeline/profiles/experimental_lowT.yaml` (extends mirova_equivalent, sin la clave); lo nombran
  `scripts/run_pilot_a5_s76.py` y `scripts/analyze_pilot_a5_results.py`. SCRIPT:SALIDA `m1_perfiles_salida.txt`,
  `m1b_perfiles_con_workflow.txt`, `m1c_resumen_herencia.txt`.
- QUÉ PASA: el guard nuevo sólo decide perfiles nombrados por workflows programados; el informe del implementador
  (punto 3) declara «todos los `_*.yaml`», y este no empieza con guion bajo. Contexto: 60 perfiles extienden
  producción, 55 heredan la vía (True), 45 de ellos corren MODIS y 16 de esos los nombra un workflow activo (todos de
  despacho manual) o un script.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd copia_b && VRP_PROFILE=experimental_lowT python -c "import pipeline.profile as p;
  print(p.ENABLE_MODIS_CODIGO_MIROVA)"` da True.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1.

### MA172-111
- TÍTULO: un perfil deprecado escribe en la carpeta de producción con la vía apagada
- ARCHIVO:LÍNEA: `pipeline/profiles/mirova_equivalent_villarrica_test1.yaml` (sin extends, `data_subdir:
  mirova_equivalent`, cabecera «DEPRECADO S124 ... NO USAR»); lo menciona `.github/workflows/nrt.yml:154` en un
  comentario. SCRIPT:SALIDA `m1_perfiles_salida.txt` (via=False, subdir=mirova_equivalent).
- QUÉ PASA: si alguien lo despacha tras el PR B, mete records MODIS de un detector viejo (ni K ni la vía) en la serie
  de producción. Preexistente; el PR B no lo empeora salvo que ahora la serie MODIS de producción sería de la vía.
- CÓMO SE VE EN EL DASHBOARD: invisible salvo que se despache.
- CÓMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent_villarrica_test1 python -c "import pipeline.profile as p;
  print(p.DATA_SUBDIR, p.ENABLE_MODIS_CODIGO_MIROVA)"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1.

## 4. SEGUIMIENTOS (fuera de mi eje)

- El diseño escribe el vencimiento de la vigilancia de K como «~2026-02-15»
  (`docs/superpowers/specs/2026-11-01-encendido-modd-design.md:47`); el dato dice 2027-02-15
  (`data/audit_continuous/sombra_latest.json`, `"vence": "2027-02-15"`). Confianza: CONFIRMADO.
- El guard nuevo dice «58 perfiles hacen `extends: mirova_equivalent`»
  (`tests/test_guard_modis_codigo_mirova_encendido_s172.py:9`); con A más B son 60 (`m1c_resumen_herencia.txt`).
  Número sin script, A90. Confianza: CONFIRMADO.
- Los píxeles de la vía no traen `vrp_mw` por píxel (`pipeline/mirova_v750_codigo.py:727-731`); el toggle del mapa
  «Todos los pixels» ordena «top-10 por VRP» (comentario `frontend/index.html:3060`). Con la vía ese orden no está
  definido. Para el frente 2. Confianza: SOSPECHA.
- `scripts/vigilancia_guardia_modis.py:85-102` fecha el encendido con `first_processed_utc` o `processed_utc`, y
  `processed_utc` se reescribe en cada versión del record (`pipeline/store.py:541`). Para quien audite el PR A.
  Confianza: SOSPECHA.

## 5. VERIFICADO LIMPIO

- Línea base roja del barrido: el censo por nombre (`02_censo_grep_nombres.txt`, comando en su primera línea, 235
  líneas fuera de `data/`) encuentra `pipeline/profiles/experimental.yaml:66`, `experimental_ndc_focus.yaml:44`,
  `_s146_ab_control.yaml:42` y `tests/test_guard_modis_codigo_mirova_encendido_s172.py`. El instrumento no está ciego.
- Valor efectivo del flag en los 101 perfiles leído con el cargador real (`m1_perfiles.py`, un subproceso por perfil):
  producción True, `sombra_codigo_mirova` True, `guardia_k_modis`, `experimental`, `experimental_ndc_focus`,
  `_s146_ab_control` False. Vara: `pipeline.profile` (A89); control: dos valores opuestos en la misma corrida.
- Ningún workflow programado se le escapa al guard por `on:` sin comillas (`m7_guard_on_sin_comillas.txt`: 14 vistos,
  0 escapan; control: se cuenta también la clave booleana).
- Los campos que lee el predicado del tablero (`CAMPOS_JS` de `scripts/banco_paridad.py`) están todos en el record de la
  vía (`m2_claves.json`: `CAMPOS_JS_solo_k` vacío; el record de la vía tiene 26 claves, el de K 53). Los 29 campos que
  sólo trae K los leen fallbacks `??`, el CSV de exportación y scripts no programados (`m2b_consumidores_campos_solo_k.txt`).
- `scripts/build_recent_json.py` sólo filtra por fecha y conserva `via_codigo_mirova` (leído l. 52-60), así que la
  marca de `frontend/cambio_detector.js:159` la puede ver en el JSON liviano.
- `pipeline/process_modis.py`: el PR B sólo cambia comentarios (`m11_ast_process_modis.txt`: 1792 líneas en ambos, AST
  igual; control: un cambio de una expresión da AST distinto). Lo declaran el cuerpo del PR B (l. 41-42) y el informe
  del implementador (punto 8); el diseño no lo menciona.
- Cobertura de la vía como la corre producción (`m6_salida.txt`, `m6b_salida.txt`; 17 archivos, 326 pruebas; M0 sin
  fallas): atrapadas por aserción M1 (la vía nunca corre, 4), M2b (sin record cae a K, 1 más un desplazamiento de
  línea), M3 (run_pipeline pasa el ancla, 2, indirecto vía arnés de K), M4 (producción apaga el flag, 7), M5 (el
  almacén trata la vía como K, 4), M7 (coeficiente de V750 en MODIS, 8), M8 (sin radio interior, 3). Control M6
  (caída provocada): 5 caídas, 0 aserciones. M2 original era de caída por construcción y no cuenta.
- Las 33 pruebas que el flag solo rompe pasan en `copia_b`; en 49 archivos de prueba más que leen perfiles
  (`m9_lista_ampliada.txt`) el PR B no agrega fallas (`m9_pytest_copia_b.txt` y `m9_pytest_copia_da67.txt`: la misma
  falla de ambiente en los dos).
- `scripts/vigilancia_guardia_modis.py:116-125` lee el flag de producción desde `pipeline.profile` en un subproceso
  (A89) y avisa si está encendido sin records de la vía (l. 304-306). Leído, no ejecutado.

## 6. SIN DATO

- CI del PR B en GitHub: no lo consulté; MA172-103 predice rojo, sin verlo.
- Suite completa sobre b42823194: prohibida en esta tarea; corrí 82 + 49 archivos explícitos.
- Efecto en datos reales de MA172-102 (cuántas pasadas de la vía tienen alertados lejanos primero): no hay records de
  la vía en producción todavía.
- MODIS real extremo a extremo: pyhdf no corre en Windows.

## 7. FUERA DE ALCANCE

- Lo que ve el operador en el tablero más allá de MA172-102, y la simulación de reversión (frente 2).
- Crons, concurrencia de workflows y el lector de V375-E (frente 3).
