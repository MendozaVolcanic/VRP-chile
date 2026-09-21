# -*- coding: utf-8 -*-
"""Puede existir un pico de UNA sola celda en el campo de MIROVA?  Y correlacion espacial."""
import json, numpy as np, rasterio, collections
P=[p for p in json.load(open("pares.json")) if p["zen"] is not None]
rows=[]
for p in P:
    with rasterio.open(p["tif"]) as ds: a=ds.read(1).astype(float)
    # exceso de cada celda sobre la media de sus 8 vecinos, normalizado por la sd del disco 5km
    c=a[1:-1,1:-1]
    nb=(a[:-2,:-2]+a[:-2,1:-1]+a[:-2,2:]+a[1:-1,:-2]+a[1:-1,2:]+a[2:,:-2]+a[2:,1:-1]+a[2:,2:])/8.0
    e=c-nb
    s=np.nanstd(a)
    en=e/s
    # correlacion a lag 1..4 (promedio x,y)
    ac=[]
    for L in (1,2,3,4):
        x0=a[:,:-L].ravel(); x1=a[:,L:].ravel(); k=np.isfinite(x0)&np.isfinite(x1)
        r1=np.corrcoef(x0[k],x1[k])[0,1]
        y0=a[:-L,:].ravel(); y1=a[L:,:].ravel(); k=np.isfinite(y0)&np.isfinite(y1)
        r2=np.corrcoef(y0[k],y1[k])[0,1]
        ac.append((r1+r2)/2)
    rows.append(dict(vol=p["vol"],zen=p["zen"],
                     max_en=float(np.nanmax(en)), p9999=float(np.nanpercentile(en,99.99)),
                     frac_gt2=float(np.nanmean(en>2)), frac_gt3=float(np.nanmean(en>3)),
                     ac1=ac[0],ac2=ac[1],ac3=ac[2],ac4=ac[3]))
import statistics as st
print("n TIF VIIRS375 (2026-05-09..20):",len(rows))
print("maximo exceso de UNA celda sobre sus 8 vecinos, en unidades de sd de la escena:")
print("   mediana del maximo por imagen: %.2f  |  p90 %.2f  |  maximo global %.2f"%(
    st.median([r['max_en'] for r in rows]), np.percentile([r['max_en'] for r in rows],90), max(r['max_en'] for r in rows)))
print("   fraccion de celdas con exceso >2 sd: mediana %.6f ; >3 sd: mediana %.6f"%(
    st.median([r['frac_gt2'] for r in rows]), st.median([r['frac_gt3'] for r in rows])))
print("correlacion espacial del campo (lag en celdas de 0,375 km):")
for L,k in [(1,'ac1'),(2,'ac2'),(3,'ac3'),(4,'ac4')]:
    print("   lag %d (%.2f km): mediana r=%.4f"%(L,L*0.375,st.median([r[k] for r in rows])))
lo=[r for r in rows if r['zen']<30]; hi=[r for r in rows if r['zen']>=52]
for nm,g in [("nadir <30",lo),("borde >=52",hi)]:
    print(f"  {nm:12s} n={len(g)} r(lag1)={st.median([r['ac1'] for r in g]):.4f} r(lag2)={st.median([r['ac2'] for r in g]):.4f} r(lag3)={st.median([r['ac3'] for r in g]):.4f} r(lag4)={st.median([r['ac4'] for r in g]):.4f}")
json.dump(rows,open("picos.json","w"),indent=0)
