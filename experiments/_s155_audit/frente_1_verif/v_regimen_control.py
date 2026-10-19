"""Control positivo de v_regimen_por_fecha: mismo conteo sobre los JSON en 34cea39e (antes del backfill K).
Si alli el tramo 09-18..10-18 tiene Test 1 >0, el 0 de hoy es efecto del reproceso y no un campo muerto."""
import json, subprocess, collections, sys
vols=['Villarrica','Lascar','Copahue','Llaima','NevadosDeChillan','Lastarria','Isluga','Chaiten','Tupungatito','PlanchonPeteroa','PuyehueCordonCaulle']
ref=sys.argv[1]
tot=0;t1=0;proc=collections.Counter()
for v in vols:
    s=subprocess.run(['git','show',f'{ref}:data/mirova_equivalent/{v}.json'],capture_output=True).stdout
    d=json.loads(s); recs=d['records'] if isinstance(d,dict) else d
    for r in recs:
        dt=r.get('datetime_utc','')
        if '2026-09-18'<=dt<'2026-10-18T09:57:30':
            tot+=1; t1+= bool(r.get('triggered_test1')) or (r.get('n_test1_pixels') or 0)>0
            proc[(r.get('processed_utc') or '')[:10]]+=1
print(ref,'tramo 09-18..10-18 records',tot,'con_test1',t1, f'{100*t1/max(tot,1):.1f}%')
print('processed_utc:',sorted(proc.items())[-8:])
