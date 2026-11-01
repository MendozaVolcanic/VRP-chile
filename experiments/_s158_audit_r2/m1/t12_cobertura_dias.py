# M1 T12. Camino distinto al de V2 para F5-01 (faltan 12, 13 y 18 oct en el reproceso): mirar la PRODUCCION (records
# vigentes en data/mirova_equivalent) de esos dias, su product_version (standard/nrt) y cuando se procesaron por primera
# vez. Si el Standard existiera hoy para el 18-oct, la reposicion (decision 1 de AUDIT) es factible; si los records del
# 18-oct siguen siendo 'nrt', el Standard todavia no existe y el reproceso no podria reponerlos.
# Pregunta 1: si produccion no tuviera esas pasadas, el conteo seria 0 (y se vería). Pregunta 2: control con un dia
# anterior que seguro es 'standard' (2026-10-01).
import json,glob,collections,os
TIER=['PuyehueCordonCaulle','Villarrica','Lascar','Copahue','NevadosDeChillan','Llaima','Chaiten','PlanchonPeteroa','Lastarria','Isluga','Tupungatito']
c=collections.defaultdict(collections.Counter); fp=collections.defaultdict(list)
for v in TIER:
    for r in json.load(open(f'data/mirova_equivalent/{v}.json',encoding='utf-8'))['records']:
        d=r['datetime_utc'][:10]
        if d in ('2026-10-01','2026-10-12','2026-10-13','2026-10-17','2026-10-18','2026-10-19') and r['sensor'].startswith('VIIRS'):
            c[d][r.get('product_version')]+=1
            fp[d].append(r.get('first_processed_utc'))
for d in sorted(c):
    f=sorted(x for x in fp[d] if x)
    print(d,'records VIIRS Tier A:',sum(c[d].values()),dict(c[d]),'| primer procesado min/max:',f[0] if f else None,f[-1] if f else None)
