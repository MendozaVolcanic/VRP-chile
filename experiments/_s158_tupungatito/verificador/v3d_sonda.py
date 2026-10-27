# Sonda del verificador S158 (movida desde _tmp/verif/). Correr desde la raíz del worktree; espera el JSON C0 en _tmp/Tupungatito_pre883.json (git show 8471add46^:data/mirova_equivalent/Tupungatito.json).
import json, math, statistics as st, sys, os
from collections import Counter
sys.path.insert(0,'.')
os.environ.setdefault("VRP_PROFILE","mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK
from pipeline import process_viirs as pv
LAM,KW,AREA=pv.I04_LAMBDA,pv.WOOSTER_COEFF,pv.NADIR_PIXEL_AREA_M2
L=lambda t: C1_PLANCK/(LAM**5*(math.exp(C2_PLANCK/(LAM*t))-1))
T=lambda l: C2_PLANCK/(LAM*math.log(1+C1_PLANCK/(LAM**5*l)))
pre=json.load(open('_tmp/Tupungatito_pre883.json',encoding='utf-8'))['records']
c=Counter()
for r in pre:
    if (r.get('regimen') or {}).get('codigo_sha') or r['sensor'] not in ('VIIRS_SNPP','VIIRS_NOAA20','VIIRS_NOAA21') or r.get('final_hotspot_source')!='ctx_cluster' or not r.get('t_bg_k'): continue
    pix=[p for p in (r.get('anomaly_pixels') or []) if p['vrp_mw']>0 and p.get('dist_km') is not None and p['dist_km']<=7]
    ts=[T(L(p['bt_k'])-p['vrp_mw']*1e6/(KW*AREA)) for p in pix if L(p['bt_k'])-p['vrp_mw']*1e6/(KW*AREA)>0]
    if not ts: continue
    cl='anillo' if abs(r['t_bg_k']-st.median(ts))<0.3 else 'mas_frio'
    c[(cl, r.get('triggered_test1'), r.get('n_test1_pixels',0)>0)]+=1
for k,v in sorted(c.items(),key=str): print(k,v)
