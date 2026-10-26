import sys, collections, statistics
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluar_diurno_k as ev, sustrato_k as sk
filas = sk.cargar_ref(Path(sys.argv[1]))
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
c = collections.defaultdict(collections.Counter)
for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN"):
    d = p.instante.strftime("%Y-%m-%d")
    if p.volcano in ev.coords() and p.sensor_bucket=="VIIRS375" and p.fuente=="CONS" and any(w[1]<=d<=w[2] for w in vent):
        c[d]["dia" if ev.es_dia_vol(p.volcano,p.instante) else "noche"] += 1
dd = [c[d]["dia"] for d in c]; nn=[c[d]["noche"] for d in c]
md, mn = statistics.median(dd), statistics.median(nn)
print("mediana diaria dia", md, "noche", mn, "dias", len(c))
for d in sorted(c):
    if c[d]["dia"] < 0.5*md or c[d]["noche"] < 0.5*mn:
        print(d, dict(c[d]))
# dias de cada ventana sin ninguna pasada
import datetime
for w,a,b in vent:
    t=datetime.date.fromisoformat(a); e=datetime.date.fromisoformat(b)
    while t<=e:
        if t.isoformat() not in c: print("sin pasadas CONS V375:", w, t)
        t+=datetime.timedelta(1)
