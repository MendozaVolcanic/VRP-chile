"""
F52 extended — Tupungatito + PCC audit (read-only).

Hipotesis arquitectural F52-extended (sesion S77):
  3 volcanes Tier A con cuerpos de agua al pie del crater sobre-/sub-estiman vs MIROVA:
    - Tupungatito ratio mediano ~30x (sobre-estima MAS grave)
    - Villarrica   ratio mediano ~10.9x (subagente paralelo)
    - PCC          ratio mediano ~0.48x (sub-estima, patron opuesto)
  Otros 8 Tier A: banda 0.5-2.0 (sin agua o despreciable).

Este script no modifica nada. Match nearest-neighbor temporal +-30 min, sensor compatible,
sobre la ventana >= 2026-05-17 (ultimos 7 dias antes del audit).

Salida: experiments/147_f52_tupungatito_pcc/audit.json + impresion legible.
"""
from __future__ import annotations
import json, math, sys, io
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
CSV  = ROOT / 'data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv'

# --- Configuracion volcanes auditados ---
VOLCANOES = {
    'Tupungatito': {
        'json':       ROOT/'data/mirova_equivalent/Tupungatito.json',
        'csv_name':   'Tupungatito',
        'vent_lat':   -33.389044, 'vent_lon': -69.826374,
        'inner_km':   7,
        'crater_lake_lat': -33.4269, 'crater_lake_lon': -69.8004,
        'crater_lake_radius_km': 1.0,
    },
    'PuyehueCordonCaulle': {
        'json':       ROOT/'data/mirova_equivalent/PuyehueCordonCaulle.json',
        'csv_name':   'Puyehue-Cordon Caulle',
        'vent_lat':   -40.525499, 'vent_lon': -72.146137,
        'mirova_center_lat': -40.582, 'mirova_center_lon': -72.131,
        'inner_km':   20,
    },
}

WINDOW_START = datetime(2026, 5, 17)
MATCH_TOL_MIN = 30

# ---------- helpers ----------
def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    R=6371.0
    p1,p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def bearing_deg(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return None
    p1,p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2-lon1)
    y = math.sin(dl)*math.cos(p2)
    x = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360

