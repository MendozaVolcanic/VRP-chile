# Q1: si MODIS no corriera por la via, la fraccion via=true desde el 2026-11-02 18:00 seria 0 (la ve). Q2: instrumento muerto daria total 0 (se imprime el total).
# Control positivo: records MODIS anteriores a esa fecha tienen via None/ausente. Denominador: records MODIS con datetime_utc>=2026-11-02 18:00 en los JSON de data/mirova_equivalent a 752d348bc.
import json,subprocess,collections
files=subprocess.run(["git","ls-tree","-r","--name-only","752d348bc","data/mirova_equivalent"],capture_output=True,text=True,check=True).stdout.split()
post=collections.Counter(); pre=collections.Counter()
for f in files:
    if not f.endswith(".json"): continue
    d=json.loads(subprocess.run(["git","show","752d348bc:"+f],capture_output=True,check=True).stdout)
    recs=d if isinstance(d,list) else d.get("records",[])
    for r in recs:
        if "MODIS" not in str(r.get("sensor","")).upper(): continue
        t=str(r.get("datetime_utc"))
        (post if t>="2026-11-02 18:00" else pre)[r.get("via_codigo_mirova")]+=1
print("desde 2026-11-02 18:00:",dict(post)); print("antes:",dict(pre))
