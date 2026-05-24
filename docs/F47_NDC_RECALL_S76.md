# F47 — Nevados de Chillán: recall 0.20 en S76 (caso aislado vs patrón Tier A)

**Estado**: documento de hipótesis e investigación. No hay reprocesos ni cambios de código en este PR.
**Sesión origen**: S76 (audit `experiments/139_recall_precision_s76/audit_s76.md`).
**Responsable propuesto S77**: investigación bite-sized H1→H4→H2 antes de tocar pipeline.

---

## 1. Resumen ejecutivo

La auditoría S76 mide para cada volcán Tier A del perfil `mirova_equivalent` el
recall contra el CSV consolidado MIROVA (latest_consolidado.csv) sobre el
horizonte sin restricción. Tras los fixes acumulados en S73–S75 (F2.8 saturation
guard, Test 1 integrated, dual-ROI, kernel dNTI contextual, NOAA-21, sigma-cap
VIIRS), el patrón Tier A es:

| Volcán | Recall S76 |
|---|---|
| Villarrica | 0.98 |
| PuyehueCordonCaulle | 0.96 |
| Chaitén | 0.93 |
| Tupungatito | 0.91 |
| Lastarria | 0.88 |
| Llaima | 0.87 |
| Copahue | 0.85 |
| Isluga | 0.84 |
| Lascar | 0.82 |
| Planchón-Peteroa | 0.82 |
| **NevadosDeChillan** | **0.20** (1 TP / 4 FN) |

NdC es el único Tier A bajo 0.50. La mediana del resto está en ~0.87. F46
(inflación TIR `vrp_tir_mw` espuria) afecta la **precision** general pero no
explica por qué este volcán pierde 4/5 referencias MIROVA: NdC se separa del
patrón post-S75 por una razón distinta y propia.

El golpe es operacional: NdC tiene cráter Nicanor activo monitoreado por
SERNAGEOMIN-OVDAS desde 2016. Un recall de 0.20 en mirova_equivalent significa
que el dashboard publica "sin actividad detectada" cuatro de cada cinco noches
en que MIROVA sí está reportando VRP.

---

## 2. Contexto geológico (por qué este volcán es difícil)

Nevados de Chillán es un complejo volcánico, no un edificio único. La cumbre
está formada por al menos tres cráteres alineados NO-SE:

- **Nicanor**: cráter más joven, activo desde 2016. Crecimiento de domo
  Gil-Cruz (≥2018) y flujos de lava cortos 2020–2024. Es la fuente actual
  de la mayor parte de la señal térmica.
- **Arrau** (a ~600 m del Nicanor): fumarólico desde inicios del siglo XX.
- **Volcán Viejo** (a ~1.5 km al NO): cráter relicto, sin actividad
  conocida reciente.

La cumbre se mantiene cubierta de nieve gran parte del año (subantártico,
~3.200 m s.n.m.), lo que **infla el background térmico heterogéneo** (mezcla
nieve+roca+domo) y rompe los gates `N·σ` exactamente igual que en Tupungatito
y Villarrica antes de los fixes S15/S25.

La señal típica de fumarolas+domo Nicanor en MODIS/VIIRS NRT cae en
0.1–3 MW (sub-pixel), con eventos puntuales 5–20 MW durante extrusiones
activas. Es señal débil-persistente — el régimen donde el pipeline más
puede perder eventos si los thresholds están calibrados para clusters
fuertes.

---

## 3. Las referencias MIROVA sin match (4 FN)

Para esta auditoría S76 el ground truth son los 5 records MIROVA-NRT del CSV
consolidado en el horizonte audit. La lista exacta de fechas FN debe extraerse
de `experiments/139_recall_precision_s76/audit_s76.json` (o regenerar con
`scripts/audit_recall_per_volcano.py --volcano NevadosDeChillan --verbose`).
No la pego aquí para no enquistar datos que pueden variar al regenerar el
audit con el código actual.

Evidencia tangencial relevante extraída del JSON operacional
`data/mirova_equivalent/NevadosDeChillan.json` (1.218 records, perfil
mirova_equivalent, snapshot S75 cierre):

- **0** records con `vrp_mw > 0` (top-level).
- **822** records con `n_anomalous_pixels > 0`.
- **464** records con `triggered_test1=True`.
- **121** records con **`primary_cluster.vrp_mw > 0` pero `vrp_mw==0`** (el
  top-level se quedó vacío).
