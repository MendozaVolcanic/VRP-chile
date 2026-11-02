import json,glob,statistics as st,yaml
from datetime import datetime
from collections import defaultdict,Counter
def p(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
def m(a,b): return (p(b)-p(a)).total_seconds()/60
def pct(v,q):
    v=sorted(v); k=(len(v)-1)*q; f=int(k); c=min(f+1,len(v)-1); return v[f]+(v[c]-v[f])*(k-f)
d=yaml.safe_load(open('volcanoes.yaml',encoding='utf-8')); vv=d['volcanoes'] if isinstance(d,dict) else d
tierA={x['name'] for x in vv if x.get('mirova_monitored')}
rec=[]
for f in glob.glob('jobs_old/*.json'):
    try: r=json.load(open(f,encoding='utf-8'))
    except Exception: continue
    if not r.get('jobs'): continue
    rec.append(r)
rec.sort(key=lambda r:r['createdAt'])
print('runs',len(rec),rec[0]['createdAt'],rec[-1]['createdAt'],Counter(len(r['jobs']) for r in rec))
# Mantener runs con 45 jobs
full=[r for r in rec if len(r['jobs'])==45]
print('runs con 45 jobs',len(full), full[0]['createdAt'] if full else '', full[-1]['createdAt'] if full else '')
exp=defaultdict(list); mir=defaultdict(list); job=defaultdict(list); concl=Counter(); walls=[]; fails=defaultdict(int)
for r in full:
    js=r['jobs']
    st0=min(j['startedAt'] for j in js); en=max(j['completedAt'] for j in js)
    walls.append((m(r['createdAt'],en), m(st0,en)))
    for j in js:
        v=j['name'][len('process ('):-1]
        concl[j['conclusion']]+=1
        if j['conclusion']!='success': fails[v]+=1; continue
        jm=m(j['startedAt'],j['completedAt'])
        if jm<0: continue
        job[v].append(jm)
        for s in j['steps']:
            if s['conclusion']!='success' or s['startedAt']==s['completedAt']: continue
            if 'experimental profile' in s['name']: exp[v].append(m(s['startedAt'],s['completedAt']))
            elif 'mirova_equivalent profile' in s['name']: mir[v].append(m(s['startedAt'],s['completedAt']))
print('job conclusions',concl)
print('wall createdAt->end med %.0f p95 %.0f max %.0f ; first-start->end med %.0f p95 %.0f max %.0f'%(st.median([w[0] for w in walls]),pct([w[0] for w in walls],.95),max(w[0] for w in walls),st.median([w[1] for w in walls]),pct([w[1] for w in walls],.95),max(w[1] for w in walls)))
def grp(name,dic,names):
    a=[x for v in names for x in dic.get(v,[])]
    if a: print('%-34s n=%4d med %5.1f p95 %5.1f max %5.1f'%(name,len(a),st.median(a),pct(a,.95),max(a)))
chicos=[v for v in job if v not in tierA]
grp('experimental step 34 chicos',exp,chicos); grp('experimental step 11 TierA',exp,list(tierA))
grp('job completo 34 chicos',job,chicos); grp('job completo 11 TierA',job,list(tierA))
grp('mirova_equiv step TierA',mir,list(tierA))
print('fallos por volcan (n jobs no success):',sum(fails.values()),'en',len(full)*45)
print('fallos chicos',sum(v for k,v in fails.items() if k not in tierA),'TierA',sum(v for k,v in fails.items() if k in tierA))
lat={x['name']:abs(x['lat']) for x in vv}
rows=[]
for v in sorted(job,key=lambda v:lat[v]):
    if v in exp: rows.append((v,lat[v],st.median(exp[v]),pct(exp[v],.95),len(exp[v])))
json.dump(rows,open('old_rows.json','w'))
for r in rows: print('%-24s lat %4.1f exp med %5.1f p95 %5.1f n %d %s'%(r[0],r[1],r[2],r[3],r[4],'A' if r[0] in tierA else ''))
print('--- extra')
w=[x[1] for x in walls]
print('runs wall(first start->end) >120:',sum(1 for x in w if x>120),'de',len(w),'; >150:',sum(1 for x in w if x>150))
to=0;tot=0;failstep=Counter();tochic=0
for r in full:
    for j in r['jobs']:
        if j['conclusion']=='failure':
            tot+=1
            dur=m(j['startedAt'],j['completedAt'])
            if dur>=59: to+=1
            fs=[s['name'][:45] for s in j['steps'] if s['conclusion']=='failure']
            failstep[fs[0] if fs else 'sin paso']+=1
print('jobs failure',tot,'con duracion>=59 min (timeout job 60):',to)
print(failstep.most_common(6))
# por mes
bym=defaultdict(lambda:[0,0])
for r in full:
    for j in r['jobs']:
        bym[r['createdAt'][:7]][0]+=1
        if j['conclusion']!='success': bym[r['createdAt'][:7]][1]+=1
print({k:(v[1],v[0],round(100*v[1]/v[0],1)) for k,v in bym.items()})
