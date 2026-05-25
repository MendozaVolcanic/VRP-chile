# F63 — Cluster connectivity brainstorm (S78)

**Status**: read-only investigation. No pipeline / data changes.
**Trigger**: Copahue 141 FPs en Caviahue (lago a ~14 km del vent). Hipótesis del usuario:
"el clustering se extiende hasta el lago por threshold demasiado generoso".
**Veredicto**: hipótesis **REFUTADA en su forma original** — el cluster NO se "extiende"
geográficamente hasta Caviahue. Pero descubrí un mecanismo **distinto y peor**: clusters
lejanos aislados son **elegidos como primary_cluster** cuando los clusters cercanos al vent
tienen `vrp_mw=0` (clip D4). Detalle abajo.

---

## 1. Cómo MIROVA agrupa pixels (Coppola 2016a §2.2)

> "Once a pixel is flagged as active, neighbor pixels within ~1 km are aggregated
> into a single hotspot/cluster."

Interpretación: connectivity **espacial de vecindad**, no clustering por distancia
métrica arbitraria. Para sensores con pixel size ≤ 1 km (MODIS 1km, VIIRS-M 750m,
VIIRS-I 375m) la "vecindad 1 km" se implementa naturalmente como **8-connectivity
en grid** (pixel vecino directo o diagonal).

---

## 2. Cómo VRP-Chile agrupa pixels — auditoría de `pipeline/clustering.py`

Hay **dos funciones**:

### 2.1 `cluster_hotspots()` — la que usa el pipeline NRT

- Operación: `scipy.ndimage.label(hot_mask_2d, structure=8-conn)`.
- Conexión: 8-vecindad **en índices de grid**, no en distancia métrica.
- Distancia implícita entre vecinos:
  - MODIS 1 km grid → 8-conn = **hasta ~1.41 km diagonal** (paridad MIROVA ✓).
  - VIIRS-M 750m → ~1.06 km diagonal (paridad MIROVA ✓).
  - VIIRS-I 375m → ~530 m diagonal (más estricto que MIROVA, OK).
- **No hay límite de tamaño total del cluster**: un cluster puede crecer
  indefinidamente mientras la cadena de pixels detectados sea contigua en grid.

**Llamada desde process_*.py** con `strategy="vent_anchored"` (default en
`mirova_equivalent`) + `inner_radius_km` per-volcán. La estrategia ordena clusters
por proximidad al vent y elige el primero como `primary_cluster`.

### 2.2 `cluster_pixels_geographic()` — helper, NO usado en NRT

- Operación: union-find por haversine, threshold `max_dist_km=1.5` (default).
- Solo se usa en `scripts/add_primary_cluster_vrp.py` (ad-hoc post-procesamiento).
- **No interviene en pipeline NRT** → fuera de scope del bug Caviahue.

### 2.3 Conclusión auditoría connectivity

El threshold de connectivity es paridad razonable con Coppola 2016a (~1 km).
**El bug NO está en cluster_hotspots geométrico.**

---

## 3. Diagnóstico empírico cluster sizes — Tier A

Datos: `data/mirova_equivalent/<Volcano>.json` (snapshot actual main, S77).

| Volcán | inner_km | n_with_pc | within_inner | far(>inner) | %_far | max_n_pix | p10 | p90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 20 | 1242 | 1221 | 21 | 1.7% | **731** | 1 | 46 |
| Villarrica | 5 | 1005 | 655 | 350 | 34.8% | **538** | 1 | 70 |
| Lascar | 5 | 909 | 692 | 217 | 23.9% | 103 | 1 | 69 |
| Copahue | 4 | 988 | 532 | 456 | **46.2%** | 107 | 1 | 56 |
| NevadosDeChillan | 5 | 849 | 548 | 301 | 35.5% | 100 | 1 | 58 |
| Llaima | 5 | 897 | 580 | 317 | 35.3% | 88 | 1 | 68 |
| Chaiten | 5 | 1002 | 777 | 225 | 22.5% | 428 | 1 | 58 |
| PlanchonPeteroa | 3 | 878 | 551 | 327 | 37.2% | **872** | 1 | 59 |
| Lastarria | 3 | 940 | 619 | 321 | 34.1% | 92 | 1 | 49 |
| Isluga | 5 | 762 | 564 | 198 | 26.0% | 107 | 1 | 54 |
| Tupungatito | 7 | 855 | 732 | 123 | 14.4% | 270 | 1 | 78 |

Lecturas:

- **PCC tiene 1.7% far** (inner=20km absorbe casi todo) — `vent_anchored` funciona.
- **Copahue 46%, PlanchonPeteroa 37%, Villarrica 35% far** — un tercio o más de
  records publican primary_cluster fuera del inner. Bandera roja.
