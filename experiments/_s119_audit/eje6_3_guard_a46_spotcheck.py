# S119 audit Eje 6.3(ii) — spot-check guard A46 post-flip C2 (>= 2026-06-28 21:00 UTC)
# Busca records summit cuyo primary_cluster.centroid esta a > inner_radius_km del vent
# y que NO esten etiquetados final_hotspot_source=='cluster_rescue'. Esperado: 0 incoherencias
# summit->far espurias (guard S113 store.py). Nota A81/S106: anclas honestas
# (ctx_cluster/test1_roi/test1_nti_peak) pueden legitimamente tener pc lejos — se reportan aparte.
import sys, io, json, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "eje6_3_guard_a46_spotcheck.json")
CUTOFF = "2026-06-28 21:00"

import yaml
with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as f:
    vols_cfg = {v["name"]: v for v in yaml.safe_load(f)["volcanoes"]}

TIER_A = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
          "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
          "NevadosDeChillan"]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


HONEST = {"ctx_cluster", "test1_roi", "test1_nti_peak"}
result = {"cutoff_utc": CUTOFF, "vols": {}, "violations": [], "honest_anchor_far_pc": []}
total_recent = total_summit = 0
for vol in TIER_A:
    cfg = vols_cfg.get(vol)
    path = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if cfg is None or not os.path.exists(path):
        result["vols"][vol] = "MISSING"
        continue
    inner = cfg.get("inner_radius_km")
    vlat = cfg.get("vent_lat", cfg["lat"])
    vlon = cfg.get("vent_lon", cfg["lon"])
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    recs = data.get("records", data if isinstance(data, list) else [])
    recent = [r for r in recs if (r.get("datetime_utc") or "") >= CUTOFF]
    n_summit = n_viol = n_honest_far = 0
    for r in recent:
        if r.get("distance_class") != "summit":
            continue
        n_summit += 1
        pc = r.get("primary_cluster") or {}
        clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
        if clat is None or clon is None:
            continue
        d = haversine_km(clat, clon, vlat, vlon)
        if d > inner and r.get("final_hotspot_source") != "cluster_rescue":
            entry = {"volcano": vol, "datetime_utc": r.get("datetime_utc"),
                     "sensor": r.get("sensor"), "pc_dist_vent_km": round(d, 2),
                     "inner_km": inner,
                     "final_hotspot_source": r.get("final_hotspot_source"),
                     "pc_vrp_mw": pc.get("vrp_mw")}
            if r.get("final_hotspot_source") in HONEST:
                n_honest_far += 1
                result["honest_anchor_far_pc"].append(entry)
            else:
                n_viol += 1
                result["violations"].append(entry)
    result["vols"][vol] = {"n_recent": len(recent), "n_summit": n_summit,
                           "n_violations": n_viol, "n_honest_anchor_far_pc": n_honest_far}
    total_recent += len(recent)
    total_summit += n_summit

result["totals"] = {"n_recent": total_recent, "n_summit": total_summit,
                    "n_violations": len(result["violations"]),
                    "n_honest_anchor_far_pc": len(result["honest_anchor_far_pc"])}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Records >= {CUTOFF}: {total_recent} | summit: {total_summit}")
print(f"VIOLACIONES guard A46 (summit, pc>inner, sin cluster_rescue ni ancla honesta): "
      f"{len(result['violations'])}")
for v in result["violations"]:
    print(" ", v)
print(f"Anclas honestas con pc>inner (legitimas por diseño S106): "
      f"{len(result['honest_anchor_far_pc'])}")
for v in result["honest_anchor_far_pc"]:
    print(" ", v)
print(f"OK -> {OUT}")
