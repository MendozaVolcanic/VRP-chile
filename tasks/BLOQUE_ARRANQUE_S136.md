# Bloque de arranque S136

> **Estado fijado el 2026-09-08 con trabajo EN CURSO**: el chunk 2 del A/B (run 34208191011) iba
> en **21 de 30 jobs** cuando se escribió esto. Lo que aterrice después no está acá. Verifícalo
> antes de creerle a este documento: `gh run view 34208191011 --json status,jobs`.

## 0. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **Segundo pase condicionado (D2)** implementado detrás de flag **en OFF** | terminado | PR #605 · `pipeline/detection_context.py` (`conditioned=`) · `ENABLE_SECOND_PASS_CONDITIONED` · 17 tests |
| **A/B de 5 brazos**, 6 volcanes, perfiles aislados | chunk 1 terminado, chunk 2 **corriendo** | `reproc-s135-ab-d1d2.yml` · chunk 1 run 34173711390 (30/30 verde) · chunk 2 run 34208191011 (21/30 al cierre) |
| **Resultado del chunk 1** (06-01 → 07-15, los 6 volcanes) | terminado | `experiments/_s135_ab_d1d2/RESULTADO_CHUNK1.md` + `resultado_chunk1.json` |
| **Las 5 pérdidas del brazo fiel**, investigadas una por una | terminado | `INVESTIGACION_ISLUGA_2NOCHES.md` (5 tramos) + `investigar_perdidas.py` |
| **Pre-registro del A/B** con la decisión de Nicolás incorporada | terminado | `docs/PREREGISTRO_AB_D1_D2_S135.md` |
| **D19 medido en el régimen vigente** | terminado | `experiments/_s135_probe_etapas/D19_HOY.md` · `d19_regimen_vigente.py` |
| **Probe A75 por etapa** + paso 0 cat-b | terminado | `experiments/_s135_probe_etapas/` (yml en `_archive/`) |
| **Paper: §4, §5 y §6 en prosa** + script único de números | escrito, falta revisión de Nicolás | `docs/paper/` (`sec4`, `sec5`, `sec6`, `README.md`) · `scripts/paper_numbers.py` |
| **D20** (el NTI de MODIS usa la banda 31 y el canon la 32) registrado | terminado | `docs/MIROVA_DIVERGENCES.md` |
| Suite | **1245 passed · 4 skipped · 2 xfailed** | los 2 xfail son los tripwires de D19, intactos |
| Rama y remoto | `main`, verificado contra `git ls-remote` | las 5 ramas `s135-*` integradas (`git cherry` = 0) |

### El resultado del chunk 1, que es lo que hay que leer

156 noches confirmadas (Isluga 38, Lastarria 30, Láscar 26, Planchón-Peteroa 23, Puyehue 20,
Tupungatito 19), después de excluir pasadas diurnas y coincidencias de fecha con objetos distintos.

| brazo | pierde | quita el artefacto | paridad | veredicto |
|---|---|---|---|---|
| A control | 0 | — | 0,691 | — |
| **B sin `keep_peak`** | **0** | **100 %** | 0,692 | **cumple los tres** |
| C sólo 2º pase condicionado | 0 | **−65,8 %** | 0,689 | no |
| D ambos (el más fiel) | **5** | 100 % | 0,692 | pierde 5 |
| E 2º pase apagado | 0 | **−65,8 %** | 0,658 | no |

