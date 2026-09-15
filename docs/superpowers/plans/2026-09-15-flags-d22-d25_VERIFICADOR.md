# Verificador del plan D22/D25 (VIIRS 375)

Plan verificado: `docs/superpowers/plans/2026-09-15-flags-d22-d25.md` sobre `main` en `f0020c7b20e5c790e4bd86dd94d27a96d6529103` (medido con `git rev-parse HEAD` al empezar y al terminar).

Veredicto: **EJECUTABLE CON CAMBIOS.** La mecánica del plan está bien: las 24 anclas de edición existen y son únicas, el código compila, los 113 tests del plan y de los guards vecinos pasan sobre una copia, y los valores esperados se reproducen. Lo que falla es el alcance de lo que se afirma y se prueba. El arnés nunca ejercita el camino del Test 1, que es por donde sale la mayoría de las detecciones V375 de producción. Además, D22 no queda aislada de ese camino.

## Cómo se verificó (instrumentos de esta sesión)

- `experiments/_s142_verif_plan_d22_d25/arnes_copia_del_plan.py`: el arnés de la Tarea 1 copiado tal cual desde el plan (sólo cambia `parents[2]`).
- `experiments/_s142_verif_plan_d22_d25/probe_d22_simulado.py`: simula D22 sin tocar `pipeline/`. Envuelve sólo los tres helpers contextuales con `bt_sanity_k=-inf`; los caminos B y C no se tocan.
- `experiments/_s142_verif_plan_d22_d25/aplicar_plan_en_copia.py`: copia `pipeline/` y `tests/` al scratchpad, genera el golden antes de editar y aplica **literalmente** los bloques de código del plan (con `count == 1` exigido en cada ancla). Después corre los tests del plan y cuatro mutaciones de control. El repo no se tocó: `git status` final muestra sólo este informe, la carpeta de scripts y los dos no rastreados previos.
- Páginas renderizadas con PyMuPDF a 200 dpi y miradas como imagen: `sp426.5.pdf` visor 6, 7 y 8; `s00445-024-01721-z.pdf` (Campus 2024) visor 3; `Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf` (Coppola et al. 2025, Remote Sens. 17, 1191, "Fernandina") visor 9.

## Qué dice el paper renderizado

**Test 1 (SP426.5, visor p. 6, columna izquierda, "Fixed NTI threshold").** Es `NTI_PIX > K1` y nada más, sin condición de temperatura. En la columna derecha agrega que los píxeles que lo cumplen se marcan activos y se descartan por no aptos para los pasos siguientes. La SOSPECHA del plan (§6, primer punto) queda **resuelta: el Test 1 tampoco tiene compuerta**. Por lo tanto `process_viirs.py:979` también es una divergencia literal. Dejarla fuera de D22 se justifica por alcance (D23), no porque el paper la tenga.

**Tests 2 y 3 (visor p. 7, columna izquierda).** `dNTI_PIX > C1 or dNTI_PIX > mu + C2 sigma` y lo mismo con dETI, unidos por "and". No hay condición de temperatura. Confirma D22.

**Fondo del VRP (visor p. 8, columna derecha, ec. 6).** "L4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)". No dice "no alertados", no dice cuántos vecinos y no menciona recorte a cero. El paréntesis admite una corona del cúmulo.

**Campus 2024 (Bull. Volcanol. 86:25, p. 3 de 7, columna derecha, bajo ec. 1 y ec. 2).** Cada píxel alertado tiene su propio fondo, "the arithmetic mean of the radiance of the pixels surrounding the alerted one(s)", y el fondo total es la suma: `L_MIRbk = Σ L_pixbk`. Es radiancia, no temperatura. No da tamaño de ventana ni dice qué hacer sin vecinos. En la misma columna, más arriba, dice que MIROVA remuestrea el gránulo a una grilla UTM regular de 50 x 50 km antes de detectar.

