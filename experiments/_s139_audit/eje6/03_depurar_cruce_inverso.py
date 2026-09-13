"""Depuracion del cruce inverso de 02 (1499 pareos directos contra 28 inversos no cuadran).
Mide: duplicados OSF por (volcan, res, minuto); desfase temporal nuestro->OSF mas cercano;
tipo de solar_zenith_deg. Si el desfase tipico fuera > 10 min, el inverso estaba mal."""
import json, pathlib, bisect
import pandas as pd
from datetime import datetime, timedelta
R=pathlib.Path(__file__).resolve().parents[3]
osf=pd.read_csv(R/'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
osf['t']=pd.to_datetime(osf.timeUTC,format='%d/%m/%Y %H:%M',errors='coerce')
o=osf[(osf.Volc_Name=='Láscar')&(osf.t>='2025-02-15')&(osf.t<'2025-12-01')&(osf.Resolution==375)]
print('Lascar 375 OSF filas',len(o),'duplicados (t)',o.duplicated('t').sum(), 'Satellite',o.Satellite.value_counts().to_dict())
ts=sorted(o.t.dt.to_pydatetime())
recs=json.load(open(R/'data/mirova_equivalent/Lascar.json',encoding='utf-8'))['records']
sz=[type(r.get('solar_zenith_deg')).__name__ for r in recs[:5]]; print('tipo sza',sz)
difs=[];n=0
for r in recs:
    if r['sensor'].startswith('MODIS') or r['sensor'].endswith('_750'): continue
    dt=datetime.strptime(r['datetime_utc'],'%Y-%m-%d %H:%M')
    if not (datetime(2025,2,15)<=dt<datetime(2025,12,1)): continue
    pc=r.get('primary_cluster') or {}
    if not ((pc.get('vrp_mw') or 0)>0 and (pc.get('centroid_dist_km') or 99)<=5): continue
    n+=1; i=bisect.bisect_left(ts,dt)
    c=[abs((ts[j]-dt).total_seconds())/60 for j in (i-1,i) if 0<=j<len(ts)]
    difs.append(min(c) if c else None)
s=pd.Series(difs); print('Lascar 375 nuestras det crater',n); print(s.describe()); print('<=10 min',(s<=10).sum(),' <=60',(s<=60).sum())
print('sza de muestra', [recs[k].get('solar_zenith_deg') for k in range(0,len(recs),1500)])
