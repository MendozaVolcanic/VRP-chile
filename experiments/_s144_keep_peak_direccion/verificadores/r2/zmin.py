from common import *
idx=load_idx(); rf=ref()
rows=[]
for v in VOLS:
    rn=CSVN.get(v,v); tv=idx[idx.volcano==TIFN.get(v,v)].sort_values("acquisition_utc")
    r=rf[(rf.Volcan==rn)&(rf.t>=pd.Timestamp("2026-05-09",tz="UTC"))]
    for t,g in r.groupby("t"):
        cons_rut=((g.src=="CONS")&(g.Tipo_Registro=="RUTINA")&(g.VRP_MW==0)).any()
        if not cons_rut: continue
        pure=(g.Tipo_Registro=="RUTINA").all()
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        if c.empty: continue
        c=c.iloc[0]
        if not c.own or not os.path.exists(c.path): continue
        R=raster(c.path)
        if R["med"]>=0.2: continue
        dv=hav(R["lat"],R["lon"],*vent(v))
        s=seed(R,dv<=3.4)
        if s is None or not ((dv<=3.4)&np.isfinite(R["z"])).any():
            print("SIN_CELDAS",v,t,c.path[-60:],R["epsg"],float(np.nanmin(dv))); continue
        # celda al azar dentro del disco (nulo de celda individual)
        rng=np.random.default_rng(abs(hash((v,str(t))))%2**32)
        cand=np.argwhere((dv<=3.4)&np.isfinite(R["z"]))
        rc=cand[rng.integers(len(cand))]
        rows.append(dict(vol=v,t=t,pure=pure,hour=t.hour,tramo="post" if t>=CUT else "pre",zseed=s["z"],zrand=float(R["z"][tuple(rc)]),lat_h=c.lat_h))
df=pd.DataFrame(rows); df.to_pickle("rutina.pkl")
pd.set_option("display.width",200)
print(df.groupby("vol").agg(n=("zseed","size"),n_pure=("pure","sum"),n_pre=("tramo",lambda s:(s=="pre").sum()),zmin=("zseed",lambda s:s.quantile(.9)),zmed=("zseed","median")).round(2))
zm=df.groupby("vol").zseed.quantile(.9)
df["zm"]=df.vol.map(zm)
print("frac celda al azar con z>=zmin por volcan"); print(df.assign(x=df.zrand>=df.zm).groupby("vol").x.mean().round(3))
print("zmin por tramo"); print(df.groupby(["vol","tramo"]).zseed.quantile(.9).unstack().round(2))
json.dump(zm.round(4).to_dict(),open("zmin.json","w"),indent=1)
