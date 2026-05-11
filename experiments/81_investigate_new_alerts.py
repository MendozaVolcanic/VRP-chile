"""81 — Investigar 14 alertas nuevas MIROVA 10-11 mayo 2026.

Para cada alerta, buscar:
1. ¿VRP-chile detectó algo (con cualquier vrp_mw)?
2. Si sí, ¿qué reporta primary_cluster?
3. ¿Pattern bug H8 (discarded pixels)?
4. ¿Pattern bug D8 (cluster equivocado)?
5. ¿Tenemos TIF deterministic en mirova-tif-archive?

Output: reports/new_alerts_audit.csv + summary.
"""
import json, csv, sys, io, urllib.request, math
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = Path(__file__).resolve().parent.parent
ARCHIVE = REPO.parent.parent.parent.parent / 'mirova-tif-archive' / 'index.csv'

VOL_MAP = {'Isluga':'Isluga','Lascar':'Lascar','Lastarria':'Lastarria','Tupungatito':'Tupungatito',
           'PlanchonPeteroa':'PlanchonPeteroa','NevadosDeChillan':'Nevados de Chillan',
           'Copahue':'Copahue','Llaima':'Llaima','Villarrica':'Villarrica',
           'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Chaiten':'Chaitén'}
rev_map = {v:k for k,v in VOL_MAP.items()}

