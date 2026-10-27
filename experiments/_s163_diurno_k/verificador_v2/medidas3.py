import os, sys, collections, json
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, sustrato_k as sk, clase_mirova as cm
filas = sk.cargar_ref(sys.argv[1])
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN")
       if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in vent)]
claves, sin = ev.claves_reflejo(pas, ev._filas_1_13())
print("reflejo probable:", len(claves), collections.Counter(c.split("|")[1] for c in claves))
sin_v = [x for x in sin if any(w[1] <= x.split("|")[2][:10] <= w[2] for w in vent)]
print("filas del estudio dentro de W2..W6 sin pasada:", len(sin_v), sin_v)
f113 = ev._filas_1_13()
print("filas 1.13 total", len(f113), collections.Counter(f.get("clase") for f in f113))
# cuantas de las 17 son protegidas / de que ventana, y fuente
por = {ev.ec.clave(p): p for p in pas}
for c in sorted(claves):
    p = por[c]; print("  ", c, p.estado, p.vrp_mw, p.fuente)
# variante: en las 26 protegidas V375 cuantas son W2
