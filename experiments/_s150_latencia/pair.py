import json, glob, pandas as pd, numpy as np
fs=[]
for f in glob.glob('first_seen_*.json'): fs+=json.load(open(f))
v=pd.DataFrame(fs).drop_duplicates(subset=['v','sensor','acq'])
v['acq']=pd.to_datetime(v.acq).dt.tz_localize('UTC'); v['commit']=pd.to_datetime(v.first_commit,utc=True)
v=v[(v.acq>='2026-09-14')&(v.acq<'2026-10-02 12:00')]   # excluye pasadas que el pipeline aun no podia ver al quedar detenido
pr=pd.DataFrame(json.load(open('pages_runs.json')))
pr=pr[pr.conclusion=='success']; pr['c']=pd.to_datetime(pr.createdAt,utc=True); pr['u']=pd.to_datetime(pr.updatedAt,utc=True); pr=pr.sort_values('c')
def panel(t):
    s=pr[pr.c>=t]; return s.u.iloc[0] if len(s) else pd.NaT
v['panel']=v.commit.apply(panel)
v['lat_commit']=(v.commit-v.acq).dt.total_seconds()/3600
v['lat_panel']=(v.panel-v.acq).dt.total_seconds()/3600
v['fam']=np.where(v.sensor.str.startswith('MODIS'),'MODIS',np.where(v.sensor.str.endswith('_750'),'VIIRS','VIIRS375'))
m=pd.read_csv('mirova_consolidado.csv').dropna(subset=['Fecha_Proceso_GitHub'])
m['acq']=pd.to_datetime(m.Fecha_Satelite_UTC).dt.tz_localize('UTC')
m['seen']=pd.to_datetime(m.Fecha_Proceso_GitHub).dt.tz_localize('America/Santiago',ambiguous='NaT',nonexistent='NaT').dt.tz_convert('UTC')
m['lat_m']=(m.seen-m.acq).dt.total_seconds()/3600
name={'Puyehue-Cordon Caulle':'PuyehueCordonCaulle','Nevados de Chillan':'NevadosDeChillan'}
m['v']=m.Volcan.replace(name); m['fam']=m.Sensor
rows=[]
for _,r in v.iterrows():
    c=m[(m.v==r.v)&(m.fam==r.fam)]
    if c.empty: continue
    dt=(c.acq-r.acq).abs()
    i=dt.idxmin()
    if dt[i]<=pd.Timedelta(minutes=3):
        rows.append(dict(v=r.v,fam=r.fam,sensor=r.sensor,acq=r.acq,lat_commit=r.lat_commit,lat_panel=r.lat_panel,lat_m=m.lat_m[i],vrp=r.vrp,mvrp=m.VRP_MW[i],tipo=m.Tipo_Registro[i]))
p=pd.DataFrame(rows)
def s(x): x=x.dropna(); return f"n={len(x)} med={x.median():.2f} p10={x.quantile(.1):.2f} p90={x.quantile(.9):.2f} min={x.min():.2f} max={x.max():.2f}"
print('VRP Chile pasadas nuevas (14-sep a 2-oct 12UTC):',len(v), 'con panel:',v.lat_panel.notna().sum())
print('VRP commit total:',s(v.lat_commit)); print('VRP panel total:',s(v.lat_panel))
for f in ['MODIS','VIIRS','VIIRS375']:
    print(f,'VRP panel',s(v[v.fam==f].lat_panel))
print('\nEMPAREJADAS (volcan+familia sensor+|dt|<=3min):',len(p), 'VRP sin pareja MIROVA:',len(v)-len(p))
print('VRP Chile panel:',s(p.lat_panel)); print('VRP Chile commit:',s(p.lat_commit)); print('MIROVA scraper:',s(p.lat_m))
d=p.lat_panel-p.lat_m; print('dif VRP-MIROVA:',s(d), ' VRP antes que MIROVA:',(d<0).sum())
for f in ['MODIS','VIIRS','VIIRS375']:
    q=p[p.fam==f]; print(f,'| VRP',s(q.lat_panel),'| MIROVA',s(q.lat_m),'| VRP primero',(q.lat_panel<q.lat_m).sum())
a=p[(p.tipo=='ALERTA_TERMICA')]
print('\nsolo ALERTA_TERMICA MIROVA:',len(a)); 
if len(a): print('VRP',s(a.lat_panel),'| MIROVA',s(a.lat_m))
p.to_csv('pares.csv',index=False)
