"""
S109 diffuse-field probe (READ-ONLY).

Question: in the inflated MODIS records (pc.vrp_mw > 5 MW) of the snow-clad
volcanoes, are the ~7 MW the SUM of many low-VRP pixels near the background
(a diffuse field) or do they come from ONE hot focus pixel?

Method:
  - Read data/mirova_equivalent/<vol>.json.
  - MODIS records = sensor.startswith("MODIS").  (Verified convention:
    MODIS_AQUA / MODIS_TERRA; VIIRS_* are I/M band, excluded.)
  - Inflated = primary_cluster.vrp_mw > 5.
  - The cluster is NOT stored as a separate pixel list; anomaly_pixels is
    scene-wide.  But per-pixel VRP/BT IS persisted in anomaly_pixels[]
    (keys: lat, lon, dist_km, bt_k, vrp_mw).  We reconstruct the cluster as
    the pc.n_pixels anomaly_pixels nearest the cluster centroid.  Validated:
    their VRP sum == pc.vrp_mw to <1e-3 MW for the sampled records, so the
    reconstruction is exact (cluster = nearest-n to centroid).
  - Per record compute:
      cluster_vrp_sum   = pc.vrp_mw  (sum of cluster pixel VRPs)
      max_pixel_vrp     = VRP of the single hottest-VRP pixel IN the cluster
      max_over_sum      = max_pixel_vrp / cluster_vrp_sum
      delta_t           = t_max_k - t_bg_k
      n_pixels          = pc.n_pixels
  - Report medians per volcano.  Lascar = control (real MODIS focus).
"""
import json
import math
import os
import statistics
from collections import Counter

BASE = os.path.join(os.path.dirname(__file__), "..", "..",
                    "data", "mirova_equivalent")
BASE = os.path.abspath(BASE)

VOLS = ["Chaiten", "Villarrica", "Llaima", "Tupungatito",
        "PuyehueCordonCaulle", "Lascar"]

R_EARTH = 6371.0


def hav(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_EARTH * math.asin(math.sqrt(x))


def reconstruct_cluster(rec):
    """Return list of (vrp, bt) for the n_pixels anomaly_pixels nearest the
    cluster centroid, plus a flag whether sum matches pc.vrp_mw."""
    pc = rec.get("primary_cluster") or {}
    n = pc.get("n_pixels")
    clat = pc.get("centroid_lat")
    clon = pc.get("centroid_lon")
    ap = rec.get("anomaly_pixels") or []
    if not n or clat is None or clon is None or not ap:
        return None, None
    enriched = []
    for p in ap:
        if "lat" not in p or "lon" not in p:
            continue
        dc = hav(clat, clon, p["lat"], p["lon"])
        enriched.append((dc, p.get("vrp_mw", 0.0), p.get("bt_k")))
    if len(enriched) < n:
        n = len(enriched)
    enriched.sort(key=lambda t: t[0])
    cluster = enriched[:n]
    vsum = sum(v for _, v, _ in cluster)
    match = abs(vsum - (pc.get("vrp_mw") or 0.0)) < 1e-2
    return cluster, match


def med(xs):
    return statistics.median(xs) if xs else None


def main():
    sensor_counter_global = Counter()
    per_vol = []
    for vol in VOLS:
        path = os.path.join(BASE, vol + ".json")
        if not os.path.exists(path):
            print(f"MISSING {vol}")
            continue
        d = json.load(open(path, encoding="utf-8"))
        recs = d.get("records", [])
        modis = [r for r in recs if (r.get("sensor") or "").startswith("MODIS")]
        sensor_counter_global.update(r.get("sensor") for r in recs)
        inflated = []
        for r in modis:
            pc = r.get("primary_cluster") or {}
            if (pc.get("vrp_mw") or 0) > 5:
                inflated.append(r)

        n_pix_list, cl_sum_list, max_pix_list, ratio_list, dt_list = [], [], [], [], []
        match_ok, match_total = 0, 0
        for r in inflated:
            pc = r["primary_cluster"]
            cl_sum = pc.get("vrp_mw") or 0.0
            n_pix = pc.get("n_pixels")
            cluster, match = reconstruct_cluster(r)
            t_max = r.get("t_max_k")
            t_bg = r.get("t_bg_k")
            dt = (t_max - t_bg) if (t_max is not None and t_bg is not None) else None

            n_pix_list.append(n_pix)
            cl_sum_list.append(cl_sum)
            if dt is not None:
                dt_list.append(dt)
            if cluster:
                match_total += 1
                if match:
                    match_ok += 1
                max_vrp = max(v for _, v, _ in cluster)
                max_pix_list.append(max_vrp)
                if cl_sum > 0:
                    ratio_list.append(max_vrp / cl_sum)

        per_vol.append({
            "vol": vol,
            "n_inflated": len(inflated),
            "median_cluster_pixels": med(n_pix_list),
            "median_cluster_vrp_sum": med(cl_sum_list),
            "median_max_pixel_vrp": med(max_pix_list),
            "max_over_sum_ratio": med(ratio_list),
            "median_delta_t": med(dt_list),
            "cluster_recon_match": f"{match_ok}/{match_total}",
        })

    print("=== GLOBAL SENSOR CONVENTION (all records, these 6 vols) ===")
    for s, c in sensor_counter_global.most_common():
        print(f"  {s}: {c}")
    print()
    print("=== PER-VOLCANO (MODIS, pc.vrp_mw > 5) ===")
    hdr = ("vol", "n_infl", "med_npix", "med_clsum", "med_maxpix",
           "max/sum", "med_dT", "recon_match")
    print("{:<20} {:>6} {:>9} {:>10} {:>11} {:>8} {:>7} {:>12}".format(*hdr))
    for v in per_vol:
        print("{:<20} {:>6} {:>9} {:>10.3f} {:>11.4f} {:>8.3f} {:>7.2f} {:>12}".format(
            v["vol"], v["n_inflated"],
            v["median_cluster_pixels"] if v["median_cluster_pixels"] is not None else -1,
            v["median_cluster_vrp_sum"] or 0,
            v["median_max_pixel_vrp"] or 0,
            v["max_over_sum_ratio"] or 0,
            v["median_delta_t"] or 0,
            v["cluster_recon_match"],
        ))

    out = os.path.join(os.path.dirname(__file__), "result.json")
    json.dump(per_vol, open(out, "w", encoding="utf-8"), indent=2)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
