# VPR172 V-5: duracion de los jobs del run 39125546355 (reproceso K). P1: control positivo: debe haber 176 jobs 'reproc' + plan + otro.
import csv, datetime as dt, statistics as st, collections, re
rows=[]
for f in ("jobs_p1.tsv","jobs_p2.tsv"):
    for l in open(f, encoding="utf-8"):
        p=l.rstrip("\n").split("\t"); rows.append(p)
print("jobs totales", len(rows), collections.Counter(r[0].split(" ")[0] for r in rows))
rp=[r for r in rows if r[0].startswith("reproc")]
def t(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
d=[]; 
for r in rp:
    if r[2] and r[3]:
        m=(t(r[3])-t(r[2])).total_seconds()/60; d.append((m,r[1],r[0]))
print("reproc jobs", len(rp), "conclusiones", collections.Counter(x[1] for x in d))
ms=sorted(x[0] for x in d)
def pct(p): 
    k=(len(ms)-1)*p; f=int(k); c=min(f+1,len(ms)-1); return ms[f]+(ms[c]-ms[f])*(k-f)
print("min",round(ms[0],1),"mediana",round(st.median(ms),1),"p95",round(pct(.95),1),"max",round(ms[-1],1),"suma_h",round(sum(ms)/60,1))
ok=[x for x in d if x[1]=="success"]; ms2=sorted(x[0] for x in ok)
print("solo success: n",len(ok),"mediana",round(st.median(ms2),1),"p95",round(ms2[int(.95*(len(ms2)-1))],1),"max",round(ms2[-1],1), "suma_h", round(sum(ms2)/60,1))
fl=[x for x in d if x[1]!="success"]
for x in fl: print("  no success:", x)
# dias por trozo
def dias(n):
    m=re.search(r", (\d{4}-\d{2}-\d{2}), (\d{4}-\d{2}-\d{2})\)", n); 
    a,b=[dt.date.fromisoformat(x) for x in m.groups()]; return (b-a).days+1
ds=[dias(x[2]) for x in d]; print("dias por trozo: min/max/media", min(ds), max(ds), round(sum(ds)/len(ds),1), "volcan-dias total", sum(ds))
print("min por volcan-dia (suma runner/volcan-dia, sobrecarga incluida):", round(sum(ms)/sum(ds),2))
# pared
starts=[t(r[2]) for r in rp]; ends=[t(r[3]) for r in rp if r[3]]
print("pared h:", round((max(ends)-min(starts)).total_seconds()/3600,1))
# por min/volcan-dia, p95 de min por job normalizado
rate=sorted(x[0]/dias(x[2]) for x in d); print("min/volcan-dia por job: mediana",round(st.median(rate),2),"p95",round(rate[int(.95*(len(rate)-1))],2))
# proyeccion trozos de 20 dias con factor via 1.06-1.25: p95 por job
import math
for f in (1.0,1.06,1.25):
    print("factor",f,"p95 estimado 20d:", round(rate[int(.95*(len(rate)-1))]*20*f,0), "max estimado 20d:", round(rate[-1]*20*f,0))
# por volcan
byv=collections.defaultdict(list)
for x in d: byv[x[2].split(",")[0].split("(")[1]].append(x[0]/dias(x[2]))
print({k: round(st.median(v),2) for k,v in byv.items()})
