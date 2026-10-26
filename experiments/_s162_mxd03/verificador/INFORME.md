# Verificador con contexto limpio: arnés, evaluador y vara del A/B de MxD03 sobre K (S162, tarea 1.30)

## 1. Encabezado

- **Fecha y hora del servidor** (header `Date` de `api.github.com`): inicio Sat, 24 Oct 2026 15:47:52 GMT; `caminos.md` sellado a las 15:49:57 GMT; cierre de mediciones 16:10:02 GMT.
- **Commit sobre el que medí**: worktree `D:\vrp-trabajo\s162-mxd03`, rama `s162-mxd03-codigo`, HEAD `87e91adf00d20e3535f12831877cf5ba1fa16682`. `origin/main` hoy = `80b819828f16e19ceacbd21dc7c4e474d46122b4` = merge-base con la rama (main no avanzó durante la sesión). Pre-registro sellado leído en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0\experiments\_s159\mxd03_prereg\PREREGISTRO_MXD03.md` (550 líneas, TEXTO).
- **Modelo y esfuerzo**: Claude Fable 5.1 (`claude-fable-5-1`); el nivel de esfuerzo lo fija la sesión que me lanzó y no me es visible.
- **CARPETA**: `D:\vrp-trabajo\s162-mxd03\experiments\_s162_mxd03\verificador\` (todo lo que escribí está ahí; no toqué nada fuera, no hice commit, push ni despacho; 0 llamadas a la API REST de GitHub, sólo el header `Date` de `curl -sI`).
- **Qué NO miré** (para que mi silencio no se lea como «todo bien»):
  - No corrí nada con HDF reales ni con `pyhdf` (Windows). Todo lo que pasa por `calculate_vrp` lo hice con la escena sintética de la 1.17 (`experiments/_s151_mxd03_etiquetas/probar_probe_mxd03.py`), que no tiene bow tie ni relleno de MxD03.
  - No probé `git fetch --depth 1 origin <sha>` ni `git worktree add` en un checkout superficial de Actions (VMX-08, SOSPECHA).
  - No re-derivé la regla de «lado del barrido» (`poblacion_mxd03.lado`) ni los deltas de «expuesta»: comprobé que reproducen los números del §5, no que la regla sea la de S151.
  - No verifiqué el núcleo importado de 1.17, 1.21 y 1.23 más allá de leer las funciones que el arnés llama (`procesar_brazo`, `publica`, `argumentos_*`, `resumir`, `rumbos`, `vector_nulo`, `trasladar_ne`, `medido_en`, `pico_por_indice`, `comparar`, `evaluar_sola.vara`, `estado_vara`, `resumir_noche`): la tarea las da por verificadas en 1.17, 1.21 y 1.23.
  - No abrí el informe del auditor (por diseño del encargo).

## 2. En una pantalla

1. **Las ocho afirmaciones se sostienen en lo esencial**: censo y vara se reproducen **byte a byte** desde copias mías; las 4 + 5 mutaciones y las 12 pruebas se re-corren igual; rama idéntica a `origin/main 80b819828` en `pipeline/ scripts/ volcanoes.yaml frontend/ data/mirova_equivalent/`; `k_en_sha.py` sobre `main` con escena sintética reproduce el brazo K exacto; los 12 `codigo_sha` son ancestros de `main` con firmas idénticas.
2. **Ningún defecto encontrado hace que el A/B dé CUMPLE SIN DAÑO cuando X daña**; los defectos son de instrumento (suite, controles débiles) y de operación.
3. **Dos cosas evitables antes de gastar las ~47 h**: (a) el gránulo del control 1 (`MYD021KM.A2026073.0705`) no está en el humo y cae en la **parte 16 (tanda 3)**: el humo siempre da INDECIDIBLE por geometría y el control 1 se estrena recién al final (VMX-01); (b) el evaluador **no deduplica `(vol, dt)`**: si los artefactos del humo y de la tanda 1 caen en la misma carpeta, P2 cuenta doble y ningún control lo acusa, medido -1 a -2 (VMX-02).
4. **La suite del evaluador no fija el camino real de la vara ni el núcleo de P2**: `regla_vara` y `pareadas` se prueban pero `main()` no las usa; 9 de 11 mutaciones mías pasan las 12 pruebas (VMX-03). El código es correcto por lectura; el hueco es del instrumento.
5. Veredicto: **LISTO CON CAMBIOS CHICOS** (VMX-01 y VMX-02 antes del despacho; el resto son seguimientos).

## 3. Veredicto por afirmación

| afirmación | veredicto | gravedad propia | evidencia de esta sesión |
|---|---|---|---|
| A1 censo | **CONFIRMADO** | 0 | `rerun_poblacion_mxd03_salida.txt`: 5.465 / 1.232 / 2.046 en 511 / etiquetas y pubK iguales al §5 / 222 / 4 protegidas expuestas; `poblacion.json` de mi copia **sha256 idéntico** al comprometido (`0a1ac868b48b6b65…`); referencia congelada con sha256 LF igual al MANIFIESTO; controles positivos del §8.7 OK; la copia difiere del original en 1 línea (`RAIZ`), diff impreso en la salida |
| A2 arnés | **CONFIRMADO** | 0 | `rerun_probar_probe_mxd03_ab_salida.txt`: caso base OK, 4 de 4 por aserción. Leído: `argumentos_calculate_vrp` y `argumentos_append_record` (probe_etiquetas.py l. 52-81) = `scripts/run_pipeline.py` l. 253-273 argumento por argumento; `rumbos` (probe_mxd03_ab.py l. 91-96) es la de 1.23 (probe_sola.py l. 109-114) con la sal `s159-mxd03-r`; R sólo con `fila_pob["r_nulos"]` (z ≤ 35 del record de K); X_fondo/X_det/XF_id/XD_id como el §3; `decide()` = §8.4; retención sólo si decide y difiere. `verif_deps_bloqueadas_salida.txt`: el arnés corre sin pandas, pyproj, matplotlib; `requests` lo trae `earthaccess` (dependencia dura, `pip show`) |
| A3 control 4 | **CONFIRMADO EN PARTE** | 2 | Scripts implementan la clasificación del §8.4 (`recorrer_en_sha.py` l. 72-73). Probé lo que se puede sin HDF: `verif_k_en_sha_sintetico_salida.txt` LIMPIO (parche `store.DATA_DIR` redirige, 1 línea JSON, 0 argumentos omitidos, record idéntico al brazo K del arnés, `data/` intacto). `shas_viejos_compat_salida.txt`: los 12 `codigo_sha` existen, son ancestros de `origin/main`, y en los 12 `store.py` tiene `DATA_DIR` global usado en `append_record`, `run_pipeline.load_volcanoes`, `VOLCANIC_FEATURES` y `get_detection_anchor` existen, y las firmas de `calculate_vrp` y `append_record` son idénticas a las de hoy. **Sin probar**: `git fetch` + `worktree add` en el runner (VMX-08). El hueco pesa poco en el veredicto (una falla da INDECIDIBLE, nunca CUMPLE) y mucho en costo (los HDF retenidos se borran al terminar `recorrer_en_sha.py`, l. 82-83) |
| A4 evaluador | **CONFIRMADO EN PARTE** | 3 | Reglas §6 y controles §8 leídos uno a uno contra el código (sección 5); tabla §10 = `veredicto()` l. 346-363. Re-corridas: 12 de 12, 5 de 5, 0 de 12 contra el vacío, punta a punta OK. **Pero**: VMX-02 (duplicados), VMX-03 (suite no fija el camino real), VMX-04 (control «union» tautológico, sin re-etiquetado), VMX-05 (apartamientos menores de §6) |
| A5 vara | **CONFIRMADO EN PARTE** | 1 | `rerun_vara_construir_salida.txt`: 92 / 83 / 65 y `vara_viirs_mxd03.json` **sha256 idéntico** al comprometido. «Sin cambiar el instrumento»: importa `resumir_noche`, `VENTANA_H`, `VIIRS375` y `evaluar_sola.vara`, pero el **bucle de selección** (publicada por node, no Test 1, 6 h, estricta = `pos` con regla SN, diurnas fuera) es una **copia adaptada** de `construir_vara_viirs.main` (l. 87-160), no un import: misma lógica por lectura, pero A102 aplica. `verif_vara_evaluar_sintetico_salida.txt`: la cadena `--evaluar` → `evaluar_sola.vara` → `vara_desde_estado` da DETIENE (INTERP MAS CERCA, n = 65, Terra 31 / Aqua 34), NO DETIENE (MXD03 MAS CERCA) y SIN VARA → NO DETIENE |
| A6 workflow | **CONFIRMADO** | 1 | `yaml.safe_load`: claves `['name','on','concurrency','jobs']`, `on.push.branches` = las 4 ramas exactas, sin patrones; token: paso «Token presente» antes del checkout con `exit 1` si vacío, ningún `EARTHDATA_USERNAME/PASSWORD` en el yml; `ubuntu-24.04` en los 2 jobs; `max-parallel: 8` y 8 partes por rama; `timeout-minutes: 300`; deps = `nrt.yml` l. 140-143 (misma lista, Python 3.11). Costo con `poblacion.json`: 51 a 52 gránulos y 2.386 a 2.389 corridas por parte → 52 × 32,8 s + 2.389 × 2,15 s ≈ 114 min ≈ 1,9 h; × 1,3 = 2,5 h < 5 h. Notas: VMX-01, VMX-09 |
| A7 rama = main | **CONFIRMADO** | 0 | `git diff --stat 80b819828f16 HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` vacío; `git status` sólo `?? experiments/_s162_mxd03/verificador/`; sparse-checkout incluye `data/mirova_equivalent/` (45 JSON en disco), `pipeline/` y `scripts/` materializados; la rama agrega sólo `.github/workflows/probe-s162-mxd03.yml` y `experiments/_s162_mxd03/` (20 archivos) |
| A8 adenda y apartamientos | **CONFIRMADO EN PARTE** | 2 | Los 5 puntos de la adenda (D35, tag sin merge, censo re-medido, construcción, despacho por push) no tocan pregunta, brazos, métricas ni §6 (leído, l. 21-38). Apartamientos encontrados entre el texto sellado y el código: lista en la sección 6; ninguno cambia P1 ni la regla de P2; los de más peso son VMX-04 (el evaluador no re-etiqueta) y la exclusión de una `bajo1` partida de P2 (VMX-05) |

## 4. Hallazgos (lo peor primero)

### VMX-01
- **TÍTULO**: El humo no ejercita el control 1 de geometría; su gránulo cae en la última tanda.
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\s162-mxd03\.github\workflows\probe-s162-mxd03.yml:31` (`solo=` del humo: 3 gránulos sin `MYD021KM.A2026073.0705`); `D:\vrp-trabajo\s162-mxd03\experiments\_s162_mxd03\probe_mxd03_ab.py:84` y `:312-315` (control sólo en ese gránulo y Láscar); `evaluar_mxd03.py:309-315` (`control_geometria` da INDECIDIBLE sin él); `poblacion.json`: el gránulo está en la **parte 16** (tanda 3).
- **QUÉ PASA**: el control positivo del instrumento de geometría (2,581 ± 0,05 km hacia el sensor en Láscar, S151) es lo único que ata «MxD03 se leyó bien» a un número medido; sin él el evaluador declara INDECIDIBLE todo (l. 349-350). El humo (3 gránulos) no lo contiene, así que **el humo nunca puede dar un veredicto distinto de INDECIDIBLE** y no comprueba el control 1. Si el control falla por un detalle evitable (signo, tolerancia, cambio de `_leer_geo`), se sabe recién al cerrar la tanda 3, tras ~47 h.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (A/B de sólo lectura).
- **CÓMO REPRODUCIRLO**: `python -c "import json;p=json.load(open('experiments/_s162_mxd03/poblacion.json'));print([i for i,x in enumerate(p['partes']) if 'MYD021KM.A2026073.0705' in x])"` → `[16]`. En el humo: correr `evaluar_mxd03.py --art <artefacto humo>` → `control geometria INDECIDIBLE` (es lo que la prueba de punta a punta ya exige, `probar_punta_a_punta.py` l. 45-47).
- **CONFIANZA**: CONFIRMADO (leído y contado).
- **GRAVEDAD**: 3 (no tuerce ninguna alerta; es el error evitable que puede dejar ~47 h en INDECIDIBLE). Arreglo trivial de operación: agregar `MYD021KM.A2026073.0705` a `solo=` del humo (el gránulo trae Láscar `bajo1` expuesta con z 44,59: también ejercita la retención).

