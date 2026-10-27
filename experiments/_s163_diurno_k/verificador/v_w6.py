import sys, collections
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
filas = sk.cargar_ref(Path(sys.argv[1]))
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN") if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and "2026-10-01" <= p.instante.strftime("%Y-%m-%d") <= "2026-10-14"]
T = ec.tabla_por_pasada(pas, {"c": []}, "c")
c = collections.Counter()
for f in T:
    if ev.es_dia_vol(f["pasada"].volcano, f["pasada"].instante) and f["dia"] in ("2026-10-13","2026-10-14","2026-10-12"):
        c[(f["dia"], f["pasada"].sensor_bucket, "protegida" if f["protegida"] else ec.clase_p2(f))] += 1
for k in sorted(c): print(k, c[k])