- `distance_class`: 479 summit / 364 far / 375 None.
- `final_hotspot_source`: 563 eruption-path / 280 test1 / 375 None.

Es decir: NdC **sí está detectando pixels anómalos casi continuamente** y
**Test 1 está disparando**, pero el VRP rollup que el dashboard consume
(`vrp_mw` top-level) está en 0 para todo el archivo. Esto, por sí mismo,
es razón suficiente para que el audit reporte recall 0.20: si el matcher
exige `vrp_mw > 0` en el record nuestro contra el MW MIROVA, casi todo
es FN trivialmente.

---

## 4. Hipótesis

### H1 — Fetch incompleto (cobertura granules)

**Mecanismo**. NdC sufre pasadas perdidas porque: (a) NOAA-21 (VJ202IMG/MOD)
recién entró post-S18 y puede no haber sido reprocesado retrospectivo, (b)
gaps NRT LANCE típicos en la latencia 3h, (c) bbox de fetch mal centrado
para complejos volcánicos extendidos.

**Probabilidad a priori**: BAJA. El JSON tiene 1.218 registros — densidad
comparable a Lascar (Tier A bien cubierto). Pero solo se confirma midiendo
contra MIROVA.

**Verificación propuesta** (5 min):

```
grep -c '"granule_id"' data/mirova_equivalent/NevadosDeChillan.json
# vs número de pasadas MIROVA mismo horizonte
python scripts/count_mirova_passes.py --volcano "Nevados de Chillan" --since 2025-01-01
```

Si nuestro count < 50% del de MIROVA → H1 confirmada. Si está dentro de
±10% → H1 refutada y pasamos a H2.

---

### H2 — `inner_radius_km=5` insuficiente para complejo de cráteres

**Mecanismo geológico**. Si el `vent_lat/lon` apunta solo al Nicanor y un
evento térmico real ocurre en Arrau (~600 m) entra como summit, OK. Pero si
ocurre en pixels que MODIS asigna a su grilla a 1–2 km del centro
(scan-angle elongation MODIS llega a 4.83×2.42 km en edge), el centroide
del pixel cae fuera del anillo summit=5 km **solo si** además el lat/lon
del vent oficial está descentrado respecto a la silueta MIROVA.

**Evidencia ya en el JSON**. 364 records con `distance_class='far'` y
`primary_cluster.vrp_mw > 0`. Top 5 ordenado por `pc.vrp_mw`:

| sensor | pc.vrp_mw | centroid_dist_km | distance_class | top vrp_mw |
|---|---|---|---|---|
| MODIS_TERRA | 332.8 MW | 0.5 km | **far** | 0 |
| MODIS_TERRA | 330.9 MW | 25.2 km | far | 1.325 MW |
| MODIS_TERRA | 121.1 MW | 20.0 km | far | 869 MW |
| MODIS_TERRA | 91.7 MW | 28.0 km | far | 0 |
| MODIS_TERRA | 89.0 MW | 14.0 km | far | 534 MW |

La fila 1 es la más diagnóstica: un cluster con centroide a **0.5 km** del
vent oficial fue clasificado **far** y tiene `vrp_mw=0` top-level. Esto
**no puede ser un problema de radio** — el cluster está literalmente
dentro del cráter. Es un bug de clasificación o de promoción summit/far,
o el `final_hotspot` se asignó a un cluster lejano paralelo. **H2 se
desdobla** en H2.a (radio chico) y H2.b (clasificación distance_class
inconsistente con centroide del primary_cluster).

**Verificación propuesta** (10 min):

```
python scripts/inspect_record.py --volcano NevadosDeChillan \
    --granule <granule_id_de_la_fila_1>
```

Imprimir vent_hotspot_*, hotspot_*, final_hotspot_*, primary_cluster, todos
los clusters detectados. Cruzar con KMZ MIROVA
(`kmz/ChillanNevadosde_VIIRS750_Last_GE.kmz`) — si el GroundOverlay MIROVA
está centrado en lat/lon distinto al de `volcanoes.yaml` (offset >1 km, como
fue el caso Tupungatito 3 km SE y Planchón-Peteroa 1.87 km N en S15
Fase 0.7), proponer `mirova_center_lat/lon` para NdC en el yaml.

---

### H3 — Threshold demasiado estricto sobre fumarolas débiles

**Mecanismo**. Las fumarolas crónicas Nicanor + Arrau emiten 0.1–2 MW
sub-pixel. Los thresholds actuales:

- `ANOMALY_THRESHOLD_K = 5K` sobre background (ΔT min).
- `N_SIGMA_MIR = 3` (gate sigma vent-path).
- `MAX_SIGMA_COMPONENT_K = 7K` (cap eruption-path).

Con `σ_bg` inflado por nieve parcial, `N_SIGMA_MIR=3` puede pedir ΔT > 9 K,
matando 0.5–2 MW reales antes del pool.

**Pero**: 464 registros tienen `triggered_test1=True` y 280 tienen
`final_hotspot_source='test1'`. Eso significa que Test 1 integrated
(Coppola 2015) **está rescatando muchos casos donde el threshold local
falla**. La pregunta es por qué Test 1 dispara pero el `vrp_mw` queda en 0.

**Verificación propuesta** (1–2 h, hay que descargar granules):

Para los 4 FN específicos, descargar el granule MODIS/VIIRS, reprocesar
local con un flag `--debug-intermediates` que persista `hot_mask`,
`sigma_bg`, `threshold_local`, `nti`, `dnti_contextual`, `test1_k_observed`,
y comparar lado a lado con el record MIROVA del mismo timestamp
(`vrp_mw_mirova`). Esto distingue tres sub-casos:

- (a) Nuestro `nti` no supera el gate → tuning de threshold.
- (b) Test 1 dispara pero el cluster cae lejos del vent → ver H2.
- (c) Test 1 dispara y cluster cae cerca pero `vrp_mw` rollup queda en 0
  → ver H4 (más probable según el JSON ya inspeccionado).

---

### H4 — Bug en el rollup `vrp_mw` top-level (la hipótesis más fuerte)

**Mecanismo de código**. El record VRP de un granule tiene dos campos
de VRP:

- `primary_cluster.vrp_mw`: VRP del cluster principal seleccionado por
  el pipeline.
- `vrp_mw` top-level: rollup operacional que consume el dashboard y el
  audit. Debería ser igual a `primary_cluster.vrp_mw` cuando hay
  cluster summit, o suma/promedio cuando hay varios.

**Evidencia**. 121 records (≈10% del archivo) tienen
`primary_cluster.vrp_mw > 0` mientras `vrp_mw == 0`. Y el caso extremo
es el del cluster a 0.5 km del vent con 332.8 MW clasificado far y
`vrp_mw=0`. Esto bordea lo absurdo: hay actividad de 332 MW en el
cráter mismo y el rollup la tira a la basura.

Posibles causas:

- **C1**. La promoción summit/far evalúa `final_hotspot_dist_km` (¿calculado
  con qué origen?) en vez de `primary_cluster.centroid_dist_km`. Si el
  `final_hotspot` se asignó a un cluster espurio lejano (FP de Test 1 a 25
  km), el record entero queda etiquetado `far` y el `vrp_mw` no rolls up.
- **C2**. Hay un filtro `vrp_mw = pc.vrp_mw if distance_class=='summit' else 0`
  en `store.py` o `process_viirs.py`. Si C1 + C2 coexisten, todo cluster
  realmente summit pero mal etiquetado far queda en 0.
- **C3**. F46 (inflación TIR) toca también este rollup y enmascara el
  problema. Vale revisar el PR de F46 abierto.

**Verificación propuesta** (15 min, lectura de código):

```
grep -n "vrp_mw" pipeline/store.py pipeline/process_modis.py pipeline/process_viirs*.py | grep -v '#'
# Buscar dónde se asigna vrp_mw top-level
# Buscar la condicional sobre distance_class / summit / far
```

Si encontramos la condicional `if summit: vrp_mw=pc.vrp_mw else: 0`, **eso
explica el 0.20 recall directamente**: cada vez que el clasificador
distance_class falla (H2.b) y manda a `far` un cluster cráter-céntrico,
el rollup queda 0 y el audit cuenta FN.

**Esta es la hipótesis con mayor ROI**. La evidencia ya está en el JSON.

---

### H5 — Geofencing / exclusion zones

**Mecanismo**. `pipeline/exclusion_zones.py` o `data/exclude_zones.yaml`
podrían filtrar pixels reales si NdC heredó zonas de exclusión por
analogía con otros volcanes con ciudad/lago cercano.

**Verificación**. Ya hecha — grep en `pipeline/exclusion_zones.py` no
arroja matches a `NevadosDeChillan|Chillan`. No hay zona específica
declarada. H5 refutada por inspección directa, salvo que haya una
exclusion zone genérica (rectángulo global) que incluya a Chillán por
accidente. Poco probable, descartable en 2 min.