**Fernandina 2025 (Remote Sens. 17, 1191, p. 9 de 26, §2.3.1, ec. 3).** `ΔL_MIR = Σ L_MIRhot(i) − L_MIRbk`, con `L_MIRbk` "the averaged radiance of the surrounding, non-alerted pixels". La resta se hace sobre la suma, sin recorte por píxel. En el primer párrafo de la página dice que se remuestrea a una grilla UTM de 51 x 51 km centrada en la cumbre del GVP.

**Convención "impresa = visor + 180".** No la pude verificar: las páginas renderizadas de SP426.5 no muestran número de página impreso en la cabecera. Todas las citas de este informe usan la página del visor.

## Hallazgos (ordenados por gravedad)

### H1 · El arnés no ejercita el camino del Test 1, y ese camino produce la mayoría de las detecciones V375 · gravedad 4 · CONFIRMADO

- **Archivo:línea**: plan, Tarea 1 (`escena_v375`) y Tarea 2 (`test_perfil_operacional_reproduce_el_golden_bit_a_bit`); bloques D25 del Test 1 en `process_viirs.py:1861-1873` y `:1881-1902`.
- **Qué pasa**: en las seis escenas V375 del arnés, `final_hotspot_source` sale `ctx_cluster` o `None`; el Test 1 nunca gana la fuente (salida de `arnes_copia_del_plan.py`, resumida en `probe_d22_simulado.py`). La mutación **M3**, que con el flag OFF multiplica por 0,5 el fondo de **los dos** bloques del Test 1, **pasa** el test bit a bit (rc=0, "1 passed"). En producción, desde 2026-06-01, 2.211 de las 3.615 detecciones V375 llevan `final_hotspot_source = "test1_roi"`. Esa etiqueta se asigna cuando no hay cúmulo contextual y el Test 1 disparó (`anchor.py:85-89`). En ese caso la cascada interna fija la fuente en `"test1"` (`process_viirs.py:1730-1735`) y los bloques de `:1861` y `:1881` reconstruyen `anomaly_pixels`, que es lo que suma F5 (`f5_core.py:97-104`). Esta última cadena es una traza de lectura, no de ejecución.
- **Qué se mediría mal**: "apagado no cambia nada" queda probado sólo para la minoría contextual. Un error en los bloques del Test 1 con el flag OFF pasaría la suite y llegaría al cron NRT. Con el flag ON, D25 sobre el Test 1 (la rama que más importa en los nevados de señal débil) no tiene ningún caso de punta a punta, sólo guards de fuente. El plan lo admite en §6, pero no dice que esa rama es el 61 % de lo publicado.
- **Cómo reproducir**: `python experiments/_s142_verif_plan_d22_d25/aplicar_plan_en_copia.py <scratch>/copia` y buscar "MUTACION M3". El conteo sale de un `json.load` de `data/mirova_equivalent/*.json`, filtrando sensor V375 y `datetime_utc >= 2026-06-01` (script inline de esta sesión).
- **Cambio sugerido**: agregar una escena V375 donde el Test 1 dispare sin cúmulo contextual (lago de lava sub-píxel difuso en un disco de 3 km, con dNTI bajo C1), congelarla en el golden y verificar que M3 falla.

### H2 · D22 no queda aislada: su salida alimenta el filtro contextual del Test 1 (`keep_peak`, D19) y la elección de fuente · gravedad 4 · CONFIRMADO el mecanismo, SOSPECHA el tamaño

