# Verificador v3: el escenario E1 de la v2 (V-N4) contra la v3. Un brazo que recupera protegidas y publica en 60 pasadas
# que NO son negativos limpios. Caso A: las 60 son FALSO_POSITIVO diurnos. Caso B: son RUTINA de periodos con una alerta.
import os, sys
os.environ["VRP_PROFILE"]="mirova_equivalent"
R=sys.argv[1]
sys.path[:0]=[R, R+"/scripts", R+"/experiments/_s163_diurno_k"]
import test_evaluar_diurno_k as T
from datetime import datetime, timedelta
def caso_a():
    c=T.Completa()
    c.protegida(datetime(2026,7,25,16,0))
    for i in range(60):
        vol=T.VOLS[i%11]; ins=datetime(2026,7,20+(i%10),19,30)
        c.filas.append(T.fila(vol,T.V375,ins,"FALSO_POSITIVO"))
        c.rb.append(T.rec(vol,T.V375,ins,pub=True,disp=0.3,diag=True))
    return c.correr()
def caso_b():
    c=T.Completa()
    for k in range(6):                                           # 6 periodos (volcan, dia), cada uno con 1 protegida recuperada
        vol=T.VOLS[k]; dia=21+k
        c.protegida(datetime(2026,7,dia,16,0), vol=vol)
        for j in range(10):                                      # 10 RUTINA del mismo periodo, todas publicadas por el brazo
            ins=datetime(2026,7,dia,17,0)+timedelta(minutes=10*j+3)
            c.filas.append(T.fila(vol,T.V375,ins))
            c.rb.append(T.rec(vol,T.V375,ins,pub=True,disp=0.3,diag=True))
    return c.correr()
for nombre,f in (("A: 60 FALSO_POSITIVO diurnos publicados",caso_a),("B: 60 RUTINA de periodos con alerta publicadas",caso_b)):
    r=f(); m=r["principal"]["por_sensor"]["VIIRS375"]
    print("==", nombre, "| principal:", r["principal"]["global"], "| variantes:", r["variantes"], "| FINAL:", r["final"])
    print("   V375 principal: caso", m["caso"], "P", m["P"], "/", m["P_obs"], "neg_pub", m["neg_pub"], "/", m["neg_obs"], "pub_otra", m["pub_otra"])
