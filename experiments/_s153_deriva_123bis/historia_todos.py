# Para los 470 records de la muestra 1.17: commit de la ultima escritura (biseccion sobre la historia
# del JSON del volcan) y valor de n_anomalous_pixels antes del gate S84 (#224, 2026-05-26) y antes del flip S118 (#474, 2026-07-01).
import json,subprocess,sys,io,collections,datetime as D
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
REPO="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
rows=json.load(open('tabla.json'))
byv=collections.defaultdict(list)
for r in rows: byv[r['v']].append(r)
GATE=D.datetime(2026,5,26,17,52,19,tzinfo=D.timezone.utc)   # eb68f8c4c #224
FLIP=D.datetime(2026,7,1,20,46,0,tzinfo=D.timezone.utc)     # 92fc4412c #474
def sig(r):
    if r is None: return None
    return (r.get('n_anomalous_pixels'),r.get('diag_n_first_pass_pixels'),r.get('diag_n_second_pass_recapture'),r.get('product_version'),round(r.get('t_bg_k') or 0,3))
out=[]
for vol,rs in byv.items():
    path='data/mirova_equivalent/%s.json'%vol
    cs=subprocess.run(['git','-C',REPO,'log','--format=%H|%cI|%s','--',path],capture_output=True,text=True,encoding='utf-8').stdout.strip().split('\n')
    cs=[c.split('|',2) for c in cs][::-1]
    ts=[D.datetime.fromisoformat(c[1]).astimezone(D.timezone.utc) for c in cs]
    keys=[(r['dt'],r['sensor']) for r in rs]
    cache={}
    def load(i):
        if i not in cache:
            b=subprocess.run(['git','-C',REPO,'show','%s:%s'%(cs[i][0],path)],capture_output=True).stdout
            try: x=json.loads(b.decode('utf-8'))
            except Exception: x=[]
            x=x['records'] if isinstance(x,dict) else x
            ks=set(keys); d={}
            for rr in x:
                k=(rr.get('datetime_utc'),rr.get('sensor'))
                if k in ks: d[k]=sig(rr)
            cache[i]=d
        return cache[i]
    last=len(cs)-1
    ig=max([i for i in range(len(cs)) if ts[i]<GATE],default=None)
    ifl=max([i for i in range(len(cs)) if ts[i]<FLIP],default=None)
    for r in rs:
        k=(r['dt'],r['sensor']); want=load(last).get(k)
        lo,hi=0,last
        while lo<hi:
            mid=(lo+hi)//2
            if load(mid).get(k)==want: hi=mid
            else: lo=mid+1
        r2=dict(r); r2['escrito_commit']=cs[lo][0][:9]; r2['escrito_utc']=ts[lo].isoformat(); r2['escrito_msg']=cs[lo][2][:80]
        r2['antes']=load(lo-1).get(k) if lo>0 else None
        r2['pre_gate']=load(ig).get(k) if ig is not None else None
        r2['pre_flip']=load(ifl).get(k) if ifl is not None else None
        r2['actual']=want
        out.append(r2)
    print(vol,len(rs),'commits cargados',len(cache),flush=True)
json.dump(out,open('historia_todos.json','w'),indent=0)
