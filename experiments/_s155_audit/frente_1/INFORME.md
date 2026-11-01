# Frente 1, auditoría S155: propagación de K en la documentación y en los textos que se leen para decidir

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f1`, detached en `cb90031a` (origin/main del 2026-10-19). Nada del
repositorio se modificó; todo lo de esta carpeta es medición. Scripts y salidas en
`D:\vrp-trabajo\worktrees\s155-audit-f1\experiments\_s155_audit\frente_1\`.

## 0. Qué es cierto hoy (la vara contra la que se mide cada texto)

| Hecho | Evidencia de esta sesión |
|---|---|
| Producción corre K: `ENABLE_TEST1_PATH = False`, `ENABLE_TESTS_23_PROSE_BRANCH = True`, `ENABLE_MODIS_B22_PRIMARY = True` | `leer_flags.py` / `leer_flags.out`, leído desde `pipeline.profile` (A89) |
| El laboratorio corre C0 (los tres flags al revés) | mismo script, perfil `experimental` (control positivo: el cargador distingue perfiles) |
| K corre de verdad en los datos, no sólo en el YAML: 0 de 3.661 records procesados después del merge con `triggered_test1`, contra 758 de 1.807 antes | `efecto_k_en_datos.py` / `.out` (la primera versión, con ventana 2026-10-01 a merge, dio 17 records porque #852 reprocesó 2026-09-18 a 10-18; se corrigió la ventana y queda anotado en el script) |
| El Test 1 integrado sólo se ejecuta bajo el flag | `pipeline/process_modis.py:741`, `pipeline/process_viirs.py:1126`, `pipeline/process_viirs_mod.py:754` (`if (ENABLE_TEST1_PATH ...)` antes de `compute_test1_mir`) |
| Merge de #850: squash `34cea39e`, 2026-10-18 06:57:30 -0300 = 09:57:30 UTC; tag `pre-s153-adopcion-k` existe | `git show 34cea39e`, `git tag -l` |
| De 95 perfiles resueltos: 78 C0, 8 K, 9 otros | `flags_todos_perfiles.py` / `.out` |

Las dos preguntas del instrumento, en cada script: están en su docstring. Las de lectura de texto (grep) no
tienen nulo medible más allá del control positivo: el script de secciones del catálogo tenía que encontrar las
cinco marcas S153 que #850 escribió (H_S27_1, D19, D21, D26, D30) y las encontró.

---

## Hallazgos, de mayor a menor gravedad

### F1-01 La reversión que todos los textos describen («`git revert` del PR de adopción») ya no es limpia, y nadie nombra el commit
- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md:25` y `:48`; `docs/MISSION.md:17`; `CLAUDE.md:120-121`;
  `pipeline/profiles/mirova_equivalent.yaml:266-267`; marcas S153 de D21, D26 y D30 en `docs/MIROVA_DIVERGENCES.md`.
  SCRIPT: `simular_revert.sh` / `revert_sim.out`; `buscar_850.sh` / `buscar_850.out`.