# Load consolidado, filter alertas 10-11 may
urllib.request.urlretrieve('https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv', '/tmp/c.csv')
alertas = []
with open('/tmp/c.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        v_int = rev_map.get(r['Volcan'].strip())
        if not v_int: continue
        ts = r['Fecha_Satelite_UTC'].strip()
        if ts < '2026-05-10': continue
        if r['Tipo_Registro'].strip() != 'ALERTA_TERMICA': continue
        alertas.append({
            'vol': v_int, 'sensor_cons': r['Sensor'].strip(),
            'ts': ts, 'vrp': float(r.get('VRP_MW',0) or 0),
            'dist': float(r.get('Distancia_km',0) or 0),
        })
print(f'ALERTAS 10-11 may: {len(alertas)}')

# Load VRP-chile records
def load_recs(d):
    out = {}
    for jf in Path(d).glob('*.json'):
        with open(jf) as f: data = json.load(f)
        recs = data if isinstance(data, list) else data.get('records', [])
        for r in recs:
            dt = r.get('datetime_utc', '')
            if dt < '2026-05-10': continue
            out[(jf.stem, r.get('sensor',''), dt)] = r
    return out

baseline = load_recs(REPO/'data'/'mirova_equivalent')
print(f'records mirova_equivalent 10-11 may: {len(baseline)}')

# Load archive
archive = {}
if ARCHIVE.exists():
    with open(ARCHIVE, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if not r.get('acquisition_utc'): continue
            archive[(r['volcano'], r['sensor'], r['acquisition_utc'])] = r
print(f'archive deterministic TIFs: {len(archive)}')

def sens_cons_to_vrp(sc):
    if sc == 'MODIS': return ['MODIS_AQUA', 'MODIS_TERRA']
    if sc == 'VIIRS': return ['VIIRS_NOAA20_750', 'VIIRS_NOAA21_750', 'VIIRS_SNPP_750']
    if sc == 'VIIRS375': return ['VIIRS_NOAA20', 'VIIRS_NOAA21', 'VIIRS_SNPP']
    return []

def sens_cons_to_archive(sc):
    return {'MODIS':'MODIS', 'VIIRS':'VIIRS750', 'VIIRS375':'VIIRS375'}.get(sc, sc)

rows = []
for a in alertas:
    vrp_match = None; vrp_sensor = None
    for sens_vrp in sens_cons_to_vrp(a['sensor_cons']):
        for k, r in baseline.items():
            if k[0]==a['vol'] and k[1]==sens_vrp and k[2][:16]==a['ts'][:16]:
                vrp_match = r; vrp_sensor = sens_vrp
                break
        if vrp_match: break
    # Archive lookup
    sens_arch = sens_cons_to_archive(a['sensor_cons'])
    acq_iso_candidates = [
        a['ts'][:19].replace(' ','T') + '+00:00',
        a['ts'][:19].replace(' ','T'),
    ]
    arch_match = None
    for acq in acq_iso_candidates:
        arch_match = archive.get((a['vol'], sens_arch, acq))
        if arch_match: break

    if vrp_match:
        pc = vrp_match.get('primary_cluster') or {}
        row = {
            'vol': a['vol'], 'ts': a['ts'], 'sens_M': a['sensor_cons'], 'sens_V': vrp_sensor,
            'mirova_vrp': a['vrp'], 'mirova_dist': a['dist'],
            'vrp_chile_vrp_mw': vrp_match.get('vrp_mw',0),
            'vrp_chile_vrp_mir': vrp_match.get('vrp_mir_mw',0),
            'pc_n': pc.get('n_pixels',0), 'pc_vrp': pc.get('vrp_mw',0),
            'pc_dist': pc.get('centroid_dist_km'),
            'class': vrp_match.get('distance_class',''),
            'discarded_reason': vrp_match.get('discarded_reason',''),
            'n_disc_pix': len(vrp_match.get('discarded_anomaly_pixels',[])),
            'TIF_in_archive': 'Yes' if arch_match else 'No',
        }
    else:
        row = {'vol': a['vol'], 'ts': a['ts'], 'sens_M': a['sensor_cons'], 'sens_V': '',
               'mirova_vrp': a['vrp'], 'mirova_dist': a['dist'],
               'vrp_chile_vrp_mw': 'NO MATCH', 'vrp_chile_vrp_mir': '',
               'pc_n': '', 'pc_vrp': '', 'pc_dist': '', 'class': '',
               'discarded_reason': '', 'n_disc_pix': '',
               'TIF_in_archive': 'Yes' if arch_match else 'No'}
    rows.append(row)

# Print table
print()
print(f'{"vol":<22} {"ts":<18} {"sens":<10} {"M.vrp":>6} {"M.dist":>7} {"V.vrp":>7} {"V.vrp_mir":>9} {"pc_n":>5} {"pc_vrp":>7} {"pc_dist":>8} {"class":<7} {"disc":<28} {"TIF"}')
print('-' * 160)
for r in rows:
    pc_dist = f"{r['pc_dist']:.2f}" if isinstance(r['pc_dist'], (int,float)) else str(r['pc_dist'])
    print(f"{r['vol']:<22} {r['ts']:<18} {r['sens_M']:<10} {r['mirova_vrp']:>6.2f} {r['mirova_dist']:>7.2f} "
          f"{str(r['vrp_chile_vrp_mw']):>7} {str(r['vrp_chile_vrp_mir']):>9} {str(r['pc_n']):>5} "
          f"{str(r['pc_vrp']):>7} {pc_dist:>8} {r['class']:<7} {r['discarded_reason']:<28} {r['TIF_in_archive']}")

# Summary
print()
n_match = sum(1 for r in rows if r['vrp_chile_vrp_mw'] != 'NO MATCH')
n_tp = sum(1 for r in rows if isinstance(r['vrp_chile_vrp_mw'], (int,float)) and r['vrp_chile_vrp_mw'] > 0)
n_fn = sum(1 for r in rows if r['vrp_chile_vrp_mw'] == 0 or r['vrp_chile_vrp_mw'] == 'NO MATCH')
n_disc = sum(1 for r in rows if r['discarded_reason'])
n_tif = sum(1 for r in rows if r['TIF_in_archive'] == 'Yes')
print(f'SUMMARY: {len(rows)} alertas')
print(f'  VRP-chile match: {n_match}')
print(f'  VRP-chile TP (vrp>0): {n_tp}')
print(f'  VRP-chile FN (vrp=0 o sin match): {n_fn}')
print(f'  Records con discarded_reason: {n_disc} (bug H8 active)')
print(f'  TIFs en mirova-tif-archive: {n_tif}/{len(rows)}')

# Write CSV
reports = REPO/'reports'
reports.mkdir(exist_ok=True)
out = reports/'new_alerts_audit.csv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f'\\nCSV: {out}')