- **Clusters extremos**:
  - PCC 731px MODIS @ 1.9km: erupción 2011 real, cluster legítimo.
  - PlanchonPeteroa 872px MODIS @ 3.5km: sospechoso. Posible fósil pre-S73
    (saturation bug) o incendio masivo borde ROI.
  - Villarrica 538px VIIRS-I @ 18km: 75 km² lejos del vent → no es lava lake
    (sub-pixel sub-MW), probable cirrus o incendio forestal.
  - Chaiten 428px MODIS @ 5.9km: domo 2008 + flujos piroclásticos, posible OK.

---

## 4. Caso Copahue / Caviahue (foco del trigger)

**Geometría**: vent en `(-37.856, -71.184)`, lago Caviahue en `(-37.876, -71.029)`,
distancia ~14 km E del vent. Inner_radius = 4 km. Outer_radius = 25 km.

### Distribución de primary_cluster.centroid_dist_km en Copahue (988 records)

| Bucket km | Records | % |
|---|---:|---:|
| 0–4 (inner) | 532 | 53.8% |
| 4–10 | 57 | 5.8% |
| **10–15 (Caviahue band)** | **156** | **15.8%** |
| 15–25 | 166 | 16.8% |
| >25 | 77 | 7.8% |

**131 records (13%) tienen el primary_cluster a <3 km del lago Caviahue.**

### Tamaño de esos clusters lejanos

Los far clusters NO son enormes. La mayoría son **1–2 pixels aislados** a 10–33 km
del vent. Es decir, son hotspots **independientes** del summit (no extensión del
cluster summit a través de connectivity). Top 20 lejanos:

```
dist_km | n_pix | area_km2 | vrp_mw | sensor
34.1    | 2     | 2.0      | 21.53  | MODIS_AQUA
33.5    | 1     | 0.14     | 0.34   | VIIRS_SNPP
33.1    | 2     | 2.0      | 6.42   | MODIS_TERRA
...
```

### El mecanismo real del bug — descubrimiento S78

**`vent_anchored` ya está ON** en mirova_equivalent.yaml. La estrategia ordena clusters
por (inside_inner, dist asc, -vrp desc). PERO hay un parche S43 (líneas 133-138 de
`clustering.py`):

```python
if has_vrp:
    with_vrp = [c for c in clusters if c.get("vrp_mw", 0.0) > 0]
    ranking_set = with_vrp if with_vrp else clusters
```

Cuando los pixels detectados dentro del inner_radius tienen `vrp_mw=0` (clip D4 sobre
pixels con `delta_L ≤ 0`), el ranking_set se reduce a clusters con vrp>0 — que pueden
estar **fuera del inner**. Entonces el cluster a 14 km gana sobre el cluster a 1 km
(que tiene vrp=0).

**Evidencia empírica**: 381 de 456 records far en Copahue (83.5%) tienen
`n_anomalous_pixels > primary_cluster.n_pixels`, lo que indica **había otros clusters
en el granule** (potencialmente más cercanos al vent) pero quedaron descartados por la
regla "vrp>0 prevalece sobre inner".

Este es el bug real S43 introdujo: privilegia VRP físico sobre prioridad summit. Para
volcanes con domo pasivo / lava lake sub-MW (Villarrica, Copahue post-erupción, Lastarria),
el cluster summit frecuentemente tiene vrp=0 por clip → cluster cercano a fuente
geotermal/lago caliente gana.

---

## 5. Per-volcano FP-en-lago / valle pre-evaluación

Sin re-procesar, estimación cualitativa basada en distribución `dist_to_vent`:

| Volcán | Cluster radius (físico) | %FP-lejano sospechoso | Mecanismo dominante | Fix prioridad |
|---|---|---:|---|---|
| Copahue | 8-conn 1km MODIS / 0.5km VIIRS-I | 46% (Caviahue) | S43 vrp>0 override gana cluster lago | **ALTA** |
| Villarrica | 8-conn idem | 35% (lago Villarrica, ríos) | S43 override + sub-pixel lava lake | **ALTA** |
| PlanchonPeteroa | 8-conn idem | 37% (Laguna del Maule borde, glaciares) | S43 override + cluster 872px sospechoso | **ALTA** |
| Llaima | 8-conn idem | 35% (Conguillío, lagunas) | S43 override | MEDIA |
| NdC | 8-conn idem | 35% (laguna en cráter, ríos hot) | S43 override | MEDIA |
| Lastarria | 8-conn idem | 34% (fumaroles laterales legítimos!) | inner=3km estricto, hotspots reales 3-5km posibles | BAJA (no es bug, es ROI estrecho) |
| Isluga | 8-conn idem | 26% (Salar Surire al SE) | S43 override + sal | MEDIA |
| Lascar | 8-conn idem | 24% (Salar Atacama) | S38 D8 fix parcial, S43 reabrió hueco | MEDIA |
| Chaiten | 8-conn idem | 22% (domo extenso post-erupción) | mayoría legítimos | BAJA |
| Tupungatito | 8-conn idem | 14% (mayormente snow/glaciar) | inner=7km ya amplio | BAJA |
| PCC | 8-conn idem | 1.7% | inner=20km absorbe todo | OK |

