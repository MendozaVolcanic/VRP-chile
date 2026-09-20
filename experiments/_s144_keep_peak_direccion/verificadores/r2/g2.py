from common import *
idx=load_idx(); rf=ref(); zmin=json.load(open("zmin.json"))
rows=[]
for v in ["Lascar","Villarrica"]+[x for x in VOLS if x not in ("Lascar","Villarrica")]:
    rn=CSVN.get(v,v); tv=idx[idx.volcano==TIFN.get(v,v)]
    a=rf[(rf.Volcan==rn)&rf.Tipo_Registro.str.startswith("ALERTA")]
    for t,g in a.groupby("t"):
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        if c.empty: continue
        c=c.iloc[0]
        if not c.own or not os.path.exists(c.path): continue
        R=raster(c.path)
        if R["med"]>=0.2: continue
        dv=hav(R["lat"],R["lon"],*vent(v)); s=seed(R,dv<=4)
        if s is None: continue
        rS=hav(s["lat"],s["lon"],*mc(v))
        for src in ("CONS","OCR"):
            gg=g[g.src==src]
            if gg.empty: continue
            D=float(gg.Distancia_km.iloc[0])
            rows.append(dict(vol=v,t=t,src=src,vrp=float(g.VRP_MW.max()),Dist=D,dseed=float(hav(s["lat"],s["lon"],*vent(v))),rS=float(rS),
                dn=(s["lat"]-vent(v)[0])*111.195,de=(s["lon"]-vent(v)[1])*111.195*math.cos(math.radians(vent(v)[0])),z=s["z"],lat_h=c.lat_h))
df=pd.DataFrame(rows); df.to_pickle("g2.pkl")
G=df[(df.vol.isin(["Lascar","Villarrica"]))&(df.vrp>=0.3)].drop_duplicates("t")
print("G v2 (sin latencia): n",len(G),G.vol.value_counts().to_dict(),"frac<=0.75",round((G.dseed<=0.75).mean(),3),"mediana",round(G.dseed.median(),3),"dn",round(G.dn.mean(),3),"de",round(G.de.mean(),3))
G8=G[G.lat_h<=8]; print("G lat<=8: n",len(G8),"frac",round((G8.dseed<=0.75).mean(),3),"dn",round(G8.dn.mean(),3),"de",round(G8.de.mean(),3))
# residuo del anillo: semilla con z alto y cerca del crater (objeto = crater), |rS - Dist|
H=df[(df.dseed<=0.75)&(df.z>=df.vol.map(zmin))]
H["res"]=(H.rS-H.Dist).abs()
print("residuo |r_semilla(mc) - Distancia| en alertas con semilla en el crater y z>=zmin, por volcan y fuente:")
print(H.groupby(["vol","src"]).res.agg(["size","median",lambda s:(s>0.6).mean()]).round(2))
