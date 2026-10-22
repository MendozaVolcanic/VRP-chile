# M1 T13. Recuento independiente (script propio, sin importar nada de f3/ ni v3/) de F3-H1 / V3: cumulos de cumbre
# de VIIRS 750 con vrp 0 por recorte, por volcan, y cuantos son alertas de la tabla de MIROVA (solo tabla, lectura A).
# Pregunta 1: si el defecto no existiera el recuento de 'todos los pixeles con bt <= t_bg' seria ~0 entre los cumulos
# en cero. Pregunta 2: control positivo = en los cumulos NO en cero la mayoria debe tener bt_max > t_bg.
# Noche = elevacion solar < 0 (solar_zenith_deg > 90). Ventana 2026-03-01..fin de datos. Tier A.
import json,pandas as pd,numpy as np,collections
TIER={'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Villarrica':'Villarrica','Lascar':'Lascar','Copahue':'Copahue','NevadosDeChillan':'Nevados de Chillan','Llaima':'Llaima','Chaiten':'Chaiten','PlanchonPeteroa':'PlanchonPeteroa','Lastarria':'Lastarria','Isluga':'Isluga','Tupungatito':'Tupungatito'}
tab=pd.read_csv('latest_consolidado.csv'); tab['t']=pd.to_datetime(tab.Fecha_Satelite_UTC)
al=tab[(tab.Sensor=='VIIRS')&(tab.Tipo_Registro=='ALERTA_TERMICA')&(tab.t>='2026-03-01')]
rows=[]
for v,nm in TIER.items():
    a=al[al.Volcan==nm]
    atimes=a.t.values
    for r in json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records']:
        if not r['sensor'].endswith('_750') or r['datetime_utc']<'2026-03-01': continue
        if (r.get('solar_zenith_deg') or 0)<=90: continue
        n=r.get('n_anomalous_pixels') or 0
        if n<1: continue
        pc=r.get('primary_cluster') or {}
        px=r.get('anomaly_pixels') or []
        t=pd.Timestamp(r['datetime_utc'])
        ma=bool(len(atimes)) and (np.abs((atimes-np.datetime64(t)).astype('timedelta64[s]').astype(float))<=480).any()
        bts=[p['bt_k'] for p in px if p.get('bt_k') is not None]
        rows.append(dict(vol=v,summit=r.get('distance_class')=='summit',vrp=pc.get('vrp_mw'),tbg=r.get('t_bg_k'),
                         btmax=max(bts) if bts else np.nan,mirova=ma,n=n))
d=pd.DataFrame(rows)
print('records V750 nocturnos con >=1 alertado (2026-03-01..), Tier A:',len(d))
z=d[d.summit&(d.vrp==0)]
print('cumulos de cumbre con vrp==0:',len(z),'| de ellos todos los pixeles bt<=t_bg (btmax<=tbg):',int((z.btmax<=z.tbg).sum()))
nz=d[d.summit&(d.vrp>0)]
print('control: cumulos de cumbre con vrp>0:',len(nz),'| btmax>tbg:',int((nz.btmax>nz.tbg).sum()))
print(pd.concat([z.groupby('vol').size().rename('cero'),d.groupby('vol').size().rename('records')],axis=1).fillna(0).astype(int).to_string())
print('cumulos en cero que coinciden con alerta de la TABLA (|dt|<=8 min):',int(z.mirova.sum()),'de',len(z))