- **Archivo:línea**: `process_viirs.py:1034-1052` (salida `dnti_ctx_hot` y `n_dnti_ctx_path`); `:1696-1702` (`only_test1_source` exige `n_dnti_ctx_path == 0`); `:1788-1799` (`apply_contextual_test1_filter(test1_hot_filtered, dnti_ctx_hot, keep_peak_rc=...)`).
- **Qué pasa**: el plan apaga la compuerta en las dos llamadas del camino D. En producción ese camino no publica, porque `hot_mask_2d = fp_hot` lo pisa (`:1262`). Pero su máscara es la que decide qué píxeles del Test 1 sobreviven al filtro contextual, y su conteo entra en `only_test1_source`. En la escena principal, la simulación de D22 cambió `n_dnti_ctx_path` de 0 a 2 (`probe_d22_simulado.py`, "claves_distintas"). Allí no movió nada publicado sólo porque el Test 1 no dispara (H1). En producción, 1.590 de los 2.211 records `test1_roi` tienen `n_dnti_ctx_path == 0`: son la población donde encender D22 puede cambiar el filtro contextual. Con `keep_peak` OFF (brazos literales), un filtro vacío hoy borra el cúmulo del Test 1, y con D22 ON puede dejar de estar vacío.
- **Qué se mediría mal**: la afirmación "sola, D22 no devuelve alertas ni mueve la magnitud" (plan §0, docstring del test de la Tarea 6 y nota para el catálogo en la Tarea 8) se apoya en una escena que no toca esta rama. La ablación `lit_con_compuerta` medirá compuerta **más** filtro contextual del Test 1 **más** elección de fuente, atribuyéndolo todo a la compuerta. Es el modo de falla de S137/S138 (atribución sin el paso siguiente).
- **Cómo reproducir**: leer las tres zonas citadas; correr `probe_d22_simulado.py` y mirar `n_dnti_ctx_path`.
- **Cambio sugerido**: (a) quitar la frase "no cambia lo publicado" de la nota del catálogo, o acotarla a "en el camino contextual"; (b) decidir si el camino D recibe D22 (ver H4) o si D22 se limita al primer pase; (c) si se mantiene, documentar en el pre-registro que `lit_con_compuerta` no aísla la compuerta.

### H3 · La secuencia pide interpretar el probe v2 antes de proponer brazos · gravedad 3 · CONFIRMADO

- **Archivo:línea**: `tasks/BLOQUE_ARRANQUE_S142.md:24` (probe v2 "corrido, SIN interpretar") y `:103-104` ("lanzar un verificador con contexto limpio sobre el veredicto antes de cualquier lectura. No proponer brazos de A/B sin eso"); spec `2026-09-13-plan-definitivo-paridad-design.md:122-124` y `:131` ("A/B con los brazos que el probe justifique").
- **Qué pasa**: la Tarea 7 escribe seis brazos y la Tarea 10 (pre-registro, verificador, workflow) no menciona el probe v2.
- **Qué se mediría mal**: el diseño de brazos quedaría fijado antes del dato que debía justificarlo.
- **Cambio sugerido**: dejar la Tarea 7 condicionada al verificador del probe v2, o agregarlo como paso 0 de la Tarea 10. Las Tareas 0 a 6 (flags OFF y tests) no dependen del probe.

### H4 · El camino D no son los Tests 2 y 3 del paper · gravedad 3 · CONFIRMADO

- **Archivo:línea**: `detection_context.py:264-270` (`contextual_dnti_hot_mask`: sólo `dnti > c1`, sin dETI ni `mu + C2 sigma`); plan §1.3, fila `:269`: "la fórmula del paper es dNTI contra C1".
- **Qué pasa**: los Tests 2 y 3 (SP426.5 visor p. 7) exigen dNTI **y** dETI, cada uno contra `C1` o contra `mu + C2 sigma`. El camino D es un test parcial heredado (S15). Quitarle la compuerta no lo acerca al paper; sólo lo afloja. En producción su único efecto es H2.
- **Qué se rompería**: nada en el código. Se rompe la justificación "literal" y aparece el acople de H2.
- **Cambio sugerido**: decisión del dueño (tabla DECISIONES, fila c3).

### H5 · El recorte a cero por píxel no es lo que escriben Fernandina 2025 ni Campus 2024 · gravedad 3 · CONFIRMADO (lectura), decisión abierta

