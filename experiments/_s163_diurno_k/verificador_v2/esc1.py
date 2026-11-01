# Escenarios propios del verificador v2 (no tocan el repo). Usa la Escena de la batería.
import os, sys
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44\experiments\_s163_diurno_k")
import test_evaluar_diurno_k as T
ev = T.ev
V375, V750, VOLS = T.V375, T.V750, T.VOLS

def resumen(r, etiqueta):
    print("==", etiqueta, "| GLOBAL", r["global"], "| inv", len(r["compuertas"]["invalido"]), "ind", len(r["compuertas"]["indecidible"]))
    for x in r["compuertas"]["invalido"][:5] + r["compuertas"]["indecidible"][:5]:
        print("    ", x)
    for s, m in r["por_sensor"].items():
        print("  ", s, m["veredicto"], "caso", m["caso"], "| p2", m["p2"], "neto", m["neto"], "B", m["p2_det"]["B"], "| P", m["P"], "/", m["P_obs"],
              "| mb", m["amb_recuperadas"], "/", m["amb_obs"], "| neg", m["neg_pub"], "/", m["neg_obs"], "| otra pub", m["pub_otra"], "| D", m["D"], "| publica", m["publica"])

# E1: caso b con publicaciones masivas en "otra" (pasadas FALSO_POSITIVO diurnas), 1 protegida recuperada, 0 negativos publicados
for opcion in ("e-i", "e-ii"):
    e = T.Escena().base()
    e.dia("Lascar", V375, 25, estado="alerta", vrp=2.0, pub_b=True)          # 1 protegida recuperada
    for i in range(60):                                                       # 60 FALSO_POSITIVO diurnos publicados
        e.dia(VOLS[i % 11], V375, 1 + (i % 25), hora=19, estado="fp", pub_b=True)
    resumen(e.evaluar(opcion), "E1 b con 60 pubs en FP (otra), opcion " + opcion)

# E2: brazo estrictamente mejor bajo 1 MW pero sin protegida: 4 mb recuperadas en 4 bloques, 0 FP
e = T.Escena().base()
for i in range(4):
    e.dia(VOLS[i], V375, 21 + i, estado="alerta", vrp=0.4, pub_b=True)
resumen(e.evaluar("e-ii"), "E2 4 mb recuperadas, 0 negativos publicados, P=0")

# E3: lo mismo con 1 protegida a la vez
e = T.Escena().base()
for i in range(4):
    e.dia(VOLS[i], V375, 21 + i, estado="alerta", vrp=0.4, pub_b=True)
e.dia("Lastarria", V375, 26, estado="alerta", vrp=3.0, pub_b=True)
resumen(e.evaluar("e-ii"), "E3 4 mb + 1 protegida, 0 FP")

# E4: solo 1 protegida recuperada en V750, resto callado (tipo reflejo)
e = T.Escena().base()
e.dia("Lascar", V750, 25, estado="alerta", vrp=760.0, pub_b=True, disp_b=700.0)
resumen(e.evaluar("e-ii"), "E4 V750: 1 protegida (reflejo posible), 0 FP")

# E5: 10 FP publicadas en negativos + 10 mb recuperadas + 1 protegida: neto 0 -> case b
e = T.Escena().base()
for i in range(10):
    e.dia(VOLS[i % 11], V375, 1 + i, estado="alerta", vrp=0.3, pub_b=True, hora=17)
e.dia("Lastarria", V375, 26, estado="alerta", vrp=3.0, pub_b=True)
k = 0
for r in e.rb:
    if r["b"] == V375 and r["es_dia"] and not r["pub"] and k < 10:
        r["pub"], r["disp"] = True, 0.5; k += 1
resumen(e.evaluar("e-ii"), "E5 10 mb recuperadas + 10 FP + 1 protegida (neto 0)")
