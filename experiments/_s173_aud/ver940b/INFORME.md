# Verificación limpia, segunda ronda, del PR #940 (arreglos del primer verificador)

Verificador: Fable 5.1, contexto limpio (no escribí el código ni los arreglos). Hora del servidor de GitHub al
empezar: 2026-11-03 23:23:52 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`). Esfuerzo: alto.

- Regla sellada: tag `s173-prereg-retro-sellado` (objeto `26c970564`, commit `aa2a63079`, 2026-11-02 17:12 UTC);
  blob del pre-registro `9c58997a3`, igual en `origin/loop/activo` `526c69f58`; sha256 LF
  `b58a225404c80ae0929b5096d30eea2d36c33cea09979427123f291f3c153c91`; copia en `prereg_sellado.md` (749 líneas).
- PR #940, rama `claude/s173-retro-paquete`, punta `dbaa4085c` (borrador; check `pytest` IN_PROGRESS al empezar).
  Diff nuevo verificado: `6e93764bf..dbaa4085c`, 7 commits, 6 archivos, +424/−42 (`diff_nuevo.patch`, 705 líneas).
- Worktree propio `C:/Users/nmend/vrp-wt/ver940b` (detached en la punta). Sólo lectura del repo: no comenté, no
  pusheé, no despaché, no toqué `pipeline/`, `data/` ni `frontend/`, sin `git stash`. Lo que escribí está sólo en
  `experiments/_s173_aud/ver940b/` de ese worktree.
- Disco al empezar: C: 19,6 GB libres, D: 4,2 GB libres (`df -h`).

## Veredicto

**MERGEABLE CON CAMBIOS** (los cambios son de gravedad 1 salvo uno de gravedad 2 que solo informa). Ocho de los nueve arreglos hacen lo que el hallazgo pedia, cada uno con una prueba que lo vigila y una mutacion que lo pone en rojo (23 de 23 del PR y 6 de 7 mias atrapadas por asercion; suite 3.161 en verde). El noveno, VPR940-11, esta implementado segun la letra del §7 pero el instrumento no puede variar: con K contra K la prueba de signos tiene B = 0 y da SIN SUSTRATO siempre, y mi mutacion que lo deja constante sobrevive (VPR940b-01). Como solo informa, no bloquea el merge; si cambia una lectura del texto sellado, la decide Nicolas. El diff nuevo no introduce defectos de gravedad 2 o mas; VPR940-01, 07 y 10 quedan bien presentados como pendientes.

## 1. Cobertura: archivos del diff nuevo y hallazgos de la lista

| archivo tocado por el diff nuevo | líneas (+/−) | leído entero |
|---|---|---|
| `experiments/_s172_retro_paquete/leer_retro.py` (1.184 líneas) | +158/−17 | SÍ (l. 1 a 1184) |
| `experiments/_s172_retro_paquete/controles_via.py` (101) | +13/−9 | SÍ |
| `experiments/_s172_retro_paquete/mutar_leer_retro.py` (150) | +44/−10 | SÍ |
| `experiments/_s172_retro_paquete/mutar_leer_retro_salida.txt` | +29 | SÍ (el diff) |
| `tests/test_leer_retro_s172.py` (674) | +167/−1 | SÍ (l. 1 a 674) |
| `tests/test_retro_paquete_workflow_s172.py` (218) | +15/−3 | SÍ |

Además leí, sin que el diff los toque: `.github/workflows/reproc-retro-paquete.yml` l. 60 a 170 (pasos de reproceso,
C-via y artifacts), `reglas/evaluar_f4.py` l. 126 a 141 (`escalar`) y 255 a 294 (`p2`, `pares_m`),
`scripts/banco_paridad.py` l. 143 a 175 y el `_JS` del predicado, `frontend/index.html` l. 1169 a 1182, 1314 a 1365
y 1595 a 1620 (tope de 50.000 MW, filtros de artefacto a 273,15 y 278,15 K, `isValidDetection`),
`experiments/_s162_v750a/PREREGISTRO_V750A.md` en `aa5583646` l. 255 y 305 (L7), el pre-registro sellado §5, §6,
§7, §10.3 y §11, y el informe y el CSV del primer verificador (`experiments/_s173_aud/ver940/` en `loop/activo`).

| hallazgo | qué pedía | dónde está el arreglo | estado |
|---|---|---|---|
| VPR940-02 (3) | K de disco con la marca de la vía es rojo en todas las ventanas | `armar_pasadas` l. 245 a 248; `c_k_puro` l. 542 a 547; comunes l. 1160 | CONFIRMADO |
| VPR940-03 (2) | C-K comprueba la cobertura del K-gemelo que manda D3 | `cobertura_kgemelo` l. 550 a 570; `c_k` l. 590 a 595 | CONFIRMADO |
| VPR940-04 (2) | el nulo de runner descuenta las nombradas | `_nombradas` l. 598; `nulo_runner` l. 605 a 606 | CONFIRMADO |
| VPR940-05 (2) | el placebo mira P1 y P2 salvo causas de L7 | `c_placebo` l. 627 a 640; constantes l. 121 a 122 | CONFIRMADO |
| VPR940-06 (2) | C-montaje validado | `validar_montaje` l. 697 a 722; comunes l. 1162 | CONFIRMADO |
| VPR940-08 (2) | sensor vacío no deja rojo el trozo | `controles_via.py` l. 72 a 76 y 88 a 94 | CONFIRMADO |
| VPR940-09 (2) | C-cobertura en R25 por clase del OSF | `c_cobertura` l. 521 a 528; `leer_sensor` l. 1059 a 1061 | CONFIRMADO |
| VPR940-11 (2) | sorteo de etiquetas por estrato (§7) | `barajar_en_estratos` l. 913 a 929; `sorteo_etiquetas` l. 932 a 946; l. 1081 | EN PARTE (VPR940b-01) |
| VPR940-15 (1) | ENSAYO en cada línea | `main` l. 1173 a 1174 | CONFIRMADO |
| VPR940-01, 07, 10 | esperan a Nicolás | sin tocar (`regla_v750` l. 477 a 478, `regla_v375` l. 458, `leer_sensor` l. 1070) | presentados bien como pendientes |

## 2. Cada arreglo contra el texto sellado

Leyenda: CONFIRMADO hace lo que el hallazgo pedía y lo vigila una prueba que una mutación pone en rojo; EN PARTE
está implementado pero no cumple el fin del texto sellado; REFUTADO no hace lo que dice.

**VPR940-02, CONFIRMADO.** `armar_pasadas` l. 245 a 248 pone `estado = "k_con_marca:True"` cuando el record de K
trae `via_codigo_mirova is True`, antes de mirar si la vía tiene pasada (así la fila no se cuenta como SIN DATO ni
como evaluable, `tabla_publica` l. 337); `c_k_puro` l. 542 a 547 queda ROJO con un solo record y entra a los
controles comunes (l. 1160), que `veredicto()` l. 1008 a 1010 lleva a la fila 1 en los tres sensores, R25
incluida. Prueba: `test_k_de_disco_con_la_marca_de_la_via_es_rojo_en_todas_las_ventanas` (tres fechas, F26, R25 y
DM; y que `None`, `False` y `"sin_grilla"` NO marcan) y `test_k_puro_en_rojo_lleva_el_sensor_a_la_fila_1`.
Mutaciones N02a y N02b ATRAPADAS en mi corrida. Lo que se escribe en producción es `True` (bool) cuando la vía
corre (`pipeline/mirova_v750_codigo.py:704`, `process_modis.py:1767` con `_via_marca`) y `"sin_grilla"` o
`"sin_mxd03"` cuando vuelve a K: el `is True` atrapa el caso que importa; el caso «K escrito por producción con la
vía encendida pero caída a K» pasa como K puro (VPR940b-04, gravedad 1, lo decide Nicolás).

**VPR940-03, CONFIRMADO.** `cobertura_kgemelo` l. 550 a 570 exige, sobre las filas con `k_rec` (incluidas las SIN
DATO de la vía): que haya pasadas de K en DM y todas estén en el K-gemelo; todas las de F26 (F26-V, F26-M y
F26-M3) de Láscar y Nevados de Chillán; y en cada otro volcán con F26, al menos 3 noches UTC con TODAS sus
pasadas (los tres sensores) en el K-gemelo. Es lo que manda D3 (§10.3: «DM entero; Láscar y Chillán en F26
enteros; tres días de F26 de cada uno de los otros 9»), y coincide con la ventana D3 que `plan_trozos` arma en
`test_los_conteos_de_jobs_son_los_del_preregistro` (02-24, 03-02, 03-20 por volcán). `c_k` l. 590 a 593 lo suma a su
estado. Prueba `test_c_k_exige_la_cobertura_del_k_gemelo_de_d3` (una pasada sola, DM de Isluga, F26 de Láscar e
Isluga con 2 días); mutaciones N03a, N03b y mi P03 (quitar la exigencia de DM) ATRAPADAS. Límite anotado
(VPR940b-07): un volcán sin ninguna pasada de K en F26 se salta sin aviso.

**VPR940-04, CONFIRMADO.** `nulo_runner` l. 605 a 606 saca de `con` las pasadas nombradas (`_nombradas`: vol,
dt[:16], y sólo si traen el empate de `argsort` escrito), y sobre el resto exige B = 0 y que el nulo pueda fallar
contra PLACEBO. El tope de 3 por sensor no lo mira el nulo, lo mira `c_k` l. 588 (`excede`), y los dos son
controles comunes: con 4 excepciones el sensor cae por C-K. Prueba `test_nulo_runner_descuenta_las_excepciones_nombradas`
(ROJO con una diferencia; OK nombrada con empate; ROJO nombrada sin empate); mutaciones N04 y mi P04 (descontar sin
exigir el empate) ATRAPADAS.

**VPR940-05, CONFIRMADO.** `c_placebo` l. 627 a 640 recorre las filas evaluables de las tres clases que deciden
(protegida, bajo1, neg_limpio) y toma como discordancia toda pasada donde el tablero publica distinto para K y
para K × 1,2; la explica sólo por las dos causas de L7 de V750-A §7 (`aa5583646` l. 305): `t_max_k` del record de K
bajo 278,15 K, o la magnitud mostrada de K que cruza el tope de 50.000 MW al escalarla. Comprobé contra
`frontend/index.html` que esos son los sitios del predicado que miran la magnitud: los filtros de artefacto
(`isCirrusArtifact` l. 1338, `t_max_k < 273.15` y `eq > 10`; `isDiffuseFieldArtifact` l. 1358, `t_max_k <
278.15`, `eq >= 50`, `eq/npx < 1`) y el tope (`> 50000 ? 0` en l. 1171, 1182 y 1314), y que el predicado de
`banco_paridad._JS` los incluye (`isThermalArtifact` y `disp > 0`); `escalar` (`evaluar_f4.py:128-141`) multiplica
también `f5_core_vrp_mw`, así que VIIRS 375 no queda fuera. Es más estricto que el texto (no pasa por `F4.p2`
sino por cada pasada, VPR940b-11, informa), no más laxo. Prueba `test_placebo_mira_p1_y_p2_y_acepta_solo_las_dos_causas_de_l7`
(negativo con t_max 300 ROJO, con 275 OK, con 45.000 MW OK, protegida ROJO); mutaciones N05, mi P05a (todo
explicado por t_max) y mi P05b (sin mirar protegidas) ATRAPADAS.

**VPR940-06, CONFIRMADO en lo que pedía el hallazgo.** `validar_montaje` l. 697 a 722 exige `estado` OK, `tags`
(lista no vacía de strings), `diff_listado` no vacío, `diferencias` lista, y cada diferencia con `explicada_por`
igual a `hunk` con el hunk escrito o a `otro_granulo`; `main` l. 1162 ya no acepta el JSON tal cual. Prueba
`test_c_montaje_se_valida_y_no_basta_un_estado_ok`; mutaciones N06 y mi P06 (hunk vacío) ATRAPADAS. Sigue sin
construirse C-montaje (lo dice el PR) y no se comprueba qué tags ni qué pasadas (VPR940b-06, gravedad 1).

**VPR940-08, CONFIRMADO.** `controles_via.py` l. 72 a 76: un sensor con 0 records ya no sube el código a 4; escribe
`::warning::` y la línea `SENSOR_VACIO <sensor>`; el trozo sin ningún record sigue en 4 (l. 66 a 67). El flag
`--permitir-sensor-vacio` desapareció. El workflow no cambió y no necesita cambiar: el paso de C-via (l. 129 a 134)
hace `tee controles_via.txt` (la línea viaja en el artifact del log, l. 144 a 151) y «Guardar el trozo» (l. 153 a
160) corre sólo si el paso salió 0, que ahora es el caso con un sensor vacío. En la lectura, esas pasadas de K sin
vía quedan `sin_dato_cobertura` y cuentan para el 10 % por clase (`c_cobertura`), como dice el §6. Prueba
`test_cvia_rojo_con_trozo_vacio_y_aviso_con_sensor_vacio`; mutación N08 ATRAPADA (la batería del workflow ahora
carga la copia mutada por `CONTROLES_VIA_MODULO`, l. 31 a 35). `run_pipeline.py` sólo devuelve 3 por búsquedas
caídas con `--estricto-cobertura` (l. 447, 505, 528), no por un sensor sin records, así que el paso no se pone rojo por
otro camino.

**VPR940-09, CONFIRMADO.** `c_cobertura` l. 521 a 528 recibe la clave y las clases; `leer_sensor` l. 1059 a 1061
la llama sobre las filas de R25 del sensor con `clave="lab_osf"` y la única clase que decide en R25
(`protegida_osf`, la que `p1_osf` l. 812 pone sobre la pasada pareada, también si es SIN DATO). Prueba
`test_c_cobertura_en_r25_por_clase_del_osf` (2 de 10 SIN DATO: ROJO y fila 1 con el motivo); mutaciones N09 y mi
P09 (clase de la tabla en vez de la del OSF) ATRAPADAS. Sólo existe con `--osf` (VPR940b-08, gravedad 1).

**VPR940-11, EN PARTE.** `barajar_en_estratos` l. 913 a 929 permuta `lab`, `vrp_mirova` y `lab_union` dentro de
cada estrato volcán × tramo de 10° de cenit (la prueba comprueba que los multiconjuntos por estrato se conservan y
que algo cambia; N11, que baraja entre estratos, ATRAPADA). Pero `sorteo_etiquetas` l. 932 a 946 corre `F4.p2`
con los brazos `("K", "K")`, o `("KG", "K")` si el K-gemelo cubre todas las evaluables. Con dos brazos iguales
`contribuciones()` (`evaluar_f4.py:261-277`) es vacía, B = 0 y `regla_signos_p2` da SIN SUSTRATO por
construcción (`MAX_B_SIN_SUSTRATO_P2 = 4`): `gana_o_empate` es 0,0 pase lo que pase con las etiquetas. Medido en
`sorteo_degenerado_salida.txt`: cuatro poblaciones sintéticas y un K-gemelo idéntico a K dan `{'SIN SUSTRATO': 50}`
de 50; el mismo barajado con la vía contra K da `{'GANA': 50}`, que es la cifra que la GUIA §3b fila 7 pide («qué
cumple el azar»). Y mi mutación P11b (devolver SIN SUSTRATO sin calcular nada) SOBREVIVE a la batería. Es un
informe que no puede variar (A116) y la prueba no exige que pueda. El código sigue la letra del §7 («sobre K
contra K»); lo que no sirve es el fin. Decide Nicolás cómo leer el §7 (VPR940b-01, gravedad 2); no bloquea el
merge porque sólo informa.

**VPR940-15, CONFIRMADO.** `main` l. 1173 a 1174 antepone `ENSAYO (NO DECIDE) ` a cada línea de veredicto con
`--ensayo`; prueba en `test_main_de_punta_a_punta_con_predicado_sintetico` (las 3 líneas); mutación N15 ATRAPADA.

**VPR940-01, 07 y 10.** No se tocaron, y el cuerpo del PR (sección «Espera decisión de Nicolás (no se tocaron)»,
`pr_body_pendientes.txt`) los presenta bien como pendientes, con la pregunta de cada uno. La cabecera del lector
l. 46 a 51 dice lo mismo. No los juzgo como defectos.

## 3. Suite y mutaciones, corridas por mí

**Suite completa** (`python -m pytest tests -q -p no:cacheprovider`, salida en `pytest_suite_salida.txt`, 2026-11-04 01:10 a 01:20 UTC, HEAD `dbaa4085c`, arbol quieto, sin ninguna edicion durante la corrida, A112): **3.161 pasan, 32 saltadas, 2 xfail, 0 fallan**, 531 s. Reproduce exacto lo que declara el PR. El check `pytest` del PR en GitHub paso a COMPLETED SUCCESS durante mi lectura.

**Mutaciones del PR** (`python experiments/_s172_retro_paquete/mutar_leer_retro.py`, salida en
`mutar_salida_ver940b.txt`, 2026-11-03 23:21 a 2026-11-04 00:45 UTC, árbol quieto, `git status` limpio al terminar y
sin copias `_mut_*`): **23 de 23 mutaciones reales ATRAPADAS por aserción**, el control de caída sale **CAE**
(`resumen: {'ATRAPADA': 23, 'CAE': 1}`). Reproduce `mutar_leer_retro_salida.txt` ronda 3 del PR, prueba por prueba.
Cada ATRAPADA lleva al menos una prueba que falla con `AssertionError`; el clasificador (l. 121) no cuenta las
excepciones como atrapadas. Lo que no puedo decir: si alguna de las 11 nuevas además hace caer otras pruebas, porque
la salida ATRAPADA calla las caídas (VPR940b-12, SIN VERIFICAR).

**Mutaciones propias** (`mutaciones_propias.py`, salida en `mutaciones_propias_salida.txt`, 00:45 a 01:10 UTC, mismo
clasificador): **6 de 7 ATRAPADAS, 1 SOBREVIVE**.

| mutación | arreglo | resultado |
|---|---|---|
| P05a toda discordancia del placebo queda explicada por t_max | 05 | ATRAPADA |
| P05b el placebo no mira las protegidas (P1) | 05 | ATRAPADA |
| P03 C-K no exige DM entero en el K-gemelo | 03 | ATRAPADA |
| P09 C-cobertura de R25 con la clase de la tabla, no la del OSF | 09 | ATRAPADA |
| P04 el nulo descuenta nombradas sin el empate escrito | 04 | ATRAPADA |
| P11b el sorteo devuelve SIN SUSTRATO sin calcular P2 | 11 | **SOBREVIVE** (VPR940b-01) |
| P06 C-montaje acepta un hunk vacío | 06 | ATRAPADA |

## 4. Hallazgos nuevos

Están todos en `hallazgos.csv` (gravedad 1 a 4, confianza, archivo:línea, reproducción). Los de gravedad 2 o más:

**VPR940b-01 (2, confianza alta). El sorteo de etiquetas del §7 no puede variar.** Detalle en §2 (VPR940-11) y en
`sorteo_degenerado_salida.txt`. No decide nada, así que no cambia un veredicto; pero el §7 lo pone «antes de leer»
como medida de poder y hoy mide una constante. Arreglo posible, que decide Nicolás por ser lectura del texto
sellado: barajar las etiquetas y correr la vía contra K (la fracción de barajados con GANA o EMPATE es el «azar»
que la GUIA pide), rotulado post hoc; y una prueba que exija que el instrumento pueda dar GANA.

Los demás (VPR940b-02 a 12) son de gravedad 1: duplicación de `_nombradas`, KeyError con una excepción de C-K mal
formada (reproducido en `vpr940b_03_keyerror_salida.txt`), el `is True` que deja pasar «sin_grilla» en K, la ruta local
del informe en la cabecera, la validación mínima de C-montaje, volcanes sin F26 que `cobertura_kgemelo` no acusa,
R25 sin control sin `--osf`, el rojo por sensor sin R25 (no es nuevo), las nombradas fuera del control «puede
fallar», el placebo más estricto que el texto, y el clasificador de mutaciones que calla las caídas.

**Defectos nuevos introducidos por el diff:** ninguno de gravedad 2 o más encontré. El diff no toca `pipeline/`,
`data/` ni `frontend/` (`git diff --stat 6e93764bf..dbaa4085c`: sólo los 6 archivos de la tabla).

## 5. Lo que NO pude comprobar (SIN VERIFICAR)

- Si alguna de las 11 mutaciones nuevas, además de la aserción, hace caer otras pruebas (el clasificador lo calla).
- Que producción escriba hoy records con `via_codigo_mirova: True` en `data/mirova_equivalent/` (no leí datos reales;
  el `is True` lo verifiqué contra el código del pipeline, no contra el corpus).
- El comportamiento del workflow en el runner con un sensor vacío (no se despachó nada; la lectura es del yml).
- El §10.1 último punto y lo que el primer verificador dejó SIN VERIFICAR siguen igual: no era parte de este encargo.

## 6. Salidas guardadas

Todo en `C:/Users/nmend/vrp-wt/ver940b/experiments/_s173_aud/ver940b/`:
`INFORME.md`, `hallazgos.csv`, `prereg_sellado.md` (copia del tag), `diff_nuevo.patch`, `mutar_salida_ver940b.txt`
(batería del PR), `mutaciones_propias.py` y `mutaciones_propias_salida.txt`, `sorteo_degenerado.py` y
`sorteo_degenerado_salida.txt`, `vpr940b_03_keyerror_salida.txt`, `pr_body_pendientes.txt`, `pytest_suite_salida.txt`.
Python 3.12.10, pytest 9.0.3, node presente (la prueba del predicado real no se saltó en la batería).
