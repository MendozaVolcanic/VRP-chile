#!/usr/bin/env python
"""S120 audit: scan Tier A for high-MW records (>50 MW scene-wide or cluster).

Clasifica cada record segun categorias exactas (precedencia a-d):
  a. far_scene        - distance_class=="far" o (pc null y final_hotspot_dist_km > inner)
  b. pathD_cirrus     - summit, pc>50, path-D-only, t_bg_k<260 (D9/A23)
  c. summit_alto      - resto summit con pc>50 (candidato revision real)
  d. scene_sum_summit - summit, vrp_mw>50 pero pc<=50 (suma scene-wide infla)

Read-only sobre data/mirova_equivalent/. Output: highmw_scan.json.
"""
import sys
import json
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")  # guard utf-8 (regla proyecto)

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "mirova_equivalent"
OUT = Path(__file__).resolve().parent / "highmw_scan.json"

# Tier A + inner_radius_km oficial MIROVA (CLAUDE.md proyecto)
TIER_A_INNER = {
    "Lascar": 5, "Lastarria": 3, "Isluga": 5, "Llaima": 5, "Villarrica": 5,
    "Chaiten": 5, "Tupungatito": 7, "Copahue": 4, "PlanchonPeteroa": 3,
    "PuyehueCordonCaulle": 20, "NevadosDeChillan": 5,
}

PATH_FIELDS = ["diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path", "diag_n_eti_path"]


def load_records(vol):
    p = DATA / f"{vol}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["records"] if isinstance(d, dict) else d


def path_d_only(r):
    """path-D-only = diag_n_dnti_ctx_path>0 y los demas paths ==0 o null."""
    dctx = r.get("diag_n_dnti_ctx_path")
    if not dctx or dctx <= 0:
        return False
    others = [r.get("diag_n_bt_path"), r.get("diag_n_nti_path"),
              r.get("diag_n_eti_path"), r.get("n_test1_pixels")]
    return all(o is None or o == 0 for o in others)


def classify(r, inner):
    pc = r.get("primary_cluster") or {}
    pc_vrp = pc.get("vrp_mw")
    dc = r.get("distance_class")
    dist = r.get("final_hotspot_dist_km")
    t_bg = r.get("t_bg_k")
    # a. far_scene
    if dc == "far" or (pc_vrp is None and dist is not None and dist > inner):
        return "far_scene"
    # summit (o sin clase pero pc presente / dist dentro del inner)
    pc_val = pc_vrp or 0
    if pc_val > 50:
        # b. pathD_cirrus
        if path_d_only(r) and t_bg is not None and t_bg < 260:
            return "pathD_cirrus"
        # c. summit_alto
        return "summit_alto"
    # d. scene_sum_summit (vrp_mw>50 con pc<=50)
    return "scene_sum_summit"


def extract(vol, r, cat):
    pc = r.get("primary_cluster") or {}
    return {
        "volcano": vol,
        "datetime_utc": r.get("datetime_utc"),
        "sensor": r.get("sensor"),
        "vrp_mw": r.get("vrp_mw"),
        "pc_vrp_mw": pc.get("vrp_mw"),
        "distance_class": r.get("distance_class"),
        "final_hotspot_dist_km": r.get("final_hotspot_dist_km"),
        "t_bg_k": r.get("t_bg_k"),
        "diag_n_bt_path": r.get("diag_n_bt_path"),
        "diag_n_nti_path": r.get("diag_n_nti_path"),
        "diag_n_dnti_ctx_path": r.get("diag_n_dnti_ctx_path"),
        "diag_n_eti_path": r.get("diag_n_eti_path"),
        "n_test1_pixels": r.get("n_test1_pixels"),
        "n_anomalous_pixels": r.get("n_anomalous_pixels"),
        "product_version": r.get("product_version"),
        "category": cat,
    }


def main():
    hits = []
    for vol, inner in TIER_A_INNER.items():
        for r in load_records(vol):
            vrp = r.get("vrp_mw") or 0
            pc_vrp = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if vrp > 50 or pc_vrp > 50:
                hits.append(extract(vol, r, classify(r, inner)))

    by_cat = Counter(h["category"] for h in hits)
    by_vol = Counter((h["category"], h["volcano"]) for h in hits)
    by_sensor = Counter((h["category"], h["sensor"]) for h in hits)

    def maxmw(h):
        return max(h["vrp_mw"] or 0, h["pc_vrp_mw"] or 0)

    over100 = Counter(h["category"] for h in hits if maxmw(h) > 100)
    over500 = Counter(h["category"] for h in hits if maxmw(h) > 500)

    top15 = {}
    for cat in by_cat:
        cat_hits = sorted((h for h in hits if h["category"] == cat), key=maxmw, reverse=True)
        top15[cat] = cat_hits[:15]

    out = {
        "n_total_hits": len(hits),
        "counts_by_category": dict(by_cat),
        "counts_by_category_volcano": {f"{c}|{v}": n for (c, v), n in sorted(by_vol.items())},
        "counts_by_category_sensor": {f"{c}|{s}": n for (c, s), n in sorted(by_sensor.items())},
        "counts_over_100mw_by_category": dict(over100),
        "counts_over_500mw_by_category": dict(over500),
        "top15_by_category": top15,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Total hits (vrp>50 o pc>50): {len(hits)}")
    print("\nPor categoria:")
    for c, n in by_cat.most_common():
        print(f"  {c:18s} {n}")
    print("\n>100 MW:", dict(over100))
    print(">500 MW:", dict(over500))
    print("\nTop 5 global:")
    for h in sorted(hits, key=maxmw, reverse=True)[:5]:
        print(f"  {h['volcano']:20s} {h['datetime_utc']} {h['sensor']:15s} "
              f"vrp={h['vrp_mw']:.1f} pc={h['pc_vrp_mw']} dist={h['final_hotspot_dist_km']} "
              f"[{h['category']}]")
    print(f"\nJSON -> {OUT}")


if __name__ == "__main__":
    main()
