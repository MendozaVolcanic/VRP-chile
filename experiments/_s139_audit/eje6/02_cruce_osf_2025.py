"""S139 eje 6: el archivo OSF v2.5 de MIROVA (VRP_GLOBAL_ARCHIVE_2025.csv, 615.470 filas,
2000-02 a 2025-12) contra nuestros records del backfill 2025 (data/mirova_equivalent/).

POR QUE: es la unica verdad externa del propio grupo MIROVA con, por pasada, VRP, Npix,
Tot_Lmir_bk (radiancia de FONDO) y class 0/1 (volcanico / no volcanico). Desde S120 tenemos
records de 2025 que solapan con el. Ninguna metrica viva lo usa (grep scripts/pipeline/tests = 0).

Pregunta 1 (si lo medido estuviera roto, lo veria?): si nuestra deteccion al crater estuviera
muerta, el recall contra OSF caeria a ~0; si inflaramos magnitud, el ratio lo mostraria.
Pregunta 2 (instrumento muerto?): se separa SIN DATO (no hay record nuestro en +-10 min, la
pasada no se proceso) de FALLA (hay record y no detecta). Control positivo: desplazar las
horas OSF +6 h debe hundir el pareo (si no se hunde, el pareo es por azar).
Ventana: 2025-02-15 a 2025-11-30 (lo que cubre el backfill). Solo noche (Dayflag=0).
"""
import json, pathlib, bisect
import pandas as pd
from datetime import datetime, timedelta
R=pathlib.Path(__file__).resolve().parents[3]
MAP={'Láscar':'Lascar','Lastarria':'Lastarria','Isluga':'Isluga','Llaima':'Llaima','Villarrica':'Villarrica',
     'Chaitén':'Chaiten','Copahue':'Copahue','Planchón-Peteroa':'PlanchonPeteroa',
     'Puyehue-Cordón Caulle':'PuyehueCordonCaulle','Chillán, Nevados de':'NevadosDeChillan','Tupungatito':'Tupungatito'}
INNER={"Lascar":5,"Lastarria":3,"Tupungatito":7,"PlanchonPeteroa":3,"NevadosDeChillan":5,"Chaiten":5,
       "Villarrica":5,"Llaima":5,"Copahue":4,"Isluga":5,"PuyehueCordonCaulle":20}
