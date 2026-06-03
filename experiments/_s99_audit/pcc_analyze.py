#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""S99 PCC investigation. Reads PCC.json + TIFs, writes JSON results.
No numbers by hand; everything reproducible. A61 spatial audit."""
import os, sys, json, math, glob
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
except Exception:
    pass

REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TIFDIR = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive/data/tif/PuyehueCordonCaulle"
OUT = os.path.join(REPO, "experiments/_s99_audit")

VENT_LAT, VENT_LON = -40.525499, -72.146137      # lacolito (vent)
MC_LAT, MC_LON = -40.5903, -72.1187              # mirova_center
INNER_KM = 20.0

def hav(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def pc_of(r):
    pc = r.get("primary_cluster") or {}
    return pc

# ---------- 1. records ----------
d = json.load(open(os.path.join(REPO, "data/mirova_equivalent/PuyehueCordonCaulle.json"), encoding="utf-8"))
recs = d["records"] if isinstance(d, dict) and "records" in d else d

def get_vrp(r):
    pc = pc_of(r)
    return pc.get("vrp_mw", 0) or 0

giants = []
for r in recs:
    v = get_vrp(r)
    if v is None:
        continue
    if v > 100:
        pc = pc_of(r)
        paths = {
            "bt": r.get("diag_n_bt_path"),
            "nti": r.get("diag_n_nti_path"),
            "dnti_ctx": r.get("diag_n_dnti_ctx_path"),
            "eti": r.get("diag_n_eti_path"),
        }
        giants.append({
            "datetime_utc": r.get("datetime_utc"),
            "sensor": r.get("sensor"),
            "pc_vrp_mw": round(v, 2),
            "record_vrp_mw": round(r.get("vrp_mw", 0) or 0, 2),
            "pc_n_pixels": pc.get("n_pixels"),
            "n_anomalous_pixels": r.get("n_anomalous_pixels"),
            "t_bg_k": r.get("t_bg_k"),
            "t_max_k": r.get("t_max_k"),
            "centroid_lat": pc.get("centroid_lat"),
            "centroid_lon": pc.get("centroid_lon"),
            "centroid_dist_km": pc.get("centroid_dist_km"),
            "geo_class": pc.get("geo_class"),
            "distance_class": r.get("distance_class"),
            "single_pixel_mode": pc.get("single_pixel_mode"),
            "triggered_test1": r.get("triggered_test1"),
            "paths": paths,
            "product_version": r.get("product_version"),
            "final_hotspot_source": r.get("final_hotspot_source"),
        })

# distance of centroid to vent and to mirova_center for each giant
for g in giants:
    cl, co = g["centroid_lat"], g["centroid_lon"]
    if cl is not None and co is not None:
        g["centroid_to_vent_km"] = round(hav(cl, co, VENT_LAT, VENT_LON), 3)
        g["centroid_to_mc_km"] = round(hav(cl, co, MC_LAT, MC_LON), 3)

# also >1000 subset
giants.sort(key=lambda x: -x["pc_vrp_mw"])
over1000 = [g for g in giants if g["pc_vrp_mw"] > 1000]

# sensor breakdown of >100
from collections import Counter
sensor_ct = Counter(g["sensor"] for g in giants)
sensor_ct_1000 = Counter(g["sensor"] for g in over1000)

# date range of records (post-S98 check)
dates = sorted([r.get("datetime_utc") for r in recs if r.get("datetime_utc")])

summary = {
    "n_records_total": len(recs),
    "n_gt100": len(giants),
    "n_gt1000": len(over1000),
    "sensor_breakdown_gt100": dict(sensor_ct),
    "sensor_breakdown_gt1000": dict(sensor_ct_1000),
    "date_min": dates[0] if dates else None,
    "date_max": dates[-1] if dates else None,
    "vent_lat_lon": [VENT_LAT, VENT_LON],
    "mirova_center_lat_lon": [MC_LAT, MC_LON],
    "vent_to_mc_km": round(hav(VENT_LAT, VENT_LON, MC_LAT, MC_LON), 3),
}

# ---------- TIF analysis ----------
import rasterio
import numpy as np

def tif_centroid(path, top_frac=0.999):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64")
        nod = ds.nodata
        T = ds.transform
        crs = ds.crs
        H, W = arr.shape
        mask = np.isfinite(arr)
        if nod is not None:
            mask &= (arr != nod)
        mask &= (arr > 0)
        ys, xs = np.where(mask)
        if len(ys) == 0:
            return None
        vals = arr[ys, xs]
        # pixel centers -> CRS coords
        xc, yc = rasterio.transform.xy(T, ys, xs, offset="center")
        xc = np.asarray(xc); yc = np.asarray(yc)
        # weighted centroid in CRS
        cx = np.average(xc, weights=vals)
        cy = np.average(yc, weights=vals)
        # to lat/lon
        from rasterio.warp import transform as warp_tf
        lons, lats = warp_tf(crs, "EPSG:4326", [cx], [cy])
        clon, clat = lons[0], lats[0]
        # top pixel
        ti = int(np.argmax(vals))
        tlons, tlats = warp_tf(crs, "EPSG:4326", [xc[ti]], [yc[ti]])
        return {
            "n_pos_pixels": int(len(vals)),
            "sum_val": float(vals.sum()),
            "max_val": float(vals.max()),
            "weighted_centroid_lat": float(clat),
            "weighted_centroid_lon": float(clon),
            "top_pixel_lat": float(tlats[0]),
            "top_pixel_lon": float(tlons[0]),
            "crs": str(crs),
        }

tif_files = sorted(glob.glob(os.path.join(TIFDIR, "*.tif")))
# pick recent VIIRS375 (real source) + a MODIS for comparison
v375 = [f for f in tif_files if "VIIRS375" in os.path.basename(f)]
modis = [f for f in tif_files if "MODIS" in os.path.basename(f)]
picks = (v375[-3:] if v375 else []) + (modis[-2:] if modis else [])

tif_results = []
for f in picks:
    try:
        c = tif_centroid(f)
        if c is None:
            tif_results.append({"file": os.path.basename(f), "error": "no positive pixels"})
            continue
        c["file"] = os.path.basename(f)
        c["centroid_to_vent_km"] = round(hav(c["weighted_centroid_lat"], c["weighted_centroid_lon"], VENT_LAT, VENT_LON), 3)
        c["centroid_to_mc_km"] = round(hav(c["weighted_centroid_lat"], c["weighted_centroid_lon"], MC_LAT, MC_LON), 3)
        c["toppix_to_vent_km"] = round(hav(c["top_pixel_lat"], c["top_pixel_lon"], VENT_LAT, VENT_LON), 3)
        c["toppix_to_mc_km"] = round(hav(c["top_pixel_lat"], c["top_pixel_lon"], MC_LAT, MC_LON), 3)
        tif_results.append(c)
    except Exception as e:
        tif_results.append({"file": os.path.basename(f), "error": repr(e)})

result = {
    "summary": summary,
    "giants_gt1000": over1000,
    "giants_gt100_top20": giants[:20],
    "tif_picks": [os.path.basename(f) for f in picks],
    "tif_results": tif_results,
    "n_tif_total": len(tif_files),
    "n_v375": len(v375),
    "n_modis": len(modis),
}
with open(os.path.join(OUT, "pcc_result.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2, ensure_ascii=False)
print("WROTE pcc_result.json")
print(json.dumps(summary, indent=2, ensure_ascii=False))
print("--- TIF ---")
for t in tif_results:
    print(json.dumps(t, ensure_ascii=False))
