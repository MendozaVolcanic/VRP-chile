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
print(len(pas), collections.Counter(p['sat'] for p in pas))
# K/mir por satelite
for s in sorted({p['sat'] for p in pas}):
    r=[p['VK']/p['mir'] for p in pas if p['sat']==s and p['K'] and p['VK'] and p['mir']>0]
    print(s,len(r),'mediana K/MIROVA',round(float(np.median(r)),3))
pares=CC.pares_por_noche(pas,'VK','K')
# satelite de cada extremo: reconstruir
idx={(p['vol'],p['hora']):p for p in pas}
def sat_of(par, k):
    for p in pas:
        if p['vol']==par['vol'] and p['hora'][:10]==par['noche'] and abs(p['z']-par['z'][k])<1e-9 and p['mir']==par['mir'][k]:
            return p['sat']
cruz=[sat_of(p,0)!=sat_of(p,1) for p in pares]
print('pares principales',len(pares),'con satelites distintos',sum(cruz))
# d principal por mismo/distinto satelite
for flag in (False,True):
    ds=[p['d'] for p,c in zip(pares,cruz) if c==flag]
    print('  satelites distintos' if flag else '  mismo satelite',len(ds),'mediana d',round(float(np.median(ds)),3))
# nulo: pares por satelite
nulo=CC.pares_nulo(pas,'VK','K')
def sat_nulo(par,k):
    for p in pas:
        if p['vol']==par['vol'] and p['hora'][:10]==par['noche'] and abs(p['z']-par['z'][k])<1e-9:
            return p['sat']
cn=[sat_nulo(p,0)!=sat_nulo(p,1) for p in nulo]
print('nulo',len(nulo),'pares con satelites distintos',sum(cn))
for flag in (False,True):
    ds=[p['d'] for p,c in zip(nulo,cn) if c==flag]
    if ds: print('  nulo', 'distintos' if flag else 'mismo', len(ds),'mediana d',round(float(np.median(ds)),3),'mediana |log d|',round(float(np.median(np.abs(np.log(ds)))),3))
# 1) simetria por construccion: mediana de d == 1 con orden al azar, sesgo de plataforma inyectado
rng=np.random.default_rng(5)
def sim(bias, reps=300):
    """K sintetico = MIROVA * (bias si satelite NOAA21 o NOAA20 else 1) * ruido; el nulo debe 'ver' el sesgo si es lo que dice."""
    falla=0
    for r in range(reps):
        q=[]
        for p in pas:
            f=bias if p['sat']!='VIIRS_SNPP' else 1.0
            q.append({**p,"K":True,"VK":p['mir']*f*math.exp(rng.normal(0,0.3))})
        res=CC.resumen(CC.pares_por_noche(q,'VK','K'),nulo=CC.pares_nulo(q,'VK','K',semilla=int(rng.integers(1,1e9))))
        if CC.veredicto(res)=="NULO SESGADO": falla+=1
    return falla/reps
for b in (1.0,0.6,0.3):
    print('sesgo de plataforma x',b,'-> NULO SESGADO en',round(sim(b),3),'de las simulaciones')
