import json, urllib.request, urllib.parse, collections
CAJA="-72.5,-39.5,-67.5,-23.0"
for prod in ["VNP02IMG","VJ102IMG","VJ202IMG","VNP02MOD","VJ102MOD","VJ202MOD"]:
    q=urllib.parse.urlencode({"short_name":prod,"bounding_box":CAJA,"page_size":2000,"temporal":"2026-10-11T00:00:00Z,2026-10-15T23:59:59Z"})
    e=json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?"+q,timeout=90))["feed"]["entry"]
    por=collections.defaultdict(list)
    for g in e: por[g["time_start"][:10]].append(g["time_start"][11:16])
    print(prod, {d:(len(v), sorted(v)) for d,v in sorted(por.items())})
