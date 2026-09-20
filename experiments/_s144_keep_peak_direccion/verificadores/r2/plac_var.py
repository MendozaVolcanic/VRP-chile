from common import *
B=pd.read_pickle("B.pkl"); zmin=json.load(open("zmin.json")); pool=pd.read_pickle("pool.pkl")
noct=pool[(pool.b=="VIIRS375")&(pool.st=="usable")].drop_duplicates("path")[["vol","t","path"]]
E=B[B.P_in&B.F_in&~B.cerca&(B.vol!="Lastarria")]
# precomputar identidad placebo de cada (pasada, tif candidato)
tab=[]
for _,b in E.iterrows():
    D=b.dists[0]; cand=noct[(noct.vol==b.vol)&((noct.t-b.t).abs()>pd.Timedelta(days=3))]
    ids=[]
    for p in cand.path:
        R=raster(p); dv=hav(R["lat"],R["lon"],*vent(b.vol)); dm=hav(R["lat"],R["lon"],*mc(b.vol))
        s=seed(R,((dv<=3.4)|(dm<=D+1))&(np.abs(dm-D)<=0.6)); ids.append(bool(s is not None and s["z"]>=zmin[b.vol]))
    tab.append((b.vol,np.array(ids)))
for v,a in tab: pass
print("tasa placebo esperada por pasada:",[ (v,round(a.mean(),2)) for v,a in tab])
exp=np.mean([a.mean() for v,a in tab]); print("tasa esperada media",round(exp,3),"n",len(tab))
sims=[]
for s in range(2000):
    r=np.random.default_rng(s); sims.append(np.mean([a[r.integers(len(a))] for v,a in tab]))
sims=np.array(sims); print("percentiles placebo",np.percentile(sims,[5,50,95]).round(3))
print("frac simulaciones con real(12/19) - placebo < 0.20:",round((12/19-sims<0.20-1e-9).mean(),3))
# placebo solo de TIF de pasadas RUTINA puras?
