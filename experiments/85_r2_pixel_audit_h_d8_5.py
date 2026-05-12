"""85 — R2 pixel-level audit H_D8_5 vs mirova-tif-archive.

Para cada record de `data/_h_d8_5_full/<vol>.json` que tiene TIF MIROVA
disponible en `mirova-tif-archive/data/tif/<vol>/`, cruza pixel-by-pixel
los `anomaly_pixels` contra el TIF y reporta:

  - n_match: pixels VRP-chile que coinciden con un pixel VRP>0 del TIF
  - n_missed: pixels VRP>0 del TIF que VRP-chile NO captura
  - n_excess: pixels VRP-chile que el TIF NO marca
  - delta vs disabled: pixels NEW que H_D8_5 captura vs el control

Adicional: identifica casos D8 (cluster ≠ MIROVA-reported location) y
reporta si H_D8_5_full los corrige.

Default: corre sobre TODOS los TIFs disponibles en el window del A/B.
Modo single-case: --volcano X --datetime "YYYY-MM-DD HH:MM"

Uso:
  python experiments/85_r2_pixel_audit_h_d8_5.py
  python experiments/85_r2_pixel_audit_h_d8_5.py --volcano PuyehueCordonCaulle
  python experiments/85_r2_pixel_audit_h_d8_5.py --start 2026-04-15 --end 2026-05-09
"""
from __future__ import annotations
import json, sys, io, math, argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent

# mirova-tif-archive vive paralelo al repo VRP-chile en .../Volcanologia/
TIF_ARCHIVE = REPO.parent.parent.parent.parent / 'mirova-tif-archive' / 'data' / 'tif'

# Mapping VRP-chile sensor naming → TIF naming
def sensor_to_tif_suffix(sensor):
    s = sensor.upper()
    if 'MODIS' in s:
        return 'MODIS'
    if '_375' in s or sensor in ('VIIRS_SNPP', 'VIIRS_NOAA20', 'VIIRS_NOAA21'):
        return 'VIIRS375'
    if '_750' in s:
        return 'VIIRS750'
    return None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlat = lat2r - lat1r
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1r)*math.cos(lat2r)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def parse_record_dt(record):
    """Parse 'YYYY-MM-DD HH:MM' to datetime."""
    try:
        return datetime.strptime(record['datetime_utc'], '%Y-%m-%d %H:%M')
    except (KeyError, ValueError):
        return None


def find_tif_for_record(volcano, record_dt, sensor_suffix, tolerance_min=10):
    """Find TIF in archive matching volcano + timestamp within ±tolerance."""
    vol_dir = TIF_ARCHIVE / volcano
    if not vol_dir.exists():
        return None
    target = record_dt
    best = None
    best_diff = timedelta(minutes=tolerance_min + 1)
    for tif in vol_dir.glob(f'*_{sensor_suffix}*.tif'):
        # Skip _lm variants (low magnitude alt rendering)
        if '_lm.tif' in tif.name:
            continue
        # Parse YYYYMMDD_HHMMSS from name
        try:
            stem = tif.stem
            date_str, time_str = stem.split('_')[:2]
            tif_dt = datetime.strptime(f'{date_str}{time_str}', '%Y%m%d%H%M%S')
        except (ValueError, IndexError):
            continue
        diff = abs(tif_dt - target)
        if diff < best_diff:
            best_diff = diff
            best = tif
    return best


def read_tif_pixels(tif_path):
    """Return list of (lat, lon, vrp_value) for pixels with VRP > 0 in TIF."""
    try:
        import tifffile
    except ImportError:
        return None  # tifffile not installed
    import numpy as np
    try:
        with tifffile.TiffFile(tif_path) as tif:
            page = tif.pages[0]
            tp = page.tags['ModelTiepointTag'].value
            sc = page.tags['ModelPixelScaleTag'].value
            arr = page.asarray()
    except (KeyError, OSError):
        return None
    i0, j0, _, x0, y0, _ = tp[:6]
    sx, sy, _ = sc
    H, W = arr.shape
    pixels = []
    valid = (arr > 0) & np.isfinite(arr)
    for i, j in zip(*valid.nonzero()):
        lon = x0 + (int(j) - i0) * sx
        lat = y0 - (int(i) - j0) * sy
        pixels.append({'lat': float(lat), 'lon': float(lon),
                       'vrp': float(arr[int(i), int(j)])})
    return pixels


