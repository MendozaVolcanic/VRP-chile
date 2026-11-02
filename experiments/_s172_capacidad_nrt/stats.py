import json,glob,statistics as st
from datetime import datetime
from collections import defaultdict
def p(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
def mins(a,b): return (p(b)-p(a)).total_seconds()/60
def pct(v,q):
    v=sorted(v); k=(len(v)-1)*q; f=int(k); c=min(f+1,len(v)-1); return v[f]+(v[c]-v[f])*(k-f)
runs=[]
for f in [x for x in glob.glob('jobs/*.json') if not x.endswith('41290080234.json')]:
    d=json.load(open(f,encoding='utf-8')); d['id']=__import__('os').path.basename(f)[:-5]; runs.append(d)
runs.sort(key=lambda d:d['createdAt'])
print('n runs',len(runs),runs[0]['createdAt'],'->',runs[-1]['updatedAt'])
from collections import Counter
print(Counter(len(d['jobs']) for d in runs), Counter(d['event'] for d in runs))
byv=defaultdict(lambda:{'job':[],'pipe':[],'co':[],'wait':[]})
wall=[];lastjobstart=[]
for d in runs:
    js=d['jobs']
    st0=min(p(j['startedAt']) for j in js); en=max(p(j['completedAt']) for j in js)
    wall.append((en-st0).total_seconds()/60)
    starts=sorted(p(j['startedAt']) for j in js)
    lastjobstart.append((starts[-1]-starts[0]).total_seconds()/60)
    for j in js:
        v=j['name'][len('process ('):-1]
        byv[v]['job'].append(mins(j['startedAt'],j['completedAt']))
        for s in j['steps']:
            if 'mirova_equivalent profile' in s['name']:
                byv[v]['pipe'].append(mins(s['startedAt'],s['completedAt']))
            if s['name']=='Checkout repository': byv[v]['co'].append(mins(s['startedAt'],s['completedAt']))
print('%-22s %3s %6s %6s %6s %6s | %6s %6s %6s'%('vol','n','jmed','jp95','jmax','jmin','pmed','pp95','pmax'))
alljob=[];allpipe=[]
for v,x in sorted(byv.items(), key=lambda kv:-st.median(kv[1]['job'])):
    j=x['job'];q=x['pipe']; alljob+=j; allpipe+=q
    print('%-22s %3d %6.1f %6.1f %6.1f %6.1f | %6.1f %6.1f %6.1f'%(v,len(j),st.median(j),pct(j,.95),max(j),min(j),st.median(q),pct(q,.95),max(q)))
print('ALL jobs n',len(alljob),'med %.1f p95 %.1f max %.1f'%(st.median(alljob),pct(alljob,.95),max(alljob)))
print('ALL pipe n',len(allpipe),'med %.1f p95 %.1f max %.1f'%(st.median(allpipe),pct(allpipe,.95),max(allpipe)))
print('wall run: med %.1f p95 %.1f max %.1f min %.1f n %d'%(st.median(wall),pct(wall,.95),max(wall),min(wall),len(wall)))
print('start spread last-first job: med %.1f p95 %.1f max %.1f'%(st.median(lastjobstart),pct(lastjobstart,.95),max(lastjobstart)))
co=[c for x in byv.values() for c in x['co']]; print('checkout med %.2f p95 %.2f'%(st.median(co),pct(co,.95)))
json.dump({v:x for v,x in byv.items()},open('byv.json','w'))
# per run table
for d in runs:
    js=d['jobs']; st0=min(p(j['startedAt']) for j in js); en=max(p(j['completedAt']) for j in js)
    print(d['id'],d['event'][:5],d['createdAt'][5:16],'wall %.1f'%((en-st0).total_seconds()/60),'maxjob %.1f'%max(mins(j['startedAt'],j['completedAt']) for j in js))
