import sys; sys.argv=[sys.argv[0]]
from g_control import *
sys.path.insert(0,ROOT+"/scripts")
import banco_paridad as bp, glob, collections
rf=ref()
NM={"Lascar":"Lascar","Villarrica":"Villarrica","Lastarria":"Lastarria","Isluga":"Isluga","Tupungatito":"Tupungatito","PlanchonPeteroa":"PlanchonPeteroa","Chaiten":"Chaiten","Llaima":"Llaima","Copahue":"Copahue","NevadosDeChillan":"Nevados de Chillan","PuyehueCordonCaulle":"Puyehue-Cordon Caulle"}
TIFV={"NevadosDeChillan":"ChillanNevadosde"}
rows=[]
for v,rn in NM.items():
    y=cfg[v]; mc=(y["mirova_center_lat"],y["mirova_center_lon"])
    recs=json.load(open(f"{ROOT}/data/mirova_equivalent/{v}.json",encoding="utf-8"))["records"]
    al=rf[(rf.Volcan==rn)&rf.Tipo_Registro.str.startswith("ALERTA")&(rf.VRP_MW>0)]
    tv=idx[idx.volcano==TIFV.get(v,v)]
    for r in recs:
        if bp.bucket(r["sensor"])!="VIIRS375" or r["datetime_utc"]<"2026-05-09" or int(r["datetime_utc"][11:13])>=12: continue
        pc=r.get("primary_cluster") or {}
        if pc.get("n_pixels")!=1 or pc.get("centroid_lat") is None or r.get("final_hotspot_lat") is None: continue
        P=(pc["centroid_lat"],pc["centroid_lon"]);F=(r["final_hotspot_lat"],r["final_hotspot_lon"])
        if hav(*P,*F)<=0.5: continue
        t=pd.Timestamp(r["datetime_utc"],tz="UTC")
        a=al[(al.t-t).abs().dt.total_seconds()<=120]
        if a.empty: continue
        a=a.sort_values("src")  # CONS antes que OCR
        dist=a.Distancia_km.iloc[0]; dist=float(dist) if pd.notna(dist) else 0.0
        R=max(4.0,dist+1.0)
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        st="sin_tif"
        if len(c):
            c=c.iloc[0]
            if not c.own: st="no_propia"
            elif c.lat_h>8: st="latencia"
            elif not os.path.exists(c.path): st="no_local"
            else:
                with rasterio.open(c.path) as ds: med=float(np.nanmedian(ds.read(1)))
                st="usable" if med<0.2 else "diurna"
        rows.append(dict(vol=v,t=r["datetime_utc"],src=r.get("final_hotspot_source"),st=st,P_in_R=hav(*P,*mc)<=R-0.375,F_in_R=hav(*F,*mc)<=R-0.375,dist=dist))
df=pd.DataFrame(rows)
print(pd.crosstab([df.vol],df.st,margins=True).to_string())
u=df[df.st=="usable"]
print(pd.crosstab([u.vol,u.src],[u.P_in_R,u.F_in_R]).to_string())
print("usable fuera de Lastarria",(u.vol!="Lastarria").sum(),"de ellos P fuera del disco",((u.vol!="Lastarria")&~u.P_in_R).sum())
