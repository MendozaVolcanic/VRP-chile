"""82 — Audit Tier A con OSF v2.5 como ground truth (vs OCR consolidado).

Cambio crítico: usa MIROVA OSF v2.5 (~48k refs Tier A) en vez de
Mirova-v1 latest.php scrapeado (~14k refs). Esto resuelve la duda
'Villarrica recall 0%' que era artefacto de data stale (solo 6 refs OCR
vs 5,211 OSF).

Output: reports/osf_v25_tier_a_audit.csv + summary md
"""
import csv, sys, io, json, os
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent
OSF = r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'

# Tier A IDvolc → nombre interno VRP-chile
TIER_A = {
    '355100':'Lascar', '355120':'Lastarria', '357010':'Tupungatito',
    '357120':'Villarrica', '357150':'PuyehueCordonCaulle', '357090':'Copahue',
    '357070':'NevadosDeChillan', '357110':'Llaima', '358041':'Chaiten',
    '357040':'PlanchonPeteroa', '355030':'Isluga',
}

# OSF Satellite codes (sospechado, validar con schema doc)
# 1, 2 = MODIS Terra/Aqua; 3, 4 = VIIRS NPP/NOAA20
SAT_LABEL = {'1':'MODIS_T', '2':'MODIS_A', '3':'VIIRS_SNPP', '4':'VIIRS_N20'}

def parse_osf_ts(s):
    try:
        return datetime.strptime(s, '%d/%m/%Y %H:%M').replace(tzinfo=timezone.utc)
    except: return None

# Stats
total_per_vol = defaultdict(int)
class_per_vol = defaultdict(lambda: defaultdict(int))  # vol -> class -> count
sensor_per_vol = defaultdict(lambda: defaultdict(int))
last_ts = defaultdict(lambda: None)
first_ts = defaultdict(lambda: None)
recent_30d_per_vol = defaultdict(int)
recent_alerta = defaultdict(list)

cutoff = datetime(2026,4,10,tzinfo=timezone.utc)
classes_seen = set()

print(f'Reading OSF v2.5 ({os.path.getsize(OSF)/1e6:.1f} MB)...')
with open(OSF, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        idv = r['IDvolc'].strip()
        if idv not in TIER_A: continue
        vol = TIER_A[idv]
        total_per_vol[vol] += 1
        cls = r.get('class','').strip()
        class_per_vol[vol][cls] += 1
        classes_seen.add(cls)
        sat = SAT_LABEL.get(r.get('Satellite','').strip(), '?')
        sensor_per_vol[vol][sat + '_' + r.get('Resolution','').strip()] += 1
        ts = parse_osf_ts(r['timeUTC'])
        if ts is None: continue
        if last_ts[vol] is None or ts > last_ts[vol]: last_ts[vol] = ts
        if first_ts[vol] is None or ts < first_ts[vol]: first_ts[vol] = ts
        if ts >= cutoff:
            recent_30d_per_vol[vol] += 1
            recent_alerta[vol].append({
                'ts': r['timeUTC'], 'sat': r.get('Satellite',''),
                'res': r.get('Resolution',''), 'vrp': r.get('VRP',''),
                'dist': r.get('Max_Dist',''), 'class': cls,
            })

print()
print('=== OSF v2.5 — refs Tier A por volcán ===')
print(f'{"Volcán":<22} {"Total":>8} {"Primer":<19} {"Último":<19} {"Last 30d":>9}')
print('-'*80)
for vol in sorted(TIER_A.values()):
    n = total_per_vol[vol]
    ft = first_ts[vol].strftime('%Y-%m-%d %H:%M') if first_ts[vol] else '—'
    lt = last_ts[vol].strftime('%Y-%m-%d %H:%M') if last_ts[vol] else '—'
    r30 = recent_30d_per_vol[vol]
    print(f'{vol:<22} {n:>8} {ft:<19} {lt:<19} {r30:>9}')

print()
print('=== Class distribution (Tier A) ===')
print(f'Classes únicas: {sorted(classes_seen)}')
print(f'{"Volcán":<22} ' + ' '.join(f'{c:>6}' for c in sorted(classes_seen)))
for vol in sorted(TIER_A.values()):
    row = ' '.join(f'{class_per_vol[vol].get(c,0):>6}' for c in sorted(classes_seen))
    print(f'{vol:<22} {row}')

print()
print('=== Sensor distribution (top per volcán) ===')
for vol in sorted(TIER_A.values()):
    sensors = sorted(sensor_per_vol[vol].items(), key=lambda x: -x[1])
    if not sensors: continue
    s = ', '.join(f'{k}={v}' for k,v in sensors[:5])
    print(f'  {vol}: {s}')

print()
print('=== Recent activity (últimos 30d) ===')
for vol, lst in sorted(recent_alerta.items()):
    print(f'  {vol}: {len(lst)} eventos')
    for e in lst[:5]:
        print(f'    {e["ts"]} sat={e["sat"]} res={e["res"]} VRP={e["vrp"]} dist={e["dist"]}km class={e["class"]}')

# Cross-comparison vs OCR consolidado
print()
print('=== Comparación OSF v2.5 vs OCR consolidado (Mirova-v1) ===')
import urllib.request
print('  bajando OCR consolidado...')
urllib.request.urlretrieve('https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv', '/tmp/ocr.csv')
ocr_per_vol = defaultdict(int)
VOL_MAP_OCR = {'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
               'PlanchonPeteroa':'PlanchonPeteroa','NevadosDeChillan':'Nevados de Chillan',
               'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
               'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Chaiten':'Chaitén'}
with open('/tmp/ocr.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA': continue
        for k,v in VOL_MAP_OCR.items():
            if r['Volcan'].strip() == v:
                ocr_per_vol[k] += 1
                break

print(f'{"Volcán":<22} {"OSF v2.5":>10} {"OCR cons.":>10} {"Ratio"}')
for vol in sorted(TIER_A.values()):
    o = total_per_vol[vol]
    oc = ocr_per_vol.get(vol, 0)
    ratio = f'{o/oc:.1f}x' if oc else '∞'
    print(f'{vol:<22} {o:>10} {oc:>10} {ratio:>10}')

# Save filtered OSF Tier A
out = REPO / 'reports' / 'osf_v25_tier_a.csv'
out.parent.mkdir(exist_ok=True)
print(f'\\nWriting {out}...')
with open(OSF, encoding='utf-8') as fin, open(out, 'w', encoding='utf-8', newline='') as fout:
    reader = csv.DictReader(fin)
    writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
    writer.writeheader()
    n = 0
    for r in reader:
        if r['IDvolc'].strip() in TIER_A:
            writer.writerow(r); n += 1
    print(f'  wrote {n} filas Tier A')