### VMX-02
- **TÍTULO**: El evaluador no deduplica `(vol, dt)`: artefactos del humo y de la parte 0 juntos duplican filas y P2 cuenta doble.
- **SCRIPT:SALIDA**: `verificador\verif_duplicados_artefactos.py` : `verif_duplicados_artefactos_salida.txt` (una copia: `delta_x=-1 n=2`; dos copias en subcarpetas distintas: `delta_x=-2 n=4`, cobertura OK, union OK). Código: `evaluar_mxd03.py:371-379` (`cargar`, glob recursivo `**/ab_parte*.jsonl`, sin dedupe); `:402-411` (la unión hace `base.update(pf)` por fila, no por clave).
- **QUÉ PASA**: el humo escribe `ab_parte00.jsonl` (`probe_mxd03_ab.py:263`, rotulado con `--parte 0`) y la parte 0 de la tanda 1 también. Descargados a una misma carpeta `--art`, las filas de los 3 gránulos del humo entran dos veces: S(X), S(K) y cada S(Rk) se inflan en esas pasadas, el denominador `n` también, y ninguno de los controles (cobertura es un conjunto, union compara con la población, procedencia exige un solo commit, que se cumple) lo acusa.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s162_mxd03 && PYTHONIOENCODING=utf-8 python verificador/verif_duplicados_artefactos.py`.
- **CONFIANZA**: CONFIRMADO (medido).
- **GRAVEDAD**: 3 (puede mover P2 de EMPATE a PIERDE o GANA, o P1 contar una pérdida dos veces, por un error de carpeta). Evitable: un `assert` de unicidad de `(vol, dt)` en `cargar` o no mezclar el artefacto del humo con los de las tandas.

### VMX-03
- **TÍTULO**: La suite prueba funciones que `main()` no usa (`regla_vara`, `pareadas`) y deja sin fijar el camino real de la vara y el núcleo de P2.
- **SCRIPT:SALIDA**: `verificador\verif_mutaciones_propias_evaluador.py` : `verif_mutaciones_propias_evaluador_salida.txt`: **2 de 11 mutaciones propias atrapadas** por las 12 pruebas. No atrapadas: `vara_desde_estado` siempre NO DETIENE (es la función que `main()` usa, `evaluar_mxd03.py:421`; `regla_vara`, l. 240-246, sólo la usa la prueba 10); vara `None` → CUMPLE; `control_r_modulo`, `control_cableado`, `control_geometria` siempre OK; `p1b` siempre `[]`; **ruido = máximo de 20 en vez del segundo mayor** (la prueba 2 usa `dr=[-1,1]*10`, donde el máximo y el segundo coinciden); **saldo sin las bajo 1 MW no publicadas** (`con_saldo`, `probar_evaluar_mxd03.py:62-69`, sólo enciende negativos); veredicto que ignora los controles externos. `pareadas` (l. 65-68) no tiene llamador fuera de la prueba 12: el evaluador no parea nada, toma `lab` de `poblacion.json`; la mutación «pareo a 300 s» se atrapa por esa función muerta, mientras que el efecto real de `TOL_S` (l. 392-393, `pob["tol_s"] != TOL_S` → INDECIDIBLE) no tiene prueba.
- **QUÉ PASA**: el código leído es correcto en todos esos puntos (ruido l. 117-119, saldo l. 112-114, `vara_desde_estado` l. 249-254), pero una edición futura los rompe sin que la suite se entere. La prueba de punta a punta sí atraparía la de geometría (exige INDECIDIBLE sin S151).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s162_mxd03 && PYTHONIOENCODING=utf-8 python verificador/verif_mutaciones_propias_evaluador.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 hoy (código correcto), 4 si alguien edita el evaluador antes del veredicto sin agregar pruebas.

### VMX-04
- **TÍTULO**: El control «union» compara la población consigo misma y el evaluador no re-etiqueta con `banco_paridad.etiquetar` como pide el §8.
- **ARCHIVO:LÍNEA**: `probe_mxd03_ab.py:186-188` (el arnés copia `lab`, `z`, `tramo`, `lado`, `r_nulos` de `fila_pob`, que viene de `poblacion.json`); `evaluar_mxd03.py:405-411` (compara esos campos con `poblacion.json` otra vez); PREREGISTRO §8, «Reglas propias: … y el etiquetado con `banco_paridad.etiquetar` a 120 s (importado, no copiado)» (TEXTO, l. 414-415); docstring de `poblacion_mxd03.py:8-10` que dice que «el evaluador vuelve a etiquetar con la misma referencia congelada».
- **QUÉ PASA**: la etiqueta que decide P1 y P2 sale de `poblacion.json` en los dos lados; el control sólo puede fallar si el archivo cambia entre el despacho y la evaluación (eso sí lo cubre, y la cabecera guarda `poblacion_checkout`). Lo que no hay es la segunda medición independiente que el §8 escribió: el evaluador no abre la referencia congelada salvo para comparar sha256 si se le pasa `--ref`. Si `poblacion.json` se regenerara con otra referencia o ventana, el evaluador no se enteraría más que por `tol_s`.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n "etiquetar\|indexar_referencia\|cargar_referencia" experiments/_s162_mxd03/evaluar_mxd03.py` → 0 líneas.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (apartamiento del texto sellado; el riesgo real es bajo porque la población se reproduce byte a byte y está en el commit del tag).

