import json,sys,collections,statistics,math
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(sys.argv[1]); ROOT=Path(sys.argv[2])
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))
import banco_paridad as bp
s149={tuple(k) for k in json.load(open(ROOT/'experiments/_s151_d25_v750_disco/lista_268_s149.json',encoding='utf-8'))['negativos']}
filas=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.rglob('*.json'))]
inner=bp.inner_desde_html()
casos=[];idx=[]
for i,f in enumerate(filas):
    for b in ('control','a','b'):
        r=f[b]['record']; casos.append([{k:r.get(k) for k in bp.CAMPOS_JS},inner[f['volcan']]]); idx.append((i,b))
res=bp.correr_node(casos)
pub=collections.defaultdict(dict)
for (i,b),p in zip(idx,res): pub[i][b]=p[4]
pc=lambda f,b:(f[b]['record'].get('primary_cluster') or {})
print('--- b apaga')
for i,f in enumerate(filas):
    if pub[i]['control'] and not pub[i]['b']:
        print(f['clase'],f['volcan'],f['pasada_utc'],f['sensor'],'mirova_alerta_mw',f.get('mirova_vrp_alerta_mw'),'t_bg',f['persistido']['t_bg_k'])
        print('  ctrl',pc(f,'control'),'\n  a',pc(f,'a'),'\n  b',pc(f,'b'))
        for c in f['b']['llamadas_fondo']:
            print('  call b', {k:c[k] for k in ('n_hot','n_sin_vecinos','vecinos_8') if k in c}, 'bt',c['bt_hot_k'][:5],'Lhot',[round(x,4) for x in c['L_hot'][:5]],'Lhoy',[round(x,4) for x in c['L_bg_hoy'][:5]],'Lnew',[round(x,4) for x in c['L_bg_nuevo'][:5]])
print('--- C-P1 Isluga 06-10: en s149?', ('Isluga','2026-06-10 05:36','VIIRS_NOAA21_750') in s149)
for i,f in enumerate(filas):
    if not f.get('control_p1'): print(f['volcan'],f['pasada_utc'],{b:pub[i][b] for b in pub[i]}, 'a pc',pc(f,'a'))
# alerts: MIROVA mw vs arm a
print('--- alertas cero: mirova vs a')
al=[(f.get('mirova_vrp_alerta_mw'),pc(f,'a').get('vrp_mw'),f['volcan']) for f in filas if f['clase']=='alerta_cero']
for x in sorted(al,key=lambda t:t[0] or 0): print(x)
# AUC pc vrp a: alertas vs neg268
neg=[pc(f,'a').get('vrp_mw') or 0 for f in filas if f['clase']=='neg_cero' and (f['volcan'],f['pasada_utc'],f['sensor']) in s149]
ale=[v for _,v,_ in al]
auc=sum((a>n)+0.5*(a==n) for a in ale for n in neg)/(len(ale)*len(neg))
print('AUC pc vrp brazo a alertas vs negativos',round(auc,3))
