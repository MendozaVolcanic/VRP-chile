from common import *
B=pd.read_pickle("B.pkl"); zmin=json.load(open("zmin.json")); idx=load_idx()
pool=pd.read_pickle("pool.pkl")
# TIF nocturnos usables por volcan (para placebo): de pool V375 usable (unicos por path)
noct=pool[(pool.b=="VIIRS375")&(pool.st=="usable")].drop_duplicates("path")[["vol","t","path"]]
rng=np.random.default_rng(144)
rows=[]
for _,b in B.sort_values(["vol","t"]).iterrows():
    v=b.vol
    for which,Dist in [("CONS",None),("OCR",None)]:
        pass
    dists=list(b.dists)
    res=dict(vol=v,t=b.t,tramo=b.tramo,cerca=b.cerca,inreg=b.P_in and b.F_in,src=b.src,ndist=len(dists))
    for k,Dist in enumerate([dists[0],dists[-1]]):
        R=raster(b.path)
        dv=hav(R["lat"],R["lon"],*vent(v)); dm=hav(R["lat"],R["lon"],*mc(v))
        reg=(dv<=3.4)|(dm<=Dist+1); ring=reg&(np.abs(dm-Dist)<=0.6)
        dP=hav(R["lat"],R["lon"],*b.P); dF=hav(R["lat"],R["lon"],*b.F)
        # P alcanzable: celda del anillo a <=T de P y >T de F ; F alcanzable: celda a <=T de F y >2T de P
        res[f"Preach{k}"]=bool((ring&(dP<=0.75)&(dF>0.75)).any())
        res[f"Freach{k}"]=bool((ring&(dF<=0.75)&(dP>1.5)).any())
        res[f"Oreach{k}"]=bool((ring&(dF>0.75)&(dP>1.5)).any())
        res[f"nring{k}"]=int(ring.sum())
        s=seed(R,ring); res[f"id{k}"]=bool(s is not None and s["z"]>=zmin[v])
        # placebo
        cand=noct[(noct.vol==v)&((noct.t-b.t).abs()>pd.Timedelta(days=3))]
        pp=cand.path.iloc[rng.integers(len(cand))]
        R2=raster(pp); dv2=hav(R2["lat"],R2["lon"],*vent(v)); dm2=hav(R2["lat"],R2["lon"],*mc(v))
        ring2=((dv2<=3.4)|(dm2<=Dist+1))&(np.abs(dm2-Dist)<=0.6)
        s2=seed(R2,ring2); res[f"plac{k}"]=bool(s2 is not None and s2["z"]>=zmin[v])
    rows.append(res)
df=pd.DataFrame(rows); df.to_pickle("ident.pkl")
df["fuera"]=df.vol=="Lastarria"
pd.set_option("display.width",250)
e=df[df.inreg&~df.cerca]
print("elegibles (en region, no cerca):",len(e)," fuera de Lastarria:",(~e.fuera).sum())
print(pd.crosstab([e.fuera],[e.Preach0,e.Freach0],rownames=["Lastarria"],colnames=["P alcanzable","F alcanzable"]))
print("con la otra distancia:"); print(pd.crosstab([e.fuera],[e.Preach1,e.Freach1]))
for k in (0,1):
    g=e.groupby("fuera").agg(n=("vol","size"),ident=(f"id{k}","sum"),plac=(f"plac{k}","sum"))
    print("distancia",k); print(g)
print(e.groupby("vol").agg(n=("vol","size"),Preach=("Preach0","sum"),Freach=("Freach0","sum"),ident=("id0","sum"),plac=("plac0","sum"),ident1=("id1","sum"),tramo_post=("tramo",lambda s:(s=="post").sum())))
