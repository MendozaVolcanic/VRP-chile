# Verificador adenda 1: re-corre W1 con tres listas de dias excluidos, con codigo propio sobre el evaluador sellado.
import os, sys, json, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import banco_paridad as bp, evaluar_diurno_k as ev, sustrato_k as sk
raiz, ref = sys.argv[1], sys.argv[2]
C,B="_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"
SHA="68687d2d4b73bb0527da18a2c886a6dcc241a0ac"
V1=[("W1","2026-03-01","2026-03-20")]
inner=bp.inner_desde_html()
recs={C:ev.cargar_brazo([raiz],C,V1,inner),B:ev.cargar_brazo([raiz],B,V1,inner)}
filas=sk.cargar_ref(__import__("pathlib").Path(ref))
pas=ev.pasadas_de(filas,"tabla",V1,("Lascar",))
sus=json.load(open(os.path.join(CAR,"sustrato_k.json"),encoding="utf-8"))
ps=ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
for nombre,lista in [("sin excluir",[]),("(b)",["2026-03-10"]),("(a)+(b')",["2026-03-10","2026-03-11","2026-03-12"])]:
    r=ev.evaluar(pas,recs,C,B,"e-ii",ps,SHA,V1,excluir_dias=lista)
    print(nombre, lista, "| invalido", r["compuertas"]["invalido"], "| indecidible", r["compuertas"]["indecidible"], "| cob diurna", {k:(v) for k,v in r["cobertura_diurna"].items()} if isinstance(r["cobertura_diurna"],dict) else r["cobertura_diurna"], "| global", r["global"])
    for s,m in r["por_sensor"].items():
        print("   ",s,m["veredicto"],m["caso"],"protegidas",m["P"],"de",m["P_obs"],"| negativos",m["neg_pub"],"de",m["neg_obs"])
# que sale de W1 con la lista (a)+(b'): pasadas de MIROVA y records por plataforma
exc={"2026-03-10","2026-03-11","2026-03-12"}
c=collections.Counter()
for p in pas:
    d=p.instante.strftime("%Y-%m-%d")
    if d in exc:
        c[(p.sensor_bucket, "dia" if ev.es_dia_vol(p.volcano,p.instante) else "noche", p.estado, "prot" if getattr(p,"protegida",None) else "")]+=1
print("pasadas de MIROVA (tabla) que salen:", dict(c))
cr=collections.Counter()
for lado,rs in recs.items():
    for r in rs:
        if r["dt"].strftime("%Y-%m-%d") in exc:
            cr[(lado[-7:], r["b"], "dia" if r["es_dia"] else "noche")]+=1
print("records de W1 que salen:", dict(cr))
print("campos de PasadaMirova:", pas[0]._fields)