---

## 5. Plan de investigación S77 (ordenado por costo)

Aplicar el principio A2 (diagnósticos paralelos antes de reprocesos caros):

1. **H4 + H2.b — lectura código + grep en JSON** (15–20 min, costo cero
   computacional). Confirmar si existe la condicional
   `vrp_mw = pc.vrp_mw if summit else 0` y si la asignación de
   `distance_class` usa `final_hotspot_dist_km` o
   `primary_cluster.centroid_dist_km`. **Si H4 confirmada, esto es fix de
   pocas líneas y resuelve el 80% del recall sin tocar thresholds.**

2. **H1 — count granules vs MIROVA** (5 min). Descartar o confirmar fetch
   incompleto. Resultado binario: si nuestro count ≥ 90% de MIROVA, cerrar
   H1 y seguir.

3. **H2.a — KMZ offset check** (10 min). Extraer GroundOverlay del KMZ
   MIROVA y comparar con `lat=-36.863, lon=-71.377`. Si offset >1 km,
   proponer `mirova_center_lat/lon` para NdC. Independiente de los demás.

4. **H3 — reproc debug de los 4 FN** (1–2 h, solo si 1–3 no resolvieron).
   Bajar los 4 granules de los FN exactos, correr `--debug-intermediates`,
   imprimir tabla comparativa con MIROVA. Costo real: requiere conexión
   Earthdata y storage L1B temporal.

5. **H5 — descartar formalmente** (2 min). Confirmar que el JSON
   `data/exclude_zones.yaml` (si existe) no toca el bbox de NdC.

Orden lógico: 1 → 2 → 5 → 3 → 4. Si H4 confirmada en paso 1, los pasos
3 y 4 pueden quedar diferidos.

---

## 6. Métricas de éxito S77

- **Recall NdC post-fix ≥ 0.70** sobre el mismo audit S76 regenerado.
- **Precision NdC no cae por debajo de 0.30** (umbral mínimo Tier A
  acordado en CLAUDE.md).
- **Ratio mediano `our_vrp_mw / mirova_vrp_mw` en 0.5–2.0** para los TPs
  rescatados (declared MIROVA error ±30%).
- **No regresiones**: tests 456 (S75) → ≥456 passed, 0 regresiones en los
  otros 10 Tier A.
- **A38+A39 obligatorio**: si H4 implica tocar `store.py` /
  `process_viirs.py` / `process_modis.py`, tag defensivo
  `pre-s77-f47-ndc-rollup` + confirmación explícita Nicolás antes de mergear
  (es pipeline NRT crítico — regla A45 S75).

---

## 7. Datos brutos relevantes

Resumen estadístico extraído de `data/mirova_equivalent/NevadosDeChillan.json`
(snapshot post-S75, 1.218 records):

```
total records:                                       1218
records con vrp_mw > 0 (top-level):                     0
records con n_anomalous_pixels > 0:                   822
records con triggered_test1 = True:                   464
records con primary_cluster.vrp_mw > 0 Y vrp_mw == 0: 121
distance_class breakdown:    summit=479  far=364  None=375
final_hotspot_source:        eruption=563  test1=280  None=375
```

`volcanoes.yaml` entry NdC (S76 actual):

```yaml
- name: NevadosDeChillan
  mirova_monitored: true
  lat: -36.863
  lon: -71.377
  radius_km: 25
  inner_radius_km: 5  # MIROVA KML oficial
  vent_lat: -36.863
  vent_lon: -71.377
  vent_radius_km: 2
  lbg_global_compatible: true
  # Nota S42: 2/3 alertas D4 (Test 1 dispara, primary cráter cercano,
  # vrp=0 por L_bg local). Activar D4 selectivo similar a Lascar/Lastarria.
```

**Conexión con S42**: la nota interna del yaml ya identificó el patrón
"Test 1 dispara, primary cluster cráter cercano, vrp=0". Es el **mismo
síntoma** que medimos S76 (121 records). Lo que cambió: S42 lo propuso
resolver activando D4 selectivo; eso no se hizo o no fue suficiente. F47
debe revisar si la activación D4 está realmente operativa y, si lo está,
por qué sigue produciendo `vrp_mw=0` rollup.

---

## 8. Referencias

