# Historia nocturna (produccion, main) cerca de cada punto diurno: cuantos records tienen un pixel anomalo a <=1 km del punto.
import sys, io, json, math
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OUT = Path("D:/vrp-trabajo/temporales/s167_diurnas_13")
def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    return 2*6371*math.asin(math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2))
ctx = json.loads((OUT/"contexto_13.json").read_text(encoding="utf-8"))
cache = {}
for c in ctx:
    vol = c["vol"]
    if vol not in cache: cache[vol] = json.loads((OUT/("prod/data/mirova_equivalent/%s.json" % vol)).read_text(encoding="utf-8"))["records"]
    recs = cache[vol]
    lat, lon = c["pixeles"][0][0], c["pixeles"][0][1]
    if c["pc_centroide_dist_rumbo"]:  # usar el pixel mas cercano al hotspot publicado
        lat, lon = min(c["pixeles"], key=lambda p: abs(p[2]-c["dist"]))[:2]
    n_tot = n_px = n_fh = 0; meses = {}; desde = None
    for r in recs:
        t = r.get("datetime_utc", "")
        if not t.startswith("2026"): continue
        n_tot += 1
        px = r.get("anomaly_pixels") or []
        if any(hav(lat, lon, p["lat"], p["lon"]) <= 1.0 for p in px if p.get("lat") is not None):
            n_px += 1; meses[t[:7]] = meses.get(t[:7], 0)+1
        if r.get("final_hotspot_lat") is not None and hav(lat, lon, r["final_hotspot_lat"], r["final_hotspot_lon"]) <= 1.0: n_fh += 1
    print("%-20s %s %-9s punto (%.4f, %.4f) %.2f km del crater | 2026 nocturno: %d records, %d con pixel anomalo a <=1 km, %d con hotspot final a <=1 km | por mes %s"
          % (vol, c["t"], c["b"], lat, lon, c["dist"], n_tot, n_px, n_fh, dict(sorted(meses.items()))))
