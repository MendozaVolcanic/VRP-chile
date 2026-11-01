# Verificador del censo del oráculo V750 (S159): veredictos sobre las cinco afirmaciones

## 1. Encabezado

- Fecha y hora del servidor (GitHub, header `Date`): Thu, 22 Oct 2026 04:40:24 GMT (inicio 04:24:27 GMT).
- Commit sobre el que medí: el worktree `C:\vrp-trabajo\s159-m` estaba en `f7dba3c57` al empezar; durante la sesión
  pasó a `42e2b799a` (commit del auditor, que agrega 03_detalle.py, 04_por_que_no_publica.py,
  05_pixeles_fuera_del_recuadro.py, INFORME.md y resultados_crudos.tar.gz; `git diff --stat f7dba3c57 42e2b799`:
  sólo archivos nuevos, `02_analizar.py` y `objetivos.json` no cambiaron). Records de producción: `origin/main`
  533398f8f según `poblacion_completa.json`. Código del run del censo: `7ee78d03` (rama `s159-oraculo-disparo`); el
  compare `533398f8f...7ee78d03` trae 300 archivos y ninguno de `pipeline/`, `frontend/index.html`,
  `volcanoes.yaml`, `scripts/banco_paridad.py` ni del oráculo (`verificador/compare_533398f8f_7ee78d03_files.txt`).
