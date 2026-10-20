# Verificador con contexto limpio: λ por banda en la vuelta a radiancia de MODIS (S157)

Fecha: 2026-10-20. Worktree verificado: `D:\vrp-trabajo\s157-lambda-b22` (rama `s157-lambda-b22`, commits
`a45028184` y `79e0a1c18` sobre el tag `pre-s157-lambda-b22` = `f101d7304`). No edité nada del repo ni corrí la
suite: los scripts del experimento los corrí desde copias en esta carpeta, con `python -B` (sin bytecode) y con
las salidas redirigidas; `git status --short` del worktree quedó vacío después de cada corrida.

Afirmación: «Con el detector K (enable_modis_b22_primary activo), la magnitud MODIS vuelve a radiancia con la
longitud de onda de la banda 21 aunque la temperatura de brillo venga de la banda 22; eso deja la magnitud
1,053 a 1,075 veces más baja que la radiancia medida; es un defecto respecto de Coppola 2016a; y el arreglo
detrás del flag enable_modis_mir_lambda_por_banda lo corrige sin mover nada con el flag apagado.»

## 0. Caminos por los que la afirmación podría estar mal (cobertura primero)

| # | Camino | Revisado en | Resultado |
|---|---|---|---|
| a | Física: ¿B21 y B22 reportan la misma radiancia y la ida y vuelta con λ distinta da otra radiancia? | cálculo Planck, §2 | se sostiene |
| b | Lectura del paper (qué λ, qué banda, exceso en radiancia o en temperatura) | `sp426.5.pdf` p. 3 y p. 8 renderizadas | se sostiene |
| c | El 18,9 podría estar calibrado contra NUESTRA radiancia con λ21 (entonces el "defecto" se compensaría) | `experiments/21_calibrate_k_viirs375_vs_osf.py`, `21_results.json` | no: sale de las columnas de MIROVA |
| d | Instrumento sin L1B: aproximación de n_eff, kernel local, magnitud focal | re-corrida + inversión exacta por píxel propia | se sostiene, con precisión en el extremo bajo |
| e | Pareo con MIROVA | re-corrida con consolidado más nuevo | reproduce idéntico |
| f | Identidad bit a bit con el flag apagado | re-corrida + lectura de las expresiones | se sostiene en el procesador |
| g | Sitios de Planck no listados en la traza | grep de `pipeline/`, `scripts/`, `frontend/`, `tests/` | ninguno nuevo en el pipeline; un test de texto que se rompe |
| h | Efectos del flag encendido sobre decisiones que dependen de la magnitud | node con el predicado del tablero, modo de un píxel, D9, ranking | sin cambios de publicación hoy; el caso borde es calculable |
| i | Regla de origen de banda en la saturación de B22 | `merge_mir_bands` vs `lambda_mir_por_pixel` | coincide salvo radiancia negativa (irrelevante para la magnitud) |
| j | ¿El defecto existía también bajo C0? | lectura de `merge_mir_bands` | sólo en los píxeles de respaldo B22, población mínima |

## 1. Veredicto por parte

| Parte | Veredicto |
|---|---|
| 1. Con K la magnitud vuelve con λ de B21 aunque la BT venga de B22 | **CONFIRMADO** |
| 2. La magnitud queda 1,053 a 1,075 veces más baja que la de la radiancia medida | **CONFIRMADO** con precisión: exacto por píxel da 1,051 a 1,075 (mediana 1,0575, n = 24) |
| 3. Es un defecto respecto de Coppola 2016a | **CONFIRMADO** |
| 4. El arreglo detrás del flag lo corrige | **CONFIRMADO** en los sitios que corren en producción; **PARCIAL** en el camino del Test 1 (apagado) |
| 5. Sin mover nada con el flag apagado | **CONFIRMADO** para el procesador; **pero la rama rompe un test de la suite** (hallazgo H1) |

## 2. Hallazgos con evidencia

**H1 (importante, nadie lo pidió). La rama hace caer `tests/test_fondo_persistido_s140.py::test_record_guarda_fondo_en_la_banda_del_delta_L[pipeline/process_modis.py]`.**
El test exige por regex `"diag_L_bg_w_m2_sr_um": redondear_diag(radiancia_planck(t_bg, BAND21_LAMBDA))`
(`tests/test_fondo_persistido_s140.py:50-59`). La rama cambió esa línea a `radiancia_planck(t_bg, _lam_bg)`
(`pipeline/process_modis.py:1577`). Evaluado el mismo regex con Python sobre los dos archivos: rama `False`,
tag `True`. El diff no toca ese test (`git diff --stat` no lo lista). Lo correcto es actualizar el test (el
nombre del test, «en la banda del delta_L», es justo lo que `_lam_bg` respeta), no revertir el código. La
corrida de la suite en curso debería mostrarlo como falla; no es preexistente (A50). No lo corrí con pytest
para no escribir en el árbol: lo comprobé evaluando el regex.

