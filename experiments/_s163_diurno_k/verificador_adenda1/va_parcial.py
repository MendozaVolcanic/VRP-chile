# Huecos PARCIALES en CMR (dias con pocos granulos): los que la regla (a) no ve.
import json, urllib.request, urllib.parse, collections, datetime as dt
CAJA="-72.5,-39.5,-67.5,-23.0"
W={"W1":("2026-03-01","2026-03-20"),"W2":("2026-06-13","2026-06-30"),"W3":("2026-07-20","2026-07-31"),"W4":("2026-08-13","2026-08-31"),"W5":("2026-09-01","2026-09-20"),"W6":("2026-10-01","2026-10-14")}
for prod in ["VNP02IMG","VJ102IMG","VJ202IMG"]:
    for w,(d0,d1) in W.items():
        q=urllib.parse.urlencode({"short_name":prod,"bounding_box":CAJA,"page_size":2000,"temporal":f"{d0}T00:00:00Z,{d1}T23:59:59Z"})
        e=json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?"+q,timeout=90))["feed"]["entry"]
        por=collections.defaultdict(list)
        for g in e: por[g["time_start"][:10]].append(g["time_start"][11:16])
        a=dt.date.fromisoformat(d0); n=(dt.date.fromisoformat(d1)-a).days+1
        bajos=[(str(a+dt.timedelta(i)),len(por[str(a+dt.timedelta(i))])) for i in range(n) if len(por[str(a+dt.timedelta(i))])<=4]
        print(prod,w,"dias con <=4 granulos:",bajos)
