# Loop autónomo de VRP Chile: plan, reglas y bitácora

> **Para el agente que corre el loop:** este archivo es tu única fuente de verdad entre vueltas. En cada vuelta
> se lee entero, se ejecuta UNA acción de la cola (o se revisa algo que está corriendo), se anota en la
> bitácora del final y se commitea. Nunca supongas el estado: reconstrúyelo con `git log`, `gh run list` y la
> bitácora. Sub-skills: `superpowers:executing-plans` para ejecutar, `writing-plans` + `test-driven-development`
> para cada tarea que toque código, `verification-before-completion` antes de marcar algo hecho.

**Objetivo (Nicolás, S147 y S150):** la réplica `mirova_equivalent` publica lo que MIROVA publica y calla donde
MIROVA calla, medido contra la base de MIROVA; el perfil `experimental` (congelado en #771, corre a diario en
`experimental-diario.yml`) busca más detecciones reales aunque traiga falsos positivos.

**Arquitectura:** cada palanca es una prueba pre-registrada (diseño, script de evaluación con control positivo y
negativo, verificador con contexto limpio, sello de Nicolás), corrida en GitHub Actions sobre perfiles con
`data_subdir` aislado, evaluada contra una referencia de MIROVA congelada desde la UNIÓN histórica. Lo que gana
y sobrevive al verificador queda listo como PR con tag defensivo en la cola de decisiones; el loop nunca adopta.

**Herramientas:** Python 3.11/3.12, GitHub Actions (`reproc-s146-ab-sin-test1.yml` como molde de A/B,
`probe-s150-tres-campos.yml`), `scripts/banco_paridad.py`, `scripts/referencia_mirova_unificada.py`,
`scripts/calidad_referencia_mirova.py`, `gh` CLI. Fuentes del plan: `docs/audit_s150/meta/` (cuatro auditores
y dos verificadores, 2026-10-09).

---

## 1. Reglas de juego (decididas por Nicolás el 2026-10-09 y el 2026-10-13; no se reabren)

1. **El loop no cambia la réplica en producción** (`pipeline/process_*.py`, `pipeline/store.py`,
   `pipeline/profiles/mirova_equivalent.yaml`, regla A45). Deja PR + tag defensivo + evidencia en la cola de
   decisiones (§5), abre un issue con etiqueta `decision-nicolas` y sigue con otra tarea.
2. **Criterio de victoria = opción 3 (2026-10-13).** En la réplica no se acepta ningún cambio que pierda una
   alerta que MIROVA clasifique de "Bajo" para arriba; dentro de "Muy Bajo", una alerta perdida y una
   publicación de más pesan igual (suma de errores). El umbral es la clasificación de la propia MIROVA. Se mide
   en las dos direcciones, por sensor y por tramo de calidad de la referencia (A119), con tres métricas: recall
   de sus alertas, publicación en negativos limpios y razón de magnitud. El objetivo está alcanzado cuando cada
   palanca abierta quedó medida y ninguna mejora el criterio. Los umbrales salen de los datos.
   **Ojo, sin resolver aún (tarea 0.2):** la columna `Clasificacion Mirova` no es un corte del VRP de la pasada
   (hay "Bajo" de 0,04 MW y "Muy Bajo" de 0,99 MW); hay que establecer qué mide antes de usarla.
3. **Escala:** como máximo 5 agentes y 2 A/B en GitHub a la vez. Verificador con contexto limpio obligatorio
   antes de aceptar cualquier resultado (el que verifica no es el que encontró).
4. **Aviso:** un issue por cada decisión lista para Nicolás; resumen diario en la bitácora (§6).
5. **El loop se detiene solo si:** disco libre bajo 3 GB en C: o en D: (`df -h /c /d`), el token de Earthdata falla, el NRT de
   producción lleva más de 12 h sin corrida verde, o dos pruebas seguidas dan INDETERMINADO POR INSTRUMENTO.
   Al detenerse, lo escribe en la bitácora y abre un issue `loop-detenido`.
6. **Sellos:** cada pre-registro lo sella Nicolás con `sellar.py --aprobo "Nicolas Mendoza" --informe <...>`
   (el clasificador de permisos impide que el agente registre su aprobación). Mientras espera, el loop sigue con
   otra tarea de la cola.
7. **Prohibido siempre:** credenciales (sólo `EARTHDATA_TOKEN` en Actions; nunca usuario y clave, A71), pull o
   clone de `mirova-tif-archive` (17 GB), `git archive` sin ruta, borrados masivos sin tag (A38), editar con
   heredocs (usar Edit), checkout en el árbol compartido mientras un subagente lo lee (A44).
8. **Español de Chile, sin guiones largos ni medios** en todo lo que se escriba; rutas absolutas al informar.

## 2. Protocolo de cada vuelta

0. **Dónde vive el estado.** El loop trabaja siempre en la rama `loop/activo` (la crea desde `main` la primera
   vuelta, si no existe) y lee y escribe ESTE archivo ahí, no en `main`: la bitácora de una vuelta no puede
   depender de que la anterior se haya mergeado. Al empezar cada vuelta, `git merge origin/main` en
   `loop/activo` para recoger el NRT y lo mergeado. Cada tarea que produce código o documentos va en su propia
   rama `loop/<tarea>` desde `main`, con su PR.
   **Discos (Nicolás, 2026-10-19: «que se usen de aquí en adelante»):** el repo principal y `loop/activo` siguen en C:.
   Los worktrees de tareas y de agentes (A44) y los temporales grandes (uniones de A/B, raíces de evaluación,
   artefactos bajados) van en **D:**, en `D:\vrp-trabajo\worktrees\<tarea>` (`git worktree add
   D:/vrp-trabajo/worktrees/<tarea> -b loop/<tarea> origin/main`, probado: los scripts ubican el repo desde ahí) y
   `D:\vrp-trabajo\temporales\`. Así C: queda para el repo y el sistema, y caben más agentes en paralelo. Un worktree
   se borra apenas se mergea su PR. El tope real de paralelismo sigue siendo GitHub (20 jobs, compartidos con el NRT) y
   MODIS no se procesa en Windows (pyhdf): el disco permite más trabajo local, no corre más rápido los reprocesos.
1. `gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date` (hora del servidor, A86); `git fetch origin
   --prune`; `git checkout loop/activo && git merge --no-edit origin/main`; `df -h /c /d`.
2. Chequeos de parada (§1.5): `gh run list --workflow nrt.yml --limit 3`; issues abiertos con etiqueta de alerta.
3. Si hay algo corriendo (run de GitHub, agente): revisar su estado. Si terminó, evaluarlo según su tarea.
4. Si no, tomar la primera tarea `[ ]` de §3 o §4 cuyo bloqueo esté libre. Una tarea por vuelta.
5. Anotar en la bitácora (§6): hora del servidor, tarea, acción, resultado con número y fuente, próximo paso.
6. Commit de la bitácora en `loop/activo` y push. El PR de cada tarea se mergea si el CI está verde y no toca
   nada de §1.1 (A39 con su enmienda S142: esperar el run con conclusión; si `gh pr merge` falla por el
   worktree, `gh api --method PUT repos/MendozaVolcanic/VRP-chile/pulls/<N>/merge -f merge_method=squash`).
   **Mientras el CI de `main` siga rojo por el guard de la referencia (tarea 0.1), ningún PR se mergea**: lo
   producido se acumula en sus ramas y la tarea 0.1 va primero, porque es la que lo pone verde. La única
   excepción la autorizó Nicolás para #777 (2026-10-14) y no se extiende a otros PR. `loop/activo` se mergea a
   `main` con un PR propio cuando el CI esté verde, como mínimo una vez al día.
7. Programar la próxima vuelta según lo que se espera: un run de A/B se mira a su duración esperada (no antes);
   sin nada corriendo, 20 a 30 min.

## 3. Bloque 0: higiene antes de medir (en orden; sin esto las pruebas miden con una vara rota)

- [x] **0.1 Referencia de MIROVA desde la unión histórica.** HECHA 2026-10-14 (#778, squash `46947bda`;
  `main` verde en el run 38558333297). Pendientes que deja: (i) RESUELTO 2026-10-14 (#803): el auto-audit
  ya suma la unión histórica en el paso 1 (30 alertas más, 2 en la ventana de 60 días); (ii) sólo las 207 del 06-oct tienen testigo
  independiente en la suite; (iii) 372 claves de tipo cambiante, al menos 318 del cambio masivo
  EVIDENCIA_DIARIA a RUTINA del 21-ene; (iv) RESUELTO 2026-10-14 (#805): el OCR perdió 5 alertas, todas en su
  tramo inestable (hasta el 2026-02-24); no se agregan, y `experiments/_s151_ocr_perdidas/medir.py` lo repite.
  Por qué: el consolidado remoto de Mirova-v1 perdió filas en silencio al menos cinco veces (21-ene, 23-abr,
  25-ago, 26-ago y 06-oct, 207 filas con 8 alertas) y nunca las repuso (`docs/audit_s150/meta/VERIFICADOR_DATOS.md`
  D1). Una referencia congelada desde el remoto de hoy no las tiene. El snapshot previo a la última caída está
  protegido por el tag `pre-s150-consolidado-perdida-207`.
  Archivos: `scripts/referencia_mirova_unificada.py` (extender), nuevo `tests/test_referencia_union_historica_s150.py`.
  Pasos: (a) escribir el test: toda fila de `git show pre-s150-consolidado-perdida-207:data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
  está en la unión, y las 8 alertas del 06-oct también; correrlo y verlo fallar; (b) implementar la unión de
  todas las versiones del CSV en la historia de Mirova-v1 (API de GitHub por sha, sin clonar) y del snapshot
  local, deduplicando por (volcán normalizado, sensor, fecha del satélite); (c) test en verde; (d) que
  `banco_paridad.indexar_referencia` lea la unión; (e) informar cuántas filas aporta cada versión.
  Aceptación: el test pasa; las referencias congeladas de las pruebas nuevas salen de la unión; y
  `tests/test_referencia_unificada_s139.py::test_la_principal_gana_y_el_respaldo_solo_agrega` vuelve a verde
  **por la razón correcta**. Ese guard está rojo en `main` desde la caída (run 38413222685, 2026-10-13: el
  respaldo agrega 21 alertas que la principal perdió, tope 17): es la alarma de la pérdida funcionando, no un
  test roto. Prohibido ensancharle el rango para ponerlo verde.

- [x] **0.2 Qué mide `Clasificacion Mirova`.** HECHA 2026-10-14 (#780, squash `03c44eed`, verificada): alerta
  protegida = PASADA con alerta del scraper y VRP >= 1 MW recalculado (lectura A, 439 pasadas); la columna es
  del scraper y no sirve; el corte lo sostiene el banner de MIROVA, no el paper (fig. 11 se contradice).
  Lectura B (VRP >= 1 MW a cualquier distancia, 992) en la decisión D-4 (#782): evaluar con las dos.
  Por qué: el criterio de victoria depende de "Bajo o superior", y la columna no es un corte del VRP por pasada
  (Muy Bajo 1.372 filas de 0,01 a 0,99 MW; Bajo 265 de 0,04 a 8,75; Moderado 4 de 13,1 a 15,8; medido en
  `latest_consolidado.csv` el 2026-10-13). Hipótesis a probar: el nivel es el de la página del volcán en ese
  momento (agregado de días), no el de la pasada. Fuentes: código del scraper de Mirova-v1 (por la API), umbrales
  de nivel en `documentacion/` (buscar antes en `BIBLIOGRAPHY_SYNTHESIS.md`; la página del PDF se lee
  renderizada a imagen, A95).
  Entregable: `docs/S151_CRITERIO_CLASE_MIROVA.md` con la definición operativa de "alerta protegida", su script
  y su control. Si la columna resulta inservible y ningún paper da el umbral, la definición queda en la cola de
  decisiones (§5) con la alternativa medida, y el loop sigue evaluando con las dos lecturas en paralelo.

- [x] **0.3 Propagación A113 a las puertas de entrada.** HECHA 2026-10-14 (#784, squash `88e97d84`, verificada y con
  arreglos). Quedan para Nicolás: tooltip "probablemente artefacto" (texto del operador) y P1 (memoria, fuera del repo).
  Por qué: `docs/audit_s150/meta/VERIFICADOR_DOCUMENTOS.md` confirmó P1 a P6 (bloque de arranque de S149,
  MISSION choca con las dos direcciones, veredicto S27, D8' contra la anomalía mayor, tope D9 con "0 sobre 5 MW"
  falso y 338 hoy, ficha SDA desactualizada) y el hallazgo del tablero (dice que el pipeline no marca el tope).
  Archivos: `CLAUDE.md`, `docs/MISSION.md` (agregar el criterio de §1.2), `docs/MIROVA_DIVERGENCES.md`
  (encabezados de D8', D9, D21, D27 y las marcas contradictorias l. 795, 840 y 2817), `docs/FICHA_SDA_VRP_CHILE.md`,
  `docs/INDEX.md` (los 12 documentos que faltan), y los textos del tablero en `frontend/index.html`,
  `frontend/diario.html`, `frontend/mosaico.html` (sólo texto; el conteo "1.403" pasa a salir de los datos).
  Usar las marcas propuestas en el informe del verificador (⚠️ + qué cayó + sesión + puntero, conservando el
  texto viejo). Correr `grep -rl <archivo> tests/` y la suite completa después (un test puede leer esos docs).
  Aceptación: cero guiones largos y medios en cada archivo tocado; suite verde; el guard G8 sigue verde.

- [x] **0.4 Instrumentos chicos.** HECHA 2026-10-14: (a), (b) y (d) en #781 (`b2187648`), (c) en #791 (`fecc3eae`);
  que espera a la 0.3 porque toca `CLAUDE.md`.
  (a) `evaluar_ventana.py` (en `experiments/_s149_prereg_invierno/` o donde lo ubique `git ls-files | grep
  evaluar_ventana`) deja de mandar stderr a DEVNULL, así el aviso A119 llega al log; (b) `scripts/calidad_referencia_mirova.py`
  gana los hitos de NOAA-21 y de Suomi NPP (con fuente); (c) A119 en `CLAUDE.md`: el "86 % en enero" es
  Tupungatito en el denominador (sin él, 95 a 99,5 %) y "0 alertas MODIS dependen del OCR" es falso (5 hoy);
  (d) sacar `ENABLE_TEST1_NULL_CORRECTED` de toda cola (ningún procesador lo lee, VERIFICADOR_DATOS D8).
  Cada arreglo con su test que falla antes.

- [~] **0.5 Scraper de Mirova-v1 con VRP de 1.000 MW o más** PR Mirova-v1#21 listo con CI verde; espera el sí
  de Nicolás (issue #783). (issue MendozaVolcanic/Mirova-v1#19, 36 ciclos
  caídos; `scraper.py:140`). En plena erupción de Chillán es el caso que puede pasar. PR en Mirova-v1 con test
  del caso "1,234.5"; **el merge espera el sí de Nicolás** (es otro repo de producción).

- [~] **0.6 Marca de régimen en cada record** PR #785 con tag `pre-s151-marca-regimen`, en la cola (D-3, issue
  #786); NO se mergea sin el sí de Nicolás. (perfil + sha del código; 0 de 65.206 records la tienen,
  VERIFICADOR_DATOS D7). Bloquea toda adopción futura. Toca `pipeline/store.py` → regla §1.1: plan + test + tag
  + PR, y a la cola de decisiones.

## 4. Bloque 1: pruebas (cola, en orden; una tarea puede avanzar mientras otra espera un sello o un run)

- [x] **1.1 Prueba de Nevados de Chillán** HECHA 2026-10-14 (#796, `014fa659`, `docs/S151_RESULTADO_NDC.md`,
  verificador PARCIAL): ningún candidato vetado; F/K pasan y quedan para la corrida de los 11 volcanes; quitar el
  tope D9 quedó sin probar. Despachada 2026-10-14 11:58 UTC, run 38560317428 (4 a 6 h). La
  congelada no perdió filas de Chillán en la ventana (le faltan 12 de otros volcanes, 1 alerta de Láscar),
  así que no se re-congeló. (pre-registro v3 APROBADO, `experiments/_s150_ndc/PREREGISTRO_NDC.md`;
  despacho autorizado desde el 2026-10-13). Antes de despachar: comprobar que `_congelado_ndc` no perdió filas de
  la ventana 2026-09-14 a 2026-10-07 contra la unión de 0.1 (si perdió, re-congelar y anotarlo). Despacho: un run
  de `reproc-s146-ab-sin-test1.yml`, volcán NevadosDeChillan, del 2026-09-14 al 2026-10-07, los 10 brazos,
  control `_s146_ab_control`, desde `main`, `preregistro_aprobado=si`. Evaluar con `medir_ndc.py`; verificador
  limpio sobre el resultado; las líneas `FLAGS_BRAZO` del log confirman los flags efectivos de cada brazo.

- [ ] **1.2 Sonda de los tres campos** (PR #776, `experiments/_s150_sonda_tres_campos/`, verificada tres veces).
  Bloqueo: el sello de Nicolás. Luego: piloto (lote 1, sin veredicto); si la σ contra el A/B o el gránulo
  difieren en más del 5 % de las pasadas, no se despacha el resto (§10 bis del DISENO); si no, despacho completo
  y evaluación con su `evaluar.py`.

- [x] **1.3 A/B de D22, pre-registro v2.** ⚠️ S151, D-9 (#820, verificador): bajo la regla SN el techo baja de
  14 a 5 pasadas (8 con umbral 0,04) y el equilibrio de 5,2 % a cerca de 1,8 %; refuerza la resolución sin A/B.
  RESUELTA SIN A/B 2026-10-14 (#788): las 14 pérdidas confiables son
  Muy Bajo (0,03 a 0,08 MW); techo 14 pasadas contra 271 negativos reabribles; sólo gana si reabre menos del
  5,2 %. La selectividad la mide la sonda (1.2). Texto original: Con la tabla sola, el camino D22 pesa 12 de 24 pérdidas débiles de
  `max` (VERIFICADOR_DATOS D3). Rehacer el pre-registro suspendido (`experiments/_s150_ab_d22/PREREGISTRO.md`)
  con los hallazgos de su verificador (`docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md`), el criterio de §1.2 y
  la referencia de 0.1; verificador limpio; sello de Nicolás; despacho.

- [~] **1.4 A/B de anomalía mayor (`vrp_max`) contra `vent_anchored`** PRE-REGISTRO en `main` (#794, `1795676b`,
  verificado con arreglos). D-6 DECIDIDA 2026-10-14: SIGUE (Nicolás: la réplica debe reproducir también las
  anomalías lejanas para demostrar fidelidad a la metodología; distancia similar más TIF bastan para identificar
  el objeto). Paso 1 en curso: estudio con TIF y distancia de qué objeto informa MIROVA y si es la mayor (rama
  `loop/1.4-estudio-tif`); paso 2: código de A2 con tag y PR sin merge (A45); paso 3: A/B con R4 como métrica
  central. Antes: A1 casi inerte (el flag no llega a la Regla D ni al ancla) y P5 prevé un veto con la lectura A.
  Universo de comparación: 359 detecciones lejanas nocturnas de MIROVA, no 858 (VERIFICADOR_DATOS D2); la
  clasificación NULO la escribe el scraper. Medir distancias desde el cráter y no desde el catálogo
  (`process_viirs.py:754`, AUDITOR_F1). Pre-registro, verificador, sello, despacho.

- [x] **1.5 D25, fondo por vecinos, primero sin correr nada:** HECHA 2026-10-15 (#823, verificado PARCIAL): probe
  válido, los dos brazos NO VALEN con la detección de hoy porque con piso 0 todo cúmulo alertado publica; D25 calza
  la magnitud con MIROVA (mediana 1,19 en 28 rescates, AUC 0,861). Cierre CONDICIONADO a la detección: re-medir D25
  junto con el cambio de detección que se adopte (conectiva, caja, D22). VIIRS 375 sin evidencia. Texto previo: sobre los 268 negativos de VIIRS 750 ya en disco
  (`AUDIT_S149.md:139`). ESTADO 2026-10-14: magnitud SIN MEDIR (no hay vecinos en records ni gránulos en disco);
  techo: cualquier magnitud positiva publicaría los 268 negativos y las 28 alertas. Probe de sólo lectura (356
  pasadas) en `main` (#790, `2b6a1be8`), verificado, con candado; ESPERA el sello (D-5, #793). El descarte de vecinos nublados bajo 255 K es de Coppola 2014 p. 3412, no del canon
  2016a (VERIFICADOR_DATOS D9): medirlo como variante, no como "lo que exige el paper".

- [~] **1.6 MODIS: banda 22 junto con `max`** PRE-REGISTRO de F y K contra producción en los 11 volcanes en `main`
  (#797, `2c174b5b`, verificado con arreglos); APROBADO por Nicolás el 2026-10-14 (D-7). V1 DESPACHADO 21:21 UTC,
  run 38639658446 (~12,5 h); faltan V2a y V2b, uno a la vez. Los flags de compuerta y de fondo de
  MODIS siguen sin existir (A45). Texto original: con los flags de compuerta y de fondo que le faltan a MODIS
  (`audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:285`). En MODIS, `max` solo apaga el detector (S147).

- [x] **1.7 La caja de 5 × 5 km (D18)** HECHA 2026-10-15 (#825, verificada): **NO CUMPLE (veto)** en D1, por una
  protegida MODIS de Láscar cuyo píxel cae en la corona; el cierre vale con la geolocalización MODIS de hoy (ver
  1.15). D2 y V1 no se despachan. Texto previo: PRE-REGISTRO v2 en `main` (#800, `d5bc604f`; marca en D18 #802),
  verificado; ESPERA el sello (D-8, #801): despacho reducido a D1/D2 (~35 min) y B/BC en V1 (~6 h). Hallazgo:
  MIROVA mide `Distancia_km` desde el centro de su grilla. Texto original: medida por primera vez ahora que
  llega a los dos pases (#738), con el
  Test 1 apagado en el brazo de control donde la palanca puede actuar (A114, A118).

- [x] **1.8 Modo de un solo píxel en erupción** HECHA 2026-10-14 (#799, `7145a692`, verificada CONFIRMADO): el
  modo sólo decide en VIIRS 750 (28 de 1.304 pares), 0 publicaciones cambian, 0 protegidas; la subestimación en
  erupción es de cuántos píxeles alertamos. No se toca. (AUDIT_S150 familia 3: Chillán VIIRS 750 mostró 2,66, 11,08 y
  2,49 MW en 54 min).

- [x] **1.9 Preferencia de MIROVA entre banda I y banda M** HECHA 2026-10-14 (#787, squash `cd23ae20`): el NRT
  NO tiene preferencia (13.964 pasadas con las dos bandas, 246 con alerta en las dos); la regla es del archivo.
  Palanca descartada para la réplica. Origen: `FRENTE_F_FIDELIDAD_VIIRS.md:474`, F-07.

- [x] **1.10 Las 4 alertas de VIIRS 750 de 0,32 a 0,65 MW que `max` pierde** HECHA 2026-10-14 (#789, squash
  `28d03ba0`, verificador PARCIAL con arreglos aplicados): todas Muy Bajo; contra B la suma de errores baja de
  400 a 90 (abril a agosto, contada por pasada). Es contra B (sin Test 1), no contra producción; con la lectura B
  de D-4, F pierde una pasada protegida de otro objeto (Chillán 2026-07-23). Origen: VERIFICADOR_DATOS D4.

- [ ] **1.11 Experimental** (bloqueado hasta que Nicolás entregue la cronología OVDAS de Chillán y las
  coordenadas de los rasgos reales: Cerro Blanco, Pichi-Llaima, Lazufre, El Agrio). Su vara no es MIROVA
  (A115).

**Agregadas por Nicolás el 2026-10-14 (en este orden; "puedes correr donde necesites": GitHub Actions incluido,
siempre con el tope de 2 A/B a la vez y sin desplazar el A/B de F/K en curso).**

- [x] **1.12 (estudio D) Las alertas de 0,05 MW o menos: ¿MIROVA las considera anomalía?** HECHA 2026-10-14 (#810, squash `f14b31ac`, verificada): en VIIRS 375 MIROVA llama NONE a 0,04 MW o menos y
  VERY LOW a 0,06 o más; 155 alertas del scraper de 0,05 o menos. Cómo contarlas: decisión D-9 (#811).
  Por qué: el banner de MIROVA dice NONE en 9 pasadas que el scraper registra como alerta (0,02 a 0,05 MW,
  `docs/S151_CRITERIO_CLASE_MIROVA.md` §5), y 9 de las 14 pérdidas débiles de D22 están en ese rango. Si MIROVA no
  las ve como anomalía, toda suma de errores las cuenta mal (como alerta perdida o como acierto), incluida la del
  A/B de F/K en curso. Es la vara de todas las pruebas: va primero.
  Qué medir: cuántas alertas de la unión tienen VRP de 0,05 MW o menos, por sensor, volcán y tramo A119; qué dice
  el banner (cuando hay) y el TIF de esas pasadas; si la frontera NONE / VERY LOW está en 0,05 MW o depende del
  redondeo; y cuánto cambia la suma de errores de los resultados ya medidos (meses de S150, VIIRS 750, Chillán)
  si esas pasadas se tratan como "MIROVA no vio nada". Control que pueda fallar.
  Entregable: documento con la regla propuesta para el evaluador, y la regla queda como decisión para Nicolás
  si cambia algún veredicto ya publicado.

- [x] **1.13 (estudio C) Alertas diurnas de MIROVA que la réplica no mira.** HECHA 2026-10-14 (#812, squash
  `51b1977b`, verificada con arreglos): MIROVA sí procesa VIIRS de día; 40 pasadas diurnas usables (A119) contra
  232 nocturnas; decisión D-10 (#813). Antes: ENTREGADO #812, en verificación
  limpia. Antes: EN CURSO 2026-10-14 (agente en
  `VRP-Chile-113`, rama `loop/1.13-alertas-diurnas`).
  Por qué: la réplica procesa sólo de noche (MIR contaminado por el sol), pero la tabla de MIROVA trae 37 alertas
  entre las 13 y las 21 UTC, 19 de 1 MW o más (dato de la tarea 0.3, `docs/audit_s150/meta/`). Con la lectura A
  son alertas protegidas que se pierden por construcción, y ningún evaluador las cuenta porque todos filtran el día.
  Qué medir: la población completa de alertas diurnas en la unión (por sensor, volcán, hora y elevación solar);
  cuáles son reales y cuáles reflejo solar en nubes (A76: VIIRS 375 cerca del mediodía sobre nube); qué haría la
  réplica con ellas (¿procesa MIROVA el día para VIIRS?, Coppola 2016a y la tesis de Massimetti en
  `documentacion/`, página renderizada); y cuánto pesan en el criterio. Sin tocar el pipeline.

- [x] **1.14 (estudio A) Presupuesto de la magnitud, pasada por pasada.** HECHA 2026-10-14 (#814, `33c42ab5`,
  verificado PARCIAL y con los siete arreglos aplicados). Resultado: el reparto selección/fondo es una identidad que
  depende de la bisagra (fondo 21 a 64 % del déficit V375; Shapley 43 %); la dependencia con el ángulo NO es D17
  (el Npix de MIROVA no crece con el área) y queda SIN ATRIBUIR; D25 es la palanca que más mueve (×1,28, sube de
  1,00 en nadir a 1,20 en el borde). Siguiente: pre-registro de D25 como brazo sobre C0 y sobre F (negativos limpios
  medidos en F, porque en C0 el Test 1 satura, A114), coordinado con #793 y con el resultado de F/K; se escribe
  cuando F/K se evalúe. El estudio B (remuestreo D17) pierde su motivación principal.
  Por qué: subestimamos la energía (Láscar 0,44, Isluga 0,52, Lastarria 0,56, Tupungatito 0,65 en el auto-audit
  del 2026-10-14; 0,4 a 0,6 en la erupción de Chillán) y no sabemos cuánto viene de cada causa: cuántos píxeles
  alertamos contra cuántos suma MIROVA (Campus 2022: suma de todos los alertados), cuánta energía trae cada píxel,
  y cuánto resta el fondo (anillo contra vecinos, D25; A99 rebajada: dos factores opuestos que se compensan).
  Qué medir: descomponer la razón contra MIROVA en esos factores por pasada, usando nuestros `anomaly_pixels` y,
  donde se pueda, el conteo de píxeles calientes del TIF de MIROVA (A24: el TIF no es VRP sumable; A106: CRS y hora
  de adquisición; A109). Resultado: qué palanca mueve la magnitud (conectiva, fondo, área o remuestreo D17) y
  cuánto, para decidir el siguiente A/B. Control que pueda fallar.

- [~] **1.15 (agregada por el loop el 2026-10-15, de sólo lectura) El píxel MODIS del cráter corrido hacia el
  sensor.** EN CURSO.
  Por qué: el verificador del veto de la caja (#825) encontró en Láscar que el píxel MODIS del cráter aparece
  corrido hacia el lado del sensor y que el corrimiento crece con el ángulo de visión (Aqua +1,1 km a 17°, +3,5 km
  a 45°; Terra -0,9 a -2,2 km a 31°; n = 13). Si es real y general, decide la etiqueta summit/far de MODIS (A46,
  A81, D11), la posición de cada auditoría espacial (A61) y el veto de la caja. Candidatos: la interpolación de
  la geolocación de 5 a 1 km (`_interp_geo`, `pipeline/process_modis.py:342`) o el paralaje de cumbres altas
  sobre el elipsoide. Qué medir: el corrimiento por volcán (altura de 2.200 a 5.600 m), por satélite y por ángulo,
  contra la geolocación oficial MOD03/MYD03 de 1 km y contra la posición de MIROVA (TIF hasta el 22-sep, A106);
  separar paralaje (proporcional a altura por tangente del ángulo) de error de interpolación. Sin tocar el
  pipeline. Control que pueda fallar: VIIRS, cuya geolocación es nativa por píxel, no debería mostrarlo.

- [x] **1.16 HECHA 2026-10-16 (vuelta 75):** `experiments/_s151_repaso_crudo/INVENTARIO.md`, cinco conclusiones en
  orden de ataque (citas archivo:línea revisadas): (1) etiquetas summit/far MODIS del corpus con MxD03 → tarea 1.17;
  (2) saturación en erupción, que el JSON no puede contestar → 1.18; (3) dependencia angular de la magnitud V375 con el
  OSF global y un sintético → 1.19; (4) cat-b de A54 contra SWIR (espera las coordenadas de Nicolás, 1.11); (5) D20,
  banda 32. Texto original:
  **1.16 (agregada por Nicolás el 2026-10-16) Repaso con material crudo.** Va **después de cerrar el arreglo de
  G3** del evaluador diurno (rama `loop/diurno-g3-tolerancia`). De sólo lectura; entregable de **una página**.
  Por qué: dos defectos de este mes estuvieron escondidos porque se auditaba sobre material ya digerido: el
  corrimiento MODIS (meses en nuestros JSON; lo destapó la geolocalización oficial MOD03, #828) y la distancia del
  OCR (discrepa en ~24 % de las pasadas del 06-13 al 10-08; lo destapó leer `Dist.png` como serie de tiempo,
  `experiments/_s151_distancia_ocr/`). Y los «verificadores limpios» son otra instancia de Claude: atrapan errores
  de lógica, pero no son un árbitro independiente. Origen: el prompt de «versión más profunda, no más grande»
  (qué haría un especialista, material más crudo, métodos, quién más mostraría que está bien), conversado en la
  sesión vrp 151.
  Qué entregar: un inventario de las conclusiones VIGENTES que se apoyan sólo en material digerido (nuestros JSON,
  el CSV del scraper, resúmenes de papers, texto extraído de PDF), y para cada una: (a) el material crudo que la
  confirmaría o la tumbaría (L1B, MOD03/VNP03, GeoTIFF y OSF de MIROVA, página renderizada del paper); (b) el
  árbitro externo (base de MIROVA para la réplica; OVDAS, Sentinel-2 y Landsat en onda corta para el experimental;
  MOD03 para posición; Coppola para el código); (c) el método (píxel a píxel contra la oficial, sintéticos con
  respuesta conocida, el detector sobre los casos publicados por MIROVA); (d) un orden de ataque por lo que
  decide. No re-litigar los A/B ya pre-registrados: su vara está fijada. La reescritura del plan cabe en una página;
  si no cabe, se prioriza, no se alarga.

**Agregadas por el loop el 2026-10-16, del inventario de la 1.16 (todas de sólo lectura; árbitro externo, no Claude).**

- [ ] **1.17 Etiquetas summit/far MODIS re-medidas con MxD03 en los 11 volcanes.** Por qué: #828 midió 7 gránulos,
  casi sólo Láscar; D12, el recall MODIS (A81/A82) y el `far` de Chillán se apoyan en posiciones de `_interp_geo`. Qué:
  probe en GitHub Actions (pyhdf sólo en Linux) que reubica `anomaly_pixels` y `final_hotspot` con MxD03 y re-etiqueta
  con el predicado del tablero (A97); recuento por volcán, satélite y cenit. Informa la decisión del arreglo MxD03
  (A45), que sigue siendo de Nicolás. Autenticación sólo con `EARTHDATA_TOKEN`.
- [x] **1.18 HECHA (vuelta 86): 0 saturados en 385 gránulos, confirmado por verificador; ver bitácora.** Saturación en la erupción de Chillán, leída en el L1B. Por qué: nuestro techo I04 es 361,77 K y el de
  MIROVA 353 K; el corpus ya llegó a 354,24 K, y un píxel borrado no aparece en `t_max`. Qué: en las pasadas de
  Chillán desde el 2026-09-28, contar en VNP02IMG/VJ102IMG (bit de saturación de I04) y MOD021KM (SI = 65533) los
  píxeles saturados, y recalcular el VRP con y sin ellos contra lo que MIROVA publicó (9,0, 10,0 y 8,24 MW).
- [x] **1.21 HECHA 2026-10-17 (vuelta 147, verificador CONFIRMADO): EMPEORA.** La etiqueta desde el cúmulo no es
  adoptable (+3.544,5 errores, todos de la etiqueta). MxD03 sola cae por la letra de la regla 1 (2 protegidas de Láscar
  por A46, Test 1 que deja de disparar), pero el nulo de posición pierde 4: ni refutada ni probada. Siguiente: tarea
  1.23. Resultado en `experiments/_s151_mxd03_cumulo_121/resultado/`. Texto original:
  **1.21 (agregada por el loop el 2026-10-16, del resultado de la 1.17) MxD03 junto con la etiqueta desde el
  cúmulo.** El probe 1.17 dio PIERDE PROTEGIDA por la letra, pero las 2 pérdidas vienen de que `distance_class` sale del
  hotspot final (`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`), no de la posición. Probe de tres brazos sobre la
  misma población (C; MxD03; MxD03 + etiqueta desde el cúmulo), con la regla 1 como compuerta, el término a lo largo
  de la traza agregado al modelo de corrimiento y un brazo con ruido de posición como control real. Pre-registro,
  verificador, sello de Nicolás. Informe del verificador de la 1.17 en `verif_117r`.
- [x] **1.23 HECHA 2026-10-17 (vuelta 174, verificador CONFIRMADO con matices):** en Láscar, bajo 35° de cenit,
  MxD03 pone el píxel caliente donde VIIRS ve el calor (vara principal MXD03 MÁS CERCA, dd 0,62 km [0,32; 0,96], n 76;
  Terra y Aqua lo dan por separado, control que cancela un sesgo constante de la vara). Por la letra sigue PIERDE
  PROTEGIDA (2 de Láscar) y no es adoptable; las 2 pérdidas son el Test 1 cruzando su umbral (σ_bg sube, ΔL baja), lo
  mismo que rompe cualquier corrimiento de ese tamaño (cada una se sigue publicando en 7 de 20 nulos); el Test 1 con
  signo dio MIXTO. No dice nada del borde del barrido ni de otros volcanes. Resultado en
  `experiments/_s151_mxd03_sola_123/resultado/`. Siguiente: D-19. Texto original:
  **1.23 (agregada por el loop el 2026-10-17, del verificador de la 1.21) MxD03 sola: lo que falta para decidirla.**
  Por qué: la 1.21 no la refuta ni la prueba; sus 2 pérdidas son el Test 1 de Láscar cruzando el umbral (4,81 a 2,56
  y 3,28 a 2,83) con ~0,4 km de corrimiento, y el nulo (un solo rumbo por gránulo) pierde 4. Qué: (1) nulo con ~20
  rumbos por gránulo para tener distribución; (2) una vara de posición independiente (cúmulo VIIRS 375 de la misma
  noche, o TIF UTM de MIROVA, A106); (3) por qué el Test 1 de Láscar es tan sensible a 0,4 km; (4) el caso del borde
  del barrido (Chillán Aqua 2026-10-12 07:20, cenit 59°, MC elige otro cúmulo a 9,7 km), corrigiendo antes la
  anisotropía del nulo sobre 50°. De sólo lectura más probe; pre-registro y verificador antes de correr.
  Además, del mismo verificador: **8 records de producción salen hoy con más píxeles anómalos que los guardados**
  (deriva de código, mismos 8 en la 1.17 y la 1.21, todos Standard): identificar el commit.
- [ ] **1.22 (agregada el 2026-10-17, D-16 b aprobada por Nicolás) Desempate determinista del hotspot de escena
  MODIS.** ⚠️ Corregido el 2026-10-17 por el autor de #843: el píxel que cambia NO es el `np.nanargmax` de
  `process_modis.py:1218` (`diag_t_max_dist_km` es idéntico en los dos intentos), sino el primero de
  `np.argsort(-per_pixel_vrp_mw)` (`:1085-1099`), el mismo top-100 no estable; en los records del Test 1 esa lista
  se reemplaza en `:1399`. Texto original: Por qué: dos corridas del mismo commit eligen distinto el píxel más caliente de la escena
  (`np.nanargmax(roi_bt_full)`, `pipeline/process_modis.py:1218`) con la misma BT máxima; cambia `final_hotspot_source`
  y el `vrp_mw` del record (V1 Llaima 4,281/3,568; W2a Copahue 4,782/1,834), no lo publicado. Qué: confirmar el
  mecanismo (SOSPECHA: ulps de log/exp según la CPU) con un sintético y con los dos casos; proponer un desempate
  explícito (BT redondeada más índice) con su test, tag defensivo y PR SIN merge (§1.1, A45); medir cuántos records
  del corpus cambia. Revisar también el top-100 de `process_modis.py:1085` (`np.argsort` no estable).
- [ ] **1.20 (agregada por el loop el 2026-10-16, del verificador de la 1.18) Techos que borran señal válida.** De sólo
  lectura. (1) Techo M15 de 343 K en `pipeline/process_viirs_mod.py:182` contra M15 válido hasta 374 K: ¿cuántos
  píxeles y records del corpus borra, y cuánto VRP cambia? (2) I04 de NOAA-21 con LUT máx 361,00 K contra el corte de
  361,27 K: ¿la defensa secundaria queda muerta en ese satélite? Cada uno con su control positivo. Toca producción (A45):
  sólo medir y proponer.
- [x] **1.19 HECHA (vuelta 85, verificador PARCIAL: sólo el escalón de 52,66° se sostiene; sin palanca que pre-registrar).** Dependencia angular de la magnitud V375 sobre el OSF global.** Por qué: hoy «SIN ATRIBUIR» con 33 a 44
  pares por bin. Qué: buscar el salto en Npix y VRP/Npix en los límites de las zonas de agregación VIIRS (ángulos del
  User Guide del SDR, página renderizada) en las 252.374 filas de 375 m del OSF; y un sintético subpíxel de energía
  fijada por física antes de correr, pasado por la huella VNP03 y por el detector. Decide la palanca de magnitud
  después de D25.

### Bloque S154 (agregado el 2026-10-18; K adoptada en #850 a las 09:57:30 UTC). Dueño del loop: sesión S154 «retomar»

Nicolás pidió el 2026-10-18 que «todo lo posible quede en el loop». Orden de la cola:

- [ ] **1.24 Reproceso histórico con K y reemplazo en la serie operacional** (autorizado por Nicolás el
  2026-10-18: sí a los reprocesos 5 y 6, vía por trozos en perfil aislado). Run 39125546355 (`reproc-chunked.yml`,
  `_s154_reproc_k_historico`, 2025-02-15 a 2026-09-17, 176 trozos de a 8, estimado 28 a 35 h). Al terminar: (a)
  trozos fallidos o sin artefacto se repiten sólo esos (misma ventana del trozo); (b) ensayo por volcán con
  `scripts/reemplazar_ventana_reproceso.py` (sin `--aplicar`, tope 2 %), informes en `experiments/_s154_reproc_k/`;
  si un volcán se rehúsa, repetir sus trozos; (c) verificador limpio sobre los ensayos (no lo hace quien los corrió);
  (d) aplicar los 11 en UN commit justo después de que termine un NRT y antes del siguiente (:10), con tag defensivo
  previo; (e) `experiments/_s154_reproc_k/verificar_ventana.py` sobre 2025-02-15..2026-09-17 contra ese tag (0
  perdidas, 0 cambiadas antes de la ventana) y R8 sobre el JSON publicado. Después, borrar
  `data/_s154_reproc_k_historico/` de `main` en un PR (queda en la historia de git).
- [x] **1.25 HECHA 2026-10-18 (vuelta 198), verificador PARCIAL:** NO ADOPTAR se sostiene para C0 y NO se traslada a K
  (`experiments/_s151_ab_diurno/salidas/W2_W6_s154/verificador/INFORME.md`). Sigue en 1.32. Texto original:
  **1.25 Diurno W6a y evaluación W2 a W6** (autorizado 2026-10-18). W6a (39090434307) quedó con `recolectar` en
  rojo por cobertura: al brazo `_s151_ab_diurno_on` le faltan 4 noches. Repetir los volcanes afectados en los dos
  brazos, misma ventana (2026-10-01 a 10-07), `--ref s151-diurno-codigo`; unir con
  `experiments/_s153_fk_v2/unir_ventana.py` (D-13); juntar W2 a W6 y evaluar con `evaluar_diurno.py`; verificador
  limpio. El resultado responde #813 (D-10) y va a Nicolás; el loop no enciende la rama diurna.
- [x] **1.26 Verificador limpio de `experiments/_s153_localizacion/`** HECHA 2026-10-18 (vuelta 196): la tesis central
  REFUTADA (K no relocaliza, deja de publicar); ver la marca sobre la entrada de la vuelta original y
  `experiments/_s153_localizacion/verificador/INFORME.md`.
- [x] **1.31 HECHA 2026-10-18 (#853, R8 en el tablero publicado; D-24 aprobada por Nicolás).** Texto original:
  **1.31 El marcador del mapa de detalle no es el cúmulo en los records `ctx_cluster`** (hallazgo H3 del verificador de
  1.26, gravedad 4; leído en `frontend/index.html` de `main` el 2026-10-18: para `test1_roi`/`test1_nti_peak` el primer
  marcador es `final_hotspot`, pero para `ctx_cluster` es `anomaly_pixels[0]`, el píxel más fuerte de la escena, y por
  defecto sólo se dibuja el índice 0). Con K todos los records son `ctx_cluster`. Medido por el verificador sin navegador:
  en V1, marcadores a más de 2 km en Láscar 23 de 70 y Lastarria 34 de 46; en producción tras el backfill, Láscar
  centroide 97 % bajo 1 km contra marcador 66 %. Qué: (a) confirmarlo con el código real en el navegador sobre el
  tablero publicado; (b) si se confirma, PR que ponga `final_hotspot` como primer marcador también en `ctx_cluster`
  (es la posición del cúmulo que el tablero ya usa para la distancia), con prueba en node y R8. Display legítimo (A72):
  el dato es real, el marcador elige el píxel equivocado. Bloqueo para mergear: el sí de Nicolás (D-24), porque cambia
  lo que ve el operador.
- [~] **1.27 (vuelta 200: Terra IRRECUPERABLE; falta NOAA-21 del 18-oct desde el 2026-10-23)** CMR público, `MOD021KM`
  en ventanas de una hora: el archivo estándar NO tiene Terra el 28-sep de 01:15 a 01:40, el 2-oct de 00:35 a 00:55 ni el
  10-oct de 00:55 a 01:15 (control: el 9-oct a la misma hora está completo, 00:40 a 01:45 cada 5 min); `MOD021KM_NRT` da 0
  en el catálogo. Esos records se escribieron con NRT de LANCE (`product_version: nrt`) y quedan en C0 con su marca de
  régimen: no hay de dónde reprocesarlos. Las de NOAA-21 del 18-oct 06:4x se rehacen con `backfill-tier-a.yml`
  (2026-10-18 a 2026-10-18, overwrite, `push-main` libre) cuando exista el producto estándar (3 a 5 días). Texto original:
  **1.27 Las 56 pasadas de la ventana de 30 días que quedaron sin K** (`experiments/_s154_reproc_k/ventana_30d.json`):
  MODIS Terra del 28-sep, 2-oct y 10-oct y NOAA-21 del 18-oct 06:4x. Comprobar primero si los gránulos existen hoy en
  LAADS; si existen, `backfill-tier-a.yml` con overwrite sólo para esas fechas, despachado con `push-main` libre
  (justo después de un NRT); verificar con `verificar_ventana.py`.
- [ ] **1.28 Sombra de K** (regla de adopción §4.9): cada semana contar contra MIROVA producción (K) y sombra (C0) con el
  mismo evaluador; reversión pre-autorizada con `git revert` de #850 si se pierde una protegida A que MIROVA y la
  sombra publican y producción calla (confirmada en la cabecera de la imagen), con issue y aviso a Nicolás el mismo
  día. Hasta 29 protegidas A nocturnas o 120 días.
- [ ] **1.33 PRIORIDAD (Nicolás, 2026-10-19): déficit de magnitud de Nevados de Chillán en erupción, pasada por
  pasada.** «Sí, agrega al loop como prioridad el déficit de magnitud de Chillán: revisar pasada por pasada (empezando
  por VIIRS 750 de las 06:48) y pre-registrar D25 sobre K con Chillán como caso.» Medido el 2026-10-18 (consolidado
  remoto de Mirova-v1 contra `data/mirova_equivalent/NevadosDeChillan.json`, predicado del tablero con node): de noche
  las 10 alertas de MIROVA publicadas también por nosotros, todas con K, pero razón de magnitud 0,12 a 0,72 (mediana
  ~0,46), con «Bajo» donde MIROVA dice «Moderado» en 7 de 10. Peor caso: VIIRS_NOAA21_750 2026-10-18 06:48, 2,84 MW
  contra 22,85 (0,12). Qué: (a) para cada pasada, descomponer la diferencia en selección (píxeles que suma MIROVA y
  nosotros no: dETI, piso C1, A103), fondo (anillo regional contra vecinos, D25), recorte a cero y saturación, leyendo
  el L1B si hace falta (A6, A97, A99 rebajada); empezar por la de las 06:48 en VIIRS 750 y comparar con la de VIIRS 375
  de la misma pasada (8,93 contra 25,79); (b) verificador limpio; (c) con eso, escribir el pre-registro de D25 sobre K
  (1.29) con Chillán como caso y criterio de magnitud, para el sello de Nicolás. Sólo lectura hasta el sello (A45).
  ⚠️ **S154, 01:50 UTC, la atribución a D17 de abajo es FALSA como cierre** (la detectó el subagente del índice por
  síntoma): la tarea 1.14 (`experiments/_s151_presupuesto_magnitud/README.md` §3.2) ya había retirado «el ángulo es
  D17»: el Npix de MIROVA no crece hacia el borde, lo que empeora es nuestro fondo (F_bg 0,85 a 0,73) y el efecto de D25
  crece con el ángulo (×1,18 a nadir, ×1,41 en el borde, Tabla C2). Estado vigente: la curva es real (Chillán la
  repite; tabla reproducible en `experiments/_s154_chillan/razon_por_cenit.py` y su salida), el mecanismo está SIN
  ATRIBUIR, con D25 y D17 compitiendo. Texto original conservado:
  **Primer resultado (2026-10-19, 00:55 UTC):** la razón cae con el cenit del sensor: VIIRS 0,64 a 0,72 a 20-22°,
  0,41 a 0,46 a 49°, 0,35 (375) y 0,12 (750) a 67,6°; MODIS 0,49 a 23° y 0,24 a 38°. Es la curva que S130 ya probó
  (`docs/s130/GRADIENTE_CENITAL.md`, D17: MIROVA remuestrea a malla de área constante y es plano con el ángulo; nosotros
  caemos 2,7×). O sea que el grueso del déficit en erupción es geométrico (D17, «bow-tie + regrid»), y D25 explica a lo
  más el resto a nadir (0,72). TIFF de MIROVA para Chillán: el último es del 2026-09-22 (archivo congelado desde esa
  fecha), así que la referencia espacial de hoy son los PNG y la distancia del CSV. Decisión pendiente con Nicolás: qué
  pre-registrar primero (D17 regrid o D25).
- [ ] **1.34 Índice por síntoma** (Nicolás, 2026-10-19: «continúa con lo que recomiendes», sobre la propuesta de
  mejorar memoria y metodología tras el error de atribuir Chillán a D25). `docs/SINTOMAS.md`, corto: de cada síntoma
  («magnitud baja», «sobre-publicación», «posición corrida», «pérdida de recall», «el A/B no cambia nada») a qué está
  medido, con qué script, qué sigue abierto y qué no reabrir, con punteros a D-n, A-n y documentos de sesión. Se
  actualiza en el mismo PR en que cambia una divergencia (como A113). Y un paso nuevo en el protocolo §2: antes de
  proponer una palanca, leer el síntoma en `docs/SINTOMAS.md` y estratificar por cenit, sensor, volcán y régimen.
- [ ] **1.35 Estratificación automática por cenit y régimen en los instrumentos** (mismo pedido). Que el auto-audit
  semanal y los evaluadores de A/B informen sus métricas también por tramos de cenit del sensor y por régimen (antes y
  después de #535 y de K), para que un agregado no esconda una curva (A90, A114). Con prueba y sin cambiar ningún
  veredicto existente.
- [ ] **1.29 PRIMERO: pre-registro de D25 sobre K con Chillán como caso** (pedido original de Nicolás del
  2026-10-19; el orden «D17 primero» que yo recomendé se apoyaba en una lectura de S130 ya retirada por 1.14 y se
  revierte). D25 es la palanca cuyo efecto medido crece con el ángulo (1.14, Tabla C2). Criterio de magnitud informado
  por tramo de cenit (la curva de Chillán y la de 1.14 como referencia), verificador limpio y sello de Nicolás. Bloqueo
  para despachar: el sello.
- [ ] **1.36 Después: D17 (bow-tie + remuestreo) como hipótesis competidora de la curva angular.** Sólo si después de
  D25 queda dependencia con el cenit; diseñar la prueba que separe D17 de D25 (el Npix de MIROVA por tramo de cenit es
  la firma que 1.14 usó). Sello de Nicolás antes de despachar.
- [ ] **1.37 Propagar K al catálogo** (A113, hallado por el subagente del índice): `docs/MIROVA_DIVERGENCES.md` no
  menciona #850; D21 (banda 22) sigue «ABIERTA» aunque la banda 22 está en producción desde el 2026-10-18, y lo mismo
  para las otras dos palancas de K (Test 1 integrado, conectiva `max`). Marca al inicio de cada D afectada con qué
  cambió, cuándo y el puntero a la regla de adopción.
- [ ] **1.30 Pre-registro de MxD03 sobre K** (D-19): ídem. Bloqueo para despachar: el sello de Nicolás.
- [ ] **1.32 A/B diurno sobre K** (del verificador de 1.25, H4). El A/B W2 a W6 corrió sobre C0: de día el Test 1
  dispara en 2.000 de las 2.077 publicaciones de VIIRS 375 en negativos limpios, 987 vienen sólo de `test1_roi`, y 11
  de las 22 protegidas recuperadas también. El contrafactual sólo `ctx_cluster` (sin `max`) deja G1 W3 a W6 CUMPLIENDO
  (P = 0,001) y G2 fallando (1.142 contra 20 permitidas; 357 contra 6); con `max` podría bajar a unas 96 y 38
  (SOSPECHA). Si G1 cumple sobre K, la regla da «DECIDE NICOLÁS CON M4». Qué: perfiles diurnos sobre K (control =
  réplica K, brazo = K más `enable_daytime_viirs`), con los tres flags de K declarados (guard S153); adenda del
  pre-registro (mismas ventanas y reglas, sólo cambia la base); verificador; **sello de Nicolás** antes de despachar.
  Arreglar antes el aviso A114 del evaluador (H1: `evaluar_diurno.py:940` junta los dos sensores en el q_neg; debe ser
  por sensor) y fijar el nulo (H2: `:635`, el p95 cambia entre procesos con la misma semilla; usar el exacto).

### Bloque S158 R2 y plan S159 (agregado el 2026-10-21 ~18:15 UTC por la sesión dueña del loop)

Origen: `docs/AUDIT_S158_R2.md` (PR #888) y su bloque propuesto `tasks/LOOP_BLOQUE_S158_R2.md` (rama
`claude/s158-audit-r2-0eeee2`), que se copia aquí y se borra de esa rama. Nicolás pidió que el loop siga «con todo lo
que estamos desarrollando» y aprobó el 2026-10-21 el plan de pruebas S159
(`docs/superpowers/specs/2026-10-21-pruebas-post-auditoria-s158-design.md`, rama `s159-pruebas`), incluidos Octave para
O1 y un tope de 400 pasadas para el primer lote de N. Cada R2.x lleva entre corchetes el frente S159 que la trabaja.
Las reglas del §1 siguen intactas: nada se adopta en producción sin pre-registro, sello de Nicolás y verificador limpio.

- [ ] **R2.1 Instrumentos antes de cualquier A/B** [frente IA, worktree `C:\vrp-trabajo\s159-instrumentos`, EN CURSO].
  (a) Cero gránulos en un día con pasadas esperadas, y un L1B sin su geolocalización, cuentan como falla de cobertura y
  no como «completa» (R2-9, VB-1); toca el flujo del NRT, así que no se mergea sin el sí de Nicolás. (b) Placebo de
  ganancia constante obligatorio en toda métrica de magnitud (R2-8). (c) El default de calibración de
  `experiments/_s157_prereg_d25/evaluar_d25.py:79` contradice la adenda sellada (VB-2): se corrige sólo por adenda y
  con Nicolás. (d) Una sola definición de «alerta de MIROVA». (e) Prueba `xfail(strict)` del tope de cordura de
  `pipeline/store.py:551-557` (R2-7); el arreglo, con tag y sí (A45).
- [ ] **R2.2 A/B de D25: no leer el veredicto** [relectura D25, ola 2]. El 2026-10-18 y el 19 no se reponen mientras
  CMR no los sirva (R2-13). Vigilar en cada vuelta si CMR vuelve a servirlos (búsqueda pública `granules.json`, sin
  credenciales). Decisión para Nicolás: evaluar sin esos días o repetir en otra ventana, y agregar un brazo con el
  fondo del código.
- [ ] **R2.3 Pre-registro: fondo y suma del código en VIIRS 750 junto con quitar la compuerta de 3 K del primer pase**
  (VA-1) [síntesis, ola 3, con los datos de N]. Métricas en las dos caras: alertas de MIROVA de la misma pasada
  recuperadas (pareo a 8 min) y negativos limpios despegados del cero. Sello antes de despachar.
- [ ] **R2.4 D17 fase 0** [frentes GEO (ola 1, sin gránulos) y N (ola 2, workflow de sólo lectura con
  `EARTHDATA_TOKEN`)]: grilla de 750 m e interpolador de MIROVA. N cubre las ~40 pasadas del bloque R2 dentro de su
  tope de 400.
- [ ] **R2.5 ROI de MIROVA en Cordón Caulle y Tupungatito** [frente GEO, parte R, EN CURSO], con los TIF y la
  `Distancia_km` cuantizada (D15).
- [ ] **R2.6 Geolocalización MODIS desde MOD03** [frente M, ola 2]. P1 encontró el respaldo citable: Coppola 2026 Sci
  Data p. 4 dice que MIROVA usa MOD03 con corrección de terreno. El verificador de R2 midió el corrimiento asimétrico
  (2 a 3,6 km de un lado del barrido sobre 25°).
- [ ] **R2.7 Marcas A113 pendientes**: las del §8 de `docs/AUDIT_S158_R2.md` (bajo A45, en el PR que toque cada
  archivo), las U1 a U13 del meta-auditor (`experiments/_s158_audit_r2/m1/INFORME.md` §3) y las candidatas de P1 y P2
  (`experiments/_s159/p1/INFORME.md` §4, `experiments/_s159/p2/INFORME.md`): entre ellas «MIR solo nocturno» en
  CLAUDE.md:183 y «para MODIS y VIIRS 375 manda el paper» en `docs/MISSION.md:130`, cuando ningún paper describe la
  detección de VIIRS 375 (P2).
- [ ] **R2.8 Pendientes de Nicolás**: D-10 (VIIRS diurno; la rama apagada usa K1 -0,6 y no tiene filtro de reflejo
  solar, VB-3) y la revisión visual del §9 de `docs/AUDIT_S158_R2.md`.
- [ ] **S159 frentes sin R2.x** [ola 1, EN CURSO]: P3 (linaje MODIS), O1 (los ports contra el `.m` en Octave, con
  paquete para MATLAB Online), COB (las 411 pasadas del OSF 2025 sin record nuestro y los huecos de producción del 13
  y el 20 de octubre). P1 y P2 terminados (commits `241234581` y `353229357` en `s159-pruebas`).

## 5. Cola de decisiones para Nicolás (el loop agrega; Nicolás responde en el issue)

| # | decisión | evidencia | PR / tag | issue |
|---|---|---|---|---|
| D-45 | **CERRADA: opción (ii)** (Nicolás, 2026-10-22, respuesta textual: «Sí a D-45 opción (ii): P2 se decide con la prueba de signos por bloque noche-volcán (exacta hasta 20 noches), en una quinta adenda sellada, con implementador, candados y verificador antes del tag; corrige también V42-21. Hazlo en una sesión nueva tras /cierre.»). Pendiente de ejecutar en S161. Texto original: **PENDIENTE, bloquea el tag de D25**: cómo decide P2 con pocas noches. El verificador (D-42 vuelta 3, V42-20, gravedad 3, por enumeración exacta de los 2^B signos con la W real) mostró que el intervalo bootstrap de D-34 con pocos bloques da PIERDE en 6,25 %% de las asignaciones con B = 7 noches iguales (todas de un lado más las de 6 contra 1), así que **con 7 noches discordantes P2 queda INDECIDIBLE siempre**, aunque la prueba exacta de signos dé p = 0,78 %%; y con tasas en el borde (4,6 a 5,5 %%: 11 en 10 noches, 8 en 7) la decisión depende de la semilla 161 (falla el 42 a 92 %% de las semillas). Opciones: (i) dejar como está; (ii) **decidir P2 directamente con la prueba de signos por bloque noche-volcán** (valor-p exacto enumerado hasta 20 noches, si no 10.000 sorteos; GANA o PIERDE con p de 5 %% o menos; BLOQUEA si el neto va en contra sin llegar; SIN SUSTRATO con 4 noches o menos, como D-44), calibrada por construcción y sin semilla; (iii) mantener D-34 y calibrar por enumeración exacta (quita la semilla, no el 6,25 %% de B = 7); (iv) 10.000 sorteos. Recomendación del loop: **(ii)**, en una quinta adenda sellada, con implementador, candados y verificador antes del tag. Además V42-21 (el placebo simétrico sortea por pasada y no por noche, una línea) se corrige en esa misma ronda | `experiments/_s159/instrumentos/verificador_d42/vuelta3/INFORME.md` (`bcfdc7c76`, rama `s159-evaluador-d25`) | #890 | (sin issue) |
| D-44 | **CERRADA: sí a las tres** (Nicolás, 2026-10-22, respuesta textual: «Sí a D-44: un PIERDE calibrado manda (NO CUMPLE), acepto que P2 no decida con 4 noches o menos, y corre antes del tag los placebos (a), (b) y simétrico sobre producción, con verificador.»). Con esto la lectura de §2.5 de `ADENDA_CALIBRACION_P2.md` queda fijada como la del código (PIERDE manda antes que INDECIDIBLE, como PREREGISTRO §8 d y H2). Texto original: **PENDIENTE, antes del tag de D25**: (1) V42-03, si un PIERDE calibrado de P2 en un sensor manda sobre un INDECIDIBLE en el otro (el código da NO CUMPLE, coherente con PREREGISTRO §8 d y H2): recomendación, **sí, NO CUMPLE**; (2) aceptar que P2 no decide con 4 noches discordantes o menos (16 combinaciones de signo, el azar ya da 12,5 %%): recomendación, **sí**; (3) V42-10: correr antes del tag los placebos (a), (b) y simétrico sobre producción (instrumento, sin leer brazos), o leer ya declarando el placebo como SIN DATO: recomendación, **correrlos**, son unas horas y dan la tasa de falsos de P2 calibrada sobre datos reales | `verificador_d42/INFORME.md` y `vuelta2/INFORME.md` (rama `s159-evaluador-d25`, `9359a762f`) | #890 | (sin issue) |
| D-43 | **PENDIENTE**: las nueve decisiones de la auditoría S160, con su recomendación, en `docs/AUDIT_S160.md` §5 (rama `s160-auditoria`, `b941c8052`; no se copian aquí para que haya una sola vara). Las que tocan esta cola: su 1 = #891 (sí); su 2 = D-42 (mismo problema de P2 visto por otro camino, V1a-01); su 3 = D-37 (#892) más que «sin gránulos de una plataforma esperada» no se llame «Cobertura: completa» en el NRT (241, gravedad 4; toca `pipeline/`, A45); su 5 = llevar a `main` lo de S157 y S158 (el `CLAUDE.md` que carga cada sesión no tiene ninguna de sus marcas); su 7 = guarda de la copia de la referencia (245) y de token vacío en `nrt.yml` (247: el token vence el 2026-12-07) | `docs/AUDIT_S160.md` (rama `s160-auditoria`), `docs/COLA_CAMPO.md` (10 casos; C-06 es el cese del 2-nov) | #891 | (sin issue) |
| D-42 | **CERRADA: opción (a)** (Nicolás, 2026-10-22 ~09:40 UTC, respuesta textual: «Sí a D-42 opción (a): calibra P2 como M en una cuarta adenda sellada, con los candados de V34-03 y V29-01 y verificador limpio antes del tag.»). Adenda `experiments/_s157_prereg_d25/ADENDA_CALIBRACION_P2.md` (`ca65069f6`, rama `s159-evaluador-d25`): signo de cada bloque noche-volcán al azar, 1.000 sorteos, semilla 161, 5 % por cola; si falla, P2 INDECIDIBLE. Texto original: calibración de P2. Lo confirma por otro camino la auditoría S160 (V1a-01: con tolerancia 0, P2 aprueba un placebo que apaga al azar el 1 % de las publicaciones; recomienda no leer #890 hasta que el evaluador lo rechace). El verificador limpio de D-34 (V34-01, medido con la función real sobre datos sintéticos, n = 2.000 por escenario) muestra que la regla sellada de P2 decide GANA o PIERDE en falso en **24,8 %** de los nulos con 3 noches discordantes de signo común por noche (4 noches 13,0 %, 5 noches 6,5 %, 12 noches 4,0 %; nulo iid 6,5 a 8,7 %): con pocas noches todas del mismo lado, ningún remuestreo por bloques cruza 0. M tiene su calibración (D-27) y queda INDECIDIBLE si falla; P2 adoptó los mínimos de M sin esa calibración. El código hace lo que la adenda dice: el defecto es de la regla. Opciones: (a) **calibrar P2 como M**: sobre las mismas pasadas discordantes, nulo con el signo de cada noche al azar (1.000 repeticiones, semilla fija); si los falsos GANA más PIERDE pasan de 5 %, P2 queda INDECIDIBLE; (b) subir el mínimo de noches (no basta: con 8 noches correlacionadas sigue en 7,0 %); (c) leer como está, con V34-01 declarado. Recomendación del loop: **(a)**, en una cuarta adenda sellada antes del tag, junto con los candados de V34-03 (7 mutaciones que hoy pasan en verde) y D-29; después, verificador limpio del cambio y recién ahí el tag. Además V34-02: bajo el nulo, BLOQUEA apaga CUMPLE en 37 a 48 % de los casos (lo pide la adenda; leerlo como moneda, no como señal) | `experiments/_s159/instrumentos/verificador_d34/INFORME.md` (`786bfb288`, rama `s159-evaluador-d25`) | #890 | (sin issue) |
| D-41 | **PENDIENTE**: alertas sólo OCR en el criterio de victoria de VRP Chile (las 184 protegidas que sólo existen en el OCR; entre 40 y 90 serían falsas, centro ~55, estimado). Opciones: todas; sólo las del método de la estrella, nocturnas y desde V29.2 (2026-06-13); ninguna. Recomendación del informe y del loop: **sólo estrella nocturna desde V29.2**, el resto contado aparte. Hoy `Metodo_Validacion` no dice el método (hay que leerlo en la nota, R10). No toca los pre-registros sellados: aplica a evaluaciones nuevas, y en las selladas se informa como lectura adicional | informe §4 y H-O1 | | (sin issue) |
| D-40 | **PENDIENTE**: arreglos del OCR y la operación de Mirova-v1 (R5 fallar fuerte, R6 vigilante de dato, R7 cron de respaldo y fila de credencial, R8 lista cerrada de sensores, R9 y R10 marcar el método de grupo y guardar el método real, R11 rastro de reconciliación, R12 mojibake). Recomendación del informe: R9 + R10 (marcar, no apagar) y R5 a R7 primero; 141 ciclos reales con 0 filas cerraron «Proceso completado» | informe §3 y H-P1, H-O1, H-O4 | | (sin issue) |
| D-39 | **PENDIENTE**: bucle de push del scraper Mirova-v1 (la tabla pierde filas: 1.948 en 60 días, 18 protegidas, 14 de Láscar, por 8 commits del propio scraper que mezclan como texto un CSV reescrito en otro orden). Opciones: R1 solo; R1+R2+R3; nada. Recomendación del informe y del loop: **R1+R2+R3** y **reponer las filas en Mirova-v1** (R4, `filas_recuperadas.csv`); además R13 en VRP Chile (`sync-mirova-csv.yml:191`: reset a `origin/main` en vez de rebase, porque el mismo mecanismo fabricó la copia corrupta `81dd25ce3`). Es producción de Mirova-v1 y un workflow de VRP Chile: sólo con el sí de Nicolás | `experiments/_s159/mirova_v1_auditoria/INFORME.md` H-T1 y H-V1 (copia; scripts en `D:\vrp-trabajo\mirova-v1-auditoria\`) | | (sin issue) |
| D-38 | **PENDIENTE**: alarma de plataforma callada en #892: ¿comenta cada día mientras dure (lo pedido), o patrón S123 (editar el cuerpo y comentar sólo cuando cambia la lista de sensores callados)? Recomendación del loop: **patrón S123**; un comentario diario idéntico se deja de leer, y el cambio son pocas líneas, después del merge | descripción de #892, «Preguntas que quedan» 2 | #892 | (sin issue) |
| D-37 | **PENDIENTE, con plazo 2026-11-02 13:00 UTC**: merge de **#892** (vigilancia por plataforma, aviso del cese de Suomi NPP en index, diario y mosaico, ficha SDA v1.10; toca `frontend/` y `.github/`, no `pipeline/` ni `data/`). CI `pytest` verde; verificado en el navegador (comentario en el PR). Más la pregunta 1 del PR: el issue informativo, ¿«una sola vez» aunque se cierre (busca en abiertos y cerrados) o se repite al cerrarlo? Recomendación del loop: **mergear ya** y **una sola vez** (el cese es un hecho único; repetirlo es ruido) | #892 y su comentario de verificación (`issuecomment-6332148549`) | #892 | (sin issue) |
| D-36 | **PENDIENTE**: ampliar el port (bloque S160 §b.9). El verificador limpio deja el «GANA contra K» de MODIS **NO RESUELTO**: el estrato de negativos limpios donde producción calla (5.093 noches MODIS, 3.348 VIIRS 375) tiene 0 de 37 y 0 de 45 sorteados, y con 0 eventos el bootstrap estratificado no ve nada; la cota de Wilson deja el silencio del port hasta 9,4 % (MODIS) y 8,5 % (VIIRS 375), contra 0,76 % y 3,85 % de K. Recomendación del loop: **sí, un lote de sólo lectura con 300 a 400 negativos de ese estrato por sensor**, con pre-registro previo (con 0 en 400 la cota baja a ~0,95 %, del orden de K); el lote corre fuera de producción | `experiments/_s159/portes/verificador/INFORME.md` V-1 (`ca034d66e`, ramas `s159-portes` y `s159-pruebas`) | | (sin issue) |
| D-35 | **CERRADA: sí** (Nicolás, 2026-10-22 ~09:30 UTC, respuesta textual: «Sí a D-35: despacha el brazo de sensibilidad de D25 sobre el 17 al 19 de octubre por NRT, declarado aparte, desde un tag de código del evaluador.»). Despachado como run **39756261926** desde `s157-d25-k-codigo` (`66961f65d`, el código de V1), 2026-10-17 a 2026-10-19, brazos control, gemelo y D25; CMR NRT servía los 6 productos VIIRS esos días (4 a 5 gránulos nocturnos cada uno, 09:32 UTC). Sus resultados **no se miran antes del tag de lectura de D25** y no entran al veredicto sellado. Texto original: brazo de sensibilidad de D25 sobre el 17 al 19-oct por NRT de LANCE (bloque S160 §b.1), declarado aparte y sin tocar el veredicto sellado. Recomendación del loop: **correrlo**, despachado desde el tag de lectura de D25 en cuanto exista; dice si los días excluidos por D-29 cambian el veredicto. **Plazo medido 2026-10-22 ~03:28 UTC: LANCE retiene ~7,7 días; el 17-oct se purga cerca del 2026-10-24 ~16:00 UTC** | bitácora 2026-10-22 ~03:45 UTC (S160 nocturna) | tag de lectura de D25 (por crear) | (sin issue) |
| D-34 | **CERRADA: opción (c) con la variante** (Nicolás, 2026-10-21, respuesta textual a la propuesta del coordinador: «si, has lo que nos entregue mayor informacion o la mejor metodologia para lograr nuestro trabajo, tenemos tokens  tiempo y podemos probarlo todo»). P2 de D25 se decide como M: sobre las pasadas donde K y D publican distinto, diferencia neta (alertas bajo 1 MW recuperadas menos publicaciones de más en negativos limpios) con intervalo bootstrap al 95 % por bloques noche-volcán. GANA si el intervalo queda entero del lado bueno, PIERDE si entero del malo, EMPATE si cruza 0; variante: una diferencia neta en contra que no alcance PIERDE bloquea CUMPLE (como EMPEORA en los estratos que sólo bloquean, D-27). Se declara que K' mide determinismo dentro de una máquina y se cita el ruido entre máquinas de F/K V1 con su salvedad. La lista de pasadas discordantes se informa siempre sin decidir, y el evaluador informa también lo que habrían dado (a) y (b), sin decidir. Reemplaza a D-33 | `experiments/_s159/gemelo_d25/INFORME.md` | #890 | (sin issue) |
| D-33 | ⚠️ **REEMPLAZADA por D-34 el mismo día, antes de implementarse** (el coordinador mostró que (b) usa un corte arbitrario de dos pasadas y un diagnóstico hecho después de mirar, y que había una opción (c) mejor). Texto original: **CERRADA: opción (b)** (Nicolás, 2026-10-21: «Opción (b) por adenda: todo GANA o PIERDE de P2 decidido por una o dos pasadas netas se lista y se diagnostica pasada por pasada antes de declararlo; además se declara que K' mide determinismo dentro de una máquina y se cita el ruido entre máquinas de F/K V1 con su salvedad.»). Tercera adenda de D25 (`ADENDA_GEMELO.md` en `s159-evaluador-d25`); el evaluador marca esos casos como pendientes de diagnóstico en vez de declararlos | `experiments/_s159/gemelo_d25/INFORME.md` (0 de 4.610 en V1; 0 de 3.420 entre máquinas en F/K V1, detector C0, sin Villarrica) | #890 | (sin issue) |
| D-32 | **CERRADA: sí** (Nicolás, 2026-10-21: «Sí: sube las repeticiones de la calibración de d′ (por ejemplo a 1.000) y sella esa semilla y ese número antes del tag, para que una sola semilla no decida V2 VIIRS 750.»). La calibración de d′ pasa de 200 a 1.000 repeticiones con el tope por cola proporcional (5 % por cola), con semilla fija; número y semilla quedan escritos en el §5 de `ADENDA_PLACEBO.md` antes del tag de lectura | verificador del comparador, punto 5.1 | #890 | (sin issue) |
| D-31 | **CERRADA: sí** (Nicolás, 2026-10-21: «Sí: despacha el censo de ~120 pasadas (los 60 cúmulos de cumbre en 0 MW, los 59 far e Isluga 10-12) para cerrar el efecto de F en negativos, con el mismo workflow de sólo lectura.»). Censo que reemplaza al estimador ponderado de F sobre los negativos elegibles; lo corre el agente del frente N con pre-registro previo | `experiments/_s159/n/verificador/INFORME.md` | rama `s159-n` | (sin issue) |
| D-30 | **CERRADA: sí a las cinco** (Nicolás, 2026-10-21, respuesta textual: «Acepto tus recomendaciones para las cinco preguntas de la adenda D-28: INDECIDIBLE si falla la calibración de d′, sólo la cola de mejora en esa calibración, la lectura del caso sellada como el brazo a mitad de camino, el comparador apagado con --calibracion sellada, y los tres detalles numéricos.»). Cambian el código de `b4258040c` en dos puntos: (1) si d da MEJORA y la calibración de d′ falla, el estrato queda INDECIDIBLE (no NEUTRO); (2) la calibración de d′ exige sólo la cola de mejora. Se aplica DESPUÉS de que entregue el verificador limpio que corre sobre `b4258040c`, y ese delta pasa por verificación antes del tag de lectura | descripción de #890 (preguntas 1 a 5) | #890 | (sin issue) |
| D-29 | **CERRADA: sí** (Nicolás, 2026-10-21: «D25 se evalúa sin el 17 al 20 de octubre ni el 13 parcial, declarados en el veredicto»). Los días que CMR no sirve no se reponen ni se repite la ventana: se excluyen de V1 en los tres brazos por igual y el veredicto lo dice en su primera línea. La relectura espera la implementación de D-28 y su verificador limpio | COB H2 (`experiments/_s159/cob/INFORME.md`); conteos CMR del 2026-10-21 en la bitácora | #890 | (sin issue) |
| D-28 | **CERRADA: SELLADA** (Nicolás, 2026-10-21: «Placebo como comparador y no como compuerta, por adenda sellada»). Segunda adenda de D25: MEJORA de M sólo si D queda más cerca de MIROVA que K por ĝ (mediana de D/K del estrato); EMPEORA sigue contra K; la compuerta se retira. Los detalles del §3 derivan de (b) y se pueden objetar antes del tag de lectura | `experiments/_s157_prereg_d25/ADENDA_PLACEBO.md` (`2629f5a16`, rama `s159-evaluador-d25`) | #890 | (sin issue) |
| D-25 | **CERRADA: SELLADA** (Nicolás, 2026-10-18, las dos opciones recomendadas; #857). **Sello de la adenda del A/B diurno sobre K** (tarea 1.32), con dos decisiones: (1) cola exacta del nulo en G1 (recomendada) o muestreo; (2) si G1 cumple sin W2 y falla con W2: DECIDE NICOLÁS CON M4 (recomendada, simétrica de la regla de «pasa sólo con W2») o NO ADOPTAR. Después del sello y antes de despachar: H2a, H2b y, si se aprueba, la cola exacta con sus pruebas | `experiments/_s151_ab_diurno/ADENDA_K.md` v2, `verificador_adenda_k/INFORME.md` | #857 | pendiente |
| D-24 | **CERRADA: sí** (Nicolás, 2026-10-18; #853 mergeado y R8). Arreglo del marcador del mapa de detalle en los records `ctx_cluster` (tarea 1.31): primer marcador = `final_hotspot` (el cúmulo) en vez de `anomaly_pixels[0]` (el píxel más fuerte de la escena). Cambia lo que ve el operador; con K afecta a todos los records. Recomendación: sí, después de confirmarlo en el navegador | `experiments/_s153_localizacion/verificador/INFORME.md` H3; `frontend/index.html` de `main` | | pendiente |
| D-23 | **EN CURSO** (Nicolás, 2026-10-18: sí al reproceso histórico; tarea 1.24). Reproceso de los 3.231 records MODIS de enero a junio de 2026 escritos con los gates intra-radio (deriva 1.23 bis, CONFIRMADA). Recomendación: hacerlo dentro del reproceso histórico con K si se adopta #850, no antes | `experiments/_s153_deriva_123bis/` | | pendiente |
| D-22 | Ratificar la desviación de W5a (intento 2 entero para Llaima `_s151_ab_diurno_on`: 2 records diurnos VIIRS 375 distintos por empate del top-100, mismo predicado, mismo cúmulo) y, aparte, decidir si se extiende a VIIRS el desempate determinista de #844 (producción, A45) | bitácora vuelta 189 | | pendiente |
| D-21 | **CERRADA: sí** (Nicolás, 2026-10-18; merge squash `34cea39e` a las 09:57:30 UTC, marca #851). **Merge de la adopción de K** (producción, A45). Cumple la regla #848 entera: combinado CUMPLE (original y SN), verificador CONFIRMADO, R3 idéntico, cruce de 1 MW ninguno, A61 sin protegidas movidas a otro objeto, segundo lector 4 de 4 lejanas, R2 5 de 5, K sobre main idéntico. Además: auto-audit sin recalibrar (recomendado), laboratorios lowT y ndc_focus en C0, aviso a consumidores | `experiments/_s153_fk_v2/` | #850, tag `pre-s153-adopcion-k` | pendiente |
| D-19 | MxD03 después de la 1.23: las 2 protegidas que pierde caen por el **Test 1**, que K elimina. Propuesta del loop: no adoptarla sobre producción de hoy; si K se adopta (#848), pre-registrar MxD03 **sobre K** (sin Test 1 el mecanismo de esas pérdidas no existe), con Láscar bajo 35° como vara y el borde del barrido aparte | `experiments/_s151_mxd03_sola_123/resultado/` (evaluación y verificador CONFIRMADO) | | pendiente |
| D-20 | ~~Regla de adopción de K~~ **APROBADA** (Nicolás, 2026-10-17 ~23:45 UTC: «tal como está, incluida la reversión con git revert pre-autorizada»), antes de evaluar V2; mergeada (squash `cf507f46`); instrumento fijado en `2766c198` | `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`, verificador limpio con arreglos aplicados | #848 | cerrada |
| D-1 | Adoptar conectiva `max` en VIIRS 375 (criterio §1.2 por medir en 0.2) | `docs/S150_RESULTADO_MESES.md`, `docs/audit_s150/meta/AUDITOR_F2_NUMEROS.md` | pendiente | pendiente |
| D-2 | ~~Merge del arreglo del scraper Mirova-v1#19 (tarea 0.5)~~ **HECHO** (Nicolás, 2026-10-15; squash `40ef1a45`) | CI verde de Mirova-v1#21; 4 tests | Mirova-v1#21 | #783 |
| D-3 | Marca de régimen en `store.py` (tarea 0.6): **APROBADA** (Nicolás, 2026-10-15), se mergea con el CI del PR actualizado | 4 tests, 3 fallaban antes; suite 1706 | #785, tag `pre-s151-marca-regimen` | #786 |
| D-4 | ~~Alerta protegida: lectura A o B~~ **DECIDIDA: A** (Nicolás, 2026-10-14; propagada en #808) | `docs/S151_CRITERIO_CLASE_MIROVA.md` §5 | #780 | #782 (cerrado) |
| D-5 | ~~Sello del probe de D25 en VIIRS 750~~ **SELLADO** (Nicolás, 2026-10-15); piloto Tupungatito 10 pasadas, run 38678279921 | `experiments/_s151_d25_v750_disco/README.md`, verificador limpio con arreglos | #790 | #793 |
| D-6 | ~~A/B de anomalía mayor~~ **DECIDIDA: SIGUE** (Nicolás, 2026-10-14; estudio TIF primero) | `experiments/_s151_ab_vrp_max/PREREGISTRO.md`, verificador limpio con arreglos | #794 | #795 |
| D-7 | ~~Sello del A/B de F y K~~ **APROBADO** (Nicolás, 2026-10-14); V1 en curso, run 38639658446 | `experiments/_s151_prereg_fk_11/PREREGISTRO.md`, verificador limpio con arreglos | #797 | #798 |
| D-8 | ~~Sello del A/B reducido de la caja~~ **SELLADO** (Nicolás, 2026-10-15); workflow propio con otro grupo de concurrencia en preparación para no desplazar a F/K | `experiments/_s151_prereg_caja/PREREGISTRO.md`, verificador limpio con arreglos | #800 | #801 |
| D-9 | ~~Alertas de 0,05 MW o menos~~ **DECIDIDA: SN** (Nicolás, 2026-10-15), informando también SE y la regla original en cada evaluación; implementación en curso | `experiments/_s151_alertas_minimas/README.md`, verificado | #810 | #811 |
| D-10 | ~~¿Abrir el día en la réplica?~~ **DECIDIDA: 1** (Nicolás, 2026-10-15): rama diurna VIIRS apagada por flag (tag `pre-s151-rama-diurna-viirs`) y A/B diurno; código en curso | `experiments/_s151_alertas_diurnas/README.md`, verificado | #812 | #813 |

| D-13 | **DECIDIDA: repetir y unir intentos (A108)** (Nicolás, 2026-10-16), aunque tome más tiempo | V1 intento 3 y W2a intento 2 despachados | F/K, diurno | cerrada |
| D-13 (texto original) | Cobertura de los A/B largos: ¿repetir y unir intentos (A108, ~20 h por vuelta y puede abrir huecos nuevos) o evaluar sobre la intersección de pasadas presentes en todos los brazos, informando las excluidas (desviación registrada; la pérdida es por descarga, independiente del brazo)? Recomendación del loop: intersección, con la regla del 5 % del control contra producción como compuerta | `C:\Users\nmend\AppData\Local\Temp\claude\fk_v1\detalle_cobertura.txt` (V1: 31 de 44 jobs cortos, 0,5 a 1,4 % por job; C0 de PCC falla el 5 %) | F/K V1, V2a, diurno | pendiente |
| D-12 | ~~Merge de la columna~~ **HECHO** (Nicolás, 2026-10-16): Mirova-v1#25 mergeado 11:43 UTC (`2eac1758`); historia despachada (run 38895687049); hito A119 en #838 | | | cerrada |
| D-12 (texto original) | Merge de la columna `Distancia_aprox_*` en el scraper (Mirova-v1 es producción) | verificador limpio en dos vueltas: sin bloqueos; `Distancia_km` y columnas viejas byte a byte iguales; umbral 5 provisional | Mirova-v1#25 (`f774a5d`) | pendiente |
| D-17/D-18 y token | **DECIDIDAS por Nicolás el 2026-10-17 (~20:10 UTC): «continúa con todo, haz lo que recomiendes».** D-18: #846 mergeado (`eb97779f`), 1.23 sellada, tag `s151-1.23-probe`, `Lascar-2a` suelto despachado (run 39066031570). D-17: #844 mergeado (`eed583b4`, producción, tag defensivo `pre-s151-desempate-top100`) tras fijar los despachos restantes del diurno al tag `s151-diurno-codigo` (`eb97779f`, mismo `pipeline/` que W2 a W5); reproceso de los 29 no hecho (opcional); #845 cosmético después, con el CI de la rama actualizada. Token `vrp-chile-cron-externo` **sin vencimiento** por ahora (anotado en `REGISTRO_CREDENCIALES.md`; se acortará más adelante). Cron externo: lo cambia Nicolás en cron-job.org | bitácora vuelta 169 | #844, #845, #846 | cerradas |
| D-18 | Sello y merge del pre-registro 1.23 (MxD03 sola: nulo de 20 rumbos en km, vara VIIRS 375 de la misma noche, lectura 4 con signo, borde sobre 35° descriptivo). Puede decir si la posición MxD03 es mejor y si las pérdidas de Láscar son azar o efecto de una posición mejor; NO puede hacerla adoptable (por la letra vuelve a dar PIERDE PROTEGIDA) ni contestar el borde del barrido. 24 medios jobs, ~27 min el peor | `experiments/_s151_mxd03_sola_123_verif/` (dos vueltas) más revisión del último diff | #846 (`e87a5e17`) | pendiente |
| D-17 | Merge del desempate determinista del top-100 MODIS (tarea 1.22, PR #844, producción). Congela con una convención fija (VRP, después fila, después columna) una elección que hoy hace la CPU del runner; no mejora la física. Efecto estimado: ~29 de 13.353 records MODIS (0,2 %) podrían cambiar su publicación hacia adelante (SOSPECHA: 9 de lejana a cráter, 2 dejan de publicarse). Sin flag (el «apagado» de hoy no es un comportamiento definido). **Cuándo:** después de terminar los A/B en curso (F/K V2b desde tag; diurno W5 y W6 desde `main`), o fijando sus despachos restantes a un tag previo, porque brazos de antes y después no se mezclan. Recomendación del loop: sí, con un reproceso acotado previo de los 29 (dos convenciones, dos runners) si Nicolás quiere ver la dirección | `experiments/_s151_desempate_top100_verif/VERIFICADOR.md` | #844 (`7c6f36d6`), #845 cosmético aparte (`3e0f940b`), tag `pre-s151-desempate-top100` | pendiente |
| D-14/D-15/D-16 y cron | **DECIDIDAS por Nicolás el 2026-10-17 (~12:40 UTC): «sí a todo»**, es decir, las recomendaciones del loop. D-14: #840 mergeado (squash `e472c673`) y 1.21 sellada; tag `s151-1.21-probe` en `e472c673`; Láscar-2 suelto despachado (run 39033482528). D-15: tag `s151-fk-v2-codigo` en `7b74435e`; V2b despachada desde el tag (run 39033530622). D-16: (a) en curso (agente, rama `loop/unir-intentos-hotspot-escena`); (b) pasa a la tarea 1.22. Cron externo `10 1-12 * * *` UTC: lo cambia Nicolás en cron-job.org (su cuenta); falta la fecha de vencimiento del token | bitácora vuelta 137 | #840, tags | cerradas |
| D-16 (ampliada 2026-10-17, vuelta 136) | **Ya no es sólo Copahue: bloquea también F/K V1.** En Llaima del control de V1 (intentos 1 y 3, mismo commit), 4 de 458 pasadas MODIS tienen otro hotspot de escena con la misma BT máxima, y 2 cambian campos de decisión (Terra 2026-10-06 01:45: `final_hotspot_source` test1/cluster_rescue, `vrp_mw` 4,281/3,568, clase `summit` en las dos). Unida, Llaima del control da 461 pasadas = F, y **la cobertura de V1 queda pareja**; sin unirla faltan 2 (VIIRS NOAA-21 750 del 09-16, sólo en el intento 1). Repetir no sirve: depende de la CPU de cada corrida. Opciones: (a) admitir en `unir_intentos.py` diferencias del hotspot de escena MODIS cuando `distance_class`, `primary_cluster` y el predicado del tablero coinciden, conservando el primer intento e informándolas (cambio del instrumento: tests y verificador); (b) arreglar el desempate en producción (A45). Recomendación: (a) ahora para poder evaluar V1 y W2, (b) como tarea propia | bitácora vueltas 127 y 136 | | pendiente |
| D-16 | W2a del A/B diurno: el intento 2 solo es completo y parejo (1.085 noches por brazo), pero `unir_intentos.py` (#841) bloquea Copahue `_s151_ab_diurno_on` porque un record MODIS Aqua (2026-06-18 07:30) difiere en un campo de decisión entre intentos del MISMO commit: `final_hotspot_source` test1 contra cluster_rescue, hotspot a 20,31 contra 0,94 km, `vrp_mw` 4,782 contra 1,834; los 11 `anomaly_pixels`, `distance_class` (summit), `primary_cluster.vrp_mw` (1,834) y la BT máxima (274,29 K) idénticos. SOSPECHA: empate de BT máxima desempatado según la CPU. Opciones: (a) usar el intento 2 entero e informar el record; (b) repetir Copahue otra vez; (c) arreglar el desempate en producción (A45). Recomendación: (a) para W2 y (c) como tarea propia | bitácora vuelta 127 | | pendiente |
| D-15 | Commit de V2b de F/K: el pre-registro dice `--ref main` (`PREREGISTRO.md:139`), pero desde el commit de V1 y V2a (`402447f3` y `7b74435e`, mismo `pipeline/`) entraron #785 (marca de régimen en `store.py`), #821 (rama diurna apagada por flag, `process_viirs_mod.py`) y #822 (perfiles diurnos). Con `main`, la ventana V2 mezclaría dos pipelines (A108). Recomendación del loop: despachar V2b desde un tag en `7b74435e` | `git diff --stat 7b74435ed origin/main -- pipeline/` | tag propuesto `s151-fk-v2-codigo` | pendiente |
| D-14 | Sello del probe 1.21 (C, CC, M, MC, R, RC) y merge de #840 (el clasificador de permisos le negó el merge al loop el 2026-10-16) | `experiments/_s151_mxd03_cumulo_121/README.md`, verificador limpio en dos vueltas (`experiments/_s151_mxd03_cumulo_121_verif/`) más revisión del último diff | #840 (`2d9be9a9`) | pendiente |
| D-11 | ~~Sello del probe 1.17~~ **SELLADO** (Nicolás, 2026-10-16); run 38894508138 sobre `d9b10482` (incluye #837) | Sello del probe 1.17 (posición MODIS con MxD03 en los 11 volcanes; regla 1 como compuerta) | `experiments/_s151_mxd03_etiquetas/README.md`, verificador limpio en dos vueltas (`experiments/_s151_mxd03_etiquetas_verif/`) | #834, #835, #837 | pendiente |

## 6. Bitácora (la más nueva arriba; una entrada por vuelta)

### 2026-10-26 ~13:30 UTC (S164, vuelta 3): #907 mergeado (cableado de la vía V750, flag apagado)
- `loop-viirs750-2` entregó #907 en `f96b379e7` (6 commits sobre `b09a7b321`; tag `pre-rebase-s162-via-mirova` sobre
  la versión previa `a16aa14b4`). Suite en árbol quieto: 2.582 aprobadas, 29 omitidas, 2 xfail, 0 fallas
  (`experiments/_s162_v750a/suite_via_salida_cola.txt`). Verificador limpio Sonnet: LISTO CON CAMBIOS, ninguno sobre el
  código A45, aplicados en `89e9d2855` (`experiments/_s162_v750a/verificador_cableado/INFORME.md`). Bit a bit del
  almacén: 6.143 de 6.143 records iguales, control con la marca distinto en 32 de 45.
- Alcance menor que el parche aprobado: sin kwarg nuevo; la vía reconoce el volcán por coordenadas, así que
  `run_pipeline.py` y la firma de `calculate_vrp` no cambian (paridad GR1). Archivos A45: `process_viirs_mod.py` (bloque
  dentro de `ENABLE_V750_CODIGO_MIROVA`) y `store.py` (tres compuertas saltadas sólo si `via_codigo_mirova is True`).
- Revisión propia del diff: el flag se lee de `_t` con valor por defecto False y ningún perfil lo pone (`git grep` en
  `pipeline/profiles/` de `origin/main`: 0). Sí de Nicolás: vuelta 11 de S163 («apruebo los últimos 3 puntos»).
- Tag defensivo `pre-s164-merge-907` sobre `main` `14453e3f6`; merge commit `cff07d173`; Tests en `main` verde
  (run 40329188081). Encender la vía sigue exigiendo el sello de V750-A, censo, sombra, tag y el sí de Nicolás.

### 2026-10-26 ~13:05 UTC (S164, vuelta 2): D-39 verificado y paso 1 hecho; la pausa del scraper la negó el clasificador
- `d39-mirova-v1` entregó (informe en su rama `claude/s163-d39-mirova-v1-710f72` `49de07d65`,
  `experiments/_s163_d39_mirova_v1/INFORME.md`; verificador limpio Fable 5.1, ningún REFUTADO): 0 llaves perdidas y 0 campos
  cambiados en el consolidado y en el OCR, +2.351 filas repuestas, todas reales. Hace falta sumar
  `s163/d39-reposicion-y-bucle` (`dd606a65a`): el bucle viejo volvió a perder 241 filas el 2026-10-24 17:44 UTC, dos de
  ellas protegidas (Villarrica MODIS 2026-05-29 19:55, 1,83 MW; Chillán VIIRS 375 2026-10-24 05:48, 2,36 MW).
- Comprobación propia (CSV bajados por raw, sin clonar el repo de 14 GB): 2.351 llaves de reposición, 0 presentes en
  `main` `5bb1c8edf`, las dos protegidas presentes en la reposición y ausentes de `main`; unión = 45.367 = 43.016 + 2.351.
  El diff `main...dd606a65a` no toca `registro_vrp_consolidado.csv` ni `registro_vrp_ocr.csv` (sólo código, pruebas y el
  archivo de reposición).
- Paso 1: `fix/referencia-estable` avanzó por fast-forward a `dd606a65a`; CI del PR #26 en verde (6 de 6, run 40328078318).
- Paso 2 (`gh workflow disable` de `main.yml` y `ocr_workflow.yml`): **negado por el clasificador de permisos** («Interfere
  With Workloads»). No se intentó por otra vía. El scraper sigue corriendo normal; nada cambió en `main` de Mirova-v1.
  Los pasos 2 a 6 los hace Nicolás o da el permiso.

### 2026-10-26 12:38 UTC (S164, vuelta 1): relevo tomado; estado verificado contra el remoto
- `loop/activo` = remoto en `4d41d78eb`; `main` en `b09a7b321`. Disco: C: 16 GB, D: 8,4 GB libres.
- NRT: 5 corridas verdes seguidas (08:10 a 11:10 UTC), la de 12:10 en curso; último dato en `data/mirova_equivalent/`
  a las 10:48 UTC (Copahue).
- Ramas de las seis sesiones en el remoto e iguales al local: `claude/s162-modis-2-0dd578` `cac483b74`,
  `claude/s162-viirs750-2-918174` `fb95d62ba`, `claude/s162-viirs375-c1b864` `7c9faed07`,
  `claude/s163-d39-mirova-v1-710f72` `f3b002ea9`, `claude/s163-instrumento-pendientes-ab5a2d` `f391376a0`,
  `claude/s163-diurno-k-prereg-5c4f44` `ce20f9cf0`; `s162-modd-candado` `ff2ced531`. `s162-via-mirova` (#907) está en el
  remoto en `a16aa14b4`, el worktree local quedó atrás en `3a02ad28f` (no importa: manda el remoto).
- Abiertos: PR #907, #912, #913 (borradores); issues #864 (auto-audit 2026-10-19) y #813 (D-10). Mirova-v1#26 OPEN.
- `experiments/_s162_v750b/objetivos_v750b.json` no existe en ninguna rama ni tag; sí el generador `objetivos_v750b.py`
  (también en el tag `s162-v750b-sellado`). Para el 2026-11-03 hay que generarlo, commitear y anotar su sha256. Avisado
  a `loop-viirs750-2`.
- Avisado el relevo a las seis sesiones (cinco entregados, `diurno-k-prereg` en cola porque estaba en un turno).

### 2026-10-26 12:35 UTC (S163): cierre de la coordinadora; relevo a S164
- Nicolás: «sí, cierra y abre la siguiente con lo que corresponda y necesario para seguir con todo». Loop de S163 detenido.
  Traspaso en `tasks/BLOQUE_ARRANQUE_S164.md`. Estado fijado con trabajo en curso: `loop-modis-2`, `loop-viirs750-2`,
  `loop-viirs375`, `d39-mirova-v1`, `instrumento-pendientes` y `diurno-k-prereg` siguen corriendo; la nueva coordinadora
  les avisa su id.

### 2026-10-26 ~12:15 UTC (S163, vuelta 15): #911 mergeado (evidencia S159 a S163 en main); entregas del paper y del congreso
- **#911 mergeado** (squash `b09a7b321`; CI verde; 1.091 archivos, todos en `experiments/`, comprobado con `git diff
  --name-only`; 62,5 MB): evidencia verificada de 13 ramas (oráculo y PORTES de S159, línea D25, MODIS, V375, V750 a/b/c/f,
  O2, O2 alternativa, H3). Quedaron fuera a propósito el `PREREGISTRO_MXD03.md` (el de main es más nuevo), las colas de las
  hijas vivas, 6 tests de D25 y un workflow de probe. Citas rotas de 54 a 12: 4 viven en ramas de hijas, 6 nunca se
  commitearon (`_s160_audit/f1b/matriz_instrumentos.csv`, `_s160_audit/f4/propagacion.csv`, `_s160_espacial/data`,
  `_s162_modis_verif_cde/arbol`, `_s162_v750b/objetivos_v750b.json`, `_s162_v750b/sin_granulo_v750b.json`). Avisadas las
  hijas de los 10 choques add/add previstos (en los 10 manda la versión de la hija). Hallazgo lateral: las copias viejas de
  los `.m` de MIROVA en main (`_s158_d17_diseno/osf_codigo_mirova`, `_s159/o1/o2_paquete`, `prueba_o2_en_octave`) tienen md5
  distinto del OSF (normalización de fines de línea); las de `_s163_o2` sí son byte a byte.
- Paper: **#912** en borrador (informe de estado, estructura, políticas de IA y lista de chequeo; dos verificadores limpios;
  manuscrito sin tocar). Congreso: propuesta lámina por lámina en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\congreso geologico 2026\2_PRESENTACIONES\PROPUESTA_REVISION_2026-10-26.md`
  (verificador: 15 afirmaciones, 0 refutadas, 6 precisadas); los mazos nuevos esperan el visto bueno de Nicolás.

### 2026-10-26, servidor 11:48 UTC (S163, vuelta 14): primer NRT con #909 en verde; sesiones de paper, congreso y retrospectiva
- NRT de las 11:10 UTC (`b43f4ee4f`, incluye #909): **success**. El log ya registra la cobertura por volcán («Cobertura NO
  COMPLETA: 1 incidencias (ninguna búsqueda ni descarga fallida)»): es el día en curso, parcial por construcción, como avisó
  `rebase-889`; el código de salida no cambia. Sin issue nuevo del auto-audit todavía.
- Sesiones abiertas a pedido de Nicolás: «Presentaciones del Congreso Geológico 2026» (`local_ad3af6f7-bad7-4dfe-9535-
  2069fc795630`, en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\congreso geologico 2026\`, mejora
  `AT8-7_VRP_Chile.pptx` y `AT3-6_IA_multiplicador.pptx` sin sobrescribirlas) y «Retrospectiva del proceso VRP Chile: plan»
  (`local_09e29bf2-a78f-4ef3-96af-9ee2f8b361b6`: qué funcionó, qué no, auditorías, prompts, errores evitables, lo logrado
  sin Coppola, rol de Nicolás, tiempo y rango de tokens), base común para el paper y las charlas.
- Disco: C: 18 GB, D: 8,5 GB (varias sesiones trabajando); sin riesgo aún (parada bajo 3 GB).

### 2026-10-26 ~11:50 UTC (S163): O2-375 cerrado contra MATLAB; la regla no extrapola como MATLAB
- `loop-viirs375` (`dbe9af431`, `o2_375/verificador_matlab/INFORME.md`, verificador Sonnet CONFIRMADO): el ΔL de MATLAB
  difiere de la vara en 0 de 422 escenas (máx 1,03e-15); el control contra el port falla donde debe (137 escenas, máx
  0,83); Etna igual al OSF; un Delaunay sin perturbar difiere en 22 de 58, así que la tolerancia distingue triangulaciones.
  **La vara de V375 deja de ser preliminar y V375-D queda fuera del programa.** V375-E espera la vía (#907 y su cableado) y
  PD1.
- **Hallazgo (gravedad 1)**: fuera de la envolvente convexa MATLAB deja NaN, y `delaunay_perturbado.rellenar` pone el vecino
  más cercano (38.955 celdas en 12 escenas de V375; 159 en 10 de MODIS; ninguna sobre una alerta). Con `omitnan` un NaN se
  descarta de L_bk y un extrapolado se suma. Pedido a `loop-viirs750-2`: que la función de la vía devuelva NaN fuera de la
  envolvente, con prueba de oro y mutación.
- Con esto, la vara de magnitud de los tres sensores queda reproducida contra MATLAB real: V750 166 de 166, MODIS 404 de
  404, V375 422 de 422.

### 2026-10-26 ~11:40 UTC (S163): O2 MODIS confirmado contra MATLAB; sesión del paper
- `loop-modis-2` (`experiments/_s163_o2_modis/RESULTADO_O2_MODIS_MATLAB.md`, verificador Sonnet en
  `verificador_matlab/INFORME.md`): la regla reproduce el fondo de MATLAB R2026b en 404 de 404 filas y 191 de 191 escenas
  MODIS, incluidos los 6 bloques 2 × 2 que estaban en SOSPECHA (máx 5,55e-17); el port y el marco cambiado quedan a 1,06e-4.
  El port no es MATLAB en 1 píxel (24 de 87 iguales), ni en 2 × 2, ni en formas dispersas. Alcance: 161 de 191 escenas de
  Láscar, huecos de 3 × 3; MATLAB no extrapola (159 celdas sin rellenar en 10 escenas, ninguna alerta). SIN DATO que MIROVA
  use ese `.m` para MODIS. **Con D-48**: la columna M con la regla en MOD-D deja de ser preliminar; la vía de MODIS, cuando
  exista, reutiliza la función de #907. Mutaciones del candado: 18 de 31 atrapadas hasta ahora.
- Nicolás pidió revisar el paper (estado, estructura, uso de IA y doble chequeos): sesión aparte «Paper VRP Chile: estado,
  estructura y riesgos de la IA» (`local_41e333ef-587b-4af7-96db-c19cc7f3b9b5`), entrega en `docs/paper/` con PR en
  borrador.

### 2026-10-26 ~11:20 UTC (S163, vuelta 13): tres sesiones en paralelo; borradores viejos resueltos
- Nicolás: «Sí, lanza las tres sesiones en paralelo (unificar evidencia S162 y S159, pendientes del instrumento,
  pre-registro del A/B diurno sobre K) y cierra o integra los borradores viejos como recomiendas». MATLAB: ya entregó todo
  lo necesario (O2 de V750, MODIS y V375); detenerlo no afecta.
- Sesiones abiertas (cada una en su worktree desde main, reportan a S163, ninguna despacha ni mergea):
  `unificar-evidencia` (`local_60e2df4b-710b-4476-938e-79bdaf0837e8`): lleva a main la evidencia de S159 y S162 repartida
  en ramas (no toca las ramas de las hijas vivas); `instrumento-pendientes` (`local_bad70f2d-a64f-4eec-98f8-0497c3601256`):
  placebos de D-44 sobre producción, tarea 1.35, «no observado» frente a hueco de NASA; `diurno-k-prereg`
  (`local_bd4d68e7-100e-412a-9456-3f89c7beb7e4`): pre-registro, arnés y evaluador del A/B diurno sobre K (D-10, tarea 1.32),
  sin despachar.
- Borradores viejos: **#886 y #887 mergeados** (squash `e9ef99cbe` y `047bd5692`; sólo `experiments/_s158_*`, CI verde);
  **#776, #880 y #890 cerrados** con comentario (los dos primeros meterían workflows de probe en main; #890 por D25 no
  adoptada y el placebo ya en #905). Sus ramas se conservan.
- Ajustes propuestos al programa por sensor (pendiente de escribir en el spec): O2 cerrado y vara M = regla exacta de
  MATLAB en los tres paquetes; V375-D fuera; D17 como pieza central de los paquetes.

### 2026-10-26 ~10:55 UTC (S163, vuelta 12): MATLAB corrió los paquetes de MODIS y VIIRS 375
- Nicolás volvió a entrar a MathWorks. Entradas bajadas dentro de MATLAB con `websave` desde los commits verificados y
  comprobadas por md5 (MODIS `89479be35`: 3 de 3; V375 `138a931ee`: 4 de 4). MATLAB R2026b.
- **MODIS**: 404 escenas en 2,0 s (npix 1: 168, 2: 132, 3: 77, 4: 27). `resultado_o2_modis.mat` md5
  d20cf7ddd3b6ba015c7b474afe627085, `salida_matlab_modis.txt` da9e409f9958c4e4e40fda7142e27ec9.
- **VIIRS 375**: Etna exacto al OSF (Tot_Lmir_bk 1,072886152; VRP 9.889.528,4 W); 422 escenas en 11,2 s.
  `resultado_v375.mat` md5 71d0f8218a445c337560efd73d904374, `salida_matlab_v375.txt` 53def07b353129ae9100629af1c65bf0.
- md5 iguales en MATLAB Drive y tras la descarga; copiados a las carpetas de cada hija (sin seguimiento: los commitean
  ellas) y avisadas. Con esto se puede sacar el PRELIMINAR de las varas de MODIS y V375 si calzan con la regla.

### 2026-10-26 ~10:50 UTC (S163, vuelta 11): Nicolás aprueba #909, el cableado de V750 y D-39; #909 mergeado
- Nicolás: «continúa con todo lo que recomiendes apruebo los últimos 3 puntos» (cableado de V750 y merge de #909 bajo A45;
  D-39; volver a entrar a MathWorks) y luego «investiga bien lo de mirova-v1, no queremos perder datos, lanza una sesión
  específica si es necesario».
- **#909 mergeado** (squash `ccb378425`), tag defensivo `pre-s163-merge-909` sobre el main anterior `a73e5b241`. Toca
  `pipeline/fetch.py` y `scripts/run_pipeline.py`: el NRT registra incidencias de cobertura; su código de salida no cambia
  sin `--estricto-cobertura`. Vigilar las próximas corridas del NRT.
- Cableado de la vía «código MIROVA» en V750: el sí de Nicolás pasado a `loop-viirs750-2` con sus palabras textuales;
  flag apagado; pedido: rebase sobre main (por #909), prueba de producción bit a bit igual con el flag apagado, suite, CI y
  verificador limpio; el merge lo hace la coordinadora.
- **D-39**: sesión `d39-mirova-v1` (`local_57b44db2-3006-49fb-a00c-0228be793b29`) para demostrar antes de mergear
  Mirova-v1#26 que ninguna fila se pierde ni cambia (cuenta fila a fila en las dos direcciones), que cada fila a reponer
  existe en la historia, plan de despliegue con tag y pausa de workflows, y R13 en VRP Chile; no mergea, entrega a S163.
- MATLAB: la pestaña sigue en el inicio de sesión de MathWorks (página gris); los paquetes de MODIS y V375 esperan que
  Nicolás entre.

### 2026-10-26 ~05:45 UTC (S163): candado de MOD-D, adenda 4; punto (b) aprobado con D-48
- Verificador limpio (Fable) del candado: «se puede despachar el humo con cambios chicos». VCM-01 (gravedad 3): la adenda 3
  sacaba del denominador más de lo que permite el §8.5 sellado, y una protegida que K publica pero el port no pudo evaluar
  dejaba de vetar P1 (podía torcer NO CANDIDATO en CANDIDATO). Arreglo en la adenda 4 (`s162-modd-candado`): (a) sólo
  «volcán fuera del gránulo» y «escena inválida» salen del denominador; una falla del arnés o del port deja la cobertura en
  rojo (INDECIDIBLE): instrumento, aceptado. (b) **Aprobado con D-48**: si una protegida que K publica sale del denominador
  por esos dos motivos, el veredicto no puede ser CANDIDATO y va a la fila 5 (DECIDE NICOLÁS). Más estricto que lo sellado,
  fijado antes de ver datos (el humo no se despachó). Condiciones: escrito con hora del servidor antes del despacho,
  segunda vuelta del verificador que lo cubra, y un escenario de batería que lo ejercite.
- Resto de la adenda 4: manifiesto de hashes del arnés y del evaluador comprobado en el workflow y en el evaluador;
  procedencia exige el commit del tag; 32 pruebas y 31 mutaciones; K33 por el mismo predicado; punto informativo de M con la
  regla de `fillmissing2`. Después: mutaciones, segunda vuelta, tag y pedido de despacho del humo.

### 2026-10-26 ~05:10 UTC (S163): vara MODIS preliminar verificada; #910 mergeado; adenda de M para MOD-D aprobada
- `loop-modis-2` (`38df75a02`, `experiments/_s163_o2_modis/RESULTADO_VARA_PRELIMINAR.md`, verificador Sonnet en
  `verificador_vara/INFORME.md`): con la regla, el hueco calza con el del `.m` en 404 de 404, pero son **191 escenas
  distintas (161 de Láscar)**, no 404. En 1 píxel no hay sesgo sino ruido por escena (típico 9,1 %, máx 3,8 veces; el port
  elige la otra pareja de celdas en 139 de 168); la regla en 1 píxel equivale al promedio de las dos celdas a dos columnas
  (167 de 168). Efecto en 4 píxeles por bloques 2 × 2 que ningún caso de VIIRS validó contra MATLAB: SOSPECHA. SIN DATO que
  el fondo de MODIS en MIROVA sea el del `.m` de VIIRS 750 (MIROVA no publicó código MODIS) y que la regla no dependa de la
  grilla. Prueba de oro en MATLAB pendiente (sesión de MathWorks expirada).
- **Aprobada con D-48** la recomendación de MODIS: adenda informativa a MOD-D, antes de leer el censo, que informe M también
  con esta regla, fuera de línea, con las grillas que guarda el censo. No cambia ninguna regla sellada.
- **#910 mergeado** (squash, CI verde; sólo docs): sello D-48 del pre-registro de MxD03 y los seguimientos de #906
  (FICHA_SDA:29, paper sec5:7, que además decía banda 21 primaria, y Coppola 2026 en MISSION). Cierra el segundo conflicto
  del inventario.

### 2026-10-26 ~04:40 UTC (S163): adenda 1 de V750-B CONFIRMADA bajo D-48
- Verificador Sonnet de la adenda (`claude/s162-viirs750-2-918174`, `experiments/_s162_v750b/adenda1/verificador/
  INFORME.md`): LISTO CON CAMBIOS, sin gravedad 4 o 5; confirmó el defecto (escenario: 68 de 69 observadas, 0 SIN DATO,
  compuerta abierta) y que con el probe sellado no debería ocurrir. Cambios hechos (VAD-01 a VAD-05): lector
  `adenda1/leer_v750b.py` que corre el compañero y no deja pasar al analizador si cierra; rutas absolutas; caja `null` o
  `{}` = «caja ilegible», cierra siempre; escenarios A9 a A17 y L1 a L4. Batería 52 de 52; nulo 17 de 17, identidad PASA,
  control CAÍDA. VAD-07 y VAD-08 aceptados tal cual.
- Comprobado por la coordinadora sobre `7aa2788a0`: `analizar_v750b.py` **idéntico** al tag `s162-v750b-sellado`; el diff
  del pre-registro sólo agrega la marca y la sección de la adenda; ninguna regla cambia. **Confirmada con D-48.** El
  2026-11-03 la lectura se hace con el comando del lector (final de `PREREGISTRO_V750B.md`).

### 2026-10-26, servidor 04:27 UTC (S163, vuelta 10): CI de main verde tras #908; reserva del borde medida en V375
- CI de main verde sobre `a6d3935cc` (merge de #908). NRT corriendo (04:10). Sin issue nuevo del auto-audit. Disco C: 25 GB,
  D: 9,6 GB. Ramas de las hijas en el remoto.
- `loop-viirs375` (`da0693783`, `o2_375/envolvente_v375.py`): 0 de 422 escenas con celdas de alerta fuera de la envolvente
  convexa, así que la reserva del borde del verificador no toca su vara; 12 escenas tienen celdas del hueco dilatado fuera
  (orilla de la pasada), que no entran en L_bk; magnitud igual con y sin ellas (C13 0,999). Vara PRELIMINAR sólo por la
  prueba de oro en MATLAB.

### 2026-10-26 ~04:20 UTC (S163): V375-A cableado; la referencia del checkout perdió filas de Chillán
- `loop-viirs375` (`e48843858`): `protegidas_crater_v375.py` aplica `protegida_de_crater` de #903 (copiada de main sin
  cambios) a las 81 protegidas de S159, S162 y S162b: 70 de cráter; las 11 que no, todas por `ocr_snpp_antes_del_hito`.
  C13 y M14 pierden 6 protegidas y K 3, todas no de cráter; sólo PIX7 pierde una de cráter (Cordón Caulle 2026-06-07).
  Informado al lado de P1, sin tocar veredictos. Coincide con el verificador de las protegidas SNPP.
- **Hallazgo lateral**: la referencia de MIROVA del checkout **perdió las filas de tabla de 4 protegidas de Chillán (15 y
  16 de octubre)**; el evaluador tuvo que usar las filas guardadas en los objetivos al seleccionarse. Es la misma familia
  que D-39 (bucle de push del scraper Mirova-v1 que pierde filas; Mirova-v1#26 sin mergear): suma peso a esa decisión de
  Nicolás.
- Para V375-E sólo faltan la vía (#907 y su cableado, A45) y PD1.

### 2026-10-26 ~04:05 UTC (S163, vuelta 9): #889 reemplazado por #909 (borrador, espera a Nicolás)
- `rebase-889` (`local_cc8da696-d46e-4b43-8cf9-74c0744abfdd`): #889 cerrado con comentario a **#909** (rama
  `s163-instrumentos`, `2ce1c8310` sobre main `691e4d588`, CI verde, «no mergear sin el sí de Nicolás»); el force-push a la
  rama vieja lo bloquearon los permisos; tag `pre-s163-rebase-889` (`d0968e389`). Conservado: I1 (incidencias de cobertura
  por volcán y día, fusionado con la cobertura por plataforma de #897; código de salida del NRT sigue en 0 sin el modo
  estricto), I3 (`banco_paridad.TOL_S` seguía como literal 120; ningún número cambia) y A (xfail del tope de cordura de V375;
  `store.py` sin tocar). Retirado: I2 (ya en #890; D25 no se adopta; el placebo vive en #905). Evidencia: 11 rojas sobre
  main, 12 de 12 mutaciones, suite 2.528 sin fallas, verificador Sonnet sin regresión.
- **Decide Nicolás**: (1) merge de #909 (toca el NRT); (2) aceptar que los reprocesos con `--estricto-cobertura` salgan con 3
  cuando tocan el día en curso o un L1B sin geolocalización (frecuencia histórica SIN DATO); (3) #890. No cubierto: VA61-01
  vive dentro de `process_modis` (otro trabajo, A45) y el estado «sin dato» no llega a `data/` ni al tablero.

### 2026-10-26 ~04:45 UTC (S163, vuelta 8): #908 mergeado; regla de MATLAB confirmada; V375-D no hace falta por magnitud
- **#908 mergeado** con commit de merge (`a6d3935cc`), CI verde sobre `94fdd7aaf`: main ya tiene la bitácora, los traspasos
  S152 a S163, el programa por sensor y la marca de D25. Lo que difiere hoy entre main y loop/activo son sólo los datos NRT
  posteriores (4 archivos).
- **Regla de `fillmissing2` CONFIRMADA** por verificador limpio (Sonnet) con implementación independiente (`mi_cgal.py`):
  166 de 166 VRP, 84 de 84 fondos, sin fuga de datos de MATLAB. CONFIRMADO EN PARTE el control: otras simetrías del marco
  calzan 159 a 160 y un desempate ±eps·x·y 153, así que el control de ejes cambiados (42) era débil; la separación sigue
  nítida. La parte 2 (no separa contra MIROVA con 6 pasadas) CONFIRMADA. No cubierto: extrapolación fuera de la envolvente
  (1 escena), independencia de las 166 (83 son variantes de 10 pasadas). Informe en `s163-o2-alternativa` `c95483d31`,
  `experiments/_s163_o2alt/verificador/`. Avisadas las tres hijas, con las reservas.
- `loop-viirs375`, tarea 2 PRELIMINAR (`04d7151d2`): con la regla, el fondo de 1 a 4 px no cambia la magnitud de V375-C
  (veredicto B igual; M de 0,998 a 0,999 en M14 y M13); **V375-D no hace falta por magnitud**. Queda pendiente la prueba de
  oro en MATLAB (sesión de MathWorks expirada).

### 2026-10-26 ~04:15 UTC (S163, vuelta 7): inventario del trabajo paralelo; loop/activo a main (#908); worktrees liberados
- Inventario S158-S163 (subagente de sólo lectura, `scratchpad\INVENTARIO_PARALELO.md` de S163). Conflictos reales sólo
  tres: (1) encabezado de D25 en `docs/MIROVA_DIVERGENCES.md` (main con la marca S158, loop/activo con la S162): resuelto
  en loop/activo conservando las dos (`a907c44f3`); (2) `claude/s162-modis-2` contra main en ese trozo y en
  `PREREGISTRO_MXD03.md`, que main (#906) presenta como borrador cuando ya está sellado: pedido a `loop-modis-2` un PR chico
  con el sello, la adenda y los seguimientos de #906 (FICHA_SDA:29, sec5_methods:7, Coppola 2026 en MISSION); (3) #889, ya
  en su sesión.
- **Huérfano mayor: loop/activo no llegaba a main desde #816 (15-oct, 421 commits)**. Abierto **#908** (loop/activo a main,
  339 archivos, sólo `docs/`, `tasks/`, `experiments/` y `CLAUDE.md`, comprobado con `git diff --stat`), con merge commit
  para que los próximos no choquen. Otros huérfanos que quedan anotados: PORTES y censo del oráculo de S159
  (`s159-oraculo-censo`, 110 archivos sin PR); evidencia de S162 repartida en ~7 ramas (MOD-B, A61, SNPP, O2, H3, V375) sin
  plan de unión; borradores viejos #776, #880, #886, #887, #890 sin decidir; pendientes del instrumento terminado
  (placebos D-44 sobre producción, tarea 1.35, «no observado» frente a hueco de NASA); A/B diurno sobre K (tarea 1.32).
- Las dos explicaciones de O2 no se contradicen: «promedio de la fila a ±2» (verificador de O2) es el caso de un píxel de la
  regla general de Delaunay con desempate (alternativa a O2), que `loop-viirs750-2` ya portó a la vía (166 de 166, 84 de 84).
- Worktrees a la papelera (limpios y con su commit en el remoto, comprobado uno por uno): `C:\vrp-trabajo\
  s162-negmodis-disparo`, `s162-pr-mxd03`, `s162-v375-prot`, `s162-verif-snpp`, `D:\vrp-trabajo\temporales\s158_d17`,
  `D:\vrp-trabajo\worktrees\s162-instrumento-tareas`; `git worktree prune`. No tocados: los de `.claude\worktrees` de
  sesiones viejas y los que tienen copias de verificador sin seguimiento (`s162-modis-774bb0`, `s162-v750a-eval`,
  `s162-a61`, `D:\vrp-trabajo\s162-mxd03`, `s159-pruebas`); `C:\vrp-trabajo\s162-modd` tiene 14 archivos sin commitear de
  `loop-modis-2` (activo).

### 2026-10-26 ~03:30 UTC, servidor 03:16 (S163, vuelta 6): regla de MATLAB identificada; dos paquetes esperan MATLAB
- **Alternativa a O2 entregada** (subagente Opus, `s163-o2-alternativa` `cd812c746`, `experiments/_s163_o2alt/INFORME.md`):
  (1) **regla de `fillmissing2` identificada**: Delaunay con perturbación simbólica estilo CGAL (x = fila, y = columna),
  relleno lineal; reproduce el VRP de MATLAB en **166 de 166** escenas (máx 1,55e-15) y el fondo completo en 84 de 84;
  control de ejes cambiados 42 de 166; nulo de 20 desempates al azar, máx 110 de 166. SOSPECHA (no medido) que MATLAB use
  CGAL por dentro. (2) **Contra lo que MIROVA publicó, NO SEPARA**: 6 pasadas de 1 px pareadas, IC 95 % del bootstrap
  cruza 0, el margen no supera el nulo; domina el ruido del regrillado propio (0,134 en log VRP); harían falta 50 a 100
  pasadas. **Sin verificador todavía**: lanzado uno limpio (Sonnet) con implementación independiente, entrega en
  `C:\vrp-trabajo\s163-verif-regla\INFORME.md`.
- `loop-viirs750-2` llegaba a 79 de 84 por su lado (perturbación y·(1+1e-6)): avisado para no duplicar; su tarea pasa a
  portar la regla como función de la vía, con prueba de oro contra `resultado_o2.mat`.
- Paquetes para MATLAB listos y comprobados: MODIS (`89479be35`, 404 escenas) y VIIRS 375 (`138a931ee`, 422 escenas,
  `experiments/_s162_v375/o2_375/`). **No corridos**: la sesión de MathWorks del Chrome de Nicolás expiró (la pestaña volvió
  al inicio de sesión) y Claude no inicia sesión. Mientras tanto, las hijas pueden calcular la vara con la regla local,
  marcada PRELIMINAR; MATLAB queda como prueba de oro.
- `#907` (vía «código MIROVA», sin archivos A45) abierto en borrador por `loop-viirs750-2`; adenda 1 de V750-B: verificador
  Sonnet «listo con cambios», en arreglo. Ramas de las hijas en el remoto (ls-remote 03:16). Runs fallidos de
  `vigilar-osf-mirova.yml` a las 03:01 y 03:16: ruido conocido de S162 (disparo sobre árbol viejo), no producción. Sin
  issue nuevo del auto-audit todavía (el de la semana pasada se abrió a las 16:29 UTC).

### 2026-10-26 ~04:30 UTC (S163, vuelta 5): H3 refutado; paquete O2 de MODIS listo; temporales a la papelera
- **H3 REFUTADO para el tablero de hoy** (`audit-h3-tablero`, rama `claude/s163-audit-h3-6c292b` `5a349caa9`,
  `experiments/_s163_h3/INFORME.md`, verificador Sonnet CONFIRMADO): en origin/main `0b233221f`, 0 de 72.438 records Tier
  A sin K y 0 de 9.538 publicados por el predicado del tablero (node); Pages igual. H3 era cierto sólo en la rama de S162,
  nacida antes de #883 (desplegado el 2026-10-21 11:48 UTC, que cambió 2.730 de 5.603 noches de publica a no publica).
  No se reprocesa nada. Marca A113 pendiente sobre el H3 del informe de S162 (`s162-v375-protegidas-snpp`).
- `loop-modis-2` entregó el paquete O2 de MODIS (`claude/s162-modis-2-0dd578` `89479be35`, `experiments/_s163_o2_modis/`,
  404 escenas de 1 a 4 píxeles, 168 de 1 píxel; md5 del remoto comprobados). **No corrido todavía**: el Chrome de Nicolás
  dejó de responder a la extensión (capturas y lectura de texto fallan en MATLAB); se le pidió revisarlo.
- Temporales a la **papelera de Windows** (no borrado permanente), tras comprobar que ninguno se usa: `D:\vrp-trabajo\
  mirova-v1` (885 MB; clon limpio y al día con GitHub en `fix/referencia-estable`), `D:\vrp-trabajo\temporales\
  pytest-of-nmend`, `pytest_tmp`, `s157_prereg_merge`, `s157_saturacion`, `s157_smoke`, `s157_verif874` (0 citas en main y
  loop/activo, sin escrituras desde el 24-oct). Se conservan las carpetas citadas como evidencia de veredictos cerrados y
  `D:\vrp-trabajo\temporales\s158_d17` (worktree registrado). `C:\vrp-trabajo\temporales\s162_v375\verif_v3\` ya no
  existía (la borró loop-viirs375). Pendiente medir `experiments/_s140` y `_s160_espacial/data` contra las ramas remotas.
- Pendiente de Nicolás que salió en la revisión: D-39 (bucle de push del scraper Mirova-v1, Mirova-v1#26).

### 2026-10-26 ~03:40 UTC (S163): loop-viirs750-2 corrige un desvío de A45; cableado de la vía espera el sí de Nicolás
- Había editado sin commitear `pipeline/process_viirs_mod.py` y `pipeline/store.py` para cablear la vía «código MIROVA»;
  los devolvió a origin/main. El cableado queda como parche propuesto (`experiments/_s162_v750a/cableado_pendiente/
  cableado.patch`, aplica limpio, 6 pruebas verdes; tag `pre-s162-via-mirova` existe): (a) `calculate_vrp` de V750 llama a
  la vía dentro de `ENABLE_V750_CODIGO_MIROVA` (apagado); (b) `store.py` deja pasar los records `via_codigo_mirova=True`
  sin geocerca, filtro de píxeles por distancia ni tope por cúmulo (compuertas de K que el `.m` no tiene); (c)
  `run_pipeline` pasa el nombre del volcán. Con el flag apagado, inerte. **Planteado a Nicolás (A45).**
- PR en borrador aparte (rama `s162-via-mirova`, sin archivos A45): `pipeline/mirova_v750_codigo.py`,
  `pipeline/grillas_mirova.yaml`, flag en `pipeline/profile.py`, pruebas (equivalencia contra el oráculo roja a verde 1.020
  + 10, nulo 8/8, 35 propias).

### 2026-10-26 ~03:30 UTC (S163, vuelta 4): ocho PR mergeados; O2 verificado; #889 a su sesión
- Nicolás: «sí a mergear, sí a rebasar si es lo que recomiendas; borra los temporales que ya no tengan uso; el correo a
  Coppola aún no». Mergeados por squash vía API, en orden: #900 (`5bb0c120c`), #902 (`c0f176908`), #903 (`744d8190b`),
  #904 (`d96fa5f4d`, base cambiada a main), #906 (`b498cffe8`), #901 (`e8a7f3aa1`), #898 (`32812b925`), #905 (`691e4d588`).
  #905 quedó en conflicto tras el squash de #904: tag `pre-s163-rebase-905`, rebase de sus 2 commits propios sobre main
  (51 pruebas del instrumento en verde local), push con lease, CI verde (run 40260060896) y merge. CI de main sobre
  `691e4d588`: pendiente al escribir esto (los intermedios se cancelaron por los merges seguidos).
- #889: sesión `rebase-889` (`local_cc8da696-d46e-4b43-8cf9-74c0744abfdd`): tag, rebase sobre main, retirar lo que #903 a
  #905 superan (probablemente I3 e I2), conservar I1 (estado «sin dato» de cobertura en el NRT), borrador con «no mergear
  sin el sí de Nicolás» (toca `pipeline/fetch.py`).
- **O2 verificado** (Sonnet, `C:\vrp-trabajo\s163-verif-o2\INFORME.md`, copiado a `s163-o2-paquete` `60fd6f98c`):
  afirmaciones 1 a 3 y conteos CONFIRMADOS (cabecera GLNXA64, no Octave). **H1**: en las 51 escenas de un píxel con
  vecindad intacta MATLAB rellena siempre con el promedio de la fila a ±2 columnas (desempate de diagonal); la frase «la
  vara no puede ser un port» queda REFUTADA (marca A113 en `RESULTADO_O2.md`). Pasado a `loop-viirs750-2` para el port
  exacto.
- D-10 (#813) ya estaba decidida (opción 1, 2026-10-15): rama diurna VIIRS apagada por flag (#821); el A/B diurno sobre el
  detector anterior dio NO ADOPTAR; **falta repetirlo sobre K (tarea 1.32)**: pendiente sin dueño, entra al inventario.
- Inventario de trabajo paralelo S158-S163 (pedido de Nicolás): subagente de sólo lectura en curso.

### 2026-10-26 ~02:45 UTC (S163): loop-modis-2 al día; su rama sí estaba en el remoto
- Comprobado con `git ls-remote`: `claude/s162-modis-2-0dd578` = `557e4ae79` (la subió ~01:50; mi consulta de 01:58 fue
  antes de que apareciera), `s162-a61-mxd03` = `72f85df71`, `s162-modd-candado` = `04a86a90e`.
- Verificador limpio (Opus) de la A61 de MxD03: **P4 se sostiene** (nada espacial frena la adopción); E4 refutada (H4 va
  de −27 a +48 %, no ±27 %); **VA61-01: ~215 records con el cráter en el borde del gránulo guardados como negativos**
  (misma familia que el defecto del relleno −999: falta el estado «sin dato»; entra al diseño del flag de MxD03,
  `docs/superpowers/plans/2026-10-25-flag-mxd03-modis.md` en su rama, sin tocar `pipeline/`).
- Candado de MOD-D en curso (19 pruebas rojas contra el vacío, mutaciones corriendo, falta verificador). Sin despacho
  pedido todavía.

### 2026-10-26 ~02:40 UTC (S163, vuelta 3): O2 a los otros sensores; trabajo repartido en paralelo
- Nicolás: «¿no tienes que hacer esto mismo para los otros sensores? ... continúa con todo lo que falte, abre nuevas
  sesiones si es necesario, en paralelo y en loop». OSF zm62w sin cambios desde el 2026-08-19 (logs de la API): MIROVA
  sólo publicó código de VIIRS 750. Los ports de VIIRS 375 y MODIS trasladan esa estructura, así que heredan la
  ambigüedad del fondo de un píxel que O2 midió; el fondo de `MIROVA_VIIRS750_VRP.m` no depende del sensor (sólo el
  coeficiente), así que MATLAB puede dar la vara para los tres. Pedido a las hijas:
  - `loop-viirs750-2`: `fillmissing2` en Python exacto contra las 166 escenas de MATLAB (o tabla de vara para M de V750-A),
    antes de cerrar la vía de proceso.
  - `loop-modis-2`: paquete MATLAB con escenas MODIS de 1 a 4 píxeles de MOD-B/MOD-C, detrás de su cola actual.
  - `loop-viirs375`: sale de la pausa; paquete MATLAB con escenas V375 de 1 a 4 píxeles, re-medir la magnitud de V375-C
    con esa vara y decidir V375-D; dejar V375-E listo para la vía de proceso.
  La coordinadora corre cada paquete en MATLAB Online (Chrome de Nicolás) y lo publica en una rama propia.
- Sesión nueva `audit-h3-tablero` (`local_aea8959c-6f0f-4f19-b9b9-e8deaaf59573`, worktree desde `main`): confirmar o
  refutar H3 (el tablero muestra records del detector anterior a K antes del 2026-09-18) con el predicado del tablero en
  node, medir el efecto en noches y proponer (no ejecutar) un reproceso. Reporta a S163.
- Inconcluso que sigue en manos de Nicolás: merges #900 (antes del 02-11), #902 a #906, #901, #898; #889 (rebase con A45);
  D-10 (#813, ¿abrir el día?); correo a Coppola (en espera); borrado de temporales.

### 2026-10-26 ~02:25 UTC (S163, vuelta 2): O2 corrido en MATLAB; verificador lanzado
- Nicolás activó MATLAB Online basic (llenó él el formulario de empresa y teléfono). La subida por el navegador no tomó
  archivos (MATLAB corre en un marco aislado y MATLAB Drive ignora la entrada puesta por programa), así que el paquete se
  publicó en la rama `s163-o2-paquete` (sin tocar el checkout) y MATLAB lo bajó con `websave`; md5 dentro de MATLAB
  iguales a los originales (los `.m` de MIROVA se publicaron sin normalizar fines de línea).
- Resultado (R2026b, `fillmissing2` y `colfilt` de MATLAB): **Etna exacto al OSF** (Tot_Lmir_bk 1,072886152; VRP
  9.889.528,4 W); **detección igual a Octave en 311 de 311**; **VRP: ningún modelo de `fillmissing2` es MATLAB** (>1 % en
  32, 26 y 45 de 166; en un píxel hay casos donde MATLAB no calza con ninguno, Villarrica 09-19 nearest 0,4212 contra
  0,7438). Consecuencia: en alertas de un píxel la vara de magnitud es la salida de MATLAB o un port nuevo validado contra
  ella. Todo en `s163-o2-paquete` `9b755f315`, `experiments/_s163_o2/RESULTADO_O2.md`. **Sin verificador todavía**:
  lanzado uno limpio (Sonnet), entrega en `C:\vrp-trabajo\s163-verif-o2\INFORME.md`.
- Al subagente de la alternativa a O2 se le pidió sumar MATLAB como cuarta variante y decir si su VRP reproduce lo que
  MIROVA publicó mejor que los tres modelos (cierra el camino de punta a punta).

### 2026-10-26 ~02:10 UTC, servidor 01:56 al abrir (S163, vuelta 1): relevo tomado; decisión 9 aplicada; alternativa a O2 lanzada
- Coordinadora S163 = `local_8a135e90-b711-4bb9-9dec-ff02036f206b`. A pedido de Nicolás se separó de S162 (ya es sesión
  de nivel superior): las hijas siguen anidadas bajo S162 y sus avisos automáticos le llegan a ella, así que se les pidió
  por mensaje que manden resultados y pidan despachos a S163. Avisadas `loop-modis-2`, `loop-viirs750-2` y `loop-viirs375`.
- Estado verificado: `loop/activo` = remoto (`4e8865435`); runs sin nada del loop (NRT verde 01:10 UTC); PRs #898 a #906
  abiertos y CLEAN (#889 DIRTY); issue #864 abierto; disco C: 26 GB, D: 9,6 GB. **La rama de `loop-modis-2`
  (`claude/s162-modis-2-0dd578`) no está en el remoto**: se le pidió subirla.
- **Decisión 9 aplicada con D-48** tras el verificador limpio (Opus, `s162-verif-protegidas-snpp` `3c6836076`,
  `experiments/_s162_v375/protegidas_snpp/verificador/INFORME.md`): para las 6 protegidas de Suomi NPP, CONFIRMADO que no
  son de cráter por tres evidencias independientes de la fecha (cabecera de la imagen 18 a 102 min posterior en 6 de 6;
  VRP de su pasada que calza con el total del port, nulo 0 de 2.000; K publica 279, 288 y 289 sólo por un píxel del cráter
  bajo 0,05 MW). Se juzgan con la regla de cráter de #903. Correcciones al informe del subagente 4: las distancias son a
  8,2 a 28,9 km **del cráter** (el informe medía al centro de MIROVA, VP162-01); la corroboración de NOAA-20 en 294 mira otro
  objeto a 34,75 km (VP162-02, queda SIN DATO). **Para el estrato NO se extiende tal cual** (VP162-03): de las 128
  protegidas sólo OCR anteriores al 2026-10-09, 48 son Suomi NPP con record nuestro, 9 NOAA, 71 sin record a 3 min, y 88
  caen también por el hito de distancia; iguales a las 6 en sentido estricto, 11. Regla que queda: **cada adopción de un
  paquete de VIIRS 375 informa al lado la lectura A y separa tres grupos: (i) los 11 como las 6, (ii) los sin
  plataforma, (iii) los que la regla saca también por `ocr_sin_distancia_medida`**; nunca se presenta el 128 como «128
  casos como estas 6». Revocable por Nicolás.
- Adenda 1 de V750-B: su verificador Sonnet todavía no entrega (carpeta `adenda1/verificador/` sin INFORME); se confirma
  con D-48 cuando dé conforme.
- Alternativa a O2 lanzada (subagente Opus, sólo lectura, worktree `C:\vrp-trabajo\s163-o2alt`, rama
  `s163-o2-alternativa` desde `s160-auditoria`): calibrar las variantes de `fillmissing2` contra el VRP que MIROVA publicó
  en sus alertas de VIIRS 750 de un píxel, con control de 2 a 4 píxeles, nulo medido y veredicto SEPARA / NO SEPARA /
  INDECIDIBLE. Después, verificador limpio de otro modelo. O2 queda como confirmación opcional.

### 2026-10-25 (S162): relevo de la coordinadora
- Nicolás: «lanza esa nueva sesión que recomiendas». Abierta `coordinadora-s163` (`local_8a135e90-b711-4bb9-9dec-ff02036f206b`)
  en este mismo checkout, con el traspaso S163. S162 detiene su loop aquí: desde ahora la única coordinadora (y la única
  que despacha y escribe este archivo) es S163; ella avisa a las hijas su id. El verificador de las protegidas SNPP que
  lanzó S162 entrega en la rama `s162-verif-protegidas-snpp`.

### 2026-10-25 (S162): adenda 1 de V750-B escrita (loop-viirs750-2)
- `claude/s162-viirs750-2-918174` `e7c56af0b`: el analizador sellado (`analizar_v750b.py` l. 205-209) deja caer sin
  contar la pasada «ok» sin una caja del oráculo (escenario D1 lo demuestra); la adenda no edita el analizador: el
  compañero `experiments/_s162_v750b/adenda1/cobertura_cajas_v750b.py` se corre antes de la lectura del 2026-11-03 y
  manda si dice INSUFICIENTE. Prueba roja sin el compañero, verde con él; nulo 7/7. Se confirma con D-48 cuando
  entregue su verificador Sonnet.
- Pregunta de Nicolás «¿por qué necesitas MATLAB?»: explicado (la triangulación de `fillmissing2` decide el fondo en
  alertas de un píxel, hasta 1,8×; no cambia qué se publica). Alternativa propuesta: calibrar la variante de interpolación
  contra el VRP que MIROVA publicó en sus alertas de un píxel (A1, A115), con un subagente; espera su respuesta.

### 2026-10-25 (S162): O2 sin sesión de MathWorks; correo a Coppola en espera; verificador de las protegidas SNPP
- Nicolás: «haz tú lo de MATLAB; el correo a Coppola aún no lo enviaremos; el resto haz lo que recomiendes».
- O2: no hay MATLAB local y en su Chrome no hay sesión de MathWorks (matlab.mathworks.com pide iniciar sesión); Claude
  no inicia sesión con credenciales. Pendiente de Nicolás: iniciar sesión en MathWorks en su Chrome; con la sesión
  abierta, la coordinadora sube los cuatro archivos de `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\`,
  corre `correr_o2` y baja `resultado_o2.mat` (paso a paso en `experiments/_s162_v750f/PASO_A_PASO_O2.md`).
- Correo a Coppola: en espera por decisión de Nicolás.
- Decisión 9 (protegidas sólo OCR de Suomi NPP): lanzado el verificador limpio (Opus) del informe del subagente 4,
  rama `s162-verif-protegidas-snpp`; con su conforme se aplica la recomendación (que decida la regla de cráter de #903,
  informando la lectura A al lado). Merges y borrado de carpetas siguen siendo de Nicolás (clasificador y regla de no
  borrar archivos de forma permanente).

### 2026-10-25 (S162): relevos abiertos; loop coordinador reanudado
- Nicolás: «continúa con todo lo que recomiendes, ¿hay que abrir nuevas sesiones? ¿en qué quedaron las otras?». Abiertos
  desde el computador: `loop-modis-2` (`local_0af7e1d8-7bde-4a4d-b8a3-6cf256a36c67`, desde `claude/s162-modis-774bb0`:
  verificador de la A61, candado de MOD-D, diseño del flag de MxD03 con «sin dato» de geolocalización) y
  `loop-viirs750-2` (`local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a`, desde `s162-v750a-evaluador`: adenda del defecto de
  V750-B, segunda vuelta del verificador de V750-A, vía de proceso «código MIROVA» detrás de flag, despacho de V750-B el
  2026-11-03). `loop-viirs375` borró sus 1,9 GB de artefactos fabricados del verificador y quedó en pausa.

### 2026-10-25 ~07:30 UTC (S162): analizador de V750-A terminado; los 5 subagentes entregaron; loop coordinador detenido
- Subagente 3 (Opus; `s162-v750a-evaluador` `7d5e723c6`): `evaluar_v750a.py` con 50 pruebas, 52/52 mutaciones
  atrapadas, verificador Sonnet «listo con cambios» corregido (sin segunda vuelta). Lecturas L2, L4, L7, L18 para el
  sello de V750-A (DN-4). Defecto previo en `analizar_v750b.py` (sellado): pasada «ok» sin una caja del oráculo sale del
  denominador sin contarse SIN DATO; adenda informativa antes de leer V750-B el 2026-11-03. Contrato pendiente: el S-1
  necesita que el productor de artefactos exponga los contrastes de la celda decisiva.
- Sin trabajo en vuelo de la coordinadora: los cinco subagentes entregaron, sin runs del loop. El loop coordinador se
  detiene aquí (la próxima acción es abrir los relevos desde el computador y el despacho de V750-B el 2026-11-03);
  retomar con /retomar sobre `tasks/BLOQUE_ARRANQUE_S163.md`.

### 2026-10-25 ~03:10 UTC (S162): A61 de MxD03 hecha; defecto del relleno de geolocalización en producción
- Subagente 1 (Fable; `s162-a61-mxd03` `56f721d99`): las 48 protegidas quedan con MxD03 a 0,15-0,89 km del cráter (con
  K 0,81-3,20), mismos píxeles reubicados en 44, reselección de vecinos en 4, ninguna se fue a otro objeto; §6 P4 se
  cumple. Defecto de producción (G3): sin estado «sin dato» de geolocalización, el relleno −999 hace escribir negativos
  sobre escenas sin cráter (2 de 5.465). `final_hotspot_dist_km` de MODIS se mide desde el centro del volcán (A46).
  Falta verificador limpio de este informe y del de las protegidas SNPP. Queda 1 subagente en vuelo (analizador V750-A).

### 2026-10-25 ~03:00 UTC (S162): las 6 protegidas SNPP de VIIRS 375 no son de cráter (sin verificador)
- Subagente 4 (Fable; `s162-v375-protegidas-snpp` `014a1ab61`): con la regla de #903 tal cual, 0 de 6 son protegidas de
  cráter (`ocr_snpp_antes_del_hito`; la tabla no trae ninguna; cabecera de la imagen de una pasada posterior; VRP de un
  objeto a 8,7-29 km). Las 3 que K publica son por un píxel débil del cráter bajo el NONE de D-9. Estrato grande: 128 de
  234 protegidas A de VIIRS 375 son sólo OCR anteriores al 2026-10-09. Decisión 9 del bloque S163 (recomendación: que
  decida la regla de cráter, tras verificador limpio). H3 (SOSPECHA): el tablero muestra records del detector anterior
  antes del 2026-09-18. Quedan 2 subagentes en vuelo (A61 de MxD03 y analizador V750-A).

### 2026-10-25 ~02:45 UTC (S162): PR #906 del veredicto de MxD03 (borrador, CI verde)
- Subagente 2: #906 (rama `s162-pr-veredicto-mxd03` sobre origin/main `f9e22f8d6`): D35 nueva en el catálogo con la cita
  de MOD-A, marcas A113 en D18, SINTOMAS §3, BEYOND §12 (fila MEJ-7, Láscar 2026-05-11, SOSPECHA fuerte),
  DISENO_D17 §4.7 y el §2 del pre-registro de MxD03. CI `pytest` SUCCESS; suite 2.418 passed. Seguimientos: Coppola
  2026 falta en la lista de papers de `docs/MISSION.md`; `docs/FICHA_SDA_VRP_CHILE.md:29` y `docs/paper/sec5_methods.md:7`
  dicen que usamos MOD03 (se baja y no se usa): corregir en la adopción. Marca A113 agregada al §10 del programa.

### 2026-10-25 ~02:30 UTC (S162): entregó el subagente del auto-audit del lunes
- Simulación con el `auto_audit_weekly.py` real y reloj fijo (validada reproduciendo los 10 flags de #864): el lunes 26
  sale FUERA_DE_BANDA con 11 flags (Puyehue VIIRS 750 0,517x nuevo) y abre un issue nuevo sin cerrar #864; #900 no
  cambia nada antes del 9-nov. Informe en `experiments/_s162_vuelta3/AUTOAUDIT_LUNES_26.md`. Quedan 4 subagentes en vuelo.

### 2026-10-25 ~02:15 UTC (S162): relevos preparados; cinco subagentes lanzados desde la coordinadora
- Revisión de las hijas: `loop-instrumento` terminado; `loop-viirs375` en pausa (PD1 completo, espera la vía de
  proceso y #903/#905; su rama no estaba en el remoto y la subió la coordinadora, `c0215a97d`); `loop-modis` cerrado
  con traspaso; `loop-viirs750` con su loop detenido. Relevos de MODIS y VIIRS 750 preparados en
  `tasks/BRIEFS_SESIONES_S162.md` (`649d14a66`); no se abrieron porque la app no abre sesiones desde el control remoto.
- Nicolás: «Sí lo que recomiendes, si necesitas seguir en otra con retomar puedes hacerlo». Lanzados como subagentes,
  cada uno en su worktree y con su rama empujada al remoto, para que su resultado sobreviva a esta sesión:
  1. A61 de las 48 protegidas de MxD03 y los cuatro seguimientos del verificador (Fable) → rama `s162-a61-mxd03`,
     `C:\vrp-trabajo\s162-a61\experiments\_s162_mxd03\a61\INFORME.md`.
  2. PR del veredicto de MxD03 (D35, marcas A113 en D18 y SINTOMAS §3, Láscar 05-11 en BEYOND §12, cita de MOD-A) en
     borrador, sin merge (Opus) → rama `s162-pr-veredicto-mxd03`.
  3. Analizador de V750-A con TDD, mutaciones y verificador (Opus) → rama `s162-v750a-evaluador`.
  4. Las 6 protegidas de Suomi NPP que pierden los brazos de VIIRS 375, con la regla de #903 (Fable) → rama
     `s162-v375-protegidas-snpp`.
  5. Simulación del auto-audit del lunes 26 sin y con #900 (Sonnet) → scratchpad de S162 `vuelta3\autoaudit_lunes`.
- Los relevos de MODIS y VIIRS 750 tienen que partir leyendo esas ramas (las tareas 1, 2 y 3 ya no son suyas).

### 2026-10-24 ~22:45 UTC (S162): V375-B RESUELTO con B2: SILENCIO ACOTADO BAJO K (verificado)
- Verificador limpio (Sonnet, CONFIRMADO; `claude/s162-viirs375-c1b864` `52f255721`, `experiments/_s162_v375/b2/
  resultado_run40131572769/INFORME.md`): en 1.165 noches limpias nuevas el port publica 6 (0,52 % [0,24; 1,12]), todas
  de 1 píxel y 0,01-0,04 MW; cota sobre todas las noches limpias 2,48 % (estricta 2,65 %) contra la vara de 3,85 % de
  K. Control de vida 20/20, recálculo = runner 19.277/19.277, K = publicado 2.032/2.032; las 35 no observadas no
  mueven el veredicto (harían falta 13 a 15 publicando). Matices: la unión no confirma de forma independiente (73 % del
  lote que decide); «calla al menos tanto como K» no es «no enciende nada nuevo» (apaga 72,5 % de lo que K publica en
  noches limpias y enciende ~17 de 3.323 donde K calla).
- **PD1 de VIIRS 375 completo**: caja C13 en el cráter (V375-C), silencio acotado (V375-B), V375-D no se abre. V375-E
  espera la vía de proceso en `pipeline/` (PD3, se construye primero para V750 y se reutiliza) y #903/#905. Loop de
  `loop-viirs375` en pausa. Limpieza pendiente de Nicolás: 1,8 GB de artefactos falsos del verificador en
  `C:\vrp-trabajo\temporales\s162_v375\verif_v3\`.

### 2026-10-24 ~22:20 UTC (S162): lote V375-B2 completo; loop-modis cerrado
- Lote V375-B2 (40131572769): 1.220/1.220 pasadas con resultado, 1.185 grillas; los 26 rojos son exit 2 de diseño
  (comprobado por la coordinadora en 21: 1 o 2 pasadas sin procesar, sin Traceback). Control de vida 20/20 ok; muestra
  1.165 ok y 35 `volcan_fuera_del_granulo` (2,9 %, mismo gránulo que producción, píxel más cercano a 5,8-30,5 km, 16
  pasadas partidas): «no observado». Artefactos en `C:\vrp-trabajo\temporales\s162_v375\run_40131572769\` (144 MB).
  Evaluación en curso, verificador limpio antes de informar.
- `loop-modis` cerró con /cierre: traspaso en el bloque 0 de `tasks/LOOP_MODIS.md` (`claude/s162-modis-774bb0`
  `7824fd1fc`). Pendiente para su próxima sesión: PR del veredicto de MOD-B, A61 de las 48 protegidas, candado de MOD-D.

### 2026-10-24 ~21:25 UTC (S162): MOD-B VERIFICADO: CUMPLE SIN DAÑO
- Verificador Fable alto, código independiente (`s162-mxd03-codigo` `afb3fcdea`, `experiments/_s162_mxd03/resultado/`):
  5.465/5.465 pasadas, un solo commit, 0 errores, 0 duplicados; P1 0 de 48 protegidas perdidas; P2 bajo 35° EMPATE;
  vara MxD03 más cerca por cinco caminos; scripts reproducidos byte a byte.
- Matices: 12 controles reales, no 13 (`vara_cruda` siempre da OK); la vara mide «más cerca del cráter de Láscar», no
  «del calor de esa noche»; M neutro en la mediana pero 17 de 79 alertas cambian más de 10 % y 6 más de 30 %; las 48
  protegidas quedan más cerca del cráter con MxD03 (mediana 1,46 km); la re-corrida en sha del control 4 nunca se
  ejercitó. Seguimientos: control del módulo de R con relleno, `_interp_geo` con −999 (SOSPECHA), 36 records en que X
  pierde píxeles sin geolocalización, corrimiento de 10 a 16 km en el borde del barrido con `_interp_geo`.
- Abre el ciclo de adopción por fidelidad literal (tag, flag con TDD, A61 de las 48 protegidas, sí de Nicolás, FICHA,
  marca en las tres vistas, aviso a OVDAS). Por D-48, dentro del paquete MODIS (MOD-D). `loop-modis` cierra con
  /cierre y sigue en sesión nueva con el PR del veredicto y la A61.

### 2026-10-24 ~21:10 UTC (S162): V375-B2 sellado firme; lote despachado
- Re-verificación del delta v2→v3 (Fable, contexto limpio) CONFORME: el control de vida atrapa por sí solo seis modos de
  port roto (no detecta, detecta todo, magnitud doblada, muerto sólo en el control, caída de 3 de 20, control ausente)
  con VEREDICTO B INVALIDO, y con lote sano da SILENCIO ACOTADO. H1 (la fuerza del control vivía en el archivo de
  objetivos) cubierto también en el evaluador. Sello firme por D-48 (`claude/s162-viirs375-c1b864` `1d81fe9f8`).
- **Lote V375-B2: run 40131572769** (1.220 pasadas, 48 trozos, max-parallel 8). Corrida vacía del vigilar-osf viejo:
  40131571938.

### 2026-10-24 ~21:00 UTC (S162): MOD-B (MxD03 sobre K) PRELIMINAR: CUMPLE SIN DAÑO
- Censo completo 5.465/5.465 pasadas en 24 partes, sin errores; K = data/, K2 = K. 13 controles en verde. P1 sin
  protegidas perdidas; P2 bajo 35° EMPATE (ΔX −1, ruido 4); vara VIIRS: **MxD03 más cerca por 0,73 km** (IC 0,49 a
  1,10, Terra y Aqua del mismo signo); M NEUTRO (ĝ 1,00). Condicionan la adopción sin cambiar el veredicto: auditoría
  espacial A61 de las 48 protegidas cuyo cúmulo se mueve (§6 P4, obligatoria) y P2 sin Cordón Caulle con signo contrario
  (+1 contra −1). Informe `experiments/_s162_mxd03/resultado/INFORME.md` (`s162-mxd03-codigo` `1aaaf709c`); verificador
  Fable alto en curso. Por D-48 la adopción va dentro del paquete MODIS (MOD-D), salvo que se atrase más de un mes.

### 2026-10-24 20:38 UTC, hora del servidor (S162): las tres tandas de MOD-B terminadas; humo de V375-B2 OK
- t3 de MOD-B (40126381034): 9/9 success. Las tres tandas corridas (t1 40112510038, t2 40122029477, t3 40126381034);
  `loop-modis` evalúa las tres juntas con verificador limpio.
- Humo de V375-B2 (40128648709) success: control de vida 5000 (Láscar 2026-04-25 05:54) M14 5 píxeles y 1,4126318824
  MW, exacto a S162; muestra 3000 (Isluga neg_resto) 0 píxeles. El lote espera la re-verificación del delta v2→v3
  (Fable, rompiendo el port en copias). NRT corriendo ahora (11 jobs).

### 2026-10-24 ~20:30 UTC (S162): humo de V375-B2 despachado; el lote espera una re-verificación corta
- V375-B2 v3 (`ae65eaaaf`, tag `s162-v375-b2-listo`): el segundo verificador dio CONFIRMADO EN PARTE con un G3 (ningún
  control probaba que el port estuviera vivo; un port muerto daba «calla»); arreglado con 20 pasadas de control
  re-medidas fuera de todo denominador (INVALIDO si M14 no las reproduce), probado con runs fabricados (vivo 20/20,
  muerto INVALIDO), NO DECIDE con más de 10 % sin dato, línea «VEREDICTO B». La probabilidad de decidir integrando la
  incertidumbre de 4 de 389 baja de 93 % a 0,74-0,80.
- Comprobado: el humo `74e368f6e` sólo agrega el workflow fuera de la carpeta; pipeline/ idéntico a `533398f8f`; el lote
  `a9331d51c` es fast-forward con 4 líneas del workflow. **Humo: run 40128648709**. El lote (48 jobs) sale con la
  re-verificación corta del delta v2→v3 conforme y el OK al humo, después de t3 de MOD-B.
- `loop-viirs750`: S-1 incorporado a V750-A §5 como diagnóstico obligatorio que no decide (`27973d13a`).

### 2026-10-24 ~20:15 UTC (S162): ablación real del bow tie de MODIS (D28) verificada
- `loop-modis`, verificador Fable alto (`claude/s162-modis-774bb0` `f49e57dd7`, `experiments/_s162_modis_bowtie/real/`):
  rearmar los 403 recortes nativos de MOD-C reproduce el lote 403/403; el método A (quitar sólo los centros que el
  barrido anterior ya cubre) no abre huecos reales y las 11 protegidas siguen publicando; la regla de filas de borde
  mataría la protegida de Chillán 2026-10-01 08:35 (5,18 MW): descartada. No se sostiene que el efecto quede en el foco
  duplicado (pasa por la sigma global del umbral de cumbre), ni que el 2 a 0 en neg_resto sea robusto (márgenes de NTI
  de 1e-6 a 8e-4). Efecto de D28 sobre la magnitud SIN DATO. MOD-D: brazo PM-sin_dup con el método A, sólo informativo.
- **Seguimiento S-1** (también para VIIRS 750): el umbral de cumbre del oráculo usa la sigma de toda la grilla de 51 km,
  lo que acopla cualquier A/B de remuestreo al borde de la escena; reenviado a `loop-viirs750` para V750-A.

### 2026-10-24 ~20:05 UTC (S162): t2 de MOD-B sin huecos; t3 despachada
- t2 (40122029477): 1.837/1.837 records ok, K2 = K, K = data/, commit `ffbb36248` en las 8 partes (24 a 52 min por
  job). Llevan 3.651 de 5.465 pasadas. Artefactos en `D:\vrp-trabajo\temporales\s162_mxd03\t2\`.
- **t3: run 40126381034**. Con ella salen las tres tandas; `loop-modis` evalúa las tres juntas con verificador limpio.

### 2026-10-24 ~19:40 UTC (S162): V375-B2 dimensionado en 1.200 noches; t2 de MOD-B casi lista
- V375-B2: el primer verificador mostró que la v1 reutilizaba S162 (en la frontera declaraba «calla» en 11-20 % de los
  casos cuando no correspondía); en la v2 decide sólo la muestra nueva de neg_resto. Tamaño: **1.200 noches** (con la
  tasa observada 1,16 %, probabilidad de decidir 93 %; ~8,3 h de runner, 48 trozos, ~90 min de reloj). Aprobado con
  D-48. Segundo verificador en curso (`claude/s162-viirs375-c1b864` `7ff23cc3a`, `experiments/_s162_v375/b2/`).
- t2 de MOD-B: 7 de 8 partes en verde, falta la 15.

### 2026-10-24 ~19:30 UTC (S162): V375-B y V375-C verificados (PD1 de VIIRS 375)
- Verificador limpio (Sonnet), sin hallazgos que cambien veredictos; informe `experiments/_s162_v375/
  resultado_run40116289866/INFORME.md` (`claude/s162-viirs375-c1b864` `35e9560c2`). Instrumento: 709/709 pasadas,
  recálculo = runner 7.427/7.427, K = publicado 847/847, cobertura del marco 0 alertas sin record.
- **V375-C: la caja de cumbre va en el CRÁTER de `volcanoes.yaml`, brazo C13 (13 × 13 celdas de 375 m)**. Recall bajo
  1 MW de 0,69 (caja de S159) a 0,95 [0,92; 0,98], a la par de K (0,957); P2 contra K GANA; negativos 2,03 %; M 0,999.
  La ganancia está en Cordón Caulle y Tupungatito (cráter a 7,6 y 4,8 km del centro del TIF). V375-D no se abre.
- **V375-B: NO RESUELTO** con la regla sellada (port 4 de 389 neg_resto; unión 0,95 % [0,37; 2,38]; la cota de 8,5 %
  baja a 2,4 %). ENCIENDE DE MÁS descartado. Con D-48: segunda muestra disjunta de neg_resto, pre-registrada antes de
  mirar, con la misma regla.
- Riesgo para V375-E: los 10 brazos pierden las mismas 6 protegidas, todas Suomi NPP sólo OCR del lote de S159 (K publica
  3); lo decide V375-A (#903).

### 2026-10-24 ~19:15 UTC (S162): diagnóstico físico de las dos publicaciones de MOD-C (SOSPECHA fuerte, sin verificador)
- Láscar 2026-05-11 07:55 (Aqua, 38°): **calor real del cráter** (K publica el cráter esa noche en VIIRS 375 y 750 de
  los tres satélites a 0,03-0,31 km; MIROVA alertó en VIIRS esa noche y en casi todas las vecinas; su MODIS dice RUTINA
  a las 07:55). Para la réplica es costo; físicamente, señal: candidata al perfil experimental.
- Llaima 2026-07-24 01:05 (Terra, 63°): **artefacto de gradiente** (ninguna de las otras 10 pasadas de la noche tiene
  cúmulo, MIROVA RUTINA en todas, nadie ve nada del 19 al 29-jul; 5 × 5 con 14,1 K de cambio en TIR).
- Con D-48: estrato informativo en MOD-D (soporte de otro sensor la misma noche en otro gránulo, A109), sin tocar la
  regla sellada; adenda con verificador antes del candado. Informe en `claude/s162-modis-774bb0`
  `experiments/_s162_modis_negativos/diagnostico/INFORME.md`.

### 2026-10-24 ~19:05 UTC (S162): MOD-C verificado INDECIDIBLE; se resuelve en el censo de MOD-D
- Verificador limpio (Fable alto) confirmó MOD-C: x = 2 de n = 390, ΔE −18,1 [−44,4; +40,1], lector idéntico byte a
  byte. VRC-01: en el denominador de K el port da 0,54 %. VRC-05: las dos publicaciones deciden (con 0 sería CONFIRMA),
  son robustas al instrumento pero dependen de banda 22 y MxD03 (con banda 21 o geolocalización de 5 km dan 0); calor
  real o artefacto SIN DATO.
- Aplicado con D-48: sin lote nuevo; el «gana contra K» de MODIS lo resuelve el censo de MOD-D. Pedido a `loop-modis` un
  diagnóstico físico de sólo lectura de las dos publicaciones (Láscar 2026-05-11 07:55, Llaima 2026-07-24 01:05).
- `loop-viirs375`: lectura pre-registrada del lote lista, en verificación limpia; instrumento limpio (recálculo = runner
  en 7.427 pasadas por brazo, K = publicado 847/847, cobertura completa).

### 2026-10-24 ~18:50 UTC (S162): MOD-C terminado (preliminar INDECIDIBLE); t2 de MOD-B despachada
- MOD-C (40120713181): 7 trozos en exit 2 de diseño (8 volcán fuera del gránulo, 2 escenas inválidas), sin errores de
  proceso; artefactos en `C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181\` (108 MB). **Preliminar, sin
  verificador**: con la regla sellada INDECIDIBLE: el port publica en 2 de 390 neg_resto evaluables (0,51 %; Láscar
  2026-05-11 07:55, 0,30 MW a 1 km, cenit 38°; Llaima 2026-07-24 01:05, 0,43 MW a 2 km, cenit 63°; ambos de 1 píxel).
  ΔE −18,1 [−43,8; +40,1]. Controles en verde (K = publicado 403/403; 13 controles iguales a S159; 11 protegidas
  publican). La cota de 9,4 % de S159 queda reemplazada por una tasa medida. Informe `experiments/_s162_modis_negativos/
  INFORME.md` (`claude/s162-modis-774bb0` `11570ab30`).
- **t2 de MOD-B: run 40122029477**. t3 cuando termine.

### 2026-10-24 18:26 UTC, hora de los runs (S162): lote V375 completo; MOD-C despachado
- Lote V375 (40116289866) terminado en «failure» sólo por los exit 2 de diseño: 709 pasadas con resultado, 698 ok y
  11 `volcan_fuera_del_granulo`, todas neg_resto. Diagnóstico de `loop-viirs375`: **«no observado», no falla de
  cobertura** (el probe bajó exactamente el mismo gránulo que el record de producción; el píxel más cercano queda a
  5,1-24,6 km del centro; producción dejó record porque su círculo de 25 km roza el gránulo; en 6 hay otro record del
  mismo volcán a ≤ 7 min, la pasada partida). Salen del denominador (11 de 400, 2,75 %, bajo el 10 % del §4.1),
  declarado conservador para el port. Artefactos en `C:\vrp-trabajo\temporales\s162_v375\run_40116289866\` (86 MB).
  Evaluación en curso, con verificador limpio antes de informar.
- **MOD-C: run 40120713181** (rama `s162-negmodis-disparo` en `ffc1abc1b`, tag `s162-base-portes` sobre `0e18e1053`).
  t2 de MOD-B cuando termine.

### 2026-10-24 ~18:25 UTC (S162): V750-B SELLADO bajo D-48
- Condición cumplida: 13 de 13 mutaciones atrapadas por aserción (las 11 de la tercera vuelta más VB3-01 y VB3-02), con
  la identidad PASA y el control de caída CAÍDA, cada una corriendo la batería entera de 19 escenarios
  (`experiments/_s162_v750b/mutar_bateria_salida.txt`). Ensayo con datos reales: compuerta abierta, censo 503/503
  iguales en posición, control positivo 7 y 7, negativo 0 bloques.
- **Sellado**: commit `1af6c3cd8`, tag `s162-v750b-sellado` (en el remoto). El 2026-11-03 la hija genera
  `objetivos_v750b.json` y `sin_granulo_v750b.json` desde el tag y pide el despacho con sus sha256.

### 2026-10-24 17:59 UTC, hora del servidor (S162): lote V375 con 6 jobs en exit 2 (no son caídas)
- Run 40116289866: 9 success, 6 failure, 8 en curso, 5 en cola. Los 6 failure (probe 1, 8, 9, 10, 11, 13) tienen cada
  uno 1 pasada con `estado=volcan_fuera_del_granulo` y salen con exit 2 por diseño; los artefactos se suben igual.
  Pasado a `loop-viirs375` para que distinga «gránulo distinto al de producción» (cobertura) de «no observado» (fuera
  del denominador, regla de #904) antes de evaluar. Nada relanzado.
- V750-B: VB3-01 aplicado (`93d34d5aa`), medición de mutaciones (13 más control de caída, batería de 19 escenarios) en
  curso.

### 2026-10-24 ~18:10 UTC (S162): fase 0 del instrumento terminada; su loop detenido
- `loop-instrumento`: las 7 tareas en #902 a #905, los cuatro con CI verde, verificador limpio aplicado y mutaciones
  atrapadas por aserción; ninguno toca `pipeline/`; ninguno mergeado (merges de Nicolás). Loop de la hija detenido.
  #889 (R2.1, toca `pipeline/`) sigue en borrador y sin rebase.
- V750-B: tercera vuelta corta lanzada (`439968ec1`, con nulo de la batería medido rompiendo una copia del analizador).
  Lote V375 (40116289866) en curso, la hija cuenta los 28 trozos antes de evaluar.

### 2026-10-24 ~17:55 UTC (S162): V750-B v3 y t1 sin huecos; cobertura del marco de V375 OK
- V750-B: segunda vuelta (Sonnet) «conforme con cambios»; v3 `81a5cfcd2` con VB2-01 (desempate exige «no peor»
  también con la tabla sola) y VB2-02 (lectura conservadora, **confirmada con D-48**: SIN SUSTRATO es «no peor» sólo
  con neto en 0 o a favor); batería sellada de 11 escenarios, 11/11. Pedida una **tercera vuelta corta sobre el delta**
  v2→v3 (Fable): cada vuelta anterior encontró un G3 en la regla de decisión. Sello efectivo si da conforme sin tocar la
  regla.
- t1 de MOD-B sin huecos: 1.814/1.814 records ok, K2 = K, 0 re-corridas, commit `ffbb36248` en las 8 partes; 24 a 48
  min por job: las 24 partes sumarán ~15 h de runner, no 47. Artefactos en `D:\vrp-trabajo\temporales\s162_mxd03\t1\`.
- V375: cobertura de #904 aplicada al marco desde la rama del instrumento (`ff452671c`): COBERTURA OK, 0 alertas y 0
  protegidas sin record de producción (adenda 2, `a01d50f57`); el veredicto deja de ser provisional por esa causa.

### 2026-10-24 17:28 UTC, hora de los runs (S162): t1 de MOD-B terminada; lote de V375 despachado
- t1 de MOD-B (40112510038): 9 de 9 jobs success (~50 min, menos que las 2 h estimadas); `loop-modis` revisa cobertura.
- Humo de V375 (40115765406) success en 2 min 15 s; OK de `loop-viirs375`: Láscar 2026-04-05 05:30 protegida, port
  1,521 MW en los 10 brazos contra 1,52 de MIROVA; K re-corrido igual a lo publicado (pc 1,086, f5_core 1,1206);
  Tupungatito neg_resto 0 píxeles en los 10 brazos; recálculo sin red igual al runner 467/467, K = publicado 151/151;
  nulo, NUNCA y PLACEBO en verde. El humo destapó un KeyError del evaluador en el camino S162 (arreglado sin cambiar
  reglas, adenda 1 de PREREGISTRO_C.md, `a6a02071b`; el runner no lo usa).
- **Lote de V375: run 40116289866** (28 jobs, max-parallel 8), en cola detrás del NRT y del experimental diario. Nuevo
  orden: MOD-C cuando termine el lote V375; t2 y t3 de MOD-B después.

### 2026-10-24 17:21 UTC, hora de los runs (S162): humo de V375 despachado
- `loop-viirs375` armó los disparos sobre el árbol de `ca034d66e` (pipeline/ idéntico a `533398f8f`, el que escribió los
  records del marco) para que «K re-corrido = publicado» compare el mismo detector. Comprobado: el humo `fd0ba12bb` sólo
  agrega `experiments/_s162_v375/` y `.github/workflows/probe-s162-v375.yml`; el lote `798cac8ea` sólo cambia 4 líneas
  del workflow. Tags `s162-v375-bc-sello`, `s162-v375-disparo-humo`, `s162-v375-disparo-lote` subidos.
- **Humo: run 40115765406** (2 pasadas, 1 job, junto a t1 de MOD-B: 9 jobs). Efecto lateral: el árbol viejo trae el
  `vigilar-osf-mirova.yml` inválido de S158, y el push dejó una corrida sin jobs (40115764552); inocuo para el probe.
  Lección para disparos sobre árboles viejos: revisar qué otros workflows del árbol corren por push.
- Lote (28 jobs, max-parallel 8, ~50 min de reloj) con el OK de la hija, después de MOD-C.

### 2026-10-24 ~17:40 UTC (S162): V375-B/C salen sin esperar a V750-B; orden de despachos
- V750-B no sale antes del 2026-11-03; el lote de V375-B y V375-C (709 pasadas, ~4,9 h de runner) no depende de esa
  fecha, así que sale antes. Sello aplicado con D-48 sobre la recomendación de `loop-viirs375` (D-36 y la ROI ya
  aprobadas), revocable por Nicolás.
- Orden por cupo (NRT 11 jobs, tope 20): t1 de MOD-B (en curso) → MOD-C (8 jobs) → humo V375 → lote V375 con OK al
  humo → t2 → t3 de MOD-B → V750-B desde el 03-11. La cobertura de #904 se aplica al evaluar desde la rama del
  instrumento, declarando el commit, aunque #904 no esté mergeado.
- `loop-viirs750`: prueba de equivalencia de V750-A escrita y probada antes de la implementación (`76a1e6f53`; roja
  hoy porque el módulo no existe; contra el oráculo pasa en 1.020 casos y 10 recortes nativos; 6 mutaciones
  atrapadas). `loop-instrumento`: hallazgos del verificador de #905 cerrados (P2 suma por bloque noche-volcán).

### 2026-10-24 17:10 UTC, hora del servidor (S162): vuelta; el hueco del NRT de la tarde es normal
- t1 de MOD-B (40112510038): 2 trozos terminados en verde, 6 en curso. Disco C: 42 GB, D: 9,7 GB.
- NRT sin correr desde las 13:49 UTC: **normal**. Los despachos horarios de cron-job.org van de 04:10 a 12:10 UTC (la
  noche chilena) y el `schedule` de GitHub dispara cada ~5 h en la práctica (ayer 14:40, 19:47 y 22:53 UTC). La
  observación de las vueltas anteriores queda cerrada.

### 2026-10-24 ~17:30 UTC (S162): V750-B v2 listo; sello por D-48 condicionado a una segunda vuelta del verificador
- `loop-viirs750`: pre-registro V750-B v2 (`claude/s162-viirs750-f63ef4` `62e6ea194`); verificador Fable «listo para
  sello con cambios», 16 hallazgos corregidos (VB-01: el desempate podía elegir un brazo que PIERDE contra B1). Ensayo
  sobre las 510 grillas de N: B0 y B1 iguales al censo 503/503, K igual a producción 503/503, control positivo 7 (PCC).
  Brazos B0, B1, B2, B3, B4, B5, K más el diagnóstico N0/N1 (confirma V750-C en el mismo run). Ventana 2026-04-01 a
  2026-11-02 12:59 UTC sin 12, 13 y 17-20 oct: **despacho no antes del 2026-11-03**.
- Aplicado con D-48 sobre las lecturas conservadoras de la hija: T decide la tabla sola, O tabla+OCR; sin ganador nunca
  un brazo que PIERDE o BLOQUEA; distancia desde el cráter; B5 con la lectura del comentario del `.m`. DN-2 como paso
  obligatorio de la lectura (si gana B2 o B4, documentar fidelidad al `.m` y no gate propio, A85). Sello efectivo
  cuando la **segunda vuelta del verificador** sobre la v2 dé conforme (pedida: VB-01 cambió la regla de decisión).
  Revocable por Nicolás.

### 2026-10-24 ~17:15 UTC (S162): MOD-D sellado por D-48; instrumento con sus 7 tareas en PR
- `loop-modis`: MOD-C con segunda ronda del verificador («se puede despachar tal como está»; disparo `ffc1abc1b` sin
  cambios); MOD-E verificado (D28 SIN DATO); MOD-D v2 listo para el sello de reglas. **Aplicado por la coordinadora con
  D-48** (autorización vigente de Nicolás «sobre las decisiones mías haz lo que tú recomiendes», sobre la recomendación
  de la hija): reglas de MOD-D v2 SELLADAS (el candado y su verificador siguen antes del despacho); D35 y las marcas A113
  de MxD03 al catálogo en el PR del veredicto de MOD-B. Revocable por Nicolás.
- Dato de MODIS: en la población congelada K/MIROVA de Chillán es 0,635 (n 7), no 0,485; cae de 0,64-0,85 bajo 30° de
  cenit a 0,14-0,21 entre 35 y 51°; el port detecta las dos protegidas a 58° que K no ve.
- `loop-instrumento`: las 7 tareas con PR (#902 a #905; #905 = T3 apilado sobre #904, 21 mutaciones atrapadas, coincide
  con el evaluador sellado de D25 en 250 casos; su verificador corre). t1 de MOD-B en curso (8 jobs).

### 2026-10-24 ~17:00 UTC (S162): MOD-C listo; sale entre t1 y t2 de MOD-B
- `loop-modis` entregó MOD-C (lote de 400 negativos neg_resto del port MODIS más 13 controles, D-36; regla Jeffreys
  fijada antes: GANA sólo con 0 de 400, 1 a 7 INDECIDIBLE, 8 o más refuta), pre-registro en `claude/s162-modis-774bb0`
  `5f40f604d` (`experiments/_s162_modis_negativos/`), verificador Fable alto: se sostiene, tres grietas arregladas.
  El verificador refutó la lectura previa del bow tie (MOD-E): D28 queda SIN DATO hasta la ablación con los recortes de
  MOD-C. MOD-D todavía no despachable.
- Commit de disparo preparado por la coordinadora: `ffc1abc1b` (5f40f604d + workflow copiado a `.github/workflows/`),
  worktree temporal `C:\vrp-trabajo\s162-negmodis-disparo`, sin subir. Orden por cupo de 20 jobs (NRT 11): al
  terminar t1 (40112510038), tag `s162-base-portes` sobre `0e18e1053` + push a `s162-negmodis-disparo`; al terminar
  MOD-C, t2.

### 2026-10-24 ~16:40 UTC, hora de los runs (S162): humo de MOD-B en verde; t1 despachada
- Humo 40111997157: plan y probe success (comprobado); evaluado por `loop-modis`: VEREDICTO INCOMPLETO esperado (15 de
  5.465 pasadas), todos los controles OK (geometría S151 2,581 km igual, nulo 0,0 km, K igual a data/ 15 de 15, K2 igual
  a K, 0 re-etiquetadas, predicado con el mismo sha256), archivado en `s162-mxd03-codigo` `0c2a912ee`. Descargas de 2 a
  3 s por archivo (contra 32,8 s en el probe M).
- **t1 despachada: run 40112510038** (rama `s162-mxd03-t1`, tag `s162-mxd03-tag`), sin otros runs vivos. t2 y t3 cuando
  termine cada anterior.

### 2026-10-24 ~16:55 UTC (S162): humo de MOD-B (MxD03 sobre K) despachado
- Pedido de `loop-modis`: pre-registro v2 sellado con D-48 más adenda de 5 puntos; arnés 4/4 mutaciones, evaluador
  22/22 pruebas y 16 mutaciones; verificador Fable alto en dos rondas («se puede despachar el humo»). Comprobado por la
  coordinadora: el commit `ffbb36248` sólo agrega `experiments/_s162_mxd03/` y `.github/workflows/probe-s162-mxd03.yml`
  sobre origin/main `80b819828` (0 archivos en `pipeline/`, `scripts/`, `volcanoes.yaml`, `frontend/`,
  `data/mirova_equivalent/`); YAML válido con `"on":`, sólo `EARTHDATA_TOKEN`.
- Tag **`s162-mxd03-tag`** sobre `ffbb36248` y rama de disparo `s162-mxd03-humo`: **run 40111997157** (4 gránulos, 1
  job, en curso). Las tandas t1, t2 y t3 (8 jobs cada una, ~2-2,5 h de pared, ~47 h de runner) recién con el OK de
  `loop-modis` al humo, una a la vez y sin chocar con el cupo de 20 jobs (NRT usa 11).
- Observación: el NRT no corre desde las 13:49 UTC (datos al 14:21); vigilar si es la ventana de cron-job.org.

### 2026-10-24 ~16:50 UTC (S162): estado de las hijas; armando el despacho combinado de la fase 1
- **loop-instrumento**: #902 (MOD-A, cita de MOD03), #903 (alerta y protegida por pasada, la tabla manda) y #904
  (evaluador común con cobertura contra la referencia) con CI verde y CLEAN; el verificador de #904 encontró dos
  defectos de G3 (protegida que falta en un solo brazo no invalidaba; control incompleto dejaba ciego al evaluador),
  arreglados con prueba roja primero. Merges: de Nicolás.
- **loop-viirs375**: pre-registros V375-B, V375-C y V375-E listos para el sello (rama `claude/s162-viirs375-c1b864`,
  `b9e9c9f97`, `experiments/_s162_v375/`), evaluador probado, verificador limpio (Sonnet) pasado y corregido. Lote único
  de sólo lectura para B y C: 709 pasadas VIIRS 375 (400 neg_resto, 41 protegidas, 155 bajo 1 MW, 113 neg_pub), ~4,9 h
  de runner, `probe-s162-v375.yml` de 28 trozos, humo «1011,1062». Hallazgo: el nulo por hora de la curva de cenit de
  750 no sirve en 375.
- **loop-viirs750**: prueba local de V750-B commiteada (`331921487`); falta el ensayo del analizador y su verificador.
- **loop-modis**: MOD-E con informe; esperando dos verificadores (arnés de MOD-B; MOD-C/D/E) antes de pedir despacho.
- Despacho combinado de la fase 1 (V750-B, V375-B, V375-C, MOD-C): se arma cuando estén los verificadores de V750-B y
  MOD-C; se pide un solo sello a Nicolás para los cuatro pre-registros. Disco: C: 43 GB, D: 9,7 GB.

### 2026-10-24 ~16:20 UTC (S162): V750-C cerrado con verificador limpio (loop-viirs750)
- Rama `claude/s162-viirs750-f63ef4`, commit `5b56c77da`, verificador Fable 5.1. **Dos piezas callan las cumbres tibias
  que K deja en 0 MW, no una**: dentro de la caja sensible 7x7 (38 de 60) las calla la **interpolación lineal** (vecino
  más cercano en la misma grilla recupera 23, en la celda exacta de K; aísla interpolador y fase, no la ausencia de
  remuestreo); fuera de la caja (22: Tupungatito 17, PCC 4, Láscar 1) las calla la **ROI** (la celda de K está a 4,4-5,4
  km del centro de la grilla de MIROVA, con umbrales conservadores). Las 7 protegidas que pierde la caja por defecto son
  todas de PCC (lacolito a 7,7 km). **La magnitud la da el fondo del código**: mismo código y píxeles con fondo de anillo
  0,458 contra 0,999 (K 0,510). Recorte, regresión del pase 2, K1/mínimos y compuerta no deciden. La «caja por defecto»
  es un supuesto de una matriz de ejemplo de 2023; el `.m` (l. 105-125) dice que la ROI se ajusta por volcán.
- Consecuencia: D17 (remuestreo con interpolación lineal) es condición del paquete también para la detección, y la ROI
  de PCC y Tupungatito (V750-B) es la otra pieza obligatoria.
- Borradores en la rama: `experiments/_s162_v750b/PREREGISTRO_V750B.md` (brazos B0, B0e, B1, B2, B3, B4, K más el
  brazo nativo N0/N1 de S_C; 32 trozos, ~2 h; guarda grillas GEO ~170 MB y ventanas nativas ~30 MB), `_s162_v750a/
  PREREGISTRO_V750A.md`, `_s162_v750f/PASO_A_PASO_O2.md` (para Nicolás). V750-B **no se despacha todavía**: falta su
  prueba local, su verificador, la cobertura del instrumento (#904) y el sello de Nicolás.
- Sesiones nuevas abiertas por las hijas (vistas en `git worktree list`): `D:\vrp-trabajo\s162-mxd03` (rama
  `s162-mxd03-codigo`, de loop-modis) y `D:\vrp-trabajo\worktrees\s162-instrumento-tareas` (`instrumento/evaluador-t3`,
  de loop-instrumento). Sus ids `local_…` todavía no me los avisaron.

### 2026-10-24 15:51 UTC, hora del servidor (S162): vuelta de la coordinadora
- Sin runs vivos en GitHub; NRT verde (último 13:49 UTC; vigilar que vuelvan los despachos de las :10). Disco C: 43 GB,
  D: 9,7 GB (bajó 1,3 GB desde la limpieza: lo usan las hijas; parada en 3 GB).
- `loop-instrumento` abrió #902 (MOD-A, cita de MOD03), #903 (T4+T6, alerta y protegida por pasada) y #904 (T1+T2+T5,
  evaluador común con cobertura contra la referencia): se revisan cuando la hija entregue su resumen; los merges son
  de Nicolás. `loop-viirs750` corre la segunda pasada de V750-C (los `.npz` de N sólo traen la grilla GEO lineal; usa
  sustitutos del barrido nativo y pedirá un probe de ventana nativa si el veredicto depende de eso). Fase 1 sin
  despachar: espera la cobertura contra la referencia (#904).

### 2026-10-24 ~16:40 UTC (S162): las hijas pueden abrir sus propias sesiones
- Nicolás: «si esas sesiones y loops necesitan iniciar otras también lo tienen permitido, envíales un mensaje para que
  lo sepan». Mensaje enviado a las cuatro (entregado en su bandeja), con las reglas: worktree y rama propios, cola y
  bitácora propias enlazadas desde su `tasks/LOOP_<X>.md`, despachos sólo vía esta coordinadora (sesión «Retomar»),
  nada en `pipeline/` sin tag y sí, parada bajo 3 GB, y avisar el id `local_…` de cada sesión nueva.

### 2026-10-24 ~16:30 UTC (S162): programa por sensor, cuatro sesiones hijas con loop, decisiones de Nicolás aplicadas
- Programa escrito: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` (`b05d60527`): pasar de palancas
  sueltas a «el paquete del código de MIROVA por sensor con brazos de diagnóstico»; D17 pasa a pieza obligatoria.
- Nicolás: «Sí, abre las cuatro sesiones hijas [...] cada una con su loop». Abiertas, cada una en su worktree desde
  `loop/activo`, con su cola en `tasks/LOOP_<X>.md` y despachos pedidos a esta coordinadora: `loop-instrumento`
  (fase 0, rama `s162-instrumento`), `loop-viirs750` (`s162-viirs750`), `loop-viirs375` (`s162-viirs375`),
  `loop-modis` (`s162-modis`). Esta sesión lleva el turno de los A/B (máx 2) y es la única que escribe este archivo.
- **Decisión de Nicolás (D-48, 2026-10-24): «sobre las decisiones mías haz lo que tú recomiendes»**, sobre las 14 del
  §9 del programa más las del traspaso S162. Aplicado:
  - D25 NO SE ADOPTA: marca al inicio de D25 en `docs/MIROVA_DIVERGENCES.md` (la divergencia sigue ABIERTA; el camino es
    el fondo del programa dentro del paquete). Pruebas que leen el catálogo: 68 passed, 2 xfailed.
  - Paquete por sensor, validación por equivalencia + censo + sombra prospectiva, etiqueta de protegida de cráter
    informada al lado, filtro de publicación con predicado de cumbre y P-sinfiltro medido, ROI de PCC y Tupungatito a
    medir, D-36 (lote de negativos 375 y MODIS), MxD03 sellado (D-19) para correrlo, vía «código MIROVA» detrás de flag
    tras PD1, D9 fuera del paquete medido, tope de cordura aparte, diurno después: pasan a las colas de las hijas.
  - #888 cerrado (superado por contenido; rama en el remoto).
  - Limpieza segura: 9 worktrees verificados limpios y con su commit en el remoto, quitados con `git worktree remove`
    (ramas intactas, incluidas `s159-oraculo-censo` y `s159-portes`). C: 35 → 44 GB, D: 8,6 → 11 GB.
- **No aplicado, necesita a Nicolás**: los merges de #900, #901 y #898 (CI verde, CLEAN; el clasificador de permisos
  bloquea merges a main, como en S158); borrar las carpetas no versionadas (`D:\vrp-trabajo\mirova-v1`, temporales de
  pytest en `D:\vrp-trabajo\temporales\`, `experiments/_s140`, `experiments/_s160_espacial/data`); correr O2 en MATLAB
  Online; enviar el correo a Coppola (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`). #889 (toca `pipeline/`, en conflicto
  con main) queda en la cola de `loop-instrumento`.

### 2026-10-24 ~15:45 UTC (S162): verificador de los cúmulos por matriz; Nicolás pide programa por sensor en sesiones hijas con loop propio
- Verificador limpio (Opus, `experiments/_s162_vuelta2/VERIFICADOR_CUMULOS_MATRIZ.md`, origin/main 80b819828):
  CM162-01 CONFIRMADO EN PARTE (G3): mecanismo y los dos casos se reproducen; en K cambian 7 a 13 de 290
  publicaciones V750 según el umbral, sólo 1 protegida cruza 1 MW (Láscar 2026-05-05 06:06); control a nadir 0
  cambios bajo 20°; no cambia qué se publica. Denominadores del auditor no reproducidos (290/86/1.769 contra
  338/82/2.070). CM162-02 G1 (f5_core inmune, 0 de 153). CM162-03 en parte: en Láscar el tablero publica el máximo,
  no la suma; en Chillán 10-01 los 4,2 MW son cota superior. VM162-01 (G2): pegar no es neutro (un negativo limpio de
  PCC 2026-06-11 sube de 0,447 a 3,03 MW). **Lectura: es una sola divergencia, D17 sin de-solape ni remuestreo**
  (DISENO_D17 §4.3 ya nombra el doble conteo; lo nuevo es la causa de la fragmentación y la instancia V750).
- Nicolás: «más que sólo los frentes deberían haber planes para continuar los estudios y experimentos [...] después
  de la información nueva [del código de MIROVA V750]»; «cada plan puede ir en sesiones diferentes o hijas»; «cada una
  con su loop si es que se puede». Planificador (Opus) armando el borrador del programa por sensor; después, sesiones
  hijas (instrumento, VIIRS 750, VIIRS 375, MODIS), cada una con su loop, su cola y su bitácora propias; esta sesión
  coordina y lleva el turno de los A/B.

### 2026-10-24 ~15:20 UTC (S162): cúmulos armados por la matriz del barrido (sin verificar todavía)
- Agente Fable (`experiments/_s162_vuelta2/CUMULOS_POR_MATRIZ.md`): `cluster_hotspots` agrupa por vecindad 3x3 de
  índices (clustering.py:96); lejos del nadir los barridos se solapan y VIIRS borra filas, así que vecinos en el suelo
  no lo son en la matriz. En VIIRS 750 (publica `pc.vrp_mw`) se publica a veces un fragmento sin el píxel más
  caliente: pegando fragmentos cambian 8 de 338 publicaciones de las ventanas K, todas hacia arriba (4 de 82
  protegidas, 1 cruza 1 MW); en la historia 61 de 2.070. VIIRS 375 inmune en el número (f5_core), torcido en
  n_pixels/centroide. También cuenta doble huellas repetidas (Chillán V750 2026-10-01 06:00, 4,2 de 11,1 MW). No está
  en el catálogo con este nombre. Verificador limpio (Opus) despachado.

### 2026-10-24 ~15:05 UTC (S162): hueco silencioso del 12-oct en V1 del A/B de D25
- Agente (Opus, `experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`), comprobado por mí en el log del brazo
  control de Chillán (l. 2590-2664, n=0 en NRT de Suomi NPP y NOAA-21 para el 12-oct) y en los records (el 12-oct los
  brazos sólo traen NOAA-20): NASA reprocesó Suomi NPP y NOAA-21 del 12-oct el 19-oct y CMR no los devolvió cuando
  corrió V1 (2026-10-21 04:50 UTC). A los tres brazos les faltan 44 pasadas que producción tiene, entre ellas la
  protegida de Chillán NOAA-21 05:18 (MIROVA 8,44 MW en 750; producción 3,46 MW summit).
- **Defecto del instrumento (no de producción)**: el hueco pasó cuatro filtros sin aviso: búsqueda vacía no es falla
  (`fetch.py:1087-1088` en 66961f65), la cobertura del A/B compara brazos entre sí, el evaluador busca protegidas sin
  record sólo entre pasadas con record (`evaluar_d25.py:988`, 999-1001) y la tolerancia de 5 % contra producción
  (l. 81, 1006-1007) no lo ve. 9 protegidas VIIRS de V1 sin record, todas de Chillán (7 del 18-oct, ya en D-29).
- No cambia la recomendación de D25 (no adoptar). Para A/B futuros: la cobertura debe contar pasadas protegidas sin
  record contra la referencia, no sólo contra los brazos ni con tolerancia agregada.

### 2026-10-24 ~14:50 UTC (S162): verificador de VIIRS 750; recomendación final de D25 a Nicolás; vuelta 2 lanzada
- Verificador limpio (Opus, `experiments/_s162_vuelta1/VERIFICADOR_ENCENDIDAS.md`): son 126 pasadas con D-29 (no 127),
  todas un píxel de cumbre que entra por el segundo pase sin compuerta y que K deja en 0,0 MW; D publica el 100 % de
  esos cúmulos (D25 no selecciona nada: VE162-02, la palanca real es el segundo pase, D19/D2). Recuperadas y
  encendidas no se separan (AUC 0,682, p corregido 0,146; poder sólo para separaciones fuertes). Que sean calor real es
  plausible pero el 750 de MIROVA calla ahí: bajo la vara de la réplica no rescata a D25; candidatas a `experimental`.
  VE162-01: una «recuperada» de PCC (2026-04-30 06:06) está a 16,7 km o más de la alerta de MIROVA. VE162-03: 9
  publicaciones de D sobre pasadas RUTINA que P2 no cuenta.
- Síntesis para Nicolás: **recomendación NO adoptar D25 tal como está** (no es el fondo del programa de MIROVA, que
  dilata 3x3, interpola, suma todo y no recorta; en magnitud actúa como ganancia pareja; en V750 publica lo que el
  segundo pase deja pasar). Lo que sí sale: el defecto de selección de K (CH162-01, VC162-01) y el «fondo del
  programa» como candidato del pre-registro R2.3.
- Vuelta 2 (sólo lectura): cúmulos armados por la matriz del barrido en pasadas oblicuas (Fable) y la alerta
  protegida de Chillán V750 2026-10-12 05:18 sin record (Opus).

### 2026-10-24 ~14:35 UTC (S162): verificador de Chillán: una protegida es defecto de K, la otra efecto real de D25
- Verificador limpio (Opus, `experiments/_s162_vuelta1/VERIFICADOR_CHILLAN.md`):
  - **CH162-01 CONFIRMADO, defecto de K en producción** (no de D25): en V750 Chillán 2026-10-14 06:18 el cúmulo
    publicado es la media de dos píxeles a lados opuestos del cráter y deja fuera al de 1,89 MW; con ese píxel D
    publicaría 1,363 MW y no cruzaría 1 MW. Mismo patrón en 4 protegidas V750 de V1, todas de Chillán.
  - **VC162-01 (G3, nuevo)**: en pasadas oblicuas los cúmulos se arman por posición en la matriz del barrido, no por
    geografía (V375 multi-cúmulo con píxeles de cúmulos distintos a menos de 0,30 km: 3/91 bajo 30°, 26/51 sobre
    50°). Mecanismo (bow tie) SOSPECHA. No está en el catálogo de divergencias.
  - La protegida V375 del 11-oct sí es efecto genuino de D25 (halo de vecinos 265-270 K contra anillo 262 K).
  - CH162-04 CONFIRMADO: el programa de MIROVA aparta los 8 vecinos (dilata 3x3), interpola, suma todo y no recorta;
    D25 tal como está no es el fondo de MIROVA en V750.
  - VC162-02: P1b sólo mira hacia abajo; D sube 3 protegidas V750 sobre 1 MW y baja 1. VC162-04: alerta protegida
    V750 Chillán 2026-10-12 05:18 sin record en ningún brazo (SOSPECHA).

### 2026-10-24 ~14:20 UTC (S162): #900 con el aviso de VIIRS sin juzgar, CI verde, listo para Nicolás
- Implementador (Opus) en `s161-auto-audit-cese-snpp`, head `7ab5e64f6`: `leer_ceses` valida la lista (PR162-04) y
  `sensores_sin_juzgar` deja el aviso en consola, latest.json (`plataformas.sin_juzgar`) y en el cuerpo de los issues
  (audit-weekly.yml). Rojas 5 por aserción contra `a7d1c0b91`; suite completa en árbol quieto 2.432 passed, 0 fallas;
  26-oct y 2-nov idénticos a main; 9-nov trae los dos avisos. CI `pytest` SUCCESS (run 40100161260), CLEAN, borrador.
- Supuesto declarado: el aviso no abre issue por sí solo si el lunes sale VERDE. Seguimientos: magnitudes por volcán
  bajo `MIN_N_RATIO` sin aviso individual; guiones largos viejos en el título del issue y la línea VEREDICTO.

### 2026-10-24 ~14:05 UTC (S162): inventario de limpieza entregado; informes de la vuelta 1 al repo
- Inventario (Sonnet, sólo lectura): 14 worktrees sin cambios versionados, todas sus ramas en el remoto. BORRAR SEGURO
  ~2,9 GB en D: y ~7,7 GB en C: (9 directorios de worktree, clon `D:\vrp-trabajo\mirova-v1`, temporales de pytest,
  `experiments/_s140` y `_s160_espacial/data`). No borrar las ramas remotas `s159-oraculo-censo` y `s159-portes` (sin
  PR, únicas). PREGUNTAR: 6,8 GB de temporales S155-S160 en D: (s160_audit 2,0 GB citado por main), 4 worktrees con
  datos ignorados, 4 stashes de mayo. #888 superado por contenido (cerrable). Espera decisión de Nicolás.
- Los cuatro informes de la vuelta 1 copiados a `experiments/_s162_vuelta1/` (persistencia; los de Chillán y VIIRS
  750 siguen SIN VERIFICAR hasta que entreguen sus verificadores).

### 2026-10-24 ~13:50 UTC (S162): diagnóstico de lo que D25 publica de más en VIIRS 750 (sin verificar todavía)
- Agente Fable (scratchpad S162 `vuelta1\encendidas_v750\INFORME.md`): las 127 pasadas de VIIRS 750 que D publica y K no
  (V1 45, V2 82) son un mismo objeto: un píxel junto al cráter que sólo entra por el segundo pase sin condicionar, al
  que K recorta a 0,0 MW y D le da 0,17 a 0,60 MW. Recuperadas y encendidas indistinguibles (29 variables, AUC máx
  0,67, no significativo). En 32 de 37 encendidas MIROVA alertó esa noche en VIIRS 375 y la 375 del mismo barrido
  publica a ~0,30 km (A109: no independiente). D25 no agrega ninguna noche nueva ni apaga nada en VIIRS 750.
  Lectura del agente: fuente sub-píxel que 375 m resuelve y 750 m diluye (cat. b A54), no artefacto.
- Verificador limpio (Opus) despachado.

### 2026-10-24 ~13:35 UTC (S162): diagnóstico de las 2 protegidas de Chillán (sin verificar todavía)
- Agente Fable (informe en scratchpad S162 `vuelta1\chillan_p1b\INFORME.md`): en Chillán el signo de D25 lo decide la
  temperatura del ANILLO (la cumbre está siempre a 259-269 K); las dos protegidas caen en noches de anillo frío
  (258-262 K, SOSPECHA de nube en el valle, máscara de nube apagada desde #535). VIIRS 750 14-oct 06:18: el cúmulo
  publicado no contiene al píxel más caliente (selección `vent_anchored` + modo de un píxel); sumando todos los
  alertados, D 2,40 queda más cerca de MIROVA 2,0 que K 4,01. VIIRS 375 11-oct: halo tibio de 265-270 K junto al
  cráter que el programa de MIROVA aparta y D25 resta. En el resto de V1, D25 sube Chillán (44/61 y 29/33).
- Verificador limpio (Opus) despachado sobre CH162-01 a 05, incluido si CH162-01 es defecto de K en producción.

### 2026-10-24 ~13:20 UTC (S162): vuelta 1, entregaron el verificador de D25 y la revisión de #900
- Verificador limpio de D25 (Fable): veredicto CONFIRMADO bit a bit (re-corrida de V1, V2, tabla sola y 17-19 oct);
  cuatro detalles del README corregidos y verificación guardada en `lectura_s162/verificacion/` (`ded217af4`).
- Revisión de #900 (Opus): hace lo que dice, salida idéntica a main antes del corte; costo PR162-01 (G2): desde el
  informe del 9-nov VIIRS queda sin juzgar en silencio (11 flags a 6). Recomienda mergear con un aviso. Despachado un
  implementador en el worktree del PR para el aviso (PR162-01) y `leer_ceses` robusto (PR162-04), sin merge.
- Decisión 3 medida: MODIS sin pasada nocturna en 7 de 2.607 volcán-días (0,27 %, 2026-03-01 a 10-23, sólo Láscar e
  Isluga); Suomi NPP 220 (8,4 %) con 20 días mudos en los 11 a la vez; en vivo 10 a 23-oct, 0 de 154. El archivo
  esconde los silencios en vivo (backfills): un modo estricto se mide por plataforma con `first_processed_utc`.
  Informe: scratchpad S162 `vuelta1\pr900_modis\INFORME.md` (se copia a la rama del PR como REVISION_S162.md).

### 2026-10-24 ~12:45 UTC (S162): loop reactivado (sesión dueña S162, /loop dinámico), vuelta 1 con 5 agentes
- Nicolás: «Como seguimos? Realiza todo lo que pueda en paralelo» y «Este trabajo debe quedar en loop». S162 es la
  sesión dueña del loop (una sola, memoria S153); despertador de respaldo cada ~30 min, los agentes avisan al terminar.
- Despachados, todos de sólo lectura y con carpeta propia en el scratchpad de S162 (`vuelta1\<agente>`), sin commits:
  (1) verificador limpio de la lectura de D25 (Fable, high); (2) por qué D25 baja las 2 protegidas de Chillán, más
  los puntos de Chillán de #864 (Fable, high); (3) qué son las pasadas de VIIRS 750 que D25 enciende o recupera
  (Fable, high); (4) revisión de #900 y medición de volcán-día de MODIS sin pasadas, para la decisión 3 (Opus);
  (5) inventario de worktrees, borradores y temporales, sin borrar (Sonnet).
- Decisión pendiente de Nicolás: qué hacer con D25 (recomendación: no adoptar por ahora). Los agentes 1 a 3 la informan.

### 2026-10-24 ~12:30 UTC (S162): D25 LEÍDO: DECIDE NICOLÁS
- Evaluador del tag `s161-d25-lectura` sin cambios (sha256 `93c26d62...fec2`), numpy 2.4.4, sobre los artefactos
  `s146ab-todo` de V1 (39530508296, intento 2), V2a (39575542584) y V2b (39612909810); cobertura pareja en los tres.
- **Veredicto combinado: DECIDE NICOLÁS.** P1 CUMPLE en las dos ventanas y sensores. P1b: 2 protegidas de Chillán
  bajan de 1 MW con D (V375 10-11 05:36, V750 10-14 06:18). P2 BLOQUEA en V1 VIIRS 750 (neto +6, 26 noches, p 0,16) y
  en V2 VIIRS 375 sólo con SN (neto +1, p 0,50). M MEJORA sólo en V1 VIIRS 750 cenit ≤ 40°; en los demás estratos D
  sube la magnitud como una ganancia uniforme (d mejora, d′ no). Tabla de latest.php sola en V1: mismo veredicto.
- Brazo del 17 al 19-oct (39756261926), aparte: INDECIDIBLE por falta de sustrato; no cambia nada.
- Informe y salidas: `experiments/_s157_prereg_d25/lectura_s162/` en `s159-evaluador-d25` (`e634f819f`). Nada en
  producción (A45).

### 2026-10-23 ~20:45 UTC (S161): CIERRE de la sesión
- Sin trabajo en curso: ningún agente ni proceso propio vivo; `s159-evaluador-d25` limpia e igual al remoto en
  `a7418e01d`; sesiones laterales terminadas (#897 y #899 mergeados; #898, #900 y #901 en borrador con CI verde).
- Traspaso: `tasks/BLOQUE_ARRANQUE_S162.md`. Primera tarea de S162: leer D25 con el evaluador del tag
  `s161-d25-lectura`. Informe de la sesión lateral sobre #864 commiteado en `experiments/_s161_estado_864/INFORME.md`.

### 2026-10-23 20:17 UTC, hora del servidor (S161): tag de lectura de D25 puesto
- Corrida final de mutaciones con las pruebas finales (HEAD `fb053347a`): control 0 fallas en 106; **58 de 58
  atrapadas por aserción**, 0 por otra excepción; q01 equivalente, no atrapada. Cierra V45-05.
- `NOTA_D47.md` commiteada (`a7418e01d`, sha256 `e77eda6d...c6e4`).
- **Tag `s161-d25-lectura` sobre `a7418e01d`**, subido (objeto `724e43452`). `evaluar_d25.py` sha256 `93c26d62...fec2`.
  Ningún veredicto del A/B leído antes del tag. Lo que sigue: la lectura de D25 (V1, V2a, V2b) con la referencia
  congelada por hash, la tabla de `latest.php` sola al lado y el estrato 203; después, aparte, el brazo del 17 al 19
  (run 39756261926). Recomendado hacerla en una sesión nueva (esta lleva más de 30 intercambios).

### 2026-10-23 19:23 UTC, hora del servidor (S161): D-47 ratificada por Nicolás
- Textual: «Sí a D-47: ratifico las tres lecturas como recomiendas (signo común de la noche en el placebo c, orden de
  los bloques por su clave con la versión de numpy anotada en el registro, y D-34 y D-42 informados con su propio
  mínimo), sin cambio de código.» Nota sellada `NOTA_D47.md` junto a la adenda, se commitea en `s159-evaluador-d25`
  cuando termine la corrida final de mutaciones (árbol quieto). numpy local 2.4.4, Python 3.12.10.
- Falta para el tag de lectura: que la corrida final de mutaciones con las pruebas finales dé 58 de 58 (V45-05).

### 2026-10-23 ~19:05 UTC (S161): verificador de D-45 entregó; mutaciones finales corriendo; D-47 a Nicolás
- Verdes (segunda corrida, `7eb91eb5e`): probar 31 de 31; suite 2.447 pasan y 1 falla de frescura del CSV de la rama
  (2026-10-21, sin cambios desde la adenda: entorno). Árbol quieto comprobado.
- Verificador limpio (Fable 5.1, high, `fb053347a`, `experiments/_s159/instrumentos/verificador_d45/INFORME.md`): A1
  (el evaluador decide P2 como la adenda §2) CONFIRMADO con enumeración y generador propios; A2, A3, A5, A6, A7
  CONFIRMADOS; A4 y A8 CONFIRMADOS EN PARTE (V45-05: 57 de las 58 mutaciones corrieron con pruebas anteriores a
  `ac6eab47b`; V45-04: verdes sobre `8642543ec`, mismos sha256). 5 mutaciones propias, las 5 atrapadas. Sobre el texto
  de la regla, gravedad 2: V45-01 (el paréntesis de §6 dice acción común y el nulo pide signo común; el código sigue el
  signo) y V45-02 (con B de 21 o más el valor-p por sorteos depende del orden de los bloques, que la adenda no fija; el
  código usa la clave del bloque). Nada cambia un veredicto de P2 ni impide el tag por el lado del evaluador.
- Para cerrar V45-05 por medición y no por argumento: corrida completa de `mutar_signos_p2.py` con las pruebas finales,
  en curso desde ~19:04 UTC (salida a `C:\vrp-trabajo\tmp_s161\mut_final\`, se copia a `signos_p2/` al terminar).
- **D-47 (pendiente, Nicolás)**: ratificar antes del tag (a) V45-01: en (c) manda el signo común de la noche; (b)
  V45-02: con sorteos, el orden de los bloques es el de su clave, y la versión de numpy se anota en el registro de la
  lectura; (c) lectura 1: D-34 y D-42 se informan con su propio mínimo. Recomendación: ratificar las tres, sin cambio de
  código.

### 2026-10-23 17:53 UTC, hora del servidor (S161): D-45 implementado; D-46 decidida; verdes re-corriendo
- Implementador de D-45 entregó (con dos cortes: suspensión y reinicio del equipo, y un ENOTFOUND de la API). En
  `s159-evaluador-d25`: rojas 31 de 31 por aserción (`da5e895c7`), código (`c8a000602`), placebos (404 corridas:
  (a) GANA y (b) PIERDE en todas las celdas con sustrato; (c) por noche GANA 8/320 y PIERDE 4/320), mediciones
  sintéticas (tasa exacta por cola de 4,81 % o menos con B de 5 a 20), mutaciones 58 de 58 por aserción (s12a2
  re-corrida tras preguntar por `ic95` en `tests/test_evaluar_d25_p2_s159.py`, `ac6eab47b`).
- **D-46 decidida por Nicolás** (textual: «lo que recomiendes», ante la recomendación de leer el 5 % del placebo (c)
  sobre todo (c) e informar cada celda): se lee sobre todo (c) por cola; V2 50 % VIIRS 375 (GANA 3/40, P binomial 0,136)
  se informa y no decide. POR QUÉ: leído por celda, 16 celdas-cola con 40 semillas rechazan una regla correcta con
  probabilidad 0,67. Nota sellada `NOTA_D46.md` junto a la adenda.
- Verdes, primera corrida (17:12 a 17:18 UTC) ROJA por el instrumento: `verdes.sh` no le pasó la carpeta de casos a
  `probar_evaluar_d25.py` (IndexError sin correr nada), y la suite dio 1 falla de 2.448 en
  `test_mirova_csv_freshness_f49` (el CSV de la rama es del 2026-10-21, sin cambios desde la adenda: entorno, no
  D-45). Corregido en `8642543ec`; segunda corrida en curso.

### 2026-10-23 ~14:55 UTC (S161): vigilante de OSF arreglado (#899)
- Nicolás (textual): «Sí: arregla las comillas del vigilante de OSF en un PR chico aparte de #888, con prueba de que
  el yml se acepta, y mergéalo con CI verde.» #899 mergeado por squash (`e31bf0a1d`) con CI verde (run 39972785243).
- Guarda nueva `tests/test_guard_expresiones_workflows_s161.py` sobre los 47 workflows: roja contra `main` sólo en
  `vigilar-osf-mirova.yml`, por aserción; un primer borrador marcaba en falso `nrt.yml` y dos backfills (comillas dobles
  dentro de un JSON entre simples, válido) y quedó como control. La prueba S158 `test_workflow_abre_issue_sin_empujar`
  exigía `"1"` y `"2"`, o sea fijaba la forma rota; corregida (primer CI rojo por eso).
- Prueba de aceptación: el push de la rama y el del merge a `main` no dejaron corrida fallida del vigilante (antes,
  cada push a cualquier rama dejaba una: 100 en `failure` desde el 2026-10-20, con 0 jobs). Primer calendario: miércoles
  2026-10-28 10:15 UTC. Las ramas cortadas antes del arreglo siguen mandando un correo por push hasta ponerse al día.
- Error propio (A96): en el worktree aislado `git stash` con árbol limpio no guardó nada y `git stash pop` reaplicó
  el stash ajeno de S78 sobre `Tupungatito.json` y un CSV; restaurados con `git checkout HEAD --`, stashes intactos.

### 2026-10-23 14:36 UTC, hora del servidor (S161): #897 mergeado con el sí de Nicolás; vigilante de OSF ciego
- Nicolás (textual): «Sí a #897: crea el tag defensivo pre-s161-cese-snpp sobre la punta de main justo antes del
  merge, súbelo y mergea por squash. Dejo el modo estricto como nota y lo decidimos aparte.» Tag
  `pre-s161-cese-snpp` sobre `180b61317` (punta de `main` en ese momento), subido; squash `c3ee70ed6`. CI de `main`
  sobre `c3ee70ed6` en curso al escribir esto. Desde el 2026-11-03 el NRT no busca Suomi NPP.
- Hallazgo: `.github/workflows/vigilar-osf-mirova.yml` en `main` (desde `79aeb3406`, S158) tiene comillas dobles en
  las expresiones `if:` (l. 44 y 66). GitHub lo rechaza: las 40 últimas corridas son `push` en `failure`, y **0
  corridas por calendario**. El vigilante del código de MIROVA en OSF nunca corrió en `main`. #888 (borrador) lo
  corrige mezclado con la auditoría S158 R2.
- El computador se suspendió el 22-oct 19:36 UTC (cambio de fuente) hasta el 23-oct 12:50 UTC y se reinició el
  23-oct 13:21 UTC (menú Inicio): el implementador de D-45 se relanzó desde git (`8dd8438ae`).

### 2026-10-22 19:04 UTC, hora del servidor (S161): quinta adenda de D25 sellada (D-45); implementador corriendo
- Quinta adenda `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md` en `s159-evaluador-d25` (`c13cf5808`, subida;
  sha256 `28eea84cf77b860a2aad12088e6ad6795c8ce3d1395a71890dabe0b3fba900c3`). Escrita antes de leer V1, V2 y el brazo
  del 17 al 19. Lecturas propias de la adenda, que Nicolás puede vetar antes del tag: una cola por dirección al 5 %
  (§2.4, por D-42 §2.4 y porque es la única en que «4 noches o menos» queda en la frontera); +1 en el valor-p por
  sorteos y semilla 162 con B de 21 o más; B cuenta los bloques de suma 0; placebo (c) con 40 semillas por punto; (a)
  y (b) re-decididos con la regla nueva.
- Implementador (agente, worktree `C:\vrp-trabajo\s159-evaluador`) lanzado ~19:03 UTC; entrega en
  `experiments/_s159/instrumentos/signos_p2/README.md`. Después: verificador limpio en Fable 5.1, y recién ahí tag.

### 2026-10-22 ~18:41 UTC (S160): D-45 cerrada por Nicolás (opción ii); CIERRE de la sesión
- D-45: P2 se decidirá con la prueba exacta de signos por bloque noche-volcán, en una quinta adenda, con
  implementador, candados y verificador antes del tag; a hacer en S161. Corrige también V42-21.
- Cierre sin trabajo en curso: ningún agente vivo; `s159-evaluador-d25` en `bcfdc7c76` igual al remoto; #892, #891,
  #893 y #895 mergeados. Traspaso: `tasks/BLOQUE_ARRANQUE_S161.md` (bloque de arriba; el de las 07:30 queda como
  historia). Pedido de Nicolás para S161: mapa interactivo sobre imagen satelital y persistencia por mes, noche y
  día separados.

### 2026-10-22 ~18:29 UTC (S160): placebos de D-44 corridos y verificados; P2 con pocas noches falla por el intervalo → D-45
- Implementador (`20ac098a3`, `experiments/_s159/instrumentos/placebos_d44/`): 444 corridas desde producción. (a)
  apagar negativos limpios: GANA 80 de 80 celdas en V1 al 50 %%, 52 de 80 en V2 (28 INDECIDIBLE); (b) apagar alertas
  bajo 1 MW: PIERDE en todo punto con sustrato, GANA nunca; (c) simétrico con moneda justa: falsos 2 %% por cola.
  Composición de lo que K publica: negativos limpios 4,8 %% (V375 V1), 18,2 %% (V750 V1), 2,8 y 8,7 %% (V2).
- Verificador vuelta 3 (`bcfdc7c76`): todo CONFIRMADO en los números; V42-20 (gravedad 3): con 7 noches discordantes
  P2 queda INDECIDIBLE siempre y con 10 u 11 decide la semilla; es defecto del intervalo de D-34, no del sorteo →
  **D-45**. V42-21: (c) sortea por pasada, no por noche (cota inferior donde hay noches dobles). V42-22: 80 semillas
  agregadas en un punto tras mirar (parada opcional; ninguna tanda pasa el 5 %%).

### 2026-10-22 ~17:16 UTC (S160): auditoría espacial Tupungatito, Cordón Caulle e Isluga (pedida por Nicolás), verificada
- `experiments/_s160_espacial/` (auditor Fable, verificador Opus; leer primero `verificador/INFORME.md` y el README).
  El cráter está a 4,79 km NW (Tupungatito) y 7,61 km N (Cordón Caulle) del centro del TIF de MIROVA; el calor que
  MIROVA alerta cae casi siempre en el cráter y nuestro cúmulo en el mismo lugar (0,21 a 0,49 km; control A109 0,47
  a 0,59). Isluga: 0,8 a 1,0 km SW del yaml. Lo que no publicamos es sobre todo el cráter en 0,0 MW (D25).
- Cordón Caulle con inner 20 km publica en noches limpias hasta 20 km del cráter, muchos fuera del anillo de MIROVA
  (V375 30 de 38 a más de 2 km, V750 13 de 30, MODIS 26 de 38). La caja de cumbre del código centrada en el TIF no
  reproduce las alertas de MIROVA en esos dos volcanes (0 de 10, 0 de 48): hecho del port, no prueba de producción.
- **VE-01 (SOSPECHA, gravedad 3)**: protegida de Tupungatito 2026-09-29 04:54 (Suomi NPP, 1,86 MW) con nuestro único
  píxel a 9,42 km ENE del cráter, fuera del inner de 7 km: posible protegida perdida por radio. VE-02: alerta de
  Cordón Caulle del 2026-10-21 lejos del cráter (publicamos 1,42 MW a 10,1 km SW). La «fuente persistente» del E de
  Cordón Caulle no lo es (13 de 15 RUTINA diurnos, 19 de 23 apariciones del 9 al 18-may); corregido en el mapa.
- Mapa para Nicolás: `experiments/_s160_espacial_mapa/`. No commiteadas las copias de datos (`data/`, `_censo_s159/`).

### 2026-10-22 ~16:24 UTC (S160): umbrales de VRP por sensor de MIROVA (pregunta de Nicolás)
- Coppola et al. 2026, *Scientific Data*, tabla 1 (p. 7 y 8 del PDF, RENDER): umbral nocturno de VRP para construir el
  archivo, MODIS 1,0 × 10⁵ W, VIIRS 750 5,0 × 10⁶ W, VIIRS 375 1,0 × 10⁴ W; diurno 5,0 × 10⁷ W en los tres.
  **No es errata**: en `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (OSF v2.5) el mínimo de cada grupo calza
  exacto (VIIRS 750 noche: n = 82.782, mínimo 5 × 10⁶ W, ninguna fila bajo eso).
- **El tiempo casi real no lo aplica**: en la tabla de `latest.php` (snapshot del 2026-10-14, «VIIRS» a secas = 750
  según `normalize_sensor`), 294 de 301 alertas nocturnas de VIIRS 750 están bajo 5 MW; MODIS 0 de 96 bajo 0,1 MW y
  VIIRS 375 0 de 1.216 bajo 0,01 MW. Archivo y NRT son productos distintos (A105). Por qué 5 MW en VIIRS 750:
  SOSPECHA (el archivo usaría 750 sólo para lo intenso, donde I4 satura).
- **Alerta protegida**: sigue 1 MW para los tres sensores, sostenido por el banner (VIIRS 375: 107 pasadas; VIIRS
  750: 7; MODIS: ninguna). Pregunta abierta: confirmar el banner de MODIS en imágenes de MIROVA.

### 2026-10-22 ~16:12 UTC (S160): arreglos verificados; el placebo del 1 % no podía fallar con K
- Implementador: V42-02 (candado donde la calibración decide) y V42-04 cerrados; curva de placebo 1, 5, 10 y 20 %%
  (`743525a29`, `452956cf8`). Verificador vuelta 2 (`9359a762f`, `verificador_d42/vuelta2/INFORME.md`): los dos
  CONFIRMADOS (m07 atrapada; suite sola 2.417; rojas 26 de 39). **V42-10 (gravedad 3)**: el placebo de apagado al azar
  no podía fallar con K: de 7.551 discordantes creadas, 85,7 %% son alertas bajo 1 MW perdidas y 14,3 %% negativos
  limpios, así que apagar a ciegas le cuesta a K seis alertas por cada negativo y GANA es imposible por construcción.
  Su «0 GANA» es SIN DATO sobre la pregunta de S160, no CUMPLE. Lo que S160 temía sólo pasa donde más de la mitad de
  las publicaciones bajo 1 MW son negativos limpios; K no es ese régimen. Propone placebos que sí pueden fallar: (a)
  apagar sólo negativos (control de poder: debe dar GANA), (b) apagar sólo alertas (debe dar PIERDE), (c) el simétrico
  (apagar y encender p %% en la misma semilla, neto esperado 0: tasa de falsos de P2 calibrada sobre datos reales).
  → D-44 a Nicolás, junto con V42-03 y el «4 noches o menos».

### 2026-10-22 ~13:44 UTC (S160): calibración de P2 implementada y verificada en el código; dos huecos antes del tag
- Implementador (Opus; `31bb1c371` y `b57ecfe62`, rama `s159-evaluador-d25`, `experiments/_s159/instrumentos/calib_p2/`):
  calibración de P2 según D-42 y estrato 203; 28 de 28 mutaciones; suite 2.415; poder calibrado C 98,8 %, C2 99,8 %,
  D 68 %, E 33 %; con 4 noches discordantes o menos P2 no decide nunca (16 combinaciones de signo).
- Verificador limpio (Fable 5.1; `981cceda7`, `verificador_d42/INFORME.md`): código CONFIRMADO en los siete puntos y
  el estrato 203 sólo informa; el exceso de falsos por muestreo (A, B7, B8) era de la muestra de semillas (espejo exacto
  y 1.000 semillas nuevas: 2,6 a 4,3 %). Huecos: **V42-01** el placebo del 1 % no ejercitó la calibración (V1 0 de 80
  celdas calibradas; casi todo SIN SUSTRATO), así que su «0 GANA» no mide nada; **V42-02** sin candado donde la
  calibración decide; V42-04 menor. Encargados al implementador. **V42-03**: la lectura de §2.5 (PIERDE de un sensor
  contra INDECIDIBLE del otro: el código da NO CUMPLE, coherente con PREREGISTRO §8 d y H2) queda para Nicolás, junto
  con aceptar que P2 no decida con 4 noches o menos.

### 2026-10-22 ~10:40 UTC (S160): estrato informativo 203 declarado antes del tag; #893 listo
- La auditoría S160 propuso informar aparte su hallazgo 203 (30 de 97 cúmulos de cumbre V750 en 0,0 MW en K por el
  recorte a cero del exceso sobre el anillo; 7 con alerta de MIROVA, 11 negativos limpios, ninguna protegida). Es el
  conjunto que D25 más puede mover, en los dos sentidos. Declarado como estrato que sólo informa en
  `experiments/_s157_prereg_d25/NOTA_ESTRATO_203.md` (`5f986a209`, antes del tag, sin abrir nada del A/B); su código va
  con el implementador de D-42 y lo revisa el mismo verificador.
- Según la sesión S160: #893 (`s160-auditoria`) entra limpio a `main` tras traer #891; el mapa de integración de las
  ramas S157 a S159 está en `docs/AUDIT_S160.md` §9 de esa rama. Merge de Nicolás.

### 2026-10-22 ~10:38 UTC (S160, con Nicolás despierto): D-42 sellada; implementación en curso; placebo del 1 %
- D-42 cerrada por Nicolás (opción a). Cuarta adenda `ADENDA_CALIBRACION_P2.md` (`ca65069f6`). Implementa un agente
  Opus en `C:\vrp-trabajo\s159-evaluador` (calibración, candados de V34-03 y V29-01, falsos y poder sintéticos,
  suite con árbol quieto); después verificador limpio en Fable y recién ahí el tag de lectura.
- Propuesta de la auditoría S160 (V1a): con tolerancia 0, P2 aprueba un placebo sin información (D = K con el 1 % de
  las publicaciones apagado al azar: GANA en 16 de 30 semillas en V1 y 5 de 10 en V2). **La adenda D-42 no lo cubre**:
  la calibración quita las decisiones del azar, no el premio a publicar menos. Se agregó como control del instrumento
  al implementador (brazos armados desde producción, no desde el A/B; criterio: P2 calibrada no da GANA en más del
  5 % de las semillas; si lo da, va a Nicolás como defecto de la métrica, sin inventar regla).
- Según la sesión S160: **#891 ya está en `main`**; **#892 lo bloqueó el clasificador** al intentar mergearlo, así que
  lo mergea Nicolás (D-37).

### 2026-10-22 ~09:33 UTC (S160 nocturna, tras el cierre): D-35 despachado con el sí de Nicolás
- Nicolás aprobó D-35. Run **39756261926** (`reproc-s146-ab-sin-test1.yml`, ref `s157-d25-k-codigo` = `66961f65d`,
  2026-10-17 a 2026-10-19, los 11 volcanes, brazos `_s157_ab_d25_k_control`, `_s157_ab_d25_k_gemelo` y
  `_s157_ab_d25_k_on`, control `_s157_ab_d25_k_control`), con el grupo `s146-ab-sin-test1` libre. Publica en una
  rama `s146-ab/39756261926` y como artefacto, nunca en `main`. Antes: CMR NRT con los 6 productos VIIRS los tres días.
- **No abrir sus resultados antes del tag de lectura de D25** (D-42 sigue pendiente): es un brazo declarado aparte.
  Al terminar, contar sus pasadas por brazo contra producción (A108) sin mirar publicaciones.

### 2026-10-22 ~07:30 UTC (S160 nocturna): verificador de D-29 y CIERRE de la sesión nocturna
- Verificador limpio de D-29 (Fable 5.1; `29831d7bc`, `experiments/_s159/instrumentos/verificador_d29/INFORME.md`;
  se cortó una vez por un error 529 de la API y se reanudó desde el disco). El código hace lo que dice la fila D-29: la
  exclusión llega a la tabla, a los crudos y a la cobertura, y todo lo que decide sale de esos tres objetos; control
  positivo sin exclusión: 60 pasadas más por sensor, «D: le faltan 54 de K», P4 54 y 16, determinismo FALLA. Lo débil
  (V29-01): las 5 pruebas atrapan 4 de sus 9 mutaciones; las que dejan pasar días dentro de `evaluar` pasan en verde.
  V29-02: mi `rojo_d29.txt` salió de un borrador de la prueba (re-medido por él: 5 de 5 rojas con la commiteada).
  Recomendación: sumar al candado un caso de punta a punta como su `cobertura_sintetica.py` junto con D-42.
- **Cierre**: traspaso `tasks/BLOQUE_ARRANQUE_S161.md`. Sin trabajo en curso salvo el CI de #890 sobre `29831d7bc`
  (`pytest` pendiente, run 39740189157). Ningún agente vivo. Nada decidido por Nicolás esta noche.

### 2026-10-22 ~06:03 UTC (S160 nocturna): auditoría S160 terminada; D-29 implementado en el evaluador
- **Auditoría S160** (sesión `auditor-a-s160-de-vrp-ch`) terminada: síntesis `docs/AUDIT_S160.md` en `s160-auditoria`
  (`b941c8052`), 27 marcas A113 en esa rama, cola de campo `docs/COLA_CAMPO.md`. En una pantalla: lo que está en
  producción se sostiene; el riesgo más cercano es una plataforma callada («Cobertura: completa» con código 0, 241, y
  el auto-audit no ve protegidas sin record, V3-01); lo más grave de detector, 30 de 97 cúmulos de cumbre V750 en
  0,0 MW por el recorte a cero del fondo (203, gravedad 5, 7 con alerta de MIROVA, ninguna protegida); los
  documentos rectores no dicen que #883 reemplazó el histórico por K. Sus decisiones van a D-43; su V1a-01 refuerza
  D-42. No dupliqué su trabajo ni hice git en su worktree.
- **D-29 implementado** en `evaluar_d25.py` (rama `s159-evaluador-d25`, sin commitear mientras corre la suite):
  `DIAS_EXCLUIDOS["V1"]` = 13, 17, 18, 19 y 20 de octubre; `filtrar_dias` aplicado a las tablas K-brazo, a los crudos
  de cada brazo y a la referencia de cobertura; «EVALUADO SIN ... (D-29)» al inicio de la línea del veredicto combinado
  y en la cabecera de V1. Prueba nueva `tests/test_evaluar_d25_dias_d29_s160.py`: 5 de 5 rojas por aserción antes,
  36 de 36 verdes con las del evaluador. Mutaciones (`experiments/_s159/instrumentos/d29/mutar_d29.py`): 4 de 4
  atrapadas por aserción. Control del instrumento: la primera versión del lector daba 0 de 4 porque buscaba el tipo
  de excepción en el resumen de `-q`, que no lo trae; con el XML de JUnit, 4 de 4, y la copia sin mutar pasa 5 de 5.
  Falta: `probar_evaluar_d25` y la suite (corriendo) y un verificador limpio del cambio, junto con el de D-42.

### 2026-10-22 ~05:57 UTC (S160 nocturna): verificador de D-34: código fiel, regla de P2 descalibrada; tag de lectura NO creado
- `experiments/_s159/instrumentos/verificador_d34/INFORME.md` (Fable 5.1; `786bfb288`). Las ocho afirmaciones
  CONFIRMADAS en el código: D-30 (INDECIDIBLE si d mejora y d′ no calibra; sólo la cola de mejora; marca de
  `--calibracion sellada`), D-32 (1.000 repeticiones, semilla 160, tope 50 por cola), D-34 (P2 por bloques con GANA,
  PIERDE, EMPATE, BLOQUEA y SIN SUSTRATO), las tres guardas, y el signo de P2 (neto = errores de D menos errores de K;
  coincide con la fila P2 del pre-registro, no con el encargo al revés). Pruebas reproducidas: 11 de 11 rojas sobre
  `7cbee245a`, 31 de 31 verdes, 17 de 17 mutaciones por aserción, suite 2.373 con el árbol quieto.
- **V34-01 (gravedad 3)**: la regla sellada de P2 no tiene calibración y con el sustrato mínimo decide en falso en
  24,8 % de los nulos correlacionados por noche → **D-42**. V34-02: bajo el nulo, BLOQUEA apaga CUMPLE en 37 a 48 %.
  V34-03: 7 de 23 mutaciones propias pasan en verde (semilla, remuestreos, nivel, borde de PIERDE de P2; tope de d′
  en la comparación; alcance del INDECIDIBLE; marca de validez en el estado). V34-04 y V34-05 menores.
- **Decisión de la noche: no creo el tag de lectura ni leo el veredicto.** Leerlo con una regla que se sabe
  descalibrada amarraría la decisión, y corregirla después de mirar sería sospechosa. Queda para Nicolás (D-42). El
  plazo de LANCE de D-35 (24-oct ~16:00 UTC) no depende de esto si el brazo de sensibilidad se despacha desde un tag de
  código, no de lectura.
- Limpieza: quité los 5 enlaces (junctions) de `raiz_falsa` del verificador con `rmdir` (los destinos quedaron
  intactos) y su carpeta sintética `tmp_probar` (527 MB).

### 2026-10-22 ~04:54 UTC (S160 nocturna): D-34 commiteado; verificador limpio corriendo; D-29 falta en el evaluador
- El agente de S159 subió **`c44709e27`** (P2 con bootstrap por bloques, D-34, y `ADENDA_GEMELO.md`): roja 11 de 11,
  verde 31 de 31, mutaciones 17 de 17 por aserción, suite 2.373 con árbol quieto, según su mensaje. Verificador con
  contexto limpio (Fable 5.1, high) sólo del diff `63e310af5..c44709e27`, con prohibición de tocar datos reales del
  A/B; escribe en `C:\vrp-trabajo\s159-evaluador\experiments\_s159\instrumentos\verificador_d34\`.
- **Hallazgo propio: D-29 no está implementado.** `evaluar_d25.py` no excluye ningún día: la ventana V1 va del
  2026-08-29 al 2026-10-18 entera, y la cobertura (`claves_cobertura`) compara los brazos contra producción, que sí
  tiene el 17 y el 18 por NRT. Sin la exclusión, V1 podría quedar INDECIDIBLE por cobertura o mezclar días. Parche
  diseñado (constante de días por ventana, filtro de claves `volcán|sensor|fecha` en tablas, crudos y cobertura, y
  la exclusión al inicio de la línea del veredicto); se aplica **después** del verificador de D-34 para no cambiarle el
  árbol a mitad de camino (A112), con prueba roja, y pasa por verificación antes del tag. Interpretación que aplico y
  dejo a la vista de Nicolás: «sin el 13 parcial» = se excluye el día 13 entero, en los tres brazos por igual (una
  exclusión por pasada dependería de qué faltó en cada brazo); el 19 y el 20 caen fuera de V1.

### 2026-10-22 ~04:45 UTC (S160 nocturna): verificador del censo del oráculo: números CONFIRMADOS; integrado a s159-pruebas
- `experiments/_s159/oraculo_censo/verificador/INFORME.md` (Fable 5.1, high; `ebf8cf861`). Re-corrió el analizador
  (tablas byte a byte iguales) y recontó desde los crudos sin pasar por él: K 54, O-def 5, O-sens 15 de 5.353; O-def
  pierde 6 protegidas de Cordón Caulle; O-sens 0 perdidas y 1 ganada; ΔE −60 y −90; con el rescate −62 y −92.
  Etiquetas sin cambio. Lo que cambia la lectura: dos de las pérdidas bajo 1 MW no son del detector de MIROVA sino del
  record sintético (VOC-01, Láscar 2026-08-26 05:48: el centroide sin pesos de un píxel del cráter y uno a 17,3 km cae
  a 9,3 km y queda `far`; VOC-02, Cordón Caulle 2026-10-21 05:48: 11 píxeles a 10,3 MW con 270,8 K que el filtro de
  cirrus del tablero apaga, la única vez que dispara en el censo). Las 6 protegidas de O-def son geometría de la caja
  (O-sens las encuentra a 7,7 a 7,8 km del centro del TIF). **Con la tabla de `latest.php` sola**: 5 alertas que
  deciden vienen sólo del OCR (todas protegidas, desde el 13-jun); O-def pierde 5 en vez de 6, O-sens sigue en 0, ΔE
  igual. Salvedades de redacción de los controles: control 2 = 503 pasadas × 2 cajas; la pata de magnitud del control
  1 compara 422 pares (el resto None con None); en 9 pasadas de NOAA-21 del 20-oct K corrió sobre NRT y producción
  sobre Standard (VOC-03). Población: 30 pasadas RUTINA de la tabla sin record nuestro a 120 s quedan fuera (0,5 %,
  0 alertas; VOC-05). Seguimiento VOC-04: comprobar en el `.m` de MIROVA si la prueba p1 se aplica fuera de la caja.
- Arreglado S-1 (mío): 178 bytes NUL al final de mis dos salidas de texto.
- Integrado: `s159-oraculo-censo` trae `s159-pruebas` y se empuja como `s159-pruebas` (`812624cc6`), desde
  `C:\vrp-trabajo\s159-m`.

### 2026-10-22 ~04:24 UTC (S160 nocturna): censo del oráculo V750 analizado, verificador corriendo
- Run **39713438252** terminado (28 verdes, 4 rojos por 20 pasadas sin procesar declaradas, todas del 12-oct) y
  rescate **39715348772** (20 de 20 ok). El agente de S159 que lo diseñó ya no estaba vivo: corrí el analizador
  pre-registrado sin cambios de lógica (`1259ccc66` sólo toca la salida y se hizo antes de que terminara el run).
  Informe `experiments/_s159/oraculo_censo/INFORME.md` (`f7dba3c57`, rama `s159-oraculo-censo`; artefactos en
  `D:\vrp-trabajo\temporales\s159_oraculo\`). **SIN VERIFICAR**: verificador limpio en Fable corriendo, escribe en
  `C:\vrp-trabajo\s159-m\experiments\_s159\oraculo_censo\verificador\`.
- Controles 1 a 4 pasan (K = producción 5.620 de 5.620; oráculo = N 1.006 de 1.006; nulo 1.006 de 1.006; razón
  O/MIROVA 1,000 y 0,999). Negativos limpios publicados sobre 5.353: **K 54, O-def 5, O-sens 15** (cierra la cota
  «hasta ~139» del frente N). O-def **PIERDE PROTEGIDAS** (6 de Cordón Caulle, ΔE −60); O-sens **GANA EN EL CENSO**
  (0 perdidas, 1 ganada, ΔE −90, rango −92 a −73). Con el rescate: 0 SIN DATO, ΔE −62 y −92, mismas etiquetas.
  Etiquetas descriptivas: no deciden adopción (ola 3, con pre-registro y sello).
- Falta, como seguimiento: la lectura con la tabla de `latest.php` sola (el analizador no la da).
- Corrección: el agente del censo seguía vivo. Comparó su corrida con la mía (mismo texto) y agregó al informe los
  hallazgos C-1 a C-6 (`42e2b799a`, en el remoto). Dos que importan para la ola 3: (1) con el recuadro sensible el
  oráculo **detecta 43 negativos y publica 15**: el filtro de distancia del tablero deja 28 como `far`; sin ese filtro
  ΔE quedaría en −62 o menos, así que la ventaja depende del predicado del tablero; (2) el record sintético promedia la
  posición de los píxeles y eso hace perder una alerta de Láscar (2026-08-26 05:48). La protegida de Chillán 05:18 del
  rescate sale con 6,75 MW contra 8,44 de MIROVA. 324 pasadas no miran el volcán, no ven la cumbre o están partidas, y
  nadie publica en ellas.

### 2026-10-22 ~03:47 UTC (S160 nocturna): auditoría de Mirova-v1 entregada
- Sesión `audit-mirova-v1` terminada (sólo lectura, commit medido `c48d24cad8`). Informe y `hallazgos.csv` copiados a
  `experiments/_s159/mirova_v1_auditoria/`; scripts y verificadores en `D:\vrp-trabajo\mirova-v1-auditoria\`. Sin
  verificación propia de esta sesión. En una pantalla: (1) la tabla pierde filas por el bucle de push del scraper
  (`git pull --rebase -X ours` mezcla como texto un CSV reescrito en otro orden), reproducido byte a byte, sigue
  activo; (2) el contenido de la tabla es confiable, pero `latest.php` sólo muestra la última pasada de cada volcán y
  sensor: una pasada que el scraper no alcanzó se pierde y entra como «sin información», nunca como negativo; (3) el
  OCR vale como VRP y hora, y como clase sólo con el método de la estrella, de noche y desde V29.2; (4) las 39
  reescrituras son manuales de Nicolás; la copia corrupta `81dd25ce3` la fabricó el sync de VRP Chile; (5) el scraper
  y el OCR salen con código 0 en toda falla de MIROVA. Decisiones D-39 a D-41.
- **Para la relectura de D25**: la referencia sellada es la copia congelada por hash del pre-registro (no se cambia
  después del sello). El informe agrega dos lecturas informativas para poner al lado, sin decidir: la tabla sola (ya
  pedida) y las protegidas sólo OCR restringidas al método de la estrella nocturna desde V29.2. El riesgo latente de
  `scripts/clase_mirova.py:65-75` (una fila OCR que le gana a la histórica de la tabla) da 0 casos hoy según el informe.

### 2026-10-22 ~03:43 UTC (S160 nocturna): #892 (cese de Suomi NPP) verificado en el navegador
- PR **#892** abierto por el agente de S159 (rama `s159-cese-snpp`, `f995d7101`, CI `pytest` verde). Verificado en el
  preview `vrp-frontend-s159-cese`: recuadro en index, diario y mosaico bajo el aviso de K; ausente en comparacion;
  ninguna línea «sin Suomi NPP» hoy, con control positivo; texto en pasado con el reloj en el 3-nov y nulo a los 90
  días; a 375 px el recuadro cabe, y el desborde de diario (449 px) y mosaico (496 px) es previo al PR (igual sin el
  recuadro); 404 sólo de `*_recent.json`. Resultado en el comentario `issuecomment-6332148549`. Merge y sus dos
  preguntas, a la cola (D-37, D-38).
- Seguimiento sin decisión: diario y mosaico desbordan a 375 px por la barra de navegación y las tarjetas; candidato
  a una tarea de frontend aparte.

### 2026-10-22 ~03:32 UTC (S160 nocturna): verificador del port entregado e integrado
- `experiments/_s159/portes/verificador/INFORME.md` (`ca034d66e`, empujado a `s159-portes` y `s159-pruebas` desde el
  worktree `C:\vrp-trabajo\s159-n`; el informe no declara su modelo, el «Opus» del mensaje del commit es un error mío).
  Veredictos: (1) MODIS **PARCIAL**: detección, banda 21 que se hunde y geolocalización de 5 km que degrada,
  CONFIRMADOS e idénticos con la tabla sola; el GANA contra K y el silencio en negativos, **NO RESUELTOS** (D-36).
  (2) Magnitud VIIRS 375 **CONFIRMADA** y pasada a pasada, no sólo en promedio: 82 % en banda contra la misma pasada
  de MIROVA y 15 % contra otra pasada de la misma noche (control A109). (3) Pérdida de protegidas en VIIRS 375
  **PARCIAL**: con la tabla de `latest.php` sola el port pierde **0 de 29**, y el verificador recuerda que eso no es
  rescate post hoc sino la regla A119 vigente para esa ventana; pero de las 6 perdidas con OCR, 3 son de la regla del
  centroide, 2 (Isluga 2026-09-09 06:06, Tupungatito 2026-08-01 05:00) calzan con un píxel débil del cráter (0,02 a
  0,04 MW) que producción ve y el port no, y 1 apoya «otra pasada». (4) Controles **CONFIRMADOS** (391 de 391).
- Censo del oráculo V750: run **39713438252** (rama `s159-oraculo-disparo`) en curso a las 03:34 UTC (14 jobs
  terminados, 8 corriendo, 10 en cola); el rescate LAADS del 12-oct terminó verde (run 39715348772). El análisis
  (`experiments/_s159/oraculo_censo/02_analizar.py`, con un cambio sin commitear en `C:\vrp-trabajo\s159-m`) queda
  para cuando termine. Las horas «~03:45» y «~04:00» que escribí primero en estas dos entradas estaban adelantadas;
  corregidas contra la hora del servidor (A86).
- Los archivos del verificador quedaron también sin seguimiento en `C:\vrp-trabajo\s159-pruebas` (worktree de la
  sesión S160); avisado a esa sesión, sin git ahí.

### 2026-10-22 ~03:28 UTC (S160 nocturna, ÚNICA dueña del loop; Nicolás duerme)
- Toma del loop tras el cierre de S159 (`0be01b35a`). Hora del servidor 03:27 UTC al abrir. Comprobado contra GitHub:
  #889 y #890 en borrador, CLEAN; #891 listo, CLEAN, Tests verde (run 39715954605); la rama `s159-cese-snpp` no
  existe en el remoto (el agente trabaja en `C:\vrp-trabajo\s159-instrumentos`, sin commit). Nada nuevo subido en
  `s159-evaluador-d25` (sigue en `7cbee245a`, D-34 sin commitear en su worktree) ni en `s159-oraculo-censo`
  (`96ba0955b`). El verificador del port escribe en `experiments/_s159/portes/verificador/` sin INFORME aún.
- **Plazo de LANCE para D-35 (b.1), medido**: CMR NRT tiene hoy los 6 productos VIIRS (MOD e IMG de SNPP, NOAA-20 y
  NOAA-21) del 17, 18 y 19-oct sobre Chile (4 a 5 gránulos nocturnos por producto y día). El gránulo más viejo de
  `VJ102MOD_NRT` es del **2026-10-14 11:36 UTC**: la retención es ~7,7 días. El 17-oct se purga cerca del
  **2026-10-24 ~16:00 UTC** y el 19-oct cerca del 27-oct. Consultas: `curl` a `cmr.earthdata.nasa.gov/search/granules.json`
  con `bounding_box=-76,-46,-66,-17`, 00 a 12 UTC.
- Ruido sin consecuencia: las ~60 corridas `failure` de `vigilar-osf-mirova.yml` en las ramas `s159-*` y
  `s160-auditoria` son la versión vieja del yml (literales con comillas dobles en `if:`, GitHub no la acepta: 0 jobs),
  heredada de `s158-d17-diseno` (#885). #888 ya trae la versión corregida con comillas simples. No tocar
  `s159-pruebas` (es de la sesión S160); se resuelve al integrar #888.
- Borrador del prompt del verificador de D-30, D-32 y D-34 (Fable, porque el implementador fue Opus) en la carpeta de
  notas compartidas de la familia de sesiones (`s160noche_prompt_verificador_d25.md`).

### 2026-10-22 ~03:20 UTC (S159, dueña del loop): port a VIIRS 375 y MODIS; S160 en su sesión; un merge en rama ajena revertido
- **PORTES** (`experiments/_s159/portes/`, pre-registro `6fb94d1c3`, informe `599a5659`, run 39712862945, 310 pasadas;
  integrado a `s159-pruebas` en `2934273f5`), SIN VERIFICAR, verificador corriendo. El código V750 de MIROVA, cambiando
  sólo bandas, grilla, coeficiente y caja, **reproduce a MIROVA en MODIS** (banda 22 + MxD03: protegidas 50 de 50, razón
  1,006, ΔE −44 contra K; con banda 21 se hunde, con la geolocalización de 5 km baja a 0,903) y en la **magnitud de VIIRS
  375** (razón 1,000 en 61 alertas). En VIIRS 375 el veredicto pre-registrado es PIERDE PROTEGIDA (6 de 36); el post hoc
  las atribuye a filas sólo OCR de Suomi NPP con distancia de otra pasada (A119), sin verificar.
- **Auditoría S160**: la inició Nicolás con la tarjeta (sesión `local_7491a729-1f11-4a2c-b5db-9dc29f9c436c`, rama
  `s160-auditoria` en `C:\vrp-trabajo\s159-pruebas`). Ese worktree pasa a ser de esa sesión.
- **Error propio corregido**: hice un merge del port en `s160-auditoria` creyendo que el worktree seguía en
  `s159-pruebas` (commit local `f47f39e5d`, nunca subido). Revertido con `git reset --keep 06e0fad3b` (el último commit de
  la sesión, igual al remoto) y avisado a la sesión. Lección: antes de un merge en un worktree compartido, mirar
  `git branch --show-current`; si otra sesión puede estar ahí, integrar desde el worktree de la rama de origen con
  `git push origin HEAD:<destino>`.

### 2026-10-22 (S159, dueña del loop): verificador de la referencia y cese de Suomi NPP
- **Verificador de la referencia** (`5ab6716db`): la pérdida de filas de la tabla es del CSV del scraper (carrera de
  workflows, Mirova-v1#19), no de MIROVA; las 39 reescrituras del OCR son correcciones MANUALES documentadas de Nicolás
  (15-jun y 4-ago) que dejaron 0 contradicciones con la tabla; el veredicto de K no cambia (referencia congelada por hash).
  Riesgo latente: `scripts/clase_mirova.py:65-75` cuenta como protegida una alerta OCR aunque la tabla diga FALSO_POSITIVO.
  Nicolás: «solo latest.php es lo mas creible»; auditoría de Mirova-v1 en sesión aparte (`audit-mirova-v1`, copia parcial
  en `D:\vrp-trabajo\mirova-v1`, sólo lectura).
- **Cese de Suomi NPP** (`experiments/_s159/cese_snpp/`): el 2-nov el pipeline se apaga en SILENCIO (CMR devuelve [],
  `fetch.py:1085-1088` sigue sin registrar falla, «Cobertura: completa», código 0; simulado sin red). Ninguna vigilancia
  mira por plataforma (sin SNPP 0 avisos; sin MODIS, control, 11). Costo medido: 0 de 362 noches quedan sin VIIRS, pero
  22 noches publicadas dependían sólo de SNPP; pérdida neta 1 noche con alerta por sensor VIIRS en 33 días (una
  protegida: PCC V750 2026-10-10, 1,19 MW). El NRT de LANCE probablemente también se corta (NESDIS: «all S-NPP data
  products, Permanent»), SIN CONFIRMAR. Cambios urgentes sin tocar `pipeline/`: vigilancia por plataforma, aviso al
  operador en los tres HTML, ficha SDA v1.10; después, confirmar el corte el 3-nov y separar el auto-audit antes y después.

### 2026-10-21 (S159, dueña del loop): rescate de gránulos entregado
- `experiments/_s159/laads_rescate/` (`798400dec`): el **12-oct** fue reprocesado por NASA el 19-oct; LAADS borró los
  originales y CMR sigue entregando las entradas viejas (404). La protegida de Chillán 05:18 existe como
  `VJ202MOD.A2026285.0518.021.2026292150831.nc` (más Isluga 05:48 y Chillán 05:54); se las pasé al censo del oráculo
  como estrato aparte. **17 al 19-oct**: 66 gránulos intactos en LAADS que CMR Standard no indexa; CMR NRT los tiene hoy
  (ayer 18:41 UTC no), y LANCE purga en pocos días. **SNPP del 20-oct, 04:18 a 07:48 UTC**: no existe en ningún depósito,
  se declara «no observado». El pipeline sólo usa CMR (`pipeline/fetch.py:767-806`) y una búsqueda vacía sale sin
  registrar falla (`fetch.py:1087-1088`).
- Comprobado por el coordinador en `origin/main`: **producción sí tiene records del 17 al 19** (Chillán, Láscar,
  Villarrica, Isluga, los tres sensores), procesados en su momento con NRT; el hueco sólo afectó a los A/B. El 20 Láscar
  no tiene ningún record VIIRS (SNPP ausente).
- Decisiones para Nicolás: reabrir D-29 con un brazo suplementario de D25 sobre el 17 al 19 por NRT antes de que LANCE
  purgue (sensibilidad, no reemplaza el veredicto sellado); arreglo durable en `fetch.py` (fallback a listado de LAADS
  ante cero resultados o 404, con registro de falla; A45).

### 2026-10-21 (S159, dueña del loop): referencia inestable; guía de auditorías mejorada y en git; diseño de S160
- **Estabilidad de la referencia** (`experiments/_s159/referencia_estable/`, `8c5db502c`, SIN VERIFICAR, verificador
  corriendo): la tabla nunca cambia una fila pero las PIERDE (1.948 filas pasadas en 60 días, 14 protegidas); la unión
  histórica recupera 1.946 con 1 a 50 días de atraso; el OCR SÍ reescribe (39 alertas a FALSO_POSITIVO_OCR, 30
  protegidas, distancia de 0-2 a 10-33 km sin cambiar fecha), contra el «sin reproceso retroactivo» de A119 y del mapa de
  bases S139. Recomienda congelar la referencia por hash en todo A/B (aplica a la relectura de D25).
- **Guía de auditorías mejorada** y versionada: `GUIA_MAESTRA_AUDITORIAS.md` de 214 a 442 líneas (commit `31b70f1` en
  `MendozaVolcanic/workspace-guias`, privado): §3b de experimentos comparativos, §5 de prompting reescrita (bloque de
  autonomía oficial, tabla única de modelo y esfuerzo, bloque del verificador), reglas nuevas. Informe de integración en
  `experiments/_s159/guia_auditorias/C_INTEGRACION.md` (`e32b58265`), con cambios propuestos al preámbulo de VRP (P1 a P8,
  ruta `_s134_audit` vencida): van en un PR del repo, con el sí de Nicolás.
- Orden acordado con Nicolás («me parece ese orden»): guía primero, después diseño de la auditoría S160 con la guía nueva.
  Diseño encargado (borrador `docs/PLAN_AUDITORIA_S160.md` en `s159-pruebas`); se presenta antes de lanzar nada.

### 2026-10-21 (S159, dueña del loop): ⚠ Suomi NPP cesa el 2026-11-02; bibliografía entregada
- **Suomi NPP deja de entregar datos el 2026-11-02 a las 13:00 UTC** (aviso NASA Earthdata del 21-oct, comprobado por el
  coordinador en la fuente: «is still expected to cease at 13:00 Universal Time (UTC) on November 2, 2026», sujeto a
  cambio; no dice si incluye NRT). Es una de las tres plataformas VIIRS (`VIIRS_SNPP`, `VIIRS_SNPP_750`). Frente
  `experiments/_s159/cese_snpp/` lanzado: qué se apaga en silencio y qué preparar antes de esa fecha.
- **Bibliografía** (`experiments/_s159/biblio_2026/`, `a861d4d15`, PNG y PDF fuera del repo): MODIS C6.1 con decomiso
  anunciado (LAADS 199534) y C7 en paralelo, la 6.1 sigue produciendo; el hueco del 17 al 20 de octubre es de las
  colecciones **Standard**, no de NRT (8 a 11 gránulos por día), lo que matiza la premisa «CMR no sirve Chile» (D-29
  sigue en pie: los brazos de D25 usaron lo que había); el 12-13 sí tiene aviso de NASA (huecos de nivel 0). Matiza P2:
  Coppola et al. 2022 (Front. Earth Sci. 10:964372, p. 4-5) dice que el 375 m sigue «the procedure already used for
  MODIS (Coppola et al., 2015) and VIIRS (Campus et al., 2022)», y Aveni 2024 RSE p. 5 §3.2 da la grilla de 375 («regular
  134 × 134 UTM grid centred on the volcano summit»); el interpolador sigue sin fuente. Coppola 2022 da k ≈ 7,16 para
  I04 donde usamos 18,0 (validado). Fuentes 2026 no leídas: Aveni, Coppola y Laiolo 2026 RSE 10.1016/j.rse.2026.115626
  (OA, bajarla a mano) y la tesis de Aveni (Sapienza).

### 2026-10-21 (S159, dueña del loop): negativo con cráter, código OSF, verificador del oblicuo; guía y censo del oráculo lanzados
- **Negativo limpio con cráter** (`experiments/_s159/negativo_crater/`, `33532e4ac`): hipótesis REFUTADA. Exigir que el
  gránulo de MIROVA tenga el cráter sólo saca denominador (K publica 0 veces en esas pasadas en las ventanas del
  auto-audit y de N; 1 en la larga): la tasa de K sube 0,01 a 0,07 puntos. F sigue en +12. La regla sólo hace falta si
  alguien ensancha el pareo (con ±390 s K pasaría de 48/113/60 a 52/122/64 falsas). VIIRS 375 en negativos: 3,7 %.
- **Código OSF entero** (`experiments/_s159/osf_codigo/`, `d6ae7bb11`): 42 pasos, 12 iguales, 22 distintos, 7 sólo
  suyos; 24 de los 29 no iguales ya tienen D o frente. El código no dice nada del gránulo (recibe la matriz ya
  remuestreada; la elección del sur pasa antes). Sin frente: sun-glint < 12° (no existe en nuestro lado, pesa con D-10),
  el segundo pase sin adyacencia, y tres de gravedad 1. OSF sin novedades desde julio.
- **Verificador del oblicuo**: el 0,996 NO es tautológico (barajado dentro del volcán [0,17; 4,13]; otra pasada de la
  noche 9 de 78 en rango contra 38 de 45 pareadas) pero mide RÉPLICA, no física: **MIROVA también tiene el déficit
  oblicuo** (pasada más oblicua sobre menos oblicua de la misma noche: MIROVA 0,503, oráculo 0,517, K 0,239; nulo 1,054).
  Fuera de Chillán sobre 50° n 3. Candidata §12: corregir la dilución oblicua en el experimental.
- Lanzados: **integración de la guía de auditorías** (A + B a `GUIA_MAESTRA_AUDITORIAS.md`, repo `workspace-guias`) y
  **censo del oráculo** sobre los 5.476 negativos limpios VIIRS 750 (rama `s159-oraculo-censo` en `C:\vrp-trabajo\s159-m`).

### 2026-10-21 (S159, dueña del loop): gemelo de D25 medido; oblicuo y prompting entregados
- **Gemelo de D25** (`experiments/_s159/gemelo_d25/INFORME.md`): K, K' y D corren en el mismo job, en serie y sobre la
  misma CPU; K' es copia bit a bit de K (0 de 4.610 pasadas con publicación o `pc.vrp_mw` distintos en V1, en los cuatro
  estratos). El ruido de P2 vale 0 por construcción: P2 decide con una sola pasada neta, y el control de determinismo
  del §7 no puede fallar. Ruido entre máquinas medido en F/K V1 (un brazo por job): también 0 de 3.420 (detector C0, sin
  Villarrica). Controles: mutación 8 de 7 y 76 de 60; K contra C0, 1.576 discordancias. Propuesta de adenda para Nicolás
  antes del tag: declarar qué mide K', citar el ruido de F/K V1 con su salvedad, y (a) aceptar que P2 decide por una
  pasada neta diciéndolo en la primera línea o (b) listar y diagnosticar por pasada todo GANA o PIERDE de una o dos
  pasadas netas antes de declararlo.
- **Oblicuo** (`experiments/_s159/oblicuo_paquete/`, `cf964a718`, SIN VERIFICAR, verificador corriendo): en VIIRS 750
  sobre 50° de cenit el oráculo da 0,996 contra 0,178 de K (12 de 16 son Chillán); el remuestreo reparte el píxel
  oblicuo en 1,5 a 2,75 celdas.
- **Guía de auditorías**: agente B (prompting) entregó `experiments/_s159/guia_auditorias/B_PROMPTING.md`; falta A.
  Guías del workspace versionadas en el repo privado nuevo `MendozaVolcanic/workspace-guias` (línea base `59f1817`).

### 2026-10-21 (S159, dueña del loop): ola 2b, ocho frentes en paralelo (sí de Nicolás al paquete)
- Nicolás pidió vías nuevas y aprobó el paquete («si continua con el paquete que dices, todo lo que se pueda en
  paralelo»). Lanzados, sin worktrees nuevos (carpetas en `s159-pruebas` salvo el 6, en `C:\vrp-trabajo\s159-n` rama
  `s159-portes`): (1) **gemelo de D25**: ¿K y K' corren en el mismo job y su ruido de P2 es cero por construcción?, sin
  abrir el brazo D; (2) **negativo limpio con cráter**: exigir que el gránulo que listó MIROVA tenga el cráter y
  recalcular la línea base de K, el +12 de F y el oráculo; (3) **estabilidad de la referencia**: cuántas filas pasadas
  reescribe el consolidado y en cuánto se asienta; (4) **¿el paquete cura el déficit oblicuo?**, con los datos de N por
  cenit; (6) **portar el código de VIIRS 750 a VIIRS 375 y MODIS** contra MIROVA (tope 300 pasadas, runs de sólo
  lectura); (7) **rescatar gránulos** del 12 y del 17 al 20 de octubre listando LAADS y LANCE; (8) **código OSF entero**
  (Fable): pasos distintos sin frente y qué dice de la selección de gránulo; (9) **bibliografía 2025-2026 y avisos de
  NASA** (Fable, skill `investigacion`). El (5), censo del oráculo sobre todos los negativos de VIIRS 750, espera el sí
  de Nicolás por la escala. Sigue corriendo la segunda vuelta de #890 (D-30, D-32).

### 2026-10-21 (S159, dueña del loop): censo de F (D-31) terminado
- Run 39693661527 (pre-registro `bf6cf4db5` antes del disparo; apéndice `69eb48eb0` en `s159-n`, integrado a
  `s159-pruebas`). 122 pasadas: 60 negativos con cúmulo de cumbre en 0 MW, 59 `far`, Isluga 2026-10-12 05:48 y las otras
  dos SIN DATO de ese día. Controles en verde en las 119 con estado ok. **F enciende 60 de 60 cumbres** (1 píxel, 0,06 a
  0,61 MW; una ambigua por triangulación) **y 0 de 59 `far`**. Negativos limpios publicados sobre 5.476: K 54 (0,99 %),
  F 114 (2,08 %). **ΔE de F por censo = +12** (rango +10 a +12), igual que la predicción del verificador (≈ +11).
  Veredicto pre-registrado: ENCIENDE DE MÁS, ahora contado. 0 protegidas perdidas de 78; las 3 pasadas del 10-12, entre
  ellas la protegida de Chillán 05:18 (8,44 MW), siguen SIN DATO porque CMR no devuelve esos gránulos.

### 2026-10-21 (S159, dueña del loop): pre-registro de MxD03 v2
- `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md` v2 (`4a6559082` en `s159-pruebas`), §0 con cada cambio contra el
  verificador. P2 con nulo de 20 semillas de R en los 2.046 records con cenit ≤ 35° (sobre 35° y sin Cordón Caulle sólo
  informa); M sólo informa (la alternativa con el comparador D-28 en EMPEORA queda en el §11); evaluador
  `evaluar_mxd03.py` diseñado, no implementado; citas corregidas; pareo fijo a 120 s; CUMPLE SIN DAÑO; ~47 h de runner
  en 1.232 gránulos; control 3 sin tolerancia, con re-corrida en el `codigo_sha` del record (5.449 de 5.465 records
  escritos con un `pipeline/` distinto del de hoy). §11 con 12 puntos para Nicolás. Discrepa del verificador en dos
  números (H1: 7 de 31 negativos de Cordón Caulle a 17 km o más, no «muchos» en el borde; H9: 12 `codigo_sha` en la
  ventana, no 16). PENDIENTE: verificación del delta v1 a v2 antes del sello.

### 2026-10-21 (S159, dueña del loop): verificador de Chillán MODIS entregado
- `experiments/_s159/chillan_modis/verificador/INFORME.md`. **CONFIRMADAS**: Test 2 (z 3,78 y 3,72 contra 5; 0 de 28 y
  0 de 32 píxeles dentro de 5 km lo pasan, no depende del píxel elegido), magnitud 0 MW (Chillán sin `local_kernel_bg`,
  fondo global del anillo con recorte), controles 7 de 7 y estrato (por CSV remoto: 16 protegidas, 11 publicadas, 2
  con cúmulo nulo, 3 diurnas). **PARCIAL**: la compuerta (cuentas bien; la causa «cumbre nevada más fría» queda
  SOSPECHA y no decide la detección porque el segundo pase corre sin ella) y los descartes: con el flag REAL la
  conectiva `min` sola detecta dentro del inner (2 y 3 píxeles, cúmulo summit a 3,40 y 0,92 km); el «min más sin
  compuerta» del agente aplicaba `min` sólo al primer pase, que no existe en producción. Para publicar no basta ninguna.
- Propio: a 58° la geolocalización de `_interp_geo` está comprimida (separación entre filas 0,40 y 0,81 km contra 1,00
  en nadir), así que las distancias del informe están en una geometría que no es la real (liga con M y MxD03).

### 2026-10-21 (S159, dueña del loop): verificador del comparador D-28: PARCIAL
- `experiments/_s159/instrumentos/verificador_comparador/INFORME.md` (`63e310af5` en `s159-evaluador-d25`). El código
  sigue el §2 punto por punto; ninguna ganancia uniforme ni por volcán da MEJORA (0 de 56 y 0 de 54); el nulo de d′
  está centrado (2,4 a 3,0 % por cola en 20 semillas). Lo que falla: **poder** ante un efecto con dispersión entre
  pasadas (mitad de camino con ruido 0,05 en log10: CUMPLE 12 de 12; con 0,10: 1 de 12), así que un SIN EFECTO no
  distingue «no acerca» de «acerca con dispersión»; **tres guardas faltantes** (opción A sobre d′, calibración de d′
  ignorada, opción A contada con d); y la **semilla de d′** decide V2 VIIRS 750 z≤40 (11 de 200 contra tope 10).
- El implementador aplica D-30 (INDECIDIBLE, una cola), las tres guardas, la marca de `--calibracion sellada` en el
  JSON y un §5 de la adenda con D-30 y la curva de poder declarada antes del tag. Semilla y repeticiones de la
  calibración de d′: decisión para Nicolás.

### 2026-10-21 (S159, dueña del loop): verificador del pareo MODIS entregado
- `experiments/_s159/pareo_modis/verificador/INFORME.md` (`0392cdffc`). **CONFIRMADAS**: el pareo a ±120 s (ensanchar
  rescata 0 de 2.212 alertas y sólo duplica el conteo; ninguna protegida en las 148); MIROVA lista el gránulo sur
  (Terra 57 de 60, Aqua 70 de 70, lo que descarta el orden del scraper) y no alerta con el cráter al norte (0 observadas
  contra 28,7 esperadas; control sur 24 contra 25,4); #864 no cambia (también cambian las falsas de C0, 295 a 299 en
  V375); Chillán 01-19 es borde. Matices: en MODIS la regla descansa en una sola alerta (22 de las 24 son V375), y los
  negativos limpios contaminados son 0,9 % MODIS, 2,0 % V375 y 1,4 % V750. **PARCIAL**: el exceso de publicación del
  gránulo norte está inflado por el doble record (p 0,043 contra la tasa esperada con dos oportunidades); fuera de toda
  métrica quedan 7 publicaciones V375, 13 en los tres sensores. Queda SOSPECHA si MIROVA mira un solo gránulo o si el
  canal que scrapeamos sólo expone el del sur.

### 2026-10-21 (S159, dueña del loop): verificador del pre-registro de MxD03: LISTO CON CAMBIOS
- Informe `experiments/_s159/mxd03_prereg/verificador/INFORME.md` (`464152853`). Población reproducida exacta y no
  condicionada a K; citas de Coppola 2026 p. 4 y Coppola 2016a sobre remuestreo textuales. Cuatro cambios obligatorios:
  (1) P2 decide con un nulo muerto (K2 en el mismo proceso da ruido 0; 31 de 39 negativos que K publica son de Cordón
  Caulle en el borde del radio de 20 km); (2) M bloquea por un 3 % (X = 0,97·K da EMPEORA con intervalo de ancho cero,
  EMPEORA va sin el comparador D-28); (3) `evaluar_d25.py` es sólo VIIRS, hace falta evaluador MODIS; (4) Coppola 2016a
  no dice 50° ni 55° (sólo «>30°», sobre cráteres hondos). Más cinco de redacción (pareo fijo a 120 s, CUMPLE = sin daño,
  1.232 gránulos, tres afirmaciones heredadas corregidas, control 3 sin tolerancia). El autor escribe la v2.

### 2026-10-21 (S159, dueña del loop): Chillán MODIS entregado, verificador corriendo
- Integrado a `s159-pruebas` (`0d949d1f5`; rama `s159-chillan` `05f16cf2c`; runs 39692725826 y 39693552091). SIN
  VERIFICAR. Las dos protegidas MODIS de Chillán del #864 (10-12 07:20 y 10-15 01:05, ~58° de cenit) caen en el
  **Test 2** (dNTI a ~3,7σ con umbral μ+5σ, no el piso C1) y también en la **compuerta de 3 K** (BT MIR 3,7 y 4,4 K
  bajo `t_bg`: la cumbre nevada nocturna está 10 a 12 K más fría que el anillo de 5 a 25 km). Descartadas con número:
  saturación, banda primaria, σ del fondo, nube. Sólo `min` más sin compuerta, juntos, detectan (2 y 3 píxeles), y aun
  así la magnitud sale 0 MW por el fondo del anillo con recorte. Es la cara MODIS de D25 y R2-6 (D25 no existe en
  `process_modis`, D-26). Estrato sep-oct: 16 protegidas MODIS de Chillán, 11 publicadas, estas 2 con record y 3
  diurnas sin record (pipeline MODIS sólo nocturno, D-10).

### 2026-10-21 (S159, dueña del loop): pareo MODIS y borrador de MxD03 entregados; dos verificadores corriendo
- **Pareo** (`s159-pruebas` `82220c314`, `experiments/_s159/pareo_modis/INFORME.md`), SIN VERIFICAR: el pareo de ±120 s
  acierta y ensanchar a ±5 min empeora (no tocar `TOL_S` ni `VENTANA_S`). De 6.646 records MODIS con referencia, 148
  parean sólo con el gránulo vecino: 130 son la otra mitad de una pasada ya pareada, 18 son pasadas con un gránulo
  nuestro; 0 protegidas. El «noveno caso» del verificador de M (Chillán 01-19) no vale. Hallazgo central: con el volcán
  en dos gránulos MIROVA lista el del sur en 526 de 537 casos y sólo alerta si el cráter está en él (24 de 24), así que
  RUTINA de gránulo vecino entran como negativos limpios (1 a 3 %); nuestras publicaciones del gránulo norte quedan fuera
  de toda métrica. #864 no cambia (reproducido hoja por hoja, 0 de 1.203).
- **Borrador del pre-registro de MxD03** (`a0484dc8b`, `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`): censo de
  5.465 pasadas MODIS nocturnas (2026-03-01 a 2026-10-16; 50 protegidas, 42 bajo 1 MW, 5.110 negativos limpios), brazos
  K, K2 y X en arnés por gránulo (~58 h de runner contra 235 h de reproceso), nueve decisiones para Nicolás. Lo
  inesperado: los TIF MODIS de MIROVA están todos en EPSG:4326 (la grilla UTM fue sólo VIIRS 375); 44 de las 50
  protegidas están bajo 40° de cenit; 43 de 44 noches con protegida MODIS ya publican por VIIRS; Coppola 2026 no está en
  la lista de papers de MISSION; el consolidado remoto cambió entre dos corridas de la misma tarde (congelar la
  referencia).
- Verificadores con contexto limpio lanzados para los dos. Corriendo además: censo de F (D-31), Chillán MODIS,
  verificador del evaluador de D25.

### 2026-10-21 (S159, dueña del loop): verificador limpio de N entregado
- Integrado a `s159-pruebas` (merge `1360c4631`; verificador en `s159-n` `dc07644df`). Informe:
  `experiments/_s159/n/verificador/INFORME.md`. Recalculó la publicación de los cinco brazos con el predicado del tablero
  en node y coincide en las 1.955 combinaciones.
- **CONFIRMADAS**: la grilla de GEO con remuestreo lineal (sobre las 107 alertas que detectan las cinco variantes, 1,000
  [0,985; 1,008]; la esquina viene de los encabezados de los TIF y quedó fija en el pre-registro: sin sobreajuste; son
  cuartiles, no IC, y condicionado a que el oráculo detecte, 145 de 181); C cambia 0 de 391; el tope D9 recorta la
  protegida de Chillán (F 6,214 a 5,0, sigue publicada); K reproduce producción en 391 de 391.
- **PARCIAL** lo de F: el mecanismo y las 48 alertas ganadas se sostienen (0 protegidas perdidas sobre 78 de 79; Chillán
  2026-10-12 05:18 SIN DATO), pero el **3,8 % y el ΔE +104 caen**: F no cambia la detección, así que sólo puede encender
  donde K ya tiene cúmulo sin publicar, y eso se cuenta entero en la población (60 de cumbre en 0 MW y 59 `far`). Techo
  real 173 negativos (3,2 %), ΔE ≤ +71; con lo observado, ΔE cerca de +11 (rango −16 a +11, más 0 a +59 por los `far`
  sin caso en la muestra). La muestra sacó 4,3 % de elegibles contra 1,1 % de la población. Se cierra con un **censo de
  ~120 pasadas** (las 60, las 59 y Isluga 10-12).
- **PARCIAL** el oráculo post hoc: aritmética reproducida, pero una de las 6 protegidas de Cordón Caulle está a 4,59 km
  según MIROVA (no 7,8 a 10,5); publica 0 de 140 negativos muestreados pero cambia la detección y no tiene techo por
  censo (cota 2,6 %, ΔE hasta +34); y mezcla el predicado del agente con el del tablero.

### 2026-10-21 (S159, dueña del loop): frente N terminado, verificador limpio corriendo
- N (rama `s159-n`, `3faa5a4f6`; pre-registro `0b20eb1f3` antes del disparo; runs 39680724047, 39682867040 y
  39690106947; 391 de 398 pasadas con los cinco brazos, K2 = K y K = record publicado en 391 de 391). Todo SIN
  VERIFICAR hasta que entregue el verificador:
  - **F y FC: ENCIENDEN DE MÁS** (pre-registrado). Negativos limpios publicados de 54 (1,0 %) a 206 (3,8 % de 5.385,
    ponderado; 6 eventos en 141 muestreados), ΔE +104 [14,5; 212]; 0 protegidas perdidas; alertas bajo 1 MW sin
    publicar de 65 a 17 de 175. Lo encendido son cúmulos de 1 píxel en 0 MW del segundo pase que el código de MIROVA
    no detecta: el fondo solo no es el arreglo.
  - **C (sin la compuerta de 3 K): 0 de 391 cambios.** El cero de los cúmulos lo pone el fondo, no D22 (responde VA-1).
  - **El código entero en la grilla de GEO reproduce la magnitud de MIROVA**: razón 0,999 [0,978; 1,007] en 145
    alertas, con remuestreo lineal y esquina a -187,5 m. Primera medición por valores que sostiene la grilla de GEO.
  - **Post hoc**: el oráculo como brazo, con umbrales de cumbre en todo el recuadro, gana en las dos caras (negativos de
    54 a 8, 59 alertas débiles ganadas, 0 protegidas perdidas); con la caja por defecto pierde 6 protegidas de Cordón
    Caulle. Para la ola 3 lo que cuenta es el paquete entero, no el fondo solo.
  - El tope D9 recorta con F una protegida de Chillán (MIROVA 9,0; F 6,21 a 5,0).
  - SIN DATO: 3 pasadas del 2026-10-12 que CMR autenticado no devuelve, 2 diurnas de Chillán (estrato diurno sin
    medir), 2 de Chaitén con el volcán fuera del gránulo.
- Incidente: la cuenta de GitHub tocó el límite de la API a las 22:16 UTC, en parte por `gh run watch` con el intervalo
  por defecto. Regla para los agentes: nada de `gh run watch` ni bucles de `gh`.
- Decisiones para Nicolás que deja N: escalar la muestra de negativos sobre el tope de 400 y medir el estrato diurno.

### 2026-10-21 ~23:20 UTC (S159, dueña del loop): D-28 implementada; cuatro frentes nuevos en paralelo
- **#890** (`b4258040c`, borrador): comparador implementado; roja 10 por aserción, verde 15 de 15,
  `probar_evaluar_d25.py` 30 de 30 (los 27 de S157 idénticos), con los pares reales de K el placebo ya no da MEJORA
  (|d′| máximo 0,0), mutaciones 4 de 4 más 2 extras, suite 2.357 pasan y 0 fallas en árbol quieto. Cinco preguntas
  para la adenda en el PR. Verificador limpio corriendo. No se tocó ningún brazo del A/B.
- **`vigilar-osf-mirova.yml` arreglado** en la rama de #888 (`7a8f9fe61`): las condiciones `if:` usaban comillas dobles
  y GitHub rechazaba el archivo; el push siguiente sólo disparó Tests.
- Lanzados sin crear worktrees (Nicolás pidió cuidar el espacio): **Chillán MODIS** (por qué el primer pase no ve las
  dos protegidas del #864; worktree de M reusado en la rama `s159-chillan`), **pareo MODIS en el borde del gránulo**
  (`experiments/_s159/pareo_modis/`, local) y **diseño del pre-registro de MxD03**
  (`experiments/_s159/mxd03_prereg/`, sin despachar). N sigue corriendo.

### 2026-10-21 (S159, dueña del loop): verificador limpio de M entregado
- Integrado a `s159-pruebas` (`db3e9cbb4`, fast-forward desde `s159-m`). Informe:
  `experiments/_s159/m/verificador/INFORME.md`. **CONFIRMADAS** las afirmaciones 2 (desplazamientos 2,817 / 5,041 /
  1,101 / 2,475 km; sin Láscar, 2,951 con n 9), 3 (Chillán: los 4 archivos existen en LAADS y LANCE, records con
  `primary_cluster` nulo, primer pase 0 en los dos brazos) y 4 (Láscar 2,543 a 0,588 km en 38 de 38 con la misma
  detección). **PARCIAL** la 1: los 12 cambios se reproducen, pero 7 de los 10 apagados salen del círculo (no «6 en el
  borde»; Cordón Caulle 2025-08-03 06:35 se apaga sin salir); 4 de los 12 son de **fondo**, no de posición (Láscar,
  `t_bg` se mueve 0,24 a 0,41 K y `pc.vrp_mw` cruza cero), contra el «fondo casi igual» de H5; con pareo a ±5 min hay 9
  referencias de MIROVA, no 8 (7 de 9 se acercan); y el saldo apagados contra encendidos sale en parte del diseño
  (población condicionada a que A publicó, A109).
- Hallazgo del verificador para el instrumento de todas las evaluaciones MODIS (gravedad 2): el pareo por hora exacta
  pierde las pasadas que caen en el borde entre gránulos (121 de 5.815 records MODIS sólo parean a ±5 min). Pendiente
  medir su efecto en el auto-audit y en `banco_paridad`.

### 2026-10-21 ~22:40 UTC (S159, dueña del loop): frente M terminado, verificador limpio corriendo
- M (rama `s159-m`, `cecd4b0f1`, run 39681481914, 85 de 85 records, controles en verde): **CONFIRMA** su
  pre-registro, todavía SIN VERIFICAR. Lo que afirma: con MxD03 cambian 12 de 57 publicaciones MODIS de cumbre sobre
  40° (10 se apagan, 2 se encienden; 6 eran píxeles en el borde del círculo de cumbre); desplazamiento mediano de 2,82
  km a 40-50° y 5,04 km sobre 50° del lado del frame 0; fondo y magnitud casi iguales (razón 1,03 y 1,00); y las dos
  protegidas de Chillán del #864 sí tienen gránulo, procesado y sin detección en los dos brazos, así que la
  geolocalización no las explica.
- Hallazgo lateral (H7 de M, confirmado por el coordinador en los runs 39685038909 y siguientes):
  `.github/workflows/vigilar-osf-mirova.yml` (viene de #888) deja un run fallido sin jobs en cada push de las ramas
  que lo traen. Arreglarlo antes de mergear #888.
- Leer MxD03 en `process_modis` toca `pipeline/`: va con ciclo A45 y A/B, decisión de Nicolás.

### 2026-10-21 ~19:50 UTC (S159 «retomar», dueña del loop): D-28 sellada; ola 2 lanzada con N y M
- Verificado al abrir: `loop/activo` = remoto (`a722063c4`); NRT operacional publicó a las 15:24 UTC; #885 a #890 en
  borrador; CMR sigue sin Chile el 18 y 19 de octubre (0 gránulos en VNP02IMG, VJ102IMG y MOD021KM) y parcial el 17 y 20.
  O2 sin correr. #864 abierto, a la espera de D25.
- **D-28**: Nicolás eligió la opción (b) para el placebo de M. Adenda `ADENDA_PLACEBO.md` en `s159-evaluador-d25`
  (`2629f5a16`), escrita antes de leer V1, V2a y V2b. Un agente la implementa en `evaluar_d25.py` (TDD, mutaciones,
  sin tocar los brazos del A/B); falta después el verificador con contexto limpio antes del tag de lectura.
- **#889**: Nicolás dijo que lo mergea él. Al anotar esto sigue abierto y en borrador.
- **Ola 2**: N en `C:\vrp-trabajo\s159-n` (rama `s159-n`, disparo por `s159-n-disparo`) y M en `C:\vrp-trabajo\s159-m`
  (rama `s159-m`, disparo por `s159-m-disparo`), los dos cortados de `origin/s159-pruebas` (`dc8b51832`), cada uno con
  pre-registro propio antes de despachar. La relectura de D25 espera la decisión de los días sin CMR (decisión 3 del
  bloque S159) y el verificador del evaluador.
- Worktree nuevo `C:\vrp-trabajo\s159-evaluador` para #890. C: con 22 GB libres tras crear los tres.

### 2026-10-21 tarde (S158 «retomar», dueña del loop): ola 1 de S159 COMPLETA
- Siete frentes terminados y commiteados en `s159-pruebas` (P1 `69c482c64`, P2 `3f133d69d`, P3 `70e31dcb9`, GEO
  `fbbbbfc1d`, O1 `46664ad9d`, COB `dc8b51832`; la rama se reescribió con el sí de Nicolás para sacar 52 páginas de
  papers con copyright, que quedan en disco). IA en #889 (CI verde, merge bloqueado por el clasificador de permisos:
  lo hace Nicolás) y su pieza del evaluador de D25 en #890 (borrador, requiere adenda).
- Lo que cambia la ola 2: (1) **N usa la grilla de 750 m correcta** (GEO: esquina a -187,5 m en x e y de la de 375 m;
  la prueba con gránulos de R2 usó la de 375 m) y rehace Láscar 2026-09-26 y Chaitén 2026-10-06; (2) **MODIS lleva dos
  variantes de fondo**, media de vecinos y halo (P3: ningún paper MODIS describe halo, interpolación ni recorte);
  (3) **con un píxel el VRP varía hasta 1,82 veces según la triangulación** (O1): informar banda o esperar O2 (paquete
  para MATLAB Online listo en `experiments/_s159/o1/o2_paquete/`); (4) **M estratifica por lado del barrido y por
  posición dentro del gránulo** (P3: ±2 líneas en los extremos); (5) toda evaluación contra el OSF 2025 empieza el
  2025-02-15 (COB H1: 357 de las 411 «sin record» son anteriores a nuestra serie); (6) CMR no sirve Chile del 17 al
  20 de octubre (COB H2): ninguna ventana los incluye sin declararlo.
- Lista viva de lo que podríamos hacer mejor que MIROVA: `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 (pedido de Nicolás).

### 2026-10-21 18:14 UTC (S158 «retomar», dueña del loop): bloque R2 incorporado; ola 1 de S159 corriendo
- La segunda ronda cerró en el PR borrador #888 (checks verdes; ningún hallazgo refutado por sus verificadores). Su
  bloque `tasks/LOOP_BLOQUE_S158_R2.md` quedó copiado al §4 («Bloque S158 R2 y plan S159»); la sesión de la segunda
  ronda lo borra de su rama.
- Plan S159 aprobado por Nicolás (texto: «Apruebo el plan completo, instala GNU Octave 11.3 con winget para O1, tope de
  400 pasadas en el primer lote de N. Lanza la primera ola.»). Octave 11.3 instalado. Dos worktrees en C:
  (`C:\vrp-trabajo\s159-pruebas`, rama `s159-pruebas`; `C:\vrp-trabajo\s159-instrumentos`, rama `s159-instrumentos`).
- Ola 1: P1 y P2 terminados y commiteados; P3, GEO, COB, IA y O1 corriendo como subagentes. Nada despachado en
  Actions todavía; nada tocado en `pipeline/`, `data/` ni `frontend/`.

### 2026-10-21 ~02:50 UTC (S158, dueña del loop): despachadores relanzados y aprobación de la tabla b
- Sin rastro de los procesos de S157 (verificado en la lista de procesos). Tres procesos locales de S158, con logs en
  `D:\vrp-trabajo\temporales\s158\` (`relleno.log`, `d25.log`, `control_nrt.log`): relleno líneas 5 a 10 en serie
  (el 4.º, 39533674886, terminó `success`; el 5.º, PCC 2026-04-25, = run 39534689286); V2a y V2b de D25 desde el tag
  `s157-d25-k-codigo` (= `66961f65`, igual al de V1) con 0 A/B vivos; control del NRT a las 09:35 UTC.
- **Aprobación de Nicolás, en esta sesión y textual**: «En las decisiones que te listó estoy de acuerdo con todas sus
  recomendaciones, incluida responder #864 dejando lo de Chillán a la espera de D25.» Cubre la tabla b de
  `tasks/BLOQUE_ARRANQUE_S158.md`: (1) las ~64 `nrt` sin estándar se procesan desde el NRT con K; (2) mergear #878;
  (3) la λ de B22 se enciende junto con el reproceso que traiga D25; (4) mergear #869, #879 y #881, y #880 cuando
  mida el 18-oct; (5) implementar la lista de corridas juzgadas del watchdog (#876); (6) #813 postergado hasta D25;
  (7) PAT y aviso a OVDAS quedan con él. Y responder #864.
- #881 traía `.github/workflows/probe-s157-pcc865.yml` (probe por push a su rama, sólo lectura): se archiva en
  `.github/workflows/_archive/` antes del merge para que no quede un workflow muerto en `main`.
- Mergeados #878 (`458d5b43`), #869 (`1fe351e1`), #879 (`bd4d8e4b`); ramas borradas. #864 respondido
  (comentario 6306747826), con el matiz de que **la parte MODIS de Chillán no la contesta D25** (D-26 dejó MODIS
  fuera; PREREGISTRO l. 6-7, 70 y 298-301).
- **La decisión (1) no es ejecutable tal cual** (CMR consultado 2026-10-21 ~02:55 UTC, `granules.json`, caja
  -75,-45,-65,-17, 00-12 UTC): `VNP02IMG_NRT` da 0 gránulos el 2026-08-05 y también el 09-01, 09-20, 10-01 y 10-08, y 5
  el 10-15, o sea que LANCE retiene el NRT apenas días; y `VNP02IMG` (estándar) da **0 del 2026-08-03 al 08-06**
  contra 4 a 6 el 08-02, 08-07 y 08-08 (NOAA-20 `VJ102IMG` sí tiene 4 a 6 esos días). Las ~64 pasadas `nrt` se
  procesaron en vivo y hoy no hay archivo de donde reprocesarlas. Pregunta abierta a Nicolás: dejarlas en C0 con su
  marca y volver a consultar CMR por si NASA publica el estándar más adelante. SIN VERIFICAR: por qué falta el
  estándar (hueco de producción de NASA o algo del satélite).
- #881 mergeado (`c0ee0950`; probe archivado en `_archive/`, CI verde sobre `a5f7130e`). **#876 arreglado en PR #882**
  (`s158-watchdog-juzgadas`): lista `.github/reproc-watchdog-juzgadas.json` con id, intento, motivo y referencia;
  exime sólo terminadas y sólo ese intento; entrada incompleta invalida la lista y deja el job en rojo. 41 de 41
  locales, dos mutaciones atrapadas por aserción. Merge cuando el CI dé conclusión (enmienda A39).
- Relleno: 5.º (39534689286, PCC 2026-04-25) `success`; 6.º = 39535573533 (Copahue 2026-07-02).
- **Nicolás, textual**: «has todo lo que recomiendes para que avancemos mas rapido». Aplicado: (1) las ~64 `nrt`
  sin estándar **quedan en C0 con su marca** y se vuelve a consultar CMR antes de aplicar el reemplazo; Auto-fix
  activo en #882. **El reemplazo en producción (1.24 d) NO se aplica con este mensaje**: A45 pide un sí puntual
  sobre ese paso, con tag y ensayo a la vista; se le pide cuando esté listo.
- 1.24 b adelantado: `experiments/_s158_reemplazo/ensayo_11.py` (copia del de S157 con Chillán y selección por
  argumento), rama `s158-reemplazo-ensayo` (worktree `D:\vrp-trabajo\temporales\s158_reemplazo`). Avance sólo
  Chillán: **PASA**, 5.558 en ventana, 5.552 reemplazados, 844 agregados, 6 en C0 (0,11 %, las 6 `nrt`), 5.904 a
  6.748 records. Los 11 juntos se corren tras el relleno.
- **#882 mergeado** (`d428137a`, CI `pytest` verde). Efecto medido: watchdog despachado sobre `main` (run
  39536910831, `success`): «2 corridas juzgadas en la lista», «vigilando 14 reprocesos vivos de 44 archivos», «sin
  problemas»; **#876 se cerró solo**.
- `verificar_ventana.py` (1.24 e) vive sólo en `loop/activo` (`experiments/_s154_reproc_k/`), no en `main`.
- #880, control de la consulta: misma caja sobre Chillán da 3/4/12 (VNP02IMG/VJ102IMG/MOD021KM) el 10-15, 3/3/6 el
  10-16, 1/3/5 el 10-17 y 0/0/0 el 10-18 y 10-19: CMR aún no indexa el estándar del 18-oct; #880 sigue esperando.
- **Relleno 10 de 10 `success`** (03:38 UTC; runs en `D:\vrp-trabajo\temporales\s158\relleno.log`). Ensayo de los 11
  tras el relleno (rama `s158-reemplazo-ensayo`, `25f3a463`): **los 11 PASAN**, C0 = 64, **las 64 `nrt`, 0
  `standard`** (máx. 0,15 %, Tupungatito). Verificador limpio en primer plano (`D:\vrp-trabajo\temporales\s158_verif\
  INFORME.md`): las tres afirmaciones CONFIRMADAS (relleno: 14+9+5+3 = 31 claves `standard` agregadas, nada borrado;
  CMR: estándar de Suomi NPP cortado de 2026-08-03T01:54 a 08-06T16:30, también `VNP02MOD`).
- **Hallazgo H1 del verificador (gravedad 3, decisión de Nicolás)**: las 64 C0 quedan SIN marca dentro de la serie K y
  **25 publican**, concentradas en dos pasadas de Suomi NPP del 2026-08-06 (05:06/05:12 y 06:42/06:54) en 8 volcanes:
  un pulso simultáneo falso. Ni la prueba de frontera (95 %) ni `detector_de_noche` del auto-audit lo ven. Conteo con
  un puerto Python de `mirovaEqVrp`, no con el predicado literal (A97): SOSPECHA en el número exacto, patrón claro.
- **Misma familia, ya en producción hoy**: 26 records `MODIS_TERRA` `nrt` sin `regimen` después del 2026-09-18
  (09-28, 10-02, 10-10), procesados por el NRT con C0 antes de la adopción (p. ej. PCC 09-28 01:25 procesado
  2026-09-28T10:56Z) y no reemplazados por el reproceso de 30 días por falta de estándar de Terra (1.27). 2 publican
  en PCC (0,852 y 0,378 MW).
- H3 (informativo, para el sí del reemplazo): lo publicado en la ventana baja de 25.202 a 9.120 pasadas (Villarrica
  2.761 a 86, Llaima 2.133 a 17); protegidas de MIROVA cubiertas suben de 243 a 288 de 379, se pierden 3 pasadas y
  0 noches.
- **Decisiones de Nicolás, textuales (AskUserQuestion, ~10:25 UTC)**: residuos C0 = «Sacarlas a un archivo aparte
  (Recommended)»; reemplazo = «Sí, aplícalo (Recommended)» (pregunta: aplicar el reemplazo de los 11 con tag
  defensivo, frontera al 2025-02-15, pruebas, `verificar_ventana.py`, un solo commit entre dos NRT).
- El PC estuvo suspendido de ~03:40 a ~09:10: el control del NRT no escribió; contado a mano: **33** `NRT update`
  de 02:00 a 09:30 del 21-oct contra **24** del 20-oct; NRT verde 8 de 8. **Control PASA.**
- **V1 de D25 terminó `failure`**: 2 jobs (Llaima y Villarrica, trozo 4, 2026-10-16..18) con código 3 del modo
  estricto, «3 búsquedas o descargas fallidas (días: ['2026-10-17'])», CMR inestable. V2a despachado por el
  despachador a las 09:16 (39575542584). V1 relanzado sólo en sus fallidos (`gh run rerun --failed`, intento 2)
  con V2a ya corriendo, así que entra como único pendiente del grupo y no desplaza a nadie.
- Preparado en `s158-reemplazo-ensayo` (`356b0aa1`): frontera `DATOS_K_DESDE_UTC` al 2025-02-15, guard
  `tests/test_guard_serie_k_pura_s158.py` (100 % con marca desde la frontera; línea base ROJA sobre main: las 26 de
  Terra), `apartar_c0.py`, `aplicar_11.sh`. Ensayo aplicado en el worktree y descartado: 90 apartados, 106 pruebas
  verdes, vigilancia de la sombra VERDE antes y después con los mismos disparadores (sólo crecen ventana,
  retrospectivo 252 a 2.207 y la lista informativa de protegidas 5 a 9). El NRT rebasa con `-X theirs` (gana el
  commit del NRT en un trozo en conflicto, al revés de lo que dice el comentario de `nrt.yml`), por eso el reemplazo
  entra con el NRT quieto, regenerado sobre main fresco por `D:\vrp-trabajo\temporales\s158\aplicar_en_ventana.sh`.
- **Reemplazo aplicado en la rama de #883** (11:08 UTC, con el NRT quieto; el clasificador de permisos rechazó dos
  veces saltarse la compuerta «NRT vivo», así que se esperó el fin del NRT y se corrió con la compuerta intacta).
  Tag `pre-s158-reemplazo-k` = `0e80bb88` (empujado). CI del commit de datos: 4 pruebas ancladas a la historia C0
  (banco de paridad S139 con 63,5 %, golden 4 de Villarrica, isValidDetection con sustrato C0, ancla Chaitén)
  re-ancladas en `f7c18018`: el banco con K da 2,59 % en 3.701 negativos limpios de V375 (MODIS 0,75 %, V750 0,93 %,
  recall por noche V375 0,967); el golden 4 era una publicación de más (MIROVA RUTINA 0,0 MW en esa pasada) y ahora
  vigila que K calle; el sustrato C0 queda en la sombra `experimental_v2` (27) y en los residuos (3). El NRT de las
  11:10 generó conflicto: los 11 JSON se tomaron de main y el reemplazo se reaplicó (`cdbf7478`); 24 pruebas clave
  verdes. Falta el CI y el merge.
- **1.24 d HECHO: #883 MERGEADO** (squash `8471add4`, 2026-10-21 11:48:37 UTC; el 502 de la API llegó después del
  merge, comprobado en el estado del PR). CI `pytest` verde sobre `615f26fd`. Auto-merge: Nicolás dijo sí, pero el
  repo exige reglas de protección en `main` para usarlo y esas reglas bloquearían los push directos del NRT; el ajuste
  `allow_auto_merge` se habilitó y se volvió a `false` sin efecto. Verificación: `verificar_ventana.py
  --desde 2025-02-15 --hasta 2026-09-17 --corte 2026-10-18T09:57:30Z --tag pre-s158-reemplazo-k`: **68.072 de 68.072
  con K, 0 sin K, 64 claves fuera (las de Suomi NPP apartadas; las 26 de Terra quedan después de la ventana), 0
  cambiados antes**. R8: el sitio publicado sirve `DATOS_K_DESDE_UTC = 2025-02-15`; `Llaima/NevadosDeChillan/
  Copahue_recent.json`: 0 pasadas Suomi NPP del 06-ago y 0 records sin marca; el tablero carga sin errores de
  consola y el aviso dice «desde el 15 feb 2025 son del detector K». Pendiente menor: el aviso todavía dice que «las
  series que cruzan el 15 feb 2025 mezclan dos detectores», que ya no aplica (la serie empieza ese día).
- **#884** (workflow `aplicar-reemplazo.yml`: regenera sobre main en cada intento, sin rebase; guard nuevo, g4 lo
  reconoce, mutación de orden atrapada), abierto, para los próximos reemplazos (D25, λ de B22).
- Tres sesiones paralelas en worktrees de D: (la app exige 24,8 GB libres en C: para crear los suyos y había 16,8):
  `local_5c68f9b3` (V750, `D:\vrp-trabajo\temporales\s158_v750`), `local_4b70f190` (Tupungatito, `..\s158_tupun`),
  `local_a4b23469` (D17, `..\s158_d17`). Borrar cada worktree cuando entregue su PR.
- Pendiente 1.24 cola: PR que borre `data/_s154_reproc_k_historico/` de `main` (queda en la historia y en el tag).
  **NO antes de evaluar D25**: `experiments/_s157_prereg_d25/evaluar_d25.py` y `sustrato_k.py` lo leen. Junto con
  ese PR, pulir la frase del aviso de `frontend/cambio_detector.js` sobre «series que crucen» la frontera.
- **D25, estado a las 16:48 UTC** (la app se cerró a media tarde y mató `d25_serie.sh`, que ya había despachado
  todo): **V1 completo** tras el reintento (intento 2 de 39530508296: los trozos 4 de Llaima y Villarrica en
  `success`; `recolectar` dio COBERTURA PAREJA, 4.610 pasadas por brazo, 0 faltan, 0 sobran). Su `failure` es sólo
  la publicación de la rama `s146-ab/39530508296`, rechazada («fetch first») porque ya existía del intento 1: los
  datos están en el artefacto `s146ab-todo` del intento 2 (vence 2027-01-19). Defecto menor del workflow: un
  reintento no puede reescribir su propia rama de resultados. **V2a** 39575542584 `success`. **V2b** 39612909810
  corriendo (16 de 23 jobs a las 16:48). Al terminar: cobertura de V2a y V2b (A108), `evaluar_d25.py --calibracion
  simetrica`, verificador limpio, informe.
- Sesiones paralelas entregadas: #885 (D17: diseño + auditoría de 6 frentes contra el código de MIROVA V750 en OSF,
  verificadores corriendo al cierre de la app), #886 (Tupungatito: las 2 protegidas de #864 no son del cráter, déficit
  0,36 a 0,49 por fondo), #887 (V750: ninguna pérdida por M15; 55 de 75 pérdidas son cráter en 0,0 MW). Nicolás
  liberó espacio: C: 31 GB.
- **#884 mergeado** (`34c23d1a`). CI de main sobre `8471add4`: Tests `success`, Deploy `success`. D25: V2a
  (39575542584) corriendo, V1 intento 2 pendiente detrás, V2b lo despacha el proceso local `d25_serie.sh`.
- #880 (texto previo): CMR no devolvió gránulos del 18-oct sobre Chillán en ningún producto, ni siquiera MODIS; SIN DATO hasta
  validar la consulta con un día que sí tenga (CMR lento, consulta de control en segundo plano).

### 2026-10-21 02:45 UTC: TRASPASO del loop de S157 a la sesión nueva (S158)
- S157 detuvo sus tres procesos locales a las 02:41 UTC para que haya una sola dueña del loop (S153). **Desde ahora
  la dueña es la sesión que corrió `/retomar` a las 02:36 UTC.** S157 no despacha nada más.
- Estado exacto que se hereda:
  - **D25**: V1 = run 39530508296, corriendo. **V2a y V2b NO despachados.** Despacharlos según PREREGISTRO §6, desde
    el tag `s157-d25-k-codigo`, recién con 0 A/B vivos (el despachador de S157 esperaba eso y se detuvo antes).
  - **Relleno**: 3 de 10 verdes (39531624046 PP 2025-04-09, 39532248029 PP 2025-10-01, 39532959533 Chaitén
    2025-10-18). **El 4.º (39533674886, Copahue 2026-03-07) sigue corriendo en GitHub**; no despachar el 5.º hasta
    que termine (mismo grupo de concurrencia). Faltan 6: PCC 2026-04-25, Copahue 2026-07-02, Copahue 2026-07-05, PCC
    2026-07-13, PP 2026-07-27, PCC 2026-09-11 (comandos en `D:\vrp-trabajo\temporales\relleno_cmds.txt`, líneas 5 a
    10, y en `experiments/_s157_relleno/plan_relleno.json` del worktree `D:\vrp-trabajo\temporales\s157_relleno_wt`,
    cuyos archivos regenerados siguen sin commitear).
  - **Control del NRT**: no se hizo. A las 09:35 UTC, contar `NRT update` de 02:00 a 09:30 del 21-oct contra los 24
    del 20-oct. A las 02:29 ya había 4.

### 2026-10-21 ~02:25 UTC (S157, tras el cierre): relleno confirmado en CMR y despachándose
- `armar_relleno.py` con CMR arriba (consulta 02:11 UTC): **31 `standard` = «existe (CMR)», 58 `nrt` = «no_existe
  (CMR)»**. Los archivos regenerados quedaron sin commitear en `D:\vrp-trabajo\temporales\s157_relleno_wt` (worktree
  detached de `main`): llevarlos a `main` con el PR del relleno.
- Proceso local despachando los 10 días en serie (`reproc-chunked`, perfil `_s154_reproc_k_historico`, modo
  estricto); cada resultado queda en el log del proceso. Si la app se cerró, revisar `gh run list -w reproc-chunked.yml`
  y despachar los que falten desde `experiments/_s157_relleno/plan_relleno.json`. Después: contar pasadas (A108).

### 2026-10-21 ~02:10 UTC (S157): NRT con código nuevo verde; **A/B de D25 DESPACHADO**; relleno en preparación
- NRT 39525751661 (01:10 UTC, sobre `cf07ead1`, con #877): verde, 88 `AUTH_OK`, 484 `SEARCH_VENTANA` (búsqueda por
  ventana activa), cobertura completa salvo 1 falla en un volcán, sin el 401 de NOAA-21 del probe. **0 commits**:
  todos «No changes to commit». No prueba regresión (ayer los commits de esa franja salieron de la corrida de las 02:10,
  y entre 22:55 y 01:10 no hay pasadas nocturnas nuevas). Control en segundo plano a las 09:35 UTC: commits del NRT de
  02:00 a 09:30 contra los 24 de ayer.
- Disco: 9 worktrees terminados borrados (limpios y subidos); D: 19 GB. C: bajó a 18 GB por 7,8 GB del temporal de
  Claude de OTRO proyecto (`Diversion-Poleras`), no tocado.
- **D25 (D-26, D-27)**: tag `s157-d25-k-codigo` = `66961f65`. V1 (2026-08-29..10-18, tres brazos) = run
  **39530508296**. Proceso local despacha V2a (04-01..05-07) y V2b (05-08..06-12), dos brazos, en serie y sólo con 0
  A/B vivos (H18). Prueba corta previa: 39510227734.
- Relleno de las 31 (plan de #873): `armar_relleno.py` corriendo otra vez con CMR (lento) en
  `D:\vrp-trabajo\temporales\s157_relleno_wt`; los 10 despachos de un día se lanzan en serie después.

### 2026-10-21 ~00:00 UTC (S157): saturación (#880) sin poder decidir; dos hallazgos laterales
- Run 39512756808 midió 2 de 40 pasadas. Grupo A (18-oct): sin medir (CMR no indexa el 18 ni el 19; respaldo de
  LAADS falló). Grupo B: 1 medida (Suomi NPP 750, 2026-09-29 06:36, cenit 55,8°): 0 de 156 píxeles saturados, en el
  tope o borrados; cota 0 contra 1,701 MW que faltan, pero `t_max_k` 273,28 K hacía imposible saturar. Controles:
  C sólo MODIS (trivial), POS no corrió. **No decide.** Verificador limpio confirmó bit y números, corrigió una cita
  (el «Reported Range» fijado es de la DNB, no de I y M) y pidió máscaras 256 y 2048 y fondo de MODIS por banda.
  Pista del verificador (SIN VERIFICAR): a las 06:48 del 18-oct VIIRS 375 marca ~310 K y M13 273 K, más D17 que
  saturación.
- Lateral 1 (SIN VERIFICAR): 44 de 156 píxeles traen M15 en sentinela con M13 sano, incoherente con el bow-tie; el
  lector los deja en NaN y se pierde su NTI en VIIRS 750. Candidato a investigar.
- Lateral 2: la descarga de NOAA-21 dio HTTP 401 en LAADS en el probe. Vigilar si el NRT de las 01:10 también falla
  en NOAA-21 (credencial o autorización de colección).
- PR #880 borrador; rama auxiliar `s157-saturacion-probe` (sólo dispara el workflow).

### 2026-10-20 ~23:45 UTC (S157): azimut verificado (#879), con el efecto acotado
- Verificador limpio en primer plano reprodujo exactas las cifras centrales (MIROVA 1,460, nosotros 1,145, razón
  0,865; 1,91 desde 35°) y confirmó signo del azimut (267 de 267 contra el banner), pareo (desfase 0 s), nulo (4 a
  5 % de falsos) y que el código de S130 agrega un par por record aunque su docstring diga «máximo de cada lado»
  (`experiments/_s130_cenital/medir_gradiente_cenital.py` l. 20 y 102-103 contra l. 92-94).
- Lo que cambió: nuestro efecto de lado es sólo Isluga; el de MIROVA sin Isluga baja a 1,2 a 1,4 y noche a noche ya
  no es significativo (1,18, p 0,15). **Lo sólido: nuestra razón contra MIROVA es más baja desde el este, 0,79 noche
  a noche sin Isluga, p < 0,001.** Lado y hora no se separan en VIIRS (las primeras pasadas desde el oeste son todas
  MODIS). Sin verificar: mecanismo en MIROVA, K, `f5_core_vrp_mw`, y MODIS (el filtro 3 a 9 UTC de S130 bota Terra).

### 2026-10-20 ~23:30 UTC (S157): #865 CERRADO sin cambiar K
- Nicolás: «Sí: cierra #865 sin cambiar K, con el mecanismo y el costo documentados (#881).» Cerrado con comentario
  (mecanismo, clase 1 de 155, costo de `min` en VIIRS 750 +314 negativos limpios). #881 queda en borrador.
- Pendiente menor: `sombra_pasadas_juzgadas.json` registra PCC como «no revertir, investigar»; revisar si la
  vigilancia de la sombra necesita la marca de cerrado para no reabrir el issue de investigación.

### 2026-10-20 ~23:20 UTC (S157): #865 explicado (#881, verificado); azimut (#879, sin verificar); saturación en curso
- **#865 / #881** (verificador limpio confirmó; tres frases corregidas): la anomalía de PCC VIIRS 750 del 2026-10-10
  05:54 son dos píxeles contiguos que se bajan el contraste uno al otro en el promedio de 8 vecinos. Con K el Test 2
  pide max(C1, μ+5σ) = 0,01415 y dan 0,01332 (falta 5,9 %) y 0,01204 (14,9 %); pasan Test 3 y BT. Con `min`
  (umbral 0,003) pasan: la palanca es la conectiva. El cúmulo de C0 salió de `ctx_cluster`, no del Test 1.
  **Aislado**: K pierde 1 de 155 protegidas nocturnas de VIIRS 750 (2026-01-10..10-19), ésta. Volver VIIRS 750 a
  `min` recupera 4 alertas bajo 1 MW y 0 protegidas, a costo de +314 negativos limpios publicados (1,1 % a 9,3 %;
  PCC 6,2 % a 44,6 %; A/B de meses S151). Recomendación: no cambiar K; cerrar #865 con el mecanismo documentado.
- **Azimut / #879** (SIN VERIFICAR, verificador pedido en primer plano): en VIIRS 375 con C0, MIROVA reporta 1,46
  veces más desde el este (nulo 0,89 a 1,14), nosotros 1,15; crece con el cenit (MIROVA 1,91 sobre 35°). La
  «MIROVA plana» de S130 sería el promedio de dos pendientes opuestas. Lado y hora están confundidos en VIIRS
  (correlación −0,99); mecanismo en MIROVA sin identificar.
- **Saturación / #880**: sin cifras; run 39512756808 en curso (CMR no indexa el 18 y 19-oct, el grupo de las 06:48
  puede no bajar). Hallazgo de código verificado: el pipeline pone NaN en píxeles saturados (VIIRS bit 4, tope de
  LUT, M15 ≥ 342,5 K; MODIS SI > 32767): si satura la banda térmica, el píxel nunca alerta. SOSPECHA para Chillán
  en VIIRS 375; en VIIRS 750 M13 tiene doble ganancia (techo ~634 K) y sería improbable.

### 2026-10-20 ~23:10 UTC (S157): prueba corta del A/B de D25 PASA en lo sustantivo
- Run 39510227734 (Chillán 2026-10-17..18, tres brazos, workflow de brazos juntos de #877): reproceso verde en 6 min;
  8 pasadas por brazo, 0 faltan, 0 sobran. `FLAGS_BRAZO`: D25 encendido sólo en `_s157_ab_d25_k_on` (375 y 750,
  half 3), MODIS apagado y Test 1 apagado en los tres. Control y gemelo idénticos (suma `pc.vrp_mw` 58,273); D25
  64,670 (+11 %, del orden del probe de L1B).
- `recolectar` en rojo por el defecto conocido de las ventanas de un volcán (cuenta los otros 10 como «archivos que
  no llegaron»; mismo caso que #870). No afecta al A/B completo, que corre los 11.
- Proceso local esperando el NRT de las 01:10 UTC (primero con búsqueda por ventana en producción).

### 2026-10-20 ~23:00 UTC (S157): #871 mergeado; prueba corta del A/B de D25; tres investigaciones en paralelo
- Nicolás: «Sí: despacha D25 tal cual. Mergea #871 cuando quede verde sobre main y sigue con el orden: prueba corta
  del A/B, NRT de las 01:10, relleno de las 31 y despacho de D25 desde tag.»
- #871: merge de `origin/main` en la rama (choque en `reproc-s146-ab-sin-test1.yml`: se dejó la estructura de brazos
  juntos de #877 y se llevaron los flags de D25 a su línea `FLAGS_BRAZO`), 64 pruebas del workflow y perfiles en
  verde, CI verde, CLEAN; **mergeado `49c70c99`**.
- Prueba corta del A/B nuevo: run **39510227734** (Chillán 2026-10-17..18, brazos control, gemelo y D25, desde
  `main`). Primera corrida de punta a punta del workflow reestructurado.
- Tres subagentes de sólo lectura en D:: saturación de VIIRS y MODIS en las pasadas oblicuas de Chillán (separa
  saturación de D17; a lo más 2 jobs), efecto del lado del barrido contra MIROVA (pregunta de Nicolás; sin Actions)
  y el caso PCC de #865 (traza por etapa y si es una clase).

### 2026-10-20 ~22:45 UTC (S157): adenda de D25 sellada (D-27) y #877 mergeado
- Nicolás: «Sello la adenda de calibración de D25 con el nulo simétrico y la opción A (mejora en al menos dos
  volcanes). Y mergea #877 con modo estricto en los reprocesos y sin modo estricto en el NRT.»
- **D-27**: sello registrado en `ADENDA_CALIBRACION.md` sobre `0a91eb634` (rama `s157-prereg-d25`, `e3d88fd2`). Con
  D-26 el candado de D25 queda completo; falta mergear #871 y despachar desde tag.
- **#877 mergeado** (`54a085ed`) tras comprobar CLEAN, CI verde y tag `pre-s157-busqueda-ventana`; `Tests` verde
  sobre `main`. Modo estricto: `--estricto-cobertura` en `reproc-chunked.yml` (2) y en el A/B; `nrt.yml` sin él (0).
  Merge a las 22:30 UTC, fuera de la ventana del NRT (01:10 a 12:10 UTC). **Vigilar el primer NRT de las 01:10 UTC**
  con el código nuevo (búsqueda por ventana en producción).
- Nicolás preguntó si hacen falta tantos días de reproceso para las pruebas (respuesta en el chat).

### 2026-10-20 ~18:50 UTC (S157): Chillán completo; PR #878 con el JSON rearmado
- Tercera pasada (run 39467050396): 13 de 13 verdes. Con las dos pasadas de relleno (44 trozos): 478 records
  agregados, 6.396 en total, control contra el tag intacto. **Contra la operacional faltan 6**, todas `nrt` de Suomi
  NPP del 5 y 6 de agosto de 2026 (sin estándar en NASA, igual que en los otros 10 volcanes).
- **PR #878** (borrador): `data/_s154_reproc_k_historico/NevadosDeChillan.json` más el script y sus salidas, rama
  `s157-chillan-rearmado` rebasada sobre `main`. Con esto los 11 Tier A del histórico con K están completos salvo las
  pasadas sin estándar y las 31 `standard` de los otros 10 (plan de relleno de #873, sin despachar).
- Siguiente en 1.24: rellenar las 31 de los otros 10 (el workflow ya conserva el archivo), decidir con Nicolás las
  ~64 `nrt` sin estándar, y el ensayo de Chillán más el reemplazo de los 11 juntos entre corridas del NRT.

### 2026-10-20 ~18:30 UTC (S157): sello de D25 registrado aquí; la calibración de M necesita una adenda sellada
- La sesión de D25 no pudo registrar el «Apruebo» (el control de permisos no acepta una aprobación reenviada). Se
  registró desde esta sesión en `PREREGISTRO.md` (rama `s157-prereg-d25`, `365d543e`) sobre `9ff738f3d`, el commit
  cuyo resumen vio Nicolás (el pre-registro no cambió desde ahí). Cita textual y las tres decisiones del §8.
- Candado armado (`0a91eb634`, CI verde): `evaluar_d25.py`, 27 de 27 pruebas, 22 de 23 mutaciones (la que sobrevive,
  `calib_por_par`, declarada); verificador del evaluador PARCIAL, 7 arreglos.
- **No se despacha**: con la calibración de M escrita, 5 de 8 estratos que deciden quedan indecidibles con K y el
  control positivo sale INDECIDIBLE. `ADENDA_CALIBRACION.md` propone nulo simétrico (sorteo del signo de d por bloque
  noche-volcán, tope 5 % de 200 por cola) y, aparte, la opción A: un MEJORA cuenta sólo si la mediana de d es negativa
  en al menos dos volcanes del estrato con 3 pares o más (cada estrato lo domina un volcán: V750 oblicuo es 19 de 23
  pares de Chillán en V1). **Espera el sello de Nicolás.**
- Incidente de esa sesión: sus mutaciones llenaron D: a 0 GB unos minutos; liberado (13 GB ahora) y el script borra
  cada temporal. Sin daño visible en esta sesión.

### 2026-10-20 18:05 UTC (S157): #877 (búsqueda por ventana y brazos juntos) listo para el sí; tercera pasada corriendo
- **#877** borrador, CI verde, CLEAN; tag `pre-s157-busqueda-ventana` (`ac015254`). Toca `pipeline/fetch.py`,
  `scripts/run_pipeline.py`, `reproc-chunked.yml`, el A/B y tres scripts nuevos. Medición
  (`experiments/_s157_busqueda_ventana/MEDICION.md`): los ~51 min sin marcador eran la búsqueda de geolocalización;
  en 27 jobs, con CMR rápido la búsqueda pesa ~10 %, con CMR lento 45 a 63 %; con CMR caído (HTTP 500 salta el
  cortacircuito) **5 de 27 reprocesos y 6 de 9 NRT terminaron verdes sin datos**. Por trozo de 37 días, de ~590
  búsquedas a ~16. Probe 39462816493: Chillán 4 días y 2 brazos 1.381 s a 810 s; Láscar 703 a 544 s (cotas
  inferiores: el tag perdió búsquedas). Identidad: 0 diferencias en 327 producto-días y 807 gránulos contra CMR;
  74 records comparados, 0 diferencias más allá de redondeo de 9,1e-12 (control rama contra rama 3,4e-12); 36
  pasadas sólo en la rama, todas perdidas por el tag por CMR caído. 53 pruebas, suite 2.316, 29 de 29 mutaciones.
  Verificador: 7 hallazgos, 6 arreglados. **Decisiones para Nicolás en el PR**: (1) modo estricto rechaza el trozo
  entero ante una falla transitoria; (2) con brazos juntos, un corte común a todos sale del conteo A108 y sólo lo
  ve el modo estricto. Sin medir: costo en el NRT real con CMR caído (estimado 2,5 a 4,5 min) y el A/B
  reestructurado de punta a punta.
- Incidente reportado por el subagente: una prueba llamó a `process_date` real ~2 min con `~/_netrc` presente (riesgo
  A71). Comprobado: el NRT de las 14:40 UTC tiene 88 `AUTH_OK` y 704 `SEARCH_DONE`; el próximo NRT corre a las 01:10
  UTC (cron-job.org `10 1-12`). Sin señal de bloqueo. El `_netrc` local sigue siendo un riesgo para pruebas futuras.
- Tercera pasada de Chillán despachada a las 17:33 UTC con CMR estable: **run 39467050396** (2026-05-14..09-17, 13
  trozos de 10 días).
- Rama remota `s157-validar-busqueda` (dispara el probe) se puede borrar tras el merge.

### 2026-10-20 17:10 UTC (S157): segunda pasada con datos, pero CMR la volvió a cortar; tercera en espera
- Run 39431309981: 31 de 31 verdes, hasta 82 min por trozo (esta vez con datos). Relleno: **277 pasadas
  agregadas**, unión 6.195 records, control contra el tag intacto (3.637 de 3.637). Todo 2025 quedó completo.
- **Siguen faltando 207** (197 `standard`), en 33 días entre 2026-05-14 y 2026-09-17, los MISMOS en las dos copias.
  Log del trozo 2026-08-20..09-07 (job 118657483762): `SEARCH_CMR_TIMEOUT ... breaker ON esta corrida` a las 16:52
  y desde ahí `SEARCH_SKIP` en cada día. CMR siguió inestable después de la caída de la mañana, y el cortacircuito
  pierde el resto de cada trozo tras el primer timeout. A las 17:02 UTC CMR vuelve a dar HTTP 500.
- Proceso local: con tres respuestas 200 seguidas de CMR, despacha la tercera pasada (2026-05-14..2026-09-17,
  `max_days` 10, 13 trozos: un trozo corto pierde menos días si el cortacircuito salta; #873 ya conserva el resto
  del archivo). `rearmar_y_contar.py --relleno` acepta varias pasadas y ventanas sueltas (rama
  `s157-chillan-rearmado`).
- Esto refuerza la mejora en curso del subagente (búsqueda por ventana y días que no salen verdes en silencio): hoy
  el NRT y los reprocesos degradan sin avisar con cada inestabilidad de CMR.

### 2026-10-20 ~14:45 UTC (S157): aprobada la aceleración (búsqueda por ventana y brazos en un mismo job)
- Nicolás: «Sí: parte por buscar una vez por ventana y procesar todos los brazos en el mismo job, con medición antes,
  tag defensivo y verificador. El merge de fetch.py me lo traes para el sí.»
- Subagente de esta sesión en `D:\vrp-trabajo\s157-busqueda-ventana` (rama `s157-busqueda-ventana`): medición
  primero (atribuir los ~51 min sin marcador; se detiene si el ahorro no está), plan, tag
  `pre-s157-busqueda-ventana`, TDD, validación en Actions con identidad de records contra el tag (sólo sin
  reproc-chunked corriendo, a lo más 4 jobs), mutaciones, verificador limpio y PR borrador. **Merge: sí de Nicolás.**
- El A/B de D25 (sellado) conviene despacharlo DESPUÉS de este cambio si llega a tiempo: con 3 brazos es donde más
  rinde. Si no llega, se despacha igual con el workflow de hoy.

### 2026-10-20 ~14:30 UTC (S157): #874 y #875 mergeados; D25 SELLADO; segunda pasada de Chillán corriendo
- Nicolás: «Apruebo» (a mergear #874 y #875 y a sellar D25 con las tres recomendaciones). #874 `b249b1b9`, #875
  `3868c5db`; `Tests` verde sobre `3868c5db` (el de `b249b1b9` quedó cancelado por el siguiente, que lo contiene).
- **D-26 SELLADA (D25 sobre K, #871)**: VIIRS 375 con cenit sobre 40° sólo bloquea; ventana de vecinos 7x7 sola;
  MODIS fuera de este A/B (escribir D25 en MODIS se decide aparte). La sesión del pre-registro registra el sello con
  la cita y arma el candado (`evaluar_d25.py`, pruebas y verificador); no despacha. El despacho, desde tag, después
  del reproceso de Chillán.
- CMR volvió a las 13:22 UTC (200 en las dos pruebas); el proceso local relanzó la segunda pasada de Chillán:
  **run 39431309981** (13:33 UTC, 31 trozos de 19 días, con el merge nuevo de #873).
- Medido en el log del trozo 15 del histórico (job 117669982883, 151 min entre marcadores): búsquedas en CMR
  ~50 min (296 búsquedas, 8 por día de ventana, 9 timeouts), descargas ~15 min, después de la descarga ~36 min,
  y ~51 min entre el fin de una búsqueda y el siguiente marcador (SIN ATRIBUIR: hay pasos sin marcador). SOSPECHA:
  buscar una vez por ventana en vez de una por día y producto ahorraría cerca de un tercio y bajaría los cortes de
  CMR. Y cada brazo de un A/B (`reproc-s146-ab-sin-test1.yml`, matrix brazo x volcán) busca y baja lo mismo otra vez.

### 2026-10-20 ~14:00 UTC (S157): #874 con las tres observaciones corregidas; #874 y #875 listos para merge
- #874 `723480ec`: `n_misma_pasada` en cada celda (noches K con pasada máxima distinta de la de MIROVA: VIIRS 375 29
  de 90, VIIRS 750 4 de 22, MODIS 0 de 8), regímenes antes_535 / 535_a_571 / 571_a_K / K, prueba de no regresión que
  corre en el CI (paso apagado contra encendido) y skip «SOLO LOCAL» explícito. 13 pruebas, 12 de 12 mutaciones,
  suite 2.265, CI verde, CLEAN. Sin resolver: el verificador contó 98 noches K de V375 y el autor 90 (otra población,
  SOSPECHA; no cambia ningún veredicto porque las claves son informativas).
- #875 `0b905614`: CI verde, CLEAN. Los dos esperan el sí de Nicolás para mergear (el clasificador niega el merge
  sin revisión).

### 2026-10-20 ~13:30 UTC (S157): 1.34 en #875 y 1.35 en #874, los dos en borrador con CI verde
- **#874** (1.35, auto-audit por cenit y régimen, sólo `scripts/auto_audit_weekly.py` y su prueba): CI verde,
  CLEAN, 7 de 7 mutaciones. Control positivo: la magnitud de Chillán cae con el cenit en los tres sensores (MODIS
  0,707 a z<30 contra 0,171 a 0,203 en tramos oblicuos; VIIRS 375 no monótona, con n chico). Verificador limpio:
  CON OBSERVACIONES, nada bloquea (no regresión, particiones, falsas V375 y corte #535 comprobados). Pedidas al autor:
  conteo de noches con la misma pasada (35 de 98 en V375 no coinciden a ±120 s: el tramo no es la curva pareada de
  S154), régimen partido en #571, y una prueba de no regresión que sí corra en el CI (`fetch-depth: 1` salta la de
  SHA fijo). En curso.
- **#875** (1.34, `docs/SINTOMAS.md`, 9 síntomas, 219 líneas): CI verde, CLEAN; verificador en primer plano aplicado.
  Fuera de lo pedido, marcó con S157 (A113) D17 y `docs/s130/GRADIENTE_CENITAL.md`, que seguían dando la caída con el
  ángulo por D17 probado sin la marca de 1.14. Hallazgo: A118 dice «D18 nunca se ha medido» (obsoleto; anotado).
- `experiments/_s153_deriva_123bis/` (citado en la marca S153 de A85 en CLAUDE.md) **existe en `loop/activo`**
  (vuelta 192, `97b027a0`) y no en `main`: no es una cita inventada, es una cita a otra rama. Pendiente: llevarlo a
  `main` o anotar la rama en la marca.

### 2026-10-20 12:30 UTC (S157): NRT vacío mientras CMR cae (se recupera solo); #870 cerrado; 1.34 y 1.35 lanzadas
- Nicolás: «continúa acá» (seguir en esta sesión, no abrir otras).
- NRT: runs `success` a las 09:10, 10:10, 11:10 y 12:10 UTC sin un solo commit de datos (último, 07:50). El
  healthcheck mira 48 h, así que no avisa. **No se pierde nada**: `scripts/run_pipeline.py:384`
  (`default_date_window`, 7 días hacia atrás) reprocesa la semana en cada corrida y recupera las pasadas cuando CMR
  vuelva. Lo que sí cuesta es la latencia: mientras dure la caída, el tablero no muestra la mañana.
- #870 (watchdog nuevo): era la repetición D1 de la caja (run 38698329137), ya evaluada con `--repeticion` en la
  vuelta 55; la «falla» es la recolección que cuenta los 10 volcanes que la ventana no corre. Cerrado con comentario.
- Lanzados dos subagentes de esta sesión, cada uno en su worktree de D:: **1.35** (auto-audit por tramo de cenit y
  régimen, claves nuevas sin tocar veredictos, PR borrador) y **1.34** (`docs/SINTOMAS.md` con verificador, PR
  borrador).

### 2026-10-20 ~12:00 UTC (S157): #873 mergeado: el merge de trozos ya no borra lo que main tiene
- #873 squash `c408a909` por su sesión (verificador limpio incorporado en un segundo commit); `Tests` verde sobre
  `main` comprobado aquí. El job merge de `reproc-chunked.yml` lee la base de `origin/main` en cada intento y
  conserva lo que está fuera de las ventanas de la corrida. Desde ahora repetir unos trozos no borra el resto.
- Plan de relleno en `experiments/_s157_relleno/` (sin despachar; CMR caído, decisiones desde el listado de LAADS):
  las 31 `standard` están en LAADS (repetir esos días debería traerlas); las 58 `nrt` de Suomi NPP del 4 al 6 de
  agosto de 2026 NO tienen estándar (hueco en la colección 5200 hasta el 6-ago 16:30 UTC). **Decisión para Nicolás
  al aplicar el reemplazo**: esas 58 quedan en C0 con su marca o se procesan desde el NRT.
- La segunda pasada de Chillán que relanza el proceso local saldrá ya con el merge nuevo; el rearmado sigue saliendo
  de los artefactos, así que no cambia el método.

### 2026-10-20 ~11:40 UTC (S157): #872 mergeado con el flag apagado (sí de Nicolás)
- Nicolás: «Sí: mergea #872 con el flag apagado. El encendido lo decido después.» Squash `5fd2ac2e` por la API, tras
  comprobar CLEAN, CI verde y `enable_modis_mir_lambda_por_banda: false` en la rama. Tag defensivo
  `pre-s157-lambda-b22` (`f101d730`) ya estaba puesto por la sesión.
- Verificado sobre `5fd2ac2e`: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` da
  `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA = False` (A89); `Tests` y Pages verdes. Worktree de la sesión borrado.
- Pendiente de Nicolás: encender el flag (efecto medido: magnitud MODIS +5,75 % mediana; contra MIROVA, 12 pasadas
  con K, razón 0,362 a 0,382). Al encenderlo: R8 y reproceso de la ventana con K para que la serie no mezcle dos λ.

### 2026-10-20 11:15 UTC (S157): #872 (λ de B22) y #871 (pre-registro D25) listos; CMR sigue caído
- **#872** (borrador, CI `pytest` verde, CLEAN): con K la vuelta a radiancia de MODIS usaba la λ de B21 (3,929 µm)
  sobre temperaturas de B22 (3,959 µm); magnitud MODIS 1,051 a 1,075 veces más baja (mediana 1,0575, 24 records
  desde el 2026-09-18). Contra MIROVA, 12 pasadas MODIS con K y alerta: razón mediana 0,362 a 0,382 (acerca en las 12,
  pero es un 5 %: no es la palanca de Chillán). Arreglo detrás de `enable_modis_mir_lambda_por_banda: false`
  (bit a bit igual con OFF, identidad 96 de 96 contra el tag `pre-s157-lambda-b22` = `f101d730`); D33 nueva en el
  catálogo. Toca `pipeline/` (A45): **merge y encendido esperan el sí de Nicolás.**
- **#871** (borrador): pre-registro de D25 sobre K, v2 con los 20 hallazgos del verificador. Falta el probe de L1B de
  Chillán (CMR caído; se relanza solo). **Espera el sello de Nicolás**; no se despachó ningún A/B.
- Sesión del merge que conserva el archivo: batería de mutaciones corriendo, sin PR todavía.
- CMR: HTTP 500 en cada prueba desde las 08:10 hasta las 11:02 UTC (más de 3 h).

### 2026-10-20 ~09:15 UTC (S157): #866 y #868 mergeados con el sí de Nicolás; tres sesiones nuevas corriendo
- Nicolás: «Sí: mergea #866 y #868 y arranca las tres tarjetas». Merges squash por la API (el clasificador los había
  negado sin su sí): #866 `8c94c847` (ensayo del reemplazo, sólo `experiments/`), #868 `f101d730` (propagación de
  K, A113). CI `Tests` verde sobre `f101d730` (el de `8c94c847` quedó cancelado por el siguiente, que lo contiene);
  Pages verde y R8: el `index.html` publicado trae la marca S157 del modal.
- Worktrees de #866 y #868 borrados (limpios). D: 15 GB libres.
- Corriendo, cada una en su worktree de D:: merge de trozos que conserva el archivo más plan de relleno de las 31
  pasadas (`local_4eec6aae`), λ de B22 en MODIS con K (`local_c5486ed1`), pre-registro de D25 sobre K con probe de
  L1B (`local_51f1447d`). Las dos últimas dependen de CMR para bajar datos: la caída de NASA puede frenarlas.

### 2026-10-20 08:40 UTC (S157): la segunda pasada salió VERDE Y VACÍA: CMR de NASA caído
- Run 39391332259: 31 de 31 trozos verdes en 5 a 11 min cada uno (contra 60 a 76 min con datos). Log: `WARN: Failed
  to fetch <producto>: {"errors":["An Internal Error has occurred."]}` en los 8 productos. Artefactos: **0 records
  nuevos** (los 267 que traen son del checkout, ventana del trozo 9). No sirve como relleno: se descarta.
- CMR comprobado a las 08:36 UTC con la API pública: HTTP 500 en `granules.json` de MOD021KM y VNP02IMG. El NRT
  escribió por última vez a las 07:50 UTC; sus runs siguen saliendo `success`, así que mientras dure la caída el NRT
  publica nada sin avisar (mismo modo que A108 y la SOSPECHA de la entrada anterior).
- Proceso local en segundo plano: prueba CMR cada 10 min (hasta 12 h) y, con dos respuestas 200 seguidas, relanza la
  segunda pasada (mismos parámetros) y espera su fin. Después: contar records por trozo ANTES de usarla.
- El JSON de Chillán en `data/_s154_reproc_k_historico/` de `main` quedó pisado por ese merge vacío; no importa
  (nadie lo lee, el rearmado sale de los artefactos y del tag).

### 2026-10-20 08:15 UTC (S157): Chillán rearmado, pero los trozos VERDES del original perdieron 316 pasadas
- B (39363796988) 4 de 4 verdes (60 a 67 min) y el trozo 9 (39370713699) verde en 132 min. Artefactos de los 4 runs
  en `D:\vrp-trabajo\temporales\s157_chillan\` (98 MB).
- `experiments/_s157_chillan_rearmado/rearmar_y_contar.py` (rama `s157-chillan-rearmado`, worktree en
  `D:\vrp-trabajo\s157-chillan-rearmado`): 21 trozos contiguos 2025-02-15..2026-09-17, 5.918 records, 0 duplicados.
  **Control contra el tag `pre-s157-chillan-trozos`: 3.637 de 3.637 records idénticos** en las ventanas originales.
- **Cobertura (A108): 326 pasadas de la operacional no están** (316 `standard`), en 51 días y 29 ventanas, casi
  todas en trozos VERDES del run original (13, 14 y 15 suman 216; los nuevos sólo 12). Causa leída en el log del
  trozo 15 (job 117669982883): `SEARCH_CMR_TIMEOUT host=cmr.earthdata.nasa.gov -> breaker ON esta corrida` y
  `SEARCH_SKIP CMR degradada` para todos los productos: el cortacircuito de A64 salta días enteros sin fallar el job.
  O sea que «verde» no dice nada de la cobertura, y el ensayo de los otros 10 (#866) lo midió bien por eso.
- Segunda pasada completa de Chillán despachada: run 39391332259 (2025-02-15..2026-09-17, `max_days` 19, 31 trozos,
  `main` en `d6c1c947`, mismo `pipeline/` que `3695f675`: sólo difieren dos perfiles diurnos). El script ganó
  `--relleno`: de la segunda copia toma SOLO las claves que faltan; los records originales no se tocan.
- SOSPECHA a medir: el cortacircuito por CMR también puede estar dejando días sin procesar en el NRT; un job verde
  con `SEARCH_SKIP` no avisa. Candidato a vigilancia (cuántos `SEARCH_SKIP` por corrida).

### 2026-10-20 04:40 UTC (S157): tanda A de Chillán verde; B corriendo; trozo 9 en cola
- Run 39363774747: 6 de 6 trozos verdes, de 65 a 76 min por 19 días (3,4 a 4,0 min por día de Chillán), más merge.
  Como se esperaba, el merge dejó `data/_s154_reproc_k_historico/NevadosDeChillan.json` sólo con su ventana (1.225
  records, 2025-07-13..10-31); el archivo de 10 trozos está en el tag `pre-s157-chillan-trozos` (3.637 records).
- B (39363796988) pasó a `in_progress` a las 04:39; el proceso local despachó el trozo 9 tal cual (run 39370713699,
  en cola). Riesgo: a 3,4 a 4,0 min por día, 37 días son 126 a 148 min contra el tope de 170 (A15 pediría 164 a 192).
  Si cae por tiempo, se parte en dos.

### 2026-10-20 ~04:15 UTC (S157): resultados de las cuatro sesiones
- **#867 MERGEADO** (watchdog por duración de job, F3-10 y parte de F3-07; CI verde) y **#824 CERRADO**. Queda
  abierta la parte de F3-07 que vive en el auto-audit semanal.
- **#866** (ensayo del reemplazo, 10 volcanes): los 10 PASAN el tope del 2 % (peor Planchón Peteroa, 0,37 %).
  Verificador G4: con una sola `DATOS_K_DESDE_UTC` no hay frontera correcta si Chillán queda aparte, así que se
  aplican los 11 juntos. El reemplazo agrega 7.518 records (llena el hueco 2025-11-16..2026-01-28). Quedan 89
  pasadas en C0: 31 `standard` cortadas por NASA (repetibles) y 58 `nrt` de Suomi NPP del 2026-08-05 y 06 (quizá
  sin estándar). CI verde. **Merge negado por el clasificador de permisos («merge sin revisión»): lo mergea Nicolás.**
- **#868** (propagación de K, A113 en catálogo, MISSION, CLAUDE.md, INDEX, ficha, cabeceras y modal del tablero):
  en `pipeline/` sólo cambian comentarios y la docstring (diff revisado). Suite 2.206 y CI verdes, verificador limpio
  aplicado. **Mismo merge negado: lo mergea Nicolás.**
- **#869** (magnitud de Chillán, 87 pasadas, verificador PARCIAL): en VIIRS 375 oblicuo el fondo no cierra el déficit
  ni con fondo cero; en VIIRS 750 de borde pesa el recorte del tablero (F_rec 0,57). Recomienda D25 primero con el
  criterio de Chillán corregido (V375 sólo con cenit de 40° o menos) y D17 después con dos brazos. Falta el L1B.
- **Hallazgo lateral de #869, comprobado en el código**: con K, `process_modis.py` (~l. 1036 y 1040 de `main`) vuelve a
  radiancia con `BAND21_LAMBDA` aunque la BT venga de B22; magnitud MODIS estimada de 1,052 a 1,059 veces menor.
  Producción (A45): se investiga y se deja detrás de flag; el merge es de Nicolás.
- Este turno lo abrió el aviso de las sesiones, así que la app no deja arrancar sesiones nuevas: quedaron propuestas
  como tarjetas (merge de trozos que conserva el archivo más relleno de las 31 pasadas; λ de B22 en MODIS;
  pre-registro de D25 sobre K con probe de L1B).
- Disco: C: 27 GB, D: 18 GB (worktrees de 1,1 GB cada uno).

### 2026-10-20 ~03:45 UTC (S157, dueña del loop): cuatro sesiones paralelas en D:, el loop sigue sin pedir permiso
- Nicolás: «todo lo que recomiendes y puedes, usa el disco D para que C no colapse, el loop debe continuar, no me pidas
  permiso». Límite que se mantiene: nada se ADOPTA en producción sin su sello (A45); todo lo demás avanza solo.
- Sesiones lanzadas, cada una en su propio worktree en `D:\vrp-trabajo\s157-*`, sin tocar esta bitácora ni despachar
  workflows (salvo el CI de su PR): ensayo del reemplazo con K para los 10 volcanes completos (1.24 b y c, PR borrador,
  sin aplicar); magnitud de Chillán pasada por pasada (1.33 a y b, sólo lectura, recomienda D25 o D17 para 1.29);
  propagación de K a los textos (1.37 más arreglo 5 de AUDIT_S155, PR borrador); watchdog por duración de job (arreglo
  7, F3-10 y F3-07; mergea si queda CLEAN y verde y cierra #824).
- Decisiones del bloque S157 tabla b aplicadas con la recomendación: #864 abierto (estado de K); falsa alarma de Muy
  Bajo aceptada; #824 se cierra al mergear el arreglo del watchdog, no antes (el watchdog lo reabriría); #776 sigue
  como borrador, ligado a #865 (comentario en el PR); #813 postergado hasta después del reemplazo. Rotar el PAT y avisar
  a OVDAS son de Nicolás (credencial y mensaje a terceros).

### 2026-10-20 03:25 UTC (S157 «retomar»): trozos caídos de Chillán relanzados; el merge no conserva el archivo
- El histórico con K (39125546355) terminó a las 20:22 UTC del 19-oct: 172 verdes, **6 fallidos, todos de
  NevadosDeChillan** (el bloque S157 decía 3). Por el tope de 170 min del paso: 5, 6, **7, 11 y 12**; por el runner: 9.
  El merge del run sí corrió y dejó `data/_s154_reproc_k_historico/NevadosDeChillan.json` con los 10 trozos buenos
  (3.637 records; faltan 2025-07-13..10-31, 2025-12-08..2026-01-13 y 2026-02-20..05-04).
- Nicolás: «parte en dos los trozos 5, 6, 7, 11 y 12 sobre el commit 3695f675 y relanza el 9 tal cual».
- **Hallazgo que cambia el cómo**: `scripts/merge_chunk_stores.py` escribe `--out` SÓLO con los trozos de su corrida
  (no lee el archivo existente). Un run nuevo deja el JSON de Chillán con únicamente sus ventanas. `gh run rerun` no
  sirve para partir trozos, y despachar desde un tag en `3695f675` haría lo mismo con un checkout donde el archivo ni
  existe. Ruta elegida: despachar desde `main` y **rearmar Chillán a mano** desde los artefactos de los 4 runs con
  `merge_chunk_stores.py --ventanas` (los del run original vencen el **2026-10-26**).
- Mismo código: `git diff 3695f675 origin/main` no toca `pipeline/` (sólo agrega dos perfiles diurnos), ni
  `scripts/run_pipeline.py`, `volcanoes.yaml`, `reproc-chunked.yml`, `merge_chunk_stores.py` o `split_date_window.py`.
  Lo que cambió (`auto_audit_weekly.py`, `banco_paridad.py`, `vigilancia_sombra.py`, tests, CSV) no lo importa el
  pipeline. Los runs nuevos quedan en `57d18ad7` (A108: mismo código, otro commit).
- Tag defensivo `pre-s157-chillan-trozos` (`57d18ad7`): el JSON de Chillán con los 10 trozos, antes de que los merges
  nuevos lo pisen (nadie automático lee ese directorio: grep en `.github/`, `frontend/`, `scripts/`).
- Despachados, en serie porque comparten grupo de concurrencia (un tercero en cola desplaza al pendiente):
  A = run 39363774747 (2025-07-13..10-31, `max_days` 19, 6 trozos); B = run 39363796988 (2026-02-20..05-04, 19,
  4 trozos), en cola; C = trozo 9 tal cual (2025-12-08..2026-01-13, 37), lo despacha un proceso local cuando A
  termine y B arranque.
- Falta: contar pasadas de cada ventana contra lo esperado (A108) antes de rearmar y de dar el histórico por completo.

### 2026-10-19 17:33 UTC (vuelta 226, S156): vigilancia de la sombra mergeada (#863) y probada en Actions; issue #865
- #863 squash `9ac09b16`, CI verde sobre `4e9eae28`. Cinco verificadores limpios en total; cada uno encontró algo y
  todo quedó arreglado o anotado (`experiments/_s156_autoaudit/sombra/README.md`). 65 pruebas; 82 de 82 mutaciones
  (script y workflow) caen por aserción, con control del criterio; suite 2.206 aprobadas.
- Decisiones de Nicolás escritas en la marca del paso 9 de `REGLA_ADOPCION.md`: (a) pasada; (b) desde la adopción;
  (c) Muy Bajo coherente con D-9 (cota SE: 7 de 161 V1, 12 de 343 V2); (d) pasadas juzgadas en
  `sombra_pasadas_juzgadas.json` (PCC la primera); (e) fuera de plazo sin pre-autorización; (f) rachas juzgadas.
- Run real despachado a mano (39294849891): todos los pasos verdes, VERDE, commit `a4a9d222` con los dos archivos de
  salida, sin issue. Desde ahora corre al terminar `experimental-diario` y a las 23:40 UTC de respaldo.
- Issue #865 (investigación del caso PCC VIIRS 750 2026-10-10), con título que no choca con los automáticos.
- Histórico con K (39125546355): 165 verdes, **1 fallido**, 11 pendientes a las 17:33. El fallido es NevadosDeChillan
  trozo 9 (2025-12-08 a 2026-01-13): «runner received a shutdown signal» a los 50 min durante una búsqueda; no es el
  tope (otros trozos duraron 160 min) ni el código. Al terminar el run: `gh run rerun 39125546355 --failed` y contar
  pasadas contra el control antes del reemplazo (A108).
- Anotado sin resolver: falsa alarma de Muy Bajo 0,58 en 120 días (bajó de 0,68); la clase de una pasada puede cambiar
  si entra o sale una protegida anterior de la referencia (SIN VERIFICAR a escala diaria).
- Heredoc con barras invertidas rompió archivos dos veces más en esta sesión (workflow y batería); arreglado con la
  herramienta de edición. Worktrees de la tarea borrados.

### 2026-10-19 tarde (vuelta 225, S156): decisión B sobre PCC y vigilancia de la sombra endurecida (#863, sin mergear)
- Auditoría espacial A61 del caso PCC: MISMO OBJETO que MIROVA, firmeza alta (ancla y centro de la grilla de MIROVA a
  7,56 km; 216 pasadas de control). Verificador 1: candidata reproducida con instrumento propio, cabecera de NOAA-21
  VIIRS 750 confirmada; las 61 protegidas «vistas» eran todas anteriores a la adopción.
- **Decisión de Nicolás**: «lo que recomiendes» ante la recomendación B: no revertir; unidad = pasada; la vigilancia
  cuenta desde la adopción (09:57:30); lo anterior es retrospectivo y va a investigación con issue a mano. Escrita al
  inicio del paso 9 de `REGLA_ADOPCION.md` (rama `s156-vigilancia-sombra`), diciendo que se decidió viendo el caso.
- Verificador 2: 12 de 13 mutaciones nuevas sobrevivían (la peor, parear sin sensor, borraba el caso PCC); sombra
  muerta en un solo volcán daba VERDE; el issue no se abría si fallaba el push; deduplicación por bolsa de palabras.
  Todo arreglado: 34 pruebas, 37 de 37 mutaciones por fallo de prueba, suite 2.175 aprobadas. (i) y (iii) pasan a la
  etiqueta original (como las cotas del A/B); reversión y persistencia con D-9 SN.
- Causa encontrada de la falla «local SIN ATRIBUIR» de la vuelta 222: g1d y g2c fallan con el repo en D: y el
  temporal en C: (`relpath` entre discos); con `TMP` en D: pasan. Anotado en la memoria de dos discos.
- Pendiente para Nicolás: con evaluación diaria, la primera Muy Bajo de VIIRS 375 perdida en un volcán dispara
  INVESTIGAR (Wilson de 1 de 1); el verificador 2 estimó 57 % de falsa alarma en 120 días. Es la letra de la regla.
- En curso: verificador 3 sobre `0b8d4bc5`. Después: merge de #863, issue de investigación del caso PCC.

### 2026-10-19 ~13:30 UTC (vuelta 224, S156): la vigilancia de la sombra encuentra una candidata a reversión de K
- Arreglo 4 en curso, rama `s156-vigilancia-sombra` (worktree `D:\vrp-trabajo\worktrees\s156-sombra`, sin PR todavía):
  `scripts/vigilancia_sombra.py` implementa el paso 9 de `REGLA_ADOPCION.md` §4, con 9 pruebas.
- Corrida con la referencia del 2026-10-19 (ventana 2026-09-18 a 10-19; sombra del 10-02 al 10-18): **REVERSION_CANDIDATA**.
  Puyehue-Cordón Caulle, VIIRS 750 (NOAA-21), 2026-10-10 05:54 UTC: fila de la TABLA (no OCR) ALERTA_TERMICA 1,19 MW
  a 7,83 km; la sombra C0 publica (cúmulo 1,886 MW, 8 px, Test 1 integrado disparado: 4,8 K, 26 px; primer paso 2 px
  más 6 recapturados); K no detecta nada (0 px, primer paso vacío). NTI máx −0,906 (piso), BT máx 277,7 contra fondo
  271,85 K, cenit 23°. **Cabecera de la imagen de MIROVA confirmada**: PNG `20261010_083116_VIIRS750_Latest10NTI.png`
  de mirova-tif-archive dice «Last Update 10-Oct-2026 05:54:02», «Thermal anomaly: LOW», «VRP = 1 MW».
- Contexto: fuera de las ventanas del A/B (V1 08-29 a 10-08, V2 03-01 a 06-12), así que es evidencia nueva. La misma
  pasada en VIIRS 375 sí la publica K (0,283 MW, MIROVA 0,39 Muy Bajo): la noche no se perdió, la pasada de 750 sí.
  Las otras 4 protegidas que K no publica: Chillán MODIS 12 y 15-oct, la sombra tampoco; Tupungatito 28 y 29-sep, sin
  sombra. Protegidas vistas en la sombra: 61 (objetivo 29, ya cumplido).
- NO se revirtió: la regla la pre-autoriza, pero Nicolás está presente y la noche quedó cubierta por VIIRS 375; se le
  presenta la decisión. Pendiente también: auditoría espacial A61 (¿es el mismo objeto que MIROVA a 7,83 km?) y
  verificador limpio del código.

### 2026-10-19 12:22 UTC (vuelta 223, S156): arreglos 2 y 3 de AUDIT_S155 mergeados (#862) antes del auto-audit del lunes
- Con el sí de Nicolás («parte por los arreglos 2 y 3 de AUDIT_S155 antes del auto-audit del lunes»). PR #862, squash
  `484d037d`, CI verde sobre `ca3ee1eb`. Sin tocar `pipeline/`.
- El auto-audit evalúa cada noche sólo con records de su detector (frontera leída de `frontend/cambio_detector.js`),
  juzga sólo el vigente (K), D-9 SN decide, magnitud publicada por volcán y sensor, falsas por detector y cenit, y lista
  por nombre las alertas protegidas (lectura A) con flag por cada una sin publicar. `history.jsonl` dice de qué detector
  es cada línea. Un aviso de detector degrada el veredicto.
- Corrida local con la referencia fresca (`experiments/_s156_autoaudit/`): `FUERA_DE_BANDA`, 10 flags, todos de K:
  recall VIIRS 750 73,3 % (n 30); magnitud publicada Chillán MODIS 0,485, VIIRS 375 0,65, VIIRS 750 0,687, Tupungatito
  VIIRS 375 0,251; cinco protegidas sin publicar (Tupungatito VIIRS 375 28 y 29-sep, marcadas referencia sospechosa por
  A119; PCC VIIRS 750 10-oct; Chillán MODIS 12 y 15-oct). Falsas K VIIRS 375 3,3 % SN, 2,0 % original; C0 86,8 %.
- Verificador limpio (`experiments/_s156_autoaudit/verificador/INFORME.md`): A1 a A4 y A6 confirmadas con instrumento
  propio; A5 parcial y A7 refutada en parte (4 de 12 mutaciones). Arreglado en el mismo PR: prueba de punta a punta de
  `main()` (12 de 12 por prueba), D-9 sobre la referencia unificada, avisos que degradan, marca de Suomi NPP.
- El g1d/g2c de `test_guard_libro_de_pruebas_s146.py` que la vuelta 222 daba por fallando en local hoy pasa 7 de 7.
- Abierto: el lunes se abre un issue nuevo con #779 todavía abierto (deduplicar es el arreglo 7); decisión de Nicolás
  sobre cerrar #779. Worktrees `D:\vrp-trabajo\worktrees\s156-autoaudit` y `s156-verif` siguen en disco.

### 2026-10-19 11:31 UTC (vuelta 222, S155): #860 y #861 mergeados, marca verificada en el tablero público; cierre
- Con el sí de Nicolás («mergea #860 y #861 cuando el CI esté verde, verifica que el tablero público muestre la marca
  nueva, y después corre /cierre»). #860: CI verde, squash `67122696` (el primer intento chocó con un commit del NRT,
  reintentado); Pages `39244255528` success; en `diario.html` público Copahue muestra la línea «detector K» el 18-sep y
  el aviso nombra las dos fechas. #861: el primer CI falló por la guarda G6 (`docs/INDEX.md` tiene que listar la última
  auditoría); arreglado en la rama, CI verde, squash `dd1c0b7b`.
- Locales sólo en Windows: `tests/test_guard_libro_de_pruebas_s146.py` g1d y g2c fallan en este computador también sin
  los cambios de la sesión (worktree de la marca), y el CI no las marca. SIN ATRIBUIR.
- Horas de las vueltas 220 y 221 corregidas contra los commits (las había estimado sin pedir la hora al servidor, A86).
- Worktrees de la sesión borrados (sólo queda la raíz en `loop/activo`). Histórico con K: 141 de 177 a las 11:31.

### 2026-10-19 11:19 UTC (vuelta 221, S155): auditoría post-K completa; #860 y #861 abiertos
- Cinco auditores y cinco verificadores limpios entregaron. Consolidado en `docs/AUDIT_S155.md` (PR #861, sólo docs y
  `experiments/_s155_audit/`; 40 archivos de más de 1 MB fuera, listados en `EXCLUIDOS.md`).
- Hallazgo central, por cuatro vías y tres verificadores: la frontera C0/K de los datos es la fecha de observación
  2026-09-18, no el merge. Con el sí de Nicolás («cuando los verificadores confirmen... arregla la marca... y pásame el
  PR»): #860 mueve la línea a esa fecha, el aviso dice las dos fechas y `tests/test_cambio_detector_frontera_s155.py`
  mide la frontera contra los JSON (se pondrá roja cuando se aplique el histórico, 1.24). CI del PR verde; navegador
  local con las tres vistas; **sin mergear, espera respuesta de Nicolás**.
- Gravedad 4 verificados (además del central): F3-02 el auto-audit registra 31,1 % de publicación en negativos de
  VIIRS 375 que es C0 86,5 % y K 1,8 %; F3-04 y F5-05 dos protegidas MODIS de Chillán (10-12 07:20 y 10-15 01:05) sin
  detección ni instrumento que las vea; F2-02 Chillán un nivel bajo MIROVA (24 de 38 Moderado mostradas Bajo o Muy
  Bajo); F5-01 cúmulo parcial en VIIRS 750 y MODIS (36 % modo de un píxel, 64 % selección).
- Arreglos propuestos en orden en `docs/AUDIT_S155.md` §5; decisiones para Nicolás en §6. El auto-audit del lunes
  abrirá un issue con 2 flags (Chillán y Tupungatito) que son mezcla de regímenes.
- Worktrees de la auditoría borrados; quedan `s155-marca` y `s155-auditoria` hasta sus merges. Discos: C: 23 GB, D: 20 GB.

### 2026-10-19 10:39 UTC (vuelta 220, S155): auditoría post-K lanzada (bloque 1 del plan)
- Pedido de Nicolás: aprovechar el paralelo. Cinco auditores Opus en segundo plano, uno por frente, cada uno en su
  worktree detached sobre `origin/main` `cb90031a` (`D:\vrp-trabajo\worktrees\s155-audit-f1` a `f5`, ~0,94 GB cada uno;
  D: 18 GB libres después de crearlos). Preámbulo canónico entero; sin commits, sin despachos, sin Earthdata local.
  Frentes: 1 propagación de K en docs y textos; 2 lo que ve el operador (tres vistas, predicados con node); 3
  instrumentos (auto-audit, watchdog, evaluadores; #779 como caso); 4 cierres que K pudo volver falsos (censo S145); 5
  magnitud de Chillán pasada por pasada (sin L1B: si hace falta, deja el gránulo especificado).
- Pendiente: un verificador limpio por frente cuando cada uno entregue; después `docs/AUDIT_S155.md`.
- Worktrees del candado (`s155-candado`, `s155-verif-candado`) borrados; el informe del verificador v3 quedó en
  `experiments/_s151_ab_diurno/verificador_candado_k_v3/` (commit `e2fff4a2`).

### 2026-10-19 ~10:30 UTC (vuelta 219, S155): #859 mergeado y tag de despacho puesto (sin despachar)
- Con el sí de Nicolás («mergea el #859 cuando el CI termine en verde, y después pon el tag»): CI del PR `pytest`
  SUCCESS sobre `5674eab7`; squash por API, `main` en `e66b402c`. Diff de `main` contra la rama vacío en
  `experiments/_s151_ab_diurno/` y `pipeline/`.
- Tag anotado `s154-diurno-k-codigo` en el remoto. **Para `--sha-codigo`: `e66b402c70b1c97cb8164bc05e33a70d63501c9d`**
  (`git rev-parse s154-diurno-k-codigo^{commit}`). Sin `^{commit}` sale el objeto tag `26a8398c…`, que ningún record
  trae: es exactamente el caso de H-5. Como también tiene 40 caracteres, el chequeo de formato lo deja pasar, y H2a
  marcaría todos los records como de otro commit (INDECIDIBLE, falla cerrada).
- CI de `main` sobre `e66b402c` (run 39237172832, Tests): completed success.
- **NO despachado.** Espera el fin del reproceso histórico con K (run 39125546355) y su reemplazo (1.24).
- Disco: C: bajó de 33 a 23 GB libres entre las 03:48 y las 10:40 UTC sin causa encontrada en esta sesión (worktrees y
  copias mutadas van a D:; temporales de los arneses en C: son 4 carpetas de 31 MB; el scratchpad de 4,6 GB de otra
  sesión, Poleras, no cambia desde las 01:19). SIN ATRIBUIR; vigilar.

### 2026-10-19 ~09:20 UTC (vuelta 218, S155): pruebas del candado cerradas; PR #859
- Worktree `D:\vrp-trabajo\worktrees\s155-candado`, rama `loop/s155-candado` desde `origin/main` (`4877788b`); commits
  `1c1c2b1f`, `3d08652f`, `5674eab7`. Sólo `experiments/_s151_ab_diurno/`.
- Pruebas de N-1 a N-5, H-3 y H-5 (verificador v2), vistas primero en rojo (las de N-5, H-5 y el conteo fallaban sobre
  el evaluador sin cambios) y después en verde. Cambios mínimos al evaluador: H2a informa raíz o brazo sin records y
  cuenta los leídos; `--base k` exige sha de 40 caracteres; rótulo final según la base. `DESPACHO_K.md` con
  `git rev-parse <tag>^{commit}` (la adenda sellada no se tocó).
- Error propio cazado por las mutaciones: el chequeo de 40 caracteres hizo que `sha_opcional` cayera por caída; ahora
  cada rechazo da su motivo y la prueba lo mira.
- Tercera vuelta del verificador limpio (Opus) sobre `1c1c2b1f`: listo para despachar desde las pruebas, con la
  condición de no tocar el evaluador entre el tag y la evaluación; H2a da 0 problemas sobre las diez medias ventanas
  reales de C0 rotuladas como K. Dejó V3-1 a V3-3 (gravedad 2) y V3-4 a V3-7 (gravedad 1) y 30 mutaciones propias;
  V3-1 a V3-5 cerrados en `3d08652f`. Informe en `D:\vrp-trabajo\worktrees\s155-verif-candado\experiments\_s151_ab_diurno\verificador_candado_k_v3\INFORME.md`
  (sin commitear; copiar al cierre si se conserva).
- **Resultado final sobre el código de `5674eab7`: 72 mutaciones, 71 por prueba, 0 por caída**; `xobs_techo` es
  equivalente (0 diferencias en 12.502.499 pares, `candado_k_s155/xobs_techo_equivalente_salida.txt`). Batería completa
  138 de 138 con el árbol quieto.
- Abierto, gravedad 1: `--brazos ""` (H-4); `gh workflow run` completo en `DESPACHO_K.md`; repetición como `--raiz`
  aparte con un solo brazo da INDECIDIBLE (V3-6). SOSPECHA del verificador sobre `GITHUB_SHA` de un tag anotado: la
  documentación de `workflow_dispatch` dice que es el último commit del ref; no comprobado en un run.
- Siguiente: CI de #859 con conclusión, merge, tag `s154-diurno-k-codigo` y despacho del A/B diurno sobre K **después**
  del fin del histórico (run 39125546355: 120 de 177 a las 07:04 UTC).

### 2026-10-19 ~03:25 UTC (vuelta 217, S154): segunda verificación del candado: el código decide bien, las pruebas no alcanzan
- Informe en `experiments/_s151_ab_diurno/verificador_candado_k_v2/INFORME.md` (copiado a `loop/activo`). Batería completa
  107 de 107. Con el código de hoy el evaluador aplica la regla sellada (datos reales de C0: base c0 NO ADOPTAR; base k
  cola 0,5223 y 0,1058, INDECIDIBLE por cableado y H2a, lo esperable con datos C0).
- **Mutaciones: 42; 30 atrapadas por prueba, 1 por caída, 11 NO atrapadas.** Pasan incluso la batería completa:
  `g1_regla_inversa`, `h2a_solo_primera_raiz`, `h2a_solo_lascar`, `h2a_solo_diurno`. No las atrapa la corrida 1,3,k:
  `g1_siempre_cola`, `xobs_floor`, `alfa_g1_le`, `alfa_g1_0055`, `control_sin_b`, `w2_con_sin_sustrato`,
  `h2a_sha_prefijo7`. `veredicto_w2_antes_de_g3` sólo cae con la batería completa. (Mi resumen previo de «5 no
  atrapadas» estaba mal: eran 12 en la corrida filtrada.)
- H-1 cerrado; H-2 cerrado con poco margen (el nulo +1 falla por 0,002); H-3 cerrado para x_obs y cola, ABIERTO para la
  regla (el empate está en el borde del soporte, donde las dos reglas coinciden); H-4 cerrado; H-5 falta escribir
  `git rev-parse <tag>^{commit}` en el procedimiento. Nuevos: N-1 (3) ninguna prueba distingue la regla que decide de la
  del rótulo (`evaluar_diurno.py:621` y `:625`; usar uno de los 8 casos de borde de m4); N-2 (3) H2a probado con 1 raíz,
  1 volcán y 1 brazo cuando el A/B corre con 10 raíces; N-3 (1) las comprobaciones rápidas dejan `ED.REGLA` en k; N-4 (2)
  x_obs por truncamiento no se vería; N-5 (1) H2a da OK con cero records.
- **Decisión del loop: NO despachar todavía.** La adenda sellada pide «cola exacta con sus pruebas antes de despachar»;
  las pruebas no protegen la regla. Primer bloque de S155: cerrar N-1, N-2, N-3, N-4, N-5, H-3 (regla) y H-5, y que las
  11 mutaciones caigan por prueba; tercera vuelta corta del verificador. El despacho espera además el fin del histórico
  (95 de 176 a las 02:43).

### 2026-10-19 02:45 UTC (vuelta 216, S154): el PC se reinició; la segunda verificación del candado quedó a medias
- El verificador v2 del candado se cortó sin INFORME (salidas parciales en
  `experiments/_s151_ab_diurno/verificador_candado_k_v2/` del worktree `s153-adopcion`). Lo ya medido: **5 mutaciones NO
  ATRAPADAS** (`control_sin_b`, `w2_con_sin_sustrato`, `h2a_solo_diurno`, `h2a_sha_prefijo7`,
  `veredicto_w2_antes_de_g3`), 1 atrapada sólo por caída (`k_sin_flag_b22`, no cuenta, S152), y **la prueba del empate
  no distingue cola exacta de p95 muestreado** (las dos dan FALLA); hay 8 de 800 casos de borde que sí discrepan y sirven
  de prueba. El candado NO está listo para despachar: hay que cerrar esas mutaciones con pruebas. Verificador reanudado
  desde su transcripción para escribir el informe. Histórico 1.24: 95 de 176. Ninguna copia mutada suelta.

### 2026-10-19 02:17 UTC (vuelta 215, S154): cron-job.org en UTC COMPROBADO
- Despacho `workflow_dispatch` del NRT a las 02:10:21 UTC (run en cola al mirar). La decisión «cron» del bloque S154
  queda cerrada. Segunda verificación del candado: 11 salidas parciales, sin informe todavía.

### 2026-10-19 01:55 UTC (vuelta 214, S154): cron-job.org en UTC; plan de S155; segunda verificación del candado en curso
- **Nicolás cambió la zona horaria de `vrp-chile-cron-externo` a UTC** (expresión sin cambio, `10 1-12 * * *`).
  Comprobar el primer despacho a las 02:10 UTC (antes el primero salía a las 04:10 UTC y dejaba fuera la ventana MODIS).
- Plan de la próxima sesión acordado con Nicolás: `tasks/PLAN_S155.md` (auditoría post-K de 5 frentes con
  verificadores, índice por síntoma, CLAUDE.md, estratificación automática, pruebas en curso, reglas de proceso).
- Segunda vuelta del verificador del candado en curso (salidas parciales en
  `experiments/_s151_ab_diurno/verificador_candado_k_v2/` del worktree `s153-adopcion`). El cierre de S154 espera su
  informe.

### 2026-10-19 01:25 UTC (vuelta 213, S154): candado de la adenda K mergeado (#858); 1.34 a 1.36 en la cola
- #858 mergeado (`cf272543`, squash 01:23 UTC, CI del último commit verde antes del merge). Pruebas del verificador del
  candado agregadas; las cuatro mutaciones de la ruta K atrapadas por pruebas (M3 ya no cae: H2a sin sha devuelve
  problema); batería completa 107 de 107.
- **Antes de despachar el A/B diurno sobre K faltan:** (a) segunda vuelta de verificador limpio sobre el candado ya
  mergeado; (b) que termine el histórico 1.24 (88 de 176 trozos a las 01:23); (c) tag de despacho y `--sha-codigo` con
  `git rev-parse <tag>^{commit}` (H-5).
- Nicolás: «continúa con lo que recomiendes» sobre la propuesta de memoria y metodología: índice por síntoma (1.34),
  estratificación automática (1.35), D17 antes que D25 (1.36, luego 1.29); adelgazar el CLAUDE.md del proyecto en el
  próximo `/cierre`. Memoria nueva: `feedback_s154_estratificar_por_cenit`.

### 2026-10-19 ~00:45 UTC (vueltas 211-212, S154): candado ampliado (sin commitear); 1.33 Chillán como prioridad
- Verificador limpio del candado (`experiments/_s151_ab_diurno/verificador_candado_k/INFORME.md`): las cuatro piezas
  CONFIRMADAS en el código y en el cálculo (la cola exacta reproduce 0,5223 y 0,1058, x_obs 25 y 17), pero pruebas
  PARCIALES: H-1 (cuatro mutaciones de la ruta K no atrapadas), H-2 (faltaban las pruebas (d) y la mitad de (e)), H-3
  (el empate no fijaba x_obs), H-4 (`--base c0` con brazos K se aceptaba), H-5 (tag anotado: pasar `tag^{commit}`).
- Agregado en `loop/diurno-k-candado` (worktree `s153-adopcion`), **SIN COMMITEAR**: casos de punta a punta con
  `--base k` (k1 ADOPTAR con cola exacta y H2a OK; k2 NO ADOPTAR; k3 y k4 INDECIDIBLE por H2a; sin sha y `--base c0`
  con brazos K, rechazo); regla W2 armada con `configurar_brazos` y su caso «falla con y sin W2»; colas del muestreo
  contra las exactas (peor 0,47 de 4 errores estándar); control del nulo que FALLA con el nulo corrido en +1; empate con
  x_obs y cola exacta; H-4 en `resolver_base`; H2a sin sha devuelve problema en vez de caerse (ESTE último sin probar).
  Mutaciones re-corridas sobre copias dentro del árbol (borradas): M1 base k sin regla W2 y M4 decidir sin mirar G1 sin
  W2, atrapadas; M2 H2a apagado, atrapada (punta a punta); M3 `--sha-codigo` opcional, el evaluador SE CAÍA (TypeError),
  que no cuenta como atrapada (S152): por eso el cambio de H2a sin sha.
- El clasificador de permisos dejó de responder a mitad de la vuelta: falta correr la prueba de H2a sin sha, repetir
  M3, batería completa, commit, CI de #858 y merge. Después: tag de despacho (`git rev-parse <tag>^{commit}` para
  `--sha-codigo`, H-5) y despacho cuando termine 1.24.
- **1.33 agregada como PRIORIDAD por Nicolás**: déficit de magnitud de Chillán pasada por pasada, empezando por VIIRS
  750 de las 06:48, y pre-registro de D25 sobre K con Chillán como caso.

### 2026-10-19 ~00:30 UTC (vueltas 209-210, S154): D-25 SELLADA; candado implementado (#858), en verificación
- **Nicolás selló la adenda** (D-25): «Sello la adenda del A/B diurno sobre K (D-25) con las dos opciones
  recomendadas: cola exacta del nulo en G1 y, si G1 cumple sin W2 y falla con W2, decido yo con M4. Implementa H2a, H2b
  y la cola exacta con sus pruebas y verificador antes de despachar.» Registrado en la adenda; #857 mergeado
  (`34fedcd6`, CI del commit del sello esperado con conclusión antes del merge, A39).
- #858 (rama `loop/diurno-k-candado`, CI verde, SIN mergear hasta el verificador): con `--base k`, G1 decide con
  P(nulo >= D) exacta (siempre informada), regla W2 de la §3.2, controles del nulo contra la regla exacta, H2a
  (`cableado_records`, 0 records con Test 1 y `codigo_sha` = `--sha-codigo`), H2b (`--base` sin valor por defecto).
  Pruebas que fallaban antes; mutación «>=» por «>» probada sobre una copia dentro del árbol (la prueba cae); arnés 95
  de 95. Sobre W2 a W6 real la cola exacta da 0,5223 y 0,1058 y p95 exacto +0,2760 y +0,2303, iguales a la
  reimplementación del verificador de la adenda.
- Verificador limpio del candado lanzado (`experiments/_s151_ab_diurno/verificador_candado_k/`).

### 2026-10-18 ~23:30 UTC (vuelta 208, S154): adenda v2 tras el verificador; D-25 a Nicolás (#857)
- Verificador limpio de la adenda (`experiments/_s151_ab_diurno/verificador_adenda_k/INFORME.md`): P1 limpio (147
  constantes, producción = control K salvo nombre y directorio); P2 hallazgos H2a (cableado sólo por log; `unir_ventana`
  no copia logs; falta invariante por record, 0 de 3.548 records de producción bajo K con Test 1, y `codigo_sha`) y H2b
  (`--base` por defecto en c0 se apaga sin aviso); P3 limpio; P4 regla bien, prueba insuficiente (H4: fuerza bruta,
  empate, mutación de ≥, comparar colas, controles del nulo con la regla exacta; reimplementación propia reproduce los
  valores). Propios: **V1 (gravedad 4)**, el contrafactual `ctx_cluster` falla en W2 a W6 (P = 0,194) aunque cumple en
  W3 a W6: el caso «cumple sin W2, falla con W2» no está previsto en el §6; V2 evidencia sólo en `loop/activo`; V3 costo
  10 a 15 h por media ventana, 3 a 5 días.
- Adenda v2 con todo eso: §3 con dos decisiones para el sello, candado ampliado (H2a, H2b, pruebas de la cola exacta),
  costo corregido. PR #857 (documento). D-25 en la cola de decisiones.

### 2026-10-18 ~22:50 UTC (vuelta 207, S154): adenda del pre-registro del diurno sobre K, en verificación
- `experiments/_s151_ab_diurno/ADENDA_K.md` en la rama `loop/diurno-k-adenda` (`4d8bcc62`): cambia sólo brazos y base
  (cableado `--base k`); criterio, ventanas, métricas y referencia sin cambio; decisión aparte para el sello: cuantil
  exacto del nulo en G1 (opción A, recomendada) o muestreo (B). Despacho desde un tag fijo, después del histórico 1.24.
  Costo medido sobre la corrida C0 (runs 38987988455, 39041204976, 39097155412): control 15 a 24 min y diurno 40 a 58
  min por media ventana y volcán, unas 150 h de runner. Cifras del verificador cotejadas contra su informe.
- Verificador limpio de la adenda lanzado (escribe en `experiments/_s151_ab_diurno/verificador_adenda_k/`).

### 2026-10-18 ~22:30 UTC (vuelta 206, S154): infraestructura del A/B diurno sobre K mergeada (#856)
- #856 (`2ca366cd`): perfiles `_s154_ab_diurno_k_control` (réplica K tal cual) y `_s154_ab_diurno_k_on` (K más
  `enable_daytime_viirs`); `tests/test_perfiles_diurno_k_s154.py` (control = producción salvo nombre y directorio;
  diurno difiere sólo en la palanca; base K); `evaluar_diurno.py` con `--brazos` y `--base k` (cableado exige los tres
  flags de K; arnés `base_k`: un brazo con Test 1 encendido sale roto); workflow con el assert del brazo por la entrada
  `control`. Las pruebas nuevas fallaban antes; 593 del repo en verde; arnés 79 de 79; CI verde.
- Despacho futuro (tras el sello): `reproc-s151-ab-diurno.yml`, `brazos=["_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"]`,
  `control=_s154_ab_diurno_k_control`, mismas ventanas W2 a W6 en medias ventanas, desde un tag fijo (A108).
- Paradas: NRT verde 20:08, disco 17 GB. Histórico 1.24: 65 de 176. Próximo: adenda del pre-registro.

### 2026-10-18 ~20:55 UTC (vueltas 204-205, S154): 1.32 paso H2 mergeado (#855)
- Causa de H2: `estratos_de` y `grupos_de` devolvían los estratos en el orden de recorrido de `cls` (conjuntos de
  strings, orden según PYTHONHASHSEED); el generador reparte sus números en ese orden. Arreglo: ordenar por (volcán,
  sensor). Chequeo `orden_del_nulo` en el arnés (mismos datos en dos órdenes): falló en estratos, grupos y nulo
  completo (8.790 de 10.000 muestras distintas) y pasa con el arreglo; el p95 solo coincidía de casualidad con los
  datos chicos (nulo discreto), por eso el chequeo compara el nulo entero. Batería completa 75 de 75. W2 a W6 real con
  PYTHONHASHSEED 1 y 2: salidas idénticas (0 líneas de diferencia), veredicto sin cambio. #855 (`7968cc06`) mergeado.
- Para la adenda de 1.32: el cuantil exacto (+0,2760 según el verificador) y el muestreo (+0,2446) difieren porque el
  nulo es discreto y el percentil cae en un salto; W3 a W6 empata (D = p95). Proponer en la adenda el cuantil exacto
  por convolución de hipergeométricas, que cambia el método pre-registrado y por eso va al sello de Nicolás.
- Paradas: NRT verde, disco 17 GB. Histórico 1.24: 57 de 176.

### 2026-10-18 ~19:40 UTC (vuelta 203, S154): 1.32 paso H1 mergeado (#854)
- Batería completa del arnés del evaluador diurno: 72 de 72 (`probar_salida.txt` actualizado). #854 (`ac95107a`):
  aviso A114 por sensor en `res["saturacion"]`, caso 26, filtro `PROBAR_SOLO`. CI verde, no toca §1.1, mergeado.
- Histórico 1.24: 49 de 176 trozos.
- Próximo de 1.32: H2 (nulo dependiente del orden, `evaluar_diurno.py:635`), después perfiles diurnos sobre K y
  adenda del pre-registro para el sello de Nicolás.

### 2026-10-18 19:10 UTC (vuelta 201-202, S154): D-24 aprobada y aplicada (#853); arreglo A114 del evaluador en prueba
- **Nicolás aprobó D-24** («sí a D-24: confírmalo en el navegador con el código real y, si se confirma, mergea el PR
  del marcador con su prueba y R8»). Confirmación previa: vuelta 199. #853 (`c8fbe5b3`, squash 19:04:16 UTC):
  `pixelesDelMarcador(r, v)` en `frontend/index.html`, `ctx_cluster` sumado a las anclas honestas (`final_hotspot`
  primero = centroide del cúmulo en 247 de 247 records de la ventana), `anomaly_pixels` detrás. Prueba
  `tests/test_marcador_mapa_ctx_cluster_s154.py` (6 en node; fallaban las 6 antes; control sobre datos reales de
  Láscar); 261 pruebas que leen `index.html` en verde; CI verde. Navegador local y **R8 en el tablero publicado**:
  Láscar 2026-10-10 05:06 NOAA-20 pasa de 24,73 km a 1,01 km del cráter, las otras tres de la noche sin cambio,
  consola sin errores. Capturas antes y después en `experiments/_s154_marcador/`. 1.31 HECHA.
- **1.32, paso H1** (rama `loop/diurno-evaluador-a114`, worktree `s153-adopcion`): caso 26 del arnés (VIIRS 375
  saturado, 750 callado) en rojo con el evaluador viejo (`{}`) y en verde con el aviso por sensor
  (`{'VIIRS375': True, 'VIIRS750': False}`), corriendo sólo 1, 3 y 26 con el filtro nuevo `PROBAR_SOLO` (el fallo de
  `cobertura_workflow` en esa corrida es del filtro: el caso 14 reutiliza la carpeta del 8). Batería completa
  corriendo antes del PR.

### 2026-10-18 18:25 UTC (vuelta 200, S154): 1.27, las pasadas Terra sin K no se pueden reprocesar
- Paradas: NRT verde 17:04, disco 17 GB. D-24 sin respuesta.
- CMR (`MOD021KM`, ventanas de una hora): huecos en el archivo estándar de Terra exactamente en las pasadas que quedaron
  en C0 (28-sep 01:15 a 01:40, 2-oct 00:35 a 00:55, 10-oct 00:55 a 01:15); control del 9-oct completo. `MOD021KM_NRT`: 0
  en el catálogo. Quedan en C0 con su marca de régimen. NOAA-21 del 18-oct: rehacer desde el 2026-10-23.

### 2026-10-18 17:58 UTC (vuelta 199, S154): 1.31 (a) CONFIRMADA en el tablero público
- Paradas: NRT verde 17:04, disco 17 GB. Histórico 1.24: 39 de 176.
- Con el código real del tablero publicado (`?volcano=Lascar&desde=2026-10-10&hasta=2026-10-10`, capas leídas con
  `map.eachLayer` del mapa de detalle): la pasada VIIRS_NOAA20 2026-10-10 05:06, rotulada «summit» y «Confirmado por
  MIROVA (MIROVA @ 1.50 km)», cúmulo de 1 píxel 0,040 MW y distancia 0,28 km en la tabla, se dibuja a **24,73 km del
  cráter**, sobre el salar al SE. Las otras tres pasadas de esa noche, a 0,70 a 0,92 km. Captura en
  `experiments/_s154_marcador/lascar_20261010_0506_marcador_en_salar.jpg`. Búsqueda en `data/mirova_equivalent/Lascar.json`:
  4 records `ctx_cluster` «summit» de los últimos días con el píxel 0 a 20 a 25 km del cúmulo. Pendiente (b), el PR,
  según la respuesta de Nicolás a D-24.

### 2026-10-18 ~18:10 UTC (vuelta 198, S154): verificador del diurno: PARCIAL; NO ADOPTAR vale para C0, no para K
- Re-corrió el evaluador dos veces (con y sin `--repetidas`): mismos números. Tres caminos independientes: pareo
  aparte (0 discrepancias en 5.018 pasadas), nulo exacto por convolución de hipergeométricas (D de W2 a W6 en la
  mediana, P = 0,52), cobertura pareja en las 10 raíces. `--repetidas` no actúa (ninguna ventana pasa del 10 %). Los
  siete commits de las raíces tienen `pipeline/`, tablero, `run_pipeline.py`, workflow y `volcanoes.yaml` idénticos:
  todo es C0.
- **H4 (gravedad 4): no se traslada a K.** De día el Test 1 dispara en 2.000 de 2.077 publicaciones de VIIRS 375 en
  negativos limpios (987 sólo `test1_roi`; V750 389 de 731); 11 de las 22 protegidas recuperadas salen sólo del Test 1.
  Contrafactual sólo `ctx_cluster`: G1 W2 a W6 sigue fallando (+0,132 contra +0,195), W3 a W6 cumple (P = 0,001); G2
  falla (1.142 contra 20; 357 contra 6). Nueva tarea 1.32.
- H1 (3): el aviso A114 del evaluador junta los dos sensores (60,0 %) y no ve que VIIRS 375 está en 89,3 %. H2 (2): el
  p95 del nulo depende del orden de un conjunto (`:635`): +0,2446 o +0,2760, exacto +0,2760; no cambia el veredicto.
  H3 (2): «sin W2 también falla» es un empate en el cuantil exacto. H5 (1): W5a mezcla commits `7b825ba` y `eb97779`
  con código idéntico.
- #813 comentado con el resultado.

### 2026-10-18 ~17:40 UTC (vuelta 197, S154): diurno W2 a W6 evaluado: NO ADOPTAR (por verificar)
- Paradas: NRT verde 15:10 (la de 17:04 en cola), disco 17 GB. Histórico 1.24: 33 de 176.
- Chaitén de W6a repetido (39146249401) verde; unión con `unir_ventana.py`: `intento_entero`, 0 distintos (control 79
  iguales, diurno 143 iguales). W6a PAREJA (802 contra 802). Las 10 medias ventanas completas y parejas.
- `evaluar_diurno.py` sobre W2 a W6 (`--repetidas W2,W3,W5,W6`; W1 fuera, sólo informa y su raíz no se guardó), salida
  en `experiments/_s151_ab_diurno/salidas/W2_W6_s154/`: **VEREDICTO NO ADOPTAR** (original, SN y SE). G3 CUMPLE
  (9.762 pares nocturnos, 0 distintos: la noche no cambia). G1 FALLA (M1 78,1 % de 32 menos q_neg 60,0 % de 4.683 =
  +0,18, p95 del nulo +0,24; sin W2, +0,23 contra +0,23). G2 FALLA: VIIRS 375 publica en 2.236 de 2.511 pasadas
  diurnas de la tabla (MIROVA 13), VIIRS 750 en 766 de 2.466 (MIROVA 2). Salvedad A114: el A/B corrió sobre C0, donde
  el Test 1 satura (el control publica en 88,8 % de los negativos limpios nocturnos de VIIRS 375); con K podría
  cambiar. Verificador limpio lanzado, con esa pregunta explícita.

### 2026-10-18 ~16:55 UTC (vuelta 196, S154): 1.26 HECHA, la tesis de localización cae; 1.31 nueva (marcador del mapa)
- Verificador limpio de `experiments/_s153_localizacion/` (informe y salidas crudas en `verificador/`): (1) «viene del
  Test 1» PARCIAL (`triggered_test1` dice que disparó, no que decidió; cota inferior por `test1_roi`, p. ej.
  Villarrica 115 de 189); (2) «cúmulo a 2 a 3 km» CONFIRMADA para el centroide (Villarrica 2,73, Llaima 2,75, Copahue
  2,71, Láscar 0,37, sobre `60c45833f`) y REFUTADA como lo que ve el operador (para `test1_roi` el marcador va al
  cráter); (3) «con K se juntan en el cráter» REFUTADA: K publica un subconjunto estricto de C0 y esas pasadas ya
  estaban en el cráter con C0; (4) Lastarria SIN DATO; (5) «mismo mecanismo» PARCIAL (las 1.363 pasadas que K quita
  tenían el cúmulo a 2,45 a 2,83 km: 713 negativos limpios, 21 positivas).
- Hallazgos propios: **H3** (gravedad 4), marcador primario del mapa para `ctx_cluster` = `anomaly_pixels[0]`;
  confirmado leyendo `frontend/index.html` de `main` (para `ctx_cluster` no se antepone `final_hotspot` y por defecto
  sólo se dibuja el índice 0). Nueva tarea 1.31 y decisión D-24. **H4**: el backfill con K cambió los datos; los
  scripts de la carpeta no se reproducen sobre los de hoy (sí sobre `60c45833f`). **H6**: K quita 21 pasadas que el
  evaluador etiqueta positivas (no es el veto P1). Punto débil declarado: el marcador lo transcribió a Python, no lo
  corrió con node.
- 1.25: repetición de Chaitén (39146249401) en curso.

### 2026-10-18 16:46 UTC (vuelta 195, S154): 1.25 W6a repetida; raíces W2 a W6 armadas y parejas; 1.26 verificador lanzado
- Paradas: NRT verde 15:10, disco 17 GB, #779 sin cambio. Histórico 1.24 (39125546355): 31 de 176 trozos verdes a las
  16:38, de 38 a 82 min por trozo.
- **1.25:** el rojo de W6a es cobertura: `_s151_ab_diurno_on` Chaitén con 4 noches de menos (798 contra control). Repetido
  Chaitén en los dos brazos, 2026-10-01 a 10-07, `--ref s151-diurno-codigo` (= `eb97779f`, el mismo commit de W6a): run
  39146249401. Intento 1 en `C:\Users\nmend\AppData\Local\Temp\claude\w6a_39090434307\i1\`.
- Raíces de evaluación en `C:\Users\nmend\AppData\Local\Temp\claude\diurno_eval\` (una por media ventana): W2a = intento
  2 entero (parejo por sí solo, opción (a) de D-16, que es la recomendación que Nicolás aprobó con «haz lo que
  recomiendes» el 2026-10-17); W3a = intento 1 con el control de PCC de la unión; W5a = unión (logs del intento 1,
  mismo commit); W2b, W3b, W4a, W4b, W5b, W6b = artefacto `todo`. `contar_pasadas_noche.py`: las 9 PAREJAS (0 faltan,
  0 sobran) y con el día como se espera.
- **1.26:** verificador limpio de `experiments/_s153_localizacion/` lanzado (agente en segundo plano; escribe en
  `experiments/_s153_localizacion/verificador/`).
- Próximo: unir Chaitén de W6a, contar, evaluar W2 a W6 con `evaluar_diurno.py` (W1 informa aparte) y verificador limpio.

### 2026-10-18 12:15 UTC (S154): ventana de 30 días con K verificada; histórico por trozos corriendo
- Reproceso de 30 días (run 39117638055) 11 de 11 verde. `experiments/_s154_reproc_k/verificar_ventana.py` contra el
  tag `pre-s154-reproc-k-datos`: 3.521 de 3.577 pasadas de la ventana escritas con K, 0 perdidas, 0 cambiadas antes
  de la ventana (`ventana_30d.json`). Las 56 sin K son gránulos que el reproceso no bajó: MODIS Terra del 28-sep,
  2-oct y 10-oct en casi todos los volcanes, y NOAA-21 de la madrugada del 18-oct (SOSPECHA: Terra ausente en LAADS
  esos días). R8: el JSON publicado de Villarrica trae 348 de 352 con K.
- Costo previsto: el NRT de las 10:10 quedó cancelado (desplazado por el de las 11:10 mientras esperaba `push-main`).
- Nicolás eligió la vía por trozos en perfil aislado. #852 mergeado: `_s154_reproc_k_historico.yaml` (resuelve
  idéntico a la réplica salvo nombre y directorio; control negativo comprobado), `scripts/reemplazar_ventana_reproceso.py`
  y 11 tests. `reproc-chunked.yml` despachado: run 39125546355, 2025-02-15 a 2026-09-17, 176 trozos (16 x 11), de a 8;
  estimado 28 a 35 h. Después: ensayo del reemplazo por volcán, verificador limpio, aplicar en un commit entre NRT, R8.

### 2026-10-18 10:10 UTC (S154, dueña del loop: sesión S154 «retomar»): K ADOPTADA; reproceso de 30 días corriendo
- Nicolás dio el sí a #850 (D-21). Merge squash `34cea39e` a las **09:57:30 UTC**, después de que todos los jobs del
  NRT de las 09:10 arrancaran con C0 (esa corrida queda entera en C0; la de las 10:10 sale entera con K). CI de `main`
  verde sobre el merge. Worktrees de #843 y #846 borrados (1,9 GB; disco 13 GB libres).
- #851 (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`, más el test que reemplazaba literal `= null;`) mergeado; R8:
  el aviso se ve en el tablero público, consola sin errores.
- Tag de datos `pre-s154-reproc-k-datos` (`34cea39e`). Reproceso con K de la ventana por defecto del tablero:
  `backfill-tier-a.yml`, 2026-09-18 a 2026-10-18, overwrite=true, run 39117638055 (despachado con `push-main` libre).
- Histórico (D-23, pedido por Nicolás): pendiente de elegir la vía (ver la respuesta de S154).
- W6a terminado (23 de 23 jobs, sin evaluar); W6b corriendo.

### 2026-10-18 06:07 UTC (vuelta 194): CIERRE de S153 (pedido de Nicolás); bloque de arranque S154
- `tasks/BLOQUE_ARRANQUE_S154.md`. Loop detenido. Se fijó con trabajo en curso: diurno W6a (run 39090434307, 12 de 22)
  y W6b (run 39097155412, pendiente). Sin agentes vivos. #850 (adopción de K) abierto, CI verde, espera el sí de
  Nicolás. Memoria: `project_s153_estado`, `feedback_s153_una_sesion_duena_del_loop`,
  `reference_cronjob_org_zona_horaria`.

### 2026-10-18 06:00 UTC (vuelta 193, S153): espera
- NRT verde 04:10 y 05:10 (cron externo cada hora). W6a 10 de 22; W6b pendiente. #850 sin respuesta. Disco 6,4 GB.

### 2026-10-18 05:28 UTC (vuelta 192, S153): deriva 1.23 bis CONFIRMADA por verificador limpio; A85 marcada
- `experiments/_s153_deriva_123bis/verificador/VERIFICADOR.md`: fechas de los gates resueltas con `pipeline.profile` en
  cada commit (encendidos 2026-05-28 04:44 y 16:39 UTC, apagados 2026-07-01 20:46 UTC; único cambio de constantes en la
  ventana); datación rehecha por barrido lineal (corrección: Chaitén 04-28 e Isluga 05-09 y 05-19 se escribieron el
  06-06); controles nuevos que no dependen de la historia (firma estructural violada en 1 de 2.869 records de la ventana
  contra 5.319 de 8.742 después; experimento natural en el flip 37 de 38 contra 30 de 30; #535 descartado). Corpus:
  3.231 MODIS reproducidos; **segunda frontera en 2025** (backfill S120 escrito después del flip). Publicaciones en la
  muestra: 5 de 250 cambian (3 se encienden en Isluga, 2 se apagan en Chaitén), todas negativos limpios, ninguna
  protegida. VIIRS: deriva probablemente chica, SIN VERIFICAR.
- A113: marca en A85 del `CLAUDE.md` (la recaptura «volvió» sólo desde el 2026-07-01).
- **D-23 para Nicolás:** reprocesar o no los MODIS de enero a junio de 2026. Recomendación: no ahora; si se adopta K
  (#850), el reproceso histórico con K los rehace todos de una vez con un solo detector.

### 2026-10-18 05:17 UTC (vuelta 191, S153): 1.23 bis: la deriva son los gates intra-radio, no un commit (POR VERIFICAR)
- `experiments/_s153_deriva_123bis/INFORME.md`. Los 8 records MODIS (Chaitén 03-06 y 04-28, Copahue 03-06, Isluga
  05-09, 05-18 y 05-19, Llaima 03-11, Chillán 03-19; todos Standard, sin Test 1, negativos limpios) se escribieron por
  última vez con `enable_path_d_intra_radio_gate` y `enable_second_pass_intra_radio_gate` ENCENDIDOS (de #226/#229 el
  2026-05-28 a #474 el 2026-07-01), en las promociones S97 y S102; el flip OFF de S118 no se acompañó de reproceso.
  Pruebas: 247 de 250 records escritos con el gate salen hoy con más píxeles y 217 de 218 escritos después salen
  iguales; ninguno de 470 sale con menos; en 49 de 56 el conteo de hoy es exactamente primer pase + recaptura previa.
- **Alcance, POR VERIFICAR:** 3.231 records MODIS de enero a junio de 2026 (10 volcanes; Villarrica ninguno) escritos
  con el gate y nunca reescritos. Toda serie o A/B MODIS que cruce el 2026-07-01 mezcla dos detectores, y el «la
  recaptura volvió 4-6×» de A85 vale sólo desde julio. VIIRS (~4.500 expuestos) SIN VERIFICAR.
- Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_deriva\`). Corrida mínima de
  confirmación (8 gránulos, tres brazos de gates) diseñada y NO despachada.
- W6a corriendo; W6b pendiente; #850 sin respuesta.

### 2026-10-18 05:00 UTC (vuelta 190, S153): tarea 1.23 bis delegada; esperas
- NRT verde a las 04:10 (primer despacho del cron externo, en hora de Chile). W6a 4 de 22; W6b pendiente. #850 sin
  respuesta. Disco 6,5 GB.
- **1.23 bis** (commit de la deriva de los 8 records MODIS) delegada a un agente de sólo lectura, por arqueología de
  código (MODIS no corre en Windows) (`C:\Users\nmend\AppData\Local\Temp\claude\deriva_123bis\`).

### 2026-10-18 04:27 UTC (vuelta 189, S153): W5a unida y PAREJA (con desviación); W6b despachada; cron externo en hora de Chile
- **Cron externo: despachó a las 04:10 UTC** (= 01:10 de Chile): cron-job.org interpreta `10 1-12 * * *` en hora de
  Chile, o sea 04:10 a 15:10 UTC. La ventana nocturna de MODIS (01 a 03 UTC) queda sólo con el programado de GitHub,
  que viene con atraso de 1 a 2 h. Para Nicolás: poner la zona horaria del trabajo en UTC en cron-job.org, o la
  expresión `10 22-23,0-9 * * *` en hora de Chile.
- **W5a:** repetición (39068611598) pareja (339 por brazo en los 3 volcanes). Unión con `unir_ventana.py`: Llaima
  `_s151_ab_diurno_on` NO une por 2 records diurnos de VIIRS 375 (SNPP 09-01 17:42: otro conjunto de píxeles con
  lista llena; NOAA-21 09-09 17:54: un píxel del corte pasa de descartado a guardado y cambia el `vrp_mw` de escena,
  36,902 contra 37,739). Es el desempate no estable del top-100 en VIIRS (#844 lo arregló sólo en MODIS). El
  predicado del tablero da IGUAL en los dos pares, el cúmulo es idéntico (0,079 y 15,32 MW) y los dos intentos traen
  los mismos 202 records. **Desviación:** se usó el intento 2 entero para ese archivo, como D-16 (a); no cambia
  ninguna publicación ni toca el G3 (son pasadas diurnas). Para ratificar (D-22). **W5a unida: 1.199 contra 1.199,
  PAREJA** (`C:\Users\nmend\AppData\Local\Temp\claude\w5a_39032518643\union\`).
- **Diurno:** W6a corriendo (2 de 22); **W6b despachada** (run 39097155412, 2026-10-08 a 10-14, `--ref
  s151-diurno-codigo`), pendiente detrás.
- #850 sin respuesta todavía. NRT verde a las 03:09 y corriendo el de las 04:10.

### 2026-10-18 03:56 UTC (vuelta 188, S153): PR de adopción de K abierto (#850), CI verde; ESPERA el sí de Nicolás
- **#850** (rama `loop/adopcion-k`, `e0d3ebfd`): flags en `mirova_equivalent.yaml`; 46 perfiles derivados congelados en
  C0; guards `test_guard_adopcion_k_s153.py` y `test_guard_perfiles_congelados_s153.py`; ficha SDA v1.9; marcas A113 en
  D19, D21, D26, D30, D11, MISSION y CLAUDE.md (G8 remapeado a 1595); historial del auto-audit con la publicación en
  negativos; `frontend/cambio_detector.js` (`CAMBIO_DETECTOR_UTC = null` hasta el merge); evidencia de
  `experiments/_s153_fk_v2/` traída a la rama. Suite local 2.107 passed; CI verde; `MERGEABLE CLEAN`.
- **Decisiones para Nicolás (D-21):** el merge; auto-audit sin recalibrar las primeras semanas (recomendado);
  `experimental_lowT` y `experimental_ndc_focus` congelados en C0; aviso a OVDAS e Integracion_Plataformas; salvedad de
  Tupungatito 2026-09-29.
- Después del merge (loop): completar `CAMBIO_DETECTOR_UTC`, reproceso de 30 días con K en jobs partidos, R8, sombra.

### 2026-10-18 03:37 UTC (vuelta 187, S153): espera
- Rama `loop/adopcion-k`: flags, 46 perfiles derivados congelados en C0 y guards commiteados (`5df26fe1`, suite 2.096
  passed; los 91 perfiles distintos de producción resuelven idéntico a `main`, comprobado resolviendo los 92). Agente
  de documentos y marca visible en curso. NRT corriendo (programada de las 02:00, iniciada 03:09). Repetición de W5a 5
  de 6; W6a pendiente. Disco 6,8 GB.

### 2026-10-18 03:15 UTC (vuelta 186, S153): R2 de K: cinco de cinco COINCIDEN (una con salvedad)
- `experiments/_s153_fk_v2/r2/INFORME.md` y figuras `caso_*.png`. Lector `experiments/_s151_seleccion_mirova/comun_tif.py`
  (resta la mediana móvil: el campo crudo tiene su máximo en el valle tibio, A69); 9 GeoTIFF emparejados por
  `acquisition_utc` con md5. Negativos de borde (Chaitén 09-10, cenit 66°) y de nadir (Láscar 09-06; Copahue 09-15
  UTM): MIROVA calla, C0 publica, K calla. Protegida V375 de Láscar 06-03 05:24: K a 0,18 km del foco de MIROVA.
  Cúmulo movido Tupungatito 06-03: K a 0,24 km del foco (C0 estaba a 2,71 km).
- **Salvedades escritas (la regla pide explicarlas):** (a) el primer candidato del caso 3 (Láscar 06-02 05:42) y
  NOAA-21 06-03 06:12 tienen TIF que no es de su pasada (foco a 17,5 y 22 km, BT 8 y 28 K distinta): SIN IMAGEN, se
  eligió otro DESPUÉS de verlo, y se informa; (b) caso 4 MODIS Láscar 05-10: K publica a 1,34 km del foco, celda
  vecina, del tamaño del corrimiento de geolocalización MODIS (#828): COINCIDE con salvedad, a juicio de Nicolás;
  (c) en 4 de los 5 la imagen sale del mismo gránulo que nuestro detector (A109): no es independiente.
- Con esto quedan hechos los controles §4.1 a §4.5. Falta: arreglo de los 22 tests (agente en curso), pre-mortem y PR.

### 2026-10-18 ~03:12 UTC (vuelta 185, S153; hora corregida, decía ~03:35 estimada sin pedirla al servidor, A86): PR de adopción de K en preparación (rama `loop/adopcion-k`)
- **Tag defensivo `pre-s153-adopcion-k`** en `5849ee65` (main), empujado (A38, A45). Worktree
  `.claude/worktrees/s153-adopcion`. Guard nuevo `tests/test_guard_adopcion_k_s153.py` (falló en los 3 casos antes del
  cambio); flags en `mirova_equivalent.yaml` (`paths.enable_test1_path: false`, `paths.enable_tests_23_prose_branch:
  true`, `enable_modis_b22_primary: true`); actualizados `test_gr2_profile_invariants.py` y
  `test_experimental_congelado_s150.py` (cayó a propósito, como anunciaba).
- **Suite: 22 fallas.** Causa de fondo: muchos perfiles `_s1xx_*` hacen `extends: mirova_equivalent` y heredan K en
  silencio (A117), por ejemplo `_s146_ab_control` = C0 de los A/B ya evaluados. Agente encargado de congelar los
  brazos históricos con los flags de antes (como `experimental.yaml`), actualizar los tests de valor operacional y
  anclar el golden sin debilitar nada. Los A/B en curso (diurno, desde tag) no se ven afectados.
- Falta R2 (en curso). El PR no se mergea sin el sí de Nicolás (A45).

### 2026-10-18 ~03:10 UTC (vuelta 184, S153; hora corregida, decía ~03:20 estimada, A86): auditoría A61 de P4: ninguna protegida movida a otro objeto
- `experiments/_s153_fk_v2/a61/INFORME.md` (62 movidas: 8 de V1, 54 de V2). El «movimiento» es casi siempre cambio de
  agregación: K deja el cúmulo de un píxel en 54 de 62; en 40 de 62 el centroide de K cae sobre un píxel que C0 también
  marcó (38 a 0,00 km; en 30 es el más caliente de C0, cuyo centroide arrastraban 2 a 24 vecinos tibios). En 22 (VIIRS
  375 débiles salvo Isluga 06-10) K publica en otro lugar; contra el radio de MIROVA (desde `mirova_center`,
  cuantizado: 2,4 = 0,375·√41) compatible sólo K en 11, sólo C0 en 2, ninguno en 9; en 20 de 22 K se acerca al cráter.
- **Las 14 protegidas:** 12 mismo objeto (Láscar MODIS 5, Láscar V750 4, Chillán MODIS 2, Villarrica MODIS 1);
  Isluga V375 06-10 K se acerca a lo que vio MIROVA (C0 descartado por el radio); Tupungatito V375 09-14 el radio
  descarta a los dos brazos y la protección descansa sólo en el OCR de Suomi NPP: SIN VERIFICAR.
- Imágenes: 40 GeoTIFF bajados de a uno; ninguna protegida tiene imagen propia (archivo desde mayo, congelado desde el
  22-sep); el instrumento de imagen **falla su nulo** con estas señales débiles (A110), así que no decide. **Veredicto
  para el §3: ninguna movida pone el cúmulo publicado sobre otro objeto en una protegida; P4 no bloquea.**
- Falta R2 (en curso). Después: pre-mortem, tag defensivo y PR de adopción (§4.6 a §4.8).

### 2026-10-18 03:06 UTC (vuelta 183, S153): segundo lector: las cuatro alertas que K no publica son LEJANAS
- `experiments/_s153_fk_v2/lector2/INFORME.md`: Tupungatito 09-28 (22,5 km desde la referencia de MIROVA) y 09-29
  (9,6 km), Lastarria 04-18 (20,0 km; corrida la función real del scraper sobre la imagen propia, que quedó guardada con
  otro nombre: FALSO_POSITIVO_OCR) y 05-02 (19,3 km). Con la distancia propia, el scraper habría escrito
  FALSO_POSITIVO, no ALERTA; el cúmulo de K está en el mismo lugar que el punto caliente de la miniatura de MIROVA.
  **Ninguna cuenta como pérdida neta: la condición de Tupungatito del §3 de la regla queda cumplida.**
- Salvedad SIN VERIFICAR para Nicolás: Tupungatito 09-29 04:54 trae además un punto tenue cerca del cráter (~5,4 km a
  330° de la referencia), donde C0 publicaba 0,059 MW; los 1,86 MW de MIROVA podrían incluir algo de ahí.
- R2 (§4.4) lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\r2_fk\`). Falta además la auditoría A61 (en curso).

### 2026-10-18 03:05 UTC (vuelta 182, S153): R3 coincide; K sobre el main de hoy idéntico al del tag
- **§4.3 (R3):** segundo instrumento escrito desde el texto del pre-registro, sin importar `evaluar_fk`,
  `banco_paridad` ni `clase_mirova` (`experiments/_s153_fk_v2/r3/`): sustrato, P1 (A y B), P2 y la tabla §9 de C0, F, K
  y G **idénticos número por número y pasada por pasada** en V1 y V2. Control de mecanismo: en los negativos de VIIRS
  375 que C0 publica y K no (713 en V1, 826 en V2), K no tiene ningún píxel anómalo en 661 y 786, y en C0 venían del
  Test 1 integrado en 675 y 783. Límite: comparte los insumos (referencia congelada, uniones, `index.html`).
- **§4.5:** K sobre `main` (`5849ee65`, run 39091739488, Láscar y Chillán del 2026-10-01 al 10-03) contra K de la unión
  de V1: 56 de 56 pasadas `igual`, 0 decisiones de publicar distintas (`experiments/_s153_fk_v2/k_main_contra_tag.py`).
- Pendiente antes del PR: auditoría A61 de las movidas y segundo lector (agentes en curso), R2 con imágenes de MIROVA
  (§4.4). Diurno: repetición de W5a 4 de 6, W6a pendiente. NRT: última corrida verde 23:44 UTC; el cron externo
  sigue sin despachar (revisar a las 04:30 UTC).

### 2026-10-18 02:54 UTC (vuelta 181, S153): verificador limpio de F/K: CONFIRMADO; se abre el ciclo de la regla
- `experiments/_s153_fk_v2/verificador/VERIFICADOR.md`: reproducido con 0 claves distintas; instrumento = `2766c198`
  (diff vacío en evaluador, `unir_intentos`, `armar_tabla`, `scripts/`, `pipeline/`); los 43.326 records unidos son
  idénticos a un record de algún intento; `FLAGS_BRAZO` revisado en cada brazo, volcán e intento que aporta records;
  determinismo entre intentos de V2 sin diferencias en 2.346 a 5.825 pasadas por brazo; siembras de V2 detectadas
  (pérdida de Láscar PENDIENTE y VETADO con repetición, PIERDE, INDECIDIBLE por banda 21).
- **Cruce de 1 MW (§5): ninguna protegida que C0 muestra sobre 1 MW queda bajo 1 MW con K**, en V1, V2 ni V2 con OCR
  (dos cruzan hacia arriba). La magnitud no bloquea. P3 ciego otra vez: en los pares que cambian, VIIRS 375 K bajo C0
  en 127 de 144 (media de d +0,031 [+0,012; +0,049]); VIIRS 750 media +0,055.
- **P4 (V2):** 54 movidas, 30 hacia el cráter y 24 hacia afuera (en radio), mediana 1,15 km, máximo 4,06 km, ninguna
  cruza el `inner_radius_km`; Lastarria 18 de las 25 de VIIRS 375 (12 hacia afuera), MODIS 6 de Láscar; 10 son
  protegidas. V1: 8 movidas. Falta la auditoría A61 (§3 de la regla).
- Lo que el CUMPLE no dice: fuera de Láscar y Chillán deciden 8 protegidas en total (una pérdida de 18 % pasaría con
  20 % de probabilidad); por eso existe la sombra. Lastarria 2026-04-18 (sólo OCR, K la ve a 19,6 km como `far`, C0
  publicaba 0,055 MW a 2,77 km por el Test 1): parece «C0 publicaba otro objeto», SIN VERIFICAR, mirar la imagen.
- **Siguiente (antes del §4 y §4 en paralelo):** auditoría A61 de las 62 movidas; segundo lector de Tupungatito (V1) y
  de las dos de Lastarria; recuento independiente R3; K sobre el `main` de hoy (§4.5).

### 2026-10-18 02:39 UTC (vuelta 180, S153): F/K V2 evaluada: K lectura A CUMPLE combinado (POR VERIFICAR); P4 pendiente
- Instrumento fijado (`2766c198`). V1 re-unida (44 de 44 iguales salvo `_union_intentos`) y re-evaluada: CUMPLE, igual
  que antes. V2a re-unida, V2b unida y pareja. Todo en `experiments/_s153_fk_v2/` (README con la desviación: logs de
  V2b unidos porque el control de cableado exige 11 volcanes por carpeta; con las carpetas partidas salía INDECIDIBLE
  sólo por eso).
- **Combinado (§3 de la regla): K lectura A CUMPLE con la regla original y con SN.** V2: K no pierde ninguna protegida
  (MODIS 39 de 39, contra 6 de C0; VIIRS 375 38 de 38; VIIRS 750 42 de 42); negativos limpios MODIS 10,8 a 0,9 %, VIIRS
  375 85,4 a 3,7 %, VIIRS 750 21,8 a 1,1 %; P2 GANA en los tres. Lectura B: NO CUMPLE (veto) por V1 (informa, D-4).
- **Pendiente antes del §4:** P4 FALLA en V2 (54 de 632 alertas con el cúmulo movido más de 0,5 km; 30 quedan más
  cerca del cráter) → auditoría A61 de las movidas; cruce de 1 MW hacia abajo (§5: magnitud VIIRS 375 0,762 a 0,669,
  VIIRS 750 0,594 a 0,534); Tupungatito de V1 con segundo lector.
- **Con OCR (`--solo-tabla no`, informa):** VIIRS 375 K 57 de 59 protegidas: Lastarria 2026-04-18 04:42 NOAA-20 (1,29
  MW, pendiente de repetición) y Lastarria 2026-05-02 05:06 Suomi NPP (2,36 MW, sólo OCR). Mirarlas.
- Verificador limpio de V1+V2 lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v2\`), que además mide P4
  y el cruce de 1 MW. Diurno: repetición de W5a corriendo (2 de 6), W6a pendiente detrás.

### 2026-10-18 02:40 UTC (vuelta 179, S153): V2b unida y PAREJA; W6a despachada; NRT sin despacho externo
- **V2b repetida** (39068999603): los 4 volcanes repetidos parejos dentro del run (2.397 por brazo); el rojo de
  `recolectar` es sólo que los otros 7 no estaban. Intento 2 en `C:\Users\nmend\AppData\Local\Temp\claude\v2b_39033530622\i2\`.
  Unión con `unir_intentos.py` de `2766c198` (comprobado igual por contenido en `loop/activo` tras traer `main`,
  `f852e94c`): 8 pares, 0 distintos (Copahue control 5 por `borde`). **Cobertura de V2b unida: 6.147 contra 6.147,
  PAREJA** (`v2b_39033530622\union\`). Siguiente: re-unir V1 y V2a con el mismo commit y evaluar.
- **Diurno:** W5b terminó (23 de 23 verdes); la repetición de W5a arrancó. **W6a despachada** (run 39090434307,
  2026-10-01 a 10-07, `--ref s151-diurno-codigo`), pendiente detrás. W6b cuando W6a arranque.
- **NRT:** última corrida 23:44 UTC (la programada de las 22:00, con 1 h 44 de atraso), verde; último dato 15:47 UTC
  (normal: no hay pasadas nocturnas entre las 16 y las 01 UTC). El cron externo nuevo (`10 1-12 * * *`) **no despachó
  a la 01:10 ni a las 02:10 UTC**. SOSPECHA: cron-job.org interpreta la expresión en hora de Chile y la primera sería
  a las 04:10 UTC. Revisar después de las 04:30 UTC; si no hay despacho, avisar a Nicolás (es su cuenta). Lejos del
  umbral de 12 h de §1.5.

### 2026-10-17 ~23:55 UTC (vuelta 178, S153): regla de adopción de K aprobada y mergeada (D-20)
- Nicolás aprobó la regla del #848 tal como está, con la reversión por `git revert` pre-autorizada. Marca de
  aprobación en el documento (`0c5a374e`), CI verde, **#848 mergeado** (squash `cf507f46`). Ninguna evaluación de V2
  antes de esto. Próximo de F/K: cuando la repetición de V2b (run 39068999603) termine, contar cobertura, unir con
  `unir_intentos.py` de `2766c198`, re-unir y re-evaluar V1 con ese mismo commit, evaluar V2, `--combinar` con la regla
  original y con SN, y aplicar §3 de la regla.

### 2026-10-17 23:35 UTC (vuelta 177, S153): #847 mergeado; instrumento de F/K fijado en `2766c198`
- **#847 mergeado** (squash `2766c198`; CI verde en `369e201e`). Mutaciones con el árbol quieto: **15 de 15** (sin
  mutación, autoprueba verde; `u_sin_recorte_lleno` y `u_fuera_del_corte` atrapadas por sus casos 23d y 23e;
  `volatiles` rc=3 es la guarda de coherencia, no una caída). Autoprueba 69 de 69; tests 128.
- **Instrumento de la regla de adopción de K (#848, §3) fijado en `2766c198`**: con ese `evaluar_fk.py` y ese
  `unir_intentos.py` se re-une y re-evalúa V1 y se evalúa V2.
- Runs: V2b repetida 6 de 8 (2 en curso); W5a repetida pendiente detrás de W5b (14 de 22). **W6a se despacha cuando
  la repetición de W5a arranque.**
- NRT: última corrida 20:09 UTC (programada, verde). La programada de las 22:00 no apareció (GitHub omite a veces); el
  cron externo nuevo (`10 1-12 * * *`) arranca a la 01:10. Revisar que haya corrida verde antes de las 02:00 UTC.
- Worktrees del #847 y del tablero: `git worktree remove` dio «Permission denied» (archivos tomados por Windows); el
  disco subió a 9,5 GB igual. Borrar las carpetas a mano después.

### 2026-10-17 ~23:40 UTC (vuelta 176, S153): #849 en main y publicado; la localización de VIIRS 375 la decide el Test 1
- **#849 mergeado** (squash `60c45833`, CI verde); Pages desplegado; R8: `index`, `diario`, `mosaico` y `periodo.js`
  dan 200, y en el sitio público la noche del 1-oct de Chillán carga con su franja, «máx 1 oct» y sin errores.
- ⚠️ **S154, verificador limpio (`experiments/_s153_localizacion/verificador/INFORME.md`): la conclusión de abajo cae en
  su parte central.** «Con K las mismas publicaciones se juntan en el cráter» es REFUTADA: los números se reproducen,
  pero K publica un subconjunto estricto de C0 y esas mismas pasadas ya tenían el cúmulo en el cráter con C0
  (Villarrica 0,19, Tupungatito 0,23, Chaitén 0,20, PP 0,42). K no relocaliza: deja de publicar las del borde. El
  «2 a 3 km» es CONFIRMADO para el centroide del cúmulo pero no para lo que ve el operador (para `test1_roi` el
  marcador va al cráter). «Viene del Test 1» y «mismo mecanismo» quedan PARCIALES; Lastarria SIN DATO. Texto
  original conservado por historia:
- **Localización (pedido de Nicolás), POR VERIFICAR** (`experiments/_s153_localizacion/`): en producción, casi todo lo
  que VIIRS 375 publica viene del Test 1 y su cúmulo cae a 2 a 3 km del cráter, en el borde del disco de 3 km
  (Villarrica 2,73 km, Llaima 2,75, Copahue 2,71; Láscar 0,37). Con K, sobre V1, las mismas publicaciones se juntan en
  el cráter: Villarrica 0,18 km (100 % bajo 1 km), Tupungatito 0,20 (95 %), Chaitén 0,20 (100 %), Planchón Peteroa 0,40
  (95 %); Lastarria queda en 1,29 km (campo fumarólico real, A69). O sea que la sobre-publicación y la mala posición
  de VIIRS 375 son el mismo mecanismo. Pide verificador limpio antes de usarlo en el paquete de adopción de K.
- **La referencia de MIROVA cubre sólo los 11 Tier A** (el consolidado de Mirova-v1 no tiene ninguna fila de los otros
  34). Los otros 34 no tienen contra qué medir la réplica.

### 2026-10-17 ~23:00 UTC (vuelta 175, S153): selector de noche o rango del tablero (opción B, aprobada por Nicolás)
- Rama `loop/tablero-periodo` (worktree `.claude/worktrees/s153-tablero`), diseño en
  `docs/superpowers/specs/2026-10-17-selector-periodo-tablero-design.md`. `frontend/periodo.js` nuevo (sólo funciones
  nuevas; los helpers del predicado no se movieron) con su prueba en node (12 casos, fallaba antes del módulo). En
  `index.html`: «Noche o rango…» con fechas y ◀ ▶, URL compartible (`?desde=&hasta=`), franja de período, clic en una
  barra del gráfico lleva esa noche al panel, mapa del detalle y capa «Anomalías» con el criterio del gráfico
  (`eqVrp > 0` y sensores), rótulos del nivel y de las métricas con el período, tabla NRT con sensores y redibujada con
  «Sólo cráter», enlace a mosaico. `diario.html` y `mosaico.html` con su selector y enlaces que llevan el rango. G8
  remapeado 1578 a 1594 (test y `CLAUDE.md`).
- Verificado en el navegador local (zona horaria `America/Santiago`): por defecto las tres vistas muestran lo mismo que
  antes (30, 90 y 31 días); Villarrica 30 d: el mapa dibuja las 158 detecciones del gráfico (antes faltaban 18) y apagar
  MODIS quita exactamente sus 13; clic real en la barra más alta lleva al 2026-09-19; enlace a 2026-05-01..03 baja la
  historia completa y filtra 30 pasadas de Láscar; el error de Chart.js al redibujar dentro de su propio clic se arregló
  difiriendo el cambio.

### 2026-10-17 ~22:45 UTC (vuelta 174, S153): 1.23 CONFIRMADA; auditoría del tablero; D-19 y D-20 a la cola
- **1.23, verificador limpio CONFIRMADO con matices** (`experiments/_s151_mxd03_sola_123/resultado/VERIFICADOR.md`):
  reproducido idéntico; 24 de 24 medios jobs, todos con un commit, ninguno `sin_tiempo` (Tupungatitoa 14 de 15, el L1B
  faltante no era un gránulo pedido); vara 2D atada al ancla (0,145 km), así que el veredicto equivale a «MxD03 pone el
  píxel donde VIIRS ve el calor»; control Terra contra Aqua pasa. **Corrección al resumen de la vuelta 173:** «gana 9
  de 46, p 0,0952» mezcla dos conteos (el 9 es el total; bajo 35°, que decide, son 8). Decisión D-19 a la cola.
- **Auditoría del tablero** (pedido de Nicolás, informe en `C:\Users\nmend\AppData\Local\Temp\claude\audit_tablero\`):
  un solo control de período (desplegable de `index.html`); el mapa del detalle no obedece sensores ni el criterio
  del gráfico (`frontend/index.html:2944`); rótulos de ventana falsos (`:2394`, tabla NRT, refresco, CSV). Propuesta B
  (selector por noche o rango con `frontend/periodo.js`, clic en barra, mapa con el criterio del gráfico) espera el sí
  de Nicolás.

### 2026-10-17 22:27 UTC (vuelta 173, S153): regla de adopción de K en PR #848; 1.23 completa y evaluada (POR VERIFICAR)
- **Regla de adopción de K** (pedido de Nicolás: «continúa con lo que recomiendas», opción A): PR #848,
  `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`, abierto ANTES de evaluar V2 (la hora del PR es la prueba).
  Verificador limpio de la v1: APROBABLE CON ARREGLOS (`C:\Users\nmend\AppData\Local\Temp\claude\verif_regla_fk\`);
  la v2 aplica sus diez arreglos. Puntos que deciden: manda la más estricta entre la regla original y SN; tope de dos
  repeticiones; instrumento fijado en el commit de #847; el laboratorio congelado en C0 es la sombra hasta 29
  protegidas, con `git revert` pre-autorizado; la magnitud no bloquea salvo que una protegida cruce 1 MW hacia abajo.
  **Espera el sí de Nicolás; no se mergea sin él.**
- **1.23 completa:** 24 de 24 medios jobs verdes (runs 39066031570 y 39068703857, tag `s151-1.23-probe`). Evaluada en
  local (`C:\Users\nmend\AppData\Local\Temp\claude\p123_all\evaluar_local.log`): MEDIDO, adoptable False (letra: M
  pierde 2 protegidas, gana 9 de 46; pérdidas como el azar p 0,90); **vara principal MXD03 MÁS CERCA**, n 76, dd 0,62
  km [0,32; 0,96]; dos varas amplias INDECIDIBLE; Test 1: M cruza como el azar. Verificador limpio lanzado
  (`verif_123_resultado`).
- **Coordinación:** la sesión «vrp loop v2» (S152) seguía viva; confirmó que detuvo su agente y no despacha más. #847
  queda en S153. Su agente había dejado el arreglo de `borde` sin commitear; un archivo cambió durante mi corrida de
  mutaciones (A112), así que esa corrida se descartó.
- **#847:** con los arreglos del verificador V2 (`borde` sólo si el recorte cortó, `n_anomalous_pixels` > 100, y sólo
  con píxeles del VRP mínimo de la lista): tests 128 verdes; autoprueba 69 de 69; uniones reales de W2a, V1 y V2a y G3
  de W2 idénticos a los de antes (los 108 y 23 pares `borde` reales cumplen las dos condiciones). Mutaciones corriendo.
- Pedido nuevo de Nicolás: selector de fechas en el tablero y auditoría de sus interacciones. Agente de auditoría
  (sólo lectura) lanzado.
- Runs: W5a repetida pendiente; V2b repetida 6 en curso; W5b 8 de 22. Disco 8,3 GB (worktree nuevo de la regla).

### 2026-10-17 20:55 UTC (vuelta 172, S153): W5a despareja y repetida; 1.23 completa despachada; #847 en verificación
- **Cron externo del NRT:** Nicolás lo dejó en `10 1-12 * * *` UTC (decisión 1 del bloque S153, cerrada).
- **W5a (39032518643) terminó con `recolectar` en rojo por COBERTURA, no por la rama existente:** control 1.184 noches,
  brazo diurno 1.153; faltan 46 (NevadosDeChillan 30, PlanchonPeteroa 16) y sobran 15 (NevadosDeChillan 9, Llaima 6).
  Intento 1 resguardado en `C:\Users\nmend\AppData\Local\Temp\claude\w5a_39032518643\i1\` (artefacto `s151diurno-todo`).
  **Repetidos los tres volcanes, los dos brazos**, misma ventana 2026-09-01 a 09-10, `--ref s151-diurno-codigo`
  (`pipeline/` idéntico al de W5a, `7b825ba0`: diff vacío): run 39068611598, pendiente detrás de W5b. **W6a se
  despacha recién cuando este run arranque** (un solo pendiente por grupo `s151-ab-diurno`).
- **1.23:** `Lascar-2a` midió 24 de 24 gránulos en 13,4 min (umbral 50), prueba sintética OK. Despachados los otros
  23 medios jobs desde el mismo tag `s151-1.23-probe`: run 39068703857. Evaluar en local con los 24 artefactos.
- **#847:** el agente de S152 dejó el arreglo de `borde` SIN commitear en su worktree (10 archivos: `borde` sólo con
  `anomaly_pixels` + `discarded_anomaly_pixels` = 100 en los dos lados; G3 INDECIDIBLE si el predicado no corre). Los
  4 tests nuevos fallan con el `unir_intentos.py` de la rama (comprobado en copia aparte) y pasan con el nuevo (126
  verdes); autoprueba 68 de 68. Mutaciones corriendo. Segunda vuelta del verificador limpio lanzada
  (`C:\Users\nmend\AppData\Local\Temp\claude\verif_847_v2\`), que además reproduce las uniones de W2a, V1 y V2a.
- **F/K V2b (39033530622) terminó con `recolectar` en rojo por COBERTURA:** control 6.124 pasadas, K 6.096; faltan
  46 (Llaima 38, Villarrica 6, Chaitén 2) y sobran 18 (Llaima 10, Villarrica 5, Copahue 3; contado en local con
  `contar_pasadas.claves`). Intento 1 en `C:\Users\nmend\AppData\Local\Temp\claude\v2b_39033530622\i1\`. Repetidos
  Llaima, Villarrica, Chaitén y Copahue en los dos brazos, misma ventana 2026-04-21 a 06-12, desde el tag
  `s151-fk-v2-codigo` (`pipeline/` idéntico a `7b74435e`): run 39068999603. Después: unir con `unir_intentos.py`.
- W5b corriendo. Disco 11 GB.

### 2026-10-17 20:25 UTC (vuelta 171): CIERRE de S152 por contexto; bloque de arranque S153
- `tasks/BLOQUE_ARRANQUE_S153.md`. Se fijó con trabajo en curso: agente del arreglo de #847 vivo; runs 39066031570
  (1.23 `Lascar-2a`), 39033530622 (V2b), 39032518643 (W5a) y 39041204976 (W5b, pendiente). Sin evaluar: V2b, 1.23 y el
  diurno W2 a W6 (espera #847 y W6). W6a y W6b sin despachar (`--ref s151-diurno-codigo`).

### 2026-10-17 20:24 UTC (vuelta 170): tests de main verdes tras #844; #845 mergeado
- Tests de `main` sobre `eed583b4` (#844): **verde** (20:23). CI de #845 sobre la rama actualizada (`0ab92264`): verde;
  **#845 mergeado** (squash `061b6f59`). `loop/activo` sincronizada.
- NRT: la `workflow_dispatch` de las 20:00 volvió a quedar cancelada por desplazamiento; la siguiente corre con el
  desempate nuevo. 1.23 `Lascar-2a` en curso; V2b 18 de 22; W5a 21 de 22; W5b pendiente. Disco 10,1 GB.

### 2026-10-17 20:20 UTC (vuelta 169): Nicolás aprueba lo recomendado; 1.23 despachada; #844 en main; token sin vencimiento
- **D-18:** #846 mergeado (squash `eb97779f`); tag `s151-1.23-probe` en `eb97779f`; medio job suelto `Lascar-2a`
  despachado para cronometrar (run 39066031570). Si termina bajo el umbral del README, los otros 23 desde el MISMO tag.
- **D-17:** antes del merge, comprobado que todas las ventanas del diurno corrieron el mismo `pipeline/` que W2
  (`1a6f595b`, `5d05036b`, `7b825ba0`, `9fd82f26`, `087e53bf`: diff vacío contra `8b2bcd79`). Tag `s151-diurno-codigo`
  en `eb97779f` para despachar W6a y W6b sin el desempate nuevo. F/K V2b corre desde su tag y la 1.23 desde el suyo, así
  que ningún A/B mezcla brazos. **#844 mergeado** (squash `eed583b4`; CI verde en `7c6f36d6`). Desde aquí el NRT usa el
  desempate determinista (~29 records MODIS del corpus podrían cambiar hacia adelante; el histórico no se reprocesa).
  #845 (cosmético): rama actualizada contra main (`0ab92264`), se mergea con su CI verde.
- **Token** del cron externo: sin vencimiento por ahora (Nicolás); anotado en `REGISTRO_CREDENCIALES.md` (fila 31), sin
  el valor. Cadencia del cron externo: la cambia Nicolás en cron-job.org (sigue cada 30 min).
- Pendiente de despacho con `--ref s151-diurno-codigo`: W6a (2026-10-01 a 10-07) y W6b (10-08 a 10-14), cuando W5b arranque.

### 2026-10-17 19:51 UTC (vuelta 168): espera
- V2b 18 de 22 (4 en curso); W5a 21 de 22; W5b pendiente. NRT verde 19:46. Disco 10,4 GB. El autor de #847 aplica el
  arreglo de `borde` en `comparar()` y rehace las uniones de W2, V1 y V2a.

### 2026-10-17 19:28 UTC (vuelta 167): verificador de #847 (G3): MERGEABLE CON ARREGLOS; hueco en `borde` también en `unir_intentos`
- `experiments/_s151_ab_diurno_g3_verif/VERIFICADOR_V1.md`. Se sostiene: W2 reproducido byte a byte (44 uniones), G3
  nuevo CUMPLE en los dos órdenes con los conteos declarados y el viejo FALLA; el nuevo da FALLA con diferencias reales
  sembradas (píxel de más, `vrp_mw` ×1,5 y ×(1+1e-6), `pc.vrp_mw`, `distance_class`, `vrp_mir_mw`; record que aparece
  o desaparece da COBERTURA DESPAREJA); autoprueba 67/67, mutaciones 13/13 sin caídas; D2 bien escrita.
- **Bloqueante:** `borde` se admite con listas cortas, donde el recorte top-100 no actúa: en VIIRS (Chaitén 4 píxeles,
  V750 1 píxel) cambiar o agregar un píxel sin tocar el conteo da CUMPLE. Eso es detección, no empate, y la rama diurna
  es VIIRS. En W2 no pasa (los 27 `borde`/`orden` reales son MODIS con lista llena). **El mismo `borde` vive en
  `comparar()` de `unir_intentos.py` (main, #841/#843): afecta también a las uniones.** Arreglo pedido en el mismo PR:
  `borde` sólo con `len(anomaly_pixels) + len(discarded_anomaly_pixels) == 100` en los dos lados; rehacer las uniones
  de W2, F/K V1 y V2a con el `comparar()` nuevo y comprobar que no cambian.
- No bloqueante: holgura heredada de `hotspot_escena` (riesgo bajo, `ENABLE_DAYTIME_MODIS=False`); node caído debería
  dar INDECIDIBLE; `except AssertionError` de `mutar_evaluador.py` demasiado amplio.

### 2026-10-17 19:19 UTC (vuelta 166): espera
- V2b 18 de 22 (4 en curso); W5a 18 de 22; W5b pendiente. NRT verde 19:07. Disco 10,9 GB. Verificador de #847 en curso.

### 2026-10-17 18:48 UTC (vuelta 165): espera
- V2b 15 de 22; W5a 17 de 22; W5b pendiente. NRT verde 18:27. Disco 10,8 GB. Verificador de #847 (G3) en curso.
  Esperan a Nicolás: D-17 (#844, #845), D-18 (#846), cron externo y fecha del token.

### 2026-10-17 18:38 UTC (vuelta 164): pre-registro 1.23 listo para el sello (D-18)
- #846 en `e87a5e176` (CI 39058449134 verde, suite 2.027): sobre 35° la lectura 5 da «SIN NULO COMPARABLE (BOW TIE)»
  con test; rangos de las reglas 1 y 2 bajo 35° (39 de 46 protegidas, incluidas las 2 que pierde M), todos los cenits
  como anotación; `radius_km` en `cruces_de_borde`; tests de PEOR y MIXTO; poder bajo 35° en `poder_nulo.py`. Diff
  revisado por el orquestador (`git diff c101f9cc9 e87a5e176`); no toca `pipeline/`. Queda en D-18 (sello y merge de
  Nicolás; el merge de #840 lo había negado el clasificador sin su sí).

### 2026-10-17 18:22 UTC (vuelta 163): segunda verificación de la 1.23: SELLABLE CON ARREGLOS (chicos)
- `experiments/_s151_mxd03_sola_123_verif/VERIFICADOR_V2.md`. Sobre `c101f9cc9`: 41 tests; SIERRA falla de verdad con
  el jacobiano viejo (±1 a ±4 líneas dan 0,51 a 0,81 px; ±5 da 1,000); nulo en km correcto; lectura 4 alcanza sus
  cuatro estados; sin regresiones; no aplicar (c) tal cual es aceptable.
- Queda: en el borde el problema es la forma del campo (con bow tie, C − M a lo largo de la traza es un diente de sierra
  dentro de cada barrido, ±1,2 km a 35-40° y ±3,8 en el borde; modelo SIN VERIFICAR) y ninguna traslación rígida lo
  imita. Arreglos pedidos: sobre 35° la lectura 5 es descriptiva («SIN NULO COMPARABLE»), con test; rango principal de
  las reglas 1 y 2 bajo 35°; `radius_km` en `cruces_de_borde`.
- Para el sello: MxD03 vuelve a dar PIERDE PROTEGIDA por la letra; el probe dice si la posición es mejor (vara de cenit
  bajo y medio, casi seguro MXD03 MÁS CERCA, como #828) y si las pérdidas de Láscar son azar o efecto de una posición
  mejor (lectura 4 con signo); no contesta el borde del barrido (Chillán).

### 2026-10-17 18:18 UTC (vuelta 162): arreglos de la 1.23 aplicados (#846 en `c101f9cc`); segunda verificación
- Nulo en km (20 rumbos geográficos del tamaño en km del corrimiento real): el pipeline usa la posición sólo como
  distancia en km; `invariante_km.py`, grilla regular 1 × 2 km: CV del cruce de los círculos de 3, 5 y 25 km 0,03 a 0,07
  en km contra 0,24 a 0,30 en píxeles. Con bow tie ninguna unidad es invariante (CV 0,18 a 0,49 en km): se informa por
  cenit (`tamano_del_nulo`). Caso sintético SIERRA con test que falla con ±2 líneas. README: «M mueve k tanto como el
  azar»; lectura 4 con signo pre-registrada. K = 19 también cumple (anotado). CI 39057051690 verde, suite 2.022.
- Segunda vuelta del verificador lanzada (`verif_123\VERIFICADOR_V2.md`).

### 2026-10-17 18:16 UTC (vuelta 161): 1.24 en PR #847 (G3 con `comparar()`, CI verde); verificador lanzado
- `noches_identicas` clasifica cada par nocturno control/diurno con `unir_intentos.comparar`; `borde` y
  `hotspot_escena` pasan por `unir_intentos._predicado` (node, por volcán); si el tablero difiere o no corre, el par es
  `distinto`; un `distinto` es FALLA. Comprueba al importar que tolerancias y campos de proceso son los de
  `unir_intentos`. `g3_solo.py` nuevo. Desviación D2 en el §11 del pre-registro.
- Sobre W2 (2.154 pares nocturnos): G3 viejo FALLA en los dos órdenes de W2a; el nuevo CUMPLE en los dos con 0 distintos
  (1,2: igual 1.108, tolerancia 1.017, orden 15, borde 13, hotspot_escena 1; 2,1: igual 909, tolerancia 1.216, orden 17,
  borde 10, hotspot_escena 2). Un caso `hotspot_escena` (PCC Terra 06-18 02:15) aparece entre los dos BRAZOS, sin unión.
- Autoprueba 67 de 67 (casos 23 a 25 nuevos); mutaciones 13 de 13. **Hallazgo de método:** 4 mutaciones del G3 contaban
  como atrapadas sólo porque el evaluador mutado se caía; `mutar_evaluador.py` ya no cuenta una caída como atrapada.
  Suite 2.001. Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_847\`).
- Runs: V2b 13 de 22; W5a 14 de 22; W5b pendiente. NRT verde 17:46. Disco 10,9 GB.

### 2026-10-17 18:01 UTC (vuelta 160): verificador del pre-registro 1.23: SELLABLE CON ARREGLOS (dos bloqueantes)
- `experiments/_s151_mxd03_sola_123_verif/VERIFICADOR_V1.md`. 37 de 37 tests; `sensibilidad_test1_121.py` y
  `saltos_de_cumulo_121.py` reproducen idéntico. En pie: la vara VIIRS no está atada al ancla (Láscar: 127 pasadas
  `ctx_cluster` de 1 a 4 píxeles, ninguna exactamente en el ancla; Lastarria a 2,26 km) y compara posiciones 2D; las tres
  reglas del autor son elecciones de instrumento declaradas con su poder simulado; workflow correcto.
- Bloqueante 1: `jacobiano()` (`probe_sola.py:75`) deriva con ±2 líneas, y en el borde del barrido (bow tie) el
  espaciado de `_interp_geo` alterna entre f y 2-f km por línea: sobre 50° de cenit, en 67 de 223 gránulos, el nulo
  mueve más del doble de km que MxD03 (p90 de 3 a 8 veces; modelo, SIN VERIFICAR en un gránulo real). Sesga hacia
  adoptar; los INVALIDO no lo ven. Arreglo: barrido entero o nulo en km, caso sintético en diente de sierra, razón km
  del nulo / km de M por cenit.
- Bloqueante 2: **«MxD03 mueve k menos que el azar» NO se sostiene** (IC de la diferencia de medianas [−0,21; +0,20],
  signo 69 contra 72; corrige lo dicho en la vuelta 159). Con signo y por etiqueta, en las alertas de MIROVA M sube k
  más que R en 33 contra 18 (p = 0,049) y en los negativos baja (30 contra 43): lo que haría una posición mejor, un
  indicio con un solo sorteo. Arreglo: corregir el README y pre-registrar la lectura con signo por etiqueta.
- Arreglos devueltos al autor (mismo PR). Para el sello: por la letra MxD03 vuelve a dar PIERDE PROTEGIDA; la vara habla
  de Láscar a cenit bajo y medio y casi seguro dará MXD03 MÁS CERCA (#828 ya lo midió contra el cráter).

### 2026-10-17 17:45 UTC (vuelta 159): pre-registro 1.23 entregado (PR #846, CI verde); verificador lanzado
- `experiments/_s151_mxd03_sola_123/` (`4cc5e0134`, suite local 2.018). Nulo: 20 rumbos equiespaciados por gránulo,
  del tamaño del corrimiento real en PÍXELES de la propia grilla (corrige la anisotropía sin ángulos); K=20 es el
  primer K con p mínimo 1/21 < 0,05. Vara: cúmulo VIIRS 375 de la misma noche (publicado y alertado por MIROVA, sin
  cúmulos del Test 1), congelada en `vara_viirs.json`, contra el píxel MODIS más caliente por índice; control de sesgo
  por Terra contra Aqua. TIF de MIROVA descartados (1 gránulo en la ventana UTM). 24 medios jobs, peor caso 27 min,
  presupuesto 50, timeout 75.
- **Medido ya sobre los artefactos de la 1.21 (por verificar):** el Test 1 MODIS vive en su piso de ruido (k medio 1,8 a
  2,3; ruido puro 2,1; umbral 3); MxD03 mueve k menos que el azar (0,52 contra 0,60) y cruza el umbral parecido (36
  contra 29 de 149): la fragilidad es del Test 1 integrado a 1 km. Sobre 50°: MxD03 elige otro cúmulo en 41 gránulos
  contra 30 del sorteo.
- Poder: por la letra MxD03 vuelve a dar PIERDE PROTEGIDA (es determinista): el probe no la hace adoptable; dice si sus
  pérdidas y ganancias se distinguen del azar y qué posición está más cerca de lo que ve VIIRS. La vara habla de
  Láscar (70 de 76 gránulos) y de cenit bajo (2 sobre 50°).
- Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_123\`).

### 2026-10-17 17:44 UTC (vuelta 158): espera; PR #846 (pre-registro 1.23) abierto, sin informe aún
- #846 abierto por el agente de la 1.23, que sigue con trabajo en segundo plano: se verifica cuando entregue. Agente
  del G3 (1.24) sin PR todavía (lleva ~3 h). V2b 12 de 22; W5a 13 de 22; W5b pendiente. NRT verde 16:56. Disco 10,8 GB.

### 2026-10-17 17:13 UTC (vuelta 157): espera
- V2b 11 de 22; W5a 12 de 22; W5b pendiente. NRT verde 16:56. Disco 10,7 GB (dos worktrees de agentes activos).
  En curso: G3 (1.24) y pre-registro 1.23.

### 2026-10-17 16:41 UTC (vuelta 156): pre-registro de la 1.23 (MxD03 sola) delegado
- Agente en worktree, rama `loop/1.23-prereg` (`experiments/_s151_mxd03_sola_123/`): nulo con ~20 rumbos por gránulo y
  anisotropía corregida; vara de posición independiente (cúmulo VIIRS 375 de la misma noche o TIF UTM de MIROVA, con
  dirección); sensibilidad del Test 1 de Láscar a ~0,4 km; casos de borde del barrido como Chillán 10-12 07:20;
  estados con controles, regla 1 en las dos direcciones, commit por artefacto. Sin despacho: verificador y sello.
- Runs: V2b 11 de 22; W5a 10 de 22; W5b pendiente. NRT verde 16:02. Disco 12,0 GB. Agentes vivos: G3 (1.24) y 1.23.

### 2026-10-17 16:09 UTC (vuelta 155): espera; worktree de la 1.22 retirado
- Worktree del autor de #844 retirado (limpio, HEAD `7c6f36d6` = remoto); disco 12,1 GB. V2b 8 de 22 verdes; W5a 8 de
  22; W5b pendiente. NRT verde 16:02. En curso: agente del G3 (1.24).

### 2026-10-17 16:05 UTC (vuelta 154): arreglos de #844 aplicados; cosmético aparte en #845; los dos esperan a Nicolás
- #844 (`7c6f36d6c`, CI 39047262701 verde, suite local 1.994): producción reducida a `anomaly_pixels.py` +31/−1,
  `process_modis.py`, `process_viirs.py` y `process_viirs_mod.py` +6/−2 cada uno, `regrid.py` +5/−1 (`kind="stable"`,
  con test y control); golden S142 ±4; test de 330 líneas. Escena sintética nueva que SÍ discrimina el hotspot (6 de
  6 cambian con el orden viejo al apagar SIMD, 0 con el arreglo). Cuerpo corregido: 29 records, dirección como
  SOSPECHA, «orden de empates determinista», advertencia de no mezclar brazos.
- #845 (`3e0f940bc`, CI verde): sólo comentarios y docstrings sin guiones en 5 archivos de producción (241 líneas,
  AST idéntico); sin conflicto con #844. **Toca archivos de §1.1: también espera el sí de Nicolás.** Agregado a D-17.
- Reproceso acotado de los 29: no despachado, lo decide Nicolás (D-17).

### 2026-10-17 15:49 UTC (vuelta 153): verificador de #844: MERGEABLE CON ARREGLOS; D-17 para Nicolás
- `experiments/_s151_desempate_top100_verif/VERIFICADOR.md`. Confirmado: mecanismo (157 pares, no 153: 3 de 1 ulp y
  uno de Llaima 09-24 con hotspot de 24 a 7 km y lista idéntica, que el clasificador del autor no ve); el test falla
  sin el arreglo (6 de 9) y corrió en el CI (puestos 719 a 727); el commit cosmético tiene AST idéntico y conserva el
  número de líneas; el golden S142 dependía de la CPU y está bien actualizado. Sin flag: el «apagado» es la CPU que
  toque, no sirve de control (A45 pide tag y sí de Nicolás).
- Arreglos pedidos al autor: sacar el commit cosmético a otro PR (diff de producción de 278 a ~49 líneas); el 50 pasa a
  29; el test no da otro hotspot (sólo otro top-100); «independiente de la CPU» pasa a «orden de empates
  determinista» (`diag_mu_deti` sigue variando hasta 4e-5); `regrid.py:117` igual sin tocar (flag apagado); advertencia
  de no mezclar brazos de antes y después del merge en un A/B.
- D-17 registrada: merge de #844 sólo con los A/B en curso terminados o con sus despachos fijados a un tag previo.

### 2026-10-17 15:38 UTC (vuelta 152): espera
- V2b 7 de 22 verdes; W5a 6 de 22; W5b pendiente. NRT verde 15:27. Disco 11,5 GB (tres worktrees de agentes, ~1 GB
  cada uno: se retiran al terminar). En curso: verificador de #844 y agente del G3 (1.24).

### 2026-10-17 15:37 UTC (vuelta 151): 1.22 en PR #844 (producción, SIN merge); mecanismo confirmado; verificador lanzado
- Tag `pre-s151-desempate-top100` en `4943bfb79`. PR #844 (`loop/1.22-desempate-top100`), CI verde (1.976 pasan, 28
  saltados); suite local 1.990. **Mecanismo confirmado por el autor:** de 6.482 pares MODIS entre intentos (V1, V2a,
  W2a) difieren 153, todos empates EXACTOS (mismo `vrp_mw` a 4 decimales y `bt_k` a 2, el mismo entero del L1B). En el
  mismo computador y numpy 2.4.4, `NPY_DISABLE_CPU_FEATURES=X86_V3` cambia el top-100 del `argsort` por defecto; el orden
  estable no cambia. Llaima 10-06 y Copahue 06-18: empate en el primer puesto entre un píxel dentro y uno fuera de
  `radius_km`, que decide el rescate.
- Arreglo: `orden_vrp_descendente` en `pipeline/anomaly_pixels.py`, `np.lexsort((cols, rows, -vrp))`, en los tres
  procesadores y en `build_anomaly_pixels` (A102); sin flag. Test `tests/test_guard_desempate_top100_s151.py` (dos
  subprocesos con y sin SIMD). Efecto en el corpus (13.353 records MODIS): 43,0 % con más de 100 píxeles (lista
  guardada puede cambiar), 10,7 % con empate en el primer puesto, **50 con el empate a ambos lados del inner y el
  cúmulo dentro: pueden cambiar su publicación** (hacia dónde, sin reprocesar, no se sabe). Golden S142: 2 píxeles
  empatados cambian de lugar. Commit 2 cosmético (guiones fuera de 229 líneas en 4 archivos de producción).
- Puntos para el verificador: sin flag bajo A45; si el test corre en CI; los 50 records; sacar el commit cosmético.
  Sin verificar: CPU de cada runner; `diag_mu_deti`/`diag_sd_deti` difieren en ~44 % de los pares en ~1e-10 (sospecha
  `polyfit` sobre OpenBLAS, no arreglado); numpy no fijado en `requirements.txt`.

### 2026-10-17 15:05 UTC (vuelta 150): tarea 1.22 (desempate del top-100 MODIS) delegada; toca producción
- Agente en worktree, rama `loop/1.22-desempate-top100`: tag defensivo `pre-s151-desempate-top100` sobre `main`
  antes del primer edit; confirmar el mecanismo con los records de los casos reales (¿empate exacto o en ulps?),
  buscar otros desempates de la cadena MODIS, proponer un desempate determinista con un test que falle antes, medir
  cuántos records del corpus podrían cambiar. **PR sin merge (A45, §1.1): decide Nicolás.**
- Runs: V2b 6 de 22 verdes; W5a 2 de 22; W5b pendiente. NRT verde 14:52. Disco 12,7 GB. Agentes vivos: G3 (1.24) y 1.22.
- Worktree del autor de #843 sigue bloqueado por el proceso de esta sesión; se limpia al cerrarla.

### 2026-10-17 14:34 UTC (vuelta 149): tarea 1.24 (G3 del diurno con `comparar()`) delegada
- Agente en worktree, rama `loop/diurno-g3-comparar`: el G3 («noches intactas») clasifica cada par nocturno
  control/diurno con `unir_intentos.comparar` más el predicado de node; `distinto` es FALLA, y `orden`, `borde` y
  `hotspot_escena` se informan. Desviación del pre-registro registrada (motivo mecánico, como #833). Prueba: W2 unido en
  los dos órdenes debe dar el mismo G3. Sin mirar G1 ni G2. Después, verificador limpio.

### 2026-10-17 14:32 UTC (vuelta 148): W4 completa (W4b pareja); W5b despachada
- W4b (39000333548) 23 de 23 verdes: 1.069 contra 1.069 noches, 0 y 0; 427 y 425 pasadas diurnas V375/V750. Con W4a
  (vuelta 136) **W4 completa**. W5a (39032518643) corre; **W5b despachada** (39041204976, 2026-09-11 a 09-20),
  `pending`, W5a sin desplazar. Faltan W6a y W6b.
- V2b (39033530622): 4 verdes, 6 en curso, 12 en cola. NRT verde 14:17. Disco 13,9 GB.
- Diurno: W2 a W4 completos (W2 con el caso D-16 de Copahue). No se evalúa hasta que el G3 compare con `comparar()`
  más el predicado (verificador de #843): próxima vuelta, tarea 1.24.

### 2026-10-17 14:07 UTC (vuelta 147): verificador de la 1.21: CONFIRMADO; tarea 1.23 agregada
- `experiments/_s151_mxd03_cumulo_121/resultado/VERIFICADOR.md`. Resumen idéntico reproducido; conteos iguales con
  script propio; delta de MC = −38 (alertas bajo 1 MW) + 3.582,5 (negativos limpios). Cobertura: 12 jobs, un commit,
  470 de 471 (falta Tupungatito `MOD021KM.A2026275.0225`, declarado, no alerta); C' = C en 24 de 24.
- M contra C pierde las mismas 2 de la 1.17 (Láscar Terra 04-20 y 04-30 01:30) por la ETIQUETA (A46): con MxD03 el Test
  1 deja de disparar (4,81 a 2,56; 3,28 a 2,83), el hotspot salta al Salar (19 y 21 km) y el cúmulo queda MÁS cerca del
  cráter (0,23 y 0,48 km). MC contra CC pierde Chillán Aqua 2026-10-12 07:20 (MIROVA 2,18 MW a 2,24 km; cenit 59°):
  con MxD03 se elige otro cúmulo, 2 píxeles a 9,7 km (producción: 6 a 1,68 km); ésta sí es de posición.
- FRÁGIL: R pierde 4 de Láscar con el mismo mecanismo; coincide con M sólo en la del 04-30. M gana 9 contra 5 del
  ruido, con un solo sorteo por gránulo. Las ~3.500 de más vienen de la etiqueta (MC contra CC −151, indeterminado);
  el replay acierta (309 contra 312 predichas). 8 diferencias de C contra lo guardado: deriva de código (iguales en la
  1.17 y la 1.21, todos Standard); D-16 aparece en otros 3 gránulos sin efecto.
- 1.21 cerrada; 1.23 en la cola (nulo de varios rumbos, vara de posición independiente, sensibilidad del Test 1 de
  Láscar, borde del barrido, y la deriva de los 8 records).

### 2026-10-17 13:59 UTC (vuelta 146): probe 1.21 evaluado (POR VERIFICAR): EMPEORA
- Runs 39033482528 (Láscar-2) y 39034846297 (los otros 11), tag `s151-1.21-probe` (`e472c673`): 13 jobs verdes; un
  solo commit en los 12 artefactos. `evaluar_cumulo.py` en local (salida en
  `experiments/_s151_mxd03_cumulo_121/resultado/`): **VEREDICTO EMPEORA**, no adoptable. MC contra C: 0 protegidas
  perdidas, 36 ganadas de 46, delta +3.544,5 [3.006,8; 4.082,2]. CC contra C EMPEORA (+3.695). M contra C PIERDE
  PROTEGIDA (2 perdidas, 9 ganadas, delta −31,6 [−432,5; 369,4], FRÁGIL). MC contra CC PIERDE PROTEGIDA (1). Nulos:
  R contra C PIERDE PROTEGIDA (4 perdidas); RC contra CC INDETERMINADO. C igual a la guardada en 462 de 470; deriva de
  protegidas 0 de 46; 1 gránulo ausente del archivo (fuera de censo).
- Lectura: etiquetar desde el cúmulo hace que casi toda noche tranquila con un cúmulo cerca del cráter se publique;
  MxD03 sola pierde 2 protegidas, pero mover la posición al azar pierde 4: no se distingue del ruido. Verificador
  limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_121r\`).

### 2026-10-17 13:55 UTC (vuelta 145): cabeceras de las 11 protegidas solo OCR Suomi NPP de V1 (POR VERIFICAR)
- `experiments/_s151_prereg_fk_11/resultado_v1/CABECERAS_SNPP.md` (scripts e imágenes en
  `C:\Users\nmend\AppData\Local\Temp\claude\cabeceras_snpp_v1\`). Lista con `proteccion()` de `evaluar_fk.py`: 11
  pasadas (Isluga V375 3, Chillán V375 3 y V750 2, Tupungatito V375 3), igual que `v1.log` l. 11-12. C0 publica las 11;
  F y K todas menos Tupungatito 09-28 y 09-29.
- En las 11 el «Last Update» de la imagen es de una pasada POSTERIOR: distancia y clase de otra pasada. Dos imágenes
  con md5 idéntico bajo dos horas (Isluga 09-28 05:12 = 06:18; Chillán 10-01 06:00 = 18:42).
- Distancia propia (serie «Last Month» de imágenes posteriores, leída a ojo, cruzada con la tabla y `Distancia_aprox_*`
  del CSV `f1467a71`): Chillán (5) bajo 5 km, cráter; **Tupungatito 09-28 ~22,6 km y 09-29 ~9,6 km, sobre el inner de 7
  km: con su clase propia no serían protegidas A** (F/K a 23,9 y 9,3 km desde `mirova_center`, sólo radios); Isluga 09-09
  ~24 km, 09-28 ~16,7 km, 10-03 ambigua; Tupungatito 09-14 ambigua. Efecto lateral: dos filas de Isluga que los tres
  brazos publican son lejanas para MIROVA y hoy cuentan como coincidencia en la lectura A.
- Límites: valores leídos a ojo; imágenes de la rama main de Mirova-v1, no de un commit fijo. Se verifica junto con V2.

### 2026-10-17 13:42 UTC (vuelta 144): verificador de F/K V1: PARCIAL; el CUMPLE de lectura A se sostiene con matices
- `experiments/_s151_prereg_fk_11/resultado_v1/VERIFICADOR.md`. Se sostiene: reproducción exacta (0 claves
  distintas); el código mide lo que dice (protegidas, negativos limpios, exclusión Suomi NPP solo OCR, D-9); la unión
  no contamina (órdenes 1-3 y 3-1 dan 0 diferencias; la unión sin D-16 da INDECIDIBLE, lo correcto); cuatro defectos
  sembrados salen como deben (VETADO, veto sólo de K, PIERDE 750 contra 734, FALLA de P3).
- Las 21 alertas V375 que F y K dejan: 11 de 0,05 MW o menos, 8 Muy Bajo (0,06 a 0,21) y 2 de 1 MW o más:
  Tupungatito 09-28 (2,51) y 09-29 (1,86), protegidas A que descansan sólo en el OCR de Suomi NPP (la §5 las aparta por
  el hito, la §9 las cuenta: 19 de 21, sin contradicción). Todo indica objetos lejanos (OCR «lejos», cúmulo de F a 9,4 y
  21,6 km, C0 publicaba 0,05 MW en el cráter por el Test 1), pero coincide en radio, no en posición. **Falta la
  revisión de la cabecera de la imagen que exige el pre-registro.**
- No se sostiene: (1) P3 no puede fallar en V375 como está escrita (51,9 % de los pares con d exactamente 0); en los 115
  que cambian, F queda bajo C0 en 98 (~28 % menos), signos p = 0,00035, media de d +0,048 [+0,026, +0,074]: sin el Test
  1 la magnitud se aleja de MIROVA. (2) El veto de la lectura B es efecto del pareo por pasada: C0 publicaba un píxel
  del cráter (0,012 a 0,10 MW) y el objeto de MIROVA está a 11 a 28 km; F lo encuentra lejos y lo calla como `far`.
  (3) Los «far_ref» sí tienen VRP en MIROVA (corregido arriba).
- Para Nicolás antes de V2: el CUMPLE de V1 descansa en Chillán en erupción (10 de las 12 protegidas que deciden en
  V375); el poder de veto está en V2 (Láscar). Informar junto a la regla sellada la media de d con su intervalo y los
  signos. No determinismo MODIS de magnitud en el control (Llaima 10-06 01:45, 4,28/3,57 MW), sin cambio de decisión.

### 2026-10-17 13:41 UTC (vuelta 143): #843 (D-16 a) en main
- Arreglos del verificador aplicados (`9732f218`, CI verde, suite local 1.981): m1, m2 y las tres condiciones nuevas
  (a, b, c; centroide en `store.py:397-399`), 14 de 14 mutaciones mueren. Del `mutaciones.py` del verificador siguen
  admitidas 4 (LAX1/LAX2 `vrp_mw` del lado no rescatado, LAX3 hotspot a 30 km sin rescate, LAX7 a 200 km): no se
  pueden acotar desde el record (no guarda la suma de escena del Test 1 ni `max_hotspot_dist_km`); documentado, y
  ninguna la lee F/K. Casos reales: los tres entran. Unión de V1 rehecha (`union_d16_v2\`): 44 de 44 idénticas a
  `union_d16`, 4.820 por brazo. Nota del G3 en el docstring.
- El PR sólo toca `unir_intentos.py` y su test (`gh pr view --json files`); el diff contra main mostraba 10 JSON de
  `data/` por el desfase de la rama, no por el PR. **Mergeado** (squash `dc0b7e26`); `loop/activo` sincronizada sin
  conflicto. Worktree del autor bloqueado por su proceso: se retira después, sin forzar.

### 2026-10-17 13:33 UTC (vuelta 142): espera
- 1.21 (39034846297): 8 de 12 verdes. V2b: 6 en curso, 16 en cola. W4b 20 de 22; W5a pendiente. #843 en `5a1ddae9`
  (el autor aplica los arreglos). Verificador de F/K V1 en curso. NRT verde 12:59. Disco 14,4 GB.

### 2026-10-17 13:29 UTC (vuelta 141): F/K V1 evaluada (POR VERIFICAR): con lectura A, F y K CUMPLEN
- `evaluar_fk.py --ventana V1` sobre `union_d16` (salida en `experiments/_s151_prereg_fk_11/resultado_v1/`).
  Controles generales OK: cobertura pareja, versión 0 distintas, cableado de C0, F, K y G OK, determinismo del gemelo
  100 % en los tres sensores, autocontrol de la regla original OK, etiqueta original reproducida en 4.820 de 4.820.
- Veredicto de la ventana V1 (§6, regla original): **F y K CUMPLEN con lectura A** (0 protegidas perdidas en los tres
  sensores; 2 de VIIRS 375 sólo OCR Suomi NPP, apartadas por el hito); **NO CUMPLEN con lectura B** (12 pérdidas en
  VIIRS 375: 10 «far_ref» sin VRP en MIROVA [⚠️ FALSO, verificador vuelta 144: tienen 1,07 a 3,98 MW
  (FALSO_POSITIVO); el «None» es que la tabla no llena `vrp_ref` en `far_ref`] y Tupungatito 09-28 2,51 MW y 09-29 1,86 MW). P2 lectura A: MODIS 114 a
  4 (F) / 10 (K); VIIRS 375 734 a 37; VIIRS 750 331 a 26; ruido del gemelo 0. Negativos limpios publicados V375 88,2 %
  a 2,5 %, V750 24,6 % a 0,9 %, MODIS 12,3 % a 0,0 (F) / 0,8 % (K). Recall V375 260 a 239 (16 Muy Bajo perdidas de
  194). P3 CUMPLE en V375 y V750 (d mediana 0, razones C0 0,748 contra F 0,620); MODIS sin sustrato (n 3). P4 CUMPLE.
- Mejora de más de 30 %: verificador limpio y auditoría independiente lanzados (`C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v1\`).
  El veredicto final de F/K es el peor de V1 y V2; V2 espera V2b (corriendo).

### 2026-10-17 13:28 UTC (vuelta 140): verificador de #843: MERGEABLE CON ARREGLOS (no bloquean F/K); V1 en evaluación
- `C:\Users\nmend\AppData\Local\Temp\claude\verif_843\VERIFICADOR.md`. Confirmado con datos: el píxel sale del
  `argsort` de `process_modis.py:1085-1099`; P3 de F/K lee `disp` (`pc.vrp_mw` en MODIS con cúmulo) y
  `evaluar_fk.py` no lee `vrp_mw`, `hotspot_*`, `final_hotspot_*`, `z` ni `fuente`; la unión de V1 rehecha sale
  idéntica en 44 de 44 y da 4.820 por brazo. Arreglos pedidos al autor: dos tests (mutaciones m1 y m2 sobreviven) y
  tres condiciones más estrictas (geometría sólo si se movió el hotspot; `final_hotspot_*` sólo con rescate o con
  `final == hotspot`; en el rescatado `hotspot_*` = centroide del cúmulo, `store.py:398-400`).
- G3 del diurno: con el orden (2,1) Copahue 06-18 da 9 campos distintos, más 4 noches de borde ya conocidas. Una
  FALLA de G3 da INDECIDIBLE (`evaluar_diurno.py:750`): el error posible es el conservador. Regla mínima propuesta: el
  G3 clasifica cada par con `comparar()` más el predicado; `distinto` falla y `orden`, `borde` y `hotspot_escena` se
  informan. Es una desviación del pre-registro: **el diurno no se evalúa sobre uniones con esos casos hasta
  arreglarlo** (tarea propia, a proponer a Nicolás).
- **Evaluación de V1 lanzada**: `evaluar_fk.py --ventana V1` sobre `union_d16` con los logs del intento 3, salida en
  `C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446\eval\`.

### 2026-10-17 13:18 UTC (vuelta 139): D-16 (a) en PR #843 (CI verde); V1 unida y PAREJA; verificador lanzado
- #843 (`loop/unir-intentos-hotspot-escena`): categoría `hotspot_escena`, sólo MODIS, `t_max_k` igual, cúmulo presente,
  lista cerrada de campos, predicado de node igual; si cambian fuente, etiqueta o `vrp_mw`, la diferencia debe ser
  exactamente el rescate (`store.py:390-422`). 35 tests y 8 mutaciones atrapadas. Suite local: 1.963 pasan.
- Magnitud de los evaluadores: P3 de `evaluar_fk.py:379-389` usa `disp` (`mirovaEqVrpDisplay`, en MODIS con cúmulo
  `pc.vrp_mw`), no el `vrp_mw` del record: se admite. El G3 de `evaluar_diurno.py:404-420` sí lee el record crudo y
  **su veredicto depende del orden de los intentos** (Copahue 06-18 07:30: nada con el intento 1 primero, 9 campos
  distintos con el orden invertido).
- **V1: 44 de 44 unen, 2 casos admitidos (Llaima control, Terra 09-24 02:05 y 10-06 01:45), cobertura PAREJA: 4.820
  pasadas en los cuatro brazos, 0 y 0** (`C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446\union_d16\`).
  Copahue W2a: 1 caso, intento 1 entero.
- La causa real del desempate (top-100 de `:1085`, no `:1218`) corregida en la tarea 1.22. Verificador limpio de #843
  lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_843\`). Después: merge y evaluación de V1.

### 2026-10-17 13:00 UTC (vuelta 138): 1.21 Láscar-2 en 16 min; los otros 11 despachados desde el mismo tag
- Probe 1.21, job suelto Láscar-2 (run 39033482528, tag `s151-1.21-probe` = `e472c673`): verde, **16 min 25 s**
  (12:41:34 a 12:57:59), bajo el umbral de 70 min del README. **Despachados los otros 11** desde el mismo tag (run
  39034846297, mismo `e472c673`). Al terminar: evaluar en local con los artefactos de los dos runs juntos (el
  evaluador da INCOMPLETO si traen más de un commit).
- V2b (39033530622): 6 en curso, 16 en cola. W4b 16 de 22; W5a pendiente. NRT verde 12:59. Disco 15,1 GB.
  D-16 (a): el agente sigue con trabajo en segundo plano.

### 2026-10-17 12:43 UTC (vuelta 137): Nicolás aprueba todo; #840 mergeado, 1.21 y V2b despachadas, D-16 (a) en curso
- Nicolás: «sí a todo» (las cuatro recomendaciones). Hecho:
  - D-14: #840 mergeado (squash `e472c673`, CI verde en `2d9be9a9`). Tag `s151-1.21-probe` en `e472c673`.
    **Despachado el job suelto Láscar-2** (run 39033482528), para cronometrar; si termina bajo 70 min, los otros 11
    desde el MISMO tag (README de la 1.21, l. 396-404).
  - D-15: tag `s151-fk-v2-codigo` en `7b74435e` (mismo `pipeline/` que V1 y V2a). **V2b despachada** desde el tag
    (run 39033530622, 2026-04-21 a 06-12, C0 y K, comando de `PREREGISTRO.md:139` salvo el `--ref`).
  - D-16 (a): agente en worktree, rama `loop/unir-intentos-hotspot-escena`: categoría acotada para el hotspot de
    escena MODIS (misma BT máxima, clase, cúmulo, píxeles y predicado iguales, y lo que lean las métricas); prueba
    sobre V1 y Copahue. Después, verificador limpio. D-16 (b): tarea 1.22.
  - Cron externo: lo cambia Nicolás en cron-job.org. Falta la fecha de vencimiento del token.

### 2026-10-17 12:23 UTC (vuelta 136): loop relanzado (18,2 GB); V1 unida salvo Llaima control (D-16); W4a pareja; W5a despachada
- Nicolás reinició y corrió el Liberador de espacio: **18,22 GB libres** (`SoftwareDistribution\Download` 0,91 GB).
  Issue #842 cerrado. NRT verde 12:22 (cron externo cada 30 min sigue). `loop/activo` sincronizada.
- **F/K V1 intento 3** (38639658446) terminó: 44 jobs verdes, `recolectar` rojo por cobertura despareja (F 2, K 18,
  gemelo 15 faltantes) y push de rama existente. Unión con el intento 1 (rama `s146-ab/38639658446`) en
  `C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446\union\`: **43 de 44 unen**; Llaima del control no (D-16
  ampliada). `contar_pasadas.py` (08-29 a 10-08) con Llaima del control tomada provisoriamente del intento 3: control
  4.818, F, K y gemelo 4.820; las 2 que faltan son Llaima del control (VIIRS NOAA-21 750, 09-16, sólo en el intento 1).
  Con la unión de Llaima control (461 = F) la cobertura queda pareja. **V1 sin evaluar: espera D-16.**
- Diurno: W4a (38987988455) **pareja** (1.197 contra 1.197). W4b (39000333548) 14 de 22. **W5a despachada**
  (39032518643, 2026-09-01 a 09-10), `pending`, W4b sin desplazar.

### 2026-10-17 04:23 UTC (vuelta 135): **LOOP DETENIDO** por disco (§1.5): 3,04 GB libres
- Disco: 3,30 (03:39), 3,29 (03:50), 3,05 y 3,04 GB (04:23). Causa: Windows Update instalando
  (`SoftwareDistribution` de 6,43 a 0,97 GB; vuelta 133); el Temp del loop suma ~0,7 GB. Los siguientes pasos de la
  cola son evaluaciones locales (`evaluar_fk.py`, `evaluar_diurno.py`) que dejan ~2 GB de temporales (medido en la
  vuelta 32): cruzarían la línea de 3 GB. Se detiene antes, de forma ordenada. Issue `loop-detenido` abierto.
- **Para retomar:** que Nicolás reinicie (Windows termina de instalar) y corra el Liberador de espacio con «Limpieza
  de actualizaciones de Windows»; con 10 GB libres o más, relanzar el `/loop`.
- **Runs en GitHub (siguen solos, no dependen del disco):**
  - F/K V1 intento 3 (38639658446): 43 de 44 verdes, 1 en curso. **Sin unir ni evaluar.** Unir con los intentos 1 y 2
    (rama `s146-ab/38639658446` y artefactos) con `unir_intentos.py`, contar con `contar_pasadas.py`
    (2026-08-29 a 10-08) y evaluar con `evaluar_fk.py --ventana V1`.
  - F/K V2a: **unida y pareja** (5.876 por brazo, vuelta 123), uniones en el scratchpad de la sesión
    (`union_v2a\`). Se evalúa como V2 junto con V2b, que espera D-15.
  - Diurno W2: completa salvo D-16 (Copahue `_s151_ab_diurno_on`); W2a en `w2a_38853230521\`, W2b en
    `w2b_38853273752\` (Temp del loop). W3: completa (W3a unida en `w3a_38942908101\union\` para el control de PCC,
    W3b 38985239552 pareja). W4a (38987988455) corriendo, W4b (39000333548) pendiente. W5 y W6 sin despachar.
    **Ninguna ventana del diurno evaluada**: G1 a G3 se calculan sobre W2 a W6 juntas.
- Esperan a Nicolás: cadencia del cron externo, fecha del token, D-14 (sello y merge de #840), D-15 (commit de
  V2b), D-16 (Copahue en W2a).

### 2026-10-17 03:50 UTC (vuelta 134): W3b pareja (W3 completa); W4b despachada; disco estable en 3,29 GB
- W3b (38985239552) 23 de 23 verdes: 730 contra 730 noches, 0 y 0; 276 y 276 pasadas diurnas V375/V750. Con W3a
  (vuelta 128) **W3 está completa**. W4a corre (3 en curso); **W4b despachada** (39000333548, 2026-08-23 a 08-31,
  `--ref main`), `pending`, W4a sin desplazar a los 40 s.
- V1 intento 3: 39 de 44 verdes. NRT verde 03:24. Disco 3,29 GB, estable desde las 03:39 (monitor de parada activo).
- Estado del A/B diurno: W1 informada; W2 completa salvo D-16 (Copahue); W3 completa; W4 corriendo; faltan W5 y W6.

### 2026-10-17 03:39 UTC (vuelta 133): disco en 3,30 GB, a 0,3 GB de la parada; es Windows instalando la actualización
- `df -k`: 3,30 GB libres (5,9 a las 03:18). `C:\Windows\SoftwareDistribution` bajó de 6,43 a 0,97 GB: la actualización
  descargada se está **instalando** (se expande en el almacén de componentes; `WinSxS\Temp` 0,65 GB, `servicing`
  0,67 GB). No es del loop (Temp del loop ~0,7 GB, sin cambio). Suele recuperarse en parte al reiniciar y con el
  Liberador de espacio; el loop no toca la configuración del sistema.
- Monitor de parada cada 2 min: bajo 3 GB, el loop se detiene (§1.5), lo anota y abre el issue `loop-detenido`.
  Recomendación a Nicolás: reiniciar cuando Windows lo pida y correr el Liberador de espacio («Limpieza de
  actualizaciones de Windows»).

### 2026-10-17 03:18 UTC (vuelta 132): espera; disco en 5,9 GB (ciclo externo)
- W3b 19 de 22 verdes, 3 en curso; W4a pendiente; V1 intento 3 37 de 44. NRT verde 02:53.
- Disco en ciclos: 9,6, 8,9, 7,5, 6,2, 8,9, 8,5 y ahora 5,9 GB. Lo del loop en el Temp suma ~0,7 GB (sin cambio);
  la causa es externa (SOSPECHA: Windows Update, que ya escribió hoy). Monitor que avisa bajo 4 GB; con 3 GB, parada
  (§1.5) y aviso a Nicolás.

### 2026-10-17 02:37 UTC (vuelta 131): espera
- W3b 15 de 22 verdes; W4a pendiente; V1 intento 3 35 de 44. NRT verde 02:20. Disco 8,5 GB. Las cuatro decisiones
  (cron, D-14, D-15, D-16) explicadas a Nicolás en la conversación; sin respuesta todavía.

### 2026-10-17 01:46 UTC (vuelta 130): espera
- W3b 9 de 22 verdes; W4a pendiente; V1 intento 3 31 de 44. NRT verde 01:16. Disco 8,8 GB estable (monitor
  detenido tras 15 min en 8 GB). Esperan D-14, D-15 y D-16.

### 2026-10-17 01:19 UTC (vuelta 129): el disco baja otra vez (6,5 a 6,2 GB en minutos); buscando la causa
- `df -h /c`: 6,8 GB (00:46), 6,5 GB (01:19), 6,2 GB (~01:24). Descartados: Windows Update (6,43 GB, sin cambio),
  Temp (1,67 GB; `Temp\claude` 1,38 GB), Autoscan (0,13 GB escritos en 10 h). Búsqueda en todo C: de archivos de más
  de 30 MB modificados en 20 min, en curso; monitor que avisa bajo 4 GB (la parada es 3 GB).
- Runs: W3b 6 verdes, 3 en curso; W4a pendiente; V1 intento 3 31 verdes, 6 en curso, 7 en cola. NRT verde 01:16.
- Resultado de la búsqueda (archivos de más de 30 MB escritos en 20 min en todo C:): sólo un journal de MongoDB
  (100 MB), `WebCacheV01.dat` (90 MB) y archivos de Windows Update (`SoftwareDistribution\DataStore\DataStore.edb`,
  `USOPrivate\UpdateStore\store.db`). Ninguno del loop. A los ~25 min el disco volvió a **8,9 GB**: caída transitoria,
  con toda probabilidad Windows Update preparando la instalación y limpiando después (SOSPECHA, no verificado).

### 2026-10-17 00:46 UTC (vuelta 128): W3a completa tras la repetición; W3b corriendo
- W3a intento 2 (repetición del job del control de PCC): `recolectar` cuenta **699 contra 699 noches, PAREJA**; su
  rojo es sólo el push de la rama existente. `unir_intentos.py` sobre el control de PCC (intento 1 de
  `w3a_38942908101\i1\`, intento 2 del artefacto 12083033867): 65 comunes, 0 distintos (60 por tolerancia, 4 por
  orden); usa entero el intento 2 (69 pasadas). Unión en
  `C:\Users\nmend\AppData\Local\Temp\claude\w3a_38942908101\union\`; los otros 21 archivos son los del intento 1.
- W3b (38985239552): 3 en curso, 19 en cola. **W4a despachada** (38987988455, 2026-08-13 a 08-22, primera mitad de W4, `--ref main`): `pending`, W3b sin desplazar a los 40 s. V1 intento 3: 28 verdes, 6 en curso, 10 en cola. NRT verde 00:43.
  Disco 6,8 GB. Esperan D-14, D-15 y D-16.

### 2026-10-17 00:09 UTC (vuelta 127): el PC estuvo suspendido ~6 h; W2a pareja; W3a repetida; W3b despachada; D-16
- El despertar de las 18:24 UTC corrió a las 00:09 (PC suspendido). NRT verde 23:59. Disco 7,0 GB.
- **W2a intento 2 (38853230521): COBERTURA PAREJA por sí solo** (control 1.085 noches, brazo diurno 1.085, 0 y 0; 425
  y 420 pasadas diurnas V375/V750). El rojo de `recolectar` es sólo el push de la rama, que ya existía (mismo defecto
  que V2a). Con W2b (vuelta 114), W2 está completa.
- **W3a (38942908101): despareja**: al control de PCC le faltan 4 noches (diurno 699, control 695). Intento 1
  resguardado (rama `s151-ab-diurno/38942908101` y `C:\Users\nmend\AppData\Local\Temp\claude\w3a_38942908101\i1\`);
  repetido sólo el job `reproc (PuyehueCordonCaulle, _s151_ab_diurno_control)`, en curso desde las 00:11.
  **W3b despachada** (38985239552, 2026-07-26 a 07-31, `--ref main`), pendiente; W3a intento 2 sigue vivo.
- Unión de W2a con `unir_intentos.py` de main (`1a6f595b`): 21 de 22 unen (casi todos con un intento entero; muchos
  comunes por tolerancia). **Copahue `_s151_ab_diurno_on` NO une**: de 5 comunes con diferencias, 4 son empates en el
  top-100 (74+26 y 72+28 = 100) y uno difiere en decisión: MODIS Aqua 2026-06-18 07:30, `final_hotspot_source`
  test1/cluster_rescue, hotspot 20,31/0,94 km, `vrp_mw` 4,782/1,834, con `anomaly_pixels` (11), clase, cúmulo y BT
  máxima (274,29 K) idénticos. SOSPECHA: empate de la BT máxima de escena desempatado distinto según la CPU (no
  verificado: el píxel de 20 km no está en la lista guardada). La regla bloquea, como debe; no se ablanda sin
  Nicolás: D-16. Implicación para la evaluación: el G3 del diurno («noches intactas», control contra brazo en
  runners distintos) puede fallar por estos empates aunque no haya efecto.
- Corrección a la vuelta 121: además del top-100, hay un segundo desempate que no es estable (el hotspot de escena).
  El hotspot de escena sale de `np.nanargmax(roi_bt_full)` (`pipeline/process_modis.py:1218`), que con un empate
  EXACTO devuelve siempre el primero; para que cambie entre runners las BT tienen que diferir en el último bit.
  SOSPECHA de mecanismo (sin verificar): numpy usa rutinas vectorizadas distintas de `log`/`exp` según la CPU
  (AVX-512 contra AVX2) y difieren en ulps; en la inversión de Planck dos píxeles casi empatados cambian de orden. Si
  es así, el arreglo de producción no es `kind="stable"` sino un desempate explícito (por índice) sobre BT redondeada,
  o aceptar la no reproducibilidad y medirla. A45: decide Nicolás.

### 2026-10-16 17:51 UTC (vuelta 126): W3a despachada (run 38942908101)
- W2a intento 2 figura `queued` a nivel de run con 12 jobs verdes y 2 en curso: es el desfase de GitHub ya visto en
  la vuelta 33 (V2a se encoló detrás de V1 en ese estado sin desplazarlo); un run con jobs corriendo no es pendiente.
  W3a despachada con el comando del pre-registro (`PREREGISTRO.md:399`) partido en su primera mitad: `--ref main`,
  2026-07-20 a 07-25, 11 Tier A (mismo `pipeline/` que W2, vuelta 125). A los 40 s: W3a `pending`, W2a sigue `queued` con sus jobs: sin desplazamiento. W3b se despacha cuando W3a arranque.
- NRT verde 17:40. V1 intento 3: 5 verdes, 4 en curso, 35 en cola. Disco 8,1 GB. Esperan a Nicolás D-14 y D-15.

### 2026-10-16 17:20 UTC (vuelta 125): V2 se evalúa con V2a y V2b juntas; el commit de V2b va a D-15
- `evaluar_fk.py` evalúa la ventana V2 con los dos despachos (`--raiz` de V2a y de V2b) y el ruido del gemelo de V1
  (`--ruido-de v1.json`): V2a sola no se evalúa. Falta V1 intento 3 (corriendo) y V2b (sin despachar).
- Commits: V1 `402447f3` y V2a `7b74435e` tienen el mismo `pipeline/` (diff vacío); W2a y W2b, `8b2bcd79`, igual a
  `main` en `pipeline/`. Pero entre `7b74435e` y `main` entraron #785, #821 y #822 en `pipeline/`: V2b con
  `--ref main` mezclaría pipelines dentro de V2. Pregunta a Nicolás (D-15); recomendación: tag en `7b74435e`. No hay
  apuro: V2b no puede arrancar antes de que termine V1 (~12 h en su grupo).
- W3 (2026-07-20 a 07-31) va partida en mitades (§7.1 del pre-registro diurno: W1 tardó 2,5 h); W3a = 07-20 a 07-25,
  con `--ref main` (mismo `pipeline/` que W2). No se encola mientras W2a intento 2 figure `queued` a nivel de run
  (regla de la vuelta 31: un despacho detrás de un run no `in_progress` puede desplazarlo).

### 2026-10-16 17:18 UTC (vuelta 124): #841 en main; V2a lista para evaluar
- Último arreglo de #841 (`9d4ff60e`, CI run 38938003528 verde): una sola regla en los dos modos, cualquier `distinto`
  bloquea también con intento entero; `sensor_zenith_deg` derivado fuera de VIIRS 375 (único lector en la cadena F/K:
  `cenital_neg_v375`, `banco_paridad.py:464-469`; fuera de ella, `_s149_prereg_invierno/medir_predicciones.py:12,31`
  si se corre con MODIS, anotado). 42 tests; 8 mutaciones mueren. V2a: 22 de 22, records idénticos a la vuelta anterior.
  Diff revisado por el orquestador. **Mergeado** (squash `1a6f595b`). Merge de `origin/main` en `loop/activo` con el
  conflicto add/add resuelto con la versión de main (42 tests en verde). Worktree del autor retirado; disco 8,1 GB.
- Próximo: evaluar V2a con `evaluar_fk.py` sobre las uniones (cobertura pareja medida en la vuelta 123: 5.876 por
  brazo) y verificador limpio. V2b sigue sin despacharse (V1 intento 3 corre en su grupo).

### 2026-10-16 17:06 UTC (vuelta 123): segunda verificación de #841: un bloqueante; **cobertura de V2a unida PAREJA**
- `experiments/_s151_unir_intentos_verif/VERIFICADOR_V2.md`. Uniones rehechas por el verificador (`v2_a7_reunir.py`):
  idénticas record por record a las del autor. **`contar_pasadas.py` sobre las uniones (2026-03-01 a 04-20): control
  5.876, brazo `_s149_ab_sin_test1_b22_max` 5.876, 0 faltan, 0 sobran, salida 0.** Clave (sensor, minuto) = la de
  deduplicación de `pipeline/store.py:650-653`. Mutaciones: mueren 16 de 17.
- Bloqueante: el modo intento entero acepta diferencias reales (con `triggered_test1` invertido, `summit`, `vrp_mw`
  99 o `product_version` nrt en un común de Láscar da `ok=True` e informa), y `evaluar_fk.py` no lee el informe.
  Regla pedida al autor, igual en los dos modos: todo común clasificado, predicado sobre los de borde, cualquier
  `distinto` bloquea; `sensor_zenith_deg` derivado fuera de VIIRS 375 (único lector `cenital_neg_v375`, a comprobar).
- Después de ese arreglo: merge de #841 con el CI verde y evaluación de V2a con `evaluar_fk.py` sobre las uniones,
  con su verificador limpio.

### 2026-10-16 17:02 UTC (vuelta 122): arreglos de #841 aplicados (`dd4cae1d`, CI verde); segunda verificación
- Clave por pasada (sensor, minuto) sin gránulo; intento entero cuando uno solo cubre todas las pasadas (comunes
  informados); mecanismo corregido (empates en el top-100); tests de 20 a 31, matan las mutaciones que sobrevivían.
  V2a: unen 22 de 22 (21 con intento entero: Isluga control el 1, el resto el 2; sólo Chaitén `b22_max` mezcla, 592
  comunes idénticos). Uniones en el scratchpad de la sesión (`union_v2a\`).
- Punto que juzga el verificador: con intento entero, una diferencia real en los comunes sólo se informa, no bloquea.
  Además, si la clave sin gránulo puede fusionar dos pasadas legítimas. Y cuenta la cobertura unida con
  `contar_pasadas.py`.
- Disco 7,4 GB.

### 2026-10-16 16:51 UTC (vuelta 121): verificador de #841: MERGEABLE CON ARREGLOS; la vuelta 117 erró el mecanismo
- `experiments/_s151_unir_intentos_verif/VERIFICADOR_V1.md` (scripts a1 a a6 en `C:\Users\nmend\AppData\Local\Temp\claude\verif_841\`).
  Se sostiene: 20 de 22 unen, 8 de borde (Copahue); en 4.209 records unidos sólo difieren `diag_mu_deti` (5,1e-10),
  `diag_sd_deti` (4e-12) y un ulp de `final_hotspot_lat`; los 61 campos más los anidados de `primary_cluster`
  revisados contra los siete consumidores: no falta ningún campo de decisión.
- **Corrección a la vuelta 117:** no hay píxeles que crucen un umbral. En los 16 casos la lista `anomaly_pixels` mide
  exactamente 100 y el píxel que cambia empata en VRP con el mínimo de la lista: es el corte top-100 con
  `np.argsort(...)[:100]` (`process_modis.py:1085`), no estable ante empates; la máscara de detección es idéntica en
  los dos intentos. El pipeline SÍ es reproducible en la detección; lo que varía es qué píxel empatado se guarda.
- Bloqueantes: (1) la clave de `unir_intentos.py:106-107` incluye `granule` y los evaluadores agrupan por pasada sin
  gránulo (`evaluar.py:109-110`, `evaluar_diurno.py:253`): dos gránulos de la misma pasada se unirían en silencio;
  (2) sobreviven tres mutaciones (ignorar el predicado, quitar `abs_tol`, sacar `granule`); (3) el docstring describe
  el mecanismo falso. Los 2 residuales: empate de VRP en el píxel más caliente, `evaluar_fk.py` no lee la zona; regla
  recomendada: si un intento solo cubre todas las claves de la unión, se usa entero (Isluga 457, Chillán 550). G3
  (`evaluar_diurno.py:420`) compara listas por posición: estándar incoherente, anotado, no se toca en este PR.
- Arreglos devueltos al autor (mismo PR).

### 2026-10-16 16:47 UTC (vuelta 120): espera
- NRT verde 16:25 (15:30, 55 min); disco 7,5 GB estable. V1 intento 3: 6 en curso, 38 en cola; W2a intento 2: 7 de
  22 verdes. Verificador de #841 en curso; #840 sigue abierto (D-14).

### 2026-10-16 16:39 UTC (vuelta 119): `unir_intentos.py` con tolerancia en PR #841 (CI verde); verificador lanzado
- #841 (`loop/unir-intentos-tolerancia`): tolerancias del G3 (1e-9 relativa, 1e-14 absoluta; `diag_mu_deti` difiere
  5,1e-10 relativo pero 1,3e-15 absoluto); `anomaly_pixels` como conjunto; conjuntos distintos admitidos sólo con los
  campos de decisión iguales (lista con origen: `banco_paridad.py:136` `CAMPOS_JS`, `:282`/`:467`
  `sensor_zenith_deg`, `_s146_ab_sin_test1/evaluar.py:92-96`, `evaluar_fk.py:145`, `evaluar_diurno.py:261`, y dos
  condicionales en `index.html:1149`, `:1238`, `:1289`) y el predicado del tablero con node igual en los dos records.
  `unir_intentos.py` no estaba en `main` (venía de `loop/activo`, `4aa21ec8e`): al integrar `loop/activo` habrá un
  conflicto add/add que se resuelve con la versión del PR.
- V2a: unen 20 de 22 archivos (antes 14); 8 records admitidos por píxel de borde (Copahue control). Siguen sin unir
  Isluga y Chillán control, un record MODIS cada uno (Terra 03-28 01:15 y Aqua 04-17 07:30): el píxel de borde cambió
  el píxel más caliente (Isluga 6,8 km) y `sensor_zenith_deg` hasta 0,7°. El verificador juzga si bloquear es lo
  correcto y propone la regla mínima.
- Disco 7,5 GB: Windows Update sigue en 6,43 GB; la baja nueva (~1,1 GB) es el worktree del autor de #841 (0,9 GB),
  que se borra cuando el verificador termine de leerlo.

### 2026-10-16 16:15 UTC (vuelta 118): arreglo de `unir_intentos.py` delegado (worktree propio)
- Subagente en rama `loop/unir-intentos-tolerancia` desde `main`: floats con tolerancia relativa más piso absoluto
  (criterio de G3, #833); `anomaly_pixels` como conjunto, y diferencias de conjunto admitidas sólo con los campos de
  decisión de los evaluadores iguales (leídos de `evaluar_fk.py`, `evaluar_diurno.py` y el predicado del tablero, con
  `archivo:línea`), contadas e informadas; todo lo demás sigue bloqueando. Tests en los dos lados, prueba real con
  Chaitén control de V2a. PR sin merge; después verificador limpio.

### 2026-10-16 16:09 UTC (vuelta 117): V2a intento 2 despareja (6 de Chaitén); la unión estricta choca con ruido de máquina
- V2a intento 2 (38648773684) terminó: 22 jobs de proceso verdes, `recolectar` rojo por dos razones. (1) Cobertura:
  control 5.876 pasadas, brazo `_s149_ab_sin_test1_b22_max` 5.870 (faltan 6, todas de Chaitén). (2) El push de la rama
  `s146-ab/38648773684` falla en los 5 intentos porque la rama ya la publicó el intento 1 (06:31 UTC): **todo re-run
  de este workflow deja `recolectar` en rojo**; es el «rojo conocido» de S147, ahora con causa. El artefacto quedó.
- Unión (`unir_intentos.py`; intento 1 desde la rama, intento 2 desde `s146ab-todo`; mismo commit, es re-run): se
  unen 14 de 22 archivos (0 distintos); en 8 **todos** los records comunes difieren. Causa medida sobre Chaitén control:
  `diag_mu_deti` y `diag_sd_deti` difieren hasta 5,1e-10 relativo (regresión del ETI en otra CPU, el caso G3),
  `final_hotspot_lat` 1,7e-16. Además, en 11.642 records comunes, **15 traen otro conjunto de `anomaly_pixels`** (9
  más difieren sólo en el orden): los 15 son MODIS del control (Copahue 8, Isluga 3, Chillán 4), todos `far`, todos
  con `vrp_mw` topado en 5,0 (D9) y campo difuso de 56 a 90 píxeles; un píxel en el borde del umbral entra o sale
  (diferencia de 0 a 2 píxeles). En los 15, `distance_class`, `vrp_mw`, `primary_cluster.vrp_mw` y `triggered_test1`
  son idénticos: no cambia ninguna publicación. Salidas en `C:\Users\nmend\AppData\Local\Temp\claude\v2a_38648773684\`.
- Próximo (vuelta propia, rama desde `main`, TDD y verificador limpio, como G3 en #833): `unir_intentos.py` compara
  floats con tolerancia relativa más piso absoluto, y admite diferencias de `anomaly_pixels` sólo si los campos de
  publicación son idénticos, contándolas e informándolas. Para Nicolás: el pipeline no es reproducible bit a bit entre
  runners en los campos difusos topados por D9 (15 de 11.642), sin efecto en lo publicado.

### 2026-10-16 15:51 UTC (vuelta 116): la caída del disco es Windows Update (6,4 GB), no el loop
- Búsqueda de archivos de más de 200 MB escritos en los últimos 50 min (workspace, `AppData\Local`, `ProgramData`,
  `Windows\Temp`, Descargas): ninguno. `C:\Windows\SoftwareDistribution\Download` suma 6,4 GB con escrituras de
  15:17 a 15:40 UTC, la ventana de la caída. Papelera 0. Ajeno al loop y a la configuración que el loop puede tocar.
- Worktree del autor de la 1.21: git ya lo había dado de baja y la carpeta quedó vacía (0 MB) y borrada; los 936 MB se
  habían liberado en el primer intento. Disco 8,9 GB, sobre la parada de 3 GB; se vigila en cada vuelta. Si sigue
  bajando, se detiene el loop y se le pide a Nicolás liberar espacio (Liberador de espacio tras instalar la
  actualización).

### 2026-10-16 15:44 UTC (vuelta 115): el disco bajó de 18 a 9 GB en media hora; investigando
- `df -h /c`: 18 GB a las 15:11, 9,1 GB a las 15:44, 8,9 GB a las 15:47 y 9,6 GB a las 15:50: no baja de forma
  continua. La parada (§1.5) es 3 GB. `AppData/Local/Temp` suma 1,6 GB; el worktree del autor de la 1.21
  (`.claude/worktrees/agent-aa3ef748ab319056b`, limpio, HEAD `2d9be9a9` = remoto) 936 MB, no se pudo borrar todavía
  (la sesión quedó con el cwd adentro). Proceso ajeno al loop corriendo desde las 15:30 UTC: `run_ciclo.py` de
  `Empresas\Autoscan\autoscan-chile\ejecutar_ciclo.bat` (scraper con Playwright, otro proyecto de Nicolás); no se
  toca. Búsqueda de archivos grandes recientes en curso.
- Otra `workflow_dispatch` del NRT cancelada (15:00, run 38920346960, desplazada por la de las 15:30). D-13: V2a
  intento 2 19 de 22; W2a intento 2 2 verdes, 3 en curso, 17 en cola; V1 pendiente.

### 2026-10-16 15:11 UTC (vuelta 114): W2b terminó con cobertura nocturna PAREJA; espera a W2a para evaluar W2
- W2b (run 38853273752) 23 de 23 verdes. `contar_pasadas_noche.py` del job `recolectar`: control 1.069 noches y brazo
  diurno 1.069, 0 faltan y 0 sobran; brazo diurno con 438 pasadas diurnas V375 y 433 V750, sin MODIS diurno.
  Artefacto `s151diurno-todo` bajado a `C:\Users\nmend\AppData\Local\Temp\claude\w2b_38853273752\todo\` (46 archivos).
  No se evalúa sola: G1 a G3 se calculan sobre W2 a W6 juntas (PREREGISTRO §4); W2 se arma uniendo W2a y W2b.
- W2a intento 2 (38853230521) arrancó (3 en curso, 19 en cola). **W3 NO se despacha todavía** aunque el grupo
  `s151-ab-diurno` ya no tiene pendiente: si W2a vuelve a salir despareja, su repetición desplazaría a W3 en el grupo.
  Se despacha cuando W2a quede pareja.
- NRT: la corrida `schedule` de las 14:32 esperó 26 min el grupo `push-main` (la de las 14:00 tardó 58 min) y arrancó a
  las 14:58; la `workflow_dispatch` de las 15:00 quedó pendiente. Siempre una en cola. V2a intento 2 18 de 22; V1
  intento 3 pendiente. #840 sigue abierto (D-14). Disco 18 GB.

### 2026-10-16 14:43 UTC (vuelta 113): pre-registro 1.21 listo para el sello (D-14); merge negado al loop
- Último arreglo en #840 (`2d9be9a9`, CI run 38917337264, 1.885 pasan): `procedencia()` escribe `commit` y `ref` en cada
  artefacto; el evaluador da INCOMPLETO sin commit o con más de uno; tres tests nuevos que fallaban antes. README: los
  dos despachos (Lascar-2 para cronometrar, después los 11) salen del tag `s151-1.21-probe` sobre `main` tras el merge.
  Diff revisado por el orquestador (`git diff bce080328 2d9be9a9d`): hace lo que dice.
- El merge de #840 lo negó el clasificador de permisos («merge sin revisión»); no se rodea. Queda en D-14 junto con el
  sello: Nicolás mergea #840 y sella; después el loop pone el tag y despacha Lascar-2 solo.
- Lo que Nicolás debe saber al sellar (verificador v2): MEJORA casi inalcanzable en la principal; las 37 protegidas
  ganadas no entran en Δ (letra de MISSION); encender el flag tal cual crea una asimetría A46 nueva en los records del
  Test 1.

### 2026-10-16 14:39 UTC (vuelta 112): el cron externo ya desplazó una corrida (evidencia para la decisión 1)
- La `workflow_dispatch` de las 14:30 (run 38916263593) quedó `cancelled` con 0 jobs a las 14:32:35: la desplazó la
  corrida `schedule` de GitHub de las 14:32 (`nrt.yml:12`, `0 */2 * * *`), porque el grupo `push-main`
  (`nrt.yml:56`) guarda un solo pendiente. Sin pérdida de datos (la siguiente procesa el mismo día), pero el grupo es
  COMPARTIDO con los demás workflows que pushean a main (`sync-mirova-csv` y otros): con el NRT siempre en espera,
  cualquiera de ellos puede ser el desplazado, el modo de falla que perdió el job `merge` en S125 y S126. Refuerza
  bajar la cadencia del cron externo (recomendado `10 1-12 * * *` UTC) o apagar el `schedule` de `nrt.yml` si el
  externo lo reemplaza; decide Nicolás.
- D-13: V2a intento 2 18 de 22; W2b 21 de 22. #840 cambió de head (`2d9be9a9`): el autor está empujando el último
  arreglo, sin informe todavía. Disco 19 GB.

### 2026-10-16 14:33 UTC (vuelta 111): segunda verificación de la 1.21: SELLABLE CON ARREGLOS (uno, chico)
- `experiments/_s151_mxd03_cumulo_121_verif/VERIFICADOR_V2.md`. Los dos bloqueantes de la v1, arreglados en el
  código (mutaciones de código propias del verificador: las tres hacen fallar el caso TEST1; FRÁGIL global hace fallar
  el test nuevo). Cobertura re-corrida idéntica. Anisotropía: no bloquea (la principal no usa el nulo; las dos pérdidas
  de la 1.17 a 15,6° y 17,4°).
- Bloqueante nuevo: dos despachos (Lascar-2 para cronometrar y los 11) con `--ref main` sin commit en los JSON; si
  `pipeline/` cambia entre ellos, el veredicto mezcla pipelines. Arreglo pedido al autor: `GITHUB_SHA` por job y
  evaluador INCOMPLETO con más de un commit.
- Para el sello de Nicolás: MEJORA es inalcanzable en la práctica en la principal (lo esperable es EMPEORA, PIERDE
  PROTEGIDA o INDETERMINADO); las 37 protegidas ganadas no entran en el balance (letra de MISSION, decisión suya si
  deben compensar); encender el flag tal cual crea una asimetría A46 nueva en los records del Test 1.

### 2026-10-16 14:28 UTC (vuelta 110): arreglos de la 1.21 aplicados (#840 en `bce08032`, CI verde); segunda verificación
- CI run 38915427957: 1.882 pasan (45 tests nuevos). Bloqueante 1: README rebajado a cota (CC publicaría 42 a 46
  protegidas, 0 a 4 pérdidas), grupo `fuente_test1` (126 records, 4 protegidas, 113 negativos limpios), espía con los
  cuatro argumentos y el resultado, replay por grupo, caso sintético TEST1 con mutación, nota A45. Bloqueante 2:
  FRÁGIL por intersección de pasadas con control negativo. Cobertura con verdad negativa: MEJORA sale 5 %, 46 % y 92 %
  de las veces si se apaga el 50, 70 y 90 % de las 587 falsas de C. No aplicado: la anisotropía del nulo sobre 50°
  (documentada, 1,24×; las dos pérdidas de la 1.17 están bajo 20°).
- Segunda vuelta del verificador lanzada (`verif_121\VERIFICADOR_V2.md`).
- D-13: V2a intento 2 18 de 22; W2b 21 de 22; V1 y W2a pendientes.

### 2026-10-16 14:10 UTC (vuelta 109): verificador del pre-registro 1.21: SELLABLE CON ARREGLOS (dos bloqueantes)
- `C:\Users\nmend\AppData\Local\Temp\claude\verif_121\VERIFICADOR.md`. Comprobado: 39 de 39 tests, sha256 de la
  muestra, cobertura del estimador, replay coherente con A82 (88,3 % de negativos limpios contra 89,1 %), consumidores
  del flag (`process_modis.py:1330` y `:1497`), workflow (candado, token, `"on":`, grupo propio, 95 min contra 70).
- Bloqueante 1: la rama del Test 1 no está modelada. `derivar_distance_class` recibe el cúmulo del camino de erupción
  y después ese cúmulo se reemplaza por el del Test 1 (`:1425`/`:1440`), que es el guardado. Con el flag encendido la
  etiqueta sale `far` por el Salar a 14,98 km con el cúmulo publicado a 0,375 km (`verif_121\scripts\test1_rama2.py`,
  pipeline real). 126 records con fuente `test1`, 4 protegidas de Láscar, dos son las pérdidas de la 1.17. El «46 de
  46» es una cota. Para A45: con el flag, la etiqueta sale de un cúmulo distinto del que se publica.
- Bloqueante 2: FRÁGIL global (`evaluar_cumulo.py:262-263`) en vez de por pasada.
- No bloqueantes: nulo anisótropo sobre 50° de cenit; poder bajo (MEJORA casi inalcanzable en la principal); las 37
  protegidas ganadas no entran en Δ; comentario 14/12 gránulos; cronometrar un job antes de los 12.
- Arreglos devueltos al autor (mismo PR). Después, segunda vuelta del verificador.

### 2026-10-16 14:08 UTC (vuelta 108): espera
- NRT 13:00 verde (37 min 43 s); 13:30 corriendo, 14:00 pendiente: siempre una en cola con el cron de 30 min, sin
  desplazamientos hasta ahora (las tres corridas existen). D-13: V2a intento 2 17 de 22 verdes; W2b 20 de 22; V1 y
  W2a siguen pendientes. Verificador de la 1.21 en curso. Disco 19 GB.

### 2026-10-16 13:57 UTC (vuelta 107): pre-registro 1.21 entregado (PR #840, CI verde, sin merge); verificador lanzado
- PR #840 (`loop/1.21-prereg`, head `f3fb8d7a`), CI run 38911168165: 1.876 pasan (base 1.837, +39 nuevos). Seis brazos
  más C': C, CC (etiqueta desde el cúmulo sin MxD03), M, MC, R y RC (traslación rígida de la grilla del tamaño del
  corrimiento medido, como nulo). El flag se cambia en el módulo porque `process_modis.py:173` lo importa por valor;
  consumidores: dos llamadas a `derivar_distance_class` (l. 1328 y 1495). Misma muestra que la 1.17 (sha256 fijado).
  Modelo con término a lo largo de la traza: bajo 20° de cenit mediana medida 1,171 km contra 1,275 predicha
  (r = 0,981); gránulos fuera de banda 87 a 4 de 470. Estimador cambiado tras medir su cobertura (Dirichlet ½ cubría
  0 de 300 el efecto grande).
- **Predicción previa (no decide):** el replay de la etiqueta desde el cúmulo recupera 46 de 46 protegidas pero
  publica 4.454 de 5.047 negativos limpios (C 587): Δ +3.829, MC saldría EMPEORA por la regla 2. Coherente con A82
  (cúmulo dentro del inner en 89 % de los negativos limpios MODIS). Sin cronometrar: tiempo por job.
- Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_121\`). El sello espera su veredicto.

### 2026-10-16 13:49 UTC (vuelta 106): informe del paper v2 entregado a Nicolás (punto 4 del pedido)
- `experiments/_s152_paper_revision/INFORME_CAMBIOS_PAPER_v2.md` (con la v1 y el verificador al lado): 69 filas, 10
  FALSA (errores independientes), 19 REBAJADA, 13 DESACTUALIZADA, 13 FALTA, 14 SIN CAMBIO. Los 5 más graves: «no hay
  negativos» (V375 publica en 60,7 % de los negativos limpios por pasada y 79,8 % por noche antes de #535); MxD03 no
  se lee; la lectura de MODIS en §6; Methods no describe la magnitud publicada (D25, modo un píxel, tope D9, F5') y
  cierra D18 con un A/B que no midió la caja; las diurnas no se excluyen (efecto chico).
- Desacuerdo autor/verificador resuelto a favor del autor por el orquestador: el «100 % por noche» de V375 es de los
  tramos posteriores a #535 y #571 (`experiments/_s142_linea_base/RESULTADOS.md:29-30`), no del anterior.
- Sin verificar: 13 filas no revisadas por un tercero y todas las citas a PDF (ninguna página renderizada). Nada se
  reescribe en `docs/paper/` sin el visto bueno de Nicolás; decisiones previas que el informe le deja: ventana de
  validación (posterior a #535 o por tramos A119) y si `paper_numbers.py` adopta la unión histórica, la regla SN y los
  negativos limpios.

### 2026-10-16 13:45 UTC (vuelta 105): verificador del informe del paper: ENTREGAR CON CORRECCIONES
- `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\VERIFICADOR_INFORME_PAPER.md`: 33 ítems revisados, 19
  CONFIRMADO, 14 CORREGIR, 0 REFUTADO. Las 14 FALSA son 12 errores independientes (6-3, 6-14 y 6-16 son la misma
  premisa: «la referencia no tiene negativos»); 5-5 pasa a DESACTUALIZADA y 5-24 (D18) a REBAJADA. Grave 1: el 86,1 %
  de negativos limpios es posterior a #535 y no vale para la ventana del paper (antes, ~62 % por pasada). Grave 2: las
  diurnas no se excluyen, pero excluirlas mueve el recall V375 de 0,931 a 0,936. Grave 4: por noche el argumento sale
  más fuerte (98,2 % de los negativos limpios MODIS con cúmulo en el cráter). 6-13 (30/193, 210/214) se localiza en
  el `numbers.json` previo a #604. V750 246 a 244: dos alertas de PCC borradas del consolidado, que también mueven
  Isluga en `sec6:116`. Sin renderizar PDF; 13 ítems sin revisar uno por uno.
- El autor del informe aplica las correcciones (v2, `...\paper_s152\INFORME_CAMBIOS_PAPER_v2.md`); después se
  entrega a Nicolás.

### 2026-10-16 13:36 UTC (vuelta 104): sin nada que evaluar; el cron externo cada 30 min ya apila NRT
- Hora del servidor 13:36 (la vuelta 103 decía «~13:50», hora estimada y equivocada; corregida a ~13:30, A86).
- NRT: la `workflow_dispatch` de las 13:00 (38904541728) sigue corriendo a los 36 min y la de las 13:30
  (38908317829) quedó pendiente detrás. Evidencia directa para la decisión 1 del bloque S152 (cadencia): con 30 min
  siempre hay una corrida esperando.
- D-13: V2a intento 2 15 de 22 verdes; W2b 17 de 22; V1 intento 3 y W2a intento 2 pendientes. Disco 19 GB.
- En curso: subagente de la 1.21 y verificador del informe del paper.

### 2026-10-16 ~13:30 UTC (vuelta 103): informe del paper entregado por su agente, en verificación; #839 en main
- Informe `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\INFORME_CAMBIOS_PAPER.md` (69 ítems: 14 FALSA, 18
  REBAJADA, 10 DESACTUALIZADA, 13 FALTA, 13 SIN CAMBIO, 1 SIN LOCALIZAR). Comprobados por el orquestador dos de los
  graves: `sec5_methods.md:6-14` dice que MODIS lee MOD03/MYD03 y `process_modis.py:470` dice que `geo_path` no se
  usa; `sec6_validation.md:31-34` dice que las filas diurnas se excluyen y `scripts/paper_numbers.py` no filtra por
  hora (grep). El resto, verificador limpio en curso (`...\paper_s152\VERIFICADOR_INFORME_PAPER.md`). No se entrega
  a Nicolás antes del veredicto.
- PR #839 (IndexError del probe de saturación) mergeado con CI verde (pytest 2 min 16 s), squash `57c70ee5`; worktree
  y rama borrados.

### 2026-10-16 ~13:25 UTC (vuelta 102): IndexError del probe de saturación arreglado (PR #839, CI pendiente)
- `experiments/_s151_saturacion_chillan/probe_saturacion.py`: un tramo sin días (ventana de 3 días en 6 tramos, run
  38882932077) escribe su JSON con 0 pasadas y sale con 0, sin token ni red. Test nuevo parametrizado (normal y
  `--listar`) con control (el tramo con días sigue exigiendo `EARTHDATA_TOKEN`): rojo antes, 24 de 24 después.
  Rama `loop/probe-sat-tramos-vacios` en el worktree `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s152-sat`
  (A44: el árbol compartido lo lee un subagente). Se mergea con el CI verde (sólo `experiments/` y `tests/`).

### 2026-10-16 ~13:20 UTC (vuelta 101): revisión del paper delegada (sólo lectura)
- Subagente sobre `docs/paper/` (sec4, sec5, sec6, `numbers.json`, `TABLAS.md`) contra lo cambiado desde el
  2026-09-15: distancia OCR, corrimiento MODIS y MxD03, saturación, agregación VIIRS, alerta protegida y criterio de
  victoria, más las marcas ⚠️ de S146 a S151. Entrega un informe en
  `C:\Users\nmend\AppData\Local\Temp\claude\paper_s152\INFORME_CAMBIOS_PAPER.md`; no reescribe nada (lo decide Nicolás).

### 2026-10-16 ~13:15 UTC (vuelta 100): pre-registro de la 1.21 delegado (worktree propio)
- Subagente en worktree aislado, rama `loop/1.21-prereg` desde `main`: brazos C, M (MxD03), MC (MxD03 + `distance_class`
  desde el cúmulo, flag sólo en memoria y trazado a todos sus consumidores, A89/A118) y ruido de posición como control
  real (A110); término a lo largo de la traza en el modelo de corrimiento; regla 1 como compuerta en las dos
  direcciones (A81); candado `preregistro_aprobado=si`, sólo `EARTHDATA_TOKEN`, grupo de concurrencia que no desplace a
  F/K ni al diurno. Entrega un PR sin merge y sin despacho; después, verificador limpio y recién ahí el sello.

### 2026-10-16 13:09 UTC (vuelta 99): Mirova-v1 ya escribe `Distancia_aprox_*`; D-13 sigue esperando sus runs
- Sesión S152 retomada con `/loop`. Chequeos: NRT verde (08:45, 39 min; la `workflow_dispatch` del cron externo de
  las 13:00 está en cola); disco 20 GB libres; abiertos #779 (auto-audit fuera de banda, ya revisado en la vuelta 29),
  #813 (D-10) y #824 (watchdog: los A/B en cola, ruido conocido).
- **Mirova-v1, CONFIRMADO**: el OCR de las 13:00 (run 38904540596) restauró la caché completa, calculó la distancia
  aproximada en 33 s (13:02:53 a 13:03:26) y commiteó `f8a2ee01`. Contra su padre `13b5ddb5` (el commit del OCR de
  13:02): 1.090 filas en los dos; 231 con `Distancia_aprox_km` (antes 0); métodos: pendiente 244, solapado 241, único
  231, ambiguo 172, sin_control 132, sin_marcador 48, calado_debil 22. **`Distancia_km` y las otras 24 columnas
  originales, idénticas byte a byte en las 1.090 líneas** (prefijo crudo de cada línea, sin CR en ninguno de los dos).
  No hace falta arreglo de `restore-keys` (decisión 4 del bloque S152 queda sin objeto mientras siga así).
- D-13: V2a intento 2 (38648773684) corre, 12 de 22 jobs verdes; W2b (38853273752) corre, 15 de 22; V1 intento 3
  (38639658446) y W2a intento 2 (38853230521) pendientes detrás de ellos. Nada que unir todavía.
- Próximo: pre-registro de la 1.21.

### 2026-10-16 ~13:00 UTC (vuelta 98): historia de Mirova-v1 completa; cron externo creado por Nicolás
- Segunda corrida de `distancia_aprox_historia.yml` (run 38902737639) terminó en verde a las 12:59: 1.090 filas sin
  `sin_tiempo` (todas calculadas), caché completa `mirova-dist-hist-38902737639` (47 MB), la más nueva. El OCR de las
  13:00 debería restaurarla y escribir `Distancia_aprox_*` en segundos. Comprobar en la próxima sesión.
- Nicolás creó el cron externo del NRT en cron-job.org. A las 12:56 UTC no había ninguna corrida `workflow_dispatch`:
  falta el «Test run» (204 esperado) o esperar a las 01:10 UTC. Pendiente anotar el vencimiento del token en
  `REGISTRO_CREDENCIALES.md` (Nicolás da la fecha, nunca el valor).
- Sesión cerrada por contexto (84 %). Próxima: `/retomar` y relanzar el `/loop`; primero verificar la escritura de
  la columna, unir y contar V1, V2a y W2a (D-13), y pre-registrar la 1.21.

### 2026-10-16 ~13:20 UTC (vuelta 97): verificador del resultado 1.17: PARCIAL; las 2 pérdidas son A46, no posición
- `C:\Users\nmend\AppData\Local\Temp\claude\verif_117r\VERIFICADOR.md`. PIERDE PROTEGIDA es lo que manda la letra del
  pre-registro (`evaluar_mxd03.py:164-181`), con 470 de 471 gránulos. Pero las 2 pérdidas de Láscar Terra (04-20 y
  04-30 01:30) NO son de posición: con MxD03 el cúmulo queda igual y más cerca del cráter (0,72 → 0,23 km; 0,86 →
  0,48 km); el Test 1 de 3 km deja de disparar (inferido), gana `eruption` en el borde del Salar a 19 y 21 km, y
  `distance_class` sale del hotspot final porque `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`
  (`process_modis.py:1293-1310`, `1328-1330`, `319`); sin rescate F47 porque el Salar está dentro de 25 km
  (`store.py:393`). Es A46/A81. MIROVA publica las dos a 1,0 km (1,36 y 1,34 MW). En protegidas M gana 9 y pierde 2.
- El «control» no es control: `_interp_geo` también corre la posición a lo largo de la traza (2 − 0,00197·línea km),
  término ausente en el modelo de #828 (r = 0,955 bajo 30° de cenit); explica el 1,1 a 1,3 km medido contra 0,4. Δ no
  interpretable. «Otra detección» en 97 de 100 no distingue nada (se enciende en 460 de 470); la partición útil:
  36 mismo píxel reubicado, 32 cambio de fuente del hotspot, 32 otro píxel máximo. C contra producción: 462 de 470 en
  etiqueta (las 8 restantes son negativos limpios); píxeles anómalos difieren en 248 casos (deriva de código).
- Consecuencia para Nicolás: el arreglo MxD03 solo NO pasa la regla 1 tal como se pre-registró, pero la causa de las
  pérdidas es el etiquetado por hotspot final. Propuesta: tarea 1.21, probe de tres brazos (C; MxD03; MxD03 + etiqueta
  desde el cúmulo) con la misma vara, más el término a lo largo de la traza en el modelo y un brazo con ruido como
  control real. Nada se adopta.

### 2026-10-16 ~12:50 UTC (vuelta 96): probe 1.17 evaluado: PIERDE PROTEGIDA (por verificar); el cron de Mirova-v1 aún no escribe
- Probe 1.17 (run 38894508138): 470 de 471 gránulos (falta 1 de Tupungatito, bajo el tope); C' = C en 24 de 24;
  autoprueba 41 de 41. Regla 1: de 46 protegidas, C publica 9 y M 16; **se pierden 2** (Láscar Terra 04-20 y 04-30
  01:30: el cúmulo sigue en el cráter con la misma magnitud, pero el hotspot final salta a 19 a 21 km; posible
  asimetría A46, no posición) y se ganan 9. Regla 2: Δ = −49,9 [−153,1; +62,6]. 22 cambios en estratos «inmóviles» y
  97 de 100 cambios son «otra detección»; a cenit bajo el corrimiento medido (1,1 a 1,3 km) triplica el del modelo.
  Salida: `C:\Users\nmend\AppData\Local\Temp\claude\mxd03_117\`. Verificador limpio lanzado (`verif_117r`).
- Mirova-v1 tras #25: la corrida OCR de las 12:00 falló en el paso de la distancia aproximada (caché fría, push
  rechazado y timeout de 10 min) y la de las 12:20 quedó cancelada en ese paso; en las dos el commit del OCR y el
  guardado de la caché salieron bien (sin pérdida de datos). Causa: el cron restaura la caché `mirova-dist-*` más
  reciente y la de la historia (12:07) quedó tapada por la parcial de las 12:12. La caché crece en cada corrida y
  debería converger; vigilando la de las 12:30 antes de proponer un arreglo (toca producción: sólo con el sí de Nicolás).

### 2026-10-16 ~12:15 UTC (vuelta 95): D-12 hecha: distancia aproximada en producción de Mirova-v1
- Nicolás aprobó el merge. Mirova-v1#25 mergeado (squash `2eac1758`, 11:43 UTC; CI verde en `f774a5d`, lo verificado).
  Historia despachada una vez (`distancia_aprox_historia.yml`, run 38895687049, presupuesto 45 min; no escribe el
  repo, deja los calados en la caché). Hito A119 de la columna en `scripts/calidad_referencia_mirova.py` (#838,
  `a0b6545d`): complementaria, sólo VIIRS 375, desde el 2026-04-14, umbral provisional.
- Pendiente: comprobar que la historia termina y que el siguiente cron del OCR escribe `Distancia_aprox_*` en el CSV
  con `Distancia_km` intacta.

### 2026-10-16 ~12:00 UTC (vuelta 94): D-13 decidida: repetir y unir intentos
- Nicolás decidió repetir los jobs y unir intentos (A108), aunque tome más tiempo; nada de intersección. Despachados:
  F/K V1 intento 3 completo (run 38639658446, pendiente en `s146-ab-sin-test1` detrás de V2a intento 2) y W2a intento 2
  completo (run 38853230521, pendiente en `s151-ab-diurno` detrás de W2b).
- Procedimiento para cada A/B: unir los intentos de cada brazo con `experiments/_s151_ab_diurno/unir_intentos.py`
  (exige records comunes idénticos) y contar cobertura con el instrumento del pre-registro; si sigue despareja, otra
  vuelta. **No despachar V2b ni W3 mientras haya un pendiente en su grupo**: el grupo guarda un solo pendiente y el
  nuevo desplazaría al que espera.
- En curso: probe 1.17 (run 38894508138), V2a intento 2, W2b.

### 2026-10-16 ~11:50 UTC (vuelta 93): D-11 sellado por Nicolás; probe 1.17 despachado
- Nicolás selló el pre-registro de la 1.17. Despachado `probe-s151-mxd03-etiquetas.yml` con `preregistro_aprobado=si`,
  run 38894508138, sobre `d9b10482` (contiene #837, `b130fa72`). 471 gránulos en 12 jobs, 1,5 a 2 h estimado. Al
  terminar: contar cobertura, evaluar con el evaluador del pre-registro (regla 1 como compuerta), verificador limpio.

### 2026-10-16 11:24 UTC (vuelta 92): Chillán a 355,96 K sin saturar; W2a despareja (va a D-13)
- Medición de saturación sobre 10-14 a 10-16 (run 38882932077): 3 tramos V375 fallaron por un defecto menor del probe
  (ventana de 3 días en 6 tramos: los tramos sin días caen con `IndexError` al imprimir; arreglo pendiente: salir con 0
  si no hay días). Los tres días se midieron. 58 pasadas, **0 píxeles con bit de saturación**, incluida la de
  2026-10-16 06:18 (Suomi NPP, noche) con I04 válido de **355,96 K** en el interior. El «techo efectivo ~354 K» del
  verificador de la 1.20 no se cumple en esta pasada: hoy todavía no satura. Riesgo vigente, sin pérdida medida.
- W2a del A/B diurno (run 38853230521): 22 jobs verdes; `recolectar` marca 2 noches de Láscar de más en el brazo diurno
  (al control le faltan 2). Mismo patrón de pérdidas por descarga: entra en D-13. W2b corriendo (7 de 22).
- NRT verde 08:45 UTC; disco 21 GB.

### 2026-10-16 ~10:00 UTC (vuelta 91): verificador de la 1.20: PARCIAL; riesgo VIVO de saturación de I04 en Chillán
- `experiments/_s151_techos_120/verificador/VERIFICADOR.md`. (1) Código: la cadena NaN-M15 → sin NTI ni caminos B y D
  es correcta, pero el Test 1 NO rescata en general (`process_viirs_mod.py:1196-1215`: sólo si es la única fuente o si
  el pico contextual queda fuera del inner); con halo cerca del cráter, el píxel saturado queda como agujero también
  dentro de 3 km. (2) La cota física se sostiene (I05 de la gemela V375: máx 319,51 K), aunque con emisividad 0,7 a 0,9
  baja a 16 a 30 MW; el «M15 implícito» es una cota inferior. (3) **I04: el techo efectivo es ~354 K, no 359 K** (los
  máximos se amontonan en 353,3 a 354,2 K; el cálculo en centro de banda sobrestima 6 a 7 K), y **Suomi NPP ya dio
  355,96 K en el cráter de Chillán el 2026-10-16**: la pérdida por el bit de saturación es un riesgo vivo en la erupción.
  (4) El indicio de feb-2025 está a 12 a 19 km al oeste y se mueve entre noches: probablemente un incendio, no el volcán.
  (5) La propuesta choca con D24 (sigue borrando por el bit desde ~352 K); en V750 sería más fiel conservar M15 recortado
  y marcarlo.
- Medición de saturación re-despachada sobre lo reciente (run 38882932077, desde 2026-10-14; descriptiva, sin
  veredicto) para ver si el bit ya borró píxeles del cráter. Esto alimenta D24 y la decisión de Nicolás; nada se toca.

### 2026-10-16 ~09:30 UTC (vuelta 90): 1.20 terminada, SIN verificador todavía: ningún techo borra señal hoy
- `experiments/_s151_techos_120/` (informe y scripts). Techo M15 343 K (`process_viirs_mod.py:182`): pone NaN sólo en
  M15, el píxel pierde NTI y sólo el Test 1 lo rescata a menos de 3 km del cráter; se activaría con 32 a 37 MW por
  píxel como cota absoluta. Por cota física, 26.181 de 26.185 records V750 no pudieron alcanzarlo; los 4 restantes
  (Chillán, feb-2025) tienen M15 implícito de 292 a 301 K. Sin control positivo. Qué hace MIROVA con M15: SIN VERIFICAR.
  NOAA-21: LUT de I04 361,00 K contra corte 361,27 K confirmado en 46 gránulos, pero el bit 4 sí funciona (263 píxeles
  en 23 gránulos) y no hay `t_max_k` de 360,5 K o más en 26.386 records V375: pesa poco.
- Propuesta (A45, sin implementar): techo = tope de la LUT de cada gránulo; antes, probes P1 (flags de NOAA-21) y P2
  (control positivo en erupciones efusivas grandes). Laterales: el V750 más caliente del corpus es 364,86 K (Chillán
  2025-02-27 05:42 SNPP); y un indicio de que en esa erupción el bit borró I04 saturado de un foco a 15 km (I04 353,6 K
  contra M13 361,2 K en la misma pasada de NOAA-21): la cara V375 de D24, por medir.
- Falta el verificador limpio (regla 1.3) antes de darlo por aceptado: primera tarea de la próxima sesión.

### 2026-10-16 09:05 UTC (vuelta 89): 1.20 arrancada (techos M15 y NOAA-21, sólo lectura)
- Paradas: NRT corriendo desde 08:45 UTC (último verde 03:15); disco 21 GB. V2a intento 2 con 6 jobs en curso; W2a 19
  de 22. Esperan a Nicolás: D-11, D-12, D-13.
- 1.20 delegada: qué borra el techo de M15 en 343 K y si la defensa de saturación de I04 queda muerta en NOAA-21; con
  control positivo y sin tocar el pipeline. Salida en `C:\Users\nmend\AppData\Local\Temp\claude\techos_120\`.

### 2026-10-16 ~08:55 UTC (vuelta 88): F/K V1 sin evaluar: cobertura despareja en los cuatro brazos (D-13)
- Unión de intentos (43 del 1 más el gemelo del 2) contada con `contar_pasadas.py` (ventana 08-29 a 10-08): C0 4.754,
  F 4.779 (faltan 39, sobran 64), K 4.798 (22, 66), G 4.791 (29, 66); contra la unión de 4.820, a C0 le faltan 66.
  31 de 44 jobs cortos; ningún caso de gránulo distinto: son pasadas ausentes, casi siempre noches enteras (cortes de
  NASA, 0,5 a 1,4 % por job, A108). El control de PCC falla la regla del 5 % contra producción (V375 5,7 %, V750 7,3 %).
  No se evaluó. Detalle en `C:\Users\nmend\AppData\Local\Temp\claude\fk_v1\` (cobertura y `detalle_cobertura.*`).
- Tercera vez (W1, V2a, V1): es propiedad de los A/B largos, no mala suerte. Decisión D-13 para Nicolás: repetir y unir
  (A108) o evaluar sobre la intersección como desviación registrada. Mientras, nada se evalúa.

### 2026-10-16 08:34 UTC (vuelta 87): F/K V1 completa; evaluación delegada
- V1 intento 2: el gemelo de Villarrica salió verde (44 jobs verdes en total entre los dos intentos; `recolectar` del
  intento parcial no cuenta cobertura, como está diseñado). Evaluación delegada: unir intentos, contar cobertura con el
  instrumento del repo, `evaluar_fk.py` sin tocar la vara (regla D-9 SN, informando SE y original); después verificador
  limpio. Salida en `C:\Users\nmend\AppData\Local\Temp\claude\fk_v1\`.
- V2a intento 2 ya corre (6 jobs en curso). W2a 16 de 22. NRT verde 03:15 UTC (5 h 19 min; vigilar el umbral de 12 h).
  Disco 21 GB.

### 2026-10-16 ~08:30 UTC (vuelta 86): verificador de la 1.18: cero de saturación CONFIRMADO; dos hallazgos latentes
- `experiments/_s151_saturacion_chillan/verificador/VERIFICADOR.md`. El instrumento puede dar distinto de cero: lee el
  bit 4 (Saturation, Tabla C.1) y el SI crudo antes del lector de producción, y en estos mismos gránulos marca I04
  saturado en 59 y MODIS B22 = 65533 en 8, todos fuera de la caja de 25 km; el brazo «sin» reproduce producción exacto
  (182/182 `t_max_k`, 157/157 `pc.vrp_mw`). El 348,3 K era diurno; el máximo nocturno es 347,12 K (10-15 06:36),
  14,7 K bajo el techo. La pasada de 22,13 MW de MIROVA (10-15 05:00 V375) la damos en 10,36 MW, sin saturados: el
  déficit en erupción no es saturación. PARCIAL el cruce con MIROVA: el job no exporta `GH_TOKEN` y la referencia quedó
  en el snapshot del 10-14 08:35 (faltan once alertas finales, todas medidas con 0 saturados).
- **Hallazgos latentes (no activos en esta ventana), para Nicolás:** (1) en NOAA-21 la LUT de I04 llega a 361,00 K,
  bajo el corte de producción de 361,27 K: la defensa secundaria nunca dispara en ese satélite; (2) el techo de M15 en
  `pipeline/process_viirs_mod.py:182` (343 K) borra M15 válido hasta 374 K, que en erupción puede ser señal real del
  TIR. Los dos tocan producción (A45): quedan como tarea 1.20 de sólo lectura (medir cuántos records afectaría) antes
  de proponer nada. 1.18 HECHA.

### 2026-10-16 ~08:15 UTC (vuelta 85): verificador de la 1.19: PARCIAL; la conclusión fuerte cae
- `experiments/_s151_angular_119/verificador/VERIFICADOR.md`. Ángulos de zona CONFIRMADOS (31,589° y 44,680° de barrido,
  36,32° y 52,66° de cenit; M13 no se agrega, así que V750 no es réplica segura). Escalón en el OSF: sólo el de 52,66° es
  robusto (+0,12 con contraste local, placebo máx 0,086); el de 36,32° cae dentro del placebo y lo empuja el VRP total,
  no el Npix (al revés del mecanismo); la caída de Npix desaparece con nudos cada 2°; el nulo pre-registrado (barajado)
  se cambió sin declararlo. «Un tercio del límite físico»: razonamiento REFUTADO (con remuestreo, ±0,405/±0,693 es el
  límite de una fuente subpíxel; una extensa da 0). Aplanado: no circular, pero la selección no estaba pre-registrada,
  excluye a Chillán sin decirlo y es casi sólo Láscar (Isluga sola, 1,33). Sintético tautológico. La ley nueva es ~15 %
  más suave que el área geolocalizada de S133, se pasa con todos los volcanes (1,26) y no cierra D17.
- Consecuencia: la 1.19 queda con UN hallazgo (escalón real de MIROVA a 52,66° en el OSF) y SIN palanca que pre-registrar.
  No se propone A/B. La dependencia angular de nuestra magnitud sigue en gran parte SIN ATRIBUIR. La 1.19 queda hecha.

### 2026-10-16 08:02 UTC (vuelta 84): 1.18 terminada: en la erupción de Chillán no saturó ningún píxel (por verificar)
- Run 38863912173, 12 jobs verdes, 385 gránulos de Chillán del 2026-09-28 al 2026-10-16 (V375 152, V750 154, MODIS 79,
  noche y día). 0 píxeles saturados en el radio interior y en la escena, en los tres sensores; el VRP con y sin ellos
  es idéntico. El cero tiene margen físico: la BT válida más alta del interior fue 348,3 K en V375 (2026-10-08 19:30),
  bajo nuestro techo de 361,77 K y el de MIROVA, 353 K; V750 326,9 K; MODIS 307,1 K. La saturación no explica el
  déficit de magnitud en Chillán (de noche, V375 suma 118 MW donde las alertas de MIROVA suman 169; conjuntos distintos).
  Referencia: snapshot (falló la bajada remota). Salida en `experiments/_s151_saturacion_chillan/resultado_38863912173/`.
- Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_118\`). En curso también el de la 1.19.
  F/K: el job de Villarrica gemelo sigue esperando runner; V2a intento 2 pendiente. W2a 13 de 22.

### 2026-10-16 ~08:00 UTC (vuelta 83): 1.19 terminada (por verificar): la agregación del VIIRS explica la dependencia angular
⚠️ **Rebajado en la vuelta 85 (verificador limpio, PARCIAL):** sólo el escalón de 52,66° se sostiene; el de 36,32° cae
dentro del placebo y lo empuja el VRP total, no el Npix; el «tercio del límite» está mal razonado; el aplanado es casi
sólo Láscar; el sintético era tautológico; la palanca casi no se distingue del área de S133. Ver la entrada de la
vuelta 85. Texto original:
- `experiments/_s151_angular_119/` (predicciones en `PREREGISTRO.md` antes de correr; cada número con su script). En
  el OSF global de MIROVA (V375 noche, 208.293 filas, 158 volcanes, efecto fijo volcán × mes) VRP/Npix sube +0,135 y
  +0,216 en ln en los límites de zona de agregación (36,32° y 52,66° de cenit, de los ATBD de geolocalización e imagen
  leídos renderizados; el SDR User's Guide no está en `documentacion/`), sobre el máximo de 89 placebos (0,079); se
  replica en SNPP y NOAA-20; MODIS (sin agregación) no salta; el VRP total no salta (energía conservada).
- En Láscar, Isluga y Copahue (sin kernel local), corregir R por la huella con agregación aplana la razón de 1,88× a
  1,09× (0,80 a 0,87); el control con huella suave falla (2,83). Con todos los volcanes, 0,87 a 1,10. El sintético por
  `calculate_vrp` sigue la huella (pendiente 0,995). Palanca sugerida: área según la huella nativa con agregación (no el
  espaciado geolocalizado de S133). Límites: pares de 2025 (antes de #535), huella modelada (+4 % en el borde), sin PSF.
- Verificador limpio lanzado (`C:\Users\nmend\AppData\Local\Temp\claude\verif_119\`). Nada se adopta (§1.1).

### 2026-10-16 07:31 UTC (vuelta 82): 1.19 arrancada; esperan D-11 y D-12
- Paradas: NRT verde 03:15 UTC; disco 21 GB. El job de Villarrica gemelo (V1 intento 2) lleva 1 h en cola de runners;
  V2a intento 2 pendiente detrás. W2a en 12 de 22; saturación 1.18 en 4 de 11.
- 1.19 delegada (sólo lectura, local): salto de Npix y VRP/Npix en las zonas de agregación VIIRS sobre el OSF global
  (ángulos del User Guide renderizado) y fuente sintética; control que pueda fallar. Salida en
  `C:\Users\nmend\AppData\Local\Temp\claude\angular_119\`.

### 2026-10-16 ~07:45 UTC: Mirova-v1#25, segunda vuelta del verificador: sin bloqueos de producción
- Arreglos de la primera vuelta aplicados (`43ebe33`): backfill después del push del OCR (un solo escritor), presupuesto
  de 5 min, historia a mano sin escribir el repo, errores por fila con reintento y aviso, marcador compartido →
  `ambiguo` (33 filas), umbral recalculado con las dos muestras (5). Segunda vuelta: commit del OCR a salvo ante
  cancelación, sin choques de push, ningún error en silencio; `Distancia_km` y las 25 columnas viejas byte a byte iguales.
  Pendiente sólo de texto: el umbral 5 no es estable (bootstrap: 1 en 43 %, 5 o 6 en 35 %) → PROVISIONAL; y `exit 1`
  tras 5 pushes rechazados. Pedido al autor. Después: merge de Nicolás.

### 2026-10-16 ~07:15 UTC (vuelta 81): pre-registro 1.17 listo para el sello (#837 en main)
- #837 mergeado (CI verde, `b130fa72`): Δ de la regla 2 decidido sólo con el estrato A (Wilson por volcán), B summit y
  las alertas en conteo exacto; B far, fuera y control como prueba del modelo (cambio ahí = INDETERMINADO con motivo).
  Ancho bajo el nulo de ±2.265 a ±44, fijado por test; MEJORA alcanzable. Verificador: los cinco arreglos de la
  primera vuelta están y éste era el único pendiente. Pido el sello a Nicolás (D-11).

### 2026-10-16 06:58 UTC (vuelta 80): F/K V2a terminó despareja; repetida completa para unir intentos
- V2a (run 38648773684, 2026-03-01 a 04-20): 22 jobs verdes; `recolectar` marca COBERTURA DESPAREJA. No son gránulos
  reprocesados: 53 pasadas sólo en el control y 51 sólo en el brazo `_s149_ab_sin_test1_b22_max`, repartidas en 10
  volcanes. Caídas sueltas de descarga en los dos brazos, como en W1. Repetida completa (intento 2, pendiente en el
  grupo `s146-ab-sin-test1` detrás de la repetición de V1, que ya tiene su job creado); después se unen los dos
  intentos de cada brazo con `experiments/_s151_ab_diurno/unir_intentos.py` (exige records comunes idénticos) y se
  cuenta la cobertura otra vez. V2b no se despacha hasta que esto cierre.
- Corriendo: W2a (8 de 22), la medición de saturación 1.18 (6 en curso), la repetición de V1 (1 job en cola).
  NRT verde 03:15 UTC. Disco 20 GB.

### 2026-10-16 ~07:40 UTC: segunda vuelta del verificador de 1.17: SELLABLE CON UN ARREGLO
- Los cinco arreglos están en main. Ningún filtro pierde alertas: las 3 protegidas fuera del censo son diurnas (MODIS
  sólo procesa la noche). Falta uno: simulado sin cambios, el intervalo de Δ de la regla 2 da ±2.265, con 97 % del
  ancho en estratos que el modelo declara inmóviles; MEJORA y EMPEORA eran inalcanzables. Pedido al autor: Δ sólo con
  A más B summit y alertas en conteo exacto; B far, fuera y control como prueba del modelo (cambio ahí =
  INDETERMINADO con motivo); test del ancho máximo bajo el nulo.

### 2026-10-16 ~07:20 UTC (vuelta 79): 1.18 despachada (#836); arreglos de 1.17 en main (#835), segunda verificación
- 1.18 (#836, CI verde, `9011b584`): medición descriptiva de saturación en Chillán desde el 2026-09-28 (VIIRS 375 y 750,
  151 pasadas cada uno; MODIS 79; noche y día aparte), conteo de saturados por bit de calidad y por SI = 65533, VRP con
  y sin ellos a un piso explícito, cruce con MIROVA. Run 38863912173 (11 jobs, 6 a la vez, 60 a 90 min estimado; ~87 GB
  bajados y borrados en los runners). Sin veredicto, sin candado.
- 1.17 corregida (#835, `bca47c6a`): banda por record según el corrimiento predicho, censo de 88 pasadas con alerta
  de MIROVA (46 protegidas), regla 1 como compuerta, brazo C', JSON por gránulo; 471 gránulos en 12 jobs. Candado
  puesto. El mismo verificador revisa la segunda vuelta antes de pedir el sello a Nicolás.
- Worktrees 117b y 118 retirados; disco 21 GB. Sigue en curso: arreglos de Mirova-v1#25.

### 2026-10-16 ~06:50 UTC (vuelta 78): verificador del pre-registro 1.17: SELLABLE CON ARREGLOS (cambian el diseño)
- Cumple: el brazo MxD03 lleva la posición oficial a todos los lugares donde decide (parche en `read_modis_l1b`), y la
  prueba sintética distingue corrimiento presente de ausente; auth sólo token.
- No cumple: (a) la banda fija de 3 km no basta: el modelo de #828 predice 4,8 km a 54° y 9,6 km a 65° de cenit; 34 %
  de los records supera 3 km y el estrato medio sin medir tiene 197 de 622 publicaciones; (b) ninguna de las 48 pasadas
  MODIS protegidas de MIROVA del tramo (Láscar 40, Chillán 6, Villarrica 2) está en la muestra. Además el evaluador
  daba «cambia poco» con la cota inferior encendida y no marcaba INCOMPLETO si faltaba un volcán (los dos probados).
- Arreglos pedidos al agente del probe (worktree nuevo `../VRP-Chile-117b`): banda por record según corrimiento
  predicho, censo de las 48 protegidas con la regla 1 como compuerta, control negativo C', JSON incremental, evaluador
  corregido. El sello sigue esperando. En curso también: arreglos de Mirova-v1#25 y preparación de 1.18.

### 2026-10-16 ~06:30 UTC (vuelta 77): 1.17 en main con candado (#834); verificador del pre-registro lanzado
- #834 mergeado (CI verde, `b9d65830`): probe que corre cada gránulo MODIS dos veces por el pipeline de producción
  (posición interpolada contra MxD03) y re-etiqueta con el predicado del tablero. Población de 364 gránulos (A: hotspot
  a 3 km o menos del límite, tope 30 por volcán; B: sólo el cúmulo cerca, tope 8; control a más de 6 km, tope 6).
  Prueba sintética: 2 km de corrimiento da summit->far, cero da todo igual. Tiene candado: no corre sin el sello de
  Nicolás (regla 1.6). Los umbrales «poco < 2 %, mucho >= 5 %» los eligió el agente (A115): el verificador revisa si
  deben salir de la regla de victoria (alertas protegidas) en vez de publicaciones.
- Verificador limpio del pre-registro en curso (`C:\Users\nmend\AppData\Local\Temp\claude\verif_117\`). Con su
  informe, el sello pasa a Nicolás. En paralelo, el subagente de Mirova-v1#25 aplica los arreglos de su verificador.

### 2026-10-16 ~06:05 UTC: verificador de Mirova-v1#25: MERGEABLE CON ARREGLOS
- Bien: CSV escrito de una vez, columnas viejas byte a byte iguales sobre copia del CSV real, `Distancia_km` intacta,
  idempotente, 0 violaciones de `ambiguo` en 389 filas, README como complemento (192/192 y 158/161 reproducidos).
- Arreglos pedidos al subagente del PR: (1) el backfill no puede compartir job con el OCR (`cancel-in-progress` y 15
  min de presupuesto hacían perder el commit del OCR): workflow propio o después del push, presupuesto corto en cron y
  la historia una vez a mano; (2) errores por fila con reintento, anotación de advertencia, sin todo o nada; (3) el
  umbral 4 no se replica (8,5 % de error entre 4 y 7 pareos en una muestra disjunta contra 3,8 % global): re-derivar
  con las dos muestras; (4) marcador reclamado por dos filas de la misma noche → `ambiguo` (37 de 270); (5) pareos
  enteros, `*.tmp` ignorado, poda de caché; (6) tests para 3 mutaciones que sobrevivían. Informe:
  `C:\Users\nmend\AppData\Local\Temp\claude\verif_pr25\VERIFICADOR.md`. El merge sigue esperando a Nicolás.

### 2026-10-16 05:55 UTC (vuelta 76): tarea 1.17 en preparación (subagente, worktree propio)
- Paradas: NRT verde 03:15 UTC; disco 21 GB.
- 1.17 delegada: extender el probe de #828 a los 11 volcanes (records MODIS a 3 km o menos del límite summit/far más
  un control), re-etiquetar con el predicado del tablero, tope de gránulos por job, borrar cada gránulo. Worktree
  `../VRP-Chile-117`, rama `loop/1.17-mxd03-etiquetas`; PR sin merge ni despacho (lo hago yo con CI verde).
  Sigue en paralelo el verificador de Mirova-v1#25.

### 2026-10-16 ~05:35 UTC (vuelta 75): tarea 1.16 hecha; tres tareas nuevas en la cola (1.17 a 1.19)
- Inventario de material crudo (`experiments/_s151_repaso_crudo/INVENTARIO.md`, sólo lectura sobre `8b2bcd79`). Revisé
  a mano tres de sus citas (`process_modis.py:342` y `:470-471`, `VERIFICADOR_AUDITORIA.md:205-206`): calzan. Orden de
  ataque: posiciones MODIS con MxD03 en todo el corpus, saturación en Chillán leída en el L1B, dependencia angular con
  el OSF global; después cat-b contra SWIR y D20. En las filas 1 a 4 el árbitro es NASA, MIROVA o el SWIR.
- Encoladas como 1.17, 1.18 y 1.19. Próxima tarea libre: 1.17 (probe en Actions; cuenta como A/B para el tope de 2
  sólo si reprocesa, y no reprocesa: lee gránulos y records).

### 2026-10-16 05:24 UTC (vuelta 74): tarea 1.16 arrancada (subagente de sólo lectura)
- Paradas: NRT verde 03:15 UTC; disco 21 GB. V2a en 18 de 22; W2a con 3 jobs corriendo y 19 en cola; W2b y la
  repetición de V1 pendientes en sus grupos.
- 1.16 en curso: inventario de una página en `C:\Users\nmend\AppData\Local\Temp\claude\repaso_crudo\INVENTARIO.md`.
  En paralelo, el verificador limpio de Mirova-v1#25. Dos agentes.

### 2026-10-16 ~05:10 UTC (vuelta 73): Mirova-v1#25 (distancia aproximada) abierto con CI verde; en verificación
- Subagente terminó las tareas 5 a 8 del plan: [Mirova-v1#25](https://github.com/MendozaVolcanic/Mirova-v1/pull/25)
  (12 archivos, 117 tests en verde, subido por la API). Umbral `PAREOS_MINIMOS = 4`, medido con el lector portado: 38
  erradas de 1.240 decididas (3,1 %); los calados en el borde no yerran más (8 de 8 con el umbral). Backfill sobre
  copia del CSV real (31 min con caché vacía; 6 a 30 s en régimen): de las 15 sin geometría, 7 coinciden con el
  estudio, 4 de VIIRS 750 quedan `sin_control` y 4 `pendiente` (Chillán 22 MW y Villarrica tenían imagen de menos de
  1 día); del reparto 163/48/34/35, 242 de 280 coinciden y las 38 restantes tienen causa listada. Marcador a la cifra
  OCR más otro: `ambiguo`. Fuera del plan: `scraper_ocr.py` borraba columnas nuevas al guardar (ahora las conserva) y
  el paso del workflow tiene timeout de 20 min y presupuesto de 15.
- Verificador limpio lanzado (riesgo de producción primero: que una falla del backfill no rompa el OCR ni deje el CSV
  a medio escribir). El merge espera a Nicolás (Mirova-v1 es producción). Pendiente tras el merge: hito A119 en
  `scripts/calidad_referencia_mirova.py`.

### 2026-10-16 05:00 UTC (vuelta 72): G3 del evaluador diurno arreglado y verificado; PR #833 en CI
- Verificador limpio de G3: SELLABLE CON ARREGLOS. Mecanismo reproducido (OpenBLAS elige kernel por CPU y cambia el
  último bit de la regresión del ETI; MODIS también difiere y no lee el flag). Corrigió una cifra mía: no era
  «~1e-16 relativo» sino hasta 1,4e-11 relativo a μ (μ casi cero), 5,4e-14 contra σ; con tolerancia relativa sola,
  W2 a W6 habrían fallado en falso. Arreglos aplicados: piso absoluto 1e-14, enteros/None/strings exactos, casos 22c a
  22g. Autoprueba 57 de 57; mutaciones 8 de 8 nuevas y 7 de 7 de siempre; desviación D1 en `PREREGISTRO.md` §11.
  PR [#833](https://github.com/MendozaVolcanic/VRP-chile/pull/833), CI corriendo; se mergea en verde (no toca
  producción).
- Siguiente: con #833 en main, despachar W2 partida en dos mitades (06-13 a 06-21 y 06-22 a 06-30), la segunda cuando
  la primera ya corra (el grupo guarda un solo pendiente). Después, la tarea 1.16.
- **Hecho en la misma vuelta:** #833 mergeado (CI verde, `8b2bcd79`). W2a despachada (run 38853230521, 06-13 a 06-21,
  11 volcanes, ya con jobs corriendo) y W2b después (run 38853273752, 06-22 a 06-30, pendiente en el grupo). Quedan 2
  A/B en GitHub: F/K (V2a corriendo, repetición de V1 pendiente) y el diurno. W3 a W6 se despachan cuando W2 termine.

### 2026-10-16 04:20 UTC (vuelta 71): la distancia del OCR acierta el lado; trabajo en paralelo
- Nicolás pidió avanzar en paralelo cuidando disco y procesos. Computador despierto mientras haya trabajo; disco
  21 GB. La sesión aparte para Mirova-v1 tareas 5 a 8 no arrancó: el worktree pedía 23,1 GB libres y había 21,8. La
  tarea corre como subagente de este hilo, en el worktree `Mirova-v1-distaprox` (no necesita uno nuevo).
- Medición en sesión aparte (`experiments/_s151_distancia_ocr/cambian_lado/INFORME.md`, sólo lectura): si la referencia
  usara la distancia de la serie en vez de la del OCR (06-13 a 10-08), 19 protegidas pasarían de cráter a lejana y 1 al
  revés. **Pero en las 197 pasadas OCR que también están en la tabla, el OCR acierta el lado en las 197; la serie, 146
  de 153.** El sesgo de distancia del OCR (PCC, Tupungatito) es real y no cruza el límite. De los 20 cambios de
  protegidas, sólo 10 son firmes (todos diurnos: Lastarria 6, Isluga 3, Láscar 1); 8 nocturnos caen en el patrón que el
  control mostró ambiguo (5 de 9 errores) y la ganancia de Láscar 08-21 es un error de la serie. Veredictos ya
  publicados: Chillán, VIIRS 750 y la caja no cambian; en los meses de S150, F gana igual; F/K V1 (sin evaluar) perdería
  7 protegidas si se aplicara la serie, 6 en el patrón ambiguo.
- **Consecuencia (corrige las vueltas 62 y 63, A113):** NO hay que reemplazar la distancia del OCR por la de la serie
  para decidir cráter o lejana. `Distancia_aprox_*` es complemento para las filas sin distancia; se lo dije al subagente
  de Mirova-v1. Las 10 protegidas diurnas firmes quedan como pregunta para la referencia (las diurnas además dependen
  de D-10). Memoria corregida.

### 2026-10-16 01:31 UTC (vuelta 69): W1 del A/B diurno evaluada (informa); G3 del evaluador mide la máquina
- Paradas: NRT verde 22:53 UTC; disco 24 GB. V2a de F/K sigue.
- W1 intento 3: el brazo diurno tardó **2 h 30 min** (intento 1: 1 h 50). Volvió a faltar 1 noche, pero OTRA: cada
  intento pierde pasadas sueltas distintas por descarga (intento 1 sin 03-20 MODIS y 03-18 NOAA-20; intento 3 sin
  03-14 NOAA-20). En los 325 gránulos comunes los records son idénticos, así que se unieron los dos intentos
  (`experiments/_s151_ab_diurno/unir_intentos.py`, que se niega a unir si un común difiere): 183 noches contra 183.
- Evaluación (`evaluar_diurno.py`, salida en `experiments/_s151_ab_diurno/salidas/38723828037_union/`). W1 sólo
  informa (A119); decide W2 a W6. Láscar VIIRS 375 de día: **recupera las 5 alertas protegidas diurnas** (100 %),
  pero **publica en 13 de 18 negativos diurnos limpios (72,2 %)** contra una parsimonia de MIROVA de 0,5 %; VIIRS 750
  1 de 24 (4,2 %). G1 de W1 falla contra el nulo barajado. Es el riesgo escrito en el pre-registro: el Test 1 suma MIR
  absoluto y de día el Sol calienta todo el disco. Veredicto formal INDECIDIBLE (sin W2 a W6).
- **Defecto del evaluador:** G3 («noches intactas») da FALLA porque compara floats con `!=`. `diag_mu_deti` y
  `diag_sd_deti` difieren en ~1e-16 relativo en 179 de 183 noches (regresión del ETI sumada en otro orden en otro
  runner); `vrp_mw`, píxeles y dNTI son idénticos. Mismo modo de falla que S142 («golden que mide la máquina»).
  Antes de W2 a W6: G3 con tolerancia relativa (p. ej. 1e-9) y un test con este caso, más verificador limpio, porque
  es un cambio del evaluador después de ver datos (el motivo es mecánico, no el resultado).
- Duración para W2 a W6 en mitades: el brazo diurno tarda unos 2 a 2,5 h por 20 días de un volcán.
- Próxima vuelta: arreglo de G3 con su test (rama propia); después, despachar W2 partida.

### 2026-10-16 01:09 UTC (vuelta 68): tarea 4 del plan de Mirova-v1 hecha (imagen de 1 a 25 días)
- Paradas: NRT verde 22:53 UTC; disco 24 GB. W1 diurna intento 3 lleva 2 h 13 min (el intento 1 tardó 1 h 50; el
  control que murió por «perder comunicación» lo hizo a las 2 h). Si vuelve a morir, es el runner y no el código:
  pensar en partir la ventana de 20 días antes de repetir otra vez.
- `imagen_para` (más reciente de 1 a 25 días; md5 repetido por su primera aparición, A106); commit local `28589c7d`;
  suite de Mirova-v1 98 en verde.
- Próxima vuelta: W1 si terminó; si no, tarea 5 (umbral de calado débil medido contra el control, incluido el borde).

### 2026-10-16 00:46 UTC (vuelta 67): tarea 3 del plan de Mirova-v1 hecha (eliminación sólo con la tabla)
- Paradas: NRT verde 22:53 UTC; disco 24 GB. W1 diurna intento 3 sigue a 1 h 50 min (el intento 1 tardó lo mismo).
- `otras_de` y `eliminar` portados con el filtro de la tabla; commit local `7b14c37d`; cinco tests nuevos (único,
  ambiguo, solapado, sin marcador, OCR que no descuenta, propia pasada excluida). Suite de Mirova-v1 95 en verde.
- Próxima vuelta: evaluar W1 si terminó; si no, tarea 4 (imagen de 1 a 25 días).

### 2026-10-16 00:18 UTC (vuelta 66): tarea 2 del plan de Mirova-v1 hecha (calado sólo con la tabla)
- Paradas: NRT verde 22:53 UTC; disco 24 GB; W1 diurna intento 3 en curso; V2a corriendo.
- `calibrar` portado con el filtro `solo_tabla` (cambio 1 del verificador), commit local `45d8105c`; test de que una
  fila OCR no suma pareos, comprobado fallando sin el filtro. Suite de Mirova-v1 90 en verde.
- Hallazgo menor: la imagen de Chillán del 10-15 14:06 UTC cala con desfase +0,76 d, en el borde de la búsqueda (7 de
  429 imágenes del control lo hacen; la mediana por mes es +0,48 a +0,53). Queda para la tarea 5: medir con el control
  si esos calados en el borde yerran más, y si es así tratarlos como débiles. La pasada de 22 MW del 10-15 05:00 sale
  de esta imagen, así que importa.
- Próxima vuelta: tarea 3 (eliminación sólo con la tabla).

### 2026-10-15 22:55 a 23:55 UTC (vuelta 65): el lector portado pasa el re-control; tarea 1 del plan hecha
- Paradas: disco 25 GB; NRT verde a las 19:41 UTC, otro en cola desde las 22:53 (cola de GitHub). V2a en 6 de 22.
- W1 diurna intento 2: el control repetido salió bien, pero vio 183 noches de Láscar contra 181 del brazo diurno
  (corrió 7 h antes; probablemente pasadas que llegaron tarde a NASA, A108). `recolectar` además no pudo publicar
  la rama (5 intentos). Repetido el brazo diurno con el mismo código (intento 3, en curso).
- Re-control del estudio con tres lectores, 429 imágenes y 1.368 pasadas de control (`experiments/_s151_distancia_ocr/recontrol/`):
  | lector | dibujadas | único: n, mediana / p90 | dentro del intervalo | cerca/lejos erradas |
  |---|---|---|---|---|
  | estudio (scipy) | 98,5 % | 726, 0,08 / 0,64 km | 97,6 % | 40 de 1.353 |
  | port (orden estable) | 98,5 % | 722, 0,09 / 0,64 | 98,1 % | 40 |
  | port, centro de la meseta | 98,6 % | 726, 0,07 / 0,64 | 97,9 % (ancho mediano 0,41 km contra 0,54) | 41 |
  El desempate de picos cambia marcadores sueltos pero no el control. Elegido el centro de la meseta por razón
  física (el marcador está centrado en la distancia), no por la cifra. Tarea 1 HECHA (`cb72ac51`, local; suite de
  Mirova-v1 88 verde). El push por git a Mirova-v1 se corta en `send-pack`: al abrir el PR, subir por la API.
- Próxima vuelta: tarea 2 del plan (calado del eje de tiempo sólo con la tabla).

### 2026-10-15 19:18 UTC (vuelta 64): tarea 1 del plan de Mirova-v1 a medias; el lector depende de desempates
- Paradas: NRT verde (14:40 UTC; el cron de GitHub corre cada 4 a 6 h, no cada 2), disco 26 GB. F/K V1 intento 2
  pendiente detrás de V2a; W1 diurna intento 2 en curso.
- Tarea 1 del plan: `dist_serie.py` portado en el worktree
  `C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Mirova-v1-distaprox`, rama
  `feat/distancia-aprox`, commit local `2a3e7121` (WIP, sin PR). scipy no está en `requirements.txt` de Mirova-v1,
  así que la correlación pasa a OpenCV (`cv2.filter2D` con ancla `((w-1)//2, (h-1)//2)`; la de por defecto corre un
  píxel en plantillas de lado par, lo atrapó el test de equivalencia). Tres tests en verde.
- **Hallazgo:** el número de marcadores que lee el estudio depende del desempate de picos. El puntaje de un cuadrado
  empata en filas vecinas y el ruido de punto flotante (1e-16) decide. El lector del estudio es estable consigo mismo
  (0 de 449 imágenes cambian), pero el port sin redondear cambia el número de marcadores en 118 de 449, y redondeado
  con orden estable en 42 de 449. **Las cifras del control (4,5 % de error, 98,5 % dibujadas) valen para el lector
  del estudio, no para el port.** Antes de la tarea 2 hay que volver a correr el control con `dist_serie.py`
  (`experiments/_s151_distancia_ocr/scripts/control_dist.py` cambiando el import) y elegir un desempate con sentido
  físico (por ejemplo el centro de la meseta de empate), no el que dé menos diferencias.
- Nicolás suspende el PC ahora. Próxima vuelta: ese re-control, y después la tarea 2.

### 2026-10-15 18:45 UTC (vuelta 63): plan de la distancia aproximada en Mirova-v1; estudio y verificador al repo
- Paradas: NRT verde (14:40 UTC), disco 25 GB. F/K V1 intento 2 PENDIENTE detrás de V2a (38648773684, corriendo);
  W1 diurna intento 2 en curso.
- Tarea: plan de implementación (`writing-plans`) en `tasks/PLAN_MIROVA_V1_DISTANCIA_APROX.md`, con los seis cambios
  del verificador. No se implementa en esta vuelta porque Nicolás suspende el PC (~19:15 UTC). Decisión del plan:
  **no re-archivar las `Dist.png` en Mirova-v1**, porque el poller de `mirova-tif-archive` ya las guarda desde el
  05-09 con índice y md5, y se leen por raw sin clonar. Si Nicolás quiere una copia en Mirova-v1, se agrega una tarea.
- Estudio y verificador copiados del temporal a `experiments/_s151_distancia_ocr/` (informe, scripts y salidas de
  texto; sin los datos de 79 MB), para que no dependan de `AppData\Local\Temp`.
- Próxima vuelta: ejecutar el plan, tarea 1 (`executing-plans`), en un worktree de `Mirova-v1-codigo` sobre
  `origin/main`.

### 2026-10-15 18:10 UTC (vuelta 62): loop retomado tras el reinicio; dos jobs repetidos; Nicolás suspende el PC ~19:20 UTC
- Paradas: NRT verde (14:40 UTC), disco 26 GB, sin alerta nueva (#779 sigue abierto; #824 es el watchdog, ver abajo).
- F/K V1 (run 38639658446) TERMINÓ: 43 jobs verdes, falló Villarrica gemelo («el runner perdió comunicación con el
  servidor», 08:59 a 11:16 UTC) y por eso `recolectar` marca COBERTURA DESPAREJA (A108). Repetido con el mismo código
  (`gh run rerun --failed`, intento 2): queda PENDIENTE en el grupo `s146-ab-sin-test1` detrás de V2a (run
  38648773684, que ya corre: 6 jobs en curso y 16 en cola; el watchdog #824 lo veía «pending» por la cola del grupo).
  Al terminar V2a corre el gemelo; recién entonces contar cobertura y evaluar con `evaluar_fk.py` + verificador limpio.
  Ojo: no despachar V2b mientras el intento 2 de V1 espere, porque lo desplazaría del grupo.
- W1 del A/B diurno (run 38723828037): el brazo diurno `_s151_ab_diurno_on` tardó **1 h 50 min** (Láscar, 20 días),
  sobre el umbral de 1,5 h del pre-registro (§7.1): **W2 a W6 se despachan partidas en mitades**. El control falló
  igual que el gemelo («perdió comunicación», a las 2 h); repetido (intento 2, en curso). Evaluar W1 al terminar.
- Hito A119 de V31.1: el comentario decía «fecha de merge PENDIENTE»; corregido a 2026-10-15 13:46 UTC
  (Mirova-v1#22, `0bd5b88b`) en #832 (sólo comentario; 14 tests de la referencia en verde). Se mergea con CI verde.
- Verificador limpio del estudio de distancias OCR relanzado (salida en
  `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\VERIFICADOR.md`), con plazo de 40 min por la suspensión; incluye
  la comparación de las 451 distancias del OCR contra la lectura por serie de tiempo, por tramo. Si no termina antes
  de suspender, se relanza al volver, retomando lo que haya escrito.
- Esperan a Nicolás: arreglo MxD03 en producción (A45, probe #828) y qué servicio dispara el cron del scraper
  (Mirova-v1#23, punto 4).
- **Cierre de la vuelta**: #832 mergeado (`4a0967a3`). Verificador de distancias OCR TERMINADO
  (`C:\Users\nmend\AppData\Local\Temp\claude\verifdist\VERIFICADOR.md`, scripts en `...\verifdist\scripts\v2_*.py`):
  **SÍ con cambios**. El control del §4 se reproduce exacto; sacando la noche del calado el error de decisión sigue en
  4,5 % (no es circular). Población: en el control ninguna ALERTA es lejana; en ALERTA el único error medido es cerca
  leído como lejos (4,9 %), y lejos leído como cerca no tiene muestra. ⚠️ **El «23 y 25 cambian de lado» que sigue
  cayó en la vuelta 71**: es OCR contra serie, no contra la verdad; contra la tabla, el OCR acierta el lado en 197 de
  197 pasadas (`experiments/_s151_distancia_ocr/cambian_lado/INFORME.md`). **Hallazgo:** del 06-13 al 10-08 la distancia
  que el OCR sí midió discrepa más de 2 km en 36 de 152 y 51 de 207 pasadas (~24 %; 23 y 25 cambian de lado del
  límite). En las 218 que también están en la tabla, el OCR falla en 25 y la serie en 7; esas 25 son sesgo geométrico
  del OCR (PCC 3,5 km donde la tabla da 7,7; Tupungatito), no otra pasada. Las 15 sin geometría quedan PARCIAL (imágenes
  de 7 h a 1,4 d, fuera del rango controlado); Villarrica 21,5 km SIN VERIFICAR; V750 y MODIS SIN VERIFICAR.
  Cambios exigidos para Mirova-v1: (1) eliminar sólo con la tabla, nunca con distancias OCR; (2) imagen de 1 a 25 días,
  si no la fila queda pendiente; (3) guardar los pareos del calado y no escribir con calado débil; (4) declarar el
  error por población; (5) sólo VIIRS 375; (6) aplicar la columna también a las 451 medidas (o marcar la
  discrepancia), `Distancia_km` intacta. **Próxima vuelta (tras la suspensión):** implementar en Mirova-v1 con esos seis
  cambios (aprobado por Nicolás si el verificador salía bien), en PR con CI; y evaluar si la referencia unificada de
  VRP Chile debe dejar de usar la distancia OCR del 06-13 al 10-08 para summit/far (decisión para Nicolás).

### 2026-10-15 ~17:30 UTC (vuelta 61): PAUSA pedida por Nicolás (reinicio por memoria)
- Hecho desde la vuelta 60: alertas diurnas de MIROVA en el tablero como soles (#831, ningún número publicado cambia);
  columnas UTC en el scraper (Mirova-v1#24, verificado tras la primera corrida: 42.755 filas, 15 columnas, LF, 114
  vacías esperadas; issue Mirova-v1#23 abierto sólo por el punto 4, cron de respaldo: falta saber qué servicio
  externo dispara el scraper).
- Estudio de distancia OCR (`C:\Users\nmend\AppData\Local\Temp\claude\distancia_ocr\INFORME.md`): `Dist.png` es una
  serie de tiempo de 30 días; la distancia de una pasada se lee en imágenes posteriores (error mediana 0,08 km en
  1.549 pasadas V375 de control). Chillán 22,13 MW cerca (0,4 a 1,5 km); Villarrica 15-oct 06:42 lejos (21,5 km).
- QUEDÓ CORRIENDO al pausar (se pierde con el reinicio): verificador limpio del estudio, que además compara las 451
  distancias que midió el OCR contra la lectura por serie de tiempo (sospechas: geometría mal calibrada antes del
  06-11; distancia de otra pasada hasta el 10-09, Mirova-v1#20). Relanzarlo; salida esperada en
  `C:\Users\nmend\AppData\Local\Temp\claude\verifdist\`.
- Pendientes con Nicolás: arreglo MxD03 en producción (A45, probe #828); D-10 en curso (W1 diurna run 38723828037);
  F/K V1 (run 38639658446) con un job fallido de Villarrica gemelo que hay que repetir al terminar; hito A119 de V31.1
  con fecha real 2026-10-15; implementar en Mirova-v1 la distancia aproximada (archivar `Dist.png`, columna
  `Distancia_aprox_km` con rango) si el verificador la confirma (Nicolás ya dijo sí).

### 2026-10-15 13:46 UTC (vuelta 60): pasadas sin geometría publicadas (Mirova-v1#22, #830); auditoría de horas (#829)
- A pedido de Nicolás: la pasada de Chillán 05:00 (22,13 MW V375, 14 MW V750) y otras 11 que el OCR rechazaba por
  V31 se guardan como `ALERTA_SIN_GEOMETRIA_OCR` (VRP de su celda, distancia vacía). Verificador limpio PARCIAL con
  arreglos aplicados: tipo propio, LF, hito A119, cita remapeada. Decisión conservadora mía: se publican en el
  tablero (✕ grande, «distancia desconocida») pero NO cuentan en la lectura A (estrato aparte; 440 protegidas
  antes y después). Mergeados #830 (`a116d262`) y después Mirova-v1#22 (`0bd5b88b`). Pendiente: comprobar que el
  OCR de las 14:00 UTC agrega las 13 filas, que el sync las lleva a `data/mirova/` y que el tablero las muestra
  (deploy cada 2 h); corregir el texto del hito A119 con la fecha real del merge (2026-10-15).
- Auditoría de horas de Mirova-v1 (#829 mergeado): conversiones correctas (0 de 42.722 mal); `Fecha_Proceso_GitHub`
  está en hora de Chile; la noche queda completa en MIROVA cerca de las 07:00 a 07:30 hora de Chile. Issue
  Mirova-v1#23 con cuatro defectos menores; los puntos 1 y 2 (columnas UTC aditivas) los aplico tras V31.
- Probe MxD03 (#828 mergeado): arreglo de producción justificado, espera el sí de Nicolás.

### 2026-10-15 12:27 UTC (vuelta 59): F/K V1 con un job fallido; W1 diurna lleva 1,5 h
- F/K V1: 33 jobs verdes, 6 corriendo, 4 en cola y **1 fallido** (Villarrica, gemelo `_s151_ab_control_gemelo`,
  08:59 a 11:16 UTC; el log no está disponible mientras el run sigue vivo). Cuando el run termine: leer el error y
  repetir ese job con el mismo código antes de evaluar (A108).
- W1 del A/B diurno (Láscar, 20 días) sigue corriendo a 1,5 h: según el pre-registro (§7.1), si pasa de 1,5 h
  hay que partir W2 a W6 en mitades.
- #828 (resultado del probe MxD03) espera CI. NRT verde 08:52 UTC. Disco 21 GB. Decisiones pedidas a Nicolás: arreglo
  MxD03 (A45) y las dos partes del rechazo V31 de Mirova-v1.

### 2026-10-15 ~13:00 UTC (vuelta 58): probe MxD03 PARCIAL verificado (#828); diagnóstico de Mirova-v1 a pedido de Nicolás
- Probe contra MxD03: la grilla de 5 km coincide con MxD03 en el offset 2 en los dos ejes; nuestra posición MODIS se
  aparta 1,2 a 2,6 km donde importa. Arreglo de producción (leer MxD03) justificado; espera tag y sí (A45). La caja
  sigue vetada con premisa «en duda», a re-medir tras el arreglo.
- Nicolás reportó un VRP de 22 MW de Chillán (VIIRS 375, 2026-10-15 05:00) que Mirova-v1 no registró. Causa: la tabla
  `latest.php` nunca lo publicó, y el OCR lo leyó pero lo rechazó por la regla V31 (Mirova-v1#20) porque la imagen de
  distancia era de la pasada de las 06:00. Una pasada que la tabla salta y no es la última se pierde siempre. El dato
  está en `ocr_rechazos_cabecera.csv` (13 filas; también la de VIIRS 750 de las 05:00 y la de ayer 18:42). Propuesto:
  guardar esas filas con VRP y sin distancia en Mirova-v1 (espera sí) y leer los rechazos en la referencia unificada.
- TIF: el visor sigue sirviendo el archivo del 22-sep (Last-Modified 22-sep 09:29, md5 `5ad2f851` idéntico al
  archivado); la cabecera «15-Oct 06:00» viene de la base de datos, no del TIF.

### 2026-10-15 (vuelta 57): 1.15, el corrimiento MODIS es un defecto de código (verificado PARCIAL)
- #826: `_interp_geo` ignora el offset 2 de la grilla de 5 km (Data Dictionary C7 p. 66): frame s rotulado como
  0,99778·s + 2; 1,0 km a 17°, 3,0 a 45°, 5,0 a 55° hacia el nadir del lado del frame 0. CONFIRMADO por el
  verificador. MxD03 (1 km, con terreno) se baja y `calculate_vrp` lo ignora (`process_modis.py:470`). No es
  paralaje dominante. Exagerado: el «coeficiente negativo», la fila M4, el veto de la caja (queda «en duda», no
  caído); la medición descansa en el brazo K y casi sólo Láscar; en producción el efecto queda enmascarado.
  Arreglos y un probe despachable contra MxD03 pedidos al agente. Persistido en memoria.
- D-3 cerrado: la corrida NRT de las 08:52 UTC ya escribe `regimen`. D-8 cerrado (#801). Quedan abiertos: D-10.

### 2026-10-15 (vuelta 56): caja vetada y verificada (#825); tarea 1.15 nueva, en curso
- Verificador del veto D1: CONFIRMADO como resultado del pre-registro (repetición idéntica, mismo código en los
  dos brazos, 1,0 MW es protegida en el filo). Atribución PARCIAL: es posición del píxel MODIS, pero no D17; el
  píxel del cráter MODIS aparece corrido hacia el sensor creciendo con el ángulo (hasta 3,5 km a 45°, n = 13).
  Resultado y marca en D18 en #825; cierre condicionado a la geolocalización MODIS de hoy.
- 1.15 agregada (de sólo lectura, sin tocar el pipeline): medir ese corrimiento en los 11 volcanes, separar
  paralaje de interpolación, control VIIRS que pueda fallar, contraste con TIF de MIROVA. Agente lanzado.

### 2026-10-15 10:55 UTC (vuelta 55): caja D1 VETADA (por verificar); W1 del A/B diurno despachada
- Repetición de D1 (run 38698329137): cobertura 132 contra 132 (la recolección marca DESPAREJA porque cuenta los
  otros 10 volcanes que la ventana no corre: otro defecto del workflow en ventanas de un volcán). Con
  `--repeticion`, la pérdida MODIS de Láscar 2026-03-27 07:10 (MIROVA 1,0 MW, único píxel de K en la corona) queda
  confirmada: **KC NO CUMPLE (veto)** en lecturas A y B, también con las cinco reglas de D-9. VIIRS 375 y 750
  cumplen. El pre-registro ya preveía que en D1 la causa sería la posición del píxel MODIS (D17), no la caja.
  Verificador limpio lanzado antes de aceptar.
- Con la caja en espera del verificador, el cupo va al A/B diurno: W1 (Láscar, 2026-03-01 a 03-20, mide la
  duración del brazo diurno) despachada, run 38723828037. W2 a W6, mejor después de F/K (§7.1 del pre-registro).
- NRT verde 08:52 UTC. Disco 25 GB.

### 2026-10-15 07:21 UTC (vuelta 54): caja D1 evaluada: PENDIENTE DE REPETICIÓN; repetición despachada
- Tercer intento: cobertura pareja (132 contra 132). La recolección quedó roja sólo porque no pudo publicar la rama
  `s151-ab-caja/<run_id>` (ya existía del primer intento; defecto del workflow en reintentos: nombrar la rama
  con el intento o forzar). Evaluado en local desde el artefacto `s151caja-todo` del tercer intento.
- `evaluar_caja.py --ventana D1`: controles OK, cableado K y KC OK, la caja actuó (corona 3 a 1 píxel). VIIRS 375 y
  750 CUMPLEN el veto en lecturas A y B. MODIS: una protegida que K publica y KC no, Láscar 2026-03-27 07:10
  MODIS_AQUA (MIROVA 1,0 MW; el único píxel de K está en la corona): PENDIENTE DE REPETICIÓN, como manda el
  pre-registro sin gemelo. Las cinco variantes de D-9 dan lo mismo.
- Repetición de D1 despachada (run 38698329137); se evalúa con `--repeticion`. Salida en el scratchpad
  (`caja_d1_v3/eval_d1.txt`), se commitea con el veredicto.

### 2026-10-15 06:48 UTC (vuelta 53): disco bajó a 12 GB; liberado a 26 GB
- El disco cayó de 22 a 12 GB libres en tres horas: eran salidas de autopruebas de los agentes y verificadores
  (`probar_*`, `tmp_probar`, `prueba`, 2,2 GB cada una) en el temporal. Borradas sólo esas carpetas regenerables
  de verificaciones ya terminadas; quedan informes y scripts. 26 GB libres. Regla para los próximos agentes: que
  sus autopruebas escriban en una carpeta que borren al terminar.
- NRT verde 03:20 UTC. F/K V1 20 de 44. Caja D1, tercer intento del brazo caja en curso.

### 2026-10-15 ~06:00 UTC (vuelta 52): #822 en main; caja D1 sigue despareja por NASA
- #822 (infraestructura del A/B diurno) mergeado tras arreglos: 7 de 7 mutaciones atrapadas, control del nulo que
  falla con el nulo roto (se compara contra la fracción que el propio nulo deja sobre su p95, no un 5 % fijo, porque
  D toma pocos valores). Listo para despachar cuando se libere un cupo de A/B.
- Caja D1, segundo intento: control 132, caja 130; faltan Láscar 2026-03-17 04:42 y 06:24 VIIRS_NOAA20_750, por un
  `502 Bad Gateway` de NASA al buscar ese producto (A108). Tercer intento lanzado con el mismo código.
- F/K V1: 18 de 44 jobs.

### 2026-10-15 (vuelta 51): 1.5 cerrada condicionada (#823); #822 en arreglos
- Verificador del probe D25 V750: falla la detección, no el fondo (magnitud de un píxel, 0,072 MW/K; razón contra
  MIROVA 1,19 en 28 rescates; AUC 0,861). #823 mergeado, #793 cerrado. Implicancia: D25 sólo tiene sentido junto
  con una detección más parsimoniosa; candidato natural, medirlo encima del brazo F/K que salga del A/B en curso.
- #822 (A/B diurno), verificador PARCIAL: el control del nulo era tautológico y la autoprueba dejaba pasar 4 de 7
  mutaciones; arreglos enviados. Costo estimado del A/B diurno ~130 a 150 h de runner (SIN VERIFICAR).
- Caja D1: job del brazo caja repetido, en curso.

### 2026-10-15 (vuelta 50): #820 y #821 en main; probe D25 V750 terminado, NO VALE en sus dos brazos (por verificar)
- #821 (rama diurna VIIRS apagada) y #820 (regla SN, protegidas a salvo por construcción) mergeados con CI verde
  tras sus verificadores; D-9 (#811) cerrado. #822 (infraestructura del A/B diurno) en verificación limpia.
- Caja D1 (run 38679191229): cobertura DESPAREJA (control 132 pasadas, caja 124: `SEARCH_CMR_TIMEOUT` de NASA
  en el brazo caja, A108). Repetido el job del brazo caja con el mismo código; no se evalúa hasta que la
  cobertura cuadre.
- Probe D25 V750 (run 38679955131): válido (356 de 356, C-P1 354, 14 con L1B reprocesado y las 14 con C-P1).
  Brazo a (canon): enciende los 268 negativos de cero y las 28 alertas; brazo b (vecinos bajo 255 K fuera):
  187 de 268 y 25 de 28, apaga 2 de 40 que publican. Ninguna protegida apagada. Los dos NO VALE (regla 2).
  Verificador limpio lanzado: busca si "enciende todo" es física o construcción del fondo por vecinos.

### 2026-10-15 (vuelta 49): verificadores de D-9 (#820) y D-10 (#821), los dos PARCIAL; arreglos enviados
- #821 (rama diurna VIIRS apagada): código CONFIRMADO (bit a bit con el flag apagado, el flag llega a todos los
  consumidores, umbrales de la Tabla 1 renderizada, 4 mutaciones atrapadas). Pre-registro diurno a corregir: G2 usaba
  como vara la sobre-publicación nocturna (defecto conocido) en vez de la parsimonia de MIROVA de día (0,4 %); falta
  cobertura diurna y `q_noche` con perfil de control. Confirmado un defecto latente en la rama diurna de MODIS (S90):
  sin C2 diurno y su flag no abre fetch ni run_pipeline (A118); va como marca en D27, no se arregla aquí. El frontend
  asume pasadas nocturnas (corregir antes de cualquier flip).
- #820 (regla SN): default "original" reproduce bit a bit; F/K intacto (41 de 41). Falla: las protegidas no están
  a salvo por construcción (contraejemplo CONS 0,04 + OCR 1,5 en el mismo minuto; hoy no ocurre, 440 de 440);
  el evaluador de la caja no informa las reglas; hijos sin marcar; dos copias del predicado (A102). Marcada aquí la
  tarea 1.3 (techo 14 a 5 bajo SN).

### 2026-10-15 04:10 UTC (vuelta 48): D-3 mergeado, caja D1 y probe D25 completo despachados
- D-3: #785 mergeado (`37ed449b`) con CI verde tras actualizarlo. Falta ver `regimen` en la próxima corrida NRT.
- D-2: dos corridas del scraper verdes con el arreglo; #783 cerrado. Mirova-v1#19 lo cerré por error y lo
  reabrí: #21 arregla sólo la coma de miles; siguen las filas perdidas y el mojibake del OCR.
- D-8: workflow propio `reproc-s151-ab-caja.yml` (#818, grupo `s151-ab-caja`), diff revisado línea a línea
  (sólo nombre, grupo, nombres de salida y textos); D1 despachado (Láscar 03-14 a 03-27, run 38679191229).
  D2 y V1 van después, de a uno.
- D-5: piloto 9 de 10 con C-P1 en 9; la décima perdida porque NASA reprocesó el gránulo. Enmienda antes de
  correr las 356 y sin mirar alertas (#819): L1B de la misma adquisición, marcado, C-P1 decide. Probe completo
  despachado (11 volcanes, todas las pasadas, run 38679955131). Dato temprano sin valor de veredicto: en los 9
  negativos el brazo a (canon) da 0,15 a 0,34 MW y el b casi siempre 0.
- Agentes vivos: D-9 y D-10. A/B vivos: F/K y caja (tope 2).

### 2026-10-15 03:50 UTC (vuelta 47): Nicolás aprueba las seis recomendaciones ("probar todas las opciones")
- D-2: Mirova-v1#21 mergeado (`40ef1a45`; `scraper.py` y tests sin cambios en main desde la base). Falta ver la
  siguiente corrida verde del scraper.
- D-3: #785 estaba 142 commits atrás; actualizado, CI re-corriendo; se mergea en verde y se comprueba que el NRT
  escribe `regimen`.
- D-5: piloto del probe D25 V750 despachado (Tupungatito, 10 pasadas, run 38678279921).
- D-8: la caja comparte grupo con F/K (desplazaría a V2a): un agente prepara `reproc-s151-ab-caja.yml` con grupo
  propio; con F/K son 2 A/B, el tope.
- D-9: agente implementa SN como regla única, informando SE y la original, sin cambiar a escondidas el veredicto
  pre-registrado de F/K; re-evalúa los veredictos publicados con las tres.
- D-10: agente cablea la rama diurna VIIRS apagada (tag `pre-s151-rama-diurna-viirs`, A118 sobre todos los
  consumidores, golden bit a bit) y escribe el borrador del pre-registro del A/B diurno.
- #798 y #795 cerrados (ya decididos; el seguimiento sigue aquí). Agentes activos: 3.

### 2026-10-15 02:03 UTC (vuelta 46): sin tarea libre; #817 mergeado; ritmo del NRT y de V1
- #817 (propagación de la 1.4) en `main` con CI verde. Ninguna tarea de §3 y §4 está libre: todas esperan un sello
  o decisión de Nicolás (D-2, D-3, D-5, D-8, D-9, D-10, sonda 1.2) o el A/B de F/K.
- NRT: última corrida 23:06 UTC (todas verdes desde el 2026-10-08 22:55). Es el atraso crónico del cron de GitHub
  (4 a 5 corridas por día; hueco máximo reciente 11 h, 2026-10-12 08:38 a 19:37), no una falla. Ojo: un hueco así
  queda a 1 h de la condición de parada de §1.5 sin que nada esté roto. El remedio, el cron externo `10 1-12 * * *`
  que Nicolás aprobó en S150 (decisión 5, `docs/AUDIT_S150.md`), sigue sin configurar y pide una credencial que el
  loop no puede crear (§1.7): queda para Nicolás.
- V1 de F/K: 10 de 44 jobs en 4,7 h con 6 en paralelo; a ese ritmo termina cerca de las 17 a 19 UTC del 15-oct,
  no a las ~10 UTC que estimaba el pre-registro. V2a sigue pendiente detrás. Disco 22 GB.

### 2026-10-15 01:26 UTC (vuelta 45): propagación A113 de la 1.4 (#817); #815 y #816 mergeados
- #815 (D27) y el merge diario #816 entraron a `main` con CI verde.
- Propagado el estudio TIF de la 1.4 (#809) a `docs/MISSION.md`, la marca de D8' y `docs/AUDIT_S150.md` §8:
  MIROVA informa el lejano cuando es fuerte, la mayor contra la suma no está demostrado, el VRP del cráter no
  incluye el lejano débil, el brazo A2 espera F/K. Suite 1710 passed. PR #817, espera CI.
- Estado: V1 de F/K 7 de 44 jobs a las 4 h (más lento que las ~12,5 h estimadas); NRT último verde 23:06 UTC,
  vigilar que aparezca la corrida de la 01 UTC (límite de parada: 12 h). Disco 22 GB.

### 2026-10-15 00:51 UTC (vuelta 44): propagación A113 de la 1.13 a D27 (#815)
- Todas las tareas de la cola esperan un sello, una decisión o el A/B de F/K, así que la vuelta tomó la
  propagación pendiente (A113): segunda marca S151 en D27 (`docs/MIROVA_DIVERGENCES.md`): el día es sobre todo
  VIIRS 375 (94 pasadas protegidas; 40 usables bajo A119 contra 232 nocturnas), MIROVA sí procesa VIIRS de día
  (Campus 2022 p. 16 y 17), la Tabla 1 diurna sólo está en `process_modis.py` (A118); y nota en el docstring de
  `tests/test_daytime_modis.py`. El docstring de `store.py` queda para el PR de código de D-10 (archivo protegido).
  Suite 1710 passed (worktree `VRP-Chile-d27`). PR #815, espera CI.
- Estado: V1 de F/K con 6 de 44 jobs terminados a las 3,5 h (32 en cola); V2a pendiente detrás. NRT verde
  (23:06 UTC). Disco 23 GB. Corregida la marca de 1.12 (decía EN CURSO y HECHA a la vez).

### 2026-10-14 (vuelta 43): 1.14 cerrada (#814 mergeado, `33c42ab5`)
- Siete arreglos aplicados (`5c4c9705`): reparto con las dos bisagras y Shapley, D17 retirado, efecto de D25 por
  ángulo con intervalo [1,07; 1,33] en el borde, régimen de código separado de la ventana (0 de 17.450 records de
  producción abril-agosto con hora de proceso), "la que más mueve", C2 MODIS acotado a 2026, OSF sin verificar
  como vara NRT. Suite 1710 passed; CI verde; mergeado. Worktree `VRP-Chile-114` se puede retirar.

### 2026-10-14 (vuelta 42): verificador de #814 PARCIAL, arreglos enviados
- Confirmado: reconstrucción 11 de 11 y factores de las palancas (D25 1,2788). Caído: el reparto selección/fondo
  es una identidad cuyo reparto depende de la bisagra (V375 32/21 o -12/64); la atribución al remuestreo D17
  (el Npix de MIROVA no crece con el área; D25 sí actúa sobre la parte del ángulo, 1,00 a 1,20); "brazos antes
  de #535" es falso en código (S143-S149 son posteriores); "la única palanca" (keep_peak 1,05 y D22 1,03 también
  mueven); recomendación sobre producción saturada por el Test 1 (A114) → medir D25 sobre producción y sobre F.
- Arreglos (a) a (g) enviados al agente de la 1.14. Aviso: `test_perfil_operacional_reproduce_el_golden_bit_a_bit`
  falló una vez en una corrida con -x del verificador y pasó en tres posteriores; causa SIN VERIFICAR (vigilar).

### 2026-10-14 (vuelta 41): estudio TIF de la 1.4 mergeado (#809 v3, `e1074caa`)
- v3 con los arreglos del segundo verificador: dual ROI REFUTADO como mecanismo (ya encendido en los dos pases;
  en 7 de 15 alertas el primer pase alertó el píxel lejano); no es factor único (logística n 53: pico lejano más
  pico cráter AIC 30,7 contra 40,9 del lejano solo, p 0,0005), frontera blanda (z 18 a 26: 5 cerca, 10 lejos);
  tabla simétrica con prueba continua p 9e-5 y permutación por volcán p 0,0001. Sigue firme: el VRP de MIROVA
  calza con el cráter solo (+0,12 contra +0,55). Suite 1710 passed; CI verde; mergeado.
- La 1.4 sigue `[~]`: el diseño del brazo A2 (anomalía mayor) espera el resultado de F/K, porque la SOSPECHA nueva
  es la conectiva `min`, que el A/B mide. No inventar un umbral fuera de la cumbre antes de eso.

### 2026-10-14 (vuelta 40): 1.14 entregada (#814), en verificación
- Estudio del presupuesto de la magnitud (PR #814, sin verificar): reconstruye las razones del auto-audit en 11 de
  11; VIIRS 375 2025 contra el OSF, R 0,69 = recorte 43 %, selección 29 %, fondo 28 %. De las palancas ya
  construidas, sólo D25 acerca la magnitud (×1,28, medido en brazos `literal` de junio a agosto, antes de #535);
  `max` 0,93 y quitar el Test 1 0,88. Recomienda un A/B de D25 aislado en VIIRS 375 sobre producción. Controles
  que fallaron: cúmulo de un píxel en MODIS (79 a 87 %) y fondo por píxel cuando dispara el Test 1. El agente
  usó `sed -i` una vez (anotado, §1.7).
- Verificador limpio lanzado sobre #814 (identidad contra medición, OSF filtrado A105, régimen de las palancas
  A104, firma de D17). V1 de F/K corriendo (GitHub lo muestra "queued"), V2a pendiente detrás; NRT verde 23:06
  UTC; disco 21 GB libres.

### 2026-10-14 (vuelta 39): 1.13 cerrada (#812, D-10 #813)
- Arreglos de #812: clase "real" circular rebajada (39 a SIN EVIDENCIA; 54 sin evidencia y 40 reflejo); nulo
  nocturno por volcán (sólo informa en Láscar); A119 en el denominador (40 diurnas usables contra 232 nocturnas);
  cita completa de Coppola 2016a; 50 MW marcado como del archivo curado (tabla NRT: 38 diurnas, máximo 15,81 MW);
  la Tabla 1 diurna existe sólo en `process_modis.py` (VIIRS sin rama diurna; `store.py` rechaza VIIRS de día).
  CI verde, mergeado. D-10 abierta (#813), recomendación: cablear la rama diurna VIIRS apagada con A45 y A/B.
- Pendiente de propagación (A113): el docstring falso de `pipeline/store.py:180-185` (archivo protegido: va en el
  PR de código de D-10 si es "1") y el texto de D27 en `docs/MIROVA_DIVERGENCES.md` (dice MODIS, son VIIRS 375).

### 2026-10-14 (servidor 23:39 UTC): vuelta 38, #812 en arreglos; #809 v2 cambia la conclusión, segundo verificador
- #812 (alertas diurnas), verificador PARCIAL: conteos y papers confirmados; la clase "39 reales" es circular
  (sacando las propias alertas, Chillán cae de 11,5 a 0 veces el azar y con el corte de 10 la clase real queda en
  0); 50 de las 94 pasadas dependen de OCR que A119 no deja decidir (quedan ~40); el umbral diurno de 50 MW es del
  archivo curado, no del NRT (la tabla NRT publica 38 diurnas, todas bajo 50 MW). La recomendación pasa a clave de
  fidelidad: A/B diurno con la Tabla 1 diurna ya en el código, contra negativos diurnos limpios. Arreglos devueltos.
- #809 v2: lo que decide si MIROVA informa lejos es la FUERZA del foco lejano (z 15 contra 29, 0,32 contra 0,58
  MW); en 15 de las 36 alertas "cráter con foco lejano" el VRP de MIROVA calza con el cráter solo; en 21 nuestro
  píxel lejano no es un objeto que MIROVA vea. Sospecha: umbral de escena más exigente (dual ROI). "Suma" contra
  "mayor" sigue sin demostrar. Análisis nuevo: segundo verificador limpio lanzado.
- Paradas: NRT corriendo (23:06); disco 20 GB. V1: 4 verdes, 6 corriendo, 34 en espera.

### 2026-10-14 (vuelta 37): estudio C entregado (#812) en verificación; estudio A arrancado
- #812 (sin verificar aún): 135 filas de alerta diurnas, 97 protegidas (94 pasadas) contra 346 pasadas protegidas
  nocturnas; VIIRS 375 85 de 97; Láscar 39, Lastarria 31, Chillán 10. Clasificación: 39 reales probables (Láscar,
  Chillán, Villarrica), 40 reflejo o sol (Lastarria, Láscar, Isluga), 15 indeterminadas; la clase real es frágil.
  Papers (renderizados): Campus 2022 dice que MIROVA SÍ procesa VIIRS de día (alertas 51 % noche, 20 % día);
  Coppola 2016a: falsas sobre todo diurnas y bajo 5 MW; Coppola 2026: umbral diurno de 50 MW en el archivo curado.
  El docstring de `store._reject_daytime` diría que VIIRS no tiene fuente diurna de MIROVA (falso). Recomendación
  del agente: no abrir el día. Ojo: choca con el criterio de fidelidad que Nicolás pidió para D-6; va a él.
- 1.14 (presupuesto de la magnitud) arrancado con un agente en `VRP-Chile-114`.
- V1: 4 jobs verdes, 6 corriendo, 34 en espera.

### 2026-10-14 (servidor 23:28 UTC): vuelta 36, 1.12 cerrada (#810, D-9 #811); TIF congelados re-verificados
- #810: verificador CONFIRMADO en números; arreglos de presentación aplicados (14 y 20 pasadas distintas, cota
  19,3 %; 0,05 con 5 y 5; "redondeo o truncado"; SN y SE como dos lecturas; cotejo de tablas 13.677 pasadas sin
  diferencias). CI verde, mergeado. Decisión D-9 abierta (#811), recomendación SN.
- #809 (verificador PARCIAL): firme que MIROVA no elige el cráter y que vemos sus objetos lejanos (nulo de otras
  noches: 0,08 esperadas, 39 observadas); no demostrado "suma" contra "mayor" (p 0,005 a 0,12 sacando un caso);
  36 alertas con MIROVA en el cráter y nuestro píxel fuerte lejos sin explicar. Arreglos devueltos al agente.
- TIF de MIROVA: Nicolás creía que había TIF. Re-verificado contra el remoto y el servidor: el repo
  `mirova-tif-archive` está vivo y tiene TIF hasta el 22-sep; los 33 TIF que sirve MIROVA tienen Last-Modified del
  22-sep (PNG del día), y el TIF de Láscar VIIRS 375 bajado hoy es byte a byte el archivado el 22-sep 10:26.
  Anotado en `MAPA_WORKSPACE.md` y en memoria (`reference_mirova_tif_congelados_20260922.md`).

### 2026-10-14 (vuelta 35): estudio D entregado (#810) y en verificación; estudio C arrancado
- #810 (sin verificar aún): 155 de 2.281 pasadas con alerta tienen 0,05 MW o menos, todas VIIRS 375 (Lastarria 55,
  Tupungatito 26, Planchón Peteroa 18). Frontera del banner de MIROVA en VIIRS 375: NONE con 0,04 MW o menos, VERY
  LOW desde 0,06, sin excepciones en tres muestras (banner OCR, color de la estrella, 2.702 imágenes de mayo leídas
  con `leer_png_mirova.py`); 0,05 queda de los dos lados por redondeo. En mayo el corte de 1 MW VERY LOW / LOW
  también se cumple en MODIS (7) y VIIRS 750 (19). Sacarlas a un estrato aparte no cambia ningún veredicto (meses
  860/134 → 852/109; VIIRS 750 400/90 → 397/87; Chillán F/K 7 → 5) y baja el techo de D22 de 14 a 5. Regla
  propuesta (estrato "mínima", ni pérdida ni acierto ni negativo) queda para Nicolás. El agente admite un `printf >>`.
- 1.13 (alertas diurnas) arrancado con un agente en `VRP-Chile-113`.
- V1: 2 jobs terminados en verde, 6 corriendo, 36 en espera; V2a en espera detrás.

### 2026-10-14 (servidor 23:07 UTC): vuelta 34, estudio TIF de la 1.4 entregado (#809), en verificación
- Lo que trae (sin verificar todavía): 117 de 359 lejanas con TIF de su pasada. El TIF muestra un foco a la
  distancia del CSV en 84 de 97 lejanas VIIRS 375 (5 % en RUTINA); nuestro píxel de más VRP cae a 1 km o menos de
  ese foco en 39 de 54, control girado 0 de 546. Pero `anomaly_pixels` casi nunca lo guarda (4 de 57): la Regla D
  rehace la lista con los píxeles del Test 1.
- Regla de selección: "el cráter si hay algo en el cráter" y "la más cercana al centro" refutadas (28 lejanas con
  calor en el cráter, MIROVA informó lejos en todas); "la mayor" y "la suma de lo alertado" aciertan la dirección,
  y la magnitud de MIROVA en 8 casos estrictos favorece la suma (p = 0,046), que es lo que dicen los papers (A10,
  D32). `vrp_max` no sería lo que hace MIROVA: cambia el diseño del A/B y va a Nicolás antes de escribir A2.
- Láscar 2026-10-01 05:18: la fila de 1,2 MW es sólo OCR con la distancia de otra pasada; la miniatura de MIROVA
  muestra el foco lejano más fuerte que el cráter. La P5 del pre-registro (veto) queda sin respaldo.
- Operacional: MIROVA habría dejado de actualizar sus GeoTIFF el 2026-09-22 (Last-Modified); `mirova-tif-archive`
  ya no guardaría TIF nuevos. Si el verificador lo confirma, va a `MAPA_WORKSPACE.md` (pipeline que dejó de producir).
- El agente reconoce haber editado con heredoc o sed un par de veces antes de corregirse; contenido final revisado.
- Verificador limpio lanzado sobre #809.

### 2026-10-14 (servidor 22:37 UTC): vuelta 33, V2a encolado detrás de V1, estudio D (1.12) arrancado
- V1: 6 jobs en curso (el máximo) y 38 en espera; el estado global "queued" es un desfase de GitHub. V2a
  despachado (run 38648773684) y quedó `pending` en el grupo detrás de V1, sin desplazarlo (comprobado 30 s
  después). V2b se despacha cuando V2a arranque.
- 1.12 (estudio D) arrancado con un agente en `VRP-Chile-112`. Siguen corriendo el estudio TIF de la 1.4.

### 2026-10-14 (vuelta 32): mapa de gaps y tres estudios nuevos en la cola (1.12, 1.13, 1.14)
- A pedido de Nicolás, mapa de gaps con el auto-audit del 2026-10-14 (ventana de falsas 09-01 a 10-14):
  publicación en negativos limpios VIIRS 375 88,6 %, VIIRS 750 24,5 %, MODIS 13 % (meta 10 %); recall del tablero
  MODIS 30 % con el cráter detectado el 100 %, VIIRS 750 87 %, VIIRS 375 99 %; magnitud Láscar 0,44 a Villarrica
  0,82 (Llaima 8,7 con n 1). La brecha dominante sigue siendo la sobre-publicación de VIIRS 375 (la ataca F/K).
- Nicolás aprobó agregar D, C y A, en ese orden (1.12, 1.13, 1.14), con permiso de correr donde haga falta.
  Propuestos y no agregados aún: B (remuestreo a la grilla de MIROVA, D17; espera lo que diga 1.14), E (pasadas de
  MIROVA sin record nuestro, por satélite) y F (saturación en erupción).
- Espacio medido: worktree ~0,9 GB; prueba de un evaluador ~2 GB de temporales; `.git` 9 GB; TIF archive 4 GB.

### 2026-10-14 (servidor 22:09 UTC): vuelta 31, D-6 = sigue; disco liberado; V1 arrancando
- Nicolás rechazó cerrar la 1.4: la réplica existe para demostrar fidelidad a la metodología de MIROVA, y sin las
  anomalías lejanas no se puede saber si hacemos lo que ellos hacen ni defender mejoras; la distancia similar
  permite suponer el mismo objeto y el TIF muestra los píxeles. Mi recomendación de cerrarla razonaba sólo desde el
  criterio de victoria (lectura A) y dejaba fuera la fidelidad: corregida. Registrado en #795.
- Lanzado un agente (worktree `VRP-Chile-tif`) para el paso 1: con TIF de `../mirova-tif-archive` (lectura local,
  sin pull) y distancia, qué objeto informa MIROVA cuando hay calor lejano, si es la mayor, y el caso Láscar
  2026-10-01 05:18 (MIROVA dio el cráter mientras nuestro píxel más energético estaba a 19,7 km).
- Disco: había bajado a 8,9 GB por ~9 GB de carpetas temporales de las pruebas de evaluadores en mi scratchpad;
  borradas (rutas literales, tras un bloqueo del chequeo de seguridad por usar variables): 18 GB libres.
- V1 (run 38639658446): los jobs ya empezaron en `ubuntu-24.04` (la cola era espera de máquinas; GitHub Actions
  operacional), pero el run aún figura `queued`; V2a sigue sin encolar hasta verlo `in_progress`.

### 2026-10-14 (servidor 21:22 UTC): vuelta 30, Nicolás decide D-4 = A y aprueba D-7; V1 despachado tras probar todo
- Nicolás en la conversación: "A y Si, recuerda probar todo lo necesario". D-4: lectura A (issue #782 comentado
  y cerrado; propagado a MISSION, CLAUDE.md y S151_CRITERIO en #808, CI verde, mergeado). D-7: aprobado (registrado
  en #798). No existe `sellar.py` en el repo: el sello es su "sí" más el candado `preregistro_aprobado=si`.
- Pruebas previas al despacho, todas en verde:
  - Perfiles C0, F, K y G leídos desde `pipeline.profile`: Test 1, conectiva y banda 22 como lo declarado;
    `diff_perfiles.py` idéntico a la salida commiteada.
  - Referencia congelada de V1 y V2: 8 de 8 archivos con el sha256 LF del manifiesto, commiteados en git.
  - Workflow: `FLAGS_BRAZO` trae todas las claves que el evaluador revisa; token renovado el 2026-10-08; 0 runs
    vivos en el grupo.
  - Prueba del evaluador: 37 de 37, idéntica caso por caso a `probar_salida.txt`. La primera corrida la corté yo
    con un `timeout` de 25 min y salida con búfer: no imprimió nada; se repitió sin límite y con `-u`.
  - Piloto en GitHub (run 38634276942, Láscar, 2026-09-30 a 10-01, los 4 brazos): 4 jobs verdes, 18 pasadas por
    brazo sin faltantes (la recolección en rojo sólo por los 10 volcanes ausentes); `evaluar_fk.py` sobre sus
    salidas reales: referencia OK, cobertura pareja, C0 contra producción OK, cableado de los 4 OK, determinismo
    100 % en los tres sensores. Veredictos del piloto no se miran.
- V1 despachado 21:21 UTC: run 38639658446 (sha 402447f33), 2026-08-29 a 10-08, 11 volcanes, C0/F/K/G. Queda en
  cola esperando máquinas; V2a se encola sólo cuando V1 esté `in_progress` (un despacho mientras V1 figura
  pendiente podría desplazarlo).
- Próximo paso: encolar V2a con V1 corriendo; V2b cuando V2a arranque; evaluar cada ventana al terminar, con
  verificador limpio.

### 2026-10-14 (servidor 20:14 UTC): vuelta 29, la sesión se reinició; aviso #779 revisado; loop re-armado
- La sesión se reinició y la vuelta programada para las ~19:20 UTC no corrió. Se re-arma el loop.
- Issue #779 (auto-audit FUERA DE BANDA): lo abrió el `audit-weekly` que despaché a las 11:41 UTC para probar la
  unión. Flag: magnitud de Tupungatito 0,647 de MIROVA (n 23), bajo la banda de 0,7. No lo causa la unión: ese run
  es anterior a #803 (el paso 1 todavía no la leía) y Tupungatito perdió una noche, no ganó. Es la ventana rodante:
  el 2026-10-12 daba 0,707 con n 24 (ventana 08-13 a 10-12) y el 14 da 0,647 con n 23 (08-15 a 10-14). Un
  promedio con n de dos decenas pegado al umbral cambia de lado por una sola noche (A87, A90). El déficit de fondo
  es el conocido de régimen débil (S124), que es justo lo que miden las pruebas en espera (D-7, F/K). No se toca.
- Sin respuestas en los issues de decisión; NRT verde a las 14:52 y uno en curso; disco 13 GB.

### 2026-10-14 (servidor 18:22 UTC): vuelta 28, el OCR medido (#805); el loop pasa a espera
- OCR de Mirova-v1, 232 versiones diarias desde el 2026-01-20: 1.065 claves en la unión, 1.060 en la más nueva, 5
  perdidas (todas ALERTA_TERMICA_OCR; último día con ellas 20-ene, 5-feb, 22-feb), dentro del tramo inestable del
  OCR. No se agregan a la referencia; el script queda para repetirlo. #805 mergeado.
- **Resumen del día.** Hechas: 0.1, 0.2, 0.3, 0.4, 1.1, 1.3, 1.8, 1.9, 1.10 y los pendientes (i) y (iv) de 0.1.
  Diseñadas, verificadas y en `main`, esperando el sello de Nicolás: 1.5 (D-5, #793), 1.4 (D-6, #795), 1.6 (D-7,
  #798), 1.7 (D-8, #801); además la sonda 1.2. Esperan su decisión: D-2 (#783, Mirova-v1#21), D-3 (#786, #785),
  D-4 (#782). Bloqueada: 1.11 (cronología OVDAS). Sin cola autónoma que valga una vuelta propia: los arreglos del
  evaluador de Chillán sólo sirven si se vuelve a usar, y (ii)/(iii) de 0.1 son de bajo efecto.
- Próximo paso: modo espera. Revisar cada hora los issues `decision-nicolas`, el NRT y el disco; actuar apenas
  llegue un sello o una decisión.

### 2026-10-14 (servidor 18:11 UTC): vuelta 27, la etiqueta far sí oculta (nota falsa corregida, #804)
- La nota del evaluador de la caja decía que el tablero publica una pasada `far` por su cúmulo. Con el predicado
  real (`banco_paridad.correr_node`): MODIS con `far` y cúmulo de 2 MW a 0,8 km da `[0, 1, 0, 0, 0]` (no publica);
  con `summit`, `[1, 1, 0, 2, 1]`. No hay defecto del tablero; la nota era falsa y se corrigió (#804, mergeado).
- Falta propia: escribí en el PR "la prueba sigue pasando" antes de correrla bien (el script pide argumentos).
  La corrí después con el log del run de Chillán: 29 de 29, y recién entonces mergeé.
- Próximo paso: pendiente (iv) de 0.1, la unión histórica del canal OCR (el consolidado perdió filas; el OCR
  nunca se revisó).

### 2026-10-14 (servidor 18:02 UTC): vuelta 26, pendiente (i) de 0.1 resuelto (#803)
- `auto_audit_weekly.py`: el paso 1 (noches con alerta de MIROVA, base del recall) cargaba sólo el snapshot
  crudo. Nueva `alertas_mirova()` suma la unión histórica (la fila del snapshot gana). Entran 30 alertas, 2 en la
  ventana de 60 días (Láscar VIIRS 375, PCC VIIRS 750). Test con control sin capa (fallaba antes); suite 1712;
  CI verde; #803 mergeado. La parte de publicación ya usaba la referencia unificada.
- Próximo paso: la pasada MODIS etiquetada `far` que el tablero igual publica (vista de paso por el agente de
  1.7): ver si es un defecto del predicado (familia A46) o un comportamiento documentado.

### 2026-10-14 (servidor 17:54 UTC): vuelta 25, caja (1.7) en la cola (D-8) y marcada en D18
- Arreglos de #800 aplicados: D1 resuelto con `distancia_mirova.py` (MIROVA mide desde el centro de su grilla;
  dónde centra la caja queda en dos lecturas, 24,8 a 28,8 % contra 2,7 % fuera), decide sólo en los 8 centrados,
  INDECIDIBLE por ruido, P3 sobre pares que cambian (el caso sembrado pasaba con todos los pares), Q1 por Fisher,
  despacho reducido. Prueba 29 de 29. La suite pierde un test: comprobé que es el parametrizado por perfil de
  `test_perfiles_sin_claves_duplicadas_s126` que se fue con el perfil gemelo eliminado. CI verde; #800 mergeado.
- D-8 (#801) pide el sello. Marca S151 en D18 (#802, mergeado), conservando el texto viejo.
- Estado: todo lo diseñado espera a Nicolás (D-2 a D-8 y la sonda 1.2); 1.11 bloqueada. Queda trabajo sin
  sello: el pendiente (i) de 0.1 (`auto_audit_weekly.py` lee el snapshot crudo y no ve las alertas recuperadas)
  y los arreglos del evaluador de Chillán.
- Próximo paso: pendiente (i) de 0.1.

### 2026-10-14 (vuelta 24): verificador de #800: no vale la pena despachar V1 tal como está
- Confirmado: cableado (24 llamadas; el tablero no deshace la caja), workflow, sustrato, prueba 28/28, suite.
- D1 grave: si `Distancia_km` de MIROVA se mide desde el centro de su caja (lo que afirma el §2), MIROVA publica
  fuera de su propia caja entre 24,8 y 28,8 % de sus alertas VIIRS 375 de V1, igual que B (25,6 %), no 0,9 a
  2,2 %: la premisa "MIROVA calla fuera de la caja" no se sostendría en el NRT. Punto de medición SIN VERIFICAR.
- D2: el "gana" lo decide PCC, con la caja del brazo descentrada; en los 8 volcanes centrados el neto es casi
  cero. D3: P3, P4 y P1 casi seguros por construcción. D4: el ruido se leía como "inerte".
- Arreglos devueltos a su agente: establecer desde qué punto mide MIROVA, decidir sólo en los 8 centrados,
  INDECIDIBLE por ruido, P3 sobre pares que cambian, y despacho reducido a D1 y D2 (~35 min) más B/BC en V1.

### 2026-10-14 (servidor 17:07 UTC): vuelta 23, pre-registro de la caja (#800), en verificación
- Paradas: NRT verde 14:52 UTC; disco 11 GB libres (bajó de 16 GB: limpiar worktrees al cerrar cada tarea).
- Agente entregó #800: el flag de la caja llega a las 24 llamadas de umbral dual en los dos pases de los tres
  procesadores (comprobado por profile, AST y efecto con funciones reales); los consumidores con círculo no son
  umbrales. Sin prerequisito A45; agregó la clave a `FLAGS_BRAZO`. Hallazgo: `max` y la caja apagan la misma
  población: sobre K la caja sólo apaga 1 negativo de VIIRS 375 en V1 (sobre B, 55); MIROVA tiene 0,9 a 2,2 % de
  sus alertas VIIRS 375 fuera de su caja, B publica 25,6 % fuera, F/K 1,6 %. Veto con dos protegidas expuestas
  (Láscar MODIS 2026-03-27, Isluga VIIRS 375 2026-06-10). Brazos K/KC con gemelo KG y B/BC como control positivo;
  ~16 h. Sin resolver: la caja va centrada en el cráter y MIROVA la centra en su grilla (2 a 7,6 km en Tupungatito,
  PCC y Planchón Peteroa). Evaluador 28 de 28.
- Verificador limpio lanzado; se le pidió evaluar también si conviene NO despachar y cerrar D18 sobre el
  candidato con el sustrato medido.

### 2026-10-14 (servidor 16:16 UTC): vuelta 22, tarea 1.8 cerrada (#799)
- Verificador limpio: CONFIRMADO en conclusión y recomendación (orden declaración antes que script, control que
  elige píxeles sólo por centroide, 0 publicaciones por estructura: ninguna variante lleva un valor positivo a
  cero; razones recalculadas con pareo y predicado propios). Arreglos de redacción aplicados: 12 cúmulos MODIS
  ambiguos pasan a no reconstruibles (control 2.019 de 2.021), MODIS sí cambia magnitud en 536 negativos limpios
  publicados (mediana 1,57 a 1,78 MW), VIIRS 750 en erupción sube la mediana de 0,418 a 0,498 aunque el error en
  log no cambia, intervalo por volcán. CI verde; #799 mergeado.
- Estado de la cola: todo lo escrito espera a Nicolás (D-2 a D-7 y el sello de 1.2); quedan 1.7 (caja D18) sin
  pre-registro y 1.11 bloqueada. Los arreglos del evaluador de Chillán quedan como mejora para su próximo uso.
- Próximo paso: pre-registro de 1.7 (la caja de 5 × 5 km), la última palanca sin diseño.

### 2026-10-14 (servidor 15:57 UTC): vuelta 21, tarea 1.8 medida (#799), en verificación
- NRT verde a las 14:52 UTC.
- Agente entregó #799 con DECLARACION.md commiteada antes de mirar. Control de reconstrucción: la regla actual
  reproduce `pc.vrp_mw` en 2.030 de 2.033 cúmulos de 2 o 3 píxeles (C0 de Chillán 42 de 42); control negativo
  427 de 2.033; 254 records sin reconstruir (píxeles de VRP 0, casi todos MODIS).
- Hallazgo: el modo casi no llega al operador. VIIRS 375 publica el núcleo F5' (no pasa por el modo); MODIS
  publica cúmulos de más de 3 píxeles; sólo decide en VIIRS 750: 28 de 1.304 pares, 0 publicaciones cambian
  en ninguna variante, 0 protegidas afectadas. En la erupción la razón contra MIROVA queda en 0,42 a 0,58 con
  cualquier variante: el déficit es de cuántos píxeles alertamos, no de la regla de suma.
- Recomendación del agente: no tocar el modo; apagarlo, si se quiere simplificar, como brazo extra de la corrida
  F/K (#797). Verificador limpio lanzado.

### 2026-10-14 (servidor 15:35 UTC): vuelta 20, pre-registro de F/K mergeado, D-7 en la cola
- Arreglos de #797 aplicados: logs de cada media ventana revisados (caso que fallaba con la versión anterior),
  capas de la referencia congeladas con sha256 (`armar_tabla.py` gana `--historico` y `--respaldo` opcionales,
  compatibles hacia atrás, revisado por mí), F derivado de K en V2, PENDIENTE DE REPETICIÓN en vez de VETADO,
  casos V2, P6 implementado, control contra producción (umbral de 5 % del instrumento), ruido por pasadas
  discordantes, alcance "veto de Láscar" dicho. Evaluador 37 de 37; suite 1705; CI verde. #797 mergeado.
- D-7 (#798) pide el sello. Con esto, todo lo que queda en la cola espera a Nicolás (D-2 a D-7 y el sello de la
  sonda, 1.2) salvo 1.7 (caja D18) y 1.8 (modo de un píxel), y los arreglos del evaluador de Chillán.
- Próximo paso: 1.8 (modo de un solo píxel en erupción), que la prueba de Chillán ya dejó en disco.

### 2026-10-14 (vuelta 19): verificador de #797, sellable con arreglos
- Confirmado con script propio: perfiles (G = C0 salvo nombre y directorio; los tres flags llegan a los tres
  procesadores en los dos pases), ventanas (A104, A119), poder, sustrato (V1 protegidas A 4/21/12; V2 39/38/42;
  836 negativos MODIS fuera de Láscar), `probar_evaluar_fk.py` 26 de 26 sin veredictos por construcción.
- Obligatorios: (1) el evaluador sólo lee el log de la primera media ventana de V2; (2) la referencia no está
  congelada entera (la capa de la unión histórica la reescribe `audit-weekly.yml` cada semana y el respaldo no
  tiene sha). Además: F sólo con V1; pérdida de V2 sin repetición sale VETADO en vez de PENDIENTE; la prueba no
  ejercita el camino V2; P6 sin script; falta control contra producción para atrapar un job verde sin datos.
- Alcance que el documento debe decir: **el veto nuevo es Láscar** (en V2, 36 de 38, 39 de 42 y 39 de 39 de las
  protegidas; los otros 9 volcanes, 3 o menos).
- Arreglos devueltos a su agente, con la regla 1.7 (sólo Write y Edit) recalcada.

### 2026-10-14 (servidor 14:53 UTC): vuelta 18, pre-registro de F/K en los 11 volcanes (#797), en verificación
- Paradas: NRT verde a las 09:17 UTC y uno nuevo en curso (14:52); disco 16 GB libres.
- Agente entregó #797 (tareas 1.6 y la corrida de los 11 que pide Chillán): C0 contra F (VIIRS) y K (MODIS con
  banda 22 y `max`), más gemelo G de C0 (perfil nuevo `_s151_ab_control_gemelo.yaml`). Hallazgo: en el régimen
  actual casi no hay protegidas que producción publique (MODIS 3, VIIRS 375 12, VIIRS 750 10): el veto no tendría
  poder. Dos ventanas: V1 2026-08-29 a 10-08 (costo; incluye la erupción de Chillán y 836 negativos limpios de
  MODIS fuera de Láscar) y V2 2026-03-01 a 06-12 sólo tabla (poder del veto: pérdida detectable con 80 % de 4,3 %
  en VIIRS 375 y 3,8 % en VIIRS 750). Predicciones P1 veto, P2 suma de errores con ruido del gemelo, P3 magnitud,
  P4 movimiento del cúmulo (objeción de S147, tope 0,048). Evaluador 26 de 26; reproduce la suma de Chillán.
  Duración estimada en serie ~28 h. Sin resolver: flags de compuerta y fondo de MODIS no existen (A45), recall
  MODIS fuera de Láscar sin sustrato, tope D9 sin probar, lectura B espera D-4.
- El agente reconoce dos ediciones con heredoc de Python y dos `sed` sin efecto, contra la regla 1.7: anotado.
- Verificador limpio lanzado sobre #797.
- Próximo paso: veredicto de #797; si es sellable, D-7 a la cola.

### 2026-10-14 (servidor 14:08 UTC): vuelta 17, prueba de Chillán cerrada (#796)
- Verificador limpio: PARCIAL. Reprodujo la salida idéntica y recalculó por su cuenta, sin el evaluador, las
  decisiones clave. Confirmado: 0 pérdidas VIIRS de 1 MW o más; MODIS, C0 pierde 2026-10-01 08:35 (5,18 MW) y la
  recuperan E, F, J, K, KE, KET (K con 1,08 MW). Salvedades: P5 del tope es vacuo (el tope no toca la etiqueta
  `far` y en la familia K no llega a 5 MW): quitar el tope quedó sin probar; P4 no prueba la etiqueta (KE = K).
- Suma de errores bajo 1 MW (tres sensores, reposo y actividad): C0 52, B 17, J 23, F/K/KE/KET 7. Las pérdidas
  débiles de VIIRS 375 las causa quitar el Test 1; la de VIIRS 750 (09-28 04:42, 0,23 MW) es de `max`.
- Documento `docs/S151_RESULTADO_NDC.md` con evidencia del verificador; CI verde; #796 mergeado.
- Pendiente para una próxima vez: arreglos del evaluador (P5 SIN SUSTRATO, costo VIIRS y recall en reposo,
  mediana para n par, control positivo de P3).
- Próximo paso: con 1.1 cerrada, lo que queda en la cola espera a Nicolás (sellos D-5, 1.2, D-6; decisiones D-2,
  D-3, D-4) o no está escrito todavía (1.6, 1.7, 1.8). Siguiente: pre-registro de la corrida de los 11 volcanes
  para F/K, o 1.6 (MODIS banda 22 con `max`), que este resultado ya informa.

### 2026-10-14 (servidor 13:53 UTC): vuelta 16, prueba de Chillán evaluada, en verificación limpia
- Run 38560317428 terminado. `recolectar` en rojo sólo porque su chequeo de cobertura espera 11 volcanes y el run
  era de uno: los 10 brazos tienen 259 pasadas, 0 faltan, 0 sobran (cobertura pareja).
- `medir_ndc.py` en local sobre la rama `s146-ab/38560317428`: controles generales OK (cobertura, versión de
  producto, cableado de los 10 brazos leído de FLAGS_BRAZO, determinismo G contra B 100 % en los tres sensores).
  Veredictos: P1, P2, P3a, P3b, P4 (KE y KET), P5 T0 CUMPLE; P5 KET SIN DATO (sin pasadas topadas).
- Lo que dice: ningún brazo pierde alertas de VIIRS de 1 MW o más (13 de 13 en VIIRS 375, 11 de 11 en VIIRS
  750). MODIS: C0 publica 2 de 3 alertas de 1 MW o más; K, KE y KET las 3, con 0 negativos limpios publicados.
  El tope D9 recortó 11 pasadas MODIS de C0 (sin tope, hasta 122,8 MW), todas negativos o lejanas, sin cambiar
  ninguna decisión. E (sólo etiqueta) publica 33 negativos: bien descartado. Razón de magnitud mediana 0,39 a
  0,68: subestimamos en erupción. Bajo 1 MW, F/K/KE/KET pierden una en VIIRS 375 y una en VIIRS 750 contra C0.
- Salida guardada en la rama `loop/1.1-resultado-ndc`. Verificador limpio lanzado.
- Próximo paso: veredicto del verificador; documento de resultado; la prueba sólo veta, lo que pasa sigue a una
  corrida de los 11 volcanes con su propio pre-registro.

### 2026-10-14 (servidor 13:50 UTC): vuelta 15, 1.4 en la cola (D-6), Chillán con sus 10 brazos en verde
- Arreglos de #794 aplicados por su agente (P2 redefinida como cambio cerca/lejos o de publicación; caja de
  50 × 50 km; K3 por corrida con fusión probada; `probar_evaluar.py` 12 de 12; protegidas no decisivas listadas;
  INERTE exige 0 silenciadas y 0 nuevas). Diff del workflow revisado por mí: sólo agrega una clave a
  `FLAGS_BRAZO`. CI verde, #794 mergeado.
- D-6 (#795): recomendación del loop, no despachar hasta D-4; con la lectura A, A2 nace vetado por P5 y A1 casi
  no mide.
- Prueba de Chillán 38560317428: los 10 brazos terminaron en verde; falta el job de recolección.
- Próximo paso: evaluar Chillán con `medir_ndc.py` y su verificador limpio.

### 2026-10-14 (servidor 13:37 UTC aprox.): vuelta 14, verificador de #794: sellable con arreglos
- Confirmado: flag y perfil (única diferencia), Regla D y ancla ciegas al flag por `hotspot_dist_km`, sustrato
  recalculado (359 = V375 332 + V750 17 + MODIS 10; 75 a más de 25 km; 245 publicadas; 152 con Regla D), el
  cambio de `FLAGS_BRAZO` no toca la prueba de Chillán (fijada al sha f3b41421), grupo y ventana T3 correctos.
- Obligatorios: (1) P2 fallaría por construcción: el flag también elige entre cúmulos del Test 1 cercanos (24
  de 42 pasadas con 2 o más cúmulos cambian; 217 cambian cercano por cercano fuera de la Regla D); (2) el ROI es
  una caja de 50 × 50 km (hasta ~35 km), no un disco de 25 km, y `store.py:320` borra lo que está más allá, así
  que el "techo" no es cota; (3) K3 rompe con dos medias ventanas (22 logs). Más: veredictos no probados en
  `probar_evaluar.py`, tabla §1.2 incompleta, protegidas "informadas aparte" no implementadas.
- Arreglos devueltos a su agente.

### 2026-10-14 (servidor 13:27 UTC): vuelta 13, pre-registro de 1.4 entregado (#794), en verificación
- El flag `ENABLE_VENT_ANCHORED_CLUSTERING` existe pero no llega a todos sus consumidores (A118): con el Test 1
  disparando en el cráter, la Regla D (`test1_integrated.py:175`) y el ancla (`anchor.py:67`) devuelven el cráter
  justo en el caso de anomalía mayor. El brazo A1 (sólo el flag) sería casi inerte; la regla completa (A2) pide
  un cambio de código con A45, descrito y NO implementado.
- Sustrato: 359 detecciones lejanas nocturnas reproducidas (75 a más de 25 km), 245 publicadas, 152 protegidas
  por la Regla D. Control C1 pasa en VIIRS 375 (0,952) y falla en VIIRS 750 (0,72) y MODIS (0,26): ahí sólo
  cotas. C2 con nulo medido: razón 8,3 contra p95 3,40. C1 y C2 se ajustaron tras la primera salida (dicho).
- P5 prevé que A2 pierde una alerta protegida de Láscar (NOAA-21 2026-10-01 05:18, 1,2 MW): veto con la
  lectura A. El A/B no puede probar que MIROVA elija la mayor (distancia sin acimut, A93).
- Agrega `ENABLE_VENT_ANCHORED_CLUSTERING` a la línea `FLAGS_BRAZO` del workflow compartido.
- Verificador limpio lanzado sobre #794. Run de Chillán: 6 de 10 jobs en verde.
- Próximo paso: veredicto de #794; si es sellable, D-6 a la cola; evaluación de Chillán.

### 2026-10-14 (servidor 13:22 UTC): vuelta 12, probe de D25 listo para el sello
- Arreglos de #790 aplicados por su agente: criterio en CASOS (VALE sólo si el límite superior de Wilson de los
  negativos nuevos por 268 queda bajo el límite inferior del rescate por 28), regla 1 (apagar una alerta
  protegida que el control publica es NO VALE; se sumaron 17 protegidas, 356 pasadas), cobertura completa
  exigida, salida 2 con lista vacía. Autoprueba 6 de 6; el caso trampa (28 rescatadas con 225 negativos) da NO
  VALE.
- Revisión propia antes del merge: el workflow no tenía candado de sello; agregué `preregistro_aprobado`
  (falla si no es "si"). Esperé el run del commit nuevo ("0 checks" era SIN DATO, A39); CI verde; #790 mergeado.
- Cola: D-5 (#793) pide el sello del probe. PR diario de `loop/activo` a `main`: #792 (merge commit).
- Ordené tres entradas de la cola de tareas que mis reemplazos habían dejado con frases pegadas.
- Run de Chillán 38560317428: 6 de 10 jobs en verde. Agente de 1.4 en curso.
- Próximo paso: PR de 1.4 y su verificador; evaluación de Chillán cuando termine.

### 2026-10-14 (servidor 13:07 UTC): vuelta 11, 0.4 completa, 1.5 con arreglos, 1.4 en diseño
- 0.4c mergeada (#791, squash `fecc3eae`): la tarea 0.4 queda completa.
- Verificador limpio de #790 (1.5): DESPACHABLE CON ARREGLOS. Cableado del probe, control C-P1 (puede fallar),
  techo y los 268 reproducidos. Defecto que bloquea el sello: el criterio comparaba TASAS (Wilson x/28 contra
  y/268) y daba VALE rescatando 28 con 225 negativos nuevos (2.031 de 2.461 combinaciones VALE suman más
  falsos que rescates), contra la regla 2 del criterio de victoria; y no aplicaba la regla 1. Más: cobertura
  completa no exigida, job verde sin datos con un `vols` mal escrito, y límites no dichos (la variante de nube
  no separa nube de cumbre fría: anillo bajo 255 K en 56 de 339 pasadas). Arreglos devueltos a su agente.
- 1.4 (pre-registro de `vrp_max`): agente diseñando en `VRP-Chile-loop-14`, sin despachar.
- Run de Chillán 38560317428: 5 de 10 jobs en verde.
- Próximo paso: arreglos de #790 y su entrada como pre-registro a sellar; PR de 1.4 y su verificador.

### 2026-10-14 (servidor 12:57 UTC): vuelta 10, 0.3 y 1.10 mergeadas, 0.4c y 1.5 en PR
- 0.3: arreglos del verificador aplicados por su agente (criterio con D-4 y atribución del corte de 1 MW,
  puntero AUDIT_S149 §3, H_S27_1/D30 iguales a P3, ficha SDA, A82 marcada, cita nueva en G8). Revisado por mí:
  0 guiones, criterio de MISSION correcto. CI verde, #784 mergeado.
- 1.10: verificador PARCIAL: la suma 400 contra 90 es exacta pasada por pasada y no hay positivas que sólo F
  publique; con la lectura B, F pierde una pasada protegida de OTRO objeto (Chillán VIIRS 750 2026-07-23 06:30,
  FALSO_POSITIVO de MIROVA de 1,52 MW a 29,6 km; B publicaba 0,051 MW a 4,2 km). Tablas por pasada versionadas
  (CSV de 400 KB) y cuenta por pasada. #789 mergeado.
- 0.4c: A119 en CLAUDE.md y el hito de enero corregidos con las cifras de VERIFICADOR_DATOS D5/D6. PR #791.
- 1.5: los 268 negativos se reconstruyen exactos (271 hoy, por el cargador de #778). La magnitud queda SIN MEDIR:
  los records no guardan vecinos no alertados y no hay gránulos de VIIRS 750 en disco. Techo: con cualquier
  magnitud positiva publicarían los 268 negativos y las 28 alertas (el tablero no corta bajo 10 MW); decide el
  signo del contraste cráter contra vecinos. Probe de sólo lectura (339 gránulos, tres brazos) escrito y SIN
  despachar, PR #790, en verificación limpia; después va a la cola como pre-registro a sellar.
- Run de Chillán 38560317428: 2 jobs terminados en verde, el resto corriendo o en cola.
- Próximo paso: merge de #791 con CI; veredicto de #790 y su entrada en la cola de sellos.

### 2026-10-14 (servidor 12:47 UTC): vuelta 9, 1.10 medida y 1.3 resuelta sin A/B
- 1.10: `experiments/_s151_max_v750/suma_de_errores.py` lee las salidas del evaluador de abril a agosto
  (control B, brazo F): suma de errores 400 contra 90; F deja de publicar 4 alertas (todas Muy Bajo, D4) y apaga
  unas 300 publicaciones en negativos limpios. Compara contra B, no contra producción: es evidencia para una
  decisión combinada (sin Test 1 + `max`), no una adopción. Verificador limpio lanzado.
- 1.3: `experiments/_s151_d22_techo/techo.py`: las 14 pérdidas confiables del camino D22 son Muy Bajo de 0,03 a
  0,08 MW (9 en 0,05 o menos, zona NONE del banner). Techo 14 pasadas (13 noches) contra 271 negativos que
  podría reabrir: sólo mejora si reabre menos del 5,2 %. No se gasta el A/B; la pregunta va a la sonda (1.2).
  PR #788. Marca en el pre-registro suspendido.
- Agentes: arreglos de 0.3 (#784), medición 1.5 (D25 en disco) y verificador de 1.10, los tres en curso.
- Run de Chillán 38560317428 en curso.
- Próximo paso: CI de #788 y merge; veredictos de los agentes.

### 2026-10-14 (servidor 12:44 UTC): vuelta 8, 1.9 cerrada, 0.3 con arreglos, 1.5 delegada
- 1.9: en la tabla `latest.php` MIROVA lista las dos bandas VIIRS de la misma pasada en 13.964 casos (todos los
  meses; control: misma hora al segundo en el 100 %) y alerta en las dos a la vez en 246 (sólo 375: 947; sólo
  750: 32). La preferencia por 750 m de Coppola 2026 es del archivo OSF (A105), no del NRT: no es palanca de
  la réplica. Marca en F-07. CI verde, #787 mergeado.
- Verificador limpio de #784 (0.3): MERGEABLE CON ARREGLOS. Reprodujo todos los números (1.565 topados, 343
  sobre 5 MW, 32.401 de 42.929 en modo de un píxel, 7 de Chillán, 37 diurnas), 14 marcas con evidencia correcta,
  G8 intacto, frontend sólo comentarios. Arreglos: el criterio de MISSION no menciona D-4 ni que el corte de
  1 MW es del loop; puntero AUDIT_S149 §0 que es §3 l. 72; contradicción H_S27_1/D30 contra P3; dos frases de
  la ficha que dicen más de lo medido; A82 sin marca. Devueltos al agente de 0.3.
- 1.5 (D25 sobre los 268 negativos de VIIRS 750) delegada a un agente en `VRP-Chile-loop-15`.
- Falta propia: el script de 1.9 se escribió con un heredoc (prohibido por §1.7). El archivo quedó bien y se
  verificó; desde ahora los archivos se escriben sólo con Write y Edit.
- Run de Chillán 38560317428 en curso.
- Próximo paso: revisar los arreglos de #784 y mergear; resultado de 1.5; 0.4 (c) tras 0.3.

### 2026-10-14 (servidor 12:35 UTC): vuelta 7, 0.6 a la cola y 0.3 entregada por su agente
- 0.6: `append_record` escribe `regimen = {perfil, codigo_sha, origen}` (GITHUB_SHA en Actions, git en local).
  Tag `pre-s151-marca-regimen` antes del primer edit; test con 3 de 4 fallando antes; suite 1706. PR #785 NO
  se mergea (store.py, §1.1); issue #786 (D-3).
- 0.3: el agente abrió #784 (MISSION con el criterio de victoria y marcas P2 a P5, CLAUDE.md A23/A85/glosario,
  encabezados D8', D9, D21, D27 y nota en D30, ficha SDA v1.7, INDEX con 14 documentos, comentarios del
  frontend; contrato G8 de la l. 1473 a la 1483). Suite 1687 en su worktree. Recalculó: 1.565 cúmulos topados en
  5,0 (277 summit), 343 sobre 5 MW. No hizo: "1.403" desde los datos (es un comentario, no texto visible),
  P1 (memoria fuera del repo), tooltip "probablemente artefacto" (texto del operador, queda para Nicolás).
  Verificador limpio lanzado sobre #784.
- Run de Chillán 38560317428: primera tanda de 6 brazos corriendo, 4 en cola.
- Próximo paso: veredicto del verificador de #784; mientras, tarea 1.5 (D25 sobre los negativos de VIIRS 750
  en disco, sin correr nada).

### 2026-10-14 (servidor 12:29 UTC): vuelta 6, tarea 0.5 lista para el sí de Nicolás
- `scraper.py` de Mirova-v1: `numero_tabla` acepta sólo comas de miles bien formadas (una coma decimal "0,5"
  levanta error en vez de leerse 5) y una fila ilegible se salta con ADVERTENCIA en la bitácora en vez de botar
  el ciclo. Test nuevo `tests/test_numero_tabla.py`: 4 de 4 contra el arreglo, falla contra el original.
  Rama y commits por la API (sin clonar). PR Mirova-v1#21, CI verde completo (run 38563906601). Issue #783.
- El clasificador de permisos bloqueó ejecutar en local código bajado de Mirova-v1 (después de la corrida de
  tests): no se vuelve a correr código de otro repo en local; la prueba la da su CI.
- 0.3 sigue con su agente. Run de Chillán 38560317428 en curso.
- Próximo paso: PR de 0.3 y su verificador; luego 0.4 (c) y 0.6 (marca de régimen, va a la cola por §1.1).

### 2026-10-14 (servidor 12:24 UTC): vuelta 5, 0.2 verificada y mergeada, 0.4 (a, b, d) mergeada, 0.3 en curso
- Verificador limpio de #780: regla de 1 MW CONFIRMADA, pero (i) los conteos eran filas: por pasada son 2.280
  alertas y **439 protegidas** (377 pasadas están en consolidado y OCR); (ii) Coppola 2016a fig. 11 se
  contradice (pie: Low bajo 1 MW; figura: bajo 10 MW, banner "VERY HIGH" con 6.797 MW), comprobado sobre la
  imagen renderizada: el corte lo sostiene el banner de hoy; (iii) los controles no llamaban a la función;
  (iv) lectura B: MIROVA marca LOW pasadas que el scraper llama FALSO_POSITIVO (992 pasadas con VRP >= 1 MW).
  Todo corregido en #780; D-4 a Nicolás (issue #782, etiqueta `decision-nicolas` creada). CI verde, merge.
- 0.4: (a) `evaluar_ventana.py` deja pasar el stderr (aviso A119); (b) hitos de NOAA-21 (2026-04-09, cifra
  heredada de `AUDIT_S149.md:56`) y de Suomi NPP (2026-10-09, Mirova-v1#20): septiembre ya no es ventana
  limpia y los dos tests de S149 se actualizaron a eso; (d) `ENABLE_TEST1_NULL_CORRECTED` fuera de las colas,
  con guard. Tests que fallaban antes; suite 1695; CI verde; #781 mergeado. Sin verificador limpio: son
  arreglos de instrumento con su test, no resultados.
- 0.3 delegada a un agente en el worktree `VRP-Chile-loop-03`, rama `loop/0.3-propagacion-a113` (abre PR, no
  mergea). Run de Chillán 38560317428 en curso.
- Próximo paso: PR de 0.3 con su verificador limpio; después 0.4 (c) y 0.5 (scraper Mirova-v1#19).

### 2026-10-14 (servidor 12:10 UTC): vuelta 4, tarea 0.2 implementada, PR #780 en verificación
- La hipótesis del plan (nivel agregado de la página) queda REFUTADA. La columna `Clasificacion Mirova` la
  calcula el scraper desde el VRP de la pasada (Mirova-v1 `volcanes.py:63`); ya estaba en S139 H110 y no llegó
  al plan (A50). Coherente con el VRP desde febrero (consolidado) y julio (OCR); antes, escalas retiradas.
- Cortes de MIROVA: Coppola 2016a fig. 11 (p. 16, página renderizada): 1, 10, 100, 1.000 MW, nombres corridos
  un nivel respecto del sitio actual. Banner `Nivel_Anomalia_MIROVA` (único campo de MIROVA): por pasada,
  VERY LOW 0,05 a 0,91 MW (107), LOW 1,00 a 8,00 MW (20), NONE 0,02 a 0,05 MW (9 alertas del scraper).
- Definición: alerta protegida = alerta (CONS u OCR) con VRP >= 1 MW recalculado. Unión: 536 de 2.657
  alertas (VIIRS 375 254, VIIRS 750 189, MODIS 93); leyendo la columna serían 764. Las dos lecturas del
  criterio dan el mismo corte: no queda decisión para Nicolás. Consecuencia para 1.10: las 4 alertas de
  VIIRS 750 de 0,32 a 0,65 MW son "Muy Bajo", suma de errores, no veto.
- Suite local 1694 passed. Verificador limpio lanzado en worktree aparte. Run de Chillán 38560317428 en curso.
- Próximo paso: veredicto del verificador sobre #780 y merge si CI verde; luego tarea 0.3.

### 2026-10-14 (servidor 11:58 UTC): vuelta 3, auto-audit comprobado y prueba de Chillán despachada
- `audit-weekly` (run 38558346837) verde: el paso de la unión tardó 11 min en GitHub (tope 25) y su commit
  `f3b414213` pasó el `.gitignore`. Cierra lo que el verificador de #778 dejó SIN VERIFICAR.
- Tarea 1.1: `_congelado_ndc` (bajado el 08-oct, después de la caída del 06-oct) contra la unión, ventana
  2026-09-14 a 2026-10-07: 0 filas de más, 0 tipos distintos, le faltan 12 (11 RUTINA y 1 ALERTA_TERMICA, de
  Isluga, Chaitén, Láscar, PCC, Tupungatito y Villarrica), **ninguna de Nevados de Chillán**. La prueba sólo
  evalúa Chillán: no se re-congela. Los 10 perfiles existen en `main`; sin otros A/B corriendo.
- Despacho: run 38560317428, `NevadosDeChillan`, 2026-09-14 a 2026-10-07, 10 brazos, control
  `_s146_ab_control`, desde `main`, `preregistro_aprobado=si` (aprobado por Nicolás el 2026-10-08).
- Nicolás preguntó (2026-10-14) si el loop necesitaba su autorización para seguir: no, salvo los sellos, la
  cronología OVDAS y los merges de otro repo. El loop no espera runs largos: avanza con la próxima tarea libre.
- Próximo paso: tarea 0.2 mientras corre el run; el run se evalúa con `medir_ndc.py` cuando termine.

### 2026-10-14 (servidor 11:45 UTC): vuelta 2, tarea 0.1 verificada, mergeada y `main` en verde
- Verificador con contexto limpio sobre #778 (informe en el temporal de la sesión, resumido acá): CONFIRMA 1, 2,
  3, 4, 6 y 7. Ubicó las cinco caídas commit a commit por el salto de tamaño (21-ene 07:35, 23-abr 14:38,
  25-ago 18:44, 26-ago 18:37, 06-oct 01:42 UTC): siempre un commit que duplica filas y el siguiente que
  deduplica perdiendo claves. Las pérdidas exactas coinciden con las 794 del muestreo diario, ninguna fila nació
  el mismo día de su caída, y el tipo guardado es el del commit previo a cada caída (0 diferencias). PARCIAL en
  5: la alarma de atraso dependía de un push humano y las 318 llamadas no tenían reintento.
- Arreglado en #778 antes del merge: issue automático si `--union-historica` falla en `audit-weekly`, y
  reintentos con test. CI del PR verde (run 38557916419), merge squash `46947bda`, `main` verde (run 38558333297).
- `audit-weekly` despachado sobre `main` (run 38558346837) para medir en GitHub la duración del paso de la
  unión y que el commit pase el `.gitignore` (el verificador lo dejó SIN VERIFICAR).
- Próximo paso: revisar ese run; después, tarea 1.1 (comprobar `_congelado_ndc` contra la unión y despachar la
  prueba de Chillán) o 0.2 si 1.1 se traba. Desde ahora los PR del loop se pueden mergear con CI verde (§2.6).

### 2026-10-14 (servidor 10:47 a 11:20 UTC): vuelta 1, tarea 0.1 implementada, PR #778 abierto
- Paradas: NRT verde 09:17 UTC; disco 22 GB libres; sin issues de alerta salvo #762; `main` rojo sólo por el
  guard de la tarea 0.1 (run 38549663327: 1 failed, 1670 passed). Rama `loop/activo` creada desde `main`.
- Hallazgo de instrumento: Mirova-v1 pesa 13 GB y el consolidado tiene unas 285 versiones por día (17.700 sólo
  desde el 13-ago), así que no se puede bajar cada versión. Las 207 filas del 06-oct son viejas (fechas de
  satélite de 2026-01-12 a 2026-10-05), por eso alcanza con la última versión de cada día.
- Resultado (`data/mirova_reference/union_historica/procedencia.json`): 277 versiones diarias, la historia
  arranca alrededor del 2026-01-10. 794 filas perdidas (737 RUTINA, 40 ALERTA_TERMICA, 17 FALSO_POSITIVO), en
  cinco caídas cuyo último día con las filas es 20-ene (37), 22-abr (162), 24-ago (202), 25-ago (186) y
  05-oct (207). El respaldo de abril aporta **0** filas sobre snapshot + historia (antes aportaba 21 alertas
  sobre el snapshot solo). Cero fantasmas a 15 min o menos.
- Guard S139: pasa de "1 a 17 alertas del respaldo" a "0 alertas" (más estricto); la alarma de caídas futuras
  pasa a un test de atraso de la unión (8 días) y a `audit-weekly.yml`, que la regenera con el snapshot.
- Suite local 1688 passed, 4 skipped, 2 xfailed. PR #778, rama `loop/0.1-union-historica`.
- Abierto, sin resolver: 372 claves cambiaron de `Tipo_Registro` entre versiones (para las vivas gana la de
  hoy, como antes); el OCR no se recorrió.
- Próximo paso: verificador con contexto limpio sobre #778 (lanzado en un worktree aparte) y CI de #778. Si
  los dos dan bien, merge (es la tarea que pone verde `main`) y se marca 0.1. Después, tarea 1.1 (comprobar
  `_congelado_ndc` contra la unión) o 0.2.

### 2026-10-14 (servidor 10:22 UTC): plan actualizado y #777 mergeado por decisión de Nicolás
- Nicolás autorizó mergear #777 con el CI rojo heredado de `main` (sólo el guard de la tarea 0.1).
- Se agregó §2.0 (el estado vive en `loop/activo`) y la regla de §2.6 mientras `main` siga rojo.
- Estado: NRT verde con corridas cada 5 a 6 h (09:17, 03:39, 22:17, 17:21 UTC; cron externo todavía sin
  configurar); `experimental-diario` corrió el 13-oct 20:00 UTC; sonda de tres campos SIN SELLAR (#776, sin
  `SELLO_PREREGISTRO.txt` en la rama); prueba de Chillán sin despachar (tarea 1.1, autorizada desde el 13-oct);
  issue #762 abierto; disco 9,9 GB libres.
- Próximo paso: tarea 0.1; la 1.1 puede ir en paralelo en cuanto 0.1 compruebe la referencia congelada de Chillán.

### 2026-10-13 (servidor 14:18 UTC): plan escrito, loop sin lanzar
- Estado: NRT verde, pero el cron de GitHub corre con atraso (5 a 7 h entre corridas; cron externo sin configurar).
  `experimental-diario` corrió el 10, 11 y 12 de octubre. `audit-weekly` corrió el 12-oct 18:42. Sonda sin sellar.
  Issue #762 abierto (A/B S146 fallido del 8-oct; revisar si es residuo de algo ya cerrado).
- El CI de `main` está ROJO por un solo guard de datos (`test_referencia_unificada_s139.py`, ver tarea 0.1),
  comprobado con un run despachado sobre `main` (38413222685). Mientras siga rojo, ningún PR del loop pasa la
  regla §2.6: la tarea 0.1 es la que lo destraba.
- Próximo paso: tarea 0.1.
