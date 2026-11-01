"""Verifica el comentario de frontend/index.html:1624 «con K (#850) todos los records son ctx_cluster».
Cuenta, entre records procesados despues del merge de #850, los que tienen final_hotspot_source != ctx_cluster
y hotspot no nulo, con volcan, sensor, distance_class, distancia del final_hotspot y del anomaly_pixels[0], y pc.vrp_mw.
P1: si el comentario fuera falso, aparecen records 'eruption' (u otro) con hotspot.
P2: control: el total de ctx_cluster debe coincidir con efecto_k_en_datos.out (531)."""
import json, glob
from math import radians, sin, cos, asin, sqrt
CUT = "2026-10-18T09:57:30"
def hav(a, b, c, d):
    a, b, c, d = map(radians, (a, b, c, d)); h = sin((c-a)/2)**2 + cos(a)*cos(c)*sin((d-b)/2)**2
    return 2*6371*asin(sqrt(h))
n_ctx = 0; rows = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    d = json.load(open(f, encoding="utf-8")); v = f.split("\\")[-1].split("/")[-1][:-5]
    for r in d.get("records", []):
        if str(r.get("processed_utc") or "") < CUT: continue
        s = r.get("final_hotspot_source")
        if s == "ctx_cluster": n_ctx += 1
        elif s is not None:
            ap = (r.get("anomaly_pixels") or [{}])[0]
            dap = None
            if ap.get("lat") is not None and r.get("final_hotspot_lat") is not None:
                dap = round(hav(r["final_hotspot_lat"], r["final_hotspot_lon"], ap["lat"], ap["lon"]), 2)
            pc = r.get("primary_cluster") or {}
            rows.append((v, r["sensor"], r["datetime_utc"], s, r.get("distance_class"), r.get("final_hotspot_dist_km"), dap, pc.get("vrp_mw")))
print("ctx_cluster:", n_ctx, "| otras fuentes con hotspot:", len(rows))
from collections import Counter
print(Counter((x[0], x[1], x[4]) for x in rows))
for x in rows[:30]: print(x)
