import os, sys
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44\experiments\_s163_diurno_k")
import test_evaluar_diurno_k as T
V375 = T.V375
def caso(con_diurno):
    e = T.Escena().base()
    # noche con alerta protegida de MIROVA el dia 25 en Lascar V375: SIN record en NINGUN brazo
    ins = T.t(25, 5)
    e.pasadas.append(T.pas("Lascar", V375, ins, "alerta", 3.0))
    if con_diurno:
        e.dia("Lascar", V375, 25)      # el brazo diurno si tiene un record diurno ese dia
    r = e.evaluar("e-ii")
    return r["compuertas"]["invalido"], r["global"]
for c in (False, True):
    inv, g = caso(c)
    print("record diurno del brazo ese dia:", c, "| invalido:", inv, "| global:", g)