## 1. Decisiones que esperan a Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | El brazo B cumple los tres criterios, pero se apoya en un segundo pase que sabemos infiel a Coppola. ¿Se adopta igual? | (a) adoptar B; (b) no adoptar y perseguir la hipótesis del Test 1; (c) esperar el chunk 2 | **(c), y después (b)**. B es el menos malo del eje, no una solución: quita el artefacto conservando un mecanismo que el paper no tiene. Adoptarlo cierra el problema en falso |
| 2 | La hipótesis que dejan los 5 casos: que el **Test 1 integrado no deba intersectarse con la máscara contextual**. ¿Se investiga? | (a) sí, con las 3 preguntas de MISSION y su propio A/B; (b) archivar | **(a)**. Es la única salida que no obliga a elegir entre perder señal y publicar artefacto, y tiene 5 casos que la motivan |
| 3 | D19 sigue abierta. Con lo medido, ¿se re-enuncia? | (a) reescribirla con el matiz de Copahue y el tamaño real; (b) dejarla | **(a)**: el anillo de 2,5-3 km contiene artefacto **y** señal (en Copahue MIROVA reporta a 2,7 km), y su enunciado usa un denominador que se mueve |
| 4 | Las notas al editor de §4 y §5 del paper esperan tu lectura | (a) revisarlas ahora; (b) seguir con §3/§7/§8 | **(a)** primero: hay dos citas de Coppola 2014 de segunda mano que sostienen el argumento central del paper |
| 5 | ¿El A/B debería reintentar solo los jobs que quedan con cobertura corta? | (a) automatizar el reintento; (b) verificar a mano con el control que ya existe | **(b)** por ahora: el control de cobertura ya lo detecta y avisa; automatizarlo es alcance nuevo |

## 2. Lo aprendido

**Reglas de método, candidatas al `CLAUDE.md` del proyecto:**

- **Un denominador que se mueve solo invalida el antes/después.** Medí un mecanismo sobre los
  records etiquetados *summit*, y ese etiquetado lo movía el mismo cambio de código que estaba
  midiendo. Con el denominador robusto la caída se desvanece. Corolario: dos puntos no distinguen
  un salto de la variación normal; hace falta la serie previa.
- **Antes de comparar dos brazos, verificar que hayan procesado lo mismo.** Un cortacircuitos de
  red dejó un brazo con 149 de 203 pasadas, y sus «pérdidas» eran días que nunca miró. El control
  de cobertura ahora corre primero en el evaluador.
- **Una «pérdida» se define simulando todas las etapas siguientes**, no sólo la que se apaga.

**Reglas generales del workspace, no sólo de este proyecto:**

- **A93, tres veces en una sesión:** restar dos radios sin preguntar desde qué punto mide cada
  uno. La separación cráter ↔ centro de grilla de MIROVA va de 0,115 km en Lastarria a 7,569 en
  Puyehue. Lo delató un número absurdo, no una revisión del método.
- **Un techo artificial se reconoce por su forma**: «entonces no podemos aspirar a igualarlos».
  Escribí que MIROVA publica cosas por supervisión humana; la regla que lo desmiente estaba en la
  memoria desde S21 y aun así lo escribí.
- **Un guard que falla por razones equivocadas también queda inutilizado**: la versión fuerte del
  guard de citas daba falsos positivos con las líneas históricas que el proyecto cita a propósito.
  Se dejó la débil, con su límite escrito en el propio test.

## 3. Problemas abiertos e hipótesis

**CONFIRMADO** (verificado con herramientas en esta sesión):

- El patrón «Test 1 dispara y el primer pase da cero» está en **2.315 de 4.571** records de
  VIIRS 375 m (50,6 %); **118** de ellos son detecciones que MIROVA confirma y son el mismo
  objeto. Todas dependen hoy de `keep_peak` o del segundo pase suelto.
- Las **5 pérdidas del brazo fiel** son un solo mecanismo, en 4 volcanes y con fuentes físicas
  distintas: primer pase 0-2 px, Test 1 con 65-98 px, y la detección la sostienen los brazos B, C
  y E. En dos casos la magnitud coincide con MIROVA (0,057 vs 0,06 y 0,098 vs 0,06).
- **Arreglar sólo el segundo pase empeora el artefacto un 65,8 %**: al condicionarlo o apagarlo,
  el camino contextual deja de ganar la selección y el Test 1 pasa a ser la fuente con su píxel
  único.
- En **Copahue el 27 de julio**, tres pasadas seguidas, nuestro cúmulo está a 2,9 km y MIROVA
  reporta 2,7 km: un cúmulo a ~3 km **no** es automáticamente el artefacto del borde.