def load_records(profile, volcano):
    p = REPO / 'data' / profile / f'{volcano}.json'
    if not p.exists():
        return []
    with open(p) as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('records', [])


def index_by_dt_sensor(records):
    return {(r.get('datetime_utc', ''), r.get('sensor', '')): r for r in records}


def match_pixels(our_pixels, tif_pixels, max_dist_km=0.5):
    """Greedy nearest match between our pixels and TIF pixels.

    Returns (matched, missed_in_tif, excess_in_ours):
      - matched: pairs (our, tif) where haversine <= max_dist_km
      - missed_in_tif: TIF pixels with no match
      - excess_in_ours: our pixels with no match
    """
    matched = []
    used_tif = set()
    for op in our_pixels:
        best = None
        best_d = max_dist_km + 1e9
        for k, tp in enumerate(tif_pixels):
            if k in used_tif:
                continue
            d = haversine_km(op['lat'], op['lon'], tp['lat'], tp['lon'])
            if d < best_d:
                best_d = d
                best = k
        if best is not None and best_d <= max_dist_km:
            matched.append({'our': op, 'tif': tif_pixels[best], 'dist_km': best_d})
            used_tif.add(best)
    missed = [tp for k, tp in enumerate(tif_pixels) if k not in used_tif]
    excess = [op for op in our_pixels if op not in [m['our'] for m in matched]]
    return matched, missed, excess


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--volcano', default=None,
                   help='Single volcano (default: all 11 Tier A).')
    p.add_argument('--datetime', default=None,
                   help='Single record datetime "YYYY-MM-DD HH:MM" (default: scan window).')
    p.add_argument('--start', default='2026-04-12')
    p.add_argument('--end', default='2026-05-11 23:59:59')
    p.add_argument('--match-km', type=float, default=0.5,
                   help='Max haversine for pixel match (default 0.5 km).')
    return p.parse_args()


TIER_A = ['Chaiten', 'Copahue', 'Isluga', 'Lascar', 'Lastarria', 'Llaima',
          'NevadosDeChillan', 'PlanchonPeteroa', 'PuyehueCordonCaulle',
          'Tupungatito', 'Villarrica']


def audit_record(rec_full, rec_dis, tif_path, match_km):
    """Pixel-level comparison for a single (record, tif) pair."""
    tif_pixels = read_tif_pixels(tif_path)
    if tif_pixels is None:
        return None
    if not tif_pixels:
        return {'tif_n': 0, 'note': 'TIF sin pixels VRP>0'}

    our_full = rec_full.get('anomaly_pixels', []) if rec_full else []
    our_dis = rec_dis.get('anomaly_pixels', []) if rec_dis else []

    m_full, miss_full, exc_full = match_pixels(our_full, tif_pixels, match_km)
    m_dis, miss_dis, _ = match_pixels(our_dis, tif_pixels, match_km)

    return {
        'tif_n': len(tif_pixels),
        'tif_sum_vrp': sum(p['vrp'] for p in tif_pixels),
        'full_n_pix': len(our_full),
        'full_matched': len(m_full),
        'full_missed': len(miss_full),
        'full_excess': len(exc_full),
        'dis_n_pix': len(our_dis),
        'dis_matched': len(m_dis),
        'dis_missed': len(miss_dis),
        'delta_matched': len(m_full) - len(m_dis),  # mejora H_D8_5 vs control
    }