- **Archivo:línea**: `process_viirs.py:1420`, `:1869`, `:1893` (`np.maximum(..., 0.0)` por píxel); plan §0 "Qué NO cambia" y §5 punto 6.
- **Qué pasa**: Fernandina 2025 p. 9 ec. 3 y Campus 2024 p. 3 ec. 1 y 2 restan sumas (`Σ L_hot − Σ L_bk`), sin recorte por píxel. Con D25 ON, un píxel alertado más frío que la media de sus vecinos (el vecino tibio de un cúmulo) cuenta 0 en vez de restar.
- **Qué se mediría mal**: el criterio 3 del spec (magnitud cerca de 1) evaluará un híbrido (fondo literal con recorte no literal) que sesga la magnitud hacia arriba respecto de MIROVA. El plan lo declara fuera de alcance y lo remite a la pregunta 4 del correo. Es legítimo, pero el pre-registro debe decirlo.
- **Cómo reproducir**: mirar las páginas citadas.

### H6 · En el arnés, MODIS no ejercita la compuerta: su parte del test (d) pasa por construcción · gravedad 2 · CONFIRMADO

- **Archivo:línea**: plan, Tarea 2, `test_modis_y_viirs750_no_cambian_con_los_dos_flags_on`.
- **Qué pasa**: la mutación **M1** (default `apply_bt_gate=False` en los tres helpers, así que MODIS y V750 pierden la compuerta) hace fallar el test con "AssertionError: v750". El bucle recorre `("modis", "v750")` en ese orden, así que MODIS quedó idéntico: la escena MODIS no es sensible a la compuerta. Además, `test_los_helpers_con_su_default_no_cambian_con_los_flags_on` pasa por construcción, porque los helpers no leen el perfil. Los guards de fuente (`_tokens(...) == 0` en MODIS y V750) sí cubren el cableado.
- **Cambio sugerido**: en la escena MODIS, un píxel que sólo pase por quitar la compuerta, y un control que muestre que M1 lo mueve.

### H7 · Los "vecinos" se toman en la grilla nativa del barrido; MIROVA los toma en la grilla UTM remuestreada · gravedad 2 · CONFIRMADO (lectura)

- **Archivo:línea**: `mirova_equivalent` con `ENABLE_UTM_REGRID=False` (plan §1.1); Campus 2024 p. 3 y Fernandina p. 9 (remuestreo).
- **Qué pasa**: la ventana de 8 vecinos (o de 7x7) de 375 m nativos no es el mismo entorno físico que el de MIROVA fuera del nadir. Es D17 cruzada con D25, y no invalida el flag.
- **Cambio sugerido**: una línea en §5 y en el pre-registro.

### H8 · Diagnósticos D25 doble contados o de otra población en records del Test 1 · gravedad 2 · CONFIRMADO (lectura)

- **Archivo:línea**: plan, Tarea 6, Paso 8 (`_bg_vecinos_n_sin_vecinos += _n_sin` en el bloque contextual) y Paso 9, segundo bloque (otra suma); `diag_L_bg_vecinos` sólo se asigna en el bloque contextual.
- **Qué pasa**: en un record con fuente Test 1 el contador suma evaluaciones de los dos bloques, y la mediana del fondo describe píxeles contextuales que no son los publicados.
- **Cambio sugerido**: reiniciar el contador y reasignar `diag_L_bg_vecinos` en el bloque del Test 1 que reconstruye `anomaly_pixels`.

### H9 · La SP426.5 admite una corona del cúmulo, y esa implementación ya existe · gravedad 2 · CONFIRMADO (lectura)

- **Archivo:línea**: SP426.5 visor p. 8, ec. 6 "(or around the active cluster)"; `process_viirs.py:1491-1497` (`apply_corona_magnitude_v375`, S126, flag OFF).
- **Qué pasa**: el plan implementa el fondo por píxel (Campus 2024) y mantiene la corona OFF en todos los brazos. La literatura no decide entre las dos lecturas: SP426.5 admite ambas y Campus 2024 elige por píxel. Ningún texto leído fija el número de vecinos ni qué hacer cuando no hay vecinos no alertados.

### H10 · El test de `max_half` inválido escribe un YAML dentro de `pipeline/profiles/` · gravedad 1 · CONFIRMADO

- **Archivo:línea**: plan, Tarea 4, `test_max_half_invalido_falla_al_cargar`.
- **Qué pasa**: si el test se interrumpe, queda `_s142_tmp_max_half_cero.yaml` suelto en el repo. Conviene `tmp_path` más un mecanismo de carga desde ruta, o al menos un `.gitignore`.

