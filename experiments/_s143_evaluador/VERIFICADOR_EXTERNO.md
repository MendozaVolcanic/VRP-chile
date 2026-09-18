# Verificador con contexto limpio: el evaluador del A/B D22/D25 (PR #686)

> Auditado el 2026-09-17 sobre `origin/s143-evaluador-ab` (`f39f557af`), en un worktree de sólo
> lectura (`C:/Users/nmend/AppData/Local/Temp/verif-686`). No toqué la rama principal, no commiteé,
> no despaché nada. Único archivo escrito en el checkout: este informe. Archivos auditados:
> `experiments/_s143_evaluador/{evaluar.py, fusionar.py, control_s135.py, README.md, CONTROL_S135.md}`
> y `tests/test_evaluador_ab_s143.py`. Contraste: `docs/PREREGISTRO_AB_D22_D25_S143.md` §5,
> `docs/PREREGISTRO_AB_D22_D25_S143_VERIFICADOR.md` (hallazgos 2, 3, 4, 7, 10, 11, 14, 15, 16),
> `experiments/_s135_ab_d1d2/{evaluar_ab.py, resultado_final.json}`, `scripts/banco_paridad.py`,
> `scripts/build_c2ab_windows.py`.

## Veredicto

**CORREGIR ANTES.** El instrumento mide lo que dice y su control sobre S135 se sostiene (lo
reproduje por mi cuenta), pero no está atado al pre-registro, sus **reglas de veredicto no las
vigila ningún test** (siete mutaciones sobre los umbrales de decisión pasan en verde) y la
redefinición del criterio 1 endurece la regla de "cero pérdidas" que Nicolás aprobó bajo la
definición floja. El código puede mergearse; no debería juzgar el A/B hasta cerrar H1, H2 y H3.

## Hallazgos

Gravedad 5 = el A/B se juzgaría con otra medida que la declarada; 1 = redacción.

