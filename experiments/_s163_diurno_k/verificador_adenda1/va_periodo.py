# Huecos de un PERIODO entero (noche UTC 03-09 o dia 16-21) en CMR, para las ventanas W1 a W6 (lo que la regla (a), de dia entero, no ve)
import json, urllib.request, urllib.parse, collections, datetime as dt
CAJA="-72.5,-39.5,-67.5,-23.0"
W={"W1":("2026-03-01","2026-03-20"),"W2":("2026-06-13","2026-06-30"),"W3":("2026-07-20","2026-07-31"),"W4":("2026-08-13","2026-08-31"),"W5":("2026-09-01","2026-09-20"),"W6":("2026-10-01","2026-10-14")}
for prod in ["VNP02IMG","VJ102IMG","VJ202IMG"]:
    for w,(d0,d1) in W.items():
        q=urllib.parse.urlencode({"short_name":prod,"bounding_box":CAJA,"page_size":2000,"temporal":f"{d0}T00:00:00Z,{d1}T23:59:59Z"})
        e=json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?"+q,timeout=90))["feed"]["entry"]
        n=collections.defaultdict(lambda:[0,0])
        for g in e:
            h=int(g["time_start"][11:13])
            if 3<=h<=9: n[g["time_start"][:10]][0]+=1
            elif 16<=h<=21: n[g["time_start"][:10]][1]+=1
        a=dt.date.fromisoformat(d0); N=(dt.date.fromisoformat(d1)-a).days+1
        sinN=[str(a+dt.timedelta(i)) for i in range(N) if n[str(a+dt.timedelta(i))][0]==0]
        sinD=[str(a+dt.timedelta(i)) for i in range(N) if n[str(a+dt.timedelta(i))][1]==0]
        print(prod,w,"dias sin granulos de NOCHE:",sinN,"| sin granulos de DIA:",sinD)
