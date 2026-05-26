# Villarrica VIIRS 375m — TIF + KMZ + CSV (S33 post-Phase 1 revertido)

Generado por `scripts/generate_villarrica_pruebas.py` desde
`data/mirova_equivalent/Villarrica.json` (Driver A solo, fix S33).

## Pasadas incluidas (8 total)

8 pasadas VIIRS 375m de los días 8 y 19 abril 2026:
- 2026-04-08: NOAA-20, NOAA-21, SNPP, NOAA-20 (4 pasadas)
- 2026-04-19: NOAA-20, NOAA-21, SNPP, NOAA-20 (4 pasadas)

## Por carpeta

Cada subdir `<fecha_hora>_<sensor>/` contiene 3 archivos:

1. **`Villarrica_<sensor>_<datetime>.tif`** — GeoTIFF 134×134 float64
   EPSG:4326. Replica formato MIROVA OUTPUTweb. Valores en MW por pixel
   con `vrp_mw > 0` solamente. Bounds 50×50km centrado en Villarrica vent.

2. **`Villarrica_<sensor>_<datetime>.kmz`** — Google Earth con polígonos
   ~375m × 375m por pixel detectado. Color por nivel MIROVA (Muy Bajo
   gris → Muy Alto carmesí). Solo pixels con `vrp_mw > 0`.

3. **`Villarrica_<sensor>_<datetime>_pixels.csv`** — CSV con TODOS los
   anomaly_pixels del record (incluso `vrp_mw = 0`). Columnas:
   `lat, lon, bt_k, vrp_mw, dist_km`. Útil para inspección detallada
   de pixels que el pipeline marcó pero clip a 0 en VRP.

## Limitación importante

Nuestro pipeline aplica clip `ΔL ≥ 0` per pixel:
```
t1_delta_L = np.maximum(t1_L - test1_L_bg_local, 0.0)
```

Resultado: pixels marginalmente más fríos que L_bg local NO contribuyen
al VRP, aunque hayan sido marcados como anomaly por path NTI/dNTI/Test1.

Por eso muchos pixels en CSV tienen `vrp_mw = 0` (89/91 en algunos casos)
mientras MIROVA reportó VRP positivo (probablemente MIROVA usa una
fórmula diferente, posiblemente Coppola 2015 Eq.1 integrated sin clip
per-pixel — refutado por simulación R2 con `t_bg_global` pero no
verificado con `t_bg_local`).

## Comparación con MIROVA real

Para comparar con MIROVA, descargar manualmente desde
https://www.mirovaweb.it/NRT/volcanoMap.php?volcano=Villarrica&sensor=VIIRS375
con login. Sin login, solo el archivo "Last" más reciente está accesible
públicamente — no los históricos por fecha.

## Nuestros datos

Generados con `mirova_equivalent.yaml` post-S33:
- Driver A: `mirovaEqVrp` con fix S33 (validación pc.centroid_dist_km vs inner_radius).
- Phase 1: OFF (refutado, destruye recall).
- D4: OFF (refutado, efecto despreciable post-fix).
- Resultado: recall global 74.2%, ratio mediano 2.53× (Driver A solo).
