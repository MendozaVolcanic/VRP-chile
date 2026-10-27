# Contexto: en los datos de produccion (data/mirova_equivalent, noche) de las ventanas W2 a W6, ¿cuantos (volcan, plataforma, dia) no tienen ningun record?
import json, glob, collections, datetime as dt, os
R=os.path.join("..","..","..","data","mirova_equivalent")
W={"W2":("2026-06-13","2026-06-30"),"W3":("2026-07-20","2026-07-31"),"W4":("2026-08-13","2026-08-31"),"W5":("2026-09-01","2026-09-20"),"W6":("2026-10-01","2026-10-14")}
VOLS=['Lascar','Lastarria','Isluga','Tupungatito','PlanchonPeteroa','NevadosDeChillan','Llaima','Villarrica','Copahue','PuyehueCordonCaulle','Chaiten']
SENS=['VIIRS_SNPP','VIIRS_NOAA20','VIIRS_NOAA21','VIIRS_SNPP_750','VIIRS_NOAA20_750','VIIRS_NOAA21_750']
tiene=collections.defaultdict(set)
for v in VOLS:
    d=json.load(open(os.path.join(R,v+".json"),encoding="utf-8"))
    for r in d["records"]:
        tiene[(v,r["sensor"])].add(r["datetime_utc"][:10])
def dias(a,b):
    x=dt.date.fromisoformat(a); return [(x+dt.timedelta(i)).isoformat() for i in range((dt.date.fromisoformat(b)-x).days+1)]
tot=0; falt=collections.defaultdict(list)
for w,(a,b) in W.items():
    for v in VOLS:
        for s in SENS:
            for d in dias(a,b):
                tot+=1
                if d not in tiene[(v,s)]: falt[(w,s)].append((v,d))
print("triples (volcan, plataforma, dia):", tot, "| sin ningun record:", sum(len(x) for x in falt.values()))
for k,v in sorted(falt.items()): print(k, len(v), v[:6])
# dias en que NINGUN volcan tiene record de una plataforma (lo que (b') pediria)
for w,(a,b) in W.items():
    for s in SENS:
        sin=[d for d in dias(a,b) if not any(d in tiene[(v,s)] for v in VOLS)]
        if sin: print("(b') sin ningun record de",s,w,sin)
