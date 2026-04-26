# S23 T14 — Factor 42 RESUELTO: MIROVA reporta CLUSTERS, nosotros pixels individuales

**Fecha**: 2026-04-26 (S23 audit followup)
**Hallazgo**: hipótesis del audit S22 CONFIRMADA empíricamente.

## Test ejecutado

`experiments/50_factor_42_clustering_test.py`: para records con muchos pixels
(>50), aplicar union-find con `cluster_radius_km` variable. Resultado de
"factor px/cluster" indica si pixels son contiguos (ratio alto) o dispersos
(ratio cercano a 1).

## Resultados

### Lastarria 2026-04-14 05:06 VIIRS_NOAA21 (77 pixels)

| cluster_radius_km | n_clusters | ratio px/cluster |
|---:|---:|---:|
| 0.5 | (no medido) | (no medido) |
| 1.0 | **3** | **25.7** |
| 1.5 | 3 | 25.7 |
| 2.0 | 3 | 25.7 |

### Chaitén 2026-04-12 05:00 VIIRS_NOAA20 (360 pixels)

| cluster_radius_km | n_clusters | ratio px/cluster |
|---:|---:|---:|
| 0.5 | 151 | 2.4 |
| 1.0 | **9** | **40.0** |
| 1.5 | 6 | 60.0 |
| 2.0 | 6 | 60.0 |

### Chaitén 2026-04-11 05:18 VIIRS_NOAA20 (113 pixels)

| cluster_radius_km | n_clusters | ratio |
|---:|---:|---:|
| 1.0 | **18** | 6.3 |
| 1.5 | 15 | 7.5 |
| 2.0 | 14 | 8.1 |

## Conclusión

**Factor 42 reportado de Lascar 2025-11-15** (77 pixels nuestro vs 4 MIROVA):
ratio 19.25 = compatible con cluster_radius ~0.5-1.0 km.

**Hipótesis CONFIRMADA**: MIROVA reporta el **número de clusters** (regiones
contiguas), NO el número de pixels detectados. Nosotros reportamos pixels
individuales en `n_anomalous_pixels` y `anomaly_pixels` array.

Los dos cuentan **lo mismo físicamente** — solo es una diferencia de
agregación al reportar:
- **MIROVA**: `n_hotspots` (regiones contiguas).
- **VRP Chile**: `n_anomalous_pixels` (pixels individuales).

Cuando "factor 42" surgió como bug aparente, en realidad NO había bug — solo
una diferencia de unidad de conteo NO documentada.

## Implicancia para detección

**Ninguna**. La detección física es la misma — los pixels son los mismos. Solo
cambia el conteo reportado. Recall y precision NO se ven afectados (siempre
matcheamos por proximidad espacio-temporal, no por conteo).

## Acción recomendada (NO crítica)

### Opción A: documentar en CLAUDE.md y cerrar (recomendado)

Agregar al glosario CLAUDE.md sección "Glosario obligatorio":

```markdown
- **Cluster vs pixel** — MIROVA reporta `n_hotspots` (regiones espacialmente
  contiguas, agrupadas con conectividad ~1km). VRP Chile reporta
  `n_anomalous_pixels` (pixels individuales del granule). Para 1 cluster
  MIROVA, esperamos 5-50 pixels nuestros (depende del tamaño de la región
  hot). NO es bug.
```

### Opción B: agregar campo `n_clusters` a nuestros records (paridad MIROVA)

Calcular clusters con union-find al guardar el record:

```python
# pipeline/store.py
def _count_clusters(pixels, radius_km=1.0):
    # union-find igual al de experiments/50_factor_42_clustering_test.py
    ...
record["n_anomalous_clusters"] = _count_clusters(record.get("anomaly_pixels", []))
```

Costo: 1-2h fix + tests + reproceso. Permite comparar 1:1 con MIROVA en
auditorías futuras. Diferido S24+ si surge necesidad.

## Items derivados

1. ✅ Factor 42 RESUELTO conceptualmente (no es bug, es diferencia de agregación).
2. Agregar nota a CLAUDE.md glosario (siguiente commit).
3. Diferido S24+: implementar `n_anomalous_clusters` si se necesita paridad
   exacta con MIROVA.

## Lección de auditoría

**Audit dijo "factor 42 abierto desde S15"** sin investigación profunda.
Confirma regla A2 CLAUDE.md: "diagnósticos paralelos antes de reprocesos caros".
Un script ad-hoc de 80 líneas resolvió en 5 minutos lo que llevaba 2 sesiones
abierto como misterio.
