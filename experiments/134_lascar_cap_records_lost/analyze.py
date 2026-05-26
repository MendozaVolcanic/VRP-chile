"""F2.5.b R2-style: Lascar records lost due to S71 cap (PR #112).

Compare pre-cap baseline vs cap-only profile for Lascar (90d window).
Identify lost detections + cross-reference MIROVA NRT (CONS+OCR).
"""
import csv
import json
import io
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PRE = json.load(open('experiments/134_lascar_cap_records_lost/Lascar_precap.json'))
CAP = json.load(open('data/mirova_equivalent_path_d_cap_v1/Lascar.json'))


def in_window(r):
    return '2026-02-20' <= r.get('datetime_utc', '')[:10] <= '2026-05-20'


pre_w = [r for r in PRE['records'] if in_window(r)]
cap_w = [r for r in CAP['records'] if in_window(r)]

# Sensor normalization: pre uses VIIRS_SNPP_750 (M-band) AND VIIRS_SNPP (I-band); cap profile may only have I-band
pre_map = {(r['datetime_utc'], r['sensor']): r for r in pre_w}
cap_map = {(r['datetime_utc'], r['sensor']): r for r in cap_w}
shared = set(pre_map) & set(cap_map)
only_pre = set(pre_map) - set(cap_map)

print(f'pre_w: {len(pre_w)}, cap_w: {len(cap_w)}, shared: {len(shared)}, only_pre: {len(only_pre)}')
print(f'only_pre sensors: {Counter(s for _, s in only_pre)}')


