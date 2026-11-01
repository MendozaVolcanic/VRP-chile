# M1 T11. Reconstruccion INDEPENDIENTE (escrita desde cero, sin importar codigo de f3/ ni v3/) del pareo OSF v2.5 2025
# contra nuestros records y de la tabla central de F3-H2 (conteo y energia nuestro/MIROVA por tramo de cenit, V375).
# Por que: V3 'verifico' F3-H2 regenerando el pareo con el script de F3 (idem celda a celda), de modo que el pareo
# era un punto unico de falla compartido por F3-H2/H3/H4 y V3. Aqui el pareo exige ademas el MISMO satelite
# (columna Satellite del OSF contra el sensor del record), que f3 no usaba.
# Pregunta 1: si el pareo de F3 estuviera mezclando satelites, la tabla cambiaria. Pregunta 2: control positivo:
# el cenit del OSF y el del record deben coincidir (|dz| mediana ~0.07) y la identidad k*A debe valer.
# Definicion de 'dentro del inner': pixel alertado con distancia al CRATER (vent) <= inner_radius_km del volcan.
import json,math,numpy as np,pandas as pd,yaml,sys
OSF=r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'
IDS={358041:'Chaiten',357070:'NevadosDeChillan',357090:'Copahue',355030:'Isluga',355100:'Lascar',355120:'Lastarria',357110:'Llaima',357040:'PlanchonPeteroa',357150:'PuyehueCordonCaulle',357120:'Villarrica'}
vy=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8')); vy=vy['volcanoes'] if 'volcanoes' in vy else vy
cfg={v['name']:v for v in vy}
def hv(a,b,c,d):
    R=6371.0088;p1,p2=math.radians(a),math.radians(c);dl=math.radians(d-b);dp=p2-p1
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
o=pd.read_csv(OSF,encoding='latin-1')
o=o[o.IDvolc.isin(IDS)&(o.Dayflag==0)&(o.Resolution==375)].copy()
o['t']=pd.to_datetime(o.timeUTC,format='%d/%m/%Y %H:%M',errors='coerce')
o=o[(o.t>='2025-01-01')&(o.t<'2026-01-01')&(o['class']==1)]
o['vol']=o.IDvolc.map(IDS)
print('OSF V375 noche 2025 clase 1 en los 10 volcanes:',len(o),'Satellite:',o.Satellite.value_counts().to_dict())
sat_names={}
rows=[]
ct=[]
for vol,g in o.groupby('vol'):
    c=cfg[vol]; inner=c.get('inner_radius_km',10); vent=(c.get('vent_lat',c['lat']),c.get('vent_lon',c['lon']))
    recs=json.load(open(f'data/mirova_equivalent/{vol}.json',encoding='utf-8'))['records']
    recs=[(pd.Timestamp(r['datetime_utc']),r) for r in recs if r['sensor'].startswith('VIIRS') and not r['sensor'].endswith('_750') and r['datetime_utc'][:4]=='2025']
    for _,m in g.iterrows():
        cand=[(abs((t-m.t).total_seconds())/60,t,r) for t,r in recs if abs((t-m.t).total_seconds())<=300]
        if not cand: continue
        for dt,t,r in cand: ct.append((int(m.Satellite),r['sensor']))
        # MISMO satelite: elegir candidato cuyo sensor corresponde al Satellite (se infiere del crosstab, ver abajo)
        rows.append((vol,m,cand,inner,vent))
ctt=pd.crosstab(pd.Series([a for a,b in ct],name='OSF_Satellite'),pd.Series([b for a,b in ct],name='sensor_nuestro'))
print('crosstab de candidatos (|dt|<=5 min): ');print(ctt.to_string())
satmap={s:ctt.loc[s].idxmax() for s in ctt.index}
print('mapa Satellite->sensor inferido (modo):',satmap)
out=[]
for vol,m,cand,inner,vent in rows:
    same=[x for x in cand if x[2]['sensor']==satmap[int(m.Satellite)]]
    if not same: continue
    dt,t,r=min(same,key=lambda x:x[0])
    px=r.get('anomaly_pixels') or []
    nall=r.get('n_anomalous_pixels') or 0
    # todos los alertados de MIROVA dentro del inner: Max_Dist (m) <= inner*1000
    if m.Max_Dist>inner*1000: continue
    if len(px)<nall: continue  # lista incompleta (top100)
    din=[p for p in px if hv(*vent,p['lat'],p['lon'])<=inner]
    out.append(dict(vol=vol,zen=m.SatZen,zo=r.get('sensor_zenith_deg'),NM=m.Npix,n=len(din),
                    E=sum(max(p['vrp_mw'],0) for p in din),M=m.VRP/1e6,dt=dt))
df=pd.DataFrame(out)
print('\npares tras mismo-satelite + todo MIROVA dentro del inner + lista completa:',len(df))
print('control cenit |zo-zen| mediana %.3f p95 %.3f'%((df.zo-df.zen).abs().median(),(df.zo-df.zen).abs().quantile(.95)))
bins=[(0,10),(10,20),(20,30),(30,40),(40,50),(50,60),(60,75)]
print('tramo   n   sum(n)/sum(N_M)   sum(E)/sum(M)   N_M medio')
for lo,hi in bins:
    s=df[(df.zen>=lo)&(df.zen<hi)]
    if len(s): print(f'{lo:>2}-{hi:<2} {len(s):4d}   {s.n.sum()/s.NM.sum():.3f}            {s.E.sum()/s.M.sum():.3f}         {s.NM.mean():.2f}')
from scipy.stats import spearmanr
print('Spearman(N_M, cenit) global:',round(spearmanr(df.NM,df.zen)[0],3),'| Spearman(n/N_M, cenit):',round(spearmanr(df.n/df.NM,df.zen)[0],3))
df.to_csv('experiments/_s158_audit_r2/m1/t11_pares.csv',index=False)
