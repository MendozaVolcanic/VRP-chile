# F1 (meta-auditoría S150): lo que las auditorías recomendaron y nunca se hizo

Fecha: 2026-10-09. `main` en `13f5bb0dd`. Modo de solo lectura: lo único que se escribió está en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\F1\` y en este archivo.

**Censo completo**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\F1\censo.csv`
(1.339 filas). Se rearma con `python juntar.py` desde los `tanda_*.txt` de la misma carpeta. El archivo
`progreso.txt` dice qué archivo entró en qué tanda y cómo se muestreó.

## 1. Cobertura y método (auditable)

- **Universo**: `ls docs/AUDIT_S*.md | sort -V` da 41 informes (S86 a S150). Las carpetas
  `docs/audit_s138` a `docs/audit_s150` traen 91 informes más. En total son **132 de 132 archivos**, más
  `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`, al que remite `AUDIT_S146.md` §7 para sus recomendaciones.
- **Quién leyó qué**:
  - Yo leí enteros `AUDIT_S150.md`, `AUDIT_S149.md` §0 a §7 y `AUDIT_S146.md` §4 a §8. También el plan de
    paridad S146 por secciones, `AUDIT_S138.md` §6/M/D/Seguimientos y la tabla de decisiones S134 a S138
    (`docs/audit_s138/EJE_6`).
  - En `docs/audit_s150/` leí los hallazgos de los cuatro auditores y de los verificadores.
  - Esas tandas (01, 02 y 06) dan 119 filas con evidencia leída por mí.
  - El resto (1.220 filas) lo extrajeron diez lectores de lote, cada uno sobre archivos enteros con
    instrucciones comunes (`PROMPT_LOTES.md`). Sus filas llevan en la evidencia el prefijo `[L#]`.
- **Unidad**: una fila es una acción propuesta en un informe. Si la misma acción reaparece en varias
  auditorías, cuenta una vez por auditoría. Así el número mide **recomendaciones emitidas**, no
  problemas distintos. La etiqueta `tema` no está normalizada entre lotes (1.199 temas): no sirve para
  deduplicar.
- **Las dos preguntas del instrumento**:
  1. **Si una recomendación se hizo y no deja rastro en PR, commit, código ni flag, el censo la marca
     ABANDONADO.** El sesgo va hacia lo abandonado. Por eso abajo se muestrea en las dos direcciones.
  2. **El barrido por palabras clave (`extraer_candidatos.py`, 1.027 líneas) no superó su control
     positivo.** No ve los encabezados de S146, así que no se usó como censo: los archivos se leyeron
     enteros.
- **Definición de estado**:
  - HECHO, DESCARTADO y REEMPLAZADO llevan evidencia citada.
  - **VIGENTE** = abierto y listado como pendiente en un documento de S147 a S150 o en una D abierta del
    catálogo.
  - **ABANDONADO** = abierto y sin rastreo en ningún documento de S147 a S150.
  - El borde entre VIGENTE y ABANDONADO es de definición: el lote L9 llamó VIGENTE a lo que AUDIT_S149 §4
    lista sin ejecutar, y yo lo llamé ABANDONADO cuando ninguna tarea de S150 lo retoma. Los dos estados
    juntos son "no hecho".
- **Lo que no se importó**: `lote_L10.csv` (128 filas de `docs/audit_s150/`) cubre los mismos archivos que
  mi tanda 02 y queda como complemento de grano fino. Mis filas propias de S146 (frentes E a I) y de las
  carpetas S147 a S149 se reemplazaron por los lotes L8 y L9, más completos, y quedan como contraste en
  `propias_*.txt`. En las 5 filas comunes, L9 dio la misma evidencia que yo.

## 2. Conteo por estado

Denominador: 1.339 recomendaciones de 132 informes, emitidas entre S86 (2026-05) y S150 (2026-10-08).
Estado medido el 2026-10-09.

| estado | total | S86 a S137 | S138 a S145 | S146 a S150 |
|---|---|---|---|---|
| HECHO | 609 (45,5 %) | 227 | 147 | 235 |
| ABANDONADO | 341 (25,5 %) | 93 | 76 | 172 |
| VIGENTE | 226 (16,9 %) | 57 | 40 | 129 |
| REEMPLAZADO | 91 | 36 | 39 | 16 |
| DESCARTADO | 47 | 34 | 9 | 4 |
| SIN_EVIDENCIA | 25 | 11 | 3 | 11 |
| **total** | **1.339** | 458 | 314 | 567 |

