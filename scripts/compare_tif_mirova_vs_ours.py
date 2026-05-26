"""S33+ — Comparación pixel-by-pixel TIF MIROVA "Last" vs nuestro TIF
para la misma pasada satelital. Aplica R2 verdadero (verificación contra
datos MIROVA reales).

Args via constants:
  - VOLCANO: nombre Tier A (Lascar, PuyehueCordonCaulle, ...)
  - DATETIME_TARGET: '2026-05-08 06:30' aprox — pasada satelital del MIROVA "Last"
  - SENSOR: 'VIIRS_NOAA20', 'VIIRS_SNPP', 'VIIRS_NOAA21' (o auto-detect)

Output:
  - Stats: pixels comunes, pixel-by-pixel correlación, diferencia VRP suma.
  - Plots: nuestro TIF vs MIROVA TIF lado a lado (matplotlib).
  - Diff map: |nuestro - mirova| por pixel.
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path("C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
PRUEBAS = ROOT / "Pruebas"

# Config — modificable
VOLCANO = 'Lascar'
DATETIME_TARGET = '2026-05-05 06:06'  # cerca de MIROVA Last 2026-05-08 06:30
SENSOR_FILTER = 'VIIRS_NOAA20'  # mismo satélite que probablemente bajó MIROVA

MIROVA_TIF = PRUEBAS / "mirova_real" / f"{VOLCANO}_VIIRS375_I04.tif"


def find_our_record(volcano, target_dt_str, sensor_filter=None):
    """Busca el record nuestro VIIRS 375m más cercano al timestamp target."""
    target_dt = datetime.fromisoformat(target_dt_str.replace(' ', 'T'))
    recs = json.loads((ROOT / "data" / "mirova_equivalent" / f"{volcano}.json").read_text())['records']
    candidates = []
    for r in recs:
        s = r.get('sensor', '')
        if not s.startswith('VIIRS_') or s.endswith('_750'):
            continue
        if sensor_filter and s != sensor_filter:
            continue
        try:
            dt = datetime.strptime(r['datetime_utc'][:16], '%Y-%m-%d %H:%M')
        except (ValueError, KeyError):
            continue
        delta = abs((dt - target_dt).total_seconds())
        if delta <= 3600:  # 1h tolerance
            candidates.append((delta, r))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def load_our_tif(record, volcano):
    """Genera nuestro TIF para el record (replica lógica generate_villarrica_pruebas).
    Bounds del MIROVA TIF como referencia (mismo bbox)."""
    with rasterio.open(MIROVA_TIF) as ref:
        bounds = ref.bounds
        transform = ref.transform
        h, w = ref.shape
        crs = ref.crs

    grid = np.zeros((h, w), dtype=np.float64)
    aps = record.get('anomaly_pixels') or []
    pixel_sz_lon = (bounds.right - bounds.left) / w
    pixel_sz_lat = (bounds.top - bounds.bottom) / h
    n_in_bounds = 0
    n_pos = 0
    for p in aps:
        lat, lon = p.get('lat'), p.get('lon')
        v = p.get('vrp_mw') or 0
        if lat is None or lon is None:
            continue
        if not (bounds.left <= lon <= bounds.right) or not (bounds.bottom <= lat <= bounds.top):
            continue
        n_in_bounds += 1
        if v <= 0:
            continue
        col = int((lon - bounds.left) / pixel_sz_lon)
        row = int((bounds.top - lat) / pixel_sz_lat)
        col = max(0, min(w - 1, col))
        row = max(0, min(h - 1, row))
        if v > grid[row, col]:
            grid[row, col] = v
        n_pos += 1
    return grid, bounds, transform, crs, n_in_bounds, n_pos


def main():
    print(f"# Comparación TIF MIROVA \"Last\" vs nuestro — {VOLCANO}\n")
    if not MIROVA_TIF.exists():
        print(f"❌ MIROVA TIF no encontrado: {MIROVA_TIF}")
        return

    # MIROVA TIF
    with rasterio.open(MIROVA_TIF) as r:
        mirova_data = r.read(1).astype(np.float64)
        mirova_bounds = r.bounds
    mirova_pos = mirova_data[mirova_data > 0]
    print(f"## MIROVA TIF ({MIROVA_TIF.name})")
    print(f"  shape: {mirova_data.shape}, bounds: {mirova_bounds}")
    print(f"  pixels >0: {len(mirova_pos)}, sum={mirova_pos.sum():.4f}, max={mirova_pos.max():.4f}")
    print(f"  values: min={mirova_pos.min():.5f}, mean={mirova_pos.mean():.5f}, median={np.median(mirova_pos):.5f}\n")

    # Nuestro record
    rec = find_our_record(VOLCANO, DATETIME_TARGET, SENSOR_FILTER)
    if rec is None:
        print(f"❌ No record nuestro para {VOLCANO} VIIRS 375m cerca de {DATETIME_TARGET}")
        return
    print(f"## Nuestro record (closest match)")
    print(f"  datetime_utc: {rec['datetime_utc']}, sensor: {rec['sensor']}")
    pc = rec.get('primary_cluster') or {}
    print(f"  pc_vrp: {pc.get('vrp_mw',0):.3f} MW, pc_dist: {pc.get('centroid_dist_km','?')} km")
    print(f"  triggered_test1: {rec.get('triggered_test1')}, n_test1_pixels: {rec.get('n_test1_pixels',0)}")
    aps = rec.get('anomaly_pixels') or []
    pos = sum(1 for p in aps if (p.get('vrp_mw') or 0) > 0)
    print(f"  anomaly_pixels: {len(aps)}, con vrp>0: {pos}\n")

    # Nuestro TIF (mismo bbox MIROVA)
    our_data, _, _, _, n_in_bounds, n_pos_plotted = load_our_tif(rec, VOLCANO)
    our_pos = our_data[our_data > 0]
    print(f"## Nuestro TIF (mismo bbox MIROVA)")
    print(f"  pixels en bbox: {n_in_bounds}, ploteados (vrp>0): {n_pos_plotted}")
    max_str = f"{our_pos.max():.4f}" if len(our_pos) else "0"
    print(f"  pixels >0 en grid: {len(our_pos)}, sum={our_pos.sum():.4f}, max={max_str}")

    # Diff map
    diff = our_data - mirova_data
    print(f"\n## Diff map (nuestro - MIROVA)")
    print(f"  |diff| pixels >0: {(np.abs(diff) > 0).sum()}")
    print(f"  diff sum: {diff.sum():+.4f} MW")
    print(f"  diff range: {diff.min():+.4f} to {diff.max():+.4f}")

    # Coincidencias pixel-by-pixel
    common = (mirova_data > 0) & (our_data > 0)
    only_mirova = (mirova_data > 0) & (our_data == 0)
    only_ours = (mirova_data == 0) & (our_data > 0)
    print(f"\n## Pixel-by-pixel concordancia")
    print(f"  Pixels donde AMBOS detectan: {common.sum()}")
    print(f"  Solo MIROVA: {only_mirova.sum()}")
    print(f"  Solo nuestro: {only_ours.sum()}")
    if common.sum() > 0:
        # Correlación en pixels comunes
        m_c = mirova_data[common]
        o_c = our_data[common]
        if len(m_c) > 1:
            corr = np.corrcoef(m_c, o_c)[0, 1]
            print(f"  Correlación VRP en pixels comunes: {corr:.3f}")
            print(f"  Ratio promedio (nuestro/MIROVA) en pixels comunes: {(o_c/m_c).mean():.2f}")

    # Save diff map TIF
    out_diff = PRUEBAS / "mirova_real" / f"{VOLCANO}_diff_our_minus_mirova.tif"
    with rasterio.open(MIROVA_TIF) as ref:
        with rasterio.open(out_diff, 'w', driver='GTiff', width=ref.width, height=ref.height,
                           count=1, dtype='float64', crs=ref.crs, transform=ref.transform,
                           compress='PackBits') as dst:
            dst.write(diff, 1)
    print(f"\nDiff map guardado: {out_diff.relative_to(ROOT)}")

    # Save our TIF for visual comparison
    out_ours = PRUEBAS / "mirova_real" / f"{VOLCANO}_VIIRS375_OURS.tif"
    with rasterio.open(MIROVA_TIF) as ref:
        with rasterio.open(out_ours, 'w', driver='GTiff', width=ref.width, height=ref.height,
                           count=1, dtype='float64', crs=ref.crs, transform=ref.transform,
                           compress='PackBits') as dst:
            dst.write(our_data, 1)
    print(f"Nuestro TIF guardado: {out_ours.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