- El snapshot del ground truth lo refresca `audit-weekly.yml` (lunes), no el sync horario: el
  desfase con lo que ve el frontend es de hasta una semana, no permanente.

**SOSPECHA** (no verificada en esta sesión):

- Que el **Test 1 integrado no deba intersectarse con la máscara contextual**. Tiene 5 casos que
  la motivan y base en el paper (allí es un camino propio, no un candidato a filtrar), pero **no
  se midió** qué cúmulo se formaría sobre el footprint completo ni qué pasaría con el artefacto
  en los nevados.
- Que el contraste contra vecinos falle en estos casos **porque la anomalía es más ancha que el
  píxel de 375 m**. Encaja con los diagnósticos, pero no se probó contra el footprint real.

## 4. Cerrado, no rehacer

- **Las 4 «pérdidas» del brazo B en Puyehue**: eran un job degradado por el cortacircuitos de CMR
  (`ConnectionResetError` de NASA), ya relanzado y con cobertura completa (203 pasadas). El brazo
  B **no pierde ninguna noche**.
- **Una de las 2 noches de Isluga** del análisis parcial: era coincidencia de fecha con un objeto
  distinto (el control acertaba con algo a 2,77 km cuando MIROVA veía a 0,75), no una pérdida.
- **El A/B tiene sustrato**: los 5 brazos leen lo que declaran y producen resultados distintos,
  verificado con test propio y en un paso previo dentro de cada job.
- **El criterio de cero pérdidas** ya está incorporado al pre-registro y al evaluador, junto con
  la instrucción de investigar cada diferencia en vez de descartar el brazo.
- **«MIROVA lo revisó a mano» no es explicación válida** para una diferencia contra su canal NRT.
- **D14** (máscara de nube) sigue cerrada y correcta: lo que se descubrió es que su cambio movió
  el etiquetado y el fondo, no que hubiera que revisarla.

## 5. Prompt para la próxima sesión

```
Continuamos VRP Chile desde S135. Antes de creerle a nada de lo que sigue, verifica el estado:

    cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
    git fetch origin --prune && git pull --ff-only
    gh run view 34208191011 --json status,jobs   # chunk 2 del A/B: iba 21/30 al cierre de S135
    gh run list --workflow=nrt.yml --limit 3     # que el NRT siga produciendo

LEER, en este orden:
  1. tasks/BLOQUE_ARRANQUE_S136.md               (este bloque)
  2. experiments/_s135_ab_d1d2/RESULTADO_CHUNK1.md
  3. experiments/_s135_ab_d1d2/INVESTIGACION_ISLUGA_2NOCHES.md   (5 tramos)
  4. docs/PREREGISTRO_AB_D1_D2_S135.md           (criterio y decisiones ya tomadas)
  5. docs/MIROVA_DIVERGENCES.md, entradas D19 y D20

QUÉ HACER, en orden:

1. Si el chunk 2 terminó: bajar sus artefactos, juntarlos con los del chunk 1 y correr
       python experiments/_s135_ab_d1d2/evaluar_ab.py --dir <carpeta>
   El evaluador verifica PRIMERO la paridad de cobertura entre brazos. Si avisa que un volcán
   quedó desparejo, relanzar ese job antes de leer cualquier número: pasó con Puyehue/brazo B,
   que el cortacircuitos de CMR dejó con 149 de 203 pasadas y produjo 4 pérdidas falsas.
   Investigar cada noche perdida con
       python experiments/_s135_ab_d1d2/investigar_perdidas.py --dir <carpeta> --brazo D

2. Presentarle a Nicolás las 5 decisiones de la sección 1, con su recomendación. La 1 y la 2
   son las que mueven el proyecto.

3. Si autoriza la hipótesis del Test 1 sin intersección contextual: pasar las 3 preguntas de
   MISSION.md ANTES de tocar nada, y recién entonces diseñar su A/B. Hay 5 casos documentados
   como evidencia, y el flag ENABLE_TEST1_CONTEXTUAL_FILTER ya existe.

4. Paper: las notas al editor de docs/paper/sec4 y sec5 esperan la revisión de Nicolás. Lo más
   urgente son dos citas de Coppola 2014 de segunda mano que sostienen el argumento central.
   Después vienen §3, §7 y §8. Los números se regeneran con
       python scripts/paper_numbers.py --tests

REGLAS DURAS:
  · Nada en pipeline/ sin tag defensivo Y confirmación explícita de Nicolás (A45).
  · Ningún flag se enciende sin A/B con reproceso real y criterio pre-registrado (A18/A91).
  · Todo número con denominador y ventana (A90). Un radio no es una posición, y dos radios sólo
    se restan si salen del mismo origen (A93): falló tres veces en S135.
  · Antes de comparar dos brazos, verificar que procesaron las mismas pasadas.
  · «MIROVA lo revisó a mano» NO explica una diferencia: su canal NRT no tiene supervisión.
  · Los 2 xfail de tests/test_guard_keep_peak_s134.py son el tripwire de D19.
  · Español de Chile sin voseo; fenómeno físico → mecanismo → números.

SI LA SESIÓN NO ALCANZA: lo mínimo es dejar escrito el veredicto del A/B completo en
experiments/_s135_ab_d1d2/ y las decisiones presentadas a Nicolás. Lo demás puede esperar.
```

