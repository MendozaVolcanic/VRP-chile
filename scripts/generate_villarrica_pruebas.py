"""Generate TIF + KMZ equivalents for Villarrica VIIRS375 records,
2026-04-08 + 2026-04-19 (todas las pasadas).

Usa los anomaly_pixels ya procesados en data/mirova_equivalent/Villarrica.json
(Driver A solo, Phase 1 OFF, métrica corregida S33). NO descarga granules
nuevos — usa lo que el pipeline ya generó.

Output replica formato MIROVA OUTPUTweb:
- TIF: 134×134 float64, EPSG:4326, bounds ~50×50km centrado en Villarrica vent.
- KMZ: KML con polígonos 375m colorados por VRP nivel MIROVA + Style.

Salida: Pruebas/output/<fecha>_<sensor>/
"""
from __future__ import annotations
import json, sys, io, os
from pathlib import Path
import zipfile
from datetime import datetime
import numpy as np
import rasterio
from rasterio.transform import from_bounds

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
DATA = ROOT / "data" / "mirova_equivalent" / "Villarrica.json"
OUTDIR = ROOT / "Pruebas" / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)

# Villarrica vent (volcanoes.yaml) y geometría TIF (replica MIROVA)
VENT_LAT = -39.420
VENT_LON = -71.930
# Bounds replicando ejemplo MIROVA: 134×134 con span 0.598°lon × 0.463°lat
BOUNDS = {
    'left': -72.23041592110762,
    'right': -71.63293289514706,
    'top': -39.18854390415147,
    'bottom': -39.651949079806535,
}
GRID_W, GRID_H = 134, 134
TRANSFORM = from_bounds(BOUNDS['left'], BOUNDS['bottom'],
                         BOUNDS['right'], BOUNDS['top'], GRID_W, GRID_H)
PIXEL_SIZE_LAT = (BOUNDS['top'] - BOUNDS['bottom']) / GRID_H
PIXEL_SIZE_LON = (BOUNDS['right'] - BOUNDS['left']) / GRID_W

# Niveles MIROVA (legend dashboard) — colores RGB
LEVELS = [
    (0.05, "Muy Bajo",   (128, 128, 128)),  # gris
    (1.0,  "Bajo",       (34, 139, 34)),    # forest green
    (10.0, "Moderado",   (255, 215, 0)),    # gold
    (100.0,"Alto",       (255, 140, 0)),    # dark orange
    (1e9,  "Muy Alto",   (220, 20, 60)),    # crimson
]


def vrp_to_kml_color(vrp_mw):
    """Returns ABGR hex (KML uses aabbggrr) for the VRP level."""
    for thr, label, (r, g, b) in LEVELS:
        if vrp_mw < thr:
            return f"cc{b:02x}{g:02x}{r:02x}", label  # alpha=cc, then bgr
    thr, label, (r, g, b) = LEVELS[-1]
    return f"cc{b:02x}{g:02x}{r:02x}", label


def lat_lon_to_grid(lat, lon):
    """Grid index (col, row) en el raster 134×134."""
    if not (BOUNDS['left'] <= lon <= BOUNDS['right']):
        return None, None
    if not (BOUNDS['bottom'] <= lat <= BOUNDS['top']):
        return None, None
    col = int((lon - BOUNDS['left']) / PIXEL_SIZE_LON)
    row = int((BOUNDS['top'] - lat) / PIXEL_SIZE_LAT)
    col = max(0, min(GRID_W - 1, col))
    row = max(0, min(GRID_H - 1, row))
    return col, row


def write_tif(path, anomaly_pixels):
    """Genera GeoTIFF 134x134 float64 con valores VRP (MW)."""
    grid = np.zeros((GRID_H, GRID_W), dtype=np.float64)
    n_plotted = 0
    for p in anomaly_pixels:
        lat, lon = p.get('lat'), p.get('lon')
        v = p.get('vrp_mw') or 0
        if lat is None or lon is None or v <= 0:
            continue
        col, row = lat_lon_to_grid(lat, lon)
        if col is None:
            continue
        if v > grid[row, col]:
            grid[row, col] = v
        n_plotted += 1
    profile = {
        'driver': 'GTiff',
        'width': GRID_W,
        'height': GRID_H,
        'count': 1,
        'dtype': 'float64',
        'crs': 'EPSG:4326',
        'transform': TRANSFORM,
        'compress': 'PackBits',
    }
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(grid, 1)
    return n_plotted, float(grid.max())


