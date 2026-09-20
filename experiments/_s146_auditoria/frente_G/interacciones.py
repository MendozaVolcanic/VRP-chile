"""Frente G: numeros de las interacciones I-1 (ancla honesta vs cerca) e I-8 (segundo pase sin compuerta). Regimen >= 2026-09-01."""
import json, os, collections, yaml
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
cfg = yaml.safe_load(open(os.path.join(root, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]
C = collections.defaultdict(collections.Counter)
for v in cfg:
    if not v.get("inner_radius_km"): continue
    for r in json.load(open(os.path.join(root, "data/mirova_equivalent", v["name"] + ".json"), encoding="utf-8"))["records"]:
        if (r.get("datetime_utc") or "") < "2026-09-01": continue
        s = str(r.get("sensor") or ""); b = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
        c = C[b]; pc = r.get("primary_cluster") or {}
        fp = r.get("diag_n_first_pass_pixels") or 0; sp = r.get("diag_n_second_pass_recapture") or 0
        if r.get("final_hotspot_source") == "test1_roi":
            c["test1_roi"] += 1
            c["test1_roi y distance_class=summit"] += r.get("distance_class") == "summit"
            c["test1_roi y final_hotspot_dist_km==0"] += (r.get("final_hotspot_dist_km") == 0)
            d = pc.get("centroid_dist_km")
            if d is not None: c["test1_roi: centroide del cumulo publicado > 1 km del crater"] += d > 1.0
        if fp == 0 and sp > 0: c["primer pase 0 y segundo pase > 0 (el segundo pase detecta solo)"] += 1
        if fp > 0: c["primer pase > 0"] += 1
        if sp > fp and fp > 0: c["recaptura > primer pase"] += 1
        c["n"] += 1
out = {b: dict(c) for b, c in C.items()}
for b, c in out.items(): print(b, c)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "interacciones.json"), "w"), indent=1)
