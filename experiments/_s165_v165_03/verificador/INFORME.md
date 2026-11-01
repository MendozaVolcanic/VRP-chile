# Verificador con contexto limpio: PR #922 (S165 V165-03, la pasada «sin dato» queda anotada)

Hora de inicio: 2026-10-27 21:58 UTC (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
Commit medido: `3926f6a93` (rama `claude/s165-v165-03-sin-dato`, PR #922, borrador). Base: tag anotado
`pre-s165-v165-03-sin-dato` = `97ef53aa5` (`git rev-parse <tag>^{commit}`).
Árboles propios: `D:\vrp-trabajo\temporales\s165_v16503_verificador\arbol` (3926f6a93, detached) y `arbol_tag`
(97ef53aa5, detached, con `tests/arnes_sin_dato_s165.py` copiado encima). Los dos se borran al terminar; quedan
esta carpeta, `CAMINOS.md` (sha256 en `CAMINOS.sha256`, escrito antes de leer el diff) y `salidas/`.
Disco al empezar: C: 24,1 GB libres, D: 7,4 GB; con los dos árboles, D: 5,0 GB. No se tocó `data/`, ni el
worktree del PR, ni NASA.

## Veredictos

| Afirmación | Veredicto | Ancla |
|---|---|---|
| A1 | CONFIRMADO | goldens regenerados desde el tag y desde HEAD, idénticos byte a byte (sha256 abajo) |
| A2 | CONFIRMADO | `salidas/head_geo_sin_dato.json` contra `salidas/tag_geo_sin_dato.json`, diff por escena |
| A3 | CONFIRMADO EN PARTE | código y corrida propia confirman; la razón declarada no cubre el A/B que decidiría encender el flag (V16503-01) |
| A4 | CONFIRMADO | `pipeline/process_modis.py:679-681` único sitio; matriz de 6 casos corrida; `return None` de l. 658, 720 y 766 no avisan |
| A5 | CONFIRMADO | único llamador de producción `scripts/run_pipeline.py:253` con el aviso en l. 263; VIIRS sin regla equivalente |
| A6 | CONFIRMADO | corrida propia: 10 de 10 atrapadas por aserción, controles viva y caída, árbol restaurado (`salidas/mutaciones_salida_verificador.txt`); huecos de cobertura nombrados en la sección |
| A7 | CONFIRMADO | suite propia 2723 passed, 29 skipped, 2 xfailed, 0 fallas, árbol quieto; CI run 40590920721 verde sobre 3926f6a93 |
| A8 | CONFIRMADO EN PARTE | las citas que el PR tocó son correctas por contenido; una cita que el cambio también corrió (A100, `process_modis.py:1172`) no se remapeó (V16503-03) y la fila v1.17 de la FICHA tiene 3 celdas en vez de 4 (V16503-02) |

## A1. Bit a bit con los flags apagados

Qué corrí (`salidas/correr_arnes.log`, `salidas/*.json`, sha256 en la misma carpeta):

- `arbol_tag` (97ef53aa5 + arnés copiado): `python tests/arnes_sin_dato_s165.py --salida tag_apagado.json` y lo
  mismo con `--flag ENABLE_MODIS_GEO_MXD03=True` y con los dos flags.
- `arbol` (3926f6a93): las mismas tres corridas, más `--flag ENABLE_MODIS_CRATER_SIN_DATO=True` solo.

Resultados (`cmp`):

| comparación | resultado |
|---|---|
| `tag_apagado.json` vs golden `tests/datos_s165_mxd03/sin_dato_corrida_apagado_antes.json` | IGUAL (sha256 `5b21b9f3…3f187b`) |
| `head_apagado.json` vs ese golden | IGUAL (mismo sha256) |
| `head_geo.json` vs `tag_geo.json` | IGUAL (`ce0ece26…73d9d2`) |
| `head_sin_dato_solo.json` vs `tag_apagado.json` | IGUAL |
| `tag_geo_sin_dato.json` vs golden `sin_dato_corrida_geo_sin_dato_antes.json` | IGUAL (`01694f60…9b8683`) |
| `head_geo_sin_dato.json` vs `tag_geo_sin_dato.json` | DIFIERE (es lo que A2 mide) |

Premisas comprobadas con git: `git diff 97ef53aa5 399891638 -- pipeline scripts` vacío (el commit del golden
tiene `pipeline/` y `scripts/` iguales al tag); el arnés y los dos goldens no cambian entre 399891638 y 3926f6a93
(`git diff --stat` vacío); `tests/arnes_mxd03_s165.py` y `tests/arnes_sintetico_s142.py` existen en el tag y son
iguales en 399891638. El merge 0df7b5257 trajo a `scripts/run_pipeline.py` sólo la impresión de VIIRS 375 con
`.get` (12 líneas) y no tocó `pipeline/process_modis.py` ni `pipeline/fetch.py`; el arnés sólo ejerce MODIS, así que
la igualdad bit a bit con #921 integrado vale para lo que el arnés corre.

Límite del «bit a bit» (camino A1.2 de CAMINOS.md): el golden serializa `codigo`, el JSON de cobertura y los records
que llegan a `store.append_record`; no serializa la salida por pantalla. La línea «Cobertura: completa» la cubren
aparte `test_el_resumen_nombra_el_caso` y mi grep de los logs (abajo, A2). Los flags se leen como nombres del módulo
`pipeline.process_modis` (importados de `pipeline.profile`, l. 104 a 108), que es lo que el arnés parchea: el golden
mide el flag que el código lee (camino A1.8 descartado). En producción los dos flags están apagados en
`mirova_equivalent` y en `experimental` (`pipeline.profile` importado con cada perfil).

## A2. La pasada descartada queda anotada una vez, con sus datos, y la cobertura deja de decir «completa»

Con los dos flags encendidos, HEAD contra el tag, por escena (`salidas/head_geo_sin_dato.json` y
`salidas/tag_geo_sin_dato.json`, diff en Python):

- `crater_borde` y `crater_relleno`, con y sin `--estricto-cobertura`: `records` vacío en los dos árboles;
  `codigo` 0 en los dos; lo único que difiere es `cobertura.incidencias` y `cobertura.n_incidencias`. HEAD trae
  exactamente una incidencia: `tipo crater_sin_dato`, `volcan Villarrica`, `fecha 2026-07-19`,
  `plataforma MODIS_TERRA`, `cuenta_estricto false`, `motivo "cráter sin posición en el gránulo (borde o relleno del
  MxD03): MOD021KM.A2026200.0300.061.hdf"`. El tag trae `[]`.
- `etiqueta` y `mxd03_corrido`: nada difiere (un record, sin incidencias) en los dos árboles.
- Salida por pantalla (`salidas/head_geo_sin_dato.log`): 4 líneas «Cobertura NO COMPLETA: 1 incidencias (ninguna
  búsqueda ni descarga fallida)» (las dos escenas sin cráter, con y sin estricto) y 4 «Cobertura: completa»; en el
  tag (`tag_geo_sin_dato.log`) 8 «Cobertura: completa».

Límite: el arnés fabrica un gránulo por pasada (`MODIS_TERRA`, un L1B y un MxD03), así que «exactamente una vez» está
medido para n = 1 gránulo. En `run_pipeline.py:244-263` el aviso se construye por gránulo L1B dentro del bucle, y en
`calculate_vrp` se llama una sola vez por gránulo (l. 679 a 681), de modo que dos gránulos de una misma noche darían
dos incidencias, una por descarte, que es lo que la afirmación dice. La fecha es la del `--date` de la corrida
(`date.strftime("%Y-%m-%d")`, `run_pipeline.py:406`), no la hora del gránulo; coincide con la del arnés porque el
gránulo es de ese día. No comprobé qué pasa cuando un gránulo cae en el día UTC siguiente al `--date` (SIN DATO;
es la misma convención de las incidencias de S159).

## A3. No cuenta en modo estricto; reproc_brazos la trata como no contable

- `pipeline/fetch.py:789-790`: `TIPOS_INCIDENCIA["crater_sin_dato"] = False`; `registrar_incidencia` (l. 798 a 803)
  copia ese valor a `cuenta_estricto`.
- `scripts/run_pipeline.py:471`: `cuentan = any(i.get("cuenta_estricto") ...)`, y l. 503 devuelve `3 if (estricto
  and cuentan) else 0`. Mi corrida: `codigo` 0 en `crater_borde|estricto=True` y `crater_relleno|estricto=True`.
- `scripts/reproc_brazos.py:114-119`: `cuentan = [i for i in incidencias if i.get("cuenta_estricto")]`, leído del
  JSON que escribió `run_pipeline`; no tiene lista propia de tipos, hereda la de `fetch`. Confirmado por lectura;
  `test_reproc_brazos_cuenta_lo_que_el_estricto_cuenta` (S159) fija el mecanismo. Detalle menor: su `::warning`
  (l. 117) sigue diciendo «(L1B sin geolocalización o día parcial)», y para las incidencias que no cuentan
  `reproc_brazos` no imprime nada, sólo las deja en su JSON (`l. 107`); eso ya era así con `sin_granulos`.

Lo que no sostiene la razón declarada: «se repite igual en todos los brazos de un A/B» vale cuando todos los brazos
llevan el flag. El A/B que decidiría encenderlo (brazo con `GEO` y `SIN_DATO` contra control sin ellos) descarta en un
brazo y escribe en el otro por construcción; ahí el modo estricto tampoco debería contar la incidencia (no es un hueco
de NASA, A108), así que la decisión se sostiene, pero por otra razón que la escrita. Y en ese A/B el evaluador
de paridad etiqueta esas ausencias como si el run no hubiera registrado nada: ver V16503-01.

## A4. El aviso sólo en el descarte por cráter sin posición; `None` igual sin aviso

Lectura: `calculate_vrp` tiene cuatro `return None` (l. 658, 682, 720, 766). El aviso está sólo en l. 680 a 681,
dentro del `if sin_dato_de_geolocalizacion(...)` (l. 679), que devuelve False salvo con
`ENABLE_MODIS_CRATER_SIN_DATO` encendido y `geo_fuente == "mxd03"` (l. 558 a 563), y `geo_fuente` sólo es
`"mxd03"` con `ENABLE_MODIS_GEO_MXD03` encendido y el MxD03 leído y de la misma forma (l. 525 a 537). La l. 658
es la vía «código MIROVA» (`ENABLE_MODIS_CODIGO_MIROVA`, apagado), l. 720 es ROI vacío y l. 766 es fondo sin píxeles:
ninguno avisa. El parámetro tiene default `None` y la llamada está guardada por `if al_sin_dato is not None`.
Corrida: `test_calculate_vrp_avisa_solo_cuando_descarta` (6 casos: dos flags en borde y relleno avisan y devuelven
None; `etiqueta` con dos flags, `GEO` solo, `SIN_DATO` solo y sin flags no avisan y devuelven record) y
`test_sin_aviso_sigue_devolviendo_none` pasan en mi suite; y mis corridas del arnés con `GEO` solo y con `SIN_DATO`
solo son bit a bit iguales al tag.

Observación, no defecto de este PR: con la vía «código MIROVA» de MODIS encendida (apagada hoy),
`calcular_vrp_granulo` devuelve None cuando el píxel más cercano al centro queda a más de 5 km o hay menos de 100
píxeles en el recorte (`pipeline/mirova_v750_codigo.py:791-808`), y `calculate_vrp` lo devuelve tal cual (l. 657 a
658) sin aviso. Es la semántica de «el gránulo no cubre el volcán», no la regla del cráter sin posición; si algún día
se quiere la misma trazabilidad para esa vía, es otro cambio.

## A5. Llamadores de producción

`grep -rn calculate_vrp` sobre `pipeline/ scripts/ .github/ frontend/` (`.py .yml .yaml .sh`): el único llamador de
`process_modis.calculate_vrp` fuera de `experiments/` y `tests/` es `scripts/run_pipeline.py:253`, y pasa el aviso en
l. 263 (`al_sin_dato=_crater_sin_dato(volcano, date, platform)`). Ni alias ni import renombrado: `scripts/` importa
`process_modis` sólo en `run_pipeline.py:82` (más `paper_numbers.py:161` y `libro_de_cuentas.py:233`, que no llaman a
`calculate_vrp`). Los workflows llegan por `run_pipeline.py` (nrt, backfill-tier-a, experimental-diario, reproc-*,
`reproc_brazos.py` que lo invoca por subproceso) o por probes de `experiments/` (29 archivos llaman a
`calculate_vrp` de MODIS; 3 pasan `al_sin_dato=None` explícito: los dos probes S151 del PR y la batería; los otros
26 usan el default, que es el mismo `None`). `scripts/backfill_nov_2025.py:49` importa `process_date` de
`run_pipeline` (pasa el aviso) pero nunca llama a `informar_cobertura`: anota y no informa; no está en ningún
workflow y ya le pasaba lo mismo con las incidencias de S159 (V16503-05, gravedad 0). VIIRS: `grep
crater_cubierto|sin_dato|SIN_DATO` sobre `process_viirs.py` y `process_viirs_mod.py` da 0: no hay descarte
equivalente que requiera aviso.

## A6. Batería de mutaciones

Corrida propia sobre `arbol` (3926f6a93), árbol quieto, después de la suite:
`salidas/mutaciones_salida_verificador.txt`. Ver el resultado al final de esta sección.

Lectura de la batería (`experiments/_s165_v165_03/mutaciones.py`): clasifica «atrapada» si al menos un `failure` o
`error` del junit empieza por `AssertionError` o `assert`; «caída» si sólo hay excepciones; «viva» si todo pasa. Los
controles son sin mutación (viva) y un `raise RuntimeError` al inicio de `informar_cobertura` (caída: el arnés en
subproceso convierte la muerte en `RuntimeError`, no en assert). Cada mutación exige que el texto original aparezca
exactamente una vez y restaura los tres archivos al final (y en `finally`). Muta los archivos del árbol que las
pruebas importan (no una copia). El commit dice que la corrida fue sobre 0df7b5257; 3926f6a93 sólo agrega la batería
y su salida, así que es el mismo código.

Qué cubren las 10: el tipo (que cuente en estricto; que no exista), `calculate_vrp` (no avisar; avisar en toda
pasada; motivo sin gránulo), `run_pipeline` (no pasar el aviso; anotar otro tipo; sin plataforma; otro volcán) y el
título del resumen. Qué no cubren: `informar_cobertura` con el tipo contando por otra vía (`cuentan`), la fecha
(`date.strftime`), la unicidad (avisar dos veces), `reproc_brazos`, y el `if al_sin_dato is not None` (quitarlo
haría caer a los llamadores sin aviso con `TypeError`, que la batería clasificaría «caída», no «atrapada»). Las
pruebas sí tienen aserciones que atraparían la fecha y la unicidad (`i["fecha"] == ARNES.FECHA`, `len(inc) == 1`),
pero la batería no lo demuestra.

## A7. Suite y CI

- Suite completa propia: `python -m pytest tests -q -p no:cacheprovider --basetemp=D:\...\pytest_tmp` con
  `VRP_PROFILE=mirova_equivalent PYTHONIOENCODING=utf-8`, sobre `arbol` sin tocar nada mientras corría (las corridas
  del arnés en paralelo son de sólo lectura): **2723 passed, 29 skipped, 2 xfailed, 0 fallas, 312 s**
  (`salidas/pytest_suite.txt`, rc = 0). `git status` limpio después.
- CI: PR #922 `mergeStateStatus CLEAN`, check `pytest` SUCCESS sobre `3926f6a933…` (run 40590920721, «Tests»,
  creado 2026-10-27 21:56:51 UTC): «2719 passed, 33 skipped, 2 xfailed». El workflow corre `python -m pytest tests/`
  en Linux con pyhdf; la diferencia de 4 passed / 4 skipped con mi corrida es de plataforma (SIN DATO cuáles; no
  los comparé uno a uno).

## A8. Citas y FICHA

- G8 verifica por contenido: `tests/test_guard_declarado_vs_efectivo_s131.py:218-223` lee la línea citada y exige
  que contenga el token. Contrato cambiado: `process_modis.py:1191 _path_d_cap_active` y `process_viirs.py:214
  compute_test1_nti`; en HEAD, l. 1191 es `_path_d_cap_active = (` y l. 214 es `from .test1_integrated import
  (compute_test1_mir, compute_test1_nti,`.
- CLAUDE.md, comprobado línea a línea en HEAD: `run_pipeline.py` 252/296/345 son las tres
  `get_detection_anchor(volcano)`; 262 es `local_kernel_bg_compatible=volcano.get("local_kernel_bg", False)` (la línea
  nueva quedó en 263, así que A89 no se corrió); `process_modis.py:64` es `compute_test1_mir`;
  `process_viirs.py:214/1170` son el import y la llamada a `compute_test1_nti`; `process_viirs_mod.py:164/467`
  correctas; `index.html` l. 1595 es `function isValidDetection(r) {`.
- Remapeo por contenido, repetido por mí con la herramienta del repo sobre los documentos tal como estaban en el tag
  (`scripts/remapear_citas.py pipeline/process_modis.py scripts/run_pipeline.py pipeline/process_viirs.py --base
  97ef53aa5 --docs <CLAUDE.md y guard del tag>`; `salidas/remapear_desde_tag.txt`): para el guard propone exactamente
  1185 → 1191 y 213 → 214, que es lo que el PR escribió. Para CLAUDE.md propone además 1112 → 1144 (el PR escribió
  1170 con la nota de que 1112 ya estaba corrido; 1170 es la correcta por contenido, 1144 es a donde fue la línea
  equivocada), 1313 → 1345 (histórica, «al momento del hallazgo», bien dejada) y **1172 → 1178, que el PR no
  aplicó** (V16503-03).
- FICHA: cabecera v1.17 del 2026-10-27 con v1.16 (#921) y v1.15 en orden; historial con filas v1.17 y v1.16. El
  texto de v1.17 no afirma de más: «sigue desactivada», «no hace fallar los reprocesos de comparación», «con la
  opción apagada el sistema produce exactamente lo mismo que antes» (medido en A1). Pero la fila tiene **3 celdas y
  no 4**: falta «Traz. interna» (V16503-02). Y la razón «se repite igual en todos ellos» hereda la salvedad de A3.

## Hallazgos propios

### V16503-01 (gravedad 2). El evaluador de paridad etiqueta la pasada anotada como «sin incidencia»

`scripts/evaluador_comun.py:324`: `_TIPOS_HUECO = ("falla_busqueda", "falla_descarga", "sin_geolocalizacion",
"dia_parcial")` es una lista en línea (A102), no deriva de `fetch.TIPOS_INCIDENCIA`, y no incluye `crater_sin_dato`.
`causa_ausencia` (l. 339 a 353) devuelve `CAUSA_SIN_INCIDENCIA` para una pasada cuyo único evento registrado es la
incidencia nueva; la constante se documenta como «el run no registró nada: no observado legítimo (o pérdida del
proceso)» (l. 322). Reproducido (`salidas/repro_evaluador_comun.txt`, archivo idéntico en tag y HEAD):

```
causa con incidencia crater_sin_dato     -> sin_incidencia
causa con incidencia sin_geolocalizacion -> hueco_nasa
causa sin eventos                        -> sin_incidencia
```

Qué pasa: en el A/B que decidiría encender el flag (brazo con `GEO` y `SIN_DATO` contra control), las 223 pasadas que
el censo MOD-D dice que el brazo descartaría quedarían, en el informe de huecos del evaluador, indistinguibles de
una pérdida del proceso: el mismo síntoma que V165-03 cierra en `run_pipeline`, una capa más arriba. No cambia el
veredicto del evaluador (`huecos` informa, no decide, según su propio comentario l. 311 a 320), pero sí lo que el
verificador de ese A/B leería. Confianza alta en el mecanismo; el impacto depende de que alguien corra ese A/B. No
está en las afirmaciones del PR. Arreglo esperable: una causa propia («sin dato del cráter») o derivar las listas de
`fetch.TIPOS_INCIDENCIA`, con prueba en `tests/test_evaluador_comun_s163.py`.

### V16503-02 (gravedad 1). La fila v1.17 de la FICHA tiene 3 celdas; falta «Traz. interna»

`docs/FICHA_SDA_VRP_CHILE.md`, fila `| v1.17 | 2026-10-27 | ... |`: contadas con `awk -F'|'`, 3 campos; la fila
v1.16 y las anteriores tienen 4. La tabla declara cuatro columnas (`Versión | Fecha | Cambios sustantivos | Traz.
interna`). Es el único cambio del historial sin su trazabilidad (archivos y pruebas: `pipeline/fetch.py`,
`pipeline/process_modis.py`, `scripts/run_pipeline.py`, `tests/test_crater_sin_dato_incidencia_s165.py`,
`tests/arnes_sin_dato_s165.py`, `tests/datos_s165_mxd03/sin_dato_corrida_*_antes.json`,
`experiments/_s165_v165_03/`). Reproducir: `grep -n "^| v1.17" docs/FICHA_SDA_VRP_CHILE.md | awk -F'|' '{print
NF-2}'` da 3. Confianza alta.

### V16503-03 (gravedad 1). `CLAUDE.md:1403` (A100) cita `process_modis.py:1172`, que el cambio corrió y no se remapeó

La cita dice que `FOCAL_CLUSTER_KEEP_PEAK` vive en `pipeline/process_modis.py:1172`. En el tag esa línea ya era
`n_excluded_water = 0` (cita vieja antes del PR); en HEAD la l. 1172 está en blanco y `keep_peak=FOCAL_CLUSTER_KEEP_PEAK`
está en l. 1356 (1350 en el tag). El cambio del PR la desplaza 6 líneas más, la herramienta del repo corrida desde
el tag la lista (1172 → 1178, que seguiría sin apuntar al símbolo), y el PR no la tocó ni la marcó. G8 no la vigila
(no está en `CITAS_CLAUDE_MD`); `test_g8b` sólo exige que la línea exista. Reproducir: `sed -n 1172p
pipeline/process_modis.py`; `grep -n FOCAL_CLUSTER_KEEP_PEAK pipeline/process_modis.py`. Confianza alta. Rebaja A8
a CONFIRMADO EN PARTE: «las citas que el cambio corrió» incluye esta, que no se remapeó por contenido ni por
aritmética.

### V16503-04 (gravedad 0, seguimiento). `docs/MIROVA_DIVERGENCES.md` arrastra 14 citas a `process_modis.py` que este PR corre 4 a 6 líneas

La herramienta corrida desde el tag (`salidas/remapear_desde_tag.txt`) lista 14 citas a `process_modis.py` (l. 245,
511, 2454, 2816, 2863, 2962, 2963, 3237 del documento) y 11 a `process_viirs.py` (estas corridas por #921, ya en
main). Casi todas ya estaban viejas antes (ejemplo: `:1009` en l. 245 es el número de S157 que el propio CLAUDE.md dice
que pasó a 1056, 1094 y 1185), y muchas están en bloques citados de auditorías pasadas. El docstring de
`scripts/remapear_citas.py` nombra este documento como tercer lugar a remapear. No es defecto de este PR; es deriva
heredada que el PR extiende. Sin verificar una por una cuáles son deliberadamente históricas.

### V16503-05 (gravedad 0, contexto). `scripts/backfill_nov_2025.py` anota y no informa

`scripts/backfill_nov_2025.py:49` importa `process_date` y `load_volcanoes` de `run_pipeline` y llama a
`process_date` (l. 106); no llama a `informar_cobertura` ni lee `fetch.incidencias_de_cobertura()`. Las incidencias
(las de S159 y esta) quedan en `fetch._INCIDENCIAS` y nunca se imprimen. No está en ningún workflow (`grep` en
`.github/workflows/` da 0) y es anterior al PR. Sólo para que nadie lo use como camino de reproceso creyendo que
informa cobertura.

## SIN DATO

- A2: comportamiento con un gránulo cuyo día UTC no es el `--date` (la fecha de la incidencia es la de la corrida).
  Misma convención que las incidencias de S159; no lo medí.
- A7: cuáles 4 pruebas pasan en mi Windows y se saltan en el CI de Linux (2723/29 contra 2719/33); no las comparé.
- Camino sin ejercer por el arnés (dicho por el propio arnés): la lectura real del HDF (pyhdf no corre en Windows),
  la red, `store` y el reloj solar están reemplazados. Lo que el arnés no puede decir: que con un MxD03 real `leer_mxd03`
  devuelva la forma del L1B (si no calza, `geo_fuente` no es `"mxd03"` y la regla no actúa, l. 533 a 535), ni que el
  nombre del gránulo real llegue al motivo (es `hdf_path.name`, l. 681: con una ruta real es el nombre del archivo).
- A6: resultado de mi corrida de la batería, al final de esta sección si terminó; si no, queda como SIN DATO.

## Seguimientos sugeridos (no bloquean el PR, salvo el que Nicolás decida)

1. V16503-01: agregar `crater_sin_dato` al evaluador con causa propia, o derivar `_TIPOS_HUECO` y la causa de
   `fetch.TIPOS_INCIDENCIA`, antes de correr cualquier A/B con el flag encendido.
2. V16503-02: completar la cuarta celda de la fila v1.17.
3. V16503-03: corregir la cita de A100 a `process_modis.py:1356` (`keep_peak=FOCAL_CLUSTER_KEEP_PEAK`) con la nota
   de historia, y considerar meterla en `CITAS_CLAUDE_MD` de G8.
4. Afinar la razón escrita en `fetch.py:785-787`, en `_crater_sin_dato` y en la FICHA: «no cuenta porque no es un
   hueco de NASA que repetir el job recupere», sin «se repite igual en todos los brazos», que no vale para el A/B del
   flag.
5. `reproc_brazos.py:117`: el texto del `::warning` enumera sólo dos tipos contables; cosmético.

## Resultado de la batería (corrida propia)

`python experiments/_s165_v165_03/mutaciones.py` sobre `arbol` (3926f6a93), después de la suite y sin nada más
corriendo sobre el árbol (`salidas/mutaciones_salida_verificador.txt`, rc = 0): las 12 filas con `OK`,
«mutaciones reales atrapadas por aserción: 10 de 10», «controles: sin mutación viva, caída caida», «todo como se
esperaba». Las líneas de resumen son idénticas a las de `experiments/_s165_v165_03/mutaciones_salida.txt` del PR
(`diff` vacío). `git status` limpio al terminar: la batería restauró los tres archivos. A6 queda CONFIRMADO con los
huecos de cobertura dichos en su sección (no son mutaciones fallidas, son piezas que la batería no ejerce).

Cierre: 2026-10-27, después de las 22:30 UTC (hora de inicio 21:58 UTC por el servidor; lo demás es duración
medida localmente, no vuelta a pedir). Los dos árboles de D: se borran con `git worktree remove --force` al entregar.
