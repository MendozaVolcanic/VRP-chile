import json,glob,sys,statistics as st
from datetime import datetime
from collections import defaultdict
def p(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
def m(a,b): return (p(b)-p(a)).total_seconds()/60
def pct(v,q):
    v=sorted(v); k=(len(v)-1)*q; f=int(k); c=min(f+1,len(v)-1); return v[f]+(v[c]-v[f])*(k-f)
d_=sys.argv[1]; key=sys.argv[2]
by=defaultdict(list); walls=[]; nr=0
for f in glob.glob(d_+'/*.json'):
    d=json.load(open(f,encoding='utf-8')); 
    if not d.get('jobs'): continue
    nr+=1
    js=d['jobs']
    walls.append(m(min(j['startedAt'] for j in js),max(j['completedAt'] for j in js)))
    for j in js:
        if m(j['startedAt'],j['completedAt'])<0: continue
        for s in j['steps']:
            if key in s['name'] and s['conclusion']=='success':
                by[j['name']].append((m(s['startedAt'],s['completedAt']),m(j['startedAt'],j['completedAt'])))
print(d_,'runs',nr,'wall med %.1f p95 %.1f max %.1f'%(st.median(walls),pct(walls,.95),max(walls)))
allp=[];allj=[]
for v,x in sorted(by.items()):
    a=[i[0] for i in x];b=[i[1] for i in x]; allp+=a; allj+=b
    print('%-34s n=%2d step med %5.1f p95 %5.1f max %5.1f | job med %5.1f p95 %5.1f max %5.1f'%(v,len(a),st.median(a),pct(a,.95),max(a),st.median(b),pct(b,.95),max(b)))
print('ALL n=%d step med %.1f p95 %.1f max %.1f | job med %.1f p95 %.1f max %.1f'%(len(allp),st.median(allp),pct(allp,.95),max(allp),st.median(allj),pct(allj,.95),max(allj)))
