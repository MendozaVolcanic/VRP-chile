import json, math, statistics as st, yaml, collections
from datetime import datetime, timezone
d = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8")); vs = d["volcanoes"] if isinstance(d, dict) else d
TIER = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
cfg = {v["name"]: v for v in vs}
def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
def publica(r, inner):  # mirovaEqVrp con solo crater (index.html:1161)
    pc = r.get("primary_cluster")
    if not pc: return False
    if r.get("distance_class") and r["distance_class"] != "summit": return False
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner: return False
    return (pc.get("vrp_mw") or 0) > 0
DESDE = "2026-08-29"
print(f"{'volcan':20s} {'sensor':8s} {'n':>4s} {'N km':>6s} {'E km':>6s} {'dist med':>8s} {'p90':>5s} rumbo dominante")
for v in TIER:
    c = cfg[v]; vlat, vlon = c.get("vent_lat") or c["lat"], c.get("vent_lon") or c["lon"]; inner = c.get("inner_radius_km") or 10
    recs = json.load(open(f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]
    por = collections.defaultdict(list)
    for r in recs:
        if (r.get("datetime_utc") or "") < DESDE or not publica(r, inner): continue
        pc = r["primary_cluster"]
        if pc.get("centroid_lat") is None: continue
        dn = (pc["centroid_lat"] - vlat) * 111.32
        de = (pc["centroid_lon"] - vlon) * 111.32 * math.cos(math.radians(vlat))
        por[bucket(r.get("sensor"))].append((dn, de))
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        l = por.get(b, [])
        if len(l) < 5: continue
        dn = st.median(x[0] for x in l); de = st.median(x[1] for x in l)
        dist = sorted(math.hypot(*x) for x in l)
        rumbos = collections.Counter(("N" if x[0] > 0 else "S") + ("E" if x[1] > 0 else "O") for x in l if math.hypot(*x) > 0.3)
        tot = sum(rumbos.values()) or 1
        dom = rumbos.most_common(1)[0] if rumbos else ("-", 0)
        print(f"{v:20s} {b:8s} {len(l):4d} {dn:+6.2f} {de:+6.2f} {st.median(dist):8.2f} {dist[int(.9*len(dist))]:5.2f} {dom[0]} {dom[1]/tot:.0%}")
