# Auditoría S179, frente D: planes pendientes contra la misión

ESTADO: TERMINADO. Informe completo, con sus scripts y salidas en la misma carpeta.

## 0. Encabezado

- **Hora del servidor**: empecé a las 2026-11-11 01:19:56 UTC y cerré las mediciones a las 01:44:03 UTC (cabecera `Date` de GitHub). La hora de cierre del informe está al final.
- **Base sobre la que medí**: código `main` `438a60a1e`; documentos del loop `0472cd95e`. Lo que vive fuera de main lo rotulo así: plan de reemplazo `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` en el PR #981 (`62ccb8830`, fuera de main); `docs/AUDIT_S175.md` en `origin/claude/relaxed-almeida-d17378` (`37670d910`, PR #955, fuera de main); PR #974 (`bbbe2068d`) y #983 (`e68819484`), fuera de main. Insumos de GitHub: los de `D:\vrp-trabajo\temporales\s179-audit\insumos\` (2026-11-10 20:37:28 UTC) más 5 llamadas mías a la API pública, sin credencial (guardadas como `api_*.json` en CARPETA).
- **Modelo y esfuerzo**: Claude Fable 5.2 (`claude-fable-5-2`). El nivel de esfuerzo no lo puedo leer desde dentro de la sesión: quien orquesta lo ve en el transcripto. No lancé subagentes.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\d\`. Temporal: `D:\vrp-trabajo\temporales\s179-audit\d\` (339 MB: copia de `data/` de la base sacada con `git show`, la unión D2 más D4 y las simulaciones).
- **Inventario de decisiones**: lo armé leyendo enteras las entradas S172 a S178 de `tasks/LOOP_OBJETIVOS.md` §6 (líneas 570 a 1689 de `0472cd95e`) y con `python inventario_frases.py D:\vrp-trabajo\temporales\s179-audit\d\bitacora_s172_s178.md inventario_frases_bitacora.txt` (55 frases citadas en 52 entradas). Los bloques de arranque S178 y S179 los leí enteros; los S172 a S177, por búsqueda de palabras (34, compuerta, reemplazo, Pages, preliminar, B1, B2, encendido, historia).
- **Qué NO miré** (mi silencio ahí no es «todo bien»):
  - No abrí `docs/PLAN_AUDITORIA_S179.md` ni nada bajo `experiments/_s179_*` fuera de mi carpeta.
  - No corrí la suite de pruebas ni repetí las simulaciones de la suite del §4.2 del plan de reemplazo.
  - No abrí el tablero en un navegador. Lo que digo del tablero sale de ejecutar con node el predicado y los módulos reales de `frontend/`.
  - No tengo los artefactos de P4 (enero, abril a septiembre y 17 de octubre a 9 de noviembre de 2026): no están bajados. Todo lo que mido sobre «qué publicaría la vía» vale sólo para febrero y marzo de 2026, 1 a 16 de octubre de 2026 y 2025.
  - No miré ninguna imagen de MIROVA. Si MIROVA alertó en el cráter en una pasada dada lo digo desde la tabla y el OCR del repo.
  - No leí entero el lector de la retrospectiva (`experiments/_s172_retro_paquete/leer_retro.py`), sólo las líneas que cito. No juzgo la lectura con candado: es de otro frente.
  - No leí el diseño `docs/superpowers/specs/2026-11-08-encendido-v375e-design.md` entero (sólo busqué la regla de posición: no la nombra).
  - No revisé la salud de las corridas de `sombra-34.yml` (no hay insumo), ni `scripts/vigilar_sombra_34.py`, ni la capacidad del NRT con 45 volcanes.
- **Un error mío, ya corregido**: cuatro salidas `.json` de mis scripts (M3, M3b, M4 y M5) quedaron escritas por un rato dentro de la instantánea compartida `D:\vrp-trabajo\temporales\s179-audit\main\`, porque los scripts cambian de directorio antes de escribir. Las moví a CARPETA, comprobé que la instantánea quedó sin archivos míos y corregí los scripts (resuelven la ruta de salida antes de cambiar de directorio). No toqué ningún otro archivo de esa carpeta.

## 1. En una pantalla

1. **El plan de reemplazo de la historia (#981) no se puede ejecutar como está escrito.** Además de los 3 huecos que ya anotó su verificador, medí dos efectos nuevos: el paso de MODIS deja ciega la vigilancia de la guardia K de MODIS (su control pasa de 167 pares a 0 y el veredicto de VERDE a VIGILANCIA_CIEGA), y el paso de VIIRS corre el «encendido» que define la regla sellada al 2026-11-08 18:04 UTC y borra también su control (223 pares a 0).
2. **El encendido de VIIRS 375 (B1) da por tomada la regla de posición.** La retrospectiva decidió VIIRS 375 con la posición «cercano»; producción escribe «radiante» y B1 no cambia eso. Con el predicado del tablero, la vía deja sin publicar 5 de 72 alertas protegidas de MIROVA que K sí publica (febrero, marzo y octubre de 2026), las 5 sólo del OCR.
3. **Lo que sí se sostiene.** En MODIS el reemplazo no quita ninguna protegida publicada (gana 3) y apartar las 217 pasadas K sin par no quita nada que hoy se publique. Las cifras del plan se reproducen (42.389 records, 217, 787, 1.574 y 1.563).
4. **El plan de los 34 volcanes quedó viejo.** Sus compuertas A y B ya no describen lo que pasó (sombra con las vías desde el 2026-11-02, página pública desde el 2026-11-09) ni lo que se podrá medir después de B1 y B2. Su fase 4 escribe los volcanes nuevos en la carpeta de la réplica, contra `docs/MISSION.md`.
5. **GitHub Pages.** El despliegue ya copia 799 MB medidos en git, de los cuales 586 MB son carpetas que el tablero no lee; el artefacto real pesa 89 MB comprimido. Sacar esas carpetas del despliegue da el margen que el plan necesita. Guardia K de VIIRS: 0 de 3 noches verdes en la base, 1 de 3 a las 00:12 UTC del 11-11.

## 2. Hallazgos (lo peor primero)

### 551
- **TÍTULO**: B1 enciende en producción la posición «radiante», pero la evidencia que autoriza encender VIIRS 375 se midió con «cercano»; con el predicado del tablero la vía calla 5 de 72 protegidas que K publica.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m4_reemplazo_efecto.py` con salida `m4_reemplazo_efecto_salida.txt`; `m5_cinco_protegidas_v375.py` con salida `m5_cinco_protegidas_v375_salida.txt` (CARPETA). Código: `experiments/_s172_retro_paquete/leer_retro.py` l. 1274 en `438a60a1e`; `tasks/LOOP_OBJETIVOS.md` l. 2256, 2300 y 3005 en `0472cd95e`.
- **QUÉ PASA**: hay noches en que un píxel tibio en el cráter convive con una fuente más fuerte a 13 a 23 km (otro centro, un incendio, un artefacto). MIROVA suma toda la energía y, según la referencia del repo, informa la alerta a 1 a 3 km del volcán. La vía también suma todo (su VRP calza con el de MIROVA: 2,199 contra 2,21 MW en Isluga el 2026-03-20), pero pone el punto del record en la fuente más radiante, lo etiqueta `far` y el tablero no lo publica. K publica el píxel del cráter. El lector de la retrospectiva decidió VIIRS 375 con el brazo «V-cercano» (`leer_retro.py` l. 1274, TEXTO: «brazo = {"MODIS": "V", "VIIRS375": "V-cercano", "VIIRS750": BRAZO_DE[posicion_v750]}[sensor]»). «Cercano» se calcula en el lector, fuera de `pipeline/`. El PR #974 sólo cambia el flag del perfil (lo comprobé con `git diff 438a60a1e...bbbe2068d`: ningún cambio en `pipeline/*.py` ni en `frontend/`), así que producción seguirá escribiendo «radiante». El pre-registro de V375-E ya había dado, en su ventana, «cercano CUMPLE (falta la sombra), radiante y pico NO CUMPLE» (`tasks/LOOP_OBJETIVOS.md` l. 2300, TEXTO).
- **Medido** (ventanas F26 2026-02-01 a 03-31 y DM 2026-10-01 a 10-16; vía = records de D2; K = `data/mirova_equivalent/` de `438a60a1e`; «publica» = predicado del tablero con node; protegida = lectura A con D-9 SN, referencia de `438a60a1e`): VIIRS 375, F26, 49 protegidas, K publica 47 y la vía 44; DM, 23 protegidas, K publica 23 y la vía 21. Protegidas que K publica y el record de la vía no: Isluga 2026-03-20 05:06 (2,21 MW), Isluga 2026-03-24 05:30 (1,51), Láscar 2026-03-15 05:00 (1,54), Isluga 2026-10-03 05:18 (1,62), Láscar 2026-10-01 05:18 (1,2). En las 5 el record de la vía trae `distance_class: far` y el punto a 13,0 a 23,3 km. Las 5 filas de MIROVA son sólo del OCR (`ALERTA_TERMICA_OCR`, sin fila de la tabla); 4 son de Suomi NPP antes del 2026-10-09, que el proyecto trata como referencia sospechosa (la distancia del OCR puede ser de otra pasada); la quinta es NOAA-21. La lectura con candado contó 26 protegidas en VIIRS 375 y ninguna perdida: no la contradigo, usa otra referencia, la regla N-3 y el brazo cercano. Lo que digo es que ese brazo no es el que verá el operador.
- **CÓMO SE VE EN EL DASHBOARD**: en esas noches la pasada de VIIRS 375 queda sin punto en Isluga o Láscar, mientras MIROVA muestra una alerta de 1,2 a 2,2 MW y K (hoy) muestra un punto de 0,04 a 0,38 MW en el cráter. Después del encendido, la vigilancia de la guardia lo informaría como `REVERSION_CANDIDATA` (la regla sellada, §4.2, dice que N-3 ya no aplica).
- **CÓMO REPRODUCIRLO**: `python m4_reemplazo_efecto.py D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base C:/Users/nmend/vrp-temporales/s177_d2 C:/Users/nmend/vrp-temporales/s177_d4 D:/vrp-trabajo/temporales/s179-audit/d/union_d2_d4 m4_reemplazo_efecto_salida.json` y después `python m5_cinco_protegidas_v375.py D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base D:/vrp-trabajo/temporales/s179-audit/d/union_d2_d4 m4_reemplazo_efecto_salida.json m5_cinco_protegidas_v375_salida.json`. Caso tipo: Isluga, VIIRS_SNPP, 2026-03-20 05:06 UTC.
- **CONFIANZA**: CONFIRMADO lo medido (control positivo de M4 en verde; en M5 el record K de las 5 pasadas sale publicado). SOSPECHA que MIROVA haya alertado de verdad en el cráter en esas 5 pasadas: hay que mirar la cabecera de la imagen (A61).
- **GRAVEDAD 1-5**: 4. Es el caso que la regla sellada llama costo («un foco incipiente, sub-píxel»): un píxel débil de cumbre queda callado cuando hay una fuente mayor lejos. Y si la referencia está mal, produce una reversión candidata falsa en las primeras semanas.

