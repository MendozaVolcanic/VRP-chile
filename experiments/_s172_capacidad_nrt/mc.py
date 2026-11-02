import json,glob,random,heapq,statistics as st
from datetime import datetime
def p(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
def m(a,b): return (p(b)-p(a)).total_seconds()/60
def pct(v,q):
    v=sorted(v); k=(len(v)-1)*q; f=int(k); c=min(f+1,len(v)-1); return v[f]+(v[c]-v[f])*(k-f)
pool=[];obs=[];ranlast=[]
for f in glob.glob('jobs/*.json'):
    d=json.load(open(f,encoding='utf-8'))
    if f.endswith('41290080234.json'): continue
    js=d['jobs']
    obs.append(m(min(j['startedAt'] for j in js),max(j['completedAt'] for j in js)))
    for j in js:
        step=[s for s in j['steps'] if 'mirova_equivalent profile' in s['name']][0]
        pool.append((m(j['startedAt'],j['completedAt']),m(step['startedAt'],step['completedAt'])))
print('runs obs',len(obs),'pool',len(pool))
print('OBS wall 11 jobs mp8: med %.1f p95 %.1f max %.1f'%(st.median(obs),pct(obs,.95),max(obs)))
print('pool job: med %.1f p95 %.1f max %.1f ; paso: med %.1f p95 %.1f max %.1f ; sobrecarga job-paso: med %.2f'%(st.median([a for a,b in pool]),pct([a for a,b in pool],.95),max(a for a,b in pool),st.median([b for a,b in pool]),pct([b for a,b in pool],.95),max(b for a,b in pool),st.median([a-b for a,b in pool])))
random.seed(172)
def sim(n_a,n_c,mp,fc=1.0,mult=1.0,N=20000):
    out=[];mx=[]
    for _ in range(N):
        durs=[]
        for i in range(n_a+n_c):
            j,s=random.choice(pool)
            f=1.0 if i<n_a else fc
            durs.append((j-s)+s*f*mult)
        # orden de matriz: Tier A primero luego chicos (peor orden para la cola: da igual en media)
        slots=[0.0]*min(mp,len(durs)); heapq.heapify(slots); end=0
        for d in durs:
            t=heapq.heappop(slots); e=t+d; end=max(end,e); heapq.heappush(slots,e)
        out.append(end); mx.append(max(durs))
    return st.median(out),pct(out,.95),pct(out,.99),pct(mx,.95),max(mx)
print('VALIDACION modelo iid, 11 jobs mp8: med %.1f p95 %.1f p99 %.1f | peor job p95 %.1f max %.1f'%sim(11,0,8))
rows=[]
for label,(na,nc,fc) in {'11 actual':(11,0,1.0),'45 (chicos=TierA)':(11,34,1.0),'45 (chicos=0,9xTierA)':(11,34,0.9)}.items():
    for mp in (8,10,15,20):
        for mult,lab in ((1.0,'K'),(1.25,'MODIS 1,25 en todo el paso')):
            if na==11 and nc==0 and mp>8: continue
            r=sim(na,nc,mp,fc,mult,N=8000)
            print('%-24s mp=%2d %-28s wall med %5.1f p95 %5.1f p99 %5.1f | peor job p95 %5.1f max %5.1f'%((label,mp,lab)+r))
print('--- extra: MODIS 1,06 (25 % del paso x 1,25) y 34 chicos solos')
for mp in (8,15,20):
    r=sim(11,34,mp,0.9,1.06,N=8000); print('45 (chicos=0,9xA) mp=%2d mult 1,06: wall med %5.1f p95 %5.1f p99 %5.1f'%((mp,)+r[:3]))
for mp in (4,6,8,10):
    for fc,lab in ((1.0,'chicos=A'),(0.9,'chicos=0,9xA')):
        r=sim(0,34,mp,fc,1.0,N=8000) if False else None
def sim34(mp,fc,N=8000):
    out=[]
    for _ in range(N):
        durs=[]
        for i in range(34):
            j,s=random.choice(pool); durs.append((j-s)+s*fc)
        slots=[0.0]*mp; heapq.heapify(slots); end=0
        for d in durs:
            t=heapq.heappop(slots); e=t+d; end=max(end,e); heapq.heappush(slots,e)
        out.append(end)
    return st.median(out),pct(out,.95),pct(out,.99)
for mp in (4,6,8,10):
    for fc in (1.0,0.9): print('34 chicos solos mp=%2d fc=%.1f: wall med %5.1f p95 %5.1f p99 %5.1f'%((mp,fc)+sim34(mp,fc)))
