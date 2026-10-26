import json,collections,sys,io,datetime as D
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
H=json.load(open('historia_todos.json'))
ON=D.datetime(2026,5,28,4,44,tzinfo=D.timezone.utc); OFF=D.datetime(2026,7,1,20,46,tzinfo=D.timezone.utc)
g=[r for r in H if ON<=D.datetime.fromisoformat(r['escrito_utc'])<OFF]
c=collections.defaultdict(lambda:[0,0])
for r in g:
    c[r['v']][0]+=1; c[r['v']][1]+= r['n_c']>r['n_s']
print('gate_ON por volcan (n, con mas pixeles hoy):'); [print(' ',v,x) for v,x in sorted(c.items())]
# primer pase igual entre la version previa al gate y la guardada? (cual de los dos gates actua)
t=collections.Counter(); rec=collections.Counter()
for r in g:
    pg=r['pre_gate']
    if not pg or pg[1] is None or r['fp'] is None: continue
    t['fp igual' if pg[1]==r['fp'] else 'fp distinto']+=1
    if pg[1]==r['fp']:
        rec['hoy == fp_guardado + sp_pregate' if r['n_c']==r['fp']+pg[2] else 'no']+=1
print('primer pase, version pre-gate vs guardada:',dict(t)); print('  ',dict(rec))
# delta hoy-guardado vs recaptura guardada
import statistics as st
print('mediana sp guardada en gate_ON:',st.median(r['sp'] or 0 for r in g))
