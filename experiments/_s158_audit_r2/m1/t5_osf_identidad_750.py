# M1 T5. Recuento independiente de F6-H1 / V1 F6-1 (VRP del OSF v2.5 en VIIRS 750 no cumple VRP = 1.97e7*0.5625*dL
# sobre 50 grados de cenit). Escrito desde cero. Pregunta 1: si el hallazgo fuera un artefacto del umbral de
# tolerancia (|r-1|>=1e-4) o de como se calcula dL, el barrido de tolerancias y la variante con Tot_Lmir_bk
# distinto lo mostraria. Pregunta 2: control positivo en los otros dos sensores con su propio k (deben cumplir 100%),
# y control negativo (k de 750 aplicado a 375: debe fallar casi todo).
import pandas as pd,numpy as np
p=r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv'
d=pd.read_csv(p,usecols=['Resolution','SatZen','Npix','Tot_Lmir_hot','Tot_Lmir_bk','VRP','Dayflag','Satellite'])
print('filas',len(d),d.Resolution.value_counts().to_dict())
K={750:1.97e7*0.5625,375:18.0*140625,1000:18.9e6}
print('claves Resolution:',sorted(d.Resolution.unique()))
d['dL']=d.Tot_Lmir_hot-d.Tot_Lmir_bk
for res,k in [(750,K[750]),(375,K[375])]:
    s=d[d.Resolution==res]
    r=s.VRP/(k*s.dL)
    print(f'--- Resolution {res}: n={len(s)} k={k:,.0f}')
    for tol in [1e-6,1e-4,1e-3,1e-2,5e-2]:
        bad=(np.abs(r-1)>=tol)
        print(f'  tol {tol:g}: fuera {bad.sum()} ({bad.mean()*100:.2f}%) | sobre 50deg {bad[s.SatZen>50].sum()} de {(s.SatZen>50).sum()} | <=50deg {bad[s.SatZen<=50].sum()} de {(s.SatZen<=50).sum()}')
mod=d[d.Resolution==1000]
if len(mod)==0: mod=d[~d.Resolution.isin([375,750])]
print('MODIS (res!=375/750) n=',len(mod), 'valores res:',mod.Resolution.unique()[:5])
r=mod.VRP/(K[1000]*mod.dL); print('  MODIS fuera tol1e-4:',(np.abs(r-1)>=1e-4).sum())
# control negativo: k750 sobre 375
s=d[d.Resolution==375]; r=s.VRP/(K[750]*s.dL); print('control neg: k750 sobre 375 fuera tol1e-4:',(np.abs(r-1)>=1e-4).sum(),'de',len(s))
# escalon en 50: fraccion fuera por bin de 0.5 grados alrededor de 50 en 750 con dL*k>100MW
s=d[(d.Resolution==750)].copy(); s['r']=s.VRP/(K[750]*s.dL); s['big']=K[750]*s.dL>100e6
for lo in [48.5,49,49.5,50,50.5,51,52]:
    b=s[(s.SatZen>=lo)&(s.SatZen<lo+0.5)&s.big]
    print(f'  zen[{lo},{lo+.5}) big n={len(b)} fuera={(np.abs(b.r-1)>=1e-4).sum()}')
# dependencia de otras variables entre las filas >50 deg y dL*k>100MW
b=s[(s.SatZen>50)&s.big]
print('>50 y big: n',len(b),'fuera',(np.abs(b.r-1)>=1e-4).sum(),'| por Satellite:',b.assign(f=np.abs(b.r-1)>=1e-4).groupby('Satellite').f.agg(['sum','count']).to_dict('index'))
print('Dayflag en fuera:',s[(s.SatZen>50)&(np.abs(s.r-1)>=1e-4)].Dayflag.value_counts().to_dict())
