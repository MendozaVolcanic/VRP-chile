# Verificador del PR #826 (contexto limpio): reajusta desde el CSV comprometido del brazo K, sin el script del PR.
# Copiado desde la carpeta temporal del verificador; solo cambia la ruta del CSV, que ahora es relativa.
import csv, math, random, statistics as st, collections, sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
F = Path(__file__).resolve().parents[1] / "salidas" / "corrimiento_pasadas_s149_ab_sin_test1_b22_max.csv"
rows = [r for r in csv.DictReader(open(F, encoding="utf-8")) if r["grupo"] == "MODIS"]
for r in rows:
    for k in ("cenit","acimut","dn_km","de_km","u_km","v_km","pred_der","pred_izq","relieve_km","h_vent_km"):
        r[k] = float(r[k])
print("n", len(rows))
# (c) coherencia del lado con el acimut: der => acimut ~ rumbo-90
c = collections.Counter((r["sat"], r["lado"], "sensorE" if math.sin(math.radians(r["acimut"]))>0 else "sensorW",
                         r["fecha"][11:13]) for r in rows)
for k,v in sorted(c.items()): print("  ", k, v)
def fit(sub, cols, nb=1000, seed=3, cluster=None):
    vols = sorted({r["volcan"] for r in sub}); iv = {v:i for i,v in enumerate(vols)}
    def solve(s):
        A = np.zeros((2*len(s), 2*len(vols)+len(cols))); y = np.zeros(2*len(s))
        for i,r in enumerate(s):
            a = math.radians(r["acimut"]); j = iv[r["volcan"]]
            A[2*i,2*j]=1; A[2*i+1,2*j+1]=1
            for k,cf in enumerate(cols):
                x = cf(r); A[2*i,2*len(vols)+k]=x*math.cos(a); A[2*i+1,2*len(vols)+k]=x*math.sin(a)
            y[2*i]=r["dn_km"]; y[2*i+1]=r["de_km"]
        co,*_ = np.linalg.lstsq(A,y,rcond=None); return co[2*len(vols):], float(np.sqrt(np.mean((y-A@co)**2)))
    co, rms = solve(sub); rnd = random.Random(seed); bs=[]
    keys = sorted({cluster(r) for r in sub}) if cluster else None
    for _ in range(nb):
        if cluster:
            ks=[keys[rnd.randrange(len(keys))] for _ in keys]; s=[r for k in ks for r in sub if cluster(r)==k]
        else:
            s=[sub[rnd.randrange(len(sub))] for _ in sub]
        if len({r["volcan"] for r in s})<len(vols): continue
        bs.append(solve(s)[0])
    bs=np.array(bs); return co, np.percentile(bs,2.5,0), np.percentile(bs,97.5,0), rms
tz = lambda r: math.tan(math.radians(r["cenit"]))
pl = lambda r: r["pred_der"] if r["lado"]=="der" else r["pred_izq"]
pinv = lambda r: r["pred_izq"] if r["lado"]=="der" else r["pred_der"]
def show(name, sub, cols, **kw):
    co,lo,hi,rms = fit(sub, cols, **kw)
    print("%-55s n=%3d rms %.3f | %s" % (name, len(sub), rms, "  ".join("%+.2f[%+.2f,%+.2f]"%(a,b,c) for a,b,c in zip(co,lo,hi))))
show("M2b interp lado der (reproduce PR)", rows, [pl])
show("M2b bootstrap por noche (fecha)", rows, [pl], cluster=lambda r: r["fecha"][:10])
show("M2b bootstrap por mes", rows, [pl], cluster=lambda r: r["fecha"][:7])
show("interp lado INVERTIDO solo", rows, [pinv])
show("libre tan z en lado der / lado izq", rows, [lambda r: tz(r)*(r["lado"]=="der"), lambda r: tz(r)*(r["lado"]=="izq")])
for sat in ("AQUA","TERRA"):
    s=[r for r in rows if r["sat"]==sat]
    show("M2b solo "+sat, s, [pl])
    show("  libre der/izq solo "+sat, s, [lambda r: tz(r)*(r["lado"]=="der"), lambda r: tz(r)*(r["lado"]=="izq")])
show("Solo Lascar M2b", [r for r in rows if r["volcan"]=="Lascar"], [pl])
show("M2b + libre tan z (simetrico)", rows, [pl, tz])
show("M2b + componente E fija por satelite", rows, [pl])
# residuo hacia el sensor tras quitar la interpolacion, por lado
print("residuo u - 0.90*pred (mediana) por sat/lado:")
for sat in ("AQUA","TERRA"):
    for ld in ("der","izq"):
        s=[r for r in rows if r["sat"]==sat and r["lado"]==ld]
        print("  %s %s n=%d  u_med %+.2f  pred_med %+.2f  resid_med %+.2f  v_med %+.2f" % (sat, ld, len(s), st.median(r["u_km"] for r in s),
              st.median(pl(r) for r in s), st.median(r["u_km"]-pl(r) for r in s), st.median(r["v_km"] for r in s)))
# paralaje esperado para el ajuste
print("relieve Lascar", {r["relieve_km"] for r in rows if r["volcan"]=="Lascar"}, "h_vent", {r["h_vent_km"] for r in rows if r["volcan"]=="Lascar"})
print("\n--- desplazamiento fijo por (volcan, satelite): la interpolacion solo se identifica dentro de cada satelite ---")
rows2 = [dict(r, volcan=r["volcan"]+"_"+r["sat"]) for r in rows]
show("M2b, fijo por volcan+sat", rows2, [pl])
show("libre tan z simetrico, fijo por volcan+sat", rows2, [tz])
show("libre der/izq, fijo por volcan+sat", rows2, [lambda r: tz(r)*(r["lado"]=="der"), lambda r: tz(r)*(r["lado"]=="izq")])
show("M2b + libre simetrico, fijo por volcan+sat", rows2, [pl, tz])
show("interp invertido, fijo por volcan+sat", rows2, [pinv])
co,lo,hi,rms = fit(rows2,[pl])
# offsets implicitos: comparar con modelo solo offsets
show("solo offsets volcan+sat (columna nula)", rows2, [lambda r: 0.0])
show("solo offsets volcan (columna nula)", rows, [lambda r: 0.0])