| # | grav. | estado | hallazgo | evidencia | corrección propuesta |
|---|---|---|---|---|---|
| H1 | **3** | CONFIRMADO | **El pre-registro no queda atado al evaluador.** El hallazgo 3 pedía "commitear y citar su sha en el pre-registro". El PR no toca `docs/`: el pre-registro sigue diciendo "Falta además el evaluador" y el comando exacto (ocho volcanes, ventana, `--cota-km`, `--B`, `--semilla`, `--n-min`, `--tol-magnitud`, `--denominadores`) vive sólo en el README, que es editable. Todo eso queda elegible después de ver datos: es el grado de libertad más grande que queda abierto. | `git diff --stat origin/main...HEAD` (9 archivos, ninguno en `docs/`); `grep -n "evaluador" docs/PREREGISTRO_AB_D22_D25_S143.md` da una sola línea, la 8 | En la v2 del pre-registro: pegar el comando literal y el sha de `evaluar.py`. En el código: que el JSON marque `parametros_igual_al_preregistro: false` (ya guarda los valores en `meta.parametros`, falta el contraste) y que el informe lo diga en la primera línea. |
| H2 | **3** | CONFIRMADO | **El criterio 1 cambió de definición y con eso cambia la decisión de Nicolás.** Exigirle la cota también al brazo (hallazgo 2, bien implementado) lleva al brazo D de S135 de **12 a 28** pérdidas y al brazo B de **0 a 14**. Con este instrumento, B (que S135 declaró sin pérdidas) queda rechazado. La regla "umbral 0" se decidió el 2026-09-07 sobre la definición floja; aplicarla sobre la estricta es otra regla, más dura, y hoy `cumple` usa sólo la estricta. | `experiments/_s143_evaluador/control_s135.json`: `brazos._s135_ab_d_ambos.criterio1.n_perdidas = 28` contra `n_perdidas_sin_filtro_brazo = 12`; `_s135_ab_b_nokeeppeak`: 14 contra 0 | Ratificarlo con Nicolás en la v2, con la tabla de S135 como ejemplo de cuánto cambia. El veredicto debe imprimir los dos conteos lado a lado (el JSON ya los trae; el informe también, pero la palabra "cumple" no distingue). |
| H3 | **3** | CONFIRMADO | **Las reglas de veredicto no las cubre ningún test.** De 22 mutaciones, 13 mueren y 9 sobreviven, y las sobrevivientes se concentran justo en las decisiones: qué extremo del IC decide el criterio 2 (M5), la dirección de la desigualdad del criterio 3 (M16), el umbral 0 del criterio 1 (M21), la exclusión de volcanes desparejos (M22), el castigo al brazo sin pares decisivos (M23), y los valores por defecto de la cota y la tolerancia (M24, M20). Comprobé a mano que el código vigente acierta en los tres casos límite, así que no hay bug: hay un instrumento sin fusible justo donde importa. | Tabla de mutaciones más abajo. Comprobación del código real: IC `[-0,15; 0,15]` con `dif = 0` da `cumple False`; magnitud 1,0 -> 0,2 sin volcán evaluado da `cumple False` | Seis tests: (a) IC que cruza el cero no cumple el criterio 2; (b) brazo que empeora en el total no cumple el criterio 3; (c) exactamente una pérdida no cumple el criterio 1; (d) volcán desparejo queda fuera de `volcanes_evaluados` (test de punta a punta); (e) `n_pares_decisivo == 0` cuenta como que empeora; (f) los valores por defecto de `PRESUPUESTO_COTA_KM` y `TOL_MAGNITUD` fijados literalmente. |
| H4 | **3** | CONFIRMADO | **El test de determinismo del bootstrap no falla cuando se saca la semilla.** `test_bootstrap_estratificado_determinista_con_semilla` compara dos llamadas con la misma semilla, pero la fixture tiene 5 noches y el percentil es tan grueso que dos corridas sin semilla suelen coincidir: reemplacé `default_rng(semilla)` por `default_rng()` y la suite quedó verde; en 6 corridas directas, 2 dieron un intervalo distinto y 4 el mismo. El test dice "determinista con semilla" y no es sensible a la semilla. | Mutación M17: `23 passed`. Corrida directa con la semilla anulada: `(-0,4117; -0,0769)` cuatro veces, `(-0,4166; -0,0769)` y `(-0,4143; -0,0833)` una vez cada una | Fijar el intervalo esperado a valores literales, y agregar que dos semillas distintas den intervalos distintos sobre una fixture con suficientes noches. |
| H5 | **2** | CONFIRMADO | **`evaluar()` no se ejercita de punta a punta en la suite.** Ningún test llama a `evaluar()` ni a `main()`: cobertura -> exclusión de volcanes, seguimiento, referencia por sha, controles de instrumento y armado del informe sólo corren dentro de `control_s135.py`, que necesita los artefactos locales de S135 y red. Por eso M22 sobrevive. | `grep -n "evaluar.evaluar\|ev.evaluar" tests/test_evaluador_ab_s143.py` no da nada; `control_s135.py:287` es el único llamador | Un test de integración con dos volcanes sintéticos, saltado si no hay node, con la referencia por `--ref-cons/--ref-ocr` local. |
| H6 | **2** | CONFIRMADO | **La cota de mismo objeto se ablanda cuando MIROVA tiene más filas esa noche.** La cota es el mínimo sobre TODAS las distancias de alerta de la noche, de cualquier pasada y mezclando CONS y OCR (que informan la misma pasada con dos números: 3,75 y 4,36 km). Cuantas más filas, más fácil "coincidir". Medido: Isluga 2026-06-10, con una sola distancia disponible la noche se descarta; con tres, se acepta. Está heredado de S135 (`evaluar_ab.py:276-280`), pero implica que el tamaño del universo del criterio 1 depende de cuán completo esté el OCR, que se completa con retraso (hallazgo 11). No sesga la comparación entre brazos: la referencia está fijada por sha y es la misma para todos. | Corrida propia sobre los artefactos de S135: `dist MIROVA hoy=[3,75; 4,36; 1,41]` contra `pre=[3,75]` para Isluga 2026-06-10; `evaluar.py:271-275` | Anotar por noche cuántas filas dieron la cota y con cuál se aceptó. A futuro, evaluar parear la distancia a la PASADA y no a la noche (es otro criterio, no lo cambies ahora). |
| H7 | **2** | CONFIRMADO | **Fuga latente `sin_cota`, y asimétrica en el reporte.** Si un brazo publica una noche con un record sin centroide, o si MIROVA no dio distancia esa noche, la noche se retiene sin pasar por la cota (`evaluar.py:267-269`). Para el control eso se reporta (`aceptadas_sin_cota_calculable`), para el brazo no aparece en ningún lado. En S135 el contador es 0, así que hoy no muerde; en los brazos sin compuerta puede cambiar. | `control_s135.json`: `noches_confirmadas.aceptadas_sin_cota_calculable = {}`; `criterio1()` (l. 294-311) no expone `est_brazo[v]["sin_cota"]` | Agregar `retenidas_sin_cota` por brazo y volcán a `criterio1`, y sacarlo en el informe al lado de las pérdidas. |
| H8 | **2** | CONFIRMADO | **El sha de `frontend/index.html` se registra pero no se compara con el del pre-registro.** El predicado se ejecuta del archivo vivo; si `index.html` cambia entre el pre-registro y la evaluación, el predicado cambia sin aviso. Hoy coinciden (`24fba8a1...`). | `evaluar.py:584` guarda `sha_index_html`; `denominadores.json meta.sha_index_html` lo tiene pre-registrado; nada los cruza | Campo `sha_index_html_coincide_con_preregistro` y aviso en el informe si es falso. |
| H9 | **2** | CONFIRMADO | **Números escritos a mano en `CONTROL_S135.md`** (regla S91): "93,8 %", "557 alertas OCR", el borde "0,70 km" (también literal en `control_s135.py:174`), "2 minutos", y el título "Las doce noches" cuando el conteo es calculado. Los verifiqué y son correctos, pero no salen del JSON: el 557 lo reproduje por mi cuenta y el 93,8 % es `502/535`, el mismo número que el JSON trae como `0,9383`. | `control_s135.py:195-197, 234-236, 219`; conteo propio sobre `f9805ad397dc_registro_vrp_ocr.csv`: 892 filas ALERTA, **557** ganan distancia con el regex de #652 | Pasar esos cuatro a la salida del script (el umbral 0,70 como constante con nombre) y que la prosa los interpole. |
| H10 | **2** | CONFIRMADO | **El hallazgo 16 quedó a medias.** Pedía "declarar el rango esperado del control y qué se hace si no cae". El evaluador publica la línea base (`control.neg_limpio_tasa_publica`) y el README dice que sirve "para contrastarla con el régimen esperado", pero el rango no está escrito en ninguna parte y no hay acción declarada. | `README.md` fila 16; `evaluar.py:593-598` | Declarar el rango en la v2 del pre-registro (la referencia post #571 es 87,1 %, A104) y que el JSON traiga `linea_base_en_rango`. |
| H11 | **2** | CONFIRMADO | **Escotilla `--ref-cons/--ref-ocr`.** Permite evaluar con una referencia distinta de la fijada por sha; registra el blob y sigue. Es la salida correcta para correr sin red, pero es un grado de libertad abierto. | `evaluar.py:529-533, 755-756` | Que el JSON marque `referencia_fijada_por_sha: false` y que el informe lo muestre arriba, no dentro del bloque de procedencia. |
| H12 | 1 | CONFIRMADO | **La atribución del 257 contra 260 es correcta pero el relato la simplifica.** No son "3 noches menos": son 4 que bajan y 1 que sube. Isluga pierde el 2026-06-09 (gana distancia OCR 2,18 y el objeto publicado queda a 0,648 de la cota) y gana el 2026-06-10 (las distancias nuevas 4,36 y 1,41 acercan la cota), neto 0 en Isluga. La tabla por volcán lo esconde. | Corrida propia: `FLIP Isluga 2026-06-09`, `FLIP INVERSO Isluga: ['2026-06-10']`, `FLIP PuyehueCordonCaulle 2026-06-01 y 06-10`, `FLIP Tupungatito 2026-06-04` | Una línea en `CONTROL_S135.md` con las cuatro que bajan y la que sube. |

**Fuera de alcance de este PR, pero sigue abierto**: el hallazgo 1 del verificador del pre-registro
(gravedad 5, la compuerta de temperatura sigue puesta en la máscara contextual que filtra el camino
del Test 1). El evaluador no lo toca ni puede tocarlo. Mientras no se decida, el A/B no debe
despacharse aunque el instrumento esté listo.

## Las mutaciones que probé

Cada una se aplicó sola sobre el worktree temporal, se corrió `pytest tests/test_evaluador_ab_s143.py`
y se restauró el archivo. Suite intacta antes y después: 23 passed.

| # | mutación | resultado |
|---|---|---|
| M1 | `cota <= presupuesto` invertido | ROJO `test_estado_noches_aplica_cota_desde_mirova_center` |
| M2 | pérdida sin exigir la cota al brazo (revierte el hallazgo 2) | ROJO `test_perdida_exige_la_misma_cota_en_el_brazo` |
| M3 | bootstrap con el signo cambiado (control menos brazo) | ROJO `test_bootstrap_remuestrea_dentro_de_cada_volcan` |
| M4 | bootstrap sin estratificar (pool de todas las noches) | ROJO `test_bootstrap_remuestrea_dentro_de_cada_volcan` |
| M5 | criterio 2 decide con el extremo BAJO del IC | **PASA (23)** |
| M6 | criterio 3 sobre el conjunto de cada brazo, no los pares comunes | ROJO `test_criterio3_decisivo_sobre_pasadas_publicadas_por_ambos` |
| M7 | fila MIROVA: OCR antes que CONS | ROJO `test_fila_mirova_cons_antes_que_ocr` |
| M8 | cobertura ciega a las pasadas de más del brazo | ROJO `test_cobertura_product_version_distinto_es_desparejo` |
| M9 | cobertura ciega a `product_version` | ROJO `test_cobertura_product_version_distinto_es_desparejo` |
| M10 | n mínimo contado en los pares y no en las `pos` del control | ROJO `test_criterio3_n_min_se_cuenta_en_las_pos_del_control` |
| M11 | magnitud del brazo tomada del control | ROJO `test_criterio3_n_min_se_cuenta_en_las_pos_del_control` |
| M12 | fusión que no detecta conflictos entre tramos | ROJO `test_fusion_une_tramos_y_avisa_solape_conflictivo` |
| M15 | criterio 2 filtra por la etiqueta del brazo y no la del control | PASA (mutante equivalente: la etiqueta la fija la referencia, es la misma en los dos) |
| M16 | criterio 3 con la desigualdad invertida | **PASA (23)** |
| M17 | bootstrap sin semilla | **PASA (23)**, ver H4 |
| M18 | sin filtro de pasada diurna | ROJO `test_cargador_reproduce_al_banco_de_paridad` |
| M19 | la noche se acepta siempre (cota apagada) | ROJO, 2 tests |
| M20 | tolerancia de magnitud 0,05 -> 0,10 | **PASA (23)** |
| M21 | criterio 1 cumple con hasta una pérdida | **PASA (23)** |
| M22 | los volcanes desparejos ya no se excluyen | **PASA (23)** |
| M23 | brazo sin pares decisivos deja de contar como que empeora | **PASA (23)** |
| M24 | cota por defecto 0,55 -> 5,0 km | **PASA (23)** |
| M13, M14 | inocuas (comentario; orden de claves del dict de salida) | PASA, como corresponde |

Mueren 13 de 22 mutaciones sustantivas. Las que sobreviven son las reglas de veredicto y los valores
por defecto (H3), más una equivalente.

## Lo que comprobé y SÍ está bien

- **El predicado es el del dashboard ejecutado con node** (A97), no reconstruido: `construir_pasadas`
  arma los mismos casos que `banco_paridad.cargar_nuestros` y el test con node lo compara campo a
  campo; el control de identidad (`[0,1,1,1,0], [1,0]`) sale `true` en `control_s135.json`. Si una
  función del `index.html` se renombra, el runner de node tira excepción en vez de seguir.
- **La referencia está fijada por sha**: bajé los dos CSV por los sha de `denominadores.json`
  (`92f26b98b490...` y `f9805ad397dc...`) y el evaluador los usa con el loader unificado.
- **Los números del informe salen del JSON**: `informe_markdown(res)` no interpola nada que no venga
  de `res`; los tres `.md` publicados tienen 0 guiones largos y 0 medios.
- **Cobertura simétrica y `product_version`** (hallazgo 15): implementado y con mutación que muere.
- **Bootstrap** (hallazgo 14): remuestrea noches DENTRO de cada volcán, estratificado, semilla 143,
  B = 10.000, con el par (control, brazo) de la misma noche conservado, y el estadístico es la
  diferencia de tasas sobre las mismas pasadas: responde exactamente la pregunta del criterio 2.
  `margen_signo` dice cuántas pasadas discordantes netas deciden el signo.
- **Criterio 3** (hallazgo 4): decide sobre las pasadas `pos` que publican AMBOS, informa además el
  conjunto de cada brazo, cuenta el n mínimo sobre las `pos` del control, y fija una sola fila de
  MIROVA por pasada con CONS antes que OCR. Las cuatro cosas con mutación que muere.
- **Hallazgo 7**: toda pérdida cuenta, no hay reclasificación posterior en el código.
- **Hallazgo 10**: `tasa_art` y `tasa_predisplay` (`summit && valid && disp > 0`) en negativos
  limpios, para control y brazo, más la bandera `art_sube_en_brazo`.
- **Estratos**: los de `build_c2ab_windows.py:41-42`, y los ocho volcanes del pre-registro caen donde
  dice su tabla (5 focales, 3 nevados). Siempre va el desglose por volcán.
- **Control sobre S135, reproducido por mi cuenta, sin usar `control_s135.py`**: fusioné los
  artefactos de los dos runs, construí las 2.157 pasadas con node y conté las noches confirmadas dos
  veces. Con el regex de hoy: **257** (Isluga 71, Láscar 52, Lastarria 48, PCC 31, PP 28, Tupungatito
  27). Con el regex anterior al PR #652: **260** (PCC 33, Tupungatito 28). Idéntico a lo que reporta
  el agente, volcán por volcán. **La atribución al loader OCR es correcta**: las cuatro noches que
  cambian son exactamente noches en que la distancia de MIROVA sólo existe con el regex nuevo
  (`git log -L 93,93:pipeline/mirova_csv_loader.py` confirma que el regex previo es el que usa
  `control_s135.py`), y el objeto publicado queda lejos de esa distancia (cotas 0,648 / 3,023 / 0,758
  / 3,288 km). El "557 alertas OCR" también lo reproduje: 557 de 892 filas ALERTA del OCR ganan
  distancia con el regex de #652.
- **Las doce noches de S135** coinciden una a una con `resultado_final.json` (`perdidas_sin_filtro_brazo`),
  y el control del instrumento contra sí mismo da 0 pérdidas, 0 ganancias y diferencia 0.
- **`fusionar.py`** es genérico (prefijo, brazos, volcanes y N tramos por argumento), avisa de claves
  repetidas con contenido distinto, no escribe la fusión si falta un tramo, y tiene `--estricto`.
- **Orden de los commits**: los tests entraron primero ("rojo primero") y el código después.

## Lo que este informe NO prueba

- Que la cota de 0,55 km acepte sólo objetos de verdad iguales: es una cota inferior por construcción
  (A93) y sigue siéndolo.
- Que los criterios 2 y 3 estén bien calibrados para los brazos de S143: los perfiles son otros.
- Nada sobre el hallazgo 1 del verificador del pre-registro, que es lo que hoy bloquea el A/B.
- El costo en CPU y memoria del evaluador con ocho volcanes y seis brazos: los artefactos de S135
  pesan 2 a 4 MB por volcán y brazo, así que no veo riesgo, pero no lo medí a esa escala.
