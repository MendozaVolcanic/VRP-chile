import json,sys,collections,statistics
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(sys.argv[1])
filas=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.rglob('*.json'))]
pc=lambda f,b:(f[b]['record'].get('primary_cluster') or {})
print('--- C-P1 fallan')
for f in filas:
    if not f.get('control_p1'):
        print(f['clase'],f['volcan'],f['pasada_utc'],f['sensor'],'persist',f['persistido'],'\n   control pc',pc(f,'control'),'l1b',f.get('l1b_reprocesado'),'processed',f.get('processed_utc'),'pv',f['product_version'], f['control']['record'].get('product_version'))
print('--- reprocesados')
for f in filas:
    if f.get('l1b_reprocesado'):
        print(f['clase'],f['volcan'],f['pasada_utc'],'cp1',f['control_p1'],'ctrl',pc(f,'control').get('vrp_mw'),'pers',f['persistido']['pc_vrp_mw'],'a',pc(f,'a').get('vrp_mw'),'b',pc(f,'b').get('vrp_mw'))
print('--- cambios de magnitud control->a en clases que publican')
for cl in ('control_publica','protegida_publica','alerta_cero'):
    d=[(pc(f,'a').get('vrp_mw') or 0)-(pc(f,'control').get('vrp_mw') or 0) for f in filas if f['clase']==cl]
    print(cl,'iguales',sum(abs(x)<1e-9 for x in d),'de',len(d),'mediana dif',statistics.median(d))
