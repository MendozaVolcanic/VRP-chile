import json,sys,collections,statistics,math
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(sys.argv[1])
s149={tuple(k) for k in json.load(open(sys.argv[2],encoding='utf-8'))['negativos']}
filas=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.rglob('*.json'))]
C1,C2=1.191042e8,1.4387752e4; LAM=4.05
def T(L): return C2/(LAM*math.log(1+C1/(LAM**5*L)))
def q(xs):
    xs=sorted(xs)
    if not xs: return None
    return [round(xs[0],3),round(xs[len(xs)//4],3),round(statistics.median(xs),3),round(xs[3*len(xs)//4],3),round(xs[-1],3)]
for brazo in ('a','b'):
  print('=== brazo',brazo)
  for clase in ('neg_cero','alerta_cero','control_publica','protegida_publica'):
    sel=[f for f in filas if f['clase']==clase and (clase!='neg_cero' or (f['volcan'],f['pasada_utc'],f['sensor']) in s149)]
    npx=pos=pos_hoy=0; dT_new=[]; dT_hoy=[]; nsin=0; ncalls=0; npc=[]; srcs=collections.Counter(); calls_per=collections.Counter()
    for f in sel:
        ll=f[brazo]['llamadas_fondo']; calls_per[len(ll)]+=1
        rec=f[brazo]['record']; srcs[(rec.get('final_hotspot_source'),rec.get('triggered_test1'))]+=1
        npc.append((rec.get('primary_cluster') or {}).get('n_pixels') or 0)
        # use last call (the one that publishes)
        for c in ll[-1:]:
            ncalls+=1; nsin+=c['n_sin_vecinos']
            for bth,Lh,Lh0,Ln in zip(c['bt_hot_k'],c['L_hot'],c['L_bg_hoy'],c['L_bg_nuevo']):
                npx+=1; pos+=Lh>Ln; pos_hoy+=Lh>Lh0
                dT_new.append(bth-T(Ln)); dT_hoy.append(bth-T(Lh0))
    print(clase,'n',len(sel),'pix',npx,'Lhot>Lbg_nuevo',pos,'Lhot>Lbg_hoy',pos_hoy,'sin_vecinos',nsin)
    print('   dT vs nuevo q',q(dT_new),' dT vs hoy q',q(dT_hoy))
    print('   n_pixels pc q',q(npc),' llamadas/pasada',dict(calls_per))
    print('   src',srcs.most_common(5))
