# -*- coding: utf-8 -*-
import json, collections, statistics as st, sys
from datetime import date, timedelta
d = json.load(open("pob_2026-09-05_2026-11-01.json", encoding="utf-8"))
D0, D1 = date(2026,9,5), date(2026,10,30)   # 56 noches = 8 semanas de 7 noches
noches = [D0+timedelta(days=i) for i in range((D1-D0).days+1)]
assert len(noches)==56
def serie(filtro):
    a = {n.isoformat(): 0 for n in noches}; dato = {n.isoformat(): 0 for n in noches}
    for o in d["pob"]:
        if o["noche"] not in a: continue
        dato[o["noche"]] += 1
        if o["clase"] in ("pos_prot","pos_bajo") and filtro(o): a[o["noche"]] += 1
    return a, dato
def pct(x,p):
    x=sorted(x); k=(len(x)-1)*p; f=int(k); c=min(f+1,len(x)-1); return x[f]+(x[c]-x[f])*(k-f)
res = {}
for nombre, f in (("todas", lambda o: True), ("sin_chillan", lambda o: o["volcan"]!="NevadosDeChillan"),
                  ("solo_tabla", lambda o: o["alerta_tabla"]),
                  ("solo_prot", lambda o: o["clase"]=="pos_prot"),
                  ("solo_chillan", lambda o: o["volcan"]=="NevadosDeChillan")):
    a, dato = serie(f)
    sem = []
    for w in range(8):
        ns = [n.isoformat() for n in noches[7*w:7*w+7]]
        sem.append({"semana": w+1, "desde": ns[0], "hasta": ns[-1], "noches_con_dato": sum(1 for n in ns if dato[n]>0),
                    "alertas": sum(a[n] for n in ns), "pasadas_pob": sum(dato[n] for n in ns),
                    "alertas_por_noche": round(sum(a[n] for n in ns)/7,2),
                    "noches_con_alguna_alerta": sum(1 for n in ns if a[n]>0)})
    v = list(a.values())
    res[nombre] = {"alertas_total": sum(v), "noches": 56, "noches_con_dato": sum(1 for n in dato if dato[n]>0),
                   "media": round(sum(v)/56,2), "mediana": st.median(v), "p10": pct(v,.1), "p90": pct(v,.9), "min": min(v), "max": max(v),
                   "semanas": sem, "serie": a}
res["dato"] = serie(lambda o: True)[1]
json.dump(res, open("series.json","w"), ensure_ascii=False, indent=1)
for k in ("todas","sin_chillan","solo_tabla","solo_prot","solo_chillan"):
    r=res[k]; print(k, {x:r[x] for x in ("alertas_total","noches_con_dato","media","mediana","p10","p90","min","max")})
    print("  por semana (alertas):", [s["alertas"] for s in r["semanas"]], "noches con dato:", [s["noches_con_dato"] for s in r["semanas"]])
print("noches sin dato:", [n for n,v in res["dato"].items() if v==0])
print("pasadas pob por noche: ", st.median(res["dato"].values()), min(res["dato"].values()), max(res["dato"].values()))
# por volcan
c=collections.Counter((o["volcan"],o["clase"]) for o in d["pob"] if o["noche"]<="2026-10-30" and o["noche"]>="2026-09-05" and o["clase"] in("pos_prot","pos_bajo"))
tot=collections.Counter()
for (v,cl),n in c.items(): tot[v]+=n
print(tot.most_common())
# meses
for mes in ("2026-09","2026-10"):
    n=sum(1 for o in d["pob"] if o["noche"].startswith(mes) and "2026-09-05"<=o["noche"]<="2026-10-30" and o["clase"] in("pos_prot","pos_bajo"))
    nch=sum(1 for o in d["pob"] if o["noche"].startswith(mes) and "2026-09-05"<=o["noche"]<="2026-10-30" and o["clase"] in("pos_prot","pos_bajo") and o["volcan"]=="NevadosDeChillan")
    print(mes,"alertas",n,"de Chillan",nch)