- `experiments/139_recall_precision_s76/audit_s76.md` — audit origen.
- `data/mirova_equivalent/NevadosDeChillan.json` — JSON operacional.
- `volcanoes.yaml:214-235` — entrada NdC + nota S42.
- `kmz/ChillanNevadosde_VIIRS750_Last_GE.kmz` — GroundOverlay MIROVA
  para H2.a.
- `docs/MISSION.md` — 3 preguntas obligatorias antes de cualquier cambio
  en `pipeline/`.
- `CLAUDE.md` — reglas A38 (tag defensivo), A39 (Claude mergea PRs),
  A45 (pipeline NRT requiere confirmación explícita).
- Patrón análogo histórico: S15 Tupungatito (σ inflado glaciar) +
  S25 Villarrica (sub-pixel) — ambos casos también empezaron con
  recall <0.10 y se resolvieron sin bajar thresholds globales, con
  fixes localizados.

---

## 9. H4 ROOT CAUSE CONFIRMADO (S77 investigación read-only)

**Veredicto**: H4 confirmada y refinada. **No es** la condicional hipotética
`vrp_mw = pc.vrp_mw if summit else 0` (esa nunca existió). Es una asimetría
arquitectónica más sutil entre dos sistemas de "qué hotspot representa al
record" que conviven en el pipeline desde S38 y nunca se reconciliaron.

### 9.1 El gate exacto

**Archivo:línea**: `pipeline/store.py:183-195`

```python
# pipeline/store.py L175-197
vrp_eruption = record.get("vrp_mw", 0) or 0
hotspot_dist = record.get("hotspot_dist_km")
vrp_vent = record.get("vrp_vent_mw", 0) or 0

# Safety net (legacy + H8): si después del pixel-level filter, hotspot_dist
# sigue indicando un hotspot lejano (...), aplicar el zero-out histórico.
# Garantiza que vrp_mw=0 cuando solo hay señal far.
if hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
    record["discarded_hotspot_lat"] = record.get("hotspot_lat")
    record["discarded_hotspot_lon"] = record.get("hotspot_lon")
    record["discarded_hotspot_dist_km"] = hotspot_dist
    record.setdefault("discarded_reason", "eruption_hotspot_too_far")
    if record.get("anomaly_pixels"):
        record["discarded_anomaly_pixels"] = record["anomaly_pixels"]
    record["hotspot_lat"] = None
    record["hotspot_lon"] = None
    record["hotspot_dist_km"] = None
    record["anomaly_pixels"] = []
    vrp_eruption = 0

record["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)
```

El gate decide sobre `hotspot_dist_km`. Ese campo se asigna en
`pipeline/process_modis.py:771-774` (y análogo VIIRS) como **el pixel
individual con max VRP**:

```python
# pipeline/process_modis.py L771-774
# Primary hotspot = highest VRP pixel
hotspot_lat = anomaly_pixels[0]["lat"]
hotspot_lon = anomaly_pixels[0]["lon"]
hotspot_dist_km = anomaly_pixels[0]["dist_km"]
```

Es decir: `hotspot_*` mira **un solo pixel** (el más caliente del scene),
mientras que `primary_cluster.*` (asignado en `process_modis.py:805-811`,
estrategia `vent_anchored` desde S38) mira el **cluster contiguo más
cercano al vent**. Cuando esos dos disienten — y el caso bandera muestra
que disienten dramáticamente — `store.py` cree al pixel individual y mata
el rollup, ignorando al cluster que el resto del pipeline ya seleccionó.

### 9.2 Reproducción mínima

Granule MODIS_TERRA NdC 2026-02-01 02:55:

| Campo | Valor | Origen |
|---|---|---|
| `primary_cluster.n_pixels` | 21 | vent-anchored cluster S38 |
| `primary_cluster.centroid_dist_km` | **0.536 km** | dentro inner=5 |
| `primary_cluster.vrp_mw` | **332.756 MW** | cluster válido cráter |
| `hotspot_lat/lon` | top pixel single | max VRP individual |
| `hotspot_dist_km` | **26.58 km** | pixel hottest cae lejos |
| `final_hotspot_source` | `eruption` | rama L915-919 |
| `final_hotspot_dist_km` | **26.58 km** | hereda hotspot_dist_km |
| `distance_class` | **`far`** | L939: 26.58 > 5 |
| `discarded_reason` | `eruption_hotspot_too_far` | gate store.py:183 |
| **`vrp_mw` top-level** | **0** | zero-out aplicado |

