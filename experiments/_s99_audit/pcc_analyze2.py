#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""S99 PCC part 2: giants by record.vrp_mw + vrp_mir_mw (what the MAP popup shows),
spatial location of those records, and LOCAL TIF centroid near crater (A24-aware).
S98 anchor check."""
import os, sys, json, math, glob
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
import numpy as np, rasterio
from rasterio.warp import transform as warp_tf

REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TIFDIR = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive/data/tif/PuyehueCordonCaulle"
OUT = os.path.join(REPO, "experiments/_s99_audit")
VENT_LAT, VENT_LON = -40.525499, -72.146137
MC_LAT, MC_LON = -40.5903, -72.1187

def hav(a, b, c, d):
    R=6371.0088; p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

d = json.load(open(os.path.join(REPO,"data/mirova_equivalent/PuyehueCordonCaulle.json"),encoding="utf-8"))
recs = d["records"]
def rv(r): return r.get("vrp_mw",0) or 0
def mir(r): return r.get("vrp_mir_mw",0) or 0
def pcv(r): return (r.get("primary_cluster") or {}).get("vrp_mw",0) or 0

# what the MAP popup shows: recordTotalVrp = vrp_mw ?? vrp_mir_mw
def map_val(r):
    v = r.get("vrp_mw")
    return v if v is not None else (r.get("vrp_mir_mw") or 0)

big = [r for r in recs if map_val(r) > 100]
big.sort(key=lambda r:-map_val(r))
rows = []
for r in big[:25]:
    pc = r.get("primary_cluster") or {}
    cl, co = pc.get("centroid_lat"), pc.get("centroid_lon")
    rows.append({
        "datetime_utc": r.get("datetime_utc"), "sensor": r.get("sensor"),
        "map_popup_total_mw": round(map_val(r),1),
        "vrp_mw": round(rv(r),1), "vrp_mir_mw": round(mir(r),1),
        "pc_vrp_mw": round(pcv(r),2),
        "n_anom_px": r.get("n_anomalous_pixels"), "pc_n_px": pc.get("n_pixels"),
        "t_bg_k": r.get("t_bg_k"), "t_max_k": r.get("t_max_k"),
        "n_dnti_ctx": r.get("diag_n_dnti_ctx_path"),
        "n_bt": r.get("diag_n_bt_path"), "n_nti": r.get("diag_n_nti_path"),
        "centroid_lat": cl, "centroid_lon": co,
        "centroid_dist_km": pc.get("centroid_dist_km"),
        "cent_to_vent_km": round(hav(cl,co,VENT_LAT,VENT_LON),3) if cl else None,
        "cent_to_mc_km": round(hav(cl,co,MC_LAT,MC_LON),3) if cl else None,
        "geo_class": pc.get("geo_class"), "distance_class": r.get("distance_class"),
        "fhs": r.get("final_hotspot_source"),
        "fh_lat": r.get("final_hotspot_lat"), "fh_lon": r.get("final_hotspot_lon"),
        "fh_dist": r.get("final_hotspot_dist_km"),
    })

# S98 anchor check: did centroid move to crater for post-fix records?
# group by month, look at centroid_dist_km (anchored to detection anchor)
from collections import defaultdict
by_month = defaultdict(list)
for r in recs:
    dt = r.get("datetime_utc","")
    m = dt[:7]
    pc = r.get("primary_cluster") or {}
    cd = pc.get("centroid_dist_km")
    cl, co = pc.get("centroid_lat"), pc.get("centroid_lon")
    if cl is not None:
        by_month[m].append({
            "cd_km": cd,
            "to_vent": hav(cl,co,VENT_LAT,VENT_LON),
            "to_mc": hav(cl,co,MC_LAT,MC_LON),
        })
month_summary = {}
for m in sorted(by_month):
    arr = by_month[m]
    tv = sorted(x["to_vent"] for x in arr)
    tm = sorted(x["to_mc"] for x in arr)
    cd = sorted(x["cd_km"] for x in arr if x["cd_km"] is not None)
    def med(L): return round(L[len(L)//2],3) if L else None
    month_summary[m] = {"n":len(arr), "med_centroid_to_vent_km":med(tv),
                        "med_centroid_to_mc_km":med(tm),
                        "med_centroid_dist_km_field":med(cd)}

# ---- LOCAL TIF centroid near crater (A24-aware): restrict to pixels within 12 km of vent ----
def local_centroid(path, anchor_lat, anchor_lon, radius_km, top_n=15):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64"); T=ds.transform; crs=ds.crs; nod=ds.nodata
        m = np.isfinite(arr) & (arr>0)
        if nod is not None: m &= (arr!=nod)
        ys,xs = np.where(m)
        if len(ys)==0: return None
        vals = arr[ys,xs]
        xc,yc = rasterio.transform.xy(T,ys,xs,offset="center")
        lons,lats = warp_tf(crs,"EPSG:4326",list(xc),list(yc))
        lons=np.array(lons); lats=np.array(lats)
        dists = np.array([hav(la,lo,anchor_lat,anchor_lon) for la,lo in zip(lats,lons)])
        sel = dists<=radius_km
        if sel.sum()==0: return None
        sv=vals[sel]; sla=lats[sel]; slo=lons[sel]; sd=dists[sel]
        # top_n hottest within radius
        order=np.argsort(-sv)[:top_n]
        tv=sv[order]; tla=sla[order]; tlo=slo[order]
        cla=np.average(tla,weights=tv); clo=np.average(tlo,weights=tv)
        # absolute hottest within radius
        hi=int(np.argmax(sv))
        return {
            "n_within_radius": int(sel.sum()),
            "topN_centroid_lat": float(cla), "topN_centroid_lon": float(clo),
            "topN_cent_to_vent_km": round(hav(cla,clo,VENT_LAT,VENT_LON),3),
            "topN_cent_to_mc_km": round(hav(cla,clo,MC_LAT,MC_LON),3),
            "hottest_lat": float(sla[hi]), "hottest_lon": float(slo[hi]),
            "hottest_to_vent_km": round(hav(sla[hi],slo[hi],VENT_LAT,VENT_LON),3),
            "hottest_to_mc_km": round(hav(sla[hi],slo[hi],MC_LAT,MC_LON),3),
            "hottest_val": float(sv[hi]),
        }

tifs = sorted(glob.glob(os.path.join(TIFDIR,"*VIIRS375.tif")))
local_results=[]
for f in tifs[-4:]:
    # local centroid anchored at vent and at mc, radius 12 km
    lv = local_centroid(f, VENT_LAT, VENT_LON, 12.0)
    lm = local_centroid(f, MC_LAT, MC_LON, 12.0)
    local_results.append({"file":os.path.basename(f),
                          "local_near_vent_r12": lv,
                          "local_near_mc_r12": lm})

out = {
    "map_popup_giants_top25": rows,
    "n_map_gt100": len(big),
    "n_map_gt1000_recordlevel": len([r for r in recs if map_val(r)>1000]),
    "max_vrp_mw": round(max(rv(r) for r in recs),1),
    "max_vrp_mir_mw": round(max(mir(r) for r in recs),1),
    "max_pc_vrp_mw": round(max(pcv(r) for r in recs),1),
    "month_centroid_summary": month_summary,
    "local_tif_centroids": local_results,
}
json.dump(out, open(os.path.join(OUT,"pcc_result2.json"),"w",encoding="utf-8"), indent=2, ensure_ascii=False)
print("WROTE pcc_result2.json")
print("map>100:",out["n_map_gt100"],"map>1000:",out["n_map_gt1000_recordlevel"])
print("max vrp_mw",out["max_vrp_mw"],"max vrp_mir_mw",out["max_vrp_mir_mw"],"max pc",out["max_pc_vrp_mw"])
print("--- month centroid summary ---")
for m,v in month_summary.items(): print(m, v)
print("--- local TIF centroids (r=12km) ---")
for lr in local_results:
    print(lr["file"])
    print("  near_vent:", lr["local_near_vent_r12"])
    print("  near_mc  :", lr["local_near_mc_r12"])
