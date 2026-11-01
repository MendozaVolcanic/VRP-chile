import sys, collections
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
filas = sk.cargar_ref(Path(sys.argv[1]))
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN")
       if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_NOCHE
       and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in vent)]
T = ec.tabla_por_pasada(pas, {"c": []}, "c")
c = collections.Counter()
alert_hora = collections.defaultdict(set)
for f in T:
    p = f["pasada"]
    if p.estado in ("alerta",):
        alert_hora[(p.volcano, p.sensor_bucket, f["dia"])].add("dia" if ev.es_dia_vol(p.volcano, p.instante) else "noche")
for f in T:
    p = f["pasada"]
    if p.sensor_bucket not in ev.SENSORES_DIA or not ev.es_dia_vol(p.volcano, p.instante): continue
    cl = "protegida" if f["protegida"] else ec.clase_p2(f)
    if cl != "otra": continue
    k = (p.volcano, p.sensor_bucket, f["dia"])
    if p.estado == "rutina" and p.fuente == "CONS":
        motivo = "RUTINA/CONS, dia con alerta solo de " + ("+".join(sorted(alert_hora.get(k, set()))) or "?") + (" + FP" if f["noche_con_fp"] and not f["noche_con_alerta"] else "")
    else:
        motivo = "estado=%s fuente=%s" % (p.estado, p.fuente)
    c[(p.sensor_bucket, motivo)] += 1
for k in sorted(c): print(k, c[k])
