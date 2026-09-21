# -*- coding: utf-8 -*-
import json, random, collections, statistics, sys
recs=json.load(open(sys.argv[1],encoding="utf-8"))
def R(sel): 
    n=len(sel); return (sum(r["pub"] for r in sel), n)
print("== 1. Puede el AZAR pasar el piso de recall C1? (adelgazado uniforme al azar) ==")
print("Se apaga cada publicacion del control con prob (1-p) SIN mirar la etiqueta.")
for b,piso,techo in (("VIIRS375",0.825,0.45),("VIIRS750",0.667,0.12)):
    pos=[r for r in recs if r["b"]==b and r["lab"]=="pos"]
    neg=[r for r in recs if r["b"]==b and r["lab"]=="neg_limpio"]
    print(" %s control: recall %d/%d=%.3f  tasa_neg %d/%d=%.3f"%(b,*R(pos),R(pos)[0]/R(pos)[1],*R(neg),R(neg)[0]/R(neg)[1]))
    for p in (0.9,0.7,0.5,0.4,0.3):
        rnd=random.Random(146); rec_ok=0; c3_ok=0; ambos=0
        for _ in range(2000):
            rp=sum(1 for r in pos if r["pub"] and rnd.random()<p)
            rn=sum(1 for r in neg if r["pub"] and rnd.random()<p)
            a=rp/len(pos)>=piso; c=rn/len(neg)<=techo
            rec_ok+=a; c3_ok+=c; ambos+= (a and c)
        print("   p=%.1f -> pasa C1 %.1f%% | pasa C3 %.1f%% | pasa AMBOS %.1f%%"%(p,100*rec_ok/2000,100*c3_ok/2000,100*ambos/2000))
print()
print("== 2. La vara de NOCHE con un brazo que apaga al azar (contra-argumento del doc) ==")
nv=collections.defaultdict(list)
for r in recs: nv[(r["vol"],r["noche"])].append(r)
noches_pos=[v for v in nv.values() if any(x["lab"]=="pos" for x in v)]
print(" noches con alerta:",len(noches_pos))
for p in (0.9,0.5,0.3,0.15):
    rnd=random.Random(146); tot=0
    for _ in range(500):
        tot+=sum(1 for v in noches_pos if any(x["pub"] and rnd.random()<p for x in v))
    print("   p=%.2f -> noches conservadas, media %.2f de %d"%(p,tot/500,len(noches_pos)))
print()
print("== 3. C4: cuantos estratos volcan|sensor tienen n>=5 pares (control) ==")
g=collections.defaultdict(list)
for r in recs:
    if r["lab"]=="pos" and r["pub"] and r.get("vrp_ref"): g[(r["vol"],r["b"])].append(r)
for k,v in sorted(g.items(), key=lambda kv:-len(kv[1])):
    print("   %-28s n=%d %s"%("|".join(k),len(v),"<-- CUENTA (n>=5)" if len(v)>=5 else ""))
tot=collections.Counter()
for k,v in g.items(): tot[k[1]]+=len(v)
print("   agregados TODOS|<sensor>:",dict(tot))
print("   estratos por volcan con n>=5:",sum(1 for v in g.values() if len(v)>=5))
