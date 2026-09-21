import json, numpy as np, rasterio, collections
P=json.load(open("pares.json"))
P=[p for p in P if p["zen"] is not None]
rows=[]
for p in P:
    with rasterio.open(p["tif"]) as ds: a=ds.read(1).astype(float)
    m=np.isfinite(a)
    dx=np.diff(a,axis=1); dy=np.diff(a,axis=0)
    eqx=np.nanmean(dx==0); eqy=np.nanmean(dy==0)
    uniq=len(np.unique(a[m]))/m.sum()
    # rugosidad normalizada: |laplaciano| / sd  (suave -> bajo)
    lap=a[1:-1,1:-1]*4-a[:-2,1:-1]-a[2:,1:-1]-a[1:-1,:-2]-a[1:-1,2:]
    rug=np.nanstd(lap)/np.nanstd(a)
    # autocorrelacion lag-1 en x
    x0=a[:,:-1].ravel(); x1=a[:,1:].ravel(); k=np.isfinite(x0)&np.isfinite(x1)
    ac=np.corrcoef(x0[k],x1[k])[0,1]
    rows.append(dict(vol=p["vol"],zen=p["zen"],eqx=eqx,eqy=eqy,uniq=uniq,rug=rug,ac=ac,
                     vmin=float(np.nanmin(a)),vmax=float(np.nanmax(a))))
import statistics as st
print("n TIF VIIRS375 con zenital conocido (2026-05-09 a 2026-05-20):",len(rows))
print("fraccion de pares horizontales EXACTAMENTE iguales: min %.5f med %.5f max %.5f"%(
    min(r['eqx'] for r in rows), st.median([r['eqx'] for r in rows]), max(r['eqx'] for r in rows)))
print("fraccion verticales iguales: max %.5f"%max(r['eqy'] for r in rows))
print("valores unicos / celdas validas: min %.4f med %.4f"%(min(r['uniq'] for r in rows), st.median([r['uniq'] for r in rows])))
lo=[r for r in rows if r['zen']<30]; hi=[r for r in rows if r['zen']>=52]; mid=[r for r in rows if 30<=r['zen']<52]
for nm,g in [("nadir <30",lo),("medio 30-52",mid),("borde >=52",hi)]:
    if not g: continue
    print(f"{nm:14s} n={len(g):3d} zen[{min(r['zen'] for r in g):.1f}-{max(r['zen'] for r in g):.1f}] "
          f"autocorr_lag1 med {st.median([r['ac'] for r in g]):.4f}  rugosidad med {st.median([r['rug'] for r in g]):.4f} "
          f"eqx med {st.median([r['eqx'] for r in g]):.5f}")
json.dump(rows,open("smooth.json","w"),indent=0)