### H11 · Rendimiento del bucle por píxel: sin riesgo · gravedad 1 · CONFIRMADO

En los 24.991 records V375 de `data/mirova_equivalent/`, el máximo de `n_anomalous_pixels` es 360 y el percentil 99 es 34. Con ventanas de hasta 7x7, el costo es despreciable frente a `generic_filter`.

### H12 · Con el segundo pase condicionado ON, el camino ETI queda vacío en los brazos literales · gravedad 1 · CONFIRMADO (lectura)

`detection_context.py` (dentro de `second_pass_adjacent`): `if conditioned and not np.any(active_mask): return active_mask.copy()`. `process_viirs.py:1149` lo llama con `empty_active`. Es inerte hoy (`ENABLE_ETI_QUADRATIC_SCENE=False`), así que la decisión 5 del plan no cambia nada medible.

## VERIFICADO LIMPIO

- **Anclas del plan**: las 24 ediciones encuentran su texto exactamente una vez sobre `f0020c7b2`; `py_compile` rc 0 en los cuatro módulos editados (log de `aplicar_plan_en_copia.py`).
- **Tests**: 113 PASS sobre la copia (tests nuevos del plan, GR2, `test_fondo_persistido_s140.py`, `test_second_pass_conditioned_s135.py` (17), `test_local_kernel_background.py` (8), corona S126 y S127). A49: los `return` quedan intactos (compila y los tests de extremo a extremo pasan).
- **Mutaciones de control**: M1 (default de la compuerta) y M2 (fondo por vecinos siempre activo) hacen fallar los tests; M4 (la llamada dual-ROI ignora el flag) la atrapa el guard de fuente con "assert 2 == 3". Sólo M3 escapa (H1).
- **Golden**: el paso 2 de la Tarea 1 da `mirova_equivalent 0 2 [(266.0, 0.0), (262.0, 0.0)]`, idéntico a lo esperado. Dos corridas dan `cmp` IDENTICO.
- **Valores ON**: D22 simulado da primer pase 0 a 2, segundo pase 2 a 0 y `anomaly_pixels` y `primary_cluster` sin cambio. En los helpers, el cráter (12960) y el vecino (12961) entran con `mu` y `sigma` intactos. El cráter en ~0,0968 MW también se reproduce con la mutación del flag D25.
- **Lectura de flags (A89, S124)**: `enable_*` desde `_p` (`profile.py:131`), parámetros desde `_t` (`:79`); `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK` desde `_p` (`:264`); sensores desde `_cfg["sensors"]` (`:808-811`); `run_pipeline.py:213-218` salta plataformas. Los seis brazos leen lo que declaran (test PASS en la copia).
- **Citas `archivo:línea` del plan contrastadas**: `detection_context.py:269, 373, 376, 532, 803`; `process_viirs.py:83, 212, 215, 235-238, 619, 671, 897, 925, 979, 1001, 1034-1051, 1113, 1180-1181, 1191, 1240-1262, 1370-1377, 1401-1424, 1491-1497, 1648-1653, 1696-1702, 1788-1799, 1847-1902, 2131`; `process_modis.py:667, 695, 703, 823, 871`; `process_viirs_mod.py:626, 645, 679, 687, 782, 834`; `profile.py:88`; `mirova_equivalent.yaml:30, 44, 138, 428, 442`; `volcanoes.yaml:54, 89, 523, 623, 661`; `run_pipeline.py:244, 288, 334`; `vrp_regimes.py:30, 35, 106, 109`; `test1_integrated.py:412`; `f5_core.py:97-104`; `store.py:551-554`; `MIROVA_DIVERGENCES.md:2246, 2257-2260, 2295, 2299-2301`; `test_fondo_persistido_s140.py:65-74`; `test_guard_declarado_vs_efectivo_s131.py:146-158`. Todas existen y hacen lo que el plan dice.
- **Contrato G8**: tras las ediciones, `FLAG_DNS` sigue en la l. 83 y el import de `compute_test1_nti` en la 212; la llamada pasa de 1082 a **1113** (el número que la Tarea 9 tendrá que medir).
- **`hot_mask_2d` definido en los bloques del Test 1** (SOSPECHA del plan §6): resuelta por traza. `test1_n_contrib > 0` sólo se asigna en `:1113`, dentro de `if _t_bg_tmp is not None` (`:925`), la misma rama que asigna `hot_mask_2d` en `:1191`. Los tests de extremo a extremo no dieron `UnboundLocalError`, aunque, por H1, esos bloques no se ejecutaron.
- **Sitios de la compuerta**: el grep de `bt_sanity_k|NTI_BT_SANITY_K` coincide con la tabla §1.3; no falta ningún sitio V375.
- **F5**: `store.py` no resta fondo; `f5_core_vrp_mw` suma `anomaly_pixels[*].vrp_mw`, así que hereda D25.

