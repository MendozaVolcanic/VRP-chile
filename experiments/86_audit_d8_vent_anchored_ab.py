"""86 — Audit comparativo D8 vent-anchored A/B (S38).

Adaptado de experiments/84 para los profiles vent-anchored. Compara:
  - operacional:               data/mirova_equivalent/ (baseline)
  - d8_vent_anchored_disabled: data/_d8_vent_anchored_disabled/ (control)
  - d8_vent_anchored:          data/_d8_vent_anchored/ (vent-anchored + H8)

contra ground truth NRT (OCR consolidado Mirova-v1).

Métricas:
- recall por dataset
- ratio_med (objetivo: bajar de 3.79× a <2.0×)
- dist_diff_med (vent_anchored debería matchear MIROVA mejor)
- D8 cases (dist_diff>5km) (objetivo: bajar de 31 a <10)
- Per-volcano breakdown TP / dist_diff

Uso:
  python experiments/86_audit_d8_vent_anchored_ab.py
  python experiments/86_audit_d8_vent_anchored_ab.py --start 2026-04-27 --end "2026-05-11 23:59:59"
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
    p.add_argument('--start', default='2026-04-27')
    p.add_argument('--end', default='2026-05-11 23:59:59')
    return p.parse_args()


def load_alertas(start, end):
    cons = '/tmp/cons_86.csv'
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/'
        'monitoreo_satelital/registro_vrp_consolidado.csv', cons)
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


def measure(dataset, alertas, common, label):
    """Mide recall + ratio para un dataset usando primary_cluster style
    (campo vrp_mw). vent_anchored cambia QUE cluster es primary pero el
    campo sigue siendo vrp_mw del record (= sum hot pixels post H8 si
    pixel filter activo).
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
            vrp = r.get('vrp_mw') or 0
            if vrp > 0:
                found = True
                if info['vrp'] > 0:
                    ratios.append(vrp / info['vrp'])
                # dist_diff: nuestra primary cluster vs MIROVA reported
                our_dist = r.get('hotspot_dist_km') or 0
                if our_dist and info['dist']:
                    diff = abs(our_dist - info['dist'])
                    dist_diffs.append(diff)
                    if diff > 5.0:
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
    print(f'{label:<32} recall={rec:>5.1f}% TP={tp:>3} FN={fn:>3}  '
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
    dis = load_recs(REPO / 'data' / '_d8_vent_anchored_disabled', args.start, args.end)
    va = load_recs(REPO / 'data' / '_d8_vent_anchored', args.start, args.end)

    dir_op = REPO / 'data' / 'mirova_equivalent'
    dir_dis = REPO / 'data' / '_d8_vent_anchored_disabled'
    dir_va = REPO / 'data' / '_d8_vent_anchored'
    vols_op = {p.stem for p in dir_op.glob('*.json')} if dir_op.exists() else set()
    vols_dis = ({p.stem for p in dir_dis.glob('*.json')}
                if dir_dis.exists() else set())
    vols_va = ({p.stem for p in dir_va.glob('*.json')}
                if dir_va.exists() else set())

    if not vols_dis or not vols_va:
        print()
        print('  ⚠ Datasets D8 vent-anchored A/B aún no presentes.')
        print('  Trigger: gh workflow run "A/B reproceso D8 vent-anchored '
              'clustering (S38)" -f start=2026-04-27 -f end=2026-05-11')
        return

    common = vols_op & vols_dis & vols_va
    print(f'common vols ({len(common)}): {sorted(common)}')
    common_alertas = {k: v for k, v in alertas.items() if k[0] in common}
    print(f'Alertas en common vols: {len(common_alertas)}')
    print()

    print(f'=== A/B D8 vent-anchored (window={args.start[:10]}, vols={len(common)}) ===')
    measure(op, alertas, common, 'operacional')
    measure(dis, alertas, common, 'd8_vent_anchored_disabled')
    r_va = measure(va, alertas, common, 'd8_vent_anchored (target)')

    # Per volcano breakdown
    print()
    print('=== Per volcano (vent-anchored vs disabled) ===')
    for vol in sorted(common):
        n_alerta = sum(1 for k in common_alertas if k[0] == vol)
        if n_alerta == 0:
            continue
        tp_dis = 0
        tp_va = 0
        d8_dis = 0
        d8_va = 0
        for (v, sens_cons, ts_min), info in common_alertas.items():
            if v != vol:
                continue
            # disabled
            for k, r in dis.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_dis += 1
                    our_dist = r.get('hotspot_dist_km') or 0
                    if our_dist and info['dist'] and abs(our_dist - info['dist']) > 5.0:
                        d8_dis += 1
                    break
            # vent_anchored
            for k, r in va.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_va += 1
                    our_dist = r.get('hotspot_dist_km') or 0
                    if our_dist and info['dist'] and abs(our_dist - info['dist']) > 5.0:
                        d8_va += 1
                    break
        print(f'  {vol:<22} alertas={n_alerta:>3}  '
              f'disabled TP={tp_dis:>3} D8={d8_dis:>2}  '
              f'va TP={tp_va:>3} D8={d8_va:>2}  '
              f'delta_TP={tp_va-tp_dis:+d} delta_D8={d8_va-d8_dis:+d}')


if __name__ == '__main__':
    main()