---

## 0-prev. Bloque previo de S136 (HISTÓRICO — escrito antes de correr el A/B)

> Se conserva entero, sin editar, para poder ver qué se creía antes de tener el
> resultado. El estado vigente está arriba.

### Prompt de entonces (superado por el de arriba)

```
Continuamos VRP Chile desde S135. Ayer corrimos el probe A75 por etapa en CI (decisión D1(b) de
AUDIT_S134 §D): experiments/_s135_probe_etapas/RESULTADOS.md, verificado con contexto limpio.

QUÉ SALIÓ. El criterio pre-registrado dio H1 REFUTADA por la rama prevista: en Villarrica
2026-07-01 el cráter no está en el footprint del Test 1 antes de keep_peak (0 px a <0,5 km; el
disco entero a 239 K, 27 K bajo el fondo global — gradiente A69 o tope de nube, el probe no
capturó I05). keep_peak no descarta el cráter; elige el borde de un footprint que nunca lo tuvo.
Tres noches, tres fenómenos (07-01 cono frío; 08-14 flanco S; 08-31 objeto discreto a 2,97 km E,
dNTI-positivo, donde keep_peak es inerte). Control Láscar 3/3 pero vacuo: keep_peak sólo corre
si final_hotspot_source == "test1" y en Láscar siempre gana el contextual.

LO NO PREVISTO, y lo más importante: 2 de 3 pasadas de Villarrica NO reproducen el record
persistido con el código de hoy sobre el mismo granule. Causa: hasta #535 (2026-08-28 23:00 UTC)
process_viirs.py fijaba CLOUD_BT_THRESHOLD = 260 K a mano; hoy lee cloud_mask_bt_k: 0.0 (D14,
cerrada, correcta). En nevados el fondo global baja 6-8 K (Villarrica 268,5 → 262,3 K; Llaima
268,6 → 260,9; Láscar no se mueve) y el first pass dispara 4-7× más. Los conteos de D19
(245/289 test1_roi) son del régimen viejo: 396 records contra 40 del nuevo. El mecanismo sigue
(08-31 reproduce exacto) pero su tamaño en producción hoy NO está medido.

PASO 0 YA CORRIÓ (S135, experiments/_s135_probe_etapas/RESULTADOS_PASO0.md, verificado): 12 pasadas
(9 cat-b Lastarria/Tupungatito/Isluga + 3 control Láscar con first pass vacío), con I05, sin nube.
Veredicto pre-registrado INTERMEDIA (0 pérdidas con el pico en el cráter, n=2; 4/9 con el pico en el
borde). El verificador limpio corrigió (gravedad 5) que off_pierde ignoraba el second pass, que corre
antes del filtro y no depende de keep_peak: con D2 permisivo (hoy) el second pass rescata 3 de las 4
(Lastarria 08-28 con el píxel idéntico, Tupungatito 08-21 con el cráter) y la cuarta (Isluga 08-19)
no es señal (−3,8 K; cota A93 2,56 km del hotspot de MIROVA). Con D2 condicionado como manda Coppola,
keep_peak OFF pierde el campo fumarólico de Lastarria (cota 0,08/0,64, presupuesto 0,55 km) y el
cráter de Tupungatito 08-21. Conclusión: D1 y D2 son UN diseño de 4 brazos (keep_peak OFF/ON ×
second pass condicionado/no), régimen nuevo, FN cat-b por volcán, cota A93 desde mirova_center.
11/12 test1_roi persistidos son hoy ctx_cluster (régimen D14). H2 = 13/13 ≤ 3 K.

PAPER (S135): docs/paper/ tiene §4 y §5 en prosa (PR #601), README del flujo, y
scripts/paper_numbers.py --tests → numbers.json/TABLAS.md (Tablas 2-4; PR #600). D20 registrado
(banda 31 vs 32, despreciable). Siguiente paso acordado: §6 Validation con la Tabla 4 y las
divergencias abiertas de frente; después §3/§7/§8. Las 11+6 notas al editor de sec4/sec5 esperan
revisión de Nicolás (la más importante: Coppola 2014 citado de segunda mano; grilla 50 vs 51 km).

OBJETIVO S136 (si Nicolás no decide otra cosa): (1) medir D19 sobre el régimen vigente
(records V375 summit desde 2026-08-28 23:00; reusar experiments/_s134_audit/f3/verif_h1.py con
esa ventana; reportar con denominador — hoy n≈40 por volcán, así que puede convenir esperar o
reprocesar junio-agosto con el código actual en CI, chunked, sin tocar data/ operacional);
(2) escribir el pre-registro del A/B de 4 brazos (keep_peak OFF/ON × second pass condicionado a
conjunto activo no vacío + vecindad 8, Coppola 2016a l.329-341) con FN medido sobre cat-b por
volcán y presentárselo a Nicolás; (3) si lo aprueba, montar los 4 perfiles con data_subdir
aislado (patrón S24/S25) sobre la ventana del régimen nuevo.

HILO PARALELO — el paper. Nicolás preguntó en S135 en qué quedó. Estado: un solo borrador,
docs/PAPER_VRP_CHILE_DRAFT_S72.md (475 líneas, esqueleto anotado, sin prosa salvo el abstract,
que está marcado [UPDATE S119]); sin tocar desde S120 (2026-07-02, PR #479). Decisiones ya
tomadas (§0): venue Volcanica (diamond OA, sin APC), scope clon + beyond-MIROVA, Coppola después,
MIT, Claude en agradecimientos. Faltan: prosa de §3-§11, tablas de validación regeneradas por
script (S91), 12+ figuras, ~30-40 refs con DOI (hoy 20 sin DOI, sin .bib), coautores, disclosure
IA con SERNAGEOMIN. Riesgo: el abstract cita números de S119 y desde entonces cambiaron
nadir-fijo, D14, D17/D18, S130 (piso), S132 (F5'), D19. Propuesta de S135 para seguirlo: ver
el mensaje de cierre de S135 (cuatro pasos: congelar los números en un script único, redactar
§4-§5 desde MIROVA_DIVERGENCES + FICHA_SDA, §6 validación con la banda de paridad vigente, y
recién entonces §3/§7/§8). Preguntar a Nicolás qué paso quiere primero.

LÍMITES: nada en pipeline/ sin tag + confirmación (A45); ningún flag sin A/B real y criterio
pre-registrado (A18/A91); granules sólo en CI (A71); los 2 xfail de test_guard_keep_peak_s134.py
son el tripwire de D19. Español de Chile sin voseo; fenómeno → mecanismo → números; todo número
con denominador y ventana (A90); un radio no es una posición (A93).

LEER, en orden: 1. este bloque · 2. experiments/_s135_probe_etapas/RESULTADOS.md ·
3. docs/MIROVA_DIVERGENCES.md D19 (adenda S135, al final) · 4. docs/AUDIT_S134.md §D ·
5. docs/PAPER_VRP_CHILE_DRAFT_S72.md §0 y §C (sólo si se retoma el paper).

ESTADO AL ARRANCAR: suite 1211 passed · 4 skipped · 2 xfailed. Nada corriendo en CI. Yml del
probe archivado. Tres flags de S132 siguen OFF. Ninguna decisión de §D tomada por Nicolás.
```

