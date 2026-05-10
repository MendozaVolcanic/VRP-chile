"""80 — H8 A/B comparison restricted to 7d window + common volcanoes."""
import json,sys,io,csv,urllib.request,statistics
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent
VOL_MAP = {'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
           'PlanchonPeteroa':'PlanchonPeteroa','NevadosDeChillan':'Nevados de Chillan',
           'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
           'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Chaiten':'Chaitén'}
rev_map = {v:k for k,v in VOL_MAP.items()}

CONS = '/tmp/cons.csv'
urllib.request.urlretrieve('https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv', CONS)

WIN_START = '2026-05-03'
WIN_END = '2026-05-09 23:59:59'

alertas = {}
with open(CONS, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        v = r['Volcan'].strip()
        v_int = rev_map.get(v)
        if not v_int: continue
        ts = r['Fecha_Satelite_UTC'].strip()
        if ts < WIN_START or ts > WIN_END: continue
        if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA': continue
        alertas[(v_int, r['Sensor'].strip(), ts[:16])] = {
            'vrp': float(r.get('VRP_MW',0) or 0),
            'dist': float(r.get('Distancia_km',0) or 0),
        }

print(f'Alertas window 7d: {len(alertas)}')

def load_recs(d):
    out = {}
    for jf in Path(d).glob('*.json'):
        with open(jf) as f: data = json.load(f)
        recs = data if isinstance(data,list) else data.get('records',[])
        for r in recs:
            dt = r.get('datetime_utc','')
            if dt < WIN_START or dt > WIN_END: continue
            out[(jf.stem, r.get('sensor',''), dt)] = r
    return out

baseline = load_recs(REPO/'data'/'mirova_equivalent')
h8_off = load_recs(REPO/'data'/'_h8_pixel_filter_disabled')
h8_on = load_recs(REPO/'data'/'_h8_pixel_filter_enabled')

vols_off = {p.stem for p in (REPO/'data'/'_h8_pixel_filter_disabled').glob('*.json')}
vols_on = {p.stem for p in (REPO/'data'/'_h8_pixel_filter_enabled').glob('*.json')}
common = vols_off & vols_on
print(f'common vols ({len(common)}): {sorted(common)}')

def sens_to_cons(s):
    if 'MODIS' in s: return 'MODIS'
    if '_750' in s: return 'VIIRS'
    return 'VIIRS375'

def measure(dataset, label):
    tp = fn = 0
    ratios = []
    for (vol, sens_cons, ts_min), info in alertas.items():
        if vol not in common: continue
        found = False
        for k, r in dataset.items():
            if k[0] != vol: continue
            if k[2][:16] != ts_min: continue
            if sens_to_cons(k[1]) != sens_cons: continue
            vrp = r.get('vrp_mw',0) or 0
            if vrp > 0:
                found = True
                if info['vrp'] > 0: ratios.append(vrp/info['vrp'])
                break
        if found: tp += 1
        else: fn += 1
    n = tp+fn
    rec = 100*tp/n if n else 0
    med = statistics.median(ratios) if ratios else 0
    mn = statistics.mean(ratios) if ratios else 0
    print(f'{label:<14} recall={rec:>5.1f}% TP={tp:>3} FN={fn:>3}  ratio_med={med:>6.2f}x ratio_mean={mn:>6.2f}x  (n_ratios={len(ratios)})')

# Filter alertas to common vols only
common_alertas = {k:v for k,v in alertas.items() if k[0] in common}
print(f'\\nAlertas en common vols: {len(common_alertas)}')

print(f'\\n=== APPLES-TO-APPLES (7d window, vols comunes) ===')
measure(baseline, 'baseline')
measure(h8_off, 'h8_off')
measure(h8_on, 'h8_on')

# Volcán-by-volcán
print('\\n=== Per volcano breakdown (h8_off vs h8_on) ===')
for vol in sorted(common):
    n_alerta = sum(1 for k in common_alertas if k[0]==vol)
    if n_alerta == 0:
        continue
    tp_off = tp_on = 0
    for (v, sens_cons, ts_min) in common_alertas:
        if v != vol: continue
        for k,r in h8_off.items():
            if k[0]==vol and k[2][:16]==ts_min and sens_to_cons(k[1])==sens_cons and (r.get('vrp_mw',0) or 0) > 0:
                tp_off += 1; break
        for k,r in h8_on.items():
            if k[0]==vol and k[2][:16]==ts_min and sens_to_cons(k[1])==sens_cons and (r.get('vrp_mw',0) or 0) > 0:
                tp_on += 1; break
    print(f'  {vol:<22} alertas={n_alerta:>3}  off TP={tp_off:>3}  on TP={tp_on:>3}  delta={tp_on-tp_off:+d}')
