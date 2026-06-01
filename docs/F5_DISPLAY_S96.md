# F5' display-first — implementación S96

**Sesión S96 (2026-06-01 UTC).** Implementación display-first del toggle de magnitud
**Cluster ⟷ Núcleo F5'** (D2-safe v2) en las 3 vistas frontend (index/diario/mosaico).
Decisión Nicolás S94: F5' es display-first, reversible, **detección NUNCA se toca**.
Calibración base: [F5_CALIBRATION_S95.md](F5_CALIBRATION_S95.md).

## Qué se implementó

- Toggle UI en las 3 vistas (default **Cluster** = comportamiento actual, sin cambio).
- `mirovaEqVrpCore(r, innerKm)` recomputa la magnitud desde `anomaly_pixels` con
  D2-safe v2; el **gating (detección/visibilidad) es idéntico** al de `mirovaEqVrp`.
- Punto único de display por vista: `mirovaEqVrpDisplay`/`eqVrpDisplay` rutea según
  el flag `USE_F5_CORE`. Filtros de artefacto (cirrus/campo difuso) NO usan el núcleo
  (sus umbrales se calibraron contra `pc.vrp_mw`).

## 3 correcciones halladas en preview (por esto se valida en navegador)

La calibración S95 validó D2-safe **solo sobre VIIRS375 matcheado a MIROVA** sobre data
REPROCESADA (`data/_s94_reproc`). Aplicarlo como transform de display ciego sobre la
data LIVE (`data/mirova_equivalent`, todos los sensores/records) expuso 3 fallas:

1. **Solo VIIRS375.** En MODIS (1 km) el ancla "píxel de máxima energía" cae en un
   píxel coarse lejano e infla (PCC MODIS 2026-05-30: peak a 12.8 km → 8→22 MW). Fix:
   el núcleo solo se aplica a VIIRS I-band 375 m (convención A48: `VIIRS_{SNPP,NOAA20,
   NOAA21}` sin sufijo; `_750`=M-band; `MODIS_*`). MODIS/V750 conservan el cluster.

2. **Anclar cerca del cluster summit, no del máximo global.** Aun en VIIRS375, el máximo
   global de la escena puede ser una fuente AJENA (incendio a 19 km — caso PP). Fix:
   los candidatos del núcleo se restringen a `anomaly_pixels` dentro de `inner_radius`
   del **centroide del primary_cluster** (que el gating ya validó como summit). Distancia
   desde lat/lon, NO `dist_km` (Eje3/A48: su ancla es el centro del volcán, no el cluster).

3. **Guard de schema A46/A07.** `anomaly_pixels` a veces NO contiene los píxeles del
   `primary_cluster` (caso PP 2026-05-30: cluster 19 px @summit, pero `anomaly_pixels`
   = 3 px, todos lejos). Si no hay ningún `anomaly_pixel` dentro de `inner` del centroide,
   **no se recomputa** (fallback a `pc.vrp_mw`). Evita anclar a fuentes ajenas y sub-contar.

## Validación (preview real, navegador, data live)

- **Seguridad — 0 inflación**: máximo 48h por Tier A en modo Núcleo nunca supera el de
  modo Cluster (ratio ≤ 1.0 en los 11).
- **Eficacia (90 d, solo VIIRS375)** — efecto mediano `Σcore/Σcluster`:
  NdC 0.22× · Lastarria 0.26× · Isluga 0.33× · Copahue 0.36× · Llaima 0.42× ·
  Chaitén 0.55× · PP 0.57× · Villarrica 0.61× · Tupungatito 0.74× · PCC 0.79× ·
  **Láscar 0.93×** (cráter caliente, casi sin cambio — correcto).
- **Villarrica 48h**: 3.26→0.17 MW (el 0.17 coincide con la magnitud real del lava lake
  que MIROVA ve ~0.1–0.2 MW; el 3.26 era el halo glaciar inflado).
- 0 errores de consola en las 3 vistas.

## Limitación honesta (data dependency)

El efecto pleno requiere que `anomaly_pixels` cubra el cluster summit. En la data live
muchos records recientes tienen `anomaly_pixels` incompleto (asimetría A46/A07) → caen
al fallback (cluster). Por eso el **máximo** 48h de varios vols no cambia aunque el
**grueso** de records VIIRS375 sí reduce (nReduced alto). El cure completo de la
calibración se vio sobre data reprocesada con `anomaly_pixels` completo.

## Validación contra MIROVA + guard de seguridad (S96, pedido Nicolás)

`experiments/_s96_audit/f5_display_vs_mirova.py` cruza, record por record, **Cluster vs
Núcleo vs MIROVA** (ground truth CONS+OCR, VIIRS375 matcheado ±60 min) sobre data live.
Resultado (1653 records matcheados):

| | Cluster | Núcleo F5' (con guard) |
|---|---|---|
| Mediana ratio vs MIROVA (donde Núcleo>0) | 2.00× | **1.59×** (más cerca de 1.0) |
| Tupungatito | 11.19× | **5.66×** |
| Lastarria | 3.60× | **1.65×** |
| Isluga | 1.24× | **1.00×** |
| Láscar (cráter caliente) | 0.92× | 0.95× (sin cambio) |
| **Regresiones (Cluster>0 → Núcleo 0)** | — | **0** |

**El Núcleo aproxima mejor a MIROVA** (gana en 8/11 vols, mediana global 1.59 vs 2.00).

### Guard de seguridad (el "→0" que vio Nicolás)
Sin guard, **73/1653 records (4.4%) confirmados por MIROVA caían de un valor positivo en
Cluster a 0 en Núcleo** (concentrados en PP 42, Tupungatito 10, Isluga 9, Villarrica 6).
Causa: asimetría A46/A07 — `anomaly_pixels` cerca del cráter no cargan la energía del
cluster (el cluster agrega VRP real pero los píxeles guardados dan ~0) → el Núcleo
recompone ~0. **En monitoreo, borrar una detección real es el peor error.**

**Fix (1 línea por vista)**: `if (core <= 0 && base > 0) return base` — el Núcleo NUNCA
borra una detección del Cluster; solo REDUCE el halo glaciar donde tiene datos. Con el
guard: **0 regresiones**, Núcleo "mejor o igual, nunca peor". Distingue reducción
genuina (Tupungatito 6.35→0.35, anomaly_pixels con energía) de regresión (Villarrica
6.149→6.149 fallback, anomaly_pixels vacíos).

## Pendiente antes de bajar a pipeline (NO hecho — requiere decisión Nicolás)

El guard hace el display **seguro** pero NO cura la raíz: el beneficio pleno requiere
que `anomaly_pixels` cargue la energía del cluster. Para adoptar F5' en `process_viirs.py`
(segundo umbral de magnitud, detección intacta), con A45 completo:
1. **Raíz A46/A07**: que el pipeline persista en `anomaly_pixels` los píxeles reales del
   cluster con su VRP (completar lo que #297/#294 empezó). Sin esto, ~30% de records
   VIIRS375 caen al fallback y F5' no aporta. Es el bloqueante real.
2. Re-validar D2-safe v2 con el **anclaje centroide-restringido** (el script S95 usa
   ancla global) — confirmar que no degrada los ratios validados.
3. R2 pixel-level vs TIF MIROVA.
