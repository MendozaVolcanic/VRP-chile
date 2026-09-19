import json, collections, sys
B='ab_fus'
V=["Isluga","Lascar","Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Chaiten","Villarrica","NevadosDeChillan"]
A=["_s142_ab_control","_s142_ab_literal","_s142_ab_lit_sin_fondo","_s142_ab_lit_con_compuerta","_s142_ab_lit_sp_suelto","_s142_ab_lit_keep_peak"]
def load(a,v):
    d=json.load(open(f'{B}/s143ab-{a}-{v}/{v}.json',encoding='utf-8'))
    return {(r['datetime_utc'],r['sensor']):r for r in d['records']}
IGN={'processed_utc'}
def cmp(a1,a2):
    nrec=ndiff=0; fields=collections.Counter(); byv=collections.Counter(); sens=collections.Counter()
    for v in V:
        x,y=load(a1,v),load(a2,v)
        for k in x.keys()&y.keys():
            nrec+=1
            d=[f for f in set(x[k])|set(y[k]) if f not in IGN and x[k].get(f)!=y[k].get(f)]
            if d:
                ndiff+=1; byv[v]+=1; sens[k[1]]+=1
                for f in d: fields[f]+=1
    return nrec,ndiff,byv,sens,fields
pairs=[("_s142_ab_literal","_s142_ab_lit_sp_suelto"),("_s142_ab_control","_s142_ab_literal"),("_s142_ab_literal","_s142_ab_lit_keep_peak"),("_s142_ab_control","_s142_ab_lit_keep_peak")]
for p in pairs:
    n,nd,byv,sens,f=cmp(*p)
    print(p,'records',n,'difieren',nd); print('  por volcan',dict(byv)); print('  por sensor',dict(sens)); print('  campos',f.most_common(12))