- Modelo: Claude Fable 5.1 (claude-fable-5-1). Esfuerzo: el de la tarea (no se fijó uno explícito).
- CARPETA: `C:\vrp-trabajo\s159-m\experiments\_s159\oraculo_censo\verificador\`.
- Qué NO miré: el INFORME.md del auditor (a propósito, hasta escribir esto); el código del oráculo portado
  (`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`) más allá de usar `radiancia_a_temperatura`; el `.m` de
  MIROVA; los runs del frente N más allá de contar sus pasadas; el pipeline de K (`store.append_record`,
  `process_viirs_mod.py`); los gránulos (no bajé ninguno); el 18 y 19 de octubre (fuera de la población por diseño);
  los TIF de MIROVA.
- Disco al terminar: C: 14 GB libres, D: 9,4 GB libres (sobre el piso de 3 GB).
- Camino sellado antes de abrir nada citado: `caminos.md` (sha256 del contenido `2c1cedfc…dfec37f6`, hora del
  servidor 04:26:28 GMT al final del archivo).

## 2. En una pantalla

1. Las cinco afirmaciones se sostienen en sus números: re-corrí `02_analizar.py` sobre los dos runs y las tablas
   salieron byte a byte iguales a las del auditor (sha256 de `tabla_por_pasada.csv` = `33270abf…`), y un recuento
   propio desde los crudos, sin pasar por el analizador, da los mismos K 54, O-def 5, O-sens 15 de 5.353, 6 protegidas
   perdidas por O-def (todas Cordón Caulle), 0 perdidas y 1 ganada por O-sens, ΔE −60 y −90, rangos −62 a −43 y −92
   a −73, y con el rescate −62 y −92 sin SIN DATO.
2. Lo que cambia la lectura, no el número: dos de las «bajo 1 MW perdidas» del oráculo no son del detector de
   MIROVA sino del record sintético (VOC-01: Láscar 2026-08-26, el oráculo alertó el cráter a 1,5 km y un píxel a
   17,3 km fuera del recuadro, el centroide sin pesos cae a 9,3 km y queda `far`; VOC-02: Cordón Caulle 2026-10-21,
   O-sens suma 11 píxeles a 10,3 MW con t_max 270,8 K y el filtro de cirrus del tablero lo apaga). Las 6 protegidas
   perdidas por O-def son geometría de la caja: O-def no tiene ningún píxel y O-sens encuentra 1 a 2 a 7,7 a 7,8 km
   del centro del TIF (el lacolito queda fuera de la cumbre de 7 × 7).
3. Controles con salvedad de redacción: «1.006 de 1.006» del control 2 son 503 pasadas × 2 cajas (508 de N: 2 fuera,
   3 SIN DATO del 12-oct); en el control 1 la pata de magnitud compara 422 pares, los otros 5.198 son None-None; el
   control 4 «detecta» es píxeles > 0, no «publica». Los 4 jobs rojos son exactamente los chunks 10, 11, 17 y 18 con
   los 20 `sin_granulo` del 12-oct, y los 32 JSON traen las 5.746 pasadas sin duplicados.
4. Lectura con la tabla sola (c): 5 alertas que deciden vienen sólo del OCR (todas protegidas, desde el 13-jun); con
   la tabla sola O-def pierde 5 en vez de 6, O-sens sigue en 0 perdidas y 1 ganada, ΔE no cambia (−60 y −90).
5. Población (d): 30 pasadas RUTINA de VIIRS 750 de la tabla en la ventana no tienen record nuestro a 120 s y quedan
   fuera del censo (0,5 % del universo de negativos limpios posibles); 0 alertas quedan fuera; a 120 s ninguna fila se
   parea con dos records (a 480 s, 149).

## 3. Veredictos por afirmación

### Afirmación 1: los cuatro controles del pre-registro §5 pasan

**Veredicto: CONFIRMADO EN PARTE (los cuatro pasan; tres necesitan una precisión de redacción). Gravedad propia: 1.**

- Re-corrida: `02_analizar_salida_verif.txt` líneas 4 a 8 iguales a las del auditor (la única diferencia entre los
  dos archivos de texto son 178 bytes NUL al final del suyo, ver SEGUIMIENTOS).
- Control 1 (K = producción, 5.620 de 5.620): CONFIRMADO en la publicación; la vara no es tautológica: `pub_prod` se
  calcula con node sobre el record de producción de `origin/main` (`scripts/banco_paridad.py:294-296` dentro de
  `cargar_nuestros`, consumido por `experiments/_s159/n/01_poblacion.py:118-119`) y `pub_K` sobre el record que el
  job escribió con `store.append_record` sobre el gránulo recién bajado (`probe_censo.py:90`). Mi recuento propio
  (`verif_recuento_salida_censo.txt`, bloque «control 1 propio»): pub distinta 0, pc.vrp_mw distinto 0. **Precisión**:
  5.198 de los 5.620 pares son None-None (ni producción ni K tienen cúmulo), así que la pata de magnitud a 0,001 MW
  compara 422 pares, no 5.620; la de publicación sí compara 5.620. El control pasa en los 15 SHA de código distintos
  que escribieron los records de producción (`regimen.codigo_sha`, todos con `processed_utc` de octubre de 2026).
  Camino C1.5 (gránulo): en 9 de las 5.620 el record K es de otro archivo que el de producción (VOC-03).
- Control 2 (oráculo = N): CONFIRMADO; «1.006» son comparaciones pasada × caja en 503 pasadas
  (`02_analizar.py:209-210`). Las 508 que N midió son 503 ok + 2 fuera del gránulo + 3 SIN DATO del 12-oct
  (`verif_control2_box0_salida.txt`). Es un control de regresión del port (mismo código sobre los mismos gránulos), no
  de corrección; lo digo porque la afirmación lo llama control sin ese matiz.
- Control 3 (nulo): CONFIRMADO; 1.006 = 956 (2 perturbaciones × 478 publicaciones del oráculo: 210 O-def + 268
  O-sens, contadas por mí en el bloque (b)) + 50 inyectadas; 0 sin cambio. El 1.006 coincide con el del control 2 por
  casualidad, no son el mismo conjunto. Mi control positivo propio: los 5.353 K forzados a `far` dan 0 publicaciones;
  5.348 negativos sin publicar por O-def con cúmulo inyectado de 0,3 MW publican 5.348.
- Control 4 (razón mediana 1,000 y 0,999): CONFIRMADO en los números (líneas 7 y 8). **Precisión**: «detecta» es
  `npix > 0` (`02_analizar.py:215`), no el predicado «publica»; y 23 de 193 (O-def) y 41 de 241 (O-sens) razones quedan
  fuera de 0,8 a 1,25, con un extremo en Cordón Caulle 2026-10-21 (10,3 MW del oráculo contra 0,36 de MIROVA, VOC-02).

### Afirmación 2: negativos limpios publicados sobre 5.353 ok: K 54, O-def 5, O-sens 15

**Veredicto: CONFIRMADO. Gravedad propia: 1 (una nota de denominador).**

- Recuento propio desde los crudos (`verif_recuento.py`, carga propia de los 32 JSON: 5.746 ids, 0 duplicados, 0 ids
  fuera de objetivos; record sintético reimplementado desde PREREGISTRO.md §3 y comparado con `record_oraculo`: 0
  distintos de 11.240; node corrido una vez con las cinco columnas): K 54, O-def 5, O-sens 15 de 5.353 ok.
- Por otro camino: `pub_prod` de producción en los mismos 5.353 ok es 54; en los 5.476 negativos de la población
  también 54 (0 en los 106 «fuera», 0 en los 17 negativos SIN DATO). O sea que el denominador 5.353 contra el 5.476 del
  pre-registro §4 («el conteo principal usa las 5.476») no mueve el numerador de K: 54/5.476 = 0,99 % en vez de 1,01 %.
  El analizador imprime los dos denominadores en la misma línea (`02_analizar.py:262-263`); la afirmación eligió el ok.
- «Negativo limpio» en el código es más estricto que la vara del preámbulo: exige fila RUTINA del consolidado con VRP 0
  **y** noche del sensor sin alerta ni falso positivo (`scripts/banco_paridad.py:323-326`). Los 5.353 cumplen la vara
  (0 negativos con alguna fila que no sea RUTINA, medido).
- Encendidos (O publica, K no): O-def 1, O-sens 7; en los 7, K tiene cúmulo con 0,0 MW (4 casos, 1 píxel) o ningún
  cúmulo (3 casos); ninguno es una etiqueta `far` de K con cúmulo dentro del inner (A46 cara b: 0 casos en las 5.620).

### Afirmación 3: O-def pierde 6 protegidas (Cordón Caulle), O-sens 0 perdidas y 1 ganada, ΔE −90 (−92 a −73)

**Veredicto: CONFIRMADO en los números; CONFIRMADO EN PARTE en lo que miden. Gravedad propia: 2.**

- Números reproducidos por mi recuento: protegidas (78 ok) K publica 77, O-def 71 (6 sólo K, 0 sólo O), O-sens 78 (0
  sólo K, 1 sólo O: Cordón Caulle 2026-10-10 05:54, 1,19 MW, K sin cúmulo). Bajo 1 MW (175 ok): K 110, O-def 121 (33
  sólo K, 44 sólo O), O-sens 161 (8 sólo K, 59 sólo O). ΔE O-def −60, O-sens −90; rangos −62 a −43 y −92 a −73
  (`02_analizar.py:250-252`: supone que K no publica ninguna SIN DATO; con el rescate se comprobó que así fue en los 17
  negativos y las 2 bajo 1 MW).
- Las 6 protegidas perdidas por O-def son geometría de la caja, no umbral: O-def tiene 0 píxeles en las 6 y O-sens
  tiene 1 a 2 píxeles a 7,73 a 7,83 km del centro del TIF (el lacolito del Cordón Caulle), fuera de la cumbre de
  7 × 7 celdas (±2,6 km) y dentro del anillo con umbrales de escena, que no las alcanza
  (`verif_recuento_salida_censo.txt`, «protegidas que O-def pierde»). Producción las publica con cúmulos de 0,11 a 1,02
  MW a 0,1 a 0,5 km de su ancla.
- Dos de las «bajo 1 MW perdidas» del oráculo no son del detector de MIROVA: VOC-01 (Láscar 2026-08-26 05:48, en las
  dos cajas) y VOC-02 (Cordón Caulle 2026-10-21 05:48, sólo O-sens). Sin ellas, O-sens perdería 6 en vez de 8 y O-def
  32 en vez de 33; ΔE −92 y −61; las etiquetas no cambian.

### Afirmación 4: con el rescate del 12-oct no quedan SIN DATO y las etiquetas no cambian (ΔE −62 y −92)

**Veredicto: CONFIRMADO. Gravedad propia: 1.**

- Re-corrida con los dos runs: `tabla_por_pasada_verif_rescate.csv`, `negativos_publicados_verif_rescate.csv` y
  `resumen_verif_rescate.json` idénticos a los del auditor; texto igual salvo los 178 NUL.
- Las 20 rescatadas (`verif_detalles_salida.txt`, bloque «20 rescatadas»): 17 negativos, ninguno publicado por K ni por
  el oráculo; Chillán 05:18 (protegida, 8,44 MW) publicada por K (pc 3,46) y por las dos cajas (6,75 MW); Isluga
  05:48 (0,24) y Chillán 05:54 (0,40) ganadas por las dos cajas (K con pc 0,0 o sin cúmulo). De ahí −60 → −62 y
  −90 → −92.
- Además el control 1 pasó también en las 20 (`02_analizar_salida_verif_rescate.txt` l. 5: 0 distintas sobre 5.640),
  aunque el pre-registro §8 lo eximía: K sobre el archivo reprocesado por NASA (`…2026292…`) publica igual que
  producción sobre el original. El rescate bajó los 4 gránulos (`probe_rescate.log`: «pasadas sin procesar: 0 de 20»).

### Afirmación 5: los 4 jobs rojos del run 39713438252 son los 20 SIN DATO del 12-oct y no dañan el resto

**Veredicto: CONFIRMADO. Gravedad propia: 1.**

- API de GitHub: el run tiene 32 jobs, 4 con `failure`: `probe (10)`, `probe (11)`, `probe (17)`, `probe (18)`. Los
  logs de esos 4 chunks (`D:\vrp-trabajo\temporales\s159_oraculo\run_39713438252\s159-oraculo-censo-chunk-{10,11,17,18}\probe_*.log`)
  terminan en «pasadas sin procesar: 2 de 196 / 8 de 191 / 2 de 195 / 8 de 167» = 20, cada una con 3 intentos
  `sin_granulo_VJ202MOD` o `sin_granulo_VNP02MOD` y todas del 2026-10-12. El rojo es el `return 2 if faltan` de
  `probe_censo.py:161`, por diseño.
- No dañan el resto: los 32 `resultados_*.json` traen 5.746 ids, 0 duplicados, 0 fuera de objetivos; las líneas
  `chunk N/32: … pasadas` de los 32 logs suman 5.746; los JSON de los chunks rojos traen todas sus pasadas (el script
  escribe el JSON después de cada gránulo, `probe_censo.py:159`).

## 4. Hallazgos propios (ordenados por gravedad)

### VOC-01

- TÍTULO: El record sintético del oráculo pierde una alerta que el oráculo sí detectó en el cráter, porque promedia el
  centroide con un píxel a 17 km fuera del recuadro.
- ARCHIVO:LÍNEA: `experiments/_s159/n/07_censo_analizar.py:42-44` (centroide sin pesos de todos los alertados) y
  `:49` (`far` si la distancia supera el inner); SCRIPT:SALIDA: `verificador/verif_control2_box0_salida.txt` y
  `verificador/verif_detalles_salida.txt` (fila `1892 Lascar 2026-08-26 05:48`).
- QUÉ PASA: en Láscar 2026-08-26 05:48 (alerta de MIROVA, 0,37 MW) el código de MIROVA alertó dos píxeles: uno en el
  cráter (celda [31,33], BOX 2, 1,5 km del centro) y otro en la celda [14,20], BOX 0, a 17,27 km, fuera del 21 × 21.
  El record sintético suma los dos (1,269 MW) y pone el centroide sin pesos a 9,26 km, con inner 5 → `far` → no
  publica en ninguna caja. El censo lo cuenta como «bajo 1 MW perdida» de O-def y de O-sens cuando el detector sí
  vio el cráter. Producción publica (pc 0,172).
- CÓMO SE VE EN EL DASHBOARD: invisible (es un experimento); en el censo infla en 1 las pérdidas de las dos cajas.
- CÓMO REPRODUCIRLO: `python experiments/_s159/oraculo_censo/verificador/verif_recuento.py --art D:\vrp-trabajo\temporales\s159_oraculo\run_39713438252 --salida _x`
  y mirar `pixeles` del id 1892 en `s159-oraculo-censo-chunk-*/resultados_*.json`. Volcán Láscar, pasada 2026-08-26
  05:48 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. No cambia etiquetas (O-sens seguiría GANA EN EL CENSO; O-def PIERDE PROTEGIDAS), pero el mismo
  mecanismo puede torcer un A/B futuro en el que dos focos reales (cráter + flanco) se promedien a un punto vacío.
- Nota: el mensaje del commit `42e2b799a` del auditor nombra «centroide mezclado (Lascar 08-26)»; no leí su informe,
  así que probablemente es el mismo hallazgo y habrá que fundirlos.

### VOC-02

- TÍTULO: El filtro de cirrus del tablero apaga una publicación de O-sens porque el oráculo suma 11 píxeles a 10,3 MW
  donde MIROVA publicó 0,36 y K 1,42.
- ARCHIVO:LÍNEA: `frontend/index.html:1336-1340` (`isCirrusArtifact`: `t_max_k < 273.15` y `mirovaEqVrp > 10`);
  SCRIPT:SALIDA: `verificador/verif_detalles_salida.txt` (fila `4962 PuyehueCordonCaulle 2026-10-21 05:48`,
  `flags=[1, 1, 1, 10.312, 0]`).
- QUÉ PASA: sobre fondo frío (t_max 270,8 K) el recuadro sensible de 21 × 21 alerta 11 celdas del lacolito y su suma
  cruza los 10 MW del filtro de cirrus de display; el record de K tiene un cúmulo de 1,418 MW y no lo cruza. Es la única
  de las 5.620 × 3 evaluaciones en que `isThermalArtifact` dispara (0 en K, 0 en O-def, 1 en O-sens). El censo la cuenta
  como «bajo 1 MW perdida» de O-sens; el detector de MIROVA sí la vio (razón O/MIROVA 28×).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (K no cruza el umbral). Si se adoptara la suma de caja como magnitud, el
  operador vería desaparecer del mapa una alerta real de Cordón Caulle bajo el rótulo de artefacto.
- CÓMO REPRODUCIRLO: misma corrida que VOC-01; id 4962, caja `geo_linear_anillo_sensible`. Volcán Cordón Caulle,
  pasada 2026-10-21 05:48 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VOC-03

- TÍTULO: En 9 de las 5.620 pasadas ok el brazo K corrió sobre el gránulo NRT y producción sobre el Standard: «mismo
  gránulo» no es literal.
- ARCHIVO:LÍNEA: `experiments/_s159/n/probe_n.py:301` (busca `…MOD` y después `…MOD_NRT` por ventana);
  SCRIPT:SALIDA: `verificador/verif_detalles_salida.txt` (bloque «9 pasadas ok cuyo record K trae otro nombre de
  granulo»).
- QUÉ PASA: las 9 son las pasadas de NOAA-21 del 2026-10-20 (06:00, 06:06, 06:12); `objetivos.json` trae
  `VJ202MOD.A2026293.…` y el record K `VJ202MOD_NRT.A2026293.…`. Todas negativas, ninguna publicada por producción
  ni por K, pc None en los dos lados, así que el control 1 no lo vio ni podía verlo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: misma corrida que VOC-01, bloque «record K del mismo granulo que el objetivo: granule distinto 9».
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VOC-04

- TÍTULO: El oráculo alerta píxeles con BOX 0 (fuera del 7 × 7 y del 21 × 21) en 2 pasadas; el pre-registro §2 describe
  las cajas como 7 × 7 más 21 × 21.
- ARCHIVO:LÍNEA: `experiments/_s158_audit_r2/granulos/probe_granulos.py` (`caja_mirova`, BOX 0 fuera del 21 × 21);
  `experiments/_s159/n/probe_n.py:86-87` (`ORA.detectar(m13g, m15g, box, …)`); SCRIPT:SALIDA:
  `verificador/verif_box_pixeles_salida.txt` y `verif_control2_box0_salida.txt`.
- QUÉ PASA: de 517 píxeles alertados por O-def y 665 por O-sens en todo el censo, 2 tienen BOX 0: Lastarria 2026-08-25
  05:48 (celda [38,3], 22,81 km, 1 píxel, negativo, queda `far`) y Láscar 2026-08-26 05:48 (celda [14,20], 17,27 km,
  VOC-01). Los dos salen por la prueba `n_p1` con `n_abs = 0`. No sé si el `.m` de MIROVA excluye BOX 0 o si el port lo
  deja pasar: eso es del eje del oráculo, no del mío.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python - < verif_box_pixeles` (el bloque está en `verificador/verif_box_pixeles_salida.txt`,
  generado desde los crudos del run 39713438252).
