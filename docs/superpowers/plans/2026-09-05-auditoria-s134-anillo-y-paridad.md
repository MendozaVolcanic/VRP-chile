# Auditoría S134 — el anillo, y por qué nos alejamos de MIROVA

> **Para el agente que ejecuta:** este es un plan de AUDITORÍA, no de implementación. Cada
> frente produce mediciones y hallazgos, no código de producción. Sigue la guía maestra
> `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` y el protocolo del
> proyecto `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`. Todo prompt de auditor empieza pegando
> entero `docs/_prompts/PREAMBULO-AUDITOR.md`.

**Objetivo:** explicar, con evidencia por pasada, por qué la magnitud que publicamos se aleja
de la de MIROVA en régimen débil, partiendo del hallazgo de S133: en 9 de 11 Tier A el cúmulo
que integramos está a 2,3-2,8 km del cráter (`docs/s133/ANILLO_TIER_A.md`).

**Eje nuevo declarado (regla A):** *posición del cúmulo → magnitud publicada → paridad con
MIROVA*, por sensor y régimen, con la **misma pasada y la misma ancla** en los dos sistemas y
con Láscar como control positivo. S104 midió posición (A61/A70) y S131 midió paridad por
cenital; nadie encadenó las dos ni las cruzó con el estrato MODIS que A46 esconde como *far*.

**Lo que este plan NO hace:** no adopta flags, no toca `pipeline/`, no reabre D11-MODIS por la
vía espectral (A82) ni el re-ancla del `ctx_cluster` (A84). Si un frente llega por ahí, lo
reporta como llegada por la vía geométrica, que A82 dejó explícitamente abierta.

---

## 0. Regla C — los pendientes heredados, verificados antes de tocar

La auditoría **empieza** acá (Sonnet, effort bajo). Para cada ítem: ¿sigue abierto contra el
código de HOY? Una lista de pendientes envejece hacia el falso positivo (guía §2.5).

