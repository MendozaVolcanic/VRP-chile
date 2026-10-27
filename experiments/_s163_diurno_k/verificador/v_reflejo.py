import sys, collections, json
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)):
    sys.path.insert(0, p)
import clase_mirova as cm, evaluador_comun as ec, evaluar_diurno_k as ev, sustrato_k as sk
ref = Path(sys.argv[1])
filas = sk.cargar_ref(ref)
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = []
for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN"):
    d = p.instante.strftime("%Y-%m-%d")
    if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_NOCHE and any(w[1] <= d <= w[2] for w in vent):
        if p.sensor_bucket == "MODIS" and ev.es_dia_vol(p.volcano, p.instante): continue
        pas.append(p)
print("pasadas", len(pas))
refl, sin = ev.claves_reflejo(pas, ev._filas_1_13())
print("reflejo claves", len(refl), "sin pareo", len(sin))
rows = ev._filas_1_13()
print("filas 1.13", len(rows), collections.Counter(r.get("clase") for r in rows))
print("claves", sorted(refl))
T0 = ec.tabla_por_pasada(pas, {"c": []}, "c")
pas2 = [p for p in pas if ec.clave(p) not in refl]
T1 = ec.tabla_por_pasada(pas2, {"c": []}, "c")
c0 = {f["clave"]: ec.clase_p2(f) for f in T0}
c1 = {f["clave"]: ec.clase_p2(f) for f in T1}
cambios = collections.Counter()
ej = []
for k, v in c1.items():
    if c0[k] != v:
        cambios[(c0[k], v)] += 1
        ej.append((k, c0[k], v))
print("cambios de clase por quitar las protegidas de reflejo:", dict(cambios))
for e in ej[:15]: print(e)
# dia/noche de los que cambian
print("de ellos diurnos VIIRS:", sum(1 for k,_,_ in ej if ev.es_dia_vol(k.split('|')[0], __import__('datetime').datetime.strptime(k.split('|')[2],'%Y-%m-%d %H:%M:%S')) ))
print("---- sin pareo dentro de ventanas:")
en = [x for x in sin if any(w[1] <= x.split("|")[2][:10] <= w[2] for w in vent)]
print(len(en), en)
print("fuera de ventanas:", [x for x in sin if x not in en][:30])
print("---- protegidas diurnas VIIRS vs filas 1.13")
from datetime import datetime
rows = ev._filas_1_13()
cl = {}
for f in rows:
    t0 = datetime.strptime(f["fecha_utc"], "%Y-%m-%d %H:%M:%S")
    for p in pas:
        if p.volcano==f["volcano"] and p.sensor_bucket==f["sensor_bucket"] and abs((p.instante.replace(tzinfo=None)-t0).total_seconds())<=cm.VENTANA_S:
            cl[ec.clave(p)] = f["clase"]
cnt = collections.Counter()
for p in pas:
    if p.sensor_bucket in ev.SENSORES_DIA and cm.es_protegida(p) and ev.es_dia_vol(p.volcano, p.instante):
        cnt[(p.sensor_bucket, cl.get(ec.clave(p), "SIN FILA"))] += 1
        if cl.get(ec.clave(p), "SIN FILA")=="SIN FILA": print("sin fila:", ec.clave(p), p.vrp_mw)
print(dict(cnt))