- CONFIANZA: CONFIRMADO el hecho (2 píxeles BOX 0); SOSPECHA que sea defecto del port.
- GRAVEDAD: 2 (por VOC-01; solo, sería 1).

### VOC-05

- TÍTULO: 30 pasadas RUTINA de VIIRS 750 de la tabla de MIROVA en la ventana no tienen record nuestro a 120 s y quedan
  fuera del censo; el denominador «negativos limpios» es «con record nuestro».
- ARCHIVO:LÍNEA: `experiments/_s159/n/01_poblacion.py:104-106` (la población se arma recorriendo NUESTROS records y
  pareándolos a la referencia; sólo las alertas sin record se informan, l. 132); SCRIPT:SALIDA:
  `verificador/verif_poblacion_salida.txt`.
- QUÉ PASA: la referencia tiene 6.236 pasadas V750 nocturnas (volcán, minuto) en la ventana; 6.202 tienen record
  nuestro a 120 s y 34 no (todas RUTINA del consolidado; 10 lo tendrían a 480 s). 30 de las 34 son negativos limpios
  potenciales (noche del sensor sin alerta ni FP). Son 0,5 % del universo (30 de 5.506) y 0 alertas: no tuercen el
  censo, pero el pre-registro §1 no las declara. A 120 s ninguna fila se parea con más de un record; a 480 s, 149.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/oraculo_censo/verificador/verif_poblacion.py` (lee
  `D:\vrp-trabajo\temporales\s159_n\ref` y `…\data_main`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VOC-06

- TÍTULO: La pata de magnitud del control 1 compara 422 pares; los otros 5.198 son None-None.
- ARCHIVO:LÍNEA: `experiments/_s159/oraculo_censo/02_analizar.py:182` (`(kv is None and pvv is None)` cuenta como
  igual); SCRIPT:SALIDA: `verificador/verif_recuento_salida_censo.txt`, bloque «control 1 propio».
- QUÉ PASA: «K = producción con el mismo pc.vrp_mw a 0,001 MW en 5.620» es cierto como enunciado lógico, pero en 5.198
  pasadas ni producción ni K tienen cúmulo, así que la igualdad de magnitud se midió en 422. La de publicación sí se
  midió en 5.620, y que K no invente cúmulo donde producción no lo tiene también es información.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: misma corrida que VOC-01.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. `02_analizar_salida.txt` y `02_analizar_salida_con_rescate.txt` del objeto, tal como están commiteados en
  `f7dba3c57`, terminan en 178 bytes NUL cada uno (`git show f7dba3c57:…/02_analizar_salida.txt | tail -c 200 | xxd`);
  por eso `diff` los declara binarios y `file` dice `data`. El texto antes de los NUL es idéntico al de mi re-corrida.
  Parece corrupción al escribir (OneDrive o disco al 98 %), no del analizador, que escribe con `write_text`.
  CONFIRMADO, gravedad 1.
- S-2. VOC-04: comprobar en el `.m` de MIROVA (OSF zm62w) si la prueba p1 se aplica fuera de BOX; si no, el port
  alerta 2 píxeles que MIROVA no alertaría. SOSPECHA, gravedad 2.
- S-3. La «sensibilidad declarada» del pre-registro §3 (distancia desde `volcanoes.yaml`) mueve O-sens de 15 a 16
  negativos publicados y O-def no cambia (`02_analizar_salida.txt` l. 58 y 65); con inner 7 en Tupungatito y centro del
  TIF a 2,85 km de la coordenada, los 5 encendidos de O-sens en Tupungatito están a 4,8 a 6,7 km del centro del TIF.
  Sólo lo anoto: cuál ancla es la de MIROVA es pregunta del eje D15/D17.

## 6. VERIFICADO LIMPIO

| Qué | Comando | Vara |
|---|---|---|
| Analizador reproducible | `python experiments/_s159/oraculo_censo/02_analizar.py --art D:\vrp-trabajo\temporales\s159_oraculo\run_39713438252 --salida _verif` (y con el run del rescate, `_verif_rescate`) | tablas, CSV y JSON byte a byte iguales a los del auditor (sha256 `tabla_por_pasada` = `33270abf…`) |
| Carga de crudos | `verif_recuento.py` | 5.746 ids, 0 duplicados, 0 fuera de objetivos; estados ok 5.620, fuera 106, sin_granulo 20 (todos 2026-10-12) |
| Record sintético copiado = pre-registro §3 | `verif_recuento.py` (reimplementación propia) | 0 distintos de 11.240 |
| Pareo del gránulo | `verif_recuento.py` | hora y sensor iguales en 5.620; gránulo distinto en 9 (VOC-03) |
| Referencia fijada | `gh api repos/MendozaVolcanic/Mirova-v1/contents/monitoreo_satelital/<csv>?ref=<sha>` | blob del consolidado en `7ea275df` = `9d605c2e…` = sha1 del archivo local (8.143.085 bytes); OCR en `4ddd5481` = `13b79ea9…` = local (525.536 bytes) |
| Código del run = producción en lo que decide | compare `533398f8f...7ee78d03` | 300 archivos cambiados, ninguno de `pipeline/`, `frontend/index.html`, `volcanoes.yaml`, `banco_paridad.py` ni del oráculo |
| Rango de ΔE | recomputado con las definiciones de §4 | −62 a −43 y −92 a −73; el supuesto «K no publica SIN DATO» se cumplió en las 19 no protegidas del rescate |
| A46 cara b en K | `verif_recuento.py` | 0 records de K con etiqueta `far` y cúmulo con energía dentro del inner (en las 5.620) |
| Redondeo a 0,000 del oráculo | `verif_recuento.py` | 0 records con píxeles y VRP redondeado a 0 |
| Píxel fuera del inner con centroide dentro | `verif_recuento.py` | 0 publicaciones del oráculo con algún píxel alertado fuera del inner |
| Alertas de MIROVA sin record nuestro | `verif_poblacion.py` | 0 a 120 s (274 con record) |
| Jobs del run | API `actions/runs/39713438252/jobs` | 32 jobs, 4 `failure` = chunks 10, 11, 17, 18 |
| Rescate | `probe_rescate.log` | 4 gránulos bajados, 20 de 20 ok, run 39715348772 `success` |
| Tabla sola (c) | `verif_recuento.py` bloque (c) | 5 alertas sólo OCR desde el 13-jun (todas protegidas); O-def pierde 5, O-sens 0 y gana 1; ΔE −60 y −90 |

## 7. SIN DATO

- Si el `.m` de MIROVA excluye BOX 0 (VOC-04, S-2): no leí el código de MIROVA ni el port.
- Por qué LAADS no sirvió el Standard de NOAA-21 del 2026-10-20 el 22 de octubre (VOC-03): no miré LAADS.
- Esfuerzo de razonamiento con que corrí: no viene en la tarea; sólo puedo decir el modelo.

## 8. FUERA DE ALCANCE

- Si O-def u O-sens deben adoptarse (ola 3); si la caja de MIROVA es 7 × 7 + 21 × 21 o 21 × 19 (el propio
  `caja_mirova` lo declara SUPUESTO); el valor científico de que el oráculo encuentre el lacolito a 7,8 km; la
  calidad del OCR.

## 9. Archivos en CARPETA

`caminos.md` (sellado), `verif_recuento.py` + `verif_recuento_salida_censo.txt`, `verif_poblacion.py` +
`verif_poblacion_salida.txt`, `verif_detalles_salida.txt`, `verif_box_pixeles_salida.txt`,
`verif_control2_box0_salida.txt`, `compare_533398f8f_7ee78d03_files.txt`, `rerun_censo_stdout.txt`,
`rerun_rescate_stdout.txt`, y las salidas del analizador movidas aquí: `02_analizar_salida_verif.txt`,
`tabla_por_pasada_verif.csv`, `negativos_publicados_verif.csv`, `resumen_verif.json` y sus `_verif_rescate`.
`hallazgos.csv` con una fila por hallazgo.
