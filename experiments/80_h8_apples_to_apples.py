"""80 — H8 A/B comparison restricted to N-day window + common volcanoes.

Supports two ground truth sources:
  --source ocr (default)  Mirova-v1 latest.php scraping (live NRT, covers 2026+).
  --source osf            MIROVA OSF v2.5 archive (curated, ends 2025-12-31).

OSF requires running `experiments/82_osf_v25_audit.py` first to generate
`reports/osf_v25_tier_a.csv`. OSF refs are ~71× denser per volcano (48k vs
677 Tier A), so audits with adequate window overlap give much more reliable
recall/ratio estimates than OCR.

IMPORTANT — temporal coverage:
  - OSF v2.5 ends 2025-12-31. Pipeline `data/mirova_equivalent/` records
    typically start ~2026-01-29. For OSF mode to produce meaningful output,
    the pipeline must be reproc'd over a window within OSF coverage (e.g.
    `scripts/run_pipeline.py --start 2025-11-01 --end 2025-12-31`).
  - For 2026+ live audits, use --source ocr.

Defaults:
  --source ocr → window 2026-05-03 .. 2026-05-09 23:59:59 (current H8 A/B run)
  --source osf → window 2025-12-01 .. 2025-12-31 23:59:59 (last OSF month)
"""
import json, sys, io, csv, urllib.request, statistics, argparse
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent

# OSF IDvolc → internal VRP-chile volcano name. Doubles as Tier A whitelist.
TIER_A_IDVOLC = {
    '355100': 'Lascar', '355120': 'Lastarria', '357010': 'Tupungatito',
    '357120': 'Villarrica', '357150': 'PuyehueCordonCaulle', '357090': 'Copahue',
    '357070': 'NevadosDeChillan', '357110': 'Llaima', '358041': 'Chaiten',
    '357040': 'PlanchonPeteroa', '355030': 'Isluga',
}

# OCR consolidado: Spanish display name → internal VRP-chile name.
VOL_MAP_OCR = {
    'Isluga': 'Isluga', 'Lascar': 'Lascar', 'Lastarria': 'Lastarria',
    'Tupungatito': 'Tupungatito', 'PlanchonPeteroa': 'PlanchonPeteroa',
    'NevadosDeChillan': 'Nevados de Chillan', 'Copahue': 'Copahue',
    'Llaima': 'Llaima', 'Villarrica': 'Villarrica',
    'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'Chaiten': 'Chaitén',
}
REV_MAP_OCR = {v: k for k, v in VOL_MAP_OCR.items()}


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('--source', choices=['ocr', 'osf'], default='ocr',
                   help='Ground truth source (default: ocr).')
    p.add_argument('--win-start', default=None,
                   help='Window start YYYY-MM-DD[ HH:MM[:SS]] (default depends on --source).')
    p.add_argument('--win-end', default=None,
                   help='Window end YYYY-MM-DD[ HH:MM[:SS]] (default depends on --source).')
    p.add_argument('--osf-include-class0', action='store_true',
                   help='Include OSF class=0 records (curated FPs). Default: exclude.')
    return p.parse_args()