Salida de `python resumen.py`.

- **Lo abandonado es sobre todo texto.** De las 341 filas ABANDONADO, 124 son correcciones de
  documentos (citas, marcas de rebaja, localizadores) y 23 son tests o guards. Las de pipeline y
  medición suman 99.
- **Por objetivo, entre ABANDONADO y VIGENTE**: réplica 303, higiene 158, operación 55, experimental 34,
  ambos 17.
- **208 filas anotan una premisa caída** (A82, A83, D9, A99, D26, caja S130, A10 y otras).

## 3. Muestra verificada por mí

**ABANDONADO** (24 casos, 21 de ellos de lotes; cada uno con lectura propia del código o del documento de hoy): **24 de 24
confirmados.**

- `CLAUDE.md`:
  - :1619 sigue con "priorizamos recall sobre precision".
  - :144 da las bandas MODIS sin D20.
  - :116 conserva la "rama OR completa".
  - :298 conserva las "887 filas".
  - :167 trae A1 sin matiz.
- `pipeline/`:
  - `detection_context.py:223,226` dice "median" donde el código usa media.
  - `mirova_equivalent.yaml:482` cita Gaua.
  - `test1_integrated.py:7` cita "Coppola 2015 Eq.1".
  - `process_viirs.py:754` mide la distancia desde `volcano_lat`.
  - `profile.py:90` mantiene el default 7.0.
  - `store.py:320-324` sigue igual.
  - `geo_utils.py:81` conserva `get_effective_vent`.
- Workflows:
  - `nrt.yml:80` sigue en max-parallel 8.
  - `nrt.yml:173-174` y `:207-208` pasan el par usuario y clave vencido.
- Documentos:
  - `MIROVA_DIVERGENCES.md:1050` dice "Table 2" y `:2598` cita `sanity_cap_tocado`.
  - `docs/D9_PATH_D_CIRRUS_FP.md` no existe.
  - `docs/paper/sec5_methods.md:30` dice "unusable by day".
  - `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:142` propone n=12.
  - `HYPOTHESIS_LOG.md:1469-1496` tiene tres H_S137 en "active".
- Otros:
  - `.gitignore` no incluye `.netrc`.
  - 301 ramas remotas y ningún tag `pre-s138*`.
  - `scraper.py:140` de Mirova-v1 (leído por `gh api`) hace `float()` sin quitar la coma de miles, y el
    issue Mirova-v1#19 sigue OPEN.
  - Los records V375 de feb a abr con VRP traen `final_hotspot_source` test1 34 y eruption 26 en Isluga,
    y test1 75 y eruption 25 en PP: exacto lo que dijo el lote L1.

**HECHO** (8 filas de los lotes elegidas al azar, semilla 150): **8 de 8 confirmados.**

- PR #659 y #666 mergeados.
- `S149_COSTO_OCULTO_MAX.md:88-91`.
- `_s143_evaluador/parametros.json:9` (`cota_km` 0,55).
- `CLAUDE.md:933` (cita de A76 marcada).
- `rebuild_mirova_from_consolidado.py:45-50` (escala completa).
- `BORRADOR_CORREO_COPPOLA.md:10-11`.
- `S148_RESULTADO_AB_CONECTIVA.md:37-38`.
- En `nrt.yml` las entradas de `github.event.inputs` van por `env` y por `if`, no dentro de `run`.

**Una corrección a mi propia tanda**: yo había marcado HECHO el Test 1 con el estadístico corregido, y el
frente E de S149 tenía razón. El flag existe, pero **ningún procesador lo lee** (ver H-1).

## 4. Hallazgos (lo abandonado que tuerce decisiones), por gravedad

### H-1. El flag del Test 1 corregido es un flag muerto: un brazo de A/B con él sería idéntico al control
- **ARCHIVO:LÍNEA**:
  - `ENABLE_TEST1_NULL_CORRECTED = False` está en `flags_mirova_equivalent.txt`.
  - `grep NULL_CORRECTED` en `pipeline/*.py` fuera de `profile.py` sólo da el parámetro `null_corrected` de
    `pipeline/test1_integrated.py:220,307,361,467`, y ningún `process_*.py` lo pasa.
