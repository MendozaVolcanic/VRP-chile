# M1 T15. Los frentes parean alertas de MIROVA con records nuestros con tolerancias distintas y no declaradas igual:
# F1 20 min (alertas_mirova_perdidas.py:49, cruce_referencia.py:56), V1 8 min, F3 5 min, V2 minuto exacto, F6/F5 otros.
# Si dos satelites distintos pasaran a menos de la tolerancia sobre el mismo volcan, el pareo podria asignar la
# alerta a un record de OTRO satelite (A48-like). Pregunta 1: la separacion minima entre pasadas de satelites
# distintos sobre un mismo volcan, en records V750 de 2026, lo dice. Pregunta 2: control = misma estadistica entre
# records del MISMO satelite (debe ser ~12 h o mas, nunca <90 min).
import json,collections,numpy as np,pandas as pd
TIER=['PuyehueCordonCaulle','Villarrica','Lascar','Copahue','NevadosDeChillan','Llaima','Chaiten','PlanchonPeteroa','Lastarria','Isluga','Tupungatito']
gaps=[];same=[]
for v in TIER:
    rs=[(pd.Timestamp(r['datetime_utc']),r['sensor']) for r in json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records'] if r['sensor'].endswith('_750') and r['datetime_utc']>='2026-03-01']
    rs.sort()
    for (t1,s1),(t2,s2) in zip(rs,rs[1:]):
        g=(t2-t1).total_seconds()/60
        (gaps if s1!=s2 else same).append(g)
gaps=np.array(gaps);same=np.array(same)
print('consecutivos de satelites DISTINTOS: n',len(gaps),'min %.1f p1 %.1f p5 %.1f mediana %.1f'%(gaps.min(),np.percentile(gaps,1),np.percentile(gaps,5),np.median(gaps)))
print('  cuantos con separacion <=20 min:',int((gaps<=20).sum()),'| <=30:',int((gaps<=30).sum()),'| <=45:',int((gaps<=45).sum()))
print('consecutivos del MISMO satelite: n',len(same),'min %.1f'%same.min())

# --- parte 2: para cada ALERTA_TERMICA V750 de la tabla (2026-03-01..), distancia al record V750 mas cercano del volcan
import numpy as np
alias={'PuyehueCordonCaulle':'Puyehue-Cordon Caulle','Villarrica':'Villarrica','Lascar':'Lascar','NevadosDeChillan':'Nevados de Chillan','Isluga':'Isluga','Chaiten':'Chaiten','Lastarria':'Lastarria','Tupungatito':'Tupungatito','PlanchonPeteroa':'PlanchonPeteroa','Llaima':'Llaima','Copahue':'Copahue'}
tab=pd.read_csv('latest_consolidado.csv'); tab['t']=pd.to_datetime(tab.Fecha_Satelite_UTC)
al=tab[(tab.Sensor=='VIIRS')&(tab.Tipo_Registro=='ALERTA_TERMICA')&(tab.t>='2026-03-01')]
dts=[]
for v,nm in alias.items():
    rs=np.array([np.datetime64(pd.Timestamp(r['datetime_utc'])) for r in json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records'] if r['sensor'].endswith('_750')])
    for t in al[al.Volcan==nm].t.values:
        d=np.abs((rs-t).astype('timedelta64[s]').astype(float))/60
        dts.append(d.min() if len(d) else np.nan)
dts=np.array(dts)
print('\nALERTA_TERMICA V750 tabla desde 2026-03-01:',len(dts),'| con record V750 a <=1 min:',int((dts<=1).sum()),'| (1,8]:',int(((dts>1)&(dts<=8)).sum()),'| (8,20]:',int(((dts>8)&(dts<=20)).sum()),'| >20 o sin record:',int((dts>20).sum()+np.isnan(dts).sum()))
