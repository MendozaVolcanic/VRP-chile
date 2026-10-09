import json, glob, re, statistics as st
from datetime import datetime, timezone, timedelta
rows=[]
for f in glob.glob('vrp/*.json'):
    d=json.load(open(f)); v=d['volcano'] if 'volcano' in d else f
    for r in d['records']:
        if not r.get('processed_utc'): continue
        acq=datetime.strptime(r['datetime_utc'],'%Y-%m-%d %H:%M')
        pr=datetime.strptime(r['processed_utc'],'%Y-%m-%dT%H:%M:%SZ')
        g=r.get('granule','') or ''
        m=re.search(r'\.(\d{7})(\d{6})\.(NRT\.)?(hdf|nc|h5)',g)
        m2=re.search(r'\.(\d{13})\.',g)
        prod=None
        mm=re.findall(r'\.(\d{13})\.',g)
        if mm:
            s=mm[-1]; prod=datetime.strptime(s[:7],'%Y%j')+timedelta(hours=int(s[7:9]),minutes=int(s[9:11]),seconds=int(s[11:13]))
        rows.append(dict(v=v,s=r.get('sensor'),acq=acq,pr=pr,prod=prod,pv=r.get('product_version'),g=g,vrp=r.get('vrp_mw') or 0,dc=r.get('distance_class')))
print('records con processed_utc:',len(rows))
from collections import Counter
print(Counter(r['pv'] for r in rows)); print(Counter(r['s'] for r in rows))
print('acq min/max',min(r['acq'] for r in rows),max(r['acq'] for r in rows))
print('proc min/max',min(r['pr'] for r in rows),max(r['pr'] for r in rows))
for r in rows[:3]: print(r['g'])
def h(x): return x.total_seconds()/3600
def q(xs):
    xs=sorted(xs); n=len(xs)
    return f"n={n} med={st.median(xs):.2f}h p10={xs[int(.1*n)]:.2f} p90={xs[int(.9*n)]:.2f} min={xs[0]:.2f} max={xs[-1]:.2f}"
nrt=[r for r in rows if r['pv']=='nrt' and r['acq']>=datetime(2026,9,2)]
print('NRT desde 2-sep', len(nrt))
lat=[h(r['pr']-r['acq']) for r in nrt]
print('proc-acq total:',q(lat))
print('  <=48h:',q([x for x in lat if x<=48]))
for s in sorted(set(r['s'] for r in nrt)):
    xs=[h(r['pr']-r['acq']) for r in nrt if r['s']==s and h(r['pr']-r['acq'])<=48]
    ys=[h(r['prod']-r['acq']) for r in nrt if r['s']==s and r['prod']]
    zs=[h(r['pr']-r['prod']) for r in nrt if r['s']==s and r['prod'] and h(r['pr']-r['acq'])<=48]
    print(s,'proc-acq',q(xs)); 
    if ys: print('   NASAprod-acq',q(ys)); print('   proc-NASAprod',q(zs))
json.dump([dict(v=r['v'],s=r['s'],acq=str(r['acq']),pr=str(r['pr']),vrp=r['vrp'],dc=r['dc']) for r in nrt],open('vrp_nrt.json','w'))
