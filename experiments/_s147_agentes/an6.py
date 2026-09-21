# -*- coding: utf-8 -*-
"""El barajado de poder_recall.py rompe la estructura de NOCHE. Se mide que pasa si se preserva."""
import json, random, collections, sys
recs=json.load(open(sys.argv[1],encoding="utf-8"))
def varas(rs):
    out={}
    g=collections.defaultdict(list)
    for r in rs: g[(r["vol"],r["noche"])].append(r)
    n1=[v for v in g.values() if any(x["lab"]=="pos" for x in v)]
    out["noche_volcan"]=(sum(any(x["pub"] for x in v) for v in n1),len(n1))
    g2=collections.defaultdict(list)
    for r in rs: g2[(r["vol"],r["b"],r["noche"])].append(r)
    n2=[v for v in g2.values() if any(x["lab"]=="pos" for x in v)]
    for b in ("VIIRS375","VIIRS750"):
        sub=[v for v in n2 if v[0]["b"]==b]
        out["noche_sensor_"+b]=(sum(any(x["pub"] for x in v) for v in sub),len(sub))
        pos=[r for r in rs if r["lab"]=="pos" and r["b"]==b]
        out["pasada_"+b]=(sum(r["pub"] for r in pos),len(pos))
    return out
obs=varas(recs)
guardado=[r["pub"] for r in recs]

def correr(modo,n=200,semilla=146):
    rnd=random.Random(semilla); acum=collections.defaultdict(list)
    if modo=="record":   # el de poder_recall.py: baraja el vector pub dentro de (vol,sensor)
        grupos=collections.defaultdict(list)
        for i,r in enumerate(recs): grupos[(r["vol"],r["b"])].append(i)
    else:                # preserva la NOCHE: baraja BLOQUES de noche dentro de (vol,sensor)
        grupos=collections.defaultdict(lambda: collections.defaultdict(list))
        for i,r in enumerate(recs): grupos[(r["vol"],r["b"])][r["noche"]].append(i)
    for _ in range(n):
        if modo=="record":
            for idxs in grupos.values():
                vals=[recs[i]["pub"] for i in idxs]; rnd.shuffle(vals)
                for i,v in zip(idxs,vals): recs[i]["pub"]=v
        else:
            for noches in grupos.values():
                claves=list(noches); bloques=[[recs[i]["pub"] for i in noches[k]] for k in claves]
                rnd.shuffle(bloques)
                for k,bl in zip(claves,bloques):
                    idxs=noches[k]
                    # bloques de distinto largo: se recicla ciclicamente, preservando el patron
                    for j,i in enumerate(idxs): recs[i]["pub"]=bl[j%len(bl)]
        for k,(num,den) in varas(recs).items(): acum[k].append(num)
    for r,p in zip(recs,guardado): r["pub"]=p
    return acum
for modo,titulo in (("record","A. barajado POR RECORD (el que usa poder_recall.py)"),
                    ("noche","B. barajado POR BLOQUE DE NOCHE (preserva la correlacion intra-noche)")):
    ac=correr(modo)
    print(titulo)
    for k,(num,den) in obs.items():
        xs=sorted(ac[k]); alc=sum(1 for x in xs if x>=num)/len(xs)
        print("   %-24s obs %3d/%3d | nulo med %3d  min %3d max %3d | alcanza %.3f -> %s"%(
            k,num,den,xs[len(xs)//2],xs[0],xs[-1],alc,
            "NO DISCRIMINA" if alc>=0.5 else ("DEBIL" if alc>=0.05 else "DISCRIMINA")))