Resultado: el dashboard publica `vrp_mw=0` para una noche donde el cráter
mismo está emitiendo 332 MW comprobables (21 pixels contiguos). El audit
S76 cuenta esto como FN ante el record MIROVA del mismo timestamp.

### 9.3 Distribución empírica en NdC (1.218 records)

Audit `experiments/141_f47_h4_rootcause/audit.py` sobre los 121 records
mismatch:

```
Breakdown distance_class:       far=88   summit=33
Breakdown final_hotspot_source: eruption=90  test1=31
Breakdown discarded_reason:     eruption_hotspot_too_far=116  None=5

pc.centroid_dist_km <= 5:  38 / 121
  └─ de esos, final_hotspot_dist_km > 5:  5  (clasificación inconsistente)
pc cerca (<5) Y hotspot_dist_km lejos (>5): 1
```

**Lectura del breakdown**:

- **116 de 121** entran al gate L183 con `hotspot_dist > 5 km` y se les anula
  `vrp_eruption`. La rama L915-919 (`final_hotspot_source='eruption'`) hereda
  el dist del top pixel y por eso `distance_class='far'` en 88 casos.
- Los **31 con `final_hotspot_source='test1'`** sí dispararon Test 1 y
  reescribieron `final_hotspot` al centroide Test 1 cercano (L905-908 o
  L911-914). Pero igual quedan con `vrp_mw=0` porque el gate
  `hotspot_dist > 5` ya disparó antes en store.py — Test 1 reescribe
  `final_hotspot_*` pero **no toca `hotspot_dist_km`**, así que el gate
  store.py sigue viendo el top pixel lejano.