## Lo que S135 dejó hecho

| item | dónde |
|---|---|
| probe A75 por etapa VIIRS375, read-only, corrido en CI (run 34071793829, 6/6) | `experiments/_s135_probe_etapas/` · PR #598 |
| paso 0 (12 pasadas cat-b/control, I05, criterio pre-registrado) corrido (run 34091969140) | `RESULTADOS_PASO0.md` · PR #600/#602 |
| paper: §4 + §5 en prosa, README, `scripts/paper_numbers.py`, D20 | `docs/paper/` · PR #600/#601 |
| análisis puro con 13 tests (A89, escena sintética D19, criterio, yml) | `analisis.py`, `tests/test_probe_etapas_s135.py` |
| resultados + verificación con contexto limpio (4 correcciones incorporadas) | `RESULTADOS.md` |
| §3 dos regímenes de fondo, con script | `regimen_fondo.py` → `regimen_fondo.json` |
| adenda S135 a D19 | `docs/MIROVA_DIVERGENCES.md` |
| yml archivado | `.github/workflows/_archive/probe-s135-etapas.yml` |
| D19 medido en el régimen vigente: **la caída no está demostrada** (39,0 % cae dentro de la variación mensual; el artefacto se mudó de rama) | `D19_HOY.md` · `d19_regimen_vigente.py` |
| pre-registro del A/B de 4 brazos, con criterio y umbrales | `docs/PREREGISTRO_AB_D1_D2_S135.md` |
| paper: §6 Validation en prosa + recorte de la ventana de ground truth | `docs/paper/sec6_validation.md` |

