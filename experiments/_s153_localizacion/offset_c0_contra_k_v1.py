import json, math, statistics as st, yaml, sys, os
d = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8")); vs = d["volcanoes"] if isinstance(d, dict) else d
cfg = {v["name"]: v for v in vs}
U = r"C:/Users/nmend/AppData/Local/Temp/claude/v1_38639658446/union_d16_v2"
TIER = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
def publica(r, inner):
    pc = r.get("primary_cluster")
    if not pc: return False
    if r.get("distance_class") and r["distance_class"] != "summit": return False
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner: return False
    return (pc.get("vrp_mw") or 0) > 0
def dists(arm, v, sens):
    c = cfg[v]; vlat, vlon = c.get("vent_lat") or c["lat"], c.get("vent_lon") or c["lon"]; inner = c.get("inner_radius_km") or 10
    p = os.path.join(U, arm, v + ".json")
    out = []
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        s = r.get("sensor") or ""
        b = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
        if b != sens or not publica(r, inner): continue
        pc = r["primary_cluster"]
        if pc.get("centroid_lat") is None: continue
        out.append(math.hypot((pc["centroid_lat"] - vlat) * 111.32, (pc["centroid_lon"] - vlon) * 111.32 * math.cos(math.radians(vlat))))
    return out
f = lambda l: f"n {len(l):3d} med {st.median(l):4.2f} km, <1 km {sum(x<1 for x in l)/len(l):4.0%}" if l else "n   0"
for sens in ("VIIRS375", "VIIRS750"):
    print("==", sens, "   C0 (produccion)                      K")
    for v in TIER:
        print(f"{v:20s} {f(dists('_s146_ab_control', v, sens)):34s} {f(dists('_s149_ab_sin_test1_b22_max', v, sens))}")