### VMX-05
- **TÍTULO**: Cuatro apartamientos menores del §6 en el evaluador y el arnés.
- **ARCHIVO:LÍNEA**: (a) `evaluar_mxd03.py:99-104` `_invisible` excluye de P2 toda partida con hermana `sin_info`, también una **bajo1**: medido en `poblacion.json`, 1 record (Villarrica 2026-09-25 08:05, z 5,78, K no publica), que el §8 prueba 6 no nombra (habla de un negativo); (b) `:206-210` P6 lista los cambios en las partidas **invisibles** (109 de 222: 106 `neg_limpio`, 2 `sin_info`, 1 `bajo1`) y en `sin_info`/`far_ref`, no en «las 222 mitades» del §6; las 6 `neg_limpio` partidas con hermana no `sin_info` van a P2 y, si cambian, no salen en P6; (c) §6 «si su signo difiere del de P2, la primera línea lo dice»: `main` imprime el estado de P2 sin Cordón Caulle (l. 432-433) pero no compara signos ni lo marca; (d) §6 «"Publica" es el predicado de `frontend/index.html` ejecutado con node, con su sha256 impreso»: ni el arnés ni el evaluador imprimen el sha256 del html (`grep sha256` sólo da la referencia); lo que lo fija es el commit de `procedencia`.
- **QUÉ PASA**: lecturas razonables del texto, pero son apartamientos y van listados. (a) resta un record a P2 que MIROVA sí alertó (no es «invisible» para MIROVA).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: conteo en la salida de la celda «partidas invisibles por etiqueta» de esta sesión (ver `INFORME.md` §7, comando incluido).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

