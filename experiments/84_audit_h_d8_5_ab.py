"""84 — Audit comparativo H_D8_5 A/B (S37, commit 8).

Compara los 3 datasets:
  - operacional: data/mirova_equivalent/ (baseline actual, primary_cluster)
  - h_d8_5_disabled: data/_h_d8_5_disabled/ (control aislado del A/B)
  - h_d8_5_full: data/_h_d8_5_full/ (algoritmo MIROVA literal)

contra ground truth NRT (OCR consolidado scraper Mirova-v1, latest.php).

Métricas reportadas:
  - recall por dataset (TP / (TP+FN))
  - ratio mediano y medio: VRP nuestro / VRP MIROVA
  - sum_vrp vs primary_cluster comparación (solo h_d8_5_full)
  - dist_diff per record vs MIROVA distancia reportada
  - casos D8 detectados (dist_diff > 5 km)

Uso:
  python experiments/84_audit_h_d8_5_ab.py
  python experiments/84_audit_h_d8_5_ab.py --start 2026-04-15 --end 2026-05-09

Default window: misma que el workflow A/B (30d 2026-04-12 → 2026-05-11).
Ground truth = OCR Mirova-v1 (NRT, lo que MIROVA disparó en vivo).
"""
import json, sys, io, csv, urllib.request, statistics, argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent

VOL_MAP_OCR = {
    'Isluga': 'Isluga', 'Lascar': 'Lascar', 'Lastarria': 'Lastarria',
    'Tupungatito': 'Tupungatito', 'PlanchonPeteroa': 'PlanchonPeteroa',
    'NevadosDeChillan': 'Nevados de Chillan', 'Copahue': 'Copahue',
    'Llaima': 'Llaima', 'Villarrica': 'Villarrica',
    'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'Chaiten': 'Chaitén',
}
REV_MAP_OCR = {v: k for k, v in VOL_MAP_OCR.items()}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--start', default='2026-04-12')
    p.add_argument('--end', default='2026-05-11 23:59:59')
    return p.parse_args()


def load_alertas(start, end):
    cons = '/tmp/cons_84.csv'
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/'
        'monitoreo_satelital/registro_vrp_consolidado.csv',
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
            if ts < start or ts > end:
                continue
            if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA':
                continue
            alertas[(v_int, r['Sensor'].strip(), ts[:16])] = {
                'vrp': float(r.get('VRP_MW', 0) or 0),
                'dist': float(r.get('Distancia_km', 0) or 0),
            }
    return alertas


def load_recs(d, start, end):
    out = {}
    if not d.exists():
        return out
    for jf in d.glob('*.json'):
        with open(jf) as f:
            data = json.load(f)
        recs = data if isinstance(data, list) else data.get('records', [])
        for r in recs:
            dt = r.get('datetime_utc', '')
            if dt < start or dt > end:
                continue
            out[(jf.stem, r.get('sensor', ''), dt)] = r
    return out


def sens_to_cons(s):
    if 'MODIS' in s:
        return 'MODIS'
    if '_750' in s:
        return 'VIIRS'
    return 'VIIRS375'


def measure(dataset, alertas, common, label, vrp_field='vrp_mw'):
    """Mide recall + ratio. vrp_field='vrp_mw' usa el primary_cluster style
    (compat actual); 'vrp_mw_sum_active' usa el campo nuevo H_D8_5.
    """
    tp = fn = 0
    ratios = []
    dist_diffs = []
    d8_cases = 0
    for (vol, sens_cons, ts_min), info in alertas.items():
        if vol not in common:
            continue
        found = False
        for k, r in dataset.items():
            if k[0] != vol or k[2][:16] != ts_min:
                continue
            if sens_to_cons(k[1]) != sens_cons:
                continue
            vrp = r.get(vrp_field) or 0
            # Fallback al primary cuando sum field no existe (disabled profile)
            if vrp == 0 and vrp_field != 'vrp_mw':
                vrp = r.get('vrp_mw', 0) or 0
            if vrp > 0:
                found = True
                if info['vrp'] > 0:
                    ratios.append(vrp / info['vrp'])
                # dist comparison
                dist_field = ('hotspot_dist_km_furthest'
                              if vrp_field == 'vrp_mw_sum_active'
                              else 'hotspot_dist_km')
                our_dist = r.get(dist_field) or r.get('hotspot_dist_km') or 0
                if our_dist and info['dist']:
                    dist_diffs.append(abs(our_dist - info['dist']))
                    if abs(our_dist - info['dist']) > 5.0:
                        d8_cases += 1
                break
        if found:
            tp += 1
        else:
            fn += 1
    n = tp + fn
    rec = 100 * tp / n if n else 0
    med = statistics.median(ratios) if ratios else 0
    mn = statistics.mean(ratios) if ratios else 0
    med_diff = statistics.median(dist_diffs) if dist_diffs else 0
    print(f'{label:<30} recall={rec:>5.1f}% TP={tp:>3} FN={fn:>3}  '
          f'ratio_med={med:>6.2f}x mean={mn:>6.2f}x  '
          f'dist_diff_med={med_diff:>5.2f}km  D8_cases={d8_cases}')
    return {'recall': rec, 'tp': tp, 'fn': fn, 'ratio_med': med,
            'ratio_mean': mn, 'dist_diff_med': med_diff,
            'd8_cases': d8_cases, 'n_ratios': len(ratios)}