def write_kmz(path, anomaly_pixels, record_meta):
    """Genera KMZ (zip de KML) con polígonos ~375m por pixel anomalous."""
    sensor = record_meta['sensor']
    dt_utc = record_meta['datetime_utc']
    fecha_label = dt_utc.replace(' ', 'T') + 'Z'

    kml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        f'<name>VRP-Chile · {sensor} · {dt_utc}</name>',
        f'<description>Driver A solo (Phase 1 OFF, fix S33). Detection pixels VRP MW. Vent Villarrica -39.42, -71.93.</description>',
    ]
    for thr, label, (r, g, b) in LEVELS:
        kml_lines.append(f'<Style id="lvl_{label}">')
        kml_lines.append('<LineStyle><color>ff000000</color><width>1</width></LineStyle>')
        kml_lines.append(f'<PolyStyle><color>cc{b:02x}{g:02x}{r:02x}</color><fill>1</fill><outline>1</outline></PolyStyle>')
        kml_lines.append('</Style>')

    n_plotted = 0
    for p in anomaly_pixels:
        lat, lon = p.get('lat'), p.get('lon')
        v = p.get('vrp_mw') or 0
        bt = p.get('bt_k') or 0
        if lat is None or lon is None or v <= 0:
            continue
        # Get level
        for thr, label, _ in LEVELS:
            if v < thr:
                level_label = label
                break
        else:
            level_label = LEVELS[-1][1]
        # Polygon ~375m x 375m around pixel
        dlat = PIXEL_SIZE_LAT / 2
        dlon = PIXEL_SIZE_LON / 2
        coords = [
            (lon - dlon, lat - dlat),
            (lon + dlon, lat - dlat),
            (lon + dlon, lat + dlat),
            (lon - dlon, lat + dlat),
            (lon - dlon, lat - dlat),
        ]
        coord_str = ' '.join(f'{c[0]:.6f},{c[1]:.6f},0' for c in coords)
        kml_lines.append('<Placemark>')
        kml_lines.append(f'<name>{level_label} - {v:.3f} MW</name>')
        kml_lines.append(f'<description><![CDATA[VRP: {v:.4f} MW<br/>BT: {bt:.2f} K<br/>Sensor: {sensor}<br/>Datetime: {dt_utc} UTC]]></description>')
        kml_lines.append(f'<styleUrl>#lvl_{level_label}</styleUrl>')
        kml_lines.append('<Polygon><outerBoundaryIs><LinearRing>')
        kml_lines.append(f'<coordinates>{coord_str}</coordinates>')
        kml_lines.append('</LinearRing></outerBoundaryIs></Polygon>')
        kml_lines.append('</Placemark>')
        n_plotted += 1
    kml_lines.append('</Document>')
    kml_lines.append('</kml>')
    kml = '\n'.join(kml_lines)

    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml)
    return n_plotted


# Cargar records target
records = json.loads(DATA.read_text(encoding='utf-8'))['records']
target = []
for r in records:
    dt = r.get('datetime_utc', '')
    if not (dt.startswith('2026-04-08') or dt.startswith('2026-04-19')):
        continue
    sensor = r.get('sensor', '')
    if not sensor.startswith('VIIRS_') or sensor.endswith('_750'):
        continue
    target.append(r)

print(f"# Generación TIF + KMZ Villarrica VIIRS 375m\n")
print(f"Records target: {len(target)}\n")
print(f"Output dir: {OUTDIR}\n")

# Procesar cada pasada
results = []
for r in target:
    dt = r['datetime_utc']
    sensor = r['sensor']
    aps = r.get('anomaly_pixels') or []
    # Carpeta por pasada: 2026-04-08_05-54_VIIRS_SNPP
    safe_dt = dt.replace(' ', '_').replace(':', '-')
    folder = OUTDIR / f"{safe_dt}_{sensor}"
    folder.mkdir(parents=True, exist_ok=True)
    tif_path = folder / f"Villarrica_{sensor}_{safe_dt}.tif"
    kmz_path = folder / f"Villarrica_{sensor}_{safe_dt}.kmz"
    n_tif, max_vrp = write_tif(tif_path, aps)
    n_kmz = write_kmz(kmz_path, aps, r)
    # CSV con TODOS los anomaly_pixels (incluso vrp=0 por clip per-pixel)
    csv_path = folder / f"Villarrica_{sensor}_{safe_dt}_pixels.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("lat,lon,bt_k,vrp_mw,dist_km\n")
        for p in aps:
            f.write(f"{p.get('lat','')},{p.get('lon','')},"
                    f"{p.get('bt_k','')},{p.get('vrp_mw','')},"
                    f"{p.get('dist_km','')}\n")
    pc = r.get('primary_cluster') or {}
    print(f"  {dt:20} {sensor:18}")
    print(f"    Records anomaly_pixels: {len(aps)}")
    print(f"    pc_vrp reportado: {pc.get('vrp_mw', 0):.3f} MW")
    print(f"    pc_dist: {pc.get('centroid_dist_km', '?')} km, dist_class: {r.get('distance_class','?')}")
    print(f"    triggered_test1: {r.get('triggered_test1', False)}")
    print(f"    TIF pixels plotted: {n_tif}, max value: {max_vrp:.4f} MW")
    print(f"    KMZ polygons: {n_kmz}")
    print(f"    → {folder.relative_to(ROOT)}/")
    results.append({
        'dt': dt, 'sensor': sensor, 'tif': str(tif_path), 'kmz': str(kmz_path),
        'n_pixels': len(aps), 'max_vrp': max_vrp, 'pc_vrp': pc.get('vrp_mw', 0),
    })

print(f"\n## Resumen final\n")
print(f"Generadas {len(results)} pasadas (TIF + KMZ cada una).")
print(f"Ubicación: {OUTDIR}/<fecha_hora>_<sensor>/")
print(f"\nFormato output replica MIROVA OUTPUTweb:")
print(f"  - TIF: {GRID_H}x{GRID_W} float64 EPSG:4326 ({BOUNDS['left']:.4f}..{BOUNDS['right']:.4f} lon)")
print(f"  - KMZ: KML con polígonos {PIXEL_SIZE_LAT*111:.0f}m x {PIXEL_SIZE_LON*111*np.cos(np.radians(VENT_LAT)):.0f}m por pixel.")
print(f"\nNota: estos son nuestros datos (Driver A solo, Phase 1 OFF, fix S33),")
print(f"NO los datos MIROVA originales. Para comparar con MIROVA, descargar")
print(f"manualmente desde el portal con login.")

# README
readme = OUTDIR / "README.md"
with open(readme, 'w', encoding='utf-8') as f:
    f.write(f"""# Villarrica VIIRS 375m — TIF + KMZ + CSV (S33 post-Phase 1 revertido)

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
""")
print(f"\nREADME: {readme.relative_to(ROOT)}")
