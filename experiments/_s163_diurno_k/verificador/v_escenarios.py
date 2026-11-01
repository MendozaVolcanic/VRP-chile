import sys
from pathlib import Path
AQ = Path(__file__).resolve().parent.parent
ROOT = AQ.parents[1]
for p in (str(ROOT), str(ROOT/"scripts"), str(AQ)): sys.path.insert(0, p)
import test_evaluar_diurno_k as T
V375, V750 = T.V375, T.V750
def resumen(nombre, r, s):
    m = r["por_sensor"][s]
    print("%-46s %s: global=%s | sensor=%s caso=%s | P2=%s neto=%+d P=%d/%d Qd=%.4f D=%s pub_otra=%d | inval=%d indec=%d" % (
        nombre, s, r["global"], m["veredicto"], m["caso"], m["p2"], m["neto"], m["P"], m["P_obs"], m["Qd"], m["D"], m["pub_otra"],
        len(r["compuertas"]["invalido"]), len(r["compuertas"]["indecidible"])))
    return m

# A: una protegida recuperada en V750 y 60 publicaciones en pasadas "otra" (dia con alerta nocturna del mismo volcan)
e = T.Escena().base()
for i in range(60):
    v = T.VOLS[i % 11]; d = 1 + (i % 28)
    e.noche(v, V750, d, estado="alerta", vrp=0.3, pub=True, disp=0.3, hora=4)       # alerta nocturna que vuelve "otra" al dia
    e.dia(v, V750, d, hora=19, pub_b=True)                                           # el brazo publica de dia en la RUTINA de ese dia
e.dia("Lascar", V750, 28, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5, hora=16)
r = e.evaluar(); resumen("A: 60 pubs en otra + 1 protegida", r, V750)
# A2: lo mismo sin las pubs en otra
e = T.Escena().base(); e.dia("Lascar", V750, 28, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5, hora=16)
r = e.evaluar(); resumen("A2: solo 1 protegida", r, V750)

# B: la noche NO queda identica: un record nocturno RUTINA del control que el brazo no tiene (no alerta) y uno que solo tiene el brazo
e = T.Escena().base()
e.rb.pop(3)                                                    # le falta al brazo un record nocturno de rutina
r = e.evaluar(); print("B1 falta record nocturno en brazo -> inval:", r["compuertas"]["invalido"], "indec:", r["compuertas"]["indecidible"], "solo:", r["noche_solo_un_lado"], "global", r["global"])
e = T.Escena().base()
e.rc.pop(3)
r = e.evaluar(); print("B2 falta record nocturno en control -> inval:", r["compuertas"]["invalido"], "indec:", r["compuertas"]["indecidible"], "solo:", r["noche_solo_un_lado"], "global", r["global"])

# C: I6 con pocas publicaciones de mas
e = T.Escena().base()
e.dia("Lascar", V750, 22, estado="alerta", vrp=3.0, pub_b=True, disp_b=2.5)
e = T.publicar_negativos_diurnos(e, V750, 3)
r = e.evaluar(); m = resumen("C: 3 negativos publicados + 1 protegida", r, V750); print("   I6:", {k:v for k,v in r["i6"][V750].items() if k!="problemas"}, r["i6"][V750]["problemas"])
