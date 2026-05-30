# -*- coding: utf-8 -*-
"""S90 audit — buscar records con VRP anómalamente alto (cientos/miles MW) en los
11 Tier A. Distingue record.vrp_mw (suma scene-wide) de pc.vrp_mw (cluster summit,
= lo que MIROVA reporta, regla A10). Compara contra MIROVA ref si existe."""
import json, os, glob, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIER_A = ['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima',
          'NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle',
          'Tupungatito','Villarrica']

def load(path):
    if not os.path.exists(path): return None
    d = json.load(open(path, encoding='utf-8'))
    return d.get('records', d) if isinstance(d, dict) else d

lines = []
def out(s=''): lines.append(s)

for vol in TIER_A:
    recs = load(os.path.join(BASE,'data','mirova_equivalent', vol+'.json')) or []
    if not recs:
        out(f'### {vol}: SIN DATA'); continue
    # extremos
    def gv(r): return r.get('vrp_mw') or 0
    def gpc(r):
        pc = r.get('primary_cluster') or {}
        return pc.get('vrp_mw') or 0
    by_rec = sorted(recs, key=gv, reverse=True)
    by_pc  = sorted(recs, key=gpc, reverse=True)
    n_rec_100 = sum(1 for r in recs if gv(r) > 100)
    n_rec_500 = sum(1 for r in recs if gv(r) > 500)
    n_pc_100  = sum(1 for r in recs if gpc(r) > 100)
    n_pc_500  = sum(1 for r in recs if gpc(r) > 500)
    out(f'### {vol}  (n={len(recs)})')
    out(f'  record.vrp_mw  >100MW: {n_rec_100:4d}   >500MW: {n_rec_500:4d}   max: {gv(by_rec[0]):.1f}')
    out(f'  pc.vrp_mw      >100MW: {n_pc_100:4d}   >500MW: {n_pc_500:4d}   max: {gpc(by_pc[0]):.1f}')
    out('  -- TOP 5 por record.vrp_mw (suma scene) --')
    for r in by_rec[:5]:
        pc = r.get('primary_cluster') or {}
        out(f'    {r.get("datetime_utc","?"):16s} {r.get("sensor","?"):20s} '
            f'rec={gv(r):9.2f}  pc={gpc(r):8.2f}  '
            f'dist_class={r.get("distance_class","?"):7s} geo={pc.get("geo_class")} '
            f'npix={r.get("n_anomalous_pixels")} pc_npix={pc.get("n_pixels")} '
            f'pc_dist={pc.get("centroid_dist_km")}')
    out('  -- TOP 3 por pc.vrp_mw (cluster=MIROVA-equiv) --')
    for r in by_pc[:3]:
        pc = r.get('primary_cluster') or {}
        out(f'    {r.get("datetime_utc","?"):16s} {r.get("sensor","?"):20s} '
            f'pc={gpc(r):9.2f}  rec={gv(r):8.2f}  '
            f'dist_class={r.get("distance_class","?"):7s} geo={pc.get("geo_class")} '
            f'pc_dist={pc.get("centroid_dist_km")}')
    out('')

open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'audit_high_vrp.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines))