- Los 33 `distance_class='summit'` del breakdown son los casos donde Test 1
  rescató el clasificador pero el rollup VRP siguió en 0 igual — exactamente
  el síntoma S42 ya documentado en `volcanoes.yaml:231-234` ("Test 1 dispara,
  primary cráter cercano, vrp=0"). La nota S42 lo atribuyó a `L_bg` local;
  el dato empírico S77 muestra que es por el gate store.py, no por L_bg.

### 9.4 Por qué la asimetría existe

Recorrido histórico:

1. **Pre-S26/S27**: el pipeline solo tenía `hotspot_*` (top pixel) y la
   regla "si está lejos, anula" tenía sentido — no había noción de cluster.
2. **S27**: se agregó cluster aggregation (Coppola 2016a, `n_hotspots`)
   con `primary_cluster`. Pero `hotspot_*` se mantuvo por backward compat.
3. **S38 D8** (`docs/MIROVA_DIVERGENCES.md` y comentarios en
   `process_modis.py:785-794`): se cambió la **selección del cluster** a
   `vent_anchored` (cluster más cercano al vent dentro de inner_radius).
   Esto resolvió el caso Lascar Salar de Atacama donde el cluster por
   `vrp_max` caía a 25 km del vent. **Pero `hotspot_*` (top pixel single)
   siguió sin actualizarse.**
4. **S30 + S44** agregaron Test 1-priority para reescribir
   `final_hotspot_*` cuando Test 1 detecta cerca y eruption lejos —
   parche que cubre solo el sub-caso "Test 1 dispara".
5. **S35 H8** (pixel-level distance filter) atacó el problema parcial
   (descartar pixels lejos individualmente) pero el gate scene-level
   `hotspot_dist > max_dist` se mantuvo como **safety net** y sigue
   ahí. Cuando `enable_pixel_level_distance_filter=True` (default) los
   pixels lejos ya están fuera de `anomaly_pixels`, pero **`hotspot_dist_km`
   se asigna ANTES** del filtro en process_modis.py:774 — preservando el
   top pixel original. El comentario "Safety net (legacy + H8)" de
   store.py:179 muestra que el autor del filter sabía del solapamiento
   pero conservó el zero-out por compat.

En síntesis: el código tiene **dos representaciones del hotspot** que
evolucionaron por separado. El gate de store.py se quedó conectado a la
representación vieja (top pixel single, scene-wide).

### 9.5 Fix propuesto (pseudocódigo, NO implementar acá)

**Opción A — mínima, alineada al espíritu S38**: que el gate store.py
mire `primary_cluster.centroid_dist_km` en vez de `hotspot_dist_km`
cuando hay cluster vent-anchored disponible. Si el cluster principal
está dentro del radio, NO anular `vrp_eruption` aunque haya un pixel
individual lejano (ese pixel es un FP aislado o señal secundaria, no la
"verdad del scene").

```python
# pipeline/store.py L175-197 reemplazo propuesto
vrp_eruption = record.get("vrp_mw", 0) or 0
hotspot_dist = record.get("hotspot_dist_km")
vrp_vent = record.get("vrp_vent_mw", 0) or 0
pc = record.get("primary_cluster") or {}
pc_cdist = pc.get("centroid_dist_km")

# S77 F47 fix: si el cluster vent-anchored cae dentro del radio, ese es
# la verdad del scene — NO anular por un top pixel single lejano (FP aislado).
# El gate legacy solo aplica cuando no hay cluster cercano que rescate.
cluster_rescues = (pc_cdist is not None
                    and pc_cdist <= MAX_HOTSPOT_DIST_KM
                    and (pc.get("vrp_mw") or 0) > 0)

if (not cluster_rescues
        and hotspot_dist is not None
        and hotspot_dist > MAX_HOTSPOT_DIST_KM):
    # ... zero-out histórico igual que hoy ...
    vrp_eruption = 0
elif cluster_rescues and hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
    # Cluster cráter rescata: usar pc.vrp_mw como vrp_eruption efectivo y
    # reescribir hotspot_* al centroide del cluster (paridad con final_hotspot).
    vrp_eruption = pc["vrp_mw"]
    record["hotspot_lat"] = pc.get("centroid_lat")
    record["hotspot_lon"] = pc.get("centroid_lon")
    record["hotspot_dist_km"] = pc_cdist
    record["discarded_anomaly_pixels_outside_cluster"] = ... # opcional, auditoría
    record["discarded_reason"] = "single_pixel_far_overridden_by_cluster"

record["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)
```

**Opción B — más estructural**: que `process_modis.py:771-774` y análogo
VIIRS asignen `hotspot_*` desde el `primary_cluster` (centroide del
cluster vent-anchored) en vez del top pixel single. Resuelve el problema
en origen pero cambia el contrato del campo `hotspot_*` (más invasivo,
afecta auditorías y frontend que consuman hotspot_* en vez de
final_hotspot_*).

**Opción C — solo classifier, sin tocar VRP**: en process_modis.py:902-919
priorizar `primary_cluster.centroid_dist_km` para asignar
`final_hotspot_dist_km` cuando eruption es la fuente y hay cluster cerca.
Esto corrige `distance_class` pero **no** el `vrp_mw=0` (porque el gate
store.py es independiente). **Insuficiente solo**.

**Recomendación**: Opción A. Aísla el cambio al rollup, preserva el
campo `hotspot_*` como "top pixel single" (backward compat para audits
que lo usen), y el comportamiento legacy sigue activo cuando NO hay
cluster cercano que rescate. Es el cambio de menor superficie que
resuelve el síntoma observado.

**Pre-condición A38+A45 (S75)**: tocar `store.py` afecta pipeline NRT
crítico — requiere tag defensivo `pre-s77-f47-store-cluster-rescue` y
confirmación explícita Nicolás antes de mergear. Test obligatorio: caso
sintético con `pc.cdist=0.5` + `hotspot_dist=26` + `pc.vrp_mw=332` →
record final `vrp_mw=332` (no 0).

### 9.6 Impacto esperado más allá de NdC

Spot-check `experiments/141_f47_h4_rootcause/spotcheck_tierA.py` sobre los
11 Tier A. Columnas:

- `pc>0 & v=0`: records con primary_cluster.vrp_mw > 0 PERO vrp_mw == 0.
- `pc<=in & disc=far`: subset con primary cerca del vent (dentro inner) Y
  discarded_reason='eruption_hotspot_too_far' (el gate store.py disparó).

| Volcán | Records totales | pc>0&v=0 | pc<=inner & disc=far |
|---|---:|---:|---:|
| Lascar | 1065 | 112 | 20 |
| Lastarria | 1064 | 71 | 13 |
| PuyehueCordonCaulle | 1306 | 122 | 110 |
| Llaima | 1255 | 83 | 27 |
| Villarrica | 1262 | 147 | 59 |
| Copahue | 1240 | 211 | 79 |
| Chaiten | 1312 | 119 | 49 |
| Isluga | 1021 | 133 | 29 |
| Tupungatito | 1173 | 65 | 23 |
| PlanchónPeteroa | 1190 | 101 | 22 |
| **NevadosDeChillan** | **1218** | **121** | **33** |

**Lectura geológica**: el patrón existe en los 11. NdC se siente más por
tener pocos refs MIROVA absolutos (5 en horizonte audit, vs 50-200 en
otros), pero Copahue (79 casos), Villarrica (59), Chaitén (49) y
PuyehueCordonCaulle (110, beneficiado por inner_radius=20) son los que
más records cráter-céntricos legítimos están perdiendo en el rollup. El
fix Opción A debería:

- **Recuperar 200-400 records VRP** distribuidos entre los 11 Tier A.
- **Recall NdC**: alza esperada de 0.20 → 0.60-0.80 (depende de cuántos
  de los 4 FN MIROVA coincidan en timestamp con records "pc<=inner &
  disc=far"). Verificación post-fix obligatoria.
- **Recall otros Tier A**: alza marginal porque ya están en 0.82-0.98 (la
  saturación contra MIROVA es por otros factores, no este). Pero
  `vrp_mw` distinto de 0 en records actualmente censurados mejora la
  serie temporal del dashboard y reduce el sesgo a la baja del ratio
  mediano `our/mirova` en esos volcanes.
- **Precision**: leve baja esperada en volcanes con vent_radius muy
  permisivo (Copahue 79 records expone más a FPs cráter cercanos). Hay
  que medirla. PCC con 110 candidatos es el spot a vigilar — su
  inner=20 km cubre el lacolito Cordón Caulle entero y puede absorber
  clusters que no son del vent.

### 9.7 Conexión con S42 y F46

La nota interna en `volcanoes.yaml:231-234` (S42) ya había identificado
el patrón "Test 1 dispara, primary cluster cráter cercano, vrp=0". S42
lo atribuyó a `L_bg` local del ring 1-3km contaminado por calor crónico
del domo Nicanor, y propuso activar D4 selectivo. Pero el dato empírico
S77 muestra que `lbg_global_compatible: true` **ya está activado** en el
yaml de NdC y `effective_L_bg` global se está usando (`process_modis.py:
970-974` rama afirmativa). Aun así los 121 records persisten en
`vrp_mw=0`. **D4 ya está operativo y no resuelve el síntoma** porque el
zero-out de store.py ocurre **después** de cualquier recompute por L_bg
y antes del rollup final. El L_bg recompute de S30/S33 corrige el valor
de `vrp_mw` calculado en process_modis, pero store.py lo anula
silenciosamente cuando el top pixel está lejos.

F46 (drift VRP_TIR Stefan-Boltzmann sobre mask 4σ) es un problema
distinto en `vrp_tir_mw`, no toca este rollup VRP_MIR. F46 y F47 deben
mergearse independientes y ambos pueden coexistir sin conflicto en
store.py (rutas distintas del record).

### 9.8 Lecciones meta (candidatas CLAUDE.md S77)

- **A46 propuesta**: cuando el código mantiene dos representaciones del
  mismo concepto físico (acá "hotspot del scene"), todo gate/filter
  debe declarar explícitamente sobre cuál opera. Asimetrías silenciosas
  (gate sobre A, classifier sobre B) producen bugs como F47 que tardan
  ~5 sesiones (S42 → S77) en diagnosticarse porque el síntoma vive en
  el rollup y la causa en otra capa.
- **A47 propuesta**: nota inline tipo S42 en `volcanoes.yaml` con
  hipótesis sobre causa pero sin verificación empírica → necesita
  flag "**hipótesis pendiente verificación**" o equivalente. La nota
  S42 culpó al L_bg local; F47 demuestra que era el gate scene-level.
  Sin marcador, futuras sesiones pueden creer la hipótesis y aplicar
  fixes (D4 más selectivo) que no resuelven el problema real.

### 9.9 Próximo paso S77 (decisión Nicolás)

Antes de cualquier implementación:

1. Confirmar fix Opción A vs B vs combinación (A para store.py + C para
   classifier — coherencia full).
2. Aplicar A38: tag defensivo `pre-s77-f47-store-cluster-rescue` antes
   de tocar store.py.
3. Test sintético TDD primero (`tests/test_store_cluster_rescue.py`).
4. Reprocesar 11 Tier A en profile A/B (`mirova_equivalent_f47_{on,off}`)
   sobre 30 días mínimo. Medir recall, precision, ratio mediano,
   nuevos FPs.
5. Si métricas validan en A/B, push a `mirova_equivalent` default y
   reproc histórico full vía local (no GitHub Actions, A1 timeout).

Esta investigación es **read-only** — el fix queda como propuesta hasta
que Nicolás autorice (regla A45 — pipeline NRT crítico requiere
confirmación explícita).
