# Verificador S156: pixeles de la sombra (VIIRS750 y 375) y de K (375) en PCC 2026-10-10 05:54: distancia al
# punto de volcanoes.yaml y al vent, para saber si lo que publica la sombra esta cerca de los 7,8 km de MIROVA.
# (Sin acimut de MIROVA, A93: solo radio; la posicion del objeto es tema del agente a61.)
import json, math, sys, yaml
from pathlib import Path
W = Path(sys.argv[1])
v = [x for x in yaml.safe_load(open(W/"volcanoes.yaml", encoding="utf-8"))["volcanoes"] if x["name"] == "PuyehueCordonCaulle"][0]
print({k: v.get(k) for k in ("lat", "lon", "vent_lat", "vent_lon", "inner_radius_km", "radius_km", "mirova_center")})
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp = p2 - p1; dl = math.radians(d - b)
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
for sub, sens in (("experimental_v2", "VIIRS_NOAA21_750"), ("experimental_v2", "VIIRS_NOAA21"), ("mirova_equivalent", "VIIRS_NOAA21")):
    for r in json.load(open(W/"data"/sub/"PuyehueCordonCaulle.json", encoding="utf-8"))["records"]:
        if r["datetime_utc"] == "2026-10-10 05:54" and r["sensor"] == sens:
            pc = r.get("primary_cluster") or {}
            print("==", sub, sens, "pc centroide", pc.get("centroid_lat"), pc.get("centroid_lon"), "pc_dist", pc.get("centroid_dist_km"), "pc_vrp", pc.get("vrp_mw"))
            for p in r.get("anomaly_pixels") or []:
                print("   px %.4f %.4f vrp=%s bt=%s d_volc=%.2f d_vent=%s" % (p["lat"], p["lon"], p.get("vrp_mw"), p.get("bt_k"),
                      hav(v["lat"], v["lon"], p["lat"], p["lon"]),
                      "%.2f" % hav(v["vent_lat"], v["vent_lon"], p["lat"], p["lon"]) if v.get("vent_lat") else None))
