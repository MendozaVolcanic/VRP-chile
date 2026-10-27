# INFORME del verificador con contexto limpio: S164 MOD-D fase 3, via «codigo MIROVA» para MODIS (PR #919)

Commit medido: `c4efdc78c` (rama `claude/s164-modis-codigo-mirova`). Base: tag `pre-s16x-modis-codigo-mirova` =
`9c1adb629` (origin/main al abrir el cambio era `cc16b3a7f`, que incluye ese tag mas commits de datos NRT; el diff que
se verifico es `git diff pre-s16x-modis-codigo-mirova c4efdc78c`, 18 archivos). Hora del servidor al empezar:
`Tue, 27 Oct 2026 12:11:33 GMT`. CAMINOS.md escrito antes de abrir el codigo, sha256
`d82f8dfa81ab352df7126ea3cbe7b650ca43a56799da8428a7d3ae7c2da7c238` (`CAMINOS.sha256`).

Carpeta de este informe: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\funny-kepler-68f0ef\experiments\_s164_modis_codigo\verificador\`.
Ningun archivo del repo fuera de esa carpeta se modifico (`git status --short` da solo `?? experiments/_s164_modis_codigo/verificador/`).
Las mutaciones se corrieron sobre una copia de HEAD en el scratchpad, nunca sobre `pipeline/` del worktree.

## Veredicto global

**El cambio hace lo que dice en lo esencial**: con el flag apagado el procesador MODIS es identico al de antes al
nivel del `repr` de cada double (no solo a 9 cifras), en los tres perfiles; la via de VIIRS 750 no cambio; la deteccion
de la via MODIS reproduce al port del censo en **5.321 de 5.321** pasadas del censo (no solo en 5); el fallback y la
exencion del almacen son los declarados; las mutaciones del PR se reproducen; el CI de #919 corrio sobre este commit.

**Lo que no se sostiene tal como esta escrito**: (1) A3, «el VRP del port del censo con el relleno segun la regla de
fillmissing2», vale en las 5 fixtures y en 108 de 109 alertas del censo, pero **no en la 109**: en una alerta pegada al
borde del granulo (PCC 2026-03-16 03:10) la via da **2,535 MW** donde el instrumento del censo (`m_con_regla_matlab.py`,
blob f273a47a) dio **0,246 MW**, porque la via deja NaN fuera de la envolvente convexa (como MATLAB, con prueba de oro)
y el blob f273a47a rellena con el vecino mas cercano. El «codigo independiente» de `esperado.json` es ese blob, asi que
las fixtures no pueden ver esta diferencia. (2) A4, «las del paper»: la lambda TIR de 11,03 um es la banda 31, pero el
algoritmo del paper usa la banda 32 (12,02 um) para el NTI (divergencia D20, ya catalogada), y la caja conservadora de
15 x 15 celdas no esta en el paper (ROI2 del paper = todo el marco de 50 x 50 km salvo ROI1); si son las de produccion y
las del port del censo. (3) A1, «bit a bit»: la prueba del PR compara a 9 cifras significativas; el bit a bit lo midio
este verificador aparte y se cumple.

Por afirmacion: A1 CONFIRMADO · A2 CONFIRMADO · A3 CONFIRMADO EN PARTE · A4 CONFIRMADO EN PARTE · A5 CONFIRMADO EN
PARTE (lectura; HDF real SIN DATO) · A6 CONFIRMADO · A7 CONFIRMADO (25 de 25 reproducidas; cinco mutaciones obvias
quedan vivas, V164-06) · A8 CONFIRMADO · A9 CONFIRMADO (CI verde sobre el commit y suite local 2640 / 29 / 2).

Hallazgos propios, por gravedad: V164-01 (3) VRP de la via 2,535 MW contra 0,246 del censo en una alerta de borde ·
V164-06 (3) remuestreo, radio, sun-glint y clase de distancia sin prueba que los vigile · V164-02 (2) atribucion al
paper de la banda 31 (D20) y de la caja 15 x 15 · V164-03 (1) `mutaciones.py` fragil ante CRLF · V164-04 (1) cortes de
cobertura de la via sin marca, costo cero en el censo · V164-05 (1) «bit a bit» del PR es a 9 cifras.

---

## Veredictos por afirmacion

### A1. Flag apagado = bit a bit lo mismo que antes en process_modis.py. **CONFIRMADO** (gravedad 1 por el nombre)

Caminos revisados (CAMINOS.md §A1, 1 a 8):

- *Golden generado con el codigo nuevo (1)*: regenere la salida del arnes S142 (`--solo modis`) con el arbol del tag
  base extraido por `git archive` a un directorio aparte y con HEAD. sha256 identicos
  (`9475bfd7…4191` las dos) e identicos al golden `tests/datos_s164_modis/modis_k_antes.json` en forma canonica
  (`golden==base_tag: True`, `golden==hoy: True`). Archivos: `golden_base_tag_modis.json`, `golden_hoy_modis.json`.
- *«Bit a bit» con redondeo (6)*: la prueba del PR canoniza con `arnes_sintetico_s142._redondear`, que redondea a
  `SIGNIFICATIVAS = 9` cifras (`tests/arnes_sintetico_s142.py:291`). Este verificador comparo ademas con `repr` de cada
  float (ida y vuelta exacta): `a1_bit_a_bit_crudo.py` sobre los dos arboles y los perfiles `mirova_equivalent`,
  `experimental` y `experimental_ndc_focus`, 3 escenas, 53 claves por record: **IGUAL crudo** en los 3 perfiles
  (`a1_salidas/`, los sha difieren solo por las claves `__raiz` y `__flag`, que se quitan antes de comparar).
- *Flag leido de otro lado (3, 8)*: `pipeline/profile.py:909` lo lee de `_t` (`thresholds:`), como `enable_v750_codigo_mirova`;
  `grep codigo_mirova pipeline/profiles/*.yaml` da 0 resultados: ningun perfil lo escribe, default `False` en todos.
  El arbol base no tiene el atributo (`NO EXISTE EN ESTE ARBOL`), HEAD lo tiene en `False`.
- *Segundo punto de entrada (4)*: el diff toca `process_modis.py` (bloque condicionado + `_sensor_modis`, que devuelve
  el mismo string que antes), `profile.py` (una constante) y `mirova_v750_codigo.py`. `store.py`, `run_pipeline.py` y
  `process_viirs_mod.py` no cambian en este PR (`git diff --stat`).
- *La via se ejecuta por otro camino (7)*: `test_flag_apagado_no_toca_la_via` parchea las 5 funciones de `MV` que el
  bloque llama y el bloque hace `from . import mirova_v750_codigo as _MV` en tiempo de llamada, asi que ve los parches.
  Ademas el bloque entero esta bajo `if ENABLE_MODIS_CODIGO_MIROVA:` (`process_modis.py:558`).

Vara: salida del arnes S142 del arbol base, sin redondeo. Las 3 escenas incluyen una que publica (`nevado`, vrp 4,6352).

### A2. FAMILIAS no cambia la via de VIIRS 750 ni su cableado. **CONFIRMADO**

- `a2_v750_base_vs_head.py` carga el modulo del tag base y el de HEAD y compara con `repr` exacto: Etna del OSF
  (mascara, diag completo con contrastes, VRP), las 8 escenas del oro de MATLAB (fondo celda a celda y VRP), 30 grillas
  sinteticas 67 x 67 (22 con alerta: deteccion, diag, VRP y record de `procesar_grilla`), grillas y cajas de los 11
  volcanes y los 5 tipos de ROI, y un granulo sintetico de 750 m en Lascar por `calcular_vrp_granulo` (remuestreo
  incluido). **Todo IGUAL** (`a2_v750_base_vs_head_salida.txt`).
- Cableado: `process_viirs_mod.py:507` llama `grilla_del_volcan(volcan_nombre)` y `:512` `calcular_vrp_granulo(...)` sin
  `familia`, asi que caen en los defaults `paso_m=750`, `clave_roi="roi_v750"`, `familia="VIIRS750"`; `procesar_grilla`
  con `coef=None` toma `FAMILIAS["VIIRS750"]["coef"] == COEF_VRP_V750` (misma constante, `11.08125` en los dos arboles).
  Los 3 archivos de prueba (`test_mirova_v750_codigo_s162.py`, `test_mirova_v750_cableado_s162.py`,
  `test_mirova_modis_codigo_s164.py`) dan **88 passed** (`pytest_tres_archivos_salida.txt`).

### A3. 5 grillas del censo: mismos pixeles, numeros por pase y VRP con la regla de MATLAB; Lascar 1611 da 1,1124 MW. **CONFIRMADO EN PARTE**

Lo que se confirma:
- Las 5 fixtures dan los mismos pixeles, `n_abs/n_p1/n_p2`, mu, sd y umbrales de cada pase que `mirova_port` del censo
  (prueba del PR, 88 passed; y vuelto a medir en `a3_a8_censo.py`).
- Lascar 2026-04-25 07:35 (id 1611): `vrp_regla_matlab = 1.1123740911483764` recalculado por mi con el blob f273a47a sobre
  la grilla del censo, igual al esperado a 1e-12; `censo_vrp_port = 0.973082188789508` (el port con su desempate).
- **Extendido a todo el censo** (`a3_a8_censo_salida.txt`): 5.465 records, 5.321 `ok` con `port.fisica`. Deteccion de
  la via con `FAMILIAS["MODIS"]` contra `port.fisica`: **0 pasadas con pixeles distintos, 0 con (n_abs, n_p1, n_p2)
  distintos**, 109 con alerta (histograma npix: 1: 45, 2: 35, 3: 16, 4: 6, 5: 4, 6: 1, 8: 1, 9: 1).

Lo que NO se sostiene (hallazgo V164-01, abajo): en las 109 alertas, el VRP de la via contra `hueco + f273a47a.rellenar`
(el instrumento del censo, `m_con_regla_matlab.py::regla`) da **108 iguales y 1 distinto**: PCC 2026-03-16 03:10
(id 3933), 1 pixel en BOX 2, via **2,534755 MW**, censo **0,245619 MW**, con 1 celda de alerta cuyo fondo es NaN en la
via. La afirmacion «el VRP del port del censo con el relleno segun la regla de fillmissing2 de MATLAB» vale para las 5
fixtures y no para la via en general.

### A4. Constantes MODIS = paper, produccion y port. **CONFIRMADO EN PARTE**

| constante | via (`FAMILIAS["MODIS"]`) | produccion (`process_modis.py`) | port (`mirova_port.SENSORES["MODIS"]`) | paper (`documentacion/sp426_5.txt`) |
|---|---|---|---|---|
| lambda MIR | 3,959 | `BAND22_LAMBDA = 3.959` (l. 76) | 3,959 | l. 176-177: «radiance of band 22 (L22), centred at 3.959 mm» |
| lambda TIR | 11,03 | `BAND31_LAMBDA = 11.03` (l. 81) | 11,03 | l. 179-180: banda 31 «centred at 11.03 mm»; **pero** l. 214-216: «we used two of them (L21ok and L32) … LTIR is the radiance of the TIR channel (L32)», banda 32 a 12,02 um (l. 182-183) |
| coeficiente | `1.89e7 * 1.0 / 1e6` | `WOOSTER_COEFF = 18.9`, `NADIR_PIXEL_AREA_M2 = 1e6` (l. 84, 87) | 1,89e7 x 1,0 | l. 374: «RPPIX = 18.9 × APIX × DL4PIX (7)»; l. 384: «APIX is the pixel size (1 km2 for the resampled» |
| grilla | 1.000 m, 51 celdas | (produccion no remuestrea, D17) | `celda: 1000`, n 51 (grillas.json) | l. 162-164: «resampled (into an equally spaced 1 km grid) … within a grid (50 × 50 km)» |
| caja sensible | 5 x 5 celdas | no aplica | «fisica»: ±2.625 m = 5 celdas | l. 189-191: «inner region (ROI1) consists of a box (5 × 5 km) centred on the volcano's summit» |
| caja conservadora | 15 x 15 celdas (BOX 1) | no aplica | «fisica»: ±7.875 m = 15 celdas | l. 204-206: «second, larger region (ROI2) represents the outer frame (measuring 50 × 50 km) and includes the whole scene with the exception of the ROI1»: **no hay 15 x 15 en el paper** |

- La lambda TIR es la de produccion y del port, no la del algoritmo del paper: es la divergencia **D20** del catalogo
  (`docs/MIROVA_DIVERGENCES.md:2678`, «El NTI de MODIS se calcula con la banda 31 (11,03 µm); Coppola 2016a y Wright
  2002 usan la banda 32 (12,02 µm)»). La via hereda D20; la afirmacion la atribuye al paper.
- La caja 15 x 15 sale del `.m` de VIIRS 750 (21 celdas de 750 m) pasado a metros, no del paper. En el `.m` BOX 0 y
  BOX 1 se evaluan con los mismos umbrales conservadores (`MIROVA_VIIRS750_hotspot_detection.m` l. 105-110: «BOX == 0 …
  tested using the same conservative NTI and ETI thresholds»), asi que en umbrales la via coincide con las dos ROI del
  paper y el 15 x 15 solo marca la zona en el diagnostico. Efecto en la deteccion: ninguno (SOSPECHA razonada desde el
  `.m`, no medida aparte).
- `test_constantes_de_modis_son_las_del_paper_y_de_produccion` compara via = produccion = port y cita el paper en el
  docstring; mide la igualdad entre los tres, no contra el paper.

### A5. Lectura y armado = los del probe del censo. **CONFIRMADO EN PARTE** (por lectura de codigo; HDF real SIN DATO)

Fuente del censo: `probe_paquete.py` (tag `s162-modd-tag`, blob `6e9c94b4`) corre `probe_portes.procesar(..., sin_k=True)`
del blob sellado `8ec50e7b`, que es el que esta en el worktree (`git hash-object experiments/_s159/portes/probe_portes.py`
= `8ec50e7bbb76…`; `mirova_port.py` = `96769a89…`, tambien sellado).

Igual, linea a linea:
- `leer_radiancia_modis` = `probe_portes.leer_modis` en bandas: `read_modis_l1b` de produccion, `float64`,
  `merge_mir_bands(b21, b22, True)` (B22 primaria, B21 donde satura), TIR = banda 31.
- `leer_geo_mxd03` = `leer_modis` en geolocalizacion: `Latitude`/`Longitude` del MxD03 a float64, fuera de rango a NaN,
  4 angulos por `scale_factor` sin enmascarar.
- Control de forma: probe `lat3.shape != d["band21"].shape`; via `np.shape(_lat) != np.shape(_rad["MIR"])` (la MIR
  fusionada conserva la forma de band21).
- Corte de 5 km al centro, `i0` = pixel mas cercano, `geom` en `i0`, `dayflag = 0 if solar_zenith > 90 else 1` con
  default 180, `sunglint_deg(sat_zen, sun_zen, sat_azi, sun_azi)`: identicos.
- Remuestreo: probe `grillar` toma `isfinite(lat)&isfinite(lon)&haversine<45` y `griddata(..., method="linear")` sobre
  `MP.centros(g)`; via `remuestrear_grilla` toma `isfinite(lat)&haversine<45` (lon NaN cae por el haversine NaN) y el
  mismo `griddata` lineal sobre `ul_x + paso*(k+0.5)`, `ul_y - paso*(k+0.5)`, que es `MP.centros`. Mismo conjunto de
  puntos en el mismo orden (seleccion booleana en orden de filas; el recorte rectangular `_ventana` del probe es un
  sub-rectangulo contiguo que contiene el disco de 45 km + 15 km de margen, l. 130-141), asi que Qhull recibe lo mismo.
- Grilla: `grilla_del_volcan(nombre, 1000.0, "roi_modis")` reproduce `ul_x`, `ul_y`, `n`, `epsg` de `grillas.json` del
  tag (prueba del PR para los 11, 88 passed).

Diferencias encontradas (ninguna con efecto medible en el censo, ver V164-04):
- La via devuelve `None` si hay menos de 100 pixeles a menos de 45 km (`calcular_vrp_granulo`); el probe no tiene ese
  corte (tiene el de `_ventana`: ningun pixel submuestreado a menos de 60 km).
- El probe marca `port_grilla = "grilla_incompleta"` si mas de la mitad de la grilla es NaN (45 pasadas del censo) y
  sigue; la via sigue igual y guarda `celdas_sin_dato` en el diag.

SIN DATO: `pyhdf` no corre en Windows; la lectura real de un MxD021KM/MxD03 por `leer_radiancia_modis`/`leer_geo_mxd03`
no se ejecuto aqui. La prueba del PR simula `pyhdf.SD` con un doble.

### A6. Fallback a K con motivo; store.py exime solo a `via_codigo_mirova is True`. **CONFIRMADO**

- `process_modis.py:558-583`: `sin_grilla` si `volcan_por_coordenadas` da None o no hay grilla; `sin_mxd03` si
  `geo_path is None`; `geo_distinta` si las formas no calzan; en los tres casos el bloque no retorna, K corre y la marca
  entra al record final (`:1668`, solo si `_via_marca is not None`; con el flag apagado la clave no existe). Pruebas del
  PR para los tres (88 passed) y mutaciones `pm_sin_marca_sin_grilla`, `pm_sin_control_mxd03`, `pm_sin_control_forma`,
  `pm_marca_no_se_escribe` atrapadas.
- `store.py:357` `_via_mirova = record.get("via_codigo_mirova") is True`; exime en `:362` (filtro de pixeles por
  distancia), `:401` (cero por hotspot lejano) y `:455` (tope de pixeles del cumulo). Marcas `False` y `"sin_grilla"` no
  eximen (prueba parametrizada del PR; mutacion extra `store_truthy_en_vez_de_is_true`, ver §A7).
- Observaciones (no contradicen A6):
  - `sin_mxd03` es **inalcanzable desde `run_pipeline.py`**: `:247-250` descarta el L1B sin su MxD03 antes de llamar
    (`_sin_geolocalizacion`). Solo un llamador directo puede pasar `geo_path=None`.
  - Cuando la via corre y devuelve `None` (volcan fuera del granulo: menos de 100 pixeles a 45 km o pixel mas cercano a
    mas de 5 km), `calculate_vrp` devuelve `None` **sin correr K y sin marca** (`:578-579`). En el censo ese caso ocurrio
    144 veces (`port_estado = volcan_fuera_del_granulo`) y en las 144 **K tampoco publico** (`pub K = 0`;
    `a6_censo_estados_y_pcc3933_salida.txt`), asi que en la poblacion medida no cuesta nada. Fuera de ella es SOSPECHA.
  - El rechazo diurno del almacen (`store.py:646-651`, `_reject_daytime`) sigue aplicando a los records de la via (no
    esta eximido). Coherente con el censo (solo pasadas nocturnas) y con `_check_night` de `run_pipeline.py:245`.
  - En el camino `geo_distinta` la via ya leyo el L1B (`leer_radiancia_modis`) y despues K lo vuelve a leer: doble
    lectura, solo costo de tiempo.

### A7. Mutaciones 25 de 25 atrapadas; clasificador; mutaciones que faltan. **CONFIRMADO**, con hallazgos

- Clasificador (`mutaciones.py::correr`): lee el junit y cuenta «atrapada» solo si algun `failure/error` tiene mensaje
  que empieza por `AssertionError` o `assert`; si solo hay excepciones, «caida». Una caida **no** puede contarse como
  atrapada por ese criterio. Lo que si puede: una mutacion que hace caer varias pruebas y hace fallar por asercion UNA
  cuenta como atrapada (ej. `paso_750`: `IndexError` en las de identidad y asercion en la de constantes). Es un criterio
  razonable (basta una prueba que la vea), pero el conteo «25 de 25» mezcla vigilancia fuerte (identidad en 5 grillas)
  con vigilancia por una sola asercion de constantes.
- Control de caida: `control_caida` sale «caida» (RuntimeError en 2 pruebas), como debe.
- Re-corrida: ver `mutaciones_rerun_en_copia_salida.txt` (copia de HEAD en el scratchpad con finales de linea LF). El
  resultado de la primera re-corrida fue invalido por mi instrumento: `git archive` con `core.autocrlf=true` produjo CRLF
  y la mutacion `geo_sin_enmascarar_lat` (anclada en `\n`) no encontro su texto; ademas faltaba el `.mat` de Etna en la
  copia. Se repitio con `git -c core.autocrlf=false archive` y con `experiments/_s158_d17_diseno/osf_codigo_mirova`
  (la salida de la primera corrida quedo sobrescrita por la segunda en el mismo archivo; sus dos lineas que importan,
  copiadas de la consola: `control_sin_mutacion esperado=viva resultado=caida NO` con
  `test_etna_igual_al_oraculo_y_a_produccion_de_miroVA: 'OSError: Reader needs file name…'`, y
  `AssertionError: geo_sin_enmascarar_lat: el texto original aparece 0 veces`).
  **Segunda corrida: 28 lineas de resumen identicas a `mutaciones_salida.txt` del PR** (`diff` vacio): 25 de 25
  atrapadas, `control_sin_mutacion` viva, `control_caida` caida, `roi_de_v750` viva (equivalente, como se esperaba).
- Mutaciones extra (no incluidas en el PR), `mutaciones_extra.py` → `mutaciones_extra_salida.txt`, misma copia y mismo
  clasificador (`control_sin_mutacion` viva):

  | mutacion | resultado | que la ve |
  |---|---|---|
  | `pm_via_none_cae_a_k_en_silencio` (`if _rec is None: return None` → sigue a K) | **viva** | nadie |
  | `radio_recorte_30_km` (`RADIO_RECORTE_KM` 45 → 30) | **viva** | nadie |
  | `remuestreo_nearest` (`griddata(..., method="linear")` → `"nearest"`) | **viva** | nadie |
  | `sunglint_sin_azimut` (azimuts a 0 en `calcular_vrp_granulo`) | **viva** | nadie |
  | `distance_class_siempre_summit` | **viva** | nadie (las pruebas solo tienen casos summit) |
  | `minimo_100_pixeles_roto` (`< 100` → `< 100000`) | caida | `test_extremo_a_extremo…` se cae con `TypeError`, no asevera |
  | `dayflag_invertido` | atrapada | `test_extremo_a_extremo…` (`assert 1 == 0`) |
  | `coef_v750_en_procesar_grilla` | atrapada | `test_lascar_…` (0,652 vs 1,112), `test_procesar_grilla_usa_…` |
  | `store_truthy_en_vez_de_is_true` | atrapada | las dos pruebas del almacen (MODIS y V750) con marca `"sin_grilla"` |
  | `sensor_terra_aqua_invertido` | atrapada | bit a bit, `test_flag_encendido_…`, `test_extremo_a_extremo…` |

  Ver V164-06: el remuestreo lineal y su radio, que el propio modulo describe como «la pieza que … calla las cumbres
  tibias» (`mirova_v750_codigo.py:183`), no tienen ninguna prueba en `tests/` que los vigile, ni para MODIS ni para
  VIIRS 750.

### A8. Fixtures sin alterar; esperados por codigo independiente. **CONFIRMADO** (con la salvedad de A3)

- `a3_a8_censo.py`: las 5 `grilla_*.npz` son **byte a byte** (`array_equal(equal_nan=True)`, mismo `float32`) los
  arreglos `mir` y `tir` de `grilla_NNNN.npz` del censo en `D:\vrp-trabajo\temporales\s162_modd\censo\run_*\...`;
  `vol`, `dt`, `lab`, `inner`, `dayflag`, `sunglint`, `npix`, `pixeles`, `vrp_port`, `n_abs/n_p1/n_p2` de
  `esperado.json` coinciden con el record `ab_*.jsonl` del censo; `vrp_regla_matlab` recalculado por mi con el blob
  `f273a47a` (`git cat-file -p f273a47a`, mismo hash que `experiments/_s162_modis_paquete/delaunay_perturbado.py` del
  tag) coincide a 1e-12 en las 4 con alerta y es `None` en Villarrica 4943 (sin alerta).
- Independencia: `armar_fixtures.py` importa `delaunay_perturbado` (f273a47a) y `mirova_port`, no `pipeline/`. Pero
  f273a47a **no es la misma regla que la via** fuera de la envolvente convexa (`diff_delaunay_via_vs_f273a47a.txt`:
  `_orient` e `_incircle` identicas; `lado_perturbado` equivalente (refactor a `elif`); `triangular` igual salvo el
  contador de volteos; `rellenar` rellena fuera de la envolvente con `griddata(..., method="nearest")` y la via deja
  NaN). Por eso el «codigo independiente» no puede ver V164-01.

### A9. Suite 2640 passed, 29 skipped, 2 xfailed; CI de #919 verde. **CONFIRMADO**

- `gh pr view 919`: `headRefOid = c4efdc78ca395716ecc19ed1f64d9d3a32316f3a`, check `pytest` `SUCCESS`, estado `OPEN`,
  borrador.
- Suite local completa sobre el worktree en `c4efdc78c` (`VRP_PROFILE=mirova_equivalent`, `-p no:cacheprovider`, sin
  editar nada durante la corrida; en paralelo corrian las mutaciones, pero sobre la copia del scratchpad, otro arbol):
  **`2640 passed, 29 skipped, 2 xfailed, 84 warnings in 372.54s`**, exit 0 (`pytest_suite_completa_salida.txt`). Los
  mismos tres numeros que afirma el PR.

---

## Hallazgos propios (orden por gravedad)

### V164-01. La via y el instrumento del censo discrepan 10x en una alerta pegada al borde del granulo; las fixtures no lo ejercen
- **Archivo:linea**: `pipeline/mirova_v750_codigo.py:505-538` (`_fillmissing2_lineal`, «FUERA de la envolvente convexa
  queda NaN», l. 507) y `:541-563` (`vrp_mirova`; `L_bk = nansum(fondo[mascara])` en l. 561); `experiments/_s162_modis_paquete/m_con_regla_matlab.py`
  del tag (`regla = DP.rellenar(enm, "xy_fila_col")[0]`, con `rellenar` que pone vecino mas cercano fuera de la
  envolvente, `insumos/delaunay_perturbado_f273a47a.py:160-163`); `tests/datos_s164_modis/armar_fixtures.py:26-30`.
- **Que pasa**: en PCC 2026-03-16 03:10 (id 3933, MODIS_TERRA, cenit 65,2°, 1.294 de 2.601 celdas NaN) la unica
  alerta esta en (23, 24), BOX 2, con el borde del granulo a su derecha (vecindario en
  `a6_censo_estados_y_pcc3933_salida.txt`). Tras el halo 3 x 3 la celda queda fuera de la envolvente de los puntos con
  dato: MATLAB (y la via) no la rellenan, `sum(..., 'omitnan')` del `.m` (`MIROVA_VIIRS750_VRP.m` l. 83-84) la descarta
  del fondo y el VRP es toda la radiancia: **2,535 MW**; el blob f273a47a le pone el vecino mas cercano y da **0,246 MW**
  (igual al port, 0,245619). MIROVA en esa pasada: `neg_limpio` (no vio nada); K: 0.
- **Como se ve**: la columna M «con regla de MATLAB» del censo (D-48) y la FICHA v1.14 («reproduce a MATLAB en 191 de
  191 escenas») se midieron con f273a47a; la propia nota de S163 lo dejo como SOSPECHA («con una alerta fuera de la
  envolvente MATLAB y la regla si discreparian», `RESULTADO_O2_MODIS_MATLAB.md` l. 14-15 en la rama s162). Aqui esa
  sospecha tiene un caso real: 1 de 109 alertas del censo, y el cambio cruza el corte de 1 MW de alerta protegida en un
  negativo limpio. La via sigue al `.m` + MATLAB; el instrumento del censo no. La afirmacion A3 y el texto de la FICHA
  («el fondo bajo las alertas se rellena con la misma regla que usa MATLAB») atribuyen a la via el numero del censo.
- **Reproducir**: `python experiments/_s164_modis_codigo/verificador/a3_a8_censo.py` (seccion «A3: VRP via …», 137 s).
- **Confianza 5 · Gravedad 3** (una pasada en 5.321, pero cambia la clase del error y las pruebas no lo ven; cual de los
  dos rellenos es el de MIROVA para MODIS es SOSPECHA en los dos sentidos).

### V164-06. El remuestreo lineal, su radio de 45 km, el sun-glint y la clase de distancia no tienen prueba que los vigile
- **Archivo:linea**: `pipeline/mirova_v750_codigo.py:180-204` (`remuestrear_grilla`, `griddata(..., method="linear")`,
  `RADIO_RECORTE_KM`), `:767-768` (`sunglint_deg(...)` con los azimuts), `:682` (`distance_class`);
  `pipeline/process_modis.py:578-579` (`if _rec is None: return None`).
- **Que pasa**: con el mismo clasificador del PR y sobre la copia de HEAD, cinco mutaciones quedan **vivas**:
  `remuestreo_nearest`, `radio_recorte_30_km`, `sunglint_sin_azimut`, `distance_class_siempre_summit` y
  `pm_via_none_cae_a_k_en_silencio` (`mutaciones_extra_salida.txt`). Las pruebas de identidad (A3) arrancan de grillas
  YA remuestreadas, las de cableado parchean `calcular_vrp_granulo`, y la unica prueba que remuestrea
  (`test_extremo_a_extremo_con_granulo_sintetico_en_lascar`) usa un foco de 300 K sobre 265 K que cualquier remuestreo
  detecta, de noche (sun-glint sin efecto) y en la cumbre. El mismo hueco existe para VIIRS 750 desde S162
  (`test_mirova_v750_codigo_s162.py` no llama a `remuestrear_grilla`).
- **Como se ve**: el modulo dice que el remuestreo lineal es «la pieza que, segun V750-C, calla las cumbres tibias de un
  pixel» (`:183-184`); una regresion ahi (metodo, radio, orden de puntos) pasaria la suite completa en verde. Las 25 de
  25 del PR cubren constantes, caja, lectura, lambdas, fallback y marca; no la interpolacion.
- **Reproducir**: `python experiments/_s164_modis_codigo/verificador/mutaciones_extra.py <copia de HEAD con LF>`.
- **Confianza 5 · Gravedad 3** (no es un error del cambio: es lo que la suite no puede ver; con el flag apagado no
  afecta produccion).

### V164-02. A4 atribuye al paper dos constantes que no son del paper
- **Archivo:linea**: `pipeline/mirova_v750_codigo.py:77-78` (comentario «banda 22 y banda 31 (Coppola 2016a, sp426_5.txt
  l. 174-180…)»), `:92-105` (FAMILIAS, caja 5/15); `tests/test_mirova_modis_codigo_s164.py:81-85` (docstring).
- **Que pasa**: el paper dice banda 31 a 11,03 um en su lista de bandas (l. 179-180) pero calcula el NTI con L32
  (l. 214-216), banda 32 a 12,02 um (l. 182-183): es D20, catalogada. Y la ROI2 del paper es «the outer frame
  (measuring 50 × 50 km) … with the exception of the ROI1» (l. 204-206), no una caja de 15 x 15 km.
- **Como se ve**: la via es fiel a produccion y al censo (lo medido), no al paper en esos dos puntos. Sin efecto en los
  numeros (la prueba compara via = produccion = port).
- **Reproducir**: `sed -n 176,183p; sed -n 203,216p` sobre `documentacion/sp426_5.txt`; `grep -n D20 docs/MIROVA_DIVERGENCES.md`.
- **Confianza 5 · Gravedad 2** (atribucion, no comportamiento; A113: la marca de D20 no bajo a este comentario).

### V164-03. `mutaciones.py` depende de finales de linea LF y de archivos fuera de los que lista
- **Archivo:linea**: `experiments/_s164_modis_codigo/mutaciones.py:47-49` (`"    lat[(lat < -90) | (lat > 90)] = np.nan\n"`),
  `:53` (`'    lam = cfg["lam_mir"]\n'`), `:73` (`"    if ENABLE_MODIS_CODIGO_MIROVA:\n"`), `:79`
  (`"                    vent_lat if vent_lat is not None else volcano_lat,\n"`); `:104-105` (`assert s.count(a) == 1`).
- **Que pasa**: cuatro mutaciones anclan en `\n`; sobre una copia con CRLF (lo que produce `git archive` o un checkout
  con `core.autocrlf=true`, que es la configuracion de este repo en Windows) el texto «aparece 0 veces» y el script
  aborta en la mutacion 13 (`mutaciones_rerun_en_copia_salida.txt` de la primera corrida, conservada en este informe,
  §A7). El worktree tiene LF y por eso el PR corrio entero.
- **Como se ve**: fragilidad del instrumento, no del cambio. En un checkout nuevo con autocrlf el script no reproduce
  los 25 de 25 (memoria S163 «md5 y autocrlf»).
- **Reproducir**: `git archive HEAD pipeline tests … | tar -x -C X` con `core.autocrlf=true` y correr `mutaciones.py` ahi.
- **Confianza 5 · Gravedad 1**.

### V164-04. Cortes de cobertura de la via que ninguna prueba ni el censo acotan
- **Archivo:linea**: `pipeline/mirova_v750_codigo.py:760-764` (`sel.sum() < 100 → None`; `dist[i0] > 5 → None`);
  `pipeline/process_modis.py:578-579` (`if _rec is None: return None`).
- **Que pasa**: si el volcan esta en el granulo para K (ROI de `radius_km`) pero la via dice «fuera» (menos de 100
  pixeles a 45 km, o el pixel mas cercano al centro de la grilla a mas de 5 km), no hay record, no corre K y no queda
  marca. El probe del censo tampoco tenia el corte de 100 pixeles. En el censo: 144 «volcan_fuera_del_granulo», K publico
  0 en las 144, asi que el costo medido es cero; fuera de esa poblacion es SOSPECHA.
- **Reproducir**: `python experiments/_s164_modis_codigo/verificador/a6_censo_estados_y_pcc3933.py`.
- **Confianza 4 · Gravedad 1**.

### V164-05. «Bit a bit» del PR es «igual a 9 cifras significativas»
- **Archivo:linea**: `tests/test_mirova_modis_codigo_s164.py:285-293` (`_canon` → `arnes._redondear`),
  `tests/arnes_sintetico_s142.py:291` (`SIGNIFICATIVAS = 9`).
- **Que pasa**: la prueba del PR no detectaria una diferencia en la decima cifra. Este verificador la midio sin
  redondeo y no la hay (A1). Es el nombre, no el hecho.
- **Confianza 5 · Gravedad 1**.

---

## VERIFICADO LIMPIO (que y contra que vara)

| item | vara |
|---|---|
| Flag apagado: salida MODIS identica a 9 cifras y al `repr` exacto, 3 perfiles, 3 escenas | arnes S142 corrido sobre el arbol del tag base (`git archive`) y sobre HEAD |
| Golden `modis_k_antes.json` = salida del arbol base | regenerado y comparado en forma canonica |
| Via V750 identica entre tag base y HEAD (Etna OSF, 8 escenas oro MATLAB, 30 sinteticas, 11 grillas x 5 ROI, granulo sintetico) | modulo del tag base cargado aparte, `repr` exacto |
| Deteccion MODIS de la via = `port.fisica` del censo en 5.321 de 5.321 pasadas (pixeles y conteos por pase) | `ab_*.jsonl` + `grilla_NNNN.npz` del censo en D: |
| VRP de la via = `hueco + f273a47a` en 108 de 109 alertas del censo | blob f273a47a del tag |
| Fixtures `grilla_*.npz` byte a byte = censo; `esperado.json` = censo + recalculo f273a47a | idem |
| Lascar 1611: 1,1123740911483764 MW (regla), 0,973082188789508 (port) | recalculo independiente |
| Constantes via = produccion = port (3,959; 11,03; 18,9 x 1e6 / 1e6; 1 km; 5 y 15 celdas) | lectura de `process_modis.py:75-87`, `mirova_port.py:34-41`, `grillas.json` |
| 3,959 um, 18,9 x A_pix con A_pix 1 km2, grilla 1 km / 50 km, ROI1 5 x 5 km: en el paper | `sp426_5.txt` l. 162-164, 176-177, 189-191, 374, 384 |
| Fallback `sin_grilla`/`sin_mxd03`/`geo_distinta` y exencion `is True` en 3 compuertas | lectura `process_modis.py:558-583,1668`; `store.py:357,362,401,455`; 88 passed |
| Clasificador de mutaciones no cuenta caidas como atrapadas; control de caida en orden | lectura `mutaciones.py:84-98`; re-corrida en copia LF |
| CI de #919 verde sobre `c4efdc78c` | `gh pr view 919 --json headRefOid,statusCheckRollup` |
| Cita `process_modis.py:1094` `_path_d_cap_active` de CLAUDE.md y del guard S131 | `sed -n 1094p` |
| Blobs del port del censo en el worktree = sellados (`8ec50e7b`, `96769a89`) | `git hash-object` |
| Worktree sin cambios fuera de la carpeta del verificador | `git status --short` |

## SIN DATO

- Lectura real de HDF (`leer_radiancia_modis`, `leer_geo_mxd03`) y una corrida de `calculate_vrp` con el flag encendido
  sobre un granulo real: `pyhdf` no esta en Windows. La igualdad con el probe del censo es por lectura de codigo y por la
  prueba del PR con un doble de `pyhdf.SD`.
- Cual relleno (NaN fuera de la envolvente como MATLAB, o vecino mas cercano) usa MIROVA en MODIS: no hay codigo de
  MODIS publicado; V164-01 solo mide que la via y el censo difieren en un caso.
- Las cifras heredadas del censo («8 errores contra 49», «M MEJORA», «191 de 191») no se re-midieron aqui: pertenecen
  a la fase anterior (verificador propio en `experiments/_s162_modis_paquete/censo/verificador/` de la rama s162).
- Efecto de la caja 15 x 15 contra «todo el marco» del paper: razonado desde el `.m` (mismos umbrales en BOX 0 y 1), no
  medido con una corrida con BOX 1 = todo.

## Instrumentos (todos en esta carpeta)

`CAMINOS.md` (+ `.sha256`) · `a1_bit_a_bit_crudo.py` → `a1_salidas/`, `golden_base_tag_modis.json`,
`golden_hoy_modis.json` · `a2_v750_base_vs_head.py` → `_salida.txt` · `a3_a8_censo.py` → `_salida.txt` ·
`a6_censo_estados_y_pcc3933.py` → `_salida.txt` · `diff_delaunay_via_vs_f273a47a.txt` · `mutaciones_extra.py` →
`_salida.txt` · `mutaciones_rerun_en_copia_salida.txt` · `pytest_tres_archivos_salida.txt` ·
`pytest_suite_completa_salida.txt` · `insumos/` (copias de solo lectura del tag s162-modd-tag: `probe_paquete.py`,
`m_con_regla_matlab.py`, `delaunay_perturbado.py` = `delaunay_perturbado_f273a47a.py`, `grillas.json`).
