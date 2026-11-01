# S159 M: existen en CMR los granulos de las dos alertas protegidas MODIS de Chillan del #864? (sin autenticacion)
import json
import urllib.parse
import urllib.request

for g in ("MYD021KM.A2026285.0720", "MYD03.A2026285.0720", "MOD021KM.A2026288.0105", "MOD03.A2026288.0105"):
    q = urllib.parse.urlencode({"short_name": g.split(".")[0], "readable_granule_name": g + "*",
                                "options[readable_granule_name][pattern]": "true", "page_size": 10})
    d = json.load(urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?" + q, timeout=60))
    print(g, [(e["title"], e.get("time_start")) for e in d["feed"]["entry"]])
