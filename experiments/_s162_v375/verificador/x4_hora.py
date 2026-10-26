import json,collections,io,sys
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXC=("2026-10-12","2026-10-13","2026-10-17","2026-10-18","2026-10-19","2026-10-20")
pob=json.load(open('../../_s159/portes/poblacion_completa.json',encoding='utf-8'))['pasadas']
pas=[o for o in pob if o['b']=='VIIRS375' and o['lab']=='pos' and o['decide'] and o['hora_utc'][:10] not in EXC]
por=collections.defaultdict(list)
for o in pas:
    if o['mirova_vrp'] and o['mirova_vrp']>0: por[(o['volcan'],o['hora_utc'][:10])].append(o)
r=[]
for k,l in por.items():
    l=sorted(l,key=lambda o:o['hora_utc'])
    for a,b in zip(l[:-1],l[1:]): r.append(b['mirova_vrp']/a['mirova_vrp'])
print('pares consecutivos misma noche',len(r),'mediana',round(float(np.median(r)),3))
# cuantas noches con >=3 pasadas con alerta
print(collections.Counter(len(l) for l in por.values()))
# cenit vs hora: correlacion dentro de noche
