# Q1: si la nota S153 de A85 (MODIS ene-jun 2026 escrito con gates intra-radio) siguiera cierta, processed_utc de esos records seria anterior a #883 (2026-10-21). Q2: instrumento muerto daria total 0 (se imprime). Control positivo: records con datetime reciente deben tener processed_utc de noviembre.
# Denominador: records MODIS de los JSON de data/mirova_equivalent a 752d348bc, datetime_utc 2026-01-01..2026-06-30.
import json,subprocess,collections
files=subprocess.run(["git","ls-tree","-r","--name-only","752d348bc","data/mirova_equivalent"],capture_output=True,text=True,check=True).stdout.split()
c=collections.Counter(); rec=collections.Counter(); tot=0
for f in files:
    if not f.endswith(".json"): continue
    d=json.loads(subprocess.run(["git","show","752d348bc:"+f],capture_output=True,check=True).stdout)
    for r in (d if isinstance(d,list) else d.get("records",[])):
        if "MODIS" not in str(r.get("sensor","")).upper(): continue
        t=str(r.get("datetime_utc")); p=str(r.get("processed_utc"))[:7]
        if "2026-01-01"<=t[:10]<="2026-06-30": c[p]+=1; tot+=1
        elif t[:10]>="2026-11-01": rec[p]+=1
print("total ene-jun 2026:",tot,dict(sorted(c.items()))); print("control reciente:",dict(rec))
