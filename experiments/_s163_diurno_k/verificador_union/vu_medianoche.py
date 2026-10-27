import os, sys, pathlib, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import sustrato_k as sk
from datetime import datetime, timedelta
filas=sk.cargar_ref(pathlib.Path(sys.argv[1]))
print("filas", len(filas))
# 1) filas cuyo +-120 s cruza la medianoche UTC (hay otra fila del mismo volcan y sensor a <=120 s del otro lado)
def t(f): return datetime.strptime(str(f["fecha_utc"])[:19],"%Y-%m-%d %H:%M:%S")
por=collections.defaultdict(list)
for f in filas: por[(f["volcano"],f["sensor_bucket"])].append((t(f),f))
cruzan=0; ejemplos=[]
for k,l in por.items():
    l.sort(key=lambda x:x[0])
    for (a,fa),(b,fb) in zip(l,l[1:]):
        if a.date()!=b.date() and (b-a).total_seconds()<=120:
            cruzan+=1; ejemplos.append((k,str(a),str(b)))
print("pares consecutivos mismo volcan+sensor a <=120 s con dia UTC distinto:", cruzan, ejemplos[:5])
# 2) cualquier fila a +-5 min de medianoche UTC
cerca=[f for f in filas if t(f).hour==23 and t(f).minute>=55 or t(f).hour==0 and t(f).minute<=5]
print("filas a +-5 min de medianoche UTC:", len(cerca), collections.Counter((f["sensor_bucket"],f["source"]) for f in cerca))
# 3) horas UTC por sensor
h=collections.defaultdict(collections.Counter)
for f in filas: h[f["sensor_bucket"]][t(f).hour]+=1
for s,c in h.items(): print(s, sorted(c.items()))
# 4) filas sin fecha / con fecha rara
print("fechas vacias:", sum(1 for f in filas if not f.get("fecha_utc")), "claves", sorted(filas[0].keys()))