def main():
    args = parse_args()
    print(f'Window: {args.start} → {args.end}')
    print()
    alertas = load_alertas(args.start, args.end)
    print(f'Alertas MIROVA NRT (OCR) en window: {len(alertas)}')

    op = load_recs(REPO / 'data' / 'mirova_equivalent', args.start, args.end)
    dis = load_recs(REPO / 'data' / '_h_d8_5_disabled', args.start, args.end)
    full = load_recs(REPO / 'data' / '_h_d8_5_full', args.start, args.end)

    vols_op = {p.stem for p in (REPO / 'data' / 'mirova_equivalent').glob('*.json')}
    vols_dis = ({p.stem for p in (REPO / 'data' / '_h_d8_5_disabled').glob('*.json')}
                if (REPO / 'data' / '_h_d8_5_disabled').exists() else set())
    vols_full = ({p.stem for p in (REPO / 'data' / '_h_d8_5_full').glob('*.json')}
                 if (REPO / 'data' / '_h_d8_5_full').exists() else set())

    if not vols_dis or not vols_full:
        print()
        print('  ⚠ Datasets H_D8_5 A/B aún no presentes en disco.')
        print('  Trigger workflow: gh workflow run reproc-ab-h-d8-5.yml '
              '-f start=2026-04-12 -f end=2026-05-11')
        print('  Esperar finalización (~1-2 h) y re-correr este script.')
        return

    common = vols_op & vols_dis & vols_full
    print(f'common vols ({len(common)}): {sorted(common)}')
    common_alertas = {k: v for k, v in alertas.items() if k[0] in common}
    print(f'Alertas en common vols: {len(common_alertas)}')
    print()

    print('=== A/B H_D8_5 (window={start}, vols={n}) ==='.format(
        start=args.start[:10], n=len(common)))
    measure(op, alertas, common, 'operacional (primary)', 'vrp_mw')
    measure(dis, alertas, common, 'h_d8_5_disabled (primary)', 'vrp_mw')
    measure(full, alertas, common, 'h_d8_5_full (primary)', 'vrp_mw')
    measure(full, alertas, common, 'h_d8_5_full (sum_active)', 'vrp_mw_sum_active')

    # Per volcano breakdown
    print()
    print('=== Per volcano (sum_active H_D8_5 full vs disabled primary) ===')
    for vol in sorted(common):
        n_alerta = sum(1 for k in common_alertas if k[0] == vol)
        if n_alerta == 0:
            continue
        # disabled primary
        tp_dis = 0
        for (v, sens_cons, ts_min) in common_alertas:
            if v != vol:
                continue
            for k, r in dis.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_dis += 1
                    break
        # full sum_active
        tp_full = 0
        for (v, sens_cons, ts_min) in common_alertas:
            if v != vol:
                continue
            for k, r in full.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons):
                    vrp_field = (r.get('vrp_mw_sum_active')
                                 or r.get('vrp_mw', 0)) or 0
                    if vrp_field > 0:
                        tp_full += 1
                    break
        print(f'  {vol:<22} alertas={n_alerta:>3}  '
              f'disabled TP={tp_dis:>3}  full TP={tp_full:>3}  '
              f'delta={tp_full - tp_dis:+d}')


if __name__ == '__main__':
    main()