| # | pendiente | origen | qué verificar antes de actuar |
|---|---|---|---|
| P1 | A54: gazetteer de rasgos volcánicos en `volcanoes.yaml` para que la clasificación física de FP sea un `join` | S128 §7, S131 §6.1 | `grep -n "features\|rasgos" volcanoes.yaml`; existe `volcanic_features.yaml`? |
| P2 | D13: el denominador de la cerca `distance_class != summit` del frontend | S124, S131 §6.1 | `docs/MIROVA_DIVERGENCES.md` D13 sigue «documental»? |
| P3 | `mirova_center` por volcán×sensor (hoy uno por volcán) | S128 | `grep -c mirova_center volcanoes.yaml` = 11? |
| P4 | Corpus duplicado (records repetidos por granule) | S128 | `experiments/_s133/analizar_ab_area.py` ya reporta `granules_duplicados`: reusar |
| P5 | `nti_max` persistido en MODIS (patrón A7, seis líneas) | S131 §6.4 | `grep -n nti_max pipeline/process_modis.py` |
| P6 | Guard del timeout de `nrt.yml` contra duración observada | S131 §6.5 | `tests/test_guard_timeout_vs_ventana_s129.py` cubre `nrt.yml`? |
| P7 | Scraper del producto OLI/MSI de MIROVA (`NPixHot`) | S131 §6.7 | ningún repo del ecosistema lo hace; sigue así? |
| P8 | Instrumento para el «≤ 0,17 % contra OSF v2.5» de los coeficientes | S131 §6.8 | `grep -rn "0.17\|OSF" tests/` |
| P9 | Marcador «extensión» para PCC (R15/R16) — decisión volcanológica de Nicolás | S132 | no se hace; se le pregunta |
| P10 | `diag_d9_capped` persistido en el pipeline (A72) | S132 | `grep -n d9_capped pipeline/` |
| P11 | Chunks 2 y 3 del A/B del área | S133 | NO correr: el veredicto no cambia con más datos (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`). Cerrar el pendiente con esa razón |
| P12 | A/B de B22 con ventana ancha y volcanes con más alertas | S133 | diseñar, no correr, hasta que F1-F3 digan dónde está la magnitud |

Cerrados en S133 y que NO se re-auditan: poller de TIF (vivo, 231 snapshots), NRT de MODIS
(colección corregida), cadencia del cron (medida), issues #506 y #567.

Salida de §0: `docs/AUDIT_S134.md` §0 con tres números — confirmados abiertos / ya cerrados /
sin poder verificar — y un guard por cada uno que se cierre (regla B).

---

## 1. Los frentes (disjuntos, un auditor por frente, en paralelo)

### F1 · Posición → magnitud → paridad, por pasada (Fable, effort alto) — EL EJE NUEVO

**Pregunta:** cuando nuestra magnitud se aleja de la de MIROVA, ¿el cúmulo que integramos está
en el cráter o en el flanco? ¿La distancia al cráter predice la razón?

**Script a escribir:** `experiments/_s134_audit/f1_posicion_magnitud_paridad.py`, que:
1. Carga los 11 Tier A desde `data/mirova_equivalent/*.json`, records desde 2026-04-01.
2. Ancla = `vent_lat/vent_lon` de `volcanoes.yaml` (nunca `lat/lon`: en Villarrica el catálogo
   está a 0,85 km del cráter, A13).
3. Distancia `d_crater` = haversine(centroide del `primary_cluster`, ancla).
4. Magnitud publicada: `f5_core_vrp_mw` para VIIRS375, `pc.vrp_mw` para VIIRS750 y MODIS
   (regla A10 con el matiz S132).
5. Ground truth: `pipeline/mirova_csv_loader` (CONS ∪ OCR), pareo **por pasada** (±20 min),
   nunca por noche (A90, S131 §7).
6. Para cada par: razón `ours/mirova`, `d_crater`, sensor, volcán, `sensor_zenith_deg`.
7. Estratifica: por sensor × bin de `d_crater` (≤0,5 · 0,5-1,5 · 1,5-3 · >3 km). Reporta
   mediana de razón, n, y el mismo cruce por volcán.

**Controles obligatorios (guía §3):**
- Positivo: Láscar VIIRS375 (79 % del cúmulo a <500 m). Si el script no lo muestra pegado al
  cráter, el script está mal, no Láscar.
- Negativo: los records `far` (fuera del inner) — la razón ahí debe ser ruido, no señal.
- Línea base roja: correr primero con la ancla = `lat/lon` de catálogo y guardar la tabla;
  después con `vent_*`. Si no cambia nada en Villarrica, la ancla no se está usando (A89).

**Criterio pre-registrado para el hallazgo (escribirlo ANTES de correr):** «la posición
explica la paridad» si la razón mediana del bin ≤0,5 km está dentro de 0,7-1,4 **y** la del bin
>1,5 km está fuera, en ≥ 6 de los 9 volcanes con anillo. Si la razón NO depende de `d_crater`,
la hipótesis de `ANILLO_TIER_A.md` §«Por qué importa» queda refutada y se dice.

**Lo que NO debe hacer:** proponer un gate por distancia (A55, A85); tocar `pipeline/`.

### F2 · Dónde pone MIROVA su cúmulo, misma pasada (Opus, effort alto) — EVIDENCIA EXÓGENA

**Pregunta:** ¿MIROVA integra la celda del cráter o también se corre? Si también se corre, el
anillo no explica la brecha.

**Fuente:** `mirova-tif-archive` en GitHub (18.758 capturas indexadas en `index.csv` con
`acquisition_utc`, `sensor`, `tif_path`, `kmz_path`). **Consultar por el `index.csv` del
remote, nunca listando el directorio**: la API de contenidos corta en 1000 archivos sin avisar
(costó un falso «los TIF pararon en julio» en S133). No clonar el repo (Nicolás: los TIF no se
bajan al PC); bajar sólo los TIF de las pasadas elegidas a `experiments/_s134_audit/tif/`.

**Muestra:** 30 pasadas VIIRS375 nocturnas con alerta MIROVA, 10 de cada régimen: focal
(Láscar), nevado débil (Villarrica, Llaima, Copahue), difuso (PCC). Para cada una, del TIF de
MIROVA: la celda de máxima radiancia dentro del inner y su distancia al `vent_*`. Del nuestro:
`d_crater` del cúmulo de la misma pasada.

**Control de instrumento (S131 §7 ya lo hizo una vez):** el GeoTIFF se refutó como árbitro de
POSICIÓN en S131 (error mediano 4,80 km). Antes de usarlo, reproducir ese control sobre 5
pasadas de Láscar: si el máximo del TIF no cae en el cráter de Láscar, el TIF no sirve para
posición y F2 se cierra con eso como hallazgo, no se fuerza.

**Prueba de campo (guía §0):** las 30 pasadas van a la cola de validación con la URL de
mirovaweb y la del dashboard, para que Nicolás las mire.

### F3 · El mecanismo que corre el cúmulo al flanco (Fable, effort alto) — CÓDIGO vs FÍSICA

**Pregunta:** ¿en qué etapa del ensamblado el cúmulo publicado deja de estar en el cráter?

**Método:** el probe de atribución por etapa de A75 (monkeypatch read-only sobre
`first_pass_tests_2_and_3`, `second_pass_adjacent`, `cluster_hotspots`), aplicado a 3 pasadas
de Villarrica del anillo (elegir las de `d_crater` 2-3 km con `f5_core_vrp_mw` > 0,05) y 3 de
Láscar como control. Capturar la máscara de cada etapa y el centroide resultante.

**Patrones de la guía §1 a buscar por relación:**
- #1 *bug entre dos piezas correctas*: la detección (Test 1) marca el cráter, la selección de
  cúmulo (`cluster_hotspots(vent_anchored)`) elige otro. Trazar el caller (A6): qué ancla recibe
  y qué devuelve, en `scripts/run_pipeline.py:234/277/324` → `get_detection_anchor()`.
- #7 *observable equivocado*: `final_hotspot_dist_km` mide desde el catálogo, el mapa mide
  desde el cráter. Censar todos los campos de distancia del schema y desde qué punto miden (A3).
- #6 *un arreglo que cubre un camino de dos*: ¿el `ctx_cluster` de S106 y el `primary_cluster`
  usan la misma ancla?

**Salida:** tabla etapa × pasada con centroide y `d_crater`, y la afirmación «el cúmulo se
corre en la etapa X» con archivo:línea. Si se corre en `cluster_hotspots`, A84 dice que
re-anclar destruye Lastarria: reportarlo como tensión, no proponer fix.

### F4 · El solape del barrido (Opus, effort medio) — LA LEY DE ÁREA INTERMEDIA

**Pregunta:** ¿cuánto se solapan los píxeles VIIRS adyacentes en el borde del swath, y una
área geolocalizada **descontando el solape** deja los dos bins de cenital en banda?

**Sustrato ya medido:** el A/B de S133 dio control 0,879/0,619 y área geolocalizada
0,958/1,360 (nadir/borde). La ley correcta está entre las dos si la hipótesis del solape es
cierta (`docs/s133/AB_AREA_VEREDICTO_CHUNK1.md`).

**Método, sin reprocesar:** sobre 5 granules VIIRS I-band ya en disco o descargados a
`experiments/_s134_audit/granules/` (uno por bin de cenital), medir con la geolocalización el
paso entre centros y compararlo con el tamaño de píxel del ATBD 423-ATBD-002 Tabla 2.2-1
(`documentacion/VIIRS_Geolocation_ATBD_2014.pdf`, verbatim). La diferencia es el solape.
Ajustar `pixel_areas_from_geolocation` en un **script aparte** (no en `scan_geometry.py`) y
recomputar la razón por bin sobre los pares del A/B ya descargados (`~/ab_area/`, o
re-bajar el run 33912398561 antes del 2026-09-19).

**Criterio pre-registrado:** los dos bins en 0,9-1,1 y cola >2 ≤ 10 %, el mismo de S132. Si
no lo cumple, se reporta y no se ajusta el poste. Si lo cumple, es propuesta de A/B para
S135, con tag y confirmación (A45).

### F5 · Regla C mecánica (Sonnet, effort bajo)

La tabla de §0, ítem por ítem, con el comando y su salida. Sin interpretación: sólo «sigue
abierto / cerrado en commit X / no pude verificar».

---

## 2. Verificación cruzada (el que verifica no es el que encontró)

Cada hallazgo CONFIRMADO de F1-F4 pasa a un verificador con contexto limpio (Opus) que recibe
sólo TÍTULO + ARCHIVO:LÍNEA o SCRIPT, relee, enumera los caminos y pone su propia gravedad.
En ARSAND, seis de seis verificadores encontraron hallazgos propios además: es un segundo
buscador. Lo que el verificador no confirma baja a SOSPECHA.

## 3. Cierre por guard (regla B)

Ningún hallazgo entra a `docs/AUDIT_S134.md` como CONFIRMADO sin un test en `tests/` que lo
mida, o la frase «no medible porque …». Candidatos ya visibles:
- guard de que la ancla de todos los scripts de posición sea `vent_*` y no `lat/lon` (A13);
- guard de que `anillo_tier_a.py` reproduzca Láscar < 0,5 km (control positivo permanente).

## 4. Pruebas de campo para Nicolás (frente M)

`docs/AUDIT_S134.md` §M: tabla ID · pasada UTC · volcán · URL mirovaweb · URL dashboard ·
qué mirar · qué decide. Mínimo las 30 de F2 y las 6 de F3.

## 5. Tabla de decisiones del dueño (guía §6.4)

Se entrega al cierre con opciones y recomendación, no antes. Hoy ya hay tres que esperan:
- P9 marcador «extensión» de PCC;
- el flip de `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` (A/B S132 dio NO ADOPTAR por C2
  tautológico; C2' propuesto en `docs/s133/C2_NORMALIZADO_INNER_RADIUS.md`);
- si B22 se re-corre con ventana ancha (P12).

## 6. Presupuesto y orden

F5 primero y solo (media hora, desbloquea el resto). F1, F2, F3 en paralelo (worktrees
dedicados, A44), F4 después de F1. Cierre: `docs/AUDIT_S134.md` con los tres números de la
regla C, `docs/INDEX.md` en la misma sesión (S133 lo incumplió), memoria, bloque S135.

## Auto-revisión del plan

- Cobertura del pedido de Nicolás: anillo en todos los volcanes → F1 (medido) + F3 (mecanismo);
  «por qué nos alejamos de MIROVA» → F1 + F2; «explorar nuevas formas» → F4; pendientes → §0.
- Sin placeholders: cada frente tiene script, fuente, controles y criterio pre-registrado.
- Consistencia: `d_crater` y `vent_*` se usan con el mismo nombre en F1, F2, F3 y §3.