def load_ocr(win_start, win_end):
    """Load alertas dict from OCR consolidado (Mirova-v1 scraper of latest.php).

    Returns: {(vol_internal, sensor_raw, ts_min): {'vrp': MW, 'dist': km}}
    where ts_min is the first 16 chars of ISO datetime ('YYYY-MM-DD HH:MM').
    """
    cons = '/tmp/cons.csv'
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv',
        cons,
    )
    alertas = {}
    with open(cons, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            v = r['Volcan'].strip()
            v_int = REV_MAP_OCR.get(v)
            if not v_int:
                continue
            ts = r['Fecha_Satelite_UTC'].strip()
            # OCR timestamps are ISO 'YYYY-MM-DD HH:MM:SS', lexicographic compare ok
            if ts < win_start or ts > win_end:
                continue
            if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA':
                continue
            alertas[(v_int, r['Sensor'].strip(), ts[:16])] = {
                'vrp': float(r.get('VRP_MW', 0) or 0),
                'dist': float(r.get('Distancia_km', 0) or 0),
            }
    return alertas


def osf_sensor_label(satellite, resolution):
    """Map OSF (Satellite, Resolution) → OCR-equivalent sensor token.

    Satellite: '1'=MODIS Terra, '2'=MODIS Aqua, '3'=VIIRS SNPP, '4'=VIIRS NOAA20.
    Resolution: '1000' (MODIS), '750' (VIIRS M-band), '375' (VIIRS I-band).
    Output matches sens_to_cons() bucket: MODIS / VIIRS / VIIRS375.
    """
    sat = str(satellite).strip()
    res = str(resolution).strip()
    if sat in ('1', '2'):
        return 'MODIS'
    if res == '375':
        return 'VIIRS375'
    return 'VIIRS'  # 750 M-band


def _parse_window_bound(s):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    sys.exit(f'ERROR: cannot parse window bound: {s!r}')


def load_osf(win_start, win_end, include_class0=False):
    """Load alertas dict from MIROVA OSF v2.5 archive (filtered Tier A).

    Requires `reports/osf_v25_tier_a.csv` produced by
    `experiments/82_osf_v25_audit.py`. By default excludes class=0 (curated
    FPs); pass include_class0=True to keep them for raw-detection comparisons.

    Returns same shape as load_ocr().
    """
    p = REPO / 'reports' / 'osf_v25_tier_a.csv'
    if not p.exists():
        sys.exit(
            f'ERROR: {p} not found.\n'
            f'Generate first:\n'
            f'  python experiments/82_osf_v25_audit.py'
        )
    ws = _parse_window_bound(win_start)
    we = _parse_window_bound(win_end)
    alertas = {}
    with open(p, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            idv = r['IDvolc'].strip()
            if idv not in TIER_A_IDVOLC:
                continue
            cls = r.get('class', '').strip()
            if not include_class0 and cls == '0':
                continue
            try:
                ts = datetime.strptime(r['timeUTC'], '%d/%m/%Y %H:%M')
            except ValueError:
                continue
            if ts < ws or ts > we:
                continue
            vol = TIER_A_IDVOLC[idv]
            sens = osf_sensor_label(r['Satellite'], r['Resolution'])
            ts_key = ts.strftime('%Y-%m-%d %H:%M')  # 16 chars, matches OCR key
            alertas[(vol, sens, ts_key)] = {
                'vrp': float(r.get('VRP', 0) or 0),
                'dist': float(r.get('Max_Dist', 0) or 0),
            }
    return alertas


def load_recs(d, win_start, win_end):
    """Load pipeline JSON records from a profile directory into dict."""
    out = {}
    if not d.exists():
        return out
    for jf in d.glob('*.json'):
        with open(jf) as f:
            data = json.load(f)
        recs = data if isinstance(data, list) else data.get('records', [])
        for r in recs:
            dt = r.get('datetime_utc', '')
            if dt < win_start or dt > win_end:
                continue
            out[(jf.stem, r.get('sensor', ''), dt)] = r
    return out


def sens_to_cons(s):
    """Pipeline sensor name → OCR/OSF sensor bucket."""
    if 'MODIS' in s:
        return 'MODIS'
    if '_750' in s:
        return 'VIIRS'
    return 'VIIRS375'


def measure(dataset, alertas, common, label):
    tp = fn = 0
    ratios = []
    for (vol, sens_cons, ts_min), info in alertas.items():
        if vol not in common:
            continue
        found = False
        for k, r in dataset.items():
            if k[0] != vol:
                continue
            if k[2][:16] != ts_min:
                continue
            if sens_to_cons(k[1]) != sens_cons:
                continue
            vrp = r.get('vrp_mw', 0) or 0
            if vrp > 0:
                found = True
                if info['vrp'] > 0:
                    ratios.append(vrp / info['vrp'])
                break
        if found:
            tp += 1
        else:
            fn += 1
    n = tp + fn
    rec = 100 * tp / n if n else 0
    med = statistics.median(ratios) if ratios else 0
    mn = statistics.mean(ratios) if ratios else 0
    print(f'{label:<14} recall={rec:>5.1f}% TP={tp:>3} FN={fn:>3}  '
          f'ratio_med={med:>6.2f}x ratio_mean={mn:>6.2f}x  (n_ratios={len(ratios)})')


def main():
    args = parse_args()

    # Window defaults per source
    if args.source == 'ocr':
        win_start = args.win_start or '2026-05-03'
        win_end = args.win_end or '2026-05-09 23:59:59'
    else:
        win_start = args.win_start or '2025-12-01'
        win_end = args.win_end or '2025-12-31 23:59:59'

    print(f'Source: {args.source}  Window: {win_start} → {win_end}')
    if args.source == 'osf':
        print(f"OSF mode: class=0 (curated FPs) "
              f"{'INCLUDED' if args.osf_include_class0 else 'EXCLUDED'}")

    if args.source == 'ocr':
        alertas = load_ocr(win_start, win_end)
    else:
        alertas = load_osf(win_start, win_end, args.osf_include_class0)

    print(f'Alertas in window: {len(alertas)}')
    if not alertas:
        print('  No refs in window — adjust --win-start/--win-end or switch source.')
        if args.source == 'osf':
            print('  Note: OSF v2.5 coverage ends 2025-12-31.')
            print('  Pipeline operational records typically start 2026-01-29.')
            print('  For OSF audits, reproc pipeline over a 2025 window first:')
            print('    scripts/run_pipeline.py --profile mirova_equivalent '
                  '--volcano <vol> --start 2025-11-01 --end 2025-12-31')
        return

    baseline = load_recs(REPO / 'data' / 'mirova_equivalent', win_start, win_end)
    h8_off = load_recs(REPO / 'data' / '_h8_pixel_filter_disabled', win_start, win_end)
    h8_on = load_recs(REPO / 'data' / '_h8_pixel_filter_enabled', win_start, win_end)

    dir_off = REPO / 'data' / '_h8_pixel_filter_disabled'
    dir_on = REPO / 'data' / '_h8_pixel_filter_enabled'
    vols_off = {p.stem for p in dir_off.glob('*.json')} if dir_off.exists() else set()
    vols_on = {p.stem for p in dir_on.glob('*.json')} if dir_on.exists() else set()

    if vols_off and vols_on:
        common = vols_off & vols_on
    else:
        # No A/B reprocs found — fall back to baseline-only audit over alertas vols
        common = {k[0] for k in alertas.keys()}
        print(f'(no h8 A/B reprocs found in data/_h8_pixel_filter_{{disabled,enabled}}/; '
              f'falling back to alertas vols for "common")')

    print(f'common vols ({len(common)}): {sorted(common)}')

    common_alertas = {k: v for k, v in alertas.items() if k[0] in common}
    print(f'\nAlertas en common vols: {len(common_alertas)}')

    print(f'\n=== APPLES-TO-APPLES (window={win_start}/{win_end} '
          f'source={args.source}, vols comunes) ===')
    measure(baseline, alertas, common, 'baseline')
    if h8_off:
        measure(h8_off, alertas, common, 'h8_off')
    if h8_on:
        measure(h8_on, alertas, common, 'h8_on')

    if not (h8_off or h8_on):
        print('  (h8_off / h8_on datasets empty in this window — '
              'reproc those profiles to include them in A/B)')
        return

    # Per-volcano breakdown for h8 A/B
    print('\n=== Per volcano breakdown (h8_off vs h8_on) ===')
    for vol in sorted(common):
        n_alerta = sum(1 for k in common_alertas if k[0] == vol)
        if n_alerta == 0:
            continue
        tp_off = tp_on = 0
        for (v, sens_cons, ts_min) in common_alertas:
            if v != vol:
                continue
            for k, r in h8_off.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_off += 1
                    break
            for k, r in h8_on.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_on += 1
                    break
        print(f'  {vol:<22} alertas={n_alerta:>3}  off TP={tp_off:>3}  '
              f'on TP={tp_on:>3}  delta={tp_on - tp_off:+d}')


if __name__ == '__main__':
    main()
