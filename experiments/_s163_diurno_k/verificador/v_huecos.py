import sys, collections
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluar_diurno_k as ev, sustrato_k as sk
filas = sk.cargar_ref(Path(sys.argv[1]))
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN") if p.volcano in ev.coords()]
# por dia, pasadas VIIRS (noche, dia), fuente CONS
c = collections.defaultdict(lambda: collections.Counter())
for p in pas:
    d = p.instante.strftime("%Y-%m-%d")
    if "2026-09-25" <= d <= "2026-10-25" and p.sensor_bucket in ("VIIRS375","VIIRS750"):
        c[d][(p.sensor_bucket, "dia" if ev.es_dia_vol(p.volcano,p.instante) else "noche", p.fuente)] += 1
for d in sorted(c):
    print(d, " ".join("%s/%s/%s:%d" % (k[0][5:],k[1][0],k[2][0],v) for k,v in sorted(c[d].items())))