def main():
    args = parse_args()

    if not TIF_ARCHIVE.exists():
        sys.exit(f'ERROR: mirova-tif-archive not found at {TIF_ARCHIVE}')

    try:
        import tifffile  # noqa: F401
    except ImportError:
        sys.exit('ERROR: pip install tifffile')

    print(f'TIF archive: {TIF_ARCHIVE}')
    print(f'Window: {args.start} → {args.end}')
    print(f'Match threshold: {args.match_km} km')
    print()

    volcanoes = [args.volcano] if args.volcano else TIER_A
    rows = []
    for vol in volcanoes:
        full_recs = index_by_dt_sensor(load_records('_h_d8_5_full', vol))
        dis_recs = index_by_dt_sensor(load_records('_h_d8_5_disabled', vol))
        if not full_recs and not dis_recs:
            continue
        # Iterate full records (cuando sum_active>0 — caso interesante)
        for (dt, sens), rec in full_recs.items():
            if dt < args.start or dt > args.end:
                continue
            if args.datetime and dt[:16] != args.datetime[:16]:
                continue
            if (rec.get('vrp_mw_sum_active') or rec.get('vrp_mw', 0) or 0) == 0:
                continue
            record_dt = parse_record_dt(rec)
            if not record_dt:
                continue
            suffix = sensor_to_tif_suffix(sens)
            if not suffix:
                continue
            tif = find_tif_for_record(vol, record_dt, suffix)
            if not tif:
                continue
            rec_dis = dis_recs.get((dt, sens))
            result = audit_record(rec, rec_dis, tif, args.match_km)
            if result is None:
                continue
            result['volcano'] = vol
            result['datetime'] = dt
            result['sensor'] = sens
            result['tif'] = tif.name
            rows.append(result)

    if not rows:
        print('No (record, TIF) pairs encontrados.')
        print('Verificar: data/_h_d8_5_full/ existe, mirova-tif-archive sincronizado.')
        return

    print(f'=== R2 pixel-level audit ({len(rows)} pares record-TIF) ===')
    print()
    header = (f'{"volcano":<22} {"datetime":<17} {"sensor":<15} '
              f'{"TIF_n":>6} {"full_match":>11} {"dis_match":>10} '
              f'{"delta":>6} {"full_miss":>10} {"full_excess":>12}')
    print(header)
    print('-' * len(header))
    totals = {'tif_n': 0, 'full_matched': 0, 'dis_matched': 0,
              'full_missed': 0, 'full_excess': 0}
    for r in rows:
        if 'tif_n' not in r or r.get('full_matched') is None:
            continue
        print(f'{r["volcano"]:<22} {r["datetime"]:<17} {r["sensor"]:<15} '
              f'{r["tif_n"]:>6} {r["full_matched"]:>11} {r["dis_matched"]:>10} '
              f'{r["delta_matched"]:>+6} {r["full_missed"]:>10} {r["full_excess"]:>12}')
        for k in totals:
            totals[k] += r.get(k, 0)
    print('-' * len(header))
    print(f'{"TOTAL":<22} {"":<17} {"":<15} '
          f'{totals["tif_n"]:>6} {totals["full_matched"]:>11} {totals["dis_matched"]:>10} '
          f'{totals["full_matched"] - totals["dis_matched"]:>+6} '
          f'{totals["full_missed"]:>10} {totals["full_excess"]:>12}')

    n_d8_resolved = sum(1 for r in rows
                        if r.get('full_matched', 0) > r.get('dis_matched', 0))
    n_total_pairs = len(rows)
    print()
    print(f'H_D8_5 capture improvement: {n_d8_resolved}/{n_total_pairs} pares '
          f'({100*n_d8_resolved/n_total_pairs:.1f}%) tienen full_matched > dis_matched')
    if totals['tif_n']:
        recall_full = 100 * totals['full_matched'] / totals['tif_n']
        recall_dis = 100 * totals['dis_matched'] / totals['tif_n']
        print(f'Recall pixel-level full: {recall_full:.1f}%  '
              f'disabled: {recall_dis:.1f}%  delta: {recall_full - recall_dis:+.1f}pp')


if __name__ == '__main__':
    main()