### 552
- **TÍTULO**: El paso de MODIS del plan de reemplazo deja ciega la vigilancia de la guardia K de MODIS hasta el 2027-03-02.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m3_vigilancia_tras_reemplazo.py` con salida `m3_vigilancia_tras_reemplazo_salida.txt`. Código: `scripts/vigilancia_guardia_modis.py` l. 296 a 313 (el nulo), l. 374 a 379 (`avisos_nulo`) y l. 526 a 528 (veredicto) en `438a60a1e`.
- **QUÉ PASA**: la guardia K corre al lado de producción para ver si la vía calla algo que K publicaba. Su control compara, en los 14 días anteriores al encendido, la guardia (K) con producción (K): tienen que publicar lo mismo. El reemplazo convierte esos records de producción en records de la vía, y el vigilante excluye del control todo record de la vía (l. 303). El control queda con 0 pares, eso es un aviso, y un VERDE con aviso se informa como VIGILANCIA_CIEGA.
- **Medido**: con los datos de la base, el `evaluar()` real da VERDE, encendido 2026-11-02 20:11:43, nulo de 167 pares y 0 distintas, igual que lo que el workflow dejó guardado en `data/audit_continuous/guardia_modis_latest.json` (control). Con 747 records K de MODIS del 2026-10-01 al 11-02 marcados como de la vía (lo que hace el paso 8 del plan, regla A): VIGILANCIA_CIEGA, nulo 0 pares, aviso «el nulo de la guardia no tiene pasadas pareadas en los 14 días previos al encendido». El encendido no se mueve en MODIS, porque los records del reproceso se procesaron después (desde el 2026-11-08 18:04 UTC).
- **CÓMO SE VE EN EL DASHBOARD**: invisible para el operador. Para quien vigila: un issue de «vigilancia ciega» todos los días, y un aviso real de ceguera (guardia sin datos, referencia detenida) quedaría con el mismo veredicto que este aviso permanente. Una candidata a reversión sí seguiría saliendo (el aviso no la tapa).
- **CÓMO REPRODUCIRLO**: `python m3_vigilancia_tras_reemplazo.py D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base D:/vrp-trabajo/temporales/s179-audit/d/sim_modis m3_vigilancia_tras_reemplazo_salida.json`. Los 11 Tier A, MODIS, ventana 2026-10-19 a 2026-11-10.
- **CONFIANZA**: CONFIRMADO para el nulo, los avisos y el veredicto (dependen sólo de la marca). SIN DATO para lo que depende de lo que la vía publica en esas pasadas (`borde_del_encendido`): la simulación conserva el contenido de K.
- **GRAVEDAD 1-5**: 3. No calla una alerta, pero deja sin lectura la red que sostiene la reversión pre-autorizada de MODIS mientras su plazo sigue abierto (11 de 29 protegidas vistas; vence el 2027-03-02).

### 553
- **TÍTULO**: El paso de VIIRS del plan de reemplazo corre el «encendido» de la regla sellada a la fecha del reproceso y borra el control de la guardia K de VIIRS.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m3b_vigilancia_viirs_tras_reemplazo.py` con salida `m3b_vigilancia_viirs_tras_reemplazo_salida.txt`; `m4_reemplazo_efecto_salida.txt` (líneas `processed_utc`). Regla: `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md` §4.1 (l. 55 a 59) y §4.6 en `438a60a1e`; código `scripts/vigilancia_guardia_modis.py` l. 124 a 146.
- **QUÉ PASA**: la regla sellada dice (§4.1, TEXTO): «Encendido de cada sensor = el menor `processed_utc` de un record de producción de ese sensor con `via_codigo_mirova: true`». Los records del reproceso (D2, D4 y P4) se procesaron entre el 2026-11-08 18:04 UTC y el 2026-11-10, antes de cualquier encendido de VIIRS. Si se copian a la serie después de B1, el vigilante leerá como encendido el 2026-11-08 18:04:23 UTC y contará desde ahí el plazo de 120 días y las cotas de 14 y 17. Y el control (nulo) se queda sin pares, igual que en 552.
- **Medido**: menor `processed_utc` de los records VIIRS 375 de la vía en D2 y D4: 2026-11-08T18:04:23Z (VIIRS 750: 18:04:36Z). Simulación sobre la base con un encendido ficticio el 2026-11-09 12:00 UTC: sólo B1 da encendido 2026-11-09 12:00:00, nulo 223 pares, VERDE (control); B1 más reemplazo da encendido 2026-11-08 18:04:23, vencimiento corrido del 2027-03-09 al 2027-03-08, nulo 0 pares y VIGILANCIA_CIEGA. Con el encendido real (no antes del 2026-11-13 si se esperan las 3 noches), el corrimiento sería de 4 días o más.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. En la vigilancia: plazo y cotas contados desde una fecha en que VIIRS todavía era K, y «vigilancia ciega» diaria.
- **CÓMO REPRODUCIRLO**: `python m3b_vigilancia_viirs_tras_reemplazo.py D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base D:/vrp-trabajo/temporales/s179-audit/d/sim_viirs m3b_vigilancia_viirs_tras_reemplazo_salida.json`. Los 11 Tier A, VIIRS 375.
- **CONFIANZA**: CONFIRMADO (controles S0 y S1 en verde). El flag de producción se simuló encendido; reversión, Muy Bajo y sobre-publicación quedan SIN DATO en la simulación.
- **GRAVEDAD 1-5**: 3.