---

## 6. Propuestas de fix (ranqueadas por costo / beneficio)

### Fix A — Revertir la regla "vrp>0 prevalece sobre inner" (S43) **[recomendado #1]**

`clustering.py` líneas 133-138: eliminar el filtro `with_vrp`. Volver a regla
S38 pura: cluster dentro de inner_radius gana, sin importar si su vrp es 0 o positivo.

Trade-off:
- Pro: cierra el bug Caviahue/Villarrica/PP de raíz. Restaura semántica vent_anchored.
- Contra: vuelven a aparecer los 18 FNs S43 documenta (Tupungatito/Lastarria/PP donde
  cluster cercano vrp=0 por D4 clip). Pero esos pueden ser ya FP-by-design (cluster
  cercano no aporta señal real). Verificar con audit MIROVA reference.

**Costo**: 5 líneas de código + revertir 1 test + reproceso A/B sobre Copahue/Villarrica.

### Fix B — Hard exclusion radius post-cluster

Después de cluster_hotspots(), filtrar primary_cluster con `centroid_dist_km > 2*inner_radius_km`. Si todos los clusters están fuera, NO publicar detección (record sin primary_cluster).

Trade-off:
- Pro: garantiza que ningún record reporte fuente "summit" en realidad estando a 14 km.
- Contra: pierde detecciones legítimas de **fumaroles laterales** (Lastarria 3-5 km
  del vent son fumaroles reales documentados por Aguilera 2021).

**Costo**: 10 líneas + per-volcano cap config.

### Fix C — Cluster size cap absoluto

Después de cluster_hotspots(), descartar clusters con `n_pixels > MAX_CLUSTER_PIXELS`
(p.ej. 100 MODIS, 200 VIIRS-I) como "sospechosos de cirrus/incendio extendido".

Trade-off:
- Pro: cubre el caso PlanchonPeteroa 872px y Villarrica 538px.
- Contra: descarta erupciones reales (PCC 731px, Chaiten 428px erupción 2008-12).

**Costo**: 15 líneas + threshold per-régimen eruptivo. Difícil de calibrar sin perder TPs.

### Fix D — Cluster radius físico estricto (1 km MIROVA literal)

Reemplazar `scipy.ndimage.label` por `cluster_pixels_geographic(max_dist_km=1.0)`. Forzar
distancia métrica haversine ≤ 1 km entre pixels del mismo cluster.

Trade-off:
- Pro: paridad literal Coppola 2016a "neighbor pixels within ~1 km".
- Contra: **no resuelve el bug Caviahue** porque los clusters lejanos YA son separados
  del cluster summit en la representación actual. Cambiar el threshold no los une al
  summit ni los descarta. Es **null fix** para este problema específico.

**Costo**: 30 líneas refactor. **No recomendado** — el problema no es de connectivity.

### Fix E — Per-volcán cluster_radius_km

Agregar `cluster_radius_km` a volcanoes.yaml para volcanes con topografía especial.
Sin valor base que justifique cambio respecto a 8-conn grid actual.

**No recomendado** — solución sin problema.

---

## 7. Recomendación final

1. **Fix A (revertir S43 override) — ALTA PRIORIDAD**. Mecanismo real del bug
   Caviahue/Villarrica/PP. Cierre 5 líneas + tests A/B.
2. **Si Fix A reintroduce FNs S43 documentaba**: investigar por qué el cluster
   summit tiene vrp=0. Probablemente D4 delta_L clip demasiado agresivo en
   summit con background propio caliente. Fix en D4, no en clustering.
3. **PlanchonPeteroa 872px MODIS y Villarrica 538px VIIRS-I**: investigar individual
   timestamps. Probable fósil pre-S73 saturation (PP) y cirrus/incendio (VR).
   No requiere cambio de algoritmo, sino re-proceso post-PR #133 + inspección caso
   a caso.
4. **Cluster connectivity NO requiere cambio**. 8-conn grid es paridad razonable con
   Coppola 2016a §2.2. La hipótesis original del usuario ("clustering generoso se
   extiende al lago") **no se confirma** — clusters lejanos son entidades
   independientes seleccionadas mal por S43 override, no extensiones del cluster
   summit.

---

## 8. Referencias

- Coppola, D. et al. 2016a — Space Science Reviews **426**:5. §2.2 hotspot aggregation.
- `pipeline/clustering.py` (S78 snapshot main `f2f60ac`).
- `pipeline/profiles/mirova_equivalent.yaml` línea 186 (`enable_vent_anchored_clustering: true`).
- Bug S43 documentado: `clustering.py` líneas 122-138 comentario inline.
- Bug S38 D8 documentado: `clustering.py` líneas 116-121 comentario inline.
