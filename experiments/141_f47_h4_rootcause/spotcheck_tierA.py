"""Spot-check del patrón H4 en otros Tier A."""
import json
from pathlib import Path

VOLCANOS = [
    "Lascar", "Lastarria", "PuyehueCordonCaulle", "Llaima", "Villarrica",
    "Copahue", "Chaiten", "Isluga", "Tupungatito", "PlanchonPeteroa",
    "NevadosDeChillan",
]
# inner_radius_km per CLAUDE.md S14
INNER = {
    "Lastarria": 3, "PlanchonPeteroa": 3, "Copahue": 4,
    "Lascar": 5, "Isluga": 5, "NevadosDeChillan": 5, "Llaima": 5,
    "Villarrica": 5, "Chaiten": 5,
    "Tupungatito": 7, "PuyehueCordonCaulle": 20,
}

base = Path("data/mirova_equivalent")
hdr = ["volcano", "tot", "pc>0&v=0", "pc<=in&disc=far", "pc<=in&fh>in"]
print("  ".join(f"{h:>22}" for h in hdr))
for v in VOLCANOS:
    p = base / f"{v}.json"
    if not p.exists():
        print(f"  {v:>22}  (no JSON)")
        continue
    inner = INNER.get(v, 5)
    data = json.loads(p.read_text())
    recs = data["records"]
    mis = 0
    pc_near_discarded = 0
    pc_near_fh_far = 0
    for r in recs:
        pc = r.get("primary_cluster") or {}
        pc_vrp = pc.get("vrp_mw", 0) or 0
        pc_d = pc.get("centroid_dist_km")
        fh_d = r.get("final_hotspot_dist_km")
        if pc_vrp > 0 and (r.get("vrp_mw") or 0) == 0:
            mis += 1
            if pc_d is not None and pc_d <= inner:
                if r.get("discarded_reason") == "eruption_hotspot_too_far":
                    pc_near_discarded += 1
                if fh_d is not None and fh_d > inner:
                    pc_near_fh_far += 1
    print("  ".join(f"{c:>22}" for c in [v, len(recs), mis, pc_near_discarded, pc_near_fh_far]))