### 554
- **TÍTULO**: El plan de reemplazo no cuenta qué deja de publicarse, y lo aplicaría sobre meses que nadie leyó contra MIROVA.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: plan `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` (`62ccb8830`, fuera de main) l. 6 a 7 y l. 272 a 274; `m4_reemplazo_efecto_salida.txt`.
- **QUÉ PASA**: reemplazar la historia cambia lo que el operador ve hacia atrás: pasadas que hoy muestran una anomalía dejan de mostrarla y otras empiezan. El plan dice de sí mismo (l. 6 a 7, TEXTO): «No se leyó ningún veredicto ni se comparó la vía con K o con MIROVA». Su ensayo (paso 6) informa reemplazados, apartados, caídas a K, agregados y sha256, pero no cuántas pasadas publicadas cambian ni si alguna es protegida. `docs/MISSION.md` l. 113 (TEXTO): «En la réplica no se acepta ningún cambio que pierda una alerta protegida». La lectura con candado cubrió F26, DM y R25; las ventanas de P4 no tienen lectura.
- **Medido** (pasadas nocturnas con record en K y en la vía, D2 más D4, predicado del tablero): VIIRS 375, K publica 4.319 de 17.212; con la vía dejarían de publicarse 935 y empezarían 152 (en 2025: 737 y 113), más 1 pasada sin par que K publica. MODIS: K publica 398 de 8.597; dejarían 107 y empezarían 30. VIIRS 750: K publica 1.316 de 17.060; dejarían 260 y empezarían 211. En F26 y DM, donde hay tabla de MIROVA, ninguna de las pasadas MODIS que dejan de publicarse es una alerta de MIROVA; en VIIRS 375, 5 son protegidas (hallazgo 551) y 9 son alertas bajo 1 MW. En 2025 no hay tabla: ahí sólo se puede decir cuánto cambia.
- **CÓMO SE VE EN EL DASHBOARD**: en la serie histórica de VIIRS 375 desaparecería cerca de una de cada cinco pasadas con punto (en lo medido). Casi todo es sobre-publicación de K en noches sin alerta de MIROVA, que es lo que se busca; pero el plan no obliga a comprobarlo antes de pedir el sí.
- **CÓMO REPRODUCIRLO**: el comando de M4 del hallazgo 551. Volcanes: los 11 Tier A (10 en 2025).
- **CONFIANZA**: CONFIRMADO en F26, DM y R25. SIN DATO en enero, abril a septiembre y 2026-10-17 a 11-09 (artefactos de P4 sin bajar).
- **GRAVEDAD 1-5**: 3.

### 555
- **TÍTULO**: Un solo record K que quede antes de la vía mueve la línea de «cambio de detector» a una fecha falsa en todas las vistas; y la comprobación que el plan propone ya no puede fallar.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m7_linea_via_con_k_residual.js` con salida `m7_linea_via_con_k_residual_salida.txt`; `frontend/cambio_detector.js` l. 211 a 226 y l. 273 a 303 en `438a60a1e`; plan (`62ccb8830`) l. 196 a 200 y l. 278.
- **QUÉ PASA**: el tablero dibuja una línea vertical donde la serie pasa de K a la vía, y toma la fecha más temprana de todos los volcanes cargados. Si Tupungatito queda con K antes del 2026-02-23 (opción 2 del plan) la línea de MODIS cae en el 2026-02-23 en todos los volcanes. Si se conserva una sola pasada K de borde (regla B), la línea cae en esa fecha de 2025. Además, el plan justifica apartar esas pasadas con un aviso naranja de texto que ya no existe: #984 lo quitó de la página y dejó sólo la línea. Su comprobación «las tres vistas sin `#aviso-cambio-via-modis`» pasa siempre, haya o no K residual.
- **Medido** (módulo real): Villarrica hoy da 2026-11-02T01:15Z (control); con MODIS entero de la vía, `null` (control); Tupungatito con K antes del 02-23, 2026-02-23T02:35Z; una pasada K conservada el 2025-06-01, 2025-06-01T06:45Z; `notarRecords` con Villarrica toda de la vía y Tupungatito con K: línea en 2026-02-23.
- **CÓMO SE VE EN EL DASHBOARD**: una línea vertical rotulada como cambio a la vía en una fecha en que el detector no cambió en ese volcán.
- **CÓMO REPRODUCIRLO**: `node m7_linea_via_con_k_residual.js D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base/data/mirova_equivalent`. Volcanes: Villarrica y Tupungatito.
- **CONFIANZA**: CONFIRMADO en el módulo; no lo vi dibujado en un navegador.
- **GRAVEDAD 1-5**: 2.

