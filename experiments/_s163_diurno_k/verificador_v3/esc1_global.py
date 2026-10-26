# Verificador v3: matriz completa de veredicto_global sobre los veredictos por sensor posibles.
import os, sys, itertools
os.environ["VRP_PROFILE"]="mirova_equivalent"
R=sys.argv[1]
sys.path[:0]=[R, R+"/scripts", R+"/experiments/_s163_diurno_k"]
import evaluar_diurno_k as ev
vs=[ev.ADOPTAR, ev.NO_ADOPTAR, ev.SIN_CAMBIO, ev.DECIDE_M4]
ok={"invalido":[], "indecidible":[]}
for a,b in itertools.product(vs,vs):
    print("V375=%-22s V750=%-22s -> %s" % (a,b,ev.veredicto_global(ok,[],{"VIIRS375":a,"VIIRS750":b})))