# Load MIROVA NRT (CONS+OCR)
def load_mirova(fp):
    rows = []
    with open(fp, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['Volcan'].strip().lower() != 'lascar':
                continue
            try:
                dt = datetime.strptime(r['Fecha_Satelite_UTC'], '%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
            rows.append({
                'dt': dt,
                'sensor': r['Sensor'].strip().upper(),
                'vrp_mw': float(r['VRP_MW'] or 0),
                'dist_km': float(r['Distancia_km'] or 0),
                'tipo': r['Tipo_Registro'].strip(),
                'clasif': r.get('Clasificacion Mirova', '').strip(),
            })
    return rows


mirova_rows = (load_mirova('data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv')
               + load_mirova('data/mirova_reference/registro_vrp_ocr.csv'))
mirova_rows = [r for r in mirova_rows if datetime(2026, 2, 20) <= r['dt'] <= datetime(2026, 5, 20, 23, 59)]
print(f'MIROVA Lascar rows in window: {len(mirova_rows)}')


def mirova_match(dt_utc_str, our_sensor, tol_min=60):
    """Find MIROVA NRT row within +/- tol_min of dt_utc_str on same sensor family."""
    try:
        dt = datetime.strptime(dt_utc_str, '%Y-%m-%d %H:%M')
    except Exception:
        return None
    family = 'MODIS' if 'MODIS' in our_sensor else 'VIIRS'
    best = None
    for r in mirova_rows:
        if family not in r['sensor']:
            continue
        delta = abs((r['dt'] - dt).total_seconds()) / 60.0
        if delta <= tol_min:
            if best is None or delta < best[0]:
                best = (delta, r)
    return best


# Categorize all shared records: lost (detection -> none) + capped (still detection, mag diff)
lost_records = []
capped_records = []
for k in shared:
    p = pre_map[k]
    c = cap_map[k]
    pv = (p.get('primary_cluster') or {}).get('vrp_mw') or 0.0
    cv = (c.get('primary_cluster') or {}).get('vrp_mw') or 0.0
    if pv > 0.01 and cv <= 0.01:
        lost_records.append((k, p, c))
    elif pv > 0.01 and cv > 0.01 and pv != cv:
        capped_records.append((k, p, c))

print(f'\n=== LOST (detection -> non-detection): {len(lost_records)} ===')
print(f'=== CAPPED (still detection, magnitude shifted): {len(capped_records)} ===')


# Categorize lost: A = MIROVA also detects (TP loss); B = MIROVA does NOT detect (FP fix)
def classify(rec_tuple):
    k, p, c = rec_tuple
    dt_str, sens = k
    m = mirova_match(dt_str, sens, tol_min=60)
    if m is None:
        return 'B_no_mirova_match', None
    delta, mr = m
    # Detection: alerta termica or vrp>0.1
    is_alerta = 'ALERTA' in mr['tipo'].upper()
    is_detection = is_alerta or mr['vrp_mw'] > 0.1
    if is_detection:
        return 'A_mirova_detects', mr
    else:
        return 'B_mirova_rutina_zero', mr


lost_categorized = [(k, p, c, *classify((k, p, c))) for (k, p, c) in lost_records]
capped_categorized = [(k, p, c, *classify((k, p, c))) for (k, p, c) in capped_records]


def summary_cat(records):
    cnt = Counter(cat for _, _, _, cat, _ in records)
    return dict(cnt)


print(f'\nLost categorization: {summary_cat(lost_categorized)}')
print(f'Capped categorization: {summary_cat(capped_categorized)}')


# Detail table for lost
print('\n=== Detail LOST (13 records) ===')
header = ['datetime_utc', 'sensor', 'pre_vrp', 'cap_vrp', 'pre_pc_vrp', 'cap_pc_vrp',
         't_bg_pre', 't_bg_cap', 'pre_ctx', 'cap_ctx', 'pre_bt', 'cap_bt', 'pre_nti', 'cap_nti',
         'category', 'mirova_vrp', 'mirova_tipo', 'mirova_dist']
print('\t'.join(header))
for k, p, c, cat, mr in lost_categorized:
    pc_p = p.get('primary_cluster') or {}
    pc_c = c.get('primary_cluster') or {}
    row = [
        k[0], k[1],
        f"{p.get('vrp_mw', 0):.3f}",
        f"{c.get('vrp_mw', 0):.3f}",
        f"{pc_p.get('vrp_mw') or 0:.3f}",
        f"{pc_c.get('vrp_mw') or 0:.3f}",
        f"{p.get('t_bg_k', 0):.1f}",
        f"{c.get('t_bg_k', 0):.1f}",
        str(p.get('diag_n_dnti_ctx_path')),
        str(c.get('diag_n_dnti_ctx_path')),
        str(p.get('diag_n_bt_path')),
        str(c.get('diag_n_bt_path')),
        str(p.get('diag_n_nti_path')),
        str(c.get('diag_n_nti_path')),
        cat,
        f"{mr['vrp_mw']:.2f}" if mr else '-',
        mr['tipo'] if mr else '-',
        f"{mr['dist_km']:.1f}" if mr else '-',
    ]
    print('\t'.join(row))


# Detail summary for capped: how many were originally insane magnitudes (>>5MW) at t_bg<270K
print('\n=== Capped magnitude distribution ===')
capped_above_5_at_cold = [(k, p, c) for k, p, c, _, _ in capped_categorized
                         if (p.get('primary_cluster') or {}).get('vrp_mw', 0) > 5.0
                         and c.get('t_bg_k', 999) < 270.0]
print(f'Capped at vrp>5MW & t_bg<270K (cap target): {len(capped_above_5_at_cold)}')

big_drops = sorted(capped_categorized,
                  key=lambda x: -((x[1].get('primary_cluster') or {}).get('vrp_mw', 0)
                                  / max((x[2].get('primary_cluster') or {}).get('vrp_mw', 1e-9), 1e-9)))[:10]
print('\nTop 10 biggest cap reductions (pre/cap ratio):')
print('datetime_utc\tsensor\tpre_pc_vrp\tcap_pc_vrp\tratio\tt_bg\tcategory\tmirova_vrp\tmirova_tipo')
for k, p, c, cat, mr in big_drops:
    pp = (p.get('primary_cluster') or {}).get('vrp_mw', 0)
    cc = (c.get('primary_cluster') or {}).get('vrp_mw', 0)
    ratio = pp / max(cc, 1e-9)
    print(f"{k[0]}\t{k[1]}\t{pp:.2f}\t{cc:.2f}\t{ratio:.1f}\t{c.get('t_bg_k', 0):.1f}\t{cat}\t{(mr['vrp_mw'] if mr else 0):.2f}\t{(mr['tipo'] if mr else '-')}")


# Save bulk JSON
out = {
    'window': '2026-02-20..2026-05-20',
    'pre_records': len(pre_w),
    'cap_records': len(cap_w),
    'shared_records': len(shared),
    'only_in_pre': len(only_pre),
    'only_in_pre_note': 'These 315 records (all VIIRS_*_750) were absent from path_d_cap_v1 profile, NOT lost-to-cap.',
    'lost_count': len(lost_records),
    'capped_count': len(capped_records),
    'lost_categorization': summary_cat(lost_categorized),
    'capped_categorization': summary_cat(capped_categorized),
    'lost_details': [
        {
            'datetime_utc': k[0],
            'sensor': k[1],
            'pre': {
                'vrp_mw': p.get('vrp_mw'),
                'pc_vrp_mw': (p.get('primary_cluster') or {}).get('vrp_mw'),
                't_bg_k': p.get('t_bg_k'),
                'n_anomalous_pixels': p.get('n_anomalous_pixels'),
                'final_hotspot_dist_km': p.get('final_hotspot_dist_km'),
                'diag_n_bt_path': p.get('diag_n_bt_path'),
                'diag_n_nti_path': p.get('diag_n_nti_path'),
                'diag_n_dnti_ctx_path': p.get('diag_n_dnti_ctx_path'),
            },
            'cap': {
                'vrp_mw': c.get('vrp_mw'),
                'pc_vrp_mw': (c.get('primary_cluster') or {}).get('vrp_mw'),
                't_bg_k': c.get('t_bg_k'),
                'n_anomalous_pixels': c.get('n_anomalous_pixels'),
                'final_hotspot_dist_km': c.get('final_hotspot_dist_km'),
                'diag_n_bt_path': c.get('diag_n_bt_path'),
                'diag_n_nti_path': c.get('diag_n_nti_path'),
                'diag_n_dnti_ctx_path': c.get('diag_n_dnti_ctx_path'),
            },
            'category': cat,
            'mirova_nrt_match': {
                'vrp_mw': mr['vrp_mw'],
                'tipo': mr['tipo'],
                'clasif': mr['clasif'],
                'dist_km': mr['dist_km'],
                'sensor': mr['sensor'],
                'dt': mr['dt'].isoformat(),
            } if mr else None,
        }
        for k, p, c, cat, mr in lost_categorized
    ],
    'capped_summary': {
        'n_with_cap_target_match': len(capped_above_5_at_cold),
        'top_10_drops': [
            {
                'datetime_utc': k[0],
                'sensor': k[1],
                'pre_pc_vrp_mw': (p.get('primary_cluster') or {}).get('vrp_mw'),
                'cap_pc_vrp_mw': (c.get('primary_cluster') or {}).get('vrp_mw'),
                't_bg_k': c.get('t_bg_k'),
                'category': cat,
                'mirova_vrp_mw': mr['vrp_mw'] if mr else None,
                'mirova_tipo': mr['tipo'] if mr else None,
            }
            for k, p, c, cat, mr in big_drops
        ],
    },
}

with open('experiments/134_lascar_cap_records_lost/lost_records.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)
print('\nSaved -> experiments/134_lascar_cap_records_lost/lost_records.json')
