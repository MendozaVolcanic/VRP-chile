# Backlog S32 — schema gap `anomaly_pixels` vs `primary_cluster.vrp_mw`

> Hallazgo lateral durante S32 P2 Driver B análisis. NO urgente. Documentado
> para sesión futura.

## Síntoma observado

`experiments/62_driver_b_pixel_threshold.py` sanity check:
- `pc_vrp` reportado por pipeline (campo `primary_cluster.vrp_mw`).
- vs suma de `anomaly_pixels` cuyos lat/lon están dentro del `cluster_radius_km`
  alrededor del `primary_cluster.centroid_lat/lon`.

**Diff mediano: 60%. Diff max: 100%.**

## Causa raíz identificada

Los 3 procesadores (`process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`)
construyen `anomaly_pixels` desde el **hot_mask global del granule** (top-100 VRP,
cap S26 para evitar bloat JSON):

```python
sorted_indices = np.argsort(-per_pixel_vrp_mw)[:100]
for idx in sorted_indices:
    anomaly_pixels.append({"lat": ..., "lon": ..., "vrp_mw": ...})
```

Pero cuando `final_hotspot_source="test1"`, los campos `vrp_mw` y `primary_cluster`
se RECALCULAN sobre `test1_hot` (la mask Test 1 integrated-ROI de Coppola 2015).
Esa mask es **diferente** del hot_mask global:

- hot_mask global = pixels que pasan threshold pixel-level (BT > t_bg + 5σ summit, etc.).
- test1_hot = pixels en ROI 3km del vent que contribuyen al integrated trigger
  (incluye pixels marginales que individualmente no pasarían pixel-level threshold).

Cuando Test 1 dispara pero pocos pixels pasan también el threshold pixel-level,
los arrays divergen: `anomaly_pixels` puede tener 1-3 pixels y `pc_vrp` reportado
suma 14-49 pixels (el problema Driver B).

## Impacto

- **Frontend visual**: el mapa de pixels (scatter `anomaly_pixels`) no muestra
  los pixels que realmente componen el `pc_vrp` reportado en records Test 1.
- **Análisis pixel-level frontend-side**: imposible reconstruir el cluster
  Test 1 desde el JSON; hay que recomputar desde HDF.
- **Driver B fix S32**: cuando se aplica el filtro N·σ pixel-level a la mask
  Test 1 (commit `0d8f0b5`), el `pc_vrp` del cluster filtrado puede ser MÁS
  parecido a la suma de `anomaly_pixels` cercanos al centroid (porque ambos
  ahora aplican thresholds pixel-level). Habrá que verificar post-A/B.

## Soluciones posibles (futuras)

### Opción A — exportar pixels Test 1 cuando aplique

Cuando `final_hotspot_source="test1"`, reemplazar `anomaly_pixels` con top-100
pixels de `test1_hot` ordenados por per-pixel VRP. Pros: coherencia
`anomaly_pixels` ↔ `pc_vrp`. Contras: cambio en schema usado por frontend
para mapeo, posible regresión visual.

### Opción B — campo nuevo `cluster_pixels`

Agregar `primary_cluster.pixels` como sub-array con lat/lon/vrp_mw de los
pixels que componen el cluster. Mantiene `anomaly_pixels` global como está.
Pros: coherencia, no rompe nada existente. Contras: bloat JSON.

### Opción C — no hacer nada, documentar drift

Aceptar el gap como divergencia de schema — `anomaly_pixels` es para
visualización global del granule, `primary_cluster` es para magnitud
MIROVA-equivalente. No son la misma cosa.

## Recomendación

**Opción C ahora, Opción A futuro si dashboard agrega exploración pixel-level
del cluster**. La métrica que importa al usuario y a MIROVA es `pc_vrp`, no la
suma de `anomaly_pixels`. El gap es un detalle de schema, no afecta operacional.

## Acciones

- Ninguna inmediata.
- Si en S33+ se quiere agregar interactividad "explorar pixels del cluster"
  en el dashboard, considerar Opción A o B.
- Si Driver B A/B valida (ratio mediano cae a ~1×), re-medir el gap — debería
  reducirse porque ambos arrays ahora aplican thresholds pixel-level
  consistentes.