- **QUÉ PASA**: el Test 1 suma un exceso recortado a cero, así que el ruido puro de una cumbre fría suma
  positivo. La corrección se escribió, pero no llega al detector: es la forma de A118. S149 lo dijo (E-04)
  y `BLOQUE_ARRANQUE_S150` §f 3e sigue mandando correr "el brazo del Test 1 con el estadístico corregido
  para el experimental". Ese brazo saldría idéntico al control y se leería como "la corrección no cambia
  nada".
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `grep -rn "NULL_CORRECTED\|null_corrected" "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/pipeline"`
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3, porque invalida en silencio un A/B planificado.

### H-2. La regla del dueño (fidelidad en los dos sentidos) no llegó a donde se lee primero
- **ARCHIVO:LÍNEA**:
  - `CLAUDE.md:1619` todavía dice "priorizamos recall sobre precision".
  - En `docs/MISSION.md` (último cambio `5167951c2`, 2026-09-20), `grep "dos sentidos|callar"` da 0.
  - `AUDIT_S131.md:68` sigue con "111 FN, todos reales y sub-umbral", sin marca.
  - El título de A76 en `CLAUDE.md:926` sigue diciendo "supervisión MANUAL".
- **QUÉ PASA**: la Fase 0.1 de S149 pidió propagar la decisión de Nicolás: callar donde MIROVA calla. La
  brecha medida es sobre-publicación (VIIRS 375 publica en 86,8 % de los negativos). Una sesión fría que
  lee el glosario prioriza al revés.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; tuerce el criterio de cada A/B nuevo.
- **CÓMO REPRODUCIRLO**: `grep -n "priorizamos recall" CLAUDE.md docs/MISSION.md`
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

### H-3. El fondo por vecinos (D25) está implementado sin la exclusión de nube que el paper le pone
- **ARCHIVO:LÍNEA**:
  - `pipeline/process_viirs.py:683` (`vrp_bg_neighbor_mean_v375(bt_grid, alert_mask, ...)`).
  - `pipeline/process_viirs_mod.py:416` (la versión V750).
  - Ni la firma ni las líneas 683 a 740 reciben la banda TIR ni mencionan nube o 255 K.
  - `AUDIT_S128.md:548-556` cita la p. 3412: el fondo L4bk es la media de los vecinos "not contaminated
    by clouds", con `BT11 < 255` (Giglio 2003). El lote L3 la marcó ABANDONADO.
- **QUÉ PASA**: un vecino bajo una nube fría baja el fondo y sube el exceso del píxel alertado. El brazo
  D25, que es la palanca número 1 del plan de S149 para las 28 alertas V750 en 0,0 MW, se mediría sin
  esa defensa. Además el sustrato de la decisión, los 268 negativos que podrían empezar a publicar, son
  noches frías.
- **CÓMO SE VE EN EL DASHBOARD**: invisible hasta que se adopte.
- **CÓMO REPRODUCIRLO**: `sed -n 683,740p pipeline/process_viirs.py`
- **CONFIANZA**: CONFIRMADO el cableado. El efecto es SOSPECHA y no está medido.
- **GRAVEDAD**: 3.

### H-4. El scraper de la referencia aborta con un VRP de mil o más MW, justo en una erupción
- **SCRIPT:SALIDA**: `gh api repos/MendozaVolcanic/Mirova-v1/contents/scraper.py`, l. 140, hace
  `vrp = float(cols[3].text.strip())`. El issue Mirova-v1#19 sigue OPEN.
- **QUÉ PASA**: `latest.php` escribe los miles con coma (`2,178.53`), `float()` falla y el ciclo se corta
  (`docs/audit_s139/MAPA_BASES_MIROVA_V1.md:202`). Con Chillán en erupción, la referencia contra la que se
  mide la réplica puede dejar de actualizarse en la pasada más fuerte.
- **CÓMO SE VE EN EL DASHBOARD**: la línea de MIROVA se congela.
- **CONFIANZA**: CONFIRMADO el código. Que ya haya pasado es SOSPECHA.
- **GRAVEDAD**: 3. El arreglo es de otro repo.

### H-5. El relleno del ancla honesta en VIIRS 375 nunca se corrió
- **SCRIPT:SALIDA**: los records VIIRS 375 de feb a abr de 2026 con VRP > 0 traen
  `final_hotspot_source = test1 / eruption` en 34 y 26 de Isluga, y en 75 y 25 de PP. Esas fuentes
  pertenecen al esquema anterior al ancla. Fuente de la recomendación: `AUDIT_S106.md:59`, lote L1.
