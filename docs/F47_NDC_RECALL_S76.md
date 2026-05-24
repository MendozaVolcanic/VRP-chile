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
