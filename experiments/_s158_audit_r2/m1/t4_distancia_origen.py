# M1 T4. V1 (F1-H3) infirio que la Distancia_km de MIROVA en Cordon Caulle se mide desde mirova_center (centro de
# su grilla) y que 7.65-8.55 km significa 'alerta en el crater' (el crater esta a 7.6 km del centro). Esa
# inferencia nunca se midio con posiciones (A93: la distancia no trae acimut). Prueba: para pasadas V750 de PCC
# con alerta de la tabla (lectura A) y un cumulo nuestro, comparar Distancia_km de MIROVA con nuestra distancia
# (centroide del cumulo) a (a) mirova_center, (b) el crater (vent), (c) lat/lon nominal. Si la hipotesis de V1 es
# correcta, (a) debe acercarse a MIROVA mejor que (b). Control positivo: Villarrica (centro~crater, 0.85 km).
# Pregunta 2: si no hubiera pares el script imprime n=0.
import json,math,pandas as pd,numpy as np,yaml
def hv(a,b,c,d):
    R=6371.0088; p1,p2=math.radians(a),math.radians(c); dl=math.radians(d-b); dp=p2-p1
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
vy=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8'))
cfg={v['name']:v for v in (vy['volcanoes'] if 'volcanoes' in vy else vy)}
tab=pd.read_csv('latest_consolidado.csv'); tab['t']=pd.to_datetime(tab.Fecha_Satelite_UTC)
alias={'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Villarrica':'Villarrica','Lascar':'Lascar','NevadosDeChillan':'Nevados de Chillan','Isluga':'Isluga','Chaiten':'Chaiten','Lastarria':'Lastarria','Tupungatito':'Tupungatito','PlanchonPeteroa':'PlanchonPeteroa','Llaima':'Llaima','Copahue':'Copahue'}
for vol in ['PuyehueCordonCaulle','Villarrica','Lascar','NevadosDeChillan']:
    c=cfg[vol]; mc=(c.get('mirova_center_lat',c['lat']),c.get('mirova_center_lon',c['lon']))
    vent=(c.get('vent_lat',c['lat']),c.get('vent_lon',c['lon'])); nom=(c['lat'],c['lon'])
    a=tab[(tab.Sensor=='VIIRS')&(tab.Tipo_Registro=='ALERTA_TERMICA')&(tab.Volcan==alias[vol])&(tab.t>='2026-03-01')]
    recs=json.load(open(f'data/mirova_equivalent/{vol}.json',encoding='utf-8'))['records']
    idx={}
    for r in recs:
        if r['sensor'].endswith('_750') and r.get('primary_cluster') and r['primary_cluster'].get('centroid_lat') is not None:
            idx.setdefault(pd.Timestamp(r['datetime_utc']),[]).append(r)
    rows=[]
    for _,x in a.iterrows():
        best=None
        for tt,lst in idx.items():
            dt=abs((tt-x.t).total_seconds())/60
            if dt<=8 and (best is None or dt<best[0]): best=(dt,lst[0])
        if best:
            pc=best[1]['primary_cluster']; la,lo=pc['centroid_lat'],pc['centroid_lon']
            rows.append((x.Distancia_km,hv(*mc,la,lo),hv(*vent,la,lo),hv(*nom,la,lo)))
    R=np.array(rows)
    print(f'{vol}: alertas tabla V750 desde 2026-03-01: {len(a)}, con cumulo nuestro (|dt|<=8 min): {len(R)}')
    if len(R):
        for j,nm in [(1,'mirova_center'),(2,'crater(vent)'),(3,'nominal')]:
            e=np.abs(R[:,0]-R[:,j]); print(f'   |Dist_MIROVA - dist_nuestra a {nm}|: mediana {np.median(e):.2f} km, p90 {np.percentile(e,90):.2f}; MIROVA mediana {np.median(R[:,0]):.2f}, nuestra a {nm} mediana {np.median(R[:,j]):.2f}')