## Estado del A/B al cierre del tramo (S135)

**Run del chunk 1**: 34173711390 (`reproc-s135-ab-d1d2.yml`, 2026-06-01 → 07-15, overwrite=true).
**Falta el chunk 2**: mismo workflow con `start=2026-07-16 end=2026-08-31 overwrite=false`.
Bajar los artefactos con `gh run download <run_id> --dir <destino>` y evaluar con
`python experiments/_s135_ab_d1d2/evaluar_ab.py --dir <destino>`.

**Resultado parcial** (3 de 6 volcanes: Isluga, Láscar, Lastarria; sólo el chunk 1):

| brazo | FN | quita artefacto | paridad | veredicto |
|---|---|---|---|---|
| A control | 0 | 0 % | 0,647 | — |
| B sin keep_peak | 0 | 100 % | 0,647 | CUMPLE |
| C segundo pase condicionado | 0 | **−25 %** | 0,644 | no cumple |
| D ambos (el más fiel) | **2** | 100 % | 0,652 | pierde 2 noches |
| E segundo pase apagado | 0 | **−25 %** | 0,626 | no cumple |

**Las 2 noches perdidas están investigadas** (`experiments/_s135_ab_d1d2/INVESTIGACION_ISLUGA_2NOCHES.md`,
cinco tramos): Isluga 01-jul (cráter, MIROVA 0,10 MW @ 0,75 km) y Lastarria 02-jul (campo
fumarólico del Lazufre, MIROVA 0,06 MW @ 1,55 km, nuestra magnitud 0,057 — coincide). **Son el
mismo mecanismo**: primer pase 0 píxeles, el Test 1 integrado SÍ dispara (82-89 px), y la
intersección con la máscara contextual (filtro de S99, que no es de Coppola) lo anula; lo que
sostiene la detección es `keep_peak` o el segundo pase suelto.

**Frecuencia del patrón** (`frecuencia_patron_test1.py`): el patrón «Test 1 dispara + primer
pase en cero» está en **2.315 de 4.571** records V375 (50,6 %), y **118** de esos son
detecciones que MIROVA confirma y son el mismo objeto (Lastarria 35, Isluga 33, Chaitén 24).
Todas dependen hoy de los dos mecanismos en cuestión.

