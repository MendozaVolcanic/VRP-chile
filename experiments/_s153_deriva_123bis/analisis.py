# Cruza "cuando se escribio por ultima vez el record" con "si hoy sale con mas pixeles".
# Prediccion falsable: drift (n_c > n_s) <=> escrito con gates intra-radio ON (2026-05-28 04:44 a 2026-07-01 20:46 UTC),
# y en esos, el valor PREVIO al gate (si el record existia) es igual al de hoy.
import json,collections,sys,io,datetime as D
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
H=json.load(open('historia_todos.json'))
ON=D.datetime(2026,5,28,4,44,tzinfo=D.timezone.utc); OFF=D.datetime(2026,7,1,20,46,tzinfo=D.timezone.utc)
def reg(r):
    t=D.datetime.fromisoformat(r['escrito_utc'])
    return 'antes_gate' if t<ON else ('gate_ON' if t<OFF else 'despues_flip')
c=collections.Counter()
for r in H:
    c[(reg(r),'igual' if r['n_s']==r['n_c'] else ('mas' if r['n_c']>r['n_s'] else 'menos'))]+=1
print('regimen de escritura x resultado:'); [print(' ',k,v) for k,v in sorted(c.items())]
# test 2: pre-gate value vs C, en records escritos con gate ON que existian antes
t2=collections.Counter(); ej=[]
for r in H:
    if reg(r)!='gate_ON': continue
    pg=r['pre_gate']
    if pg is None: t2['sin version previa al gate']+=1; continue
    ok=pg[0]==r['n_c']; t2['pre_gate == hoy' if ok else 'pre_gate != hoy']+=1
    if not ok and len(ej)<15: ej.append((r['v'],r['dt'],r['sensor'][-5:],'pre',pg[0],'guard',r['n_s'],'hoy',r['n_c']))
print('test 2 (gate ON con version previa):',dict(t2)); [print('  ',e) for e in ej]
# commits que escribieron los records gate_ON
w=collections.Counter((r['escrito_commit'],r['escrito_msg'][:60]) for r in H if reg(r)=='gate_ON')
print('commits que escribieron los gate_ON:'); [print('  ',k,v) for k,v in w.most_common(15)]
print('los 8:')
for r in H:
    if r['ocho']: print('  ',r['v'],r['dt'],r['sensor'],r['n_s'],'->',r['n_c'],'| escrito',r['escrito_commit'],r['escrito_utc'][:16],r['escrito_msg'][:50],'| pre_gate',r['pre_gate'],'| antes',r['antes'])
# igual en gate_ON: por que?
print('gate_ON e igual:')
for r in H:
    if reg(r)=='gate_ON' and r['n_s']==r['n_c']: print('  ',r['v'],r['dt'],r['sensor'][-5:],r['n_s'],'fp',r['fp'],'sp',r['sp'])
print('despues_flip y mas:')
for r in H:
    if reg(r)!='gate_ON' and r['n_s']!=r['n_c']: print('  ',r['v'],r['dt'],r['sensor'][-5:],r['pv'],r['n_s'],r['n_c'],r['escrito_utc'][:16],r['escrito_msg'][:50])
