# -*- coding: utf-8 -*-
import json, os, io, sys
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIER_A = ['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima',
          'NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito','Villarrica']

def load(p):
    if not os.path.exists(p): return []
    d = json.load(open(p, encoding='utf-8')); return d.get('records', d) if isinstance(d,dict) else d

L = []
def out(s=''): L.append(s)

# (1) Lastarria — distribución de distancias MIROVA: ¿reporta algo ~12km (cluster 17)?
out('=== (1) LASTARRIA — distancias que reporta MIROVA ===')
mir = load(os.path.join(BASE,'data','mirova','Lastarria.json'))
dists = [r.get('distancia_km') for r in mir if r.get('distancia_km') is not None]
out(f'  n refs MIROVA Lastarria: {len(mir)}  con distancia: {len(dists)}')
if dists:
    out(f'  dist min/med/max: {min(dists):.2f} / {sorted(dists)[len(dists)//2]:.2f} / {max(dists):.2f} km')
    far = [d for d in dists if d > 8]
    out(f'  refs MIROVA con dist >8km: {len(far)}  (valores: {sorted(far, reverse=True)[:10]})')
    out(f'  refs MIROVA con dist >11km: {len([d for d in dists if d>11])}')

# (2) firma de fechas recurrentes: high record.vrp_mw>500 por fecha, cuántos volcanes
out('')
out('=== (2) FIRMA ARTEFACTO — fechas con record.vrp_mw>500, # de volcanes que pican ===')
date_vol = defaultdict(set)
for vol in TIER_A:
    recs = load(os.path.join(BASE,'data','mirova_equivalent', vol+'.json'))
    for r in recs:
        if (r.get('vrp_mw') or 0) > 500:
            date_vol[(r.get('datetime_utc') or '')[:10]].add(vol)
multi = sorted(((len(v), d, sorted(v)) for d,v in date_vol.items()), reverse=True)
for n, d, vols in multi[:12]:
    out(f'  {d}: {n} volcanes  {vols}')

# (3) cross-check pc.vrp_mw alto vs MIROVA mismo día/sensor
out('')
out('=== (3) ¿MIROVA reportó algo los días de pc.vrp_mw alto? ===')
def sens_bucket(s):
    s=(s or '')
    if s.startswith('MODIS'): return 'MODIS'
    if '750' in s: return 'VIIRS750'
    if s.startswith('VIIRS'): return 'VIIRS375'
    return '?'
checks = [('PuyehueCordonCaulle','2026-04-16'),('PuyehueCordonCaulle','2026-05-04'),
          ('Chaiten','2026-05-04'),('NevadosDeChillan','2026-03-13'),
          ('PlanchonPeteroa','2026-04-19'),('Villarrica','2026-01-31')]
for vol, day in checks:
    ours = load(os.path.join(BASE,'data','mirova_equivalent', vol+'.json'))
    mir  = load(os.path.join(BASE,'data','mirova', vol+'.json'))
    o_hi = [r for r in ours if (r.get('datetime_utc') or '')[:10]==day and ((r.get('primary_cluster') or {}).get('vrp_mw') or 0)>100]
    m_day = [r for r in mir if (r.get('datetime_utc') or '')[:10]==day]
    out(f'  {vol} {day}:')
    for r in o_hi[:3]:
        pc=r.get('primary_cluster') or {}
        out(f'    OURS  {r.get("datetime_utc")} {r.get("sensor"):18s} pc={pc.get("vrp_mw"):.1f}MW dist={pc.get("centroid_dist_km")} npix={pc.get("n_pixels")} dc={r.get("distance_class")}')
    if m_day:
        for r in m_day[:4]:
            out(f'    MIROVA {r.get("datetime_utc")} {str(r.get("sensor")):10s} VRP={r.get("VRP_MW")}MW dist={r.get("distancia_km")} clas={r.get("clasificacion")}')
    else:
        out(f'    MIROVA: SIN reporte ese día')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cross_mirova.txt'),'w',encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
