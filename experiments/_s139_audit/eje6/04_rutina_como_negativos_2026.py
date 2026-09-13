"""S139 eje 6: las 35.018 filas RUTINA del CSV consolidado (MIROVA miro la pasada y no publico
anomalia) usadas como NEGATIVOS, que ninguna metrica viva usa (auto_audit_weekly solo mide
recall y magnitud). Unidad: noche (fecha UTC, 00-11 UTC) por volcan y bucket de sensor.
Pregunta 1: si nuestro detector gritara en todas las noches, la fraccion 'dashboard en noche
RUTINA-pura' subiria hacia 100 %: la medicion lo veria. Pregunta 2: una noche sin fila MIROVA
de ningun tipo es SIN_REF, no negativo. Control positivo: noches ALERTA deben dar deteccion alta.
Predicado dashboard = crater (pc.vrp_mw>0, dist<=inner, <=50000, distance_class summit/None).
Ventana: 2026-01-10 a 2026-09-12 (rango del CSV). Limitacion: D2 (el CSV no cubre ~21 % de
pasadas publicadas) y RUTINA puede ser una pasada distinta a la nuestra de la misma noche."""
import json, pathlib
import pandas as pd
R=pathlib.Path(__file__).resolve().parents[3]
INNER={"Lascar":5,"Lastarria":3,"Tupungatito":7,"PlanchonPeteroa":3,"NevadosDeChillan":5,"Chaiten":5,
       "Villarrica":5,"Llaima":5,"Copahue":4,"Isluga":5,"PuyehueCordonCaulle":20}
def norm(n): return ''.join(ch for ch in str(n) if ch.isalnum()).lower()
ALIAS={norm(k):k for k in INNER}; ALIAS.update({'puyehuecordoncaulle':'PuyehueCordonCaulle','nevadosdechillan':'NevadosDeChillan','chillannevadosde':'NevadosDeChillan','planchonpeteroa':'PlanchonPeteroa'})
c=pd.read_csv(R/'latest_consolidado.csv'); o=pd.read_csv(R/'data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv')
ref=pd.concat([c,o]); ref['t']=pd.to_datetime(ref.Fecha_Satelite_UTC,errors='coerce'); ref=ref[ref.t.dt.hour<=11]
ref['vol']=ref.Volcan.map(lambda x: ALIAS.get(norm(x))); ref['bk']=ref.Sensor.map({'MODIS':'MODIS','VIIRS':'VIIRS750','VIIRS375':'VIIRS375'})
print('filas ref nocturnas sin volcan mapeado',ref.vol.isna().sum(), ref[ref.vol.isna()].Volcan.unique()[:10])
ref=ref.dropna(subset=['vol','bk']); ref['n']=ref.t.dt.date
ref['alerta']=ref.Tipo_Registro.str.startswith('ALERTA')
g=ref.groupby(['vol','bk','n']).agg(alerta=('alerta','max'),tipos=('Tipo_Registro',lambda s:'|'.join(sorted(set(s)))))
def bk(s): return 'MODIS' if s.startswith('MODIS') else ('VIIRS750' if s.endswith('_750') else 'VIIRS375')
rows=[]
for v in INNER:
    for r in json.load(open(R/f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records']:
        t=pd.Timestamp(r['datetime_utc'])
        if t<pd.Timestamp('2026-01-10') or t>=pd.Timestamp('2026-09-13') or t.hour>11: continue
        pc=r.get('primary_cluster') or {}; vr=pc.get('vrp_mw') or 0; d=pc.get('centroid_dist_km')
        ok= vr>0 and d is not None and d<=INNER[v] and vr<=50000 and r.get('distance_class') in ('summit',None)
        rows.append((v,bk(r['sensor']),t.date(),ok))
d=pd.DataFrame(rows,columns=['vol','bk','n','det']).groupby(['vol','bk','n']).det.max()
j=pd.concat([d,g],axis=1,join='outer')
j['clase']=j.apply(lambda x: 'SIN_NUESTRO' if pd.isna(x.det) else ('SIN_REF' if pd.isna(x.alerta) else ('ALERTA' if x.alerta else ('SOLO_FP' if 'RUTINA' not in x.tipos else 'RUTINA'))),axis=1)
k=j[~j.clase.isin(['SIN_NUESTRO'])]
out=k.assign(det=k.det.astype(bool)).groupby(['clase']).det.agg(['size','sum']); out['pct_det']=(out['sum']/out['size']*100).round(1); print(out)
kk=k[k.clase.isin(['RUTINA','ALERTA'])].assign(det=lambda z:z.det.astype(bool))
t=kk.groupby([kk.index.get_level_values('bk'),'clase']).det.agg(['size','sum']); t['pct']=(t['sum']/t['size']*100).round(1); print(t)
tr=kk[kk.clase=='RUTINA'].groupby(level='vol').det.agg(['size','sum']); tr['pct']=(tr['sum']/tr['size']*100).round(1); print(tr)
tp=kk[(kk.clase=='ALERTA')&kk.det].shape[0]; fp=kk[(kk.clase=='RUTINA')&kk.det].shape[0]
print(f'precision proxy noche (dashboard): {tp}/({tp}+{fp}) = {tp/(tp+fp)*100:.1f}%')
