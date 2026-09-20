from common import *
df=pd.read_pickle("pool.pkl"); zmin=json.load(open("zmin.json"))
df["pat"]=(df.npx==1)&(df.dPF>0.5)
pd.set_option("display.width",220); pd.set_option("display.max_rows",200)
print("== patron + alerta, por sensor y estado del TIF")
x=df[df.pat&(df.n_al>0)]
print(pd.crosstab(x.b,x.st))
B=x[(x.b=="VIIRS375")&(x.st=="usable")].copy()
print("== Parte B (V375, usable) por volcan y tramo:"); print(pd.crosstab(B.vol,B.tramo,margins=True))
print("== alertas con varias distancias distintas en la misma pasada:",(B.dists.map(len)>1).sum(), " sin distancia:",(B.dists.map(len)==0).sum())
print(B[B.dists.map(len)!=1][["vol","t","n_al_cons","n_al_ocr","dists"]])
print("== CONS/OCR:",pd.crosstab(B.n_al_cons>0,B.n_al_ocr>0))
B["Dist"]=B.dists.map(lambda s: s[0] if len(s) else np.nan)
B["Rmc"]=B.Dist+1
B["P_in"]=(B.dPv<=3.4)|(B.dPmc<=B.Rmc); B["F_in"]=(B.dFv<=3.4)|(B.dFmc<=B.Rmc)
B["cerca"]=B.dPF<1.5
print("== fuera de region (P o F):"); print(pd.crosstab(B.vol,~(B.P_in&B.F_in)))
print("== cerca (dPF<1.5) por volcan:"); print(pd.crosstab(B.vol,B.cerca))
print("== NaN en celda de P o F:",(B.zP_nan|B.zF_nan).sum(), " nan_frac>0.5:",(B.nan_frac>0.5).sum())
B.to_pickle("B.pkl")
