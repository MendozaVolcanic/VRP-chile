import json,collections,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
R="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
rows=json.load(open('tabla.json'))
cache={}
def rec(v,dt,s):
    if v not in cache:
        x=json.load(open(R+'data/mirova_equivalent/%s.json'%v,encoding='utf-8'));x=x['records'] if isinstance(x,dict) else x
        cache[v]={(r['datetime_utc'],r['sensor']):r for r in x}
    return cache[v][(dt,s)]
grp=collections.defaultdict(collections.Counter); n=collections.Counter()
for r in rows:
    g=('proc' if r['proc'] else 'noproc')+'/'+('igual' if r['n_s']==r['n_c'] else 'mas')
    n[g]+=1
    s=rec(r['v'],r['dt'],r['sensor'])
    for k,val in s.items():
        if val is not None: grp[g][k]+=1
    pc=s.get('primary_cluster') or {}
    for k,val in pc.items():
        if val is not None: grp[g]['pc.'+k]+=1
keys=sorted(set().union(*[set(c) for c in grp.values()]))
print('grupos',dict(n))
for k in keys:
    vals=[grp[g][k] for g in sorted(n)]
    if len(set(v/n[g] for v,g in zip(vals,sorted(n))))>1: print(k, dict(zip(sorted(n),vals)))
# month distribution
m=collections.Counter((r['dt'][:7],('proc' if r['proc'] else 'noproc'),'igual' if r['n_s']==r['n_c'] else 'mas') for r in rows)
for k in sorted(m): print(k,m[k])
