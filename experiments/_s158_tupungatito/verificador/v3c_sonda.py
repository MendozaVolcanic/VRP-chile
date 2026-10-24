# Sonda del verificador S158 (movida desde _tmp/verif/). Correr desde la raíz del worktree; espera el JSON C0 en _tmp/Tupungatito_pre883.json (git show 8471add46^:data/mirova_equivalent/Tupungatito.json).
import json, math, statistics as st, sys, os
sys.path.insert(0,'.')
os.environ.setdefault("VRP_PROFILE","mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK
from pipeline import process_viirs as pv
LAM,KW,AREA=pv.I04_LAMBDA,pv.WOOSTER_COEFF,pv.NADIR_PIXEL_AREA_M2
L=lambda t: C1_PLANCK/(LAM**5*(math.exp(C2_PLANCK/(LAM*t))-1))
T=lambda l: C2_PLANCK/(LAM*math.log(1+C1_PLANCK/(LAM**5*l)))
pre=json.load(open('_tmp/Tupungatito_pre883.json',encoding='utf-8'))['records']
c0=[r for r in pre if not (r.get('regimen') or {}).get('codigo_sha') and r['sensor'] in ('VIIRS_SNPP','VIIRS_NOAA20','VIIRS_NOAA21') and r.get('final_hotspot_source')=='ctx_cluster' and r.get('t_bg_k')]
n=0
for r in c0:
    pix=[p for p in (r.get('anomaly_pixels') or []) if p.get('dist_km') is not None and p['vrp_mw']>0]
    out=[]
    for p in pix:
        rest=L(p['bt_k'])-p['vrp_mw']*1e6/(KW*AREA)
        out.append((round(p['dist_km'],2), p['bt_k'], p['vrp_mw'], round(r['t_bg_k']-T(rest),2) if rest>0 else None))
    if any(o[3] and o[3]>3 for o in out):
        n+=1
        if n<=6:
            print(r['datetime_utc'], r['sensor'], 'z',r.get('sensor_zenith_deg'),'t_bg',r['t_bg_k'],'ncloud',r.get('n_cloud_masked'),'vrp_mir',r.get('vrp_mir_mw'),'pc',r.get('primary_cluster'))
            print('    ',out[:6], 'keys extra:', [k for k in r if 'corona' in k or 'area' in k or 'kernel' in k])
print('ctx records with some pixel dT>3:',n,'of',len(c0))
