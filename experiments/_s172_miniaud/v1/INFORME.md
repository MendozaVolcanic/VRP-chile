# Informe del verificador V1 (frentes f1 y f3)

## 1. Encabezado
- Fecha y hora del servidor: 2026-11-02 01:42 UTC (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera Date).
- Objeto medido: worktree D:/vrp-trabajo/worktrees/s172-miniaud-b, HEAD b4282319446cfea944aa1a4621c0fec7da8649a0 (PR B), verificado con `git rev-parse HEAD`. B son 3 commits sobre da67fa4173ee08fa20bd13992d857912386e03b6 (`git rev-parse b42823194~3`); c83882fcf no es ancestro de B (`git merge-base --is-ancestor`) y su merge-base con B es da67. Base main d3cd0b2ae.
- Modelo y esfuerzo reales: Sonnet 5.5, esfuerzo alto.
- CARPETA: D:/vrp-trabajo/temporales/s172_miniaud/v1
- caminos.md escrito antes de abrir ningún archivo citado. sha256 del archivo final (incluye la nota de cierre): a5119e73510406dd59ffc4be977d13c5ab77e2c10bdc775f423c6713c5387b27. sha256 del contenido anterior a la nota: 2cb9a5f59ee0c5263066d5d40cf36482ce82b9fb540e2454e9a44e2c9dce94f9. Hora de la nota: 2026-11-02 01:36:11 UTC.
- No miré: INFORME.md ni hallazgos.csv de f1, f2, f3 (prohibido); la suite completa; ningún workflow en GitHub; datos reales de producción tras el flip (no existen aún: `grep -l '"codigo_mirova"'` en data/experimental_v2 y data/mirova_equivalent no devuelve archivos).
- Límite de entorno: MODIS real no corre en Windows. Los records de la vía se construyeron con la función real `MV.procesar_grilla` sobre las fixtures del censo (tests/datos_s164_modis), más un foco sintético en un caso.

## 2. En una pantalla
- Los 8 ítems se sostienen: 6 CONFIRMADO, 2 CONFIRMADO EN PARTE (105 y 106), 0 REFUTADO. MA172-101 y MA172-302 son el mismo defecto y los fundo.
- Bloquean el PR B: 101/302 (la vigilancia de K cuenta los records de la vía como K y pediría `git revert` de K ante una pérdida de la vía), 102 (marcador del mapa en el primer píxel alertado: 16,15 km con el record "summit" a 0,567 km, reproducido con la función real) y 103 (prueba roja en la punta de B, verde en da67). Ninguno bloquea el PR A, que es inerte con el flag apagado.
- No bloquean: 104 y 110 (perfiles que heredan la vía, sin workflow vivo), 105 y 106 (documentación; la cabecera FICHA de mirova_v750_codigo.py sigue titulando APAGADA).
- Hallazgos propios: un comentario de pipeline/profile.py que dice APAGADA (gravedad 1) y una sospecha sobre el orden de merge de A y B.

## 3. Hallazgos nuevos

