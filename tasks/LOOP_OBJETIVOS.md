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
  EVIDENCIA_DIARIA a RUTINA del 21-ene; (iv) el OCR no se recorrió.
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

- [x] **1.3 A/B de D22, pre-registro v2.** RESUELTA SIN A/B 2026-10-14 (#788): las 14 pérdidas confiables son
  Muy Bajo (0,03 a 0,08 MW); techo 14 pasadas contra 271 negativos reabribles; sólo gana si reabre menos del
  5,2 %. La selectividad la mide la sonda (1.2). Texto original: Con la tabla sola, el camino D22 pesa 12 de 24 pérdidas débiles de
  `max` (VERIFICADOR_DATOS D3). Rehacer el pre-registro suspendido (`experiments/_s150_ab_d22/PREREGISTRO.md`)
  con los hallazgos de su verificador (`docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md`), el criterio de §1.2 y
  la referencia de 0.1; verificador limpio; sello de Nicolás; despacho.

- [~] **1.4 A/B de anomalía mayor (`vrp_max`) contra `vent_anchored`** PRE-REGISTRO en `main` (#794, `1795676b`,
  verificado con arreglos); ESPERA a Nicolás (D-6, #795): A1 casi inerte (el flag no llega a la Regla D ni al
  ancla), A2 necesita código (A45) y P5 prevé un veto con la lectura A. (decisión de Nicolás para la réplica).
  Universo de comparación: 359 detecciones lejanas nocturnas de MIROVA, no 858 (VERIFICADOR_DATOS D2); la
  clasificación NULO la escribe el scraper. Medir distancias desde el cráter y no desde el catálogo
  (`process_viirs.py:754`, AUDITOR_F1). Pre-registro, verificador, sello, despacho.

- [~] **1.5 D25, fondo por vecinos, primero sin correr nada:** sobre los 268 negativos de VIIRS 750 ya en disco
  (`AUDIT_S149.md:139`). ESTADO 2026-10-14: magnitud SIN MEDIR (no hay vecinos en records ni gránulos en disco);
  techo: cualquier magnitud positiva publicaría los 268 negativos y las 28 alertas. Probe de sólo lectura (356
  pasadas) en `main` (#790, `2b6a1be8`), verificado, con candado; ESPERA el sello (D-5, #793). El descarte de vecinos nublados bajo 255 K es de Coppola 2014 p. 3412, no del canon
  2016a (VERIFICADOR_DATOS D9): medirlo como variante, no como "lo que exige el paper".

- [~] **1.6 MODIS: banda 22 junto con `max`** PRE-REGISTRO de F y K contra producción en los 11 volcanes en `main`
  (#797, `2c174b5b`, verificado con arreglos); ESPERA el sello (D-7, #798). Los flags de compuerta y de fondo de
  MODIS siguen sin existir (A45). Texto original: con los flags de compuerta y de fondo que le faltan a MODIS
  (`audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:285`). En MODIS, `max` solo apaga el detector (S147).

- [~] **1.7 La caja de 5 × 5 km (D18)** PRE-REGISTRO v2 en `main` (#800, `d5bc604f`; marca en D18 #802),
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

## 5. Cola de decisiones para Nicolás (el loop agrega; Nicolás responde en el issue)

| # | decisión | evidencia | PR / tag | issue |
|---|---|---|---|---|
| D-1 | Adoptar conectiva `max` en VIIRS 375 (criterio §1.2 por medir en 0.2) | `docs/S150_RESULTADO_MESES.md`, `docs/audit_s150/meta/AUDITOR_F2_NUMEROS.md` | pendiente | pendiente |
| D-2 | Merge del arreglo del scraper Mirova-v1#19 (tarea 0.5) | CI verde de Mirova-v1#21; 4 tests | Mirova-v1#21 | #783 |
| D-3 | Marca de régimen en `store.py` (tarea 0.6) | 4 tests, 3 fallaban antes; suite 1706 | #785, tag `pre-s151-marca-regimen` | #786 |
| D-4 | Alerta protegida: lectura A (alertas del scraper, 439 pasadas, recomendada) o B (todo VRP >= 1 MW, 992) | `docs/S151_CRITERIO_CLASE_MIROVA.md` §5 | #780 | #782 |
| D-5 | Sello del probe de D25 en VIIRS 750 (tarea 1.5); pilotear Tupungatito con 10 pasadas | `experiments/_s151_d25_v750_disco/README.md`, verificador limpio con arreglos | #790 | #793 |
| D-6 | A/B de anomalía mayor: sello de A1 y si se implementa el código de A2 (recomendación: esperar D-4) | `experiments/_s151_ab_vrp_max/PREREGISTRO.md`, verificador limpio con arreglos | #794 | #795 |
| D-7 | Sello del A/B de F y K contra producción en los 11 volcanes (V1 costo, V2 veto; ~28 h) | `experiments/_s151_prereg_fk_11/PREREGISTRO.md`, verificador limpio con arreglos | #797 | #798 |
| D-8 | Sello del A/B reducido de la caja (D1/D2 con K/KC, ~35 min; V1 con B/BC, ~6 h) | `experiments/_s151_prereg_caja/PREREGISTRO.md`, verificador limpio con arreglos | #800 | #801 |

## 6. Bitácora (la más nueva arriba; una entrada por vuelta)

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
