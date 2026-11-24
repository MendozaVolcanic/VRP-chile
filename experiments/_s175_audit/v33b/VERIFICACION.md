# VERIFICACION V33B: 15 afirmaciones de S175 (F2, F3, F5) que no pasaron el corte del verificador

## 1. Encabezado

- Hora del servidor al empezar: `Sun, 08 Nov 2026 14:14:24 GMT` (header `Date` de github.com); al cerrar las
  mediciones: `14:33:02 GMT`. Hora local de la maquina: UTC-3.
- Commit base sobre el que medi: `752d348bc67190e53b610989877e2405d238a1bc` (2026-11-07 03:38 UTC), extraido con
  `git -c core.autocrlf=false archive` a `C:\Users\nmend\vrp-temporales\s175_audit\v33b\arbol_752d348bc\`
  (sha256 verificados: `registro_vrp_consolidado.csv` f833bfde…, `registro_vrp_ocr.csv` 577a336e…,
  `frontend/index.html` e3963f56…, iguales a los de la tarea y a `git show`).
- origin/main de hoy: `cc32ab1fc85df430ec0887f81630482cc2b178e8` (2026-11-08 12:36:37 UTC), confirmado contra el
  remoto con `gh api repos/MendozaVolcanic/VRP-chile/commits/main` (`api_main_head.json` en CARPETA). La copia
  local de `origin/main` era la misma.
- Documentos de loop/activo: referencia de la tarea `395af8034` (2026-11-07 00:31 -03); los auditores citan
  `06de6876a` (2026-11-06 10:36 -03); ademas mire `origin/loop/activo` local `174bb691f` (2026-11-08 11:19 -03).
- Lector de la sombra V375-E: tag `s172-v375e-lector-resellado` (`12b49057f`), blob `e720dbc46`, extraido a
  `C:\Users\nmend\vrp-temporales\s175_audit\v33b\arbol_tag_lector\` (sin `data/`, `docs/`, `documentacion/`).
- Modelo: Claude Fable 5.1. Esfuerzo: SIN DATO (no veo el nivel con que corro).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\v33b\`
  Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\v33b\` (596 MB al cerrar; tope del verificador 0,5 GB
  superado en 96 MB por el arbol entero del tag que exige el lector: se declara, ver SEGUIMIENTOS).
- Discos al cerrar: C: 19 GB libres, D: 4,5 GB libres (no escribi en D:). Llamadas a la API de GitHub: 3 de 5.
- `caminos.md` escrito antes de abrir ningun archivo citado; sha256 del cuerpo `742bb509…`, sellado a las
  14:16:01 GMT y no editado despues.
- Que NO mire: ningun `INFORME.md` ni las columnas de razonamiento de los `hallazgos.csv` de f2, f3 y f5; ninguna
  llamada a NASA ni a Earthdata; el log del check `pytest` rojo de #951 (solo su conclusion por la API); el estado
  de la memoria del agente a la hora de la auditoria F3 (no tiene historial); la identidad detras de la cuenta
  `MendozaVolcanic` (asumo que es la de Nicolas: SOSPECHA); el remoto `origin/loop/activo` (use la copia local, 3 h
  mas nueva que la referencia de la tarea); ningun workflow.

## 2. En una pantalla

- De las 15 afirmaciones: 12 CONFIRMADAS, 3 CONFIRMADAS EN PARTE (F2-210, 261, 265), 0 REFUTADAS, 0 SIN DATO
  (en 264 el CI rojo y el «fuera de main» se confirman; la causa que da la bitacora queda SOSPECHA). Todas se reproducen con los scripts de los auditores corridos de nuevo sobre mi propio
  arbol de la base: banco F2 identico linea a linea, `sin_geometria` identico, `f5_medir_out.json` identico byte a
  byte, lector de la sombra con los mismos contadores (3 noches y 9 alertas con la tabla de la vara; 4 y 26 con la
  tabla raiz).
- Lo que mas pesa (gravedad 2): el lector que decidira la adopcion de V375-E no esta en main (F2-209); la cola de
  decisiones §5 lleva cinco filas que la propia bitacora ya cerro (255, y 261 es un caso de la fila D-39); 18
  pasadas de 1 MW o mas sin geometria quedan fuera del denominador protegido por decision documentada, 2 de ellas
  no publicadas (F2-211); el criterio «ninguna protegida perdida» es vacuo en 5 de 11 volcanes en la ventana del
  audit (308, 6 de 11 con la ventana de 60 dias); C-04 sigue abierto y la distancia del OCR de Tupungatito
  2026-09-28 05:18 es la misma, con la misma nota, que la de las 05:36 (F2-213).
- Nada de lo verificado cambia hoy una alerta publicada: los efectos son de gobernanza, documentos y medicion.
- Hallazgo propio nuevo: las dos «protegidas sin record» de marzo (F2-210) son filas solo OCR (v21, antes del hito
  de calibracion del 2026-06-11) cuyas horas no existen en la tabla de MIROVA; que haya habido pasada es SIN DATO.

## 3. Veredictos por afirmacion (ordenados por gravedad, la peor primero)

### F2-209. El lector de la sombra V375-E no esta en la base ni en origin/main
- VEREDICTO: CONFIRMADO. GRAVEDAD (mia): 2.
- EVIDENCIA: `git ls-tree -r 752d348bc | grep e720dbc46` y `git ls-tree -r origin/main | grep e720dbc46` dan vacio
  (rc 1); `git ls-tree -r --name-only {752d348bc,origin/main} | grep -i leer_sombra` vacio; `git merge-base
  --is-ancestor fc3912cb2 {752d348bc,origin/main}` rc 1. El blob vive en el tag `s172-v375e-lector-resellado`
  (`experiments/_s168/v375e_sombra/leer_sombra_v375e.py`) y en `origin/claude/s172-v375e-relector`; tambien en
  `s170-v375e-lector` y `s173-prereg-retro-sellado`. Comprobado contra el remoto: main es `cc32ab1fc`
  (`api_main_head.json`), igual a la copia local.
- MATIZ (camino T5): el MISMO blob `e720dbc46` esta en `origin/loop/activo` como
  `experiments/_s173_cenit/v375/_leer_sombra.py` (copia para un verificador), y `origin/main` solo lo nombra en un
  comentario (`experiments/_s172_retro_paquete/leer_retro.py:132`). Ningun workflow de main lo corre (`git grep
  leer_sombra_v375e origin/main` da solo ese comentario). La lectura de la ventana P depende de un archivo fuera
  de main (regla de S174 «instrumento fuera de tests/ no tiene CI»).
- COMO SE VE EN EL DASHBOARD: invisible.

### 255. Cola de decisiones §5 con cinco filas desfasadas (D-1, D-19, D-23, D-37, D-39)
- VEREDICTO: CONFIRMADO. GRAVEDAD: 2.
- EVIDENCIA: las cinco filas estan en las lineas 526 (D-39), 528 (D-37), 540 (D-23), 543 (D-19) y 545 (D-1) de
  `tasks/LOOP_OBJETIVOS.md` en `06de6876a`, en `395af8034` y en `origin/loop/activo` `174bb691f`, con texto
  identico (`255_filas_395af8034.txt` en el temporal). Contra la realidad:
  - D-39 dice `**PENDIENTE**` (l. 526) y la misma bitacora dice en l. 2554 «D-39 CERRADO; identidad de #919
    comprobada aparte» (TEXTO) y en l. 2701 «Nicolás da permiso para D-39».
  - D-37 dice «PENDIENTE, con plazo 2026-11-02 13:00 UTC: merge de #892» (l. 528); #892 esta en main
    (`3489e55c3 S159: vigilancia por plataforma ... (#892)`) y la bitacora l. 3945 dice «#892, #891, #893 y #895
    mergeados» (TEXTO).
  - D-23 dice «EN CURSO ... reproceso de los 3.231 records MODIS» (l. 540); main tiene `1bea8c35e S158: #883
    mergeado y verificado (68.072 de 68.072 con K ...)`.
  - D-19 propone «pre-registrar MxD03 sobre K» (l. 543); main tiene `e949f06c4 S163 MODIS: sello D-48 del
    pre-registro de MxD03 en main ... (#910)`.
  - D-1 «Adoptar conectiva max en VIIRS 375 ... pendiente | pendiente» (l. 545); el perfil de la base
    `pipeline/profiles/mirova_equivalent.yaml:288` dice «S153 (K): conectiva de prosa de Coppola 2016a para los
    Tests 2 y 3 (`max` ...)» (TEXTO) y `enable_test1_path: false` (l. 287).
- La fila D-39 ademas contiene R13 («sólo con el sí de Nicolás»), que es la afirmacion 261: se funden en parte.
- COMO SE VE EN EL DASHBOARD: invisible (documento de trabajo).

### F2-211. 18 pasadas sin geometria de 1 MW o mas fuera del denominador protegido; 14 de Chillan; 2 no publicadas
- VEREDICTO: CONFIRMADO. GRAVEDAD: 2.
- EVIDENCIA: re-corri `sin_geometria.py` del auditor sobre mi arbol
  (`sin_geometria_v33b_salida.txt`): «V375 sin_geometria n 64 publicadas 57»; 18 filas `>=1 MW`, 14 de
  NevadosDeChillan, 2 con `pub 0` (Villarrica 2026-10-29 05:36 VIIRS_SNPP, MIROVA 2,83 MW, nuestro `dc far`;
  Copahue 2026-10-16 06:18 VIIRS_SNPP, MIROVA 1,34 MW, `dc far`). Salida identica a la del auditor (`diff` vacio).
  Ventana 2026-03-01 a 2026-11-07; denominador 64 pasadas sin geometria de VIIRS 375.
- POR QUE ESTAN FUERA: `scripts/clase_mirova.py` l. 25 a 28 (752d348bc), TEXTO: «de estas filas no se sabe la
  distancia, asi que NO son alerta protegida bajo A (decision del coordinador del loop, 2026-10-15, la
  conservadora ...)». Es una decision documentada, no un descuido; lo que el auditor agrega es su tamano en MW.
- COMO SE VE EN EL DASHBOARD: en 16 de las 18 el operador ve la anomalia (publicadas, `summit`); en las 2 `far`
  no ve nada mientras MIROVA publico 2,83 y 1,34 MW. Las dos son Suomi NPP, cuyo OCR antes del 2026-10-09 puede
  llevar distancia de otra pasada (S150): la clase `far` nuestra no esta contrastada con la posicion de MIROVA.

### F2-213. C-04 actualizado: Tupungatito 2026-09-28 05:18, distancia de MIROVA igual a la de su pasada de las 05:36; sigue abierto
- VEREDICTO: CONFIRMADO. GRAVEDAD: 2.
- EVIDENCIA (otro camino: lei las filas crudas del OCR, no la salida del auditor): en
  `registro_vrp_ocr.csv` del snapshot, la fila `2026-09-28 05:18:00` tiene VRP 2,51, `Distancia_km` 5,27, nota
  «Estrella verde en Y=256 -> 5.27 km (límite 7.0 km, geometría medida)», `Fecha_Proceso_UTC`
  2026-09-28T09:01:47Z; la fila `05:36:01` tiene VRP 0,09, `Distancia_km` 5,27 y la MISMA nota, procesada antes
  (08:31:32Z). Las dos comparten `Distancia_aprox_imagen` = `data/png/Tupungatito/20261022_085933_VIIRS375_Dist.png`
  (una imagen del 2026-10-22, metodo «ambiguo»). La tabla consolidada no tiene ninguna pasada a las 05:18 ese
  dia (tiene 04:42 RUTINA, 05:36 ALERTA 0,09 MW dist 5,21, 06:18 RUTINA): la protegida de 2,51 MW es solo OCR.
  `docs/COLA_CAMPO.md` l. 15: C-04 «abierto» en 752d348bc y en origin/main `cc32ab1fc`.
- Nuestro record (salida del auditor, `perdidas_protegidas_base_salida.txt`): pc 0,15 MW a 21,6 km, 0 pixeles
  dentro de 7 km; no lo volvi a medir.
- COMO SE VE EN EL DASHBOARD: Tupungatito sin anomalia esa pasada; MIROVA (solo OCR) 2,51 MW.

### 308. El criterio «ninguna protegida perdida» no tiene casos en 5 de 11 volcanes
- VEREDICTO: CONFIRMADO. GRAVEDAD: 2.
- EVIDENCIA por otro camino (`recontar_i10.py` propio, sin el pkl del auditor; salida
  `recontar_i10_salida.txt`): filas de referencia leidas 47.626; protegidas nocturnas unicas por volcan en
  2026-09-01 a 2026-11-07: Lastarria 0, Llaima 0, Chaiten 0, Copahue 0, PlanchonPeteroa 0 (5 de 11; Chillan 136
  como control positivo). Con la ventana real del audit semanal (`aw.WINDOW_DAYS` = 60, 2026-09-08 a 2026-11-07)
  son 6 de 11 (se suma Villarrica); desde 2026-03-01 son 3 de 11 (Llaima, Chaiten, Copahue). Mi recuento coincide
  con el I10 del auditor y mi re-corrida de `f5_medir.py` (copia con solo `OUT` cambiado) da un JSON identico.
- QUE SIGNIFICA: en esos volcanes el «cumple» del criterio es vacuo (0 de 0), no una verificacion. Como lo
  presenta el issue semanal no lo mire: SOSPECHA de que salga como cumplido y no como SIN DATO.
- COMO SE VE EN EL DASHBOARD: invisible (es del audit).

### F2-208. Fecha de parada de la sombra V375-E: noche 30 con datos, 2026-12-02 si no falta ninguna (4 noches y 26 alertas al 2026-11-06)
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1 (es informacion, no defecto).
- EVIDENCIA: `leer_sombra_v375e.py` del tag, l. 90 `PARADA_NOCHES, PARADA_ALERTAS = 30, 40` y l. 279 a 290
  `noche_parada`: cuenta noches con dato y se detiene cuando `noches >= 30 and alertas >= 40` (las dos). El
  perfil `pipeline/profiles/sombra_codigo_mirova.yaml:7` (752d348bc), TEXTO: «30 noches o 40 alertas que decidan,
  lo que llegue último». 2026-11-03 + 29 dias = 2026-12-02 (`python`). Corri el lector dos veces desde el arbol
  del tag con `GIT_DIR` apuntando al repo (solo lectura): con la tabla del snapshot (la vara) «noches 3 de 30,
  alertas 9 de 40»; con `latest_consolidado_base.csv` de insumos «noches 4 de 30, alertas 26 de 40»
  (`lector_v33b_snapshot_stdout.txt`, `lector_v33b_raiz_stdout.txt`; S0, S1, S7, S10 OK; rc 5 = parada no
  alcanzada, no escribio nada). La sombra de la base tiene pasadas VIIRS 375 el 11-03, 04, 05 y 06 (30, 32, 27,
  33), ultimo record 2026-11-06 06:48 UTC.
- MATIZ: la vara de la tarea (snapshot) da 3 noches; el «4 y 26» del auditor sale con la tabla raiz, mas fresca.
  A 6,5 alertas por noche las 40 se alcanzan hacia la noche 7, asi que la condicion que manda es la de 30 noches.
- COMO SE VE EN EL DASHBOARD: invisible.

### 259. D25 NO SE ADOPTA cerrado bajo una delegacion general (D-48), no con una frase sobre D25
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1.
- EVIDENCIA: `docs/MIROVA_DIVERGENCES.md` l. 2863 a 2865 (752d348bc; en origin/main l. 2864, mismo texto), TEXTO:
  «decisión de Nicolás: «sobre las decisiones mías haz lo que tú recomiendes», sobre la recomendación de no
  adoptar». Bitacora `395af8034` l. 3702 a 3704: «Decisión de Nicolás (D-48, 2026-10-24): «sobre las decisiones
  mías haz lo que tú recomiendes», sobre las 14 del §9 del programa más las del traspaso S162. Aplicado: D25 NO SE
  ADOPTA ...» (TEXTO). Las unicas frases textuales de Nicolas que nombran D25 en la bitacora son D-35 y D-34
  (l. 530, 531: despacho del brazo de sensibilidad y metodologia), ninguna sobre adoptar o no.
- MATIZ: la delegacion se aplico a D25 de forma explicita y quedo escrita como «Revocable por Nicolás» (l. 3608 y
  3702): es de segunda mano, pero documentada.

### 260. La A45 de #920 («Si, los tres apagados») quedo en el repo solo de segunda mano
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1.
- EVIDENCIA: `git log -1 --format=%B 4164d4547`: «Si explicito de Nicolas en el chat de esta sesion (A45); tag
  pre-s165-mxd03-modis.» (TEXTO), sin la frase. La frase solo aparece en la bitacora, l. 2468 de `06de6876a` y
  l. 2488 de `395af8034`: «Según la sesión: A45 dado por Nicolás en su chat («Sí, los tres apagados»)» (TEXTO).
  `git grep -i 'tres apagados' origin/main` da solo `tests/test_guard_mxd03_flags_s165.py:8` («con los tres
  apagados», descripcion de la prueba, no la frase). `4164d4547` esta en main por `ab3ff9fe3 Merge pull request
  #920`.

### 261. #895 (R13 del sync) entro a main sin frase de Nicolas en la bitacora mientras D-39 lo pedia
- VEREDICTO: CONFIRMADO EN PARTE. GRAVEDAD: 1.
- QUE PARTE SE CONFIRMA: la fila D-39 (l. 526) pide para R13 «sólo con el sí de Nicolás» (TEXTO) y la bitacora
  solo registra «#892, #891, #893 y #895 mergeados» (l. 3945) y D-43 «resueltas ... 7 (#894, #895)» (l. 522): no
  hay frase. `.github/workflows/sync-mirova-csv.yml` l. 90 a 102 (752d348bc) es R13 («S160 (R13, hallazgo H-V1
  ...): si el push pierde la carrera, NO se rebasa»).
- QUE PARTE NO: el PR #895 lo abrio y lo mergeo la cuenta `MendozaVolcanic` el 2026-10-22 11:29 UTC
  (`api_pr895.json`: `merged_by` = `user` = MendozaVolcanic; squash `6547f5315`, autor NMendoza). Si esa cuenta es
  la de Nicolas (SOSPECHA, no lo verifique), el si fue el click del merge, no una frase.
- Se funde con 255 (la fila D-39 sigue PENDIENTE).

### 262. Decision 3 de la sombra de los 34 implementada con radio max(4 km, inner) en vez de 4 km
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1.
- EVIDENCIA: texto de la decision en la bitacora `06de6876a` l. 959: «decisión 3 (marcar en la lectura las pasadas
  con píxeles a menos de 4 km del vecino)» (TEXTO). Squash `438a010ab` (#935) trae el commit «radio del vecino =
  max(4 km, inner_radius_km), desde cráter y punto nominal (V935-01)» y la prueba
  `tests/test_vecinos_sombra_34_s173.py` (diff l. 544: «Villarrica inner 5 km (KML de MIROVA) > 4; PCC inner 20»),
  asi que el cambio no es neutro. La bitacora l. 933 lo documenta como arreglo del verificador V935-01 («el
  lacolito de PCC en la grilla de Antillanca no se marcaba con 4 km desde el cráter»). Las decisiones 3 y 4
  estaban «pendientes de Nicolás» a las 15:15 UTC (l. 975) y se resolvieron bajo «en el resto haz lo que
  recomiendes» (l. 951 a 952), sin frase de Nicolas sobre el radio.
- COMO SE VE EN EL DASHBOARD: invisible (la sombra de los 34 esta fuera de Pages por la decision 4).

### 263. El texto sellado de la regla MOD-D cambio en una linea al sellarse; el archivo sigue llamandose BORRADOR
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1.
- EVIDENCIA: re-corri `sello_regla_modd.py` del auditor (`sello_regla_modd_v33b_salida.txt`): sha256 LF de
  `3a3b5e495` = `7f300a14…` (coincide con la cabecera: control positivo), base y tag `s173-regla-modd-sellada`
  = `bf1705d9…`, 9 lineas distintas. Por otro camino (difflib propio) la unica linea del cuerpo que cambio es
  «Falta la frase de sello de Nicolás.» a «Falta la frase de sello de Nicolás (dada, ver la cabecera).»; el resto
  es la cabecera nueva, que dice «Desde aquí el texto no se cambia» (TEXTO). El sha `7f300a14` ya no se reproduce
  desde el cuerpo actual. `REGLA_REVERSION_MODD_BORRADOR.md` existe con ese nombre en 752d348bc y en origin/main,
  identicos (`base == origin/main: True`).

### 264. #951 mergeado con CI rojo en la rama de V750 (fuera de main)
- VEREDICTO: CONFIRMADO (el CI rojo y el «fuera de main»); la causa, EN PARTE. GRAVEDAD: 1.
- EVIDENCIA: `gh api .../commits/c666ab08f/check-runs` (`api_checks_c666ab08f.json`): 1 check `pytest`,
  `conclusion: failure`, 2026-11-05T21:54:02Z. `git log -1 c8152580b`: 2026-11-05 22:10 -03, solo en
  `origin/claude/s162-viirs750-2-918174`; `git merge-base --is-ancestor c8152580b origin/main` rc 1. La bitacora
  misma lo declara (`06de6876a` l. 637 y `395af8034` l. 657): «CI con 1 falla ajena al cambio:
  `test_csv_max_age_under_48h`» (TEXTO). Que la falla sea esa prueba no lo verifique (no abri el log): SOSPECHA.

### 265. El indice de memoria tiene desfasado el estado de S174 (#945, #950, #951)
- VEREDICTO: CONFIRMADO EN PARTE. GRAVEDAD: 1.
- EVIDENCIA: la memoria vive fuera del repo y no tiene historial, asi que el estado a la hora de la auditoria F3
  (`f3/hallazgos.csv` 2026-11-07 06:07 -03) es SIN DATO. Hoy `MEMORY.md` (mtime 2026-11-08 10:48 -03) l. 28 dice
  «S174 CERRADA 2026-11-07: #945, #952, #953 y #954 mergeados» y `project_s174_estado.md` (2026-11-07 17:03 -03)
  nombra #945, #953, #952 y #954: lo de #945 quedo corregido despues de la auditoria. Ni el indice ni esa ficha
  nombran #950 (`77e54e8e0`, en main) ni #951 (`c8152580b`, en la rama de V750): `grep -c '#950|#951'` da 0 y 0.
  El script del auditor (`git log --grep`) mide el repo, no la memoria: no sirve de vara para esta afirmacion.

### 310. El ratio de magnitud de Lastarria V375 cambia de banda al restringirlo a la misma pasada
- VEREDICTO: CONFIRMADO. GRAVEDAD: 1.
- EVIDENCIA: re-corrida de `f5_medir.py` (copia con `OUT` cambiado, insumos del auditor en
  `C:\Users\nmend\vrp-temporales\s175_audit\f5\root` y `f5_base.pkl`; `root` verificado igual a la base con sha256
  LF): `I4` identico, `Lastarria|VIIRS375` mediana por noche 0,664 (n 15, «bajo») contra misma pasada 0,712
  (n 13, «en banda»), banda (0,7; 1,4), ventana 2026-09-03 a 2026-11-02. Es la unica fila que cambia de banda;
  la diferencia con el borde es 0,036 y 0,012, con n 13 a 15.
- POR QUE NO SE VE: `scripts/auto_audit_weekly.py:145` (752d348bc) `UNDER_BAND_KNOWN = {"Lastarria", "Lascar",
  "Isluga"}` y l. 161: la sub-banda de Lastarria no abre issue en ninguna de las dos lecturas. Invisible para el
  operador.

### F2-210. Dos protegidas de marzo sin record nuestro (Lascar 2026-03-11 06:18, Isluga 2026-03-10 04:54)
- VEREDICTO: CONFIRMADO EN PARTE. GRAVEDAD: 1.
- QUE PARTE SE CONFIRMA: re-corri `f2_banco_v375.py` sobre mi arbol (`banco_v33b_0301_1107_salida.txt`, identico
  al del auditor): «PROTEGIDAS SIN RECORD NUESTRO SN (2)»: Lascar 2026-03-11 06:18 (4,35 MW, OCR, dist 1,73) e
  Isluga 2026-03-10 04:54 (1,45 MW, OCR, dist 3,01). Nuestros records VIIRS 375 esa noche (script propio sobre
  `data/mirova_equivalent`): Lascar 04:54 NOAA-20, 05:48 NOAA-21, 06:36 NOAA-20; Isluga 05:12 NOAA-20, 06:06
  NOAA-21; ninguno a 120 s (`TOL_S = VENTANA_S`, `banco_paridad.py:78`). No hay dias de marzo sin records VIIRS 375
  en ninguno de los dos volcanes (31 de 31): no es un hueco de cobertura general.
- QUE PARTE NO: las dos filas son solo OCR, `Version_OCR` 21.0, `Distancia_km` 0.0 en la columna (la distancia va
  en la nota: «Grupo píxeles rojos Y=284 (área=31 px², dist≈1.73 km)», «Estrella en Y=288 ... dist≈3.01 km»), de
  antes del hito de calibracion del OCR del 2026-06-11 (A119). La tabla consolidada de MIROVA no tiene pasada a esas
  horas: Lascar 2026-03-11 tiene 04:54:01 (ALERTA 0,81 MW) y 06:36:01; Isluga 2026-03-10 tiene 05:12:01 (ALERTA
  0,35 MW) y 06:36. Si a las 06:18 y 04:54 hubo una pasada (Suomi NPP, probablemente) que el NRT no proceso, o si la
  hora del OCR es de otra imagen, es SIN DATO sin NASA. Por eso bajo la gravedad a 1.
- COMO SE VE EN EL DASHBOARD: en esas noches el operador ve las otras pasadas (Lascar 0,21 y 3,04 MW; Isluga 0,40
  y 0,24 MW), no una pasada a esa hora.

## 4. SEGUIMIENTOS (fuera de mi eje, reproducibles)

- S-1. El lector de la sombra no corre desde un arbol suelto: `ventana_ya_leida` exige resolver `origin/loop/activo`
  con git (`leer_sombra_v375e.py` l. 812 a 816) y `cargar_deps` exige el arbol entero del tag (`experiments/_s162_v375`,
  `mirova_port`). Reproducir: correrlo desde `git archive` del tag sin `.git`: rc 2 «origin/loop/activo no se puede
  resolver». Lo resolvi con `GIT_DIR` del repo (solo lectura). Confianza CONFIRMADO, gravedad 1.
- S-2. Las dos filas OCR de Tupungatito 2026-09-28 (05:18 y 05:36) comparten `Distancia_aprox_imagen` del
  2026-10-22 (`20261022_085933_VIIRS375_Dist.png`, metodo «ambiguo»): la distancia aproximada del scraper apunta a
  una imagen de 24 dias despues. Es de Mirova-v1, no de este repo. CONFIRMADO (columna leida), gravedad 1.
- S-3. `alerta_protegida` acepta filas solo OCR anteriores al hito 2026-06-11 (las dos de F2-210, OCR v21): A119 dice
  que el OCR de ese tramo esta mal calibrado. Si la lectura A las cuenta como protegidas, el recall de marzo se mide
  contra una referencia que el propio proyecto declara dudosa. SOSPECHA (no lei si `calidad_referencia_mirova` las
  excluye en el banco), gravedad 2.
- S-4. Mi temporal quedo en 596 MB (tope del verificador 0,5 GB): 409 MB son el arbol del tag que el lector exige.
  Se borra al terminar la sesion si quien orquesta lo pide; no lo borro yo (los instrumentos se quedan).
- S-5. El criterio de 308 en el issue semanal: comprobar si `auto_audit_weekly.py` imprime «cumple» o «sin casos»
  por volcan cuando `n_prot` es 0 (no lo mire). SOSPECHA, gravedad 2.

## 5. VERIFICADO LIMPIO

- El banco F2 del auditor es reproducible: mi corrida sobre un arbol propio de 752d348bc da una salida identica
  linea a linea (`diff` vacio salvo el nombre del arbol); sha256 de index.html, cons y ocr en la salida coinciden
  con la vara (`e3963f56`, `f833bfde`, `577a336e`). Vara: la de la tarea (predicado de `index.html` por node,
  `etiquetar` con D-9, `TOL_S`).
- `f5_medir.py` es reproducible: JSON identico byte a byte (`todo el json igual: True`), sobre `root` del auditor
  verificado igual a la base por sha256 LF (4 archivos clave y `volcanoes.yaml`).
- `sello_regla_modd.py` reproduce su control positivo (`7f300a14` en `3a3b5e495`).
- Las cinco filas de 255 tienen la misma numeracion y texto en las tres versiones del documento.
- origin/main local = remoto (`cc32ab1fc`).

## 6. SIN DATO

- Estado de la memoria del agente al momento de la auditoria F3 (sin historial).
- Si existio una pasada satelital a las horas de las dos protegidas de marzo (requiere NASA/CMR; prohibido).
- Que prueba fallo en el check `pytest` de `c666ab08f` (no abri el log).
- Identidad de la cuenta GitHub `MendozaVolcanic`.
- Nivel de esfuerzo con que corri.

## 7. FUERA DE ALCANCE

- No audite los otros hallazgos de S175 ni los frentes F0, F1, F4; no toque `pipeline/`, workflows ni git que
  escriba; no corri NASA; no abri `INFORME.md` de ningun auditor.

## 8. Archivos en CARPETA

- `caminos.md` (sellado antes de leer), `VERIFICACION.md`, `hallazgos.csv`, `escribir_csv.py`, `recontar_i10.py` y
  `recontar_i10_salida.txt`, `banco_v33b_0301_1107.json`, `banco_v33b_0301_1107_salida.txt`, `banco_v33b_stderr.txt`,
  `sin_geometria_v33b_salida.txt`, `lector_v33b_snapshot_stdout.txt`, `lector_v33b_raiz_stdout.txt`,
  `sello_regla_modd_v33b_salida.txt`, `f5_medir_v33b_stdout.txt`, `f5_medir_v33b_stderr.txt`, `api_main_head.json`,
  `api_pr895.json`, `api_checks_c666ab08f.json`.
- Temporal `C:\Users\nmend\vrp-temporales\s175_audit\v33b\`: `arbol_752d348bc\`, `arbol_tag_lector\`,
  `f5_copia\` (copia de `f5_medir.py` con `OUT` cambiado, `hacer_copia.py`, `f5_medir_out.json`, `i2_pares.csv`),
  `LOOP_*.md` (las tres versiones de la bitacora), `255_filas_395af8034.txt`, `lector_out_*`.
