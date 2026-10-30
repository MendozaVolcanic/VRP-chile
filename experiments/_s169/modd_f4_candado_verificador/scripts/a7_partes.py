# P1: si alguna parte tuviera muchisimas mas pasadas que otra (y no cupiera en 240 min), lo veria: cuento pasadas y granulos por parte desde poblacion_f4.json.
import json, collections
p=json.load(open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/poblacion_f4.json',encoding='utf-8'))
cl=lambda x: x.get('clave') or '.'.join(str(x.get('l1b') or '').split('.')[:3])
par={}
for i,pt in enumerate(p['partes']):
    for c in pt: par[c]=i
n=collections.Counter(par[cl(x)] for x in p['pasadas'])
g=collections.Counter(i for c,i in par.items())
print('pasadas por parte min/max', min(n.values()), max(n.values()), 'total', sum(n.values()))
print('granulos por parte min/max', min(g.values()), max(g.values()))
print('partes por tanda t1/t2/t3 (pasadas):', sum(n[i] for i in range(0,8)), sum(n[i] for i in range(8,16)), sum(n[i] for i in range(16,24)))
print('peor parte a 9 s/pasada (min):', max(n.values())*9/60, ' con 3x:', max(n.values())*27/60)
# humo: numero de granulos distintos
S={(x['vol'],x['dt']):x for x in p['pasadas']}
H=[tuple(s.strip() for s in l.split('#',1)[0].split('|')) for l in open('D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/humo_f4.txt',encoding='utf-8') if l.split('#',1)[0].strip()]
print('humo granulos', len({cl(S[h]) for h in H}), 'pasadas', len(H))
