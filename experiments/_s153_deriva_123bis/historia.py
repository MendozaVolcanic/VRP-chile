# Para registros objetivo, busca por biseccion el commit en que el record alcanzo su valor actual
import json,subprocess,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
REPO="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
vol=sys.argv[1]; targets=[(a.split('|')[0],a.split('|')[1]) for a in sys.argv[2:]]
path='data/mirova_equivalent/%s.json'%vol
commits=subprocess.run(['git','-C',REPO,'log','--format=%H|%cI|%s','--',path],capture_output=True,text=True,encoding='utf-8').stdout.strip().split('\n')
commits=[c.split('|',2) for c in commits][::-1]  # viejo->nuevo
cache={}
def load(i):
    if i not in cache:
        out=subprocess.run(['git','-C',REPO,'show','%s:%s'%(commits[i][0],path)],capture_output=True)
        try:
            x=json.loads(out.stdout.decode('utf-8'))
        except Exception: x=[]
        x=x['records'] if isinstance(x,dict) else x
        cache[i]={(r.get('datetime_utc'),r.get('sensor')):r for r in x}
    return cache[i]
def sig(r):
    if r is None: return None
    return (r.get('n_anomalous_pixels'),r.get('diag_n_first_pass_pixels'),r.get('diag_n_second_pass_recapture'),r.get('product_version'),round(r.get('t_bg_k') or 0,3))
cur=load(len(commits)-1)
for t in targets:
    want=sig(cur.get(t))
    lo,hi=0,len(commits)-1
    while lo<hi:
        mid=(lo+hi)//2
        if sig(load(mid).get(t))==want: hi=mid
        else: lo=mid+1
    prev=sig(load(lo-1).get(t)) if lo>0 else None
    print(t,'actual',want,'desde',commits[lo][0][:9],commits[lo][1],commits[lo][2][:90],'| antes',prev)