**H2. El paper respalda la parte 3** (renderizado a 180 dpi, por columnas, `p3_L.png`, `p3_R.png`, `p8_R.png`,
`p5_L.png` en esta carpeta). p. 3 col. izq., lista (iv) y (v): banda 21 «centred at 3.959 µm (low-gain MIR
channel)» y banda 22 «centred at 3.959 µm (high-gain MIR channel)». p. 3 col. der., 3.er párrafo: «a corrected
spectral band centred at 3.959 µm (hereby called band L21ok), by using the L21 or L22 radiance, depending on
band 22 saturation». p. 8 col. der.: Ec. 6, ΔL4PIX = L4alert − L4bk en «4 µm radiance», L4bk «arithmetic mean
of all the pixels surrounding», y Ec. 7, RP = 18.9 × A × ΔL. El exceso es en radiancia, sin pasar por
temperatura. Nuestro `BAND21_LAMBDA = 3.929` (`process_modis.py:75`) es el borde inferior de la ventana.
Nota de lectura: p. 3 col. izq. también dice que se eliminan los DN > 32 768 «with the exception of the pixels
with DN = 65 533»; nuestro `calibrate()` (`process_modis.py:253-257`) deja NaN todos, y el NaN hace de marca de
saturación. Es consistente con la regla de respaldo, no afecta la afirmación.

**H3. El 18,9 no depende de nuestra λ (camino c).** `experiments/21_calibrate_k_viirs375_vs_osf.py:75-77`:
`delta = Tot_Lmir_hot − Tot_Lmir_bk`, `coef_emp = VRP / delta`, sobre `VRP_GLOBAL_ARCHIVE_2025.csv` (columnas
leídas: no trae ninguna temperatura, sólo radiancias de MIROVA). `21_results.json`: MODIS n = 13.157, mediana
18.900.000, error 1,97·10⁻¹⁴ %. El coeficiente multiplica la radiancia de MIROVA, no la nuestra, así que el
arreglo no descalibra nada.

**H4. Traza de `bt_mir` y de los sitios (parte 1).** En el tag: `bt21 = radiance_to_bt(rad21, BAND21_LAMBDA)`,
`bt22 = radiance_to_bt(rad22, BAND22_LAMBDA)`, `bt_mir = merge_mir_bands(bt21, bt22, ENABLE_MODIS_B22_PRIMARY)`
(l. 552-554), con `merge_mir_bands` devolviendo B22 donde no es NaN si `b22_primary` (l. 323-340). Todos los
sitios de vuelta a radiancia usaban `BAND21_LAMBDA` en el tag: l. 746, 773, 857, 1036, 1040, 1062, 1155,
1253-1254, 1367, 1377, 1392, 1528 (grep sobre `git show pre-s157-lambda-b22:pipeline/process_modis.py`),
idénticos a la tabla del README §4. Perfil efectivo leído de `pipeline.profile`: `ENABLE_MODIS_B22_PRIMARY
True`, `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA False`, `ENABLE_LOCAL_KERNEL_BG True`, `ENABLE_FOCAL_CLUSTER_MAGNITUDE
True`, `ENABLE_SINGLE_PIXEL_SUB_MW_MODE True`, `ENABLE_TEST1_PATH False`, `ENABLE_VENT_PATH_MODIS False`,
`ENABLE_LOCAL_CLUSTER_MAGNITUDE False`, `ENABLE_UTM_REGRID False`.

**H5. Sitios no listados (camino g): ninguno en el pipeline.** `vrp_regimes.neighbor_mean_radiance_background`
y `compute_vrp_lava_lake_eq16` no los importa `process_modis.py` (import l. 55-61); `bt_to_radiance` está
definida y no se llama; `vrptir.py` no la usa MODIS; el tablero no reconvierte radiancia en MODIS
(`f5CoreMagnitude` es sólo I-band, `frontend/index.html:1298-1305`). Fuera del pipeline sólo
`scripts/descomponer_magnitud_osf.py:57`, que el README ya anota. El NTI observado usa radiancia
(`rad_mir_for_nti`, l. 609-612), no BT: no tiene el defecto. El `NTI_app` (sitio 10) queda fuera a propósito y
lo acepto como SIN MEDIR.