def compass(b):
    if b is None: return None
    dirs=['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
    return dirs[int((b/22.5)+0.5)%16]

def parse_dt(s):
    try: return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except Exception:
        try: return datetime.strptime(s, '%Y-%m-%d %H:%M')
        except Exception: return None

def sensor_norm(s):
    s=(s or '').upper()
    if 'MODIS' in s: return 'MODIS'
    if 'VIIRS' in s or 'I-BAND' in s or 'M-BAND' in s or 'JPSS' in s or 'SUOMI' in s: return 'VIIRS'
    return s

# ---------- load MIROVA ----------
import csv as _csv
mirova_rows = []
with open(CSV, 'r', encoding='utf-8', errors='replace') as f:
    rdr = _csv.DictReader(f)
    for r in rdr:
        dt = parse_dt(r.get('Fecha_Satelite_UTC',''))
        if dt is None or dt < WINDOW_START: continue
        try: vrp = float(r.get('VRP_MW') or 0)
        except: vrp = 0
        try: dist = float(r.get('Distancia_km') or 0)
        except: dist = 0
        mirova_rows.append({
            'volcan': r['Volcan'].strip(),
            'sensor': sensor_norm(r.get('Sensor','')),
            'dt': dt,
            'vrp_mw': vrp,
            'dist_km_reported': dist,
            'clasificacion': r.get('Clasificacion Mirova',''),
            'tipo': r.get('Tipo_Registro',''),
        })

print(f'MIROVA refs window>={WINDOW_START.date()}: {len(mirova_rows)} total')

# ---------- audit per volcano ----------
results = {}
for vname, cfg in VOLCANOES.items():
    print(f'\n=== {vname} ===')
    with open(cfg['json'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    recs = data.get('records', data) if isinstance(data, dict) else data
    ours = []
    for r in recs:
        dt = parse_dt(r.get('datetime_utc',''))
        if dt is None or dt < WINDOW_START: continue
        ours.append({
            'dt': dt,
            'sensor': sensor_norm(r.get('sensor','')),
            'vrp_mw': r.get('vrp_mw') or 0,
            'vrp_mir_mw': r.get('vrp_mir_mw'),
            'n_anom_px': r.get('n_anomalous_pixels',0),
            'n_clusters': r.get('n_hotspots_clustered',0),
            'final_hotspot_lat': r.get('final_hotspot_lat'),
            'final_hotspot_lon': r.get('final_hotspot_lon'),
            'final_hotspot_dist_km': r.get('final_hotspot_dist_km'),
            'final_hotspot_source': r.get('final_hotspot_source'),
            'distance_class': r.get('distance_class'),
            'hotspot_lat': r.get('hotspot_lat'),
            'hotspot_lon': r.get('hotspot_lon'),
            'hotspot_dist_km': r.get('hotspot_dist_km'),
            'vent_hotspot_dist_km': r.get('vent_hotspot_dist_km'),
            'n_vent_pixels': r.get('n_vent_pixels',0),
            't_max_k': r.get('t_max_k'),
            't_bg_k': r.get('t_bg_k'),
            'diag_sigma_bg_k': r.get('diag_sigma_bg_k'),
            'primary_cluster': r.get('primary_cluster') or {},
            'triggered_test1': r.get('triggered_test1', False),
        })
    print(f'  ours window: {len(ours)} records')

    refs = [m for m in mirova_rows if m['volcan'] == cfg['csv_name']]
    refs_pos = [m for m in refs if m['vrp_mw'] > 0]
    print(f'  mirova refs window: {len(refs)} total / {len(refs_pos)} positive (vrp_mw>0)')

    # Match nearest temporal +-30 min same sensor
    matches = []
    used_ours = set()
    for m in refs:
        candidates = [(i,o) for i,o in enumerate(ours) if i not in used_ours and o['sensor']==m['sensor']
                      and abs((o['dt']-m['dt']).total_seconds()) <= MATCH_TOL_MIN*60]
        if not candidates:
            matches.append({'mirova': m, 'ours': None}); continue
        candidates.sort(key=lambda x: abs((x[1]['dt']-m['dt']).total_seconds()))
        i,o = candidates[0]
        used_ours.add(i)
        matches.append({'mirova': m, 'ours': o})

    unmatched_ours = [o for i,o in enumerate(ours) if i not in used_ours]
    matched_pairs  = [p for p in matches if p['ours'] is not None]
    mirova_only    = [p for p in matches if p['ours'] is None]

    # Filter matched pairs to those where MIROVA positive (most informative for ratio)
    pairs_pos = [p for p in matched_pairs if p['mirova']['vrp_mw'] > 0]
    pairs_both_pos = [p for p in pairs_pos if (p['ours']['vrp_mw'] or 0) > 0]

    ratios = []
    for p in pairs_both_pos:
        r = (p['ours']['vrp_mw'] or 0) / p['mirova']['vrp_mw']
        ratios.append(r)
    ratio_med = median(ratios) if ratios else None

    # Bearing analysis of OUR final_hotspot vs vent — where do our detections go?
    bearings_matched = []
    for p in matched_pairs:
        o = p['ours']
        if o.get('final_hotspot_lat') is None: continue
        b = bearing_deg(cfg['vent_lat'], cfg['vent_lon'], o['final_hotspot_lat'], o['final_hotspot_lon'])
        d = haversine(cfg['vent_lat'], cfg['vent_lon'], o['final_hotspot_lat'], o['final_hotspot_lon'])
        bearings_matched.append((b, compass(b), d, o['dt'].isoformat()))

    bearings_unmatched = []
    for o in unmatched_ours:
        if o.get('final_hotspot_lat') is None: continue
        b = bearing_deg(cfg['vent_lat'], cfg['vent_lon'], o['final_hotspot_lat'], o['final_hotspot_lon'])
        d = haversine(cfg['vent_lat'], cfg['vent_lon'], o['final_hotspot_lat'], o['final_hotspot_lon'])
        bearings_unmatched.append((b, compass(b), d, o['dt'].isoformat(), o.get('vrp_mw')))

    # For Tupungatito: how many fall INSIDE crater_lake whitelist circle?
    on_lake = []
    if 'crater_lake_lat' in cfg:
        for o in ours:
            if o.get('final_hotspot_lat') is None: continue
            d = haversine(cfg['crater_lake_lat'], cfg['crater_lake_lon'],
                          o['final_hotspot_lat'], o['final_hotspot_lon'])
            if d is not None and d <= cfg['crater_lake_radius_km']:
                on_lake.append({'dt': o['dt'].isoformat(), 'dist_to_lake_km': round(d,2),
                                'vrp_mw': o['vrp_mw'], 'source': o.get('final_hotspot_source')})

    # Cluster size distribution (PCC focus)
    n_pix_dist = {}
    bt_max_distribution = []
    for o in ours:
        pc = o.get('primary_cluster') or {}
        npx = pc.get('n_pixels', 0)
        n_pix_dist[npx] = n_pix_dist.get(npx,0)+1
        if o.get('t_max_k'): bt_max_distribution.append(o['t_max_k'])

    # Summary
    summary = {
        'volcano': vname,
        'window_start': WINDOW_START.isoformat(),
        'ours_records': len(ours),
        'mirova_refs_total': len(refs),
        'mirova_refs_positive': len(refs_pos),
        'matched_pairs': len(matched_pairs),
        'matched_pairs_mirova_pos': len(pairs_pos),
        'matched_pairs_both_pos': len(pairs_both_pos),
        'unmatched_ours': len(unmatched_ours),
        'mirova_only_unmatched': len(mirova_only),
        'ratio_median': ratio_med,
        'ratio_p25': sorted(ratios)[len(ratios)//4] if len(ratios)>=4 else None,
        'ratio_p75': sorted(ratios)[3*len(ratios)//4] if len(ratios)>=4 else None,
        'on_crater_lake_count': len(on_lake) if 'crater_lake_lat' in cfg else None,
        'cluster_n_pixels_distribution_top5': sorted(n_pix_dist.items(), key=lambda x:-x[1])[:5],
        'bt_max_k_median': round(median(bt_max_distribution),2) if bt_max_distribution else None,
        'bt_max_k_max': round(max(bt_max_distribution),2) if bt_max_distribution else None,
    }
    print(f'  matched pairs: {len(matched_pairs)} (both pos: {len(pairs_both_pos)})')
    print(f'  unmatched OURS: {len(unmatched_ours)} (we detected, MIROVA did NOT)')
    print(f'  MIROVA-only unmatched: {len(mirova_only)} (MIROVA detected, we MISSED -> FN)')
    print(f'  ratio mediano (both pos): {ratio_med}')
    if 'crater_lake_lat' in cfg:
        print(f'  records con final_hotspot dentro crater_lake (1km): {len(on_lake)} / {len(ours)}')
    print(f'  bearing matched (top sample):')
    for b,c,d,t in bearings_matched[:6]:
        print(f'    {t}  bearing={b:.0f} ({c}) dist={d:.2f} km')
    print(f'  bearing unmatched-OURS (top sample):')
    for b,c,d,t,vrp in bearings_unmatched[:6]:
        print(f'    {t}  bearing={b:.0f} ({c}) dist={d:.2f} km vrp={vrp}')

    results[vname] = {
        'summary': summary,
        'bearings_matched': [{'bearing': b, 'compass': c, 'dist_km': d, 'dt': t} for b,c,d,t in bearings_matched],
        'bearings_unmatched_ours': [{'bearing': b, 'compass': c, 'dist_km': d, 'dt': t, 'vrp_mw': v}
                                    for b,c,d,t,v in bearings_unmatched],
        'on_crater_lake_sample': on_lake[:10],
        'cluster_n_pixels_distribution': sorted(n_pix_dist.items()),
    }

# ---------- save ----------
out_path = Path(__file__).parent / 'audit.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, default=str, ensure_ascii=False)
print(f'\nSaved -> {out_path}')
