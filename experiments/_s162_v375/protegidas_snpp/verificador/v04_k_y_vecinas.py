# -*- coding: utf-8 -*-
"""VP162 verificador, v04: (a) distancia al crater del cumulo que K publica en 279/288/289, recalculada con haversine
propio desde lat/lon del record de K re-corrido (no el campo centroid_dist_km); (b) para 294, ¿el objeto que NOAA-20 ve a
las 05:36 (record de produccion) es el mismo que el port ve a las 05:18? Distancia entre posiciones, no entre radios (A93,
A107). Pregunta 1: si K publicara por el objeto lejano, el centroide estaria a > inner. Pregunta 2: control: la misma
cuenta sobre el par 285 K-far / port (mismo granulo) tiene que dar < 1 km (si da grande, el instrumento esta roto).
"""
import io, json, glob, math, sys
from pathlib import Path
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
ART = r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945"
rs = {r["id"]: r for f in sorted(glob.glob(ART + r"\s159-portes-VIIRS375-*\resultados_VIIRS375_*.json"))
      for r in json.load(open(f, encoding="utf-8"))}
V = {v["name"]: v for v in yaml.safe_load(open(R/"volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a, b, c, d):
    r = 6371.0088; p1, p2 = math.radians(a), math.radians(c)
    return 2*r*math.asin(math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2))
for i in (279, 285, 288, 289, 294, 295):
    r = rs[i]; v = V[r["volcan"]]; k = r["K"]["record"]; pc = k["primary_cluster"]
    vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    print(f"{i} {r['volcan']} {r['hora_utc']}: K pc {pc['n_pixels']} px {pc['vrp_mw']} MW en {pc['centroid_lat']},{pc['centroid_lon']} -> "
          f"haversine al vent {hav(pc['centroid_lat'], pc['centroid_lon'], vl, vo):.3f} km (campo {pc['centroid_dist_km']}); geo_class {pc.get('geo_class')} dc {k['distance_class']} "
          f"| vrp escena {k['vrp_mw']} f5 {k.get('f5_core_vrp_mw')} n_anom {k['n_anomalous_pixels']} discarded {k.get('discarded_reason')}")
    print(f"     claves K record: {sorted(k.keys())}")
# (b) produccion Tupungatito 2026-09-28
d = json.load(open(R/"data/mirova_equivalent/Tupungatito.json", encoding="utf-8"))["records"]
v = V["Tupungatito"]; vl, vo = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
port294 = (-33.6092, -69.9004)   # centro aprox de los 6 pixeles del port (v03)
kfar294 = (rs[294]["K"]["record"]["primary_cluster"]["centroid_lat"], rs[294]["K"]["record"]["primary_cluster"]["centroid_lon"])
print(f"\n294: K far centroide {kfar294}, a {hav(*kfar294, *port294):.1f} km del objeto del port")
for rec in d:
    if rec["datetime_utc"].startswith("2026-09-28 05") or rec["datetime_utc"].startswith("2026-09-28T05"):
        pc = rec.get("primary_cluster") or {}
        print(f"  prod {rec['datetime_utc']} {rec['sensor']} vrp {rec.get('vrp_mw')} dc {rec.get('distance_class')} pc {pc.get('vrp_mw')} en {pc.get('centroid_lat')},{pc.get('centroid_lon')}")
        if pc.get("centroid_lat") is not None:
            c = (pc["centroid_lat"], pc["centroid_lon"])
            print(f"     -> al vent {hav(*c, vl, vo):.2f} km; al objeto del port 05:18 {hav(*c, *port294):.2f} km; al K-far 05:18 {hav(*c, *kfar294):.2f} km")
        for key in ("anomaly_pixels", "discarded_anomaly_pixels"):
            for p in (rec.get(key) or [])[:12]:
                la, lo = p.get("lat"), p.get("lon")
                if la is None: continue
                print(f"     {key}: {la:.4f},{lo:.4f} al vent {hav(la, lo, vl, vo):.2f} km, al objeto port {hav(la, lo, *port294):.2f} km, al K-far {hav(la, lo, *kfar294):.2f} km, bt {p.get('bt_k') or p.get('t_k') or p.get('bt')}")
