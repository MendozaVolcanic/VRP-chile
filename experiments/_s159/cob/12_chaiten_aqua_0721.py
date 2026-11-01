# -*- coding: utf-8 -*-
"""COB 12 (S159). Chaiten, MYD021KM 2026-07-21 08:50 UTC: unico granulo nocturno de CMR sobre algun volcan en un dia con 0 records de Aqua.
Se mide si el volcan cae dentro de la huella (geodesicas densificadas, como 08). Control: el granulo de dia-1 08:10 (con record) debe dar dentro."""
import sys, io, json, time, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np, yaml
from shapely.geometry import Polygon, Point
from pyproj import Geod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas")
v = {x["name"]: x for x in yaml.safe_load(open(WT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}["Chaiten"]
BASE = "https://cmr.earthdata.nasa.gov/search/granules.json"
d = 25 / 111.0
def pol(dia, hh):
    p = {"short_name": "MYD021KM", "version": "6.1", "temporal": f"{dia}T{hh}:00:00Z,{dia}T{hh}:59:59Z", "page_size": "20",
         "bounding_box": f"{v['lon']-d:.5f},{v['lat']-d:.5f},{v['lon']+d:.5f},{v['lat']+d:.5f}"}
    time.sleep(1)
    r = json.loads(urllib.request.urlopen(urllib.request.Request(BASE + "?" + urllib.parse.urlencode(p), headers={"User-Agent": "vrp-chile-audit-s159"}), timeout=90).read())
    return [(e["producer_granule_id"], e["time_start"], e["polygons"][0][0]) for e in r["feed"]["entry"]]
def km(txt):
    a0 = np.array(txt.split(), float).reshape(-1, 2); g = Geod(ellps="WGS84"); pts = []
    for i in range(len(a0) - 1):
        pts.append(tuple(a0[i]))
        for lo, la in g.npts(a0[i][1], a0[i][0], a0[i + 1][1], a0[i + 1][0], 60): pts.append((la, lo))
    a = np.array(pts); x = (a[:, 1] - v["lon"]) * 111.32 * math.cos(math.radians(v["lat"])); y = (a[:, 0] - v["lat"]) * 110.57
    pg = Polygon(np.c_[x, y]).buffer(0); dist = pg.exterior.distance(Point(0, 0)) if pg.geom_type == "Polygon" else pg.boundary.distance(Point(0, 0))
    return dist if pg.contains(Point(0, 0)) else -dist
for dia, hh in (("2026-07-21", "08"), ("2026-07-20", "08")):
    for pid, t0, txt in pol(dia, hh):
        print(dia, pid, t0, "km al borde (+ dentro):", round(km(txt), 1))
