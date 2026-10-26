import json,collections,io,sys,math
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,'..')
import curva_cenit as CC
EXC=("2026-10-12","2026-10-13","2026-10-17","2026-10-18","2026-10-19","2026-10-20")
pob=json.load(open('../../_s159/portes/poblacion_completa.json',encoding='utf-8'))['pasadas']
pas=[]
for o in pob:
    if o['b']!='VIIRS375' or o['lab']!='pos' or not o['decide'] or o['hora_utc'][:10] in EXC: continue
    vk=o.get('f5_core') if o.get('f5_core') is not None else o.get('pc_vrp')
    pas.append({"vol":o['volcan'],"hora":o['hora_utc'],"z":o['z'],"mir":o['mirova_vrp'],"K":bool(o['pub_prod']),"VK":vk,"sat":o['sensor']})
for s in sorted({p['sat'] for p in pas}):
    r=[p['VK']/p['mir'] for p in pas if p['sat']==s and p['K'] and p['VK'] and p['mir']>0]
    print(s,len(r),'mediana K/MIROVA',round(float(np.median(r)),3))
rng=np.random.default_rng(5)
def ci_nulo(q,seed):
    n=CC.pares_nulo(q,'VK','K',semilla=seed)
    d=np.array([p['d'] for p in n]); r=np.random.default_rng(seed)
    b=[np.median(d[r.integers(0,len(d),len(d))]) for _ in range(400)]
    lo,hi=np.percentile(b,[2.5,97.5]); return len(d),float(np.median(d)),lo,hi
def sim(bias,reps=150):
    falla=0;anch=[];ns=[]
    for r in range(reps):
        q=[{**p,"K":True,"VK":p['mir']*(bias if p['sat']!='VIIRS_SNPP' else 1.0)*math.exp(rng.normal(0,0.3))} for p in pas]
        n,m,lo,hi=ci_nulo(q,int(rng.integers(1,1e9)))
        falla+= not (lo<=1<=hi); anch.append(hi-lo); ns.append(n)
    return falla/reps,float(np.mean(anch)),float(np.mean(ns))
for b in (1.0,0.6,0.3):
    f,a,n=sim(b)
    print(f"sesgo de plataforma NOAA/SNPP = x{b}: NULO SESGADO en {f:.3f} de 150 simulaciones; ancho medio del IC {a:.2f}; noches del nulo {n:.0f}")
