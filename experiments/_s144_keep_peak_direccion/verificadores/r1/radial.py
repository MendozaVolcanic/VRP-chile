import sys; sys.argv=[sys.argv[0]]
from g_control import *
rf=ref()
for v,rn in [("Villarrica","Villarrica"),("Llaima","Llaima"),("Lastarria","Lastarria"),("Lascar","Lascar")]:
    y=cfg[v]; vent=(y.get("vent_lat",y["lat"]),y.get("vent_lon",y["lon"]))
    r=rf[(rf.Volcan==rn)&(rf.t.dt.hour<12)]
    rut=[t for t,g in r.groupby("t") if (g.Tipo_Registro=="RUTINA").all() and (g.VRP_MW==0).all()]
    tv=idx[(idx.volcano==v)&idx.own&(idx.lat_h<=8)]
    profs=[];dprofs=[]
    for t in rut:
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        if c.empty or not os.path.exists(c.iloc[0].path): continue
        with rasterio.open(c.iloc[0].path) as ds:
            L=ds.read(1).astype(float)
            rows,cols=np.indices(L.shape); xs,ys=rasterio.transform.xy(ds.transform,rows.ravel(),cols.ravel())
        lat=np.array(ys).reshape(L.shape);lon=np.array(xs).reshape(L.shape)
        if np.nanmedian(L)>=0.2: continue
        P=np.pad(L,1,constant_values=np.nan)
        nb=np.nanmean(np.stack([P[1+a:1+a+L.shape[0],1+b:1+b+L.shape[1]] for a in (-1,0,1) for b in (-1,0,1) if (a,b)!=(0,0)]),axis=0)
        dL=L-nb
        d=hav(lat,lon,*vent)
        bins=[0,0.75,1.5,2.25,3.0,3.75,5,8]
        profs.append([np.nanmean(L[(d>=bins[i])&(d<bins[i+1])]) for i in range(len(bins)-1)])
        dprofs.append([np.nanmean(dL[(d>=bins[i])&(d<bins[i+1])]) for i in range(len(bins)-1)])
    if profs:
        print(v,"n",len(profs),"L medio por anillo desde el crater",np.round(np.nanmedian(profs,axis=0),4))
        print(v,"      dL0 medio por anillo",np.round(np.nanmedian(dprofs,axis=0),5))
