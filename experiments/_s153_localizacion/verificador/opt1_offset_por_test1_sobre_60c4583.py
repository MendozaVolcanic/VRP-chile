import json, math, statistics as st, yaml, collections
d = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8")); vs = d["volcanoes"] if isinstance(d, dict) else d
cfg = {v["name"]: v for v in vs}
TIER = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
def publica(r, inner):
    pc = r.get("primary_cluster")
    if not pc: return False
    if r.get("distance_class") and r["distance_class"] != "summit": return False
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner: return False
    return (pc.get("vrp_mw") or 0) > 0
print(f"{'volcan':20s} {'con Test 1':>22s} {'sin Test 1':>22s}   fuente de la posición (con Test 1)")
for v in TIER:
    c = cfg[v]; vlat, vlon = c.get("vent_lat") or c["lat"], c.get("vent_lon") or c["lon"]; inner = c.get("inner_radius_km") or 10
    recs = json.load(open(f"C:/Users/nmend/AppData/Local/Temp/claude/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/7dc24c2e-f151-417e-a032-2d224bb93be0/scratchpad/prod_60c4583/{v}.json", encoding="utf-8"))["records"]
    g = {True: [], False: []}; fuentes = collections.Counter()
    for r in recs:
        s = r.get("sensor") or ""
        if (r.get("datetime_utc") or "") < "2026-08-29" or not s.startswith("VIIRS") or s.endswith("_750") or not publica(r, inner): continue
        pc = r["primary_cluster"]
        if pc.get("centroid_lat") is None: continue
        dist = math.hypot((pc["centroid_lat"] - vlat) * 111.32, (pc["centroid_lon"] - vlon) * 111.32 * math.cos(math.radians(vlat)))
        t1 = bool(r.get("triggered_test1")); g[t1].append(dist)
        if t1: fuentes[r.get("final_hotspot_source")] += 1
    f = lambda l: f"n {len(l):3d} med {st.median(l):4.2f} p90 {sorted(l)[int(.9*len(l))]:4.2f}" if len(l) >= 5 else f"n {len(l):3d}"
    print(f"{v:20s} {f(g[True]):>22s} {f(g[False]):>22s}   {dict(fuentes.most_common(2))}")