**H6. Re-corrida del instrumento (parte 2).** `medir_efecto_lambda.py` (copia con salida redirigida a
`rerun\`): controles A 743 records, error rel. máx 3,67·10⁻⁴; B 23 píxeles, mediana 3,5·10⁻⁴, p95 2,7·10⁻³;
C 1,68·10⁻¹⁴. F: n = 24, mín 1,0527, mediana 1,0575, máx 1,0753; 1 topado D9; 0 píxeles B21. Contra MIROVA
n = 12, mediana 0,3624 a 0,3818, |log| 1,0757 a 1,0236; Chillán 11 (0,2397 a 0,2526), Láscar 1 (0,4875 a
0,5168). Idéntico al README aun con un consolidado más nuevo (`b8d5be37` contra `d742f26a`).
El script informa también `n_kernel_local = 10` de 24, dato que el README no menciona.

**H7. Inversión exacta por píxel (propia, camino d y punto 5).** `f_por_pixel.py`: para cada píxel de
`anomaly_pixels` (que guarda `bt_k` y su `vrp_mw`) despejo el fondo efectivamente restado,
L_bg,i = Planck21(bt) − vrp·10⁶/(18,9·10⁶), que vale también con kernel local (es el fondo por píxel), y
F_i = (Planck22(bt) − Planck22(T_bk,i)) / (Planck21(bt) − L_bg,i). Sin suponer n_eff ni fondo:
F del píxel pico mín **1,0514**, mediana **1,0575**, máx **1,0753**; F ponderado por VRP mín 1,0520, máx
1,0753; rango de todos los píxeles 1,0514 a 1,0753. El extremo bajo (Chillán 2026-10-16 01:40, 9,25 MW, dos
píxeles fuera del modo de un píxel) es 1,051 a 1,052, no 1,053: la aproximación del script con n_eff = n_pixels
lo sobreestima 0,001 (su propio `F_si_n_eff_1` da 1,0501). En los 10 records con kernel local (PCC,
Villarrica, Planchón) la inversión exacta coincide con la del script a 4 decimales en los de un píxel. Con
magnitud focal la suma es sobre un subconjunto, pero F_i varía menos de 0,003 dentro de un record, así que la
aproximación es válida.

**H8. Identidad con el flag apagado (parte 5).** Re-corrida de `identidad_flag_apagado.py` (copia, `-B`):
«48 de 48 combinaciones idénticas», «control 24 de 24 distintas», cobertura 6/6/6, salida 0. Lectura del
código: con el flag apagado `lambda_mir_por_pixel` devuelve el escalar `BAND21_LAMBDA`, `lambda_en` lo devuelve
tal cual, `lambda_grid=None` y `_lam_bg = BAND21_LAMBDA`: las expresiones son textualmente las del tag con el
mismo float de Python, así que la igualdad es exacta, no sólo tras el redondeo. Límite: el script compara el
record serializado (ya redondeado a 3 y 4 decimales), y no cubre los sitios 6 a 8 (Test 1 apagado), cosa que el
README declara; por lectura esos sitios también quedan idénticos.

**H9. Efectos del flag encendido (camino h, punto 7).**
(a) Publicación: el README dice que no cambia porque `isValidDetection` es `pc.vrp_mw > 0`. La razón está
incompleta: el predicado del tablero también tiene umbrales de magnitud en los filtros de artefacto
(`isCirrusArtifact` > 10 MW con t_max < 273,15 K, `isDiffuseFieldArtifact` ≥ 50 MW,
`frontend/index.html:1336-1356`). Lo medí con el predicado ejecutado en node (`pub_con_flag.py`, A97) sobre los
743 records MODIS con K, escalando la magnitud: con F = 1,05, 1,0753 y 1,20, **0 cambios** (21 publicados, 0
artefactos); control positivo con F = 100: 5 cambios (el instrumento ve). La conclusión del README se sostiene
para el corpus de hoy; la razón no es general.
(b) Ranking del píxel pico (`hotspot_*`, `final_hotspot`, `keep_peak`): con fondo escalar y área uniforme el VRP
por píxel es monótono en bt con cualquier λ; con kernel local podría reordenarse. Medido (`swap_top.py`): 11
records con 2 o más píxeles de VRP > 0, **0 cambios de pico**. La selección de cúmulo `vent_anchored` sólo usa el
signo del VRP y el VRP como desempate (`clustering.py:143-154`), y el signo no cambia (misma λ en píxel y fondo).
(c) El caso borde del README §8 es **calculable**, no desconocido: Chillán 2026-10-01 01:45 tiene el segundo
píxel del cúmulo con bt 266,93 K bajo t_bg 271,72 K, o sea VRP 0 con cualquier λ. Con el flag la suma pasa a
4,8043 × 1,0541 = **5,064 MW**, cruza el umbral de 5 MW (`single_pixel_mode.py`, compara la suma), sale del modo
de un píxel y publica 5,064; el tope D9 no actúa porque t_bg 271,72 ≥ 270 K (`PATH_D_ONLY_CAP_TBG_MAX_K`). El
cambio es exactamente F (5,4 %), no «mayor que el 5 %»; lo que sí cambia es la etiqueta `single_pixel_mode`.

**H10. Arreglo incompleto en el camino del Test 1 (parte 4, PARCIAL).** Con el flag encendido
`compute_test1_mir(..., lambda_um=_lam_bg)` (`process_modis.py:790`) usa λ22 escalar para TODOS los píxeles,
incluidos los de respaldo B21 (B22 saturada), cuya BT salió con λ21. Para un píxel a 420 K eso da una
radiancia 1,028 veces mayor que la medida (cálculo Planck propio). El README lo rotula «λ primaria, escalar»
sin decir que en esos píxeles queda mal. Hoy no decide nada (`ENABLE_TEST1_PATH False`).

**H11. Regla de origen de banda (camino i).** `lambda_mir_por_pixel` decide con `np.isnan(rad22)` y
`merge_mir_bands` decide con `np.isnan(bt22)`. Difieren sólo si rad22 < 0: `radiance_to_bt` da NaN con
radiancia −0,001 y 0 K con radiancia 0 (comprobado). Ahí la BT sale de B21 y la λ dice B22. Es un píxel
gélido que nunca es caliente ni entra al fondo (máscara de nube), así que no afecta la magnitud; el docstring
dice «misma regla» y es casi la misma.

**H12. Matices de la física (caminos a y j).** A igual temperatura L22/L21 vale 1,086 a 230 K, 1,067 a 270 K,
1,059 a 290 K y 1,028 a 420 K, y la BT con λ21 de la misma radiancia queda 1,2 a 1,4 K más alta que con λ22
(cálculo propio). Dos consecuencias que el README no dice: (1) bajo C0 el defecto «no existía» salvo en los
píxeles de respaldo B22 (donde B21 es NaN), población que no medí pero mínima; (2) con K, todo píxel que cae a
B21 por cualquier DN inválido de B22 (no sólo saturación, porque `calibrate()` deja NaN todo DN > 32 767)
entra a `bt_mir` con un escalón de ~1,3 K respecto de sus vecinos de B22, lo que toca σ y umbrales en kelvin. Es
el punto §6.2 del README («sólo afecta los píxeles que saturan B22») con una población más amplia. Sin L1B no
se puede contar cuántos son: SIN MEDIR.

**H13. Procedimiento.** `medir_efecto_lambda.py` escribe sus salidas junto al script (`AQUI`) aunque se le pase
`--dest`; `--dest` sólo recibe las descargas. Re-correrlo tal como está sobrescribe las salidas commiteadas.
Por eso lo corrí desde una copia.

## 3. Lo que no pude comprobar

- El número de píxeles MODIS con B22 inválida no saturada (H12) y el efecto del `NTI_app` (sitio 10): necesitan
  L1B (pyhdf no corre en Windows).
- La λ efectiva de las funciones de respuesta espectral reales de B21 y B22 (el paper da 3,959 para las dos; no
  verifiqué contra el documento de MCST).
- El Coppola 2025 cap. 11 sólo está en `.txt`; no lo usé.
- No corrí pytest (para no escribir en el árbol): H1 sale de evaluar el regex del test, no de la suite.

## 4. Archivos de esta verificación

`D:\vrp-trabajo\temporales\s157-lambda\verificador\`: `p3_L.png`, `p3_R.png`, `p5_L.png`, `p8_L.png`,
`p8_R.png`; `medir_copia.py` y `rerun\medir_efecto_lambda_salida.{json,txt}`; `identidad_copia.py`;
`f_por_pixel.py` y `f_por_pixel.json`; `swap_top.py`; `pub_con_flag.py`; `ref\` (descargas de Mirova-v1).