- **QUÉ PASA**: la regla de adopción pre-autoriza revertir «el mismo día» si la sombra ve una alerta de 1 MW o
  más que la réplica calla. Hoy `git revert 34cea39e` sobre main choca: CONFLICT modify/delete en
  `frontend/cambio_detector.js` y en `tests/test_cambio_detector_s153.py`, porque #851 modificó después un
  archivo que #850 creó. Si el conflicto se resuelve conservando la versión de HEAD (la salida por defecto que
  deja merge-tree), los tres flags vuelven a C0 (comprobado en el árbol simulado: `enable_test1_path: true`,
  `enable_modis_b22_primary: false`) pero el aviso del tablero sigue diciendo que la réplica usa K. Además los
  30 días que #852 reprocesó con K (commits `data(backfill)` 2026-09-18 a 2026-10-18) quedan en K. Ninguno de los
  textos lo advierte, y ninguno nombra `#850` ni `34cea39e` (0 menciones en CLAUDE.md, MISSION, catálogo, ficha,
  YAML; sólo un comentario de `frontend/index.html` dice «#850»).
- **CÓMO SE VE EN EL DASHBOARD**: tras una reversión hecha con prisa, el aviso amarillo «Desde el 18 oct 2026
  09:57 UTC la réplica usa el detector K» seguiría arriba de un tablero que ya corre C0, y la tendencia de 90
  días tendría 30 días K pegados a pasadas C0 nuevas sin marca.
- **CÓMO REPRODUCIRLO**: `bash experiments/_s155_audit/frente_1/simular_revert.sh` (sale 1 con dos líneas
  CONFLICT; `git show <árbol>:pipeline/profiles/mirova_equivalent.yaml | grep enable_test1_path`).
- **CONFIANZA**: CONFIRMADO (conflicto y contenido del árbol medidos). Que los 30 días sean K: CONFIRMADO por el
  título de #852 y de los commits de backfill, no medido record a record.
- **GRAVEDAD**: 3. Tuerce la única acción de emergencia pre-autorizada.
- **Orden de corrección**: FICHA (pública) y MISSION/CLAUDE.md (se leen primero) en el mismo PR: nombrar
  `34cea39e`, `a7a46677` (#851) y el reproceso de #852 en el procedimiento.

### F1-02 El modal «Acerca de» del tablero muestra como vigentes las métricas de S119, medidas con C0
- **ARCHIVO:LÍNEA**: `frontend/index.html:542-552` (título «Métricas de desempeño (S119, auditoría integral
  post-flip C2, 2026-07-01)»; «Recall de noches ALERTA: VIIRS375 98.4% · VIIRS750 84.5% · MODIS-cráter 100%»).
  SCRIPT: `costos_k_por_sensor.py` / `.out`.
- **QUÉ PASA**: K dejó de publicar a propósito parte de las alertas débiles de VIIRS 375 (las de un lago de lava
  o un foco sub-píxel). En las dos ventanas de la adopción, por pasada: VIIRS 375 C0 260/260 y 426/426, K 239/260
  (91,9 %) y 400/426 (93,9 %); VIIRS 750 C0 32/42 y 95/117, K 28/42 (66,7 %) y 91/117 (77,8 %); MODIS sube
  (3/8 a 5/8, 7/65 a 60/65). La definición del modal (noches) no es la de los logs (pasadas), así que los
  números no se comparan uno a uno; lo que sí es cierto es que el modal describe un detector que ya no corre y
  no lleva marca. `grep S153 frontend/index.html` no da nada en esa sección.
- **CÓMO SE VE EN EL DASHBOARD**: el operador que abre «Acerca de» lee un recall de 98,4 % en VIIRS 375 y puede
  tomar un silencio de VIIRS 375 como evidencia más fuerte de «no hay calor» de lo que hoy vale.
- **CÓMO REPRODUCIRLO**: abrir `frontend/index.html`, botón «Acerca de»; `python
  experiments/_s155_audit/frente_1/costos_k_por_sensor.py` (control positivo: reproduce 239/260, 400/426, 21/832
  y 37/1010 que la ficha cita).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. Puede inflar la confianza en un silencio de VIIRS 375 en una noche de actividad débil.
- **Orden**: primero que todo lo interno, porque es lo único de esta lista que ve el operador.

### F1-03 Los encabezados de D21 y D30 siguen diciendo «ABIERTA», y el proyecto declara que el estado vivo son los encabezados
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:2601` (D21 «**ABIERTA** (... ningún brazo cumple aún ...)»),
  `:2849` (D30 «**ABIERTA** (... descrita, sin decisión)»), `:2745` (D26 «ABIERTA, efecto nulo bajo la conectiva
  `min`»). La regla: `CLAUDE.md:1822` («el estado vivo son los encabezados de cada D en el catálogo») y
  `docs/MISSION.md:208`. SCRIPT: `secciones_divergences.py` / `.out`.
- **QUÉ PASA**: #850 puso la marca correcta debajo de cada encabezado (D21 «ADOPTADA en producción», D30
  «RESUELTA en producción»), pero el encabezado dice lo contrario. A113 (d) cuenta eso como texto sin marcar. Una
  sesión que lista el catálogo por encabezados (`grep "^## D"`, que es como yo lo recorrí primero) ve D21 y D30
  abiertas y sin decisión. D26: el «efecto nulo bajo `min`» describe una conectiva que ya no corre; su marca dice
  «abierta y sin medir bajo `max`», que es lo que debería decir el encabezado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -n "^## D2[16]\|^## D30" docs/MIROVA_DIVERGENCES.md`.
- **CONFIANZA**: CONFIRMADO. (El orquestador ya sabía lo de D21; se agrega D30 y D26 y la razón por la que el
  encabezado pesa más que la marca.)
- **GRAVEDAD**: 3. Puede reabrir D21 o D30 como trabajo pendiente, o diseñar un A/B con C0 de control.

### F1-04 El cierre de D11 estaba condicionado a la banda 21; K cumplió la condición y el cierre sigue en pie en tres lugares
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:1492` (D11 «CERRADA S114, CONDICIONADA S138 (el
  «irreducible a 1 km» ... valen sólo bajo banda 21 primaria y compuerta de 3 K, D21 y D22, abiertas ...)»);
  `docs/MISSION.md:215-217` («cara MODIS far→summit CERRADA S114 (irreducible a 1 km ...)»); `CLAUDE.md:1020`
  (A82: «Sólo Láscar; en los otros diez volcanes no está medido»). SCRIPT: lectura de
  `experiments/_s153_fk_v2/v1.log` y `v2.log`, sección 9.
- **QUÉ PASA**: la idea de D11/A82 era que a 1 km un foco débil y el gradiente frío cumbre contra valle tibio son
  el mismo objeto, y por eso MODIS sobre-detecta sin remedio. Con la banda 22 (diez veces menos ruido) y `max`,
  K midió MODIS en los 11 volcanes: fuera de Láscar, publicación en negativos limpios C0 107/825 a K 7/825 (V1)
  y 242/2173 a 18/2173 (V2). La ficha pública ya lo dice (`docs/FICHA_SDA_VRP_CHILE.md:33`, nota v1.9). El
  catálogo, MISSION y A82 no: siguen con «cerrada», «irreducible» y «no medido en los otros diez». El D11 tiene
  una sola marca S153 y es dentro del texto, sobre la conectiva (`:1557`), no sobre el cierre.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `awk '/== 9\./,/== VEREDICTO/' experiments/_s153_fk_v2/v2.log` (bloque «MODIS fuera de
  Lascar»).
- **CONFIANZA**: CONFIRMADO que el texto contradice la medición. Qué hacer con D11 (reabrir, re-cerrar como
  resuelta por K, medir la cara de posición) no lo decide esta auditoría.
- **GRAVEDAD**: 3. El «no reabrir» de A82/D11 apaga trabajo, y la ficha pública y el catálogo interno ahora dicen
  cosas distintas del mismo límite.

### F1-05 La cabecera del perfil de producción describe a C0
- **ARCHIVO:LÍNEA**: `pipeline/profiles/mirova_equivalent.yaml:1-15`: «clon literal MIROVA con Test 1
  integrated-ROI activo en los 3 sensores que MIROVA usa (MODIS B21 + VIIRS I04 + VIIRS M13)», «vent-path OFF
  (... reemplazado por Test 1)», «Test 1 integrated-ROI ON en MODIS B21 + VIIRS I04 + M13 (S27-S29)»;
  `:19-21` description «clon MIROVA literal ... Sin parches».
- **QUÉ PASA**: lo primero que lee quien abre el perfil operacional dice lo contrario de las líneas 268, 271 y
  578, que sí llevan la marca S153. Sin marca al inicio.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `sed -n 1,21p pipeline/profiles/mirova_equivalent.yaml` contra `leer_flags.out`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F1-06 La ficha pública omite el costo de K en VIIRS 750 y dice más de lo que la auditoría espacial probó
- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md:25` («Costo conocido: dejan de publicarse 21 de 260 y 26 de
  426 alertas de VIIRS 375 m ...»; «una auditoría de las pasadas donde el foco publicado se movió (ninguna
  protegida queda sobre otro objeto)») y `:48`. Contra: `costos_k_por_sensor.out`;
  `experiments/_s153_fk_v2/a61/INFORME.md:141-150`.
- **QUÉ PASA**: (a) en VIIRS 750 K deja de publicar 4 de 42 y 4 de 117 alertas (netas; ninguna protegida: 12/12
  y 42/42). La ficha sólo declara el costo de VIIRS 375; de VIIRS 750 sólo cuenta la mejora en negativos.
  (b) La auditoría A61 dice «no encontré ninguna» y aclara en la misma sección que «que el objeto publicado por K
  sea el de MIROVA» queda SIN VERIFICAR en las 14 protegidas, y que en Tupungatito 09-14 «ninguno de los dos
  brazos está en el objeto de MIROVA». La ficha lo convierte en «ninguna protegida queda sobre otro objeto».
- **CÓMO SE VE EN EL DASHBOARD**: invisible; lo lee un tercero (CPLT, SERNAGEOMIN).
- **CÓMO REPRODUCIRLO**: `python experiments/_s155_audit/frente_1/costos_k_por_sensor.py`; leer a61 §5.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2. Es el documento de transparencia; una omisión ahí es un dato que el tercero no tiene.

### F1-07 «El laboratorio es idéntico al operacional» es falso desde S150 y K; y con K el laboratorio ve MENOS que producción en MODIS
- **ARCHIVO:LÍNEA**: `pipeline/profiles/experimental.yaml:26-30` (description: «hoy es idéntico al operacional
  salvo el directorio de salida»), que contradice su propio bloque `:63-76`; `CLAUDE.md:1483-1484` (A117);
  `tests/test_guard_laboratorio_no_mas_ciego_s147.py:19`; `tests/test_viirs_path_d.py:71`. Siete perfiles
  derivados más dicen «idéntico al operacional» y resuelven C0 (`flags_todos_perfiles.out`).
- **QUÉ PASA**: `experimental` resuelve C0 (`leer_flags.out`). Y la tensión que nadie escribió: A117 dice que el
  laboratorio nunca puede ver menos que el operacional, pero con el congelamiento S150 y K, en MODIS el
  laboratorio publica 7 de 65 alertas y 6 de 39 protegidas (V2) contra 60 de 65 y 39 de 39 de producción. El
  guard de A117 sólo compara pisos de magnitud, así que sigue verde (`pytest_lab.out`: 13 passed).
- **CÓMO SE VE EN EL DASHBOARD**: invisible en la vista operacional.
- **CÓMO REPRODUCIRLO**: `VRP_PROFILE=experimental PYTHONPATH=. python experiments/_s155_audit/frente_1/leer_flags.py`;
  `python -m pytest -q -p no:cacheprovider tests/test_guard_laboratorio_no_mas_ciego_s147.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2. Quien lea A117 o la descripción creerá que la sombra que vigila la reversión es una copia
  inútil de producción.

### F1-08 A69 y el cuerpo de D11 dicen que el Test 1 sobre MIR absoluto sigue vivo en los tres sensores
- **ARCHIVO:LÍNEA**: `CLAUDE.md:874-882` (sub-punto S125 de A69: «La causa raíz que A69 describe sigue viva en los
  3 sensores»); `CLAUDE.md:856` («nuestro `Test1 integrado`»); `docs/MIROVA_DIVERGENCES.md:1504-1507` (D11:
  «Nuestro Test1 integrado mide ... capta el valle tibio»); cabecera `pipeline/process_modis.py:14-15`
  («sobre-deteccion difusa irreducible a 1 km»).
- **QUÉ PASA**: el camino que A69 culpa sólo corre bajo `ENABLE_TEST1_PATH`, hoy False, y no dispara en ningún
  record nuevo (0 de 3.661). Lo que la ficha v1.9 dice bien (el límite «sigue descrito porque no se ha medido
  cuánto queda en los caminos que siguen activos») no bajó a A69 ni a D11.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python experiments/_s155_audit/frente_1/efecto_k_en_datos.py`; grep de
  `compute_test1_mir(` en `pipeline/`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F1-09 Decisiones que se justificaron con «el Test 1 cubre ese rol» quedaron sin su argumento
- **ARCHIVO:LÍNEA**: `pipeline/profiles/mirova_equivalent.yaml:189-194` (vent-path OFF: «Coppola 2015 §2.2 Test 1
  integrated-ROI cumple rol equivalente para sub-pixel»), `:398-421` (camino de BT OFF: «Sin bt_path, las
  detecciones son solo del path Test 1 ... + dnti contextual»), `:9`; `docs/MISSION.md:260` («sub-pixel debe ir
  por Test 1»), `docs/MISSION.md:203-204` («Resueltas: ... D4 recall sub-pixel (S27)»);
  `docs/MIROVA_DIVERGENCES.md:800` (H_S27_1 «(S27 cierre D4)»).
- **QUÉ PASA**: el apagado del vent-path y del camino de BT, y el cierre de D4 (recall sub-píxel), se apoyaron en
  que el Test 1 integrado recogía la señal sub-píxel. Con K eso ya no corre, y el costo de K cae justo ahí (19
  de las 21 alertas de VIIRS 375 que deja de publicar en V1 están bajo 1 MW). La marca global de MISSION
  (`:13-15`) cubre «frases que describan el detector con el Test 1», pero no saca la consecuencia: D4 deja de
  estar cerrada por su mecanismo original y los dos apagados quedan sin la justificación escrita. No sostengo
  que haya que reabrirlos (la regla de adopción pesó ese costo); sostengo que el texto da un argumento que ya no
  existe.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (lectura).
- **GRAVEDAD**: 2.

### F1-10 Comentarios de código que invitan a «corregir» `max` de vuelta a `min`, y docstrings con la banda 21 primaria
- **ARCHIVO:LÍNEA**: `pipeline/detection_context.py:933-937` («Bug fix S46 Task 5: antes usábamos `max` (AND
  lógico), ahora `min` (OR lógico paper-correct)»); `:513-524` («Es el comportamiento por defecto ... Adopción
  sujeta a A/B»); `pipeline/profile.py:707-724` («Adopción sujeta a A/B»), `:631-633` (B22: «Arranca OFF; la
  adopción va por A/B»), `:171-175` (Test 1 «Coppola 2015 Eq.1»); `pipeline/process_modis.py:28-30` (docstring:
  «Band 21 ... primary MIR hotspot channel / Band 22 ... used where Band 21 is saturated»), `:561-562`
  («(21 primary, 22 fallback)»), `:727-728` («Test 1 integrated-ROI MIR (Coppola 2015 §2.2 Eq.1) en MODIS Banda
  21»).
- **QUÉ PASA**: quien audite fidelidad al paper sobre `second_pass_adjacent` lee que `max` fue un bug y `min` lo
  correcto, sin saber que producción corre `max` por decisión aprobada. Los defaults del cargador siguen en
  False (correcto como default), pero el texto los presenta como pendientes de A/B.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO (lectura).
- **GRAVEDAD**: 2 el de `detection_context.py:933-937`; 1 los demás.

### F1-11 Cabeceras FICHA de los módulos (transparencia CPLT) siguen describiendo el Test 1 integrado como parte del método MIROVA en producción
- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:5-6` («Tests contextuales y de ROI integrado de Coppola 2016a»);
  `pipeline/test1_integrated.py:4` («Uno de los 3 criterios MIROVA») y `:7` («Coppola 2015 Eq.1»), que
  contradicen su propia `:12` («DETECTOR PROPIO ... no del paper») y no dicen que el módulo no corre en
  producción; `pipeline/process_viirs.py:6` («deteccion contextual/ROI»).
- **QUÉ PASA**: la cabecera FICHA es lo que el estándar de transparencia del workspace pide mantener al día por
  bloque. Hoy atribuye a Coppola 2016a un detector que no es del paper y que además está apagado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; lo lee quien audite el código público.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F1-12 En main, el último bloque de arranque es el de S150 (antes de K)
- **ARCHIVO:LÍNEA**: `CLAUDE.md:20-22` (primer comando: `ls tasks/BLOQUE_ARRANQUE_S*.md | sort -V | tail -1`).
  Comando: `git ls-tree --name-only origin/main tasks/` da hasta `BLOQUE_ARRANQUE_S150.md`; `loop/activo` tiene
  S152 a S155 y `PLAN_S155.md`.
- **QUÉ PASA**: una sesión que arranca en main como dice CLAUDE.md lee como plan vigente un traspaso del
  2026-10-14, que habla de K como brazo pendiente de despachar. CLAUDE.md no menciona `loop/activo`. (Aparte, sin
  relación con K: `CLAUDE.md:23` dice «hoy: AUDIT_S123.md» y la última en main es AUDIT_S150.)
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F1-13 `docs/INDEX.md` no registra la adopción y deja sin marca el «NO ADOPTAR» de B22
- **ARCHIVO:LÍNEA**: `docs/INDEX.md` (último commit 2026-10-14, `88e97d84e`); `:109` («s133/AB_B22_VEREDICTO.md:
  A/B de B22: NO ADOPTAR»), `:26` (batería S137 «ninguno cumple»). 0 menciones de `REGLA_ADOPCION`, `_s153_fk_v2`,
  ficha v1.9 o el tag.
- **QUÉ PASA**: el índice maestro, que se presenta como «leer estos primero», no lleva a la evidencia de K y deja
  vivo el veredicto contrario sobre B22.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### F1-14 Ajustes del Test 1 «ADOPTADOS» que hoy no actúan, y D24 con el orden de bandas de C0
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:1434` (D10 ctxpeak «ADOPTADO S100», sin marca S153);
  `pipeline/profiles/mirova_equivalent.yaml:312-397` (S100 ctxpeak, S39 `lbg_global`, S112 prioridad y anillo
  intermedio, todos «ADOPTADO»); `CLAUDE.md` A100 («nunca apagarlo solo»); D24 en
  `docs/MIROVA_DIVERGENCES.md:2690` («el NaN de B21 cae a B22»), contra `pipeline/process_modis.py:337-339`.
- **QUÉ PASA**: el filtro contextual y el keep-peak exigen `final_hotspot_source == "test1"`
  (`pipeline/process_viirs.py:1876`), que sin Test 1 no ocurre: no actúan. Para el anillo intermedio y el
  `lbg_global` no tracé la cadena completa (se calculan en `:1904-1923` y alimentan el recálculo del Test 1):
  inertes es SOSPECHA. En D24, con B22 primaria el NaN de B22 cae a B21, no al revés; la física del paroxismo
  (la 21 saturada en el foco) sigue valiendo.
- **CONFIANZA**: CONFIRMADO para filtro contextual y keep-peak; SOSPECHA para los otros dos.
- **GRAVEDAD**: 1.

### F1-15 Menores del tablero
- **ARCHIVO:LÍNEA**: `frontend/index.html:1624` («con K (#850) todos los records son ctx_cluster»);
  `frontend/cambio_detector.js:41` (el aviso dice sólo «sin el Test 1 integrado»). SCRIPT: `eruption_tras_k.py`.
- **QUÉ PASA**: de 557 records con hotspot procesados tras el merge, 26 son `eruption` (todos MODIS: Chillán 13,
  Puyehue 8, Láscar 2, Villarrica 2, Planchón 1). No daña el marcador: en los 26 el `anomaly_pixels[0]` coincide
  con el `final_hotspot` (0,0 km). El aviso nombra uno de los tres cambios de K; para MODIS, el que más cambia
  (banda 22) no aparece.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

---

## Orden de corrección sugerido (por dónde se lee primero)
1. Tablero: F1-02 (modal) y F1-15 (aviso).
2. Ficha pública: F1-06 y el procedimiento de reversión de F1-01.
3. `CLAUDE.md` y `docs/MISSION.md`: F1-01 (reversión), F1-04 (A82, D11), F1-07 (A117), F1-08 (A69), F1-09 (D4),
   F1-12 (puntero al traspaso).
4. `docs/MIROVA_DIVERGENCES.md`: encabezados de F1-03, D11 de F1-04, D10/D24 de F1-14.
5. Cabeceras y comentarios: YAML de producción (F1-05, F1-09), `experimental.yaml` (F1-07), FICHA de módulos
   (F1-11), `detection_context.py` (F1-10).
6. `docs/INDEX.md` (F1-13).

## VERIFICADO LIMPIO
- **Flags de producción**: K, leído de `pipeline.profile` (`leer_flags.out`); el laboratorio C0 (control).
- **K corre en los datos**: 0/3.661 con `triggered_test1` tras el merge, 758/1.807 antes (`efecto_k_en_datos.out`).
- **Números de la ficha sobre VIIRS 375, MODIS y negativos de VIIRS 750**: coinciden con la sección 9 de `v1.log`
  y `v2.log` (`costos_k_por_sensor.out`).
- **Marcas S153 bien puestas al inicio**: CLAUDE.md, punto «NTI / dNTI contextual» (`:112-123`) y su (b) (`:138`);
  MISSION, marca global (`:7-17`) y sección del Test 1 (`:328`); catálogo, H_S27_1, D19, D21, D26, D30
  (`secciones_divergences.out`); YAML, `:262-271` y `:575-578`. Ninguna miente sobre lo que corre.
- **Ficha v1.9**: cabecera, «Funcionamiento», sesgo topográfico, sobre-detección difusa e historial describen K
  (salvo lo de F1-01 y F1-06).
- **Hora del aviso del tablero**: `CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"` es la hora del merge
  (06:57:30 -0300); el aviso está en las tres vistas vivas (`diario.html:10`, `index.html:12`, `mosaico.html:24`).
- **Tag de reversión**: existe, y el árbol revertido restaura los tres flags de C0 (`revert_sim.out`).
- **`docs/META_RULES_S80.md`**: no afirma nada sobre el Test 1, la conectiva ni la banda (grep sin coincidencias).
- **Cita A10 (`isValidDetection` en `frontend/index.html:1595`)**: correcta.
- **Guards del laboratorio**: 13 passed (`pytest_lab.out`); miden pisos, no detector (ver F1-07).
