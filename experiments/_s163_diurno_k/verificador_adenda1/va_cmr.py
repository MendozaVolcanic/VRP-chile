# Verificador adenda 1: consulta propia a CMR (independiente del script verificado).
import json, urllib.request, urllib.parse, collections, datetime as dt, sys, time
CAJA="-72.5,-39.5,-67.5,-23.0"
W={"W1":("2026-03-01","2026-03-20"),"W2":("2026-06-13","2026-06-30"),"W3":("2026-07-20","2026-07-31"),
   "W4":("2026-08-13","2026-08-31"),"W5":("2026-09-01","2026-09-20"),"W6":("2026-10-01","2026-10-14")}
PRODS={"VNP02IMG":"2","VJ102IMG":"2.1","VJ202IMG":"2.1","VNP02MOD":"2","VJ102MOD":"2.1","VJ202MOD":"2.1"}
def consulta(short, d0, d1, version=None):
    c=collections.Counter(); vers=collections.Counter(); p=1; tot=0
    while True:
        q={"short_name":short,"bounding_box":CAJA,"page_size":2000,"temporal":f"{d0}T00:00:00Z,{d1}T23:59:59Z","page_num":p}
        if version: q["version"]=version
        r=json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?"+urllib.parse.urlencode(q),timeout=90))
        e=r["feed"]["entry"]
        for g in e:
            c[g["time_start"][:10]]+=1; vers[g.get("version_id")]+=1
        tot+=len(e)
        if len(e)<2000: break
        p+=1
    return c,vers,tot
def dias(d0,d1):
    a=dt.date.fromisoformat(d0); n=(dt.date.fromisoformat(d1)-a).days+1
    return [(a+dt.timedelta(i)).isoformat() for i in range(n)]
print("hora UTC", dt.datetime.now(dt.timezone.utc).isoformat())
for prod,ver in PRODS.items():
    for w,(d0,d1) in W.items():
        c1,v1,t1=consulta(prod,d0,d1,ver)
        c0,v0,t0=consulta(prod,d0,d1,None)
        v1d=[d for d in dias(d0,d1) if not c1[d]]
        v0d=[d for d in dias(d0,d1) if not c0[d]]
        print(prod,w,"con_version",t1,"vacios",v1d,"| sin_version",t0,"vacios",v0d,"versiones",dict(v0), "min/max por dia", (min(c0[d] for d in dias(d0,d1)), max(c0[d] for d in dias(d0,d1))))
