# Sonda del verificador S158 (movida desde _tmp/verif/). Correr desde la raíz del worktree; espera el JSON C0 en _tmp/Tupungatito_pre883.json (git show 8471add46^:data/mirova_equivalent/Tupungatito.json).
import json, math, statistics as st, sys, os
from collections import defaultdict
sys.path.insert(0,'.')
os.environ.setdefault("VRP_PROFILE","mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK
from pipeline import process_viirs as pv
LAM,KW,AREA=pv.I04_LAMBDA,pv.WOOSTER_COEFF,pv.NADIR_PIXEL_AREA_M2
L=lambda t: C1_PLANCK/(LAM**5*(math.exp(C2_PLANCK/(LAM*t))-1))
T=lambda l: C2_PLANCK/(LAM*math.log(1+C1_PLANCK/(LAM**5*l)))
pre=json.load(open('_tmp/Tupungatito_pre883.json',encoding='utf-8'))['records']
post={(r['sensor'],r['datetime_utc']):r for r in json.load(open('data/mirova_equivalent/Tupungatito.json',encoding='utf-8'))['records']}
c0=[r for r in pre if not (r.get('regimen') or {}).get('codigo_sha') and r['sensor'].startswith('VIIRS_') and not r['sensor'].endswith('750')]
for fu in ('test1_roi','ctx_cluster'):
    g=defaultdict(list)
    for r in c0:
        if r.get('final_hotspot_source')!=fu or not r.get('t_bg_k'): continue
        pix=[p for p in (r.get('anomaly_pixels') or []) if p.get('dist_km') is not None and p['dist_km']<=7 and p['vrp_mw']>0]
        ts=[T(L(p['bt_k'])-p['vrp_mw']*1e6/(KW*AREA)) for p in pix if L(p['bt_k'])-p['vrp_mw']*1e6/(KW*AREA)>0]
        if not ts: continue
        z=r.get('sensor_zenith_deg'); z=z if z is not None else (post.get((r['sensor'],r['datetime_utc'])) or {}).get('sensor_zenith_deg')
        if z is None: continue
        per='2025' if r['datetime_utc']<'2026' else ('2026<06-07' if r['datetime_utc']<'2026-06-07' else '2026>=06-07')
        b='<30' if z<30 else ('30-50' if z<50 else '>=50')
        g[(per,b)].append(r['t_bg_k']-st.median(ts))
    print('==',fu)
    for k in sorted(g): print('  ',k,'n',len(g[k]),'mediana %.2f'%st.median(g[k]),'p10 %.2f p90 %.2f'%(sorted(g[k])[len(g[k])//10],sorted(g[k])[9*len(g[k])//10]))