- **QUÉ PASA**: el mismo cráter se ubica con dos reglas según el mes.
- **CÓMO SE VE EN EL DASHBOARD**: en esa ventana el mapa mezcla dos posiciones.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2, porque el reproceso del día de la adopción lo arrastra.

### H-6. Otros abandonados verificados por mí, de operación
- `nrt.yml:173-174` y `:207-208` le siguen pasando al NRT el par usuario y clave vencido. Con un token
  vacío cae ahí (A-8 de S150), y en S146 ese par ya bloqueó la cuenta.
- `nrt-healthcheck.yml:247` y `:388` crean la etiqueta sin `--force`, así que el job sale rojo justo
  cuando avisa bien (A-10).
- El sync horario no refresca `mirova_v1_snapshot/registro_vrp_consolidado.csv`, que es el que leen los
  evaluadores (A-11).
- `volcanoes.yaml:75` mantiene `max_cluster_pixels: 12` en Villarrica, que anula una colada real de más
  de 12 píxeles (C-06).
- `process_modis.py:1171-1183` no guarda la magnitud anterior al tope D9.
- El catálogo no anota que el camino D nunca recibió el flag sin compuerta de D22.

Ninguno de estos seis entró a la síntesis `AUDIT_S150.md`: `grep` de cada ID da 0.

## 5. Lo más valioso para continuar (ABANDONADO o VIGENTE que sirve al objetivo)

Orden: primero lo que mueve la paridad de la réplica contra MIROVA, ponderado por costo.