**HIPÓTESIS PARA DESPUÉS DEL A/B, no implementada**: que el Test 1 integrado no deba
intersectarse con la máscara contextual. Pasa por las 3 preguntas de MISSION. Los dos casos son
la evidencia.

**Matiz que corrige D19**: en Copahue 2026-07-27, tres pasadas seguidas, nuestro cúmulo está a
2,9 km y MIROVA reporta 2,7 km (mismo objeto). Un cúmulo a ~3 km NO es automáticamente el
artefacto del borde.

**Tres errores propios corregidos en el camino** (los tres de la familia A93 / A90): el techo
artificial de la supervisión humana (lo corrigió Nicolás), el denominador que se movía solo, y
la cota que restaba radios de orígenes distintos (Láscar 4 → 26 noches).

## Seguimiento nuevo (S135, no arreglado a propósito)

**El ground truth de los análisis va hasta una semana atrás del que ve el frontend.**
`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` (35.037 filas, hasta
2026-08-31) es el que consumen el cargador canónico, `scripts/paper_numbers.py` y todas las
mediciones; `latest_consolidado.csv` en la raíz es el que `sync-mirova-csv.yml` actualiza cada hora y el que
consume el frontend. **Corregido el mismo día**: el snapshot NO está congelado — lo refresca
`audit-weekly.yml` (cron lunes 09:00 UTC) con `curl` al repo del scraper, y se actualizó al
07-sep durante la sesión. El desfase real es de hasta una semana, no permanente. No se tocó en
S135 porque cambiar la fuente en medio de una medición comparativa la invalidaría. Al
arreglarlo, ojo con la asimetría: `latest_consolidado.csv` es sólo el canal consolidado; el OCR
fresco sigue en el snapshot. Mitigación ya aplicada: `paper_numbers.py` y
`d19_regimen_vigente.py` recortan toda comparación a la última fecha presente en el CSV y lo
declaran en la salida (antes, seis días de septiembre contaban como «detectamos y MIROVA no»).

## Decisiones que siguen esperando a Nicolás (AUDIT_S134 §D)

**D1 y D2: DECIDIDO Y EN EJECUCIÓN (2026-09-07).** Nicolás autorizó tocar el pipeline, fijó
**cero pérdidas** sobre lo que MIROVA entrega (más exigente que el 10 % propuesto) e instruyó
«ser lo más fiel posible y entender por qué sucede y arreglar cuando diferimos»: una pérdida
NO descarta el brazo, abre una investigación por pasada. Corre sobre los 6 volcanes que
deciden. El segundo pase condicionado está implementado detrás de
`ENABLE_SECOND_PASS_CONDITIONED` (OFF en producción, 17 tests, PR #605) y el A/B de 5 brazos
está lanzado (`reproc-s135-ab-d1d2.yml`, chunk 1 = 06-01→07-15 con overwrite=true; **falta el
chunk 2 = 07-16→08-31 con overwrite=false**). Evaluador pre-escrito:
`experiments/_s135_ab_d1d2/evaluar_ab.py --dir <artefactos>`. Texto viejo, por historia:
**esperaba tres respuestas suyas**
(`docs/PREREGISTRO_AB_D1_D2_S135.md` §«Lo que necesito de vos»): (a) ¿autoriza tocar
`pipeline/detection_context.py` para el brazo del segundo pase condicionado (A45)?; (b) ¿acepta
el umbral de rechazo del criterio 1 (perder >10 % de noches MIROVA-confirmadas en Lastarria,
Tupungatito o Isluga descarta el brazo)?; (c) ¿los 11 Tier A o los 5 que deciden? Sin (a) sólo
corren los brazos A y B. · D3 · D4 · D5 · D6 · D7 · D8. Y una nueva: **qué es el objeto a 2,97 km E del cráter
de Villarrica** (08-31, +8 K sobre un disco plano, dNTI-positivo).
