# Oraculo: evaluar_completo con ev.evaluar parcheado para inyectar excluir_dias (semantica del evaluador sellado)
# vs el camino de evaluar_con_exclusion (quitar_dias + evaluar_completo). Datos: referencia congelada + fixture propio.
import os, sys, json, pathlib, random, collections
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
sys.stdout.reconfigure(encoding="utf-8")
import time; T0=time.time()
import banco_paridad as bp, evaluar_diurno_k as ev, evaluar_con_exclusion as ex, sustrato_k as sk
raiz, ref = sys.argv[1], pathlib.Path(sys.argv[2])
C,B="_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"; SHA="a"*40
vent=[(w[0],w[1],w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
inner=bp.inner_desde_html()
VOLS=set(sys.argv[3].split(","))
filas=[f for f in sk.cargar_ref(ref) if f["volcano"] in VOLS]
recs={C:ev.cargar_brazo([raiz],C,vent,inner),B:ev.cargar_brazo([raiz],B,vent,inner)}
import time; recs={k:[r for r in v if r["vol"] in VOLS] for k,v in recs.items()}
print("t", time.time()-T0)
print("records C", len(recs[C]), "B", len(recs[B]))
sus=json.load(open(os.path.join(CAR,"sustrato_k.json"),encoding="utf-8")); ps=ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
f113=ev._filas_1_13()
def vol(r):
    r=dict(r); r["principal"]=dict(r["principal"]); r["principal"].pop("T",None)
    return json.dumps({k:r[k] for k in ("principal","variantes","final","motivo","info","reflejo","reflejo12")}, sort_keys=True, default=str)
_orig=ev.evaluar
def con_oraculo(dias):
    dias=set(dias)
    def parcheada(pasadas, recs_por_lado, control, brazo, *a, excluir_dias=(), **kw):
        return _orig(pasadas, recs_por_lado, control, brazo, *a, excluir_dias=set(excluir_dias)|dias, **kw)
    ev.evaluar=parcheada
    try:
        return ev.evaluar_completo(filas, recs, C, B, "e-ii", ps, SHA, vent, (), f113)
    finally:
        ev.evaluar=_orig
def con_glue(dias):
    f,r=ex.quitar_dias(filas,recs,dias)
    return ev.evaluar_completo(f, r, C, B, "e-ii", ps, SHA, vent, (), f113)
dias_ventana=sorted({p.instante.strftime("%Y-%m-%d") for p in ev.pasadas_de(filas,"union",vent)})
prot=collections.Counter(p.instante.strftime("%Y-%m-%d") for p in ev.pasadas_de(filas,"union",vent) if p.estado=="alerta" and (p.vrp_mw or 0)>=1.0 and p.sensor_bucket.startswith("VIIRS"))
rnd=random.Random(3)
casos=[("vacio",[]),("fuera de ventana",["2026-03-11"]),("W2 un dia",[dias_ventana[0]]),("W6 ultimo dia",[dias_ventana[-1]]),
       ("2026-10-13 (V5 W6)",["2026-10-13"]),("dia con mas protegidas VIIRS",[prot.most_common(1)[0][0]]),
       ("3 dias con protegidas",[d for d,_ in prot.most_common(3)]),
       ("aleatorio 5",sorted(rnd.sample(dias_ventana,5))),("aleatorio 15",sorted(rnd.sample(dias_ventana,15)))]
SEL=[int(x) for x in sys.argv[4].split(',')] if len(sys.argv)>4 else range(len(casos))
for nombre,d in [casos[i] for i in SEL]:
    t=time.time(); a=vol(con_oraculo(d)); t1=time.time()-t; b=vol(con_glue(d)); print("   t oraculo %.0fs, total %.0fs" % (t1, time.time()-T0))
    ra=json.loads(a); 
    print("%-32s dias=%s iguales=%s  final=%s principal=%s" % (nombre, d[:4], a==b, ra["final"][:40], ra["principal"]["global"]))
    if a!=b:
        ja,jb=json.loads(a),json.loads(b)
        for k in ja:
            if ja[k]!=jb[k]: print("   DIFIERE en", k)
