# Verificador S144: control G del pre-registro keep_peak, medido sobre datos locales (solo lectura)
import pandas as pd, numpy as np, rasterio, os, math, yaml, re, sys, json, warnings
from rasterio.warp import transform as wtransform
warnings.filterwarnings("ignore")
ROOT="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TD=ROOT+"/experiments/_s144_conteo_tif/_dl_tif/"
cfg={v["name"]:v for v in yaml.safe_load(open(ROOT+"/volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
idx=pd.read_csv(TD+"da4fe36e8920_index.csv")
for c in ["captured_at_utc","acquisition_utc","last_modified_utc"]:
    idx[c]=pd.to_datetime(idx[c],utc=True,format="mixed",errors="coerce")
idx=idx[(idx.sensor=="VIIRS375")&idx.acquisition_utc.notna()&(idx.size_bytes>0)].copy()
idx["firstcap"]=idx.md5.map(idx.groupby("md5").captured_at_utc.min())
idx["firstacq"]=idx.md5.map(idx.groupby("md5").acquisition_utc.min())
idx["lat_h"]=(idx.firstcap-idx.acquisition_utc).dt.total_seconds()/3600
idx["own"]=idx.acquisition_utc==idx.firstacq
idx["path"]=TD+"da4fe36e8920/"+idx.tif_path
idx=idx.sort_values("captured_at_utc").drop_duplicates(["volcano","acquisition_utc"])
def hav(a,b,c,d):
    p=np.radians; x=np.sin(p(c-a)/2)**2+np.cos(p(a))*np.cos(p(c))*np.sin(p(d-b)/2)**2
    return 2*6371.0088*np.arcsin(np.sqrt(x))
def ref():
    cons=pd.read_csv(TD+"referencia/3b18c772f65a_registro_vrp_consolidado.csv"); cons["src"]="CONS"
    ocr=pd.read_csv(TD+"referencia/7e3438046ca1_registro_vrp_ocr.csv"); ocr["src"]="OCR"
    d=pd.concat([cons,ocr]); d=d[d.Sensor=="VIIRS375"]
    d["t"]=pd.to_datetime(d.Fecha_Satelite_UTC,utc=True)
    return d
def analiza(path,center,vent,R):
    with rasterio.open(path) as ds:
        L=ds.read(1).astype(float); crs=ds.crs
        rows,cols=np.indices(L.shape)
        xs,ys=rasterio.transform.xy(ds.transform,rows.ravel(),cols.ravel())
        xs=np.array(xs);ys=np.array(ys)
        if crs.to_epsg()!=4326:
            lon,lat=wtransform(crs,"EPSG:4326",xs,ys); lon=np.array(lon);lat=np.array(lat)
        else: lon,lat=xs,ys
    lat=lat.reshape(L.shape);lon=lon.reshape(L.shape)
    P=np.pad(L,1,mode="constant",constant_values=np.nan)
    nb=np.nanmean(np.stack([P[1+di:1+di+L.shape[0],1+dj:1+dj+L.shape[1]] for di in (-1,0,1) for dj in (-1,0,1) if (di,dj)!=(0,0)]),axis=0)
    dL=L-nb
    fin=dL[1:-1,1:-1].ravel(); fin=fin[np.isfinite(fin)]
    sig=1.4826*np.median(np.abs(fin-np.median(fin)))
    rc=hav(lat,lon,center[0],center[1])
    m=(rc<=R)&np.isfinite(dL)
    m[0,:]=m[-1,:]=m[:,0]=m[:,-1]=False
    i=np.nanargmax(np.where(m,dL,-np.inf))
    r,c=np.unravel_index(i,L.shape)
    sl,so=lat[r,c],lon[r,c]
    dv=hav(sl,so,vent[0],vent[1])
    # desplazamiento N-S y E-O en km
    dn=(sl-vent[0])*111.195; de=(so-vent[1])*111.195*math.cos(math.radians(vent[0]))
    # z del crater y rango
    vr=np.unravel_index(np.argmin(hav(lat,lon,vent[0],vent[1])),L.shape)
    return dict(seed_dvent=float(dv),dn=float(dn),de=float(de),z=float(dL[r,c]/sig),med=float(np.nanmedian(L)),epsg=crs.to_epsg(),
                z_vent=float(dL[vr]/sig), L_seed=float(L[r,c]), cell_km=(float(hav(lat[0,0],lon[0,0],lat[1,0],lon[1,0])),float(hav(lat[0,0],lon[0,0],lat[0,1],lon[0,1]))))
if __name__=="__main__":
    VOLS=sys.argv[1].split(",") ; VRPMIN=float(sys.argv[2])
    rf=ref()
    names={"Lascar":"Lascar","Villarrica":"Villarrica","Lastarria":"Lastarria","Isluga":"Isluga","Tupungatito":"Tupungatito","PlanchonPeteroa":"PlanchonPeteroa","Chaiten":"Chaiten","Llaima":"Llaima","Copahue":"Copahue"}
    out=[]
    for v in VOLS:
        y=cfg[v]; center=(y["mirova_center_lat"],y["mirova_center_lon"]); vent=(y.get("vent_lat",y["lat"]),y.get("vent_lon",y["lon"]))
        a=rf[(rf.Volcan==v)&rf.Tipo_Registro.str.startswith("ALERTA")&(rf.VRP_MW>=VRPMIN)&(rf.t.dt.hour<12)]
        a=a.sort_values(["t","src"]).drop_duplicates("t")
        tv=idx[idx.volcano==v]
        for _,al in a.iterrows():
            dt=(tv.acquisition_utc-al.t).abs().dt.total_seconds()
            cand=tv[dt<=120]
            rec=dict(vol=v,t=str(al.t)[:16],vrp=al.VRP_MW,dist=al.Distancia_km,src=al.src)
            if cand.empty: rec["estado"]="sin_tif"; out.append(rec); continue
            c=cand.iloc[0]
            rec.update(own=bool(c.own),lat_h=round(c.lat_h,2),exists=os.path.exists(c.path))
            if not rec["exists"]: rec["estado"]="no_local"; out.append(rec); continue
            try: dist=float(al.Distancia_km)
            except: dist=0.0
            if not np.isfinite(dist): dist=0.0
            R=max(4.0,dist+1.0)
            rec.update(analiza(c.path,center,vent,R))
            rec["estado"]="usable" if (rec["own"] and rec["lat_h"]<=8 and rec["med"]<0.2) else "excluido"
            out.append(rec)
    df=pd.DataFrame(out)
    pd.set_option("display.width",250); pd.set_option("display.max_rows",500)
    print(df.drop(columns=[c for c in ["cell_km"] if c in df]).to_string())
    print(df.estado.value_counts())
    u=df[df.estado=="usable"]
    for lab,s in [("usable",u),("todos con TIF (sin corte latencia)",df[df.get("med",pd.Series(dtype=float)).notna()&(df.get("med",0)<0.2)])]:
        if len(s): print(lab,"n",len(s),"frac<=0.75",(s.seed_dvent<=0.75).mean().round(3),"mediana",s.seed_dvent.median().round(3),"dn medio",s.dn.mean().round(3),"de medio",s.de.mean().round(3), "z med",s.z.median().round(2))
    if "cell_km" in df: print("celda km (NS,EO) ejemplo",df.cell_km.dropna().iloc[0])
