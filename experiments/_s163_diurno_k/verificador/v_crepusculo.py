import sys
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluar_diurno_k as ev, sustrato_k as sk
from pipeline.store import _solar_elevation
filas = sk.cargar_ref(Path(sys.argv[1]))
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
n=0; cerca=[]
for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN"):
    d = p.instante.strftime("%Y-%m-%d")
    if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and any(w[1] <= d <= w[2] for w in vent):
        lat, lon = ev.coords()[p.volcano]
        e = _solar_elevation(lat, lon, p.instante.replace(tzinfo=None)); n+=1
        if abs(e) < 3: cerca.append((p.volcano, p.sensor_bucket, p.instante.strftime("%m-%d %H:%M"), round(e,2), p.estado))
print("pasadas VIIRS", n, "con |elevacion|<3 grados:", len(cerca)); print(cerca[:20])
