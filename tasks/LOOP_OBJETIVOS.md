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
  `main` verde en el run 38558333297). Pendientes que deja: (i) `auto_audit_weekly.py` lee el snapshot crudo
  con `load_mirova_alertas` y no ve las 40 alertas recuperadas; (ii) sólo las 207 del 06-oct tienen testigo
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

- [~] **0.2 Qué mide `Clasificacion Mirova`.** IMPLEMENTADA 2026-10-14 (#780, en verificación): alerta
  protegida = alerta con VRP de la pasada >= 1 MW recalculado; la columna es del scraper y no sirve.
  Por qué: el criterio de victoria depende de "Bajo o superior", y la columna no es un corte del VRP por pasada
  (Muy Bajo 1.372 filas de 0,01 a 0,99 MW; Bajo 265 de 0,04 a 8,75; Moderado 4 de 13,1 a 15,8; medido en
  `latest_consolidado.csv` el 2026-10-13). Hipótesis a probar: el nivel es el de la página del volcán en ese
  momento (agregado de días), no el de la pasada. Fuentes: código del scraper de Mirova-v1 (por la API), umbrales
  de nivel en `documentacion/` (buscar antes en `BIBLIOGRAPHY_SYNTHESIS.md`; la página del PDF se lee
  renderizada a imagen, A95).
  Entregable: `docs/S151_CRITERIO_CLASE_MIROVA.md` con la definición operativa de "alerta protegida", su script
  y su control. Si la columna resulta inservible y ningún paper da el umbral, la definición queda en la cola de
  decisiones (§5) con la alternativa medida, y el loop sigue evaluando con las dos lecturas en paralelo.

- [ ] **0.3 Propagación A113 a las puertas de entrada.**
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

- [ ] **0.4 Instrumentos chicos.**
  (a) `evaluar_ventana.py` (en `experiments/_s149_prereg_invierno/` o donde lo ubique `git ls-files | grep
  evaluar_ventana`) deja de mandar stderr a DEVNULL, así el aviso A119 llega al log; (b) `scripts/calidad_referencia_mirova.py`
  gana los hitos de NOAA-21 y de Suomi NPP (con fuente); (c) A119 en `CLAUDE.md`: el "86 % en enero" es
  Tupungatito en el denominador (sin él, 95 a 99,5 %) y "0 alertas MODIS dependen del OCR" es falso (5 hoy);
  (d) sacar `ENABLE_TEST1_NULL_CORRECTED` de toda cola (ningún procesador lo lee, VERIFICADOR_DATOS D8).
  Cada arreglo con su test que falla antes.

- [ ] **0.5 Scraper de Mirova-v1 con VRP de 1.000 MW o más** (issue MendozaVolcanic/Mirova-v1#19, 36 ciclos
  caídos; `scraper.py:140`). En plena erupción de Chillán es el caso que puede pasar. PR en Mirova-v1 con test
  del caso "1,234.5"; **el merge espera el sí de Nicolás** (es otro repo de producción).

- [ ] **0.6 Marca de régimen en cada record** (perfil + sha del código; 0 de 65.206 records la tienen,
  VERIFICADOR_DATOS D7). Bloquea toda adopción futura. Toca `pipeline/store.py` → regla §1.1: plan + test + tag
  + PR, y a la cola de decisiones.

## 4. Bloque 1: pruebas (cola, en orden; una tarea puede avanzar mientras otra espera un sello o un run)

- [~] **1.1 Prueba de Nevados de Chillán** DESPACHADA 2026-10-14 11:58 UTC, run 38560317428 (4 a 6 h). La
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

- [ ] **1.3 A/B de D22, pre-registro v2.** Con la tabla sola, el camino D22 pesa 12 de 24 pérdidas débiles de
  `max` (VERIFICADOR_DATOS D3). Rehacer el pre-registro suspendido (`experiments/_s150_ab_d22/PREREGISTRO.md`)
  con los hallazgos de su verificador (`docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md`), el criterio de §1.2 y
  la referencia de 0.1; verificador limpio; sello de Nicolás; despacho.

- [ ] **1.4 A/B de anomalía mayor (`vrp_max`) contra `vent_anchored`** (decisión de Nicolás para la réplica).
  Universo de comparación: 359 detecciones lejanas nocturnas de MIROVA, no 858 (VERIFICADOR_DATOS D2); la
  clasificación NULO la escribe el scraper. Medir distancias desde el cráter y no desde el catálogo
  (`process_viirs.py:754`, AUDITOR_F1). Pre-registro, verificador, sello, despacho.

- [ ] **1.5 D25, fondo por vecinos, primero sin correr nada:** sobre los 268 negativos de VIIRS 750 ya en disco
  (`AUDIT_S149.md:139`). El descarte de vecinos nublados bajo 255 K es de Coppola 2014 p. 3412, no del canon
  2016a (VERIFICADOR_DATOS D9): medirlo como variante, no como "lo que exige el paper".

- [ ] **1.6 MODIS: banda 22 junto con `max`**, con los flags de compuerta y de fondo que le faltan a MODIS
  (`audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:285`). En MODIS, `max` solo apaga el detector (S147).

- [ ] **1.7 La caja de 5 × 5 km (D18)**, medida por primera vez ahora que llega a los dos pases (#738), con el
  Test 1 apagado en el brazo de control donde la palanca puede actuar (A114, A118).

- [ ] **1.8 Modo de un solo píxel en erupción** (AUDIT_S150 familia 3: Chillán VIIRS 750 mostró 2,66, 11,08 y
  2,49 MW en 54 min).

- [ ] **1.9 Preferencia de MIROVA entre banda I y banda M** (`FRENTE_F_FIDELIDAD_VIIRS.md:474`, F-07): se mide
  en minutos con la referencia.

- [ ] **1.10 Las 4 alertas de VIIRS 750 de 0,32 a 0,65 MW que `max` pierde** (VERIFICADOR_DATOS D4): su clase
  según 0.2 decide si `max` en VIIRS 750 cumple el criterio de §1.2.

- [ ] **1.11 Experimental** (bloqueado hasta que Nicolás entregue la cronología OVDAS de Chillán y las
  coordenadas de los rasgos reales: Cerro Blanco, Pichi-Llaima, Lazufre, El Agrio). Su vara no es MIROVA
  (A115).

## 5. Cola de decisiones para Nicolás (el loop agrega; Nicolás responde en el issue)

| # | decisión | evidencia | PR / tag | issue |
|---|---|---|---|---|
| D-1 | Adoptar conectiva `max` en VIIRS 375 (criterio §1.2 por medir en 0.2) | `docs/S150_RESULTADO_MESES.md`, `docs/audit_s150/meta/AUDITOR_F2_NUMEROS.md` | pendiente | pendiente |
| D-2 | Merge del arreglo del scraper Mirova-v1#19 (tarea 0.5) | pendiente | pendiente | pendiente |
| D-3 | Marca de régimen en `store.py` (tarea 0.6) | pendiente | pendiente | pendiente |

## 6. Bitácora (la más nueva arriba; una entrada por vuelta)

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
