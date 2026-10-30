# Verificación del candado de MOD-D fase 4 (commit 3db87f50d)

## 1. Encabezado

- Fecha y hora del servidor: empecé a las 00:41 UTC y escribí este informe a las ~01:03 UTC del viernes 30-oct-2026 (`date -u`).
- Commit medido: `3db87f50d` (extraído con `git -c core.autocrlf=false archive`, en `arbol\`). Vara: el pre-registro sellado `experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` (tag `s168-modd-f4-sellado`, commit `3768e9431`), §4, §8, §11 y §13.
- Modelo y esfuerzo: Claude Sonnet 5.5 (claude-sonnet-5-5), esfuerzo bajo (el que dio el entorno).
- CARPETA: `D:\vrp-trabajo\temporales\s169_ver_candado\` (este informe, `caminos.md`, `hallazgos.csv`, `scripts\` con cada script y su salida al lado, `arbol\`, `tmp\`).
- Agregué al árbol extraído, con `git show 3db87f50d:<ruta>`, los 8 archivos que el manifiesto cita y la extracción no traía: `experiments/_s157_prereg_d25/evaluar_d25.py` (blob 1dbabf65 comprobado con `git hash-object`), `experiments/_s146_ab_sin_test1/evaluar.py`, `_s151_mxd03_cumulo_121/probe_cumulo.py`, `_s151_mxd03_etiquetas/probe_etiquetas.py`, `_s151_mxd03_sola_123/jobs_123.py` y `probe_sola.py`, `_s151_prereg_fk_11/evaluar_fk.py`, `_s151_probe_mod03/probe_mod03.py`. Todo dentro de CARPETA. No toqué el repositorio (solo `git show`, `git diff`, `git ls-tree`, `git log`, `git grep` de lectura). Cero red, cero tokens, nada despachado.
- Qué NO miré, para que mi silencio no se lea como "todo bien": no recalculé etiquetas ni la población (no hay `data/` ni los CSV de Mirova-v1 en el árbol); no corrí `reetiquetado_f4.py`, `ensayo_en_seco_f4.py`, `mutar_evaluar_f4.py` ni las mutaciones del arnés (pesado o dependiente de `data/` y del git del repo); no probé LAADS ni el token (sin red); no corrí el workflow en GitHub; no leí `probe_f4.py` línea por línea (solo `main()`, imports perezosos, `pasadas_de_la_parte` y las mutaciones), ni `evaluar_f4.py` más allá de `control_identidad`, `control_posicion`, `control_predicado` y su diff contra el sello; no verifiqué el contenido del PREREGISTRO fuera de §4, §8, §11 y §13. La primera tanda de la batería del evaluador la cortó mi timeout de 280 s en E46; la terminé con `--solo`.

## 2. En una pantalla

1. Las ocho afirmaciones se sostienen en lo que pude medir. Tres cosas no se pudieron re-ejecutar y quedan SIN DATO con su comando: A3(b)(c), las mutaciones del arnés (A4) y el ensayo en seco.
2. **Defecto real que bloquea la lectura (VC169-01, gravedad 3):** `externos_referencia.json` guarda el sha256 de la población con fin de línea CRLF (`5e0147b0...`) y el commit trae la población en LF (`e8315ba4...`). En cualquier checkout LF (runner Linux, `git archive`, WSL) `externos_f4` deja `referencia` y `reetiquetado` en INDECIDIBLE y el veredicto sale INDECIDIBLE. Falla cerrado, pero hay que arreglarlo antes del tag; el ensayo en seco (juguete) no lo habría visto.
3. El manifiesto de 64 archivos es correcto (lo recalculé aparte), pero no cubre `scripts/run_pipeline.py`, `pipeline/fetch.py`, `process_viirs*.py`, `test1_*.py` ni `pipeline/volcanic_features.yaml`, que el arnés y la identidad usan en ejecución (VC169-02). La identidad no compara la clase del record del runner (VC169-03). Las mutaciones del evaluador siguen siendo las de 63 escenarios (VC169-04).
4. **Veredicto del candado: CANDADO VERIFICABLE PARA TAG CON CAMBIOS** (cambios mínimos en la sección 10).
5. **Veredicto del workflow: MERGEABLE YA**, solo ese archivo y byte-idéntico (sha256 LF `50d9fc92...`): único trigger `workflow_dispatch`, `contents: read` en los tres jobs con pasos, único secreto `EARTHDATA_TOKEN`, ni push ni commit ni escritura en `data/`; fuera de un tag falla cerrado, salvo `head_e` que queda verde sin hacer nada.

## 3. Veredicto por afirmación

Cada script y su salida están en `scripts\` (nombre indicado). Las dos preguntas del instrumento van en la cabecera de cada script.

| ID | Veredicto | Gravedad mía | Evidencia |
|---|---|---|---|
| A1 población | CONFIRMADO | 1 | `a1_poblacion.py`: 5.709 pasadas únicas (C 5.465, E 244); `grilla_censo` verdadera en 5.321 y todas de C (388 filas traen `False`); `lab == protegida` 56 (C 50, E 6); `sin_pasada_nuestra` y su detalle en 0. `a1_cruces.py`: las 144 pasadas de C sin grilla son 92 neg_limpio y 52 sin_info; 5.465 menos 144 es 5.321. `a1_umbrales.py`: ninguna protegida bajo 1 MW (mínimo 1,00), ninguna bajo1 sobre 1 MW (máximo 0,99), cero bajo1 con 0,05 MW o menos. `a1_contrato_rerun_salida.txt`: re-corrí `contrato_poblacion_f4.py` en mi árbol, salida idéntica a la del commit, "CONTRATO: CALZA". `a5_grillas_existen.py`: las 5.321 rutas `grilla_censo` existen en `D:\vrp-trabajo\temporales\s162_modd\censo\` (1.779 + 1.775 + 1.767 en tres runs); control de ruta inventada, False. NO recalculé las etiquetas desde la referencia: SIN DATO. |
| A2 HEAD tramo E | CONFIRMADO | 1 | `a2_head.py`: las 106 URL de `e_candidatas` son exactamente las claves de `head_e.json` (53 L1B + 53 MxD03), todas con status 200, `pide_urs` 0, sin errores, 10 de 10 días `sirve`, `dias_e_excluidos` vacío; el control sintético (quitar una URL) se detecta. `head_e.py:78-90` hace `requests.head` sin cabecera Authorization en modo `--publico` y trae control positivo (200) y negativo (404). Lo de "sin credenciales" lo respalda el modo registrado `publico`; no repetí la red. Salvedad (SOSPECHA, gravedad 1): un 200 público sobre una URL firmada de CloudFront no prueba que la bajada con token del runner se comporte igual; el job `head_e` del workflow lo repite con token. |
| A3 referencia | CONFIRMADO EN PARTE | (a) 1; amarre a la población 3 (VC169-01) | (a) CONFIRMADO por otro camino: `a3_sha_ref_local_salida.txt` recalcula el sha256 de las copias locales de S165 (`D:\vrp-trabajo\temporales\s165_regla_posicion\ref\`): `811c4c07...` y `01c9478d...`, iguales a los de `reetiquetado_f4_salida.txt` y a `git show loop/activo:experiments/_s165_regla_posicion/referencia_salida.txt`. (b) "dos corridas iguales" y (c) "0 distintas en 5.465 con la referencia del censo": solo los leí en la salida del autor; no los re-ejecuté (necesitan el repo con `data/` y las dos referencias): SIN DATO propio. **Defecto nuevo: el sha de la población que `externos_referencia.json` registra no es el del commit (VC169-01).** |
| A4 arnés | CONFIRMADO EN PARTE | 2 | La salida del autor dice 18 de 18, 16 de 16 atrapadas sin caídas y controles VIVA, CAE, ROTA; su cabecera trae el sha256 LF de `probe_f4.py` (`4ff7b5a5...`), que es el de hoy y el del manifiesto. Lo re-corrí sin mutaciones (`a4_probar_probe_sin_mut_salida.txt`, 15 s): 15 de 18 OK; `t_data`, `t_arbol` y `t_cabecera` fallan porque mi árbol no es repo git ni trae `data/` (esperado: eso es lo que prueban). Las 16 mutaciones (19 baterías, unos 5 min) no las re-ejecuté: SIN DATO. Por lectura (`probar_probe_f4.py:500-558`): ATRAPADA exige al menos una aserción y ninguna caída, y la salida es 1 si algún control no sale como debe. |
| A5 identidad | CONFIRMADO | 2 (VC169-03) | `a5_probar_identidad_salida.txt`: re-corrí `probar_identidad_f4.py` (70 s, TMP en mi carpeta, contra las grillas locales del censo): "RESUMEN: 8 de 8 OK" sobre 101 grillas; los controles en rojo salen rojos (S2 celda cambiada, S3 segundo otro gránulo, S4 faltante, S6 captura alterada, S8 un l1b distinto). Salvedad: el "runner" de la prueba se arma con las mismas grillas del censo, así que prueba el comparador y su cruce con `control_identidad`, no la lectura real del HDF. |
| A6 manifiesto | CONFIRMADO | 2 (VC169-02, VC169-07) | `a6_manifiesto_comprobar_salida.txt` (`manifiesto_candado_f4.py` sin `--escribir`: OK, n=64, faltan [], distintos []). `a6_manifiesto_indep.py`: recalculé aparte los 64 sha256 LF, 0 distintos; `tag` y `commit_tag` en null. La cobertura tiene huecos (VC169-02). |
| A7 workflow | CONFIRMADO con matices | 1 | Sección 5. |
| A8 evaluador | CONFIRMADO | 2 (VC169-04) | `a8_bateria_real_salida.txt` (E01 a E46) y `a8_bateria_real_parte2_salida.txt` (E47 a E64, N01, N02): 46 + 20 = 66 escenarios distintos, 66 OK, 0 fallas, 0 caídas. `a8_bateria_vacio_salida.txt`: contra `evaluar_vacio.py`, "RESUMEN: 66 escenarios, 0 OK, 66 fallan por aserción, 0 caen" (0,7 s); esa línea contiene literalmente " 0 OK, " y " 0 caen", que es lo que busca el workflow. `git diff 3768e9431 3db87f50d -- experiments/_s166_modd_f4/evaluar_f4.py`: vacío; sha256 de `evaluar_f4.py` en el tag sellado y en 3db87f50d: `8a1edc14...` ambos; sha256 del PREREGISTRO en ambos: `a2bd15ee...`; `git diff --stat s168-modd-f4-sellado 3db87f50d -- pipeline scripts frontend volcanoes.yaml experiments/_s162_mxd03 experiments/_s157_prereg_d25`: vacío. Solo cambiaron `probar_evaluar_f4.py`, `mutar_evaluar_f4.py` y dos salidas. VS-01 a VS-08: cada uno tiene su cambio en el diff (ATRAPADA_CON_CAIDAS, E53 acotado a "math domain error", E62, `N_GRILLAS_CENSO == 5321` en E41, E63, E64, `--traza`, M83 a M86). Pero la **medición de mutaciones con la batería nueva no existe** (VC169-04). |

## 4. Hallazgos

Ordenados por gravedad; los mismos están en `hallazgos.csv`.

### VC169-01
- TÍTULO: `externos_referencia.json` registra el sha256 de la población en CRLF y el commit la trae en LF: referencia y re-etiquetado quedan INDECIDIBLES en cualquier checkout LF
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/externos_f4.py:94-99` (compara `ref["poblacion_sha256"]` con `{sha256_bytes, sha256_lf}` de la población local); `experiments/_s166_modd_f4/reetiquetado_f4.py:80,171` (`PF.sha256(a.poblacion)` sin `lf=True`; definición en `poblacion_f4.py:95-99`); dato en `experiments/_s166_modd_f4/externos_referencia.json`, campo `poblacion_sha256` = `5e0147b0f92b9730028a53b6710d42c0446c1e2ee77c07f9f59af3d72ad5aac6`. SCRIPT:SALIDA `scripts/a3_externos_sha.py : scripts/a3_externos_sha_salida.txt`.
- QUÉ PASA: lo que se mide (las etiquetas contra la referencia) está bien; el amarre entre esa medición y la población que lee el evaluador está roto por el fin de línea. `poblacion_f4.py` escribió el JSON en Windows con CRLF (sha `5e0147b0...`, el que imprimen `poblacion_f4_salida.txt` y `reetiquetado_f4_salida.txt`); git lo normalizó a LF al commitear (blob de 6.668.399 bytes, sha256 `e8315ba4...`, el que usa el manifiesto), y `externos_f4.referencia_y_reetiquetado` solo acepta el sha del archivo local tal cual o normalizado a LF. Con la población en LF el sha CRLF no está en el conjunto y las dos claves salen INDECIDIBLE con el motivo "se midió sobre otra población que la local".
- CÓMO SE VE EN EL DASHBOARD: invisible (el A/B no publica nada); en la lectura, el veredicto de MOD-D fase 4 saldría INDECIDIBLE en vez de evaluarse.
- CÓMO REPRODUCIRLO: `python -I D:/vrp-trabajo/temporales/s169_ver_candado/scripts/a3_externos_sha.py` (llama a la función real). Salida: "committed (CRLF sha en el json) -> referencia INDECIDIBLE, reetiquetado INDECIDIBLE"; control positivo (sha LF en el json) OK; población local con CRLF (checkout Windows con autocrlf) OK. A mano: `tr -d '\r' < poblacion_f4.json | sha256sum` da `e8315ba4...`; agregándole CRLF da `5e0147b0...`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. No sesga el A/B (falla cerrado), pero trabaría la lectura en el runner y se descubriría recién al final de 10 h de tandas. Arreglo posible (no lo hago): regenerar `externos_referencia.json` con `sha256_lf`, o que `reetiquetado_f4.py` use `PF.sha256(..., lf=True)`, antes del tag. El ensayo en seco usa una referencia de juguete con `sha256_bytes` de su propia población (`ensayo_en_seco_f4.py:135-136`), por eso no lo habría visto.

### VC169-02
- TÍTULO: el manifiesto no cubre código y datos que el arnés y la identidad usan en ejecución (su lista se arma solo con lo importado al cargar)
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/manifiesto_candado_f4.py:52-58,74-81` (SONDA: `import probe_f4, evaluar_f4`, más `identidad_f4`); usos perezosos en `probe_f4.py:418` (`download_granules`), `:523-524` (`import run_pipeline as rp`, `from pipeline.fetch import auth`) y `identidad_f4.py:88` (`import run_pipeline as rp`). SCRIPT:SALIDA `scripts/a6_manifiesto_perezosos.py : scripts/a6_manifiesto_perezosos_salida.txt`.
- QUÉ PASA: el manifiesto es la defensa de la lectura, que corre "después, en otra máquina y con otro checkout" (su propio docstring). Los módulos que se cargan de forma perezosa quedan fuera: `scripts/run_pipeline.py` (de ahí salen la posición del cráter, el `inner_radius_km` y las `VOLCANIC_FEATURES` que alimentan K, V y la identidad V-grilla), `pipeline/fetch.py`, `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`, `pipeline/test1_contextual_filter.py`, `pipeline/test1_spatial_core.py` y `pipeline/volcanic_features.yaml`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd arbol; python -I ../scripts/a6_manifiesto_perezosos.py`. Salida: base 42 módulos con 0 fuera del manifiesto; tras usar `run_pipeline` y `pipeline.fetch`, 48 con 6 fuera, y `volcanic_features.yaml` fuera.
- CONFIANZA: CONFIRMADO (el hueco); SOSPECHA (que alguien lo toque entre el tag y la lectura).
- GRAVEDAD: 2. En los jobs el tag fija todo (procedencia); el hueco está en la lectura, la identidad y la reproducibilidad.

### VC169-03
- TÍTULO: el control de identidad no compara la clase del record que dejó el runner; la deriva de la grilla
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/identidad_f4.py:179-180,192,210` (`dc_r = vr.get("distance_class")` cuando el npz no la guarda; `captura_coherente` compara esa clase consigo misma); `evaluar_f4.py:471-473` (solo lee `mismo_granulo`, `misma_mascara`, `dvrp`, `misma_clase`); el npz del arnés no guarda la clase (`probe_f4.py:215`). SCRIPT:SALIDA `scripts/a5_probar_identidad_salida.txt` ("clase de {'via_sobre_grilla_runner'}").
- QUÉ PASA: la máscara y el VRP sí son los capturados del record real del runner, pero la clase `summit` o `far` se vuelve a calcular con `procesar_grilla` sobre la grilla del runner. Si el record real de V (después de `calculate_vrp`) saliera con otra clase por otra ancla u otro `inner`, la identidad no lo vería. `v_slim_dc_igual`, `box_igual`, `pos_crater_igual` y `captura_coherente` se calculan, pero ni `control_identidad` ni nada de `evaluar_f4.py` los lee.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "captura_coherente\|box_igual\|pos_crater_igual\|v_slim_dc_igual" experiments/_s166_modd_f4/evaluar_f4.py` no devuelve líneas.
- CONFIANZA: CONFIRMADO (qué se compara y qué no); SOSPECHA (que algún día la clase real difiera con máscara y VRP iguales).
- GRAVEDAD: 2. Cierra barato: guardar `distance_class` en el npz o exigir `v_slim_dc_igual`.

### VC169-04
- TÍTULO: la medición de mutaciones del evaluador es la de 63 escenarios y 82 mutaciones; M83 a M86 y el control de caída con ValueError no se han corrido, y E53 cambió después de medir M70
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/mutar_evaluar_f4_salida.txt` ("MUTACIONES: 82 de 82"; batería de "63 escenarios"); `mutar_evaluar_f4.py:36-38,138-144` (control nuevo y M83 a M86); `PREREGISTRO_MODD_F4.md` §13 (63 y 82); `experiments/_s168/modd_f4_candado/INFORME.md` ("queda viejo hasta esta corrida"). SCRIPT:SALIDA `grep -c '^M[0-9][0-9]_' mutar_evaluar_f4_salida.txt` = 82 contra 86 en `mutar_evaluar_f4.py`.
- QUÉ PASA: lo declara el propio autor, pero cuenta para la vara: "atrapada" hoy es ATRAPADA sin caídas con la batería de 66, y esa medición no existe. La batería sí está medida (66 de 66, y 66 de 66 rojos contra el vacío, mías).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s166_modd_f4/mutar_evaluar_f4.py --paralelo 1` con TMP en D: (el autor estima unas 9 h; no lo corrí).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (pendiente declarado; no puede ir al tag sin cerrarse).

### VC169-05
- TÍTULO: el "ensayo en seco" del §11 punto 6 no tiene salida y, con externos de juguete, no ejercita la referencia real
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/ensayo_en_seco_f4.py:135-139`; `PREREGISTRO_MODD_F4.md` §11 punto 6; no existe `ensayo_en_seco_f4_salida.txt` en el commit (lista de `experiments/_s166_modd_f4/`).
- QUÉ PASA: el candado enumera humo y ensayo en seco; el ensayo no se corrió. Aun corrido, arma `externos_referencia` de juguete con `sha256_bytes` de su propia población, así que VC169-01 no aparece.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s166_modd_f4/ensayo_en_seco_f4.py` (comando del autor; pesado, 27.000 records por node; no lo corrí).
- CONFIANZA: CONFIRMADO (ausencia de salida); SOSPECHA (lo que encontraría).
- GRAVEDAD: 2.

### VC169-06
- TÍTULO: nada en el candado ata el pre-registro y el evaluador al blob sellado; el §13 se va a editar y el manifiesto hashea el documento entero
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:36-40,65` (registra el sha de lo que haya al regenerar); `externos_f4.py` (no compara contra `s168-modd-f4-sellado`); `grep -n "s168-modd-f4-sellado\|3768e9431" evaluar_f4.py externos_f4.py manifiesto_candado_f4.py` no muestra código que compare (solo menciones en comentarios).
- QUÉ PASA: hoy `evaluar_f4.py` y `PREREGISTRO_MODD_F4.md` son byte-idénticos al sello (medido: `8a1edc14...` y `a2bd15ee...` en el tag sellado y en 3db87f50d), pero el plan del autor es editar el §13 de un documento sellado y regenerar el manifiesto; después, quien lea solo el manifiesto no puede distinguir una edición del §13 de una del §7. Es una comprobación manual de quien orquesta.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git diff s168-modd-f4-sellado <tag-del-candado> -- experiments/_s166_modd_f4/evaluar_f4.py experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` debe mostrar cambios solo dentro de §13 y §13 ter.
- CONFIANZA: CONFIRMADO (no hay chequeo automático); SOSPECHA (impacto).
- GRAVEDAD: 2.

### VC169-07
- TÍTULO: las 5.321 grillas del censo (265 MB, fuera del repositorio) no tienen sha256 en ningún lado, y el manifiesto dice que `identidad_f4.py` registra su procedencia
- ARCHIVO:LÍNEA: `manifiesto_candado_f4.py:16-17` (la frase); `identidad_f4.py` (cero líneas con `sha256`, `hashlib` ni `procedencia`; solo guarda la ruta en `identidad.json["censo"]`); `poblacion_f4.json` (`grilla_censo` es una ruta relativa, sin hash). SCRIPT:SALIDA `scripts/a5_grillas_existen.py : scripts/a5_grillas_existen_salida.txt` (5.321 de 5.321 existen hoy).
- QUÉ PASA: la identidad se mide contra archivos que podrían cambiar sin que nada lo vea; si cambiaran, lo normal es rojo (falla cerrado), salvo que cambien de forma coherente.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "sha256\|hashlib\|procedencia" experiments/_s166_modd_f4/identidad_f4.py` (sin salida).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VC169-08
- TÍTULO: el job `head_e` corre en todos los modos y, si falta `head_e.py`, termina verde sin hacer nada
- ARCHIVO:LÍNEA: `.github/workflows/probe-s168-modd-f4.yml:67-68` (`needs: [plan]`, sin `if`) y `:84-86` (`exit 0` si no existe `head_e.py`); el comentario de cabecera dice "head_e solo el HEAD".
- QUÉ PASA: despachado desde `main` (donde `head_e.py` aún no existe) el job sale verde y el artefacto trae solo un log de una línea; en los modos t1 a t3 repite los HEAD aunque nada consuma ese artefacto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura del yml (no despaché).
- CONFIANZA: CONFIRMADO (por lectura).
- GRAVEDAD: 1. Para el humo, despachar siempre con `--ref <tag>`.

### VC169-09
- TÍTULO: el job `plan` y el nivel de workflow no declaran `permissions`
- ARCHIVO:LÍNEA: `.github/workflows/probe-s168-modd-f4.yml` (job `plan` sin bloque `permissions`; los otros tres jobs sí traen `contents: read`, l. 71, 112 y 162). SCRIPT:SALIDA `scripts/a7_workflow.py : scripts/a7_workflow_salida.txt` (`permissions: null` en `plan` y en el nivel superior).
- QUÉ PASA: hereda el permiso por defecto del repositorio; `plan` no hace checkout ni usa el token, así que hoy no puede escribir nada.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: ver el script.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1. Si se corrige, que sea antes del merge (cambia el sha del manifiesto).

## 5. A7, el workflow, en detalle

Verificado con `scripts/a7_workflow.py` (PyYAML) y por lectura:
- Clave `"on"` entre comillas (parsea como el string `'on'`), único trigger `workflow_dispatch`. Control positivo: el mismo script sobre `nrt.yml` marca `schedule`, `git push` y `EARTHDATA_USERNAME/PASSWORD`.
- Secretos referenciados: solo `EARTHDATA_TOKEN` (regex `secrets\.X`). La marca `USERNAME/PASSWORD: true` que imprime el script viene de un comentario del yml ("Sin EARTHDATA_USERNAME ni EARTHDATA_PASSWORD"), no de un uso.
- Falla si el token viene vacío: job `probe` (primer paso), job `head_e` (después de comprobar que `head_e.py` existe), y `head_e.py` y `probe_f4.py` lo repiten.
- Sin `git push|commit|add|tag` en ningún `run`, sin escritura a `data/` (el arnés parchea `store.DATA_DIR` a un temporal: `probe_f4.py:249`). `contents: read` en `head_e`, `prueba` y `probe` (VC169-09 para `plan`).
- Procedencia: `plan` exige `GITHUB_REF == refs/tags/$TAG`; `prueba` y `probe` hacen `git fetch` del tag y `test "$(git rev-parse TAG^{commit})" = "$(git rev-parse HEAD)"`, más el blob de `evaluar_d25.py` y `manifiesto --comprobar`. No es literalmente "cada job": `plan` y `head_e` no comprueban el commit (lo segundo es intencional, es el modo sin tag). El input `tag` pasa por variables de entorno, nunca interpolado en el script.
- Concurrency: grupo fijo `probe-s168-modd-f4`, `cancel-in-progress: false`. GitHub deja un solo pendiente por grupo, así que un tercer despacho desplaza al segundo; falla cerrado porque `externos_f4.procedencia` exige las partes 0 a 23 una vez cada una.
- Timeouts: partes de 219 a 245 pasadas (`a7_partes.py`); 245 por 9 s son 37 min, 110 min si fuera 3 veces peor; `probe` 240 min, `prueba` 45 min, `head_e` 30 min.
- Entorno de runner: sin rutas `D:` en los archivos que corre; el escaneo de f-strings solo-3.12 (`a7_py311.py`) da 0 en 19 archivos (control positivo marcado); los paquetes de terceros cargados (`a7_deps.py`) están cubiertos por el `pip install` del yml o son dependencias de `earthaccess`.
- Guardas del repo contra el yml nuevo en mi árbol (`a7_pytest_guards_workflow_salida.txt`): 35 passed, 3 skipped (g5 `on` entre comillas, g4 pusher, expresiones, timeout, token vacío). Mis 4 fallas en `test_guard_declarado_vs_efectivo_s131.py` (g1, g2, g6, g8b) son archivos que mi árbol reducido no trae (`CLAUDE.md`, `docs/`); no tocan el yml. En `origin/main` (ref local, 23:00 UTC) hay tests nuevos que leen workflows; el único que enumera el resto (`tests/test_sombra_codigo_mirova_s167.py:182`) exige que el grupo de concurrency de la sombra no coincida con otro, y el de este yml es distinto.

**Pregunta concreta: ¿mergear antes del tag introduce algún riesgo?** No hallé ninguno. (1) Ningún trigger corre solo. (2) Permisos de escritura: no. (3) Secreto distinto: no. (4) Algo que el tag no controle: la versión del yml que corre es la del `--ref` (el tag), no la de `main`; el yml en `main` solo hace que el workflow exista para despacharlo (limitación documentada en CLAUDE.md del proyecto, "workflow_dispatch limitation (S73)"). Despachado fuera de un tag, `plan` falla cerrado salvo en el modo `head_e` (VC169-08).

**¿Depende de archivos que todavía van a cambiar?** El yml no incrusta el §13 ni hashes; sí llama a `manifiesto_candado_f4.py --comprobar`, `probar_probe_f4.py`, `probar_evaluar_f4.py`, `evaluar_vacio.py`, `probe_f4.py` y `head_e.py`, todos del tag. Su propio sha256 está en el manifiesto: el PR de merge debe llevar el archivo byte-idéntico (sha256 LF `50d9fc92ac5389dc28098b9423b24e8d1eb3cfc25d3aee3e4117670431cf13e9`), y cualquier retoque (VC169-08 o 09) hay que hacerlo ANTES del merge o regenerar el manifiesto. Además `3db87f50d` nace de un `main` más viejo: en `origin/main` hay `pipeline/profiles/sombra_codigo_mirova.yaml`, `scripts/revisar_sombra.py`, `scripts/ventana_sombra.py` nuevos y `scripts/auto_audit_weekly.py` distinto. Si el tag se corta sobre otro commit que 3db87f50d más lo regenerado, hay que re-verificar el manifiesto.

## 6. SEGUIMIENTOS (fuera de mi eje)

- S-1: `probar_evaluar_f4_salida.txt` perdió su primera línea `[VRP profile=...]` entre el sello y 3db87f50d (diff leído); sin consecuencia, pero la salida ya no registra con qué perfil corrió. CONFIRMADO, gravedad 1.
- S-2: `poblacion_f4_salida.txt` y `reetiquetado_f4_salida.txt` registran rutas de un worktree (`...\.claude\worktrees\elated-bell-62d203\...`); no se pueden reproducir tal cual. SOSPECHA, gravedad 1.
- S-3: `carga_partes` en `poblacion_f4.json` (por ejemplo 2.496) no es el número de pasadas por parte (219 a 245); no sé qué pesa. No lo perseguí. SOSPECHA, gravedad 1.
- S-4: el runner usa Python 3.11 y otro node que los 3.12 y node 22 con que se probó todo; la batería `prueba` corre en el runner (falla cerrado), pero la cabecera no registra la versión de node. SOSPECHA, gravedad 1.

## 7. VERIFICADO LIMPIO (comando y vara)

- Población y contrato (A1): `scripts/a1_poblacion.py`, `a1_cruces.py`, `a1_umbrales.py`, `a1_contrato_rerun_salida.txt`. Vara: el propio json (recuento independiente por clave) y los controles de cobertura e identidad del evaluador; no es vara contra la referencia real (eso es SIN DATO). También `diagnostico_canal` del json: 31 + 3 alertas OCR, ninguna sin alerta de la tabla en su pasada, así que un `lab_union` igual a `lab` en todas las filas es un cero medido y no un canal muerto (leído en `poblacion_f4_salida.txt`).
- HEAD de E (A2): `scripts/a2_head.py` contra `e_candidatas` de la población.
- sha256 de la referencia (A3a): contra la copia local de S165 y contra `loop/activo:experiments/_s165_regla_posicion/referencia_salida.txt`.
- Manifiesto (A6): `python -I experiments/_s166_modd_f4/manifiesto_candado_f4.py` en mi árbol y `scripts/a6_manifiesto_indep.py` (cálculo propio de sha256 LF).
- Identidad (A5): `probar_identidad_f4.py` re-corrido, 8 de 8.
- Evaluador (A8): batería real 66 de 66, vacío 66 de 66 rojos por aserción, sin cambios en `evaluar_f4.py` ni en el PREREGISTRO desde el sello.
- Workflow (A7): `scripts/a7_*.py` y pytest de guardas, contra el pre-registro §11 punto 5 ("sólo lectura con `"on":`, `EARTHDATA_TOKEN` y nada más (A71)") y contra A43 y A71 del proyecto.
- Humo: 25 pasadas distintas, todas en la población (24 de C, 1 de E, 23 con grilla), incluye Láscar 2026-04-25 07:35 y Chillán 2026-10-25 07:20 (`humo_f4.txt`); 24 gránulos.
- Partes: las 24 partes cubren los 1.285 gránulos una vez (`a7_partes.py`; 1.232 de C y 53 de E).

## 8. SIN DATO (y qué correr)

- Re-etiquetado (A3b, A3c) y etiquetas de la población: `python -I experiments/_s166_modd_f4/reetiquetado_f4.py --ref D:/vrp-trabajo/temporales/s168_candado/ref --ref-censo D:/vrp-trabajo/temporales/s168_candado/ref_censo` en el repo con `data/` (unos 90 s). Control de instrumento: debe dar 2 cambios con la referencia de hoy.
- Mutaciones del arnés (16 y 3 controles): `python -I experiments/_s166_modd_f4/probar_probe_f4.py` en un clon con `.git` y `data/` (unos 5 min).
- Mutaciones del evaluador con la batería de 66: VC169-04.
- Ensayo en seco: VC169-05.
- Humo y tandas en el runner: requieren el workflow en `main` y el tag.
- `head_e` con token y la bajada real con token en LAADS: sin red.

## 9. FUERA DE ALCANCE

Reglas §6 a §9 de `evaluar_f4.py` (selladas antes); `probe_f4.medir_pasada` (lectura parcial); K = producción (§8.1) sobre datos reales; los 518 records sin `codigo_sha` que declara el autor.

## 10. Veredictos globales

- **Candado: CANDADO VERIFICABLE PARA TAG CON CAMBIOS.** Antes del tag: (1) arreglar VC169-01 y regenerar `externos_referencia.json`; (2) correr las mutaciones del evaluador con la batería de 66 y poner el §13 al día (VC169-04), con un `git diff` contra el sello limitado a §13 y §13 ter (VC169-06); (3) correr el ensayo en seco (VC169-05); (4) idealmente sumar al manifiesto los archivos de VC169-02, guardar o exigir la clase real en la identidad (VC169-03) y registrar el sha de las grillas del censo (VC169-07). Con eso no veo nada que deje pasar una corrida distinta de la pre-registrada: procedencia, sha del tablero, blob de `evaluar_d25`, particiones y cobertura fallan cerrado.
- **Workflow: MERGEABLE YA** (solo ese archivo, byte-idéntico al de 3db87f50d; despachar siempre con `--ref <tag>` y el mismo `tag` en el input). Razones en la sección 5.