### VMX-06
- **TÍTULO**: Módulo homónimo `evaluar_mxd03.py` en `experiments/_s151_mxd03_etiquetas/`, y `vara_mxd03.py` pone esa carpeta antes en `sys.path`.
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\s162-mxd03\experiments\_s151_mxd03_etiquetas\evaluar_mxd03.py` (evaluador de la 1.17); `vara_mxd03.py:40-42` (inserta `_s151_mxd03_etiquetas` en `sys.path[0]`); `probar_probe_mxd03_ab.py:35-36` (orden final `[RAIZ, etiquetas, AQUI]`: etiquetas antes que la carpeta del A/B).
- **QUÉ PASA**: en los caminos reales no se pisa (cada script corre con su carpeta en `sys.path[0]` o importa por ruta). Pero cualquier script que importe `vara_mxd03` o `probar_probe_mxd03_ab` y después `import evaluar_mxd03` toma el de la 1.17 sin error: me pasó en `verif_vara_evaluar_sintetico.py` (primer intento, `AttributeError: module 'evaluar_mxd03' has no attribute 'vara_desde_estado'`), y lo resolví importando por ruta. Es el patrón A89: cero error, módulo equivocado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `cd experiments/_s162_mxd03 && python -c "import sys;sys.path.insert(0,'.');import vara_mxd03,evaluar_mxd03;print(evaluar_mxd03.__file__)"` → la ruta de `_s151_mxd03_etiquetas`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

### VMX-07
- **TÍTULO**: «INTERP MAS CERCA SIN CONTROL DE SESGO» se lee como NO DETIENE sin marca propia; SESGO POR SATÉLITE sólo aparece si el efecto global excluye el cero.
- **ARCHIVO:LÍNEA**: `evaluar_mxd03.py:249-254` (`vara_desde_estado`: sólo la cadena exacta `INTERP MAS CERCA` detiene); `experiments/_s151_mxd03_sola_123/evaluar_sola.py:227-245` (`estado_vara`: con menos de 2 satélites de 5 o más gránulos agrega « SIN CONTROL DE SESGO»; SESGO sólo si `(lo > 0 or hi < 0) and fuera_del_nulo`).
- **QUÉ PASA**: hoy no aplica (Terra 31 / Aqua 34 bajo 35°, los dos sobre el mínimo de 5), pero con otra población una vara que dijera INTERP MAS CERCA con un solo satélite pasaría como NO DETIENE y el veredicto podría ser CUMPLE SIN DAÑO; el estado crudo queda en `vara_cruda.estado_evaluar_sola`, así que se ve si alguien lo lee. Mi caso C (`verif_vara_evaluar_sintetico_salida.txt`: Terra con C cerca y Aqua con M cerca) dio INDECIDIBLE, no SESGO: es la definición de la 1.23, no un defecto del pegamento.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `verif_vara_evaluar_sintetico.py`, caso C.
- **CONFIANZA**: CONFIRMADO (leído y medido).
- **GRAVEDAD**: 1.

### VMX-08
- **TÍTULO**: El control 4 depende de `git fetch --depth 1 origin <sha>` y `git worktree add` dentro del checkout superficial del runner, sin prueba.
- **ARCHIVO:LÍNEA**: `recorrer_en_sha.py:52-55`; `probe-s162-mxd03.yml:55` (`actions/checkout@v5` sin `fetch-depth`, o sea superficial, con `permissions: contents: read`).
- **QUÉ PASA**: si el fetch por sha o el worktree fallan en el runner, cada record retenido queda en `estado: "error"` (l. 74-77), `control_arnes` lo clasifica `no_reproduce` → INDECIDIBLE para todo el A/B (l. 269, 279), y los HDF retenidos se borran al terminar (l. 82-83): rehacer el control 4 exige volver a bajar esos gránulos. Es fail-safe (nunca CUMPLE), pero es justo el «error evitable ahora» que la tarea pide buscar. Hay 135 records que deciden (50 protegidas, 42 bajo1, 42 negativos publicados, 1 `sin_info` expuesta), escritos por 3 shas (`3695f6758` 114, `34cea39e4` 20, `57d18ad78` 1): el fetch se hará como máximo 3 veces por parte.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: sólo en el runner; el humo lo ejercita si alguno de sus records difiere de `data/` (Láscar 03-27 y Chillán 10-10 son de `3695f6758`, el sha de la mayoría).
- **CONFIANZA**: SOSPECHA (no probado aquí; en GitHub el fetch por sha alcanzable suele funcionar, pero no lo medí).
- **GRAVEDAD**: 2.

### VMX-09
- **TÍTULO**: El workflow no comprueba que la rama de disparo esté en el tag ni que `pipeline/` sea el de `main` congelado; `procedencia` sólo exige un commit único.
- **ARCHIVO:LÍNEA**: `probe-s162-mxd03.yml:74` (sólo imprime `git rev-parse HEAD`); `evaluar_mxd03.py:399-401` (`len(commits) == 1`); la cabecera guarda `poblacion_checkout` pero nadie compara `pipeline/` del commit del job contra él.
- **QUÉ PASA**: la adenda (punto 2) fija que el brazo K es «producción del `main` congelado» porque la rama sale de él sin tocar `pipeline/`. Eso lo garantiza hoy el `git diff` vacío que medí (A7), no el workflow. Si una rama de disparo se empujara desde otro commit (por ejemplo tras un rebase sobre un `main` nuevo), K dejaría de ser la producción del censo y el evaluador no lo vería (control 4 lo atraparía sólo donde difiera de `data/`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: n/a (es una ausencia de control). Barato: un paso en el yml con `git diff --quiet <poblacion.checkout> HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent || exit 1` leyendo el checkout de `poblacion.json`.
- **CONFIANZA**: CONFIRMADO (ausencia leída).
- **GRAVEDAD**: 1 (riesgo de operación, no de código).

## 5. Lectura regla por regla del §6, §8 y §10 contra el código (A4)

| regla sellada | código | estado |
|---|---|---|
| P1 veto: protegida que K publica y X no; fragilidad en R informa | `p1` l. 76-84 | igual |
| P1b: K ≥ 1 MW y X < 1 MW en protegidas que ambos publican | `p1b` l. 87-95 | igual |
| P2: S = bajo1 sin publicar + neg_limpio publicados; Δ_X, Δ_Rk; ruido = segundo mayor de 20 abs; GANA/PIERDE/EMPATE; sólo z ≤ 35 | `saldo` l. 112-114, `ruido_p2` l. 117-119, `regla_p2` l. 122-126, `filas_p2` l. 107-109 | igual; `rango_x` = comparador |
| P2 INDECIDIBLE si R no mueve un cúmulo publicado > 0,5 km en el censo ≤ 35 | `r_vivo` l. 137-147 sobre todas las filas con `r_nulos` | igual |
| P2 sobre 35° y sin Cordón Caulle informan | `p2_informe` l. 168-175; `CC = "PuyehueCordonCaulle"` coincide con `poblacion.json` | igual salvo VMX-05 (c) |
| P4 0,01 km y cambios de `distance_class`; protegida → A61 | `p4` l. 179-192 | igual; no entra al veredicto («condiciona») |
| P5 atribución | `p5` l. 195-203 | igual |
| P6 | `p6` l. 206-210 | subconjunto (VMX-05 b) |
| M sólo informa; d, ĝ, intervalo por bloques; d′ sin intervalo | `m_informa` l. 214-236 con `pesos_bloque` y `regla_m` de `evaluar_d25.py` (existen, l. 120 y 152) | igual, d′ declarado |
| Control 1 | `control_geometria` l. 309-315; valor S151 leído en `experiments/_s151_probe_mod03/resultado/probe_mod03.json`: `obs_hacia_sensor_km = 2.581` (positivo) | igual |
| Control 2 | `control_r_modulo` l. 296-306 + `r_vivo` | igual |
| Control 3 | `control_k2` l. 258-259 | igual |
| Control 4 | `control_arnes` l. 262-281; `MIN_SHA_ESTRATO = 50` lectura propia declarada | igual (umbral de estrato declarado) |
| Control 5 | `control_cobertura` l. 284-293 | igual |
| Control 6 | `--ref` opcional l. 394-397 | parcial (sólo si se pasa `--ref`) |
| Control 7 | en `poblacion_mxd03.py` l. 60-62, 198-203 | igual (3 de los 4: el de febrero está fuera de la ventana) |
| Control 8 | `control_cableado` l. 318-329 | igual |
| Tabla §10 | `veredicto` l. 346-363 | igual; agrega PENDIENTE DE LA VARA cuando falta (más estricto) |

## 6. Apartamientos entre el texto sellado y la implementación (A8)

| # | texto sellado | código | peso |
|---|---|---|---|
| 1 | §8: el evaluador etiqueta con `banco_paridad.etiquetar` a 120 s | toma `lab` de `poblacion.json` (VMX-04) | medio-bajo |
| 2 | §8 prueba 6: una mitad partida con hermana `sin_info` (negativo) va a P6 | `_invisible` también saca una `bajo1` (1 record) | bajo |
| 3 | §6 P6: cambios en las 222 mitades partidas | sólo las 109 invisibles | bajo |
| 4 | §6: «la primera línea lo dice» si el signo de P2 sin CC difiere | no se compara el signo | bajo |
| 5 | §6: sha256 del html impreso | no se imprime; lo fija el commit | bajo |
| 6 | §8 control 4: 98 % «estratificado por `codigo_sha`» | estratos con 50 records o más (declarado en l. 52) | bajo, declarado |
| 7 | §8: d′ con `comparar_con_ganancia` si está en `main` | no está en `main`; d′ puntual sin intervalo (previsto por el §8) | nulo |
| 8 | §9: tag `s159-mxd03-codigo`, despacho con `gh workflow run` | adenda: tag `s162-mxd03-codigo`, push a rama | nulo (adenda) |
| 9 | §9: no hay humo | el yml agrega una rama humo de 3 gránulos | nulo (no toca reglas); ver VMX-01 |
| 10 | §10 CUMPLE requiere «la vara VIIRS no detiene» | sin vara → PENDIENTE DE LA VARA | más estricto, nulo |
| 11 | §3: «ángulos, bandas y perfil iguales» | el lector sólo reemplaza `lat`/`lon` (`probe_mxd03_ab.py:154-159`) | igual |

La adenda (5 puntos) no cambia pregunta, brazos, métricas ni §6: confirmado por lectura de l. 21-38 contra §1, §3 y §6.

## 7. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- **Censo**: `python -I experiments/_s162_mxd03/verificador/rerun_poblacion_mxd03_copia.py --sin-bajar --ref D:/vrp-trabajo/temporales/s162_mxd03/ref` → `poblacion.json` sha256 idéntico al comprometido. Vara: los números del §5 del texto sellado y el `MANIFIESTO.json`; controles positivos del §8.7 en verde y exigidos (salida 2 si fallan). Copia = original salvo `RAIZ` (diff en `rerun_poblacion_mxd03_salida.txt`).
- **Referencia congelada**: `tr -d '\r' < f | sha256sum` sobre `D:/vrp-trabajo/temporales/s162_mxd03/ref/*` = `MANIFIESTO.json` (8ec5d918… y fd7a7098…). Vara: el manifiesto; no bajé los commits de Mirova-v1 (0 llamadas a la API).
- **Arnés sintético**: `python experiments/_s162_mxd03/probar_probe_mxd03_ab.py` → caso base OK, 4 de 4 por aserción (`rerun_probar_probe_mxd03_ab_salida.txt`). Vara: la escena de la 1.17 por el `calculate_vrp` real de este checkout.
- **Dependencias del runner**: `verif_deps_bloqueadas.py` → con pandas, pyproj, matplotlib y requests bloqueados, el caso base del arnés corre y los módulos del runner importan; los 2 «FALLA» (`run_pipeline`, `pipeline.fetch`) son por `requests`, que es dependencia dura de `earthaccess` (`pip show earthaccess` → `Requires: … requests …`), así que en el runner está. Vara: la lista `pip install` del yml, igual a `nrt.yml` l. 140-143.
- **Evaluador**: `python probar_evaluar_mxd03.py --mutaciones` → 12 de 12 y 5 de 5; `--modulo evaluar_vacio` → 0 de 12; `probar_punta_a_punta.py` → OK (salidas `rerun_*`). Vara: las 12 pruebas del §8 del texto sellado, leídas una a una contra lo que afirman.
- **k_en_sha sobre main**: `verif_k_en_sha_sintetico.py` LIMPIO. Vara: el brazo K del arnés sobre la misma escena (`registros_iguales`) y `data/` intacto por sha256.
- **Compatibilidad de los 12 `codigo_sha`**: `shas_viejos_compat_salida.txt`. Vara: `git show <sha>:archivo` (contenido, no identificador).
- **Vara VIIRS**: `rerun_vara_mxd03_copia.py --construir` → json idéntico; `verif_vara_evaluar_sintetico.py` → DETIENE alcanzable, NO DETIENE y SIN VARA correctos. Vara: `evaluar_sola.estado_vara` leído.
- **Workflow**: `yaml.safe_load` (claves string, A43), ramas exactas, token-only, `ubuntu-24.04`, 300 min, 8 × 3. Vara: el §9 y la adenda.
- **A7**: `git diff --stat 80b819828f16 HEAD -- pipeline scripts volcanoes.yaml frontend data/mirova_equivalent` vacío; `git fetch origin --prune` previo; `git merge-base HEAD origin/main` = 80b819828.
- **Partes balanceadas**: 51 a 52 gránulos y 2.386 a 2.389 corridas por parte (24 partes; `poblacion.json`).
- **Humo**: los 3 gránulos existen en la población: Láscar 03-27 `protegida` z 39,85 (sin R), Chillán 10-10 `protegida` z 35,06 (**sin R**: 35,06 > 35), Cordón Caulle 10-11 `neg_limpio` publicado z 16,05 (con R) y Chaitén z 22,52 (con R).

## 8. SEGUIMIENTOS (fuera de mi eje, reproducibles)

- **S-1**: `concurrency.group: probe-s162-mxd03` con `cancel-in-progress: false`: GitHub mantiene **un solo run pendiente por grupo**; si se empujan t2 y t3 mientras corre t1, t2 se pierde (misma lección que `nrt.yml`, CLAUDE.md «Concurrency»). El encabezado del yml (l. 7) lo dice; conviene que quien despache lo tenga delante. Confianza CONFIRMADO por lectura del yml; gravedad 2 (operación).
- **S-2**: `probar_probe_mxd03_ab.py:35-36` deja `_s151_mxd03_etiquetas` antes que la carpeta del A/B en `sys.path` (hoy inocuo; ver VMX-06).
- **S-3**: si `recorrer_en_sha.py` cae a mitad (excepción fuera del `try` por record), los HDF retenidos no se borran y tampoco se suben (el artefacto sólo toma `*.jsonl *.log *.txt`): quedan en el runner y se pierden. `probe-s162-mxd03.yml:91-94`. Gravedad 1.
- **S-4**: `evaluar_mxd03.py:394-397` calcula `_sha256_lf` dos veces por archivo (8 MB): costo nulo, sólo estilo.

## 9. SIN DATO

- El comportamiento del arnés con **HDF reales** (bow tie, relleno -999 de MxD03 → `n_fill_mxd03`, `desplazamiento_crater` con `nanargmin`): sin pyhdf no se puede medir aquí. Lo cubrirá el humo.
- `git fetch`/`worktree` en el runner (VMX-08).
- El tiempo real por parte: sólo estimado con las cotas del §9 (32,8 s por gránulo, 2,15 s por corrida) y los conteos de `poblacion.json`.
- La regla de «lado» (`poblacion_mxd03.lado`) y los `DELTA` de «expuesta»: reproducen el §5, no verifiqué su origen (S151, M H3).

## 10. FUERA DE ALCANCE

- Si X es o no fiel a MIROVA (la pregunta del A/B), la paridad de posición, D17/D18/D25.
- El núcleo de 1.17, 1.21, 1.23 y S151 más allá de lo que el arnés llama.
- El informe del auditor (no lo abrí).

## 11. Instrumentos de esta carpeta

| archivo | qué es |
|---|---|
| `caminos.md` | caminos por los que cada afirmación podía estar mal, sellado con sha256 `d2cbfe92…` a las 15:49:57 GMT antes de abrir nada |
| `rerun_poblacion_mxd03_copia.py` + `rerun_poblacion_mxd03_salida.txt` + `poblacion.json` + `MANIFIESTO.json` | censo re-corrido desde copia (1 línea distinta) |
| `rerun_vara_mxd03_copia.py` + `rerun_vara_construir_salida.txt` + `vara_viirs_mxd03.json` | vara reconstruida desde copia |
| `rerun_probar_probe_mxd03_ab_salida.txt`, `rerun_probar_evaluar_mxd03_salida.txt`, `rerun_probar_evaluar_contra_vacio_salida.txt`, `rerun_probar_punta_a_punta_salida.txt` | las pruebas del auditor re-corridas |
| `verif_deps_bloqueadas.py` + salida | dependencias como en el runner |
| `verif_k_en_sha_sintetico.py` + salida | `k_en_sha.py` real sobre `main` con escena sintética |
| `verif_mutaciones_propias_evaluador.py` + salida | 11 mutaciones propias contra las 12 pruebas |
| `verif_duplicados_artefactos.py` + salida | VMX-02 |
| `verif_vara_evaluar_sintetico.py` + salida | cadena de la vara en 4 casos |
| `shas_viejos_compat_salida.txt` | los 12 `codigo_sha` contra lo que `k_en_sha.py` necesita |
| `hallazgos.csv` | una fila por hallazgo (módulo `csv`) |
