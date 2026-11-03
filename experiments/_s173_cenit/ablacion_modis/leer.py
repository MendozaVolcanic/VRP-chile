import json, sys, random, numpy as np
from scipy.stats import spearmanr
d=json.load(open(sys.argv[1],encoding='utf-8'))
P=[e for e in d['pasadas'] if e.get('estado')=='ok']
print('n ok',len(P),'V0=V',sum(e['control_V0_igual_V'] for e in P),'dif campo vacia',sum(e['control_produccion_dif']==[] for e in P))
def val(e,b):
    if b=='K': x=e['K']['pc_vrp_mw']
    elif b=='V': x=e['V']['pc_vrp_mw']
    else:
        br=e['brazos'][b]; x=br.get('pc_vrp_mw', br.get('vrp_mw'))
    return 0.0 if x is None else x
arms=['K','V','V0','X2','FA','FSH','SC','FA_SC','RN','G5','NAT','NAT_AREA']
z=np.array([e['z_record'] for e in P]); m=np.array([e['vrp_mirova_mw'] for e in P])
rng=random.Random(173)
print('n bajo30',(z<30).sum(),'sobre30',(z>=30).sum())
for b in arms:
    r=np.array([val(e,b) for e in P])/m
    lo,hi=np.median(r[z<30]),np.median(r[z>=30])
    rho=spearmanr(z,r).correlation
    null=[]
    for _ in range(200):
        zz=list(z); rng.shuffle(zz); null.append(spearmanr(zz,r).correlation)
    q=np.percentile(null,[2.5,97.5])
    pub=sum(((e['brazos'][b]['publica'] or 0) if b in e['brazos'] else (e['K_publica'] if b=='K' else e['V_publica'])) for e in P)
    ceros=int((r==0).sum())
    print(f"{b:9s} bajo {lo:6.3f} sobre {hi:6.3f} rho {rho:+.3f} nulo [{q[0]:+.2f},{q[1]:+.2f}] publica {pub}/27 ceros {ceros}")
