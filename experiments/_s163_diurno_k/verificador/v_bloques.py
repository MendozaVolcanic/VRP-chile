import sys, collections
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import clase_mirova as cm, evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
filas = sk.cargar_ref(Path(sys.argv[1]))
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN") if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in vent)]
T = ec.tabla_por_pasada(pas, {"c": []}, "c")
for s in ev.SENSORES_DIA:
    pr = [f for f in T if f["pasada"].sensor_bucket==s and ev.es_dia_vol(f["pasada"].volcano, f["pasada"].instante) and f["protegida"]]
    al = [f for f in T if f["pasada"].sensor_bucket==s and ev.es_dia_vol(f["pasada"].volcano, f["pasada"].instante) and (f["protegida"] or ec.clase_p2(f)=="alerta_mb")]
    print(s, "protegidas", len(pr), "bloques volcan-dia", len({(f["pasada"].volcano, f["dia"]) for f in pr}), "| alertas (prot+mb)", len(al), "bloques", len({(f["pasada"].volcano, f["dia"]) for f in al}), "| volcanes", collections.Counter(f["pasada"].volcano for f in pr))
