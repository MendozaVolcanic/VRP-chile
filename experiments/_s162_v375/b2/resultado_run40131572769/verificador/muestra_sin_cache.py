import sys,json,random
sys.path.insert(0,r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375")
sys.path.insert(0,'.')
import evaluar as E
from recuento import *
V=E.volcanes()
cache=json.load(open('cache_copia.json'))
art=r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"
ids=sorted(i for i,r in b2.items() if r['estado']=='ok')
random.seed(7); samp=random.sample(ids,40)+[i for i in (3313,3515,3230,3089,3150,3537)]+list(range(5000,5004))
bad=0;badc=0
for i in samp:
    o=dict(ob['pasadas'][0]) if False else None
    o=[x for x in ob['pasadas'] if x['id']==i][0]; r=b2[i]
    rec=E.recalcular(o,r,art,V,{})
    ok=all(E.mismo(rec[b],r['port'][b]) for b in E.BR.BRAZOS)
    # contra cache
    import hashlib
    g=E.grilla_npz(art,i); k=f"{i}|{g[2]}"
    okc=all(E.mismo(rec[b],cache[k][b]) for b in E.BR.BRAZOS) if k in cache else None
    if not ok: bad+=1
    if okc is False: badc+=1
    if okc is None: print("sin cache",i)
print("muestra",len(samp),"recalculo fresco != runner:",bad,"fresco != cache:",badc)
