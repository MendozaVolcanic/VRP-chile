# Verificador v2 S144: funciones comunes (solo lectura)
import pandas as pd, numpy as np, rasterio, os, math, yaml, json, warnings, functools
from rasterio.warp import transform as wtransform
warnings.filterwarnings("ignore")
ROOT="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TD=ROOT+"/experiments/_s144_conteo_tif/_dl_tif/"
cfg={v["name"]:v for v in yaml.safe_load(open(ROOT+"/volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
VOLS=["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
CSVN={"NevadosDeChillan":"Nevados de Chillan","PuyehueCordonCaulle":"Puyehue-Cordon Caulle"}
TIFN={"NevadosDeChillan":"ChillanNevadosde"}
CUT=pd.Timestamp("2026-08-28 23:00",tz="UTC")
def hav(a,b,c,d):
    p=np.radians; x=np.sin(p(c-a)/2)**2+np.cos(p(a))*np.cos(p(c))*np.sin(p(d-b)/2)**2
    return 2*6371.0088*np.arcsin(np.sqrt(x))
def vent(v): y=cfg[v]; return (y["vent_lat"],y["vent_lon"])
def mc(v): y=cfg[v]; return (y["mirova_center_lat"],y["mirova_center_lon"])
def load_idx(sensor="VIIRS375"):
    idx=pd.read_csv(TD+"da4fe36e8920_index.csv")
    for c in ["captured_at_utc","acquisition_utc","last_modified_utc"]:
        idx[c]=pd.to_datetime(idx[c],utc=True,format="mixed",errors="coerce")
    if sensor: idx=idx[idx.sensor==sensor]
    idx=idx[idx.acquisition_utc.notna()&(idx.size_bytes>0)].copy()
    idx["firstcap"]=idx.md5.map(idx.groupby("md5").captured_at_utc.min())
    idx["firstacq"]=idx.md5.map(idx.groupby(["volcano","md5"]).acquisition_utc.min().droplevel(0).groupby(level=0).min()) if False else None
    fa=idx.groupby(["volcano","md5"]).acquisition_utc.min().rename("firstacq_v").reset_index()
    idx=idx.drop(columns=["firstacq"]).merge(fa,on=["volcano","md5"],how="left")
    idx["own"]=idx.acquisition_utc==idx.firstacq_v
    idx["lat_h"]=(idx.firstcap-idx.acquisition_utc).dt.total_seconds()/3600
    idx["path"]=TD+"da4fe36e8920/"+idx.tif_path
    idx=idx.sort_values("captured_at_utc").drop_duplicates(["volcano","acquisition_utc"])
    return idx
def ref():
    cons=pd.read_csv(TD+"referencia/3b18c772f65a_registro_vrp_consolidado.csv"); cons["src"]="CONS"
    ocr=pd.read_csv(TD+"referencia/7e3438046ca1_registro_vrp_ocr.csv"); ocr["src"]="OCR"
    d=pd.concat([cons,ocr]); d=d[d.Sensor=="VIIRS375"].copy()
    d["t"]=pd.to_datetime(d.Fecha_Satelite_UTC,utc=True)
    return d
@functools.lru_cache(maxsize=4000)
def raster(path):
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
    edge=np.zeros(L.shape,bool); edge[0,:]=edge[-1,:]=edge[:,0]=edge[:,-1]=True
    fin=dL[~edge]; fin=fin[np.isfinite(fin)]
    sig=1.4826*np.median(np.abs(fin-np.median(fin)))
    z=dL/sig; z[edge]=np.nan
    return dict(z=z,lat=lat,lon=lon,med=float(np.nanmedian(L)),epsg=crs.to_epsg())
def zcell(R,pt):
    d=hav(R["lat"],R["lon"],pt[0],pt[1]); i=np.unravel_index(np.nanargmin(d),d.shape)
    return float(R["z"][i]), float(d[i])
def seed(R,mask):
    zz=np.where(mask&np.isfinite(R["z"]),R["z"],-np.inf)
    if not np.isfinite(zz).any() or zz.max()==-np.inf: return None
    i=np.unravel_index(np.argmax(zz),zz.shape)
    return dict(z=float(R["z"][i]),lat=float(R["lat"][i]),lon=float(R["lon"][i]))
