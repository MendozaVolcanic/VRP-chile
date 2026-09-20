import sys; sys.argv=[sys.argv[0]]
from g_control import *
rf=ref()
out=[]
for v in ["Lastarria","Isluga","Lascar","Villarrica","Tupungatito","PlanchonPeteroa","Llaima","Copahue","Chaiten"]:
    y=cfg[v]; center=(y["mirova_center_lat"],y["mirova_center_lon"]); vent=(y.get("vent_lat",y["lat"]),y.get("vent_lon",y["lon"]))
    r=rf[(rf.Volcan==v)&(rf.t.dt.hour<12)]
    g=r.groupby("t")
    tv=idx[(idx.volcano==v)&idx.own&(idx.lat_h<=8)]
    for t,grp in g:
        tipo="ALERTA" if grp.Tipo_Registro.str.startswith("ALERTA").any() else ("RUTINA" if (grp.Tipo_Registro=="RUTINA").all() and (grp.VRP_MW==0).all() else "otro")
        if tipo=="otro": continue
        dt=(tv.acquisition_utc-t).abs().dt.total_seconds(); c=tv[dt<=120]
        if c.empty: continue
        c=c.iloc[0]
        if not os.path.exists(c.path): continue
        a=grp[grp.Tipo_Registro.str.startswith("ALERTA")]
        dist=float(a.Distancia_km.iloc[0]) if len(a) and pd.notna(a.Distancia_km.iloc[0]) else 0.0
        vrp=float(a.VRP_MW.max()) if len(a) else 0.0
        res=analiza(c.path,center,vent,max(4.0,dist+1.0))
        if res["med"]>=0.2: continue
        out.append(dict(vol=v,t=str(t)[:16],tipo=tipo,vrp=vrp,dist=dist,**{k:res[k] for k in ["seed_dvent","z","z_vent"]}))
df=pd.DataFrame(out); df.to_csv("neg_seed.csv",index=False)
df["bin"]=pd.cut(df.seed_dvent,[0,0.75,1.5,2.0,3.2,99])
print(pd.crosstab([df.vol,df.tipo],df.bin))
print(df.groupby(["vol","tipo"]).z.describe()[["count","25%","50%","75%"]])
