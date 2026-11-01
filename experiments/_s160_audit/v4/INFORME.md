# V4: verificación de los hallazgos de F4 (cierres, rebajas y reglas con número desde S146)

## 1. Encabezado

- Hora del servidor: inicio 2026-10-22 04:02:52 UTC (dos HEAD a api.github.com devolvieron el mismo segundo; caché
  probable, por eso el sello de `caminos.md` lleva esa hora), cierre 2026-10-22 04:15:47 UTC.
- Código y datos medidos: main `d516b9d8c` (instantánea `D:\vrp-trabajo\temporales\s160_audit\main\`; comprobé que
  sus JSON son los blobs de `d516b9d8c` salvo fin de línea: Copahue y Lascar, tras quitar los CR, dan el mismo sha256;
  referencia: tabla `bc1522c24c924cb5`, OCR `94679246acbd0db5`). Otras versiones leídas con `git show`: loop/activo
  `dbc377bbe` (igual al checkout de OneDrive y a `origin/loop/activo`), y la rama del worktree
  `C:\vrp-trabajo\s159-pruebas`, que **no** es `s159-pruebas` sino `s160-auditoria` (HEAD `cda902080` al medir; se
  movió desde `411b5bda8` durante mi sesión, por commits de otra sesión). Corpus de fechas pasadas: `88e97d84e`
  (2026-10-14, el de las marcas S151) y `03c44eed7` (2026-10-14, D-4), extraídos a `D:\vrp-trabajo\temporales\s160_audit\v4\`.
- Modelo: Opus 5.5 (`claude-opus-5-5`); esfuerzo: el que fijó quien orquesta (no lo veo desde dentro).
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v4\`. `caminos.md` sellado antes de abrir los archivos
  citados (sha256 y hora al pie).
- Plan: `git diff 06e0fad3b -- docs/PLAN_AUDITORIA_S160.md` muestra sólo el §11.2b (R7 y la línea del PR del
  preámbulo, dentro del mismo bloque). Sin hallazgo por ese lado.
- Qué NO miré: U2, U4 a U7, U9, U11 y U14 de la tabla de M1 uno por uno (sólo los que la lista nombra); el script de
  D33 no lo re-corrí (baja datos de la red); no abrí el informe de F4 ni sus CSV, como pide la tarea.
- Llamadas a la API de GitHub: 3 (HEAD a la raíz, sólo para la hora).

## 2. En una pantalla

- 281 se sostiene en main: los 68.072 records anteriores al 2026-09-18 son K (0 sin marca; control: los 90 residuos
  apartados salen C0) y ningún documento rector de main lo dice. Gravedad 4, no 5. Y hay algo peor (V4-01): el
  `CLAUDE.md` que carga cada sesión abierta desde OneDrive (loop/activo) no tiene ni una marca S157 ni S158.
- 282, 283, 290 y 291: los números de las marcas **se reproducen exactos en el corpus de su fecha** (1.565/343/7;
  439/992; 1.642/37/19/233; 24); hoy no, por corpus vivo y reemplazo con K (A90), no porque nunca se reprodujeran.
- 284 REFUTADO: los 14 y el 5 y 5 salen enteros del script persistido (`frontera_banner.py`, lectura C automática).
- 286 y 293: la rama está mal nombrada (S158 no vive en loop/activo sino en el linaje `s160-auditoria`), y ahí varias
  marcas que el auditor da por ausentes sí están. 285, 288 y 289 confirmados.
- Nuevo: V4-02, la marca del hueco nov-ene de `CLAUDE.md` quedó falsa tras #883 (74 de 74 días en los 11 volcanes).

## 3. Veredictos sobre la lista de F4, ordenados por mi gravedad

### 281: el reemplazo del histórico con K no bajó a los documentos rectores. CONFIRMADO EN PARTE, gravedad 4
- Medición propia (`v_281_regimen_por_mes.py`, salida `v_281_regimen_por_mes_salida.txt`). Pregunta 1: si no hubiera
  reemplazo, los records anteriores al 2026-09-18 saldrían sin `regimen.codigo_sha` y la cuenta lo vería. Pregunta 2:
  control positivo, los 90 residuos de `data/_c0_residuales/` (extraídos de `d516b9d8c`; la instantánea no los trae)
  salen 90 sin marca. Resultado en los 11 Tier A de main: del 2025-02-15 al 2026-09-17, **68.072 K y 0 sin marca**;
  desde el 2026-09-18, 3.896 K y 0 sin marca; ningún record antes del 2025-02-15.
  `DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z"` (`frontend/cambio_detector.js:32`). #883 (`8471add46`) es ancestro de
  main y no tocó ningún documento rector; ningún commit posterior en main toca CLAUDE.md, MISSION, SINTOMAS, el
  catálogo ni README.
- Textos de main que siguen con la frontera vieja (leídos): `docs/MISSION.md:22`, `CLAUDE.md:127, 190, 1335`,
  `docs/SINTOMAS.md:9, 19, 198`, `docs/MIROVA_DIVERGENCES.md:1444, 1507, 1640`; 0 menciones de #883, `2025-02-15T` o
  `_c0_residuales` en los cinco documentos.
- Lo que matiza: MISSION:23-24 y SINTOMAS:20-21 avisan en futuro que «la frontera se moverá más atrás cuando se aplique
  el reproceso histórico con K». No dicen que ya pasó, pero quien lee con atención queda advertido. En el linaje
  `s160-auditoria` hay una marca (R2-12, `CLAUDE.md:136-139`, «la frontera del 2026-09-18 ya no separa detectores»);
  ahí mismo siguen sin marca `CLAUDE.md:141, 210, 1376`, MISSION:22 y SINTOMAS:9, 19, 211. En loop/activo los
  documentos no mencionan esa frontera (son anteriores a S157): el hallazgo no aplica tal cual ahí; ver V4-01.
- Por qué 4 y no 5: la decisión en producción (K) no se apoya en estos textos; lo que tuercen es la medición
  (estratificar «C0 antes del 2026-09-18» sobre datos que son todos K).

### 282: el tope D9 de 5 MW bajo K. CONFIRMADO EN PARTE, gravedad 3
- Re-corrí `experiments/_s150_meta_audit/verif_docs/contar_topados_d9.py` en dos corpus y conté por otro camino (la
  bandera `primary_cluster.d9_capped`, separada por régimen; `v_282_d9_capped.py`). Corpus de la marca (`88e97d84e`):
  65.705 records, **1.565** con `pc.vrp_mw == 5,0`, 1.565 con `d9_capped`, **343** sobre 5 MW, y **7** pasadas MODIS
  topadas de Chillán entre el 2026-09-28 y el 2026-10-13, todas `far` (`v_282_chillan_salida.txt`): la marca era
  exacta en su fecha. Main: 74.811 records, `pc.vrp_mw == 5,0` = **9** (el «16» del auditor es «cualquiera de los tres
  campos», otra métrica que la de la marca), `d9_capped` = 9 (todos K), 183 sobre 5 MW, Chillán 0 topadas de 31.
- Las marcas S151 llevan su ventana («Corpus al 2026-10-14 (65.705 records)», `docs/MIROVA_DIVERGENCES.md:229-230`,
  `docs/MISSION.md:187-189`), así que no son falsas: falta la marca de que bajo K el tope casi no actúa. Las líneas que
  el auditor cita para MISSION (134-140) no corresponden: el pasaje está en 184-189.

### 285: A118 dice «D18 nunca se ha medido» sin marca. CONFIRMADO, gravedad 3
- `CLAUDE.md:1530` (main), `:1501` (loop/activo), `:1571` (`s160-auditoria`): la misma frase, sólo con la nota
  «arreglado en S149» del cableado. D18 sí tiene las marcas S151 (`docs/MIROVA_DIVERGENCES.md:2339-2357`: KC NO CUMPLE,
  veto) y SINTOMAS:160 ya la da por vieja. Gravedad 3 y no 4: el texto viejo abre (invita a medir), no apaga.

### 286: S158 sólo en loop/activo. CONFIRMADO EN PARTE, gravedad 3
- Confirmado: main no tiene `docs/AUDIT_S158.md`, ni D34, ni ninguna «S158» en CLAUDE.md, MISSION ni el catálogo.
- Refutado el lugar: loop/activo (`dbc377bbe`) tampoco tiene nada de eso (AUDIT_S158 no, D34 0, S158 0). La síntesis
  `76622cd77` está en `claude/s158-audit-r2-*`, `s158-d17-diseno`, varias `s159-*` y el linaje del worktree
  (`s160-auditoria`, 72 commits por delante y 55 por detrás de main al medir). Las líneas que el auditor da como de
  loop/activo calzan con el worktree.
- En ese linaje, contra la tabla U de `experiments/_s158_audit_r2/m1/INFORME.md:186-199`: U1 (D34 «Alcance»,
  `docs/MIROVA_DIVERGENCES.md:3314`) sin marca, confirmado; U3 (D18) 0 marcas S158 en toda la sección, confirmado; U8 en
  parte: `docs/MIROVA_DIVERGENCES.md:1104` **sí** está marcado (marca S158 R2 en 1092-1098, que termina en «Texto
  conservado»), `CLAUDE.md:152` («kernel 8-vec aritmético») sin marca; U10 (`experiments/50_FACTOR_42_HALLAZGO.md`)
  0 marcas, confirmado; U12 (memoria) sin marca, confirmado; U13 (`docs/DISENO_D17_REMUESTREO_UTM.md:282-283`, sigue
  «pendiente del verificador») confirmado. `CLAUDE.md:181` **sí** está marcado (marca en 175-180). D27: la marca S158
  R2 está justo debajo del encabezado, cuyo texto no cambió («nunca se ejecuta»); por A113 (d) es caso de borde.

### 288: la memoria del agente conserva cinco números rebajados sin marca. CONFIRMADO, gravedad 3
- Los cinco archivos tienen 0 marcas (grep de ⚠️, S146, S151, rebaj, OBSOLET, corrupt). `MEMORY.md:50` («S27 Test1
  cierra D4 (recall 50→80 %)») se carga en cada sesión (está en el contexto de esta). El de calidad de la referencia
  dice «86 % enero (10 volcanes, sin Tupungatito ...)», que contradice la corrección S151 (sin Tupungatito, enero da
  99 %). `milestone_s27_h_s27_1_confirmada.md` y `reference_s113_cirrus_d9_scope.md` no están en el índice de
  MEMORY.md: se leen sólo a pedido.

### 289: README describe el Test 1 integrado como detector vivo. CONFIRMADO, gravedad 3
- `README.md:54, 92, 131, 220` idénticos en main, loop/activo y `s160-auditoria`; ninguna mención de K, #850 ni S153;
  el perfil tiene `enable_test1_path: false` (`pipeline/profiles/mirova_equivalent.yaml:268`, main). Es la
  descripción pública de un SDA.

### 293: F2-H3 a H9 de S158. CONFIRMADO EN PARTE, gravedad 3
- Main y loop/activo: ninguna marca S158, confirmado.
- `s160-auditoria`: tienen marca S158 R2 H3 (`docs/MISSION.md:302`, `CLAUDE.md:224`), H4 en su parte de git
  (`CLAUDE.md:60`), H5 (D8), H6 (D27), H7 en el punto del kernel (`CLAUDE.md:175`) y H9 (comentarios «S158» en 12
  archivos de `tests/`). Siguen sin marca: H8 (`pipeline/detection_context.py:977`, «MÁSCARA DE SATURACIÓN», bajo
  A45), el YAML, `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` (fuera de git) y el «C1 = 0.003 summit / 0.010 scene» de
  `CLAUDE.md:150`. El «H3 H4 H7 H8 H9 siguen sin marca en las dos ramas» cae para H3 y H9, y en parte para H4 y H7.

### 283: D-4 (439 y 992). CONFIRMADO EN PARTE, gravedad 2
- Con `scripts/clase_mirova.py`, `scripts/referencia_mirova_unificada.py`, `pipeline/mirova_csv_loader.py` y la unión
  de `03c44eed7` salen **439** (A) y **992** (B) exactos (`v_283_d4_en_su_fecha.txt`). Con la unión de main: 478 y
  1.055, de las cuales 437 y 993 son anteriores al 2026-10-14 y 41 y 62 posteriores: es corpus vivo (A90), con un cambio
  chico hacia atrás (2 protegidas A menos y 1 B más en la ventana vieja).
- Confirmado que `docs/MISSION.md:90-92` y `CLAUDE.md:1695-1696` dan el número sin ventana ni hash
  (`docs/S151_CRITERIO_CLASE_MIROVA.md:85` dice «hoy» y «unión histórica»). El número no decide nada: lo que decide es
  la regla (lectura A).
- Ojo con el instrumento (V4-03): en `clase_mirova.py` los argumentos `--cons` y `--ocr` no tocan el conteo de
  protegidas, así que el 478 del auditor no es «tabla sola» aunque su comando pase la tabla.

### 290: la marca S151 de D27. CONFIRMADO, gravedad 2
- `v_290_d27_conteo.py` sobre la tabla de `88e97d84e` (sha256 `edefbbd3e5067cad`), ventana 2026-01-11 a 2026-10-14:
  **1.642 / 37 / 19 / 233**, exacto. Sobre la tabla de main: 1.589 / 37 / 20 / 228 (igual que el script del auditor).
  La tabla perdió 53 alertas dentro de una ventana cerrada y ganó una protegida de tarde (MODIS, Chillán). La marca sí
  declara ventana y fuente (`docs/MIROVA_DIVERGENCES.md:2862`); no lleva hash ni script.

### 291: D33. CONFIRMADO, gravedad 2
- La marca declara ventana (2026-09-18 a 2026-10-20). Mi cuenta (`v_291_d33_conteo_salida.txt`): en esa ventana main
  tiene 25 records MODIS K con cúmulo (la marca 24, con su filtro de píxeles y sin capados); en toda la historia 582.
  El script de D33 toma «todos los records K» según la frontera de `cambio_detector.js`, que #883 movió al 2025-02-15:
  por eso hoy da 581 y 95 pasadas, con Láscar (83) en vez de Chillán (11 de 12) dominando la razón contra MIROVA. El
  efecto F (1,05 a 1,08) es estable.

### 287: el «1 SIN EVIDENCIA» de A113 (D9, 207 de 214). CONFIRMADO EN PARTE, gravedad 2
- El estado SIN EVIDENCIA está bien propagado en main (`CLAUDE.md:1867`, `docs/MISSION.md:206`,
  `docs/MIROVA_DIVERGENCES.md:637`); que S159 no lo tocara no es un defecto.
- Confirmado en la memoria: `reference_s113_cirrus_d9_scope.md:3, 22-23, 37` y `project_s113_estado.md:40` repiten el
  207 sin marca; ninguno de los dos está en el índice de MEMORY.md.
- «Bajo K la población que lo sostenía cambió»: SIN DATO, no lo medí.

### 284: D-9, 14 pasadas NONE. REFUTADO, gravedad 1
- `experiments/_s151_alertas_minimas/frontera_salida.txt`, sección «PASADAS DISTINTAS de VIIRS 375 (A, B con par en el
  consolidado y C juntas; cada pasada una vez)»: «VRP <= 0,04 : {'NONE': 14}» y «VRP 0,05 : {'NONE': 5, 'ANOMALIA': 5}».
  La lectura propia de imágenes es la sección C, automática (`leer_png_mirova.py`, banner por máscara y por color
  coinciden en 2.702 de 2.702) y persistida. Re-corrido hoy sobre los datos del worktree: 15 y 6/5
  (`v_284_frontera_rerun_worktree.txt`): crece con el corpus y sigue sin excepciones. Única dependencia externa: el
  archivo local `mirova-tif-archive` (`leer_png_mirova.py:30`).

## 4. Hallazgos propios

### V4-01
- TÍTULO: El CLAUDE.md que carga cada sesión abierta desde OneDrive (loop/activo) no tiene ninguna marca S157 ni S158
- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\CLAUDE.md` (igual a `dbc377bbe:CLAUDE.md`)
- QUÉ PASA: loop/activo se separó de main el 2026-10-18 (merge-base `2ca366cdc`, #856) y no tiene #868 (propagación
  de K a los textos que se leen primero), #872 (D33) ni #875 (SINTOMAS). Conteos: S157 = 0, S158 = 0, frontera 09-18 =
  0 (main: 13, 0, 3; `s160-auditoria`: 13, 11, 4). El contexto de esta misma sesión muestra el texto de reversión de
  S153 sin la marca S157. Las sesiones heredan el documento más atrasado de los tres.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -c S157 "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/CLAUDE.md"`;
  `git -C C:/vrp-trabajo/s159-pruebas log --oneline dbc377bbe..d516b9d8c -- CLAUDE.md docs/MISSION.md docs/SINTOMAS.md`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 4

### V4-02
- TÍTULO: La marca V-15 del hueco nov-2025 a ene-2026 quedó falsa tras el relleno de #883
- ARCHIVO:LÍNEA: `CLAUDE.md:1603-1607` (main); el mismo texto en las otras dos ramas
- QUÉ PASA: la marca dice que hay un hueco del 2025-11-16 al 2026-01-28 en 9 de los 11 volcanes, que sólo Villarrica es
  continuo y que los primeros 19 días de la referencia sólo se parean en Villarrica. En main los 11 tienen record en 74
  de 74 días de esa ventana (689 a 880 records). Control positivo: en el tag `pre-s158-reemplazo-k`, Láscar, Llaima y
  PCC dan 0 de 74 y Villarrica 74.
- CÓMO SE VE EN EL DASHBOARD: invisible (el tablero ya muestra la serie entera).
- CÓMO REPRODUCIRLO: `python -I v_nuevo_hueco.py D:/vrp-trabajo/temporales/s160_audit/main/data/mirova_equivalent`
  (salida `v_nuevo_hueco_salida.txt`)
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3 (lleva a descartar la ventana nov-ene de cualquier pareo)

### V4-03
- TÍTULO: En clase_mirova.py los argumentos --cons y --ocr no cambian el conteo de protegidas
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py:227-231` (main)
- QUÉ PASA: las protegidas salen siempre de `cargar_referencia_unificada()` con sus valores por defecto (snapshot +
  respaldo 2026-04-08 + filas recuperadas); `--cons latest_consolidado.csv` sólo afecta la tabla de coherencia. Quien
  pasa la tabla para medir «tabla sola» recibe la unión, sin aviso.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer `scripts/clase_mirova.py:218-231` de main.
- CONFIANZA: CONFIRMADO por lectura; que la salida sea la misma con y sin el argumento es SOSPECHA (no lo corrí dos veces).
- GRAVEDAD: 2 (eje de F1a; también en SEGUIMIENTOS)

## 5. SEGUIMIENTOS
- V4-03 es del eje de F1a (instrumentos).
- El worktree `C:\vrp-trabajo\s159-pruebas` está en la rama `s160-auditoria` (la rama `s159-pruebas` apunta a
  `50e4ffb5f`) y otra sesión le hizo commits mientras yo medía (`411b5bda8` a `cda902080`). Es la causa probable de que
  F4 llamara «loop/activo» a ese linaje. Afecta a todo verificador que cite «la rama s159-pruebas».
- La tabla pierde y gana filas dentro de ventanas cerradas (53 alertas menos y una protegida nueva entre el 2026-01-11
  y el 2026-10-14): ya conocido por S159 (referencia estable); lo anoto como otra instancia.

## 6. VERIFICADO LIMPIO
- Sello del plan: `git diff 06e0fad3b -- docs/PLAN_AUDITORIA_S160.md` sólo trae el §11.2b. Vara: el propio plan.
- La instantánea de main es `d516b9d8c` salvo CRLF (Copahue y Lascar, sha256 tras quitar CR). Vara: `git show`.
- Hashes de la referencia: tabla `bc1522c24c924cb5`, OCR `94679246acbd0db5`, los del preámbulo.
- `f4/mis_conteos.py` re-corrido: salida idéntica a la del auditor (`v_rerun_mis_conteos.txt`, diff vacío).
- La rebaja del «207 de 214» está en CLAUDE.md, MISSION y el catálogo de main (`git grep` de la frase). Vara: A113.

## 7. SIN DATO
- Si la población del «207 de 214» cambió bajo K (287).
- El script de D33 contra MIROVA (no lo corrí porque baja datos de la red); uso la salida del auditor sólo para los n.
- U2, U4 a U7, U9, U11 y U14 de la tabla de M1, no verificados uno por uno.

## 8. FUERA DE ALCANCE
- Poner marcas, arreglar `clase_mirova.py`, despachar workflows o reprocesar.
