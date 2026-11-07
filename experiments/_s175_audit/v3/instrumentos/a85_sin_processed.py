# Q1: los 518 records MODIS ene-jun 2026 sin processed_utc: tienen otra marca de vintage (first_processed_utc, regimen)? Q2: total 0 si el instrumento esta muerto (se imprime).
# Denominador: MODIS datetime_utc 2026-01-01..2026-06-30, JSON de data/mirova_equivalent a 752d348bc, sin processed_utc.
import json,subprocess,collections
files=subprocess.run(["git","ls-tree","-r","--name-only","752d348bc","data/mirova_equivalent"],capture_output=True,text=True,check=True).stdout.split()
byv=collections.Counter(); fp=collections.Counter(); reg=collections.Counter(); sn=collections.Counter(); keys=collections.Counter(); n=0
for f in files:
    if not f.endswith(".json"): continue
    d=json.loads(subprocess.run(["git","show","752d348bc:"+f],capture_output=True,check=True).stdout)
    for r in (d if isinstance(d,list) else d.get("records",[])):
        if "MODIS" not in str(r.get("sensor","")).upper(): continue
        t=str(r.get("datetime_utc"))
        if not ("2026-01-01"<=t[:10]<="2026-06-30"): continue
        if r.get("processed_utc"): continue
        n+=1; fp[str(r.get("first_processed_utc"))[:7]]+=1; reg[str(r.get("regimen"))]+=1; sn[f.split('/')[-1]]+=1
        keys[tuple(sorted(r.keys()))[:0]]+=1
print("sin processed_utc:",n); print("first_processed_utc:",dict(fp)); print("regimen:",dict(reg)); print("por archivo:",dict(sn))
