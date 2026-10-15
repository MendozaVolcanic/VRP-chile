# Verificador del PR #826 (contexto limpio): control VIIRS 375 en el brazo K, bootstrap por noche.
# Copiado desde la carpeta temporal del verificador; solo cambia la ruta del CSV, que ahora es relativa.
import csv, math, random, sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parents[1] / "salidas" / "corrimiento_pasadas_s149_ab_sin_test1_b22_max.csv"
rows=[r for r in csv.DictReader(open(F,encoding="utf-8"))]
for r in rows:
    for k in ("cenit","acimut","dn_km","de_km","u_km"): r[k]=float(r[k])
def fit(sub, cols, nb=300):
    vols=sorted({r["volcan"] for r in sub}); iv={v:i for i,v in enumerate(vols)}
    def solve(s):
        A=np.zeros((2*len(s),2*len(vols)+len(cols))); y=np.zeros(2*len(s))
        for i,r in enumerate(s):
            a=math.radians(r["acimut"]); j=iv[r["volcan"]]; A[2*i,2*j]=1; A[2*i+1,2*j+1]=1
            for k,c in enumerate(cols):
                x=c(r); A[2*i,2*len(vols)+k]=x*math.cos(a); A[2*i+1,2*len(vols)+k]=x*math.sin(a)
            y[2*i]=r["dn_km"]; y[2*i+1]=r["de_km"]
        co,*_=np.linalg.lstsq(A,y,rcond=None); return co[2*len(vols):]
    rnd=random.Random(1); noches=sorted({r["fecha"][:10] for r in sub}); by={}
    for r in sub: by.setdefault(r["fecha"][:10],[]).append(r)
    bs=[]
    for _ in range(nb):
        s=[r for n in (noches[rnd.randrange(len(noches))] for _ in noches) for r in by[n]]
        if len({r["volcan"] for r in s})==len(vols): bs.append(solve(s))
    return solve(sub), np.percentile(bs,[2.5,97.5],axis=0)
tz=lambda r: math.tan(math.radians(r["cenit"]))
for g in ("V375","MODIS"):
    sub=[r for r in rows if r["grupo"]==g]
    co,ci=fit(sub,[tz]); print(g,"brazo K todas n=%d vols=%d  g*tan z = %+.3f [%+.3f,%+.3f] (bootstrap por noche)"%(len(sub),len({r['volcan'] for r in sub}),co[0],ci[0][0],ci[1][0]))
    if g=="V375":
        sub2=[r for r in sub if r["cenit"]>=35]
        import statistics as st
        print("  V375 cenit>=35 n=%d mediana u %+.2f km"%(len(sub2),st.median(r["u_km"] for r in sub2)))