### 556
- **TÍTULO**: El orden de encendido escrito («mergea #974» y luego «mergea #983») no se puede ejecutar como está: los dos PR chocan con main.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `git merge-tree $(git merge-base 438a60a1e bbbe2068d) 438a60a1e bbbe2068d` y lo mismo con `e68819484` (salida en esta sesión: 2 marcas de conflicto cada uno, las dos en `docs/FICHA_SDA_VRP_CHILE.md`). `tasks/BLOQUE_ARRANQUE_S179.md` l. 38 a 39 y l. 110; `tasks/LOOP_OBJETIVOS.md` l. 582.
- **QUÉ PASA**: #974 está 97 commits detrás de main y #983, 46. Los dos cambian la línea de versión de la ficha pública, que main ya movió a v1.22 con #984. Hay que rehacer #974 (ficha v1.23), esperar su CI y mergear; y después rehacer #983, porque trae dentro la versión vieja de B1. El CI verde que muestran los insumos es anterior a #984. Confirmé además que #983 trae los dos flags (`enable_v375_codigo_mirova: true` y `enable_v750_codigo_mirova: true`) y #974 sólo el primero.
- **CÓMO SE VE EN EL DASHBOARD**: invisible mientras no se mergee. Si #983 entra primero, VIIRS 375 y 750 cambian de detector a la vez.
- **CÓMO REPRODUCIRLO**: los dos comandos `git merge-tree` de arriba, en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`; `git diff 438a60a1e...e68819484 -- pipeline/profiles/mirova_equivalent.yaml`.
- **CONFIANZA**: CONFIRMADO en la base. Si alguien ya rehízo las ramas después de las 20:37 UTC del 11-10, no lo vi.
- **GRAVEDAD 1-5**: 2.

### 557
- **TÍTULO**: Las compuertas A y B del plan de los 34 ya no se pueden ejecutar como están escritas.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` (`0472cd95e`) l. 9 a 14, l. 88 a 90 y l. 397 a 401; `tasks/LOOP_OBJETIVOS.md` l. 597, 629 a 635 y 1599 a 1604; `REGLA_REVERSION_V375E_BORRADOR.md` fila D5.
- **QUÉ PASA**: la compuerta A pedía que la retrospectiva diera «CUMPLE» en cada sensor antes de abrir la sombra de los 34 (l. 399 a 401). La sombra de los 34 se abrió el 2026-11-02 con las vías, por decisión de Nicolás de ese día, antes de cualquier lectura; y la lectura no da «CUMPLE» en ningún sensor: MODIS y VIIRS 750 quedaron en «DECIDE NICOLÁS» y VIIRS 375 en «NO SE CONTRADICE FUERA DE MUESTRA». La compuerta B pedía que «las sombras prospectivas de los 11» confirmaran (l. 12 a 14), y el plan decía que cambiar esa prueba final después de ver un resultado favorable «sería exactamente el error que A95 y A115 prohíben» (l. 88 a 90, TEXTO). Con la regla sellada (D5, «Sí a D2 a D7») esas lecturas dejaron de decidir, y después de B1 y B2 producción y sombra corren el mismo detector. El calendario del §0 también quedó atrás. El pendiente «actualizar el plan a la sombra adelantada y a los 13 volcanes con vecino» está anotado desde el bloque S173 (l. 22) y no se hizo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. El riesgo es que una sesión ejecute el plan al pie de la letra o declare cumplida una compuerta que ya no mide nada.
- **CÓMO REPRODUCIRLO**: leer las líneas citadas; `node m6_vista_preliminar_34.js ...` muestra que la sombra de los 34 ya corre con las vías (1.885 records, todos con `via_codigo_mirova: true`, del 2026-11-03 al 11-09).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 558
- **TÍTULO**: Los 34 ya tienen una página pública desde el 2026-11-09, antes de la compuerta B; 15 de 34 volcanes muestran «foco lejano» sin que nadie haya revisado qué son.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m6_vista_preliminar_34.js` con salida `m6_vista_preliminar_34_salida.txt`; `frontend/preliminar_34.html` l. 39 a 43 y l. 66 en `438a60a1e`; `api_pr_972.json`; `tasks/LOOP_OBJETIVOS.md` l. 699.
- **QUÉ PASA**: el plan decía que la sombra de los 34 no publica y que la publicación pedía 14 noches con el detector final, revisión del experto de cada publicación de 1 MW o más y aviso al OVDAS. La página `preliminar_34.html` se mergeó el 2026-11-09 23:05:05 UTC (#972) y lee la sombra directo del repo público. Lleva el rótulo correcto («sin referencia de MIROVA, paridad no medida [...] No la uses para decidir una alerta») y la ficha SDA v1.20 la declara. La bitácora dice que entró «con la frase de Nicolás», pero no cita la frase, y el cuerpo del PR tampoco. El detector que muestra son las vías, que en VIIRS todavía no son el de producción de los 11 (el plan, decisión D2, recomendaba «nunca publicar en los nuevos un detector que no esté demostrado en los 11»).
- **Medido** (módulo real sobre `data/sombra_34/` de `438a60a1e`, ventana de 14 días hasta el 2026-11-10 17:00 UTC): 34 de 34 con archivo; 30 detecciones, 28 focos distintos, 0 en cumbre; 15 volcanes en estado «foco lejano» y 19 «sin detección»; VRP máximo mostrado entre 0,18 MW (Ollagüe) y 3,78 MW (Guallatiri); 8 volcanes muestran un máximo sobre 1 MW (Guallatiri 3,78; Olca-Paruma 2,09; San Pedro 1,85; Irruputuncu 1,50; San José 1,24; Putana 1,12; Antillanca 1,09; Tolhuaca 1,03). Ningún foco cae a 5 km o menos de un Tier A.
- **CÓMO SE VE EN EL DASHBOARD**: una tabla aparte, enlazada desde el tablero, con 15 volcanes en amarillo «foco lejano» y su VRP.
- **CÓMO REPRODUCIRLO**: `node m6_vista_preliminar_34.js D:/vrp-trabajo/temporales/s179-audit/main D:/vrp-trabajo/temporales/s179-audit/d/base/data/sombra_34 m6_vista_preliminar_34_salida.json`. Ejemplo: Guallatiri.
- **CONFIANZA**: CONFIRMADO lo medido y la fecha del merge. Que falte la frase es un SIN RESPALDO documental, no una prueba de que Nicolás no la dio.
- **GRAVEDAD 1-5**: 2. El rótulo y la separación están; lo que falta es la revisión de los focos y el registro de la decisión.

### 559
- **TÍTULO**: La fase 4 del plan de los 34 escribe los volcanes nuevos en la carpeta de la réplica, contra lo que `docs/MISSION.md` dice que vive ahí.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: plan de los 34 l. 631 (TEXTO: «Workflow de publicación `nrt-red-ampliada.yml` (escribe en `data/mirova_equivalent/`)»); `docs/MISSION.md` l. 78 a 81 y l. 408 a 409 en `438a60a1e`.
- **QUÉ PASA**: la misión dice (l. 78 a 80, TEXTO) que «la réplica `mirova_equivalent` publica lo que MIROVA publica y calla donde MIROVA calla» y que «Lo que MIROVA no publica ya no vive en la réplica». MIROVA no publica ninguno de los 34. Y dice (l. 408 a 409, TEXTO): «Cualquier otra divergencia requiere actualizar este documento primero». El plan no trae ese paso. Hoy la sombra vive en `data/sombra_34/`, que sí respeta la separación. Además, en `data/mirova_equivalent/` siguen los 2.843 records de abril de los 34 con K (518 MODIS, 1.163 VIIRS 375 y 1.162 VIIRS 750, medidos en M2), que el plan (D15) mandaba archivar antes del primer record nuevo.
- **CÓMO SE VE EN EL DASHBOARD**: hoy invisible. Con la fase 4 tal cual, los auditores, el banco de paridad y la vigilancia, que leen esa carpeta, mezclarían volcanes con y sin referencia.
- **CÓMO REPRODUCIRLO**: leer las líneas citadas; `python m2_estado_serie.py D:/vrp-trabajo/temporales/s179-audit/d/base/data/mirova_equivalent m2_estado_serie_salida.json` (bloque «Los 34 fuera del NRT»).
- **CONFIANZA**: CONFIRMADO (lectura y conteo).
- **GRAVEDAD 1-5**: 2.

### 560
- **TÍTULO**: El despliegue de Pages ya copia 586 MB de carpetas que el tablero no lee; la prueba que lo vigila sólo conoce sombras y guardias, así que las carpetas nuevas del plan irían al sitio público.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `m1_pages_tamano.py` con salida `m1_pages_tamano_salida.txt`; `api_artifacts_pages_42860414397.json`; `.github/workflows/pages-deploy.yml` l. 77 y l. 81; `tests/test_pages_sin_sombras_s173.py` l. 29 a 36 en `438a60a1e`.
- **QUÉ PASA**: el workflow copia `data/` entera y sólo borra 4 carpetas. Medido en blobs de git en `438a60a1e`: `data/` pesa 784,0 MB en 346 archivos; al sitio van 776,8 MB más 21,8 MB de `frontend/`, imágenes y CSV: 798,6 MB, antes de los `_recent` que genera el build (unos 27 MB según el comentario del workflow). De eso, 586,4 MB son carpetas que el comentario del workflow no nombra como leídas por el tablero; busqué en `frontend/` y 493 MB no los referencia ninguna página (153,8 MB de `_s154_reproc_k_historico`, el reproceso de #883, y 19 carpetas de A/B viejos). El artefacto real del despliegue de la base (run 42860414397) pesa 89,0 MB comprimido. GitHub dice (docs.github.com, «GitHub Pages limits», leído el 2026-11-11 con WebFetch, TEXTO): «Published GitHub Pages sites may be no larger than 1 GB». Si ese límite se mide comprimido o sin comprimir es SIN DATO. La prueba deriva su lista de los perfiles `sombra*.yaml` y `guardia*.yaml`: `data/_s178_historia_via/` (unos 190 MB), `data/_k_residuales_via/` y `data/_via_viirs_residuales/` (regla sellada §4.7) no la pondrían en rojo.
- **CÓMO SE VE EN EL DASHBOARD**: hoy nada. Si un despliegue supera el límite y GitHub lo rechaza, el tablero queda congelado en la última versión: el operador vería datos viejos sin aviso propio.
- **CÓMO REPRODUCIRLO**: `python m1_pages_tamano.py "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" 438a60a1e m1_pages_tamano_salida.json`.
- **CONFIANZA**: CONFIRMADO el tamaño en git y el del artefacto. SOSPECHA que esas carpetas no tengan otro consumidor fuera del tablero (no hice censo de consumidores externos).
- **GRAVEDAD 1-5**: 2.

### 561
- **TÍTULO**: Ningún documento dice cómo se revierte la vía de un sensor después de haber reemplazado su historia.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `REGLA_REVERSION_V375E_BORRADOR.md` §4.7 (l. 108 a 110) y §6 (l. 128 a 130) en `438a60a1e`; plan de reemplazo (`62ccb8830`) l. 279 a 280.
- **QUÉ PASA**: la reversión pre-autorizada apaga el flag y, en 7 días, aparta los records de la vía y repone K. La regla dice que no cubre el reemplazo de la historia (§6, TEXTO: «El reemplazo de la historia publicada [...] va después de cada encendido, con tag y frase»). El plan dice sólo «Reversión: `git revert` del commit de datos o volver al tag». Si se revierte un sensor con la historia ya reemplazada, producción vuelve a K y la historia queda de la vía: el escalón al revés, y el paso del día después tendría que reponer 21 meses, no una semana. En MODIS el plazo de reversión sigue abierto (vence el 2027-03-02).
- **CÓMO SE VE EN EL DASHBOARD**: tras una reversión, la serie del sensor con la vía hasta la fecha del revert y K después, con la línea en esa fecha.
- **CÓMO REPRODUCIRLO**: leer las líneas citadas. No lo simulé.
- **CONFIANZA**: CONFIRMADO que los dos documentos no lo cubren. SOSPECHA sobre el tamaño del trabajo de reponer.
- **GRAVEDAD 1-5**: 2.

### 562
- **TÍTULO**: Los records de la vía que el plan necesita no están en git: P4 vive sólo en GitHub hasta cerca del 2026-12-10 y D2 y D4 sólo en un disco local.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `api_run_p4.json` (run 42749607584: `completed`, `success`, intento 2, 2026-11-10 17:56:18 UTC); `ls C:/Users/nmend/vrp-temporales/` en esta sesión (existen `s177_d2`, 25 MB, y `s177_d4`, 93 MB; no existe `s178_p4`); plan l. 153 a 160.
- **QUÉ PASA**: el reproceso costó más de un día de Actions y miles de descargas a NASA. Los artefactos vencen a los 30 días (D2 hacia el 2026-12-08). El paso 5 del plan los commitea «antes del 2026-12-08», pero ese paso depende de decidir dónde vive la unión (hallazgo 560). `C:\Users\nmend\vrp-temporales\` está fuera de OneDrive y de git.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Si se pierden, hay que volver a reprocesar, cruzando la rotación del token del 2026-11-27.
- **CÓMO REPRODUCIRLO**: `curl -s https://api.github.com/repos/MendozaVolcanic/VRP-chile/actions/runs/42749607584` y `ls C:/Users/nmend/vrp-temporales/`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 563
- **TÍTULO**: El texto del plan de reemplazo quedó atrás de main en cuatro puntos, además de los que anotó su verificador.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: plan (`62ccb8830`) l. 13 a 16, l. 142 a 147, l. 266 y l. 282; `scripts/reemplazar_ventana_reproceso.py` l. 55 a 83; `tests/test_guard_regla_c_s134.py` l. 69 a 87; `m2_estado_serie_salida.txt`.
- **QUÉ PASA**: (1) el «por qué» del plan es un aviso naranja que #984 quitó (hallazgo 555). (2) El script, tal cual, con `--hasta 2026-11-02` pisaría los 22 records de la vía que producción ya tiene con fecha hasta el 11-02 (2 por volcán, medidos) y agregaría los de P4: confirmo el hueco 1 del verificador con su número. (3) La prueba P5 exige 20 records K de MODIS en Villarrica desde el 2026-06-01 y su docstring ya anuncia que el reemplazo la pondrá roja: confirmo el hueco 2. (4) El plan nombra #975 para VIIRS 750; el PR vigente es #983. (5) El paso 4 pide tener resueltos #976 y #978 «antes de ese PR»: los dos ya están en main.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; el efecto es main en rojo después del paso de MODIS (por P5) y records de producción pisados en el borde del 11-02 si el script no se cambia.
- **CÓMO REPRODUCIRLO**: `python m2_estado_serie.py ...` (columna «via<=11-02»); leer las líneas citadas.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 564
- **TÍTULO**: La página preliminar de los 34 usa un radio de cumbre que Nicolás no ha decidido y no marca un foco que sea del volcán Tier A vecino.
- **ARCHIVO:LÍNEA o SCRIPT:SALIDA**: `frontend/preliminar_34.js` l. 12 a 14 y la función `focosCompartidos` en `438a60a1e`; `tasks/BLOQUE_ARRANQUE_S178.md` l. 47 (decisión heredada); `m6_vista_preliminar_34_salida.txt`.
- **QUÉ PASA**: la página llama «cumbre» a todo píxel a 5 km o menos y cita «la decisión D5» del plan, que sigue en la lista de decisiones pendientes (la página sí rotula el valor como «por defecto»). En calderas como Laguna del Maule 5 km puede dejar fuera la zona activa. Y «mismo foco visto desde» compara sólo entre los 34: el cráter de Villarrica visto desde la grilla de Quetrupillán (19,8 km) saldría como «foco lejano» de Quetrupillán sin decir que es de Villarrica. En la base no hay ningún caso (0 focos a 5 km o menos de un Tier A). Nota: esta página decide «cumbre» por el píxel alertado más cercano, que es la regla «cercano»; el tablero de los 11 usa la posición radiante del record (hallazgo 551). Son dos reglas distintas publicadas para el mismo detector.
- **CÓMO SE VE EN EL DASHBOARD**: latente. El día que Villarrica o Chaitén tengan un foco fuerte, el volcán vecino de la lista de 34 mostraría un «foco lejano» con ese VRP.
- **CÓMO REPRODUCIRLO**: el comando de M6; leer `frontend/preliminar_34.js`.
- **CONFIANZA**: CONFIRMADO por lectura del módulo y por el control de M6; el caso del vecino es SOSPECHA hasta que ocurra.
- **GRAVEDAD 1-5**: 1.

## 3. Inventario de decisiones del eje y veredicto

Líneas de `tasks/LOOP_OBJETIVOS.md` en `0472cd95e`. «Frase» es la cita que la bitácora atribuye a Nicolás.

| # | Fecha UTC y frase (línea) | Qué decide | Veredicto | Evidencia de esta sesión |
|---|---|---|---|---|
| 1 | 2026-11-02 00:30, «Sí, prepáralo» (l. 1621) | Preparar el plan de los 34 con sombra previa | APLICADA DISTINTO | El plan existe, pero lo que se hizo después no sigue sus compuertas (557) |
| 2 | 2026-11-02 01:24, «la idea es lanzar los 34 que faltan cuando ya sepamos que estamos funcionando igual que MIROVA» (l. 1599) | La publicación de los 34 cuelga de la paridad en los 11 | SOSTENIDA CON RESERVAS | El tablero principal no lee la sombra; pero hay página pública preliminar desde el 11-09 (558) |
| 3 | 2026-11-02 01:24, «continúa con todo para que avancemos más rápido» (l. 1602) | Sombra de los 34 con las vías desde ya; agregar grillas | SOSTENIDA | 45 grillas (34 nuevas con `roi_v750: def`); 1.885 records, todos de la vía (M6) |
| 4 | 2026-11-02 15:15, «Sí, mergear #932» (l. 1495) | Merge de la sombra de los 34 | SOSTENIDA | perfil `sombra_34.yaml` y workflow en main |
| 5 | 2026-11-02 15:42, «de1 a d7 si, en el resto hace lo que recomiendes» (l. 1475) | Decisión 3 (marcar pasadas a menos de 4 km del vecino) y 4 (sombras fuera de Pages) | SOSTENIDA CON RESERVAS | 4: comprobada en `pages-deploy.yml` l. 29 a 32 y l. 81. 3: existe `scripts/vecinos_sombra_34.py` (l. 47 a 63), pero la página pública no lo usa (564). La frase es genérica |
| 6 | 2026-11-03 10:23, «nadie consume el producto [...] hasta que podamos demostrar que tenemos los mismos datos y podamos extender a los otros volcanes» (l. 1360) | Extender a otros volcanes es un objetivo | SOSTENIDA | No está escrito en `docs/MISSION.md` (559) |
| 7 | 2026-11-09 23:05, #972 «con la frase de Nicolás», sin cita (l. 699) | Publicar la página preliminar de los 34 | SIN RESPALDO | Ni la bitácora ni el PR citan la frase (`api_pr_972.json`) |
| 8 | Pendiente (bloque S177 b6, bloque S178 b9) | Radio de cumbre de los 34 | Pendiente que la página da por tomada | `preliminar_34.js` l. 12 a 14 (564) |
| 9 | 2026-11-10 03:28, «Sí, despacha ahora» (l. 675) | Despachar P4 (historia que faltaba con la vía) | SOSTENIDA CON RESERVAS | Terminó verde (intento 2, 17:56 UTC). Sin Tupungatito antes del 02-23; artefactos sin bajar (562) |
| 10 | 2026-11-10 04:09, «Sí, quítalo» (l. 671); 10:20, «quita los 3» (l. 593); «Mergea #984» (l. 576) | Quitar los avisos de texto del tablero | SOSTENIDA | Consecuencia: el plan #981 pierde su razón escrita y su comprobación (555, 563) |
| 11 | Pendiente (bloque S179 b6): recomendación «Apartarlas» | Pasadas K sin par en la vía | SOSTENIDA en MODIS, con la razón corregida | 0 de 217 pasadas MODIS sin par se publican hoy; en VIIRS 375, 1 de 601 (Cordón Caulle 2025-09-24 05:24, 0,247 MW). La razón vigente es la línea falsa (555), no el aviso |
| 12 | Pendiente (bloque S179 b7): recomendación «Reprocesar con la vía» | Tupungatito antes del 2026-02-23 | SOSTENIDA CON RESERVAS | Conteos confirmados (787, 1.574 y 1.563, todos K). Dejar K mueve la línea al 02-23 en todas las vistas (555). Pide un despacho fuera del planificador sellado y llamadas a NASA antes de la rotación del token |
| 13 | 2026-11-08 17:50, «si empieza, pero porque no lanzar todos los sensores con la nueva via?» (l. 747) y 17:44 «Sí, prepáralo» (l. 800) | Encender VIIRS con guardia K, B1 y B2 separados | SOSTENIDA | Guardia y vigilancia en main; perfiles confirmados |
| 14 | 2026-11-10 01:17, «Retro primero» (l. 687) | Encender VIIRS si la retrospectiva no pierde protegidas | DEBILITADA | La condición se cumplió con el brazo «cercano»; producción escribe «radiante» y con el tablero se pierden 5 de 72 (551) |
| 15 | 2026-11-10 03:21, «Sí, escríbelos» (l. 680) | Escribir B1 y B2 | SOSTENIDA CON RESERVAS | Existen; no mergean limpio sobre main (556) |
| 16 | 2026-11-10, «C-rad (14/17)» (l. 600), «Sí a D2 a D7» (l. 597), «Sello la regla» (l. 586) | Regla de reversión de VIIRS | SOSTENIDA CON RESERVAS | Su §4.1 choca con el paso VIIRS del reemplazo (553); su D5 deja sin base la compuerta B de los 34 (557) |
| 17 | Bloque S179 §b1, §b2 y §g.6 (no es frase todavía) | Orden: 3 noches de guardia, #974, #983, y el reemplazo después | SIN RESPALDO tal como está | 556 (choques), 551 (posición), 552 y 553 (el reemplazo rompe la vigilancia). Guardia: 0 de 3 en la base; 1 de 3 a las 00:12 UTC del 11-11 (`api_runs_guardia_k_viirs.json`) |

Pendientes de `docs/AUDIT_S175.md` (rama del PR #955) que caen en este eje: §8 decisión 1 (rotar `EARTHDATA_TOKEN` antes del 2026-11-27) sigue abierta y pesa sobre todo despacho nuevo del reemplazo; §8 decisión 20 (llevar a main el lector de V375-E antes de la parada de la sombra) queda DEBILITADA por D5 de la regla sellada, porque esa lectura ya no decide; §6 fila 262 (radio `max(4 km, inner)` para vecinos) está en el código (`scripts/vecinos_sombra_34.py` l. 47 a 63); §6 fila 255 (cola de decisiones desfasada) no la revisé; §11.6 figura resuelto en la rama.

## 4. Las tres preguntas de `docs/MISSION.md`, por plan

| Plan | 1. ¿Papers o código de MIROVA? | 2. ¿Cierra una divergencia? | 3. ¿Alineación interna? | Lectura |
|---|---|---|---|---|
| Reemplazo de la historia con la vía | Para VIIRS 750 sí: manda el código de MIROVA (MISSION l. 163 a 166). Para MODIS y VIIRS 375 la vía entra por «una medición» (l. 166) | Sí en magnitud (K entrega cerca de la mitad de la potencia de MIROVA en VIIRS) | Sí: es una operación de datos | Pasa, con una condición que el plan no trae: el criterio de victoria (l. 113) se comprueba sobre la historia que se reemplaza (554) |
| Encendido B1 (VIIRS 375) | Por medición; pero la medida que decide es de «cercano» | Sí | No aplica | No pasa limpio hasta resolver la regla de posición (551) |
| Encendido B2 (VIIRS 750) | Sí, el código | Sí | No aplica | Pasa en lo que medí: 0 protegidas perdidas en F26 y DM (50 contra 50 y 21 contra 22). La lectura quedó en «DECIDE NICOLÁS» por V750-A sin sello: esa decisión está pendiente (bloque S179 b2) |
| Red de los 34 | No: MIROVA no vigila esos volcanes y su geometría no se puede copiar | No | Sólo si se trata como producto aparte | La sombra y la página aparte pasan por la pregunta 3. La fase 4 tal cual no: mete en la réplica algo que MIROVA no publica (559) |

## 5. PROPUESTAS PARA LOS PLANES (no implemento ninguna)

1. **Antes de B1, decidir la regla de posición donde la lee el operador** (551). Opciones: que el record de la vía marque `summit` cuando su píxel alertado más cercano está dentro del radio interno (toca `pipeline/`, A45); que el predicado del tablero lo haga para records de la vía, como ya hace `frontend/preliminar_34.js` (toca `frontend/`, A45); o que Nicolás acepte «radiante» por escrito sabiendo los 5 casos. Antes: mirar la cabecera de la imagen de MIROVA de las 5 pasadas (A61) y pedir al frente de VIIRS la fila de la retrospectiva con el brazo radiante (el lector ya la calcula: `cercano_y_radiante_difieren`).
2. **Arreglar la vigilancia antes de cualquier reemplazo, o reemplazar después del plazo de la guardia** (552, 553). Para el encendido: que `encendido_desde_datos` mire sólo records con `regimen.perfil` igual a `mirova_equivalent` (los del reproceso traen `_s172_retro_paquete`, medido en M4), o fijar el encendido medido en un archivo sellado. Para el nulo: guardar su resultado ya medido como evidencia fija en vez de recalcularlo sobre una historia que va a cambiar. Las dos cosas tocan una regla sellada: piden frase de Nicolás. La alternativa sin código es reemplazar cada sensor cuando su plazo de reversión cierre (MODIS: 29 protegidas o 2027-03-02).
3. **Agregar al ensayo un recuento de publicación con veto** (554). Por familia, sobre la unión completa (D2, D4 y P4), con el banco de paridad: protegidas que hoy se publican y después no (tiene que ser 0, o cada una explicada con su imagen), pasadas que dejan y que empiezan a publicarse, y lo mismo para las pasadas sin par. `m4_reemplazo_efecto.py` sirve de punto de partida. Sin P4 bajado, ese paso queda SIN DATO y el sí no se pide.
4. **Reescribir el §0, el §4.1 y los pasos del plan #981** (555, 563): la razón es la línea falsa y la mezcla de detectores, no el aviso; la comprobación del paso 9 mira la línea (`primeraVia` igual a `null` en los 45 archivos y en los `_recent`, con el control que inserta un K y exige que la fecha vuelva); tercera regla del script (no pisar records con `via_codigo_mirova: true` ni agregar los de P4 desde el 11-02); P5 reasignada a `data/guardia_k_modis/` en el mismo PR de código; #983 en lugar de #975.
5. **Sacar del despliegue lo que el tablero no lee, y poner la unión fuera de `data/`** (560). Lista blanca en `pages-deploy.yml` (hoy bastan `mirova_equivalent`, `mirova`, `experimental`, `experimental_v2`, `_s99_test1_eq16`, el CSV de `mirova_reference` y las alertas), previa búsqueda de consumidores como se hizo con las sombras; el sitio bajaría de unos 800 a unos 300 MB sin comprimir. Un paso que mida `du -s _site` y falle sobre un techo. La unión y los residuos (`_k_residuales_via`, `_via_viirs_residuales`) en una carpeta que no se despliegue, y la prueba de Pages vigilando «todo lo que no está en la lista blanca» en vez de los nombres `sombra*` y `guardia*`.
6. **Bajar P4 ahora y sellar los tres despachos con sha256** (562), en un disco con respaldo, antes de decidir dónde se commitea la unión.
7. **Escribir la reversión después del reemplazo** (561): qué se revierte primero (el PR del flag o el commit de datos), con qué tag, y quién repone K en la historia.
8. **Orden de encendido ejecutable** (556): actualizar #974 con main (ficha v1.23), CI y revisión del diff; «mergea #974»; rehacer #983 sobre main (ficha v1.24), CI; cerrar #975 para que nadie lo confunda con el vigente. Entre B1 y B2, comprobar que el nulo de VIIRS 750 sigue con pares.
9. **Reescribir el plan de los 34** (557, 559): marcar la fase 0 y la compuerta A como superadas por las decisiones del 2026-11-02; redefinir la compuerta B con criterios que se puedan medir después de B1 y B2 (por ejemplo: guardia K de cada sensor sin candidatas en N noches, revisión del experto de los focos de la sombra, 14 noches con el detector final); llevar a la lista de decisiones D1 (43 o 45), D5 (radio de cumbre) y D15 (archivar abril) como pendientes; que la fase 4 escriba en una carpeta propia y que antes se actualice `docs/MISSION.md` con el objetivo de extender, citando la frase del 2026-11-03.
10. **Página preliminar de los 34** (558, 564): anotar la frase de Nicolás que autorizó #972; marcar el foco que cae dentro del radio de un Tier A vecino; revisar los 28 focos (qué hay en el terreno) antes de darle más visibilidad.
11. **Calendario contra el token** (pendiente §8.1 de la auditoría S175): cualquier despacho nuevo (Tupungatito antes del 02-23, y del 2026-11-10 al encendido de VIIRS) termina antes del 2026-11-27 o empieza después de comprobar la rotación.

## 6. SEGUIMIENTOS (visto fuera de mi eje, una línea cada uno)

- PR #980 (vara MATLAB, condición de B2): en los insumos su `pytest` figura en FAILURE (`insumos/pr_980.json`), y el bloque S179 recomienda mergearlo. Causa SIN DATO. Confianza: CONFIRMADO el estado a las 20:37 UTC del 11-10.
- `scripts/vigilancia_guardia_modis.py` l. 244 a 246: `disparadores` no usa el campo `referencia_sospechosa` que sí calcula `vigilancia_sombra.pasadas_de_alerta`. Con N-3 fuera (regla §4.2), una protegida sólo del OCR dispara igual que una de la tabla. Confianza: CONFIRMADO por lectura; efecto SOSPECHA.
- El veredicto VIGILANCIA_CIEGA junta todos los avisos (l. 526 a 528): un aviso permanente tapa a uno nuevo en el titular. Confianza: CONFIRMADO por lectura.
- Planchón-Peteroa tiene un record K de MODIS del 2026-11-02 01:15, cinco minutos antes de su primera pasada de la vía (M2). Es el VX-04 de la auditoría S175. Confianza: CONFIRMADO que existe; causa SIN DATO.
- En 2025, VIIRS 375: 737 pasadas que K publica y la vía no, y 113 al revés (M4). No hay tabla de MIROVA de 2025 en el repo para juzgarlas. Para el frente de VIIRS.
- GitHub recomienda 1 GB para el repositorio fuente de Pages (misma página de límites). No medí el tamaño del repo.
- `loop/activo` no tiene integrado main (284 commits según el bloque S179). No lo medí.
- Decisiones fuera de mi eje que vi en la bitácora y no juzgo: encendido de MODIS («Sí, sellar y encender», l. 1409); ROI B4 de VIIRS 750 («Sí, confirmo B4»); C-montaje («Sí, opción A» y «Sí, opción 1», decisiones *post hoc*); re-sellado del lector de V375-E; arreglo del token en `pipeline/fetch.py`; regla de cirrus del tablero; ventana fija y 14 noches del lector de V750-A; prueba ciega de Codex; plan del visualizador.

## 7. VERIFICADO LIMPIO

| Qué | Vara | Comando | Resultado |
|---|---|---|---|
| Referencia de la base | sha256 del encargo | `sha256sum` sobre los archivos sacados con `git show 438a60a1e:` | `latest_consolidado.csv` `40b1b928...7fdf6` y OCR `7e54155a...1e75`: iguales |
| Cifras del plan #981 §2.2 | conteo propio de claves | M4 | 42.389 records en D2 más D4, 0 claves repetidas, todos `via_codigo_mirova: true`, perfil `_s172_retro_paquete`; MODIS sin par 217; VIIRS 375 sin par 601; VIIRS 750 sin par 0 |
| Tupungatito antes del 2026-02-23 | conteo propio | M2 | 787 MODIS, 1.574 VIIRS 375, 1.563 VIIRS 750, todos K |
| Frontera K y vía de MODIS | conteo propio | M2 | primera pasada de la vía 2026-11-02 01:15 o 01:20; 0 records K posteriores a la primera vía; 0 caídas a K; menor `processed_utc` de la vía 2026-11-02T20:11:43Z; 0 records anteriores al 2025-02-15 en los 45 archivos |
| «Entre el commit del reproceso y main no cambia la detección» | `git diff --stat a7a6ae360 438a60a1e -- pipeline/ scripts/run_pipeline.py volcanoes.yaml` | esta sesión | sólo `pipeline/fetch.py` y `pipeline/profiles/guardia_k_viirs.yaml` |
| MODIS: el reemplazo no quita protegidas publicadas | predicado del tablero y lectura A con SN, F26 y DM | M4 | F26: 32 protegidas, K publica 31 y la vía 32; DM: 9, K 7 y la vía 9; 0 que K publique y la vía no |
| MODIS: apartar las pasadas sin par no quita nada publicado | predicado del tablero, D2 más D4 | M4 | 0 de 217 se publican hoy |
| VIIRS 750: sin protegidas perdidas | lo mismo | M4 | F26: 51, K 50 y la vía 50, 0 que K publique y la vía no; DM: 22, K 21 y la vía 22 |
| El instrumento ve una pérdida | control positivo | M4 | al quitar un record de la vía de una protegida, «K publica y la vía sin record» pasa de 0 a 1 |
| Sombras y guardias fuera del sitio | lectura del workflow | `pages-deploy.yml` l. 29 a 32 y l. 81 | las 4 carpetas se excluyen del disparo y del artefacto |
| Los 34 tienen grilla y corren con las vías | conteo propio | `yaml` sobre `pipeline/grillas_mirova.yaml`; M6 | 45 grillas (43 `def`, 2 `sens`); 34 archivos, 1.885 records, todos de la vía |
| #983 trae B1 y B2; #974 sólo B1; ninguno cambia código | `git diff 438a60a1e...<rama> -- pipeline frontend` | esta sesión | sólo perfiles YAML |
| P4 terminó | API de GitHub | `api_run_p4.json` | `success`, intento 2, 2026-11-10 17:56:18 UTC |
| La ficha SDA declara la página preliminar | lectura | `docs/FICHA_SDA_VRP_CHILE.md` l. 51 | v1.20, 2026-11-09 |
| La vigilancia de la base se reproduce | salida guardada por el workflow | M3 y M3b | MODIS VERDE con 167 pares; VIIRS 375 VERDE con 223 pares |

## 8. SIN DATO

- Todo lo de las ventanas de P4 (enero, abril a septiembre y 2026-10-17 a 11-09): cobertura, pasadas sin par, protegidas, cambios de publicación.
- Si MIROVA alertó en el cráter en las 5 pasadas del hallazgo 551 (falta la imagen).
- Si el límite de 1 GB de Pages se mide sobre el artefacto comprimido (89 MB) o sobre el sitio expandido (unos 800 MB).
- Si las pasadas VIIRS 375 sin par son todas descarte de borde (el plan tampoco lo sabe).
- La frase con que Nicolás autorizó #972.
- Lo que la vía publica en las pasadas anteriores al encendido una vez reemplazadas (`borde_del_encendido` de la vigilancia).
- La suite completa con la historia reemplazada (no repetí las simulaciones del §4.2 del plan).
- Cómo se ve todo esto en un navegador real.
- La salud de las corridas de `sombra-34.yml` y la causa del rojo de #980.

## 9. FUERA DE ALCANCE

- La validez de la lectura con candado de la retrospectiva y de sus controles (otro frente).
- La adopción de la vía en MODIS y su regla de reversión, salvo el choque con el reemplazo.
- El contenido de B1 y B2 más allá de los flags y de la regla de posición.
- El plan del visualizador y el plan de auditoría con GPT Codex.
- Cualquier arreglo: no modifiqué nada fuera de CARPETA y de mi temporal.

## 10. Archivos de esta carpeta

Scripts con su salida al lado: `m1_pages_tamano.py`, `m2_estado_serie.py`, `m3_vigilancia_tras_reemplazo.py`, `m3b_vigilancia_viirs_tras_reemplazo.py`, `m4_reemplazo_efecto.py`, `m5_cinco_protegidas_v375.py`, `m6_vista_preliminar_34.js`, `m7_linea_via_con_k_residual.js`, `inventario_frases.py`. Respuestas de la API: `api_artifacts_pages_42860414397.json`, `api_pr_972.json`, `api_runs_guardia_k_viirs.json`, `api_run_p4.json`. Tabla de hallazgos: `hallazgos.csv`. Los textos de la regla sellada, del plan de reemplazo, de la auditoría S175 y de la bitácora, tal como los leí, quedaron en el temporal `D:\vrp-trabajo\temporales\s179-audit\d\` (`REGLA_REVERSION_V375E_438a60a1e.md`, `PLAN_REEMPLAZO_62ccb8830.md`, `AUDIT_S175_rama.md`, `bitacora_s172_s178.md`).

Llamadas a la API de GitHub: 5 de 10 (cabecera de fecha, artefactos del run 42860414397, PR #972, corridas de `guardia-k-viirs.yml`, run 42749607584), todas públicas y sin credencial. Una lectura de docs.github.com. Ninguna llamada a NASA, ningún workflow, ningún commit.

Cierre del informe: 2026-11-11 01:52:58 UTC (cabecera `Date` de GitHub). Después de corregir la ruta de salida de M3, M3b, M4 y M5 los volví a correr: las cuatro salidas de texto son idénticas a las guardadas (`diff` de 0 líneas) y la instantánea compartida quedó sin archivos míos. Disco al cerrar: C: 13 GB libres, D: 23 GB libres; mi temporal, 339 MB.
