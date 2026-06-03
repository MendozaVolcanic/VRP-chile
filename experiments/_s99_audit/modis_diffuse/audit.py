# -*- coding: utf-8 -*-
"""
S99 MODIS diffuse-field scope audit.
Characterizes MODIS records with pc.vrp_mw > 50/20 MW across the 11 Tier A
volcanoes that MIROVA does NOT report from MODIS.

Read-only over data/mirova_equivalent/*.json + latest_consolidado.csv + OCR CSV.
NO numbers by hand: every figure in scope.md is sourced from this script's JSON output.
"""
import json, csv, os, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DATA = os.path.join(ROOT, 'data', 'mirova_equivalent')
OUT  = os.path.dirname(__file__)

TIER_A = ['PuyehueCordonCaulle','Villarrica','Lascar','Copahue','NevadosDeChillan',
          'Llaima','Chaiten','PlanchonPeteroa','Lastarria','Isluga','Tupungatito']

def pcvrp(r):
    pc = r.get('primary_cluster') or {}
    return pc.get('vrp_mw') or 0.0

def is_modis(r):
    return 'MODIS' in (r.get('sensor') or '')

def load(vol):
    p = os.path.join(DATA, vol + '.json')
    d = json.load(open(p, encoding='utf-8'))
    return d['records'] if isinstance(d, dict) and 'records' in d else d

# ---- Step 1+2: per-vol MODIS big records, path breakdown ----
result = {'per_vol': {}, 'big_records': {}}
for vol in TIER_A:
    recs = load(vol)
    modis = [r for r in recs if is_modis(r)]
    over50 = [r for r in modis if pcvrp(r) > 50]
    over20 = [r for r in modis if pcvrp(r) > 20]
    # path attribution among >20 records: count dominant path by diag_n_* on the cluster's pixels
    def dom_path(r):
        d = {'eti': r.get('diag_n_eti_path') or 0,
             'nti': r.get('diag_n_nti_path') or 0,
             'dnti_ctx': r.get('diag_n_dnti_ctx_path') or 0,
             'bt': r.get('diag_n_bt_path') or 0}
        if r.get('triggered_test1'):
            d['test1'] = r.get('n_test1_pixels') or 1
        return max(d, key=d.get) if any(d.values()) else 'none'
    pathcount20 = {}
    for r in over20:
        pathcount20[dom_path(r)] = pathcount20.get(dom_path(r), 0) + 1
    result['per_vol'][vol] = {
        'n_modis_total': len(modis),
        'n_modis_over20': len(over20),
        'n_modis_over50': len(over50),
        'max_pc_vrp': round(max([pcvrp(r) for r in modis], default=0), 1),
        'dom_path_over20': pathcount20,
        'n_triggered_test1_over20': sum(1 for r in over20 if r.get('triggered_test1')),
        'n_source_eruption_over20': sum(1 for r in over20 if r.get('final_hotspot_source') == 'eruption'),
    }
    # detail of >50 records
    det = []
    for r in sorted(over50, key=pcvrp, reverse=True):
        pc = r.get('primary_cluster') or {}
        det.append({
            'dt': r.get('datetime_utc'),
            'pc_vrp': round(pcvrp(r), 1),
            'n_pixels': pc.get('n_pixels'),
            't_max_k': r.get('t_max_k'),
            't_bg_k': r.get('t_bg_k'),
            'dT': round((r.get('t_max_k') or 0) - (r.get('t_bg_k') or 0), 1),
            'src': r.get('final_hotspot_source'),
            'test1': r.get('triggered_test1'),
            'n_bt': r.get('diag_n_bt_path'),
            'n_dnti_ctx': r.get('diag_n_dnti_ctx_path'),
            'n_eti': r.get('diag_n_eti_path'),
            'n_nti': r.get('diag_n_nti_path'),
            'n_2nd_pass': r.get('diag_n_second_pass_recapture'),
            'cdist_km': round(pc.get('centroid_dist_km') or 0, 2),
            'vrp_per_px': round(pcvrp(r) / (pc.get('n_pixels') or 1), 2),
        })
    result['big_records'][vol] = det

# ---- Step 3: MIROVA ground truth (CONS + OCR) for MODIS in these vols ----
def read_csv_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding='utf-8', errors='replace') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            rows.append(row)
    return rows

# name variants per A14
NAME_VARIANTS = {
    'PuyehueCordonCaulle': ['Puyehue-Cordon Caulle','PuyehueCordonCaulle','Puyehue'],
    'PlanchonPeteroa': ['PlanchonPeteroa','Planchon-Peteroa','Planchon Peteroa','PlanchonPeteroa'],
    'NevadosDeChillan': ['Nevados de Chillan','NevadosDeChillan','Nevados De Chillan'],
    'Tupungatito': ['Tupungatito'], 'Villarrica': ['Villarrica'], 'Lascar': ['Lascar'],
    'Copahue': ['Copahue'], 'Llaima': ['Llaima'], 'Chaiten': ['Chaiten'],
    'Lastarria': ['Lastarria'], 'Isluga': ['Isluga'],
}

cons = read_csv_rows(os.path.join(ROOT, 'latest_consolidado.csv'))
# OCR: use most recent snapshot
ocr_path = os.path.join(ROOT, 'registro_vrp_consolidado_25_04_2026.csv')
ocr = read_csv_rows(os.path.join(ROOT, '14042026 registro_vrp_ocr.csv'))

def colmatch(rows, keys):
    if not rows: return None
    hdr = rows[0].keys()
    for k in keys:
        for h in hdr:
            if k.lower() == h.lower():
                return h
    return None

cons_vol_col = colmatch(cons, ['Volcan','Volcano','volcan'])
cons_sensor_col = colmatch(cons, ['Sensor','sensor'])
cons_vrp_col = colmatch(cons, ['VRP','vrp','VRP_MW','vrp_mw'])

mirova_modis = {}
if cons and cons_vol_col:
    for vol in TIER_A:
        variants = [v.lower() for v in NAME_VARIANTS.get(vol, [vol])]
        n_modis = 0
        n_modis_vrp = 0
        for row in cons:
            v = (row.get(cons_vol_col) or '').strip().lower()
            if v in variants:
                s = (row.get(cons_sensor_col) or '').upper() if cons_sensor_col else ''
                if 'MODIS' in s:
                    n_modis += 1
                    try:
                        if float((row.get(cons_vrp_col) or '0').replace(',','.')) > 0:
                            n_modis_vrp += 1
                    except: pass
        mirova_modis[vol] = {'cons_modis_rows': n_modis, 'cons_modis_vrp_gt0': n_modis_vrp}

result['mirova_cons'] = {
    'columns': {'vol': cons_vol_col, 'sensor': cons_sensor_col, 'vrp': cons_vrp_col},
    'n_rows_total': len(cons),
    'modis_per_vol': mirova_modis,
    'sensors_seen': sorted(set((r.get(cons_sensor_col) or '').strip() for r in cons)) if cons_sensor_col else [],
}

json.dump(result, open(os.path.join(OUT, 'audit_result.json'), 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print('WROTE audit_result.json')
print(json.dumps(result['per_vol'], indent=2, ensure_ascii=False))
print('--- MIROVA CONS sensors:', result['mirova_cons']['sensors_seen'])
print('--- MIROVA CONS MODIS per vol:', json.dumps(mirova_modis, ensure_ascii=False))
