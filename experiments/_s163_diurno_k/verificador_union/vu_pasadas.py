# Equivalencia estructural: pasadas_de(filas sin dias) vs pasadas_de(filas) menos las del dia, sobre la referencia congelada.
import os, sys, pathlib, random, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import evaluar_diurno_k as ev, evaluar_con_exclusion as ex, sustrato_k as sk
ref=sys.argv[1]
filas=sk.cargar_ref(pathlib.Path(ref))
vent=[(w[0],w[1],w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
vent_all=[(w[0],w[1],w[2]) for w in sk.VENTANAS]
print("ventanas", vent_all)
print("filas", len(filas), "tipos fecha", collections.Counter(type(f["fecha_utc"]).__name__ for f in filas), "largos", collections.Counter(len(str(f["fecha_utc"])) for f in filas))
def clave(p): return (p.volcano,p.sensor_bucket,p.instante,p.estado,p.vrp_mw,p.dist_km,p.fuente,p.solo_ocr,p.contradice,p.cruza_umbral if hasattr(p,"cruza_umbral") else None, len(p.filas) if hasattr(p,"filas") else None)
print("campos Pasada", ev.cm.PasadaMirova._fields)
def comparar(ventanas, dias, canal="union"):
    base=ev.pasadas_de(filas,canal,ventanas)
    esperado=[p for p in base if p.instante.strftime("%Y-%m-%d") not in dias]
    f,_=ex.quitar_dias(filas,{},dias)
    real=ev.pasadas_de(f,canal,ventanas)
    ce=sorted(map(repr,[ (p.volcano,p.sensor_bucket,p.instante,p.estado,p.vrp_mw,p.dist_km,p.fuente,p.solo_ocr,p.ocr_contradice_tabla,p.ocr_cruza_1mw,len(p.filas)) for p in esperado]))
    cr=sorted(map(repr,[ (p.volcano,p.sensor_bucket,p.instante,p.estado,p.vrp_mw,p.dist_km,p.fuente,p.solo_ocr,p.ocr_contradice_tabla,p.ocr_cruza_1mw,len(p.filas)) for p in real]))
    return ce==cr, len(base), len(esperado), len(real), [x for x in cr if x not in set(ce)][:3], [x for x in ce if x not in set(cr)][:3]
dias_todos=sorted({p.instante.strftime("%Y-%m-%d") for p in ev.pasadas_de(filas,"union",vent_all)})
print("dias con pasadas en ventanas:", len(dias_todos), dias_todos[:2], dias_todos[-2:])
malos=[]
import time; T0=time.time()
rndd=random.Random(5)
muestra=sorted(set(rndd.sample(dias_todos,20))|{dias_todos[0],dias_todos[-1],"2026-10-13","2026-06-24"})
for canal in ("union","tabla"):
    for d in muestra:
        ok,nb,ne,nr,extra,falta=comparar(vent_all,{d},canal)
        if not ok: malos.append((canal,d,nb,ne,nr,extra,falta))
print("dias individuales comparados:", len(muestra),"x2 canales; con diferencia:", len(malos), "t=%.0fs"%(time.time()-T0))
for m in malos[:10]: print(m)
rnd=random.Random(7); n_mal=0
for i in range(30):
    ds=set(rnd.sample(dias_todos, rnd.randint(2,12)))
    ok,*_=comparar(vent_all,ds)
    if not ok: n_mal+=1
print("conjuntos aleatorios con diferencia:", n_mal, "de 30")
# cercania a medianoche UTC: filas con hora < 00:05 o > 23:55
def hm(f): s=str(f["fecha_utc"]); return s[11:16]
cerca=[f for f in filas if hm(f)>="23:50" or hm(f)<="00:10"]
print("filas a +-10 min de medianoche UTC (toda la referencia):", len(cerca), collections.Counter((f["sensor_bucket"],f["source"]) for f in cerca))
# distribucion horaria por sensor en ventanas
ps=ev.pasadas_de(filas,"union",vent_all)
h=collections.Counter()
for p in ps: h[(p.sensor_bucket, p.instante.hour)]+=1
print("horas UTC con pasadas, VIIRS/MODIS:", sorted({(k[0],k[1]) for k in h}))