### VMA172-101
- TÍTULO: pipeline/profile.py describe la vía de MODIS como «entra APAGADA» junto al flag que producción tiene en true
- ARCHIVO:LÍNEA: pipeline/profile.py:905-909 (worktree B)
- QUÉ PASA: el comentario de la constante que lee el flag de la vía dice que «entra APAGADA» y que con False el procesador MODIS «es el de hoy». Es historia de S164; desde el PR B producción lo lee en true (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"` imprime True). Misma familia que MA172-106, un tercer archivo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/worktrees/s172-miniaud-b && sed -n 905,909p pipeline/profile.py`
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1. Cambio mínimo: una marca A113 de una línea.

### VMA172-102
- TÍTULO: orden de merge de A y B: B contiene los 7 commits de código de A y no el commit c83882fcf
- ARCHIVO:LÍNEA: `git log --oneline d3cd0b2ae..c83882fcf` y `git rev-parse b42823194~3` (da67fa417)
- QUÉ PASA: B se construyó sobre el código de A. Si A se mergea con squash y después B, el diff de B contra el main nuevo puede arrastrar los mismos archivos de A; si B va primero, A queda casi vacío. No lo probé.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git merge-base --is-ancestor c83882fcf b42823194; echo $?` (da 1).
- CONFIANZA: SOSPECHA (el efecto del squash no lo medí).
- GRAVEDAD: 2 (merge sucio, o revert de B que arrastra A). Cambio mínimo: rebasar B sobre la punta de A antes de pedir el sí, o mergear A sin squash.

## 4. Veredictos por ítem (detalle en veredictos.csv)

### MA172-101 y MA172-302: CONFIRMADO (fundidos; mismo defecto), gravedad mía 3
- Qué comprobé: `scripts/vigilancia_sombra.py:432` arma `prod` con `bp.cargar_nuestros(...)` filtrando sólo por `r.get("sha")`. `cargar_nuestros` (scripts/banco_paridad.py:283-290) guarda `sha` y `perfil` de `regimen` y no copia `via_codigo_mirova` (la cadena "via" no aparece en su fuente). `pipeline/store.py:549` pone `regimen` a todo record y `_marca_regimen` (store.py:89-94) lleva sólo perfil y sha. Un record MODIS de la vía es indistinguible de uno de K.
- Medición (scripts/v101_vigilancia_via.py, salida v101_salida.txt): con las funciones reales `pasadas_de_alerta` y `disparadores`, una pasada MODIS de Láscar con alerta de 2,5 MW de MIROVA, sombra (C0) que publica y producción que calla. Escenario A (K calla): REVERSION_CANDIDATA. Escenario B (record de la vía que calla, misma forma): REVERSION_CANDIDATA. Control C (producción publica): VERDE. Denominador: una pasada por escenario, ventana sintética 2026-11-03.
- Pregunta 1 (¿vería el instrumento una rotura?): sí, A y B disparan y C no. Pregunta 2 (¿se vería distinto si estuviera muerto?): sí, A y B contra C.
- Consecuencia: `.github/workflows/vigilancia-sombra.yml:134-135` abre el issue «Sombra de K: candidata a reversion» y dice que la regla pre-autoriza `git revert` del PR de adopción de K (#850). Tras el PR B la pérdida sería de la vía; revertir K quitaría el detector que quedó de guardia y el de VIIRS. El script no revierte, sólo abre el issue; por eso 3 y no 4. El plazo de esa vigilancia corre hasta unos 120 días desde la adopción del 2026-10-18 o 29 protegidas (docstring de vigilancia_sombra.py), así que el defecto queda vivo meses.
- Es un hueco no declarado: el informe del implementador dice que `vigilancia_guardia_modis.py` importa `vigilancia_sombra.py` «sin modificarlo» y que ese archivo «vigila K»; no menciona que sus records de producción en MODIS pasan a incluir la vía.
- Bloquea: PR B (en A es inerte, no hay records de la vía). Cambio mínimo: que `cargar_nuestros` copie `via_codigo_mirova` (campo aditivo) y que `cargar_insumos` excluya de `prod` los records MODIS con la vía en true, porque MODIS ya lo vigila vigilancia_guardia_modis.

### MA172-102: CONFIRMADO, gravedad 3
- Qué comprobé: `pipeline/mirova_v750_codigo.py:742` emite `final_hotspot_source: "codigo_mirova"`; `frontend/index.html:1630-1631` (y 1697, 2735, 2766, 3283, 3677, 3683) reconocen sólo `["test1_roi","test1_nti_peak","ctx_cluster"]`. Con otra fuente `pixelesDelMarcador` usa `r.anomaly_pixels` y el marcador es el índice 0, que en la vía sale de `np.nonzero(mascara)` (orden de filas), no el píxel de más energía ni el cúmulo (mirova_v750_codigo.py:730-735).
- Medición A (scripts/v102_marcador_via.py, v102_salida.txt): records reales de la vía (6 fixtures del censo) y el JS real de `pixelesDelMarcador` ejecutado con node. Chillán 2026-10-15 07:35: cúmulo y tabla 0,567 km, marcador de la vía a 2,233 km del cráter; control (mismo record con `ctx_cluster`) 0,565 km. Láscar 2026-03-20 07:40: cúmulo 0,91 km, marcador 1,905 km. Los records de un solo píxel coinciden. Denominador: 5 pasadas con alerta de 6 (la sexta no alerta).
- Medición B (scripts/v102c_dos_cumulos.py, v102c_salida.txt): fixture de Chillán más un segundo foco sintético 15 celdas al norte con 0,95 a 0,99 de la radiancia pico, con la función real `procesar_grilla`: record `distance_class: "summit"`, `final_hotspot_dist_km` 0,567, marcador a 16,152 km; control `ctx_cluster` 0,565 km. Reproduce la clase del hallazgo (el auditor dio 14,89 km); su cifra exacta no la reproduje, el mecanismo sí.
- Otras rutas (v102b_salida.txt): la tabla (2735/3283) y la vista resumen (3677) usan `hotspot_dist_km` y `hotspot_lat`, el píxel pico del cúmulo: en Chillán 0,001 km contra 0,567 del cúmulo. Diferencia chica, dentro del cúmulo.
- Bloquea: PR B. Es el mismo fallo que S154 arregló para K (comentario en index.html:1618-1625). Puede resolverse en el PR A, que ya toca frontend y es inerte. Cambio mínimo: agregar `"codigo_mirova"` a las siete listas (mejor una constante común) y extender tests/test_marcador_mapa_ctx_cluster_s154.py.

### MA172-103: CONFIRMADO, gravedad 2
- `python -m pytest -p no:cacheprovider tests/test_guard_adopcion_k_s153.py -q` en B: 1 failed, 2 passed (v103_pytest_B.txt). Falla `test_el_laboratorio_difiere_de_produccion_exactamente_en_k` con la diferencia {ENABLE_MODIS_B22_PRIMARY, ENABLE_MODIS_CODIGO_MIROVA, ENABLE_TEST1_PATH, ENABLE_TESTS_23_PROSE_BRANCH} contra los tres de K. Control: el mismo archivo con `git archive da67fa417 pipeline tests/test_guard_adopcion_k_s153.py volcanoes.yaml` en copia_da67: 3 passed. B no toca el archivo (`git log da67fa417..b42823194 -- tests/test_guard_adopcion_k_s153.py` vacío) y pruebas_pr_b.txt del implementador no lo menciona.
- Bloquea: PR B, por CI rojo (enmienda A39 de S142). Cambio mínimo: tests/test_guard_adopcion_k_s153.py:48, esperar `set(K) | {"ENABLE_MODIS_CODIGO_MIROVA"}`.

### MA172-104: CONFIRMADO, gravedad 2
- `VRP_PROFILE=_s154_reproc_k_historico python -c "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"` imprime True en B (guardia_k_modis imprime False: control). El perfil se declara «IDENTICO A LA REPLICA salvo nombre y directorio» y con K. Las pruebas test_reproceso_historico_k_s154, test_guard_perfiles_congelados_s153 y test_guard_modis_codigo_mirova_encendido_s172 pasan juntas (23 passed): la de identidad compara contra producción, así que hereda el True y no puede ver el cambio. Ningún workflow lo nombra (grep en .github/workflows), pero `reproc-chunked.yml` acepta cualquier perfil por input manual.
- Lo ya declarado: el desvío 3 del implementador dice que los `_*.yaml` salvo `_s146_ab_control` siguen heredando la vía. Lo que no está dicho: éste promete K y su prueba queda verde por construcción.
- No bloquea. Dormante hasta que alguien lo despache (por ejemplo para los 34 volcanes). Cambio mínimo: `enable_modis_codigo_mirova: false` en `thresholds` del perfil y que la prueba de identidad lo reconozca como diferencia declarada.

### MA172-105: CONFIRMADO EN PARTE, gravedad 2
- Confirmado: ninguno de los tres lugares menciona la vía y B no los toca (`git diff da67fa417 b42823194 -- README.md docs/SINTOMAS.md frontend/index.html` vacío); PR_B_CUERPO.md no los menciona. frontend/index.html:544 lo ve el operador: «Desde el 18 oct 2026 la réplica usa el detector K».
- En parte: los tres ya llevan marcas de la adopción de K (README.md:52-56 marca S160; SINTOMAS.md:25-28 «Régimen vigente: el detector K está en producción desde #850») y son verdad como historia de K. Para MODIS quedan incompletos, no falsos.
- No bloquea. Cambio mínimo: una línea A113 en cada uno; la de index.html:544 es la que ve el operador.

### MA172-106: CONFIRMADO EN PARTE, gravedad 2
- pipeline/mirova_v750_codigo.py:5-6 dice «APAGADA por flag en cada sensor (... enable_modis_codigo_mirova, S164)». Con el flag en true en producción es falso como titular; la cláusula «con los flags apagados no corre nada» sigue cierta. Es la cabecera FICHA de un archivo que corre en producción (Res. CPLT 372). B actualizó la cabecera de process_modis.py (línea 20) y no ésta (no está en `git diff --stat da67fa417 b42823194`).
- pipeline/store.py:351-356: el comentario habla del flag de V750 «APAGADO», literalmente cierto para V750; no dice que la misma rama `_via_mirova` ya corre en producción para MODIS. Incompleto, no falso.
- No bloquea A. Conviene corregirlo en B (ficha SDA). Cambio mínimo: reemplazar «APAGADA por flag en cada sensor» por el estado por sensor y sumar una línea en store.py.

### MA172-110: CONFIRMADO, gravedad 1
- `VRP_PROFILE=experimental_lowT python -c "..."` imprime True; hereda de mirova_equivalent por `extends`. Ningún workflow ni test lo nombra (`grep -rn experimental_lowT .github/workflows tests pipeline scripts`: sólo los scripts de piloto local VIIRS run_pilot_a5_s76.* y analyze_pilot_a5_results.py). El guard del PR B cubre perfiles que nombra un workflow programado (tests/test_guard_modis_codigo_mirova_encendido_s172.py, línea 98), así que que no cubra a lowT es por diseño. MODIS no corre en Windows, donde se ejecutan esos pilotos.
- No bloquea. Cambio mínimo: `enable_modis_codigo_mirova: false` en el perfil o una línea en la declaración del implementador.

## 5. SEGUIMIENTOS
- tests/test_guard_libro_de_pruebas_s146.py (g1d y g2c) fallan en mi corrida de B con `ValueError: path is on mount 'C:', start on mount 'D:'` (vnuevo_libro_pruebas_B.txt). Parece de entorno (temporal en C:, repo en D:), no del PR; coinciden con las 2 fallas de pruebas_pr_b.txt del implementador. SOSPECHA de que en CI Linux pasen; no lo medí.
- Tras arreglar 101, revisar que MODIS no tenga dos vigilantes que abran issues duplicados (el viejo y vigilancia_guardia_modis).
- pruebas_pr_b.txt del implementador (1339 passed, 2 failed) no muestra en rojo test_guard_adopcion_k_s153.py aunque en B la mía falla; no sé qué subconjunto corrió ni sobre qué árbol (SIN DATO).

## 6. VERIFICADO LIMPIO
- Topología de B: `git rev-parse b42823194~3` = da67fa417; c83882fcf no es ancestro de B; `git diff --stat da67fa417 b42823194` lista 21 archivos con pipeline/process_modis.py. Vara: la afirmación del brief.
- Flags leídos de `pipeline.profile` (A89), no del YAML: mirova_equivalent True, guardia_k_modis False, experimental False (data_subdir experimental_v2), experimental_ndc_focus False, _s146_ab_control False, sombra_codigo_mirova True, ENABLE_V750_CODIGO_MIROVA False, ENABLE_V375_CODIGO_MIROVA False.
- Las pruebas test_reproceso_historico_k_s154, test_guard_perfiles_congelados_s153 y test_guard_modis_codigo_mirova_encendido_s172 pasan en B (23 passed). Eso NO prueba que el perfil histórico siga siendo K (ver 104).

## 7. SIN DATO
- La cifra exacta de 14,89 km del auditor (otra escena); sólo el mecanismo, con 16,15 km sintético.
- Con qué frecuencia dispararía la vigilancia de K tras el flip (depende de records de la vía que aún no existen).
- Efecto de un merge con squash de A seguido de B.
- Resultado de las pruebas en Linux y CI.

## 8. FUERA DE ALCANCE
- Suite completa, workflows, scripts de mutaciones, el resto de los hallazgos de otros frentes.
