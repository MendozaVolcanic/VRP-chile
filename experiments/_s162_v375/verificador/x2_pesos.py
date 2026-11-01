import json,collections,math,io,sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
o=json.load(open('../objetivos_v375_bc.json',encoding='utf-8'))
meta=o['meta']['estratos']
for c in ('pos_prot','pos_bajo','neg_pub','neg_resto'):
    est=meta[c]; N=sum(v['N'] for v in est.values())
    sin_nuevo=[(h,v['N'],v['n_s159']) for h,v in est.items() if v['n_nuevo']==0 and v['N']>0]
    N_sin=sum(x[1] for x in sin_nuevo)
    w=[v['N']/(v['n_s159']+v['n_nuevo']) for v in est.values() if v['n_s159']+v['n_nuevo']]
    n=[(v['n_s159']+v['n_nuevo']) for v in est.values()]
    # Kish sobre pasadas
    ws=[]
    for v in est.values():
        k=v['n_s159']+v['n_nuevo']
        ws+= [v['N']/k]*k if k else []
    kish=sum(ws)**2/sum(x*x for x in ws)
    print(c,'N',N,'estratos',len(est),'sin pasada nueva:',len(sin_nuevo),'N en ellos',N_sin, 'frac',round(N_sin/N,3),'n union total',sum(n),'Kish',round(kish,1))
    # solo S162: n_nuevo
    ws=[]
    for v in est.values():
        k=v['n_nuevo']
        ws+= [v['N']/k]*k if k else []
    if ws: print('   S162 solo: pasadas',len(ws),'Kish',round(sum(ws)**2/sum(x*x for x in ws),1),'N representado',round(sum(v['N'] for v in est.values() if v['n_nuevo']),0),'de',N)
    if c=='neg_resto':
        print('   estratos con N<=20:',[(h,v['N'],v['n_s159'],v['n_nuevo']) for h,v in est.items() if v['N']<=20])
        print('   n union min/max',min(n),max(n))
