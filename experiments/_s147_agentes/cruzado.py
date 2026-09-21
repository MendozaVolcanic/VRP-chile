# -*- coding: utf-8 -*-
"""A109: el mismo punto en OTRA pasada de la misma noche (otro granulo)."""
import json, numpy as np, rasterio, collections, datetime as dt, sys
sys.path.insert(0,'.')
from common import tif_rows, TIF2OURS
from medir import stats_en, R_KM   # reusa el estadistico
F={ (f["vol"],f["t"]):f for f in json.load(open("master.json")) }
O=[o for o in json.load(open("medido.json")) if o["src"]=="ctx_cluster" and o["dentro"]]
TT=collections.defaultdict(list)
for tr in tif_rows("VIIRS375"): TT[TIF2OURS[tr["volcano"]]].append(tr)

res=[]
for o in O:
    f=F[(o["vol"],o["t"])]
    t0=dt.datetime.strptime(f["t"],"%Y-%m-%d %H:%M")
    cands=[]
    for tr in TT[o["vol"]]:
        dm=abs((tr["_t"]-t0).total_seconds())/60
        if 45<=dm<=180 and tr["_abs"]!=f["tif"]: cands.append((dm,tr))
    if not cands: res.append(dict(o,cruz=None)); continue
    dm,tr=min(cands)
    with rasterio.open(tr["_abs"]) as ds:
        a=ds.read(1).astype(float); rk=ds.res[1]*110.57
        rc=ds.index(f["pc_lon"],f["pc_lat"])
        s=stats_en(a,rc[0],rc[1],R_KM/rk)
    res.append(dict(o,cruz=s,cruz_dmin=dm,cruz_tif=tr["tif_path"]))
json.dump(res,open("cruzado.json","w"),indent=0)
for cl in ["MIROVA_RUTINA0","MIROVA_ALERTA"]:
    g=[r for r in res if r["clase"]==cl and r["cruz"]]
    if not g: print(cl,"sin pareja cruzada"); continue
    p=np.array([r["ours_pctl"] for r in g]); c=np.array([r["cruz"]["pctl"] for r in g])
    z=np.array([r["ours_z"] for r in g]); cz=np.array([r["cruz"]["z"] for r in g])
    print(f"{cl:16s} n={len(g):3d} (con otra pasada a {np.median([r['cruz_dmin'] for r in g]):.0f} min) "
          f"percentil mismo granulo {np.median(p):.3f} vs otro granulo {np.median(c):.3f} | "
          f"z mismo {np.median(z):+.2f} vs otro {np.median(cz):+.2f}")
print("sin pareja cruzada:", sum(1 for r in res if not r["cruz"]),"/",len(res))