| # | qué | estado | fuente | por qué sirve | costo para probarlo |
|---|---|---|---|---|---|
| 1 | **D25, fondo por vecinos, medido en los dos sentidos**, primero sobre los 268 negativos V750 ya en disco y **con la exclusión de nube de 255 K** (H-3) | VIGENTE (más un faltante ABANDONADO) | `AUDIT_S149.md:139-143`; `AUDIT_S128.md:553`; `audit_s149/plan_final/VERIFICADOR_MAGNITUD_CERO.md:78` | 28 alertas V750 perdidas con 0,0 MW, y parte del 0,6 de magnitud. Cayeron los dos veredictos que lo apagaron | la medición en disco toma horas; después, el ciclo A45 para la nube y un A/B |
| 2 | **A/B de `vrp_max` contra `vent_anchored`**, con distancias medidas desde el cráter y no desde el catálogo | VIGENTE (decisión de Nicolás); la distancia está ABANDONADA | `AUDIT_S150.md:153`; `AUDIT_S134.md:438`; `process_viirs.py:754` | Es la regla de selección de MIROVA: publicó 858 detecciones a 20 km de mediana. Sin el arreglo de distancia, la paridad de distancias compara puntos distintos | pre-registro más A/B de 11 volcanes |
| 3 | **MODIS: banda 22 con `max`, más los flags de compuerta y fondo que MODIS no tiene** | VIGENTE (banda 22) y ABANDONADO (flags) | `AUDIT_S149.md:146`; `audit_s146/A2_RESULTADO_VARA_CORREGIDA.md:285`; `audit_s149/plan_final/FRENTE_E_PAPER_CONTRA_CODIGO.md:236` | MODIS publica igual con alerta que sin ella. El brazo que da 9 de 9 en el Apéndice A no se puede armar en MODIS sin esos flags | escribir los flags apagados (A45), y después el A/B en Láscar de marzo a junio |
| 4 | **La caja de 5 × 5 km (D18), medida por primera vez** ahora que llega a los dos pases (#738), encima de "sin Test 1" | VIGENTE | `audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md:115`; `BLOQUE_ARRANQUE_S150` §b1 | Es literal del paper y el NO ADOPTAR de S130 no midió la caja | reescribir el pre-registro (Q3 no tiene sustrato) y repetir los brazos G y H |
| 5 | **Cablear `ENABLE_TEST1_NULL_CORRECTED` a los procesadores** antes de cualquier brazo (H-1) | ABANDONADO | `audit_s149/plan_final/FRENTE_E_PAPER_CONTRA_CODIGO.md:226` | Sin cableado, el brazo del experimental no mide nada | chico, con A45 |
| 6 | **Regla de preferencia de MIROVA entre banda I y M** (retiene la de 750 m cuando coinciden) | ABANDONADO | `audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:474` (F-07); `FRENTE_H_HIPOTESIS_Y_AB.md:396` | Puede explicar parte del 86 % de V375 en negativos: una fila de MIROVA contra dos records nuestros. Salvedad A105: es la regla del OSF, quizá no la del NRT | minutos, sobre lo persistido |
| 7 | **Propagar la Fase 0 de S149** (H-2) y **marcar en el catálogo las rebajas de S138 que no bajaron**: el cuerpo de D21 sigue diciendo "la pérdida de Villarrica la causa D22" (`MIROVA_DIVERGENCES.md:2545`) | ABANDONADO | `AUDIT_S149.md:122`; `audit_s138/EJE_3_verificador_instrumentos_s137.md:321` | Es lo que cada sesión hereda primero (A113) | un PR de documentos |
| 8 | **Para el experimental**: correr el Test 1 con fondo local sobre NTI (la única cura de A69 que se diseñó), con el banco de paridad, y conseguir la tabla de episodios de OVDAS | ABANDONADO y VIGENTE | `audit_s146/FRENTE_H_HIPOTESIS_Y_AB.md:225`; `AUDIT_S149.md:156`; `AUDIT_S150.md:164` | Más detección real en los nevados con menos falso topográfico; sin vara de OVDAS no se valida | probe A75 o A/B, y el dato de OVDAS que trae Nicolás |

**Premisas caídas que tocan este ranking**:
- El ítem 1 revive porque cayeron sus dos veredictos de apagado (FRENTE_D_VEREDICTOS_VIEJOS H2).
- El ítem 3 lo bloqueaba el "irreducible" de A82.
- El ítem 4 lo bloqueaba el NO ADOPTAR de S130, medido con el Test 1 encendido y con el flag que sólo
  llegaba al primer pase.
- Además, **el lote L1 marca como DESCARTADO un pool de fondo sin la cumbre nevada** (S110), y su razón
  era que "el leak entra 100 % por C1". Esa razón vale bajo `min`. Si la réplica pasa a `max`, el sigma
  pasa a gobernar y conviene reabrirlo (SOSPECHA, no medido).

## 6. Lo que este informe no cubrió, dicho

- 1.220 de las 1.339 filas son de lectores de lote. Muestreé 29 de ellas (21 ABANDONADO y 8 HECHO).
  El error residual de los lotes no está medido más allá de esa muestra: 29 de 29 sin error.
- La deduplicación entre auditorías no está hecha. Una acción recomendada en cinco sesiones (por ejemplo,
  la co-validación de D9) aparece cinco veces.
- No abrí las carpetas `docs/s124` a `docs/s137` ni los `BLOQUE_ARRANQUE`, salvo el de S150. Las
  recomendaciones que vivan sólo ahí están fuera.

## VERIFICADO LIMPIO (no volver a mirar)

| qué | comando |
|---|---|
| `nrt.yml` fijado a `ubuntu-24.04` | `grep -n runs-on .github/workflows/nrt.yml` (l. 68) |
| `first_processed_utc` en `store.py` | `grep -n first_processed_utc pipeline/store.py` (620-624) |
| experimental congelado, idéntico a la réplica salvo el directorio | `diff experiments/_s150_meta_audit/F1/flags_mirova_equivalent.txt experiments/_s150_meta_audit/F1/flags_experimental.txt` (sólo `DATA_SUBDIR` y `PROFILE_NAME`) |
| hook de sesión de alertas y token | `grep -n DIAS_AVISO_TOKEN ~/.claude/hooks/check_alertas_vrp.py` |
| monitor y auditoría semanal de S150 | existen `scripts/nrt_monitor_decision.js`, `tests/test_nrt_monitor_decision_s150.py`, `tests/test_auto_audit_cobertura_s150.py` |
| sync horario trae el OCR | `grep -n registro_vrp_ocr .github/workflows/sync-mirova-csv.yml` (99-100) |
| `pc.classification` con `provisorio` | `grep -n provisori scripts/clasificacion_referencia.py` (ESQUEMA 2) |
| cita 77:55 retirada del pipeline | `grep -rn "77:55" pipeline` (sólo los comentarios que explican el retiro) |
| D9 reabierta, con el estado viejo conservado | `sed -n 622,644p docs/MIROVA_DIVERGENCES.md` |
| token rotado | `REGISTRO_CREDENCIALES.md:28` (2026-10-08, vence 2026-12-07) |
| `github.event.inputs` fuera de los bloques `run` en `nrt.yml` | `grep -n github.event.inputs .github/workflows/nrt.yml` (todo en `env` o `if`) |
