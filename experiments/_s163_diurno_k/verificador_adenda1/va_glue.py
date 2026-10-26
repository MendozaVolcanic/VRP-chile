# ¿Dar la lista por prefiltrado de filas y records (sin tocar el evaluador) equivale a evaluar(excluir_dias=lista)? W1, Láscar.
import os, sys, json, pathlib
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import banco_paridad as bp, evaluar_diurno_k as ev, sustrato_k as sk
raiz, ref = sys.argv[1], sys.argv[2]
C,B="_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"; SHA="68687d2d4b73bb0527da18a2c886a6dcc241a0ac"
V1=[("W1","2026-03-01","2026-03-20")]; L=["2026-03-10","2026-03-11","2026-03-12"]
inner=bp.inner_desde_html()
recs={C:ev.cargar_brazo([raiz],C,V1,inner),B:ev.cargar_brazo([raiz],B,V1,inner)}
filas=[f for f in sk.cargar_ref(pathlib.Path(ref)) if f["volcano"]=="Lascar"]
sus=json.load(open(os.path.join(CAR,"sustrato_k.json"),encoding="utf-8")); ps=ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
def resumen(r): return (r["global"], r["compuertas"]["invalido"], {s:(m["veredicto"],m["P"],m["P_obs"],m["neg_pub"],m["neg_obs"]) for s,m in r["por_sensor"].items()})
a=ev.evaluar(ev.pasadas_de(filas,"union",V1),recs,C,B,"e-ii",ps,SHA,V1,excluir_dias=L)
filas_p=[f for f in filas if f["fecha_utc"][:10] not in L]
recs_p={k:[r for r in v if r["dt"].strftime("%Y-%m-%d") not in L] for k,v in recs.items()}
b=ev.evaluar(ev.pasadas_de(filas_p,"union",V1),recs_p,C,B,"e-ii",ps,SHA,V1)
print("excluir_dias :", resumen(a)); print("prefiltrado  :", resumen(b)); print("iguales:", resumen(a)==resumen(b))
# y evaluar_completo (principal + variantes) con el prefiltrado: ¿corre? ¿qué dice?
r=ev.evaluar_completo(filas_p, recs_p, C, B, "e-ii", ps, SHA, V1)
print("evaluar_completo prefiltrado -> principal", r["principal"]["global"], "| variantes", r["variantes"], "| final", r["final"], (r["motivo"] or "")[:120])
r0=ev.evaluar_completo(filas, recs, C, B, "e-ii", ps, SHA, V1)
print("evaluar_completo sin lista    -> principal", r0["principal"]["global"], "| final", r0["final"])
