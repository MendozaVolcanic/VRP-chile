# -*- coding: utf-8 -*-
"""Refuerzo: exceso sobre 8 vecinos normalizado, rango en la imagen, mejor celda a <=1 km."""
import json, numpy as np, rasterio, collections
F={(f["vol"],f["t"]):f for f in json.load(open("master.json"))}
O=[o for o in json.load(open("medido.json"))]
out=[]
for o in O:
    f=F[(o["vol"],o["t"])]
    with rasterio.open(f["tif"]) as ds:
        a=ds.read(1).astype(float); rk=ds.res[1]*110.57
        rr,cc=ds.index(f["pc_lon"],f["pc_lat"])
        H,W=a.shape
        nb=(a[:-2,:-2]+a[:-2,1:-1]+a[:-2,2:]+a[1:-1,:-2]+a[1:-1,2:]+a[2:,:-2]+a[2:,1:-1]+a[2:,2:])/8.0
        e=(a[1:-1,1:-1]-nb)/np.nanstd(a)
        if 1<=rr<H-1 and 1<=cc<W-1:
            ours_e=float(e[rr-1,cc-1]); rank=float(np.nanmean(e<ours_e))
        else: ours_e=None; rank=None
        # mejor celda (percentil en disco 5km) dentro de 1 km de la nuestra
        rad=int(round(1.0/rk)); best=-1; bz=None
        y,x=np.ogrid[:H,:W]
        for dr in range(-rad,rad+1):
            for dc in range(-rad,rad+1):
                r2,c2=rr+dr,cc+dc
                if not(0<=r2<H and 0<=c2<W): continue
                if dr*dr+dc*dc>rad*rad: continue
                v=a[r2,c2]
                if not np.isfinite(v): continue
                m=((y-r2)**2+(x-c2)**2<=(5.0/rk)**2)&np.isfinite(a)
                p=float((a[m]<v).mean())
                if p>best: best=p
        # maximo del disco de radio inner alrededor del crater, como percentil de la escena
        vlat,vlon=f["vent"]; vr,vc=ds.index(vlon,vlat)
        mi=((y-vr)**2+(x-vc)**2<=(f["inner"]/rk)**2)&np.isfinite(a)
        vmax=float(np.nanmax(a[mi])) if mi.sum() else None
        pmax=float((a[np.isfinite(a)]<vmax).mean()) if vmax is not None else None
    out.append(dict(o, exc8_sd=ours_e, rank_exc8=rank, mejor_pctl_1km=best, pctl_max_inner=pmax, rad1km_celdas=rad))
json.dump(out,open("medido2.json","w"),indent=0)
def g(cl,src="ctx_cluster",dentro=True):
    return [o for o in out if o["clase"]==cl and o["src"]==src and o["dentro"]==dentro]
for cl in ["MIROVA_RUTINA0","MIROVA_ALERTA","MIROVA_FALSO_POS"]:
    gg=g(cl)
    if not gg: continue
    print(f"{cl:18s} n={len(gg):3d} | exceso sobre 8 vecinos (sd de escena) med {np.median([o['exc8_sd'] for o in gg]):+.3f} "
          f"| su rango entre todas las celdas de la imagen med {np.median([o['rank_exc8'] for o in gg]):.4f} "
          f"| mejor percentil a <=1 km med {np.median([o['mejor_pctl_1km'] for o in gg]):.3f} "
          f"| percentil del maximo dentro del radio interno med {np.median([o['pctl_max_inner'] for o in gg]):.4f}")