T0,T1=datetime(2025,2,15),datetime(2025,12,1)
osf=pd.read_csv(R/'data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv')
osf['t']=pd.to_datetime(osf.timeUTC,format='%d/%m/%Y %H:%M',errors='coerce')
print('Tupungatito en OSF:', (osf.Volc_Name.str.contains('Tupun',na=False)).sum())
o=osf[osf.Volc_Name.isin(MAP)&(osf.t>=T0)&(osf.t<T1)].copy()
o['vol']=o.Volc_Name.map(MAP); o['res']=o.Resolution.astype(int)
print('OSF Chile ventana filas',len(o),'Dayflag',o.Dayflag.value_counts().to_dict(),'class',o['class'].value_counts().to_dict())
print('Npix min',o.Npix.min(),'Npix==0',(o.Npix==0).sum())
def res(s): return 1000 if s.startswith('MODIS') else (750 if s.endswith('_750') else 375)
ours={}
for v in INNER:
    recs=json.load(open(R/f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records']
    for r in recs:
        dt=datetime.strptime(r['datetime_utc'],'%Y-%m-%d %H:%M')
        if not (T0-timedelta(hours=7)<=dt<T1+timedelta(hours=7)): continue
        ours.setdefault((v,res(r['sensor'])),[]).append((dt,r))
for k in ours: ours[k].sort(key=lambda x:x[0])
def crater(r,v):
    pc=r.get('primary_cluster') or {}
    vr=pc.get('vrp_mw') or 0; d=pc.get('centroid_dist_km')
    return vr>0 and d is not None and d<=INNER[v] and vr<=50000 and r.get('distance_class') in ('summit',None), vr
def nearest(v,rs,t,tol=10):
    L=ours.get((v,rs),[]); ts=[x[0] for x in L]; i=bisect.bisect_left(ts,t); best=None
    for j in (i-1,i):
        if 0<=j<len(L) and abs((L[j][0]-t).total_seconds())<=tol*60:
            if best is None or abs((L[j][0]-t).total_seconds())<abs((best[0]-t).total_seconds()): best=L[j]
    return best
def run(shift_h=0, label=''):
    rows=[]
    for _,x in o[(o.Dayflag==0)].iterrows():
        m=nearest(x.vol,x.res,x.t.to_pydatetime()+timedelta(hours=shift_h))
        if m is None: st,vr='SIN_DATO',None
        else:
            ok,vr=crater(m[1],x.vol); st='DETECTA' if ok else 'NO_DETECTA'
        rows.append((x.vol,x.res,int(x['class']),st,vr,x.VRP/1e6))
    d=pd.DataFrame(rows,columns=['vol','res','cls','st','ours','osf'])
    print(f'\n== {label} (shift {shift_h} h) denominador = pasadas nocturnas OSF Chile en ventana')
    t=pd.crosstab([d.res,d.cls],d.st,margins=True); print(t)
    for res_ in (375,750,1000):
        s=d[(d.res==res_)&(d.cls==1)&(d.st!='SIN_DATO')]
        if len(s): print(f'recall crater class1 res{res_}: {(s.st=="DETECTA").mean()*100:.1f}% de n={len(s)} (excluye SIN_DATO)')
    return d
d=run(0,'REAL'); run(6,'CONTROL POSITIVO desplazado')
s=d[(d.cls==1)&(d.st=='DETECTA')&(d.osf>0)]
s=s.assign(r=s.ours/s.osf)
print('\n== ratio ours(pc.vrp_mw)/OSF VRP por res y volcan, class1, ambos detectan')
print(s.groupby('res').r.agg(['size','median']).round(3))
print(s.groupby(['vol']).r.agg(['size','median']).round(3))
# negativos: nuestras detecciones crater nocturnas sin fila OSF (de ninguna clase) en +-10 min
idx={}
for _,x in o.iterrows(): idx.setdefault((x.vol,x.res),[]).append(x.t.to_pydatetime())
fp=tp=0; per={}
for (v,rs),L in ours.items():
    ts=sorted(idx.get((v,rs),[]))
    for dt,r in L:
        if not (T0<=dt<T1): continue
        # v2 (depurado en 03): los records del backfill traen solar_zenith_deg=None; la v1
        # los trataba como dia y los descartaba (instrumento roto: 28 vs 1350). Si falta el
        # angulo, noche = hora UTC 00-11 (noche local en Chile).
        sza=r.get('solar_zenith_deg')
        if (sza is not None and sza<90) or (sza is None and dt.hour>11): continue
        ok,_=crater(r,v)
        if not ok: continue
        i=bisect.bisect_left(ts,dt-timedelta(minutes=10))
        hit= i<len(ts) and ts[i]<=dt+timedelta(minutes=10)
        per.setdefault((rs,v),[0,0])[0 if hit else 1]+=1
        if hit: tp+=1
        else: fp+=1
print(f'\n== nuestras detecciones crater nocturnas en ventana: con fila OSF {tp}, SIN fila OSF {fp} (fraccion sin respaldo {fp/(tp+fp)*100:.1f}%)')
print(pd.DataFrame({k:v for k,v in per.items()},index=['con_OSF','sin_OSF']).T.groupby(level=0).sum())

# Unidad del operador (A94): la NOCHE por volcan y resolucion. Noche = fecha UTC (00-11 UTC).
nights_osf={}
for _,x in o[o.Dayflag==0].iterrows(): nights_osf.setdefault((x.vol,x.res),{}).setdefault(x.t.date(),set()).add(int(x['class']))
tab={}
for (v,rs),L in ours.items():
    dets={dt.date() for dt,r in L if T0<=dt<T1 and dt.hour<=11 and crater(r,v)[0]}
    no=nights_osf.get((v,rs),{})
    for dd in dets:
        k='OSF_class1' if 1 in no.get(dd,set()) else ('OSF_solo_class0' if dd in no else 'SIN_OSF')
        tab.setdefault((rs,v),{}).setdefault(k,0); tab[(rs,v)][k]+=1
t=pd.DataFrame(tab).T.fillna(0).astype(int); print('\n== noches con deteccion crater nuestra, por respaldo OSF'); print(t); print(t.groupby(level=0).sum())
