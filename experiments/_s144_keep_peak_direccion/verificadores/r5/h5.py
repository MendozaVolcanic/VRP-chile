import os, sys, json, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3"); V4 = os.path.abspath(HERE + "/../v4")
sys.path.insert(0, V3); sys.path.insert(0, V4); sys.path.insert(0, HERE)
from common3 import *  # noqa
from cruz5 import df  # noqa
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/scripts")
import banco_paridad as bp
inner = bp.inner_desde_html()
pos = df[(df.lab == "pos") & df.tif.notna()].copy()
usab = {}
for _, r in pos.iterrows():
    Rq, _ = usable({"own": r["own"], "path": r["tif"]}, r["vol"])
    usab[(r["vol"], pd.Timestamp(r["dt"]).strftime("%Y-%m-%d %H:%M"))] = Rq is not None
    raster.cache_clear()
for exig_usable in (False, True):
    c1, c2 = {}, {}
    for vol in VOLS:
        d = json.load(open(ROOT + f"/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            if bp.bucket(r.get("sensor")) != "VIIRS375":
                continue
            k = (vol, (r.get("datetime_utc") or "")[:16])
            if k not in usab:
                continue
            if exig_usable and not usab[k]:
                continue
            pc = r.get("primary_cluster") or {}
            n = pc.get("n_pixels") or 0
            la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
            if n >= 2 and la is not None and hav(la, lo, *vent(vol)) <= inner[vol]:
                c1[vol] = c1.get(vol, 0) + 1
                if r.get("final_hotspot_source") == "ctx_cluster":
                    c2[vol] = c2.get(vol, 0) + 1
    print("usable=%s  primary>=2px dentro inner: %d %s" % (exig_usable, sum(c1.values()), c1))
    print("         + src==ctx_cluster:        %d %s" % (sum(c2.values()), c2))
