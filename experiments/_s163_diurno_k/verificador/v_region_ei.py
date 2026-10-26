import sys, random, collections
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import nulo_estructural as nu, evaluar_diurno_k as ev, evaluador_comun as ec
T, sint = nu.armar(sys.argv[1])
ids = {id(r) for r in sint}
filas = [f for f in T if f["es_dia"] and f["rec"]["diurno"] is not None and id(f["rec"]["diurno"]) in ids]
def poner(f, v):
    f["rec"]["diurno"]["pub"], f["rec"]["diurno"]["disp"] = v, (0.3 if v else 0.0)
def escenario(s, n_prot, n_amb, n_neg, n_otra, semilla=1):
    rng = random.Random(semilla)
    for r in sint: r["pub"], r["disp"] = False, 0.0
    fs = [f for f in filas if f["pasada"].sensor_bucket == s]
    prot = [f for f in fs if f["protegida"]]; amb = [f for f in fs if ec.clase_p2(f)=="alerta_mb"]
    neg = [f for f in fs if ec.clase_p2(f)=="negativo"]; otra = [f for f in fs if ec.clase_p2(f)=="otra" and not f["protegida"]]
    for lst, n in ((prot,n_prot),(amb,n_amb),(neg,n_neg),(otra,n_otra)):
        for f in rng.sample(lst, min(n, len(lst))): poner(f, True)
    m = ev.metricas_sensor(T, sint, "ctrl", "diurno", s)
    print("%s prot=%d amb=%d neg=%d otra=%d -> P2 %s (neto %+d, B %d, p_pierde %.4f) Qd %.4f Qn %.4f D %s -> e-i %s | e-ii %s" % (
        s, n_prot, n_amb, n_neg, n_otra, m["p2"], m["neto"], m["p2_det"]["B"], m["p2_det"]["p_pierde"], m["Qd"], m["Qn"], m["D"],
        ev.veredicto_sensor(m,"e-i")[0], ev.veredicto_sensor(m,"e-ii")[0]))
escenario("VIIRS375", 2, 2, 50, 0)
escenario("VIIRS375", 4, 0, 52, 300)
escenario("VIIRS375", 1, 0, 40, 0)
escenario("VIIRS750", 1, 0, 18, 0)
escenario("VIIRS750", 1, 0, 18, 200)
escenario("VIIRS750", 2, 0, 20, 0)