No corrí la suite completa del repo (el plan la toma como línea base en la Tarea 0), ni `auditar_guards_por_subcadena.py`. El guard nuevo de `_tokens` usa frontera de palabra a ambos lados y, por M4, no pasa por subcadena.

## DECISIONES

| # | decisión | quién | recomendación |
|---|---|---|---|
| a1 | ¿El Test 1 (NTI > K1) tiene condición de temperatura? | literatura | **No** (SP426.5 visor p. 6). Dejar `:979` fuera de D22 sólo por alcance D23 y corregir la SOSPECHA del plan §6 |
| a2 | ¿Tests 2 y 3 con compuerta? | literatura | **No** (visor p. 7). D22 confirmada |
| a3 | ¿Fondo en radiancia o en temperatura? | literatura | **Radiancia** (Campus 2024 p. 3; Fernandina p. 9) |
| a4 | ¿Fondo por píxel o único? | literatura, parcial | Campus 2024 p. 3: **por píxel**, total = suma. SP426.5 ec. 6 admite también la corona del cúmulo |
| b1 | Escena sintética donde gane el Test 1 (H1) y control M3 que falle | quien implementa | hacerlo antes de la Tarea 6 |
| b2 | Escena MODIS sensible a la compuerta (H6) | quien implementa | agregar |
| b3 | Contador y diagnóstico D25 en el bloque del Test 1 (H8) | quien implementa | reiniciar y reasignar ahí |
| b4 | Test de `max_half` sin escribir en `pipeline/profiles/` (H10) | quien implementa | usar ruta temporal |
| b5 | Corregir en §0, Tarea 6 y Tarea 8 la frase "D22 sola no cambia lo publicado" (H2) | quien implementa | acotarla al camino contextual |
| c1 | Número de vecinos, ventana creciente hasta 7x7 y respaldo al fondo de hoy | Nicolás | ningún texto lo fija. Aceptar `max_half_px = 3` como propone el plan, pero barrer 1 contra 3 en el A/B y reportar cuántos píxeles caen al respaldo |
| c2 | Recorte a cero por píxel frente a resta de sumas (H5) | Nicolás, con la pregunta 4 a Coppola | mantener el recorte en este A/B, pero declararlo en el pre-registro como confusor de la magnitud. Evaluar un brazo "resta de sumas" cuando Coppola conteste |
| c3 | ¿El camino D (dNTI > C1) recibe D22? (H2, H4) | Nicolás | **no** en el brazo literal: limitar D22 al primer pase y al ETI. El camino D no es un test del paper y su compuerta acopla D22 con `keep_peak` |
| c4 | ¿Fondo por píxel o corona del cúmulo (S126)? (H9) | Nicolás | por píxel en el literal (Campus 2024 lo precisa), dejando la corona como ablación posible |
| c5 | ¿Crear brazos antes del verificador del probe v2? (H3) | Nicolás | no: Tareas 0 a 6 sí; la Tarea 7 después del verificador del probe v2 |
| c6 | Grilla nativa frente a UTM remuestreada (H7) | Nicolás | no bloquea; anotarlo como límite en el pre-registro |
