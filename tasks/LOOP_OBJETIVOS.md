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
5. **El loop se detiene solo si:** disco libre bajo 3 GB (`df -h /c`), el token de Earthdata falla, el NRT de
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
1. `gh api -i repos/MendozaVolcanic/VRP-chile | grep -i ^date` (hora del servidor, A86); `git fetch origin
   --prune`; `git checkout loop/activo && git merge --no-edit origin/main`; `df -h /c`.
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
- [ ] **1.21 (agregada por el loop el 2026-10-16, del resultado de la 1.17) MxD03 junto con la etiqueta desde el
  cúmulo.** El probe 1.17 dio PIERDE PROTEGIDA por la letra, pero las 2 pérdidas vienen de que `distance_class` sale del
  hotspot final (`ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`), no de la posición. Probe de tres brazos sobre la
  misma población (C; MxD03; MxD03 + etiqueta desde el cúmulo), con la regla 1 como compuerta, el término a lo largo
  de la traza agregado al modelo de corrimiento y un brazo con ruido de posición como control real. Pre-registro,
  verificador, sello de Nicolás. Informe del verificador de la 1.17 en `verif_117r`.
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

## 5. Cola de decisiones para Nicolás (el loop agrega; Nicolás responde en el issue)

| # | decisión | evidencia | PR / tag | issue |
|---|---|---|---|---|
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
| D-16 | W2a del A/B diurno: el intento 2 solo es completo y parejo (1.085 noches por brazo), pero `unir_intentos.py` (#841) bloquea Copahue `_s151_ab_diurno_on` porque un record MODIS Aqua (2026-06-18 07:30) difiere en un campo de decisión entre intentos del MISMO commit: `final_hotspot_source` test1 contra cluster_rescue, hotspot a 20,31 contra 0,94 km, `vrp_mw` 4,782 contra 1,834; los 11 `anomaly_pixels`, `distance_class` (summit), `primary_cluster.vrp_mw` (1,834) y la BT máxima (274,29 K) idénticos. SOSPECHA: empate de BT máxima desempatado según la CPU. Opciones: (a) usar el intento 2 entero e informar el record; (b) repetir Copahue otra vez; (c) arreglar el desempate en producción (A45). Recomendación: (a) para W2 y (c) como tarea propia | bitácora vuelta 127 | | pendiente |
| D-15 | Commit de V2b de F/K: el pre-registro dice `--ref main` (`PREREGISTRO.md:139`), pero desde el commit de V1 y V2a (`402447f3` y `7b74435e`, mismo `pipeline/`) entraron #785 (marca de régimen en `store.py`), #821 (rama diurna apagada por flag, `process_viirs_mod.py`) y #822 (perfiles diurnos). Con `main`, la ventana V2 mezclaría dos pipelines (A108). Recomendación del loop: despachar V2b desde un tag en `7b74435e` | `git diff --stat 7b74435ed origin/main -- pipeline/` | tag propuesto `s151-fk-v2-codigo` | pendiente |
| D-14 | Sello del probe 1.21 (C, CC, M, MC, R, RC) y merge de #840 (el clasificador de permisos le negó el merge al loop el 2026-10-16) | `experiments/_s151_mxd03_cumulo_121/README.md`, verificador limpio en dos vueltas (`experiments/_s151_mxd03_cumulo_121_verif/`) más revisión del último diff | #840 (`2d9be9a9`) | pendiente |
| D-11 | ~~Sello del probe 1.17~~ **SELLADO** (Nicolás, 2026-10-16); run 38894508138 sobre `d9b10482` (incluye #837) | Sello del probe 1.17 (posición MODIS con MxD03 en los 11 volcanes; regla 1 como compuerta) | `experiments/_s151_mxd03_etiquetas/README.md`, verificador limpio en dos vueltas (`experiments/_s151_mxd03_etiquetas_verif/`) | #834, #835, #837 | pendiente |

## 6. Bitácora (la más nueva arriba; una entrada por vuelta)

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
