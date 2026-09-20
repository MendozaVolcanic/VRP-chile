# Construye los pools de las Partes B, C y H con las reglas de la v2, SIN clasificar.
import sys
from common import *
sys.path.insert(0,ROOT+"/scripts")
idx=load_idx(); rf=ref()
zmin=json.load(open("zmin.json"))
def bucket(s):
    s=s or ""
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
out=[]
for v in VOLS:
    rn=CSVN.get(v,v); tv=idx[idx.volcano==TIFN.get(v,v)]
    r=rf[rf.Volcan==rn]
    recs=json.load(open(f"{ROOT}/data/mirova_equivalent/{v}.json",encoding="utf-8"))["records"]
    for rec in recs:
        b=bucket(rec.get("sensor"))
        if rec.get("datetime_utc","")<"2026-05-01": continue
        pc=rec.get("primary_cluster") or {}
        t=pd.Timestamp(rec["datetime_utc"],tz="UTC")
        g=r[(r.t-t).abs().dt.total_seconds()<=120]
        al=g[g.Tipo_Registro.str.startswith("ALERTA")]
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        if c.empty: continue
        c=c.iloc[0]
        if not os.path.exists(c.path): st="no_local"
        elif not c.own: st="no_propia"
        else:
            R=raster(c.path); st="usable" if R["med"]<0.2 else "diurna"
        n1=pc.get("n_pixels")==1 and pc.get("centroid_lat") is not None and rec.get("final_hotspot_lat") is not None
        d=dict(vol=v,t=t,b=b,st=st,n_al=len(al),n_al_cons=(al.src=="CONS").sum(),n_al_ocr=(al.src=="OCR").sum(),
               dists=tuple(sorted(set(al.Distancia_km.dropna().round(3)))),
               cons_rut0=((g.src=="CONS")&(g.Tipo_Registro=="RUTINA")&(g.VRP_MW==0)).any(),
               anyfp=g.Tipo_Registro.str.startswith("FALSO").any(),
               src=rec.get("final_hotspot_source"),npx=pc.get("n_pixels"),dc=rec.get("distance_class"),lat_h=c.lat_h,
               tramo="post" if t>=CUT else "pre")
        if pc.get("centroid_lat") is not None and rec.get("final_hotspot_lat") is not None:
            P=(pc["centroid_lat"],pc["centroid_lon"]); F=(rec["final_hotspot_lat"],rec["final_hotspot_lon"])
            d.update(P=P,F=F,dPF=float(hav(*P,*F)),dPv=float(hav(*P,*vent(v))),dFv=float(hav(*F,*vent(v))),dPmc=float(hav(*P,*mc(v))),dFmc=float(hav(*F,*mc(v))),
                     pc_dist_inner=pc.get("centroid_dist_km"))
        if st=="usable":
            d["nan_frac"]=float(np.isnan(R["z"]).mean())
            if "P" in d:
                d["zP_nan"]=np.isnan(zcell(R,d["P"])[0]); d["zF_nan"]=np.isnan(zcell(R,d["F"])[0])
        d["path"]=c.path
        out.append(d)
df=pd.DataFrame(out); df.to_pickle("pool.pkl")
print(df.groupby(["b","st"]).size())
