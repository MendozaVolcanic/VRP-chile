"""87 — Audit comparativo D8 combo (S38 C.1).

Compara operacional / disabled / combo_full (vent_anchored + H8 + lbg_global).
Adaptado de experiments/86 con los profiles combo.
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
    cons = '/tmp/cons_87.csv'
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/'
        'monitoreo_satelital/registro_vrp_consolidado.csv', cons)
    alertas = {}
    with open(cons, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            v_int = REV_MAP_OCR.get(r['Volcan'].strip())
            if not v_int: continue
            ts = r['Fecha_Satelite_UTC'].strip()
            if ts < start or ts > end: continue
            if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA': continue
            alertas[(v_int, r['Sensor'].strip(), ts[:16])] = {
                'vrp': float(r.get('VRP_MW', 0) or 0),
                'dist': float(r.get('Distancia_km', 0) or 0),
            }
    return alertas


def load_recs(d, start, end):
    out = {}
    if not d.exists(): return out
    for jf in d.glob('*.json'):
        with open(jf) as f: data = json.load(f)
        recs = data if isinstance(data, list) else data.get('records', [])
        for r in recs:
            dt = r.get('datetime_utc', '')
            if dt < start or dt > end: continue
            out[(jf.stem, r.get('sensor', ''), dt)] = r
    return out


def sens_to_cons(s):
    if 'MODIS' in s: return 'MODIS'
    if '_750' in s: return 'VIIRS'
    return 'VIIRS375'


def measure(dataset, alertas, common, label):
    tp = fn = 0
    ratios = []
    dist_diffs = []
    d8_cases = 0
    for (vol, sens_cons, ts_min), info in alertas.items():
        if vol not in common: continue
        found = False
        for k, r in dataset.items():
            if k[0] != vol or k[2][:16] != ts_min: continue
            if sens_to_cons(k[1]) != sens_cons: continue
            vrp = r.get('vrp_mw') or 0
            if vrp > 0:
                found = True
                if info['vrp'] > 0: ratios.append(vrp / info['vrp'])
                our_dist = r.get('hotspot_dist_km') or 0
                if our_dist and info['dist']:
                    diff = abs(our_dist - info['dist'])
                    dist_diffs.append(diff)
                    if diff > 5.0: d8_cases += 1
                break
        if found: tp += 1
        else: fn += 1
    n = tp + fn
    rec = 100 * tp / n if n else 0
    med = statistics.median(ratios) if ratios else 0
    mn = statistics.mean(ratios) if ratios else 0
    med_diff = statistics.median(dist_diffs) if dist_diffs else 0
    print(f'{label:<30} recall={rec:>5.1f}% TP={tp:>3} FN={fn:>3}  '
          f'ratio_med={med:>6.2f}x mean={mn:>6.2f}x  '
          f'dist_diff_med={med_diff:>5.2f}km  D8={d8_cases}')


def main():
    args = parse_args()
    print(f'Window: {args.start} → {args.end}')
    alertas = load_alertas(args.start, args.end)
    print(f'Alertas MIROVA NRT: {len(alertas)}\n')

    op = load_recs(REPO/'data'/'mirova_equivalent', args.start, args.end)
    dis = load_recs(REPO/'data'/'_d8_combo_disabled', args.start, args.end)
    full = load_recs(REPO/'data'/'_d8_combo_full', args.start, args.end)

    dir_dis = REPO/'data'/'_d8_combo_disabled'
    dir_full = REPO/'data'/'_d8_combo_full'
    vols_op = {p.stem for p in (REPO/'data'/'mirova_equivalent').glob('*.json')}
    vols_dis = ({p.stem for p in dir_dis.glob('*.json')} if dir_dis.exists() else set())
    vols_full = ({p.stem for p in dir_full.glob('*.json')} if dir_full.exists() else set())

    if not vols_dis or not vols_full:
        print('  ⚠ Datasets combo no presentes — trigger workflow primero.')
        return

    common = vols_op & vols_dis & vols_full
    print(f'common vols ({len(common)}): {sorted(common)}')
    common_alertas = {k: v for k, v in alertas.items() if k[0] in common}
    print(f'Alertas en common vols: {len(common_alertas)}\n')

    print(f'=== A/B D8 combo (window={args.start[:10]}, vols={len(common)}) ===')
    measure(op, alertas, common, 'operacional')
    measure(dis, alertas, common, '_d8_combo_disabled')
    measure(full, alertas, common, '_d8_combo_full (target)')

    print('\n=== Per volcano (combo full vs disabled) ===')
    for vol in sorted(common):
        n_alerta = sum(1 for k in common_alertas if k[0] == vol)
        if n_alerta == 0: continue
        tp_dis = tp_full = 0
        for (v, sens_cons, ts_min) in common_alertas:
            if v != vol: continue
            for k, r in dis.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_dis += 1; break
            for k, r in full.items():
                if (k[0] == vol and k[2][:16] == ts_min
                        and sens_to_cons(k[1]) == sens_cons
                        and (r.get('vrp_mw', 0) or 0) > 0):
                    tp_full += 1; break
        print(f'  {vol:<22} alertas={n_alerta:>3}  '
              f'dis TP={tp_dis:>3}  full TP={tp_full:>3}  delta={tp_full-tp_dis:+d}')


if __name__ == '__main__':
    main()
